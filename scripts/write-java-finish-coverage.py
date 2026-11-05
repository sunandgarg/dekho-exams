"""Publish a route-level map, research handoff and explicit remaining scope."""
import html,json,pathlib
ROOT=pathlib.Path(__file__).resolve().parents[1];OUT=ROOT.parent.parent/'outputs'
entries=json.loads((ROOT/'src/data/fixtures.json').read_text());lookup={e['path']:e for e in entries}
batch=json.loads((OUT/'java-finish-batch.json').read_text())
new=set(batch['added']+batch['newQuizzes']);expanded=set(batch['expanded']+batch['expandedQuizzes'])
remaining={
 'java/java':['More nested access-control exercises across separate packages.','Unicode grapheme segmentation, confusable identifiers and locale-specific collation.'],
 'java/advanced-java':['Production database isolation, pools, migrations and engine-specific fault tests.','Heap-dump interpretation and a longer JFR incident workflow.','Java features beyond the current tested Java 21 baseline.','JMH fixture passed a short execution check; a representative multi-fork experiment is still separate work.'],
 'java/java-collections':['Larger combined comparator, iterator and nested-mutability exercise sets.','Application-level atomic workflows spanning multiple concurrent structures.'],
 'java/dsa-in-java':['AVL deletion; trie deletion and ranked suggestions.','Wider graph/string/DP problem sets and complexity proofs.'],
 'java/java-interview-questions':['More interview follow-ups using multi-file applications and production incident traces.'],
 'java/java-exercises':['More difficulty-graded algorithm practice and mutation/rejection cases.','Server-judged submissions require an execution service; current exercises run locally.'],
 'java/java-examples':['More multi-package examples and external-service fault scenarios.'],
 'java/java-quizzes':['Authenticated cross-device attempt storage requires a backend; current scores are browser-local.','Larger banks with application-level code-trace questions.'],
 'java/java-projects':['Concurrent persisted application with load tests and end-to-end deadlines.','External HTTP/TLS, pooled production database and deployment failure testing.','Reading-list persistence is a bounded single-writer file fixture, not crash-durable storage.'],
 'java/java-cheatsheet':['References for Java releases beyond 21 after their contracts and examples are verified.']}
sources=[
('Priority 1: LinkedList API contract','https://docs.oracle.com/javase/8/docs/api/java/util/LinkedList.html'),
('Priority 2: curriculum inspection','https://www.geeksforgeeks.org/java/java/'),
('Priority 3: topic inspection','https://www.w3schools.com/java/java_linkedlist.asp'),
('Priority 4: topic inspection','https://beginnersbook.com/2013/12/linkedlist-in-java-with-example/'),
('Priority 5: topic inspection','https://codingnomads.com/java-301-linked-lists')]
api=[('lang/Module',21),('util/concurrent/CopyOnWriteArrayList',8),('util/concurrent/ConcurrentSkipListMap',8),('lang/ref/WeakReference',8),('util/SequencedCollection',21),('util/concurrent/locks/Condition',8),('util/concurrent/Semaphore',8),('util/concurrent/Future',8),('nio/channels/FileChannel',8),('net/Socket',8),('text/Normalizer',8),('util/List',21),('util/Comparator',8),('util/concurrent/ScheduledExecutorService',8),('lang/ClassLoader',8),('util/regex/Pattern',8),('sql/Connection',8),('lang/Record',21)]
for path,version in api:
 sources.append((path+' contract',('https://docs.oracle.com/javase/8/docs/api/java/' if version==8 else 'https://docs.oracle.com/en/java/javase/21/docs/api/java.base/java/')+path+'.html'))
sources.extend([
('Numeric/reference conversion rules','https://docs.oracle.com/javase/specs/jls/se8/html/jls-5.html'),
('Memory model','https://docs.oracle.com/javase/specs/jls/se21/html/jls-17.html'),
('JVM runtime structure','https://docs.oracle.com/javase/specs/jvms/se21/html/jvms-2.html'),
('Interrupt propagation','https://docs.oracle.com/javase/tutorial/essential/concurrency/interrupt.html'),
('JFR recording API','https://docs.oracle.com/en/java/javase/21/docs/api/jdk.jfr/jdk/jfr/Recording.html'),
('HTTP client API','https://docs.oracle.com/en/java/javase/21/docs/api/java.net.http/java/net/http/HttpClient.html'),
('JDBC transaction contract','https://docs.oracle.com/javase/tutorial/jdbc/basics/transactions.html'),
('JUnit 5.11 test contract','https://docs.junit.org/5.11.0/user-guide/'),
('Gradle Java build contract','https://docs.gradle.org/current/userguide/building_java_projects.html'),
('OpenJDK JMH build and benchmark runner','https://github.com/openjdk/jmh'),
('H2 integration fixture contract','https://www.h2database.com/html/tutorial.html'),
('Java learning/module coverage','https://dev.java/learn/'),
('Spanning-tree algorithm reference','https://algs4.cs.princeton.edu/43mst/'),
('String search algorithm reference','https://algs4.cs.princeton.edu/53substring/'),
('Trie algorithm reference','https://algs4.cs.princeton.edu/52trie/')])
routes={e['path'] for e in entries if e['path'].startswith('java/') or e['type']=='quiz' and e.get('subject')=='java-quizzes'}
(OUT/'aitrove-java-full-content.json').write_text(json.dumps([e for e in entries if e['path'] in routes],indent=2,ensure_ascii=False)+'\n')
sections=[];linked=set()
for tab in lookup['java/java']['data']['resource_tabs']:
 hub=lookup[tab['path']];modules=[]
 for module in hub['data']['modules']:
  modules.append({'title':module['title'],'lessons':[{'path':p,'title':lookup[p]['title'],'status':'new' if p in new else 'expanded' if p in expanded else 'existing'} for p in module['lessons']]})
  linked.update(module['lessons'])
 linked.add(hub['path']);sections.append({'path':hub['path'],'title':tab['title'],'modules':modules,'remaining':remaining[hub['path']]})
# Include every actual route, even a helper page outside a visible module.
unlisted=sorted(routes-linked)
if unlisted:
 sections[0]['modules'].append({'title':'Supporting Java pages','lessons':[{'path':p,'title':lookup[p]['title'],'status':'new' if p in new else 'expanded' if p in expanded else 'existing'} for p in unlisted]})
report={**batch,'javaRoutes':len(routes),'sections':sections,'sources':[{'purpose':p,'url':u} for p,u in sources],'remaining':'Core curriculum pages are present, but Java is not exhaustively covered. WordPress import and any production deployment are still pending.'}
(OUT/'java-finish-coverage.json').write_text(json.dumps(report,indent=2))
esc=html.escape;branches=[]
for section in sections:
 modules=[]
 for module in section['modules']:
  links=''.join('<li data-status="'+l['status']+'"><a href="http://127.0.0.1:3001/'+l['path']+'">'+esc(l['title'])+'</a> <span>'+l['status'].capitalize()+'</span></li>' for l in module['lessons'])
  modules.append('<details open><summary>'+esc(module['title'])+'</summary><ul>'+links+'</ul></details>')
 modules.append('<details class="remaining" open><summary>Still remaining</summary><ul>'+''.join('<li>'+esc(t)+'</li>' for t in section['remaining'])+'</ul></details>')
 branches.append('<section class="branch"><h2><a href="http://127.0.0.1:3001/'+section['path']+'">'+esc(section['title'])+'</a></h2>'+''.join(modules)+'</section>')
# Reuse the already verified responsive skeleton's static style and filtering script.
previous=(OUT/'java-next-coverage.html').read_text()
style=previous.split('<style>')[1].split('</style>')[0];script=previous.split('<script>')[1].split('</script>')[0]
intro=f'<p><strong>{len(routes)} local routes: {batch["javaArticles"]} articles, 10 hubs, 11 quizzes and 132 questions.</strong></p><p>This pass adds {len(batch["added"])} articles, expands {len(batch["expanded"])} articles and updates every quiz bank. Core curriculum pages are present. Existing means present, not exhaustive coverage of an API.</p><p>Build, runtime and boundary checks target Java 8, 11, 17 and 21. JMH verification checks execution only. Backend judging and WordPress publishing remain separate work.</p><p><a href="http://127.0.0.1:3001/java/java">Open Java locally</a> · <a href="http://127.0.0.1:3001/downloads/aitrove-java-source-kit.zip" download>Download source kit</a></p>'
doc='<!doctype html><html lang="en"><head><meta charset="utf-8"><meta name="viewport" content="width=device-width,initial-scale=1"><title>AI Trove Java coverage · 29 September</title><style>'+style+'</style></head><body><main><h1>AI Trove Java · coverage and remaining work</h1><div class="intro">'+intro+'</div><div class="controls"><input id="find" aria-label="Find a topic" placeholder="Find a topic"><select id="show" aria-label="Show"><option value="all">All coverage</option><option value="new">New and expanded</option><option value="remaining">Remaining only</option></select></div>'+''.join(branches)+'<p>No content was pushed, deployed or imported into WordPress.</p></main><script>'+script+'</script></body></html>'
(OUT/'java-finish-coverage.html').write_text(doc)
(ROOT/'public/java-coverage.html').write_text(doc)
lines=['# AI Trove Java completion pass','',f'{len(batch["added"])} new articles, {len(batch["expanded"])} expanded articles, 6 new and 5 expanded quizzes. {len(routes)} routes total, 132 questions.','', '## Originality and scope','', 'Research checked API contracts and topic coverage. New explanations and programs were written for AI Trove, rather than copying examples and changing identifiers. Java facts, APIs, third-party logos and dependencies are not exclusive AI Trove property. No claim of human authorship or guaranteed AI-detector results is made. The public tutorial bodies contain internal learning links; source URLs are kept here.','', 'The approved 16-card Explore homepage is preserved. Java content stays within Java lessons and curricula. This preview still uses local CMS fixtures; the JSON export is a later WordPress import payload, not an already completed CMS import.','', '## Verification','', 'See java-program-check.json: 144 compiled JDK programs/fragments, 135 executions and 120 exact output checks. Dependencies are checked separately: 19 JUnit/H2 cases, two named modules, the two-project Gradle build, and both JMH benchmarks in a short execution run. java-finish-properties.json records 2,385,569 checks over nine new algorithm/concurrency topics. The website build passed. java-finish-browser-check.json verifies all 45 new screens, 132 quiz answers/explanations, 175 route responses, download equality, search, six viewport widths and mobile contents/heading jumps.','', '## Research in requested priority order, then primary references','']
lines += [f'- [{p}]({u})' for p,u in sources]
lines += ['', '## Remaining', '']
for section in sections:lines += ['### '+section['title'],'']+['- '+t for t in section['remaining']]+['']
lines += ['WordPress import, deployment, backend judging and authenticated cross-device quiz storage have not been performed. The downloadable source kit does not bundle third-party binaries or a Gradle wrapper. The JMH smoke scores are not a performance ranking. A complete internet crawl or exhaustive coverage of Java libraries is not claimed.','', '## Changed articles', '']+[f'- [{lookup[p]["title"]}](http://127.0.0.1:3001/{p})' for p in batch['added']+batch['expanded']]
(OUT/'java-finish-editorial-handoff.md').write_text('\n'.join(lines)+'\n')
print(json.dumps({'javaRoutes':len(routes),'newArticles':len(batch['added']),'expandedArticles':len(batch['expanded']),'changedUniqueRoutes':len(new|expanded),'supportingRoutes':unlisted}))
