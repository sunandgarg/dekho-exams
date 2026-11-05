receipts = [(43, 125), (41, 75), (42, 75)]
ranked = sorted(receipts, key=lambda receipt: receipt[1])
print(ranked)
print(receipts)
result = receipts.sort(key=lambda receipt: receipt[0])
print(result)
print(receipts)
