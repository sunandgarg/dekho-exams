"""Add advanced, executable data-structure lessons to the existing DSA path."""

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
root = "dsa/dsa-tutorial-learn-data-structures-and-algorithms"
stamp = datetime.datetime.now(datetime.UTC).isoformat()

lessons = [
    {
        "path": "dsa/lru-cache-eviction-invariant",
        "title": "LRU caches: couple keyed lookup to recency order",
        "section": "dsa/hash-tables",
        "summary": "Bound a cache and move accessed keys to the newest end before eviction.",
        "definition": "A least-recently-used cache evicts the entry whose most recent access is oldest. It needs both keyed lookup and an order that changes on every hit. A hash map joined to a doubly linked list gives expected O(1) lookup, move, insertion, and eviction when each map value points directly to its list node. Python's OrderedDict packages that ordering behavior. Recency is a policy choice, not a measure of entry value or size. Reads that update recency are writes to shared cache state, so concurrency rules must cover them too.",
        "case": "An in-process route cache holds only two depot summaries. North and East are loaded. A request for North makes it newest; loading West then evicts East. The result depends on access order even when the stored summaries never change. A process restart clears this cache, and the origin remains authoritative. If a summary changes upstream, the cache needs expiry or explicit invalidation; LRU alone cannot prove freshness. The two-entry capacity is deliberately small so the eviction is visible.",
        "code": "from collections import OrderedDict\n\nroute_cache = OrderedDict()\ncapacity = 2\n\ndef read_or_load(depot, summary):\n    if depot in route_cache:\n        route_cache.move_to_end(depot)\n        return route_cache[depot]\n    route_cache[depot] = summary\n    if len(route_cache) > capacity:\n        route_cache.popitem(last=False)\n    return summary\n\nread_or_load(\"North\", 47)\nread_or_load(\"East\", 52)\nread_or_load(\"North\", 47)\nread_or_load(\"West\", 61)\nprint(list(route_cache.items()))",
        "output": "[('North', 47), ('West', 61)]",
        "cost": "For c cached keys, storage is O(c). OrderedDict endpoint and key operations are O(1) on average under ordinary hashing assumptions, while the oldest-key eviction is an endpoint operation. This demonstration passes a known summary to the loader; a production loader would call the origin only on a miss and would not trust a caller-supplied replacement for an existing key. Capacity counts entries rather than bytes, so a real cache with uneven object sizes may require weighted eviction. Define behavior for zero capacity before accepting requests.",
        "mistakes": ["Do not treat a hit as read-only when it changes recency.", "Do not assume LRU invalidates stale source data.", "Do not evict by insertion age when the contract says last access."],
        "related": ["dsa/hash-map-collision-and-load-contract", "dsa/doubly-linked-list-relink-and-ownership", "dsa/hash-set-membership-and-order"],
    },
    {
        "path": "dsa/avl-rotation-height-invariant",
        "title": "AVL trees: restore height balance after insertion",
        "section": "dsa/trees-and-heaps",
        "summary": "Track subtree heights and rotate when an insertion tilts a node beyond one level.",
        "definition": "An AVL tree is a binary search tree whose left and right subtree heights differ by at most one at every node. This balance condition keeps height O(log n), so lookup, insertion, and deletion each take O(log n) in the worst case. A rotation changes a few references while retaining in-order key order. Height metadata must be recomputed from children after every structural change. The demonstration isolates the left-left insertion case; a complete implementation must also handle right-right, left-right, and right-left cases and rebalance after deletion.",
        "case": "A depot index receives numeric bay keys 61, 52, then 47. An ordinary binary search tree forms a three-node left chain. Rotating right around 61 makes 52 the root, with 47 and 61 as children. The in-order sequence remains 47, 52, 61, which is the search invariant. The height difference at the new root becomes zero. For a large stream of monotonic bay IDs, the balance guarantee is the reason to choose a self-balancing tree rather than a plain tree whose height can grow linearly.",
        "code": "class BayNode:\n    def __init__(self, bay_key, left=None, right=None):\n        self.bay_key = bay_key\n        self.left = left\n        self.right = right\n        self.height = 1\n\ndef height(node):\n    return 0 if node is None else node.height\n\ndef refresh(node):\n    node.height = 1 + max(height(node.left), height(node.right))\n\ndef rotate_right(old_root):\n    new_root = old_root.left\n    old_root.left = new_root.right\n    new_root.right = old_root\n    refresh(old_root)\n    refresh(new_root)\n    return new_root\n\nroot = BayNode(61, BayNode(52, BayNode(47)))\nrefresh(root.left)\nrefresh(root)\nroot = rotate_right(root)\nprint(root.bay_key, root.left.bay_key, root.right.bay_key, root.height)",
        "output": "52 47 61 2",
        "cost": "The shown rotation changes a constant number of pointers and height fields, so the rotation itself costs O(1) time and O(1) extra space. Finding the insertion position and walking back through ancestors costs O(log n) when the AVL invariant already holds. The example constructs one known imbalance to expose the operation; it is not a complete insertion API. Deletion can trigger balance repair on multiple ancestors. Store heights consistently or a later operation may select the wrong rotation despite the tree looking correct locally.",
        "mistakes": ["Do not confuse one rotation example with a complete AVL implementation.", "Do not update parent height before recomputing its changed child.", "Do not lose the transferred subtree during a rotation."],
        "related": ["dsa/binary-search-tree-order-invariant", "dsa/binary-heap-priority-scheduling", "dsa/trie-prefix-index-and-terminal-flag"],
    },
    {
        "path": "dsa/csr-sparse-graph-storage",
        "title": "CSR graphs: pack sparse neighbors for repeated scans",
        "section": "dsa/graphs-and-disjoint-sets",
        "summary": "Store each vertex's edge slice using offsets and one flat neighbor array.",
        "definition": "Compressed sparse row storage represents a graph with a vertex-offset array and a flat neighbor array. Neighbors of vertex v occupy positions offsets[v] through offsets[v + 1]. Storage is O(V + E), as for adjacency lists, but contiguous edges can reduce object and pointer overhead during repeated scans. The tradeoff is mutation: inserting one new edge may require rebuilding the packed arrays or maintaining an overlay. Vertex IDs should be normalized to a dense integer range before building. An offset array of length V + 1 also represents isolated vertices without inventing empty edge objects.",
        "case": "A nightly route snapshot has four depots. North has edges to East and West; East has one edge to South; West and South have none. The offsets are 0, 2, 3, 3, 3, and the flat neighbors are 1, 2, 3. Reading North's slice yields 1 and 2, while West's equal adjacent offsets yield an empty slice. This representation fits a read-heavy snapshot. If a dispatcher adds a route during the day, keep a versioned delta or rebuild before calling the packed snapshot current.",
        "code": "depot_names = [\"North\", \"East\", \"West\", \"South\"]\nroute_rows = [[1, 2], [3], [], []]\noffsets = [0]\nneighbors = []\nfor route_row in route_rows:\n    neighbors.extend(route_row)\n    offsets.append(len(neighbors))\n\ndef outgoing(depot_id):\n    return [depot_names[neighbor_id] for neighbor_id in neighbors[offsets[depot_id]:offsets[depot_id + 1]]]\n\nprint(offsets)\nprint(outgoing(0), outgoing(2))",
        "output": "[0, 2, 3, 3, 3]\n['East', 'West'] []",
        "cost": "Building these arrays scans V rows and E edges, using O(V + E) time and space. Visiting every outgoing edge of one vertex costs O(outdegree), while direct membership testing within its slice is O(outdegree) unless neighbors are separately indexed or sorted for binary search. Python's integers and lists still carry object overhead; the physical memory advantage is more visible in typed packed arrays. Decide whether duplicate edges and self loops are allowed before producing the snapshot, because CSR preserves whatever the builder emits.",
        "mistakes": ["Do not assume CSR supports cheap arbitrary edge insertion.", "Do not forget the final offset for the last vertex.", "Do not claim a packed neighbor slice provides constant-time edge membership."],
        "related": ["dsa/graph-adjacency-list-and-bfs", "dsa/disjoint-set-union-connectivity", "dsa/resizable-array-growth-and-insert-cost"],
    },
    {
        "path": "dsa/sparse-table-immutable-range-minimum",
        "title": "Sparse tables: precompute immutable range minima",
        "section": "dsa/range-query-structures",
        "summary": "Use overlapping power-of-two blocks for constant-time minimum queries.",
        "definition": "A sparse table stores the minimum for every power-of-two block starting at each valid position. For a nonempty half-open range [left, right), two blocks of the largest fitting power cover the range, possibly overlapping. Minimum is idempotent, so overlapping elements do not affect the result. Build time and space are O(n log n), while each minimum query is O(1). This two-block method does not work unchanged for sums because overlapping elements would be counted twice. The source array must remain immutable or the precomputed blocks become stale.",
        "case": "A depot freezes six daily delay counts: 47, 31, 26, 58, 19, and 42. Its audit asks for the minimum over days [1, 5), which is 19. The query selects blocks covering indices 1 through 4; any overlap is harmless for minimum. If a late correction changes day 4, the table belongs to the old audit revision and cannot answer the new one. The immutable snapshot is a product decision as well as an algorithmic assumption. Use a segment tree if mixed point changes and range queries dominate.",
        "code": "daily_delay = [47, 31, 26, 58, 19, 42]\nminimum_blocks = [daily_delay[:]]\nblock_width = 2\nwhile block_width <= len(daily_delay):\n    half = block_width // 2\n    previous = minimum_blocks[-1]\n    minimum_blocks.append([min(previous[start], previous[start + half]) for start in range(len(daily_delay) - block_width + 1)])\n    block_width *= 2\n\ndef range_minimum(left, right):\n    length = right - left\n    level = length.bit_length() - 1\n    width = 1 << level\n    return min(minimum_blocks[level][left], minimum_blocks[level][right - width])\n\nprint(range_minimum(1, 5))\nprint(range_minimum(0, 3))",
        "output": "19\n26",
        "cost": "The build creates O(log n) levels, each with at most n values, so its time and storage are O(n log n). A query performs constant arithmetic and two table reads. Validate 0 <= left < right <= n; an empty range has no minimum without an application-defined identity. The sample uses Python integers and nested lists for clarity; a compact numeric array lowers storage overhead at large n. Rebuilding after every edit is costly, which is why this representation belongs to a frozen revision rather than a live counter.",
        "mistakes": ["Do not apply the overlapping-block shortcut to a non-idempotent sum.", "Do not query an empty minimum range without a stated result.", "Do not reuse a table after its source snapshot changes."],
        "related": ["dsa/prefix-sum-range-query-contract", "dsa/segment-tree-range-sum-update", "dsa/fenwick-tree-point-update-prefix-query"],
    },
]

assert all(lesson["path"] not in by_path for lesson in lessons)
for order, lesson in enumerate(lessons):
    section = lesson["section"]
    path = lesson["path"]
    connections = [section, root, *lesson["related"], "dsa/projects", "dsa/quizzes"]
    body = (
        "<p>" + html.escape(lesson["definition"]) + "</p>"
        + "<h2>Operational case</h2><p>" + html.escape(lesson["case"]) + "</p>"
        + '<h2>Working Python program</h2><pre><code class="language-python">' + html.escape(lesson["code"], quote=False) + "</code></pre>"
        + '<h3>Output</h3><pre><code class="language-text">' + html.escape(lesson["output"]) + "</code></pre>"
        + "<h2>Time, space, and tradeoff</h2><p>" + html.escape(lesson["cost"]) + "</p>"
        + "<h3>Common Mistakes</h3><ul>" + "".join("<li>" + html.escape(item) + "</li>" for item in lesson["mistakes"]) + "</ul>"
        + "<h2>Connected lessons</h2><ul>" + "".join('<li><a href="/' + related_path + '">' + html.escape(by_path[related_path]["title"]) + "</a></li>" for related_path in connections) + "</ul>"
    )
    entry = copy.deepcopy(by_path["dsa/fenwick-tree-point-update-prefix-query"])
    entry.update(id=str(uuid.uuid5(uuid.NAMESPACE_URL, "aitrove:" + path)), path=path, title=lesson["title"],
                 summary=lesson["summary"], body=body, sort_order=40300 + order * 10,
                 created_at=stamp, updated_at=stamp, published_at=stamp)
    entry["data"].update(section_path=section, related=[{"path": related_path, "title": by_path[related_path]["title"]} for related_path in connections])
    entries.append(entry)
    by_path[path] = entry
    for hub_path in (section, root):
        hub = by_path[hub_path]
        modules = hub["data"]["modules"]
        if hub_path == root:
            module = next(module for module in modules if module["title"] == by_path[section]["title"])
        else:
            module = modules[0]
        module["lessons"].append(path)
        hub["body"] += '<p><a href="/' + path + '">' + html.escape(lesson["title"]) + "</a></p>"
        hub["updated_at"] = stamp

FIXTURE.write_text(json.dumps(entries, ensure_ascii=False, indent=2) + "\n")
print(json.dumps({"addedAdvancedLessons": len(lessons), "paths": [lesson["path"] for lesson in lessons]}))
