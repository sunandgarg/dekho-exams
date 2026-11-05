import sqlite3

connection = sqlite3.connect(":memory:")
connection.execute("CREATE TABLE receipt(offset INTEGER PRIMARY KEY, identifier TEXT NOT NULL)")
connection.execute("CREATE TABLE checkpoint(id INTEGER PRIMARY KEY CHECK(id=1), last_offset INTEGER NOT NULL)")
connection.execute("INSERT INTO checkpoint VALUES (1, 0)")
connection.commit()

def ingest(start, identifiers):
    if type(start) is not int or start <= 0 or type(identifiers) is not list or not 1 <= len(identifiers) <= 10 or any(type(identifier) is not str or len(identifier) != 3 for identifier in identifiers):
        raise ValueError("bounded import")
    with connection:
        previous = connection.execute("SELECT last_offset FROM checkpoint WHERE id=1").fetchone()[0]
        if start != previous + 1:
            raise ValueError("offset gap or replay")
        for offset, identifier in enumerate(identifiers, start):
            connection.execute("INSERT INTO receipt VALUES (?, ?)", (offset, identifier))
        connection.execute("UPDATE checkpoint SET last_offset=? WHERE id=1", (start + len(identifiers) - 1,))

ingest(1, ["R41", "R42"])
try:
    ingest(4, ["R43"])
except ValueError:
    print("gap rejected")
print("rows:", connection.execute("SELECT offset,identifier FROM receipt ORDER BY offset").fetchall())
print("checkpoint:", connection.execute("SELECT last_offset FROM checkpoint").fetchone()[0])
connection.close()
