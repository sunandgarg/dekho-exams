from pathlib import Path
import sqlite3
import tempfile

with tempfile.TemporaryDirectory() as directory:
    path = Path(directory) / "owned.sqlite3"
    first = sqlite3.connect(path, timeout=0, isolation_level=None)
    second = sqlite3.connect(path, timeout=0, isolation_level=None)
    try:
        first.execute("CREATE TABLE receipts (id INTEGER PRIMARY KEY, amount INTEGER NOT NULL)")
        first.execute("INSERT INTO receipts VALUES (41,125)")
        first.execute("BEGIN IMMEDIATE")
        first.execute("UPDATE receipts SET amount=amount+25 WHERE id=41")
        try:
            second.execute("BEGIN IMMEDIATE")
        except sqlite3.OperationalError as failure:
            print("busy rejected:", failure.sqlite_errorcode == sqlite3.SQLITE_BUSY)
        first.commit()
        second.execute("BEGIN IMMEDIATE")
        second.execute("UPDATE receipts SET amount=amount+25 WHERE id=41")
        second.commit()
        print("committed amount:", first.execute("SELECT amount FROM receipts WHERE id=41").fetchone()[0])
    finally:
        first.close(); second.close()
