"""Independent graph/sequence/state oracles and service failure boundaries."""
import base64
import contextlib
import copy
import gzip
import io
import itertools
import json
from pathlib import Path
import random
import runpy
import sqlite3
import subprocess
import sys
import tempfile
import unittest

HERE = Path(__file__).resolve().parent
COUNTS = {}
def load(name):
    with contextlib.redirect_stdout(io.StringIO()):
        return runpy.run_path(str(HERE / (name + '.py')))
def counted(name):
    COUNTS[name] = COUNTS.get(name, 0) + 1
def component_count(size, edges, removed=None):
    unseen = set(range(size)) - {removed}
    count = 0
    while unseen:
        count += 1
        pending = [unseen.pop()]
        while pending:
            vertex = pending.pop()
            for left, right in edges:
                neighbor = right if left == vertex else left if right == vertex else None
                if neighbor in unseen:
                    unseen.remove(neighbor)
                    pending.append(neighbor)
    return count

class ServiceContracts(unittest.TestCase):
    def test_vertex_removal_oracle(self):
        operation = load('articulation_points')['articulation_points']
        randomizer = random.Random(141)
        for _ in range(500):
            size = randomizer.randrange(1, 9)
            edges = [(randomizer.randrange(size), randomizer.randrange(size)) for _ in range(randomizer.randrange(20))]
            baseline = component_count(size, edges)
            expected = [vertex for vertex in range(size) if component_count(size, edges, vertex) > baseline]
            self.assertEqual(operation(size, edges), expected)
            counted('removedVertexConnectivityOracle')
        self.assertEqual(operation(0, []), [])
        with self.assertRaises(ValueError): operation(2, [(True, 1)])

    def test_condensation_reachability_oracle(self):
        operation = load('component_condensation')['condensation']
        randomizer = random.Random(142)
        for _ in range(500):
            size = randomizer.randrange(1, 9)
            edges = [(randomizer.randrange(size), randomizer.randrange(size)) for _ in range(randomizer.randrange(20))]
            reaches = []
            for origin in range(size):
                reached, pending = {origin}, [origin]
                while pending:
                    source = pending.pop()
                    for left, right in edges:
                        if left == source and right not in reached:
                            reached.add(right); pending.append(right)
                reaches.append(reached)
            partition = []
            unseen = set(range(size))
            while unseen:
                origin = min(unseen)
                members = sorted(vertex for vertex in unseen if vertex in reaches[origin] and origin in reaches[vertex])
                partition.append(members); unseen.difference_update(members)
            components, collapsed = operation(size, edges)
            self.assertEqual(components, partition)
            owner = {vertex: index for index, members in enumerate(partition) for vertex in members}
            self.assertEqual(collapsed, sorted({(owner[left], owner[right]) for left, right in edges if owner[left] != owner[right]}))
            indegrees = [sum(target == vertex for _, target in collapsed) for vertex in range(len(partition))]
            available = [vertex for vertex, degree in enumerate(indegrees) if degree == 0]
            consumed = 0
            while available:
                source = available.pop(); consumed += 1
                for left, right in collapsed:
                    if left == source:
                        indegrees[right] -= 1
                        if indegrees[right] == 0: available.append(right)
            self.assertEqual(consumed, len(partition))
            counted('mutualReachabilityCondensationOracle')

    def test_euler_edge_permutation_oracle(self):
        operation = load('directed_euler_trail')['euler_trail']
        randomizer = random.Random(143)
        for _ in range(250):
            size = randomizer.randrange(1, 5)
            edges = [(randomizer.randrange(size), randomizer.randrange(size)) for _ in range(randomizer.randrange(8))]
            exists = any(all(edges[order[index]][1] == edges[order[index + 1]][0] for index in range(len(order) - 1)) for order in itertools.permutations(range(len(edges))))
            if exists:
                trail = operation(size, edges)
                self.assertEqual(sorted(trail), list(range(len(edges))))
                self.assertTrue(all(edges[trail[index]][1] == edges[trail[index + 1]][0] for index in range(len(trail) - 1)))
            else:
                with self.assertRaises(ValueError): operation(size, edges)
            counted('edgePermutationTrailOracle')
        with self.assertRaises(ValueError): operation(2, [(0, True)])

    def test_z_direct_match_oracle(self):
        operation = load('z_string_search')['z_matches']
        randomizer = random.Random(144)
        for _ in range(2000):
            text = ''.join(randomizer.choice('$abé') for _ in range(randomizer.randrange(40)))
            pattern = ''.join(randomizer.choice('$abé') for _ in range(randomizer.randrange(8)))
            self.assertEqual(operation(text, pattern), [index for index in range(len(text) + 1) if text.startswith(pattern, index)])
            counted('directSubstringOracle')
        with self.assertRaises(ValueError): operation('a' * 129, 'a')

    def test_lis_all_subsequences_oracle(self):
        operation = load('lis_reconstruction')['increasing_subsequence']
        randomizer = random.Random(145)
        for _ in range(500):
            values = [randomizer.randrange(-4, 5) for _ in range(randomizer.randrange(11))]
            longest = 0
            for mask in range(1 << len(values)):
                candidate = [value for index, value in enumerate(values) if mask & (1 << index)]
                if all(left < right for left, right in zip(candidate, candidate[1:])):
                    longest = max(longest, len(candidate))
            selected = operation(values)
            self.assertEqual(len(selected), longest)
            self.assertTrue(all(left < right for left, right in zip(selected, selected[1:])))
            cursor = iter(values)
            self.assertTrue(all(any(value == chosen for value in cursor) for chosen in selected))
            counted('exhaustiveSubsequenceOracle')
        with self.assertRaises(ValueError): operation([True])

    def test_ttl_reference_state(self):
        cache_type = load('ttl_cache_project')['ReceiptTTL']
        randomizer = random.Random(146)
        tick = [0]
        cache, reference = cache_type(lambda: tick[0]), []
        for _ in range(10000):
            tick[0] += randomizer.randrange(3)
            key = 'R' + str(randomizer.randrange(8))
            reference = [record for record in reference if record[2] > tick[0]]
            if randomizer.random() < .6:
                amount, ttl = randomizer.randrange(1000), randomizer.randrange(1, 30)
                reference = [record for record in reference if record[0] != key]
                reference.append((key, amount, tick[0] + ttl))
                reference = reference[-4:]
                cache.put(key, amount, ttl)
            else:
                expected = next((amount for identifier, amount, _ in reference if identifier == key), None)
                self.assertEqual(cache.get(key), expected)
            self.assertEqual(list(cache.entries.items()), [(key, (amount, until)) for key, amount, until in reference])
            counted('orderedExpiryStateOracle')
        before = copy.deepcopy(cache.entries), cache.last
        with self.assertRaises(ValueError): cache.put('R41', True, 10)
        self.assertEqual((cache.entries, cache.last), before)
        tick[0] -= 1
        with self.assertRaises(ValueError): cache.get('R41')
        self.assertEqual((cache.entries, cache.last), before)
        tick[0] = -1
        with self.assertRaises(ValueError): cache_type(lambda: tick[0]).get('R41')

    def test_expiry_interval_oracle(self):
        operation = load('expiry_exercise')['classify_expiry']
        randomizer = random.Random(147)
        for _ in range(1000):
            records = [{'receipt_id': 'R' + str(index), 'created': randomizer.randrange(100), 'ttl': randomizer.randrange(1, 30)} for index in range(randomizer.randrange(20))]
            before = copy.deepcopy(records)
            now = randomizer.randrange(130)
            expected = {'pending': [], 'active': [], 'expired': []}
            for record in records:
                if record['created'] > now: expected['pending'].append(record['receipt_id'])
                elif record['created'] + record['ttl'] <= now: expected['expired'].append(record['receipt_id'])
                else: expected['active'].append(record['receipt_id'])
            self.assertEqual(operation(records, now), {state: sorted(identifiers) for state, identifiers in expected.items()})
            self.assertEqual(records, before)
            counted('declaredIntervalOracle')
        record = {'receipt_id': 'R41', 'created': 100, 'ttl': 10}
        for invalid in ([record, record], [dict(record, ttl=True)], [dict(record, extra=1)]):
            before = copy.deepcopy(invalid)
            with self.assertRaises(ValueError): operation(invalid, 100)
            self.assertEqual(invalid, before)

    def test_encoding_authentication_and_expansion(self):
        decoder = load('base64_records')['canonical_bytes']
        randomizer = random.Random(148)
        for _ in range(500):
            payload = bytes(randomizer.randrange(256) for _ in range(randomizer.randrange(33)))
            self.assertEqual(decoder(base64.b64encode(payload).decode('ascii')), payload)
            counted('ownedBase64RoundTripOracle')
        for encoded in ('fR==', 'fQ==\n', 'fQ', '__8=', base64.b64encode(b'x' * 33).decode('ascii')):
            with self.assertRaises(ValueError): decoder(encoded)
        expanded = load('gzip_output_budget')['bounded_gzip']
        self.assertEqual(expanded(gzip.compress(b'x' * 128, mtime=0)), b'x' * 128)
        for payload in (gzip.compress(b'x' * 129, mtime=0), gzip.compress(b'x' * 65, mtime=0) + gzip.compress(b'x' * 64, mtime=0), b'x' * 513, gzip.compress(b'valid', mtime=0)[:-1]):
            with self.assertRaises(ValueError): expanded(payload)
        damaged = bytearray(gzip.compress(b'valid', mtime=0)); damaged[-8] ^= 1
        with self.assertRaises(ValueError): expanded(bytes(damaged))
        signed = load('hmac_envelope')
        self.assertTrue(signed['authenticated'](signed['payload'], signed['tag']))
        self.assertFalse(signed['authenticated'](signed['payload'] + b' ', signed['tag']))
        self.assertFalse(signed['authenticated'](b'x' * 129, signed['tag']))
        self.assertFalse(signed['authenticated'](signed['payload'], signed['tag'].upper()))

    def test_leases_reclaim_stale_ack_and_contention(self):
        namespace = load('leased_outbox_project')
        with tempfile.TemporaryDirectory() as directory:
            path = Path(directory) / 'lease.sqlite3'
            first, second = sqlite3.connect(path, isolation_level=None, timeout=0), sqlite3.connect(path, isolation_level=None, timeout=0)
            try:
                first.execute('CREATE TABLE outbox(event_id INTEGER PRIMARY KEY,token TEXT,lease_until INTEGER NOT NULL DEFAULT 0,done INTEGER NOT NULL DEFAULT 0)')
                first.executemany('INSERT INTO outbox(event_id) VALUES(?)', [(41,), (42,)])
                self.assertEqual(namespace['claim'](first, 100, 'claimA'), 41)
                self.assertEqual(namespace['claim'](second, 100, 'claimB'), 42)
                self.assertIsNone(namespace['claim'](second, 109, 'claimC'))
                self.assertEqual(namespace['claim'](second, 110, 'claimC'), 41)
                self.assertFalse(namespace['acknowledge'](first, 41, 'claimA'))
                self.assertTrue(namespace['acknowledge'](second, 41, 'claimC'))
                self.assertFalse(namespace['acknowledge'](second, 41, 'claimC'))
                first.execute('BEGIN IMMEDIATE')
                with self.assertRaises(sqlite3.OperationalError): namespace['claim'](second, 120, 'claimD')
                self.assertFalse(second.in_transaction)
                first.rollback()
                self.assertEqual(namespace['claim'](second, 120, 'claimD'), 42)
                before = first.execute('SELECT * FROM outbox ORDER BY event_id').fetchall()
                with self.assertRaises(ValueError): namespace['claim'](first, True, 'claimE')
                self.assertEqual(first.execute('SELECT * FROM outbox ORDER BY event_id').fetchall(), before)
            finally:
                second.close(); first.close()

    def isolated(self, name, checks, keep_database=False):
        source = 'import contextlib,io,runpy,sys\n'
        if keep_database:
            source += 'from pathlib import Path\nnamespace={}\nwith contextlib.redirect_stdout(io.StringIO()):\n    exec(compile(Path(sys.argv[1]).read_text().replace("    connection.close()", "    pass"), sys.argv[1], "exec"),namespace)\n'
        else:
            source += 'with contextlib.redirect_stdout(io.StringIO()):\n    namespace=runpy.run_path(sys.argv[1])\n'
        source += checks + '\nprint("service boundary passed")\n'
        result = subprocess.run([sys.executable, '-I', '-c', source, str(HERE / (name + '.py'))], capture_output=True, text=True, timeout=30)
        self.assertEqual(result.returncode, 0, result.stderr)
        self.assertEqual(result.stdout, 'service boundary passed\n')

    def test_multipart_rejection(self):
        self.isolated('flask_multipart_budgets', '''
from werkzeug.datastructures import MultiDict
with namespace['app'].test_client() as client:
    for data, status in [({'receipt_id':'bad','receipt':(io.BytesIO(b'ok'),'../../ignored.txt')},400),
                         ({'receipt_id':'R-0041'},400),
                         ({'receipt_id':'R-0041','receipt':(io.BytesIO(b'x'*128),'../../ignored.txt')},201),
                         ({'receipt_id':'R-0041','receipt':(io.BytesIO(b'x'*129),'ignored.txt')},413)]:
        response=client.post('/receipts',data=data)
        assert response.status_code==status,(response.status_code,status)
    response=client.post('/receipts',data=MultiDict([('receipt_id','R-0041'),('receipt_id','R-0042'),('receipt',(io.BytesIO(b'ok'),'ignored.txt'))]))
    assert response.status_code==413
    assert client.post('/receipts',data=b'x'*4097,content_type='multipart/form-data; boundary=owned').status_code==413
''')

    def test_database_identity_and_bulk_constraints(self):
        self.isolated('django_owner_constraints', '''
Receipt=namespace['OwnedReceipt']
transaction=namespace['transaction']
IntegrityError=namespace['IntegrityError']
assert Receipt.objects.count()==2
for values in [dict(owner_id=1,receipt_id='R-0041',amount=50),dict(owner_id=3,receipt_id='R-0042',amount=-1)]:
    try:
        with transaction.atomic(): Receipt.objects.bulk_create([Receipt(**values)])
    except IntegrityError: pass
    else: raise AssertionError('database constraint missing')
assert Receipt.objects.count()==2
Receipt.objects.create(owner_id=3,receipt_id='R-0041',amount=50)
assert Receipt.objects.count()==3
namespace['connection'].close()
''', keep_database=True)

    def test_generator_lifetime_rejection(self):
        namespace = load('generator_control')
        producer = namespace['running_total']()
        initial = len(namespace['closed'])
        with self.assertRaises(TypeError): producer.send(125)
        self.assertEqual(len(namespace['closed']), initial)
        self.assertEqual(next(producer), 0)
        self.assertEqual(producer.send(1000), 1000)
        with self.assertRaises(ValueError): producer.send(1001)
        self.assertEqual(len(namespace['closed']), initial + 1)
        with self.assertRaises(StopIteration): next(producer)

if __name__ == '__main__':
    result = unittest.TextTestRunner(verbosity=2).run(unittest.defaultTestLoader.loadTestsFromTestCase(ServiceContracts))
    print(json.dumps({'passed': result.wasSuccessful(), 'suites': result.testsRun, 'oracleComparisons': sum(COUNTS.values()), 'comparisons': COUNTS}))
    raise SystemExit(not result.wasSuccessful())
