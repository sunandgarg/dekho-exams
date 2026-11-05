import sqlite3

connection = sqlite3.connect(":memory:")
connection.row_factory = sqlite3.Row
try:
    connection.execute("CREATE TABLE receipts (receipt_id INTEGER, state TEXT)")
    connection.execute("INSERT INTO receipts VALUES (?, ?)", (47, "paid"))
    selected = connection.execute(
        "SELECT receipt_id AS receipt_key, state AS receipt_state FROM receipts"
    ).fetchone()
    print("record", selected["receipt_key"], selected["receipt_state"])
    ambiguous = connection.execute(
        "SELECT receipt_id AS result, state AS result FROM receipts"
    ).fetchone()
    print("duplicate_names", ambiguous.keys().count("result"))
    print("named_value", ambiguous["result"])
finally:
    connection.close()
