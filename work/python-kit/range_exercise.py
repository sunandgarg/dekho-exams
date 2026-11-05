def prefix_totals(amounts):
    if len(amounts) > 128 or any(type(amount) is not int for amount in amounts):
        raise ValueError("bounded integer amounts required")
    prefix = [0]
    for amount in amounts:
        prefix.append(prefix[-1] + amount)
    return prefix

def interval_total(prefix, left, right):
    count = len(prefix) - 1
    if any(type(index) is not int for index in (left, right)) or not 0 <= left <= right <= count:
        raise ValueError("invalid half-open interval")
    return prefix[right] - prefix[left]

amounts = [125, 250, 75]
prefix = prefix_totals(amounts)
print(prefix)
print(interval_total(prefix, 1, 3))
print(interval_total(prefix, 2, 2))
amounts[0] = 999
print("snapshot total:", interval_total(prefix, 0, 3))
