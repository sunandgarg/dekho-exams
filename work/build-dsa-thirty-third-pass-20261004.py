"""Add eight more independent Data Structures lessons and connected assessments."""

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
    dict(path="dsa/bk-tree-edit-distance-label-search", program="bk_tree_incident_labels.py",
         template="dsa/ternary-search-tree-incident-completion", section="dsa/trees-and-heaps",
         title="BK-trees: search incident labels within edit distance",
         summary="Use metric edge distances to prune approximate label matches without scanning every term by default.",
         definition="A BK-tree stores one label per node. The edge from a parent to a child is the edit distance between their labels; one parent has at most one child for each edge distance. Insertion follows the appropriate edge until it finds an empty position or a duplicate. A radius query computes the distance d from its target to the current node and explores only child edges e in [d-r,d+r], where r is the requested tolerance. That band follows from the triangle inequality: a subtree attached through a more distant edge cannot contain a qualifying label. The program uses Levenshtein distance over Python code points and sorts matches by distance then label. Its labels are immutable after insertion.",
         case="A review queue indexes invoice, invoces, invoices, incident, invoker, and voice. A radius-one lookup for invoice returns invoice itself and invoices. A second insertion of invoice returns false rather than creating a duplicate branch. The query must still examine a child at edge distance d+r, because a valid result may lie exactly on the tolerance boundary. Likewise, a node outside the radius does not justify dropping its entire subtree; its child edges may lead back toward the query. Case folding and Unicode normalization are caller decisions: this exact model treats differently encoded labels as different strings.",
         cost="Computing edit distance between strings of lengths A and B takes O(AB) time and O(B) row space in this implementation. A lookup may visit every stored label, giving O(NAB) worst-case time, and an unbalanced insertion path can do the same. The tree stores O(N) nodes and edges. Small radii and a useful label distribution can prune many branches, but no universal sublinear query guarantee follows from the shape alone. The structure answers approximate whole-label matching; a trie serves exact prefixes, while a trigram index can produce substring candidates that need verification.",
         mistakes=["Do not prune the entire subtree merely because its parent label is outside the radius.", "Do not omit the equality cases at either edge-band boundary.", "Do not call code-point edit distance locale-aware spelling correction.", "Do not assume the tree stays balanced after adversarial insertion order."],
         related=["dsa/ternary-search-tree-incident-completion", "dsa/trigram-index-verified-substring-candidates", "dsa/compressed-trie-edge-splitting"]),
    dict(path="dsa/vantage-point-metric-nearest-depot", program="vantage_point_depot_index.py",
         template="dsa/kd-tree-exact-nearest-depot", section="dsa/trees-and-heaps",
         title="Vantage-point trees: nearest depots by a metric radius",
         summary="Partition static points by distance from a pivot and prune with the triangle inequality.",
         definition="A vantage-point tree chooses a pivot object, measures every remaining object's distance to it, and divides the objects around a median radius. This static index uses Manhattan distance between depot coordinates, so the distance function satisfies the triangle inequality. Its near partition has distances no greater than the stored radius; its far partition has distances no less. A nearest-neighbor query evaluates the pivot, searches the side containing the query first, then visits the other side only if the best distance still reaches the radius boundary. Equal-distance candidates use depot ID as a deterministic tie. Splitting by median position keeps the shape balanced even when several points share a radius.",
         case="Five depot coordinates include central at (47,47) and west at (83,29). For destination (50,45), central is five Manhattan units away; for (80,30), west is four. The pivot chosen during construction is not guaranteed to be the nearest. If a query lies just inside a pivot radius, a qualifying depot may live in the far child; pruning it without comparing the current best distance to that radius would return the wrong result. This representation is frozen. Moving a depot changes the distance partitions and requires a rebuild, whereas a moving-point grid elsewhere in the curriculum supports live coordinate updates.",
         cost="Sorting distances in each balanced component gives O(N log-squared N) construction time in this direct implementation and O(N) stored nodes. A nearest query can visit O(N) pivots in a difficult metric distribution or high dimension; it uses O(H) recursion space for tree height H. No unconditional logarithmic nearest-neighbor bound is claimed. The metric itself can be expensive: with long vectors or string edit distance, computing distance may dominate the tree walk. A k-d tree uses coordinate axis cuts, while this pivot split depends only on the metric and can be reused for non-Cartesian objects with an appropriate distance function.",
         mistakes=["Do not prune the opposite child when the best-distance ball reaches the radius boundary.", "Do not use a distance function that violates the triangle inequality and expect exact pruning.", "Do not promise logarithmic nearest queries for every data distribution.", "Do not update a depot coordinate without rebuilding the static partitions."],
         related=["dsa/kd-tree-exact-nearest-depot", "dsa/spatial-hash-grid-moving-points", "dsa/static-bvh-axis-aligned-box-overlap"]),
    dict(path="dsa/centroid-decomposition-nearest-marked-depot", program="centroid_marked_depot_distance.py",
         template="dsa/heavy-light-tree-path-sums", section="dsa/graphs-and-disjoint-sets",
         title="Centroid decomposition: nearest marked depot on a fixed tree",
         summary="Precompute centroid ancestor distances so mark and nearest-distance queries touch few records.",
         definition="Centroid decomposition repeatedly removes a tree vertex whose removal leaves no component larger than half of the current component. Each original vertex records its distance to the centroids of the nested components that contain it. Marking a vertex improves the best marked distance stored at every centroid on that vertex's path. To query another vertex, combine its distance to each centroid with that centroid's best marked distance and take the minimum. Any route between a query vertex and a marked vertex crosses a centroid that separates their decomposition branches, so one of these combinations reaches the true tree distance. The example handles an unweighted static tree and marks only; it does not remove marks.",
         case="The seven-depot road tree has branches through depots one and three. Before any mark, nearest marked distance from depot two is None. Marking depot four makes that distance three edges. Marking depot six then makes depot five one edge from a marked depot. A duplicate mark is a no-op. The road graph must contain exactly N-1 edges and be connected; a cycle would make the component traversal and distance records invalid. If dispatch later removes a road or adds a new depot, the centroid hierarchy is no longer the hierarchy of the current graph and must be rebuilt.",
         cost="For N vertices, scanning and choosing a centroid at each level costs O(N log N) total in this implementation; distance-path storage is O(N log N). Once paths are built, a mark and a nearest-distance query inspect O(log N) centroid records. One mark only decreases best-distance values; supporting unmark would require per-centroid multisets or another reversible summary. Python lists and dictionaries increase actual memory. This data structure helps repeated marked-node distance queries over fixed topology, while heavy-light paths answer different path-aggregate questions and link-cut forests permit topology changes at higher implementation cost.",
         mistakes=["Do not use this mark-only summary for unmark without repairing every affected centroid record.", "Do not apply it to a graph with cycles or changing tree edges.", "Do not forget to include the marked vertex's entire centroid path.", "Do not confuse nearest marked distance with the identity of a nearest depot."],
         related=["dsa/heavy-light-tree-path-sums", "dsa/binary-lifting-lowest-common-ancestor", "dsa/link-cut-forest-path-sums"]),
    dict(path="dsa/two-level-perfect-hashing-static-case-ids", program="two_level_perfect_case_hash.py",
         template="dsa/linear-hashing-incremental-bucket-splits", section="dsa/hash-tables",
         title="Two-level perfect hashing: exact static case membership",
         summary="Choose bucket hashes and square-sized secondary tables with no stored-key collisions.",
         definition="A two-level perfect hash index is built for one fixed set of keys. The first hash sends keys to N buckets. Construction retries that hash until the sum of squared bucket sizes is bounded by a constant multiple of N. Each bucket of size S then receives S-squared secondary slots and an independently chosen hash with no collisions among its stored keys. A membership query performs two hash computations and compares the exact key in the resulting slot. The comparison matters: an absent key can still land in a occupied slot and must return false. This model accepts unique nonnegative integer IDs smaller than its fixed prime field and uses a deterministic random stream solely to make the demonstration reproducible.",
         case="Seven case IDs produce thirteen allocated secondary slots in the shown build. Membership for 61 is true; adjacent missing ID 62 is false. The first-level bucket selected for 62 may still contain another case, and its second-level slot may not be empty, so checking only slot occupancy would turn a collision with an absent key into a false positive. The construction has finite retry limits and raises a failure if it cannot find suitable hashes in those budgets. Adding case 149 after publication invalidates the collision-free choices; this immutable index must be rebuilt from the new complete set.",
         cost="Lookup takes O(1) worst-case hash and slot operations under the fixed-width integer model, with O(1) query memory. The accepted first-level squared-size bound limits allocated secondary slots to O(N) for the built set. The classical two-level scheme has expected linear build work with suitable universal hash choices; this bounded teaching implementation makes no build-time guarantee and can fail after its retry budget. Python lists and integer objects occupy more than the conceptual slots. A mutable hash map or linear hashing table is a better fit when IDs change frequently; perfect hashing is attractive for read-heavy snapshots.",
         mistakes=["Do not skip exact-key comparison for an occupied secondary slot.", "Do not insert into a published static table without rebuilding its hashes.", "Do not claim construction always succeeds within a fixed retry budget.", "Do not send IDs outside the configured integer universe through the hash arithmetic."],
         related=["dsa/linear-hashing-incremental-bucket-splits", "dsa/extendible-hash-directory-bucket-splits", "dsa/static-xor-filter-membership"]),
    dict(path="dsa/fm-index-backward-substring-search", program="fm_index_incident_search.py",
         template="dsa/suffix-array-lcp-incident-search", section="dsa/trees-and-heaps",
         title="FM-index backward search: narrow a suffix interval by character",
         summary="Use a last-column transform, first-column offsets, and character ranks for exact substring counts.",
         definition="An FM-index uses a sorted suffix order and its last-column transform to search a pattern backwards. For each character, a first-column offset C gives the start of that character's block in sorted order, while a rank table counts its occurrences before any last-column position. The current suffix interval [left,right) becomes [C[c]+rank(c,left), C[c]+rank(c,right)) when character c is prepended. After all pattern characters are processed, interval width is the exact occurrence count. The example retains the full suffix array to locate positions and stores complete prefix-rank arrays for each character. It is an index mechanics model, not a compressed production FM-index. A single sentinel terminates the text and is forbidden in the input and pattern.",
         case="The incident string cabacaba contains aba at offsets one and five. Backward search narrows the suffix interval to two rows, then the retained suffix positions report [1,5]. A pattern with a character absent from the alphabet has an empty interval. An empty pattern is rejected rather than assigned a special occurrence convention. The exact count includes overlapping matches when they exist. If the sentinel appeared inside the text, suffix order would no longer describe one uniquely terminated string, so the constructor fails before publishing the index. Text edits change the last column and rank tables and require reconstruction.",
         cost="Backward counting takes O(M) time for a pattern of length M because every rank lookup is an array access. Locating K matches takes O(K log K) here to sort their original positions. The deliberately simple suffix-string sorting construction has an O(N-squared log N) upper-bound time and large temporary cost; full rank arrays use O(N times alphabet size) memory, plus O(N) suffix positions. Production compressed indexes replace these arrays with compact rank structures and sampled positions, changing locate costs. This lesson isolates the exact backward interval rule rather than claiming compression or fast construction in Python.",
         mistakes=["Do not allow the sentinel inside text or pattern.", "Do not mix inclusive and half-open suffix interval boundaries.", "Do not call full rank arrays a compressed index.", "Do not assume counting positions and locating positions have the same cost."],
         related=["dsa/suffix-array-lcp-incident-search", "dsa/bitvector-rank-select-superblocks", "dsa/wavelet-matrix-static-rank-quantile"]),
    dict(path="dsa/block-max-postings-exact-topk-pruning", program="block_max_incident_postings.py",
         template="dsa/inverted-index-sorted-postings-intersection", section="dsa/hash-tables",
         title="Block-max postings: skip safe document-score regions",
         summary="Store term-score upper bounds by document-ID block for exact top-k review.",
         definition="A block-max posting index keeps an upper bound for each query term within each document-ID block. This example's document score is the sum of nonnegative weights for distinct query terms. Summing the term maxima yields an upper bound on every document in that block, even though different maxima may belong to different documents. Once K candidates are known, a block can be skipped when its upper bound is strictly below the current Kth score. The strict comparison preserves deterministic ties: an equal-score document with a smaller ID might replace the current last candidate. The example scans blocks in ID order and keeps a small sorted leader list. It illustrates exact block pruning, not the full iterator-pivot procedure of a production top-k engine.",
         case="Five incident documents have breach and urgent weights. Asking for the best two returns document 21 with score ten and document 19 with score eight; three later low-bound blocks are skipped. A score bound is safe only if every term contribution is nonnegative and the stored maximum is at least every real contribution in its block. If a term weight changed without refreshing its block maximum, the index might skip a new winner. A document with no matching query term contributes zero and is omitted. Duplicate query terms are treated as one term by the set conversion; a ranking product that weights repeated query words must state a different scoring rule.",
         cost="Building term maxima visits each stored term weight once and uses O(P+B) space for P weights and B block records. A query touches every block summary for each distinct term, then scores documents only in blocks that survive the bound. In the worst case it scores all documents, so this Python implementation has no guaranteed sublinear query bound. Its leader-list maintenance sorts at most K+1 items per scored document, adding O(K log K) work there. A production index would use posting iterators, compressed blocks, and a heap; these are intentionally outside this exact-score teaching model.",
         mistakes=["Do not skip a block on a bound equal to the Kth score when ID ties matter.", "Do not use stale or underestimated term maxima.", "Do not apply a nonnegative-sum bound to scoring with negative contributions.", "Do not label this block scan a complete WAND iterator implementation."],
         related=["dsa/inverted-index-sorted-postings-intersection", "dsa/gap-varint-postings-seek-checkpoints", "dsa/positional-inverted-index-phrase-matching"]),
    dict(path="dsa/piecewise-interpolation-rank-catalog", program="piecewise_rank_case_index.py",
         template="dsa/eytzinger-array-search-layout", section="dsa/array-data-structure-guide",
         title="Piecewise interpolation indexes: predict a bounded rank window",
         summary="Store fixed-size linear rank models and certify local binary-search windows.",
         definition="A piecewise interpolation index divides one sorted unique integer catalog into fixed-size blocks. Each block stores its first and last key, starting rank, count, and the largest training-key error of a line between endpoints. A query first finds the block whose last key is at least the target. It predicts a rank with integer arithmetic, then binary-searches only a window expanded by the certified error plus a small boundary allowance. That allowance also covers values between stored keys, where a lower bound jumps even though the line is continuous. The algorithm still compares actual keys, so the model is a hint with a checked correction step, not an authority on membership or order.",
         case="Case IDs 19, 29, 47, 61, 83, 103, 127, 149, and 173 form one immutable catalog. The lower-bound rank for 60 is three, for 103 it is five, and a target beyond the maximum returns nine. Nonuniform gaps make interpolation imperfect, but the local error window contains the exact lower bound. A missing target can have a valid insertion rank without being a member. A writer that inserts a new key between 47 and 61 changes later ranks and potentially every model boundary; the index must be rebuilt. The fixed block width is a design choice, not a claim of an optimal learned segmentation.",
         cost="Given already sorted keys, this direct constructor scans N keys once and stores O(N divided by block width) model records plus the original O(N) key array. A query binary-searches the block ends and then a local window, costing O(log B+log(E+1)) comparisons for B blocks and that block's certified error E, with the fixed allowance folded in. In the worst case E can approach the block width, so the method may offer no advantage over ordinary binary search. The exact integer predictor avoids floating-point rounding, but it assumes numeric keys and static ranks. Any claimed speedup needs measurement against bisect on the actual workload.",
         mistakes=["Do not trust a predicted rank without checking the stored keys.", "Do not ignore between-key lower-bound jumps when sizing the correction window.", "Do not keep a model after inserting or removing catalog keys.", "Do not claim fixed-width blocks are a minimal piecewise model."],
         related=["dsa/eytzinger-array-search-layout", "dsa/coordinate-compression-ordered-ranks", "dsa/resizable-array-growth-and-insert-cost"]),
    dict(path="dsa/euler-tour-rmq-constant-query-lca", program="euler_rmq_depot_ancestors.py",
         template="dsa/binary-lifting-lowest-common-ancestor", section="dsa/trees-and-heaps",
         title="Euler-tour RMQ: answer static common ancestors in constant query time",
         summary="Record DFS returns, then find the shallowest tour entry between first visits.",
         definition="A rooted tree's Euler tour records a node on entry and after returning from each child. The first visit of each node gives an interval boundary; the shallowest tour entry between two first visits is their lowest common ancestor. This implementation stores the tour, depth at each tour position, first-visit positions, and a sparse table of minimum-depth tour indices. Two overlapping power-of-two table ranges cover any query interval, giving a constant-time minimum-index choice. The tree is unweighted; road distance follows from node depths and the selected ancestor. It rejects disconnected input and cycles, and assumes the rooted topology remains fixed after construction.",
         case="The seven-depot road tree has a 13-entry Euler tour. Depots two and six first meet at depot one, and their path has four road edges. The tour repeats branch ancestors after each child returns, which is why it has 2N-1 entries rather than one entry per depot. Choosing the minimum node ID between first visits would be wrong; the sparse table compares depths. A query for the same depot returns that depot, and the distance is zero. Reorienting the root changes first visits and ancestors even if undirected path lengths remain the same, so the index must be rebuilt for a new root.",
         cost="The DFS tour takes O(N) time and stores O(N) entries. Building the sparse table costs O(N log N) time and space; an LCA and unweighted road-distance query then take O(1) time and O(1) extra query memory. This Python DFS is recursive and can hit interpreter depth limits on a long chain even though the abstract preprocessing bound holds. Binary lifting uses comparable O(N log N) storage and O(log N) queries, while a balanced-parentheses encoding offers another static tree view. None of these static indexes handles link or cut operations without rebuilding or a different structure.",
         mistakes=["Do not confuse the minimum tour depth with the minimum depot ID.", "Do not omit the return-to-parent entries from the Euler tour.", "Do not reuse first-visit positions after changing the root or edges.", "Do not claim this recursive Python build handles arbitrary-depth chains without a stack limit."],
         related=["dsa/binary-lifting-lowest-common-ancestor", "dsa/balanced-parentheses-static-tree-navigation", "dsa/sparse-table-immutable-range-minimum"]),
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
                 sort_order=44000 + order * 10, created_at=stamp, updated_at=stamp, published_at=stamp)
    entry["data"].update(section_path=section, related=[{"path": target, "title": by_path[target]["title"]} for target in related])
    entries.append(entry)
    by_path[path] = entry
    for hub_path in (section, subject_root):
        hub = by_path[hub_path]
        module = hub["data"]["modules"][0] if hub_path == section else next(
            module for module in hub["data"]["modules"] if module["title"] == by_path[section]["title"])
        module["lessons"].append(path)
        hub["body"] += '<p><a href="/' + path + '">' + html.escape(lesson["title"]) + "</a></p>"
        hub["updated_at"] = stamp

groups = [
    dict(paths=[item["path"] for item in lessons[:4]],
         project="dsa/metric-centroid-perfect-membership-audit-project",
         quiz="quizzes/dsa-metric-centroid-perfect-membership-contracts",
         title="Project: audit metric searches, marked depots, and static membership",
         intro="Build a dispatch review that separates four questions. A BK-tree finds labels near a misspelled incident term, a vantage-point tree selects an exact nearest depot under Manhattan distance, a centroid decomposition reports distance to a marked depot in a fixed road tree, and a two-level perfect hash checks one frozen case-ID set. Record the metric and input version beside each answer. The BK and centroid examples admit limited additions, while the vantage and perfect-hash indexes need a rebuild for changed snapshots. Do not substitute one query type for another just because all four use tree-shaped records.",
         trace="Index invoice, invoces, invoices, incident, invoker, and voice. A radius-one query for invoice returns invoice and invoices. Depot central at (47,47) is five units from (50,45); west at (83,29) is four from (80,30). In the seven-node road tree, marking node four gives node two a nearest-marked distance of three, and marking six gives node five distance one. A frozen seven-ID perfect hash accepts 61 and rejects 62, even if the absent ID maps to an occupied secondary slot. Duplicate label and mark operations should leave logical contents unchanged.",
         failures="Generate short random labels and compare BK-tree radius answers with direct edit-distance scans. Compare vantage answers with exhaustive distance and ID tie ordering, especially when several points lie exactly on the pivot radius. Compare centroid marks with a breadth-first road distance oracle. Build many small perfect-hash snapshots and test every inserted key plus random absent IDs. Force a malformed road cycle, an out-of-field case ID, and a text normalization mismatch. A randomized hash retry limit is a construction failure that must be reported, never converted into a silent missing-key result. Distinguish metric computation costs from tree traversal counts.",
         mistakes=["Do not discard BK children solely because the parent label misses the radius.", "Do not prune a vantage branch across an intersecting radius boundary.", "Do not use a mark-only centroid summary to unmark a depot.", "Do not treat an occupied perfect-hash slot as exact key equality."],
         questions=[
             ("Which BK-tree child edges can satisfy radius r from a node at distance d?", "Edges between d-r and d+r inclusive", "Only edge d", "Every edge greater than d+r", "The metric triangle inequality bounds a candidate's distance through the parent edge; both band boundaries can contain valid labels."),
             ("What happens when an inserted BK label already exists?", "The insertion returns false without a new node", "A duplicate child is added at edge zero", "The entire tree is rebuilt", "Zero edit distance identifies the same stored label, so a unique-label index does not allocate another copy."),
             ("What is the worst BK-tree query shape?", "It can visit all N labels", "It always visits one node", "It is guaranteed logarithmic", "A broad radius or poorly separated labels can keep every child edge inside the admissible metric band."),
             ("What makes vantage pruning exact?", "A metric triangle inequality and the pivot-radius bound", "Sorted depot IDs alone", "One arbitrary coordinate comparison", "The difference between pivot-query distance and partition radius lower-bounds the other side's possible distance."),
             ("How are equal-distance depots ordered here?", "By smaller depot ID", "By insertion time", "By larger coordinate sum", "The comparison key stores distance first and depot ID second, making exact ties reproducible."),
             ("What happens after a depot moves?", "Rebuild the static vantage partitions", "Only rename the depot ID", "Keep all pivot distances unchanged", "Every radius partition was calculated from the old coordinate snapshot and may no longer bound search."),
             ("How many centroid records does one mark inspect?", "O(log N) along its decomposition path", "Every original edge on every mark", "Always one record", "Removing a centroid halves each remaining component, so one node belongs to logarithmically many nested components."),
             ("Can the current centroid example unmark?", "No; its minimum summaries only decrease", "Yes; deleting one integer repairs all minima", "Yes; each query clears marks", "Removing a current best mark requires knowing the next-best candidate for every affected centroid, which this model does not retain."),
             ("What graph is required by the centroid model?", "One fixed connected acyclic road tree", "Any changing directed graph", "A disconnected graph with arbitrary cycles", "Its decomposition and precomputed path distances assume a tree whose topology remains unchanged."),
             ("Why allocate S-squared secondary slots for a first-level bucket of S keys?", "To find a collision-free second hash for that fixed bucket", "To store S-squared duplicate keys", "To support arbitrary future insertions", "The construction retries second-level hashes until the current S keys occupy distinct positions."),
             ("Why compare the exact key after perfect-hash lookup?", "An absent key can land on an occupied slot", "Stored keys are never unique", "The first hash is too slow", "Collision-free placement applies to the stored set; it does not make every outside key map to an empty slot."),
             ("What does a bounded hash-construction retry failure mean?", "The snapshot index was not built and must not be published", "Every absent key is now present", "Lookup becomes exact by default", "Finite retries can exhaust without a suitable selection, so the caller needs a rebuild or explicit failure handling."),
         ]),
    dict(paths=[item["path"] for item in lessons[4:]],
         project="dsa/fm-block-max-model-euler-audit-project",
         quiz="quizzes/dsa-fm-block-max-model-euler-contracts",
         title="Project: audit text intervals, score bounds, rank models, and ancestor tours",
         intro="Build a frozen incident-search release with four separate indexes. An FM-index counts and locates exact text patterns, a block-max posting summary skips document-ID blocks that cannot beat the current top-k score, a piecewise interpolation catalog predicts a bounded lower-bound rank, and an Euler-tour sparse table answers lowest common ancestors for a fixed depot tree. Each index makes a different statement about its source snapshot. Publish the text, document scores, sorted case IDs, and tree topology with version labels so a query never combines old pruning bounds with new documents or old tour positions with new roads.",
         trace="In cabacaba, backward search for aba returns count two and offsets one and five. A five-document score index ranks document 21 at ten above document 19 at eight and skips three low-bound blocks. A sorted case catalog gives lower-bound rank three for target 60, rank five for 103, and rank nine beyond its maximum. The seven-depot Euler tour has thirteen entries; nodes two and six share node one as their lowest common ancestor and are four roads apart. Verify these outputs against direct suffix scans, full document scoring, ordinary bisect, and parent-path ancestry.",
         failures="Use repeated text characters and overlapping patterns to test the FM interval, and reject a sentinel in text or query. Fuzz nonnegative document weights, absent terms, equal scores, and ID ties against exhaustive ranking; an upper bound equal to the current cutoff must remain searchable. Test interpolation targets at every key, every between-key gap, and beyond the endpoints. Generate random trees and compare sparse-table answers with a direct ancestor walk. Change one source snapshot after building each index and record its required rebuild; none of these four examples includes a live incremental update protocol. Report Python memory separately from compact-index theory.",
         mistakes=["Do not present full FM rank arrays as compressed storage.", "Do not skip an equal-bound block when a smaller document ID can win a tie.", "Do not use a predicted rank without exact correction.", "Do not compare depot IDs instead of depths in Euler range minimum queries."],
         questions=[
             ("What does backward FM search narrow?", "A half-open interval of sorted suffix rows", "A mutable graph component", "A document-score heap", "Each prepended character uses first-column offset and last-column rank to map the current suffix interval to a smaller one."),
             ("Which FM data does this example retain for locating?", "The full suffix-position array", "Only a Bloom filter", "No position information", "Counting needs only the matching interval, while this teaching version reads retained suffix positions to list original offsets."),
             ("What happens if the sentinel appears inside input text?", "Construction rejects the text", "It becomes an ordinary repeated character", "Only the final count changes", "The unique terminator is part of the suffix-order contract and cannot also occur as an internal text character."),
             ("How is a block score upper bound formed here?", "Sum each query term's maximum nonnegative weight in that block", "Take the minimum document ID", "Average only the already scored documents", "Every document's nonnegative term score is bounded by that term's block maximum, so their sum bounds the full score."),
             ("Why is strict less-than used for a skip?", "An equal-score smaller-ID document might still win the tie", "Scores are never integers", "The index has no block IDs", "The ranking order breaks equal scores by document ID, so equality to the cutoff is not enough to exclude a block."),
             ("What is the worst query behavior of this block scan?", "It may score every document", "It always skips all blocks", "It has constant work independent of corpus size", "If block upper bounds remain high, exact pruning cannot discard their documents and the query reaches the full scan."),
             ("What must follow an interpolation prediction?", "Binary search within a certified correction window", "Return the predicted number as exact", "Delete the nearest key", "The line approximates rank; stored-key comparison establishes the actual lower bound, including missing targets."),
             ("When does this rank catalog need rebuilding?", "After a key insertion or deletion changes sorted ranks", "After every read-only query", "Only when a target is absent", "Fixed block endpoints and position errors were certified for one immutable sorted key snapshot."),
             ("What does a target above the final catalog key return?", "The catalog length as insertion rank", "The final stored key's value", "A negative rank", "A lower bound beyond every key is the one-past-end position, whether or not the target is a member."),
             ("Which Euler entry gives the common ancestor between first visits?", "The shallowest tour node in that interval", "The numerically smallest depot ID", "The last inserted depot", "A depth minimum over the Euler subarray corresponds to the first shared ancestor reached between the two visits."),
             ("How many entries does a tree Euler tour have here?", "2N-1 for N nodes", "Exactly N squared", "Exactly N without parent returns", "DFS records one entry per node plus one return entry per tree edge, totaling N+N-1."),
             ("What is the query cost after the sparse table is built?", "O(1) for LCA and unweighted distance", "O(N) for every pair", "O(log N) only after each tree edit", "Two overlapping precomputed range minima cover the first-visit interval; depth arithmetic then gives road distance."),
         ]),
]

for group_number, group in enumerate(groups):
    project_path, quiz_path = group["project"], group["quiz"]
    assert project_path not in by_path and quiz_path not in by_path
    project = copy.deepcopy(by_path["dsa/allocation-ownership-coalescing-audit-project"])
    project.update(id=str(uuid.uuid5(uuid.NAMESPACE_URL, "aitrove:" + project_path)), path=project_path,
                   title=group["title"], summary="Compare four new structures with direct oracles and failure traces.",
                   sort_order=44090 + group_number * 20, created_at=stamp, updated_at=stamp, published_at=stamp)
    project["data"].update(reading_minutes=35, related=[{"path": path, "title": by_path[path]["title"]} for path in group["paths"]])
    project["body"] = "<p>" + html.escape(group["intro"]) + "</p>"
    project["body"] += "<h2>Acceptance trace</h2><p>" + html.escape(group["trace"]) + "</p>"
    project["body"] += "<h2>Failure and cost review</h2><p>" + html.escape(group["failures"]) + "</p>"
    project["body"] += "<h3>Common Mistakes</h3><ul>" + "".join("<li>" + html.escape(item) + "</li>" for item in group["mistakes"]) + "</ul>"
    project["body"] += "<h2>Connected lessons</h2>" + links(group["paths"] + ["dsa/projects", "dsa/quizzes", subject_root])
    entries.append(project)
    by_path[project_path] = project
    assert len(group["questions"]) == 12
    balanced = []
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
                sort_order=44100 + group_number * 20, created_at=stamp, updated_at=stamp, published_at=stamp)
    quiz["data"].update(duration_minutes=20,
                        related=[{"path": path, "title": by_path[path]["title"]} for path in group["paths"] + [project_path]],
                        questions=balanced)
    quiz["body"] = "<p>Choose the invariant or failure response implied by each operation contract. Verify the working program against a direct reference model.</p><h2>Lessons</h2>" + links(group["paths"]) + "<h2>Design exercise</h2>" + links([project_path, subject_root])
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
    ("dsa/ternary-search-tree-incident-completion", "dsa/bk-tree-edit-distance-label-search"),
    ("dsa/trigram-index-verified-substring-candidates", "dsa/bk-tree-edit-distance-label-search"),
    ("dsa/kd-tree-exact-nearest-depot", "dsa/vantage-point-metric-nearest-depot"),
    ("dsa/spatial-hash-grid-moving-points", "dsa/vantage-point-metric-nearest-depot"),
    ("dsa/heavy-light-tree-path-sums", "dsa/centroid-decomposition-nearest-marked-depot"),
    ("dsa/link-cut-forest-path-sums", "dsa/centroid-decomposition-nearest-marked-depot"),
    ("dsa/linear-hashing-incremental-bucket-splits", "dsa/two-level-perfect-hashing-static-case-ids"),
    ("dsa/static-xor-filter-membership", "dsa/two-level-perfect-hashing-static-case-ids"),
    ("dsa/suffix-array-lcp-incident-search", "dsa/fm-index-backward-substring-search"),
    ("dsa/wavelet-matrix-static-rank-quantile", "dsa/fm-index-backward-substring-search"),
    ("dsa/inverted-index-sorted-postings-intersection", "dsa/block-max-postings-exact-topk-pruning"),
    ("dsa/gap-varint-postings-seek-checkpoints", "dsa/block-max-postings-exact-topk-pruning"),
    ("dsa/eytzinger-array-search-layout", "dsa/piecewise-interpolation-rank-catalog"),
    ("dsa/coordinate-compression-ordered-ranks", "dsa/piecewise-interpolation-rank-catalog"),
    ("dsa/binary-lifting-lowest-common-ancestor", "dsa/euler-tour-rmq-constant-query-lca"),
    ("dsa/balanced-parentheses-static-tree-navigation", "dsa/euler-tour-rmq-constant-query-lca"),
]:
    entry = by_path[old_path]
    entry["body"] += '<p><a href="/' + target + '">' + html.escape(by_path[target]["title"]) + "</a> adds a distinct structure contract to compare.</p>"
    entry["updated_at"] = stamp

fixture.write_text(json.dumps(entries, ensure_ascii=False, indent=2) + "\n")
print(json.dumps({"lessons": len(lessons), "projects": len(groups), "quizzes": len(groups),
                  "new_routes": len(lessons) + 2 * len(groups)}))
