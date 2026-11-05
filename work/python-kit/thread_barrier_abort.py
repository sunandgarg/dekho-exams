from threading import Barrier, BrokenBarrierError, Event, Thread

phase_gate = Barrier(2)
worker_entered = Event()
worker_outcomes = []

def await_receipt_phase():
    worker_entered.set()
    try:
        phase_gate.wait(timeout=2)
    except BrokenBarrierError:
        worker_outcomes.append("released")

worker = Thread(target=await_receipt_phase)
worker.start()
if not worker_entered.wait(timeout=2):
    raise TimeoutError("worker did not start")
phase_gate.abort()
worker.join(timeout=2)
if worker.is_alive():
    raise TimeoutError("worker did not stop")
print("worker", worker_outcomes)
try:
    phase_gate.wait(timeout=2)
except BrokenBarrierError:
    print("later_wait_rejected", True)
print("broken", phase_gate.broken)
