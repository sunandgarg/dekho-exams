"""Tenth Python pass: pairing, iterator, storage, data and search boundaries."""
lesson('zip-strict-pairing','Python zip(strict=True): reject a mismatched pair of input feeds',
'zip pairs values by position; strict=True raises ValueError if the inputs end at different positions.',
'The receipt IDs and minor-unit amounts are bounded concrete lists. A normal zip would silently discard an unmatched trailing ID; this fixture requires the same length before a reconciliation can be accepted. The first run pairs both feeds. The second run reaches the length mismatch and rejects it. Because zip is lazy, the exception appears when the pairs are consumed, not when the zip object is constructed.',
'A strict zip still cannot prove that two rows with the same position refer to the same real-world receipt. Validate identifiers and provenance separately. Streaming feeds can have partial side effects before a late mismatch becomes visible; stage changes before publishing them. [[python/iterator-protocol|One-use iterators]], [[python/reconciliation-exercise|Reconciliation]] and [[python/itertools-pipelines|Iterator pipelines]] cover those boundaries.',
r'''def pair_receipts(identifiers, amounts):
    if type(identifiers) is not list or type(amounts) is not list or len(identifiers) > 10 or len(amounts) > 10:
        raise ValueError("bounded feeds")
    return list(zip(identifiers, amounts, strict=True))

print(pair_receipts(["R41", "R42"], [125, 75]))
try:
    pair_receipts(["R41", "R42"], [125])
except ValueError:
    print("length mismatch rejected")''',"[('R41', 125), ('R42', 75)]\nlength mismatch rejected",
'Pairing n values takes O(n) time; materializing the result takes O(n) storage. A streaming caller can avoid that result list, but must define rollback or staging for a mismatch discovered at the end.',
['Default zip truncates to the shortest input.','Strict pairing checks length, not row identity or authorization.'],['python/iterator-protocol','python/reconciliation-exercise','python/itertools-pipelines'])

lesson('setdefault-aliasing','Python dict.setdefault: the returned collection remains mutable shared state',
'dict.setdefault returns the existing value for a key or inserts and returns the supplied default when the key is absent.',
'The shipment index groups receipt IDs by route. The first call installs a new list; a later call returns that same list and appends to it. The identifier is then added through a separate alias, proving that the dictionary retained mutable state rather than a copy. This is useful inside one owned aggregation pass, but it is an implicit mutation boundary.',
'The default expression is evaluated before setdefault is called, even when the key already exists. Do not use a side-effecting or expensive factory there; defaultdict can defer construction. Neither form provides thread-safe compound updates. [[python/defaultdict-grouping|Deferred defaults]], [[python/dict-view-liveness|Live mapping views]] and [[python/copy-deepcopy|Copy ownership]] make the alternatives explicit.',
r'''by_route = {}
route_receipts = by_route.setdefault("north", [])
route_receipts.append("R41")
same_list = by_route.setdefault("north", [])
same_list.append("R42")
print(by_route)
print(route_receipts is same_list)
print(route_receipts is by_route["north"])''',"{'north': ['R41', 'R42']}\nTrue\nTrue",
'Average mapping lookup and insertion are constant time under ordinary hash behavior, while each append is amortized constant time. The lists retain every grouped receipt; no bound follows from setdefault itself.',
['The returned list is an alias, not a snapshot.','A default expression still runs when the key is already present.'],['python/defaultdict-grouping','python/dict-view-liveness','python/copy-deepcopy'],subject='python-types')

lesson('tee-buffer-lifetime','Python itertools.tee: a lagging reader retains buffered values',
'itertools.tee creates independent iterators over one source by buffering values consumed ahead by another reader.',
'Two receipt readers share a three-item source. The fast reader consumes two IDs before the slow reader consumes one; the slow reader can still retrieve the first ID because tee retained it. The fixture then drains both. This is not two independent upstream queries or a free clone of a generator.',
'If one reader runs far ahead or never resumes, the buffer can grow with the entire unread stream. tee iterators are not safe for simultaneous use from multiple threads. When full replay is needed and the input is already small and bounded, materializing a list can make the memory cost easier to reason about. [[python/iterator-protocol|Iterator ownership]], [[python/itertools-pipelines|Pipelines]] and [[python/spooled-file-budgets|Spooling]] show other choices.',
r'''from itertools import tee

source_reads = []
def receipt_stream():
    for identifier in ("R41", "R42", "R43"):
        source_reads.append(identifier)
        yield identifier

fast, slow = tee(receipt_stream())
print(next(fast), next(fast))
print("upstream:", source_reads)
print("slow:", next(slow))
print("fast rest:", list(fast))
print("slow rest:", list(slow))''','R41 R42\nupstream: [\'R41\', \'R42\']\nslow: R41\nfast rest: [\'R43\']\nslow rest: [\'R42\', \'R43\']',
'Total upstream reads are O(n), but retained buffer size depends on the maximum reader lag and can reach O(n). The three-item fixture does not measure a long-running service.',
['tee can retain a large unread backlog.','Two tee readers must not be consumed concurrently from different threads.'],['python/iterator-protocol','python/itertools-pipelines','python/spooled-file-budgets'],subject='python-advanced')

lesson('async-timeout-boundary','Python asyncio.timeout: catch the deadline outside the context',
'asyncio.timeout limits how long an awaiting task may remain inside its asynchronous context.',
'The owned Event is never set, so the wait cannot finish normally. A zero-second deadline cancels the current task at its next suspension; the context converts that cancellation into TimeoutError on exit. The caller catches it outside the context and records a rejected receipt lookup. No network call or wall-clock sleep is needed to show the boundary.',
'The timeout limits the awaiting task, not arbitrary blocking work already moved to a thread or remote service. Cleanup in finally still needs its own failure and time budget, and swallowing CancelledError inside the context can defeat the intended deadline. [[python/async-deadlines|Deadline composition]], [[python/async-to-thread-context|Thread offload]] and [[python/async-shield-ownership|Shielding]] describe adjacent ownership rules.',
r'''import asyncio

async def wait_for_receipt():
    gate = asyncio.Event()
    try:
        async with asyncio.timeout(0):
            await gate.wait()
    except TimeoutError:
        return "lookup timed out"
    return "receipt arrived"

print(asyncio.run(wait_for_receipt()))''','lookup timed out',
'The fixture creates one Event and task. A real deadline must include queueing, transport and cleanup costs; timing behavior under load is not established by this deterministic expired-deadline case.',
['Catch TimeoutError around the context, not inside it.','Cancelling the await does not prove a remote or threaded side effect stopped.'],['python/async-deadlines','python/async-to-thread-context','python/async-shield-ownership'],subject='python-advanced')

lesson('bool-int-key-interview','Python interview: bool and int can address the same dictionary key',
'Dictionary keys that compare equal and have equal hashes refer to one mapping entry, even when their types differ.',
'The permission flags are written with True and then 1 as keys. Since bool is an int subclass and these values compare equal with equal hashes, the second assignment replaces the first value rather than adding a second entry. The result has one key and its latest value. The lesson concerns key equality, not a claim that a boolean should be accepted as an integer identifier.',
'At a data boundary, reject boolean IDs explicitly before storing them as integer keys. The same issue can affect set membership and deduplication. [[python/hash-equality|Hash/equality contract]], [[python/type-conversion|Numeric conversion]] and [[python/hash-key-mutation-interview|Mutable keys]] cover the neighboring traps.',
r'''access = {True: "review"}
access[1] = "approve"
print("entries:", len(access))
print("by bool:", access[True])
print("by int:", access[1])
print("same hash:", hash(True) == hash(1))''','entries: 1\nby bool: approve\nby int: approve\nsame hash: True',
'Both lookups are average constant-time mapping operations. A malicious or pathological key set can change collision costs, and no permission decision should be based on an unvalidated ID type.',
['bool passes isinstance(value, int), so use a deliberate input rule.','Distinct key types do not guarantee distinct dictionary entries.'],['python/hash-equality','python/type-conversion','python/hash-key-mutation-interview'],subject='python-interview')

lesson('stable-top-k-exercise','Python exercise: select the highest scores with stable tie order',
'A stable top-k selection returns the k greatest scored records while preserving their original order among equal scores.',
'The review queue contains bounded integer scores and receipt IDs. The function validates the requested count and each record, sorts by descending score and original position, and returns the first k identifiers. A tie between R41 and R42 keeps their input order. The input list remains unchanged, which makes the ownership contract visible.',
'A heap can reduce work when k is much smaller than n, but its tie and replacement policy must be defined before substituting it. A score does not confer authorization to act on the receipt. [[python/heap-top-k|Heap selection]], [[python/sorting|Stable sorting]] and [[python/ordering-protocol|Ordering rules]] provide the comparison.',
r'''def top_receipts(records, count):
    if type(records) is not list or len(records) > 100 or type(count) is not int or not 0 <= count <= len(records):
        raise ValueError("bounded selection")
    if any(type(row) is not tuple or len(row) != 2 or type(row[0]) is not str or type(row[1]) is not int or not 0 <= row[1] <= 100 for row in records):
        raise ValueError("receipt record")
    ranked = sorted(enumerate(records), key=lambda item: (-item[1][1], item[0]))
    return [row[0] for _, row in ranked[:count]]

queue = [("R41", 8), ("R42", 8), ("R43", 9)]
print(top_receipts(queue, 2))
print(queue)
try:
    top_receipts(queue, True)
except ValueError:
    print("boolean count rejected")''',"['R43', 'R41']\n[('R41', 8), ('R42', 8), ('R43', 9)]\nboolean count rejected",
'Sorting n records costs O(n log n) time and O(n) result/index storage in this implementation. The 100-record cap bounds the fixture; a streaming top-k implementation needs a separately tested tie policy.',
['A plain heap replacement may reorder equal scores.','Validate count before slicing; bool is not an acceptable count.'],['python/heap-top-k','python/sorting','python/ordering-protocol'],subject='python-exercises')

lesson('merge-half-open-exercise','Python exercise: merge overlapping half-open reservations',
'A half-open interval includes its start and excludes its end, so intervals meeting at one boundary do not overlap.',
'The fixture merges sorted valid reservations only when the next start is strictly before the current end. The first two ranges overlap and become one; a third begins exactly at the merged end and remains separate. That distinction matters when adjacent bookings are allowed. Empty and reversed ranges are rejected before sorting.',
'The function returns new tuples and leaves the caller input unchanged. It does not attach owners, timezones or permissions to the ranges. [[python/interval-conflict-exercise|Conflict checks]], [[python/weighted-intervals|Scheduling]] and [[python/zone-local-classification|Local time ambiguity]] cover those separate contracts.',
r'''def merge_reservations(ranges):
    if type(ranges) is not list or len(ranges) > 100 or any(type(row) is not tuple or len(row) != 2 or any(type(value) is not int for value in row) or not 0 <= row[0] < row[1] <= 1000 for row in ranges):
        raise ValueError("bounded half-open ranges")
    merged = []
    for start, end in sorted(ranges):
        if merged and start < merged[-1][1]:
            merged[-1] = (merged[-1][0], max(end, merged[-1][1]))
        else:
            merged.append((start, end))
    return merged

print(merge_reservations([(0, 3), (2, 5), (5, 7)]))
try:
    merge_reservations([(4, 4)])
except ValueError:
    print("empty range rejected")''','[(0, 5), (5, 7)]\nempty range rejected',
'Sorting n intervals takes O(n log n) time; the result can retain O(n) intervals. For presorted trusted input, the scan is O(n), but this boundary validates and sorts before merging.',
['Using start <= end would merge merely adjacent bookings.','Reject empty ranges before interpreting their overlap.'],['python/interval-conflict-exercise','python/weighted-intervals','python/zone-local-classification'],subject='python-exercises')

lesson('heap-merge-feeds','Python heapq.merge: combine sorted feeds without sorting every value again',
'heapq.merge yields values from already sorted inputs in order while retaining one candidate from each feed.',
'Two bounded receipt feeds are sorted by integer timestamp. The merge returns a timestamp-ordered stream of pairs, then the fixture materializes it for display. The inputs stay unchanged. If a feed breaks its sorted contract, merge does not repair it and its output may be wrong; the wrapper rejects such a feed before yielding.',
'The wrapper uses concrete lists so it can validate before a caller consumes any result. A real one-use stream cannot be fully validated without buffering or a staged failure policy. [[python/sorted-merge-exercise|Manual stable merge]], [[python/iterator-protocol|One-use input]] and [[python/heap-top-k|Heap costs]] connect the data-structure choices.',
r'''from heapq import merge

def merged_events(*feeds):
    if len(feeds) > 4 or any(type(feed) is not list or len(feed) > 20 or any(type(row) is not tuple or len(row) != 2 or type(row[0]) is not int or type(row[1]) is not str for row in feed) or any(a[0] > b[0] for a, b in zip(feed, feed[1:])) for feed in feeds):
        raise ValueError("sorted bounded feeds")
    return list(merge(*feeds, key=lambda row: row[0]))

print(merged_events([(1, "R41"), (4, "R43")], [(2, "R42"), (5, "R44")]))
try:
    merged_events([(3, "R43"), (1, "R41")])
except ValueError:
    print("unsorted feed rejected")''',"[(1, 'R41'), (2, 'R42'), (4, 'R43'), (5, 'R44')]\nunsorted feed rejected",
'For n total items across k feeds, merging costs O(n log k) comparisons and O(k) heap storage. This wrapper materializes O(n) output and scans inputs for validation first.',
['heapq.merge assumes every feed is sorted.','Materializing the iterator removes its streaming-memory benefit.'],['python/sorted-merge-exercise','python/iterator-protocol','python/heap-top-k'],subject='python-examples')

lesson('sqlite-foreign-key-boundary','Python SQLite foreign keys: enable enforcement on each connection',
'SQLite foreign-key constraints reject a child row without a matching parent only when enforcement is enabled for the connection.',
'The owned in-memory connection enables the setting before a transaction, creates a customer and a receipt that references it, then attempts an orphan receipt. The orphan raises IntegrityError and does not appear in the final count. The fixture checks the setting so a default configuration cannot silently change the lesson result.',
'Enable the PRAGMA separately on every new connection before writes; declaring REFERENCES alone is insufficient on configurations where foreign keys are off. This does not replace authorization or a production migration. [[python/sqlite-transactions|Transaction boundaries]], [[python/sqlite-writer-contention|Writer contention]] and [[python/django-owner-constraints|Owner constraints]] cover related state rules.',
r'''import sqlite3

connection = sqlite3.connect(":memory:")
connection.execute("PRAGMA foreign_keys=ON")
print("enabled:", connection.execute("PRAGMA foreign_keys").fetchone()[0])
connection.execute("CREATE TABLE customer(id INTEGER PRIMARY KEY)")
connection.execute("CREATE TABLE receipt(id INTEGER PRIMARY KEY, customer_id INTEGER NOT NULL REFERENCES customer(id))")
with connection:
    connection.execute("INSERT INTO customer VALUES (41)")
    connection.execute("INSERT INTO receipt VALUES (1, 41)")
try:
    with connection:
        connection.execute("INSERT INTO receipt VALUES (2, 99)")
except sqlite3.IntegrityError:
    print("orphan rejected")
print("receipts:", connection.execute("SELECT COUNT(*) FROM receipt").fetchone()[0])
connection.close()''','enabled: 1\norphan rejected\nreceipts: 1',
'The indexed parent-key lookup adds database work to each child write; actual cost depends on schema and workload. This small in-memory fixture says nothing about disk durability or multi-connection deployment behavior.',
['A REFERENCES clause alone does not prove this connection enforces it.','A foreign key enforces existence, not tenant permission.'],['python/sqlite-transactions','python/sqlite-writer-contention','python/django-owner-constraints'],subject='python-examples')

lesson('pandas-join-cardinality','Pandas merge(validate=): reject an unintended many-to-many join',
'pandas merge can check declared key cardinality with validate before accepting a joined result.',
'Each receipt should have one currency record. The first merge uses one_to_one and produces two rows. A duplicate key in the right-hand frame would multiply receipt rows; the second merge raises MergeError instead of silently inflating totals. This is a shape check, not a check that every expected key was present.',
'Missing joins, null-key matching and field-level validity need separate policy. Pandas can match null keys to each other, unlike ordinary SQL join expectations. [[python/pandas-joins|Join semantics]], [[python/pandas-null-joins|Null keys]] and [[python/pandas-groupby|Aggregation]] cover those failure paths.',
r'''import pandas as pd
from pandas.errors import MergeError

receipts = pd.DataFrame({"receipt_id": [41, 42], "minor": [125, 75]})
currency = pd.DataFrame({"receipt_id": [41, 42], "unit": ["INR", "INR"]})
joined = receipts.merge(currency, on="receipt_id", validate="one_to_one")
print("joined:", len(joined))
duplicates = pd.DataFrame({"receipt_id": [41, 41], "unit": ["INR", "USD"]})
try:
    receipts.merge(duplicates, on="receipt_id", validate="one_to_one")
except MergeError:
    print("duplicate key rejected")''','joined: 2\nduplicate key rejected',
'Hash or sort join costs depend on pandas implementation and key distribution; this fixture has two rows. A materialized many-to-many result can grow as the product of duplicate group sizes, which is why cardinality is checked before using totals.',
['validate checks key multiplicity, not business completeness.','Null keys can match in pandas merges; define their handling explicitly.'],['python/pandas-joins','python/pandas-null-joins','python/pandas-groupby'],subject='python-data',dependencies=['pandas==3.0.6','numpy==2.5.3'])

lesson('pandas-groupby-missing-key','Pandas groupby(dropna=False): keep a missing category visible',
'groupby normally excludes rows with missing grouping keys unless dropna=False is selected.',
'Three receipt amounts include one with an absent region. A default groupby would leave that amount out of the regional totals; the fixture uses dropna=False, then prints the named region and the missing-key total separately. The accounted sum equals the raw sum, so no amount disappears in the report.',
'A missing region is not automatically a valid business category. It may need rejection or separate remediation before publication. [[python/pandas-nullable|Missing values]], [[python/pandas-groupby|Grouped totals]] and [[python/reconciliation-exercise|Total reconciliation]] help define that decision.',
r'''import pandas as pd

receipts = pd.DataFrame({"region": ["north", None, "north"], "minor": [125, 75, 50]})
totals = receipts.groupby("region", dropna=False)["minor"].sum()
print("north:", int(totals.loc["north"]))
print("missing:", int(totals[totals.index.isna()].iloc[0]))
print("accounted:", int(totals.sum()) == int(receipts["minor"].sum()))''','north: 175\nmissing: 75\naccounted: True',
'Grouping n rows requires work and memory proportional to the input and number of groups; exact implementation costs depend on dtype and key distribution. The equality check is useful but does not prove each row was classified correctly.',
['Default groupby can hide missing-key amounts from a grouped report.','Keeping a missing group is a visibility policy, not proof the data is valid.'],['python/pandas-nullable','python/pandas-groupby','python/reconciliation-exercise'],subject='python-data',dependencies=['pandas==3.0.6','numpy==2.5.3'])

lesson('flask-if-match-write','Python Flask If-Match: reject a stale in-memory revision before mutation',
'An If-Match precondition lets a client require a specific representation revision before a write is accepted.',
'The local test client first reads a quoted revision tag, then sends an update with that tag. The handler checks it before changing the receipt amount and increments the revision. Replaying the old tag returns 412 and leaves the new amount intact. This shows an optimistic conflict boundary without opening a network listener.',
'This in-memory state is not durable and is shared only within this fixture. Real handlers must authenticate the caller, apply tenant scope and make the compare-and-update atomic in the persistent store. [[python/flask-conditional-response|Conditional reads]], [[python/flask-sqlite-persistence|Storage]] and [[spring/data-transactions|Transaction contracts]] show the next layer.',
r'''from flask import Flask, jsonify, request

application = Flask(__name__)
receipt = {"minor": 125, "revision": 1}

@application.get("/receipt")
def read_receipt():
    response = jsonify(minor=receipt["minor"])
    response.headers["ETag"] = f'"{receipt["revision"]}"'
    return response

@application.put("/receipt")
def update_receipt():
    if request.headers.get("If-Match") != f'"{receipt["revision"]}"':
        return jsonify(error="stale revision"), 412
    payload = request.get_json(silent=True)
    if type(payload) is not dict or type(payload.get("minor")) is not int or not 0 <= payload["minor"] <= 1000:
        return jsonify(error="invalid amount"), 400
    receipt["minor"] = payload["minor"]
    receipt["revision"] += 1
    return jsonify(minor=receipt["minor"])

with application.test_client() as client:
    tag = client.get("/receipt").headers["ETag"]
    print("accepted:", client.put("/receipt", json={"minor": 150}, headers={"If-Match": tag}).status_code)
    print("stale:", client.put("/receipt", json={"minor": 175}, headers={"If-Match": tag}).status_code)
    print("stored:", client.get("/receipt").get_json()["minor"])''','accepted: 200\nstale: 412\nstored: 150',
'The dictionary comparison and update are tiny local operations. This fixture does not measure HTTP deployment latency or establish atomicity across workers; a database update needs a revision predicate in the write itself.',
['An ETag is not an authentication token.','A read-then-write check outside a transaction can race in a persistent service.'],['python/flask-conditional-response','python/flask-sqlite-persistence','spring/data-transactions'],subject='python-web',dependencies=['Flask==3.1.3'])

lesson('sqlite-backup-project','Python SQLite backup project: copy a committed snapshot to another connection',
'sqlite3.Connection.backup copies database pages into a destination connection while preserving a consistent SQLite snapshot.',
'The fixture commits one receipt in a source in-memory database, backs it up to a second in-memory connection and checks the destination row. It then inserts another source row. The destination still has the earlier snapshot until another backup is run. Both connections are owned and closed by the program.',
'A backup is not a verified disaster-recovery plan. A production copy needs destination storage, integrity checks, retention, restore drills and coordination with external side effects. [[python/sqlite-transactions|Committed state]], [[python/sqlite-checkpoint-project|Import cursors]] and [[python/atomic-report-project|File publication]] describe other persistence boundaries.',
r'''import sqlite3

source = sqlite3.connect(":memory:")
destination = sqlite3.connect(":memory:")
source.execute("CREATE TABLE receipt(id TEXT PRIMARY KEY)")
with source:
    source.execute("INSERT INTO receipt VALUES ('R41')")
source.backup(destination)
with source:
    source.execute("INSERT INTO receipt VALUES ('R42')")
print("source:", source.execute("SELECT COUNT(*) FROM receipt").fetchone()[0])
print("copy:", destination.execute("SELECT COUNT(*) FROM receipt").fetchone()[0])
source.close()
destination.close()''','source: 2\ncopy: 1',
'Backup copies pages and requires storage proportional to the destination database. This two-row, in-memory demonstration does not measure backup duration or test a power-loss recovery path.',
['A one-time backup does not track later source commits.','Validate that a backup can be restored, not only that the API returned.'],['python/sqlite-transactions','python/sqlite-checkpoint-project','python/atomic-report-project'],subject='python-projects')

lesson('asyncmock-await-contract','Python AsyncMock: assert that a collaborator was awaited',
'AsyncMock records calls to an asynchronous collaborator separately from completed awaits.',
'The receipt handler awaits its injected writer before returning an accepted status. The test checks the awaited argument with assert_awaited_once_with. A second mock is called but never awaited; its call count increases while await_count remains zero. That difference catches a common bug where a coroutine object is constructed and discarded.',
'A mock verifies interaction with a substitute, not database durability or network delivery. The injected writer is trusted here; real tests need failure and cancellation paths too. [[python/asyncio-test-fixture|Async test lifecycle]], [[python/mock-failures|Failure injection]] and [[python/gather-sibling-lifetime|Task lifetime]] show follow-up checks.',
r'''import asyncio
from unittest.mock import AsyncMock

async def accept_receipt(identifier, writer):
    await writer(identifier)
    return "accepted"

async def main():
    writer = AsyncMock()
    print(await accept_receipt("R41", writer))
    writer.assert_awaited_once_with("R41")
    print("awaited:", writer.await_count)
    unused = AsyncMock()
    pending = unused("R42")
    print("called but not awaited:", unused.call_count, unused.await_count)
    pending.close()

asyncio.run(main())''','accepted\nawaited: 1\ncalled but not awaited: 1 0',
'The fixture has two mock calls and no external I/O. Mock bookkeeping adds local overhead; it is not a measurement of the real writer. Await assertions do not prove a side effect committed.',
['assert_called_once_with does not prove an async function was awaited.','Close an intentionally unawaited coroutine in a test to avoid a warning.'],['python/asyncio-test-fixture','python/mock-failures','python/gather-sibling-lifetime'],subject='python-testing')

lesson('a-star-grid','Python A-star grid search: use an admissible lower bound for shortest paths',
'A-star expands candidate paths by current cost plus a heuristic lower bound on remaining cost.',
'The bounded grid allows unit-cost orthogonal moves. Manhattan distance never overestimates the remaining cost under those rules. The center cell is blocked, so the route from the top-left to the bottom-right goes around it with four moves. A priority queue keeps frontier states; the best-known cost map discards stale heap entries.',
'A heuristic that overestimates or ignores a cheaper movement mode can break optimality. For weighted or diagonal moves, choose a matching lower bound or fall back to zero, which gives Dijkstra behavior. [[python/dijkstra|Nonnegative shortest paths]], [[python/graph-bfs|Unit-cost BFS]] and [[python/floyd-warshall-paths|All-pairs costs]] make the assumptions visible.',
r'''from heapq import heappop, heappush

def grid_cost(width, height, blocked, start, goal):
    if type(width) is not int or type(height) is not int or not 1 <= width <= 10 or not 1 <= height <= 10 or type(blocked) is not set or any(type(cell) is not tuple or len(cell) != 2 or any(type(value) is not int for value in cell) for cell in blocked) or any(type(cell) is not tuple or len(cell) != 2 or any(type(value) is not int for value in cell) for cell in (start, goal)):
        raise ValueError("grid bounds")
    valid = lambda cell: 0 <= cell[0] < width and 0 <= cell[1] < height and cell not in blocked
    if not valid(start) or not valid(goal):
        raise ValueError("endpoint")
    estimate = lambda cell: abs(cell[0] - goal[0]) + abs(cell[1] - goal[1])
    best = {start: 0}
    frontier = [(estimate(start), 0, start)]
    while frontier:
        _, cost, cell = heappop(frontier)
        if cost != best[cell]:
            continue
        if cell == goal:
            return cost
        for dx, dy in ((1, 0), (-1, 0), (0, 1), (0, -1)):
            neighbor = (cell[0] + dx, cell[1] + dy)
            if valid(neighbor) and cost + 1 < best.get(neighbor, float("inf")):
                best[neighbor] = cost + 1
                heappush(frontier, (cost + 1 + estimate(neighbor), cost + 1, neighbor))
    return None

print(grid_cost(3, 3, {(1, 1)}, (0, 0), (2, 2)))
print(grid_cost(2, 1, {(1, 0)}, (0, 0), (0, 0)))''','4\n0',
'For V reachable cells and E possible moves, heap operations give O((V+E) log V) time with O(V) retained state in this bounded implementation. The heuristic may reduce expansions but does not improve the worst-case guarantee.',
['A heuristic must be a lower bound under the actual movement costs.','Reject blocked or out-of-range endpoints before search.'],['python/dijkstra','python/graph-bfs','python/floyd-warshall-paths'],subject='python-dsa')

lesson('fenwick-prefix-sums','Python Fenwick tree: update one amount and query prefix totals',
'A Fenwick tree stores partial sums so point updates and prefix-sum queries each visit logarithmically many nodes.',
'The owned ledger starts with three minor-unit amounts. The tree builds by adding each amount, reports the first two-item total, then increases the second amount by 25 and reports the new prefix and full totals. Public indexes are zero-based; internal tree indexes start at one. The wrapper rejects out-of-range positions before mutation.',
'This structure answers prefix and range sums, not arbitrary minimum or maximum updates. Unbounded integer values can grow memory and arithmetic cost, so an import boundary should cap them. [[python/segment-tree|Range structures]], [[python/lazy-range-sums|Range additions]] and [[python/numpy-precision|Numeric representation]] cover alternatives.',
r'''class PrefixLedger:
    def __init__(self, amounts):
        if type(amounts) is not list or not 1 <= len(amounts) <= 100 or any(type(value) is not int or not 0 <= value <= 1000 for value in amounts):
            raise ValueError("bounded amounts")
        self.size = len(amounts)
        self.tree = [0] * (self.size + 1)
        for index, amount in enumerate(amounts):
            self.add(index, amount)
    def add(self, index, delta):
        if type(index) is not int or not 0 <= index < self.size or type(delta) is not int or not -1000 <= delta <= 1000:
            raise ValueError("point update")
        position = index + 1
        while position <= self.size:
            self.tree[position] += delta
            position += position & -position
    def prefix(self, end):
        if type(end) is not int or not 0 <= end <= self.size:
            raise ValueError("exclusive end")
        total = 0
        while end:
            total += self.tree[end]
            end -= end & -end
        return total

ledger = PrefixLedger([125, 75, 50])
print(ledger.prefix(2))
ledger.add(1, 25)
print(ledger.prefix(2), ledger.prefix(3))''','200\n225 275',
'Construction by repeated updates costs O(n log n) here; each later update or prefix query costs O(log n), with O(n) storage. A linear construction is possible but would need a separate checked fixture.',
['Do not mix zero-based public indexes with one-based tree positions.','A delta can make a stored amount negative; this fixture does not enforce per-item post-update bounds.'],['python/segment-tree','python/lazy-range-sums','python/numpy-precision'],subject='python-dsa')

for subject,title,slugs in [
 ('python','Strictly paired feeds',['zip-strict-pairing']),
 ('python-types','Mapping alias ownership',['setdefault-aliasing']),
 ('python-advanced','Buffered readers and deadlines',['tee-buffer-lifetime','async-timeout-boundary']),
 ('python-interview','Dictionary equality traces',['bool-int-key-interview']),
 ('python-exercises','Stable ranking and half-open ranges',['stable-top-k-exercise','merge-half-open-exercise']),
 ('python-examples','Sorted feeds and relational integrity',['heap-merge-feeds','sqlite-foreign-key-boundary']),
 ('python-data','Join shape and missing groups',['pandas-join-cardinality','pandas-groupby-missing-key']),
 ('python-web','Conditional writes',['flask-if-match-write']),
 ('python-projects','Backup snapshot boundaries',['sqlite-backup-project']),
 ('python-testing','Await assertions',['asyncmock-await-contract']),
 ('python-dsa','Heuristic paths and prefix totals',['a-star-grid','fenwick-prefix-sums'])]:
 group(subject,title,slugs)

BOUNDARY_QUESTIONS=[
 ('When does zip(strict=True) detect an unmatched trailing value?',['When the zip object is constructed','When the pairs are consumed','Only after list sorting','It silently discards it'],1,'Strict zip is lazy; the mismatch becomes visible during iteration.'),
 ('What does setdefault return for an existing list value?',['An immutable copy','The stored list object','A new empty list','Only the key'],1,'The returned list aliases the mapping value.'),
 ('What happens if one tee reader outruns the other?',['No state is retained','Unread values can accumulate in a buffer','Both readers restart the source','The source is copied eagerly'],1,'The lagging reader needs the values already pulled upstream.'),
 ('Where should TimeoutError from asyncio.timeout be caught?',['Outside its context','Only in an event loop callback','Before entering the context','Inside a synchronous thread'],0,'The context transforms cancellation into TimeoutError as it exits.'),
 ('Why do True and 1 collapse into one dictionary entry?',['They are identical objects','They compare equal and share a hash','Dictionaries store only strings','The later value is ignored'],1,'Mapping key equality and hash consistency determine entry identity.'),
 ('What preserves a stable tie in a top-k result?',['Descending score plus original position','Reversing all input rows','Dropping equal scores','A set of receipt IDs'],0,'Original position supplies the declared tie order.'),
 ('Do half-open intervals [0,5) and [5,7) overlap?',['Yes','No','Only when sorted','Only if the endpoints are floats'],1,'The first interval excludes its end, so adjacency is not overlap.'),
 ('What must hold for heapq.merge input feeds?',['Each feed is already sorted','All feeds have the same length','The feeds contain no duplicate values','Their values are hashable'],0,'The merge operation does not sort a broken source feed.'),
 ('What is required for a SQLite foreign key to reject an orphan child?',['A REFERENCES clause only','Connection enforcement enabled before writes','A Python dictionary','A read-only cursor'],1,'Foreign-key enforcement is connection state and must be enabled where needed.'),
 ('What does pandas merge(validate="one_to_one") reject?',['An absent key on either side','Duplicate join keys that violate one-to-one shape','Any null value in a non-key column','Every unindexed frame'],1,'Validation checks key cardinality; completeness is separate.'),
 ('What should a stale If-Match write return in this fixture?',['200 with the old value','412 without changing the receipt','A larger revision number','A background task ID'],1,'A mismatched revision fails before mutation.'),
 ('What makes Manhattan distance admissible on the lesson grid?',['Only orthogonal unit-cost moves are allowed','Diagonal moves are free','The grid has no blocked cells','All edges have negative cost'],0,'Each remaining horizontal or vertical step costs at least one.'),
]
quiz_slug='python-boundary-contracts';quiz_title='Python pairing, storage and search boundary quiz';BANKS[quiz_slug]=(quiz_title,BOUNDARY_QUESTIONS)
quiz_refs=['python/zip-strict-pairing','python/tee-buffer-lifetime','python/async-timeout-boundary','python/pandas-join-cardinality','python/flask-if-match-write','python/a-star-grid']
quiz=copy.deepcopy(lookup['quizzes/python-basics']);quiz_path='quizzes/'+quiz_slug
quiz.update(id=str(uuid.uuid5(uuid.NAMESPACE_URL,'https://aitrove.in/'+quiz_path)),path=quiz_path,title=quiz_title,summary='Twelve explained checks on Python iterators, storage constraints, data joins and graph search.',sort_order=700+len(added),published_at=stamp,updated_at=stamp)
quiz['body']=para('This self-check asks where paired feeds fail, how iterator buffering grows, when storage and HTTP writes are rejected, and which path heuristic stays valid.')+'<h2>Review the related lessons</h2><ul>'+''.join('<li><a href="/'+path+'">'+html.escape(lookup[path]['title'])+'</a></li>' for path in quiz_refs)+'</ul><h3>Common Mistakes</h3>'+para('A correct answer does not prove a deployed database, authenticated writer or large graph implementation is safe. Run the bounded examples and inspect each ownership rule.')
quiz['data']['questions']=[dict(prompt=prompt,options=options,answer=answer,explanation=explanation) for prompt,options,answer,explanation in BOUNDARY_QUESTIONS]
quiz['data']['related']=[dict(path=path,title=lookup[path]['title']) for path in quiz_refs]
upsert(quiz);added.append(quiz_path)

BOUNDARY_REVERSE={
 'python/iterator-protocol':['zip-strict-pairing','tee-buffer-lifetime'],
 'python/defaultdict-grouping':['setdefault-aliasing'],
 'python/async-deadlines':['async-timeout-boundary'],
 'python/hash-equality':['bool-int-key-interview'],
 'python/heap-top-k':['stable-top-k-exercise'],
 'python/interval-conflict-exercise':['merge-half-open-exercise'],
 'python/sorted-merge-exercise':['heap-merge-feeds'],
 'python/sqlite-transactions':['sqlite-foreign-key-boundary','sqlite-backup-project'],
 'python/pandas-joins':['pandas-join-cardinality'],
 'python/pandas-groupby':['pandas-groupby-missing-key'],
 'python/flask-conditional-response':['flask-if-match-write'],
 'python/asyncio-test-fixture':['asyncmock-await-contract'],
 'python/dijkstra':['a-star-grid'],
 'python/segment-tree':['fenwick-prefix-sums']}
for original,slugs in BOUNDARY_REVERSE.items():
 targets=['python/'+slug for slug in slugs];assert original in lookup and all(path in lookup for path in targets)
 item=lookup[original];marker='<h2>Trace the next boundary</h2>'
 item['body']=item['body'].split(marker)[0]+marker+para(', '.join('[['+path+'|'+lookup[path]['title']+']]' for path in targets)+'.')
 known={related['path'] for related in item['data'].get('related',[])}
 item['data'].setdefault('related',[]).extend({'path':path,'title':lookup[path]['title']} for path in targets if path not in known)
 item['updated_at']=stamp
