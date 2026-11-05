import sqlite3

connection = sqlite3.connect(":memory:")
connection.execute("PRAGMA foreign_keys=ON")
print("enabled:", connection.execute("PRAGMA foreign_keys").fetchone()[0])
connection.execute("CREATE TABLE customer(id INTEGER PRIMARY KEY)")
connection.execute("CREATE TABLE receipt(id INTEGER PRIMARY KEY, customer_id INTEGER NOT NULL REFERENCES customer(id))")
with connection:
    connection.execute("INSERT INTO customer VALUES (41)")
    connection.execute("INSERT INTO receipt VALUES (1, 41)")
try:
    with connection:
        connection.execute("INSERT INTO receipt VALUES (2, 99)")
except sqlite3.IntegrityError:
    print("orphan rejected")
print("receipts:", connection.execute("SELECT COUNT(*) FROM receipt").fetchone()[0])
connection.close()
