import re

def receipt_map(records):
    if not isinstance(records, list) or len(records) > 64: raise ValueError("batch rejected")
    result = {}
    for record in records:
        if not isinstance(record, dict) or set(record) != {"id", "amount"}: raise ValueError("fields rejected")
        identifier, amount = record["id"], record["amount"]
        if not isinstance(identifier, str) or re.fullmatch(r"R-[0-9]{4}", identifier) is None or identifier in result: raise ValueError("identifier rejected")
        if type(amount) is not int or not 0 <= amount <= 1000000: raise ValueError("amount rejected")
        result[identifier] = amount
    return result

def reconcile_receipts(left_records, right_records):
    left, right = receipt_map(left_records), receipt_map(right_records)
    differences = []
    for identifier in sorted(left.keys() | right.keys()):
        if identifier not in left: differences.append((identifier, "missing-left"))
        elif identifier not in right: differences.append((identifier, "missing-right"))
        elif left[identifier] != right[identifier]: differences.append((identifier, "amount-mismatch"))
    return differences

left = [{"id":"R-0041","amount":125},{"id":"R-0042","amount":250}]
right = [{"id":"R-0041","amount":150},{"id":"R-0043","amount":75}]
print(reconcile_receipts(left, right))
try: reconcile_receipts(left + [left[0].copy()], right)
except ValueError: print("duplicate rejected")
