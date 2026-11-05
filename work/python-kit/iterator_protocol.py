class ReceiptBatch:
    def __init__(self, receipt_ids):
        candidate = tuple(receipt_ids)
        if any(type(identifier) is not int or identifier <= 0 for identifier in candidate):
            raise ValueError("positive receipt IDs required")
        self._receipt_ids = candidate
    def __iter__(self):
        return iter(self._receipt_ids)

batch = ReceiptBatch([41, 42])
reader = iter(batch)
print(list(reader))
print(list(reader))
print(list(batch))
