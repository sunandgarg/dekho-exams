import sqlite3
import tempfile
from pathlib import Path

def renew(connection, identifier, token, now, new_expiry):
    if type(identifier) is not int or not 1 <= identifier <= 1000 or type(token) is not str or not 1 <= len(token) <= 32:
        raise ValueError("claim fields")
    if any(type(value) is not int or not 0 <= value <= 1000000 for value in (now, new_expiry)) or not now < new_expiry <= now + 10:
        raise ValueError("clock/extension bounds")
    connection.execute("BEGIN IMMEDIATE")
    try:
        changed = connection.execute("UPDATE job SET expiry=? WHERE id=? AND token=? AND expiry>? AND expiry<?",
            (new_expiry, identifier, token, now, new_expiry)).rowcount == 1
        connection.execute("COMMIT")
        return changed
    except BaseException:
        connection.execute("ROLLBACK")
        raise

with tempfile.TemporaryDirectory() as directory:
    database = Path(directory) / "claims.db"
    first = sqlite3.connect(database, isolation_level=None)
    second = sqlite3.connect(database, isolation_level=None)
    try:
        first.execute("CREATE TABLE job(id INTEGER PRIMARY KEY, token TEXT NOT NULL, expiry INTEGER NOT NULL)")
        first.execute("INSERT INTO job VALUES (41, 'claim-a', 10)")
        print("renewed:", renew(first, 41, "claim-a", 5, 15))
        print("stale token:", renew(second, 41, "claim-old", 6, 16))
        print("no extension:", renew(second, 41, "claim-a", 6, 14))
        print("at expiry:", renew(second, 41, "claim-a", 15, 20))
        print("stored expiry:", second.execute("SELECT expiry FROM job").fetchone()[0])
    finally:
        second.close()
        first.close()
