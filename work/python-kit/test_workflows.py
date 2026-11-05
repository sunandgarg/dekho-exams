"""Independent small-case comparisons and failure checks for the ninth Python pass."""
import contextlib
import html
import io
import itertools
import json
import pathlib
import random
import re
import sqlite3
import unittest

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


ORACLES = {'stableMergeComparisons': 1800, 'runGroupComparisons': 1800,
           'dependencyOrderComparisons': 1500, 'allPairsComparisons': 450,
           'minimumCutComparisons': 450, 'finiteMaskComparisons': 500}


class WorkflowChecks(unittest.TestCase):
    def test_callable_sentinel_and_byte_view(self):
        pulled = load('callable-iterator-sentinel')
        self.assertEqual(pulled['reads'], 3)
        self.assertEqual(len(pulled['pending']), 0)
        with self.assertRaises(ValueError):
            pulled['pull_receipt']()
        owned = load('bytearray-aliasing')
        self.assertEqual(owned['snapshot'], b'R41:125')
        self.assertEqual(bytes(owned['frame']), b'X41:125!')
        with self.assertRaises(ValueError):
            owned['view'][0]

    def test_cached_state_and_task_lifetimes(self):
        invoice = load('cached-property-invalidation')['Invoice']([20, 30])
        self.assertEqual(invoice.total, 50)
        self.assertEqual(invoice.total, 50)
        self.assertEqual(invoice.computations, 1)
        invoice.replace([20, 40])
        self.assertEqual(invoice.total, 60)
        self.assertEqual(invoice.computations, 2)
        with self.assertRaises(ValueError):
            invoice.replace([True])
        self.assertEqual(invoice.total, 60)
        self.assertEqual(load('async-to-thread-context')['request_label'].get(), 'unset')
        self.assertTrue(callable(load('gather-sibling-lifetime')['delayed_receipt']))

    def test_interview_traces_and_test_fixtures(self):
        parsed = load('try-else-finally-interview')['parse_amount']
        self.assertEqual(parsed('17'), (17, ['parsed', 'cleanup']))
        self.assertEqual(parsed('X'), (None, ['rejected', 'cleanup']))
        bound = load('comprehension-scope-interview')['bound']
        self.assertEqual([callback() for callback in bound], [0, 1, 2])
        self.assertEqual(load('unittest-subtests')['result'].testsRun, 1)
        self.assertTrue(load('asyncio-test-fixture')['result'].wasSuccessful())

    def test_stable_merge_against_decorated_sort(self):
        merge = load('sorted-merge-exercise')['merge_feeds']
        rng = random.Random(20260930)
        for _ in range(ORACLES['stableMergeComparisons']):
            left = sorted(rng.randrange(0, 30) for _ in range(rng.randrange(0, 25)))
            right = sorted(rng.randrange(0, 30) for _ in range(rng.randrange(0, 25)))
            expected = sorted([(value, 'left') for value in left] + [(value, 'right') for value in right],
                              key=lambda pair: (pair[0], pair[1] != 'left'))
            original = (left.copy(), right.copy())
            self.assertEqual(merge(left, right), expected)
            self.assertEqual((left, right), original)
        for bad in ([True], [-1], [1001], [2, 1]):
            with self.assertRaises(ValueError):
                merge(bad, [])

    def test_run_encoding_against_groupby(self):
        encode = load('run-length-exercise')['encode_states']
        rng = random.Random(141)
        for _ in range(ORACLES['runGroupComparisons']):
            states = ''.join(rng.choice('QSR') for _ in range(rng.randrange(0, 80)))
            expected = [(state, sum(1 for _ in run)) for state, run in itertools.groupby(states)]
            self.assertEqual(encode(states), expected)
        for bad in ('Q１', 'Q3', 'Q' * 101, None):
            with self.assertRaises(ValueError):
                encode(bad)

    def test_dependency_order_against_pair_positions(self):
        verify = load('dag-order-exercise')['valid_order']
        rng = random.Random(381)
        for _ in range(ORACLES['dependencyOrderComparisons']):
            nodes = [f'step{index}' for index in range(rng.randrange(1, 9))]
            edges = [(left, right) for left in nodes for right in nodes if left != right and rng.random() < 0.09]
            order = nodes.copy()
            rng.shuffle(order)
            expected = all(order.index(left) < order.index(right) for left, right in edges)
            self.assertEqual(verify(nodes, edges, order), expected)
        self.assertFalse(verify(['a', 'b'], [('a', 'b')], ['a', 'a']))
        self.assertFalse(verify(['a'], [], [[]]))
        with self.assertRaises(ValueError):
            verify(['a', 'a'], [], ['a', 'a'])

    def test_floyd_against_repeated_relaxation(self):
        solve = load('floyd-warshall-paths')['all_pairs']
        rng = random.Random(731)
        for _ in range(ORACLES['allPairsComparisons']):
            size = rng.randrange(2, 8)
            edges = [(start, end, rng.randrange(0, 11)) for start in range(size)
                     for end in range(size) if start != end and rng.random() < 0.3]
            matrix = solve(size, edges)
            for source in range(size):
                cost = [None] * size
                cost[source] = 0
                for _ in range(size - 1):
                    previous = cost.copy()
                    for start, end, weight in edges:
                        if previous[start] is not None:
                            next_cost = previous[start] + weight
                            if cost[end] is None or next_cost < cost[end]:
                                cost[end] = next_cost
                self.assertEqual(matrix[source], cost)
        with self.assertRaises(ValueError):
            solve(2, [(0, 1, -2), (1, 0, 1)])

    def test_maxflow_against_every_source_sink_cut(self):
        solve = load('max-flow-residual')['maximum_flow']
        rng = random.Random(407)
        for _ in range(ORACLES['minimumCutComparisons']):
            size = rng.randrange(2, 7)
            edges = [(start, end, rng.randrange(1, 6)) for start in range(size)
                     for end in range(size) if start != end and rng.random() < 0.22]
            best = None
            middle = list(range(1, size - 1))
            for bits in itertools.product((False, True), repeat=len(middle)):
                left = {0} | {vertex for vertex, selected in zip(middle, bits) if selected}
                cut = sum(capacity for start, end, capacity in edges if start in left and end not in left)
                best = cut if best is None else min(best, cut)
            self.assertEqual(solve(size, edges, 0, size - 1), best)
        with self.assertRaises(ValueError):
            solve(3, [(0, 1, True)], 0, 2)

    def test_finite_masks_and_asof_contract(self):
        numpy = load('numpy-finite-gate')['np']
        rng = random.Random(599)
        for _ in range(ORACLES['finiteMaskComparisons']):
            values = [rng.choice((0.0, 1.0, -1.0, float('nan'), float('inf'), float('-inf')))
                      for _ in range(rng.randrange(0, 20))]
            mask = numpy.isfinite(numpy.array(values)) & (numpy.array(values) >= 0)
            expected = [value in (0.0, 1.0) for value in values]
            self.assertEqual(mask.tolist(), expected)
        asof = load('pandas-asof-joins')['joined']
        self.assertEqual(asof['minute'].tolist(), [10, 20, 30])
        self.assertTrue(asof['state'].isna().iloc[2])

    def test_packaging_web_and_checkpoint_boundaries(self):
        spec = load('version-specifier-check')['accepted']
        self.assertFalse(spec.contains('2.5rc1', prereleases=False))
        self.assertTrue(spec.contains('2.4', prereleases=False))
        plugin = load('entry-point-discovery')
        self.assertEqual(plugin['selected'][0].name, 'validator')
        flask = load('flask-keyset-list')['application']
        with flask.test_client() as client:
            self.assertEqual(client.get('/receipts?after=%EF%BC%91').status_code, 400)
            self.assertEqual(client.get('/receipts?after=43').get_json()['ids'], [])
        with self.assertRaises(sqlite3.ProgrammingError):
            load('sqlite-checkpoint-project')['connection'].execute('SELECT 1')


if __name__ == '__main__':
    unittest.main(verbosity=2)
