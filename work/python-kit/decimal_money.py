from decimal import Decimal, localcontext, ROUND_HALF_UP

def invoice_amount(text):
    if len(text) > 24:
        raise ValueError("amount too long")
    with localcontext() as context:
        context.prec = 28
        amount = Decimal(text)
        if not amount.is_finite():
            raise ValueError("finite amount required")
        return amount.quantize(Decimal("0.01"), rounding=ROUND_HALF_UP)

print(invoice_amount("12.345"))
try:
    invoice_amount("NaN")
except ValueError:
    print("non-finite amount rejected")
