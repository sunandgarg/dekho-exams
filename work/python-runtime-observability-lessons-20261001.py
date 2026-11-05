"""Publish checked Python runtime, introspection, and native-memory lessons."""

import copy
import datetime
import html
import json
from pathlib import Path
import uuid


root = Path(__file__).resolve().parents[1]
fixture = root / "src/data/fixtures.json"
rows = json.loads(fixture.read_text())
by_path = {row["path"]: row for row in rows}
stamp = datetime.datetime.now(datetime.UTC).isoformat()

lessons = [
    dict(
        slug="free-threaded-lock-contract", section="python/advanced-python", subject="python-advanced", minimum="3.13",
        title="Python free-threaded builds: lock the whole shared-state update",
        summary="An optional free-threaded CPython build changes scheduling; a shared application invariant still needs an explicit lock.",
        contract="Four workers each record forty-seven accepted events. The count is updated inside one lock, so the final count is 188 regardless of scheduling. The program also reads the running process's GIL state instead of guessing from its Python version. The displayed state is from the checked standard build.",
        boundary="The GIL state can differ on a free-threaded binary and can change when an extension enables it. A successful run under the usual build is not a concurrency stress test. Every writer and reader of a multi-field invariant must follow the same synchronization policy; a thread-safe dictionary operation alone cannot make a larger transaction atomic.",
        source='''import sys
from threading import Lock, Thread

accepted_events = 0
event_lock = Lock()

def record_events():
    global accepted_events
    for _ in range(47):
        with event_lock:
            accepted_events += 1

workers = [Thread(target=record_events) for _ in range(4)]
for worker in workers:
    worker.start()
for worker in workers:
    worker.join()
print("gil_enabled", sys._is_gil_enabled())
print("accepted", accepted_events)''',
        expected="gil_enabled True\naccepted 188",
        cost="The four workers perform 188 locked increments. Lock contention can serialize this short operation; measure a real workload on each supported interpreter build.",
        mistakes=["A free-threaded build is not proof that a compound operation is safe without a lock.", "The version number does not reveal the process's current GIL state.", "Do not infer a speedup from a tiny counter fixture."],
        related=["python/thread-locks", "python/thread-pools", "python/runtime-compatibility"],
    ),
    dict(
        slug="interpreter-pool-isolation", section="python/advanced-python", subject="python-advanced", minimum="3.14",
        title="Python InterpreterPoolExecutor: pass results across isolated runtimes",
        summary="Interpreter workers have separate module state; return values instead of expecting a shared mutable global.",
        contract="Two receipt amounts are processed by isolated interpreters. Each worker appends to its own module-level list, returns a score, and the parent collects ordered results. The parent's list remains empty. Run this source as a file so the top-level callable can be found by workers.",
        boundary="The executor serializes submitted callables and arguments. Large payloads may spend more time crossing the boundary than the calculation saves. Extension modules must support subinterpreters, and a worker-local global is not shared state or persistent storage. Do not use this fixture as evidence of a multi-core speedup.",
        source='''from concurrent.futures import InterpreterPoolExecutor

reviewed_amounts = []

def score_receipt(amount):
    reviewed_amounts.append(amount)
    return amount * 2

if __name__ == "__main__":
    with InterpreterPoolExecutor(max_workers=2) as pool:
        scores = list(pool.map(score_receipt, (47, 48)))
    print("scores", scores)
    print("parent_reviews", len(reviewed_amounts))''',
        expected="scores [94, 96]\nparent_reviews 0",
        cost="Each worker owns interpreter state and incurs startup plus serialization overhead. Parallel CPU work needs enough duration to repay those costs.",
        mistakes=["A module global in one interpreter is not the parent's global.", "A local closure or unsupported extension may fail to cross the worker boundary.", "A returned value is not a durable write to a database."],
        related=["python/multiprocessing-spawn-guard", "python/thread-pools", "python/executor-map-buffer"],
    ),
    dict(
        slug="template-string-html-text", section="python/examples", subject="python-examples", minimum="3.14", syntax="3.14",
        title="Python template strings: escape text values before rendering HTML",
        summary="A t-string keeps literal fragments separate from evaluated expressions so a renderer can escape text values.",
        contract="The renderer receives a developer-owned markup template with an invoice ID and a customer note. Literal fragments are preserved; interpolated values are HTML-escaped. The note contains angle brackets and an ampersand, so the output shows them as text rather than treating them as markup.",
        boundary="This renderer is only for text-node substitutions inside a trusted template. Attribute, URL, CSS, and script contexts need different rules; simply escaping a value does not make an arbitrary HTML template safe. Expression evaluation happens when the t-string is created, before the renderer sees it. Never treat a template object as a general sandbox.",
        source='''from html import escape
from string.templatelib import Interpolation

def render_text_nodes(template):
    fragments = []
    for part in template:
        if isinstance(part, Interpolation):
            fragments.append(escape(str(part.value), quote=True))
        else:
            fragments.append(part)
    return "".join(fragments)

invoice_id = "inv-47"
customer_note = "<admin>& overdue"
markup = render_text_nodes(t"<p>{invoice_id}: {customer_note}</p>")
print(markup)''',
        expected="<p>inv-47: &lt;admin&gt;&amp; overdue</p>",
        cost="Rendering visits each template fragment and allocates an output string proportional to the final escaped length. It does not parse or validate arbitrary HTML.",
        mistakes=["A t-string does not escape values automatically.", "Text-node escaping is not an attribute or URL policy.", "Expressions run while constructing the template object."],
        related=["python/flask-json-api", "python/django-template-escaping", "python/typing-reference"],
    ),
    dict(
        slug="cprofile-call-counts", section="python/testing", subject="python-testing", minimum="3.11",
        title="Python cProfile: inspect call counts without asserting timing",
        summary="cProfile records executed calls; exact elapsed time is not a stable test assertion.",
        contract="A settlement calculation runs three times under one profiler. The resulting Stats object is queried for the function's call count, while the last business total is asserted independently. This verifies instrumentation without printing timing numbers that change with hardware and process load.",
        boundary="Profiling adds overhead and can change scheduling. A deterministic call count says nothing about production latency, input-size growth, or memory allocation. For a bottleneck decision, profile representative data and inspect cumulative time across the actual call graph, then benchmark the revised implementation separately.",
        source='''import cProfile
import pstats

def net_total(amounts):
    return sum(amount - 3 for amount in amounts)

profile = cProfile.Profile()
for _ in range(3):
    last_total = profile.runcall(net_total, (47, 48, 49))
statistics = pstats.Stats(profile)
calls = sum(record[1] for key, record in statistics.stats.items()
            if key[2] == "net_total")
print("last_total", last_total)
print("calls", calls)''',
        expected="last_total 135\ncalls 3",
        cost="Instrumentation records function events and adds runtime overhead. Its storage grows with the number of distinct recorded call sites, not with this printed call count alone.",
        mistakes=["Do not assert exact profile seconds in a portable test.", "A call count is not a latency measurement.", "Small synthetic inputs can hide the expensive path in production."],
        related=["python/tracemalloc-retention", "python/unittest-contracts", "python/runtime-compatibility"],
    ),
    dict(
        slug="asyncio-call-graph-observation", section="python/advanced-python", subject="python-advanced", minimum="3.14",
        title="Python asyncio call graphs: inspect a live task without retaining frames",
        summary="capture_call_graph can show the current task and its await relationship during execution.",
        contract="A task created inside TaskGroup captures its own graph. It reports that the graph refers to the running task and that an awaiting parent is recorded. The fixture prints only booleans, avoiding unstable frame addresses and line numbers in the displayed output.",
        boundary="A graph is a momentary diagnostic, not a proof that the task will finish. Custom Future bridges need to register await relationships for a complete picture. Captured frames can retain local references; consume the result promptly and avoid storing it in a long-lived diagnostic cache. Task names and stacks can also expose sensitive data if logged raw.",
        source='''import asyncio

async def inspect_receipt():
    graph = asyncio.capture_call_graph(depth=0)
    return (graph.future is asyncio.current_task(),
            bool(graph.awaited_by))

async def main():
    async with asyncio.TaskGroup() as group:
        inspection = group.create_task(inspect_receipt())
    current, awaited = inspection.result()
    print("current_task", current)
    print("awaited_by_parent", awaited)

asyncio.run(main())''',
        expected="current_task True\nawaited_by_parent True",
        cost="Walking a call graph takes time proportional to the captured stacks and await relationships. Keep diagnostics off hot request paths unless sampled and measured.",
        mistakes=["A captured graph is not a completion guarantee.", "Do not retain frame-bearing graph objects indefinitely.", "Custom Future wrappers can hide relationships unless they cooperate."],
        related=["python/async-task-groups", "python/async-shield-ownership", "python/asyncio-test-fixture"],
    ),
    dict(
        slug="ctypes-memoryview-pointer-lifetime", section="python/advanced-python", subject="python-advanced", minimum="3.14",
        title="Python ctypes.memoryview_at: keep native pointer storage alive",
        summary="A view created from an address does not take ownership of the memory behind that address.",
        contract="A ctypes buffer owns forty-seven bytes. memoryview_at exposes the same bytes without making a second payload copy; changing the first byte through the owner is visible through the view. The buffer remains alive until the view is released. No external library or untrusted address is used.",
        boundary="An integer address alone is not a lifetime guarantee. If native code frees or reallocates the storage while Python still reads the view, access can be invalid. The caller must prove the pointer and length are valid for the entire view lifetime. readonly prevents writes through that view but does not freeze memory owned elsewhere.",
        source='''import ctypes

receipt_buffer = ctypes.create_string_buffer(b"R" * 47)
address = ctypes.addressof(receipt_buffer)
receipt_view = ctypes.memoryview_at(address, 47, readonly=True)
try:
    print("initial", bytes(receipt_view) == b"R" * 47)
    receipt_buffer[0] = b"S"
    print("owner_change_visible", bytes(receipt_view).startswith(b"S"))
finally:
    receipt_view.release()''',
        expected="initial True\nowner_change_visible True",
        cost="View creation is O(1) and avoids copying the payload. Converting the view to bytes in this small verification allocates and copies forty-seven bytes.",
        mistakes=["A readonly view does not make other owners unable to write.", "Never construct a view from an unverified integer address or length.", "Keep the native allocation alive until every view is released."],
        related=["python/memoryview-buffers", "python/weakref-cache-ownership", "python/runtime-compatibility"],
    ),
    dict(
        slug="partial-placeholder-position", section="python/advanced-python", subject="python-advanced", minimum="3.14",
        title="Python partial Placeholder: leave a positional amount open",
        summary="functools.Placeholder reserves a positional slot inside a partially applied callable.",
        contract="A quote function expects an amount, a fixed fee, and a currency. The partial binds the latter two while leaving the amount open, so a caller can price a forty-seven-unit invoice with a seven-unit fee. A call that supplies no amount fails before the quote function runs.",
        boundary="Every placeholder must receive a positional value at call time. Placeholder cannot stand in for a keyword argument. A partial object binds values but does not validate whether the fee, currency, or amount matches a live pricing policy; that belongs in the called function or its owner.",
        source='''from functools import Placeholder, partial

def invoice_balance(amount, fixed_fee, currency):
    return f"{currency} {amount - fixed_fee}"

quote_after_fee = partial(invoice_balance, Placeholder, 7, "INR")
print("balance", quote_after_fee(47))
try:
    quote_after_fee()
except TypeError:
    print("missing_amount_rejected", True)''',
        expected="balance INR 40\nmissing_amount_rejected True",
        cost="A partial stores bound argument references and adds a small call wrapper. It does not precompute the invoice result or clone mutable bound objects.",
        mistakes=["All reserved positional slots must be filled.", "Placeholder is not supported as a keyword value in partial.", "Binding an amount or fee does not enforce a business rule."],
        related=["python/closures", "python/decorators", "python/copy-replace-protocol"],
    ),
    dict(
        slug="pathlib-copy-policy", section="python/examples", subject="python-examples", minimum="3.14",
        title="Python Path.copy: a snapshot needs an explicit metadata policy",
        summary="Path.copy creates another file or tree; copied bytes and copied metadata have different defaults.",
        contract="A temporary receipt file is copied into an archive path, then the source is revised. The destination retains its earlier bytes. The default call checks file content only; it does not ask to preserve all available metadata. Both paths are owned by the fixture and removed when the temporary directory closes.",
        boundary="Path.copy may replace an existing file at the destination, and symlinks are followed by default. Choose a destination policy before copying user-selected paths. The copy is not a transactional backup: source mutation during copying, failed writes, cross-filesystem behavior, and crash recovery need separate handling. Request metadata preservation only when the application requires it.",
        source='''from pathlib import Path
from tempfile import TemporaryDirectory

with TemporaryDirectory() as directory:
    source = Path(directory) / "current-receipt.txt"
    archived = Path(directory) / "archived-receipt.txt"
    source.write_text("batch-47", encoding="utf-8")
    copied = source.copy(archived)
    source.write_text("batch-48", encoding="utf-8")
    print("copied", copied.read_text(encoding="utf-8"))
    print("current", source.read_text(encoding="utf-8"))''',
        expected="copied batch-47\ncurrent batch-48",
        cost="Copy cost generally grows with data size, although a filesystem may support copy-on-write. Metadata preservation and cross-device handling add filesystem work; measure on the deployment volume.",
        mistakes=["The default copy need not preserve every file attribute.", "The destination may be replaced if it already exists.", "A copy made during concurrent writes is not automatically a consistent snapshot."],
        related=["python/pathlib-files", "python/tempdir-cleanup-tests", "python/atomic-file-replacement"],
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
    body += "<h3>Common Mistakes</h3><ul>" + "".join(
        "<li>" + html.escape(mistake) + "</li>" for mistake in item["mistakes"]
    ) + "</ul>"
    body += "<h2>Connected lessons</h2><ul>" + "".join(
        '<li><a href="/' + target + '">' + html.escape(titles[target]) + "</a></li>"
        for target in item["related"]
    ) + "</ul>"
    row = copy.deepcopy(by_path["python/async-task-groups"])
    row.update(id=str(uuid.uuid5(uuid.NAMESPACE_URL, "https://aitrove.in/" + path)),
               path=path, title=item["title"], summary=item["summary"], body=body,
               subject=item["subject"], tags=["python", item["slug"]],
               sort_order=8200 + order, published_at=stamp, created_at=stamp, updated_at=stamp)
    row["data"] = {"subject_root": "python/python-programming-language-tutorial",
                   "section_path": item["section"], "content_format": "html", "kind": "tutorial",
                   "python_version": f"{item['minimum']}+; verified on local CPython",
                   "python_minimum": item["minimum"], "reading_minutes": 5,
                   "author_path": "authors/aitrove-editorial",
                   "download_path": "/downloads/aitrove-python-source-kit.zip",
                   "related": [{"path": target, "title": titles[target]} for target in item["related"]],
                   "seo_ready": True, "expected_output": item["expected"]}
    if "syntax" in item:
        row["data"]["python_syntax"] = item["syntax"]
    rows.append(row)
    by_path[path] = row

for section in sorted({item["section"] for item in lessons}):
    paths = ["python/" + item["slug"] for item in lessons if item["section"] == section]
    hub = by_path[section]
    hub["data"]["modules"].append({"title": "Runtime, profiling, and ownership",
                                   "summary": "Runnable interpreter and memory-boundary checks.",
                                   "lessons": paths})
    hub["body"] += "<h2>Runtime, profiling, and ownership</h2><ul>" + "".join(
        '<li><a href="/' + path + '">' + html.escape(titles[path]) + "</a></li>"
        for path in paths) + "</ul>"
    hub["updated_at"] = stamp

parent = by_path["python/python-programming-language-tutorial"]
parent["body"] += "<h2>Runtime and observability contracts</h2><ul>" + "".join(
    '<li><a href="/python/' + item["slug"] + '">' + html.escape(item["title"]) + "</a></li>"
    for item in lessons) + "</ul>"
parent["updated_at"] = stamp
for source, target in [
    ("python/thread-locks", "python/free-threaded-lock-contract"),
    ("python/multiprocessing-spawn-guard", "python/interpreter-pool-isolation"),
    ("python/django-template-escaping", "python/template-string-html-text"),
    ("python/tracemalloc-retention", "python/cprofile-call-counts"),
    ("python/async-task-groups", "python/asyncio-call-graph-observation"),
    ("python/memoryview-buffers", "python/ctypes-memoryview-pointer-lifetime"),
    ("python/closures", "python/partial-placeholder-position"),
    ("python/pathlib-files", "python/pathlib-copy-policy"),
]:
    row = by_path[source]
    row["body"] += '<p><a href="/' + target + '">Continue with ' + html.escape(titles[target]) + "</a>.</p>"
    row["updated_at"] = stamp

quiz_path = "quizzes/python-runtime-observability-contracts"
assert quiz_path not in by_path
quiz = copy.deepcopy(by_path["quizzes/python-boundary-contracts"])
targets = ["python/" + item["slug"] for item in lessons]
quiz_body = "<p>Check runtime-state, worker-isolation, profiling and native-memory decisions.</p><h2>Review the related lessons</h2><ul>"
quiz_body += "".join('<li><a href="/' + path + '">' + html.escape(titles[path]) + "</a></li>" for path in targets)
quiz_body += "</ul><h3>Common Mistakes</h3><p>A correct answer does not establish an extension's subinterpreter support or a free-threaded performance gain.</p>"
quiz.update(id=str(uuid.uuid5(uuid.NAMESPACE_URL, "https://aitrove.in/" + quiz_path)),
            path=quiz_path, title="Python runtime and observability contracts quiz",
            summary="Twelve explained questions on interpreters, t-strings, profiling, async graphs and pointer ownership.",
            body=quiz_body, sort_order=8300, published_at=stamp, created_at=stamp, updated_at=stamp)
raw_questions = [
    ("Which check reports whether the GIL is enabled in the running process?", "sys._is_gil_enabled()", "The minor version alone", "The number of live threads", "Runtime state can differ from build support and can be changed by extension imports."),
    ("What protects a multi-step shared update on a free-threaded build?", "An explicit synchronization policy", "A list append somewhere else", "The source filename", "Protect the complete invariant across all cooperating readers and writers."),
    ("Why is the parent's global list unchanged after InterpreterPoolExecutor tasks?", "Workers have separate interpreter module state", "The parent list is automatically frozen", "map discards every return value", "Workers return results across isolation; they do not mutate the parent's global list."),
    ("What does a t-string renderer receive for an interpolation?", "An evaluated value separate from literal fragments", "Automatically escaped HTML", "A compiled database transaction", "The renderer chooses how to process each value for its output context."),
    ("Is HTML text-node escaping enough for an arbitrary URL attribute?", "No, the output context needs its own policy", "Yes, every attribute is a text node", "Only if the string begins with a slash", "The demonstrated renderer handles trusted markup with text slots only."),
    ("Which cProfile result is stable enough for the fixed local call fixture?", "The expected number of calls to the owned function", "Exact wall-clock seconds", "Production throughput", "Three explicit calls can be checked without making timing an assertion."),
    ("What may an asyncio call graph retain if stored long term?", "Frame references and their local objects", "A guaranteed task result", "A database snapshot", "Inspect a captured graph promptly and avoid keeping diagnostic frames alive."),
    ("What does a live task call graph fail to prove?", "That the task will eventually complete", "That a current task exists", "That an await relationship was captured", "The graph describes one moment rather than a completion contract."),
    ("Who owns bytes behind ctypes.memoryview_at in the fixture?", "The ctypes buffer", "The integer address", "The readonly flag", "The view does not extend an arbitrary native allocation's lifetime by itself."),
    ("Does a readonly pointer view freeze writes through another owner?", "No", "Yes", "Only on a free-threaded build", "Readonly limits that view's writes, not all ways to mutate the underlying storage."),
    ("What must happen to each partial Placeholder slot at call time?", "It receives a positional argument", "It becomes a keyword argument", "It is always replaced by None", "An unfilled positional reservation makes the call fail."),
    ("What is not guaranteed by Path.copy's default policy?", "Full metadata preservation and a transactional snapshot", "A new destination path", "Copied file bytes on success", "Source concurrency, metadata requirements and destination replacement need explicit policy."),
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
parent["body"] += '<p><a href="/' + quiz_path + '">Check the runtime and observability quiz</a>.</p>'
for path in targets:
    by_path[path]["body"] += '<p><a href="/' + quiz_path + '">Test this contract</a>.</p>'

fixture.write_text(json.dumps(rows, ensure_ascii=False, indent=2) + "\n")
print("Added", len(lessons), "lessons and one quiz")
