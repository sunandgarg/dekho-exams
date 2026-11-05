"""Build AI Trove's original data-structure learning path and executable cases."""

import copy
import datetime
import html
import json
import uuid
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
FIXTURE = ROOT / "src/data/fixtures.json"
entries = json.loads(FIXTURE.read_text())
by_path = {entry["path"]: entry for entry in entries}
stamp = datetime.datetime.now(datetime.UTC).isoformat()
root_path = "dsa/dsa-tutorial-learn-data-structures-and-algorithms"
sections = [
    ("dsa/array-data-structure-guide", "Arrays", "Indexed storage, range summaries, and growth costs."),
    ("dsa/linked-lists", "Linked Lists", "Pointer changes, traversal, and node ownership."),
    ("dsa/stacks-and-queues", "Stacks and Queues", "Ordering contracts for undo, buffering, and scheduling."),
    ("dsa/hash-tables", "Hashing", "Keyed lookup, collisions, and membership."),
    ("dsa/trees-and-heaps", "Trees and Heaps", "Hierarchical search and priority order."),
    ("dsa/graphs-and-disjoint-sets", "Graphs", "Adjacency, traversal, and connectivity."),
    ("dsa/range-query-structures", "Range Queries", "Point updates and repeated interval queries."),
    ("dsa/projects", "Projects", "Combine structures under an operation contract."),
    ("dsa/quizzes", "Quizzes", "Check invariants and cost claims."),
]
tabs = [{"path": root_path, "title": "Data Structures"}] + [
    {"path": path, "title": title} for path, title, _ in sections
]

lessons = [
    {
        "slug": "resizable-array-growth-and-insert-cost",
        "title": "Resizable arrays: account for growth and shifting",
        "section": sections[0][0],
        "summary": "Indexed reads are constant time; middle inserts and occasional growth pay for movement.",
        "definition": "A resizable array keeps elements in indexed order and reserves capacity beyond its current length. Reading an existing index costs O(1). Appending is O(1) amortized when capacity grows geometrically, although an individual growth operation copies O(n) references. Inserting at index zero or in the middle shifts a suffix and costs O(n). The interface promises a sequence, not a stable pointer to every element after mutation. Python lists implement this family of behavior; their exact allocation policy is an implementation detail, so do not base an API contract on a particular spare-capacity count.",
        "case": "A dispatch board records shipment IDs in arrival order. The operator appends S-47, S-52, and S-61, then inserts an urgent S-58 at position one. The urgent item is visible immediately, but the two later IDs must move. A separate index keyed by shipment ID would help repeated lookup; it would not remove the shifting cost when display order changes. If the board needs constant-time inserts at arbitrary positions, first ask whether those positions are already known as node references and whether indexed reads can be surrendered.",
        "code": "shipment_order = [\"S-47\", \"S-52\", \"S-61\"]\nshipment_order.insert(1, \"S-58\")\nprint(shipment_order[2])\nprint(shipment_order)",
        "output": "S-52\n['S-47', 'S-58', 'S-52', 'S-61']",
        "cost": "The shown insertion shifts two entries, but its asymptotic worst case is O(n) time and O(1) additional application space. The backing list may already have spare capacity or may allocate a larger block. Repeated insertion at the front of a growing list costs O(n²) total movement; append then sort or use a different representation when the workload permits. A short list often still wins through locality and low pointer overhead, so measure realistic sizes before replacing it.",
        "mistakes": ["Do not call every append worst-case O(1).", "Do not assume inserting at the front avoids moving existing entries.", "Do not confuse list capacity with its visible length."],
        "related": ["dsa/array-data-structure-guide", "dsa/singly-linked-list-head-tail-invariants", "dsa/hash-map-collision-and-load-contract"],
    },
    {
        "slug": "prefix-sum-range-query-contract",
        "title": "Prefix sums: trade one scan for constant-time ranges",
        "section": sections[0][0],
        "summary": "Build cumulative totals once, then answer immutable half-open range sums.",
        "definition": "A prefix-sum array stores the sum of all values before each boundary. With an initial zero, the sum over half-open interval [left, right) is prefix[right] minus prefix[left]. Construction costs O(n) time and O(n) extra space; each valid range query costs O(1). The contract assumes the underlying values do not change after building the prefix table. If values update, the table becomes stale and rebuilding costs O(n); a Fenwick tree or segment tree serves frequent mixed updates and queries more efficiently. Half-open bounds make adjacent ranges compose without counting a boundary twice.",
        "case": "A warehouse dashboard stores daily scanned parcel counts of 47, 31, 26, and 58. It needs the sum for days one through three, represented as [1, 4), which is 31 + 26 + 58 = 115. The first day remains outside the range. A table built from these four daily values answers many reporting windows cheaply. When a late scan changes day two from 26 to 29, the old prefix table cannot be used until rebuilt; returning its previous 115 would hide the correction.",
        "code": "daily_scans = [47, 31, 26, 58]\nprefix = [0]\nfor scan_count in daily_scans:\n    prefix.append(prefix[-1] + scan_count)\nleft_day, right_day = 1, 4\nprint(prefix[right_day] - prefix[left_day])\nprint(prefix)",
        "output": "115\n[0, 47, 78, 104, 162]",
        "cost": "The loop visits n values once and stores n + 1 totals. Query bounds must satisfy 0 <= left <= right <= n; an empty interval then returns zero. Negative counts may be valid adjustments, but they change whether a cumulative total is monotone. In fixed-width integer languages, check overflow before adding large measurements. A prefix array saves work when queries substantially outnumber updates and the input snapshot has an explicit revision.",
        "mistakes": ["Do not use inclusive right bounds with this half-open formula.", "Do not query a prefix table after the source data changes.", "Do not assume prefix totals are increasing when adjustments can be negative."],
        "related": ["dsa/resizable-array-growth-and-insert-cost", "dsa/fenwick-tree-point-update-prefix-query", "dsa/segment-tree-range-sum-update"],
    },
    {
        "slug": "singly-linked-list-head-tail-invariants",
        "title": "Singly linked lists: preserve head and tail invariants",
        "section": sections[1][0],
        "summary": "Use node links for cheap known-position changes, with linear search and pointer overhead.",
        "definition": "A singly linked list stores each value with a reference to its successor. A head reference reaches the first node; an optional tail reference makes append O(1) when maintained correctly. Prepending is O(1), but finding an arbitrary value or the predecessor of a node is O(n). Inserting after a node already in hand is O(1); finding that node is not. The empty list has both head and tail absent, and the last node points to no successor. Python object references add allocation and cache costs, so a linked list is not automatically faster than a built-in list for a small workload.",
        "case": "A repair queue records jobs J-47 and J-61, then places emergency J-52 at the head. The queue order becomes J-52, J-47, J-61 without shifting array entries. If the dispatcher later asks whether J-61 is present, traversal still walks nodes from the head. The tail must stay J-61 after the prepend. Removing the last job requires finding its predecessor unless the structure also keeps backward links. This case separates a cheap head mutation from a general indexed operation.",
        "code": "class RepairNode:\n    def __init__(self, job_id, next_node=None):\n        self.job_id = job_id\n        self.next_node = next_node\n\nhead = RepairNode(\"J-47\", RepairNode(\"J-61\"))\nhead = RepairNode(\"J-52\", head)\njob_ids = []\ncurrent = head\nwhile current is not None:\n    job_ids.append(current.job_id)\n    current = current.next_node\nprint(job_ids)",
        "output": "['J-52', 'J-47', 'J-61']",
        "cost": "The prepend allocates one node in O(1) time and space. Traversal is O(n) time and uses O(n) output space here because the demonstration builds a list; a streaming visitor could use O(1) extra space. Every node carries reference overhead, and pointer chasing tends to be less cache-friendly than contiguous storage. A cycle introduced by a bad link would make this traversal fail to terminate, so production mutation methods must maintain invariants and test empty, one-node, and last-node cases.",
        "mistakes": ["Do not claim arbitrary insertion is O(1) without an existing node reference.", "Do not leave a stale tail after removing the final node.", "Do not traverse a potentially cyclic list without a cycle policy."],
        "related": ["dsa/resizable-array-growth-and-insert-cost", "dsa/doubly-linked-list-relink-and-ownership", "dsa/queue-fifo-deque-boundary"],
    },
    {
        "slug": "doubly-linked-list-relink-and-ownership",
        "title": "Doubly linked lists: relink known nodes safely",
        "section": sections[1][0],
        "summary": "Backward links allow constant-time removal only when the target node is already known.",
        "definition": "A doubly linked list gives each node a previous and next reference. Given a valid node belonging to the list, removal changes a bounded number of links in O(1) time. Searching for the node by value remains O(n). A sentinel head and tail simplify edge cases because insertion and removal use the same link operations at both ends. The representation invariant requires adjacent nodes to agree: if A.next is B, then B.previous is A. A removed node should lose its old links so an accidental second removal cannot quietly corrupt neighbors.",
        "case": "A session tracker keeps active cards C-47, C-52, and C-61. Its hash map holds direct node references, allowing the card C-52 to move to the front after access without a list search. The list supplies recency order; the map supplies keyed lookup. When C-52 is removed, C-47 and C-61 become neighbors. The data structure is worthwhile only if the map and list are updated together; a map entry pointing to a detached node makes later operations incorrect even though both containers still exist.",
        "code": "class CardNode:\n    def __init__(self, card_id):\n        self.card_id = card_id\n        self.previous = None\n        self.next = None\n\nfirst, middle, last = (CardNode(card_id) for card_id in (\"C-47\", \"C-52\", \"C-61\"))\nfirst.next, middle.previous = middle, first\nmiddle.next, last.previous = last, middle\nfirst.next, last.previous = last, first\nmiddle.previous = middle.next = None\nprint(first.card_id, first.next.card_id, last.previous.card_id)",
        "output": "C-47 C-61 C-47",
        "cost": "Known-node removal changes four endpoint references in O(1) time and needs no new node. The structure stores two references per node, and the map used for keyed access consumes O(n) additional space. A complete implementation should guard against removing a sentinel or a node owned by another list; the small example shows the relink itself, not a concurrent production cache. Under concurrency, map and list mutations need one consistency boundary so observers cannot see an index pointing at a detached node.",
        "mistakes": ["Do not describe lookup by value as constant time without an index.", "Do not detach only one side of a neighboring pair.", "Do not keep an index entry for a removed node."],
        "related": ["dsa/singly-linked-list-head-tail-invariants", "dsa/hash-map-collision-and-load-contract", "dsa/stack-lifo-undo-contract"],
    },
    {
        "slug": "stack-lifo-undo-contract",
        "title": "Stacks: last-in-first-out for reversible edits",
        "section": sections[2][0],
        "summary": "Push inverse operations and pop them in reverse commit order.",
        "definition": "A stack exposes push, peek, and pop at one end. Its last-in-first-out order makes it suitable for nested parsing, depth-first traversal, and undo records. The invariant is order, not storage form: a resizable array can implement a stack with amortized O(1) push and O(1) pop from the end. An undo stack should hold inverse operations or enough prior state to restore them; storing only human-readable action names cannot reverse a mutation. Decide whether failed operations enter the history and what an empty pop means before exposing the API.",
        "case": "A shipment editor changes S-47 from 'queued' to 'held' and then from 'held' to 'reviewed.' To undo the latest edit, it restores 'held'; another undo restores 'queued.' The stack stores prior states in commit order, so two pops retrieve them backward. If an edit fails after partially changing external systems, a local stack is not an authoritative transaction log. The example is a local state demonstration, and a real workflow would reconcile server receipts before offering undo.",
        "code": "shipment_state = \"queued\"\nundo_states = []\nfor next_state in (\"held\", \"reviewed\"):\n    undo_states.append(shipment_state)\n    shipment_state = next_state\nshipment_state = undo_states.pop()\nprint(shipment_state, undo_states)",
        "output": "held ['queued']",
        "cost": "For m edits, the stack uses O(m) space. Each shown push is amortized O(1), and pop is O(1); history retention still needs a bound if sessions can run indefinitely. Using list.pop(0) would move remaining entries and break the intended constant-time end operation. A stored reference to mutable state may change later, so capture an immutable value or controlled copy when the undo record must represent the earlier state.",
        "mistakes": ["Do not pop an empty stack without an explicit result or error policy.", "Do not store only the new value when undo needs the old value.", "Do not assume local undo reverses a remote side effect."],
        "related": ["dsa/queue-fifo-deque-boundary", "dsa/doubly-linked-list-relink-and-ownership", "dsa/graph-adjacency-list-and-bfs"],
    },
    {
        "slug": "queue-fifo-deque-boundary",
        "title": "Queues: preserve arrival order without front shifts",
        "section": sections[2][0],
        "summary": "Use a deque for constant-time endpoint operations under a FIFO contract.",
        "definition": "A first-in-first-out queue removes the oldest enqueued item first. Python's collections.deque supports appending at the right and removing from the left without shifting the entire collection. Those endpoint operations are O(1) in the intended queue use. A queue decides order; it does not provide durable delivery, retries, consumer acknowledgment, or fairness among external workers. A bound on queue length and a behavior when full matter in a live service, because constant-time insertion does not prevent unbounded memory growth when producers outrun consumers.",
        "case": "A loading dock receives pallets P-47, P-52, and P-61. The next pickup is P-47, and P-61 remains waiting. Using a list with pop(0) would shift later entries on each pickup, which becomes expensive for a large backlog. A deque keeps the endpoint contract clear. If P-47's pickup fails after it has been removed, this in-memory queue alone cannot know whether to retry safely; the application needs a separate receipt and retry policy.",
        "code": "from collections import deque\n\nwaiting_pallets = deque([\"P-47\", \"P-52\", \"P-61\"])\nnext_pickup = waiting_pallets.popleft()\nprint(next_pickup)\nprint(list(waiting_pallets))",
        "output": "P-47\n['P-52', 'P-61']",
        "cost": "Enqueue and dequeue at opposite ends are O(1), while scanning the queue for a specific pallet is O(n). Space is O(n) for n waiting items. A deque is often the right in-process choice; a distributed queue has different guarantees about persistence, visibility, and duplicate delivery. Set backpressure or a maximum backlog before production use, and define whether an empty dequeue raises or returns a sentinel so callers do not mistake no work for a valid item.",
        "mistakes": ["Do not use list.pop(0) for a large FIFO backlog.", "Do not mistake an in-memory deque for durable messaging.", "Do not let the queue grow without a capacity or backpressure rule."],
        "related": ["dsa/stack-lifo-undo-contract", "dsa/ring-buffer-capacity-and-wrap", "dsa/graph-adjacency-list-and-bfs"],
    },
    {
        "slug": "ring-buffer-capacity-and-wrap",
        "title": "Ring buffers: make capacity and overwrite rules explicit",
        "section": sections[2][0],
        "summary": "Wrap head and tail indices while keeping count separate from physical positions.",
        "definition": "A ring buffer stores a fixed number of elements in a reusable array. Head identifies the next read slot; tail identifies the next write slot; count distinguishes empty from full when the indices coincide. Each enqueue and dequeue uses O(1) time without shifting elements. The API must choose whether a full buffer rejects new data, blocks a producer, or overwrites the oldest item. Those choices have different correctness effects. A telemetry sampler might overwrite old samples, while a payment queue must not silently discard a pending request.",
        "case": "A sensor gateway reserves three slots for latest pressure readings. It writes 47, 52, and 61, reads 47, then writes 58 into the freed physical slot. Logical read order is now 52, 61, 58 even though physical array order wraps. The fourth write before a read would be rejected under this contract. The gateway might choose overwrite semantics for a dashboard, but that would need a different method name and a lost-sample counter. Capacity is part of the interface, not a hidden implementation setting.",
        "code": "capacity = 3\nslots = [None] * capacity\nhead = tail = count = 0\nfor reading in (47, 52, 61):\n    slots[tail] = reading\n    tail = (tail + 1) % capacity\n    count += 1\noldest = slots[head]\nhead = (head + 1) % capacity\ncount -= 1\nslots[tail] = 58\ntail = (tail + 1) % capacity\ncount += 1\nprint(oldest, [slots[(head + offset) % capacity] for offset in range(count)])",
        "output": "47 [52, 61, 58]",
        "cost": "Storage is O(capacity), and each index update is O(1). The demonstration collects current readings in O(count) time only to display them. A real implementation should check count before every write and read; this short trace has known valid operations. Under concurrent producers and consumers, index changes need synchronization or a proven lock-free protocol. Modulo arithmetic is cheap relative to shifting a long list, but a zero capacity must be rejected before the first operation.",
        "mistakes": ["Do not use head == tail alone to distinguish full from empty.", "Do not overwrite unread items unless the contract says so.", "Do not share mutable indices across threads without coordination."],
        "related": ["dsa/queue-fifo-deque-boundary", "dsa/resizable-array-growth-and-insert-cost", "dsa/stack-lifo-undo-contract"],
    },
    {
        "slug": "hash-map-collision-and-load-contract",
        "title": "Hash maps: keyed lookup with collision and load costs",
        "section": sections[3][0],
        "summary": "Expected constant-time access depends on hashing, equality, and load management.",
        "definition": "A hash map assigns a key to a bucket using a hash function, then resolves collisions among keys sharing a bucket. Lookups, insertions, and deletion are expected O(1) under ordinary hashing and controlled load; worst-case work can be O(n). Correctness requires equal keys to have equal hash values and keys not to change their hash-relevant state while stored. A map's key is an identity choice, not just a performance choice: using only a shipment number without tenant scope can join two different customers' records. Python dictionaries handle collisions and resizing internally, but application key design remains the caller's responsibility.",
        "case": "Two depots both issue shipment number S-47. A global index keyed only by S-47 would overwrite one status with the other. The application uses a tuple of depot ID and shipment ID, so North/S-47 and South/S-47 remain distinct. The map returns a status quickly for a verified key, but it does not enforce tenant permissions by itself; the request layer must decide which depot key the caller may query. If the status object is mutable, returning it directly can also expose shared state that another request changes.",
        "code": "shipment_status = {\n    (\"north\", \"S-47\"): \"held\",\n    (\"south\", \"S-47\"): \"queued\",\n}\nprint(shipment_status[(\"north\", \"S-47\")])\nprint(len(shipment_status))",
        "output": "held\n2",
        "cost": "The example uses O(n) space for n keyed records and expected O(1) lookup. Resizing occasionally copies table entries, making a single insertion more expensive than the average. If every operation must have a strict worst-case bound, this ordinary hash-map contract may be insufficient. Use immutable tuple keys, test duplicate identifiers across scopes, and avoid relying on iteration order as a substitute for a sorting requirement.",
        "mistakes": ["Do not describe hash-map operations as guaranteed worst-case O(1).", "Do not omit tenant scope from a key that must be unique across tenants.", "Do not mutate a stored key's equality-relevant state."],
        "related": ["dsa/hash-set-membership-and-order", "dsa/doubly-linked-list-relink-and-ownership", "dsa/graph-adjacency-list-and-bfs"],
    },
    {
        "slug": "hash-set-membership-and-order",
        "title": "Hash sets: fast membership without an order promise",
        "section": sections[3][0],
        "summary": "Deduplicate by key while separating membership from presentation order.",
        "definition": "A hash set stores unique keys and answers membership queries in expected O(1) time. It uses hashing and equality like a hash map but does not attach an application value to each key. A set does not promise a stable sorted order, so a caller that needs a repeatable display order should sort the final keys or track order separately. Deduplication needs a deliberate identity key: two events with the same shipment ID may represent distinct scans, while two copies of the same event ID are duplicates. Choosing the wrong key can silently erase valid data.",
        "case": "A scanner exports event IDs E-47, E-52, E-47, and E-61. The second E-47 is a repeated upload, so the service counts three unique events. It still keeps the raw log for audit and uses a set only for the deduplicated view. Sorting the set gives a repeatable report, but that O(n log n) presentation step is separate from expected constant-time membership. If the IDs belonged to different depots, the key should include depot scope just as a hash map does.",
        "code": "raw_event_ids = [\"E-47\", \"E-52\", \"E-47\", \"E-61\"]\nunique_event_ids = set(raw_event_ids)\nprint(len(unique_event_ids))\nprint(sorted(unique_event_ids))\nprint(\"E-52\" in unique_event_ids)",
        "output": "3\n['E-47', 'E-52', 'E-61']\nTrue",
        "cost": "Building the set from n IDs takes expected O(n) time and O(u) space for u unique IDs. Sorting u IDs costs O(u log u) time and O(u) output storage. Worst-case collision behavior is not a guarantee of constant time. When memory is tight and the input is already sorted, adjacent duplicate removal may avoid the hash table; when the raw order matters, preserve it separately rather than expecting the set to remember it.",
        "mistakes": ["Do not assume set iteration is a stable report order.", "Do not deduplicate by a field that is not unique for the intended event.", "Do not discard the original log when audit requires raw records."],
        "related": ["dsa/hash-map-collision-and-load-contract", "dsa/graph-adjacency-list-and-bfs", "dsa/resizable-array-growth-and-insert-cost"],
    },
    {
        "slug": "binary-search-tree-order-invariant",
        "title": "Binary search trees: preserve order through every branch",
        "section": sections[4][0],
        "summary": "Search by ordered keys, but account for tree height and duplicate policy.",
        "definition": "A binary search tree stores a key at each node, with smaller keys in its left subtree and larger keys in its right subtree under a chosen duplicate policy. Search follows one branch per level and costs O(h) for tree height h. A balanced tree has h = O(log n); ordinary insertion without rebalancing can create a chain with h = O(n). The invariant applies to whole subtrees, not just immediate children. A duplicate key must either replace an associated value, increment a count, or be rejected; leaving that behavior implicit breaks search and traversal assumptions.",
        "case": "A parts catalog inserts keys 52, 47, 61, and 58. Searching for 58 visits 52, then 61, then 58. Its in-order traversal is 47, 52, 58, 61, confirming the chosen ordering on this fixture. If future uploads arrive in ascending order, a plain tree degenerates and no longer provides logarithmic lookup. A production catalog might prefer a balanced tree or database index; the simple code exposes the ordering rule without pretending it maintains balance.",
        "code": "class PartNode:\n    def __init__(self, part_code):\n        self.part_code = part_code\n        self.left = None\n        self.right = None\n\nroot = PartNode(52)\nfor part_code in (47, 61, 58):\n    current = root\n    while True:\n        side = \"left\" if part_code < current.part_code else \"right\"\n        child = getattr(current, side)\n        if child is None:\n            setattr(current, side, PartNode(part_code))\n            break\n        current = child\ncurrent = root\nvisited = []\nwhile current is not None:\n    visited.append(current.part_code)\n    current = current.left if 58 < current.part_code else current.right if 58 > current.part_code else None\n    if visited[-1] == 58:\n        break\nprint(visited)",
        "output": "[52, 61, 58]",
        "cost": "Insertion and lookup each cost O(h) time and O(1) extra space in this iterative example. The structure stores O(n) nodes and references. The code assumes unique keys; a production insertion method should explicitly reject or replace duplicates and test the path where a key equals an existing node. Deletion needs extra cases for zero, one, or two children and must reconnect subtrees without violating their global bounds. To guarantee logarithmic height, use a balancing scheme rather than hoping insertion order stays favorable.",
        "mistakes": ["Do not claim an unbalanced search tree always has O(log n) lookup.", "Do not check only immediate children when validating order.", "Do not let duplicate keys take an undocumented branch."],
        "related": ["dsa/binary-heap-priority-scheduling", "dsa/trie-prefix-index-and-terminal-flag", "dsa/hash-map-collision-and-load-contract"],
    },
    {
        "slug": "binary-heap-priority-scheduling",
        "title": "Binary heaps: select the next priority with a tie rule",
        "section": sections[4][0],
        "summary": "A min-heap exposes its least-priority tuple in logarithmic update time.",
        "definition": "A binary min-heap stores a complete tree in an array with each parent no greater than its children. The smallest key is at index zero. Insertion and removal repair the heap in O(log n) time; inspecting the smallest item is O(1). A heap does not keep every item sorted, and searching for a named item is O(n) without another index. For equal priorities, include an explicit sequence number when first-in tie behavior matters. Python's heapq compares tuple fields in order, so a unique counter also avoids comparing non-orderable task payloads.",
        "case": "A repair scheduler receives jobs J-47 at priority 2, J-52 at priority 1, and J-61 at priority 1. The two urgent jobs should run in arrival order. Their tuples include a sequence counter, so J-52 leaves before J-61 even though both have priority 1. The heap is an in-memory selection structure, not a durable job runner. If a worker fails after popping a job, the system needs an independent claim and retry record to avoid losing work.",
        "code": "import heapq\n\nrepair_heap = []\nfor arrival, (priority, job_id) in enumerate(((2, \"J-47\"), (1, \"J-52\"), (1, \"J-61\"))):\n    heapq.heappush(repair_heap, (priority, arrival, job_id))\nprint(heapq.heappop(repair_heap)[2])\nprint(heapq.heappop(repair_heap)[2])",
        "output": "J-52\nJ-61",
        "cost": "Building by repeated pushes costs O(n log n); heapify can build an existing batch in O(n). Each pop costs O(log n), and the heap retains O(n) entries. For mutable priorities, blindly pushing a changed job creates duplicates; use a versioned entry and skip stale records on pop, or maintain an indexed heap. The ordering tuple is part of correctness, not an incidental detail. Negative priorities are allowed if the contract defines them consistently.",
        "mistakes": ["Do not expect a heap's full array to be sorted.", "Do not rely on task payload comparison to break priority ties.", "Do not equate popping an in-memory heap with durable execution."],
        "related": ["dsa/binary-search-tree-order-invariant", "dsa/queue-fifo-deque-boundary", "dsa/graph-adjacency-list-and-bfs"],
    },
    {
        "slug": "trie-prefix-index-and-terminal-flag",
        "title": "Tries: make prefix search distinct from complete-key lookup",
        "section": sections[4][0],
        "summary": "Store characters along paths and mark where an actual key ends.",
        "definition": "A trie follows one edge per symbol in a key. Prefix lookup and insertion take O(L) time for key length L, independent of the number of stored keys under constant-time child lookup assumptions. A path existing does not mean its prefix is a stored complete key, so a terminal flag is necessary. Tries can use substantial memory because each node has child mappings and references. Normalize case and Unicode according to the application's identifier contract before insertion; otherwise visually similar labels may take different paths and produce confusing search results.",
        "case": "A depot indexes part codes AX47 and AX52. Prefix AX exists, but it is not a complete part code. The terminal marker on AX47 distinguishes an exact match from a prefix suggestion. The two codes share the AX nodes, which makes prefix filtering natural. A general substring search inside arbitrary product descriptions is a different problem; this trie only follows prefixes from the root. For a small catalog, a sorted list may be simpler and use less memory.",
        "code": "part_root = {}\nfor part_code in (\"AX47\", \"AX52\"):\n    current = part_root\n    for symbol in part_code:\n        current = current.setdefault(symbol, {})\n    current[\"$end\"] = True\n\ndef lookup(part_code):\n    current = part_root\n    for symbol in part_code:\n        if symbol not in current:\n            return False\n        current = current[symbol]\n    return \"$end\" in current\n\nprint(lookup(\"AX\"), lookup(\"AX47\"))",
        "output": "False True",
        "cost": "The two insertions take O(total characters) time and space. Lookup is O(L) expected time with hash-backed child maps. The sentinel key is safe here because symbols are individual characters and no input character equals the multi-character marker; a typed node with a separate boolean is clearer in a larger implementation. Deletion needs to unmark the terminal and prune only nodes no longer shared by another code. Prefix listing also pays for every descendant key returned, beyond the O(L) path walk.",
        "mistakes": ["Do not report every existing prefix as a full stored key.", "Do not mistake prefix search for arbitrary substring search.", "Do not prune a shared branch while deleting one key."],
        "related": ["dsa/binary-search-tree-order-invariant", "dsa/hash-set-membership-and-order", "dsa/graph-adjacency-list-and-bfs"],
    },
    {
        "slug": "graph-adjacency-list-and-bfs",
        "title": "Graphs: adjacency lists and breadth-first reachability",
        "section": sections[5][0],
        "summary": "Represent sparse edges explicitly and mark vertices before enqueueing.",
        "definition": "An adjacency list maps each vertex to its outgoing neighbors. For V vertices and E stored edges, it uses O(V + E) space; an adjacency matrix uses O(V²) space but offers constant-time direct edge checks. Breadth-first search explores vertices in layers from a start vertex. With a visited set, traversal takes O(V + E) time over the reachable subgraph. Mark a vertex when enqueueing, not only after dequeueing, to prevent the same vertex from entering the queue repeatedly through converging paths. Direction and edge meaning must be explicit before interpreting reachability.",
        "case": "A depot route map has directed links North to East and West, East to South, and West to South. Starting at North, the queue visits East and West before South. South is enqueued only once despite two incoming paths. The traversal shows reachability, not the cheapest weighted route or a guaranteed physical delivery path; road closures and edge weights would need a richer model. A disconnected depot would remain absent from this result and should not be described as unreachable globally without checking the intended direction.",
        "code": "from collections import deque\n\nroutes = {\"North\": [\"East\", \"West\"], \"East\": [\"South\"], \"West\": [\"South\"], \"South\": []}\nfrontier = deque([\"North\"])\nvisited = {\"North\"}\norder = []\nwhile frontier:\n    depot = frontier.popleft()\n    order.append(depot)\n    for neighbor in routes[depot]:\n        if neighbor not in visited:\n            visited.add(neighbor)\n            frontier.append(neighbor)\nprint(order)",
        "output": "['North', 'East', 'West', 'South']",
        "cost": "Building an adjacency list costs O(V + E) storage when all vertices are represented. BFS adds O(V) worst-case queue and visited storage and scans each stored edge once. For an undirected graph, store both directions or normalize the graph builder; otherwise the implementation silently becomes directed. Neighbor order controls the exact printed traversal order but not the set of reachable vertices. A missing adjacency entry should have an explicit policy instead of raising unexpectedly during a long-running traversal.",
        "mistakes": ["Do not call BFS a weighted shortest-path algorithm.", "Do not mark visited only after dequeueing when paths converge.", "Do not infer an undirected edge from a single stored direction."],
        "related": ["dsa/queue-fifo-deque-boundary", "dsa/disjoint-set-union-connectivity", "dsa/hash-set-membership-and-order"],
    },
    {
        "slug": "disjoint-set-union-connectivity",
        "title": "Disjoint sets: merge connectivity without tracing every path",
        "section": sections[5][0],
        "summary": "Union by size and path compression support near-constant amortized connectivity checks.",
        "definition": "A disjoint-set union structure partitions known elements into groups and supports find and union. Union by size attaches the smaller root under the larger; path compression shortens later find paths. Over a sequence of operations, amortized cost is O(alpha(n)) per operation, where alpha is the inverse Ackermann function and grows extremely slowly. The structure answers whether two elements are in the same component. It does not recover the actual path between them, represent directed reachability, or automatically remove an edge. The element universe and behavior for an unknown ID must be defined by the caller.",
        "case": "A warehouse network has sites 0 through 3. Repairs open links 0-1 and 2-3, leaving two components. When link 1-2 opens, all four sites share a component. A connectivity dashboard can answer whether 0 and 3 are connected without walking the route map each time. If a link later closes, this DSU cannot split the group; the application must rebuild from active links or use a more complex changing-link connectivity method. This matters in operational dashboards where links can both appear and disappear.",
        "code": "parent = list(range(4))\nsize = [1] * 4\n\ndef find(site):\n    while parent[site] != site:\n        parent[site] = parent[parent[site]]\n        site = parent[site]\n    return site\n\ndef connect(left, right):\n    left_root, right_root = find(left), find(right)\n    if left_root == right_root:\n        return\n    if size[left_root] < size[right_root]:\n        left_root, right_root = right_root, left_root\n    parent[right_root] = left_root\n    size[left_root] += size[right_root]\n\nconnect(0, 1)\nconnect(2, 3)\nprint(find(0) == find(3))\nconnect(1, 2)\nprint(find(0) == find(3))",
        "output": "False\nTrue",
        "cost": "Initialization uses O(n) time and space for n sites. Union and find have near-constant amortized behavior with both optimizations, but a single operation's exact path length is not literally constant. The sample uses fixed integer IDs and mutates parent links; a production wrapper should validate ID bounds. Do not use this representation alone when a caller needs a route or a historical answer at an earlier edge version. Keep active-link revision with the DSU snapshot to avoid claiming current connectivity from stale unions.",
        "mistakes": ["Do not use DSU to answer directed reachability.", "Do not expect union to support removing an edge.", "Do not infer an actual route from a shared root."],
        "related": ["dsa/graph-adjacency-list-and-bfs", "dsa/hash-map-collision-and-load-contract", "dsa/queue-fifo-deque-boundary"],
    },
    {
        "slug": "fenwick-tree-point-update-prefix-query",
        "title": "Fenwick trees: update points and query prefix totals",
        "section": sections[6][0],
        "summary": "Store partial sums at binary-indexed positions for O(log n) updates and queries.",
        "definition": "A Fenwick tree stores selected partial sums in a one-indexed array. Adding a delta at one position walks upward using the least significant set bit; querying a prefix walks downward using the same bit rule. Both operations cost O(log n) time and the structure uses O(n) space. A half-open range sum [left, right) is prefix(right) minus prefix(left). This is useful when values change between queries; a static prefix-sum table is simpler and faster per query when updates never occur. The index conversion between zero-based application positions and one-based internal positions must be explicit.",
        "case": "A depot tracks four daily counts: 47, 31, 26, and 58. The sum for days [1, 4) is 115. A late batch adds 3 to day index 2, so the same range becomes 118 without rebuilding all cumulative totals. The update is a delta, not a replacement value. A negative delta can correct an overcount, but the caller must determine whether negative final daily counts are valid for its business contract. The data structure handles arithmetic; it does not validate the meaning of a correction.",
        "code": "daily_scans = [47, 31, 26, 58]\nfenwick = [0] * (len(daily_scans) + 1)\n\ndef add(day_index, delta):\n    position = day_index + 1\n    while position < len(fenwick):\n        fenwick[position] += delta\n        position += position & -position\n\ndef prefix(end_exclusive):\n    total = 0\n    while end_exclusive:\n        total += fenwick[end_exclusive]\n        end_exclusive -= end_exclusive & -end_exclusive\n    return total\n\nfor day_index, scan_count in enumerate(daily_scans):\n    add(day_index, scan_count)\nprint(prefix(4) - prefix(1))\nadd(2, 3)\nprint(prefix(4) - prefix(1))",
        "output": "115\n118",
        "cost": "The shown build uses n updates and costs O(n log n); a specialized linear construction can do O(n). Each later point update and prefix query costs O(log n), with O(n) stored numbers. Validate 0 <= day_index < n and 0 <= end_exclusive <= n in a public API. Passing an invalid negative index into bit arithmetic can make a loop fail to progress. If the operation changes from sum to minimum, this additive update formula no longer applies directly.",
        "mistakes": ["Do not pass a replacement value where the method expects a delta.", "Do not mix zero-based input positions with one-based internal indices.", "Do not reuse the sum implementation for arbitrary noninvertible operations."],
        "related": ["dsa/prefix-sum-range-query-contract", "dsa/segment-tree-range-sum-update", "dsa/resizable-array-growth-and-insert-cost"],
    },
    {
        "slug": "segment-tree-range-sum-update",
        "title": "Segment trees: combine child ranges after updates",
        "section": sections[6][0],
        "summary": "Tree nodes summarize intervals, supporting point updates and range queries.",
        "definition": "A segment tree stores an aggregate for each interval in a binary partition of an array. For sums, each internal node equals the sum of its children. A point update changes one leaf and recomputes its ancestors; a half-open range query combines only nodes intersecting the requested interval. Both cost O(log n), while building takes O(n) and storage is O(n). The same shape can support other associative aggregates with an identity value, but the combine operation and update contract must match. Lazy propagation is a separate extension for efficient updates over whole ranges.",
        "case": "A maintenance dashboard starts with job counts 47, 31, 26, and 58. The range [1, 4) totals 115. A corrected day index 2 becomes 29, so the range is 118. The point-update method replaces the old value; unlike the Fenwick example's add method, it does not accept a delta. The root stores the total for all days, but a caller may query only the bounded window. If two writers update different days concurrently, the tree still needs synchronization to prevent lost parent recomputations.",
        "code": "job_counts = [47, 31, 26, 58]\nleaf_count = len(job_counts)\ntree = [0] * (2 * leaf_count)\ntree[leaf_count:] = job_counts\nfor position in range(leaf_count - 1, 0, -1):\n    tree[position] = tree[2 * position] + tree[2 * position + 1]\n\ndef range_sum(left, right):\n    left += leaf_count\n    right += leaf_count\n    total = 0\n    while left < right:\n        if left & 1:\n            total += tree[left]\n            left += 1\n        if right & 1:\n            right -= 1\n            total += tree[right]\n        left //= 2\n        right //= 2\n    return total\n\ndef replace(day_index, new_count):\n    position = leaf_count + day_index\n    tree[position] = new_count\n    while position > 1:\n        position //= 2\n        tree[position] = tree[2 * position] + tree[2 * position + 1]\n\nprint(range_sum(1, 4))\nreplace(2, 29)\nprint(range_sum(1, 4))",
        "output": "115\n118",
        "cost": "The iterative array uses 2n slots for n positive-length inputs and builds in O(n) time. Queries and point replacements touch O(log n) nodes. A production wrapper must reject empty input or define its identity-only tree and validate 0 <= left <= right <= n. This storage layout works for a non-power-of-two n because parent sums still cover the corresponding leaves under the iterative query algorithm. Choose a simpler prefix array when data is immutable; a more complex tree is justified by repeated updates.",
        "mistakes": ["Do not confuse replace with add-delta semantics.", "Do not query outside the half-open array bounds.", "Do not claim this point-update tree already supports range updates."],
        "related": ["dsa/fenwick-tree-point-update-prefix-query", "dsa/prefix-sum-range-query-contract", "dsa/binary-search-tree-order-invariant"],
    },
]

lesson_paths = ["dsa/" + lesson["slug"] for lesson in lessons]
project_paths = ["dsa/dispatch-board-structure-selection-project", "dsa/depot-network-range-audit-project"]
quiz_paths = ["quizzes/dsa-linear-hash-decisions", "quizzes/dsa-tree-graph-range-decisions"]
new_section_paths = [path for path, _, _ in sections if path not in by_path]
assert not set(lesson_paths + project_paths + quiz_paths + new_section_paths).intersection(by_path)

titles = {entry["path"]: entry["title"] for entry in entries}
titles.update({path: title for path, title, _ in sections})
titles.update({path: lesson["title"] for path, lesson in zip(lesson_paths, lessons)})
titles.update({project_paths[0]: "Project: choose structures for a dispatch board", project_paths[1]: "Project: audit depot connectivity and daily ranges"})
titles.update({quiz_paths[0]: "Linear and hash structure decisions", quiz_paths[1]: "Tree, graph, and range structure decisions"})


def link(path):
    assert path in titles, path
    return f'<a href="/{html.escape(path)}">{html.escape(titles[path])}</a>'


def links(paths):
    return "<ul>" + "".join(f"<li>{link(path)}</li>" for path in dict.fromkeys(paths)) + "</ul>"


def related(paths):
    return [{"path": path, "title": titles[path]} for path in dict.fromkeys(paths)]


def new_entry(path, title, summary, body, section, order, kind="tutorial"):
    entry = copy.deepcopy(by_path["prompt-engineering/evaluation-slice-design"])
    entry.update(id=str(uuid.uuid5(uuid.NAMESPACE_URL, "aitrove:" + path)), path=path,
                 title=title, summary=summary, body=body, subject="dsa", difficulty="Intermediate",
                 tags=["data structures", section.split("/")[-1]], sort_order=40100 + order,
                 status="published", published_at=stamp, created_at=stamp, updated_at=stamp)
    entry["data"].update(kind=kind, reading_minutes=9 if kind == "tutorial" else 16,
                         author_path="authors/aitrove-editorial", subject_root=root_path,
                         section_path=section, content_format="html", seo_ready=True)
    return entry


new_rows = []
for position, (path, lesson) in enumerate(zip(lesson_paths, lessons)):
    section = lesson["section"]
    section_peers = [peer for peer, other in zip(lesson_paths, lessons) if other["section"] == section and peer != path]
    quiz = quiz_paths[0] if position < 9 else quiz_paths[1]
    connections = [section, root_path] + lesson["related"] + section_peers + project_paths + [quiz]
    body = ("<p>" + html.escape(lesson["definition"]) + "</p>"
            + "<h2>Operational case</h2><p>" + html.escape(lesson["case"]) + "</p>"
            + '<h2>Working Python program</h2><pre><code class="language-python">' + html.escape(lesson["code"], quote=False) + "</code></pre>"
            + '<h3>Output</h3><pre><code class="language-text">' + html.escape(lesson["output"], quote=False) + "</code></pre>"
            + "<h2>Time, space, and tradeoff</h2><p>" + html.escape(lesson["cost"]) + "</p>"
            + "<h3>Common Mistakes</h3><ul>" + "".join("<li>" + html.escape(mistake) + "</li>" for mistake in lesson["mistakes"]) + "</ul>"
            + "<h2>Connected lessons</h2>" + links(connections))
    entry = new_entry(path, lesson["title"], lesson["summary"], body, section, position * 10)
    entry["data"]["related"] = related(connections)
    new_rows.append(entry)

project_specs = [
    {
        "path": project_paths[0],
        "title": titles[project_paths[0]],
        "summary": "Select a sequence, keyed index, FIFO queue, and priority schedule for a fictional dispatch board.",
        "body": "<p>Design the in-memory data structures for a fictional depot dispatch board. A display sequence records shipments S-47, S-52, and S-61. A keyed status index distinguishes North/S-47 from South/S-47. Pallets P-47, P-52, and P-61 leave in arrival order unless an explicit priority policy chooses a different job. The project asks for the data structure behind each operation, its invariant, and a cost statement. It does not claim durable delivery or user authorization from an in-memory container.</p><h2>Choose by operation</h2><p>Use a resizable array when indexed display reads dominate and middle inserts are rare. Use a scoped hash-map key for shipment status, not shipment ID alone. Use a deque for FIFO pallet pickup; use a heap of priority, arrival, and job ID when urgency overrides arrival order while ties remain fair. A doubly linked list only helps if a node reference is already known, such as through a separate map. A hash set can deduplicate event IDs, but the raw scan log remains available for audit.</p><h2>Verify behavior</h2><p>Insert S-58 into display position one and record the shift cost. Verify that North/S-47 and South/S-47 return different statuses. Pop P-47 first from the FIFO queue. For equal priority jobs J-52 and J-61, pop the earlier arrival first. State what happens on an empty queue, a duplicate event, and a backlog beyond the in-memory capacity. Do not imply that a local pop proves a remote worker completed the job.</p><pre><code class=\"language-text\">Sequence: S-47, S-58, S-52, S-61 after a middle insert.\nStatus keys: (north, S-47) and (south, S-47) are distinct.\nFIFO: P-47 leaves before P-52 and P-61.\nPriority tie: J-52 leaves before J-61 by arrival sequence.\nRelease check: no accidental cross-depot key collision.</code></pre><h2>Cost and review</h2><p>The array gives O(1) indexed reads and O(n) middle insertion. The hash map gives expected O(1) keyed lookup, while the deque gives O(1) endpoint operations. Heap push and pop cost O(log n). Every structure uses O(n) storage for n active records, and duplicate references across structures increase memory further. Review synchronization if one update touches the display list and status index together; a fast structure with inconsistent state is still incorrect.</p><h3>Common Mistakes</h3><ul><li>Do not use one shipment ID across tenants as a unique key.</li><li>Do not use list.pop(0) for a large FIFO backlog.</li><li>Do not promise a heap orders equal-priority jobs without a tie field.</li></ul>",
        "related": lesson_paths[:9] + [quiz_paths[0]],
    },
    {
        "path": project_paths[1],
        "title": titles[project_paths[1]],
        "summary": "Compare BFS, disjoint sets, prefix sums, and mutable range indexes under changing depot data.",
        "body": "<p>Review a fictional depot network and daily count dashboard. Sites North, East, West, and South form directed route edges. A breadth-first traversal from North visits East and West before South. A separate undirected connectivity view uses disjoint sets when links are added, but it cannot remove a link from an existing component. Daily counts 47, 31, 26, and 58 support a [1, 4) sum of 115; a correction of +3 to day index two changes it to 118. The project keeps route reachability, undirected grouping, and arithmetic ranges as distinct questions.</p><h2>Select the correct representation</h2><p>Use an adjacency list and BFS for reachability from a start site. Mark neighbors when enqueueing. Use DSU for repeated component checks while links only appear; rebuild or choose another method when deletions matter. Use a prefix-sum array for immutable reporting snapshots. Use a Fenwick tree for point deltas and prefix sums or a segment tree for point replacements and chosen associative range aggregates. Record which operation accepts a delta and which accepts a replacement.</p><h2>Test the edge conditions</h2><p>Add a disconnected site and confirm BFS omits it without claiming no other route exists from a different start. Close an undirected link and show why the old DSU snapshot must not be reused. Query empty interval [2, 2) and expect zero. Reject out-of-range day indices. Keep the revision of the daily data beside any cached prefix table. A wrong half-open bound can silently add a day's count and still produce a plausible report.</p><pre><code class=\"language-text\">Directed BFS from North: North, East, West, South.\nDSU: union-only connectivity; closing a link needs rebuild.\nDaily counts: [47, 31, 26, 58].\nRange [1, 4): 115; after index 2 gains 3: 118.\nEmpty [2, 2): 0; invalid bounds: reject.</code></pre><h2>Cost and review</h2><p>BFS costs O(V + E) time and storage for the route graph. DSU is near-constant amortized per union or find but cannot answer a path. Prefix sums build in O(n) and answer static ranges in O(1); Fenwick and segment trees update and query in O(log n). The dashboard should report which snapshot each result belongs to. A correct number under a stale revision is not an acceptable current answer.</p><h3>Common Mistakes</h3><ul><li>Do not use directed reachability and undirected connectivity interchangeably.</li><li>Do not apply a link deletion to DSU as if it could split a group.</li><li>Do not reuse a prefix table after a count correction.</li></ul>",
        "related": lesson_paths[9:] + [quiz_paths[1]],
    },
]
for project_index, project in enumerate(project_specs):
    connections = [sections[7][0], root_path] + project["related"]
    body = project["body"] + "<h2>Connected lessons</h2>" + links(connections)
    entry = new_entry(project["path"], project["title"], project["summary"], body,
                      sections[7][0], 220 + project_index * 10, kind="project")
    entry["data"]["related"] = related(connections)
    new_rows.append(entry)

quiz_specs = [
    (quiz_paths[0], lesson_paths[:9], project_paths[0], [
        ("What does a resizable array append cost?", "O(1) amortized, with occasional O(n) growth", "O(1) worst case on every append", "O(log n) always"),
        ("What does insertion at the front of a length-n array cost?", "O(n) shifts", "O(1) because the index is zero", "O(log n) search"),
        ("What is the sum of [1, 4) over 47, 31, 26, 58?", "115", "162", "104"),
        ("When is a static prefix table stale?", "After a source value changes", "After an O(1) query", "Only after an empty interval"),
        ("When is singly linked-list insertion O(1)?", "When the required insertion node is already known", "Whenever a value can be searched", "Only when the list is sorted"),
        ("What must a doubly linked list update on removal?", "Both neighboring links and any external index", "Only the removed node's value", "Only the head"),
        ("What does a stack pop first?", "The most recently pushed item", "The earliest pushed item", "The lowest priority item"),
        ("Which in-process Python container fits FIFO endpoint operations?", "collections.deque", "A list with repeated pop(0)", "A set"),
        ("What distinguishes empty from full when ring indices coincide?", "A count or other explicit state", "The tail index alone", "The stored value's truthiness"),
        ("What is a hash map's ordinary lookup bound?", "Expected O(1), with possible worse cases", "Guaranteed O(1) for every input", "O(log n) by tree height"),
        ("Why key shipment status by depot and ID?", "The same shipment ID may occur in multiple depots", "It sorts results automatically", "It removes authorization checks"),
        ("What does a hash set promise about report order?", "No stable sorted order", "Insertion order by contract", "Numeric order"),
    ]),
    (quiz_paths[1], lesson_paths[9:], project_paths[1], [
        ("What controls plain BST search time?", "Tree height h", "Always log n", "Only the root value"),
        ("What causes a plain BST to become a chain?", "An unfavorable insertion order without balancing", "A hash collision", "A heap tie"),
        ("What does a min-heap expose at its root?", "A minimum key", "A fully sorted sequence", "The most recently inserted item"),
        ("How can equal-priority jobs preserve arrival order?", "Include an arrival counter in each heap key", "Depend on payload names", "Sort the whole heap after every pop"),
        ("Why does a trie need a terminal marker?", "A prefix path is not necessarily a stored complete key", "To balance the tree", "To hash every child"),
        ("What is BFS time with adjacency lists?", "O(V + E)", "O(V squared) on every graph", "O(log V)"),
        ("When should BFS mark a newly found vertex visited?", "Before enqueueing it", "Only after all neighbors are processed", "Never when a queue exists"),
        ("What can union-find answer directly?", "Whether two elements share a component", "The exact directed route", "The effect of deleting any edge"),
        ("What does a Fenwick point update accept in this lesson?", "A delta", "A replacement without converting it", "A whole range assignment"),
        ("What does the segment-tree update accept here?", "A replacement value for one point", "A delta under the same API", "An arbitrary range assignment"),
        ("What is [1, 4) after day index two rises from 26 to 29?", "118", "115", "162"),
        ("When is a prefix array a better simple choice?", "When the data snapshot stays unchanged across many queries", "When every point changes between queries", "When links are directed"),
    ]),
]
for quiz_index, (quiz_path, selected, project_path, questions) in enumerate(quiz_specs):
    quiz_entry = copy.deepcopy(by_path["quizzes/prompt-engineering-memory-lifecycle"])
    quiz_entry.update(id=str(uuid.uuid5(uuid.NAMESPACE_URL, "aitrove:" + quiz_path)), path=quiz_path,
                      title=titles[quiz_path], summary="Test data-structure invariants, edge cases, and operation costs.",
                      body="<p>Select the operation contract supported by the stated structure and workload.</p><h2>Lessons</h2>" + links(selected) + "<h2>Project and sections</h2>" + links([project_path, sections[8][0], root_path]),
                      subject="dsa", tags=["data structures", "quiz"], sort_order=40400 + quiz_index * 10,
                      status="published", published_at=stamp, created_at=stamp, updated_at=stamp)
    quiz_entry["data"].update(subject_root=root_path, section_path=sections[8][0],
                              content_format="html", author_path="authors/aitrove-editorial",
                              seo_ready=True, duration_minutes=12, related=related(selected + [project_path]),
                              questions=[{"prompt": question,
                                          "options": ([correct, other_a, other_b][i % 3:] + [correct, other_a, other_b][:i % 3]),
                                          "answer": (-i) % 3,
                                          "explanation": "The stated operation and invariant determine this choice."}
                                         for i, (question, correct, other_a, other_b) in enumerate(questions)])
    new_rows.append(quiz_entry)

section_lessons = {path: [lesson_path for lesson_path, lesson in zip(lesson_paths, lessons) if lesson["section"] == path]
                   for path, _, _ in sections}
section_lessons[sections[7][0]] = project_paths
section_lessons[sections[8][0]] = quiz_paths

for section_index, (section_path, section_title, section_summary) in enumerate(sections):
    selected = section_lessons[section_path]
    section_entry = by_path.get(section_path) or copy.deepcopy(by_path["dsa/array-data-structure-guide"])
    section_entry.update(id=section_entry["id"] if section_path in by_path else str(uuid.uuid5(uuid.NAMESPACE_URL, "aitrove:" + section_path)),
                         path=section_path, title=section_title, summary=section_summary, body="<p>" + html.escape(section_summary) + " Work through the operation contract, runnable case, and cost before selecting the structure for a real workload.</p><h2>Lessons</h2>" + links(selected) + "<h2>Practice and next steps</h2>" + links(project_paths + quiz_paths + [root_path]),
                         subject="dsa", difficulty=None, tags=["data structures"], sort_order=40010 + section_index,
                         status="published", updated_at=stamp)
    section_entry["data"] = {"subject_root": root_path, "section_path": section_path,
                             "content_format": "html", "seo_ready": True, "resource_tabs": tabs,
                             "modules": [{"title": section_title, "summary": section_summary, "lessons": selected}]}
    if section_path not in by_path:
        section_entry["created_at"] = stamp
        section_entry["published_at"] = stamp
        new_rows.append(section_entry)

root_entry = by_path[root_path]
root_entry.update(title="Data Structures", summary="Choose storage and access patterns by invariants, time, space, and update workload.",
                  body="<p>A data structure defines which operations are cheap, which are costly, and which invariants must stay true after mutation. Start with the workload: indexed reads, ordered updates, keyed lookup, priority selection, connectivity, or repeated range queries. Then compare time, memory, and failure behavior rather than choosing by name alone.</p>" + "".join("<h2>" + html.escape(title) + "</h2><p>" + html.escape(summary) + "</p>" + links(section_lessons[path] + [path]) for path, title, summary in sections),
                  updated_at=stamp)
root_entry["data"] = {"subject_root": root_path, "section_path": root_path,
                      "content_format": "html", "seo_ready": True, "resource_tabs": tabs,
                      "modules": [{"title": title, "summary": summary, "lessons": section_lessons[path]}
                                  for path, title, summary in sections]}

def quick_sort_body():
    program = """def quick_sort(records):
    if len(records) < 2:
        return records[:]
    pivot = records[len(records) // 2][0]
    lower = [record for record in records if record[0] < pivot]
    equal = [record for record in records if record[0] == pivot]
    higher = [record for record in records if record[0] > pivot]
    return quick_sort(lower) + equal + quick_sort(higher)

shipment_priority = [(52, "S-52"), (47, "S-47"), (61, "S-61")]
print(quick_sort(shipment_priority))"""
    return (
        "<p>Quick sort partitions a sequence around a pivot and recursively orders the lower and higher partitions. Its average work is O(n log n), while consistently uneven partitions can make it O(n²). This article uses three partitions so the duplicate-key rule is explicit. It is an algorithm applied to indexed storage, not a separate container.</p>"
        "<h2>Operational case</h2><p>A dispatch board has shipment priorities 52, 47, and 61. It must display S-47, S-52, then S-61. The middle record supplies the first pivot; smaller records go left and larger records go right. Equal-priority records stay together in their input order in this particular implementation. A large already ordered feed may still create expensive partitions under a poor pivot rule, so a production system should measure the input shape and normally prefer the language's tested built-in sort for ordinary application code.</p>"
        '<h2>Working Python program</h2><pre><code class="language-python">' + html.escape(program, quote=False) + '</code></pre>'
        "<h3>Output</h3><pre><code class=\"language-text\">[(47, 'S-47'), (52, 'S-52'), (61, 'S-61')]</code></pre>"
        "<h2>Time, space, and tradeoff</h2><p>Each partition scans its current input. Balanced levels give O(n log n) time; a sequence of one-sided partitions gives O(n²) time and deep recursion. This version allocates new lists at every level, so it is easier to inspect but uses more memory than an in-place partition. The base case returns a copy rather than the caller's list, avoiding an alias surprise. Python's built-in stable sort is usually the safer application choice when the goal is simply ordered records; learning this implementation explains partition invariants and the worst-case boundary.</p>"
        "<h3>Common Mistakes</h3><ul><li>Do not call every pivot split balanced.</li><li>Do not claim this out-of-place version uses constant extra space.</li><li>Do not ignore the ordering requirement for equal-priority records.</li></ul>"
        '<h2>Connected lessons</h2><ul><li><a href="/dsa/array-data-structure-guide">Arrays</a></li><li><a href="/dsa/resizable-array-growth-and-insert-cost">Resizable arrays: account for growth and shifting</a></li><li><a href="/dsa/binary-search-tree-order-invariant">Binary search trees: preserve order through every branch</a></li><li><a href="/dsa/dsa-tutorial-learn-data-structures-and-algorithms">Data Structures</a></li></ul>'
    )


sort_entry = by_path["dsa/quick-sort-algorithm"]
sort_entry.update(body=quick_sort_body(),
                  summary="Three-way partitioning, duplicate handling, and the worst-case boundary.",
                  updated_at=stamp)
sort_entry["data"].update(subject_root=root_path, section_path=sections[0][0], content_format="html", seo_ready=True,
                          related=related([sections[0][0], lesson_paths[0], lesson_paths[9], root_path]))
by_path[sections[0][0]]["data"]["modules"][0]["lessons"].append(sort_entry["path"])
by_path[sections[0][0]]["body"] += "<h2>Sorting alongside arrays</h2>" + links([sort_entry["path"]])
root_entry["data"]["modules"][0]["lessons"].append(sort_entry["path"])

backlinks = {
    "python/python-lists": lesson_paths[0],
    "python/dictionaries": lesson_paths[7],
    "python/sets": lesson_paths[8],
    "python/counter-deque": lesson_paths[5],
    "python/heap-top-k": lesson_paths[10],
    "python/linked-list-reversal": lesson_paths[2],
    "java/arrays": lesson_paths[0],
    "java/hashmap": lesson_paths[7],
    "java/linkedlist": lesson_paths[2],
}
for old_path, new_path in backlinks.items():
    entry = by_path[old_path]
    entry["body"] += "<p><strong>Continue with:</strong> " + link(new_path) + ".</p>"
    entry["data"]["related"] = related([item["path"] for item in entry["data"].get("related", [])] + [new_path])
    entry["updated_at"] = stamp

entries.extend(new_rows)
FIXTURE.write_text(json.dumps(entries, ensure_ascii=False, indent=2) + "\n")
print(json.dumps({"lessons": len(lesson_paths), "projects": len(project_paths), "quizzes": len(quiz_paths),
                  "newSections": len(new_section_paths), "paths": lesson_paths + project_paths + quiz_paths}))
