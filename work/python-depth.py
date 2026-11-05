"""Third Python pass: original programs and explicit failure contracts."""
lesson('memoryview-buffers','Python memoryview: shared buffers and explicit release',
'A memoryview exposes a supported buffer without copying its bytes; a view of mutable storage can write into that storage.',
'The upload header belongs to a bytearray. A sliced view selects two bytes and changing that view changes the owned header. The program releases both views before growing the bytearray. This distinction matters when a parser returns a view: the caller receives access to the original buffer, not a stable snapshot. Use bytes when a retained independent result is required.',
'An exported view prevents size-changing operations on this bytearray. Releasing a parent view does not revoke a separately retained child view. A view can also have a format or stride that a downstream API cannot consume as contiguous bytes. [[python/strings-bytes|Byte encoding]] and [[python/numpy-views|Array aliases]] have comparable ownership concerns.',
r'''header = bytearray(b"ABCD")
view = memoryview(header)
selected = view[1:3]
selected[0] = ord("Z")
print(bytes(header))
try:
    header.append(0)
except BufferError:
    print("resize blocked while exported")
selected.release()
view.release()
header.append(0)
print(len(header))''',"b'AZCD'\nresize blocked while exported\n5",
'Creating this contiguous view retains references without duplicating n buffer bytes. Converting it to bytes copies O(n) data. A tiny slice can keep a large exporter alive; avoid calling retained views free storage.',
['A view is not an immutable snapshot of a mutable exporter.','Release every retained child before resizing its bytearray.'],['python/strings-bytes','python/numpy-views','python/copy-deepcopy'],subject='python-types')

lesson('hash-equality','Python hash and equality: immutable dictionary keys',
'A hashable dictionary key needs a hash that remains stable during its lifetime, and equal keys must produce equal hashes.',
'The receipt key has two immutable fields and value-based equality supplied by a frozen dataclass. Separately constructed equal keys retrieve the same ledger entry. The stored amount is not part of the key. Keeping identity separate from changing state avoids losing an entry after a field used by its hash changes.',
'Frozen dataclasses prevent their normal field assignment; they do not recursively freeze nested objects. This key uses only a string and an integer. A class that defines equality without a suitable hash becomes unhashable. Hash collisions are legal: dictionary lookup still compares candidate keys. [[python/dictionaries|Dictionary lookup]] and [[python/dataclasses|Frozen state]] explain the surrounding rules.',
r'''from dataclasses import dataclass

@dataclass(frozen=True)
class ReceiptKey:
    region: str
    sequence: int

ledger = {ReceiptKey("DEL", 41): 1250}
lookup_key = ReceiptKey("DEL", 41)
print(ledger[lookup_key])
print(hash(lookup_key) == hash(ReceiptKey("DEL", 41)))
try:
    ledger[["DEL", 41]] = 1250
except TypeError:
    print("mutable list rejected as key")''','1250\nTrue\nmutable list rejected as key',
'Dictionary operations have expected constant lookup work under suitable hash behavior, but collisions can require more comparisons. Computing a key hash also has field-dependent cost. Do not persist Python hash values as stable cross-process identifiers.',
['Equal keys must have equal hashes; unequal keys may also collide.','A frozen wrapper can still contain unsuitable mutable fields.'],['python/dictionaries','python/dataclasses','python/sets'],subject='python-types')

lesson('enums','Python Enum: parse wire values into a closed state set',
'Enum names a fixed set of members and separates those members from unchecked wire strings.',
'The dispatcher accepts only the two declared task states. Constructing a member from its wire value validates membership; it does not infer a new state from a spelling variation. The member name and its wire value serve different uses. Renaming a Python identifier need not change the serialized value.',
'An enum is not a workflow engine. It cannot prove that a transition from queued to delivered is permitted for a particular job. Normal Enum members are not interchangeable with strings, while IntEnum and StrEnum have different comparison behavior. Keep those choices explicit. [[python/pattern-matching|Branching]] and [[python/idempotent-jobs|Job transitions]] show the next boundary.',
r'''from enum import Enum, unique

@unique
class DispatchState(Enum):
    QUEUED = "queued"
    DELIVERED = "delivered"

state = DispatchState("queued")
print(state.name, state.value)
print(state == "queued")
try:
    DispatchState("QUEUE")
except ValueError:
    print("unknown wire state rejected")''','QUEUED queued\nFalse\nunknown wire state rejected',
'This small declared set has bounded parsing work. The enum stores its members once at class construction. Domain checks, persistence and transition history cost more and remain application responsibilities.',
['Membership does not prove a state transition is authorized.','Changing wire values can break stored records even when member names stay similar.'],['python/pattern-matching','python/idempotent-jobs','python/json-validation'],subject='python-types')

lesson('slots','Python slots: attribute layout without deep immutability',
'__slots__ declares named instance storage and can omit an instance dictionary when its inheritance hierarchy permits that layout.',
'The parcel record admits two attributes. A misspelled third attribute fails immediately rather than silently creating unused state. Updating quantity still works: slots restrict attribute layout, not mutation. That distinction is useful when a large collection of small records should not accept arbitrary extension fields.',
'A subclass without its own slots can regain an instance dictionary. Weak references need suitable support, commonly a __weakref__ slot. Multiple inheritance with incompatible layouts can fail at class creation. Use measured object counts and actual memory profiling before selecting slots solely for size; [[python/weak-references|Weak references]] and [[python/mro-super|Inheritance order]] affect the result.',
r'''class ParcelRecord:
    __slots__ = ("receipt_id", "quantity")
    def __init__(self, receipt_id, quantity):
        self.receipt_id = receipt_id
        self.quantity = quantity

parcel = ParcelRecord("R-0041", 2)
parcel.quantity = 3
print(parcel.quantity)
print(hasattr(parcel, "__dict__"))
try:
    parcel.quanity = 4
except AttributeError:
    print("unknown attribute rejected")''','3\nFalse\nunknown attribute rejected',
'The fixture makes no portable byte-size claim. Slots can avoid a per-instance dictionary but do not shrink referenced strings or other reachable objects. Lookup and allocation effects depend on the interpreter and hierarchy.',
['Slots do not make a record immutable.','A subclass can restore a dictionary unless its layout also restricts it.'],['python/classes','python/mro-super','python/weak-references'],subject='python-advanced')

lesson('weak-references','Python weak references: a cache does not own its values',
'A weak reference observes a supported object without keeping that object alive solely through the reference.',
'The receipt cache uses weak values. The caller owns the record through a strong reference; the cache only helps find it while it remains alive. Deleting that owner and collecting unreachable objects leaves no cached value. This cache cannot promise retention between two separate lookups.',
'Retrieve a weak value once into a local strong reference before using it. Testing membership and then fetching again creates a lifetime gap. Many built-in values cannot be weakly referenced directly. Weak references are also unsuitable for resource cleanup guarantees; [[python/exit-stack|Explicit cleanup]] controls acquired resources independently of garbage collection.',
r'''import gc
from weakref import WeakValueDictionary

class ReceiptRecord:
    def __init__(self, receipt_id):
        self.receipt_id = receipt_id

cache = WeakValueDictionary()
owned_record = ReceiptRecord("R-0041")
cache[owned_record.receipt_id] = owned_record
print(cache.get("R-0041") is owned_record)
del owned_record
gc.collect()
print(cache.get("R-0041") is None)''','True\nTrue',
'The cache retains keys and weak-reference bookkeeping rather than owning the entire value graph. Collection timing is interpreter-dependent. This fixture calls collection explicitly; production code must tolerate a value disappearing whenever no strong owner remains.',
['A weak cache is not a durable store or retention promise.','Hold the retrieved value locally instead of checking membership and fetching later.'],['python/slots','python/python-variables','python/exit-stack'],subject='python-advanced')

lesson('exit-stack','Python ExitStack: unwind partially acquired resources',
'ExitStack records cleanup actions and runs them in reverse registration order when its context exits.',
'The import acquires two owned in-memory streams before a third acquisition fails. Previously acquired streams close through the stack even though the main import never starts. Register cleanup immediately after each successful acquisition. A separate close callback records order so the failure path can be inspected without using a real service.',
'ExitStack.callback does not suppress an exception. Context managers entered through enter_context may have different exit behavior. A callback that raises can change the visible failure, so cleanup itself needs a failure policy. The stack does not close resources merely because it is garbage collected. [[python/context-managers|Context management]] and [[python/exceptions|Failure propagation]] supply the underlying rules.',
r'''from contextlib import ExitStack
from io import StringIO

closed = []
def release(stream, label):
    stream.close()
    closed.append(label)

streams = []
try:
    with ExitStack() as stack:
        for label in ("receipts", "prices"):
            stream = StringIO(label)
            streams.append(stream)
            stack.callback(release, stream, label)
        raise OSError("third input unavailable")
except OSError:
    print("acquisition failed")
print(closed)
print(all(stream.closed for stream in streams))''',"acquisition failed\n['prices', 'receipts']\nTrue",
'Registering k callbacks retains O(k) cleanup state. Unwinding takes the sum of their costs. Resource acquisition and close latency are external to the stack bookkeeping and may block.',
['Register cleanup before attempting the next acquisition.','Do not depend on stack garbage collection to release resources.'],['python/context-managers','python/pathlib-files','python/exceptions'],subject='python-advanced')

lesson('toml-configuration','Python tomllib: parse configuration and validate its schema',
'Tomllib parses TOML into Python values; parsing does not enforce an application configuration schema.',
'The dispatch file supplies an exact field set, one known region and a bounded worker count. The schema rejects a TOML boolean for workers even though Python considers bool an int subclass. Keeping parser errors separate from domain errors helps distinguish malformed files from well-formed unsupported configuration.',
'Tomllib.loads consumes text; load expects a binary file. Neither writes TOML. The fixture bounds text length before parsing, but a real file read must enforce a byte budget before materializing it. Configuration strings may contain secrets, so validation failures should name a field without echoing its value. [[python/configuration-precedence|Source precedence]] and [[python/log-redaction|Diagnostic redaction]] extend this contract.',
r'''import tomllib

def dispatch_config(text):
    if len(text) > 1024:
        raise ValueError("configuration budget exceeded")
    parsed = tomllib.loads(text)
    if set(parsed) != {"region", "workers"}:
        raise ValueError("unexpected configuration fields")
    if parsed["region"] not in {"DEL", "BOM"}:
        raise ValueError("unknown region")
    if type(parsed["workers"]) is not int or not 1 <= parsed["workers"] <= 8:
        raise ValueError("workers must be an integer from 1 to 8")
    return parsed

print(dispatch_config('region="DEL"\nworkers=3'))
try:
    dispatch_config('region="DEL"\nworkers=true')
except ValueError:
    print("boolean worker count rejected")''',"{'region': 'DEL', 'workers': 3}\nboolean worker count rejected",
'Parsing and validation retain the parsed document, with work dependent on input shape. A pre-read byte limit, depth policy and supported field types matter more than assuming a tiny final dictionary means the original document was cheap.',
['Successful TOML parsing is not schema validation.','Do not print a full configuration when a field is rejected.'],['python/configuration-precedence','python/json-validation','python/log-redaction'],subject='python-examples')

lesson('configuration-precedence','Python configuration precedence: merge, validate, then publish',
'Configuration precedence chooses which source wins for each setting before the merged result becomes application state.',
'The fixture applies defaults, then file settings, then explicit overrides. All input mappings remain owned by their callers. Unknown keys fail before merging, and the final worker count is validated after precedence has selected it. Publishing one validated dictionary avoids services observing half-applied settings.',
'An override with a null or empty value is still an override unless the protocol defines otherwise. Reading process environment variables would require separate string parsing and a secret policy; this fixture deliberately receives owned mappings instead. Reloading an existing service also needs coordination around the published snapshot. [[python/toml-configuration|File schema]] and [[python/thread-locks|Protected state]] cover those boundaries.',
r'''def resolve_settings(defaults, file_settings, overrides):
    allowed = {"region", "workers"}
    for source in (defaults, file_settings, overrides):
        if set(source) - allowed:
            raise ValueError("unknown setting")
    merged = {**defaults, **file_settings, **overrides}
    if set(merged) != allowed or merged["region"] not in {"DEL", "BOM"}:
        raise ValueError("incomplete settings")
    if type(merged["workers"]) is not int or not 1 <= merged["workers"] <= 8:
        raise ValueError("invalid workers")
    return merged

defaults = {"region": "DEL", "workers": 2}
print(resolve_settings(defaults, {"workers": 3}, {"region": "BOM"}))
print(defaults)
try:
    resolve_settings(defaults, {}, {"workers": None})
except ValueError:
    print("null override rejected")''',"{'region': 'BOM', 'workers': 3}\n{'region': 'DEL', 'workers': 2}\nnull override rejected",
'Merging k total mapping entries takes expected O(k) reference work and retains an outer result. It does not deep-copy nested configuration. This schema permits only immutable scalar values, keeping publication ownership small.',
['Do not silently ignore an explicit invalid override.','Validate the final resolved state before replacing live settings.'],['python/toml-configuration','python/copy-deepcopy','python/thread-locks'],subject='python-examples')

lesson('log-redaction','Python logging: allowlist fields before they reach a handler',
'Log redaction reduces disclosed data by selecting permitted diagnostic fields before formatting a message.',
'The audit formatter keeps an exact event label and receipt ID while dropping an input token. It rejects line breaks and unexpected identifier shapes. This is an allowlist for one event, not a general secret detector. The original record remains unchanged so diagnostic formatting cannot mutate application state.',
'Filtering a structured object cannot undo a secret already embedded in a free-text message, exception or another handler. Avoid handing the raw payload to logging in the first place. This fixture does not establish a retention, access-control or privacy policy. [[python/logging-context|Context fields]] and [[python/json-validation|Wire contracts]] should be reviewed alongside it.',
r'''import json
import re

def audit_line(record):
    event = record.get("event")
    receipt_id = record.get("receipt_id")
    if event not in {"accepted", "rejected"}:
        raise ValueError("unsupported audit event")
    if not isinstance(receipt_id, str) or re.fullmatch(r"R-[0-9]{4}", receipt_id) is None:
        raise ValueError("invalid audit identifier")
    return json.dumps({"event": event, "receipt_id": receipt_id}, sort_keys=True)

record = {"event": "accepted", "receipt_id": "R-0041", "token": "fixture-only"}
print(audit_line(record))
print("token" in record)
try:
    audit_line({"event": "accepted", "receipt_id": "R-0041\n"})
except ValueError:
    print("line injection rejected")''','{"event": "accepted", "receipt_id": "R-0041"}\nTrue\nline injection rejected',
'The selected identifier has a fixed six-character budget and the serialized result has bounded size. This cost does not apply to arbitrary messages or stack traces. Handler I/O and durable storage are separate operations.',
['Do not log raw request objects before sanitizing them.','A field allowlist cannot inspect secrets hidden inside arbitrary text.'],['python/logging-context','python/regex-validation','python/json-validation'],subject='python-examples')

lesson('recursion-boundaries','Python recursion: bound depth instead of raising the limit',
'Recursion executes a function through nested calls, retaining one active call frame for each unfinished level.',
'The nested batch traversal accepts lists and exact integer leaves with an explicit depth ceiling. Reaching a deeper list fails rather than changing the interpreter recursion limit. The owned fixture is an acyclic tree. An input graph with aliases or cycles needs a separate identity policy and node budget before traversal.',
'This example rejects bool leaves. Its depth check makes recursion shallow, but does not bound a very wide list. A production decoder should impose both depth and item budgets, and a parser might already have exhausted memory before traversal begins. [[python/tree-traversal|Iterative traversal]] removes call-stack dependence without removing those input obligations.',
r'''def total_batch(batch, depth=0):
    if depth > 4:
        raise ValueError("batch nesting too deep")
    if type(batch) is int:
        return batch
    if type(batch) is not list:
        raise ValueError("integer leaves required")
    return sum(total_batch(child, depth + 1) for child in batch)

print(total_batch([125, [250, [75]]]))
try:
    total_batch([[[[[[1]]]]]])
except ValueError:
    print("depth budget rejected")''','450\ndepth budget rejected',
'For an accepted tree of n entries and depth d, traversal takes O(n) operations and O(d) live call/generator state, excluding growing integer digit costs. Increasing the recursion limit is not a substitute for an input contract.',
['Depth and total node count are different budgets.','A cyclic object graph is not an acyclic nested record tree.'],['python/tree-traversal','python/memoization','python/json-validation'])

group('python-types','Buffer and key contracts',['memoryview-buffers','hash-equality','enums'])
group('python-advanced','Layout, lifetime and resource acquisition',['slots','weak-references','exit-stack'])
group('python-examples','Configuration and disclosure boundaries',['toml-configuration','configuration-precedence','log-redaction'])
group('python','Bounded nested input',['recursion-boundaries'])
lesson('edit-distance','Python edit distance: rolling rows for insert, delete and replace',
'Levenshtein edit distance counts the fewest single-code-point insertions, deletions and replacements needed to transform one string into another.',
'The reconciliation helper returns a distance, not an edit script. It computes each cell from insertion, deletion and replacement costs while retaining only the previous row. The shorter label becomes the column dimension to reduce retained cells. Both labels are bounded to 64 code points before work begins.',
'This metric treats a combining accent as a separate code point and assigns every replacement the same cost. It is not a rule for merging customer identities or correcting an account number. Normalize only under an explicit domain policy; [[python/unicode-normalization|Unicode equivalence]] and [[python/longest-common-subsequence|Sequence alignment]] solve related but distinct problems.',
r'''def label_distance(stored, imported):
    if not isinstance(stored, str) or not isinstance(imported, str):
        raise ValueError("text labels required")
    if max(len(stored), len(imported)) > 64:
        raise ValueError("label budget exceeded")
    if len(imported) > len(stored):
        stored, imported = imported, stored
    previous = list(range(len(imported) + 1))
    for row, stored_char in enumerate(stored, 1):
        current = [row]
        for column, imported_char in enumerate(imported, 1):
            current.append(min(current[-1] + 1, previous[column] + 1,
                               previous[column - 1] + (stored_char != imported_char)))
        previous = current
    return previous[-1]

print(label_distance("dispatch", "despatch"))
print(label_distance("", "DEL"))
try:
    label_distance("x" * 65, "DEL")
except ValueError:
    print("label budget rejected")''','1\n3\nlabel budget rejected',
'For lengths m and n, time is O(mn) and working rows use O(min(m,n)) cells. Recovering the actual edit operations needs retained predecessor information or a different reconstruction method.',
['Code-point distance is not visual-character distance.','A small edit distance is not permission to merge records.'],['python/longest-common-subsequence','python/unicode-normalization','python/memoization'],subject='python-dsa')

lesson('sliding-window','Python sliding window: longest span without repeated symbols',
'A sliding window maintains a contiguous range while moving its left boundary only far enough to restore an invariant.',
'The scanner finds the length of the longest span with distinct ASCII symbols. Each symbol stores its most recent position. A repeat inside the current window moves the left boundary past that earlier position; a repeat outside it must not move the boundary backward. The program rejects non-ASCII input because this exercise defines symbols as protocol bytes represented in text.',
'This result is a length, not a returned substring. Tie handling would need a separate contract if start and end positions were returned. For Unicode user-visible text, code points do not necessarily correspond to grapheme clusters. [[python/strings-bytes|Wire alphabets]] and [[python/kmp-search|Pattern matching]] use other scanning invariants.',
r'''def distinct_span(sequence):
    if not isinstance(sequence, str) or not sequence.isascii() or len(sequence) > 256:
        raise ValueError("bounded ASCII sequence required")
    left = 0
    best = 0
    latest = {}
    for right, symbol in enumerate(sequence):
        left = max(left, latest.get(symbol, -1) + 1)
        latest[symbol] = right
        best = max(best, right - left + 1)
    return best

print(distinct_span("ABCADEAF"))
print(distinct_span(""))
try:
    distinct_span("DEL\u00e9")
except ValueError:
    print("wire alphabet rejected")''','5\n0\nwire alphabet rejected',
'For n symbols, expected time is O(n) with suitable dictionary behavior. Stored last positions use O(min(n,128)) entries for this ASCII contract. The max operation prevents a stale repeat from reopening an invalid earlier window.',
['Never move the left boundary backward after an old repeat.','A different symbol definition needs different preprocessing.'],['python/dictionaries','python/kmp-search','python/strings-bytes'],subject='python-dsa')

lesson('bellman-ford','Python Bellman-Ford: negative edges and reachable negative cycles',
'Bellman-Ford relaxes weighted directed edges repeatedly and can detect a negative-cost cycle reachable from a selected source.',
'The route function accepts bounded integer node IDs and signed integer costs. An unreachable node remains None. At most V minus one relaxation rounds establish finite shortest-path costs when no reachable negative cycle exists; one more improving edge proves that a finite answer cannot be supplied for the reachable cycle. A disconnected negative cycle does not invalidate this source’s reachable routes.',
'Dijkstra requires a different cost contract. Negative edges are accepted here, while malformed endpoints and boolean costs are rejected before relaxation. The caller receives a fresh cost list; the edge sequence is unchanged. This implementation reports a cycle error without returning a cycle witness or marking every affected destination. [[python/dijkstra|Nonnegative routes]] and [[python/graph-bfs|Unweighted traversal]] use cheaper algorithms under narrower assumptions.',
r'''def signed_routes(count, edges, source):
    if type(count) is not int or not 1 <= count <= 32:
        raise ValueError("node budget exceeded")
    if type(source) is not int or not 0 <= source < count or len(edges) > 512:
        raise ValueError("invalid source or edge budget")
    for start, end, weight in edges:
        if any(type(value) is not int for value in (start, end, weight)):
            raise ValueError("integer edges required")
        if not 0 <= start < count or not 0 <= end < count or abs(weight) > 1000000:
            raise ValueError("invalid edge")
    costs = [None] * count
    costs[source] = 0
    for _ in range(count - 1):
        changed = False
        for start, end, weight in edges:
            if costs[start] is not None:
                candidate = costs[start] + weight
                if costs[end] is None or candidate < costs[end]:
                    costs[end] = candidate
                    changed = True
        if not changed:
            break
    for start, end, weight in edges:
        if costs[start] is not None and (costs[end] is None or costs[start] + weight < costs[end]):
            raise ValueError("reachable negative cycle")
    return costs

print(signed_routes(4, [(0, 1, 5), (1, 2, -2), (0, 2, 8)], 0))
try:
    signed_routes(3, [(0, 1, 1), (1, 2, -2), (2, 1, 1)], 0)
except ValueError:
    print("reachable negative cycle rejected")''','[0, 5, 3, None]\nreachable negative cycle rejected',
'Worst-case relaxation time is O(VE), with O(V) cost storage beyond the supplied edges. Early stopping helps settled inputs but does not improve the worst-case bound. Integer digit costs grow with represented values.',
['Rejecting every negative edge would change this algorithm’s contract.','An unreachable negative cycle does not affect source-specific finite costs.'],['python/dijkstra','python/graph-bfs','python/topological-sort'],subject='python-dsa')

lesson('kruskal-forest','Python Kruskal: minimum spanning forests and disconnected graphs',
'Kruskal selects undirected edges by increasing weight and joins only components that are still separate.',
'The network function returns the forest weight and remaining component count. Negative weights are permitted. Self-loops cannot join components and parallel edges compete normally. A disconnected input produces a forest rather than pretending to connect every site. Edges are sorted into a fresh sequence and the caller’s input order remains untouched.',
'A minimum spanning forest does not answer directed shortest-path queries. The fixture validates integer endpoints and bounds nodes and edges before sorting. Tied weights may permit several equally cheap forests; this contract returns only weight and component count, avoiding an unnecessary promise about the selected edge identity. [[python/union-find|Component ownership]] and [[python/dijkstra|Route costs]] make that distinction concrete.',
r'''def network_forest(count, edges):
    if type(count) is not int or not 1 <= count <= 32 or len(edges) > 256:
        raise ValueError("network budget exceeded")
    for start, end, weight in edges:
        if any(type(value) is not int for value in (start, end, weight)):
            raise ValueError("integer edge required")
        if not 0 <= start < count or not 0 <= end < count or abs(weight) > 1000000:
            raise ValueError("invalid edge")
    parents = list(range(count))
    sizes = [1] * count
    def find(site):
        while parents[site] != site:
            parents[site] = parents[parents[site]]
            site = parents[site]
        return site
    total = 0
    components = count
    for start, end, weight in sorted(edges, key=lambda edge: edge[2]):
        first, second = find(start), find(end)
        if first == second:
            continue
        if sizes[first] < sizes[second]:
            first, second = second, first
        parents[second] = first
        sizes[first] += sizes[second]
        total += weight
        components -= 1
    return total, components

print(network_forest(4, [(0, 1, 4), (1, 2, 2), (0, 2, 3)]))
print(network_forest(2, [(0, 0, -5), (0, 1, -2)]))''','(5, 2)\n(-2, 1)',
'Sorting E edges costs O(E log E). Size-weighted union with path compression gives near-constant amortized component operations, conventionally O(alpha(V)). Arrays use O(V) storage and sorting retains O(E) edge references.',
['A disconnected result is a forest, not a spanning tree.','Self-loops must not reduce the component count.'],['python/union-find','python/dijkstra','python/sorting'],subject='python-dsa')

lesson('segment-tree','Python segment tree: point replacement and half-open range sums',
'A sum segment tree stores interval totals so a point replacement or range query need not rescan the entire sequence.',
'The ledger accepts exact integers and owns a separate tree array. Queries use half-open ranges: the left index is included and the right index is excluded. An empty range returns zero. Replacing a point updates its leaf and every ancestor total; it does not add a delta to an already changed value.',
'The fixture bounds the initial list and rejects boolean values or invalid ranges before mutation. It supports point replacement only. Interval addition needs lazy propagation or a different representation. Concurrent readers need coordination if replacement can occur during a query. [[python/python-lists|Outer ownership]] and [[python/thread-locks|Publication locks]] explain what the tree alone does not provide.',
r'''class LedgerSums:
    def __init__(self, amounts):
        if not 1 <= len(amounts) <= 128 or any(type(amount) is not int for amount in amounts):
            raise ValueError("bounded integer amounts required")
        self.count = len(amounts)
        self.tree = [0] * (2 * self.count)
        self.tree[self.count:] = amounts
        for index in range(self.count - 1, 0, -1):
            self.tree[index] = self.tree[2 * index] + self.tree[2 * index + 1]
    def replace(self, index, amount):
        if type(index) is not int or not 0 <= index < self.count or type(amount) is not int:
            raise ValueError("invalid replacement")
        position = index + self.count
        self.tree[position] = amount
        while position > 1:
            position //= 2
            self.tree[position] = self.tree[2 * position] + self.tree[2 * position + 1]
    def total(self, left, right):
        if any(type(index) is not int for index in (left, right)) or not 0 <= left <= right <= self.count:
            raise ValueError("invalid half-open interval")
        left += self.count
        right += self.count
        amount = 0
        while left < right:
            if left % 2:
                amount += self.tree[left]
                left += 1
            if right % 2:
                right -= 1
                amount += self.tree[right]
            left //= 2
            right //= 2
        return amount

ledger = LedgerSums([125, 250, 75, 50])
print(ledger.total(1, 4))
ledger.replace(2, 100)
print(ledger.total(0, 4))
print(ledger.total(2, 2))''','375\n525\n0',
'Building n leaves costs O(n) time and O(n) storage. A replacement and a range query each cost O(log n) tree operations, excluding arbitrary-size integer arithmetic. The private array is a teaching convention, not a tamper-proof access boundary.',
['Keep the right endpoint exclusive.','Point replacement is not range addition.'],['python/python-lists','python/binary-search','python/thread-locks'],subject='python-dsa')

lesson('bst-deletion','Python BST deletion: replace a two-child node with its successor',
'Binary search tree deletion removes a key while preserving the ordering of keys in every retained subtree.',
'The owned tree stores unique integer receipt numbers. A missing key leaves the tree logically unchanged. A node with zero or one child returns its surviving subtree; a node with two children takes the smallest key from its right subtree and deletes that successor there. The caller must assign the returned root because deleting the root can replace it.',
'This implementation accepts roots created by the bounded builder. It does not validate arbitrary cyclic node graphs. Tree nodes remain mutable and caller-owned; deletion changes them in place. No balancing occurs, so sorted insertion creates a chain. [[python/tree-traversal|Traversal]] and [[python/recursion-boundaries|Depth limits]] show why a small fixture cannot establish safe depth for an unbounded service.',
r'''from dataclasses import dataclass

@dataclass
class ReceiptNode:
    key: int
    left: "ReceiptNode | None" = None
    right: "ReceiptNode | None" = None

def receipt_tree(keys):
    if len(keys) > 64 or any(type(key) is not int for key in keys) or len(set(keys)) != len(keys):
        raise ValueError("bounded unique integer keys required")
    def insert(root, key):
        if root is None:
            return ReceiptNode(key)
        if key < root.key:
            root.left = insert(root.left, key)
        else:
            root.right = insert(root.right, key)
        return root
    root = None
    for key in keys:
        root = insert(root, key)
    return root

def delete_receipt(root, key):
    if type(key) is not int:
        raise ValueError("integer key required")
    if root is None:
        return None
    if key < root.key:
        root.left = delete_receipt(root.left, key)
    elif key > root.key:
        root.right = delete_receipt(root.right, key)
    elif root.left is None:
        return root.right
    elif root.right is None:
        return root.left
    else:
        successor = root.right
        while successor.left is not None:
            successor = successor.left
        root.key = successor.key
        root.right = delete_receipt(root.right, successor.key)
    return root

def ordered_receipts(root):
    return [] if root is None else ordered_receipts(root.left) + [root.key] + ordered_receipts(root.right)

root = receipt_tree([41, 20, 60, 50, 70])
root = delete_receipt(root, 41)
print(ordered_receipts(root))
root = delete_receipt(root, 999)
print(ordered_receipts(root))''','[20, 50, 60, 70]\n[20, 50, 60, 70]',
'Deletion costs O(h) traversal work and O(h) call-stack space for height h; h can equal n. The display helper concatenates lists and can cost O(n squared) on a chain. It is bounded here and is not the deletion algorithm’s storage cost.',
['Always retain the returned root after deletion.','Successor replacement must also remove the successor from its old subtree.'],['python/tree-traversal','python/recursion-boundaries','python/linked-list-reversal'],subject='python-dsa')

group('python-dsa','Range, tree and signed-graph invariants',['edit-distance','sliding-window','bellman-ford','kruskal-forest','segment-tree','bst-deletion'])
lesson('pandas-groupby','Pandas groupby: retain missing keys and define all-null totals',
'GroupBy partitions rows by keys and applies an aggregation to each partition; missing-key and missing-value policies are separate choices.',
'The receipt totals retain rows whose region is missing by setting dropna to false. Sum uses min_count equal to one, so a region containing only missing amounts keeps a missing total instead of becoming a misleading zero. Nullable integer storage preserves integer amounts alongside missing values. The fixture prints an explicit label for its missing region.',
'Count counts nonmissing values, while size counts rows. They answer different questions. A missing group label must not silently become an actual business region; this fixture has no real unassigned region identifier. Joins after aggregation still require their own cardinality checks. [[python/pandas-nullable|Nullable values]] and [[python/pandas-joins|Join contracts]] address those layers.',
r'''import pandas as pd

receipts = pd.DataFrame({"region": pd.Series(["DEL", "DEL", None, "BOM"], dtype="string"),
                         "amount": pd.Series([125, 250, 75, None], dtype="Int64")})
totals = receipts.groupby("region", dropna=False, sort=True)["amount"].sum(min_count=1)
for region, amount in totals.items():
    label = "missing-region" if pd.isna(region) else region
    value = None if pd.isna(amount) else int(amount)
    print(label, value)
print("rows retained:", int(receipts.groupby("region", dropna=False).size().sum()))''','BOM None\nDEL 375\nmissing-region 75\nrows retained: 4',
'Aggregation scans rows and retains group state. Work depends on keys, sorting and the selected aggregation; do not assume arbitrary group apply has the same cost as sum. A large distinct-key set can retain nearly one accumulator per row.',
['dropna for group keys is not min_count for aggregated values.','Count and size differ when amounts are missing.'],['python/pandas-nullable','python/pandas-joins','python/chunked-aggregation'],subject='python-data',dependencies=['pandas==3.0.6'])

lesson('pandas-rolling','Pandas rolling windows: minimum observations and causal boundaries',
'A rolling aggregation computes a result over a moving neighborhood of observations rather than over the whole series.',
'The receipt series uses a two-row trailing window. The first row lacks two observations, so min_periods equal to two leaves its total missing. Later totals include the current row and its predecessor. This is an observation-count window, not a duration window; irregular timestamps do not change its row membership.',
'Centered windows can include future observations and leak information into forecasting features. Time-based windows require a suitable ordered datetime index and a declared endpoint policy. Missing values also change the count of valid observations. [[python/datetime-boundaries|Time representation]] and [[python/ml-pipeline|Training boundaries]] make these choices visible rather than burying them in a feature calculation.',
r'''import pandas as pd

amounts = pd.Series([125, 250, 75, 50], dtype="Int64")
trailing = amounts.rolling(window=2, min_periods=2).sum()
print([None if pd.isna(value) else int(value) for value in trailing])
with_gap = pd.Series([125, None, 75], dtype="Int64")
print(with_gap.rolling(2, min_periods=2).count().tolist())''','[None, 375, 325, 125]\n[nan, 1.0, 1.0]',
'An aggregation such as this rolling sum can use specialized implementations. A custom function evaluated across k entries at n positions may instead cost O(nk). Output retains n results even when window state is small.',
['Two observations are not necessarily two days.','Centered or future-inclusive windows can invalidate forecasting evaluation.'],['python/datetime-boundaries','python/pandas-nullable','python/ml-pipeline'],subject='python-data',dependencies=['pandas==3.0.6'])

lesson('chunked-aggregation','Pandas chunked CSV aggregation: validate every chunk before returning totals',
'Chunked CSV reading yields batches so aggregation need not retain every parsed row at once.',
'The import accepts exactly region and amount columns, known region labels and nonnegative integer minor units. Each chunk is validated before its group totals enter a private accumulator. A failure in a later chunk raises without returning a partial result. The fixture bounds source text and row count as well as chunk size.',
'Chunking bounds a batch, not the entire input or number of groups. Real files require a pre-read byte policy and parser limits; this fixture already owns a small string. It does not write results externally, so no transaction is needed to hide partial internal accumulation. [[python/bounded-csv|CSV reception]] and [[python/sqlite-cli-project|Transactional publication]] cover those different stages.',
r'''from io import StringIO
import pandas as pd

def region_totals(text):
    if not isinstance(text, str) or len(text) > 1024:
        raise ValueError("CSV budget exceeded")
    totals = {}
    rows = 0
    with pd.read_csv(StringIO(text), chunksize=2,
                     dtype={"region": "string", "amount": "Int64"}) as chunks:
        for chunk in chunks:
            rows += len(chunk)
            if list(chunk.columns) != ["region", "amount"] or rows > 100:
                raise ValueError("CSV shape rejected")
            if chunk.isna().any().any() or not chunk["region"].isin(["DEL", "BOM"]).all():
                raise ValueError("CSV fields rejected")
            if (chunk["amount"] < 0).any() or (chunk["amount"] > 1000000).any():
                raise ValueError("amount range rejected")
            for region, amount in chunk.groupby("region")["amount"].sum().items():
                totals[region] = totals.get(region, 0) + int(amount)
    return totals

print(region_totals("region,amount\nDEL,125\nBOM,75\nDEL,250\n"))
try:
    region_totals("region,amount\nDEL,125\nBOM,75\nDEL,-1\n")
except ValueError:
    print("later chunk rejected; no result returned")''',"{'BOM': 75, 'DEL': 375}\nlater chunk rejected; no result returned",
'For n accepted rows, aggregation performs row-dependent work and retains one chunk plus group accumulators. With c chunk rows and g group keys, parsed working storage is approximately O(c+g), excluding the owned source string and parser buffers. Integer overflow policy matters for large vectorized sums; per-row and row-count bounds keep this fixture below that limit.',
['A chunk size is not a file-size limit.','Do not expose partial totals before the complete import succeeds.'],['python/bounded-csv','python/pandas-groupby','python/sqlite-cli-project'],subject='python-data',dependencies=['pandas==3.0.6'])

lesson('numpy-precision','NumPy floating-point checks: finite values and declared tolerances',
'Floating-point arithmetic represents many real values approximately, so equality and tolerance checks express different contracts.',
'The sensor fixture rejects nonfinite values before computing a comparison. Its tolerance check sets both relative and absolute tolerances explicitly. A near-zero measurement needs an absolute scale, while a larger reference can use a relative budget. The fixture does not reuse these tolerances for money or every measurement unit.',
'NumPy isclose uses its second operand as the reference scale and is not generally symmetric. Default tolerances can accept differences that are too large for tiny values. NaN and infinity need a separate acceptance policy, not an accidental comparison result. [[python/decimal-money|Exact decimal amounts]] and [[python/numpy-broadcasting|Array shape checks]] solve other representation constraints.',
r'''import numpy as np

measurements = np.array([0.1 + 0.2, 0.0], dtype=np.float64)
references = np.array([0.3, 1e-12], dtype=np.float64)
if not np.isfinite(measurements).all() or not np.isfinite(references).all():
    raise ValueError("finite measurements required")
print((measurements == references).tolist())
print(np.isclose(measurements, references, rtol=1e-10, atol=1e-11).tolist())
print(bool(np.isfinite(np.array([1.0, np.nan])).all()))''','[False, False]\n[True, True]\nFalse',
'Elementwise checks scan n values and allocate boolean results unless an API-specific output strategy avoids them. Array broadcasting can enlarge intermediate shapes. Tolerances describe an application error budget; they do not improve the underlying stored precision.',
['Choose tolerances in the measurement’s units.','Reject or handle nonfinite data before claiming a numerical result is usable.'],['python/numpy-broadcasting','python/decimal-money','python/pandas-nullable'],subject='python-data',dependencies=['numpy==2.5.3'])

lesson('matplotlib-figures','Matplotlib figures: render a labeled report without a display server',
'Matplotlib draws data through a figure and axes, while its selected backend determines how the result is rendered.',
'The dispatch report uses the Agg backend before importing pyplot, then saves a labeled bar chart to an owned byte buffer. It closes the figure after saving. The PNG signature check confirms the returned container format; it does not evaluate whether the chart communicates its data honestly. Minor-unit labels prevent the displayed numbers from being mistaken for rupee amounts.',
'This example uses fixture totals, no remote images and no browser screenshot. Rendering a chart does not repair incorrect aggregation. Repeated unclosed figures can retain memory even after an output buffer is discarded. [[python/pandas-groupby|Group totals]] and [[python/exit-stack|Resource release]] provide the preceding and following boundaries.',
r'''from io import BytesIO
import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt

figure, axes = plt.subplots(figsize=(6, 3.5), constrained_layout=True)
try:
    axes.bar(["DEL", "BOM", "BLR"], [375, 250, 175], color="#286c83", width=0.6)
    axes.set(title="Accepted receipts by region", ylabel="Amount (minor units)")
    axes.set_ylim(bottom=0)
    axes.spines[["top", "right"]].set_visible(False)
    with BytesIO() as output:
        figure.savefig(output, format="png", dpi=120)
        image = output.getvalue()
    print("PNG container:", image.startswith(b"\x89PNG\r\n\x1a\n"))
finally:
    plt.close(figure)
print("open figures:", len(plt.get_fignums()))''','PNG container: True\nopen figures: 0',
'Rendering work depends on artists, pixel dimensions and backend. Raster output retains pixel-related storage; increasing each dimension multiplies the pixel count. This fixture does not print compressed byte size because rendering details can change across package versions.',
['Select a noninteractive backend before importing pyplot.','A saved image does not automatically release its figure.'],['python/pandas-groupby','python/chunked-aggregation','python/exit-stack'],subject='python-data',dependencies=['matplotlib==3.11.2'])

lesson('ml-pipeline','Scikit-learn pipelines: fit preprocessing on training data only',
'A scikit-learn Pipeline chains preprocessing and an estimator so fitting and prediction apply the same ordered transformations.',
'The fixture has an explicit training partition and an independent evaluation partition. StandardScaler learns its mean from training rows during fit. Prediction transforms the evaluation rows with that fitted state without refitting the scaler. The program inspects the fitted mean before and after prediction to test that boundary rather than advertising an accuracy score on a tiny synthetic dataset.',
'A pipeline cannot correct a split that already leaked related records, future observations or duplicate customers across partitions. Hyperparameter selection also needs a separate validation or cross-validation policy. This classifier has no calibrated business guarantee, fairness evaluation or deployment interface. [[python/pandas-rolling|Causal features]] and [[python/classification-metrics|Error counts]] cover two common evaluation failures.',
r'''import numpy as np
from sklearn.pipeline import Pipeline
from sklearn.preprocessing import StandardScaler
from sklearn.linear_model import LogisticRegression

training = np.array([[1, 10], [2, 20], [3, 30], [4, 40]], dtype=float)
labels = np.array([0, 0, 1, 1])
evaluation = np.array([[2.5, 25], [100, 1000]], dtype=float)
model = Pipeline([("scale", StandardScaler()),
                  ("classify", LogisticRegression(random_state=41, max_iter=200))])
model.fit(training, labels)
owned_mean = model.named_steps["scale"].mean_.copy()
print("training mean:", owned_mean.tolist())
predictions = model.predict(evaluation)
print("prediction count:", len(predictions))
print("mean unchanged:", bool(np.array_equal(owned_mean, model.named_steps["scale"].mean_)))''','training mean: [2.5, 25.0]\nprediction count: 2\nmean unchanged: True',
'Scaling n rows and p dense features costs O(np) work and retains p fitted statistics. Logistic regression training cost depends on solver, iterations, features and data. There is no general constant-time fit claim, and this fixture does not benchmark it.',
['Never fit preprocessing on held-out evaluation rows.','A pipeline does not choose an appropriate time, group or identity split for you.'],['python/pandas-rolling','python/classification-metrics','python/numpy-precision'],subject='python-data',dependencies=['numpy==2.5.3','scikit-learn==1.9.1'])

lesson('classification-metrics','Python classification metrics: fix label order before counting errors',
'A confusion matrix counts actual and predicted labels, exposing different failure types that a single accuracy number can hide.',
'The review fixture declares label order as zero then one. Rows represent actual labels and columns represent predictions. A false positive marks a clean receipt for review; a false negative misses a receipt that required review. Precision and recall use different denominators, so they describe different costs even when their numeric values happen to match.',
'This sample has five fixture records and no claim about real review quality. Empty positive classes require a declared zero-division policy. Threshold selection, class imbalance, grouped records and uncertainty need a larger evaluation design. [[python/ml-pipeline|Held-out preprocessing]] and [[python/pandas-groupby|Partition counts]] help prevent a tidy metric from hiding a broken data boundary.',
r'''from sklearn.metrics import confusion_matrix, precision_score, recall_score

actual = [0, 0, 0, 1, 1]
predicted = [0, 1, 0, 0, 1]
print(confusion_matrix(actual, predicted, labels=[0, 1]).tolist())
print("precision:", precision_score(actual, predicted, zero_division=0))
print("recall:", recall_score(actual, predicted, zero_division=0))
print("empty-positive precision:", precision_score([0, 0], [0, 0], zero_division=0))''','[[2, 1], [1, 1]]\nprecision: 0.5\nrecall: 0.5\nempty-positive precision: 0.0',
'Counting n labels takes row-dependent work; a k-class confusion matrix retains O(k squared) cells. Accuracy can look high under a skewed class distribution while the rare failure class remains poorly detected.',
['Declare matrix label order before interpreting its positions.','Do not treat a zero-division fallback as evidence of adequate positive-class performance.'],['python/ml-pipeline','python/pandas-groupby','python/numpy-precision'],subject='python-data',dependencies=['scikit-learn==1.9.1'])

lesson('pytest-fixtures','Pytest fixtures: isolated files and parameterized rejection tests',
'A pytest fixture supplies test-owned setup and cleanup so cases can exercise an operation without sharing accidental state.',
'The fixture creates a tiny test module in an owned temporary directory and runs pytest in a child interpreter. The tmp_path fixture gives the accepted-input test its own file. Parameterized rejection cases cover a negative quantity, a boolean and text. The subprocess checks the exit code rather than depending on pytest’s version-specific progress text.',
'This lesson disables automatic third-party plugin loading in the child environment and names its test file explicitly. A passing fixture does not prove every caller or deployment path is safe. Test isolation must extend to databases, clocks and network collaborators when those enter the operation. [[python/mock-failures|Failure injection]] and [[python/unittest-contracts|Standard-library tests]] illustrate alternative test boundaries.',
r'''from pathlib import Path
import os
import subprocess
import sys
import tempfile

TEST_SOURCE = """import pytest

def accepted_quantity(value):
    if type(value) is not int or not 0 <= value <= 8:
        raise ValueError('quantity rejected')
    return value

def test_owned_file(tmp_path):
    manifest = tmp_path / 'quantity.txt'
    manifest.write_text('3', encoding='utf-8')
    assert accepted_quantity(int(manifest.read_text(encoding='utf-8'))) == 3

@pytest.mark.parametrize('quantity', [-1, True, '3'])
def test_rejected_quantity(quantity):
    with pytest.raises(ValueError):
        accepted_quantity(quantity)
"""
with tempfile.TemporaryDirectory() as directory:
    target = Path(directory) / "test_quantity.py"
    target.write_text(TEST_SOURCE, encoding="utf-8")
    environment = dict(os.environ, PYTEST_DISABLE_PLUGIN_AUTOLOAD="1")
    result = subprocess.run([sys.executable, "-I", "-m", "pytest", "-q", str(target)],
                            cwd=directory, env=environment, capture_output=True, text=True, timeout=10)
    if result.returncode:
        raise RuntimeError("owned pytest cases failed")
print("four owned pytest cases passed")''','four owned pytest cases passed',
'The four cases perform bounded local work. Interpreter startup and test collection dominate this small run; no speed comparison with unittest is claimed. Real integration suites must budget their external resources separately.',
['Do not let tests share mutable files without explicit ownership.','Assert the operation’s contract rather than copying its implementation into the expected result.'],['python/unittest-contracts','python/mock-failures','python/input-exercise'],subject='python-testing',dependencies=['pytest==9.1.1'])

lesson('mypy-checks','Mypy static checks: annotations do not validate runtime payloads',
'Mypy checks supported type relationships in annotated Python code without executing the application as a runtime validator.',
'The positive module declares a function returning an integer amount. A separate module returns text under the same return annotation. Strict checking accepts the first and reports the incompatible return in the second. Each file is checked independently through the same interpreter and target syntax version, with caches disabled to keep this small fixture isolated.',
'A type check can miss untyped or deliberately escaped paths, and an annotation does not reject untrusted JSON. The fixture also checks the expected diagnostic category rather than counting an arbitrary nonzero exit as success; tool startup failures would otherwise masquerade as a useful rejection. [[python/type-hints|Annotations]] and [[python/json-validation|Runtime validation]] serve different boundaries.',
r'''from pathlib import Path
import subprocess
import sys
import tempfile

with tempfile.TemporaryDirectory() as directory:
    owned = Path(directory)
    accepted = owned / "accepted.py"
    rejected = owned / "rejected.py"
    accepted.write_text("def receipt_amount() -> int:\n    return 125\n", encoding="utf-8")
    rejected.write_text("def receipt_amount() -> int:\n    return '125'\n", encoding="utf-8")
    command = [sys.executable, "-I", "-m", "mypy", "--strict", "--python-version", "3.11",
               "--no-incremental", "--cache-dir", str(owned / "cache")]
    good = subprocess.run(command + [str(accepted)], cwd=directory, capture_output=True, text=True, timeout=10)
    bad = subprocess.run(command + [str(rejected)], cwd=directory, capture_output=True, text=True, timeout=10)
    if good.returncode != 0 or bad.returncode != 1 or "[return-value]" not in bad.stdout:
        raise RuntimeError("unexpected type-check result")
print("valid return accepted")
print("text return rejected by static check")''','valid return accepted\ntext return rejected by static check',
'Static analysis cost depends on program size, imports and type relationships. This fixture uses two tiny independent files and does not claim a whole-service check. The 3.11 checker target is not execution on Python 3.11.',
['A type annotation cannot sanitize a received payload.','A failed checker process is not automatically the expected type diagnostic.'],['python/type-hints','python/typing-protocol','python/json-validation'],subject='python-testing',dependencies=['mypy==2.3.1'])

lesson('mock-failures','Python unittest.mock: inject a collaborator failure before publication',
'A mock replaces a collaborator in a test so the caller’s response to a selected result or failure can be observed.',
'The importer stages one receipt, asks a writer to publish it, and updates its accepted list only after that writer succeeds. A spec-limited mock raises an OSError. The test checks that the list remains empty and the writer received exactly the staged record. This tests an application boundary rather than every internal line.',
'The injected writer models one synchronous call that either returns or raises before a successful publication is reported. It does not simulate a remote write that commits and then loses its acknowledgment. That case needs idempotency and reconciliation. [[python/idempotent-jobs|Replay-safe identity]] and [[python/atomic-report-project|File staging]] address the ambiguity.',
r'''from unittest.mock import Mock

class ReceiptWriter:
    def publish(self, receipt):
        raise NotImplementedError

def import_receipt(receipt, writer, accepted):
    staged = dict(receipt)
    writer.publish(staged)
    accepted.append(staged["receipt_id"])

writer = Mock(spec_set=ReceiptWriter)
writer.publish.side_effect = OSError("fixture writer unavailable")
accepted = []
try:
    import_receipt({"receipt_id": "R-0041", "amount": 125}, writer, accepted)
except OSError:
    print("writer failure propagated")
writer.publish.assert_called_once_with({"receipt_id": "R-0041", "amount": 125})
print("accepted:", accepted)''','writer failure propagated\naccepted: []',
'The fixture makes one bounded collaborator call and an outer record copy. Mocks do not measure real I/O latency or establish compatibility with the actual writer. Separate integration tests need to exercise that implementation.',
['Mock the boundary the caller actually uses.','A timeout after remote commit is not the same as this pre-publication failure.'],['python/pytest-fixtures','python/idempotent-jobs','python/atomic-report-project'],subject='python-testing')

group('python-data','Aggregation, rendering and evaluation',['pandas-groupby','pandas-rolling','chunked-aggregation','numpy-precision','matplotlib-figures','ml-pipeline','classification-metrics'])
group('python-testing','Owned tests and static checking',['pytest-fixtures','mypy-checks','mock-failures'])
DJANGO_DB = r'''from django.conf import settings
settings.configure(INSTALLED_APPS=[], DATABASES={"default": {"ENGINE": "django.db.backends.sqlite3", "NAME": ":memory:"}},
                   DEFAULT_AUTO_FIELD="django.db.models.AutoField", USE_TZ=True)
import django
django.setup()
from django.db import connection, models, IntegrityError, transaction

class DispatchPartner(models.Model):
    region = models.CharField(max_length=3, unique=True)
    class Meta:
        app_label = "receipt_fixture"

class StoredReceipt(models.Model):
    receipt_id = models.CharField(max_length=6, unique=True)
    partner = models.ForeignKey(DispatchPartner, on_delete=models.PROTECT)
    amount = models.IntegerField()
    class Meta:
        app_label = "receipt_fixture"
        constraints = [models.CheckConstraint(condition=models.Q(amount__gte=0), name="receipt_amount_nonnegative")]

with connection.schema_editor() as schema:
    schema.create_model(DispatchPartner)
    schema.create_model(StoredReceipt)
'''
lesson('django-models','Django models: database constraints survive an unchecked save',
'A Django model maps fields and relationships to stored records, while database constraints enforce selected invariants at the storage boundary.',
'The receipt model has a unique receipt identifier, a partner foreign key and a nonnegative amount constraint. The fixture explicitly creates its schema in an in-memory SQLite database. A negative amount reaches the database through create and is rejected there. The transaction block contains the rejected write so later queries run outside the failed transaction.',
'Model save does not automatically call full_clean. Database constraints do not replace field parsing, authorization or an application’s full domain rules. This standalone fixture uses app labels and schema_editor for a small owned schema; it is not a substitute for an installed application and migration history. [[python/django-migrations|Real migrations]] and [[python/django-forms|Input fields]] cover those separate layers.',
DJANGO_DB+r'''
partner = DispatchPartner.objects.create(region="DEL")
StoredReceipt.objects.create(receipt_id="R-0041", partner=partner, amount=125)
try:
    with transaction.atomic():
        StoredReceipt.objects.create(receipt_id="R-0042", partner=partner, amount=-1)
except IntegrityError:
    print("database constraint rejected negative amount")
print("stored receipts:", StoredReceipt.objects.count())
connection.close()''','database constraint rejected negative amount\nstored receipts: 1',
'Each stored field and index adds database work and storage. Constraint checks and query plans depend on the backend. A passing SQLite fixture does not establish PostgreSQL locking, isolation or migration behavior.',
['Do not assume save invokes full_clean.','Catch an integrity error outside the atomic block that must roll back.'],['python/django-forms','python/django-migrations','python/django-atomic'],subject='python-web',dependencies=['Django==5.2.17'])

lesson('django-query-counts','Django select_related: measure the foreign-key N plus one query pattern',
'Select_related joins supported single-valued relationships into a queryset so reading those related objects need not issue a query per row.',
'Three stored receipts share one partner. Reading each receipt’s partner from a plain queryset issues the receipt query and three related-object queries. A fresh queryset using select_related retrieves the required fields in one joined query. Both paths return the same region labels, so the fixture checks query count without changing the answer.',
'QuerySets are lazy and can cache evaluated results. Measure a fresh queryset for each comparison; reusing an already evaluated one can hide database work. Select_related is not the tool for every many-valued relation, and a wide join may transfer unused columns. [[python/django-models|Relationship storage]] and [[python/django-pagination|Bounded retrieval]] should shape the query before optimizing it.',
DJANGO_DB+r'''
from django.test.utils import CaptureQueriesContext
partner = DispatchPartner.objects.create(region="DEL")
for number in (41, 42, 43):
    StoredReceipt.objects.create(receipt_id=f"R-{number:04d}", partner=partner, amount=125)
with CaptureQueriesContext(connection) as plain_queries:
    plain = [receipt.partner.region for receipt in StoredReceipt.objects.order_by("id")]
with CaptureQueriesContext(connection) as joined_queries:
    joined = [receipt.partner.region for receipt in StoredReceipt.objects.select_related("partner").order_by("id")]
print("same regions:", plain == joined)
print("plain queries:", len(plain_queries))
print("joined queries:", len(joined_queries))
connection.close()''','same regions: True\nplain queries: 4\njoined queries: 1',
'The plain path performs 1+n query round trips here. The joined path performs one query but still transfers n result rows and the selected related fields. Query count alone does not measure latency, index use or total transferred bytes.',
['Measure fresh querysets rather than cached results.','Use prefetching or a different query for many-valued relationships.'],['python/django-models','python/django-pagination','python/pandas-joins'],subject='python-web',dependencies=['Django==5.2.17'])

lesson('django-atomic','Django atomic transactions: rollback the batch and defer callbacks',
'An atomic block groups database operations so an escaping failure rolls its attempted changes back at that transaction boundary.',
'The import first stores a valid receipt and then encounters a duplicate identifier inside the same block. Both attempted inserts are rolled back. An on_commit callback registered inside that failed block is discarded. A later successful block commits one receipt and runs its callback after success. The callback list is only a local observation of timing.',
'Database rollback does not rewind already mutated Python objects or sent network messages. On_commit is also not a durable job queue: a process can fail after database commit before an external action finishes. An outbox or idempotent consumer needs a different design. [[python/idempotent-jobs|Replay identity]] and [[python/sqlite-transactions|Transaction ownership]] address part of that boundary.',
DJANGO_DB+r'''
partner = DispatchPartner.objects.create(region="DEL")
callbacks = []
try:
    with transaction.atomic():
        StoredReceipt.objects.create(receipt_id="R-0041", partner=partner, amount=125)
        transaction.on_commit(lambda: callbacks.append("discarded"))
        StoredReceipt.objects.create(receipt_id="R-0041", partner=partner, amount=250)
except IntegrityError:
    print("failed batch rows:", StoredReceipt.objects.count())
with transaction.atomic():
    StoredReceipt.objects.create(receipt_id="R-0042", partner=partner, amount=75)
    transaction.on_commit(lambda: callbacks.append("committed"))
print("stored rows:", StoredReceipt.objects.count())
print("callbacks:", callbacks)
connection.close()''',"failed batch rows: 0\nstored rows: 1\ncallbacks: ['committed']",
'Transaction work depends on statements, indexes and backend locking. Holding a transaction open during unrelated I/O lengthens its lock and connection lifetime. The local SQLite run does not test multi-process contention or crash recovery.',
['Rollback does not reverse an already sent message.','An on_commit callback is not a durable delivery guarantee.'],['python/django-models','python/sqlite-transactions','python/idempotent-jobs'],subject='python-web',dependencies=['Django==5.2.17'])

lesson('django-migrations','Django migrations: generate and apply an owned application schema',
'A Django migration records a schema transition for an installed application so that a database can apply a versioned sequence of changes.',
'The fixture writes its own tiny installed app into a temporary directory, generates its initial migration and applies it to an in-memory SQLite database. It then creates a record through the model and checks the applied migration entry. Unlike the separate schema_editor fixtures, this program exercises Django’s migration loader and recorded history.',
'Generating a migration compares model state with migration state; it does not inspect every production database as a source of truth. A successful initial migration says nothing about a large-table alteration, concurrent traffic or data backfill. Review generated operations and plan releases before changing a live schema. [[python/django-models|Constraints]] and [[python/package-layout|Installed package layout]] provide the prerequisites.',
r'''from pathlib import Path
from io import StringIO
import importlib
import sys
import tempfile

with tempfile.TemporaryDirectory() as directory:
    package = Path(directory) / "receipt_store"
    package.mkdir()
    (package / "__init__.py").write_text("", encoding="utf-8")
    (package / "models.py").write_text(
        'from django.db import models\n'
        'class Receipt(models.Model):\n'
        '    receipt_id = models.CharField(max_length=6, unique=True)\n', encoding="utf-8")
    sys.path.insert(0, directory)
    from django.conf import settings
    settings.configure(INSTALLED_APPS=["receipt_store"],
                       DATABASES={"default": {"ENGINE": "django.db.backends.sqlite3", "NAME": ":memory:"}},
                       DEFAULT_AUTO_FIELD="django.db.models.AutoField")
    import django
    django.setup()
    from django.core.management import call_command
    from django.db import connection
    from django.db.migrations.loader import MigrationLoader
    with StringIO() as command_output:
        call_command("makemigrations", "receipt_store", verbosity=0, stdout=command_output)
        call_command("migrate", verbosity=0, stdout=command_output)
    Receipt = importlib.import_module("receipt_store.models").Receipt
    Receipt.objects.create(receipt_id="R-0041")
    print("initial migration written:", (package / "migrations" / "0001_initial.py").exists())
    print("initial migration applied:", ("receipt_store", "0001_initial") in MigrationLoader(connection).applied_migrations)
    print("stored records:", Receipt.objects.count())
    connection.close()
    sys.path.remove(directory)''','initial migration written: True\ninitial migration applied: True\nstored records: 1',
'Schema changes can lock tables, rewrite data or rebuild indexes depending on backend and operation. This tiny initial SQLite schema has none of the scale or deployment costs of a production alteration; no zero-downtime claim follows from it.',
['Commit reviewed migration files with the model change.','Do not treat an initial schema test as evidence that a later data migration is safe.'],['python/django-models','python/package-layout','python/django-atomic'],subject='python-web',dependencies=['Django==5.2.17'])

lesson('django-template-escaping','Django templates: escape untrusted text at HTML output',
'Django template autoescaping converts supported HTML-sensitive characters in rendered values so ordinary text is not interpreted as markup.',
'The review heading receives a deliberately hostile-looking label. A standalone template Engine renders it with autoescaping enabled, and the program verifies that a literal script opening tag did not enter the output. The original label remains unchanged; escaping belongs to the output context rather than an irreversible rewrite of stored text.',
'HTML text escaping is not a universal encoder for JavaScript, CSS, URL schemes or arbitrary attribute contexts. Marking a value safe can bypass the protection. This fixture uses a text node and no user-defined template source. [[python/django-forms|Input acceptance]] and [[python/django-csrf|Request origin protection]] solve different security boundaries.',
r'''from django.template import Context, Engine

label = '<script>alert("receipt")</script>'
template = Engine(debug=False).from_string("<h2>{{ label }}</h2>")
rendered = template.render(Context({"label": label}, autoescape=True))
print("literal script tag:", "<script>" in rendered)
print("escaped tag:", "&lt;script&gt;" in rendered)
print("original preserved:", label.startswith("<script>"))''','literal script tag: False\nescaped tag: True\noriginal preserved: True',
'Rendering scans the selected values and creates output text. A size limit on accepted labels bounds that work in an application; this fixed fixture alone does not impose such a policy on every view.',
['Do not mark received text safe to fix unwanted escaping.','HTML text escaping does not validate a URL or encode a JavaScript expression.'],['python/django-forms','python/django-csrf','python/strings-bytes'],subject='python-web',dependencies=['Django==5.2.17'])

lesson('django-csrf','Django CSRF checks: require the token without confusing it with identity',
'CSRF middleware checks unsafe requests against a token and origin policy to reduce unauthorized cross-site actions in a browser session.',
'The local review view obtains a CSRF cookie on GET. A test client with CSRF enforcement enabled receives a forbidden result for a POST without the matching token and accepts a POST carrying it. The fixture checks both paths; the default test client’s relaxed behavior would not establish this protection.',
'The token does not prove user identity, record ownership or safe input. Real HTTPS deployment also needs the appropriate origin, cookie, proxy and session configuration. The fixture uses a local test-only secret and testserver host, makes no network listener and stores no user session. [[python/django-forms|Field validation]] and [[python/flask-json-api|Body validation]] remain necessary after an origin check succeeds.',
r'''from django.conf import settings
settings.configure(SECRET_KEY="owned-local-csrf-fixture", ROOT_URLCONF=__name__,
                   ALLOWED_HOSTS=["testserver"],
                   MIDDLEWARE=["django.middleware.csrf.CsrfViewMiddleware"], INSTALLED_APPS=[])
import django
django.setup()
from django.http import HttpResponse
from django.middleware.csrf import get_token
from django.urls import path
from django.test import Client

def review(request):
    get_token(request)
    return HttpResponse("local review received")

urlpatterns = [path("review/", review)]
client = Client(enforce_csrf_checks=True)
client.get("/review/")
token = client.cookies["csrftoken"].value
print("without token:", client.post("/review/", {}).status_code)
print("with token:", client.post("/review/", {}, HTTP_X_CSRFTOKEN=token).status_code)''','without token: 403\nwith token: 200',
'This test exercises in-process middleware dispatch. It does not measure network latency or verify a production reverse proxy. Token checks are only one part of a request’s total parsing, database and authorization cost.',
['Enable CSRF enforcement in the test that claims to check it.','A valid token is not permission to change a receipt.'],['python/django-forms','python/django-template-escaping','python/flask-json-api'],subject='python-web',dependencies=['Django==5.2.17'])

lesson('django-pagination','Django keyset pagination: stable ordering and a bounded next page',
'Keyset pagination selects rows after an ordered cursor instead of repeatedly skipping an offset of earlier rows.',
'The receipt cursor is a positive primary-key position under ascending ID order. Each query fetches at most the page size plus one row; the extra row indicates whether a next page existed at query time. Returned pages own their ID lists. Boolean cursors and excessive page sizes fail before querying.',
'An ID cursor is not a snapshot across requests. Concurrent inserts or deletes can change later results, and a user-visible API needs authorization plus an opaque or validated cursor contract. Ordering by a nonunique timestamp would require a tie-breaker. [[python/django-query-counts|Query work]] and [[python/django-atomic|Transaction scope]] help distinguish bounded retrieval from consistency guarantees.',
DJANGO_DB+r'''
def receipt_page(after_id=0, size=2):
    if type(after_id) is not int or after_id < 0 or type(size) is not int or not 1 <= size <= 20:
        raise ValueError("invalid page request")
    selected = list(StoredReceipt.objects.filter(id__gt=after_id).order_by("id").values_list("id", flat=True)[:size + 1])
    page = selected[:size]
    cursor = page[-1] if len(selected) > size else None
    return page, cursor

partner = DispatchPartner.objects.create(region="DEL")
for number in (41, 42, 43):
    StoredReceipt.objects.create(receipt_id=f"R-{number:04d}", partner=partner, amount=125)
first, cursor = receipt_page()
print(first, cursor)
print(receipt_page(cursor))
try:
    receipt_page(True)
except ValueError:
    print("boolean cursor rejected")
connection.close()''','[1, 2] 2\n([3], None)\nboolean cursor rejected',
'The fixture fetches at most size plus one values. With a suitable ordered index, keyset retrieval avoids offset scanning; actual database work still depends on plans, filters and backend. It provides no stable total-count claim.',
['Always define deterministic ordering and a tie-breaker when needed.','A cursor across separate requests is not a transaction snapshot.'],['python/django-query-counts','python/django-atomic','python/binary-search'],subject='python-web',dependencies=['Django==5.2.17'])

lesson('idempotent-jobs','Python SQLite job project: reject conflicting replays by request identity',
'An idempotent request key associates one operation identity with one accepted payload so a matching replay can reuse its stored result.',
'The local job ledger accepts a bounded job ID and an exact nonnegative integer amount. It stores the accepted payload and result together under a unique key. The first call creates the row; a matching replay returns the same result without another row. Reusing the key for a different amount raises a conflict instead of silently returning an unrelated result.',
'This fixture calculates a local result inside one SQLite transaction and uses one connection sequentially. It does not dispatch an external payment, resolve ambiguous remote timeouts or coordinate competing connections. Those cases need backend-specific contention handling and a durable delivery design. [[python/django-atomic|Commit callbacks]] and [[python/mock-failures|Injected failures]] explain why replay identity alone cannot promise exactly-once external effects.',
r'''import re
import sqlite3

def open_job_ledger():
    database = sqlite3.connect(":memory:")
    database.execute("CREATE TABLE jobs (job_id TEXT PRIMARY KEY, amount INTEGER NOT NULL, result INTEGER NOT NULL)")
    return database

def accept_job(database, job_id, amount):
    if not isinstance(job_id, str) or re.fullmatch(r"J-[0-9]{4}", job_id) is None:
        raise ValueError("job identity rejected")
    if type(amount) is not int or not 0 <= amount <= 1000000:
        raise ValueError("amount rejected")
    with database:
        existing = database.execute("SELECT amount, result FROM jobs WHERE job_id = ?", (job_id,)).fetchone()
        if existing is not None:
            if existing[0] != amount:
                raise ValueError("request identity conflict")
            return existing[1], False
        result = amount + 25
        database.execute("INSERT INTO jobs VALUES (?, ?, ?)", (job_id, amount, result))
        return result, True

if __name__ == "__main__":
    database = open_job_ledger()
    try:
        print(accept_job(database, "J-0041", 125))
        print(accept_job(database, "J-0041", 125))
        try:
            accept_job(database, "J-0041", 250)
        except ValueError:
            print("conflicting replay rejected")
        print("stored jobs:", database.execute("SELECT count(*) FROM jobs").fetchone()[0])
    finally:
        database.close()''','(150, True)\n(150, False)\nconflicting replay rejected\nstored jobs: 1',
'The primary-key index supports keyed retrieval with database-dependent logarithmic work. The fixture retains one row per accepted key and has no expiry policy. Deleting an identity too early can permit a later replay to be treated as a new operation.',
['A matching key with a different payload must be rejected.','A local transaction does not make an external side effect exactly once.'],['python/django-atomic','python/sqlite-cli-project','python/mock-failures'],subject='python-projects')

group('python-web','Stored state and request boundaries',['django-models','django-query-counts','django-atomic','django-migrations','django-template-escaping','django-csrf','django-pagination'])
group('python-projects','Replay identity and stored outcomes',['idempotent-jobs'])
DEPTH_BANKS={
'python-storage-contracts':('Python storage and request contracts quiz',['python/django-models','python/django-query-counts','python/django-atomic','python/django-migrations','python/django-csrf','python/django-pagination','python/idempotent-jobs'],[
('Does Model.save automatically run full_clean?',['Always','No','Only for every foreign key'],1,'Database storage and model validation are separate; the constraint fixture rejects a negative amount at the database boundary.'),
('Where should the handled integrity failure be caught in this atomic fixture?',['Outside its atomic block','Between two statements inside the broken block','Only inside the template'],0,'Let the block exit and roll back before continuing database work.'),
('What happens to an on_commit callback registered inside a rolled-back block?',['It runs twice','It becomes a durable job','It is discarded'],2,'The callback belongs to the successful-commit path and is discarded with the failed transaction boundary.'),
('Does rollback undo a previously sent HTTP message?',['No','Always','Only with SQLite'],0,'A database rollback cannot rewind an external effect already sent.'),
('What does select_related optimize in this receipt fixture?',['Every many-to-many collection','Access to its single-valued partner relation','Input authentication'],1,'A joined foreign-key fetch replaces this particular per-row related lookup; it does not cover every relation.'),
('Why use fresh querysets in a query-count comparison?',['To randomize order','To disable all indexes','To avoid an evaluated queryset cache hiding queries'],2,'An already materialized queryset can reuse results and distort the comparison.'),
('What does the migration fixture actually verify?',['An owned initial app migration is generated and applied','A production data backfill cannot lock','Every later migration is safe'],0,'The test applies a tiny initial SQLite schema and checks recorded history; deployment alterations remain untested.'),
('Is HTML text autoescaping sufficient to validate a received URL scheme?',['Yes','No','Only when the label is short'],1,'Encoding in an HTML text node and accepting a safe URL are different contracts.'),
('Why enable enforce_csrf_checks in the client?',['To prove the caller owns a receipt','To increase database capacity','To exercise token rejection in the local test'],2,'The test intentionally turns on CSRF enforcement; a valid token still supplies no authorization.'),
('Does an ID cursor create a snapshot across separate requests?',['No','Always','Only for pages of two rows'],0,'Later mutations can change later pages unless a separate consistency mechanism is supplied.'),
('What should happen when a job key is replayed with a different amount?',['Return any cached result','Reject an identity conflict','Delete every job'],1,'A stored request identity is bound to its accepted payload; a different payload cannot reuse that result.'),
('Does one sequential SQLite replay fixture establish exactly-once remote payments?',['Yes','Only for integers','No'],2,'Remote effects and competing connections need further coordination, recovery and backend-specific tests.')]),
'python-data-evaluation':('Python aggregation and evaluation quiz',['python/pandas-groupby','python/pandas-rolling','python/chunked-aggregation','python/numpy-precision','python/matplotlib-figures','python/ml-pipeline','python/classification-metrics'],[
('Which GroupBy choice retains missing group keys?',['dropna=False','min_count=0','center=True'],0,'dropna controls missing keys; the aggregation’s min_count controls valid values.'),
('Why use min_count=1 for an all-null amount group?',['To force a fabricated zero','To preserve a missing total','To drop every row'],1,'No valid amount should remain missing rather than quietly appearing as a measured zero.'),
('How does size differ from count for a nullable amount column?',['They always match','Size excludes missing values','Size counts rows; count excludes missing amounts'],2,'The row count and valid-value count describe different quantities.'),
('Does a two-row rolling window necessarily mean two days?',['No','Yes','Only on integer amounts'],0,'An observation-count window follows rows, not elapsed time.'),
('What risk can a centered rolling feature introduce for forecasting?',['A new primary key','Future information in a feature','Guaranteed lower memory'],1,'A centered neighborhood can use later observations that were unavailable at prediction time.'),
('What does CSV chunksize fail to bound by itself?',['Each yielded batch','Every parser option','Total file size and distinct groups'],2,'Chunking does not cap source bytes or the number of retained group accumulators.'),
('Which rows should fit the scaler before evaluating a model?',['Training rows only','All rows including evaluation','Only evaluation rows'],0,'Evaluation must use fitted training statistics; fitting on held-out data leaks information.'),
('Does a pipeline fix a split that puts the same customer on both sides?',['Yes','No','Only with two features'],1,'Partition design is a separate data contract; a pipeline cannot repair an already leaky split.'),
('How are this confusion matrix’s positions defined?',['Rows predicted, columns actual','Arbitrary by record order','Rows actual, columns predicted under declared labels'],2,'Label order is explicit and positions must be interpreted under the actual/predicted axis convention.'),
('Is zero_division=0 evidence that a model detects the positive class well?',['No','Always','Only on five rows'],0,'The fallback makes a denominator boundary explicit; it is not a performance claim.'),
('Why set floating tolerances explicitly?',['To turn every float into money','To express the application’s unit-dependent error budget','To remove all rounding'],1,'Relative and absolute tolerances define accepted differences; stored precision remains approximate.'),
('What still needs release after saving a Matplotlib figure?',['The label alphabet','The CSV header','The figure’s retained resources'],2,'Saving bytes does not automatically close pyplot’s figure bookkeeping.')]),
'python-range-graph-tests':('Python range algorithms and test boundaries quiz',['python/edit-distance','python/sliding-window','python/bellman-ford','python/kruskal-forest','python/segment-tree','python/bst-deletion','python/pytest-fixtures','python/mypy-checks','python/mock-failures'],[
('What does rolling-row edit distance omit?',['A reconstructed edit script','The numeric distance','Insertion costs'],0,'The retained rows compute the distance; returning the edit operations requires additional reconstruction work.'),
('Why must the distinct-span left boundary never move backward?',['To sort symbols','An old repeat outside the window must not reopen invalid state','To count every duplicate twice'],1,'Taking the maximum with the current boundary preserves the window invariant.'),
('Which negative cycle invalidates source-specific Bellman-Ford costs here?',['Every disconnected cycle','Only a positive cycle','A reachable negative cycle'],2,'A reachable improving cycle prevents finite shortest costs; a disconnected cycle does not affect this source.'),
('What does Kruskal return when the graph is disconnected?',['A minimum spanning forest','A directed route tree','A fabricated connecting edge'],0,'Each connected component gets its own tree; the component count remains greater than one.'),
('What is the segment tree query’s endpoint convention?',['Both inclusive','Left inclusive, right exclusive','Both always excluded'],1,'The half-open contract permits an empty interval with zero sum.'),
('Does this point-replacement tree implement lazy interval addition?',['Yes','Only for negative values','No'],2,'Range addition needs separate state and propagation; it is outside this fixture.'),
('Why assign the return from BST deletion back to root?',['Deleting root can replace it with a surviving subtree','It sorts every amount','It creates a balanced tree'],0,'The operation may return a different root; ignoring it loses the updated tree entrypoint.'),
('Can a sorted insertion order make this unbalanced BST height linear?',['No','Yes','Only for strings'],1,'Without balancing, a chain has height equal to its node count.'),
('What does tmp_path supply to a test?',['Production storage durability','A hosted database','An owned temporary filesystem location'],2,'The fixture isolates local file state without claiming deployment persistence.'),
('Does a successful mypy check validate received JSON at runtime?',['No','Always','Only with strict enabled'],0,'Annotations and static relationships are different from checking an actual payload.'),
('Why inspect the expected mypy diagnostic as well as its exit code?',['To copy source text','A startup failure must not masquerade as a useful type rejection','To install packages globally'],1,'A nonzero exit can indicate a tool failure rather than the intended return-value error.'),
('What does the injected writer error fail to simulate?',['A local exception','An unchanged accepted list','Remote commit followed by lost acknowledgment'],2,'The mock’s synchronous failure does not establish recovery from an ambiguous external write.')])}
for slug,(title,refs,questions) in DEPTH_BANKS.items():
 BANKS[slug]=(title,questions)
 path='quizzes/'+slug
 entry=copy.deepcopy(lookup['quizzes/python-basics'])
 entry.update(id=str(uuid.uuid5(uuid.NAMESPACE_URL,'https://aitrove.in/'+path)),path=path,title=title,summary='Twelve explained questions on '+title.lower().replace(' quiz','')+'.',tags=['python','quiz'],sort_order=200+len(added),published_at=stamp,updated_at=stamp)
 entry['body']=para('A Python self-check tests a selected operation contract through twelve questions with explanations.')+'<h2>Review the related lessons</h2><ul>'+''.join('<li><a href="/'+p+'">'+html.escape(lookup[p]['title'])+'</a></li>' for p in refs)+'</ul><h3>Common Mistakes</h3>'+para('A correct local answer is not a deployment guarantee. Read the input, ownership and failure clauses before adapting the program. Results stay in this browser.')
 entry['data']['questions']=[{'prompt':prompt,'options':options,'answer':answer,'explanation':explanation} for prompt,options,answer,explanation in questions]
 entry['data']['related']=[{'path':p,'title':lookup[p]['title']} for p in refs]
 upsert(entry);added.append(path)

DEPTH_REVERSE={
'python/strings-bytes':['memoryview-buffers','django-template-escaping'],
'python/dataclasses':['hash-equality','slots'],
'python/dictionaries':['hash-equality','sliding-window'],
'python/pattern-matching':['enums'],
'python/context-managers':['exit-stack'],
'python/json-validation':['toml-configuration','mypy-checks'],
'python/logging-context':['log-redaction'],
'python/tree-traversal':['bst-deletion','recursion-boundaries'],
'python/longest-common-subsequence':['edit-distance'],
'python/dijkstra':['bellman-ford'],
'python/union-find':['kruskal-forest'],
'python/python-lists':['segment-tree','memoryview-buffers'],
'python/pandas-nullable':['pandas-groupby','pandas-rolling'],
'python/pandas-joins':['django-query-counts','chunked-aggregation'],
'python/numpy-broadcasting':['numpy-precision','ml-pipeline'],
'python/unittest-contracts':['pytest-fixtures','mock-failures'],
'python/type-hints':['mypy-checks'],
'python/django-forms':['django-models','django-csrf'],
'python/django-routing':['django-template-escaping','django-pagination'],
'python/sqlite-transactions':['django-atomic','idempotent-jobs'],
'python/package-layout':['django-migrations'],
'python/bounded-csv':['chunked-aggregation'],
'python/atomic-report-project':['mock-failures'],
'python/inventory-project':['idempotent-jobs'],
}
for original,slugs in DEPTH_REVERSE.items():
 assert original in lookup, original
 targets=[slug if slug.startswith('python/') else 'python/'+slug for slug in slugs]
 entry=lookup[original]
 marker='<h2>Related Python operation checks</h2>'
 entry['body']=entry['body'].split(marker)[0]+marker+para(', '.join('[['+p+'|'+lookup[p]['title']+']]' for p in targets)+'.')
 known={item['path'] for item in entry['data'].get('related',[])}
 entry['data'].setdefault('related',[]).extend({'path':p,'title':lookup[p]['title']} for p in targets if p not in known)
