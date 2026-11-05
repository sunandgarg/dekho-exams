"""Check source-backed Spring structure, canonical curricula and all related links."""
import json,html,re,pathlib,collections,subprocess,xml.etree.ElementTree as ET,zipfile
from html.parser import HTMLParser
ROOT=pathlib.Path(__file__).resolve().parents[1];OUT=ROOT.parent.parent/'outputs'
es=json.loads((ROOT/'src/data/fixtures.json').read_text()); lookup={e['path']:e for e in es}
assert len(lookup)==len(es), 'duplicate routes'
selected=[e for e in es if e['path'].startswith(('spring/','quizzes/spring-'))]
allowed={'p','h2','h3','ul','li','strong','pre','code','a'}
banned=re.compile(r'\b(delve|leverage|harness|foster|streamline|showcase|navigate|demystify|furthermore|moreover|additionally|robust|crucial|pivotal|multifaceted|bespoke|seamless|dynamic|quintessential|nuanced|powerful|versatile)\b',re.I)
links=[]
class Structure(HTMLParser):
 def handle_starttag(self,tag,attrs):
  assert tag in allowed,tag
  if tag=='a':
   assert len(attrs)==1 and attrs[0][0]=='href',attrs
   href=attrs[0][1];assert href.startswith(('/spring/','/java/','/quizzes/', '/python/', '/web-tech/')),href
   assert href[1:].split('#')[0] in lookup,href;links.append(href)
  else:assert not attrs or tag=='code' and all(n=='class' and v.startswith('language-') for n,v in attrs),(tag,attrs)
modules=set();titles=[]
for e in selected:
 Structure().feed(e['body']);assert not banned.search(re.sub('<[^>]*>',' ',e['body'])),e['path']
 assert e['data']['subject_root']=='spring/spring-boot',e['path']
 assert e['data']['seo_ready'] is True,e['path']
 assert lookup[e['data']['section_path']]['type']=='subject',e['path']
 titles.append(e['title'])
 if e['type']=='article':assert e['body'].startswith('<p>') and '<h3>Common Mistakes</h3>' in e['body'],e['path']
 if e['type']=='quiz':
  qs=e['data']['questions'];assert 12<=len(qs)<=30,e['path']
  for q in qs:assert len(set(q['options']))==len(q['options']) and 0<=q['answer']<len(q['options']) and q['explanation']
 if e['type']=='subject':
  rows=[r for r in selected if r['subject']==e['subject']];assert len(rows)<=100,(e['path'],len(rows))
  for m in e['data']['modules']:
   assert m['lessons'],e['path']
   for path in m['lessons']:assert lookup[path]['subject']==e['subject'],path;modules.add(path)
 for r in e['data'].get('related',[]):assert r['path'] in lookup,r
assert len(titles)==len(set(titles)), 'duplicate Spring titles'
assert modules=={e['path'] for e in selected if e['type'] in ('article','quiz')},'curriculum orphans'
for e in es:
 if e['type']=='subject' and e['path'].startswith('java/'):
  assert all(not s.startswith(('spring/','quizzes/spring-')) for m in e['data']['modules'] for s in m['lessons']),e['path']
kit=ROOT/'work/spring-kit';classpath=(kit/'target/classpath.txt').read_text().strip();programs=[]
for name,expected in {
 'ContainerContracts':'csv:receipt\ndifferent=true\nevents=1\nclosed=true\nadvised=1',
 'JdbcReceiptLedger':'constraint rejected\nafter failure=0\nafter rollback=0\nafter commit=1',
 'AsyncReceiptWork':'capacity rejected',
 'ReceiptCacheBoundary':'tenant-a:7\ntenant-a:7\ntenant-b:7'}.items():
 result=subprocess.run(['/usr/bin/java','-cp',str(kit/'target/classes')+':'+classpath,'in.aitrove.learning.'+name],capture_output=True,text=True,timeout=20)
 assert result.returncode==0,(name,result.stderr);assert result.stdout.strip()==expected,(name,result.stdout,expected);programs.append(name)
tests=failures=errors=skipped=0
for file in (kit/'target/surefire-reports').glob('TEST-*.xml'):
 r=ET.parse(file).getroot();tests+=int(r.attrib['tests']);failures+=int(r.attrib['failures']);errors+=int(r.attrib['errors']);skipped+=int(r.attrib['skipped'])
assert tests>=30 and failures==errors==skipped==0,(tests,failures,errors,skipped)
reactive_tests=reactive_failures=reactive_errors=reactive_skipped=0
for file in (kit/'reactive-r2dbc/target/surefire-reports').glob('TEST-*.xml'):
 r=ET.parse(file).getroot();reactive_tests+=int(r.attrib['tests']);reactive_failures+=int(r.attrib['failures']);reactive_errors+=int(r.attrib['errors']);reactive_skipped+=int(r.attrib['skipped'])
assert reactive_tests>=6 and reactive_failures==reactive_errors==reactive_skipped==0,(reactive_tests,reactive_failures,reactive_errors,reactive_skipped)
def counted_tests(directory):
 total=failures=errors=skipped=0
 for file in directory.glob('TEST-*.xml'):
  result=ET.parse(file).getroot();total+=int(result.attrib['tests']);failures+=int(result.attrib['failures']);errors+=int(result.attrib['errors']);skipped+=int(result.attrib['skipped'])
 return total,failures,errors,skipped
batch_tests,batch_failures,batch_errors,batch_skipped=counted_tests(kit/'batch-chunks/target/surefire-reports')
modulith_tests,modulith_failures,modulith_errors,modulith_skipped=counted_tests(kit/'modulith-boundaries/target/surefire-reports')
assert 'spring-boot-starter-batch-jdbc' in (kit/'batch-chunks/pom.xml').read_text(), 'Batch restart kit needs a JDBC repository'
assert batch_tests>=8 and batch_failures==batch_errors==batch_skipped==0,(batch_tests,batch_failures,batch_errors,batch_skipped)
assert modulith_tests>=4 and modulith_failures==modulith_errors==modulith_skipped==0,(modulith_tests,modulith_failures,modulith_errors,modulith_skipped)
report={'passed':True,'springArticles':sum(e['type']=='article' for e in selected),'springHubs':sum(e['type']=='subject' for e in selected),'springQuizzes':sum(e['type']=='quiz' for e in selected),'quizQuestions':sum(len(e['data']['questions']) for e in selected if e['type']=='quiz'),'bodyLinks':len(links),'linkTargets':len(set(links)),'curriculumOrphans':0,'javaCurriculumContainsSpring':False,'mavenTests':tests,'reactiveMavenTests':reactive_tests,'batchMavenTests':batch_tests,'modulithMavenTests':modulith_tests,'standaloneProgramOutputsChecked':programs}
(OUT/'spring-content-validation.json').write_text(json.dumps(report,indent=2));print(json.dumps(report))
