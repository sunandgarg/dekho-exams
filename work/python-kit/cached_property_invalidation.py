from functools import cached_property

class Invoice:
    def __init__(self, amounts):
        self.computations = 0
        self.replace(amounts)
    def replace(self, amounts):
        candidate = tuple(amounts)
        if len(candidate) > 20 or any(type(amount) is not int or not 0 <= amount <= 1000 for amount in candidate):
            raise ValueError("bounded minor units")
        self.amounts = candidate
        self.__dict__.pop("total", None)
    @cached_property
    def total(self):
        self.computations += 1
        return sum(self.amounts)

invoice = Invoice([125, 75])
print(invoice.total, invoice.total, invoice.computations)
invoice.replace([125, 100])
print(invoice.total, invoice.computations)
