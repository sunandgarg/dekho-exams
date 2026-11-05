import asyncio

async def trace():
    started, release = asyncio.Event(), asyncio.Event()
    retained = []
    async def persist():
        started.set()
        await release.wait()
        return "stored"
    async def caller():
        task = asyncio.create_task(persist())
        retained.append(task)
        try:
            await asyncio.shield(task)
        except asyncio.CancelledError:
            print("caller cancelled")
            raise
    request = asyncio.create_task(caller())
    await started.wait()
    request.cancel()
    try:
        await request
    except asyncio.CancelledError:
        pass
    print("inner pending:", not retained[0].done())
    release.set()
    print("inner result:", await retained[0])

asyncio.run(trace())
