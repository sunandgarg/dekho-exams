"""Independent state-change oracles and publication boundaries for the fifth pass."""
import contextlib
import copy
import io
import json
from pathlib import Path
import random
import runpy
import subprocess
import sys
import unittest

HERE = Path(__file__).resolve().parent
COUNTS = {}

def load(name):
    with contextlib.redirect_stdout(io.StringIO()):
        return runpy.run_path(str(HERE/(name+'.py')))

def counted(name):
    COUNTS[name] = COUNTS.get(name,0)+1

class AppliedContracts(unittest.TestCase):
    def test_avl_mixed_add_remove_against_sorted_keys(self):
        index_type = load('avl_deletion')['RemovableIndex']
        def inspect(node,lower=None,upper=None):
            if node is None: return [],0
            self.assertTrue(lower is None or lower<node.key)
            self.assertTrue(upper is None or node.key<upper)
            left,left_height = inspect(node.left,lower,node.key)
            right,right_height = inspect(node.right,node.key,upper)
            self.assertLessEqual(abs(left_height-right_height),1)
            self.assertEqual(node.height,1+max(left_height,right_height))
            return left+[node.key]+right,node.height
        randomizer = random.Random(91)
        for _ in range(150):
            index = index_type(); accepted = set()
            for _ in range(120):
                key = randomizer.randrange(-40,41)
                if randomizer.random()<.55:
                    index.add(key); accepted.add(key)
                else:
                    self.assertEqual(index.remove(key),key in accepted); accepted.discard(key)
                self.assertEqual(inspect(index.root)[0],sorted(accepted)); self.assertEqual(index.keys,accepted)
                counted('avlMixedKeySetOracle')
            before = inspect(index.root)
            with self.assertRaises(ValueError): index.remove(True)
            self.assertEqual(inspect(index.root),before)
            for key in list(accepted): index.remove(key)
            self.assertIsNone(index.root)

    def test_components_against_mutual_reachability(self):
        components = load('strongly_connected_components')['dependency_components']; randomizer = random.Random(92)
        for _ in range(1000):
            count = randomizer.randrange(0,9)
            edges = [(source,target) for source in range(count) for target in range(count) if randomizer.random()<.25]
            adjacency = [set() for _ in range(count)]
            for source,target in edges: adjacency[source].add(target)
            reachable = []
            for source in range(count):
                seen = set(); pending = [source]
                while pending:
                    node = pending.pop()
                    if node in seen: continue
                    seen.add(node); pending.extend(adjacency[node]-seen)
                reachable.append(seen)
            remaining = set(range(count)); expected = []
            while remaining:
                source = min(remaining)
                component = sorted(node for node in remaining if node in reachable[source] and source in reachable[node])
                expected.append(component); remaining-=set(component)
            before = edges.copy()
            self.assertEqual(components(count,edges),sorted(expected)); self.assertEqual(edges,before)
            counted('mutualReachabilityOracle')
        for count,edges in ((True,[]),(33,[]),(2,[(0,True)]),(2,[(0,2)])):
            with self.assertRaises(ValueError): components(count,edges)

    def test_bridges_against_edge_removal_connectivity(self):
        bridges = load('graph_bridges')['bridge_links']; randomizer = random.Random(93)
        def count_components(count,edges):
            adjacency = [set() for _ in range(count)]
            for first,second in edges: adjacency[first].add(second); adjacency[second].add(first)
            remaining = set(range(count)); result = 0
            while remaining:
                pending = [next(iter(remaining))]; seen = set()
                while pending:
                    node = pending.pop()
                    if node in seen: continue
                    seen.add(node); pending.extend(adjacency[node]-seen)
                remaining-=seen; result+=1
            return result
        for _ in range(1000):
            count = randomizer.randrange(1,9)
            edges = [(randomizer.randrange(count),randomizer.randrange(count)) for _ in range(randomizer.randrange(18))]
            initial = count_components(count,edges)
            expected = [number for number in range(len(edges)) if count_components(count,edges[:number]+edges[number+1:])>initial]
            self.assertEqual(bridges(count,edges),expected); counted('removedEdgeConnectivityOracle')
        self.assertEqual(bridges(2,[(0,1),(0,1)]),[])
        self.assertEqual(bridges(1,[(0,0)]),[])
        with self.assertRaises(ValueError): bridges(2,[(0,True)])

    def test_compressed_trie_against_exact_word_set(self):
        namespace = load('compressed_trie'); build,contains = namespace['compressed_routes'],namespace['contains_route']
        randomizer = random.Random(94)
        for _ in range(200):
            accepted = {''.join(randomizer.choices('ABCD',k=randomizer.randrange(1,9))) for _ in range(60)}
            routes = build(list(accepted))
            for _ in range(50):
                word = ''.join(randomizer.choices('ABCD',k=randomizer.randrange(1,9)))
                self.assertEqual(contains(routes,word),word in accepted); counted('compressedWordSetOracle')
            for word in accepted: self.assertTrue(contains(routes,word))
        routes = build(['DEL','DELHI','BOM'])
        self.assertTrue(contains(routes,'DEL')); self.assertFalse(contains(routes,'DE'))
        for word in ('',None,'a','A'*33):
            with self.assertRaises(ValueError): contains(routes,word)

    def test_palindrome_against_all_substrings(self):
        longest = load('longest_palindrome')['longest_label_palindrome']; randomizer = random.Random(95)
        for _ in range(2000):
            text = ''.join(randomizer.choices('ABCD',k=randomizer.randrange(22)))
            expected = ''
            for left in range(len(text)):
                for right in range(left+1,len(text)+1):
                    candidate = text[left:right]
                    if candidate==candidate[::-1] and len(candidate)>len(expected): expected=candidate
            self.assertEqual(longest(text),expected); counted('palindromeSubstringOracle')
        for text in (None,'A'*129):
            with self.assertRaises(ValueError): longest(text)

    def test_lru_against_access_list(self):
        cache_type = load('lru_project')['ReceiptCache']; randomizer = random.Random(96)
        for _ in range(200):
            capacity = randomizer.randrange(1,9); cache = cache_type(capacity); expected = []
            for _ in range(100):
                key = f'R-{randomizer.randrange(16):04d}'
                match = next((entry for entry in expected if entry[0]==key),None)
                if randomizer.random()<.6:
                    amount = randomizer.randrange(1001)
                    cache.put(key,amount)
                    expected = [entry for entry in expected if entry[0]!=key]+[(key,amount)]
                    expected=expected[-capacity:]
                else:
                    self.assertEqual(cache.get(key),None if match is None else match[1])
                    if match is not None: expected=[entry for entry in expected if entry[0]!=key]+[match]
                self.assertEqual(list(cache.entries.items()),expected); counted('lruAccessListOracle')
            before = list(cache.entries.items())
            for key,amount in (('R-0000',True),('bad',125),('R-0000',None),('R-0000',1000001)):
                with self.assertRaises(ValueError): cache.put(key,amount)
                self.assertEqual(list(cache.entries.items()),before)

    def test_reconciliation_against_record_search(self):
        reconcile = load('reconciliation_exercise')['reconcile_receipts']; randomizer = random.Random(97)
        for _ in range(1000):
            left = [{'id':f'R-{number:04d}','amount':randomizer.randrange(1000)} for number in range(16) if randomizer.random()<.6]
            right = [{'id':f'R-{number:04d}','amount':randomizer.randrange(1000)} for number in range(16) if randomizer.random()<.6]
            expected = []
            for number in range(16):
                key = f'R-{number:04d}'
                first=next((row for row in left if row['id']==key),None)
                second=next((row for row in right if row['id']==key),None)
                if first is None and second is not None: expected.append((key,'missing-left'))
                elif second is None and first is not None: expected.append((key,'missing-right'))
                elif first is not None and first['amount']!=second['amount']: expected.append((key,'amount-mismatch'))
            before = copy.deepcopy((left,right))
            self.assertEqual(reconcile(left,right),expected); self.assertEqual((left,right),before)
            counted('reconciliationRecordSearchOracle')
        for records in ([{'id':'R-0001','amount':True}],[{'id':'R-0001','amount':1}]*2,[{'id':'R-0001','amount':1,'owner':7}]):
            with self.assertRaises(ValueError): reconcile(records,[])

    def test_json_line_budgets_duplicates_and_ownership(self):
        read = load('bounded_json_lines')['read_receipt_lines']
        accepted = io.BytesIO(b'{"id":"R-0041","amount":0}\n')
        self.assertEqual(read(accepted),[{'id':'R-0041','amount':0}]); self.assertFalse(accepted.closed)
        rejected = [b'{"id":"R-0041","amount":1,"amount":2}\n',b'{"id":"R-0041","amount":true}\n',b'{"id":"R-0041","amount":1}',b'x'*65,b'{}\n'*5,b'{"id":"R-0041","amount":1,"owner":7}\n',b'{"id":"R-0041","amount":-1}\n']
        for payload in rejected:
            source = io.BytesIO(payload)
            with self.assertRaises(ValueError): read(source)
            self.assertFalse(source.closed)
        late = io.BytesIO(b'{"id":"R-0041","amount":125}\n{"id":"R-0042","amount":true}\n')
        with self.assertRaises(ValueError): read(late)
        self.assertEqual(read(io.BytesIO(b'')),[])
        row=b'{"id":"R-0041","amount":1}\n'
        self.assertEqual(len(read(io.BytesIO(row*4))),4)
        with self.assertRaises(ValueError): read(io.BytesIO(row*5))
        padded=row[:-1]+b' '*(64-len(row))+b'\n'
        self.assertEqual(len(read(io.BytesIO(padded*2))),2)
        with self.assertRaises(ValueError): read(io.BytesIO(padded*3))

    def test_zip_names_modes_and_actual_byte_budgets(self):
        import stat
        import zipfile
        namespace = load('zip_member_validation'); stage,archive = namespace['staged_zip_members'],namespace['owned_archive']
        self.assertEqual(stage(archive('receipts.txt',b'accepted')),{'receipts.txt':b'accepted'})
        for name,data in (('../escape.txt',b'x'),('/absolute.txt',b'x'),('nested/file.txt',b'x'),('back\\slash.txt',b'x'),('receipts.txt',b'x'*257)):
            with self.assertRaises(ValueError): stage(archive(name,data))
        buffer=io.BytesIO()
        with zipfile.ZipFile(buffer,'w') as package:
            member=zipfile.ZipInfo('receipts.txt'); member.create_system=3; member.external_attr=(stat.S_IFLNK|0o777)<<16
            package.writestr(member,b'outside')
        with self.assertRaises(ValueError): stage(buffer.getvalue())
        buffer=io.BytesIO()
        with zipfile.ZipFile(buffer,'w') as package:
            for name,data in (('first.txt',b'x'*256),('second.txt',b'x'*256),('third.txt',b'x')): package.writestr(name,data)
        with self.assertRaises(ValueError): stage(buffer.getvalue())

    def test_outbox_rollback_and_replay(self):
        namespace = load('outbox_project'); database=namespace['open_outbox']()
        try:
            with self.assertRaises(RuntimeError): namespace['create_receipt'](database,'R-0041',125,True)
            self.assertEqual(database.execute('SELECT count(*) FROM receipts').fetchone()[0],0)
            self.assertEqual(namespace['pending_events'](database),[])
            namespace['create_receipt'](database,'R-0041',125)
            self.assertEqual(namespace['pending_events'](database),[('created:R-0041','R-0041')])
            with self.assertRaises(ValueError): namespace['create_receipt'](database,'R-0042',True)
            self.assertEqual(database.execute('SELECT count(*) FROM receipts').fetchone()[0],1)
        finally: database.close()

    def test_api_list_and_creation_isolated(self):
        cases = {
            'drf_list_visibility': """assert namespace['visible_receipts'](7,0,2)==[{'id':41},{'id':43}]
assert namespace['visible_receipts'](7,43,2)==[{'id':44}]
assert namespace['visible_receipts'](8,0,2)==[{'id':42}]
for args in ((True,0,2),(7,-1,2),(7,0,3)):
    try: namespace['visible_receipts'](*args)
    except ValueError: pass
    else: raise AssertionError(args)
""",
            'drf_creation_ownership': """records=namespace['RECEIPTS']; records.clear(); create=namespace['local_create']
assert create({'receipt_id':'R-0041','amount':125})==201
assert records['R-0041']['owner_id']==7
assert create({'receipt_id':'R-0041','amount':250})==409
for payload in ({'receipt_id':'R-0042','amount':True},{'receipt_id':'R-0042','amount':'125'},{'receipt_id':'R-0042','amount':125,'owner_id':8},{'receipt_id':'R-0042 ','amount':125}): assert create(payload)==400,payload
assert len(records)==1
request=namespace['APIRequestFactory']().post('/receipts',{'receipt_id':'R-0042','amount':125},format='json')
assert namespace['ReceiptCreateView'].as_view()(request).status_code==403
""",
            'drf_serializers': """serializer=namespace['ReceiptInput'](data={'receipt_id':'R-0041','amount':125,'owner_id':8})
assert not serializer.is_valid()
assert 'non_field_errors' in serializer.errors
""",
        }
        for name,checks in cases.items():
            source='import contextlib,io,runpy,sys\nwith contextlib.redirect_stdout(io.StringIO()):\n    namespace=runpy.run_path(sys.argv[1])\n'+checks+'\nprint("request boundary passed")\n'
            result=subprocess.run([sys.executable,'-I','-c',source,str(HERE/(name+'.py'))],capture_output=True,text=True,timeout=30)
            self.assertEqual(result.returncode,0,result.stderr); self.assertEqual(result.stdout,'request boundary passed\n')

if __name__ == '__main__':
    result=unittest.TextTestRunner(verbosity=2).run(unittest.defaultTestLoader.loadTestsFromTestCase(AppliedContracts))
    report={'passed':result.wasSuccessful(),'suites':result.testsRun,'oracleComparisons':sum(COUNTS.values()),'comparisons':COUNTS}
    print(json.dumps(report));raise SystemExit(not result.wasSuccessful())
