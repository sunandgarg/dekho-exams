class InventoryLedger:
    def __init__(self):
        self._stock = {"paper": 8, "ink": 4}

    def apply(self, changes):
        if len(changes) > 100:
            raise ValueError("batch too large")
        candidate = self._stock.copy()
        for item, change in changes:
            if item not in candidate or type(change) is not int:
                raise ValueError("known item and integer change required")
            next_quantity = candidate[item] + change
            if next_quantity < 0:
                raise ValueError("negative stock")
            candidate[item] = next_quantity
        self._stock = candidate

    def snapshot(self):
        return self._stock.copy()

ledger = InventoryLedger()
try:
    ledger.apply([("paper", -2), ("ink", -9)])
except ValueError:
    print("batch rejected")
print(ledger.snapshot())
ledger.apply([("paper", -2), ("ink", 1)])
print(ledger.snapshot())
