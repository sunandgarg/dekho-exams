from concurrent.futures import ThreadPoolExecutor
from threading import local

worker_state = local()

def record_receipt():
    worker_state.receipt_id = "R-47"
    return worker_state.receipt_id

def inspect_next_job():
    previous = getattr(worker_state, "receipt_id", None)
    if hasattr(worker_state, "receipt_id"):
        del worker_state.receipt_id
    return previous, getattr(worker_state, "receipt_id", None)

with ThreadPoolExecutor(max_workers=1) as pool:
    print("first", pool.submit(record_receipt).result())
    print("next", pool.submit(inspect_next_job).result())
