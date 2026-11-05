from decimal import Decimal, Inexact, InvalidOperation, localcontext

def minor_units(text):
    if type(text) is not str or not 1 <= len(text) <= 12:
        raise ValueError("amount length")
    try:
        value = Decimal(text)
        if not value.is_finite() or not 0 <= value <= 10000:
            raise ValueError("amount range")
        with localcontext() as context:
            context.traps[Inexact] = True
            cents = value.quantize(Decimal("0.01"))
        return int(cents * 100)
    except (InvalidOperation, Inexact) as cause:
        raise ValueError("fractional minor unit") from cause

print(minor_units("12.50"))
print(minor_units("12.500"))
try:
    minor_units("12.501")
except ValueError:
    print("fractional cent rejected")
