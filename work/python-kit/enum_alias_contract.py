from enum import Enum, unique

class ReceiptStatus(Enum):
    PENDING = "pending"
    NEW = "pending"
    POSTED = "posted"

print("iteration:", [member.name for member in ReceiptStatus])
print("declared:", list(ReceiptStatus.__members__))
print("alias identity:", ReceiptStatus.NEW is ReceiptStatus.PENDING)
print("alias canonical name:", ReceiptStatus["NEW"].name)
try:
    unique(ReceiptStatus)
except ValueError:
    print("duplicate values rejected")
