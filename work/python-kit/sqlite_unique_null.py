import sqlite3

connection = sqlite3.connect(":memory:")
connection.execute("CREATE TABLE receipt(id INTEGER PRIMARY KEY, external_id TEXT UNIQUE)")
connection.execute("INSERT INTO receipt(external_id) VALUES (NULL), (NULL), ('R41')")
try:
    connection.execute("INSERT INTO receipt(external_id) VALUES ('R41')")
except sqlite3.IntegrityError:
    print("duplicate ID rejected")
print("missing IDs:", connection.execute("SELECT COUNT(*) FROM receipt WHERE external_id IS NULL").fetchone()[0])
connection.close()
