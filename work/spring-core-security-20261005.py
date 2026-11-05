"""Add original Spring container and security lessons to local fixtures."""

import copy
import datetime
import html
import json
import pathlib
import re
import uuid

ROOT = pathlib.Path(__file__).resolve().parents[1]
FIXTURE = ROOT / "src/data/fixtures.json"
rows = json.loads(FIXTURE.read_text())
by_path = {row["path"]: row for row in rows}
stamp = datetime.datetime.now(datetime.UTC).isoformat()


def prose(value):
    escaped = html.escape(value)
    return re.sub(
        r"\[\[([^|]+)\|([^\]]+)\]",
        lambda match: '<a href="/' + match[1] + '">' + match[2] + "</a>",
        escaped,
    )


lessons = [
    dict(
        slug="beanfactorypostprocessor-definition-phase", section="spring/spring-core",
        title="Spring BeanFactoryPostProcessor: inspect definitions before instances exist",
        summary="A bean-factory post-processor works on registration metadata before ordinary application beans are created.",
        blocks=[
            ("The definition is the input", "A receipt signer must be one shared instance because it owns a limited key handle. At container startup, a BeanFactoryPostProcessor can inspect the signer definition and reject a non-singleton scope before the application serves traffic. It operates on bean definitions, not the signer object. [[spring/bean-scopes|Scope choice]] and [[spring/constructor-injection|constructor wiring]] remain the ordinary first options; use a post-processor when one policy spans registrations you do not own."),
            ("Do not instantiate during definition work", "Calling getBean inside the post-processor constructs an object before normal post-processing has finished. That object may miss proxy advice, property injection, or another extension step. The static @Bean method in the example lets the container register the post-processor without first creating its configuration object. [[spring/beanpostprocessor-early-beans|BeanPostProcessor]] works later on instances and has a different lifecycle risk."),
            ("Test failure at refresh", "Register a prototype receiptSigner in a small application context and require refresh to fail with the scope message. Repeat with the singleton definition and assert one constructed signer. A unit call to the post-processor function can test the predicate, but only a context refresh proves Spring discovered it at the intended phase. Avoid using this hook for ordinary request validation or database access."),
        ],
        code='@Configuration\nclass ReceiptDefinitionPolicy {\n    @Bean\n    static BeanFactoryPostProcessor signerScopeGuard() {\n        return factory -> {\n            BeanDefinition signer =\n                factory.getBeanDefinition("receiptSigner");\n            if (!signer.isSingleton()) {\n                throw new IllegalStateException(\n                    "receiptSigner must use singleton scope");\n            }\n        };\n    }\n}',
        cost="The policy runs during context creation, so a failure blocks startup rather than a later request. A metadata scan is cheap; calling getBean here can trigger broad, premature initialization and make startup ordering hard to reason about.",
        mistakes=["Do not call getBean from definition processing to inspect an application object.", "Do not declare a stateful non-static factory method for an early post-processor without understanding initialization order.", "Do not use container metadata hooks when a direct bean definition or constructor check expresses the rule."],
        related=["spring/bean-scopes", "spring/beanpostprocessor-early-beans", "spring/constructor-injection", "spring/component-scan-vs-bean", "spring/proxy-self-invocation"],
    ),
    dict(
        slug="beanpostprocessor-early-beans", section="spring/spring-core",
        title="Spring BeanPostProcessor: instance callbacks and the early-bean trap",
        summary="A bean post-processor sees created instances, but it and its direct dependencies are initialized before ordinary proxy processing is complete.",
        blocks=[
            ("Operate on instances", "A BeanPostProcessor can inspect or replace a freshly initialized connector. The receipt connector policy below runs after initialization and leaves the same object in the container. Unlike [[spring/beanfactorypostprocessor-definition-phase|definition processing]], this callback has an instance to inspect. Use it sparingly: ordinary validation belongs in a constructor or initialization method when only one class is affected."),
            ("Keep the processor's dependency graph small", "The container creates post-processors early so they can advise later beans. If a processor injects an application service, that service can also be instantiated early and miss transaction, cache or method-security proxying. Register the processor with a static @Bean method and avoid pulling runtime services into its constructor. [[spring/proxy-self-invocation|Proxy boundaries]] already require care; early initialization can remove the proxy entirely."),
            ("Check both identity and advice", "Start a context with the connector and an advised service. Verify the processor saw the connector, then call the advised service through the injected bean and assert its transaction or authorization advice still runs. A log line that says a bean was processed is not proof the rest of the application kept its proxies. If the callback wraps a bean, preserve its exposed interface and inspect identity-sensitive consumers."),
        ],
        code='@Configuration\nclass ReceiptConnectorPolicy {\n    @Bean\n    static BeanPostProcessor connectorGuard() {\n        return new BeanPostProcessor() {\n            @Override\n            public Object postProcessAfterInitialization(\n                    Object candidate, String registeredName) {\n                if (candidate instanceof ReceiptConnector connector) {\n                    connector.verifyStartupPolicy();\n                }\n                return candidate;\n            }\n        };\n    }\n}',
        cost="A processor callback can run for many bean instances, so keep its type check and validation bounded. The larger risk is startup side effects and early dependencies that lose advice, not the nanoseconds of the instanceof test.",
        mistakes=["Do not inject a broad service graph into an early BeanPostProcessor.", "Do not assume a post-processed bean kept every expected AOP proxy without a context test.", "Do not replace an object with a wrapper that drops its interface or lifecycle contract."],
        related=["spring/beanfactorypostprocessor-definition-phase", "spring/proxy-self-invocation", "spring/configuration-proxy-bean-methods", "spring/lifecycle-cleanup", "spring/factorybean-product-type"],
    ),
    dict(
        slug="factorybean-product-type", section="spring/spring-core",
        title="Spring FactoryBean: expose the product type without constructing it",
        summary="A FactoryBean creates a container product; accurate object-type and singleton declarations let Spring wire that product predictably.",
        blocks=[
            ("Two objects share one registration", "The container name receiptSigner normally resolves to the ReceiptSigner product. Prefixing the name with an ampersand retrieves its ReceiptSignerFactoryBean. This distinction matters when diagnostics inspect the factory while application code injects the signer. FactoryBean is an extension point for special construction; a normal @Bean method is easier when creation has no unusual type or lifecycle requirements. [[spring/component-scan-vs-bean|Registration choices]] should stay explicit."),
            ("Tell the container what it will receive", "getObjectType should return ReceiptSigner.class before the product is constructed. A null or incorrect type can make type-based lookup and autowiring miss the signer. isSingleton must agree with getObject: returning true while manufacturing a fresh mutable signer on each call creates a false lifecycle promise. The example holds one signer and returns it consistently. If the signer owns a socket or key handle, close it through an explicit lifecycle contract; [[spring/lifecycle-cleanup|destruction rules]] are separate from product lookup."),
            ("Verify type lookup and identity", "Refresh a context, inject ReceiptSigner by type, then request the named product twice and assert identity when the factory says singleton. Retrieve the factory by its prefixed name and assert its getObjectType. A factory-level unit test alone cannot show whether the container cached the product or selected it for injection. Watch startup cost if construction contacts a remote signing service."),
        ],
        code='final class ReceiptSignerFactoryBean\n        implements FactoryBean<ReceiptSigner> {\n    private final ReceiptSigner signer;\n\n    ReceiptSignerFactoryBean(SigningKeyHandle handle) {\n        this.signer = new ReceiptSigner(handle);\n    }\n\n    @Override public ReceiptSigner getObject() { return signer; }\n    @Override public Class<?> getObjectType() {\n        return ReceiptSigner.class;\n    }\n    @Override public boolean isSingleton() { return true; }\n}',
        cost="Accurate type prediction avoids constructing a product just to answer a lookup. A singleton signer saves repeated initialization but concentrates concurrent use and cleanup in one object; its implementation must be thread-safe.",
        mistakes=["Do not return null from getObjectType when the product type is known.", "Do not claim singleton while returning different stateful products.", "Do not confuse the FactoryBean object with the product injected under its registration name."],
        related=["spring/component-scan-vs-bean", "spring/bean-scopes", "spring/lifecycle-cleanup", "spring/beanpostprocessor-early-beans", "spring/constructor-injection"],
    ),
    dict(
        slug="smartlifecycle-phase-drain", section="spring/spring-core",
        title="Spring SmartLifecycle phases: drain work before destroying dependencies",
        summary="A SmartLifecycle component can stop accepting work, wait for in-flight operations, and signal shutdown completion at a chosen phase.",
        blocks=[
            ("Phase defines dependency order", "A receipt dispatcher uses a database pool. It should stop claiming new rows and drain its current batch before the pool closes. SmartLifecycle starts lower phases earlier and stops higher phases earlier. Give the dispatcher a phase that stops it before its data dependencies. A phase number is meaningful only relative to other lifecycle components in the same context; do not copy a number into every service without examining their order. [[spring/poller-shutdown|Poller shutdown]] covers the worker-level drain."),
            ("Always finish the stop callback", "The container's stop callback tells it that asynchronous stopping has completed. Stop accepting first, wait for a bounded drain, then call the callback even if draining reports a failure. A callback that never runs can hold shutdown until the phase timeout. During a forced process kill, neither SmartLifecycle nor a destroy method can guarantee delivery; [[spring/worker-drain-on-shutdown|durable work ownership]] must tolerate replay."),
            ("Exercise termination under load", "Start a batch with 47 receipts, request context shutdown, and assert no new claims begin while in-flight writes either finish or remain retryable. Record the time to callback and the remaining unprocessed rows. Compare this result with [[spring/boot-graceful-shutdown|HTTP graceful shutdown]]; server requests and background worker drains are different lifecycles."),
        ],
        code='final class ReceiptDispatchLifecycle implements SmartLifecycle {\n    private final ReceiptDispatcher dispatcher;\n    private final AtomicBoolean running = new AtomicBoolean();\n\n    ReceiptDispatchLifecycle(ReceiptDispatcher dispatcher) {\n        this.dispatcher = dispatcher;\n    }\n\n    @Override public void start() {\n        dispatcher.start();\n        running.set(true);\n    }\n    @Override public void stop(Runnable finished) {\n        dispatcher.stopAccepting();\n        dispatcher.drain(Duration.ofSeconds(19))\n            .whenComplete((ignored, failure) -> {\n                running.set(false);\n                finished.run();\n            });\n    }\n    @Override public void stop() { stop(() -> {}); }\n    @Override public boolean isRunning() { return running.get(); }\n    @Override public int getPhase() { return 250; }\n}',
        cost="A bounded drain holds shutdown resources for up to its deadline. Shorter limits increase replay work; longer limits delay replacement capacity. The database claim and idempotency design determine whether an interrupted batch is safe.",
        mistakes=["Do not close the database pool before the worker has stopped using it.", "Do not omit the stop callback on error or timeout.", "Do not treat a graceful stop hook as a guarantee against process termination."],
        related=["spring/poller-shutdown", "spring/worker-drain-on-shutdown", "spring/boot-graceful-shutdown", "spring/lifecycle-cleanup", "spring/scheduled-worker-multi-instance"],
    ),
    dict(
        slug="jwt-jwks-rotation-window", section="spring/security",
        title="Spring Resource Server JWT key rotation: overlap keys across token lifetime",
        summary="Publish a replacement verification key before issuing tokens with it, and retain the retiring key until old tokens and caches expire.",
        blocks=[
            ("A kid is a lookup hint", "A signed JWT carries a key identifier that helps the decoder choose a public key from the issuer's JWK set. The signature still has to verify; a kid is not proof of trust. Spring Resource Server can obtain and refresh JWK data from the configured issuer. Keep the issuer and accepted algorithm policy deliberate, and retain [[spring/jwt-issuer-audience-boundary|issuer, audience and time validation]] alongside signature checks. If the application supplies its own JwtDecoder bean, configure validators explicitly and test a token from the wrong issuer; do not assume a builder method installed those validators."),
            ("Roll in two directions", "First publish the new public key while still signing with the old private key. Wait for verifiers to fetch the new set, then begin signing new tokens. Keep the old public key until every old token can expire plus any relevant cache window. If the issuer drops it immediately, valid tokens can fail during rollout. If a compromised private key must be revoked immediately, accepting some old tokens is no longer safe; plan for an explicit user reauthentication event."),
            ("Test the outage path", "Run a verifier against a controlled JWK endpoint: accept a token signed with the old key, add the new key, accept a new token, then remove the old key after its expiry window. Test an unknown kid while the endpoint is unavailable and inspect the chosen decoder's cache behavior. Do not assume every node refreshes at the same instant. [[spring/security-authentication-vs-denial|Authentication failure mapping]] should distinguish bad credentials from a resource outage in logs without leaking key details to callers."),
        ],
        code='spring.security.oauth2.resourceserver.jwt.issuer-uri=${JWT_ISSUER}',
        code_language="properties",
        cost="JWK retrieval and cache misses add network and parse work. An overly short cache can overload the issuer; an overly long cache can delay planned rotation or emergency revocation. Measure the verifier's actual refresh behavior under load.",
        mistakes=["Do not remove the old public key as soon as new signing begins.", "Do not accept a token merely because its kid matches a published key.", "Do not assume a custom JwtDecoder carries issuer and audience validators unless you configured and tested them."],
        related=["spring/jwt-issuer-audience-boundary", "spring/jwt-resource-server", "spring/security-authentication-vs-denial", "spring/jwt-web-context-test", "spring/security-filter-chain"],
    ),
    dict(
        slug="password-hash-upgrade-on-login", section="spring/security",
        title="Spring password hash upgrade after a verified login",
        summary="Re-encode a legacy password only after a successful match, then replace the stored hash with a conditional update.",
        blocks=[
            ("Verify before migration", "A user account holds a stored password hash with an algorithm marker. DelegatingPasswordEncoder can choose the correct verifier for that marker and use a current encoder for new hashes. On a successful login, upgradeEncoding tells the application whether the stored encoding should be replaced. This is a write to credential state, not a reason to retain or log the raw password. [[spring/password-encoding|Password storage basics]] cover the format; this lesson covers rolling a live account set forward."),
            ("Protect concurrent changes", "Two successful logins can both observe the old hash. A compare-and-set update keyed by user ID and old hash lets only one write the replacement; the other can safely continue because its credential check already succeeded. A password reset racing with login must win over a stale rehash, so do not update by user ID alone. If a legacy hash lacks an algorithm marker, define an explicit migration mapping rather than silently treating an unknown format as plaintext."),
            ("Measure the rollout", "Count remaining legacy IDs and successful upgrades without emitting hashes or passwords. Exercise a successful legacy login, a failed password, a concurrent reset and a user whose hash is already current. Rehashing costs CPU and may increase login latency; cap login concurrency and tune the selected algorithm on deployment hardware. An upgrade-on-login path will never reach dormant accounts, so set a separate reset policy if the old format must be retired by a date."),
        ],
        code='public void verifyAndUpgrade(String rawPassword, Account account) {\n    String observedHash = account.passwordHash();\n    if (!passwordEncoder.matches(rawPassword, observedHash)) {\n        throw new BadCredentialsException("Invalid credentials");\n    }\n    if (passwordEncoder.upgradeEncoding(observedHash)) {\n        String replacement = passwordEncoder.encode(rawPassword);\n        accounts.updateHashIfCurrent(\n            account.id(), observedHash, replacement);\n    }\n}',
        cost="A password hash intentionally consumes CPU and memory. A login that upgrades pays one verification plus one new encoding, and the conditional database update adds a write. Rate limits and capacity planning matter during a broad migration.",
        mistakes=["Do not re-encode before confirming that the supplied password matches.", "Do not overwrite a concurrent password reset with a stale login upgrade.", "Do not log raw passwords, stored hashes or replacement hashes during migration."],
        related=["spring/password-encoding", "spring/session-principal-invalidation", "spring/security-authentication-vs-denial", "spring/method-security-proxy-boundary", "spring/security-filter-chain"],
    ),
    dict(
        slug="securitycontext-async-handoff", section="spring/security",
        title="Spring SecurityContext handoff to a bounded async executor",
        summary="Wrap a short-lived executor task with the submitting security context, then recheck authorization at the work boundary.",
        blocks=[
            ("A thread does not inherit request identity safely", "An HTTP handler submits receipt work to a thread pool. SecurityContextHolder is normally associated with the executing thread; an ordinary worker does not automatically receive the caller's Authentication. DelegatingSecurityContextAsyncTaskExecutor wraps submissions so the task sees the captured context and clears it afterward. This is useful for short-lived request work. [[spring/transaction-thread-boundary|The transaction]] is still separate, and [[spring/async-trace-context|trace context]] has its own propagation path."),
            ("Keep authorization close to the effect", "Capturing a security context does not make a queued task safe forever. The user may lose access before the task runs, or the token may expire. Pass a stable tenant and actor ID, re-evaluate any policy that must be current, and bound the queue so stale work does not pile up. For durable jobs, persist an explicit actor and command rather than a Java thread-local Authentication; [[spring/async-vs-durable-delivery|durable delivery]] has a different failure contract."),
            ("Test isolation between tasks", "Submit two tasks from different authenticated callers and assert each sees only its own tenant. After each task, submit a task without authentication and assert it does not inherit the previous caller. Run rejection and cancellation cases through [[spring/bounded-executor-rejection|the bounded executor]] to ensure no security context leaks when work never starts."),
        ],
        code='@Bean("receiptSecurityExecutor")\nAsyncTaskExecutor receiptSecurityExecutor(\n        @Qualifier("receiptExecutor") AsyncTaskExecutor pool) {\n    return new DelegatingSecurityContextAsyncTaskExecutor(pool);\n}',
        cost="Wrapping tasks adds context capture and restoration per submission. Queue delay is often the larger cost and can make a captured identity stale; keep capacity bounded and record the actor needed for audit.",
        mistakes=["Do not assume request SecurityContext automatically appears on an arbitrary pool thread.", "Do not use a captured Authentication as the only authorization check for long-delayed work.", "Do not confuse security-context propagation with transaction or trace-context propagation."],
        related=["spring/transaction-thread-boundary", "spring/async-trace-context", "spring/async-vs-durable-delivery", "spring/bounded-executor-rejection", "spring/jpa-auditing-actor-context"],
    ),
    dict(
        slug="cors-preflight-security-order", section="spring/security",
        title="Spring Security CORS preflight: evaluate origin before authentication",
        summary="An OPTIONS preflight lacks ordinary credentials; configure a bounded CORS policy in the security chain before protected requests reach authorization.",
        blocks=[
            ("Preflight is not the business request", "A browser sends OPTIONS with an Origin and requested method before some cross-origin API calls. That preflight may have no session cookie or bearer token. Rejecting it for missing authentication prevents the browser from making a later valid POST. Spring Security can process CORS before authorization when a suitable configuration source is wired. [[spring/cors-boundaries|The browser boundary]] still does not replace server-side authentication."),
            ("Name allowed callers precisely", "Accept one configured web origin, the required methods, and the exact headers used by the client. A wildcard origin with credentialed requests is a dangerous mismatch and may be rejected by browser rules. The example uses an environment-provided origin and does not permit credentials by default; a cookie-based application needs a separate, reviewed CSRF and cookie policy. [[spring/session-csrf-boundary|Session CSRF]] and bearer-token APIs should not be mixed casually."),
            ("Probe both requests", "Send an OPTIONS request with a permitted Origin, Access-Control-Request-Method POST and Access-Control-Request-Headers Authorization. Assert the response permits the browser to continue without authenticating the preflight. Then send the actual POST without a valid token and require denial; a successful preflight grants no write access. Repeat with an unapproved origin and with [[spring/security-matcher-order|multiple filter chains]], since the selected chain controls the CORS policy."),
        ],
        code='@Bean\nUrlBasedCorsConfigurationSource apiCors(\n        @Value("${app.web-origin}") String webOrigin) {\n    CorsConfiguration policy = new CorsConfiguration();\n    policy.setAllowedOrigins(List.of(webOrigin));\n    policy.setAllowedMethods(List.of("GET", "POST", "OPTIONS"));\n    policy.setAllowedHeaders(List.of("Authorization", "Content-Type"));\n    UrlBasedCorsConfigurationSource source =\n        new UrlBasedCorsConfigurationSource();\n    source.registerCorsConfiguration("/api/**", policy);\n    return source;\n}\n\n@Bean\nSecurityFilterChain apiChain(HttpSecurity http) throws Exception {\n    http.securityMatcher("/api/**")\n        .cors(Customizer.withDefaults())\n        .authorizeHttpRequests(rules ->\n            rules.anyRequest().authenticated());\n    return http.build();\n}',
        cost="Preflight adds an extra browser round trip unless cached. A narrow policy costs little server CPU, but every new origin, method or header expands the cross-origin surface and should correspond to a real client requirement.",
        mistakes=["Do not require a bearer token on the OPTIONS preflight and then call the browser broken.", "Do not treat a successful preflight as authorization for the actual request.", "Do not apply a broad origin wildcard to a credentialed browser flow."],
        related=["spring/cors-boundaries", "spring/security-filter-chain", "spring/security-matcher-order", "spring/session-csrf-boundary", "spring/mockmvc-security-filter-path"],
    ),
]

titles = {path: row["title"] for path, row in by_path.items()}
titles.update({"spring/" + item["slug"]: item["title"] for item in lessons})
subjects = {"spring/spring-core": "spring-core", "spring/security": "spring-security"}
for number, item in enumerate(lessons):
    path = "spring/" + item["slug"]
    assert path not in by_path, path
    for target in item["related"]:
        assert target in titles, (path, target)
    body = "<p>" + prose(item["summary"]) + "</p>"
    for heading, content in item["blocks"]:
        body += "<h2>" + html.escape(heading) + "</h2><p>" + prose(content) + "</p>"
    language = item.get("code_language", "java")
    body += ('<h2>Implementation contract</h2><pre><code class="language-' + language + '">'
             + html.escape(item["code"], quote=False) + "</code></pre>")
    body += "<h2>Cost and verification</h2><p>" + prose(item["cost"]) + "</p>"
    body += "<h3>Common Mistakes</h3><ul>" + "".join(
        "<li>" + prose(mistake) + "</li>" for mistake in item["mistakes"]
    ) + "</ul>"
    body += "<h2>Read next</h2><p>" + ", ".join(
        '<a href="/' + target + '">' + html.escape(titles[target]) + "</a>"
        for target in item["related"]
    ) + ".</p>"
    row = copy.deepcopy(by_path["spring/component-scan-vs-bean"])
    row.update(
        id=str(uuid.uuid5(uuid.NAMESPACE_URL, "https://aitrove.in/" + path)),
        path=path, title=item["title"], summary=item["summary"], body=body,
        subject=subjects[item["section"]],
        tags=["spring", "spring-boot", item["section"].split("/")[-1], item["slug"]],
        sort_order=5700 + number, published_at=stamp, created_at=stamp,
        updated_at=stamp,
    )
    row["data"] = {
        "subject_root": "spring/spring-boot", "section_path": item["section"],
        "kind": "tutorial", "content_format": "html", "seo_ready": True,
        "reading_minutes": max(4, round(len(re.sub(r"<[^>]+>", " ", body).split()) / 150)),
        "author_path": "authors/aitrove-editorial",
        "framework_version": "Spring Boot 4 / Spring Framework 7 / Spring Security 7 where relevant",
        "java_version": "21 or later",
        "verification_suite": "Spring API contract review; snippets require an application-specific model",
        "related": [{"path": target, "title": titles[target]} for target in item["related"]],
    }
    rows.append(row)
    by_path[path] = row

for section, heading, summary in [
    ("spring/spring-core", "Container extension and shutdown contracts",
     "Definition processing, instance callbacks, factory products and worker drain order."),
    ("spring/security", "Security maintenance and request boundaries",
     "JWT rotation, password migration, async identity and browser preflight."),
]:
    paths = ["spring/" + item["slug"] for item in lessons if item["section"] == section]
    hub = by_path[section]
    hub["data"]["modules"].append({"title": heading, "summary": summary, "lessons": paths})
    hub["body"] += "<h2>" + heading + "</h2><ul>" + "".join(
        '<li><a href="/' + path + '">' + html.escape(titles[path]) + "</a></li>"
        for path in paths
    ) + "</ul>"
    hub["updated_at"] = stamp

parent = by_path["spring/spring-boot"]
parent["body"] += "<h2>Container and security contracts</h2><ul>" + "".join(
    '<li><a href="/spring/' + item["slug"] + '">' + html.escape(item["title"]) + "</a></li>"
    for item in lessons
) + "</ul>"
parent["updated_at"] = stamp

for source, target in [
    ("spring/bean-scopes", "spring/beanfactorypostprocessor-definition-phase"),
    ("spring/proxy-self-invocation", "spring/beanpostprocessor-early-beans"),
    ("spring/component-scan-vs-bean", "spring/factorybean-product-type"),
    ("spring/poller-shutdown", "spring/smartlifecycle-phase-drain"),
    ("spring/jwt-resource-server", "spring/jwt-jwks-rotation-window"),
    ("spring/password-encoding", "spring/password-hash-upgrade-on-login"),
    ("spring/async-trace-context", "spring/securitycontext-async-handoff"),
    ("spring/cors-boundaries", "spring/cors-preflight-security-order"),
]:
    entry = by_path[source]
    entry["body"] += ('<h2>Related Spring boundary</h2><p><a href="/' + target + '">'
                      + html.escape(titles[target]) + "</a></p>")
    entry["updated_at"] = stamp

FIXTURE.write_text(json.dumps(rows, ensure_ascii=False, indent=2) + "\n")
print("Added", len(lessons), "Spring core and security lessons")
