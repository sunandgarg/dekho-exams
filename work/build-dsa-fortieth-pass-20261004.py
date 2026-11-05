"""Add four distinct DSA tutorials, an audit project, and a contract quiz."""

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
subject = "dsa/dsa-tutorial-learn-data-structures-and-algorithms"
stamp = datetime.datetime.now(datetime.UTC).isoformat()


def links(paths):
    return "<ul>" + "".join('<li><a href="/' + path + '">' + html.escape(by_path[path]["title"]) + "</a></li>" for path in paths) + "</ul>"


lessons = [
    dict(path="dsa/persistent-range-mex-last-occurrence-index", program="persistent_range_mex_alerts.py",
         template="dsa/persistent-segment-tree-versioned-sums", section="dsa/range-query-structures",
         title="Persistent range MEX: search last occurrences in prefix versions",
         summary="Keep one segment-tree root per prefix and find the first value absent from a half-open range.",
         definition="The minimum excluded value, or MEX, of a range is its smallest nonnegative integer that does not occur there. This static index builds a persistent segment tree over candidate values from zero through N, where N is the array length. Version r records the last zero-based position at which each candidate appeared before array position r; unseen candidates hold minus one. A query over [l,r) inspects version r and descends toward the leftmost value whose last occurrence is less than l. Each internal node stores the minimum last occurrence in its value interval, so a whole child interval can be skipped when all its values occurred inside the requested range. Each update path-copies nodes and keeps previous roots unchanged. Negative values and values above N cannot affect the MEX of a length-at-most-N range and are ignored. The input array is frozen after construction; this is not an online point-update index.",
         case="For readings [0,3,1,0,2,7,1], the first five positions contain 0, 1, 2, and 3, so their MEX is 4. Positions [2,7) contain 1, 0, 2, 7, and 1; their MEX is 3. An empty range has MEX zero. The example builds eight prefix roots, including the empty prefix, even though only seven observations exist. Value 7 is tracked because the candidate domain is zero through seven, but it does not change these answers. A query must use root r, not root l, because root r holds the most recent occurrences before the right endpoint.",
         cost="Each eligible observation copies O(log N) nodes in its prefix version. Construction therefore costs O(N log N) time and O(N log N) retained nodes in the worst case, plus O(N) root references; ignored values reuse the preceding root. A valid range query follows one branch per value-tree level in O(log N) time and O(1) auxiliary space. The Python tuple representation adds object overhead and recursive construction uses O(log N) call depth. A direct scan with a temporary set costs O(range length) time and space and can be better for a few small queries. Persistence pays when many ranges in one immutable array need independent right-endpoint snapshots.",
         mistakes=["Do not search the version at the left endpoint instead of the right endpoint.", "Do not treat a last occurrence equal to l as absent from [l,r).", "Do not mutate nodes shared by earlier prefix roots.", "Do not assume values above the array length can change its range MEX."],
         related=["dsa/persistent-segment-tree-versioned-sums", "dsa/wavelet-matrix-static-rank-quantile", "dsa/verified-range-majority-candidates", "dsa/square-root-range-mode-readings", "dsa/segment-tree-range-sum-update", "dsa/coordinate-compression-ordered-ranks"]),
    dict(path="dsa/segment-tree-range-xor-linear-basis", program="range_xor_basis_shipments.py",
         template="dsa/segment-tree-range-sum-update", section="dsa/range-query-structures",
         title="Range XOR bases: merge linear spans in a segment tree",
         summary="Store binary linear bases per interval for subset-XOR maxima and reachability.",
         definition="A linear XOR basis stores independent bit vectors whose combinations span the same XOR results as its input values. Each nonzero vector is reduced from its highest set bit downward; an unoccupied pivot becomes a new basis vector, while an occupied pivot is XORed away. A segment tree stores such a basis for every array interval. Joining two nodes inserts every right basis pivot into a copy of the left basis, preserving the span of all values in their union. A half-open range query merges the O(log N) nodes covering that range, then greedily raises the answer by XORing pivots from high bit to low bit. The same range basis can test whether a target XOR is representable and report its linear rank. This model uses fixed-width unsigned shipment flags, supports point replacement, and treats duplicate values as separate inputs that may be linearly dependent.",
         case="For flags [47,29,61,83,19], the range [1,4) covers 29, 61, and 83. Its maximum subset XOR is 115, and the three values are independent at the configured width. The target 29 XOR 61 is representable because those two items may be selected. Replacing 61 with 37 changes the range maximum to 118; the empty range [4,4) contains only the empty subset, whose XOR is zero. A basis describes achievable XOR values, not which shipment IDs produce them. A user needing the witness subset would have to retain provenance through elimination, which this compact model does not do.",
         cost="Let B be the configured bit width. Inserting one value into a basis takes O(B) bit tests and XORs. Merging two bases may insert up to B pivots and costs O(B squared), giving O(N B squared) segment-tree construction time and O(NB) stored pivot cells. A range query visits O(log N) covering nodes and costs O(B squared log N), followed by O(B) for maximum or reachability. Point replacement rebuilds O(log N) ancestors at the same merge cost. B is twelve in the runnable program, so Python integers fit comfortably, but the stated bound keeps bit width explicit. A binary trie answers maximum XOR against one chosen query value; a range linear basis answers the maximum XOR of any subset in an interval.",
         mistakes=["Do not confuse maximum subset XOR with maximum XOR against one element.", "Do not count dependent duplicate vectors as extra rank.", "Do not reuse a parent basis after one leaf changes.", "Do not accept flags outside the fixed bit width."],
         related=["dsa/binary-trie-maximum-xor-multiset", "dsa/segment-tree-range-sum-update", "dsa/persistent-segment-tree-versioned-sums", "dsa/static-xor-filter-membership", "dsa/wavelet-matrix-static-rank-quantile", "dsa/ordered-treap-split-join-rank"]),
    dict(path="dsa/lazy-segment-tree-affine-range-sums", program="affine_range_sensor_sums.py",
         template="dsa/lazy-segment-tree-range-add-minimum", section="dsa/range-query-structures",
         title="Affine lazy segment trees: compose range calibration before summing",
         summary="Apply multiply-and-add corrections in order and answer modular range sums.",
         definition="An affine range update replaces every reading x in [l,r) with a*x+b under a fixed modulus. A segment-tree node stores its interval sum and one pending affine transformation for children that have not yet been visited. Applying a new transformation to a node of length k changes its sum to a*sum+b*k. If the node already carries an older pending transformation x maps to m*x+c, then the new pending pair becomes a*m and a*c+b; reversing that composition gives wrong results when updates overlap. Before a partial update or query descends, the pending transform is pushed to both children and reset to the identity pair (1,0). This model requires a nonempty fixed array, supports negative multipliers by reduction modulo the configured modulus, and uses half-open ranges. It does not expose min, max, or assignment as separate operations, although assignment can be represented by multiplier zero.",
         case="Start with readings [47,19,61,29,83] modulo 1009. Applying x maps to 3x+7 over positions [1,4) gives a total sum of 478, of which the transformed middle interval contributes 348. Applying x maps to 2x+5 over [2,5) next raises the total to 860, and the final three positions sum to 749. The second update overlaps two earlier corrected readings, so its pending transformation must be composed after the first. An empty range has sum zero and an empty update makes no change. The modulus is part of the stored arithmetic contract; changing it after construction would invalidate every cached sum and pending pair.",
         cost="A full-cover update changes one node in O(1), while a partial range visits O(log N) boundary paths and a bounded number of covered nodes, so each update and range-sum query costs O(log N) time. The tree and two pending arrays use O(N) space, and recursion uses O(log N) call depth. Values are always reduced modulo the configured modulus; this does not preserve an unreduced physical reading. A plain prefix-sum array answers static sums faster but cannot repair overlapping calibration ranges without rebuilding later prefixes. An ordinary range-add lazy tree needs only one pending offset; affine updates need both multiplier and addend in the right composition order.",
         mistakes=["Do not reverse the order of old and new affine transformations.", "Do not forget the addend times interval length in a node sum.", "Do not descend with a stale pending transform on the parent.", "Do not compare a modular sum with an unreduced real-world total."],
         related=["dsa/lazy-segment-tree-range-add-minimum", "dsa/segment-tree-range-sum-update", "dsa/segment-tree-beats-range-cap-sum", "dsa/two-dimensional-segment-tree-heat-grid", "dsa/disjoint-sparse-table-range-sum", "dsa/two-stack-sliding-window-aggregation"]),
    dict(path="dsa/min-max-heap-double-ended-dispatch", program="min_max_heap_dispatch_priorities.py",
         template="dsa/binary-heap-priority-scheduling", section="dsa/trees-and-heaps",
         title="Min-max heaps: remove either end of one dispatch priority array",
         summary="Alternate min and max levels so both extremes stay at the top of one complete tree.",
         definition="A min-max heap is one complete binary tree stored in an array. Its root is a minimum level; children are maximum level; grandchildren return to minimum level, and the pattern alternates. Every minimum-level node is no greater than its descendants, while a maximum-level node is no smaller. The global minimum is at the root. The global maximum is among its two children. Insertion compares the new key with its parent, then bubbles along grandparents of the appropriate level. Removing an extreme replaces its slot with the last array item and trickles through children or grandchildren; a grandchild swap may need a parent correction to preserve the opposite-level order. Duplicate priorities are allowed and one instance is removed at a time. The model offers both extremes, not arbitrary removal, keyed decrease-priority, or stable first-in-first-out order among ties.",
         case="Insert priorities 47, 19, 61, 29, 83, 37, and another 47. The minimum is 19 and the maximum is 83. Removing one of each leaves five entries with minimum 29 and maximum 61. The two 47 entries remain distinct array items even though their values compare equal. A pop from an empty queue returns no value, and a one-item queue reports the same key as both ends. When removing a maximum from one of the root's children, the last item may be smaller than the root; the implementation exchanges them before max-level trickling so the minimum-level rule remains intact. Array positions are transient after any insertion or removal.",
         cost="The two extremes are found in O(1) time, and insertion or either pop moves along O(log N) levels. Trickle-down examines at most six descendants per visited node, so the work per level is bounded. The array uses O(N) space and no second synchronized heap or tombstone map. This program inserts items one at a time, costing O(N log N) to build from N priorities; it does not implement the separate linear-time bulk-heapify method. A two-heap double-ended queue can offer the same endpoint operations with stale-entry bookkeeping, while this one maintains one alternating-level array. For stable ties or ID-based updates, add an explicit payload and handle policy.",
         mistakes=["Do not apply a normal min-heap sift to maximum levels.", "Do not forget to repair the opposite-level parent after a grandchild swap.", "Do not claim equal priorities preserve insertion order.", "Do not call array positions durable handles after a pop."],
         related=["dsa/binary-heap-priority-scheduling", "dsa/dual-heap-double-ended-priority-queue", "dsa/indexed-binary-heap-decrease-key", "dsa/dary-heap-stable-priority-dispatch", "dsa/pairing-heap-two-pass-meld", "dsa/leftist-heap-null-path-meld"]),
]

for number, lesson in enumerate(lessons):
    path = lesson["path"]
    assert path not in by_path
    program = (root / "work/dsa-programs" / lesson["program"]).read_text().rstrip()
    output = subprocess.run([sys.executable, "-c", program], capture_output=True, text=True, check=True).stdout.strip()
    related = [lesson["section"], subject, *lesson["related"], "dsa/projects", "dsa/quizzes"]
    body = "<p>" + html.escape(lesson["definition"]) + "</p>"
    body += "<h2>Operational case</h2><p>" + html.escape(lesson["case"]) + "</p>"
    body += '<h2>Working Python program</h2><pre><code class="language-python">' + html.escape(program, quote=False) + "</code></pre>"
    body += '<h3>Output</h3><pre><code class="language-text">' + html.escape(output) + "</code></pre>"
    body += "<h2>Time, space, and tradeoff</h2><p>" + html.escape(lesson["cost"]) + "</p>"
    body += "<h3>Common Mistakes</h3><ul>" + "".join("<li>" + html.escape(item) + "</li>" for item in lesson["mistakes"]) + "</ul>"
    body += "<h2>Connected lessons</h2>" + links(related)
    entry = copy.deepcopy(by_path[lesson["template"]])
    entry.update(id=str(uuid.uuid5(uuid.NAMESPACE_URL, "aitrove:" + path)), path=path, title=lesson["title"],
                 summary=lesson["summary"], body=body, sort_order=47000 + 10 * number,
                 created_at=stamp, updated_at=stamp, published_at=stamp)
    entry["data"].update(section_path=lesson["section"],
                         related=[{"path": target, "title": by_path[target]["title"]} for target in related])
    entries.append(entry)
    by_path[path] = entry
    for hub_path in (lesson["section"], subject):
        hub = by_path[hub_path]
        module = hub["data"]["modules"][0] if hub_path == lesson["section"] else next(
            module for module in hub["data"]["modules"] if module["title"] == by_path[lesson["section"]]["title"])
        module["lessons"].append(path)
        hub["body"] += '<p><a href="/' + path + '">' + html.escape(lesson["title"]) + "</a></p>"
        hub["updated_at"] = stamp

paths = [lesson["path"] for lesson in lessons]
project_path = "dsa/range-mex-xor-affine-priority-audit-project"
quiz_path = "quizzes/dsa-range-mex-xor-affine-priority-contracts"
project = copy.deepcopy(by_path["dsa/allocation-ownership-coalescing-audit-project"])
project.update(id=str(uuid.uuid5(uuid.NAMESPACE_URL, "aitrove:" + project_path)), path=project_path,
               title="Project: audit range MEX, XOR spans, calibration sums, and priority ends",
               summary="Compare four different query and mutation contracts with direct models.",
               sort_order=47050, created_at=stamp, updated_at=stamp, published_at=stamp)
project["data"].update(reading_minutes=35,
                       related=[{"path": path, "title": by_path[path]["title"]} for path in paths])
project["body"] = "<p>A dispatch report asks four unrelated questions over numbered observations. Which nonnegative code is absent from a historical range? What is the greatest XOR achievable by a subset of shipment flags? What is a corrected sensor sum after overlapping multiply-and-add calibrations? Which current dispatch job has the lowest or highest priority? Use a persistent last-occurrence index, a segment tree of binary linear bases, an affine lazy segment tree, and a min-max heap respectively. Keep each result's domain and update policy separate: the first array is immutable, the XOR tree replaces points, the calibration tree transforms ranges under one modulus, and the heap mutates by inserting or removing its extremes.</p>"
project["body"] += "<h2>Acceptance trace</h2><p>For [0,3,1,0,2,7,1], require MEX four on [0,5) and three on [2,7). On flags [47,29,61,83,19], require maximum subset XOR 115 for [1,4), then replace 61 with 37 and require 118. On readings [47,19,61,29,83] modulo 1009, apply x maps to 3x+7 over [1,4), then x maps to 2x+5 over [2,5), and require total 860. Finally insert seven dispatch priorities with both 47 values retained; pop 19 and 83 and require 29 and 61 as the remaining endpoints. Compare every result with direct enumeration or arithmetic before accepting the index output.</p>"
project["body"] += "<h2>Failure and cost review</h2><p>Test empty and single-item MEX windows and confirm an earlier root does not change after later prefix versions are built. For short XOR ranges, enumerate all subsets and compare both maximum and representability, including duplicate and zero flags. Compose affine updates in both orders on an overlapping region to prove order matters; test multiplier zero as assignment. Mix heap insertion with both endpoint removals and compare its multiset with a sorted list after every operation. Record the range query costs separately rather than claiming one universal logarithmic index. Reject unsupported point edits to the frozen MEX array and out-of-width XOR flags.</p>"
project["body"] += "<h3>Common Mistakes</h3><ul><li>Do not query a MEX from the wrong prefix version.</li><li>Do not count a dependent XOR vector as a new pivot.</li><li>Do not reverse affine composition over an overlap.</li><li>Do not treat min-max heap positions as stable job handles.</li></ul>"
project["body"] += "<h2>Connected lessons</h2>" + links(paths + ["dsa/projects", "dsa/quizzes", subject])
entries.append(project)
by_path[project_path] = project

raw = [
    ("Which prefix version answers MEX over [l,r)?", "The version built after the first r values", "The version before l", "The final version for every range", "The right-endpoint root stores the latest occurrence of each candidate before r, which can be compared with l."),
    ("When is a candidate value absent from [l,r)?", "Its last occurrence before r is less than l", "Its last occurrence equals l", "Its numeric value exceeds r", "A last occurrence inside the half-open interval begins at l, so only positions strictly below l establish absence."),
    ("Why can values above N be ignored for MEX in an N-item array?", "An interval of length at most N always misses something from zero through N", "They are stored in every tree node", "They must all be negative", "The N plus one candidates from zero to N cannot all occur in a range containing at most N array positions."),
    ("What does a range XOR basis describe?", "Every XOR obtainable from subsets of values in the interval", "Only the XOR of all values together", "The nearest stored flag to a query", "Independent pivots span precisely the same binary-vector combinations as the interval's original values."),
    ("What does a dependent duplicate vector do to rank?", "It adds no new pivot", "It doubles the rank", "It changes the maximum by itself", "A duplicate reduces to zero against its existing pivot, so the represented span and its dimension stay unchanged."),
    ("What must happen after point replacement in a basis segment tree?", "Rebuild bases on ancestors of that leaf", "Change only the leaf and keep parent bases", "Rebuild every source array position", "Parent nodes represent merged child spans, so they must be recomputed along the path from the changed leaf to the root."),
    ("How does a full-cover affine update change a node sum?", "Multiply the old sum and add the offset times interval length", "Add the offset only once", "Multiply only the first reading", "Every one of the node's readings receives the addend, contributing its interval length times that addend to the sum."),
    ("How do new and old pending affine transforms compose?", "Apply the old transform first, then the new transform", "Apply the new transform first, then the old", "Discard the old transform on overlap", "A newly requested correction acts on values already affected by the older pending correction, fixing multiplier and addend order."),
    ("What pending pair represents no calibration change?", "Multiplier one and addend zero", "Multiplier zero and addend one", "Multiplier zero and addend zero", "The identity mapping x to x uses a multiplier of one and an addend of zero under any valid modulus."),
    ("Where is the minimum in a min-max heap?", "At the root minimum level", "In whichever leaf was most recently inserted", "At the larger root child", "The alternating order makes the root no greater than its descendants, so it always contains a minimum item."),
    ("Where can the global maximum be found?", "Among the root's at most two children", "Only by scanning every leaf", "At the root with the minimum", "The root children lie on a maximum level and dominate their descendant subtrees, so one of them holds the largest key."),
    ("Does equal priority imply stable FIFO removal?", "No, this heap orders by numeric priority alone", "Yes, the array records insertion time", "Only after a priority decrease", "The structure stores numeric priorities without a tie sequence, so equal keys have no preserved arrival-order contract."),
]
questions = []
for number, (prompt, correct, wrong_one, wrong_two, explanation) in enumerate(raw):
    assert len(explanation) >= 60
    answer = number % 3
    options = [wrong_one, wrong_two]
    options.insert(answer, correct)
    questions.append({"prompt": prompt, "options": options, "answer": answer, "explanation": explanation})
quiz = copy.deepcopy(by_path["quizzes/dsa-splay-and-resident-history-contracts"])
quiz.update(id=str(uuid.uuid5(uuid.NAMESPACE_URL, "aitrove:" + quiz_path)), path=quiz_path,
            title="Check range MEX, XOR spans, affine updates, and priority ends",
            summary="Twelve explained decisions about snapshots, linear bases, transform order, and heap levels.",
            sort_order=47060, created_at=stamp, updated_at=stamp)
quiz["data"].update(duration_minutes=20,
                    related=[{"path": path, "title": by_path[path]["title"]} for path in paths + [project_path]],
                    questions=questions)
quiz["body"] = "<p>Choose the supported range or endpoint contract for each structure. Check each answer against its runnable trace and the direct model described in the audit project.</p><h2>Lessons</h2>" + links(paths) + "<h2>Design exercise</h2>" + links([project_path, subject])
entries.append(quiz)
by_path[quiz_path] = quiz

for hub_path, destination in (("dsa/projects", project_path), ("dsa/quizzes", quiz_path)):
    hub = by_path[hub_path]
    hub["data"]["modules"][0]["lessons"].append(destination)
    hub["body"] += '<p><a href="/' + destination + '">' + html.escape(by_path[destination]["title"]) + "</a></p>"
    hub["updated_at"] = stamp
    root_module = next(module for module in by_path[subject]["data"]["modules"] if module["title"] == hub["title"])
    root_module["lessons"].append(destination)
    by_path[subject]["body"] += '<p><a href="/' + destination + '">' + html.escape(by_path[destination]["title"]) + "</a></p>"
    by_path[subject]["updated_at"] = stamp

for path in paths:
    entry = by_path[path]
    peers = [other for other in paths if other != path]
    entry["body"] += "<p>Compare this operation boundary with " + ", ".join(
        '<a href="/' + other + '">' + html.escape(by_path[other]["title"]) + "</a>" for other in peers)
    entry["body"] += ', then complete the <a href="/' + project_path + '">audit project</a> and <a href="/' + quiz_path + '">decision quiz</a>.</p>'
    entry["updated_at"] = stamp

for lesson in lessons:
    for old_path in lesson["related"][:2]:
        old = by_path[old_path]
        old["body"] += '<p><a href="/' + lesson["path"] + '">' + html.escape(lesson["title"]) + "</a> examines a related structure with a different operation boundary.</p>"
        old["updated_at"] = stamp

fixture.write_text(json.dumps(entries, ensure_ascii=False, indent=2) + "\n")
print(json.dumps({"lessons": 4, "projects": 1, "quizzes": 1, "new_routes": 6}))
