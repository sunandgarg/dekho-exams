from abc import ABC, abstractmethod

class ReceiptWriter(ABC):
    @abstractmethod
    def publish(self, receipt):
        raise NotImplementedError

class MissingWriter(ReceiptWriter):
    pass

class LocalReceiptWriter(ReceiptWriter):
    def publish(self, receipt):
        return receipt["receipt_id"]

try:
    MissingWriter()
except TypeError:
    print("incomplete writer rejected")
print(LocalReceiptWriter().publish({"receipt_id": "R-0041"}))
