"""Independent contract checks for the eleventh Python curriculum pass."""
import contextlib
import html
import io
import json
import pathlib
import random
import re
import sqlite3
import unittest
from fractions import Fraction
from heapq import heappop, heappush

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

ORACLES = {'window': 800, 'zeroOneGraph': 500, 'median': 800, 'capacity': 500}

class IntegrityChecks(unittest.TestCase):
    def test_decode_and_header_boundaries(self):
        decode = load('strict-utf8-import')['decode_receipt']
        self.assertEqual(decode('Café R41'.encode()), 'Café R41')
        with self.assertRaises(UnicodeDecodeError):
            decode(b'\xc3(')
        with self.assertRaises(ValueError):
            decode(b'\xef\xbb\xbfR41')
        document = load('json-duplicate-keys')['receipt_document']
        with self.assertRaises(ValueError):
            document('{"outer":{"id":1,"id":2}}')
        self.assertEqual(document('{"receipt":{"id":"R41"}}')['receipt']['id'], 'R41')
        rows = load('csv-duplicate-headers')['receipt_rows']
        with self.assertRaises(ValueError):
            rows('id,id\nR41,R42\n')
        with self.assertRaises(ValueError):
            rows('id,minor\nR41\n')

    def test_exact_amount_and_alias_ownership(self):
        minor = load('decimal-inexact-trap')['minor_units']
        self.assertEqual(minor('12.500'), 1250)
        with self.assertRaises(ValueError):
            minor('12.501')
        with self.assertRaises(ValueError):
            minor('NaN')
        replace = load('dataclass-replace-alias')
        self.assertIs(replace['shared'].receipt_ids, replace['original'].receipt_ids)
        self.assertIsNot(replace['isolated'].receipt_ids, replace['original'].receipt_ids)
        union = load('dict-union-shallow')
        self.assertIs(union['configured']['depots'], union['defaults']['depots'])
        self.assertIsNot(union['owned']['depots'], union['defaults']['depots'])

    def test_storage_constraints_and_staged_import(self):
        store = load('sqlite-conflict-update')['store']
        with self.assertRaises(sqlite3.ProgrammingError):
            store('R42', 50)
        project = load('validated-jsonl-ledger-project')['import_batch']
        connection = sqlite3.connect(':memory:')
        connection.execute('CREATE TABLE receipt(id TEXT PRIMARY KEY, minor INTEGER NOT NULL)')
        project(connection, '{"id":"R41","minor":125}')
        with self.assertRaises(sqlite3.IntegrityError):
            project(connection, '{"id":"R42","minor":75}\n{"id":"R41","minor":0}')
        self.assertEqual(connection.execute('SELECT id FROM receipt ORDER BY id').fetchall(), [('R41',)])
        with self.assertRaises(ValueError):
            project(connection, '{"id":"R43","minor":75,"minor":0}')
        connection.close()

    def test_window_against_naive_max(self):
        solve = load('monotonic-window-maximum')['window_peaks']
        rng = random.Random(111)
        for _ in range(ORACLES['window']):
            samples = [rng.randrange(-20, 21) for _ in range(rng.randrange(1, 40))]
            width = rng.randrange(1, len(samples) + 1)
            expected = [max(samples[index:index + width]) for index in range(len(samples) - width + 1)]
            self.assertEqual(solve(samples, width), expected)

    def test_zero_one_against_dijkstra(self):
        solve = load('zero-one-bfs')['transfer_cost']
        rng = random.Random(222)
        for _ in range(ORACLES['zeroOneGraph']):
            count = rng.randrange(1, 15)
            graph = {node: [] for node in range(count)}
            for node in graph:
                graph[node] = [(other, rng.randrange(2)) for other in graph if other != node and rng.random() < .2]
            goal = rng.randrange(count)
            costs, queue = {0: 0}, [(0, 0)]
            while queue:
                cost, node = heappop(queue)
                if cost != costs[node]:
                    continue
                for other, weight in graph[node]:
                    next_cost = cost + weight
                    if next_cost < costs.get(other, float('inf')):
                        costs[other] = next_cost
                        heappush(queue, (next_cost, other))
            self.assertEqual(solve(graph, 0, goal), costs.get(goal))
        with self.assertRaises(ValueError):
            solve({'A': [('B', 2)], 'B': []}, 'A', 'B')

    def test_running_median_against_sorted_prefixes(self):
        solve = load('running-median-heaps')['running_medians']
        rng = random.Random(333)
        for _ in range(ORACLES['median']):
            values = [rng.randrange(-100, 101) for _ in range(rng.randrange(0, 35))]
            expected = []
            for end in range(1, len(values) + 1):
                ordered = sorted(values[:end])
                expected.append(Fraction(ordered[(end - 1) // 2] + ordered[end // 2], 2))
            self.assertEqual(solve(values), expected)

    def test_capacity_against_linear_search(self):
        solve = load('capacity-binary-search')['minimum_daily_capacity']
        rng = random.Random(444)
        for _ in range(ORACLES['capacity']):
            weights = [rng.randrange(1, 15) for _ in range(rng.randrange(1, 15))]
            days = rng.randrange(1, len(weights) + 1)
            expected = None
            for capacity in range(max(weights), sum(weights) + 1):
                used, current_load = 1, 0
                for weight in weights:
                    if current_load + weight > capacity:
                        used += 1
                        current_load = 0
                    current_load += weight
                if used <= days:
                    expected = capacity
                    break
            self.assertEqual(solve(weights, days), expected)

if __name__ == '__main__':
    unittest.main(verbosity=2)
