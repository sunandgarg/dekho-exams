import sqlite3

def unique_name_row(cursor, values):
    names = [column[0] for column in cursor.description]
    normalized = [name.casefold() for name in names]
    if len(set(normalized)) != len(normalized):
        raise ValueError("duplicate result column")
    return dict(zip(names, values, strict=True))

connection = sqlite3.connect(":memory:")
try:
    connection.row_factory = unique_name_row
    receipt = connection.execute(
        "SELECT 47 AS receipt_id, 26 AS amount_cents").fetchone()
    print("receipt", receipt)
    try:
        connection.execute("SELECT 47 AS total, 26 AS TOTAL").fetchone()
    except ValueError:
        print("duplicate_rejected", True)
finally:
    connection.close()
