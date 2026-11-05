"""Independent oracles and boundary checks for the third Python pass."""
import contextlib
from functools import lru_cache
import io
import itertools
import json
from pathlib import Path
import random
import runpy
import unittest

HERE = Path(__file__).resolve().parent
COUNTS = {}

def load(name):
    with contextlib.redirect_stdout(io.StringIO()):
        return runpy.run_path(str(HERE / (name + '.py')))

def counted(name):
    COUNTS[name] = COUNTS.get(name, 0) + 1

class DepthContracts(unittest.TestCase):
    def test_edit_distance_against_recursive_search(self):
        distance = load('edit_distance')['label_distance']
        @lru_cache(None)
        def oracle(first, second):
            if not first: return len(second)
            if not second: return len(first)
            return min(oracle(first[1:], second) + 1,
                       oracle(first, second[1:]) + 1,
                       oracle(first[1:], second[1:]) + (first[0] != second[0]))
        randomizer = random.Random(71)
        for _ in range(1000):
            first = ''.join(randomizer.choices('ABC', k=randomizer.randrange(7)))
            second = ''.join(randomizer.choices('ABC', k=randomizer.randrange(7)))
            self.assertEqual(distance(first, second), oracle(first, second))
            counted('recursiveEditOracle')
        for first, second in [(None, 'DEL'), ('x' * 65, 'DEL')]:
            with self.assertRaises(ValueError): distance(first, second)

    def test_window_against_every_substring(self):
        span = load('sliding_window')['distinct_span']
        randomizer = random.Random(72)
        for _ in range(1000):
            text = ''.join(randomizer.choices('ABCDE', k=randomizer.randrange(24)))
            expected = max((right - left for left in range(len(text) + 1)
                            for right in range(left, len(text) + 1)
                            if len(set(text[left:right])) == right - left), default=0)
            self.assertEqual(span(text), expected)
            counted('substringWindowOracle')
        for text in [None, '\u00e9', 'x' * 257]:
            with self.assertRaises(ValueError): span(text)

    def test_signed_routes_against_floyd_warshall(self):
        routes = load('bellman_ford')['signed_routes']
        randomizer = random.Random(73)
        for _ in range(500):
            count = randomizer.randrange(1, 7)
            edges = [(start, end, randomizer.randrange(-4, 8))
                     for start in range(count) for end in range(count)
                     if randomizer.random() < .22]
            matrix = [[float('inf')] * count for _ in range(count)]
            for node in range(count): matrix[node][node] = 0
            for start, end, weight in edges: matrix[start][end] = min(matrix[start][end], weight)
            for via in range(count):
                for start in range(count):
                    for end in range(count):
                        matrix[start][end] = min(matrix[start][end], matrix[start][via] + matrix[via][end])
            source = randomizer.randrange(count)
            negative = any(matrix[source][node] < float('inf') and matrix[node][node] < 0 for node in range(count))
            if negative:
                with self.assertRaisesRegex(ValueError, 'reachable negative cycle'): routes(count, edges, source)
            else:
                expected = [None if cost == float('inf') else cost for cost in matrix[source]]
                self.assertEqual(routes(count, edges, source), expected)
            counted('signedAllPairsOracle')
        self.assertEqual(routes(3, [(1, 2, -2), (2, 1, 1)], 0), [0, None, None])
        for count, edges, source in [(True, [], 0), (2, [(0, 1, True)], 0), (2, [(0, 2, 1)], 0)]:
            with self.assertRaises(ValueError): routes(count, edges, source)

    def test_forest_against_exhaustive_subsets(self):
        forest = load('kruskal_forest')['network_forest']
        randomizer = random.Random(74)
        def partitions(count, edges):
            adjacency = [set() for _ in range(count)]
            for first, second, weight in edges:
                adjacency[first].add(second); adjacency[second].add(first)
            remaining = set(range(count)); result = []
            while remaining:
                pending = [next(iter(remaining))]; component = set()
                while pending:
                    node = pending.pop()
                    if node in component: continue
                    component.add(node); pending.extend(adjacency[node] - component)
                remaining -= component; result.append(frozenset(component))
            return set(result)
        for _ in range(250):
            count = randomizer.randrange(1, 6)
            edges = [(first, second, randomizer.randrange(-4, 8))
                     for first in range(count) for second in range(first + 1, count)
                     if randomizer.random() < .65][:8]
            target = partitions(count, edges)
            selected_count = count - len(target)
            candidates = [sum(edge[2] for edge in selected)
                          for selected in itertools.combinations(edges, selected_count)
                          if partitions(count, selected) == target]
            before = edges.copy()
            self.assertEqual(forest(count, edges), (min(candidates), len(target)))
            self.assertEqual(edges, before)
            counted('enumeratedForestOracle')
        self.assertEqual(forest(2, [(0, 0, -100), (0, 1, 4), (0, 1, 2)]), (2, 1))
        with self.assertRaises(ValueError): forest(2, [(0, True, 4)])

    def test_tree_ranges_against_direct_sums(self):
        tree_class = load('segment_tree')['LedgerSums']
        randomizer = random.Random(75)
        for _ in range(150):
            amounts = [randomizer.randrange(-100, 101) for _ in range(randomizer.randrange(1, 40))]
            original = amounts.copy(); owned = amounts.copy(); tree = tree_class(amounts)
            for _ in range(30):
                position = randomizer.randrange(len(owned))
                amount = randomizer.randrange(-100, 101)
                tree.replace(position, amount); owned[position] = amount
                left = randomizer.randrange(len(owned) + 1)
                right = randomizer.randrange(left, len(owned) + 1)
                self.assertEqual(tree.total(left, right), sum(owned[left:right]))
                counted('directRangeSumOracle')
            before = tree.total(0, len(owned))
            for position, amount in [(-1, 2), (len(owned), 2), (True, 2), (0, True)]:
                with self.assertRaises(ValueError): tree.replace(position, amount)
            self.assertEqual(tree.total(0, len(owned)), before)
            self.assertEqual(amounts, original)
        with self.assertRaises(ValueError): tree_class([])

    def test_bst_deletion_against_owned_key_set(self):
        namespace = load('bst_deletion')
        build, delete, ordered = (namespace[name] for name in ('receipt_tree', 'delete_receipt', 'ordered_receipts'))
        randomizer = random.Random(76)
        for _ in range(200):
            keys = randomizer.sample(range(100), randomizer.randrange(25))
            root = build(keys); expected = set(keys)
            removals = keys.copy(); randomizer.shuffle(removals)
            removals = [999] + removals + [999]
            for key in removals:
                root = delete(root, key); expected.discard(key)
                self.assertEqual(ordered(root), sorted(expected))
                counted('bstKeySetOracle')
        for keys in [[1, 1], [True], list(range(65))]:
            with self.assertRaises(ValueError): build(keys)

    def test_chunked_totals_against_python_accumulator(self):
        totals = load('chunked_aggregation')['region_totals']
        randomizer = random.Random(77)
        for _ in range(200):
            rows = [(randomizer.choice(['DEL', 'BOM']), randomizer.randrange(1000))
                    for _ in range(randomizer.randrange(1, 20))]
            expected = {}
            for region, amount in rows: expected[region] = expected.get(region, 0) + amount
            text = 'region,amount\n' + ''.join(f'{region},{amount}\n' for region, amount in rows)
            self.assertEqual(totals(text), expected)
            counted('chunkAccumulatorOracle')
        for text in ['region,amount\nDEL,1\nBOM,2\nUNKNOWN,3\n', 'region,amount\nDEL,1\nBOM,2\nDEL,\n',
                     'region,amount,token\nDEL,1,x\n', 'region,amount\nDEL,1.5\n']:
            with self.assertRaises((ValueError, TypeError)): totals(text)

    def test_configuration_does_not_mutate_its_sources(self):
        resolve = load('configuration_precedence')['resolve_settings']
        defaults = {'region': 'DEL', 'workers': 2}
        file_settings = {'workers': 3}; overrides = {'region': 'BOM'}
        self.assertEqual(resolve(defaults, file_settings, overrides), {'region': 'BOM', 'workers': 3})
        self.assertEqual(defaults, {'region': 'DEL', 'workers': 2})
        self.assertEqual(file_settings, {'workers': 3}); self.assertEqual(overrides, {'region': 'BOM'})
        for changed in [{'workers': True}, {'workers': 9}, {'workers': None}, {'secret': 'fixture'}]:
            with self.assertRaises(ValueError): resolve(defaults, {}, changed)
        parse = load('toml_configuration')['dispatch_config']
        for text in ['region="DEL"\nworkers=true', 'region="DEL"\nworkers=0', 'region="DEL"\nworkers=2\nextra=1']:
            with self.assertRaises(ValueError): parse(text)

    def test_replay_conflicts_preserve_the_stored_result(self):
        namespace = load('idempotent_jobs')
        database = namespace['open_job_ledger']()
        accept = namespace['accept_job']
        try:
            for number in range(20):
                key = f'J-{number:04d}'; amount = number * 125
                self.assertEqual(accept(database, key, amount), (amount + 25, True))
                self.assertEqual(accept(database, key, amount), (amount + 25, False))
                with self.assertRaises(ValueError): accept(database, key, amount + 1)
                self.assertEqual(database.execute('SELECT amount,result FROM jobs WHERE job_id=?', (key,)).fetchone(), (amount, amount + 25))
            before = database.execute('SELECT count(*) FROM jobs').fetchone()[0]
            for key, amount in [('J-0000', True), ('J-００４１', 2), ('J-0020', -1), ('J-0020', 1000001)]:
                with self.assertRaises(ValueError): accept(database, key, amount)
            self.assertEqual(database.execute('SELECT count(*) FROM jobs').fetchone()[0], before)
        finally: database.close()

if __name__ == '__main__':
    result = unittest.TextTestRunner(verbosity=2).run(unittest.defaultTestLoader.loadTestsFromTestCase(DepthContracts))
    report = {'passed': result.wasSuccessful(), 'suites': result.testsRun,
              'oracleComparisons': sum(COUNTS.values()), 'comparisons': COUNTS,
              'boundaryCases': ['input budgets', 'boolean rejection', 'unreachable negative cycle',
                                'parallel edges and loops', 'invalid replacement preserves state',
                                'later chunk rejection', 'source mappings unchanged', 'conflicting job replay']}
    print(json.dumps(report, sort_keys=True))
    raise SystemExit(0 if result.wasSuccessful() else 1)
