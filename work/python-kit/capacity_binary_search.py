def minimum_daily_capacity(weights, days):
    if type(weights) is not list or not 1 <= len(weights) <= 100 or any(type(weight) is not int or not 1 <= weight <= 1000 for weight in weights):
        raise ValueError("shipment weights")
    if type(days) is not int or not 1 <= days <= len(weights):
        raise ValueError("day count")
    def feasible(capacity):
        used, load = 1, 0
        for weight in weights:
            if load + weight > capacity:
                used += 1
                load = 0
            load += weight
        return used <= days
    low, high = max(weights), sum(weights)
    while low < high:
        middle = (low + high) // 2
        if feasible(middle):
            high = middle
        else:
            low = middle + 1
    return low

print(minimum_daily_capacity([3, 2, 2, 4, 1], 3))
try:
    minimum_daily_capacity([3, 2], True)
except ValueError:
    print("day count rejected")
