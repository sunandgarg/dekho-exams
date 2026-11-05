def first_overdue(receipts):
    for receipt in receipts:
        if not receipt["active"]:
            continue
        if receipt["days_late"] > 0:
            matched = receipt["receipt_id"]
            break
    else:
        return None
    return matched

receipts = [{"receipt_id": "R-0041", "active": False, "days_late": 4},
            {"receipt_id": "R-0042", "active": True, "days_late": 2}]
print(first_overdue(receipts))
print(first_overdue([]))
attempts = 0
while attempts < 3:
    attempts += 1
print("bounded attempts:", attempts)
