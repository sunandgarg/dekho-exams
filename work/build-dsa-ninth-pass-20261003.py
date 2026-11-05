"""Add four advanced search and streaming structures to local DSA fixtures."""

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
        "path": "dsa/aho-corasick-failure-linked-alert-index",
        "program": "aho_corasick_alert_index.py",
        "title": "Failure-linked tries: find overlapping alert terms in one scan",
        "summary": "Build a multi-pattern trie, follow suffix failures, and emit every matching term.",
        "section": "dsa/trees-and-heaps",
        "definition": "A failure-linked trie indexes several fixed search terms so one pass through a message can report all of them. Each trie node stores character edges, a fallback state for the longest suffix that is also a term prefix, and term IDs that end at that state. A breadth-first build assigns fallbacks from shorter prefixes outward. During scanning, a missing edge follows failures until another edge or the root applies. Output lists inherited from the failure state preserve suffix matches and overlapping terms; skipping that inheritance silently loses valid hits. This implementation rejects empty and duplicate terms, keeps matching case-sensitive, and reports offsets in Python Unicode code points.",
        "case": "The alert index contains heat, eat, and seal. Scanning overheat seal heat reports heat beginning at offset 4 and eat at 5, seal at 9, and the two overlapping heat/eat matches again near the end. One input character can complete several indexed terms. The resulting pairs are ordered by ending position and then by the terms stored on that state; they are not necessarily sorted by starting offset. The term set is immutable after construction, which matters because adding a term would require rebuilding failure links and inherited output lists.",
        "cost": "Let M be the total term length, H the longest term, N the message length, and Z the number of reported matches. This sparse-edge builder uses O(M) trie nodes but may walk up to H failure links while assigning an edge, so a conservative construction bound is O(MH + R) time, where R counts inherited output references. Stored output lists can also reach O(M + R) space. Once built, scanning takes O(N + Z) amortized time: each fallback reduces the active prefix depth, while each character can increase it by at most one. Holding the returned match list takes O(Z) space. Large term sets with many suffix relationships can make output storage substantial; consider streaming matches when result volume is high.",
        "mistakes": ["Do not discard matches inherited through a failure link.", "Do not assume one character can end only one term.", "Do not call code-point offsets UTF-8 byte positions.", "Do not mutate the term set without rebuilding the failure graph."],
        "related": ["dsa/trie-prefix-index-and-terminal-flag", "dsa/compressed-trie-edge-splitting", "dsa/compressed-trie-deletion-and-merge"],
    },
    {
        "path": "dsa/suffix-array-lcp-incident-search",
        "program": "suffix_array_incident_index.py",
        "title": "Suffix arrays: indexed substring search and adjacent LCP",
        "summary": "Sort suffix offsets by rank doubling and compute common-prefix lengths in one pass.",
        "section": "dsa/trees-and-heaps",
        "definition": "A suffix array stores the start offsets of every suffix of an immutable text in lexicographic order. This implementation ranks one-character prefixes, then repeatedly sorts suffixes by the ranks of two adjacent blocks; doubling the block width distinguishes longer prefixes until every suffix has a unique rank. A separate linear pass records the longest common prefix of each suffix and its immediate predecessor in sorted order. Two binary searches bound the run of suffixes whose first characters equal a nonempty query pattern. The returned offsets retain suffix order, which differs from left-to-right text order.",
        "case": "The incident text is valve alert valve. The pattern valve occurs at offsets 12 and 0, and the suffix array returns 12 first because the short suffix valve sorts before the longer suffix starting at 0. Alert occurs at offset 6. The suffix at 0 and the preceding suffix share the five-character prefix valve, so its adjacent LCP value is 5. The index does not record document boundaries or support inserts into the middle of the text; a changed message requires a new build.",
        "cost": "For text length N, each prefix-doubling round sorts N integer rank pairs in O(N log N) time, and there are O(log N) rounds, giving O(N log² N) construction time here and O(N) index arrays beyond the original text. The LCP pass is O(N) time and O(N) space. A pattern of length P takes O(P log N) time for two binary searches because each comparison slices up to P characters; returning Z matches adds O(Z) output space. The code does not use LCP to accelerate search. An empty pattern is rejected because reporting all N+1 insertion positions would be a different API contract.",
        "mistakes": ["Do not confuse suffix-array order with document offset order.", "Do not quote a linear build time for this rank-doubling and sorting implementation.", "Do not claim that computing LCP automatically accelerates the shown binary search.", "Do not reuse the index after changing the underlying text."],
        "related": ["dsa/trie-prefix-index-and-terminal-flag", "dsa/aho-corasick-failure-linked-alert-index", "dsa/sparse-table-immutable-range-minimum"],
    },
    {
        "path": "dsa/kd-tree-exact-nearest-depot",
        "program": "kd_tree_nearest_depot.py",
        "title": "K-d trees: exact nearest depot with plane pruning",
        "summary": "Build a balanced two-dimensional point tree and prune only when the split plane is too far.",
        "section": "dsa/trees-and-heaps",
        "definition": "A two-dimensional k-d tree partitions points by alternating east and north coordinates. This static builder sorts each subproblem on its active axis and stores a median as the node, yielding a balanced shape for its input set. An exact nearest query descends the side containing the target first. It may skip the other side only when the squared distance to the splitting plane is strictly greater than the best squared point distance already found. Equal plane distance must still be explored because a point there can win a deterministic tie by depot ID. This program uses ordinary planar coordinates, not geodesic distance on Earth.",
        "case": "Depots D-19, D-47, and D-61 have planar coordinates (4, 9), (18, 7), and (12, 22). A request at (16, 9) selects D-47 with squared distance 8. A request at (5, 8) selects D-19 with squared distance 2. Squared distances avoid a square-root operation and preserve nearest ordering. Depot IDs break equal-distance ties. The tree is built for a fixed point set; moving a depot without rebuilding would invalidate the partition boundaries used for pruning.",
        "cost": "Sorting every recursive subproblem costs O(N log² N) time in this simple median builder for N points. The tree stores O(N) nodes; sorting and slicing allocate additional temporary lists, and balanced recursion uses O(log N) stack depth. A nearest query often prunes many branches, but its guaranteed worst-case work is O(N) with O(log N) stack depth for this balanced static tree. Dimensionality, point distribution, and ties strongly affect pruning. For a frequently changing point set, a rebuild policy or a different spatial index is needed. The code's returned distance is squared planar distance, not travel time or road-network distance.",
        "mistakes": ["Do not prune the far side when the split-plane distance equals the best candidate distance and tie-breaking matters.", "Do not treat latitude and longitude as planar coordinates without an appropriate distance model.", "Do not promise logarithmic nearest-query time in the worst case.", "Do not move indexed points in place without rebuilding the tree."],
        "related": ["dsa/graph-adjacency-list-and-bfs", "dsa/stale-entry-heap-shortest-route", "dsa/interval-tree-max-endpoint-pruning"],
    },
    {
        "path": "dsa/count-min-sketch-frequency-boundary",
        "program": "count_min_event_sketch.py",
        "title": "Count-min sketches: bounded-memory event estimates",
        "summary": "Update several hash rows and take their minimum to estimate nonnegative counts.",
        "section": "dsa/hash-tables",
        "definition": "A count-min sketch stores a small matrix of counters instead of a key-to-count map. Recording a nonnegative event increments one hashed column in every row; estimating a key returns the minimum of those row counters. Any collision contributes extra count, so under positive-only updates the estimate cannot fall below the true count represented by the sketch. It can overestimate. This example uses personalized, deterministic cryptographic hashes to give repeatable columns, but it does not establish a formal probabilistic error bound from a universal hash family. The sketch itself does not store keys or identify which event codes are present.",
        "case": "A compact four-row, 47-column sketch records bay-hot seven times and gate-open three times. Their estimates print 7 and 3 for this particular state; another event code can collide and return a positive estimate even if it was never recorded. Increasing width lowers collision pressure at a memory cost. Increasing depth takes more updates and hash work, while a minimum across rows helps avoid a collision in every row. The simple API rejects zero or negative amounts, so subtraction and deletion are outside its guarantee.",
        "cost": "With D rows and W columns, the counter matrix uses O(DW) space independent of the number of distinct event codes. Record and estimate perform D hash computations over a code of length K, costing O(DK) time here, plus O(D) counter operations. Initialization touches O(DW) counters. Exact counts would require a separate map, which may grow with distinct keys; this sketch trades accuracy for fixed memory. Overflow is limited only by Python integer memory in this implementation. Practical deployments must choose width, depth, hash family, counter representation, merge compatibility, and an error policy from their workload rather than assuming the sample's exact printed estimates generalize.",
        "mistakes": ["Do not interpret a nonzero estimate as proof the key was recorded.", "Do not subtract counts from this positive-only sketch and keep the no-underestimate claim.", "Do not claim a formal probability bound from arbitrary deterministic row hashes.", "Do not combine sketches with different dimensions or hash conventions as if their cells aligned."],
        "related": ["dsa/bloom-filter-membership-boundary", "dsa/hash-map-collision-and-load-contract", "dsa/sparse-set-bounded-identifiers"],
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
                 body=body, sort_order=41400 + order * 10, created_at=stamp, updated_at=stamp, published_at=stamp)
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
