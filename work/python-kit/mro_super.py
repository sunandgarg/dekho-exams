class BasePolicy:
    def tags(self):
        return ["base"]
class ReceiptPolicy(BasePolicy):
    def tags(self):
        return super().tags() + ["receipt"]
class AuditPolicy(BasePolicy):
    def tags(self):
        return super().tags() + ["audit"]
class DispatchPolicy(AuditPolicy, ReceiptPolicy):
    pass

print([kind.__name__ for kind in DispatchPolicy.__mro__[:-1]])
print(DispatchPolicy().tags())
