from collections import defaultdict

groups = defaultdict(list)
for region, receipt_id in [("DEL", "R-0041"), ("BOM", "R-0042"), ("DEL", "R-0043")]:
    groups[region].append(receipt_id)
print(dict(groups))
print(groups.get("BLR"))
print("BLR" in groups)
print(groups["BLR"])
print("BLR" in groups)
