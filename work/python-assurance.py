"""Eighth Python pass: verification boundaries and language behavior."""
lesson('starred-unpacking','Python starred unpacking: allocate the middle and reject wrong arity',
'Starred assignment collects the unmatched middle elements of an iterable into a new list.',
'The wire record has a version at the front and a checksum at the end. The starred target captures zero or more payload fields, even when the input was a tuple. This is useful when the envelope has fixed endpoints but variable payload length. The parser still checks the version, field count and checksum; unpacking alone says nothing about record validity. A two-field record produces an empty payload, which this contract rejects.',
'Unpacking consumes the iterable. Passing a one-use stream can exhaust it before any later validation, and an unbounded stream can allocate an unbounded middle list. This fixture first restricts a concrete list or tuple to five fields. [[python/iterator-protocol|Iterator ownership]] and [[python/argument-unpacking|Call unpacking]] have different contracts.',
r'''def decode_envelope(fields):
    if type(fields) not in (list, tuple) or not 3 <= len(fields) <= 5:
        raise ValueError("bounded envelope")
    version, *payload, checksum = fields
    if version != "v1" or type(checksum) is not int or checksum != sum(len(part) for part in payload if type(part) is str):
        raise ValueError("envelope fields")
    if any(type(part) is not str or not part for part in payload):
        raise ValueError("nonempty text payload")
    return payload

print(decode_envelope(("v1", "DEL", "R41", 6)))
try:
    decode_envelope(("v1", 0))
except ValueError:
    print("short envelope rejected")
try:
    decode_envelope(("v1", "DEL", 2))
except ValueError:
    print("checksum rejected")''',"['DEL', 'R41']\nshort envelope rejected\nchecksum rejected",
'For n accepted fields, starred unpacking takes O(n) time and O(n) middle-list storage. The five-field gate bounds both here. The sum expression is also linear in the payload text length; production formats should cap each field length before computing it.',
['The starred target is a list even when the input is a tuple.','Unpacking does not validate a wire format or bound an arbitrary iterator.'],['python/argument-unpacking','python/iterator-protocol','python/bounded-csv'])

lesson('comparison-chains','Python comparison chains: the middle operand is evaluated once',
'A chained comparison evaluates adjacent relations in order and stops when one relation is false.',
'The receipt amount is read through a function that records each call. The expression zero less than amount less than or equal to a cap calls that function once. The explicit and expression also calls it once here because its second comparison uses a saved local value. Repeating a function call on both sides of and would read mutable state twice and could compare two different observations.',
'Comparison chains do not freeze the object returned by the middle expression; mutation inside a custom comparison method can still change its state. An input validator should reject bool explicitly when integer amounts are required, since bool inherits int. [[python/operators|Arithmetic contracts]] and [[python/signature-boundaries|Call boundaries]] cover adjacent rules.',
r'''reads = []
def read_amount():
    reads.append("ledger")
    return 125

print(0 < read_amount() <= 500)
print("reads:", len(reads))
amount = read_amount()
print(0 < amount and amount <= 100)
print("reads:", len(reads))''','True\nreads: 1\nFalse\nreads: 2',
'The comparisons themselves are bounded for small integers. Calling an expensive or stateful middle expression once matters more than syntax length. Custom ordering methods and unbounded integers have their own cost.',
['Do not translate a chain into two calls to a stateful getter.','A chained comparison is not a transaction over mutable operands.'],['python/operators','python/ordering-protocol','python/signature-boundaries'])

lesson('import-cache-ownership','Python module cache: repeated imports reuse an owned module object',
'Python caches imported modules by name in sys.modules so a later import of the same resolved name usually returns the existing module object.',
'The fixture creates a temporary owned module, imports it twice and observes one object and one initialization. It removes only its own cache entry before importing again, which creates a second module with fresh state. The cleanup also removes the temporary directory from sys.path. This is an inspection of import lifetime, not a recommendation to delete shared process modules during application requests.',
'A module name is not a proof of source provenance. Modifying sys.path, shadowing a package name or importing untrusted code can run unexpected initialization. Tests should isolate interpreter state; services should use explicit package layouts and trusted installation. [[python/modules|Module lookup]], [[python/import-failures|Partial imports]] and [[python/package-layout|Package layout]] address the broader boundary.',
r'''import importlib
import sys
import tempfile
from pathlib import Path

with tempfile.TemporaryDirectory() as directory:
    module_file = Path(directory) / "aitrove_owned_counter.py"
    module_file.write_text("starts = 1\n", encoding="utf-8")
    sys.path.insert(0, directory)
    importlib.invalidate_caches()
    try:
        first = importlib.import_module("aitrove_owned_counter")
        first.starts += 1
        second = importlib.import_module("aitrove_owned_counter")
        print("same object:", first is second, second.starts)
        sys.modules.pop("aitrove_owned_counter", None)
        third = importlib.import_module("aitrove_owned_counter")
        print("fresh state:", third is first, third.starts)
    finally:
        sys.modules.pop("aitrove_owned_counter", None)
        sys.path.remove(directory)''','same object: True 2\nfresh state: False 1',
'Module initialization runs when its name is first loaded in this interpreter. Reimport lookup is usually dictionary-backed, but finder/path behavior and arbitrary module initialization prevent a universal constant-time import claim. The temporary filesystem fixture tests one process only.',
['Do not delete a shared module from sys.modules in a live service.','A matching name does not establish where the imported bytes came from.'],['python/modules','python/import-failures','python/package-layout'])

lesson('context-exit-suppression','Python context manager exit: returning true can hide a failure',
'A context manager __exit__ method receives exception information when its with body fails and can suppress that exception by returning a true value.',
'The first owned guard records ValueError and declines suppression, so the caller catches the failure. The second guard explicitly suppresses that one type. Other failures still propagate. A real transaction wrapper should normally roll back and let unexpected errors reach the caller; silent suppression can turn a failed write into an apparent success.',
'The example logs only exception type, avoiding payloads in diagnostic output. The method is invoked on normal exit as well, with no active exception. Returning true in every case is dangerous because it would hide programming errors. [[python/context-managers|Cleanup ownership]] and [[python/exitstack-transfer|Transferred cleanup]] handle resource lifetime separately from failure policy.',
r'''class FailureGuard:
    def __init__(self, suppress=False):
        self.suppress = suppress
        self.seen = []
    def __enter__(self):
        return self
    def __exit__(self, failure_type, failure, traceback):
        self.seen.append(None if failure_type is None else failure_type.__name__)
        return self.suppress and failure_type is ValueError

strict = FailureGuard()
try:
    with strict:
        raise ValueError("invalid receipt")
except ValueError:
    print("strict propagated:", strict.seen)
soft = FailureGuard(suppress=True)
with soft:
    raise ValueError("invalid receipt")
print("soft continued:", soft.seen)''',"strict propagated: ['ValueError']\nsoft continued: ['ValueError']",
'Exit invokes one callback for this one guard; actual cleanup cost belongs to the resource. Suppression changes control flow, not the work already performed before the exception. State changes require rollback or compensation as a separate operation.',
['A true __exit__ return suppresses the exception.','Suppressing an exception does not roll back earlier state changes.'],['python/context-managers','python/exceptions','python/sqlite-savepoints'],subject='python-interview')

lesson('hash-key-mutation-interview','Python interview: mutating a hash key breaks dictionary lookup assumptions',
'A dictionary key needs a stable hash and equality relation for as long as that key remains in the mapping.',
'The intentionally unsafe ReceiptKey hashes its mutable identifier. After insertion, changing that identifier can make a normal lookup fail even though iterating the dictionary still shows the same object. The fixture prints an observed failed lookup for small fixed strings; hash collisions or a different hash seed could make that particular outcome differ, so the dependable rule is the violated key contract, not an asserted universal miss. The safe alternative uses an immutable tuple of validated fields.',
'This class is a failure demonstration, never a pattern for production keys. If the key identifier can change, remove and reinsert under a new immutable value rather than mutating an object already owned by a mapping. [[python/hash-equality|Hash and equality rules]] and [[python/dataclasses|Immutable records]] explain the underlying contract.',
r'''class ReceiptKey:
    def __init__(self, identifier):
        self.identifier = identifier
    def __hash__(self):
        return hash(self.identifier)
    def __eq__(self, other):
        return type(other) is ReceiptKey and self.identifier == other.identifier

key = ReceiptKey("receipt-41")
ledger = {key: 125}
key.identifier = "receipt-42"
print("stored object:", next(iter(ledger)) is key)
print("stable replacement:", {("receipt-42",): 125}[("receipt-42",)])''','stored object: True\nstable replacement: 125',
'Dictionary operations are expected O(1) for ordinary stable keys, with collision and resizing qualifications. Violating the hash invariant makes lookup behavior unreliable; this demonstration deliberately avoids asserting a specific lookup result.',
['Never mutate fields used by __hash__ while the key is stored.','Finding the key by iteration does not mean hash-based lookup still works.'],['python/hash-equality','python/dataclasses','python/dictionaries'],subject='python-interview')

lesson('multiset-diff-exercise','Python exercise: reconcile duplicate receipt counts without losing multiplicity',
'A multiset difference keeps the count of each value rather than reducing the input to distinct values.',
'Two bounded batches represent expected and scanned receipt IDs. Counter subtraction reports missing and unexpected occurrences separately. The expected batch contains R41 twice; a set comparison would erase that discrepancy. The function returns sorted count pairs so output order is independent of input arrival. It validates every identifier before counting and does not change either caller list.',
'Counter subtraction discards nonpositive results, which is correct for each directional gap but wrong for a signed ledger balance. An identifier appearing in both batches can still have a positive gap in one direction. For very large streams, batch materialization and sorted output need size limits or a persisted counting strategy. [[python/counter-deque|Counter behavior]], [[python/reconciliation-exercise|Ledger reconciliation]] and [[python/collections-reference|Collection operations]] give nearby contracts.',
r'''from collections import Counter

def receipt_gaps(expected, scanned):
    for batch in (expected, scanned):
        if type(batch) is not list or len(batch) > 100:
            raise ValueError("batch cap")
        if any(type(identifier) is not str or len(identifier) != 3 or identifier[0] != "R" or not identifier[1:].isascii() or not identifier[1:].isdigit() for identifier in batch):
            raise ValueError("receipt identifier")
    due, seen = Counter(expected), Counter(scanned)
    return sorted((due - seen).items()), sorted((seen - due).items())

print(receipt_gaps(["R41", "R41", "R42"], ["R41", "R43"]))
try:
    receipt_gaps(["R41"], ["R４１"])
except ValueError:
    print("non-ASCII identifier rejected")''',"([('R41', 1), ('R42', 1)], [('R43', 1)])\nnon-ASCII identifier rejected",
'Counting n+m values takes expected O(n+m) dictionary work and O(u) key storage, where u is the number of distinct IDs. Sorting u results costs O(u log u). The 100-entry cap bounds this teaching exercise.',
['A set comparison loses duplicate counts.','Directional Counter subtraction is not a signed net balance.'],['python/counter-deque','python/reconciliation-exercise','python/collections-reference'],subject='python-exercises')

lesson('interval-conflict-exercise','Python exercise: validate half-open reservations before accepting a batch',
'Two half-open intervals conflict when each starts before the other ends.',
'The room schedule accepts integer minute pairs within one day, sorts a copy and rejects overlapping neighbors. Touching endpoints are allowed: a reservation ending at minute 60 can be followed by one starting at 60. Sorting a copy preserves the caller order. Validation happens before sorting, so malformed pairs cannot be mistaken for valid time points.',
'The function reports only a Boolean and does not allocate rooms or choose a maximum weighted schedule. Empty and single-entry schedules are conflict-free by this rule. A real calendar needs timezone, identity, recurrence and concurrent-write rules; [[python/weighted-intervals|Weighted scheduling]] solves a different optimization problem.',
r'''def no_conflicts(reservations):
    if type(reservations) is not list or len(reservations) > 200:
        raise ValueError("reservation cap")
    for span in reservations:
        if type(span) is not tuple or len(span) != 2 or any(type(minute) is not int for minute in span) or not 0 <= span[0] < span[1] <= 1440:
            raise ValueError("half-open minute pair")
    ordered = sorted(reservations)
    return all(previous[1] <= current[0] for previous, current in zip(ordered, ordered[1:]))

print(no_conflicts([(60, 90), (0, 60)]))
print(no_conflicts([(60, 90), (89, 100)]))
print(no_conflicts([]))
try:
    no_conflicts([(True, 60)])
except ValueError:
    print("boolean minute rejected")''','True\nFalse\nTrue\nboolean minute rejected',
'Sorting n intervals costs O(n log n) time and O(n) copied references; the neighbor scan is O(n). The 200-item gate controls this fixture, but the integer-minute model deliberately excludes dates and timezone rules.',
['Touching half-open endpoints do not overlap.','Do not mutate the caller schedule merely to check it.'],['python/weighted-intervals','python/range-exercise','python/datetime-boundaries'],subject='python-exercises')

lesson('fake-clock-tests','Python testing: inject a clock to test expiry at the exact boundary',
'A test clock supplies a chosen time value to code that would otherwise read wall time.',
'The lease is valid strictly before its expiry. The fixture passes the current instant as an integer rather than patching a global clock. This makes the equal-to-expiry case explicit, repeatable and independent of machine timezone or test execution speed. The same function rejects Boolean times and malformed lease fields before checking expiry. A test need not sleep to reach a boundary it can supply as data.',
'An injected clock does not solve clock trust across hosts. Stored leases still need a deployed authority for timestamps, monotonic versus wall-clock policy and transaction ordering. The fixture checks a pure predicate only. [[python/lease-renewal-project|Stored renewal]] and [[python/expiry-exercise|Expiry decisions]] connect the predicate to state transitions.',
r'''def active_lease(now_ms, expiry_ms):
    if type(now_ms) is not int or type(expiry_ms) is not int or not 0 <= now_ms <= 100000 or not 0 <= expiry_ms <= 100000:
        raise ValueError("bounded millisecond times")
    return now_ms < expiry_ms

for controlled_now in (499, 500, 501):
    print(controlled_now, active_lease(controlled_now, 500))
try:
    active_lease(True, 500)
except ValueError:
    print("boolean clock rejected")''','499 True\n500 False\n501 False\nboolean clock rejected',
'The predicate uses bounded integer comparisons and no sleeping. A production storage check has database and contention costs that are absent here. Time units and clock authority must remain part of the caller contract.',
['A sleeping test can miss or delay the exact equality boundary.','A local injected clock does not establish distributed clock agreement.'],['python/expiry-exercise','python/lease-renewal-project','python/pytest-fixtures'],subject='python-testing')

lesson('metamorphic-reconciliation','Python testing: check a reconciliation relation without copying the implementation',
'A metamorphic test checks how an output should change after a controlled input transformation.',
'The receipt-total function rejects booleans and negative amounts, then sums bounded entries. The test changes the order of a batch and checks the total remains equal. It also appends one accepted amount and checks that the total rises by exactly that amount. Neither property requires a second copy of the sum loop as an oracle. The test still checks an explicit small expected value to catch a function that always returns zero.',
'These relations cannot prove every accepted input is correct. A faulty function can satisfy both properties on a narrow set. Pair them with independently chosen examples, rejected-input cases and mutation checks. [[python/hypothesis-properties|Generated properties]], [[python/mutation-testing|Mutation checks]] and [[python/refactor-contract-tests|Refactor tests]] extend that evidence.',
r'''def receipt_total(amounts):
    if type(amounts) is not list or len(amounts) > 20 or any(type(amount) is not int or not 0 <= amount <= 1000 for amount in amounts):
        raise ValueError("bounded minor units")
    return sum(amounts)

batch = [125, 75, 50]
base = receipt_total(batch)
print("known total:", base)
print("reorder invariant:", receipt_total(list(reversed(batch))) == base)
print("append relation:", receipt_total(batch + [30]) == base + 30)
try:
    receipt_total([True])
except ValueError:
    print("boolean amount rejected")''','known total: 250\nreorder invariant: True\nappend relation: True\nboolean amount rejected',
'Summing n bounded integers takes O(n) time and bounded accumulator size here. A test that creates many permutations has factorial growth, so the fixture checks one transformation and relies on separate randomized or exhaustive suites for broader coverage.',
['A relation alone may accept a constant or selectively wrong implementation.','Do not duplicate the production algorithm and call it an independent oracle.'],['python/hypothesis-properties','python/mutation-testing','python/refactor-contract-tests'],subject='python-testing')

lesson('patch-lookup-tests','Python unittest.mock: patch the name the caller actually resolves',
'A patch replaces a selected name for the duration of a test; the caller must resolve that exact name for the patch to affect it.',
'The owned temporary module imports a clock function into its namespace. Patching the original source module after that import leaves the captured reference untouched. Patching the consumer module name changes the value read by the function. The test uses a small owned module and restores the patched name when the context exits. It prints stable numeric values rather than mocking a third-party service.',
'Patching sys.modules and sys.path in a real test suite needs isolation; this fixture cleans up only its owned name. Broad mocks can hide changes in call signatures. A fake clock passed as an argument is simpler when code permits it; patching is useful for legacy lookup sites. [[python/fake-clock-tests|Injected time]] and [[python/mock-failures|Failure mocks]] cover the two approaches.',
r'''import importlib
import sys
import tempfile
from pathlib import Path
from unittest.mock import patch

with tempfile.TemporaryDirectory() as directory:
    Path(directory, "aitrove_clock_source.py").write_text("def time_value():\n    return 10\n", encoding="utf-8")
    Path(directory, "aitrove_clock_consumer.py").write_text("from aitrove_clock_source import time_value\ndef read():\n    return time_value()\n", encoding="utf-8")
    sys.path.insert(0, directory)
    importlib.invalidate_caches()
    try:
        source = importlib.import_module("aitrove_clock_source")
        consumer = importlib.import_module("aitrove_clock_consumer")
        with patch.object(source, "time_value", return_value=20):
            print("source patch:", consumer.read())
        with patch.object(consumer, "time_value", return_value=30):
            print("consumer patch:", consumer.read())
    finally:
        for name in ("aitrove_clock_consumer", "aitrove_clock_source"):
            sys.modules.pop(name, None)
        sys.path.remove(directory)''','source patch: 10\nconsumer patch: 30',
'Each patch changes one module attribute temporarily. The filesystem and module imports dominate this tiny test’s cost. It does not measure production lookup overhead or prove other consumers use the same name.',
['Patch the consumer lookup site, not only the function’s defining module.','Use owned module names and restore test changes to process-wide import state.'],['python/mock-failures','python/fake-clock-tests','python/import-cache-ownership'],subject='python-testing')

lesson('test-double-signature','Python testing: autospec catches a changed call signature',
'An autospecced mock accepts the callable signature of the object it stands in for.',
'The shipping operation has a required receipt ID and a keyword-only region. The mock records a valid call and rejects a positional region. A plain unconstrained Mock would accept that mistaken call and let a test pass even though the real function rejects it. The example also checks exact call arguments so a missing or swapped field is visible.',
'Autospec does not test the real function’s business behavior or external effects. A test suite still needs contract cases against the real implementation. Computed attributes and descriptor side effects can complicate autospec inspection; use it where the inspected interface is stable. [[python/mock-failures|Fault injection]] and [[python/signature-boundaries|Signature rules]] give the surrounding contract.',
r'''from unittest.mock import create_autospec

def submit_receipt(receipt_id, *, region):
    return f"{region}:{receipt_id}"

submission = create_autospec(submit_receipt, return_value="queued")
print(submission(41, region="DEL"))
submission.assert_called_once_with(41, region="DEL")
try:
    submission(41, "DEL")
except TypeError:
    print("positional region rejected")
print("real function:", submit_receipt(41, region="DEL"))''','queued\npositional region rejected\nreal function: DEL:41',
'Autospec adds mock/signature bookkeeping to each test call; it is not a throughput stand-in for a real service. The interface check is fixed-size for this function, while the actual operation cost is outside the fixture.',
['A signature-correct mock can still return an unrealistic result.','An unconstrained Mock can accept arguments the real function rejects.'],['python/mock-failures','python/signature-boundaries','python/refactor-contract-tests'],subject='python-testing')

lesson('wheel-record-verification','Python wheel RECORD: verify member bytes before trusting a local archive',
'A wheel RECORD lists installed paths and optional digests; checking those digests detects changed bytes for entries that declare one.',
'The fixture builds a tiny owned ZIP with a module and a RECORD row containing its SHA-256 digest in URL-safe base64. The verifier requires the row to name the expected module, rejects duplicate entries for that module and compares the digest for its bytes. It checks the clean archive, then a second archive with altered module bytes and the unchanged RECORD. This is byte-integrity verification, not package authenticity.',
'A received archive can supply both malicious bytes and a matching malicious RECORD. Trust still needs an authenticated publisher artifact or independently obtained expected digest. This demonstration verifies one module entry, not full wheel installation rules, tags, signatures, dependency resolution or extraction safety. [[python/artifact-digest-check|Independent expectations]], [[python/wheel-metadata|Metadata inspection]] and [[python/wheel-installation|Offline installation]] distinguish those steps.',
r'''import base64
import csv
import hashlib
import io
import zipfile

def archive_for(source):
    digest = base64.urlsafe_b64encode(hashlib.sha256(b"owner = 'aitrove'\n").digest()).rstrip(b"=").decode("ascii")
    record = f"receipt_tools.py,sha256={digest},18\n"
    output = io.BytesIO()
    with zipfile.ZipFile(output, "w") as wheel:
        wheel.writestr("receipt_tools.py", source)
        wheel.writestr("receipt_tools-1.0.dist-info/RECORD", record)
    return output.getvalue()

def declared_module_matches(blob):
    with zipfile.ZipFile(io.BytesIO(blob)) as wheel:
        rows = list(csv.reader(io.StringIO(wheel.read("receipt_tools-1.0.dist-info/RECORD").decode("utf-8"))))
        if len(rows) != 1 or rows[0][0] != "receipt_tools.py" or len(rows[0]) != 3 or wheel.namelist().count("receipt_tools.py") != 1:
            raise ValueError("record shape")
        digest = base64.urlsafe_b64encode(hashlib.sha256(wheel.read("receipt_tools.py")).digest()).rstrip(b"=").decode("ascii")
        return rows[0][1] == "sha256=" + digest and rows[0][2] == str(len(wheel.read("receipt_tools.py")))

print("owned bytes:", declared_module_matches(archive_for(b"owner = 'aitrove'\n")))
print("altered bytes:", declared_module_matches(archive_for(b"owner = 'other'\n")))''','owned bytes: True\naltered bytes: False',
'Reading all archive and member bytes here uses O(n) memory and time in their byte lengths. The fixture is tiny; a production verifier must cap compressed/uncompressed sizes, entry count and duplicate paths before reading, then cover every required member. It must not extract merely to verify this field.',
['RECORD inside an untrusted archive is not an independent trust source.','Verifying one row does not verify every archive member.'],['python/artifact-digest-check','python/wheel-metadata','python/wheel-installation'],subject='python-packaging')

lesson('module-origin-check','Python packaging: inspect an imported module origin before using it',
'A module spec records the loader and origin selected by Python import resolution.',
'The fixture creates a package module inside an owned temporary directory and imports it through an explicit search path. It checks that the resolved file is the expected owned path before calling a function from the module. The procedure demonstrates provenance inspection in one local process; the example does not claim that a pathname alone authenticates code.',
'An attacker controlling the directory can replace the file before or during import. Source code is executed during import, so an after-import origin check is too late as a security boundary. For received code, authenticate bytes before execution and run only trusted packages. [[python/package-layout|Package lookup]], [[python/import-cache-ownership|Module caching]] and [[python/artifact-digest-check|Artifact expectations]] cover these layers.',
r'''import importlib.util
import tempfile
from pathlib import Path

with tempfile.TemporaryDirectory() as directory:
    owned = Path(directory, "receipt_policy.py")
    owned.write_text("def limit():\n    return 500\n", encoding="utf-8")
    spec = importlib.util.spec_from_file_location("aitrove_owned_receipt_policy", owned)
    if spec is None or spec.loader is None or Path(spec.origin).resolve() != owned.resolve():
        raise ValueError("unexpected module origin")
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    print("owned origin:", Path(spec.origin).resolve() == owned.resolve())
    print("limit:", module.limit())''','owned origin: True\nlimit: 500',
'Creating a spec and executing a module includes filesystem access and arbitrary module initialization cost. The example bounds the source to owned fixed bytes. Filesystem path equality is a diagnostic, not a signature or sandbox.',
['Do not import received code before deciding whether its bytes are trusted.','A path can change contents while a process is running.'],['python/package-layout','python/import-cache-ownership','python/artifact-digest-check'],subject='python-packaging')

lesson('assignment-expression','Python assignment expressions: capture a checked value once',
'An assignment expression binds a name while returning that value to the surrounding expression.',
'The import reader returns one bounded line at a time. The loop captures each read, stops at the empty-string EOF sentinel and rejects an oversized line before publication. That differs from writing while (line := stream.readline()), which would also stop on an empty string but gives no size policy. The fixture counts only accepted, newline-stripped receipt IDs and shows that the reader was called once per record plus once for EOF.',
'This syntax does not make a read atomic with a later write. A failed record should not publish earlier partial state unless the application declares that policy. Parentheses matter in conditions, and a captured mutable object may change later. [[python/bounded-csv|Bounded ingestion]], [[python/iterator-protocol|One-use readers]] and [[python/atomic-report-project|Staged publication]] extend the same input path.',
r'''from io import StringIO

def read_ids(stream):
    accepted = []
    reads = 0
    while (line := stream.readline(16)) != "":
        reads += 1
        if len(line) > 8 or not line.endswith("\n"):
            raise ValueError("bounded complete line")
        identifier = line[:-1]
        if len(identifier) != 3 or identifier[0] != "R" or any(char not in "0123456789" for char in identifier[1:]):
            raise ValueError("receipt identifier")
        accepted.append(identifier)
    return accepted, reads + 1

print(read_ids(StringIO("R41\nR42\n")))
try:
    read_ids(StringIO("R41\nBAD\n"))
except ValueError:
    print("invalid line rejected")''',"(['R41', 'R42'], 3)\ninvalid line rejected",
'Reading n lines uses O(total bytes) time and O(n) output references plus text. The per-read cap prevents one returned chunk from exceeding sixteen characters but does not cap total records; add a record count for a public ingestion boundary.',
['A captured read value is not a transaction with later publication.','An empty-string EOF sentinel differs from a valid blank line.'],['python/bounded-csv','python/iterator-protocol','python/atomic-report-project'])

lesson('dict-view-liveness','Python dictionary views: iteration sees a live mapping, not a snapshot',
'A dictionary view reflects the current contents of its backing mapping.',
'The audit status view is created before a second receipt is added. Reading the view afterward includes the new key; a copied tuple retains the earlier set of keys. A loop over a view should not change the dictionary size during iteration, because that can raise RuntimeError or produce an incomplete walk. The fixture collects a snapshot before deletion, then mutates the original mapping safely.',
'A tuple of keys freezes the outer key sequence, not mutable objects inside values. Sorted order requires an explicit sort; dictionary insertion order is a separate property. [[python/dictionaries|Mapping basics]], [[python/copy-deepcopy|Copy limits]] and [[python/ordered-dictionaries|Order behavior]] separate these claims.',
r'''ledger = {"R41": "queued"}
keys_view = ledger.keys()
keys_snapshot = tuple(keys_view)
ledger["R42"] = "sent"
print("live:", list(keys_view))
print("snapshot:", keys_snapshot)
for identifier in tuple(keys_view):
    if ledger[identifier] == "queued":
        del ledger[identifier]
print("remaining:", sorted(ledger))''',"live: ['R41', 'R42']\nsnapshot: ('R41',)\nremaining: ['R42']",
'Creating a view is bounded work; materializing n keys into a tuple takes O(n) time and retained references. Deletion in the example is safe because the loop walks that tuple rather than a live dictionary iterator.',
['A view is not a fixed list of keys.','Do not resize a dictionary while iterating directly over its keys view.'],['python/dictionaries','python/copy-deepcopy','python/ordered-dictionaries'],subject='python-types')

lesson('finally-return-interview','Python interview: a return from finally replaces a pending exception',
'A finally block runs as a function leaves a try statement, including when an exception is pending.',
'The unsafe function deliberately returns from finally. That return hides the ValueError raised in try, so the caller receives a success-looking marker. The safe function performs cleanup in finally without returning; its ValueError still reaches the caller. The two traces make the failure mode observable without relying on a real external resource.',
'Cleanup itself can raise and replace an earlier error, so production cleanup needs an explicit failure policy. This exercise demonstrates language control flow only. [[python/exceptions|Exception translation]], [[python/context-exit-suppression|Context suppression]] and [[python/exit-stack|Cleanup stacks]] cover related ownership choices.',
r'''events = []
def unsafe_result():
    try:
        raise ValueError("invalid receipt")
    finally:
        events.append("unsafe cleaned")
        return "accepted"

def safe_result():
    try:
        raise ValueError("invalid receipt")
    finally:
        events.append("safe cleaned")

print("unsafe:", unsafe_result())
try:
    safe_result()
except ValueError:
    print("safe propagated")
print("events:", events)''',"unsafe: accepted\nsafe propagated\nevents: ['unsafe cleaned', 'safe cleaned']",
'The control-flow example performs constant application work. Real cleanup may have I/O cost and failure of its own. A return in finally changes the caller-visible result even though the try body already failed.',
['Do not return from finally when callers need a pending failure.','A cleanup failure can also displace the original exception.'],['python/exceptions','python/context-exit-suppression','python/exit-stack'],subject='python-interview')

lesson('stable-dedup-exercise','Python exercise: retain first-seen order while rejecting duplicate IDs',
'Stable deduplication keeps the first occurrence of each key and preserves the input order of those first occurrences.',
'The import preview accepts a bounded list of short ASCII receipt IDs. It returns unique IDs in first-seen order and a separate duplicate count. The first duplicate is not silently deleted from the source list; the function creates new output. This is useful for previewing a batch, but it does not grant exactly-once processing of external effects.',
'Set iteration order is not the requested output order, so the algorithm uses a set only for membership and a list for presentation. For a durable import, duplicate rules also need a stored unique key and transaction policy. [[python/idempotent-jobs|Idempotent work]], [[python/multiset-diff-exercise|Multiplicity]] and [[python/dictionaries|Mapping order]] show distinct contracts.',
r'''def first_seen(receipt_ids):
    if type(receipt_ids) is not list or len(receipt_ids) > 100:
        raise ValueError("batch cap")
    if any(type(identifier) is not str or len(identifier) != 3 or identifier[0] != "R" or any(char not in "0123456789" for char in identifier[1:]) for identifier in receipt_ids):
        raise ValueError("ASCII receipt ID")
    seen = set()
    ordered = []
    duplicates = 0
    for identifier in receipt_ids:
        if identifier in seen:
            duplicates += 1
        else:
            seen.add(identifier)
            ordered.append(identifier)
    return ordered, duplicates

batch = ["R42", "R41", "R42", "R43", "R41"]
print(first_seen(batch))
print("input kept:", batch[0])''',"(['R42', 'R41', 'R43'], 2)\ninput kept: R42",
'Expected O(n) membership work and O(u) retained keys plus O(u) output references for u unique IDs; worst-case collision behavior is not constant. The 100-record gate bounds this exercise. Durable deduplication needs persistent state beyond this process.',
['A set alone discards the requested first-seen sequence.','In-memory deduplication is not exactly-once delivery.'],['python/idempotent-jobs','python/multiset-diff-exercise','python/dictionaries'],subject='python-exercises')

lesson('pathlib-reference','Python pathlib reference: distinguish a path name from validated file content',
'Path objects represent filesystem paths and provide operations to read and write files.',
'The fixture creates an owned temporary directory, writes one UTF-8 report and reads it back with an explicit encoding. The suffix and basename describe a path spelling, not the bytes stored at that path. The read is limited to this owned fixture; opening arbitrary names from a request would need directory containment, symlink and race policies.',
'A path does not become safe because it has a .txt suffix. Replacing a visible report atomically requires staging, validation and a suitable filesystem publication step. [[python/pathlib-files|File boundaries]], [[python/atomic-report-project|Staged replacement]] and [[python/zip-member-validation|Archive paths]] cover those tasks.',
r'''from pathlib import Path
from tempfile import TemporaryDirectory

with TemporaryDirectory() as directory:
    report = Path(directory) / "receipt-41.txt"
    report.write_text("amount_minor=125\n", encoding="utf-8")
    print("name:", report.name)
    print("suffix:", report.suffix)
    print("content:", report.read_text(encoding="utf-8").strip())
    print("missing:", (Path(directory) / "receipt-42.txt").exists())''','name: receipt-41.txt\nsuffix: .txt\ncontent: amount_minor=125\nmissing: False',
'Writing and reading n bytes take O(n) I/O and text allocation. The temporary directory owns cleanup after the with block. This example does not claim crash durability or safe access to untrusted paths.',
['A familiar suffix does not validate content or source.','A temporary directory is not a replacement for a publication protocol.'],['python/pathlib-files','python/atomic-report-project','python/zip-member-validation'],subject='python-reference')

lesson('iterator-reference','Python iterator reference: consume once or create a repeatable source',
'An iterator exposes one sequence of next() results and remains exhausted after its final value.',
'The fixture shows that list(iterator) consumes a one-use stream. Repeating list(iterator) is empty, while calling iter() on an owned tuple gives a new reader each time. A conversion to a tuple creates a reusable snapshot with its own storage cost. The choice belongs in an API contract: a database cursor should not be advertised as replayable unless the query is run again or rows are stored.',
'An exhausted iterator is not an empty underlying collection. A generator may also hold files or other resources until it is closed. [[python/iterator-protocol|Iterator implementation]], [[python/generator-control|Generator cleanup]] and [[python/bounded-csv|Streaming input]] explain the resource side.',
r'''receipt_ids = (41, 42)
stream = iter(receipt_ids)
print("first:", list(stream))
print("second:", list(stream))
print("new reader:", list(iter(receipt_ids)))
print("snapshot:", tuple(receipt_ids))''','first: [41, 42]\nsecond: []\nnew reader: [41, 42]\nsnapshot: (41, 42)',
'Creating a tuple snapshot from n values costs O(n) time and references; creating an iterator over an existing tuple is bounded. Materializing list(iterator) costs O(r) for r remaining items.',
['A consumed iterator is not reusable simply because its source still exists.','Replaying a source can repeat I/O or see changed external state.'],['python/iterator-protocol','python/generator-control','python/bounded-csv'],subject='python-reference')

lesson('tempdir-cleanup-tests','Python testing: assert temporary cleanup after a failure',
'A temporary-directory test verifies that owned filesystem state is removed when a context exits, even if work inside it raises.',
'The fixture creates one marker, captures only its owned path, then raises a validation error. After the exception is caught outside the context, the path no longer exists. This checks a cleanup boundary rather than the content of the file. It uses a generated temporary location but prints only a Boolean, so the displayed output is stable.',
'This does not establish how cleanup behaves after process termination or power loss. On some platforms, open handles can prevent removal; tests that keep a file open should close it first. [[python/pathlib-files|Owned files]], [[python/pathlib-reference|Path operations]] and [[python/pytest-fixtures|Fixture lifetime]] cover related behavior.',
r'''from pathlib import Path
from tempfile import TemporaryDirectory

owned_path = None
try:
    with TemporaryDirectory() as directory:
        owned_path = Path(directory) / "receipt.marker"
        owned_path.write_text("pending", encoding="utf-8")
        raise ValueError("invalid receipt")
except ValueError:
    print("cleaned:", not owned_path.exists())''','cleaned: True',
'The fixture writes and removes a tiny file. Real temporary trees cost work proportional to entry count and file size, and cleanup can fail for reasons this owned test does not exercise.',
['Catch the intended error after the ownership context exits.','Do not infer crash recovery from normal context-manager cleanup.'],['python/pathlib-files','python/pathlib-reference','python/pytest-fixtures'],subject='python-testing')

for subject,title,slugs in [
 ('python','Unpacking and evaluation',['starred-unpacking','comparison-chains','import-cache-ownership','assignment-expression']),
 ('python-interview','Mutation and suppression reasoning',['context-exit-suppression','hash-key-mutation-interview','finally-return-interview']),
 ('python-exercises','Multiplicity and half-open ranges',['multiset-diff-exercise','interval-conflict-exercise','stable-dedup-exercise']),
 ('python-testing','Deterministic tests and doubles',['fake-clock-tests','metamorphic-reconciliation','patch-lookup-tests','test-double-signature','tempdir-cleanup-tests']),
 ('python-packaging','Archive bytes and module origins',['wheel-record-verification','module-origin-check']),
 ('python-types','Mapping views and snapshots',['dict-view-liveness']),
 ('python-reference','File and iteration reminders',['pathlib-reference','iterator-reference'])]:
 group(subject,title,slugs)

ASSURANCE_QUESTIONS=[
 ('What does a starred assignment target retain?',['A tuple','A list of unmatched elements','A generator only','The original iterable unchanged'],1,'The middle target is a new list; unpacking consumes the input.'),
 ('How many times is the middle call evaluated in a chained comparison?',['Zero','Once','Twice','Once per failed relation'],1,'A chain evaluates its middle expression once before adjacent comparisons.'),
 ('Why can a second import return the same module state?',['The source file is immutable','sys.modules caches the loaded module by name','Imports always deep-copy modules','The loader blocks mutation'],1,'Repeated import normally returns the cached module object.'),
 ('What does a true __exit__ return do for an active exception?',['Rolls back all writes','Suppresses the exception','Closes every nested resource','Retries the with body'],1,'Suppression changes propagation; it does not undo state.'),
 ('Why is a mutable hash field unsafe for a stored dictionary key?',['Iteration becomes impossible','Hash lookup assumes stable hash/equality','The key becomes a list','Python silently copies the object'],1,'Changing a field used for hashing violates the mapping key contract.'),
 ('Why is a set insufficient for duplicate receipt reconciliation?',['It sorts values','It discards multiplicity','It cannot contain strings','It changes the input list'],1,'Repeated IDs collapse to one set member.'),
 ('Do [0, 60) and [60, 90) overlap?',['Yes','No','Only in a leap year','Only after sorting'],1,'Half-open intervals exclude their end points.'),
 ('What should an expiry check return when now equals expiry?',['Valid forever','Expired under a strict before rule','Unknown because of UTC','A Boolean timestamp'],1,'The fixture declares validity strictly before expiry.'),
 ('What does an append relation test check?',['A second copy of the algorithm','How output changes after adding a controlled input','A remote service','Only syntax'],1,'The total should rise by the appended amount.'),
 ('Where should unittest.mock patch a name imported into a consumer module?',['Only its original source module','The consumer lookup site','Every module on sys.path','The Python builtins mapping'],1,'The consumer resolves its own captured module-level name.'),
 ('What does autospec check?',['Business correctness','Callable signature compatibility','Remote performance','Data persistence'],1,'It rejects argument shapes the real callable would reject.'),
 ('What does a matching wheel RECORD digest alone establish?',['Publisher identity','That a declared member matches the archive declaration','Safe installation','Complete dependency resolution'],1,'A received archive can carry both altered bytes and a matching altered RECORD.')]
slug='python-assurance-boundaries';title='Python evaluation, testing and archive boundary quiz';BANKS[slug]=(title,ASSURANCE_QUESTIONS)
refs=['python/starred-unpacking','python/import-cache-ownership','python/context-exit-suppression','python/hash-key-mutation-interview','python/multiset-diff-exercise','python/fake-clock-tests','python/patch-lookup-tests','python/wheel-record-verification']
entry=copy.deepcopy(lookup['quizzes/python-basics']);path='quizzes/'+slug
entry.update(id=str(uuid.uuid5(uuid.NAMESPACE_URL,'https://aitrove.in/'+path)),path=path,title=title,summary='Twelve explained questions on Python evaluation, test boundaries and archive bytes.',sort_order=650+len(added),published_at=stamp,updated_at=stamp)
entry['body']=para('A Python self-check tests evaluation order, resource failure policy, deterministic tests and archive byte declarations.')+'<h2>Review the related lessons</h2><ul>'+''.join('<li><a href="/'+p+'">'+html.escape(lookup[p]['title'])+'</a></li>' for p in refs)+'</ul><h3>Common Mistakes</h3>'+para('A correct answer on these fixtures does not prove all runtime versions or archive inputs. Inspect each lesson’s rejected inputs and ownership boundary.')
entry['data']['questions']=[dict(prompt=q,options=o,answer=a,explanation=e) for q,o,a,e in ASSURANCE_QUESTIONS]
entry['data']['related']=[dict(path=p,title=lookup[p]['title']) for p in refs]
upsert(entry);added.append(path)
ASSURANCE_REVERSE={
 'python/argument-unpacking':['starred-unpacking'], 'python/bounded-csv':['assignment-expression'], 'python/operators':['comparison-chains'],
 'python/modules':['import-cache-ownership'], 'python/dictionaries':['dict-view-liveness','stable-dedup-exercise'], 'python/package-layout':['import-cache-ownership','module-origin-check'],
 'python/context-managers':['context-exit-suppression'], 'python/exceptions':['finally-return-interview'], 'python/hash-equality':['hash-key-mutation-interview'],
 'python/counter-deque':['multiset-diff-exercise'], 'python/reconciliation-exercise':['multiset-diff-exercise'],
 'python/weighted-intervals':['interval-conflict-exercise'], 'python/idempotent-jobs':['stable-dedup-exercise'], 'python/expiry-exercise':['fake-clock-tests'], 'python/pathlib-files':['pathlib-reference','tempdir-cleanup-tests'], 'python/iterator-protocol':['iterator-reference'],
 'python/hypothesis-properties':['metamorphic-reconciliation'], 'python/mock-failures':['patch-lookup-tests','test-double-signature'],
 'python/wheel-metadata':['wheel-record-verification'], 'python/artifact-digest-check':['wheel-record-verification','module-origin-check']}
for original,slugs in ASSURANCE_REVERSE.items():
 targets=['python/'+slug for slug in slugs];assert original in lookup and all(p in lookup for p in targets)
 entry=lookup[original];marker='<h2>Check this related boundary</h2>'
 entry['body']=entry['body'].split(marker)[0]+marker+para(', '.join('[['+p+'|'+lookup[p]['title']+']]' for p in targets)+'.')
 known={item['path'] for item in entry['data'].get('related',[])}
 entry['data'].setdefault('related',[]).extend({'path':p,'title':lookup[p]['title']} for p in targets if p not in known)
 entry['updated_at']=stamp
