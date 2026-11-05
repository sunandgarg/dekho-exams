import sqlite3

database = sqlite3.connect(":memory:", isolation_level=None)
database.execute("BEGIN IMMEDIATE")
database.execute("CREATE TABLE receipts (receipt_id TEXT PRIMARY KEY)")
database.execute("PRAGMA user_version = 1")
database.execute("COMMIT")

try:
    database.execute("BEGIN IMMEDIATE")
    database.execute("ALTER TABLE receipts ADD COLUMN batch_id TEXT")
    database.execute("CREATE TABLE receipts (duplicate_id TEXT)")
    database.execute("PRAGMA user_version = 2")
    database.execute("COMMIT")
except sqlite3.OperationalError:
    database.execute("ROLLBACK")

version = database.execute("PRAGMA user_version").fetchone()[0]
columns = [row[1] for row in database.execute("PRAGMA table_info(receipts)")]
print("version", version)
print("columns", columns)
database.close()
