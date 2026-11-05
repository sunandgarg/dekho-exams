"""Seventh Python pass: resource ownership, update invariants and bounded state."""
lesson('exitstack-transfer','Python ExitStack pop_all: transfer cleanup without discarding it',
'ExitStack stores cleanup operations, and pop_all moves those operations into another stack without running them.',
'The acquisition stack registers release callbacks for a receipt stream and its index. A completed setup transfers both callbacks to the returned owner. Exiting the acquisition block now has nothing to release. The caller closes the owner later, which runs index release before stream release. A failed setup takes the other path: exiting the acquisition block releases its partial resources immediately. The log is an owned list rather than a real storage service, so the order can be checked without filesystem effects.',
'Transfer is not cancellation of cleanup. A caller that loses the returned stack also loses its explicit release boundary; object collection is not a substitute for close. Callbacks registered with callback cannot suppress exceptions through a return value. Failures in cleanup need their own policy. [[python/exit-stack|Multiple acquisition]] and [[python/context-managers|Single resource ownership]] establish the preceding contracts.',
r'''from contextlib import ExitStack

def acquire_bundle(events, fail=False):
    with ExitStack() as pending:
        pending.callback(events.append, "stream released")
        pending.callback(events.append, "index released")
        if fail:
            raise ValueError("index validation")
        return pending.pop_all()

events = []
owner = acquire_bundle(events)
print("before close:", events)
owner.close()
owner.close()
print("after close:", events)
failed_events = []
try:
    acquire_bundle(failed_events, fail=True)
except ValueError:
    print("failed setup:", failed_events)''',"before close: []\nafter close: ['index released', 'stream released']\nfailed setup: ['index released', 'stream released']",
'Registering k callbacks retains O(k) references. Closing executes them in reverse registration order, plus each callback cost. pop_all transfers the registered stack rather than traversing resources to release them. This fixture does not test operating-system handle exhaustion or a callback that fails.',
['Retain and close the new owner after pop_all.','A successful setup must not silently abandon its cleanup callbacks.'],['python/exit-stack','python/context-managers','python/generator-control'],subject='python-advanced')

lesson('exception-group-partition','Python ExceptionGroup split: retain the nested failure structure',
'ExceptionGroup split partitions matching leaf exceptions while preserving the nesting needed to locate those failures.',
'The import batch contains one amount error at the root and another inside a row group beside an I/O failure. Splitting ValueError extracts both amount leaves. The remainder retains the I/O leaf inside its row group. A recursive summarizer visits leaves for the displayed type list; it does not flatten the groups being handled. The original group still owns all three exception objects after the split.',
'Handling the matching subgroup does not handle the remainder. Raising the residual group is one possible policy; logging it and pretending the entire batch succeeded is not. A custom subclass may need derive to preserve its extra fields. This example partitions ordinary Exception leaves; it does not put KeyboardInterrupt or cancellation into an ExceptionGroup. [[python/exception-groups|Grouped propagation]] and [[python/exceptions-interview|Failure traces]] cover the surrounding call boundary.',
r'''def leaf_types(failure):
    if isinstance(failure, BaseExceptionGroup):
        return [name for child in failure.exceptions for name in leaf_types(child)]
    return [type(failure).__name__]

batch = ExceptionGroup("import", [ValueError("amount"),
    ExceptionGroup("row", [OSError("read"), ValueError("identifier")])])
matched, residual = batch.split(ValueError)
print("matched:", leaf_types(matched))
print("residual:", leaf_types(residual))
print("original:", leaf_types(batch))
print("nested remainder:", isinstance(residual.exceptions[0], ExceptionGroup))''',"matched: ['ValueError', 'ValueError']\nresidual: ['OSError']\noriginal: ['ValueError', 'OSError', 'ValueError']\nnested remainder: True",
'Partitioning visits the exception tree and retains references to its matching leaves. This fixture has bounded depth; deeply nested externally constructed groups need a traversal-depth policy. Exception messages and attached tracebacks can retain sensitive values and large object graphs.',
['Do not mark the entire batch handled after processing only one subgroup.','A leaf summary is a reporting view, not the original nested error structure.'],['python/exception-groups','python/exceptions','python/async-task-groups'],subject='python-advanced')

lesson('enum-alias-contract','Python Enum aliases: iteration and member lookup have different domains',
'An Enum alias is a second declared name that refers to an existing member with the same value.',
'The receipt status definition keeps NEW as an alias of PENDING. Ordinary iteration returns each canonical member once, while __members__ contains every declared name, including NEW. Reading the alias name returns the canonical member whose name is PENDING. That matters when a received value must round-trip through a stored status: aliases preserve lookup compatibility but do not preserve the original spelling.',
'Use unique when duplicate values are a schema mistake rather than an intended compatibility policy. Enum aliases are distinct from two external strings mapped to one field by a parser. Do not serialize the Python class name as an enduring wire identifier. [[python/enums|Status values]], [[python/json-validation|Wire schema]] and [[python/dictionaries|Name lookup]] remain separate concerns.',
r'''from enum import Enum, unique

class ReceiptStatus(Enum):
    PENDING = "pending"
    NEW = "pending"
    POSTED = "posted"

print("iteration:", [member.name for member in ReceiptStatus])
print("declared:", list(ReceiptStatus.__members__))
print("alias identity:", ReceiptStatus.NEW is ReceiptStatus.PENDING)
print("alias canonical name:", ReceiptStatus["NEW"].name)
try:
    unique(ReceiptStatus)
except ValueError:
    print("duplicate values rejected")''',"iteration: ['PENDING', 'POSTED']\ndeclared: ['PENDING', 'NEW', 'POSTED']\nalias identity: True\nalias canonical name: PENDING\nduplicate values rejected",
'Lookup uses the declared member mapping. Iteration visits canonical members, so counts differ when aliases exist. Creating a large enum and its mappings has construction and retained-object costs; this two-value definition is not a benchmark.',
['Iteration omits aliases; use __members__ when examining declared names.','An alias cannot retain an independently chosen canonical name.'],['python/enums','python/json-validation','python/hash-equality'],subject='python-types')

lesson('fraction-ratios','Python Fraction: exact ratios require an exact input representation',
'Fraction stores a rational number as a reduced integer numerator and a positive integer denominator.',
'The invoice allocation uses three tenths as an exact ratio and applies it to a bounded integer amount. Multiplication produces a rational result, so a nonintegral minor-unit amount remains visible rather than being rounded silently. Fraction constructed from the string 0.1 represents one tenth; Fraction constructed from the float 0.1 preserves that float’s binary value instead. limit_denominator selects an approximation under its cap. It does not recover the sender’s intent.',
'A payment ledger still needs an allocation remainder and rounding policy. Reject Boolean values, unbounded denominators and nonpositive divisors before invoking rational arithmetic. Exactness can increase retained digits when repeated operations combine unrelated denominators. [[python/decimal-money|Decimal money]] and [[python/numpy-precision|Floating precision]] address different numeric domains.',
r'''from fractions import Fraction

def allocation(amount, numerator, denominator):
    if any(type(value) is not int for value in (amount, numerator, denominator)):
        raise ValueError("exact integer fields")
    if not 0 <= amount <= 100000 or not 0 <= numerator <= denominator <= 1000 or denominator == 0:
        raise ValueError("allocation bounds")
    return amount * Fraction(numerator, denominator)

print("allocation:", allocation(125, 3, 10))
print("text exact:", Fraction("0.1") == Fraction(1, 10))
print("float exact:", Fraction(0.1) == Fraction(1, 10))
print("approximation:", Fraction(0.1).limit_denominator(10))
try:
    allocation(125, 1, 0)
except ValueError:
    print("zero denominator rejected")''','allocation: 75/2\ntext exact: True\nfloat exact: False\napproximation: 1/10\nzero denominator rejected',
'Reduction performs integer arithmetic and a greatest-common-divisor operation. Cost depends on digit length, not only the count of fields. The accepted bounds cap this fixture’s operands; a general rational accumulator needs its own digit and batch limits.',
['Constructing a Fraction from float preserves the float’s value.','Exact arithmetic does not decide how a fractional minor unit should be posted.'],['python/decimal-money','python/type-conversion','python/numpy-precision'],subject='python-types')

lesson('zone-local-classification','Python ZoneInfo: classify unique, repeated and missing local times',
'A named-zone local clock reading can identify one UTC instant, two instants during a backward transition, or no instant during a forward transition.',
'The classifier accepts a naive datetime and an existing ZoneInfo object. It builds both fold candidates, converts each to UTC and back, and retains only candidates whose round-trip reproduces the same local fields. UTC instants are deduplicated because a normal time gives the same instant for both folds. The New York fixtures show one ordinary time, the repeated 01:30 autumn reading, and the missing 02:30 spring reading. No candidate is selected automatically.',
'Attaching tzinfo does not itself reject a nonexistent local time. Returning two candidates lets the application ask for an offset or a deliberate earlier/later choice. Returning none requires rejection or a separately declared adjustment policy. Zone rules depend on the installed IANA data. [[python/timezone-fold|Fold behavior]] and [[python/datetime-boundaries|Offset-required ingestion]] provide the next step after classification.',
r'''from datetime import datetime, timezone
from zoneinfo import ZoneInfo

def local_candidates(local, zone):
    if type(local) is not datetime or local.tzinfo is not None or not isinstance(zone, ZoneInfo):
        raise ValueError("naive datetime and named zone required")
    candidates = set()
    for fold in (0, 1):
        instant = local.replace(tzinfo=zone, fold=fold).astimezone(timezone.utc)
        restored = instant.astimezone(zone).replace(tzinfo=None)
        if restored == local:
            candidates.add(instant)
    return sorted(candidates)

zone = ZoneInfo("America/New_York")
for local in (datetime(2024, 2, 1, 12), datetime(2024, 11, 3, 1, 30),
              datetime(2024, 3, 10, 2, 30)):
    print("candidates:", len(local_candidates(local, zone)))
print("repeated UTC:", [value.strftime("%H:%M") for value in
      local_candidates(datetime(2024, 11, 3, 1, 30), zone)])''',"candidates: 1\ncandidates: 2\ncandidates: 0\nrepeated UTC: ['05:30', '06:30']",
'Two conversion paths give bounded application work per reading, plus zone transition lookup. This is classification for the installed data, not a promise about future government timezone changes. Persist the chosen instant and, when relevant, the original zone and selection policy.',
['Do not treat replace(tzinfo=zone) as validation of a local reading.','Do not silently resolve a repeated reading by whichever fold happens to be the default.'],['python/timezone-fold','python/datetime-boundaries','java/zone-transitions'],subject='python-types')

lesson('singledispatch-contract','Python singledispatch: dispatch follows the first argument’s type',
'Singledispatch chooses a registered implementation from the runtime type of the first positional argument.',
'The default receipt encoder rejects unsupported types. The integer implementation has an exact-type and amount check, while a Boolean registration explicitly rejects bool before its int inheritance can select the numeric route. A text implementation only accepts a small ASCII decimal representation and forwards the converted value to the same integer rule. This keeps two accepted input formats behind one amount contract.',
'Dispatch is not schema validation. Registering int does not imply that every int subclass or every integer magnitude is a valid amount. Other arguments do not participate in singledispatch selection. A broad object registration changes the fallback, and extension registration is a trusted code action. [[python/first-class-functions|Callables]], [[python/type-conversion|Conversion]] and [[python/subclass-hooks|Subclass behavior]] explain those boundaries.',
r'''from functools import singledispatch

@singledispatch
def encoded_amount(amount):
    raise ValueError("unsupported representation")

@encoded_amount.register(int)
def encode_integer(amount):
    if type(amount) is not int or not 0 <= amount <= 1000:
        raise ValueError("bounded exact integer")
    return f"minor:{amount}"

@encoded_amount.register(bool)
def reject_boolean(amount):
    raise ValueError("boolean amount")

@encoded_amount.register(str)
def encode_text(amount):
    if not 1 <= len(amount) <= 4 or any(character not in "0123456789" for character in amount):
        raise ValueError("ASCII amount")
    return encode_integer(int(amount))

print(encoded_amount(125))
print(encoded_amount("75"))
for invalid in (True, 1.5, "-1"):
    try:
        encoded_amount(invalid)
    except ValueError:
        print("representation rejected")''','minor:125\nminor:75\nrepresentation rejected\nrepresentation rejected\nrepresentation rejected',
'Initial dispatch may examine type relationships; subsequent dispatches can use cached decisions. This is not a fixed-cost promise for arbitrary class hierarchies. The four-character text cap bounds conversion work; formatting a general unbounded integer needs a separate cost policy.',
['bool is an int subclass, so numeric registration needs a Boolean policy.','singledispatch does not inspect all arguments or enforce annotated types.'],['python/first-class-functions','python/type-conversion','python/subclass-hooks'],subject='python-advanced')

lesson('ordering-protocol','Python rich comparison: return NotImplemented for unsupported operands',
'NotImplemented tells Python that a comparison method does not implement the supplied operand pair, allowing reflected comparison or the normal fallback.',
'The receipt rank compares only another rank from the same domain. Unsupported values receive NotImplemented rather than false or an arbitrary ordering. total_ordering supplies the other ordering methods from equality and less-than. Equality with an unrelated integer falls back to false, while ordering the same pair raises TypeError. These results are intentional: inequality does not grant a meaningful cross-type order.',
'A rank object should not change its ordering fields while retained inside a sorted structure. This teaching class exposes a simple field and therefore requires caller discipline; use an immutable representation at a public boundary. Returning false for every unrelated comparison can hide mistakes and violate sorting assumptions. [[python/hash-equality|Equality and keys]], [[python/sorting|Stable order]] and [[python/bisect-insertion|Sorted insertion]] depend on a consistent contract.',
r'''from functools import total_ordering

@total_ordering
class ReceiptRank:
    def __init__(self, priority):
        if type(priority) is not int or not 0 <= priority <= 9:
            raise ValueError("priority bound")
        self.priority = priority
    def __eq__(self, other):
        if type(other) is not ReceiptRank:
            return NotImplemented
        return self.priority == other.priority
    def __lt__(self, other):
        if type(other) is not ReceiptRank:
            return NotImplemented
        return self.priority < other.priority

print("ordered:", ReceiptRank(2) < ReceiptRank(4))
print("unrelated equal:", ReceiptRank(2) == 2)
print("method fallback:", ReceiptRank(2).__lt__(2) is NotImplemented)
try:
    ReceiptRank(2) < 2
except TypeError:
    print("unrelated ordering rejected")''','ordered: True\nunrelated equal: False\nmethod fallback: True\nunrelated ordering rejected',
'Each bounded-priority comparison has fixed scalar work. Generated methods can invoke several underlying comparisons rather than performing one primitive operation. This class is unhashable after defining equality; do not add a hash that disagrees with equality.',
['NotImplemented is a result, not the NotImplementedError exception.','Returning false is not the same as declining an unsupported comparison.'],['python/hash-equality','python/sorting','python/bisect-insertion'],subject='python-advanced')

lesson('sqlite-savepoints','Python SQLite savepoints: discard one substep without committing the batch',
'A SQLite savepoint marks a position inside a transaction that can be rolled back while preserving earlier uncommitted work.',
'The ledger starts an explicit transaction, writes receipt 41, then opens a named savepoint for a second import step. A duplicate primary key fails inside that step after receipt 42 was inserted. ROLLBACK TO removes the step’s changes, and RELEASE removes its savepoint marker. Receipt 43 is then accepted and the outer transaction commits only receipts 41 and 43. A second transaction releases a successful inner step and subsequently rolls back its outer transaction, proving that inner release did not commit independently.',
'ROLLBACK TO leaves the named savepoint active; RELEASE is a separate operation. Use constant owned names or a controlled naming mechanism, not received SQL fragments. A failed cleanup or commit needs a caller policy. [[python/sqlite-transactions|Outer transactions]], [[python/sqlite-writer-contention|Writer conflicts]] and [[python/django-atomic|Framework nesting]] describe related boundaries.',
r'''import sqlite3

connection = sqlite3.connect(":memory:", isolation_level=None)
try:
    connection.execute("CREATE TABLE receipt(id INTEGER PRIMARY KEY)")
    connection.execute("BEGIN")
    connection.execute("INSERT INTO receipt VALUES (41)")
    connection.execute("SAVEPOINT import_step")
    try:
        connection.execute("INSERT INTO receipt VALUES (42)")
        connection.execute("INSERT INTO receipt VALUES (41)")
    except sqlite3.IntegrityError:
        connection.execute("ROLLBACK TO import_step")
    connection.execute("RELEASE import_step")
    connection.execute("INSERT INTO receipt VALUES (43)")
    connection.execute("COMMIT")
    print("committed:", connection.execute("SELECT id FROM receipt ORDER BY id").fetchall())
    connection.execute("BEGIN")
    connection.execute("SAVEPOINT accepted_step")
    connection.execute("INSERT INTO receipt VALUES (44)")
    connection.execute("RELEASE accepted_step")
    connection.execute("ROLLBACK")
    print("after outer rollback:", connection.execute("SELECT COUNT(*) FROM receipt").fetchone()[0])
finally:
    connection.close()''','committed: [(41,), (43,)]\nafter outer rollback: 2',
'Transaction costs depend on changed pages, indexes and storage policy. This owned in-memory database establishes savepoint behavior, not disk durability, multi-engine isolation or production throughput. Nested markers do not create independent committed database copies.',
['Release inside an outer transaction does not make the inner writes durable.','ROLLBACK TO does not remove its savepoint marker.'],['python/sqlite-transactions','python/sqlite-writer-contention','python/django-atomic'],subject='python-examples')

lesson('spooled-file-budgets','Python SpooledTemporaryFile: rollover is a storage choice, not an upload limit',
'SpooledTemporaryFile starts in memory and can roll into an owned temporary file when its storage threshold is crossed or rollover is requested.',
'The staging function receives immutable bytes, rejects more than 32 bytes before writing, and uses an eight-byte spool threshold. It then explicitly requests rollover and verifies that reading back preserves the exact bytes. The explicit rollover avoids probing private fields or relying on a particular threshold implementation. Closing the context releases the temporary storage. The application cap and spool threshold remain separate: the threshold alone would accept a much larger write.',
'Calling fileno can also force disk backing, so a library that requests a descriptor may change the storage path unexpectedly. The input bytes already exist before this function checks their length. A network reader must cap reception before allocating them. [[python/flask-multipart-budgets|Upload boundaries]], [[python/bounded-json-lines|Bounded reading]] and [[python/pathlib-files|Publication]] cover those next stages.',
r'''from tempfile import SpooledTemporaryFile

def stage_payload(payload):
    if type(payload) is not bytes or len(payload) > 32:
        raise ValueError("byte payload cap")
    with SpooledTemporaryFile(max_size=8, mode="w+b") as staging:
        staging.write(payload)
        staging.rollover()
        staging.seek(0)
        restored = staging.read(33)
        return restored

print("round trip:", stage_payload(b"receipt:41") == b"receipt:41")
print("empty:", stage_payload(b""))
try:
    stage_payload(b"x" * 33)
except ValueError:
    print("application cap rejected")''',"round trip: True\nempty: b''\napplication cap rejected",
'Writing and reading n accepted bytes costs O(n) byte work and storage. Rollover can copy buffered data and add filesystem costs. A per-file cap does not bound simultaneous files, disk quota, file descriptors or whole-process memory.',
['max_size is a rollover threshold, not a rejection threshold.','Do not inspect private spool fields as a portable storage contract.'],['python/flask-multipart-budgets','python/bounded-json-lines','python/pathlib-files'],subject='python-examples')

lesson('socket-frame-reading','Python socket recv: assemble a bounded frame across partial reads',
'A stream socket exposes an ordered byte stream, so one recv call does not identify an application message boundary.',
'The local socket pair carries a two-byte big-endian length followed by a payload. read_exact keeps receiving until its requested count is assembled or EOF rejects truncation. It intentionally requests at most two bytes per call, making the loop exercise partial application reads even on the local fixture. read_frame checks the declared size before requesting the body. A second pair contains a length of five but only two body bytes, then closes its sending direction; the receiver detects that short frame.',
'A timeout on each receive call is not an absolute operation deadline: a peer can keep delivering tiny chunks before each timeout. The fixture uses already sent local bytes, no remote host, and a one-second socket timeout. [[python/binary-records|Record layout]], [[python/async-deadlines|Whole-operation deadlines]] and [[python/gzip-output-budget|Decoded output bounds]] cover independent layers.',
r'''import socket

def read_exact(stream, count):
    chunks = bytearray()
    while len(chunks) < count:
        chunk = stream.recv(min(2, count - len(chunks)))
        if not chunk:
            raise EOFError("truncated frame")
        chunks.extend(chunk)
    return bytes(chunks)

def read_frame(stream):
    length = int.from_bytes(read_exact(stream, 2), "big")
    if length > 32:
        raise ValueError("frame cap")
    return read_exact(stream, length)

for wire in (b"\x00\x05R0041", b"\x00\x05R0", b"\x00\x21"):
    sender, receiver = socket.socketpair()
    with sender, receiver:
        receiver.settimeout(1)
        sender.sendall(wire)
        sender.shutdown(socket.SHUT_WR)
        try:
            print("payload:", read_frame(receiver))
        except (EOFError, ValueError) as failure:
            print(type(failure).__name__)''',"payload: b'R0041'\nEOFError\nValueError",
'The accepted body has at most 32 bytes, so this frame reader has bounded retained payload storage. Repeated frames still need a connection-wide count, byte budget and absolute deadline. A successful frame leaves following bytes for the next frame; it is not proof that the stream has no extra messages.',
['recv may return fewer bytes than requested without reaching EOF.','Check declared length before reading or allocating the body.'],['python/binary-records','python/async-deadlines','python/bounded-json-lines'],subject='python-examples')

lesson('url-target-policy','Python urlsplit: parsing a URL does not authorize a request target',
'Urlsplit separates URL components without establishing that the result belongs to an application’s accepted target set.',
'The policy accepts only an ASCII HTTPS URL at learn.aitrove.in, an absent or 443 port, exactly one allowed path, and no user information, query or fragment. Controls and spaces are rejected before parsing because a parser may discard some leading or embedded characters. The function returns a canonical owned target string instead of forwarding received text. No URL is requested by this program; the host is a teaching identifier.',
'This narrow policy is not a general SSRF defense. A real request still needs DNS/address restrictions, redirect checks, TLS verification and network policy at every connection. Percent-encoded path variants are rejected rather than decoded into the accepted path. [[python/regex-validation|Field alphabets]], [[python/json-validation|Schema validation]] and [[python/subprocess-boundaries|Received commands]] use the same separation between parsing and permission.',
r'''from urllib.parse import urlsplit

def accepted_target(text):
    if type(text) is not str or not 1 <= len(text) <= 128 or any(not 33 <= ord(char) <= 126 for char in text):
        raise ValueError("ASCII target bound")
    parsed = urlsplit(text)
    if (parsed.scheme != "https" or parsed.hostname != "learn.aitrove.in" or
        parsed.username is not None or parsed.password is not None or
        parsed.port not in (None, 443) or parsed.path != "/receipts" or
        parsed.query or parsed.fragment):
        raise ValueError("target policy")
    return "https://learn.aitrove.in/receipts"

print(accepted_target("https://learn.aitrove.in:443/receipts"))
for target in ("https://learn.aitrove.in.evil/receipts",
               "https://user@learn.aitrove.in/receipts", "\nhttps://learn.aitrove.in/receipts"):
    try:
        accepted_target(target)
    except ValueError:
        print("target rejected")''','https://learn.aitrove.in/receipts\ntarget rejected\ntarget rejected\ntarget rejected',
'The 128-character gate bounds parser work and returned storage. Address resolution and network costs are absent. Reusing a hostname allowlist as a production network-boundary claim would omit rebinding, redirects and private-address routing.',
['A parsed hostname is not proof that a request is safe or permitted.','Reject controls before a parser normalizes the received text.'],['python/regex-validation','python/json-validation','python/flask-routing'],subject='python-web')

lesson('radix-trie-updates','Python compressed trie updates: split on insertion and compact after deletion',
'A compressed trie stores multi-character edge labels and keeps terminal markers where complete keys end.',
'The owned trie accepts at most 64 distinct lowercase ASCII keys, each no longer than 16 characters. Insertion scans for an edge with the same first character, consumes a shared prefix, and splits an edge when a key ends or diverges inside it. Deletion removes only the terminal marker for the exact key. An empty child is pruned; a nonterminal child with one edge is merged into its parent edge. A terminal prefix is never merged away. The test sequence inserts car, cart, carbon and cat, removes car, then confirms the longer keys survive.',
'The tree stores set membership, not counts or payload records. Missing deletion returns false and repeated insertion leaves the set unchanged. An empty key is rejected so the root has no special terminal-key role. Recursion is bounded by the 16-character key contract. [[python/compressed-trie|Static edge compression]], [[python/trie-deletion|Uncompressed removal]] and [[python/trie-prefix|Prefix membership]] establish the comparison.',
r'''class RadixSet:
    def __init__(self):
        self.root = [False, {}]
        self.size = 0
    def validate(self, key):
        if type(key) is not str or not 1 <= len(key) <= 16 or any(char not in "abcdefghijklmnopqrstuvwxyz" for char in key):
            raise ValueError("bounded ASCII key")
    def contains(self, key):
        self.validate(key)
        node = self.root
        while key:
            edge = next((label for label in node[1] if key.startswith(label)), None)
            if edge is None:
                return False
            key, node = key[len(edge):], node[1][edge]
        return node[0]
    def add(self, key):
        self.validate(key)
        if self.contains(key):
            return False
        if self.size >= 64:
            raise ValueError("key capacity")
        def insert(node, suffix):
            if not suffix:
                node[0] = True
                return
            for label, child in list(node[1].items()):
                shared = 0
                while shared < min(len(label), len(suffix)) and label[shared] == suffix[shared]:
                    shared += 1
                if not shared:
                    continue
                if shared == len(label):
                    insert(child, suffix[shared:])
                else:
                    branch = [False, {label[shared:]: child}]
                    del node[1][label]
                    node[1][label[:shared]] = branch
                    insert(branch, suffix[shared:])
                return
            node[1][suffix] = [True, {}]
        insert(self.root, key)
        self.size += 1
        return True
    def discard(self, key):
        self.validate(key)
        def remove(node, suffix):
            if not suffix:
                if not node[0]:
                    return False
                node[0] = False
                return True
            for label, child in list(node[1].items()):
                if not suffix.startswith(label):
                    continue
                if not remove(child, suffix[len(label):]):
                    return False
                if not child[0] and not child[1]:
                    del node[1][label]
                elif not child[0] and len(child[1]) == 1:
                    extension, descendant = next(iter(child[1].items()))
                    del node[1][label]
                    node[1][label + extension] = descendant
                return True
            return False
        removed = remove(self.root, key)
        self.size -= int(removed)
        return removed

index = RadixSet()
for identifier in ("car", "cart", "carbon", "cat"):
    index.add(identifier)
print("removed prefix:", index.discard("car"))
print("membership:", [index.contains(key) for key in ("car", "cart", "carbon", "cat")])
print("missing removal:", index.discard("cab"))
print("duplicate:", index.add("cart"))
print("size:", index.size)''',"removed prefix: True\nmembership: [False, True, True, True]\nmissing removal: False\nduplicate: False\nsize: 3",
'Each node scans at most 26 outgoing first-character choices under the declared alphabet. Traversal comparisons follow the key, but Python slicing and concatenation allocate strings; this implementation can perform O(L squared) copied-character work along a deeply split L-character key. Distinct-key storage is bounded by total stored key characters plus node/mapping overhead. It is not a compact native-memory index or a concurrent structure.',
['Never merge away a terminal prefix during compaction.','Deleting a prefix must not delete the subtree containing longer keys.'],['python/compressed-trie','python/trie-deletion','python/trie-prefix'],subject='python-dsa')

lesson('bipartite-matching','Python bipartite matching: augment an assignment instead of taking the first free slot',
'A bipartite matching assigns pairs across two vertex sets without using a vertex in more than one pair.',
'The roster lists which workers may take which slots. Each worker attempts a path through its allowed slots; if a slot is occupied, the search tries moving its current worker elsewhere. The new worker succeeds only when that chain reaches a free slot. A per-attempt visited-slot set prevents repeated traversal. The example makes the flexible worker move from slot zero to slot one, allowing the restricted worker to take slot zero. First-free greedy assignment would miss that second match.',
'The graph accepts up to eight workers and eight slots, with exact integer endpoints and no duplicate edge in a worker row. It maximizes pair count, not fairness, priority or total monetary weight. Traversal order makes the displayed assignment repeatable but does not imply a unique optimum. [[python/graph-bfs|Reachability]], [[python/union-find|Components]] and [[python/weighted-intervals|Weighted selection]] solve different graph or optimization problems.',
r'''def maximum_assignment(allowed, slot_count):
    if type(allowed) is not list or len(allowed) > 8 or type(slot_count) is not int or not 0 <= slot_count <= 8:
        raise ValueError("roster bounds")
    for row in allowed:
        if type(row) is not list or any(type(slot) is not int or not 0 <= slot < slot_count for slot in row) or len(set(row)) != len(row):
            raise ValueError("slot endpoints")
    owners = [-1] * slot_count
    def augment(worker, visited):
        for slot in allowed[worker]:
            if slot in visited:
                continue
            visited.add(slot)
            if owners[slot] == -1 or augment(owners[slot], visited):
                owners[slot] = worker
                return True
        return False
    for worker in range(len(allowed)):
        augment(worker, set())
    return sorted((worker, slot) for slot, worker in enumerate(owners) if worker != -1)

print("pairs:", maximum_assignment([[0, 1], [0]], 2))
print("isolated:", maximum_assignment([[], [1]], 2))
print("empty:", maximum_assignment([], 0))
try:
    maximum_assignment([[True]], 2)
except ValueError:
    print("Boolean endpoint rejected")''',"pairs: [(0, 1), (1, 0)]\nisolated: [(1, 1)]\nempty: []\nBoolean endpoint rejected",
'Each augmentation scans reachable edges with visited slots, and at most W attempts are made for W workers. The usual bound is O(W times E) edge work plus validation and output sorting; slot ownership takes O(S) storage. The small explicit caps bound recursion. This is the simple augmenting-path algorithm, not Hopcroft-Karp or a measured production scheduler.',
['Greedy first-free assignment can leave a feasible slot unused.','A maximum-cardinality match says nothing about fairness or weighted cost.'],['python/graph-bfs','python/weighted-intervals','python/topological-sort'],subject='python-dsa')

lesson('weighted-intervals','Python weighted interval scheduling: reconstruct the accepted nonoverlapping jobs',
'Weighted interval scheduling chooses a nonoverlapping subset of intervals whose total declared weight is maximal.',
'The job tuple contains start, end and nonnegative reward. Endpoints are half-open, so one job ending at time four is compatible with another starting at four. Sorting by end time lets a binary search locate the last compatible prefix. Each DP entry compares skipping the current job with taking it plus the best compatible prefix. Reconstruction follows those same decisions and reports original input indices. Ties deliberately skip the current job; the policy chooses one optimum without claiming every optimum is identical.',
'The boundary accepts at most 16 jobs, exact integer fields within zero to 1000, and strictly positive duration. Negative rewards and Boolean timestamps are rejected. The supplied list is copied into indexed records and remains unchanged. [[python/bisect-insertion|Binary search endpoints]], [[python/knapsack|State choice]] and [[python/expiry-exercise|Exact interval endpoints]] explain the constituent contracts.',
r'''from bisect import bisect_right

def best_schedule(jobs):
    if type(jobs) is not list or len(jobs) > 16:
        raise ValueError("job capacity")
    for job in jobs:
        if type(job) is not tuple or len(job) != 3 or any(type(value) is not int or not 0 <= value <= 1000 for value in job) or job[0] >= job[1]:
            raise ValueError("job fields")
    ordered = sorted((end, start, reward, index) for index, (start, end, reward) in enumerate(jobs))
    ends = [job[0] for job in ordered]
    best, previous, take = [0], [], []
    for position, (end, start, reward, identifier) in enumerate(ordered):
        prefix = bisect_right(ends, start, 0, position)
        candidate = best[prefix] + reward
        previous.append(prefix)
        take.append(candidate > best[-1])
        best.append(max(best[-1], candidate))
    chosen = []
    position = len(ordered)
    while position:
        if take[position - 1]:
            chosen.append(ordered[position - 1][3])
            position = previous[position - 1]
        else:
            position -= 1
    return best[-1], list(reversed(chosen))

print("schedule:", best_schedule([(0, 4, 5), (1, 3, 4), (3, 5, 4), (4, 6, 5)]))
print("empty:", best_schedule([]))
try:
    best_schedule([(2, 2, 10)])
except ValueError:
    print("empty duration rejected")''','schedule: (10, [0, 3])\nempty: (0, [])\nempty duration rejected',
'Sorting and n binary searches cost O(n log n), with O(n) DP and reconstruction storage. The n<=16 fixture also permits an independent exhaustive-subset oracle in tests. Real schedules may need resources, dependencies, setup costs or fairness constraints that this one-resource interval model does not express.',
['Use the declared half-open boundary when testing compatibility.','An optimal total alone does not verify that the reconstructed jobs are compatible.'],['python/bisect-insertion','python/knapsack','python/expiry-exercise'],subject='python-dsa')

lesson('covariance-policy','Python covariance: state the denominator and preserve paired observations',
'Covariance measures joint variation of paired observations around their respective means, with a declared sample or population denominator.',
'The receipt fixture treats x and y as paired measurements. It rejects unequal lengths, fewer than two pairs, Boolean values, nonfinite values and magnitudes over one million. Centered products are summed with fsum and divided by n minus one for sample covariance or n for population covariance. The same three pairs therefore produce sample covariance four and population covariance eight thirds. Magnitude is checked before the finite-number conversion so an oversized integer is rejected by the declared boundary instead of overflowing during a float conversion. Pair membership stays fixed; sorting one column separately would change the question.',
'This is descriptive calculation, not evidence that one variable causes the other. fsum reduces summation error but does not make input floats or centered products exact. Extreme ranges can still lose information, so bounds and a recorded unit remain relevant. [[python/quantile-policy|Estimator choices]], [[python/numpy-precision|Numeric representation]] and [[python/pandas-null-joins|Pair membership]] affect the interpretation.',
r'''import math

def paired_covariance(left, right, *, sample=True):
    if type(sample) is not bool or type(left) is not list or type(right) is not list or not 2 <= len(left) == len(right) <= 64:
        raise ValueError("paired lengths")
    if any(type(value) not in (int, float) or abs(value) > 1000000 or not math.isfinite(value) for value in left + right):
        raise ValueError("finite bounded observations")
    count = len(left)
    left_mean, right_mean = math.fsum(left) / count, math.fsum(right) / count
    centered = math.fsum((x - left_mean) * (y - right_mean) for x, y in zip(left, right, strict=True))
    return centered / (count - int(sample))

print("sample:", paired_covariance([1, 2, 3], [2, 4, 10]))
print("population:", round(paired_covariance([1, 2, 3], [2, 4, 10], sample=False), 6))
try:
    paired_covariance([1, 2], [2, float("nan")])
except ValueError:
    print("nonfinite pair rejected")''','sample: 4.0\npopulation: 2.666667\nnonfinite pair rejected',
'Two passes over n pairs give O(n) arithmetic work. The implementation concatenates validation lists and builds no matrix, so it retains O(n) temporary references. With <=64 bounded observations, product magnitude remains modest; larger data, streaming summaries and parallel merges need separate error analysis.',
['Sorting or filtering one column alone destroys observation pairing.','Sample and population denominators answer different declared questions.'],['python/quantile-policy','python/numpy-precision','python/bootstrap-means'],subject='python-data')

lesson('numpy-shape-contract','Python NumPy shape validation: reject accidental broadcasting before arithmetic',
'NumPy broadcasting aligns trailing dimensions, allowing compatible size-one axes to expand without copying the input for each result position.',
'The demand matrix has one row per warehouse and one column per product. The price contract requires exactly one price for each product, represented as a one-dimensional vector. A shape of two by one could broadcast per warehouse and still produce a result, so compatibility alone is insufficient. The boundary converts to float64, caps matrix dimensions at eight, rejects nonfinite inputs and checks the price shape before multiplication. It returns one cost total per warehouse.',
'The requested domain shape is stricter than NumPy’s broadcasting rules. Conversion can allocate before the post-conversion size gate; this is a trusted local input fixture, not a serialized-array reception boundary. float64 costs are approximate and are not an exact currency ledger. [[python/numpy-broadcasting|Broadcast rules]], [[python/numpy-views|Array ownership]] and [[python/decimal-money|Monetary units]] cover the adjacent decisions.',
r'''import numpy as np

def warehouse_costs(demand, prices):
    matrix = np.asarray(demand, dtype=np.float64)
    vector = np.asarray(prices, dtype=np.float64)
    if matrix.ndim != 2 or any(not 1 <= size <= 8 for size in matrix.shape) or vector.shape != (matrix.shape[1],):
        raise ValueError("warehouse/product shape")
    if not np.isfinite(matrix).all() or not np.isfinite(vector).all() or (matrix < 0).any() or (vector < 0).any():
        raise ValueError("finite nonnegative values")
    return (matrix * vector).sum(axis=1)

print("totals:", warehouse_costs([[2, 1], [1, 3]], [1.5, 2.0]).tolist())
try:
    warehouse_costs([[2, 1], [1, 3]], [[1.5], [2.0]])
except ValueError:
    print("broadcastable wrong shape rejected")''',"totals: [5.0, 7.5]\nbroadcastable wrong shape rejected",
'For R warehouses and C products, multiplication and reduction take O(R times C) arithmetic and the intermediate product matrix retains O(R times C) floats. Broadcasting does not eliminate that result allocation. These fixtures have small nonoverflowing values; the boundary does not cap arbitrary finite magnitudes or guarantee finite outputs for every finite input.',
['A broadcastable array can still represent the wrong domain axis.','Broadcasting avoids repeated input copies, not every result allocation.'],['python/numpy-broadcasting','python/numpy-views','python/numpy-precision'],subject='python-data',dependencies=['numpy==2.5.3'])

lesson('lease-renewal-project','Python SQLite lease renewal: reject stale tokens and exact-expiry ownership',
'A lease renewal extends a stored expiry only while the supplied token still owns an unexpired claim.',
'The project stores one job with a token and an integer expiry in an owned SQLite database. Renewal validates exact bounded fields, starts BEGIN IMMEDIATE, and conditionally updates the row only when its token matches and expiry is strictly greater than now. The new expiry must move forward and may extend at most ten clock units from the supplied time. A stale token, a nonextending expiry and a request exactly at expiry return false without replacing state. Two real connections use the same file to observe the accepted update.',
'The token is caller-supplied teaching data, not a generated secret or a trusted identity. A deployment must choose a clock domain, prevent clock regression, generate unique claims and authenticate workers. Renewal also cannot revoke an already running external side effect. [[python/leased-outbox-project|Claim and reclaim]], [[python/idempotent-jobs|Replay policy]] and [[python/sqlite-writer-contention|Writer contention]] complete the workflow around this one transition.',
r'''import sqlite3
import tempfile
from pathlib import Path

def renew(connection, identifier, token, now, new_expiry):
    if type(identifier) is not int or not 1 <= identifier <= 1000 or type(token) is not str or not 1 <= len(token) <= 32:
        raise ValueError("claim fields")
    if any(type(value) is not int or not 0 <= value <= 1000000 for value in (now, new_expiry)) or not now < new_expiry <= now + 10:
        raise ValueError("clock/extension bounds")
    connection.execute("BEGIN IMMEDIATE")
    try:
        changed = connection.execute("UPDATE job SET expiry=? WHERE id=? AND token=? AND expiry>? AND expiry<?",
            (new_expiry, identifier, token, now, new_expiry)).rowcount == 1
        connection.execute("COMMIT")
        return changed
    except BaseException:
        connection.execute("ROLLBACK")
        raise

with tempfile.TemporaryDirectory() as directory:
    database = Path(directory) / "claims.db"
    first = sqlite3.connect(database, isolation_level=None)
    second = sqlite3.connect(database, isolation_level=None)
    try:
        first.execute("CREATE TABLE job(id INTEGER PRIMARY KEY, token TEXT NOT NULL, expiry INTEGER NOT NULL)")
        first.execute("INSERT INTO job VALUES (41, 'claim-a', 10)")
        print("renewed:", renew(first, 41, "claim-a", 5, 15))
        print("stale token:", renew(second, 41, "claim-old", 6, 16))
        print("no extension:", renew(second, 41, "claim-a", 6, 14))
        print("at expiry:", renew(second, 41, "claim-a", 15, 20))
        print("stored expiry:", second.execute("SELECT expiry FROM job").fetchone()[0])
    finally:
        second.close()
        first.close()''','renewed: True\nstale token: False\nno extension: False\nat expiry: False\nstored expiry: 15',
'The primary-key predicate targets one row, with database page and transaction costs rather than an in-memory constant-time guarantee. BEGIN IMMEDIATE may block or fail under writer contention; this project does not implement bounded retry. Two sequential connections establish visibility and token checks, not a multi-worker load result or power-loss guarantee.',
['An expiry equal to now is already expired under this contract.','Never extend a lease using only its job ID without checking the current token.'],['python/leased-outbox-project','python/idempotent-jobs','python/sqlite-writer-contention'],subject='python-projects')

lesson('artifact-digest-check','Python artifact hashes: verify owned bytes against a separately trusted expectation',
'A cryptographic digest identifies the exact bytes of an artifact relative to an expected digest selected through a separate trust path.',
'The verifier accepts at most 4096 received bytes and a 64-character lowercase hexadecimal SHA-256 expectation. It hashes the bytes and compares the result with the expectation. The owned receipt artifact passes; changing one byte fails. A malformed expectation is rejected as a schema error rather than being treated as a mismatched release. The example does not download, unpack or install anything.',
'A digest stored beside an untrusted artifact does not establish the publisher’s identity, because an attacker can replace both. A release pipeline needs an authenticated expectation, dependency selection and archive/install boundaries too. [[python/wheel-metadata|Declared metadata]], [[python/wheel-installation|Installation origin]] and [[python/hmac-envelope|Authenticated bytes]] describe distinct checks. SHA-256 collision resistance is not a guarantee that the contents are safe to execute.',
r'''import hashlib
import hmac

def artifact_matches(payload, expected):
    if type(payload) is not bytes or len(payload) > 4096:
        raise ValueError("artifact byte cap")
    if type(expected) is not str or len(expected) != 64 or any(char not in "0123456789abcdef" for char in expected):
        raise ValueError("digest format")
    actual = hashlib.sha256(payload).hexdigest()
    return hmac.compare_digest(actual, expected)

owned_artifact = b"receipt-schema:v1\namount:integer\n"
trusted_expectation = hashlib.sha256(owned_artifact).hexdigest()
print("owned bytes:", artifact_matches(owned_artifact, trusted_expectation))
print("altered bytes:", artifact_matches(owned_artifact + b"x", trusted_expectation))
try:
    artifact_matches(owned_artifact, "not-a-digest")
except ValueError:
    print("digest schema rejected")''','owned bytes: True\naltered bytes: False\ndigest schema rejected',
'Hashing n bytes takes O(n) byte work, with bounded hash state. This program already receives the full bytes in memory, so its reception allocation is O(n); a large-artifact implementation should hash bounded chunks while enforcing a total-byte cap. Verification here does not examine archive members or dependency graphs.',
['The expected digest needs a trust source separate from received bytes.','Matching a digest does not mean an artifact is safe to import or install.'],['python/wheel-metadata','python/wheel-installation','python/hmac-envelope'],subject='python-packaging')

lesson('flask-conditional-response','Python Flask ETag responses: preserve cache validators across conditional reads',
'An ETag is a response validator that lets a client ask whether a selected representation has changed.',
'The owned Flask endpoint returns a fixed receipt summary, marks it private with a short cache lifetime, sets an ETag for those exact representation bytes and applies the request’s conditional headers. A normal local test-client GET returns the payload and validator. A second GET sends the same If-None-Match and receives 304 with no body. A mismatched validator receives 200 and the representation. All three requests remain inside the local test client.',
'A validator is not permission to read a resource. A real endpoint must perform authentication and tenant/resource checks before deciding which representation is selected, even when it might return 304. This fixture has no identity service or persistent record changes. A production validator must change when the represented bytes change and must account for representation variants. [[python/drf-list-visibility|Read scope]], [[python/flask-error-boundaries|Response errors]] and [[python/flask-json-api|Input schemas]] remain necessary.',
r'''from flask import Flask, Response, request

application = Flask(__name__)

@application.get("/receipts/41")
def receipt_summary():
    response = Response(b"receipt=41;amount=125\n", mimetype="text/plain")
    response.cache_control.private = True
    response.cache_control.max_age = 30
    response.add_etag()
    return response.make_conditional(request)

with application.test_client() as client:
    initial = client.get("/receipts/41")
    validator = initial.headers["ETag"]
    unchanged = client.get("/receipts/41", headers={"If-None-Match": validator})
    changed = client.get("/receipts/41", headers={"If-None-Match": '"different"'})
    print("statuses:", initial.status_code, unchanged.status_code, changed.status_code)
    print("304 body:", unchanged.data)
    print("validator retained:", unchanged.headers["ETag"] == validator)
    print("cache policy:", initial.headers["Cache-Control"])''',"statuses: 200 304 200\n304 body: b''\nvalidator retained: True\ncache policy: private, max-age=30",
'Computing the validator reads the representation bytes. Avoid reconstructing an expensive report merely to discover it is unchanged when a correctly maintained version can identify the same representation. This tiny response does not measure proxy behavior, compression variants, bandwidth savings or production cache hit rate.',
['Run access checks before returning an unchanged-resource status.','Do not reuse a validator when the selected representation bytes change.'],['python/flask-json-api','python/drf-list-visibility','python/flask-error-boundaries'],subject='python-web',dependencies=['Flask==3.1.3'])

lesson('matching-exercise','Python assignment exercise: verify pair feasibility separately from optimality',
'A matching verifier checks whether supplied worker-slot pairs form a valid assignment; optimality requires a separate maximum-cardinality comparison.',
'The exercise accepts a small owned eligibility graph and a proposed list of worker-slot tuples. Each worker and slot may occur once, and every pair must be an allowed edge. The accepted two-pair proposal uses both available slots. A duplicated slot and an ineligible edge are rejected. An empty proposal is feasible even though a larger assignment exists. That final distinction prevents a test from mistaking a valid result for an optimal result.',
'The function validates the graph itself before looking at the proposal, including exact integer slot IDs and duplicate eligibility edges. It does not repair invalid pairs or trust a solver simply because that solver returned a list. [[python/bipartite-matching|Augmenting assignment]] supplies the optimization algorithm. The independent test enumerates small alternatives to compare its pair count, while this checker focuses on feasibility.',
r'''def valid_assignment(allowed, slot_count, pairs):
    if type(allowed) is not list or len(allowed) > 8 or type(slot_count) is not int or not 0 <= slot_count <= 8 or type(pairs) is not list or len(pairs) > 8:
        raise ValueError("assignment bounds")
    for row in allowed:
        if type(row) is not list or any(type(slot) is not int or not 0 <= slot < slot_count for slot in row) or len(set(row)) != len(row):
            raise ValueError("eligibility fields")
    workers, slots = set(), set()
    for pair in pairs:
        if type(pair) is not tuple or len(pair) != 2:
            return False
        worker, slot = pair
        if type(worker) is not int or type(slot) is not int or not 0 <= worker < len(allowed) or slot not in allowed[worker] or worker in workers or slot in slots:
            return False
        workers.add(worker)
        slots.add(slot)
    return True

allowed = [[0, 1], [0]]
for proposal in ([(0, 1), (1, 0)], [(0, 0), (1, 0)], [(1, 1)], []):
    print("feasible:", valid_assignment(allowed, 2, proposal))''','feasible: True\nfeasible: False\nfeasible: False\nfeasible: True',
'Graph validation scans E eligibility entries and verifying P pairs scans the corresponding small rows, with O(P) used-vertex storage. The eight-by-eight cap bounds this work. Removing the cap should use indexed eligibility sets and separately account for their construction; optimality checking by enumeration grows exponentially.',
['A feasible empty result can still miss every possible assignment.','Check uniqueness and eligibility, not only the number of returned pairs.'],['python/bipartite-matching','python/collection-exercise','python/refactor-contract-tests'],subject='python-exercises')

for subject, title, slugs in [
 ('python-types','Exact ratios, aliases and local-clock ambiguity',['enum-alias-contract','fraction-ratios','zone-local-classification']),
 ('python-advanced','Transferred cleanup and type protocols',['exitstack-transfer','exception-group-partition','singledispatch-contract','ordering-protocol']),
 ('python-examples','Partial input and nested rollback',['sqlite-savepoints','spooled-file-budgets','socket-frame-reading']),
 ('python-dsa','Mutable compressed edges and optimal selection',['radix-trie-updates','bipartite-matching','weighted-intervals']),
 ('python-data','Paired estimates and declared axes',['covariance-policy','numpy-shape-contract']),
 ('python-projects','Renewing a stored claim',['lease-renewal-project']),
 ('python-packaging','Artifact bytes and expectations',['artifact-digest-check']),
 ('python-web','Target policies and conditional representations',['url-target-policy','flask-conditional-response']),
 ('python-exercises','Feasibility before optimality',['matching-exercise'])]:
 group(subject,title,slugs)

LIFETIME_QUESTIONS=[
 ('What does ExitStack.pop_all do?', ['Run all cleanup immediately','Discard all callbacks','Transfer cleanup to another stack','Make resources immortal'],2,'The returned stack owns the callbacks and still needs to be closed.'),
 ('After splitting ValueError leaves from a group, what must be considered?', ['Only the matching leaves','The residual subgroup too','No remaining failure','Only the group message'],1,'Handling the match does not handle the other nested leaves.'),
 ('Why is an Enum alias absent from ordinary iteration?', ['It has no declared name','Iteration returns canonical members once','It is inaccessible','Its value has changed'],1,'__members__ still contains the alias name, which points to the canonical member.'),
 ('What does Fraction(0.1) preserve?', ['An exact one tenth automatically','The original text spelling','The received float value','A payment rounding policy'],2,'The binary float value differs from Fraction("0.1"), which parses the decimal text.'),
 ('What does zero round-tripping UTC candidates mean here?', ['A unique local instant','A missing local reading','A selected later fold','A parser crash'],1,'Neither fold reproduces the local reading; the application must reject or declare an adjustment.'),
 ('Why does numeric singledispatch need a Boolean policy?', ['bool is an int subclass','bool is a float subclass','Dispatch ignores types','Annotations reject bool automatically'],0,'A Boolean can select the integer route unless the contract handles or rejects it.'),
 ('What follows unsupported rich ordering when both operands decline it?', ['Always false','A made-up alphabetical order','TypeError','Automatic conversion'],2,'NotImplemented declines a pair; it does not supply an ordering value.'),
 ('Does releasing an inner savepoint commit its writes independently?', ['Always','No, an outer rollback can still remove them','Only when it has a name','Only for primary keys'],1,'The outer transaction still controls commitment.'),
 ('What does a spool threshold constrain?', ['Maximum accepted upload size','The storage rollover choice','Total process memory','Maximum number of temporary files'],1,'An application needs a separate byte rejection cap.'),
 ('Why can greedy first-free assignment miss a larger matching?', ['Slots are always weighted','An existing worker may need reassignment','All graphs are disconnected','A list cannot store pairs'],1,'An augmenting path can move a flexible worker to free a restricted worker’s only slot.'),
 ('What must an artifact digest expectation have?', ['The same untrusted delivery path only','A separate trust policy','A filename ending in zip','A large enough payload'],1,'An attacker can replace both bytes and a digest delivered without authentication.'),
 ('Does 304 remove the need for access checks?', ['Yes, it has no body','Only for private caches','No, selecting a representation still requires permission','Only with an ETag'],2,'A conditional read still identifies a resource and representation; the validator is not authorization.')]
slug='python-lifetime-updates'; title='Python resource lifetime and update contract quiz'
refs=['python/exitstack-transfer','python/exception-group-partition','python/zone-local-classification','python/radix-trie-updates','python/bipartite-matching','python/lease-renewal-project','python/artifact-digest-check','python/flask-conditional-response']
BANKS[slug]=(title,LIFETIME_QUESTIONS)
entry=copy.deepcopy(lookup['quizzes/python-basics']); path='quizzes/'+slug
entry.update(id=str(uuid.uuid5(uuid.NAMESPACE_URL,'https://aitrove.in/'+path)),path=path,title=title,summary='Twelve explained questions on Python cleanup, protocols and stored-state updates.',sort_order=600+len(added),published_at=stamp,updated_at=stamp)
entry['body']=para('A Python self-check tests resource ownership and update contracts through twelve explained questions.')+'<h2>Review the related lessons</h2><ul>'+''.join('<li><a href="/'+p+'">'+html.escape(lookup[p]['title'])+'</a></li>' for p in refs)+'</ul><h3>Common Mistakes</h3>'+para('A valid small fixture does not establish production safety or exhaustive language coverage. Read the rejected-input and state-preservation boundaries. Quiz results remain in this browser.')
entry['data']['questions']=[dict(prompt=q,options=o,answer=a,explanation=e) for q,o,a,e in LIFETIME_QUESTIONS]
entry['data']['related']=[dict(path=p,title=lookup[p]['title']) for p in refs]
upsert(entry);added.append(path)

LIFETIME_REVERSE={
 'python/exit-stack':['exitstack-transfer'], 'python/context-managers':['exitstack-transfer'],
 'python/exception-groups':['exception-group-partition'],'python/enums':['enum-alias-contract'],
 'python/decimal-money':['fraction-ratios'],'python/timezone-fold':['zone-local-classification'],
 'python/datetime-boundaries':['zone-local-classification'],'python/first-class-functions':['singledispatch-contract'],
 'python/hash-equality':['ordering-protocol'],'python/sqlite-transactions':['sqlite-savepoints'],
 'python/django-atomic':['sqlite-savepoints'],'python/flask-multipart-budgets':['spooled-file-budgets'],
 'python/binary-records':['socket-frame-reading'],'python/regex-validation':['url-target-policy'],
 'python/compressed-trie':['radix-trie-updates'],'python/trie-deletion':['radix-trie-updates'],
 'python/graph-bfs':['bipartite-matching'],'python/bisect-insertion':['weighted-intervals'],
 'python/knapsack':['weighted-intervals'],'python/quantile-policy':['covariance-policy'],
 'python/numpy-broadcasting':['numpy-shape-contract'],'python/leased-outbox-project':['lease-renewal-project'],
 'python/idempotent-jobs':['lease-renewal-project'],'python/wheel-metadata':['artifact-digest-check'],
 'python/hmac-envelope':['artifact-digest-check'],'python/flask-json-api':['flask-conditional-response'],
 'python/drf-list-visibility':['flask-conditional-response'],'python/collection-exercise':['matching-exercise']}
for original, slugs in LIFETIME_REVERSE.items():
 targets=['python/'+slug for slug in slugs]; assert original in lookup and all(p in lookup for p in targets)
 entry=lookup[original]; marker='<h2>Follow the ownership and update boundary</h2>'
 entry['body']=entry['body'].split(marker)[0]+marker+para(', '.join('[['+p+'|'+lookup[p]['title']+']]' for p in targets)+'.')
 known={item['path'] for item in entry['data'].get('related',[])}
 entry['data'].setdefault('related',[]).extend({'path':p,'title':lookup[p]['title']} for p in targets if p not in known)
 entry['updated_at']=stamp
