from functools import Placeholder, partial

def invoice_balance(amount, fixed_fee, currency):
    return f"{currency} {amount - fixed_fee}"

quote_after_fee = partial(invoice_balance, Placeholder, 7, "INR")
print("balance", quote_after_fee(47))
try:
    quote_after_fee()
except TypeError:
    print("missing_amount_rejected", True)
