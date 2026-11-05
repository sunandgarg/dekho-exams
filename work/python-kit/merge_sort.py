def sort_receipts(receipts):
    if len(receipts) > 128 or any(type(amount) is not int or type(identifier) is not str for amount, identifier in receipts):
        raise ValueError("bounded receipt pairs required")
    def sort_run(records):
        if len(records) < 2:
            return records.copy()
        middle = len(records) // 2
        left, right = sort_run(records[:middle]), sort_run(records[middle:])
        merged, left_index, right_index = [], 0, 0
        while left_index < len(left) and right_index < len(right):
            if left[left_index][0] <= right[right_index][0]:
                merged.append(left[left_index]); left_index += 1
            else:
                merged.append(right[right_index]); right_index += 1
        return merged + left[left_index:] + right[right_index:]
    return sort_run(receipts)

receipts = [(125, "R41"), (75, "R42"), (125, "R43")]
print(sort_receipts(receipts))
print(receipts)
