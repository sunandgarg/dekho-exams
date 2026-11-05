import sqlite3

connection = sqlite3.connect(":memory:")
try:
    connection.execute("CREATE TABLE receipts (receipt_id INTEGER PRIMARY KEY)")
    connection.execute("INSERT INTO receipts VALUES (?)", (47,))
    connection.commit()
    callbacks = 0

    def stop_long_query():
        global callbacks
        callbacks += 1
        return int(callbacks >= 40)

    connection.set_progress_handler(stop_long_query, 1)
    try:
        connection.execute("WITH RECURSIVE numbers(value) AS ("
                           "SELECT 1 UNION ALL SELECT value + 1 FROM numbers WHERE value < 100000) "
                           "SELECT sum(value) FROM numbers").fetchone()
    except sqlite3.DatabaseError:
        print("query_interrupted", True)
    finally:
        connection.set_progress_handler(None, 0)
    print("receipt_kept", connection.execute("SELECT receipt_id FROM receipts").fetchone()[0])
finally:
    connection.close()
