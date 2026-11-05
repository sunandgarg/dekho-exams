"""Add executable Python lifetime and I/O contracts plus an explained quiz."""

import copy
import datetime
import html
import json
import pathlib
import uuid

root = pathlib.Path(__file__).resolve().parents[1]
fixture = root / "src/data/fixtures.json"
rows = json.loads(fixture.read_text())
by_path = {row["path"]: row for row in rows}
stamp = datetime.datetime.now(datetime.UTC).isoformat()

lessons = [
    dict(slug="multiprocessing-spawn-guard", section="python/advanced-python", subject="python-advanced",
         title="Python multiprocessing spawn: keep startup behind the main guard",
         summary="A spawned worker imports the main module again, so process creation must not run during import.",
         contract="The receipt calculation is a top-level function that a fresh interpreter can import. The process and queue are created only under the main guard. An explicit spawn context makes the behavior visible even on a system whose default differs. The parent receives one result and joins the child before declaring success.",
         boundary="This source must run from a real file; pasting it into a REPL does not provide an importable main module. Queue.get has a timeout, but if it expires the owner still needs to stop and join the worker in a production error path. The fixture's worker exits normally, so it does not prove crash recovery, queue persistence, or safe forced termination.",
         source='''from multiprocessing import get_context

def revise_receipt(quantity, outbound):
    outbound.put(quantity + 1)

if __name__ == "__main__":
    context = get_context("spawn")
    outbound = context.Queue()
    worker = context.Process(target=revise_receipt, args=(46, outbound))
    worker.start()
    print("revision", outbound.get(timeout=3))
    worker.join(timeout=3)
    print("exit", worker.exitcode)
    outbound.close()
    outbound.join_thread()''',
         expected="revision 47\nexit 0",
         cost="Spawn starts another interpreter and serializes arguments. That setup costs much more than this addition; process work needs enough CPU load to justify it.",
         mistakes=["A nested function or REPL lambda may not be importable by a spawned child.", "A queue result is not a durable job acknowledgement.", "A timed-out get does not release a still-running child."],
         related=["python/thread-pools", "python/subprocess-timeout-reap", "python/package-layout"]),
    dict(slug="contextvars-task-snapshot", section="python/advanced-python", subject="python-advanced",
         title="Python ContextVar tasks: capture request context at task creation",
         summary="An asyncio task receives a copy of the current context when it is created unless a context is supplied.",
         contract="The parent assigns tenant north-47 and creates a task waiting on a gate. Before opening the gate, the parent changes its own tenant to south-47. The task still reads the value captured at creation. That is useful for request labels, but only when task creation happens under the intended request context.",
         boundary="ContextVar values are not an authorization decision. A copied reference to a mutable object can still alias that object, so store immutable identifiers rather than a shared mutable request bag. Explicitly reset tokens in the same context after a request. Thread and process handoffs have their own propagation rules.",
         source='''import asyncio
from contextvars import ContextVar

tenant_id = ContextVar("tenant_id")

async def read_tenant(gate):
    await gate.wait()
    return tenant_id.get()

async def main():
    token = tenant_id.set("north-47")
    try:
        gate = asyncio.Event()
        reader = asyncio.create_task(read_tenant(gate))
        tenant_id.set("south-47")
        gate.set()
        print("task", await reader)
        print("parent", tenant_id.get())
    finally:
        tenant_id.reset(token)

asyncio.run(main())''',
         expected="task north-47\nparent south-47",
         cost="Creating a task copies context bindings. Large mutable objects referenced by those bindings can outlive a request if tasks remain alive.",
         mistakes=["Changing the parent context after task creation does not rewrite the task copy.", "Context propagation does not authorize a tenant operation.", "A copied context binding can still reference mutable shared state."],
         related=["python/async-to-thread-context", "python/async-task-groups", "python/logging-context"]),
    dict(slug="weakref-cache-ownership", section="python/advanced-python", subject="python-advanced",
         title="Python weak-value cache: an entry does not own its result",
         summary="WeakValueDictionary drops an entry when no strong reference keeps its value alive.",
         contract="A receipt snapshot is inserted into a weak-value index while a caller holds it. Once that caller releases the last strong reference, collection removes the cache entry. The explicit collection makes the local CPython result observable; the timing is not a portable cache-expiration clock.",
         boundary="A weak cache cannot promise a hit even moments after insertion. Some built-in values cannot be weakly referenced. Do not store the only copy of business data here, and do not rely on a weak-reference callback to close a critical resource or commit a transaction.",
         source='''import gc
import weakref

class ReceiptSnapshot:
    def __init__(self, revision):
        self.revision = revision

snapshots = weakref.WeakValueDictionary()
current = ReceiptSnapshot(47)
snapshots["north-47"] = current
print("held", "north-47" in snapshots)
del current
gc.collect()
print("after_release", "north-47" in snapshots)''',
         expected="held True\nafter_release False",
         cost="Lookup is expected O(1), but entries disappear with object lifetime. Recomputing a missing value can dominate dictionary cost.",
         mistakes=["A weak cache is not a durable store.", "Garbage collection is not a request deadline.", "Resource cleanup must have an explicit owner."],
         related=["python/functools-cache", "python/lru-project", "python/cached-property-invalidation"]),
    dict(slug="sqlite-migration-reopen-check", section="python/projects", subject="python-projects",
         title="Python SQLite migration: reopen the file after a failed upgrade",
         summary="A migration rollback should be checked through a fresh connection to the same database file.",
         contract="Version one is committed to a temporary disk database. A second connection attempts a column change and then fails on a duplicate table. After rollback and close, a third connection reads version and columns from the file. Reopening catches a class of mistakes that an in-memory connection-only assertion cannot show.",
         boundary="A temporary file is still not a production rehearsal. The fixture does not check lock contention, a large table rewrite, power loss, multiple app versions, or restoration from backup. Run the exact release sequence against a copy of realistic data and hold one migration owner at a time.",
         source='''import sqlite3
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
    print("columns", columns)''',
         expected="version 1\ncolumns ['receipt_id']",
         cost="A fresh connection adds file I/O and catches committed-state mistakes. Schema rewrites can block writers and need measurement at real data size.",
         mistakes=["Do not infer file state from one still-open connection alone.", "Updating the version marker before the schema succeeds mislabels the database.", "This fixture does not simulate a killed process mid-upgrade."],
         related=["python/sqlite-migration-rollback", "python/sqlite-backup-project", "python/sqlite-transactions"]),
    dict(slug="tar-extraction-byte-quota", section="python/projects", subject="python-projects",
         title="Python tar extraction: reject members before exceeding a byte quota",
         summary="An archive importer needs a limit on files and uncompressed bytes before writing each member.",
         contract="Two regular report members total 54 bytes, while this import accepts at most 50. The first file is written to a fresh directory; the second is rejected before opening a destination. Each member must stay beneath the reports folder, contain no parent component, and be a regular file. The code copies through a small chunk buffer rather than calling extractall.",
         boundary="The limit uses declared member sizes; a production importer should also count bytes actually read and written, reject truncated content, cap member count and name length, and remove the temporary directory on any failure. Concurrent changes to the source or destination need stronger isolation. This local archive is fixed and trusted for test construction.",
         source='''import io
import tarfile
import tempfile
from pathlib import Path, PurePosixPath

archive_bytes = io.BytesIO()
with tarfile.open(fileobj=archive_bytes, mode="w") as archive:
    for name, payload in (
        ("reports/receipt-47.txt", b"R" * 47),
        ("reports/receipt-48.txt", b"S" * 7),
    ):
        member = tarfile.TarInfo(name)
        member.size = len(payload)
        archive.addfile(member, io.BytesIO(payload))

archive_bytes.seek(0)
accepted = []
rejected = 0
total_bytes = 0
with tempfile.TemporaryDirectory() as directory:
    with tarfile.open(fileobj=archive_bytes, mode="r:") as archive:
        for member in archive:
            name = PurePosixPath(member.name)
            if (not member.isfile() or not name.parts or name.is_absolute()
                    or ".." in name.parts or name.parts[0] != "reports"
                    or total_bytes + member.size > 50):
                rejected += 1
                continue
            destination = Path(directory).joinpath(*name.parts)
            destination.parent.mkdir(parents=True, exist_ok=True)
            with archive.extractfile(member) as source, destination.open("xb") as target:
                remaining = member.size
                while remaining:
                    chunk = source.read(min(16, remaining))
                    if not chunk:
                        raise EOFError("truncated archive member")
                    target.write(chunk)
                    remaining -= len(chunk)
            total_bytes += member.size
            accepted.append(member.name)
print("accepted", accepted)
print("rejected", rejected)
print("bytes", total_bytes)''',
         expected="accepted ['reports/receipt-47.txt']\nrejected 1\nbytes 47",
         cost="The importer scans O(member count + extracted bytes), keeps a 16-byte application copy buffer, and writes up to the stated quota in this fixture.",
         mistakes=["The tar header's size is not a complete resource limit by itself.", "A safe filename check does not authorize links or special files.", "Duplicate names and case-insensitive collisions need an explicit policy."],
         related=["python/tar-member-preflight", "python/zip-member-validation", "python/gzip-output-budget"]),
    dict(slug="subprocess-stream-byte-cutoff", section="python/examples", subject="python-examples",
         title="Python subprocess pipe: stop after the first byte beyond budget",
         summary="A pipe reader can reject output as soon as it consumes one byte past the allowed limit.",
         contract="A fixed child writes 47,000 bytes. The parent reads only 4,097 bytes against a 4,096-byte contract, then kills and reaps the child. Unlike a post-run spool check, it does not wait for a full output file before rejecting. The one extra byte distinguishes exactly-at-limit from over-limit output.",
         boundary="This is one boundary, not a full untrusted-process runner. A child that emits fewer bytes and stalls can block read, so a separate wall-clock deadline is required. stderr is discarded here; a production runner needs a separate bounded diagnostic channel. The direct child is stopped, but a process tree requires an OS-specific group policy.",
         source='''import subprocess
import sys

child = subprocess.Popen(
    [sys.executable, "-c", "import sys; sys.stdout.buffer.write(b'R' * 47000)"],
    stdout=subprocess.PIPE,
    stderr=subprocess.DEVNULL,
)
prefix = child.stdout.read(4097)
too_large = len(prefix) > 4096
if too_large:
    child.kill()
child.stdout.close()
child.wait(timeout=5)
print("too_large", too_large)
print("reaped", child.returncode is not None)''',
         expected="too_large True\nreaped True",
         cost="The decision retains O(limit) bytes and stops reading after limit plus one. Kernel pipe and buffered-reader capacity add bounded buffering; a separate timeout is still required.",
         mistakes=["A byte cutoff is not a wall-clock cutoff.", "Closing stdout without reaping leaves process ownership unresolved.", "A discarded stderr pipe cannot later supply diagnostics."],
         related=["python/subprocess-output-spool", "python/subprocess-timeout-reap", "python/spooled-file-budgets"]),
    dict(slug="socket-idle-timeout", section="python/advanced-python", subject="python-advanced",
         title="Python socket idle timeout: bound one blocking receive",
         summary="A socket timeout limits how long one receive waits for data; it does not define a whole-request deadline.",
         contract="A local socket pair has no incoming byte at first, so recv raises a timeout. The peer then sends one byte, and the next receive succeeds. This shows the per-operation idle boundary without contacting a remote host. A framed protocol still needs length limits and enough reads to assemble a message.",
         boundary="Repeated successful one-byte receives can extend total elapsed time indefinitely. Track an overall deadline separately, validate frame length before allocation, and close both sockets on every path. Socket pair availability and exact timing vary by platform; the fixture checks only local stream behavior.",
         source='''import socket

reader, writer = socket.socketpair()
with reader, writer:
    reader.settimeout(0.02)
    try:
        reader.recv(1)
    except socket.timeout:
        print("idle_timeout", True)
    writer.sendall(b"R")
    print("received", reader.recv(1).decode("ascii"))''',
         expected="idle_timeout True\nreceived R",
         cost="The fixture waits about 20 milliseconds for the empty receive. Repeated timeouts or tiny reads can still waste CPU and connections without a total deadline.",
         mistakes=["An idle timeout is not an overall request deadline.", "One recv is not one application message.", "Always close both socket owners after a failed read."],
         related=["python/socket-frame-reading", "python/async-deadlines", "python/url-target-policy"]),
    dict(slug="hashlib-streaming-integrity", section="python/examples", subject="python-examples",
         title="Python streaming SHA-256: hash bytes without a second full copy",
         summary="A digest can be updated in chunks while reading a byte stream, but it does not authenticate who supplied the bytes.",
         contract="The receipt payload is fed to SHA-256 seven bytes at a time. Its result matches a one-shot digest of the same bytes. The chunk loop is useful when the input is a file or stream and retaining another complete copy would be wasteful. The exact bytes and their order are part of the contract; text normalization changes the digest.",
         boundary="A matching digest detects accidental changes only when the expected digest comes from a trusted channel. An attacker who can replace both content and its plain digest can make them agree. Use a keyed MAC or signature for sender authentication. For an untrusted stream, enforce byte and time limits while hashing.",
         source='''import hashlib
import io

payload = b"R" * 47 + b"|north-47"
digest = hashlib.sha256()
source = io.BytesIO(payload)
while chunk := source.read(7):
    digest.update(chunk)
expected = hashlib.sha256(payload).digest()
print("same", digest.digest() == expected)
print("bytes", len(payload))''',
         expected="same True\nbytes 56",
         cost="Hashing visits each byte once and retains a fixed digest state plus one seven-byte chunk here. Its CPU cost grows linearly with input size.",
         mistakes=["A plain digest is not an authentication tag.", "Hash the exact bytes that the protocol defines.", "A streaming hash does not impose its own input-size limit."],
         related=["python/hmac-envelope", "python/pathlib-files", "python/zip-member-validation"]),
]

titles = {path: row["title"] for path, row in by_path.items()}
titles.update({"python/" + item["slug"]: item["title"] for item in lessons})
for order, item in enumerate(lessons):
    path = "python/" + item["slug"]
    assert path not in by_path
    for target in item["related"]:
        assert target in titles, (path, target)
    body = "<p>" + html.escape(item["summary"]) + "</p>"
    body += "<h2>Operation contract</h2><p>" + html.escape(item["contract"]) + "</p>"
    body += "<h2>Failure and ownership boundary</h2><p>" + html.escape(item["boundary"]) + "</p>"
    body += '<h2>Working program</h2><pre><code class="language-python">' + html.escape(item["source"], quote=False) + "</code></pre>"
    body += '<h3>Output</h3><pre><code class="language-text">' + html.escape(item["expected"], quote=False) + "</code></pre>"
    body += "<h2>Costs and limits</h2><p>" + html.escape(item["cost"]) + "</p>"
    body += "<h3>Common Mistakes</h3><ul>" + "".join("<li>" + html.escape(text) + "</li>" for text in item["mistakes"]) + "</ul>"
    body += "<h2>Connected lessons</h2><ul>" + "".join(
        '<li><a href="/' + target + '">' + html.escape(titles[target]) + "</a></li>"
        for target in item["related"]) + "</ul>"
    row = copy.deepcopy(by_path["python/async-task-groups"])
    row.update(id=str(uuid.uuid5(uuid.NAMESPACE_URL, "https://aitrove.in/" + path)),
               path=path, title=item["title"], summary=item["summary"], body=body,
               subject=item["subject"], tags=["python", item["slug"]],
               sort_order=7800 + order, published_at=stamp, created_at=stamp, updated_at=stamp)
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
    hub["data"]["modules"].append({"title": "Lifetime and I/O boundaries",
                                   "summary": "Runnable ownership and rejection contracts.", "lessons": paths})
    hub["body"] += "<h2>Lifetime and I/O boundaries</h2><ul>" + "".join(
        '<li><a href="/' + path + '">' + html.escape(titles[path]) + "</a></li>"
        for path in paths) + "</ul>"
    hub["updated_at"] = stamp

parent = by_path["python/python-programming-language-tutorial"]
parent["body"] += "<h2>Lifetime and I/O contracts</h2><ul>" + "".join(
    '<li><a href="/python/' + item["slug"] + '">' + html.escape(item["title"]) + "</a></li>"
    for item in lessons) + "</ul>"
parent["updated_at"] = stamp
for source, target in [
    ("python/thread-pools", "python/multiprocessing-spawn-guard"),
    ("python/async-task-groups", "python/contextvars-task-snapshot"),
    ("python/functools-cache", "python/weakref-cache-ownership"),
    ("python/sqlite-migration-rollback", "python/sqlite-migration-reopen-check"),
    ("python/tar-member-preflight", "python/tar-extraction-byte-quota"),
    ("python/subprocess-output-spool", "python/subprocess-stream-byte-cutoff"),
    ("python/socket-frame-reading", "python/socket-idle-timeout"),
    ("python/hmac-envelope", "python/hashlib-streaming-integrity"),
]:
    row = by_path[source]
    row["body"] += '<p><a href="/' + target + '">Continue with ' + html.escape(titles[target]) + "</a>.</p>"
    row["updated_at"] = stamp

quiz_path = "quizzes/python-lifetime-io-contracts"
assert quiz_path not in by_path
quiz = copy.deepcopy(by_path["quizzes/python-boundary-contracts"])
targets = ["python/" + item["slug"] for item in lessons]
quiz_body = "<p>Test lifecycle and byte-boundary decisions before adapting these local programs.</p><h2>Review the related lessons</h2><ul>"
quiz_body += "".join('<li><a href="/' + path + '">' + html.escape(titles[path]) + "</a></li>" for path in targets)
quiz_body += "</ul><h3>Common Mistakes</h3><p>The quiz does not certify process supervision, remote sockets, or archive intake under hostile load.</p>"
quiz.update(id=str(uuid.uuid5(uuid.NAMESPACE_URL, "https://aitrove.in/" + quiz_path)),
            path=quiz_path, title="Python lifetime and I/O contract quiz",
            summary="Twelve explained questions on process startup, task context, storage, archives and streams.",
            body=quiz_body, sort_order=7900, published_at=stamp, created_at=stamp, updated_at=stamp)
raw_questions = [
    ("Why put multiprocessing startup under a main guard?", "A spawned interpreter imports the module again", "The queue cannot hold integers", "The worker needs a global lock", "Import-time process creation can recursively create workers."),
    ("What must a spawned worker target usually be?", "Importable and picklable", "A REPL lambda", "A closed local function", "A fresh interpreter must locate and serialize the target."),
    ("When is an asyncio task's default context copied?", "At task creation", "At the next print call", "Only after its first exception", "Later parent changes do not rewrite an already created task's context."),
    ("Does a copied ContextVar binding deep-copy a mutable value?", "No, the referenced object can still be shared", "Yes, recursively", "Only on process exit", "Context copying binds values; it is not a deep-copy operation."),
    ("What keeps a weak-value cache entry present?", "A strong reference to its value elsewhere", "The cache key alone", "A timer inside the dictionary", "Weak mappings do not own the value's lifetime."),
    ("What does reopening a SQLite file test after rollback?", "Committed state visible to a fresh connection", "Power-loss survival", "Migration speed on production data", "A fresh connection reads the file state rather than one connection's in-memory view."),
    ("When does the tar quota fixture reject its second member?", "Before opening the destination file", "After writing its full payload", "Only after extractall completes", "Declared size would push the total past the accepted byte budget."),
    ("What further check should an untrusted tar importer make while copying?", "Count actual bytes read and written", "Trust only the header size", "Ignore duplicate names", "Headers are one layer; actual consumption also needs a limit."),
    ("Why read limit plus one bytes from a subprocess pipe?", "To distinguish exactly-at-limit from over-limit", "To authenticate the child", "To make output UTF-8", "The extra byte is the first proof that the budget was exceeded."),
    ("What can still hang in the pipe cutoff fixture?", "A child that emits too few bytes and stalls", "A child that has already been reaped", "A finished fixed output string", "A byte budget needs a separate wall-clock deadline."),
    ("Does a socket idle timeout bound total request time?", "No, repeated progress can extend the operation", "Yes, across every future recv", "Only when the peer sends zero bytes", "A per-call wait and an overall deadline are separate contracts."),
    ("What does a plain SHA-256 digest fail to prove?", "Who supplied the bytes", "Whether two digests of identical bytes agree", "Whether bytes were visited in order", "Authentication needs a trusted expected value, a keyed MAC, or a signature."),
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
quiz_hub["body"] = quiz_hub["body"].replace("</ul><h2>Continue learning</h2>",
    '<li><a href="/' + quiz_path + '">' + html.escape(quiz["title"]) + "</a></li></ul><h2>Continue learning</h2>")
parent["body"] += '<p><a href="/' + quiz_path + '">Check the lifetime and I/O quiz</a>.</p>'
for path in targets:
    by_path[path]["body"] += '<p><a href="/' + quiz_path + '">Test this boundary</a>.</p>'

fixture.write_text(json.dumps(rows, ensure_ascii=False, indent=2) + "\n")
print("Added", len(lessons), "lessons and one quiz")
