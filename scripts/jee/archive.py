"""Collect public JEE Main question groups from a cached chapter and paper inventory.
Run with Python + lxml. JEE_CACHE points to the folder containing index/*.gz.
Fetch: archive.py fetch; build: archive.py build. Never request PDF download endpoints.
"""
import collections, concurrent.futures, gzip, hashlib, html as escapehtml, json, os, re, subprocess, sys, threading, time
from pathlib import Path
from collections.abc import MutableMapping
import zlib
from urllib.parse import urlsplit
from urllib.robotparser import RobotFileParser
from lxml import html, etree
ROOT=Path(__file__).resolve().parents[2]; CACHE=Path(os.environ['JEE_CACHE']); EXAM=os.environ.get('JEE_EXAM','jee-main')
if EXAM not in ('jee-main','jee-advanced'):raise ValueError('Unsupported JEE archive')
EXAM_NAME={'jee-main':'JEE Main','jee-advanced':'JEE Advanced'}[EXAM]
ASSETS='jee-archive' if EXAM=='jee-main' else 'jee-advanced-archive'
OUT=ROOT/'public'/ASSETS
QUESTION_REDIRECTS=json.loads((ROOT/'src/data/jee-question-redirects.json').read_text())
ORIGINAL_SLUGS={v:k for k,v in QUESTION_REDIRECTS.items()}
BASE=os.environ.get('JEE_CONTENT_ORIGIN','').rstrip('/')
def origin(value):
 parsed=urlsplit(value)
 if parsed.scheme!='https' or not parsed.hostname or parsed.path or parsed.username or parsed.password or parsed.query or parsed.fragment:raise ValueError('Set an HTTPS catalog origin before collecting pages.')
 return value
UA='DekhoexamsImport/1.0 (OpenAI Codex; user-directed JEE Main catalog; +https://dekhoexams.com)'
parser=html.HTMLParser(huge_tree=True,encoding='utf-8')
def doc(data):return html.fromstring(data,parser=parser)
def cls(node,name):return node.xpath('.//*[contains(concat(" ",normalize-space(@class)," ")," '+name+' ")]')
def rows(subject,slug):
 path=CACHE/'index'/(f'_past-years_jee_{EXAM}_'+subject+'_'+slug+'.gz')
 return cls(doc(gzip.decompress(path.read_bytes())),'preview-row')
def batches():
 chapters=json.loads((ROOT/f'src/data/{EXAM}-chapters.json').read_text())
 for subject,chap in chapters.items():
  for slug in chap:
   groups=collections.defaultdict(list)
   for row in rows(subject,slug):
    groups[row.getparent().getparent().get('id')].append(row.get('href'))
   for group,links in groups.items():
    for i in range(0,len(links),4):yield (subject,slug,group,i,links[i:i+4])
def key(path):return hashlib.sha256(path.encode()).hexdigest()[:24]
def fetch(lang="en", jobs=None, reverse=False):
 origin(BASE)
 rules=RobotFileParser()
 rules.parse(subprocess.check_output(['curl','-fsSL','-A',UA,BASE+'/robots.txt']).decode().splitlines())
 stop=threading.Event(); dest=CACHE/('detail' if lang=='en' else 'hindi');dest.mkdir(exist_ok=True)
 def get(batch):
  path=batch[-1][0];out=dest/(key(path)+'.gz')
  if out.exists() or stop.is_set():return
  url=BASE+path+("?lang=hi" if lang=="hi" else "")
  if not rules.can_fetch(UA,url): raise ValueError('robots exclusion: '+path)
  res=subprocess.run(['curl','--compressed','--max-time','40','-sS','-w','%{http_code}','-A',UA,url],capture_output=True)
  data,status=res.stdout[:-3],res.stdout[-3:]
  if status in (b'403',b'429'):stop.set();raise RuntimeError('server declined '+str(status))
  if status!=b'200' or b'data-qid=' not in data:return
  q=doc(data); blocks=q.xpath('//*[@data-question][@data-qid]')
  # Store question components and the definitions needed by their math, never page scripts or navigation.
  defs=q.xpath('//defs/path[@id]')
  data=etree.tostring(html.Element('div'),encoding='utf-8') if not blocks else b'<div>'+b''.join(etree.tostring(n,method='html',encoding='utf-8',with_tail=False) for n in [*defs,*blocks])+b'</div>'
  tmp=out.with_suffix('.'+str(os.getpid())+'.tmp');tmp.write_bytes(gzip.compress(data,compresslevel=3));tmp.replace(out)
  time.sleep(.25)
 with concurrent.futures.ThreadPoolExecutor(max_workers=4 if lang=="en" else 3) as pool:
  groups=batches() if jobs is None else ((None,None,None,None,[path]) for path in jobs)
  if reverse:groups=reversed(list(groups)[3000:])
  for i,_ in enumerate(pool.map(get,groups),1):
   if i%300==0:print(i,flush=True)
def index():
 origin(BASE)
 # Known inventory paths are validated before use; do not discover other exams or private pages.
 chapters=json.loads((ROOT/f'src/data/{EXAM}-chapters.json').read_text())
 papers=json.loads((ROOT/f'src/data/{EXAM}-papers.json').read_text())
 hub=f'/past-years/jee/{EXAM}';paperhub=f'/past-years/year-wise/jee/{EXAM}'
 paths=[hub,*[hub+'/'+s for s in chapters],*[hub+'/'+s+'/'+c for s,cs in chapters.items() for c in cs],paperhub,*[paperhub+'/'+p['slug'] for p in papers]]
 rules=RobotFileParser();rules.parse(subprocess.check_output(['curl','-fsSL','-A',UA,BASE+'/robots.txt']).decode().splitlines())
 dest=CACHE/'index';dest.mkdir(exist_ok=True,parents=True)
 for path in paths:
  out=dest/(path.replace('/','_')+'.gz');url=BASE+path
  if out.exists():continue
  if not rules.can_fetch(UA,url):raise ValueError('robots exclusion: '+path)
  data=subprocess.check_output(['curl','--compressed','-fsS','--max-time','40','-A',UA,url])
  out.write_bytes(gzip.compress(data,compresslevel=3));time.sleep(.25)
if __name__=='__main__' and sys.argv[1]=='fetch':fetch()
if __name__=='__main__' and sys.argv[1]=='hindi':fetch('hi')
if __name__=='__main__' and sys.argv[1]=='index':index()
if __name__=='__main__' and sys.argv[1]=='hindi-reverse':fetch('hi',reverse=True)
if __name__=='__main__' and sys.argv[1]=='reconcile':
 english=set()
 hindi=set()
 for file in sorted((OUT/'q').glob('*.bin')):
  for q in json.loads(gzip.decompress(file.read_bytes())).values():
   path='/past-years/jee/question/'+ORIGINAL_SLUGS.get(q['slug'],q['slug']) if q['chapter'] else f'/past-years/year-wise/jee/{EXAM}/'+q['paper']+'/'+q['slug']
   if not q['complete']:english.add(path)
   if not q.get('hi'):hindi.add(path)
 print('Pending exact detail URLs',len(english),'English and',len(hindi),'Hindi',flush=True)
 if english:fetch(jobs=sorted(english))
 if hindi:fetch('hi',jobs=sorted(hindi))

# Only semantic content and the small SVG vocabulary used for mathematics survive import.
TAGS=set('p br div span em i u b strong sup sub table thead tbody tr td th ul ol li blockquote pre code h3 h4 img svg g use path rect line polygon polyline circle ellipse text tspan'.split())
SVGTAGS=set('svg g use path rect line polygon polyline circle ellipse text tspan'.split())
GLYPHS={}
def esc(x):return escapehtml.escape(x or '',quote=True)
def glyphs(tree):
 for n in tree.xpath('//path[@id][@d]'):
  if re.fullmatch(r'MJX-[a-zA-Z0-9_-]+',n.get('id')):GLYPHS[n.get('id')]=n.get('d')
def figure(src,alt):
 # Only reviewed, local figures can appear in practice or print. Keep the ID for matching a replacement.
 id=key(src)
 # A shared source URL can have different English and Hindi drawings in the tagged paper.
 tagged=key(id+'\n'+(alt or ''))
 if (ROOT/'public/jee-figures'/(tagged+'.png')).is_file():id=tagged
 if (ROOT/'public/jee-figures'/(id+'.png')).is_file():
  return '<img src="/jee-figures/'+id+'.png" alt="'+esc(alt or 'Question diagram')+'" loading="lazy">'
 return '<span class="jee-figure-pending" data-figure="'+id+'">Diagram pending · चित्र उपलब्ध नहीं है</span>'
def markup(n):
 if not isinstance(n.tag,str) or n.tag in ('script','style','iframe','object','template'):return ''
 tag=n.tag
 children=esc(n.text)+''.join(markup(e)+esc(e.tail) for e in n)
 if tag not in TAGS:return children
 attr={}
 if tag in SVGTAGS:
  for k,v in n.attrib.items():
   if k=='href' and re.fullmatch(r'#MJX-[a-zA-Z0-9_-]+',v):attr[k]=f'/{ASSETS}/math.svg'+v
   elif k in ('fill','stroke') and v in ('none','currentColor','black','white'):attr[k]=v
   elif k in ('width','height','viewbox','transform','stroke-width','d','x','y','x1','x2','y1','y2','points','cx','cy','rx','ry','r','font-size','dx','dy','text-anchor') and re.fullmatch(r'[a-zA-Z0-9()+.,% eE\-]*',v):attr['viewBox' if k=='viewbox' else k]=v
  if tag=='svg':
   chars=[]
   for u in n.xpath('.//use/@href'):
    try:chars.append(chr(int(u.rsplit('-',1)[1],16)))
    except (ValueError,OverflowError):pass
   attr.update(role='img',**{'aria-label':''.join(chars) or 'Mathematical expression'})
 if tag=='img':return figure(n.get('src',''),n.get('alt',''))
 if tag in ('td','th'):
  for k in ('rowspan','colspan'):
   if n.get(k,'').isdigit():attr[k]=n.get(k)
 a=''.join(' '+k+'="'+esc(v)+'"' for k,v in attr.items())
 return '<'+tag+a+'>'+('' if tag in ('br','img') else children+'</'+tag+'>')
def strip(n):return ' '.join(n.text_content().split())
def plain(n):
 # Teasers include the characters in formulae rather than silently deleting mathematics.
 vals=n.xpath('.//text()[not(ancestor::svg)] | .//use/@href');parts=[]
 for v in vals:
  if v.startswith('#MJX-'):
   try:v=chr(int(v.rsplit('-',1)[1],16))
   except (ValueError,OverflowError):v=''
  parts.append(v)
 return ' '.join(''.join(parts).split())[:260] or 'Open the question to view the diagram.'
def dump(rel,data):
 path=OUT/(rel+'.bin');path.parent.mkdir(parents=True,exist_ok=True)
 path.write_bytes(gzip.compress(json.dumps(data,ensure_ascii=False,separators=(',',':')).encode(),compresslevel=6,mtime=0))
def bucket(s):return hashlib.sha256(s.encode()).hexdigest()[:3]
def choice_key(text):
 # A final, explicitly labelled option is a published key. Do not infer one from a calculation.
 text=' '.join(text.split());suffix=r'[.!)\s]*$'
 for pattern in (r'(?:correct (?:option|choice) is|correct answer is (?:option|choice))\s*[:\-]?\s*[\[(]?([A-D1-4])[\])]?',r'(?:option|choice)\s*[\[(]?([A-D1-4])[\])]?\s+is (?:the )?correct(?: (?:answer|option|choice))?'):
  m=re.search(r'\b'+pattern+suffix,text,re.I)
  if m:
   key=m[1].upper();return int(key)-1 if key.isdigit() else ord(key)-65
 return None
assert choice_key('Hence, the correct option is (C).')==2
assert choice_key('Option B is correct but Option A is also true.') is None
assert choice_key('The answer is 2.') is None
def multiple_choice_key(text,option_count):
 # Require the final statement to explicitly list the correct choices together.
 sequence=r'[(\[]?[A-D][)\]]?(?:(?:\s*,\s*(?:and\s+)?|\s+and\s+|\s*&\s*)[(\[]?[A-D][)\]]?)+'
 for pattern in (r'(?:hence|therefore|thus|so)[,:]?\s+options\s+('+sequence+r')\s+are correct',r'(?:the )?correct options are\s*[:\-]?\s*('+sequence+r')'):
  match=re.search(r'\b'+pattern+r'[.!\s]*$',text,re.I)
  if match:
   letters=[ord(v.upper())-65 for v in re.findall(r'\b([A-D])\b',match[1],re.I)]
   if len(set(letters))==len(letters) and len(letters)>1 and max(letters)<option_count:return sorted(letters)
 return None
assert multiple_choice_key('Hence, options (A) and (D) are correct.',4)==[0,3]
assert multiple_choice_key('Option A is correct. Option C is correct.',4) is None
def body_html(body):
 result=[]
 for node in cls(body,'q-prose'):
  content=markup(node)
  if 'q-aside' in node.get('class','').split():
   content='<aside class="jee-passage" aria-label="Shared passage">'+content+'</aside>'
  result.append(content)
 return ''.join(result)
def explanation(result):
 blocks=[]
 for container in result:
  for section in cls(container,'q-section'):
   heads=cls(section,'q-section-title')
   for node in cls(section,'q-prose'):
    if heads and strip(heads[0])=='Answer' and re.fullmatch(r'correct answer is (?:solve it|(?:solve|do)(?: it)? (?:by )?yourself)[.! ]*',strip(node),re.I):
     continue
    blocks.append(markup(node))
 return ''.join(blocks)
class PackedRecords(MutableMapping):
 # Formula-rich Unicode strings expand considerably in memory. Keep only the records being written uncompressed.
 def __init__(self):self.data={}
 def __getitem__(self,k):return json.loads(zlib.decompress(self.data[k]))
 def __setitem__(self,k,v):self.data[k]=zlib.compress(json.dumps(v,ensure_ascii=False,separators=(',',':')).encode(),1)
 def __delitem__(self,k):del self.data[k]
 def __contains__(self,k):return k in self.data
 def __iter__(self):return iter(self.data)
 def __len__(self):return len(self.data)
def build():
 lists={}; questions=PackedRecords(); alias={}; details=PackedRecords(); missing=collections.Counter()
 chapters=json.loads((ROOT/f'src/data/{EXAM}-chapters.json').read_text())
 papers=json.loads((ROOT/f'src/data/{EXAM}-papers.json').read_text())
 for p in (CACHE/'detail').glob('*.gz'):
  d=doc(gzip.decompress(p.read_bytes())); glyphs(d)
  for q in d.xpath('//*[@data-qid]'):
   body=cls(q,'q-body')[0];res=cls(q,'q-result')
   prose=cls(body,'q-prose')
   stem=next(node for node in prose if 'q-aside' not in node.get('class','').split())
   item=dict(qid=q.get('data-qid'),body=body_html(body),options=[markup(n) for n in cls(q,'option-content')],solution=explanation(res),kind=q.get('data-type'),finger=plain(stem))
   if q.get('data-type')=='mcq' and len(item['options'])==4:
    explicit=choice_key(' '.join(strip(r) for r in res))
    if explicit is not None:item['choiceKey']=explicit
   if q.get('data-type')=='mcqm':
    keys=multiple_choice_key(' '.join(strip(r) for r in res),len(item['options']))
    if keys:item['choiceKeys']=keys
   if q.get('data-type')=='t/f' and len(item['options'])==2:
    text=' '.join(strip(r) for r in res)
    explicit=choice_key(text)
    if explicit is None:
     truth=re.search(r'(?:given |above )?statement is (true|false)[.! ]*$',text,re.I)
     opts=[strip(n).strip('. ').lower() for n in cls(q,'option-content')]
     if truth and sorted(opts)==['false','true']:explicit=opts.index(truth[1].lower())
    if explicit in (0,1):item['choiceKey']=explicit
   for h in cls(q,'q-section-title'):
    if strip(h)!='Answer' or q.get('data-type')!='integer':continue
    prose=cls(h.getparent(),'q-prose')
    answer=re.fullmatch(r'Correct answer is\s+([+-]?(?:\d+(?:\.\d+)?|\.\d+))\s*\.?',strip(prose[0]),re.I) if prose else None
    if answer:item['numericKey']=float(answer[1])
    elif prose:
     number=r'([+-]?(?:\d+(?:\.\d+)?|\.\d+))'
     interval=re.fullmatch(r'Correct answer is\s+'+number+r'\s+to\s+'+number+r'\.?',strip(prose[0]),re.I)
     if interval and float(interval[1])<=float(interval[2]):item['numericRange']=[float(interval[1]),float(interval[2])]
   details[q.get('data-qid')]=item
 for p in (CACHE/'hindi').glob('*.gz'):
  d=doc(gzip.decompress(p.read_bytes()));glyphs(d)
  for q in d.xpath('//*[@data-qid]'):
   en=details.get(q.get('data-qid'));body=cls(q,'q-body')[0]
   # Both language editions were inspected: these two contain only mathematical or chemical notation.
   notation_only = EXAM=='jee-main' and q.get('data-qid') in {'1ldpo9hzf','U1oLUueqALYqitPf'}
   translated = any(re.search(r'[ऀ-ॿ]',v.text_content()) for v in [body,*cls(q,'option-content'),*cls(q,'q-result')])
   if not en or not (translated or notation_only):continue
   res=cls(q,'q-result');en['hi']=dict(body=body_html(body),options=[markup(n) for n in cls(q,'option-content')],solution=explanation(res))
   details[q.get('data-qid')]=en
 # Exact paper IDs take precedence. Use paper + question text only if it identifies one question.
 fingerprints=collections.defaultdict(set); titles={p['title']:p['slug'] for p in papers}
 for p in papers:
  slug=p['slug'];d=doc(gzip.decompress((CACHE/'index'/(f'_past-years_year-wise_jee_{EXAM}_'+slug+'.gz')).read_bytes()));glyphs(d)
  ls=[]
  for r in cls(d,'preview-row'):
   qid=r.get('href').split('/')[-1]; b=cls(r,'preview-body')[0];teaser=plain(b)
   g=r.getparent().getparent();subject=g.xpath('.//h2/text()')[0].strip().lower()
   fingerprints[(slug,teaser)].add(qid)
   ls.append(dict(id=qid,teaser=teaser,group=subject,paper=p['title']))
   rec=dict(slug=qid,teaser=teaser,paper=slug,subject=subject,chapter='',kind='',body=markup(b),options=[],solution='',complete=False)
   if qid in details:rec.update(details[qid],complete=True)
   questions[qid]=rec
  lists['paper/'+slug]=ls
 for subject,chaps in chapters.items():
  for chapter in chaps:
   d=doc(gzip.decompress((CACHE/'index'/(f'_past-years_jee_{EXAM}_'+subject+'_'+chapter+'.gz')).read_bytes()));glyphs(d)
   ls=[]; groups=collections.defaultdict(list)
   for row in cls(d,'preview-row'):
    href=row.get('href'); original=href.split('/')[-1]; slug=QUESTION_REDIRECTS.get(original,original); b=cls(row,'preview-body')[0];group=row.getparent().getparent().get('id')
    teaser=plain(b);paper=strip(cls(row,'preview-meta')[0]);ps=titles.get(paper,'')
    groups[group].append((href,slug,b,teaser,paper,ps))
   for group,gr in groups.items():
    for offset in range(0,len(gr),4):
     batch=gr[offset:offset+4]
     src=CACHE/'detail'/(key(batch[0][0])+'.gz');ids=[]
     if src.exists():ids=doc(gzip.decompress(src.read_bytes())).xpath('//*[@data-qid]/@data-qid')
     for j,(href,slug,b,teaser,paper,ps) in enumerate(batch):
      qid=ids[j] if j<len(ids) and details.get(ids[j],{}).get('finger')==teaser else None
      matches=fingerprints[(ps,teaser)]
      if not qid and len(matches)==1:qid=next(iter(matches))
      if not qid or qid not in details:
       direct=CACHE/'detail'/(key(href)+'.gz')
       if direct.exists():
        direct_ids=doc(gzip.decompress(direct.read_bytes())).xpath('//*[@data-qid]/@data-qid')
        if direct_ids and details.get(direct_ids[0],{}).get('finger')==teaser:qid=direct_ids[0]
      if not ps and qid and qid in questions and not questions[qid]['chapter']:ps=questions[qid]['paper']
      rec=dict(slug=slug,teaser=teaser,paper=ps,subject=subject,chapter=chapter,kind=group,body=markup(b),options=[],solution='',complete=False)
      if qid in details and details[qid]['finger']==teaser:rec.update(details[qid],complete=True)
      if rec['complete'] and qid and ps and qid in questions and questions[qid]['paper']==ps:alias[qid]=slug
      if not rec['complete']:missing[subject]+=1
      rec['paperTitle']=paper;questions[slug]=rec
      ls.append(dict(id=slug,teaser=teaser,group=group,paper=paper))
   lists['chapter/'+subject+'/'+chapter]=ls
 if EXAM=='jee-main':
  # The supplied paper editions place the extra chapter records after the original paper listing.
  for paper,slugs in json.loads((ROOT/'scripts/jee/paper-supplements.json').read_text()).items():
   rows=lists['paper/'+paper];ids={r['id'] for r in rows};extra=[]
   for slug in slugs:
    q=questions[slug];qid=q['qid'];assert q['complete'] and q['paper']==paper
    extra.append(qid)
    if qid not in ids:
     assert qid not in questions
     rows.append(dict(id=qid,teaser=q['teaser'],group=q['subject'],paper=q['paperTitle']))
     questions[qid]=dict(q,slug=qid,chapter='');ids.add(qid)
    alias[qid]=slug
   assert [r['id'] for r in rows[-len(extra):]]==extra
 for qid,slug in alias.items():
  if questions[qid]['complete'] and not questions[slug]['complete']:raise ValueError('unexpected unresolved match '+qid)
  rec=questions[qid];rec['canonical']=slug;questions[qid]=rec
 # Adjacency belongs to the student's chosen chapter or paper.
 for route,ls in lists.items():
  for i,x in enumerate(ls):
   rec=questions[x['id']];rec['prev']=ls[i-1]['id'] if i else None;rec['next']=ls[i+1]['id'] if i+1<len(ls) else None;questions[x['id']]=rec
  dump(route,ls)
 shards=collections.defaultdict(list)
 for id in questions:shards[bucket(id)].append(id)
 for k,ids in shards.items():
  records={id:questions[id] for id in ids}
  for q in records.values():q.pop('finger',None)
  dump('q/'+k,records)
 (OUT/'math.svg').write_text('<svg xmlns="http://www.w3.org/2000/svg"><defs>'+''.join('<path id="'+esc(k)+'" d="'+esc(v)+'"/>' for k,v in sorted(GLYPHS.items()))+'</defs></svg>')
 counts={k:len(v) for k,v in lists.items() if k.startswith('chapter/')}
 (ROOT/f'src/data/{EXAM}-counts.json').write_text(json.dumps(counts,indent=1)+'\n')
 print_editions(lists,questions,papers)
 print('published numerical keys',sum('numericKey' in v for v in details.values()),'explicit choice keys',sum('choiceKey' in v for v in details.values()),flush=True)
 print('Hindi question IDs',sum('hi' in v for v in details.values()),'English with explanations',sum(bool(v['solution']) for v in details.values()),flush=True)
 print('chapter question listings',sum(counts.values()),'paper listings',sum(len(v) for k,v in lists.items() if k.startswith('paper/')),'detail IDs',len(details),'chapter incomplete',dict(missing),'matched paper aliases',len(alias),flush=True)
def print_editions(lists,questions,papers):
 hindi_print=[]
 meta=json.loads((ROOT/f'src/data/{EXAM}-chapter-meta.json').read_text())
 editions=[(p['slug'],p['title'],p['date'],f'/past-years/year-wise/jee/{EXAM}/'+p['slug'],lists['paper/'+p['slug']]) for p in papers]
 editions.extend((k.replace('/','--'),EXAM_NAME+' · '+v['name'],v['unit'],f'/past-years/jee/{EXAM}/'+k,lists['chapter/'+k]) for k,v in meta.items())
 for edition,title,byline,link,rows in editions:
  for lang in ('en','hi'):
   recs=[questions[r['id']] for r in rows]
   if lang=='hi' and not any(q.get('hi') for q in recs):continue
   if lang=='hi':hindi_print.append(edition)
   parts=['<!doctype html><html lang="'+lang+'"><meta charset="utf-8"><meta name="viewport" content="width=device-width,initial-scale=1"><meta name="robots" content="noindex,follow"><title>'+esc(title)+' | Dekhoexams</title><link rel="stylesheet" href="/jee-print.css"><script defer src="/jee-print.js"></script><header><strong><img class="edition-logo" src="/dekhoexams-icon.svg" alt=""> Dekhoexams</strong><h1>'+esc(title)+'</h1><p>'+esc(byline)+' · '+str(len(rows))+(' question · ' if len(rows)==1 else ' questions · ')+('Hindi' if lang=='hi' else 'English')+'</p><nav><a href="'+esc(link)+'">Online practice</a> <label><input type="checkbox" id="print-solutions"> Include solutions</label> <button type="button">Print / Save as PDF</button></nav></header>']
   if any('jee-figure-pending' in part for q in recs for item in [q.get('hi',q) if lang=='hi' else q] for part in [item['body'],*item['options'],item['solution']]):
    parts.append('<p class="figure-notice">'+('कुछ चित्र अभी उपलब्ध नहीं हैं। उनके स्थान पर सूचना दी गई है।' if lang=='hi' else 'Some diagrams are pending. Each missing figure is marked in the edition.')+'</p>')
   last=''
   for i,(q,r) in enumerate(zip(recs,rows),1):
    if r['group']!=last:last=r['group'];parts.append('<h2>'+esc({'mcq':'Single correct','integer':'Numerical','mcqm':'Multiple correct'}.get(last,last.title()))+'</h2>')
    item=q.get('hi',q) if lang=='hi' else q
    parts.append('<article><h3>Q'+str(i)+'</h3>'+('<small>'+esc(r['paper'])+'</small>' if '--' in edition else '')+('<small>English · Hindi unavailable</small>' if lang=='hi' and 'hi' not in q else '')+item['body']+'<ol type="A">'+''.join('<li>'+a+'</li>' for a in item['options'])+'</ol><section class="print-solution"><h4>'+('हल' if lang=='hi' else 'Solution')+'</h4>'+item['solution']+'</section></article>')
   parts.append('</html>');path=OUT/'print'/edition/(lang+'.bin');path.parent.mkdir(parents=True,exist_ok=True);path.write_bytes(gzip.compress(''.join(parts).replace('loading="lazy"','loading="eager"').encode(),compresslevel=6,mtime=0))
 (ROOT/f'src/data/{EXAM}-hindi-print.json').write_text(json.dumps(hindi_print,indent=1)+'\n')

def reprint():
 from functools import lru_cache
 @lru_cache(maxsize=32)
 def shard(prefix):
  return json.loads(gzip.decompress((OUT/'q'/(prefix+'.bin')).read_bytes()))
 class PublishedQuestions:
  def __getitem__(self,id):return shard(bucket(id))[id]
 lists={str(f.relative_to(OUT).with_suffix('')):json.loads(gzip.decompress(f.read_bytes())) for folder in ('chapter','paper') for f in (OUT/folder).rglob('*.bin')}
 papers=json.loads((ROOT/f'src/data/{EXAM}-papers.json').read_text())
 print_editions(lists,PublishedQuestions(),papers)
if __name__=='__main__' and sys.argv[1]=='build':build()
if __name__=='__main__' and sys.argv[1]=='print':reprint()
