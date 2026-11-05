"""Add a deeper, linked set of original Data Structures lessons."""

import copy
import datetime
import html
import json
import uuid
from pathlib import Path

root_dir = Path(__file__).resolve().parents[1]
fixture = root_dir / "src/data/fixtures.json"
entries = json.loads(fixture.read_text())
by_path = {entry["path"]: entry for entry in entries}
root_path = "dsa/dsa-tutorial-learn-data-structures-and-algorithms"
stamp = datetime.datetime.now(datetime.UTC).isoformat()

lessons = [
    {
        "path": "dsa/bloom-filter-membership-boundary",
        "title": "Bloom filters: reject absent keys without claiming exact membership",
        "section": "dsa/hash-tables",
        "summary": "A compact bit array can rule out membership but may report a false positive.",
        "definition": "A Bloom filter maps each inserted key through several hash functions into a fixed bit array. A lookup returning a zero at any required bit proves the key was not inserted into that filter. A lookup finding all bits set means only that the key may have been inserted. With no deletions and correct hashing, ordinary insertion does not create false negatives; collisions can create false positives. As more keys arrive, the false-positive rate rises unless capacity was planned or the filter is rebuilt. The filter is an advisory precheck, not the authoritative record store.",
        "case": "A warehouse keeps an authoritative shipment index and uses a small filter to avoid costly index reads for IDs definitely absent. IDs S-47 and S-61 are inserted. A lookup for S-47 returns possible and must still query the index. A lookup for a key whose required bit is zero can skip the index. The filter must be populated from the same accepted-write stream as the index; if a shipment reaches the index but its bit update is missed, the no-false-negative promise no longer holds for the system. Deleting a shipment cannot simply clear its bits because other IDs may share them.",
        "code": "from hashlib import sha256\n\nbit_count = 128\nfilter_bits = 0\n\ndef positions(shipment_id):\n    for salt in (\"route-a\", \"route-b\", \"route-c\"):\n        digest = sha256(f\"{salt}:{shipment_id}\".encode()).digest()\n        yield int.from_bytes(digest[:8], \"big\") % bit_count\n\ndef record(shipment_id):\n    global filter_bits\n    for position in positions(shipment_id):\n        filter_bits |= 1 << position\n\ndef possibly_recorded(shipment_id):\n    return all(filter_bits & (1 << position) for position in positions(shipment_id))\n\nrecord(\"S-47\")\nrecord(\"S-61\")\nprint(possibly_recorded(\"S-47\"), possibly_recorded(\"S-52\"))",
        "output": "True False",
        "cost": "With k hash positions, insertion and lookup each take O(k) hash work and the bit array uses O(m) bits for m positions. This Python integer is a teaching representation; its allocation is implementation-specific and digest computation dominates the tiny trace. A deployed filter needs capacity and acceptable false-positive targets, a stable hash scheme across rebuilds, and an atomic ordering between authoritative writes and filter updates. A false positive wastes a lookup. A false negative caused by an out-of-sync system can hide an existing record, so correctness depends on the integration path as well as the data structure.",
        "mistakes": ["Do not treat a positive filter response as proof that a record exists.", "Do not clear shared bits on ordinary deletion.", "Do not promise no false negatives after a missed filter update."],
        "related": ["dsa/hash-set-membership-and-order", "dsa/hash-map-collision-and-load-contract", "dsa/lru-cache-eviction-invariant"],
    },
    {
        "path": "dsa/sparse-set-bounded-identifiers",
        "title": "Sparse sets: constant-time membership for bounded integer IDs",
        "section": "dsa/hash-tables",
        "summary": "Use a dense member array and a sparse position array when IDs have a known bound.",
        "definition": "A sparse set stores active integer IDs in a dense array and maps each possible ID to a candidate dense index through a sparse array. Membership checks both that the candidate index falls inside the current dense length and that the dense value at that index matches the queried ID. That second comparison makes stale sparse entries harmless after clearing or swap deletion. Insert, membership, deletion, and clear are O(1) under a fixed bounded universe. Memory is O(U + n), where U is the possible ID range and n the active count, so this choice is poor when U is enormous and few IDs are active.",
        "case": "A gateway has device slots numbered 0 through 127. Slots 47, 61, and 52 are active. Removing 61 moves the last dense member, 52, into its place and changes 52's sparse position. The dense array is now 47, 52; an old sparse position for 61 may still exist, but the membership check rejects it because that position no longer points to 61. The operation changes iteration order. If users need chronological order, store it separately rather than claiming this set preserves the order of activation.",
        "code": "slot_limit = 128\nsparse_position = [-1] * slot_limit\nactive_slots = []\n\ndef contains(slot_id):\n    position = sparse_position[slot_id]\n    return 0 <= position < len(active_slots) and active_slots[position] == slot_id\n\ndef activate(slot_id):\n    if not contains(slot_id):\n        sparse_position[slot_id] = len(active_slots)\n        active_slots.append(slot_id)\n\ndef deactivate(slot_id):\n    if not contains(slot_id):\n        return\n    position = sparse_position[slot_id]\n    last_slot = active_slots.pop()\n    if position < len(active_slots):\n        active_slots[position] = last_slot\n        sparse_position[last_slot] = position\n\nfor slot_id in (47, 61, 52):\n    activate(slot_id)\ndeactivate(61)\nprint(active_slots, contains(61), contains(52))",
        "output": "[47, 52] False True",
        "cost": "Each demonstrated operation touches a bounded number of array positions and takes O(1) time. Initializing sparse positions takes O(U) time and space, while active storage uses O(n). A clear operation can discard only the dense members in O(1) time if the membership check continues to compare dense values; old candidate positions must never be trusted alone. Public methods must reject negative or out-of-range IDs, since Python negative indices would otherwise address the wrong slot. The structure trades a fixed universe allocation for predictable membership operations.",
        "mistakes": ["Do not trust a sparse index without checking the dense value.", "Do not claim swap deletion preserves iteration order.", "Do not accept Python negative indices as valid device IDs."],
        "related": ["dsa/hash-set-membership-and-order", "dsa/resizable-array-growth-and-insert-cost", "dsa/ring-buffer-capacity-and-wrap"],
    },
    {
        "path": "dsa/skip-list-ordered-index",
        "title": "Skip lists: randomized levels over an ordered bottom chain",
        "section": "dsa/trees-and-heaps",
        "summary": "Promote some nodes to higher lanes so ordered searches skip long runs.",
        "definition": "A skip list keeps all keys in a sorted bottom lane and assigns some nodes additional forward pointers at higher lanes. Search starts high, moves right while the next key is smaller, and descends toward the target. Independent promotion choices give expected O(log n) search and insertion with O(n) expected pointers, while a rare unfavorable assignment can still require O(n) work. This small implementation fixes a maximum height for a bounded teaching input; a long-lived index must size or adapt the height ceiling for its expected key count. Duplicate-key behavior belongs in the API contract.",
        "case": "A depot stores ordered dock codes 19, 47, 52, 61, and 83. Search for 52 can skip over part of the bottom chain using promoted links. A later insertion of 58 must appear between 52 and 61 on the bottom lane while any promoted links also remain sorted. The seeded random generator makes the trace reproducible, but it does not make the structure deterministically balanced for arbitrary input. A sorted Python list may still be simpler for a small mostly read-only catalog, because skip-list nodes carry pointer overhead.",
        "code": "from random import Random\n\nclass DockNode:\n    def __init__(self, dock_key, height):\n        self.dock_key = dock_key\n        self.forward = [None] * height\n\nmax_height = 16\nhead = DockNode(-1, max_height)\ncoin = Random(47)\n\ndef locate(dock_key):\n    current = head\n    predecessors = [head] * max_height\n    for level in range(max_height - 1, -1, -1):\n        while current.forward[level] and current.forward[level].dock_key < dock_key:\n            current = current.forward[level]\n        predecessors[level] = current\n    return predecessors\n\ndef insert(dock_key):\n    predecessors = locate(dock_key)\n    next_node = predecessors[0].forward[0]\n    if next_node and next_node.dock_key == dock_key:\n        return\n    height = 1\n    while height < max_height and coin.random() < 0.5:\n        height += 1\n    new_node = DockNode(dock_key, height)\n    for level in range(height):\n        new_node.forward[level] = predecessors[level].forward[level]\n        predecessors[level].forward[level] = new_node\n\nfor dock_key in (61, 19, 83, 47, 52, 58):\n    insert(dock_key)\nordered = []\ncurrent = head.forward[0]\nwhile current:\n    ordered.append(current.dock_key)\n    current = current.forward[0]\nprint(ordered)\nprint(locate(52)[0].forward[0].dock_key == 52)",
        "output": "[19, 47, 52, 58, 61, 83]\nTrue",
        "cost": "Search and insertion are expected O(log n) while the level cap is high enough for the stored population; the worst case remains O(n). The implementation allocates one node per key and as many forward references as that key's sampled height. It rejects duplicate keys by leaving the existing node unchanged. It does not implement deletion, concurrency, or persistence. The search path is an O(max_height) temporary array in this insertion implementation. A production index should state ordering of duplicate values, random-state ownership, and synchronization across pointer updates.",
        "mistakes": ["Do not describe expected logarithmic cost as a worst-case guarantee.", "Do not allow duplicate bottom-lane keys when lookup assumes uniqueness.", "Do not reuse this fixed height ceiling for an unbounded population without analysis."],
        "related": ["dsa/binary-search-tree-order-invariant", "dsa/avl-rotation-height-invariant", "dsa/singly-linked-list-head-tail-invariants"],
    },
    {
        "path": "dsa/bplus-leaf-split-range-index",
        "title": "B+ leaf pages: split full pages and keep range order",
        "section": "dsa/trees-and-heaps",
        "summary": "A bounded leaf-page model shows separator updates after an insertion split.",
        "definition": "A B+ tree keeps sorted entries in leaf pages and uses separator keys in internal pages to route searches. A range scan finds its first leaf and continues across ordered leaves. In a real implementation, page capacity, minimum occupancy, split propagation, parent pointers, and storage durability determine correctness. The program here models only a root with leaf pages: it inserts one key into a full leaf, splits that leaf, and adds a separator. It is not a complete B+ tree or a database index. The model isolates the boundary that a parent separator must match the first key of the new right page.",
        "case": "A depot index begins with leaves [19, 47] and [52, 61], each limited to two keys. Adding 58 targets the right leaf. That leaf becomes [52, 58, 61], exceeds capacity, and splits into [52] and [58, 61]. The root separators become 52 and 58. A half-open range [47, 61) returns 47, 52, and 58. The example does not cover duplicate keys, deletion, or a root that itself overflows; those are the next design steps before an implementation can serve live records.",
        "code": "from bisect import bisect_right, insort\n\nleaf_pages = [[19, 47], [52, 61]]\nseparators = [52]\npage_capacity = 2\n\ndef insert_bay(bay_key):\n    page_index = bisect_right(separators, bay_key)\n    page = leaf_pages[page_index]\n    insort(page, bay_key)\n    if len(page) > page_capacity:\n        split_at = len(page) // 2\n        right_page = page[split_at:]\n        leaf_pages[page_index] = page[:split_at]\n        leaf_pages.insert(page_index + 1, right_page)\n        separators.insert(page_index, right_page[0])\n\ninsert_bay(58)\nrange_keys = [bay_key for page in leaf_pages for bay_key in page if 47 <= bay_key < 61]\nprint(leaf_pages, separators)\nprint(range_keys)",
        "output": "[[19, 47], [52], [58, 61]] [52, 58]\n[47, 52, 58]",
        "cost": "Routing among this model's root separators costs O(log p) comparisons for p leaf pages. Python list insertion may shift O(p) leaf references and O(c) keys within a page of capacity c; the demonstration therefore does not have the I/O behavior of a page-oriented B+ tree. A real balanced B+ tree targets O(log fanout n) page visits for search or update plus scan work for returned entries, but split propagation and persistence require a complete implementation. Treat this fragment as an invariant exercise, not a replacement for a database index.",
        "mistakes": ["Do not claim the one-level model handles arbitrary tree height.", "Do not forget to update the parent separator after splitting a leaf.", "Do not equate Python list movement with storage-page I/O."],
        "related": ["dsa/binary-search-tree-order-invariant", "dsa/avl-rotation-height-invariant", "dsa/sparse-table-immutable-range-minimum"],
    },
    {
        "path": "dsa/persistent-segment-tree-versioned-sums",
        "title": "Persistent segment trees: retain old range-sum versions",
        "section": "dsa/range-query-structures",
        "summary": "Copy only the changed root-to-leaf path when a point value changes.",
        "definition": "A persistent segment tree keeps earlier roots usable after an update. For a point replacement, it creates new nodes along one root-to-leaf path and shares every untouched subtree with the prior version. The initial build takes O(n) time and space; each update takes O(log n) time and new nodes, and a range sum takes O(log n) time in this balanced tree. Version roots must be retained intentionally. This is persistence of data-structure versions, not crash durability or database transactions; storing Python objects in memory does not make them survive a process restart.",
        "case": "A warehouse freezes counts 47, 31, 26, and 58. Version zero reports 115 over [1, 4). A late correction replaces index two with 29; version one reports 118 for the same range, while version zero still reports 115. The old right and left subtrees not on the changed path can be shared. A report can therefore state which revision it used without copying the entire input on every correction. The application still needs ownership, storage, and publication rules for roots if audit history must survive restarts.",
        "code": "def build(counts, left, right):\n    if right - left == 1:\n        return (counts[left], None, None)\n    middle = (left + right) // 2\n    first = build(counts, left, middle)\n    second = build(counts, middle, right)\n    return (first[0] + second[0], first, second)\n\ndef replace(node, left, right, changed_index, new_count):\n    if right - left == 1:\n        return (new_count, None, None)\n    middle = (left + right) // 2\n    first, second = node[1], node[2]\n    if changed_index < middle:\n        first = replace(first, left, middle, changed_index, new_count)\n    else:\n        second = replace(second, middle, right, changed_index, new_count)\n    return (first[0] + second[0], first, second)\n\ndef range_sum(node, left, right, query_left, query_right):\n    if query_right <= left or right <= query_left:\n        return 0\n    if query_left <= left and right <= query_right:\n        return node[0]\n    middle = (left + right) // 2\n    return range_sum(node[1], left, middle, query_left, query_right) + range_sum(node[2], middle, right, query_left, query_right)\n\ncounts = [47, 31, 26, 58]\nversion_zero = build(counts, 0, len(counts))\nversion_one = replace(version_zero, 0, len(counts), 2, 29)\nprint(range_sum(version_zero, 0, 4, 1, 4))\nprint(range_sum(version_one, 0, 4, 1, 4))\nprint(range_sum(version_zero, 0, 4, 1, 4))",
        "output": "115\n118\n115",
        "cost": "The example creates O(n) nodes in the first version and O(log n) additional nodes for each replacement. Queries use O(log n) time and O(log n) recursion stack in this implementation. With u retained updates, total node storage is O(n + u log n). Reject empty input, invalid point indices, and range bounds outside 0 <= left <= right <= n in a public wrapper. If no caller retains an old root, ordinary garbage collection may reclaim its unshared nodes. Retaining every root forever is a separate memory policy.",
        "mistakes": ["Do not mutate an old node while constructing a new version.", "Do not claim in-memory versions survive process failure.", "Do not retain unlimited roots without a memory policy."],
        "related": ["dsa/segment-tree-range-sum-update", "dsa/fenwick-tree-point-update-prefix-query", "dsa/sparse-table-immutable-range-minimum"],
    },
    {
        "path": "dsa/monotonic-deque-window-minimum",
        "title": "Monotonic deques: maintain a sliding minimum in linear time",
        "section": "dsa/stacks-and-queues",
        "summary": "Discard expired and dominated indices as a fixed window advances.",
        "definition": "A monotonic deque keeps candidate indices in increasing value order for a sliding-window minimum. When a new value arrives, remove older candidates from the back while their values are greater than or equal to it; they cannot become the minimum before the newer equal-or-smaller value expires. Remove indices from the front when they leave the window. The front then identifies the minimum. Each index enters and leaves at most once, so all windows together cost O(n) time and O(w) extra space for window width w. The tie rule here prefers the newer equal value.",
        "case": "A sensor receives delay readings 47, 31, 26, 58, 19, and 42. A three-reading window produces minima 26, 26, 19, and 19. A heap could also track candidate values but would need a stale-index policy and O(log w) insertion; rescanning each window costs O(nw). The deque's removal logic discards values that can never win a future window. If the window width changes on every request, precomputation and state ownership need a different contract.",
        "code": "from collections import deque\n\nreadings = [47, 31, 26, 58, 19, 42]\nwindow_width = 3\ncandidates = deque()\nminimums = []\nfor reading_index, delay in enumerate(readings):\n    while candidates and candidates[0] <= reading_index - window_width:\n        candidates.popleft()\n    while candidates and readings[candidates[-1]] >= delay:\n        candidates.pop()\n    candidates.append(reading_index)\n    if reading_index + 1 >= window_width:\n        minimums.append(readings[candidates[0]])\nprint(minimums)",
        "output": "[26, 26, 19, 19]",
        "cost": "The loop processes n readings and stores at most w candidate indices. Each index is appended once and removed at most once, giving O(n) total time despite the nested while loops. The result list itself needs O(n - w + 1) space. Validate 1 <= w <= n before running; zero width makes the expiration rule meaningless. If readings are corrected retroactively, this one-pass stream state cannot repair old emitted windows without replay or a separate indexed structure.",
        "mistakes": ["Do not mistake nested loops here for O(nw) total work.", "Do not store values alone when expiry requires their indices.", "Do not accept a zero-width window."],
        "related": ["dsa/queue-fifo-deque-boundary", "dsa/ring-buffer-capacity-and-wrap", "dsa/binary-heap-priority-scheduling"],
    },
]

assert all(lesson["path"] not in by_path for lesson in lessons)
for order, lesson in enumerate(lessons):
    path, section = lesson["path"], lesson["section"]
    related_paths = [section, root_path, *lesson["related"], "dsa/projects", "dsa/quizzes"]
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
                 body=body, sort_order=40500 + order * 10, created_at=stamp, updated_at=stamp, published_at=stamp)
    entry["data"].update(section_path=section, related=[{"path": related_path, "title": by_path[related_path]["title"]} for related_path in related_paths])
    entries.append(entry)
    by_path[path] = entry
    for hub_path in (section, root_path):
        hub = by_path[hub_path]
        module = hub["data"]["modules"][0] if hub_path == section else next(module for module in hub["data"]["modules"] if module["title"] == by_path[section]["title"])
        module["lessons"].append(path)
        hub["body"] += '<p><a href="/' + path + '">' + html.escape(lesson["title"]) + "</a></p>"
        hub["updated_at"] = stamp

fixture.write_text(json.dumps(entries, ensure_ascii=False, indent=2) + "\n")
print(json.dumps({"addedLessons": len(lessons), "paths": [lesson["path"] for lesson in lessons]}))
