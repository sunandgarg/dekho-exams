"""Publish checked connectivity, queue, snapshot, and journal lessons."""

import copy
import datetime
import html
import json
import subprocess
import sys
import uuid
from pathlib import Path

root = Path(__file__).resolve().parents[1]
fixture = root / "src/data/fixtures.json"
entries = json.loads(fixture.read_text())
by_path = {entry["path"]: entry for entry in entries}
subject_root = "dsa/dsa-tutorial-learn-data-structures-and-algorithms"
stamp = datetime.datetime.now(datetime.UTC).isoformat()

lessons = [
    {
        "path": "dsa/offline-connectivity-edge-lifetimes",
        "program": "offline_connectivity.py",
        "title": "Offline connectivity: edge lifetimes and rollback unions",
        "summary": "Place active edge intervals on a time tree and restore connectivity after each branch.",
        "section": "dsa/graphs-and-disjoint-sets",
        "definition": "A rollback disjoint-set can undo recent unions but cannot remove one arbitrary active edge while preserving later changes. If all add, remove, and connectivity questions are known in advance, convert each edge's active span into a half-open interval on the event timeline. A segment tree over time stores that edge in nodes whose ranges fit inside its span. A depth-first walk unions each node's edges, answers questions at leaves, then rolls back to the checkpoint held before entering the node. The resulting connectivity at a query time contains exactly the edges active at that time. This program rejects duplicate adds, removing an absent edge, unknown depots, self-edges, and unknown actions. It is an offline batch algorithm, not a live graph service.",
        "case": "The event stream adds D-19 to D-26, asks whether D-19 reaches D-47, adds D-26 to D-47, asks again, removes that second edge, and asks a third time. The answers are false, true, false. The first edge spans the whole timeline after its addition; the second spans only the interval before removal. Each active interval is attached to O(log Q) time-tree nodes for Q events. The traversal can restore the disjoint-set state after evaluating an earlier time branch without rebuilding the graph from zero for each question. Event order matters: an edge added at position i is active for later questions until its removal event.",
        "cost": "For V depots, Q events, and I edge-active intervals, placing intervals costs O(I log Q) time and stored references. With union by size and no path compression, find and union cost O(log V), so a conservative total is O(Q + (I log Q + A) log V), where A is the number of questions. The segment tree, events, answers, and stored intervals use O(Q + I log Q) space; disjoint-set arrays and active rollback history add O(V + I) on a single traversal path. The model assumes a fixed depot set and one active copy of each undirected edge. Parallel edges, online arrival, and persistence need separate contracts.",
        "mistakes": ["Do not remove one DSU edge directly and assume other unions remain valid.", "Do not leave an edge active beyond its removal position in the time tree.", "Do not use path compression without recording every parent change for rollback.", "Do not call an offline batch answer a live update API."],
        "related": ["dsa/disjoint-set-rollback-checkpoints", "dsa/disjoint-set-union-connectivity", "dsa/graph-adjacency-list-and-bfs"],
    },
    {
        "path": "dsa/bounded-queue-close-and-drain",
        "program": "closing_work_queue.py",
        "title": "Bounded queues: close, wake waiters, and drain accepted work",
        "summary": "A condition-protected FIFO rejects new work after closure and wakes blocked threads.",
        "section": "dsa/stacks-and-queues",
        "definition": "A bounded FIFO queue can block producers when full and consumers when empty. Closing it needs an explicit state transition: reject any later offer, wake producers waiting for space, and let consumers drain work already accepted before returning a closed signal. This implementation guards a deque and closed flag with one condition variable. Waits occur inside while loops because waking does not guarantee the desired condition still holds. None is reserved as the drained-and-closed result. The example is a thread-safe in-process buffer with a single queue state; it is not a lock-free queue, a durable message broker, or a task-completion tracker.",
        "case": "A two-slot intake accepts J-47 and J-52. A nonblocking offer of J-61 reports false while the queue is full. Closing intake leaves the two accepted jobs in FIFO order: take returns J-47, then J-52, then None. Offering J-83 after closure raises QueueClosed. In a threaded run, a producer blocked on a full queue wakes when close broadcasts the state change and raises instead of waiting forever. A consumer blocked on an empty queue also wakes and sees the drained signal. Draining is a policy choice; discarding accepted work would need a different documented shutdown path.",
        "cost": "Appending and removing from the deque are O(1) while the lock is held. A full producer or empty consumer can wait for an unbounded wall-clock time until another thread changes state or close wakes it. The buffer uses O(C) space for capacity C, plus condition-waiter bookkeeping owned by the runtime. Close itself changes state in O(1) and broadcasts to waiting threads; waking many threads has scheduling cost outside a constant-time queue-operation claim. A taken job is merely removed from memory. If processing fails afterward, this structure has no retry record, acknowledgment, or crash recovery.",
        "mistakes": ["Do not use an if check before wait; recheck the queue state after every wake.", "Do not close without waking blocked producers and consumers.", "Do not treat queue removal as proof that a worker completed its job.", "Do not call a condition-variable queue lock-free or persistent."],
        "related": ["dsa/bounded-thread-queue-acknowledgment", "dsa/ring-buffer-capacity-and-wrap", "dsa/queue-fifo-deque-boundary"],
    },
    {
        "path": "dsa/immutable-index-snapshot-publication",
        "program": "index_snapshot_publication.py",
        "title": "Index snapshots: publish related maps as one in-memory version",
        "summary": "Copy two maps, validate their relationship, then swap one immutable snapshot pointer.",
        "section": "dsa/hash-tables",
        "definition": "Readers can observe a consistent pair of related indexes if a writer builds both replacements privately and publishes one snapshot only after validation. This program copies a bay-owner map and repair-window map under a lock, removes retired bays from both, applies additions, checks that every window belongs to an existing bay, and swaps one current-snapshot reference. A reader acquires the lock briefly to capture that reference, then can inspect immutable mapping views after the lock is released. Existing readers retain the prior snapshot. The sample values are immutable strings and interval tuples; a shallow mapping view would not freeze a mutable value object stored inside either map.",
        "case": "Version 1 contains bays 47 and 52, with [19, 26) booked at 47. A release retires 47 and adds bay 61 with [47, 58). The old snapshot still reports version 1 and its bay 47 window; the newly returned snapshot reports version 2 and bays 52 and 61. A caller supplies the version it planned against. If another writer has published since then, the operation raises rather than silently overwriting that later change. Invalid orphan windows also fail before the pointer changes. The lock makes one in-process publication coherent, but no data has been written durably.",
        "cost": "With B bay entries and W windows, each publication copies and validates O(B + W) entries and temporarily uses O(B + W) additional memory. Retaining multiple versions costs that amount per full copied version, unlike a path-copying persistent tree that shares untouched structure. Reading the current snapshot takes O(1) lock-protected pointer work; individual dictionary lookups are expected O(1) with normal hashing. The writer holds the same lock during copying and validation, so large indexes delay readers. This is one-process visibility, not disk durability, cross-process transactions, or a lock-free design.",
        "mistakes": ["Do not publish one map before the matching map is validated.", "Do not assume a mapping view recursively freezes mutable values.", "Do not ignore an expected-version mismatch from a stale writer.", "Do not equate in-memory atomic visibility with crash-safe persistence."],
        "related": ["dsa/hash-map-collision-and-load-contract", "dsa/persistent-segment-tree-versioned-sums", "dsa/index-mutation-invariants-project"],
    },
    {
        "path": "dsa/page-redo-journal-recovery-model",
        "program": "page_redo_journal.py",
        "title": "Page journals: replay committed index changes",
        "summary": "Keep ordered page records and apply only transactions with a commit marker during replay.",
        "section": "dsa/trees-and-heaps",
        "definition": "A page-index update may touch several pages. An ordered redo journal can group proposed page contents by transaction ID and make replay apply a group only after its commit marker appears. This teaching model stores begin, page, and commit records in a list. Recovery starts from a checkpoint page map, accumulates pending page changes, and applies those changes when it reads a matching commit. A transaction ending without commit is ignored. The model deliberately keeps every record and page in memory; it does not perform a disk flush, validate a torn record, undo an uncommitted page already written to storage, or guarantee atomicity of a physical commit marker.",
        "case": "A committed page change rewrites P-19 as rebalanced and introduces P-26 as a new leaf. A later proposed split for P-52 has no commit record, representing an interrupted operation. Replay returns only P-19 and P-26 from the committed group. It does not manufacture P-52. The order of records is part of the structure: a page record without its begin or a commit without its begin raises. In a real storage engine, log durability must precede publishing dirty index pages, and recovery policy must account for any uncommitted changes that reached disk. This small replay model assumes they did not.",
        "cost": "For R journal records and P checkpoint pages, replay scans O(R) records and copies O(P) pages; applying page updates costs O(U) for U committed update records, already bounded by R. The in-memory journal and pending transaction maps use O(R) additional space in the worst case, while the recovered page map uses O(P + U) entries. A production implementation needs durable write ordering, checksums or equivalent record validation, truncation or checkpointing, concurrency control, and an undo or no-steal policy consistent with its page-flush rules. This example establishes a replay invariant, not a database durability guarantee.",
        "mistakes": ["Do not apply an uncommitted page record during redo-only recovery.", "Do not flush uncommitted data pages and assume this model can undo them.", "Do not claim a Python list models durable ordered writes or torn-record detection.", "Do not reuse transaction IDs in one untrimmed journal without a generation rule."],
        "related": ["dsa/bplus-deletion-borrow-merge", "dsa/bplus-multilevel-insertion", "dsa/immutable-index-snapshot-publication"],
    },
]

assert all(lesson["path"] not in by_path for lesson in lessons)
for order, lesson in enumerate(lessons):
    path, section = lesson["path"], lesson["section"]
    source = root / "work/dsa-programs" / lesson["program"]
    program = source.read_text().rstrip()
    output = subprocess.run([sys.executable, str(source)], check=True, capture_output=True, text=True).stdout.strip()
    related_paths = [section, subject_root, *lesson["related"], "dsa/projects", "dsa/quizzes"]
    body = (
        "<p>" + html.escape(lesson["definition"]) + "</p>"
        + "<h2>Operational case</h2><p>" + html.escape(lesson["case"]) + "</p>"
        + '<h2>Working Python program</h2><pre><code class="language-python">' + html.escape(program, quote=False) + "</code></pre>"
        + '<h3>Output</h3><pre><code class="language-text">' + html.escape(output) + "</code></pre>"
        + "<h2>Time, space, and tradeoff</h2><p>" + html.escape(lesson["cost"]) + "</p>"
        + "<h3>Common Mistakes</h3><ul>" + "".join("<li>" + html.escape(mistake) + "</li>" for mistake in lesson["mistakes"]) + "</ul>"
        + "<h2>Connected lessons</h2><ul>" + "".join('<li><a href="/' + related_path + '">' + html.escape(by_path[related_path]["title"]) + "</a></li>" for related_path in related_paths) + "</ul>"
    )
    entry = copy.deepcopy(by_path["dsa/fenwick-tree-point-update-prefix-query"])
    entry.update(id=str(uuid.uuid5(uuid.NAMESPACE_URL, "aitrove:" + path)), path=path, title=lesson["title"], summary=lesson["summary"],
                 body=body, sort_order=41200 + order * 10, created_at=stamp, updated_at=stamp, published_at=stamp)
    entry["data"].update(section_path=section, related=[{"path": related_path, "title": by_path[related_path]["title"]} for related_path in related_paths])
    entries.append(entry)
    by_path[path] = entry
    for hub_path in (section, subject_root):
        hub = by_path[hub_path]
        module = hub["data"]["modules"][0] if hub_path == section else next(module for module in hub["data"]["modules"] if module["title"] == by_path[section]["title"])
        module["lessons"].append(path)
        hub["body"] += '<p><a href="/' + path + '">' + html.escape(lesson["title"]) + "</a></p>"
        hub["updated_at"] = stamp

fixture.write_text(json.dumps(entries, ensure_ascii=False, indent=2) + "\n")
print(json.dumps({"addedLessons": len(lessons), "paths": [lesson["path"] for lesson in lessons]}))
