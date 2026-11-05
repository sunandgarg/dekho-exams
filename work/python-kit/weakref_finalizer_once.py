import weakref

class ReceiptLease:
    pass

released_receipts = []
lease = ReceiptLease()
cleanup = weakref.finalize(lease, released_receipts.append, "R-47")
print("registered", cleanup.alive)
cleanup()
cleanup()
print("released", released_receipts)
print("still_live", cleanup.alive)
