"""
基于 Redis 的队列（带去重）

底层使用 Redis List + Set 实现：
- List (queue:{name})  存放消息顺序
- Set  (queue:{name}:keys) 记录未消费消息的 key，用于去重

使用示例：
    from redis import Redis
    from redis_queue import RedisQueue

    redis_cli = Redis(host="localhost", port=6379)
    q = RedisQueue(name="tasks", redis_cli=redis_cli)
    q.put("hello")        # True，入队成功
    q.put("hello")        # False，重复消息被过滤
    item = q.get()        # "hello"
    q.put("hello")        # True，消费后可再次入队
    item = q.get(timeout=5)
    item = q.get_nowait() # 空则抛 queue.Empty
    print(q.size())
    q.close()
"""
import json
from queue import Empty
from typing import Any, Callable, Optional

from redis import Redis


class RedisQueue:
    """基于 Redis List + Set 的队列，支持未消费消息去重"""

    def __init__(
        self,
        name: str = "default",
        redis_cli: Redis = None,
        key_func: Optional[Callable[[Any], str]] = None,
    ):
        """
        Args:
            name:       队列名称，作为 Redis key 前缀
            redis_cli:  Redis 客户端实例，由调用方传入
            key_func:   去重键提取函数，默认用 str(item)
                        可自定义，如 key_func=lambda x: x["id"]
        """
        if redis_cli is None:
            raise ValueError("redis_cli 不能为 None，请传入 Redis 客户端实例")
        self.name = name
        self._client = redis_cli
        self._key_func = key_func or (lambda item: str(item))
        self._queue_key = f"queue:{name}"
        self._keys_key = f"queue:{name}:keys"

    @staticmethod
    def _serialize(item: Any) -> str:
        return json.dumps(item, ensure_ascii=False)

    @staticmethod
    def _deserialize(data: bytes) -> Any:
        return json.loads(data)

    def _item_key(self, item: Any) -> str:
        return self._key_func(item)

    def put(self, item: Any) -> bool:
        """
        放入元素（LPUSH）。如果该消息已在队列中未被消费，则过滤不入队。

        Returns:
            True  - 入队成功
            False - 重复消息被过滤
        """
        key = self._item_key(item)
        # SADD 返回新增成员数：1 表示新增成功，0 表示已存在
        added = self._client.sadd(self._keys_key, key)
        if added == 0:
            return False
        data = self._serialize(item)
        self._client.lpush(self._queue_key, data)
        return True

    def get(self, timeout: Optional[float] = None) -> Any:
        """
        阻塞获取元素（BRPOP）。
        timeout=None 表示无限等待，timeout=0 表示非阻塞。
        """
        # BRPOP 的 timeout=0 表示无限等待，与 Python queue 语义不同
        redis_timeout = 0 if timeout is None else timeout
        result = self._client.brpop(self._queue_key, timeout=redis_timeout)
        if result is None:
            raise Empty(f"队列 {self.name} 为空，等待超时")
        _, data = result
        item = self._deserialize(data)
        # 消费后从去重集合中移除，允许再次入队
        self._client.srem(self._keys_key, self._item_key(item))
        return item

    def get_nowait(self) -> Any:
        """非阻塞获取（RPOP），队列空时抛出 Empty 异常。"""
        data = self._client.rpop(self._queue_key)
        if data is None:
            raise Empty(f"队列 {self.name} 为空")
        item = self._deserialize(data)
        self._client.srem(self._keys_key, self._item_key(item))
        return item

    def size(self) -> int:
        return self._client.llen(self._queue_key)

    def empty(self) -> bool:
        return self.size() == 0

    def close(self) -> None:
        """不关闭 redis_cli（由调用方管理生命周期），仅清理本队列的 Redis key"""
        self._client.delete(self._queue_key, self._keys_key)

    def __len__(self) -> int:
        return self.size()

    def __repr__(self) -> str:
        return f"RedisQueue(name={self.name}, size={self.size()})"
