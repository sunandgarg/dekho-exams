"""Check canonical Python curricula and execute exact public programs in isolation."""
import ast, html, json, pathlib, re, subprocess, sys, tempfile
from html.parser import HTMLParser
ROOT=pathlib.Path(__file__).resolve().parents[1];OUT=ROOT.parent.parent/'outputs'
entries=json.loads((ROOT/'src/data/fixtures.json').read_text());lookup={e['path']:e for e in entries}
assert len(entries)==len(lookup),'duplicate canonical paths'
selected=[e for e in entries if e['path'].startswith(('python/','quizzes/python-'))]
hub_count=sum(e['type']=='subject' for e in selected)
dependency_runtime=ROOT/'work/python-env/bin/python'
allowed={'p','h2','h3','ul','li','strong','pre','code','a'}
banned=re.compile(r'\b(delve|leverage|harness|foster|streamline|showcase|navigate|demystify|furthermore|moreover|additionally|robust|crucial|pivotal|multifaceted|bespoke|seamless|dynamic|quintessential|nuanced|powerful|versatile)\b',re.I)
links=[]
class Structure(HTMLParser):
 def __init__(self):super().__init__();self.stack=[]
 def handle_starttag(self,tag,attrs):
  assert tag in allowed,tag
  if tag=='a':
   assert not any(t in ('code','pre') for t in self.stack),'link inside source'
   assert len(attrs)==1 and attrs[0][0]=='href',attrs
   target=attrs[0][1];assert target.startswith('/'),target
   assert target[1:].split('#')[0] in lookup,target;links.append(target)
  else:assert not attrs or tag=='code' and attrs==[('class',next(v for k,v in attrs if k=='class'))] and attrs[0][1].startswith('language-'),(tag,attrs)
  self.stack.append(tag)
 def handle_endtag(self,tag):assert self.stack.pop()==tag,(tag,self.stack)
modules=set();programs=[];questions=0
kit=ROOT/'work/python-kit';kit.mkdir(exist_ok=True)
with tempfile.TemporaryDirectory(prefix='aitrove-python-check-') as directory:
 for e in selected:
  parser=Structure();parser.feed(e['body']);assert not parser.stack,e['path']
  assert not banned.search(re.sub('<[^>]*>',' ',e['body'])),e['path']
  assert e['data']['subject_root']=='python/python-programming-language-tutorial',e['path']
  assert lookup[e['data']['section_path']]['type']=='subject',e['path']
  assert e['data']['seo_ready'] is True
  for related in e['data'].get('related',[]):assert related['path'] in lookup,related
  if e['type']=='subject':
   assert len(e['data']['resource_tabs'])==hub_count
   assert {t['path'] for t in e['data']['resource_tabs']}=={h['path'] for h in selected if h['type']=='subject'}
   assert sum(x['subject']==e['subject'] for x in selected)<=100
   for m in e['data']['modules']:
    assert m['lessons']
    for path in m['lessons']:assert lookup[path]['subject']==e['subject'],path;modules.add(path)
  if e['type']=='quiz':
   assert len(e['data']['questions'])==12
   for q in e['data']['questions']:
    assert len(q['options'])==len(set(q['options'])) and 0<=q['answer']<len(q['options']) and q['explanation']
    assert not banned.search(q['prompt']+' '+q['explanation'])
   questions+=len(e['data']['questions'])
  if e['type']!='article':continue
  assert e['body'].startswith('<p>') and '<h3>Common Mistakes</h3>' in e['body'],e['path']
  matches=re.findall(r'<pre><code class="language-python">([\s\S]*?)</code></pre>',e['body']);assert len(matches)==1,e['path']
  source=html.unescape(matches[0])
  minimum_syntax=e['data'].get('python_syntax','3.11')
  assert minimum_syntax in {'3.11','3.12','3.13','3.14'},(e['path'],minimum_syntax)
  syntax_version=tuple(map(int,minimum_syntax.split('.')))
  runtime_version=sys.version_info[:2]
  assert syntax_version<=runtime_version,(e['path'],'checker runtime is older than declared syntax')
  declared_runtime=tuple(map(int,e['data']['python_minimum'].split('.')))
  assert syntax_version<=declared_runtime,(e['path'],'syntax minimum exceeds runtime minimum')
  ast.parse(source,feature_version=syntax_version)
  text=re.findall(r'<pre><code class="language-text">([\s\S]*?)</code></pre>',e['body']);assert len(text)==1
  expected=e['data']['expected_output'];assert html.unescape(text[0])==expected,(e['path'],'output metadata mismatch')
  name=e['path'].split('/')[-1].replace('-','_')+'.py';file=pathlib.Path(directory)/name;file.write_text(source+'\n')
  dependencies=e['data'].get('python_dependencies',[])
  executable=str(dependency_runtime) if dependencies else sys.executable
  for requirement in dependencies:
   package,version=requirement.split('==')
   probe=subprocess.run([executable,'-I','-c','import importlib.metadata,sys; print(importlib.metadata.version(sys.argv[1]))',package],capture_output=True,text=True,check=True)
   assert probe.stdout.strip()==version,(e['path'],requirement,probe.stdout)
  result=subprocess.run([executable,'-I',str(file)],cwd=directory,capture_output=True,text=True,timeout=45)
  assert result.returncode==0,(e['path'],result.stderr)
  assert result.stdout.rstrip('\n')==expected,(e['path'],result.stdout,expected)
  (kit/name).write_text(source+'\n')
  programs.append({'path':e['path'],'file':name,'minimumSyntax':minimum_syntax,'verifiedRuntime':sys.version.split()[0],'dependencies':dependencies,'output':result.stdout.rstrip('\n')})
assert modules=={e['path'] for e in selected if e['type'] in ('article','quiz')},'curriculum orphan'
assert len({e['title'] for e in selected})==len(selected),'duplicate Python title'
for e in entries:
 if e['type']=='subject' and e['path'].startswith(('java/','spring/')):
  assert all(not p.startswith(('python/','quizzes/python-')) for m in e['data']['modules'] for p in m['lessons']),e['path']
report={'passed':True,'articles':len(programs),'hubs':sum(e['type']=='subject' for e in selected),'quizBanks':sum(e['type']=='quiz' for e in selected),'questions':questions,'bodyLinks':len(links),'distinctLinkTargets':len(set(links)),'curriculumOrphans':0,'programOutputsChecked':len(programs),'runtime':sys.version.split()[0],'syntaxParsedAs':sorted({program['minimumSyntax'] for program in programs}),'programs':programs}
(OUT/'python-content-validation.json').write_text(json.dumps(report,indent=2));(kit/'manifest.json').write_text(json.dumps(programs,indent=2)+'\n')
print(json.dumps({k:v for k,v in report.items() if k!='programs'}))
