from itertools import batched

accepted_ids = (f"receipt-{number}" for number in range(47, 53))
groups = list(batched(accepted_ids, 3, strict=True))
print("groups", len(groups))
print("first", groups[0])

incomplete_ids = (f"receipt-{number}" for number in range(47, 54))
complete_before_error = 0
try:
    for settlement_group in batched(incomplete_ids, 3, strict=True):
        complete_before_error += 1
except ValueError:
    print("complete_before_error", complete_before_error)
