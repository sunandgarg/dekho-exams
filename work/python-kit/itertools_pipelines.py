from itertools import chain, groupby, islice

receipts = [("DEL", 125), ("BOM", 75), ("DEL", 250)]
runs = [(region, sum(amount for _, amount in group)) for region, group in groupby(receipts, key=lambda row: row[0])]
print("adjacent groups:", runs)
print("bounded prefix:", list(islice(chain([125, 250], [75, 40]), 3)))
try:
    list(zip(["R-0041", "R-0042"], [125], strict=True))
except ValueError:
    print("unequal batches rejected")
