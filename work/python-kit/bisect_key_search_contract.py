from bisect import bisect_left, insort_left

receipts = [
    {"due_day": 12, "receipt": "R-12"},
    {"due_day": 47, "receipt": "R-47"},
    {"due_day": 73, "receipt": "R-73"},
]
due_day = lambda receipt: receipt["due_day"]
print("found_at", bisect_left(receipts, 47, key=due_day))
insort_left(receipts, {"due_day": 26, "receipt": "R-26"}, key=due_day)
print("ordered_days", [receipt["due_day"] for receipt in receipts])
