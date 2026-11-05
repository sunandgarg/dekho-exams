from collections import deque

pending = deque(["R41", "R42", ""])
reads = 0
def pull_receipt():
    global reads
    reads += 1
    if reads > 3:
        raise ValueError("missing stop marker")
    return pending.popleft()

print(list(iter(pull_receipt, "")))
print("calls:", reads)
print("remaining:", list(pending))
