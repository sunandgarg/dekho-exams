def first_seen(receipt_ids):
    if type(receipt_ids) is not list or len(receipt_ids) > 100:
        raise ValueError("batch cap")
    if any(type(identifier) is not str or len(identifier) != 3 or identifier[0] != "R" or any(char not in "0123456789" for char in identifier[1:]) for identifier in receipt_ids):
        raise ValueError("ASCII receipt ID")
    seen = set()
    ordered = []
    duplicates = 0
    for identifier in receipt_ids:
        if identifier in seen:
            duplicates += 1
        else:
            seen.add(identifier)
            ordered.append(identifier)
    return ordered, duplicates

batch = ["R42", "R41", "R42", "R43", "R41"]
print(first_seen(batch))
print("input kept:", batch[0])
