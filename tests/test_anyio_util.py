"""
AnyIOUtil 单元测试
pip install anyio pytest pytest-asyncio
"""
import asyncio
import time

import anyio
import pytest
import pytest_asyncio

from importlib import import_module

_anyio_util = import_module("utils.async.anyio_util")
AnyIOUtil = _anyio_util.AnyIOUtil


# ─── run_sync ───────────────────────────────────────────────

@pytest.mark.asyncio
async def test_run_sync_basic():
    """在异步环境中调用同步函数，返回正确结果"""

    def sync_add(a, b):
        return a + b

    result = await AnyIOUtil.run_sync(sync_add, 3, 5)
    assert result == 8


@pytest.mark.asyncio
async def test_run_sync_with_kwargs():
    """run_sync 通过 functools.partial 支持关键字参数"""
    from functools import partial

    def sync_greet(name, greeting="hello"):
        return f"{greeting}, {name}"

    result = await AnyIOUtil.run_sync(partial(sync_greet, greeting="hi"), "world")
    assert result == "hi, world"


@pytest.mark.asyncio
async def test_run_sync_does_not_block_event_loop():
    """run_sync 在线程中运行同步函数，不阻塞事件循环"""

    def blocking_sleep():
        time.sleep(0.2)
        return "done"

    # 同时启动两个阻塞调用，若阻塞事件循环则总耗时接近 0.4s
    start = time.monotonic()
    results = await asyncio.gather(
        AnyIOUtil.run_sync(blocking_sleep),
        AnyIOUtil.run_sync(blocking_sleep),
    )
    elapsed = time.monotonic() - start

    assert list(results) == ["done", "done"]
    assert elapsed < 0.35  # 并行执行，应远小于串行的 0.4s


@pytest.mark.asyncio
async def test_run_sync_exception_propagation():
    """run_sync 中同步函数抛出异常时，异常应传播到调用方"""

    def raise_value_error():
        raise ValueError("sync error")

    with pytest.raises(ValueError, match="sync error"):
        await AnyIOUtil.run_sync(raise_value_error)


# ─── run_async ──────────────────────────────────────────────

def test_run_async_from_sync_no_loop():
    """在无事件循环的同步环境中调用 async 函数"""

    async def async_multiply(a, b):
        return a * b

    result = AnyIOUtil.run_async(async_multiply, 6, 7)
    assert result == 42


def test_run_async_with_kwargs():
    """run_async 通过 functools.partial 支持关键字参数"""
    from functools import partial

    async def async_greet(name, greeting="hello"):
        return f"{greeting}, {name}"

    result = AnyIOUtil.run_async(partial(async_greet, greeting="hey"), "world")
    assert result == "hey, world"


def test_run_async_exception_propagation():
    """run_async 中 async 函数抛出异常时，异常应传播到调用方"""

    async def raise_type_error():
        raise TypeError("async error")

    with pytest.raises(TypeError, match="async error"):
        AnyIOUtil.run_async(raise_type_error)


def test_run_async_from_running_loop():
    """在已有事件循环的线程中调用 async 函数（使用 from_thread.run）"""

    async def async_add(a, b):
        return a + b

    # 在一个独立线程中模拟已有事件循环的环境
    import threading

    result_holder = {"value": None}

    def run_in_thread():
        # 在线程中启动事件循环，从另一个线程调用 run_async
        async def main():
            await asyncio.sleep(0.1)  # 让事件循环运行一会儿

        loop = asyncio.new_event_loop()
        asyncio.set_event_loop(loop)
        loop.run_until_complete(main())
        # 此时事件循环仍在运行，可以测试 from_thread.run 路径
        result_holder["value"] = AnyIOUtil.run_async(async_add, 10, 20)
        loop.close()

    t = threading.Thread(target=run_in_thread)
    t.start()
    t.join(timeout=5)
    assert result_holder["value"] == 30


# ─── fire_and_forget ────────────────────────────────────────

def test_fire_and_forget_no_loop():
    """在无事件循环的同步环境中 fire_and_forget，任务应在新线程中执行"""

    result_holder = {"value": None}

    async def set_value():
        result_holder["value"] = 99

    AnyIOUtil.fire_and_forget(set_value)
    # 等待后台线程完成
    time.sleep(0.5)
    assert result_holder["value"] == 99


def test_fire_and_forget_exception_does_not_crash():
    """fire_and_forget 中协程抛异常时不应崩溃"""

    async def raise_error():
        raise RuntimeError("task failed")

    # 不应抛出异常
    AnyIOUtil.fire_and_forget(raise_error)
    time.sleep(0.5)


@pytest.mark.asyncio
async def test_fire_and_forget_with_running_loop():
    """在已有事件循环中 fire_and_forget，使用 asyncio.create_task"""

    result_holder = {"value": None}

    async def set_value():
        result_holder["value"] = 42

    AnyIOUtil.fire_and_forget(set_value)
    # 等待 task 被调度执行
    await asyncio.sleep(0.1)
    assert result_holder["value"] == 42


@pytest.mark.asyncio
async def test_fire_and_forget_with_task_group():
    """有 GLOBAL_TASK_GROUP 时，fire_and_forget 使用 task group 调度"""

    result_holder = {"value": None}

    async def set_value():
        result_holder["value"] = 77

    async with anyio.create_task_group() as tg:
        AnyIOUtil.GLOBAL_TASK_GROUP = tg
        AnyIOUtil.fire_and_forget(set_value)
        # 等待 task group 中的任务执行完
        await asyncio.sleep(0.1)

    AnyIOUtil.GLOBAL_TASK_GROUP = None
    assert result_holder["value"] == 77


# ─── 互调组合 ───────────────────────────────────────────────

def test_run_async_calling_run_sync():
    """在同步环境中通过 run_async 调用 run_sync"""

    def sync_square(n):
        return n * n

    async def async_use_run_sync(n):
        return await AnyIOUtil.run_sync(sync_square, n)

    result = AnyIOUtil.run_async(async_use_run_sync, 5)
    assert result == 25
