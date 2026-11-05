"""Independent small-case checks for the tenth Python curriculum pass."""
import contextlib
import html
import io
import json
import pathlib
import random
import re
import sqlite3
import unittest
from collections import deque

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


ORACLES = {'stableTopK': 1000, 'intervalCoverage': 1000, 'sortedFeedMerge': 500,
           'gridShortestPaths': 500, 'fenwickTransitions': 1000}


class BoundaryChecks(unittest.TestCase):
    def test_pairing_aliases_and_buffered_reader(self):
        pair = load('zip-strict-pairing')['pair_receipts']
        self.assertEqual(pair(['R41'], [125]), [('R41', 125)])
        with self.assertRaises(ValueError):
            pair(['R41', 'R42'], [125])
        alias = load('setdefault-aliasing')
        self.assertIs(alias['same_list'], alias['route_receipts'])
        buffered = load('tee-buffer-lifetime')
        self.assertEqual(buffered['source_reads'], ['R41', 'R42', 'R43'])
        self.assertEqual(list(buffered['fast']), [])

    def test_expired_timeout_and_bool_key(self):
        import asyncio
        timeout = load('async-timeout-boundary')['wait_for_receipt']
        self.assertEqual(asyncio.run(timeout()), 'lookup timed out')
        mapping = load('bool-int-key-interview')['access']
        self.assertEqual(len(mapping), 1)
        self.assertEqual(mapping[1], 'approve')

    def test_stable_top_k_against_position_order(self):
        select = load('stable-top-k-exercise')['top_receipts']
        rng = random.Random(101)
        for _ in range(ORACLES['stableTopK']):
            records = [(f'R{index:03}', rng.randrange(0, 10)) for index in range(rng.randrange(0, 35))]
            count = rng.randrange(0, len(records) + 1)
            expected = [record[0] for index, record in sorted(enumerate(records), key=lambda pair: (-pair[1][1], pair[0]))[:count]]
            original = records.copy()
            self.assertEqual(select(records, count), expected)
            self.assertEqual(records, original)
        with self.assertRaises(ValueError):
            select([('R41', 8)], True)

    def test_merged_intervals_against_integer_coverage(self):
        merge = load('merge-half-open-exercise')['merge_reservations']
        rng = random.Random(202)
        for _ in range(ORACLES['intervalCoverage']):
            ranges = [(start, start + rng.randrange(1, 10)) for start in
                      (rng.randrange(0, 30) for _ in range(rng.randrange(0, 30)))]
            expected = {point for start, end in ranges for point in range(start, end)}
            result = merge(ranges)
            actual = {point for start, end in result for point in range(start, end)}
            self.assertEqual(actual, expected)
            self.assertTrue(all(left[1] <= right[0] for left, right in zip(result, result[1:])))
        self.assertEqual(merge([(0, 5), (5, 7)]), [(0, 5), (5, 7)])

    def test_heap_merge_against_global_sort(self):
        merge = load('heap-merge-feeds')['merged_events']
        rng = random.Random(303)
        for _ in range(ORACLES['sortedFeedMerge']):
            feeds = [[(value, f'R{feed_index}-{index}') for index, value in enumerate(sorted(
                rng.randrange(0, 100) for _ in range(rng.randrange(0, 15))))]
                for feed_index in range(rng.randrange(1, 5))]
            self.assertEqual([row[0] for row in merge(*feeds)], sorted(row[0] for feed in feeds for row in feed))
        with self.assertRaises(ValueError):
            merge([(2, 'R42'), (1, 'R41')])

    def test_storage_data_and_conditional_write(self):
        foreign = load('sqlite-foreign-key-boundary')
        with self.assertRaises(sqlite3.ProgrammingError):
            foreign['connection'].execute('SELECT 1')
        joined = load('pandas-join-cardinality')['joined']
        self.assertEqual(joined['receipt_id'].tolist(), [41, 42])
        grouped = load('pandas-groupby-missing-key')['totals']
        self.assertEqual(int(grouped.sum()), 250)
        flask = load('flask-if-match-write')['application']
        with flask.test_client() as client:
            self.assertEqual(client.put('/receipt', json={'minor': 180}, headers={'If-Match': '"1"'}).status_code, 412)
            self.assertEqual(client.get('/receipt').get_json()['minor'], 150)
        backup = load('sqlite-backup-project')
        with self.assertRaises(sqlite3.ProgrammingError):
            backup['destination'].execute('SELECT 1')

    def test_async_await_contract(self):
        mock = load('asyncmock-await-contract')
        self.assertTrue(callable(mock['accept_receipt']))

    def test_a_star_against_breadth_first_search(self):
        solve = load('a-star-grid')['grid_cost']
        rng = random.Random(404)
        for _ in range(ORACLES['gridShortestPaths']):
            width, height = rng.randrange(2, 8), rng.randrange(2, 8)
            start, goal = (0, 0), (width - 1, height - 1)
            blocked = {(x, y) for x in range(width) for y in range(height)
                       if (x, y) not in (start, goal) and rng.random() < 0.25}
            queue = deque([(start, 0)])
            seen = {start}
            expected = None
            while queue:
                cell, distance = queue.popleft()
                if cell == goal:
                    expected = distance
                    break
                for dx, dy in ((1, 0), (-1, 0), (0, 1), (0, -1)):
                    neighbor = (cell[0] + dx, cell[1] + dy)
                    if 0 <= neighbor[0] < width and 0 <= neighbor[1] < height and neighbor not in blocked and neighbor not in seen:
                        seen.add(neighbor)
                        queue.append((neighbor, distance + 1))
            self.assertEqual(solve(width, height, blocked, start, goal), expected)
        with self.assertRaises(ValueError):
            solve(2, 2, {(0, 0)}, (0, 0), (1, 1))

    def test_fenwick_against_direct_prefix(self):
        ledger_type = load('fenwick-prefix-sums')['PrefixLedger']
        rng = random.Random(505)
        values = [rng.randrange(0, 100) for _ in range(30)]
        ledger = ledger_type(values.copy())
        for _ in range(ORACLES['fenwickTransitions']):
            index = rng.randrange(len(values))
            change = rng.randrange(-5, 6)
            ledger.add(index, change)
            values[index] += change
            end = rng.randrange(len(values) + 1)
            self.assertEqual(ledger.prefix(end), sum(values[:end]))
        with self.assertRaises(ValueError):
            ledger.prefix(True)


if __name__ == '__main__':
    unittest.main(verbosity=2)
