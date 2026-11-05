import asyncio
from threading import Thread

async def collect_receipt():
    loop = asyncio.get_running_loop()
    delivered = asyncio.Event()
    receipts = []

    def accept_on_loop():
        receipts.append(47)
        delivered.set()

    worker = Thread(target=lambda: loop.call_soon_threadsafe(accept_on_loop))
    worker.start()
    await asyncio.wait_for(delivered.wait(), timeout=2)
    worker.join()
    print("receipts", receipts)

asyncio.run(collect_receipt())
