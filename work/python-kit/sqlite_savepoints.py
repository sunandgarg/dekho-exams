import sqlite3

connection = sqlite3.connect(":memory:", isolation_level=None)
try:
    connection.execute("CREATE TABLE receipt(id INTEGER PRIMARY KEY)")
    connection.execute("BEGIN")
    connection.execute("INSERT INTO receipt VALUES (41)")
    connection.execute("SAVEPOINT import_step")
    try:
        connection.execute("INSERT INTO receipt VALUES (42)")
        connection.execute("INSERT INTO receipt VALUES (41)")
    except sqlite3.IntegrityError:
        connection.execute("ROLLBACK TO import_step")
    connection.execute("RELEASE import_step")
    connection.execute("INSERT INTO receipt VALUES (43)")
    connection.execute("COMMIT")
    print("committed:", connection.execute("SELECT id FROM receipt ORDER BY id").fetchall())
    connection.execute("BEGIN")
    connection.execute("SAVEPOINT accepted_step")
    connection.execute("INSERT INTO receipt VALUES (44)")
    connection.execute("RELEASE accepted_step")
    connection.execute("ROLLBACK")
    print("after outer rollback:", connection.execute("SELECT COUNT(*) FROM receipt").fetchone()[0])
finally:
    connection.close()
