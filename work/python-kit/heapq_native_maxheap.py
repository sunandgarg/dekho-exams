from heapq import heapify_max, heappop_max, heappush_max

inspection_scores = [47, 82, 65]
heapify_max(inspection_scores)
heappush_max(inspection_scores, 91)
descending = []
while inspection_scores:
    descending.append(heappop_max(inspection_scores))
print("priority_order", descending)
