import sqlite3
import tempfile
from pathlib import Path

def claim(connection, now, token):
    if type(now) is not int or not 0 <= now <= 1000000 or type(token) is not str or not token.isascii() or not token.isalnum() or not 1 <= len(token) <= 16:
        raise ValueError("bounded clock and fresh token required")
    connection.execute("BEGIN IMMEDIATE")
    try:
        row = connection.execute("SELECT event_id FROM outbox WHERE done=0 AND lease_until<=? ORDER BY event_id LIMIT 1", (now,)).fetchone()
        if row:
            connection.execute("UPDATE outbox SET token=?,lease_until=? WHERE event_id=?", (token, now + 10, row[0]))
        connection.commit()
        return row[0] if row else None
    except BaseException:
        connection.rollback()
        raise

def acknowledge(connection, event_id, token):
    cursor = connection.execute("UPDATE outbox SET done=1 WHERE event_id=? AND token=? AND done=0", (event_id, token))
    return cursor.rowcount == 1

with tempfile.TemporaryDirectory() as directory:
    path = Path(directory) / "owned.sqlite3"
    first = sqlite3.connect(path, isolation_level=None, timeout=0)
    second = sqlite3.connect(path, isolation_level=None, timeout=0)
    try:
        first.execute("CREATE TABLE outbox(event_id INTEGER PRIMARY KEY,token TEXT,lease_until INTEGER NOT NULL DEFAULT 0,done INTEGER NOT NULL DEFAULT 0)")
        first.execute("INSERT INTO outbox(event_id) VALUES(41)")
        print("first claim:", claim(first, 100, "claimA"))
        print("active lease:", claim(second, 109, "claimB"))
        print("reclaimed:", claim(second, 110, "claimB"))
        print("stale ack:", acknowledge(first, 41, "claimA"))
        print("current ack:", acknowledge(second, 41, "claimB"))
        print("after ack:", claim(first, 120, "claimC"))
    finally:
        second.close()
        first.close()
