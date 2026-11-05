"""Add four range-index contracts, a comparison project, and a quiz."""

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
        path="dsa/square-root-block-range-sum", program="sqrt_block_capacity.py",
        title="Square-root blocks: update one capacity and sum a range",
        summary="Group adjacent values so a range scan can skip full blocks after constant-time replacements.",
        definition="A block index divides one fixed-length array into consecutive groups and stores one sum per group. A query visits individual values at its two partial ends, then uses cached sums for every complete block between them. Replacing one value changes that value and its block sum by the same difference. This contract is deliberately narrow: zero-based positions, half-open query ranges, point replacement, and integer sums. An empty range returns zero. The implementation keeps the original values because partial blocks still need them. Its block width is the integer square root of the array length, with a minimum of one for an empty array.",
        case="A depot has seven daily capacities: 23, 47, 19, 61, 38, 52, and 29. The window [1, 6) totals 217. Correct the value at position three from 61 to 74; that same window now totals 230. The correction raises one cached block by 13. Query [4, 4) and receive zero without reading any capacity. These outputs are useful acceptance checks because the main window crosses block boundaries, the corrected position lies inside it, and the empty window tests the half-open convention. An invalid index is rejected before the block total changes.",
        cost="For N values and a block width near the square root of N, construction scans O(N) values and retains O(N) values plus O(sqrt N) block sums. Replacement costs O(1). A query touches at most two partial blocks and O(sqrt N) full blocks, so its worst-case time is O(sqrt N). For very small arrays, a plain scan may be faster and simpler. Compared with a Fenwick tree, this design offers a cheaper point replacement but a slower range query. It does not offer range assignment, minimum queries, array insertion, or automatic resizing; changing array length requires rebuilding the block partition.",
        mistakes=["Do not count a partial block both element by element and by its cached sum.", "Do not forget to apply the replacement difference to the cached block.", "Do not treat the stop index as included.", "Do not claim logarithmic query time for this fixed-width block scan."],
        related=["dsa/fenwick-tree-point-update-prefix-query", "dsa/segment-tree-range-sum-update", "dsa/prefix-sum-range-query-contract"],
    ),
    dict(
        path="dsa/merge-sort-tree-threshold-count", program="merge_sort_tree_threshold.py",
        title="Merge-sort trees: count readings below a threshold in one interval",
        summary="Keep a sorted run at each interval node and binary-search covered runs.",
        definition="A merge-sort tree overlays a binary interval tree on an immutable array. Each node retains a sorted copy of the values in its interval. To count readings at most a threshold inside [start, stop), the query partitions that range into fully covered nodes and binary-searches each node's sorted run. Equal values are counted individually; bisect-right is the boundary that includes the threshold itself. The structure preserves positions through its interval tree while retaining value order locally inside each node. It answers a two-dimensional question involving both position and value, which an ordinary prefix sum cannot answer without another restriction.",
        case="The stored sensor readings are 41, 18, 41, 73, 26, 55, and 12. In positions [1, 6), three readings are at most 41: 18, 41, and 26. Across the full array, two readings are strictly below 26, which the program expresses as at most 25. The duplicate 41 matters: when a selected interval contains both copies, both must count. A zero-length interval counts zero, including in an empty index. The index is a snapshot; if an old reading changes, this implementation rebuilds rather than patching sorted runs along a path.",
        cost="For N readings, each tree level stores N copied values. Construction takes O(N log N) time and O(N log N) space. A query covers O(log N) nodes and performs O(log N) binary search at each, giving O(log squared N) time. The Python implementation also pays for list objects and merged copies, so memory is material. A wavelet tree can answer related rank and selection queries with different storage and traversal tradeoffs. A simple sort of the selected slice costs O(K log K) for a range of K readings and may win when queries are rare. This lesson's index has no incremental update method.",
        mistakes=["Use bisect-right for an inclusive at-most threshold; bisect-left excludes equality.", "Do not discard duplicate readings when merging runs.", "Do not assume the sorted root preserves original positions by itself.", "Do not advertise point updates for this immutable implementation."],
        related=["dsa/wavelet-tree-subarray-order-statistics", "dsa/segment-tree-range-sum-update", "dsa/sparse-table-immutable-range-minimum"],
    ),
    dict(
        path="dsa/disjoint-sparse-table-range-sum", program="disjoint_sparse_table_sums.py",
        title="Disjoint sparse tables: immutable sums with constant-time queries",
        summary="Precompute disjoint suffix and prefix aggregates around binary split points.",
        definition="A disjoint sparse table prepares an immutable sequence for associative range queries. At every binary scale, it computes suffix sums on the left of a split and prefix sums on the right. For a non-singleton interval, the highest bit where its first and last positions differ identifies one split between them. The corresponding suffix and prefix cover the requested interval exactly once, with no overlap. That matters for addition: an ordinary sparse-table trick that overlaps two intervals works for idempotent minimum, but double-counts values under sum. The public method uses half-open positions and returns zero for an empty interval by explicit API choice.",
        case="The seven scan totals are 23, 47, 19, 61, 38, 52, and 29. The sum over [1, 6) is 217, across several binary split sizes. A one-value query [3, 4) returns 61 directly, since there is no differing endpoint bit to select. The empty query [2, 2) returns zero. Use unequal values so a duplicated contribution would change the expected result, and test intervals that both cross and stay within the largest split. Any later edit to a reading invalidates the prepared layers and calls for a rebuild.",
        cost="For N values, each of O(log N) layers fills at most N cells, giving O(N log N) preprocessing time and O(N log N) stored cells. A query performs bounds checks, one highest-differing-bit calculation, and two array reads, which is O(1) under a fixed-width word model. With arbitrary-precision integers, the bit and sum operations also depend on operand size. For query-only sums, a prefix-sum array is simpler, uses O(N) memory, and also answers in O(1); disjoint tables matter when the associative operation lacks a cheap inverse. This sum example makes the disjoint-cover invariant inspectable, not a claim that it beats prefix sums in practice.",
        mistakes=["Do not overlap the two halves when the operation is addition.", "Do not compute a split level for a singleton interval.", "Do not mutate the source values after building the layers.", "Do not choose this larger index for ordinary static sums without comparing a prefix array."],
        related=["dsa/sparse-table-immutable-range-minimum", "dsa/prefix-sum-range-query-contract", "dsa/segment-tree-range-sum-update"],
    ),
    dict(
        path="dsa/li-chao-tree-line-minimum", program="li_chao_tariff_minimum.py",
        title="Li Chao trees: minimum linear tariff at a chosen quantity",
        summary="Insert full-domain cost lines and query their minimum over fixed integer coordinates.",
        definition="A Li Chao tree stores linear cost functions over a declared inclusive integer domain. At each node, it keeps the line that is better at that node's midpoint; a displaced candidate can still be better on one side, so insertion continues only down that side. A point query walks one root-to-leaf path and takes the least value among lines encountered. This version uses integer slopes and intercepts, answers minimum only, and treats every inserted line as valid across the entire domain. It allocates nodes when needed. An empty index has no minimum, and a query outside the domain is rejected rather than silently extrapolated.",
        case="Three delivery tariffs charge 7 times units plus 13, 4 times units plus 49, and 9 times units minus 11, with units restricted to 0 through 80. At five units the costs are 48, 69, and 34, so the minimum is 34. At 35 units they are 258, 189, and 304, so the minimum is 189. The winner changes as quantity changes; storing only the line with the smallest intercept or slope would fail. Negative intercepts are allowed in this numerical model, but a business system would separately decide whether such tariffs are valid.",
        cost="Let D be the number of integer coordinates in the declared domain and M the number of inserted full-domain lines. Each insertion and point query visits O(log D) nodes; insertion may allocate O(log D) nodes, so total storage is O(M log D) in the worst case. Integer evaluation also has operand-bit cost beyond the tree step count. This version does not delete lines, restrict a line to one subinterval, or expand its coordinate domain. For a small fixed set of lines, a direct O(M) scan avoids tree memory and is often enough. The logarithmic domain cost is useful when many lines and many point queries coexist.",
        mistakes=["Do not query outside the declared integer domain.", "Do not assume one line wins at every quantity because it wins at the midpoint.", "Do not describe this full-line index as supporting segment-limited tariffs or deletion.", "Do not take a minimum before any line has been inserted."],
        related=["dsa/segment-tree-range-sum-update", "dsa/sparse-coordinate-segment-tree", "dsa/range-query-structures"],
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
                 sort_order=42200 + order * 10, created_at=stamp, updated_at=stamp, published_at=stamp)
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
project_path = "dsa/range-workload-index-audit-project"
quiz_path = "quizzes/dsa-block-threshold-disjoint-line-contracts"
assert project_path not in by_path and quiz_path not in by_path
project = copy.deepcopy(by_path["dsa/scan-batch-capacity-median-integrity-project"])
project.update(id=str(uuid.uuid5(uuid.NAMESPACE_URL, "aitrove:" + project_path)), path=project_path,
               title="Project: audit four range-query workloads", summary="Select and verify an index against exact query and update contracts.",
               sort_order=42240, created_at=stamp, updated_at=stamp, published_at=stamp)
project["data"].update(reading_minutes=27, related=[{"path": path, "title": by_path[path]["title"]} for path in new_paths])
project["body"] = (
    "<p>A depot report combines four requests that happen to mention ranges but demand different indexes. Daily capacities can be corrected in place and summed. An immutable sensor batch needs position-bounded threshold counts. A frozen scan array needs many associative aggregate queries. A growing offer book needs the least linear charge at selected integer quantities. Build a tiny plain reference for each: list slicing for sums, a filtered slice for threshold counts, the built-in sum for frozen intervals, and a scan of every tariff line for each quantity. Compare outputs after every operation. The references should remain separate because a structure that answers one contract does not automatically support the others.</p>"
    "<h2>Acceptance trace</h2><p>Use capacities 23, 47, 19, 61, 38, 52, 29; replace position three with 74 and require 230 over [1, 6). Use readings 41, 18, 41, 73, 26, 55, 12 and require three values at most 41 over [1, 6). On the original capacity snapshot, require 217 over [1, 6), 61 over [3, 4), and zero over [2, 2). Insert tariffs 7x+13, 4x+49, and 9x-11 over integer x from zero through 80; require minimums 34 at five and 189 at 35. These checks expose both endpoint convention and the distinction between a mutable index and a frozen snapshot.</p>"
    '<h3>Expected output</h3><pre><code class="language-text">corrected-sum=230 threshold-count=3 frozen-sum=217\ntariff-at-5=34 tariff-at-35=189</code></pre>'
    "<h2>Boundary and cost review</h2><p>Try an empty array, empty intervals, duplicate threshold values, a negative capacity correction, an empty tariff book, and a query just outside the declared quantity domain. Then state which edits require rebuilding each immutable index. Compare query-heavy and update-heavy workloads before choosing a structure. Measure memory as well as steps: the two static tables replicate values across logarithmic levels, while the block index keeps the underlying array plus block totals. Document whether the workload truly needs the general associative table when a prefix sum would be cheaper.</p>"
    "<h3>Common Mistakes</h3><ul><li>Do not include the stop position in a half-open query.</li><li>Do not count a threshold equal to the bound as excluded.</li><li>Do not use overlapping sparse-table intervals for addition.</li><li>Do not query an empty tariff book or outside its domain.</li></ul>"
    "<h2>Connected lessons</h2>" + links(new_paths + ["dsa/projects", "dsa/quizzes", subject_root])
)
entries.append(project)
by_path[project_path] = project

questions = [
    ("What changes when one block-indexed capacity is replaced?", ["The value and its one cached block sum", "Every cached block sum", "Only a sorted copy of the values"], "Only the group containing that position changes; its cached sum receives the new value minus the previous value."),
    ("What is the worst-case query cost near square-root block width?", ["O(sqrt N)", "O(1) for every interval", "O(N log N)"], "A query reads up to two partial blocks and roughly square-root N complete block summaries in the worst case."),
    ("Which update requires rebuilding this fixed block partition?", ["Changing the array length", "Replacing a value at an existing position", "Reading an empty interval"], "The cached groups rely on fixed positions and width, so insertion or deletion changes the partition itself."),
    ("How does a merge-sort tree include readings equal to a threshold?", ["Binary-search the right boundary of the threshold in each covered sorted run", "Discard duplicate values during merging", "Only inspect the root's first value"], "The right insertion boundary counts every selected reading at or below the threshold, including duplicate equal readings."),
    ("Why does each merge-sort tree node keep a sorted run?", ["A fully covered interval can answer a threshold count by binary search", "It makes arbitrary point replacement constant time", "It removes the need to preserve positional intervals"], "The interval tree restricts positions, while a sorted run at each covered node restricts values with binary search."),
    ("What is the query cost of the shown merge-sort tree?", ["O(log squared N)", "O(1) for any threshold", "O(N) for every nonempty range"], "A range has logarithmically many covered nodes, and each node performs a logarithmic binary search."),
    ("Why is an ordinary overlapping sparse-table query wrong for sums?", ["Overlap counts the shared values twice", "Addition is not associative", "An empty range cannot return zero"], "Addition is associative but not idempotent, so shared elements must occur in exactly one selected precomputed piece."),
    ("Which bit chooses the disjoint layer for a non-singleton range?", ["The highest bit where its first and last positions differ", "The least set bit of the range length", "The sign bit of its total"], "The highest differing endpoint bit identifies the split separating a prepared left suffix from a prepared right prefix."),
    ("What workload fits the disjoint table in this lesson?", ["Many queries over an immutable array", "Frequent replacements of old values", "Deleting tariffs from a line set"], "The table precomputes aggregates from a frozen sequence; any edit would invalidate stored suffixes and prefixes."),
    ("What quantity domain does the shown Li Chao index accept?", ["Only integer points in its declared inclusive interval", "Every real number", "Any integer without a declared bound"], "The tree is built over a fixed inclusive integer interval, and a query outside it is rejected before traversal."),
    ("What is stored along a Li Chao query path?", ["Candidate lines whose evaluated values are compared at the requested quantity", "Only the globally smallest slope", "Only the most recently inserted line"], "A candidate that loses at one midpoint can win elsewhere, so the minimum at a point comes from evaluating lines on its path."),
    ("Which feature is absent from this tariff index?", ["Deleting an inserted line", "Inserting full-domain integer lines", "Querying a point inside the domain"], "This implementation adds whole-domain lines and answers minimum point queries; line deletion needs a different design."),
]
balanced = []
for number, (prompt, options, explanation) in enumerate(questions):
    correct = options[0]
    distractors = options[1:]
    position = number % 3
    distractors.insert(position, correct)
    balanced.append({"prompt": prompt, "options": distractors, "answer": position, "explanation": explanation})
quiz = copy.deepcopy(by_path["quizzes/dsa-range-proof-median-contracts"])
quiz.update(id=str(uuid.uuid5(uuid.NAMESPACE_URL, "aitrove:" + quiz_path)), path=quiz_path,
            title="Block, threshold, disjoint, and line index contracts", summary="Check four range-index invariants, costs, and boundaries.",
            sort_order=42250, created_at=stamp, updated_at=stamp, published_at=stamp)
quiz["data"].update(duration_minutes=20, related=[{"path": path, "title": by_path[path]["title"]} for path in new_paths + [project_path]], questions=balanced)
quiz["body"] = "<p>Choose an index by its accepted operations, then check endpoints, mutation rules, and cost. Each question refers to the specific implementation linked below.</p><h2>Lessons</h2>" + links(new_paths) + "<h2>Design exercise</h2>" + links([project_path, subject_root])
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
    ("dsa/segment-tree-range-sum-update", new_paths[0]),
    ("dsa/wavelet-tree-subarray-order-statistics", new_paths[1]),
    ("dsa/sparse-table-immutable-range-minimum", new_paths[2]),
    ("dsa/prefix-sum-range-query-contract", new_paths[2]),
    ("dsa/sparse-coordinate-segment-tree", new_paths[3]),
):
    old = by_path[old_path]
    old["body"] += '<p><a href="/' + new_path + '">' + html.escape(by_path[new_path]["title"]) + "</a> extends this range-query decision.</p>"
    old["updated_at"] = stamp
for path in new_paths:
    entry = by_path[path]
    peers = [other for other in new_paths if other != path]
    entry["body"] += '<p>Compare its contract with ' + ", ".join('<a href="/' + other + '">' + html.escape(by_path[other]["title"]) + "</a>" for other in peers) + ', then apply the <a href="/' + project_path + '">range workload project</a> and check the <a href="/' + quiz_path + '">range-index quiz</a>.</p>'
    entry["updated_at"] = stamp

fixture.write_text(json.dumps(entries, ensure_ascii=False, indent=2) + "\n")
print(json.dumps({"lessons": new_paths, "project": project_path, "quiz": quiz_path, "questions": len(questions)}))
