"""Add runnable Python lessons for concurrency, storage and algorithms."""

import copy
import datetime
import html
import json
import pathlib
import re
import uuid

ROOT = pathlib.Path(__file__).resolve().parents[1]
FIXTURE = ROOT / "src/data/fixtures.json"
rows = json.loads(FIXTURE.read_text())
by_path = {row["path"]: row for row in rows}
stamp = datetime.datetime.now(datetime.UTC).isoformat()


def prose(value):
    return re.sub(
        r"\[\[([^|]+)\|([^\]]+)\]\]",
        lambda match: '<a href="/' + match[1] + '">' + match[2] + "</a>",
        html.escape(value),
    )


lessons = [
    dict(
        slug="async-semaphore-admission", section="python/advanced-python", subject="python-advanced",
        title="Python asyncio Semaphore: bound active work, not queued tasks",
        summary="An asyncio semaphore limits simultaneous entries into a critical section; it does not bound the number of waiting tasks.",
        explanation="A delivery-status client permits only two active requests to a downstream service. The semaphore holds that limit, but all four scheduled tasks still exist and can retain their inputs while waiting. For an unbounded feed, admit jobs through [[python/async-queues|a bounded queue]] before creating tasks. [[python/async-task-groups|Task groups]] own the child lifetimes; they do not impose admission limits by themselves.",
        boundary="Cancellation inside async with releases a permit as the context exits. A coroutine that catches CancelledError for cleanup should normally propagate it after cleanup; suppressing it can confuse structured concurrency. A semaphore does not turn a blocking library call into cooperative I/O. The program deliberately uses sleep(0) to yield while the limit is held, making the observed peak repeatable.",
        source='''import asyncio

async def main():
    gate = asyncio.Semaphore(2)
    active = 0
    peak = 0

    async def fetch_status(parcel_id):
        nonlocal active, peak
        async with gate:
            active += 1
            peak = max(peak, active)
            await asyncio.sleep(0)
            active -= 1
            return parcel_id

    async with asyncio.TaskGroup() as group:
        tasks = [group.create_task(fetch_status(parcel_id))
                 for parcel_id in ("P-47", "P-48", "P-49", "P-50")]
    print("scheduled:", len(tasks))
    print("peak:", peak)
    print("results:", [task.result() for task in tasks])

asyncio.run(main())''',
        expected="scheduled: 4\npeak: 2\nresults: ['P-47', 'P-48', 'P-49', 'P-50']",
        cost="The permit count is bounded, but task memory grows with admitted inputs. A fixed-capacity queue is required to bound waiting payloads.",
        mistakes=["A semaphore does not cap the number of created tasks.", "Do not swallow cancellation and claim the request stopped.", "Async syntax does not make synchronous blocking I/O cooperative."],
        related=["python/async-queues", "python/async-task-groups", "python/async-deadlines"],
    ),
    dict(
        slug="future-cancel-before-start", section="python/advanced-python", subject="python-advanced",
        title="Python Future cancellation: queued work versus running work",
        summary="Future.cancel() can prevent a queued executor call from starting, but cannot interrupt a callable that is already running.",
        explanation="A single-worker pool is occupied with one ledger export. A second export remains queued, so cancel() can remove it before a worker begins. Once a callable is running, cancel() returns False; the callable needs its own cooperative stop rule. [[python/thread-pools|Worker count]] limits parallel execution, not retained queue memory.",
        boundary="Two events make the transition observable. The first worker signals that it started, then waits until the caller releases it. In application code, release that wait in a finally block so an assertion or shutdown failure cannot strand the pool. A timeout on future.result() stops only the caller's wait. It does not stop the worker.",
        source='''from concurrent.futures import ThreadPoolExecutor
from threading import Event

started = Event()
release = Event()

def export_ledger():
    started.set()
    release.wait()
    return "ledger-ready"

with ThreadPoolExecutor(max_workers=1) as workers:
    running = workers.submit(export_ledger)
    started.wait()
    pending = workers.submit(lambda: "second-export")
    print("pending cancelled:", pending.cancel())
    release.set()
    print("running result:", running.result())
    print("second cancelled:", pending.cancelled())''',
        expected="pending cancelled: True\nrunning result: ledger-ready\nsecond cancelled: True",
        cost="Every queued Future retains a callable and its arguments. Large payloads need admission control before submission.",
        mistakes=["A result timeout does not stop a running callable.", "cancel() cannot forcibly interrupt a worker in progress.", "A small worker count does not imply a small queue."],
        related=["python/thread-pools", "python/condition-predicates", "python/async-semaphore-admission"],
    ),
    dict(
        slug="queue-task-done-ownership", section="python/advanced-python", subject="python-advanced",
        title="Python Queue task_done: completion accounting includes shutdown items",
        summary="Queue.join() needs one task_done() for each queued item, including a sentinel that stops the worker.",
        explanation="A receipt printer consumes two jobs and then a shutdown sentinel. Every successful get() creates a completion obligation. Calling task_done() in finally satisfies that obligation even when the worker returns on the sentinel. A completed queue counter says all items were acknowledged by workers; it does not prove a remote printer or database committed the result. [[python/idempotent-jobs|Idempotent job handling]] covers replay after a process failure.",
        boundary="One worker makes output order stable. With several workers, enqueue one sentinel for each worker after ordinary work, or use an explicit shutdown protocol. Calling task_done() twice raises ValueError. A daemon worker can be terminated at process exit, so it is not a durability guarantee.",
        source='''from queue import Queue
from threading import Thread

jobs = Queue()
processed = []

def print_receipts():
    while True:
        receipt_id = jobs.get()
        try:
            if receipt_id is None:
                return
            processed.append(receipt_id)
        finally:
            jobs.task_done()

worker = Thread(target=print_receipts)
worker.start()
for receipt_id in ("R-47", "R-48"):
    jobs.put(receipt_id)
jobs.put(None)
jobs.join()
worker.join()
print("processed:", processed)
print("unfinished:", jobs.unfinished_tasks)''',
        expected="processed: ['R-47', 'R-48']\nunfinished: 0",
        cost="An unlimited queue retains all submitted payloads. Set maxsize and measure both item count and retained bytes.",
        mistakes=["A sentinel needs task_done() too.", "Queue.join() is not proof of an external commit.", "Do not submit unbounded payloads to an unlimited queue."],
        related=["python/async-queues", "python/thread-pools", "python/idempotent-jobs"],
    ),
    dict(
        slug="sqlite-busy-write-contract", section="python/examples", subject="python-examples",
        title="Python SQLite busy writer: handle contention as a bounded outcome",
        summary="SQLite can reject a second writer while another write transaction owns the lock.",
        explanation="Two connections target one database file. The first begins an immediate transaction and inserts a receipt. The second has a zero busy timeout, so its competing BEGIN fails immediately. After the first commits, the second can start a new transaction. [[python/sqlite-writer-contention|Writer contention]] is a process-level concern, not merely a thread scheduling detail.",
        boundary="A lock error does not say that the first command failed. If the second operation retries, it needs a stable business key and a bounded attempt policy. Do not hold a write transaction over a network call while other writers wait. The fixture uses explicit BEGIN with isolation_level=None to expose the lock boundary; [[python/sqlite-transactions|transaction ownership]] should remain in one application layer.",
        source='''import sqlite3
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
    contender.close()''',
        expected="second writer blocked\nrows: 2",
        cost="A longer busy timeout waits rather than failing immediately, but holds a request worker. Keep transactions short and size retry time to the service deadline.",
        mistakes=["Do not classify every OperationalError as a lock error in production.", "Do not retry a non-idempotent command under a new identity.", "Do not hold an immediate transaction during HTTP calls."],
        related=["python/sqlite-writer-contention", "python/sqlite-transactions", "python/sqlite-conflict-update"],
    ),
    dict(
        slug="sqlite-wal-snapshot-read", section="python/examples", subject="python-examples",
        title="Python SQLite WAL reader: an open transaction keeps its snapshot",
        summary="A SQLite reader in WAL mode can continue seeing its earlier snapshot after another connection commits.",
        explanation="A report begins a read transaction and sees 47 units. Another connection commits an update to 52. The report still sees 47 until it ends that transaction; a new read then sees 52. This supports a consistent report, but is not a live view. [[python/sqlite-checkpoint-project|WAL checkpoints]] and [[python/sqlite-backup-project|backups]] have separate lifecycle rules.",
        boundary="A long reader can keep WAL content from being reclaimed. Do not hold a read transaction while formatting or sending a large response. The example uses a temporary file because separate :memory: connections would be separate databases and could not show one shared snapshot.",
        source='''import sqlite3
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
    writer.close()''',
        expected="snapshot: 47 47\nnew read: 52",
        cost="A stable read trades freshness for consistency and can delay checkpoint progress. Measure WAL growth under long reports.",
        mistakes=["An open read transaction does not see later commits.", "Two :memory: connections do not test one shared database.", "Do not retain a report transaction longer than its consistency need."],
        related=["python/sqlite-checkpoint-project", "python/sqlite-backup-project", "python/sqlite-busy-write-contract"],
    ),
    dict(
        slug="json-nonfinite-number-boundary", section="python/examples", subject="python-examples",
        title="Python JSON nonfinite numbers: reject NaN on input and output",
        summary="Python's json defaults can accept or emit NaN and infinity, so a strict wire boundary needs explicit checks.",
        explanation="A risk-score service receives a payload containing NaN. Python accepts that token by default even though it is outside strict JSON number grammar. The parse_constant hook rejects it. On output, allow_nan=False prevents the service from emitting a nonfinite float. [[python/json-duplicate-keys|Duplicate object names]] are another decoder policy and require their own check.",
        boundary="The hook does not validate numeric ranges, nesting depth or application schema. Enforce a byte budget before parsing an untrusted body. For exact decimal money, choose [[python/decimal-money|a decimal representation]] and a deliberate serialization format rather than relying on binary float conversion.",
        source='''import json

def reject_nonfinite(token):
    raise ValueError("nonfinite number: " + token)

try:
    json.loads('{"risk": NaN}', parse_constant=reject_nonfinite)
except ValueError as error:
    print(error)

print("accepted:", json.loads('{"risk": 47}')["risk"])
try:
    json.dumps({"risk": float("nan")}, allow_nan=False)
except ValueError:
    print("nonfinite output rejected")''',
        expected="nonfinite number: NaN\naccepted: 47\nnonfinite output rejected",
        cost="The token check is small relative to parsing. Input bytes and nesting still need separate limits.",
        mistakes=["Do not assume the default parser rejects NaN.", "Do not emit nonfinite floats into a strict JSON API.", "A nonfinite check is not a complete schema validator."],
        related=["python/json-duplicate-keys", "python/json-validation", "python/decimal-money"],
    ),
    dict(
        slug="heap-priority-revision", section="python/dsa-in-python", subject="python-dsa",
        title="Python heapq priority updates: skip stale entries",
        summary="heapq has no decrease-key operation; a version map lets a consumer discard superseded entries.",
        explanation="A dispatcher ranks one parcel at priority 7, then raises it to priority 2. Pushing another tuple does not remove the old one. A map records the current priority and sequence for each parcel; pop discards tuples that no longer match. A monotonic sequence breaks equal-priority ties without comparing parcel objects. [[python/heap-top-k|Top-k selection]] needs less bookkeeping when priorities never change.",
        boundary="This is lazy deletion. Many revisions without draining grow heap memory even if the current map has one key. Rebuild from current entries above a measured stale-entry threshold. The parcel identifier must remain a stable hash key; [[python/hash-equality|mutable hash keys]] break lookup.",
        source='''import heapq
from itertools import count

pending = []
current = {}
sequence = count()
stale = 0

def set_priority(parcel_id, priority):
    revision = next(sequence)
    current[parcel_id] = (priority, revision)
    heapq.heappush(pending, (priority, revision, parcel_id))

def take_next():
    global stale
    while pending:
        priority, revision, parcel_id = heapq.heappop(pending)
        if current.get(parcel_id) != (priority, revision):
            stale += 1
            continue
        del current[parcel_id]
        return parcel_id
    return None

set_priority("P-47", 7)
set_priority("P-48", 5)
set_priority("P-47", 2)
print(take_next())
print(take_next())
print(take_next())
print("stale:", stale)''',
        expected="P-47\nP-48\nNone\nstale: 1",
        cost="Each push and pop takes O(log h) for h heap entries. Storage follows total revisions until stale entries are drained or compacted.",
        mistakes=["A new priority does not remove the old tuple.", "Do not compare arbitrary task objects to break ties.", "Do not ignore stale-entry memory under frequent updates."],
        related=["python/heap-top-k", "python/hash-equality", "python/running-median-heaps"],
    ),
    dict(
        slug="topological-cycle-witness", section="python/dsa-in-python", subject="python-dsa",
        title="Python topological failure: return a cycle witness",
        summary="A directed cycle makes a topological order impossible; the active DFS path can identify it.",
        explanation="A shipment workflow has receive, validate and dispatch stages. Dispatch depends on receive, closing the cycle. Returning the offending path gives an operator a specific configuration error instead of an empty schedule. [[python/topological-sort|Topological sorting]] handles acyclic dependencies; [[python/strongly-connected-components|strong components]] help when many cycles must be grouped.",
        boundary="DFS state distinguishes unseen, active-path and completed nodes. Only an edge to an active node proves a cycle on the current traversal. This recursive version is suitable for bounded configuration graphs; an untrusted deep graph needs an iterative stack to avoid Python's recursion limit.",
        source='''graph = {
    "receive": ["validate"],
    "validate": ["dispatch"],
    "dispatch": ["receive"],
}
state = {}
path = []

def cycle_from(stage):
    state[stage] = "active"
    path.append(stage)
    for dependency in graph[stage]:
        if state.get(dependency) == "active":
            return path[path.index(dependency):] + [dependency]
        if dependency not in state:
            found = cycle_from(dependency)
            if found:
                return found
    path.pop()
    state[stage] = "done"
    return None

print(" -> ".join(cycle_from("receive")))''',
        expected="receive -> validate -> dispatch -> receive",
        cost="DFS takes O(V+E) time and O(V) state. The path lookup is O(V) once a cycle is found; an index map helps when reporting many witnesses.",
        mistakes=["An edge to a completed node is not a back edge.", "Do not publish a partial order as valid after finding a cycle.", "Recursive DFS needs a depth policy for untrusted input."],
        related=["python/topological-sort", "python/strongly-connected-components", "python/component-condensation"],
    ),
    dict(
        slug="interval-capacity-sweep", section="python/dsa-in-python", subject="python-dsa",
        title="Python interval capacity sweep: process ends before starts",
        summary="A sweep over half-open intervals counts simultaneous reservations when end events precede starts at one timestamp.",
        explanation="One loading-dock reservation ends at the instant another begins; [start, end) semantics say they do not overlap. Encode starts as +1 and ends as -1. Sorting the pair (time, change) processes -1 before +1 on a tie. [[python/interval-conflict-exercise|Pairwise overlap checks]] answer whether two bookings conflict; this sweep finds the peak across all bookings.",
        boundary="Reject an interval whose end is not greater than its start. Normalize time zones before sorting real timestamps; [[python/datetime-boundaries|datetime rules]] affect the ordering. A peak count tells how many docks are needed, not which dock each reservation receives.",
        source='''reservations = [(9, 14), (14, 17), (12, 16)]
events = []
for start, end in reservations:
    if end <= start:
        raise ValueError("empty or reversed reservation")
    events.extend(((start, 1), (end, -1)))

active = 0
peak = 0
for _, change in sorted(events):
    active += change
    peak = max(peak, active)
print("peak docks:", peak)''',
        expected="peak docks: 2",
        cost="Sorting 2n events takes O(n log n) time and O(n) storage. Online updates need a different ordered structure.",
        mistakes=["Processing starts first makes adjacent half-open intervals look overlapping.", "Reject zero-length or reversed intervals unless the domain defines them.", "A peak count is not a resource assignment."],
        related=["python/interval-conflict-exercise", "python/datetime-boundaries", "python/monotonic-window-maximum"],
    ),
    dict(
        slug="frozen-dataclass-shallow-state", section="python/advanced-python", subject="python-advanced",
        title="Python frozen dataclass: field rebinding stops, nested mutation remains",
        summary="frozen=True blocks field assignment but does not recursively freeze objects stored in those fields.",
        explanation="A dispatch plan stores route IDs in a list. The frozen dataclass refuses a new list assignment, yet a caller can append to the existing list. If plans must be stable snapshots, store a tuple built from the input instead. [[python/dataclass-replace-alias|Dataclass replacement]] also reuses referenced objects unless the copy policy says otherwise.",
        boundary="A frozen dataclass containing a list is not a safe dictionary key: hashing still reaches an unhashable mutable field. Do not use unsafe_hash to conceal that state. Create a new validated value object when the business action changes the plan, and avoid retaining a caller-owned mutable list.",
        source='''from dataclasses import FrozenInstanceError, dataclass

@dataclass(frozen=True)
class DispatchPlan:
    route_ids: list[str]

plan = DispatchPlan(["route-47"])
plan.route_ids.append("route-48")
print("routes:", plan.route_ids)
try:
    plan.route_ids = []
except FrozenInstanceError:
    print("field rebinding rejected")''',
        expected="routes: ['route-47', 'route-48']\nfield rebinding rejected",
        cost="Freezing field assignment has a small initialization cost but makes no deep copy. Converting n entries to a tuple costs O(n) time and storage.",
        mistakes=["frozen=True does not mean deep immutability.", "Do not assume a frozen object containing a list is hashable.", "Do not use unsafe_hash to hide mutable key fields."],
        related=["python/dataclasses", "python/dataclass-replace-alias", "python/hash-equality"],
    ),
]

titles = {path: row["title"] for path, row in by_path.items()}
titles.update({"python/" + item["slug"]: item["title"] for item in lessons})
for number, item in enumerate(lessons):
    path = "python/" + item["slug"]
    assert path not in by_path, path
    for target in item["related"]:
        assert target in titles, (path, target)
    body = "<p>" + prose(item["summary"]) + "</p>"
    body += "<h2>Operation contract</h2><p>" + prose(item["explanation"]) + "</p>"
    body += "<h2>Failure and ownership boundary</h2><p>" + prose(item["boundary"]) + "</p>"
    body += '<h2>Working program</h2><pre><code class="language-python">' + html.escape(item["source"], quote=False) + "</code></pre>"
    body += '<h3>Output</h3><pre><code class="language-text">' + html.escape(item["expected"], quote=False) + "</code></pre>"
    body += "<h2>Costs and limits</h2><p>" + prose(item["cost"]) + "</p>"
    body += "<h3>Common Mistakes</h3><ul>" + "".join("<li>" + prose(mistake) + "</li>" for mistake in item["mistakes"]) + "</ul>"
    body += "<h2>Connected lessons</h2><p>" + ", ".join(
        '<a href="/' + target + '">' + html.escape(titles[target]) + "</a>" for target in item["related"]
    ) + ".</p>"
    row = copy.deepcopy(by_path["python/async-task-groups"])
    row.update(id=str(uuid.uuid5(uuid.NAMESPACE_URL, "https://aitrove.in/" + path)),
               path=path, title=item["title"], summary=item["summary"], body=body,
               subject=item["subject"], tags=["python", item["slug"]],
               sort_order=7000 + number, published_at=stamp, created_at=stamp, updated_at=stamp)
    row["data"] = {
        "subject_root": "python/python-programming-language-tutorial",
        "section_path": item["section"], "content_format": "html", "kind": "tutorial",
        "python_version": "3.11+ syntax; verified on local CPython", "python_minimum": "3.11",
        "reading_minutes": max(4, round(len(re.sub(r"<[^>]+>", " ", body).split()) / 150)),
        "author_path": "authors/aitrove-editorial",
        "download_path": "/downloads/aitrove-python-source-kit.zip",
        "related": [{"path": target, "title": titles[target]} for target in item["related"]],
        "seo_ready": True, "expected_output": item["expected"],
    }
    rows.append(row)
    by_path[path] = row

for section, heading in {
    "python/advanced-python": "Concurrency and immutable-state boundaries",
    "python/examples": "SQLite and JSON integrity",
    "python/dsa-in-python": "Heap, graph and interval contracts",
}.items():
    paths = ["python/" + item["slug"] for item in lessons if item["section"] == section]
    hub = by_path[section]
    hub["data"]["modules"].append({
        "title": heading, "summary": "Executable programs, exact output and failure cases.", "lessons": paths,
    })
    hub["body"] += "<h2>" + heading + "</h2><ul>" + "".join(
        '<li><a href="/' + path + '">' + html.escape(titles[path]) + "</a></li>" for path in paths
    ) + "</ul>"
    hub["updated_at"] = stamp

parent = by_path["python/python-programming-language-tutorial"]
parent["body"] += "<h2>Runtime and integrity contracts</h2><ul>" + "".join(
    '<li><a href="/python/' + item["slug"] + '">' + html.escape(item["title"]) + "</a></li>"
    for item in lessons
) + "</ul>"
parent["updated_at"] = stamp
for source, target in [
    ("python/async-task-groups", "python/async-semaphore-admission"),
    ("python/thread-pools", "python/future-cancel-before-start"),
    ("python/async-queues", "python/queue-task-done-ownership"),
    ("python/sqlite-writer-contention", "python/sqlite-busy-write-contract"),
    ("python/sqlite-checkpoint-project", "python/sqlite-wal-snapshot-read"),
    ("python/json-validation", "python/json-nonfinite-number-boundary"),
    ("python/heap-top-k", "python/heap-priority-revision"),
    ("python/topological-sort", "python/topological-cycle-witness"),
    ("python/interval-conflict-exercise", "python/interval-capacity-sweep"),
    ("python/dataclasses", "python/frozen-dataclass-shallow-state"),
]:
    row = by_path[source]
    row["body"] += '<h2>Related boundary</h2><p><a href="/' + target + '">' + html.escape(titles[target]) + "</a></p>"
    row["updated_at"] = stamp

FIXTURE.write_text(json.dumps(rows, ensure_ascii=False, indent=2) + "\n")
print("Added", len(lessons), "Python lessons")
