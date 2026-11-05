import asyncio

async def reject_receipt():
    raise ValueError("invalid receipt")

async def delayed_receipt(gate):
    await gate.wait()
    return "R42 stored"

async def main():
    gate = asyncio.Event()
    sibling = asyncio.create_task(delayed_receipt(gate))
    try:
        await asyncio.gather(reject_receipt(), sibling)
    except ValueError:
        print("sibling pending:", not sibling.done())
    gate.set()
    print("sibling result:", await sibling)

asyncio.run(main())
