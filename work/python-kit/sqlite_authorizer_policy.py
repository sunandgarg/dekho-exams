import sqlite3

connection = sqlite3.connect(":memory:")
try:
    connection.execute("CREATE TABLE receipts (receipt_id INTEGER PRIMARY KEY)")
    connection.execute("INSERT INTO receipts VALUES (?)", (47,))
    connection.commit()

    def authorize_receipt_read(action, first, second, database, trigger):
        if action in (sqlite3.SQLITE_DELETE, sqlite3.SQLITE_UPDATE):
            return sqlite3.SQLITE_DENY
        return sqlite3.SQLITE_OK

    connection.set_authorizer(authorize_receipt_read)
    try:
        connection.execute("DELETE FROM receipts WHERE receipt_id = ?", (47,))
    except sqlite3.DatabaseError:
        print("delete_rejected", True)
    print("remaining", connection.execute("SELECT count(*) FROM receipts").fetchone()[0])
finally:
    connection.set_authorizer(None)
    connection.close()
