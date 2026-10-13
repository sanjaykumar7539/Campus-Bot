import asyncio
from src.core.traffic_guard import TrafficGuard


def test_guard_rejects_when_queue_full():
    async def run():
        guard = TrafficGuard(max_concurrent=1, max_waiting=1, queue_timeout=0.05)
        assert await guard.acquire() is not None
        waiter = asyncio.create_task(guard.acquire())
        await asyncio.sleep(0.01)
        assert await guard.acquire() is None
        await guard.release()
        assert await waiter is not None
        await guard.release()
    asyncio.run(run())


def test_guard_snapshot_tracks_active():
    async def run():
        guard = TrafficGuard(max_concurrent=2, max_waiting=3, queue_timeout=0.1)
        await guard.acquire()
        snap = await guard.snapshot()
        assert snap.active == 1
        assert snap.max_concurrent == 2
        await guard.release()
    asyncio.run(run())
