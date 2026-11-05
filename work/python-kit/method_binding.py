class Receipt:
    def __init__(self, quantity):
        self.quantity = self.validate_quantity(quantity)
    @staticmethod
    def validate_quantity(quantity):
        if type(quantity) is not int or not 1 <= quantity <= 20:
            raise ValueError("quantity rejected")
        return quantity
    @classmethod
    def from_quantity(cls, quantity):
        return cls(quantity)
    def amount(self, unit_minor):
        return self.quantity * unit_minor

class ExpressReceipt(Receipt):
    pass

receipt = ExpressReceipt.from_quantity(3)
print(type(receipt).__name__)
print(receipt.amount(125))
print(Receipt.validate_quantity(2))
