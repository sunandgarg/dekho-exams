"""Second Python pass. Executed by python-content.py with its editorial helpers."""
EXTRA_MODULES={}
def lesson(slug,title,definition,contract,boundary,source,expected,cost,mistakes,related,subject='python',dependencies=None):
 put(slug,title,definition,contract,boundary,source,expected,cost,mistakes,related,subject)
 if dependencies:
  entry=lookup['python/'+slug]
  entry['data']['python_dependencies']=dependencies
  entry['data']['python_version']='Verified on CPython 3.14.6; see the pinned package versions in this lesson'
  entry['data']['python_minimum']='3.14'
  marker='<h2>Working program</h2>'
  setup=para('Dependency check: this program was executed on CPython 3.14.6 with '+', '.join(dependencies)+'. Install these versions in a separate virtual environment. The download includes the recorded environment snapshot; no third-party package is part of the website runtime.')
  entry['body']=entry['body'].replace(marker,'<h2>Tested environment</h2>'+setup+marker)

def group(subject,title,slugs):EXTRA_MODULES.setdefault(subject,[]).append((title,slugs))

lesson('scope-bindings','Python scope: local assignment, nonlocal state and late binding',
'Python resolves a name through its enclosing namespaces, while assignment inside a function normally binds a local name.',
'The progress counter keeps one integer inside its closure and uses nonlocal to rebind that enclosing name. The label callbacks capture their current receipt ID through a default argument. These mechanisms solve different problems: nonlocal gives several calls shared state; the bound default gives each callback its own selected value. A closure over a loop variable without that binding would read its final value when called later.',
'The counter is not thread-safe. Its read, addition and replacement form one application transition but not one protected transaction. An immutable captured integer is safe from later mutation; capturing a mutable record would still retain its alias. [[python/closures|Closure ownership]] and [[python/thread-locks|Locks]] make those boundaries concrete.',
r'''def progress_counter():
    completed = 0
    def record_completion():
        nonlocal completed
        completed += 1
        return completed
    return record_completion

record = progress_counter()
labels = [lambda receipt_id=receipt_id: receipt_id for receipt_id in (41, 42)]
print(record(), record())
print([label() for label in labels])''','1 2\n[41, 42]',
'Each closure retains its reachable captured objects. Creating n label callbacks takes O(n) time and O(n) retained function/default storage. Growing integer counts also incur digit costs.',
['nonlocal changes an enclosing binding, not a global variable.','A captured reference does not freeze the referenced object.'],['python/closures','python/function-arguments','python/thread-locks'])

lesson('argument-unpacking','Python unpacking: keyword collisions and strict record pairing',
'Python unpacking expands an iterable into positional arguments or a mapping into keyword arguments at a call boundary.',
'The dispatch operation accepts a named region and an optional priority. Passing two mappings with the same keyword raises TypeError before the function body runs. That differs from building a merged dictionary: the latter can overwrite earlier values. The paired receipt import uses strict zip so a missing amount fails instead of silently truncating a record.',
'Strict zip can yield earlier pairs before detecting unequal lengths. The fixture materializes all pairs before any publication, so a length error cannot leave a half-written ledger. Large or infinite input needs an explicit ingestion bound rather than this eager list. [[python/collection-exercise|Staged collections]] and [[python/sqlite-cli-project|Transactional imports]] apply the same validate-before-write rule.',
r'''def dispatch(*, region, priority=0):
    return f"{region}:{priority}"

print(dispatch(**{"region": "DEL"}, **{"priority": 2}))
try:
    dispatch(**{"region": "DEL"}, **{"region": "BOM"})
except TypeError:
    print("duplicate keyword rejected")
try:
    list(zip([41, 42], [125], strict=True))
except ValueError:
    print("incomplete record batch rejected")''','DEL:2\nduplicate keyword rejected\nincomplete record batch rejected',
'Building n pairs takes O(n) time and storage. Mapping expansion copies argument references into call bookkeeping; it does not copy the objects supplied as values.',
['Dictionary merging and call-time duplicate keywords have different rules.','Do not publish strict-zip pairs before exhaustion when the batch must be atomic.'],['python/function-arguments','python/collection-exercise','python/sqlite-cli-project'])

lesson('copy-deepcopy','Python shallow and deep copies: preserve aliases deliberately',
'A shallow copy duplicates a container’s outer references; a deep copy recursively copies supported reachable state while tracking already-copied objects.',
'Two dispatch entries intentionally reference one shared label list. A shallow copy of their dictionary still references the original list. Deepcopy creates a separate list but preserves the relationship between the two fields within the copied graph. That alias preservation matters: deep copying does not mean every path becomes an unrelated object.',
'Files, sockets and arbitrary custom objects are not automatically meaningful snapshots. Classes can override copying, and a graph may contain cycles. For domain snapshots, a fresh immutable data representation is often easier to audit than recursively copying a live service object. [[python/dataclasses|Dataclass ownership]] and [[python/inventory-project|Staged inventory state]] cover alternatives.',
r'''from copy import copy, deepcopy

labels = ["checked"]
batch = {"first": labels, "second": labels}
shallow = copy(batch)
owned = deepcopy(batch)
owned["first"].append("packed")
print(shallow["first"] is labels)
print(owned["first"] is owned["second"])
print(labels)
print(owned["second"])''',"True\nTrue\n['checked']\n['checked', 'packed']",
'An outer dictionary copy takes O(n) reference work. Deepcopy cost depends on the reachable graph and custom hooks; visited-object bookkeeping prevents copying the same supported object repeatedly, but there is no general constant-cost snapshot.',
['A deep copy can preserve shared references inside the copied graph.','Do not treat copying live I/O handles as an application recovery plan.'],['python/python-variables','python/dataclasses','python/inventory-project'],subject='python-types')

lesson('unicode-normalization','Python Unicode normalization: equality is not visual identity',
'Unicode normalization maps equivalent code-point sequences into a selected normalization form; Python string equality otherwise compares their code points.',
'The display label uses one precomposed letter in one record and a letter plus combining accent in another. NFC normalizes both into the same canonical form for this comparison. The program keeps display text separate from an identifier policy: deciding that two labels compare equally is not permission to merge two customer records.',
'Normalization does not remove every visually confusable character and does not count grapheme clusters. A normalized string can still include mixed scripts, controls or misleading labels. Use an explicit identifier alphabet when the protocol allows one, and enforce length after transformations as well as before them. [[python/regex-validation|ASCII identifiers]] and [[python/strings-bytes|Encoding boundaries]] address different layers.',
r'''import unicodedata

stored_label = "Caf\u00e9"
imported_label = "Cafe\u0301"
print(stored_label == imported_label)
print(len(stored_label), len(imported_label))
print(unicodedata.normalize("NFC", stored_label) ==
      unicodedata.normalize("NFC", imported_label))''','False\n4 5\nTrue',
'Normalization scans input and allocates transformed text; work and storage depend on code points and combining sequences. len(str) counts code points, not visible symbols or UTF-8 bytes.',
['Normalization is not a confusable-character detector.','Never silently merge accounts merely because their display labels normalize equally.'],['python/strings-bytes','python/regex-validation','python/pandas-joins'],subject='python-types')

lesson('counter-deque','Python Counter and deque: counts, queues and bounded history',
'Counter stores counts by key, while deque stores ordered entries with endpoint operations suited to queues and rolling histories.',
'The audit history retains the last two receipt IDs. Its maxlen causes an older entry to be discarded when a third arrives, so this is a rolling display rather than a durable event log. Counter separately counts review outcomes. The sorted output defines presentation order instead of relying on how outcome keys happened to enter the import.',
'A bounded deque discards evidence by design. It should not replace a financial ledger or retry queue that must retain every outstanding job. Counter also permits zero and negative counts; its contents do not by themselves establish a nonnegative inventory invariant. [[python/inventory-project|Inventory rules]] and [[python/async-queues|Work queues]] provide the missing contracts.',
r'''from collections import Counter, deque

recent_receipts = deque(maxlen=2)
for receipt_id in (41, 42, 43):
    recent_receipts.append(receipt_id)
outcomes = Counter(["accepted", "rejected", "accepted"])
print(list(recent_receipts))
print(sorted(outcomes.items()))
print(outcomes["missing"])''',"[42, 43]\n[('accepted', 2), ('rejected', 1)]\n0",
'For n outcomes with u distinct keys, counting uses expected O(n) dictionary work and O(u) retained keys. Endpoint deque operations avoid shifting an entire list; the rolling history stores at most its declared capacity.',
['maxlen discards old entries; it does not reject new work.','A Counter is not a validated nonnegative stock ledger.'],['python/dictionaries','python/heap-top-k','python/async-queues'],subject='python-types')

lesson('timezone-fold','Python zoneinfo and fold: two instants can share one clock label',
'A zone-aware datetime combines a local clock reading with timezone rules; fold distinguishes repeated local times during a backward clock transition.',
'The fixture converts two known UTC instants into America/New_York. Both display 01:30 on the transition date, but their offsets and fold values differ. Starting from UTC avoids guessing which instant an ambiguous user-entered clock reading intended. Appointment entry needs its own reject-or-select policy; conversion cannot infer one.',
'ZoneInfo uses installed IANA timezone data, which may differ across deployments. The source kit pins tzdata for a portable fallback, but a system timezone database can take precedence. Arithmetic on local datetimes and equality with the same zone object also require care around folds; compare UTC instants for elapsed-time decisions. [[python/datetime-boundaries|Explicit offsets]] is the simpler wire format.',
r'''from datetime import datetime, timezone
from zoneinfo import ZoneInfo

zone = ZoneInfo("America/New_York")
for hour in (5, 6):
    instant = datetime(2024, 11, 3, hour, 30, tzinfo=timezone.utc)
    local = instant.astimezone(zone)
    print(local.isoformat(), "fold=" + str(local.fold))''','2024-11-03T01:30:00-04:00 fold=0\n2024-11-03T01:30:00-05:00 fold=1',
'Zone rules are loaded and cached by the runtime. This fixture converts two instants; it does not measure timezone lookup cost or claim an elapsed-hour calculation from local labels.',
['A timezone name does not resolve an ambiguous typed clock reading automatically.','Store the timezone database/version policy when future scheduling depends on it.'],['python/datetime-boundaries','python/strings-bytes'],subject='python-types')

lesson('iterator-protocol','Python iterators: exhaustion and repeatable collection ownership',
'An iterator returns itself from iter() and supplies successive values through next(), raising StopIteration when exhausted.',
'The receipt batch retains an immutable tuple snapshot. Each call to iter(batch) creates a fresh iterator, so separate readers can traverse the batch independently. Holding one iterator and converting it to a list twice instead consumes it once and then produces an empty result. An iterable collection and a one-use iterator are different public contracts.',
'The tuple snapshot protects only the outer sequence. This fixture restricts receipt IDs to integers; accepting mutable receipt objects would retain their aliases. An iterator that reads a database cursor also owns a live I/O lifetime and cannot be treated like this in-memory batch. [[python/generators|Generator exhaustion]] and [[python/context-managers|Cleanup ownership]] explain that distinction.',
r'''class ReceiptBatch:
    def __init__(self, receipt_ids):
        candidate = tuple(receipt_ids)
        if any(type(identifier) is not int or identifier <= 0 for identifier in candidate):
            raise ValueError("positive receipt IDs required")
        self._receipt_ids = candidate
    def __iter__(self):
        return iter(self._receipt_ids)

batch = ReceiptBatch([41, 42])
reader = iter(batch)
print(list(reader))
print(list(reader))
print(list(batch))''','[41, 42]\n[]\n[41, 42]',
'Creating the tuple snapshot costs O(n) time and storage; creating an iterator is bounded. Materializing its remaining values into a list takes O(r) retained output.',
['Do not promise repeatable reads when returning the same iterator instance.','An outer tuple does not freeze mutable values stored inside it.'],['python/generators','python/tuples','python/iterator-interview'],subject='python-advanced')

lesson('descriptors','Python descriptors: field validation and attribute precedence',
'A descriptor is a class attribute whose type implements attribute-access hooks such as __get__ or __set__.',
'The managed quantity accepts exact integers between zero and one thousand. The descriptor records its field name during class creation, then validates before writing instance storage. Because it defines __set__, normal attribute lookup gives this data descriptor precedence over an instance dictionary entry with the public name. That prevents an accidental public-name assignment from bypassing this particular access path.',
'This is an application convention, not a security boundary. A caller with the object can edit its private dictionary directly or replace class behavior. Class access returns the descriptor itself; forgetting that case can attempt to read storage from None. [[python/properties|Properties]] uses the same attribute-management mechanism for a single field.',
r'''class BoundedQuantity:
    def __set_name__(self, owner, name):
        self.storage = "_" + name
    def __get__(self, instance, owner=None):
        if instance is None:
            return self
        return instance.__dict__[self.storage]
    def __set__(self, instance, value):
        if type(value) is not int or not 0 <= value <= 1000:
            raise ValueError("quantity out of range")
        instance.__dict__[self.storage] = value

class DispatchLine:
    quantity = BoundedQuantity()
    def __init__(self, quantity):
        self.quantity = quantity

line = DispatchLine(12)
try:
    line.quantity = True
except ValueError:
    print("boolean rejected")
line.__dict__["quantity"] = 999
print(line.quantity)
print(isinstance(DispatchLine.quantity, BoundedQuantity))''','boolean rejected\n12\nTrue',
'For these small integers, validation has bounded work and each instance stores one field value. Attribute hook calls add dispatch overhead; benchmark the application rather than assigning a universal descriptor cost.',
['Handle class access where instance is None.','Descriptors do not prevent a caller from changing private storage.'],['python/properties','python/classes','python/mro-super'],subject='python-advanced')

lesson('mro-super','Python super and method resolution: cooperate across mixins',
'Python super() continues attribute lookup after a selected class in the object’s method-resolution order.',
'The audit mixin and receipt mixin both extend the result returned by super(). The final pipeline therefore executes one ordered chain through both mixins and the base operation. A direct call to BasePolicy.tags would skip participants between the current class and the base. Cooperative composition requires compatible signatures and a shared agreement about who owns the result.',
'Every participant must preserve the call contract. A mixin that omits super can end the chain; one that passes an argument the next method cannot accept can fail at runtime. The returned list is newly allocated by the terminal method, so extending it does not mutate a class-level shared default. [[python/inheritance|Inheritance boundaries]] and [[python/function-arguments|Arguments]] are prerequisites.',
r'''class BasePolicy:
    def tags(self):
        return ["base"]
class ReceiptPolicy(BasePolicy):
    def tags(self):
        return super().tags() + ["receipt"]
class AuditPolicy(BasePolicy):
    def tags(self):
        return super().tags() + ["audit"]
class DispatchPolicy(AuditPolicy, ReceiptPolicy):
    pass

print([kind.__name__ for kind in DispatchPolicy.__mro__[:-1]])
print(DispatchPolicy().tags())''',"['DispatchPolicy', 'AuditPolicy', 'ReceiptPolicy', 'BasePolicy']\n['base', 'receipt', 'audit']",
'The tiny chain has fixed depth. Repeated list concatenation copies intermediate results; with a long chain and growing tags, total copied entries can exceed the final result size.',
['super refers to the next lookup position, not simply a named parent.','Keep cooperative signatures compatible through the whole chain.'],['python/inheritance','python/function-arguments','python/descriptors'],subject='python-advanced')

lesson('typing-protocol','Python Protocol: structural intent without runtime validation',
'A typing Protocol describes operations a static type checker expects an object to provide without requiring inheritance from that protocol.',
'The receipt renderer accepts a store with an amount method. The in-memory store supplies that method structurally. The function still checks the returned amount because a type annotation is not a runtime wire validator. A third-party implementation could return an invalid value despite its advertised annotation, or raise an I/O failure that the caller must handle.',
'The fixture runs without a static checker. It proves the runtime behavior of one implementation, not that every implementation passes a type checker. runtime_checkable protocols also cannot validate full argument/result semantics merely by checking attribute presence. [[python/type-hints|Annotations]] and [[python/json-validation|Input schemas]] solve separate problems.',
r'''from typing import Protocol

class ReceiptStore(Protocol):
    def amount(self, receipt_id: int) -> int: ...
class MemoryReceipts:
    def amount(self, receipt_id: int) -> int:
        return {41: 125}[receipt_id]

def render_amount(store: ReceiptStore, receipt_id: int) -> str:
    amount = store.amount(receipt_id)
    if type(amount) is not int or amount < 0:
        raise ValueError("invalid minor-unit amount")
    return f"R{receipt_id}:{amount}"

print(render_amount(MemoryReceipts(), 41))''','R41:125',
'An annotation adds no database lookup optimization. The fixture performs one dictionary lookup with expected bounded hash work; a remote store would add its own latency and failure budget.',
['A Protocol annotation does not validate an external implementation at runtime.','Specify whether missing IDs raise, return None or produce a domain result.'],['python/type-hints','python/classes','python/json-validation'],subject='python-advanced')

lesson('process-pools','Python process pools: importable workers and serialization costs',
'ProcessPoolExecutor executes submitted operations in separate processes and transfers supported inputs and results through serialization.',
'The receipt checksum is defined at module scope so spawned workers can import it. The main guard creates a two-worker pool using an explicit spawn context, avoiding accidental pool creation during worker import. map returns results in input order even if tasks finish in another order. The fixture submits only three bounded integers and uses no external service.',
'Pool setup and data transfer can cost more than the arithmetic here. A closure or open connection is not an appropriate worker payload. Waiting with a timeout also does not terminate arbitrary already-running work; executor shutdown can still wait for it. [[python/thread-pools|Threads]] and [[python/subprocess-boundaries|Child process ownership]] need different shutdown decisions.',
r'''from concurrent.futures import ProcessPoolExecutor
from multiprocessing import get_context

def receipt_checksum(receipt_id):
    if type(receipt_id) is not int or not 1 <= receipt_id <= 1000:
        raise ValueError("receipt ID out of range")
    return receipt_id * receipt_id % 97

if __name__ == "__main__":
    with ProcessPoolExecutor(max_workers=2, mp_context=get_context("spawn")) as pool:
        results = list(pool.map(receipt_checksum, [41, 42, 43]))
    print(results)''','[32, 18, 6]',
'For n fixed-size jobs, serialization and collection grow with n, plus process startup cost. This fixture is not a CPU speed comparison and does not bound an arbitrary worker’s memory or execution time.',
['Keep spawned worker definitions importable and pool startup behind the main guard.','A future wait timeout is not a guarantee that running work has stopped.'],['python/modules','python/thread-pools','python/subprocess-boundaries'],subject='python-advanced')

lesson('subprocess-boundaries','Python subprocess: argument vectors, exit codes and bounded fixtures',
'subprocess.run starts a child operation, waits for completion and reports its exit status or a waiting failure.',
'The fixture starts the current interpreter with an explicit argument vector and shell disabled. A literal dollar expression is printed as data instead of being evaluated by a command shell. A second child exits with status three; check=True turns that nonzero status into CalledProcessError. The caller reads the exit status without pretending a failed command succeeded.',
'The child programs are fixed and emit tiny output. capture_output retains all child output, so this is not safe handling for arbitrary noisy commands. The timeout controls this run’s wait and child cleanup, not every descendant process an application may start. External tools need output limits, trusted executable selection and an OS-specific process-tree policy. [[python/process-pools|Worker processes]] is a separate API.',
r'''import subprocess
import sys

result = subprocess.run(
    [sys.executable, "-I", "-c", "import sys; print(sys.argv[1])", "$(receipt)"],
    capture_output=True, text=True, check=True, timeout=3,
)
print(result.stdout.strip())
try:
    subprocess.run([sys.executable, "-I", "-c", "raise SystemExit(3)"],
                   check=True, capture_output=True, timeout=3)
except subprocess.CalledProcessError as failure:
    print("exit:", failure.returncode)''','$(receipt)\nexit: 3',
'Child startup dominates these small operations. Captured output uses O(b) memory for b output bytes; timeout is not a byte budget.',
['Do not interpolate untrusted fields into a shell command.','capture_output can retain unbounded output from an untrusted executable.'],['python/process-pools','python/exceptions','python/receipt-cli'],subject='python-advanced')

lesson('thread-locks','Python locks: protect the complete inventory transition',
'A thread lock coordinates access to a shared application invariant across cooperating threads.',
'The stock reservation holds its lock across the availability check and quantity decrement. Protecting only the assignment would still let two callers both observe the same remaining stock. Thirty callers each request one unit from twenty available units; accepted results and final stock are deterministic even though the identities of successful callers depend on scheduling.',
'Every access to the invariant must follow the locking contract. A lock does not make unrelated direct field writes safe, and holding it during a remote call can stall all reservation work. This program does not assume a GIL makes a multi-step business transition atomic. [[python/inventory-project|Staged batches]] handles a different failure boundary: rejecting an entire multi-item request.',
r'''from concurrent.futures import ThreadPoolExecutor
from threading import Lock

class Stock:
    def __init__(self, available):
        self._available = available
        self._lock = Lock()
    def reserve_one(self):
        with self._lock:
            if self._available == 0:
                return False
            self._available -= 1
            return True
    def remaining(self):
        with self._lock:
            return self._available

stock = Stock(20)
with ThreadPoolExecutor(max_workers=4) as pool:
    accepted = list(pool.map(lambda _: stock.reserve_one(), range(30)))
print(sum(accepted), stock.remaining())''','20 0',
'The fixture does O(n) small transitions but serializes the shared state section. Locks can add waiting; no throughput claim follows from adding worker threads.',
['Protect the check and mutation together.','Do not hold this lock while waiting for an external service.'],['python/thread-pools','python/inventory-project','python/async-queues'],subject='python-advanced')

lesson('async-queues','Python asyncio.Queue: backpressure and completion accounting',
'An asyncio.Queue coordinates producer and consumer coroutines, with maxsize limiting the number of queued entries.',
'The producer awaits each put into a capacity-two queue, so it pauses when buffered work has not been removed. The consumer acknowledges each retrieved item in finally, including the sentinel used to stop it. join waits for acknowledgements, not for proof of a business success. The program records completed receipt IDs in one consumer, which preserves their order.',
'This is a finite local pipeline. A failing consumer needs an explicit supervisor and producer cancellation policy; otherwise a producer or join can wait forever. maxsize bounds queued entries, not the bytes in each entry or already-running work. [[python/async-task-groups|Task supervision]] and [[python/async-deadlines|Deadlines]] complete those ownership decisions.',
r'''import asyncio

async def pipeline():
    queue = asyncio.Queue(maxsize=2)
    completed = []
    async def consume():
        while True:
            receipt_id = await queue.get()
            try:
                if receipt_id is None:
                    return
                completed.append(receipt_id)
            finally:
                queue.task_done()
    worker = asyncio.create_task(consume())
    for receipt_id in (41, 42, 43):
        await queue.put(receipt_id)
    await queue.put(None)
    await queue.join()
    await worker
    return completed

print(asyncio.run(pipeline()))''','[41, 42, 43]',
'For n fixed-size receipts the pipeline does O(n) queue work. Buffered entries stay within capacity, but the displayed completion list retains O(n) IDs.',
['task_done acknowledges queue bookkeeping, not a successful durable write.','Bound entry bytes and running work separately from queue length.'],['python/async-task-groups','python/async-deadlines','python/counter-deque'],subject='python-advanced')

lesson('async-deadlines','Python asyncio timeout: cancellation and cleanup ownership',
'asyncio.timeout limits an asynchronous context’s waiting period by cancelling its task when the deadline expires.',
'The local operation waits on an event that is never set. A short timeout cancels that wait; the operation’s finally clause marks cleanup before the caller handles TimeoutError outside the context. The test observes cleanup rather than timing a sleep and claiming an exact elapsed duration. The result says nothing about a remote server completing or rolling back work.',
'Cancellation is cooperative. Blocking code in the event-loop thread prevents timely scheduling, and swallowing CancelledError can break the enclosing timeout contract. A cancelled HTTP request may already have caused a remote mutation; retries need idempotency and an unknown-outcome policy. [[python/async-task-groups|Supervision]] and [[python/sqlite-cli-project|Local transactions]] cover different guarantees.',
r'''import asyncio

async def inspect_timeout():
    released = False
    async def wait_for_receipt():
        nonlocal released
        try:
            await asyncio.Event().wait()
        finally:
            released = True
    try:
        async with asyncio.timeout(0.01):
            await wait_for_receipt()
    except TimeoutError:
        print("deadline expired")
    print("cleanup:", released)

asyncio.run(inspect_timeout())''','deadline expired\ncleanup: True',
'The fixture retains one task and one event. Scheduling delay depends on the runtime and machine load; the timeout is a deadline policy, not a precise latency benchmark.',
['Handle TimeoutError outside the timeout context.','Cancellation cannot undo an already-committed remote mutation.'],['python/async-task-groups','python/async-queues','python/exceptions'],subject='python-advanced')

lesson('bounded-csv','Python CSV ingestion: cap bytes, rows and fields before publication',
'A bounded CSV import validates its byte budget, row count and field schema before publishing accepted records.',
'The importer receives a byte buffer no larger than 512 bytes, decodes strict UTF-8 and requires a receipt_id,amount_minor header. It stages at most three records, rejects duplicate IDs and accepts only bounded ASCII decimal fields. The return value appears only after the complete import passes, so callers cannot mistake a yielded prefix for an accepted batch.',
'The byte input is already materialized; a listening server must enforce the byte limit while receiving it. This fixture does not handle spreadsheet formula export, uploaded file storage or authorization. CSV parsing alone does not establish numeric units or identity. [[python/csv-import|CSV syntax]] and [[python/sqlite-cli-project|Transactional storage]] separate format handling from persistence.',
r'''import csv
import io

def import_receipts(payload):
    if type(payload) is not bytes or len(payload) > 512:
        raise ValueError("byte budget")
    reader = csv.reader(io.StringIO(payload.decode("utf-8", errors="strict")), strict=True)
    if next(reader, None) != ["receipt_id", "amount_minor"]:
        raise ValueError("header mismatch")
    staged = {}
    for row in reader:
        if len(staged) == 3 or len(row) != 2:
            raise ValueError("row budget or shape")
        if any(not field or len(field) > 6 or not field.isascii() or not field.isdecimal() for field in row):
            raise ValueError("bounded decimal fields required")
        receipt_id, amount = map(int, row)
        if receipt_id <= 0 or amount <= 0 or receipt_id in staged:
            raise ValueError("invalid or duplicate receipt")
        staged[receipt_id] = amount
    return staged

print(import_receipts(b"receipt_id,amount_minor\n41,125\n42,75\n"))
try:
    import_receipts(b"receipt_id,amount_minor\n41,125\n41,75\n")
except ValueError:
    print("duplicate batch rejected")''',"{41: 125, 42: 75}\nduplicate batch rejected",
'Parsing costs O(b) for b bounded input bytes, with staged storage O(r) for r accepted rows. The input buffer and decoded text also consume memory; row limits alone do not bound upload memory.',
['Enforce the byte budget during reception as well as at this function boundary.','Do not insert records as they are parsed if the whole batch must pass first.'],['python/csv-import','python/regex-validation','python/sqlite-cli-project'],subject='python-examples')

lesson('merge-sort','Python merge sort: stable ordering without editing the input',
'Merge sort orders a sequence by sorting smaller runs and merging them while preserving a declared equal-key order.',
'The receipt sorter accepts a bounded list of integer amount and string ID pairs. During merge it takes an equal-key entry from the left run first, preserving the input order of equal amounts. The caller’s list remains unchanged. This stability is useful when a previous import order carries meaning that should survive amount-based sorting.',
'The fixture caps input at 128 records and rejects booleans as amounts. A comparison function with side effects or inconsistent ordering would invalidate the proof. Production Python already provides a stable built-in sort; this program teaches merge mechanics rather than recommending a replacement. [[python/sorting|Built-in sorting]] defines the practical default.',
r'''def sort_receipts(receipts):
    if len(receipts) > 128 or any(type(amount) is not int or type(identifier) is not str for amount, identifier in receipts):
        raise ValueError("bounded receipt pairs required")
    def sort_run(records):
        if len(records) < 2:
            return records.copy()
        middle = len(records) // 2
        left, right = sort_run(records[:middle]), sort_run(records[middle:])
        merged, left_index, right_index = [], 0, 0
        while left_index < len(left) and right_index < len(right):
            if left[left_index][0] <= right[right_index][0]:
                merged.append(left[left_index]); left_index += 1
            else:
                merged.append(right[right_index]); right_index += 1
        return merged + left[left_index:] + right[right_index:]
    return sort_run(receipts)

receipts = [(125, "R41"), (75, "R42"), (125, "R43")]
print(sort_receipts(receipts))
print(receipts)''',"[(75, 'R42'), (125, 'R41'), (125, 'R43')]\n[(125, 'R41'), (75, 'R42'), (125, 'R43')]",
'The implementation performs O(n log n) comparisons and copied references, with O(n) peak auxiliary entries plus O(log n) call depth. Slicing and intermediate list concatenation add allocation work.',
['Choosing the right run on equal keys would change stability.','Use the built-in sort when implementing an application rather than studying the algorithm.'],['python/sorting','python/binary-search','python/copy-deepcopy'],subject='python-dsa')

lesson('topological-sort','Python topological sort: dependency order and cycle rejection',
'A topological ordering places each prerequisite before its dependent operation in a directed acyclic graph.',
'The pipeline graph lists all operations explicitly. The sorter computes indegrees and takes ready operations from a min-heap, giving a reproducible lexical tie rule. Removing an operation decrements the indegree of its dependents. If fewer operations are emitted than were declared, a cycle prevented a valid complete ordering.',
'The function rejects undeclared endpoints, duplicate edges and oversized graphs before scheduling. A cycle rejection occurs before any application task runs: this program only returns a plan. A valid order does not imply a task will succeed or that executing every ready task concurrently is safe. [[python/async-queues|Task queues]] needs a separate execution policy.',
r'''import heapq

def dependency_order(graph):
    if len(graph) > 64 or any(type(node) is not str or len(edges) > 64 for node, edges in graph.items()):
        raise ValueError("graph budget")
    indegree = dict.fromkeys(graph, 0)
    for edges in graph.values():
        if len(edges) != len(set(edges)) or any(target not in graph for target in edges):
            raise ValueError("invalid dependency")
        for target in edges:
            indegree[target] += 1
    ready = [node for node, count in indegree.items() if count == 0]
    heapq.heapify(ready)
    ordered = []
    while ready:
        node = heapq.heappop(ready)
        ordered.append(node)
        for target in graph[node]:
            indegree[target] -= 1
            if indegree[target] == 0:
                heapq.heappush(ready, target)
    if len(ordered) != len(graph):
        raise ValueError("dependency cycle")
    return ordered

print(dependency_order({"import": ["validate"], "validate": ["publish"], "publish": []}))
try:
    dependency_order({"import": ["publish"], "publish": ["import"]})
except ValueError:
    print("cycle rejected")''',"['import', 'validate', 'publish']\ncycle rejected",
'For V nodes and E edges, validation and indegrees take O(V+E) expected hash work; heap tie ordering adds O(V log V). Retained bookkeeping is O(V), excluding the caller’s graph.',
['A missing endpoint is invalid input, not an invisible extra node.','A topological plan does not provide transaction rollback for failing tasks.'],['python/graph-bfs','python/async-queues','python/dijkstra'],subject='python-dsa')

lesson('dijkstra','Python Dijkstra: nonnegative weights and stale heap entries',
'Dijkstra’s algorithm finds shortest path costs from a source when every edge weight is nonnegative.',
'The route graph uses integer minute costs and integer node IDs. A relaxation may improve a node after an older cost was already placed in the heap; the algorithm skips that stale entry rather than expanding it again. Unreachable nodes retain None in the public result, so zero remains a valid source cost instead of being overloaded as failure.',
'Negative weights, booleans, undeclared nodes and oversized adjacency lists are rejected before traversal. This algorithm does not solve negative-edge paths or represent time-dependent travel rules. The heap can contain several entries for one node, so its storage cannot be described as one slot per node. [[python/graph-bfs|BFS]] is the simpler choice for unit-cost edges.',
r'''import heapq

def route_costs(graph, source):
    if type(source) is not int or source not in graph or len(graph) > 64:
        raise ValueError("source or graph budget")
    for node, edges in graph.items():
        if type(node) is not int or len(edges) > 64:
            raise ValueError("node budget")
        for target, cost in edges:
            if type(target) is not int or target not in graph or type(cost) is not int or not 0 <= cost <= 1000:
                raise ValueError("nonnegative bounded edges required")
    distances = dict.fromkeys(graph, None)
    distances[source] = 0
    pending = [(0, source)]
    while pending:
        distance, node = heapq.heappop(pending)
        if distance != distances[node]:
            continue
        for target, cost in graph[node]:
            candidate = distance + cost
            if distances[target] is None or candidate < distances[target]:
                distances[target] = candidate
                heapq.heappush(pending, (candidate, target))
    return distances

print(route_costs({0: [(1, 9), (2, 2)], 1: [], 2: [(1, 3)], 3: []}, 0))
try:
    route_costs({0: [(1, -1)], 1: []}, 0)
except ValueError:
    print("negative edge rejected")''',"{0: 0, 1: 5, 2: 2, 3: None}\nnegative edge rejected",
'This lazy-duplicate heap implementation uses O(V+E log(E+1)) work and O(V+E) extra storage in the worst case, with bounded integer operands. Graph validation is part of the measured operation contract.',
['Reject negative weights before using this greedy relaxation.','Do not expand a stale heap cost or claim the heap contains only V entries.'],['python/graph-bfs','python/topological-sort','python/heap-top-k'],subject='python-dsa')

lesson('union-find','Python union-find: connected groups with path compression',
'Union-find maintains disjoint groups by mapping each member to a representative and joining representatives when groups merge.',
'The receipt-group fixture assigns bounded integer indexes. find follows parent links and shortens them toward the root; union attaches the smaller tree under the larger one. Repeatedly joining an already-connected pair returns False and leaves the group count unchanged. Representative indexes are implementation details, so callers ask whether two members share a root rather than requiring a specific root number.',
'This structure handles additions to connectivity. Removing an edge cannot simply undo a union because previous paths and size records have already changed. The class accepts only indexes within its declared capacity and rejects bool. [[python/graph-bfs|Graph traversal]] can rebuild connectivity when deletions change the graph.',
r'''class ReceiptGroups:
    def __init__(self, count):
        if type(count) is not int or not 0 <= count <= 128:
            raise ValueError("group budget")
        self.parent = list(range(count))
        self.size = [1] * count
        self.groups = count
    def find(self, member):
        if type(member) is not int or not 0 <= member < len(self.parent):
            raise ValueError("member index")
        while member != self.parent[member]:
            self.parent[member] = self.parent[self.parent[member]]
            member = self.parent[member]
        return member
    def union(self, first, second):
        left, right = self.find(first), self.find(second)
        if left == right:
            return False
        if self.size[left] < self.size[right]:
            left, right = right, left
        self.parent[right] = left
        self.size[left] += self.size[right]
        self.groups -= 1
        return True

groups = ReceiptGroups(4)
print(groups.union(0, 1), groups.union(1, 2), groups.union(0, 2))
print(groups.find(0) == groups.find(2), groups.groups)''','True True False\nTrue 2',
'Initialization takes O(n) space and time. Union by size with path compression gives very small amortized parent work over a sequence of operations; an individual first find can still follow a logarithmic-depth tree before compression.',
['Do not expose representative identity as a permanent business ID.','Deleting an edge is not supported by reversing one parent assignment.'],['python/graph-bfs','python/dictionaries','python/tree-traversal'],subject='python-dsa')

lesson('trie-prefix','Python trie: exact words, prefixes and node allocation',
'A trie indexes a key by storing its successive characters along a path, with a separate marker for a complete key.',
'The label index stores nonempty lowercase ASCII words of at most 32 characters. The endpoint marker distinguishes the stored label ledger from the prefix led. Duplicate insertion returns False rather than creating another label. Prefix lookup tests whether a path exists; exact lookup also requires the endpoint marker.',
'The fixture permits at most 64 distinct labels and retains nodes for their shared prefixes. It does not support deletion, Unicode normalization or ranked suggestions. A prefix index for user display labels must first define a text policy rather than silently lowercasing every identifier. [[python/unicode-normalization|Normalization]] and [[python/dictionaries|Hash keys]] describe those prior decisions.',
r'''class LabelTrie:
    def __init__(self):
        self.root = {}
        self.count = 0
    def checked(self, label):
        if type(label) is not str or not 1 <= len(label) <= 32 or any(not "a" <= character <= "z" for character in label):
            raise ValueError("lowercase ASCII label required")
    def insert(self, label):
        self.checked(label)
        if self.contains(label):
            return False
        if self.count == 64:
            raise ValueError("label budget")
        node = self.root
        for character in label:
            node = node.setdefault(character, {})
        node["$"] = True
        self.count += 1
        return True
    def lookup(self, label):
        self.checked(label)
        node = self.root
        for character in label:
            if character not in node:
                return None
            node = node[character]
        return node
    def contains(self, label):
        node = self.lookup(label)
        return node is not None and "$" in node
    def has_prefix(self, label):
        return self.lookup(label) is not None

labels = LabelTrie()
print(labels.insert("ledger"), labels.insert("ledger"))
print(labels.contains("led"), labels.has_prefix("led"))
print(labels.contains("ledger"))''','True False\nFalse True\nTrue',
'For a label of length L, traversal takes expected O(L) dictionary work. Allocated nodes are bounded by the total stored characters; Python dictionary/object overhead can dominate tiny labels.',
['A prefix path is not proof that the prefix itself was inserted.','Do not claim tries always use less memory than a hash set.'],['python/dictionaries','python/unicode-normalization','python/kmp-search'],subject='python-dsa')

lesson('kmp-search','Python prefix-function search: overlapping matches without rescanning',
'Prefix-function string search reuses the length of an already-matched prefix when a mismatch occurs.',
'The importer scans a bounded text field for every occurrence of a nonempty marker, including overlapping occurrences. The prefix array tells it how much matched state remains useful after a mismatch or a complete match. Returning positions in ascending order follows the left-to-right scan; it does not require sorting the result.',
'The program compares code points exactly. It does not normalize text, decode bytes or treat visually equal sequences as equal. Empty markers are rejected rather than implicitly matching every boundary. Use Python’s built-in string operations in ordinary applications unless the all-overlaps or streaming contract justifies a separate implementation. [[python/unicode-normalization|Text equivalence]] must be decided before matching.',
r'''def marker_positions(text, marker):
    if type(text) is not str or type(marker) is not str or len(text) > 4096 or not 1 <= len(marker) <= 128:
        raise ValueError("text or marker budget")
    prefix = [0] * len(marker)
    matched = 0
    for position in range(1, len(marker)):
        while matched and marker[position] != marker[matched]:
            matched = prefix[matched - 1]
        if marker[position] == marker[matched]:
            matched += 1
        prefix[position] = matched
    found, matched = [], 0
    for position, character in enumerate(text):
        while matched and character != marker[matched]:
            matched = prefix[matched - 1]
        if character == marker[matched]:
            matched += 1
        if matched == len(marker):
            found.append(position - len(marker) + 1)
            matched = prefix[matched - 1]
    return found

print(marker_positions("R41|R41|R42", "R41"))
print(marker_positions("aaaa", "aa"))''','[0, 4]\n[0, 1, 2]',
'For text length n and marker length m, prefix construction plus scanning takes O(n+m) comparisons. Storage is O(m+k) for the prefix array and k returned matches.',
['Reset to the stored prefix length after a full match to retain overlapping matches.','Do not conflate code-point positions with encoded byte offsets.'],['python/strings-bytes','python/unicode-normalization','python/regex-validation'],subject='python-dsa')

lesson('longest-common-subsequence','Python longest common subsequence: rolling-row DP and its limits',
'The longest common subsequence length counts the largest order-preserving selection of matching values from two sequences without requiring adjacent matches.',
'The fixture compares two bounded event-label strings. Matching characters extend the previous row’s diagonal result; differing characters retain the larger result from dropping one side’s current character. Only the previous and current rows are needed when the result is a length. Keeping a complete path reconstruction would need another storage or recomputation plan.',
'This is not longest common substring and not an edit script. The string inputs are limited to 128 code points; their equality is exact. A document comparison service also needs tokenization and a work budget because the product of input lengths drives this recurrence. [[python/kmp-search|Contiguous marker matching]] answers a different question.',
r'''def common_event_length(first, second):
    if type(first) is not str or type(second) is not str or max(len(first), len(second)) > 128:
        raise ValueError("sequence budget")
    if len(first) < len(second):
        first, second = second, first
    previous = [0] * (len(second) + 1)
    for first_event in first:
        current = [0]
        for index, second_event in enumerate(second, 1):
            current.append(previous[index - 1] + 1 if first_event == second_event
                           else max(previous[index], current[-1]))
        previous = current
    return previous[-1]

print(common_event_length("PACK", "PARK"))
print(common_event_length("", "PACK"))''','3\n0',
'Time is O(n*m), with O(min(n,m)) row storage. The output is a length, so this program does not retain the actual chosen subsequence.',
['A subsequence can skip entries; a substring cannot.','A linear-space length result is not automatically a linear-space reconstruction.'],['python/memoization','python/kmp-search','python/knapsack'],subject='python-dsa')

lesson('knapsack','Python 0/1 knapsack: descending capacity prevents item reuse',
'0/1 knapsack selects each available item at most once while maximizing total value under a capacity limit.',
'The cargo fixture accepts positive integer weights and nonnegative integer values. It visits capacities from high to low for each item, so the lower-capacity state still belongs to the previous item set. Ascending capacity would let the current item feed its own later updates and change the problem into a reusable-item recurrence.',
'The function caps capacity at 256 and item count at 32, rejects bool and returns only the optimum value. It does not identify a selected load or model fractional cargo. The zero-capacity and empty-item results are valid zero values, distinct from a parser failure. [[python/memoization|Reusable package counts]] deliberately solves another recurrence.',
r'''def cargo_value(items, capacity):
    if type(capacity) is not int or not 0 <= capacity <= 256 or len(items) > 32:
        raise ValueError("cargo budget")
    if any(type(weight) is not int or type(value) is not int or weight <= 0 or value < 0 for weight, value in items):
        raise ValueError("positive weight and nonnegative value required")
    best = [0] * (capacity + 1)
    for weight, value in items:
        for available in range(capacity, weight - 1, -1):
            best[available] = max(best[available], best[available - weight] + value)
    return best[capacity]

print(cargo_value([(2, 6), (3, 8), (4, 9)], 5))
print(cargo_value([(2, 6)], 4))''','14\n6',
'Time is O(n*C) and storage O(C) for capacity C and n items, aside from integer digit costs. This is pseudo-polynomial in numeric capacity, not polynomial in the length of its textual encoding.',
['Ascending updates would allow the same item more than once.','Do not advertise a selected-item list when returning only its total value.'],['python/memoization','python/longest-common-subsequence','python/input-exercise'],subject='python-dsa')

lesson('linked-list-reversal','Python linked-list reversal: validate cycles before changing links',
'Reversing a singly linked list replaces each node’s next reference so traversal follows the original nodes in reverse order.',
'The program first walks the chain, rejecting a cycle or more than 64 nodes before it changes any link. It then saves each successor, points the current node at the previous node and advances. The caller receives the new head; the former head is now the tail. These are the same node objects, so every external alias still refers to its original node.',
'The validation set uses extra memory to guarantee rejection before mutation. Claiming constant extra storage for this whole operation would therefore be wrong, even though the pointer-replacement phase alone uses three references. Concurrent mutation and objects that override attribute access are outside this fixture’s contract. [[python/copy-deepcopy|Graph copies]] does not describe this in-place ownership change.',
r'''class DispatchNode:
    def __init__(self, receipt_id, next_node=None):
        self.receipt_id = receipt_id
        self.next = next_node

def reverse_chain(head):
    seen, current = set(), head
    while current is not None:
        if type(current) is not DispatchNode or id(current) in seen or len(seen) == 64:
            raise ValueError("cycle, node type or chain budget")
        seen.add(id(current)); current = current.next
    previous, current = None, head
    while current is not None:
        successor = current.next
        current.next = previous
        previous, current = current, successor
    return previous

head = DispatchNode(41, DispatchNode(42, DispatchNode(43)))
old_head = head
head = reverse_chain(head)
values = []
while head is not None:
    values.append(head.receipt_id); head = head.next
print(values)
print(old_head.next is None)''','[43, 42, 41]\nTrue',
'Two passes give O(n) work. Cycle/budget validation stores O(n) identities; pointer replacement itself has O(1) temporary reference storage.',
['Retain the successor before replacing the next reference.','Describe validation memory rather than claiming the complete safe operation is constant-space.'],['python/python-variables','python/copy-deepcopy','python/tree-traversal','java/linkedlist'],subject='python-dsa')

lesson('tree-traversal','Python iterative tree traversal: shared nodes are not a tree',
'An iterative tree traversal stores pending nodes explicitly instead of using one recursive Python call per level.',
'The dispatch hierarchy lists integer node IDs and ordered child lists. The walker pushes children in reverse order so a LIFO stack visits them in the original child order. A visited set rejects any repeated reachable node, including a cycle or two parents sharing one child, because this operation promises a tree rather than a general graph walk.',
'All declared child endpoints must exist. The root traversal ignores disconnected components but validates their edge shapes first; the lesson does not claim it produces a complete traversal of every node in a forest. The graph and child lists are bounded and must remain unchanged during the walk. [[python/graph-bfs|Graph BFS]] intentionally permits a different revisit policy.',
r'''def hierarchy_preorder(children, root):
    if type(root) is not int or root not in children or len(children) > 64:
        raise ValueError("root or hierarchy budget")
    if any(type(node) is not int or len(edges) > 64 or any(type(child) is not int or child not in children for child in edges)
           for node, edges in children.items()):
        raise ValueError("invalid child reference")
    pending, seen, ordered = [root], set(), []
    while pending:
        node = pending.pop()
        if node in seen:
            raise ValueError("reachable cycle or shared child")
        seen.add(node); ordered.append(node)
        pending.extend(reversed(children[node]))
    return ordered

print(hierarchy_preorder({0: [1, 2], 1: [3], 2: [], 3: []}, 0))
try:
    hierarchy_preorder({0: [1, 2], 1: [2], 2: []}, 0)
except ValueError:
    print("shared child rejected")''','[0, 1, 3, 2]\nshared child rejected',
'Validation scans O(V+E) declared data. Traversal stores visited nodes and pending edges; for a valid reachable tree this is O(r) extra references for r reached nodes. General rejected graphs can enqueue more pending references before a repeat is found.',
['Reversing the child push order is needed for left-to-right preorder.','A tree promise must reject shared reachable children as well as cycles.'],['python/graph-bfs','python/topological-sort','python/linked-list-reversal'],subject='python-dsa')

lesson('iterator-interview','Python iterator interview: lazy calls, exhaustion and partial failure',
'An iterator interview trace asks when work executes, which values are consumed and what remains after a failure.',
'The receipt generator records a label immediately before each yield. Constructing it does not run that body; next consumes the first value; list consumes the rest. The final read returns no values because the iterator is exhausted. This trace tests execution timing rather than memorizing the output of an arbitrary arithmetic puzzle.',
'A generator may perform external writes before yielding and may fail after emitting a prefix. Laziness alone provides neither rollback nor bounded memory: a consumer can immediately materialize every yielded result. Read the ownership rule before moving a side effect into an iterator. [[python/bounded-csv|Staged import]] deliberately returns only a completely validated batch.',
r'''def receipt_stream(trace):
    for receipt_id in (41, 42):
        trace.append("read:" + str(receipt_id))
        yield receipt_id

trace = []
stream = receipt_stream(trace)
print(trace)
print(next(stream))
print(trace)
print(list(stream))
print(list(stream))''',"[]\n41\n['read:41']\n[42]\n[]",
'The generator itself retains bounded loop state here, but the trace grows with every produced value and list(stream) allocates all remaining output. Report consumer storage as well as iterator state.',
['Creating a generator does not execute its body immediately.','A consumed prefix is not undone if later iteration fails.'],['python/generators','python/iterator-protocol','python/bounded-csv'],subject='python-interview')

lesson('rollback-exercise','Python rollback exercise: reject a later failure without keeping earlier edits',
'A staged-state exercise verifies that a rejected batch leaves the previously accepted state unchanged.',
'The inventory adjustment copies current quantities into a candidate map, applies validated changes there, and returns the replacement only after every change passes. The first edit in the failing fixture would be valid, but a later edit would make stock negative. The caller keeps its original dictionary because the function never mutates it.',
'The operation accepts at most 32 changes, known keys and bounded exact integers. This is local state staging, not a database transaction or protection against another thread replacing stock at the same time. Extend the exercise by checking empty batches, duplicate key edits and a failure at each possible position. [[python/thread-locks|Shared state]] requires a wider critical section.',
r'''def adjusted_stock(stock, changes):
    if len(changes) > 32 or any(type(value) is not int or not 0 <= value <= 1000 for value in stock.values()):
        raise ValueError("stock budget")
    candidate = stock.copy()
    for label, delta in changes:
        if label not in candidate or type(delta) is not int or abs(delta) > 1000:
            raise ValueError("invalid adjustment")
        quantity = candidate[label] + delta
        if not 0 <= quantity <= 1000:
            raise ValueError("quantity out of range")
        candidate[label] = quantity
    return candidate

stock = {"paper": 12, "ink": 4}
try:
    adjusted_stock(stock, [("paper", -2), ("ink", -5)])
except ValueError:
    print("batch rejected")
print(stock)
print(adjusted_stock(stock, [("paper", -2)]))''',"batch rejected\n{'paper': 12, 'ink': 4}\n{'paper': 10, 'ink': 4}",
'Copying s stock entries costs O(s) time and storage, then c changes cost expected O(c) dictionary work. The fixture does not cap the caller’s pre-existing map size; an external service must set that limit too.',
['Mutating the original map and trying to undo edits is a different failure contract.','A returned replacement must still be published under an appropriate concurrency policy.'],['python/inventory-project','python/thread-locks','python/sqlite-cli-project'],subject='python-exercises')

lesson('sqlite-cli-project','Python SQLite project: transactional batches, duplicate IDs and reopen checks',
'A SQLite receipt ledger stores a validated batch in one database transaction and checks accepted state after reopening its database file.',
'The batch parser requires positive bounded exact integers and distinct IDs before starting inserts. SQL placeholders bind values. The connection context commits successful work and rolls back a failing batch; a duplicate primary key in a later insert therefore rejects the entire attempted transaction. Reopening the local database verifies that previously accepted receipts are present independently of the original connection.',
'The schema uses a primary key and a positive-amount check as a second boundary. The program owns its temporary directory and explicitly closes connections; the connection context does not itself close a connection. Reopen tests do not simulate a power failure or certify a deployment filesystem’s durability. This project has no authentication, migration runner or remote multi-writer service. [[python/sqlite-transactions|Transaction basics]] and [[python/bounded-csv|Import bounds]] feed it.',
r'''import sqlite3
import tempfile
from pathlib import Path

def accept_batch(connection, rows):
    if len(rows) > 32:
        raise ValueError("batch budget")
    identifiers = set()
    for receipt_id, amount in rows:
        if type(receipt_id) is not int or type(amount) is not int or not 1 <= receipt_id <= 100000 or not 1 <= amount <= 1000000 or receipt_id in identifiers:
            raise ValueError("invalid receipt batch")
        identifiers.add(receipt_id)
    with connection:
        connection.executemany("INSERT INTO receipts(receipt_id, amount_minor) VALUES (?, ?)", rows)

with tempfile.TemporaryDirectory() as directory:
    database = Path(directory) / "receipts.db"
    connection = sqlite3.connect(database)
    try:
        connection.execute("CREATE TABLE receipts(receipt_id INTEGER PRIMARY KEY, amount_minor INTEGER NOT NULL CHECK(amount_minor > 0))")
        accept_batch(connection, [(41, 125), (42, 75)])
        try:
            accept_batch(connection, [(43, 90), (41, 20)])
        except sqlite3.IntegrityError:
            print("duplicate transaction rolled back")
    finally:
        connection.close()
    reopened = sqlite3.connect(database)
    try:
        print(reopened.execute("SELECT receipt_id, amount_minor FROM receipts ORDER BY receipt_id").fetchall())
    finally:
        reopened.close()''',"duplicate transaction rolled back\n[(41, 125), (42, 75)]",
'Validation uses O(r) IDs for r rows; insertion cost depends on the database indexes, journaling and filesystem. SELECT allocates the displayed result rows. No constant database write latency is claimed.',
['A connection context manages transaction outcome, not connection closing.','A clean reopen test does not prove power-loss recovery.'],['python/sqlite-transactions','python/bounded-csv','python/atomic-report-project','spring/data-transactions'],subject='python-projects')

lesson('atomic-report-project','Python file project: stage a report before replacing the visible file',
'Staged file publication writes a complete candidate before replacing the pathname readers use for the accepted report.',
'The receipt summary validates all bounded integer amounts before opening its candidate file. It creates that file in the target directory, writes UTF-8 text, flushes the language buffer and requests fsync on the file before os.replace. A failed validation leaves the prior report visible. Finally removes a leftover candidate if an I/O failure prevented replacement.',
'The project uses an owned temporary directory and a fixed target name. It does not defend an attacker-controlled directory, coordinate multiple writers or prove crash durability. A deployment needs platform-specific directory synchronization, permission preservation and recovery tests. A replacement can fail across filesystems, which is why the candidate is created beside the target. [[python/pathlib-files|Path ownership]] and [[python/sqlite-cli-project|Database transactions]] provide different publication primitives.',
r'''import os
import tempfile
from pathlib import Path

def publish_report(target, amounts):
    if len(amounts) > 32 or any(type(amount) is not int or not 0 <= amount <= 1000000 for amount in amounts):
        raise ValueError("report amounts")
    candidate = None
    try:
        with tempfile.NamedTemporaryFile(mode="w", encoding="utf-8", dir=target.parent, delete=False) as output:
            candidate = Path(output.name)
            output.write("total_minor=" + str(sum(amounts)) + "\n")
            output.flush()
            os.fsync(output.fileno())
        os.replace(candidate, target)
    finally:
        if candidate is not None:
            candidate.unlink(missing_ok=True)

with tempfile.TemporaryDirectory() as directory:
    target = Path(directory) / "report.txt"
    publish_report(target, [125, 75])
    try:
        publish_report(target, [125, True])
    except ValueError:
        print("invalid report rejected")
    print(target.read_text(encoding="utf-8").strip())''','invalid report rejected\ntotal_minor=200',
'Validation scans n amounts; the report is tiny. Filesystem write, sync and replacement costs depend on the platform and storage. Atomic visibility and crash durability are separate claims.',
['Do not publish a candidate before its complete validation and write succeed.','File fsync alone is not a tested cross-platform directory durability guarantee.'],['python/pathlib-files','python/bounded-csv','python/sqlite-cli-project'],subject='python-projects')

lesson('package-layout','Python package layout: owned imports and module entrypoints',
'A Python package groups importable modules under an owned namespace, and a module entrypoint can be executed with the interpreter’s -m option.',
'The self-contained fixture builds a temporary src-layout package with an amount formatter and an __main__ module. A child interpreter receives that exact src directory through an explicit path insertion, then executes the package entrypoint. In an installed application the installation supplies import visibility instead; editing sys.path in a production CLI is not the packaging recommendation.',
'The package directory and source text are authored by this fixture, not downloaded or user supplied. Executing code from an untrusted package is arbitrary code execution. Package names can also collide with standard-library names. [[python/modules|Import-time behavior]] and [[python/pyproject-config|Wheel metadata]] explain why source layout, import ownership and installation are separate decisions.',
r'''import subprocess
import sys
import tempfile
from pathlib import Path

with tempfile.TemporaryDirectory() as directory:
    source_root = Path(directory) / "src"
    package = source_root / "aitrove_receipts"
    package.mkdir(parents=True)
    (package / "__init__.py").write_text("", encoding="utf-8")
    (package / "amounts.py").write_text('def label(amount):\n    return f"minor={amount}"\n', encoding="utf-8")
    (package / "__main__.py").write_text('from .amounts import label\nprint(label(125))\n', encoding="utf-8")
    launcher = "import sys, runpy; sys.path.insert(0, sys.argv[1]); runpy.run_module('aitrove_receipts', run_name='__main__')"
    result = subprocess.run([sys.executable, "-I", "-c", launcher, str(source_root)],
                            check=True, capture_output=True, text=True, timeout=3)
    print(result.stdout.strip())''','minor=125',
'Creating this tiny package costs a few filesystem writes and one child startup. Real import and installation costs depend on module contents and dependency graphs; src layout alone does not establish isolation.',
['A source directory must be installed or deliberately placed on the import path.','Never run a downloaded package merely to inspect whether its metadata looks plausible.'],['python/modules','python/setup-interpreter','python/pyproject-config'],subject='python-packaging')

lesson('pyproject-config','Python pyproject.toml: build a wheel and inspect its metadata',
'pyproject.toml declares a Python project’s build backend and distribution metadata, which an installed import package does not provide by itself.',
'The fixture writes a small src-layout package and project configuration, builds a wheel offline through the installed backend, then inspects the archive for its import module and METADATA file. Distribution name and import package name differ deliberately. The metadata describes Python requirements; it does not prove that a package is safe or that every claimed interpreter was tested.',
'The build uses --no-isolation only because this teaching environment already pins its frontend and backend. Normal build isolation lets declared backend requirements be installed in a separate environment. Building an untrusted project can execute backend code. This fixture does not publish to a registry or install into system Python. [[python/package-layout|Import layout]] and [[python/setup-interpreter|Environment ownership]] come first.',
r'''import subprocess
import sys
import tempfile
import zipfile
from pathlib import Path

with tempfile.TemporaryDirectory() as directory:
    project = Path(directory)
    package = project / "src" / "aitrove_receipts"
    package.mkdir(parents=True)
    (package / "__init__.py").write_text('def amount_unit():\n    return "minor"\n', encoding="utf-8")
    (project / "pyproject.toml").write_text(''' + '"""' + '''[build-system]
requires = ["setuptools==84.0.0"]
build-backend = "setuptools.build_meta"
[project]
name = "aitrove-receipt-fixture"
version = "0.1.0"
requires-python = ">=3.11"
[tool.setuptools.packages.find]
where = ["src"]
''' + '"""' + ''', encoding="utf-8")
    subprocess.run([sys.executable, "-I", "-m", "build", "--wheel", "--no-isolation", str(project)],
                   check=True, capture_output=True, text=True, timeout=10)
    wheel = next((project / "dist").glob("*.whl"))
    with zipfile.ZipFile(wheel) as archive:
        names = archive.namelist()
        metadata = archive.read(next(name for name in names if name.endswith("/METADATA"))).decode("utf-8")
        print("module included:", "aitrove_receipts/__init__.py" in names)
        print("Python metadata:", "Requires-Python: >=3.11" in metadata)''','module included: True\nPython metadata: True',
'A wheel build reads source and creates a compressed archive. Its cost depends on package size and backend work; build configuration may execute code, so metadata parsing and building have different trust boundaries.',
['Distribution names and import names are not necessarily identical.','Do not use --no-isolation without owning the build environment’s requirements.'],['python/package-layout','python/setup-interpreter','python/subprocess-boundaries'],subject='python-packaging',dependencies=['build==1.6.1','setuptools==84.0.0'])

lesson('numpy-views','NumPy slices and indexed copies: verify who owns the buffer',
'A NumPy array stores typed values in a buffer, while an array view can refer to selected positions in another array’s buffer.',
'The receipt amounts use an explicit signed 64-bit integer dtype. A basic slice shares the original buffer, so changing its first value changes the original amount. Selecting positions with an integer index list makes a separate array in this fixture. shares_memory checks those relationships instead of assuming every array-returning operation copies.',
'These are small one-dimensional numeric arrays. Object arrays can retain Python object references, and reshaping or layout changes need their own view/copy checks. A buffer alias can expose caller-owned data to later mutation. [[python/copy-deepcopy|Python container copies]] uses a different representation, while [[python/numpy-broadcasting|Broadcasting]] adds shape rules.',
r'''import numpy as np

amounts = np.array([125, 75, 90], dtype=np.int64)
view = amounts[1:]
selected = amounts[[1, 2]]
view[0] = 80
selected[0] = 999
print(amounts.tolist())
print(selected.tolist())
print(bool(np.shares_memory(amounts, view)))
print(bool(np.shares_memory(amounts, selected)))''','[125, 80, 90]\n[999, 90]\nTrue\nFalse',
'The slice creates view metadata without copying its numeric buffer. Advanced selection allocates O(k) selected elements here. shares_memory itself can be expensive for complicated strided layouts; this fixture has simple contiguous storage.',
['Do not mutate a borrowed slice while promising to preserve the caller’s data.','NumPy copy/view behavior is not the same as copying a list’s object references.'],['python/python-lists','python/copy-deepcopy','python/numpy-broadcasting'],subject='python-data',dependencies=['numpy==2.5.3'])

lesson('numpy-broadcasting','NumPy broadcasting: declare axes and bound integer arithmetic',
'NumPy broadcasting aligns compatible array shapes so elementwise operations can combine them without explicitly copying each smaller operand.',
'The dispatch calculation has three item quantities and two price schedules. Reshaping quantities to a column and prices to a row produces a three-by-two matrix with an intentional meaning for each axis. Multiplication allocates the result even though the broadcast operands need not be replicated into full matrices. Reduction uses an explicit 64-bit accumulator.',
'The fixture’s values and shape are fixed and fit int64. Fixed-width NumPy arithmetic is not Python’s arbitrary-size integer arithmetic; sufficiently large products can overflow. Money calculations need unit, range and rounding policies before vectorization. An accidental extra axis can also allocate a much larger result than intended. [[python/decimal-money|Money rules]] remain part of the contract.',
r'''import numpy as np

quantities = np.array([2, 3, 1], dtype=np.int64)
unit_prices = np.array([125, 150], dtype=np.int64)
line_costs = quantities[:, None] * unit_prices[None, :]
print(line_costs.shape)
print(line_costs.tolist())
print(line_costs.sum(axis=0, dtype=np.int64).tolist())''','(3, 2)\n[[250, 300], [375, 450], [125, 150]]\n[750, 900]',
'For n items and p schedules, the materialized result requires O(n*p) values and arithmetic. Avoiding replicated operands does not remove result storage; choose shapes and budgets before allocating.',
['Name what each axis means before relying on a compatible shape.','A fixed-width integer dtype does not prevent arithmetic overflow.'],['python/numpy-views','python/decimal-money','python/pandas-nullable'],subject='python-data',dependencies=['numpy==2.5.3'])

lesson('pandas-nullable','Pandas nullable integers: missing amounts are not zero',
'Pandas nullable integer columns represent integer values and a distinct missing-value marker without converting every amount to a float.',
'The import uses Int64 rather than the NumPy int64 spelling. Its missing amount stays absent and is counted separately. A sum with min_count=1 returns missing for an entirely absent column rather than manufacturing a valid zero total. Dropping missing entries for display is explicit; silently replacing them with zero would change the business meaning.',
'The program supplies already-validated integer values. It does not prove that arbitrary textual amounts parse safely or that bool is acceptable money input. External CSV ingestion needs its own byte, row and field rules. Pandas missing-value behavior varies by dtype, so inspect the actual dtype instead of treating None, NaN and pd.NA as interchangeable values. [[python/bounded-csv|CSV boundaries]] comes before analysis.',
r'''import pandas as pd

amounts = pd.Series([125, None, 75], dtype="Int64")
absent = pd.Series([None, None], dtype="Int64")
print(str(amounts.dtype))
print(amounts.dropna().astype(int).tolist())
print("missing:", int(amounts.isna().sum()))
print("total:", int(amounts.sum(min_count=1)))
print("all absent stays missing:", bool(pd.isna(absent.sum(min_count=1))))''','Int64\n[125, 75]\nmissing: 1\ntotal: 200\nall absent stays missing: True',
'Constructing and scanning n rows takes O(n) work and retained column storage. The missing-value mask consumes memory too; nullable representation is not a free wrapper around an ordinary integer array.',
['Use min_count when an all-missing sum must remain missing.','Do not replace absent financial input with zero without a declared policy.'],['python/bounded-csv','python/numpy-broadcasting','python/pandas-joins'],subject='python-data',dependencies=['pandas==3.0.6','numpy==2.5.3'])

lesson('pandas-joins','Pandas joins: cardinality validation and missing lookup keys',
'A Pandas merge combines rows by keys, and its result size depends on how many matching rows exist on each side.',
'The receipt rows may repeat a region, but the region directory must contain one row per region. validate="many_to_one" enforces that promise during the merge. The indicator column identifies a receipt whose region has no directory match. A duplicate directory entry is rejected instead of multiplying the receipt’s amount into several apparent records.',
'Null join keys need special care: Pandas can match null keys to one another, unlike the usual SQL null comparison expectation. This fixture’s explicit non-null keys avoid that ambiguity. Joining by a display label is also not an identity policy. [[python/unicode-normalization|Label equivalence]] cannot replace stable business keys.',
r'''import pandas as pd

receipts = pd.DataFrame({"receipt_id": [41, 42, 43], "region": ["DEL", "DEL", "BOM"]})
directory = pd.DataFrame({"region": ["DEL"], "owner": ["north"]})
joined = receipts.merge(directory, on="region", how="left", validate="many_to_one", indicator=True)
print(joined.loc[joined["_merge"] == "left_only", "receipt_id"].tolist())
print(joined.loc[joined["_merge"] == "both", "receipt_id"].tolist())
try:
    receipts.merge(pd.DataFrame({"region": ["DEL", "DEL"]}), on="region", validate="many_to_one")
except pd.errors.MergeError:
    print("duplicate directory key rejected")''','[43]\n[41, 42]\nduplicate directory key rejected',
'Join bookkeeping and output storage depend on key counts and implementation. Without a cardinality promise, repeated keys on both sides can create a product-sized result; input row limits alone do not cap merged output.',
['Validate the promised lookup cardinality before trusting totals after a join.','Declare null-key behavior; do not assume SQL null semantics.'],['python/dictionaries','python/pandas-nullable','python/unicode-normalization'],subject='python-data',dependencies=['pandas==3.0.6','numpy==2.5.3'])

lesson('flask-routing','Flask routing: application factories, converters and test clients',
'Flask maps an HTTP method and URL rule to a view function on an application instance.',
'The factory creates the application and registers a receipt route with an integer URL converter. The view returns JSON for positive IDs and rejects zero explicitly. A local test client requests valid, invalid and missing routes without binding a network port. Converting a path segment to int only establishes its shape; it does not establish that the requested receipt belongs to the caller.',
'The amount is fixture data. There is no database, identity, authorization or deployed server here. TESTING lets tests inspect failures, and the development server is not a production deployment plan. [[python/flask-json-api|Body validation]] adds another boundary; [[python/sqlite-cli-project|SQLite storage]] remains a separate local project until deliberately wired into an API.',
r'''from flask import Flask, abort

def create_application():
    application = Flask(__name__)
    application.config["TESTING"] = True
    @application.get("/receipts/<int:receipt_id>")
    def receipt(receipt_id):
        if receipt_id <= 0:
            abort(400)
        return {"receipt_id": receipt_id, "amount_minor": 125}
    return application

client = create_application().test_client()
response = client.get("/receipts/41")
print(response.status_code, response.get_json())
print(client.get("/receipts/0").status_code)
print(client.get("/receipts/not-an-id").status_code)''',"200 {'amount_minor': 125, 'receipt_id': 41}\n400\n404",
'The test performs three local dispatches with tiny responses. It does not measure proxy behavior, network concurrency or production throughput.',
['A URL converter is not a record-level authorization check.','A test client is not evidence that a service is deployed or listening.'],['python/flask-json-api','python/python-functions','python/sqlite-cli-project','spring/web-apis'],subject='python-web',dependencies=['Flask==3.1.3'])

lesson('flask-json-api','Flask JSON API: reject unknown fields, booleans and oversized bodies',
'A JSON API boundary validates content type, payload shape and domain values before performing application work.',
'The receipt estimate requires exactly quantity and unit_minor, both bounded exact integers. bool is rejected even though it inherits from int. A 256-byte framework request limit is separate from schema validation. The successful view returns a calculated total only; it does not write a ledger or charge a payment method.',
'The built-in JSON parser can already have collapsed duplicate object keys before this schema check. A wire contract that rejects duplicate keys needs a custom parser or an earlier strict ingestion boundary. Malformed JSON, unsupported media types and excessive bodies are HTTP errors, not valid empty requests. [[python/json-validation|Strict JSON ingestion]] explains the distinction.',
r'''from flask import Flask, abort, request

def create_application():
    application = Flask(__name__)
    application.config.update(TESTING=True, MAX_CONTENT_LENGTH=256)
    @application.post("/receipt-estimates")
    def estimate():
        payload = request.get_json()
        if type(payload) is not dict or set(payload) != {"quantity", "unit_minor"}:
            abort(400)
        quantity, unit_minor = payload["quantity"], payload["unit_minor"]
        if type(quantity) is not int or type(unit_minor) is not int or not 0 <= quantity <= 100 or not 0 <= unit_minor <= 100000:
            abort(400)
        return {"total_minor": quantity * unit_minor}
    return application

client = create_application().test_client()
print(client.post("/receipt-estimates", json={"quantity": 3, "unit_minor": 125}).get_json())
print(client.post("/receipt-estimates", json={"quantity": True, "unit_minor": 125}).status_code)
print(client.post("/receipt-estimates", json={"quantity": 1, "unit_minor": 1, "extra": 2}).status_code)
print(client.post("/receipt-estimates", data="x" * 300, content_type="application/json").status_code)''',"{'total_minor': 375}\n400\n400\n413",
'Body parsing and schema checks scale with accepted bytes and fields. A byte limit should also be enforced at the deployment proxy; this local test proves only the configured application behavior.',
['Exact int checks avoid accepting booleans as quantities.','Framework-parsed dictionaries do not preserve evidence of duplicate JSON keys.'],['python/json-validation','python/flask-routing','python/input-exercise'],subject='python-web',dependencies=['Flask==3.1.3'])

lesson('django-routing','Django URL routing: local dispatch and parameter boundaries',
'Django resolves URL patterns to view callables and passes converted path parameters to those views.',
'The standalone fixture configures a minimal Django application, registers an integer receipt route and uses Django’s local test client. The view rejects zero rather than assuming an integer converter enforces a positive-ID domain. An unmatched textual ID produces 404. JsonResponse serializes the fixture record; no ORM model is installed or queried.',
'The fixed secret is only a test placeholder in this isolated process. A deployment needs its own secret storage, host policy, middleware, identity and record authorization. This program configures settings once; real projects use a settings module and an application registry that must not be repeatedly reconfigured. [[python/django-forms|Form validation]] and [[python/flask-routing|Flask routing]] show comparable boundaries.',
r'''from django.conf import settings
settings.configure(SECRET_KEY="local-fixture-only", DEBUG=False, ROOT_URLCONF=__name__,
                   ALLOWED_HOSTS=["testserver"], INSTALLED_APPS=[], MIDDLEWARE=[])
import django
django.setup()
from django.http import JsonResponse
from django.test import Client
from django.urls import path

def receipt(request, receipt_id):
    if receipt_id <= 0:
        return JsonResponse({"error": "positive ID required"}, status=400)
    return JsonResponse({"receipt_id": receipt_id, "amount_minor": 125})

urlpatterns = [path("receipts/<int:receipt_id>/", receipt)]
client = Client()
response = client.get("/receipts/41/")
print(response.status_code, response.json())
print(client.get("/receipts/0/").status_code)
print(client.get("/receipts/missing/").status_code)''',"200 {'receipt_id': 41, 'amount_minor': 125}\n400\n404",
'The test uses one in-process application and three requests. URL dispatch timing does not establish database, middleware, network or production performance.',
['A converted path value still requires a domain and authorization rule.','Keep the test placeholder secret out of a deployed settings module.'],['python/django-forms','python/flask-routing','python/sqlite-cli-project'],subject='python-web',dependencies=['Django==5.2.17'])

lesson('django-forms','Django forms: ASCII wire fields and cleaned domain values',
'A Django form validates submitted fields and exposes cleaned values only after its declared field and form rules pass.',
'The amount field accepts one to six ASCII decimal digits and then converts the validated text into a positive integer. The fixture deliberately uses RegexField rather than accepting every string int() might parse. A form-wide check rejects undeclared fields because this particular wire contract allows exactly amount_minor. The program prints stable validity and cleaned-data results instead of locale-dependent error messages.',
'Django forms do not automatically reject every extra submitted field. That policy is explicit here. The fixture validates local dictionaries; it does not render a browser form or prove CSRF protection, session identity or persistence. Never read cleaned_data as a complete accepted result before is_valid passes. [[python/input-exercise|Boundary parsing]] establishes the same rule without a framework.',
r'''from django.conf import settings
settings.configure(SECRET_KEY="local-fixture-only", USE_I18N=False, INSTALLED_APPS=[])
import django
django.setup()
from django import forms

class ReceiptAmountForm(forms.Form):
    amount_minor = forms.RegexField(regex=r"\A[0-9]{1,6}\Z", max_length=6)
    def clean_amount_minor(self):
        amount = int(self.cleaned_data["amount_minor"])
        if amount == 0:
            raise forms.ValidationError("positive amount required")
        return amount
    def clean(self):
        cleaned = super().clean()
        if set(self.data) != {"amount_minor"}:
            raise forms.ValidationError("unexpected fields")
        return cleaned

accepted = ReceiptAmountForm({"amount_minor": "125"})
print(accepted.is_valid(), accepted.cleaned_data)
print(ReceiptAmountForm({"amount_minor": "１２５"}).is_valid())
print(ReceiptAmountForm({"amount_minor": "125", "owner": "other"}).is_valid())''',"True {'amount_minor': 125}\nFalse\nFalse",
'Field validation scans the bounded text and stores cleaned values/errors. The program has one field; large forms need their own field count, upload and validation budgets.',
['Reject extra fields explicitly when the endpoint contract requires it.','A valid form is not a CSRF or record-ownership check.'],['python/input-exercise','python/django-routing','python/regex-validation'],subject='python-web',dependencies=['Django==5.2.17'])

group('python','Scope and call boundaries',['scope-bindings','argument-unpacking'])
group('python-types','Copies, text and rolling collections',['copy-deepcopy','unicode-normalization','counter-deque','timezone-fold'])
group('python-advanced','Object protocols and lookup',['iterator-protocol','descriptors','mro-super','typing-protocol'])
group('python-advanced','Processes, locks and async budgets',['process-pools','subprocess-boundaries','thread-locks','async-queues','async-deadlines'])
group('python-examples','Bounded ingestion',['bounded-csv'])
group('python-dsa','Ordering and connectivity',['merge-sort','topological-sort','dijkstra','union-find'])
group('python-dsa','Text indexes and DP',['trie-prefix','kmp-search','longest-common-subsequence','knapsack'])
group('python-dsa','Linked and hierarchical state',['linked-list-reversal','tree-traversal'])
group('python-interview','Execution timing',['iterator-interview'])
group('python-exercises','Failure before state replacement',['rollback-exercise'])
group('python-projects','Disk-backed local publication',['sqlite-cli-project','atomic-report-project'])
group('python-packaging','Import ownership and distribution',['package-layout','pyproject-config'])
group('python-data','NumPy buffers and shapes',['numpy-views','numpy-broadcasting'])
group('python-data','Pandas missing values and cardinality',['pandas-nullable','pandas-joins'])
group('python-web','Flask request contracts',['flask-routing','flask-json-api'])
group('python-web','Django routing and validation',['django-routing','django-forms'])

NEW_BANKS={
'python-object-protocols':('Python object protocols quiz',['python/iterator-protocol','python/descriptors','python/mro-super','python/copy-deepcopy','python/typing-protocol'],[
('An iterable batch returns a fresh iterator on each iter call. What does this permit?',['Independent complete traversals','One shared cursor only','Automatic deep copies of records'],0,'Fresh cursors isolate traversal position; referenced record ownership remains a separate decision.'),
('What remains after list consumes the same iterator once?',['All values reset','No unconsumed values','A cached copy is required'],1,'Exhaustion does not rewind the iterator; create a fresh iterator from a repeatable collection.'),
('When does the body of a generator function first run?',['When its iterator is first advanced','At function definition','When an annotation is read'],0,'Calling the function constructs a generator; advancing it starts or resumes its body.'),
('A descriptor defining __set__ has what precedence over an instance dictionary entry of the public name?',['The dictionary always wins','The data descriptor wins during normal lookup','The two values are merged'],1,'Normal instance access consults a data descriptor ahead of the instance dictionary.'),
('What should a descriptor do when accessed through its class in this fixture?',['Read None storage','Delete its field','Return the descriptor object'],2,'Class access passes instance=None; returning the descriptor supports inspection without instance storage.'),
('Does a descriptor prevent a caller from editing private dictionary storage directly?',['No','Yes','Only for integers'],0,'It supplies an access convention, not an object security boundary.'),
('What does super continue in cooperative multiple inheritance?',['Only the first textual parent','Lookup after the selected class in the MRO','Every parent independently'],1,'The MRO defines the ordered chain; compatible signatures and super calls maintain cooperation.'),
('What can happen when one cooperative mixin omits super?',['All remaining methods still run','The chain can stop there','The runtime sorts the parents again'],1,'A method that returns without forwarding may skip later participants in the agreed operation.'),
('A deep-copied dictionary had two keys sharing one list. What can the copy preserve?',['The internal sharing relationship','The original list identity','No cycles under any circumstances'],0,'Deepcopy tracks copied objects so supported shared references remain shared inside the separate copy.'),
('Does a Protocol annotation validate an implementation’s returned amount at runtime?',['Always','Only after a keyword call','No'],2,'Static structural intent is separate from runtime domain validation.'),
('What does len of a Python string count?',['UTF-8 bytes','Code points','User-visible grapheme clusters'],1,'Code-point length can differ from byte count and from visible-character count.'),
('Two clock readings share 01:30 but differ in timezone fold. What is the safe elapsed-time comparison basis?',['Their UTC instants','Their display label alone','Their string length'],0,'A repeated local label can represent two instants; elapsed-time decisions need instant semantics.')]),
'python-data-contracts':('Python data analysis contracts quiz',['python/numpy-views','python/numpy-broadcasting','python/pandas-nullable','python/pandas-joins'],[
('A basic NumPy slice shares the source buffer. What can a slice assignment change?',['Only a detached list','The original array','The dtype metadata alone'],1,'A view refers to the same numeric storage, so writing a referenced element changes the source.'),
('Integer-list advanced indexing in the fixture produces what?',['A separate selected array','A cursor into the file','A shared ordinary slice'],0,'This selection allocates its own array rather than the basic slice’s shared buffer.'),
('What should be checked before changing a borrowed array?',['Only its variable name','Its storage ownership and alias contract','Its printed color'],1,'A new array object can still be a view onto caller-owned storage.'),
('Three quantities as a column multiplied by two prices as a row produces what shape?',['(2, 3)','(3,)','(3, 2)'],2,'Each of three item rows combines with each of two price columns.'),
('Does broadcasting eliminate allocation of the multiplication result?',['No','Yes','Only for monetary data'],0,'Operand replication can be avoided while the result matrix still requires storage.'),
('Does int64 have Python arbitrary-size integer semantics?',['Yes','No','Only when used with a named axis'],1,'Fixed-width integer operations can overflow; inputs need numeric bounds.'),
('What does nullable Pandas Int64 retain separately from numeric values?',['An absent-value state','A permanent zero price','A string for every number'],0,'A missing marker is distinct from a valid integer zero.'),
('Why sum with min_count=1 for an entirely absent amount column?',['To force a zero result','To keep the result missing','To sort the column'],1,'The result stays absent when no nonmissing value satisfies the required minimum count.'),
('What join promise does many_to_one validate?',['Every left key is unique','Every matching right key is unique','Both sides have the same row count'],1,'Left keys may repeat; the right lookup must supply at most one matching row per key.'),
('Repeated keys on both join sides can cause what?',['Product-sized output','No output under any merge','Automatic duplicate rejection'],0,'Each matching left row can combine with each matching right row unless a cardinality rule rejects it.'),
('Does Pandas null-key matching always behave like SQL NULL equality?',['Yes','Only in a left join','No'],2,'Pandas can match null keys to each other; declare the intended policy rather than assuming SQL semantics.'),
('The merge indicator says left_only. What does that describe?',['A receipt with no directory match','A deleted receipt','A confirmed record owner'],0,'The indicator describes join presence, not authorization or deletion.')]),
'python-web-boundaries':('Python web application boundaries quiz',['python/flask-routing','python/flask-json-api','python/django-routing','python/django-forms','python/sqlite-cli-project'],[
('An integer URL converter proves what?',['The record belongs to the caller','The segment fits its converter','The record exists'],1,'Conversion establishes path shape; existence and authorization require application checks.'),
('A local Flask or Django test client proves what?',['In-process application behavior','A listening public deployment','Production proxy limits'],0,'The client exercises local dispatch without establishing network or proxy behavior.'),
('Why reject bool for a quantity even though it is an int subclass?',['To disable every integer','Because it is not a quantity in this wire contract','Because JSON cannot encode booleans'],1,'The declared domain requires exact integers rather than boolean flags.'),
('Which rule is distinct from field-schema validation?',['A request byte budget','The field names','Whether quantity exists'],0,'Body reception/parsing needs a byte limit even when the accepted schema has only two fields.'),
('A parsed JSON dictionary can hide what evidence?',['Every positive value','Duplicate object keys','Its field count'],1,'A parser may collapse duplicate keys before a later dictionary schema check can inspect them.'),
('Is an amount estimate response a committed payment?',['Yes','Only with status 200','No'],2,'This fixture calculates a result without payment or ledger side effects.'),
('Do Django forms automatically reject every unknown submitted field?',['No','Yes','Only in the test client'],0,'This lesson’s form-wide check explicitly enforces the exact field-set policy.'),
('When may cleaned_data be treated as the complete accepted form result?',['Before validation','After is_valid returns true','After any field exists'],1,'A form can contain only partially cleaned data while another rule failed.'),
('Is form validity proof of CSRF or record authorization?',['Yes','No','Only for ASCII inputs'],1,'Input validation, request origin protection and identity authorization are different boundaries.'),
('What does a SQLite connection context manage here?',['Transaction commit or rollback','Automatic connection closing','Password rotation'],0,'The program still explicitly closes its connection after the transaction context.'),
('A later insert hits a duplicate primary key in one transaction. What happens to earlier inserts in that attempted batch?',['They must all remain','They are always individually committed','They roll back under this context'],2,'The unhandled integrity failure makes the transaction context roll back the attempted batch.'),
('Does reopening a database after a clean close prove power-loss recovery?',['No','Yes','Only when the data is JSON'],0,'Clean persistence checks do not simulate a crash or certify the deployment filesystem.')])}
for slug,(title,refs,questions) in NEW_BANKS.items():
 BANKS[slug]=(title,questions)
 path='quizzes/'+slug
 e=copy.deepcopy(lookup['quizzes/python-basics'])
 e.update(id=str(uuid.uuid5(uuid.NAMESPACE_URL,'https://aitrove.in/'+path)),path=path,title=title,summary='Twelve explained questions on '+title.lower().replace(' quiz','')+'.',tags=['python','quiz'],sort_order=200+len(added),published_at=stamp,updated_at=stamp)
 e['body']=para('A Python self-check tests operation contracts through twelve questions with explanations.')+'<h2>Review the related lessons</h2><ul>'+''.join('<li><a href="/'+p+'">'+html.escape(lookup[p]['title'])+'</a></li>' for p in refs)+'</ul><h3>Common Mistakes</h3>'+para('Distinguish input validation, state ownership and deployment guarantees. Results stay in this browser; this self-check supplies no credential or hosted code execution.')
 e['data']['questions']=[{'prompt':q,'options':o,'answer':a,'explanation':x} for q,o,a,x in questions]
 upsert(e);added.append(path)
# Old lessons point to new material where a specific operation contract overlaps.
RECIPROCAL={
'python/python-variables':['copy-deepcopy','linked-list-reversal'],
'python/function-arguments':['scope-bindings','argument-unpacking'],
'python/closures':['scope-bindings','iterator-interview'],
'python/generators':['iterator-protocol','iterator-interview'],
'python/classes':['descriptors','mro-super','typing-protocol'],
'python/properties':['descriptors'],
'python/inheritance':['mro-super'],
'python/type-hints':['typing-protocol'],
'python/strings-bytes':['unicode-normalization','kmp-search'],
'python/datetime-boundaries':['timezone-fold'],
'python/dictionaries':['counter-deque','trie-prefix','pandas-joins'],
'python/python-lists':['copy-deepcopy','numpy-views'],
'python/sorting':['merge-sort'],
'python/graph-bfs':['dijkstra','topological-sort','tree-traversal'],
'python/memoization':['longest-common-subsequence','knapsack'],
'python/heap-top-k':['counter-deque','dijkstra'],
'python/thread-pools':['thread-locks','process-pools'],
'python/async-task-groups':['async-queues','async-deadlines'],
'python/modules':['package-layout','process-pools'],
'python/setup-interpreter':['pyproject-config'],
'python/sqlite-transactions':['sqlite-cli-project'],
'python/inventory-project':['rollback-exercise','thread-locks'],
'python/csv-import':['bounded-csv','pandas-nullable'],
'python/pathlib-files':['atomic-report-project'],
'python/json-validation':['flask-json-api'],
'python/input-exercise':['django-forms'],
'python/decimal-money':['numpy-broadcasting','pandas-nullable'],
'python/receipt-cli':['sqlite-cli-project','package-layout'],
}
for path,slugs in RECIPROCAL.items():
 e=lookup[path];e['body']+='<h2>Apply this boundary</h2>'+para(', '.join('[['+'python/'+slug+'|'+lookup['python/'+slug]['title']+']]' for slug in slugs)+'.')
 known={r['path'] for r in e['data']['related']}
 e['data']['related'].extend({'path':'python/'+slug,'title':lookup['python/'+slug]['title']} for slug in slugs if 'python/'+slug not in known)
