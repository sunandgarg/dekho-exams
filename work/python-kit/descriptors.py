class BoundedQuantity:
    def __set_name__(self, owner, name):
        self.storage = "_" + name
    def __get__(self, instance, owner=None):
        if instance is None:
            return self
        return instance.__dict__[self.storage]
    def __set__(self, instance, value):
        if type(value) is not int or not 0 <= value <= 1000:
            raise ValueError("quantity out of range")
        instance.__dict__[self.storage] = value

class DispatchLine:
    quantity = BoundedQuantity()
    def __init__(self, quantity):
        self.quantity = quantity

line = DispatchLine(12)
try:
    line.quantity = True
except ValueError:
    print("boolean rejected")
line.__dict__["quantity"] = 999
print(line.quantity)
print(isinstance(DispatchLine.quantity, BoundedQuantity))
