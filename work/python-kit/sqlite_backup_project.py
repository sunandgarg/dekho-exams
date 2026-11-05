import sqlite3

source = sqlite3.connect(":memory:")
destination = sqlite3.connect(":memory:")
source.execute("CREATE TABLE receipt(id TEXT PRIMARY KEY)")
with source:
    source.execute("INSERT INTO receipt VALUES ('R41')")
source.backup(destination)
with source:
    source.execute("INSERT INTO receipt VALUES ('R42')")
print("source:", source.execute("SELECT COUNT(*) FROM receipt").fetchone()[0])
print("copy:", destination.execute("SELECT COUNT(*) FROM receipt").fetchone()[0])
source.close()
destination.close()
