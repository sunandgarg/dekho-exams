import asyncio

async def import_batch():
    events = []
    started = asyncio.Event()
    async def waiting_import():
        started.set()
        try:
            await asyncio.Event().wait()
        finally:
            events.append("sibling cleaned")
    async def failed_import():
        await started.wait()
        raise ValueError("invalid receipt")
    try:
        async with asyncio.TaskGroup() as tasks:
            tasks.create_task(waiting_import())
            tasks.create_task(failed_import())
    except* ValueError:
        events.append("failure observed")
    print(events)

if __name__ == "__main__":
    asyncio.run(import_batch())
