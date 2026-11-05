import gc
from weakref import WeakValueDictionary

class ReceiptRecord:
    def __init__(self, receipt_id):
        self.receipt_id = receipt_id

cache = WeakValueDictionary()
owned_record = ReceiptRecord("R-0041")
cache[owned_record.receipt_id] = owned_record
print(cache.get("R-0041") is owned_record)
del owned_record
gc.collect()
print(cache.get("R-0041") is None)
