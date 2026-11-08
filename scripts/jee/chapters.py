"""Import JEE Main historical chapter statistics and permitted PDF catalog metadata."""
from archive import EXAM,ROOT,CACHE,UA,doc,cls,strip,dump,origin
from urllib.robotparser import RobotFileParser
import concurrent.futures, gzip,json,os,re,subprocess,threading,time
from urllib.parse import urlsplit
def main():
 host=origin(os.environ.get('JEE_PDF_ORIGIN','').rstrip('/'))
 chapters=json.loads((ROOT/f'src/data/{EXAM}-chapters.json').read_text())
 h=doc(gzip.decompress((CACHE/f'index/_past-years_jee_{EXAM}.gz').read_bytes()))
 cards={a.get('href'):a for a in cls(h,'chapter-card')}
 data={}
 rules=RobotFileParser();rules.parse(subprocess.check_output(['curl','-fsSL','-A',UA,host+'/robots.txt']).decode().splitlines())
 dest=CACHE/'chapterpdf';dest.mkdir(exist_ok=True);stop=threading.Event()
 def process(sc):
  s,c=sc;path=f'/past-years/jee/{EXAM}/'+s+'/'+c;url=host+path;out=dest/(s+'_'+c+'.gz')
  if stop.is_set():return
  if not rules.can_fetch(UA,url):raise ValueError(url)
  if not out.exists():
   res=subprocess.run(['curl','--compressed','-sS','-A',UA,'--max-time','30','-w','%{http_code}',url],capture_output=True)
   if res.stdout[-3:] in (b'403',b'429'):stop.set();raise RuntimeError('server declined')
   if res.stdout[-3:]!=b'200':raise ValueError((url,res.stdout[-3:]))
   out.write_bytes(gzip.compress(res.stdout[:-3],compresslevel=3));time.sleep(.3)
  pdf=doc(gzip.decompress(out.read_bytes()));editions={}
  for a in pdf.xpath('//a[contains(@href,"/download/")]'):
   u=urlsplit(a.get('href'))
   if u.netloc or not u.path.startswith('/download/') or not u.path.endswith('.pdf'):continue
   editions[u.path]=strip(a)
  d=doc(gzip.decompress((CACHE/'index'/(path.replace('/','_')+'.gz')).read_bytes()))
  stats=[[strip(x) for x in row.xpath('td')] for t in cls(d,'cp-table') for row in t.xpath('.//tbody/tr')]
  card=cards[path];cunits=card.getparent().getparent().xpath('.//h3')
  data[s+'/'+c]=dict(name=strip(cls(card,'cc-title')[0]),unit=strip(cunits[0]) if cunits else '',latest=strip(cls(card,'cc-stats')[0]) if cls(card,'cc-stats') else '',stats=stats,pdfs=editions)
 with concurrent.futures.ThreadPoolExecutor(max_workers=2) as pool:list(pool.map(process,[(s,c) for s,cs in chapters.items() for c in cs]))
 (ROOT/f'src/data/{EXAM}-chapter-meta.json').write_text(json.dumps({k:{'name':v['name'],'latest':v['latest'],'unit':v['unit']} for k,v in sorted(data.items())},indent=1,ensure_ascii=False)+'\n')
 for k,v in data.items():dump('meta/'+k,{'stats':v['stats'],'pdfs':v['pdfs']})
 print(len(data),'chapters',sum(len(v['pdfs']) for v in data.values()),'PDF edition links')
if __name__=='__main__':main()
