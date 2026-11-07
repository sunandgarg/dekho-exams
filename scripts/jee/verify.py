"""Check every published archive route, adjacent question, sprite glyph and paper cross-link."""
from pathlib import Path
from collections import Counter
import gzip,json,re,hashlib
root=Path(__file__).resolve().parents[2]
out=root/'public/jee-archive'
def read(p):return json.loads(gzip.decompress(p.read_bytes()))
qs={}; stats=Counter();glyphs=set(re.findall(r'id="([^"]+)"',(out/'math.svg').read_text()))
for f in (out/'q').glob('*.bin'):
 for k,q in read(f).items():
  assert hashlib.sha256(k.encode()).hexdigest()[:3]==f.stem,(k,f)
  assert q['slug']==k and k not in qs
  assert re.fullmatch(r'[A-Za-z0-9-]+(?:\.htm)?',k),k
  for edition in [q]+([q['hi']] if q.get('hi') else []):
   h=''.join([edition['body'],edition['solution'],*edition['options']])
   assert not re.search(r'<(?:script|iframe)\b|<[a-z][^<>]*\son[a-z]+\s*=',h,re.I),k
   assert set(re.findall(r'/jee-archive/math\.svg#([\w-]+)',h))<=glyphs,k
  payload=hashlib.sha256(json.dumps([q['body'],q['options'],q['solution'],q.get('hi'),q.get('numericKey'),q.get('choiceKey')],ensure_ascii=False).encode()).hexdigest()
  qs[k]=(q['chapter'],q['paper'],q['prev'],q['next'],q.get('canonical'),q.get('qid'),payload)
  kind='chapter' if q['chapter'] else 'paper'
  stats[kind]+=1;stats[kind+' detailed']+=bool(q['complete']);stats[kind+' explanations']+=bool(q['solution']);stats[kind+' Hindi']+=bool(q.get('hi'));stats[kind+' numerical keys']+=q.get('numericKey') is not None;stats[kind+' choice keys']+=q.get('choiceKey') is not None
for name in ('chapter','paper'):
 for f in (out/name).rglob('*.bin'):
  rows=read(f);ids=[x['id'] for x in rows]
  assert len(set(ids))==len(ids)
  for i,k in enumerate(ids):
   ch,pa,prev,nxt,canonical,qid,payload=qs[k]
   assert (ch if name=='chapter' else pa)==f.stem
   assert (prev,nxt)==(ids[i-1] if i else None,ids[i+1] if i+1<len(ids) else None)
   if canonical:assert qs[canonical][1]==pa and qs[canonical][5]==k and qs[canonical][6]==payload,(k,canonical)
stats['chapters']=len(list((out/'chapter').rglob('*.bin')))
stats['papers']=len(list((out/'paper').glob('*.bin')))
assert (stats['chapters'],stats['chapter'],stats['papers'],stats['paper'])==(95,18006,202,15280)
for f in (out/'print').rglob('*.bin'):
 h=gzip.decompress(f.read_bytes())
 owner=f.parent.name
 list_file=out/'chapter'/(owner.replace('--','/')+'.bin') if '--' in owner else out/'paper'/(owner+'.bin')
 assert h.count(b'<article>')==len(read(list_file)),f
 stats['print '+f.stem]+=1
assert stats['chapter detailed']==stats['chapter'] and stats['paper detailed']==stats['paper']
print(json.dumps(stats,indent=2))
