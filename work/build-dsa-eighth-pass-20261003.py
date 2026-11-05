"""Add online, shared-index, journal, and queue-protocol lessons to local fixtures."""

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
        "path": "dsa/online-connectivity-after-edge-removal",
        "program": "online_connectivity.py",
        "title": "Online connectivity: answer after each edge change",
        "summary": "Maintain live adjacency sets and search the current graph after additions or deletions.",
        "section": "dsa/graphs-and-disjoint-sets",
        "definition": "Online connectivity answers a question against the graph that exists now, without knowing future edge changes. An undirected adjacency set gives an exact baseline: adding or removing an edge updates both endpoints, and a breadth-first search answers whether two depots share a path. This is deliberately a single-writer structure. A disjoint-set union can absorb additions cheaply but cannot reverse an arbitrary bridge deletion; the search recomputes reachability instead of pretending the old component partition is still valid. Duplicate adds and absent removals are errors, making the update contract observable rather than silently hiding a caller mistake.",
        "case": "D-19 is connected to D-26, while D-47 starts isolated. The first question is false. Adding D-26 to D-47 makes the second question true; deleting that same edge makes the third false. A single removed edge can split a component, or it can leave an alternate route intact. The search detects either case from the remaining adjacency sets. This immediate-answer contract differs from an event batch whose future additions, deletions, and questions are all known before processing begins.",
        "cost": "An add or remove performs expected O(1) hash-set work per endpoint and stores O(V + E) adjacency entries for V depots and E undirected edges. Each connectivity question takes O(V + E) time in the worst case and O(V) temporary space for the queue and visited set. The baseline is sensible when updates are common but questions are modest, or when correctness is more valuable than a complex update structure. High-query workloads can justify fully online connectivity machinery, but its replacement-edge search and amortized bounds require a separate, much larger implementation. This program does not supply thread safety or distributed agreement.",
        "mistakes": ["Do not leave the reverse adjacency entry behind when deleting an undirected edge.", "Do not use a union-only component cache after deleting a possible bridge.", "Do not treat a repeated add or missing-edge removal as a harmless no-op without specifying that policy.", "Do not quote amortized bounds for an advanced online structure as the cost of this breadth-first search."],
        "related": ["dsa/graph-adjacency-list-and-bfs", "dsa/disjoint-set-union-connectivity", "dsa/offline-connectivity-edge-lifetimes"],
    },
    {
        "path": "dsa/persistent-ordered-index-path-copying",
        "program": "persistent_order_index.py",
        "title": "Persistent ordered indexes: copy search paths, share subtrees",
        "summary": "Keep older ordered-map roots alive while insertion and deletion create new roots.",
        "section": "dsa/trees-and-heaps",
        "definition": "A persistent ordered index returns a new root for each edit while old roots remain valid. This immutable treap stores a search key, owner, random priority, and child references in each node. Split and merge rebuild only nodes on traversed paths; untouched subtrees are reused by identity. A new version can delete a key without deleting it from an earlier version. The binary-search ordering supports lookup and ordered traversal; the priority ordering gives expected balanced height when priorities are independent random values. Randomization is an expected-cost assumption, not a worst-case height guarantee.",
        "case": "Version one contains asset 47 owned by North. Version two adds asset 61 owned by East. Version three removes 47, so its ordered output contains only 61; version one still contains 47. A fourth version branches from version two by adding 83, and its untouched left subtree is the identical node used by version two. A caller can hold any root as a point-in-time view. Node immutability makes sharing safe. A mutable owner object stored inside a frozen node would still let old versions appear to change, so the shown owners are immutable strings.",
        "cost": "Find takes expected O(log N) time for N keys. Split, merge, insertion, and deletion copy O(log N) nodes in expectation and take expected O(log N) time; an unlucky priority order can make any of them O(N). Across K versions, total retained memory is the initial tree plus nodes copied by edits, not a full O(N) map copy per version. The shown ordered traversal builds a list with O(N) time and O(N) output space; Python recursion also uses height-proportional stack space. Production systems need a rule for priority generation, recursion limits, version retention, and garbage collection. This structure is in memory, not a disk index.",
        "mistakes": ["Do not mutate an old node while creating a new version.", "Do not promise worst-case logarithmic time for random-priority balancing.", "Do not mistake a frozen node for deep immutability of objects referenced by its fields.", "Do not retain every historical root forever without a storage budget."],
        "related": ["dsa/persistent-segment-tree-versioned-sums", "dsa/immutable-index-snapshot-publication", "dsa/binary-search-tree-order-invariant"],
    },
    {
        "path": "dsa/framed-journal-torn-tail-recovery",
        "program": "framed_commit_journal.py",
        "title": "Framed journals: detect a torn tail before replay",
        "summary": "Write one bounded transaction frame, sync it, and replay only complete prefix records.",
        "section": "dsa/trees-and-heaps",
        "definition": "A framed append journal stores each transaction as a length, checksum, and complete payload. This single-writer example puts all page replacements for one transaction into one frame, writes it to an existing file, then calls fsync before acknowledging the append. Recovery scans a contiguous valid prefix. A short final header or payload represents a torn tail and is truncated before another append; a full frame with a bad checksum raises for manual recovery instead of silently discarding potentially committed records after it. A recovered map is rebuilt solely from complete validated frames. The example does not write separate data pages, so it needs no undo for uncommitted page contents.",
        "case": "The first complete frame replaces P-19 and creates P-26. Eleven bytes of a later frame for P-52 are injected without a complete payload. Recovery yields P-19 and P-26, removes the incomplete tail, and leaves P-52 absent. The demonstration controls byte truncation; it does not simulate a real power cut or prove the storage device honored its flush request. A transaction frame that is fully present and checksum-valid may still have been written without a successful fsync in another failure schedule, so acknowledgment and replay policy must be defined together.",
        "cost": "Encoding a transaction with B payload bytes takes O(B) time and space; appending writes O(B) bytes and pays a storage-dependent fsync latency. Recovery scans O(L) bytes for a journal of length L and stores O(P) latest page values plus one bounded record buffer, where P is the number of distinct pages. Replaying the entire file on startup grows with history until a separately designed checkpoint is added. CRC detects many accidental corruptions but is not an authentication code and cannot repair data. The model assumes one writer, an existing durable filename, a file system with meaningful fsync behavior, and no concurrent reader that races truncation. It is a small disk-backed journal, not a complete database transaction engine.",
        "mistakes": ["Do not acknowledge a frame before checking that its write and fsync succeeded.", "Do not skip over a checksum failure in the middle and silently apply later records.", "Do not append new frames behind a torn tail before recovery trims that tail.", "Do not claim that CRC or fsync alone guarantees safety against every hardware fault or directory-entry loss."],
        "related": ["dsa/page-redo-journal-recovery-model", "dsa/bplus-multilevel-insertion", "dsa/immutable-index-snapshot-publication"],
    },
    {
        "path": "dsa/cas-queue-link-help-and-reclamation",
        "program": "cas_queue_schedule.py",
        "title": "CAS queue protocol: link, help, and reclaim safely",
        "summary": "Trace failed stale comparisons and tail helping before choosing an atomic implementation.",
        "section": "dsa/stacks-and-queues",
        "definition": "A linked multiple-producer, multiple-consumer queue can use a dummy head, a tail pointer, and compare-and-swap operations to coordinate insertion and removal. Enqueue first links a new node after the observed tail, then tries to advance tail. Another participant may help advance a lagging tail. Dequeue reads the successor of the dummy head, helps tail if needed, and advances head to claim the next item. This Python program is a sequential schedule model: its comparison methods are ordinary Python checks and assignments, not atomic instructions. It demonstrates state transitions and a stale-link failure; it cannot be called a concurrent lock-free queue.",
        "case": "One simulated participant remembers the initial tail. A completed offer links J-47, changing that tail node's successor. The remembered attempt to link a different node with the old expected successor returns false. J-61 follows, and two takes return J-47 then J-61 before empty returns None. A real implementation must make every shared-pointer comparison atomic, define memory ordering, and prevent a removed node from being freed or reused while another participant still holds its address. An address reused too early can make a stale comparison appear valid again; tagging or managed reclamation addresses that separate boundary.",
        "cost": "The model's successful link and head moves each take O(1) local operations, but loops may retry and there is no bound on one participant's completion time. A proven lock-free implementation argues system-wide progress under its atomic and reclamation assumptions; this sequential Python model proves no such property. Space is O(Q + R) for Q queued nodes and R nodes retained after removal in this model, because it never reclaims nodes. Actual memory reclamation, ABA protection, close semantics, and platform-specific atomic support can dominate an implementation review. Use the condition-protected queue when a working in-process Python buffer is the requirement.",
        "mistakes": ["Do not call a sequence of Python equality checks and assignments atomic CAS.", "Do not free or recycle a removed node while another participant may still read it.", "Do not assume moving tail is the insertion linearization point; linking the node makes it reachable.", "Do not equate lock-free system progress with wait-free completion for each caller."],
        "related": ["dsa/bounded-queue-close-and-drain", "dsa/bounded-thread-queue-acknowledgment", "dsa/queue-fifo-deque-boundary"],
    },
]

for order, lesson in enumerate(lessons):
    path, section = lesson["path"], lesson["section"]
    assert path not in by_path
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
        + "<h3>Common Mistakes</h3><ul>" + "".join("<li>" + html.escape(item) + "</li>" for item in lesson["mistakes"]) + "</ul>"
        + "<h2>Connected lessons</h2><ul>" + "".join('<li><a href="/' + related_path + '">' + html.escape(by_path[related_path]["title"]) + "</a></li>" for related_path in related_paths) + "</ul>"
    )
    entry = copy.deepcopy(by_path["dsa/fenwick-tree-point-update-prefix-query"])
    entry.update(id=str(uuid.uuid5(uuid.NAMESPACE_URL, "aitrove:" + path)), path=path, title=lesson["title"], summary=lesson["summary"],
                 body=body, sort_order=41300 + order * 10, created_at=stamp, updated_at=stamp, published_at=stamp)
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
