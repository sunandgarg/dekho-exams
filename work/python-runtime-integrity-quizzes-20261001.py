"""Add explained quizzes for the new Python boundary lessons."""

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


def question(prompt, correct, wrong_a, wrong_b, explanation, position):
    choices = [correct, wrong_a, wrong_b]
    ordered = choices[position:] + choices[:position]
    return {"prompt": prompt, "options": ordered,
            "answer": ordered.index(correct), "explanation": explanation}


banks = [
    (
        "python-concurrency-storage-contracts",
        "Python concurrency and storage boundary quiz",
        ["python/async-semaphore-admission", "python/future-cancel-before-start",
         "python/queue-task-done-ownership", "python/sqlite-busy-write-contract",
         "python/sqlite-wal-snapshot-read", "python/frozen-dataclass-shallow-state"],
        [
            ("What does an asyncio.Semaphore limit in the lesson?", "Tasks inside the guarded region at one time", "The total number of created tasks", "The number of operating-system processes", "The semaphore controls admission to its protected region, not task creation."),
            ("Does a semaphore make a shared object thread-safe?", "No; it only governs cooperating callers that acquire it", "Yes, for every thread in the process", "Yes, when its capacity is greater than one", "Uncoordinated code can still mutate the same state."),
            ("When can Future.cancel() prevent work from starting?", "Before a worker begins that future", "After the callable has returned", "Only after result() raises", "Cancellation of a pending future can succeed; a running callable is not stopped by cancel()."),
            ("What does cancel() returning False prove?", "The pending cancellation did not succeed", "The callable completed successfully", "The worker process crashed", "A false result does not describe whether a running callable will succeed."),
            ("How often should a consumer call queue.task_done()?", "Once for each item returned by get()", "Once for each rejected item plus once for its retry", "Only when the queue becomes empty", "Each get adds one completion obligation, including a failed processing attempt."),
            ("What can queue.join() tell the producer?", "Every enqueued item has had its completion call", "All business operations succeeded", "No consumer can add more items", "The unfinished-task counter says nothing about business success."),
            ("What happens when two SQLite writers conflict beyond the configured busy timeout?", "One operation raises an operational error", "SQLite merges both writes automatically", "The older connection becomes read-only forever", "A finite wait does not guarantee that the lock becomes available."),
            ("Should the application retry a write while holding an unrelated lock?", "No; that can compound contention", "Yes; it guarantees transaction order", "Yes; SQLite releases every application lock", "A retry policy needs bounded attempts and a clear transaction boundary."),
            ("What can a WAL reader see during a concurrent committed write?", "Its established read snapshot until that transaction ends", "Every uncommitted row immediately", "No rows at all", "A read transaction keeps its snapshot while writes can commit separately."),
            ("Does WAL mean SQLite allows two simultaneous writers?", "No; writes still serialize", "Yes, with no transaction boundary", "Only if both writers share a cursor", "WAL improves reader and writer overlap, not the single-writer rule."),
            ("Does frozen=True recursively freeze a list field?", "No; the referenced list may still mutate", "Yes; every nested element becomes a tuple", "Only when slots=True is also set", "The generated assignment guard is shallow."),
            ("How should a frozen record expose an immutable sequence contract?", "Store a tuple or copy into immutable storage", "Return the original mutable list", "Disable equality", "Immutable field references do not make mutable objects immutable."),
        ],
    ),
    (
        "python-io-algorithm-boundaries",
        "Python I/O and algorithm boundary quiz",
        ["python/json-nonfinite-number-boundary", "python/heap-priority-revision",
         "python/topological-cycle-witness", "python/interval-capacity-sweep",
         "python/csv-spreadsheet-export-boundary", "python/ipaddress-network-membership",
         "python/argparse-command-contract"],
        [
            ("What must a strict JSON writer do with NaN?", "Reject it or define a separate valid representation", "Write it as an ordinary JSON number", "Convert it to a boolean automatically", "NaN is outside the JSON number grammar; allow_nan=False rejects it."),
            ("Why is allow_nan=False useful at an API boundary?", "It exposes non-finite values before publication", "It validates every object schema", "It encrypts the response", "Strict encoding reveals invalid numeric state without claiming to validate the entire payload."),
            ("What should a heap consumer do with an obsolete priority entry?", "Skip it after checking the current revision", "Treat it as the latest value", "Mutate the tuple inside the heap", "Lazy invalidation compares a popped entry with authoritative state."),
            ("What resource cost can lazy heap invalidation add?", "Stale entries occupy heap memory until removed or rebuilt", "Every update becomes constant memory", "The heap stops ordering priorities", "Logical deletion avoids arbitrary heap removal but retains stale entries temporarily."),
            ("What does an incomplete topological ordering imply?", "At least one cycle remains in the selected dependency graph", "The graph has no nodes", "Every node has zero indegree", "Kahn's algorithm cannot emit all nodes when cyclic dependencies remain."),
            ("Can a topological order prove which single edge caused a cycle?", "No; a separate cycle witness is needed", "Yes; the first emitted edge is always the cause", "Yes; sorting node names identifies it", "The incomplete order detects a cycle but does not by itself identify a precise edge."),
            ("With half-open booking intervals, which event happens first at a shared endpoint?", "An ending booking is released before a starting booking", "A starting booking consumes capacity first", "Both bookings remain active forever", "At [start,end) boundaries, adjacent bookings do not overlap."),
            ("What does a capacity sweep require before counting occupancy?", "A consistent endpoint convention", "A database index", "Only integer customer IDs", "Changing endpoint meaning changes the overlap result."),
            ("Does csv.writer quoting prevent a spreadsheet formula from executing?", "No; quoting preserves CSV structure only", "Yes; every spreadsheet treats quotes as text", "Only if the header is uppercase", "Spreadsheet interpretation occurs after CSV parsing and varies by product."),
            ("Is a request-supplied forwarded IP header an authenticated peer address?", "No; trust requires a defined proxy boundary", "Yes; the header name proves its origin", "Yes, for private address ranges", "An attacker can supply headers unless the edge strips and rewrites them."),
            ("What does argparse type=int check for --limit?", "Integer syntax, not the accepted business range", "The caller's authorization", "The command's side effects", "Range validation remains explicit application work."),
            ("What does required=True on argparse subparsers prevent?", "An omitted operation selecting an implicit command", "Every misspelled tenant", "All filesystem access", "A required subcommand makes operation selection explicit before work begins."),
        ],
    ),
]

for slug, title, targets, raw_questions in banks:
    path = "quizzes/" + slug
    assert path not in by_path
    assert len(raw_questions) == 12
    for target in targets:
        assert target in by_path, target
    body = "<p>Choose the operation contract, then read why the other choices fail.</p>"
    body += "<h2>Review the related lessons</h2><ul>" + "".join(
        '<li><a href="/' + target + '">' + html.escape(by_path[target]["title"]) + "</a></li>"
        for target in targets) + "</ul>"
    body += "<h3>Common Mistakes</h3><p>A browser quiz cannot verify a deployed service or an unfamiliar spreadsheet. Run the linked programs against your own boundary.</p>"
    row = copy.deepcopy(by_path["quizzes/python-boundary-contracts"])
    row.update(id=str(uuid.uuid5(uuid.NAMESPACE_URL, "https://aitrove.in/" + path)),
               path=path, title=title,
               summary="Twelve explained checks on Python concurrency, storage, I/O and algorithm contracts.",
               body=body, tags=["python", "quiz", "contracts"],
               sort_order=7400 + len(rows), published_at=stamp, created_at=stamp, updated_at=stamp)
    row["data"]["questions"] = [question(*values, index % 3) for index, values in enumerate(raw_questions)]
    rows.append(row)
    by_path[path] = row
    hub = by_path["python/quizzes"]
    hub["data"]["modules"][-1]["lessons"].append(path)
    hub["body"] = hub["body"].replace("</ul><h2>Continue learning</h2>",
        '<li><a href="/' + path + '">' + html.escape(title) + "</a></li></ul><h2>Continue learning</h2>")
    for parent in ("python/python-programming-language-tutorial", targets[0]):
        host = by_path[parent]
        host["body"] += '<p><a href="/' + path + '">Test this contract in the ' + html.escape(title) + "</a>.</p>"

fixture.write_text(json.dumps(rows, ensure_ascii=False, indent=2) + "\n")
print("Added", len(banks), "Python quiz banks")
