"""
基于文件持久化的本地队列（带去重）

底层使用 SQLite 存储，重启后数据不丢失，线程安全。
利用 SQLite UNIQUE 约束实现未消费消息去重，消费后可再次入队。

使用示例：
    from file_queue import FileQueue

    q = FileQueue(name="tasks", dir_path="/tmp/queues")
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
import os
import sqlite3
import threading
import time
from queue import Empty
from typing import Any, Callable, Optional


class FileQueue:
    """基于 SQLite 的持久化队列，支持未消费消息去重"""

    def __init__(self, name: str = "default", dir_path: str = "/tmp/local_queue",
                 key_func: Optional[Callable[[Any], str]] = None):
        """
        Args:
            name:       队列名称，同时作为 SQLite 表名
            dir_path:   SQLite 数据库文件存放目录
            key_func:   去重键提取函数，默认用 str(item)
                        可自定义，如 key_func=lambda x: x["id"]
        """
        self.name = name
        self._key_func = key_func or (lambda item: str(item))
        os.makedirs(dir_path, exist_ok=True)
        self._db_path = os.path.join(dir_path, f"{name}.db")
        self._lock = threading.Lock()
        self._not_empty = threading.Condition(threading.Lock())
        self._conn = self._create_connection()
        self._init_table()

    def _create_connection(self) -> sqlite3.Connection:
        conn = sqlite3.connect(self._db_path, check_same_thread=False)
        conn.execute("PRAGMA journal_mode=WAL")
        conn.execute("PRAGMA synchronous=NORMAL")
        return conn

    def _init_table(self) -> None:
        with self._lock:
            self._conn.execute(
                f"CREATE TABLE IF NOT EXISTS {self.name} "
                f"(id INTEGER PRIMARY KEY AUTOINCREMENT, "
                f"key TEXT NOT NULL UNIQUE, "
                f"data TEXT NOT NULL)"
            )
            self._conn.commit()

    @staticmethod
    def _serialize(item: Any) -> str:
        return json.dumps(item, ensure_ascii=False)

    @staticmethod
    def _deserialize(data: str) -> Any:
        return json.loads(data)

    def _item_key(self, item: Any) -> str:
        return self._key_func(item)

    def put(self, item: Any) -> bool:
        """
        放入元素并持久化。如果该消息已在队列中未被消费，则过滤不入队。

        Returns:
            True  - 入队成功
            False - 重复消息被过滤
        """
        key = self._item_key(item)
        data = self._serialize(item)
        with self._lock:
            try:
                self._conn.execute(
                    f"INSERT INTO {self.name} (key, data) VALUES (?, ?)", (key, data)
                )
                self._conn.commit()
            except sqlite3.IntegrityError:
                return False
        with self._not_empty:
            self._not_empty.notify()
        return True

    def get(self, timeout: Optional[float] = None) -> Any:
        """阻塞获取元素。超时抛出 Empty 异常。"""
        deadline = None if timeout is None else time.monotonic() + timeout
        while True:
            try:
                return self.get_nowait()
            except Empty:
                remaining = None
                if deadline is not None:
                    remaining = deadline - time.monotonic()
                    if remaining <= 0:
                        raise Empty(f"队列 {self.name} 为空，等待超时")
                with self._not_empty:
                    self._not_empty.wait(timeout=remaining)

    def get_nowait(self) -> Any:
        """非阻塞获取，队列空时抛出 Empty 异常。"""
        with self._lock:
            cursor = self._conn.execute(
                f"SELECT id, data FROM {self.name} ORDER BY id LIMIT 1"
            )
            row = cursor.fetchone()
            if row is None:
                raise Empty(f"队列 {self.name} 为空")
            row_id, data = row
            self._conn.execute(
                f"DELETE FROM {self.name} WHERE id = ?", (row_id,)
            )
            self._conn.commit()
        return self._deserialize(data)

    def size(self) -> int:
        with self._lock:
            cursor = self._conn.execute(f"SELECT COUNT(*) FROM {self.name}")
            return cursor.fetchone()[0]

    def empty(self) -> bool:
        return self.size() == 0

    def close(self) -> None:
        """关闭数据库连接，释放资源"""
        with self._not_empty:
            self._not_empty.notify_all()
        try:
            self._conn.close()
        except Exception:
            pass

    def __len__(self) -> int:
        return self.size()

    def __repr__(self) -> str:
        return f"FileQueue(name={self.name}, size={self.size()}, db={self._db_path})"
