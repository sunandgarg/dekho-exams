import asyncio

async def review():
    permit = asyncio.Semaphore(1)
    started, blocked = asyncio.Event(), asyncio.Event()
    trace = []
    async def worker():
        async with permit:
            started.set()
            try:
                await blocked.wait()
            finally:
                trace.append("cleanup")
    task = asyncio.create_task(worker())
    await started.wait()
    task.cancel()
    try:
        await task
    except asyncio.CancelledError:
        trace.append("cancelled")
    async with permit:
        trace.append("next acquired")
    print(trace)
    print("permit available:", not permit.locked())

asyncio.run(review())
