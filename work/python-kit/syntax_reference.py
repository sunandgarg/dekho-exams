receipt_ids = [41, 42]
amounts = [125, 75]
print([f"{position}:{identifier}" for position, identifier in enumerate(receipt_ids, start=1)])
print(sum(amount for identifier, amount in zip(receipt_ids, amounts, strict=True)))
try:
    list(zip(receipt_ids, [125], strict=True))
except ValueError:
    print("length mismatch rejected")
