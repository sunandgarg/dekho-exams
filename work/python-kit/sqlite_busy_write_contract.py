import sqlite3
import tempfile
from pathlib import Path

with tempfile.TemporaryDirectory() as directory:
    database = Path(directory) / "receipts.db"
    owner = sqlite3.connect(database, timeout=0, isolation_level=None)
    contender = sqlite3.connect(database, timeout=0, isolation_level=None)
    owner.execute("CREATE TABLE receipts (receipt_id TEXT PRIMARY KEY)")
    owner.execute("BEGIN IMMEDIATE")
    owner.execute("INSERT INTO receipts VALUES (?)", ("R-47",))
    try:
        contender.execute("BEGIN IMMEDIATE")
    except sqlite3.OperationalError:
        print("second writer blocked")
    owner.execute("COMMIT")
    contender.execute("BEGIN IMMEDIATE")
    contender.execute("INSERT INTO receipts VALUES (?)", ("R-48",))
    contender.execute("COMMIT")
    print("rows:", owner.execute("SELECT count(*) FROM receipts").fetchone()[0])
    owner.close()
    contender.close()
