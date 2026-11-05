import csv
import io

source = io.StringIO('amount_minor,note\n125,"review, accepted"\n', newline="")
reader = csv.DictReader(source)
if reader.fieldnames != ["amount_minor", "note"]:
    raise ValueError("expected receipt header")
for row in reader:
    if set(row) != {"amount_minor", "note"} or None in row.values():
        raise ValueError("complete row required")
    amount = int(row["amount_minor"])
    if amount <= 0:
        raise ValueError("positive amount required")
    print(amount)
    print(row["note"])
