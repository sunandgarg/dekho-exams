import heapq
from itertools import count

pending = []
current = {}
sequence = count()
stale = 0

def set_priority(parcel_id, priority):
    revision = next(sequence)
    current[parcel_id] = (priority, revision)
    heapq.heappush(pending, (priority, revision, parcel_id))

def take_next():
    global stale
    while pending:
        priority, revision, parcel_id = heapq.heappop(pending)
        if current.get(parcel_id) != (priority, revision):
            stale += 1
            continue
        del current[parcel_id]
        return parcel_id
    return None

set_priority("P-47", 7)
set_priority("P-48", 5)
set_priority("P-47", 2)
print(take_next())
print(take_next())
print(take_next())
print("stale:", stale)
