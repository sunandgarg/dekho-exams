"""Independent small-input oracles and application rejection checks for pass two."""
import contextlib
import io
import itertools
import json
from pathlib import Path
import random
import runpy
import sqlite3
import tempfile
import unittest
from unittest.mock import patch

HERE = Path(__file__).resolve().parent
COUNTS = {}

def load(name):
    with contextlib.redirect_stdout(io.StringIO()):
        return runpy.run_path(str(HERE / (name + '.py')))

def counted(name):
    COUNTS[name] = COUNTS.get(name, 0) + 1

class ExpansionContracts(unittest.TestCase):
    def test_merge_against_stable_builtin(self):
        sort = load('merge_sort')['sort_receipts']
        randomizer = random.Random(41)
        for _ in range(1000):
            rows = [(randomizer.randrange(-5, 6), 'R' + str(index)) for index in range(randomizer.randrange(25))]
            before = rows.copy()
            self.assertEqual(sort(rows), sorted(rows, key=lambda row: row[0]))
            self.assertEqual(rows, before)
            counted('stableSort')
        for rows in [[(True, 'R41')], [(1, 41)], [(1, 'R41')] * 129]:
            with self.assertRaises(ValueError): sort(rows)

    def test_weighted_routes_against_all_pairs(self):
        routes = load('dijkstra')['route_costs']
        randomizer = random.Random(42)
        for _ in range(250):
            count = randomizer.randrange(1, 8)
            graph = {node: [(target, randomizer.randrange(10)) for target in range(count) if randomizer.random() < .25] for node in range(count)}
            matrix = [[float('inf')] * count for _ in range(count)]
            for node, edges in graph.items():
                matrix[node][node] = 0
                for target, cost in edges: matrix[node][target] = min(matrix[node][target], cost)
            for via in range(count):
                for start in range(count):
                    for end in range(count):
                        matrix[start][end] = min(matrix[start][end], matrix[start][via] + matrix[via][end])
            source = randomizer.randrange(count)
            expected = {node: None if matrix[source][node] == float('inf') else matrix[source][node] for node in range(count)}
            self.assertEqual(routes(graph, source), expected)
            counted('weightedAllPairs')
        for graph, source in [({0: [(1, -1)], 1: []}, 0), ({0: [(1, True)], 1: []}, 0), ({0: [(2, 1)]}, 0), ({0: []}, True)]:
            with self.assertRaises(ValueError): routes(graph, source)

    def test_dependency_order_against_enumerated_orders(self):
        order = load('topological_sort')['dependency_order']
        randomizer = random.Random(43)
        nodes = ['archive', 'import', 'publish', 'validate']
        for _ in range(150):
            graph = {node: [target for target in nodes if target != node and randomizer.random() < .25] for node in nodes}
            valid = [candidate for candidate in itertools.permutations(nodes)
                     if all(candidate.index(node) < candidate.index(target) for node, edges in graph.items() for target in edges)]
            if valid: self.assertEqual(tuple(order(graph)), min(valid))
            else:
                with self.assertRaises(ValueError): order(graph)
            counted('dependencyPermutations')
        with self.assertRaises(ValueError): order({'import': ['missing']})
        with self.assertRaises(ValueError): order({'import': ['publish', 'publish'], 'publish': []})

    def test_union_groups_against_graph_reachability(self):
        Groups = load('union_find')['ReceiptGroups']
        groups, graph = Groups(20), {node: set() for node in range(20)}
        randomizer = random.Random(44)
        def reachable(start):
            seen, pending = set(), [start]
            while pending:
                node = pending.pop()
                if node not in seen:
                    seen.add(node); pending.extend(graph[node] - seen)
            return seen
        for _ in range(300):
            first, second = randomizer.randrange(20), randomizer.randrange(20)
            previously_joined = second in reachable(first)
            self.assertEqual(groups.union(first, second), not previously_joined)
            graph[first].add(second); graph[second].add(first)
            for member in range(20):
                self.assertEqual(groups.find(member) == groups.find(first), member in reachable(first))
            counted('unionTransitions')
        with self.assertRaises(ValueError): groups.find(True)
        with self.assertRaises(ValueError): groups.find(20)

    def test_marker_search_against_repeated_builtin_find(self):
        positions = load('kmp_search')['marker_positions']
        randomizer = random.Random(45)
        for _ in range(1000):
            text = ''.join(randomizer.choice('abc') for _ in range(randomizer.randrange(40)))
            marker = ''.join(randomizer.choice('abc') for _ in range(randomizer.randrange(1, 8)))
            expected, start = [], 0
            while True:
                position = text.find(marker, start)
                if position < 0: break
                expected.append(position); start = position + 1
            self.assertEqual(positions(text, marker), expected)
            counted('overlappingMatches')
        with self.assertRaises(ValueError): positions('receipt', '')
        with self.assertRaises(ValueError): positions('x' * 4097, 'x')

    def test_lcs_against_subsequence_enumeration(self):
        length = load('longest_common_subsequence')['common_event_length']
        randomizer = random.Random(46)
        def subsequences(text):
            return {''.join(text[index] for index in range(len(text)) if mask & (1 << index)) for mask in range(1 << len(text))}
        for _ in range(200):
            first = ''.join(randomizer.choice('abc') for _ in range(randomizer.randrange(8)))
            second = ''.join(randomizer.choice('abc') for _ in range(randomizer.randrange(8)))
            self.assertEqual(length(first, second), max(map(len, subsequences(first) & subsequences(second))))
            counted('subsequenceEnumeration')
        with self.assertRaises(ValueError): length('x' * 129, '')

    def test_knapsack_against_subsets(self):
        cargo = load('knapsack')['cargo_value']
        randomizer = random.Random(47)
        for _ in range(250):
            items = [(randomizer.randrange(1, 7), randomizer.randrange(15)) for _ in range(randomizer.randrange(9))]
            capacity = randomizer.randrange(15)
            values = [sum(items[index][1] for index in range(len(items)) if mask & (1 << index))
                      for mask in range(1 << len(items))
                      if sum(items[index][0] for index in range(len(items)) if mask & (1 << index)) <= capacity]
            self.assertEqual(cargo(items, capacity), max(values))
            counted('cargoSubsetEnumeration')
        for items, capacity in [([(0, 1)], 1), ([(1, True)], 1), ([], True), ([], 257)]:
            with self.assertRaises(ValueError): cargo(items, capacity)

    def test_trie_against_word_set(self):
        Trie = load('trie_prefix')['LabelTrie']
        trie, words = Trie(), set()
        randomizer = random.Random(48)
        for _ in range(500):
            word = ''.join(randomizer.choice('abc') for _ in range(randomizer.randrange(1, 5)))
            if word in words or len(words) < 64:
                self.assertEqual(trie.insert(word), word not in words); words.add(word)
            else:
                with self.assertRaises(ValueError): trie.insert(word)
            query = ''.join(randomizer.choice('abc') for _ in range(randomizer.randrange(1, 5)))
            self.assertEqual(trie.contains(query), query in words)
            self.assertEqual(trie.has_prefix(query), any(word.startswith(query) for word in words))
            counted('trieOperations')
        for word in ['', 'LEDGER', '$', 'é']:
            with self.assertRaises(ValueError): trie.insert(word)

    def test_link_reversal_preserves_nodes_and_rejects_cycles_before_edit(self):
        program = load('linked_list_reversal'); Node, reverse = program['DispatchNode'], program['reverse_chain']
        for size in range(65):
            nodes = [Node(index) for index in range(size)]
            for index in range(size - 1): nodes[index].next = nodes[index + 1]
            head = reverse(nodes[0] if nodes else None)
            observed = []
            while head is not None: observed.append(head); head = head.next
            self.assertEqual(observed, list(reversed(nodes))); counted('chainIdentity')
        first, second = Node(41), Node(42)
        first.next, second.next = second, first
        with self.assertRaises(ValueError): reverse(first)
        self.assertIs(first.next, second); self.assertIs(second.next, first)
        nodes = [Node(index) for index in range(65)]
        for index in range(64): nodes[index].next = nodes[index + 1]
        with self.assertRaises(ValueError): reverse(nodes[0])
        self.assertIs(nodes[0].next, nodes[1])

    def test_tree_repeat_policy_and_depth(self):
        preorder = load('tree_traversal')['hierarchy_preorder']
        self.assertEqual(preorder({index: [index + 1] if index < 63 else [] for index in range(64)}, 0), list(range(64)))
        for graph in [{0: [1], 1: [0]}, {0: [1, 2], 1: [2], 2: []}, {0: [1]}, {0: [True], 1: []}]:
            with self.assertRaises(ValueError): preorder(graph, 0)

    def test_ingestion_boundaries(self):
        accept = load('bounded_csv')['import_receipts']
        cases = [b'x' * 513, b'receipt_id,amount_minor\n41,125\n41,75\n', b'receipt_id,amount_minor\n41,0\n', b'receipt_id,amount_minor\n41,1\n42,1\n43,1\n44,1\n', b'bad,header\n', b'receipt_id,amount_minor\n41,1,2\n', 'receipt_id,amount_minor\n４１,125\n'.encode(), b'receipt_id,amount_minor\n41,\xff\n']
        for payload in cases:
            with self.assertRaises(ValueError): accept(payload)
        self.assertEqual(accept(b'receipt_id,amount_minor\n'), {})

    def test_batch_failure_and_sql_reopen(self):
        adjust = load('rollback_exercise')['adjusted_stock']
        stock = {'paper': 12, 'ink': 4}
        for changes in [[('paper', -2), ('ink', -5)], [('paper', -2), ('missing', 1)], [('paper', True)]]:
            with self.assertRaises(ValueError): adjust(stock, changes)
            self.assertEqual(stock, {'paper': 12, 'ink': 4})
        accept = load('sqlite_cli_project')['accept_batch']
        with tempfile.TemporaryDirectory() as directory:
            file = Path(directory) / 'receipts.db'
            connection = sqlite3.connect(file)
            try:
                connection.execute('CREATE TABLE receipts(receipt_id INTEGER PRIMARY KEY, amount_minor INTEGER NOT NULL CHECK(amount_minor > 0))')
                accept(connection, [(41, 125)])
                for rows in [[(42, 75), (41, 90)], [(42, 75), (41, 20), (43, 10)]]:
                    with self.assertRaises(sqlite3.IntegrityError): accept(connection, rows)
                for rows in [[(42, True)], [(42, 75), (42, 90)]]:
                    with self.assertRaises(ValueError): accept(connection, rows)
            finally: connection.close()
            reopened = sqlite3.connect(file)
            try: self.assertEqual(reopened.execute('SELECT * FROM receipts').fetchall(), [(41, 125)])
            finally: reopened.close()

    def test_file_replace_failure_preserves_previous_and_cleans_candidate(self):
        publish = load('atomic_report_project')['publish_report']
        with tempfile.TemporaryDirectory() as directory:
            target = Path(directory) / 'report.txt'; target.write_text('old', encoding='utf-8')
            with patch('os.replace', side_effect=OSError('injected replacement failure')):
                with self.assertRaises(OSError): publish(target, [125])
            self.assertEqual(target.read_text(), 'old')
            self.assertEqual(list(Path(directory).iterdir()), [target])
            publish(target, [125, 75]); self.assertEqual(target.read_text(), 'total_minor=200\n')

    def test_descriptor_rejection_and_copy_aliases(self):
        Line = load('descriptors')['DispatchLine']; line = Line(12)
        for value in [True, -1, 1001, '12']:
            with self.assertRaises(ValueError): line.quantity = value
            self.assertEqual(line.quantity, 12)
        copies = load('copy_deepcopy')
        self.assertIs(copies['owned']['first'], copies['owned']['second'])
        self.assertIsNot(copies['owned']['first'], copies['labels'])

    def test_flask_request_boundaries(self):
        client = load('flask_json_api')['create_application']().test_client()
        for payload in [[], None, {'quantity': 1}, {'quantity': -1, 'unit_minor': 125}, {'quantity': 101, 'unit_minor': 125}, {'quantity': 1, 'unit_minor': True}]:
            response = client.post('/receipt-estimates', data=json.dumps(payload), content_type='application/json')
            self.assertEqual(response.status_code, 400)
        self.assertEqual(client.post('/receipt-estimates', data='plain', content_type='text/plain').status_code, 415)
        self.assertEqual(client.post('/receipt-estimates', data='{', content_type='application/json').status_code, 400)
        self.assertEqual(client.post('/receipt-estimates', data=' ' * 257, content_type='application/json').status_code, 413)
        self.assertEqual(client.post('/receipt-estimates', json={'quantity': 0, 'unit_minor': 0}).get_json(), {'total_minor': 0})

if __name__ == '__main__':
    suite = unittest.defaultTestLoader.loadTestsFromTestCase(ExpansionContracts)
    result = unittest.TextTestRunner(verbosity=2).run(suite)
    report = {'passed': result.wasSuccessful(), 'tests': result.testsRun, 'oracleComparisons': sum(COUNTS.values()), 'oracles': COUNTS, 'failures': len(result.failures), 'errors': len(result.errors)}
    print(json.dumps(report))
    raise SystemExit(0 if result.wasSuccessful() else 1)
