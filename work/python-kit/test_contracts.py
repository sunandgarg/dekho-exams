"""Boundary and independent-oracle tests for the exact public teaching sources."""
import bisect, contextlib, io, pathlib, random, runpy, unittest
ROOT=pathlib.Path(__file__).resolve().parent

def load(name):
 with contextlib.redirect_stdout(io.StringIO()):
  return runpy.run_path(str(ROOT/(name+'.py')))

class Contracts(unittest.TestCase):
 def test_search_against_bisect(self):
  search=load('binary_search')['lower_bound'];rng=random.Random(4101)
  for _ in range(1000):
   sequence=sorted(rng.randrange(-30,31) for _ in range(rng.randrange(50)))
   target=rng.randrange(-35,36)
   self.assertEqual(search(sequence,target),bisect.bisect_left(sequence,target))
  with self.assertRaises(ValueError):search([1]*10001,1)

 def test_package_minimum_against_forward_distance(self):
  minimum=load('memoization')['minimum_packages'];rng=random.Random(4102)
  for _ in range(1000):
   sizes=tuple(rng.randrange(1,12) for _ in range(rng.randrange(1,7)))
   target=rng.randrange(101)
   # Forward breadth layers over reachable amounts, independent of recursive cache.
   reached={0};front={0};answer=0 if target==0 else -1
   for depth in range(1,target+1):
    following={amount+size for amount in front for size in sizes if amount+size<=target}-reached
    if target in following:answer=depth;break
    if not following:break
    reached.update(following);front=following
   self.assertEqual(minimum(sizes,target),answer,(sizes,target))
  for sizes,target in [((),5),((0,),5),((True,),5),((1,),True),((1,),101)]:
   with self.assertRaises(ValueError):minimum(sizes,target)

 def test_graph_against_all_pairs_relaxation(self):
  distance=load('graph_bfs')['route_distances'];rng=random.Random(4103)
  for _ in range(250):
   count=rng.randrange(1,12)
   graph=[[v for v in range(count) if rng.random()<.18] for _ in range(count)]
   # Floyd-Warshall checks distances without a BFS queue or discovery array.
   matrix=[[0 if u==v else 1 if v in graph[u] else 1000 for v in range(count)] for u in range(count)]
   for middle in range(count):
    for left in range(count):
     for right in range(count):matrix[left][right]=min(matrix[left][right],matrix[left][middle]+matrix[middle][right])
   start=rng.randrange(count)
   self.assertEqual(distance(graph,start),[-1 if d==1000 else d for d in matrix[start]])
  for graph,start in [([],0),([[]],True),([[]],1),([[1]],0),([[False]],0),([[0]*10001],0)]:
   with self.assertRaises(ValueError):distance(graph,start)

 def test_json_schema_and_duplicate_members(self):
  read=load('json_validation')['receipt_amount']
  self.assertEqual(read('{"amount_minor":125}'),125)
  for payload in ['[]','null','{"amount_minor":true}','{"amount_minor":0}','{"amount_minor":1.5}','{"amount_minor":1,"amount_minor":2}','{"amount_minor":125,"currency":"INR"}','x'*1025]:
   with self.assertRaises(ValueError):read(payload)

 def test_inventory_rejects_whole_batch_and_copies_snapshot(self):
  Ledger=load('inventory_project')['InventoryLedger'];ledger=Ledger();before=ledger.snapshot()
  for changes in [[('paper',-2),('ink',-9)],[('paper',-2),('unknown',1)],[('paper',True)],[('paper',1)]*101]:
   with self.assertRaises(ValueError):ledger.apply(changes)
   self.assertEqual(ledger.snapshot(),before)
  snapshot=ledger.snapshot();snapshot['paper']=999;self.assertEqual(ledger.snapshot(),before)
  ledger.apply([('paper',-8)]);self.assertEqual(ledger.snapshot()['paper'],0)

 def test_ascii_wire_amount_boundary(self):
  read=load('input_exercise')['wire_amount'];self.assertEqual(read('00000125'),125);self.assertEqual(read('99999999'),99999999)
  for value in ['', '0','000','+125',' 125','125\n','１２５','١٢٥','123456789']:
   with self.assertRaises(ValueError):read(value)

 def test_ledger_rejected_rows_and_no_input_mutation(self):
  read=load('collection_exercise')['validated_ledger'];rows=[(41,125),(42,75)];original=rows.copy()
  self.assertEqual(read(rows),{41:125,42:75});self.assertEqual(rows,original)
  for invalid in [[(41,125),(41,75)],[(True,125)],[(41,True)],[(0,125)],[(41,0)],[(1,1)]*1001]:
   with self.assertRaises(ValueError):read(invalid)

class MoreBoundaries(unittest.TestCase):
 def test_match_rejects_extra_boolean_or_wrong_operation(self):
  route=load('pattern_matching')['route_command']
  self.assertEqual(route({'operation':'read','receipt_id':41}),'read:41')
  for command in [{},[],{'operation':'read','receipt_id':True},{'operation':'read','receipt_id':0},{'operation':'delete','receipt_id':41},{'operation':'read','receipt_id':41,'extra':1}]:
   with self.assertRaises(ValueError):route(command)

 def test_timestamp_requires_offset_and_same_instant(self):
  parse=load('datetime_boundaries')['receipt_instant']
  self.assertEqual(parse('2026-09-29T10:00:00+05:30'),parse('2026-09-29T04:30:00+00:00'))
  for value in ['', 'x'*41, '2026-09-29T10:00:00', '2026-02-30T10:00:00+00:00']:
   with self.assertRaises(ValueError):parse(value)

 def test_regex_exact_alphabet_and_whole_value(self):
  valid=load('regex_validation')['valid_receipt_id']
  self.assertTrue(valid('R-0000'));self.assertTrue(valid('R-9999'))
  for value in ['R-0041\n','xR-0041','R-００４１','R-123','R-12345','r-0041','R-0041suffix']:
   self.assertFalse(valid(value))

if __name__=='__main__':unittest.main()
