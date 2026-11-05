from concurrent.futures import ThreadPoolExecutor
from threading import Event

started = Event()
release = Event()

def export_ledger():
    started.set()
    release.wait()
    return "ledger-ready"

with ThreadPoolExecutor(max_workers=1) as workers:
    running = workers.submit(export_ledger)
    started.wait()
    pending = workers.submit(lambda: "second-export")
    print("pending cancelled:", pending.cancel())
    release.set()
    print("running result:", running.result())
    print("second cancelled:", pending.cancelled())
