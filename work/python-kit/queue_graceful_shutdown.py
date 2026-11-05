from queue import Queue, ShutDown
from threading import Thread

receipts = Queue(maxsize=3)
processed = []

def write_receipts():
    while True:
        try:
            receipt_id = receipts.get()
        except ShutDown:
            return
        try:
            processed.append(receipt_id)
        finally:
            receipts.task_done()

worker = Thread(target=write_receipts)
worker.start()
for receipt_id in ("north-47", "north-48"):
    receipts.put(receipt_id)
receipts.shutdown()
receipts.join()
worker.join()
try:
    receipts.put("north-49")
except ShutDown:
    print("late_rejected", True)
print("processed", sorted(processed))
