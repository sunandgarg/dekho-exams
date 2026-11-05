from decimal import Decimal, Inexact, ROUND_HALF_UP, getcontext, localcontext

prior_rounding = getcontext().rounding
with localcontext(rounding=ROUND_HALF_UP) as receipt_policy:
    rounded = Decimal("47.245").quantize(Decimal("0.01"))
    was_inexact = receipt_policy.flags[Inexact]

print("rounded", rounded)
print("inexact", was_inexact)
print("rounding_restored", getcontext().rounding == prior_rounding)
