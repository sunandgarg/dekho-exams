import csv
import io

def import_receipts(payload):
    if type(payload) is not bytes or len(payload) > 512:
        raise ValueError("byte budget")
    reader = csv.reader(io.StringIO(payload.decode("utf-8", errors="strict")), strict=True)
    if next(reader, None) != ["receipt_id", "amount_minor"]:
        raise ValueError("header mismatch")
    staged = {}
    for row in reader:
        if len(staged) == 3 or len(row) != 2:
            raise ValueError("row budget or shape")
        if any(not field or len(field) > 6 or not field.isascii() or not field.isdecimal() for field in row):
            raise ValueError("bounded decimal fields required")
        receipt_id, amount = map(int, row)
        if receipt_id <= 0 or amount <= 0 or receipt_id in staged:
            raise ValueError("invalid or duplicate receipt")
        staged[receipt_id] = amount
    return staged

print(import_receipts(b"receipt_id,amount_minor\n41,125\n42,75\n"))
try:
    import_receipts(b"receipt_id,amount_minor\n41,125\n41,75\n")
except ValueError:
    print("duplicate batch rejected")
