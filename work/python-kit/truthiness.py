def effective_discount(discount):
    if discount is None:
        return 25
    if type(discount) is not int or discount < 0:
        raise ValueError("discount rejected")
    return discount

print("or default:", 0 or 25)
print("explicit zero:", effective_discount(0))
print("missing default:", effective_discount(None))
print("selected operand:", "DEL" and "accepted")
try:
    effective_discount(False)
except ValueError:
    print("boolean amount rejected")
