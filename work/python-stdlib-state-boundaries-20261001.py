"""Publish checked Python state-boundary lessons and internal routes."""

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
        slug="contextvar-token-reset",
        title="Python ContextVar tokens: restore nested request state exactly",
        summary="A ContextVar.set call returns a single-use token that restores the value it replaced in the current context.",
        contract="A receipt handler temporarily changes the request ID twice. Resetting the inner token exposes the outer ID; resetting the outer one restores the unbound default. The program also proves that reusing a token raises an error rather than applying an old value again.",
        boundary="A token belongs to its variable and context. Do not hand it to another task for cleanup. Use try/finally around each temporary set, because an exception between set and reset otherwise leaves the current task with stale request data.",
        source='''from contextvars import ContextVar

request_id = ContextVar("request_id", default="unbound")
outer_token = request_id.set("R-47")
try:
    inner_token = request_id.set("R-48")
    try:
        print("nested", request_id.get())
    finally:
        request_id.reset(inner_token)
    print("outer", request_id.get())
finally:
    request_id.reset(outer_token)

print("restored", request_id.get())
try:
    request_id.reset(outer_token)
except RuntimeError:
    print("second_reset_rejected", True)''',
        expected="nested R-48\nouter R-47\nrestored unbound\nsecond_reset_rejected True",
        cost="Each set records a prior binding in a token. Copying the current context is cheap, but values retained by a long-lived context can keep large request objects alive; store a compact identifier instead.",
        mistakes=["Reset tokens in reverse nesting order.", "A ContextVar value is context-local, not a process-wide request registry.", "A token cannot safely be used twice or reset in another context."],
        related=["python/context-variables", "python/contextvars-task-snapshot", "python/async-to-thread-context"],
    ),
    dict(
        slug="groupby-consecutive-keys",
        title="Python itertools.groupby: contiguous runs are not global groups",
        summary="itertools.groupby starts a new group whenever the key changes in input order.",
        contract="Three receipts arrive for north, south, then north again. Streaming groupby reports three runs. Sorting a copy by region first lets the same operation produce one total per region without changing the original arrival list.",
        boundary="The group iterator shares the underlying input iterator and must be consumed before advancing to the next group. Sorting creates a full materialized copy and loses arrival order; choose a dictionary accumulator when global totals matter more than sorted output.",
        source='''from itertools import groupby

receipts = [("north", 47), ("south", 26), ("north", 11)]

def region_totals(ordered_receipts):
    return [(region, sum(amount for _, amount in run))
            for region, run in groupby(ordered_receipts, key=lambda receipt: receipt[0])]

print("arrival_runs", region_totals(receipts))
sorted_receipts = sorted(receipts, key=lambda receipt: receipt[0])
print("region_totals", region_totals(sorted_receipts))
print("original_order", [region for region, _ in receipts])''',
        expected="arrival_runs [('north', 47), ('south', 26), ('north', 11)]\nregion_totals [('north', 58), ('south', 26)]\noriginal_order ['north', 'south', 'north']",
        cost="Grouping already ordered data scans it once with constant iterator overhead beyond each active run. Sorting an unsorted collection costs O(n log n) time and O(n) storage for the new list.",
        mistakes=["Do not treat separated equal keys as one group.", "Consume each run before requesting the next group.", "Sorting is a semantic choice when arrival order carries meaning."],
        related=["python/itertools-pipelines", "python/defaultdict-grouping", "python/chunked-aggregation"],
    ),
    dict(
        slug="deque-maxlen-eviction",
        title="Python bounded deque: append silently evicts the opposite end",
        summary="A deque with maxlen retains a fixed number of items and discards an item from the opposite end when full.",
        contract="An operations display keeps three recent receipt IDs. Appending a fourth removes the oldest left item. Inserting an older correction at the left then removes the rightmost item; the two directions have different eviction victims.",
        boundary="This structure is a recent-events view, not an audit trail. Eviction is silent and permanent unless another owner stores the record. A bounded deque also rejects indexed insertions that would exceed its limit; it is not a general fixed-capacity queue protocol.",
        source='''from collections import deque

recent_receipts = deque(["R-47", "R-48", "R-49"], maxlen=3)
recent_receipts.append("R-50")
print("after_new", list(recent_receipts))
recent_receipts.appendleft("R-46")
print("after_correction", list(recent_receipts))
print("capacity", recent_receipts.maxlen)''',
        expected="after_new ['R-48', 'R-49', 'R-50']\nafter_correction ['R-46', 'R-48', 'R-49']\ncapacity 3",
        cost="Appending at either end is approximately O(1), and retained references are bounded by maxlen. Looking up a middle index costs linear time, so use a list or dictionary for repeated random access.",
        mistakes=["A bounded deque does not tell the caller which item it dropped.", "appendleft evicts from the right when full.", "Do not use this view as the only copy of financially significant events."],
        related=["python/counter-deque", "python/sliding-window", "python/monotonic-window-maximum"],
    ),
    dict(
        slug="dataclass-initvar-derived-total",
        title="Python dataclass InitVar: validate and derive state without storing input",
        summary="InitVar passes a construction-only value into __post_init__ without making it a dataclass field.",
        contract="A frozen receipt stores its subtotal and derived total. The service percentage is accepted only during construction, validated, then omitted from fields(). Replacing the object requires a fresh percentage because it is not retained for later reconstruction.",
        boundary="This example uses integer cents and an exact percentage result. Real pricing must define how fractional cents are rounded. Frozen dataclasses block ordinary reassignment but do not recursively freeze mutable objects held in fields.",
        source='''from dataclasses import InitVar, dataclass, field, fields, replace

@dataclass(frozen=True)
class ReceiptCharge:
    subtotal_cents: int
    service_percent: InitVar[int]
    total_cents: int = field(init=False)

    def __post_init__(self, service_percent):
        if type(self.subtotal_cents) is not int or self.subtotal_cents < 0:
            raise ValueError("invalid subtotal")
        if type(service_percent) is not int or not 0 <= service_percent <= 20:
            raise ValueError("invalid percentage")
        numerator = self.subtotal_cents * service_percent
        if numerator % 100:
            raise ValueError("fractional cent needs a rounding rule")
        object.__setattr__(self, "total_cents", self.subtotal_cents + numerator // 100)

charge = ReceiptCharge(4700, service_percent=6)
print("total", charge.total_cents)
print("stored_fields", [item.name for item in fields(charge)])
updated = replace(charge, service_percent=8)
print("replaced_total", updated.total_cents)''',
        expected="total 4982\nstored_fields ['subtotal_cents', 'total_cents']\nreplaced_total 5076",
        cost="Generated field access is constant time. __post_init__ validation runs for every construction and replacement; reject unsupported fractional-cent cases before a value enters a ledger.",
        mistakes=["InitVar is not available later as a stored field.", "replace must receive a required InitVar again.", "Frozen fields do not freeze mutable objects reachable through them."],
        related=["python/dataclasses", "python/dataclass-replace-alias", "python/decimal-money"],
    ),
    dict(
        slug="sqlite-row-factory-duplicate-guard",
        title="Python SQLite row factories: reject duplicate output names before mapping",
        summary="A custom sqlite3 row_factory can enforce unique result column names before turning a row into a dictionary.",
        contract="One query returns a receipt ID and amount as separate names. A second uses aliases that differ only by case. The factory rejects that second row rather than letting a dictionary overwrite a value under a normalized key.",
        boundary="This guard operates on the result shape after SQLite executes a query; it is not SQL authorization. It protects a local mapping contract, while the caller still needs parameter binding, query ownership, and explicit connection closure.",
        source='''import sqlite3

def unique_name_row(cursor, values):
    names = [column[0] for column in cursor.description]
    normalized = [name.casefold() for name in names]
    if len(set(normalized)) != len(normalized):
        raise ValueError("duplicate result column")
    return dict(zip(names, values, strict=True))

connection = sqlite3.connect(":memory:")
try:
    connection.row_factory = unique_name_row
    receipt = connection.execute(
        "SELECT 47 AS receipt_id, 26 AS amount_cents").fetchone()
    print("receipt", receipt)
    try:
        connection.execute("SELECT 47 AS total, 26 AS TOTAL").fetchone()
    except ValueError:
        print("duplicate_rejected", True)
finally:
    connection.close()''',
        expected="receipt {'receipt_id': 47, 'amount_cents': 26}\nduplicate_rejected True",
        cost="The factory builds names, a normalized list, a set, and a dictionary for every fetched row. That adds O(c) work and storage for c columns per row; validate a stable query shape once if a high-volume path needs less overhead.",
        mistakes=["Plain dict construction can hide duplicate aliases by overwriting one value.", "Set connection.row_factory before creating cursors that should inherit it.", "A with connection block manages transactions, not connection closure."],
        related=["python/sqlite-row-name-collision", "python/sqlite-transactions", "python/sqlite-authorizer-policy"],
    ),
    dict(
        slug="queue-listener-shutdown",
        title="Python QueueListener: stop the logging worker after queued records drain",
        summary="QueueHandler moves log handling to a listener thread, and the owner must stop that listener before exit.",
        contract="A receipt logger sends two records into an owned SimpleQueue. A recording handler receives them on the listener thread. The owner stops the listener before reading the output, giving the two messages a defined completion point.",
        boundary="SimpleQueue is unbounded. If producers outpace a slow handler, memory can grow without limit. A bounded queue needs an explicit policy for put failures and enough room for the stop sentinel; the example does not implement that service-level policy.",
        source='''import logging
from logging.handlers import QueueHandler, QueueListener
from queue import SimpleQueue

class ReceiptCollector(logging.Handler):
    def __init__(self):
        super().__init__()
        self.records = []

    def emit(self, record):
        self.records.append(record.getMessage())

receipt_queue = SimpleQueue()
collector = ReceiptCollector()
queue_handler = QueueHandler(receipt_queue)
logger = logging.getLogger("aitrove.receipt.queue.contract")
logger.setLevel(logging.INFO)
logger.propagate = False
logger.addHandler(queue_handler)
listener = QueueListener(receipt_queue, collector)
listener.start()
try:
    logger.info("receipt %s accepted", "R-47")
    logger.info("receipt %s exported", "R-48")
finally:
    listener.stop()
    logger.removeHandler(queue_handler)
    queue_handler.close()
    collector.close()

print("delivered", collector.records)''',
        expected="delivered ['receipt R-47 accepted', 'receipt R-48 exported']",
        cost="Enqueueing reduces producer time spent in slow handlers, but adds a worker thread, queue memory, and shutdown work. The listener still processes one handler call at a time in this fixture.",
        mistakes=["Stopping the process without listener.stop can leave records unhandled.", "An unbounded queue is not a backpressure strategy.", "Keep a handler that writes to a shared sink thread-safe or give it one clear owner."],
        related=["python/logging-context", "python/log-redaction", "python/queue-task-done-ownership"],
    ),
    dict(
        slug="thread-barrier-abort",
        title="Python threading.Barrier: abort a failed phase so peers do not wait forever",
        summary="Barrier.abort marks a rendezvous as broken and releases current and future waiters with BrokenBarrierError.",
        contract="A worker announces that it is entering a phase gate. The owner aborts the gate to represent a failed peer. Whether the worker reached wait just before or after abort, it receives the same broken-barrier outcome; a later wait also fails.",
        boundary="A barrier coordinates a known number of threads; it does not cancel their underlying work. Resetting while peer state is uncertain can mix phases. This program creates one barrier, aborts it once, and joins its owned worker.",
        source='''from threading import Barrier, BrokenBarrierError, Event, Thread

phase_gate = Barrier(2)
worker_entered = Event()
worker_outcomes = []

def await_receipt_phase():
    worker_entered.set()
    try:
        phase_gate.wait(timeout=2)
    except BrokenBarrierError:
        worker_outcomes.append("released")

worker = Thread(target=await_receipt_phase)
worker.start()
if not worker_entered.wait(timeout=2):
    raise TimeoutError("worker did not start")
phase_gate.abort()
worker.join(timeout=2)
if worker.is_alive():
    raise TimeoutError("worker did not stop")
print("worker", worker_outcomes)
try:
    phase_gate.wait(timeout=2)
except BrokenBarrierError:
    print("later_wait_rejected", True)
print("broken", phase_gate.broken)''',
        expected="worker ['released']\nlater_wait_rejected True\nbroken True",
        cost="A barrier maintains shared phase state and blocks each arrival until all parties appear or the phase breaks. Timeouts and abort paths need explicit owners, or a missing worker can strand the rest.",
        mistakes=["An Event does not replace a barrier when every peer must reach a phase.", "Aborting a barrier does not stop work outside wait().", "Do not reset a broken barrier while peer phases are unknown."],
        related=["python/thread-locks", "python/condition-predicates", "python/queue-graceful-shutdown"],
    ),
    dict(
        slug="decimal-localcontext-rounding",
        title="Python decimal localcontext: keep a rounding rule inside one calculation",
        summary="decimal.localcontext creates a temporary arithmetic policy and restores the prior context on exit.",
        contract="A receipt amount with three decimal places is quantized to cents under ROUND_HALF_UP. The local context records that information was discarded. After the with block, the calling context still has its original rounding policy.",
        boundary="Rounding mode and where rounding occurs are business rules. This fixture does not claim ROUND_HALF_UP is appropriate for every currency or jurisdiction. Construct Decimal from text when exact decimal input matters; binary floats can carry prior approximation.",
        source='''from decimal import Decimal, Inexact, ROUND_HALF_UP, getcontext, localcontext

prior_rounding = getcontext().rounding
with localcontext(rounding=ROUND_HALF_UP) as receipt_policy:
    rounded = Decimal("47.245").quantize(Decimal("0.01"))
    was_inexact = receipt_policy.flags[Inexact]

print("rounded", rounded)
print("inexact", was_inexact)
print("rounding_restored", getcontext().rounding == prior_rounding)''',
        expected="rounded 47.25\ninexact True\nrounding_restored True",
        cost="Decimal arithmetic has more overhead than integer-cent arithmetic. Context flags are sticky within a context, so clear or use a fresh local context when each operation needs an independent signal.",
        mistakes=["Do not change a shared arithmetic policy for one receipt and forget to restore it.", "Inexact is a status flag unless its trap is enabled.", "A Decimal made from a float can preserve the float's approximation."],
        related=["python/decimal-money", "python/decimal-inexact-trap", "python/locale-independent-money-input"],
    ),
    dict(
        slug="bisect-key-search-contract",
        title="Python bisect key: search with a key value, insert with a record",
        summary="bisect_left applies key to stored elements, while the search value is already the comparable key.",
        contract="A due-date index stores receipt records ordered by day. The search passes day 47, rather than an entire record, to bisect_left. insort_left then receives a full new record and places it at the correct day.",
        boundary="Bisection assumes the list remains sorted under the same key. Mutating a stored record's day breaks later searches. Concurrent writers also need synchronization around search and insertion; the functions do not make a shared list transactional.",
        source='''from bisect import bisect_left, insort_left

receipts = [
    {"due_day": 12, "receipt": "R-12"},
    {"due_day": 47, "receipt": "R-47"},
    {"due_day": 73, "receipt": "R-73"},
]
due_day = lambda receipt: receipt["due_day"]
print("found_at", bisect_left(receipts, 47, key=due_day))
insort_left(receipts, {"due_day": 26, "receipt": "R-26"}, key=due_day)
print("ordered_days", [receipt["due_day"] for receipt in receipts])''',
        expected="found_at 1\nordered_days [12, 26, 47, 73]",
        cost="The search uses O(log n) comparisons, but insertion shifts list entries and costs O(n). Computing an expensive key repeatedly can dominate comparisons; keep precomputed keys when queries are frequent.",
        mistakes=["For bisect_left with key, pass the search key as x, not a full record.", "Do not mutate an indexed sort field in place.", "A log-time search does not make list insertion log-time."],
        related=["python/bisect-insertion", "python/sorting", "python/capacity-binary-search"],
    ),
    dict(
        slug="lru-cache-mutable-result",
        title="Python lru_cache: callers share the same cached mutable result",
        summary="lru_cache stores a function's returned object and returns that same object on a cache hit.",
        contract="A cached list of receipt IDs is changed by its first caller. The second caller sees the added ID even though the loader never returned it. A separate cached tuple resists this form of mutation and gives repeatable reads.",
        boundary="The list function is deliberately unsafe to expose the alias. A tuple is only shallowly immutable; nested mutable elements can still change. Cache entries also stay resident until eviction or cache_clear, so large return graphs need a memory budget.",
        source='''from functools import lru_cache

@lru_cache(maxsize=8)
def mutable_receipt_codes(region):
    return ["R-47"]

@lru_cache(maxsize=8)
def receipt_codes(region):
    return ("R-47",)

first_caller = mutable_receipt_codes("west")
first_caller.append("R-48")
print("shared_list", mutable_receipt_codes("west"))
print("stable_tuple", receipt_codes("west"))
print("same_cached_object", first_caller is mutable_receipt_codes("west"))''',
        expected="shared_list ['R-47', 'R-48']\nstable_tuple ('R-47',)\nsame_cached_object True",
        cost="A hit avoids recomputation, but the cache holds strong references to arguments and results up to maxsize. The wrapper is threadsafe as a data structure; simultaneous misses can still compute the same key more than once.",
        mistakes=["Do not return a mutable cached collection directly to untrusted callers.", "A tuple containing a list is still mutable through that inner list.", "Caching is not an exactly-once execution guarantee for concurrent misses."],
        related=["python/functools-cache", "python/copy-deepcopy", "python/ttl-cache-project"],
    ),
]

new_paths = ["python/" + item["slug"] for item in lessons]
assert not any(path in by_path for path in new_paths)
titles = {row["path"]: row["title"] for row in rows}
titles.update({path: item["title"] for path, item in zip(new_paths, lessons)})
for order, (item, path) in enumerate(zip(lessons, new_paths)):
    assert all(target in titles for target in item["related"]), path
    body = "<p>" + html.escape(item["summary"]) + "</p>"
    body += "<h2>Observed contract</h2><p>" + html.escape(item["contract"]) + "</p>"
    body += "<h2>Boundary</h2><p>" + html.escape(item["boundary"]) + "</p>"
    body += '<h2>Executable case</h2><pre><code class="language-python">' + html.escape(item["source"], quote=False) + "</code></pre>"
    body += '<h3>Output</h3><pre><code class="language-text">' + html.escape(item["expected"], quote=False) + "</code></pre>"
    body += "<h2>Cost</h2><p>" + html.escape(item["cost"]) + "</p>"
    body += "<h3>Common Mistakes</h3><ul>" + "".join("<li>" + html.escape(mistake) + "</li>" for mistake in item["mistakes"]) + "</ul>"
    body += "<h2>Connected lessons</h2><ul>" + "".join(
        '<li><a href="/' + target + '">' + html.escape(titles[target]) + "</a></li>"
        for target in item["related"]) + "</ul>"
    row = copy.deepcopy(by_path["python/async-task-groups"])
    row.update(id=str(uuid.uuid5(uuid.NAMESPACE_URL, "https://aitrove.in/" + path)),
               path=path, title=item["title"], summary=item["summary"], body=body,
               subject="python-advanced", tags=["python", item["slug"]],
               sort_order=9200 + order, published_at=stamp, created_at=stamp, updated_at=stamp)
    row["data"] = {"subject_root": "python/python-programming-language-tutorial",
                   "section_path": "python/advanced-python", "content_format": "html", "kind": "tutorial",
                   "python_version": "3.11+ syntax; verified on local CPython",
                   "python_minimum": "3.11", "reading_minutes": 5,
                   "author_path": "authors/aitrove-editorial",
                   "download_path": "/downloads/aitrove-python-source-kit.zip",
                   "related": [{"path": target, "title": titles[target]} for target in item["related"]],
                   "seo_ready": True, "expected_output": item["expected"]}
    rows.append(row)
    by_path[path] = row

advanced = by_path["python/advanced-python"]
advanced["data"]["modules"].append({"title": "Standard-library state and ownership contracts",
                                    "summary": "Local programs for cached values, row shapes, queue shutdown, and scoped state.",
                                    "lessons": new_paths})
advanced["body"] += "<h2>Standard-library state and ownership contracts</h2><ul>" + "".join(
    '<li><a href="/' + path + '">' + html.escape(titles[path]) + "</a></li>"
    for path in new_paths) + "</ul>"
advanced["updated_at"] = stamp
parent = by_path["python/python-programming-language-tutorial"]
parent["body"] += "<h2>Standard-library state and ownership contracts</h2><ul>" + "".join(
    '<li><a href="/' + path + '">' + html.escape(titles[path]) + "</a></li>"
    for path in new_paths) + "</ul>"
parent["updated_at"] = stamp

for source, target in [
    ("python/context-variables", "python/contextvar-token-reset"),
    ("python/itertools-pipelines", "python/groupby-consecutive-keys"),
    ("python/counter-deque", "python/deque-maxlen-eviction"),
    ("python/dataclasses", "python/dataclass-initvar-derived-total"),
    ("python/sqlite-row-name-collision", "python/sqlite-row-factory-duplicate-guard"),
    ("python/logging-context", "python/queue-listener-shutdown"),
    ("python/thread-locks", "python/thread-barrier-abort"),
    ("python/decimal-money", "python/decimal-localcontext-rounding"),
    ("python/bisect-insertion", "python/bisect-key-search-contract"),
    ("python/functools-cache", "python/lru-cache-mutable-result"),
]:
    row = by_path[source]
    row["body"] += '<p><a href="/' + target + '">Continue with ' + html.escape(titles[target]) + "</a>.</p>"
    row["updated_at"] = stamp

quiz_path = "quizzes/python-stdlib-state-contracts"
assert quiz_path not in by_path
quiz = copy.deepcopy(by_path["quizzes/python-boundary-contracts"])
quiz_body = "<p>Check ten standard-library contracts around scoped state, grouping, mutation, and shutdown.</p><h2>Review the cases</h2><ul>"
quiz_body += "".join('<li><a href="/' + path + '">' + html.escape(titles[path]) + "</a></li>" for path in new_paths)
quiz_body += "</ul><h3>Common Mistakes</h3><p>Passing a local contract does not test a concurrent production workload.</p>"
quiz.update(id=str(uuid.uuid5(uuid.NAMESPACE_URL, "https://aitrove.in/" + quiz_path)),
            path=quiz_path, title="Python standard-library state contracts quiz",
            summary="Twelve explained questions on state restoration, grouping, caches, SQLite rows, and threads.",
            body=quiz_body, sort_order=9200, published_at=stamp, created_at=stamp, updated_at=stamp)
raw_questions = [
    ("What does a ContextVar token restore?", "The binding replaced by its set call", "The process-global default only", "Every task's binding", "A token records the prior value in its own context."),
    ("Can the same ContextVar token be reset twice?", "No", "Yes", "Only if the value is immutable", "A token is single-use."),
    ("What does groupby do when a key appears, changes, then appears again?", "Creates a later separate run", "Combines both runs", "Raises ValueError", "Groups are consecutive runs in input order."),
    ("Which item does appendleft evict from a full bounded deque?", "The rightmost item", "The new item", "The leftmost item", "A full deque discards from the opposite end."),
    ("Is an InitVar returned by dataclasses.fields?", "No", "Yes", "Only for frozen classes", "It is a construction-only pseudo-field."),
    ("What can happen when duplicate SQL aliases become dictionary keys?", "A value may be overwritten", "SQLite always rejects them", "The row gains two identical keys", "A mapping needs an explicit duplicate-name rule."),
    ("Why stop a QueueListener before reading the final output?", "The worker must finish queued handling", "It changes log severity", "It closes every logger", "stop joins the listener after its sentinel is processed."),
    ("What does Barrier.abort do to later wait calls?", "They raise BrokenBarrierError", "They pass immediately", "They create a new barrier", "An aborted barrier stays broken until explicitly reset."),
    ("What happens after exiting decimal.localcontext?", "The earlier context is restored", "The local rounding rule stays global", "Every Decimal is converted to float", "The context manager scopes arithmetic settings."),
    ("With bisect_left(key=...), what is passed as x?", "A comparable key value", "A mandatory full record", "A key function", "The key function is applied to stored elements during search."),
    ("What does lru_cache return for a cached mutable list?", "The same list object", "A deep copy", "A read-only proxy", "A cache hit returns the retained result object."),
    ("Does lru_cache guarantee one calculation for simultaneous misses?", "No", "Yes", "Only with maxsize eight", "Concurrent callers can compute the same missing key before one result is stored."),
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
assert needle in quiz_hub["body"]
quiz_hub["body"] = quiz_hub["body"].replace(needle,
    '<li><a href="/' + quiz_path + '">' + html.escape(quiz["title"]) + "</a></li>" + needle)
parent["body"] += '<p><a href="/' + quiz_path + '">Check the standard-library state quiz</a>.</p>'
for path in new_paths:
    by_path[path]["body"] += '<p><a href="/' + quiz_path + '">Test this contract</a>.</p>'

fixture.write_text(json.dumps(rows, ensure_ascii=False, indent=2) + "\n")
print("Added", len(lessons), "lessons and one quiz")
