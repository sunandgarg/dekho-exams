class StockItem:
    def __init__(self, quantity):
        self.quantity = quantity

    @property
    def quantity(self):
        return self._quantity

    @quantity.setter
    def quantity(self, value):
        if type(value) is not int or value < 0:
            raise ValueError("nonnegative integer required")
        self._quantity = value

stock = StockItem(8)
try:
    stock.quantity = -1
except ValueError:
    print("update rejected")
print(stock.quantity)
