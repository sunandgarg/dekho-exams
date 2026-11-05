import asyncio

async def inspect_delimiter_limit():
    reader = asyncio.StreamReader(limit=8)
    reader.feed_data(b"receipt-47-untrusted\n")
    reader.feed_eof()
    try:
        await reader.readuntil(b"\n")
    except asyncio.LimitOverrunError:
        print("overrun_rejected", True)
    retained_prefix = await reader.readexactly(10)
    print("retained_prefix", retained_prefix.decode("ascii"))

asyncio.run(inspect_delimiter_limit())
