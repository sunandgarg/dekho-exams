"""Add coordinate ranks, ordered frequencies, offline distinct counts, and grid sums."""

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
section = "dsa/range-query-structures"
stamp = datetime.datetime.now(datetime.UTC).isoformat()

lessons = [
    dict(
        path="dsa/coordinate-compression-ordered-ranks", program="coordinate_rank_catalog.py",
        title="Coordinate compression: preserve order with dense integer ranks",
        summary="Map sparse numeric keys to contiguous positions without discarding duplicates in source records.",
        definition="Coordinate compression replaces each distinct key in a known finite catalog with its position in sorted key order. It does not shrink a numeric value or preserve the distance between values; it preserves equality and relative order. A key-to-rank map supports exact lookup, and a sorted key array reverses a rank and finds the first known key at or above an arbitrary threshold. The source batch may contain duplicates, yet the catalog contains each distinct key once. Later algorithms can place counts or sums in a compact array indexed by rank. This version is static: adding a previously unknown key requires rebuilding the sorted catalog and any dependent index.",
        case="Shipment weights arrive as 4700, -35, 4700, 82000, and 19. The known keys become -35, 19, 4700, 82000; 4700 maps to rank two in zero-based order and rank three maps back to 82000. A lower-bound lookup for 20 gives rank two, the first known key no smaller than 20. The two shipments weighing 4700 still occupy two records even though the catalog gives them the same rank. A consumer that uses rank differences as weight differences would make a serious mistake: the gap between 19 and 4700 is 4681, while their rank gap is one.",
        cost="For N input values and U distinct keys, sorting the unique catalog costs O(N + U log U) expected time under ordinary hash-set assumptions, plus O(U) catalog storage. Building the dictionary costs O(U) expected time. Exact rank lookup is O(1) expected hash time, reverse lookup is O(1), and lower-bound lookup is O(log U). Comparisons of large or composite keys also have their own cost. If hash behavior is adversarial, dictionary and set bounds can degrade. Coordinate ranking does not solve a query alone; it supplies compact ordered positions to a frequency tree or another structure. Rebuilding after unknown keys arrive can change every later rank.",
        mistakes=["Do not mistake a dense rank for the original measurement or distance.", "Do not discard duplicate source records merely because catalog keys are unique.", "Do not assume an unseen key already has an exact rank.", "Do not update a dependent rank index without rebuilding when the catalog changes."],
        related=["dsa/fenwick-tree-point-update-prefix-query", "dsa/wavelet-tree-subarray-order-statistics", "dsa/sparse-coordinate-segment-tree"],
    ),
    dict(
        path="dsa/fenwick-order-statistic-multiset", program="fenwick_order_statistics.py",
        title="Fenwick frequency index: select the kth stored key",
        summary="Combine a fixed ordered key catalog with mutable counts and binary lifting on a Fenwick tree.",
        definition="A frequency Fenwick tree stores nonnegative counts at dense ranks of a known ordered key catalog. Insertion and removal change one count and all Fenwick summaries above it. To find the kth stored key, the search descends powers of two through the implicit prefix tree, skipping a candidate prefix only when its count is smaller than the remaining one-based rank. Duplicate keys consume multiple positions in rank order. A separate prefix count tells how many stored keys lie strictly below a threshold, even when the threshold itself is not in the catalog. The key universe is fixed here, although multiplicities may change. Negative multiplicity and an out-of-range selection are rejected before mutation.",
        case="Declare allowed weights -35, 19, 4700, and 82000. Record shipments weighing 4700, -35, 4700, 19, and 82000. Sorted by weight, the third stored shipment weighs 4700; two shipments weigh less than 4700. Remove one 4700 shipment and the third still weighs 4700 because the other copy remains. This trace tests multiplicity and the one-based selection contract, not just unique-key ordering. A request for rank zero or rank five after removal is invalid. A previously unseen weight needs a rebuilt catalog and tree, so the example does not pretend that arbitrary keys can arrive without cost.",
        cost="Let U be the number of allowed distinct weights and M the number of recorded shipments. The initial sorted catalog costs O(U log U), and the Fenwick arrays use O(U) space. A count change, strict-below query, or kth selection takes O(log U) tree steps; finding a key's catalog position by binary search is also O(log U). The total stored multiplicity M does not enlarge the tree. Python integer arithmetic and comparisons add operand-size costs. An unsorted list gives cheap appends but expensive rank selection. A balanced search tree with subtree counts can admit new keys without rebuilding, at a more involved implementation cost. This fixed catalog favors a known key universe.",
        mistakes=["Do not use zero-based k when the selection API expects one-based rank.", "Do not remove more copies than the multiset contains.", "Do not let a negative count invalidate monotone prefix totals.", "Do not treat an unknown weight as though it already has a Fenwick position."],
        related=["dsa/coordinate-compression-ordered-ranks", "dsa/fenwick-tree-point-update-prefix-query", "dsa/avl-subtree-size-rank-select"],
    ),
    dict(
        path="dsa/mo-offline-distinct-range-counts", program="mo_distinct_batches.py",
        title="Mo ordering: count distinct scan codes across an offline query batch",
        summary="Reorder fixed-array window requests to reuse a mutable frequency counter.",
        definition="Mo ordering is an offline range-query plan for a frozen array. It groups requests by the block containing each left endpoint and sorts within a group by the right endpoint. A moving half-open window maintains a frequency counter and a distinct-key count. Adding a code changes the distinct count only when its old frequency was zero; removal changes it only when the new frequency becomes zero. Queries execute in reordered sequence, while answers return to their original request positions. This is useful when the aggregate can be updated cheaply by adding or removing one boundary element but does not have a compact prefix inverse. The program validates every request before moving the window.",
        case="Seven scan codes are D47, D19, D47, D61, D19, D83, D47. Four requested windows are [1, 6), [0, 3), [3, 3), and [2, 7). Their distinct counts in original request order are four, two, zero, and four. The algorithm may answer those requests in a different order internally, so retaining each original position is essential. Duplicate D47 values should increase frequency without increasing the distinct count twice. Empty [3, 3) must return zero even if the previous processed window was nonempty. Changing a scan code after requests have been planned is outside this static implementation's contract.",
        cost="With N values and Q requests, sorting requests takes O(Q log Q) time. A standard square-root block ordering makes O((N + Q) sqrt N) boundary moves in a conservative bound, with expected O(1) counter work per move under ordinary hash-map assumptions. Memory is O(N + Q) for the copied input, current frequencies, and answer list; the number of keys in the counter never exceeds N. Python sorting and hashing constants matter. For a handful of short windows, scanning a set over each requested slice is simpler. This program does not answer queries as they arrive, update values between queries, or claim that reordering is valid when answers determine later request endpoints.",
        mistakes=["Do not return answers in processing order instead of request order.", "Do not change the distinct total on every duplicate add or partial removal.", "Do not treat the stop endpoint as included.", "Do not use offline reordering when later requests depend on earlier answers."],
        related=["dsa/square-root-block-range-sum", "dsa/merge-sort-tree-threshold-count", "dsa/wavelet-tree-subarray-order-statistics"],
    ),
    dict(
        path="dsa/two-dimensional-prefix-grid-sums", program="prefix_grid_capacity.py",
        title="Two-dimensional prefixes: constant-time static rectangle sums",
        summary="Build a padded cumulative grid and recover any half-open rectangle by inclusion and exclusion.",
        definition="A two-dimensional prefix grid stores the total above and left of every boundary in an extra top row and left column. Each cell combines its source value with the prefix above and the prefix to its left, then removes their shared top-left overlap. A rectangle query applies the same inclusion and exclusion to four prefix corners. This implementation accepts half-open row and column bounds: [top, bottom) by [left, right). Empty rectangles return zero. It rejects ragged input rows because a rectangle needs one consistent column count. The grid is a frozen snapshot; the program does not expose a point update method or silently repair stale prefixes after source changes.",
        case="The capacity grid has rows 23, 47, 19, 61; 38, 52, 29, 74; and 13, 41, 67, 31. The rectangle spanning rows [0, 2) and columns [1, 3) totals 147. The whole grid totals 495. A zero-height rectangle over rows [1, 1) totals zero even when its column span is nonempty. The padded border removes separate code paths for a query touching row zero or column zero. A rectangle whose bottom or right bound exceeds the grid shape is rejected before any arithmetic, which keeps inclusive and exclusive coordinates from drifting between callers.",
        cost="For R rows and C columns, construction reads every cell once, taking O(RC) time and O((R + 1)(C + 1)) space. Each rectangle query uses four stored prefix values and constant arithmetic, so O(1) time under a fixed-width arithmetic model. Integer size still matters for very large totals. Recomputing a source cell would affect many prefixes and can take O(RC) in this simple snapshot; a two-dimensional Fenwick tree offers logarithmic updates and rectangle sums with a different memory and implementation cost. If only a few small rectangles are requested, a direct nested scan may be cheaper than building the full table.",
        mistakes=["Do not omit the shared top-left term after subtracting top and left strips.", "Do not mix inclusive bottom-right coordinates with the half-open API.", "Do not accept ragged rows as one rectangular grid.", "Do not claim that this static prefix table supports cheap point updates."],
        related=["dsa/prefix-sum-range-query-contract", "dsa/two-dimensional-fenwick-rectangle-sums", "dsa/disjoint-sparse-table-range-sum"],
    ),
]


def links(paths):
    return "<ul>" + "".join('<li><a href="/' + path + '">' + html.escape(by_path[path]["title"]) + "</a></li>" for path in paths) + "</ul>"


for order, lesson in enumerate(lessons):
    path = lesson["path"]
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
                 sort_order=42300 + order * 10, created_at=stamp, updated_at=stamp, published_at=stamp)
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
project_path = "dsa/query-workload-rank-window-grid-audit-project"
quiz_path = "quizzes/dsa-rank-window-grid-contracts"
assert project_path not in by_path and quiz_path not in by_path
project = copy.deepcopy(by_path["dsa/range-workload-index-audit-project"])
project.update(id=str(uuid.uuid5(uuid.NAMESPACE_URL, "aitrove:" + project_path)), path=project_path,
               title="Project: audit ranks, windows, and grid reports", summary="Verify four indexes against plain reference calculations and mutation limits.",
               sort_order=42340, created_at=stamp, updated_at=stamp, published_at=stamp)
project["data"].update(reading_minutes=28, related=[{"path": path, "title": by_path[path]["title"]} for path in new_paths])
project["body"] = (
    "<p>A logistics report has four independent lookup requirements. Shipment weights have sparse numeric labels but a known catalog. Recorded weights need mutable multiplicities and kth selection. A frozen scan batch needs distinct-code counts across many submitted windows. A fixed rectangular capacity grid needs rectangle totals. Build each index only after writing a plain reference: sorted unique keys for ranks, a sorted multiset list for kth values, a set over each scan slice for distinct counts, and a nested rectangle sum for the grid. Run the same requests through both paths. Preserve duplicates in records even though the rank catalog removes duplicate keys. State which requests can arrive online and which must be collected before reordering.</p>"
    "<h2>Acceptance trace</h2><p>For weights 4700, -35, 4700, 82000, 19, require rank two for 4700 and two recorded weights below 4700. The third recorded weight is 4700 before and after one copy is removed. For scan codes D47, D19, D47, D61, D19, D83, D47, require window counts four, two, zero, four for [1, 6), [0, 3), [3, 3), [2, 7). For the three-by-four capacity grid in the lesson, require 147 for rows [0, 2) by columns [1, 3), and 495 for the whole grid. Check the results in the original request order even if the window processor rearranges work.</p>"
    '<h3>Expected output</h3><pre><code class="language-text">rank-4700=2 third-weight=4700 distinct=[4, 2, 0, 4]\ncenter-capacity=147 full-capacity=495</code></pre>'
    "<h2>Boundary and cost review</h2><p>Test an empty key catalog, an empty frequency index, duplicate weights, a removal larger than recorded multiplicity, windows of length zero, a query with an excluded stop at the array length, an empty grid, and a ragged grid. Rebuild when an unseen weight enters the catalog or when the frozen scan codes or grid values change. Compare memory costs before selecting an index: the rank catalog stores distinct keys, the frequency tree stores one slot per known key, Mo ordering stores all requests, and the prefix grid stores an additional border. A report that needs one small query may need no index at all.</p>"
    "<h3>Common Mistakes</h3><ul><li>Do not use rank differences as measurement differences.</li><li>Do not select the kth key from distinct keys while ignoring multiplicity.</li><li>Do not return offline window answers in processing order.</li><li>Do not forget the rectangle overlap correction.</li></ul>"
    "<h2>Connected lessons</h2>" + links(new_paths + ["dsa/projects", "dsa/quizzes", subject_root])
)
entries.append(project)
by_path[project_path] = project

questions = [
    ("What does a coordinate rank preserve?", ["Equality and sorted key order", "Numeric distance between keys", "The original duplicate count by itself"], "Sorted distinct keys keep equality and relative order, while the gaps between their integer ranks do not represent measured gaps."),
    ("What happens when a new unseen key joins a static rank catalog?", ["Rebuild the catalog and dependent rank indexes", "Append it at the final rank regardless of value", "Reuse any duplicate rank"], "An inserted key may sit between old keys and shift later positions, so dependent dense indexes must be rebuilt or redesigned."),
    ("What does lower bound return when the threshold is absent?", ["The position of the first known key no smaller than it", "A required exact-key match", "The position of the greatest smaller key"], "Binary lower bound finds the insertion position for a threshold and does not require that threshold to be a catalog key."),
    ("Why may a Fenwick kth search skip a candidate prefix?", ["Its stored count is smaller than the remaining one-based rank", "Its key is negative", "It contains duplicate measurements"], "The search subtracts an entirely preceding frequency prefix only when that prefix cannot contain the requested occurrence."),
    ("What happens to kth selection when a key has two copies?", ["That key occupies two ranks in sorted multiset order", "It occupies one rank because catalog keys are unique", "The tree rejects duplicates"], "The catalog stores one coordinate for the key, but its nonnegative frequency contributes both recorded occurrences to prefix counts."),
    ("Why reject a removal that would make one frequency negative?", ["Kth search relies on nondecreasing prefix counts", "The key would become numerically smaller", "The catalog would become unsorted"], "Binary lifting over Fenwick frequencies assumes each key count is nonnegative, making cumulative counts monotone."),
    ("Why does Mo ordering retain each query's original position?", ["Processing order differs from the caller's request order", "The array elements are permanently reordered", "Every window is sorted internally"], "Block ordering changes the sequence in which windows are processed, so answers need their original slots when returned."),
    ("When does an added scan code increase the distinct total?", ["Only when its previous window frequency was zero", "Every time it appears", "Only when it equals the previous code"], "A repeated code changes frequency but does not create another distinct key inside the current half-open window."),
    ("Which request pattern breaks this offline batch plan?", ["A later window endpoint depends on an earlier answer", "All windows are known before processing", "Some windows are empty"], "Offline reordering is invalid if a caller cannot form the next request until it sees the previous answer."),
    ("Why is the grid prefix array padded with a top row and left column?", ["Boundary-touching rectangles use the same four-corner formula", "It stores one more original data row", "It enables constant-time point updates"], "A zero border makes prefixes at row or column zero defined, so the rectangle formula needs no separate edge cases."),
    ("Which term repairs double subtraction in a rectangle sum?", ["The shared top-left prefix is added back", "The entire bottom-right prefix is subtracted twice", "The source rectangle is multiplied by two"], "Removing the top and left outside strips subtracts their shared corner twice, so that overlap must be restored once."),
    ("Which operation is expensive for a static two-dimensional prefix grid?", ["Changing a stored cell and keeping all prefixes current", "Reading one valid rectangle", "Reading an empty rectangle"], "A changed source cell affects many later prefixes, while the built snapshot answers rectangle queries with four reads."),
]
balanced = []
for number, (prompt, options, explanation) in enumerate(questions):
    correct = options[0]
    distractors = options[1:]
    position = number % 3
    distractors.insert(position, correct)
    balanced.append({"prompt": prompt, "options": distractors, "answer": position, "explanation": explanation})
quiz = copy.deepcopy(by_path["quizzes/dsa-block-threshold-disjoint-line-contracts"])
quiz.update(id=str(uuid.uuid5(uuid.NAMESPACE_URL, "aitrove:" + quiz_path)), path=quiz_path,
            title="Coordinate ranks, order selection, offline windows, and grid sums", summary="Check multiplicity, offline order, and rectangle boundaries.",
            sort_order=42350, created_at=stamp, updated_at=stamp, published_at=stamp)
quiz["data"].update(duration_minutes=20, related=[{"path": path, "title": by_path[path]["title"]} for path in new_paths + [project_path]], questions=balanced)
quiz["body"] = "<p>Each structure has one data and update contract. Check what ranks preserve, how frequencies affect selection, why offline order changes, and how rectangle corners combine.</p><h2>Lessons</h2>" + links(new_paths) + "<h2>Design exercise</h2>" + links([project_path, subject_root])
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
    ("dsa/fenwick-tree-point-update-prefix-query", new_paths[0]),
    ("dsa/wavelet-tree-subarray-order-statistics", new_paths[1]),
    ("dsa/square-root-block-range-sum", new_paths[2]),
    ("dsa/merge-sort-tree-threshold-count", new_paths[2]),
    ("dsa/prefix-sum-range-query-contract", new_paths[3]),
    ("dsa/two-dimensional-fenwick-rectangle-sums", new_paths[3]),
):
    old = by_path[old_path]
    old["body"] += '<p><a href="/' + new_path + '">' + html.escape(by_path[new_path]["title"]) + "</a> extends this operation choice.</p>"
    old["updated_at"] = stamp
for path in new_paths:
    entry = by_path[path]
    peers = [other for other in new_paths if other != path]
    entry["body"] += '<p>Compare with ' + ", ".join('<a href="/' + other + '">' + html.escape(by_path[other]["title"]) + "</a>" for other in peers) + ', then run the <a href="/' + project_path + '">query workload audit</a> and <a href="/' + quiz_path + '">contract quiz</a>.</p>'
    entry["updated_at"] = stamp

fixture.write_text(json.dumps(entries, ensure_ascii=False, indent=2) + "\n")
print(json.dumps({"lessons": new_paths, "project": project_path, "quiz": quiz_path, "questions": len(questions)}))
