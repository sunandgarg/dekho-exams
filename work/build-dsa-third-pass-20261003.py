"""Extend the DSA curriculum with ordered, interval, prefix, and queue contracts."""

import copy
import datetime
import html
import json
import uuid
from pathlib import Path

fixture = Path(__file__).resolve().parents[1] / "src/data/fixtures.json"
entries = json.loads(fixture.read_text())
by_path = {entry["path"]: entry for entry in entries}
root = "dsa/dsa-tutorial-learn-data-structures-and-algorithms"
stamp = datetime.datetime.now(datetime.UTC).isoformat()

lessons = [
    {
        "path": "dsa/red-black-tree-invariant-audit",
        "title": "Red-black trees: audit color and black-height invariants",
        "section": "dsa/trees-and-heaps",
        "summary": "Check ordered keys, red-parent rules, and equal black height before trusting a tree.",
        "definition": "A red-black tree is an ordered binary search tree with a color bit on each node. The root is black; null leaves count as black; red nodes have black children; and every path from a node to a null leaf has the same number of black nodes. Those invariants bound height by O(log n), giving O(log n) worst-case search, insertion, and deletion when the algorithms maintain them. The executable case here is an invariant checker, not insertion or deletion. A checker can catch a broken state after a rotation or recoloring but cannot repair it. Duplicate-key policy must also be explicit.",
        "case": "A scheduler indexes deadlines 47, 52, and 61. Deadline 52 is the black root; 47 and 61 are red children. Both root-to-null paths contain the same number of black nodes. Adding a red node 19 beneath red node 47 makes two red nodes adjacent and fails the audit even though numeric key order still looks correct. This shows why checking only in-order traversal is insufficient. A production insertion routine must handle red-uncle recoloring, inner and outer rotations, and root recoloring, then preserve the black-height rule across the whole changed path.",
        "code": "class DeadlineNode:\n    def __init__(self, deadline, color, left=None, right=None):\n        self.deadline = deadline\n        self.color = color\n        self.left = left\n        self.right = right\n\ndef black_height(node, lower, upper):\n    if node is None:\n        return 1\n    assert lower < node.deadline < upper\n    assert node.color in (\"red\", \"black\")\n    if node.color == \"red\":\n        assert node.left is None or node.left.color == \"black\"\n        assert node.right is None or node.right.color == \"black\"\n    left_height = black_height(node.left, lower, node.deadline)\n    right_height = black_height(node.right, node.deadline, upper)\n    assert left_height == right_height\n    return left_height + (node.color == \"black\")\n\nroot = DeadlineNode(52, \"black\", DeadlineNode(47, \"red\"), DeadlineNode(61, \"red\"))\nassert root.color == \"black\"\nprint(black_height(root, float(\"-inf\"), float(\"inf\")))\nroot.left.left = DeadlineNode(19, \"red\")\ntry:\n    black_height(root, float(\"-inf\"), float(\"inf\"))\nexcept AssertionError:\n    print(\"invalid\")",
        "output": "2\ninvalid",
        "cost": "The audit visits every node and runs in O(n) time, with O(h) recursion stack for tree height h. That is separate from O(log n) search and update bounds for a correctly maintained red-black tree. The sample uses assertions for a compact teaching check; production validation should raise explicit errors even when Python optimization disables assertions. A checker also needs a root-color test at its public boundary. Never infer that a tree is valid just because local parent-child ordering holds or a single sample insertion worked.",
        "mistakes": ["Do not equate sorted in-order output with valid color invariants.", "Do not count null leaves inconsistently across paths.", "Do not present an invariant checker as a complete update implementation."],
        "related": ["dsa/binary-search-tree-order-invariant", "dsa/avl-rotation-height-invariant", "dsa/skip-list-ordered-index"],
    },
    {
        "path": "dsa/btree-page-split-insertion",
        "title": "B-trees: split full pages during ordered insertion",
        "section": "dsa/trees-and-heaps",
        "summary": "A minimum-degree page model inserts unique keys and propagates a median upward.",
        "definition": "A B-tree stores several ordered keys per node and routes searches through child ranges. For minimum degree t, every non-root node has between t minus one and two t minus one keys. All leaves have the same depth. Before descending into a full child, insertion can split it and move its median into the parent, so the next descent enters a nonfull node. The example implements unique-key insertion and search in memory with t equal to two. It omits deletion, concurrent page changes, disk persistence, and duplicate-key records; those are separate parts of a storage engine.",
        "case": "An inventory index receives bay keys 47, 52, 61, 19, 26, 58, and 83. A page holds at most three keys. As insertions fill pages, a median moves up and two children hold the keys on either side. Searching 58 succeeds; searching 49 fails. Reading every page in order yields 19, 26, 47, 52, 58, 61, 83. The shape may differ with insertion order, but the range boundaries, capacity constraints, and equal leaf depth must remain true. The application should choose page size around its actual storage medium, not this tiny classroom degree.",
        "code": "from bisect import bisect_left, bisect_right, insort\n\nclass BayPage:\n    def __init__(self, leaf=True):\n        self.leaf = leaf\n        self.keys = []\n        self.children = []\n\nminimum_degree = 2\nroot = BayPage()\n\ndef contains(page, bay_key):\n    position = bisect_left(page.keys, bay_key)\n    if position < len(page.keys) and page.keys[position] == bay_key:\n        return True\n    return False if page.leaf else contains(page.children[position], bay_key)\n\ndef split_child(parent, position):\n    full = parent.children[position]\n    right = BayPage(full.leaf)\n    median = full.keys[minimum_degree - 1]\n    right.keys = full.keys[minimum_degree:]\n    full.keys = full.keys[:minimum_degree - 1]\n    if not full.leaf:\n        right.children = full.children[minimum_degree:]\n        full.children = full.children[:minimum_degree]\n    parent.keys.insert(position, median)\n    parent.children.insert(position + 1, right)\n\ndef insert_nonfull(page, bay_key):\n    if page.leaf:\n        insort(page.keys, bay_key)\n        return\n    position = bisect_right(page.keys, bay_key)\n    if len(page.children[position].keys) == 2 * minimum_degree - 1:\n        split_child(page, position)\n        if bay_key > page.keys[position]:\n            position += 1\n    insert_nonfull(page.children[position], bay_key)\n\ndef insert(bay_key):\n    global root\n    if contains(root, bay_key):\n        return\n    if len(root.keys) == 2 * minimum_degree - 1:\n        parent = BayPage(False)\n        parent.children = [root]\n        split_child(parent, 0)\n        root = parent\n    insert_nonfull(root, bay_key)\n\ndef ordered(page):\n    if page.leaf:\n        return page.keys[:]\n    result = []\n    for position, bay_key in enumerate(page.keys):\n        result.extend(ordered(page.children[position]))\n        result.append(bay_key)\n    result.extend(ordered(page.children[-1]))\n    return result\n\nfor bay_key in (47, 52, 61, 19, 26, 58, 83):\n    insert(bay_key)\nprint(ordered(root))\nprint(contains(root, 58), contains(root, 49))",
        "output": "[19, 26, 47, 52, 58, 61, 83]\nTrue False",
        "cost": "A balanced B-tree has O(log_t n) page levels. A search or insertion visits that many nodes; searching and moving keys within a node costs O(t) CPU work in this list-based model, giving O(t log_t n) time in the simple bound. Memory is O(n) keys plus child references. A storage engine often weighs page reads separately from comparisons; this Python model does not simulate I/O, crash recovery, or write-ahead logging. Insertion may allocate a new root, and deleting keys requires borrow or merge logic absent here. Validate minimum occupancy and uniform leaf depth before treating a larger implementation as correct.",
        "mistakes": ["Do not descend into a full child without handling its split under this algorithm.", "Do not confuse a B-tree node with one binary-tree key.", "Do not infer disk durability from an in-memory page model."],
        "related": ["dsa/bplus-leaf-split-range-index", "dsa/binary-search-tree-order-invariant", "dsa/red-black-tree-invariant-audit"],
    },
    {
        "path": "dsa/interval-tree-max-endpoint-pruning",
        "title": "Interval trees: prune overlap search with subtree maximums",
        "section": "dsa/trees-and-heaps",
        "summary": "Augment ordered starts with the largest end in each subtree.",
        "definition": "An interval search tree orders intervals by start and stores the maximum end reachable in each subtree. To find any overlap with a half-open query [low, high), first check the current interval. A left subtree whose maximum end is at most low cannot overlap, so the search can skip it. The maximum field must be recomputed after insertion, deletion, or rotation. With a balanced underlying tree, one overlap search takes O(log n) in the usual augmented search bound; this teaching code uses an ordinary unbalanced BST and therefore has O(h) search and insertion for actual height h, up to O(n).",
        "case": "Maintenance windows occupy [19, 26), [31, 42), [47, 61), [52, 58), and [83, 91). A request for [25, 32) intersects [19, 26), even though only one time unit overlaps; [62, 80) intersects none. Half-open endpoints make [61, 83) nonoverlapping with both [47, 61) and [83, 91). The augmented maximum can rule out an entire left subtree, but it cannot fix a chain-shaped BST. For a live calendar, pair the augmentation with balancing and define what should happen when many windows overlap.",
        "code": "class WindowNode:\n    def __init__(self, start, end):\n        self.start = start\n        self.end = end\n        self.max_end = end\n        self.left = None\n        self.right = None\n\ndef add_window(node, start, end):\n    if node is None:\n        return WindowNode(start, end)\n    if start < node.start:\n        node.left = add_window(node.left, start, end)\n    else:\n        node.right = add_window(node.right, start, end)\n    node.max_end = max(node.end, node.left.max_end if node.left else node.end, node.right.max_end if node.right else node.end)\n    return node\n\ndef first_overlap(node, low, high):\n    while node:\n        if node.start < high and low < node.end:\n            return (node.start, node.end)\n        if node.left and node.left.max_end > low:\n            node = node.left\n        else:\n            node = node.right\n    return None\n\nroot = None\nfor start, end in ((47, 61), (19, 26), (52, 58), (83, 91), (31, 42)):\n    root = add_window(root, start, end)\nprint(first_overlap(root, 25, 32))\nprint(first_overlap(root, 62, 80))",
        "output": "(19, 26)\nNone",
        "cost": "The tree stores O(n) nodes and one max-end value per node. Building by repeated insertion is O(nh) under a current height bound h; an adversarial order can give O(n²) total. A single overlap lookup follows O(h) nodes in this unbalanced implementation. Returning every overlap can cost at least O(k) for k results and may visit more branches. Reject invalid intervals with start at or beyond end, and preserve max-end values during deletion and rotation. The returned first overlap is not guaranteed to be the earliest or shortest one.",
        "mistakes": ["Do not claim logarithmic worst-case search for an unbalanced BST.", "Do not use inclusive endpoint comparisons with this half-open contract.", "Do not leave max-end metadata stale after a structural edit."],
        "related": ["dsa/binary-search-tree-order-invariant", "dsa/segment-tree-range-sum-update", "dsa/avl-rotation-height-invariant"],
    },
    {
        "path": "dsa/compressed-trie-edge-splitting",
        "title": "Compressed tries: split shared edge labels at the divergence",
        "section": "dsa/trees-and-heaps",
        "summary": "Collapse single-child paths while retaining exact-key terminal markers.",
        "definition": "A compressed trie stores a sequence of symbols on each edge instead of forcing one node per symbol. When two keys share only part of an existing edge, insertion splits that edge at their longest common prefix. A terminal marker still distinguishes a complete stored key from a route toward longer keys. The compressed form can cut node count when keys have long nonbranching runs, but it retains edge-label storage. This sample scans a node's child labels to find a shared prefix; lookup cost depends on key length and branching degree rather than being a strict constant per character without a more specialized child index.",
        "case": "A parts index stores dock47, dock52, and doll61. The first two share dock; the third shares only do with them. Splitting at divergence leaves a shared do edge and two branches. A query for dock47 is an exact hit, while dock alone is only a path and must return false. This matters when user-entered part IDs can be valid prefixes of other IDs. Case normalization and Unicode rules must be fixed before insertion; otherwise two visually similar labels may take different compressed routes.",
        "code": "part_root = {}\n\ndef shared_length(first, second):\n    length = 0\n    while length < min(len(first), len(second)) and first[length] == second[length]:\n        length += 1\n    return length\n\ndef insert(part_code):\n    current = part_root\n    suffix = part_code\n    while suffix:\n        edge = next((label for label in current if label != \"$end\" and shared_length(label, suffix)), None)\n        if edge is None:\n            current[suffix] = {\"$end\": True}\n            return\n        width = shared_length(edge, suffix)\n        if width < len(edge):\n            old_child = current.pop(edge)\n            current[edge[:width]] = {edge[width:]: old_child}\n            edge = edge[:width]\n        current = current[edge]\n        suffix = suffix[width:]\n    current[\"$end\"] = True\n\ndef contains(part_code):\n    current = part_root\n    suffix = part_code\n    while suffix:\n        edge = next((label for label in current if label != \"$end\" and suffix.startswith(label)), None)\n        if edge is None:\n            return False\n        suffix = suffix[len(edge):]\n        current = current[edge]\n    return \"$end\" in current\n\nfor part_code in (\"dock47\", \"dock52\", \"doll61\"):\n    insert(part_code)\nprint(contains(\"dock47\"), contains(\"dock\"), contains(\"doll61\"))\nprint(list(part_root))",
        "output": "True False True\n['do']",
        "cost": "For key length L, the sample may compare against several outgoing labels at each node. With a bounded alphabet and suitable child indexing, lookup follows O(L) symbols; this compact Python mapping does not guarantee that bound for arbitrary many-way labels. The total stored label characters are bounded by inserted key material, while node count can drop relative to a one-symbol-per-edge trie. Deletion must unmark a terminal and may merge a now-single-child path. This program shows insert and exact lookup only, not deletion or concurrent mutation.",
        "mistakes": ["Do not treat every traversable prefix as a complete stored key.", "Do not split an edge without preserving its old child subtree.", "Do not claim constant-time child selection for an unbounded linear label scan."],
        "related": ["dsa/trie-prefix-index-and-terminal-flag", "dsa/hash-map-collision-and-load-contract", "dsa/bplus-leaf-split-range-index"],
    },
    {
        "path": "dsa/bounded-thread-queue-acknowledgment",
        "title": "Bounded thread queues: separate FIFO removal from task completion",
        "section": "dsa/stacks-and-queues",
        "summary": "A synchronized queue limits backlog and counts work until consumers acknowledge it.",
        "definition": "A bounded thread queue coordinates producers and consumers with a FIFO item order and a maximum count of waiting items. In Python, queue.Queue provides synchronized put and get operations; a full queue can block a producer or raise Full for a nonblocking attempt. Removing an item does not mark the task complete: a consumer calls task_done after processing, and join waits for that unfinished-task count to reach zero. This is an in-process concurrency primitive. It does not persist work, retry failed jobs, or provide a distributed acknowledgment protocol. Locking also changes latency under contention, so an O(1) endpoint storage operation is not a wall-clock completion guarantee.",
        "case": "A repair dispatcher has two waiting slots, preloaded with J-47 and J-52. A nonblocking attempt to add J-61 reports backpressure instead of silently discarding a job. One worker processes the two queued jobs and acknowledges each after appending it to its local result list. The main thread waits for the unfinished count and then for the worker to exit. Only one consumer runs here, so result order matches FIFO. With several workers, dequeue order remains defined, but completion order can differ; callers must not assume the printed order would remain identical.",
        "code": "from queue import Full, Queue\nfrom threading import Thread\n\nrepair_queue = Queue(maxsize=2)\nrepair_queue.put(\"J-47\")\nrepair_queue.put(\"J-52\")\ntry:\n    repair_queue.put_nowait(\"J-61\")\nexcept Full:\n    print(\"backpressure\")\n\nprocessed = []\ndef repair_worker():\n    for _ in range(2):\n        job_id = repair_queue.get()\n        try:\n            processed.append(job_id)\n        finally:\n            repair_queue.task_done()\n\nworker = Thread(target=repair_worker)\nworker.start()\nrepair_queue.join()\nworker.join()\nprint(processed)",
        "output": "backpressure\n['J-47', 'J-52']",
        "cost": "Queue capacity bounds waiting items at O(c) space for capacity c, excluding items already held by workers. Endpoint enqueue and dequeue use constant-time underlying operations in ordinary conditions, but lock acquisition and blocking waits have workload-dependent latency. The sample uses a known two-task count so the worker can exit; a long-running service needs a sentinel, cancellation, or shutdown contract. Calling task_done in a finally block prevents join from hanging, but it does not mean a failed job succeeded. A real worker must separately record failures and decide whether and how to retry.",
        "mistakes": ["Do not treat get as an acknowledgment of successful processing.", "Do not read qsize and assume the next put or get cannot block.", "Do not mistake an in-process queue for durable delivery."],
        "related": ["dsa/queue-fifo-deque-boundary", "dsa/ring-buffer-capacity-and-wrap", "dsa/stack-lifo-undo-contract"],
    },
]

assert all(lesson["path"] not in by_path for lesson in lessons)
for order, lesson in enumerate(lessons):
    path, section = lesson["path"], lesson["section"]
    related_paths = [section, root, *lesson["related"], "dsa/projects", "dsa/quizzes"]
    body = (
        "<p>" + html.escape(lesson["definition"]) + "</p>"
        + "<h2>Operational case</h2><p>" + html.escape(lesson["case"]) + "</p>"
        + '<h2>Working Python program</h2><pre><code class="language-python">' + html.escape(lesson["code"], quote=False) + "</code></pre>"
        + '<h3>Output</h3><pre><code class="language-text">' + html.escape(lesson["output"]) + "</code></pre>"
        + "<h2>Time, space, and tradeoff</h2><p>" + html.escape(lesson["cost"]) + "</p>"
        + "<h3>Common Mistakes</h3><ul>" + "".join("<li>" + html.escape(mistake) + "</li>" for mistake in lesson["mistakes"]) + "</ul>"
        + "<h2>Connected lessons</h2><ul>" + "".join('<li><a href="/' + related_path + '">' + html.escape(by_path[related_path]["title"]) + "</a></li>" for related_path in related_paths) + "</ul>"
    )
    entry = copy.deepcopy(by_path["dsa/fenwick-tree-point-update-prefix-query"])
    entry.update(id=str(uuid.uuid5(uuid.NAMESPACE_URL, "aitrove:" + path)), path=path, title=lesson["title"], summary=lesson["summary"],
                 body=body, sort_order=40700 + order * 10, created_at=stamp, updated_at=stamp, published_at=stamp)
    entry["data"].update(section_path=section, related=[{"path": related_path, "title": by_path[related_path]["title"]} for related_path in related_paths])
    entries.append(entry)
    by_path[path] = entry
    for hub_path in (section, root):
        hub = by_path[hub_path]
        module = hub["data"]["modules"][0] if hub_path == section else next(module for module in hub["data"]["modules"] if module["title"] == by_path[section]["title"])
        module["lessons"].append(path)
        hub["body"] += '<p><a href="/' + path + '">' + html.escape(lesson["title"]) + "</a></p>"
        hub["updated_at"] = stamp

fixture.write_text(json.dumps(entries, ensure_ascii=False, indent=2) + "\n")
print(json.dumps({"addedLessons": len(lessons), "paths": [lesson["path"] for lesson in lessons]}))
