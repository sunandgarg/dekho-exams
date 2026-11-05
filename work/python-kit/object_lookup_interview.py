class CachedLabel:
    def __get__(self, instance, owner):
        return "class label"

class RequiredLabel:
    def __get__(self, instance, owner):
        return "required label"
    def __set__(self, instance, value):
        raise AttributeError("read-only label")

class ReceiptView:
    cached = CachedLabel()
    required = RequiredLabel()

receipt = ReceiptView()
receipt.__dict__["cached"] = "instance label"
receipt.__dict__["required"] = "attempted shadow"
print(receipt.cached)
print(receipt.required)
try:
    receipt.required = "replacement"
except AttributeError:
    print("normal assignment rejected")
