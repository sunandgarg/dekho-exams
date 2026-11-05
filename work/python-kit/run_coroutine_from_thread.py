import asyncio
from threading import Event, Thread

async def calculate_receipt_total():
    return 47 + 26

loop = asyncio.new_event_loop()
ready = Event()

def run_receipt_loop():
    asyncio.set_event_loop(loop)
    ready.set()
    loop.run_forever()

worker = Thread(target=run_receipt_loop)
worker.start()
try:
    if not ready.wait(timeout=2):
        raise TimeoutError("loop did not start")
    result = asyncio.run_coroutine_threadsafe(calculate_receipt_total(), loop)
    print("total", result.result(timeout=2))
finally:
    loop.call_soon_threadsafe(loop.stop)
    worker.join(timeout=2)
    if worker.is_alive():
        raise TimeoutError("loop did not stop")
    loop.close()
