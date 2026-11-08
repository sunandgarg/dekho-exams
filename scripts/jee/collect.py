"""Discover and collect one JEE archive in chapter, question, paper and PDF order."""
import concurrent.futures
import gzip
import json
import os
import re
import subprocess
import threading
import time
from urllib.parse import urlsplit
from urllib.robotparser import RobotFileParser
from archive import BASE, CACHE, EXAM, ROOT, UA, cls, doc, fetch, origin, strip

hub = f'/past-years/jee/{EXAM}'
paper_hub = f'/past-years/year-wise/jee/{EXAM}'
cache_dir = CACHE/'index'
cache_dir.mkdir(parents=True, exist_ok=True)
rules = {}
stop = threading.Event()

def rules_for(host):
    rule = RobotFileParser()
    rule.parse(subprocess.check_output(['curl','-fsS','--max-time','25','-A',UA,host+'/robots.txt']).decode().splitlines())
    rules[host] = rule

def page(path, host=BASE):
    url = host + path
    if not rules[host].can_fetch(UA,url) or stop.is_set():
        raise RuntimeError(f'Collection stopped at {url}')
    file = cache_dir / (('pdf' if host != BASE else '') + path.replace('/','_')+'.gz')
    if not file.exists():
        response = subprocess.run(['curl','--compressed','-sS','-A',UA,'--max-time','40','-w','%{http_code}',url],capture_output=True)
        body,status = response.stdout[:-3],response.stdout[-3:]
        if status in (b'403',b'429'):stop.set()
        if status!=b'200':raise RuntimeError((path,status))
        file.write_bytes(gzip.compress(body,compresslevel=3))
        time.sleep(.2)
    return doc(gzip.decompress(file.read_bytes()))

def save(name,value):
    (ROOT/'src/data'/f'{EXAM}-{name}.json').write_text(json.dumps(value,ensure_ascii=False,indent=1)+'\n')

def collect():
    rules_for(origin(BASE))
    subjects={}
    for card in cls(page(hub),'chapter-card'):
        path=card.get('href','')
        if not re.fullmatch(hub+r'/[a-z0-9-]+/[a-z0-9-]+',path):raise ValueError(path)
        subject,chapter=path.split('/')[-2:]
        subjects.setdefault(subject,[]).append(chapter)
    assert set(subjects)=={'physics','chemistry','mathematics'}
    save('chapters',subjects)
    paths=[hub+'/'+s for s in subjects]+[hub+'/'+s+'/'+c for s,cs in subjects.items() for c in cs]
    with concurrent.futures.ThreadPoolExecutor(max_workers=3) as pool:
        for _ in pool.map(page,paths):pass
    print('Chapters collected', {s:len(cs) for s,cs in subjects.items()},flush=True)
    fetch()
    fetch('hi')
    print('Chapter question groups collected. Reading papers.',flush=True)
    paper_index=page(paper_hub)
    paper_slugs={a.get('href').split('/')[-1] for a in paper_index.xpath('//a[@href]') if re.fullmatch(paper_hub+r'/[a-z0-9-]+',a.get('href'))}
    assert paper_slugs
    with concurrent.futures.ThreadPoolExecutor(max_workers=3) as pool:
        for _ in pool.map(page,[paper_hub+'/'+slug for slug in sorted(paper_slugs)]):pass
    pdf_host=origin(os.environ['JEE_PDF_ORIGIN'])
    rules_for(pdf_host)
    papers=[]
    for row in cls(page(paper_hub,pdf_host),'paper'):
        anchor=cls(row,'paper-title')[0]
        slug=urlsplit(anchor.get('href')).path.split('/')[-1]
        variants=[]
        for download in row.xpath('.//a[@data-pdf-download="paper"]'):
            path=urlsplit(download.get('href')).path
            assert path.startswith(f'/download/paper/jee/{EXAM}/{slug}/')
            variants.append(path.split('/')[-1])
        papers.append(dict(slug=slug,title=strip(anchor),date=strip(cls(row,'paper-meta')[0]),variants=variants))
    assert {p['slug'] for p in papers}==paper_slugs
    save('papers',papers)
    print('Paper inventory',len(papers),'PDF editions',sum(len(p['variants']) for p in papers),flush=True)
    from chapters import main
    main()

if __name__=='__main__':collect()
