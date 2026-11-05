def merge_feeds(left, right):
    for feed in (left, right):
        if type(feed) is not list or len(feed) > 100 or any(type(value) is not int or not 0 <= value <= 1000 for value in feed) or any(a > b for a, b in zip(feed, feed[1:])):
            raise ValueError("sorted bounded integer feed")
    merged = []
    left_index = right_index = 0
    while left_index < len(left) or right_index < len(right):
        if right_index == len(right) or left_index < len(left) and left[left_index] <= right[right_index]:
            merged.append((left[left_index], "left"))
            left_index += 1
        else:
            merged.append((right[right_index], "right"))
            right_index += 1
    return merged

print(merge_feeds([10, 20, 20], [20, 30]))
try:
    merge_feeds([20, 10], [])
except ValueError:
    print("unsorted feed rejected")
