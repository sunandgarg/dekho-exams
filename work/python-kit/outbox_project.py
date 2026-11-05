import sqlite3

def open_outbox():
    database = sqlite3.connect(":memory:")
    database.executescript("CREATE TABLE receipts (id TEXT PRIMARY KEY, amount INTEGER NOT NULL); CREATE TABLE outbox (id TEXT PRIMARY KEY, receipt_id TEXT NOT NULL, acknowledged INTEGER NOT NULL DEFAULT 0);")
    return database

def create_receipt(database, identifier, amount, fail=False):
    if not isinstance(identifier, str) or identifier not in {"R-0041", "R-0042"} or type(amount) is not int or not 0 <= amount <= 1000000:
        raise ValueError("receipt rejected")
    with database:
        database.execute("INSERT INTO receipts VALUES (?,?)", (identifier, amount))
        if fail: raise RuntimeError("staged failure")
        database.execute("INSERT INTO outbox(id,receipt_id) VALUES (?,?)", ("created:" + identifier, identifier))

def pending_events(database):
    return database.execute("SELECT id,receipt_id FROM outbox WHERE acknowledged=0 ORDER BY id LIMIT 16").fetchall()

with open_outbox() as database:
    create_receipt(database, "R-0041", 125)
    try: create_receipt(database, "R-0042", 250, fail=True)
    except RuntimeError: print("failed receipt rolled back")
    print("receipts:", database.execute("SELECT count(*) FROM receipts").fetchone()[0])
    first = pending_events(database)
    print("pending:", first)
    print("replay before acknowledgement:", pending_events(database) == first)
    with database:
        database.execute("UPDATE outbox SET acknowledged=1 WHERE id=?", (first[0][0],))
    print("pending after acknowledgement:", pending_events(database))
database.close()
