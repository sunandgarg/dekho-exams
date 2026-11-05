def lower_bound(timestamps, target):
    if len(timestamps) > 10000:
        raise ValueError("sequence too large")
    left, right = 0, len(timestamps)
    while left < right:
        middle = (left + right) // 2
        if timestamps[middle] < target:
            left = middle + 1
        else:
            right = middle
    return left

print(lower_bound([10, 20, 20, 30], 20))
print(lower_bound([10, 20, 20, 30], 40))
print(lower_bound([], 20))
