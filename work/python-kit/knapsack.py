def cargo_value(items, capacity):
    if type(capacity) is not int or not 0 <= capacity <= 256 or len(items) > 32:
        raise ValueError("cargo budget")
    if any(type(weight) is not int or type(value) is not int or weight <= 0 or value < 0 for weight, value in items):
        raise ValueError("positive weight and nonnegative value required")
    best = [0] * (capacity + 1)
    for weight, value in items:
        for available in range(capacity, weight - 1, -1):
            best[available] = max(best[available], best[available - weight] + value)
    return best[capacity]

print(cargo_value([(2, 6), (3, 8), (4, 9)], 5))
print(cargo_value([(2, 6)], 4))
