"""Exercise the advanced DSA examples against independent small oracles."""

import contextlib
import copy
import bisect
import html
import heapq
import io
import json
import math
import random
import re
import tempfile
import threading
from collections import Counter, deque
from fractions import Fraction
from pathlib import Path

root = Path(__file__).resolve().parents[1]
entries = {entry["path"]: entry for entry in json.loads((root / "src/data/fixtures.json").read_text())}
checks = 0


def namespace(path):
    body = entries[path]["body"]
    block = re.search(r'<pre><code class="language-python">([\s\S]*?)</code></pre>', body)
    assert block, path
    program = html.unescape(block.group(1))
    scope = {}
    with contextlib.redirect_stdout(io.StringIO()):
        exec(program, scope)
    return scope, program


bloom, _ = namespace("dsa/bloom-filter-membership-boundary")
for shipment_number in range(70, 170):
    shipment_id = f"S-{shipment_number}"
    bloom["record"](shipment_id)
    assert bloom["possibly_recorded"](shipment_id)
    checks += 1

sparse, _ = namespace("dsa/sparse-set-bounded-identifiers")
expected_slots = set(sparse["active_slots"])
random_source = random.Random(503)
for _ in range(400):
    slot_id = random_source.randrange(128)
    if random_source.randrange(2):
        sparse["activate"](slot_id)
        expected_slots.add(slot_id)
    else:
        sparse["deactivate"](slot_id)
        expected_slots.discard(slot_id)
    assert set(sparse["active_slots"]) == expected_slots
    assert all(sparse["contains"](candidate) == (candidate in expected_slots) for candidate in range(128))
    checks += 1
sparse["active_slots"].clear()
assert not any(sparse["contains"](candidate) for candidate in range(128))
checks += 1

skip, _ = namespace("dsa/skip-list-ordered-index")
expected_keys = {19, 47, 52, 58, 61, 83}
for dock_key in random_source.sample(range(1, 360), 140):
    skip["insert"](dock_key)
    expected_keys.add(dock_key)
    current = skip["head"].forward[0]
    observed = []
    while current:
        observed.append(current.dock_key)
        current = current.forward[0]
    assert observed == sorted(expected_keys)
    checks += 1
assert all(skip["locate"](dock_key)[0].forward[0].dock_key == dock_key for dock_key in expected_keys)
checks += 1

pages, _ = namespace("dsa/bplus-leaf-split-range-index")
expected_bays = {19, 47, 52, 58, 61}
for bay_key in random_source.sample([key for key in range(1, 360) if key not in expected_bays], 100):
    pages["insert_bay"](bay_key)
    expected_bays.add(bay_key)
    assert [key for page in pages["leaf_pages"] for key in page] == sorted(expected_bays)
    assert pages["separators"] == [page[0] for page in pages["leaf_pages"][1:]]
    assert all(0 < len(page) <= pages["page_capacity"] for page in pages["leaf_pages"])
    checks += 1

persistent, _ = namespace("dsa/persistent-segment-tree-versioned-sums")
counts = [47, 31, 26, 58]
roots = [persistent["version_zero"]]
snapshots = [counts[:]]
for _ in range(70):
    index = random_source.randrange(4)
    replacement = random_source.randrange(80)
    counts[index] = replacement
    roots.append(persistent["replace"](roots[-1], 0, 4, index, replacement))
    snapshots.append(counts[:])
    for version in (0, len(roots) - 1, random_source.randrange(len(roots))):
        for left in range(5):
            for right in range(left, 5):
                assert persistent["range_sum"](roots[version], 0, 4, left, right) == sum(snapshots[version][left:right])
                checks += 1

_, window_program = namespace("dsa/monotonic-deque-window-minimum")
for _ in range(80):
    readings = [random_source.randrange(-30, 90) for _ in range(random_source.randrange(1, 25))]
    width = random_source.randrange(1, len(readings) + 1)
    variant = re.sub(r"^readings = .*$", f"readings = {readings!r}", window_program, count=1, flags=re.M)
    variant = re.sub(r"^window_width = .*$", f"window_width = {width}", variant, count=1, flags=re.M)
    scope = {}
    with contextlib.redirect_stdout(io.StringIO()):
        exec(variant, scope)
    assert scope["minimums"] == [min(readings[index:index + width]) for index in range(len(readings) - width + 1)]
    checks += 1

btree, _ = namespace("dsa/btree-page-split-insertion")
expected_btree = {19, 26, 47, 52, 58, 61, 83}
for bay_key in random_source.sample([key for key in range(1, 700) if key not in expected_btree], 220):
    btree["insert"](bay_key)
    expected_btree.add(bay_key)
    assert btree["ordered"](btree["root"]) == sorted(expected_btree)
    assert btree["contains"](btree["root"], bay_key)
    checks += 1


def audit_btree(page, depth=0, is_root=True):
    assert page.keys == sorted(set(page.keys))
    assert len(page.keys) <= 3
    if not is_root:
        assert len(page.keys) >= 1
    if page.leaf:
        assert not page.children
        return {depth}
    assert len(page.children) == len(page.keys) + 1
    depths = set()
    for child in page.children:
        depths.update(audit_btree(child, depth + 1, False))
    return depths


assert len(audit_btree(btree["root"])) == 1
checks += 1

interval, _ = namespace("dsa/interval-tree-max-endpoint-pruning")
windows = [(47, 61), (19, 26), (52, 58), (83, 91), (31, 42)]
interval_root = interval["root"]
for _ in range(120):
    start = random_source.randrange(0, 500)
    end = start + random_source.randrange(1, 30)
    windows.append((start, end))
    interval_root = interval["add_window"](interval_root, start, end)
for _ in range(350):
    low = random_source.randrange(0, 500)
    high = low + random_source.randrange(1, 35)
    found = interval["first_overlap"](interval_root, low, high)
    expected = any(start < high and low < end for start, end in windows)
    assert (found is not None) == expected
    if found is not None:
        assert found[0] < high and low < found[1]
    checks += 1

compressed, _ = namespace("dsa/compressed-trie-edge-splitting")
part_codes = {"dock47", "dock52", "doll61"}
for part_number in random_source.sample(range(100, 700), 180):
    part_code = f"part{part_number}"
    compressed["insert"](part_code)
    part_codes.add(part_code)
    assert compressed["contains"](part_code)
    checks += 1
assert all(compressed["contains"](part_code) for part_code in part_codes)
assert not compressed["contains"]("part")
checks += 1

redblack, _ = namespace("dsa/red-black-tree-invariant-audit")
valid_root = redblack["DeadlineNode"](52, "black", redblack["DeadlineNode"](47, "red"), redblack["DeadlineNode"](61, "red"))
assert redblack["black_height"](valid_root, float("-inf"), float("inf")) == 2
valid_root.right.color = "black"
try:
    redblack["black_height"](valid_root, float("-inf"), float("inf"))
except AssertionError:
    checks += 1
else:
    raise AssertionError("red-black audit accepted unequal black height")

redblack_insert, _ = namespace("dsa/red-black-ordered-insertion")
deadline_root = redblack_insert["deadline_root"]
deadline_keys = {19, 26, 47, 52, 58, 61, 83}
for deadline in random_source.sample(range(1, 1600), 500):
    deadline_root = redblack_insert["insert"](deadline_root, deadline)
    deadline_keys.add(deadline)
    assert redblack_insert["ordered"](deadline_root) == sorted(deadline_keys)
    assert not deadline_root.red
    assert redblack_insert["audit"](deadline_root, float("-inf"), float("inf")) > 0
    checks += 1

bplus_insert, _ = namespace("dsa/bplus-multilevel-insertion")
bay_root = bplus_insert["bay_root"]
bay_keys = {19, 26, 31, 47, 52, 58, 61, 67, 73, 83}


def audit_bplus(page, depth=0, is_root=True):
    assert page.keys == sorted(set(page.keys))
    assert len(page.keys) <= bplus_insert["maximum_keys"]
    if not is_root:
        assert page.keys
    if page.leaf:
        assert not page.children
        return depth, page.keys[0], page.keys[-1]
    assert len(page.children) == len(page.keys) + 1
    children = [audit_bplus(child, depth + 1, False) for child in page.children]
    assert len({child[0] for child in children}) == 1
    assert page.keys == [child[1] for child in children[1:]]
    assert all(left[2] < right[1] for left, right in zip(children, children[1:]))
    return children[0][0], children[0][1], children[-1][2]


for bay_key in random_source.sample([key for key in range(1, 1600) if key not in bay_keys], 500):
    bay_root = bplus_insert["insert"](bay_root, bay_key)
    bay_keys.add(bay_key)
    assert bplus_insert["ordered"](bay_root) == sorted(bay_keys)
    assert bplus_insert["contains"](bay_root, bay_key)
    audit_bplus(bay_root)
    checks += 1
assert not bplus_insert["contains"](bay_root, 1601)
checks += 1

avl_interval, _ = namespace("dsa/avl-interval-index-insertion")
window_root = avl_interval["window_root"]
windows = {(47, 61), (19, 26), (52, 58), (83, 91), (31, 42)}


def audit_avl_interval(node, lower=None, upper=None):
    if node is None:
        return 0, float("-inf")
    key = node.start, node.end
    assert lower is None or lower < key
    assert upper is None or key < upper
    left_height, left_end = audit_avl_interval(node.left, lower, key)
    right_height, right_end = audit_avl_interval(node.right, key, upper)
    assert node.height == 1 + max(left_height, right_height)
    assert abs(left_height - right_height) <= 1
    assert node.max_end == max(node.end, left_end, right_end)
    return node.height, node.max_end


for _ in range(300):
    start = random_source.randrange(0, 1800)
    end = start + random_source.randrange(1, 60)
    window_root = avl_interval["add_window"](window_root, start, end)
    windows.add((start, end))
    audit_avl_interval(window_root)
    checks += 1
for _ in range(500):
    low = random_source.randrange(0, 1800)
    high = low + random_source.randrange(1, 60)
    found = avl_interval["first_overlap"](window_root, low, high)
    assert (found is not None) == any(start < high and low < end for start, end in windows)
    if found is not None:
        assert found in windows and found[0] < high and low < found[1]
    checks += 1

trie_delete, _ = namespace("dsa/compressed-trie-deletion-and-merge")
part_codes = {"dock47", "doll61"}
for number in random_source.sample(range(100, 1500), 250):
    part_code = f"part{number}"
    trie_delete["insert"](part_code)
    part_codes.add(part_code)
    assert trie_delete["contains"](part_code)
    checks += 1
for part_code in random_source.sample(sorted(part_codes), 125):
    assert trie_delete["remove"](part_code)
    part_codes.remove(part_code)
    assert not trie_delete["contains"](part_code)
    assert not trie_delete["remove"](part_code)
    checks += 1
assert all(trie_delete["contains"](part_code) for part_code in part_codes)
checks += 1

bplus_delete, _ = namespace("dsa/bplus-deletion-borrow-merge")


def audit_bplus_delete(page, depth=0, is_root=True):
    assert page.keys == sorted(set(page.keys))
    assert len(page.keys) <= 3
    if page.leaf:
        assert not page.children
        if not is_root:
            assert len(page.keys) >= 2
        return depth, page.keys[0] if page.keys else None, page.keys[-1] if page.keys else None
    assert len(page.children) == len(page.keys) + 1
    assert len(page.children) >= 2
    children = [audit_bplus_delete(child, depth + 1, False) for child in page.children]
    assert len({child[0] for child in children}) == 1
    assert page.keys == [child[1] for child in children[1:]]
    assert all(left[2] < right[1] for left, right in zip(children, children[1:]))
    return children[0][0], children[0][1], children[-1][2]


for seed in range(8):
    sequence = random.Random(900 + seed).sample(range(1, 1100), 100)
    root_page = bplus_delete["BayPage"](True)
    remaining = set()
    for bay_key in sequence:
        root_page = bplus_delete["insert"](root_page, bay_key)
        remaining.add(bay_key)
        assert bplus_delete["ordered"](root_page) == sorted(remaining)
        audit_bplus_delete(root_page)
        checks += 1
    for bay_key in random.Random(1900 + seed).sample(sequence, len(sequence)):
        root_page, removed = bplus_delete["remove"](root_page, bay_key)
        assert removed
        remaining.remove(bay_key)
        assert bplus_delete["ordered"](root_page) == sorted(remaining)
        audit_bplus_delete(root_page)
        checks += 1
    assert root_page.leaf and root_page.keys == []
    checks += 1

indexed_heap, _ = namespace("dsa/indexed-binary-heap-decrease-key")
dispatch = indexed_heap["DispatchHeap"]()
priorities = {}
for number in range(240):
    job_id = f"J-{number}"
    priority = random_source.randrange(1000)
    dispatch.add(job_id, priority)
    priorities[job_id] = priority
    assert all(dispatch.position[item[1]] == index for index, item in enumerate(dispatch.items))
    checks += 1
for number in random_source.sample(range(240), 120):
    job_id = f"J-{number}"
    priority = random_source.randrange(priorities[job_id] + 1)
    dispatch.decrease(job_id, priority)
    priorities[job_id] = priority
    assert all(dispatch.position[item[1]] == index for index, item in enumerate(dispatch.items))
    assert all(dispatch.items[(index - 1) // 2] <= item for index, item in enumerate(dispatch.items) if index)
    checks += 1
while priorities:
    expected = min((priority, job_id) for job_id, priority in priorities.items())
    assert dispatch.pop() == expected
    del priorities[expected[1]]
    checks += 1

open_address, _ = namespace("dsa/open-addressing-tombstones-rehash")
for seed in range(12):
    directory = open_address["BayDirectory"]()
    owners = {}
    source = random.Random(3000 + seed)
    for _ in range(500):
        bay_id = source.randrange(220)
        action = source.randrange(3)
        if action == 0:
            owner = f"owner-{source.randrange(1000)}"
            directory.put(bay_id, owner)
            owners[bay_id] = owner
        elif action == 1:
            assert directory.remove(bay_id) == (bay_id in owners)
            owners.pop(bay_id, None)
        else:
            assert directory.lookup(bay_id) == ((True, owners[bay_id]) if bay_id in owners else (False, None))
        assert directory.live == len(owners)
        assert all(directory.lookup(key) == (True, value) for key, value in owners.items())
        checks += 1

topology, _ = namespace("dsa/dependency-graph-topological-order")
for seed in range(100):
    source = random.Random(4000 + seed)
    tasks = [f"task-{index}" for index in range(30)]
    requirements = {task: source.sample(tasks[:index], source.randrange(min(index, 5) + 1)) for index, task in enumerate(tasks)}
    result = topology["execution_order"](requirements)
    positions = {task: index for index, task in enumerate(result)}
    assert len(result) == len(tasks)
    assert all(positions[prerequisite] < positions[task] for task, prerequisites in requirements.items() for prerequisite in prerequisites)
    checks += 1
try:
    topology["execution_order"]({"receive": ["audit"], "audit": ["receive"]})
except ValueError:
    checks += 1
else:
    raise AssertionError("dependency cycle accepted")

redblack_delete, _ = namespace("dsa/red-black-ordered-deletion")
for seed in range(12):
    source = random.Random(5000 + seed)
    deadlines = source.sample(range(1, 1300), 100)
    deadline_root = None
    remaining = set()
    for deadline in deadlines:
        deadline_root = redblack_delete["insert"](deadline_root, deadline)
        remaining.add(deadline)
        assert redblack_delete["ordered"](deadline_root) == sorted(remaining)
        assert not deadline_root.red
        assert redblack_delete["audit"](deadline_root, float("-inf"), float("inf")) > 0
        checks += 1
    for deadline in source.sample(deadlines, len(deadlines)):
        deadline_root, removed = redblack_delete["remove"](deadline_root, deadline)
        assert removed
        remaining.remove(deadline)
        assert redblack_delete["ordered"](deadline_root) == sorted(remaining)
        assert deadline_root is None or (not deadline_root.red and redblack_delete["audit"](deadline_root, float("-inf"), float("inf")) > 0)
        checks += 1
    assert deadline_root is None
    checks += 1

avl_delete, _ = namespace("dsa/avl-interval-index-deletion")
for seed in range(12):
    source = random.Random(6000 + seed)
    windows = {(start, start + source.randrange(1, 50)) for start in source.sample(range(1, 1100), 100)}
    window_root = None
    for start, end in windows:
        window_root = avl_delete["add_window"](window_root, start, end)
        audit_avl_interval(window_root)
        checks += 1
    for start, end in source.sample(sorted(windows), len(windows)):
        window_root, removed = avl_delete["remove_window"](window_root, start, end)
        assert removed
        windows.remove((start, end))
        audit_avl_interval(window_root)
        low = source.randrange(0, 1100)
        high = low + source.randrange(1, 50)
        found = avl_delete["first_overlap"](window_root, low, high)
        assert (found is not None) == any(left < high and low < right for left, right in windows)
        checks += 1
    assert window_root is None
    checks += 1

rollback, _ = namespace("dsa/disjoint-set-rollback-checkpoints")
for seed in range(12):
    source = random.Random(7000 + seed)
    depots = [f"D-{number}" for number in range(20)]
    network = rollback["RollbackConnectivity"](depots)
    accepted_edges = []
    for _ in range(55):
        first, second = source.sample(depots, 2)
        if network.join(first, second):
            accepted_edges.append((first, second))
        if source.randrange(5) == 0:
            checkpoint = network.checkpoint()
            for _ in range(7):
                first, second = source.sample(depots, 2)
                network.join(first, second)
            network.rollback(checkpoint)
        for _ in range(8):
            first, second = source.sample(depots, 2)
            reached = {first}
            frontier = [first]
            for depot in frontier:
                for left, right in accepted_edges:
                    neighbor = right if depot == left else left if depot == right else None
                    if neighbor is not None and neighbor not in reached:
                        reached.add(neighbor)
                        frontier.append(neighbor)
            assert network.connected(first, second) == (second in reached)
            checks += 1

shortest, _ = namespace("dsa/stale-entry-heap-shortest-route")
for seed in range(50):
    source = random.Random(8000 + seed)
    depots = [f"D-{number}" for number in range(12)]
    roads = {depot: [] for depot in depots}
    for departure in depots:
        for arrival in depots:
            if departure != arrival and source.randrange(5) == 0:
                roads[departure].append((arrival, source.randrange(20)))
    origin = depots[0]
    distances = {depot: float("inf") for depot in depots}
    distances[origin] = 0
    for _ in range(len(depots) - 1):
        for departure, neighbors in roads.items():
            for arrival, travel_minutes in neighbors:
                distances[arrival] = min(distances[arrival], distances[departure] + travel_minutes)
    for destination in depots:
        result = shortest["shortest_route"](roads, origin, destination)
        assert (result is None) == (distances[destination] == float("inf"))
        if result:
            minutes, path = result
            assert minutes == distances[destination]
            assert path[0] == origin and path[-1] == destination
            assert minutes == sum(next(weight for neighbor, weight in roads[left] if neighbor == right) for left, right in zip(path, path[1:]))
        checks += 1

offline, _ = namespace("dsa/offline-connectivity-edge-lifetimes")
for seed in range(60):
    source = random.Random(9000 + seed)
    depots = [f"D-{number}" for number in range(7)]
    active_edges = set()
    events = []
    expected = []
    for _ in range(70):
        first, second = source.sample(depots, 2)
        edge = tuple(sorted((first, second)))
        action = source.randrange(3)
        if action == 0 and edge not in active_edges:
            active_edges.add(edge)
            events.append(("add", first, second))
        elif action == 1 and edge in active_edges:
            active_edges.remove(edge)
            events.append(("remove", first, second))
        else:
            events.append(("ask", first, second))
            reached = {first}
            frontier = [first]
            for depot in frontier:
                for left, right in active_edges:
                    neighbor = right if depot == left else left if depot == right else None
                    if neighbor is not None and neighbor not in reached:
                        reached.add(neighbor)
                        frontier.append(neighbor)
            expected.append(second in reached)
            checks += 1
    assert offline["answer_timeline"](depots, events) == expected
    checks += 1

closing, _ = namespace("dsa/bounded-queue-close-and-drain")
intake = closing["ClosingWorkQueue"](1)
intake.offer("J-47")
producer_result = []
producer_entered = threading.Event()


def blocked_producer():
    producer_entered.set()
    try:
        intake.offer("J-52")
    except closing["QueueClosed"]:
        producer_result.append("closed")


producer = threading.Thread(target=blocked_producer)
producer.start()
assert producer_entered.wait(1)
intake.close()
producer.join(1)
assert not producer.is_alive() and producer_result == ["closed"]
assert intake.take() == "J-47" and intake.take() is None
checks += 3

waiting = closing["ClosingWorkQueue"](1)
consumer_result = []
consumer_entered = threading.Event()


def blocked_consumer():
    consumer_entered.set()
    consumer_result.append(waiting.take())


consumer = threading.Thread(target=blocked_consumer)
consumer.start()
assert consumer_entered.wait(1)
waiting.close()
consumer.join(1)
assert not consumer.is_alive() and consumer_result == [None]
checks += 2

snapshot, _ = namespace("dsa/immutable-index-snapshot-publication")
store = snapshot["InventoryIndexStore"]({47: "north"}, {47: (19, 26)})
for number in range(100):
    before = store.read()
    bay_id = 100 + number
    after = store.publish(before.version, {bay_id: f"owner-{number}"}, (), {bay_id: (number, number + 7)})
    assert before.version + 1 == after.version
    assert bay_id not in before.bay_owners and bay_id in after.bay_owners
    assert set(after.repair_windows) <= set(after.bay_owners)
    checks += 1
try:
    store.publish(1, {}, (), {})
except ValueError:
    checks += 1
else:
    raise AssertionError("stale snapshot write accepted")
before = store.read()
try:
    store.publish(before.version, {}, (), {9999: (1, 2)})
except ValueError:
    assert store.read() is before
    checks += 1
else:
    raise AssertionError("orphan repair window accepted")

journal, _ = namespace("dsa/page-redo-journal-recovery-model")
for seed in range(60):
    source = random.Random(10000 + seed)
    log = journal["PageRedoJournal"]({"P-0": "original"})
    expected_pages = {"P-0": "original"}
    for _ in range(70):
        changes = {f"P-{source.randrange(12)}": f"v-{source.randrange(1000)}"}
        committed = bool(source.randrange(2))
        log.record(changes, commit=committed)
        if committed:
            expected_pages.update(changes)
        assert log.recover() == expected_pages
        checks += 1

online, _ = namespace("dsa/online-connectivity-after-edge-removal")
for seed in range(35):
    source = random.Random(11000 + seed)
    depots = [f"D-{number}" for number in range(10)]
    network = online["DepotNetwork"](depots)
    active_edges = set()
    for _ in range(100):
        first, second = source.sample(depots, 2)
        edge = tuple(sorted((first, second)))
        if edge in active_edges:
            network.disconnect(first, second)
            active_edges.remove(edge)
        else:
            network.connect(first, second)
            active_edges.add(edge)
        start, destination = source.sample(depots, 2)
        reached = {start}
        frontier = [start]
        for depot in frontier:
            for left, right in active_edges:
                adjacent = right if depot == left else left if depot == right else None
                if adjacent is not None and adjacent not in reached:
                    reached.add(adjacent)
                    frontier.append(adjacent)
        assert network.connected(start, destination) == (destination in reached)
        assert all((right in network.neighbors[left]) == ((left, right) in active_edges) for left in depots for right in depots if left < right)
        checks += 1

ordered_index, _ = namespace("dsa/persistent-ordered-index-path-copying")
for seed in range(12):
    source = random.Random(12000 + seed)
    priority_source = random.Random(13000 + seed)
    current_root = None
    current_entries = {}
    roots = [(current_root, current_entries.copy())]
    for _ in range(90):
        asset_id = source.randrange(140)
        if asset_id in current_entries and source.randrange(2):
            current_root = ordered_index["remove"](current_root, asset_id)
            del current_entries[asset_id]
        elif asset_id not in current_entries:
            owner = f"owner-{seed}-{asset_id}"
            current_root = ordered_index["put"](current_root, asset_id, owner, priority_source.getrandbits(63))
            current_entries[asset_id] = owner
        roots.append((current_root, current_entries.copy()))
        historical_root, historical_entries = source.choice(roots)
        assert ordered_index["ordered"](current_root) == sorted(current_entries.items())
        assert ordered_index["ordered"](historical_root) == sorted(historical_entries.items())

        def audit_treap(node, minimum=None, maximum=None):
            if node is None:
                return
            assert (minimum is None or minimum < node.asset_id) and (maximum is None or node.asset_id < maximum)
            if node.left:
                assert node.priority <= node.left.priority
            if node.right:
                assert node.priority <= node.right.priority
            audit_treap(node.left, minimum, node.asset_id)
            audit_treap(node.right, node.asset_id, maximum)

        audit_treap(current_root)
        checks += 1

framed, _ = namespace("dsa/framed-journal-torn-tail-recovery")
with tempfile.TemporaryDirectory() as temporary_directory:
    journal_path = Path(temporary_directory) / "test-pages.log"
    expected_pages = {}
    for sequence in range(36):
        changes = {f"P-{sequence % 9}": f"value-{sequence}"}
        framed["append_transaction"](journal_path, changes)
        expected_pages.update(changes)
    assert framed["recover"](journal_path) == expected_pages
    complete_size = journal_path.stat().st_size
    with open(journal_path, "ab") as log_file:
        log_file.write(framed["encode_transaction"]({"P-52": "torn"})[:13])
    assert framed["recover"](journal_path) == expected_pages
    assert journal_path.stat().st_size == complete_size
    checks += 3
    damaged = bytearray(journal_path.read_bytes())
    damaged[framed["HEADER"].size + 1] ^= 0x40
    journal_path.write_bytes(damaged)
    try:
        framed["recover"](journal_path)
    except ValueError:
        checks += 1
    else:
        raise AssertionError("full-frame checksum corruption was silently accepted")

cas, _ = namespace("dsa/cas-queue-link-help-and-reclamation")
schedule = cas["QueueSchedule"]()
stale_tail = schedule.tail_id
for job_number in range(150):
    schedule.offer(f"J-{job_number}")
assert not schedule.cas_link(stale_tail, None, 99999)
assert [schedule.take() for _ in range(150)] == [f"J-{job_number}" for job_number in range(150)]
assert schedule.take() is None
checks += 3

alerts, _ = namespace("dsa/aho-corasick-failure-linked-alert-index")
for seed in range(70):
    source = random.Random(14000 + seed)
    terms = set()
    while len(terms) < 8:
        terms.add("".join(source.choice("abc") for _ in range(source.randrange(1, 5))))
    index = alerts["AlertIndex"](sorted(terms))
    message = "".join(source.choice("abc") for _ in range(90))
    expected = sorted((start, term) for term in terms for start in range(len(message) - len(term) + 1) if message.startswith(term, start))
    assert sorted(index.scan(message)) == expected
    checks += 1

suffix, _ = namespace("dsa/suffix-array-lcp-incident-search")
for seed in range(70):
    source = random.Random(15000 + seed)
    message = "".join(source.choice("abc") for _ in range(source.randrange(1, 45)))
    index = suffix["IncidentTextIndex"](message)
    assert index.suffixes == sorted(range(len(message)), key=lambda start: message[start:])
    for rank, start in enumerate(index.suffixes):
        predecessor = index.suffixes[rank - 1] if rank else None
        shared = 0
        if predecessor is not None:
            while start + shared < len(message) and predecessor + shared < len(message) and message[start + shared] == message[predecessor + shared]:
                shared += 1
        assert index.lcp[rank] == shared
        checks += 1
    for _ in range(12):
        pattern = "".join(source.choice("abcd") for _ in range(source.randrange(1, 5)))
        expected = [start for start in range(len(message)) if message.startswith(pattern, start)]
        assert sorted(index.occurrences(pattern)) == expected
        checks += 1

spatial, _ = namespace("dsa/kd-tree-exact-nearest-depot")
for seed in range(70):
    source = random.Random(16000 + seed)
    points = [spatial["DepotPoint"](f"D-{number}", source.randrange(-80, 81), source.randrange(-80, 81)) for number in range(45)]
    index = spatial["build_spatial_index"](points)
    for _ in range(30):
        east, north = source.randrange(-90, 91), source.randrange(-90, 91)
        expected = min(((point.east - east) ** 2 + (point.north - north) ** 2, point.depot_id) for point in points)
        assert spatial["nearest"](index, east, north) == (expected[1], expected[0])
        checks += 1
assert spatial["nearest"](None, 47, 61) is None
checks += 1

sketch, _ = namespace("dsa/count-min-sketch-frequency-boundary")
for seed in range(60):
    source = random.Random(17000 + seed)
    approximate = sketch["EventCountSketch"](31, 4)
    exact = {}
    for _ in range(120):
        event_code = f"event-{source.randrange(80)}"
        amount = source.randrange(1, 5)
        approximate.record(event_code, amount)
        exact[event_code] = exact.get(event_code, 0) + amount
    assert all(approximate.estimate(code) >= count for code, count in exact.items())
    assert len(approximate.counters) == 4 and all(len(row) == 31 for row in approximate.counters)
    checks += 1
collision_sketch = sketch["EventCountSketch"](2, 1)
collision_sketch.record("recorded-event", 3)
assert any(collision_sketch.estimate(f"unseen-{number}") > 0 for number in range(100))
checks += 1

ring, _ = namespace("dsa/circular-linked-list-tail-invariant")
for seed in range(35):
    source = random.Random(18000 + seed)
    dispatch = ring["DispatchRing"]()
    expected = deque()
    for operation in range(170):
        choice = source.randrange(3)
        if choice == 0 or not expected:
            depot_id = f"D-{seed}-{operation}"
            dispatch.append(depot_id)
            expected.append(depot_id)
        elif choice == 1:
            dispatch.rotate_once()
            expected.rotate(-1)
        else:
            assert dispatch.remove_front() == expected.popleft()
        assert dispatch.length == len(expected)
        assert dispatch.snapshot() == list(expected)
        assert (dispatch.tail is None) == (not expected)
        if dispatch.tail:
            current = dispatch.tail.next
            for _ in range(dispatch.length):
                current = current.next
            assert current is dispatch.tail.next
        checks += 1

traversal, _ = namespace("dsa/iterative-binary-tree-traversal-orders")
for seed in range(55):
    source = random.Random(19000 + seed)
    nodes = [traversal["TaskNode"](f"T-{number}") for number in range(35)]
    available = [(nodes[0], "left"), (nodes[0], "right")]
    for node in nodes[1:]:
        slot = source.randrange(len(available))
        parent, side = available.pop(slot)
        setattr(parent, side, node)
        available.extend(((node, "left"), (node, "right")))

    def recursive_orders(node):
        if node is None:
            return [], [], []
        left_pre, left_in, left_post = recursive_orders(node.left)
        right_pre, right_in, right_post = recursive_orders(node.right)
        return ([node.task_id] + left_pre + right_pre,
                left_in + [node.task_id] + right_in,
                left_post + right_post + [node.task_id])

    expected_pre, expected_in, expected_post = recursive_orders(nodes[0])
    assert traversal["preorder"](nodes[0]) == expected_pre
    assert traversal["inorder"](nodes[0]) == expected_in
    assert traversal["postorder"](nodes[0]) == expected_post
    breadth = deque([nodes[0]])
    expected_level = []
    while breadth:
        task = breadth.popleft()
        expected_level.append(task.task_id)
        breadth.extend(child for child in (task.left, task.right) if child is not None)
    assert traversal["level_order"](nodes[0]) == expected_level
    checks += 1

bitgraph, _ = namespace("dsa/bitset-adjacency-matrix-dense-graph")
for seed in range(35):
    source = random.Random(20000 + seed)
    depots = [f"D-{number}" for number in range(18)]
    graph = bitgraph["DepotBitGraph"](depots)
    adjacency = {depot: set() for depot in depots}
    for _ in range(150):
        first, second = source.sample(depots, 2)
        if source.randrange(2):
            graph.connect(first, second)
            adjacency[first].add(second)
            adjacency[second].add(first)
        else:
            graph.disconnect(first, second)
            adjacency[first].discard(second)
            adjacency[second].discard(first)
        candidate, other = source.sample(depots, 2)
        assert graph.neighbors(candidate) == [depot for depot in depots if depot in adjacency[candidate]]
        assert graph.adjacent(candidate, other) == (other in adjacency[candidate])
        assert graph.common_neighbor_count(candidate, other) == len(adjacency[candidate] & adjacency[other])
        checks += 1

order_stats, _ = namespace("dsa/avl-subtree-size-rank-select")
for seed in range(25):
    source = random.Random(21000 + seed)
    root_node = None
    expected_keys = set()
    for _ in range(170):
        asset_id = source.randrange(260)
        if asset_id in expected_keys and source.randrange(2):
            root_node = order_stats["remove"](root_node, asset_id)
            expected_keys.remove(asset_id)
        elif asset_id not in expected_keys:
            root_node = order_stats["insert"](root_node, asset_id)
            expected_keys.add(asset_id)

        def audit_order_node(node, minimum=None, maximum=None):
            if node is None:
                return 0, 0
            assert (minimum is None or minimum < node.asset_id) and (maximum is None or node.asset_id < maximum)
            left_height, left_size = audit_order_node(node.left, minimum, node.asset_id)
            right_height, right_size = audit_order_node(node.right, node.asset_id, maximum)
            assert abs(left_height - right_height) <= 1
            assert node.height == 1 + max(left_height, right_height)
            assert node.size == 1 + left_size + right_size
            return node.height, node.size

        assert audit_order_node(root_node)[1] == len(expected_keys)
        ordered_keys = sorted(expected_keys)
        probe = source.randrange(260)
        assert order_stats["rank"](root_node, probe) == sum(key < probe for key in expected_keys)
        if ordered_keys:
            ordinal = source.randrange(len(ordered_keys))
            assert order_stats["select"](root_node, ordinal) == ordered_keys[ordinal]
        checks += 1

sparse_coordinates, _ = namespace("dsa/sparse-coordinate-segment-tree")
for seed in range(24):
    source = random.Random(22000 + seed)
    index = sparse_coordinates["SparseMeterIndex"](1 << 24)
    readings = {}
    for _ in range(130):
        position = source.randrange(1 << 24)
        replacement = source.randrange(-40, 80)
        index.assign(position, replacement)
        if replacement:
            readings[position] = replacement
        else:
            readings.pop(position, None)
        left = source.randrange(1 << 24)
        right = source.randrange(left, (1 << 24) + 1)
        assert index.sum_between(left, right) == sum(value for coordinate, value in readings.items() if left <= coordinate < right)
        assert index.root.total == sum(readings.values())
        checks += 2

wavelet, _ = namespace("dsa/wavelet-tree-subarray-order-statistics")
for seed in range(45):
    source = random.Random(23000 + seed)
    latencies = [source.randrange(-35, 80) for _ in range(source.randrange(1, 50))]
    index = wavelet["IncidentQuantiles"](latencies)
    for _ in range(55):
        start = source.randrange(len(latencies))
        stop = source.randrange(start + 1, len(latencies) + 1)
        threshold = source.randrange(-45, 90)
        ordinal = source.randrange(stop - start)
        assert index.count_below(start, stop, threshold) == sum(value < threshold for value in latencies[start:stop])
        assert index.select(start, stop, ordinal) == sorted(latencies[start:stop])[ordinal]
        checks += 2
    assert index.count_below(0, 0, 47) == 0
    checks += 1

parity, _ = namespace("dsa/parity-disjoint-set-constraints")
for seed in range(45):
    source = random.Random(24000 + seed)
    assets = [f"A-{number}" for number in range(15)]
    groups = parity["ParityGroups"](assets)
    edges = {asset: [] for asset in assets}

    def expected_relation(first, second):
        pending = deque([(first, 0)])
        seen = {first}
        while pending:
            current, relation = pending.popleft()
            if current == second:
                return relation
            for neighbor, edge_parity in edges[current]:
                if neighbor not in seen:
                    seen.add(neighbor)
                    pending.append((neighbor, relation ^ edge_parity))
        return None

    for _ in range(145):
        first, second = source.sample(assets, 2)
        required = source.randrange(2)
        implied = expected_relation(first, second)
        assert groups.constrain(first, second, bool(required)) == (implied is None or implied == required)
        if implied is None:
            edges[first].append((second, required))
            edges[second].append((first, required))
        probe_first, probe_second = source.sample(assets, 2)
        probe = expected_relation(probe_first, probe_second)
        expected = "unknown" if probe is None else "different" if probe else "same"
        assert groups.relationship(probe_first, probe_second) == expected
        checks += 2

implicit, _ = namespace("dsa/implicit-treap-range-reversal")
for seed in range(35):
    source = random.Random(25000 + seed)
    sequence = implicit["DispatchSequence"](seed + 67)
    expected = []
    for operation in range(160):
        if source.randrange(3) == 0 or not expected:
            position = source.randrange(len(expected) + 1)
            task_id = f"T-{seed}-{operation}"
            sequence.insert(position, task_id)
            expected.insert(position, task_id)
        else:
            start = source.randrange(len(expected) + 1)
            stop = source.randrange(start, len(expected) + 1)
            sequence.reverse(start, stop)
            expected[start:stop] = reversed(expected[start:stop])
        assert sequence.snapshot() == expected
        assert implicit["length"](sequence.root) == len(expected)
        checks += 2

bitmap, _ = namespace("dsa/bitvector-rank-select-superblocks")
for seed in range(45):
    source = random.Random(26000 + seed)
    flags = [bool(source.randrange(3) == 0) for _ in range(source.randrange(0, 190))]
    index = bitmap["IncidentBitmap"](flags)
    positions = [position for position, active in enumerate(flags) if active]
    for stop in range(len(flags) + 1):
        assert index.rank1(stop) == sum(flags[:stop])
        checks += 1
    for ordinal, position in enumerate(positions):
        assert index.select1(ordinal) == position
        checks += 1
    for invalid in (-1, len(positions)):
        try:
            index.select1(invalid)
        except IndexError:
            checks += 1
        else:
            raise AssertionError("invalid bitmap ordinal accepted")

hld, _ = namespace("dsa/heavy-light-tree-path-sums")
for seed in range(40):
    source = random.Random(27000 + seed)
    depots = [f"D-{number}" for number in range(28)]
    links = [(depots[number], depots[source.randrange(number)]) for number in range(1, len(depots))]
    adjacency = {depot: [] for depot in depots}
    for first, second in links:
        adjacency[first].append(second)
        adjacency[second].append(first)
    weights = {depot: source.randrange(-20, 80) for depot in depots}
    index = hld["DepotPathSums"](depots, links, weights)
    for _ in range(140):
        if source.randrange(3) == 0:
            depot = source.choice(depots)
            weights[depot] = source.randrange(-20, 80)
            index.update(depot, weights[depot])
        first, second = source.sample(depots, 2)
        pending = deque([(first, None, 0)])
        expected_sum = None
        while pending:
            current, parent, running = pending.popleft()
            running += weights[current]
            if current == second:
                expected_sum = running
                break
            pending.extend((neighbor, current, running) for neighbor in adjacency[current] if neighbor != parent)
        assert index.path_sum(first, second) == expected_sum
        checks += 1
    assert index.path_sum(depots[0], depots[0]) == weights[depots[0]]
    checks += 1

runs, _ = namespace("dsa/lsm-sorted-runs-tombstone-compaction")
for seed in range(45):
    source = random.Random(28000 + seed)
    index = runs["RunIndex"](flush_limit=source.randrange(2, 8))
    expected = {}
    keys = [f"A-{number}" for number in range(30)]
    for operation in range(190):
        asset_id = source.choice(keys)
        if source.randrange(4) == 0:
            index.delete(asset_id)
            expected.pop(asset_id, None)
        else:
            value = f"location-{seed}-{operation}"
            index.put(asset_id, value)
            expected[asset_id] = value
        if source.randrange(11) == 0:
            index.compact_all()
        assert all(index.get(key) == expected.get(key) for key in keys)
        assert all(list(run) == sorted(run) for run in index.runs)
        checks += 1

lazy, _ = namespace("dsa/lazy-segment-tree-range-add-minimum")
for seed in range(35):
    source = random.Random(29000 + seed)
    expected = [source.randrange(-45, 95) for _ in range(source.randrange(1, 55))]
    index = lazy["CapacityMinimums"](expected[:])
    for _ in range(175):
        start = source.randrange(len(expected))
        stop = source.randrange(start + 1, len(expected) + 1)
        if source.randrange(2):
            amount = source.randrange(-35, 36)
            index.add_between(start, stop, amount)
            for position in range(start, stop):
                expected[position] += amount
        assert index.minimum_between(start, stop) == min(expected[start:stop])
        assert index.minimum[1] == min(expected)
        checks += 2

lifting, _ = namespace("dsa/binary-lifting-lowest-common-ancestor")
for seed in range(35):
    source = random.Random(30000 + seed)
    employees = [f"E-{number}" for number in range(42)]
    parent = {employees[number]: employees[source.randrange(number)] for number in range(1, len(employees))}
    index = lifting["ReportingTree"](employees, parent)
    for _ in range(180):
        first, second = source.sample(employees, 2)
        first_path = [first]
        while first_path[-1] in parent:
            first_path.append(parent[first_path[-1]])
        second_path = [second]
        while second_path[-1] in parent:
            second_path.append(parent[second_path[-1]])
        common = next(employee for employee in first_path if employee in set(second_path))
        assert index.common_manager(first, second) == common
        generations = source.randrange(len(first_path) + 3)
        expected_ancestor = first_path[generations] if generations < len(first_path) else None
        assert index.ancestor(first, generations) == expected_ancestor
        checks += 2

grid, _ = namespace("dsa/two-dimensional-fenwick-rectangle-sums")
for seed in range(40):
    source = random.Random(31000 + seed)
    rows, columns = 7, 9
    index = grid["WarehouseGrid"](rows, columns)
    expected = [[0] * columns for _ in range(rows)]
    for _ in range(150):
        row, column = source.randrange(rows), source.randrange(columns)
        quantity = source.randrange(-25, 105)
        index.assign(row, column, quantity)
        expected[row][column] = quantity
        row_start = source.randrange(rows + 1)
        row_stop = source.randrange(row_start, rows + 1)
        column_start = source.randrange(columns + 1)
        column_stop = source.randrange(column_start, columns + 1)
        oracle = sum(expected[probe_row][probe_column]
                     for probe_row in range(row_start, row_stop)
                     for probe_column in range(column_start, column_stop))
        assert index.rectangle(row_start, row_stop, column_start, column_stop) == oracle
        assert index.prefix(rows, columns) == sum(map(sum, expected))
        checks += 2

robin, _ = namespace("dsa/robin-hood-hash-backward-shift-deletion")
for seed in range(55):
    source = random.Random(32000 + seed)
    index = robin["AssetSlotSet"](13)
    expected = set()
    candidates = [13 * number + number % 3 for number in range(45)]
    for _ in range(220):
        asset_id = source.choice(candidates)
        if source.randrange(2):
            if asset_id not in expected and len(expected) == index.capacity:
                try:
                    index.insert(asset_id)
                except OverflowError:
                    pass
                else:
                    raise AssertionError("full table accepted a distinct key")
            else:
                assert index.insert(asset_id) == (asset_id not in expected)
                expected.add(asset_id)
        else:
            assert index.remove(asset_id) == (asset_id in expected)
            expected.discard(asset_id)
        assert index.size == len(expected)
        assert {asset for asset in index.slots if asset is not None} == expected
        assert all(index.contains(candidate) == (candidate in expected) for candidate in candidates)
        checks += 3

forest_scope, _ = namespace("dsa/link-cut-forest-path-sums")
for seed in range(25):
    source = random.Random(33000 + seed)
    depot_ids = [f"D-{number}" for number in range(12)]
    weights = {depot_id: source.randrange(-30, 70) for depot_id in depot_ids}
    index = forest_scope["DepotForest"](weights)
    adjacency = {depot_id: set() for depot_id in depot_ids}
    edges = set()

    def path_between(first, second):
        frontier = deque([(first, [first])])
        seen = {first}
        while frontier:
            current, route = frontier.popleft()
            if current == second:
                return route
            for neighbor in adjacency[current] - seen:
                seen.add(neighbor)
                frontier.append((neighbor, route + [neighbor]))
        return None

    for _ in range(175):
        operation = source.randrange(4)
        first, second = source.sample(depot_ids, 2)
        if operation == 0 and path_between(first, second) is None:
            index.link(first, second)
            adjacency[first].add(second)
            adjacency[second].add(first)
            edges.add(frozenset((first, second)))
        elif operation == 1 and edges:
            edge = source.choice(tuple(edges))
            first, second = tuple(edge)
            index.cut(first, second)
            adjacency[first].remove(second)
            adjacency[second].remove(first)
            edges.remove(edge)
        elif operation == 2:
            weights[first] = source.randrange(-30, 70)
            index.update(first, weights[first])
        route = path_between(first, second)
        assert index.connected(first, second) == (route is not None)
        if route is not None:
            assert index.path_sum(first, second) == sum(weights[depot_id] for depot_id in route)
        checks += 2

automaton_scope, _ = namespace("dsa/suffix-automaton-online-substrings")
for seed in range(35):
    source = random.Random(34000 + seed)
    index = automaton_scope["IncidentTextAutomaton"]()
    incident_text = ""
    for _ in range(20):
        incident_text += source.choice("depot-")
        index.append(incident_text[-1])
        substrings = {incident_text[start:stop] for start in range(len(incident_text))
                      for stop in range(start + 1, len(incident_text) + 1)}
        assert index.distinct_substrings() == len(substrings)
        for _ in range(4):
            probe = "".join(source.choice("depot-x") for _ in range(source.randrange(7)))
            assert index.contains(probe) == (probe in incident_text)
        checks += 5

piece_scope, _ = namespace("dsa/piece-table-text-editing")
for seed in range(35):
    source = random.Random(35000 + seed)
    expected_note = "Depot cleared"
    note = piece_scope["IncidentNote"](expected_note)
    for _ in range(130):
        if source.randrange(2) or not expected_note:
            position = source.randrange(len(expected_note) + 1)
            fragment = "".join(source.choice("north 47-") for _ in range(source.randrange(6)))
            note.insert(position, fragment)
            expected_note = expected_note[:position] + fragment + expected_note[position:]
        else:
            start = source.randrange(len(expected_note) + 1)
            stop = source.randrange(start, len(expected_note) + 1)
            note.delete(start, stop)
            expected_note = expected_note[:start] + expected_note[stop:]
        assert note.text() == expected_note
        assert note.length == len(expected_note) == sum(piece.length for piece in note.pieces)
        checks += 2

cuckoo_scope, _ = namespace("dsa/cuckoo-hashing-relocation-rebuild")
for seed in range(30):
    source = random.Random(36000 + seed)
    index = cuckoo_scope["AssetCuckooSet"](4)
    expected = set()
    for _ in range(115):
        asset_id = source.randrange(100)
        if source.randrange(2):
            assert index.insert(asset_id) == (asset_id not in expected)
            expected.add(asset_id)
        else:
            assert index.remove(asset_id) == (asset_id in expected)
            expected.discard(asset_id)
        assert index.size == len(expected)
        assert {asset for table in index.tables for asset in table if asset is not None} == expected
        assert all(index.contains(candidate) == (candidate in expected) for candidate in range(100))
        checks += 4
grown = cuckoo_scope["AssetCuckooSet"](2)
for asset_id in range(27):
    assert grown.insert(asset_id)
assert grown.capacity > 2 and all(grown.contains(asset_id) for asset_id in range(27))
try:
    grown.insert(1 << 64)
except ValueError:
    pass
else:
    raise AssertionError("out-of-domain asset ID was accepted")
checks += 3

spatial_scope, _ = namespace("dsa/packed-r-tree-rectangle-intersection")
for seed in range(35):
    source = random.Random(37000 + seed)
    rectangles = []
    for number in range(70):
        west, south = source.randrange(-40, 40), source.randrange(-40, 40)
        rectangles.append((f"D-{number}", spatial_scope["Rectangle"](
            west, south, west + source.randrange(10), south + source.randrange(10))))
    index = spatial_scope["PackedDepotIndex"](rectangles, source.randrange(2, 7))
    for _ in range(65):
        west, south = source.randrange(-50, 50), source.randrange(-50, 50)
        query = spatial_scope["Rectangle"](west, south, west + source.randrange(19), south + source.randrange(19))
        assert index.search(query) == sorted(depot_id for depot_id, box in rectangles if box.intersects(query))
        checks += 1
empty_spatial = spatial_scope["PackedDepotIndex"]([])
assert empty_spatial.search(spatial_scope["Rectangle"](0, 0, 1, 1)) == []
touching_spatial = spatial_scope["PackedDepotIndex"]([("D-edge", spatial_scope["Rectangle"](1, 1, 3, 3))])
assert touching_spatial.search(spatial_scope["Rectangle"](3, 3, 5, 5)) == ["D-edge"]
checks += 2

fingerprint_scope, _ = namespace("dsa/binary-trie-maximum-xor-multiset")
for seed in range(35):
    source = random.Random(38000 + seed)
    index = fingerprint_scope["AssetFingerprintTrie"](9)
    expected = Counter()
    for _ in range(150):
        fingerprint = source.randrange(512)
        if source.randrange(2):
            index.add(fingerprint)
            expected[fingerprint] += 1
        elif expected[fingerprint]:
            index.remove(fingerprint)
            expected[fingerprint] -= 1
        assert index.count(fingerprint) == expected[fingerprint]
        live = [stored for stored, count in expected.items() if count]
        if live:
            query = source.randrange(512)
            partner, score = index.best_xor_partner(query)
            assert expected[partner] > 0 and score == max(query ^ stored for stored in live)
        checks += 2
empty_fingerprints = fingerprint_scope["AssetFingerprintTrie"](8)
try:
    empty_fingerprints.best_xor_partner(19)
except ValueError:
    pass
else:
    raise AssertionError("empty fingerprint index returned a partner")
empty_fingerprints.add(47)
empty_fingerprints.add(47)
empty_fingerprints.remove(47)
assert empty_fingerprints.count(47) == 1
empty_fingerprints.remove(47)
assert empty_fingerprints.count(47) == 0
checks += 3

range_scope, _ = namespace("dsa/fenwick-two-tree-range-add-sum")
for seed in range(35):
    source = random.Random(39000 + seed)
    expected = [source.randrange(-45, 80) for _ in range(source.randrange(46))]
    index = range_scope["CapacityRangeIndex"](expected[:])
    for _ in range(140):
        start = source.randrange(len(expected) + 1)
        stop = source.randrange(start, len(expected) + 1)
        if source.randrange(2):
            amount = source.randrange(-30, 31)
            index.add_between(start, stop, amount)
            for position in range(start, stop):
                expected[position] += amount
        assert index.sum_between(start, stop) == sum(expected[start:stop])
        prefix_stop = source.randrange(len(expected) + 1)
        assert index.sum_before(prefix_stop) == sum(expected[:prefix_stop])
        checks += 2

merkle_scope, _ = namespace("dsa/merkle-tree-indexed-inclusion-proof")
for seed in range(35):
    source = random.Random(40000 + seed)
    records = [f"scan-{seed}-{number}-{source.randrange(10000)}".encode()
               for number in range(source.randrange(1, 42))]
    tree = merkle_scope["ScanBatchTree"](records)
    for position, record in enumerate(records):
        proof = tree.proof(position)
        assert merkle_scope["verify_scan"](record, position, len(records), proof, tree.root)
        assert not merkle_scope["verify_scan"](record + b"!", position, len(records), proof, tree.root)
        assert not merkle_scope["verify_scan"](record, position, len(records) + 1, proof, tree.root)
        assert not merkle_scope["verify_scan"](record, position, len(records),
                                              proof + [("right", b"\x00" * 32)], tree.root)
        checks += 4

median_scope, _ = namespace("dsa/two-heap-running-median")
for seed in range(35):
    source = random.Random(41000 + seed)
    index = median_scope["ScanMedian"]()
    expected = []
    for _ in range(160):
        value = source.randrange(-1000, 1000)
        expected.append(value)
        index.record(value)
        ordered = sorted(expected)
        length = len(ordered)
        oracle = Fraction(ordered[length // 2]) if length & 1 else Fraction(
            ordered[length // 2 - 1] + ordered[length // 2], 2)
        assert index.median() == oracle
        assert len(index.lower) in (len(index.upper), len(index.upper) + 1)
        assert not index.upper or -index.lower[0] <= index.upper[0]
        checks += 3

block_scope, _ = namespace("dsa/square-root-block-range-sum")
threshold_scope, _ = namespace("dsa/merge-sort-tree-threshold-count")
disjoint_scope, _ = namespace("dsa/disjoint-sparse-table-range-sum")
line_scope, _ = namespace("dsa/li-chao-tree-line-minimum")
for seed in range(24):
    source = random.Random(52000 + seed)
    values = [source.randrange(-95, 140) for _ in range(source.randrange(0, 34))]
    blocks = block_scope["BlockCapacitySums"](values)
    thresholds = threshold_scope["ThresholdCountIndex"](values)
    disjoint = disjoint_scope["DisjointSumTable"](values)
    for _ in range(120):
        start = source.randrange(len(values) + 1)
        stop = source.randrange(start, len(values) + 1)
        threshold = source.randrange(-110, 150)
        assert blocks.sum_between(start, stop) == sum(values[start:stop])
        assert thresholds.count_at_most(start, stop, threshold) == sum(value <= threshold for value in values[start:stop])
        assert disjoint.sum_between(start, stop) == sum(values[start:stop])
        checks += 3
        if values and source.randrange(4) == 0:
            position = source.randrange(len(values))
            replacement = source.randrange(-95, 140)
            blocks.replace(position, replacement)
            assert blocks.values[position] == replacement
            checks += 1
            blocks.replace(position, values[position])
    if values:
        try:
            blocks.replace(len(values), 0)
            assert False, "out-of-range replacement accepted"
        except IndexError:
            checks += 1
for seed in range(32):
    source = random.Random(63000 + seed)
    left = source.randrange(-30, 0)
    right = source.randrange(0, 40)
    index = line_scope["LiChaoTariffs"](left, right)
    try:
        index.min_cost(left)
        assert False, "empty tariff book accepted"
    except ValueError:
        checks += 1
    lines = []
    for _ in range(18):
        line = line_scope["TariffLine"](source.randrange(-40, 41), source.randrange(-70, 90))
        lines.append(line)
        index.add_line(line)
        for point in range(left, right + 1):
            assert index.min_cost(point) == min(candidate.cost(point) for candidate in lines)
            checks += 1
    for point in (left - 1, right + 1):
        try:
            index.min_cost(point)
            assert False, "out-of-domain tariff query accepted"
        except IndexError:
            checks += 1

coordinate_scope, _ = namespace("dsa/coordinate-compression-ordered-ranks")
frequency_scope, _ = namespace("dsa/fenwick-order-statistic-multiset")
mo_scope, _ = namespace("dsa/mo-offline-distinct-range-counts")
grid_scope, _ = namespace("dsa/two-dimensional-prefix-grid-sums")
for seed in range(35):
    source = random.Random(74000 + seed)
    samples = [source.randrange(-120, 180) for _ in range(source.randrange(0, 60))]
    catalog = coordinate_scope["CoordinateRankCatalog"](samples)
    ordered_keys = sorted(set(samples))
    assert catalog.keys == ordered_keys
    checks += 1
    for rank, weight in enumerate(ordered_keys):
        assert catalog.rank(weight) == rank
        assert catalog.weight(rank) == weight
        checks += 2
    for threshold in range(-130, 190, 7):
        assert catalog.lower_bound(threshold) == sum(weight < threshold for weight in ordered_keys)
        checks += 1
    frequencies = frequency_scope["WeightOrderIndex"](ordered_keys)
    recorded = []
    for _ in range(95):
        if not ordered_keys:
            break
        weight = source.choice(ordered_keys)
        if weight in recorded and source.randrange(3) == 0:
            frequencies.change(weight, -1)
            recorded.remove(weight)
        else:
            frequencies.change(weight, 1)
            recorded.append(weight)
        sorted_recorded = sorted(recorded)
        assert frequencies.total == len(sorted_recorded)
        checks += 1
        if recorded:
            rank = source.randrange(1, len(recorded) + 1)
            assert frequencies.kth(rank) == sorted_recorded[rank - 1]
            checks += 1
        threshold = source.randrange(-130, 190)
        assert frequencies.count_below(threshold) == sum(weight < threshold for weight in recorded)
        checks += 1
for seed in range(50):
    source = random.Random(85000 + seed)
    scan_codes = [source.randrange(-9, 13) for _ in range(source.randrange(0, 45))]
    windows = []
    for _ in range(55):
        start = source.randrange(len(scan_codes) + 1)
        stop = source.randrange(start, len(scan_codes) + 1)
        windows.append((start, stop))
    actual = mo_scope["distinct_in_windows"](scan_codes, windows)
    assert actual == [len(set(scan_codes[start:stop])) for start, stop in windows]
    checks += len(windows)
for seed in range(35):
    source = random.Random(96000 + seed)
    rows = source.randrange(0, 12)
    columns = source.randrange(0, 12)
    values = [[source.randrange(-60, 95) for _ in range(columns)] for _ in range(rows)]
    grid = grid_scope["CapacityGridPrefix"](values)
    for _ in range(90):
        top = source.randrange(rows + 1)
        bottom = source.randrange(top, rows + 1)
        left = source.randrange(grid.columns + 1)
        right = source.randrange(left, grid.columns + 1)
        assert grid.rectangle_sum(top, left, bottom, right) == sum(sum(row[left:right]) for row in values[top:bottom])
        checks += 1

empty_frequencies = frequency_scope["WeightOrderIndex"]([])
try:
    empty_frequencies.kth(1)
    assert False, "empty multiset selected a key"
except IndexError:
    checks += 1
single_frequency = frequency_scope["WeightOrderIndex"]([47])
try:
    single_frequency.change(47, -1)
    assert False, "negative multiplicity accepted"
except ValueError:
    assert single_frequency.total == 0
    checks += 2
try:
    single_frequency.change(19, 1)
    assert False, "unknown catalog key accepted"
except KeyError:
    assert single_frequency.total == 0
    checks += 2
try:
    mo_scope["distinct_in_windows"]([47, 19], [(0, 3)])
    assert False, "out-of-bounds offline window accepted"
except IndexError:
    checks += 1
try:
    grid_scope["CapacityGridPrefix"]([[47, 19], [23]])
    assert False, "ragged grid accepted"
except ValueError:
    checks += 1
try:
    grid_scope["CapacityGridPrefix"]([[47, 19]]).rectangle_sum(0, 0, 2, 1)
    assert False, "out-of-bounds rectangle accepted"
except IndexError:
    checks += 1

posting_scope, _ = namespace("dsa/inverted-index-sorted-postings-intersection")
position_scope, _ = namespace("dsa/positional-inverted-index-phrase-matching")
trigram_scope, _ = namespace("dsa/trigram-index-verified-substring-candidates")
lexicon_scope, _ = namespace("dsa/front-coded-term-lexicon-blocks")
for seed in range(45):
    source = random.Random(107000 + seed)
    vocabulary = ["alarm", "brake", "coil", "depot", "engine", "fuse", "gauge"]
    documents = {100 + document_id * 7: [source.choice(vocabulary) for _ in range(source.randrange(0, 14))]
                 for document_id in range(source.randrange(0, 14))}
    postings = posting_scope["IncidentPostings"](documents)
    positions = position_scope["PositionalIncidentIndex"](documents)
    for _ in range(85):
        terms = [source.choice(vocabulary + ["missing"]) for _ in range(source.randrange(0, 5))]
        expected_all = sorted(document_id for document_id, tokens in documents.items()
                              if terms and all(term in tokens for term in terms))
        assert postings.containing_all(terms) == expected_all
        checks += 1
        phrase = [source.choice(vocabulary + ["missing"]) for _ in range(source.randrange(0, 5))]
        expected_phrase = sorted(document_id for document_id, tokens in documents.items()
                                 if phrase and any(tokens[start:start + len(phrase)] == phrase
                                                   for start in range(len(tokens) - len(phrase) + 1)))
        assert positions.phrase_documents(phrase) == expected_phrase
        checks += 1
for seed in range(40):
    source = random.Random(118000 + seed)
    alphabet = "abcd xyz"
    documents = {200 + document_id * 11: "".join(source.choice(alphabet) for _ in range(source.randrange(0, 45)))
                 for document_id in range(source.randrange(0, 15))}
    index = trigram_scope["TrigramIncidentIndex"](documents)
    for _ in range(90):
        if documents and source.randrange(2):
            text = source.choice(list(documents.values()))
            start = source.randrange(len(text) + 1)
            fragment = text[start:start + source.randrange(0, 9)]
        else:
            fragment = "".join(source.choice(alphabet) for _ in range(source.randrange(0, 9)))
        assert index.containing(fragment) == sorted(document_id for document_id, text in documents.items()
                                                   if fragment in text)
        checks += 1
for seed in range(40):
    source = random.Random(129000 + seed)
    alphabet = "abcdep"
    terms = ["".join(source.choice(alphabet) for _ in range(source.randrange(1, 14)))
             for _ in range(source.randrange(0, 75))]
    dictionary = lexicon_scope["FrontCodedIncidentTerms"](terms, block_size=source.randrange(1, 10))
    assert [term for block in range(len(dictionary.blocks)) for term in dictionary.block_terms(block)] == sorted(set(terms))
    checks += 1
    for term in terms + ["".join(source.choice(alphabet) for _ in range(source.randrange(0, 14))) for _ in range(30)]:
        assert dictionary.contains(term) == (term in terms)
        checks += 1

lfu_scope, _ = namespace("dsa/lfu-cache-frequency-and-recency-eviction")
expiry_scope, _ = namespace("dsa/ttl-heap-expiration-with-stale-records")
slots_scope, _ = namespace("dsa/generational-slot-map-stale-handle-rejection")
dary_scope, _ = namespace("dsa/dary-heap-stable-priority-dispatch")
for seed in range(32):
    source = random.Random(140000 + seed)
    capacity = source.randrange(0, 9)
    cache = lfu_scope["IncidentLFUCache"](capacity)
    expected = {}
    sequence = 0
    for _ in range(170):
        key = source.randrange(0, 14)
        if source.randrange(2):
            actual = cache.get(key)
            if key in expected:
                value, frequency, _ = expected[key]
                sequence += 1
                expected[key] = (value, frequency + 1, sequence)
                assert actual == value
            else:
                assert actual is None
        else:
            value = source.randrange(-1000, 1000)
            evicted = None
            if capacity:
                if key in expected:
                    _, frequency, _ = expected[key]
                    sequence += 1
                    expected[key] = (value, frequency + 1, sequence)
                else:
                    if len(expected) == capacity:
                        evicted = min(expected, key=lambda resident: (expected[resident][1], expected[resident][2]))
                        del expected[evicted]
                    sequence += 1
                    expected[key] = (value, 1, sequence)
            assert cache.put(key, value) == evicted
        assert {key: pair[0] for key, pair in cache.entries.items()} == {
            key: state[0] for key, state in expected.items()}
        assert {key: pair[1] for key, pair in cache.entries.items()} == {
            key: state[1] for key, state in expected.items()}
        checks += 3
for seed in range(28):
    source = random.Random(151000 + seed)
    index = expiry_scope["IncidentExpiryIndex"]()
    expected = {}
    now = 0
    for _ in range(150):
        now += source.randrange(0, 5)
        expected = {key: state for key, state in expected.items() if state[1] > now}
        key = source.randrange(0, 12)
        if source.randrange(2):
            lifetime = source.randrange(0, 35)
            value = source.randrange(-100, 100)
            index.put(key, value, now, lifetime)
            if lifetime:
                expected[key] = (value, now + lifetime)
            else:
                expected.pop(key, None)
        else:
            actual = index.get(key, now)
            assert actual == (expected[key][0] if key in expected else None)
            checks += 1
        index.advance(now)
        assert {key: (value, expiry) for key, (value, expiry, _) in index.entries.items()} == expected
        checks += 1
    try:
        index.advance(now - 1)
        assert False, "backward clock accepted"
    except ValueError:
        checks += 1
for seed in range(28):
    source = random.Random(162000 + seed)
    store = slots_scope["IncidentSlotStore"]()
    foreign = slots_scope["IncidentSlotStore"]()
    live = {}
    retired = []
    for _ in range(170):
        if live and source.randrange(3) == 0:
            handle = source.choice(list(live))
            assert store.remove(handle) == live.pop(handle)
            retired.append(handle)
        else:
            value = source.randrange(-10000, 10000)
            handle = store.insert(value)
            live[handle] = value
            assert store.get(handle) == value
        checks += 1
        if retired:
            try:
                store.get(source.choice(retired))
                assert False, "retired handle resolved"
            except KeyError:
                checks += 1
        for handle, value in list(live.items())[-4:]:
            assert store.get(handle) == value
            checks += 1
    if live:
        handle = next(iter(live))
        try:
            foreign.get(handle)
            assert False, "foreign handle resolved"
        except KeyError:
            checks += 1
for arity in (2, 3, 4, 7):
    for seed in range(25):
        source = random.Random(173000 + seed * 13 + arity)
        queue = dary_scope["DaryDispatchHeap"](arity)
        oracle = []
        sequence = 0
        for _ in range(230):
            if oracle and source.randrange(3) == 0:
                assert queue.pop() == heapq.heappop(oracle)[2]
            else:
                priority = source.randrange(-100, 100)
                sequence += 1
                incident_id = f"incident-{sequence}"
                queue.push(priority, incident_id)
                heapq.heappush(oracle, (priority, sequence, incident_id))
            assert len(queue.values) == len(oracle)
            assert all(queue.values[(child - 1) // arity] <= queue.values[child]
                       for child in range(1, len(queue.values)))
            checks += 2
        while oracle:
            assert queue.pop() == heapq.heappop(oracle)[2]
            checks += 1

misra_scope, _ = namespace("dsa/misra-gries-frequent-item-candidates")
space_scope, _ = namespace("dsa/space-saving-topk-stream-summary")
hll_scope, _ = namespace("dsa/hyperloglog-register-distinct-estimate")
reservoir_scope, _ = namespace("dsa/reservoir-sampling-fixed-memory")
for slot_count in (1, 2, 4, 7):
    for seed in range(28):
        source = random.Random(184000 + slot_count * 41 + seed)
        summary = misra_scope["FrequentIncidentCandidates"](slot_count)
        exact = Counter()
        for _ in range(160):
            incident_code = f"code-{source.randrange(0, 13)}"
            summary.record(incident_code)
            exact[incident_code] += 1
            candidates = set(summary.candidates())
            assert len(candidates) <= slot_count
            assert all(code in candidates for code, frequency in exact.items()
                       if frequency * (slot_count + 1) > summary.seen)
            checks += 2
for capacity in (1, 2, 4, 8):
    for seed in range(28):
        source = random.Random(195000 + capacity * 43 + seed)
        summary = space_scope["SpaceSavingIncidents"](capacity)
        exact = Counter()
        for _ in range(160):
            incident_code = f"code-{source.randrange(0, 15)}"
            summary.record(incident_code)
            exact[incident_code] += 1
            assert len(summary.entries) <= capacity
            assert all(estimate - error <= exact[code] <= estimate
                       for code, (estimate, error) in summary.entries.items())
            minimum = min((estimate for estimate, _ in summary.entries.values()), default=0)
            assert all(frequency <= minimum for code, frequency in exact.items()
                       if code not in summary.entries and len(summary.entries) == capacity)
            checks += 3
for precision in (5, 7, 9):
    for seed in range(24):
        source = random.Random(206000 + precision * 47 + seed)
        left_ids = {f"incident-{source.randrange(0, 1100)}" for _ in range(320)}
        right_ids = {f"incident-{source.randrange(0, 1100)}" for _ in range(320)}
        left = hll_scope["DistinctIncidentEstimate"](precision)
        right = hll_scope["DistinctIncidentEstimate"](precision)
        union = hll_scope["DistinctIncidentEstimate"](precision)
        for incident_id in left_ids:
            left.add(incident_id)
            union.add(incident_id)
        for incident_id in right_ids:
            right.add(incident_id)
            union.add(incident_id)
        before = list(left.registers)
        for incident_id in left_ids:
            left.add(incident_id)
        assert left.registers == before
        left.merge(right)
        assert left.registers == union.registers
        assert abs(left.estimate() - len(left_ids | right_ids)) / len(left_ids | right_ids) < (0.75 if precision == 5 else 0.35)
        checks += 3
for capacity in (0, 1, 4, 9):
    for seed in range(60):
        sampler = reservoir_scope["IncidentReservoir"](capacity, seed)
        replay = reservoir_scope["IncidentReservoir"](capacity, seed)
        for event_number in range(37):
            incident_id = f"incident-{event_number}"
            sampler.record(incident_id)
            replay.record(incident_id)
            assert len(sampler.sample()) == min(capacity, event_number + 1)
            assert len(set(sampler.sample())) == len(sampler.sample())
            checks += 2
        assert sampler.sample() == replay.sample()
        assert sampler.seen == 37
        checks += 2
sample_counts = Counter()
for seed in range(4000):
    sampler = reservoir_scope["IncidentReservoir"](4, seed)
    for event_number in range(20):
        sampler.record(event_number)
    sample_counts.update(sampler.sample())
assert all(abs(sample_counts[event_number] - 800) < 110 for event_number in range(20))
checks += 20

counting_scope, _ = namespace("dsa/counting-bloom-filter-balanced-deletion")
scalable_scope, _ = namespace("dsa/scalable-bloom-filter-layer-growth")
blocked_scope, _ = namespace("dsa/blocked-bloom-filter-locality-tradeoff")
cuckoo_filter_scope, _ = namespace("dsa/cuckoo-filter-fingerprint-relocation")
for seed in range(40):
    source = random.Random(217000 + seed)
    filter_index = counting_scope["CountingIncidentFilter"](127, 4)
    exact = Counter()
    for _ in range(180):
        incident_id = f"incident-{source.randrange(0, 60)}"
        if exact[incident_id] and source.randrange(3) == 0:
            filter_index.remove_known_insert(incident_id)
            exact[incident_id] -= 1
        else:
            filter_index.add(incident_id)
            exact[incident_id] += 1
        assert all(filter_index.might_contain(code)
                   for code, multiplicity in exact.items() if multiplicity)
        assert all(counter >= 0 for counter in filter_index.counters)
        checks += 2
for first_capacity in (1, 3, 7):
    for seed in range(25):
        source = random.Random(228000 + first_capacity * 53 + seed)
        filter_index = scalable_scope["ScalableIncidentFilter"](first_capacity, 0.04)
        inserted = []
        for _ in range(100):
            incident_id = f"incident-{source.randrange(0, 180)}"
            filter_index.add(incident_id)
            inserted.append(incident_id)
            assert all(filter_index.might_contain(code) for code in inserted)
            assert sum(layer["insertions"] for layer in filter_index.layers) == len(inserted)
            assert all(layer["insertions"] <= layer["capacity"] for layer in filter_index.layers)
            checks += 3
for seed in range(50):
    source = random.Random(239000 + seed)
    filter_index = blocked_scope["BlockedIncidentFilter"](8, 64, 4)
    inserted = set()
    for _ in range(100):
        incident_id = f"incident-{source.randrange(0, 200)}"
        filter_index.add(incident_id)
        inserted.add(incident_id)
        assert all(filter_index.might_contain(code) for code in inserted)
        assert all(block >= 0 and block.bit_length() <= 64 for block in filter_index.blocks)
        checks += 2
for seed in range(50):
    filter_index = cuckoo_filter_scope["FingerprintIncidentFilter"](
        bucket_count=8, bucket_size=2, fingerprint_bits=12, max_kicks=12, seed=seed)
    accepted = []
    rejected = 0
    for incident_number in range(45):
        incident_id = f"incident-{seed}-{incident_number}"
        before = [bucket[:] for bucket in filter_index.buckets]
        if filter_index.add(incident_id):
            accepted.append(incident_id)
            assert filter_index.might_contain(incident_id)
        else:
            rejected += 1
            assert filter_index.buckets == before
        assert all(filter_index.might_contain(code) for code in accepted)
        assert all(len(bucket) <= 2 for bucket in filter_index.buckets)
        checks += 3
    assert rejected > 0
    checks += 1

pairing_scope, _ = namespace("dsa/pairing-heap-two-pass-meld")
binomial_scope, _ = namespace("dsa/binomial-heap-degree-carry-meld")
radix_scope, _ = namespace("dsa/radix-heap-monotone-integer-priorities")
dual_scope, _ = namespace("dsa/dual-heap-double-ended-priority-queue")
for scope_name, class_name in ((pairing_scope, "PairingIncidentHeap"),
                               (binomial_scope, "BinomialIncidentHeap")):
    for seed in range(35):
        source = random.Random(250000 + seed)
        receiver = scope_name[class_name]()
        donor = scope_name[class_name]()
        expected = []
        for arrival in range(110):
            priority = source.randrange(-20, 60)
            incident_id = f"incident-{seed}-{arrival}"
            (receiver if source.randrange(2) else donor).push(priority, incident_id)
            expected.append((priority, arrival, incident_id))
        receiver.meld(donor)
        assert donor.size == 0 and receiver.size == len(expected)
        checks += 1
        for priority, _, incident_id in sorted(expected):
            assert receiver.pop() == (priority, incident_id)
            if class_name == "PairingIncidentHeap":
                pending = [receiver.root] if receiver.root else []
                counted = 0
                while pending:
                    node = pending.pop()
                    counted += 1
                    assert all(node.key <= child.key for child in node.children)
                    pending.extend(node.children)
                assert counted == receiver.size
            else:
                assert len(receiver.roots) == len(set(receiver.roots))

                def inspect_binomial(node):
                    assert sorted(child.degree for child in node.children) == list(range(node.degree))
                    assert all(node.key <= child.key for child in node.children)
                    return 1 + sum(inspect_binomial(child) for child in node.children)

                assert sum(inspect_binomial(root_node) for root_node in receiver.roots.values()) == receiver.size
                assert all(inspect_binomial(root_node) == 1 << degree
                           for degree, root_node in receiver.roots.items())
            checks += 3
for seed in range(35):
    source = random.Random(261000 + seed)
    queue = radix_scope["MonotoneIncidentQueue"]()
    expected = {}
    for arrival in range(170):
        if expected and source.randrange(3) == 0:
            priority, incident_id = queue.pop()
            assert priority == min(expected.values())
            assert expected.pop(incident_id) == priority
        else:
            priority = source.randrange(queue.last, queue.last + 120)
            incident_id = f"incident-{seed}-{arrival}"
            queue.push(priority, incident_id)
            expected[incident_id] = priority
        assert queue.size == len(expected)
        checks += 2
    while expected:
        priority, incident_id = queue.pop()
        assert priority == min(expected.values())
        assert expected.pop(incident_id) == priority
        checks += 2
    if queue.last:
        try:
            queue.push(queue.last - 1, "late-incident")
            assert False, "radix queue accepted decreasing priority"
        except ValueError:
            checks += 1
for seed in range(35):
    source = random.Random(272000 + seed)
    queue = dual_scope["DualEndedIncidentQueue"]()
    expected = {}
    sequence = 0
    for _ in range(220):
        if expected and source.randrange(3) == 0:
            if source.randrange(2):
                chosen = min(expected, key=lambda incident: (expected[incident][0], expected[incident][1]))
                assert queue.pop_min() == (expected[chosen][0], chosen)
            else:
                chosen = min(expected, key=lambda incident: (-expected[incident][0], expected[incident][1]))
                assert queue.pop_max() == (expected[chosen][0], chosen)
            del expected[chosen]
        else:
            incident_id = f"incident-{source.randrange(30)}"
            if incident_id in expected:
                continue
            priority = source.randrange(-30, 70)
            queue.push(priority, incident_id)
            expected[incident_id] = (priority, sequence)
            sequence += 1
        assert {incident: priority for incident, (priority, _) in queue.live.items()} == {
            incident: priority for incident, (priority, _) in expected.items()}
        assert len(queue.minimum) + len(queue.maximum) <= 3 * len(queue.live) + 32
        checks += 2

grid_scope, _ = namespace("dsa/spatial-hash-grid-moving-points")
quad_scope, _ = namespace("dsa/point-region-quadtree-range-report")
box_scope, _ = namespace("dsa/static-bvh-axis-aligned-box-overlap")
morton_scope, _ = namespace("dsa/morton-code-ordered-grid-range-index")

for seed in range(20):
    source = random.Random(280000 + seed)
    grid = grid_scope["MovingDepotGrid"](7)
    expected = {}
    for _ in range(180):
        depot_id = f"depot-{source.randrange(45)}"
        action = source.randrange(4)
        if action == 0 and depot_id in expected:
            grid.remove(depot_id)
            del expected[depot_id]
        elif action in (0, 1, 2):
            position = (source.randrange(-48, 49), source.randrange(-48, 49))
            grid.upsert(depot_id, *position)
            expected[depot_id] = position
        else:
            center = (source.randrange(-50, 51), source.randrange(-50, 51))
            radius = source.randrange(31)
            direct = sorted(identifier for identifier, (x, y) in expected.items()
                            if (x - center[0]) ** 2 + (y - center[1]) ** 2 <= radius ** 2)
            assert grid.within_radius(*center, radius) == direct
            checks += 1
        assert grid.points == expected
        assert {identifier for identifiers in grid.cells.values() for identifier in identifiers} == set(expected)
        assert all(identifier in grid.cells[grid._cell(*point)]
                   for identifier, point in expected.items())
        checks += 3

for seed in range(20):
    source = random.Random(281000 + seed)
    points = [(f"depot-{number}", source.randrange(64), source.randrange(64))
              for number in range(110)]
    quadtree = quad_scope["DepotQuadtree"](width=64, capacity=3, max_depth=6)
    for depot_id, x, y in points:
        quadtree.insert(depot_id, x, y)
    for _ in range(100):
        left, right = sorted((source.randrange(65), source.randrange(65)))
        bottom, top = sorted((source.randrange(65), source.randrange(65)))
        direct = sorted(depot_id for depot_id, x, y in points
                        if left <= x < right and bottom <= y < top)
        assert quadtree.range_report(left, bottom, right, top) == direct
        checks += 1

for seed in range(20):
    source = random.Random(282000 + seed)
    rectangles = []
    for number in range(110):
        x0, x1 = sorted((source.randrange(-30, 41), source.randrange(-30, 41)))
        y0, y1 = sorted((source.randrange(-30, 41), source.randrange(-30, 41)))
        rectangles.append((f"depot-{number}", (x0, y0, x1, y1)))
    hierarchy = box_scope["DepotBoxHierarchy"](rectangles, leaf_capacity=3)
    for _ in range(100):
        left, right = sorted((source.randrange(-35, 46), source.randrange(-35, 46)))
        bottom, top = sorted((source.randrange(-35, 46), source.randrange(-35, 46)))
        query = (left, bottom, right, top)
        direct = sorted(depot_id for depot_id, box in rectangles
                        if box_scope["intersects"](box, query))
        assert hierarchy.overlapping(query) == direct
        checks += 1

for seed in range(20):
    source = random.Random(283000 + seed)
    points = [(f"depot-{number}", source.randrange(64), source.randrange(64))
              for number in range(110)]
    ordered = morton_scope["MortonDepotIndex"](points, bits=6)
    for _ in range(100):
        left, right = sorted((source.randrange(65), source.randrange(65)))
        bottom, top = sorted((source.randrange(65), source.randrange(65)))
        direct = sorted(depot_id for depot_id, x, y in points
                        if left <= x < right and bottom <= y < top)
        assert ordered.range_report(left, bottom, right, top) == direct
        checks += 1

elias_scope, _ = namespace("dsa/elias-fano-monotone-alert-ids")
chunk_scope, _ = namespace("dsa/chunked-array-bitmap-alert-set")
posting_scope, _ = namespace("dsa/gap-varint-postings-seek-checkpoints")
louds_scope, _ = namespace("dsa/louds-level-order-alert-trie")

for seed in range(30):
    source = random.Random(300000 + seed)
    identifiers = sorted(source.sample(range(1024), source.randrange(121)))
    encoded = elias_scope["EliasFanoAlertIds"](identifiers, universe=1024)
    posting = posting_scope["GapPostingIndex"](identifiers, checkpoint_stride=7)
    assert [encoded.at(rank) for rank in range(len(identifiers))] == identifiers
    assert posting.values() == identifiers
    checks += 2
    for _ in range(75):
        target = source.randrange(1100)
        direct = next((identifier for identifier in identifiers if identifier >= target), None)
        assert encoded.lower_bound(target) == direct
        assert posting.seek_at_least(target) == direct
        checks += 2
try:
    posting_scope["decode_unsigned"](bytearray([128]), 0)
    assert False, "truncated variable integer accepted"
except ValueError:
    checks += 1

for seed in range(30):
    source = random.Random(301000 + seed)
    first = chunk_scope["ChunkedAlertBitmap"]()
    second = chunk_scope["ChunkedAlertBitmap"]()
    expected_first, expected_second = set(), set()
    for _ in range(450):
        identifier = source.randrange(2048)
        choose_first = source.randrange(2) == 0
        index = first if choose_first else second
        expected = expected_first if choose_first else expected_second
        if source.randrange(3) == 0 and identifier in expected:
            index.remove(identifier)
            expected.remove(identifier)
        else:
            index.add(identifier)
            expected.add(identifier)
        assert index.contains(identifier) == (identifier in expected)
        assert all(count == (len(container) if isinstance(container, list) else container.bit_count())
                   for high, count in index.counts.items()
                   for container in [index.containers[high]])
        checks += 2
    assert first.values() == sorted(expected_first)
    assert second.values() == sorted(expected_second)
    assert first.intersection(second) == sorted(expected_first & expected_second)
    checks += 3

for seed in range(30):
    source = random.Random(302000 + seed)
    words = {"".join(source.choices("abcd", k=source.randrange(6)))
             for _ in range(125)}
    trie = louds_scope["LevelOrderAlertTrie"](words)
    node_count = len(trie.terminal)
    assert len(trie.degree_bits) == 2 * node_count - 1
    assert len(trie.zero_positions) == node_count
    assert len(trie.edge_labels) == node_count - 1
    checks += 3
    for word in words:
        assert trie.contains(word)
        checks += 1
    for _ in range(80):
        candidate = "".join(source.choices("abcd", k=source.randrange(6)))
        assert trie.contains(candidate) == (candidate in words)
        assert trie.has_prefix(candidate) == any(word.startswith(candidate) for word in words)
        checks += 2

gap_scope, _ = namespace("dsa/gap-buffer-cursor-local-edits")
rope_scope, _ = namespace("dsa/immutable-rope-text-snapshots")
unrolled_scope, _ = namespace("dsa/unrolled-linked-list-block-edits")
segmented_scope, _ = namespace("dsa/segmented-array-prefix-block-locate")

for seed in range(25):
    source = random.Random(290000 + seed)
    gap = gap_scope["IncidentGapBuffer"]("", gap_capacity=3)
    expected_text = ""
    cursor = 0
    for _ in range(160):
        action = source.randrange(4)
        if action == 0:
            cursor = source.randrange(len(expected_text) + 1)
            gap.move_cursor(cursor)
        elif action == 1:
            inserted = "".join(source.choices("ABxy", k=source.randrange(5)))
            gap.insert(inserted)
            expected_text = expected_text[:cursor] + inserted + expected_text[cursor:]
            cursor += len(inserted)
        elif action == 2:
            count = source.randrange(min(4, cursor) + 1)
            gap.backspace(count)
            expected_text = expected_text[:cursor - count] + expected_text[cursor:]
            cursor -= count
        else:
            count = source.randrange(min(4, len(expected_text) - cursor) + 1)
            gap.delete_forward(count)
            expected_text = expected_text[:cursor] + expected_text[cursor + count:]
        assert gap.text() == expected_text and len(gap) == len(expected_text)
        assert gap.gap_left == cursor and gap.gap_right > gap.gap_left
        assert all(character is None for character in gap.buffer[gap.gap_left:gap.gap_right])
        assert all(character is not None for character in gap.buffer[:gap.gap_left] + gap.buffer[gap.gap_right:])
        checks += 4

for seed in range(25):
    source = random.Random(291000 + seed)
    rope = rope_scope["build_rope"]("")
    expected_text = ""
    for _ in range(80):
        old_root, old_text = rope, expected_text
        if source.randrange(2) or not expected_text:
            index = source.randrange(len(expected_text) + 1)
            inserted = "".join(source.choices("PQrs", k=source.randrange(1, 5)))
            rope = rope_scope["insert"](rope, index, inserted)
            expected_text = expected_text[:index] + inserted + expected_text[index:]
        else:
            start = source.randrange(len(expected_text) + 1)
            end = source.randrange(start, len(expected_text) + 1)
            rope = rope_scope["delete"](rope, start, end)
            expected_text = expected_text[:start] + expected_text[end:]
        assert rope_scope["flatten"](old_root) == old_text
        assert rope_scope["flatten"](rope) == expected_text
        if expected_text:
            index = source.randrange(len(expected_text))
            assert rope_scope["character_at"](rope, index) == expected_text[index]
        checks += 3

for seed in range(25):
    source = random.Random(292000 + seed)
    for class_name, scope in (("UnrolledIncidentList", unrolled_scope),
                              ("SegmentedIncidentArray", segmented_scope)):
        sequence = scope[class_name](block_capacity=3)
        expected = []
        for _ in range(160):
            action = source.randrange(3)
            if action == 0 or not expected:
                index = source.randrange(len(expected) + 1)
                incident_id = f"incident-{source.randrange(79)}"
                sequence.insert(index, incident_id)
                expected.insert(index, incident_id)
            elif action == 1:
                index = source.randrange(len(expected))
                assert sequence.delete(index) == expected.pop(index)
                checks += 1
            else:
                index = source.randrange(len(expected))
                assert sequence.at(index) == expected[index]
                checks += 1
            assert sequence.values() == expected and len(sequence) == len(expected)
            checks += 2
            if class_name == "UnrolledIncidentList":
                block = sequence.head
                flattened = []
                last = None
                while block is not None:
                    assert 1 <= len(block.items) <= sequence.capacity
                    flattened.extend(block.items)
                    last, block = block, block.next
                assert flattened == expected and sequence.tail is last
            else:
                assert all(1 <= len(block) <= sequence.capacity for block in sequence.blocks)
                running = 0
                for block, end in zip(sequence.blocks, sequence.ends):
                    running += len(block)
                    assert end == running
                assert running == len(expected) and len(sequence.blocks) == len(sequence.ends)
            checks += 2

arena_scope, _ = namespace("dsa/checkpoint-bump-arena-lifetime")
arena_model = arena_scope["CheckpointArena"](256)
arena_rng = random.Random(4719)
arena_handles = []
arena_marks = []
for step in range(350):
    action = arena_rng.randrange(5)
    if action <= 2:
        size = arena_rng.randrange(1, 24)
        alignment = 1 << arena_rng.randrange(4)
        old_cursor = arena_model.cursor
        start = (old_cursor + alignment - 1) & -alignment
        try:
            handle = arena_model.allocate(size, alignment)
        except MemoryError:
            assert start + size > 256 and arena_model.cursor == old_cursor
        else:
            assert arena_model.span(handle) == (start, size)
            assert arena_model.read(handle) == bytes(size)
            payload = bytes([step % 251]) * size
            arena_model.write(handle, payload)
            arena_handles.append((handle, start, size, payload))
    elif action == 3:
        arena_marks.append(arena_model.mark())
    elif arena_marks:
        checkpoint_index = arena_rng.randrange(len(arena_marks))
        checkpoint = arena_marks[checkpoint_index]
        arena_model.rewind(checkpoint)
        arena_marks = arena_marks[:checkpoint_index]
        arena_handles = [record for record in arena_handles if record[0] < checkpoint[2]]
    occupied = set()
    for handle, start, size, payload in arena_handles:
        assert arena_model.read(handle) == payload
        assert not occupied.intersection(range(start, start + size))
        occupied.update(range(start, start + size))
    assert set(arena_model.active) == {record[0] for record in arena_handles}
    checks += 1
previous_handle = arena_handles[-1][0] if arena_handles else None
arena_model.reset()
if previous_handle is not None:
    assert previous_handle not in arena_model.active
new_handle = arena_model.allocate(7)
assert new_handle != previous_handle
checks += 1

span_scope, _ = namespace("dsa/first-fit-free-span-coalescing")
span_pool = span_scope["FirstFitSpanPool"](128)
span_rng = random.Random(6382)
span_live = {}
for _ in range(500):
    if span_live and span_rng.randrange(3) == 0:
        start = span_rng.choice(list(span_live))
        span_pool.release(start)
        del span_live[start]
    else:
        size = span_rng.randrange(1, 28)
        expected = next((start for start, length in span_pool.free_spans if length >= size), None)
        try:
            start = span_pool.allocate(size)
        except MemoryError:
            assert expected is None
        else:
            assert start == expected
            span_live[start] = size
    occupied = {unit for start, length in span_live.items() for unit in range(start, start + length)}
    free = {unit for start, length in span_pool.free_spans for unit in range(start, start + length)}
    assert not occupied & free and occupied | free == set(range(128))
    assert len(occupied) == sum(span_live.values())
    assert len(free) == span_pool.free_units()
    assert all(first[0] + first[1] < second[0] for first, second in zip(span_pool.free_spans, span_pool.free_spans[1:]))
    checks += 1
try:
    span_pool.release(129)
except KeyError:
    checks += 1
else:
    raise AssertionError("unknown free-span owner accepted")

buddy_scope, _ = namespace("dsa/buddy-power-of-two-block-coalescing")
buddy_pool = buddy_scope["BuddyBlockPool"](128)
buddy_rng = random.Random(8197)
buddy_live = {}
for _ in range(500):
    if buddy_live and buddy_rng.randrange(3) == 0:
        start = buddy_rng.choice(list(buddy_live))
        buddy_pool.release(start)
        del buddy_live[start]
    else:
        requested = buddy_rng.randrange(1, 40)
        try:
            start = buddy_pool.allocate(requested)
        except MemoryError:
            assert all(not buddy_pool.free_by_order[order] for order in range((requested - 1).bit_length(), 8))
        else:
            order, recorded_request = buddy_pool.allocated[start]
            assert recorded_request == requested and (1 << order) >= requested
            buddy_live[start] = order
    occupied = set()
    for start, order in buddy_live.items():
        width = 1 << order
        assert start % width == 0 and not occupied.intersection(range(start, start + width))
        occupied.update(range(start, start + width))
    free = set()
    for order, blocks in enumerate(buddy_pool.free_by_order):
        width = 1 << order
        for start in blocks:
            assert start % width == 0 and not free.intersection(range(start, start + width))
            free.update(range(start, start + width))
            assert start ^ width not in blocks
    assert not occupied & free and occupied | free == set(range(128))
    assert len(free) == buddy_pool.free_units()
    checks += 1
for start in list(buddy_live):
    buddy_pool.release(start)
assert buddy_pool.free_by_order[7] == {0} and buddy_pool.free_units() == 128
checks += 1

slab_scope, _ = namespace("dsa/generational-slab-slot-cache")
slab_cache = slab_scope["IncidentSlabCache"](4)
slab_rng = random.Random(1147)
slab_live = {}
slab_stale = []
for step in range(500):
    if slab_live and slab_rng.randrange(3) == 0:
        handle = slab_rng.choice(list(slab_live))
        slab_cache.release(handle)
        slab_stale.append(handle)
        del slab_live[handle]
    else:
        record = f"case-{step}"
        handle = slab_cache.allocate(record)
        slab_live[handle] = record
    assert all(slab_cache.get(handle) == record for handle, record in slab_live.items())
    assert len(slab_cache.live) == len(slab_live)
    assert len(set(slab_cache.free_slots)) == len(slab_cache.free_slots)
    assert len(slab_cache.free_slots) + len(slab_cache.live) == len(slab_cache.pages) * 4
    for handle in slab_stale[-3:]:
        try:
            slab_cache.get(handle)
        except KeyError:
            pass
        else:
            raise AssertionError("stale slab handle accepted")
    checks += 1

hamt_scope, _ = namespace("dsa/persistent-bitmap-hamt-alert-map")
hamt_rng = random.Random(57047)
hamt_versions = [(hamt_scope["PersistentAlertMap"](), {})]
for step in range(350):
    alert_id = hamt_rng.randrange(0, 2048)
    if step % 3 == 0:
        alert_id = 47 + 256 * hamt_rng.randrange(6)
    previous_map, previous_expected = hamt_versions[-1]
    state = f"state-{step}"
    updated_map = previous_map.set(alert_id, state)
    updated_expected = {**previous_expected, alert_id: state}
    hamt_versions.append((updated_map, updated_expected))
    assert updated_map.get(alert_id) == state
    for version_map, snapshot in hamt_rng.sample(hamt_versions, min(5, len(hamt_versions))):
        for candidate in hamt_rng.sample(range(0, 2048), 8):
            if candidate in snapshot:
                assert version_map.get(candidate) == snapshot[candidate]
            else:
                try:
                    version_map.get(candidate)
                except KeyError:
                    pass
                else:
                    raise AssertionError("HAMT returned an absent key")
    checks += 1
for version_map, snapshot in hamt_versions[::17]:
    assert all(version_map.get(alert_id) == state for alert_id, state in snapshot.items())
    checks += 1

terms_scope, _ = namespace("dsa/ternary-search-tree-incident-completion")
terms_index = terms_scope["IncidentTermIndex"]()
terms_expected = set()
terms_rng = random.Random(71103)
alphabet = "abceilorv"
for step in range(320):
    term = "".join(terms_rng.choice(alphabet) for _ in range(terms_rng.randrange(0, 7)))
    terms_index.insert(term)
    terms_expected.add(term)
    prefix = term[:terms_rng.randrange(0, len(term) + 1)]
    assert terms_index.contains(term)
    assert terms_index.complete(prefix) == sorted(candidate for candidate in terms_expected if candidate.startswith(prefix))
    assert terms_index.contains(prefix) == (prefix in terms_expected)
    checks += 1

routes_scope, _ = namespace("dsa/binary-radix-longest-prefix-routes")
route_table = routes_scope["ServiceRouteTable"](12)
route_rng = random.Random(90217)
route_expected = {}
for step in range(280):
    length = route_rng.randrange(13)
    prefix = route_rng.randrange(1 << 12) & ~((1 << (12 - length)) - 1)
    gateway = f"gateway-{step}"
    route_table.add(prefix, length, gateway)
    route_expected[(prefix, length)] = gateway
    service_id = route_rng.randrange(1 << 12)
    matches = [(route_length, state) for (route_prefix, route_length), state in route_expected.items()
               if service_id & ~((1 << (12 - route_length)) - 1) == route_prefix]
    answer = max(matches, key=lambda item: item[0])[1] if matches else None
    assert route_table.lookup(service_id) == answer
    checks += 1
try:
    route_table.add(1, 0, "invalid")
except ValueError:
    checks += 1
else:
    raise AssertionError("route with host bits accepted")

directory_scope, _ = namespace("dsa/extendible-hash-directory-bucket-splits")
alert_directory = directory_scope["ExtendibleAlertDirectory"](3)
directory_rng = random.Random(21831)
directory_expected = {}
for step in range(400):
    alert_id = directory_rng.randrange(2048)
    if step % 4 == 0:
        alert_id = 47 + 256 * directory_rng.randrange(6)
    if directory_expected and step % 5 == 0:
        alert_id = directory_rng.choice(list(directory_expected))
        alert_directory.delete(alert_id)
        del directory_expected[alert_id]
    else:
        state = f"state-{step}"
        alert_directory.set(alert_id, state)
        directory_expected[alert_id] = state
    assert len(alert_directory.directory) == 1 << alert_directory.global_depth
    unique_buckets = {id(bucket): bucket for bucket in alert_directory.directory}
    all_records = {}
    for bucket in unique_buckets.values():
        aliases = [index for index, candidate in enumerate(alert_directory.directory) if candidate is bucket]
        assert len(aliases) == 1 << (alert_directory.global_depth - bucket.depth)
        assert len({index & ((1 << bucket.depth) - 1) for index in aliases}) == 1
        for stored_id, stored_state in bucket.records.items():
            assert alert_directory.directory[alert_directory._index(stored_id)] is bucket
            assert stored_id not in all_records
            all_records[stored_id] = stored_state
    assert all_records == directory_expected
    checks += 1

clock_scope, _ = namespace("dsa/clock-second-chance-page-cache")
clock_cache = clock_scope["ClockPageCache"](5)
clock_rng = random.Random(47183)
clock_frames = [None] * 5
clock_bits = [False] * 5
clock_hand = 0
clock_used = 0
for step in range(360):
    page_id = clock_rng.randrange(17)
    current = next((position for position, frame in enumerate(clock_frames)
                    if frame is not None and frame[0] == page_id), None)
    if current is not None and step % 3 == 0:
        assert clock_cache.get(page_id) == clock_frames[current][1]
        clock_bits[current] = True
    else:
        payload = f"page-{step}"
        if current is not None:
            victim_id = None
            clock_frames[current] = (page_id, payload)
            clock_bits[current] = True
        elif clock_used < 5:
            victim_id = None
            clock_frames[clock_used] = (page_id, payload)
            clock_bits[clock_used] = False
            clock_hand = (clock_used + 1) % 5
            clock_used += 1
        else:
            while clock_bits[clock_hand]:
                clock_bits[clock_hand] = False
                clock_hand = (clock_hand + 1) % 5
            victim_id = clock_frames[clock_hand][0]
            clock_frames[clock_hand] = (page_id, payload)
            clock_bits[clock_hand] = False
            clock_hand = (clock_hand + 1) % 5
        assert clock_cache.put(page_id, payload) == victim_id
    assert clock_cache.frames == clock_frames
    assert clock_cache.referenced == clock_bits
    assert clock_cache.hand == clock_hand
    assert {page_id: position for position, frame in enumerate(clock_frames)
            if frame is not None for page_id in [frame[0]]} == clock_cache.positions
    checks += 1

segmented_scope, _ = namespace("dsa/segmented-lru-probation-protected")
segmented_cache = segmented_scope["SegmentedIncidentCache"](3, 2)
segmented_rng = random.Random(61109)
probation_ref = []
protected_ref = []
resident_values = {}
for step in range(370):
    incident_id = segmented_rng.randrange(13)
    if incident_id in resident_values and step % 3 == 0:
        assert segmented_cache.get(incident_id) == resident_values[incident_id]
        if incident_id in protected_ref:
            protected_ref.remove(incident_id)
            protected_ref.append(incident_id)
        else:
            probation_ref.remove(incident_id)
            protected_ref.append(incident_id)
            if len(protected_ref) > 2:
                demoted = protected_ref.pop(0)
                probation_ref.append(demoted)
                if len(probation_ref) > 3:
                    del resident_values[probation_ref.pop(0)]
    else:
        payload = f"incident-{step}"
        if incident_id in protected_ref:
            protected_ref.remove(incident_id)
            protected_ref.append(incident_id)
            victim = None
        elif incident_id in probation_ref:
            probation_ref.remove(incident_id)
            probation_ref.append(incident_id)
            victim = None
        else:
            probation_ref.append(incident_id)
            victim = probation_ref.pop(0) if len(probation_ref) > 3 else None
            if victim is not None:
                del resident_values[victim]
        resident_values[incident_id] = payload
        assert segmented_cache.put(incident_id, payload) == victim
    assert list(segmented_cache.probation) == probation_ref
    assert list(segmented_cache.protected) == protected_ref
    assert dict(segmented_cache.probation) | dict(segmented_cache.protected) == resident_values
    assert not set(probation_ref) & set(protected_ref)
    checks += 1

admission_scope, _ = namespace("dsa/aging-frequency-sketch-cache-admission")
admission_cache = admission_scope["FrequencyAdmissionCache"](3)
admission_rng = random.Random(12601)
admission_ref = {}
admission_order = []
for step in range(320):
    incident_id = admission_rng.randrange(19)
    if incident_id in admission_ref and step % 4 == 0:
        assert admission_cache.get(incident_id) == admission_ref[incident_id]
        admission_order.remove(incident_id)
        admission_order.append(incident_id)
    else:
        sketch_after = copy.deepcopy(admission_cache.sketch)
        sketch_after.record(incident_id)
        payload = f"incident-{step}"
        if incident_id in admission_ref:
            expected_admitted = True
            admission_ref[incident_id] = payload
            admission_order.remove(incident_id)
            admission_order.append(incident_id)
        elif len(admission_order) < 3:
            expected_admitted = True
            admission_ref[incident_id] = payload
            admission_order.append(incident_id)
        else:
            victim = admission_order[0]
            expected_admitted = sketch_after.estimate(incident_id) > sketch_after.estimate(victim)
            if expected_admitted:
                del admission_ref[admission_order.pop(0)]
                admission_ref[incident_id] = payload
                admission_order.append(incident_id)
        assert admission_cache.put(incident_id, payload) is expected_admitted
        assert admission_cache.sketch.counters == sketch_after.counters
    assert dict(admission_cache.order) == admission_ref
    assert list(admission_cache.order) == admission_order
    assert all(0 <= value <= 15 for row in admission_cache.sketch.counters for value in row)
    checks += 1

wheel_scope, _ = namespace("dsa/hashed-wheel-incident-expiry")
expiry_wheel = wheel_scope["IncidentExpiryWheel"](7)
wheel_rng = random.Random(71317)
deadline_ref = {}
for step in range(400):
    incident_id = wheel_rng.randrange(21)
    action = wheel_rng.randrange(4)
    if action <= 1:
        delay = wheel_rng.randrange(1, 29)
        payload = f"review-{step}"
        expiry_wheel.schedule(incident_id, delay, payload)
        deadline_ref[incident_id] = (expiry_wheel.now + delay, payload)
    elif action == 2 and incident_id in deadline_ref:
        assert expiry_wheel.cancel(incident_id) == deadline_ref.pop(incident_id)[1]
    else:
        target_tick = expiry_wheel.now + wheel_rng.randrange(0, 5)
        expected_expired = {(record_id, payload) for record_id, (due, payload) in deadline_ref.items()
                            if due <= target_tick}
        actual_expired = expiry_wheel.advance(target_tick)
        assert len(actual_expired) == len(set(actual_expired))
        assert set(actual_expired) == expected_expired
        deadline_ref = {record_id: record for record_id, record in deadline_ref.items()
                        if record[0] > target_tick}
    assert {record_id: (due, payload) for record_id, (due, payload, _) in expiry_wheel.active.items()} == deadline_ref
    assert {record_id for slot in expiry_wheel.slots for record_id in slot} == set(deadline_ref)
    assert sum(map(len, expiry_wheel.slots)) == len(deadline_ref)
    checks += 1

splay_scope, _ = namespace("dsa/splay-tree-access-and-join-invariants")
splay_index = splay_scope["SplayCaseIndex"]()
splay_ref = set()
splay_rng = random.Random(63021)
for step in range(650):
    case_id = splay_rng.randrange(97)
    action = splay_rng.randrange(3)
    if action == 0:
        assert splay_index.insert(case_id) is (case_id not in splay_ref)
        splay_ref.add(case_id)
    elif action == 1:
        assert splay_index.remove(case_id) is (case_id in splay_ref)
        splay_ref.discard(case_id)
    else:
        assert splay_index.find(case_id) is (case_id in splay_ref)
    assert splay_index.ordered_ids() == sorted(splay_ref)
    pending = [(splay_index.root, None, None, None)] if splay_index.root is not None else []
    seen_nodes = set()
    while pending:
        node, parent, low, high = pending.pop()
        assert id(node) not in seen_nodes
        seen_nodes.add(id(node))
        assert node.parent is parent
        assert (low is None or low < node.case_id) and (high is None or node.case_id < high)
        if node.left is not None:
            pending.append((node.left, node, low, node.case_id))
        if node.right is not None:
            pending.append((node.right, node, node.case_id, high))
    assert len(seen_nodes) == len(splay_ref)
    checks += 1

history_scope, _ = namespace("dsa/resident-lru-k-history-eviction")
history_cache = history_scope["ResidentHistoryCache"](4, 3)
history_ref = {}
history_clock = 0
history_rng = random.Random(77521)
for step in range(540):
    case_id = history_rng.randrange(17)
    if step % 4 == 0:
        if case_id in history_ref:
            history_clock += 1
            payload, history = history_ref[case_id]
            history_ref[case_id] = (payload, (history + [history_clock])[-3:])
            assert history_cache.read(case_id) == history_ref[case_id][0]
        else:
            before = history_cache.clock
            try:
                history_cache.read(case_id)
            except KeyError:
                pass
            else:
                raise AssertionError("missing resident read must fail")
            assert history_cache.clock == before
    else:
        payload = f"case-{step}"
        victim = None
        if case_id not in history_ref and len(history_ref) == 4:
            def reference_rank(resident_id):
                history = history_ref[resident_id][1]
                return (history[0] if len(history) == 3 else -1, history[-1], resident_id)
            victim = min(history_ref, key=reference_rank)
            del history_ref[victim]
        history_clock += 1
        previous = history_ref[case_id][1] if case_id in history_ref else []
        history_ref[case_id] = (payload, (previous + [history_clock])[-3:])
        assert history_cache.put(case_id, payload) == victim
    assert history_cache.clock == history_clock
    assert history_cache.residents == {key: value for key, (value, _) in history_ref.items()}
    assert {key: list(value) for key, value in history_cache.histories.items()} == {key: history for key, (_, history) in history_ref.items()}
    checks += 1

layout_scope, _ = namespace("dsa/eytzinger-array-search-layout")
layout_rng = random.Random(55109)
for count in range(1, 75):
    values = layout_rng.sample(range(300), count)
    catalog = layout_scope["EytzingerCaseCatalog"](values)
    ordered = sorted(values)
    for target in range(0, 301, 11):
        rank = bisect.bisect_left(ordered, target)
        assert catalog.lower_bound(target) == (None if rank == count else (ordered[rank], rank))
        assert catalog.contains(target) is (target in values)
        checks += 1

cartesian_scope, _ = namespace("dsa/cartesian-tree-static-range-minimum")
for count in range(1, 65):
    readings = [layout_rng.randrange(23) for _ in range(count)]
    index = cartesian_scope["CartesianReadingIndex"](readings)
    for _ in range(22):
        first = layout_rng.randrange(count)
        last = layout_rng.randrange(first, count)
        assert index.minimum(first, last) == min((readings[position], position) for position in range(first, last + 1))
        checks += 1
    for parent in range(count):
        for child in (index.left[parent], index.right[parent]):
            if child is not None:
                assert index.parent[child] == parent
                assert (readings[parent], parent) <= (readings[child], child)

leftist_scope, _ = namespace("dsa/leftist-heap-null-path-meld")
heaps = [leftist_scope["LeftistDispatchHeap"](), leftist_scope["LeftistDispatchHeap"]()]
heap_reference = [[], []]
for step in range(380):
    owner = layout_rng.randrange(2)
    if step % 9 == 0:
        donor = 1 - owner
        heaps[owner].merge_from(heaps[donor])
        heap_reference[owner].extend(heap_reference[donor])
        heap_reference[donor].clear()
    elif heap_reference[owner] and step % 3 == 0:
        expected = min(heap_reference[owner])
        assert heaps[owner].pop() == expected
        heap_reference[owner].remove(expected)
    else:
        key = (layout_rng.randrange(23), step)
        heaps[owner].push(*key)
        heap_reference[owner].append(key)

    def leftist_rank(node):
        if node is None:
            return 0
        left_rank = leftist_rank(node.left)
        right_rank = leftist_rank(node.right)
        assert left_rank >= right_rank and node.rank == 1 + right_rank
        for child in (node.left, node.right):
            if child is not None:
                assert node.key <= child.key
        return node.rank

    for position, heap in enumerate(heaps):
        assert heap.count == len(heap_reference[position])
        leftist_rank(heap.root)
    checks += 1

potential_scope, _ = namespace("dsa/potential-disjoint-set-difference-constraints")
for trial in range(16):
    constraints = potential_scope["DepotOffsetConstraints"](12)
    accepted = [[] for _ in range(12)]

    def graph_difference(first, second):
        seen = {first: 0}
        pending = [first]
        while pending:
            current = pending.pop()
            if current == second:
                return seen[second]
            for neighbor, delta in accepted[current]:
                if neighbor not in seen:
                    seen[neighbor] = seen[current] + delta
                    pending.append(neighbor)
        return None

    for _ in range(90):
        first, second = layout_rng.sample(range(12), 2)
        delta = layout_rng.randrange(-80, 81)
        prior = graph_difference(first, second)
        assert constraints.constrain(first, second, delta) is (prior is None or prior == delta)
        if prior is None:
            accepted[first].append((second, delta))
            accepted[second].append((first, -delta))
        for _ in range(3):
            query_first, query_second = layout_rng.sample(range(12), 2)
            assert constraints.difference(query_first, query_second) == graph_difference(query_first, query_second)
        checks += 1

range_scope, _ = namespace("dsa/static-two-dimensional-range-tree-counting")
for count in range(0, 65):
    points = [(layout_rng.randrange(-30, 30), layout_rng.randrange(-30, 30), f"depot-{point}")
              for point in range(count)]
    tree = range_scope["DepotRangeTree"](points)
    for _ in range(28):
        x_low, x_high = sorted(layout_rng.sample(range(-35, 35), 2))
        y_low, y_high = sorted(layout_rng.sample(range(-35, 35), 2))
        expected = sum(x_low <= x < x_high and y_low <= y < y_high for x, y, _ in points)
        assert tree.count(x_low, x_high, y_low, y_high) == expected
        checks += 1

veb_scope, _ = namespace("dsa/van-emde-boas-bounded-successor")
for universe in (2, 4, 8, 16, 32, 64, 128, 256):
    tree = veb_scope["AlertUniverse"](universe)
    present = set()
    for _ in range(240):
        key = layout_rng.randrange(universe)
        if layout_rng.randrange(2):
            assert tree.insert(key) is (key not in present)
            present.add(key)
        else:
            assert tree.remove(key) is (key in present)
            present.discard(key)
        ordered = sorted(present)
        assert tree.minimum == (ordered[0] if ordered else None)
        assert tree.maximum == (ordered[-1] if ordered else None)
        for target in range(-1, universe + 1):
            position = bisect.bisect_right(ordered, target)
            assert tree.successor(target) == (ordered[position] if position < len(ordered) else None)
            assert tree.contains(target) is (target in present)
        checks += 1

scapegoat_scope, _ = namespace("dsa/scapegoat-tree-subtree-rebuild-insertion")
for trial in range(8):
    index = scapegoat_scope["ScapegoatCaseIndex"]()
    present = set()
    for key in layout_rng.choices(range(90), k=130):
        assert index.insert(key) is (key not in present)
        present.add(key)
        assert index.ordered_ids() == sorted(present)

        def audit(node, low=None, high=None):
            if node is None:
                return 0, 0
            assert (low is None or low < node.case_id) and (high is None or node.case_id < high)
            left_count, left_height = audit(node.left, low, node.case_id)
            right_count, right_height = audit(node.right, node.case_id, high)
            assert node.size == 1 + left_count + right_count
            return node.size, 1 + max(left_height, right_height)

        count, height = audit(index.root)
        assert count == len(present)
        assert height - 1 <= math.floor(math.log(max(1, count), 1.5)) + 1
        checks += 1

xor_scope, _ = namespace("dsa/static-xor-filter-membership")
for count in range(0, 110):
    keys = layout_rng.sample(range(10000), count)
    filter_index = xor_scope["StaticAlertXorFilter"](keys)
    assert all(filter_index.possibly_contains(key) for key in keys)
    assert len(filter_index.slots) == 0 if count == 0 else len(filter_index.slots) >= count
    checks += 1

new_rng = random.Random(6404)
pal_scope, _ = namespace("dsa/palindromic-tree-online-distinct-substrings")
for trial in range(18):
    index = pal_scope["PalindromicIncidentTree"]()
    text_so_far = ""
    for _ in range(45):
        text_so_far += new_rng.choice("abca")
        index.append(text_so_far[-1])
        oracle = Counter(text_so_far[left:right] for left in range(len(text_so_far))
                         for right in range(left + 1, len(text_so_far) + 1)
                         if text_so_far[left:right] == text_so_far[left:right][::-1])
        assert index.distinct_count() == len(oracle)
        assert index.longest_length() == max(map(len, oracle), default=0)
        assert sorted(index.occurrence_counts().values()) == sorted(oracle.values())
        checks += 1

beats_scope, _ = namespace("dsa/segment-tree-beats-range-cap-sum")
for trial in range(18):
    direct = [new_rng.randrange(-40, 120) for _ in range(37)]
    tree = beats_scope["CapacityCapTree"](direct)
    for _ in range(140):
        left, right = sorted(new_rng.sample(range(len(direct) + 1), 2))
        if new_rng.randrange(3):
            limit = new_rng.randrange(-60, 110)
            tree.cap(left, right, limit)
            direct[left:right] = [min(value, limit) for value in direct[left:right]]
        else:
            assert tree.sum_range(left, right) == sum(direct[left:right])
        assert tree.sum_range(0, len(direct)) == sum(direct)
        assert tree.maximum[1] == max(direct)
        checks += 1

matrix_scope, _ = namespace("dsa/wavelet-matrix-static-rank-quantile")
for trial in range(35):
    values = [new_rng.randrange(0, 256) for _ in range(new_rng.randrange(1, 80))]
    matrix = matrix_scope["AlertWaveletMatrix"](values)
    for _ in range(90):
        left = new_rng.randrange(len(values))
        right = new_rng.randrange(left + 1, len(values) + 1)
        rank = new_rng.randrange(right - left)
        target = new_rng.randrange(0, 300)
        assert matrix.kth(left, right, rank) == sorted(values[left:right])[rank]
        assert matrix.frequency(target, left, right) == values[left:right].count(target)
        checks += 1

window_scope, _ = namespace("dsa/two-stack-sliding-window-aggregation")
for trial in range(20):
    window = window_scope["CalibrationWindow"]()
    direct = deque()
    for _ in range(180):
        if direct and new_rng.randrange(3) == 0:
            assert window.remove_oldest() == direct.popleft()
        else:
            transform = (new_rng.randrange(1, 97), new_rng.randrange(97))
            direct.append(transform)
            window.append(transform)
        combined = window_scope["IDENTITY"]
        for transform in direct:
            combined = window_scope["compose"](combined, transform)
        assert window.combined() == combined
        checks += 1

linear_scope, _ = namespace("dsa/linear-hashing-incremental-bucket-splits")
for trial in range(22):
    index = linear_scope["LinearCaseIndex"](bucket_capacity=2)
    direct = set()
    for _ in range(170):
        key = new_rng.randrange(0, 130)
        if new_rng.randrange(3):
            assert index.insert(key) is (key not in direct)
            direct.add(key)
        else:
            assert index.remove(key) is (key in direct)
            direct.discard(key)
        assert index.size == len(direct)
        assert set().union(*index.buckets) == direct
        assert all(index.bucket_for(stored) == position for position, bucket in enumerate(index.buckets)
                   for stored in bucket)
        checks += 1

grid_scope, _ = namespace("dsa/offline-coordinate-fenwick-rectangle-counts")
for trial in range(25):
    possible = new_rng.sample([(x, y) for x in range(-6, 7) for y in range(-6, 7)], 40)
    grid = grid_scope["DepotPresenceGrid"](possible)
    active = set()
    for _ in range(140):
        point = new_rng.choice(possible)
        enabled = bool(new_rng.randrange(2))
        assert grid.set_present(*point, enabled) is ((point in active) != enabled)
        if enabled:
            active.add(point)
        else:
            active.discard(point)
        x_low, x_high = sorted(new_rng.sample(range(-8, 9), 2))
        y_low, y_high = sorted(new_rng.sample(range(-8, 9), 2))
        assert grid.rectangle_count(x_low, x_high, y_low, y_high) == sum(
            x_low <= x < x_high and y_low <= y < y_high for x, y in active)
        checks += 1

queue_scope, _ = namespace("dsa/persistent-two-list-fifo-queue")
for trial in range(20):
    versions = [(queue_scope["VersionedDispatchQueue"](), [])]
    for _ in range(120):
        old_queue, old_values = new_rng.choice(versions)
        if old_values and new_rng.randrange(2):
            removed, next_queue = old_queue.dequeue()
            assert removed == old_values[0]
            next_values = old_values[1:]
        else:
            key = new_rng.randrange(200)
            next_queue = old_queue.enqueue(key)
            next_values = old_values + [key]
        assert old_queue.values() == old_values
        assert next_queue.values() == next_values
        assert next_queue.count == len(next_values)
        versions.append((next_queue, next_values))
        checks += 1

paren_scope, _ = namespace("dsa/balanced-parentheses-static-tree-navigation")


def _ancestor_chain(node, parent):
    while node is not None:
        yield node
        node = parent[node]


for size in range(1, 75):
    children = {node: [] for node in range(size)}
    parent = {0: None}
    for node in range(1, size):
        parent[node] = new_rng.randrange(node)
        children[parent[node]].append(node)
    tree = paren_scope["OrganizationParentheses"](0, children)
    assert len(tree.sequence) == 2 * size
    for _ in range(90):
        first = new_rng.randrange(size)
        second = new_rng.randrange(size)
        ancestors = set()
        cursor = first
        while cursor is not None:
            ancestors.add(cursor)
            cursor = parent[cursor]
        cursor = second
        while cursor not in ancestors:
            cursor = parent[cursor]
        assert tree.lowest_common_unit(first, second) == cursor
        assert tree.contains_descendant(first, second) is (first in {
            ancestor for ancestor in _ancestor_chain(second, parent)})
        checks += 1
    for node in range(size):
        assert tree.subtree_size(node) == sum(tree.contains_descendant(node, other) for other in range(size))

third_rng = random.Random(7413)
bk_scope, _ = namespace("dsa/bk-tree-edit-distance-label-search")
for trial in range(28):
    labels = set()
    index = bk_scope["IncidentLabelBKTree"]()
    for _ in range(65):
        label = "".join(third_rng.choices("abcd", k=third_rng.randrange(2, 7)))
        assert index.insert(label) is (label not in labels)
        labels.add(label)
    for _ in range(65):
        query = "".join(third_rng.choices("abcd", k=third_rng.randrange(2, 7)))
        radius = third_rng.randrange(4)
        expected = sorted((bk_scope["edit_distance"](query, label), label) for label in labels
                          if bk_scope["edit_distance"](query, label) <= radius)
        assert index.within(query, radius) == expected
        checks += 1

vantage_scope, _ = namespace("dsa/vantage-point-metric-nearest-depot")
for size in range(0, 85):
    depots = [(f"depot-{node}", (third_rng.randrange(-50, 51), third_rng.randrange(-50, 51)))
              for node in range(size)]
    index = vantage_scope["DepotVantageTree"](depots)
    for _ in range(45):
        target = (third_rng.randrange(-50, 51), third_rng.randrange(-50, 51))
        expected = min(((abs(point[0] - target[0]) + abs(point[1] - target[1]), depot_id)
                        for depot_id, point in depots), default=None)
        assert index.nearest(target) == (None if expected is None else (expected[1], expected[0]))
        checks += 1

centroid_scope, _ = namespace("dsa/centroid-decomposition-nearest-marked-depot")
euler_scope, _ = namespace("dsa/euler-tour-rmq-constant-query-lca")
for size in range(1, 95):
    parent = [-1] + [third_rng.randrange(node) for node in range(1, size)]
    roads = [(node, parent[node]) for node in range(1, size)]
    adjacent = [[] for _ in range(size)]
    for first, second in roads:
        adjacent[first].append(second)
        adjacent[second].append(first)
    distances = []
    for source in range(size):
        row = [-1] * size
        row[source] = 0
        pending = deque([source])
        while pending:
            current = pending.popleft()
            for neighbor in adjacent[current]:
                if row[neighbor] == -1:
                    row[neighbor] = row[current] + 1
                    pending.append(neighbor)
        distances.append(row)
    marked = set()
    centroid = centroid_scope["MarkedDepotCentroids"](size, roads)
    euler = euler_scope["DepotEulerAncestorIndex"](size, roads)
    assert len(euler.euler) == 2 * size - 1
    for _ in range(95):
        first = third_rng.randrange(size)
        second = third_rng.randrange(size)
        if third_rng.randrange(2):
            assert centroid.mark(first) is (first not in marked)
            marked.add(first)
        assert centroid.nearest_marked_distance(second) == min(
            (distances[second][depot] for depot in marked), default=None)
        first_ancestors = set(_ancestor_chain(first, {node: (None if value == -1 else value)
                                                      for node, value in enumerate(parent)}))
        cursor = second
        while cursor not in first_ancestors:
            cursor = parent[cursor]
        assert euler.lowest_common_depot(first, second) == cursor
        assert euler.road_distance(first, second) == distances[first][second]
        checks += 1

perfect_scope, _ = namespace("dsa/two-level-perfect-hashing-static-case-ids")
for size in range(0, 145):
    keys = set(third_rng.sample(range(20000), size))
    index = perfect_scope["StaticCasePerfectHash"](keys)
    assert index.count == len(keys)
    assert index.allocated_slots() <= max(1, 4 * len(keys)) + len(keys)
    for key in keys:
        assert index.contains(key)
    for _ in range(70):
        key = third_rng.randrange(20000)
        assert index.contains(key) is (key in keys)
        checks += 1

fm_scope, _ = namespace("dsa/fm-index-backward-substring-search")
for size in range(0, 105):
    text_value = "".join(third_rng.choices("abcd", k=size))
    index = fm_scope["IncidentFMIndex"](text_value)
    for _ in range(45):
        pattern = "".join(third_rng.choices("abcde", k=third_rng.randrange(1, 6)))
        expected = [position for position in range(size) if text_value.startswith(pattern, position)]
        assert index.positions(pattern) == expected
        assert index.count(pattern) == len(expected)
        checks += 1

block_scope, _ = namespace("dsa/block-max-postings-exact-topk-pruning")
for trial in range(300):
    documents = {document_id: {term: third_rng.randrange(1, 14) for term in "abcd" if third_rng.randrange(2)}
                 for document_id in third_rng.sample(range(130), third_rng.randrange(1, 100))}
    index = block_scope["BlockMaxIncidentScores"](documents, block_width=third_rng.randrange(1, 17))
    terms = third_rng.sample(list("abcd"), third_rng.randrange(1, 5))
    limit = third_rng.randrange(1, 12)
    expected = sorted(((sum(weights.get(term, 0) for term in terms), document_id)
                       for document_id, weights in documents.items()
                       if sum(weights.get(term, 0) for term in terms)), key=lambda item: (-item[0], item[1]))[:limit]
    actual, skipped = index.top_k(terms, limit)
    assert actual == expected and skipped >= 0
    checks += 1

rank_scope, _ = namespace("dsa/piecewise-interpolation-rank-catalog")
for size in range(0, 105):
    keys = sorted(third_rng.sample(range(1000), size))
    index = rank_scope["PiecewiseCaseRank"](keys, block_width=third_rng.randrange(2, 16))
    for target in range(-5, 1005, 3):
        assert index.lower_bound(target) == bisect.bisect_left(keys, target)
        checks += 1

fourth_rng = random.Random(8947)
xfast_scope, _ = namespace("dsa/x-fast-trie-static-case-predecessor")
for width in range(1, 11):
    universe = 1 << width
    for _ in range(25):
        keys = sorted(fourth_rng.sample(range(universe), fourth_rng.randrange(min(universe, 30) + 1)))
        index = xfast_scope["StaticXFastCases"](keys, width)
        for target in range(universe):
            floor_position = bisect.bisect_right(keys, target)
            ceiling_position = bisect.bisect_left(keys, target)
            assert index.floor(target) == (keys[floor_position - 1] if floor_position else None)
            assert index.ceiling(target) == (keys[ceiling_position] if ceiling_position < len(keys) else None)
            checks += 1

vector_scope, _ = namespace("dsa/persistent-radix-vector-path-copying")
vector = vector_scope["CaseVector"]()
revisions = []
for position in range(240):
    revisions.append(vector)
    vector = vector.append(position + 19)
    if position > 0 and position % 7 == 0:
        branch = vector.replace(position // 2, -position)
        assert branch.at(position // 2) == -position
        assert vector.at(position // 2) == position // 2 + 19
    checks += 1
for position, revision in enumerate(revisions):
    assert revision.values() == list(range(19, 19 + position))
    checks += 1

suffix_scope, _ = namespace("dsa/static-compressed-suffix-tree-pattern-locations")
for length in range(32):
    for _ in range(25):
        incident_text = "".join(fourth_rng.choices("abc", k=length))
        index = suffix_scope["StaticSuffixTree"](incident_text)
        for _ in range(14):
            pattern = "".join(fourth_rng.choices("abcd", k=fourth_rng.randrange(1, 7)))
            assert index.locate(pattern) == [
                position for position in range(length) if incident_text.startswith(pattern, position)]
            checks += 1

window_scope, _ = namespace("dsa/disjoint-interval-union-maintenance-windows")
for _ in range(80):
    windows = window_scope["MaintenanceWindows"]()
    covered = set()
    for _ in range(55):
        start = fourth_rng.randrange(60)
        end = fourth_rng.randrange(start + 1, 62)
        if fourth_rng.randrange(2):
            windows.add(start, end)
            covered.update(range(start, end))
        else:
            windows.remove(start, end)
            covered.difference_update(range(start, end))
        assert windows.covered_length() == len(covered)
        assert all(windows.contains(instant) is (instant in covered) for instant in range(62))
        assert all(windows.windows[index][1] < windows.windows[index + 1][0]
                   for index in range(len(windows.windows) - 1))
        checks += 1

overlay_scope, _ = namespace("dsa/csr-delta-overlay-graph-updates")
for _ in range(80):
    roads = {(source, target) for source in range(9) for target in range(9) if fourth_rng.randrange(7) == 0}
    graph = overlay_scope["RoadGraphOverlay"](9, roads)
    for step in range(45):
        source, target = fourth_rng.randrange(9), fourth_rng.randrange(9)
        if fourth_rng.randrange(2):
            graph.add_road(source, target)
            roads.add((source, target))
        else:
            graph.remove_road(source, target)
            roads.discard((source, target))
        if step % 11 == 0:
            graph.compact()
        assert all(graph.neighbors(vertex) == sorted(destination for start, destination in roads if start == vertex)
                   for vertex in range(9))
        checks += 1

reach_scope, _ = namespace("dsa/bitset-transitive-reachability-snapshot")
for size in range(1, 18):
    for _ in range(16):
        roads = {(source, target) for source in range(size) for target in range(size)
                 if fourth_rng.randrange(8) == 0}
        index = reach_scope["ReachabilitySnapshot"](size, roads)
        for source in range(size):
            seen = {source}
            pending = [source]
            for vertex in pending:
                for start, target in roads:
                    if start == vertex and target not in seen:
                        seen.add(target)
                        pending.append(target)
            assert index.reachable_from(source) == sorted(seen)
            checks += 1

labels_scope, _ = namespace("dsa/gap-label-order-maintenance")
for _ in range(45):
    order = labels_scope["DispatchOrder"]([0, 1])
    expected = [0, 1]
    for task in range(2, 75):
        anchor = fourth_rng.choice(expected)
        order.insert_after(anchor, task)
        expected.insert(expected.index(anchor) + 1, task)
        assert order.tasks == expected
        assert all(order.before(expected[index], expected[index + 1])
                   for index in range(len(expected) - 1))
        checks += 1

skew_scope, _ = namespace("dsa/skew-heap-self-adjusting-meld")
for _ in range(120):
    heaps = [skew_scope["DispatchSkewHeap"](), skew_scope["DispatchSkewHeap"]()]
    expected = []
    for task in range(75):
        priority = fourth_rng.randrange(130)
        task_id = f"task-{task}"
        heaps[fourth_rng.randrange(2)].push(priority, task_id)
        expected.append((priority, task_id))
    heaps[0].merge_from(heaps[1])
    assert heaps[1].size == 0
    assert [heaps[0].pop() for _ in range(75)] == sorted(expected)
    checks += 1

fifth_rng = random.Random(52847)
fib_scope, _ = namespace("dsa/fibonacci-heap-cascading-cuts")
for trial in range(75):
    heap = fib_scope["FibonacciDispatchHeap"]()
    live = {}
    next_id = 0
    for _ in range(125):
        operation = fifth_rng.randrange(3)
        if operation == 0 or not live:
            task_id = f"T-{trial}-{next_id}"
            next_id += 1
            priority = fifth_rng.randrange(-80, 240)
            heap.insert(task_id, priority)
            live[task_id] = priority
        elif operation == 1:
            task_id = fifth_rng.choice(list(live))
            priority = live[task_id] - fifth_rng.randrange(35)
            heap.decrease(task_id, priority)
            live[task_id] = priority
        else:
            expected = min((priority, task_id) for task_id, priority in live.items())
            assert heap.pop_minimum() == expected
            del live[expected[1]]
        assert len(heap.handles) == len(live)
        if live:
            assert (heap.minimum.priority, heap.minimum.task_id) == min(
                (priority, task_id) for task_id, priority in live.items())
        checks += 1

merge_scope, _ = namespace("dsa/tournament-tree-kway-run-merge")
for _ in range(300):
    runs = [sorted(fifth_rng.randrange(45) for _ in range(fifth_rng.randrange(22)))
            for _ in range(fifth_rng.randrange(14))]
    expected = sorted((value, run_id) for run_id, run in enumerate(runs) for value in run)
    assert merge_scope["TournamentMerge"](runs).drain() == expected
    checks += 1

spatial_scope, _ = namespace("dsa/priority-search-tree-three-sided-events")
for size in range(0, 85):
    events = [(f"E-{point}", fifth_rng.randrange(-30, 31), fifth_rng.randrange(-30, 31))
              for point in range(size)]
    index = spatial_scope["DepotPrioritySearch"](events)
    for _ in range(50):
        left, right = sorted((fifth_rng.randrange(-35, 36), fifth_rng.randrange(-35, 36)))
        limit = fifth_rng.randrange(-35, 36)
        assert index.three_sided(left, right, limit) == sorted(
            point for point in events if left <= point[1] <= right and point[2] <= limit)
        checks += 1

decision_scope, _ = namespace("dsa/reduced-ordered-decision-diagram-rules")
for variable_count in range(1, 7):
    variables = [f"flag-{index}" for index in range(variable_count)]
    for _ in range(45):
        truth = {key: fifth_rng.randrange(2) for key in range(1 << variable_count)}
        def predicate(flags):
            return truth[sum(int(flags[name]) << position for position, name in enumerate(variables))]
        diagram = decision_scope["DispatchRuleDiagram"](variables, predicate)
        for key, expected in truth.items():
            flags = {name: bool(key & (1 << position)) for position, name in enumerate(variables)}
            assert diagram.permits(flags) is bool(expected)
            checks += 1

lz_scope, _ = namespace("dsa/lz78-phrase-trie-incident-compression")
for length in range(0, 150):
    for _ in range(10):
        incident = "".join(fifth_rng.choices("abcde", k=length))
        tokens = lz_scope["encode_incident"](incident)
        assert lz_scope["decode_incident"](tokens) == incident
        checks += 1

stabbing_scope, _ = namespace("dsa/segment-tree-interval-stabbing-index")
for _ in range(70):
    index = stabbing_scope["StabbingWindows"](40)
    active = {}
    for step in range(75):
        if active and fifth_rng.randrange(3) == 0:
            task_id = fifth_rng.choice(list(active))
            index.remove(task_id)
            del active[task_id]
        else:
            start = fifth_rng.randrange(40)
            end = fifth_rng.randrange(start + 1, 41)
            task_id = f"M-{step}"
            index.add(task_id, start, end)
            active[task_id] = start, end
        for instant in range(40):
            assert index.active_at(instant) == sorted(
                task_id for task_id, (start, end) in active.items() if start <= instant < end)
        checks += 1

huffman_scope, _ = namespace("dsa/huffman-prefix-code-tree")
for length in range(1, 140):
    training = "".join(fifth_rng.choices("abcdef", k=length))
    codebook = huffman_scope["IncidentCodebook"](training)
    codes = list(codebook.codes.values())
    assert all(not first.startswith(second) for index, first in enumerate(codes)
               for other, second in enumerate(codes) if index != other)
    for _ in range(18):
        payload = "".join(fifth_rng.choices(sorted(set(training)), k=fifth_rng.randrange(28)))
        assert codebook.decode(codebook.encode(payload)) == payload
        checks += 1

condensation_scope, _ = namespace("dsa/scc-condensation-reachability-index")
for size in range(1, 27):
    for _ in range(32):
        roads = {(source, target) for source in range(size) for target in range(size)
                 if fifth_rng.randrange(8) == 0}
        index = condensation_scope["CondensedRoutes"](size, roads)
        for source in range(size):
            reached = {source}
            pending = [source]
            for vertex in pending:
                for start, target in roads:
                    if start == vertex and target not in reached:
                        reached.add(target)
                        pending.append(target)
            assert all(index.reaches(source, target) is (target in reached) for target in range(size))
            checks += 1

sixth_rng = random.Random(61947)
treap_scope, _ = namespace("dsa/ordered-treap-split-join-rank")


def audit_ordered_treap(node, lower, upper, parent_priority):
    if node is None:
        return 0
    assert lower < node.key < upper
    assert node.priority <= parent_priority
    size = 1 + audit_ordered_treap(node.left, lower, node.key, node.priority)
    size += audit_ordered_treap(node.right, node.key, upper, node.priority)
    assert node.size == size
    return size


for trial in range(45):
    root_node = None
    live_keys = set()
    for _ in range(90):
        depot_key = sixth_rng.randrange(150)
        if sixth_rng.randrange(3) == 0:
            root_node, removed = treap_scope["remove"](root_node, depot_key)
            assert removed is (depot_key in live_keys)
            live_keys.discard(depot_key)
        else:
            root_node = treap_scope["insert"](root_node, depot_key, sixth_rng.getrandbits(48))
            live_keys.add(depot_key)
        boundary = sixth_rng.randrange(151)
        lower, upper = treap_scope["split"](root_node, boundary)
        assert treap_scope["ordered"](lower) == sorted(key for key in live_keys if key < boundary)
        assert treap_scope["ordered"](upper) == sorted(key for key in live_keys if key >= boundary)
        root_node = treap_scope["join"](lower, upper)
        assert treap_scope["count"](root_node) == len(live_keys)
        assert audit_ordered_treap(root_node, -1, 151, float("inf")) == len(live_keys)
        if live_keys:
            position = sixth_rng.randrange(len(live_keys))
            assert treap_scope["select"](root_node, position) == sorted(live_keys)[position]
        checks += 1

ranked_scope, _ = namespace("dsa/span-skip-list-rank-select")
for trial in range(35):
    index = ranked_scope["RankedAlertIndex"](seed=trial)
    expected_ids = set()
    for _ in range(130):
        alert_id = sixth_rng.randrange(170)
        if sixth_rng.randrange(3) == 0:
            assert index.discard(alert_id) is (alert_id in expected_ids)
            expected_ids.discard(alert_id)
        else:
            assert index.add(alert_id) is (alert_id not in expected_ids)
            expected_ids.add(alert_id)
        ordered_ids = sorted(expected_ids)
        assert index.ordered() == ordered_ids
        assert index.length == len(ordered_ids)
        probe = sixth_rng.randrange(170)
        assert index.rank(probe) == bisect.bisect_left(ordered_ids, probe)
        if ordered_ids:
            position = sixth_rng.randrange(len(ordered_ids))
            assert index.select(position) == ordered_ids[position]
        checks += 1

grid_scope, _ = namespace("dsa/two-dimensional-segment-tree-heat-grid")
for _ in range(35):
    rows, columns = sixth_rng.randrange(1, 9), sixth_rng.randrange(1, 9)
    cells = [[sixth_rng.randrange(-50, 90) for _ in range(columns)] for _ in range(rows)]
    index = grid_scope["HeatGrid"](cells)
    for _ in range(75):
        if sixth_rng.randrange(2):
            row, column = sixth_rng.randrange(rows), sixth_rng.randrange(columns)
            value = sixth_rng.randrange(-50, 90)
            cells[row][column] = value
            index.replace(row, column, value)
        top, bottom = sorted((sixth_rng.randrange(rows + 1), sixth_rng.randrange(rows + 1)))
        left, right = sorted((sixth_rng.randrange(columns + 1), sixth_rng.randrange(columns + 1)))
        assert index.rectangle_sum(top, bottom, left, right) == sum(
            cells[row][column] for row in range(top, bottom) for column in range(left, right))
        checks += 1

alias_scope, _ = namespace("dsa/alias-table-weighted-dispatch")
for _ in range(45):
    weights = [sixth_rng.randrange(0, 50) for _ in range(sixth_rng.randrange(1, 15))]
    if not any(weights):
        weights[0] = 1
    sampler = alias_scope["DispatchSampler"]({index: weight for index, weight in enumerate(weights)})
    samples = Counter(sampler.pick_from_unit((position + .5) / 20000) for position in range(20000))
    for index, weight in enumerate(weights):
        assert abs(samples[index] / 20000 - weight / sum(weights)) < .003
        checks += 1

minhash_scope, _ = namespace("dsa/minhash-banded-incident-candidates")
for _ in range(55):
    index = minhash_scope["IncidentCandidateIndex"](4, 3)
    records = {}
    for incident_id in range(35):
        tokens = {f"token-{number}" for number in range(30) if sixth_rng.randrange(4) == 0}
        if not tokens:
            tokens = {"fallback"}
        index.add(incident_id, tokens)
        records[incident_id] = tokens
    query_tokens = sixth_rng.choice(list(records.values()))
    actual = index.query(query_tokens, .45)
    assert all(len(query_tokens & records[incident_id]) / len(query_tokens | records[incident_id]) >= .45
               for incident_id, _ in actual)
    assert any(incident_id in [item[0] for item in actual] for incident_id, tokens in records.items()
               if tokens == query_tokens)
    checks += 1

bitmap_scope, _ = namespace("dsa/run-length-bitmap-set-algebra")
for _ in range(450):
    first_runs = [(sixth_rng.randrange(80), sixth_rng.randrange(81, 160)) for _ in range(8)]
    second_runs = [(sixth_rng.randrange(80), sixth_rng.randrange(81, 160)) for _ in range(8)]
    first = bitmap_scope["AlertBitmap"](first_runs)
    second = bitmap_scope["AlertBitmap"](second_runs)
    first_set = {value for start, end in first_runs for value in range(start, end)}
    second_set = {value for start, end in second_runs for value in range(start, end)}
    for result, expected in ((first.union(second), first_set | second_set),
                             (first.intersection(second), first_set & second_set),
                             (first.difference(second), first_set - second_set)):
        assert result.cardinality() == len(expected)
        assert all(result.contains(value) is (value in expected) for value in range(160))
        checks += 1

majority_scope, _ = namespace("dsa/verified-range-majority-candidates")
for _ in range(90):
    values = [sixth_rng.randrange(7) for _ in range(sixth_rng.randrange(0, 65))]
    index = majority_scope["MajorityWindowIndex"](values)
    for _ in range(75):
        start, end = sorted((sixth_rng.randrange(len(values) + 1), sixth_rng.randrange(len(values) + 1)))
        observed = index.majority(start, end)
        expected = next((value for value, count in Counter(values[start:end]).items()
                         if 2 * count > end - start), None)
        assert observed == expected
        checks += 1

seventh_rng = random.Random(72947)
move_scope, _ = namespace("dsa/moveable-disjoint-set-shipment-groups")
for size in range(1, 13):
    for _ in range(22):
        index = move_scope["MoveableWarehouseGroups"](size)
        group_labels = list(range(size))
        for _ in range(70):
            source, target = seventh_rng.randrange(size), seventh_rng.randrange(size)
            if seventh_rng.randrange(2):
                index.merge(source, target)
                source_label, target_label = group_labels[source], group_labels[target]
                group_labels = [source_label if label == target_label else label for label in group_labels]
            else:
                index.move(source, target)
                group_labels[source] = group_labels[target]
            for shipment in range(size):
                members = [member for member, label in enumerate(group_labels)
                           if label == group_labels[shipment]]
                assert index.group(shipment) == (len(members), sum(members))
            checks += 1

block_scope, _ = namespace("dsa/block-cut-tree-articulation-depots")


def component_count_without(vertex_count, roads, missing=None):
    unseen = set(range(vertex_count)) - {missing}
    components = 0
    while unseen:
        components += 1
        pending = [unseen.pop()]
        for vertex in pending:
            for neighbor in list(unseen):
                if (min(vertex, neighbor), max(vertex, neighbor)) in roads:
                    unseen.remove(neighbor)
                    pending.append(neighbor)
    return components


for size in range(1, 13):
    for _ in range(55):
        roads = {(source, target) for source in range(size) for target in range(source + 1, size)
                 if seventh_rng.randrange(4) == 0}
        index = block_scope["DepotBlockCutIndex"](size, roads)
        baseline = component_count_without(size, roads)
        expected = {vertex for vertex in range(size)
                    if component_count_without(size, roads, vertex) > baseline}
        assert index.articulations == expected
        assert all(sum(source in block and target in block for block in index.blocks) == 1
                   for source, target in roads)
        checks += 1

bottleneck_scope, _ = namespace("dsa/kruskal-reconstruction-bottleneck-index")
for size in range(1, 13):
    for _ in range(55):
        roads = [(seventh_rng.randrange(1, 120), source, target)
                 for source in range(size) for target in range(source + 1, size)
                 if seventh_rng.randrange(3) == 0]
        index = bottleneck_scope["BottleneckRouteTree"](size, roads)
        unreachable = 10**9
        distances = [[0 if source == target else unreachable for target in range(size)]
                     for source in range(size)]
        for weight, source, target in roads:
            distances[source][target] = distances[target][source] = min(distances[source][target], weight)
        for middle in range(size):
            for source in range(size):
                for target in range(size):
                    distances[source][target] = min(
                        distances[source][target], max(distances[source][middle], distances[middle][target]))
        for source in range(size):
            for target in range(size):
                expected = None if distances[source][target] == unreachable else distances[source][target]
                assert index.bottleneck(source, target) == expected
                checks += 1

family_scope, _ = namespace("dsa/zero-suppressed-diagram-dispatch-set-families")
for size in range(0, 9):
    universe = tuple(range(size))
    for _ in range(50):
        family = {frozenset(item for item in universe if seventh_rng.randrange(2))
                  for _ in range(seventh_rng.randrange(55))}
        index = family_scope["DispatchSetFamily"](universe, family)
        assert index.family_size() == len(family)
        for mask in range(1 << size):
            selection = {item for item in universe if mask & (1 << item)}
            assert index.contains(selection) is (frozenset(selection) in family)
            checks += 1

signed_scope, _ = namespace("dsa/count-sketch-signed-incident-frequencies")
for _ in range(150):
    index = signed_scope["SignedIncidentSketch"](41, 5)
    original = [row[:] for row in index.counters]
    changes = [(f"incident-{seventh_rng.randrange(90)}", seventh_rng.randrange(-35, 45))
               for _ in range(85)]
    for incident_key, change in changes:
        index.adjust(incident_key, change)
    for incident_key, change in changes:
        index.adjust(incident_key, -change)
    assert index.counters == original
    checks += 1

histogram_scope, _ = namespace("dsa/exponential-histogram-recent-failure-count")
for window_width in range(1, 45):
    for _ in range(25):
        index = histogram_scope["RecentFailureHistogram"](window_width)
        events = []
        for _ in range(90):
            failed = seventh_rng.randrange(2)
            events.append(failed)
            index.append(failed)
            exact = sum(events[-window_width:])
            assert abs(index.estimate() - exact) <= index.uncertainty() + 1e-9
            assert max(Counter(bucket[0] for bucket in index.buckets).values(), default=0) <= 2
            checks += 1

mode_scope, _ = namespace("dsa/square-root-range-mode-readings")
for size in range(0, 80):
    for _ in range(14):
        readings = [seventh_rng.randrange(-6, 8) for _ in range(size)]
        index = mode_scope["StaticReadingModes"](readings)
        for _ in range(45):
            start, stop = sorted((seventh_rng.randrange(size + 1), seventh_rng.randrange(size + 1)))
            frequency = Counter(readings[start:stop])
            expected = min((reading for reading in frequency
                            if frequency[reading] == max(frequency.values())), default=None)
            assert index.mode(start, stop) == expected
            checks += 1

eighth_rng = random.Random(381904)
double_scope, _ = namespace("dsa/double-array-trie-static-incident-codes")
for _ in range(110):
    codes = {"".join(eighth_rng.choices("abcd0123", k=eighth_rng.randrange(1, 8)))
             for _ in range(eighth_rng.randrange(1, 35))}
    index = double_scope["IncidentCodeIndex"](codes)
    prefixes = {code[:length] for code in codes for length in range(len(code) + 1)}
    for _ in range(55):
        candidate = "".join(eighth_rng.choices("abcd0123", k=eighth_rng.randrange(0, 8)))
        assert index.contains(candidate) == (candidate in codes)
        assert index.has_prefix(candidate) == (candidate in prefixes)
        checks += 1

hop_scope, _ = namespace("dsa/hopscotch-hash-shipment-neighborhoods")
for _ in range(80):
    index = hop_scope["ShipmentNeighborhoodSet"](53, 8)
    expected = set()
    for _ in range(130):
        shipment_id = eighth_rng.randrange(400)
        if eighth_rng.randrange(3):
            if index.add(shipment_id):
                expected.add(shipment_id)
        else:
            assert index.discard(shipment_id) == (shipment_id in expected)
            expected.discard(shipment_id)
        observed = {key for key in index.slots if key is not None}
        assert observed == expected and index.count == len(expected)
        assert all(index._distance(index._home(key), slot) < index.neighborhood
                   for slot, key in enumerate(index.slots) if key is not None)
        assert all(index.contains(key) for key in expected)
        checks += 1

iblt_scope, _ = namespace("dsa/invertible-bloom-replica-set-reconciliation")
for _ in range(180):
    shared = set(eighth_rng.sample(range(10000), 18))
    available = list(set(range(10000)) - shared)
    differences = eighth_rng.sample(available, 6)
    left = shared | set(differences[:3])
    right = shared | set(differences[3:])
    index = iblt_scope["ReplicaDifferenceTable"](101, 3)
    for incident_id in left:
        index.adjust(incident_id, 1)
    for incident_id in right:
        index.adjust(incident_id, -1)
    assert index.decode() == (left - right, right - left)
    checks += 1

unitig_scope, _ = namespace("dsa/de-bruijn-graph-unitig-kmer-index")
for _ in range(180):
    kmers = {"".join(eighth_rng.choices("ACGT", k=3)) for _ in range(eighth_rng.randrange(1, 50))}
    index = unitig_scope["KmerRouteIndex"](kmers)
    recovered = [path[offset:offset + index.k]
                 for path in index.unitigs() for offset in range(len(path) - index.k + 1)]
    assert Counter(recovered) == Counter(kmers)
    checks += 1

ninth_rng = random.Random(395071)
radix_scope, _ = namespace("dsa/adaptive-radix-node-fanout-incident-codes")
for _ in range(85):
    index = radix_scope["AdaptiveIncidentCodes"]()
    expected = {}
    for _ in range(75):
        key = bytes(ninth_rng.randrange(36) for _ in range(ninth_rng.randrange(0, 7)))
        value = ninth_rng.randrange(1, 100000)
        index.insert(key, value)
        expected[key] = value
        assert all(index.lookup(old_key) == old_value for old_key, old_value in expected.items())
        assert index.lookup(bytes([255, 254, 253])) is None
        checks += 1
    stack = [index.root]
    while stack:
        node = stack.pop()
        assert node.count == len(node.items()) and node.count <= node.tier
        assert len({label for label, _ in node.items()}) == node.count
        stack.extend(child for _, child in node.items())
        checks += 1

slice_scope, _ = namespace("dsa/bit-sliced-index-sensor-range-filters")
for size in range(0, 73):
    readings = [ninth_rng.randrange(256) for _ in range(size)]
    index = slice_scope["ReadingBitSlices"](readings)
    for _ in range(45):
        if size and ninth_rng.randrange(3) == 0:
            row, value = ninth_rng.randrange(size), ninth_rng.randrange(256)
            readings[row] = value
            index.replace(row, value)
        lower, upper = sorted((ninth_rng.randrange(-15, 270), ninth_rng.randrange(-15, 270)))
        expected = {row for row, value in enumerate(readings) if lower <= value <= upper}
        observed = index.between(lower, upper)
        assert {row for row in range(size) if observed & (1 << row)} == expected
        assert index.sum_selected(observed) == sum(readings[row] for row in expected)
        threshold = ninth_rng.randrange(-15, 270)
        assert index.less_than(threshold) == sum(1 << row for row, value in enumerate(readings)
                                                  if value < threshold)
        checks += 1

simhash_scope, _ = namespace("dsa/simhash-banded-incident-near-duplicates")
for _ in range(65):
    index = simhash_scope["IncidentFingerprintIndex"]()
    features = {}
    for incident_id in range(35):
        tokens = {f"token-{number}": ninth_rng.randrange(1, 5)
                  for number in ninth_rng.sample(range(24), ninth_rng.randrange(1, 7))}
        features[incident_id] = tokens
        index.add(incident_id, tokens)
    for _ in range(15):
        query = features[ninth_rng.randrange(35)] if ninth_rng.randrange(2) else {
            f"token-{number}": ninth_rng.randrange(1, 5)
            for number in ninth_rng.sample(range(24), ninth_rng.randrange(1, 7))}
        threshold = ninth_rng.randrange(8)
        fingerprint = index.fingerprint(query)
        expected = sorted((incident_id, (fingerprint ^ stored).bit_count())
                          for incident_id, stored in index.fingerprints.items()
                          if (fingerprint ^ stored).bit_count() <= threshold)
        assert index.neighbors(query, threshold) == expected
        checks += 1

dag_scope, _ = namespace("dsa/minimal-acyclic-incident-word-dictionary")
for _ in range(105):
    words = {"".join(ninth_rng.choices("abcd", k=ninth_rng.randrange(0, 7)))
             for _ in range(ninth_rng.randrange(0, 65))}
    index = dag_scope["MinimalIncidentDictionary"](words)
    for _ in range(65):
        candidate = "".join(ninth_rng.choices("abcd", k=ninth_rng.randrange(0, 7)))
        assert index.contains(candidate) == (candidate in words)
        checks += 1
    assert len(index.states) <= 1 + sum(len(word) for word in words)
    checks += 1

tenth_rng = random.Random(400193)
mex_scope, _ = namespace("dsa/persistent-range-mex-last-occurrence-index")
for size in range(0, 76):
    readings = [tenth_rng.randrange(-5, size + 9) for _ in range(size)]
    index = mex_scope["PersistentRangeMex"](readings)
    assert len(index.roots) == size + 1
    for _ in range(85):
        start, stop = sorted((tenth_rng.randrange(size + 1), tenth_rng.randrange(size + 1)))
        present = set(readings[start:stop])
        expected = next(candidate for candidate in range(size + 1) if candidate not in present)
        assert index.mex(start, stop) == expected
        checks += 1

xor_scope, _ = namespace("dsa/segment-tree-range-xor-linear-basis")
for size in range(0, 13):
    for _ in range(50):
        flags = [tenth_rng.randrange(256) for _ in range(size)]
        index = xor_scope["RangeXorBasis"](flags, width=8)
        for _ in range(30):
            if size and tenth_rng.randrange(3) == 0:
                position, replacement = tenth_rng.randrange(size), tenth_rng.randrange(256)
                flags[position] = replacement
                index.replace(position, replacement)
            start, stop = sorted((tenth_rng.randrange(size + 1), tenth_rng.randrange(size + 1)))
            segment = flags[start:stop]
            results = {0}
            for value in segment:
                results |= {former ^ value for former in tuple(results)}
            basis = index.basis(start, stop)
            assert basis.maximum() == max(results)
            assert all(basis.can_make(candidate) == (candidate in results) for candidate in range(256))
            assert (1 << basis.rank()) == len(results)
            checks += 1

affine_scope, _ = namespace("dsa/lazy-segment-tree-affine-range-sums")
for size in range(1, 61):
    readings = [tenth_rng.randrange(-500, 500) for _ in range(size)]
    direct = [reading % 1009 for reading in readings]
    index = affine_scope["AffineReadingTree"](readings, 1009)
    for _ in range(65):
        start, stop = sorted((tenth_rng.randrange(size + 1), tenth_rng.randrange(size + 1)))
        if tenth_rng.randrange(2):
            multiply, add = tenth_rng.randrange(-8, 9), tenth_rng.randrange(-90, 91)
            index.transform(start, stop, multiply, add)
            for position in range(start, stop):
                direct[position] = (multiply * direct[position] + add) % 1009
        else:
            assert index.range_sum(start, stop) == sum(direct[start:stop]) % 1009
        checks += 1

minmax_scope, _ = namespace("dsa/min-max-heap-double-ended-dispatch")
for _ in range(90):
    index = minmax_scope["DispatchPriorityEnds"]()
    direct = []
    for _ in range(330):
        operation = tenth_rng.randrange(4)
        if operation < 2 or not direct:
            value = tenth_rng.randrange(-100, 101)
            index.add(value)
            direct.append(value)
        elif operation == 2:
            expected = min(direct)
            assert index.pop_minimum() == expected
            direct.remove(expected)
        else:
            expected = max(direct)
            assert index.pop_maximum() == expected
            direct.remove(expected)
        assert sorted(index.values) == sorted(direct)
        assert index.minimum() == (min(direct) if direct else None)
        assert index.maximum() == (max(direct) if direct else None)
        for position, value in enumerate(index.values):
            if position:
                parent = (position - 1) // 2
                assert (index.values[parent] <= value if index._minimum_level(parent)
                        else index.values[parent] >= value)
        checks += 1

eleventh_rng = random.Random(581)
rank_scope, _ = namespace("dsa/persistent-subarray-kth-order-statistics")
for _ in range(60):
    values = [eleventh_rng.randrange(-20, 35) for _ in range(eleventh_rng.randrange(1, 36))]
    index = rank_scope["ShipmentRankIndex"](values)
    for _ in range(45):
        left = eleventh_rng.randrange(len(values))
        right = eleventh_rng.randrange(left + 1, len(values) + 1)
        rank = eleventh_rng.randrange(1, right - left + 1)
        assert index.kth(left, right, rank) == sorted(values[left:right])[rank - 1]
        checks += 1

burst_scope, _ = namespace("dsa/segment-tree-maximum-subarray-burst")
for _ in range(55):
    values = [eleventh_rng.randrange(-35, 36) for _ in range(eleventh_rng.randrange(1, 28))]
    index = burst_scope["FaultBurstIndex"](values)
    for _ in range(45):
        if eleventh_rng.randrange(3) == 0:
            position = eleventh_rng.randrange(len(values))
            values[position] = eleventh_rng.randrange(-35, 36)
            index.replace(position, values[position])
        left = eleventh_rng.randrange(len(values))
        right = eleventh_rng.randrange(left + 1, len(values) + 1)
        expected = max(sum(values[first:past_last]) for first in range(left, right)
                       for past_last in range(first + 1, right + 1))
        assert index.best_burst(left, right) == expected
        checks += 1

tariff_scope, _ = namespace("dsa/li-chao-tree-interval-limited-line-offers")
for _ in range(55):
    index = tariff_scope["SegmentTariffIndex"](0, 24)
    offers = []
    for _ in range(35):
        left = eleventh_rng.randrange(24)
        right = eleventh_rng.randrange(left + 1, 25)
        slope = eleventh_rng.randrange(-17, 18)
        base = eleventh_rng.randrange(-100, 101)
        index.add_tariff(left, right, slope, base)
        offers.append((left, right, slope, base))
        for minute in range(24):
            candidates = [rate * minute + fixed for start, stop, rate, fixed in offers
                          if start <= minute < stop]
            assert index.minimum_charge(minute) == (min(candidates) if candidates else None)
            checks += 1

bucket_scope, _ = namespace("dsa/all-one-frequency-bucket-counter")
for _ in range(55):
    index = bucket_scope["AlertFrequencyIndex"]()
    direct = {}
    for _ in range(130):
        code = f"dock-{eleventh_rng.randrange(22)}"
        if code in direct and eleventh_rng.randrange(2):
            index.decrement(code)
            direct[code] -= 1
            if direct[code] == 0:
                del direct[code]
        else:
            index.increment(code)
            direct[code] = direct.get(code, 0) + 1
        minimum, maximum = index.minimum(), index.maximum()
        if direct:
            assert direct[minimum] == min(direct.values())
            assert direct[maximum] == max(direct.values())
        else:
            assert minimum is maximum is None
        assert set(index.location) == set(direct)
        checks += 1

route_scope, _ = namespace("dsa/patricia-binary-prefix-routing-index")
for _ in range(55):
    index = route_scope["PatriciaRouteIndex"]()
    direct = {}
    for insertion in range(35):
        network = eleventh_rng.randrange(256)
        length = eleventh_rng.randrange(9)
        destination = f"depot-{insertion}"
        index.insert(network, length, destination)
        direct[(network >> (8 - length) if length else 0, length)] = destination
        for address in range(256):
            matches = [(prefix_length, target) for (prefix, prefix_length), target in direct.items()
                       if (address >> (8 - prefix_length) if prefix_length else 0) == prefix]
            expected = max(matches, key=lambda match: match[0])[1] if matches else None
            assert index.longest_match(address) == expected
            checks += 1

twelfth_rng = random.Random(827)
successor_scope, _ = namespace("dsa/successor-disjoint-set-retired-slots")
for capacity in range(1, 65):
    index = successor_scope["AvailableSlotIndex"](capacity)
    available = set(range(capacity))
    for _ in range(100):
        start = twelfth_rng.randrange(capacity + 1)
        expected = min((bay for bay in available if bay >= start), default=None)
        assert index.next_available(start) == expected
        if twelfth_rng.randrange(2):
            assert index.claim_next(start) == expected
            if expected is not None:
                available.remove(expected)
        else:
            bay = twelfth_rng.randrange(capacity)
            assert index.retire(bay) == (bay in available)
            available.discard(bay)
        checks += 1

distinct_scope, _ = namespace("dsa/persistent-range-distinct-last-position-count")
for _ in range(75):
    codes = [twelfth_rng.randrange(16) for _ in range(twelfth_rng.randrange(1, 48))]
    index = distinct_scope["DistinctIncidentIndex"](codes)
    for _ in range(80):
        left = twelfth_rng.randrange(len(codes) + 1)
        right = twelfth_rng.randrange(left, len(codes) + 1)
        assert index.distinct_count(left, right) == len(set(codes[left:right]))
        checks += 1

fingerprint_scope, _ = namespace("dsa/segment-tree-editable-substring-fingerprints")
for _ in range(55):
    characters = [chr(65 + twelfth_rng.randrange(8)) for _ in range(37)]
    index = fingerprint_scope["AlertTextFingerprint"]("".join(characters))
    for _ in range(75):
        if twelfth_rng.randrange(3) == 0:
            position = twelfth_rng.randrange(len(characters))
            characters[position] = chr(65 + twelfth_rng.randrange(8))
            index.replace(position, characters[position])
        left = twelfth_rng.randrange(len(characters) + 1)
        right = twelfth_rng.randrange(left, len(characters) + 1)
        direct = (0, 0, 0)
        for character in characters[left:right]:
            direct = (direct[0] + 1,
                      (direct[1] * index.BASE + ord(character) + 1) % index.MODULI[0],
                      (direct[2] * index.BASE + ord(character) + 1) % index.MODULI[1])
        assert index.fingerprint(left, right) == direct
        width = twelfth_rng.randrange(len(characters) + 1)
        first = twelfth_rng.randrange(len(characters) - width + 1)
        second = twelfth_rng.randrange(len(characters) - width + 1)
        assert index.possibly_equal(first, second, width) == (
            characters[first:first + width] == characters[second:second + width])
        checks += 1

median_scope, _ = namespace("dsa/sliding-window-median-lazy-heap-expiry")
for _ in range(600):
    waits = [twelfth_rng.randrange(-70, 71) for _ in range(twelfth_rng.randrange(1, 65))]
    width = twelfth_rng.randrange(1, len(waits) + 1)
    expected = [sorted(waits[start:start + width])[(width - 1) // 2]
                for start in range(len(waits) - width + 1)]
    assert median_scope["sliding_lower_medians"](waits, width) == expected
    checks += 1

ball_scope, _ = namespace("dsa/ball-tree-exact-nearest-depot")
for _ in range(85):
    depots = [(f"D-{number}", (twelfth_rng.randrange(-60, 61), twelfth_rng.randrange(-60, 61)))
              for number in range(twelfth_rng.randrange(1, 52))]
    index = ball_scope["DepotBallIndex"](depots)
    for _ in range(36):
        query = (twelfth_rng.randrange(-60, 61), twelfth_rng.randrange(-60, 61))
        expected_distance, expected_id = min((math.dist(query, point), depot_id)
                                             for depot_id, point in depots)
        assert index.nearest(query) == (expected_id, round(expected_distance, 3))
        checks += 1

report = {"passed": True, "checks": checks, "cases": ["Bloom inserted keys", "sparse-set mutations and clear", "skip-list ordered inserts", "B+ leaf separator model", "persistent historical sums", "monotonic window minima", "B-tree insertion and occupancy", "interval overlap search", "compressed-trie insertion", "red-black invariant rejection", "red-black ordered insertion", "multi-level B+ insertion and leaf scan", "AVL interval insertion and overlap", "compressed-trie deletion and merge", "B+ deletion occupancy and leaf links", "indexed heap positions and priority order", "open-addressed deletion and rebuild", "dependency topological order and cycle rejection", "red-black ordered deletion", "AVL interval deletion", "rollback disjoint-set connectivity", "stale-heap shortest paths", "offline connectivity across edge lifetimes", "bounded queue close and drain", "immutable index snapshot publication", "page redo replay", "online connectivity updates", "persistent ordered index versions", "framed journal torn tail and checksum", "CAS queue schedule FIFO", "failure-linked alert matches", "suffix array order and LCP", "k-d nearest depot", "count-min one-sided estimates", "circular dispatch ring", "iterative tree orders", "bitset adjacency symmetry", "AVL subtree rank and select", "sparse coordinate assignments", "wavelet subarray queries", "parity constraints", "implicit treap sequence edits", "bitvector rank and select", "heavy-light path sums", "sorted-run tombstones and compaction", "lazy range minimum", "binary-lifted common managers", "two-dimensional Fenwick rectangles", "Robin Hood deletion shifts"]}
report["cases"].extend(["link-cut forest paths", "online suffix automaton substrings", "piece-table text edits"])
report["cases"].extend(["cuckoo relocation and rebuild", "packed rectangle intersections", "binary trie multiplicity and XOR"])
report["cases"].extend(["two-tree Fenwick range corrections", "size-bound Merkle inclusion proofs", "two-heap exact running medians"])
report["cases"].extend(["square-root block replacements", "merge-sort threshold counts", "disjoint sparse-table sums", "Li Chao tariff minima"])
report["cases"].extend(["coordinate rank catalog", "Fenwick frequency order selection", "Mo offline distinct windows", "two-dimensional prefix rectangles"])
report["cases"].extend(["sorted incident posting intersections", "positional exact token phrases", "verified trigram substring candidates", "front-coded lexicon blocks"])
report["cases"].extend(["LFU frequency and recency eviction", "TTL stale-expiry replacement", "generational slot handle rejection", "d-ary stable heap order"])
report["cases"].extend(["Misra-Gries threshold candidates", "Space-Saving count bounds", "HyperLogLog duplicate and union registers", "reservoir event inclusion"])
report["cases"].extend(["counting Bloom balanced removals", "scalable Bloom layer retention", "blocked Bloom local probes", "cuckoo fingerprint rollback"])
report["cases"].extend(["pairing heap two-pass meld order", "binomial forest degree carries", "radix monotone priorities", "dual heap live-entry extremes"])
report["cases"].extend(["moving-point spatial hash radius", "point-region quadtree windows", "static box hierarchy intersections", "Morton grid rectangle ranges"])
report["cases"].extend(["gap buffer cursor edits", "immutable rope revision sharing", "unrolled block list mutations", "segmented prefix block updates"])
report["cases"].extend(["Elias-Fano rank recovery", "gap-encoded posting seeks", "chunked integer-set intersections", "level-order trie membership"])
report["cases"].extend(["checkpoint arena lifetime and zeroing", "first-fit contiguous-span coalescing", "buddy exact-partner coverage", "generational slab stale handles"])
report["cases"].extend(["persistent bitmap HAMT revisions", "ternary term completions", "binary longest-prefix routes", "extendible directory bucket ownership"])
report["cases"].extend(["CLOCK second-chance frame order", "segmented LRU promotion and demotion", "aged sketch admission", "hashed wheel exact deadlines"])
report["cases"].extend(["splay ordered access and parent links", "resident K-reference victim ranking"])
report["cases"].extend(["Eytzinger lower-bound ranks", "Cartesian range minima and parent links",
                        "leftist meld ranks and ownership", "potential DSU exact differences",
                        "two-dimensional range counts", "bounded-universe successor mutations",
                        "scapegoat insertion sizes and depth", "static XOR filter inserted membership"])
report["cases"].extend(["palindromic suffix counts", "range-cap maximum and sum invariants",
                        "wavelet matrix frequency and quantiles", "FIFO affine window composition",
                        "linear hash split-bucket ownership", "compressed 2D Fenwick active rectangles",
                        "persistent queue branch preservation", "parenthesis subtree and ancestor intervals"])
report["cases"].extend(["BK metric-radius label matches", "vantage metric nearest depots",
                        "centroid nearest marked distances", "two-level exact static membership",
                        "FM exact substring counts and locations", "block-max exact top-k scores",
                        "piecewise corrected lower-bound ranks", "Euler-tour RMQ common ancestors"])
report["cases"].extend(["X-fast exact predecessor and successor", "persistent radix revision sharing",
                        "compressed suffix tree locations", "disjoint interval add and remove",
                        "CSR overlay compaction equivalence", "bitset directed reachability",
                        "gap-label order after insertion", "skew heap meld ownership and order"])
report["cases"].extend(["Fibonacci priority decreases and removals", "tournament run-head winners",
                        "priority search three-sided events", "reduced Boolean diagram truth tables",
                        "LZ78 phrase round trips", "segment stabbing active IDs",
                        "Huffman prefix-free round trips", "condensed graph directed paths"])
report["cases"].extend(["ordered treap split join and rank", "skip-list spans and rank selection",
                        "two-dimensional segment sums", "alias table weight draws",
                        "MinHash candidate verification", "run-length bitmap algebra",
                        "range majority candidate verification"])
report["cases"].extend(["moveable DSU active group aggregates", "block-cut articulation and edge blocks",
                        "Kruskal minimax merge ancestors", "zero-suppressed family membership",
                        "signed Count Sketch update reversal", "exponential histogram boundary allowance",
                        "square-root range modes"])
report["cases"].extend(["double-array terminal and prefix membership", "hopscotch neighborhood preservation",
                        "invertible replica set differences", "de Bruijn unitig edge recovery"])
report["cases"].extend(["adaptive radix prefix splitting and tier counts", "bit-sliced exact row masks and sums",
                        "SimHash banded Hamming recall", "minimal acyclic dictionary recognition"])
report["cases"].extend(["persistent range MEX last occurrences", "range XOR span and subset maxima",
                        "affine range composition and sums", "min-max heap endpoint invariants"])
report["cases"].extend(["persistent subarray kth ranks", "maximum-subarray range summaries",
                        "interval-limited Li Chao offers", "adjacent frequency bucket extremes",
                        "Patricia longest-prefix routes"])
report["cases"].extend(["successor retirement and exhaustion", "persistent range distinct markers",
                        "editable substring hash joins", "expired sliding-window medians",
                        "ball-tree exact nearest depots"])
(root / "work/dsa-property-validation.json").write_text(json.dumps(report, indent=2) + "\n")
print(json.dumps(report))
