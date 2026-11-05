"""Add original Python concurrency and cleanup lessons with executable programs."""

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
        slug="async-exit-stack-partial-acquisition",
        title="Python AsyncExitStack: unwind acquired resources after a later open fails",
        summary="AsyncExitStack closes entered async contexts in reverse order when a later acquisition fails.",
        contract="A local receipt workflow acquires a database lease and then a queue lease. The third acquisition rejects its input before entering. The stack releases the two acquired leases in reverse order, and the original ValueError remains visible to the caller.",
        boundary="An async exit callback can itself fail or be cancelled; a real owner must decide how to retain cleanup failures and bound shutdown. This fixture records only in-memory events and does not open a database, broker, or network connection.",
        source='''import asyncio
from contextlib import AsyncExitStack, asynccontextmanager

events = []

@asynccontextmanager
async def receipt_lease(name, *, reject=False):
    if reject:
        raise ValueError("lease rejected")
    events.append("acquired:" + name)
    try:
        yield name
    finally:
        events.append("released:" + name)

async def prepare_receipt():
    try:
        async with AsyncExitStack() as resources:
            await resources.enter_async_context(receipt_lease("database"))
            await resources.enter_async_context(receipt_lease("queue"))
            await resources.enter_async_context(receipt_lease("export", reject=True))
    except ValueError:
        print("acquisition_rejected", True)
    print("events", events)

asyncio.run(prepare_receipt())''',
        expected="acquisition_rejected True\nevents ['acquired:database', 'acquired:queue', 'released:queue', 'released:database']",
        cost="Each entered context adds one cleanup record, so retained stack state is linear in acquired resources. Unwinding invokes every exit callback; a slow close extends the failure path.",
        mistakes=["Register cleanup as each acquisition succeeds, not only after all opens complete.", "Reverse release order matters when later resources depend on earlier ones.", "An in-memory unwind does not prove cancellation-safe cleanup of external services."],
        related=["python/exit-stack", "python/async-generator-cleanup", "python/async-task-groups"],
    ),
    dict(
        slug="loop-call-soon-threadsafe",
        title="Python asyncio loop callbacks: submit from a worker with call_soon_threadsafe",
        summary="A worker thread must hand a callback to the event loop through a thread-safe scheduling method.",
        contract="The loop owns an asyncio.Event and a receipt list. A worker thread schedules a callback that appends receipt 47 and sets the event. The coroutine waits for that event, joins the worker after delivery, and reads the loop-owned list.",
        boundary="The callback is short and runs on the loop thread; it must not perform blocking I/O. The worker keeps a reference to a live loop only for this bounded fixture. In a service, shutdown must stop submissions before closing the loop, and an Event wait needs a deadline.",
        source='''import asyncio
from threading import Thread

async def collect_receipt():
    loop = asyncio.get_running_loop()
    delivered = asyncio.Event()
    receipts = []

    def accept_on_loop():
        receipts.append(47)
        delivered.set()

    worker = Thread(target=lambda: loop.call_soon_threadsafe(accept_on_loop))
    worker.start()
    await asyncio.wait_for(delivered.wait(), timeout=2)
    worker.join()
    print("receipts", receipts)

asyncio.run(collect_receipt())''',
        expected="receipts [47]",
        cost="Scheduling one callback is small, but unbounded worker submissions can still overfill a loop's ready queue. A real producer needs admission control and a shutdown handshake.",
        mistakes=["Do not call a loop's ordinary call_soon from a different thread.", "Do not run blocking work inside the scheduled callback.", "A closed loop cannot accept new callbacks; stop producers first."],
        related=["python/async-to-thread-context", "python/async-queues", "python/run-coroutine-from-thread"],
    ),
    dict(
        slug="thread-local-pool-reuse",
        title="Python thread-local state: a reused pool worker retains the previous job's value",
        summary="threading.local separates threads, but it does not reset state between jobs on the same worker.",
        contract="A one-worker pool processes a first receipt and stores its ID in thread-local state. The next job runs on the same worker and sees the old ID before clearing it. The fixture confirms the worker reuse contract without depending on which operating-system thread ID was assigned.",
        boundary="This is a single-worker demonstration; larger pools make job-to-worker assignment nondeterministic. Thread-local state is not request-local state. Initialize and clear it around each job, or pass context explicitly when work can migrate between threads.",
        source='''from concurrent.futures import ThreadPoolExecutor
from threading import local

worker_state = local()

def record_receipt():
    worker_state.receipt_id = "R-47"
    return worker_state.receipt_id

def inspect_next_job():
    previous = getattr(worker_state, "receipt_id", None)
    if hasattr(worker_state, "receipt_id"):
        del worker_state.receipt_id
    return previous, getattr(worker_state, "receipt_id", None)

with ThreadPoolExecutor(max_workers=1) as pool:
    print("first", pool.submit(record_receipt).result())
    print("next", pool.submit(inspect_next_job).result())''',
        expected="first R-47\nnext ('R-47', None)",
        cost="A thread-local lookup is cheap; retained values can live as long as a pool thread and keep referenced objects alive. Explicit per-job cleanup prevents cross-request retention.",
        mistakes=["Thread isolation is not job isolation in a reusable executor.", "A pool's next job may inherit stale state from that worker.", "Do not use a thread-local field as a substitute for an explicit request argument."],
        related=["python/thread-pools", "python/context-variables", "python/async-to-thread-context"],
    ),
    dict(
        slug="eager-task-execution-order",
        title="Python eager asyncio tasks: a coroutine can finish before create_task returns",
        summary="An eager task factory starts a coroutine during task creation, changing when its side effects occur.",
        contract="A coroutine that never awaits is first created under the default task factory and is not yet done. The program awaits it, installs the eager factory, and creates the same coroutine again. The eager task is already complete when create_task returns; the prior factory is restored before shutdown.",
        boundary="This feature requires Python 3.12 or later and was executed on the local CPython build. A coroutine that suspends still needs event-loop scheduling. Switching a whole application's task factory changes ordering and can expose assumptions about side effects, callbacks, and error observation.",
        source='''import asyncio

async def cached_receipt_score():
    return 47

async def inspect_creation():
    loop = asyncio.get_running_loop()
    ordinary = asyncio.create_task(cached_receipt_score())
    print("ordinary_done_at_creation", ordinary.done())
    print("ordinary_result", await ordinary)

    prior_factory = loop.get_task_factory()
    loop.set_task_factory(asyncio.eager_task_factory)
    try:
        eager = asyncio.create_task(cached_receipt_score())
        print("eager_done_at_creation", eager.done())
        print("eager_result", await eager)
    finally:
        loop.set_task_factory(prior_factory)

asyncio.run(inspect_creation())''',
        expected="ordinary_done_at_creation False\nordinary_result 47\neager_done_at_creation True\neager_result 47",
        cost="An immediate result can avoid a scheduling step. The tradeoff is changed execution order; measure a real workload and review call sites before enabling the factory broadly.",
        mistakes=["Do not assume every created task is scheduled for a later loop turn.", "Do not infer that a suspending coroutine completes eagerly.", "Restore a temporary task factory in a reusable event loop."],
        related=["python/async-task-groups", "python/gather-sibling-lifetime", "python/async-deadlines"],
        minimum="3.12",
    ),
    dict(
        slug="weakref-finalizer-once",
        title="Python weakref.finalize: run an idempotent cleanup callback once",
        summary="A finalizer can be called explicitly once; its callback must not retain the object it watches.",
        contract="A receipt lease registers a callback with only the receipt ID, not a bound method on the lease. The owner calls the finalizer during normal shutdown, then calls it again. The callback records one release and the finalizer is no longer alive.",
        boundary="This fixture calls cleanup explicitly, so it does not depend on garbage-collection timing. A finalizer is a fallback for abandoned ownership, not a substitute for with or try/finally around a real resource. Exceptions from callbacks triggered by collection cannot be returned to the abandoned caller.",
        source='''import weakref

class ReceiptLease:
    pass

released_receipts = []
lease = ReceiptLease()
cleanup = weakref.finalize(lease, released_receipts.append, "R-47")
print("registered", cleanup.alive)
cleanup()
cleanup()
print("released", released_receipts)
print("still_live", cleanup.alive)''',
        expected="registered True\nreleased ['R-47']\nstill_live False",
        cost="The finalizer retains its callback and arguments until it runs or is detached. Capturing a large graph there can prolong its lifetime; capturing the watched object can prevent automatic collection entirely.",
        mistakes=["Do not pass a bound method of the watched object as its finalizer callback.", "Do not rely on collection timing for prompt resource release.", "An explicit second call does not repeat a live finalizer's cleanup."],
        related=["python/weak-references", "python/exit-stack", "python/context-managers"],
    ),
    dict(
        slug="rlock-nested-ledger",
        title="Python RLock: permit nested ledger methods without dropping the outer lock",
        summary="A reentrant lock lets one owning thread acquire the same lock in a nested method call.",
        contract="The ledger's reserve method acquires its lock, checks the input, and calls a locked balance method while still owning it. The nested acquisition succeeds, then reserve changes the balance. A rejected negative amount leaves the prior balance intact.",
        boundary="RLock solves only same-thread reentry. It does not make a sequence of separate public method calls atomic, protect another process, or turn an external payment into a transaction. Every acquire must be matched by release; using with scopes makes the count visible.",
        source='''from threading import RLock

class ReceiptBalance:
    def __init__(self, opening_amount):
        self._lock = RLock()
        self._available = opening_amount

    def available(self):
        with self._lock:
            return self._available

    def reserve(self, amount):
        with self._lock:
            if type(amount) is not int or amount < 0 or amount > self.available():
                raise ValueError("invalid reservation")
            self._available -= amount
            return self._available

balance = ReceiptBalance(73)
print("remaining", balance.reserve(47))
try:
    balance.reserve(-1)
except ValueError:
    print("negative_rejected", True)
print("unchanged", balance.available())''',
        expected="remaining 26\nnegative_rejected True\nunchanged 26",
        cost="RLock tracks the owning thread and recursion depth, adding bookkeeping to ordinary lock acquisition. Avoid nested public calls when a simpler private method can keep one lock scope.",
        mistakes=["An ordinary non-reentrant Lock would block on this nested acquisition.", "RLock does not protect a multi-call client workflow by itself.", "Do not return from a manual acquire path without a matching release."],
        related=["python/thread-locks", "python/condition-predicates", "python/queue-task-done-ownership"],
    ),
    dict(
        slug="run-coroutine-from-thread",
        title="Python run_coroutine_threadsafe: submit to a live loop and own shutdown",
        summary="A non-loop thread can submit a coroutine to an already-running event loop and wait on a concurrent future.",
        contract="A dedicated worker thread runs one local event loop. The main thread submits a short receipt calculation through run_coroutine_threadsafe, waits for the result with a timeout, then signals loop.stop, joins the worker, and closes the loop. No network transport is opened.",
        boundary="A result timeout does not automatically stop the coroutine. A production caller must decide whether to cancel the returned future and wait for task cleanup. The fixture waits for the known short result before stopping the loop, so it leaves no task pending at close.",
        source='''import asyncio
from threading import Event, Thread

async def calculate_receipt_total():
    return 47 + 26

loop = asyncio.new_event_loop()
ready = Event()

def run_receipt_loop():
    asyncio.set_event_loop(loop)
    ready.set()
    loop.run_forever()

worker = Thread(target=run_receipt_loop)
worker.start()
try:
    if not ready.wait(timeout=2):
        raise TimeoutError("loop did not start")
    result = asyncio.run_coroutine_threadsafe(calculate_receipt_total(), loop)
    print("total", result.result(timeout=2))
finally:
    loop.call_soon_threadsafe(loop.stop)
    worker.join(timeout=2)
    if worker.is_alive():
        raise TimeoutError("loop did not stop")
    loop.close()''',
        expected="total 73",
        cost="The thread and event loop have startup and teardown costs that dominate one addition. Keep a loop alive only for an owned workload, and bound the number of submitted tasks.",
        mistakes=["Do not call result() on the loop thread; it would block the loop.", "A timeout on the concurrent future is not automatic task cancellation.", "Stop producers and finish tasks before closing the loop."],
        related=["python/loop-call-soon-threadsafe", "python/async-deadlines", "python/thread-pools"],
    ),
    dict(
        slug="to-thread-cancel-lifetime",
        title="Python asyncio.to_thread cancellation: the blocking worker can outlive its awaiter",
        summary="Cancelling a task awaiting to_thread does not interrupt a function already running in an OS thread.",
        contract="A blocking export signals that it started, then waits on an owned threading.Event. The async task awaiting it is cancelled; the export is still blocked. The owner releases the worker, waits for its completion signal, and allows asyncio.run to shut down its executor cleanly.",
        boundary="This uses a controllable local function, not a real file or network operation. A production blocking call needs its own stop signal, deadline, and idempotent cleanup. Abandoning its async awaiter does not transfer those responsibilities to the event loop.",
        source='''import asyncio
from threading import Event

started = Event()
release = Event()
finished = Event()

def blocking_receipt_export():
    started.set()
    release.wait(timeout=5)
    finished.set()
    return "R-47"

async def cancel_export_awaiter():
    export_task = asyncio.create_task(asyncio.to_thread(blocking_receipt_export))
    try:
        if not await asyncio.to_thread(started.wait, 2):
            raise TimeoutError("export did not start")
        export_task.cancel()
        try:
            await export_task
        except asyncio.CancelledError:
            print("awaiter_cancelled", True)
        print("worker_still_blocked", not finished.is_set())
    finally:
        release.set()
    if not await asyncio.to_thread(finished.wait, 2):
        raise TimeoutError("export did not finish")
    print("worker_finished", finished.is_set())

asyncio.run(cancel_export_awaiter())''',
        expected="awaiter_cancelled True\nworker_still_blocked True\nworker_finished True",
        cost="A blocked worker consumes one executor thread even after the awaiter is cancelled. Unbounded calls can exhaust the pool; use admission limits and cooperative stop signals around blocking work.",
        mistakes=["Cancelling the asyncio task does not kill the OS thread.", "Release or stop the worker before shutting down the executor.", "A timeout on the awaiter does not bound a blocking function's own lifetime."],
        related=["python/async-to-thread-context", "python/async-shield-ownership", "python/thread-pools"],
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
        for target in item["related"]) + "</ul>"
    minimum = item.get("minimum", "3.11")
    row = copy.deepcopy(by_path["python/async-task-groups"])
    row.update(id=str(uuid.uuid5(uuid.NAMESPACE_URL, "https://aitrove.in/" + path)),
               path=path, title=item["title"], summary=item["summary"], body=body,
               subject="python-advanced", tags=["python", item["slug"]],
               sort_order=9000 + order, published_at=stamp, created_at=stamp, updated_at=stamp)
    row["data"] = {"subject_root": "python/python-programming-language-tutorial",
                   "section_path": "python/advanced-python", "content_format": "html", "kind": "tutorial",
                   "python_version": minimum + "+ syntax; verified on local CPython",
                   "python_minimum": minimum, "reading_minutes": 5,
                   "author_path": "authors/aitrove-editorial",
                   "download_path": "/downloads/aitrove-python-source-kit.zip",
                   "related": [{"path": target, "title": titles[target]} for target in item["related"]],
                   "seo_ready": True, "expected_output": item["expected"]}
    if minimum != "3.11":
        row["data"]["python_syntax"] = minimum
    rows.append(row)
    by_path[path] = row

advanced = by_path["python/advanced-python"]
advanced["data"]["modules"].append({"title": "Cross-thread scheduling and cleanup lifetime",
                                    "summary": "Checked local programs with explicit shutdown and ownership limits.",
                                    "lessons": new_paths})
advanced["body"] += "<h2>Cross-thread scheduling and cleanup lifetime</h2><ul>" + "".join(
    '<li><a href="/' + path + '">' + html.escape(titles[path]) + "</a></li>"
    for path in new_paths) + "</ul>"
advanced["updated_at"] = stamp
parent = by_path["python/python-programming-language-tutorial"]
parent["body"] += "<h2>Cross-thread scheduling and cleanup lifetime</h2><ul>" + "".join(
    '<li><a href="/' + path + '">' + html.escape(titles[path]) + "</a></li>"
    for path in new_paths) + "</ul>"
parent["updated_at"] = stamp

for source, target in [
    ("python/exit-stack", "python/async-exit-stack-partial-acquisition"),
    ("python/async-queues", "python/loop-call-soon-threadsafe"),
    ("python/thread-pools", "python/thread-local-pool-reuse"),
    ("python/gather-sibling-lifetime", "python/eager-task-execution-order"),
    ("python/weak-references", "python/weakref-finalizer-once"),
    ("python/thread-locks", "python/rlock-nested-ledger"),
    ("python/async-deadlines", "python/run-coroutine-from-thread"),
    ("python/async-to-thread-context", "python/to-thread-cancel-lifetime"),
]:
    row = by_path[source]
    row["body"] += '<p><a href="/' + target + '">Continue with ' + html.escape(titles[target]) + "</a>.</p>"
    row["updated_at"] = stamp

quiz_path = "quizzes/python-thread-async-lifetimes"
assert quiz_path not in by_path
quiz = copy.deepcopy(by_path["quizzes/python-boundary-contracts"])
quiz_body = "<p>Check async cleanup, cross-thread submission, worker state and cancellation lifetime.</p><h2>Review the related lessons</h2><ul>"
quiz_body += "".join('<li><a href="/' + path + '">' + html.escape(titles[path]) + "</a></li>" for path in new_paths)
quiz_body += "</ul><h3>Common Mistakes</h3><p>A local event ordering test is not a stress test of a shared service.</p>"
quiz.update(id=str(uuid.uuid5(uuid.NAMESPACE_URL, "https://aitrove.in/" + quiz_path)),
            path=quiz_path, title="Python threads and async lifetime quiz",
            summary="Twelve explained questions on cleanup, worker reuse, task factories and cancellation.",
            body=quiz_body, sort_order=9100, published_at=stamp, created_at=stamp, updated_at=stamp)
raw_questions = [
    ("What happens to contexts already entered when a later AsyncExitStack acquisition fails?", "They exit in reverse order", "They stay open until process exit", "They are committed automatically", "Each successful entry registered cleanup before the later failure."),
    ("Which scheduling method may a worker thread use on an asyncio loop?", "call_soon_threadsafe", "call_soon without coordination", "run_until_complete on the running loop", "The thread-safe method hands a short callback to the loop owner."),
    ("Does threading.local reset when a pool worker starts its next job?", "No", "Yes", "Only for strings", "The same OS thread can retain its prior job's fields."),
    ("When can an eager task finish?", "During task creation", "Only after a later loop turn", "Only after executor shutdown", "A coroutine that does not suspend may complete before create_task returns."),
    ("What must weakref.finalize callback arguments avoid?", "A strong reference to the watched object", "Immutable receipt IDs", "A separate release list", "Retaining the watched object can prevent collection from triggering the finalizer."),
    ("How many times does a live finalizer run after two explicit calls?", "Once", "Twice", "Until the object is collected", "The first call marks the finalizer dead."),
    ("Why does nested access work under RLock?", "The owning thread can reacquire it", "Every thread can enter without blocking", "It commits changes automatically", "Reentry is limited to the current owner and still requires balanced releases."),
    ("What does run_coroutine_threadsafe return to the submitting thread?", "A concurrent.futures.Future", "A completed coroutine object", "A new event loop", "The caller can await its outcome through the concurrent future's result method."),
    ("Does Future.result(timeout) stop its coroutine when the timeout expires?", "No", "Yes", "Only for one-thread loops", "The owner must choose whether to request cancellation and observe cleanup."),
    ("What survives cancellation of an awaiter using asyncio.to_thread?", "A blocking function already running in its worker thread", "No worker can remain", "Only the coroutine return value", "Cancelling the awaiter does not interrupt an OS thread."),
    ("What should a pool job do with request-specific thread-local state?", "Clear it before the worker serves another job", "Keep it for the next job", "Publish it as a global default", "Worker reuse can expose stale request context."),
    ("What must happen before closing a dedicated event loop?", "Stop submissions and finish owned tasks", "Call close while work is pending", "Ignore the worker thread", "Loop shutdown has task and thread owners that need an explicit sequence."),
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
parent["body"] += '<p><a href="/' + quiz_path + '">Check the thread and async lifetime quiz</a>.</p>'
for path in new_paths:
    by_path[path]["body"] += '<p><a href="/' + quiz_path + '">Test this contract</a>.</p>'

fixture.write_text(json.dumps(rows, ensure_ascii=False, indent=2) + "\n")
print("Added", len(lessons), "lessons and one quiz")
