from queue import Queue
from threading import Thread

jobs = Queue()
processed = []

def print_receipts():
    while True:
        receipt_id = jobs.get()
        try:
            if receipt_id is None:
                return
            processed.append(receipt_id)
        finally:
            jobs.task_done()

worker = Thread(target=print_receipts)
worker.start()
for receipt_id in ("R-47", "R-48"):
    jobs.put(receipt_id)
jobs.put(None)
jobs.join()
worker.join()
print("processed:", processed)
print("unfinished:", jobs.unfinished_tasks)
