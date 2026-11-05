import json
import sqlite3

def unique_pairs(pairs):
    record = {}
    for key, value in pairs:
        if key in record:
            raise ValueError("duplicate key")
        record[key] = value
    return record

def import_batch(connection, text):
    if type(text) is not str or len(text) > 400:
        raise ValueError("batch size")
    lines = text.splitlines()
    if not 1 <= len(lines) <= 5:
        raise ValueError("batch rows")
    staged = []
    seen = set()
    for line in lines:
        row = json.loads(line, object_pairs_hook=unique_pairs)
        if type(row) is not dict or set(row) != {"id", "minor"}:
            raise ValueError("record shape")
        if type(row["id"]) is not str or not row["id"].startswith("R") or not row["id"][1:].isdigit() or len(row["id"]) > 8:
            raise ValueError("receipt ID")
        if type(row["minor"]) is not int or not 0 <= row["minor"] <= 100000 or row["id"] in seen:
            raise ValueError("amount or duplicate")
        seen.add(row["id"])
        staged.append((row["id"], row["minor"]))
    with connection:
        connection.executemany("INSERT INTO receipt(id, minor) VALUES (?, ?)", staged)

connection = sqlite3.connect(":memory:")
connection.execute("CREATE TABLE receipt(id TEXT PRIMARY KEY, minor INTEGER NOT NULL)")
import_batch(connection, '{"id":"R41","minor":125}')
try:
    import_batch(connection, '{"id":"R42","minor":75}\n{"id":"R41","minor":0}')
except sqlite3.IntegrityError:
    print("batch rolled back")
print(connection.execute("SELECT id, minor FROM receipt ORDER BY id").fetchall())
connection.close()
