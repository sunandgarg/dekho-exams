from collections import deque

receipt_ids = ["R-0041", "R-0042"]
outer_snapshot = receipt_ids.copy()
known = set(receipt_ids)
amounts = {"R-0041": 125}
history = deque(receipt_ids, maxlen=2)
history.append("R-0043")
print("member:", "R-0041" in known)
print("missing amount:", amounts.get("R-0099"))
print("key created:", "R-0099" in amounts)
print("retained history:", list(history))
receipt_ids.append("R-0044")
print("outer snapshot:", outer_snapshot)
