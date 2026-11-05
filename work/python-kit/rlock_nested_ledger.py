from threading import RLock

class ReceiptBalance:
    def __init__(self, opening_amount):
        self._lock = RLock()
        self._available = opening_amount

    def available(self):
        with self._lock:
            return self._available

    def reserve(self, amount):
        with self._lock:
            if type(amount) is not int or amount < 0 or amount > self.available():
                raise ValueError("invalid reservation")
            self._available -= amount
            return self._available

balance = ReceiptBalance(73)
print("remaining", balance.reserve(47))
try:
    balance.reserve(-1)
except ValueError:
    print("negative_rejected", True)
print("unchanged", balance.available())
