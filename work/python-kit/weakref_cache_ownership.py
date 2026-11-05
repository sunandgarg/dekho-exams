import gc
import weakref

class ReceiptSnapshot:
    def __init__(self, revision):
        self.revision = revision

snapshots = weakref.WeakValueDictionary()
current = ReceiptSnapshot(47)
snapshots["north-47"] = current
print("held", "north-47" in snapshots)
del current
gc.collect()
print("after_release", "north-47" in snapshots)
