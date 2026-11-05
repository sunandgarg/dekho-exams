"""Independent oracles and failure checks for the fourth Python pass."""
import contextlib
import copy
from functools import lru_cache
import io
import json
from pathlib import Path
import random
import runpy
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

class CompletionContracts(unittest.TestCase):
    def test_avl_order_balance_and_rotation_cases(self):
        index_type = load('avl_insertion')['ReceiptIndex']
        def inspect(node, lower=None, upper=None):
            if node is None: return [], 0
            self.assertTrue(lower is None or lower < node.key)
            self.assertTrue(upper is None or node.key < upper)
            before, left_height = inspect(node.left, lower, node.key)
            after, right_height = inspect(node.right, node.key, upper)
            self.assertLessEqual(abs(left_height - right_height), 1)
            self.assertEqual(node.height, 1 + max(left_height, right_height))
            return before + [node.key] + after, node.height
        for order in ((30,20,10),(10,20,30),(30,10,20),(10,30,20)):
            index = index_type()
            for key in order: index.add(key)
            self.assertEqual(index.root.key, 20)
            self.assertEqual(inspect(index.root)[0], [10,20,30])
        randomizer = random.Random(81)
        for _ in range(100):
            index = index_type(); accepted = set()
            for key in randomizer.choices(range(-100, 101), k=80):
                index.add(key); accepted.add(key)
                self.assertEqual(inspect(index.root)[0], sorted(accepted))
                self.assertEqual(index.keys, accepted)
                counted('avlSortedSetOracle')
        index = index_type()
        for key in range(128): index.add(key)
        before = inspect(index.root)
        for key in (True, '129', 129):
            with self.assertRaises(ValueError): index.add(key)
            self.assertEqual(inspect(index.root), before)
        index.add(127)
        self.assertEqual(len(index.keys),128)

    def test_trie_deletion_against_word_set(self):
        namespace = load('trie_deletion')
        build, remove, words = (namespace[key] for key in ('build_routes','remove_route','route_words'))
        randomizer = random.Random(82)
        for _ in range(100):
            accepted = {''.join(randomizer.choices('ABC', k=randomizer.randrange(1,7))) for _ in range(50)}
            root = build(list(accepted))
            for _ in range(40):
                word = ''.join(randomizer.choices('ABC', k=randomizer.randrange(1,7)))
                existed = word in accepted
                self.assertEqual(remove(root,word), existed)
                accepted.discard(word)
                self.assertEqual(words(root), sorted(accepted))
                counted('trieWordSetOracle')
            before = copy.deepcopy(root)
            for rejected in ('', 'del', 'A'*33, '\u00c9', None):
                with self.assertRaises(ValueError): remove(root,rejected)
                self.assertEqual(root,before)
        root = build(['A','AB','ABC'])
        self.assertTrue(remove(root,'AB'))
        self.assertEqual(words(root),['A','ABC'])
        self.assertTrue(remove(root,'ABC'))
        self.assertEqual(words(root),['A'])

    def test_lazy_ranges_against_direct_mutation(self):
        tree_type = load('lazy_range_sums')['RangeAmounts']
        randomizer = random.Random(83)
        for _ in range(100):
            amounts = [randomizer.randrange(-200,201) for _ in range(randomizer.randrange(1,40))]
            before = amounts.copy(); owned = amounts.copy(); tree = tree_type(amounts)
            for _ in range(100):
                left,right = sorted((randomizer.randrange(len(owned)+1), randomizer.randrange(len(owned)+1)))
                if randomizer.random() < .6:
                    delta = randomizer.randrange(-50,51)
                    tree.add(left,right,delta)
                    for index in range(left,right): owned[index] += delta
                self.assertEqual(tree.total(left,right),sum(owned[left:right]))
                self.assertEqual(tree.total(0,len(owned)),sum(owned))
                self.assertEqual(amounts,before)
                counted('lazyDirectArrayOracle')
            snapshot = (tree.sums.copy(),tree.lazy.copy())
            for left,right,delta in ((-1,1,2),(0,len(owned)+1,2),(True,1,2),(0,1,True),(1,0,2)):
                with self.assertRaises(ValueError): tree.add(left,right,delta)
                self.assertEqual((tree.sums,tree.lazy),snapshot)
        for amounts in ([],[True],[0]*129):
            with self.assertRaises(ValueError): tree_type(amounts)

    def test_edit_script_against_recursive_distance_and_replay(self):
        namespace = load('edit_script'); align = namespace['align_labels']; replay = namespace['apply_alignment']
        @lru_cache(None)
        def oracle(first,second):
            if not first: return len(second)
            if not second: return len(first)
            return min(oracle(first[1:],second)+1,oracle(first,second[1:])+1,
                       oracle(first[1:],second[1:])+(first[0]!=second[0]))
        randomizer = random.Random(84)
        for _ in range(2000):
            first = ''.join(randomizer.choices('ABC',k=randomizer.randrange(7)))
            second = ''.join(randomizer.choices('ABC',k=randomizer.randrange(7)))
            distance,steps = align(first,second)
            self.assertEqual(distance,oracle(first,second))
            self.assertEqual(replay(first,steps),second)
            self.assertEqual(distance,sum(kind != 'keep' for kind,before,after in steps))
            counted('editReconstructionOracle')
        for first,second in ((None,'DEL'),('A'*33,'')):
            with self.assertRaises(ValueError): align(first,second)
        with self.assertRaises(ValueError): replay('ABC',[('delete','X','')])
        with self.assertRaises(ValueError): replay('ABC',[])

    def test_window_against_slice_enumeration(self):
        best = load('window_exercise')['maximum_window']; randomizer = random.Random(85)
        for _ in range(2000):
            amounts = [randomizer.randrange(-500,501) for _ in range(randomizer.randrange(1,60))]
            width = randomizer.randrange(1,len(amounts)+1); before = amounts.copy()
            self.assertEqual(best(amounts,width),max(sum(amounts[start:start+width]) for start in range(len(amounts)-width+1)))
            self.assertEqual(amounts,before); counted('fixedWindowSlicesOracle')
        for amounts,width in (([],1),([True],1),([3],True),([3],0),([3],2)):
            with self.assertRaises(ValueError): best(amounts,width)

    def test_prefix_ranges_against_sums(self):
        namespace = load('range_exercise'); build,total = namespace['prefix_totals'],namespace['interval_total']
        randomizer = random.Random(86)
        for _ in range(200):
            amounts = [randomizer.randrange(-200,201) for _ in range(randomizer.randrange(60))]
            prefix = build(amounts)
            for _ in range(30):
                left,right = sorted((randomizer.randrange(len(amounts)+1),randomizer.randrange(len(amounts)+1)))
                self.assertEqual(total(prefix,left,right),sum(amounts[left:right])); counted('prefixDirectSumsOracle')
            snapshot = prefix.copy()
            if amounts: amounts[0] += 999
            self.assertEqual(prefix,snapshot)
            for left,right in ((True,0),(-1,0),(0,len(prefix)),(1,0)):
                with self.assertRaises(ValueError): total(prefix,left,right)
        with self.assertRaises(ValueError): build([True])

    def test_aggregation_against_independent_group_sums(self):
        aggregate = load('aggregation_exercise')['accepted_totals']; randomizer = random.Random(87)
        for _ in range(1000):
            records = [{'region':randomizer.choice(('DEL','BOM')),'amount':randomizer.randrange(1000001)} for _ in range(randomizer.randrange(65))]
            expected = {region:sum(row['amount'] for row in records if row['region']==region) for region in ('DEL','BOM') if any(row['region']==region for row in records)}
            before = copy.deepcopy(records)
            self.assertEqual(aggregate(records),expected); self.assertEqual(records,before)
            counted('regionDirectSumsOracle')
            rejected = records[:63]+[{'region':'DEL','amount':True}]
            with self.assertRaises(ValueError): aggregate(rejected)
        for records in ([{'region':'XXX','amount':1}],[{'region':'DEL','amount':1,'owner':7}],[{'region':'DEL','amount':-1}],[{'region':'DEL','amount':1000001}],None,[{}]*65):
            with self.assertRaises(ValueError): aggregate(records)

    def test_input_parsers_and_stream_ownership(self):
        read = load('input_output')['read_quantity']; parse = load('type_conversion')['parse_quantity']
        for amount in range(1,21):
            source,output = io.StringIO(str(amount)+'\n'),io.StringIO()
            self.assertEqual(read(source,output),amount)
            self.assertEqual(output.getvalue(),f'accepted quantity: {amount}\n')
            self.assertFalse(source.closed); self.assertFalse(output.closed)
        for text in ('0\n','21\n',' 3\n','+3\n','3.0\n','3','\u0663\n','123456\n','\n'):
            source,output = io.StringIO(text),io.StringIO()
            with self.assertRaises(ValueError): read(source,output)
            self.assertEqual(output.getvalue(),''); self.assertFalse(source.closed)
        with self.assertRaises(EOFError): read(io.StringIO(''),io.StringIO())
        for amount in range(201):
            self.assertEqual(parse(str(amount)),amount)
        for text in ('201','+3',' 3','3.0','\u0663',True,None):
            with self.assertRaises(ValueError): parse(text)

    def test_flask_reopen_and_rejected_writes(self):
        app = load('flask_sqlite_persistence')['receipt_app']
        with tempfile.TemporaryDirectory() as directory:
            database = Path(directory)/'owned.sqlite3'; client = app(database).test_client()
            payload = {'receipt_id':'R-0041','amount':125}
            self.assertEqual(client.post('/receipts',json=payload).status_code,201)
            self.assertEqual(client.post('/receipts',json={**payload,'amount':999}).status_code,409)
            rejected = [{**payload,'receipt_id':'R-0042','amount':True},{**payload,'owner':7},{**payload,'receipt_id':' R-0042'},[],{**payload,'amount':-1}]
            for candidate in rejected: self.assertEqual(client.post('/receipts',json=candidate).status_code,400)
            self.assertEqual(client.post('/receipts',data='not JSON').status_code,415)
            self.assertEqual(client.post('/receipts',data='{'*1025,content_type='application/json').status_code,413)
            reopened = app(database).test_client()
            self.assertEqual(reopened.get('/receipts').get_json(),[payload])

    def test_drf_serializer_isolated_process(self):
        source = """import contextlib,io,runpy,sys
with contextlib.redirect_stdout(io.StringIO()):
    namespace=runpy.run_path(sys.argv[1])
ReceiptInput=namespace['ReceiptInput']
for amount in (0,1000000):
    serializer=ReceiptInput(data={'receipt_id':'R-0041','amount':amount})
    assert serializer.is_valid(),serializer.errors
for candidate in ({'receipt_id':' R-0041','amount':1},{'receipt_id':'R-0041 ','amount':1},{'receipt_id':'R-\u0660\u0660\u0664\u0661','amount':1},{'receipt_id':'R-0041','amount':True},{'receipt_id':'R-0041','amount':'1'},{'receipt_id':'R-0041','amount':1000001},{'receipt_id':'R-0041','amount':1,'owner':7}):
    assert not ReceiptInput(data=candidate).is_valid(),candidate
print('serializer boundaries passed')
"""
        result = subprocess.run([sys.executable,'-I','-c',source,str(HERE/'drf_serializers.py')],capture_output=True,text=True,timeout=30)
        self.assertEqual(result.returncode,0,result.stderr); self.assertEqual(result.stdout,'serializer boundaries passed\n')

    def test_drf_detail_permissions_isolated_process(self):
        source = """import contextlib,io,runpy,sys
with contextlib.redirect_stdout(io.StringIO()):
    namespace=runpy.run_path(sys.argv[1])
response=namespace['local_response']
assert response(7,41)==200
for principal in (8,9,None): assert response(principal,41)==403
assert response(7,99)==404
print('detail permissions passed')
"""
        result = subprocess.run([sys.executable,'-I','-c',source,str(HERE/'drf_object_permissions.py')],capture_output=True,text=True,timeout=30)
        self.assertEqual(result.returncode,0,result.stderr); self.assertEqual(result.stdout,'detail permissions passed\n')

if __name__ == '__main__':
    suite = unittest.defaultTestLoader.loadTestsFromTestCase(CompletionContracts)
    result = unittest.TextTestRunner(verbosity=2).run(suite)
    report = {'passed':result.wasSuccessful(),'suites':result.testsRun,'independentComparisons':sum(COUNTS.values()),'comparisonGroups':COUNTS}
    print(json.dumps(report))
    raise SystemExit(not result.wasSuccessful())
