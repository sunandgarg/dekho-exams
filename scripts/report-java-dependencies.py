"""Read the completed Maven run and require exact fixture/source correspondence."""
import pathlib, json, re, html, xml.etree.ElementTree as ET
ROOT = pathlib.Path(__file__).resolve().parents[1]
project = ROOT/'work/java-lesson-checks'
entries = json.loads((ROOT/'src/data/fixtures.json').read_text())
checked=[]
for entry in entries:
    dependency=entry.get('data',{}).get('java_dependency')
    if not dependency: continue
    source=html.unescape(re.search(r'<pre><code class="language-java">([\s\S]*?)</code></pre>',entry['body'])[1])
    name=re.search(r'public class (\w+)',source)[1]
    folder='test' if dependency=='junit' else 'main'
    assert (project/('src/'+folder+'/java')/(name+'.java')).read_text().strip()==source.strip(), entry['path']
    checked.append(entry['path'])
reports=list((project/'target/surefire-reports').glob('TEST-*.xml'))
assert len(reports)==2, reports
suites=[ET.parse(file).getroot() for file in reports]
assert all(int(suite.attrib['failures'])==0 and int(suite.attrib['errors'])==0 and int(suite.attrib['skipped'])==0 for suite in suites)
tests=sum(int(suite.attrib['tests']) for suite in suites)
assert tests==8,tests
report=dict(passed=True,tests=tests,failures=0,errors=0,skipped=0,runtime='JDK 21',database='H2 2.3.232 in-memory',junit='5.11.0',fixtureSourcesMatched=checked,suites=[{'name':s.attrib['name'],'tests':int(s.attrib['tests'])} for s in suites])
(ROOT.parent.parent/'outputs/java-dependency-check.json').write_text(json.dumps(report,indent=2)+'\n')
print(json.dumps(report))
