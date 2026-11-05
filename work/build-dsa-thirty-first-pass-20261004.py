"""Add eight distinct Data Structures topics with projects and review quizzes."""

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


def links(paths):
    return "<ul>" + "".join('<li><a href="/' + path + '">' + html.escape(by_path[path]["title"]) + "</a></li>" for path in paths) + "</ul>"


lessons = [
    dict(path="dsa/eytzinger-array-search-layout", program="eytzinger_case_catalog.py",
         template="dsa/resizable-array-growth-and-insert-cost", section="dsa/array-data-structure-guide",
         title="Eytzinger arrays: store a search tree in breadth-first order",
         summary="Rearrange a sorted static catalog into implicit child slots and retain lower-bound ranks.",
         definition="An Eytzinger array stores a binary search tree in breadth-first order. For a slot at index i, its children occupy 2i+1 and 2i+2 when those positions exist. This static catalog starts from unique sorted case IDs, fills the implicit tree by an in-order walk, and stores each key's rank in the original sorted sequence. A lower-bound query remembers the best key at or above the target while following one comparison path. It returns both the key and rank, or None if no qualifying ID exists. Duplicates are removed at construction; an application that needs duplicate records must define a composite key or maintain a separate posting list. The layout cannot accept a sorted append without rebuilding its implicit child positions.",
         case="A dispatch system loads case IDs 19, 29, 47, 61, 83, and 103 from a morning snapshot. The stored breadth-first layout begins with 61, then 29 and 103; it is not numerically sorted in memory. Searching for the first ID at or after 52 returns 61 at sorted rank three. A lookup for 104 returns None. An equality query for 61 is true even though the key appears at array slot zero. If a writer appends 127 to the layout as if it were a sorted array, the child arithmetic no longer represents a search tree, so this index must be rebuilt from a new immutable snapshot.",
         cost="Building the layout visits each of N unique keys once after sorting, so the implementation costs O(N log N) including sorting and O(N) extra storage for keys and ranks. A lower-bound walk uses O(log N) comparisons because the implicit tree has logarithmic height; it uses O(1) query memory. This lesson does not claim a measured cache advantage in Python. Branch prediction, prefetch behavior, element width, and the host language can change the performance comparison with ordinary binary search. The representation helps when repeated reads dominate and updates arrive as occasional snapshots. The rank array is an explicit convenience and doubles per-slot metadata relative to a keys-only layout.",
         mistakes=["Do not use a standard bisect call on the breadth-first array.", "Do not append a key without rebuilding the layout.", "Do not confuse the layout slot with the sorted rank.", "Do not promise a cache-speed gain without measuring the actual runtime."],
         related=["dsa/resizable-array-growth-and-insert-cost", "dsa/binary-search-tree-order-invariant", "dsa/immutable-index-snapshot-publication"]),
    dict(path="dsa/cartesian-tree-static-range-minimum", program="cartesian_rmq_inspection.py",
         template="dsa/binary-search-tree-order-invariant", section="dsa/trees-and-heaps",
         title="Cartesian trees: preserve sequence order under a heap minimum",
         summary="Build a min-heap tree from a sequence and answer an inclusive range minimum through ancestry.",
         definition="A min Cartesian tree has two simultaneous invariants: its in-order traversal follows the original sequence positions, and each parent is no greater than its children. This implementation uses the pair (reading, position) to break equal-value ties toward the earlier position. A monotone stack builds parent, left, and right arrays in one scan. The range minimum between two positions is the value at their lowest common ancestor. This version finds that ancestor by walking parent chains directly; it does not precompute a constant-time LCA table. The input is a static sequence, not a set of distinct keys, so comparing by reading alone would leave duplicate ownership ambiguous.",
         case="Daily inspection readings are 47, 19, 19, 61, 29, and 83. The first 19 becomes the root because the equal 19 at the next position loses the tie. The minimum from positions one through four is 19 at position one; the minimum from positions three through five is 29 at position four. A caller may ask a range whose endpoints are equal, which returns that reading. Empty or reversed intervals fail instead of producing an accidental Python slice result. Inserting another reading between days changes sequence positions and invalidates the tree, so a new static build is required.",
         cost="The monotone stack pushes and pops each of N indices at most once, giving O(N) construction time and O(N) arrays and stack space. A direct ancestor query takes O(H) time and O(H) temporary set space for tree height H; H can be N on monotone input. That limitation is deliberate. Binary lifting would add O(N log N) preprocessing and memory for O(log N) LCA queries; a more specialized static RMQ representation can do better still. This page separates the tree invariant from a particular LCA accelerator. It is useful for understanding why a range minimum can be reduced to ancestry, not as the fastest ready-made range-query engine.",
         mistakes=["Do not sort the readings before building the tree; position order is part of the invariant.", "Do not treat equal values as an unspecified tie.", "Do not call this direct-ancestor query constant time.", "Do not mutate the sequence without rebuilding its parent links."],
         related=["dsa/sparse-table-immutable-range-minimum", "dsa/binary-lifting-lowest-common-ancestor", "dsa/disjoint-sparse-table-range-sum"]),
    dict(path="dsa/leftist-heap-null-path-meld", program="leftist_dispatch_heap.py",
         template="dsa/pairing-heap-two-pass-meld", section="dsa/trees-and-heaps",
         title="Leftist heaps: keep the right spine short for meld",
         summary="Maintain null-path ranks while merging two owned priority queues.",
         definition="A leftist heap is a min-heap with an extra rank: the shortest path from a node to an absent child, counting a leaf as rank one and an absent node as zero. The left child's rank must be at least the right child's rank. Meld selects the smaller root, recursively merges the other heap into its right child, swaps children if their ranks are out of order, then repairs the root rank. The short right spine bounds merge work. This dispatch example orders by (priority, case ID), so equal priorities have a deterministic ID tie. Merge transfers the donor's nodes and empties its public handle; callers must not continue treating the donor as an independent owner of those nodes.",
         case="East dispatch has cases (4,47), (2,83), and (4,19). West has (1,61) and (3,29). Melding West into East produces extraction order (1,61), (2,83), (3,29), (4,19), (4,47). West then reports size zero. If both heap handles retained the same root after merge, popping through either could mutate the other's structure, breaking ownership and rank assertions. A self-merge is rejected for the same reason. This implementation accepts duplicate case IDs if their priority pairs differ; a service that requires one live entry per ID needs a separate keyed membership or handle index.",
         cost="The right spine of a leftist heap has O(log N) length because each node of rank r roots at least 2^r-1 nodes. Meld, push through singleton meld, and pop through child meld therefore take O(log N) worst-case time and recursive stack space here; reading the minimum is O(1). Storage is O(N) nodes with one rank each. This offers a stronger stated merge bound than the simple two-pass pairing model in this curriculum, but it still does not supply an indexed decrease-key operation. Python object pointers and recursion add overhead; an array heap may remain a better choice when queues never need to merge.",
         mistakes=["Do not forget to swap children before recomputing the rank.", "Do not leave the donor handle pointing at transferred nodes.", "Do not assume equal priorities have stable insertion order here.", "Do not advertise decrease-key without a handle and repair protocol."],
         related=["dsa/pairing-heap-two-pass-meld", "dsa/binomial-heap-degree-carry-meld", "dsa/indexed-binary-heap-decrease-key"]),
    dict(path="dsa/potential-disjoint-set-difference-constraints", program="potential_dsu_depot_offsets.py",
         template="dsa/parity-disjoint-set-constraints", section="dsa/graphs-and-disjoint-sets",
         title="Potential disjoint sets: preserve numeric differences across merges",
         summary="Attach roots with offsets so a connected pair can answer an exact difference.",
         definition="A potential disjoint set stores a parent forest and an offset equal to value[node] minus value[parent]. Finding a root sums offsets along the path; path compression rewrites the node's offset relative to the root. A constraint on depots x and y requires value[y] minus value[x] to equal a stated difference. When roots differ, union by component size attaches one root under the other with the offset equation solved algebraically. When roots match, the existing difference is either consistent or contradictory. A contradiction returns false without accepting a new relation. Absolute values remain unknown: adding the same constant to all members of one component changes no answer.",
         case="Depot zero is 47 units below depot one, while depot two is 19 units below depot one. The derived difference from zero to two is 28. A new constraint claiming 29 is rejected. The service can still answer the earlier difference 28 afterward. A disconnected depot returns None rather than a made-up zero; zero is a valid known difference for two equal-level depots. If path compression copied a parent link without accumulating its previous offset, a later query might return the wrong sign even though basic connectivity still looks correct. Randomized checks compare each response with a small explicit graph of accepted equations.",
         cost="With union by size and path compression, each accepted merge or difference query takes inverse-Ackermann amortized time over a sequence of operations, often treated as nearly constant; it stores O(N) parents, sizes, and offsets. The caveat is important: this version cannot remove a constraint or roll back a compression. It also assumes exact integer differences, so it does not model floating measurement tolerance or overflow in fixed-width integer languages. Rejected constraints can still compress paths but do not change the represented differences. For a system that needs to explain which earlier equations caused a contradiction, maintain a separate provenance graph or use an offline algorithm.",
         mistakes=["Do not attach a root without solving the offset sign.", "Do not return zero for two disconnected depots.", "Do not forget to add the old parent offset during path compression.", "Do not treat a rejected contradiction as an accepted edge."],
         related=["dsa/disjoint-set-union-connectivity", "dsa/parity-disjoint-set-constraints", "dsa/disjoint-set-rollback-checkpoints"]),
    dict(path="dsa/static-two-dimensional-range-tree-counting", program="range_tree_depot_counts.py",
         template="dsa/kd-tree-exact-nearest-depot", section="dsa/trees-and-heaps",
         title="Two-dimensional range trees: count a static rectangle",
         summary="Store sorted y coordinates at each x subtree for exact half-open window counts.",
         definition="A two-dimensional range tree organizes a static point set by x in a balanced binary tree. Every node also stores the y coordinates of all points in its subtree in sorted order. When a query rectangle fully covers a node's x range, two binary searches in its y list count points in the half-open y interval without descending to individual leaves. A partially covered x node descends to children; a disjoint node contributes zero. This implementation counts points but does not report their IDs. Duplicate x or y coordinates are permitted and counted individually, while duplicate depot IDs are rejected. The query uses [xLow,xHigh) and [yLow,yHigh), including the lower edges and excluding the upper edges.",
         case="Five facilities include pump-47 at (47,52), valve-19 at (19,61), sensor-61 at (52,58), grid-83 at (180,70), and bay-29 at (47,64). The window x from 15 to 60 and y from 45 to 65 counts four facilities. A narrow window x from 47 to 48 and y from 60 to 65 counts only bay-29. The two points at x=47 stay distinct in every sorted y list. If a facility moves, updating only its leaf leaves stale y arrays along the ancestor path; this static implementation must rebuild from a new snapshot. The same half-open edge rule must be used by both the oracle and the index.",
         cost="Sorting the points costs O(N log N). This direct implementation sorts each node's y list again, giving O(N log-squared N) build time and O(N log N) stored y entries. A query visits O(log N) fully covered canonical subtrees, each with two O(log N) y searches, so O(log-squared N) query time and O(log N) recursion space in a balanced tree. The extra per-level y storage is the price of fast orthogonal counting. A simple static two-dimensional prefix grid may be cheaper for a small dense integer domain; a moving-point hash grid suits frequent updates better. No nearest-neighbor or arbitrary polygon claim follows from this rectangle counter.",
         mistakes=["Do not count a parent and its children in the same query.", "Do not use inclusive upper bounds when the API specifies half-open windows.", "Do not update only a leaf after a point moves.", "Do not describe this counting API as nearest-neighbor search."],
         related=["dsa/two-dimensional-prefix-grid-sums", "dsa/point-region-quadtree-range-report", "dsa/kd-tree-exact-nearest-depot"]),
    dict(path="dsa/van-emde-boas-bounded-successor", program="veb_alert_successor.py",
         template="dsa/binary-radix-longest-prefix-routes", section="dsa/trees-and-heaps",
         title="Van Emde Boas trees: successor in a bounded integer universe",
         summary="Split integer IDs into recursive high and low parts for exact ordered-set changes.",
         definition="A Van Emde Boas tree is an ordered set over a fixed power-of-two integer universe. It stores the current minimum and maximum directly, partitions remaining keys by high bits into low-bit clusters, and uses a recursive summary to identify nonempty clusters. Successor first checks whether a larger key remains in the same cluster; otherwise it asks the summary for the next occupied cluster and returns that cluster's minimum. Insert promotes a new minimum while keeping the previous one in a cluster. Delete must promote the next stored key when removing the minimum and repair the summary when a cluster becomes empty. This implementation allocates clusters lazily but does not expand its universe or store duplicate keys.",
         case="An alert board admits unsigned IDs below 256 and inserts 19, 29, 47, 61, 83, and 103. The successor of 47 is 61; the successor of 83 is 103. After deleting 61, the successor of 47 becomes 83. The minimum remains 19 and maximum 103. A request for an ID outside the universe cannot be inserted, while a successor request above all stored IDs returns None. Deleting a missing key returns false. If the last member of a cluster were removed without removing that cluster from the summary, a later successor might follow an empty cluster and fail even though a higher alert exists.",
         cost="Recursive high/low splitting gives O(log log U) search, insertion, deletion, and successor time for universe size U under the usual constant-time integer-operation model. Minimum and maximum reads are O(1). The lazy Python dictionaries avoid allocating every empty cluster initially, but object overhead is high and worst-case storage can still approach O(U); this is not a compact integer set. A bitset or sorted array can win for a small or nearly full universe, while an ordered tree avoids the fixed-universe restriction. The code is single-process and has no predecessor API or persistent snapshot protocol. Verify bounds and deletion paths rather than assuming asymptotic speed proves suitability.",
         mistakes=["Do not insert an ID outside the configured universe.", "Do not leave an empty cluster advertised in the summary.", "Do not forget to promote the next minimum on deletion.", "Do not assume lazy Python nodes make this representation space-optimal."],
         related=["dsa/chunked-array-bitmap-alert-set", "dsa/binary-trie-maximum-xor-multiset", "dsa/skip-list-ordered-index"]),
    dict(path="dsa/scapegoat-tree-subtree-rebuild-insertion", program="scapegoat_case_insertion.py",
         template="dsa/avl-rotation-height-invariant", section="dsa/trees-and-heaps",
         title="Scapegoat trees: rebuild a deep insertion subtree",
         summary="Use subtree sizes and an insertion-depth threshold instead of rotation metadata.",
         definition="A scapegoat tree is a binary search tree that occasionally rebuilds an unbalanced subtree rather than rotating after every insertion. This insertion-only model uses alpha equal to two thirds. It records the search path, increments ancestor subtree sizes, and compares insertion depth with the logarithmic threshold. If the path is too deep, it walks upward to the first ancestor whose path child exceeds two thirds of that ancestor's size. It flattens that subtree in sorted order, rebuilds a balanced tree, and reconnects the original grandparent. Search itself does not mutate the tree. Duplicate IDs are rejected without changing sizes; deletion and the global rebuild rule for shrinkage are intentionally absent.",
         case="Case IDs 19, 29, 47, 61, 83, 103, 127, 149, and 173 arrive in ascending order. A plain BST would become a chain, but this index rebuilds a subtree when a new path exceeds the depth allowance. The final in-order sequence still matches sorted IDs and an existing lookup for 83 is true. The rebuild counter makes the expensive structural operation visible. If the new subtree is reattached on the wrong side of its grandparent, search order breaks even though every node is still present. If sizes are not recomputed within the rebuilt subtree, a later insertion can choose the wrong scapegoat.",
         cost="Search follows a tree of logarithmic height after the insertion rebalance rule, so it takes O(log N) worst-case time for this insertion-only variant. An insertion can rebuild O(N) nodes at once but costs O(log N) amortized over a sequence; it does not promise low tail latency for one write. The flatten list and recursion use O(S) temporary space for rebuilt subtree size S, while stored nodes and sizes occupy O(N) space. A full mutable scapegoat tree also handles deletion and rebuilds the whole tree after enough shrinkage; those operations are outside this lesson. Python recursion depth is bounded by the maintained tree height here but would need care if this code were extended without its rebalance rule.",
         mistakes=["Do not use the amortized insertion bound as a per-write latency guarantee.", "Do not update ancestor sizes after a duplicate rejection.", "Do not reconnect a rebuilt subtree to the wrong grandparent child.", "Do not claim deletion support from this insertion-only model."],
         related=["dsa/binary-search-tree-order-invariant", "dsa/avl-rotation-height-invariant", "dsa/splay-tree-access-and-join-invariants"]),
    dict(path="dsa/static-xor-filter-membership", program="xor_filter_static_alerts.py",
         template="dsa/cuckoo-filter-fingerprint-relocation", section="dsa/hash-tables",
         title="Static XOR filters: peel a fingerprint membership index",
         summary="Build three-position fingerprints for immutable IDs with explicit rebuild failure.",
         definition="A static XOR filter answers approximate membership for an immutable key set. Each key hashes to three positions in separate slot groups; the XOR of the three stored fingerprints equals a short fingerprint of that key. Construction makes a three-uniform hypergraph of these positions, repeatedly removes degree-one positions, then assigns fingerprints in reverse peel order. A cycle that cannot be peeled causes a new hash seed and a complete rebuild. This example deduplicates IDs before construction, uses eight-bit fingerprints, partitions slots into three groups, and caps seed attempts. An inserted key has no false negative after successful construction; a nonmember can match by chance, so every positive still needs authoritative verification.",
         case="An immutable alert snapshot contains IDs 19, 29, 47, 61, 83, and 103. The filter reports possible membership for 47, 61, and 83. It does not store payloads or prove the IDs still exist in a later snapshot. A dispatch service can use a negative answer to skip a more expensive exact lookup, but it must check the exact index after a positive. If an alert is added, changing one slot would corrupt other keys' equations; rebuild the filter from the new full set and publish it with the matching exact-index version. A failed peel attempt is a construction failure, not permission to publish a filter that might reject a present alert.",
         cost="With sufficient slots and favorable hashes, peeling and assignment are linear in N keys and slots; the bounded retry loop can multiply that work and can fail after its configured attempts. A query performs three slot reads and O(1) hash work. Conceptually, the eight-bit slot array occupies eight times the slot count bits, but this Python list of integers has much greater actual memory overhead. The chosen slot count is deliberately generous and no optimal-size or measured false-positive claim is made. Hash collisions among distinct stored IDs are rejected during construction. The structure is static: deletion, insertion, and synchronization with an exact index require rebuilding or a versioned overlay design.",
         mistakes=["Do not treat a positive answer as exact membership.", "Do not publish a partially peeled filter after a failed seed.", "Do not mutate a slot for one insertion without rebuilding.", "Do not describe Python-list memory as packed fingerprint bytes."],
         related=["dsa/bloom-filter-membership-boundary", "dsa/cuckoo-filter-fingerprint-relocation", "dsa/immutable-index-snapshot-publication"]),
]


for order, lesson in enumerate(lessons):
    path = lesson["path"]
    assert path not in by_path
    program = (root / "work/dsa-programs" / lesson["program"]).read_text().rstrip()
    output = subprocess.run([sys.executable, "-c", program], check=True, capture_output=True, text=True).stdout.strip()
    section = lesson["section"]
    related = [section, subject_root, *lesson["related"], "dsa/projects", "dsa/quizzes"]
    body = "<p>" + html.escape(lesson["definition"]) + "</p>"
    body += "<h2>Operational case</h2><p>" + html.escape(lesson["case"]) + "</p>"
    body += '<h2>Working Python program</h2><pre><code class="language-python">' + html.escape(program, quote=False) + "</code></pre>"
    body += '<h3>Output</h3><pre><code class="language-text">' + html.escape(output) + "</code></pre>"
    body += "<h2>Time, space, and tradeoff</h2><p>" + html.escape(lesson["cost"]) + "</p>"
    body += "<h3>Common Mistakes</h3><ul>" + "".join("<li>" + html.escape(item) + "</li>" for item in lesson["mistakes"]) + "</ul>"
    body += "<h2>Connected lessons</h2>" + links(related)
    entry = copy.deepcopy(by_path[lesson["template"]])
    entry.update(id=str(uuid.uuid5(uuid.NAMESPACE_URL, "aitrove:" + path)), path=path,
                 title=lesson["title"], summary=lesson["summary"], body=body,
                 sort_order=43600 + order * 10, created_at=stamp, updated_at=stamp, published_at=stamp)
    entry["data"].update(section_path=section, related=[{"path": target, "title": by_path[target]["title"]} for target in related])
    entries.append(entry)
    by_path[path] = entry
    for hub_path in (section, subject_root):
        hub = by_path[hub_path]
        module = hub["data"]["modules"][0] if hub_path == section else next(module for module in hub["data"]["modules"] if module["title"] == by_path[section]["title"])
        module["lessons"].append(path)
        hub["body"] += '<p><a href="/' + path + '">' + html.escape(lesson["title"]) + "</a></p>"
        hub["updated_at"] = stamp

groups = [
    dict(paths=[item["path"] for item in lessons[:4]], project="dsa/layout-heap-potential-invariant-audit-project",
         quiz="quizzes/dsa-layout-cartesian-meld-potential-contracts",
         title="Project: audit search layouts, range roots, melds, and numeric constraints",
         intro="Build one dispatch review suite with four independent structures. Load the morning case catalog into an Eytzinger layout, keep immutable daily readings in a Cartesian tree, merge two priority queues through a leftist heap, and maintain depot-level difference equations with a potential disjoint set. Do not force these workloads into one structure. The review record should report each structure's input version, expected answer, and operation cost so a failed case can be reproduced without relying on hidden global state.",
         trace="The sorted case catalog contains 19, 29, 47, 61, 83, 103; lower bound 52 is 61 at rank three. Readings 47, 19, 19, 61, 29, 83 return a first minimum of 19 at position one for range one through four. Merging East and West dispatch heaps yields priorities one, two, three, four, four with case-ID tie order. Depot constraints of plus 47 then minus 19 imply plus 28; a plus-29 constraint is rejected. Assert the donor heap is empty after merge and the earlier depot difference survives the rejected equation.",
         failures="Fuzz catalog lower bounds against bisect on sorted unique IDs, Cartesian ranges against a direct minimum with leftmost tie, heap pops against a sorted multiset, and accepted difference constraints against a small graph traversal. Inject an Eytzinger unsorted append, duplicate Cartesian readings, a self-heap-merge request, and a contradictory depot equation. Document which operations rebuild static structures, which mutate nodes, and which rejected operations leave logical contents unchanged. Inspect tree child links and null-path ranks after each heap mutation; a correct output sequence alone will miss latent pointer damage.",
         mistakes=["Do not read the Eytzinger array as though its slots are sorted.", "Do not discard a duplicate reading before Cartesian construction.", "Do not keep two public owners of melded heap nodes.", "Do not accept a contradictory numeric offset as a new union."],
         questions=[
             ("What order does an Eytzinger array store?", "Breadth-first implicit tree order", "Numerically sorted order", "Random hash-bucket order", "Its child positions are arithmetic indexes; in-order traversal, rather than memory order, restores sorted keys."),
             ("What does this lower-bound query return for an absent high target?", "None if no stored key meets the threshold", "The maximum key regardless of threshold", "The root slot", "A lower bound is the smallest stored key at least the target, so nothing qualifies above the maximum."),
             ("Which two properties define the min Cartesian tree?", "Sequence in-order and parent minimum", "Sorted in-order and parent maximum", "Equal subtree sizes and FIFO order", "The tree preserves original sequence positions in-order while the key pair respects a min-heap relation."),
             ("How does this Cartesian lesson break equal readings?", "Earlier position wins", "Later position wins", "One duplicate is removed", "The pair of reading and position makes the leftmost equal minimum the chosen ancestor."),
             ("What bounds the leftist heap's meld path?", "The right spine's null-path rank", "The number of equal priorities", "A sorted array beside the heap", "The leftist condition keeps the recursive right spine logarithmic in the number of stored nodes."),
             ("What happens to a donor heap after meld?", "Its handle becomes empty", "It retains shared mutable ownership", "It is sorted into an array", "Transferring nodes requires clearing the donor handle so later operations cannot mutate the receiver indirectly."),
             ("What does a potential DSU offset store?", "A node value minus its parent value", "Its absolute geographic height", "The number of child nodes", "Offsets compose along parent links and permit exact relative differences without choosing an absolute origin."),
             ("When does a numeric constraint contradict prior relations?", "Connected endpoints already imply a different difference", "The endpoints were previously disconnected", "The difference happens to be negative", "Within one component the existing potential difference is fixed by accepted constraints."),
             ("What is the query cost of the Eytzinger search path?", "O(log N) comparisons", "O(N) in every case", "O(1) with no comparisons", "Its implicit balanced tree has logarithmic height, though runtime cache behavior needs measurement."),
             ("How expensive is the direct Cartesian ancestor query in the worst case?", "O(N) on a chain", "Always O(1)", "Always O(log log N)", "The query walks ancestor links and a monotone sequence can create a tree of linear height."),
             ("What is the leftist heap's equal-priority tie here?", "Smaller case ID first", "Earlier insertion first", "Larger subtree first", "The stored tuple orders priority and then case ID; it does not retain insertion order."),
             ("Can this potential DSU remove an accepted equation?", "No; it has no rollback or deletion", "Yes; path compression records a full history", "Yes; every query clears an edge", "The parent forest and compressed offsets retain merged relations without a reversible operation ledger."),
         ]),
    dict(paths=[item["path"] for item in lessons[4:]], project="dsa/range-successor-rebuild-filter-audit-project",
         quiz="quizzes/dsa-range-successor-rebuild-filter-contracts",
         title="Project: audit spatial counts, bounded successors, rebuilds, and filter membership",
         intro="Build an alert catalog with four separate query paths: rectangle counts over frozen depot points, successors over bounded unsigned alert IDs, ordered case insertions through a scapegoat tree, and a static XOR membership filter over one published alert snapshot. The service must keep exact indexes as the authority. A filter negative can skip an exact read only when both structures describe the same snapshot version; a filter positive still requires exact verification. Use explicit half-open rectangle bounds and a fixed integer universe.",
         trace="The five depot points include two at x 47. A rectangle [15,60) by [45,65) counts four; a narrow x [47,48) by y [60,65) counts one. Alert IDs 19, 29, 47, 61, 83, 103 live in universe 256. After removing 61, the successor of 47 is 83. Ascending case insertions trigger at least one scapegoat rebuild while preserving sorted membership. The XOR filter contains every alert ID from its build snapshot; nonmember positives are only candidates. Publish a new exact-index version and filter version together after an alert change.",
         failures="Compare randomized rectangle counts with a direct scan, successors with a sorted set, scapegoat membership and subtree sizes with a Python set, and inserted filter keys with exact membership. Force a rectangle boundary point, remove a cluster's final vEB key, insert an out-of-universe ID, and exceed the filter's peel retry budget in a controlled construction test. Make the exact alert index advance while the old filter remains available; do not use a stale negative answer to exclude a newly added alert. Show rebuild cost and temporary allocation alongside query latency before adopting any of these static snapshots.",
         mistakes=["Do not count a point on an excluded rectangle edge.", "Do not leave empty vEB clusters in the summary.", "Do not claim every scapegoat insertion is logarithmic worst-case.", "Do not treat a filter positive as exact or a stale filter negative as current."],
         questions=[
             ("What does each range-tree node retain besides x bounds?", "Sorted y coordinates for its subtree", "Only one randomly selected point", "A heap of query IDs", "A fully covered x subtree can count y values with two binary searches over its sorted secondary list."),
             ("Which rectangle edges are excluded here?", "The upper x and y bounds", "The lower x and y bounds", "Every integer coordinate", "Both axes use half-open intervals, so points equal to either upper bound are excluded."),
             ("What bounds a Van Emde Boas key?", "A fixed power-of-two integer universe", "The current number of nodes only", "Any arbitrary string", "The recursive high/low split assumes unsigned keys from zero through U minus one."),
             ("What must deletion do when a vEB cluster becomes empty?", "Remove that cluster from the summary", "Keep it advertised forever", "Change every remaining key", "The summary tracks nonempty clusters; stale membership there can direct successor into an empty branch."),
             ("What triggers scapegoat rebuilding after insertion?", "An excessive path and a size-imbalanced ancestor", "Every ordinary successful search", "A hash collision", "Depth beyond the logarithmic allowance leads to a subtree whose child exceeds the configured size fraction."),
             ("What is the worst cost of one scapegoat insertion?", "O(N) when a large subtree rebuilds", "Always O(1)", "Always O(log log N)", "The amortized logarithmic sequence bound does not cap an individual rebuild's linear work."),
             ("What does an XOR filter positive mean?", "The key may be present and needs exact verification", "The key is proved present", "The key was inserted after the filter was built", "Short fingerprints can collide, so only a negative answer is definitive for the built set."),
             ("What follows a failed XOR peel attempt?", "Try a new seed and rebuild before publication", "Publish partial slots", "Delete arbitrary keys silently", "A cyclic placement cannot assign all required fingerprints; publishing it could create false negatives."),
             ("What is the direct range-tree build cost here?", "O(N log-squared N)", "O(1) with no sorting", "O(N cubed) by definition", "This implementation re-sorts y values at each balanced x level after the initial x sort."),
             ("What is the vEB successor bound under its integer model?", "O(log log U)", "O(N) for every nonempty set", "O(1) without assumptions", "Recursive high/low partitioning reduces the universe logarithm in each level under constant-time integer operations."),
             ("Does the scapegoat example delete case IDs?", "No; it models insertion and search only", "Yes; every search deletes its target", "Yes; an implicit expiry queue does it", "Deletion and shrink-triggered global rebuilding require additional operations absent from this insertion-only example."),
             ("When is a filter negative safe to skip an exact read?", "When its version matches the exact snapshot", "After any later alert insertion", "Only if the key also has an HTML title", "An immutable filter knows its construction set; a newer exact index may contain keys the old filter never saw."),
         ]),
]


for group_number, group in enumerate(groups):
    project_path = group["project"]
    quiz_path = group["quiz"]
    assert project_path not in by_path and quiz_path not in by_path
    project = copy.deepcopy(by_path["dsa/allocation-ownership-coalescing-audit-project"])
    project.update(id=str(uuid.uuid5(uuid.NAMESPACE_URL, "aitrove:" + project_path)), path=project_path,
                   title=group["title"], summary="Compare four new structures with exact reference models and failure traces.",
                   sort_order=43690 + group_number * 20, created_at=stamp, updated_at=stamp, published_at=stamp)
    project["data"].update(reading_minutes=35, related=[{"path": path, "title": by_path[path]["title"]} for path in group["paths"]])
    project["body"] = "<p>" + html.escape(group["intro"]) + "</p>"
    project["body"] += "<h2>Acceptance trace</h2><p>" + html.escape(group["trace"]) + "</p>"
    project["body"] += "<h2>Failure and cost review</h2><p>" + html.escape(group["failures"]) + "</p>"
    project["body"] += "<h3>Common Mistakes</h3><ul>" + "".join("<li>" + html.escape(item) + "</li>" for item in group["mistakes"]) + "</ul>"
    project["body"] += "<h2>Connected lessons</h2>" + links(group["paths"] + ["dsa/projects", "dsa/quizzes", subject_root])
    entries.append(project)
    by_path[project_path] = project
    balanced = []
    assert len(group["questions"]) == 12
    for number, (prompt, correct, wrong_one, wrong_two, explanation) in enumerate(group["questions"]):
        assert len(explanation) >= 60, prompt
        answer = number % 3
        options = [wrong_one, wrong_two]
        options.insert(answer, correct)
        balanced.append({"prompt": prompt, "options": options, "answer": answer, "explanation": explanation})
    quiz = copy.deepcopy(by_path["quizzes/dsa-splay-and-resident-history-contracts"])
    quiz.update(id=str(uuid.uuid5(uuid.NAMESPACE_URL, "aitrove:" + quiz_path)), path=quiz_path,
                title=group["title"].replace("Project: audit ", "Check "),
                summary="Twelve explained decisions about four distinct structure invariants.",
                sort_order=43700 + group_number * 20, created_at=stamp, updated_at=stamp, published_at=stamp)
    quiz["data"].update(duration_minutes=20,
                        related=[{"path": path, "title": by_path[path]["title"]} for path in group["paths"] + [project_path]],
                        questions=balanced)
    quiz["body"] = "<p>Choose the invariant or failure response that follows from each operation contract. Review the working program and compare it with a small direct oracle.</p><h2>Lessons</h2>" + links(group["paths"]) + "<h2>Design exercise</h2>" + links([project_path, subject_root])
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
        entry["body"] += '<p>Compare its update and query contract with ' + ", ".join(
            '<a href="/' + other + '">' + html.escape(by_path[other]["title"]) + "</a>" for other in peers)
        entry["body"] += ', then complete the <a href="/' + project_path + '">structure audit</a> and <a href="/' + quiz_path + '">decision quiz</a>.</p>'
        entry["updated_at"] = stamp

for old_path, target in [
    ("dsa/resizable-array-growth-and-insert-cost", "dsa/eytzinger-array-search-layout"),
    ("dsa/immutable-index-snapshot-publication", "dsa/eytzinger-array-search-layout"),
    ("dsa/sparse-table-immutable-range-minimum", "dsa/cartesian-tree-static-range-minimum"),
    ("dsa/binary-lifting-lowest-common-ancestor", "dsa/cartesian-tree-static-range-minimum"),
    ("dsa/pairing-heap-two-pass-meld", "dsa/leftist-heap-null-path-meld"),
    ("dsa/binomial-heap-degree-carry-meld", "dsa/leftist-heap-null-path-meld"),
    ("dsa/parity-disjoint-set-constraints", "dsa/potential-disjoint-set-difference-constraints"),
    ("dsa/disjoint-set-rollback-checkpoints", "dsa/potential-disjoint-set-difference-constraints"),
    ("dsa/two-dimensional-prefix-grid-sums", "dsa/static-two-dimensional-range-tree-counting"),
    ("dsa/point-region-quadtree-range-report", "dsa/static-two-dimensional-range-tree-counting"),
    ("dsa/chunked-array-bitmap-alert-set", "dsa/van-emde-boas-bounded-successor"),
    ("dsa/skip-list-ordered-index", "dsa/van-emde-boas-bounded-successor"),
    ("dsa/avl-rotation-height-invariant", "dsa/scapegoat-tree-subtree-rebuild-insertion"),
    ("dsa/splay-tree-access-and-join-invariants", "dsa/scapegoat-tree-subtree-rebuild-insertion"),
    ("dsa/bloom-filter-membership-boundary", "dsa/static-xor-filter-membership"),
    ("dsa/cuckoo-filter-fingerprint-relocation", "dsa/static-xor-filter-membership"),
]:
    entry = by_path[old_path]
    entry["body"] += '<p><a href="/' + target + '">' + html.escape(by_path[target]["title"]) + "</a> adds a distinct structure contract to compare.</p>"
    entry["updated_at"] = stamp

fixture.write_text(json.dumps(entries, ensure_ascii=False, indent=2) + "\n")
print(json.dumps({"lessons": len(lessons), "projects": len(groups), "quizzes": len(groups),
                  "new_routes": len(lessons) + 2 * len(groups)}))
