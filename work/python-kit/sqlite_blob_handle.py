import sqlite3

connection = sqlite3.connect(":memory:", isolation_level=None)
try:
    connection.execute("CREATE TABLE receipts (receipt_id INTEGER PRIMARY KEY, code BLOB NOT NULL)")
    connection.execute("BEGIN")
    try:
        connection.execute("INSERT INTO receipts VALUES (?, zeroblob(?))", (47, 6))
        with connection.blobopen("receipts", "code", 47) as receipt_blob:
            receipt_blob.write(b"R-0047")
            try:
                receipt_blob.write(b"!")
            except ValueError:
                print("overflow_rejected", True)
        connection.execute("COMMIT")
    except Exception:
        connection.execute("ROLLBACK")
        raise
    stored_code = connection.execute(
        "SELECT code FROM receipts WHERE receipt_id = ?", (47,)
    ).fetchone()[0]
    print("stored", stored_code)
finally:
    connection.close()
