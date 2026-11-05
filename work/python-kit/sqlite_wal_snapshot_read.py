import sqlite3
import tempfile
from pathlib import Path

with tempfile.TemporaryDirectory() as directory:
    database = Path(directory) / "inventory.db"
    writer = sqlite3.connect(database, isolation_level=None)
    reader = sqlite3.connect(database, isolation_level=None)
    writer.execute("PRAGMA journal_mode=WAL")
    writer.execute("CREATE TABLE stock (sku TEXT PRIMARY KEY, units INTEGER)")
    writer.execute("INSERT INTO stock VALUES (?, ?)", ("SKU-47", 47))
    reader.execute("BEGIN")
    before = reader.execute("SELECT units FROM stock").fetchone()[0]
    writer.execute("UPDATE stock SET units = ? WHERE sku = ?", (52, "SKU-47"))
    during = reader.execute("SELECT units FROM stock").fetchone()[0]
    reader.execute("COMMIT")
    after = reader.execute("SELECT units FROM stock").fetchone()[0]
    print("snapshot:", before, during)
    print("new read:", after)
    reader.close()
    writer.close()
