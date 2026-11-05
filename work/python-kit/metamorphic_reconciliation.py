def receipt_total(amounts):
    if type(amounts) is not list or len(amounts) > 20 or any(type(amount) is not int or not 0 <= amount <= 1000 for amount in amounts):
        raise ValueError("bounded minor units")
    return sum(amounts)

batch = [125, 75, 50]
base = receipt_total(batch)
print("known total:", base)
print("reorder invariant:", receipt_total(list(reversed(batch))) == base)
print("append relation:", receipt_total(batch + [30]) == base + 30)
try:
    receipt_total([True])
except ValueError:
    print("boolean amount rejected")
