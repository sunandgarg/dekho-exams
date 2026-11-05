def merge_reservations(ranges):
    if type(ranges) is not list or len(ranges) > 100 or any(type(row) is not tuple or len(row) != 2 or any(type(value) is not int for value in row) or not 0 <= row[0] < row[1] <= 1000 for row in ranges):
        raise ValueError("bounded half-open ranges")
    merged = []
    for start, end in sorted(ranges):
        if merged and start < merged[-1][1]:
            merged[-1] = (merged[-1][0], max(end, merged[-1][1]))
        else:
            merged.append((start, end))
    return merged

print(merge_reservations([(0, 3), (2, 5), (5, 7)]))
try:
    merge_reservations([(4, 4)])
except ValueError:
    print("empty range rejected")
