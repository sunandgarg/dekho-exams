from collections import Counter, deque

recent_receipts = deque(maxlen=2)
for receipt_id in (41, 42, 43):
    recent_receipts.append(receipt_id)
outcomes = Counter(["accepted", "rejected", "accepted"])
print(list(recent_receipts))
print(sorted(outcomes.items()))
print(outcomes["missing"])
