import asyncio
from contextlib import AsyncExitStack, asynccontextmanager

events = []

@asynccontextmanager
async def receipt_lease(name, *, reject=False):
    if reject:
        raise ValueError("lease rejected")
    events.append("acquired:" + name)
    try:
        yield name
    finally:
        events.append("released:" + name)

async def prepare_receipt():
    try:
        async with AsyncExitStack() as resources:
            await resources.enter_async_context(receipt_lease("database"))
            await resources.enter_async_context(receipt_lease("queue"))
            await resources.enter_async_context(receipt_lease("export", reject=True))
    except ValueError:
        print("acquisition_rejected", True)
    print("events", events)

asyncio.run(prepare_receipt())
