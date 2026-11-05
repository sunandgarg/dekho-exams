"""Add four operation-focused Data Structure lessons and practice routes."""

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
    dict(
        path="dsa/lazy-segment-tree-range-add-minimum",
        program="lazy_range_minimum.py",
        title="Lazy segment tree: add to a range and query its minimum",
        summary="Defer covered-range additions while keeping each node's minimum current.",
        section="dsa/range-query-structures",
        definition="A lazy segment tree stores an aggregate for each interval plus an update that has not yet been pushed to its children. Here the aggregate is the minimum and the deferred operation adds the same integer to every value in a covered half-open range. Adding a constant changes that interval's minimum by the same constant, so a fully covered node can update its own minimum and pending amount without touching descendants. Before a partial descent, push moves the pending amount into both children and clears the parent's marker. The visible node minimum remains current throughout. An empty update changes nothing; an empty minimum query is rejected because it has no numeric answer.",
        case="Start with capacities 61, 47, 83, 26, 52, and 19. Subtract 7 from positions [1, 5), making the full-range minimum 19. Add 20 over [3, 6); the minimum in [2, 6) becomes 39, while [0, 3) still has minimum 40. Both updates overlap at positions 3 and 4, so their deferred amounts must compose by addition. This code deliberately handles range addition, not assignment. An assignment marker would need a separate overwrite rule; treating it as another increment would give wrong values after overlapping operations.",
        cost="For N initial values, construction takes O(N) time and uses O(N) minimum and pending storage. A range addition or nonempty minimum query visits O(log N) boundary branches in a segment-tree decomposition, with O(log N) recursion depth. The implementation's query may push pending markers and therefore mutate internal representation while preserving logical values. A flat array makes updates over K elements O(K) and scans of a K-element range O(K), often a better choice for tiny workloads. This index does not resize; adding a new capacity position requires a rebuild or another representation.",
        mistakes=["Do not forget to push a pending amount before entering only one child.", "Do not combine minimums using addition after a partial update.", "Do not treat an empty range as having an ordinary minimum.", "Do not reuse the add marker for range assignment without changing composition rules."],
        related=["dsa/segment-tree-range-sum-update", "dsa/sparse-coordinate-segment-tree", "dsa/sparse-table-immutable-range-minimum"],
    ),
    dict(
        path="dsa/binary-lifting-lowest-common-ancestor",
        program="binary_lifting_ancestor.py",
        title="Binary lifting: ancestors and common managers",
        summary="Precompute powers-of-two parent jumps for a fixed rooted tree.",
        section="dsa/trees-and-heaps",
        definition="Binary lifting stores the 2^j-th ancestor of each node for successive powers j. A jump of K generations decomposes K into set bits and follows only those table entries. A lowest common ancestor query first raises the deeper node to the other node's depth, then raises both from the largest safe jump downward until their parents match. This reporting-tree implementation rejects duplicate IDs, missing managers, cycles, and disconnected components. It returns None when a requested ancestor lies above the root. The common manager of a node with itself is that node, and a manager is an ancestor of a direct report under the usual inclusive convention.",
        case="E-19 manages E-26 and E-47; E-26 manages E-52 and E-61; E-47 manages E-83. Two generations above E-52 is E-19. The lowest common manager of E-52 and E-61 is E-26, while the common manager of E-52 and E-83 is E-19. These results depend on the reporting edges staying fixed after preprocessing. Moving E-52 to a new manager invalidates its depth and every jump entry for its descendants. A mutable organization chart needs a rebuild or a different update-aware structure.",
        cost="For N employees, iterative traversal finds parents and depths in O(N) time, then builds O(N log N) ancestor entries in O(N log N) time and space. Ancestor and common-manager queries each take O(log N) time and O(1) additional working space. A single parent walk costs O(height) per request and needs only O(N) parent storage; it may be preferable when queries are rare. The table stores identifiers indirectly through integer positions, so dictionary lookup adds expected O(1) access. The model is one rooted tree, not a general directed reporting graph with multiple managers.",
        mistakes=["Do not index a missing ancestor as if it were a real employee.", "Do not compare nodes at different depths before leveling them.", "Do not reuse the table after moving a reporting edge.", "Do not accept two roots or a cycle as a valid management tree."],
        related=["dsa/heavy-light-tree-path-sums", "dsa/iterative-binary-tree-traversal-orders", "dsa/dependency-graph-topological-order"],
    ),
    dict(
        path="dsa/two-dimensional-fenwick-rectangle-sums",
        program="fenwick_warehouse_grid.py",
        title="Two-dimensional Fenwick tree: update cells and sum rectangles",
        summary="Carry point differences through row and column summaries, then use four prefixes.",
        section="dsa/range-query-structures",
        definition="A two-dimensional Fenwick tree extends prefix sums across rows and columns. Each stored cell summarizes a rectangle determined by the lowest set bit of its one-based row and column indexes. Assigning a warehouse quantity first computes its difference from the prior quantity; that difference is added to every Fenwick summary that covers the cell. A prefix query returns the sum in [0, row_stop) by [0, column_stop). A general half-open rectangle uses four prefixes by inclusion and exclusion. Rows and columns are independent dimensions, and a zero-width or zero-height rectangle has sum zero.",
        case="In a four-row, five-column warehouse, record 47 units at cell (1, 2), 61 at (2, 3), and 19 at (3, 4). Rectangle [1, 3) by [2, 4) contains the first two cells and sums to 108. Reassign (1, 2) to 26, so that same rectangle sums to 87; the whole grid now sums to 106. The coordinate contract is zero-based for public calls and one-based inside the Fenwick loops. Calling assign twice with the same quantity must leave the totals unchanged. Swapping row and column indexes silently corrupts answers on a nonsquare grid.",
        cost="For R rows and C columns, storage is O(RC) integers for both the current grid and Fenwick summaries. Point assignment and prefix sum take O(log R log C) time and O(1) working space. A rectangle query makes four prefix calls and has the same asymptotic bound. Building by repeated assignments costs O(RC log R log C) if every cell is populated; a direct bulk build could improve preprocessing. A sparse warehouse with enormous dimensions and few occupied cells should use coordinate compression or a sparse index instead of this dense allocation. The dimensions remain fixed after construction.",
        mistakes=["Do not add a replacement quantity without subtracting the old quantity.", "Do not omit the final inclusion-exclusion corner term.", "Do not confuse inclusive cell coordinates with half-open rectangle stops.", "Do not allocate a dense R by C grid for a huge sparse coordinate space."],
        related=["dsa/fenwick-tree-point-update-prefix-query", "dsa/prefix-sum-range-query-contract", "dsa/sparse-coordinate-segment-tree"],
    ),
    dict(
        path="dsa/robin-hood-hash-backward-shift-deletion",
        program="robin_hood_asset_set.py",
        title="Robin Hood hashing: probe distance and backward-shift deletion",
        summary="Give a longer-displaced key the earlier slot, then close a deletion gap.",
        section="dsa/hash-tables",
        definition="Robin Hood hashing is an open-addressed table that compares each key's distance from its home slot during insertion. When an incoming key has traveled farther than the current occupant, they swap, and the displaced occupant continues probing. Lookup can stop at an empty slot or when the occupant's home distance is smaller than the searcher's current distance; beyond that point the searched key cannot appear while the invariant holds. Deletion shifts later keys backward until it reaches an empty slot or a key already at home. This preserves the lookup stopping rule without a tombstone. The example is a fixed-capacity set of integer asset IDs, not a concurrent hash map.",
        case="Use seven slots and insert 19, 26, 33, 47, and 54. All five IDs share a home slot modulo seven, creating a visible probe cluster. Asset 47 is present. Removing 26 shifts later cluster members backward; 33 remains findable, and the sorted live IDs are 19, 33, 47, 54. A duplicate insert returns false. Once all slots are occupied, a new distinct ID raises rather than looping forever. Hash quality matters: an attacker who forces collisions can turn every operation into a long scan, regardless of the table's average-case appeal.",
        cost="With fixed capacity C, a lookup, insertion, or deletion probes O(C) slots in the worst case. Backward-shift deletion may move O(C) occupants. Under a suitable hash and controlled load, expected probes are short, but this implementation makes no formal bound for adversarial IDs. Storage is O(C) slots and O(1) working space. The public set does not resize, so callers must choose capacity and handle overflow. Iterators over raw slots are unstable across insertions and deletions because keys move. Compared with tombstones, backward shifting avoids stale markers but pays immediate movement cost at deletion time.",
        mistakes=["Do not stop a lookup merely because its first home slot contains another key.", "Do not leave a deletion hole before displaced keys that depend on that probe path.", "Do not move a key backward past its home slot.", "Do not claim worst-case constant time under collisions or a full table."],
        related=["dsa/open-addressing-tombstones-rehash", "dsa/hash-map-collision-and-load-contract", "dsa/hash-set-membership-and-order"],
    ),
]


def links(paths):
    return "<ul>" + "".join('<li><a href="/' + path + '">' + html.escape(by_path[path]["title"]) + "</a></li>" for path in paths) + "</ul>"


for order, lesson in enumerate(lessons):
    path, section = lesson["path"], lesson["section"]
    assert path not in by_path
    source = root / "work/dsa-programs" / lesson["program"]
    program = source.read_text().rstrip()
    output = subprocess.run([sys.executable, str(source)], check=True, capture_output=True, text=True).stdout.strip()
    related = [section, subject_root, *lesson["related"], "dsa/projects", "dsa/quizzes"]
    body = (
        "<p>" + html.escape(lesson["definition"]) + "</p>"
        + "<h2>Operational case</h2><p>" + html.escape(lesson["case"]) + "</p>"
        + '<h2>Working Python program</h2><pre><code class="language-python">' + html.escape(program, quote=False) + "</code></pre>"
        + '<h3>Output</h3><pre><code class="language-text">' + html.escape(output) + "</code></pre>"
        + "<h2>Time, space, and tradeoff</h2><p>" + html.escape(lesson["cost"]) + "</p>"
        + "<h3>Common Mistakes</h3><ul>" + "".join("<li>" + html.escape(item) + "</li>" for item in lesson["mistakes"]) + "</ul>"
        + "<h2>Connected lessons</h2>" + links(related)
    )
    entry = copy.deepcopy(by_path["dsa/fenwick-tree-point-update-prefix-query"])
    entry.update(id=str(uuid.uuid5(uuid.NAMESPACE_URL, "aitrove:" + path)), path=path, title=lesson["title"], summary=lesson["summary"], body=body,
                 sort_order=41800 + order * 10, created_at=stamp, updated_at=stamp, published_at=stamp)
    entry["data"].update(section_path=section, related=[{"path": target, "title": by_path[target]["title"]} for target in related])
    entries.append(entry)
    by_path[path] = entry
    for hub_path in (section, subject_root):
        hub = by_path[hub_path]
        module = hub["data"]["modules"][0] if hub_path == section else next(module for module in hub["data"]["modules"] if module["title"] == by_path[section]["title"])
        module["lessons"].append(path)
        hub["body"] += '<p><a href="/' + path + '">' + html.escape(lesson["title"]) + "</a></p>"
        hub["updated_at"] = stamp

new_paths = [lesson["path"] for lesson in lessons]
project_path = "dsa/range-ancestor-grid-hash-audit-project"
quiz_path = "quizzes/dsa-lazy-ancestor-grid-hash-contracts"
assert project_path not in by_path and quiz_path not in by_path
project = copy.deepcopy(by_path["dsa/incident-search-and-streaming-project"])
project.update(id=str(uuid.uuid5(uuid.NAMESPACE_URL, "aitrove:" + project_path)), path=project_path,
               title="Project: audit capacity ranges and warehouse indexes",
               summary="Check lazy minima, reporting ancestors, warehouse rectangles, and collision recovery.",
               sort_order=41850, created_at=stamp, updated_at=stamp, published_at=stamp)
project["data"].update(reading_minutes=24, related=[{"path": path, "title": by_path[path]["title"]} for path in new_paths])
project["body"] = (
    "<p>A warehouse console adjusts capacity estimates across intervals, answers reporting-chain questions, totals quantities in rectangular storage zones, and keeps an asset-ID set. Each index has a separate invariant. The segment tree postpones work only on fully covered intervals; the reporting table is valid only for one fixed rooted tree; the two-dimensional Fenwick grid converts assignments into differences; and a Robin Hood table preserves probe order when deleting a key. Compare outputs against an array, a plain parent map, a matrix scan, and a Python set.</p>"
    "<h2>Acceptance trace</h2><p>Start capacity values 61, 47, 83, 26, 52, 19. Subtract 7 over [1, 5), add 20 over [3, 6), and require a minimum of 39 in [2, 6). Build a reporting tree where E-19 manages E-26 and E-47, E-26 manages E-52 and E-61, and E-47 manages E-83; the common manager for E-52 and E-83 is E-19. Put 47 units at grid cell (1, 2), 61 at (2, 3), and 19 at (3, 4). Rectangle [1, 3) by [2, 4) sums to 108 before replacing the first quantity with 26, then 87. Insert five colliding asset IDs into seven slots, delete 26, and confirm 33 remains findable.</p>"
    '<h3>Expected output</h3><pre><code class="language-text">range-minimum=39 common-manager=E-19\nrectangle-before=108 rectangle-after=87\nasset-33-present=true live=19,33,47,54</code></pre>'
    "<h2>Cost and boundary review</h2><p>Lazy range updates and minimum queries take O(log N) time over a fixed array. Binary lifting spends O(N log N) preprocessing and answers common-ancestor requests in O(log N). A dense two-dimensional Fenwick grid spends O(RC) memory and O(log R log C) time per assignment or rectangle. The fixed-capacity hash set has O(C) worst-case probes and can reject insertion when full. Test invalid bounds and malformed trees explicitly. These examples are local single-process models; none supplies transactional atomicity, live topology edits, or synchronized readers.</p>"
    "<h3>Common Mistakes</h3><ul><li>Do not lose a deferred update during partial descent.</li><li>Do not use a stale ancestor table after moving an employee.</li><li>Do not omit an inclusion-exclusion corner.</li><li>Do not leave a hash deletion hole before displaced keys.</li></ul>"
    "<h2>Connected lessons</h2>" + links(new_paths + ["dsa/projects", "dsa/quizzes", subject_root])
)
entries.append(project)
by_path[project_path] = project

questions = [
    ("What does a fully covered lazy minimum node do on range addition?", ["Adds the amount to its minimum and pending marker", "Scans every original array element", "Replaces its minimum with the range length"], "The same increment changes every value and the interval minimum equally, so descendants can wait until a partial descent."),
    ("When must a pending range addition be pushed?", ["Before descending into only part of that node's interval", "Before returning a fully covered node's current minimum", "Only after rebuilding the whole tree"], "A partial visit needs child summaries to include all earlier changes that the parent has postponed."),
    ("Why reject a minimum query over an empty interval?", ["No input value has a finite minimum under this API", "The tree has no root", "Every empty interval must equal zero"], "An empty set has no ordinary numeric minimum; using zero could hide a boundary error or alter results for positive values."),
    ("What is stored in a binary-lifting table entry?", ["A node's 2^j-th ancestor", "The j-th child in insertion order", "Every employee at the same depth"], "Powers-of-two parent jumps allow an arbitrary generation count to be decomposed into a logarithmic number of moves."),
    ("What is the common manager of two employees when one manages the other?", ["The manager who is already an ancestor", "Always the root", "The younger employee"], "The lowest common ancestor is the deepest node shared by both root paths, including either endpoint itself."),
    ("What invalidates the shown reporting index?", ["Moving a reporting edge after preprocessing", "Querying an employee against itself", "Requesting zero generations"], "Parent jumps and depths describe one fixed tree, so changing a parent relation requires recomputing affected summaries."),
    ("How does a two-dimensional Fenwick assignment update summaries?", ["It propagates the new-minus-old difference along both index axes", "It adds the full new value on top of the old value", "It changes only one summary cell"], "The current quantity is already included in covering summaries; a replacement must apply only its difference."),
    ("How many prefix calls form an arbitrary rectangle sum?", ["Four", "One in every case", "One per stored grid cell"], "Inclusion and exclusion combine the large prefix, two removed strips, and their shared corner."),
    ("What does an empty-width rectangle return?", ["Zero", "The whole row total", "An unbounded coordinate error"], "The half-open rectangle contains no cells when either stop equals its corresponding start."),
    ("When does Robin Hood insertion swap with an occupant?", ["When the incoming key has probed farther from home", "Whenever its integer ID is smaller", "Only when the slot is empty"], "The longer-displaced key takes the earlier slot, while the displaced occupant continues probing from that position."),
    ("Why shift keys backward after deleting a Robin Hood slot?", ["To keep later displaced keys reachable without tombstones", "To sort keys numerically", "To enlarge the table"], "A raw hole can terminate lookup before a key that still depends on the cluster's probe path."),
    ("What is the worst-case bound for this fixed-capacity hash set?", ["O(C) probes for capacity C", "Guaranteed O(1) probes", "O(log C) probes from a balanced tree"], "Collisions can span much of the table; no randomized worst-case bound or resize step is implemented."),
]
balanced = []
for number, (prompt, options, explanation) in enumerate(questions):
    correct = options[0]
    distractors = options[1:]
    position = number % 3
    distractors.insert(position, correct)
    balanced.append({"prompt": prompt, "options": distractors, "answer": position, "explanation": explanation})
quiz = copy.deepcopy(by_path["quizzes/dsa-pattern-spatial-frequency-indexes"])
quiz.update(id=str(uuid.uuid5(uuid.NAMESPACE_URL, "aitrove:" + quiz_path)), path=quiz_path,
            title="Lazy ranges, ancestors, grids, and hash probes",
            summary="Check pending additions, parent jumps, rectangle corners, and deletion shifts.",
            sort_order=41860, created_at=stamp, updated_at=stamp, published_at=stamp)
quiz["data"].update(duration_minutes=20, related=[{"path": path, "title": by_path[path]["title"]} for path in new_paths + [project_path]], questions=balanced)
quiz["body"] = "<p>Use exact operation boundaries. The right result depends on deferred state, ancestor depth, rectangle corners, and displaced hash slots.</p><h2>Lessons</h2>" + links(new_paths) + "<h2>Design exercise</h2>" + links([project_path, subject_root])
entries.append(quiz)
by_path[quiz_path] = quiz

for hub_path, destination in (("dsa/projects", project_path), ("dsa/quizzes", quiz_path)):
    hub = by_path[hub_path]
    hub["data"]["modules"][0]["lessons"].append(destination)
    hub["body"] += '<p><a href="/' + destination + '">' + html.escape(by_path[destination]["title"]) + "</a></p>"
    hub["updated_at"] = stamp
    root_module = next(module for module in by_path[subject_root]["data"]["modules"] if module["title"] == hub["title"])
    root_module["lessons"].append(destination)
    by_path[subject_root]["body"] += '<p><a href="/' + destination + '">' + html.escape(by_path[destination]["title"]) + "</a></p>"
    by_path[subject_root]["updated_at"] = stamp

for old_path, new_path in (
    ("dsa/segment-tree-range-sum-update", new_paths[0]),
    ("dsa/heavy-light-tree-path-sums", new_paths[1]),
    ("dsa/fenwick-tree-point-update-prefix-query", new_paths[2]),
    ("dsa/open-addressing-tombstones-rehash", new_paths[3]),
):
    old = by_path[old_path]
    old["body"] += '<p><a href="/' + new_path + '">' + html.escape(by_path[new_path]["title"]) + "</a> adds a related operation contract.</p>"
    old["updated_at"] = stamp
for path in new_paths:
    entry = by_path[path]
    entry["body"] += '<p>Apply the invariant in the <a href="/' + project_path + '">warehouse indexes project</a>, then check the <a href="/' + quiz_path + '">operations quiz</a>.</p>'
    entry["updated_at"] = stamp

fixture.write_text(json.dumps(entries, ensure_ascii=False, indent=2) + "\n")
print(json.dumps({"lessons": new_paths, "project": project_path, "quiz": quiz_path, "questions": len(questions)}))
