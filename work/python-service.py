"""Sixth Python pass: bounded protocols, state transitions and application checks."""
lesson('assert-validation','Python assert versus input validation: optimized execution changes the contract',
'An assert statement checks an internal assumption when assertions are enabled; it is not a stable input-validation boundary.',
'The owned child program runs twice through the same executable, once normally and once with -O. Its assertion rejects a negative amount in the first run and disappears in the second. The application validator uses an explicit conditional and raises ValueError in both modes. Nothing received is executed: the child source is a fixed teaching string. Keep the assertion for a developer invariant only after establishing the input contract.',
'An assertion expression can have side effects that disappear under optimization. That includes logging, mutation and calls needed for correctness. Neither annotations nor assertions replace the accepted-value checks in [[python/type-conversion|Conversion]] and [[python/typing-reference|Typing]]. Tests can use assertions; public application rejection must not depend on interpreter optimization flags.',
r'''import subprocess
import sys

owned_source = """
def assertion_only(amount):
    assert amount >= 0
    return amount
def validated(amount):
    if type(amount) is not int or amount < 0:
        raise ValueError("nonnegative exact integer required")
    return amount
for operation in (assertion_only, validated):
    try:
        print(operation(-25))
    except (AssertionError, ValueError) as failure:
        print(type(failure).__name__)
"""
for optimized in (False, True):
    command = [sys.executable, "-I"] + (["-O"] if optimized else [])
    output = subprocess.run(command + ["-c", owned_source], capture_output=True,
                            text=True, check=True, timeout=5).stdout.splitlines()
    print("optimized:", optimized, output)''',"optimized: False ['AssertionError', 'ValueError']\noptimized: True ['-25', 'ValueError']",
'The scalar validator has bounded work for this input. Child startup is a process cost, not a benchmark of assertion performance. A conditional check still needs the right domain rule; checking only a sign would accept Boolean values and unrelated numeric types.',
['Do not put required work inside an assertion expression.','Do not use -O-dependent checks to enforce a public input schema.'],['python/exceptions','python/type-conversion','python/runtime-compatibility'])

lesson('signature-boundaries','Python positional-only and keyword-only parameters: keep call roles explicit',
'A positional-only parameter must be supplied by position, while a keyword-only parameter must be supplied by its declared name.',
'The charge operation receives its amount before the slash and its fee after the star. Its signature prevents a keyword from binding the amount and prevents a second positional argument from accidentally becoming the fee. Type and range checks remain inside the body. The counter confirms that rejected binding never enters the function, which matters when its body would perform a write.',
'A slash does not make a value immutable, and a star does not validate its type. A wrapper using arbitrary args and kwargs can hide the intended signature unless it preserves and enforces the contract. [[python/function-arguments|Argument rules]], [[python/argument-unpacking|Keyword collisions]] and [[python/decorators|Wrappers]] are related but separate mechanisms.',
r'''calls = 0
def charge(amount, /, *, fee=25):
    global calls
    if type(amount) is not int or amount < 0 or type(fee) is not int or fee < 0:
        raise ValueError("nonnegative exact integers required")
    calls += 1
    return amount + fee

print("charged:", charge(125, fee=50))
for arguments, keywords in (((), {"amount": 125}), ((125, 50), {})):
    try:
        charge(*arguments, **keywords)
    except TypeError:
        print("binding rejected")
print("body calls:", calls)''','charged: 175\nbinding rejected\nbinding rejected\nbody calls: 1',
'Binding this fixed signature has bounded work. Integer addition depends on digit length; a real amount field also needs an upper bound. Signature rejection happens before body-side changes, but a later failure inside the body still needs transaction handling.',
['Signature shape and value validation solve different problems.','Do not catch every TypeError as a binding failure when the function body can raise it too.'],['python/function-arguments','python/argument-unpacking','python/refactor-contract-tests'])

lesson('chainmap-configuration','Python ChainMap: live configuration layers versus an owned snapshot',
'ChainMap reads several mappings in priority order while ordinary writes and deletions target its first mapping.',
'The request layer sits ahead of deployment settings and defaults. Reading timeout finds the first binding. Writing timeout changes only request overrides, so shared defaults remain unchanged. Editing deployment settings later affects the live ChainMap. Converting it to a dictionary captures the current visible values, but only shallowly: nested mutable values would still be shared.',
'Deleting a key that exists only in a later layer raises KeyError; it does not delete a inherited setting. The fixture uses scalar values and therefore has no nested alias to manage. A configuration value also needs [[python/toml-configuration|Schema validation]], [[python/configuration-precedence|Explicit precedence]] and a policy for whether requests may alter it.',
r'''from collections import ChainMap

defaults = {"timeout": 30, "region": "local"}
deployment = {"timeout": 10}
request = {}
settings = ChainMap(request, deployment, defaults)
print("initial:", settings["timeout"])
settings["timeout"] = 5
snapshot = dict(settings)
deployment["region"] = "west"
print("request:", request)
print("default timeout:", defaults["timeout"])
print("live region:", settings["region"])
print("snapshot region:", snapshot["region"])
try:
    del settings["region"]
except KeyError:
    print("later-layer deletion rejected")''',"initial: 10\nrequest: {'timeout': 5}\ndefault timeout: 30\nlive region: west\nsnapshot region: local\nlater-layer deletion rejected",
'A missing lookup may inspect all k layers. Materializing visible bindings costs time and storage proportional to their distinct keys, with lookup work across layers. This is not an atomic snapshot under concurrent edits; protect the source mappings or create the snapshot during a controlled configuration phase.',
['Live layered reads can change after a caller retains the ChainMap.','A shallow snapshot does not own nested records.'],['python/configuration-precedence','python/copy-deepcopy','python/dictionaries'],subject='python-types')

lesson('binary-records','Python struct: a fixed-endian receipt record with exact byte length',
'Struct packs and unpacks values according to a declared binary layout, including byte order and field widths.',
'The receipt wire format is exactly nine bytes: a one-byte version, a four-byte identifier and a four-byte amount, all in network byte order. The encoder rejects Boolean values and unsigned overflow before packing. The decoder rejects truncation and trailing bytes before unpacking, then rejects an unsupported version. A file containing several records would need framing and a count or total-byte bound rather than this single-record function.',
'Native alignment depends on the host ABI. The explicit ! prefix avoids silently changing the protocol across machines. The record has no signature or checksum; successfully unpacking bytes does not establish their origin. [[python/memoryview-buffers|Shared views]], [[python/typed-arrays|Typed storage]] and [[python/hmac-envelope|Message authentication]] cover different ownership and trust boundaries.',
r'''import struct

RECEIPT = struct.Struct("!BII")
def encode_receipt(receipt_id, amount):
    if any(type(value) is not int or not 0 <= value <= 0xFFFFFFFF
           for value in (receipt_id, amount)):
        raise ValueError("unsigned exact integers required")
    return RECEIPT.pack(1, receipt_id, amount)

def decode_receipt(payload):
    if type(payload) is not bytes or len(payload) != RECEIPT.size:
        raise ValueError("exact record bytes required")
    version, receipt_id, amount = RECEIPT.unpack(payload)
    if version != 1:
        raise ValueError("unsupported version")
    return receipt_id, amount

payload = encode_receipt(41, 125)
print("bytes:", payload.hex())
print("record:", decode_receipt(payload))
for invalid in (payload[:-1], payload + b"x", bytes([2]) + payload[1:]):
    try:
        decode_receipt(invalid)
    except ValueError:
        print("record rejected")''',"bytes: 01000000290000007d\nrecord: (41, 125)\nrecord rejected\nrecord rejected\nrecord rejected",
'The format has fixed time and space costs because the field count and widths are fixed. A bytes argument can already be large before this function receives it; bound reception at the transport too. Rejecting an invalid version does not reverse bytes consumed by an earlier reader.',
['Never use implicit native alignment for a portable wire contract.','Do not accept a valid prefix while ignoring unexplained trailing bytes.'],['python/strings-bytes','python/base64-records','python/hmac-envelope'],subject='python-types')

lesson('generator-control','Python generator send and close: suspension retains state until cleanup',
'A generator preserves a suspended frame between yields, and send supplies the value received by its current yield expression.',
'The running-total generator emits its current total before accepting another amount. next primes the first suspension point; send then validates and incorporates the received amount before yielding again. An invalid amount exits the generator through ValueError and executes its finally block. A second generator is closed explicitly after priming. Neither path publishes the partially accepted state to an external ledger.',
'A non-None value cannot be sent into a generator that has not reached its first yield. close requests termination at the suspension point; cleanup must not try to yield another value in response. [[python/generators|Iteration]], [[python/context-managers|Cleanup ownership]] and [[python/async-generator-cleanup|Async producer closure]] use related lifetime rules, but they are not interchangeable APIs.',
r'''closed = []
def running_total():
    total = 0
    try:
        while True:
            amount = yield total
            if type(amount) is not int or not 0 <= amount <= 1000:
                raise ValueError("bounded exact amount required")
            total += amount
    finally:
        closed.append("released")

producer = running_total()
print("initial:", next(producer))
print("accepted:", producer.send(125))
try:
    producer.send(True)
except ValueError:
    print("invalid send rejected")
print("closed:", closed)
second = running_total()
next(second)
second.close()
print("explicit closes:", len(closed))''',"initial: 0\naccepted: 125\ninvalid send rejected\nclosed: ['released']\nexplicit closes: 2",
'A suspended frame retains its locals and reachable objects. This generator has constant-sized application state, except for growing integer digit length and the demonstration cleanup list. A producer owning a file or cursor needs explicit caller cleanup when iteration ends early.',
['Prime a generator before sending a non-None value.','Do not assume an early loop break closes a retained generator.'],['python/generators','python/iterator-protocol','python/async-generator-cleanup'],subject='python-advanced')

lesson('async-shield-ownership','Python asyncio shield: caller cancellation does not transfer task ownership',
'Asyncio shield lets an inner task continue when cancellation interrupts the caller awaiting that shield.',
'The caller creates and retains the persistence task, waits until its owned fixture starts, and then the controller cancels the caller. The caller still receives CancelledError. The inner task waits on a separate event and remains pending until the controller permits completion. The controller finally awaits it, so completion and cleanup have an explicit owner. Events establish ordering without timing-sensitive sleeps.',
'Shield is not a general cancellation ban. The inner task can still fail or be cancelled directly, and continuing work may finish after a request has gone away. Decide who may publish its result. [[python/async-deadlines|Deadlines]], [[python/async-task-groups|Task groups]] and [[python/outbox-project|Durable intent]] concern separate scopes; shield alone does not make a side effect durable.',
r'''import asyncio

async def trace():
    started, release = asyncio.Event(), asyncio.Event()
    retained = []
    async def persist():
        started.set()
        await release.wait()
        return "stored"
    async def caller():
        task = asyncio.create_task(persist())
        retained.append(task)
        try:
            await asyncio.shield(task)
        except asyncio.CancelledError:
            print("caller cancelled")
            raise
    request = asyncio.create_task(caller())
    await started.wait()
    request.cancel()
    try:
        await request
    except asyncio.CancelledError:
        pass
    print("inner pending:", not retained[0].done())
    release.set()
    print("inner result:", await retained[0])

asyncio.run(trace())''','caller cancelled\ninner pending: True\ninner result: stored',
'Each retained task owns its suspended coroutine state. Unbounded background task creation can retain memory and work after clients disconnect. This fixture owns exactly one inner task and awaits its terminal result; a service needs capacity, shutdown and failure-reporting policies.',
['The cancelled caller still receives CancelledError.','Retain and await work that continues after its original caller exits.'],['python/async-deadlines','python/async-task-groups','python/cancellation-interview'],subject='python-advanced')

lesson('condition-predicates','Python Condition: wait for protected state, not for a notification count',
'A Condition combines a lock with waiting and notification so threads can coordinate changes to a shared predicate.',
'The consumer waits until the one-element receipt slot becomes nonempty, then removes its value while holding the same condition lock. The producer writes the slot and notifies while holding that lock. wait_for rechecks the predicate after reacquiring the lock. A notification without the required state cannot make the consumer proceed; notification is a prompt to recheck, not a durable message.',
'The timeout bounds this teaching wait and raises if no receipt arrives. It is not a whole-service deadline or a process shutdown policy. The slot has one producer and one consumer; a queue with many writers needs explicit capacity and closed-state rules. [[python/thread-locks|Lock scope]], [[python/async-queues|Async queues]] and [[python/expiry-exercise|State predicates]] keep those contracts distinct.',
r'''from threading import Condition, Thread

condition = Condition()
slot, received = [], []
def consume():
    with condition:
        if not condition.wait_for(lambda: bool(slot), timeout=2):
            raise TimeoutError("receipt did not arrive")
        received.append(slot.pop())

consumer = Thread(target=consume)
consumer.start()
with condition:
    slot.append(125)
    condition.notify()
consumer.join(timeout=3)
if consumer.is_alive():
    raise RuntimeError("consumer did not finish")
print("received:", received)
print("empty slot:", slot == [])''',"received: [125]\nempty slot: True",
'This one-slot transition has bounded application storage. Scheduling and lock acquisition latency are not constant-time guarantees. wait_for releases the lock while blocked and reacquires it before returning; application work inside the lock can delay both producers and other consumers.',
['Guard reads, writes and predicate checks with the same lock.','Notify does not release the lock immediately or store a future message.'],['python/thread-locks','python/thread-pools','python/async-queues'],subject='python-advanced')

group('python','Stable rejection and explicit calls',['assert-validation','signature-boundaries'])
group('python-types','Layered settings and wire bytes',['chainmap-configuration','binary-records'])
group('python-advanced','Suspension, cancellation and shared predicates',['generator-control','async-shield-ownership','condition-predicates'])

lesson('articulation-points','Python articulation points: find vertices that separate an undirected graph',
'An articulation point is a vertex whose removal increases the connected-component count of an undirected graph.',
'The traversal records discovery order and the earliest reachable ancestor for each subtree. A non-root vertex separates a child subtree when that child cannot reach an earlier ancestor. A DFS root follows a different rule: it separates components only when it has more than one traversal child. Each edge has its own ID so skipping the incoming edge does not discard a second parallel edge. Self-loops do not create an extra DFS child.',
'The graph is an owned undirected edge list with 0 to 32 numbered vertices and at most 128 edges. It accepts parallel edges and self-loops, rejects Boolean endpoints and validates before building adjacency. Do not apply the undirected parent-edge rule to directed reachability. Compare [[python/graph-bridges|Edge removal]], [[python/strongly-connected-components|Directed components]] and [[python/union-find|Connectivity]].',
r'''def articulation_points(vertex_count, edges):
    if type(vertex_count) is not int or not 0 <= vertex_count <= 32 or type(edges) is not list or len(edges) > 128:
        raise ValueError("bounded graph required")
    adjacency = [[] for _ in range(vertex_count)]
    for edge_id, pair in enumerate(edges):
        if type(pair) is not tuple or len(pair) != 2 or any(type(vertex) is not int or not 0 <= vertex < vertex_count for vertex in pair):
            raise ValueError("valid endpoints required")
        left, right = pair
        adjacency[left].append((right, edge_id))
        adjacency[right].append((left, edge_id))
    discovered, low = [-1] * vertex_count, [0] * vertex_count
    clock, separating = 0, set()
    def visit(vertex, incoming):
        nonlocal clock
        discovered[vertex] = low[vertex] = clock
        clock += 1
        children = 0
        for neighbor, edge_id in adjacency[vertex]:
            if edge_id == incoming:
                continue
            if discovered[neighbor] == -1:
                children += 1
                visit(neighbor, edge_id)
                low[vertex] = min(low[vertex], low[neighbor])
                if incoming is not None and low[neighbor] >= discovered[vertex]:
                    separating.add(vertex)
            else:
                low[vertex] = min(low[vertex], discovered[neighbor])
        if incoming is None and children > 1:
            separating.add(vertex)
    for vertex in range(vertex_count):
        if discovered[vertex] == -1:
            visit(vertex, None)
    return sorted(separating)

print("separating:", articulation_points(5, [(0, 1), (1, 2), (2, 0), (1, 3), (3, 4), (1, 3)]))
print("cycle:", articulation_points(3, [(0, 1), (1, 2), (2, 0)]))''','separating: [1, 3]\ncycle: []',
'Traversal and adjacency storage take O(V + E), followed by O(A log A) sorting for A returned vertices. The recursion depth is bounded by the accepted 32 vertices. Larger graphs should use an explicit traversal stack or a separately tested depth policy.',
['The DFS root needs the child-count rule.','Skip an incoming edge ID, not every edge to the parent vertex.'],['python/graph-bridges','python/strongly-connected-components','python/recursion-boundaries'],subject='python-dsa')

lesson('component-condensation','Python graph condensation: collapse directed cycles into an acyclic component graph',
'A condensation graph replaces each strongly connected component with one vertex and keeps edges between different components.',
'The first traversal records finish order; the reversed graph then partitions vertices in reverse finish order. Each component is sorted, and components are ordered by their smallest vertex to make the owned fixture output reproducible. Original edges map into component IDs, with internal edges removed and repeated component edges deduplicated. This changes the graph model: a path between components does not say which original edge or vertex carried a business operation.',
'The fixture accepts an owned directed list with at most 32 vertices and 128 edges. Input is validated before traversal. Cyclic components have become individual nodes, so the returned graph has no directed cycle. [[python/strongly-connected-components|Component membership]], [[python/topological-sort|Dependency ordering]] and [[python/graph-bfs|Reachability]] answer different questions.',
r'''def condensation(vertex_count, edges):
    if type(vertex_count) is not int or not 0 <= vertex_count <= 32 or type(edges) is not list or len(edges) > 128:
        raise ValueError("bounded graph required")
    graph, reverse = [[] for _ in range(vertex_count)], [[] for _ in range(vertex_count)]
    for pair in edges:
        if type(pair) is not tuple or len(pair) != 2 or any(type(vertex) is not int or not 0 <= vertex < vertex_count for vertex in pair):
            raise ValueError("valid endpoints required")
        source, target = pair
        graph[source].append(target)
        reverse[target].append(source)
    seen, finished = set(), []
    def finish(vertex):
        seen.add(vertex)
        for target in graph[vertex]:
            if target not in seen:
                finish(target)
        finished.append(vertex)
    for vertex in range(vertex_count):
        if vertex not in seen:
            finish(vertex)
    seen.clear()
    components = []
    def collect(vertex, members):
        seen.add(vertex)
        members.append(vertex)
        for target in reverse[vertex]:
            if target not in seen:
                collect(target, members)
    for vertex in reversed(finished):
        if vertex not in seen:
            members = []
            collect(vertex, members)
            components.append(sorted(members))
    components.sort(key=lambda members: members[0])
    owner = {vertex: index for index, members in enumerate(components) for vertex in members}
    collapsed = sorted({(owner[source], owner[target]) for source, target in edges if owner[source] != owner[target]})
    return components, collapsed

print(condensation(5, [(0, 1), (1, 0), (1, 2), (2, 3), (3, 2), (3, 4)]))''',"([[0, 1], [2, 3], [4]], [(0, 1), (1, 2)])",
'Both traversals use O(V + E) work and storage. Sorting members/components/unique edges adds up to O(V log V + E log E). Original edge identity is deliberately lost in this returned summary; retain it separately when multiplicity or provenance matters.',
['Discard internal component edges when constructing the DAG.','Do not present a collapsed edge as an original edge identity.'],['python/strongly-connected-components','python/topological-sort','python/articulation-points'],subject='python-dsa')

lesson('directed-euler-trail','Python directed Euler trail: consume every edge identity exactly once',
'An Euler trail traverses every edge of a graph exactly once, while vertices may appear repeatedly.',
'The owned directed multigraph tracks each edge by its input position. Degree differences select a start for an open trail or reject an impossible degree pattern. A stack consumes outgoing edges and records edges when backtracking; reversing that list produces the trail. The final consumed-edge count rejects disconnected edge-bearing regions even when every local degree difference is balanced. Empty input returns no edges rather than inventing a starting vertex.',
'Parallel edges and self-loops remain distinct through their IDs. A Hamiltonian path visits vertices instead and is a different problem. The fixture accepts at most 32 vertices and 128 edges and chooses a deterministic outgoing order. [[python/graph-bfs|Connectivity]], [[python/topological-sort|Ordering]] and [[python/graph-bridges|Edge identity]] supply the related contracts.',
r'''def euler_trail(vertex_count, edges):
    if type(vertex_count) is not int or not 0 <= vertex_count <= 32 or type(edges) is not list or len(edges) > 128:
        raise ValueError("bounded graph required")
    outgoing, incoming = [[] for _ in range(vertex_count)], [0] * vertex_count
    for edge_id, pair in enumerate(edges):
        if type(pair) is not tuple or len(pair) != 2 or any(type(vertex) is not int or not 0 <= vertex < vertex_count for vertex in pair):
            raise ValueError("valid endpoints required")
        source, target = pair
        outgoing[source].append((target, edge_id))
        incoming[target] += 1
    if not edges:
        return []
    differences = [len(outgoing[vertex]) - incoming[vertex] for vertex in range(vertex_count)]
    starts = [vertex for vertex, degree in enumerate(differences) if degree == 1]
    ends = [vertex for vertex, degree in enumerate(differences) if degree == -1]
    if any(abs(degree) > 1 for degree in differences) or not (len(starts) == len(ends) == 0 or len(starts) == len(ends) == 1):
        raise ValueError("trail degree pattern required")
    start = starts[0] if starts else next(vertex for vertex in range(vertex_count) if outgoing[vertex])
    for neighbors in outgoing:
        neighbors.reverse()
    stack, reversed_edges = [(start, None)], []
    while stack:
        vertex, edge_id = stack[-1]
        if outgoing[vertex]:
            target, next_id = outgoing[vertex].pop()
            stack.append((target, next_id))
        else:
            stack.pop()
            if edge_id is not None:
                reversed_edges.append(edge_id)
    if len(reversed_edges) != len(edges):
        raise ValueError("edge-bearing regions disconnected")
    return list(reversed(reversed_edges))

edges = [(0, 1), (1, 0), (0, 1), (1, 2)]
print("edge IDs:", euler_trail(3, edges))
try:
    euler_trail(4, [(0, 1), (1, 0), (2, 3), (3, 2)])
except ValueError:
    print("disconnected edges rejected")''','edge IDs: [0, 1, 2, 3]\ndisconnected edges rejected',
'Adjacency construction and stack traversal take O(V + E) time and storage; each accepted edge is consumed once. This function owns its adjacency lists and preserves the caller edge list. It returns an ordering, not an executed delivery route or cost-optimal route.',
['Balanced degree counts alone do not connect separate edge regions.','Preserve edge IDs when the graph permits parallel edges.'],['python/graph-bfs','python/graph-bridges','python/component-condensation'],subject='python-dsa')

lesson('z-string-search','Python Z string matching: reuse a known matching interval without losing overlaps',
'A Z value records how many symbols match the sequence prefix starting at a selected position.',
'The matcher combines the pattern, one unique object sentinel and the text into an owned symbol list. The sentinel cannot collide with an arbitrary character, unlike a guessed delimiter such as a dollar sign. A half-open matching interval lets positions inside a known match reuse a lower bound before extending it. Positions with a Z value at least the pattern length identify text matches, including overlapping matches.',
'The input contract accepts strings up to 128 code points for the text and 32 for the pattern. An empty pattern matches every boundary, including the final boundary. Indices count code points, not encoded bytes or grapheme clusters. [[python/kmp-search|Prefix-function matching]], [[python/strings-bytes|Text versus bytes]] and [[python/unicode-normalization|Normalization policy]] must use compatible index rules.',
r'''def z_matches(text, pattern):
    if type(text) is not str or type(pattern) is not str or len(text) > 128 or len(pattern) > 32:
        raise ValueError("bounded strings required")
    if not pattern:
        return list(range(len(text) + 1))
    symbols = list(pattern) + [object()] + list(text)
    matched = [0] * len(symbols)
    left = right = 0
    for position in range(1, len(symbols)):
        if position < right:
            matched[position] = min(right - position, matched[position - left])
        while position + matched[position] < len(symbols) and symbols[matched[position]] == symbols[position + matched[position]]:
            matched[position] += 1
        if position + matched[position] > right:
            left, right = position, position + matched[position]
    offset = len(pattern) + 1
    return [position - offset for position in range(offset, len(symbols)) if matched[position] >= len(pattern)]

print("overlaps:", z_matches("ababa", "aba"))
print("delimiter text:", z_matches("$a$a", "$a"))
print("empty:", z_matches("ab", ""))''','overlaps: [0, 2]\ndelimiter text: [0, 2]\nempty: [0, 1, 2]',
'For text length n and pattern length m, interval reuse bounds extension work to O(n + m), with O(n + m) owned storage and returned-match space. This eager matcher is not a streamed matcher for arbitrarily large input.',
['A guessed text delimiter may occur in the received text.','Specify what an empty pattern means instead of leaving it accidental.'],['python/kmp-search','python/longest-palindrome','python/strings-bytes'],subject='python-dsa')

lesson('lis-reconstruction','Python longest increasing subsequence: reconstruct a strict sequence from tail candidates',
'A longest increasing subsequence selects values in their original order with each selected value strictly greater than the previous one.',
'The algorithm maintains the smallest known ending value for each subsequence length. bisect_left finds where a value replaces a tail or extends the candidate lengths. Each chosen input position retains a predecessor pointing to the prior length candidate at that time. Walking those links from the final tail reconstructs a valid subsequence; the tail array itself is not the reconstructed input sequence. Equal values replace a candidate rather than extend a strict subsequence.',
'The fixture accepts at most 128 exact integers in a bounded range, rejects Booleans and returns one optimum, without promising the lexicographically first optimum. A nondecreasing policy would change the binary-search boundary. [[python/bisect-insertion|Bisect boundaries]], [[python/longest-common-subsequence|Two-sequence DP]] and [[python/edit-script|Reconstruction]] address related choices.',
r'''from bisect import bisect_left

def increasing_subsequence(amounts):
    if type(amounts) is not list or len(amounts) > 128 or any(type(amount) is not int or not -1000000 <= amount <= 1000000 for amount in amounts):
        raise ValueError("bounded exact integers required")
    tails, positions, previous = [], [], [-1] * len(amounts)
    for index, amount in enumerate(amounts):
        length_index = bisect_left(tails, amount)
        if length_index:
            previous[index] = positions[length_index - 1]
        if length_index == len(tails):
            tails.append(amount)
            positions.append(index)
        else:
            tails[length_index] = amount
            positions[length_index] = index
    result = []
    cursor = positions[-1] if positions else -1
    while cursor != -1:
        result.append(amounts[cursor])
        cursor = previous[cursor]
    return list(reversed(result))

print("selected:", increasing_subsequence([300, 100, 200, 200, 400, 250]))
print("duplicates:", increasing_subsequence([125, 125, 125]))
print("empty:", increasing_subsequence([]))''','selected: [100, 200, 250]\nduplicates: [125]\nempty: []',
'Binary search for each of n values gives O(n log n) time, while predecessor and candidate arrays need O(n) storage. Reconstructing the returned sequence is O(L) for optimum length L. Input magnitude is bounded here, so comparisons do not hide unbounded integer digit work.',
['Tail values need not form the returned subsequence by themselves.','Strict increase cannot extend a sequence using an equal value.'],['python/bisect-insertion','python/longest-common-subsequence','python/edit-script'],subject='python-dsa')

group('python-dsa','Graph removals, edge trails and sequence reconstruction',['articulation-points','component-condensation','directed-euler-trail','z-string-search','lis-reconstruction'])

lesson('base64-records','Python strict Base64: reject alternate spellings before decoding a record',
'Base64 represents bytes with printable symbols; it does not encrypt or authenticate those bytes.',
'The receipt decoder accepts an ASCII string no longer than 64 characters, uses validate=True, and then requires re-encoding the decoded bytes to reproduce the received spelling. The second check enforces this application’s canonical padded standard alphabet, including unused pad bits. It also limits the decoded payload to 32 bytes. A valid envelope must still satisfy the binary record schema before it becomes a receipt.',
'Whitespace, URL-safe alphabets and omitted padding are deliberately rejected by this protocol. Other protocols may accept them, but silently mixing conventions creates signature and identity disagreements. Compare [[python/binary-records|Binary fields]], [[python/hmac-envelope|Authentication]] and [[python/regex-validation|Exact field grammar]]. A size check here cannot reclaim a large string already buffered by a transport.',
r'''import base64
import binascii

def canonical_bytes(encoded):
    if type(encoded) is not str or not encoded.isascii() or len(encoded) > 64:
        raise ValueError("bounded ASCII encoding required")
    try:
        decoded = base64.b64decode(encoded, validate=True)
    except binascii.Error as failure:
        raise ValueError("invalid Base64") from failure
    if len(decoded) > 32 or base64.b64encode(decoded).decode("ascii") != encoded:
        raise ValueError("canonical bounded encoding required")
    return decoded

print("decoded:", canonical_bytes("fQ==").hex())
for received in ("fQ==\n", "fQ", "fR==", "__8="):
    try:
        canonical_bytes(received)
    except ValueError:
        print("spelling rejected")''','decoded: 7d\nspelling rejected\nspelling rejected\nspelling rejected\nspelling rejected',
'Decoding and canonical re-encoding take O(n) time and storage for n encoded characters, capped here. Empty Base64 decodes to empty bytes; whether an empty payload is valid belongs to the next record schema. Do not treat decoding success as schema acceptance or trust.',
['Base64 is reversible encoding, not secrecy.','Canonical spelling and decoded record validation are separate checks.'],['python/binary-records','python/hmac-envelope','python/strings-bytes'],subject='python-examples')

lesson('hmac-envelope','Python HMAC envelopes: authenticate exact bytes and separate replay policy',
'HMAC computes a keyed authentication tag over bytes so a verifier with the same secret can detect an altered message.',
'The owned fixture signs a bounded bytes payload with SHA-256 and verifies a 64-character lowercase hexadecimal tag. compare_digest compares fixed-sized raw tags. A changed payload fails verification, while the identical message/tag pair verifies again. That repeat is intentional: integrity does not make a message fresh or single-use. The fixed key is teaching material, never a deployable secret.',
'Sign the agreed wire representation. Parsing and rebuilding equivalent JSON can change spacing or key order and therefore change the tag. Verification must be followed by a [[python/json-validation|Payload schema]], a [[python/idempotent-jobs|Replay policy]] and an actual identity/key lifecycle. This fixture does not implement transport encryption, key rotation, expiry or recipient authorization.',
r'''import hashlib
import hmac
import re

FIXTURE_KEY = b"owned-test-key-not-a-production-secret"
def authenticated(payload, tag):
    if type(payload) is not bytes or len(payload) > 128 or type(tag) is not str or re.fullmatch(r"[0-9a-f]{64}", tag) is None:
        return False
    expected = hmac.new(FIXTURE_KEY, payload, hashlib.sha256).digest()
    return hmac.compare_digest(expected, bytes.fromhex(tag))

payload = b'{"receipt_id":"R-0041","amount":125}'
tag = hmac.new(FIXTURE_KEY, payload, hashlib.sha256).hexdigest()
print("original:", authenticated(payload, tag))
print("changed:", authenticated(payload.replace(b"125", b"250"), tag))
print("replay:", authenticated(payload, tag))
print("malformed:", authenticated(payload, "not-a-tag"))''','original: True\nchanged: False\nreplay: True\nmalformed: False',
'Tag calculation processes O(n) payload bytes with fixed algorithm state. compare_digest concerns tag comparison, not a claim that every branch of the complete verifier has identical timing. Reception, secret storage and replay tracking have separate resource and security costs.',
['An authenticated duplicate can still be a replay.','Do not ship a fixture key or log a production key.'],['python/json-validation','python/base64-records','python/idempotent-jobs'],subject='python-examples')

lesson('gzip-output-budget','Python bounded gzip decoding: cap expanded output before publishing it',
'Gzip decoding expands a compressed byte stream and verifies its format and checksum while reading to its end.',
'The decoder accepts at most 512 compressed bytes and reads at most 129 expanded bytes for a 128-byte application limit. An oversized expansion is rejected before it is returned. A small accepted expansion reaches end-of-stream so a damaged trailer is not silently ignored. The fixture accepts concatenated gzip members as one bounded output because GzipFile supports that interpretation; a single-member protocol needs an additional framing rule.',
'The output cap limits what this function returns, not a hard bound on decompressor internals, CPU time or already received compressed storage. It never writes a partially decoded file. [[python/bounded-json-lines|Record reception]], [[python/zip-member-validation|Archive budgets]] and [[python/atomic-report-project|Staged publication]] each add a different boundary after or before decoding.',
r'''import gzip
import io
import zlib

def bounded_gzip(payload):
    if type(payload) is not bytes or len(payload) > 512:
        raise ValueError("compressed byte budget exceeded")
    try:
        with gzip.GzipFile(fileobj=io.BytesIO(payload), mode="rb") as decoder:
            expanded = decoder.read(129)
    except (OSError, EOFError, zlib.error) as failure:
        raise ValueError("invalid gzip stream") from failure
    if len(expanded) > 128:
        raise ValueError("expanded byte budget exceeded")
    return expanded

encoded = gzip.compress(b"receipt:125", mtime=0)
print("decoded:", bounded_gzip(encoded).decode("ascii"))
print("members:", bounded_gzip(gzip.compress(b"A", mtime=0) + gzip.compress(b"B", mtime=0)))
for invalid in (gzip.compress(b"x" * 129, mtime=0), encoded[:-1]):
    try:
        bounded_gzip(invalid)
    except ValueError:
        print("stream rejected")''',"decoded: receipt:125\nmembers: b'AB'\nstream rejected\nstream rejected",
'Returned output and accepted compressed input have explicit byte bounds. Decoder buffering and decompression work are implementation costs outside the returned-output limit. For hostile workloads, apply transport budgets and execution isolation rather than advertising this helper as a resource sandbox.',
['Small compressed input can expand beyond an application limit.','Stopping after a valid prefix may leave trailer corruption unobserved.'],['python/bounded-json-lines','python/zip-member-validation','python/strings-bytes'],subject='python-examples')

group('python-examples','Wire spelling, authentication and expansion budgets',['base64-records','hmac-envelope','gzip-output-budget'])

lesson('leased-outbox-project','Python SQLite outbox leases: stale workers must not acknowledge a newer claim',
'An outbox lease temporarily assigns a pending event to one worker and uses a claim token to distinguish successive owners.',
'The claim operation begins an immediate transaction, selects an unacknowledged expired or unclaimed row and updates it with a new token and deadline before committing. A second connection sees no eligible row while that lease is active. At the deadline a different worker can claim it with a different token. Acknowledgement matches both event ID and current token, so the first worker cannot complete a newer worker’s claim. Claim acquisition is serialized by this SQLite transaction; the external side effect is not inside it.',
'The fixture uses an owned temporary database, two real connections and a caller-supplied nondecreasing test clock. A production deployment needs an agreed time source, lock retry/deadline handling, lease renewal and recipient deduplication. The [[python/outbox-project|Atomic outbox write]] creates intent; a lease governs workers; [[python/idempotent-jobs|Stable replay identity]] governs repeated external delivery. None alone gives exactly-once effects.',
r'''import sqlite3
import tempfile
from pathlib import Path

def claim(connection, now, token):
    if type(now) is not int or not 0 <= now <= 1000000 or type(token) is not str or not token.isascii() or not token.isalnum() or not 1 <= len(token) <= 16:
        raise ValueError("bounded clock and fresh token required")
    connection.execute("BEGIN IMMEDIATE")
    try:
        row = connection.execute("SELECT event_id FROM outbox WHERE done=0 AND lease_until<=? ORDER BY event_id LIMIT 1", (now,)).fetchone()
        if row:
            connection.execute("UPDATE outbox SET token=?,lease_until=? WHERE event_id=?", (token, now + 10, row[0]))
        connection.commit()
        return row[0] if row else None
    except BaseException:
        connection.rollback()
        raise

def acknowledge(connection, event_id, token):
    cursor = connection.execute("UPDATE outbox SET done=1 WHERE event_id=? AND token=? AND done=0", (event_id, token))
    return cursor.rowcount == 1

with tempfile.TemporaryDirectory() as directory:
    path = Path(directory) / "owned.sqlite3"
    first = sqlite3.connect(path, isolation_level=None, timeout=0)
    second = sqlite3.connect(path, isolation_level=None, timeout=0)
    try:
        first.execute("CREATE TABLE outbox(event_id INTEGER PRIMARY KEY,token TEXT,lease_until INTEGER NOT NULL DEFAULT 0,done INTEGER NOT NULL DEFAULT 0)")
        first.execute("INSERT INTO outbox(event_id) VALUES(41)")
        print("first claim:", claim(first, 100, "claimA"))
        print("active lease:", claim(second, 109, "claimB"))
        print("reclaimed:", claim(second, 110, "claimB"))
        print("stale ack:", acknowledge(first, 41, "claimA"))
        print("current ack:", acknowledge(second, 41, "claimB"))
        print("after ack:", claim(first, 120, "claimC"))
    finally:
        second.close()
        first.close()''','first claim: 41\nactive lease: None\nreclaimed: 41\nstale ack: False\ncurrent ack: True\nafter ack: None',
'The teaching table contains one row. A large outbox needs measured query plans, indexes, retention and contention behavior. Tokens must be unique per claim and never reused for the same event: the parameter validator checks spelling, not global uniqueness. A late worker may still deliver after expiry, so recipients need their own event identity policy.',
['Reuse of a claim token defeats stale-owner rejection.','Lease expiry does not stop the old worker from producing an external effect.'],['python/outbox-project','python/sqlite-writer-contention','python/idempotent-jobs','spring/transaction-events'],subject='python-projects')

lesson('ttl-cache-project','Python TTL cache: expire at a defined boundary and use an injected clock',
'A TTL cache makes a stored value eligible only until its recorded expiry time, independently of its eviction order.',
'The cache stores at most four scalar receipt values. put validates its key, amount, TTL and clock before changing state. Expired entries are removed before capacity eviction; an overwrite receives a new expiry. get treats now equal to expiry as a miss and does not extend the TTL. The injected clock makes tests deterministic and allows the cache to reject clock reversal. A returned scalar has no mutable alias for the caller to modify.',
'TTL is freshness policy, not durable state or authorization. No background thread removes idle expired records; they remain until the next operation, still bounded by capacity. [[python/lru-project|Access-order eviction]], [[python/functools-cache|Memoization]] and [[python/expiry-exercise|Boundary exercises]] separate expiry from caching and retry decisions.',
r'''from collections import OrderedDict

class ReceiptTTL:
    def __init__(self, clock):
        self.clock, self.last = clock, -1
        self.entries = OrderedDict()
    def timestamp(self):
        now = self.clock()
        if type(now) is not int or not 0 <= now <= 1000000 or now < self.last:
            raise ValueError("bounded nondecreasing clock required")
        return now
    def expire(self, now):
        for key in [key for key, (_, until) in self.entries.items() if until <= now]:
            del self.entries[key]
        self.last = now
    def put(self, key, amount, ttl):
        if type(key) is not str or not key.isascii() or not key.isalnum() or not 1 <= len(key) <= 16 or type(amount) is not int or not 0 <= amount <= 1000000 or type(ttl) is not int or not 1 <= ttl <= 100:
            raise ValueError("bounded receipt fields required")
        now = self.timestamp()
        self.expire(now)
        self.entries[key] = (amount, now + ttl)
        self.entries.move_to_end(key)
        if len(self.entries) > 4:
            self.entries.popitem(last=False)
    def get(self, key):
        if type(key) is not str or not key.isascii() or not key.isalnum() or not 1 <= len(key) <= 16:
            raise ValueError("bounded key required")
        now = self.timestamp()
        self.expire(now)
        record = self.entries.get(key)
        return None if record is None else record[0]

ticks = [100]
cache = ReceiptTTL(lambda: ticks[0])
cache.put("R41", 125, 10)
ticks[0] = 109
print("before expiry:", cache.get("R41"))
ticks[0] = 110
print("at expiry:", cache.get("R41"))
cache.put("R41", 250, 5)
ticks[0] = 109
try:
    cache.get("R41")
except ValueError:
    print("clock reversal rejected")
print("retained:", list(cache.entries))''',"before expiry: 125\nat expiry: None\nclock reversal rejected\nretained: ['R41']",
'Expiry scanning is O(C) per operation for capacity C, with O(C) storage. The accepted capacity is fixed at four, so this is intentionally simpler than a heap of deadlines. Clock callbacks must be owned, side-effect-controlled code; a lock is still required if multiple threads share this cache.',
['Specify whether now equal to expiry is accepted.','Do not confuse write-order eviction with access-order LRU.'],['python/lru-project','python/ordered-dictionaries','python/expiry-exercise'],subject='python-projects')

group('python-projects','Worker claims and time-bounded application state',['leased-outbox-project','ttl-cache-project'])

lesson('wheel-metadata','Python wheel metadata: inspect an owned built artifact before installation',
'A wheel is a ZIP-based distribution artifact whose metadata describes its project, version, compatibility tags and installed-file records.',
'The fixture builds one owned pure-Python wheel offline with a fixed project/version, then reads its single dist-info METADATA and WHEEL files without installing or importing its application package. Name and Version identify the distribution; the compatibility tag describes the built artifact. The printout confirms these recorded fields, but it is not a signature or a claim that every declared requirement can be resolved on another machine.',
'This inspector reads only the artifact it just built. A received archive needs [[python/zip-member-validation|Member and expansion budgets]] before inspection. A tag saying py3-none-any does not prove that the source avoids newer syntax or unavailable dependencies. [[python/wheel-installation|Installed import origin]], [[python/runtime-compatibility|Runtime checks]] and [[python/pyproject-config|Build metadata]] must agree with the claimed support range.',
r'''import email.parser
from pathlib import Path
import subprocess
import sys
import tempfile
import zipfile

with tempfile.TemporaryDirectory() as directory:
    project = Path(directory)
    (project / "pyproject.toml").write_text('[build-system]\nrequires=["setuptools==84.0.0"]\nbuild-backend="setuptools.build_meta"\n[project]\nname="aitrove-owned-receipt"\nversion="0.1.0"\nrequires-python=">=3.11"\n[tool.setuptools]\npy-modules=["receipt_value"]\n')
    (project / "receipt_value.py").write_text('AMOUNT = 125\n')
    subprocess.run([sys.executable, "-I", "-m", "build", "--wheel", "--no-isolation", str(project)], check=True, capture_output=True, timeout=20)
    artifact, = (project / "dist").glob("*.whl")
    with zipfile.ZipFile(artifact) as archive:
        metadata_name, = [name for name in archive.namelist() if name.endswith(".dist-info/METADATA")]
        wheel_name, = [name for name in archive.namelist() if name.endswith(".dist-info/WHEEL")]
        metadata = email.parser.Parser().parsestr(archive.read(metadata_name).decode("utf-8"))
        wheel = email.parser.Parser().parsestr(archive.read(wheel_name).decode("utf-8"))
    print("name:", metadata["Name"])
    print("version:", metadata["Version"])
    print("python:", metadata["Requires-Python"])
    print("tag:", wheel["Tag"])''','name: aitrove-owned-receipt\nversion: 0.1.0\npython: >=3.11\ntag: py3-none-any',
'Build work depends on the backend and project size. Metadata parsing requires decoded file storage. The owned fixture has fixed small inputs; these costs are not an untrusted-wheel budget or a dependency supply-chain audit.',
['Compatibility metadata is a declared support claim that still needs execution tests.','Reading wheel metadata is different from installing or trusting its code.'],['python/pyproject-config','python/wheel-installation','python/editable-installation'],subject='python-packaging',dependencies=['build==1.6.1','setuptools==84.0.0'])
group('python-packaging','Built artifact inspection',['wheel-metadata'])

lesson('quantile-policy','Python quantiles: choose an interpolation policy before reporting a threshold',
'A sample quantile estimates a cut point in sorted observations using a selected rank and interpolation rule.',
'The receipt-duration fixture validates 2 to 128 bounded finite numeric observations and compares inclusive and exclusive quartile policies on the same four values. They produce different cut points because they make different assumptions about the sample endpoints. Neither choice changes the actual observed durations. The result must carry its policy and sample definition if another service will reproduce a threshold.',
'A quantile is not an observed record, a confidence interval or a proof of future latency. This fixture treats observations as an owned sample, with no claim about independent arrivals or production representativeness. [[python/bootstrap-means|Resampling]], [[python/numpy-precision|Numeric representation]] and [[python/pandas-rolling|Window membership]] concern other sources of uncertainty.',
r'''import math
import statistics

def quartiles(durations, method):
    if type(durations) is not list or not 2 <= len(durations) <= 128 or method not in ("inclusive", "exclusive") or any(type(value) not in (int, float) or not math.isfinite(value) or not 0 <= value <= 1000000 for value in durations):
        raise ValueError("bounded finite durations and declared policy required")
    return statistics.quantiles(durations, n=4, method=method)

durations = [100, 200, 300, 400]
print("inclusive:", quartiles(durations, "inclusive"))
print("exclusive:", quartiles(durations, "exclusive"))
try:
    quartiles([100, float("nan")], "inclusive")
except ValueError:
    print("nonfinite duration rejected")''','inclusive: [175.0, 250.0, 325.0]\nexclusive: [125.0, 250.0, 375.0]\nnonfinite duration rejected',
'Sorting n observations takes O(n log n) time and O(n) working storage in this library operation. The returned three cut points have fixed size. Input numbers and collection length are bounded here; output decimal formatting does not improve measurement accuracy.',
['State the interpolation rule alongside a reported quantile.','Remove or reject nonfinite values through an explicit policy, not accidental sort behavior.'],['python/bootstrap-means','python/numpy-precision','python/pandas-rolling'],subject='python-data')

lesson('time-series-validation','Python time-series validation: fit on past rows and leave a declared gap',
'Time-series validation evaluates later observations using training rows that precede them, rather than randomly mixing future and past records.',
'The owned twelve-row fixture uses three expanding training folds, two later test rows per fold and one excluded row between each training and test block. A StandardScaler is fitted separately on each training block; its mean is printed beside that fold’s boundaries. No test rows alter those fitted means. The values represent an equally spaced teaching series, not an evaluated predictive model.',
'A gap measured in rows is not necessarily a gap in time for irregular observations. Label horizons, late-arriving features, grouped subjects and transformations performed before splitting can still leak future information. [[python/ml-pipeline|Training-only transforms]], [[python/pandas-resample|Time bins]] and [[python/classification-metrics|Evaluation definitions]] need compatible assumptions.',
r'''import numpy as np
from sklearn.model_selection import TimeSeriesSplit
from sklearn.preprocessing import StandardScaler

observations = np.arange(12, dtype=float).reshape(-1, 1)
splitter = TimeSeriesSplit(n_splits=3, test_size=2, gap=1)
for training, evaluation in splitter.split(observations):
    scaler = StandardScaler().fit(observations[training])
    print("train:", [int(training[0]), int(training[-1])],
          "test:", [int(evaluation[0]), int(evaluation[-1])],
          "mean:", float(scaler.mean_[0]))''','train: [0, 4] test: [6, 7] mean: 2.0\ntrain: [0, 6] test: [8, 9] mean: 3.0\ntrain: [0, 8] test: [10, 11] mean: 4.0',
'Fold generation stores index arrays; each scaler fit processes that fold’s training rows and feature count. Expanding folds repeat earlier work. This trace verifies membership and fitted statistics, not model quality, causality or adequacy of the chosen one-row gap.',
['Random row splitting can expose future behavior to training.','Choose a gap from the feature and label horizon rather than a cosmetic row count.'],['python/ml-pipeline','python/pandas-resample','python/classification-metrics'],subject='python-data',dependencies=['numpy==2.5.3','scikit-learn==1.9.1'])
group('python-data','Declared sampling and temporal evaluation policies',['quantile-policy','time-series-validation'])

lesson('flask-multipart-budgets','Python Flask multipart uploads: bound the body, part count and accepted file',
'A multipart request divides an HTTP body into named fields and file parts that need both parser-level and application-level limits.',
'The owned endpoint requires exactly one receipt_id field and one receipt file. Flask limits the total body, parser field memory and part count before the endpoint validates the accepted names. The application reads at most 129 file bytes for a 128-byte limit and returns only a byte count. It never uses the received filename as a storage path. Three test requests check an accepted upload, an oversized file and a multipart body containing an extra part.',
'Parser limits do not replace reverse-proxy limits or a real transport deadline. Reaching request.form or request.files can trigger parsing, so catching errors after partially saving files is too late for staged publication. [[python/flask-error-boundaries|Public error shape]], [[python/bounded-json-lines|Reception budgets]] and [[python/pathlib-files|Owned paths]] cover the adjacent boundaries. This endpoint uses a local test client and has no public identity or storage service.',
r'''import io
import re
from flask import Flask, request

app = Flask(__name__)
app.config.update(MAX_CONTENT_LENGTH=4096, MAX_FORM_MEMORY_SIZE=4096, MAX_FORM_PARTS=2)
@app.errorhandler(413)
def too_large(failure):
    return {"error": "upload budget exceeded"}, 413

@app.post("/receipts")
def receive():
    if set(request.form) != {"receipt_id"} or set(request.files) != {"receipt"} or len(request.form.getlist("receipt_id")) != 1 or len(request.files.getlist("receipt")) != 1:
        return {"error": "exact parts required"}, 400
    if re.fullmatch(r"R-[0-9]{4}", request.form["receipt_id"]) is None:
        return {"error": "invalid receipt ID"}, 400
    payload = request.files["receipt"].stream.read(129)
    if len(payload) > 128:
        return {"error": "file byte budget exceeded"}, 413
    return {"bytes": len(payload)}, 201

with app.test_client() as client:
    accepted = client.post("/receipts", data={"receipt_id": "R-0041", "receipt": (io.BytesIO(b"amount=125"), "received.txt")})
    oversized = client.post("/receipts", data={"receipt_id": "R-0041", "receipt": (io.BytesIO(b"x" * 129), "received.txt")})
    extra = client.post("/receipts", data={"receipt_id": "R-0041", "receipt": (io.BytesIO(b"ok"), "received.txt"), "extra": "field"})
    print("accepted:", accepted.status_code, accepted.json)
    print("file limit:", oversized.status_code)
    print("part limit:", extra.status_code)''',"accepted: 201 {'bytes': 10}\nfile limit: 413\npart limit: 413",
'The endpoint retains at most 129 file bytes; parser and transport buffers have separate configured and implementation costs. A received request may already occupy upstream storage. Upload retention, authentication, content inspection and crash-durable publication are not provided by returning a count.',
['The received filename must not become an unchecked destination path.','Limit multipart part count as well as individual application payload size.'],['python/flask-error-boundaries','python/zip-member-validation','python/bounded-json-lines'],subject='python-web',dependencies=['Flask==3.1.3'])

lesson('django-owner-constraints','Python Django database constraints: enforce receipt identity per owner',
'A database uniqueness constraint rejects a conflicting stored identity even when application validation was bypassed.',
'The owned model defines receipt identity as owner_id plus receipt_id and requires a nonnegative amount at the database level. Two different owners may store the same receipt ID; a second row for the same owner is rejected. A bulk_create with a negative amount is rejected too, despite skipping model-level cleaning. Each expected failure is inside its own atomic block and caught outside it, leaving earlier accepted rows readable.',
'A declared owner field is not authentication. A request must obtain its owner from a trusted principal and filter reads as well as writes. [[python/drf-creation-ownership|Creation ownership]], [[python/drf-list-visibility|List visibility]] and [[python/django-atomic|Transaction failure scope]] are all required for a service policy. This fixture checks an owned in-memory SQLite schema, not another engine’s isolation or production migration history.',
r'''from django.conf import settings
settings.configure(INSTALLED_APPS=[], DATABASES={"default": {"ENGINE": "django.db.backends.sqlite3", "NAME": ":memory:"}}, DEFAULT_AUTO_FIELD="django.db.models.AutoField")
import django
django.setup()
from django.db import connection, models, transaction, IntegrityError

class OwnedReceipt(models.Model):
    owner_id = models.PositiveIntegerField()
    receipt_id = models.CharField(max_length=6)
    amount = models.IntegerField()
    class Meta:
        app_label = "owned_receipt_fixture"
        constraints = [models.UniqueConstraint(fields=["owner_id", "receipt_id"], name="owner_receipt_identity"),
                       models.CheckConstraint(condition=models.Q(amount__gte=0), name="owned_amount_nonnegative")]

with connection.schema_editor() as schema:
    schema.create_model(OwnedReceipt)
try:
    OwnedReceipt.objects.create(owner_id=1, receipt_id="R-0041", amount=125)
    OwnedReceipt.objects.create(owner_id=2, receipt_id="R-0041", amount=250)
    try:
        with transaction.atomic():
            OwnedReceipt.objects.create(owner_id=1, receipt_id="R-0041", amount=500)
    except IntegrityError:
        print("same-owner duplicate rejected")
    try:
        with transaction.atomic():
            OwnedReceipt.objects.bulk_create([OwnedReceipt(owner_id=1, receipt_id="R-0042", amount=-1)])
    except IntegrityError:
        print("bulk negative amount rejected")
    print("stored:", list(OwnedReceipt.objects.order_by("owner_id").values_list("owner_id", "amount")))
finally:
    connection.close()''',"same-owner duplicate rejected\nbulk negative amount rejected\nstored: [(1, 125), (2, 250)]",
'Constraint enforcement has engine/index-dependent costs; application preflight checks are not a replacement for it under concurrent writers. The fixture contains two rows and provides no measured production plan. CharField length and receipt spelling also need explicit schema validation; the uniqueness check alone does not enforce that grammar.',
['Application full_clean is not automatically called by every write path.','Uniqueness per owner does not authorize a received owner_id.'],['python/drf-creation-ownership','python/drf-list-visibility','python/django-atomic','python/django-migrations'],subject='python-web',dependencies=['Django==5.2.17'])
group('python-web','Reception and database-enforced identity boundaries',['flask-multipart-budgets','django-owner-constraints'])

lesson('tracemalloc-retention','Python tracemalloc: distinguish retained Python allocations from a process memory claim',
'Tracemalloc records traced Python memory allocations so snapshots can compare where owned allocations remain reachable.',
'The owned fixture starts tracing before creating sixty-four 1KiB bytearrays. It compares a snapshot taken with the retained list against a baseline, then clears the list and collects before measuring current traced storage again. It reports only qualitative relationships with broad thresholds, rather than claiming exact bytes are portable across interpreter builds. The same data would remain retained if another object still referenced the list contents.',
'Traced allocations are not total resident process memory, native extension buffers or proof of a leak. A valid cache may intentionally retain objects. [[python/weak-references|Reachability]], [[python/slots|Object representation]] and [[python/functools-cache|Cache retention]] explain why some memory remains owned. Start tracing early enough to observe the allocations you want to investigate.',
r'''import gc
import tracemalloc

tracemalloc.start()
try:
    baseline = tracemalloc.take_snapshot()
    retained = [bytearray(1024) for _ in range(64)]
    current, peak = tracemalloc.get_traced_memory()
    snapshot = tracemalloc.take_snapshot()
    positive_growth = sum(max(0, row.size_diff) for row in snapshot.compare_to(baseline, "lineno"))
    retained.clear()
    del retained, snapshot, baseline
    gc.collect()
    released, _ = tracemalloc.get_traced_memory()
    print("owned growth observed:", positive_growth >= 64 * 1024)
    print("release reduced current:", released < current // 2)
    print("peak includes retained:", peak >= current)
finally:
    tracemalloc.stop()''','owned growth observed: True\nrelease reduced current: True\npeak includes retained: True',
'Tracing adds allocation bookkeeping; storing snapshots and comparing them adds time and memory. Use a controlled workload and repeat measurements rather than converting one small fixture into a production memory ranking. Clearing references can reduce traced current storage without returning the same amount of resident memory to the operating system.',
['A high-water peak does not fall when retained objects are released.','Tracemalloc is not an RSS or native-buffer accounting tool.'],['python/weak-references','python/slots','python/functools-cache'],subject='python-testing')
group('python-testing','Owned allocation observations',['tracemalloc-retention'])

lesson('cancellation-interview','Python cancellation review: release a permit before propagating task cancellation',
'Task cancellation requests interruption at a coroutine suspension point; resource cleanup still needs a defined ownership scope.',
'The interview trace acquires a one-permit semaphore through async with, signals that acquisition and waits on an event. The controller cancels the task only after that signal. A finally clause records local cleanup, then the context manager releases the permit as cancellation leaves the block. The controller observes cancellation and a second task acquires the same permit. The answer should explain this ordering and identify which part changes if cancellation is swallowed.',
'Cancel is a request rather than a synchronous kill. A coroutine doing CPU work without suspension may not observe it promptly. Catching CancelledError and continuing can change shutdown and timeout behavior. [[python/async-shield-ownership|Retained inner tasks]], [[python/async-deadlines|Deadline scopes]] and [[python/context-managers|Cleanup]] describe different ways cancellation interacts with ownership.',
r'''import asyncio

async def review():
    permit = asyncio.Semaphore(1)
    started, blocked = asyncio.Event(), asyncio.Event()
    trace = []
    async def worker():
        async with permit:
            started.set()
            try:
                await blocked.wait()
            finally:
                trace.append("cleanup")
    task = asyncio.create_task(worker())
    await started.wait()
    task.cancel()
    try:
        await task
    except asyncio.CancelledError:
        trace.append("cancelled")
    async with permit:
        trace.append("next acquired")
    print(trace)
    print("permit available:", not permit.locked())

asyncio.run(review())''',"['cleanup', 'cancelled', 'next acquired']\npermit available: True",
'The fixture owns one blocked worker and one semaphore; no external I/O occurs. For a review exercise, ask where a network client, partial write or background task would live and who must await its final outcome. This trace is not a real-server cancellation or fairness test.',
['A finally block must not conceal a failure through a return statement.','Cancelling a task does not undo an already completed external write.'],['python/async-shield-ownership','python/async-deadlines','python/concurrency-interview'],subject='python-interview')
group('python-interview','Cancellation and permit ownership review',['cancellation-interview'])

lesson('expiry-exercise','Python expiry exercise: separate pending, active and expired records at exact boundaries',
'An expiry classifier assigns records to time states using declared inclusive and exclusive boundaries.',
'The exercise accepts an owned list of at most sixty-four unique receipt records and a bounded exact-integer clock. A record is pending before its creation time, active from creation through the instant before created plus TTL, and expired at or after that endpoint. Validate every record before returning any result. A duplicate identity or Boolean TTL fails the batch instead of quietly choosing one record. Results are sorted IDs so caller row order cannot change their presentation.',
'The clock and record times use the same abstract integer unit; the fixture does not interpret wall-clock zones or accept serialized timestamps. It never deletes or renews records. [[python/ttl-cache-project|Cache expiry]], [[python/datetime-boundaries|Time representation]] and [[python/reconciliation-exercise|Duplicate-aware batches]] add those policies separately. Test the exact creation and expiry instants, not only values comfortably inside the interval.',
r'''def classify_expiry(records, now):
    if type(now) is not int or not 0 <= now <= 1000000 or type(records) is not list or len(records) > 64:
        raise ValueError("bounded records and clock required")
    seen, states = set(), {"pending": [], "active": [], "expired": []}
    for record in records:
        if type(record) is not dict or set(record) != {"receipt_id", "created", "ttl"}:
            raise ValueError("exact fields required")
        identifier, created, ttl = record["receipt_id"], record["created"], record["ttl"]
        if type(identifier) is not str or not identifier.isascii() or not identifier.isalnum() or not 1 <= len(identifier) <= 16 or identifier in seen or type(created) is not int or not 0 <= created <= 1000000 or type(ttl) is not int or not 1 <= ttl <= 100:
            raise ValueError("unique ID and bounded times required")
        seen.add(identifier)
        state = "pending" if now < created else "active" if now < created + ttl else "expired"
        states[state].append(identifier)
    return {state: sorted(identifiers) for state, identifiers in states.items()}

records = [{"receipt_id": "R41", "created": 100, "ttl": 10},
           {"receipt_id": "R42", "created": 110, "ttl": 5},
           {"receipt_id": "R43", "created": 120, "ttl": 5}]
print(classify_expiry(records, 110))
try:
    classify_expiry(records + [dict(records[0])], 110)
except ValueError:
    print("duplicate batch rejected")''',"{'pending': ['R43'], 'active': ['R42'], 'expired': ['R41']}\nduplicate batch rejected",
'Validation and classification take O(n), with up to O(n log n) sorting and O(n) private result storage. The supplied records are left unchanged even on rejection. This is a snapshot calculation; applying its result to mutable service state later would require a concurrency policy.',
['State whether the expiry endpoint is active or expired.','Reject duplicate identities before returning a batch result.'],['python/ttl-cache-project','python/reconciliation-exercise','python/datetime-boundaries'],subject='python-exercises')
group('python-exercises','Clock and identity boundary exercises',['expiry-exercise'])

SERVICE_BANKS = {
'python-protocol-lifetimes': ('Python wire and lifetime contracts quiz', ['python/assert-validation','python/binary-records','python/base64-records','python/hmac-envelope','python/gzip-output-budget','python/generator-control','python/async-shield-ownership','python/condition-predicates'], [
('What happens to assert expressions under -O?', ['They always run twice','Their checks and expression evaluation can be omitted','They become database constraints','They validate every annotation'],1,'Required validation and side effects must use explicit application code rather than an optimization-dependent assertion.'),
('What does a positional-only parameter prevent?', ['Keyword binding to that parameter','Mutation of the passed object','All TypeError failures','Integer overflow'],0,'The slash controls call binding. It does not freeze the object or validate its domain.'),
('Where does an ordinary ChainMap write go?', ['Every mapping','The last mapping','The first mapping','A new deep copy'],2,'Reads search the layers, but ordinary mutations target the first mapping.'),
('What does ! in this struct format specify?', ['Compression','Native alignment','Authentication','Network byte order with standard sizes'],3,'An explicit portable binary layout avoids host-dependent native alignment.'),
('Why re-encode decoded Base64 in this fixture?', ['To enforce the agreed canonical spelling','To encrypt it','To select an owner','To update the interpreter'],0,'Decode validation and canonical representation checks address different acceptance rules.'),
('Can an identical valid HMAC message be replayed?', ['Never','Yes, unless a separate replay policy rejects it','Only if Base64 is missing','Only on Windows'],1,'Message authentication checks exact bytes. It does not by itself enforce freshness or single-use processing.'),
('What does the gzip output cap establish?', ['A total process-memory ceiling','A network deadline','A limit on returned expanded bytes','A signature'],2,'Decoder internals, upstream storage and CPU isolation are separate resource boundaries.'),
('What must happen before sending a non-None value to a new generator?', ['It must be pickled','Its output must be sorted','Its frame must be deleted','It must be primed to a yield'],3,'The first suspension point establishes where a sent value is received.'),
('Does shield prevent the awaiting caller from receiving cancellation?', ['No; the inner task can continue while the caller receives CancelledError','Yes, always','Only with a semaphore','Only when the task has no result'],0,'A retained inner task needs a completion owner after the original caller is cancelled.'),
('What should a condition waiter recheck after notification?', ['The notification count','The shared predicate while holding the lock','The file extension','The Python keyword list'],1,'A notification is a prompt to inspect state, not a stored application message.'),
('What index unit does the Z string fixture use?', ['UTF-8 byte offsets','Display columns','Unicode code-point positions','Grapheme-cluster positions'],2,'String indices do not automatically represent encoded byte or visible character boundaries.'),
('How do equal values affect the strict LIS fixture?', ['They always extend the length','They are invalid input','They select all records','They replace a candidate without extending strict length'],3,'bisect_left is consistent with strict increase; a nondecreasing policy needs a different boundary.'),
]),
'python-service-state': ('Python service state and measurement quiz', ['python/leased-outbox-project','python/ttl-cache-project','python/django-owner-constraints','python/flask-multipart-budgets','python/tracemalloc-retention','python/time-series-validation'], [
('Why match the current claim token during acknowledgement?', ['To reject acknowledgement by a stale owner','To compress the database','To authenticate an HTTP user','To guarantee one external delivery'],0,'A reclaimed event has a new ownership generation. An old worker must not complete that generation.'),
('Can an expired worker still produce an external effect?', ['No, the database kills it','Yes; recipient deduplication remains necessary','Only after a cache hit','Only on a self-loop'],1,'A lease changes claim eligibility; it does not terminate a remote action already in progress.'),
('What does this TTL cache do at now equal to expiry?', ['Return a hit','Renew the TTL','Return a miss and remove the expired entry','Change the clock'],2,'The acceptance interval ends before the expiry endpoint.'),
('Does get renew this cache entry?', ['Always','Only at capacity','Only for zero amounts','No'],3,'Expiry is based on put; a read does not extend its stored deadline.'),
('Why place identity uniqueness in the database?', ['Write paths can bypass application preflight checks and concurrent writers can race','To remove authentication','To sort every API response','To make fields immutable'],0,'A stored constraint enforces its declared key policy on database writes, including paths that skip model cleaning.'),
('Does per-owner uniqueness authorize a received owner_id?', ['Always','No; the server still needs a trusted principal and visibility rules','Only for positive integers','Only for bulk_create'],1,'Data integrity and request authorization are distinct contracts.'),
('Which upload limits must be considered together?', ['Filename length only','Number of routes only','Body bytes, parser parts/memory and application payload bytes','Python version only'],2,'An individual file check does not bound total multipart reception or part count.'),
('What does tracemalloc primarily observe?', ['Every process RSS allocation','All native extension buffers','All network bytes','Traced Python allocations'],3,'A traced snapshot is not complete operating-system resident-memory accounting.'),
('Does release reduce the recorded peak?', ['No; peak is a high-water measurement','Yes, immediately to zero','Only in Flask','Only after sorting'],0,'Current storage can fall while the recorded peak still reflects earlier retained allocations.'),
('Why fit a scaler inside each temporal training fold?', ['To reuse test labels','To avoid learning transform statistics from later evaluation rows','To guarantee causality','To ignore missing observations'],1,'Membership and transformation order must both respect the evaluation boundary.'),
('What can a gap measured in rows fail to establish?', ['Index ordering','Training row count','A fixed duration for irregular observation times','The existence of a test fold'],2,'A row count is not a time interval unless spacing and membership assumptions support that interpretation.'),
('What does wheel metadata inspection prove here?', ['Registry authenticity','Every-platform execution','A complete dependency lock','The recorded fields in the owned built artifact'],3,'Declared metadata and compatibility tags still need installation, runtime and dependency checks.'),
])}
for slug, (title, refs, questions) in SERVICE_BANKS.items():
 BANKS[slug] = (title, questions)
 path = 'quizzes/' + slug
 entry = copy.deepcopy(lookup['quizzes/python-basics'])
 entry.update(id=str(uuid.uuid5(uuid.NAMESPACE_URL,'https://aitrove.in/'+path)),path=path,title=title,summary='Twelve explained questions on selected Python operation contracts.',tags=['python','quiz'],sort_order=500+len(added),published_at=stamp,updated_at=stamp)
 entry['body']=para('A Python self-check tests selected input, ownership and failure contracts through twelve explained questions.')+'<h2>Review the related lessons</h2><ul>'+''.join('<li><a href="/'+p+'">'+html.escape(lookup[p]['title'])+'</a></li>' for p in refs)+'</ul><h3>Common Mistakes</h3>'+para('A correct local answer does not establish a deployed service or an exhaustive reference. Read each operation boundary before changing its inputs. Results remain in this browser.')
 entry['data']['questions']=[{'prompt':prompt,'options':options,'answer':answer,'explanation':explanation} for prompt,options,answer,explanation in questions]
 entry['data']['related']=[{'path':p,'title':lookup[p]['title']} for p in refs]
 upsert(entry);added.append(path)

SERVICE_REVERSE = {
'python/exceptions':['assert-validation'], 'python/function-arguments':['signature-boundaries'],
'python/configuration-precedence':['chainmap-configuration'], 'python/strings-bytes':['binary-records','base64-records'],
'python/memoryview-buffers':['binary-records'], 'python/generators':['generator-control'],
'python/async-deadlines':['async-shield-ownership','cancellation-interview'], 'python/thread-locks':['condition-predicates'],
'python/graph-bridges':['articulation-points','directed-euler-trail'], 'python/strongly-connected-components':['component-condensation'],
'python/topological-sort':['component-condensation'], 'python/kmp-search':['z-string-search'],
'python/bisect-insertion':['lis-reconstruction'], 'python/longest-common-subsequence':['lis-reconstruction'],
'python/json-validation':['hmac-envelope'], 'python/bounded-json-lines':['gzip-output-budget','base64-records'],
'python/zip-member-validation':['gzip-output-budget'], 'python/outbox-project':['leased-outbox-project'],
'python/idempotent-jobs':['leased-outbox-project','hmac-envelope'], 'python/lru-project':['ttl-cache-project'],
'python/wheel-installation':['wheel-metadata'], 'python/bootstrap-means':['quantile-policy'],
'python/ml-pipeline':['time-series-validation'], 'python/pandas-resample':['time-series-validation'],
'python/flask-json-api':['flask-multipart-budgets'], 'python/drf-creation-ownership':['django-owner-constraints'],
'python/drf-list-visibility':['django-owner-constraints'], 'python/django-models':['django-owner-constraints'],
'python/weak-references':['tracemalloc-retention'], 'python/concurrency-interview':['cancellation-interview'],
'python/reconciliation-exercise':['expiry-exercise']}
for original, slugs in SERVICE_REVERSE.items():
 assert original in lookup, original
 targets = ['python/'+slug for slug in slugs]
 assert all(target in lookup for target in targets), targets
 entry = lookup[original]; marker = '<h2>Follow the service contract</h2>'
 entry['body'] = entry['body'].split(marker)[0] + marker + para(', '.join('[['+path+'|'+lookup[path]['title']+']]' for path in targets)+'.')
 known={item['path'] for item in entry['data'].get('related',[])}
 entry['data'].setdefault('related',[]).extend({'path':path,'title':lookup[path]['title']} for path in targets if path not in known)
