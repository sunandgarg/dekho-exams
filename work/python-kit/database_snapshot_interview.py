from pathlib import Path
import sqlite3
import tempfile

with tempfile.TemporaryDirectory() as directory:
    path = Path(directory) / "snapshot.sqlite3"
    writer = sqlite3.connect(path, isolation_level=None)
    reader = sqlite3.connect(path, isolation_level=None)
    try:
        assert writer.execute("PRAGMA journal_mode=WAL").fetchone()[0] == "wal"
        writer.execute("CREATE TABLE receipts (id INTEGER PRIMARY KEY, amount INTEGER NOT NULL)")
        writer.execute("INSERT INTO receipts VALUES (41,125)")
        reader.execute("BEGIN")
        print("first read:", reader.execute("SELECT amount FROM receipts WHERE id=41").fetchone()[0])
        writer.execute("UPDATE receipts SET amount=250 WHERE id=41")
        print("retained snapshot:", reader.execute("SELECT amount FROM receipts WHERE id=41").fetchone()[0])
        reader.commit()
        print("new read:", reader.execute("SELECT amount FROM receipts WHERE id=41").fetchone()[0])
    finally:
        reader.close(); writer.close()
