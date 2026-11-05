from collections import Counter

def receipt_gaps(expected, scanned):
    for batch in (expected, scanned):
        if type(batch) is not list or len(batch) > 100:
            raise ValueError("batch cap")
        if any(type(identifier) is not str or len(identifier) != 3 or identifier[0] != "R" or not identifier[1:].isascii() or not identifier[1:].isdigit() for identifier in batch):
            raise ValueError("receipt identifier")
    due, seen = Counter(expected), Counter(scanned)
    return sorted((due - seen).items()), sorted((seen - due).items())

print(receipt_gaps(["R41", "R41", "R42"], ["R41", "R43"]))
try:
    receipt_gaps(["R41"], ["R４１"])
except ValueError:
    print("non-ASCII identifier rejected")
