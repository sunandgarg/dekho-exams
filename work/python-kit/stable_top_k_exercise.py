def top_receipts(records, count):
    if type(records) is not list or len(records) > 100 or type(count) is not int or not 0 <= count <= len(records):
        raise ValueError("bounded selection")
    if any(type(row) is not tuple or len(row) != 2 or type(row[0]) is not str or type(row[1]) is not int or not 0 <= row[1] <= 100 for row in records):
        raise ValueError("receipt record")
    ranked = sorted(enumerate(records), key=lambda item: (-item[1][1], item[0]))
    return [row[0] for _, row in ranked[:count]]

queue = [("R41", 8), ("R42", 8), ("R43", 9)]
print(top_receipts(queue, 2))
print(queue)
try:
    top_receipts(queue, True)
except ValueError:
    print("boolean count rejected")
