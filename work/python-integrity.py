"""Eleventh Python pass: parsing, ownership, storage and algorithms."""

lesson('json-duplicate-keys','Python JSON duplicate keys: reject ambiguous object fields',
'A JSON object can repeat a field name, but converting its pairs directly to a dict discards an earlier value.',
'The import receives a bounded document and asks the decoder for each object as ordered pairs. The hook rejects a repeated name at any nesting level before a dict can silently replace the first value. The accepted receipt retains its integer amount. A duplicate amount is rejected even if both spellings carry the same value.',
'Limit bytes before decoding, not after constructing a string. This hook rejects duplicate names but does not validate the complete receipt schema, maximum nesting, or nonstandard numeric tokens. [[python/json-validation|Object shape validation]], [[python/bounded-json-lines|Line budgets]] and [[python/strict-utf8-import|Byte decoding]] belong around this decoder.',
r'''import json

def unique_object(pairs):
    result = {}
    for name, value in pairs:
        if name in result:
            raise ValueError("duplicate field")
        result[name] = value
    return result

def receipt_document(payload):
    if type(payload) is not str or len(payload) > 200:
        raise ValueError("document length")
    return json.loads(payload, object_pairs_hook=unique_object)

print(receipt_document('{"receipt":{"id":"R41","minor":125}}'))
try:
    receipt_document('{"receipt":{"minor":125,"minor":0}}')
except ValueError:
    print("duplicate rejected")''',"{'receipt': {'id': 'R41', 'minor': 125}}\nduplicate rejected",
'Decoding and duplicate checks take O(n) expected time and O(n) retained structure for n input characters. The small character cap is a fixture limit, not a network reception limit.',
['Ordinary decoding has already lost duplicate-name evidence.','Reject bytes before decoding and validate the resulting schema afterward.'],['python/json-validation','python/bounded-json-lines','python/strict-utf8-import'],subject='python-examples')

lesson('csv-duplicate-headers','Python CSV headers: reject duplicate names before row mapping',
'CSV header names become mapping keys in DictReader, so repeated names can hide an earlier column.',
'The fixture reads a header row first and checks that it is exactly the expected two-column set with no duplicate spelling. It then hands the remaining text to DictReader using those names. A repeated amount column is rejected before any row is accepted. The normal rows retain text values so a later step can parse amounts under a separate numeric rule.',
'Opening a real file needs an encoding, newline policy, byte cap, row cap and field-size bound. Checking after converting a row to a dict is too late. Column names that differ only by case are distinct here; choose a canonicalization rule before changing that contract. [[python/csv-import|CSV parsing]], [[python/bounded-csv|Import limits]] and [[python/json-duplicate-keys|Ambiguous JSON]] cover adjacent formats.',
r'''import csv
import io

def receipt_rows(text):
    if type(text) is not str or len(text) > 200:
        raise ValueError("input size")
    stream = io.StringIO(text, newline="")
    header = next(csv.reader(stream), None)
    if header is None or len(header) != 2 or set(header) != {"id", "minor"}:
        raise ValueError("header contract")
    rows = list(csv.DictReader(stream, fieldnames=header))
    if len(rows) > 5 or any(None in row or any(value is None for value in row.values()) for row in rows):
        raise ValueError("row width")
    return rows

print(receipt_rows("id,minor\nR41,125\nR42,75\n"))
try:
    receipt_rows("id,minor,minor\nR41,125,0\n")
except ValueError:
    print("duplicate header rejected")''',"[{'id': 'R41', 'minor': '125'}, {'id': 'R42', 'minor': '75'}]\nduplicate header rejected",
'Parsing is O(n) in bounded text length and materializes O(n) row text here. DictReader does not grant a streaming memory guarantee once its result is converted to a list.',
['Validate header names before row mapping.','A parsed numeric string is not yet a validated amount.'],['python/csv-import','python/bounded-csv','python/json-duplicate-keys'],subject='python-examples')

lesson('strict-utf8-import','Python UTF-8 imports: reject malformed bytes and unexpected BOMs',
'Strict UTF-8 decoding raises UnicodeDecodeError when an incoming byte sequence is malformed.',
'The receipt boundary caps the raw payload before decoding, rejects a leading UTF-8 byte-order mark, and decodes with the default strict error handler. A normal accented customer name survives unchanged. A malformed prefix is rejected instead of being replaced with a character that might change an identifier or signature input.',
'Using errors="ignore" or "replace" changes received data. If a format explicitly permits a BOM, declare that protocol and decode with an intentional policy; do not guess encodings. Normalization and text identity remain separate. [[python/strings-bytes|Bytes versus text]], [[python/unicode-normalization|Normalization]] and [[python/json-duplicate-keys|Structured decoding]] connect the layers.',
r'''def decode_receipt(raw):
    if type(raw) is not bytes or len(raw) > 80:
        raise ValueError("byte budget")
    if raw.startswith(b"\xef\xbb\xbf"):
        raise ValueError("BOM not permitted")
    return raw.decode("utf-8")

print(decode_receipt("Café R41".encode("utf-8")))
for payload in (b"\xc3(", b"\xef\xbb\xbfR41"):
    try:
        decode_receipt(payload)
    except (UnicodeDecodeError, ValueError):
        print("bytes rejected")''','Café R41\nbytes rejected\nbytes rejected',
'Validation and decoding take O(n) time and allocate O(n) text for n bytes. The limit is applied to already received bytes; an HTTP server must cap reception upstream.',
['A replacement character is a data change, not validation.','Do not confuse an encoding policy with Unicode normalization.'],['python/strings-bytes','python/unicode-normalization','python/json-duplicate-keys'],subject='python-types')

lesson('decimal-inexact-trap','Python Decimal Inexact trap: reject fractional minor units',
'The Decimal Inexact signal records a rounding operation that discards nonzero digits.',
'The amount parser accepts short decimal strings, checks finiteness and nonnegativity, then uses a local context with an Inexact trap while quantizing to two places. A cent-exact input becomes integer minor units. An amount with three nonzero fractional places fails instead of being rounded silently. The local context keeps this choice out of unrelated decimal work.',
'Inexact differs from Rounded: dropping a trailing zero may set Rounded without losing value. Construct Decimal from the input string, not a binary float. Currency-specific scale and limits still belong to the application contract. [[python/decimal-money|Decimal amounts]], [[python/fraction-ratios|Exact ratios]] and [[python/quantile-policy|Numeric policy]] give other representations.',
r'''from decimal import Decimal, Inexact, InvalidOperation, localcontext

def minor_units(text):
    if type(text) is not str or not 1 <= len(text) <= 12:
        raise ValueError("amount length")
    try:
        value = Decimal(text)
        if not value.is_finite() or not 0 <= value <= 10000:
            raise ValueError("amount range")
        with localcontext() as context:
            context.traps[Inexact] = True
            cents = value.quantize(Decimal("0.01"))
        return int(cents * 100)
    except (InvalidOperation, Inexact) as cause:
        raise ValueError("fractional minor unit") from cause

print(minor_units("12.50"))
print(minor_units("12.500"))
try:
    minor_units("12.501")
except ValueError:
    print("fractional cent rejected")''','1250\n1250\nfractional cent rejected',
'The fixture bounds input length and amount magnitude. Decimal operation cost still depends on coefficient digits and context precision; a real money parser must also choose an explicit currency scale.',
['Inexact and Rounded are different signals.','Creating Decimal from float imports a binary approximation.'],['python/decimal-money','python/fraction-ratios','python/quantile-policy'],subject='python-types')
lesson('dataclass-replace-alias','Python dataclasses.replace: a new record can retain old mutable fields',
'dataclasses.replace constructs a new dataclass instance with selected fields changed; unchanged field values are passed through.',
'The original dispatch record owns a list of receipt IDs. Replacing its region gives a new record but keeps that same list object. Mutating the new record changes the old record’s receipt list too. The second replacement supplies an explicit copy and isolates later appends. A frozen dataclass would prevent rebinding a field, not mutation of a list held in it.',
'Shallow copy semantics matter when records cross request, worker or cache boundaries. A list of nested mutable objects needs a deeper ownership policy. [[python/dataclasses|Dataclass defaults]], [[python/copy-deepcopy|Copy depth]] and [[python/python-variables|Name aliasing]] cover the surrounding rules.',
r'''from dataclasses import dataclass, replace

@dataclass
class DispatchBatch:
    region: str
    receipt_ids: list[str]

original = DispatchBatch("north", ["R41"])
shared = replace(original, region="east")
shared.receipt_ids.append("R42")
isolated = replace(original, region="west", receipt_ids=list(original.receipt_ids))
isolated.receipt_ids.append("R43")
print(original.receipt_ids)
print(isolated.receipt_ids)
print(shared.receipt_ids is original.receipt_ids)''',"['R41', 'R42']\n['R41', 'R42', 'R43']\nTrue",
'The replacement itself has bounded field work. Copying n IDs takes O(n) time and O(n) outer storage; nested objects would remain shared.',
['A new dataclass instance is not a deep snapshot.','Frozen fields do not freeze mutable values.'],['python/dataclasses','python/copy-deepcopy','python/python-variables'],subject='python-advanced')

lesson('dict-union-shallow','Python dictionary union: new mapping, shared nested values',
'The dictionary union operator creates a new outer mapping, with right-hand values winning duplicate keys.',
'The region defaults contain a list of allowed depots. A union overrides only the dispatch window and keeps the original list as a shared value. Appending through the merged mapping changes the defaults. Copying that list before publication isolates it. A merge is a key-level choice, not a full configuration snapshot.',
'A configuration layer must decide whether later mutations are allowed at all. Nested dictionaries and lists need their own copies or an immutable representation. [[python/configuration-precedence|Layer order]], [[python/chainmap-configuration|Live layered views]] and [[python/copy-deepcopy|Copy depth]] show alternatives.',
r'''defaults = {"window": 30, "depots": ["DEL"]}
configured = defaults | {"window": 15}
configured["depots"].append("BOM")
owned = configured | {"depots": list(configured["depots"])}
owned["depots"].append("MAA")
print(defaults)
print(configured["window"])
print(owned["depots"])''',"{'window': 30, 'depots': ['DEL', 'BOM']}\n15\n['DEL', 'BOM', 'MAA']",
'A union copies O(n+m) outer entries in ordinary mappings; copying the depot list adds O(k) time and storage for k depots. Deep ownership costs depend on the entire nested object graph.',
['Right-hand precedence does not copy nested values.','Do not publish a shared mutable configuration as a snapshot.'],['python/configuration-precedence','python/chainmap-configuration','python/copy-deepcopy'],subject='python-types')

lesson('tuple-mutable-hash-interview','Python interview: a tuple can be unhashable when it contains a list',
'A tuple is immutable as a container, but hashing it requires every contained value to be hashable.',
'The receipt key holds a route and a list of identifiers. The tuple cannot swap fields, yet the list can change, so using the tuple as a dictionary key raises TypeError. Converting the identifiers to a tuple gives a hashable key for these string elements. The accepted key is then used for one lookup.',
'Calling tuple() is only a shallow conversion. A tuple containing another unhashable element still fails, and a custom hashable object with mutable equality state can corrupt mapping lookup expectations. [[python/hash-equality|Hash/equality]], [[python/hash-key-mutation-interview|Mutable key state]] and [[python/tuples|Tuple ownership]] are the next checks.',
r'''receipt_ids = ["R41", "R42"]
rejected_key = ("north", receipt_ids)
try:
    {rejected_key: 2}
except TypeError:
    print("mutable member rejected")
accepted_key = ("north", tuple(receipt_ids))
counts = {accepted_key: 2}
print(counts[("north", ("R41", "R42"))])''','mutable member rejected\n2',
'For k identifiers, creating the nested tuple and hashing it cost O(k) work on first use. The mapping retains the tuple and its referenced immutable strings.',
['Tuple immutability does not make every member hashable.','A shallow tuple conversion does not freeze nested objects.'],['python/hash-equality','python/hash-key-mutation-interview','python/tuples'],subject='python-interview')

lesson('sqlite-unique-null','Python SQLite UNIQUE with NULL: an absent key can repeat',
'A SQLite UNIQUE constraint permits multiple NULL values because NULL is not equal to another NULL.',
'An in-memory receipt table declares a unique external ID, then inserts two rows without one. Both rows survive. The fixture separately attempts two equal non-null IDs and observes an IntegrityError. This distinction matters when a deduplication key must be present for every accepted row.',
'Use NOT NULL together with UNIQUE when the business rule requires exactly one non-null key. A nullable unique column can be valid when absence is allowed, but it is not a replay identity. [[python/sqlite-foreign-key-boundary|Connection constraints]], [[python/idempotent-jobs|Replay identity]] and [[python/sqlite-transactions|Transaction policy]] supply adjacent guarantees.',
r'''import sqlite3

connection = sqlite3.connect(":memory:")
connection.execute("CREATE TABLE receipt(id INTEGER PRIMARY KEY, external_id TEXT UNIQUE)")
connection.execute("INSERT INTO receipt(external_id) VALUES (NULL), (NULL), ('R41')")
try:
    connection.execute("INSERT INTO receipt(external_id) VALUES ('R41')")
except sqlite3.IntegrityError:
    print("duplicate ID rejected")
print("missing IDs:", connection.execute("SELECT COUNT(*) FROM receipt WHERE external_id IS NULL").fetchone()[0])
connection.close()''','duplicate ID rejected\nmissing IDs: 2',
'The demonstration inserts a fixed number of rows. Indexed uniqueness has storage proportional to retained distinct values; contention and durable commit behavior are not measured here.',
['UNIQUE alone does not prohibit multiple NULLs.','A missing deduplication key cannot identify a replayed event.'],['python/sqlite-foreign-key-boundary','python/idempotent-jobs','python/sqlite-transactions'],subject='python-examples')

lesson('sqlite-conflict-update','Python SQLite upsert: make a replay update explicit',
'INSERT ... ON CONFLICT can route a uniqueness collision to an update instead of an exception.',
'The owned connection stores a receipt ID and amount. Repeating the same ID updates its amount rather than adding a second row, so the printed row count remains one. The conflict target is a primary key; a different constraint collision would not be handled by this clause. The fixture uses a transaction but makes no claim about remote event delivery.',
'An upsert is not automatically idempotent. If a retry carries a different amount, the second write changes state, as this fixture shows. Define whether replays must be identical or rejected before using this pattern for payments. [[python/idempotent-jobs|Replay contracts]], [[python/sqlite-transactions|Commit rules]] and [[python/sqlite-unique-null|Present keys]] should be read together.',
r'''import sqlite3

connection = sqlite3.connect(":memory:")
connection.execute("CREATE TABLE receipt(id TEXT PRIMARY KEY, minor INTEGER NOT NULL CHECK(minor >= 0))")
def store(identifier, minor):
    with connection:
        connection.execute(
            "INSERT INTO receipt(id, minor) VALUES (?, ?) "
            "ON CONFLICT(id) DO UPDATE SET minor=excluded.minor",
            (identifier, minor),
        )

store("R41", 125)
store("R41", 150)
print(connection.execute("SELECT id, minor FROM receipt").fetchall())
connection.close()''',"[('R41', 150)]",
'With an indexed key, lookup and update cost depend on the database index and storage engine state. Two small in-memory writes do not establish throughput, durability or cross-process ordering.',
['Upsert can overwrite different replay data.','Name the intended conflict target and validate the payload before writing.'],['python/idempotent-jobs','python/sqlite-transactions','python/sqlite-unique-null'],subject='python-examples')
lesson('monotonic-window-maximum','Python sliding-window maximum: retain only useful deque indexes',
'A monotonic deque keeps candidate indexes ordered by decreasing value for each fixed-size sliding window.',
'The queue drops indexes outside the current three-sample window and removes smaller or equal trailing candidates before appending the new index. Its front is the maximum for each completed window. Keeping indexes, rather than only values, makes expiry unambiguous even when measurements repeat.',
'The function rejects a zero or oversized window and boolean measurements. The deque never needs every historic sample, but the returned output has one value per window. [[python/sliding-window|Window boundaries]], [[python/counter-deque|Deque operations]] and [[python/heap-top-k|Heap selection]] solve different ordering problems.',
r'''from collections import deque

def window_peaks(samples, width):
    if type(samples) is not list or len(samples) > 100 or any(type(value) is not int for value in samples):
        raise ValueError("bounded integer samples")
    if type(width) is not int or not 1 <= width <= len(samples):
        raise ValueError("window width")
    candidates = deque()
    peaks = []
    for index, value in enumerate(samples):
        while candidates and candidates[0] <= index - width:
            candidates.popleft()
        while candidates and samples[candidates[-1]] <= value:
            candidates.pop()
        candidates.append(index)
        if index + 1 >= width:
            peaks.append(samples[candidates[0]])
    return peaks

print(window_peaks([4, 1, 3, 5, 2], 3))
try:
    window_peaks([4, 1], 0)
except ValueError:
    print("width rejected")''','[4, 5, 5]\nwidth rejected',
'Each index enters and leaves the deque at most once, giving O(n) time and O(width) candidate storage. Returning all n-width+1 peaks adds O(n) result storage.',
['Expiring by value cannot distinguish repeated samples.','A heap needs stale-index handling for this window contract.'],['python/sliding-window','python/counter-deque','python/heap-top-k'],subject='python-dsa')

lesson('zero-one-bfs','Python 0-1 BFS: shortest paths when every edge costs zero or one',
'0-1 BFS uses a deque to find shortest path costs in a graph whose edge weights are restricted to zero and one.',
'The route graph has four stations. A zero-cost transfer is pushed to the front; a one-cost leg is pushed to the back. The A-to-C-to-B-to-D path uses only zero-cost edges, so its total is zero. The wrapper checks every endpoint and weight before exploring the graph.',
'This is not correct for a weight of two or a negative edge. The deque may retain stale entries after an improvement; comparing the popped cost with the best-known distance avoids processing stale work. [[python/dijkstra|General nonnegative weights]], [[python/graph-bfs|Unit weights]] and [[python/bellman-ford|Negative edges]] define the neighboring algorithms.',
r'''from collections import deque

def transfer_cost(graph, start, goal):
    if type(graph) is not dict or not 1 <= len(graph) <= 30 or start not in graph or goal not in graph:
        raise ValueError("graph boundary")
    if any(type(edges) is not list or len(edges) > 30 or any(type(edge) is not tuple or len(edge) != 2 or edge[0] not in graph or type(edge[1]) is not int or edge[1] not in (0, 1) for edge in edges) for edges in graph.values()):
        raise ValueError("binary weights")
    distances = {start: 0}
    queue = deque([(start, 0)])
    while queue:
        station, cost = queue.popleft()
        if cost != distances[station]:
            continue
        for neighbor, weight in graph[station]:
            next_cost = cost + weight
            if next_cost < distances.get(neighbor, float("inf")):
                distances[neighbor] = next_cost
                if weight == 0:
                    queue.appendleft((neighbor, next_cost))
                else:
                    queue.append((neighbor, next_cost))
    return distances.get(goal)

routes = {"A": [("B", 1), ("C", 0)], "B": [("D", 0)],
          "C": [("B", 0), ("D", 1)], "D": []}
print(transfer_cost(routes, "A", "D"))
try:
    transfer_cost({"A": [("B", 2)], "B": []}, "A", "B")
except ValueError:
    print("weight rejected")''','0\nweight rejected',
'Validation takes O(V+E) time. Under the zero-or-one rule, deque relaxations take O(V+E) time and retain O(V+E) queued state in this implementation; the tiny graph is not a benchmark.',
['Use Dijkstra for a general nonnegative weight.','Do not accept an undeclared neighbor or silently reinterpret a weight.'],['python/dijkstra','python/graph-bfs','python/bellman-ford'],subject='python-dsa')

lesson('running-median-heaps','Python running median: two heaps with an exact even-count result',
'A running median partitions seen values between a max-heap of lower values and a min-heap of upper values.',
'The lower heap stores negated integers and may hold one extra value. Every insertion restores order and heap-size balance. Odd prefixes report the lower top; even prefixes return a Fraction of the two tops, so a half-unit result is exact rather than silently converted to a binary float.',
'This is an insertion-only stream; deleting old samples requires delayed deletion or a different structure. The wrapper caps input count and value magnitude. [[python/heap-top-k|Heap operations]], [[python/quantile-policy|Quantile definitions]] and [[python/fraction-ratios|Exact fractions]] cover related choices.',
r'''from fractions import Fraction
from heapq import heappush, heappop

def running_medians(values):
    if type(values) is not list or len(values) > 100 or any(type(value) is not int or abs(value) > 10000 for value in values):
        raise ValueError("bounded samples")
    lower, upper, result = [], [], []
    for value in values:
        if not lower or value <= -lower[0]:
            heappush(lower, -value)
        else:
            heappush(upper, value)
        if len(lower) > len(upper) + 1:
            heappush(upper, -heappop(lower))
        elif len(upper) > len(lower):
            heappush(lower, -heappop(upper))
        result.append(Fraction(-lower[0]) if len(lower) > len(upper)
                      else Fraction(-lower[0] + upper[0], 2))
    return result

print([str(value) for value in running_medians([7, 2, 9, 4])])
try:
    running_medians([True])
except ValueError:
    print("boolean rejected")''',"['7', '9/2', '7', '11/2']\nboolean rejected",
'Each insertion costs O(log n) and both heaps retain O(n) values; returning each median also retains O(n) fractions. This does not provide a constant-memory sliding median.',
['Rebalance both size and ordering.','An average of two integer values can be fractional.'],['python/heap-top-k','python/quantile-policy','python/fraction-ratios'],subject='python-dsa')

lesson('capacity-binary-search','Python binary search on capacity: prove the feasibility predicate',
'Binary search can find the smallest integer capacity when feasibility is monotone: once a capacity works, every larger one works.',
'The packing rule keeps order and assigns each whole shipment to one day. The minimum possible capacity is the largest single shipment; the maximum is their total weight. For each midpoint the scan counts days needed. A feasible midpoint lowers the upper bound, while an infeasible one raises the lower bound. Three days need capacity five for the stated sequence.',
'This is not bin packing: shipments are never reordered or split. A bad feasibility rule can invalidate the monotonic property and make binary search return nonsense. [[python/binary-search|Index search]], [[python/weighted-intervals|Scheduling contracts]] and [[python/knapsack|Different packing problem]] clarify the distinction.',
r'''def minimum_daily_capacity(weights, days):
    if type(weights) is not list or not 1 <= len(weights) <= 100 or any(type(weight) is not int or not 1 <= weight <= 1000 for weight in weights):
        raise ValueError("shipment weights")
    if type(days) is not int or not 1 <= days <= len(weights):
        raise ValueError("day count")
    def feasible(capacity):
        used, load = 1, 0
        for weight in weights:
            if load + weight > capacity:
                used += 1
                load = 0
            load += weight
        return used <= days
    low, high = max(weights), sum(weights)
    while low < high:
        middle = (low + high) // 2
        if feasible(middle):
            high = middle
        else:
            low = middle + 1
    return low

print(minimum_daily_capacity([3, 2, 2, 4, 1], 3))
try:
    minimum_daily_capacity([3, 2], True)
except ValueError:
    print("day count rejected")''','5\nday count rejected',
'Each feasibility scan takes O(n) time. Searching the integer range takes O(n log S) time for total weight S, with O(1) extra working storage beyond the input.',
['Do not use this predicate if shipments may be reordered or split.','Start the lower bound at the largest shipment.'],['python/binary-search','python/weighted-intervals','python/knapsack'],subject='python-dsa')

lesson('validated-jsonl-ledger-project','Python project: validate a JSONL batch before one SQLite commit',
'A batch importer can parse and validate every record before publishing the accepted set in one database transaction.',
'The project caps the already received text, rejects duplicate JSON names, checks each receipt schema and ID uniqueness, then inserts the staged rows inside one transaction. A second batch repeats a receipt ID; the database constraint rejects it, and the new batch does not leave a partial row. The first committed receipt remains. Parsing and database publication are separate boundaries.',
'The sample is an owned in-memory connection, not a hosted ingestion service. Production work needs a streaming byte cap, durable database, retry identity, authentication, and crash recovery. [[python/json-duplicate-keys|Field ambiguity]], [[python/sqlite-transactions|Commit scope]], [[python/idempotent-jobs|Replay meaning]] and [[python/bounded-json-lines|Line limits]] are prerequisites.',
r'''import json
import sqlite3

def unique_pairs(pairs):
    record = {}
    for key, value in pairs:
        if key in record:
            raise ValueError("duplicate key")
        record[key] = value
    return record

def import_batch(connection, text):
    if type(text) is not str or len(text) > 400:
        raise ValueError("batch size")
    lines = text.splitlines()
    if not 1 <= len(lines) <= 5:
        raise ValueError("batch rows")
    staged = []
    seen = set()
    for line in lines:
        row = json.loads(line, object_pairs_hook=unique_pairs)
        if type(row) is not dict or set(row) != {"id", "minor"}:
            raise ValueError("record shape")
        if type(row["id"]) is not str or not row["id"].startswith("R") or not row["id"][1:].isdigit() or len(row["id"]) > 8:
            raise ValueError("receipt ID")
        if type(row["minor"]) is not int or not 0 <= row["minor"] <= 100000 or row["id"] in seen:
            raise ValueError("amount or duplicate")
        seen.add(row["id"])
        staged.append((row["id"], row["minor"]))
    with connection:
        connection.executemany("INSERT INTO receipt(id, minor) VALUES (?, ?)", staged)

connection = sqlite3.connect(":memory:")
connection.execute("CREATE TABLE receipt(id TEXT PRIMARY KEY, minor INTEGER NOT NULL)")
import_batch(connection, '{"id":"R41","minor":125}')
try:
    import_batch(connection, '{"id":"R42","minor":75}\n{"id":"R41","minor":0}')
except sqlite3.IntegrityError:
    print("batch rolled back")
print(connection.execute("SELECT id, minor FROM receipt ORDER BY id").fetchall())
connection.close()''',"batch rolled back\n[('R41', 125)]",
'For n bounded input characters and r rows, parsing and staging use O(n) time and O(n) working storage. SQLite index operations and durable storage costs are additional; an in-memory commit is not a durability test.',
['Validate the whole batch before starting publication.','A transaction prevents partial inserts here but does not make a changed replay acceptable.'],['python/json-duplicate-keys','python/sqlite-transactions','python/idempotent-jobs','python/bounded-json-lines'],subject='python-projects')
for subject,title,slugs in [
 ('python-types','Text and numeric import boundaries',['strict-utf8-import','decimal-inexact-trap','dict-union-shallow']),
 ('python-advanced','Copying records without copying ownership',['dataclass-replace-alias']),
 ('python-interview','Container hash trace',['tuple-mutable-hash-interview']),
 ('python-examples','Ambiguous input fields',['json-duplicate-keys','csv-duplicate-headers']),
 ('python-examples','SQLite key and replay rules',['sqlite-unique-null','sqlite-conflict-update']),
 ('python-dsa','Bounded windows, weighted routes and capacity',['monotonic-window-maximum','zero-one-bfs','running-median-heaps','capacity-binary-search']),
 ('python-projects','Validated batch publication',['validated-jsonl-ledger-project'])]:
 group(subject,title,slugs)

INTEGRITY_QUESTIONS=[
 ('What does object_pairs_hook preserve before a JSON object becomes a dict?',['Only the final value','The ordered field pairs, including duplicates','A database transaction','The original byte encoding'],1,'It receives ordered pairs, so a repeated name can be rejected.'),
 ('Why inspect a CSV header before DictReader maps its rows?',['Duplicate names may overwrite an earlier column','It makes numeric strings integers','It authorizes every row','It removes all quoted fields'],0,'Mapping conversion can lose the earlier repeated column.'),
 ('What happens when strict UTF-8 sees malformed bytes?',['It guesses Latin-1','It drops the bytes','It raises UnicodeDecodeError','It silently inserts a space'],2,'Strict decoding refuses malformed sequences.'),
 ('Why can 12.500 pass an Inexact trap for cents?',['The last zero loses no value','The trap is disabled','It is a float','Quantize always raises'],0,'Dropping only a trailing zero can be Rounded without being Inexact.'),
 ('What does dataclasses.replace retain for an unchanged list field?',['A deep copy','The same list object','An immutable tuple','No field value'],1,'The new instance receives the existing list reference.'),
 ('What does a dictionary union copy here?',['All nested lists','Only outer mapping entries','The module cache','No mapping at all'],1,'Nested mutable values remain shared unless copied explicitly.'),
 ('Why does a tuple containing a list fail as a dict key?',['Tuple fields may be swapped','The list is unhashable','Strings cannot be keys','The tuple has two fields'],1,'Tuple hashing depends on the hashability of its members.'),
 ('Can two SQLite rows with NULL satisfy a UNIQUE external_id column?',['Yes','No','Only when one row is deleted','Only without an index'],0,'NULL does not compare equal to another NULL for this uniqueness rule.'),
 ('What happens when the upsert repeats an ID with a different amount?',['It rejects every replay','It changes the stored amount','It inserts a second ID','It rolls back all prior transactions'],1,'This explicit conflict action updates the row; it is not an idempotency check.'),
 ('Why does a monotonic window deque store indexes?',['To identify expiry at the left boundary','To make values immutable','To sort the entire input','To count duplicate JSON keys'],0,'An index identifies whether a candidate has left the active window.'),
 ('Which edge costs are accepted by 0-1 BFS?',['Any signed integer','Only zero and one','Any positive float','Only two and three'],1,'The deque ordering proof depends on binary nonnegative costs.'),
 ('What does the JSONL project do before its SQLite writes?',['Stage and validate all rows','Insert the first row immediately','Guess missing IDs','Convert errors to zero amounts'],0,'Validation finishes before the transaction publishes the staged rows.'),
]
quiz_slug='python-integrity-contracts';quiz_title='Python input, storage and algorithm boundary quiz'
BANKS[quiz_slug]=(quiz_title,INTEGRITY_QUESTIONS)
quiz_refs=['python/json-duplicate-keys','python/csv-duplicate-headers','python/strict-utf8-import','python/sqlite-unique-null','python/monotonic-window-maximum','python/zero-one-bfs']
quiz=copy.deepcopy(lookup['quizzes/python-basics']);quiz_path='quizzes/'+quiz_slug
quiz.update(id=str(uuid.uuid5(uuid.NAMESPACE_URL,'https://aitrove.in/'+quiz_path)),path=quiz_path,title=quiz_title,summary='Twelve explained checks on input identity, aliasing, database keys and bounded algorithms.',sort_order=750+len(added),published_at=stamp,updated_at=stamp)
quiz['body']=para('This self-check traces where received data loses identity, where a new container still shares state, and which algorithm contracts accept a weighted input.')+'<h2>Review the related lessons</h2><ul>'+''.join('<li><a href="/'+path+'">'+html.escape(lookup[path]['title'])+'</a></li>' for path in quiz_refs)+'</ul><h3>Common Mistakes</h3>'+para('A correct answer does not validate an uploaded payload, persistent service or unbounded graph. Run the linked fixtures and inspect their limits.')
quiz['data']['questions']=[dict(prompt=prompt,options=options,answer=answer,explanation=explanation) for prompt,options,answer,explanation in INTEGRITY_QUESTIONS]
quiz['data']['related']=[dict(path=path,title=lookup[path]['title']) for path in quiz_refs]
upsert(quiz);added.append(quiz_path)

INTEGRITY_REVERSE={
 'python/json-validation':['json-duplicate-keys','validated-jsonl-ledger-project'],
 'python/bounded-csv':['csv-duplicate-headers'],
 'python/strings-bytes':['strict-utf8-import'],
 'python/decimal-money':['decimal-inexact-trap'],
 'python/dataclasses':['dataclass-replace-alias'],
 'python/configuration-precedence':['dict-union-shallow'],
 'python/hash-equality':['tuple-mutable-hash-interview'],
 'python/sqlite-transactions':['sqlite-unique-null','sqlite-conflict-update'],
 'python/sliding-window':['monotonic-window-maximum'],
 'python/dijkstra':['zero-one-bfs'],
 'python/heap-top-k':['running-median-heaps'],
 'python/binary-search':['capacity-binary-search']}
for original,slugs in INTEGRITY_REVERSE.items():
 targets=['python/'+slug for slug in slugs]
 assert original in lookup and all(path in lookup for path in targets)
 item=lookup[original];marker='<h2>Follow the integrity boundary</h2>'
 item['body']=item['body'].split(marker)[0]+marker+para(', '.join('[['+path+'|'+lookup[path]['title']+']]' for path in targets)+'.')
 known={related['path'] for related in item['data'].get('related',[])}
 item['data'].setdefault('related',[]).extend({'path':path,'title':lookup[path]['title']} for path in targets if path not in known)
 item['updated_at']=stamp
