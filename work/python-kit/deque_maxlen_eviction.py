from collections import deque

recent_receipts = deque(["R-47", "R-48", "R-49"], maxlen=3)
recent_receipts.append("R-50")
print("after_new", list(recent_receipts))
recent_receipts.appendleft("R-46")
print("after_correction", list(recent_receipts))
print("capacity", recent_receipts.maxlen)
