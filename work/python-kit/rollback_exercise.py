def adjusted_stock(stock, changes):
    if len(changes) > 32 or any(type(value) is not int or not 0 <= value <= 1000 for value in stock.values()):
        raise ValueError("stock budget")
    candidate = stock.copy()
    for label, delta in changes:
        if label not in candidate or type(delta) is not int or abs(delta) > 1000:
            raise ValueError("invalid adjustment")
        quantity = candidate[label] + delta
        if not 0 <= quantity <= 1000:
            raise ValueError("quantity out of range")
        candidate[label] = quantity
    return candidate

stock = {"paper": 12, "ink": 4}
try:
    adjusted_stock(stock, [("paper", -2), ("ink", -5)])
except ValueError:
    print("batch rejected")
print(stock)
print(adjusted_stock(stock, [("paper", -2)]))
