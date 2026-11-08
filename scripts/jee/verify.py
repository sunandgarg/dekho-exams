"""Check every published archive route, adjacent question, sprite glyph and paper cross-link."""
from pathlib import Path
from collections import Counter
import gzip,json,re,hashlib,sys
root=Path(__file__).resolve().parents[2]
exam=sys.argv[1] if len(sys.argv)>1 else 'jee-main'
inventories={'jee-main':(95,18006,202,15282),'jee-advanced':(81,3959,79,3920)}
if exam not in inventories:raise ValueError('Unsupported exam')
asset_dir='jee-archive' if exam=='jee-main' else 'jee-advanced-archive'
out=root/'public'/asset_dir
def read(p):return json.loads(gzip.decompress(p.read_bytes()))
brand=re.compile(r'exam\s*(?:side|goal)|gate\s*class|geeks\s*for\s*geeks|ai\s*trove|pencil2pen',re.I)
redirects=json.loads((root/'src/data/jee-question-redirects.json').read_text())
pending=set()
qs={}; stats=Counter();glyphs=set(re.findall(r'id="([^"]+)"',(out/'math.svg').read_text()))
for f in (out/'q').glob('*.bin'):
 for k,q in read(f).items():
  assert hashlib.sha256(k.encode()).hexdigest()[:3]==f.stem,(k,f)
  assert q['slug']==k and k not in qs
  assert re.fullmatch(r'[A-Za-z0-9-]+(?:\.htm)?',k),k
  for edition in [q]+([q['hi']] if q.get('hi') else []):
   h=''.join([edition['body'],edition['solution'],*edition['options']])
   assert not re.search(r'<(?:script|iframe)\b|<[a-z][^<>]*\son[a-z]+\s*=',h,re.I),k
   assert not brand.search(h) and not brand.search(k),k
   assert not re.search(r'(?:src|href)="(?:https?:)?//',h),k
   for ref in re.findall(r'<img src="([^"]+)"',h):
    assert re.fullmatch(r'/jee-figures/[a-f0-9]{24}\.png',ref) and (root/'public'/ref[1:]).is_file(),(k,ref)
   pending.update(re.findall(r'data-figure="([a-f0-9]{24})"',h))
   assert set(re.findall('/'+asset_dir+r'/math\.svg#([\w-]+)',h))<=glyphs,k
  payload=hashlib.sha256(json.dumps([q['body'],q['options'],q['solution'],q.get('hi'),q.get('numericKey'),q.get('choiceKey'),q.get('numericRange'),q.get('choiceKeys')],ensure_ascii=False).encode()).hexdigest()
  qs[k]=(q['chapter'],q['paper'],q['prev'],q['next'],q.get('canonical'),q.get('qid'),payload)
  if not q['chapter'] and q.get('canonical'):stats['paper positions linked to chapters']+=1
  kind='chapter' if q['chapter'] else 'paper'
  if q['chapter'] or not q.get('canonical'):
   stem=any('jee-figure-pending' in part for ed in (q,q.get('hi',q)) for part in [ed['body'],*ed['options']])
   solution=any('jee-figure-pending' in ed['solution'] for ed in (q,q.get('hi',q)))
   stats['distinct questions with pending prompt figures']+=stem
   stats['distinct questions with pending solution figures only']+=solution and not stem
  stats[kind]+=1;stats[kind+' detailed']+=bool(q['complete']);stats[kind+' explanations']+=bool(q['solution']);stats[kind+' Hindi']+=bool(q.get('hi'));stats[kind+' numerical keys']+=q.get('numericKey') is not None;stats[kind+' choice keys']+=q.get('choiceKey') is not None;stats[kind+' multiple choice keys']+=bool(q.get('choiceKeys'));stats[kind+' range keys']+=bool(q.get('numericRange'));stats[kind+' shared passages']+='<aside' in q['body']
for name in ('chapter','paper'):
 for f in (out/name).rglob('*.bin'):
  rows=read(f);ids=[x['id'] for x in rows]
  assert len(set(ids))==len(ids)
  for i,k in enumerate(ids):
   ch,pa,prev,nxt,canonical,qid,payload=qs[k]
   assert (ch if name=='chapter' else pa)==f.stem
   assert (prev,nxt)==(ids[i-1] if i else None,ids[i+1] if i+1<len(ids) else None)
   if canonical:assert qs[canonical][1]==pa and qs[canonical][5]==k and qs[canonical][6]==payload,(k,canonical)
if exam=='jee-main':
 assert all(old not in qs and new in qs for old,new in redirects.items())
for f in (out/'meta').rglob('*.bin'):
 assert read(f).keys()=={'stats'},f
stats['distinct pending figure references']=len(pending)
stats['chapters']=len(list((out/'chapter').rglob('*.bin')))
stats['papers']=len(list((out/'paper').glob('*.bin')))
assert (stats['chapters'],stats['chapter'],stats['papers'],stats['paper'])==inventories[exam]
for f in (out/'print').rglob('*.bin'):
 h=gzip.decompress(f.read_bytes())
 owner=f.parent.name
 list_file=out/'chapter'/(owner.replace('--','/')+'.bin') if '--' in owner else out/'paper'/(owner+'.bin')
 assert h.count(b'<article>')==len(read(list_file))==h.count(b'<section class="print-solution">'),f
 assert b'| Dekhoexams</title>' in h and b'/dekhoexams-icon.svg' in h,f
 assert not re.search(rb'(?:src|href)="(?:https?:)?//',h) and not brand.search(h.decode()),f
 assert b'id="print-solutions"' in h,f
 stats['print '+f.stem]+=1
assert stats['chapter detailed']==stats['chapter']==stats['chapter explanations']
assert stats['paper detailed']==stats['paper']==stats['paper explanations']
assert stats['print en']==stats['chapters']+stats['papers']==stats['print hi']
assert stats['paper positions linked to chapters']==(15282 if exam=='jee-main' else 3919)
assert stats['chapter Hindi']==stats['chapter'] and stats['paper Hindi']==stats['paper']

print(json.dumps(stats,indent=2))
