"""
Redis 工具集：分布式锁 + 通用缓存操作

基于调用方传入的 redis_cli，提供：
- RedisLock:   可重入分布式锁（SET NX EX + Lua 原子释放 + Lua 可重入计数）
- RedisUtil:   通用缓存工具（get/set/delete/expire 等）

使用示例：
    from redis import Redis
    from redis_util import RedisLock, RedisUtil

    redis_cli = Redis(host="localhost", port=6379)

    # ---- 分布式锁 ----
    lock = RedisLock(redis_cli=redis_cli, name="order:123", timeout=30)

    # 方式一：手动加锁/解锁
    if lock.acquire():
        try:
            # do something
            pass
        finally:
            lock.release()

    # 方式二：上下文管理器（推荐）
    with lock:
        # do something
        pass

    # ---- 通用缓存 ----
    util = RedisUtil(redis_cli=redis_cli)

    util.set("user:1", {"name": "tom", "age": 20})
    util.set("user:2", "hello", ttl=60)  # 60 秒过期
    user = util.get("user:1")            # {"name": "tom", "age": 20}
    util.delete("user:1")
    util.expire("user:2", 120)           # 续期到 120 秒
    util.exists("user:2")                # True
    util.incr("counter")                 # 1
    util.incr("counter", 5)              # 6
"""
import json
import time
import uuid
from typing import Any, Optional

from redis import Redis
from redis.exceptions import RedisError


# ============================================================
#  分布式锁
# ============================================================

# Lua: 原子释放锁 —— 仅当 value 匹配当前持有者的 token 时才删除
_RELEASE_SCRIPT = """
if redis.call('get', KEYS[1]) == ARGV[1] then
    return redis.call('del', KEYS[1])
else
    return 0
end
"""

# Lua: 可重入加锁 —— 存在且 token 匹配则计数+1，不存在则创建
_REENTRANT_ACQUIRE_SCRIPT = """
local current = redis.call('get', KEYS[1])
if current == ARGV[1] then
    redis.call('incr', KEYS[2])
    redis.call('expire', KEYS[2], ARGV[2])
    return 1
elseif current == false then
    redis.call('set', KEYS[1], ARGV[1], 'EX', ARGV[2])
    redis.call('set', KEYS[2], 1, 'EX', ARGV[2])
    return 1
else
    return 0
end
"""

# Lua: 可重入释放锁 —— 计数-1，减到 0 时删除锁和计数器
_REENTRANT_RELEASE_SCRIPT = """
if redis.call('get', KEYS[1]) ~= ARGV[1] then
    return 0
end
local count = redis.call('decr', KEYS[2])
if count <= 0 then
    redis.call('del', KEYS[2])
    redis.call('del', KEYS[1])
end
return 1
"""


class RedisLock:
    """可重入分布式锁

    - 基于 SET NX EX 实现互斥
    - Lua 脚本保证释放的原子性（只释放自己持有的锁）
    - 支持可重入：同一线程可多次 acquire，需对应次数的 release
    - 支持上下文管理器 (with)
    """

    def __init__(
        self,
        redis_cli: Redis,
        name: str,
        timeout: float = 30,
        retry_interval: float = 0.1,
        retry_times: int = 50,
    ):
        """
        Args:
            redis_cli:       Redis 客户端实例
            name:            锁名称，作为 Redis key
            timeout:         锁超时时间（秒），防止死锁
            retry_interval:  获取锁失败时重试间隔（秒）
            retry_times:     获取锁最大重试次数
        """
        if redis_cli is None:
            raise ValueError("redis_cli 不能为 None，请传入 Redis 客户端实例")
        self._client = redis_cli
        self._lock_key = f"lock:{name}"
        self._count_key = f"lock:{name}:count"
        self._timeout = timeout
        self._retry_interval = retry_interval
        self._retry_times = retry_times
        # 每个锁实例持有唯一 token，用于标识锁的持有者
        self._token = str(uuid.uuid4())

    def acquire(self, blocking: bool = True) -> bool:
        """
        获取锁。

        Args:
            blocking: True 阻塞等待直到获取或超时，False 只尝试一次

        Returns:
            True 获取成功，False 获取失败
        """
        # 可重入：先尝试通过 Lua 脚本加锁
        acquired = self._try_reentrant_acquire()
        if acquired:
            return True
        if not blocking:
            return False

        for _ in range(self._retry_times):
            time.sleep(self._retry_interval)
            if self._try_reentrant_acquire():
                return True
        return False

    def _try_reentrant_acquire(self) -> bool:
        result = self._client.eval(
            _REENTRANT_ACQUIRE_SCRIPT, 2,
            self._lock_key, self._count_key,
            self._token, int(self._timeout),
        )
        return result == 1

    def release(self) -> bool:
        """
        释放锁（可重入：计数-1，减到 0 才真正释放）。

        Returns:
            True 释放成功，False 非锁持有者或锁已过期
        """
        result = self._client.eval(
            _REENTRANT_RELEASE_SCRIPT, 2,
            self._lock_key, self._count_key,
            self._token,
        )
        return result == 1

    def __enter__(self):
        if not self.acquire():
            raise RedisError(f"获取锁 {self._lock_key} 失败")
        return self

    def __exit__(self, exc_type, exc_val, exc_tb):
        self.release()

    def __repr__(self) -> str:
        return f"RedisLock(key={self._lock_key}, token={self._token})"


# ============================================================
#  通用缓存工具
# ============================================================

class RedisUtil:
    """Redis 通用缓存工具，支持 JSON 序列化/反序列化"""

    def __init__(self, redis_cli: Redis, prefix: str = ""):
        """
        Args:
            redis_cli:  Redis 客户端实例
            prefix:     key 前缀，如 "myapp:"，最终 key = prefix + key
        """
        if redis_cli is None:
            raise ValueError("redis_cli 不能为 None，请传入 Redis 客户端实例")
        self._client = redis_cli
        self._prefix = prefix

    def _full_key(self, key: str) -> str:
        return f"{self._prefix}{key}"

    # ---- 基础读写 ----

    def get(self, key: str) -> Any:
        """获取缓存值，自动 JSON 反序列化"""
        data = self._client.get(self._full_key(key))
        if data is None:
            return None
        return json.loads(data)

    def set(self, key: str, value: Any, ttl: Optional[int] = None) -> None:
        """
        设置缓存值，自动 JSON 序列化。

        Args:
            key:   缓存 key
            value: 缓存值，需 JSON 可序列化
            ttl:   过期时间（秒），None 表示永不过期
        """
        data = json.dumps(value, ensure_ascii=False)
        full_key = self._full_key(key)
        if ttl is not None:
            self._client.setex(full_key, ttl, data)
        else:
            self._client.set(full_key, data)

    def delete(self, *keys: str) -> int:
        """删除一个或多个 key，返回删除数量"""
        if not keys:
            return 0
        full_keys = [self._full_key(k) for k in keys]
        return self._client.delete(*full_keys)

    def exists(self, key: str) -> bool:
        """key 是否存在"""
        return self._client.exists(self._full_key(key)) == 1

    def expire(self, key: str, ttl: int) -> bool:
        """设置 key 的过期时间（秒）"""
        return self._client.expire(self._full_key(key), ttl)

    def ttl(self, key: str) -> int:
        """获取 key 的剩余过期时间（秒），-1 表示永不过期，-2 表示不存在"""
        return self._client.ttl(self._full_key(key))

    # ---- 数值操作 ----

    def incr(self, key: str, amount: int = 1) -> int:
        """自增"""
        return self._client.incr(self._full_key(key), amount)

    def decr(self, key: str, amount: int = 1) -> int:
        """自减"""
        return self._client.decr(self._full_key(key), amount)

    # ---- Hash 操作 ----

    def hget(self, name: str, key: str) -> Any:
        """获取 hash 字段值"""
        data = self._client.hget(self._full_key(name), key)
        if data is None:
            return None
        return json.loads(data)

    def hset(self, name: str, key: str, value: Any) -> None:
        """设置 hash 字段值"""
        data = json.dumps(value, ensure_ascii=False)
        self._client.hset(self._full_key(name), key, data)

    def hgetall(self, name: str) -> dict:
        """获取 hash 所有字段"""
        raw = self._client.hgetall(self._full_key(name))
        return {k.decode(): json.loads(v) for k, v in raw.items()}

    def hdel(self, name: str, *keys: str) -> int:
        """删除 hash 字段"""
        return self._client.hdel(self._full_key(name), *keys)

    # ---- 锁 ----

    def lock(
        self,
        name: str,
        timeout: float = 30,
        retry_interval: float = 0.1,
        retry_times: int = 50,
    ) -> RedisLock:
        """快捷创建分布式锁"""
        return RedisLock(
            redis_cli=self._client,
            name=name,
            timeout=timeout,
            retry_interval=retry_interval,
            retry_times=retry_times,
        )

    def __repr__(self) -> str:
        return f"RedisUtil(prefix={self._prefix!r})"
