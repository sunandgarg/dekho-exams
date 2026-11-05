import re
import sqlite3

def open_job_ledger():
    database = sqlite3.connect(":memory:")
    database.execute("CREATE TABLE jobs (job_id TEXT PRIMARY KEY, amount INTEGER NOT NULL, result INTEGER NOT NULL)")
    return database

def accept_job(database, job_id, amount):
    if not isinstance(job_id, str) or re.fullmatch(r"J-[0-9]{4}", job_id) is None:
        raise ValueError("job identity rejected")
    if type(amount) is not int or not 0 <= amount <= 1000000:
        raise ValueError("amount rejected")
    with database:
        existing = database.execute("SELECT amount, result FROM jobs WHERE job_id = ?", (job_id,)).fetchone()
        if existing is not None:
            if existing[0] != amount:
                raise ValueError("request identity conflict")
            return existing[1], False
        result = amount + 25
        database.execute("INSERT INTO jobs VALUES (?, ?, ?)", (job_id, amount, result))
        return result, True

if __name__ == "__main__":
    database = open_job_ledger()
    try:
        print(accept_job(database, "J-0041", 125))
        print(accept_job(database, "J-0041", 125))
        try:
            accept_job(database, "J-0041", 250)
        except ValueError:
            print("conflicting replay rejected")
        print("stored jobs:", database.execute("SELECT count(*) FROM jobs").fetchone()[0])
    finally:
        database.close()
