import sqlite3

connection = sqlite3.connect(":memory:")
try:
    connection.execute("CREATE TABLE receipt (id INTEGER PRIMARY KEY, amount INTEGER CHECK(amount > 0))")
    try:
        with connection:
            connection.execute("INSERT INTO receipt VALUES (?, ?)", (41, 125))
            connection.execute("INSERT INTO receipt VALUES (?, ?)", (42, -1))
    except sqlite3.IntegrityError:
        print("batch rolled back")
    print(connection.execute("SELECT count(*) FROM receipt").fetchone()[0])
    with connection:
        connection.execute("INSERT INTO receipt VALUES (?, ?)", (43, 75))
    print(connection.execute("SELECT id, amount FROM receipt ORDER BY id").fetchall())
finally:
    connection.close()
