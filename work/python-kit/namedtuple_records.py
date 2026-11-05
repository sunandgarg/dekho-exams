from collections import namedtuple

ReceiptSummary = namedtuple("ReceiptSummary", "receipt_id tags")
original = ReceiptSummary("R-0041", ("checked",))
updated = original._replace(receipt_id="R-0042")
print(original.receipt_id, updated.receipt_id)
mutable = ReceiptSummary("R-0043", [])
mutable.tags.append("packed")
print(mutable.tags)
try:
    mutable.receipt_id = "R-0044"
except AttributeError:
    print("field assignment rejected")
