def charged_amount(amount):
    return amount + 25

def refunded_amount(amount):
    return amount

HANDLERS = {"charge": charged_amount, "refund": refunded_amount}
def dispatch(operation, amount):
    if not isinstance(operation, str) or operation not in HANDLERS:
        raise ValueError("operation rejected")
    if type(amount) is not int or not 0 <= amount <= 1000000:
        raise ValueError("amount rejected")
    return HANDLERS[operation](amount)

def with_fee(fee):
    def charge(amount):
        return amount + fee
    return charge

print(dispatch("charge", 125))
print(dispatch("refund", 125))
print(with_fee(40)(125))
try:
    dispatch("__import__", 125)
except ValueError:
    print("unknown operation rejected")
