from collections import Counter
from heapq import nlargest

categories = ["accepted", "rejected", "accepted", "queued", "rejected", "accepted"]
counts = Counter(categories)
ranked = nlargest(2, counts.items(), key=lambda item: (item[1], item[0]))
print(ranked)
