"""Add sparse, wavelet, parity, and implicit-sequence lessons and practice."""

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
        path="dsa/sparse-coordinate-segment-tree",
        program="sparse_coordinate_segment_tree.py",
        title="Sparse coordinate segment tree: allocate only visited paths",
        summary="Assign readings and sum half-open ranges across a huge, mostly empty coordinate span.",
        section="dsa/range-query-structures",
        definition="A sparse coordinate segment tree stores aggregate nodes only on paths touched by point assignments. Its logical coordinate space can be enormous without allocating an array proportional to that space. Each node covers a half-open interval and keeps the sum of its descendants. Missing children represent zero. The meter index also keeps a small map of assigned values, so an assignment computes the difference from the previous reading instead of accidentally adding the new value twice. The public range convention is [start, stop); empty intervals return zero. The root exists even when no meter has a nonzero reading.",
        case="The span has 2^40 possible positions. Assign 19 at coordinate 47 and 26 at a position just above the halfway point. Reassign position 47 to 52. A query over [0, 100) returns 52, and the whole span returns 78. Assigning zero at 47 makes the first query zero again. This sparse representation does not physically prune now-empty paths in the shown code; long-running workloads that cycle through many distinct positions can retain nodes after their readings return to zero. A separate pruning pass or a different index may be needed when that pattern dominates.",
        cost="With coordinate limit U, a point assignment follows O(log U) nodes and a range sum visits O(log U) boundary branches in the standard segment-tree decomposition. The map lookup is expected O(1). If M distinct positions have ever been assigned a changed value, path allocation can use O(M log U) nodes in the worst case, even when the current nonzero count is smaller. The recursive query consumes O(log U) call-stack space. This is not a compressed coordinate index: unlike a Fenwick tree over sorted known coordinates, it accepts unseen positions online, while paying pointer and Python object overhead for each allocated node.",
        mistakes=["Do not treat a point assignment as an increment; subtract the previous value first.", "Do not mix inclusive and half-open range endpoints.", "Do not claim memory falls when a value returns to zero; this code retains its path.", "Do not allocate a full array for a 2^40 span with only a few active positions."],
        related=["dsa/segment-tree-range-sum-update", "dsa/fenwick-tree-point-update-prefix-query", "dsa/persistent-segment-tree-versioned-sums"],
    ),
    dict(
        path="dsa/wavelet-tree-subarray-order-statistics",
        program="wavelet_incident_quantiles.py",
        title="Wavelet tree: subarray counts and order statistics",
        summary="Partition a fixed latency series by value and carry position ranges through prefix counts.",
        section="dsa/trees-and-heaps",
        definition="A wavelet tree indexes a fixed sequence by recursively partitioning its value range. Each node stores prefix counts of values routed left. A query over positions [start, stop) maps that interval into child coordinates with two prefix reads. Count-below returns how many values in the subarray are strictly less than a threshold. Select returns the value at a zero-based ordinal within the subarray's sorted multiset, so duplicate values occupy distinct ordinals. This is a static index; editing a latency after construction would invalidate stored partitions and prefixes. A plain sorted copy cannot answer arbitrary original-position subarray questions with the same information.",
        case="Index latency readings 61, 19, 47, 19, 83, 26, and 52. In positions [1, 6), three readings are below 47: 19, 19, and 26. The value at sorted ordinal 2 for that subarray is 26. Across the full sequence, ordinal 6 selects 83. Repeated readings remain separate occurrences even though they share one leaf value. A query for an empty interval can count zero, but it cannot select any ordinal. Invalid position or ordinal bounds raise rather than returning a misleading sentinel reading.",
        cost="Let N be the number of readings and sigma the covered integer value span. Building partitions and prefix arrays takes O(N log sigma) time and O(N log sigma) integer entries in this straightforward Python representation. Each count or select query follows at most O(log sigma) levels and uses O(log sigma) stack space for count or O(1) working space for iterative select. Wide sparse integer domains can make this uncompressed value-depth larger than needed; coordinate compression reduces height to O(log D) for D distinct values. A scan costs O(subarray length) per query and is simpler when query volume is low.",
        mistakes=["Do not drop duplicate values when answering an ordinal query.", "Do not mix global positions with child-local positions after routing through prefix counts.", "Do not promise point updates on this immutable index.", "Do not quote compressed-alphabet bounds for this uncompressed implementation."],
        related=["dsa/avl-subtree-size-rank-select", "dsa/sparse-table-immutable-range-minimum", "dsa/persistent-segment-tree-versioned-sums"],
    ),
    dict(
        path="dsa/parity-disjoint-set-constraints",
        program="parity_disjoint_set_constraints.py",
        title="Parity disjoint set: maintain same-or-different constraints",
        summary="Keep XOR parity to the leader while merging components and rejecting contradictions.",
        section="dsa/graphs-and-disjoint-sets",
        definition="A parity disjoint set stores an XOR bit from each member to its parent. The bit expresses whether the member has the same or opposite binary label as the parent; absolute labels are unnecessary. Find returns both the component leader and accumulated parity to that leader, compressing the path while updating the stored bit. Constrain merges two components under a required same-or-different relation, or checks a relation already implied within one component. Union by size keeps the parent forest shallow. A failed constraint returns false and leaves the existing accepted constraints intact; it does not repair a contradiction by rewriting old edges.",
        case="Asset A-19 must differ from A-47, and A-47 must differ from A-61. Both constraints are accepted. Their XOR composition makes A-19 and A-61 the same, so a request that they differ is rejected. A-83 belongs to a separate component, so its relationship to A-19 is unknown. This handles online additions of binary constraints and is a compact bipartite-consistency check for an evolving undirected graph. It does not support removing accepted constraints: after a deletion, old parity paths could continue to imply a relationship no longer justified by live edges.",
        cost="Each accepted union or find has amortized O(alpha(N)) time over a sequence of operations, where alpha is the inverse Ackermann function. The parent, size, and parity maps use O(N) space. The recursive find uses call-stack space bounded by the current parent path; union by size keeps that path logarithmic before compression. The chosen representation uses dictionary lookups for string IDs. For a fixed compact numeric ID space, arrays reduce overhead. To support deletions over known time windows, use rollback with an offline lifetime tree; ordinary path compression cannot be rolled back without recording additional changes.",
        mistakes=["Do not store only a leader if queries need same-or-different parity.", "Do not compress a path without composing its parity to the new parent.", "Do not merge two leaders before checking a same-component contradiction.", "Do not claim ordinary disjoint sets can delete accepted constraints."],
        related=["dsa/disjoint-set-union-connectivity", "dsa/disjoint-set-rollback-checkpoints", "dsa/offline-connectivity-edge-lifetimes"],
    ),
    dict(
        path="dsa/implicit-treap-range-reversal",
        program="implicit_treap_sequence.py",
        title="Implicit treap: edit positions and reverse a range",
        summary="Split by subtree size, merge by priority, and defer subtree reversal.",
        section="dsa/trees-and-heaps",
        definition="An implicit treap is a sequence tree whose in-order position comes from subtree sizes, not from comparing stored task IDs. Split separates the first K elements from the remainder. Merge joins two sequences whose relative order is already defined. Random priorities tend to keep the tree shallow, while each node's size makes positional splits possible. A reversal flag marks an entire subtree as logically reversed; push swaps its children and passes the flag down only when the subtree is next inspected. The shown API supports insertion at a position and reversal of a half-open range. It keeps duplicate task IDs as separate positions because task IDs are payloads, not search keys.",
        case="Start with tasks T-19, T-47, T-61, and T-83. Reverse [1, 4) to get T-19, T-83, T-61, T-47. Insert T-26 at position 2 and the order becomes T-19, T-83, T-26, T-61, T-47. The snapshot walks all five tasks and forces pending reversals down before reading nodes. A split is destructive to the current root links until the pieces are merged back; callers should expose operations through one owner instead of handing mutable subtree roots to unrelated writers. The fixed random seed makes the demonstration repeatable, not adversary-resistant.",
        cost="With independent random priorities, expected height is O(log N). Insert and range reverse perform a constant number of splits or merges and take expected O(log N) time and O(log N) recursion space. A snapshot takes O(N) time and O(N) output space. The worst-case treap can have O(N) height, causing O(N) operations and recursion-depth failure in Python. The structure stores O(N) nodes with size, priority, and lazy-reversal state. A Python list is usually better for small sequences or bulk iteration; this tree pays pointer overhead to make repeated middle edits and interval reversals cheap in expectation.",
        mistakes=["Do not compare task IDs to choose a sequence position; use left-subtree size.", "Do not split or walk below a pending reversal before pushing it.", "Do not forget to refresh size after changing a child link.", "Do not advertise worst-case logarithmic behavior for randomized priorities."],
        related=["dsa/persistent-ordered-index-path-copying", "dsa/avl-subtree-size-rank-select", "dsa/resizable-array-growth-and-insert-cost"],
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
                 sort_order=41600 + order * 10, created_at=stamp, updated_at=stamp, published_at=stamp)
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
project_path = "dsa/sparse-quantile-parity-sequence-audit-project"
quiz_path = "quizzes/dsa-sparse-quantile-parity-sequence"
assert project_path not in by_path and quiz_path not in by_path
project = copy.deepcopy(by_path["dsa/incident-search-and-streaming-project"])
project.update(id=str(uuid.uuid5(uuid.NAMESPACE_URL, "aitrove:" + project_path)), path=project_path,
               title="Project: audit sparse readings and task constraints",
               summary="Compare sparse coordinate sums, incident quantiles, parity groups, and editable dispatch order.",
               sort_order=41650, created_at=stamp, updated_at=stamp, published_at=stamp)
project["data"].update(reading_minutes=24, related=[{"path": path, "title": by_path[path]["title"]} for path in new_paths])
project["body"] = (
    "<p>A depot console stores a few readings in a huge coordinate domain, asks for incident-latency quantiles over fixed time slices, accepts same-or-different asset constraints, and edits the order of a dispatch task list. Each operation has a different mutation rule. Keep position ranges half-open. Check every reported value against a simple independent list or map, including invalid requests and repeated assignments. The four indexes should not share mutable nodes just because they are used by one console.</p>"
    "<h2>Acceptance trace</h2><p>Assign reading 19 at coordinate 47 and 26 at a far coordinate, then replace the first reading with 52. The near range sums to 52 and the whole range to 78; clearing coordinate 47 returns the near sum to zero. For latency sequence 61, 19, 47, 19, 83, 26, 52, count readings below 47 in [1, 6) and select sorted ordinal 2 there. Expect three and 26. Build parity constraints A-19 different A-47, then A-47 different A-61. A-19 and A-61 must be the same; reject a contradictory different request. Reverse task positions [1, 4), insert T-26 at position 2, and confirm T-19, T-83, T-26, T-61, T-47.</p>"
    '<h3>Expected output</h3><pre><code class="language-text">near=52 whole=78 cleared=0\nbelow=3 ordinal-2=26\nA-19/A-61=same contradiction=rejected\nT-19 T-83 T-26 T-61 T-47</code></pre>'
    "<h2>Cost and boundary review</h2><p>The sparse tree pays O(log U) time per point change or range sum over logical span U, while retaining paths that once held values. The wavelet tree builds O(N log sigma) prefix entries and answers fixed-sequence subarray count or select in O(log sigma) time. Parity union-find handles additions in amortized O(alpha(N)) time but cannot remove constraints. An implicit treap gives expected O(log N) positional edits and reversals, while a complete snapshot costs O(N). Explain why none of these indexes should be described as a concurrent or durable production store without separate synchronization and persistence work.</p>"
    "<h3>Common Mistakes</h3><ul><li>Do not add a replacement meter reading on top of the previous value.</li><li>Do not use a wavelet prefix from the parent as a child-local position.</li><li>Do not accept a conflicting parity edge within an existing component.</li><li>Do not read an implicit treap subtree without pushing its reversal flag.</li></ul>"
    "<h2>Connected lessons</h2>" + links(new_paths + ["dsa/projects", "dsa/quizzes", subject_root])
)
entries.append(project)
by_path[project_path] = project

questions = [
    ("What does a missing child mean in the sparse sum tree?", ["Its entire interval contributes zero", "Every position in it is unknown", "The range query must scan the full span"], "The index starts at zero everywhere and allocates a child only after a point assignment changes a position on its path."),
    ("Why does assigning 52 after 19 at one position add only 33 to ancestor sums?", ["Assignment propagates the difference from the previous value", "The index ignores all earlier assignments", "Every ancestor already stores 52"], "An aggregate already contains the old reading, so adding the full replacement would count that position twice."),
    ("What memory can remain after a sparse-tree value returns to zero?", ["Previously allocated path nodes", "A full array of 2^40 positions", "No nodes under any circumstance"], "The shown code clears the value map entry but does not unlink path nodes, so allocation follows positions ever changed."),
    ("What does a wavelet node's left-prefix count map?", ["A parent position boundary into its left child's subsequence", "A value into its absolute array address", "An incident ID into a hash slot"], "The count of left-routed items before a parent boundary gives the corresponding boundary in the stable left subsequence."),
    ("How are duplicate readings treated in wavelet select?", ["Each occurrence occupies its own sorted ordinal", "Duplicates are removed during construction", "Only the first occurrence can be selected"], "A subarray is a multiset of occurrences, so equal values may fill several adjacent sorted positions."),
    ("What happens if a latency changes after building this wavelet index?", ["The partitions and prefix counts must be rebuilt or updated by a different design", "Only the root minimum needs changing", "The existing index updates itself on list mutation"], "This implementation copies routed values into static node summaries and does not expose a point-update operation."),
    ("What does a parity disjoint set store on each parent link?", ["XOR relation between the member and its parent", "An absolute label for the whole graph", "The number of accepted edges"], "Composing XOR bits along the find path gives each member's relative binary label at the component leader."),
    ("When must a new parity constraint be rejected?", ["Its two members already share a leader but their implied relation conflicts", "Its members are in separate components", "It asks for two members to be the same"], "A same-component request can be checked against existing parity; merging separate components can satisfy either binary relation."),
    ("Why does ordinary parity union-find not handle edge deletion?", ["Merged parent paths keep implications from removed constraints", "It cannot handle unknown asset IDs", "Path compression prevents all future additions"], "Deletion may split a component or remove an implied relationship, but the accepted union history is not undone by this structure."),
    ("What defines in-order position in an implicit treap?", ["The size of each left subtree", "Lexical order of task IDs", "Priority alone"], "A node's position follows all nodes in its left subtree, regardless of payload values or heap priority."),
    ("Why does a range reversal first split the sequence?", ["It isolates the requested middle interval for one lazy flag", "It sorts the interval before reversing", "It discards tasks outside the range"], "Two splits separate the prefix, target range, and suffix; the middle root can then carry a deferred reversal."),
    ("Which bound does random-priority treap editing provide?", ["Expected O(log N), with O(N) worst-case height possible", "Guaranteed O(1) for every edit", "Guaranteed O(log N) for every priority assignment"], "Independent priorities give expected shallow height, but an unlucky or adversarial shape can still form a long path."),
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
            title="Sparse sums, quantiles, parity, and sequence edits",
            summary="Check coordinate paths, subarray ordinals, XOR constraints, and lazy reversals.",
            sort_order=41660, created_at=stamp, updated_at=stamp, published_at=stamp)
quiz["data"].update(duration_minutes=20, related=[{"path": path, "title": by_path[path]["title"]} for path in new_paths + [project_path]], questions=balanced)
quiz["body"] = "<p>Read each operation contract before selecting an answer. Bounds, duplicate readings, discarded constraints, and pending reversals change the result.</p><h2>Lessons</h2>" + links(new_paths) + "<h2>Design exercise</h2>" + links([project_path, subject_root])
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
    ("dsa/avl-subtree-size-rank-select", new_paths[1]),
    ("dsa/disjoint-set-union-connectivity", new_paths[2]),
    ("dsa/persistent-ordered-index-path-copying", new_paths[3]),
):
    old = by_path[old_path]
    old["body"] += '<p><a href="/' + new_path + '">' + html.escape(by_path[new_path]["title"]) + "</a> extends this operation contract.</p>"
    old["updated_at"] = stamp
for path in new_paths:
    entry = by_path[path]
    entry["body"] += '<p>Apply the invariant in the <a href="/' + project_path + '">sparse readings and task constraints project</a>, then check the <a href="/' + quiz_path + '">operations quiz</a>.</p>'
    entry["updated_at"] = stamp

fixture.write_text(json.dumps(entries, ensure_ascii=False, indent=2) + "\n")
print(json.dumps({"lessons": new_paths, "project": project_path, "quiz": quiz_path, "questions": len(questions)}))
