"""Add five distinct indexes, an audit project, and a contract quiz."""

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
    dict(path="dsa/successor-disjoint-set-retired-slots", program="successor_slots.py",
         template="dsa/disjoint-set-union-connectivity", section="dsa/graphs-and-disjoint-sets",
         title="Successor disjoint sets: skip permanently retired slots",
         summary="Link each retired slot to its next candidate and compress paths during allocation.",
         definition="A successor disjoint set tracks the first available integer slot at or after a requested index when slots can be retired permanently. Parent entries initially point to themselves. Retiring slot s redirects its parent to the first available slot after s; a find follows and compresses those forward links. A sentinel at capacity marks exhaustion. The representative has a required meaning—the next unretired slot—so an ordinary union-by-rank choice would be wrong unless an additional successor field preserved that meaning. A claim looks up the next slot and retires it in one operation. This is a monotone allocation structure: it cannot reopen a retired slot, release a claimed bay, or serve a growing domain without rebuilding.",
         case="Nine loading bays are numbered zero through eight. Reserve bays two, three, and six. Two claims starting at bay two return four and five; the next available bay from six is seven. Retiring three again returns false because it is already absent. A claim starting at eight returns eight, then the sentinel causes the next claim to return no bay. The index includes an addressable sentinel at nine, but that sentinel is never a usable bay. Path compression can make a repeated search cheap after traversing a long retired chain, yet it never restores a retired bay.",
         cost="Initialization writes N+1 parent entries in O(N) time and space. A single find or claim can follow O(N) forward links before compression, so this implementation does not promise worst-case constant time or the usual union-by-rank inverse-Ackermann bound. Compression shortens later traversals of those same chains. Retire performs one successor find plus a redirect and is idempotent here. A sorted set supports both retirement and reopening but pays logarithmic ordered operations; a fixed bitset can be simpler for a small dense universe. Choose this one-way index only when permanent disappearance is the actual contract.",
         mistakes=["Do not apply union by rank without preserving which representative is the successor.", "Do not return the capacity sentinel as an available slot.", "Do not advertise reopening when parents only move forward.", "Do not claim a worst-case constant-time find before compression."],
         related=["dsa/disjoint-set-union-connectivity", "dsa/van-emde-boas-bounded-successor", "dsa/sparse-set-bounded-identifiers", "dsa/first-fit-free-span-coalescing", "dsa/disjoint-interval-union-maintenance-windows", "dsa/fenwick-order-statistic-multiset"]),
    dict(path="dsa/persistent-range-distinct-last-position-count", program="persistent_distinct_incidents.py",
         template="dsa/persistent-range-mex-last-occurrence-index", section="dsa/range-query-structures",
         title="Persistent range-distinct counts: keep only the latest position active",
         summary="Query the prefix version at the right boundary and count active last occurrences inside a range.",
         definition="A persistent range-distinct index keeps one path-copied segment-tree root for each prefix of an immutable incident log. In version r, exactly the latest position before r of each seen code has marker one; earlier occurrences have marker zero. Appending a code clears its prior marker if it has one, sets the new position, and retains all older roots. A query over [l,r) reads root r and sums markers from l through r-1. Every distinct code present in that interval has a latest occurrence in the interval, and no code contributes twice. The tree indexes positions rather than values, so arbitrary hashable incident codes work without value compression. The source log is frozen after construction; an in-place correction would invalidate all later prefix versions.",
         case="The log [A-47,B-19,A-47,C-61,B-19,D-83] contains three distinct codes in [0,5) and four in [2,6). An empty [3,3) interval returns zero. In [1,4), B-19, A-47, and C-61 each contribute once, so the answer is three. Version five marks the latest B-19 at position four, which still lies inside [0,5); version three marks its older position one instead. Earlier roots remain valid for earlier right boundaries. Using the final root for every query can lose a code whose later duplicate lies to the right of the requested interval.",
         cost="The empty position tree occupies O(N) nodes for N log entries. Each appended code performs one or two path-copy point assignments, taking O(log N) time and new nodes, so construction is O(N log N) time and retained space. A range count costs O(log N) time and O(log N) recursive stack space. The last-position dictionary uses O(U) extra entries for U distinct codes. A direct set over a short interval costs O(length) time and space and may be preferable when queries are rare. This index counts distinct values, not their identities or frequencies, and has no append operation after its fixed-size tree is built.",
         mistakes=["Do not count every occurrence as one active marker.", "Do not query the final version when the requested right boundary is earlier.", "Do not clear a previous position in an older shared root.", "Do not call this mutable after preprocessing; later roots depend on earlier positions."],
         related=["dsa/persistent-range-mex-last-occurrence-index", "dsa/mo-offline-distinct-range-counts", "dsa/wavelet-matrix-static-rank-quantile", "dsa/persistent-subarray-kth-order-statistics", "dsa/merge-sort-tree-threshold-count", "dsa/hash-set-membership-and-order"]),
    dict(path="dsa/segment-tree-editable-substring-fingerprints", program="rolling_hash_alert_text.py",
         template="dsa/segment-tree-range-sum-update", section="dsa/range-query-structures",
         title="Editable substring fingerprints: join hashes in a segment tree",
         summary="Compare equal-length text spans after point replacements, with collisions stated explicitly.",
         definition="An editable substring fingerprint index stores a polynomial hash and character length for each segment-tree node. To join adjacent spans, multiply the left hash by a base raised to the right span length, then add the right hash modulo a fixed prime. This positional rule lets a query combine its covered nodes into a normalized fingerprint independent of where the substring begins. A point replacement rebuilds only the leaf-to-root path. The example maintains two modular hashes and checks equal lengths, making accidental agreement less likely than one hash but never impossible. A matching fingerprint is a candidate for equality, not a proof; a caller needing exact equality must compare the underlying characters after the hash test. Text length is fixed, and offsets count Unicode code points, not grapheme clusters.",
         case="The text dock47dock47 has two equal six-character halves and two equal four-character dock prefixes. Replacing the final 7 with 9 makes the six-character halves unequal; restoring 7 makes them match again. An empty span has length zero and zero hashes, while a requested span beyond the text boundary raises an error. The same hashes cannot identify which edit occurred or where it occurred. For security decisions, stored hash pairs alone are insufficient evidence of exact content identity, since distinct strings can collide under finite moduli.",
         cost="For N characters, building powers and tree summaries costs O(N) time and space. A point replacement or range fingerprint touches O(log N) nodes and uses O(log N) recursion stack space. Comparing two hashes costs O(log N), while verifying a matching pair against the actual text takes O(length) further time. The example does not retain an editable source string, so an exact verification layer must hold one separately. Hashing is useful for quickly rejecting unequal spans under frequent edits; it should not be described as a collision-free index or cryptographic integrity check.",
         mistakes=["Do not compare hashes of different lengths as if they represented equal strings.", "Do not omit the right-span power when joining two child hashes.", "Do not treat matching modular fingerprints as guaranteed equality.", "Do not promise insertion or deletion when the index only replaces characters."],
         related=["dsa/segment-tree-range-sum-update", "dsa/trigram-index-verified-substring-candidates", "dsa/suffix-array-lcp-incident-search", "dsa/suffix-automaton-online-substrings", "dsa/piece-table-text-editing", "dsa/immutable-rope-text-snapshots"]),
    dict(path="dsa/sliding-window-median-lazy-heap-expiry", program="sliding_median_dispatch.py",
         template="dsa/two-heap-running-median", section="dsa/trees-and-heaps",
         title="Sliding medians: expire heap entries by event identity",
         summary="Balance two heaps while old window members wait for lazy removal at heap tops.",
         definition="A sliding-median index keeps a max heap for the lower half and a min heap for the upper half of active observations. The lower heap has either the same number of live items as the upper heap or one extra, so its top is the lower median. An expiring observation may sit below the top; deleting it from a binary heap by search would cost linear time. Instead, mark its unique event ID as delayed, decrement the live-size counter for its recorded heap side, and discard the stale record when it reaches a top. Rebalancing moves one visible top across when live counts diverge and updates that event's side map. The stream wrapper removes the event that just left the fixed-width window. Equal values remain distinct because heap entries carry unique IDs.",
         case="Dispatch waits [47,19,61,29,83,37,19] yield lower medians [47,29,61,37,37] for width three. Width four yields [29,29,37,29], choosing the smaller of the two central sorted values. A stale value may remain in a heap array after its window exit, but it must not count toward balancing or become the reported median. Event IDs are never reused in this example; recycling an ID while an old stale record remains would make delayed-deletion bookkeeping ambiguous. A zero-width or wider-than-stream window is rejected.",
         cost="Across N arrivals, each arrival or expiry triggers at most one cross-heap move, and every heap record is eventually popped once, giving O(N log N) total heap work for the wrapper and O(log N) amortized work per arrival or expiry. A single call can pop many delayed records at once, so its worst-case latency can be O(N log N). Without periodic heap compaction, stale records and the set of seen IDs can occupy O(N) space even though only W events are live. A running-median heap without deletion cannot answer sliding windows correctly; a sorted multiset could instead maintain O(W) active memory with logarithmic edits.",
         mistakes=["Do not count a delayed heap record as a live member.", "Do not assume a removed item is always at a heap top.", "Do not reuse an event ID while old records may remain.", "Do not promise O(W) memory without a stale-record compaction policy."],
         related=["dsa/two-heap-running-median", "dsa/dual-heap-double-ended-priority-queue", "dsa/monotonic-deque-window-minimum", "dsa/fenwick-order-statistic-multiset", "dsa/indexed-binary-heap-decrease-key", "dsa/exponential-histogram-recent-failure-count"]),
    dict(path="dsa/ball-tree-exact-nearest-depot", program="ball_tree_depot_search.py",
         template="dsa/kd-tree-exact-nearest-depot", section="dsa/trees-and-heaps",
         title="Ball trees: prune exact nearest-depot search with radius bounds",
         summary="Group static coordinates inside nested metric balls and reject groups too far to win.",
         definition="A ball tree groups static points in recursively nested metric balls. Each node stores a center and radius that enclose all points beneath it. For a query point, the triangle inequality gives a lower distance bound: distance to the center minus the radius, floored at zero. If that bound exceeds the best depot distance found so far, the entire node can be skipped without losing an exact answer. This example uses Euclidean coordinates, chooses a split axis by largest spread, divides at the median, and checks every point only inside small leaves. Children are visited in lower-bound order so an early close depot can tighten pruning. This is a static nearest-neighbor structure; it neither inserts moved depots nor guarantees that every query avoids a full scan.",
         case="For six depots at (0,0), (4,1), (9,0), (4,7), (-3,5), and (10,8), the nearest to (5,2) is D-47 at distance about 1.414. The nearest to (8,1) is D-61 at the same rounded distance; near (0,4), D-29 wins at about 3.162. The tree compares real Euclidean distances and breaks equal-distance ties by depot ID. It reports three decimal places only for display. A node's center need not be one of the stored depots, and its radius is the farthest enclosed point from that center. Pruning on a center distance alone would be unsound.",
         cost="At each balanced level this Python builder sorts each subset along a selected axis, giving O(N log squared N) construction time in the worst case and O(N) retained nodes and points. A query may inspect all N points when balls overlap or bounds are weak; there is no universal logarithmic search guarantee. Each visited node computes a center distance, and recursion uses O(log N) depth for the median split. Keeping an exact leaf scan matters even after bound pruning. This model uses floating-point geometry with a small pruning tolerance; application code needing strict numerical guarantees must set a precision policy and test boundary cases.",
         mistakes=["Do not prune from center distance without subtracting the enclosing radius.", "Do not claim every ball-tree nearest query is logarithmic.", "Do not return a center as though it were a stored depot.", "Do not silently mix coordinate dimensions in one tree."],
         related=["dsa/kd-tree-exact-nearest-depot", "dsa/vantage-point-metric-nearest-depot", "dsa/bk-tree-edit-distance-label-search", "dsa/spatial-hash-grid-moving-points", "dsa/static-bvh-axis-aligned-box-overlap", "dsa/point-region-quadtree-range-report"]),
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
                 summary=lesson["summary"], body=body, sort_order=49000 + 10 * number,
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
project_path = "dsa/slot-distinct-text-median-ball-audit-project"
quiz_path = "quizzes/dsa-slot-distinct-text-median-ball-contracts"
project = copy.deepcopy(by_path["dsa/rank-burst-tariff-frequency-routing-audit-project"])
project.update(id=str(uuid.uuid5(uuid.NAMESPACE_URL, "aitrove:" + project_path)), path=project_path,
               title="Project: audit slot, distinct, text, median, and ball indexes",
               summary="Compare five operation boundaries with direct allocation, set, text, window, and distance models.",
               sort_order=49060, created_at=stamp, updated_at=stamp, published_at=stamp)
project["data"].update(reading_minutes=40,
                       related=[{"path": path, "title": by_path[path]["title"]} for path in paths])
project["body"] = "<p>Build five separate indexes for a dispatch console. Loading bays disappear permanently as they are claimed. Incident codes repeat in a frozen log, and reports ask for the count of distinct codes in selected intervals. A fixed-length alert string receives character replacements and needs fast candidate-equality checks. Dispatch waits slide through a fixed-width median window. Static depot coordinates need exact nearest lookup. The indexes have different ownership rules: successor links only move forward, prefix roots are immutable, text hashes can collide, expiring heap records may remain stale, and metric balls only prune when their distance bounds permit it.</p>"
project["body"] += "<h2>Acceptance trace</h2><p>Reserve bays two, three, and six in a nine-bay index, then claim from two twice to receive four and five. Count three distinct codes in the first five entries of [A-47,B-19,A-47,C-61,B-19,D-83]. In dock47dock47, the two six-character spans match until the final 7 is replaced by 9. For waits [47,19,61,29,83,37,19], width-three lower medians are [47,29,61,37,37]. For the six-depot coordinate set, (5,2) selects D-47. Validate each answer against a direct small-input model before relying on an index.</p>"
project["body"] += "<h2>Failure and cost review</h2><p>Exhaust a slot universe and confirm that its sentinel is never returned as a real bay. Query an empty distinct interval and an earlier prefix version after later duplicates appear. Replace and restore a text character, but do not call equal fingerprints a proof of exact identity. Force repeated wait values and expired entries buried in a heap; compare each window median with a sorted slice. Use overlapping depot balls and tied distances to exercise the exact leaf scan and deterministic tie rule. Record the worst-case cost as well as the common-case reason for each structure.</p>"
project["body"] += "<h3>Common Mistakes</h3><ul><li>Do not reopen a slot in a forward-only successor index.</li><li>Do not count an incident twice in a single range.</li><li>Do not treat a finite hash as collision-free.</li><li>Do not balance heaps using stale entries.</li><li>Do not prune a ball from its center distance alone.</li></ul>"
project["body"] += "<h2>Connected lessons</h2>" + links(paths + ["dsa/projects", "dsa/quizzes", subject])
entries.append(project)
by_path[project_path] = project

raw = [
    ("What does a successor parent represent after a bay is retired?", "The first still-available slot at or after that bay", "The oldest retired bay", "A rank-selected DSU root", "A retired slot redirects toward the next usable candidate; the capacity sentinel means no candidate remains in the fixed domain."),
    ("Why is ordinary union by rank unsafe for the simple successor index?", "It can choose a representative that is not the next available slot", "It always increases the bay capacity", "It reopens retired slots", "The representative has application meaning, so a size-selected root would need a separate successor field to preserve the query result."),
    ("Which version answers a distinct-count query over [l,r)?", "The prefix root after r log entries", "Only the root after l entries", "The final root for all ranges", "Root r marks each code's latest position before r, allowing a sum restricted to l through r minus one to count each present code once."),
    ("What happens to a code's old marker when that code reappears?", "The new root clears the old marker and sets the new position", "Every old root is edited in place", "Both markers remain one", "Path copying changes only the new prefix version, keeping older roots valid while exactly one latest position per code stays active."),
    ("How are adjacent substring hashes joined?", "Multiply the left hash by a power for the right length, then add the right hash", "Add hashes without position adjustment", "Sort both character ranges", "Polynomial concatenation shifts every left character by the number of right characters, which requires the appropriate base power."),
    ("Does matching two modular fingerprints prove exact text equality?", "No; finite hashes can collide", "Yes, even across different lengths", "Only after a point replacement", "Two modular values greatly reduce accidental agreement but still have a finite output space, so exact decisions require character verification."),
    ("Why mark an expiring median entry for lazy deletion?", "It may be buried below the heap top", "Its value cannot be compared", "Both heaps must be rebuilt on every expiry", "A binary heap has no cheap search-based deletion for a buried item, so its unique ID is ignored until the record reaches a removable top."),
    ("Which median does the example return for even window width?", "The lower of the two central sorted values", "Their arithmetic mean", "The upper central value", "The lower heap holds the same number of live items as the upper heap, and its maximum is the specified lower median."),
    ("Can one lazy-pruning call have a large worst-case cost?", "Yes; many expired records may reach the top together", "No; it always removes exactly one record", "Only when the input contains no duplicates", "Delayed heap entries accumulate below active tops, so a later call can remove a long chain even though aggregate work stays bounded."),
    ("What lower bound does a ball tree use for a node?", "Center distance minus enclosing radius, floored at zero", "Center distance by itself", "Distance to the first inserted depot", "The triangle inequality guarantees every enclosed point is at least center distance minus radius from the query."),
    ("When may an exact nearest search prune a ball node?", "Its lower bound exceeds the best complete point distance found", "Its center is not the nearest stored depot", "Its node has more than two points", "Only a bound above the current verified best distance proves that no point inside that node can improve the answer."),
    ("What is the nearest-query worst case for overlapping balls?", "A scan of all stored points", "Guaranteed constant time", "Exactly one leaf regardless of geometry", "Weak or overlapping bounds may fail to reject any subtree, leaving the exact search to inspect every leaf point."),
]
questions = []
for number, (prompt, correct, wrong_one, wrong_two, explanation) in enumerate(raw):
    assert len(explanation) >= 60
    answer = number % 3
    options = [wrong_one, wrong_two]
    options.insert(answer, correct)
    questions.append({"prompt": prompt, "options": options, "answer": answer, "explanation": explanation})
quiz = copy.deepcopy(by_path["quizzes/dsa-rank-burst-tariff-frequency-routing-contracts"])
quiz.update(id=str(uuid.uuid5(uuid.NAMESPACE_URL, "aitrove:" + quiz_path)), path=quiz_path,
            title="Check successor, distinct, text, median, and ball contracts",
            summary="Twelve explained decisions about five different mutable or static indexes.",
            sort_order=49070, created_at=stamp, updated_at=stamp)
quiz["data"].update(duration_minutes=20,
                    related=[{"path": path, "title": by_path[path]["title"]} for path in paths + [project_path]],
                    questions=questions)
quiz["body"] = "<p>Choose the supported operation and its failure boundary for each index. The cases separate permanent retirement, immutable prefix roots, probabilistic fingerprints, delayed heap expiry, and metric pruning.</p><h2>Lessons</h2>" + links(paths) + "<h2>Design exercise</h2>" + links([project_path, subject])
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
print(json.dumps({"lessons": 5, "projects": 1, "quizzes": 1, "new_routes": 7}))
