"""Publish original, source-kit-backed Spring lessons under a separate subject."""
import copy,datetime,html,json,pathlib,re,uuid
ROOT=pathlib.Path(__file__).resolve().parents[1];FILE=ROOT/'src/data/fixtures.json'
entries=json.loads(FILE.read_text()); lookup={e['path']:e for e in entries};stamp=datetime.datetime.now(datetime.UTC).isoformat()
HUBS=[('spring-boot','Spring & Spring Boot','Boot foundations','spring-boot'),('spring-core','Spring Core','Container and object ownership','spring-core'),('web-apis','Web APIs','HTTP input and response contracts','spring-web'),('data-transactions','Data & Transactions','Bound queries and atomic changes','spring-data'),('security','Security','Authentication and browser boundaries','spring-security'),('testing','Testing','Choose the right test boundary','spring-testing'),('production','Production','Capacity, cache and health boundaries','spring-production'),('exercises','Exercises','Reproduce and repair failures','spring-exercises'),('quizzes','Quizzes','Check the contracts','spring-quizzes'),('projects','Projects','Build and inspect an application','spring-projects')]
root='spring/spring-boot'; paths={subject:'spring/'+slug for slug,title,summary,subject in HUBS}; added=[]
def para(s):
 text=html.escape(s)
 return '<p>'+re.sub(r'\[\[([^|]+)\|([^\]]+)\]\]',lambda m:'<a href="/'+m[1]+'">'+m[2]+'</a>',text)+'</p>'
def code(s,lang='java'):return '<pre><code class="language-'+lang+'">'+html.escape(s.strip(),quote=False)+'</code></pre>'
def source(name,test=False):return (ROOT/'work/spring-kit'/('src/test/java/in/aitrove/learning' if test else 'src/main/java/in/aitrove/learning')/(name+'.java')).read_text()
def put(slug,title,definition,sections,program,cost,mistakes,related,subject='spring-core',lang='java',proof='CoreBoundaryTest'):
 path='spring/'+slug; body=para(definition)+para('This lesson uses the downloadable source kit: Java 21, Spring Boot 4.0.8 and its managed Spring Framework 7 dependencies. The version is pinned for repeatable builds.')
 for heading,paragraphs in sections:body+='<h2>'+heading+'</h2>'+''.join(para(s) for s in paragraphs)
 body+='<h2>Checked source</h2>'+code(program,lang)+'<h2>Test the boundary</h2>'+para('Run mvn test in the source-kit directory. '+proof+' checks the behavior described here. Java excerpts belong to the named source-kit classes; they are not independent source files unless the complete class is shown.')
 body+='<h2>Costs and boundaries</h2>'+para(cost)+'<h3>Common Mistakes</h3><ul>'+''.join('<li>'+html.escape(s)+'</li>' for s in mistakes)+'</ul><h2>Read next</h2>'+para(', '.join('[['+s+'|'+lookup.get(s,{}).get('title',s.split('/')[-1].replace('-',' ').capitalize())+']]' for s in related)+'.')
 e=copy.deepcopy(lookup['java/casts']);e.update(id=str(uuid.uuid5(uuid.NAMESPACE_URL,'https://aitrove.in/'+path)),path=path,title=title,summary=definition,body=body,category='Backend Frameworks',subject=subject,tags=['spring','spring-boot',slug],difficulty='Intermediate',sort_order=500+len(added),published_at=stamp,updated_at=stamp,status='published',featured=False)
 e['data']={'subject_root':root,'section_path':paths[subject],'content_format':'html','kind':'tutorial','framework_version':'Spring Boot 4.0.8 / Spring Framework 7','java_version':'21 source-kit baseline','reading_minutes':max(4,round(len(re.sub('<[^>]*>',' ',body).split())/150)),'author_path':'authors/aitrove-editorial','download_path':'/downloads/aitrove-spring-source-kit.zip','related':[{'path':s,'title':lookup.get(s,{}).get('title',s.split('/')[-1].replace('-',' '))} for s in related],'seo_ready':True,'verification_suite':proof}
 if path in lookup:entries[entries.index(lookup[path])]=e
 else:entries.append(e)
 lookup[path]=e;added.append(path)

put('application-context','Spring ApplicationContext: construct and close an object graph',
'An ApplicationContext creates and connects registered bean definitions and manages the lifecycle of container-owned objects.',
[('Register before refreshing',[
'The report fixture registers an exporter and a report service, then refreshes the context. Refresh is a lifecycle transition: definitions become usable instances and missing dependencies can fail startup. Calling getBean before completing that transition is not a way to test business behavior.',
'A [[java/interfaces|Java interface]] separates the report contract from its exporter implementation. The context assembles that graph; the report still performs an ordinary Java method call. Avoid retrieving collaborators from a global context inside the report, because the constructor would then hide what the object actually requires.'
]),('Close the owner',[
'The complete ContainerContracts program opens a context in try-with-resources. Its singleton ClosingChannel is destroyed when the context closes, and the displayed closed flag confirms that lifecycle boundary. A stopped test must not keep container-owned pools and channels alive.',
'A context is not a database transaction or a request scope. Reusing a singleton report gives shared object identity within that definition and context, but says nothing about the safety of mutable fields. [[java/multi-index-invariants|Ownership rules]] still belong to the application.'
])],source('ContainerContracts'),'Startup cost depends on the number of definitions, dependencies and initialization work. This four-bean fixture does not measure a production application’s startup time. Do not build a new context per report request.',
['Register definitions before refresh.','Close a context created by a test.','Do not mistake container reuse for thread safety.'],['spring/constructor-injection','spring/bean-scopes','java/interfaces'])
put('constructor-injection','Spring constructor injection: required dependencies stay visible',
'Constructor injection supplies required collaborators when an object is created, so the object does not need to locate them during an operation.',
[('Keep business code ordinary',[
'ReceiptReport accepts Exporter in its constructor and stores it in a final field. The same class works when constructed directly in a unit test or created through the container. That is the useful boundary: choosing the implementation is assembly work, while rendering is business work.',
'The CoreBoundaryTest constructs the report without a context and verifies csv:receipt. Starting a web server to test that one method would add unrelated configuration, filters and serialization behavior. [[java/test-boundaries|Small tests]] expose the dependency contract with less machinery.'
]),('Cycles signal an ownership problem',[
'If service A requires B and B requires A to finish construction, there is no valid first complete object. Adding lazy lookup can defer the failure while preserving the design problem. Move the shared policy or orchestration into a third object when that matches the domain.',
'Injecting a Clock is the same pattern applied to time. A reservation service can ask its clock for the current instant rather than making hidden static reads. [[java/clock-injection|Expiry boundary tests]] then choose exact instants instead of waiting.'
])],'''public static class ReceiptReport {
    private final Exporter exporter;
    public ReceiptReport(Exporter exporter) { this.exporter = exporter; }
    public String render() { return exporter.format() + ":receipt"; }
}''','The report keeps one collaborator reference; the exporter’s work determines operation cost. Dependency injection does not make an expensive exporter cheaper or add fault tolerance around it.',
['Do not inject a global context to retrieve required business dependencies.','Avoid constructor cycles rather than hiding them with lookup.','Use direct construction when a test does not need the container.'],['spring/qualifiers','spring/testing-boundaries','java/clock-injection'])
put('qualifiers','Spring qualifiers: select a collaborator when types are ambiguous',
'A qualifier narrows the candidates for a dependency when more than one bean implements the requested type.',
[('Multiple exporters need a policy',[
'The kit registers csv and archive exporters. An unqualified request for Exporter is ambiguous, and the test expects NoUniqueBeanDefinitionException. The report factory uses the archive qualifier, so the selection is explicit even if registration order changes.',
'The qualifier expresses wiring intent. It does not assign an application priority to arbitrary providers or prove that an exporter supports a requested format. A runtime format decision should use a capability registry with rejected unknown values rather than silently selecting the first bean.'
]),('Factory parameters keep wiring visible',[
'QualifiedExportConfig uses proxyBeanMethods=false and obtains the selected exporter as a factory parameter. Calling another @Bean method directly in this mode is an ordinary method call and can create an unmanaged second object.',
'The archive report test checks behavior, while a separate assertion checks that type-only lookup remains ambiguous. Those are different facts. Testing only the final string could conceal a future factory change that happens to emit the same value.'
])],source('QualifiedExportConfig'),'Candidate resolution happens during wiring in this fixture. Rendering does not repeatedly search the context. A qualifier should not become a substitute for defining runtime dispatch cost and error handling.',
['Do not depend on registration order to break ambiguity.','A qualifier is not a format-validation contract.','Do not call @Bean factories as if proxyBeanMethods=false still intercepted the call.'],['spring/constructor-injection','spring/auto-configuration','java/service-discovery'])
put('bean-scopes','Spring bean scopes: singleton identity is not thread safety',
'A bean scope determines the ownership and reuse of instances created from a bean definition.',
[('Count instances at the ownership boundary',[
'The report is a singleton in its context. ImportBuffer is prototype-scoped, and two provider resolutions return different instances. The test checks identity rather than comparing equal capacity values; equal values do not establish shared ownership.',
'A prototype injected once into a singleton remains that one injected reference. It does not turn into a new buffer on every method call. Use [[spring/object-provider|an explicit provider]] when a service genuinely requires a new instance per operation.'
]),('Shared mutable state needs its own rule',[
'ReceiptStore is a singleton service. Its synchronized methods protect the map and identifier increment together, and page() returns an immutable snapshot. Removing the lock because Spring owns the service would create races in ordinary Java state.',
'Request and session scopes require a web-aware owner. Prototype objects with expensive resources need client cleanup; they do not inherit singleton destruction semantics. Before selecting a scope, decide who owns the resource and who can prove that ownership ended.'
])],'''context.registerBean(ImportBuffer.class, ImportBuffer::new,
    definition -> definition.setScope(BeanDefinition.SCOPE_PROTOTYPE));
ObjectProvider<ImportBuffer> buffers = context.getBeanProvider(ImportBuffer.class);
boolean different = buffers.getObject() != buffers.getObject();''','Singleton reuse can reduce allocations while increasing contention on shared state. Prototype allocation grows with resolutions and may retain external resources until the caller releases them. The kit’s buffer contains no native resource.',
['A singleton is not an automatic concurrency guarantee.','Prototype injection into a singleton occurs at injection time.','Do not assume prototype destruction is managed like singleton destruction.'],['spring/object-provider','spring/lifecycle-cleanup','java/threads'])
put('object-provider','Spring ObjectProvider: deferred resolution without hiding ownership',
'ObjectProvider resolves a dependency on demand from the container rather than fixing the resolved object at the provider’s injection point.',
[('Resolve at the operation boundary',[
'The kit’s provider resolves prototype ImportBuffer objects twice and verifies separate identity. That is useful when a report operation owns a fresh mutable workspace. It is unnecessary when a stateless collaborator can safely be injected once.',
'Deferred resolution changes when a lookup can fail. A missing or ambiguous bean can surface during a request instead of startup, so errors need an intentional boundary. Optional configuration should not make a required business dependency disappear silently.'
]),('Laziness is narrower than safety',[
'A provider can be queried by a long-lived service, but the resolved object still follows its own scope and lifecycle. Resolving a new buffer does not arrange cleanup for a prototype channel or make that channel safe to share between tasks.',
'[[java/optional-evaluation|Lazy suppliers]] have a related timing distinction at the Java level. Avoid computing expensive fallback state before supplying it, and avoid using delayed lookup merely to bypass an unresolved constructor cycle.'
])],'''ObjectProvider<ImportBuffer> provider = context.getBeanProvider(ImportBuffer.class);
ImportBuffer first = provider.getObject();
ImportBuffer second = provider.getObject();
System.out.println(first != second);''','Every prototype resolution allocates a new object. The fixture compares only two small buffers; no throughput or pooling claim follows from that result.',
['Do not hide a mandatory dependency as optional.','Resolution does not transfer cleanup to the container for a prototype.','Deferred lookup does not repair a dependency cycle.'],['spring/bean-scopes','java/optional-evaluation','java/generics'])
put('lifecycle-cleanup','Spring lifecycle cleanup: close container-owned resources',
'A destruction callback releases resources owned by a bean when the container ends that bean’s managed lifecycle.',
[('The owner must be able to stop',[
'ClosingChannel implements DisposableBean and records destruction. CoreBoundaryTest first observes an open channel, closes the context, and then observes the closed state. The test proves that callback delivery for this singleton; it does not demonstrate flushing a remote transport.',
'Objects that start threads should also define termination and interruption behavior. A callback that returns before its workers finish can leave writes in flight after the application claims to have stopped. Resource ownership includes the work using the resource.'
]),('Initialization can fail halfway',[
'A resource-acquiring constructor or initialization callback can throw after opening something. The partially created object may never become a normal managed bean. Release any resource already acquired when that failure path occurs.',
'[[java/try-with-resources|Java resource scopes]] remain useful inside a bean operation. Container lifetime is usually much longer than a file read or transaction, so do not keep short-lived descriptors open merely because the service is a singleton.'
])],'''public static class ClosingChannel implements DisposableBean {
    public boolean closed;
    public void destroy() { closed = true; }
}''','Closing should have a bounded wait or an explicit failure policy. This boolean fixture only verifies lifecycle delivery; graceful draining, failed flushes and forced process termination require their own tests.',
['Close contexts created by tests.','Do not assume prototype cleanup matches singleton cleanup.','Handle partial initialization failures.'],['spring/bean-scopes','spring/actuator-health','java/try-with-resources'])
put('application-events','Spring application events: local delivery is not a durable queue',
'An application event delivers a notification to listeners registered in the current application context.',
[('Keep the delivery promise small',[
'ContainerContracts publishes receipt-created and its ordinary listener increments a counter before publishEvent returns. This local fixture verifies synchronous default delivery. A listener that performs slow I/O would therefore delay the publisher unless delivery is configured differently.',
'An event name does not persist work. If the JVM stops after a payment commits but before a notification completes, this local counter cannot replay the notification. A business promise of eventual delivery needs durable state and an idempotent consumer.'
]),('Transaction timing is another boundary',[
'A regular listener can run before a surrounding database transaction commits. Reading the event as proof of committed data is therefore unsafe. Transaction-bound listeners require their own phase and rollback tests; they are a separate extension not implemented by this fixture.',
'The kit uses a string payload to expose delivery timing. A real event should carry a stable identifier and only the data its consumer needs. Passing a mutable entity graph into an asynchronous listener creates ownership and persistence-lifetime problems.'
])],'''AtomicInteger messages = new AtomicInteger();
context.addApplicationListener((ApplicationListener<PayloadApplicationEvent<String>>) event -> messages.incrementAndGet());
context.publishEvent("receipt-created");
System.out.println(messages.get());''','Publisher cost includes synchronous listener work in this fixture. Async delivery adds queue capacity and cancellation costs; neither form provides broker persistence.',
['A local event is not durable messaging.','A published event is not proof that a database transaction committed.','Do not transfer mutable request state without an ownership rule.'],['spring/transactions','spring/async-boundaries','java/executor-rejection'])
put('proxy-self-invocation','Spring AOP proxies: self-invocation bypasses proxy advice',
'A Spring proxy can intercept calls entering through the proxy reference, but an ordinary call from a target object to itself does not re-enter that proxy.',
[('The reference used for the call matters',[
'The CounterTarget outer() method calls inner(). The ProxyFactory fixture counts one advised call when the caller invokes outer through the proxy. If both methods were expected to open separate transactional boundaries, that expectation would be wrong for this call path.',
'The test uses an advice counter rather than a fake database flag. It isolates proxy dispatch. Transaction rollback needs a database test as well; a method interception count alone cannot prove a transaction manager committed or rolled back anything.'
]),('Move a boundary when it belongs elsewhere',[
'Separate orchestration and the transactional collaborator when that reflects application ownership. Calling the collaborator through its injected proxy then makes the entry boundary inspectable. Do not scatter container lookups or self-injected fields simply to make annotation interception appear to work.',
'The same call-path issue matters for caching and async annotations. A final method also cannot be overridden by a class-based proxy. Choose the proxy model and inspect the actual bean supplied to callers rather than assuming every annotated Java method is intercepted.'
])],'''AtomicInteger advised = new AtomicInteger();
ProxyFactory factory = new ProxyFactory(new CounterTarget());
factory.addAdvice((MethodInterceptor) invocation -> {
    advised.incrementAndGet(); return invocation.proceed();
});
Counter proxy = (Counter) factory.getProxy();
proxy.outer();
System.out.println(advised.get());''','Advice adds dispatch and the work inside the interceptor. The one-call fixture demonstrates a boundary, not a universal proxy overhead benchmark.',
['Self-invocation is still an ordinary target call.','An annotation is not proof that the caller used a proxy.','Do not infer database behavior from interception alone.'],['spring/transaction-proxies','spring/cache-keys','java/reflection'])
put('bootstrap','Spring Boot application bootstrap: package boundaries and startup failures',
'SpringApplication starts a Boot application context and, for a servlet application, creates the configured embedded web server.',
[('Place the root class deliberately',[
'ReceiptApplication lives in in.aitrove.learning with the controller, service and configuration classes in that package. The application annotation uses that location as a default scan boundary. Moving one class outside it can leave a dependency missing even though the source compiles.',
'The kit declares the main class in the Maven Boot plugin because several standalone teaching programs also contain main methods. An ambiguous entrypoint should fail packaging visibly rather than choose an unrelated example class.'
]),('Read the first failure',[
'Configuration binding, missing collaborators or server binding can stop startup. Do not diagnose the final wrapper exception alone; find the causal failure and the component it names. The integration tests start the server on port zero and read the assigned local port, avoiding a guessed fixed port.',
'Boot supplies assembly defaults around Spring Framework. It does not replace Java’s type, thread or exception contracts. Follow [[spring/application-context|the context lesson]] before treating auto-configuration as an unexplained source of objects.'
])],source('ReceiptApplication'),'Starting the application initializes the web stack, security, validation and datasource. Startup and shutdown are integration concerns; a direct report unit test does not need that cost.',
['Keep the scan boundary intentional.','Declare the correct entrypoint when a kit contains multiple main classes.','Read causal failures before changing unrelated properties.'],['spring/auto-configuration','spring/configuration-properties','java/maven'],subject='spring-boot',proof='HttpSecurityBoundaryTest')
put('auto-configuration','Spring Boot auto-configuration: conditions and user-defined beans',
'Auto-configuration adds bean definitions when its conditions match the application’s classes, properties and existing beans.',
[('Observe both branches',[
'FallbackExportConfig supplies an exporter only when an Exporter bean is missing. ApplicationContextRunner checks the empty case and the user-supplied case in separate contexts. The second case must contain exactly one exporter, with the user implementation selected.',
'The fixture is a small conditional configuration used to expose the missing-bean rule. It is not packaged as a reusable Boot auto-configuration starter. Publishing one requires the correct registration metadata, ordering and isolated consumer tests.'
]),('Classpath changes affect assembly',[
'Adding a starter can change the available classes and consequently the assembled object graph. A successful old test with a different dependency set is not evidence that the new graph is equivalent. Inspect the selected conditions when assembly differs from the intended design.',
'The receipt application defines its SecurityFilterChain rather than relying on an unspecified default policy. [[spring/security-filter-chain|Security behavior]] is checked with actual requests, because knowing which bean exists is weaker than knowing what a request can access.'
])],source('FallbackExportConfig'),'The runner creates two small contexts rather than starting two servers. This keeps the test focused on conditional bean creation; it does not check routing, serialization or deployment behavior.',
['Test both the matching and non-matching condition.','Do not present a conditional configuration class as a complete published starter.','A new dependency can change assembly behavior.'],['spring/qualifiers','spring/context-testing','spring/security-filter-chain'],subject='spring-boot',proof='CoreBoundaryTest.fallbackBeanBacksOffWhenUserBeanExists')
put('configuration-properties','Spring Boot configuration properties: bind values and reject bad startup input',
'ConfigurationProperties binds a named property prefix to a typed object, and validation constraints can reject invalid configuration at the binding boundary.',
[('Parse into a complete configuration',[
'ImportConfiguration binds batch size and timeout under receipt.import. The record requires a batch between one and five hundred and a non-null Duration. The kit uses 32 and 5s, then tests invalid zero directly with the validator.',
'The Binder test confirms type conversion, and the validation test confirms the declared bounds. Those separate checks do not alone prove integrated startup validation; the configuration is also registered by EnableConfigurationProperties in the running application.'
]),('A value is not a secret store',[
'Configuration source precedence can override a packaged default. Store production credentials outside the source kit and avoid logging the bound object when it contains secrets. A command-line override is visible in process arguments on many systems.',
'A timeout value needs meaning at the operation that consumes it. Binding five seconds does not make every JDBC, HTTP or shutdown operation obey that budget. [[java/properties-validation|Configuration validation in Java]] explains why parsing and application-state changes should be separate steps.'
])],source('ImportConfiguration'),'Binding happens during assembly in this application. A bounded batch size caps one dimension of retained work; payload bytes and concurrent batches still need their own limits.',
['Do not confuse successful parsing with validated ranges.','Do not log secrets by dumping configuration records.','A bound timeout has no effect until an operation uses it.'],['spring/profiles-properties','java/properties-validation','java/zone-transitions'],subject='spring-boot',proof='CoreBoundaryTest.propertyBinderMapsDuration and validationRejectsOutOfRangeBatch')
put('profiles-properties','Spring Boot profiles and property precedence: test the selected environment',
'A profile selects profile-dependent configuration, while property-source precedence determines which competing value is resolved.',
[('Make the test environment explicit',[
'The kit’s environment test selects test as the active profile and adds a fixture property source first. It then checks both the active profile and the resolved receipt.mode value. That avoids depending on whichever environment happens to exist on the developer’s machine.',
'This focused test demonstrates Environment resolution. It does not load a whole application-test.properties file or prove every Boot source-precedence rule. Test those inputs through a real application startup when deployment behavior depends on them.'
]),('Do not use a profile as authorization',[
'A prod label is not a security boundary. If a debug endpoint is enabled by a property, a mistaken source override can expose it. The security policy must still reject unauthorized access regardless of which profile assembled the service.',
'Keep behavior-changing defaults visible and bounded. Use separate credentials for real deployments; the source kit’s local-reader account exists solely for reproducible loopback tests and must not be promoted into an internet-facing user store.'
])],'''StandardEnvironment environment = new StandardEnvironment();
environment.setActiveProfiles("test");
environment.getPropertySources().addFirst(new MapPropertySource("fixture", Map.of("receipt.mode", "dry-run")));
String mode = environment.getRequiredProperty("receipt.mode");''','Environment resolution is a configuration operation, not a per-row business rule. Repeatedly querying global properties inside a hot loop hides the chosen contract and complicates tests.',
['Profiles do not grant authorization.','Do not depend on an unspecified machine environment.','Do not deploy the fixture credentials.'],['spring/configuration-properties','spring/security-filter-chain','java/resource-bundles'],subject='spring-boot',proof='CoreBoundaryTest.environmentProfileAndPropertyAreExplicit')
put('rest-validation','Spring MVC request validation: reject invalid commands before mutation',
'Spring MVC can deserialize a request body and validate its declared constraints before a controller passes the command to a service.',
[('Keep the input command small',[
'CreateReceipt contains only amountMinor. Positive validation rejects zero before create() mutates the store; the store repeats its domain check so a non-HTTP caller cannot bypass the rule. Transport validation and business invariants serve different callers.',
'The successful request returns 201 with the created receipt. The zero-amount request returns a documented 400 response through ReceiptErrors. Both tests use JSON input, so they check conversion and validation rather than merely calling the Java method.'
]),('Validation is not authorization',[
'A positive amount does not establish who may create a receipt or which tenant owns it. [[spring/security-filter-chain|Request authorization]] and tenant ownership require their own rules. Never mass-bind persistence fields such as owner, approved or internal state directly from a public command.',
'The controller fixture returns an in-memory receipt. It does not implement persistence, payment processing or idempotent retries. The integrated project documents that limit instead of treating a successful JSON response as proof of durable storage.'
])],source('ReceiptController'),'Validation work grows with the command’s fields and constraints. Body-size limits belong at the HTTP/container boundary as well; rejecting a value after deserializing a huge payload does not recover the memory already used.',
['Do not trust transport validation as the only domain guard.','Do not bind ownership fields directly from untrusted JSON.','A valid command still needs authorization.'],['spring/problem-details','spring/security-filter-chain','java/records'],subject='spring-web',proof='ReceiptBoundaryTest.createsValidReceipt and rejectsZeroAmount')
put('problem-details','Spring MVC ProblemDetail: stable errors without leaking internals',
'ProblemDetail represents a structured HTTP error with a status and detail that clients can interpret without parsing an exception stack trace.',
[('Translate at the response boundary',[
'ReceiptErrors converts MissingReceipt into 404 and rejected input into 400. The client sees a specific public message for a missing receipt and a generic validation message for rejected input. Internal SQL, stack traces and credentials do not belong in either response.',
'The missing-receipt test checks application/problem+json rather than only the status. A response can carry the right status but the wrong media type or body shape, which makes the client contract harder to consume.'
]),('Do not turn every exception into success',[
'A broad handler that converts all failures into 200 hides server faults from retry and monitoring logic. Separate invalid input, authorization failures and unexpected infrastructure failures. Log server failures with an internal correlation identifier while keeping sensitive data out of public details.',
'This fixture does not define a stable machine-readable error-code taxonomy. When clients need to act on distinct domain failures, add and test that taxonomy without requiring them to inspect English sentences.'
])],source('ReceiptErrors'),'Constructing an error object is bounded work here; exception logging, serialization and repeated invalid requests can dominate a real failure path. Rate limits and observability are separate controls.',
['Never return stack traces or SQL as public detail.','Do not convert server errors into successful status codes.','Clients should not parse prose to decide business actions.'],['spring/rest-validation','spring/mockmvc-tests','java/exceptions'],subject='spring-web',proof='ReceiptBoundaryTest.missingReceiptUsesProblemDetail and rejectsZeroAmount')
put('pagination-bounds','Spring API pagination: bounded requests and immutable snapshots',
'Pagination divides a collection response into bounded portions, but the chosen offset and ordering rules determine whether repeated requests describe a consistent view.',
[('Bound the accepted request',[
'The receipt store accepts non-negative offset and limits from one to one hundred. An offset beyond the collection returns an empty page. The controller test rejects a requested size of 101 with 400, proving that the bound is enforced rather than merely suggested in documentation.',
'The source copies receipts in insertion order and slices the copy using half-open endpoints. The returned immutable list prevents a caller from clearing the service’s response container, and the service lock covers construction of that snapshot.'
]),('Database pagination has different costs',[
'This small in-memory fixture copies the whole collection for each page. It is intentionally inspectable, not suitable for an unbounded production ledger. A database implementation should use an explicit stable sort and bounded query rather than load all rows before slicing.',
'Offset pages can drift when concurrent insertions or deletions move row positions. Keyset pagination with a stable unique ordering can address a different workload, but needs its own cursor contract. The kit does not pretend to implement that cursor by renaming offset.'
])],source('ReceiptStore'),'This implementation is O(n) time and O(n) snapshot storage per page, even when the response contains at most one hundred rows. A short response does not imply a cheap query.',
['Bound offset and limit inputs.','Do not load an unbounded database table to create one page.','Do not claim snapshot consistency across separate page requests.'],['spring/jdbc-template','spring/rest-validation','java/collection-views'],subject='spring-web',proof='ReceiptBoundaryTest.emptyPageOutsideRangeIsEmpty and returnedPageCannotMutateStore')
put('cors-boundaries','Spring MVC CORS: a browser-origin policy is not authentication',
'CORS specifies which browser origins may read or send cross-origin requests under the configured browser rules; it does not identify a user.',
[('Allow the intended origin',[
'The kit permits https://reader.aitrove.in for receipt API requests and includes credentials. Its real HTTP preflight test checks that the allowed origin is echoed and that an unlisted origin is rejected. The origin is a fixture configuration, not evidence that this domain currently hosts a reader application.',
'A credentialed browser request needs a specific allowed origin policy. Broad origin patterns require an equally explicit trust decision. Do not weaken that decision merely because a development tool can send requests without browser CORS enforcement.'
]),('Filters and handlers share the request boundary',[
'The security chain enables CORS integration so preflight can be handled before an authentication challenge defeats the browser’s request. Authentication and CSRF still govern the actual protected operation.',
'A non-browser client is not prevented from making an HTTP request just because its Origin header is absent. [[spring/security-filter-chain|Authorization]] must reject the request on its own merits. CORS and bearer-token storage are separate concerns.'
])],source('ReceiptWebConfig'),'The preflight cache duration is six hundred seconds in this fixture. Browser caching reduces repeated preflights but can delay observation of a changed policy; do not interpret it as server authentication state.',
['CORS is not user authentication.','Do not infer browser behavior from a client that ignores CORS.','Keep CSRF and credential handling explicit.'],['spring/security-filter-chain','spring/rest-validation','java/http-client'],subject='spring-web',proof='HttpSecurityBoundaryTest.configuredOriginPassesCorsPreflight and unlistedOriginIsRejected')
put('jdbc-template','Spring JdbcTemplate: bound values and visible database constraints',
'JdbcTemplate executes JDBC operations and translates database failures while leaving SQL structure and transaction ownership to the application.',
[('Bind values, keep SQL fixed',[
'JdbcReceiptLedger uses placeholders for receipt identifier and amount. The SQL statement structure is fixed. Parameter binding does not sanitize an arbitrary table name or ORDER BY expression supplied as text; allowlist any structural choices separately.',
'The database schema requires a positive amount and a unique identifier. The tests insert a valid row and reject a duplicate, confirming a database invariant rather than relying only on a controller constraint. [[java/jdbc-prepared|Prepared JDBC values]] use the same underlying principle.'
]),('A helper does not choose a transaction for you',[
'The class uses TransactionTemplate for multi-step changes. Calling two ordinary update methods without that boundary can commit the first before the second fails. The helper’s exception translation is useful to callers, but it is not atomicity.',
'The fixture uses DriverManagerDataSource and isolated H2 databases. A production service normally needs a bounded pool, migration management and tests against the chosen database. H2 behavior cannot stand in for every lock and isolation rule in PostgreSQL or MySQL.'
])],source('JdbcReceiptLedger'),'DriverManagerDataSource opens connections rather than pooling them. The count query scans behavior determined by the database plan; the fixture does not claim constant-time counting or production connection throughput.',
['Bind values instead of concatenating input into SQL.','Place related writes inside an explicit transaction.','Do not infer production database isolation from H2 alone.'],['spring/transactions','java/jdbc-prepared','java/connection-pool'],subject='spring-data',proof='ReceiptBoundaryTest.boundInsertCommitsAndDuplicateIsRejected')
put('transactions','Spring TransactionTemplate: roll back a failed multi-row change',
'TransactionTemplate executes a callback within a transaction controlled by its transaction manager, allowing the application to mark the transaction for rollback.',
[('Check state after the failure',[
'The failing batch inserts a valid receipt and then violates the positive-amount constraint. The test catches the translated database failure and checks that the table remains empty. Counting rows after the transaction ends is stronger evidence than checking that an exception was thrown.',
'A second path marks rollback-only without throwing. It also leaves the table empty. The callback’s apparent success is therefore not a promise of commit when transaction state explicitly requests rollback.'
]),('Local atomicity has a boundary',[
'A JDBC transaction can group changes on the managed connection. It cannot un-send an email or retract an HTTP request already accepted by another system. Coordinate external side effects with durable state and idempotent processing rather than calling them an automatic database rollback.',
'The H2 fixture is local and uses one datasource transaction manager. Cross-database changes, distributed recovery and production isolation behavior remain separate lessons. The source demonstrates a small atomicity contract, not a distributed transaction service.'
])],'''public void batchThatFails() {
    transactions.executeWithoutResult(status -> { add(1, 40); add(2, -7); });
}
public void rollbackOnly() {
    transactions.executeWithoutResult(status -> { add(3, 60); status.setRollbackOnly(); });
}''','A transaction retains connection and database state until completion. Long callbacks consume pool capacity and can extend lock lifetimes; do not perform slow remote work inside them without an explicit reason and bounded budget.',
['Check persisted state after rollback.','Do not treat an external HTTP operation as rollback-capable JDBC work.','Keep transaction callbacks short and bounded.'],['spring/transaction-proxies','spring/jdbc-template','java/database-isolation'],subject='spring-data',proof='ReceiptBoundaryTest.databaseFailureRollsBackWholeBatch and rollbackOnlyDoesNotCommit')
put('transaction-proxies','Spring transactional methods: call paths and rollback assumptions',
'Declarative Spring transaction advice applies at an intercepted method boundary; adding a transaction annotation does not make every target-to-target call enter that boundary.',
[('Inspect the actual call path',[
'CounterTarget.outer calls inner directly, and the advice counter records only outer entering the proxy. This is the dispatch trap behind many self-invoked transactional methods. An annotation on inner is not evidence that the call went through transaction advice.',
'The kit deliberately pairs that proxy check with separate TransactionTemplate database rollback tests. It does not pretend that the counter fixture is an annotated service with a real transaction manager. Keeping the evidence separate prevents an interception demo from becoming a false database guarantee.'
]),('State the failure policy',[
'Declarative rollback rules can distinguish unchecked and checked exceptions, and a swallowed exception can change what advice observes. Specify the intended rollback rule and test committed state for the failures your service actually throws.',
'If several operations must succeed together, choose one clear outer transaction owner. Starting a new transaction on another thread changes the connection and context boundary; [[spring/async-boundaries|async execution]] is not a transparent continuation of the caller’s transaction.'
])],'''Counter proxy = (Counter) factory.getProxy();
proxy.outer(); // outer is advised; inner is called directly by the target.
// The JDBC fixture tests rollback separately through TransactionTemplate.
ledger.batchThatFails();''','Proxy advice and database transactions add different costs. This lesson establishes call-path and rollback boundaries separately; annotated propagation modes such as REQUIRES_NEW require dedicated database fixtures beyond this kit.',
['Do not rely on self-invocation to start intercepted transactions.','Do not swallow a failure without deciding the transaction outcome.','Do not assume a transaction travels into an executor task.'],['spring/proxy-self-invocation','spring/transactions','java/jdbc-transactions'],subject='spring-data',proof='CoreBoundaryTest.selfInvocationBypassesProxyAdvice and ReceiptBoundaryTest.databaseFailureRollsBackWholeBatch')
put('security-filter-chain','Spring Security filter chain: authentication, CSRF and request order',
'A SecurityFilterChain applies selected security filters to an HTTP request before the request reaches the controller.',
[('Specify public and protected paths',[
'The receipt application allows anonymous health checks and requires authentication for other requests. A real GET without credentials returns 401; the same API GET with the fixture Basic credentials succeeds. Those tests prove request behavior, not merely that a SecurityFilterChain bean exists.',
'The user store and password are local learning fixtures. They are not a deployable account system. Basic credentials need TLS outside loopback, and production identity storage, rotation, authorization roles and tenant ownership must be designed separately.'
]),('Do not disable a protection to fix a test',[
'CSRF remains enabled. A POST carrying a Basic header but no token is rejected before Basic authentication completes in this fixture, returning 401. A request with an already-established test user but no CSRF token returns 403. With the established user and a valid token, the controller accepts a valid command.',
'That distinction is why tests check filter behavior instead of assuming every rejected authenticated-looking request returns the same status. Cookie or browser-managed credentials make CSRF relevant; moving to a bearer API requires a deliberate credential and browser threat model.'
])],source('ReceiptSecurity'),'Password verification can dominate authentication cost. Filter order also affects which work runs before rejection. The fixture does not measure capacity or provide production rate limiting.',
['Never deploy the fixture account as a production user store.','Do not disable CSRF merely to make POST tests pass.','CORS does not replace authentication or authorization.'],['spring/password-encoding','spring/cors-boundaries','spring/mockmvc-tests'],subject='spring-security',proof='HttpSecurityBoundaryTest')
put('password-encoding','Spring PasswordEncoder: salted verification rather than reversible storage',
'PasswordEncoder derives a stored password representation and verifies a candidate against it without recovering the original password.',
[('Compare through the encoder',[
'The fixture’s delegating encoder produces different salted encodings for the same password. The test verifies both against the original and rejects an incorrect candidate. Comparing a new encoding string to the stored string would fail because the salt changes the result.',
'The stored encoding includes the algorithm identifier used by the delegating encoder. Keep it when persisting the value so verification can select the intended algorithm. Truncating a database column can corrupt that representation.'
]),('Hashing is only one part of account security',[
'Password hashing does not establish session expiry, login throttling, recovery ownership or protection from credential stuffing. Do not present the small source-kit user store as a complete identity service.',
'[[java/secure-random-tokens|Opaque token generation]] is a different operation. Passwords are low-entropy user input that need slow verification; random bearer credentials have a different lookup and storage design. Reusing one representation everywhere hides that difference.'
])],'''var encoder = PasswordEncoderFactories.createDelegatingPasswordEncoder();
String first = encoder.encode("fixture-password");
String second = encoder.encode("fixture-password");
boolean verified = encoder.matches("fixture-password", first);
boolean rejected = !encoder.matches("incorrect", first);''','Adaptive hashing intentionally costs CPU. Choose and measure the work factor on the actual service hardware, then bound authentication admission. Faster verification is not automatically a security improvement.',
['Use matches rather than comparing newly encoded strings.','Preserve the encoding identifier and full stored value.','Do not log passwords or complete bearer credentials.'],['spring/security-filter-chain','java/secure-random-tokens','java/byte-streams'],subject='spring-security',proof='HttpSecurityBoundaryTest.passwordHashesUseSaltAndMatchOriginal')
put('mockmvc-tests','Spring MockMvc tests: HTTP behavior without claiming a real network test',
'MockMvc exercises Spring MVC request handling through servlet test objects, so a test can inspect conversion, validation, handlers and responses without opening a listening socket.',
[('Choose what the fixture includes',[
'ReceiptBoundaryTest constructs the controller directly, installs ReceiptErrors and a validator, and checks JSON requests. This standalone setup covers those supplied components. It does not discover every application bean or automatically install the full security chain.',
'The security tests use a web application context and apply Spring Security integration when checking authenticated-user CSRF behavior. Omitting that integration would let a controller test pass while proving nothing about the real protected route.'
]),('Assert the observable contract',[
'The positive amount test checks 201 and amountMinor in the JSON response. The missing identifier checks 404 and the ProblemDetail media type. Rejection tests use invalid inputs and check the resulting status, rather than mirroring private method names.',
'The kit also uses a real random-port HTTP server for public health, anonymous access and CORS. A mock request cannot establish actual socket binding or every container behavior. Pick the smallest boundary that supplies evidence for the claim.'
])],'''var validator = new LocalValidatorFactoryBean();
validator.afterPropertiesSet();
MockMvc mvc = MockMvcBuilders.standaloneSetup(new ReceiptController(new ReceiptStore()))
    .setControllerAdvice(new ReceiptErrors()).setValidator(validator).build();''','Standalone MVC tests avoid server startup but still initialize request handling. More complete context tests cost more assembly time and catch different problems; neither should replace all direct Java tests.',
['Do not call a standalone MVC test a full security test.','Check response shape as well as status.','Use a real server when socket and container behavior are part of the claim.'],['spring/testing-boundaries','spring/security-filter-chain','java/junit-tests'],subject='spring-testing',proof='ReceiptBoundaryTest and HttpSecurityBoundaryTest')
put('testing-boundaries','Spring tests: separate business rules, wiring and transport',
'A test boundary selects which components are real and which are supplied fixtures, determining the failures that test can detect.',
[('Three tests answer three questions',[
'The direct report test asks whether a supplied exporter produces the expected report. The context test asks whether the container can create and reuse the report bean. The MVC test asks whether a JSON request is converted, validated and translated into the promised response.',
'Starting the whole Boot application for every test adds unrelated failure modes to a small assertion. Testing everything through direct method calls misses wiring, request filters and serialization. Use both where each supplies distinct evidence.'
]),('Name the excluded behavior',[
'H2 rollback tests establish local transaction behavior for the fixture schema. They do not check a production database’s lock timing, migrations or multi-instance recovery. A deterministic cache test does not establish distributed invalidation.',
'The source kit makes those limits visible. A failing test should identify a contract the service actually promises; avoid tests that simply assert every private field has the value used to initialize it.'
])],'''assertEquals("csv:receipt", new ContainerContracts.ReceiptReport(new ContainerContracts.CsvExporter()).render());
// Container identity, MVC conversion and real HTTP filters have separate tests.
assertThrows(DataIntegrityViolationException.class, ledger::batchThatFails);
assertEquals(0, ledger.count());''','Test cost grows with the boundary’s assembly and external resources. Keep focused tests fast enough to run repeatedly, and retain integration tests for contracts that focused fixtures cannot establish.',
['Do not treat H2 as proof of production database isolation.','Do not start a server to test an ordinary pure method.','Do not omit filters from a test described as security coverage.'],['spring/context-testing','spring/mockmvc-tests','java/test-boundaries'],subject='spring-testing',proof='CoreBoundaryTest and ReceiptBoundaryTest')
put('context-testing','Spring ApplicationContextRunner: check conditional assembly in isolation',
'ApplicationContextRunner creates a small configurable application context for a test and closes it after the test callback.',
[('Test the branch that backs off',[
'The fallback exporter configuration is valid only when a user exporter is missing. One runner starts with no user bean and expects fallback; the other registers custom and expects exactly one exporter with that behavior.',
'The second test is essential. A fallback that also registers beside custom would pass the empty-case test while breaking real applications with type ambiguity. The assertion checks the candidate count and the selected behavior.'
]),('Context tests are not request tests',[
'No web server starts in this fixture. The result establishes conditional assembly, not routing or security. A class present on the test classpath can also change conditions, so keep the dependency set consistent with the consumer being tested.',
'When publishing a custom starter, add tests for registration metadata and ordering as well. This lesson checks the small condition used in the kit; it does not claim the kit is a published starter.'
])],'''new ApplicationContextRunner().withBean("custom", ContainerContracts.Exporter.class, () -> () -> "custom")
    .withUserConfiguration(FallbackExportConfig.class)
    .run(context -> {
        assertEquals(1, context.getBeansOfType(ContainerContracts.Exporter.class).size());
        assertEquals("custom", context.getBean(ContainerContracts.Exporter.class).format());
    });''','The runner initializes only the selected configuration and supplied beans. This reduces unrelated assembly work while deliberately excluding full-application behavior.',
['Test the user-bean branch as well as the empty branch.','Do not infer HTTP behavior from a non-web context.','A test classpath can affect conditional assembly.'],['spring/auto-configuration','spring/qualifiers','spring/testing-boundaries'],subject='spring-testing',proof='CoreBoundaryTest.fallbackBeanBacksOffWhenUserBeanExists')
put('actuator-health','Spring Boot Actuator health: public liveness without public diagnostics',
'Actuator exposes application operational endpoints, and its health response must be paired with an intentional exposure and authorization policy.',
[('Expose only the intended endpoints',[
'The kit exposes health and info and allows anonymous access only to the health path. Its real HTTP test checks an UP response without component details. That is a narrow monitoring contract, not blanket permission to inspect configuration, beans or environment values.',
'A service being alive is different from being ready to accept a particular workload. Database reachability can influence health while the service still has a depleted pool or overloaded worker queue. Define readiness according to the admission rule used by the deployment.'
]),('Shutdown needs a bounded drain',[
'The packaged properties request graceful server shutdown and a ten-second lifecycle phase timeout. The test context is closed after HTTP checks so its server, pool and beans do not leak into later tests.',
'This test verifies endpoint access and context closure; it does not simulate an orchestrator, a long-running request or a killed process. Production drain behavior needs a deployment-level test that stops admission and observes outstanding work.'
])],(ROOT/'work/spring-kit/src/main/resources/application.properties').read_text(),'Health checks can call contributors whose cost depends on dependencies. Avoid exposing detailed diagnostic data publicly, and avoid treating an expensive health query as a free request path.',
['Do not expose every management endpoint publicly.','Liveness and workload readiness are different contracts.','Graceful shutdown properties are not proof of deployment drain behavior.'],['spring/security-filter-chain','spring/lifecycle-cleanup','java/executor-rejection'],subject='spring-production',lang='properties',proof='HttpSecurityBoundaryTest.publicHealthIsAvailableWithoutCredentials')
put('async-boundaries','Spring task executors: capacity, rejection and lost context',
'A task executor moves work to worker threads, which changes admission, context ownership and failure reporting compared with a direct method call.',
[('Bound pending work',[
'AsyncReceiptWork configures one worker and one queue slot. It blocks the first task with a latch, queues the second and expects rejection of the third. The complete program proves that saturation is visible instead of claiming that asynchronous work is unlimited.',
'Queue capacity counts tasks, not bytes. A closure can retain a large request payload even if only one task waits. Bound input size and decide whether rejection becomes a retriable response, a durable enqueue failure or another documented outcome.'
]),('A new thread changes the boundary',[
'The caller’s transaction and thread-local state do not automatically become the worker’s context. Pass immutable input and explicit identifiers when that makes ownership easier to inspect. [[java/thread-local-cleanup|Thread-local cleanup]] matters when workers are reused.',
'Async annotation interception has the same proxy-entry issue as other advice. Calling an annotated method from the same target is not a reliable way to move work to another thread. The kit uses an executor directly so the tested scheduling boundary is visible.'
])],source('AsyncReceiptWork'),'The fixture caps active workers and queued task count. It checks admission and termination, not latency, durability or throughput under a real workload.',
['Do not hide rejected work as successful submission.','Do not assume a JDBC transaction moves to a worker.','Bound retained payload bytes as well as task count.'],['java/executor-rejection','java/thread-local-cleanup','spring/proxy-self-invocation'],subject='spring-production',proof='AsyncReceiptWork main program')
put('cache-keys','Spring cache keys: separate tenants and test the loader count',
'A cache key identifies a stored result, so omitting an input that changes the result can return another caller’s data.',
[('Include the ownership dimension',[
'The lookup receives tenant and receipt identifier. Its cache key contains both, so tenant-a receipt seven and tenant-b receipt seven occupy different entries. The test calls tenant-a twice and tenant-b once, then checks that the target loader ran exactly twice.',
'The public responses alone would not prove caching: a loader could produce the same strings every time. Counting actual target calls supplies the missing evidence without timing guesses or sleep-based assertions.'
]),('Local caching does not solve invalidation',[
'ConcurrentMapCacheManager is local to this context and does not define expiry, capacity or cross-instance consistency. A growing set of identifiers can grow memory without a bound. A production cache needs a retention rule and a stale-data policy.',
'Cached values should not be mutable entity graphs that callers can change behind the cache’s back. This fixture caches immutable strings. Proxy self-invocation can also bypass cache advice, so inspect the call path rather than relying on the annotation text.'
])],source('ReceiptCacheBoundary'),'The example’s map retains one entry per distinct tenant-and-identifier pair. No eviction is configured. This makes correctness visible but does not supply a production memory budget.',
['Do not omit tenant or other result-changing inputs from the key.','Do not treat a local cache as distributed invalidation.','Set retention and stale-data rules before production use.'],['spring/proxy-self-invocation','java/concurrent-map','java/immutable-collections'],subject='spring-production',proof='CoreBoundaryTest.cacheSeparatesTenantsAndAvoidsRepeatedLoader')
put('boundary-exercises','Spring exercises: repair validation, ownership and rollback failures',
'A boundary exercise changes one application contract and uses an observable failing assertion to determine whether the repair is correct.',
[('Start from a failing contract',[
'Run the source kit unchanged first. Then remove Positive from CreateReceipt while leaving the service guard: the MVC input path still rejects the zero amount, but the failure moves to the service. Remove the service guard too and observe why the direct-call contract needs its own test.',
'For the database exercise, move the first insert outside TransactionTemplate and let the second fail. The expected zero-row assertion should fail because the first write committed independently. Repair the transaction ownership; do not merely change the expected count.'
]),('Use separate checks for separate failures',[
'Remove tenant from the cache key and rerun the tenant test. It should expose wrong result ownership. Remove a qualifier from report wiring and inspect the ambiguity failure. Both are correctness problems that can produce plausible successful-looking output in an insufficient test.',
'The answer is the original checked boundary, not a memorized string. Keep each deliberate mutation in a local copy and revert it before packaging the kit. This exercise does not submit code to a server or grade arbitrary programs.'
])],'''assertThrows(DataIntegrityViolationException.class, ledger::batchThatFails);
assertEquals(0, ledger.count());
// Repair the transaction boundary if a deliberate mutation leaves one committed row.
assertEquals("tenant-b:7", lookup.read("tenant-b", 7));''','These exercises reuse bounded fixtures. They are local self-checks, not a hosted judge, and do not exhaustively test every database or concurrency interleaving.',
['Do not change an expected result to conceal a broken contract.','Keep transport and domain validation checks separate.','Revert deliberate mutations before distributing source.'],['spring/transactions','spring/cache-keys','spring/qualifiers'],subject='spring-exercises',proof='ReceiptBoundaryTest and CoreBoundaryTest')
put('receipt-api-project','Spring Boot receipt API project: build, test and inspect the limits',
'The receipt API project assembles a Boot web application with validated commands, protected endpoints and a separate JDBC transaction fixture.',
[('Build the supplied application',[
'The kit includes its Maven build, source files, properties and tests. Run mvn test and mvn package with JDK 21, then start the executable jar locally. ReceiptApplication is the selected entrypoint; the standalone teaching programs are separate runnable classes.',
'The API uses ReceiptStore, an in-memory synchronized map that loses receipts when the process stops. JdbcReceiptLedger is a separate transaction lesson and is not silently wired as durable API storage. Replacing the repository needs a migration, repository integration tests and explicit transaction ownership.'
]),('Inspect the actual promises',[
'GET health is public. Other requests need the fixture identity, and mutation also needs CSRF protection. The tests check valid and invalid commands, missing receipts, bounded pages, CORS and rollback. None of this implements real payment settlement, tenant accounts or a production identity provider.',
'The next extension is durable repository ownership and an idempotency contract for retries. A retry after a lost response can otherwise create another receipt. Do not call this learning project production-ready before persistence, identity, request limits and operational recovery have been tested.'
])],source('ReceiptApplication'),'The application starts a servlet server and H2 datasource, while API state remains in the in-memory store. Its source and tests expose those boundaries rather than implying a distributed service or a deployed backend.',
['Do not deploy the fixture account or database configuration.','Do not confuse the JDBC lesson with API persistence.','A successful POST does not define an idempotency policy.'],['spring/rest-validation','spring/transactions','spring/security-filter-chain','java/http-failure-project'],subject='spring-projects',proof='All source-kit Maven tests')
# Hubs and section data remain entirely separate from Java modules.
tabs=[{'title':title if slug!='spring-boot' else 'Boot Foundations','path':'spring/'+slug} for slug,title,summary,subject in HUBS]
for slug,title,summary,subject in HUBS:
 path='spring/'+slug; lessons=[s for s in added if lookup[s]['subject']==subject]
 body=para('Spring Framework manages application objects and infrastructure; Spring Boot supplies conditional assembly and application startup around that framework.' if slug=='spring-boot' else {'spring-core':'The Spring container assembles typed dependencies and controls managed object lifetimes.', 'spring-web':'Spring MVC handles HTTP requests through conversion, validation, controllers and response handling.', 'spring-data':'Spring data access connects SQL operations to explicit transaction ownership and database constraints.', 'spring-security':'Spring Security applies authentication, authorization and browser protections at request boundaries.', 'spring-testing':'Spring testing tools isolate object, container and HTTP contracts through selected fixtures.', 'spring-production':'Spring operational components expose health, task admission and cache behavior under explicit application policies.', 'spring-exercises':'A Spring boundary exercise checks a deliberate application mutation against an observable contract.', 'spring-quizzes':'A Spring self-check evaluates container, request and transaction contracts through explained questions.', 'spring-projects':'A Spring Boot project assembles application components into a buildable program with stated input and persistence boundaries.'}[subject])
 body+='<h2>Learning roadmap</h2>'+para('Read the contract, run the source-kit checks, and inspect a rejected input before extending the application. This subject covers Spring and Spring Boot together; Java language lessons remain in their own subject.')
 body+='<h2>Prerequisites</h2>'+para('Use [[java/classes-objects|Java object ownership]], [[java/interfaces|interfaces]], [[java/exceptions|exceptions]] and [[java/maven|Maven builds]] before the framework-specific lessons.')
 if lessons:body+='<h2>Section lessons</h2><ul>'+''.join('<li><a href="/'+s+'">'+html.escape(lookup[s]['title'])+'</a></li>' for s in lessons)+'</ul>'
 body+='<h2>Continue learning</h2>'+para(', '.join('[['+t['path']+'|'+t['title']+']]' for t in tabs if t['path']!=path)+'.')
 e=copy.deepcopy(lookup['java/java']);e.update(id=str(uuid.uuid5(uuid.NAMESPACE_URL,'https://aitrove.in/'+path)),path=path,title=title+' Tutorial' if slug=='spring-boot' else title,summary=summary,body=body,category='Backend Frameworks',subject=subject,tags=['spring','spring-boot'],sort_order=30,status='published',published_at=stamp,updated_at=stamp)
 e['data']={'subject_root':root,'section_path':path,'content_format':'html','seo_ready':True,'resource_tabs':tabs,'modules':[{'title':summary,'summary':'Inspect the contract and its failure cases.','lessons':lessons}] if lessons else [],'framework_version':'Boot 4.0.8 / Framework 7'}
 if path in lookup:entries[entries.index(lookup[path])]=e
 else:entries.append(e)
 lookup[path]=e
FILE.write_text(json.dumps(entries,ensure_ascii=False,indent=2)+'\n')
(ROOT.parent.parent/'outputs/spring-content-additions.json').write_text(json.dumps({'articles':added,'articleCount':len(added),'hubs':['spring/'+s for s,*rest in HUBS]},indent=2))
print('Spring articles:',len(added),'hubs:',len(HUBS))
