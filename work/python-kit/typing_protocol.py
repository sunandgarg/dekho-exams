from typing import Protocol

class ReceiptStore(Protocol):
    def amount(self, receipt_id: int) -> int: ...
class MemoryReceipts:
    def amount(self, receipt_id: int) -> int:
        return {41: 125}[receipt_id]

def render_amount(store: ReceiptStore, receipt_id: int) -> str:
    amount = store.amount(receipt_id)
    if type(amount) is not int or amount < 0:
        raise ValueError("invalid minor-unit amount")
    return f"R{receipt_id}:{amount}"

print(render_amount(MemoryReceipts(), 41))
