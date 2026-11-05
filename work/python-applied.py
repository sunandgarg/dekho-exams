"""Fifth Python pass: contracts for state changes, application paths and distribution."""
lesson('keywords-identifiers','Python keywords and identifiers: parser rules differ from field rules',
'Python keywords occupy grammatical roles, while identifiers bind names that must satisfy the parser’s naming rules.',
'The fixture compiles an owned assignment using a reserved keyword and checks that it fails before execution. A soft keyword remains usable as a name outside its special grammar position. The receipt identifier validator imposes an ASCII application grammar instead of assuming every valid Python identifier is a valid received field. No received text is executed.',
'Isidentifier does not check whether a name is reserved, and the set of soft keywords depends on the interpreter release. Unicode identifiers are valid in source but may be inappropriate for a protocol that needs a fixed alphabet. Compilation can raise SyntaxError before any statement runs. [[python/unicode-normalization|Unicode equivalence]] and [[python/type-conversion|Field grammar]] concern different boundaries.',
r'''import keyword
import re

print("reserved:", keyword.iskeyword("class"))
print("valid spelling:", "class".isidentifier())
namespace = {}
exec(compile("match = 125", "owned-source", "exec"), namespace)
print("soft keyword value:", namespace["match"])
try:
    compile("class = 125", "owned-source", "exec")
except SyntaxError:
    print("reserved assignment rejected")
print("wire accepted:", re.fullmatch(r"[A-Z][A-Z0-9_]{0,15}", "RECEIPT_41") is not None)''','reserved: True\nvalid spelling: True\nsoft keyword value: 125\nreserved assignment rejected\nwire accepted: True',
'Identifier scanning depends on source length. This fixture compiles fixed owned strings and validates a bounded field. Compiling received program text would introduce an execution boundary that this lesson does not provide.',
['A valid identifier can still be reserved.','Do not execute received text to validate a field.'],['python/setup-interpreter','python/type-conversion','python/unicode-normalization'])

lesson('first-class-functions','Python first-class functions: dispatch through an explicit operation registry',
'A function is an object that can be stored, passed and returned without immediately calling it.',
'The receipt dispatcher maps two accepted operation names to functions and invokes only the selected handler. It validates the operation and exact nonnegative integer amount before calling the registry entry. A named registry keeps accepted behavior visible; it does not need eval, a received import path or a chain of guessed method names. A returned closure retains its declared fee.',
'Passing a function differs from passing its result. A registry also retains its callable objects, including any state captured by closures. Callbacks can perform side effects, so selecting an accepted name alone is not a transaction. [[python/closures|Captured state]], [[python/lambda-functions|Binding timing]] and [[python/plugin-project|Owned plugin loading]] cover adjacent contracts.',
r'''def charged_amount(amount):
    return amount + 25

def refunded_amount(amount):
    return amount

HANDLERS = {"charge": charged_amount, "refund": refunded_amount}
def dispatch(operation, amount):
    if not isinstance(operation, str) or operation not in HANDLERS:
        raise ValueError("operation rejected")
    if type(amount) is not int or not 0 <= amount <= 1000000:
        raise ValueError("amount rejected")
    return HANDLERS[operation](amount)

def with_fee(fee):
    def charge(amount):
        return amount + fee
    return charge

print(dispatch("charge", 125))
print(dispatch("refund", 125))
print(with_fee(40)(125))
try:
    dispatch("__import__", 125)
except ValueError:
    print("unknown operation rejected")''','150\n125\n165\nunknown operation rejected',
'Expected registry lookup work is constant for suitable string hashes; handler cost is separate. The fixed registry retains two functions. Each returned closure retains its fee until the closure is released.',
['Pass a callback object when the caller must choose its execution time.','A received operation name must not become executable source or an unrestricted import.'],['python/python-functions','python/closures','python/plugin-project'])

lesson('refactor-contract-tests','Python refactoring: preserve rejected inputs as well as accepted results',
'Refactoring changes an implementation while preserving the behavior promised by its existing input and failure contract.',
'The original shipping charge chooses a bounded surcharge with branches. The replacement uses a lookup indexed only after the same type and range checks. A small unittest suite compares accepted inputs and confirms that both versions reject booleans, negatives and quantities outside the budget. Rewriting one arithmetic expression is not enough when callers depend on rejection behavior.',
'The tests compare two implementations, so a shared misconception can survive both. Independent expected cases establish the boundary amounts; equivalence checks supplement those cases rather than replace them. Exception messages are not part of this stated contract. [[python/unittest-contracts|Independent assertions]] and [[python/mutation-testing|Deliberate defects]] help assess what a suite actually protects.',
r'''import io
import unittest

def old_charge(quantity):
    if type(quantity) is not int or not 0 <= quantity <= 2:
        raise ValueError("quantity rejected")
    if quantity == 0: return 0
    if quantity == 1: return 25
    return 40

def new_charge(quantity):
    if type(quantity) is not int or not 0 <= quantity <= 2:
        raise ValueError("quantity rejected")
    return (0, 25, 40)[quantity]

class ChargeContract(unittest.TestCase):
    def test_accepted(self):
        for quantity, expected in ((0, 0), (1, 25), (2, 40)):
            self.assertEqual(old_charge(quantity), expected)
            self.assertEqual(new_charge(quantity), expected)
    def test_rejected(self):
        for operation in (old_charge, new_charge):
            for quantity in (True, -1, 3, "1"):
                with self.assertRaises(ValueError): operation(quantity)

result = unittest.TextTestRunner(stream=io.StringIO()).run(unittest.defaultTestLoader.loadTestsFromTestCase(ChargeContract))
print("contract suites:", result.testsRun)
print("preserved:", result.wasSuccessful())''','contract suites: 2\npreserved: True',
'The implementations perform bounded work for this three-value domain. Exhaustive accepted-domain checks are cheap here; a large state space requires targeted cases and independent properties rather than assuming pairwise equality proves correctness.',
['Preserve the rejected-input domain when changing representation.','Two equal implementations can share the same bug.'],['python/unittest-contracts','python/hypothesis-properties','python/mutation-testing'])

lesson('import-failures','Python import failures: module removal does not roll back every side effect',
'Import executes module initialization, and a failed initialization can leave external side effects even when its module entry is removed.',
'The program writes an owned temporary module that creates a marker and then raises. A child interpreter imports it through an explicit temporary path, catches the failure and checks sys.modules. The failed module entry is gone, but the marker remains. A retry would execute initialization again rather than resume the failed statement.',
'Other modules imported during initialization can remain cached too. Import is not an application transaction. Keep irreversible startup work outside module top-level code, and register an accepted plugin only after its loader returns successfully. The executed source is written by this fixture; [[python/plugin-project|The owned loader]] is not a sandbox for received code. [[python/atomic-report-project|Staged file publication]] supplies another boundary.',
r'''from pathlib import Path
import subprocess
import sys
import tempfile

with tempfile.TemporaryDirectory() as directory:
    owned = Path(directory)
    (owned / "aitrove_failed_import.py").write_text('from pathlib import Path\nPath(__file__).with_suffix(".marker").write_text("started")\nraise RuntimeError("initialization failed")\n', encoding="utf-8")
    source = ''' + "r'''" + '''import sys
from pathlib import Path
sys.path.insert(0, sys.argv[1])
try:
    import aitrove_failed_import
except RuntimeError:
    print("failed module retained:", "aitrove_failed_import" in sys.modules)
print("side effect retained:", (Path(sys.argv[1]) / "aitrove_failed_import.marker").exists())''' + "'''" + '''
    result = subprocess.run([sys.executable, "-I", "-c", source, str(owned)], capture_output=True, text=True, check=True, timeout=5)
    print(result.stdout.strip())''','failed module retained: False\nside effect retained: True',
'Initialization cost includes whatever the module executes, not just source lookup. This child has a fixed source and deadline. A timeout is not a general process-tree, memory or disk quota for arbitrary code.',
['Failed imports can leave files or other initialized modules behind.','Top-level initialization is not an atomic publication mechanism.'],['python/modules','python/plugin-project','python/subprocess-boundaries'])

group('python','Source names, callable dispatch and preserved startup contracts',['keywords-identifiers','first-class-functions','refactor-contract-tests','import-failures'])

lesson('typed-arrays','Python array: fixed-width numeric storage is not a portable wire encoding',
'Array stores homogeneous numeric elements using a declared machine representation rather than a list of arbitrary object references.',
'The quantity buffer uses an unsigned-byte array so accepted values fit a known one-byte range. A memoryview edits the shared buffer, demonstrating that zero-copy access retains an alias. Appending an out-of-range value raises without extending the array. Releasing the view permits later buffer resizing; resizing while the view is exported is rejected.',
'Other array type codes can have platform-dependent item sizes and native byte order. The tobytes method does not establish a portable network format without an explicit representation contract. Unsigned bytes still need domain validation if zero or 255 is invalid business input. [[python/memoryview-buffers|Shared buffers]] and [[python/strings-bytes|Encoded text]] are separate concerns.',
r'''from array import array

quantities = array("B", [3, 5, 8])
view = memoryview(quantities)
view[1] = 7
print("shared values:", quantities.tolist())
try:
    quantities.append(256)
except OverflowError:
    print("out of range rejected")
try:
    quantities.append(9)
except BufferError:
    print("resize while exported rejected")
view.release()
quantities.append(9)
print("released values:", quantities.tolist())''','shared values: [3, 7, 8]\nout of range rejected\nresize while exported rejected\nreleased values: [3, 7, 8, 9]',
'The byte array retains one byte per element plus container overhead. Appending has allocation-dependent cost; converting to a list allocates object references and does not preserve the compact representation. No measured cross-platform memory ratio is claimed.',
['An exported view shares updates and can prevent resizing.','Native numeric storage is not automatically an interoperable byte format.'],['python/memoryview-buffers','python/numpy-views','python/json-validation'],subject='python-types')

lesson('ordered-dictionaries','Python OrderedDict: explicit reordering differs from insertion order',
'OrderedDict is a mapping with operations for moving existing keys and removing entries from either end of its retained order.',
'The cache-order fixture moves a receipt to the most-recent end after a read, then removes the oldest retained entry. Replacing a value in an ordinary dictionary does not express that access-order policy. OrderedDict equality against another OrderedDict is order-sensitive, while equality against an ordinary mapping compares key/value content.',
'Ordered mapping is not a sorted mapping. It also supplies no automatic synchronization, expiry or durable cache state. An empty oldest-entry removal raises KeyError. [[python/lru-project|A bounded LRU contract]] must define capacity, misses and updates in addition to choosing a container. [[python/hash-equality|Hash stability]] still governs keys.',
r'''from collections import OrderedDict

recent = OrderedDict([("R-0041", 125), ("R-0042", 250)])
recent.move_to_end("R-0041")
print("access order:", list(recent))
print("evicted:", recent.popitem(last=False))
first = OrderedDict([("DEL", 1), ("BOM", 2)])
second = OrderedDict([("BOM", 2), ("DEL", 1)])
print("ordered equality:", first == second)
print("mapping equality:", first == dict(second))''',"access order: ['R-0042', 'R-0041']\nevicted: ('R-0042', 250)\nordered equality: False\nmapping equality: True",
'Expected key lookup and endpoint reordering avoid scanning all entries under suitable hashes. OrderedDict retains extra ordering state compared with a plain dictionary. It does not order entries by key magnitude or timestamp unless the application updates that order.',
['Insertion order is not an access-order cache policy.','Order-sensitive equality differs when both operands are OrderedDict.'],['python/lru-project','python/dictionaries','python/hash-equality'],subject='python-types')

lesson('itertools-pipelines','Python itertools: adjacent groups and shared iterator consumption',
'Itertools composes iterator operations whose work and retained state depend on when consumers request values.',
'The receipt stream has two separated runs for one region. Groupby emits three adjacent groups; it does not combine every equal key across the stream. Chain joins two batches without constructing one combined list, and islice consumes only the selected prefix. Zip with strict=True rejects unequal lengths rather than silently discarding unmatched records.',
'A group iterator shares the source with the outer group iterator, so consume or materialize a group before advancing to the next one. Sorting first can produce global key groups but changes order and adds storage/work. Tee can retain a growing backlog when consumers move at different speeds. [[python/generators|Deferred work]] and [[python/pandas-groupby|Whole-dataset grouping]] use different ownership models.',
r'''from itertools import chain, groupby, islice

receipts = [("DEL", 125), ("BOM", 75), ("DEL", 250)]
runs = [(region, sum(amount for _, amount in group)) for region, group in groupby(receipts, key=lambda row: row[0])]
print("adjacent groups:", runs)
print("bounded prefix:", list(islice(chain([125, 250], [75, 40]), 3)))
try:
    list(zip(["R-0041", "R-0042"], [125], strict=True))
except ValueError:
    print("unequal batches rejected")''',"adjacent groups: [('DEL', 125), ('BOM', 75), ('DEL', 250)]\nbounded prefix: [125, 250, 75]\nunequal batches rejected",
'The consumed prefix costs O(k) iteration work. Materialized group totals retain output per run, while groupby itself need not retain all input. A bounded islice caps consumption only when each upstream next call itself terminates.',
['Groupby groups adjacent equal keys, not all equal keys everywhere.','Strict zip can reject after earlier pairs have already been consumed.'],['python/generators','python/map-filter-reduce','python/pandas-groupby'],subject='python-types')

group('python-types','Numeric buffers, explicit order and iterator composition',['typed-arrays','ordered-dictionaries','itertools-pipelines'])

lesson('subclass-hooks','Python __init_subclass__: validate declarations without a custom metaclass',
'Init_subclass is a class hook invoked when a subclass is created, allowing a base to validate subclass declarations.',
'The parser base consumes one class keyword and forwards remaining keywords through super. An accepted subclass gets an explicit wire name. A declaration with no valid name raises during class creation. This avoids a custom metaclass for a simple invariant while leaving a normal constructor and method lookup.',
'The hook executes during class construction and is not a transaction across every cooperating base. Registering globally inside it can publish too early if a later hook fails. This fixture validates and assigns only the new class; it has no external registry. Multiple bases must agree on forwarding keywords. [[python/mro-super|Cooperative ordering]] and [[python/metaclass-registry|Explicit registry publication]] expose those tradeoffs.',
r'''class ReceiptParser:
    def __init_subclass__(cls, *, wire_name=None, **options):
        super().__init_subclass__(**options)
        if not isinstance(wire_name, str) or not wire_name or len(wire_name) > 32:
            raise ValueError("wire name required")
        cls.wire_name = wire_name

class MinorParser(ReceiptParser, wire_name="receipt-minor"):
    pass

print(MinorParser.wire_name)
try:
    class UnnamedParser(ReceiptParser):
        pass
except ValueError:
    print("unnamed declaration rejected")''','receipt-minor\nunnamed declaration rejected',
'The hook validates a bounded string once per class declaration. Classes remain ordinary objects; this check supplies neither runtime payload validation nor a code-execution sandbox.',
['Forward keywords through cooperative hooks rather than dropping them.','A successful declaration does not validate future request payloads.'],['python/mro-super','python/metaclass-registry','python/abstract-classes'],subject='python-advanced')

lesson('async-generator-cleanup','Python async generators: close a suspended producer when leaving early',
'An asynchronous generator suspends between yielded values and can retain resources until it is explicitly closed or completes.',
'The review producer records a cleanup marker in finally. The consumer exits after its first accepted receipt and wraps the producer with aclosing. Leaving that scope awaits aclose and executes the producer’s cleanup before the consumer returns. The fixture observes the marker directly rather than relying on garbage collection timing.',
'Breaking an async-for loop does not establish prompt resource release for every retained generator reference. The generator may also fail during cleanup; that failure needs an explicit application policy. Aclosing supplies deterministic closure, not cancellation shielding or a network deadline. [[python/async-deadlines|Deadline scope]] and [[python/concurrency-interview|Cancellation cleanup]] cover those boundaries.',
r'''import asyncio
from contextlib import aclosing

async def review_stream(released):
    try:
        yield "R-0041"
        yield "R-0042"
    finally:
        released.append("producer closed")

async def first_review():
    released = []
    async with aclosing(review_stream(released)) as stream:
        async for receipt_id in stream:
            print(receipt_id)
            break
    print(released)

asyncio.run(first_review())''',"R-0041\n['producer closed']",
'Only one value is consumed in this fixture. Producer work, buffered state and awaited cleanup cost depend on the actual generator. Deterministic closure removes reliance on garbage collection but does not place a bound on arbitrary cleanup work.',
['Early loop exit is not a resource-release policy by itself.','Await closure before claiming the producer has released its resources.'],['python/generators','python/async-deadlines','python/concurrency-interview'],subject='python-advanced')

lesson('typing-narrowing','Python TypeGuard: a static narrowing claim is not lasting ownership',
'TypeGuard lets a predicate describe a narrower type to a static checker when that predicate returns true.',
'The predicate checks that a bounded list contains exact nonnegative integers. A successful check proves the current contents only. Another alias can append a string afterward, invalidating the runtime assumption. Copying the accepted values into an immutable tuple gives the subsequent calculation owned membership instead of relying on a mutable shared list.',
'TypeGuard does not perform validation by itself and a checker generally trusts the predicate’s annotation. The runtime implementation must establish the declared condition. A copied tuple can still alias nested mutable objects; this fixture permits only immutable integers. [[python/typing-protocol|Structural claims]], [[python/mypy-checks|Checker diagnostics]] and [[python/copy-deepcopy|Ownership]] are separate concerns.',
r'''from typing import TypeGuard

def accepted_amounts(value: object) -> TypeGuard[list[int]]:
    return isinstance(value, list) and len(value) <= 64 and all(type(amount) is int and 0 <= amount <= 1000000 for amount in value)

received = [125, 250]
print("accepted:", accepted_amounts(received))
owned = tuple(received) if accepted_amounts(received) else ()
alias = received
alias.append("rejected")
print("shared still accepted:", accepted_amounts(received))
print("owned total:", sum(owned))
print("boolean accepted:", accepted_amounts([True]))''','accepted: True\nshared still accepted: False\nowned total: 375\nboolean accepted: False',
'Validation and tuple construction cost O(n) work and retained references for n values. The maximum batch is 64. An annotation cannot stop another owner from changing the original list after a check.',
['A narrowing predicate’s annotation is a promise its implementation must satisfy.','A mutable alias can invalidate a previously checked condition.'],['python/type-hints','python/typing-protocol','python/copy-deepcopy'],subject='python-advanced')

group('python-advanced','Declaration hooks, producer lifetime and narrowing ownership',['subclass-hooks','async-generator-cleanup','typing-narrowing'])

# Reuse AI Trove's own insertion helpers; the displayed deletion program remains standalone.
AVL_SOURCE=html.unescape(re.search(r'<pre><code class="language-python">([\s\S]*?)</code></pre>',lookup['python/avl-insertion']['body'])[1]).split('index = ReceiptIndex()')[0]
lesson('avl-deletion','Python AVL deletion: rebalance after removing a key and replacing its successor',
'AVL deletion removes a binary-search-tree key and restores subtree height balance along the changed path.',
'The receipt index retains unique exact-integer keys. A two-child removal replaces the node key with the smallest key in its right subtree, then removes that successor from the subtree. Each returning frame refreshes height and selects rotations using child balances. Unlike insertion, deletion can reduce a subtree height and require repairs at several ancestors. Missing keys leave the index unchanged.',
'The program extends the insertion fixture but includes all helpers so it runs alone. Deleting from the exposed internal node structure would bypass the wrapper’s key-set invariant. This is an owned in-memory tree, not a concurrent index or a database replacement. [[python/avl-insertion|Insertion rotations]], [[python/bst-deletion|Unbalanced deletion]] and [[python/tree-traversal|Ordered walks]] supply related contracts.',
AVL_SOURCE+r'''def delete_key(node, key):
    if node is None:
        return None
    if key < node.key:
        node.left = delete_key(node.left, key)
    elif key > node.key:
        node.right = delete_key(node.right, key)
    else:
        if node.left is None: return node.right
        if node.right is None: return node.left
        successor = node.right
        while successor.left is not None: successor = successor.left
        node.key = successor.key
        node.right = delete_key(node.right, successor.key)
    refresh(node)
    balance = height(node.left) - height(node.right)
    if balance > 1:
        if height(node.left.left) < height(node.left.right):
            node.left = rotate_left(node.left)
        return rotate_right(node)
    if balance < -1:
        if height(node.right.right) < height(node.right.left):
            node.right = rotate_right(node.right)
        return rotate_left(node)
    return node

class RemovableIndex(ReceiptIndex):
    def remove(self, key):
        if type(key) is not int:
            raise ValueError("exact integer key required")
        if key not in self.keys:
            return False
        self.root = delete_key(self.root, key)
        self.keys.remove(key)
        return True

index = RemovableIndex()
for key in (10, 20, 30, 40, 50, 25): index.add(key)
print(index.remove(30), sorted(index.keys))
print(index.remove(30), sorted(index.keys))
for key in tuple(index.keys): index.remove(key)
print("empty root:", index.root is None)''',"True [10, 20, 25, 40, 50]\nFalse [10, 20, 25, 40, 50]\nempty root: True",
'With maintained AVL invariants, deletion uses O(log n) traversal/stack space and O(log n) possible ancestor repairs. The key set adds O(n) retained storage; integer comparison costs depend on digit length. The wrapper caps accepted unique keys at 128.',
['Choose deletion rotations from child heights, not from the deleted key’s old direction.','Retain the root returned by every repair.'],['python/avl-insertion','python/bst-deletion','python/tree-traversal'],subject='python-dsa')

lesson('strongly-connected-components','Python strongly connected components: partition a directed dependency graph',
'A strongly connected component contains vertices that can each reach every other vertex through directed paths.',
'The bounded graph fixture computes finishing order on the original adjacency and then explores reversed edges in reverse finishing order. Each second-pass traversal owns one component. Isolated vertices are included. Sorting component members and the final component list gives a stable teaching result without changing the graph-theoretic partition.',
'A directed path in only one direction does not make two vertices strongly connected. Cycles can be represented as one component before building a component-level acyclic dependency graph. Duplicate edges and self-loops are accepted here; invalid endpoints are rejected before traversal. [[python/topological-sort|Dependency ordering]] and [[python/graph-bfs|Reachability]] concern related but different outputs.',
r'''def dependency_components(count, edges):
    if type(count) is not int or not 0 <= count <= 32 or len(edges) > 256:
        raise ValueError("graph budget rejected")
    forward, backward = [[] for _ in range(count)], [[] for _ in range(count)]
    for edge in edges:
        if not isinstance(edge, tuple) or len(edge) != 2 or any(type(node) is not int or not 0 <= node < count for node in edge):
            raise ValueError("edge rejected")
        source, target = edge
        forward[source].append(target); backward[target].append(source)
    seen = set(); finished = []
    def finish(node):
        seen.add(node)
        for neighbor in forward[node]:
            if neighbor not in seen: finish(neighbor)
        finished.append(node)
    for node in range(count):
        if node not in seen: finish(node)
    seen.clear(); components = []
    def collect(node, component):
        seen.add(node); component.append(node)
        for neighbor in backward[node]:
            if neighbor not in seen: collect(neighbor, component)
    for node in reversed(finished):
        if node not in seen:
            component = []; collect(node, component); components.append(sorted(component))
    return sorted(components)

print(dependency_components(6, [(0,1),(1,2),(2,0),(2,3),(3,4),(4,3)]))
print(dependency_components(2, [(0,1)]))''','[[0, 1, 2], [3, 4], [5]]\n[[0], [1]]',
'The two traversals and reversed adjacency use O(V+E) graph work and storage before output sorting. Recursive depth is bounded by at most 32 accepted vertices here; a larger graph needs a stack policy rather than blindly raising the interpreter recursion limit.',
['Use reversed edges for the second traversal.','Include isolated vertices rather than deriving vertices only from edges.'],['python/topological-sort','python/graph-bfs','python/recursion-boundaries'],subject='python-dsa')

lesson('graph-bridges','Python graph bridges: track edge identity when parallel links are allowed',
'A bridge is an undirected edge whose removal increases the graph’s number of connected components.',
'The network fixture records discovery times and the earliest ancestor reachable from each DFS subtree. A tree edge is a bridge only when its child subtree cannot reach the parent or an earlier ancestor through another edge. Every edge has an ID. Skipping only the parent edge, rather than every edge to the parent vertex, keeps a parallel link visible as an alternate route.',
'Disconnected components are all visited. Self-loops and parallel edges are accepted and do not become false bridges. This fixture returns edge IDs because two physical links can have the same endpoint pair. [[python/union-find|Connectivity state]] and [[python/strongly-connected-components|Directed components]] solve different graph contracts.',
r'''def bridge_links(count, edges):
    if type(count) is not int or not 0 <= count <= 32 or len(edges) > 256:
        raise ValueError("graph budget rejected")
    adjacency = [[] for _ in range(count)]
    for number, edge in enumerate(edges):
        if not isinstance(edge, tuple) or len(edge) != 2 or any(type(node) is not int or not 0 <= node < count for node in edge):
            raise ValueError("edge rejected")
        first, second = edge
        adjacency[first].append((second, number)); adjacency[second].append((first, number))
    discovery = [-1] * count; earliest = [0] * count; clock = 0; result = []
    def visit(node, parent_edge):
        nonlocal clock
        discovery[node] = earliest[node] = clock; clock += 1
        for neighbor, edge_id in adjacency[node]:
            if edge_id == parent_edge: continue
            if discovery[neighbor] < 0:
                visit(neighbor, edge_id)
                earliest[node] = min(earliest[node], earliest[neighbor])
                if earliest[neighbor] > discovery[node]: result.append(edge_id)
            else:
                earliest[node] = min(earliest[node], discovery[neighbor])
    for node in range(count):
        if discovery[node] < 0: visit(node, -1)
    return sorted(result)

print("parallel-safe bridges:", bridge_links(4, [(0,1),(0,1),(1,2),(2,3),(3,2)]))
print("cycle bridges:", bridge_links(3, [(0,1),(1,2),(2,0)]))''','parallel-safe bridges: [2]\ncycle bridges: []',
'DFS uses O(V+E) traversal work and retained adjacency, plus sorting of returned edge IDs. The vertex and edge budgets bound recursion and retained input here. This is a topology check, not a physical reliability estimate.',
['Skip the incoming edge ID, not every edge with the parent endpoint.','A self-loop cannot connect two otherwise separate components.'],['python/union-find','python/strongly-connected-components','python/graph-bfs'],subject='python-dsa')

lesson('compressed-trie','Python compressed trie: merge single-child paths without losing terminal words',
'A compressed trie stores a string label on each merged edge instead of retaining one node for every character of a single-child path.',
'The fixture first builds a bounded ASCII-word trie, then compresses paths only while the intermediate node is nonterminal and has exactly one child. A terminal prefix remains a node so a short accepted word can coexist with a longer word. Exact lookup consumes an entire edge label before moving to its child; ending midway through an edge is not an accepted word.',
'Compression changes representation rather than changing accepted words. Insertion or deletion into the compressed structure needs edge splitting/merging policies not implemented here. The uncompressed construction still uses its original prefix memory before the compressed result is produced. [[python/trie-prefix|Prefix traversal]] and [[python/trie-deletion|Deletion ownership]] describe the mutable version.',
r'''import re

def compressed_routes(words):
    if len(words) > 128 or any(not isinstance(word, str) or re.fullmatch(r"[A-Z]{1,32}", word) is None for word in words):
        raise ValueError("bounded route words required")
    root = {"terminal": False, "children": {}}
    for word in words:
        node = root
        for symbol in word:
            node = node["children"].setdefault(symbol, {"terminal": False, "children": {}})
        node["terminal"] = True
    def compress(node):
        result = {"terminal": node["terminal"], "edges": {}}
        for symbol, child in node["children"].items():
            label = symbol
            while not child["terminal"] and len(child["children"]) == 1:
                symbol, child = next(iter(child["children"].items())); label += symbol
            result["edges"][label] = compress(child)
        return result
    return compress(root)

def contains_route(root, word):
    if not isinstance(word, str) or re.fullmatch(r"[A-Z]{1,32}", word) is None:
        raise ValueError("route word rejected")
    position = 0; node = root
    while position < len(word):
        for label, child in node["edges"].items():
            if word.startswith(label, position):
                position += len(label); node = child; break
        else:
            return False
    return node["terminal"]

routes = compressed_routes(["DEL", "DELHI", "BOM"])
print("root labels:", sorted(routes["edges"]))
for word in ("DEL", "DELHI", "DE", "BOM"):
    print(word, contains_route(routes, word))''',"root labels: ['BOM', 'DEL']\nDEL True\nDELHI True\nDE False\nBOM True",
'Construction visits stored prefixes and retains both the temporary trie and compressed output during conversion. Lookup checks outgoing labels and consumed characters; this ASCII alphabet bounds outgoing edge count to 26. Naive repeated label concatenation adds allocation work, so no universal memory or timing improvement is claimed.',
['Do not compress away a node that marks an accepted prefix word.','Ending inside an edge label is not exact membership.'],['python/trie-prefix','python/trie-deletion','python/strings-bytes'],subject='python-dsa')

lesson('longest-palindrome','Python longest palindrome: expand around odd and even centers',
'A palindromic substring reads the same forward and backward within a contiguous sequence of code points.',
'The label fixture tests both a single-character center and a gap between adjacent characters. It expands while the two sides match and retains the longest observed span. Equal-length ties keep the earlier discovered span, which is the leftmost for this center order. Empty input returns an empty string. The function does not reorder characters or solve a subsequence problem.',
'The accepted length is capped at 128 code points. Combining marks and user-perceived grapheme clusters can require a different comparison/editing contract. Center expansion is simple but quadratic on repeated input; it is not the linear-time palindrome algorithm. [[python/unicode-normalization|Text equivalence]], [[python/longest-common-subsequence|Subsequences]] and [[python/sliding-window|Substring windows]] cover related distinctions.',
r'''def longest_label_palindrome(text):
    if not isinstance(text, str) or len(text) > 128:
        raise ValueError("bounded label required")
    best_left = 0; best_right = 0
    for center in range(2 * len(text) - 1):
        left = center // 2; right = left + center % 2
        while left >= 0 and right < len(text) and text[left] == text[right]:
            if right + 1 - left > best_right - best_left:
                best_left, best_right = left, right + 1
            left -= 1; right += 1
    return text[best_left:best_right]

print(longest_label_palindrome("DELLEVELBOM"))
print(longest_label_palindrome("ABBA"))
print("empty:", repr(longest_label_palindrome("")))
print("leftmost tie:", longest_label_palindrome("ABACDC"))''',"LEVEL\nABBA\nempty: ''\nleftmost tie: ABA",
'Worst-case center expansion costs O(n²) comparisons and O(1) working indexes. The returned slice allocates up to O(n) characters. Code-point equality is not automatically a grapheme or locale policy.',
['Even-length palindromes need gap centers.','Substring and subsequence outputs have different contracts.'],['python/sliding-window','python/unicode-normalization','python/longest-common-subsequence'],subject='python-dsa')

group('python-dsa','Deletion repair, edge identity and compressed text indexes',['avl-deletion','strongly-connected-components','graph-bridges','compressed-trie','longest-palindrome'])

lesson('bounded-json-lines','Python JSON Lines: cap line bytes and validate the whole batch before returning it',
'JSON Lines represents one JSON value per line, but a line separator does not impose byte, row or schema limits.',
'The receipt reader accepts a caller-owned binary stream, at most four rows and at most 128 received bytes. Each line is capped at 64 bytes and must end in a newline. Duplicate object keys are rejected during decoding; accepted rows require one ASCII receipt ID and an exact bounded integer amount. The reader returns its private list only after every consumed row passes.',
'A rejected later line produces no returned batch, but bytes already consumed are not put back into the source. This operation does not close the stream or promise a network deadline. Decoded JSON types still need validation, and an accepted ID still needs existence/authorization policy before database access. [[python/json-validation|Object schema]], [[python/input-output|Stream ownership]] and [[python/chunked-aggregation|Later-batch failure]] make these distinctions explicit.',
r'''import io
import json
import re

def unique_object(pairs):
    result = {}
    for key, value in pairs:
        if key in result: raise ValueError("duplicate JSON key")
        result[key] = value
    return result

def read_receipt_lines(source):
    staged = []; received = 0
    while True:
        line = source.readline(65)
        if not line: return staged
        received += len(line)
        if len(line) > 64 or not line.endswith(b"\n") or received > 128 or len(staged) >= 4:
            raise ValueError("stream budget rejected")
        record = json.loads(line.decode("utf-8"), object_pairs_hook=unique_object)
        if not isinstance(record, dict) or set(record) != {"id", "amount"}:
            raise ValueError("record fields rejected")
        if not isinstance(record["id"], str) or re.fullmatch(r"R-[0-9]{4}", record["id"]) is None:
            raise ValueError("identifier rejected")
        if type(record["amount"]) is not int or not 0 <= record["amount"] <= 1000000:
            raise ValueError("amount rejected")
        staged.append(record)

source = io.BytesIO(b'{"id":"R-0041","amount":125}\n{"id":"R-0042","amount":75}\n')
print(read_receipt_lines(source))
print("caller stream open:", not source.closed)
try:
    read_receipt_lines(io.BytesIO(b'{"id":"R-0041","amount":125}\n{"id":"R-0042","amount":true}\n'))
except ValueError:
    print("later row rejected")''',"[{'id': 'R-0041', 'amount': 125}, {'id': 'R-0042', 'amount': 75}]\ncaller stream open: True\nlater row rejected",
'The declared byte and row budgets cap retained parsing work for this fixture. Readline may still block on a real transport. Private staging retains O(n) accepted rows until completion; publication into a database requires its own transaction.',
['A line-oriented format does not cap received bytes.','Reject duplicate JSON keys before accepting a schema.'],['python/json-validation','python/input-output','python/chunked-aggregation'],subject='python-examples')

lesson('sqlite-writer-contention','Python SQLite writer contention: reject a busy transaction before changing state',
'SQLite serializes writers, so acquiring a write transaction can fail while another connection retains the writer lock.',
'Two owned connections open the same temporary database. The first begins an immediate transaction and updates one amount. The second uses a zero busy timeout and fails to acquire its own immediate transaction. After the first commits, the second can acquire the writer slot, update and commit. The final amount proves the rejected attempt did not apply an extra update.',
'A longer busy timeout changes waiting behavior rather than removing contention. Retrying a whole operation must preserve request identity and not repeat unrelated effects. Transaction modes and journal settings also affect when locks are acquired. This fixture uses local SQLite, not a claim about every production database. [[python/sqlite-transactions|Rollback]], [[python/idempotent-jobs|Replay identity]] and [[python/outbox-project|Staged events]] connect the state contracts.',
r'''from pathlib import Path
import sqlite3
import tempfile

with tempfile.TemporaryDirectory() as directory:
    path = Path(directory) / "owned.sqlite3"
    first = sqlite3.connect(path, timeout=0, isolation_level=None)
    second = sqlite3.connect(path, timeout=0, isolation_level=None)
    try:
        first.execute("CREATE TABLE receipts (id INTEGER PRIMARY KEY, amount INTEGER NOT NULL)")
        first.execute("INSERT INTO receipts VALUES (41,125)")
        first.execute("BEGIN IMMEDIATE")
        first.execute("UPDATE receipts SET amount=amount+25 WHERE id=41")
        try:
            second.execute("BEGIN IMMEDIATE")
        except sqlite3.OperationalError as failure:
            print("busy rejected:", failure.sqlite_errorcode == sqlite3.SQLITE_BUSY)
        first.commit()
        second.execute("BEGIN IMMEDIATE")
        second.execute("UPDATE receipts SET amount=amount+25 WHERE id=41")
        second.commit()
        print("committed amount:", first.execute("SELECT amount FROM receipts WHERE id=41").fetchone()[0])
    finally:
        first.close(); second.close()''','busy rejected: True\ncommitted amount: 175',
'Lock acquisition depends on database state and timeout policy, not just SQL statement count. This fixture uses one row and no waiting. A deployment needs bounded retries, cancellation and observability rather than an unbounded retry loop.',
['A busy acquisition is not permission to perform the write outside its transaction.','Retrying an operation must not duplicate external effects.'],['python/sqlite-transactions','python/idempotent-jobs','python/outbox-project'],subject='python-examples')

lesson('zip-member-validation','Python ZIP extraction: validate names and decompressed budgets before owned writes',
'ZIP member validation separates archive metadata and decompressed byte limits from the filesystem paths used to write extracted files.',
'The fixture accepts at most eight flat ASCII .txt filenames, rejects duplicate names and nonregular file modes, and caps each declared member at 256 bytes and the batch at 512. It reads each member with a second byte cap before any output file is created. Only then does it write into a freshly created owned temporary directory using exclusive file creation.',
'This intentionally rejects directories, nested paths, backslashes and symlinks instead of normalizing received paths into something accepted. Metadata alone is not a decompression guarantee; actual reads enforce the second budget and let ZIP integrity failures propagate. The archive byte buffer is already bounded/owned by the caller. This is not a race-safe extractor for a shared deployment directory or crash-durable publication. [[python/pathlib-files|Path ownership]] and [[python/atomic-report-project|Publication staging]] cover different limits.',
r'''import io
from pathlib import Path
import re
import stat
import tempfile
import zipfile

def staged_zip_members(payload):
    if not isinstance(payload, bytes) or len(payload) > 2048:
        raise ValueError("archive byte budget rejected")
    staged = {}; total = 0
    with zipfile.ZipFile(io.BytesIO(payload)) as archive:
        members = archive.infolist()
        if len(members) > 8: raise ValueError("member budget rejected")
        for member in members:
            kind = stat.S_IFMT(member.external_attr >> 16)
            if re.fullmatch(r"[a-z][a-z0-9_-]{0,15}\.txt", member.filename) is None or member.filename in staged or kind not in (0, stat.S_IFREG):
                raise ValueError("member name or mode rejected")
            if member.file_size > 256: raise ValueError("member bytes rejected")
            with archive.open(member) as stream:
                data = stream.read(257)
            total += len(data)
            if len(data) > 256 or total > 512: raise ValueError("decompressed budget rejected")
            staged[member.filename] = data
    return staged

def owned_archive(name, content):
    buffer = io.BytesIO()
    with zipfile.ZipFile(buffer, "w", zipfile.ZIP_DEFLATED) as archive:
        archive.writestr(name, content)
    return buffer.getvalue()

members = staged_zip_members(owned_archive("receipts.txt", b"R-0041\n"))
with tempfile.TemporaryDirectory() as directory:
    for name, data in members.items():
        with (Path(directory) / name).open("xb") as destination: destination.write(data)
    print("owned files:", sorted(path.name for path in Path(directory).iterdir()))
for name, content in (("../escape.txt", b"rejected"), ("receipts.txt", b"x" * 257)):
    try: staged_zip_members(owned_archive(name, content))
    except ValueError: print("archive rejected before writes")''',"owned files: ['receipts.txt']\narchive rejected before writes\narchive rejected before writes",
'Archive and decompressed budgets bound this fixture’s retained buffers. Compression processing still has format-dependent work. Entire accepted contents are staged in memory before writes; a larger importer needs streaming staging and a separate publication contract.',
['Validate actual decompressed bytes as well as advertised sizes.','A fresh owned directory is different from a shared directory with concurrent symlink changes.'],['python/pathlib-files','python/atomic-report-project','python/bounded-json-lines'],subject='python-examples')

group('python-examples','Reception, writer contention and owned archive members',['bounded-json-lines','sqlite-writer-contention','zip-member-validation'])

lesson('outbox-project','Python SQLite outbox project: commit a receipt and its pending event together',
'An outbox stores an application state change and its pending event in the same database transaction so they cannot commit independently.',
'The receipt writer inserts a receipt and one stable event ID together. A forced failure after the receipt insert rolls back both tables. The local consumer reads pending events and records an acknowledgement separately. Reading again before acknowledgement returns the same event, exposing the duplicate-delivery boundary rather than pretending a database transaction controls an external recipient.',
'No network delivery occurs here. A worker can crash after an external recipient accepts an event but before the acknowledgement commits, so the recipient still needs a deduplication/idempotency policy. Concurrent workers require claiming or lease rules absent from this sequential fixture. [[python/idempotent-jobs|Replay identity]], [[python/sqlite-writer-contention|Writer locks]] and [[spring/transaction-events|Spring transaction-event timing]] connect the same failure model.',
r'''import sqlite3

def open_outbox():
    database = sqlite3.connect(":memory:")
    database.executescript("CREATE TABLE receipts (id TEXT PRIMARY KEY, amount INTEGER NOT NULL); CREATE TABLE outbox (id TEXT PRIMARY KEY, receipt_id TEXT NOT NULL, acknowledged INTEGER NOT NULL DEFAULT 0);")
    return database

def create_receipt(database, identifier, amount, fail=False):
    if not isinstance(identifier, str) or identifier not in {"R-0041", "R-0042"} or type(amount) is not int or not 0 <= amount <= 1000000:
        raise ValueError("receipt rejected")
    with database:
        database.execute("INSERT INTO receipts VALUES (?,?)", (identifier, amount))
        if fail: raise RuntimeError("staged failure")
        database.execute("INSERT INTO outbox(id,receipt_id) VALUES (?,?)", ("created:" + identifier, identifier))

def pending_events(database):
    return database.execute("SELECT id,receipt_id FROM outbox WHERE acknowledged=0 ORDER BY id LIMIT 16").fetchall()

with open_outbox() as database:
    create_receipt(database, "R-0041", 125)
    try: create_receipt(database, "R-0042", 250, fail=True)
    except RuntimeError: print("failed receipt rolled back")
    print("receipts:", database.execute("SELECT count(*) FROM receipts").fetchone()[0])
    first = pending_events(database)
    print("pending:", first)
    print("replay before acknowledgement:", pending_events(database) == first)
    with database:
        database.execute("UPDATE outbox SET acknowledged=1 WHERE id=?", (first[0][0],))
    print("pending after acknowledgement:", pending_events(database))
database.close()''',"failed receipt rolled back\nreceipts: 1\npending: [('created:R-0041', 'R-0041')]\nreplay before acknowledgement: True\npending after acknowledgement: []",
'The fixture performs fixed-size inserts and bounded pending reads. A production outbox needs retention, indexes, retry limits and metrics. The in-memory database proves transaction behavior here, not clean-reopen durability or exactly-once external effects.',
['Store the event inside the same transaction as the state change.','An external delivery and its later acknowledgement are separate failure points.'],['python/idempotent-jobs','python/sqlite-writer-contention','spring/transaction-events'],subject='python-projects')

lesson('lru-project','Python LRU cache project: make misses, replacement and eviction explicit',
'A least-recently-used cache evicts the retained entry whose last recorded access precedes the others when a new entry exceeds capacity.',
'The receipt cache accepts one to sixteen entries with fixed ASCII IDs and exact bounded integer values. Get returns None for a miss and moves a hit to the newest end. Put updates an existing key without increasing retained count, or inserts and evicts the oldest key. All input validation precedes mutation, so a rejected amount cannot alter access order.',
'None cannot be a stored value in this contract, so it is an unambiguous miss. The cache is process-local, has no expiry and is not synchronized across threads. Mutating the exposed internal dictionary bypasses its invariant. [[python/ordered-dictionaries|Order operations]], [[python/functools-cache|Callable-result caching]] and [[python/thread-locks|Compound transitions]] have different policies.',
r'''from collections import OrderedDict
import re

class ReceiptCache:
    def __init__(self, capacity):
        if type(capacity) is not int or not 1 <= capacity <= 16:
            raise ValueError("capacity rejected")
        self.capacity = capacity; self.entries = OrderedDict()
    def _key(self, key):
        if not isinstance(key, str) or re.fullmatch(r"R-[0-9]{4}", key) is None:
            raise ValueError("cache key rejected")
    def get(self, key):
        self._key(key)
        if key not in self.entries: return None
        self.entries.move_to_end(key)
        return self.entries[key]
    def put(self, key, amount):
        self._key(key)
        if type(amount) is not int or not 0 <= amount <= 1000000:
            raise ValueError("cache amount rejected")
        self.entries[key] = amount; self.entries.move_to_end(key)
        if len(self.entries) > self.capacity: self.entries.popitem(last=False)

cache = ReceiptCache(2)
cache.put("R-0041", 125); cache.put("R-0042", 250)
print("hit:", cache.get("R-0041"))
cache.put("R-0043", 75)
print("evicted miss:", cache.get("R-0042"))
cache.put("R-0041", 150)
print("retained order:", list(cache.entries))
print("updated:", cache.get("R-0041"))''',"hit: 125\nevicted miss: None\nretained order: ['R-0043', 'R-0041']\nupdated: 150",
'Expected lookup/update/endpoint eviction work is constant under suitable hashes. Retained state is O(capacity) and accepted values are immutable integers. This implementation makes no stale-data detection or cross-process consistency guarantee.',
['Define a miss representation that cannot be confused with a stored value.','Validate rejected writes before changing order or contents.'],['python/ordered-dictionaries','python/functools-cache','python/thread-locks'],subject='python-projects')

lesson('plugin-project','Python plugin project: load owned code and publish only an accepted interface',
'A plugin loader executes a selected module and checks its exported interface before making it available to application dispatch.',
'The fixture writes two owned modules into a temporary directory and loads each through importlib’s file specification. It places the module in sys.modules for initialization and removes that entry when loading or validation fails. A successful module must expose a callable receipt_label that passes one declared smoke case. Only that accepted callable enters the local registry.',
'The smoke case is not proof for every input, and module side effects are not rolled back by removing a cache entry. This loader must receive trusted, application-owned code paths; it is not an isolation boundary for uploads or arbitrary executable text. The fixture releases its module entries when finished. [[python/import-failures|Failed initialization]], [[python/first-class-functions|Accepted dispatch]] and [[python/typing-protocol|Interface claims]] explain the remaining boundaries.',
r'''import importlib.util
from pathlib import Path
import sys
import tempfile

def load_owned_label(path, name):
    specification = importlib.util.spec_from_file_location(name, path)
    if specification is None or specification.loader is None:
        raise ValueError("module specification unavailable")
    module = importlib.util.module_from_spec(specification)
    if name in sys.modules: raise ValueError("module name already retained")
    sys.modules[name] = module
    try:
        specification.loader.exec_module(module)
        operation = getattr(module, "receipt_label", None)
        if not callable(operation) or operation(41) != "R-0041":
            raise ValueError("plugin interface rejected")
        return operation
    except BaseException:
        sys.modules.pop(name, None)
        raise

with tempfile.TemporaryDirectory() as directory:
    owned = Path(directory)
    accepted = owned / "accepted.py"; rejected = owned / "rejected.py"
    accepted.write_text('def receipt_label(number):\n    return f"R-{number:04d}"\n', encoding="utf-8")
    rejected.write_text('receipt_label = 125\n', encoding="utf-8")
    registry = {}
    try:
        registry["minor"] = load_owned_label(accepted, "aitrove_owned_label")
        print(registry["minor"](41))
        try: registry["invalid"] = load_owned_label(rejected, "aitrove_rejected_label")
        except ValueError: print("rejected registry absent:", "invalid" not in registry)
        print("failed module absent:", "aitrove_rejected_label" not in sys.modules)
    finally:
        sys.modules.pop("aitrove_owned_label", None)''','R-0041\nrejected registry absent: True\nfailed module absent: True',
'Initialization executes the module’s own work. The tiny owned sources here have bounded smoke checks; a file path or an import API does not impose execution time, memory or side-effect limits. Published callables retain their module-global references even after cache removal.',
['Import cache cleanup does not undo external side effects.','Do not label a trusted-code loader as an upload sandbox.'],['python/import-failures','python/first-class-functions','python/typing-protocol'],subject='python-projects')

group('python-projects','Accepted dispatch, bounded retention and pending-event ownership',['outbox-project','lru-project','plugin-project'])

lesson('wheel-installation','Python wheel installation: test the built artifact outside its source directory',
'A wheel installation copies a built distribution into an import environment, which can expose packaging omissions hidden by imports from a source checkout.',
'The fixture builds an owned src-layout package offline, installs its wheel without dependencies into a fresh temporary target, and imports only from that target in an isolated child process. It checks the returned value and verifies that the imported file resides under the installation target. The source directory is not added to the child’s import path.',
'No package index is contacted and no system site-packages directory is changed. Build tools execute the selected backend, so build inputs must be trusted. This test covers one pure-Python package and interpreter, not binary wheel compatibility, dependency resolution or a signed release pipeline. [[python/pyproject-config|Build metadata]], [[python/package-resources|Included data]] and [[python/runtime-compatibility|Runtime checks]] identify separate release requirements.',
r'''from pathlib import Path
import subprocess
import sys
import tempfile

with tempfile.TemporaryDirectory() as directory:
    owned = Path(directory); project = owned / "project"; target = owned / "installed"
    package = project / "src" / "aitrove_installed_receipt"; package.mkdir(parents=True)
    (package / "__init__.py").write_text('def surcharge():\n    return 25\n', encoding="utf-8")
    (project / "pyproject.toml").write_text('[build-system]\nrequires = ["setuptools==84.0.0"]\nbuild-backend = "setuptools.build_meta"\n[project]\nname = "aitrove-installed-receipt"\nversion = "0.1.0"\n[tool.setuptools.packages.find]\nwhere = ["src"]\n', encoding="utf-8")
    subprocess.run([sys.executable, "-I", "-m", "build", "--wheel", "--no-isolation", str(project)], check=True, capture_output=True, text=True, timeout=15)
    wheel = next((project / "dist").glob("*.whl"))
    subprocess.run([sys.executable, "-I", "-m", "pip", "install", "--no-index", "--no-deps", "--no-cache-dir", "--disable-pip-version-check", "--target", str(target), str(wheel)], check=True, capture_output=True, text=True, timeout=15)
    source = 'import sys\nfrom pathlib import Path\nsys.path.insert(0,sys.argv[1])\nimport aitrove_installed_receipt as receipt\nprint("installed amount:",receipt.surcharge())\nprint("installed origin:",Path(receipt.__file__).is_relative_to(Path(sys.argv[1])))\n'
    result = subprocess.run([sys.executable, "-I", "-c", source, str(target)], cwd=owned, check=True, capture_output=True, text=True, timeout=5)
    print(result.stdout.strip())''','installed amount: 25\ninstalled origin: True',
'Build and installation work depends on source size, backend behavior and the wheel. This tiny package is tested under explicit subprocess timeouts and owned temporary paths. No cross-platform wheel lock or supply-chain assurance is inferred from successful installation.',
['Import the installed artifact outside the checkout when checking packaged contents.','A successful local install does not verify every dependency or target platform.'],['python/pyproject-config','python/package-resources','python/runtime-compatibility'],subject='python-packaging',dependencies=['build==1.6.1','setuptools==84.0.0','pip==26.1.2'])

lesson('editable-installation','Python editable installation: source changes and metadata changes have different lifetimes',
'An editable installation connects an installed distribution to its working source so supported source changes can be observed without building a release wheel each time.',
'The fixture creates a fresh temporary installation target using the already tested build backend, installs one owned package in editable mode offline, and imports it in a fresh process. It edits the source and imports again in another fresh process. The changed result proves the source connection without pretending that an already imported module would automatically reload.',
'The build uses the already recorded backend environment, so this is not a clean dependency-resolution test. New package files, entry points, metadata or compiled extensions may require rebuilding/reinstalling. Imported modules remain cached in a running process. The target is explicitly processed with site.addsitedir in the child to activate its editable import hooks; it is deleted with its owned temporary directory. The project environment is not modified. [[python/wheel-installation|Release artifact installation]] and [[python/import-failures|Import state]] cover other boundaries.',
r'''from pathlib import Path
import subprocess
import sys
import tempfile

with tempfile.TemporaryDirectory() as directory:
    owned = Path(directory); project = owned / "project"; target = owned / "installed"
    package = project / "src" / "aitrove_editable_receipt"; package.mkdir(parents=True)
    module = package / "__init__.py"
    module.write_text('def fee():\n    return 25\n', encoding="utf-8")
    (project / "pyproject.toml").write_text('[build-system]\nrequires = ["setuptools==84.0.0"]\nbuild-backend = "setuptools.build_meta"\n[project]\nname = "aitrove-editable-receipt"\nversion = "0.1.0"\n[tool.setuptools.packages.find]\nwhere = ["src"]\n', encoding="utf-8")
    subprocess.run([sys.executable, "-I", "-m", "pip", "install", "--no-index", "--no-deps", "--no-build-isolation", "--no-cache-dir", "--disable-pip-version-check", "--target", str(target), "-e", str(project)], check=True, capture_output=True, text=True, timeout=20)
    def installed_fee():
        result = subprocess.run([sys.executable, "-I", "-B", "-c", 'import site,sys; site.addsitedir(sys.argv[1]); import aitrove_editable_receipt; print(aitrove_editable_receipt.fee())', str(target)], cwd=owned, check=True, capture_output=True, text=True, timeout=5)
        return result.stdout.strip()
    print("first process:", installed_fee())
    module.write_text('def fee():\n    return 125\n', encoding="utf-8")
    print("fresh process after edit:", installed_fee())''','first process: 25\nfresh process after edit: 125',
'The backend determines editable installation machinery and cost. Fresh process imports avoid stale module objects; the changed source size and disabled bytecode writes keep this fixture independent of timestamp-based bytecode reuse. This is one tested backend, not a guarantee for every build system.',
['Source editing does not automatically update a previously imported module object.','Editable development behavior does not prove release-wheel contents.'],['python/wheel-installation','python/pyproject-config','python/import-failures'],subject='python-packaging',dependencies=['setuptools==84.0.0','pip==26.1.2'])

group('python-packaging','Installed release artifacts and editable source connections',['wheel-installation','editable-installation'])

lesson('pandas-pivot','Pandas pivot: duplicates need an aggregation policy before reshaping',
'Pivot reshapes unique index/column pairs into a wider DataFrame without inventing an aggregation rule for duplicate pairs.',
'The receipt frame contains two amounts for one region and period. Direct pivot rejects that duplicate pair. The accepted contract groups each pair and sums it before reshaping, then reindexes to a declared period order. Missing combinations remain missing rather than being silently replaced with zero. The source frame stays unchanged.',
'Choosing sum, last or mean changes the meaning of duplicate input; it is not merely a formatting fix. A wide result can allocate many mostly empty cells when key cardinalities grow. Predeclare output budgets before pivoting a received large dataset. [[python/pandas-groupby|Aggregation policy]], [[python/pandas-nullable|Missing values]] and [[python/pandas-joins|Cardinality]] supply connected checks.',
r'''import pandas as pd

receipts = pd.DataFrame({"region": ["DEL", "DEL", "BOM"], "period": ["P1", "P1", "P2"], "amount": [125, 75, 250]})
try:
    receipts.pivot(index="region", columns="period", values="amount")
except ValueError:
    print("duplicate pair rejected")
grouped = receipts.groupby(["region", "period"], as_index=False)["amount"].sum()
wide = grouped.pivot(index="region", columns="period", values="amount").reindex(columns=["P1", "P2"])
print("accepted total:", int(wide.loc["DEL", "P1"]))
print("missing retained:", bool(pd.isna(wide.loc["DEL", "P2"])))
print("source rows:", len(receipts))''','duplicate pair rejected\naccepted total: 200\nmissing retained: True\nsource rows: 3',
'Grouping and reshaping cost depends on row count, key cardinalities and retained output cells. A two-dimensional result can approach the product of distinct key counts rather than merely the number of source rows.',
['Duplicate pairs need an explicit domain aggregation rule.','A missing combination is not automatically a measured zero.'],['python/pandas-groupby','python/pandas-nullable','python/pandas-joins'],subject='python-data',dependencies=['pandas==3.0.6'])

lesson('pandas-categorical','Pandas categorical values: reject unknown labels before conversion',
'A categorical dtype stores values against a declared category set and can carry an explicit ordering for those categories.',
'The receipt-state fixture declares pending, accepted and rejected in workflow order. It validates each received state against that set before conversion. An unchecked unknown label becomes missing during conversion, which would conceal a rejected input if missing and unknown were treated alike. Sorting the accepted categorical values follows the declared category order rather than alphabetic order.',
'Category order does not itself enforce valid transitions between states. A missing source value also needs a separate policy, and categorical codes are representation details rather than stable wire IDs. Memory savings depend on cardinality and representation; this fixture reports behavior, not a measured universal ratio. [[python/enums|Wire states]] and [[python/aggregation-exercise|Accepted records]] explain other state boundaries.',
r'''import pandas as pd

states = ["pending", "accepted", "rejected"]
dtype = pd.CategoricalDtype(states, ordered=True)
received = pd.Series(["accepted", "pending", "rejected"], dtype="string")
if not received.isin(states).all(): raise ValueError("unknown state rejected")
accepted = received.astype(dtype)
print("workflow order:", accepted.sort_values().astype(str).tolist())
unchecked = pd.Series(["archived"], dtype="string").astype(dtype)
print("unchecked unknown becomes missing:", bool(unchecked.isna().iloc[0]))
print("explicit validation:", bool(pd.Series(["archived"]).isin(states).all()))''',"workflow order: ['pending', 'accepted', 'rejected']\nunchecked unknown becomes missing: True\nexplicit validation: False",
'Validation scans n source values; categorical conversion retains codes and a category dictionary. High-cardinality data can erase expected memory benefits. Category transitions and versioned schema migration remain application work.',
['Validate unknown labels before they are converted to missing values.','Do not publish categorical codes as stable business identifiers.'],['python/enums','python/pandas-nullable','python/aggregation-exercise'],subject='python-data',dependencies=['pandas==3.0.6'])

lesson('bootstrap-means','NumPy bootstrap means: seeded resampling does not repair biased input',
'Bootstrap resampling draws with replacement from an observed sample to examine variation in a chosen statistic under that empirical sampling model.',
'The fixture accepts two to 64 finite numeric observations and one to 4096 resamples. It draws an owned index matrix with a seeded Generator, computes each resampled mean, and reports the fifth and ninety-fifth percentiles. Repeating the same seed under the tested package version reproduces the interval. The sampling rows do not alias the original observations.',
'This interval assumes the observed rows are suitable units to resample independently. Repeated measurements, clustering, selection bias and distribution shift can invalidate that interpretation. A fixed seed aids reproducibility; it supplies no scientific or business validity. The percentile range is not a guaranteed coverage statement for every underlying population. [[python/ml-pipeline|Evaluation boundaries]] and [[python/numpy-precision|Finite-value policy]] remain separate checks.',
r'''import numpy as np

def resampled_mean_interval(values, draws, seed):
    if not isinstance(values, list) or not 2 <= len(values) <= 64 or any(type(value) not in (int, float) or not np.isfinite(value) or not 0 <= value <= 1000000 for value in values):
        raise ValueError("observations rejected")
    if type(draws) is not int or not 1 <= draws <= 4096 or type(seed) is not int or not 0 <= seed <= 1000000:
        raise ValueError("resampling budget rejected")
    observed = np.array(values, dtype=float)
    generator = np.random.default_rng(seed)
    indexes = generator.integers(0, len(values), size=(draws, len(values)))
    means = observed[indexes].mean(axis=1)
    return np.quantile(means, [.05, .95])

values = [100, 200, 300, 400]
interval = resampled_mean_interval(values, 2000, 41)
print("percentile interval:", np.round(interval, 1).tolist())
print("seed reproduced:", bool(np.array_equal(interval, resampled_mean_interval(values, 2000, 41))))
print("input unchanged:", values == [100, 200, 300, 400])''','percentile interval: [150.0, 350.0]\nseed reproduced: True\ninput unchanged: True',
'For b resamples of n observations, the index matrix and sampled values require O(bn) work and memory before percentile selection. Explicit budgets cap that retained matrix here. Seeded results can change across algorithms or package versions.',
['A seed addresses reproducibility, not sample representativeness.','Resampling independent rows is not a policy for clustered observations.'],['python/numpy-precision','python/ml-pipeline','python/classification-metrics'],subject='python-data',dependencies=['numpy==2.5.3'])

group('python-data','Shape policy, category acceptance and bounded resampling',['pandas-pivot','pandas-categorical','bootstrap-means'])

lesson('mutation-testing','Python mutation testing: prove a suite rejects selected wrong implementations',
'Mutation testing evaluates whether tests detect deliberate code changes that alter the promised behavior.',
'The quantity predicate accepts exact integers from zero through one million. Two owned mutants widen the type check to accept booleans or change the upper bound to exclude an accepted boundary. The contract cases detect both. The fixture reports the number killed instead of treating the number of executed lines as evidence that those behaviors are protected.',
'Only these two defects are evaluated. Surviving mutants may be equivalent to the original or reveal missing cases; a killed score is not proof that every possible defect is detected. The code creates callable implementations directly rather than editing project files or running an external mutation service. [[python/coverage-branches|Branch measurement]], [[python/refactor-contract-tests|Preserved behavior]] and [[python/hypothesis-properties|Generated cases]] answer other testing questions.',
r'''def accepted_quantity(value):
    return type(value) is int and 0 <= value <= 1000000

def boolean_mutant(value):
    return isinstance(value, int) and 0 <= value <= 1000000

def boundary_mutant(value):
    return type(value) is int and 0 <= value < 1000000

CASES = [(0, True), (125, True), (1000000, True), (True, False), (-1, False), (1000001, False), ("125", False)]
def passes_contract(operation):
    return all(operation(value) is expected for value, expected in CASES)

print("original passes:", passes_contract(accepted_quantity))
mutants = [boolean_mutant, boundary_mutant]
print("selected mutants killed:", sum(not passes_contract(operation) for operation in mutants))
print("selected mutants:", len(mutants))''','original passes: True\nselected mutants killed: 2\nselected mutants: 2',
'For m mutants and c cases, this fixture performs O(mc) predicate checks. Whole-project mutation campaigns can rebuild/run many tests and need timeouts, isolated state and a policy for equivalent changes. No whole-project mutation score is claimed.',
['A killed score is meaningful only with its selected mutation set.','Coverage and mutation detection are different evidence.'],['python/coverage-branches','python/refactor-contract-tests','python/hypothesis-properties'],subject='python-testing')

lesson('runtime-compatibility','Python compatibility checks: parse syntax and execute contracts as separate evidence',
'A compatibility check separates grammar acceptance from actual interpreter execution and installed dependency behavior.',
'The fixture parses one owned program with the Python 3.11 grammar, then executes it in an isolated child using the current interpreter. Exact output confirms the selected operation on that interpreter. Reporting the current patch version makes the executed environment visible instead of equating grammar parsing with a runtime matrix.',
'The fixture executes only CPython 3.14.6 in the recorded environment. It does not run 3.11, PyPy, a free-threaded build or another operating system. Grammar parsing cannot verify library availability, dependency wheels or runtime semantics. A CI matrix must launch each declared target and install/test its declared dependencies. [[python/mypy-checks|Static diagnostics]] and [[python/wheel-installation|Installed artifacts]] provide different checks.',
r'''import ast
import subprocess
import sys

source = 'receipt_amounts = [125, 250, 75]\nprint(sum(receipt_amounts))\n'
ast.parse(source, feature_version=(3, 11))
print("3.11 grammar accepted")
result = subprocess.run([sys.executable, "-I", "-c", source], check=True, capture_output=True, text=True, timeout=5)
assert result.stdout == "450\n"
print("executed output:", result.stdout.strip())
print("executed runtime:", sys.version.split()[0])''','3.11 grammar accepted\nexecuted output: 450\nexecuted runtime: 3.14.6',
'The selected parse/execution has fixed small input and a child timeout. A full compatibility matrix multiplies build/install/test cost across runtimes and platforms. One successful target supplies evidence only for that tested target.',
['Grammar acceptance is not execution on that older interpreter.','Report executed runtimes and dependency versions rather than a generic compatibility claim.'],['python/mypy-checks','python/wheel-installation','python/type-hints'],subject='python-testing')

group('python-testing','Selected mutation detection and explicit compatibility evidence',['mutation-testing','runtime-compatibility'])

lesson('drf-list-visibility','Django REST Framework list visibility: filter the principal’s rows before paging',
'List visibility restricts the candidate records a principal can see before ordering and pagination select the returned page.',
'The local API view requires an authenticated principal, then applies the owner filter to its owned receipt records before the cursor and limit. Another owner’s row cannot appear in a page even if its ID lies between visible records. The cursor is an exclusive numeric ID and each response contains at most two records. The view never relies on detail-object checks being called for list results.',
'Test authentication is bypassed with force_authenticate, so this fixture does not implement tokens or login. Real querysets must place tenant/owner predicates in the database query before paging; filtering only after a page has been fetched can leak data or skip visible rows. A received owner_id must not choose the principal. [[python/drf-object-permissions|Detail checks]], [[python/django-pagination|Cursor pages]] and [[spring/method-authorization|Service authorization]] address other layers.',
r'''from types import SimpleNamespace
from django.conf import settings
settings.configure(INSTALLED_APPS=[], SECRET_KEY="owned-list-fixture", REST_FRAMEWORK={"DEFAULT_AUTHENTICATION_CLASSES": [], "UNAUTHENTICATED_USER": None})
import django
django.setup()
from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response
from rest_framework.views import APIView
from rest_framework.test import APIRequestFactory, force_authenticate

RECEIPTS = [{"id": 41, "owner_id": 7}, {"id": 42, "owner_id": 8}, {"id": 43, "owner_id": 7}, {"id": 44, "owner_id": 7}]
def visible_receipts(principal, after, limit):
    if type(principal) is not int or principal <= 0 or type(after) is not int or after < 0 or type(limit) is not int or not 1 <= limit <= 2:
        raise ValueError("list boundary rejected")
    candidates = sorted((record for record in RECEIPTS if record["owner_id"] == principal and record["id"] > after), key=lambda record: record["id"])
    return [{"id": record["id"]} for record in candidates[:limit]]

class ReceiptList(APIView):
    permission_classes = [IsAuthenticated]
    def get(self, request):
        return Response(visible_receipts(request.user.pk, 0, 2))

request = APIRequestFactory().get("/receipts")
force_authenticate(request, user=SimpleNamespace(pk=7, is_authenticated=True))
print("owner page:", ReceiptList.as_view()(request).data)
print("next owner page:", visible_receipts(7, 43, 2))
print("other owner page:", visible_receipts(8, 0, 2))
print("anonymous:", ReceiptList.as_view()(APIRequestFactory().get("/receipts")).status_code)''',"owner page: [{'id': 41}, {'id': 43}]\nnext owner page: [{'id': 44}]\nother owner page: [{'id': 42}]\nanonymous: 403",
'The local list scan/sort costs O(n log n) before its bounded returned page. Production query cost depends on owner/cursor indexes and the database plan. A returned page cap does not bound the cost of an unindexed scan.',
['Apply visibility predicates before selecting a page.','Detail-object permission hooks do not automatically filter list rows.'],['python/drf-object-permissions','python/django-pagination','spring/method-authorization'],subject='python-web',dependencies=['Django==5.2.17','djangorestframework==3.18.1'])

lesson('drf-creation-ownership','Django REST Framework creation ownership: assign the owner from the principal',
'Creation authorization decides which principal may create a record and which fields that principal may supply.',
'The local receipt endpoint accepts only a receipt ID and exact bounded integer amount. It rejects an extra owner_id instead of trusting or quietly copying it. Serializer save receives the owner from the authenticated request context, and the created record retains that server-selected owner. A duplicate ID is rejected before this local in-memory save.',
'Force_authenticate provides a test principal, not a production identity provider. This in-memory duplicate check is not race-safe; a database uniqueness constraint and transaction must enforce concurrent creation. Owner assignment alone also does not establish permission to create every record type. [[python/drf-serializers|Strict fields]], [[python/django-models|Database constraints]] and [[python/drf-list-visibility|Read visibility]] are connected boundaries.',
r'''from types import SimpleNamespace
from django.conf import settings
settings.configure(INSTALLED_APPS=[], USE_I18N=False, SECRET_KEY="owned-create-fixture", REST_FRAMEWORK={"DEFAULT_AUTHENTICATION_CLASSES": [], "UNAUTHENTICATED_USER": None})
import django
django.setup()
from rest_framework import serializers
from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response
from rest_framework.views import APIView
from rest_framework.test import APIRequestFactory, force_authenticate

RECEIPTS = {}
class ExactAmount(serializers.Field):
    def to_internal_value(self, value):
        if type(value) is not int or not 0 <= value <= 1000000: raise serializers.ValidationError("amount rejected")
        return value
class ReceiptCreation(serializers.Serializer):
    receipt_id = serializers.RegexField(r"\AR-[0-9]{4}\Z", trim_whitespace=False)
    amount = ExactAmount()
    def to_internal_value(self, data):
        if not isinstance(data, dict) or set(data) != {"receipt_id", "amount"}: raise serializers.ValidationError({"non_field_errors": ["fields rejected"]})
        return super().to_internal_value(data)
    def create(self, accepted):
        RECEIPTS[accepted["receipt_id"]] = accepted.copy()
        return accepted
class ReceiptCreateView(APIView):
    permission_classes = [IsAuthenticated]
    def post(self, request):
        serializer = ReceiptCreation(data=request.data); serializer.is_valid(raise_exception=True)
        if serializer.validated_data["receipt_id"] in RECEIPTS: return Response({"error": "duplicate"}, status=409)
        accepted = serializer.save(owner_id=request.user.pk)
        return Response({"receipt_id": accepted["receipt_id"]}, status=201)

def local_create(payload):
    request = APIRequestFactory().post("/receipts", payload, format="json")
    force_authenticate(request, user=SimpleNamespace(pk=7, is_authenticated=True))
    return ReceiptCreateView.as_view()(request).status_code

print("created:", local_create({"receipt_id": "R-0041", "amount": 125}))
print("assigned owner:", RECEIPTS["R-0041"]["owner_id"])
print("spoof rejected:", local_create({"receipt_id": "R-0042", "amount": 250, "owner_id": 8}))
print("retained records:", len(RECEIPTS))''','created: 201\nassigned owner: 7\nspoof rejected: 400\nretained records: 1',
'The owned mapping has expected constant lookup work under suitable hashes. This fixture is not a durable datastore and imposes no complete multi-request storage quota. A production create path needs database enforcement, request limits and real authentication.',
['Never assign ownership from an untrusted received owner field.','A pre-save duplicate lookup is not a concurrent uniqueness guarantee.'],['python/drf-serializers','python/django-models','python/drf-list-visibility'],subject='python-web',dependencies=['Django==5.2.17','djangorestframework==3.18.1'])

lesson('flask-error-boundaries','Flask error responses: preserve status without exposing internal exception text',
'An API error boundary converts failures into a declared response shape while retaining the intended HTTP status.',
'The local application converts HTTP exceptions into JSON with their numeric status and a fixed public message. Unexpected application failures return a separate fixed 500 message rather than copying exception text. Local test-client requests cover a missing path, wrong method, oversized JSON and an internal failure. The request-size limit is checked when the endpoint reads its body.',
'This response fixture does not configure production logging, trace IDs, alerting or a proxy body limit. An error handler must not translate every HTTP exception into status 200 or expose diagnostic strings to clients. Frontend retries also need a policy for which failures are transient. [[python/log-redaction|Diagnostic fields]], [[python/flask-json-api|Accepted payloads]] and [[spring/problem-details|Problem responses]] cover connected choices.',
r'''from flask import Flask, jsonify, request
from werkzeug.exceptions import HTTPException

application = Flask(__name__)
application.config["MAX_CONTENT_LENGTH"] = 64
@application.errorhandler(HTTPException)
def http_failure(failure):
    return jsonify(status=failure.code, error="request rejected"), failure.code
@application.errorhandler(Exception)
def internal_failure(failure):
    return jsonify(status=500, error="internal failure"), 500
@application.post("/receipts")
def create_receipt():
    request.get_json()
    return jsonify(accepted=True), 201
@application.get("/owned-failure")
def owned_failure():
    raise RuntimeError("owned diagnostic not for the response")

client = application.test_client()
print("missing:", client.get("/missing").status_code)
print("method:", client.get("/receipts").status_code)
print("oversized:", client.post("/receipts", data='"' + 'x' * 100 + '"', content_type="application/json").status_code)
failure = client.get("/owned-failure")
print("internal:", failure.status_code, failure.get_json()["error"])
print("diagnostic exposed:", b"owned diagnostic" in failure.data)''','missing: 404\nmethod: 405\noversized: 413\ninternal: 500 internal failure\ndiagnostic exposed: False',
'The fixtures have small bounded bodies and no network listener. Error serialization adds bounded response work here; logging/diagnostics can have their own I/O and privacy costs. The broad application handler does not make arbitrary failures safe to retry.',
['Keep the intended failure status rather than always returning 200.','Public error text must not copy arbitrary internal exception messages.'],['python/log-redaction','python/flask-json-api','spring/problem-details'],subject='python-web',dependencies=['Flask==3.1.3'])

group('python-web','List visibility, creation ownership and public failure shapes',['drf-list-visibility','drf-creation-ownership','flask-error-boundaries'])

lesson('database-snapshot-interview','Python database interview: a retained SQLite read snapshot can be older than a committed write',
'A database read transaction can retain a snapshot whose values do not change merely because another connection commits newer state.',
'The owned SQLite database uses WAL mode. A reader begins a transaction and reads the initial receipt amount, establishing its snapshot. A writer commits a larger amount. The reader still sees the old amount until it ends that transaction; its next read sees the committed value. The code checks transaction lifetime rather than adding a timing sleep.',
'This is SQLite WAL behavior under the tested local configuration, not a statement that every database isolation level behaves identically. Long readers can also retain old WAL pages and affect checkpoint progress. An application must decide where its unit of work begins and ends. [[python/sqlite-writer-contention|Writer acquisition]] and [[python/sqlite-transactions|Commit/rollback]] provide related traces.',
r'''from pathlib import Path
import sqlite3
import tempfile

with tempfile.TemporaryDirectory() as directory:
    path = Path(directory) / "snapshot.sqlite3"
    writer = sqlite3.connect(path, isolation_level=None)
    reader = sqlite3.connect(path, isolation_level=None)
    try:
        assert writer.execute("PRAGMA journal_mode=WAL").fetchone()[0] == "wal"
        writer.execute("CREATE TABLE receipts (id INTEGER PRIMARY KEY, amount INTEGER NOT NULL)")
        writer.execute("INSERT INTO receipts VALUES (41,125)")
        reader.execute("BEGIN")
        print("first read:", reader.execute("SELECT amount FROM receipts WHERE id=41").fetchone()[0])
        writer.execute("UPDATE receipts SET amount=250 WHERE id=41")
        print("retained snapshot:", reader.execute("SELECT amount FROM receipts WHERE id=41").fetchone()[0])
        reader.commit()
        print("new read:", reader.execute("SELECT amount FROM receipts WHERE id=41").fetchone()[0])
    finally:
        reader.close(); writer.close()''','first read: 125\nretained snapshot: 125\nnew read: 250',
'The fixture reads one indexed row. Snapshot lifetime affects concurrency and retained journal state independently of query count. It does not profile checkpoints, multiple processes or a deployment filesystem.',
['A second read inside the same snapshot need not see another connection’s commit.','Do not generalize one journal/isolation configuration to every database.'],['python/sqlite-writer-contention','python/sqlite-transactions','python/django-atomic'],subject='python-interview')

group('python-interview','Read transaction lifetime',['database-snapshot-interview'])

lesson('reconciliation-exercise','Python reconciliation exercise: reject duplicate IDs before comparing ledgers',
'Ledger reconciliation compares accepted records by stable identity and reports missing or mismatched entries without silently collapsing duplicates.',
'The exercise accepts two owned batches with unique ASCII receipt IDs and bounded exact integer amounts. Each batch is validated into a private mapping before comparison. The result distinguishes missing-left, missing-right and unequal amounts in sorted ID order. A duplicate receipt is rejected instead of allowing last-write-wins dictionary construction to hide it.',
'Reconciliation identifies differences; it does not decide which ledger is authoritative or apply corrective writes. A received ID does not establish permission to inspect the corresponding live record. The batches are bounded to 64 rows each, and input dictionaries remain unchanged. [[python/aggregation-exercise|Accepted batches]], [[python/hash-equality|Stable keys]] and [[python/idempotent-jobs|Request identity]] describe adjacent invariants.',
r'''import re

def receipt_map(records):
    if not isinstance(records, list) or len(records) > 64: raise ValueError("batch rejected")
    result = {}
    for record in records:
        if not isinstance(record, dict) or set(record) != {"id", "amount"}: raise ValueError("fields rejected")
        identifier, amount = record["id"], record["amount"]
        if not isinstance(identifier, str) or re.fullmatch(r"R-[0-9]{4}", identifier) is None or identifier in result: raise ValueError("identifier rejected")
        if type(amount) is not int or not 0 <= amount <= 1000000: raise ValueError("amount rejected")
        result[identifier] = amount
    return result

def reconcile_receipts(left_records, right_records):
    left, right = receipt_map(left_records), receipt_map(right_records)
    differences = []
    for identifier in sorted(left.keys() | right.keys()):
        if identifier not in left: differences.append((identifier, "missing-left"))
        elif identifier not in right: differences.append((identifier, "missing-right"))
        elif left[identifier] != right[identifier]: differences.append((identifier, "amount-mismatch"))
    return differences

left = [{"id":"R-0041","amount":125},{"id":"R-0042","amount":250}]
right = [{"id":"R-0041","amount":150},{"id":"R-0043","amount":75}]
print(reconcile_receipts(left, right))
try: reconcile_receipts(left + [left[0].copy()], right)
except ValueError: print("duplicate rejected")''',"[('R-0041', 'amount-mismatch'), ('R-0042', 'missing-right'), ('R-0043', 'missing-left')]\nduplicate rejected",
'For n and m accepted records, expected validation/mapping work is O(n+m); sorting union keys costs O(k log k). The result and private maps retain O(n+m) state. This bounded exercise has no live database or corrective side effects.',
['Duplicate identities are rejected input, not an ordinary overwrite.','Report differences before defining or executing corrective policy.'],['python/aggregation-exercise','python/hash-equality','python/idempotent-jobs'],subject='python-exercises')

group('python-exercises','Identity-aware reconciliation',['reconciliation-exercise'])

lesson('typing-reference','Python typing reference: annotations, structural checks and runtime validation differ',
'Type annotations describe intended values to readers and static tools but do not automatically validate values passed at runtime.',
'The receipt function annotates an integer amount yet still accepts a string at call time until its implementation explicitly checks the type and bounds. The accepted constructor then returns a TypedDict-shaped mapping. TypedDict supplies a static key/value contract; it does not create a validating runtime wrapper around that ordinary dictionary.',
'Protocols describe usable operations, while TypeGuard predicates make narrowing claims. Neither removes aliasing or verifies every method’s domain behavior. Keep validation at received-data boundaries and use static tools to check internal call paths. [[python/type-hints|Basic annotations]], [[python/typing-narrowing|Narrowing ownership]], [[python/typing-protocol|Structural interfaces]] and [[python/mypy-checks|Diagnostics]] cover the individual mechanisms.',
r'''from typing import TypedDict

class AcceptedReceipt(TypedDict):
    receipt_id: str
    amount: int

def receipt_amount(amount: int) -> AcceptedReceipt:
    if type(amount) is not int or not 0 <= amount <= 1000000:
        raise ValueError("runtime amount rejected")
    return {"receipt_id": "R-0041", "amount": amount}

print(receipt_amount(125))
try: receipt_amount("125")
except ValueError: print("annotated call rejected by runtime check")
received: AcceptedReceipt = {"receipt_id": "R-0041", "amount": "unchecked"}
print("ordinary dictionary:", type(received) is dict)
print("annotation alone corrected value:", type(received["amount"]) is int)''',"{'receipt_id': 'R-0041', 'amount': 125}\nannotated call rejected by runtime check\nordinary dictionary: True\nannotation alone corrected value: False",
'The explicit scalar check has bounded work. Annotation processing and whole-project checker cost depend on tool configuration and imported types. The intentionally wrong annotated assignment is a runtime teaching trace; a static checker should flag it rather than treating this file as a passing typing project.',
['TypedDict is not a runtime schema parser.','Mark intentionally wrong typing traces rather than claiming the checker accepts them.'],['python/type-hints','python/typing-narrowing','python/typing-protocol','python/mypy-checks'],subject='python-reference')

group('python-reference','Static claims versus runtime acceptance',['typing-reference'])

APPLIED_BANKS={
'python-graph-state-changes':('Python graph and index state-change quiz',['python/avl-deletion','python/strongly-connected-components','python/graph-bridges','python/compressed-trie','python/longest-palindrome'],[
('How does AVL deletion choose its repair rotation?',['Only from the deleted key','From the current child subtree heights/balances','From insertion timestamp','From the number of dictionary keys'],1,'Deletion can reduce height at several ancestors. Current child balance determines whether a single or paired rotation repairs that ancestor.'),
('What replaces a removed two-child BST key in this fixture?',['Any cached key','Its parent key','The smallest retained key in the right subtree','The largest key in the whole tree'],2,'The in-order successor preserves ordering when its original subtree position is removed too.'),
('What does a missing-key removal do?',['Adds a placeholder','Removes the root','Sorts the graph','Returns false without changing the logical key set'],3,'The wrapper checks membership before changing the owned tree.'),
('What defines a strongly connected component?',['Mutual directed reachability among its vertices','One incoming edge per vertex','Equal vertex labels','Undirected adjacency only'],0,'Reachability must hold in both directions within the component.'),
('Which adjacency is used in the second component traversal?',['The original sorted tree','The reversed directed edges','Only self-loops','Only shortest paths'],1,'The finishing order and reversed graph produce the component partition in this two-pass method.'),
('Why retain distinct undirected edge IDs?',['To hide endpoint values','To make every edge a bridge','To distinguish a parallel alternate link from the incoming edge','To guarantee physical network uptime'],2,'Skipping every edge to the parent vertex would lose parallel alternate connections and create false bridges.'),
('When is a DFS tree edge a bridge?',['When its child has no label','When its endpoint ID is greater','Whenever it is visited first','When the child subtree has no alternate reach to the parent or earlier ancestor'],3,'The low-link comparison checks whether removing that edge separates the subtree.'),
('Can a self-loop be a bridge?',['No; it does not connect separate components','Always','Only on a directed graph','Only at vertex zero'],0,'Removing a self-loop cannot increase the number of undirected connected components.'),
('When may a trie path be compressed through an intermediate node?',['Whenever the node has children','When it is nonterminal with exactly one child','Whenever it has a short key','Before validating words'],1,'A terminal prefix node must remain represented so the shorter accepted word is retained.'),
('Does ending halfway through a compressed edge prove exact word membership?',['Yes','Only when the edge has five characters','No','Only for uppercase input'],2,'Exact lookup must consume an entire edge and end at a terminal node.'),
('Which centers are required for all palindromic substring lengths?',['Only the first character','Only gap centers','Only single characters','Both character and gap centers'],3,'Odd lengths have character centers; even lengths have gaps between characters.'),
('Does center expansion find a longest palindromic subsequence?',['No; its output is contiguous','Yes, always','Only on repeated input','Only with sorting'],0,'Substring and subsequence problems have different accepted outputs and algorithms.'),
]),
'python-import-distribution':('Python import and distribution contract quiz',['python/import-failures','python/plugin-project','python/wheel-installation','python/editable-installation','python/typing-narrowing'],[
('What can remain after a failed module import?',['Only its return value','External side effects from initialization','No state anywhere','A valid transaction automatically'],1,'Removing a failed module cache entry does not undo files or effects created during initialization.'),
('When does the owned loader publish its callable?',['Before executing the module','When a file extension is known','After loading and the declared interface smoke check','Before checking duplicate module names'],2,'The local registry is updated only after the loader returns an accepted callable.'),
('Is the owned plugin loader safe for arbitrary received code?',['Yes, because it uses importlib','Yes, because files are temporary','Yes, because it checks one return value','No; it executes trusted code and is not a sandbox'],3,'A smoke check does not impose process, resource or side-effect isolation.'),
('Why import a built wheel from a fresh installation target?',['To detect packaging omissions hidden by source-checkout imports','To avoid every build backend','To prove all wheel platforms','To sign the release'],0,'Installed artifact tests should not accidentally import undeployed source files.'),
('Does the local wheel test contact a package index?',['Always','No; its install uses no-index and the owned wheel','Only for receipt values','Only after importing'],1,'Dependencies/backend versions are already present in the isolated test environment; no registry publication or resolution is performed.'),
('What does a fresh process help test after an editable source change?',['Automatic reload of every live object','Database recovery','A new import observing the connected source','Binary compatibility on every OS'],2,'Previously imported modules remain cached in an existing process. Fresh imports test the selected editable source connection.'),
('Do metadata or new entry-point changes always appear without reinstalling?',['Yes','Only on Windows','Only on Linux','No; backend/build metadata changes can need reinstalling'],3,'Editable source behavior does not guarantee every packaging change is picked up automatically.'),
('Does TypeGuard validate values solely through its annotation?',['No; its runtime predicate must establish the promised condition','Yes, before every call','Only for dictionaries','Only inside a virtual environment'],0,'Static narrowing trusts the predicate claim. Runtime validation is implemented by the predicate body.'),
('Can a shared mutable alias invalidate an earlier narrowing check?',['Never','Yes','Only after compilation','Only for frozen tuples'],1,'Another owner can change a list after it was checked. Owned immutable scalar snapshots avoid that membership change.'),
('Does TypedDict create a runtime validating wrapper?',['Always','Only for complete keys','No; runtime values are ordinary dictionaries','Only for integers'],2,'A static key/value declaration does not validate received data by itself.'),
('What does parsing with the 3.11 grammar establish?',['Execution on CPython 3.11','Dependency wheel availability','Cross-platform behavior','Syntax acceptance under that grammar only'],3,'Grammar parsing and actual target interpreter/dependency execution are separate evidence.'),
('What does passing a function preserve for a caller?',['The ability to choose when to call that function','The result of an already completed call','Automatic thread safety','A frozen copy of all globals'],0,'A callable object can retain state and side effects; it is not equivalent to its returned value.'),
]),
'python-application-publication':('Python application publication quiz',['python/bounded-json-lines','python/sqlite-writer-contention','python/outbox-project','python/drf-list-visibility','python/drf-creation-ownership','python/pandas-pivot'],[
('Why reject duplicate JSON object keys during decoding?',['To change the byte encoding','To prevent ambiguous fields being silently replaced','To make parsing constant time','To authorize the receipt'],1,'Last-write behavior can hide a conflicting input field. Schema validation follows decoding.'),
('Does rejecting a later streamed row put consumed bytes back?',['Always','Only in Flask','No','Only when the stream is caller-owned'],2,'Private result staging prevents a returned partial batch, but it does not rewind the transport.'),
('What happens when the second immediate SQLite writer cannot acquire the lock?',['It writes without a transaction','It becomes read-only forever','It changes every row','The acquisition fails before that intended write'],3,'The fixture observes SQLITE_BUSY and performs the update only after a later successful acquisition.'),
('Why insert receipt state and an outbox event in one transaction?',['To prevent one from committing without the other','To guarantee exactly-once remote delivery','To avoid database storage','To authenticate the user'],0,'Database atomicity covers those two local writes. Remote delivery and later acknowledgement remain separate failure points.'),
('What can a crash after remote delivery but before acknowledgement cause?',['Automatic universal rollback','The event can be delivered again','A new Python keyword','Guaranteed deduplication at the recipient'],1,'A recipient needs its own stable-event identity/deduplication policy if repeated delivery is possible.'),
('Where should list visibility filtering occur relative to pagination?',['Only after rendering','After selecting a page','Before selecting the page','Only on detail endpoints'],2,'Paging over unrestricted rows can leak records or skip visible records even if a later filter is applied.'),
('Where does this creation fixture obtain owner_id?',['From received JSON','From a query parameter','From the receipt filename','From the authenticated request principal'],3,'The input schema rejects owner_id and the server supplies ownership to the save operation.'),
('Is an in-memory duplicate lookup race-safe database uniqueness?',['No; use database constraints and transactions for concurrent enforcement','Yes, on every server','Only with JSON','Only for numeric amounts'],0,'Another writer can act between lookup and publication. Local teaching state is not production concurrency control.'),
('What should a public API do with arbitrary internal exception text?',['Return it to every caller','Use a fixed public failure shape and a separate diagnostic policy','Return status 200','Treat it as a receipt amount'],1,'Error shape/status can be public while internal diagnostic content requires its own handling.'),
('What does direct pivot require for each index/column pair?',['Every value is zero','Only string amounts','A unique pair unless an explicit aggregation step is chosen','A SQL database'],2,'Duplicate pairs are a domain aggregation question, not just a reshape detail.'),
('What can categorical conversion do to an unknown label?',['Authorize it','Assign a durable business ID','Repair the spelling','Turn it into missing unless validation rejects it first'],3,'Unknown and missing states should not be conflated by an unchecked conversion.'),
('What does a fixed bootstrap seed establish?',['Reproducibility in the selected tested algorithm/environment','A representative dataset','Causality','Guaranteed interval coverage for every population'],0,'A seed does not repair biased input or dependence among observations.'),
]),
}
for slug,(title,refs,questions) in APPLIED_BANKS.items():
 BANKS[slug]=(title,questions)
 path='quizzes/'+slug
 entry=copy.deepcopy(lookup['quizzes/python-basics'])
 entry.update(id=str(uuid.uuid5(uuid.NAMESPACE_URL,'https://aitrove.in/'+path)),path=path,title=title,summary='Twelve explained questions on '+title.lower().replace(' quiz','')+'.',tags=['python','quiz'],sort_order=400+len(added),published_at=stamp,updated_at=stamp)
 entry['body']=para('A Python self-check tests a selected operation contract through twelve questions with explanations.')+'<h2>Review the related lessons</h2><ul>'+''.join('<li><a href="/'+p+'">'+html.escape(lookup[p]['title'])+'</a></li>' for p in refs)+'</ul><h3>Common Mistakes</h3>'+para('A correct local answer is not a deployment guarantee. Read the input, ownership and failure clauses before adapting the program. Results stay in this browser.')
 entry['data']['questions']=[{'prompt':prompt,'options':options,'answer':answer,'explanation':explanation} for prompt,options,answer,explanation in questions]
 entry['data']['related']=[{'path':p,'title':lookup[p]['title']} for p in refs]
 upsert(entry);added.append(path)

APPLIED_REVERSE={
'python/setup-interpreter':['keywords-identifiers','runtime-compatibility'],
'python/python-functions':['first-class-functions'],
'python/unittest-contracts':['refactor-contract-tests','mutation-testing'],
'python/modules':['import-failures','plugin-project'],
'python/memoryview-buffers':['typed-arrays'],
'python/dictionaries':['ordered-dictionaries','reconciliation-exercise'],
'python/generators':['itertools-pipelines','async-generator-cleanup'],
'python/mro-super':['subclass-hooks'],
'python/metaclass-registry':['subclass-hooks','plugin-project'],
'python/type-hints':['typing-narrowing','typing-reference','runtime-compatibility'],
'python/avl-insertion':['avl-deletion'],
'python/bst-deletion':['avl-deletion'],
'python/topological-sort':['strongly-connected-components'],
'python/graph-bfs':['graph-bridges','strongly-connected-components'],
'python/trie-prefix':['compressed-trie'],
'python/trie-deletion':['compressed-trie'],
'python/sliding-window':['longest-palindrome'],
'python/json-validation':['bounded-json-lines'],
'python/csv-import':['bounded-json-lines'],
'python/sqlite-transactions':['sqlite-writer-contention','outbox-project','database-snapshot-interview'],
'python/idempotent-jobs':['outbox-project'],
'python/pathlib-files':['zip-member-validation'],
'python/functools-cache':['lru-project'],
'python/ordered-dictionaries':['lru-project'],
'python/pyproject-config':['wheel-installation','editable-installation'],
'python/package-resources':['wheel-installation'],
'python/pandas-groupby':['pandas-pivot'],
'python/pandas-nullable':['pandas-categorical'],
'python/numpy-precision':['bootstrap-means'],
'python/coverage-branches':['mutation-testing'],
'python/drf-object-permissions':['drf-list-visibility','drf-creation-ownership'],
'python/drf-serializers':['drf-creation-ownership'],
'python/flask-json-api':['flask-error-boundaries'],
'python/log-redaction':['flask-error-boundaries'],
'python/aggregation-exercise':['reconciliation-exercise'],
}
for original,slugs in APPLIED_REVERSE.items():
 assert original in lookup, original
 targets=['python/'+slug for slug in slugs]
 assert all(target in lookup for target in targets),targets
 entry=lookup[original];marker='<h2>Check the next state boundary</h2>'
 entry['body']=entry['body'].split(marker)[0]+marker+para(', '.join('[['+p+'|'+lookup[p]['title']+']]' for p in targets)+'.')
 known={item['path'] for item in entry['data'].get('related',[])}
 entry['data'].setdefault('related',[]).extend({'path':p,'title':lookup[p]['title']} for p in targets if p not in known)
