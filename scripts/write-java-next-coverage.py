"""Export the local Java batch, runnable programs and an honest coverage skeleton."""
import html, json, pathlib, re, zipfile
ROOT=pathlib.Path(__file__).resolve().parents[1]
OUT=ROOT.parent.parent/'outputs'
entries=json.loads((ROOT/'src/data/fixtures.json').read_text())
lookup={e['path']:e for e in entries}
batch=json.loads((OUT/'java-next-content-batch.json').read_text())
new=set(batch['added']); expanded=set(batch['expanded'])
remaining={
 'java/java':['More depth in the remaining short foundations lessons and beginner boundary exercises.','Full casts, promotion and nested access-control exercises across several packages.','Unicode grapheme segmentation, normalization and localized text processing.'],
 'java/advanced-java':['Class loaders and Java modules; channels, sockets and an HTTP integration project.','Conditions, semaphores, scheduling, cancellation/deadlines and more coordinated-task failure cases.','Database isolation, connection pools, migrations and production-database tests.','Gradle, multi-module builds, mocks, parameterized tests and JMH benchmarking.','JFR/heap-dump workflows and coverage beyond the current Java 21 material.'],
 'java/java-collections':['Copy-on-write and concurrent sorted collections; weak-reference lifetime.','Version-labelled immutable collection factories and sequenced collections.','More comparator, iterator and nested-mutability exercises.'],
 'java/dsa-in-java':['Balanced search trees, tries, custom heap construction and deletion.','Greedy proofs, tabulation, string-search algorithms and broader problem sets.','Minimum spanning trees and algorithms that support negative edge weights.'],
 'java/java-interview-questions':['Dedicated generics, streams, exceptions, JDBC, JVM and modern-Java question sets.','More follow-up questions with checked code traces.'],
 'java/java-exercises':['OOP, exceptions, files and concurrency exercise sets.','Broader algorithm exercises grouped by difficulty.','Judged submissions need a separate execution service; none is implied here.'],
 'java/java-examples':['Additional multi-file programs and database/HTTP example bundles.','More depth in the short LinkedList example/reference pages.'],
 'java/java-quizzes':['Larger topic-specific banks; this batch does not add quiz questions.','Authenticated server-stored attempts require a backend; existing attempts remain local.'],
 'java/java-projects':['Persistent CLI application, database-backed application and an HTTP client project.','Concurrent application with deadlines/load tests and documented downloadable builds.'],
 'java/java-cheatsheet':['Version-labelled stream, concurrency, JDBC and newer-feature reference pages.']
}
java=[e for e in entries if e['path'].startswith('java/')]
quizzes=[e for e in entries if e['type']=='quiz' and e.get('subject','').startswith('java')]
# Some quiz subjects use the section key; derive them from the published hub as well.
quiz_paths={p for m in lookup['java/java-quizzes']['data']['modules'] for p in m['lessons'] if lookup[p]['type']=='quiz'}
route_count=len(java)+len(quiz_paths)
articles=sum(e['type']=='article' for e in java)
sources=[
 ('First requested API reference; LinkedList contract','https://docs.oracle.com/javase/8/docs/api/java/util/LinkedList.html'),
 ('Second requested reference; curriculum coverage only','https://www.geeksforgeeks.org/java/java/'),
 ('Third requested reference; coverage inspection only','https://www.w3schools.com/java/java_linkedlist.asp'),
 ('Fourth requested reference; coverage inspection only','https://beginnersbook.com/2013/12/linkedlist-in-java-with-example/'),
 ('Fifth requested reference; coverage inspection only','https://codingnomads.com/java-301-linked-lists'),
 ('Scanner contract','https://docs.oracle.com/javase/8/docs/api/java/util/Scanner.html'),
 ('UTF-16 String contract','https://docs.oracle.com/javase/8/docs/api/java/lang/String.html'),
 ('Overload rules','https://docs.oracle.com/javase/specs/jls/se8/html/jls-15.html'),
 ('Access rules','https://docs.oracle.com/javase/specs/jls/se8/html/jls-6.html'),
 ('Initialization rules','https://docs.oracle.com/javase/specs/jls/se8/html/jls-12.html'),
 ('Views and wrappers','https://docs.oracle.com/javase/8/docs/api/java/util/Collections.html'),
 ('TreeSet comparator equivalence','https://docs.oracle.com/javase/8/docs/api/java/util/TreeSet.html'),
 ('EnumMap','https://docs.oracle.com/javase/8/docs/api/java/util/EnumMap.html'),
 ('EnumSet','https://docs.oracle.com/javase/8/docs/api/java/util/EnumSet.html'),
 ('ConcurrentHashMap','https://docs.oracle.com/javase/8/docs/api/java/util/concurrent/ConcurrentHashMap.html'),
 ('AtomicInteger','https://docs.oracle.com/javase/8/docs/api/java/util/concurrent/atomic/AtomicInteger.html'),
 ('ReentrantLock','https://docs.oracle.com/javase/8/docs/api/java/util/concurrent/locks/ReentrantLock.html'),
 ('Bounded queue','https://docs.oracle.com/javase/8/docs/api/java/util/concurrent/ArrayBlockingQueue.html'),
 ('Completion stages','https://docs.oracle.com/javase/8/docs/api/java/util/concurrent/CompletableFuture.html'),
 ('Byte streams','https://docs.oracle.com/javase/tutorial/essential/io/bytestreams.html'),
 ('InputStream partial-read contract','https://docs.oracle.com/javase/8/docs/api/java/io/InputStream.html'),
 ('File API','https://docs.oracle.com/javase/8/docs/api/java/nio/file/Files.html'),
 ('Algorithm coverage inspection','https://ocw.mit.edu/courses/6-006-introduction-to-algorithms-fall-2011/pages/lecture-notes/'),
 ('Author-maintained tree reference; independent program','https://algs4.cs.princeton.edu/32bst/'),
 ('Author-maintained heap reference; independent program','https://algs4.cs.princeton.edu/24pq/'),
 ('Author-maintained union-find reference; independent program','https://algs4.cs.princeton.edu/15uf/'),
 ('Author-maintained path reference; independent program','https://algs4.cs.princeton.edu/44sp/'),
 ('Author-maintained dependency reference; independent program','https://algs4.cs.princeton.edu/42digraph/')
]
report={'javaRoutes':route_count,'articles':articles,'hubs':10,'quizzes':len(quiz_paths),'new':batch['added'],'expanded':batch['expanded'],'remainingBySection':remaining,'sources':[{'purpose':p,'url':u} for p,u in sources],'localOnly':True}
(OUT/'java-next-coverage.json').write_text(json.dumps(report,indent=2))
lines=['# AI Trove Java editorial handoff','',f'{batch["newPages"]} new lessons and {batch["expandedPages"]} expanded lessons. {route_count} local Java routes: {articles} articles, 10 hubs and {len(quiz_paths)} quizzes.','', 'Research verified API/language contracts and checked topic coverage. Programs and explanations were written for AI Trove; no third-party prose or code was copied and renamed. This does not establish exclusive ownership of language facts or third-party assets.','', 'The homepage remains a topic directory. New content appears in Java section curricula, search and related lessons. No deployment or WordPress import was performed.','', '## Sources reviewed in priority order','']
lines += [f'- [{purpose}]({url})' for purpose,url in sources]
lines += ['', '## Added', '']+[f'- [{lookup[p]["title"]}](http://127.0.0.1:3001/{p})' for p in batch['added']]
lines += ['', '## Expanded', '']+[f'- [{lookup[p]["title"]}](http://127.0.0.1:3001/{p})' for p in batch['expanded']]
lines += ['', '## Remaining', '']
for hub,items in remaining.items(): lines += ['### '+lookup[hub]['title'],'']+['- '+item for item in items]+['']
(OUT/'java-next-editorial-handoff.md').write_text('\n'.join(lines)+'\n')
esc=html.escape
branches=[]
for tab in lookup['java/java']['data']['resource_tabs']:
 hub=lookup[tab['path']]; modules=[]
 for m in hub['data'].get('modules',[]):
  items=[]
  for p in m['lessons']:
   e=lookup[p]; status='New' if p in new else 'Expanded' if p in expanded else 'Existing'
   items.append(f'<li data-status="{status.lower()}"><a href="http://127.0.0.1:3001/{p}">{esc(e["title"])}</a> <span>{status}</span></li>')
  modules.append('<details open><summary>'+esc(m['title'])+'</summary><ul>'+''.join(items)+'</ul></details>')
 todo='<details class="remaining" open><summary>Still remaining</summary><ul>'+''.join('<li>'+esc(t)+'</li>' for t in remaining[hub['path']])+'</ul></details>'
 branches.append('<section class="branch"><h2><a href="http://127.0.0.1:3001/'+hub['path']+'">'+esc(tab['title'])+'</a></h2>'+''.join(modules)+todo+'</section>')
doc='''<!doctype html><html lang="en"><head><meta charset="utf-8"><meta name="viewport" content="width=device-width,initial-scale=1"><title>AI Trove Java coverage · 29 September</title><style>
*{box-sizing:border-box}body{margin:0;background:#f7f7f5;color:#202c40;font:16px/1.6 system-ui}main{max-width:980px;margin:auto;padding:28px 18px 60px}h1{font-size:30px;line-height:1.25}h2{font-size:22px}a{color:#263f78;text-underline-offset:3px}.intro,.branch{padding:18px;border:1px solid #c9ced6;background:white;margin:20px 0}.branch>h2{border-bottom:1px solid #dedfe2;padding-bottom:12px}.remaining{border:1px solid #c9ced6;padding:12px;margin-top:18px;background:#f1f2f2}summary{cursor:pointer;font-weight:650;padding:8px 0}li{margin:8px 0}li span{display:inline-block;font-size:12px;font-weight:600;padding:2px 7px;border:1px solid #b8c3d4;border-radius:3px;margin-left:5px}.controls{position:sticky;top:0;background:#f7f7f5;padding:12px 0;display:flex;flex-wrap:wrap;gap:8px;z-index:1}input,select{font:inherit;padding:10px;border:1px solid #9da9bb;border-radius:4px;background:white;color:#202c40}input{flex:1;min-width:150px}:focus-visible{outline:3px solid #263f78;outline-offset:3px}[hidden]{display:none!important}@media(max-width:500px){main{padding:18px 12px}h1{font-size:25px}.branch{padding:12px}ul{padding-left:20px}}
</style></head><body><main><h1>AI Trove Java · skeleton and remaining work</h1><div class="intro">'''+f'<p><strong>{route_count} local routes: {articles} articles, 10 section hubs and {len(quiz_paths)} quizzes.</strong></p><p>This batch adds 24 tutorials and expands 8 existing lessons. Section coverage remains partial. Existing means a page is present, not that every API or edge case has been covered.</p><p><a href="http://127.0.0.1:3001/java/java">Open Java locally</a></p>'+'''</div><div class="controls"><input id="find" aria-label="Find a topic" placeholder="Find a topic"><select id="show" aria-label="Show"><option value="all">All coverage</option><option value="new">New and expanded</option><option value="remaining">Remaining only</option></select></div>'''+''.join(branches)+'''<p>All links open the local preview. This batch has not been deployed.</p></main><script>
function filter(){const q=document.getElementById('find').value.toLowerCase();const mode=document.getElementById('show').value;document.querySelectorAll('.branch').forEach(branch=>{let visible=false;branch.querySelectorAll('details').forEach(group=>{const remaining=group.classList.contains('remaining');let shown=false;group.querySelectorAll('li').forEach(item=>{const matches=item.textContent.toLowerCase().includes(q);const state=item.dataset.status;const accepted=mode==='all'||mode==='remaining'&&remaining||mode==='new'&&!remaining&&(state==='new'||state==='expanded');item.hidden=!(matches&&accepted);shown=shown||!item.hidden;});group.hidden=!shown;visible=visible||shown;});branch.hidden=!visible;});}document.getElementById('find').addEventListener('input',filter);document.getElementById('show').addEventListener('change',filter);
</script></body></html>'''
(OUT/'java-next-coverage.html').write_text(doc)
with zipfile.ZipFile(OUT/'aitrove-java-next-programs.zip','w',zipfile.ZIP_DEFLATED) as z:
 outputs=[]
 for path in batch['added']:
  e=lookup[path]
  source=html.unescape(re.search(r'<pre><code class="language-java">([\s\S]*?)</code></pre>',e['body'])[1])
  name=re.search(r'public class (\w+)',source)[1]
  z.writestr('src/'+name+'.java',source+'\n')
  expected=html.unescape(re.search(r'<pre><code class="language-text">([\s\S]*?)</code></pre>',e['body'])[1])
  outputs.append(name+'\n'+expected+'\n')
 z.writestr('EXPECTED-OUTPUTS.txt','\n'.join(outputs))
 z.writestr('README.md','# AI Trove Java tutorial programs\n\n24 complete JDK-only programs. Use a JDK supporting Java 8 or later.\n\nFrom the extracted src directory:\n\n    javac --release 8 *.java\n    java DeliveryDistances\n    java ManifestImport\n\nOn JDK 8 itself, use javac *.java. Other programs run by their public class names listed in EXPECTED-OUTPUTS.txt. These are tutorial models with the limits explained on their pages. ManifestImport creates and deletes its own temporary input file. Concurrency programs own and shut down their workers. No credentials, remote services or dependencies are required.\n')
print(json.dumps({k:report[k] for k in ['javaRoutes','articles','hubs','quizzes']}))
