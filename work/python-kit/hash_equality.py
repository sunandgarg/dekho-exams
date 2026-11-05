from dataclasses import dataclass

@dataclass(frozen=True)
class ReceiptKey:
    region: str
    sequence: int

ledger = {ReceiptKey("DEL", 41): 1250}
lookup_key = ReceiptKey("DEL", 41)
print(ledger[lookup_key])
print(hash(lookup_key) == hash(ReceiptKey("DEL", 41)))
try:
    ledger[["DEL", 41]] = 1250
except TypeError:
    print("mutable list rejected as key")
