import asyncio

async def inspect_cancellation():
    started = asyncio.Event()
    never_released = asyncio.Event()
    cleanup = []
    async def worker():
        try:
            started.set()
            await never_released.wait()
        finally:
            cleanup.append("released")
    task = asyncio.create_task(worker())
    await started.wait()
    task.cancel()
    try:
        await task
    except asyncio.CancelledError:
        print("caller observed cancellation")
    print("cleanup:", cleanup)
    print("task finished:", task.done())

asyncio.run(inspect_cancellation())
