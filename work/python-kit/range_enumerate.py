receipt_ids = ["R-0041", "R-0042"]
print(list(enumerate(receipt_ids, start=1)))
print(list(range(2, 9, 3)))
print(list(range(4, 4)))
try:
    range(1, 4, 0)
except ValueError:
    print("zero step rejected")
