import asyncio

async def wait_for_receipt():
    gate = asyncio.Event()
    try:
        async with asyncio.timeout(0):
            await gate.wait()
    except TimeoutError:
        return "lookup timed out"
    return "receipt arrived"

print(asyncio.run(wait_for_receipt()))
