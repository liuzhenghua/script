"""
基于内存的本地队列（带去重）

底层使用 deque + set 去重，threading.Condition 实现阻塞等待。
未消费的消息重复入队时自动过滤，消费后可再次入队。

使用示例：
    from memory_queue import MemoryQueue

    q = MemoryQueue(name="tasks")
    q.put("hello")        # True，入队成功
    q.put("hello")        # False，重复消息被过滤
    item = q.get()        # "hello"
    q.put("hello")        # True，消费后可再次入队
    item = q.get(timeout=5)
    item = q.get_nowait() # 空则抛 queue.Empty
    print(q.size())
    q.close()
"""
import threading
from collections import deque
from queue import Empty
from typing import Any, Callable, Optional


class MemoryQueue:
    """基于内存的线程安全队列，支持未消费消息去重"""

    def __init__(self, name: str = "default", maxsize: int = 0,
                 key_func: Optional[Callable[[Any], str]] = None):
        """
        Args:
            name:       队列名称
            maxsize:    队列最大容量，0 表示无限制
            key_func:   去重键提取函数，默认用 str(item)
                        可自定义，如 key_func=lambda x: x["id"]
        """
        self.name = name
        self._maxsize = maxsize
        self._key_func = key_func or (lambda item: str(item))
        self._deque: deque = deque()
        self._pending_keys: set[str] = set()
        self._not_empty = threading.Condition(threading.Lock())
        self._not_full = threading.Condition(threading.Lock())

    def _item_key(self, item: Any) -> str:
        return self._key_func(item)

    def put(self, item: Any) -> bool:
        """
        放入元素。如果队列有容量限制且已满，则阻塞等待。
        如果该消息已在队列中未被消费，则过滤不入队。

        Returns:
            True  - 入队成功
            False - 重复消息被过滤
        """
        key = self._item_key(item)
        with self._not_full:
            if self._maxsize > 0:
                while len(self._deque) >= self._maxsize:
                    self._not_full.wait()
            with self._not_empty:
                if key in self._pending_keys:
                    return False
                self._deque.append(item)
                self._pending_keys.add(key)
                self._not_empty.notify()
        return True

    def get(self, timeout: Optional[float] = None) -> Any:
        """阻塞获取元素。超时抛出 Empty 异常。"""
        with self._not_empty:
            if not self._deque:
                self._not_empty.wait(timeout=timeout)
            if not self._deque:
                raise Empty(f"队列 {self.name} 为空，等待超时")
            item = self._deque.popleft()
            self._pending_keys.discard(self._item_key(item))
            with self._not_full:
                self._not_full.notify()
            return item

    def get_nowait(self) -> Any:
        """非阻塞获取，队列空时抛出 Empty 异常。"""
        with self._not_empty:
            if not self._deque:
                raise Empty(f"队列 {self.name} 为空")
            item = self._deque.popleft()
            self._pending_keys.discard(self._item_key(item))
            with self._not_full:
                self._not_full.notify()
            return item

    def size(self) -> int:
        return len(self._deque)

    def empty(self) -> bool:
        return len(self._deque) == 0

    def close(self) -> None:
        """清空队列，释放资源"""
        with self._not_empty:
            self._deque.clear()
            self._pending_keys.clear()
            self._not_empty.notify_all()
        with self._not_full:
            self._not_full.notify_all()

    def __len__(self) -> int:
        return self.size()

    def __repr__(self) -> str:
        return f"MemoryQueue(name={self.name}, size={self.size()})"
