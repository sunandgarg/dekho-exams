"""Ninth Python pass: callable iteration, task ownership and checked exercises."""
lesson('callable-iterator-sentinel','Python iter(callable, sentinel): stop a pull loop at a declared marker',
'The two-argument iter form calls a zero-argument function repeatedly until its return value compares equal to a sentinel.',
'The owned receipt feeder returns two IDs and then an empty string. iter(feed, "") exposes the two IDs without adding the stop marker to output. The feeder is stateful: another traversal after this one cannot replay the records. The example declares a three-call capacity before constructing the iterator, so a missing sentinel fails through the feeder rather than causing an unbounded pull.',
'The sentinel is compared with equality, not object identity. If an empty string is a valid record, this protocol would discard it and require a different marker. No cleanup hook is supplied by iter itself; a file or socket-backed callable still needs an owned close boundary. [[python/iterator-protocol|Iterable ownership]], [[python/assignment-expression|Bounded read loops]] and [[python/generator-control|Generator cleanup]] cover related choices.',
r'''from collections import deque

pending = deque(["R41", "R42", ""])
reads = 0
def pull_receipt():
    global reads
    reads += 1
    if reads > 3:
        raise ValueError("missing stop marker")
    return pending.popleft()

print(list(iter(pull_receipt, "")))
print("calls:", reads)
print("remaining:", list(pending))''',"['R41', 'R42']\ncalls: 3\nremaining: []",
'One call and equality check occur per accepted value plus the sentinel. Output materialization costs O(n) storage. The explicit call bound protects this fixture from a missing marker; iter alone does not.',
['Choose a sentinel that cannot also be a valid record.','A callable iterator does not reopen or clean up its data source.'],['python/iterator-protocol','python/assignment-expression','python/generator-control'])

lesson('bytearray-aliasing','Python bytearray: mutable bytes share storage only through explicit views',
'Bytearray stores mutable bytes, while bytes stores an immutable byte sequence.',
'The receipt frame begins as a bytearray. A bytes conversion makes an independent immutable snapshot. A memoryview, by contrast, observes later edits to the original buffer. The fixture changes one byte and prints all three representations, then releases its view. This distinction matters when a parser retains a buffer while a network reader refills it.',
'A view can also prevent resizing the underlying bytearray until released. An immutable bytes snapshot costs a full copy, but avoids an alias changing between validation and use. [[python/memoryview-buffers|View lifetime]], [[python/binary-records|Binary framing]] and [[python/strings-bytes|Text encoding]] separate byte ownership from decoded text.',
r'''frame = bytearray(b"R41:125")
snapshot = bytes(frame)
view = memoryview(frame)
frame[0] = ord("X")
print("snapshot:", snapshot)
print("buffer:", bytes(frame))
print("view:", view[0])
try:
    frame.extend(b"!")
except BufferError:
    print("resize blocked by view")
view.release()
frame.extend(b"!")
print("resized:", bytes(frame))''',"snapshot: b'R41:125'\nbuffer: b'X41:125'\nview: 88\nresize blocked by view\nresized: b'X41:125!'",
'Copying n bytes to bytes takes O(n) time and storage; constructing a view retains a reference without copying the payload. A released view must not be reused, and a reader still needs a bound on retained buffers.',
['A memoryview is not a frozen snapshot.','Release a view before resizing the exporting bytearray.'],['python/memoryview-buffers','python/binary-records','python/strings-bytes'],subject='python-types')

lesson('async-to-thread-context','Python asyncio.to_thread: carry context into blocking work',
'asyncio.to_thread runs a synchronous callable in a worker thread and returns an awaitable for its result.',
'The request label is stored in a ContextVar before the thread call. The blocking function reads that label and returns a bounded receipt string. The caller awaits completion before printing, so output order is fixed. This is appropriate for a small blocking operation that cannot be made asynchronous without replacing its API; it does not turn CPU-heavy Python work into an automatic throughput win.',
'Cancelling the awaiting coroutine does not forcibly terminate a thread that has already begun work. If the blocking function performs an external write, the application needs a stop or idempotency rule independent of task cancellation. [[python/context-variables|Context propagation]], [[python/thread-pools|Thread ownership]] and [[python/async-shield-ownership|Cancellation ownership]] cover those limits.',
r'''import asyncio
from contextvars import ContextVar

request_label = ContextVar("request_label", default="unset")
def blocking_receipt_lookup(identifier):
    return request_label.get() + ":" + identifier

async def main():
    token = request_label.set("review-7")
    try:
        print(await asyncio.to_thread(blocking_receipt_lookup, "R41"))
    finally:
        request_label.reset(token)

asyncio.run(main())''','review-7:R41',
'Submitting work and crossing thread boundaries add scheduling cost. The returned string is tiny; a real blocking call needs timeout, cancellation and capacity limits for its worker pool. Context propagation copies context references, not deep snapshots of mutable values.',
['A cancelled await does not guarantee the worker stopped.','ContextVar propagation does not make shared mutable payloads thread-safe.'],['python/context-variables','python/thread-pools','python/async-shield-ownership'],subject='python-advanced')

lesson('cached-property-invalidation','Python cached_property: delete the instance value when source state changes',
'cached_property computes an attribute on first access and stores the result in the instance dictionary.',
'The invoice stores an immutable tuple of minor-unit amounts and counts summary evaluations. Two reads use one computed total. Replacing the tuple without deleting the cached attribute would leave a stale total; the setter therefore deletes the cached value after validating the new amounts. A later read recomputes it. The cache is per instance, not a global memo table.',
'This descriptor needs a mutable instance __dict__. It is unsuitable for a slots-only instance without one, and concurrent first reads may run the getter more than once. Invalidation belongs with every mutation path. [[python/properties|Property updates]], [[python/functools-cache|Function caching]] and [[python/dataclasses|Owned records]] show alternatives.',
r'''from functools import cached_property

class Invoice:
    def __init__(self, amounts):
        self.computations = 0
        self.replace(amounts)
    def replace(self, amounts):
        candidate = tuple(amounts)
        if len(candidate) > 20 or any(type(amount) is not int or not 0 <= amount <= 1000 for amount in candidate):
            raise ValueError("bounded minor units")
        self.amounts = candidate
        self.__dict__.pop("total", None)
    @cached_property
    def total(self):
        self.computations += 1
        return sum(self.amounts)

invoice = Invoice([125, 75])
print(invoice.total, invoice.total, invoice.computations)
invoice.replace([125, 100])
print(invoice.total, invoice.computations)''','200 200 1\n225 2',
'An uncached total scans n amounts; a later cached read is an attribute lookup. The cached integer and instance dictionary entry remain until deletion or collection. This program has no concurrent callers, so it does not establish one-computation semantics under a race.',
['Changing source state without invalidation leaves a stale cached value.','cached_property requires an instance dictionary and does not serialize concurrent first access.'],['python/properties','python/functools-cache','python/dataclasses'],subject='python-advanced')

lesson('gather-sibling-lifetime','Python asyncio.gather: a sibling can continue after the first failure',
'With its default error behavior, asyncio.gather propagates the first exception to its awaiter without automatically cancelling other submitted awaitables.',
'The failing receipt job raises immediately. Its sibling is already waiting on a gate. After gather raises, the caller checks that the sibling task is still pending, then opens the gate and awaits it. This makes the lifetime visible rather than relying on a scheduling sleep. The caller owns cleanup of a task it intentionally allowed to continue.',
'A cancelled gather future and a child cancellation follow different rules, and another child may also fail later. TaskGroup applies a different sibling-cancellation contract. Choose one explicitly before starting work with side effects. [[python/async-task-groups|Structured tasks]], [[python/async-deadlines|Deadlines]] and [[python/cancellation-interview|Cancellation traces]] provide the comparison.',
r'''import asyncio

async def reject_receipt():
    raise ValueError("invalid receipt")

async def delayed_receipt(gate):
    await gate.wait()
    return "R42 stored"

async def main():
    gate = asyncio.Event()
    sibling = asyncio.create_task(delayed_receipt(gate))
    try:
        await asyncio.gather(reject_receipt(), sibling)
    except ValueError:
        print("sibling pending:", not sibling.done())
    gate.set()
    print("sibling result:", await sibling)

asyncio.run(main())''','sibling pending: True\nsibling result: R42 stored',
'Task creation and scheduling add runtime work; the fixture runs two tasks. A real batch needs a bound on in-flight tasks and explicit handling of every task result or failure. A continuing sibling may already have side effects when the caller sees the first error.',
['Do not assume gather cancels every sibling on the first ordinary exception.','Retain and observe tasks that continue after an early failure.'],['python/async-task-groups','python/async-deadlines','python/cancellation-interview'],subject='python-advanced')

lesson('try-else-finally-interview','Python interview: try else runs only after the try body succeeds',
'The else clause of a try statement runs when the try body finishes without an exception, before finally.',
'The parser logs a successful integer conversion in else and cleanup in finally. A malformed field skips else, enters the ValueError handler and still executes finally. This ordering matters when a writer records success: putting that record in finally would mark a failed parse as accepted. The event list makes both traces testable without inspecting traceback text.',
'The catch is limited to ValueError from integer conversion. A broader catch could hide a bug unrelated to the field. No data is committed by this fixture; [[python/sqlite-transactions|a transaction]] must still define when parsed data becomes visible. [[python/finally-return-interview|Return suppression]] is a different finally hazard.',
r'''def parse_amount(text):
    events = []
    try:
        amount = int(text)
    except ValueError:
        events.append("rejected")
        amount = None
    else:
        events.append("parsed")
    finally:
        events.append("cleanup")
    return amount, events

print(parse_amount("125"))
print(parse_amount("bad"))''',"(125, ['parsed', 'cleanup'])\n(None, ['rejected', 'cleanup'])",
'Conversion cost depends on input length and integer digits, so a real boundary needs length and magnitude caps before accepting user text. The event list stores two short strings per call in this fixture.',
['else is skipped when the try body raises.','finally is for cleanup, not unconditional success recording.'],['python/exceptions','python/finally-return-interview','python/sqlite-transactions'],subject='python-interview')

lesson('comprehension-scope-interview','Python interview: a comprehension has its own loop-variable scope',
'A Python comprehension binds its loop variable in an inner scope rather than exporting it to the surrounding one.',
'The first list comprehension builds receipt labels, leaving the surrounding index name unbound. A second builds callbacks that close over the same comprehension variable cell, so all callbacks read its final value when invoked. A default parameter captures each current integer instead. Scope isolation and late binding are separate rules; knowing one does not fix the other.',
'The callbacks here retain only small integers. Capturing a mutable receipt object would retain its reference, not freeze its state. [[python/scope-bindings|Closure binding]], [[python/closures|Ownership]] and [[python/comprehensions|Comprehension behavior]] show the adjacent cases.',
r'''labels = [f"R{index}" for index in range(3)]
late = [lambda: index for index in range(3)]
bound = [lambda index=index: index for index in range(3)]
print(labels)
print("leaked:", "index" in globals())
print("late:", [callback() for callback in late])
print("bound:", [callback() for callback in bound])''',"['R0', 'R1', 'R2']\nleaked: False\nlate: [2, 2, 2]\nbound: [0, 1, 2]",
'Constructing n callbacks and labels costs O(n) time and retained objects. Closing over a single loop cell avoids copying values but creates the late-read behavior; default binding stores one value reference per function.',
['Comprehension scope isolation does not imply per-iteration closure capture.','A bound default holds a reference, not a deep copy.'],['python/scope-bindings','python/closures','python/comprehensions'],subject='python-interview')

lesson('sorted-merge-exercise','Python exercise: merge two sorted feeds and preserve left-first ties',
'A stable merge combines sorted inputs while retaining the original order of equal-key records.',
'The fixture accepts two bounded nondecreasing integer feeds. It emits each amount with a source label, choosing the left feed first when values tie. Each input remains unchanged. The output therefore has a declared tie policy that can be tested separately from merely being sorted. A two-pointer scan avoids sorting the combined feed again.',
'The function validates both order contracts before merging; a single out-of-order value is rejected rather than hidden by a later sort. For large live feeds, materializing both inputs and output would defeat streaming. [[python/merge-sort|Merge sort]], [[python/bounded-csv|Bounded ingestion]] and [[python/iterator-protocol|Iterator ownership]] show the next boundaries.',
r'''def merge_feeds(left, right):
    for feed in (left, right):
        if type(feed) is not list or len(feed) > 100 or any(type(value) is not int or not 0 <= value <= 1000 for value in feed) or any(a > b for a, b in zip(feed, feed[1:])):
            raise ValueError("sorted bounded integer feed")
    merged = []
    left_index = right_index = 0
    while left_index < len(left) or right_index < len(right):
        if right_index == len(right) or left_index < len(left) and left[left_index] <= right[right_index]:
            merged.append((left[left_index], "left"))
            left_index += 1
        else:
            merged.append((right[right_index], "right"))
            right_index += 1
    return merged

print(merge_feeds([10, 20, 20], [20, 30]))
try:
    merge_feeds([20, 10], [])
except ValueError:
    print("unsorted feed rejected")''',"[(10, 'left'), (20, 'left'), (20, 'left'), (20, 'right'), (30, 'right')]\nunsorted feed rejected",
'Validation and merge take O(n+m) time; output retains O(n+m) labeled pairs. The 100-item cap controls this exercise. A stream merge would keep smaller memory but must define how and when input errors become visible.',
['Do not silently sort a feed whose declared input contract was broken.','Using less-than rather than less-than-or-equal changes equal-key tie order.'],['python/merge-sort','python/bounded-csv','python/iterator-protocol'],subject='python-exercises')

lesson('run-length-exercise','Python exercise: encode consecutive states without merging distant runs',
'Run-length encoding replaces each consecutive run of equal values with that value and its count.',
'The receipt-status stream contains two queued runs separated by a sent state. The encoder keeps those queued runs separate; a Counter would merge their totals and lose order. It rejects non-ASCII, nonalphabetic states and caps input length before scanning. The empty input has an empty encoding, which the decoder can distinguish from a missing field only if the caller declares that policy.',
'This is a teaching encoder, not a compression format with framing, escaping or integrity checks. Long runs and attacker-controlled counts need limits in any decoder. [[python/counter-deque|Frequency counting]] solves a different question; [[python/binary-records|Record framing]] explains why wire compression needs more than this loop.',
r'''def encode_states(states):
    if type(states) is not str or len(states) > 100 or not states.isascii() or not states.isalpha():
        if states != "":
            raise ValueError("ASCII status sequence")
    if not states:
        return []
    encoded = []
    current, count = states[0], 1
    for state in states[1:]:
        if state == current:
            count += 1
        else:
            encoded.append((current, count))
            current, count = state, 1
    encoded.append((current, count))
    return encoded

print(encode_states("QQSQQ"))
print(encode_states(""))
try:
    encode_states("Q１")
except ValueError:
    print("non-ASCII state rejected")''',"[('Q', 2), ('S', 1), ('Q', 2)]\n[]\nnon-ASCII state rejected",
'The scan costs O(n) time and O(r) output for r runs. A sequence with no repeated adjacent states can make the encoded representation larger than the input; compression is not guaranteed.',
['A Counter loses run boundaries and order.','A decoder must cap declared counts before allocating output.'],['python/counter-deque','python/binary-records','python/strings-bytes'],subject='python-exercises')

lesson('dag-order-exercise','Python exercise: verify a dependency order without confusing it with reachability',
'A topological-order verifier checks that every declared directed edge points from an earlier to a later item in a proposed sequence.',
'The build graph names three steps and two dependencies. The proposed order lists every step exactly once and places each prerequisite before its dependent step. A second order violates one edge and is rejected. The checker does not generate an order or silently discard duplicate nodes; it validates graph and proposal shapes first.',
'A cyclic graph has no valid complete order, but this verifier does not diagnose which cycle caused rejection. For construction use [[python/topological-sort|topological sorting]]; for graph grouping use [[python/strongly-connected-components|components]]. This exercise answers the narrower question of whether one submitted order satisfies the supplied edge set.',
r'''def valid_order(nodes, edges, proposed):
    if type(nodes) is not list or len(nodes) > 30 or any(type(node) is not str or not node for node in nodes) or len(set(nodes)) != len(nodes):
        raise ValueError("node set")
    if type(edges) is not list or len(edges) > 100 or any(type(edge) is not tuple or len(edge) != 2 or edge[0] not in nodes or edge[1] not in nodes for edge in edges):
        raise ValueError("edge set")
    if type(proposed) is not list or len(proposed) != len(nodes) or any(type(node) is not str for node in proposed) or set(proposed) != set(nodes):
        return False
    position = {node: index for index, node in enumerate(proposed)}
    return all(position[source] < position[target] for source, target in edges)

steps = ["read", "validate", "publish"]
edges = [("read", "validate"), ("validate", "publish")]
print(valid_order(steps, edges, ["read", "validate", "publish"]))
print(valid_order(steps, edges, ["validate", "read", "publish"]))''','True\nFalse',
'After validation, building positions costs O(V) expected dictionary work and checking E edges costs O(E). This implementation checks edge endpoint membership against a list during validation, so its actual bound includes O(EV); the 30-node/100-edge limits keep the fixture small. A larger verifier should build a node set once.',
['A permutation is not valid merely because it lists every node.','A false result does not identify a cycle or construct a repair.'],['python/topological-sort','python/strongly-connected-components','python/graph-bfs'],subject='python-exercises')

lesson('unittest-subtests','Python unittest subTest: label several cases without aborting the method',
'A subTest gives each iteration of one test method its own reported case context.',
'The owned parser accepts a short ASCII minor-unit amount and rejects negative or non-ASCII text. One test method checks three accepted values under named subTest contexts. The runner reports one method and no failures, while the observed case list confirms all three contexts executed. If one subtest failed, unittest would record that failure and continue the later contexts in the same method.',
'Subtests improve failure reporting, but they do not isolate shared mutable state between iterations. If a case changes a database or module global, reset it per case or use separate tests. [[python/unittest-contracts|Basic test contracts]], [[python/pytest-fixtures|Fixture ownership]] and [[python/refactor-contract-tests|Behavior checks]] provide the surrounding structure.',
r'''import io
import unittest

def parse_minor(text):
    if type(text) is not str or not 1 <= len(text) <= 4 or any(char not in "0123456789" for char in text):
        raise ValueError("ASCII amount")
    return int(text)

visited = []
class AmountCases(unittest.TestCase):
    def test_accepted_amounts(self):
        for raw, expected in (("0", 0), ("125", 125), ("0012", 12)):
            with self.subTest(raw=raw):
                visited.append(raw)
                self.assertEqual(parse_minor(raw), expected)

result = unittest.TextTestRunner(stream=io.StringIO()).run(
    unittest.defaultTestLoader.loadTestsFromTestCase(AmountCases))
print("method:", result.testsRun, "failures:", len(result.failures))
print("cases:", visited)
try:
    parse_minor("１２")
except ValueError:
    print("non-ASCII amount rejected")''',"method: 1 failures: 0\ncases: ['0', '125', '0012']\nnon-ASCII amount rejected",
'Three tiny cases have bounded cost. A single test method still counts as one executed method; subtest events are additional reporting context, not independent process or transaction isolation.',
['Do not assume subTest resets changed state between iterations.','The runner method count is not the number of subtest cases.'],['python/unittest-contracts','python/pytest-fixtures','python/refactor-contract-tests'],subject='python-testing')

lesson('asyncio-test-fixture','Python IsolatedAsyncioTestCase: own async setup and cleanup per test',
'IsolatedAsyncioTestCase runs each asynchronous test with an event-loop lifetime managed by unittest.',
'The fixture creates a queue in asyncSetUp, consumes one receipt in an async test and records cleanup in asyncTearDown. The runner uses an owned in-memory text stream so only stable outcome fields are printed. The event list proves setup, test and cleanup ran in that order. This checks one local queue operation, not network I/O or a production task scheduler.',
'An asynchronous test can still leak a task whose result it never observes. Own created tasks, cancel or await them in cleanup and test the failure path as well as success. [[python/async-task-groups|Task ownership]], [[python/gather-sibling-lifetime|Continuing siblings]] and [[python/async-deadlines|Deadlines]] matter when tests create background work.',
r'''import asyncio
import io
import unittest

events = []
class QueueCase(unittest.IsolatedAsyncioTestCase):
    async def asyncSetUp(self):
        self.queue = asyncio.Queue()
        events.append("setup")
    async def test_receipt(self):
        await self.queue.put("R41")
        self.assertEqual(await self.queue.get(), "R41")
        events.append("test")
    async def asyncTearDown(self):
        self.assertTrue(self.queue.empty())
        events.append("cleanup")

result = unittest.TextTestRunner(stream=io.StringIO()).run(
    unittest.defaultTestLoader.loadTestsFromTestCase(QueueCase))
print("passed:", result.wasSuccessful())
print("events:", events)''',"passed: True\nevents: ['setup', 'test', 'cleanup']",
'The test pays event-loop setup/teardown cost in addition to one queue operation. It does not measure thread contention or real service time. The in-memory queue is local to this fixture and has no persistence.',
['Observe every spawned task; loop cleanup is not proof that its work succeeded.','An in-memory async test is not a deployed I/O test.'],['python/async-task-groups','python/gather-sibling-lifetime','python/async-deadlines'],subject='python-testing')

lesson('entry-point-discovery','Python entry points: inspect a trusted distribution before loading its plugin',
'Entry points are distribution metadata naming importable objects under a declared group and name.',
'The fixture creates an owned temporary module and matching dist-info metadata. importlib.metadata discovers a receipt-validator entry point from that directory, then loads the callable and validates one owned identifier. The group name narrows selection. The example prints the selected name and result, not a machine-specific path.',
'Loading an entry point imports and executes code. Metadata is a discovery mechanism, not a signature or sandbox. In a service, allowlist a trusted installed distribution and verify release provenance before invoking its plugin; failure and plugin lifetime need separate rules. [[python/plugin-project|Owned plugin process]], [[python/module-origin-check|Import diagnostics]] and [[python/artifact-digest-check|Byte expectations]] distinguish discovery from trust.',
r'''import importlib.metadata
import sys
import tempfile
from pathlib import Path

with tempfile.TemporaryDirectory() as directory:
    root = Path(directory)
    (root / "aitrove_receipt_check.py").write_text(
        "def accepted(identifier):\n    return identifier == 'R41'\n", encoding="utf-8")
    metadata = root / "aitrove_receipt_check-1.0.dist-info"
    metadata.mkdir()
    (metadata / "METADATA").write_text(
        "Metadata-Version: 2.1\nName: aitrove-receipt-check\nVersion: 1.0\n", encoding="utf-8")
    (metadata / "entry_points.txt").write_text(
        "[aitrove.receipts]\nvalidator = aitrove_receipt_check:accepted\n", encoding="utf-8")
    sys.path.insert(0, directory)
    try:
        distribution = next(importlib.metadata.distributions(path=[directory]))
        selected = [point for point in distribution.entry_points if point.group == "aitrove.receipts"]
        print("entry point:", selected[0].name)
        print("accepted:", selected[0].load()("R41"))
    finally:
        sys.path.remove(directory)
        sys.modules.pop("aitrove_receipt_check", None)''','entry point: validator\naccepted: True',
'Metadata discovery scans distribution records on the selected path; loading also imports arbitrary module code. This tiny owned directory has fixed size. The example does not resolve dependencies, authenticate a publisher or isolate a malicious plugin.',
['Do not treat an entry-point name as code authenticity.','Loading the selected entry point executes its module.'],['python/plugin-project','python/module-origin-check','python/artifact-digest-check'],subject='python-packaging')

lesson('version-specifier-check','Python package versions: test a declared range against parsed versions',
'A version specifier selects candidate releases according to a declared package-version rule.',
'The fixture uses the packaging library to compare three candidate versions against a bounded range. An explicit stable-only policy excludes the prerelease candidate; the lower stable release is included and a later major release is outside the range. This is a selection predicate, not a dependency solver: it says nothing about transitive requirements, platform wheels or whether the candidate bytes came from a trusted publisher.',
'Comparing version strings lexically would order multi-digit components incorrectly. A deployment lock needs exact artifacts and hashes or another authenticated release policy, plus a tested platform/runtime matrix. [[python/pyproject-config|Project metadata]], [[python/wheel-installation|Offline wheel install]] and [[python/artifact-digest-check|Independent byte expectations]] cover later stages.',
r'''from packaging.specifiers import SpecifierSet
from packaging.version import Version

accepted = SpecifierSet(">=2.4,<3")
for candidate in ("2.4", "2.5rc1", "3.0"):
    print(candidate, accepted.contains(Version(candidate), prereleases=False))''','2.4 True\n2.5rc1 False\n3.0 False',
'Parsing and comparisons depend on version-string length and number of candidate constraints. The fixture checks three short values. Resolver search can have much higher cost and is not performed here.',
['Do not compare package versions as plain strings.','A matching specifier is neither a resolved dependency graph nor authenticated code.'],['python/pyproject-config','python/wheel-installation','python/artifact-digest-check'],subject='python-packaging',dependencies=['packaging==26.3'])

lesson('pandas-asof-joins','Pandas merge_asof: match an earlier event within a declared tolerance',
'An as-of join matches each left key with a nearby right key under an ordered direction rather than exact equality.',
'The receipt readings occur at times 10, 20 and 30. A backwards join with a three-unit tolerance selects events at 8 and 19; an event at 25 is too old for the reading at 30, which remains missing. Both inputs are sorted on their join key before the operation. The printed list converts missing values to a visible marker rather than silently treating an absent match as zero.',
'Time units, group ownership and tie rules must be explicit in a real telemetry pipeline. A forward match could leak future information into a historical feature. [[python/pandas-joins|Exact cardinality joins]], [[python/pandas-rolling|Rolling windows]] and [[python/time-series-validation|Temporal splits]] describe different boundaries.',
r'''import pandas as pd

readings = pd.DataFrame({"minute": [10, 20, 30], "receipt_id": [41, 42, 43]})
events = pd.DataFrame({"minute": [8, 19, 25], "state": ["opened", "checked", "closed"]})
joined = pd.merge_asof(readings, events, on="minute", direction="backward", tolerance=3)
print(["missing" if pd.isna(value) else value for value in joined["state"]])
print(joined["receipt_id"].tolist())''',"['opened', 'checked', 'missing']\n[41, 42, 43]",
'For sorted keys, an as-of join scans/looks up nearby rows without a Cartesian product; materialized output still scales with left row count. Sorting unsorted inputs costs additional O(n log n) work and memory. This fixture has three rows per side.',
['A backward join and a forward join answer different causal questions.','Missing matched state is not the same as an event with state zero.'],['python/pandas-joins','python/pandas-rolling','python/time-series-validation'],subject='python-data',dependencies=['pandas==3.0.6','numpy==2.5.3'])

lesson('numpy-finite-gate','NumPy finite gate: reject NaN and infinity before computing totals',
'A finite-value gate marks array elements that are neither NaN nor positive or negative infinity.',
'The imported amount array contains a valid positive value, NaN, infinity and a negative value. isfinite finds the first two invalid representations; a separate domain check rejects the finite negative amount. The accepted mask therefore selects only the positive value. A production import should reject the whole batch or document partial acceptance before replacing a ledger.',
'Floating-point arrays cannot represent every decimal minor-unit amount exactly. If money is the domain, parse bounded integers or Decimal before using a numeric array for secondary analysis. [[python/numpy-precision|Tolerance and finite checks]], [[python/numpy-shape-contract|Axis rules]] and [[python/decimal-money|Exact ledger amounts]] set adjacent constraints.',
r'''import numpy as np

amounts = np.array([125.0, np.nan, np.inf, -3.0], dtype=np.float64)
finite = np.isfinite(amounts)
accepted = finite & (amounts >= 0)
print("finite:", finite.tolist())
print("accepted:", accepted.tolist())
print("selected:", amounts[accepted].tolist())''','finite: [True, False, False, True]\naccepted: [True, False, False, False]\nselected: [125.0]',
'isfinite scans n elements and allocates a Boolean mask; the second comparison and selection allocate more arrays. This small fixture does not measure large-buffer memory peaks. Reject input shape and byte budgets before constructing a huge array.',
['NaN fails ordinary equality assumptions and must be handled deliberately.','A finite negative value can still violate a nonnegative business contract.'],['python/numpy-precision','python/numpy-shape-contract','python/decimal-money'],subject='python-data',dependencies=['numpy==2.5.3'])

lesson('flask-keyset-list','Python Flask keyset list: validate a cursor before selecting the next page',
'A keyset list uses the last seen ordered key to request records after that key.',
'The local Flask endpoint accepts an optional ASCII decimal after cursor, caps its length and returns at most two records from an owned sorted list. The first response gives IDs 41 and 42 and cursor 42; a second call gives ID 43. Invalid cursor text returns 400 rather than changing the query into a broad scan. The test client makes these requests without opening a network listener.',
'A cursor is not authorization, and a numeric ID can reveal ordering or cardinality. Real list handlers must filter by tenant and permissions before limiting, and persistent writes need stable key ordering and an index. [[python/django-pagination|Django keysets]], [[python/drf-list-visibility|Read scope]] and [[python/flask-routing|Route validation]] cover those boundaries.',
r'''from flask import Flask, jsonify, request

application = Flask(__name__)
receipts = [(41, 125), (42, 75), (43, 200)]

@application.get("/receipts")
def list_receipts():
    raw = request.args.get("after", "0")
    if not 1 <= len(raw) <= 6 or any(char not in "0123456789" for char in raw):
        return jsonify(error="invalid cursor"), 400
    selected = [(identifier, amount) for identifier, amount in receipts if identifier > int(raw)][:2]
    return jsonify(ids=[identifier for identifier, _ in selected],
                   next=selected[-1][0] if selected else None)

with application.test_client() as client:
    first = client.get("/receipts").get_json()
    second = client.get("/receipts?after=42").get_json()
    print(first["ids"], first["next"])
    print(second["ids"], second["next"])
    print("bad cursor:", client.get("/receipts?after=+1").status_code)''','[41, 42] 42\n[43] 43\nbad cursor: 400',
'The fixture scans all three in-memory records then slices two, so it is O(n) per call. A database implementation should use a tenant-scoped index range query and LIMIT. Cursor validation here does not prove identity, persistence or concurrent-page stability.',
['Apply authorization filters before the page limit.','An in-memory scan does not model indexed database paging cost.'],['python/django-pagination','python/drf-list-visibility','python/flask-routing'],subject='python-web',dependencies=['Flask==3.1.3'])

lesson('sqlite-checkpoint-project','Python SQLite checkpoint project: commit data and cursor together',
'A checkpointed import stores its records and last accepted source offset in the same transaction.',
'The owned in-memory database has a receipt table and one checkpoint row. A batch beginning at the expected next offset inserts records, then updates the checkpoint before committing. A later batch with a mismatched starting offset is rejected before writing. The fixture shows the accepted state and that a rejected batch leaves both records and checkpoint unchanged.',
'A source offset alone is not a deduplication key when the upstream can rewrite history or deliver a different payload at the same position. Real importers need source identity, input integrity, replay policy and recovery after a crash. [[python/sqlite-transactions|Transactions]], [[python/sqlite-cli-project|Local imports]] and [[python/idempotent-jobs|Replay identity]] explain those limits.',
r'''import sqlite3

connection = sqlite3.connect(":memory:")
connection.execute("CREATE TABLE receipt(offset INTEGER PRIMARY KEY, identifier TEXT NOT NULL)")
connection.execute("CREATE TABLE checkpoint(id INTEGER PRIMARY KEY CHECK(id=1), last_offset INTEGER NOT NULL)")
connection.execute("INSERT INTO checkpoint VALUES (1, 0)")
connection.commit()

def ingest(start, identifiers):
    if type(start) is not int or start <= 0 or type(identifiers) is not list or not 1 <= len(identifiers) <= 10 or any(type(identifier) is not str or len(identifier) != 3 for identifier in identifiers):
        raise ValueError("bounded import")
    with connection:
        previous = connection.execute("SELECT last_offset FROM checkpoint WHERE id=1").fetchone()[0]
        if start != previous + 1:
            raise ValueError("offset gap or replay")
        for offset, identifier in enumerate(identifiers, start):
            connection.execute("INSERT INTO receipt VALUES (?, ?)", (offset, identifier))
        connection.execute("UPDATE checkpoint SET last_offset=? WHERE id=1", (start + len(identifiers) - 1,))

ingest(1, ["R41", "R42"])
try:
    ingest(4, ["R43"])
except ValueError:
    print("gap rejected")
print("rows:", connection.execute("SELECT offset,identifier FROM receipt ORDER BY offset").fetchall())
print("checkpoint:", connection.execute("SELECT last_offset FROM checkpoint").fetchone()[0])
connection.close()''',"gap rejected\nrows: [(1, 'R41'), (2, 'R42')]\ncheckpoint: 2",
'Each batch inserts k rows with index maintenance and one checkpoint update inside a transaction. The fixture is in memory and sequential; disk durability, writer contention and source acknowledgements require separate tests.',
['Do not advance the cursor independently of the committed records.','An offset alone cannot prove replay payload identity.'],['python/sqlite-transactions','python/sqlite-cli-project','python/idempotent-jobs'],subject='python-projects')

lesson('floyd-warshall-paths','Python Floyd-Warshall: all-pairs costs with negative-cycle rejection',
'Floyd-Warshall computes shortest-path costs between every pair by considering each vertex as an allowed intermediate.',
'The owned graph has a negative edge but no negative cycle. The algorithm starts from zero self-distances, keeps the cheapest parallel edge and relaxes through every intermediate vertex. The first source reaches the third vertex with cost seven via the second; an unreachable pair is represented as None in the display. A second graph with a negative cycle is rejected after the diagonal becomes negative.',
'A path cost alone does not reconstruct the path; that needs a next-hop matrix. Never run this cubic algorithm on an unbounded graph. [[python/bellman-ford|Single-source negative edges]], [[python/dijkstra|Nonnegative single-source paths]] and [[python/topological-sort|DAG ordering]] have different cost and input contracts.',
r'''def all_pairs(vertex_count, edges):
    if type(vertex_count) is not int or not 1 <= vertex_count <= 12 or type(edges) is not list or len(edges) > 100:
        raise ValueError("graph bounds")
    infinity = float("inf")
    distance = [[0 if row == col else infinity for col in range(vertex_count)] for row in range(vertex_count)]
    for edge in edges:
        if type(edge) is not tuple or len(edge) != 3:
            raise ValueError("edge tuple")
        start, end, cost = edge
        if any(type(value) is not int for value in edge) or not 0 <= start < vertex_count or not 0 <= end < vertex_count or not -10 <= cost <= 10:
            raise ValueError("edge fields")
        distance[start][end] = min(distance[start][end], cost)
    for middle in range(vertex_count):
        for start in range(vertex_count):
            for end in range(vertex_count):
                distance[start][end] = min(distance[start][end], distance[start][middle] + distance[middle][end])
    if any(distance[index][index] < 0 for index in range(vertex_count)):
        raise ValueError("negative cycle")
    return [[None if value == infinity else value for value in row] for row in distance]

matrix = all_pairs(3, [(0, 1, 5), (1, 2, 2), (0, 2, 9)])
print(matrix[0], matrix[2][0])
try:
    all_pairs(2, [(0, 1, -2), (1, 0, 1)])
except ValueError:
    print("negative cycle rejected")''','[0, 5, 7] None\nnegative cycle rejected',
'O(V^3) relaxation time and O(V^2) matrix storage dominate this implementation. The twelve-vertex cap makes the teaching fixture bounded; it is not a large-network benchmark.',
['A negative edge is allowed; a negative cycle makes shortest cost undefined.','The distance matrix alone does not identify the route.'],['python/bellman-ford','python/dijkstra','python/topological-sort'],subject='python-dsa')

lesson('max-flow-residual','Python maximum flow: residual edges permit earlier choices to be revised',
'A residual network records how much capacity remains on each directed edge and how much existing flow can be undone.',
'The small source-to-sink network has capacity five across its outgoing cut. A breadth-first augmenting-path search repeatedly finds available routes, subtracts bottleneck capacity on forward residual edges and adds it on reverse edges. The returned flow is five. Reverse edges matter when an early route uses capacity needed by a later route; a greedy search that never permits rerouting can stop too early.',
'Capacities are nonnegative bounded integers. This model does not represent cost, fairness or lower bounds, and it does not return the edge-flow decomposition. [[python/bipartite-matching|Unweighted matching]] can be reduced to flow; [[python/graph-bfs|BFS]] explains the path search.',
r'''from collections import deque

def maximum_flow(vertex_count, edges, source, sink):
    if type(vertex_count) is not int or not 2 <= vertex_count <= 8 or type(source) is not int or type(sink) is not int or not 0 <= source < vertex_count or not 0 <= sink < vertex_count or source == sink or type(edges) is not list or len(edges) > 40:
        raise ValueError("network bounds")
    residual = [[0] * vertex_count for _ in range(vertex_count)]
    for edge in edges:
        if type(edge) is not tuple or len(edge) != 3 or any(type(value) is not int for value in edge):
            raise ValueError("integer edge")
        start, end, capacity = edge
        if not 0 <= start < vertex_count or not 0 <= end < vertex_count or not 0 <= capacity <= 1000 or start == end:
            raise ValueError("edge fields")
        residual[start][end] += capacity
    total = 0
    while True:
        parent = {source: None}
        pending = deque([source])
        while pending and sink not in parent:
            current = pending.popleft()
            for neighbor, capacity in enumerate(residual[current]):
                if capacity > 0 and neighbor not in parent:
                    parent[neighbor] = current
                    pending.append(neighbor)
        if sink not in parent:
            return total
        bottleneck = float("inf")
        node = sink
        while node != source:
            previous = parent[node]
            bottleneck = min(bottleneck, residual[previous][node])
            node = previous
        node = sink
        while node != source:
            previous = parent[node]
            residual[previous][node] -= bottleneck
            residual[node][previous] += bottleneck
            node = previous
        total += bottleneck

network = [(0, 1, 3), (0, 2, 2), (1, 2, 1), (1, 3, 2), (2, 3, 3)]
print(maximum_flow(4, network, 0, 3))''','5',
'This adjacency-matrix version scans O(V^2) entries per BFS. With O(VE) augmentations, the conservative bound is O(V^3 E) time and O(V^2) storage; sparse adjacency lists can reduce per-search cost. The eight-vertex/40-edge gate keeps the fixture small.',
['Forward-only residual updates can miss a rerouting path.','Maximum flow alone does not supply a minimum-cost or fair allocation.'],['python/bipartite-matching','python/graph-bfs','python/union-find'],subject='python-dsa')

for subject,title,slugs in [
 ('python','Pull loops and sentinels',['callable-iterator-sentinel']),
 ('python-types','Mutable bytes and snapshots',['bytearray-aliasing']),
 ('python-advanced','Async workers and cached state',['async-to-thread-context','cached-property-invalidation','gather-sibling-lifetime']),
 ('python-interview','Scope and exception order',['try-else-finally-interview','comprehension-scope-interview']),
 ('python-exercises','Merge, runs and dependency checks',['sorted-merge-exercise','run-length-exercise','dag-order-exercise']),
 ('python-testing','Grouped and asynchronous test cases',['unittest-subtests','asyncio-test-fixture']),
 ('python-packaging','Plugin discovery and version selection',['entry-point-discovery','version-specifier-check']),
 ('python-data','Ordered joins and invalid numbers',['pandas-asof-joins','numpy-finite-gate']),
 ('python-web','Indexed list boundaries',['flask-keyset-list']),
 ('python-projects','Stored ingest position',['sqlite-checkpoint-project']),
 ('python-dsa','All-pairs paths and residual capacity',['floyd-warshall-paths','max-flow-residual'])]:
 group(subject,title,slugs)

WORKFLOW_QUESTIONS=[
 ('What stops iter(callable, marker)?',['Identity only','A returned value comparing equal to the marker','A fixed iterator length','A return of None in every case'],1,'The callable is invoked until its result compares equal to the sentinel.'),
 ('What does a memoryview of bytearray observe?',['An immutable copy','Changes to the underlying buffer','Only the initial size and bytes','A decoded Unicode string'],1,'The view aliases the exporting buffer; a bytes conversion makes a copy.'),
 ('Does cancelling an await of asyncio.to_thread forcibly stop its running worker?',['Always','No','Only when the ContextVar is unset','Only for file I/O'],1,'A started blocking thread needs its own stop and side-effect policy.'),
 ('When must a cached_property be invalidated?',['After a source field affecting it changes','Only when the process restarts','Never, it tracks fields automatically','Before every unrelated method'],0,'The cached instance value otherwise becomes stale.'),
 ('What can a sibling do after gather raises its first ordinary exception?',['It always stops','It may continue running','It is rolled back','It loses its task identity'],1,'The caller still owns the lifetime and result of a continuing sibling.'),
 ('When does try else run?',['After every exception','Only after the try body completes without an exception','Only after finally raises','Before the try body'],1,'A caught failure skips else while finally still runs.'),
 ('What do closures made inside one comprehension loop read by default?',['A fresh copied integer each time','The shared loop variable at call time','A global variable','The outer loop name'],1,'Scope isolation does not make per-iteration closure snapshots.'),
 ('What tie policy does the stable merge fixture use?',['Right before left','Left before right','Random insertion order','Drop equal keys'],1,'The less-than-or-equal branch selects the left feed on equal keys.'),
 ('Why does Counter not replace run-length encoding?',['It cannot count','It loses consecutive boundaries and order','It cannot store letters','It changes bytes to strings'],1,'Two separated runs of one state must remain separate.'),
 ('What does a topological-order verifier require for each edge?', ['Source comes before target','Only both nodes appear somewhere','Target comes before source','The graph is weighted'],0,'Every directed dependency must point forward in the proposed order.'),
 ('What does an entry-point load do?', ['Authenticate its publisher','Import and execute the named code','Resolve every dependency','Start a sandbox'],1,'Metadata is a discovery path; loading still executes code.'),
 ('Why are reverse residual edges needed in maximum flow?', ['To sort vertices','To revise an earlier path choice','To encode negative capacity','To remove all cycles'],1,'A later augmenting path may need to undo part of a previous allocation.')]
slug='python-workflow-contracts';title='Python iteration, tasks and algorithm contract quiz';BANKS[slug]=(title,WORKFLOW_QUESTIONS)
refs=['python/callable-iterator-sentinel','python/bytearray-aliasing','python/gather-sibling-lifetime','python/sorted-merge-exercise','python/entry-point-discovery','python/pandas-asof-joins','python/floyd-warshall-paths','python/max-flow-residual']
entry=copy.deepcopy(lookup['quizzes/python-basics']);path='quizzes/'+slug
entry.update(id=str(uuid.uuid5(uuid.NAMESPACE_URL,'https://aitrove.in/'+path)),path=path,title=title,summary='Twelve explained checks on Python iteration, task lifetime, test ownership and graph algorithms.',sort_order=700+len(added),published_at=stamp,updated_at=stamp)
entry['body']=para('A Python self-check tests input markers, shared buffers, async task lifetime, plugin loading and graph contracts.')+'<h2>Review the related lessons</h2><ul>'+''.join('<li><a href="/'+p+'">'+html.escape(lookup[p]['title'])+'</a></li>' for p in refs)+'</ul><h3>Common Mistakes</h3>'+para('Passing these questions does not prove safe plugin loading, distributed task cancellation or large-graph performance. Run the examples and inspect each stated boundary.')
entry['data']['questions']=[dict(prompt=q,options=o,answer=a,explanation=e) for q,o,a,e in WORKFLOW_QUESTIONS]
entry['data']['related']=[dict(path=p,title=lookup[p]['title']) for p in refs]
upsert(entry);added.append(path)
WORKFLOW_REVERSE={
 'python/iterator-protocol':['callable-iterator-sentinel'],
 'python/memoryview-buffers':['bytearray-aliasing'],
 'python/context-variables':['async-to-thread-context'],
 'python/thread-pools':['async-to-thread-context'],
 'python/functools-cache':['cached-property-invalidation'],
 'python/async-task-groups':['gather-sibling-lifetime'],
 'python/exceptions':['try-else-finally-interview'],
 'python/closures':['comprehension-scope-interview'],
 'python/merge-sort':['sorted-merge-exercise'],
 'python/counter-deque':['run-length-exercise'],
 'python/topological-sort':['dag-order-exercise'],
 'python/unittest-contracts':['unittest-subtests'],
 'python/pytest-fixtures':['asyncio-test-fixture'],
 'python/plugin-project':['entry-point-discovery'],
 'python/pyproject-config':['version-specifier-check'],
 'python/pandas-joins':['pandas-asof-joins'],
 'python/numpy-precision':['numpy-finite-gate'],
 'python/django-pagination':['flask-keyset-list'],
 'python/sqlite-cli-project':['sqlite-checkpoint-project'],
 'python/bellman-ford':['floyd-warshall-paths'],
 'python/bipartite-matching':['max-flow-residual']}
for original,slugs in WORKFLOW_REVERSE.items():
 targets=['python/'+slug for slug in slugs];assert original in lookup and all(p in lookup for p in targets)
 item=lookup[original];marker='<h2>Trace the related workflow</h2>'
 item['body']=item['body'].split(marker)[0]+marker+para(', '.join('[['+p+'|'+lookup[p]['title']+']]' for p in targets)+'.')
 known={related['path'] for related in item['data'].get('related',[])}
 item['data'].setdefault('related',[]).extend({'path':p,'title':lookup[p]['title']} for p in targets if p not in known)
 item['updated_at']=stamp
