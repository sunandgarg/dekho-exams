"""Validate Java tutorial structure, internal links, code, and declared outputs."""
import json, re, html, pathlib, subprocess, tempfile
from html.parser import HTMLParser
ROOT = pathlib.Path(__file__).resolve().parents[1]
entries = json.loads((ROOT/'src/data/fixtures.json').read_text())
paths = {entry['path'] for entry in entries}
java = [entry for entry in entries if entry['path'].startswith('java/')]
allowed = {'p','h2','h3','ul','li','strong','pre','code','a'}
links = set()
class Structure(HTMLParser):
    def handle_starttag(self, tag, attrs):
        assert tag in allowed, tag
        if tag == 'a':
            assert len(attrs) == 1 and attrs[0][0] == 'href', attrs
            href = attrs[0][1]
            assert href.startswith('/'), href
            assert href[1:].split('#')[0] in paths, href
            links.add(href)
        else:
            assert not attrs or tag == 'code' and all(name == 'class' and value.startswith('language-') for name,value in attrs), (tag,attrs)
banned = re.compile(r'\b(delve|leverage|harness|foster|streamline|showcase|navigate|demystify|furthermore|moreover|additionally|robust|crucial|pivotal|multifaceted|bespoke|seamless|quintessential|nuanced|powerful|versatile)\b', re.I)
compiled = []; executed = []; seen = set(); snippets = 0; dependency_programs = []
with tempfile.TemporaryDirectory(prefix='aitrove-java-check-') as directory:
    work = pathlib.Path(directory)
    for entry in java:
        Structure().feed(entry['body'])
        assert not banned.search(re.sub('<[^>]+>',' ',entry['body'])), entry['path']
        if entry['type'] == 'article':
            assert entry['body'].startswith('<p>'), entry['path']
            assert '<h3>Common Mistakes</h3>' in entry['body'], entry['path']
        for match in re.finditer(r'<pre><code class="language-java">([\s\S]*?)</code></pre>', entry['body']):
            source = html.unescape(match[1])
            if source in seen: continue
            seen.add(source)
            release = str(entry.get('data', {}).get('java_release', 8))
            dependency = entry.get('data', {}).get('java_dependency')
            if entry['path'] == 'java/forkjoin-owned-pool-lifecycle':
                # This class calls ShipmentQuantitySum from the companion lesson.
                # check-java-http-forkjoin.py compiles and exercises both together.
                dependency_programs.append({'path':entry['path'],'verification':'Companion Java fork/join suite','release':release})
                continue
            if dependency in ('junit', 'jmh', 'hikari'):
                dependency_programs.append({'path':entry['path'],'verification':'Maven JUnit suite' if dependency == 'junit' else 'Maven JMH build and execution smoke check' if dependency == 'jmh' else 'Maven Hikari/H2 integration suite','release':release})
                continue
            jdk = pathlib.Path(json.loads((ROOT/'work/java-depth/toolchain/metadata.json').read_text())['home'])/'bin' if int(release)>21 else pathlib.Path('/usr/bin')
            source_file = entry.get('data', {}).get('java_source_file')
            public_class = re.search(r'public class (\w+)',source)
            if source_file:
                assert re.fullmatch(r'[A-Za-z]\w*\.java',source_file), source_file
                name = pathlib.Path(source_file).stem
            elif public_class:
                name = public_class[1]
            else:
                snippets += 1; name = 'TutorialSnippet'+str(snippets)
                if source.lstrip().startswith('static '):
                    source = 'public class '+name+' {\n'+source+'\n}'
                else:
                    source = 'public class '+name+' { public static void main(String[] args) throws Exception {\n'+source+'\n}}'
            package = re.search(r'^package ([\w.]+);',source,re.M)
            runtime_name = (package[1]+'.' if package else '')+name
            file = work/(name+'.java'); file.write_text(source)
            result = subprocess.run([str(jdk/'javac'),'--release',release,'-d',str(work),str(file)],capture_output=True,text=True)
            assert result.returncode == 0, (entry['path'],result.stderr)
            compiled.append({'path':entry['path'],'class':runtime_name,'fragment':not bool(public_class or source_file),'release':release})
            if dependency == 'h2':
                dependency_programs.append({'path':entry['path'],'verification':'Maven H2 integration suite','release':release})
                continue
            if 'public static void main' in source or entry.get('data', {}).get('java_entrypoint') == 'instance':
                runtime_flags = entry.get('data', {}).get('java_runtime_flags', [])
                assert runtime_flags in ([], ['--enable-native-access=ALL-UNNAMED']), runtime_flags
                result = subprocess.run([str(jdk/'java'),*runtime_flags,'-cp',str(work),runtime_name],capture_output=True,text=True,timeout=25)
                assert result.returncode == 0,(entry['path'],result.stderr)
                after = entry['body'][match.end():]
                expected = re.match(r'(?:\s|<h[23]>Output</h[23]>)*<pre><code class="language-text">([\s\S]*?)</code></pre>',after)
                if expected: assert result.stdout.strip() == html.unescape(expected[1]).strip(), (runtime_name,result.stdout,expected[1])
                executed.append({'path':entry['path'],'class':runtime_name,'output':result.stdout.strip(),'declaredOutputChecked':bool(expected)})
report = {'javaPages':len(java),'internalLinkTargets':len(links),'programsAndFragmentsCompiled':len(compiled),'programsAndFragmentsExecuted':len(executed),'declaredOutputsChecked':sum(item['declaredOutputChecked'] for item in executed),'releaseTargets':sorted(set(int(item['release']) for item in compiled)),'dependencyChecks':dependency_programs,'passed':True,'programs':executed}
(ROOT.parent.parent/'outputs/java-program-check.json').write_text(json.dumps(report,indent=2))
print(json.dumps({key:value for key,value in report.items() if key!='programs'}))
