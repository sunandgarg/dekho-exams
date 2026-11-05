from bisect import bisect_left

def increasing_subsequence(amounts):
    if type(amounts) is not list or len(amounts) > 128 or any(type(amount) is not int or not -1000000 <= amount <= 1000000 for amount in amounts):
        raise ValueError("bounded exact integers required")
    tails, positions, previous = [], [], [-1] * len(amounts)
    for index, amount in enumerate(amounts):
        length_index = bisect_left(tails, amount)
        if length_index:
            previous[index] = positions[length_index - 1]
        if length_index == len(tails):
            tails.append(amount)
            positions.append(index)
        else:
            tails[length_index] = amount
            positions[length_index] = index
    result = []
    cursor = positions[-1] if positions else -1
    while cursor != -1:
        result.append(amounts[cursor])
        cursor = previous[cursor]
    return list(reversed(result))

print("selected:", increasing_subsequence([300, 100, 200, 200, 400, 250]))
print("duplicates:", increasing_subsequence([125, 125, 125]))
print("empty:", increasing_subsequence([]))
