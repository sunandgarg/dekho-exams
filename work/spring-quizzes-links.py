import copy,datetime,html,json,pathlib,uuid,re
ROOT=pathlib.Path(__file__).resolve().parents[1];f=ROOT/'src/data/fixtures.json';es=json.loads(f.read_text());lookup={e['path']:e for e in es};stamp=datetime.datetime.now(datetime.UTC).isoformat()
banks={
'core':('Spring Core ownership quiz',['application-context','constructor-injection','qualifiers','bean-scopes','object-provider','lifecycle-cleanup','application-events','proxy-self-invocation'],[
('What does a singleton scope guarantee for one bean definition in one context?',['One shared instance','Automatic thread safety','One instance for the entire network'],0,'Instance reuse and thread safety are separate contracts.'),
('A prototype is injected once into a singleton. What does that field hold?',['A new object for every method call','The instance resolved at injection','A new object per thread'],1,'Ordinary injection supplies one reference at construction or injection time.'),
('How does the kit request two fresh prototype buffers?',['Repeated calls to ObjectProvider.getObject','Two reads of one injected field','Mark the field volatile'],0,'Each prototype resolution creates an instance; a field read does not resolve it again.'),
('Two Exporter beans exist. A plain type lookup has no other selection rule. What is expected?',['The most recently registered bean','Automatic alphabetic selection','An ambiguity failure'],2,'The fixture expects NoUniqueBeanDefinitionException and uses a qualifier for intentional wiring.'),
('Why does the direct report unit test need no context?',['Every bean is static','Its collaborator is an ordinary constructor argument','Unit tests automatically inject objects'],1,'Required dependencies stay visible and can be supplied directly.'),
('What closes the fixture singleton ClosingChannel?',['Closing its owning context','Reading its final field','Returning from render'],0,'The context delivers the destruction callback for this managed singleton.'),
('Does prototype scope provide the same managed destruction as singleton scope?',['Yes for every resource','Only when final','No; the caller owns cleanup after resolution'],2,'Prototype initialization and destruction have different ownership rules.'),
('What does a local application event provide in this kit?',['Durable replay after restart','Local listener delivery','A broker acknowledgement'],1,'The fixture is local and does not persist or replay work.'),
('The target outer method directly calls inner. How many proxy entries does the fixture advise?',['One','Two','Zero'],0,'Only outer enters through the proxy reference; the target-to-target call does not.'),
('Does qualifier wiring validate a runtime document format?',['Yes automatically','No; capability validation is separate','Only with prototype scope'],1,'The qualifier chooses a bean during assembly, not a domain format policy.'),
('When should a test create a new full application context?',['For every string comparison','Whenever it calls a constructor','When the contract needs actual container assembly'],2,'Select the smallest boundary that supplies the required evidence.'),
('Can a deferred provider conceal a missing required bean until runtime?',['Yes','No; every provider is eager','Only for records'],0,'Deferred resolution changes when lookup failure can occur, so mandatory dependencies need an intentional boundary.')]),
'web-security':('Spring MVC and security boundary quiz',['rest-validation','problem-details','pagination-bounds','cors-boundaries','security-filter-chain','password-encoding','mockmvc-tests'],[
('What does a positive amount constraint prove?',['The caller owns the receipt','The input value meets that constraint','The payment settled'],1,'Validation does not establish authorization or settlement.'),
('Which response does the kit promise for a created valid receipt?',['201 with the receipt representation','200 with an exception stack trace','204 with SQL diagnostics'],0,'The controller test checks creation status and the response amount.'),
('Why repeat an amount invariant inside the store?',['To avoid tests','Because JSON needs two parsers','Non-HTTP callers can bypass controller validation'],2,'Domain invariants belong to the business boundary as well as the transport boundary.'),
('What does ProblemDetail avoid requiring a client to parse?',['An English exception stack trace','The HTTP status','The response media type'],0,'A structured error keeps public behavior separate from internal diagnostics.'),
('Does a standalone MockMvc setup automatically prove the real security chain?',['Yes','No; include security integration for that claim','Only when the controller is final'],1,'Supplied controllers and validators are a narrower boundary than the full filter chain.'),
('Is CORS user authentication?',['For GET requests','For credentialed requests','No'],2,'A browser origin policy does not identify or authorize a user.'),
('A Basic header is present but CSRF validation rejects before authentication. Must the result be 403?',['Yes','No; filter order can lead to a 401 challenge','Only with JSON'],1,'The kit checks pre-authentication rejection separately from established-user rejection.'),
('What happens to a protected POST with an established test user but no CSRF token?',['403 in this fixture','201','The controller invents a token'],0,'The filter-chain test confirms forbidden mutation for that established-user request.'),
('Two encodings of the same password differ. Is verification necessarily broken?',['Yes','Only if the password is long','No; the encoder uses salt'],2,'Use matches with the stored encoding rather than comparing a freshly encoded string.'),
('Does a page of twenty rows imply O(20) work in this in-memory store?',['Yes','No; it copies the whole collection first','Only for offset zero'],1,'Response size and the cost of producing the response are different dimensions.'),
('What does the immutable returned page prevent?',['Mutation of that response list','All future updates to the store','Every element from ever changing'],0,'Container immutability does not freeze unrelated service state or arbitrary referenced elements.'),
('May the source-kit local-reader account be treated as production identity storage?',['Yes if the name is changed','Yes if the port is random','No'],2,'It is a reproducible fixture; deployment needs real credential and account ownership.')]),
'data-production':('Spring data and production contract quiz',['jdbc-template','transactions','transaction-proxies','async-boundaries','cache-keys','actuator-health','receipt-api-project'],[
('What does placeholder binding protect in the ledger insert?',['The bound values','Arbitrary table-name text','The entire network'],0,'SQL structure stays fixed; structural choices need a separate allowlist.'),
('A transaction inserts one valid row then violates a constraint. What does the kit check afterward?',['The exception class only','Zero committed rows','A log message only'],1,'Persisted state after failure is the evidence for rollback.'),
('A transaction callback marks rollback-only and returns normally. Must it commit?',['Yes','Only for inserts','No'],2,'The transaction state explicitly requests rollback despite normal callback return.'),
('Can JDBC rollback retract an HTTP operation already accepted by another server?',['No','Yes if called in a callback','Only on Java 21'],0,'Local database atomicity cannot reverse an independent external side effect.'),
('Does H2 prove every production database lock and isolation behavior?',['Yes','No','Only with prepared statements'],1,'The local fixture needs separate target-database evidence before production isolation claims.'),
('A bounded executor rejects its third task. Should the service silently claim success?',['Yes','Only during startup','No'],2,'Rejected admission needs a visible application outcome.'),
('Does a queue capacity of one bound retained payload bytes to one byte?',['No','Yes','Only for string payloads'],0,'A queued closure can retain a large payload; task count and bytes are separate bounds.'),
('What is missing from a cache key containing only receiptId in a multi-tenant lookup?',['The Java class name','Tenant ownership','The process port'],1,'The fixture includes tenant and receipt identifier so results do not cross owners.'),
('The kit uses ConcurrentMapCacheManager. Does that supply distributed invalidation?',['Yes','Only on Linux','No'],2,'This context-local cache has no distributed consistency or eviction policy.'),
('Why check the loader call count in the cache test?',['Identical output alone does not prove cache hits','It replaces tenant tests','It measures real throughput'],0,'The counter confirms which requests actually reached the target loader.'),
('Does public health access imply all management endpoints are public?',['Yes','No; endpoint exposure and authorization are explicit','Only for JSON'],1,'The fixture allows anonymous health and protects other paths.'),
('Where does the receipt API actually store its receipts?',['The separate JDBC teaching table','A remote payment service','The in-memory ReceiptStore'],2,'The project makes the persistence limit explicit; the JDBC fixture is not wired as its repository.')])}
new=[]
for slug,(title,reviews,questions) in banks.items():
 path='quizzes/spring-'+slug;body='<p>A Spring self-check tests '+html.escape(title.lower().replace(' quiz',''))+' using the source-kit contracts.</p><h2>Review before answering</h2><ul>'+''.join('<li><a href="/spring/'+s+'">'+html.escape(lookup['spring/'+s]['title'])+'</a></li>' for s in reviews)+'</ul><h2>Check your reasoning</h2><p>Answer every question, then read the explanations. This browser self-check is not a credential or a server-side code judge.</p><h3>Common Mistakes</h3><p>Distinguish a checked local fixture from a production guarantee. Container ownership, database atomicity and request authorization require separate evidence.</p>'
 e=copy.deepcopy(lookup['quizzes/java-25']);e.update(id=str(uuid.uuid5(uuid.NAMESPACE_URL,'https://aitrove.in/'+path)),path=path,title=title,summary='Twelve explained questions on '+title.lower().replace(' quiz','')+'.',body=body,category='Backend Frameworks',subject='spring-quizzes',tags=['spring','spring-boot','quiz'],created_at=stamp,published_at=stamp,updated_at=stamp,sort_order=600+len(new))
 e['data']={'questions':[{'prompt':q,'options':opts,'answer':answer,'explanation':explain} for q,opts,answer,explain in questions],'duration_minutes':15,'subject_root':'spring/spring-boot','section_path':'spring/quizzes','content_format':'html','seo_ready':True}
 if path in lookup:es[es.index(lookup[path])]=e
 else:es.append(e)
 lookup[path]=e;new.append(path)
quizhub=lookup['spring/quizzes'];quizhub['data']['modules']=[{'title':'Core, HTTP and production contracts','summary':'Twelve questions per bank with checked explanations.','lessons':new}];quizhub['body']+='<h2>Choose a self-check</h2><ul>'+''.join('<li><a href="/'+s+'">'+html.escape(lookup[s]['title'])+'</a></li>' for s in new)+'</ul>' if '<h2>Choose a self-check</h2>' not in quizhub['body'] else ''
# Useful two-way links; no Spring module is placed in a Java curriculum.
connections={
'interfaces':['constructor-injection','qualifiers'], 'classes-objects':['application-context','bean-scopes'],
'generics':['object-provider'], 'reflection':['proxy-self-invocation'], 'annotations':['rest-validation','transaction-proxies'],
'exceptions':['problem-details'], 'records':['configuration-properties','rest-validation'],
'properties-validation':['configuration-properties','profiles-properties'], 'maven':['bootstrap','receipt-api-project'],
'jdbc-prepared':['jdbc-template'], 'jdbc-transactions':['transactions','transaction-proxies'], 'database-isolation':['transactions'],
'connection-pool':['jdbc-template'], 'test-boundaries':['testing-boundaries','context-testing'], 'junit-tests':['mockmvc-tests'],
'executors':['async-boundaries'], 'thread-local-cleanup':['async-boundaries'], 'concurrent-map':['cache-keys'],
'immutable-collections':['pagination-bounds'], 'http-client':['cors-boundaries','receipt-api-project'],
'http-failure-project':['receipt-api-project'], 'secure-random-tokens':['password-encoding'], 'clock-injection':['constructor-injection']}
for slug,targets in connections.items():
 e=lookup['java/'+slug];heading='<h2>Apply this contract in Spring</h2>'
 if heading in e['body']:e['body']=e['body'].split(heading)[0]
 e['body']+=heading+'<p>'+', '.join('<a href="/spring/'+s+'">'+html.escape(lookup['spring/'+s]['title'])+'</a>' for s in targets)+'. These lessons keep framework assembly separate from the Java contract.</p>'
 e['data'].setdefault('related',[])
 for s in targets:
  if not any(x['path']=='spring/'+s for x in e['data']['related']):e['data']['related'].append({'path':'spring/'+s,'title':lookup['spring/'+s]['title']})
 e['updated_at']=stamp
# Related labels use the final canonical title, and new entries have their own creation dates.
for e in es:
 if e['path'].startswith('spring/') or e['path'] in json.loads((ROOT.parent.parent/'outputs/java-spring-java-additions.json').read_text())['added']:e['created_at']=e['published_at']
 for link in e.get('data',{}).get('related',[]):
  if link['path'] in lookup:link['title']=lookup[link['path']]['title']
f.write_text(json.dumps(es,ensure_ascii=False,indent=2)+'\n')
print(json.dumps({'springQuizzes':len(new),'newQuestions':sum(len(v[2]) for v in banks.values()),'javaToSpringLinks':sum(len(v) for v in connections.values())}))
