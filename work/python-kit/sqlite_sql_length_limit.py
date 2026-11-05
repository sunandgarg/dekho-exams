import sqlite3

connection = sqlite3.connect(":memory:")
try:
    connection.setlimit(sqlite3.SQLITE_LIMIT_SQL_LENGTH, 120)
    print("limit", connection.getlimit(sqlite3.SQLITE_LIMIT_SQL_LENGTH))
    long_statement = "SELECT 47 " + " " * 160
    try:
        connection.execute(long_statement)
    except sqlite3.Error:
        print("long_sql_rejected", True)
    print("bound_value", connection.execute("SELECT ?", (73,)).fetchone()[0])
finally:
    connection.close()
