import sqlite3

connection = sqlite3.connect(":memory:")
connection.execute("CREATE TABLE receipt(id TEXT PRIMARY KEY, minor INTEGER NOT NULL CHECK(minor >= 0))")
def store(identifier, minor):
    with connection:
        connection.execute(
            "INSERT INTO receipt(id, minor) VALUES (?, ?) "
            "ON CONFLICT(id) DO UPDATE SET minor=excluded.minor",
            (identifier, minor),
        )

store("R41", 125)
store("R41", 150)
print(connection.execute("SELECT id, minor FROM receipt").fetchall())
connection.close()
