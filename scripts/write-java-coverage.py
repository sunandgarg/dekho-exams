"""Build a reviewable coverage map from the published fixture curriculum."""
import json, pathlib, html
ROOT = pathlib.Path(__file__).resolve().parents[1]
OUT = ROOT.parent.parent/'outputs'
entries = json.loads((ROOT/'src/data/fixtures.json').read_text())
lookup = {e['path']:e for e in entries}
batch = json.loads((OUT/'java-completion-batch.json').read_text())
added = set(batch['added'])
base = 'https://aitrove-frontend.cirkle-world.workers.dev/'
remaining = {
 'java/java':['Console input and Scanner parsing','Unicode and encoding beyond the current String notes','Overload resolution, casts, and full access-control examples','More worked beginner problems and boundary tests'],
 'java/advanced-java':['Class loading, initialization, and module-system lessons','ConcurrentHashMap, locks, atomics, CompletableFuture, and structured task failure','Byte streams, channels, sockets, and a live HTTP integration project','Database isolation, deadlocks, connection pools, migrations, and production-engine tests','Gradle, multi-module packaging, test doubles, parameterized tests, and benchmarking','Collector comparison, JFR workflow, heap-dump investigation, and load-based diagnostics','Features after the explicitly covered Java 21 baseline'],
 'java/java-collections':['LinkedHashSet, TreeSet, EnumMap, and EnumSet','Concurrent and blocking collections','Weak-reference collection lifetime and specialized immutable collections','Broader comparator, view, and mutability exercises'],
 'java/dsa-in-java':['Binary-search-tree insertion/deletion and balancing','Heaps, tries, disjoint sets, and hashing problem sets','Dijkstra, topological sorting, cycle classification, and weighted graphs','Greedy proofs, backtracking, tabulation, and more cached-state problems','Two pointers, sliding windows, string algorithms, and broader complexity proofs'],
 'java/java-interview-questions':['Dedicated generics, streams, exceptions, JDBC, JVM, and modern-Java sets','More code-tracing questions with follow-ups and tested outputs'],
 'java/java-exercises':['Array, String, OOP, exception, file, and concurrency exercise sets','Algorithm exercises grouped by difficulty','Judged code submissions require a separate execution service'],
 'java/java-examples':['Broader runnable examples for files, streams, records, and database adapters','Multi-file downloadable application examples'],
 'java/java-quizzes':['Larger beginner and topic-specific question banks','Accessibility review of every quiz state','Server-stored attempts and accounts require a backend; current self-checks stay local'],
 'java/java-projects':['Persistent CLI application, tested HTTP client, and database-backed project','Concurrent application with deadlines and load tests','Complete build/run/documentation bundles for every project'],
 'java/java-cheatsheet':['Version-labelled syntax, streams, concurrency, JDBC, and modern-feature references']
}
esc = html.escape
parts=[]
tabs=lookup['java/java']['data']['resource_tabs']
for tab in tabs:
    hub=lookup[tab['path']]
    paths=[path for module in hub['data'].get('modules',[]) for path in module.get('lessons',[])]
    parts.append('<section class="branch" data-status="partial"><h2><a href="'+base+hub['path']+'">'+esc(tab['title'])+'</a> <span class="tag partial">Partial section · '+str(len(paths))+' published entries</span></h2><p>The listed pages are present. This does not mean the subject is exhaustive.</p>')
    for module in hub['data'].get('modules',[]):
        parts.append('<details open><summary>'+esc(module['title'])+'</summary><ul>')
        for path in module.get('lessons',[]):
            entry=lookup[path]
            badge='New this batch' if path in added else 'Published'
            release=entry.get('data',{}).get('java_release')
            version=' · Java '+str(release)+'+' if release else ''
            parts.append('<li data-status="published"><a href="'+base+path+'">'+esc(entry['title'])+'</a> <span class="tag done">'+badge+'</span>'+esc(version)+'<small>/'+esc(path)+'</small></li>')
        parts.append('</ul></details>')
    parts.append('<details class="remaining" open data-status="remaining"><summary>Remaining in this section</summary><ul>'+''.join('<li>'+esc(text)+'</li>' for text in remaining[hub['path']])+'</ul></details></section>')
sources = [
 ('Oracle LinkedList — first requested reference','https://docs.oracle.com/javase/8/docs/api/java/util/LinkedList.html'),
 ('GeeksforGeeks Java — coverage/presentation inspection','https://www.geeksforgeeks.org/java/java/'),
 ('W3Schools LinkedList — coverage inspection','https://www.w3schools.com/java/java_linkedlist.asp'),
 ('BeginnersBook LinkedList — coverage inspection','https://beginnersbook.com/2013/12/linkedlist-in-java-with-example/'),
 ('CodingNomads LinkedList — coverage inspection','https://codingnomads.com/java-301-linked-lists'),
 ('Oracle annotations','https://docs.oracle.com/javase/tutorial/java/annotations/'),
 ('Oracle reflection','https://docs.oracle.com/javase/tutorial/reflect/'),
 ('Java 21 reflective method contract','https://docs.oracle.com/en/java/javase/21/docs/api/java.base/java/lang/reflect/Method.html'),
 ('Java class, abstract-type, and variable-arity rules','https://docs.oracle.com/javase/specs/jls/se21/html/jls-8.html'),
 ('Oracle prepared statements','https://docs.oracle.com/javase/tutorial/jdbc/basics/prepared.html'),
 ('Oracle transactions','https://docs.oracle.com/javase/tutorial/jdbc/basics/transactions.html'),
 ('Oracle records','https://docs.oracle.com/en/java/javase/21/language/records.html'),
 ('Oracle sealed types','https://docs.oracle.com/en/java/javase/21/language/sealed-classes-and-interfaces.html'),
 ('Oracle pattern switch','https://docs.oracle.com/en/java/javase/21/language/pattern-matching-switch.html'),
 ('Oracle virtual threads','https://docs.oracle.com/en/java/javase/21/core/virtual-threads.html'),
 ('JVM runtime areas','https://docs.oracle.com/javase/specs/jvms/se21/html/jvms-2.html'),
 ('Java 21 garbage collection','https://docs.oracle.com/en/java/javase/21/gctuning/garbage-collector-implementation.html'),
 ('Oracle StringBuilder','https://docs.oracle.com/javase/8/docs/api/java/lang/StringBuilder.html'),
 ('Oracle nested classes','https://docs.oracle.com/javase/tutorial/java/javaOO/nested.html'),
 ('Java conversion rules','https://docs.oracle.com/javase/specs/jls/se21/html/jls-5.html'),
 ('Oracle HttpClient','https://docs.oracle.com/en/java/javase/21/docs/api/java/net/http/HttpClient.html'),
 ('Maven project guide','https://maven.apache.org/guides/getting-started/'),
 ('Maven compiler plugin','https://maven.apache.org/plugins/maven-compiler-plugin/'),
 ('JUnit 5.11 guide','https://docs.junit.org/5.11.0/user-guide/'),
 ('H2 embedded database','https://www.h2database.com/html/quickstart.html'),
 ('MIT algorithm lecture notes — independent verification, no copied code','https://ocw.mit.edu/courses/6-006-introduction-to-algorithms-fall-2011/pages/lecture-notes/')
]
program=json.loads((OUT/'java-program-check.json').read_text())
maven=json.loads((OUT/'java-dependency-check.json').read_text())
browser=json.loads((OUT/'java-browser-check.json').read_text())
checks='<p>'+str(program['programsAndFragmentsCompiled'])+' standalone programs/fragments compiled for their declared releases; '+str(program['programsAndFragmentsExecuted'])+' executed, with '+str(program['declaredOutputsChecked'])+' declared outputs matched. The dependency project passed '+str(maven['tests'])+' JUnit tests, including actual H2 lookup and rollback checks. Browser checks passed at 1440, 768, 390, and 360 pixels and checked all '+str(browser['javaRoutesChecked'])+' routes. All 27 new quiz answers and their explanations were checked, including saved-result reloads.</p>'
document='''<!doctype html><html lang="en"><head><meta charset="utf-8"><meta name="viewport" content="width=device-width,initial-scale=1"><meta name="robots" content="noindex"><title>AI Trove Java coverage map</title><style>
*{box-sizing:border-box}body{margin:0;background:#f4f7f5;color:#17312c;font:16px/1.65 system-ui}main{max-width:960px;margin:auto;padding:32px 20px 80px}h1{font-size:32px;margin:0 0 12px}h2{font-size:22px;line-height:1.5}a{color:#146c62;text-decoration-thickness:1px;text-underline-offset:3px}.intro{background:#e5f3ed;border:1px solid #a7cabc;padding:20px}.branch{margin:24px 0;padding:8px 20px 20px;background:#fbfcfa;border:1px solid #ccd8d2}.tag{display:inline-block;font-size:12px;padding:2px 8px;border-radius:4px;margin:4px;font-weight:600}.done{background:#dff1e8;color:#174937}.partial{background:#fff0d8;color:#674409}.remaining{background:#fff6e9;padding:12px;margin-top:16px;border:1px solid #d8bd96}summary{cursor:pointer;font-weight:650;padding:8px 0}li{margin:10px 0}small{display:block;color:#53675f;overflow-wrap:anywhere}.controls{position:sticky;top:0;background:#f4f7f5;border-bottom:1px solid #becfc6;padding:12px 0;z-index:2;display:flex;flex-wrap:wrap;gap:8px}input,select,button{font:inherit;padding:9px 12px;border:1px solid #a3b9ad;border-radius:4px;background:#fff;color:#17312c}input{flex:1;min-width:160px}:focus-visible{outline:3px solid #08766b;outline-offset:3px}[hidden]{display:none!important}.note{font-size:14px;color:#52655c}section>h2{border-bottom:1px solid #b9cdc1;padding-bottom:10px}@media(max-width:500px){main{padding:20px 12px}.branch{padding:6px 12px 16px}h1{font-size:27px}h2{font-size:20px}.tag{margin-left:0}}@media print{.controls{display:none}body{background:white}.branch{break-inside:avoid}details>*{display:block!important}}
</style></head><body><main><h1>AI Trove · Java skeleton and coverage</h1><div class="intro"><p><strong>100 Java routes: 85 lesson/reference pages, 10 section hubs, and 5 quizzes.</strong> This batch adds 29 pages and 3 quizzes with 27 explained questions.</p><p>Published means the named lesson or local quiz exists. Partial means that section still needs broader coverage. Remaining means the item is not delivered. No percentage is assigned to “all Java,” and no claim is made that the internet has been exhausted.</p><p><a href="https://aitrove-frontend.cirkle-world.workers.dev/java/java">Open the Java section</a> · <a href="aitrove-java-content.json">Content bundle</a> · <a href="aitrove-java-test-project.zip">Runnable Maven test project</a></p></div><div class="controls"><label for="search">Find a topic</label><input id="search" type="search" placeholder="JDBC, records, graphs…"><label for="status">Show</label><select id="status"><option value="all">All coverage</option><option value="published">Published pages</option><option value="remaining">Remaining work</option></select><button type="button" id="expand">Expand modules</button><button type="button" id="collapse">Collapse modules</button></div><p id="match-count" role="status"></p>'''+''.join(parts)+'''<section class="branch" data-status="remaining"><h2>Platform and publishing work still open</h2><ul><li>Hostinger WordPress installation, CMS plugin installation, content import, API configuration, and a real publish-to-frontend check. The live preview still uses fixtures.</li><li>Purchase the domain, configure DNS, and connect the CMS address.</li><li>Server-backed accounts, persistent quiz attempts, a Java compiler, and judged submissions need services before release.</li><li>Editorial review and wider source/originality review remain. Fresh explanations and programs were authored for AI Trove; changing someone else’s example values is not the method used. Java facts, syntax, logos, and open-source libraries are not claimed as exclusive property.</li><li>Courses remain archived behind the existing disabled feature flag.</li></ul></section><section class="branch" data-status="published"><h2>Interface work delivered</h2><ul><li>The fixed mobile Contents button has a light teal fill and teal border/text.</li><li>Mobile lesson and heading sheets, current-location states, fixed subject tabs, and internal links are present.</li><li>Syntax highlighting, copy-preserved code, original Java diagrams, and the LinkedList model remain available.</li></ul></section><section class="branch" data-status="published"><h2>Verified behavior</h2>'''+checks+'''<p class="note">Standalone compilation uses release 8, 11, 17, or 21 as declared. The Maven project runs on JDK 21. Java 8-compatible compilation was checked on JDK 21; it is not a separate execution on a Java 8 runtime. HTTP network execution, production database behavior, load/performance claims, and universal correctness are not claimed verified.</p></section><section class="branch"><h2>Research record</h2><p>Oracle supplied API and language contracts. The requested secondary sites were inspected in the supplied order for coverage and presentation; their text, examples, illustrations, and screenshots were not imported into these lessons. The following sources support editorial verification; public tutorial bodies contain internal lesson links.</p><ul>'''+''.join('<li><a href="'+url+'">'+esc(title)+'</a></li>' for title,url in sources)+'''</ul></section></main><script>
const search=document.querySelector('#search'),status=document.querySelector('#status');
function filter(){let count=0;document.querySelectorAll('.branch').forEach(section=>{const query=search.value.toLowerCase().trim();const match=!query||section.textContent.toLowerCase().includes(query);const mode=status.value;section.hidden=!match||(mode==='published'&&section.dataset.status==='remaining')||(mode==='remaining'&&section.dataset.status==='published')||(mode!=='all'&&!section.dataset.status);section.querySelectorAll('details').forEach(item=>{item.hidden=mode==='remaining'?item.dataset.status!=='remaining':mode==='published'?item.dataset.status==='remaining':false});if(!section.hidden)count++});document.querySelector('#match-count').textContent=count+' sections shown';}
search.addEventListener('input',filter);status.addEventListener('change',filter);document.querySelector('#expand').addEventListener('click',()=>document.querySelectorAll('details').forEach(item=>item.open=true));document.querySelector('#collapse').addEventListener('click',()=>document.querySelectorAll('details').forEach(item=>item.open=false));filter();
</script></body></html>'''
(OUT/'java-coverage-map.html').write_text(document)
# Replace the older handoff so its totals and remaining list cannot contradict the map.
(OUT/'aitrove-java-update.html').write_text(document.replace('<title>AI Trove Java coverage map</title>','<title>AI Trove Java update and coverage</title>'))
print(json.dumps({'coverageMap':str(OUT/'java-coverage-map.html'),'publishedRoutes':batch['javaPages']}))
