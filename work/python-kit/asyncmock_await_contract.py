import asyncio
from unittest.mock import AsyncMock

async def accept_receipt(identifier, writer):
    await writer(identifier)
    return "accepted"

async def main():
    writer = AsyncMock()
    print(await accept_receipt("R41", writer))
    writer.assert_awaited_once_with("R41")
    print("awaited:", writer.await_count)
    unused = AsyncMock()
    pending = unused("R42")
    print("called but not awaited:", unused.call_count, unused.await_count)
    pending.close()

asyncio.run(main())
