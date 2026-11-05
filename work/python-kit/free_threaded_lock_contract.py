import sys
from threading import Lock, Thread

accepted_events = 0
event_lock = Lock()

def record_events():
    global accepted_events
    for _ in range(47):
        with event_lock:
            accepted_events += 1

workers = [Thread(target=record_events) for _ in range(4)]
for worker in workers:
    worker.start()
for worker in workers:
    worker.join()
print("gil_enabled", sys._is_gil_enabled())
print("accepted", accepted_events)
