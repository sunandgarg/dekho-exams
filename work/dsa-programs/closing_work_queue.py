from collections import deque
from threading import Condition


class QueueClosed(Exception):
    pass


class ClosingWorkQueue:
    def __init__(self, capacity):
        if capacity < 1:
            raise ValueError("capacity must be positive")
        self.capacity = capacity
        self.jobs = deque()
        self.closed = False
        self.changed = Condition()

    def offer(self, job_id, wait=True):
        if job_id is None:
            raise ValueError("None is reserved for drained closure")
        with self.changed:
            while len(self.jobs) == self.capacity and not self.closed:
                if not wait:
                    return False
                self.changed.wait()
            if self.closed:
                raise QueueClosed("queue is closed")
            self.jobs.append(job_id)
            self.changed.notify()
            return True

    def take(self):
        with self.changed:
            while not self.jobs and not self.closed:
                self.changed.wait()
            if not self.jobs:
                return None
            job_id = self.jobs.popleft()
            self.changed.notify()
            return job_id

    def close(self):
        with self.changed:
            self.closed = True
            self.changed.notify_all()


intake = ClosingWorkQueue(2)
intake.offer("J-47")
intake.offer("J-52")
print(intake.offer("J-61", wait=False))
intake.close()
print(intake.take(), intake.take(), intake.take())
try:
    intake.offer("J-83")
except QueueClosed:
    print("closed")
