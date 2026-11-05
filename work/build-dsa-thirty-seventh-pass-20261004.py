"""Add seven distinct Data Structures topics with connected draft assessments."""

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
    dict(path="dsa/moveable-disjoint-set-shipment-groups", program="moveable_warehouse_dsu.py",
         template="dsa/disjoint-set-union-connectivity", section="dsa/graphs-and-disjoint-sets",
         title="Moveable disjoint sets: transfer one shipment without splitting its old tree",
         summary="Map each logical shipment to a current DSU node so a move can leave old parent links intact.",
         definition="Ordinary disjoint-set union can merge groups but cannot detach one member from a compressed parent tree. A moveable variant separates a logical shipment ID from the current DSU node representing it. On a move, the old group's active size and ID sum fall by one member; a fresh node is attached to the destination root and the shipment-to-node map changes. The former node remains as a ghost so other paths through it stay valid. Merge still uses union by active size and find still compresses paths. This example tracks group size and the sum of zero-based shipment IDs, not parcel weights. A move inside the same group is a no-op. Ghost nodes are never reclaimed, which is an explicit memory cost rather than a hidden deletion mechanism.",
         case="Merge shipments 1, 3, and 5 into one group and shipments 2 and 4 into another. Their size and ID-sum pairs are (3,9) and (2,6). Moving shipment 3 to shipment 4's group leaves the old group at (2,6) and the destination at (3,9); shipment 1 is no longer grouped with 3. Reassigning parent[3] directly would be unsafe because other DSU paths might pass through that node. Moving an ID that currently names a root has the same fresh-node rule. A group can retain an old root with zero active members, but no current shipment maps to that empty group.",
         cost="For N initial shipments and M successful moves, storage is O(N+M) nodes because each transfer allocates one new node. With union by active size and path compression, find-based operations have inverse-Ackermann amortized behavior in the expanded node forest; each public merge, move, membership test, or group summary performs a constant number of finds plus O(1) bookkeeping. This is not a persistent snapshot and does not support undo. A rollback DSU offers checkpoint reversal under a different update discipline, while this structure permits individual member transfers without reconstructing whole components.",
         mistakes=["Do not reparent an existing DSU node to move its logical member.", "Do not forget to update both active group size and ID sum.", "Do not count abandoned ghost nodes as active shipments.", "Do not promise that memory stays O(N) after many moves."],
         related=["dsa/disjoint-set-union-connectivity", "dsa/disjoint-set-rollback-checkpoints", "dsa/potential-disjoint-set-difference-constraints"]),
    dict(path="dsa/block-cut-tree-articulation-depots", program="block_cut_depot_network.py",
         template="dsa/scc-condensation-reachability-index", section="dsa/graphs-and-disjoint-sets",
         title="Block-cut indexes: separate articulation depots from cyclic road blocks",
         summary="Use discovery and low values to group undirected edges into vertex-biconnected blocks.",
         definition="A block-cut index exposes how an undirected network separates when one vertex is removed. Depth-first discovery times and low values identify edges that belong to the same vertex-biconnected block. An edge stack collects a block whenever a child cannot reach an ancestor of its parent; the parent is an articulation vertex when that separation disconnects remaining vertices. The root has the special rule of needing more than one DFS child. This model accepts a simple undirected graph: self-loops and parallel roads are rejected, while isolated depots receive singleton blocks. Blocks are sets of vertex IDs, and an articulation depot appears in more than one block. The stored incidence list links articulation IDs to block numbers, producing the two node types of a block-cut forest.",
         case="Roads connect a triangle among depots 0, 1, and 2, a bridge from 2 to 3, another triangle among 3, 4, and 5, and a bridge from 5 to 6. Depot 7 is isolated. The resulting blocks are [0,1,2], [2,3], [3,4,5], [5,6], and [7]; the cut depots are 2, 3, and 5. Depot 5 belongs to the triangle block and the last bridge block. A bridge is a two-vertex block in this representation. The block's numeric position is a build artifact, not a durable road ID. Adding or removing a road can change both the blocks and articulation set, so the static index must be rebuilt.",
         cost="The DFS and edge-stack decomposition scan O(V+E) vertices and roads and store O(V+E) graph and stack state. This Python implementation also sorts adjacency lists and output blocks for repeatable display and scans blocks to produce articulation incidence lists, so its total postprocessing can exceed the linear decomposition bound. Recursive DFS uses O(V) call depth and may hit Python's recursion limit on a long path. No online road update is supported. A strongly connected component index solves directed mutual reachability; block-cut decomposition instead describes failure at a single vertex in an undirected graph.",
         mistakes=["Do not use the non-root articulation rule for the DFS root.", "Do not treat a bridge as though it belongs to a cycle block.", "Do not conflate directed strongly connected groups with undirected blocks.", "Do not keep old block numbers after editing roads."],
         related=["dsa/scc-condensation-reachability-index", "dsa/online-connectivity-after-edge-removal", "dsa/csr-sparse-graph-storage"]),
    dict(path="dsa/kruskal-reconstruction-bottleneck-index", program="kruskal_bottleneck_route_tree.py",
         template="dsa/binary-lifting-lowest-common-ancestor", section="dsa/graphs-and-disjoint-sets",
         title="Kruskal reconstruction trees: answer route bottlenecks through merge ancestors",
         summary="Record each sorted-edge component merge as a new weighted parent node.",
         definition="A Kruskal reconstruction tree turns sorted undirected road insertions into a hierarchy of component merges. Original depots are leaves. Whenever an edge joins two previously separate components, a new internal node becomes the parent of their current component-tree roots and carries that edge weight. The least common ancestor of two depot leaves records the smallest threshold at which the depots become connected; equivalently, it is the minimum possible maximum road weight along a path between them. The model builds binary-lifting ancestors for static queries. Repeated edge weights are ordered reproducibly by endpoints. Self-loops and edges that join an already connected component add no merge node. Weights must be nonnegative, and a depot queried against itself has the documented bottleneck value zero.",
         case="Road weights 19 between depots 0 and 1, 47 between 1 and 2, 29 between 0 and 2, 61 between 2 and 3, and 83 between 3 and 4 make the bottleneck from 0 to 2 equal 29: the direct edge improves on the two-edge route whose largest weight is 47. From 0 to 4 the answer is 83. Depot 5 stays disconnected, so its query against 0 returns no value. A merge node's numeric ID is incidental. A new road can change the merge hierarchy; this is a frozen graph index and should not answer from an obsolete tree after edge updates.",
         cost="Sorting E roads costs O(E log E). Successful DSU unions create at most V minus one internal nodes, and binary-lifting tables over fewer than 2V nodes require O(V log V) build space and time. Each bottleneck query lifts two leaves toward their common ancestor in O(log V) time, after an O(1) component check. The constructor keeps a sorted copy of the roads, so working space also includes O(E). A single Dijkstra-style minimax search avoids the index build for a few queries. The reconstruction tree pays for many queries against the same unchanged weighted graph.",
         mistakes=["Do not use the sum of road weights when the query asks for a path maximum.", "Do not create a merge node for an edge inside an existing component.", "Do not answer disconnected pairs with a numeric threshold.", "Do not reuse a static ancestor table after road edits."],
         related=["dsa/binary-lifting-lowest-common-ancestor", "dsa/disjoint-set-union-connectivity", "dsa/stale-entry-heap-shortest-route"]),
    dict(path="dsa/zero-suppressed-diagram-dispatch-set-families", program="zero_suppressed_dispatch_families.py",
         template="dsa/reduced-ordered-decision-diagram-rules", section="dsa/trees-and-heaps",
         title="Zero-suppressed diagrams: share sparse dispatch set families",
         summary="Intern low and high branches while removing tests whose include branch is empty.",
         definition="A zero-suppressed decision diagram represents a family of subsets over a fixed ordered universe. At an item test, the low branch omits that item and the high branch includes it. Terminal zero represents no subsets; terminal one represents the family containing the empty subset. If the high branch is zero, the node is removed because no represented set contains that item. Nodes with the same item position and child pair are interned once, so repeated subfamilies share a node. This differs from a reduced ordered Boolean decision diagram: equal low and high branches are not removed by the zero-suppression rule. The teaching builder starts from explicit allowed sets, deduplicates them, and then constructs the graph; it does not generate a large implicit family symbolically.",
         case="The allowed dispatch combinations are insured alone, cold with insured, fragile with insured, and cold plus fragile with insured. The diagram represents four sets with three internal nodes in the chosen item order. Cold with insured is accepted; cold alone is not. The item oversized never occurs, so its include branch is empty and its test disappears. A query containing an unknown item is rejected. Skipped levels mean those items are absent, not don't-care values. Changing item order can alter sharing and node count even when the represented family is identical.",
         cost="For F explicit subsets and V ordered items, this direct partitioning builder spends O(FV) work and can retain O(FV) node and temporary-set records in the worst case; memoized node interning may reduce the retained graph. Recursion uses O(V) depth. Membership visits at most V item levels, and family-size counting visits each retained node once with O(M) memo space for M nodes. A giant explicitly listed family still costs time proportional to that input; the compact diagram does not make explicit enumeration free. A Boolean rule diagram models assignments, while a zero-suppressed diagram treats the absence of items as the default for sparse combination families.",
         mistakes=["Do not treat a skipped item as a wildcard that may be included.", "Do not replace zero suppression with the equal-children Boolean reduction rule.", "Do not confuse terminal one with one particular nonempty subset.", "Do not infer that this explicit builder can enumerate an exponential family cheaply."],
         related=["dsa/reduced-ordered-decision-diagram-rules", "dsa/persistent-bitmap-hamt-alert-map", "dsa/trie-prefix-index-and-terminal-flag"]),
    dict(path="dsa/count-sketch-signed-incident-frequencies", program="count_sketch_signed_incidents.py",
         template="dsa/count-min-sketch-frequency-boundary", section="dsa/hash-tables",
         title="Count Sketch: estimate signed incident frequencies with row medians",
         summary="Hash each key to signed counters and use a median to reduce collision noise.",
         definition="A Count Sketch uses several counter rows. For a key, each row chooses a bucket and a sign; an integer update adds the signed delta to that cell. A query multiplies each touched cell by the same sign and takes the median across rows. Unrelated keys can add positive or negative noise, so an estimate may lie above or below the true value. The example uses stable digest-derived bucket and sign choices, five rows, and twenty-nine columns to make its trace repeatable. It permits positive and negative updates, unlike a count-min summary whose one-sided overestimate contract assumes nonnegative increments. The code does not retain the exact key frequencies, discover heavy hitters, or assert a formal error probability for this fixed hash construction.",
         case="A scanner incident receives 47 observations and later an adjustment of minus eight. The sketch estimates 39 in the displayed trace; dock estimates 19 and an unseen key estimates zero under these collisions. Those values are particular outcomes, not universal exactness guarantees. A different stream can collide with a queried key in enough rows to move the median. Sending a negative update without a corresponding business event can produce a negative estimate; the structure stores signed algebraic changes rather than enforcing an inventory policy. The same key must use the same bucket and sign in every update and query.",
         cost="With R rows and W columns, each update and point estimate performs O(R) hash probes; storage is O(RW) integer counters. Median sorting costs O(R log R) in this Python implementation, so the full estimate is O(R log R), although a selection algorithm could avoid sorting. The sketch does not store distinct keys after updates. Its approximation quality depends on width, rows, hash behavior, and the stream's frequency energy; this example makes no strict confidence claim. A count-min sketch has a different one-sided nonnegative update model, while exact dictionaries use space proportional to distinct keys.",
         mistakes=["Do not call a signed median estimate a guaranteed upper bound.", "Do not change row hashes between an update and its query.", "Do not assume an unseen key always estimates zero after other keys collide.", "Do not mistake the sketch for an exact heavy-hitter key inventory."],
         related=["dsa/count-min-sketch-frequency-boundary", "dsa/misra-gries-frequent-item-candidates", "dsa/space-saving-topk-stream-summary", "dsa/hyperloglog-register-distinct-estimate"]),
    dict(path="dsa/exponential-histogram-recent-failure-count", program="exponential_histogram_recent_failures.py",
         template="dsa/reservoir-sampling-fixed-memory", section="dsa/array-data-structure-guide",
         title="Exponential histograms: estimate failures in a recent event window",
         summary="Keep a few timestamped buckets of each power-of-two size instead of every event bit.",
         definition="An exponential histogram summarizes the number of one-bits among the most recent W binary events. Every one creates a size-one bucket at the current event time. Whenever three buckets share a size, the two oldest merge into one bucket of double size. Buckets are ordered by their newest one-bit time; a bucket whose newest bit is before the window start expires. The sample also stores each bucket's oldest bit time. Buckets wholly inside the window contribute their exact sizes; if the oldest surviving bucket straddles the boundary, the estimate counts half of that bucket and exposes half its size as an additive uncertainty allowance. Zeros advance event time but add no bucket. This is an approximate count of events in a sliding window, not a list of exact failure timestamps.",
         case="Across a twelve-event trace with an eight-event window, the model reports an estimate of six failures and a boundary allowance of two. Its retained bucket sizes are [1,1,2,4], newest first. The exact answer can differ from the estimate because a merged bucket can cross the window boundary without storing each bit's time. Expiring a bucket from its oldest timestamp would be wrong: it may still contain newer failures inside the window. A zero event still moves the cutoff forward, even though it creates no bucket. Changing the window width midstream is unsupported because old discarded bucket information cannot be recovered.",
         cost="At most two buckets of each power-of-two size remain, yielding O(log W) stored buckets for a fixed window width W. An estimate scans those buckets in O(log W) time. This direct Python append repeatedly scans and inserts in a small bucket list during cascading merges, costing O(log-squared W) in an unfavorable call; a tighter implementation can maintain counts and ordered links. The boundary bucket produces an additive error no greater than half its size in this model. Exact window counts require retaining more information, such as all recent bits or an exact queue of failure timestamps.",
         mistakes=["Do not expire a bucket merely because its oldest one-bit left the window.", "Do not forget that a zero event advances the time boundary.", "Do not report the half-bucket estimate as an exact count.", "Do not resize the window after discarded history can no longer be restored."],
         related=["dsa/reservoir-sampling-fixed-memory", "dsa/monotonic-deque-window-minimum", "dsa/two-stack-sliding-window-aggregation", "dsa/count-min-sketch-frequency-boundary"]),
    dict(path="dsa/square-root-range-mode-readings", program="sqrt_range_mode_readings.py",
         template="dsa/verified-range-majority-candidates", section="dsa/range-query-structures",
         title="Range-mode indexes: combine complete-block modes with fringe candidates",
         summary="Precompute modes for complete block spans and verify boundary values by occurrence positions.",
         definition="A range mode is the most frequent value inside a subarray; this index breaks ties by choosing the smaller integer. The static readings array is divided into square-root-sized blocks. During construction, every pair of complete-block boundaries stores the mode of the covered core. A query adds all values in the two incomplete boundary fringes as candidates, then checks each candidate's exact occurrence count with binary searches in per-value position lists. Any global mode absent from the fringes must already be a mode of the complete core, which is why one stored core candidate suffices under the deterministic tie rule. Empty windows return no value. This lesson is for arbitrary modes, not only values occurring more than half the time.",
         case="For readings [47,19,47,29,29,29,83,47,29,61,61,61,61], positions [0,6) have mode 29 and the last five positions have mode 61. The window [2,9) also returns 29. A shorter fringe-only query falls back to its own distinct values because no complete block lies inside it. If a mode occurs in a partial block, omitting boundary values from the candidate set can lose the answer. Query endpoints are half-open, and every stored position is zero-based. A changed reading invalidates the precomputed core modes and both old and new occurrence lists, so the model has no in-place update method.",
         cost="With N readings and B about sqrt N blocks, building every core interval by extending a frequency map takes O(NB) time and O(B squared) mode slots; occurrence lists use O(N) more space. A query examines at most O(sqrt N) fringe values plus one core value, and each frequency check takes O(log N), giving O(sqrt N log N) time and O(sqrt N) temporary candidate space. The implementation uses a fixed block size and Python dictionaries, so constant factors matter. A strict-majority index can answer a narrower question in O(log N) time; this one pays more to return a mode even when its frequency is small.",
         mistakes=["Do not assume a complete-block mode alone answers a query with fringes.", "Do not treat a range mode as necessarily a strict majority.", "Do not include the half-open right endpoint in occurrence counts.", "Do not update the source array while retaining static core-mode tables."],
         related=["dsa/verified-range-majority-candidates", "dsa/square-root-block-range-sum", "dsa/merge-sort-tree-threshold-count", "dsa/wavelet-matrix-static-rank-quantile"]),
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
                 sort_order=46400 + 10 * number, created_at=stamp, updated_at=stamp, published_at=stamp)
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
         project="dsa/group-cut-threshold-family-audit-project",
         quiz="quizzes/dsa-group-cut-threshold-family-contracts",
         title="Project: audit member moves, cut depots, bottlenecks, and set families",
         intro="A depot release uses four distinct representations. The moveable disjoint set transfers one shipment without detaching old parent paths. A block-cut index finds depots whose loss separates an undirected road network. A Kruskal reconstruction tree answers minimax road-weight thresholds on a frozen graph. A zero-suppressed diagram represents permitted combinations of dispatch flags. These indexes answer different questions even when they contain the same depot or shipment IDs. Version each road snapshot and allowed-set catalog separately; a changed road or policy invalidates the corresponding static structure.",
         trace="Start with shipment groups {1,3,5} and {2,4}; after moving shipment 3 into the latter, their sizes and ID sums become (2,6) and (3,9). A road graph with two triangles and two bridges has articulation depots 2, 3, and 5. The minimum maximum edge on the route from depot 0 to 2 is 29, while depot 5 is unreachable from 0 in a separate weighted example. A four-set dispatch family includes cold plus insured but rejects cold alone. Check each trace against a direct model with the stated snapshot.",
         failures="Fuzz merge and move operations against explicit group labels; test a move of a member whose old DSU node is a root. Compare articulation vertices with component counts after removing each vertex from small graphs. Compare bottleneck queries with an all-pairs minimax oracle, including disconnected vertices and repeated edge weights. Enumerate every subset of a small item universe to check diagram membership and count. Reject parallel roads in the simple block-cut model and unknown items in the set family. Do not claim any of the static graph or family indexes repair themselves after their inputs change.",
         mistakes=["Do not reparent a live DSU node during a logical member move.", "Do not apply the non-root articulation rule to a DFS root.", "Do not confuse bottleneck maximum with path-weight sum.", "Do not treat a skipped zero-suppressed item as a wildcard."]),
    dict(paths=[lesson["path"] for lesson in lessons[4:]],
         project="dsa/signed-window-mode-audit-project",
         quiz="quizzes/dsa-signed-window-mode-contracts",
         title="Project: audit signed sketches, recent windows, and exact range modes",
         intro="An incident dashboard keeps three summaries with different confidence and update rules. A Count Sketch estimates signed key frequencies from row medians. An exponential histogram approximates the number of recent failure bits under a fixed window width. A square-root range-mode index returns an exact most-frequent reading from a frozen array. The first two discard detail intentionally, while the range-mode index retains occurrence positions and precomputed block modes. The dashboard must label approximation and exactness at the field level, not bury those distinctions in one generic performance claim.",
         trace="A scanner count receives 47 observations and an adjustment of minus eight; the shown signed sketch estimate is 39 for this small trace. After twelve binary events with an eight-event window, the histogram estimates six failures with an additive allowance of two. A static readings index returns 29 over the first six positions and 61 over the last five. For release checks, compare signed counter changes against direct totals, window estimates against exact recent bits, and every range mode against a direct frequency count with smallest-value tie breaking.",
         failures="Apply updates and their negations to the sketch and verify its counters return to the initial state; do not demand exactness under collisions. Generate binary streams and assert the exact recent count stays within the histogram's reported boundary allowance, including long stretches of zeros. Generate integer arrays and compare arbitrary half-open mode queries with direct counts; exercise empty windows, ties, and short ranges without complete blocks. Reject a negative or zero window width and edits to a frozen mode index. Distinguish an approximation's error budget from an exact query's tie policy.",
         mistakes=["Do not present a Count Sketch estimate as one-sided or exact.", "Do not drop a boundary bucket whose newest event is still active.", "Do not ignore fringe candidates in a range-mode query.", "Do not mutate a frozen range index without rebuilding it."]),
]

quiz_items = {
    "dsa/moveable-disjoint-set-shipment-groups": [
        ("Why allocate a new DSU node when one shipment moves?", "Old parent paths may still pass through its former node", "The destination root must be deleted", "Every group must have one node only", "Keeping the old node preserves the parent forest for remaining members while the logical shipment maps to its fresh destination node."),
        ("What happens to memory after many successful moves?", "It grows with the number of moves because ghost nodes remain", "It always shrinks after a move", "It stays at exactly one node per shipment", "Each successful transfer appends a new representative node and does not reclaim the abandoned historical node."),
        ("What group fields change on a transfer?", "Both active sizes and ID sums of old and new groups", "Only the moved shipment's display label", "Only the destination parent pointer", "A move removes one logical ID from its former group and adds it to the new group, changing both aggregates."),
    ],
    "dsa/block-cut-tree-articulation-depots": [
        ("When is a DFS root an articulation depot?", "When it has more than one DFS child", "Whenever one back edge exists", "Whenever it belongs to a triangle", "Removing the DFS root separates the independent child branches only when more than one such branch was discovered."),
        ("How is an undirected bridge represented here?", "As its own two-vertex block", "As a directed cycle", "As no block at all", "The edge stack emits a block containing its two endpoints when that child subtree cannot reach an earlier ancestor."),
        ("May one articulation depot belong to several blocks?", "Yes, it links the blocks that meet at that vertex", "No, every vertex belongs to one block", "Only if roads have parallel duplicates", "A cut vertex is shared by otherwise separate vertex-biconnected edge groups, so its block incidence has multiple entries."),
    ],
    "dsa/kruskal-reconstruction-bottleneck-index": [
        ("What weight labels a new reconstruction parent?", "The sorted edge that first joins its two components", "The sum of every edge in both components", "The largest vertex identifier", "Kruskal's component merge occurs at one edge threshold, and that exact edge weight becomes the new internal node's label."),
        ("What does the leaves' least common ancestor answer?", "Their minimum possible path-maximum edge weight", "Their shortest path sum", "Their number of alternative routes", "The two depots first share a component when the sorted-edge threshold reaches the weight of their merge ancestor."),
        ("What result represents disconnected depots?", "No bottleneck value", "A forced zero threshold", "The largest edge in an unrelated component", "If no sequence of accepted edges joins both depots, they have no shared reconstruction ancestor and no route bottleneck."),
    ],
    "dsa/zero-suppressed-diagram-dispatch-set-families": [
        ("When is a zero-suppressed item node removed?", "Its include branch represents no sets", "Its low and high branches are equal", "Its item name sorts last", "If no represented set includes the tested item, its high branch is the empty family and the test is bypassed."),
        ("What does terminal one represent?", "A family containing the empty subset", "One unspecified nonempty set", "Every subset of the universe", "After all selected item decisions, terminal one signals that the remaining empty subset is admitted by the family."),
        ("What does a skipped item mean for membership?", "The item is absent from represented sets on that path", "The item may freely be present or absent", "The item must be queried twice", "Zero suppression removes tests only where the include branch is empty, so a skipped item cannot be included along that route."),
    ],
    "dsa/count-sketch-signed-incident-frequencies": [
        ("How does a Count Sketch use a key in each row?", "It chooses a bucket and a sign", "It stores the complete key in every cell", "It increments every bucket uniformly", "Each row hashes the key to one cell and multiplies the update by a row-specific sign before changing the counter."),
        ("Can an estimate fall below the true signed frequency?", "Yes, collisions can create negative or positive noise", "No, all estimates are upper bounds", "Only when the table is empty", "Signed collision contributions can move a row estimate in either direction, and the median is not a one-sided bound."),
        ("What allows negative business corrections?", "Counter cells accept signed integer deltas", "The sketch retains every original event", "Rows are always rebuilt after a correction", "An adjustment simply contributes a negative signed delta to the same hashed locations used by the original key."),
        ("Does the sketch enumerate all heavy keys by itself?", "No, it has no exact key inventory", "Yes, every key is stored in its own cell", "Yes, the median lists keys", "The table retains numeric counters but no complete list of distinct keys, so candidates need another source."),
    ],
    "dsa/exponential-histogram-recent-failure-count": [
        ("Which buckets merge after a size appears three times?", "The two oldest buckets of that size", "The two newest buckets of that size", "Every bucket of every size", "Merging older buckets preserves finer detail for recent events while limiting the count at each power-of-two size."),
        ("When can a bucket be discarded as expired?", "When its newest one-bit is before the window start", "When its oldest one-bit is before the window start", "Whenever the next event is zero", "A bucket with an old first bit can still contain newer active failures; only its newest timestamp proves the whole bucket expired."),
        ("Why does a zero event still matter?", "It advances time and can move the window cutoff", "It creates a size-zero bucket", "It freezes all existing bucket timestamps", "The window covers event positions rather than only failure positions, so a zero can cause old ones to leave the active span."),
        ("What does the boundary allowance describe?", "A maximum additive error from the straddling oldest bucket", "The exact number of failures in that bucket", "An error in every stored bucket", "All fully included buckets contribute exact sizes; uncertainty comes from how many bits of the one boundary bucket remain."),
    ],
    "dsa/square-root-range-mode-readings": [
        ("Why check values in both incomplete boundary blocks?", "A global mode may gain decisive occurrences in a fringe", "Complete blocks never contain a mode", "The array is sorted by value", "If the global winner differs from the complete-core mode, it must appear among boundary values that changed its frequency rank."),
        ("Does a mode need to occur more than half the time?", "No, it only needs the greatest frequency with the tie rule", "Yes, every mode is a majority", "Only when the range has an odd length", "A range always has a most-frequent value, even when its count is far below a strict majority threshold."),
        ("How are candidate counts verified?", "With binary searches in sorted occurrence-position lists", "By trusting the core mode alone", "By summing sensor weights", "For each candidate, lower-bound searches find how many of its stored positions lie inside the half-open query interval."),
        ("Can the source array change without rebuilding?", "No, core modes and occurrence lists would become stale", "Yes, only one stored core cell changes", "Yes, the query ignores stored positions", "The lesson exposes a static index; a changed reading can alter multiple precomputed core modes and two position lists."),
    ],
}

for group_number, group in enumerate(groups):
    project_path, quiz_path = group["project"], group["quiz"]
    assert project_path not in by_path and quiz_path not in by_path
    project = copy.deepcopy(by_path["dsa/allocation-ownership-coalescing-audit-project"])
    project.update(id=str(uuid.uuid5(uuid.NAMESPACE_URL, "aitrove:" + project_path)), path=project_path,
                   title=group["title"], summary="Check separate structure guarantees against direct results and failure cases.",
                   sort_order=46490 + 20 * group_number, created_at=stamp, updated_at=stamp, published_at=stamp)
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
                summary="Twelve explained decisions about three or four structure boundaries.",
                sort_order=46500 + 20 * group_number, created_at=stamp, updated_at=stamp)
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
    ("dsa/disjoint-set-union-connectivity", "dsa/moveable-disjoint-set-shipment-groups"),
    ("dsa/disjoint-set-rollback-checkpoints", "dsa/moveable-disjoint-set-shipment-groups"),
    ("dsa/online-connectivity-after-edge-removal", "dsa/block-cut-tree-articulation-depots"),
    ("dsa/scc-condensation-reachability-index", "dsa/block-cut-tree-articulation-depots"),
    ("dsa/binary-lifting-lowest-common-ancestor", "dsa/kruskal-reconstruction-bottleneck-index"),
    ("dsa/stale-entry-heap-shortest-route", "dsa/kruskal-reconstruction-bottleneck-index"),
    ("dsa/reduced-ordered-decision-diagram-rules", "dsa/zero-suppressed-diagram-dispatch-set-families"),
    ("dsa/persistent-bitmap-hamt-alert-map", "dsa/zero-suppressed-diagram-dispatch-set-families"),
    ("dsa/count-min-sketch-frequency-boundary", "dsa/count-sketch-signed-incident-frequencies"),
    ("dsa/space-saving-topk-stream-summary", "dsa/count-sketch-signed-incident-frequencies"),
    ("dsa/reservoir-sampling-fixed-memory", "dsa/exponential-histogram-recent-failure-count"),
    ("dsa/monotonic-deque-window-minimum", "dsa/exponential-histogram-recent-failure-count"),
    ("dsa/verified-range-majority-candidates", "dsa/square-root-range-mode-readings"),
    ("dsa/square-root-block-range-sum", "dsa/square-root-range-mode-readings"),
]:
    entry = by_path[old_path]
    entry["body"] += '<p><a href="/' + target + '">' + html.escape(by_path[target]["title"]) + "</a> adds a related structure with a different operation boundary.</p>"
    entry["updated_at"] = stamp

fixture_path.write_text(json.dumps(entries, ensure_ascii=False, indent=2) + "\n")
print(json.dumps({"lessons": len(lessons), "projects": len(groups), "quizzes": len(groups),
                  "new_routes": len(lessons) + 2 * len(groups)}))
