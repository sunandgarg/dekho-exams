receipts = [(2, "R-0042"), (1, "R-0041"), (2, "R-0040")]
ordered = sorted(receipts, key=lambda receipt: (receipt[0], receipt[1]))
print(ordered)
callbacks = [lambda receipt_id=receipt_id: receipt_id for receipt_id in ("R-0041", "R-0042")]
print([callback() for callback in callbacks])
print("input unchanged:", receipts[0] == (2, "R-0042"))
