class ReceiptKey:
    def __init__(self, identifier):
        self.identifier = identifier
    def __hash__(self):
        return hash(self.identifier)
    def __eq__(self, other):
        return type(other) is ReceiptKey and self.identifier == other.identifier

key = ReceiptKey("receipt-41")
ledger = {key: 125}
key.identifier = "receipt-42"
print("stored object:", next(iter(ledger)) is key)
print("stable replacement:", {("receipt-42",): 125}[("receipt-42",)])
