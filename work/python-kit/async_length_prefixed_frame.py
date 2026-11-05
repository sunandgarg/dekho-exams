import asyncio

async def read_receipt_frame(reader, maximum_body):
    header = await reader.readexactly(2)
    body_size = int.from_bytes(header, "big")
    if body_size > maximum_body:
        raise ValueError("receipt body too large")
    return await reader.readexactly(body_size)

async def inspect_frames():
    complete = asyncio.StreamReader()
    complete.feed_data((7).to_bytes(2, "big") + b"R47paid")
    complete.feed_eof()
    print("accepted", (await read_receipt_frame(complete, 8)).decode("ascii"))

    oversized = asyncio.StreamReader()
    oversized.feed_data((73).to_bytes(2, "big"))
    oversized.feed_eof()
    try:
        await read_receipt_frame(oversized, 8)
    except ValueError:
        print("oversized_rejected", True)

    shortened = asyncio.StreamReader()
    shortened.feed_data((7).to_bytes(2, "big") + b"R73pa")
    shortened.feed_eof()
    try:
        await read_receipt_frame(shortened, 8)
    except asyncio.IncompleteReadError as failure:
        print("partial_rejected", failure.partial == b"R73pa")

asyncio.run(inspect_frames())
