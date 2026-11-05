class ParcelRecord:
    __slots__ = ("receipt_id", "quantity")
    def __init__(self, receipt_id, quantity):
        self.receipt_id = receipt_id
        self.quantity = quantity

parcel = ParcelRecord("R-0041", 2)
parcel.quantity = 3
print(parcel.quantity)
print(hasattr(parcel, "__dict__"))
try:
    parcel.quanity = 4
except AttributeError:
    print("unknown attribute rejected")
