from fractions import Fraction

def allocation(amount, numerator, denominator):
    if any(type(value) is not int for value in (amount, numerator, denominator)):
        raise ValueError("exact integer fields")
    if not 0 <= amount <= 100000 or not 0 <= numerator <= denominator <= 1000 or denominator == 0:
        raise ValueError("allocation bounds")
    return amount * Fraction(numerator, denominator)

print("allocation:", allocation(125, 3, 10))
print("text exact:", Fraction("0.1") == Fraction(1, 10))
print("float exact:", Fraction(0.1) == Fraction(1, 10))
print("approximation:", Fraction(0.1).limit_denominator(10))
try:
    allocation(125, 1, 0)
except ValueError:
    print("zero denominator rejected")
