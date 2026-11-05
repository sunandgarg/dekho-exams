"""Independent small-case oracles and rejected-state checks for the seventh pass."""
import contextlib
import html
import io
import itertools
import json
import math
import pathlib
import random
import re
import socket
import sqlite3
import tempfile
import unittest
from datetime import datetime, timezone
from fractions import Fraction
from zoneinfo import ZoneInfo

ROOT = pathlib.Path(__file__).resolve().parents[2]
FIXTURES = ROOT / 'src/data/fixtures.json'
PROGRAMS = None
if FIXTURES.exists():
    PROGRAMS = {entry['path'].split('/')[-1]: html.unescape(re.search(
        r'<code class="language-python">([\s\S]*?)</code>', entry['body'])[1])
        for entry in json.loads(FIXTURES.read_text())
        if entry['type'] == 'article' and entry['path'].startswith('python/')}


def load(slug):
    source = PROGRAMS[slug] if PROGRAMS else pathlib.Path(__file__).with_name(slug.replace('-', '_') + '.py').read_text()
    namespace = {'__name__': '__main__'}
    with contextlib.redirect_stdout(io.StringIO()):
        exec(compile(source, slug, 'exec'), namespace)
    return namespace


ORACLES = {'radixSetTransitions': 10000, 'maximumMatchEnumeration': 500,
           'weightedSubsetEnumeration': 500, 'partialFrameReads': 1500,
           'exactCovariance': 500, 'renewalStateTransitions': 1000,
           'ownedHashComparisons': 500, 'matrixAxisComparisons': 200}


class LifetimeChecks(unittest.TestCase):
    def test_transferred_cleanup(self):
        acquire = load('exitstack-transfer')['acquire_bundle']
        events = []
        owner = acquire(events)
        self.assertEqual(events, [])
        owner.close(); owner.close()
        self.assertEqual(events, ['index released', 'stream released'])
        events = []
        with self.assertRaises(ValueError):
            acquire(events, fail=True)
        self.assertEqual(events, ['index released', 'stream released'])

    def test_group_partition_identity(self):
        namespace = load('exception-group-partition')
        original, matched, residual = (namespace[name] for name in ('batch', 'matched', 'residual'))
        self.assertIs(matched.exceptions[0], original.exceptions[0])
        self.assertIs(matched.exceptions[1].exceptions[0], original.exceptions[1].exceptions[1])
        self.assertIs(residual.exceptions[0].exceptions[0], original.exceptions[1].exceptions[0])
        self.assertEqual(len(original.exceptions), 2)

    def test_enum_and_fraction_contracts(self):
        status = load('enum-alias-contract')['ReceiptStatus']
        self.assertIs(status.NEW, status.PENDING)
        self.assertEqual(len(list(status)), 2)
        self.assertEqual(len(status.__members__), 3)
        allocate = load('fraction-ratios')['allocation']
        self.assertEqual(allocate(125, 3, 10), Fraction(75, 2))
        for fields in ((True, 1, 2), (1, 2, 1), (1, 1, 0), (100001, 1, 2), (1, 1, 1001)):
            with self.assertRaises(ValueError):
                allocate(*fields)

    def test_named_zone_candidates(self):
        classify = load('zone-local-classification')['local_candidates']
        zone = ZoneInfo('America/New_York')
        self.assertEqual(classify(datetime(2024, 3, 10, 2, 30), zone), [])
        self.assertEqual(classify(datetime(2024, 11, 3, 1, 30), zone), [
            datetime(2024, 11, 3, 5, 30, tzinfo=timezone.utc),
            datetime(2024, 11, 3, 6, 30, tzinfo=timezone.utc)])
        self.assertEqual(classify(datetime(2024, 2, 1, 12), zone), [datetime(2024, 2, 1, 17, tzinfo=timezone.utc)])
        with self.assertRaises(ValueError):
            classify(datetime(2024, 2, 1, 12, tzinfo=timezone.utc), zone)

    def test_dispatch_and_rich_ordering(self):
        dispatch = load('singledispatch-contract')['encoded_amount']
        class ReceiptInteger(int):
            pass
        for value in (True, ReceiptInteger(1), '１２', 1001, None):
            with self.assertRaises(ValueError):
                dispatch(value)
        self.assertEqual(dispatch('0001'), 'minor:1')
        rank = load('ordering-protocol')['ReceiptRank']
        self.assertTrue(rank(2) <= rank(2)); self.assertTrue(rank(4) > rank(2))
        self.assertIs(rank(2).__eq__(2), NotImplemented)
        with self.assertRaises(TypeError):
            rank(2) > 2
        with self.assertRaises(TypeError):
            hash(rank(2))

    def test_savepoint_outer_rollback(self):
        with sqlite3.connect(':memory:', isolation_level=None) as connection:
            connection.execute('CREATE TABLE receipt(id INTEGER PRIMARY KEY)')
            connection.execute('BEGIN')
            connection.execute('INSERT INTO receipt VALUES (1)')
            connection.execute('SAVEPOINT owned_step')
            connection.execute('INSERT INTO receipt VALUES (2)')
            connection.execute('ROLLBACK TO owned_step')
            self.assertTrue(connection.in_transaction)
            connection.execute('INSERT INTO receipt VALUES (3)')
            connection.execute('RELEASE owned_step')
            self.assertEqual(connection.execute('SELECT COUNT(*) FROM receipt').fetchone()[0], 2)
            connection.execute('ROLLBACK')
            self.assertEqual(connection.execute('SELECT COUNT(*) FROM receipt').fetchone()[0], 0)
        connection.close()

    def test_spool_and_partial_frames(self):
        spool = load('spooled-file-budgets')['stage_payload']
        for size in (0, 8, 9, 32):
            self.assertEqual(spool(b'x' * size), b'x' * size)
        with self.assertRaises(ValueError):
            spool(b'x' * 33)
        read = load('socket-frame-reading')['read_frame']
        rng = random.Random(742)
        class FragmentStream:
            def __init__(self, wire):
                self.wire = wire
                self.offset = 0
            def recv(self, count):
                size = min(count, rng.randint(1, 3))
                chunk = self.wire[self.offset:self.offset + size]
                self.offset += len(chunk)
                return chunk
        for _ in range(1500):
            payload = rng.randbytes(rng.randint(0, 32))
            stream = FragmentStream(len(payload).to_bytes(2, 'big') + payload + b'next')
            self.assertEqual(read(stream), payload)
            self.assertEqual(stream.wire[stream.offset:], b'next')
        for wire in (b'', b'\x00', b'\x00\x02x'):
            with self.assertRaises(EOFError):
                read(FragmentStream(wire))
        stream = FragmentStream(b'\x00\x21trailing')
        with self.assertRaises(ValueError):
            read(stream)
        self.assertEqual(stream.offset, 2)
        sender, receiver = socket.socketpair()
        with sender, receiver:
            receiver.settimeout(1)
            sender.sendall(b'\x00\x01a\x00\x01b')
            self.assertEqual(read(receiver), b'a')
            self.assertEqual(read(receiver), b'b')

    def test_radix_set_oracle_and_invariants(self):
        radix = load('radix-trie-updates')['RadixSet']
        rng = random.Random(743)
        keys = [''.join(chars) for size in range(1, 4) for chars in itertools.product('abc', repeat=size)]
        index, reference = radix(), set()
        def inspect(node, root=False):
            terminal, children = node
            if not root:
                self.assertTrue(terminal or len(children) >= 2)
            firsts = [label[0] for label in children]
            self.assertEqual(len(firsts), len(set(firsts)))
            for label, child in children.items():
                self.assertTrue(label)
                inspect(child)
        for _ in range(10000):
            key = rng.choice(keys)
            if rng.randrange(2):
                self.assertEqual(index.add(key), key not in reference)
                reference.add(key)
            else:
                self.assertEqual(index.discard(key), key in reference)
                reference.discard(key)
            self.assertEqual(index.size, len(reference))
            self.assertEqual({key for key in keys if index.contains(key)}, reference)
            inspect(index.root, True)
        before = {key for key in keys if index.contains(key)}
        for invalid in ('', 'A', 'x'*17, True):
            with self.assertRaises(ValueError):
                index.add(invalid)
        self.assertEqual({key for key in keys if index.contains(key)}, before)
        capacity = radix()
        for number in range(64):
            capacity.add('k' + chr(97 + number // 26) + chr(97 + number % 26))
        self.assertFalse(capacity.add('kaa'))
        with self.assertRaises(ValueError):
            capacity.add('new')
        self.assertEqual(capacity.size, 64)

    def test_matching_exhaustive_oracle(self):
        solve = load('bipartite-matching')['maximum_assignment']
        feasible = load('matching-exercise')['valid_assignment']
        rng = random.Random(744)
        for _ in range(500):
            workers, slots = rng.randint(0, 5), rng.randint(0, 5)
            graph = [[slot for slot in range(slots) if rng.randrange(2)] for _ in range(workers)]
            optimum = 0
            for choices in itertools.product(*[[-1] + row for row in graph]):
                selected = [slot for slot in choices if slot != -1]
                if len(selected) == len(set(selected)):
                    optimum = max(optimum, len(selected))
            pairs = solve(graph, slots)
            self.assertTrue(feasible(graph, slots, pairs))
            self.assertEqual(len(pairs), optimum)
        for graph, slots in (([[True]], 1), ([[0, 0]], 1), ([[1]], 1), ([[]]*9, 1)):
            with self.assertRaises(ValueError):
                solve(graph, slots)
        self.assertFalse(feasible([[0],[0]],1,[(0,0),(1,0)]))
        self.assertTrue(feasible([[0]],1,[]))

    def test_weighted_subsets_and_reconstruction(self):
        solve = load('weighted-intervals')['best_schedule']
        rng = random.Random(745)
        for _ in range(500):
            jobs = [(start, start + rng.randint(1, 4), rng.randint(0, 9))
                    for start in [rng.randint(0, 8) for _ in range(rng.randint(0, 9))]]
            optimum = 0
            for bits in range(1 << len(jobs)):
                selected = [job for index, job in enumerate(jobs) if bits & (1 << index)]
                ordered = sorted(selected)
                if all(left[1] <= right[0] for left, right in zip(ordered, ordered[1:])):
                    optimum = max(optimum, sum(job[2] for job in selected))
            original = jobs.copy()
            total, chosen = solve(jobs)
            self.assertEqual(total, optimum)
            self.assertEqual(sum(jobs[index][2] for index in chosen), total)
            self.assertEqual(len(chosen), len(set(chosen)))
            selected = sorted(jobs[index] for index in chosen)
            self.assertTrue(all(left[1] <= right[0] for left, right in zip(selected, selected[1:])))
            self.assertEqual(jobs, original)
        for jobs in ([(True,2,1)], [(1,1,2)], [(0,2,-1)], [(0,1,1)]*17):
            with self.assertRaises(ValueError):
                solve(jobs)

    def test_exact_covariance_and_matrix_axes(self):
        covariance = load('covariance-policy')['paired_covariance']
        costs = load('numpy-shape-contract')['warehouse_costs']
        rng = random.Random(746)
        for _ in range(500):
            count = rng.randint(2, 12)
            left, right = [[rng.randint(-100,100) for _ in range(count)] for _ in range(2)]
            exact_centered = Fraction(sum(x*y for x,y in zip(left,right))) - Fraction(sum(left)*sum(right),count)
            for sample in (True, False):
                expected = float(exact_centered / (count - int(sample)))
                self.assertTrue(math.isclose(covariance(left,right,sample=sample),expected,rel_tol=1e-12,abs_tol=1e-10))
        for _ in range(200):
            rows, columns = rng.randint(1,8), rng.randint(1,8)
            matrix = [[rng.randint(0,9) for _ in range(columns)] for _ in range(rows)]
            prices = [rng.randint(0,9) for _ in range(columns)]
            self.assertEqual(costs(matrix,prices).tolist(), [sum(x*p for x,p in zip(row,prices)) for row in matrix])
        for left,right in (([1,2],[2]), ([True,2],[3,4]), ([1,float('inf')],[2,3]), ([1,10**1000],[2,3])):
            with self.assertRaises(ValueError):
                covariance(left,right)
        with self.assertRaises(ValueError):
            costs([[1,2],[3,4]],[[1],[2]])

    def test_renewal_state_and_writer_contention(self):
        renew = load('lease-renewal-project')['renew']
        rng = random.Random(747)
        with tempfile.TemporaryDirectory() as directory:
            path = pathlib.Path(directory)/'claims.db'
            first = sqlite3.connect(path,isolation_level=None,timeout=0)
            second = sqlite3.connect(path,isolation_level=None,timeout=0)
            try:
                first.execute('CREATE TABLE job(id INTEGER PRIMARY KEY, token TEXT NOT NULL, expiry INTEGER NOT NULL)')
                first.execute("INSERT INTO job VALUES (41,'owned',10)")
                for _ in range(1000):
                    expiry = rng.randint(1,100)
                    first.execute('UPDATE job SET expiry=?',(expiry,))
                    now = rng.randint(0,100)
                    extension = now + rng.randint(1,10)
                    token = rng.choice(['owned','stale'])
                    expected = token == 'owned' and expiry > now and extension > expiry
                    self.assertEqual(renew(second,41,token,now,extension),expected)
                    self.assertEqual(first.execute('SELECT expiry FROM job').fetchone()[0],extension if expected else expiry)
                first.execute('BEGIN IMMEDIATE')
                with self.assertRaises(sqlite3.OperationalError):
                    renew(second,41,'owned',1,11)
                first.execute('ROLLBACK')
                before = first.execute('SELECT expiry FROM job').fetchone()[0]
                for fields in ((True,'owned',1,5),(41,'owned',True,5),(41,'owned',1,12),(41,'',1,5)):
                    with self.assertRaises(ValueError):
                        renew(second,*fields)
                self.assertEqual(first.execute('SELECT expiry FROM job').fetchone()[0],before)
            finally:
                second.close();first.close()

    def test_owned_hashes_and_url_rejection(self):
        import hashlib
        verify = load('artifact-digest-check')['artifact_matches']
        target = load('url-target-policy')['accepted_target']
        rng = random.Random(748)
        for _ in range(500):
            payload = rng.randbytes(rng.randint(0,4096))
            expected = hashlib.sha256(payload).hexdigest()
            self.assertTrue(verify(payload,expected))
            if len(payload) < 4096:
                self.assertFalse(verify(payload+b'x',expected))
            else:
                self.assertFalse(verify(payload[:-1],expected))
        with self.assertRaises(ValueError):
            verify(b'x'*4097,'0'*64)
        for text in ('https://learn.aitrove.in:99999/receipts','https://learn.aitrove.in/receipts?read=1',
                     'https://learn.aitrove.in/receipts#private','https://learn.aitrove.in/%72eceipts',
                     'https://user@learn.aitrove.in/receipts',' https://learn.aitrove.in/receipts',
                     'https://learn.aitrove.in/receipts\n','http://learn.aitrove.in/receipts'):
            with self.assertRaises(ValueError):
                target(text)
        self.assertEqual(target('https://LEARN.AITROVE.IN/receipts'),'https://learn.aitrove.in/receipts')

    def test_conditional_http_representation(self):
        application = load('flask-conditional-response')['application']
        with application.test_client() as client:
            response = client.get('/receipts/41')
            validator = response.headers['ETag']
            response = client.get('/receipts/41',headers={'If-None-Match':validator})
            self.assertEqual(response.status_code,304);self.assertEqual(response.data,b'')
            self.assertEqual(response.headers['ETag'],validator)
            self.assertEqual(client.get('/receipts/41',headers={'If-None-Match':'W/'+validator}).status_code,304)
            head = client.head('/receipts/41')
            self.assertEqual(head.status_code,200);self.assertEqual(head.data,b'')


if __name__ == '__main__':
    result = unittest.TextTestRunner(verbosity=2).run(unittest.defaultTestLoader.loadTestsFromTestCase(LifetimeChecks))
    print(json.dumps({'passed':result.wasSuccessful(),'suites':result.testsRun,
                      'oracleComparisons':sum(ORACLES.values()),'oracles':ORACLES}))
    raise SystemExit(not result.wasSuccessful())
