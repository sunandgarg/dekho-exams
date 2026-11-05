"""Add original, runnable lessons for Python 3.13 and 3.14 library contracts."""

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
    dict(
        slug="queue-graceful-shutdown", section="python/advanced-python", subject="python-advanced", minimum="3.13",
        title="Python Queue.shutdown: drain accepted work before workers exit",
        summary="Queue.shutdown rejects new work while allowing already queued jobs to finish when immediate is false.",
        contract="The intake accepts two receipt IDs, then closes. A worker drains both, acknowledges each with task_done, and exits on ShutDown only after the queue empties. A later producer also receives ShutDown. The join call checks that accepted jobs were acknowledged, not merely dequeued.",
        boundary="An immediate shutdown can release join without processing every queued item; do not use it as a success signal. Queue.empty and qsize are snapshots, not admission checks. A worker exception before task_done can leave join waiting forever unless the owner records failure and resolves the unfinished count.",
        source='''from queue import Queue, ShutDown
from threading import Thread

receipts = Queue(maxsize=3)
processed = []

def write_receipts():
    while True:
        try:
            receipt_id = receipts.get()
        except ShutDown:
            return
        try:
            processed.append(receipt_id)
        finally:
            receipts.task_done()

worker = Thread(target=write_receipts)
worker.start()
for receipt_id in ("north-47", "north-48"):
    receipts.put(receipt_id)
receipts.shutdown()
receipts.join()
worker.join()
try:
    receipts.put("north-49")
except ShutDown:
    print("late_rejected", True)
print("processed", sorted(processed))''',
        expected="late_rejected True\nprocessed ['north-47', 'north-48']",
        cost="Accepted work and acknowledgements cost O(n). A bounded queue caps pending references at its capacity; the example also retains processed IDs for inspection.",
        mistakes=["Do not confuse immediate shutdown with completed work.", "Call task_done once for each successful get, even on a processing failure path.", "Do not use qsize to decide whether a put will block."],
        related=["python/queue-task-done-ownership", "python/thread-pools", "python/async-queues"],
    ),
    dict(
        slug="itertools-batched-strict", section="python/advanced-python", subject="python-advanced", minimum="3.13",
        title="Python batched strict: reject an incomplete import group",
        summary="itertools.batched consumes a stream lazily; strict mode fails when its last tuple is short.",
        contract="A settlement import expects groups of three IDs. The first input has six IDs and produces two complete groups. A second input has seven; two groups can be yielded before iteration raises ValueError on the final lone ID. Validate the entire stream before committing irreversible group effects.",
        boundary="Strict batching is not an atomic transaction. Previously yielded groups may already have been written when the final error appears. If all-or-nothing import is required, stage data in a transaction or temporary store first. The iterator also has no built-in total input limit.",
        source='''from itertools import batched

accepted_ids = (f"receipt-{number}" for number in range(47, 53))
groups = list(batched(accepted_ids, 3, strict=True))
print("groups", len(groups))
print("first", groups[0])

incomplete_ids = (f"receipt-{number}" for number in range(47, 54))
complete_before_error = 0
try:
    for settlement_group in batched(incomplete_ids, 3, strict=True):
        complete_before_error += 1
except ValueError:
    print("complete_before_error", complete_before_error)''',
        expected="groups 2\nfirst ('receipt-47', 'receipt-48', 'receipt-49')\ncomplete_before_error 2",
        cost="Iteration takes O(n) time and retains up to three items per current batch. Materializing all groups with list, as in the first check, takes O(n) additional space.",
        mistakes=["A late strict error does not undo earlier side effects.", "Strict mode checks final tuple length, not business validity of each item.", "An infinite input never reaches a final-batch check."],
        related=["python/iterator-protocol", "python/generators", "python/csv-import"],
    ),
    dict(
        slug="copy-replace-protocol", section="python/advanced-python", subject="python-advanced", minimum="3.13",
        title="Python copy.replace: revise one field without cloning owned data",
        summary="copy.replace constructs a new supported record with selected fields changed, retaining other field references.",
        contract="A frozen invoice record is revised from pending to approved. The new record is separate, while its tuple of line IDs remains the same object. That sharing is safe here because the tuple is immutable. The generic replace function works with dataclasses and other types that expose the replacement protocol.",
        boundary="Replacement is shallow. If a record contains a mutable list or dictionary, old and new records can still observe changes to that nested object. Frozen dataclasses prevent assigning their fields, not mutation inside referenced objects. Validate business transitions separately; replace does not enforce an approval workflow.",
        source='''from copy import replace
from dataclasses import dataclass

@dataclass(frozen=True)
class InvoiceRevision:
    invoice_id: str
    status: str
    line_ids: tuple[str, ...]

pending = InvoiceRevision("inv-47", "pending", ("line-47", "line-48"))
approved = replace(pending, status="approved")
print("old", pending.status)
print("new", approved.status)
print("shared_immutable_lines", pending.line_ids is approved.line_ids)''',
        expected="old pending\nnew approved\nshared_immutable_lines True",
        cost="A new outer record is allocated. Unchanged nested values are referenced rather than recursively copied, avoiding a full graph traversal.",
        mistakes=["A frozen outer record can still refer to mutable nested data.", "replace does not accept every arbitrary class; it needs a supported replacement protocol.", "Field replacement does not certify a valid business state transition."],
        related=["python/dataclasses", "python/copy-deepcopy", "python/typing-reference"],
    ),
    dict(
        slug="uuid7-ordered-identifiers", section="python/examples", subject="python-examples", minimum="3.14",
        title="Python UUIDv7: time-ordered IDs without treating them as a clock",
        summary="uuid.uuid7 creates identifiers with a millisecond timestamp component and local ordering support.",
        contract="Two new order IDs are generated and decoded. Both have version seven, distinct bytes, and nondecreasing embedded millisecond times in this process. The program prints properties rather than the IDs themselves because the values depend on the run.",
        boundary="An ID is not an authorization token or proof that an order existed at the embedded time. Clocks can shift, distinct hosts have no single strict issue order, and an attacker can construct a UUID with chosen bits. Store a trusted creation timestamp separately when audit or cross-host ordering matters.",
        source='''import uuid

first_order_id = uuid.uuid7()
second_order_id = uuid.uuid7()
print("versions", first_order_id.version, second_order_id.version)
print("distinct", first_order_id != second_order_id)
print("time_non_decreasing", first_order_id.time <= second_order_id.time)''',
        expected="versions 7 7\ndistinct True\ntime_non_decreasing True",
        cost="Generation uses a fixed-size identifier and constant-size metadata. Sorting many IDs still costs O(n log n), and a timestamp component does not eliminate an indexed database access path.",
        mistakes=["Do not make access decisions from an ID's timestamp bits.", "Do not claim a global strict order across independent hosts.", "Do not equate a generated ID with a durable database commit."],
        related=["python/runtime-compatibility", "python/sqlite-transactions", "python/datetime-boundaries"],
    ),
    dict(
        slug="deferred-annotations-inspection", section="python/advanced-python", subject="python-advanced", minimum="3.14",
        title="Python deferred annotations: inspect forward names without resolving them",
        summary="annotationlib can inspect a forward annotation as text even when the referenced class is unavailable.",
        contract="A repository method names a future Receipt class that is not defined in the fixture. Its function definition succeeds. STRING inspection returns the written type name without requiring the class to exist; VALUE inspection raises NameError. A framework should choose the format that matches its job instead of assuming annotation access is inert.",
        boundary="Even STRING inspection may execute annotation-related code in some expressions. Treat third-party annotations as executable input, not a safe serialization format. Runtime type checking is a separate concern. Behavior also differs for code using the older future-annotations mode, so test the project's supported Python versions.",
        source='''from annotationlib import Format, get_annotations

def load_receipt(receipt_id: str) -> FutureReceipt:
    raise NotImplementedError

written = get_annotations(load_receipt, format=Format.STRING)
print("return_name", written["return"])
try:
    get_annotations(load_receipt, format=Format.VALUE)
except NameError:
    print("value_unresolved", True)''',
        expected="return_name FutureReceipt\nvalue_unresolved True",
        cost="Deferred evaluation shifts work from function definition to the reader that inspects annotations. Repeated inspection may execute user code and should not sit on an unbounded hot path.",
        mistakes=["An annotation is not runtime input validation.", "VALUE format can fail when a forward name remains undefined.", "Do not treat annotation introspection as safe for untrusted plugin code."],
        related=["python/typing-reference", "python/runtime-compatibility", "python/dataclasses"],
    ),
    dict(
        slug="zstd-decompression-budget", section="python/examples", subject="python-examples", minimum="3.14",
        title="Python Zstandard decompression: stop at an output budget",
        summary="A compressed frame can expand far beyond its input size; bound decoded bytes while consuming it.",
        contract="A fixed 47,000-byte receipt payload is compressed locally. The incremental decompressor is asked for at most 4,097 bytes, one past a 4,096-byte intake budget. It reports that the frame is over budget without allocating the complete decoded payload through the one-shot decompress function.",
        boundary="This program supplies the full compressed frame in memory, so production intake still needs compressed-byte and time limits. If the output is within budget, finish decoding and require end-of-frame, then decide how trailing data or multiple frames are handled. The one-shot function can allocate the full decoded result and is unsuitable as the budget check.",
        source='''from compression import zstd

receipt_payload = b"R" * 47000
frame = zstd.compress(receipt_payload)
decoder = zstd.ZstdDecompressor()
prefix = decoder.decompress(frame, max_length=4097)
print("over_budget", len(prefix) > 4096)
print("complete_frame", decoder.eof)''',
        expected="over_budget True\ncomplete_frame False",
        cost="The decision retains O(limit) decoded bytes here, plus the compressed frame and decoder state. Decompression CPU and memory still need limits for hostile inputs.",
        mistakes=["Compressed size does not cap decoded size.", "A partial decode is not a successful integrity check of the full frame.", "Bound compressed input, decoded output, and elapsed time separately."],
        related=["python/gzip-output-budget", "python/zip-member-validation", "python/tar-extraction-byte-quota"],
    ),
    dict(
        slug="executor-map-buffer", section="python/advanced-python", subject="python-advanced", minimum="3.14",
        title="Python Executor.map buffersize: pause submission when results wait",
        summary="The buffersize argument limits submitted map work whose results have not yet been yielded.",
        contract="An input generator counts how many receipt IDs have been pulled. With buffersize two, creating the map iterator consumes the first two IDs; consuming results allows later IDs to be pulled. Workers return deterministic labels so scheduling order does not affect displayed output.",
        boundary="A bounded submission buffer is not a timeout, output-size quota, or cancellation policy. A slow early result can hold ordered map iteration while later work completes. Thread workers share a process, so this pattern does not isolate untrusted code or speed up CPU-heavy Python code on a conventional GIL build.",
        source='''from concurrent.futures import ThreadPoolExecutor

submitted = []

def receipt_ids():
    for number in range(47, 53):
        submitted.append(number)
        yield number

def normalize_receipt(number):
    return f"receipt-{number}"

with ThreadPoolExecutor(max_workers=2) as pool:
    results = pool.map(normalize_receipt, receipt_ids(), buffersize=2)
    print("pulled_before_next", len(submitted))
    print("first", next(results))
    print("all", len([*results]) + 1)''',
        expected="pulled_before_next 2\nfirst receipt-47\nall 6",
        cost="At most the configured number of submitted, unyielded map items is buffered by this API; the example's submitted list intentionally retains all IDs for observation. Result collection has O(n) space here.",
        mistakes=["buffersize does not bound task runtime.", "Ordered results can wait behind a slow first task.", "Do not equate a thread pool with process isolation."],
        related=["python/thread-pools", "python/iterator-protocol", "python/queue-graceful-shutdown"],
    ),
    dict(
        slug="heapq-native-maxheap", section="python/advanced-python", subject="python-advanced", minimum="3.14",
        title="Python heapq max-heap: keep highest-priority scores at the root",
        summary="The max-heap functions avoid sign inversion when numeric priority itself is the ordering key.",
        contract="Four inspection scores are heapified and consumed from highest to lowest. The heap is a list, but its internal list order is not a sorted report; only repeated heappop_max calls establish descending output. The score represents urgency, not an object with tie-breaking metadata.",
        boundary="If work items carry payloads, define an explicit tie-break rule so equal priorities do not compare incompatible objects. Changing an item's priority in place breaks the heap invariant. A heap gives fast access to one extreme, not constant-time arbitrary deletion or a fully sorted index.",
        source='''from heapq import heapify_max, heappop_max, heappush_max

inspection_scores = [47, 82, 65]
heapify_max(inspection_scores)
heappush_max(inspection_scores, 91)
descending = []
while inspection_scores:
    descending.append(heappop_max(inspection_scores))
print("priority_order", descending)''',
        expected="priority_order [91, 82, 65, 47]",
        cost="Heap construction is O(n), each push or pop is O(log n), and popping all items is O(n log n). The heap stores O(n) values.",
        mistakes=["The backing list is not a sorted sequence.", "Do not mutate a queued priority without restoring the heap invariant.", "Tie-breaking must be defined before storing payload records."],
        related=["python/heap-top-k", "python/heap-priority-revision", "python/running-median-heaps"],
    ),
]

titles = {path: row["title"] for path, row in by_path.items()}
titles.update({"python/" + item["slug"]: item["title"] for item in lessons})
for order, item in enumerate(lessons):
    path = "python/" + item["slug"]
    assert path not in by_path, path
    for target in item["related"]:
        assert target in titles, (path, target)
    body = "<p>" + html.escape(item["summary"]) + "</p>"
    body += "<h2>Operation contract</h2><p>" + html.escape(item["contract"]) + "</p>"
    body += "<h2>Failure boundary</h2><p>" + html.escape(item["boundary"]) + "</p>"
    body += '<h2>Working program</h2><pre><code class="language-python">' + html.escape(item["source"], quote=False) + "</code></pre>"
    body += '<h3>Output</h3><pre><code class="language-text">' + html.escape(item["expected"], quote=False) + "</code></pre>"
    body += "<h2>Costs and limits</h2><p>" + html.escape(item["cost"]) + "</p>"
    body += "<h3>Common Mistakes</h3><ul>" + "".join("<li>" + html.escape(mistake) + "</li>" for mistake in item["mistakes"]) + "</ul>"
    body += "<h2>Connected lessons</h2><ul>" + "".join(
        '<li><a href="/' + target + '">' + html.escape(titles[target]) + "</a></li>" for target in item["related"]
    ) + "</ul>"
    row = copy.deepcopy(by_path["python/async-task-groups"])
    row.update(id=str(uuid.uuid5(uuid.NAMESPACE_URL, "https://aitrove.in/" + path)),
               path=path, title=item["title"], summary=item["summary"], body=body,
               subject=item["subject"], tags=["python", item["slug"]],
               sort_order=8000 + order, published_at=stamp, created_at=stamp, updated_at=stamp)
    row["data"] = {"subject_root": "python/python-programming-language-tutorial",
                   "section_path": item["section"], "content_format": "html", "kind": "tutorial",
                   "python_version": f"{item['minimum']}+; verified on local CPython",
                   "python_minimum": item["minimum"], "reading_minutes": 5,
                   "author_path": "authors/aitrove-editorial",
                   "download_path": "/downloads/aitrove-python-source-kit.zip",
                   "related": [{"path": target, "title": titles[target]} for target in item["related"]],
                   "seo_ready": True, "expected_output": item["expected"]}
    rows.append(row)
    by_path[path] = row

for section in sorted({item["section"] for item in lessons}):
    paths = ["python/" + item["slug"] for item in lessons if item["section"] == section]
    hub = by_path[section]
    hub["data"]["modules"].append({"title": "Python 3.13 and 3.14 contracts",
                                   "summary": "Versioned library behavior with runnable output and failure limits.",
                                   "lessons": paths})
    hub["body"] += "<h2>Python 3.13 and 3.14 contracts</h2><ul>" + "".join(
        '<li><a href="/' + path + '">' + html.escape(titles[path]) + "</a></li>" for path in paths
    ) + "</ul>"
    hub["updated_at"] = stamp

parent = by_path["python/python-programming-language-tutorial"]
parent["body"] += "<h2>Python 3.13 and 3.14 library contracts</h2><ul>" + "".join(
    '<li><a href="/python/' + item["slug"] + '">' + html.escape(item["title"]) + "</a></li>"
    for item in lessons) + "</ul>"
parent["updated_at"] = stamp
for source, target in [
    ("python/queue-task-done-ownership", "python/queue-graceful-shutdown"),
    ("python/iterator-reference", "python/itertools-batched-strict"),
    ("python/copy-deepcopy", "python/copy-replace-protocol"),
    ("python/runtime-compatibility", "python/uuid7-ordered-identifiers"),
    ("python/typing-reference", "python/deferred-annotations-inspection"),
    ("python/gzip-output-budget", "python/zstd-decompression-budget"),
    ("python/thread-pools", "python/executor-map-buffer"),
    ("python/heap-top-k", "python/heapq-native-maxheap"),
]:
    row = by_path[source]
    row["body"] += '<p><a href="/' + target + '">Continue with ' + html.escape(titles[target]) + "</a>.</p>"
    row["updated_at"] = stamp

quiz_path = "quizzes/python-modern-runtime-contracts"
assert quiz_path not in by_path
quiz = copy.deepcopy(by_path["quizzes/python-boundary-contracts"])
targets = ["python/" + item["slug"] for item in lessons]
quiz_body = "<p>Check the versioned standard-library contracts before depending on them in an application.</p><h2>Review the related lessons</h2><ul>"
quiz_body += "".join('<li><a href="/' + path + '">' + html.escape(titles[path]) + "</a></li>" for path in targets)
quiz_body += "</ul><h3>Common Mistakes</h3><p>A correct answer does not replace version, load, or failure testing in the target runtime.</p>"
quiz.update(id=str(uuid.uuid5(uuid.NAMESPACE_URL, "https://aitrove.in/" + quiz_path)),
            path=quiz_path, title="Python 3.13 and 3.14 runtime contracts quiz",
            summary="Twelve explained questions on queue drain, batching, records, IDs, annotations and resource limits.",
            body=quiz_body, sort_order=8100, published_at=stamp, created_at=stamp, updated_at=stamp)
raw_questions = [
    ("What does Queue.shutdown(immediate=False) allow?", "Draining already accepted work", "Adding new work after shutdown", "Treating unfinished work as done", "A graceful shutdown stops new puts while consumers may finish queued jobs."),
    ("Why can Queue.shutdown(immediate=True) mislead a join caller?", "Join may unblock before queued work is processed", "It sorts the remaining work", "It copies every task to another queue", "Immediate shutdown can break the usual completed-work meaning of join."),
    ("When does batched(..., strict=True) reject an incomplete group?", "When iteration reaches the short final group", "Before the first batch is yielded", "At import time", "The iterator consumes input lazily, so earlier complete groups may have escaped."),
    ("What does copy.replace preserve for an unchanged nested value?", "The existing reference", "A guaranteed deep clone", "A frozen copy of any list", "Replacement constructs a new outer object but does not recursively copy every field."),
    ("What does a UUIDv7 timestamp fail to prove?", "That a database row was committed at that instant", "That the ID has version seven", "That an embedded time field exists", "An ID can be generated or constructed without a successful business commit."),
    ("Which annotation format can return a missing forward name as text?", "Format.STRING", "Format.VALUE", "A database cursor", "String inspection can represent the written name without resolving it to a class."),
    ("Is inspecting arbitrary annotations always side-effect free?", "No, annotation-related code may execute", "Yes, every format only reads bytes", "Only if the function returns None", "Do not evaluate annotations from untrusted plugin code as harmless metadata."),
    ("Why use max_length when incrementally decoding Zstandard?", "To cap returned decoded bytes per call", "To authenticate the frame", "To cap compressed input automatically", "A compressed frame can expand well past an intake budget."),
    ("What does a partial Zstandard decode fail to confirm?", "That the complete frame is valid", "That some prefix was produced", "That the decoder has state", "A prefix limit can stop before the end-of-frame marker and trailing-data checks."),
    ("What does Executor.map(buffersize=2) limit?", "Submitted tasks whose results have not been yielded", "Task execution time in seconds", "Worker memory to two bytes", "Input consumption pauses when the unyielded-result buffer fills."),
    ("Can ordered Executor.map results wait behind a slow first task?", "Yes", "No, results are always completion ordered", "Only for process pools", "Map preserves input order even while workers run concurrently."),
    ("Is a heapq max-heap backing list fully sorted?", "No, only the root extreme is guaranteed", "Yes, after every push", "Only when it has four items", "Heap operations maintain the heap invariant, not total list order."),
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
parent["body"] += '<p><a href="/' + quiz_path + '">Check the versioned runtime quiz</a>.</p>'
for path in targets:
    by_path[path]["body"] += '<p><a href="/' + quiz_path + '">Test this contract</a>.</p>'

fixture.write_text(json.dumps(rows, ensure_ascii=False, indent=2) + "\n")
print("Added", len(lessons), "lessons and one quiz")
