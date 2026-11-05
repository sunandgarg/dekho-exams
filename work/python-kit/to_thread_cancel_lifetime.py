import asyncio
from threading import Event

started = Event()
release = Event()
finished = Event()

def blocking_receipt_export():
    started.set()
    release.wait(timeout=5)
    finished.set()
    return "R-47"

async def cancel_export_awaiter():
    export_task = asyncio.create_task(asyncio.to_thread(blocking_receipt_export))
    try:
        if not await asyncio.to_thread(started.wait, 2):
            raise TimeoutError("export did not start")
        export_task.cancel()
        try:
            await export_task
        except asyncio.CancelledError:
            print("awaiter_cancelled", True)
        print("worker_still_blocked", not finished.is_set())
    finally:
        release.set()
    if not await asyncio.to_thread(finished.wait, 2):
        raise TimeoutError("export did not finish")
    print("worker_finished", finished.is_set())

asyncio.run(cancel_export_awaiter())
