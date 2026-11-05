"""Build seven independent Data Structures lessons and connected draft exercises."""

import copy
import datetime
import html
import json
import subprocess
import sys
import uuid
from pathlib import Path

root = Path(__file__).resolve().parents[1]
fixture_path = root / "src/data/fixtures.json"
entries = json.loads(fixture_path.read_text())
by_path = {entry["path"]: entry for entry in entries}
subject_root = "dsa/dsa-tutorial-learn-data-structures-and-algorithms"
stamp = datetime.datetime.now(datetime.UTC).isoformat()


def links(paths):
    return "<ul>" + "".join(
        '<li><a href="/' + path + '">' + html.escape(by_path[path]["title"]) + "</a></li>"
        for path in paths
    ) + "</ul>"


lessons = [
    dict(path="dsa/ordered-treap-split-join-rank", program="ordered_treap_split_join.py",
         template="dsa/implicit-treap-range-reversal", section="dsa/trees-and-heaps",
         title="Ordered treaps: split, join, and select depot keys",
         summary="Preserve search order and heap priorities while dividing or joining ordered key ranges.",
         definition="An ordered treap keeps binary-search order by integer key and max-heap order by an independently assigned priority. Split partitions a tree around a boundary, reattaching only nodes on one search path. Join consumes two trees whose every left key is below every right key; it keeps the higher-priority root and recursively joins one child. Each node caches its subtree size, allowing zero-based select to choose a key by rank. The sample assigns priorities from a fixed seed solely to make the trace repeatable. A deployed randomized treap should draw priorities independently and protect the generator and state according to its concurrency needs. Split and join mutate their input nodes; callers cannot keep treating old roots as intact snapshots. Duplicate keys are ignored, and the integer-key removal uses a key-plus-one boundary.",
         case="Insert depot keys 61, 19, 83, 47, and 29. Splitting at 47 produces [19,29] and [47,61,83]; joining those two returns the same ordered set. Remove key 61, then selecting zero-based position two returns 47. If the caller reverses the join arguments, the binary-search invariant is broken even though heap priorities may appear plausible. The size cache must be repaired after every changed child pointer or rank results silently drift. A duplicate insertion must not add another node under the same key. The example never accepts arbitrary string keys because removal's successor boundary is defined using integer addition.",
         cost="For independent random priorities, expected tree height is O(log N), so search, split, join, insert, remove, and select take expected O(log N) time and O(log N) recursive stack space. An unlucky priority sequence can make height O(N) and can exceed Python's recursion limit; no deterministic balancing guarantee is claimed. The N nodes and size fields use O(N) space. This is a mutable ordered set, while an implicit treap keys by sequence position and a persistent ordered tree copies paths instead of consuming roots. If a workload needs strict worst-case height, an AVL or red-black tree has a different repair contract.",
         mistakes=["Do not join trees whose key ranges overlap or arrive in the wrong order.", "Do not reuse a consumed split root as an unchanged version.", "Do not forget to repair subtree sizes after pointer changes.", "Do not call expected logarithmic height a worst-case guarantee."],
         related=["dsa/implicit-treap-range-reversal", "dsa/persistent-ordered-index-path-copying", "dsa/avl-subtree-size-rank-select"]),
    dict(path="dsa/span-skip-list-rank-select", program="span_skiplist_rank_select.py",
         template="dsa/skip-list-ordered-index", section="dsa/trees-and-heaps",
         title="Span skip lists: rank and select without a full scan",
         summary="Count bottom-level links crossed by each express pointer to support ordered positions.",
         definition="A rank-aware skip list augments every forward pointer with a span: the number of bottom-level nodes that pointer crosses. Search still descends from higher express levels. During insertion, the predecessor path records how many entries were passed; the new node divides each affected span, while unaffected higher pointers gain one. Removal reverses those changes and can shrink empty top levels. Rank counts keys strictly less than a target; select follows spans until the requested zero-based position is reached. The sample rejects duplicate IDs, seeds a local random generator for reproducible heights, and caps tower height at twenty. The cap is a practical bound on stored levels, not a proof that a long list remains logarithmic after it is exceeded.",
         case="Insert alert IDs 61, 19, 83, 47, and 29. Exactly two IDs lie below 47, and position two selects 47. Removing 29 leaves [19,47,61,83]; rank and select must reflect the shorter bottom chain even when the removed node had no express-level pointers. A span on a pointer leading to an empty successor can still matter during an insertion at the end of the list. Updating only pointers that directly referenced a removed node leaves higher spans stale. The list is an ordered set of unique integer IDs and does not preserve insertion order for equal keys because equal keys are refused.",
         cost="With independent coin-flip heights and a cap large enough for the list, search, insertion, removal, rank, and select have expected O(log N) work; each can take O(N) in an unlucky arrangement. Space is O(N) expected pointers and spans plus the fixed-height head. The example allocates O(H) temporary predecessor and rank arrays for maximum height H on each mutation. A basic skip list without spans can find keys quickly but must scan level zero to select an arbitrary rank. A Fenwick frequency array handles ranked integers over a fixed domain, whereas this index orders keys without allocating that whole domain.",
         mistakes=["Do not update only a removed node's own pointer levels; higher spans also change.", "Do not mix zero-based select with one-based span distance.", "Do not accept duplicate keys without defining multiset rank semantics.", "Do not claim strict logarithmic bounds from randomized towers."],
         related=["dsa/skip-list-ordered-index", "dsa/fenwick-order-statistic-multiset", "dsa/avl-subtree-size-rank-select"]),
    dict(path="dsa/two-dimensional-segment-tree-heat-grid", program="segment_tree_2d_heat_grid.py",
         template="dsa/two-dimensional-fenwick-rectangle-sums", section="dsa/range-query-structures",
         title="Two-dimensional segment trees: correct sensors and sum rectangles",
         summary="Nest column aggregates inside row nodes for mutable half-open rectangle sums.",
         definition="A two-dimensional segment tree stores a column-sum tree at every node of an outer row tree. Leaf rows hold source cell values; internal row nodes add corresponding column aggregates from their children. Replacing one sensor reading repairs one column path in each ancestor row tree. A rectangle query decomposes its row interval into canonical row nodes and performs a column interval sum in each. Both axes use half-open bounds, so the bottom row and right column are excluded. The sample pads each tree to a power of two and keeps a copy of the original cells. It handles a nonempty rectangular grid of signed numeric readings and replacement updates; it does not claim sparse-coordinate allocation or a range-add interface.",
         case="For rows [19,47,29], [61,83,17], and [23,31,53], the rectangle rows [0,2) by columns [1,3) sums to 176. Correcting the second row's last reading from 17 to 41 changes the same answer to 200. The update must replace the leaf, not add 41 on top of 17. An empty rectangle has sum zero, while an out-of-grid coordinate is rejected. Padding cells outside the supplied grid remain zero and must never appear in a valid query. A two-dimensional prefix table answers static sums cheaply but would need rebuilding or many cell changes after this point correction.",
         cost="Construction fills O(RC) padded tree entries for R rows and C columns and runs in O(RC) time; power-of-two padding changes only a constant factor. A replacement or rectangle query touches O(log R log C) entries or sums. Memory is O(RC), which can be substantial because each row node owns a complete column tree and Python stores objects for those slots. The retained source-cell copy adds O(RC). A two-dimensional Fenwick tree offers the same asymptotic point-update and rectangle-sum costs with different indexing and often lower fixed overhead; this tree makes canonical segment decomposition explicit.",
         mistakes=["Do not add a replacement value to the old sensor reading.", "Do not mix inclusive and half-open rectangle endpoints.", "Do not query padded cells as though they belong to the input grid.", "Do not claim this dense table is suitable for an enormous sparse coordinate space."],
         related=["dsa/two-dimensional-fenwick-rectangle-sums", "dsa/two-dimensional-prefix-grid-sums", "dsa/sparse-coordinate-segment-tree"]),
    dict(path="dsa/verified-range-majority-candidates", program="verified_range_majority_index.py",
         template="dsa/merge-sort-tree-threshold-count", section="dsa/range-query-structures",
         title="Range-majority indexes: verify a candidate before returning it",
         summary="Merge vote-cancellation summaries, then count actual positions inside the requested window.",
         definition="A range-majority index asks whether one value occurs more than half the time within a selected subarray. Each segment-tree node stores a candidate and a residual vote balance. Combining two summaries cancels opposing votes, preserving any true majority as a possible candidate. The summary alone is not proof: a candidate can remain after cancellation without exceeding half the range. This model stores sorted occurrence positions for every value, then uses two binary searches to count the candidate inside a half-open window. Its tree is immutable after construction, and values must be usable as dictionary keys. A zero-length window has no majority. Equality with half the window length does not qualify.",
         case="Readings [47,19,47,47,83,19,47,61] give majority 47 over positions [0,5). The last four positions have no majority. The query for [3,3) returns none because it contains no readings. If a candidate occurs twice in a four-reading window, returning it would be wrong even if the vote summary carries a nonzero balance. Positions are zero-based and the right boundary is excluded. A correction to one stored reading would require repairing the segment tree and both affected position lists; this teaching index deliberately has no mutation method, avoiding a false constant-time update promise.",
         cost="Building tree summaries and occurrence lists costs O(N) time and space for N readings. A query combines O(log N) tree nodes and performs two binary searches in the candidate's occurrence list, giving O(log N) time and O(1) extra query space. The index finds a strict majority only; it does not enumerate every value above a lower frequency threshold. The segment summary is a compact candidate filter, and the position map supplies exact verification. A merge-sort tree can count values by threshold but stores more per-node sorted data for a broader set of questions.",
         mistakes=["Do not return a vote-cancellation candidate without counting its positions.", "Do not treat exactly half the readings as a strict majority.", "Do not include the half-open right boundary in occurrence counts.", "Do not mutate source readings while keeping frozen position lists."],
         related=["dsa/merge-sort-tree-threshold-count", "dsa/wavelet-matrix-static-rank-quantile", "dsa/misra-gries-frequent-item-candidates"]),
    dict(path="dsa/alias-table-weighted-dispatch", program="alias_dispatch_weight_sampler.py",
         template="dsa/reservoir-sampling-fixed-memory", section="dsa/array-data-structure-guide",
         title="Alias tables: constant-work draws from fixed dispatch weights",
         summary="Precompute a threshold and fallback route for each equally likely column.",
         definition="An alias table preprocesses a fixed discrete distribution into one threshold and one fallback outcome per column. A uniform draw chooses a column, then uses its fractional part to decide between the column's own outcome and its alias. Construction scales weights so their average is one, pairing underfilled columns with overfilled columns until every column owns exactly one unit of probability mass. The program retains route names in input order and accepts zero weights but rejects negative, nonfinite, empty, or all-zero distributions. Its deterministic pick_from_unit method exposes the draw mapping for inspection; sample consumes an injected random generator. The table is a static snapshot of weights: changing a route weight requires rebuilding it.",
         case="North, east, and west routes have weights 19, 47, and 29. Fixed unit draws 0.03, 0.31, 0.69, and 0.94 select north, east, west, and west under this table's column arrangement. Those four draws are a trace, not statistical evidence that the weighted distribution has been reproduced. The sum of weights must remain positive and finite; an all-zero list has no meaningful probability measure. A zero-weight route can occupy a column but its threshold is zero, so the alias receives every draw from that column. The method requires a uniform input on [0,1) and rejects 1 itself.",
         cost="For K routes, table construction does O(K) arithmetic and uses O(K) storage. Each draw performs O(1) array accesses and comparisons after the random source supplies one uniform value. Updating one weight by reconstructing the table costs O(K), so a Fenwick frequency index may be preferable when weights change repeatedly. Floating-point rounding can slightly perturb boundaries, and a production sampler should define numeric precision and random-source requirements. Fixed-seed traces are useful for reproducible tests but are not suitable evidence of cryptographic unpredictability or a performance benchmark.",
         mistakes=["Do not use an alias table without rebuilding it after weights change.", "Do not allow a zero or nonfinite total weight.", "Do not treat four deterministic draws as a distribution test.", "Do not pass a unit draw equal to one into a zero-based column table."],
         related=["dsa/reservoir-sampling-fixed-memory", "dsa/fenwick-order-statistic-multiset", "dsa/two-heap-running-median", "dsa/space-saving-topk-stream-summary"]),
    dict(path="dsa/minhash-banded-incident-candidates", program="minhash_incident_candidate_index.py",
         template="dsa/trigram-index-verified-substring-candidates", section="dsa/hash-tables",
         title="MinHash bands: retrieve incident candidates, then check exact overlap",
         summary="Bucket fixed-width set sketches by bands and verify every returned Jaccard score.",
         definition="A MinHash sketch records the minimum token hash under each of several independently seeded hash functions. Similar token sets tend to agree in more sketch positions. Banding groups adjacent positions into exact tuples; records sharing a tuple in any band become candidates for later verification. This index stores each incident's complete token set, uses deterministic cryptographic hash digests for stable demonstration output, and calculates exact Jaccard intersection-over-union on retrieved candidates. The bucket search is approximate: two truly similar incidents can miss every band, so a missing result does not prove dissimilarity. Empty token sets are rejected because this interface does not define their Jaccard score, and duplicate incident IDs are refused rather than overwritten without cleaning old buckets.",
         case="Incident I-19 has dock, scanner, offline, and night. I-47 adds retry to that set, while I-83 contains unrelated payment terms. Querying the first four tokens at threshold 0.75 returns I-19 with score 1.0 and I-47 with score 0.8 in the fixed trace. The index does not compare every record, so another corpus could omit a genuine match that never collides in any band. Exact verification prevents returned false positives relative to the specified threshold, but it cannot recover candidate false negatives. Token normalization and shingling policies must stay the same between indexed incidents and queries.",
         cost="With S sketch positions and T distinct tokens in one record, this direct implementation computes O(ST) hashes and stores O(S+T) values per record, plus band-bucket references. A query hashes O(ST) token-position pairs, unions all collided buckets, then verifies each candidate in time proportional to the token-set intersection and union work. In the worst case every record is a candidate, so query work scales with corpus size. Hash agreement only estimates resemblance; this implementation reports exact scores after candidate retrieval. The fixed digest family is practical for reproducibility but does not claim perfect minwise independence or a universal recall guarantee.",
         mistakes=["Do not treat a missing band collision as proof of dissimilarity.", "Do not return an approximate score as if exact verification had run.", "Do not change token normalization between indexing and querying.", "Do not overwrite an incident without removing its old band memberships."],
         related=["dsa/trigram-index-verified-substring-candidates", "dsa/hyperloglog-register-distinct-estimate", "dsa/bloom-filter-membership-boundary", "dsa/suffix-array-lcp-incident-search"]),
    dict(path="dsa/run-length-bitmap-set-algebra", program="run_length_alert_bitmap.py",
         template="dsa/chunked-array-bitmap-alert-set", section="dsa/hash-tables",
         title="Run-length bitmaps: union, intersect, and subtract alert spans",
         summary="Store consecutive nonnegative IDs as half-open runs instead of one bit per ID.",
         definition="A run-length bitmap represents a set of nonnegative integers as sorted, disjoint half-open intervals. Construction merges overlapping and adjacent runs. Membership binary-searches the run starts, while union normalizes both run lists, intersection advances two cursors, and difference subtracts overlapping pieces without expanding individual IDs. The result of each set operation is a new bitmap; the input objects remain intact. This is effective when many IDs are consecutive. It is not automatically compact for isolated IDs, because each singleton needs its own run record. The example stores Python interval tuples rather than a byte-packed bitmap wire format, so its memory measurements would include substantial language object overhead.",
         case="North owns [19,29), [29,47), and [83,91), which construction merges into [19,47) and [83,91). East owns [23,31) and [43,61). Their intersection is [23,31) and [43,47); north minus east leaves [19,23), [31,43), and [83,91). The union contains fifty integer IDs. Each right endpoint is excluded, so 47 is absent from north before union but present in east. Adjacent intervals should merge, or the same represented set would have avoidable extra runs. A negative or empty interval is rejected rather than hidden as a silent no-op.",
         cost="For A and B input run counts, intersection and difference scan O(A+B) runs and use O(A+B) worst-case output space. The current union concatenates and sorts all runs, taking O((A+B) log(A+B)) time, even though a linear merge is possible because each input is already sorted. Membership costs O(log A); cardinality scans O(A) run lengths each call. Stored space is O(A) run tuples. A chunked bitmap may win on scattered dense blocks, while run-length encoding wins when long adjacent ID stretches dominate. Neither format by itself promises a specific byte count without an encoding specification.",
         mistakes=["Do not include the right endpoint of a half-open run.", "Do not expand every ID merely to compute an intersection.", "Do not assume runs save space for isolated identifiers.", "Do not call this Python tuple model a compressed on-disk byte format."],
         related=["dsa/chunked-array-bitmap-alert-set", "dsa/disjoint-interval-union-maintenance-windows", "dsa/bitvector-rank-select-superblocks", "dsa/inverted-index-sorted-postings-intersection"]),
]

for number, lesson in enumerate(lessons):
    path = lesson["path"]
    assert path not in by_path, path
    program = (root / "work/dsa-programs" / lesson["program"]).read_text().rstrip()
    result = subprocess.run([sys.executable, "-c", program], check=True, capture_output=True, text=True)
    related = [lesson["section"], subject_root, *lesson["related"], "dsa/projects", "dsa/quizzes"]
    body = "<p>" + html.escape(lesson["definition"]) + "</p>"
    body += "<h2>Operational case</h2><p>" + html.escape(lesson["case"]) + "</p>"
    body += '<h2>Working Python program</h2><pre><code class="language-python">' + html.escape(program, quote=False) + "</code></pre>"
    body += '<h3>Output</h3><pre><code class="language-text">' + html.escape(result.stdout.strip()) + "</code></pre>"
    body += "<h2>Time, space, and tradeoff</h2><p>" + html.escape(lesson["cost"]) + "</p>"
    body += "<h3>Common Mistakes</h3><ul>" + "".join("<li>" + html.escape(item) + "</li>" for item in lesson["mistakes"]) + "</ul>"
    body += "<h2>Connected lessons</h2>" + links(related)
    entry = copy.deepcopy(by_path[lesson["template"]])
    entry.update(id=str(uuid.uuid5(uuid.NAMESPACE_URL, "aitrove:" + path)), path=path,
                 title=lesson["title"], summary=lesson["summary"], body=body,
                 sort_order=46200 + 10 * number, created_at=stamp, updated_at=stamp, published_at=stamp)
    entry["data"].update(section_path=lesson["section"],
                         related=[{"path": target, "title": by_path[target]["title"]} for target in related])
    entries.append(entry)
    by_path[path] = entry
    for hub_path in (lesson["section"], subject_root):
        hub = by_path[hub_path]
        module = hub["data"]["modules"][0] if hub_path == lesson["section"] else next(
            module for module in hub["data"]["modules"] if module["title"] == by_path[lesson["section"]]["title"])
        module["lessons"].append(path)
        hub["body"] += '<p><a href="/' + path + '">' + html.escape(lesson["title"]) + "</a></p>"
        hub["updated_at"] = stamp

groups = [
    dict(paths=[lesson["path"] for lesson in lessons[:4]],
         project="dsa/ordered-rank-grid-majority-audit-project",
         quiz="quizzes/dsa-ordered-rank-grid-majority-contracts",
         title="Project: audit ordered ranks, grid corrections, and majority windows",
         intro="A depot analytics release combines four independent indexes. Ordered treaps split inventory keys at a dispatch boundary, a span skip list maps alert IDs to ranks, a two-dimensional segment tree corrects heat sensors and sums rectangles, and a range-majority index identifies a verified dominant reading in a frozen window. Keep ownership and mutability clear: treap splits consume their roots, skip-list spans must follow changes, grid cells can be replaced, and the majority index needs rebuilding after source edits.",
         trace="Split depot keys at 47 to obtain [19,29] and [47,61,83]. The third key after removal of 61 is 47. An alert index initially ranks 47 at position two, then removes 29. A heat-grid rectangle rises from 176 to 200 after one sensor correction. A majority query over the first five readings returns 47, while the last four have no majority. Reproduce these results with direct sorted lists, matrix slices, and occurrence counts before accepting index output.",
         failures="Generate duplicate insertions and random removals, then compare ordered treap rank selection and split partitions with sorted sets. Mutate the skip list repeatedly while checking every rank and select against that set. Replace grid values at corners and padded boundaries; compare half-open rectangles with direct sums, including empty windows. Check majority candidates against a direct frequency count, especially when one value appears exactly half the time. Record expected logarithmic bounds separately from strict worst-case claims for randomized structures.",
         mistakes=["Do not reuse consumed treap roots as snapshots.", "Do not leave skip-list spans stale after removal.", "Do not add a new grid value on top of the old cell.", "Do not return a majority candidate without exact verification."]),
    dict(paths=[lesson["path"] for lesson in lessons[4:]],
         project="dsa/weighted-candidate-bitmap-audit-project",
         quiz="quizzes/dsa-weighted-candidate-bitmap-contracts",
         title="Project: audit weighted draws, incident candidates, and alert spans",
         intro="A dispatch review uses three structures with different guarantees. An alias table samples a static weighted route list, MinHash bands retrieve possible near-duplicate incidents before an exact Jaccard check, and a run-length bitmap combines consecutive alert IDs without expanding them. The alias table has exact table probabilities up to floating-point arithmetic; MinHash candidate recall is approximate; bitmap set operations are exact. A route-weight edit needs a rebuilt alias table, while an incident replacement needs old bucket memberships removed before new ones are inserted.",
         trace="For weights 19, 47, and 29, inspect fixed unit draws 0.03, 0.31, 0.69, and 0.94. An incident query with four dock tokens returns exact overlap 1.0 for I-19 and 0.8 for I-47 among collided candidates. North and east alert runs intersect at [23,31) and [43,47), and their union contains fifty IDs. Compare route draw frequencies over many fixed unit points to the normalized weights, but do not treat a short sample as proof of distribution quality.",
         failures="Reject empty or all-zero route weights and nonfinite totals; rebuild the table when any route changes. Generate token sets and compare every reported MinHash candidate score with direct intersection-over-union, while acknowledging that a non-colliding true match can be missed. Generate random run intervals and compare union, intersection, difference, membership, and cardinality with small direct sets. Include adjacent runs, exact right boundaries, and empty intersections. Check that published records never present candidate retrieval as an exhaustive similarity search.",
         mistakes=["Do not use old aliases after weight changes.", "Do not claim that a missing MinHash collision proves no match.", "Do not return an unverified similarity estimate as an exact score.", "Do not count half-open run endpoints as members."]),
]

quiz_items = {
    "dsa/ordered-treap-split-join-rank": [
        ("What must be true before two ordered treaps are joined?", "Every left key is below every right key", "Their roots have equal priorities", "They have the same node count", "Join preserves search order only when the complete key ranges are disjoint and correctly ordered before the roots are linked."),
        ("What information makes select by rank possible?", "A current subtree size at every node", "Only a root priority", "A hash of all keys", "The selector compares a requested position with the size of the left subtree and must receive repaired counts after mutations."),
        ("Does split preserve an unchanged old root?", "No, the split rewires and consumes nodes", "Yes, it copies every path", "Yes, it only reads priorities", "This mutable implementation reattaches child pointers on the search path, so the original root no longer represents an intact snapshot."),
    ],
    "dsa/span-skip-list-rank-select": [
        ("What does a skip-list pointer span measure?", "Bottom-level entries crossed by that pointer", "Bytes used by its tower", "Maximum height of a successor", "Rank and select advance by recorded bottom-level distances, not by the physical height of the traversed pointer."),
        ("Which spans change after removing a short-tower node?", "Direct predecessor spans and higher spans crossing it", "Only spans stored on the removed node", "No spans above level zero", "Higher pointers can skip over a deleted bottom-level item even when the item had no pointer at those higher levels."),
        ("What does rank of key 47 count?", "Stored keys strictly below 47", "Keys at or below 47", "The number of upper express levels", "The contract uses a lower-bound rank, which counts bottom-level IDs strictly smaller than the requested key."),
    ],
    "dsa/two-dimensional-segment-tree-heat-grid": [
        ("What happens after one sensor reading is replaced?", "One column path is repaired in each ancestor row tree", "Only the source matrix is edited", "Every row and column tree is rebuilt", "The corrected leaf contributes to one column path inside each row ancestor, preserving all rectangle aggregates."),
        ("Does rectangle [0,2) by [1,3) include row two?", "No, the bottom row is excluded", "Yes, both row bounds are included", "Only if its values are positive", "The two axes use half-open bounds, so rows zero and one qualify while row two does not."),
        ("What does the dense index cost in memory?", "Storage proportional to row count times column count", "Constant storage regardless of grid shape", "Only one value per query", "Each outer row node owns an inner column tree, producing O(RC) padded aggregate slots."),
    ],
    "dsa/verified-range-majority-candidates": [
        ("Why count positions after obtaining a vote candidate?", "A residual candidate may still occur at most half the time", "The segment tree never stores candidates", "The position list changes the original values", "Cancellation preserves any true majority as a candidate, but it does not certify that a candidate passes the strict frequency threshold."),
        ("Is two occurrences in a four-reading window a majority?", "No, a strict majority needs more than two", "Yes, equality qualifies", "Only if the value appears first", "The contract requires more than half the window, so an occurrence count equal to half is rejected."),
        ("Can source readings change without rebuilding this index?", "No, tree summaries and position lists would both be stale", "Yes, queries inspect the live input list", "Yes, the candidate alone is always correct", "The lesson exposes a static index: changing a reading invalidates both the segment summary and the value-to-positions map."),
    ],
    "dsa/alias-table-weighted-dispatch": [
        ("What is stored for each alias-table column?", "A threshold and fallback outcome", "A complete binary tree", "One updated prefix sum per draw", "Each column's normalized mass is split between its own route and one alias, so a draw makes one threshold comparison."),
        ("How does changing a route weight affect this table?", "The static table must be rebuilt", "Only the random seed changes", "Nothing because aliases adapt automatically", "Thresholds and aliases encode the full original distribution; an edited weight invalidates that precomputed layout."),
        ("Which weight input is invalid?", "An all-zero route list", "A mixture of positive and zero weights", "Several positive finite route weights", "The sampler requires a positive finite total; zero-weight individual routes are allowed but an all-zero distribution is undefined."),
        ("What is the per-draw work after construction?", "Constant array access and one comparison", "A scan of every route", "A new alias-table construction", "After O(K) preprocessing, selecting a column and comparing against its threshold uses O(1) table work."),
    ],
    "dsa/minhash-banded-incident-candidates": [
        ("What does a matching band establish?", "The two sketches are candidates for exact checking", "The full token sets are identical", "Their Jaccard score is exactly one", "A shared band only places a record in the candidate set; the stored token sets still need exact intersection-over-union verification."),
        ("Can a true near-duplicate miss every band?", "Yes, candidate retrieval can have false negatives", "No, all similar sets share a band", "Only if the score is exactly one", "Band collisions are probabilistic, so a highly similar pair can fail to collide and remain unseen by the verifier."),
        ("What does the returned score measure?", "Exact intersection size divided by union size for a retrieved candidate", "Only the fraction of equal signature entries", "The number of records in a band bucket", "The query uses the full retained token sets for its reported Jaccard score after band-based candidate selection."),
        ("Why are duplicate IDs rejected?", "Old bucket memberships would otherwise need explicit removal", "MinHash cannot hash strings", "Two records can never share any band", "Replacing a record without clearing its former band keys leaves stale postings that can cause incorrect candidate retrieval."),
    ],
    "dsa/run-length-bitmap-set-algebra": [
        ("What does one run [19,47) represent?", "Integer IDs 19 through 46", "Integer IDs 19 through 47", "Only IDs 19 and 47", "A half-open run includes its start and excludes its end, so it represents every integer from 19 through 46."),
        ("How is intersection computed without expanding IDs?", "Advance cursors through sorted run lists", "Scan every possible integer in the universe", "Hash each individual bit into a dictionary", "Two sorted disjoint run lists can be intersected by checking endpoint overlap and advancing the interval that finishes first."),
        ("When can run-length encoding lose its space advantage?", "When most stored IDs are isolated", "When IDs occur in long consecutive spans", "When adjacent runs are merged", "Each isolated identifier needs a separate run record, so scattered sets may favor another bitmap representation."),
        ("How does this implementation compute union?", "It concatenates, sorts, and normalizes runs", "It performs only one pointer comparison", "It expands every run into individual IDs", "The union constructor sorts the combined intervals and merges touching or overlapping spans without materializing every contained ID."),
    ],
}

for group_number, group in enumerate(groups):
    project_path, quiz_path = group["project"], group["quiz"]
    assert project_path not in by_path and quiz_path not in by_path
    project = copy.deepcopy(by_path["dsa/allocation-ownership-coalescing-audit-project"])
    project.update(id=str(uuid.uuid5(uuid.NAMESPACE_URL, "aitrove:" + project_path)), path=project_path,
                   title=group["title"], summary="Check independent structure contracts against direct results.",
                   sort_order=46290 + 20 * group_number, created_at=stamp, updated_at=stamp, published_at=stamp)
    project["data"].update(reading_minutes=35,
                           related=[{"path": path, "title": by_path[path]["title"]} for path in group["paths"]])
    project["body"] = "<p>" + html.escape(group["intro"]) + "</p>"
    project["body"] += "<h2>Acceptance trace</h2><p>" + html.escape(group["trace"]) + "</p>"
    project["body"] += "<h2>Failure and cost review</h2><p>" + html.escape(group["failures"]) + "</p>"
    project["body"] += "<h3>Common Mistakes</h3><ul>" + "".join("<li>" + html.escape(item) + "</li>" for item in group["mistakes"]) + "</ul>"
    project["body"] += "<h2>Connected lessons</h2>" + links(group["paths"] + ["dsa/projects", "dsa/quizzes", subject_root])
    entries.append(project)
    by_path[project_path] = project
    raw_questions = [item for path in group["paths"] for item in quiz_items[path]]
    assert len(raw_questions) == 12
    questions = []
    for question_number, (prompt, correct, wrong_one, wrong_two, explanation) in enumerate(raw_questions):
        assert len(explanation) >= 60
        answer = question_number % 3
        options = [wrong_one, wrong_two]
        options.insert(answer, correct)
        questions.append({"prompt": prompt, "options": options, "answer": answer, "explanation": explanation})
    quiz = copy.deepcopy(by_path["quizzes/dsa-splay-and-resident-history-contracts"])
    quiz.update(id=str(uuid.uuid5(uuid.NAMESPACE_URL, "aitrove:" + quiz_path)), path=quiz_path,
                title=group["title"].replace("Project: audit ", "Check "),
                summary="Twelve explained decisions about these Data Structures contracts.",
                sort_order=46300 + 20 * group_number, created_at=stamp, updated_at=stamp)
    quiz["data"].update(duration_minutes=20,
                        related=[{"path": path, "title": by_path[path]["title"]} for path in group["paths"] + [project_path]],
                        questions=questions)
    quiz["body"] = "<p>Choose the operation contract or failure response implied by each structure. Check each choice against the runnable trace.</p><h2>Lessons</h2>" + links(group["paths"]) + "<h2>Design exercise</h2>" + links([project_path, subject_root])
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
    for path in group["paths"]:
        entry = by_path[path]
        peers = [other for other in group["paths"] if other != path]
        entry["body"] += "<p>Compare this operation boundary with " + ", ".join(
            '<a href="/' + other + '">' + html.escape(by_path[other]["title"]) + "</a>" for other in peers)
        entry["body"] += ', then complete the <a href="/' + project_path + '">structure audit</a> and <a href="/' + quiz_path + '">decision quiz</a>.</p>'
        entry["updated_at"] = stamp

for old_path, target in [
    ("dsa/implicit-treap-range-reversal", "dsa/ordered-treap-split-join-rank"),
    ("dsa/persistent-ordered-index-path-copying", "dsa/ordered-treap-split-join-rank"),
    ("dsa/skip-list-ordered-index", "dsa/span-skip-list-rank-select"),
    ("dsa/fenwick-order-statistic-multiset", "dsa/span-skip-list-rank-select"),
    ("dsa/two-dimensional-fenwick-rectangle-sums", "dsa/two-dimensional-segment-tree-heat-grid"),
    ("dsa/two-dimensional-prefix-grid-sums", "dsa/two-dimensional-segment-tree-heat-grid"),
    ("dsa/merge-sort-tree-threshold-count", "dsa/verified-range-majority-candidates"),
    ("dsa/wavelet-matrix-static-rank-quantile", "dsa/verified-range-majority-candidates"),
    ("dsa/reservoir-sampling-fixed-memory", "dsa/alias-table-weighted-dispatch"),
    ("dsa/fenwick-order-statistic-multiset", "dsa/alias-table-weighted-dispatch"),
    ("dsa/trigram-index-verified-substring-candidates", "dsa/minhash-banded-incident-candidates"),
    ("dsa/hyperloglog-register-distinct-estimate", "dsa/minhash-banded-incident-candidates"),
    ("dsa/chunked-array-bitmap-alert-set", "dsa/run-length-bitmap-set-algebra"),
    ("dsa/disjoint-interval-union-maintenance-windows", "dsa/run-length-bitmap-set-algebra"),
]:
    entry = by_path[old_path]
    entry["body"] += '<p><a href="/' + target + '">' + html.escape(by_path[target]["title"]) + "</a> adds a related structure with a different operation boundary.</p>"
    entry["updated_at"] = stamp

fixture_path.write_text(json.dumps(entries, ensure_ascii=False, indent=2) + "\n")
print(json.dumps({"lessons": len(lessons), "projects": len(groups), "quizzes": len(groups),
                  "new_routes": len(lessons) + 2 * len(groups)}))
