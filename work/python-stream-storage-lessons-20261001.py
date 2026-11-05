"""Add original, executable Python I/O and SQLite boundary lessons."""

import copy
import datetime
import html
import json
import uuid
from pathlib import Path


root = Path(__file__).resolve().parents[1]
fixture = root / "src/data/fixtures.json"
rows = json.loads(fixture.read_text())
by_path = {row["path"]: row for row in rows}
stamp = datetime.datetime.now(datetime.UTC).isoformat()

lessons = [
    dict(
        slug="async-length-prefixed-frame", section="python/advanced-python", subject="python-advanced",
        title="Python asyncio byte frames: reject an oversized length before reading a body",
        summary="A length-prefixed stream needs a maximum body size and an explicit short-read path.",
        contract="The parser consumes a two-byte unsigned length, rejects a declared body over its eight-byte limit, and then reads exactly that many bytes. One owned frame completes; another ends after five of its seven promised bytes. The partial payload is treated as a failed record, never as a shorter accepted record.",
        boundary="StreamReader.feed_data is used only to supply controlled bytes without opening a socket. A real peer can pause forever between bytes, so a caller also needs a deadline and a connection cleanup policy. The length check bounds one returned body; it does not cap the total bytes a transport may have buffered before parsing begins.",
        source='''import asyncio

async def read_receipt_frame(reader, maximum_body):
    header = await reader.readexactly(2)
    body_size = int.from_bytes(header, "big")
    if body_size > maximum_body:
        raise ValueError("receipt body too large")
    return await reader.readexactly(body_size)

async def inspect_frames():
    complete = asyncio.StreamReader()
    complete.feed_data((7).to_bytes(2, "big") + b"R47paid")
    complete.feed_eof()
    print("accepted", (await read_receipt_frame(complete, 8)).decode("ascii"))

    oversized = asyncio.StreamReader()
    oversized.feed_data((73).to_bytes(2, "big"))
    oversized.feed_eof()
    try:
        await read_receipt_frame(oversized, 8)
    except ValueError:
        print("oversized_rejected", True)

    shortened = asyncio.StreamReader()
    shortened.feed_data((7).to_bytes(2, "big") + b"R73pa")
    shortened.feed_eof()
    try:
        await read_receipt_frame(shortened, 8)
    except asyncio.IncompleteReadError as failure:
        print("partial_rejected", failure.partial == b"R73pa")

asyncio.run(inspect_frames())''',
        expected="accepted R47paid\noversized_rejected True\npartial_rejected True",
        cost="Header parsing is constant work; copying a valid body costs time and memory proportional to its declared size. A maximum body of eight bytes is a fixture policy, not a network-wide memory budget.",
        mistakes=["read(n) may return fewer than n bytes without EOF; use readexactly for a fixed frame.", "Reject the declared length before allocating or awaiting its body.", "An incomplete read is a failed frame even when partial bytes exist."],
        related=["python/socket-frame-reading", "python/async-timeout-boundary", "python/async-queues"],
    ),
    dict(
        slug="async-delimiter-overrun", section="python/advanced-python", subject="python-advanced",
        title="Python asyncio delimiter limits: an overrun leaves the bytes buffered",
        summary="StreamReader.readuntil raises on an overlong record without consuming its buffered bytes.",
        contract="The owned reader has an eight-byte separator limit. Its first line is longer than that limit, so readuntil raises LimitOverrunError. The program reads the first ten retained bytes afterward to prove that the failed delimiter search did not consume the record. It does not silently rescan the same oversized line.",
        boundary="The stream limit governs delimiter scanning, not the total memory already accepted by a transport. A service must decide whether to close the connection or drain a bounded amount after an overrun. This fixture chooses to stop; it is not a recovery parser for attacker-controlled streams.",
        source='''import asyncio

async def inspect_delimiter_limit():
    reader = asyncio.StreamReader(limit=8)
    reader.feed_data(b"receipt-47-untrusted\\n")
    reader.feed_eof()
    try:
        await reader.readuntil(b"\\n")
    except asyncio.LimitOverrunError:
        print("overrun_rejected", True)
    retained_prefix = await reader.readexactly(10)
    print("retained_prefix", retained_prefix.decode("ascii"))

asyncio.run(inspect_delimiter_limit())''',
        expected="overrun_rejected True\nretained_prefix receipt-47",
        cost="A delimiter scan examines bytes up to the limit before rejecting. Retained input still occupies memory until the connection owner consumes or discards it.",
        mistakes=["Retrying readuntil unchanged after an overrun repeats the same failure.", "A separator limit is not a complete transport buffer budget.", "Do not accept an overlong prefix as a valid shortened record."],
        related=["python/async-length-prefixed-frame", "python/socket-frame-reading", "python/async-timeout-boundary"],
    ),
    dict(
        slug="sqlite-blob-handle", section="python/examples", subject="python-examples",
        title="Python SQLite blob handles: preallocate bytes and keep the write inside a transaction",
        summary="sqlite3.Blob edits an existing fixed-size value; it cannot grow the column during a write.",
        contract="The ledger reserves six bytes for receipt 47, writes its six-byte identifier through a blob handle, and checks that a seventh byte is rejected. The handle closes before the transaction commits. A fresh query observes exactly the accepted bytes.",
        boundary="blobopen requires an existing row and does not work with a WITHOUT ROWID table. A blob handle is tied to its connection and row; close it before later row changes or connection teardown. This small fixture does not prove file-system crash durability or concurrent writer behavior.",
        source='''import sqlite3

connection = sqlite3.connect(":memory:", isolation_level=None)
try:
    connection.execute("CREATE TABLE receipts (receipt_id INTEGER PRIMARY KEY, code BLOB NOT NULL)")
    connection.execute("BEGIN")
    try:
        connection.execute("INSERT INTO receipts VALUES (?, zeroblob(?))", (47, 6))
        with connection.blobopen("receipts", "code", 47) as receipt_blob:
            receipt_blob.write(b"R-0047")
            try:
                receipt_blob.write(b"!")
            except ValueError:
                print("overflow_rejected", True)
        connection.execute("COMMIT")
    except Exception:
        connection.execute("ROLLBACK")
        raise
    stored_code = connection.execute(
        "SELECT code FROM receipts WHERE receipt_id = ?", (47,)
    ).fetchone()[0]
    print("stored", stored_code)
finally:
    connection.close()''',
        expected="overflow_rejected True\nstored b'R-0047'",
        cost="Incremental access can avoid holding a large BLOB copy in Python, but SQLite still stores the reserved bytes. A write is bounded by the allocated length; reserving excessive capacity wastes storage.",
        mistakes=["A blob write cannot extend a six-byte value to seven bytes.", "Keep the blob handle closed before changing its row or closing the connection.", "A successful COMMIT is not a claim about crash or power-loss survival."],
        related=["python/sqlite-transactions", "python/binary-records", "python/sqlite-backup-project"],
    ),
    dict(
        slug="sqlite-authorizer-policy", section="python/examples", subject="python-examples",
        title="Python SQLite authorizer: deny a statement on the connection that executes it",
        summary="A connection authorizer can reject selected SQL operations before they run.",
        contract="A prepared in-memory ledger holds receipt 47. Its authorizer rejects DELETE and UPDATE on this connection while allowing a SELECT. The rejected DELETE raises a database error, and a following count confirms that the row remains.",
        boundary="The callback is a connection-local policy aid, not a sandbox for hostile Python code. Other connections do not inherit it, and code able to replace the callback can remove it. Restrict accepted SQL, connection ownership, and file access separately. The fixture denies only two action classes, not every possible write route.",
        source='''import sqlite3

connection = sqlite3.connect(":memory:")
try:
    connection.execute("CREATE TABLE receipts (receipt_id INTEGER PRIMARY KEY)")
    connection.execute("INSERT INTO receipts VALUES (?)", (47,))
    connection.commit()

    def authorize_receipt_read(action, first, second, database, trigger):
        if action in (sqlite3.SQLITE_DELETE, sqlite3.SQLITE_UPDATE):
            return sqlite3.SQLITE_DENY
        return sqlite3.SQLITE_OK

    connection.set_authorizer(authorize_receipt_read)
    try:
        connection.execute("DELETE FROM receipts WHERE receipt_id = ?", (47,))
    except sqlite3.DatabaseError:
        print("delete_rejected", True)
    print("remaining", connection.execute("SELECT count(*) FROM receipts").fetchone()[0])
finally:
    connection.set_authorizer(None)
    connection.close()''',
        expected="delete_rejected True\nremaining 1",
        cost="The callback adds work to statement preparation and authorization. Its cost depends on statement shape; keep its decisions cheap and avoid retaining raw SQL or sensitive arguments for logging.",
        mistakes=["Installing a callback on one connection does not configure another.", "A two-action denylist is not a complete read-only policy.", "An authorizer cannot isolate hostile code that controls the Python process."],
        related=["python/sqlite-transactions", "python/sqlite-foreign-key-boundary", "python/audit-hook-observation"],
    ),
    dict(
        slug="sqlite-progress-budget", section="python/examples", subject="python-examples",
        title="Python SQLite progress handler: interrupt one expensive statement",
        summary="A progress callback can stop a query after a bounded number of virtual-machine steps.",
        contract="The connection starts with one accepted receipt. A recursive count query exceeds the fixture's forty callback allowance, so the progress handler returns a nonzero result and SQLite interrupts that statement. The handler is removed before a normal query verifies the existing row remains.",
        boundary="The callback count is a virtual-machine instruction budget, not elapsed time, memory use, or a cross-machine service-level guarantee. Different SQLite builds or query plans may do different work per result. Use a wall-clock deadline and resource policy alongside it for a real request boundary.",
        source='''import sqlite3

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
    connection.close()''',
        expected="query_interrupted True\nreceipt_kept 47",
        cost="Invoking Python after every virtual-machine step is deliberately expensive in this small fixture. A production interval should be measured against the accepted query workload, then combined with a deadline.",
        mistakes=["Instruction callbacks do not measure wall-clock time.", "Remove a request-scoped handler before reusing its connection.", "Catching the interrupt without checking surrounding transaction state can hide a partial workflow."],
        related=["python/sqlite-writer-contention", "python/sqlite-transactions", "python/sqlite-authorizer-policy"],
    ),
    dict(
        slug="sqlite-sql-length-limit", section="python/examples", subject="python-examples",
        title="Python SQLite SQL length limits: cap statement text separately from bound values",
        summary="SQLITE_LIMIT_SQL_LENGTH constrains the SQL statement, not every value bound to it.",
        contract="The connection lowers its SQL-text ceiling to 120 bytes. A long owned statement is rejected before execution, while a short parameterized statement succeeds. The program reads back the actual limit because SQLite may clamp a requested value to its compiled maximum.",
        boundary="This limit does not replace a bound-value size check, a row-count limit, or query time control. The fixture passes owned SQL; received values must still use parameters. The setting belongs to one connection and should be applied to each connection in a pool.",
        source='''import sqlite3

connection = sqlite3.connect(":memory:")
try:
    connection.setlimit(sqlite3.SQLITE_LIMIT_SQL_LENGTH, 120)
    print("limit", connection.getlimit(sqlite3.SQLITE_LIMIT_SQL_LENGTH))
    long_statement = "SELECT 47 " + " " * 160
    try:
        connection.execute(long_statement)
    except sqlite3.Error:
        print("long_sql_rejected", True)
    print("bound_value", connection.execute("SELECT ?", (73,)).fetchone()[0])
finally:
    connection.close()''',
        expected="limit 120\nlong_sql_rejected True\nbound_value 73",
        cost="Checking statement length is cheap relative to parsing the SQL. It says nothing about a parameter's bytes; add a separate application limit when large values matter.",
        mistakes=["Do not count bound data as if it were SQL text.", "Do not build received data into SQL merely to put it under this limit.", "A connection limit is not inherited by a newly opened connection."],
        related=["python/sqlite-progress-budget", "python/sqlite-authorizer-policy", "python/bounded-json-lines"],
    ),
    dict(
        slug="mmap-write-vs-copy", section="python/examples", subject="python-examples",
        title="Python mmap access modes: write-through changes a file, copy-on-write does not",
        summary="An mmap view has its own lifetime and access mode; closing the map does not close the source file.",
        contract="A temporary receipt file begins in the hold state. A writable map changes four status bytes to paid and flushes them. A later copy-on-write map changes the same bytes only in its private view. Reading the file afterward still returns paid.",
        boundary="An empty file cannot be mapped with this fixed-length fixture. A sliced flush can require page-aligned offsets, so this program flushes the whole mapping. Flush and close do not establish power-loss durability; applications requiring it need a platform-aware filesystem sync and recovery design.",
        source='''import mmap
from pathlib import Path
from tempfile import TemporaryDirectory

with TemporaryDirectory() as directory:
    receipt_path = Path(directory) / "receipt-47.state"
    receipt_path.write_bytes(b"R-0047:hold")
    with receipt_path.open("r+b") as receipt_file:
        with mmap.mmap(receipt_file.fileno(), 0, access=mmap.ACCESS_WRITE) as view:
            view[7:11] = b"paid"
            view.flush()
        with mmap.mmap(receipt_file.fileno(), 0, access=mmap.ACCESS_COPY) as private_view:
            private_view[7:11] = b"void"
            print("private", bytes(private_view[:]))
    print("stored", receipt_path.read_bytes())''',
        expected="private b'R-0047:void'\nstored b'R-0047:paid'",
        cost="Mapping uses virtual address space proportional to the mapped region; pages are loaded as accessed. A full flush may touch many dirty pages. It is not automatically faster than a small ordinary file write.",
        mistakes=["ACCESS_COPY edits are not persisted to the source file.", "Closing a map does not close the file object that provided its descriptor.", "A successful flush is not a cross-platform crash-durability promise."],
        related=["python/atomic-file-replacement", "python/memoryview-buffers", "python/pathlib-files"],
    ),
    dict(
        slug="scandir-stale-metadata", section="python/examples", subject="python-examples",
        title="Python os.scandir metadata: a cached DirEntry is not a fresh file check",
        summary="A DirEntry can cache stat data even when the named file changes afterward.",
        contract="The fixture scans an owned temporary directory, obtains a receipt file's size, rewrites the file with a longer payload, and reads its cached DirEntry size again. A fresh os.stat call reports the new size. The comparison isolates metadata caching from the file's current bytes.",
        boundary="A fresh stat still does not make a later open atomic with that check. Concurrent replacement or symlink changes require descriptor-based ownership rules, not an earlier filename test. This program changes its own file and makes no claim about hostile filesystem races.",
        source='''import os
from pathlib import Path
from tempfile import TemporaryDirectory

with TemporaryDirectory() as directory:
    receipt_path = Path(directory) / "receipt-47.state"
    receipt_path.write_bytes(b"ok")
    with os.scandir(directory) as entries:
        receipt_entry = next(entry for entry in entries if entry.name == receipt_path.name)
        before = receipt_entry.stat(follow_symlinks=False).st_size
        receipt_path.write_bytes(b"paid")
        cached = receipt_entry.stat(follow_symlinks=False).st_size
        fresh = os.stat(receipt_entry.path, follow_symlinks=False).st_size
    print("before", before)
    print("cached", cached)
    print("fresh", fresh)''',
        expected="before 2\ncached 2\nfresh 4",
        cost="scandir avoids some metadata system calls during enumeration; a fresh stat incurs another call. Retaining DirEntry objects for later decisions is both stale-data risk and unnecessary memory retention.",
        mistakes=["Do not store DirEntry metadata as a lasting file identity.", "A fresh stat followed by a separate open still permits a race.", "Directory enumeration order is unspecified; sort names when output order matters."],
        related=["python/pathlib-files", "python/filesystem-byte-path-roundtrip", "python/atomic-file-replacement"],
    ),
    dict(
        slug="sqlite-row-name-collision", section="python/examples", subject="python-examples",
        title="Python SQLite Row: duplicate result names make named access ambiguous",
        summary="sqlite3.Row gives named access, but duplicate result-column names collapse to one lookup key.",
        contract="A selected receipt has distinct aliases for its ID and state, so named access is clear. A second projection deliberately assigns the same alias to both fields; its keys contain that name twice, while lookup by that name returns only one value. The program does not use the ambiguous projection for a business decision.",
        boundary="A row factory changes Python result shape, not the database schema or SQL column identity. Assign unique aliases to every projected value before mapping rows into application records. This fixture uses an owned query and does not validate arbitrary received SQL.",
        source='''import sqlite3

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
    connection.close()''',
        expected="record 47 paid\nduplicate_names 2\nnamed_value 47",
        cost="Row objects keep the result values and name lookup structure for each row. Unique aliases cost little and prevent silent confusion when a query joins tables with repeated column names.",
        mistakes=["Duplicate aliases make name lookup ambiguous even if positional values differ.", "row_factory does not validate a record's domain fields.", "Prefer a deliberate projection to SELECT * when joins add repeated names."],
        related=["python/sqlite-transactions", "python/pandas-joins", "python/typing-reference"],
    ),
]

new_paths = ["python/" + item["slug"] for item in lessons]
assert not any(path in by_path for path in new_paths)
titles = {row["path"]: row["title"] for row in rows}
titles.update({path: item["title"] for path, item in zip(new_paths, lessons)})

for order, (item, path) in enumerate(zip(lessons, new_paths)):
    assert all(target in titles for target in item["related"]), path
    body = "<p>" + html.escape(item["summary"]) + "</p>"
    body += "<h2>Operation contract</h2><p>" + html.escape(item["contract"]) + "</p>"
    body += "<h2>Failure boundary</h2><p>" + html.escape(item["boundary"]) + "</p>"
    body += '<h2>Working program</h2><pre><code class="language-python">' + html.escape(item["source"], quote=False) + "</code></pre>"
    body += '<h3>Output</h3><pre><code class="language-text">' + html.escape(item["expected"], quote=False) + "</code></pre>"
    body += "<h2>Costs and limits</h2><p>" + html.escape(item["cost"]) + "</p>"
    body += "<h3>Common Mistakes</h3><ul>" + "".join("<li>" + html.escape(mistake) + "</li>" for mistake in item["mistakes"]) + "</ul>"
    body += "<h2>Connected lessons</h2><ul>" + "".join(
        '<li><a href="/' + target + '">' + html.escape(titles[target]) + "</a></li>"
        for target in item["related"]
    ) + "</ul>"
    row = copy.deepcopy(by_path["python/async-task-groups"])
    row.update(id=str(uuid.uuid5(uuid.NAMESPACE_URL, "https://aitrove.in/" + path)),
               path=path, title=item["title"], summary=item["summary"], body=body,
               subject=item["subject"], tags=["python", item["slug"]],
               sort_order=8600 + order, published_at=stamp, created_at=stamp, updated_at=stamp)
    row["data"] = {"subject_root": "python/python-programming-language-tutorial",
                   "section_path": item["section"], "content_format": "html", "kind": "tutorial",
                   "python_version": "3.11+ syntax; verified on local CPython",
                   "python_minimum": "3.11", "reading_minutes": 5,
                   "author_path": "authors/aitrove-editorial",
                   "download_path": "/downloads/aitrove-python-source-kit.zip",
                   "related": [{"path": target, "title": titles[target]} for target in item["related"]],
                   "seo_ready": True, "expected_output": item["expected"]}
    rows.append(row)
    by_path[path] = row

for section in sorted({item["section"] for item in lessons}):
    paths = ["python/" + item["slug"] for item in lessons if item["section"] == section]
    hub = by_path[section]
    hub["data"]["modules"].append({"title": "Bounded streams and storage controls",
                                   "summary": "Checked local programs with explicit failure and ownership limits.",
                                   "lessons": paths})
    hub["body"] += "<h2>Bounded streams and storage controls</h2><ul>" + "".join(
        '<li><a href="/' + path + '">' + html.escape(titles[path]) + "</a></li>"
        for path in paths) + "</ul>"
    hub["updated_at"] = stamp

parent = by_path["python/python-programming-language-tutorial"]
parent["body"] += "<h2>Bounded streams and storage controls</h2><ul>" + "".join(
    '<li><a href="/' + path + '">' + html.escape(titles[path]) + "</a></li>"
    for path in new_paths) + "</ul>"
parent["updated_at"] = stamp

for source, target in [
    ("python/socket-frame-reading", "python/async-length-prefixed-frame"),
    ("python/async-timeout-boundary", "python/async-delimiter-overrun"),
    ("python/sqlite-transactions", "python/sqlite-blob-handle"),
    ("python/sqlite-foreign-key-boundary", "python/sqlite-authorizer-policy"),
    ("python/sqlite-writer-contention", "python/sqlite-progress-budget"),
    ("python/bounded-json-lines", "python/sqlite-sql-length-limit"),
    ("python/memoryview-buffers", "python/mmap-write-vs-copy"),
    ("python/pathlib-files", "python/scandir-stale-metadata"),
    ("python/pandas-joins", "python/sqlite-row-name-collision"),
]:
    row = by_path[source]
    row["body"] += '<p><a href="/' + target + '">Continue with ' + html.escape(titles[target]) + "</a>.</p>"
    row["updated_at"] = stamp

quiz_path = "quizzes/python-stream-storage-boundaries"
assert quiz_path not in by_path
quiz = copy.deepcopy(by_path["quizzes/python-boundary-contracts"])
quiz_body = "<p>Check byte-frame parsing, SQLite connection controls, mapped files, and directory metadata.</p><h2>Review the related lessons</h2><ul>"
quiz_body += "".join('<li><a href="/' + path + '">' + html.escape(titles[path]) + "</a></li>" for path in new_paths)
quiz_body += "</ul><h3>Common Mistakes</h3><p>A passing local fixture does not prove a network or storage service is safe under concurrent clients.</p>"
quiz.update(id=str(uuid.uuid5(uuid.NAMESPACE_URL, "https://aitrove.in/" + quiz_path)),
            path=quiz_path, title="Python stream and storage boundaries quiz",
            summary="Twelve explained questions on byte streams, SQLite controls, mapped files and directory metadata.",
            body=quiz_body, sort_order=8700, published_at=stamp, created_at=stamp, updated_at=stamp)
raw_questions = [
    ("Which read call enforces a complete fixed-size byte frame?", "readexactly", "read", "readline", "A positive read size is only a maximum; readexactly detects a short frame."),
    ("When should a declared frame length be checked?", "Before reading the body", "After decoding the entire body", "Only after EOF", "An oversized declaration can be rejected before waiting for its payload."),
    ("What does IncompleteReadError.partial contain?", "Bytes received before EOF", "A valid shortened record", "Only the length header", "Partial bytes are failure evidence, not an accepted record."),
    ("What remains after readuntil raises LimitOverrunError?", "The buffered data", "An automatically truncated valid line", "An empty reader", "The unsuccessful delimiter scan leaves the data buffered."),
    ("Can sqlite3.Blob.write extend a reserved six-byte BLOB?", "No", "Yes, inside BEGIN", "Only with row_factory", "A blob handle edits fixed allocated storage."),
    ("Where does a SQLite authorizer policy apply?", "On its configured connection", "On every database file in the process", "On all Python code", "Another connection requires its own callback and policy."),
    ("What does a SQLite progress-handler callback count measure?", "Virtual-machine instruction intervals", "Elapsed milliseconds", "Process resident memory", "The callback interval is tied to SQLite execution steps rather than a clock."),
    ("What does SQLITE_LIMIT_SQL_LENGTH constrain?", "SQL statement text", "Every bound value", "Number of rows returned", "Parameterized values require their own size policy."),
    ("Which mmap access mode keeps edits private?", "ACCESS_COPY", "ACCESS_WRITE", "ACCESS_READ", "Copy-on-write changes the view without persisting those edits to the source file."),
    ("Does mmap.flush prove survival of a sudden power loss?", "No", "Yes on every platform", "Only for an empty file", "A storage durability policy needs more than this fixture's flush."),
    ("May a retained DirEntry.stat value be stale after a file changes?", "Yes", "No, it always refreshes", "Only after a process restart", "DirEntry can cache metadata; a new stat reads current metadata."),
    ("Why avoid duplicate result aliases with sqlite3.Row?", "Named lookup may select only one of several values", "Duplicate aliases force a database rollback", "Row objects reject the query", "Unique projection names make application field mapping unambiguous."),
]
quiz["data"]["questions"] = []
for index, (prompt, correct, wrong_a, wrong_b, explanation) in enumerate(raw_questions):
    options = [correct, wrong_a, wrong_b]
    options = options[index % 3:] + options[:index % 3]
    quiz["data"]["questions"].append({"prompt": prompt, "options": options,
                                      "answer": options.index(correct), "explanation": explanation})
rows.append(quiz)
by_path[quiz_path] = quiz
quiz_hub = by_path["python/quizzes"]
quiz_hub["data"]["modules"][-1]["lessons"].append(quiz_path)
needle = "</ul><h2>Continue learning</h2>"
assert needle in quiz_hub["body"], "quiz hub insertion point moved"
quiz_hub["body"] = quiz_hub["body"].replace(needle,
    '<li><a href="/' + quiz_path + '">' + html.escape(quiz["title"]) + "</a></li>" + needle)
parent["body"] += '<p><a href="/' + quiz_path + '">Check the stream and storage quiz</a>.</p>'
for path in new_paths:
    by_path[path]["body"] += '<p><a href="/' + quiz_path + '">Test this contract</a>.</p>'

fixture.write_text(json.dumps(rows, ensure_ascii=False, indent=2) + "\n")
print("Added", len(lessons), "lessons and one quiz")
