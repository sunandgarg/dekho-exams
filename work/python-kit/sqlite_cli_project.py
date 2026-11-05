import sqlite3
import tempfile
from pathlib import Path

def accept_batch(connection, rows):
    if len(rows) > 32:
        raise ValueError("batch budget")
    identifiers = set()
    for receipt_id, amount in rows:
        if type(receipt_id) is not int or type(amount) is not int or not 1 <= receipt_id <= 100000 or not 1 <= amount <= 1000000 or receipt_id in identifiers:
            raise ValueError("invalid receipt batch")
        identifiers.add(receipt_id)
    with connection:
        connection.executemany("INSERT INTO receipts(receipt_id, amount_minor) VALUES (?, ?)", rows)

with tempfile.TemporaryDirectory() as directory:
    database = Path(directory) / "receipts.db"
    connection = sqlite3.connect(database)
    try:
        connection.execute("CREATE TABLE receipts(receipt_id INTEGER PRIMARY KEY, amount_minor INTEGER NOT NULL CHECK(amount_minor > 0))")
        accept_batch(connection, [(41, 125), (42, 75)])
        try:
            accept_batch(connection, [(43, 90), (41, 20)])
        except sqlite3.IntegrityError:
            print("duplicate transaction rolled back")
    finally:
        connection.close()
    reopened = sqlite3.connect(database)
    try:
        print(reopened.execute("SELECT receipt_id, amount_minor FROM receipts ORDER BY receipt_id").fetchall())
    finally:
        reopened.close()
