"""Publish checked red-black, interval, rollback, and shortest-path lessons."""

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
        "path": "dsa/red-black-ordered-deletion",
        "program": "red_black_delete.py",
        "title": "Red-black deletion: move color before removing a key",
        "summary": "Maintain left-leaning red links and equal black height during ordered deletion.",
        "section": "dsa/trees-and-heaps",
        "definition": "Removing a key from a left-leaning red-black tree must preserve search order, left-leaning red links, no adjacent red links, and equal black height along every root-to-null path. A top-down deletion can move a red link into the child about to be visited, preventing descent into an unrepairable two-node. On the return path, local rotations and color changes restore the representation. When the target has two children, the smallest key in its right subtree replaces it, and that successor is removed from its old location. This program supports unique integer keys, checks whether the key exists before mutation, and blackens the root at the end. It is an in-memory single-writer index; it does not implement persistent snapshots or concurrent readers.",
        "case": "A scheduler inserts deadlines 47, 52, 61, 19, 26, 58, and 83. It removes 26, then 47, then 83. The remaining ordered keys are 19, 52, 58, and 61. The audit checks that both branches below each node have the same black height, no red edge leans right, no red node has a red left child, and descendants respect key bounds. A sorted traversal by itself would miss color damage, so a mutation test needs both content and structure checks. Removing a deadline that does not exist returns false without recoloring the tree.",
        "cost": "The red-black height is O(log n) when the invariants hold. The existence check and deletion each follow at most one root-to-leaf path with bounded local repairs per level, so a successful or absent-key removal takes O(log n) time. Recursive deletion uses O(log n) stack space; n nodes occupy O(n) tree space. The demonstration's full audit traverses every node and costs O(n), outside ordinary removal. This implementation uses Python assertions for that teaching audit; production invariant tests should use checks that cannot be disabled. A payload-bearing index would also need to move the successor's payload with its key.",
        "mistakes": ["Do not remove a black leaf without preparing the descent or restoring black height.", "Do not replace a key with its successor while leaving the successor in its original location.", "Do not treat a sorted walk as proof of color and black-height correctness.", "Do not forget to blacken the root after top-down deletion."],
        "related": ["dsa/red-black-ordered-insertion", "dsa/red-black-tree-invariant-audit", "dsa/bplus-deletion-borrow-merge"],
    },
    {
        "path": "dsa/avl-interval-index-deletion",
        "program": "avl_interval_delete.py",
        "title": "AVL interval deletion: repair balance and maximum endpoints",
        "summary": "Remove an exact half-open interval and refresh augmented metadata after rotations.",
        "section": "dsa/trees-and-heaps",
        "definition": "An AVL interval index orders windows by their (start, end) pair and stores both subtree height and maximum end at each node. Deleting an exact interval can shorten one branch, so the return path must recompute both fields and rotate any unbalanced node. A two-child target uses the smallest pair from its right subtree as a successor; that successor is then removed from its original position. Unlike insertion repair, deletion chooses a double rotation from the remaining child's balance, since the removed key does not identify the taller grandchild. The overlap query still prunes a left subtree whose maximum end cannot cross the query's low boundary. This program removes one exact pair, not every overlapping window.",
        "case": "A maintenance calendar stores [47, 61), [19, 26), [52, 58), [83, 91), and [31, 42). Removing [19, 26) reports success. The query [25, 30) now has no overlap, while [62, 80) remains clear. After repair, the root height is three and the maximum endpoint remains 91. The latter matters: if deletion leaves a stale maximum endpoint, pruning can skip a branch that actually contains a matching interval, or needlessly visit an irrelevant branch. Repeating the same exact deletion should report false and leave the tree unchanged.",
        "cost": "AVL height stays O(log n), so exact-key deletion and one-overlap search take O(log n) time. The recursive delete path uses O(log n) extra stack space, and stored nodes use O(n) space. Updating height and maximum end is constant work at each visited node; a rotation touches a bounded number of nodes. Returning k overlaps would need a different traversal and at least O(k) output work. These intervals are half-open: [19, 26) and [26, 31) only touch and do not overlap. The code does not count duplicate identical bookings or coordinate concurrent writers.",
        "mistakes": ["Do not refresh height while leaving max-end metadata from the old child arrangement.", "Do not select a deletion rotation using the removed key's direction alone.", "Do not call a touching half-open endpoint an overlap.", "Do not describe exact-pair removal as removal of every conflicting booking."],
        "related": ["dsa/avl-interval-index-insertion", "dsa/interval-tree-max-endpoint-pruning", "dsa/avl-rotation-height-invariant"],
    },
    {
        "path": "dsa/disjoint-set-rollback-checkpoints",
        "program": "rollback_connectivity.py",
        "title": "Disjoint-set rollback: restore an earlier connectivity checkpoint",
        "summary": "Keep union changes on a stack so a temporary bridge can be undone.",
        "section": "dsa/graphs-and-disjoint-sets",
        "definition": "A rollback disjoint-set structure groups connected vertices while recording every successful union's parent and size changes. A checkpoint is the current history length. Rolling back pops changes until that length is restored. Union by size bounds tree height without path compression; compressing paths during find would change many parents that this short history does not record. A union of already connected vertices changes no state and adds no history entry. This program supports checkpointed unions in one mutable timeline. It does not remove an arbitrary historical edge while keeping later unrelated unions; that requires an offline interval scheme or a different connectivity structure.",
        "case": "Depots D-19 and D-26 are joined permanently for this local scenario. A checkpoint is taken. A proposed bridge joins D-26 to D-47, making D-19 and D-47 connected. Rolling back to the checkpoint removes that temporary connectivity while preserving the D-19 to D-26 union. The printed result first reports true, then false and true. A caller should use checkpoints in a stack-like exploration: a saved integer alone cannot distinguish a stale token from a later branch that happens to have the same history length after rollback and new unions.",
        "cost": "Without path compression, union by size gives O(log n) worst-case find and union for n depots. A checkpoint is O(1). Rolling back u successful unions takes O(u) time, with O(1) restore work per recorded change. Parent and size maps use O(n) space, and the history uses O(u) space since the oldest retained checkpoint. The code assumes a fixed depot set and a single writer. A fully changing graph with edge lifetimes can pair rollback DSU with an offline time-interval decomposition, but that scheduling layer is not implemented here.",
        "mistakes": ["Do not enable unrecorded path compression and expect rollback to restore every parent.", "Do not record a redundant union as a connectivity change.", "Do not treat a history-length token as a durable cross-process version.", "Do not claim this method supports arbitrary online edge removal."],
        "related": ["dsa/disjoint-set-union-connectivity", "dsa/dependency-graph-topological-order", "dsa/graph-adjacency-list-and-bfs"],
    },
    {
        "path": "dsa/stale-entry-heap-shortest-route",
        "program": "stale_heap_shortest_path.py",
        "title": "Shortest routes: skip stale min-heap entries",
        "summary": "Run Dijkstra on nonnegative roads without an indexed decrease-key operation.",
        "section": "dsa/graphs-and-disjoint-sets",
        "definition": "Dijkstra's algorithm repeatedly settles the currently shortest tentative route when every edge weight is nonnegative. A standard min-heap does not update an existing entry in place. This version pushes a new (distance, depot) pair after an improvement and leaves the old pair in the heap. When an old pair surfaces, its distance differs from the best recorded distance and it is skipped. A predecessor map reconstructs one route after the destination is settled. The code validates every edge before searching, rejects unknown depots and negative travel times, and returns None if the destination is unreachable. It does not account for changing road times while a search runs.",
        "case": "From D-19, a direct route to D-47 costs 14 minutes, but D-19 to D-26 costs 7 and D-26 to D-47 costs 3. The improved route makes the older heap entry for D-47 stale. Continuing through D-52 for 4 more minutes yields a 14-minute route: D-19, D-26, D-47, D-52. Searching from D-52 back to D-19 returns None because this directed graph has no reverse roads. Skipping stale entries avoids processing the old D-47 distance as if it were current. The first current pop of the destination is final only because all edge weights are nonnegative.",
        "cost": "With V depots and E directed roads, validation and graph storage are O(V + E). Every strict improvement can add one heap entry, so this lazy approach may hold O(E) pending entries and take O((V + E) log(V + E)) time in a conservative bound. Best distances and predecessors use O(V) space. An indexed heap can keep one active entry per depot and support decrease-key, trading a position map and more update bookkeeping for a smaller heap. Negative weights invalidate this algorithm's settlement rule; use a method designed for them instead. The displayed route is one optimum, not necessarily unique when costs tie.",
        "mistakes": ["Do not process a popped distance that no longer equals the best known distance.", "Do not accept a negative road weight and still rely on Dijkstra's settled-node rule.", "Do not infer an undirected reverse road from a directed adjacency entry.", "Do not claim the lazy heap has only O(V) entries in its worst case."],
        "related": ["dsa/indexed-binary-heap-decrease-key", "dsa/graph-adjacency-list-and-bfs", "dsa/dependency-graph-topological-order"],
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
                 body=body, sort_order=41100 + order * 10, created_at=stamp, updated_at=stamp, published_at=stamp)
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
