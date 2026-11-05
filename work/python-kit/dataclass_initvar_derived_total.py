from dataclasses import InitVar, dataclass, field, fields, replace

@dataclass(frozen=True)
class ReceiptCharge:
    subtotal_cents: int
    service_percent: InitVar[int]
    total_cents: int = field(init=False)

    def __post_init__(self, service_percent):
        if type(self.subtotal_cents) is not int or self.subtotal_cents < 0:
            raise ValueError("invalid subtotal")
        if type(service_percent) is not int or not 0 <= service_percent <= 20:
            raise ValueError("invalid percentage")
        numerator = self.subtotal_cents * service_percent
        if numerator % 100:
            raise ValueError("fractional cent needs a rounding rule")
        object.__setattr__(self, "total_cents", self.subtotal_cents + numerator // 100)

charge = ReceiptCharge(4700, service_percent=6)
print("total", charge.total_cents)
print("stored_fields", [item.name for item in fields(charge)])
updated = replace(charge, service_percent=8)
print("replaced_total", updated.total_cents)
