from threading import Condition, Thread

condition = Condition()
slot, received = [], []
def consume():
    with condition:
        if not condition.wait_for(lambda: bool(slot), timeout=2):
            raise TimeoutError("receipt did not arrive")
        received.append(slot.pop())

consumer = Thread(target=consume)
consumer.start()
with condition:
    slot.append(125)
    condition.notify()
consumer.join(timeout=3)
if consumer.is_alive():
    raise RuntimeError("consumer did not finish")
print("received:", received)
print("empty slot:", slot == [])
