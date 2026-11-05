"""Fourth Python pass: broader core, practice and ecosystem contracts."""
lesson('input-output','Python input and output: separate parsing from terminal I/O',
'Python input reads a text line, while print writes formatted text; neither establishes the domain meaning of that text.',
'The receipt parser receives a stream rather than reading the process terminal directly. It accepts one newline-terminated ASCII quantity with at most two digits and returns an integer in the declared range. The output stream belongs to the caller, so the operation writes its accepted quantity without closing either stream. In-memory streams let the same operation be tested without an interactive prompt.',
'EOF and a blank line differ. Readline returns an empty string at EOF but returns a newline for an empty entered line. A bounded read detects oversized or unterminated input instead of consuming an arbitrary line. This protocol intentionally rejects surrounding spaces and signs; accepting those would be a different wire contract. [[python/type-conversion|Conversion]] and [[python/input-exercise|Input validation]] keep the parser separate from user-interface behavior.',
r'''from io import StringIO
import re

def read_quantity(source, output):
    line = source.readline(5)
    if line == "":
        raise EOFError("quantity input ended")
    if re.fullmatch(r"[0-9]{1,2}\n", line) is None:
        raise ValueError("quantity line rejected")
    quantity = int(line[:-1])
    if not 1 <= quantity <= 20:
        raise ValueError("quantity range rejected")
    print(f"accepted quantity: {quantity}", file=output)
    return quantity

source, output = StringIO("3\n"), StringIO()
print(read_quantity(source, output))
print(output.getvalue().strip())
for text in ("", "\n", "123456\n"):
    try:
        read_quantity(StringIO(text), StringIO())
    except (EOFError, ValueError) as failure:
        print(type(failure).__name__)''','3\naccepted quantity: 3\nEOFError\nValueError\nValueError',
'The five-character read bounds this operation’s text work. It does not drain rejected input for a later prompt; a caller that continues on the same terminal must choose a recovery policy. Stream reception and blocking latency are external to this parser.',
['EOF is not a blank entered line.','Do not close a caller-owned stream after writing one result.'],['python/type-conversion','python/input-exercise','python/pytest-fixtures'])

lesson('truthiness','Python truth values: distinguish missing data from valid zero',
'Python truth testing asks an object for a boolean interpretation; it does not distinguish every domain state that evaluates as false.',
'The discount record permits an explicit zero and uses None for an unspecified amount. Choosing a default with or replaces both states, so it loses the valid zero. An explicit None check preserves the difference. And and or also return selected operands rather than always returning bool values, which matters when their result is later serialized.',
'Empty collections, zero and None can all be false without being interchangeable. Custom __bool__ or __len__ implementations may perform work or raise. NumPy arrays also require an explicit all/any policy instead of treating an arbitrary array as one boolean. [[python/numpy-precision|Array checks]] and [[python/json-validation|Field contracts]] expose those boundaries.',
r'''def effective_discount(discount):
    if discount is None:
        return 25
    if type(discount) is not int or discount < 0:
        raise ValueError("discount rejected")
    return discount

print("or default:", 0 or 25)
print("explicit zero:", effective_discount(0))
print("missing default:", effective_discount(None))
print("selected operand:", "DEL" and "accepted")
try:
    effective_discount(False)
except ValueError:
    print("boolean amount rejected")''','or default: 25\nexplicit zero: 0\nmissing default: 25\nselected operand: accepted\nboolean amount rejected',
'Testing these built-in scalars has bounded work. A custom truth method can have arbitrary application cost. Short-circuiting skips the second expression only when the first already determines the selected operand.',
['Do not use or defaults when zero or an empty value is meaningful.','And and or return operands, not necessarily boolean values.'],['python/control-flow','python/json-validation','python/numpy-precision'])

lesson('type-conversion','Python type conversion: parsing success is not field validity',
'Python conversion functions construct a selected representation from an accepted input, but their accepted forms can exceed an application’s wire grammar.',
'The quantity protocol permits one to three ASCII digits and a maximum of 200. It validates that text before calling int. Built-in int would also accept forms such as surrounding whitespace and a sign, which this wire field rejects. Converting a float to int truncates toward zero rather than checking that the original number was an exact integer.',
'The parser rejects boolean objects, nontext input and non-ASCII decimal characters. Decimal amounts and timestamps need their own grammar and rounding or timezone policies. Catching every conversion failure as zero would conceal rejected input. [[python/decimal-money|Money representation]] and [[python/datetime-boundaries|Time parsing]] keep those contracts separate.',
r'''import re

def parse_quantity(text):
    if not isinstance(text, str) or re.fullmatch(r"[0-9]{1,3}", text) is None:
        raise ValueError("quantity grammar rejected")
    quantity = int(text)
    if quantity > 200:
        raise ValueError("quantity budget exceeded")
    return quantity

print(parse_quantity("125"))
print("builtin accepts sign:", int(" +3 "))
print("float truncation:", int(-3.8))
for text in ("+3", " 3", "３", True, "201"):
    try:
        parse_quantity(text)
    except ValueError:
        print("rejected")''','125\nbuiltin accepts sign: 3\nfloat truncation: -3\nrejected\nrejected\nrejected\nrejected\nrejected',
'This grammar bounds text to three characters, so validation and conversion perform bounded work. Large integer text needs a reception budget and interpreter-specific digit-limit awareness before conversion. A numeric type annotation performs none of these runtime checks.',
['Check the declared grammar before converting.','Truncation is not proof that a received float represented an integer.'],['python/input-output','python/decimal-money','python/type-hints'])

lesson('loop-control','Python break, continue and loop else: encode the stopping condition',
'Break exits its innermost loop, continue skips to that loop’s next iteration, and loop else runs when the loop finishes without break.',
'The review scan skips inactive receipts and stops when it finds the first active overdue record. If no such record exists, its for-else branch returns None. The two paths distinguish a found match from normal exhaustion without retaining an extra flag. Input ordering determines which match is returned.',
'An exception or return also prevents the else suite from running; else does not mean that every iteration succeeded. Break affects only the nearest loop. A while retry loop needs a bounded attempt count and an explicit exception policy rather than an open-ended condition. [[python/exceptions|Failure handling]] and [[python/generators|Deferred iteration]] show other ways iteration can stop.',
r'''def first_overdue(receipts):
    for receipt in receipts:
        if not receipt["active"]:
            continue
        if receipt["days_late"] > 0:
            matched = receipt["receipt_id"]
            break
    else:
        return None
    return matched

receipts = [{"receipt_id": "R-0041", "active": False, "days_late": 4},
            {"receipt_id": "R-0042", "active": True, "days_late": 2}]
print(first_overdue(receipts))
print(first_overdue([]))
attempts = 0
while attempts < 3:
    attempts += 1
print("bounded attempts:", attempts)''','R-0042\nNone\nbounded attempts: 3',
'The scan takes O(n) in the no-match case and O(1) extra state. This fixture assumes accepted record fields; it is not a record validator. If input is an unbounded iterator, a no-match scan can fail to terminate unless another budget is supplied.',
['Loop else means no break, not no exception.','A break inside nested loops exits only its own loop.'],['python/control-flow','python/exceptions','python/generators'])

lesson('range-enumerate','Python range and enumerate: indexes are not stable record identities',
'Range represents an arithmetic progression, while enumerate pairs iteration results with a running position.',
'The batch labels use a one-based presentation index alongside an unchanged receipt identifier. Range supplies selected positions without allocating a list of every number. An empty range is valid. Its stop is exclusive, and a zero step is invalid. These rules support bounded loop work when the selected input itself is bounded.',
'An index can shift after insertion, deletion or filtering. Do not use it as a durable receipt ID. Enumerate consumes its iterable lazily and does not freeze referenced records. A range’s compact representation does not make iterating a billion positions cheap. [[python/slicing|Slice bounds]] and [[python/python-variables|Object aliases]] distinguish representation from work and ownership.',
r'''receipt_ids = ["R-0041", "R-0042"]
print(list(enumerate(receipt_ids, start=1)))
print(list(range(2, 9, 3)))
print(list(range(4, 4)))
try:
    range(1, 4, 0)
except ValueError:
    print("zero step rejected")''',"[(1, 'R-0041'), (2, 'R-0042')]\n[2, 5, 8]\n[]\nzero step rejected",
'A range stores a bounded number of integer parameters, excluding their digit storage. Enumerate retains iterator/counter state rather than duplicating n entries. Materializing either result takes O(n) retained entries and iteration work.',
['The stop endpoint is excluded.','A display position is not a stable identity for a stored record.'],['python/slicing','python/python-variables','python/iterator-protocol'])

lesson('lambda-functions','Python lambda functions: one expression and the same closure rules',
'A lambda creates a function from one expression and captures enclosing names under the same binding rules as other nested functions.',
'The dispatch sort key selects priority and then receipt ID so tied priorities have an explicit presentation order. Sorting produces a separate outer list. The callback list binds the current receipt ID as a default argument; otherwise later calls would read the loop name’s final binding. Lambda changes the syntax, not the ownership model.',
'A key function should not mutate the collection being sorted. A captured mutable object remains shared even when its reference was bound through a default. Multi-step validation, logging and failure handling are easier to review in a named function than in a crowded expression. [[python/scope-bindings|Late binding]] and [[python/sorting|Sort contracts]] supply the underlying behavior.',
r'''receipts = [(2, "R-0042"), (1, "R-0041"), (2, "R-0040")]
ordered = sorted(receipts, key=lambda receipt: (receipt[0], receipt[1]))
print(ordered)
callbacks = [lambda receipt_id=receipt_id: receipt_id for receipt_id in ("R-0041", "R-0042")]
print([callback() for callback in callbacks])
print("input unchanged:", receipts[0] == (2, "R-0042"))''',"[(1, 'R-0041'), (2, 'R-0040'), (2, 'R-0042')]\n['R-0041', 'R-0042']\ninput unchanged: True",
'Sorting n entries has O(n log n) worst-case comparison work and O(n) auxiliary storage in this use. Key construction adds its own per-entry work. Creating n callbacks retains O(n) functions/default references.',
['Lambda does not freeze every captured value.','Use a named function when an expression hides several domain decisions.'],['python/scope-bindings','python/function-arguments','python/sorting'])

lesson('map-filter-reduce','Python map, filter and reduce: iterator timing and reduction identity',
'Map transforms iteration results, filter selects them, and reduce folds values into one accumulator.',
'The review pipeline filters positive adjustment amounts, maps them into labeled records, then materializes the result once. The deferred operations do not run when map and filter are constructed; their source list is read during consumption. Reduce sums an empty amount sequence using an explicit zero initializer, which defines its identity case.',
'An exhausted iterator does not replay its results. Mutating a source before consuming it can change the answer. For simple transformations, a comprehension can make selection and mapping easier to inspect. A reduction callback also needs an accumulator type and error policy; [[python/comprehensions|Eager results]] and [[python/iterator-interview|Execution timing]] expose those decisions.',
r'''from functools import reduce

adjustments = [125, -25, 75]
selected = filter(lambda amount: amount > 0, adjustments)
labeled = map(lambda amount: f"accepted:{amount}", selected)
adjustments.append(50)
print(list(labeled))
print(list(labeled))
print("empty total:", reduce(lambda total, amount: total + amount, [], 0))''',"['accepted:125', 'accepted:75', 'accepted:50']\n[]\nempty total: 0",
'Constructing these lazy wrappers retains small iterator state; consuming n entries costs the predicates/transforms over those entries. Materializing accepted results uses O(k) storage for k selected records. A growing accumulator can add numeric or allocation costs.',
['Constructing map does not snapshot its input.','Supply a reduction initializer when an empty input is valid.'],['python/comprehensions','python/iterator-interview','python/generators'])

lesson('method-binding','Python staticmethod and classmethod: choose the bound receiver',
'An instance method binds an instance, a classmethod binds the selected class, and a staticmethod receives neither implicitly.',
'The receipt class uses a classmethod constructor so a subclass receives its own class as the constructor target. A static validator operates only on its explicit quantity argument. An instance method calculates cost from that receipt’s state. These three responsibilities need different receivers rather than one universal utility method.',
'A classmethod constructor can violate a subclass invariant if the base assumes every subclass accepts the same constructor signature. Staticmethod does not restrict access to global state or guarantee purity. Binding behavior comes from descriptors, so assigning functions and reading them through an instance is not always equivalent to reading the class dictionary directly. [[python/descriptors|Descriptor lookup]] and [[python/mro-super|Cooperative inheritance]] explain those mechanics.',
r'''class Receipt:
    def __init__(self, quantity):
        self.quantity = self.validate_quantity(quantity)
    @staticmethod
    def validate_quantity(quantity):
        if type(quantity) is not int or not 1 <= quantity <= 20:
            raise ValueError("quantity rejected")
        return quantity
    @classmethod
    def from_quantity(cls, quantity):
        return cls(quantity)
    def amount(self, unit_minor):
        return self.quantity * unit_minor

class ExpressReceipt(Receipt):
    pass

receipt = ExpressReceipt.from_quantity(3)
print(type(receipt).__name__)
print(receipt.amount(125))
print(Receipt.validate_quantity(2))''','ExpressReceipt\n375\n2',
'Receiver binding has small bookkeeping cost relative to the method body. The fixture’s validation is bounded; constructing a record retains its fields. It does not claim that static methods make an application faster than free functions.',
['A classmethod constructor receives the subclass when called on it.','Staticmethod supplies no purity or thread-safety guarantee.'],['python/classes','python/descriptors','python/mro-super'])

group('python','Input, iteration and function tools',['input-output','truthiness','type-conversion','loop-control','range-enumerate','lambda-functions','map-filter-reduce','method-binding'])

lesson('defaultdict-grouping','Python defaultdict: missing-key reads can create state',
'Defaultdict calls its default factory for a missing subscript lookup and stores the resulting value under that key.',
'The batch groups accepted receipt IDs by region using a list factory. Calling get for an unknown region does not invoke the factory, while indexing that region creates an empty group. The fixture makes both behaviors visible because a supposedly read-only inspection can otherwise change exported group keys.',
'The factory must produce independent mutable containers. Reusing one shared list would couple unrelated groups. This helper assumes records have already been validated; grouping is not a schema or authorization check. [[python/dictionaries|Mapping operations]] and [[python/aggregation-exercise|Group validation]] cover those boundaries.',
r'''from collections import defaultdict

groups = defaultdict(list)
for region, receipt_id in [("DEL", "R-0041"), ("BOM", "R-0042"), ("DEL", "R-0043")]:
    groups[region].append(receipt_id)
print(dict(groups))
print(groups.get("BLR"))
print("BLR" in groups)
print(groups["BLR"])
print("BLR" in groups)''',"{'DEL': ['R-0041', 'R-0043'], 'BOM': ['R-0042']}\nNone\nFalse\n[]\nTrue",
'Grouping n accepted records takes expected O(n) mapping operations and O(n+g) references for g groups. A missing-key factory can perform arbitrary work; the list factory here creates one empty container.',
['Get and missing subscript lookup have different mutation behavior.','Return a fresh mutable value from each factory call.'],['python/dictionaries','python/copy-deepcopy','python/aggregation-exercise'],subject='python-types')

lesson('namedtuple-records','Python namedtuple records: immutable fields can still hold mutable objects',
'A namedtuple gives tuple positions named attributes without turning every referenced field value into an immutable object.',
'The receipt summary has a stable identifier and an immutable tuple of tags. Replacing its identifier returns a new record while retaining the old one. A second record intentionally contains a list to show that field assignment is blocked but the referenced list remains mutable. The type’s storage contract is distinct from a validated domain schema.',
'Field type annotations or names do not validate values during construction. A namedtuple can be hashable only when its contents are hashable, and extending or changing positional fields can break callers that unpack it. [[python/dataclasses|Record policy]] and [[python/hash-equality|Stable keys]] cover alternatives and key requirements.',
r'''from collections import namedtuple

ReceiptSummary = namedtuple("ReceiptSummary", "receipt_id tags")
original = ReceiptSummary("R-0041", ("checked",))
updated = original._replace(receipt_id="R-0042")
print(original.receipt_id, updated.receipt_id)
mutable = ReceiptSummary("R-0043", [])
mutable.tags.append("packed")
print(mutable.tags)
try:
    mutable.receipt_id = "R-0044"
except AttributeError:
    print("field assignment rejected")''',"R-0041 R-0042\n['packed']\nfield assignment rejected",
'Replacing a k-field record creates a new outer tuple with O(k) reference work. Referenced objects are shared rather than recursively copied. For a fixed record shape, k is small; retaining many records still costs per-record storage.',
['Immutable outer fields do not freeze a contained list.','Construction does not enforce a business schema.'],['python/tuples','python/dataclasses','python/hash-equality'],subject='python-types')

lesson('bisect-insertion','Python bisect: binary position search does not make list insertion logarithmic',
'Bisect finds a boundary in an already sorted sequence, allowing a caller to choose where equal values belong.',
'The receipt amount list is ascending. Bisect_left finds the first position for an equal amount, while bisect_right finds the position after all equal amounts. Inserting at the right boundary retains the ordering. The fixture uses immutable integer values and an owned list so comparisons and mutation have a clear boundary.',
'Bisect does not sort or validate an arbitrary input. A concurrent mutation can invalidate the selected position between search and insertion. Expensive keys may be recomputed, and comparisons need a coherent ordering policy. [[python/binary-search|Boundary invariants]] and [[python/sorting|Sort ownership]] explain the prerequisite rather than assuming every list qualifies.',
r'''from bisect import bisect_left, bisect_right, insort_right

amounts = [75, 125, 125, 250]
print(bisect_left(amounts, 125), bisect_right(amounts, 125))
insort_right(amounts, 125)
print(amounts)
print("outside upper boundary:", bisect_right(amounts, 500))''','1 3\n[75, 125, 125, 125, 250]\noutside upper boundary: 5',
'Position search makes O(log n) comparisons. Inserting into a Python list can shift O(n) references, so insort has linear overall work in the worst case. Repeated insertion is not an O(n log n) substitute for one bulk sort.',
['Keep the sequence sorted before searching it.','Separate binary search cost from list shifting cost.'],['python/binary-search','python/sorting','python/segment-tree'],subject='python-types')

group('python-types','Factories, record shapes and sorted positions',['defaultdict-grouping','namedtuple-records','bisect-insertion'])
lesson('metaclass-registry','Python metaclasses: validate a class before registering its wire format',
'A metaclass constructs class objects and can enforce a class-level contract before publishing a class into a registry.',
'The codec registry requires a unique nonempty wire name and a decode function on each concrete class. Validation and type construction finish before the registry is updated. A duplicate declaration raises without replacing the previously accepted codec. The base class deliberately has no wire name and is not registered.',
'This is a local class registry, not automatic loading of received plugin paths. Metaclass conflicts can arise with multiple bases, and another hook can have its own side effects. Preserve the class namespace when passing it to type.__new__, including compiler-provided cells. For many simple subclass checks, __init_subclass__ is sufficient; [[python/abstract-classes|Abstract interfaces]] and [[python/mro-super|Class ordering]] cover other mechanisms.',
r'''CODECS = {}
class CodecMeta(type):
    def __new__(metaclass, name, bases, namespace, **options):
        wire_name = namespace.get("wire_name")
        if wire_name is not None:
            if not isinstance(wire_name, str) or not wire_name or wire_name in CODECS:
                raise ValueError("wire name rejected")
            if not callable(namespace.get("decode")):
                raise ValueError("decode function required")
        created = super().__new__(metaclass, name, bases, namespace, **options)
        if wire_name is not None:
            CODECS[wire_name] = created
        return created

class ReceiptCodec(metaclass=CodecMeta):
    wire_name = None

class ReceiptJson(ReceiptCodec):
    wire_name = "receipt-json"
    def decode(payload):
        return payload["receipt_id"]

print(CODECS["receipt-json"].decode({"receipt_id": "R-0041"}))
try:
    class DuplicateReceipt(ReceiptCodec):
        wire_name = "receipt-json"
        def decode(payload):
            return payload
except ValueError:
    print("duplicate class rejected")
print(CODECS["receipt-json"] is ReceiptJson)''','R-0041\nduplicate class rejected\nTrue',
'Class construction performs validation once per declaration and retains the accepted class in the registry. The registry therefore owns its classes until removed. This fixture has no weak retention or plugin unload policy.',
['Do not publish a registry entry before class construction succeeds.','A metaclass does not make received plugin code safe to execute.'],['python/abstract-classes','python/mro-super','python/weak-references'],subject='python-advanced')

lesson('abstract-classes','Python ABC: prevent construction of an incomplete implementation',
'An abstract base class marks required methods so a subclass with unresolved abstract methods cannot be instantiated.',
'The writer interface requires a publish method. An incomplete subclass fails during construction; the local writer implements the operation and returns a receipt identifier. The abstract requirement checks that an implementation exists, not that every accepted input or returned value satisfies the caller’s domain contract.',
'Abstract registration and structural Protocol annotations serve different purposes. A concrete override can still have an incompatible signature or wrong behavior at runtime. Test the collaborator’s accepted values and failures separately; [[python/typing-protocol|Static interfaces]] and [[python/mock-failures|Failure tests]] address those obligations.',
r'''from abc import ABC, abstractmethod

class ReceiptWriter(ABC):
    @abstractmethod
    def publish(self, receipt):
        raise NotImplementedError

class MissingWriter(ReceiptWriter):
    pass

class LocalReceiptWriter(ReceiptWriter):
    def publish(self, receipt):
        return receipt["receipt_id"]

try:
    MissingWriter()
except TypeError:
    print("incomplete writer rejected")
print(LocalReceiptWriter().publish({"receipt_id": "R-0041"}))''','incomplete writer rejected\nR-0041',
'Abstract method bookkeeping happens during class construction and instantiation checks. Actual method cost is implementation-dependent. The fixture performs no storage publication despite its interface name; its writer returns a local value only.',
['A concrete override is not proof of behavioral compatibility.','Do not confuse an ABC with payload validation.'],['python/typing-protocol','python/mock-failures','python/metaclass-registry'],subject='python-advanced')

lesson('exception-groups','Python ExceptionGroup: handle selected failures and retain the rest',
'ExceptionGroup carries multiple related exception objects, and except* selects matching leaves while retaining unmatched failures.',
'The import has a value failure and an I/O failure. An except* ValueError handler records the value failure, while the remaining OSError is re-raised in a group and caught at the surrounding boundary. This makes partial handling visible instead of flattening every failure into a success message.',
'Except* can run several matching clauses for one raised group. It is not the same as choosing one ordinary except clause, and return, break and continue are not permitted inside its handler suites. Do not include KeyboardInterrupt or SystemExit in an ordinary ExceptionGroup; BaseExceptionGroup has a broader role. [[python/async-task-groups|Concurrent failures]] and [[python/exceptions|Exception chaining]] explain where grouped errors arise.',
r'''handled = []
try:
    try:
        raise ExceptionGroup("receipt import failures", [ValueError("quantity"), OSError("input file")])
    except* ValueError as selected:
        handled.extend(type(failure).__name__ for failure in selected.exceptions)
except ExceptionGroup as remaining:
    print("remaining:", [type(failure).__name__ for failure in remaining.exceptions])
print("handled:", handled)''',"remaining: ['OSError']\nhandled: ['ValueError']",
'Matching a group inspects its exception structure and constructs selected/unmatched group views. Work scales with the contained tree, not just the number of handler clauses. Retained tracebacks can keep referenced state alive.',
['A partial handler must not hide unmatched failures.','Except* is not ordinary single-branch exception selection.'],['python/async-task-groups','python/exceptions','python/exceptions-interview'],subject='python-advanced')

lesson('context-variables','Python ContextVar: task-local labels without sharing one global binding',
'ContextVar stores a value in the current execution context, allowing tasks to change their binding without overwriting a sibling task’s binding.',
'The parent supplies an import label before creating two tasks. Each task receives that context and temporarily binds its own receipt label. After an explicit scheduling yield, each still sees its own value. Resetting its token restores the previous binding, and the parent label remains unchanged after both tasks finish.',
'Context copying copies bindings, not an independent deep graph of every bound object. Binding one mutable dictionary can still expose shared mutation across tasks. Context propagation into thread/process boundaries also depends on the API used. [[python/async-task-groups|Task lifetime]] and [[python/copy-deepcopy|Reference ownership]] explain why task-local names alone do not isolate all state.',
r'''import asyncio
from contextvars import ContextVar

receipt_context = ContextVar("receipt_context", default="unassigned")
async def inspect_receipt(receipt_id):
    token = receipt_context.set(receipt_id)
    try:
        await asyncio.sleep(0)
        return receipt_context.get()
    finally:
        receipt_context.reset(token)

async def inspect_batch():
    token = receipt_context.set("batch-DEL")
    try:
        print(await asyncio.gather(inspect_receipt("R-0041"), inspect_receipt("R-0042")))
        print("parent:", receipt_context.get())
    finally:
        receipt_context.reset(token)

asyncio.run(inspect_batch())
print("outside:", receipt_context.get())''',"['R-0041', 'R-0042']\nparent: batch-DEL\noutside: unassigned",
'Context bindings add per-context state while referenced objects retain their own memory costs. This fixture schedules no network or external work. The scheduling yield tests binding separation rather than latency or parallel CPU execution.',
['Reset a temporary binding using the token returned by set.','A context-local reference can still point to a shared mutable object.'],['python/async-task-groups','python/copy-deepcopy','python/logging-context'],subject='python-advanced')

lesson('functools-cache','Python lru_cache: bound retention and include the revision in the key',
'Lru_cache stores recent function results under hashable argument keys and evicts older entries when its configured capacity is exceeded.',
'The price lookup includes both the receipt class and price revision in its key. A repeated revision-one lookup reuses the stored result, while revision two gets its own value. Inspecting cache_info makes retained entry count and reuse visible. Clearing the cache releases its retained key/result references.',
'The cache does not discover that an external price source changed. Omitting revision or another invalidation rule can return stale prices. It also retains returned mutable objects and does not guarantee that a concurrently missed call executes only once. [[python/hash-equality|Stable keys]] and [[python/idempotent-jobs|Request identity]] distinguish caching from publication coordination.',
r'''from functools import lru_cache

PRICES = {("standard", 1): 125, ("standard", 2): 150}
@lru_cache(maxsize=2)
def unit_price(receipt_class, revision):
    return PRICES[(receipt_class, revision)]

print(unit_price("standard", 1))
print(unit_price("standard", 1))
print(unit_price("standard", 2))
info = unit_price.cache_info()
print("hits:", info.hits, "retained:", info.currsize)
unit_price.cache_clear()
print("after clear:", unit_price.cache_info().currsize)''','125\n125\n150\nhits: 1 retained: 2\nafter clear: 0',
'For k retained entries, the cache owns O(k) key/result references plus their reachable state. A hit avoids the function body but still computes argument-key hashes. Unbounded caches can retain every distinct key; this fixture deliberately uses a capacity.',
['Cache retention is not a freshness policy.','A cached mutable result remains shared among callers.'],['python/hash-equality','python/memoization','python/idempotent-jobs'],subject='python-advanced')

group('python-advanced','Class construction, grouped failures and execution context',['metaclass-registry','abstract-classes','exception-groups','context-variables','functools-cache'])
lesson('avl-insertion','Python AVL insertion: rotate while preserving ordered keys and heights',
'An AVL tree keeps each node’s two subtree heights within one level so search paths remain logarithmic in the retained key count.',
'The receipt index stores bounded unique integer keys. Duplicate insertion leaves its logical key set unchanged. Each recursive insertion updates height before testing balance, and single or paired rotations restore the local invariant. The wrapper retains the returned root because a rotation can replace the tree’s entrypoint.',
'This fixture implements insertion only. Deletion needs its own rebalance path, and arbitrary externally edited nodes are outside the owned-tree contract. The index rejects a new key after its 128-key budget before changing nodes; a duplicate remains allowed. [[python/bst-deletion|Unbalanced deletion]] and [[python/tree-traversal|Traversal checks]] explain related but distinct operations.',
r'''from dataclasses import dataclass

@dataclass
class IndexNode:
    key: int
    left: "IndexNode | None" = None
    right: "IndexNode | None" = None
    height: int = 1

def height(node):
    return node.height if node else 0

def refresh(node):
    node.height = 1 + max(height(node.left), height(node.right))

def rotate_right(node):
    replacement = node.left
    node.left = replacement.right
    replacement.right = node
    refresh(node); refresh(replacement)
    return replacement

def rotate_left(node):
    replacement = node.right
    node.right = replacement.left
    replacement.left = node
    refresh(node); refresh(replacement)
    return replacement

def insert_key(node, key):
    if node is None:
        return IndexNode(key)
    if key < node.key:
        node.left = insert_key(node.left, key)
    elif key > node.key:
        node.right = insert_key(node.right, key)
    else:
        return node
    refresh(node)
    balance = height(node.left) - height(node.right)
    if balance > 1:
        if key > node.left.key:
            node.left = rotate_left(node.left)
        return rotate_right(node)
    if balance < -1:
        if key < node.right.key:
            node.right = rotate_right(node.right)
        return rotate_left(node)
    return node

class ReceiptIndex:
    def __init__(self):
        self.root = None
        self.keys = set()
    def add(self, key):
        if type(key) is not int or (key not in self.keys and len(self.keys) >= 128):
            raise ValueError("index key budget rejected")
        self.root = insert_key(self.root, key)
        self.keys.add(key)

index = ReceiptIndex()
for key in (10, 20, 30, 40, 50):
    index.add(key)
print("root:", index.root.key)
print("height:", index.root.height)
index.add(30)
print("unique keys:", len(index.keys))''','root: 20\nheight: 3\nunique keys: 5',
'Accepted insertion takes O(log n) tree traversal and stack depth while AVL invariants hold. Rotations change a bounded number of links, and height refresh uses retained child heights. The wrapper’s key set and nodes retain O(n) state; integer comparison/hash costs depend on digit size.',
['Refresh heights in child-before-parent order after a rotation.','A logarithmic-height claim requires checking the balance invariant after updates.'],['python/bst-deletion','python/tree-traversal','python/bisect-insertion'],subject='python-dsa')

lesson('trie-deletion','Python trie deletion: remove one word without losing its prefix neighbors',
'Trie deletion removes a word’s terminal marker and prunes only branches that no longer lead to any retained word.',
'The route-label trie stores bounded uppercase ASCII words. Removing DEL unmarks its terminal node but preserves DELHI beneath it. Removing the last descendant later can prune that branch completely. A missing word returns false and leaves the trie unchanged. The caller owns the constructed trie; received arbitrary nested dictionaries are not accepted tree input.',
'A prefix can be a complete word and an ancestor of another word at the same time. Deleting every visited node would lose valid neighbors. This fixture has no concurrent readers or compressed edges. [[python/trie-prefix|Prefix lookup]] and [[python/python-variables|Shared mutation]] explain the ownership and read-side boundaries.',
r'''import re

def valid_word(word):
    return isinstance(word, str) and re.fullmatch(r"[A-Z]{1,32}", word) is not None

def build_routes(words):
    if len(words) > 128 or any(not valid_word(word) for word in words):
        raise ValueError("route word budget rejected")
    root = {"terminal": False, "children": {}}
    for word in words:
        node = root
        for symbol in word:
            node = node["children"].setdefault(symbol, {"terminal": False, "children": {}})
        node["terminal"] = True
    return root

def remove_route(root, word):
    if not valid_word(word):
        raise ValueError("route word rejected")
    node = root; path = []
    for symbol in word:
        if symbol not in node["children"]:
            return False
        path.append((node, symbol)); node = node["children"][symbol]
    if not node["terminal"]:
        return False
    node["terminal"] = False
    for parent, symbol in reversed(path):
        child = parent["children"][symbol]
        if child["terminal"] or child["children"]:
            break
        del parent["children"][symbol]
    return True

def route_words(root):
    result = []
    def visit(node, prefix):
        if node["terminal"]:
            result.append(prefix)
        for symbol, child in sorted(node["children"].items()):
            visit(child, prefix + symbol)
    visit(root, "")
    return result

routes = build_routes(["DEL", "DELHI", "BOM"])
print(remove_route(routes, "DEL"), route_words(routes))
print(remove_route(routes, "DEL"), route_words(routes))
print(remove_route(routes, "DELHI"), route_words(routes))''',"True ['BOM', 'DELHI']\nFalse ['BOM', 'DELHI']\nTrue ['BOM']",
'Deletion visits at most the word’s L symbols and retains O(L) parent references. Complete ordered listing has output-dependent work, sorting and string-construction costs. The trie retains nodes proportional to stored prefixes, not merely the number of words.',
['A terminal prefix can have valid descendants.','Prune only nonterminal nodes with no retained children.'],['python/trie-prefix','python/python-variables','python/recursion-boundaries'],subject='python-dsa')

lesson('lazy-range-sums','Python lazy segment tree: defer interval additions and retain correct totals',
'A lazy sum tree records a pending interval addition so a covered subtree can update its total without immediately visiting every leaf.',
'The ledger owns bounded integer amounts and uses half-open ranges. Applying a delta to an interval changes its sum by interval length times delta. A partial query or update pushes that pending delta into children before descending. Empty intervals are valid and do no work. Point replacement is a different operation from these interval additions.',
'Pushing changes internal bookkeeping even during a query, so this tree is not a lock-free immutable snapshot. Invalid indexes and boolean deltas are rejected before any tree change. Arbitrarily large integers remain valid but have digit-dependent arithmetic costs. [[python/segment-tree|Point replacement]] and [[python/thread-locks|State coordination]] address the other contracts.',
r'''class RangeAmounts:
    def __init__(self, amounts):
        if not 1 <= len(amounts) <= 128 or any(type(amount) is not int for amount in amounts):
            raise ValueError("bounded integer amounts required")
        self.count = len(amounts)
        self.sums = [0] * (4 * self.count)
        self.lazy = [0] * (4 * self.count)
        def build(position, left, right):
            if right - left == 1:
                self.sums[position] = amounts[left]
                return
            middle = (left + right) // 2
            build(position * 2, left, middle); build(position * 2 + 1, middle, right)
            self.sums[position] = self.sums[position * 2] + self.sums[position * 2 + 1]
        build(1, 0, self.count)
    def _validate(self, left, right):
        if any(type(index) is not int for index in (left, right)) or not 0 <= left <= right <= self.count:
            raise ValueError("invalid half-open interval")
    def _apply(self, position, length, delta):
        self.sums[position] += length * delta
        self.lazy[position] += delta
    def _push(self, position, left, right):
        if self.lazy[position] and right - left > 1:
            middle = (left + right) // 2
            self._apply(position * 2, middle - left, self.lazy[position])
            self._apply(position * 2 + 1, right - middle, self.lazy[position])
            self.lazy[position] = 0
    def add(self, left, right, delta):
        self._validate(left, right)
        if type(delta) is not int:
            raise ValueError("integer delta required")
        def change(position, start, end):
            if right <= start or end <= left:
                return
            if left <= start and end <= right:
                self._apply(position, end - start, delta)
                return
            self._push(position, start, end)
            middle = (start + end) // 2
            change(position * 2, start, middle); change(position * 2 + 1, middle, end)
            self.sums[position] = self.sums[position * 2] + self.sums[position * 2 + 1]
        if left != right:
            change(1, 0, self.count)
    def total(self, left, right):
        self._validate(left, right)
        def query(position, start, end):
            if right <= start or end <= left:
                return 0
            if left <= start and end <= right:
                return self.sums[position]
            self._push(position, start, end)
            middle = (start + end) // 2
            return query(position * 2, start, middle) + query(position * 2 + 1, middle, end)
        return query(1, 0, self.count) if left != right else 0

ledger = RangeAmounts([1, 3, 5, 7])
print(ledger.total(0, 4))
ledger.add(1, 3, 2)
print(ledger.total(0, 4))
print(ledger.total(2, 3))
print(ledger.total(2, 2))''','16\n20\n7\n0',
'Construction uses O(n) time and storage. An accepted interval addition or sum query performs O(log n) tree work under its lazy invariant, with O(log n) recursion depth. It does not provide persistence, concurrent snapshots or crash durability.',
['Scale a covered sum update by interval length.','Push pending state before reading partially covered child totals.'],['python/segment-tree','python/thread-locks','python/range-exercise'],subject='python-dsa')

lesson('edit-script','Python edit scripts: reconstruct and verify an alignment instead of only counting it',
'An edit script records concrete insert, delete and replace operations that transform a source sequence into a target sequence.',
'The bounded label aligner keeps a complete distance matrix, then walks backward under an explicit tie policy: match or replace first, then deletion, then insertion. It returns an ordered script. Applying that script validates consumed source symbols and produces the target label, which checks the reconstruction rather than trusting the distance alone.',
'The operations use code points, not grapheme clusters, and they are not permission to rewrite account identifiers. Several minimum scripts can exist; the chosen tie policy makes this fixture repeatable but does not establish one universally correct human correction. [[python/edit-distance|Rolling-row counts]] uses less storage when only the number is required.',
r'''def align_labels(source, target):
    if not isinstance(source, str) or not isinstance(target, str) or max(len(source), len(target)) > 32:
        raise ValueError("bounded labels required")
    costs = [[0] * (len(target) + 1) for _ in range(len(source) + 1)]
    for row in range(len(source) + 1): costs[row][0] = row
    for column in range(len(target) + 1): costs[0][column] = column
    for row in range(1, len(source) + 1):
        for column in range(1, len(target) + 1):
            costs[row][column] = min(costs[row - 1][column] + 1, costs[row][column - 1] + 1,
                                     costs[row - 1][column - 1] + (source[row - 1] != target[column - 1]))
    row, column = len(source), len(target); reversed_steps = []
    while row or column:
        if row and column and costs[row][column] == costs[row - 1][column - 1] + (source[row - 1] != target[column - 1]):
            kind = "keep" if source[row - 1] == target[column - 1] else "replace"
            reversed_steps.append((kind, source[row - 1], target[column - 1])); row -= 1; column -= 1
        elif row and costs[row][column] == costs[row - 1][column] + 1:
            reversed_steps.append(("delete", source[row - 1], "")); row -= 1
        else:
            reversed_steps.append(("insert", "", target[column - 1])); column -= 1
    return costs[-1][-1], list(reversed(reversed_steps))

def apply_alignment(source, steps):
    position = 0; output = []
    for kind, before, after in steps:
        if kind not in {"keep", "replace", "delete", "insert"}:
            raise ValueError("unknown alignment operation")
        if kind != "insert":
            if position >= len(source) or source[position] != before:
                raise ValueError("alignment source mismatch")
            position += 1
        if kind != "delete": output.append(after)
    if position != len(source):
        raise ValueError("alignment left source unconsumed")
    return "".join(output)

distance, steps = align_labels("DEL", "DILHI")
print("distance:", distance)
print("reconstructed:", apply_alignment("DEL", steps))
print("edited steps:", sum(kind != "keep" for kind, before, after in steps))''','distance: 3\nreconstructed: DILHI\nedited steps: 3',
'For lengths m and n, matrix construction costs O(mn) time and storage; reconstruction adds O(m+n) steps. The shorter rolling-row distance helper saves matrix storage but cannot directly supply this predecessor walk.',
['Verify that applying the returned script consumes the source and yields the target.','A minimum code-point edit is not a domain-approved identifier change.'],['python/edit-distance','python/unicode-normalization','python/longest-common-subsequence'],subject='python-dsa')

group('python-dsa','Balanced indexes, pruning and reconstruction',['avl-insertion','trie-deletion','lazy-range-sums','edit-script'])
lesson('pandas-resample','Pandas resample: choose time-bin boundaries and preserve empty hours',
'Resample groups timestamped observations into time bins whose frequency, closed endpoint and displayed label are configurable.',
'The receipt series uses sorted UTC timestamps and one-hour bins closed and labeled on the left. Two receipts in the first hour sum to 375. The empty next hour remains missing because min_count is one. A zero amount in a populated hour would be a real zero, which is different from no observed receipt.',
'UTC avoids ambiguous local-clock bins in this fixture. Business-day reporting may instead require a named timezone, conversion and an explicit daylight-saving policy. Resampling does not automatically remove duplicate records or establish arrival completeness; [[python/timezone-fold|Repeated local times]] and [[python/pandas-rolling|Observation windows]] cover separate timing problems.',
r'''import pandas as pd

index = pd.to_datetime(["2026-09-01T00:10:00Z", "2026-09-01T00:50:00Z", "2026-09-01T02:10:00Z"])
amounts = pd.Series([125, 250, 75], index=index, dtype="Int64")
if not amounts.index.is_monotonic_increasing or amounts.index.hasnans:
    raise ValueError("ordered timestamps required")
hourly = amounts.resample("1h", closed="left", label="left").sum(min_count=1)
print([timestamp.strftime("%H:%M") for timestamp in hourly.index])
print([None if pd.isna(amount) else int(amount) for amount in hourly])''',"['00:00', '01:00', '02:00']\n[375, None, 75]",
'Result storage depends on the number of generated bins, not only the number of observations. Sparse events separated by a very long time interval can create many empty bins. Bound both input count and reporting horizon in a receiving application.',
['An empty time bin is not a measured zero.','Declare endpoint and timezone policies instead of relying on implicit reporting assumptions.'],['python/pandas-rolling','python/timezone-fold','python/pandas-groupby'],subject='python-data',dependencies=['pandas==3.0.6'])

lesson('pandas-null-joins','Pandas merge with null keys: quarantine missing identifiers before matching',
'Pandas merge can match missing keys on both sides, so missing-key acceptance needs an explicit policy in addition to join cardinality.',
'The unchecked lookup contains one missing region identifier. A raw merge matches a missing receipt region to that lookup row. The accepted lookup contract rejects missing region keys; a cleaned lookup leaves the receipt’s missing region unmatched for review. Many-to-one validation still checks that lookup keys do not multiply receipt rows.',
'Removing a missing lookup key is not permission to discard its source record without a review policy. Missing values and a real empty-string identifier also differ. Keep unmatched receipts available instead of quietly reporting them under a fabricated region. [[python/pandas-joins|Cardinality checks]] and [[python/pandas-groupby|Missing groups]] apply after the identifier policy is chosen.',
r'''import pandas as pd

def attach_regions(receipts, regions):
    if regions["region"].isna().any():
        raise ValueError("lookup region cannot be missing")
    return receipts.merge(regions, on="region", how="left", validate="many_to_one", indicator=True)

receipts = pd.DataFrame({"region": pd.Series(["DEL", None], dtype="string"), "amount": [125, 75]})
unchecked = pd.DataFrame({"region": pd.Series(["DEL", None], dtype="string"), "label": ["Delhi", "unchecked-missing"]})
print("raw null matched:", receipts.merge(unchecked, on="region", how="left")["label"].iloc[1] == "unchecked-missing")
try:
    attach_regions(receipts, unchecked)
except ValueError:
    print("missing lookup key rejected")
accepted = unchecked[unchecked["region"].notna()].copy()
joined = attach_regions(receipts, accepted)
print(joined["_merge"].astype(str).tolist())''',"raw null matched: True\nmissing lookup key rejected\n['both', 'left_only']",
'Join work and retained rows depend on cardinality, key representation and algorithm choice. The many-to-one contract limits output multiplication here but does not cap source bytes or the number of rows. An unmatched row still requires downstream handling.',
['Null keys can match each other in Pandas.','Cardinality validation does not supply a missing-identifier policy.'],['python/pandas-joins','python/pandas-groupby','python/aggregation-exercise'],subject='python-data',dependencies=['pandas==3.0.6'])

lesson('linear-least-squares','NumPy least squares: inspect rank before trusting fitted coefficients',
'Least squares chooses coefficients that minimize squared residual error for a supplied linear design matrix and response vector.',
'The fixture fits an intercept and one feature to an owned exact line, then checks the matrix rank and predictions. A second design with identical columns has deficient rank. The solver can still return coefficients there, but individual coefficient interpretation is not identified by the supplied data. The program reports that distinction instead of treating every numeric return as a valid domain model.',
'The fixture has no generalization estimate, causality claim or noisy measurement model. Floating-point tolerance, feature scaling and ill conditioning need separate policies. Split data before fitting transformations when evaluating predictive behavior; [[python/ml-pipeline|Training boundaries]] and [[python/numpy-precision|Numerical acceptance]] address those layers.',
r'''import numpy as np

feature = np.array([0, 1, 2, 3], dtype=float)
design = np.column_stack([np.ones_like(feature), feature])
observed = np.array([3, 5, 7, 9], dtype=float)
coefficients, residuals, rank, singular = np.linalg.lstsq(design, observed, rcond=None)
print("full rank:", int(rank) == design.shape[1])
print("coefficients:", np.round(coefficients, 6).tolist())
print("fit accepted:", bool(np.allclose(design @ coefficients, observed, rtol=1e-10, atol=1e-10)))
duplicate_columns = np.column_stack([feature, feature])
_, _, deficient_rank, _ = np.linalg.lstsq(duplicate_columns, observed, rcond=None)
print("deficient rank:", int(deficient_rank) < duplicate_columns.shape[1])''','full rank: True\ncoefficients: [3.0, 2.0]\nfit accepted: True\ndeficient rank: True',
'Dense least-squares cost depends on the matrix dimensions and decomposition used. Retaining an n-by-p design already costs O(np) values. Rank thresholds and conditioning matter; a small residual alone does not establish reliable coefficients or future predictions.',
['A deficient design can return numbers without identifying individual effects.','An exact training fit is not an evaluation of unseen records.'],['python/numpy-precision','python/ml-pipeline','python/numpy-broadcasting'],subject='python-data',dependencies=['numpy==2.5.3'])

group('python-data','Time bins, null identifiers and linear models',['pandas-resample','pandas-null-joins','linear-least-squares'])

lesson('hypothesis-properties','Hypothesis property tests: compare generated cases with an independent contract',
'Hypothesis generates test inputs from declared strategies and can shrink a failing input into a smaller reproducible case.',
'The quantity aggregation test compares a streaming accumulator with built-in sum over bounded integer lists. A second property tries values outside the accepted element type/range and requires rejection. The settings use deterministic generation and no example database so the teaching run owns no persistent state. Assertions check behavior rather than a handpicked output alone.',
'Passing generated cases is not a proof over every possible input. A strategy that never produces a relevant boundary cannot find that boundary’s failure. Avoid assuming a counterexample’s exact text or order stays fixed across versions. [[python/pytest-fixtures|Example-based tests]] and [[python/window-exercise|Independent oracles]] complement generated properties.',
r'''from hypothesis import given, settings, strategies as st

def aggregate_quantities(quantities):
    if len(quantities) > 32:
        raise ValueError("batch budget rejected")
    total = 0
    for quantity in quantities:
        if type(quantity) is not int or not 0 <= quantity <= 20:
            raise ValueError("quantity rejected")
        total += quantity
    return total

@settings(max_examples=100, derandomize=True, database=None, deadline=None)
@given(st.lists(st.integers(min_value=0, max_value=20), max_size=32))
def accepted_property(quantities):
    assert aggregate_quantities(quantities) == sum(quantities)

@settings(max_examples=60, derandomize=True, database=None, deadline=None)
@given(st.one_of(st.booleans(), st.integers(max_value=-1), st.integers(min_value=21), st.text(max_size=8)))
def rejected_property(quantity):
    try:
        aggregate_quantities([quantity])
    except ValueError:
        return
    raise AssertionError("rejected field became accepted")

accepted_property()
rejected_property()
print("accepted and rejected properties passed")''','accepted and rejected properties passed',
'Work depends on generated example count, input bounds and any shrinking after a failure. Disabling a deadline avoids noisy wall-clock failures in this fixture; it is not an application timeout policy. Both strategies impose small list/text bounds.',
['A generated test can miss inputs excluded by its strategy.','Use an independent answer or invariant instead of repeating the implementation.'],['python/pytest-fixtures','python/window-exercise','python/aggregation-exercise'],subject='python-testing',dependencies=['hypothesis==6.168.3'])

lesson('coverage-branches','Coverage.py branch coverage: execution paths are not correctness assertions',
'Branch coverage records which possible control-flow destinations were executed, while tests separately decide whether their results were correct.',
'The owned module has one negative-input branch and one accepted return. Tests execute both paths with explicit expected behavior, then coverage.py writes a JSON report. The program checks that no branch destination is missing. Module, report and measurement files all live in one temporary directory, and exact coverage totals are not printed as a portability promise.',
'Full measured branch coverage can still accompany wrong assertions or an incomplete input contract. The fixture is a two-path local function, not coverage of the site or an entire service. Excluded lines and subprocesses also require deliberate configuration. [[python/hypothesis-properties|Generated cases]] and [[python/mock-failures|Collaborator failures]] extend testing beyond one percentage.',
r'''from pathlib import Path
import importlib.util
import json
import tempfile
import coverage

with tempfile.TemporaryDirectory() as directory:
    target = Path(directory) / "quantity_rules.py"
    target.write_text('def accept_quantity(quantity):\n    if quantity < 0:\n        raise ValueError("negative")\n    return quantity\n', encoding="utf-8")
    measured = coverage.Coverage(branch=True, data_file=str(Path(directory) / ".coverage"))
    measured.start()
    try:
        spec = importlib.util.spec_from_file_location("owned_quantity_rules", target)
        module = importlib.util.module_from_spec(spec)
        spec.loader.exec_module(module)
        assert module.accept_quantity(3) == 3
        try:
            module.accept_quantity(-1)
        except ValueError:
            pass
        else:
            raise AssertionError("negative branch did not reject")
    finally:
        measured.stop()
    report = Path(directory) / "coverage.json"
    measured.json_report(outfile=str(report), include=[str(target)])
    details = json.loads(report.read_text(encoding="utf-8"))
    print("missing branches:", details["totals"]["missing_branches"])
print("measurement files owned by temporary directory")''','missing branches: 0\nmeasurement files owned by temporary directory',
'Instrumentation adds execution and recording overhead; this fixture does not benchmark it. Source and control-flow analysis scale with measured code, while retained coverage data scales with recorded locations. A percentage must be interpreted against the actual measured files.',
['Coverage measures execution, not the strength of an assertion.','Do not report a tiny fixture’s percentage as whole-service coverage.'],['python/hypothesis-properties','python/mock-failures','python/pytest-fixtures'],subject='python-testing',dependencies=['coverage==7.16.2'])

group('python-testing','Generated cases and measured branches',['hypothesis-properties','coverage-branches'])
lesson('flask-sqlite-persistence','Flask SQLite application: own the request connection and verify a clean reopen',
'A Flask request-scoped database connection can live in the application context and close when that context ends.',
'The local receipt application stores accepted records in an owned temporary SQLite file. Each request lazily opens one connection through g, uses parameterized statements and closes that connection in teardown. A duplicate receipt returns a conflict after its failed transaction rolls back. A second app instance reads the same file after the first request finishes, verifying clean persistence rather than only an in-memory response.',
'This application has no identity or record authorization and must not be exposed as a public receipt service. JSON parsing can also collapse duplicate object keys before schema checks. Proxy body budgets, competing writers and power-loss recovery require separate tests. [[python/flask-json-api|Request schemas]] and [[python/sqlite-cli-project|Transactional imports]] provide the preceding boundaries.',
r'''from pathlib import Path
import sqlite3
import tempfile
from flask import Flask, g, jsonify, request

def receipt_app(database_path):
    application = Flask(__name__)
    application.config["MAX_CONTENT_LENGTH"] = 1024
    with sqlite3.connect(database_path) as setup:
        setup.execute("CREATE TABLE IF NOT EXISTS receipts (receipt_id TEXT PRIMARY KEY, amount INTEGER NOT NULL CHECK(amount >= 0))")
    setup.close()
    def database():
        if "receipt_database" not in g:
            g.receipt_database = sqlite3.connect(database_path)
        return g.receipt_database
    @application.teardown_appcontext
    def release_database(failure):
        owned = g.pop("receipt_database", None)
        if owned is not None:
            owned.close()
    @application.post("/receipts")
    def store_receipt():
        if not request.is_json:
            return jsonify(error="JSON required"), 415
        import re
        payload = request.get_json()
        if not isinstance(payload, dict) or set(payload) != {"receipt_id", "amount"}:
            return jsonify(error="fields rejected"), 400
        if not isinstance(payload["receipt_id"], str) or re.fullmatch(r"R-[0-9]{4}", payload["receipt_id"]) is None:
            return jsonify(error="identifier rejected"), 400
        if type(payload["amount"]) is not int or not 0 <= payload["amount"] <= 1000000:
            return jsonify(error="amount rejected"), 400
        try:
            with database():
                database().execute("INSERT INTO receipts VALUES (?, ?)", (payload["receipt_id"], payload["amount"]))
        except sqlite3.IntegrityError:
            return jsonify(error="duplicate receipt"), 409
        return jsonify(receipt_id=payload["receipt_id"]), 201
    @application.get("/receipts")
    def list_receipts():
        rows = database().execute("SELECT receipt_id,amount FROM receipts ORDER BY receipt_id LIMIT 20").fetchall()
        return jsonify([{"receipt_id": identifier, "amount": amount} for identifier, amount in rows])
    return application

with tempfile.TemporaryDirectory() as directory:
    path = Path(directory) / "receipts.sqlite3"
    client = receipt_app(path).test_client()
    print("accepted:", client.post("/receipts", json={"receipt_id": "R-0041", "amount": 125}).status_code)
    print("duplicate:", client.post("/receipts", json={"receipt_id": "R-0041", "amount": 250}).status_code)
    reopened = receipt_app(path).test_client()
    print(reopened.get("/receipts").get_json())''',"accepted: 201\nduplicate: 409\n[{'amount': 125, 'receipt_id': 'R-0041'}]",
'The primary-key index supports keyed uniqueness checks with backend-dependent work. The listing caps returned rows but is not complete pagination. The request lifetime bounds connection ownership; contention, disk I/O and crash durability remain deployment-dependent.',
['A connection transaction context does not close that connection automatically.','Persisted receipts still require identity and authorization before a public deployment.'],['python/flask-json-api','python/sqlite-cli-project','python/drf-object-permissions'],subject='python-web',dependencies=['Flask==3.1.3'])

lesson('drf-serializers','Django REST Framework serializers: reject coercion outside the wire contract',
'A Django REST Framework serializer validates received fields and exposes accepted values through validated_data after successful validation.',
'The receipt serializer declares an exact field set, a six-character ASCII receipt identifier and an integer minor-unit amount. Its custom field rejects text and boolean amounts instead of coercing them into integers. The serializer checks the complete record before the caller reads its accepted data. Serialization itself performs no storage publication.',
'Some built-in fields intentionally accept coercible representations; that may be correct for another protocol but not this one. Unknown fields and duplicate JSON keys need separate policies, and parsed dictionaries cannot recover duplicates already collapsed by a parser. Identity and object permissions also remain separate. [[python/type-conversion|Wire grammar]] and [[python/drf-object-permissions|Record authorization]] define those boundaries.',
r'''from django.conf import settings
settings.configure(INSTALLED_APPS=[], USE_I18N=False)
import django
django.setup()
from rest_framework import serializers

class MinorAmount(serializers.Field):
    def to_internal_value(self, value):
        if type(value) is not int or not 0 <= value <= 1000000:
            raise serializers.ValidationError("exact bounded integer required")
        return value
    def to_representation(self, value):
        return value

class ReceiptInput(serializers.Serializer):
    receipt_id = serializers.RegexField(r"\AR-[0-9]{4}\Z", max_length=6, trim_whitespace=False)
    amount = MinorAmount()
    def to_internal_value(self, data):
        if not isinstance(data, dict) or set(data) != {"receipt_id", "amount"}:
            raise serializers.ValidationError({"non_field_errors": ["exact field set required"]})
        return super().to_internal_value(data)

accepted = ReceiptInput(data={"receipt_id": "R-0041", "amount": 125})
accepted.is_valid(raise_exception=True)
print(dict(accepted.validated_data))
for amount in (True, "125", -1):
    candidate = ReceiptInput(data={"receipt_id": "R-0041", "amount": amount})
    print("accepted:", candidate.is_valid())
extra = ReceiptInput(data={"receipt_id": "R-0041", "amount": 125, "owner_id": 41})
print("extra accepted:", extra.is_valid())''',"{'receipt_id': 'R-0041', 'amount': 125}\naccepted: False\naccepted: False\naccepted: False\nextra accepted: False",
'Validation scans the selected fields and retains accepted/error state. Bounds on fields do not replace a pre-parse request byte limit. A valid serializer does not imply an indexed query, transaction or permitted record mutation.',
['Read validated_data only after successful validation.','Accepting a schema does not prove that the caller owns a receipt.'],['python/type-conversion','python/json-validation','python/drf-object-permissions'],subject='python-web',dependencies=['Django==5.2.17','djangorestframework==3.18.1'])

lesson('drf-object-permissions','Django REST Framework object permissions: check the retrieved record, not only login',
'Object permission checks decide whether the current principal may access a particular retrieved object, separately from whether the principal is authenticated.',
'The local receipt view first requires an authenticated principal, then explicitly calls check_object_permissions on its retrieved fixture record. The owner receives a success response, another authenticated principal is forbidden, and a missing record returns not found. APIRequestFactory and force_authenticate isolate permission behavior without claiming that a login or token exchange occurred.',
'Force_authenticate bypasses real authentication and must stay in tests. List endpoints also need query filtering rather than assuming every returned record will receive an object check. Creation needs its own owner-assignment rule; a received owner_id must not grant access. The fixture uses no database or public listener. [[python/drf-serializers|Input acceptance]] and [[python/django-csrf|Request origin checks]] solve other request boundaries.',
r'''from types import SimpleNamespace
from django.conf import settings
settings.configure(INSTALLED_APPS=[], SECRET_KEY="owned-local-permission-fixture",
                   REST_FRAMEWORK={"DEFAULT_AUTHENTICATION_CLASSES": [], "UNAUTHENTICATED_USER": None})
import django
django.setup()
from django.http import Http404
from rest_framework.permissions import BasePermission, IsAuthenticated
from rest_framework.response import Response
from rest_framework.views import APIView
from rest_framework.test import APIRequestFactory, force_authenticate

RECEIPTS = {41: {"receipt_id": "R-0041", "owner_id": 7}}
class ReceiptOwner(BasePermission):
    def has_object_permission(self, request, view, receipt):
        return receipt["owner_id"] == request.user.pk

class ReceiptView(APIView):
    permission_classes = [IsAuthenticated, ReceiptOwner]
    def get(self, request, number):
        receipt = RECEIPTS.get(number)
        if receipt is None:
            raise Http404
        self.check_object_permissions(request, receipt)
        return Response({"receipt_id": receipt["receipt_id"]})

def local_response(principal_id, number):
    request = APIRequestFactory().get(f"/receipts/{number}")
    if principal_id is not None:
        force_authenticate(request, user=SimpleNamespace(pk=principal_id, is_authenticated=True))
    return ReceiptView.as_view()(request, number=number).status_code

print("owner:", local_response(7, 41))
print("other user:", local_response(8, 41))
print("missing record:", local_response(7, 99))
print("anonymous:", local_response(None, 41))''','owner: 200\nother user: 403\nmissing record: 404\nanonymous: 403',
'This fixture performs one dictionary retrieval and one ownership comparison. A real list/query path needs backend filters, indexes and paging budgets. Response timing and error shape may expose existence information, so a production policy must decide whether forbidden and missing should be distinguishable.',
['Call object checks after retrieving the object in a custom view.','Test authentication bypass is not a production identity provider.'],['python/drf-serializers','python/django-csrf','python/flask-sqlite-persistence'],subject='python-web',dependencies=['Django==5.2.17','djangorestframework==3.18.1'])

group('python-web','Persistent local requests and REST field/owner checks',['flask-sqlite-persistence','drf-serializers','drf-object-permissions'])

lesson('package-resources','Python package resources: read data from a ZIP-backed package',
'Importlib.resources reads package-associated data through a resource interface rather than assuming it lives at a normal filesystem path.',
'The fixture creates an owned package archive containing region labels, imports that package from the ZIP and reads its data with files(). The resource object is traversable but not necessarily a pathlib.Path. The result is text with an explicit encoding. The archive and interpreter path change are owned and cleaned up at the end.',
'Do not form paths from arbitrary received resource names. APIs that require a real file can use as_file inside its context and must not retain a temporary extraction path afterward. Package data also has to be included in the distribution build. [[python/pyproject-config|Wheel contents]] and [[python/zipapp-distribution|Archive execution]] cover those packaging boundaries.',
r'''from importlib.resources import files
import importlib
from pathlib import Path
import sys
import tempfile
from zipfile import ZipFile

with tempfile.TemporaryDirectory() as directory:
    archive = Path(directory) / "receipt_regions.zip"
    with ZipFile(archive, "w") as package:
        package.writestr("receipt_regions/__init__.py", "")
        package.writestr("receipt_regions/regions.txt", "DEL\nBOM\n")
    sys.path.insert(0, str(archive))
    try:
        importlib.import_module("receipt_regions")
        text = files("receipt_regions").joinpath("regions.txt").read_text(encoding="utf-8")
        print(text.splitlines())
    finally:
        sys.path.remove(str(archive))
        sys.modules.pop("receipt_regions", None)''',"['DEL', 'BOM']",
'Reading n resource bytes allocates the decoded text and may decompress archive data. A tiny package does not establish safe budgets for arbitrary compressed input. This archive is generated locally, not received from an untrusted upload.',
['A package resource is not always a filesystem Path.','Keep a temporary extracted path within its resource context.'],['python/pyproject-config','python/zipapp-distribution','python/pathlib-files'],subject='python-packaging')

lesson('zipapp-distribution','Python zipapp: build an executable archive without bundling an interpreter',
'A zipapp is a ZIP archive with a Python entrypoint that a compatible interpreter can execute as an application.',
'The fixture writes one owned __main__.py module, builds a compressed archive and executes it in a child interpreter with explicit arguments. The subprocess checks its exit code and expected output. The archive is deleted with its temporary directory and is not published to a package registry.',
'The archive does not contain Python itself, and third-party/native extension dependencies need a separate distribution strategy. A .pyz file is executable code, not a safe data document to inspect by running it. The example uses only source it just wrote. [[python/package-layout|Entrypoints]] and [[python/subprocess-boundaries|Child process contracts]] explain the surrounding behavior.',
r'''from pathlib import Path
import subprocess
import sys
import tempfile
import zipapp
from zipfile import ZipFile

with tempfile.TemporaryDirectory() as directory:
    application = Path(directory) / "receipt_cli"
    application.mkdir()
    (application / "__main__.py").write_text(
        'import sys\n'
        'if len(sys.argv) != 2 or sys.argv[1] != "--region-count":\n'
        '    raise SystemExit(2)\n'
        'print("supported regions: 2")\n', encoding="utf-8")
    archive = Path(directory) / "receipt_cli.pyz"
    zipapp.create_archive(application, archive, compressed=True)
    result = subprocess.run([sys.executable, "-I", str(archive), "--region-count"],
                            cwd=directory, capture_output=True, text=True, timeout=5, check=True)
    print(result.stdout.strip())
    with ZipFile(archive) as built:
        print("archive built:", "__main__.py" in built.namelist())''','supported regions: 2\narchive built: True',
'Archive creation scans and compresses supplied files; storage depends on their contents. Runtime imports may decompress source. This fixture has tiny fixed output and does not enforce a general child-output/process-tree budget.',
['A zipapp needs a compatible external interpreter.','Do not execute an untrusted archive merely to identify its format.'],['python/package-layout','python/subprocess-boundaries','python/package-resources'],subject='python-packaging')

group('python-packaging','Resource data and executable archives',['package-resources','zipapp-distribution'])
lesson('exceptions-interview','Python exception interview: chained causes and a finally return that hides failure',
'Exception chaining preserves a selected failure’s causal exception, while a return from finally can override a pending exception or return.',
'The accepted import translates an OSError into a ValueError with an explicit cause. The review inspects that cause instead of assuming only the visible exception existed. A deliberately incorrect finally-return function then reports success after raising. Comparing those traces tests whether a developer can identify a suppressed failure, not merely name exception keywords.',
'The incorrect function is included as a failure case and must not become an application cleanup pattern. Use finally for release work and allow the pending failure to continue. Catching BaseException broadly can also swallow process-control exceptions. [[python/exit-stack|Resource release]] and [[python/exception-groups|Grouped failures]] cover cleanup and multi-error paths without claiming that one translated error explains every failure.',
r'''def accepted_import():
    try:
        raise OSError("owned fixture input unavailable")
    except OSError as cause:
        raise ValueError("receipt import rejected") from cause

def incorrect_finally_return():
    try:
        raise ValueError("receipt rejected")
    finally:
        return "incorrect success"

try:
    accepted_import()
except ValueError as failure:
    print("visible:", type(failure).__name__)
    print("cause:", type(failure.__cause__).__name__)
print("suppressed failure:", incorrect_finally_return())''','visible: ValueError\ncause: OSError\nsuppressed failure: incorrect success',
'The fixture allocates a few exception/traceback objects and retains their causal references during handling. Real tracebacks can keep substantial local state alive, so storing exception objects indefinitely has an ownership cost.',
['Never return from cleanup merely to produce a reassuring result.','Inspect the chained cause when diagnosing a translated failure.'],['python/exceptions','python/exit-stack','python/exception-groups'],subject='python-interview')

lesson('object-lookup-interview','Python object lookup interview: descriptor precedence before instance state',
'Attribute lookup gives data descriptors precedence over instance dictionary entries, while a non-data descriptor can be shadowed by an instance entry.',
'The receipt object has two descriptor-backed labels. Directly adding a dictionary entry shadows the non-data descriptor but cannot shadow the data descriptor. The program deliberately edits __dict__ to expose lookup order; normal assignment to the read-only data descriptor is rejected. This trace connects properties and methods to the same attribute mechanism.',
'Custom __getattribute__ and __getattr__ hooks can alter behavior, so this fixture covers normal object lookup only. Descriptor lookup is also not a security boundary against code that can directly alter objects. [[python/descriptors|Descriptor storage]] and [[python/method-binding|Method receivers]] explain when ordinary-looking attribute access runs code.',
r'''class CachedLabel:
    def __get__(self, instance, owner):
        return "class label"

class RequiredLabel:
    def __get__(self, instance, owner):
        return "required label"
    def __set__(self, instance, value):
        raise AttributeError("read-only label")

class ReceiptView:
    cached = CachedLabel()
    required = RequiredLabel()

receipt = ReceiptView()
receipt.__dict__["cached"] = "instance label"
receipt.__dict__["required"] = "attempted shadow"
print(receipt.cached)
print(receipt.required)
try:
    receipt.required = "replacement"
except AttributeError:
    print("normal assignment rejected")''','instance label\nrequired label\nnormal assignment rejected',
'Normal lookup examines class/instance state and the inheritance path, with descriptor execution adding its own cost. A descriptor can perform arbitrary I/O or computation; an attribute’s compact spelling does not make it free.',
['An instance dictionary entry does not override a data descriptor under normal lookup.','Attribute access can execute a descriptor method.'],['python/descriptors','python/properties','python/method-binding'],subject='python-interview')

lesson('concurrency-interview','Python concurrency interview: cancellation must still run cleanup',
'Asyncio task cancellation requests that a task raise CancelledError at a suspension point, allowing its finally cleanup to run.',
'The owned worker signals that it has started, then waits on an event that the test never releases. The caller cancels it and awaits the result. Cleanup records a release marker before the caller observes CancelledError. No timing sleep is used to guess whether the worker reached its suspension point; the start event defines that boundary.',
'Cancellation is cooperative. Code that blocks the event-loop thread or suppresses cancellation can violate the caller’s expectations. Releasing a local marker is not proof that an external service canceled a request. [[python/async-deadlines|Deadline behavior]] and [[python/async-task-groups|Structured task lifetime]] address related caller/worker coordination.',
r'''import asyncio

async def inspect_cancellation():
    started = asyncio.Event()
    never_released = asyncio.Event()
    cleanup = []
    async def worker():
        try:
            started.set()
            await never_released.wait()
        finally:
            cleanup.append("released")
    task = asyncio.create_task(worker())
    await started.wait()
    task.cancel()
    try:
        await task
    except asyncio.CancelledError:
        print("caller observed cancellation")
    print("cleanup:", cleanup)
    print("task finished:", task.done())

asyncio.run(inspect_cancellation())''',"caller observed cancellation\ncleanup: ['released']\ntask finished: True",
'The fixture owns one task and two event objects. Cancellation latency depends on scheduling and the next suspension point, not a fixed wall-clock guarantee. A retained unawaited task can keep reachable state alive after the caller’s surrounding function returns.',
['Await the canceled task so cleanup and failure become observable.','Use a synchronization event instead of guessing task state with a sleep.'],['python/async-deadlines','python/async-task-groups','python/context-variables'],subject='python-interview')

group('python-interview','Explain failure and lookup traces',['exceptions-interview','object-lookup-interview','concurrency-interview'])

lesson('window-exercise','Python window exercise: verify a fixed-width maximum against direct slices',
'A fixed-width sliding total updates an adjacent interval by adding its entering value and subtracting its departing value.',
'The receipt exercise returns the largest sum over exactly k adjacent amounts. It rejects an empty batch, boolean values and a width outside one through the batch length. Negative amounts are accepted, so the best total must start from the first actual window rather than an invented zero. The independent answer uses direct slices on the same small fixture.',
'The operation returns a total without the window’s identity or tie position. Those would require another declared return contract. Its input list remains unchanged. [[python/sliding-window|Moving invariants]] and [[python/hypothesis-properties|Generated tests]] extend the exercise to varied sequences without copying the rolling update into the oracle.',
r'''def maximum_window(amounts, width):
    if not 1 <= len(amounts) <= 128 or any(type(amount) is not int for amount in amounts):
        raise ValueError("bounded integer batch required")
    if type(width) is not int or not 1 <= width <= len(amounts):
        raise ValueError("window width rejected")
    running = sum(amounts[:width]); best = running
    for index in range(width, len(amounts)):
        running += amounts[index] - amounts[index - width]
        best = max(best, running)
    return best

amounts = [125, -50, 250, 75]
print(maximum_window(amounts, 2))
print("direct answer:", max(sum(amounts[index:index + 2]) for index in range(len(amounts) - 1)))
print("negative answer:", maximum_window([-5, -3], 1))
try:
    maximum_window(amounts, 0)
except ValueError:
    print("zero width rejected")''','325\ndirect answer: 325\nnegative answer: -3\nzero width rejected',
'The scan performs O(n) arithmetic operations. Its initial slice retains O(k) temporary references in this implementation, followed by O(1) rolling state. The direct-slice oracle costs O(nk), which is acceptable for bounded tests rather than the main algorithm.',
['Initialize from an actual window when all amounts can be negative.','An oracle should compute the answer independently of the rolling update.'],['python/sliding-window','python/hypothesis-properties','python/segment-tree'],subject='python-exercises')

lesson('range-exercise','Python range exercise: immutable prefix totals and exclusive endpoints',
'A prefix-total array stores cumulative amounts so a static half-open interval can be answered by subtracting two stored totals.',
'The exercise builds an owned prefix array from bounded exact integers. Prefix position zero represents the sum before any record. A query for positions left through right-minus-one returns prefix[right] minus prefix[left]. Empty intervals return zero. Editing the source list afterward does not change the already built numeric snapshot.',
'This snapshot cannot track subsequent edits. Replacing or adding amounts requires a new prefix build or an update-capable structure. Exposing the prefix list also allows a caller to corrupt its invariant; this fixture passes only its own constructed result. [[python/segment-tree|Point updates]] and [[python/lazy-range-sums|Interval updates]] serve changing datasets.',
r'''def prefix_totals(amounts):
    if len(amounts) > 128 or any(type(amount) is not int for amount in amounts):
        raise ValueError("bounded integer amounts required")
    prefix = [0]
    for amount in amounts:
        prefix.append(prefix[-1] + amount)
    return prefix

def interval_total(prefix, left, right):
    count = len(prefix) - 1
    if any(type(index) is not int for index in (left, right)) or not 0 <= left <= right <= count:
        raise ValueError("invalid half-open interval")
    return prefix[right] - prefix[left]

amounts = [125, 250, 75]
prefix = prefix_totals(amounts)
print(prefix)
print(interval_total(prefix, 1, 3))
print(interval_total(prefix, 2, 2))
amounts[0] = 999
print("snapshot total:", interval_total(prefix, 0, 3))''','[0, 125, 375, 450]\n325\n0\nsnapshot total: 450',
'Building n totals takes O(n) arithmetic work and O(n) retained integers. A query uses two lookups and one subtraction, with digit-dependent numeric costs. Rebuilding after every change can erase that query-time advantage.',
['Prefix position zero is required for intervals starting at zero.','The snapshot does not update when the original list changes.'],['python/segment-tree','python/lazy-range-sums','python/copy-deepcopy'],subject='python-exercises')

lesson('aggregation-exercise','Python aggregation exercise: validate records before returning group totals',
'Validated aggregation combines accepted records into per-key totals without treating malformed rows as ordinary zero values.',
'The region exercise accepts an exact pair of fields, one known ASCII region and a bounded nonnegative integer amount. It accumulates into a private dictionary and returns it only after the complete batch succeeds. A rejected later record therefore cannot become a partially accepted public answer. The returned totals do not alias the original row dictionaries.',
'The batch is already an owned list, so its row limit is not a network reception limit. Publishing totals to a database or file needs a separate transaction or staging contract. Missing keys, booleans and unknown regions are deliberately rejected instead of guessed. [[python/chunked-aggregation|Batchwise imports]] and [[python/defaultdict-grouping|Group factories]] show adjacent implementation choices.',
r'''def accepted_totals(records):
    if not isinstance(records, list) or len(records) > 64:
        raise ValueError("record batch rejected")
    totals = {}
    for record in records:
        if not isinstance(record, dict) or set(record) != {"region", "amount"}:
            raise ValueError("record fields rejected")
        if not isinstance(record["region"], str) or record["region"] not in {"DEL", "BOM"}:
            raise ValueError("region rejected")
        amount = record["amount"]
        if type(amount) is not int or not 0 <= amount <= 1000000:
            raise ValueError("amount rejected")
        region = record["region"]
        totals[region] = totals.get(region, 0) + amount
    return totals

print(accepted_totals([{"region": "DEL", "amount": 125}, {"region": "DEL", "amount": 250}]))
try:
    accepted_totals([{"region": "DEL", "amount": 125}, {"region": "BOM", "amount": True}])
except ValueError:
    print("later record rejected; no totals returned")''',"{'DEL': 375}\nlater record rejected; no totals returned",
'For n accepted rows and g regions, expected mapping work is O(n) and result storage is O(g), excluding numeric digit costs. This schema has only two permitted groups and a row/amount budget, so aggregate growth is bounded.',
['A boolean is not an accepted amount even though bool subclasses int.','Do not return or publish partial totals after a rejected row.'],['python/chunked-aggregation','python/defaultdict-grouping','python/sqlite-cli-project'],subject='python-exercises')

group('python-exercises','Independent window, interval and record answers',['window-exercise','range-exercise','aggregation-exercise'])

lesson('collections-reference','Python collections reference: selection costs and retained ownership',
'Python containers offer different ordering, membership and mutation contracts, so choosing one depends on the operation rather than only the stored value type.',
'The reference contrasts a list snapshot, set membership, dictionary defaults and a bounded deque. List copying separates the outer container, set membership answers whether an ID is present, and dictionary get reads a missing entry without creating it. Deque retains only the selected history length and intentionally discards older entries.',
'This is a compact operation reference, not a universal complexity guarantee. Custom hashes, equality methods and nested aliases can change cost or behavior. A bounded history must not stand in for a ledger that must preserve every event. [[python/hash-equality|Key invariants]], [[python/copy-deepcopy|Nested ownership]] and [[python/counter-deque|Endpoint containers]] provide the detailed contracts.',
r'''from collections import deque

receipt_ids = ["R-0041", "R-0042"]
outer_snapshot = receipt_ids.copy()
known = set(receipt_ids)
amounts = {"R-0041": 125}
history = deque(receipt_ids, maxlen=2)
history.append("R-0043")
print("member:", "R-0041" in known)
print("missing amount:", amounts.get("R-0099"))
print("key created:", "R-0099" in amounts)
print("retained history:", list(history))
receipt_ids.append("R-0044")
print("outer snapshot:", outer_snapshot)''',"member: True\nmissing amount: None\nkey created: False\nretained history: ['R-0042', 'R-0043']\nouter snapshot: ['R-0041', 'R-0042']",
'List snapshot construction costs O(n) references. Set/dictionary membership has expected constant lookup work under suitable hashes. Deque endpoint operations avoid list-front shifting, while middle indexing/traversal has different costs.',
['An outer snapshot still shares mutable nested objects.','A bounded deque discards old history by design.'],['python/hash-equality','python/copy-deepcopy','python/counter-deque'],subject='python-reference')

lesson('exceptions-reference','Python exceptions reference: raise, propagate, chain and clean up',
'Exception handling chooses which failures to translate or handle while finally provides cleanup during normal return or stack unwinding.',
'The bounded parser translates an integer-conversion ValueError into a domain ValueError with an explicit cause. A finally suite appends a cleanup marker regardless of acceptance or rejection. The caller catches only the declared domain failure. Two calls show cleanup on both paths without a finally return that would hide the rejected input.',
'Exception messages can reveal received values if they are copied into logs; this fixture reports a fixed domain message. Bare except and broad BaseException handling can interfere with process control. Resource acquisition itself may fail before a finally-managed body starts, which is why [[python/exit-stack|Staged acquisition]] has its own pattern. [[python/exception-groups|Grouped errors]] needs except* rather than flattening all failures.',
r'''cleanup = []
def parsed_quantity(text):
    try:
        try:
            return int(text)
        except ValueError as cause:
            raise ValueError("quantity conversion rejected") from cause
    finally:
        cleanup.append("released")

print(parsed_quantity("3"))
try:
    parsed_quantity("invalid")
except ValueError as failure:
    print(str(failure))
    print("cause retained:", failure.__cause__ is not None)
print(cleanup)''',"3\nquantity conversion rejected\ncause retained: True\n['released', 'released']",
'The fixture has fixed small input. Int conversion can accept more syntax than a field grammar and allocate larger integers for longer text; see the strict parser rather than treating this reference operation as complete wire validation.',
['Cleanup should not replace the pending exception with a return.','Catch the intended failure category and keep received secrets out of messages.'],['python/type-conversion','python/exceptions-interview','python/exit-stack'],subject='python-reference')

group('python-reference','Collection and failure operation reminders',['collections-reference','exceptions-reference'])

COMPLETION_BANKS={
'python-language-boundaries':('Python language boundary quiz',['python/truthiness','python/type-conversion','python/loop-control','python/map-filter-reduce'],[
('Which default expression preserves an accepted zero discount?',['discount or 25','25 if discount is None else discount','bool(discount)','discount and 25'],1,'An explicit None check distinguishes missing input from a valid zero.'),
('Does successful int conversion prove a quantity satisfies an ASCII field grammar?',['Always','Only on Windows','No; conversion and field validation differ','Only for positive values'],2,'Conversion can accept syntax that the field contract rejects. Validate syntax, type and bounds separately.'),
('Why does the strict quantity parser reject True?',['Its string is too long','bool is a subclass of int but is outside this wire contract','Python cannot compare booleans','True is negative'],1,'An exact type check prevents a boolean from being accepted as an integer quantity.'),
('When does a for else suite run?',['After every iteration','Only on an empty iterable','Whenever the last item is false','When the loop finishes without break'],3,'Exhausting the iterable reaches else; break skips it. A raised exception also prevents normal completion.'),
('What does range(2, 7, 2) visit?',['2, 4, 6','2, 4, 6, 7','2, 3, 4, 5, 6','3, 5, 7'],0,'The stop bound is exclusive and the step is two.'),
('What does enumerate add?',['A persistent database identity','A presentation counter for this iteration','A copy of every record','Sorted order'],1,'The counter describes the current traversal. It is not a stable receipt identifier.'),
('Does creating map immediately call the mapping function on every value?',['Yes, always','Only on lists','No; consuming the iterator triggers work','Only on tuples'],2,'Map is lazy. Changes to a still-unconsumed mutable input can affect subsequent reads.'),
('What happens after consuming a map iterator once?',['It repeats forever','It rewinds automatically','It sorts its input','It is exhausted unless a new iterator is created'],3,'Iterator exhaustion is state, not a cached collection result.'),
('Why bind a loop value in a lambda default?',['To retain that iteration’s value instead of one later outer binding','To make lambda run in parallel','To remove its return value','To convert it into a generator'],0,'Closures retain bindings. A default argument captures the current value when the function is created.'),
('Which receiver does a classmethod receive through a subclass?',['The first instance','The subclass itself','The module globals','No receiver'],1,'The bound class argument supports subclass-aware construction, provided constructor contracts remain compatible.'),
('Does defaultdict.get on a missing key invoke its factory?',['Always','Only for lists','No','Only after iteration'],2,'Get reads without creating the missing entry. Index access can create it.'),
('What does bisect guarantee about list insertion cost?',['The whole insertion is constant time','The whole insertion is logarithmic','Every value is copied twice','Search is logarithmic, but list insertion can shift linearly many references'],3,'Finding a position and making space in an array-backed list have different costs.'),
]),
'python-lifetime-protocols':('Python class and lifetime protocol quiz',['python/metaclass-registry','python/abstract-classes','python/exception-groups','python/context-variables','python/functools-cache'],[
('When should the codec registry publish a new class?',['Before validating its wire name','Before type construction','After validation and successful class construction','When the module filename is known'],2,'Publishing earlier can leave an invalid or failed class declaration in shared registry state.'),
('What does an ABC requirement prove?',['All inputs are safe','Required abstract methods have implementations before instantiation','Database durability','Thread safety'],1,'ABC bookkeeping checks implementation presence; it does not prove the domain behavior of that implementation.'),
('What happens to unmatched members after except* handles selected errors?',['They disappear','They become return values','They are all retried','They remain as an unhandled subgroup'],3,'Partial handling retains unmatched failures rather than flattening or hiding them.'),
('Why reset a ContextVar token in finally?',['To restore the prior binding even when work fails','To share one global value with all tasks','To serialize the event loop','To cancel other requests'],0,'Token reset restores the previous context binding on normal and failure paths.'),
('Does ContextVar isolate mutation of a shared list stored as its value?',['Yes, by deep copying','No; task-local binding is not a deep-copy policy','Only on Linux','Only for small lists'],1,'Contexts can still refer to the same mutable object. Immutable labels avoid that ownership problem.'),
('Why include a price revision in a cache key?',['It encrypts the key','It makes the cache unbounded','It separates results from different declared price revisions','It makes external changes self-detecting'],2,'The caller must supply a meaningful revision. Cache lookup cannot infer an external price change by itself.'),
('What does cache_clear release?',['Every module variable','The interpreter heap','All user sessions','Retained cache entries'],3,'Clearing drops the cache’s retained keys and results; other references may still keep objects alive.'),
('Which descriptor wins over a matching instance dictionary entry?',['A data descriptor in ordinary attribute lookup','Any string attribute','An imported module','A non-data descriptor in every case'],0,'Data descriptors participate before instance state in ordinary object attribute lookup.'),
('What can a return in finally do to a pending exception?',['Make it more specific','Suppress it by replacing control flow','Attach a traceback to another task','Convert it to an ExceptionGroup'],1,'A finally return can hide a failure. Cleanup should preserve the intended return or exception.'),
('What does explicit raise DomainError from cause retain?',['An HTTP response','A retry budget','The causal relationship to the original failure','A copy of every stack variable'],2,'Explicit exception chaining records why the translated domain failure happened.'),
('Why await a task after requesting cancellation?',['To restart it','To prevent finally from running','To erase its exception','To observe completion and cleanup'],3,'Cancellation requests a state change. Awaiting observes whether the task completed, failed or acknowledged cancellation.'),
('Why is the local concurrency fixture synchronized with Events?',['It observes a known task state instead of guessing with a delay','It runs on several CPU cores','It adds network retries','It prevents all cancellation'],0,'An explicit signal identifies the point reached by the worker before cancellation is requested.'),
]),
'python-api-range-contracts':('Python API, data and range contract quiz',['python/avl-insertion','python/trie-deletion','python/lazy-range-sums','python/edit-script','python/drf-object-permissions','python/pandas-null-joins'],[
('What must an AVL rotation preserve?',['Insertion order only','Only the root key','Ordered keys, subtree links and stored heights','One node per depth'],2,'Rotation changes structure while retaining binary-search ordering and recomputing height information.'),
('When can trie deletion prune a node?',['Whenever its prefix is requested','When it is nonterminal and has no remaining children','Whenever it has one child','Before checking whether the word exists'],1,'Pruning a prefix used by another word would lose accepted neighbors.'),
('How much does adding delta to a segment of length n change its sum?',['delta','n plus delta','delta divided by n','n times delta'],3,'Every represented element changes by delta, so the stored total changes by segment length times delta.'),
('What does a half-open empty interval return in the range fixture?',['Zero','The last element','An error for every empty interval','The whole total'],0,'A validated interval with identical endpoints contains no elements.'),
('Why verify an edit script by applying it?',['To avoid validating its source length','To check reconstruction as well as the computed distance','To make the problem constant time','To replace the target with sorted input'],1,'A correct distance alone does not prove that the reconstructed operations produce the target.'),
('How should a Pandas null-key merge be treated?',['Null keys never match','It always follows SQL null semantics','Null keys can match; define a missing-key policy explicitly','All missing rows must be deleted'],2,'Pandas can match missing keys. Quarantine invalid lookup keys and retain unmatched input for review when that is the contract.'),
('What does rank deficiency warn about in least squares?',['A plotting failure','A sorted result','Guaranteed exact prediction','Coefficients may not be uniquely determined'],3,'Dependent design columns can admit several coefficient vectors. Inspect rank instead of treating every fit as identified.'),
('What does branch coverage alone establish?',['Measured execution paths were visited, not that outputs are correct','All inputs were tested','Race freedom','Correct API authorization'],0,'Assertions and independent expected results are still required even when measured branch coverage is complete.'),
('Why does the DRF amount field reject numeric text?',['Text is always unsafe','This wire contract accepts an exact integer rather than coercion','JSON cannot contain strings','SQLite rejects all strings'],1,'A field parser should enforce its declared type and bounds instead of silently widening accepted input.'),
('What must a custom DRF detail view call after retrieving a record?',['cache_clear','serializer.save for every GET','check_object_permissions with that record','django.setup on each request'],2,'Login permission is not ownership permission. The object check evaluates access to the selected record.'),
('Does an object permission automatically filter every row of a list endpoint?',['Yes, on every backend','Only with SQLite','Only for anonymous users','No; the list query needs its own visibility policy'],3,'A detail-object check does not establish safe list filtering or creation authorization.'),
('What must a zipapp host still provide?',['A compatible Python interpreter and any required external dependencies','An embedded operating system','No installed software','A browser extension'],0,'A zipapp packages source, not a Python runtime or a universal dependency installation.'),
]),
}
for slug,(title,refs,questions) in COMPLETION_BANKS.items():
 BANKS[slug]=(title,questions)
 path='quizzes/'+slug
 entry=copy.deepcopy(lookup['quizzes/python-basics'])
 entry.update(id=str(uuid.uuid5(uuid.NAMESPACE_URL,'https://aitrove.in/'+path)),path=path,title=title,summary='Twelve explained questions on '+title.lower().replace(' quiz','')+'.',tags=['python','quiz'],sort_order=300+len(added),published_at=stamp,updated_at=stamp)
 entry['body']=para('A Python self-check tests a selected operation contract through twelve questions with explanations.')+'<h2>Review the related lessons</h2><ul>'+''.join('<li><a href="/'+p+'">'+html.escape(lookup[p]['title'])+'</a></li>' for p in refs)+'</ul><h3>Common Mistakes</h3>'+para('A correct local answer is not a deployment guarantee. Read the input, ownership and failure clauses before adapting the program. Results stay in this browser.')
 entry['data']['questions']=[{'prompt':prompt,'options':options,'answer':answer,'explanation':explanation} for prompt,options,answer,explanation in questions]
 entry['data']['related']=[{'path':p,'title':lookup[p]['title']} for p in refs]
 upsert(entry);added.append(path)

COMPLETION_REVERSE={
'python/setup-interpreter':['input-output','type-conversion'],
'python/python-variables':['truthiness','type-conversion'],
'python/control-flow':['loop-control','range-enumerate'],
'python/python-functions':['lambda-functions','map-filter-reduce'],
'python/function-arguments':['input-output'],
'python/classes':['method-binding','abstract-classes'],
'python/inheritance':['abstract-classes','metaclass-registry'],
'python/descriptors':['method-binding','object-lookup-interview'],
'python/mro-super':['metaclass-registry'],
'python/exceptions':['exception-groups','exceptions-reference','exceptions-interview'],
'python/async-task-groups':['context-variables','concurrency-interview'],
'python/logging-context':['context-variables'],
'python/memoization':['functools-cache'],
'python/dictionaries':['defaultdict-grouping','collections-reference'],
'python/tuples':['namedtuple-records'],
'python/sorting':['bisect-insertion','lambda-functions'],
'python/bst-deletion':['avl-insertion'],
'python/tree-traversal':['avl-insertion'],
'python/trie-prefix':['trie-deletion'],
'python/segment-tree':['lazy-range-sums','range-exercise'],
'python/edit-distance':['edit-script'],
'python/sliding-window':['window-exercise'],
'python/pandas-joins':['pandas-null-joins'],
'python/pandas-rolling':['pandas-resample'],
'python/numpy-precision':['linear-least-squares'],
'python/unittest-contracts':['hypothesis-properties','coverage-branches'],
'python/pytest-fixtures':['hypothesis-properties','coverage-branches'],
'python/flask-json-api':['flask-sqlite-persistence'],
'python/sqlite-transactions':['flask-sqlite-persistence'],
'python/django-forms':['drf-serializers'],
'python/django-routing':['drf-object-permissions'],
'python/django-query-counts':['drf-object-permissions'],
'python/package-layout':['package-resources','zipapp-distribution'],
'python/chunked-aggregation':['aggregation-exercise'],
'python/iterator-interview':['object-lookup-interview'],
}
for original,slugs in COMPLETION_REVERSE.items():
 assert original in lookup, original
 targets=['python/'+slug for slug in slugs]
 assert all(target in lookup for target in targets),targets
 entry=lookup[original]
 marker='<h2>Follow the related contract</h2>'
 entry['body']=entry['body'].split(marker)[0]+marker+para(', '.join('[['+p+'|'+lookup[p]['title']+']]' for p in targets)+'.')
 known={item['path'] for item in entry['data'].get('related',[])}
 entry['data'].setdefault('related',[]).extend({'path':p,'title':lookup[p]['title']} for p in targets if p not in known)
