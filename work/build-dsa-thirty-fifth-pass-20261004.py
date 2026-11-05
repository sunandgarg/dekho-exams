"""Add eight separate structure lessons and connected draft assessments."""

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
    dict(path="dsa/fibonacci-heap-cascading-cuts", program="fibonacci_dispatch_heap.py",
         template="dsa/binomial-heap-degree-carry-meld", section="dsa/trees-and-heaps",
         title="Fibonacci heaps: cut on decrease and consolidate on removal",
         summary="Delay degree consolidation, then use marks and cascading cuts to repair heap order.",
         definition="A Fibonacci heap keeps a circular list of heap-ordered roots and a direct pointer to the smallest root. Insertion adds one singleton root. Removing the minimum promotes its children and consolidates roots of equal degree, linking the larger root below the smaller until each remaining root has a distinct degree. A decrease-key operation cuts a node whose new priority violates its parent's order. A non-root parent is marked after losing one child; if it loses another, it is cut too, and the repair can cascade. The task-ID map provides stable node handles. Ties compare task IDs after priorities so every trace has a reproducible minimum. This model handles insertion, decrease, and removal, but omits meld and arbitrary deletion.",
         case="A dispatch queue initially stores priorities 47, 83, 19, and 61. Removing the first minimum yields T-19 and forces consolidation. Decreasing T-83 to 17 then makes it the next minimum. The remaining tasks leave in priority order 47 then 61. A decrease may leave a node below its parent when the new key still respects heap order; cutting every decreased node would add needless roots. A task ID cannot be inserted twice, and increasing a key is rejected because this operation has only the downward-priority contract. After removal, its handle must disappear before another update can name it.",
         cost="Insertion and decrease-key are O(1) amortized under expected hash-map handle lookup; minimum removal is O(log N) amortized. One removal can examine O(N) roots, and one decrease can trigger multiple cascading cuts, so these are not per-call worst-case promises. The heap stores O(N) nodes and links; consolidation temporarily keeps a degree table and snapshots the root ring. Python object and dictionary costs can outweigh the theoretical gain over a binary heap at modest sizes. This implementation lacks constant-time meld because it does not expose a donor ownership transfer, and it makes no claim of lock-free or durable behavior.",
         mistakes=["Do not skip consolidation after promoting the removed root's children.", "Do not forget to clear a promoted child's parent and mark.", "Do not cut every node merely because its key decreased.", "Do not present amortized costs as a strict upper bound on one call."],
         related=["dsa/binomial-heap-degree-carry-meld", "dsa/indexed-binary-heap-decrease-key", "dsa/pairing-heap-two-pass-meld"]),
    dict(path="dsa/tournament-tree-kway-run-merge", program="tournament_run_merge.py",
         template="dsa/binary-heap-priority-scheduling", section="dsa/trees-and-heaps",
         title="Tournament trees: merge sorted runs through one winner path",
         summary="Keep a winner for every pair of run heads and replay only the changed leaf path.",
         definition="A tournament merge tree places one current head from each sorted run at a leaf. Each internal node stores the run ID of the smaller head in its two children. When the root winner is emitted, only that run advances; the leaf changes and winners are recomputed on its path to the root. Empty runs have no contender. The example uses the run ID to break equal-value ties, so equal keys from two runs have stable source order. The entire runs are copied into Python lists for clarity; an external merge would buffer heads from files instead. This is a winner tree, not a loser tree, because internal nodes retain winners.",
         case="Four runs contain [19,47,83], [29,47,61], an empty run, and [17,103]. The merged output starts with 17 from run three, then 19 from run zero; both 47 values retain run-zero-before-run-one tie order. After a run ends, its leaf becomes empty and cannot win again. The tree's padded leaves let the run count be any positive integer rather than only a power of two. If one input run is unsorted, updating just the winner path cannot repair global sorted order, so construction rejects it.",
         cost="With K runs and T total values, construction copies O(T) values and builds O(K) tree slots. Each emitted value updates O(log K) internal winners, giving O(T log K) merge time and O(K+T) memory in this in-memory version. A streaming version could retain O(K) heads plus source buffers instead of copying all T values. The tree stores contender IDs rather than moving values through every internal node. A binary heap offers the same asymptotic merge bound, while this tree gives a fixed replay path after each known source advances.",
         mistakes=["Do not call internal winner records loser-tree state.", "Do not forget to remove an exhausted run from contention.", "Do not claim sorted output if a source run violates its sorted-input contract.", "Do not ignore tie ordering when a downstream consumer needs stable source order."],
         related=["dsa/binary-heap-priority-scheduling", "dsa/lsm-sorted-runs-tombstone-compaction", "dsa/dary-heap-stable-priority-dispatch"]),
    dict(path="dsa/priority-search-tree-three-sided-events", program="priority_search_depot_events.py",
         template="dsa/static-two-dimensional-range-tree-counting", section="dsa/trees-and-heaps",
         title="Priority search trees: report events in a three-sided region",
         summary="Combine a minimum-y heap rule with horizontal subtree spans for static reporting.",
         definition="A priority search tree stores one point with the smallest y-coordinate in each component at its root. The remaining points split around their median x-coordinate, so recursive subtrees cover narrower horizontal spans. A query for x in [left,right] and y at most a limit prunes a subtree when its x-span misses the interval or its root minimum y exceeds the limit. Otherwise, it tests the root point and descends. The program sorts returned event records by ID after traversal. Equal y values break by event ID at construction, and duplicate IDs are rejected. This is a static reporting index for a three-sided rectangle, not a general arbitrary rectangle aggregator.",
         case="Five depot events include E-29 at (29,17) and E-61 at (61,23). The query x from 20 through 70 with y no greater than 30 reports those two events. A second query x from 18 through 50 and y no greater than 50 reports E-19 and E-29. Pruning solely because the root's x lies outside the query would be wrong: descendants may still occupy the requested horizontal span. In contrast, if the minimum y at a node is above the limit, every point below it is above the limit and the entire component is safe to skip.",
         cost="This direct builder finds a minimum and sorts remaining x values within each balanced component, costing at most O(N log-squared N) time and O(N) stored nodes. A query can visit O(N) nodes in an unfavorable region and sorts K reported records in O(K log K); its recursion uses O(log N) stack depth for the balanced construction. No output-sensitive worst-case bound is claimed for this particular Python walk. The fixed point set must be rebuilt after a location or score update. A k-d tree cuts coordinates differently, while a two-dimensional range tree spends more space to answer four-sided counts.",
         mistakes=["Do not prune a subtree from the stored point's x alone.", "Do not forget the inclusive y threshold at equality.", "Do not use the static x-span after moving an event.", "Do not claim a four-sided rectangle contract for this three-sided query."],
         related=["dsa/static-two-dimensional-range-tree-counting", "dsa/kd-tree-exact-nearest-depot", "dsa/point-region-quadtree-range-report"]),
    dict(path="dsa/reduced-ordered-decision-diagram-rules", program="reduced_decision_dispatch_rules.py",
         template="dsa/persistent-bitmap-hamt-alert-map", section="dsa/trees-and-heaps",
         title="Reduced ordered decision diagrams: share identical rule branches",
         summary="Build a canonical Boolean decision graph for one fixed variable order and predicate.",
         definition="A reduced ordered binary decision diagram represents a Boolean rule as a directed acyclic graph. Every internal node tests one variable, with low and high branches for false and true; both paths respect the same variable order. Two reduction rules shrink the graph: a node whose branches are equal is removed, and an identical (variable,low,high) triple reuses one existing node from a unique table. Terminal IDs zero and one mean false and true. This teaching constructor enumerates every assignment to a pure predicate before interning nodes. It supports evaluation and sharing, not a full symbolic apply package or variable reordering engine.",
         case="A dispatch rule permits an override or the conjunction of paid and approved. The three-variable diagram contains three internal nodes in the chosen order. A paid and approved request passes without override; paid without approval fails; override alone passes. Supplying an incomplete flag map is rejected, rather than silently interpreting omitted fields as false. The unique-table key includes the variable and both children; using only the children would merge tests of different variables and change the function. Choosing a different variable order can change graph size even when the rule's truth table stays the same.",
         cost="Enumerating all assignments costs O(2^V) predicate evaluations for V variables in this direct constructor, and the resulting graph can have exponentially many distinct nodes. Evaluation follows at most V tests and uses O(1) extra state. The unique table uses expected hash lookup and O(M) space for M retained internal nodes, plus recursion and a mutable assignment map while building. Equivalent rules can share a canonical graph only under the same variable order and reduction conventions. A plain if-statement is simpler for one small rule; this structure helps when many related Boolean functions reuse subgraphs or require equivalence checks.",
         mistakes=["Do not intern two nodes with different variable names as the same decision.", "Do not omit the rule that discards equal low and high branches.", "Do not treat missing input flags as false without an explicit policy.", "Do not claim a small graph for every variable order and predicate."],
         related=["dsa/persistent-bitmap-hamt-alert-map", "dsa/binary-radix-longest-prefix-routes", "dsa/bitset-transitive-reachability-snapshot"]),
    dict(path="dsa/lz78-phrase-trie-incident-compression", program="lz78_incident_phrase_dictionary.py",
         template="dsa/trie-prefix-index-and-terminal-flag", section="dsa/trees-and-heaps",
         title="LZ78 phrase tries: emit dictionary index and next symbol",
         summary="Grow a phrase dictionary from repeated text and reconstruct it from token pairs.",
         definition="An LZ78 encoder starts with an empty phrase at index zero. At each input position it follows the longest phrase already present in a trie, then emits that phrase's index plus the next unseen symbol and inserts the extended phrase. If the input ends exactly on an existing phrase, this format emits a final token with an empty symbol. The decoder recreates the same phrase table in token order and concatenates decoded phrases. This is a dictionary coding model over Python characters; it does not pack integers into bytes, carry a wire header, or reset a bounded dictionary. The encoder and decoder must agree on the empty-final-token rule.",
         case="The incident string cabacabacaba produces seven phrase tokens, and decoding those tokens returns the original twelve-character string. The dictionary grows only when a token includes a new symbol; the final empty-symbol token reuses an earlier phrase without adding another one. A decoder must reject a phrase index that has not yet been defined, or corrupted input could reference data from the future. Empty text produces no tokens. The output size in bytes depends on how phrase indexes and symbols are serialized, so counting pairs alone is not a compression-ratio claim.",
         cost="Encoding traverses each input character once along trie edges with expected dictionary lookup, giving O(N) expected work and O(N) nodes or tokens for input length N. The simple decoder reconstructs phrases by Python string concatenation, which can copy long prefixes repeatedly and cost O(N squared) character work in a bad case. Its token list and phrase table also occupy O(N) references plus phrase strings. A production codec would define framing, symbol encoding, dictionary limits, and corruption handling. A prefix trie indexes search terms; this phrase trie instead gives each newly seen text phrase a numeric code.",
         mistakes=["Do not add a dictionary phrase for an empty final symbol.", "Do not decode a forward reference to a phrase that has not been created.", "Do not call token count a byte-level compression ratio.", "Do not mix character offsets with encoded byte positions."],
         related=["dsa/trie-prefix-index-and-terminal-flag", "dsa/compressed-trie-edge-splitting", "dsa/front-coded-term-lexicon-blocks"]),
    dict(path="dsa/segment-tree-interval-stabbing-index", program="segment_stabbing_maintenance.py",
         template="dsa/interval-tree-max-endpoint-pruning", section="dsa/range-query-structures",
         title="Segment-tree stabbing indexes: list intervals active at one point",
         summary="Decompose each interval into canonical buckets and inspect one point path.",
         definition="An interval stabbing index answers which stored intervals contain a query coordinate. Over a fixed integer universe [0,U), this segment tree places each half-open interval in a small set of canonical tree nodes whose ranges exactly cover it. A point query follows one root-to-leaf path and collects interval IDs in buckets along that path. Each stored interval appears once on that path if it contains the queried point, and nowhere on that path otherwise. Removal uses the original interval endpoints to remove its ID from the same canonical buckets. The example stores one interval per task ID, supports add and remove, and rejects coordinates outside its configured universe.",
         case="M-19 covers [19,61) and M-47 covers [47,83). At time 50, both IDs are active; at 83 neither is active because right endpoints are excluded. Removing M-19 leaves only M-47 active at 50. The ID table prevents accidentally adding a second range under one identifier without first removing the old one. Querying an integer outside [0,128) is an error, not an empty result, because the tree has no leaf there. This structure keeps individual interval IDs, unlike a disjoint interval union that retains only the covered set.",
         cost="An add or remove touches O(log U) canonical nodes in a binary tree over U integer positions, with expected set operations for each bucket. A point query traverses O(log U) nodes, gathers K matching IDs, then sorts them in O(K log K); it uses O(K) output memory. The allocated Python bucket array has O(U) entries before any interval arrives, and M stored intervals contribute O(M log U) worst-case bucket references. A large sparse coordinate universe would warrant compression or a sparse node tree. This index reports active IDs, while a range-add segment tree usually aggregates numeric values instead.",
         mistakes=["Do not include an interval's right endpoint in a half-open point query.", "Do not lose original endpoints needed to remove canonical bucket entries.", "Do not use the index outside its configured universe.", "Do not confuse covered length with the list of interval identities."],
         related=["dsa/interval-tree-max-endpoint-pruning", "dsa/disjoint-interval-union-maintenance-windows", "dsa/sparse-coordinate-segment-tree"]),
    dict(path="dsa/huffman-prefix-code-tree", program="huffman_incident_code_tree.py",
         template="dsa/binary-heap-priority-scheduling", section="dsa/trees-and-heaps",
         title="Huffman trees: assign prefix codes from symbol frequencies",
         summary="Repeatedly combine low-frequency subtrees and decode through the resulting binary tree.",
         definition="A Huffman code tree starts with one leaf per training symbol and repeatedly joins the two lowest-frequency roots. The merged node's weight is their sum. A left edge contributes zero and a right edge contributes one, so every leaf receives a codeword and no leaf code is a prefix of another. This model uses a binary heap to build a fixed codebook, then encodes only symbols present in that training alphabet. The decoder walks the retained tree and emits a symbol whenever it reaches a leaf. A one-symbol alphabet gets code zero so its encoded length remains explicit. The codebook is part of the decoding contract, not an optional afterthought.",
         case="A codebook trained on dispatch dispatch urgent has fourteen distinct symbols. Encoding dispatch urgent yields 57 bits in this run, and the decoder restores the exact phrase. Equal-frequency symbols are resolved by a serial tie value, making the output reproducible without implying a unique Huffman bit assignment across all implementations. An unknown symbol cannot be encoded through this codebook. A trailing bit sequence that ends inside an internal node is incomplete and rejected; for a one-symbol alphabet, only zero is a valid code bit.",
         cost="For A distinct symbols, frequency counting takes O(N) time on N training characters and heap construction takes O(A log A) in this direct implementation. Encoding and decoding visit O(B) code bits for encoded length B, while codebook and tree storage are O(A) nodes plus the stored code strings. The output in the example is a Python string of zero and one characters, not packed bits, and it excludes any header needed to transmit the tree. A canonical codebook and bit packing would change serialization details. A frequency change after publication requires a newly agreed codebook.",
         mistakes=["Do not assume the bitstream is decodable without the matching codebook.", "Do not give the single-symbol alphabet an empty codeword.", "Do not accept a stream ending in the middle of a codeword.", "Do not compare Python text bits with packed file bytes as if they were equal storage."],
         related=["dsa/binary-heap-priority-scheduling", "dsa/front-coded-term-lexicon-blocks", "dsa/tournament-tree-kway-run-merge"]),
    dict(path="dsa/scc-condensation-reachability-index", program="scc_condensation_route_index.py",
         template="dsa/bitset-transitive-reachability-snapshot", section="dsa/graphs-and-disjoint-sets",
         title="Condensation DAGs: compress directed cycles before path queries",
         summary="Group strongly connected vertices, then index reachability between component nodes.",
         definition="A strongly connected component groups directed vertices that can reach one another. This index finds components through a forward finish-order traversal and a reverse-graph traversal, then replaces each component with one node in a condensation graph. Edges between distinct components form a directed acyclic graph; duplicate edges collapse into one set entry. The example precomputes a reachable-component set for every component by traversing that graph. A vertex-to-vertex path query then tests whether the target's component appears in the source component's set. Vertices within the same component always reach one another, including by the zero-edge path when source equals target.",
         case="Seven directed depots include a three-vertex cycle through zero, one, and two and a two-vertex cycle through three and four. A route from the first component can reach depot five, while depot five cannot return to depot one. The condensation has four component nodes rather than seven original vertices. Component numeric IDs depend on traversal order and are implementation details; callers should compare membership or reachability, not publish those IDs as stable depot identifiers. A changed edge can merge components or split reachability, so the entire static index needs rebuilding.",
         cost="Component discovery and DAG construction take O(V+E) time and O(V+E) space for V vertices and E edges. This model then traverses the component DAG once per component, taking O(C(C+D)) time and up to O(C squared) stored reachability entries for C components and D distinct DAG edges. A query uses expected O(1) set membership after indexing. For few queries, a direct graph search may avoid the quadratic precomputation. The iterative finish traversal avoids recursion depth, but the implementation keeps Python lists and sets rather than packed bit rows.",
         mistakes=["Do not treat component IDs as stable business IDs across rebuilds.", "Do not assume weakly connected vertices can reach each other both ways.", "Do not keep old reachability sets after adding or removing a road.", "Do not retain self-loops as edges between distinct condensation nodes."],
         related=["dsa/bitset-transitive-reachability-snapshot", "dsa/graph-adjacency-list-and-bfs", "dsa/csr-delta-overlay-graph-updates"]),
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
                 sort_order=46000 + order * 10, created_at=stamp, updated_at=stamp, published_at=stamp)
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
    "dsa/fibonacci-heap-cascading-cuts": [
        ("When does this heap consolidate equal-degree roots?", "After removing the current minimum", "After every read-only minimum check", "Before every decrease request", "Minimum removal promotes children and then links roots of equal degree so the remaining root list has distinct degrees."),
        ("Why can a decrease cause several cuts?", "Marked ancestors may lose another child in a cascade", "Every sibling must be deleted", "The task ID becomes duplicated", "A non-root node that already lost one child is marked; losing another causes it to be cut and can propagate upward."),
        ("Are its decrease and removal bounds strict per-call limits?", "No; they are amortized over sequences", "Yes; no operation can scan roots", "Yes; every cut visits exactly one node", "A removal can consolidate many roots and a decrease can cascade, so the stated bounds apply across operation sequences."),
    ],
    "dsa/tournament-tree-kway-run-merge": [
        ("Which tree path changes after one merged value is emitted?", "The leaf of its source run and ancestors to the root", "Every leaf in every run", "Only the root with no child updates", "Only one input run advances, so its contender leaf and the winners above it require replay."),
        ("What is stored in this tournament tree's internal nodes?", "The winning run ID from the two children", "The losing run ID only", "Every prior output value", "The model compares current run heads and retains winners, which makes it a winner tree rather than a loser tree."),
        ("What must be true of each source run?", "Its values are sorted before merging", "Its values are all distinct", "Its length is a power of two", "A tree of current heads cannot repair an unsorted input run; construction checks the sorted-run contract."),
    ],
    "dsa/priority-search-tree-three-sided-events": [
        ("When can a whole subtree be pruned by y?", "Its stored minimum y exceeds the query limit", "Its root x lies left of the query", "Its event ID sorts last", "Every descendant has y at least the root minimum, so a root above the limit excludes that complete subtree."),
        ("What horizontal information permits safe pruning?", "The subtree's minimum and maximum x span", "Only its root point's x", "Only its lowest y value", "A root point can lie outside the requested x interval while descendants lie inside; the full subtree span is needed."),
        ("What shape of region does this lesson report?", "An inclusive x interval with an upper y limit", "Every four-sided rectangle", "An arbitrary polygon", "The query has two x boundaries and one y ceiling; a lower y boundary is not part of this interface."),
    ],
    "dsa/reduced-ordered-decision-diagram-rules": [
        ("When can a decision node be removed?", "Its low and high branches are identical", "Its variable name is long", "Its high branch is true", "Testing a variable has no effect when both outcomes lead to the same function, so reduction bypasses that node."),
        ("What is the unique-table identity for one internal node?", "Variable plus low and high child IDs", "Low and high IDs without the variable", "The node's numeric ID alone", "Two tests of different variables cannot be merged merely because their children match; the tested variable is part of the function."),
        ("Why can changing variable order alter graph size?", "Shared subfunctions depend on the fixed path order", "Boolean truth values change automatically", "Terminals lose their values", "The represented rule remains the same, but a different test sequence exposes different repeated branches to the unique table."),
    ],
    "dsa/lz78-phrase-trie-incident-compression": [
        ("What does an ordinary emitted LZ78 token contain?", "An existing phrase ID and its next new symbol", "Only a final byte count", "Two arbitrary prior phrase IDs", "The encoder extends the longest known phrase by one symbol and assigns the extended phrase its next dictionary ID."),
        ("What happens when input ends on an existing phrase?", "A final token may carry that phrase ID and an empty symbol", "A random symbol must be invented", "The final phrase is silently discarded", "This model explicitly signals a terminal old phrase without inserting another dictionary entry."),
        ("Why is token count not a measured byte compression ratio?", "Indexes, symbols, and dictionary framing still need serialization", "Every pair always occupies one bit", "The decoder stores no phrases", "A token pair is a logical record; its physical byte cost depends on index coding and symbol representation."),
    ],
    "dsa/segment-tree-interval-stabbing-index": [
        ("Where is one interval ID stored?", "In canonical nodes whose ranges cover its half-open interval", "Only at every individual leaf", "Only in a disjoint union span", "The range is decomposed into a small number of complete segment-tree nodes for efficient add and removal."),
        ("Which nodes does an active-at-point query inspect?", "One root-to-leaf path", "Every stored interval bucket", "Only a midpoint that ignores ancestors", "Every canonical node containing the point lies on its tree path, so collecting buckets on that path finds all matching IDs."),
        ("Does [47,83) include time 83?", "No; the right endpoint is excluded", "Yes; both endpoints are included", "Only if the interval was removed", "The index defines half-open coverage, so a point equal to the right endpoint lies outside the stored interval."),
    ],
    "dsa/huffman-prefix-code-tree": [
        ("Why can the decoder identify codeword boundaries?", "No leaf code is a prefix of another leaf code", "Every symbol has the same bit length", "The decoder knows the original phrase", "Once a tree walk reaches a leaf, that symbol is complete; no other symbol continues below a leaf."),
        ("What code does this model assign to a one-symbol alphabet?", "A single zero bit", "The empty string for every occurrence", "A random two-bit word", "Using zero preserves a visible bit count, so the decoder can distinguish how many copies were sent."),
        ("What accompanies the encoded bits for independent decoding?", "The matching codebook or tree description", "Only a total frequency count", "No metadata at all", "Bits alone do not identify which symbols occupy the leaves; the decoder must share the exact code assignment."),
    ],
    "dsa/scc-condensation-reachability-index": [
        ("What does one condensation node represent?", "A strongly connected group of original vertices", "One original edge", "Every weakly connected vertex", "Vertices inside the same component can reach one another, so they can be grouped for reachability between components."),
        ("Why are cross-component edges acyclic?", "A cycle would make its participating components mutually reachable", "Every vertex has one outgoing edge", "Component IDs are sorted", "If separate components formed a directed cycle, all their vertices would belong to one larger strongly connected component."),
        ("When must this static reachability index be rebuilt?", "After graph edges change", "After every read-only query", "Only when component labels are printed", "Adding or deleting an edge can alter components and their reachability sets, invalidating the frozen index."),
    ],
}

groups = [
    dict(paths=[lesson["path"] for lesson in lessons[:4]],
         project="dsa/heap-merge-spatial-rule-audit-project",
         quiz="quizzes/dsa-heap-merge-spatial-rule-contracts",
         title="Project: audit heap repairs, run winners, spatial pruning, and rules",
         intro="A dispatch review needs four distinct indexes. A Fibonacci heap handles repeated task priority decreases. A tournament tree merges four ordered event streams. A priority search tree reports events under a y threshold inside an x corridor. A reduced decision diagram evaluates a Boolean release policy. Keep their input versions separate: a changed stream head should replay one tournament path, while a moved event needs a spatial rebuild; a new rule needs a diagram built from its own variable order.",
         trace="Insert tasks at priorities 47, 83, 19, and 61. Remove T-19, then decrease T-83 to 17 and remove it next. Merge sorted runs so the first outputs are 17 from run three and 19 from run zero. A three-sided event query over x from 20 through 70 and y at most 30 returns E-29 and E-61. A policy override permits dispatch, as does paid together with approved, but paid alone does not. Verify all four results independently.",
         failures="Fuzz heap insert, decrease, and removal against a map of live task priorities; inspect handle deletion and parent marks after cuts. Compare tournament output with a flattened sort that preserves run-ID ties. Compare spatial reports with a direct point filter, including query boundaries and equal y values. Enumerate every rule assignment and compare diagram results with the predicate. Exercise duplicate task IDs, unsorted runs, duplicate event IDs, and incomplete flag maps. Do not infer that a small measured dataset proves worst-case query bounds.",
         mistakes=["Do not confuse amortized Fibonacci costs with a per-call promise.", "Do not retain an exhausted run as winner.", "Do not prune a spatial child from its root x alone.", "Do not intern rule nodes without their tested variable."]),
    dict(paths=[lesson["path"] for lesson in lessons[4:]],
         project="dsa/phrase-stabbing-code-condensation-audit-project",
         quiz="quizzes/dsa-phrase-stabbing-code-condensation-contracts",
         title="Project: audit phrase codes, active intervals, prefix bits, and routes",
         intro="Build an incident processing release with four independent structures. An LZ78 phrase trie emits and decodes text tokens. A stabbing segment tree reports which maintenance IDs are active at a time. A Huffman tree encodes a payload under a fixed training codebook. An SCC condensation graph answers directed depot reachability from a static edge snapshot. Phrase indexes and Huffman bits need matching decoding metadata; interval membership needs its fixed universe; and reachability must be rebuilt after a road change.",
         trace="Encode cabacabacaba into seven phrase tokens and decode it exactly. Store M-19 over [19,61) and M-47 over [47,83); at time 50 both are active, at 83 neither is. A Huffman codebook trained on dispatch dispatch urgent encodes dispatch urgent to 57 bits in this deterministic trace and restores the phrase. A seven-depot directed graph condenses to four components; depot one reaches five, but depot five cannot return to one. Record the snapshot or codebook that makes each answer valid.",
         failures="Generate short strings over small alphabets and verify LZ78 encode/decode round trips, empty input, and invalid forward phrase references. Fuzz interval additions and removals against a direct task-to-range map at every coordinate. For randomly generated symbol frequencies, verify Huffman round trips and that no codeword prefixes another. Compare every condensed-graph path answer against breadth-first search in random directed graphs with cycles. Reject an incomplete Huffman final code, out-of-universe interval, and old reachability rows after an edge update. Do not count Python character strings as packed compressed bytes.",
         mistakes=["Do not invent a symbol for an LZ78 final known phrase.", "Do not include half-open right endpoints in stabbing results.", "Do not decode Huffman bits with a different tree.", "Do not keep condensation reachability after graph edits."]),
]

for group_number, group in enumerate(groups):
    project_path, quiz_path = group["project"], group["quiz"]
    assert project_path not in by_path and quiz_path not in by_path
    project = copy.deepcopy(by_path["dsa/allocation-ownership-coalescing-audit-project"])
    project.update(id=str(uuid.uuid5(uuid.NAMESPACE_URL, "aitrove:" + project_path)), path=project_path,
                   title=group["title"], summary="Compare four new structures against direct results and failure traces.",
                   sort_order=46090 + group_number * 20, created_at=stamp, updated_at=stamp, published_at=stamp)
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
                summary="Twelve explained decisions about four new structure boundaries.",
                sort_order=46100 + group_number * 20, created_at=stamp, updated_at=stamp)
    quiz["data"].update(duration_minutes=20,
                        related=[{"path": path, "title": by_path[path]["title"]} for path in group["paths"] + [project_path]],
                        questions=balanced)
    quiz["body"] = "<p>Choose the operation contract or failure response implied by each structure. Verify outputs against a direct reference model.</p><h2>Lessons</h2>" + links(group["paths"]) + "<h2>Design exercise</h2>" + links([project_path, subject_root])
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
        entry["body"] += '<p>Compare its query and update boundary with ' + ", ".join(
            '<a href="/' + other + '">' + html.escape(by_path[other]["title"]) + "</a>" for other in peers)
        entry["body"] += ', then complete the <a href="/' + project_path + '">structure audit</a> and <a href="/' + quiz_path + '">decision quiz</a>.</p>'
        entry["updated_at"] = stamp

for old_path, target in [
    ("dsa/binomial-heap-degree-carry-meld", "dsa/fibonacci-heap-cascading-cuts"),
    ("dsa/indexed-binary-heap-decrease-key", "dsa/fibonacci-heap-cascading-cuts"),
    ("dsa/binary-heap-priority-scheduling", "dsa/tournament-tree-kway-run-merge"),
    ("dsa/lsm-sorted-runs-tombstone-compaction", "dsa/tournament-tree-kway-run-merge"),
    ("dsa/static-two-dimensional-range-tree-counting", "dsa/priority-search-tree-three-sided-events"),
    ("dsa/kd-tree-exact-nearest-depot", "dsa/priority-search-tree-three-sided-events"),
    ("dsa/persistent-bitmap-hamt-alert-map", "dsa/reduced-ordered-decision-diagram-rules"),
    ("dsa/binary-radix-longest-prefix-routes", "dsa/reduced-ordered-decision-diagram-rules"),
    ("dsa/trie-prefix-index-and-terminal-flag", "dsa/lz78-phrase-trie-incident-compression"),
    ("dsa/front-coded-term-lexicon-blocks", "dsa/lz78-phrase-trie-incident-compression"),
    ("dsa/interval-tree-max-endpoint-pruning", "dsa/segment-tree-interval-stabbing-index"),
    ("dsa/disjoint-interval-union-maintenance-windows", "dsa/segment-tree-interval-stabbing-index"),
    ("dsa/dary-heap-stable-priority-dispatch", "dsa/huffman-prefix-code-tree"),
    ("dsa/tournament-tree-kway-run-merge", "dsa/huffman-prefix-code-tree"),
    ("dsa/bitset-transitive-reachability-snapshot", "dsa/scc-condensation-reachability-index"),
    ("dsa/csr-delta-overlay-graph-updates", "dsa/scc-condensation-reachability-index"),
]:
    entry = by_path[old_path]
    entry["body"] += '<p><a href="/' + target + '">' + html.escape(by_path[target]["title"]) + "</a> adds a related structure with a different operation boundary.</p>"
    entry["updated_at"] = stamp

fixture.write_text(json.dumps(entries, ensure_ascii=False, indent=2) + "\n")
print(json.dumps({"lessons": len(lessons), "projects": len(groups), "quizzes": len(groups),
                  "new_routes": len(lessons) + 2 * len(groups)}))
