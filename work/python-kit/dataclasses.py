from dataclasses import dataclass, FrozenInstanceError

@dataclass(frozen=True)
class ReceiptBatch:
    tenant: str
    identifier: int
    amounts: tuple[int, ...]

batch = ReceiptBatch("tenant-a", 41, (125, 75))
print(batch == ReceiptBatch("tenant-a", 41, (125, 75)))
print(sum(batch.amounts))
try:
    batch.identifier = 42
except FrozenInstanceError:
    print("field assignment rejected")
