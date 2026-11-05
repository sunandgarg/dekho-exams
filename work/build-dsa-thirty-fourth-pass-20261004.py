"""Add distinct Data Structures pages, runnable models, and linked assessments."""

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
    return "<ul>" + "".join(
        '<li><a href="/' + path + '">' + html.escape(by_path[path]["title"]) + "</a></li>"
        for path in paths) + "</ul>"


lessons = [
    dict(path="dsa/x-fast-trie-static-case-predecessor", program="static_xfast_case_predecessor.py",
         template="dsa/van-emde-boas-bounded-successor", section="dsa/trees-and-heaps",
         title="X-fast trie: predecessor and successor in a fixed integer universe",
         summary="Hash every binary-prefix level and find the longest present prefix by length search.",
         definition="An X-fast trie indexes fixed-width integer keys by every binary prefix length. Each prefix record stores the smallest and largest key below it, and the leaves retain their immediate predecessor and successor. An exact key is found in the leaf map. For a missing key, binary search over prefix lengths finds the deepest prefix shared with an indexed key. The next bit says whether the target fell into the absent left or right branch; subtree extrema and leaf neighbors then return its floor or ceiling. This implementation freezes the key set and uses ordinary Python dictionaries rather than promising deterministic hash-table probes. Floor and ceiling are inclusive, so a stored target returns itself.",
         case="A catalog contains case IDs 19, 47, 83, and 149 in an eight-bit universe. The floor and ceiling of 61 are 47 and 83. An exact query for 19 returns 19 as its floor, while one for 149 returns 149 as its ceiling. Below the first ID the floor is absent; above the last ID the ceiling is absent. An out-of-universe request fails instead of silently wrapping to eight bits. Every level must describe the same frozen snapshot: inserting an ID in only the leaf table would leave the longest-prefix search with stale extrema.",
         cost="Construction writes at most W+1 prefix records per key, giving O(NW) time and space for N keys of W bits. A predecessor or successor query makes O(log W) expected-time dictionary probes under ordinary hash assumptions and constant-width arithmetic; in Python, big-integer shift and hash costs also matter. A lookup can degrade with pathological hash behavior. This static teaching version omits the O(W) update procedure. A Van Emde Boas tree offers a different bounded-universe tradeoff; a sorted array is often smaller when updates are absent and logarithmic binary search is acceptable.",
         mistakes=["Do not confuse a predecessor with a lower-bound insertion position.", "Do not omit the leaf-neighbor link after falling into an absent left branch.", "Do not update only one prefix level after changing the key snapshot.", "Do not promise a deterministic dictionary lookup bound in this Python implementation."],
         related=["dsa/van-emde-boas-bounded-successor", "dsa/binary-radix-longest-prefix-routes", "dsa/piecewise-interpolation-rank-catalog"]),
    dict(path="dsa/persistent-radix-vector-path-copying", program="persistent_radix_case_vector.py",
         template="dsa/persistent-bitmap-hamt-alert-map", section="dsa/array-data-structure-guide",
         title="Persistent radix vectors: copy one indexed path per revision",
         summary="Branch a fixed-width index trie so older vector revisions retain their values.",
         definition="A persistent radix vector routes an integer position through a shallow, fixed-branching tree. Replacing one value copies only nodes on that index path and shares every untouched child with the previous root. Appending follows the next position; when the root's current capacity is full, a new root raises the height and keeps the old root as its first child. Each returned vector carries its own root, height, and length. The program uses four-way tuples and no mutable tail buffer so the sharing rule stays visible. An old revision remains readable after later replacements and appends, provided callers treat stored payload objects as immutable values.",
         case="The morning case vector is 19, 47, 83, 149, 173. A correction produces a new revision with 103 at position two, and an evening append adds 211. The morning revision still reports 83 at position two. Five elements cross the four-slot root capacity, so this trace exercises the height increase rather than only a single leaf. A shallow root copy would fail if its child tuples were edited in place; this version allocates new tuples all the way to the changed leaf. It does not implement arbitrary middle insertion, which would renumber later positions.",
         cost="At branching factor B and length N, indexed read visits O(log_B N) nodes. Replace and append copy O(B log_B N) tuple slots in this direct Python implementation and retain O(log_B N) new nodes per revision; the root-height increase is constant additional work. Listing all values takes O(N log_B N) here because it repeatedly calls indexed read. Historical roots keep shared subtrees alive, so retaining many revisions costs memory. A mutable resizable array has simpler constants when revisions are unnecessary; a persistent ordered map serves keyed lookup rather than contiguous positions.",
         mistakes=["Do not mutate a shared child tuple or mutable payload and call the revision immutable.", "Do not forget the root height increase when length reaches its current capacity.", "Do not claim constant-time middle insertion for an indexed radix vector.", "Do not compare revision memory to one flat array while retaining every old root."],
         related=["dsa/resizable-array-growth-and-insert-cost", "dsa/persistent-bitmap-hamt-alert-map", "dsa/persistent-ordered-index-path-copying"]),
    dict(path="dsa/static-compressed-suffix-tree-pattern-locations", program="static_suffix_tree_incidents.py",
         template="dsa/suffix-array-lcp-incident-search", section="dsa/trees-and-heaps",
         title="Compressed suffix trees: locate patterns across a frozen text",
         summary="Insert all terminated suffixes into compressed edges and collect matching leaves.",
         definition="A suffix tree is a compressed trie of every suffix of one text followed by a unique sentinel. Each edge stores start and end offsets into the same retained text, not a copied substring. When a new suffix disagrees partway through an edge, insertion splits that edge and hangs both old and new continuations below the branch. A pattern follows edges character by character; it may finish inside an edge, in which case every terminal below that edge is a match. Leaf terminals retain original start positions. This page uses repeated suffix insertion to expose edge splits. It does not implement a linear-time suffix-tree builder.",
         case="The frozen incident string cabacaba contains aba at offsets one and five. The pattern bac appears at offset two; zzz has no matching edge. A query ending in the middle of a compressed edge is still valid, so stopping only at explicit branch nodes would miss occurrences. The sentinel cannot occur inside user text or search patterns; otherwise suffix termination is ambiguous. Positions are Python code-point offsets, not byte or grapheme positions. If incident text changes, its suffix leaves and edge offsets refer to the old snapshot and the tree needs rebuilding.",
         cost="There are O(N) explicit nodes and edges for a terminated text of length N, while the text is stored once and edges use index pairs. This direct construction can compare O(N squared) characters across suffix insertions in the worst case. Pattern traversal costs O(M) character comparisons for pattern length M; reporting K locations costs O(K log K) here because returned offsets are sorted. Output itself needs O(K) memory. Python dictionaries and nodes add substantial overhead. A suffix array provides a compact ordered alternative, and an FM-index changes the count-versus-locate tradeoff for frozen text.",
         mistakes=["Do not require a pattern to end exactly at an explicit node.", "Do not copy every edge label into a separate string and claim shared-text storage.", "Do not accept the sentinel as ordinary incident input.", "Do not call this repeated-insertion builder linear-time."],
         related=["dsa/suffix-array-lcp-incident-search", "dsa/suffix-automaton-online-substrings", "dsa/fm-index-backward-substring-search"]),
    dict(path="dsa/disjoint-interval-union-maintenance-windows", program="disjoint_maintenance_windows.py",
         template="dsa/interval-tree-max-endpoint-pruning", section="dsa/array-data-structure-guide",
         title="Disjoint interval unions: maintain covered maintenance time",
         summary="Coalesce touching half-open windows, split on removal, and measure covered duration.",
         definition="A disjoint interval union stores covered time as sorted, nonoverlapping half-open spans [start,end). Adding a window sorts it with the existing spans and merges any overlap or touching boundary. Removing a window preserves unaffected spans and may split one span into two pieces. Membership binary-searches starts, then checks the selected end. The covered length is the sum of each disjoint span width, so overlapping requests count their shared minutes only once. This model stores integral or real time coordinates without time zones; the caller is responsible for converting wall-clock times into a consistent scale.",
         case="Three maintenance requests [19,47), [61,83), and [47,61) coalesce into [19,83), measuring 64 units. Removing [29,71) leaves [19,29) and [71,83). Time 25 is covered; time 50 is not. The equal boundary at 47 must merge in the add operation, or a supposedly disjoint representation would contain adjacent spans that should form one coverage run. Removing a range outside coverage is harmless. Empty or reversed windows are rejected, because their width and edge semantics would otherwise be unclear.",
         cost="This direct list model sorts O(R) spans on add, costing O(R log R) time, and scans O(R) spans on removal for R current disjoint runs. A membership query uses O(log R) tuple comparisons; total covered length is O(R) unless maintained as an aggregate during every update. The representation occupies O(R) space and O(R) temporary memory for add or removal. An interval tree answers overlap questions for independent original intervals, while this structure deliberately discards request identity to represent only the union. A balanced ordered map could reduce localized edit costs but needs more machinery.",
         mistakes=["Do not count overlapping windows twice when reporting covered duration.", "Do not treat a half-open right endpoint as covered.", "Do not forget that removal can split one stored span into two.", "Do not use this union to recover the identity of every original request."],
         related=["dsa/interval-tree-max-endpoint-pruning", "dsa/avl-interval-index-insertion", "dsa/coordinate-compression-ordered-ranks"]),
    dict(path="dsa/csr-delta-overlay-graph-updates", program="csr_delta_road_graph.py",
         template="dsa/csr-sparse-graph-storage", section="dsa/graphs-and-disjoint-sets",
         title="CSR delta overlays: stage road edits before compaction",
         summary="Keep a compact base graph and small add/delete sets until a rebuild is justified.",
         definition="Compressed sparse row storage packs sorted neighbors of each source vertex into one target array and an offset table. A road editor cannot insert one target without shifting later packed rows. A delta overlay leaves the base untouched, records added edges and tombstones for deleted base edges, and merges those three sources when serving a neighbor query. Deleting an edge that exists only in the added set cancels its addition. Adding a deleted base edge cancels its tombstone. Compaction writes the logical graph into fresh CSR arrays, then clears both overlays. This example models directed, simple edges; an undirected road would require paired updates.",
         case="The base has road zero to one and zero to three. A dispatch edit removes zero to one and adds zero to four, so the logical neighbors of zero are three and four before compaction. Rebuilding produces the same answer and new offsets. If a previously staged addition is removed before compaction, it must not become a base tombstone; similarly, adding a deleted base edge must clear its tombstone. A reader that accesses only packed targets while edits are pending sees an obsolete snapshot, so the query path and version boundary must be explicit.",
         cost="Building or compacting from E logical edges costs O(V+E log D) here because every vertex's degree-D row is sorted, and uses O(V+E) base storage. A neighbor read copies its base row and combines overlay sets, then sorts the result, costing O(D+ A + T + R log R) for base degree D, staged additions A, tombstones T, and result size R. Python list membership checks in add and remove cost O(D). Overlay storage grows with un-compacted edits. This is a single-process model without atomic publication; a real concurrent graph reader needs a snapshot or synchronization protocol.",
         mistakes=["Do not query the packed base alone while edits are staged.", "Do not store an added edge and a tombstone for the same logical edge.", "Do not treat one directed edit as an undirected road update.", "Do not clear overlays before the rebuilt CSR arrays are ready."],
         related=["dsa/csr-sparse-graph-storage", "dsa/bitset-adjacency-matrix-dense-graph", "dsa/immutable-index-snapshot-publication"]),
    dict(path="dsa/bitset-transitive-reachability-snapshot", program="bitset_reachability_snapshot.py",
         template="dsa/bitset-adjacency-matrix-dense-graph", section="dsa/graphs-and-disjoint-sets",
         title="Reachability bitsets: precompute directed paths for a fixed graph",
         summary="Propagate packed reachable-vertex rows across each intermediate vertex.",
         definition="A reachability snapshot gives each directed graph vertex a bit row. The initial row contains itself and its outgoing neighbors. For each intermediate vertex k, any source row that already reaches k absorbs every bit in k's row. After all intermediates, bit j in row i is set exactly when a path from i to j exists. Including the diagonal treats a zero-edge path as reachability. The algorithm supports cycles naturally: a strongly connected group ends with the same group bits in each member's row. It is a frozen all-pairs index, suited to many queries over one relatively small graph rather than occasional queries after road edits.",
         case="A six-node directed network has a cycle through zero, one, and two, then a one-way route from two through four to five. Node zero reaches five, but five cannot reach zero. Starting at one yields reachable nodes zero, one, two, four, and five. If the diagonal bit is omitted, self-reachability can depend on whether a cycle happens to exist, changing the stated query contract. Adding a new road after precomputation can expose paths absent from several rows; this example offers no incremental repair and must be rebuilt from the new graph.",
         cost="The loop runs O(V squared) Python row tests and up to O(V squared) big-integer unions; a row spans O(V) bits, so the machine-word model is O(V cubed divided by word width) work and O(V squared) bits of storage. Python big integers allocate and scan multiple internal words, so a bit test is not a strict hardware O(1) claim for unbounded V. Listing every destination costs O(V). Breadth-first search costs O(V+E) for one source on demand and may be preferable for a large graph with few reachability queries.",
         mistakes=["Do not confuse directed reachability with undirected connectivity.", "Do not leave out each vertex's self bit when zero-edge paths count.", "Do not reuse this matrix after graph topology changes.", "Do not claim Python big-integer operations cost one CPU instruction for arbitrary graph size."],
         related=["dsa/bitset-adjacency-matrix-dense-graph", "dsa/graph-adjacency-list-and-bfs", "dsa/csr-sparse-graph-storage"]),
    dict(path="dsa/gap-label-order-maintenance", program="gap_label_dispatch_order.py",
         template="dsa/segmented-array-prefix-block-locate", section="dsa/array-data-structure-guide",
         title="Gap labels: compare dispatch order across middle inserts",
         summary="Assign spare integer labels between neighbors and relabel when a gap closes.",
         definition="An order-maintenance label maps every task ID to an increasing integer. Comparing two current labels answers which task comes first without scanning the list. Inserting after a known anchor chooses an unused integer between its label and the next task's label. When no integer remains, the model relabels the full sequence with fresh gaps before inserting. The ordered Python list is retained to find anchors and display the order. That list makes middle insertion and anchor search linear; this is a gap-label mechanics model, not a constant-time full order-maintenance implementation. Labels can change at relabel, so clients must compare through the current map rather than persist old labels as external IDs.",
         case="Starting with tasks T-19 and T-83, repeated inserts immediately after T-19 consume progressively smaller gaps and eventually trigger a relabel. The final order is T-19, T-71, T-67, T-61, T-52, T-47, T-83. The current labels still put T-19 before T-83. A duplicate task ID is rejected, because one ID cannot have two positions in the map. If a user cached T-47's old label as a durable priority, a later relabel could silently invalidate that interpretation even though the task order itself remains correct.",
         cost="A comparison of two present IDs is expected O(1) dictionary work. Insert-after takes O(N) to locate the anchor and shift the Python list, and a relabel adds O(N) work; removal also shifts O(N) entries. Memory is O(N). The arithmetic gap decision itself is constant-time, but it does not erase list costs or prove an amortized bound for arbitrary repeated inserts into one gap. A linked list with direct node handles would remove list shifting, while a full order-maintenance structure needs a stronger local relabel schedule.",
         mistakes=["Do not expose labels as permanent business identifiers.", "Do not claim constant-time insertion while using list.index and list.insert.", "Do not insert a second position for an existing task ID.", "Do not leave equal labels after a gap is exhausted."],
         related=["dsa/segmented-array-prefix-block-locate", "dsa/implicit-treap-range-reversal", "dsa/doubly-linked-list-relink-and-ownership"]),
    dict(path="dsa/skew-heap-self-adjusting-meld", program="skew_heap_dispatch_meld.py",
         template="dsa/leftist-heap-null-path-meld", section="dsa/trees-and-heaps",
         title="Skew heaps: meld priorities by swapping child paths",
         summary="Use a self-adjusting heap with no rank metadata and explicit donor ownership.",
         definition="A skew heap is a heap-ordered binary tree whose core operation melds two roots. The smaller root stays above; its right subtree is melded with the other heap, then its left and right children swap. No null-path rank is stored. Push melds a singleton node, and pop removes the current root by melding its two children. This implementation compares priority first and task ID second, giving reproducible ties. A merge-from operation transfers the donor root and clears the donor, so the same mutable nodes are never owned by two live heap objects. The tree can be skewed after one operation even though operation sequences have a useful amortized bound.",
         case="Two dispatch queues hold priorities 47 and 19 in one heap and 61 and 29 in another. After transfer, popping four times returns tasks in 19, 29, 47, 61 priority order, and the donor has size zero. If the donor retained its root, a later pop on either owner would mutate nodes still reachable from the other queue. The example lacks direct handles and decrease-key; changing a task's priority requires a separate indexed design or reinsertion policy that prevents an obsolete entry from winning.",
         cost="Meld, push, and pop have O(log N) amortized time over operation sequences but O(N) worst-case time for a single highly skewed operation. This recursive Python form can also hit recursion limits on an adverse long path. Each node stores two child pointers and a priority pair, giving O(N) heap space; meld uses O(H) call-stack space for path height H. A leftist heap keeps rank metadata for a worst-case logarithmic right spine, while a binary heap may be simpler when melding is not needed. No empirical speed claim follows from these bounds.",
         mistakes=["Do not retain a mutable donor root after transferring ownership.", "Do not report worst-case logarithmic time for every individual meld.", "Do not forget the child swap after melding down the right path.", "Do not present this model as supporting decrease-key by task handle."],
         related=["dsa/leftist-heap-null-path-meld", "dsa/pairing-heap-two-pass-meld", "dsa/binomial-heap-degree-carry-meld"]),
]

for order, lesson in enumerate(lessons):
    path = lesson["path"]
    assert path not in by_path
    program = (root / "work/dsa-programs" / lesson["program"]).read_text().rstrip()
    output = subprocess.run([sys.executable, "-c", program], check=True, capture_output=True, text=True).stdout.strip()
    related = [lesson["section"], subject_root, *lesson["related"], "dsa/projects", "dsa/quizzes"]
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
                 sort_order=45000 + order * 10, created_at=stamp, updated_at=stamp, published_at=stamp)
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


questions = {
    "dsa/x-fast-trie-static-case-predecessor": [
        ("What does a missing-key floor query return?", "The largest stored ID no greater than the target", "The first greater stored ID", "The number of prefix levels", "The absent branch and its neighboring leaf determine the greatest stored key below the target; exact stored targets return themselves."),
        ("Why keep prefix records at every bit length?", "Binary-search the longest present query prefix", "Sort the entire catalog on every read", "Make all future insertions free", "Each level answers whether the target shares that prefix with any stored key, reducing the number of prefix probes."),
        ("What happens when one new case ID is added to this model?", "Rebuild the frozen prefix and leaf records", "Edit only the previous pointer", "Keep old extrema without checking", "A new key can change prefixes, subtree extrema, and leaf neighbors at several levels, which this static example does not update."),
    ],
    "dsa/persistent-radix-vector-path-copying": [
        ("Which nodes change during a vector replacement?", "Only nodes on the selected index path", "Every stored leaf", "Only the root pointer", "Path copying allocates a new route to the revised leaf while untouched branches remain shared with the old revision."),
        ("What happens when append exceeds current root capacity?", "A new root raises the tree height", "Old revisions are overwritten", "The final leaf is discarded", "The old root becomes a child of a taller root, preserving all existing indexes while exposing the next range of positions."),
        ("Why can a mutable payload still affect old revisions?", "Roots share the same referenced payload object", "Tuple paths always deep-copy payloads", "Append removes historical roots", "Structural sharing protects tuple links, but it does not freeze an arbitrary object stored inside a leaf."),
    ],
    "dsa/static-compressed-suffix-tree-pattern-locations": [
        ("Can a valid search end inside a compressed edge?", "Yes; all terminals below that edge match", "No; it must reach an explicit leaf", "Only when the pattern is empty", "An edge represents several characters, so a pattern may finish before the edge does and still prefix every suffix below it."),
        ("What does an edge store in this model?", "Start and end offsets into one retained text", "A fresh copy of every substring", "Only a document score", "Offset pairs share the original terminated string and avoid copying the edge label into each tree node."),
        ("What is the builder's time boundary?", "Repeated insertion may compare quadratic text", "It is guaranteed linear-time construction", "It never compares characters", "The code inserts every suffix directly and can revisit long shared prefixes; it does not use a linear-time construction algorithm."),
    ],
    "dsa/disjoint-interval-union-maintenance-windows": [
        ("How much coverage remains after removing [29,71) from [19,83)?", "Two spans: [19,29) and [71,83)", "One span [19,83)", "No coverage remains", "A removal cuts out only its intersection, leaving the prefix and suffix portions as separate half-open runs."),
        ("How should touching windows [19,47) and [47,61) be stored?", "As one union span [19,61)", "As two overlapping spans", "As an empty interval", "The touching boundary leaves no uncovered coordinate between the windows, so a canonical union coalesces them."),
        ("Can this union recover who requested each original window?", "No; merging discards request identity", "Yes; every source record is retained", "Only when all windows overlap", "The stored spans represent covered coordinates rather than the original submitted intervals, so provenance needs another table."),
    ],
    "dsa/csr-delta-overlay-graph-updates": [
        ("What should a neighbor query read before compaction?", "The base row adjusted by additions and tombstones", "The packed base only", "The additions only", "Logical graph state combines the immutable CSR row with staged edge changes; reading one layer alone returns an incomplete answer."),
        ("What does removing a staged added edge do?", "Cancel that addition without a base tombstone", "Delete every edge from its source", "Rewrite unrelated CSR rows", "An edge absent from the packed base has no base record to mask, so its pending addition is simply dropped."),
        ("What must happen before clearing overlays?", "Build the replacement CSR arrays from logical neighbors", "Drop all pending edits", "Publish only the old offsets", "Compaction must first materialize the graph seen by queries; otherwise clearing deltas loses accepted edits."),
    ],
    "dsa/bitset-transitive-reachability-snapshot": [
        ("Why initialize every vertex's own bit?", "The contract counts a zero-edge path to itself", "All graph edges are undirected", "It shortens the vertex list", "Self bits make reflexive reachability explicit even for an isolated vertex with no cycle or outgoing edge."),
        ("When does row i absorb row k?", "When row i already contains bit k", "When i and k have equal numeric IDs", "After every row is cleared", "If source i reaches intermediate k, any destination reachable from k also becomes reachable from i."),
        ("What happens after adding a new directed edge?", "Rebuild or implement a separate update procedure", "Old reachability rows remain exact", "Only the target's own bit changes", "A new edge can create paths for many earlier sources, so this immutable closure no longer matches the graph."),
    ],
    "dsa/gap-label-order-maintenance": [
        ("What does a label comparison answer?", "The relative order of two current tasks", "Their durable business identities", "The cost of the next insertion", "Current increasing labels encode sequence order; a later relabel may change values while preserving that order."),
        ("What occurs when no integer lies between two labels?", "Relabel the sequence with fresh gaps", "Assign a duplicate label", "Discard the anchor task", "The model creates space by spacing every current task again before choosing a label for the new position."),
        ("Why is insert-after still linear in this Python model?", "Anchor lookup and list shifting cost O(N)", "Label comparison scans every edge", "Dictionary lookup sorts the tasks", "Choosing a midpoint is cheap, but finding the list position and inserting there still require linear work."),
    ],
    "dsa/skew-heap-self-adjusting-meld": [
        ("What happens after melding along the selected root's right path?", "Swap its left and right children", "Recompute a null-path rank", "Reverse every task ID", "A skew heap performs this unconditional child swap as its self-adjustment and stores no rank metadata."),
        ("What must a donor heap do after merge-from?", "Clear its root and size after transferring nodes", "Retain the shared root for independent mutation", "Delete the receiver root", "Both heaps must not mutate the same node graph independently; transfer leaves the donor empty in this model."),
        ("Does every skew-heap operation take worst-case logarithmic time?", "No; one operation can traverse a linear path", "Yes; every tree is perfectly balanced", "Yes; Python recursion is constant depth", "The logarithmic bound is amortized over sequences; a particular meld can encounter a highly skewed right path."),
    ],
}

groups = [
    dict(paths=[lesson["path"] for lesson in lessons[:4]],
         project="dsa/predecessor-vector-suffix-interval-audit-project",
         quiz="quizzes/dsa-predecessor-vector-suffix-interval-contracts",
         title="Project: audit predecessor, revision, substring, and coverage snapshots",
         intro="Build four review indexes over separate inputs: fixed-width case IDs, versioned case sequences, frozen incident text, and a changing set of maintenance times. The X-fast prefix catalog answers inclusive floor and ceiling within one integer universe. A persistent radix vector preserves old case order after a correction. A suffix tree lists exact pattern offsets in a text snapshot. A disjoint interval union measures coverage after add and removal operations. Record an input version beside every static answer; the interval union alone accepts edits in place in this group.",
         trace="For case IDs 19, 47, 83, 149, the floor and ceiling of 61 are 47 and 83. A five-case vector keeps 83 in its morning revision after a corrected revision replaces it with 103 and appends 211. In cabacaba, aba occurs at offsets one and five. Maintenance requests [19,47), [61,83), and [47,61) cover 64 units; removing [29,71) leaves [19,29) and [71,83). Keep half-open time boundaries distinct from inclusive integer floor queries.",
         failures="Compare every integer target in a small universe with bisect on the sorted catalog. Retain many vector revisions, branch from an older revision, and compare their values with copied lists. For random short text, scan each candidate offset and compare suffix-tree results, including patterns ending inside an edge. Fuzz interval additions and removals against a set of covered integer coordinates. Exercise empty structures, a forbidden sentinel, a vector index out of range, a target outside its bit width, touching intervals, and the gap left by removal. Do not infer a linear-time suffix-tree builder from its compressed shape.",
         mistakes=["Do not mix an old prefix table with newly inserted IDs.", "Do not mutate payload objects shared by vector revisions.", "Do not require an exact match to stop at a suffix-tree node.", "Do not count an overlapping maintenance minute twice."]),
    dict(paths=[lesson["path"] for lesson in lessons[4:]],
         project="dsa/overlay-reachability-order-meld-audit-project",
         quiz="quizzes/dsa-overlay-reachability-order-meld-contracts",
         title="Project: audit graph overlays, path bits, labels, and heap ownership",
         intro="Review one dispatch system through four distinct structure contracts. A CSR delta overlay stages directed road edits before a compact rebuild. A reachability bitset answers many path questions for one frozen directed topology. Gap labels compare task order while middle inserts can force a relabel. A skew heap melds priority queues and transfers mutable node ownership. These structures can coexist, but their versions and operations cannot be substituted: reachability rows built before a road edit are stale even if the overlay reports the new neighbors correctly.",
         trace="Remove road zero to one and add road zero to four; the logical neighbor row becomes three and four before and after CSR compaction. In a separate six-node path snapshot, node zero reaches five but five does not reach zero. Repeated inserts after T-19 trigger one relabel yet leave T-19 before T-83. Melding two priority queues yields tasks at priorities 19, 29, 47, and 61, and empties the donor. Record when each snapshot is rebuilt and who owns each mutable node.",
         failures="Fuzz overlay add, remove, and compact operations against a direct edge set, including re-adding a deleted base edge. Compare every reachability row against a breadth-first scan for random directed graphs with cycles and isolated vertices. Repeatedly insert after one anchor and verify that current labels are strictly increasing with task order; confirm old labels are not durable identifiers. Merge heaps built in two owners, drain by sorted priority and ID, and assert the donor cannot still pop the transferred nodes. A graph edit should invalidate the old reachability snapshot until it is rebuilt.",
         mistakes=["Do not query only base CSR while deltas remain.", "Do not use a closure row after topology changes.", "Do not cache order labels as permanent IDs.", "Do not leave a mutable donor heap attached after meld."]),
]

for group_number, group in enumerate(groups):
    project_path, quiz_path = group["project"], group["quiz"]
    assert project_path not in by_path and quiz_path not in by_path
    project = copy.deepcopy(by_path["dsa/allocation-ownership-coalescing-audit-project"])
    project.update(id=str(uuid.uuid5(uuid.NAMESPACE_URL, "aitrove:" + project_path)), path=project_path,
                   title=group["title"], summary="Compare four new structures with direct results and failure traces.",
                   sort_order=45090 + group_number * 20, created_at=stamp, updated_at=stamp, published_at=stamp)
    project["data"].update(reading_minutes=35,
                           related=[{"path": path, "title": by_path[path]["title"]} for path in group["paths"]])
    project["body"] = "<p>" + html.escape(group["intro"]) + "</p>"
    project["body"] += "<h2>Acceptance trace</h2><p>" + html.escape(group["trace"]) + "</p>"
    project["body"] += "<h2>Failure and cost review</h2><p>" + html.escape(group["failures"]) + "</p>"
    project["body"] += "<h3>Common Mistakes</h3><ul>" + "".join("<li>" + html.escape(item) + "</li>" for item in group["mistakes"]) + "</ul>"
    project["body"] += "<h2>Connected lessons</h2>" + links(group["paths"] + ["dsa/projects", "dsa/quizzes", subject_root])
    entries.append(project)
    by_path[project_path] = project

    quiz_questions = [item for path in group["paths"] for item in questions[path]]
    assert len(quiz_questions) == 12
    balanced = []
    for number, (prompt, correct, wrong_one, wrong_two, explanation) in enumerate(quiz_questions):
        assert len(explanation) >= 60, prompt
        answer = number % 3
        options = [wrong_one, wrong_two]
        options.insert(answer, correct)
        balanced.append({"prompt": prompt, "options": options, "answer": answer, "explanation": explanation})
    quiz = copy.deepcopy(by_path["quizzes/dsa-splay-and-resident-history-contracts"])
    quiz.update(id=str(uuid.uuid5(uuid.NAMESPACE_URL, "aitrove:" + quiz_path)), path=quiz_path,
                title=group["title"].replace("Project: audit ", "Check "),
                summary="Twelve explained decisions about four separate structure contracts.",
                sort_order=45100 + group_number * 20, created_at=stamp, updated_at=stamp, published_at=stamp)
    quiz["data"].update(duration_minutes=20,
                        related=[{"path": path, "title": by_path[path]["title"]} for path in group["paths"] + [project_path]],
                        questions=balanced)
    quiz["body"] = "<p>Choose the operation contract or failure response that matches each structure. Verify outputs against a direct reference model.</p><h2>Lessons</h2>" + links(group["paths"]) + "<h2>Design exercise</h2>" + links([project_path, subject_root])
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
        entry["body"] += '<p>Compare its input and update contract with ' + ", ".join(
            '<a href="/' + other + '">' + html.escape(by_path[other]["title"]) + "</a>" for other in peers)
        entry["body"] += ', then complete the <a href="/' + project_path + '">structure audit</a> and <a href="/' + quiz_path + '">decision quiz</a>.</p>'
        entry["updated_at"] = stamp

for old_path, target in [
    ("dsa/van-emde-boas-bounded-successor", "dsa/x-fast-trie-static-case-predecessor"),
    ("dsa/binary-radix-longest-prefix-routes", "dsa/x-fast-trie-static-case-predecessor"),
    ("dsa/resizable-array-growth-and-insert-cost", "dsa/persistent-radix-vector-path-copying"),
    ("dsa/persistent-bitmap-hamt-alert-map", "dsa/persistent-radix-vector-path-copying"),
    ("dsa/suffix-array-lcp-incident-search", "dsa/static-compressed-suffix-tree-pattern-locations"),
    ("dsa/suffix-automaton-online-substrings", "dsa/static-compressed-suffix-tree-pattern-locations"),
    ("dsa/interval-tree-max-endpoint-pruning", "dsa/disjoint-interval-union-maintenance-windows"),
    ("dsa/avl-interval-index-insertion", "dsa/disjoint-interval-union-maintenance-windows"),
    ("dsa/csr-sparse-graph-storage", "dsa/csr-delta-overlay-graph-updates"),
    ("dsa/immutable-index-snapshot-publication", "dsa/csr-delta-overlay-graph-updates"),
    ("dsa/bitset-adjacency-matrix-dense-graph", "dsa/bitset-transitive-reachability-snapshot"),
    ("dsa/graph-adjacency-list-and-bfs", "dsa/bitset-transitive-reachability-snapshot"),
    ("dsa/segmented-array-prefix-block-locate", "dsa/gap-label-order-maintenance"),
    ("dsa/implicit-treap-range-reversal", "dsa/gap-label-order-maintenance"),
    ("dsa/leftist-heap-null-path-meld", "dsa/skew-heap-self-adjusting-meld"),
    ("dsa/pairing-heap-two-pass-meld", "dsa/skew-heap-self-adjusting-meld"),
]:
    entry = by_path[old_path]
    entry["body"] += '<p><a href="/' + target + '">' + html.escape(by_path[target]["title"]) + "</a> adds a related structure with a different operation boundary.</p>"
    entry["updated_at"] = stamp

fixture.write_text(json.dumps(entries, ensure_ascii=False, indent=2) + "\n")
print(json.dumps({"lessons": len(lessons), "projects": len(groups), "quizzes": len(groups),
                  "new_routes": len(lessons) + 2 * len(groups)}))
