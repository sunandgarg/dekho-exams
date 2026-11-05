"""Add eight new DSA structures, connected projects, and decision quizzes."""

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
    dict(path="dsa/palindromic-tree-online-distinct-substrings", program="palindromic_incident_tree.py",
         template="dsa/suffix-automaton-online-substrings", section="dsa/trees-and-heaps",
         title="Palindromic trees: index distinct palindromes as text arrives",
         summary="Append code points, follow suffix links, and count each distinct palindromic substring once.",
         definition="A palindromic tree keeps one node for each distinct nonempty palindrome in the text seen so far. Two special roots represent lengths minus one and zero. An append walks suffix links from the previous longest palindromic suffix until the new code point can extend that suffix on both sides. Its transition either reuses a node or creates exactly one node; the new node's suffix link points to its longest proper palindromic suffix. This index tracks how often a node was the longest suffix at an append. A later descending-length pass propagates those counts to shorter suffixes, yielding total occurrences. It accepts Unicode code points, not grapheme clusters or normalized user-visible characters.",
         case="An incident code stream receives abacaba one code point at a time. It contains seven distinct nonempty palindromes, and the longest has length seven. The tree creates a node only when an append introduces a palindrome not seen before; an existing transition increments its end count. The example prints a sorted list of propagated occurrence counts because node IDs describe construction history, not lexicographic text order. If a caller asks for counts before the propagation pass, an inner palindrome such as a would be undercounted. Appending after a count query is safe here because that query works on a copy of the end counters.",
         cost="With dictionary transitions and ordinary expected constant-time lookups, processing N code points takes O(N) expected time and O(N) nodes and transitions. The example's explicit count finalization sorts nodes by palindrome length, so that report costs O(N log N) time and O(N) temporary memory. The streaming index itself never stores every occurrence as a separate node. Hash-table worst cases, Unicode normalization policy, and the cost of retaining the full input text still matter. Use a suffix array or automaton when arbitrary substring questions dominate; this index answers palindrome-specific structure questions.",
         mistakes=["Do not count the two special roots as nonempty palindromes.", "Do not read raw end counters as total occurrence counts.", "Do not treat code-point equality as grapheme-aware or normalized text matching.", "Do not assume a transition creates a new node on every append."],
         related=["dsa/suffix-automaton-online-substrings", "dsa/suffix-array-lcp-incident-search", "dsa/ternary-search-tree-incident-completion"]),
    dict(path="dsa/segment-tree-beats-range-cap-sum", program="segment_beats_capacity_caps.py",
         template="dsa/lazy-segment-tree-range-add-minimum", section="dsa/range-query-structures",
         title="Segment tree beats: cap a range while retaining its sum",
         summary="Track the largest and second-largest capacity to skip or apply a range cap safely.",
         definition="This segment tree supports range chmin: replace every capacity in a half-open interval by the smaller of itself and a limit. A node stores its sum, largest value, second distinct largest value, and count of the largest. If the limit is at least the maximum, nothing changes. If it lies strictly above the second maximum, only the current maxima change, so the sum can be corrected without visiting leaves. Otherwise the update descends. A deferred cap is pushed to children before partial work; a parent maximum is enough to constrain a child because the second-maximum condition held when the parent was capped. The program supports range sum and caps, not range add, assignment, or range chmax.",
         case="A depot has daily capacity readings 47, 19, 83, 61, 29, and 103. Capping positions one through four at 47 reduces 83 and 61 and leaves the other readings alone, producing total 292. A later cap of positions zero through two at 23 yields first-three total 65 while the last three total 179. A cap equal to an existing maximum is a no-op. A limit below the second maximum cannot be applied to a whole mixed node by changing only the maximum count; the update must descend or its sum will be wrong.",
         cost="Build time and storage are O(N). A range-sum query visits O(log N) tree nodes after deferred caps are pushed. One cap can visit O(N) nodes in the worst case; repeated operations gain an amortized bound from the decreasing maximum structure, but that is not a per-operation latency promise. The Python implementation uses four arrays of size proportional to N and recursive calls of depth O(log N). It handles signed integer capacities, though a real capacity policy may reject negatives at its API boundary. A simple lazy segment tree is easier when updates are only additive.",
         mistakes=["Do not cap a node when the limit is at or below its second distinct maximum.", "Do not update the sum without multiplying the drop by the maximum count.", "Do not forget to push a parent cap before reading a partial child range.", "Do not promise every individual cap is logarithmic."],
         related=["dsa/lazy-segment-tree-range-add-minimum", "dsa/segment-tree-range-sum-update", "dsa/sparse-coordinate-segment-tree"]),
    dict(path="dsa/wavelet-matrix-static-rank-quantile", program="wavelet_matrix_alert_rank.py",
         template="dsa/wavelet-tree-subarray-order-statistics", section="dsa/range-query-structures",
         title="Wavelet matrices: count frequencies and find subarray quantiles",
         summary="Partition a static integer sequence by successive bits for window frequency and kth-value queries.",
         definition="A wavelet matrix stores one bit sequence per value bit position, starting with the most significant bit. At each level it stably places all zero-bit values before one-bit values and records a prefix count of ones plus the number of zeros. A query translates a half-open position interval into its zero or one child interval at every level. Frequency follows the target's bits; kth chooses a zero branch when its count covers the requested zero-based rank, otherwise subtracts that count and follows ones. Unlike a pointer-based wavelet tree, each level is one global sequence. This example accepts nonnegative integers and retains unpacked Python prefix arrays rather than compressed bitvectors.",
         case="A static alert-level stream is 47, 19, 83, 47, 29, 61, 19. The third smallest value in positions one through five is 47; value 47 appears twice in the first five positions. Both repeated 47s remain separate observations, so this is a sequence index, not a set. Frequency for a value outside the represented bit width is zero. An empty kth window is rejected because no rank can be valid. Replacing one alert level changes every later stable partition at some bit level, so the matrix must be rebuilt from a new snapshot.",
         cost="For N values and W bits in the largest value, construction takes O(NW) time and O(NW) integers in these prefix arrays. Frequency and kth each take O(W) time and O(1) query memory. A packed bitvector implementation can change practical memory use substantially; this Python teaching version does not claim succinct storage. The static wavelet tree elsewhere in this curriculum answers a related subarray order question with recursive nodes. This matrix emphasizes the levelwise layout and direct bit routing, which is useful when the alphabet is fixed and reads dominate updates.",
         mistakes=["Do not collapse duplicate values during construction.", "Do not pass an inclusive right endpoint to a half-open query.", "Do not use a rank outside the selected window.", "Do not describe Python prefix lists as compressed bitvectors."],
         related=["dsa/wavelet-tree-subarray-order-statistics", "dsa/bitvector-rank-select-superblocks", "dsa/merge-sort-tree-threshold-count"]),
    dict(path="dsa/two-stack-sliding-window-aggregation", program="two_stack_window_aggregate.py",
         template="dsa/queue-fifo-deque-boundary", section="dsa/stacks-and-queues",
         title="Two-stack window aggregation: keep FIFO order under a monoid",
         summary="Aggregate an append-and-expire window without recomputing every member.",
         definition="A two-stack aggregate queue stores each incoming calibration in a back stack with the aggregate from oldest to newest within that stack. Its front stack stores outgoing calibrations with the aggregate from its top toward the older interior. When the front is empty, the back is transferred once, reversing element order and rebuilding front aggregates. The total is the composition of the front and back aggregates in FIFO order. This matters for noncommutative operations: the affine calibration pair (scale, shift) composes left to right modulo 97. It is an associative operation with identity (1,0), so a combined result can be read without enumerating the window.",
         case="Three calibrations arrive: (2,19), (3,7), and (5,11). The combined transform is (30,40). Removing the oldest returns (2,19); adding (7,23) yields a new combined transform of (8,54). If the program swapped the front and back aggregate order, additions and multiplications of the shifts would produce a different result even though a simple sum test might pass. The queue rejects a removal from an empty window. It does not support removing an arbitrary middle calibration or changing an existing entry.",
         cost="Append and remove-oldest take O(1) amortized time when the aggregate operation itself is O(1): each entry enters and leaves each stack at most once. A transfer makes one removal O(N) worst-case, so latency-sensitive services need a stricter queue design or bounded transfer work. The combined aggregate is O(1) and storage is O(N). This model performs modular integer arithmetic; if aggregation produces a growing object, copying that object can dominate the stated bounds. A monotone deque is often better for a minimum specifically, while this structure accepts any associative operation with an identity.",
         mistakes=["Do not reverse operand order for a noncommutative aggregate.", "Do not claim worst-case constant time for the transfer-triggering removal.", "Do not use an operation without associativity and an identity.", "Do not treat this FIFO interface as arbitrary-range aggregation."],
         related=["dsa/monotonic-deque-window-minimum", "dsa/queue-fifo-deque-boundary", "dsa/disjoint-sparse-table-range-sum"]),
    dict(path="dsa/linear-hashing-incremental-bucket-splits", program="linear_hashing_case_index.py",
         template="dsa/extendible-hash-directory-bucket-splits", section="dsa/hash-tables",
         title="Linear hashing: split one bucket at a time as a table grows",
         summary="Use a split pointer and two moduli instead of doubling an entire directory at once.",
         definition="Linear hashing grows a hash table by splitting buckets in fixed round-robin order. A level defines a base modulus; buckets before the split pointer use the doubled modulus, while later buckets still use the base. A split appends one bucket, redistributes only the pointed-to bucket with the doubled modulus, and advances the pointer. When the pointer completes a round, the level increases and the pointer resets. This teaching model stores nonnegative integer case IDs in Python sets and starts with two buckets. It splits when global average occupancy exceeds a configured count. A bucket may still overflow its nominal capacity under skew; the capacity is a growth trigger, not a hard per-bucket limit.",
         case="With a trigger of two IDs per bucket, inserting seven case IDs expands the table from two to four buckets. The fourth bucket is not obtained by rehashing every stored case ID in one stop-the-world pass. An ID is always located by its current level and split pointer, so membership for 61 remains true after intervening splits. Removing 29 changes membership but does not contract the table. A service that assumes all buckets use the same modulus during a partial round will send some old keys to the wrong bucket and report false negatives.",
         cost="Locating a bucket uses O(1) integer arithmetic. Membership, insertion, and removal then pay for that bucket's set operation; expected O(1) lookup depends on ordinary hashing and a usable distribution, while adversarial skew has no fixed bucket-size bound. A split takes O(B) time and temporary space for B entries in the pointed-to bucket, not necessarily the bucket that triggered growth. Table storage is O(N plus bucket count). This example does not persist bucket pages, manage overflow chains, shrink after deletion, or handle concurrent readers during a split. Extendible hashing uses a different directory-doubling policy.",
         mistakes=["Do not use the doubled modulus for buckets that have not split yet.", "Do not split only the bucket that happened to overflow.", "Do not interpret the occupancy trigger as a hard collision limit.", "Do not assume deletion contracts this grow-only implementation."],
         related=["dsa/extendible-hash-directory-bucket-splits", "dsa/hash-map-collision-and-load-contract", "dsa/cuckoo-hashing-relocation-rebuild"]),
    dict(path="dsa/offline-coordinate-fenwick-rectangle-counts", program="offline_coordinate_fenwick_2d.py",
         template="dsa/two-dimensional-fenwick-rectangle-sums", section="dsa/range-query-structures",
         title="Compressed 2D Fenwick trees: toggle known points and count rectangles",
         summary="Predeclare possible coordinates, then maintain live point counts through sparse Fenwick catalogs.",
         definition="A compressed two-dimensional Fenwick tree fixes all possible point coordinates before updates begin. Each x Fenwick node catalogs the y coordinates that could contribute to it and owns a local y Fenwick array. Toggling a known point visits its O(log M) x ancestors and updates one y index within each. A two-dimensional prefix query visits x predecessors and asks each local y array for the count below a y boundary. Four prefix results give a half-open rectangle count. This model stores presence as zero or one; repeated activation or removal returns false rather than changing multiplicity. New coordinates need a full catalog rebuild, even if the outer x value already exists.",
         case="A catalog lists five possible depot points, including two with x equal to 47. Four are active. Rectangle [15,60) by [45,65) contains three active points. Removing (47,61) lowers the answer to two without rebuilding the y catalogs. A point at x equal to 60 or y equal to 65 would be excluded. If an update tried an unlisted coordinate, it would fail explicitly instead of silently losing its value in a missing inner Fenwick array. The index counts active points, not weights or nearest-neighbor distances.",
         cost="Let M be the number of possible points. Every point is copied into O(log M) y catalogs, using O(M log M) stored coordinate entries and Fenwick cells. The direct construction sorts and deduplicates each catalog, with O(M log-squared M) upper-bound time. Toggling and rectangle counting take O(log-squared M) time and O(1) extra query memory beyond those catalogs. Python lists and tuples carry overhead. A dense fixed-grid Fenwick array may be simpler for a small domain; a static range tree can answer counts without supporting live toggles.",
         mistakes=["Do not update a coordinate omitted from the frozen catalog.", "Do not count upper rectangle boundaries in half-open queries.", "Do not toggle an already active point as though duplicates were supported.", "Do not confuse sparse coordinate storage with a fully open coordinate universe."],
         related=["dsa/two-dimensional-fenwick-rectangle-sums", "dsa/static-two-dimensional-range-tree-counting", "dsa/two-dimensional-prefix-grid-sums"]),
    dict(path="dsa/persistent-two-list-fifo-queue", program="persistent_two_list_queue.py",
         template="dsa/queue-fifo-deque-boundary", section="dsa/stacks-and-queues",
         title="Persistent two-list queues: fork FIFO dispatch history",
         summary="Share immutable linked nodes across queue versions while preserving arrival order.",
         definition="A persistent two-list queue keeps front and rear chains of immutable linked pairs. New items are consed to the rear, while removal takes the head of the front. When the front empties, reversing the rear yields a new front in FIFO order. Each operation returns a new queue version instead of editing the old one. Existing versions can therefore answer an audit replay after later dispatch actions. The example normalizes eagerly when necessary and returns the removed case ID beside the successor version. It stores IDs, not mutable case records; if record objects changed elsewhere, the queue snapshot would not freeze their contents.",
         case="A morning queue holds cases 47, 19, and 83. Removing its head returns 47 and a midday version; appending 61 to that version yields an afternoon queue with 19, 83, 61. The morning version still reads 47, 19, 83. Mutating a shared linked node to save an allocation would corrupt both histories. A branch made from an old queue is allowed, but repeated branches can each trigger the same rear reversal; the ordinary constant amortized bound applies along a linear update history, not automatically to every adversarial branching workload.",
         cost="Consing an enqueue or removing a ready front is O(1). Reversing a rear chain takes O(N) time and allocates O(N) new nodes on that operation; along one linear history, each enqueued item is reversed once, yielding O(1) amortized queue operations. A full values listing takes O(N). Retained versions keep referenced nodes alive, so memory grows with live history and branches. The two-list representation is much simpler than a real-time persistent queue, which is needed if a strict per-operation latency bound or heavy branching is required.",
         mistakes=["Do not mutate a node shared by an older version.", "Do not claim worst-case constant time for a reversal.", "Do not apply the linear-history amortized bound blindly to repeated branches.", "Do not mistake a queue of IDs for a deep snapshot of mutable case records."],
         related=["dsa/queue-fifo-deque-boundary", "dsa/immutable-index-snapshot-publication", "dsa/immutable-rope-text-snapshots"]),
    dict(path="dsa/balanced-parentheses-static-tree-navigation", program="balanced_parentheses_org_tree.py",
         template="dsa/iterative-binary-tree-traversal-orders", section="dsa/trees-and-heaps",
         title="Balanced-parentheses trees: encode an ordered hierarchy",
         summary="Represent each static subtree as one matching parenthesis interval.",
         definition="A depth-first traversal can encode an ordered rooted tree by writing an opening parenthesis on entry to a node and a closing parenthesis on exit. Every subtree occupies one contiguous balanced interval. Its node count is half the interval length; an ancestor's interval contains every descendant interval. The example builds opening and closing positions and parent links for an organization hierarchy, then answers subtree size and ancestry directly. It finds a lowest common unit by walking parent links from one node and testing ancestors of the other. This is a teaching index with explicit dictionaries; a genuinely succinct representation would pack the bit sequence and add compact rank, select, and matching support.",
         case="An operations root has dispatch and quality branches. Dispatch owns east and west, while quality owns audit. The encoding is ((()())(())); dispatch spans three nodes and contains east. The lowest common unit for east and audit is operations. Child order affects the encoding even when the parent relationships are unchanged, so writers must define that order before publication. The constructor rejects repeated or unreachable mapped nodes. This index is static: inserting a unit changes positions after it and requires rebuilding the encoding and its maps.",
         cost="Building the sequence and explicit maps visits N nodes and edges once, using O(N) time and O(N) Python objects. Subtree size and interval-based ancestry are O(1) after construction. This direct lowest-common-unit query takes O(H) time and O(H) temporary set space for hierarchy height H; it does not claim constant-time succinct navigation. Storage is not 2N bits because the example retains strings, dictionaries, and labels. A binary-lifting table is preferable for many common-ancestor queries when O(N log N) auxiliary space is acceptable.",
         mistakes=["Do not call an unpacked Python representation succinct.", "Do not confuse a parenthesis position with a node label.", "Do not use stale positions after a hierarchy edit.", "Do not claim this direct parent-walk common-ancestor query is constant time."],
         related=["dsa/binary-lifting-lowest-common-ancestor", "dsa/bitvector-rank-select-superblocks", "dsa/louds-level-order-alert-trie"]),
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
                 sort_order=43800 + order * 10, created_at=stamp, updated_at=stamp, published_at=stamp)
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
         project="dsa/palindrome-cap-quantile-window-audit-project",
         quiz="quizzes/dsa-palindrome-cap-quantile-window-contracts",
         title="Project: audit streaming palindromes, range caps, quantiles, and window order",
         intro="Build an incident-analysis bench with four independent indexes. Append alert code points to a palindromic tree, cap mutable capacity readings through a segment tree, answer frozen alert-level quantiles through a wavelet matrix, and compose a FIFO calibration window with two aggregate stacks. Give each query an input version and compare it with a direct model. The palindromic and window indexes accept appends, the cap tree mutates a fixed-length array, and the wavelet matrix is a frozen snapshot. Those lifecycle differences are part of the contract, not implementation trivia.",
         trace="Append abacaba and verify seven distinct nonempty palindromes, longest length seven, and propagated occurrence totals. Cap readings 47, 19, 83, 61, 29, 103 in positions one through four at 47 and verify total 292. In the frozen alert stream, the third smallest value in positions one through five is 47 and the first five positions contain two copies of 47. Compose calibrations (2,19), (3,7), (5,11), remove the oldest, append (7,23), and verify the transform changes from (30,40) to (8,54). All windows are half-open.",
         failures="Test random text prefixes against a direct set of palindromic substrings, cap/sum sequences against a plain list, matrix ranks against sorted slices, and aggregate queues against left-to-right function composition. Include repeated characters, negative capacities, duplicate alert levels, and an empty queue. Count query rebuilds separately from mutation work: a matrix edit requires a new snapshot, while a palindromic append changes at most one distinct node. Record the worst observed cap-node visits and transfer length without advertising them as strict logarithmic bounds. A code result that matches one trace is insufficient if its hidden maximum or stack order invariant is already corrupt.",
         mistakes=["Do not treat a raw palindrome end count as all occurrences.", "Do not cap a mixed segment without checking its second maximum.", "Do not deduplicate a wavelet matrix input stream.", "Do not swap calibration operands when composition is noncommutative."],
         questions=[
             ("How many nonempty palindrome nodes can one append create?", "At most one", "One per matching suffix", "Always none", "The suffix-link search reaches one longest extendable suffix and its transition either exists or creates one node."),
             ("Why does occurrence reporting propagate counts?", "Shorter palindromic suffixes occur within longer suffix events", "The two special roots are ordinary words", "Every append erases old counts", "An end counter records only events where its node was the longest suffix; suffix links carry the other occurrences."),
             ("What units does this text index compare?", "Unicode code points", "Normalized grapheme clusters", "Only ASCII bytes", "The append operation accepts a one-character Python string and does not perform normalization or grapheme segmentation."),
             ("When can a cap tree change a whole node without descending?", "When the limit lies strictly above its second maximum", "Whenever its sum is positive", "Whenever the range has two values", "Then only copies of the current largest value change, and their count gives the exact sum adjustment."),
             ("What happens if a cap equals the node maximum?", "The operation is a no-op for that node", "Every element is set to zero", "The second maximum becomes the cap", "Every value is already at most the proposed limit, so no stored capacity needs a change."),
             ("What is the worst cost of one range cap?", "It can visit O(N) nodes", "It is always O(1)", "It cannot exceed one leaf", "Amortized bounds over a sequence do not prevent a single cap from descending through many mixed nodes."),
             ("What does a wavelet matrix preserve about duplicates?", "Each occurrence remains a sequence position", "It keeps one copy of each value", "It converts repeats to zero", "Stable bit partitioning moves observations but never removes them, so window frequencies count repeated readings."),
             ("How is a kth query routed at one bit level?", "Compare rank with the number of zeros in the active interval", "Always choose the one branch", "Sort the original sequence again", "Zeros precede ones in each level's stable partition, so their count decides which branch contains the rank."),
             ("What happens after changing one indexed alert level?", "Build a new static matrix snapshot", "Only change the printed output", "Remove all equal values", "A value change can alter stable partition positions at successive bit levels, invalidating the saved prefix arrays."),
             ("Why does the aggregate queue keep separate front and back results?", "To preserve FIFO operand order across a transfer", "To make addition commutative", "To permit middle deletion", "The front aggregate follows outgoing order and must compose before the back aggregate for affine transforms."),
             ("What is the cost of a transfer-triggering removal?", "O(N) worst-case, O(1) amortized along a stream", "O(1) worst-case", "O(N squared) for every removal", "The entire back stack can move at once, though each element participates in at most one such transfer."),
             ("Which algebraic property permits stack aggregates?", "Associativity with an identity", "Only commutativity", "A total ordering of entries", "Associativity permits regrouping while the identity handles an empty side; operands still keep their FIFO order."),
         ]),
    dict(paths=[item["path"] for item in lessons[4:]],
         project="dsa/split-grid-version-hierarchy-audit-project",
         quiz="quizzes/dsa-split-grid-version-hierarchy-contracts",
         title="Project: audit hash splits, spatial toggles, queue versions, and tree intervals",
         intro="Build an operations registry with four distinct ownership rules. A linear hash index accepts live case IDs and splits buckets one at a time. A compressed two-dimensional Fenwick index toggles known depot coordinates. A persistent FIFO queue retains morning and afternoon dispatch versions. A balanced-parentheses hierarchy answers static subtree and ancestry questions. Keep the case ID set, coordinate catalog, dispatch queue, and organization topology separate. Their updates have different rebuild and sharing costs; a single mutable table cannot supply the same semantics for all four.",
         trace="Insert seven nonnegative case IDs into a linear hash table with capacity trigger two and verify four buckets, a complete split round, and membership after removing 29. Activate four known depot points; rectangle [15,60) by [45,65) counts three, then two after removing (47,61). Morning queue 47, 19, 83 remains unchanged when its successor serves 47 and appends 61. The organization encoding is ((()())(())); dispatch spans three units and east plus audit share operations as their lowest common unit. A missing coordinate or repeated hierarchy node must fail explicitly.",
         failures="Compare random hash operations with a set and verify every key is in its computed bucket after each split. Compare rectangle counts with a scan of active coordinates, including excluded upper edges. Create queue branches and check that older values remain unchanged; record repeated reversal work when many branches leave the same old version. Generate small random rooted trees and compare parenthesis subtree sizes and ancestor tests with direct DFS. Then change the topology and confirm a rebuild is required. Measure bucket skew and Python metadata separately from conceptual asymptotic bounds. No structure here provides concurrent publication on its own.",
         mistakes=["Do not use one modulus for all buckets during a partial split round.", "Do not activate a point omitted from the coordinate catalog.", "Do not mutate linked queue nodes shared by old versions.", "Do not describe explicit parent maps as a succinct bit representation."],
         questions=[
             ("Which bucket does linear hashing split next?", "The bucket at its round-robin split pointer", "Always the latest inserted key's bucket", "Always the largest bucket", "Growth advances a pointer in fixed bucket order and redistributes only that pointed-to bucket."),
             ("Which modulus handles a bucket before the split pointer?", "The doubled modulus for the current level", "The old base modulus only", "A random modulus per lookup", "Those buckets have already been split in this round, so their IDs use one more address bit."),
             ("Does removing a case ID contract this example's table?", "No; removal changes membership but not bucket count", "Yes; every removal halves all buckets", "Only if the ID was odd", "The implementation has an incremental growth policy and deliberately omits a contraction policy."),
             ("When must the compressed Fenwick catalog be rebuilt?", "When a coordinate outside its possible-point set must be updated", "On every toggle of a listed point", "After every rectangle query", "Inner y catalogs are fixed before updates, so an unseen coordinate has no assigned Fenwick cells."),
             ("Which rectangle boundary is excluded?", "Each upper bound", "Each lower bound", "All points with repeated x", "The four-prefix formula uses half-open x and y intervals, excluding points equal to an upper boundary."),
             ("What does repeated activation of one point do?", "Returns false without adding a second count", "Adds another identical point", "Drops every point with that x", "The model stores a presence set, so a known active coordinate contributes exactly one to every matching query."),
             ("What happens to a prior persistent queue version?", "Its sequence stays available after a successor operation", "It is mutated in place", "It is cleared by dequeue", "Immutable linked pairs allow successor versions to share old nodes without changing the old FIFO view."),
             ("Which operation can copy a whole rear chain?", "Normalization when the front becomes empty", "Reading the count field", "Consing into a nonempty rear", "Reversing the rear list constructs a new front; one operation can pay linear work."),
             ("When can repeated queue branches weaken a simple amortized claim?", "When each branch repeats a reversal from the same old version", "When IDs are positive", "When the queue has only one item", "A linear-history potential argument does not automatically charge work shared across adversarial forks."),
             ("What does a parenthesis interval represent?", "One node and every node in its ordered subtree", "Only its immediate children", "A sorted key range", "Depth-first opening and closing tokens enclose every descendant's pair in one contiguous span."),
             ("How does this hierarchy example answer subtree size?", "Half the matching interval length", "The number of labels alphabetically before it", "Its parent depth squared", "Each node contributes one opening and one closing token inside the subtree's balanced interval."),
             ("Is this Python hierarchy a succinct 2N-bit tree?", "No; it keeps explicit dictionaries and labels", "Yes; Python strings have no overhead", "Yes; LCA is constant time here", "The parent, opening, closing, and label maps occupy O(N) objects beyond the parenthesis sequence."),
         ]),
]

for group_number, group in enumerate(groups):
    project_path, quiz_path = group["project"], group["quiz"]
    assert project_path not in by_path and quiz_path not in by_path
    project = copy.deepcopy(by_path["dsa/allocation-ownership-coalescing-audit-project"])
    project.update(id=str(uuid.uuid5(uuid.NAMESPACE_URL, "aitrove:" + project_path)), path=project_path,
                   title=group["title"], summary="Compare four structures against direct models and explicit failure traces.",
                   sort_order=43890 + group_number * 20, created_at=stamp, updated_at=stamp, published_at=stamp)
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
                summary="Twelve explained decisions about four structure invariants.",
                sort_order=43900 + group_number * 20, created_at=stamp, updated_at=stamp, published_at=stamp)
    quiz["data"].update(duration_minutes=20,
                        related=[{"path": path, "title": by_path[path]["title"]} for path in group["paths"] + [project_path]],
                        questions=balanced)
    quiz["body"] = "<p>Choose the invariant or failure response implied by each operation contract. Check the working program against a direct reference model.</p><h2>Lessons</h2>" + links(group["paths"]) + "<h2>Design exercise</h2>" + links([project_path, subject_root])
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
    ("dsa/suffix-automaton-online-substrings", "dsa/palindromic-tree-online-distinct-substrings"),
    ("dsa/suffix-array-lcp-incident-search", "dsa/palindromic-tree-online-distinct-substrings"),
    ("dsa/lazy-segment-tree-range-add-minimum", "dsa/segment-tree-beats-range-cap-sum"),
    ("dsa/segment-tree-range-sum-update", "dsa/segment-tree-beats-range-cap-sum"),
    ("dsa/wavelet-tree-subarray-order-statistics", "dsa/wavelet-matrix-static-rank-quantile"),
    ("dsa/bitvector-rank-select-superblocks", "dsa/wavelet-matrix-static-rank-quantile"),
    ("dsa/monotonic-deque-window-minimum", "dsa/two-stack-sliding-window-aggregation"),
    ("dsa/queue-fifo-deque-boundary", "dsa/two-stack-sliding-window-aggregation"),
    ("dsa/extendible-hash-directory-bucket-splits", "dsa/linear-hashing-incremental-bucket-splits"),
    ("dsa/hash-map-collision-and-load-contract", "dsa/linear-hashing-incremental-bucket-splits"),
    ("dsa/two-dimensional-fenwick-rectangle-sums", "dsa/offline-coordinate-fenwick-rectangle-counts"),
    ("dsa/static-two-dimensional-range-tree-counting", "dsa/offline-coordinate-fenwick-rectangle-counts"),
    ("dsa/immutable-index-snapshot-publication", "dsa/persistent-two-list-fifo-queue"),
    ("dsa/queue-fifo-deque-boundary", "dsa/persistent-two-list-fifo-queue"),
    ("dsa/binary-lifting-lowest-common-ancestor", "dsa/balanced-parentheses-static-tree-navigation"),
    ("dsa/louds-level-order-alert-trie", "dsa/balanced-parentheses-static-tree-navigation"),
]:
    entry = by_path[old_path]
    entry["body"] += '<p><a href="/' + target + '">' + html.escape(by_path[target]["title"]) + "</a> adds a distinct structure contract to compare.</p>"
    entry["updated_at"] = stamp

fixture.write_text(json.dumps(entries, ensure_ascii=False, indent=2) + "\n")
print(json.dumps({"lessons": len(lessons), "projects": len(groups), "quizzes": len(groups),
                  "new_routes": len(lessons) + 2 * len(groups)}))
