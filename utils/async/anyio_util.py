"""
AnyIO 工具类
pip install anyio

# 并发执行任务
async def say(name, seconds):
    print(f"{name} start")
    await anyio.sleep(seconds)
    print(f"{name} done")

async with anyio.create_task_group() as task_group:
    task_group.start_soon(say, "task1", 1)
    task_group.start_soon(say, "task2", 2)

# 限制并发数量：用 CapacityLimiter 限制并发任务数
limiter = anyio.CapacityLimiter(2)

async with anyio.create_task_group() as task_group:
    for i in range(5):
        async with limiter:
            task_group.start_soon(say, f"task{i}", 1)

# 取消任务示例
async def main():
    async with anyio.create_task_group() as task_group:
        task_group.start_soon(say, "task1", 2)
        await anyio.sleep(1)
        task_group.cancel_scope.cancel()  # 取消所有子任务
"""
import asyncio
import logging
import threading
from typing import Callable, Any, Coroutine

import anyio
from anyio.abc import TaskGroup

class AnyIOUtil:

    GLOBAL_TASK_GROUP: TaskGroup | None = None
    _LIMITER = anyio.CapacityLimiter(40)

    @classmethod
    async def run_sync(cls, sync_func: Callable[..., Any], *args, **kwargs) -> Any:
        """
        在异步环境中安全调用同步函数，不阻塞事件循环。
        """
        return await anyio.to_thread.run_sync(sync_func, *args, limiter=cls._LIMITER, **kwargs)

    @classmethod
    def run_async(cls, coro_func: Callable[..., Coroutine], *args, **kwargs) -> Any:
        """
        在同步环境中安全调用 async 函数。

        - 如果当前线程有事件循环（FastAPI sync 接口、Jupyter） → 使用 from_thread.run
        - 如果没有事件循环 → 使用 anyio.run 创建新的 loop
        """
        try:
            return anyio.from_thread.run(coro_func, *args, **kwargs)
        except RuntimeError:
            return anyio.run(coro_func, *args, **kwargs)

    @classmethod
    def fire_and_forget(cls, coro_func: Callable[..., Coroutine], *args, **kwargs) -> None:
        """
        启动一个协程任务，且不等待其结束
        :param coro_func:
        :param args:
        :param kwargs:
        :return:
        """
        async def _safe_run():
            try:
                await coro_func(*args, **kwargs)
            except Exception as e:
                logging.error(f"fire_and_forget task failed: {e}", exc_info=True)

        try:
            if cls.GLOBAL_TASK_GROUP is not None:
                cls.GLOBAL_TASK_GROUP.start_soon(_safe_run)
            else:
                asyncio.create_task(_safe_run())
        except RuntimeError:
            threading.Thread(target=lambda: anyio.run(_safe_run), daemon=True).start()
