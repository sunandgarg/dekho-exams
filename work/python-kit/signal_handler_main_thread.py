import signal
from threading import Thread

observed = []

def request_shutdown(signal_number, frame):
    observed.append(signal_number)

def worker_registration():
    try:
        signal.signal(signal.SIGINT, request_shutdown)
    except ValueError:
        observed.append("worker_rejected")

worker = Thread(target=worker_registration)
worker.start()
worker.join()
previous = signal.signal(signal.SIGINT, request_shutdown)
signal.signal(signal.SIGINT, previous)
print("worker_rejected", "worker_rejected" in observed)
print("main_restored", signal.getsignal(signal.SIGINT) == previous)
