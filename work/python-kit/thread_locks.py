from concurrent.futures import ThreadPoolExecutor
from threading import Lock

class Stock:
    def __init__(self, available):
        self._available = available
        self._lock = Lock()
    def reserve_one(self):
        with self._lock:
            if self._available == 0:
                return False
            self._available -= 1
            return True
    def remaining(self):
        with self._lock:
            return self._available

stock = Stock(20)
with ThreadPoolExecutor(max_workers=4) as pool:
    accepted = list(pool.map(lambda _: stock.reserve_one(), range(30)))
print(sum(accepted), stock.remaining())
