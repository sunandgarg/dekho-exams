"""Publish the current Java route map and an explicit editorial handoff."""
import html,json,pathlib
ROOT=pathlib.Path(__file__).resolve().parents[1];OUT=ROOT.parent.parent/'outputs'
entries=json.loads((ROOT/'src/data/fixtures.json').read_text());lookup={e['path']:e for e in entries}
batch=json.loads((OUT/'java-depth-batch.json').read_text())
new=set(batch['added']+batch['newQuizzes']);expanded=set(batch['expanded'])
remaining={
 'java/java':['Broader nested-type and cross-package exercises.','International identifier/confusable policies beyond the bounded ASCII protocol fixture, and more locale/version-specific text tests.'],
 'java/advanced-java':['Foreign-memory APIs and broader Java/library coverage beyond the selected tested Java 25 features; preview APIs require a separate version-specific track.',
 'Framework tracks such as Spring/Jakarta and desktop Swing/JavaFX are not populated in this Java curriculum.','Production database engines: serialization/deadlock faults, pool load tests, multi-deployer schema migrations and recovery. H2 checks are not evidence for another engine.','Heap-reference-path interpretation for real incidents. Synthetic heap capture and bounded JFR event recording are verified here.','Representative multi-fork JMH experiments. Earlier smoke checks prove benchmark execution, not performance rankings.'],
 'java/java-collections':['Larger comparator, iterator and nested-mutability exercise sets.','Distributed ownership and transactional workflows beyond the in-process multi-index fixture.'],
 'java/dsa-in-java':['Ranked/compressed tries and wider graph, string and DP problems with proofs.','More adversarial large-input tests and language-independent DSA material.'],
 'java/java-interview-questions':['More multi-file code traces and real incident follow-ups.'],
 'java/java-exercises':['More difficulty-graded problems and rejection cases.','Server-judged submissions require an execution service; these exercises run locally.'],
 'java/java-examples':['More multi-package examples and external-service fault scenarios.'],
 'java/java-quizzes':['Authenticated cross-device attempt storage requires a backend; scores are browser-local.','Larger application-level trace banks beyond the current 168 questions.'],
 'java/java-projects':['External HTTP/TLS: certificate-chain rotation/expiry, DNS failures, load and end-to-end service deadlines. Local TLS verifies only its stated fixture.','Crash-durable, multi-process file publication and database-backed services. The concurrent import fixture preserves the prior file on validation failure; it is not a durability guarantee.','Deployment and real-service integration testing.'],
 'java/java-cheatsheet':['More API references, release differences and library topics beyond this selected curriculum.']}
sources=[
 ('Priority 1: LinkedList API contract','https://docs.oracle.com/javase/8/docs/api/java/util/LinkedList.html'),
 ('Priority 2: curriculum inspection','https://www.geeksforgeeks.org/java/java/'),
 ('Priority 3: topic inspection','https://www.w3schools.com/java/java_linkedlist.asp'),
 ('Priority 4: topic inspection','https://beginnersbook.com/2013/12/linkedlist-in-java-with-example/'),
 ('Priority 5: topic inspection','https://codingnomads.com/java-301-linked-lists'),
 ('ScopedValue contract, Java 25','https://docs.oracle.com/en/java/javase/25/docs/api/java.base/java/lang/ScopedValue.html'),
 ('Gatherers contract, Java 25','https://docs.oracle.com/en/java/javase/25/docs/api/java.base/java/util/stream/Gatherers.html'),
 ('BreakIterator grapheme contract, Java 25','https://docs.oracle.com/en/java/javase/25/docs/api/java.base/java/text/BreakIterator.html'),
 ('Collator contract, Java 25','https://docs.oracle.com/en/java/javase/25/docs/api/java.base/java/text/Collator.html'),
 ('Access-control rules','https://docs.oracle.com/javase/specs/jls/se25/html/jls-6.html'),
 ('Flexible constructor bodies','https://docs.oracle.com/en/java/javase/25/language/flexible-constructor-bodies.html'),
 ('Module import declarations','https://docs.oracle.com/en/java/javase/25/language/module-import-declarations.html'),
 ('Language changes by release','https://docs.oracle.com/en/java/javase/25/language/java-language-changes-summary.html'),
 ('Monitor pinning change targeted for Java 24','https://inside.java/2024/11/15/jep491-target-jdk24/'),
 ('HikariCP owner documentation','https://github.com/brettwooldridge/HikariCP'),
 ('Corretto 25 distribution and checksums','https://docs.aws.amazon.com/corretto/latest/corretto-25-ug/downloads-list.html'),
 ('SSLContext contract','https://docs.oracle.com/en/java/javase/25/docs/api/java.base/javax/net/ssl/SSLContext.html'),
 ('HttpsServer contract','https://docs.oracle.com/en/java/javase/25/docs/api/jdk.httpserver/com/sun/net/httpserver/HttpsServer.html'),
 ('jcmd owned-process diagnostic commands','https://docs.oracle.com/en/java/javase/25/docs/specs/man/jcmd.html'),
 ('H2 behavior and isolation scope','https://www.h2database.com/html/advanced.html'),
 ('Shortest paths, reference authors','https://algs4.cs.princeton.edu/44sp/'),
 ('Directed graphs, reference authors','https://algs4.cs.princeton.edu/42digraph/')]
routes={e['path'] for e in entries if e['path'].startswith('java/') or e['type']=='quiz' and e.get('subject')=='java-quizzes'}
assert len(routes)==batch['articles']+batch['hubs']+batch['quizzes']==209
sections=[];linked=set()
for tab in lookup['java/java']['data']['resource_tabs']:
 hub=lookup[tab['path']];modules=[]
 for module in hub['data']['modules']:
  assert len(module['lessons'])==len(set(module['lessons']))
  modules.append({'title':module['title'],'lessons':[{'path':p,'title':lookup[p]['title'],'status':'new' if p in new else 'expanded' if p in expanded else 'existing'} for p in module['lessons']]})
  linked.update(module['lessons'])
 linked.add(hub['path']);sections.append({'path':hub['path'],'title':tab['title'],'modules':modules,'remaining':remaining[hub['path']]})
unlisted=sorted(routes-linked)
assert not unlisted,unlisted
programs=json.loads((OUT/'java-program-check.json').read_text());properties=json.loads((OUT/'java-depth-properties.json').read_text());dependencies=json.loads((OUT/'java-depth-dependency-check.json').read_text())
report={**batch,'javaRoutes':len(routes),'changedUniqueRoutes':len(new|expanded),'sections':sections,'sources':[{'purpose':p,'url':u} for p,u in sources],'remaining':'The selected Java curriculum is populated, but Java is not exhaustively covered. WordPress import, production deployment, server judging and authenticated quiz storage remain pending.','verification':{'programs':programs,'properties':properties,'dependencies':dependencies}}
if (OUT/'java-depth-browser-check.json').exists(): report['verification']['browser']=json.loads((OUT/'java-depth-browser-check.json').read_text())
(OUT/'java-depth-coverage.json').write_text(json.dumps(report,indent=2)+'\n')
(OUT/'aitrove-java-full-content.json').write_text(json.dumps([e for e in entries if e['path'] in routes],indent=2,ensure_ascii=False)+'\n')
changed=new|expanded|{s['path'] for s in sections}
(OUT/'aitrove-java-depth-content.json').write_text(json.dumps([e for e in entries if e['path'] in changed],indent=2,ensure_ascii=False)+'\n')
esc=html.escape;branches=[]
for section in sections:
 modules=[]
 for module in section['modules']:
  links=''.join('<li data-status="'+l['status']+'"><a href="http://127.0.0.1:3001/'+l['path']+'">'+esc(l['title'])+'</a> <span>'+l['status'].capitalize()+'</span></li>' for l in module['lessons'])
  modules.append('<details open><summary>'+esc(module['title'])+'</summary><ul>'+links+'</ul></details>')
 modules.append('<details class="remaining" open><summary>Still remaining</summary><ul>'+''.join('<li>'+esc(t)+'</li>' for t in section['remaining'])+'</ul></details>')
 branches.append('<section class="branch"><h2><a href="http://127.0.0.1:3001/'+section['path']+'">'+esc(section['title'])+'</a></h2>'+''.join(modules)+'</section>')
previous=(OUT/'java-next-coverage.html').read_text();style=previous.split('<style>')[1].split('</style>')[0];script=previous.split('<script>')[1].split('</script>')[0]
intro=f'<p><strong>{len(routes)} content routes: {batch["articles"]} articles, {batch["hubs"]} hubs, {batch["quizzes"]} quizzes and {batch["quizQuestions"]} questions.</strong></p><p>This pass adds {len(batch["added"])} articles, expands {len(batch["expanded"])} articles and adds three quiz banks. Every listed route is present; existing means present, not exhaustive API coverage. Each quiz also has generated attempt and review URLs, checked separately.</p><p>Checks target Java 8, 11, 17, 21 and 25: {programs["programsAndFragmentsCompiled"]} compiled code units, {programs["programsAndFragmentsExecuted"]} executions, {programs["declaredOutputsChecked"]} declared outputs, 22 dependency tests and {properties["checks"]:,} algorithm/boundary checks. JMH verification from the earlier pass checks execution only.</p><p><a href="http://127.0.0.1:3001/java/java">Open Java locally</a> · <a href="http://127.0.0.1:3001/downloads/aitrove-java-source-kit.zip" download>Download source kit</a></p>'
doc='<!doctype html><html lang="en"><head><meta charset="utf-8"><meta name="viewport" content="width=device-width,initial-scale=1"><title>AI Trove Java coverage · 29 September</title><style>'+style+'</style></head><body><main><h1>AI Trove Java · coverage and remaining work</h1><div class="intro">'+intro+'</div><div class="controls"><input id="find" aria-label="Find a topic" placeholder="Find a topic"><select id="show" aria-label="Show"><option value="all">All coverage</option><option value="new">New and expanded</option><option value="remaining">Remaining only</option></select></div>'+''.join(branches)+'<p>No content was pushed, deployed or imported into WordPress.</p></main><script>'+script+'</script></body></html>'
(OUT/'java-depth-coverage.html').write_text(doc);(ROOT/'public/java-coverage.html').write_text(doc)
lines=['# AI Trove Java depth pass','',f'{len(batch["added"])} new articles, {len(batch["expanded"])} expanded articles and three new quiz banks. Current total: {batch["articles"]} articles, 10 hubs, 14 quizzes, 168 questions and 209 content routes. Quiz attempt/review pages use shared templates and are verified separately. New prose: {batch["newProseWords"]:,} words; including programs/output: {batch["newWordsIncludingCode"]:,}.','', '## Originality and scope','', 'Research verified API contracts and topic coverage. Explanations and programs were written for AI Trove; changing identifiers in copied programs is not the writing process. Java facts, APIs, third-party logos and dependency code are not exclusive AI Trove property. Generated content is not claimed to be human-authored, and AI-detector outcomes are not guaranteed. Research links stay in this handoff; public lesson bodies use internal learning links.','', 'The approved 16-card Explore homepage is preserved. The preview uses local CMS fixtures; the full 209-entry JSON and changed 47-entry JSON are later WordPress import payloads. No import, push or deployment took place.','', '## Verification','',f'{programs["programsAndFragmentsCompiled"]} JDK code units compiled; {programs["programsAndFragmentsExecuted"]} ran; {programs["declaredOutputsChecked"]} declared outputs matched. Release targets: 8, 11, 17, 21 and 25. Corretto 25 was downloaded from its official distribution, checksum-verified and installed inside the ignored task folder; system Java was not changed. Hikari source also compiled with release 17. The Maven dependency suite passed 22 tests with no failures, errors or skips. New property tests passed {properties["checks"]:,} checks across twelve topics. Three invalid cross-package accesses failed compilation as required. jcmd inspected only the spawned fixture: fifty retained entries and an HPROF capture, removed after verification. Local TLS checked exact trust and rejected the wrong hostname. HTTP retry and concurrent import checks have stated bounds, not production reliability guarantees.','', 'See java-program-check.json, java-depth-properties.json, java-depth-dependency-check.json, java-depth-boundaries-check.json and java-depth-browser-check.json. Earlier named-module, Gradle and JMH checks are recorded in java-finish reports; their unchanged fixtures were not retested in this pass. JMH smoke results are not a speed ranking. The 193-file source kit includes 159 standalone full JDK source units plus dependency/build/access/diagnostic fixtures, without binaries or secrets. Java 25 sources need JDK 25; external dependencies require their listed build tools.','', '## Research in requested order, then primary references','']
lines += [f'- [{p}]({u})' for p,u in sources]
lines += ['', 'The five requested pages were inspected. Secondary tutorial sites informed coverage inspection; technical contracts came from primary references and executable checks. Direct OpenJDK JEP pages returned HTTP 403, so they are not claimed as reviewed. The attempted compact-source Oracle page redirected to a newer release index; the compact-source example was verified with the actual JDK 25 compiler/runtime instead. This was targeted research, not a crawl of the entire internet.','', '## Remaining','']
for section in sections:lines += ['### '+section['title'],'']+['- '+t for t in section['remaining']]+['']
lines += ['WordPress import, deployment, server judging and authenticated cross-device quiz storage remain separate. The archive does not include a Gradle wrapper or dependencies. Exhaustive coverage of the Java language, releases, libraries and frameworks is not claimed.','', '## Changed articles','']+[f'- [{lookup[p]["title"]}](http://127.0.0.1:3001/{p})' for p in batch['added']+batch['expanded']]
(OUT/'java-depth-editorial-handoff.md').write_text('\n'.join(lines)+'\n')
print(json.dumps({'javaRoutes':len(routes),'newArticles':len(batch['added']),'expandedArticles':len(batch['expanded']),'changedUniqueRoutes':len(new|expanded),'batchExportEntries':len(changed)}))
