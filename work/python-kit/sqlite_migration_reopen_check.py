import sqlite3
import tempfile
from contextlib import closing
from pathlib import Path

with tempfile.TemporaryDirectory() as directory:
    database_path = Path(directory) / "receipts.db"
    with closing(sqlite3.connect(database_path, isolation_level=None)) as database:
        database.execute("BEGIN IMMEDIATE")
        database.execute("CREATE TABLE receipts (receipt_id TEXT PRIMARY KEY)")
        database.execute("PRAGMA user_version = 1")
        database.execute("COMMIT")

    with closing(sqlite3.connect(database_path, isolation_level=None)) as database:
        try:
            database.execute("BEGIN IMMEDIATE")
            database.execute("ALTER TABLE receipts ADD COLUMN batch_id TEXT")
            database.execute("CREATE TABLE receipts (duplicate_id TEXT)")
            database.execute("PRAGMA user_version = 2")
            database.execute("COMMIT")
        except sqlite3.OperationalError:
            database.execute("ROLLBACK")

    with closing(sqlite3.connect(database_path)) as database:
        version = database.execute("PRAGMA user_version").fetchone()[0]
        columns = [row[1] for row in database.execute("PRAGMA table_info(receipts)")]
    print("version", version)
    print("columns", columns)
