import csv
import io

def receipt_rows(text):
    if type(text) is not str or len(text) > 200:
        raise ValueError("input size")
    stream = io.StringIO(text, newline="")
    header = next(csv.reader(stream), None)
    if header is None or len(header) != 2 or set(header) != {"id", "minor"}:
        raise ValueError("header contract")
    rows = list(csv.DictReader(stream, fieldnames=header))
    if len(rows) > 5 or any(None in row or any(value is None for value in row.values()) for row in rows):
        raise ValueError("row width")
    return rows

print(receipt_rows("id,minor\nR41,125\nR42,75\n"))
try:
    receipt_rows("id,minor,minor\nR41,125,0\n")
except ValueError:
    print("duplicate header rejected")
