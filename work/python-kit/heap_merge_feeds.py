from heapq import merge

def merged_events(*feeds):
    if len(feeds) > 4 or any(type(feed) is not list or len(feed) > 20 or any(type(row) is not tuple or len(row) != 2 or type(row[0]) is not int or type(row[1]) is not str for row in feed) or any(a[0] > b[0] for a, b in zip(feed, feed[1:])) for feed in feeds):
        raise ValueError("sorted bounded feeds")
    return list(merge(*feeds, key=lambda row: row[0]))

print(merged_events([(1, "R41"), (4, "R43")], [(2, "R42"), (5, "R44")]))
try:
    merged_events([(3, "R43"), (1, "R41")])
except ValueError:
    print("unsorted feed rejected")
