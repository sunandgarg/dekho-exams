from itertools import groupby

receipts = [("north", 47), ("south", 26), ("north", 11)]

def region_totals(ordered_receipts):
    return [(region, sum(amount for _, amount in run))
            for region, run in groupby(ordered_receipts, key=lambda receipt: receipt[0])]

print("arrival_runs", region_totals(receipts))
sorted_receipts = sorted(receipts, key=lambda receipt: receipt[0])
print("region_totals", region_totals(sorted_receipts))
print("original_order", [region for region, _ in receipts])
