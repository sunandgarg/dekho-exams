"""Add circular, traversal, bitset, and order-statistic lessons to fixtures."""

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
        "path": "dsa/circular-linked-list-tail-invariant",
        "program": "circular_dispatch_list.py",
        "title": "Circular linked lists: keep one tail and a valid cycle",
        "summary": "Append, rotate, and remove from a round-robin ring without losing its head.",
        "section": "dsa/linked-lists",
        "definition": "A circular singly linked list has no null link at its end: the tail node points back to the first node. Keeping only a tail reference is enough to reach both ends because tail.next is the head. This dispatch ring uses that invariant for constant-time append, one-step rotation, and removal of the current head. It tracks length so a snapshot stops after exactly that many links, avoiding an accidental infinite traversal. In the empty state tail is None and length is zero; in the singleton state tail.next points to tail itself. Removal severs the detached node's link so a caller cannot mistake it for a member of the live cycle.",
        "case": "Append D-19, D-47, and D-61. The first snapshot begins at D-19. Rotating once advances the tail reference from D-61 to D-19, which makes D-47 the new head without changing any node links. Removing that head returns D-47; the remaining ring reads D-61 followed by D-19. This convention implements fair turn order only if callers rotate or remove at the intended scheduling boundary. A ring by itself has no thread safety, job acknowledgment, or protection against a caller holding an old node reference.",
        "cost": "Append, one-step rotation, and head removal each take O(1) time and use O(1) extra space. Capturing all N members takes O(N) time and O(N) output space. A rotation by K positions would take O(K mod N) link steps in this representation; it is not a constant-time arbitrary jump. Every member adds one node and one next link, so the ring uses O(N) space. Python's cyclic garbage collector can reclaim an unreachable ring, but a live reference to any node still keeps reachable nodes alive. Use a built-in deque when the application only needs ordinary end operations and no explicit node ownership.",
        "mistakes": ["Do not leave a singleton pointing to None; it must point to itself.", "Do not use a null-terminated traversal condition on a cycle.", "Do not forget to repair tail.next when removing the head.", "Do not claim constant-time rotation by an arbitrary number of positions from this code."],
        "related": ["dsa/singly-linked-list-head-tail-invariants", "dsa/doubly-linked-list-relink-and-ownership", "dsa/queue-fifo-deque-boundary"],
    },
    {
        "path": "dsa/iterative-binary-tree-traversal-orders",
        "program": "iterative_binary_tree_traversals.py",
        "title": "Binary-tree traversals: four orders without recursion",
        "summary": "Use explicit stacks and a queue to preserve pre-, in-, post-, and level-order contracts.",
        "section": "dsa/trees-and-heaps",
        "definition": "A binary-tree traversal is an ordering contract over node visits, not a property that automatically sorts values. Pre-order visits a node before its children, in-order visits between left and right subtrees, post-order visits after both, and level-order visits breadth first. This program uses explicit stacks for the three depth-first orders and a deque for breadth-first order, avoiding Python's recursion depth limit on a long chain. Post-order stores a ready flag so a node is emitted only after both descendants have been processed. The tree is not required to satisfy a binary-search ordering rule; an in-order walk is sorted only when the tree itself has that invariant.",
        "case": "A task root T-47 has T-19 on the left and T-61 on the right; T-19 has T-07 and T-26 below it. Pre-order begins with T-47 and walks the left branch first. In-order visits T-07, T-19, T-26, T-47, then T-61. Post-order emits the leaves before their parent and ends at T-47. Level-order visits T-47, then T-19 and T-61, then the two lower tasks. These lists answer different operational questions: parent-first rendering, ordered-key inspection, dependency cleanup, and layer-by-layer work distribution.",
        "cost": "Each walk visits N nodes once and takes O(N) time, plus O(N) space for its returned list. The pre-, in-, and post-order working stacks use O(H) space for tree height H in this implementation; a degenerate chain can make H=N. The level-order queue uses O(W) working space for maximum level width W. Output storage is separate from working storage. The algorithms assume an acyclic, properly linked binary tree. If multiple parents share one mutable child or a cycle is introduced, these traversals may repeat work or fail to terminate without an additional visited-node policy.",
        "mistakes": ["Do not push a right child after a left child when a LIFO stack must visit left first.", "Do not emit a post-order parent before both children finish.", "Do not assume an arbitrary tree's in-order result is sorted.", "Do not quote O(H) total memory while retaining an O(N) result list."],
        "related": ["dsa/binary-search-tree-order-invariant", "dsa/avl-rotation-height-invariant", "dsa/graph-adjacency-list-and-bfs"],
    },
    {
        "path": "dsa/bitset-adjacency-matrix-dense-graph",
        "program": "bitset_depot_graph.py",
        "title": "Dense graph bitsets: adjacency and common neighbors",
        "summary": "Store one bit row per fixed vertex and intersect rows for shared neighbors.",
        "section": "dsa/graphs-and-disjoint-sets",
        "definition": "A bitset adjacency matrix stores one row of edge flags for each vertex. The bit at column j in row i means that vertex i connects to vertex j. This undirected depot graph mirrors every update across the two rows and rejects self-edges. Python integers hold each row, so the structure has no fixed machine-word vertex limit. Bitwise intersection followed by population count answers how many neighbors two depots share without materializing two Python sets. This representation is useful when the vertex set is fixed, adjacency is dense, or intersections dominate; it spends space even on absent edges.",
        "case": "D-19 connects to D-26 and D-47. D-61 also connects to D-26 and D-47, so the intersection of their rows has two set bits. Deleting the D-19 to D-47 edge leaves D-19 with one neighbor, D-26, and the direct adjacency query for D-47 becomes false. Repeated connect and disconnect calls are idempotent in this implementation. A different API could reject duplicates or absent removals, but callers must know which contract they are using. Vertex additions are not supported after construction because every existing row's column layout would need to agree on the new mapping.",
        "cost": "For V vertices, a conceptual bit matrix uses V² bits, or O(V²/W) machine words of W bits, plus vertex-ID lookup storage. In Python, each row is an arbitrary-precision integer with object overhead. A row update or adjacency check may scan or copy O(V/W) words rather than being constant time for unbounded V. A common-neighbor intersection and bit count similarly cost O(V/W) word work. Enumerating D set neighbors with repeated low-bit extraction performs D big-integer operations and returns O(D) values. Sparse adjacency lists need O(V+E) entries for E edges and usually win on memory when E is small; packed CSR is better for an immutable sparse graph scan.",
        "mistakes": ["Do not update only one row of an undirected adjacency matrix.", "Do not assume Python arbitrary-precision bit operations are constant time for every V.", "Do not use V²-bit storage for a huge graph with few edges without measuring the memory cost.", "Do not treat common-neighbor count as proof of connectivity or shortest-path length."],
        "related": ["dsa/graph-adjacency-list-and-bfs", "dsa/csr-sparse-graph-storage", "dsa/online-connectivity-after-edge-removal"],
    },
    {
        "path": "dsa/avl-subtree-size-rank-select",
        "program": "avl_order_statistics.py",
        "title": "AVL order statistics: maintain subtree sizes for rank and select",
        "summary": "Update height and size through every rotation so ordered positions stay correct.",
        "section": "dsa/trees-and-heaps",
        "definition": "An order-statistic tree augments each ordered node with the number of nodes in its subtree. An AVL tree also stores height to keep its shape balanced. Each insert, deletion, or rotation must refresh both fields after changing child references. Rank counts keys strictly below a requested key, even when the key is absent. Select returns the key at a zero-based ordinal by comparing that ordinal with the left subtree size and skipping the left subtree plus the current node when moving right. This implementation is a mutable set of distinct integer asset IDs; duplicate insertions and missing-key deletions raise rather than silently changing cardinality.",
        "case": "Insert assets 47, 19, 61, 52, and 83. The zero-based ordinal 2 selects 52, and rank 58 is 3 because 19, 47, and 52 are smaller. Delete 47 and enumerate all remaining ordinals: 19, 52, 61, 83. A deletion can change both balance and subtree size along the path to the root. Rotating without refreshing sizes might leave the tree search ordering intact while producing the wrong rank or select result, making this a useful invariant test beyond an ordinary membership check.",
        "cost": "For N distinct keys, AVL height is O(log N). Insert, delete, rank, and select each follow one root-to-leaf path and take O(log N) time. Inserts and deletes use O(log N) recursion stack space; rank and select use O(1) working space. Stored nodes occupy O(N) space, with one height and one size field per node. Enumerating every ordinal by calling select repeatedly costs O(N log N), as the small trace does; a single in-order traversal would take O(N). This mutable tree is not a persistent version store and is not safe for unsynchronized concurrent writers or readers during rotation.",
        "mistakes": ["Do not refresh height but leave subtree size stale after rotation.", "Do not confuse zero-based select with one-based rank in an API contract.", "Do not decrement size when a missing-key deletion raises without changing the tree.", "Do not call repeated select for every key an O(N) traversal."],
        "related": ["dsa/avl-rotation-height-invariant", "dsa/red-black-ordered-insertion", "dsa/fenwick-tree-point-update-prefix-query"],
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
                 body=body, sort_order=41500 + order * 10, created_at=stamp, updated_at=stamp, published_at=stamp)
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
