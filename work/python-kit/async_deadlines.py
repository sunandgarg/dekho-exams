import asyncio

async def inspect_timeout():
    released = False
    async def wait_for_receipt():
        nonlocal released
        try:
            await asyncio.Event().wait()
        finally:
            released = True
    try:
        async with asyncio.timeout(0.01):
            await wait_for_receipt()
    except TimeoutError:
        print("deadline expired")
    print("cleanup:", released)

asyncio.run(inspect_timeout())
