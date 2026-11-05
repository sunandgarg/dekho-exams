"""Add checked Data Structures deletion, priority, hashing, and graph lessons."""

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
        "path": "dsa/bplus-deletion-borrow-merge",
        "program": "bplus_delete.py",
        "title": "B+ deletion: borrow, merge, and repair separators",
        "summary": "Remove leaf keys while maintaining page occupancy, separator routing, and linked scans.",
        "section": "dsa/trees-and-heaps",
        "definition": "A B+ deletion removes a data key from a leaf. If that leaf falls below its minimum occupancy, a sibling can lend a key; otherwise adjacent siblings merge and their parent loses a child. An internal page can then underflow in turn, so repair must continue toward the root. The root can contract to its only child. This small model caps pages at three keys, requires two keys in a nonroot leaf and two children in a nonroot internal page, and stores data keys only in leaves. Internal separators equal the smallest key in each right child. Every leaf remains at the same depth, and the linked leaf chain must skip a removed page after a merge. The model handles unique integer keys and in-memory single-writer updates; it is not a storage engine.",
        "case": "An inventory index first inserts bay IDs 47, 52, 61, 19, 26, 58, 83, 31, 67, and 73. It then removes 19, 26, 31, 47, 52, and 58. Some removals leave a page too small, forcing a borrow or merge; enough merges can reduce tree height. The final leaf walk reports 61, 67, 73, and 83. A removal of 49 reports false because that key was never stored, and a lookup of 61 still succeeds. A test that checks only the final scan is weak: stale separators may send point lookups to the wrong leaf, while an incorrect leaf link may omit keys despite correct child pointers.",
        "cost": "Let h be tree height and c the page capacity. The path to a leaf and the upward rebalance visit O(h) structural levels, while Python list shifts and sibling merges cost O(c) per touched page. This teaching program recomputes each separator by descending to a child's leftmost leaf; repeated refreshes can cost O(c h squared) CPU in the worst case. A page implementation with maintained minimum-key metadata or precise local separator updates can avoid that extra descent. The tree stores O(n) keys and references, and the explicit ancestor path costs O(h) space. Disk I/O, latching, write-ahead logging, and crash recovery are outside this program's contract.",
        "mistakes": ["Do not remove a leaf without relinking its predecessor to the next leaf.", "Do not repair a leaf but leave a parent with too few children.", "Do not retain a root that has one child and no useful separator.", "Do not present this in-memory page model as durable database deletion."],
        "related": ["dsa/bplus-multilevel-insertion", "dsa/btree-page-split-insertion", "dsa/index-mutation-invariants-project"],
    },
    {
        "path": "dsa/indexed-binary-heap-decrease-key",
        "program": "indexed_heap.py",
        "title": "Indexed binary heaps: decrease a queued priority",
        "summary": "Maintain a job-to-position map while priorities rise through a min-heap.",
        "section": "dsa/trees-and-heaps",
        "definition": "A binary heap keeps the minimum priority at index zero and each parent no larger than either child. A plain heap does not identify the array position of an arbitrary queued job. An indexed heap adds a map from job ID to array position; every swap updates both entries in that map. Decreasing one job's priority can then find its current index and rise it toward the root instead of scanning the entire heap. This program uses a pair of priority and job ID to break equal-priority ties consistently. It rejects duplicate IDs and increases through the decrease operation. It does not implement cancellation, an arbitrary priority increase, worker execution, or persistence.",
        "case": "A dispatch queue starts with J-47 at priority 9, J-52 at 6, J-61 at 12, and J-83 at 7. A control-plane update changes J-61 to priority 3. The map finds J-61 directly; swaps move it above its parent while keeping all recorded positions current. The first removal therefore returns J-61 at 3, followed by J-52 at 6. A stale position map is a latent fault: a later decrease may edit a different job even when the heap's root happened to look correct just after one operation. Tests should inspect the map and heap invariant after every mutation.",
        "cost": "With n queued jobs, add, decrease, and pop move along at most O(log n) heap levels. Position lookup is expected O(1) for a well-behaved hash map, so decrease is expected O(log n) time; pathological hash collisions can change that assumption. Reading the minimum is O(1) if the heap is nonempty. The array and position map each use O(n) space. Equal priorities are ordered by job ID in this example, which is not submission order. If stable arrival order matters, store a monotonic sequence number as a separate tie-break field and keep its value unchanged across decreases.",
        "mistakes": ["Do not swap heap entries without updating both job positions.", "Do not assume equal priorities preserve arrival order when job IDs break ties.", "Do not call a higher numeric priority a decrease in this min-heap.", "Do not claim the queue executes, acknowledges, or durably stores jobs."],
        "related": ["dsa/binary-heap-priority-scheduling", "dsa/graph-adjacency-list-and-bfs", "dsa/bounded-thread-queue-acknowledgment"],
    },
    {
        "path": "dsa/open-addressing-tombstones-rehash",
        "program": "open_address_delete.py",
        "title": "Open-addressed hash tables: tombstones and rebuilds",
        "summary": "Preserve a linear-probing search chain after deletion and reclaim dead slots.",
        "section": "dsa/hash-tables",
        "definition": "Linear probing stores a key-value pair in an array slot found by walking forward from its hash position. Lookup stops at a truly empty slot; a deleted slot cannot be made empty if later colliding keys might lie beyond it. A tombstone marks that slot as available for later insertion while telling lookup to keep probing. This example tracks live entries and tombstones separately and rebuilds the table when occupied or formerly occupied slots approach its load threshold. A rebuild reinserts live entries and removes tombstones. It accepts nonnegative integer bay IDs; this simple modulo hash is intentionally transparent and vulnerable to clustered or adversarial IDs.",
        "case": "With eleven initial slots, bay IDs 47, 58, and 69 all start at the same remainder and form a probe run. Deleting 47 must not hide 58 or 69. The program prints successful lookups for both survivors, then inserts bay 80 and checks that it can be found while 47 remains absent. A tombstone can be reused, but a search for an existing key must continue past earlier tombstones before insertion decides where to write. If enough tombstones collect, even unsuccessful lookups walk long runs until the table is rebuilt.",
        "cost": "Lookup, insertion, and deletion are expected O(1) only under a suitable key distribution and controlled effective load; colliding keys make a single operation O(n) in the table size. A rebuild is O(n) and can pause a writer, though geometrically growing capacity gives amortized expected constant insertion work under typical distributions. The array uses O(n) slots relative to stored entries at the chosen load policy. This implementation treats a missing result as a found boolean plus value, so a stored None value is distinguishable from absence. It is single-threaded and does not use a cryptographic or universal hash function.",
        "mistakes": ["Do not replace a deleted slot with a truly empty slot inside a collision chain.", "Do not insert into the first tombstone before checking for an existing copy of the key later in the run.", "Do not measure load using only live entries when tombstones are numerous.", "Do not promise O(1) worst-case lookup for colliding integer IDs."],
        "related": ["dsa/hash-map-collision-and-load-contract", "dsa/hash-set-membership-and-order", "dsa/sparse-set-bounded-identifiers"],
    },
    {
        "path": "dsa/dependency-graph-topological-order",
        "program": "dependency_topology.py",
        "title": "Dependency graphs: topological order and cycle rejection",
        "summary": "Use incoming-edge counts to run prerequisites first and reject circular work plans.",
        "section": "dsa/graphs-and-disjoint-sets",
        "definition": "A directed dependency graph puts an edge from each prerequisite to the task that needs it. A topological order lists every task only after its prerequisites. Incoming-edge counts make the condition explicit: tasks with count zero are ready; removing one ready task reduces the counts of its dependents. If the queue becomes empty before all tasks are emitted, at least one directed cycle prevents a complete order. This program deduplicates repeated prerequisite names, rejects names missing from the task map, and raises on a cycle. It returns one valid order, not the only possible order and not an execution schedule with resource constraints.",
        "case": "A warehouse plan stocks inventory, reserves it, picks and packs goods, prints a label, then ships. Shipping depends on both pack and label. The shown input yields stock, reserve, pick, label, pack, ship; swapping independent pick and label can still be valid. A second plan makes receive depend on audit and audit depend on receive. Neither can reach incoming count zero, so the method reports a dependency cycle instead of returning a partial plan as if it were complete. A production planner might report the specific cycle and isolate affected tasks, which requires an additional traversal.",
        "cost": "Building successor lists and incoming counts takes O(V + E) expected time for V tasks and E distinct prerequisite edges, and the queue removes each task once while scanning each edge once. The graph, counts, queue, and result use O(V + E) space. Hash-map operations are assumed expected O(1). This implementation preserves the task insertion order among initially ready tasks and follows dependent insertion order, but that is only a deterministic tie policy for a fixed input map. Changing the input order can change the valid result. Topological order alone says nothing about durations, parallel capacity, retries, or durable job completion.",
        "mistakes": ["Do not reverse the prerequisite edge and accidentally run dependent work first.", "Do not return a partial ordering as success when a cycle remains.", "Do not count a repeated prerequisite twice while storing only one edge.", "Do not treat a valid order as a full scheduler or a proof that jobs completed."],
        "related": ["dsa/graph-adjacency-list-and-bfs", "dsa/disjoint-set-union-connectivity", "dsa/bounded-thread-queue-acknowledgment"],
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
                 body=body, sort_order=41000 + order * 10, created_at=stamp, updated_at=stamp, published_at=stamp)
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
