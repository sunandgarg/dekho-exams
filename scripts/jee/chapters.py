"""Publish chapter statistics from the cached chapter directory."""
import gzip, json
from archive import EXAM, ROOT, CACHE, doc, cls, strip, dump

def main():
 chapters=json.loads((ROOT/f'src/data/{EXAM}-chapters.json').read_text())
 hub=f'/past-years/jee/{EXAM}'
 def page(path):
  return doc(gzip.decompress((CACHE/'index'/(path.replace('/','_')+'.gz')).read_bytes()))
 cards={a.get('href'):a for a in cls(page(hub),'chapter-card')}
 data={}
 for subject,slugs in chapters.items():
  for chapter in slugs:
   key=subject+'/'+chapter
   path=hub+'/'+key
   stats=[[strip(x) for x in row.xpath('td')] for t in cls(page(path),'cp-table') for row in t.xpath('.//tbody/tr')]
   card=cards[path];cunits=card.getparent().getparent().xpath('.//h3')
   data[key]=dict(name=strip(cls(card,'cc-title')[0]),latest=strip(cls(card,'cc-stats')[0]) if cls(card,'cc-stats') else '',unit=strip(cunits[0]) if cunits else '')
   dump('meta/'+key,{'stats':stats})
 (ROOT/f'src/data/{EXAM}-chapter-meta.json').write_text(json.dumps(dict(sorted(data.items())),indent=1,ensure_ascii=False)+'\n')

if __name__=='__main__':main()
