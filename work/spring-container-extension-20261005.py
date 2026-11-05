"""Add original Spring container and auto-configuration lessons to preview fixtures."""

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
    return re.sub(
        r"\[\[([^|]+)\|([^\]]+)\]\]",
        lambda match: '<a href="/' + match[1] + '">' + match[2] + "</a>",
        html.escape(value),
    )


lessons = [
    dict(
        slug="singleton-mutable-state-race", section="spring/spring-core",
        title="Spring singleton state: one bean does not mean one request at a time",
        summary="A singleton instance is shared by concurrent callers; keep request-specific values outside its fields and publish shared state safely.",
        blocks=[
            ("Scope is an identity rule", "Spring's default singleton scope creates one bean instance per container definition. It does not serialize calls to that instance. A receipt pricer used by many HTTP requests must not keep the current tenant or a mutable calculation buffer in instance fields, because another thread can overwrite them mid-request. Constructor-injected collaborators can remain shared when they are safe for concurrent use. [[spring/bean-scopes|Bean scope]] controls instance creation; it is not a locking strategy."),
            ("Make the state contract explicit", "The example copies a startup rate table into an immutable map and keeps currency and amount as method arguments. If rates must change while the process runs, publish an immutable snapshot through an AtomicReference or use a store with an explicit update protocol. A ConcurrentHashMap prevents structural corruption but does not make a read-modify-write business operation atomic. Per-request information can live in a request-scoped object when an HTTP request truly owns its lifetime; [[spring/request-scope-proxy|request proxies]] have their own boundary."),
            ("Test interleaving, not just output", "Launch two requests for different tenants with a barrier between rate lookup and calculation. Verify neither can observe the other's tenant or amount. Run the test repeatedly under a thread pool; a single sequential test cannot expose a field race. For a hot rate reload, test that each calculation reads one complete snapshot rather than a mixture of old and new entries. [[spring/async-boundaries|Async work]] may outlive the HTTP request, so pass explicit values rather than reaching into request state later."),
        ],
        code="@Service\nfinal class ReceiptPricing {\n    private final Map<String, BigDecimal> rates;\n\n    ReceiptPricing(ReceiptRateProperties settings) {\n        this.rates = Map.copyOf(settings.rates());\n    }\n\n    BigDecimal total(String currency, BigDecimal subtotal) {\n        BigDecimal rate = Objects.requireNonNull(rates.get(currency));\n        return subtotal.multiply(rate).setScale(2, RoundingMode.HALF_UP);\n    }\n}",
        cost="An immutable snapshot adds one copy at startup and allows lock-free reads afterward. A mutable shared table may save a copy but requires a coherent update protocol and contention control under concurrent requests.",
        mistakes=["Do not store the current tenant, request ID or intermediate total in singleton fields.", "Do not assume ConcurrentHashMap makes a multi-step business update atomic.", "Do not inject a prototype once into a singleton and expect a new collaborator for every call."],
        related=["spring/bean-scopes", "spring/request-scope-proxy", "spring/constructor-injection", "spring/async-boundaries", "spring/lookup-method-prototype"],
        backlink="spring/bean-scopes",
    ),
    dict(
        slug="generic-type-autowire-selection", section="spring/spring-core",
        title="Spring generic autowiring: preserve type arguments at the injection point",
        summary="Generic type arguments can distinguish candidate beans without a string qualifier when the bean signatures retain that type information.",
        blocks=[
            ("A raw interface is ambiguous", "Two receipt encoders implement the same Encoder interface but produce different output models. Asking for Encoder without its type argument leaves the container with multiple candidates. Asking for Encoder<PdfReceipt> can select the PDF bean when its declared type retains the parameter. This is a compile-time type relationship used by container metadata, not a runtime check that the returned PDF bytes are valid. [[spring/qualifiers|Explicit qualifiers]] still help when two beans share the same generic type."),
            ("Keep factory signatures informative", "A factory method that declares Object, a raw Encoder, or an overly broad base type can hide the parameter Spring needs to select a candidate. Declare Encoder<PdfReceipt> and Encoder<CsvReceipt> on the bean methods even if the implementations are concrete classes. Generic selection also applies to lists: List<Encoder<PdfReceipt>> should contain only matching candidates. Do not make a new marker interface for every representation when the generic contract already expresses the difference."),
            ("Prove the chosen bean", "Refresh a minimal context containing both encoders and inject a coordinator that requires Encoder<PdfReceipt>. Assert the selected implementation and output type. Add a second PDF encoder and require the context to report ambiguity until a qualifier or primary policy resolves it. This catches accidental signature erasure during a refactor. [[spring/primary-and-qualifier-selection|Primary selection]] is a separate fallback and may hide the wrong candidate if used casually."),
        ],
        code="@Bean\nEncoder<PdfReceipt> signedPdfEncoder(SigningKey key) {\n    return new SignedPdfReceiptEncoder(key);\n}\n\n@Bean\nEncoder<CsvReceipt> csvReceiptEncoder() {\n    return new CsvReceiptEncoder();\n}\n\nfinal class ReceiptDownloadService {\n    ReceiptDownloadService(Encoder<PdfReceipt> pdfEncoder) {\n        this.pdfEncoder = pdfEncoder;\n    }\n    private final Encoder<PdfReceipt> pdfEncoder;\n}",
        cost="Generic matching is resolved at wiring time, so request-path overhead is effectively unchanged. The cost is maintaining accurate method signatures and context tests as new implementations are registered.",
        mistakes=["Do not erase generic type arguments from @Bean return types.", "Do not assume generics distinguish two candidates with the same parameterized type.", "Do not use @Primary to conceal an unintended duplicate registration."],
        related=["spring/qualifiers", "spring/primary-and-qualifier-selection", "spring/ordered-bean-list-injection", "spring/component-scan-vs-bean", "spring/constructor-injection"],
        backlink="spring/qualifiers",
    ),
    dict(
        slug="lookup-method-prototype", section="spring/spring-core",
        title="Spring @Lookup: obtain a fresh prototype from a singleton method",
        summary="Method injection lets a container-created singleton request a new prototype on each call, with subclassing limits that must be tested.",
        blocks=[
            ("The lifetime mismatch is real", "A singleton receipt renderer needs an isolated mutable render session for each document. Direct constructor injection of a prototype creates one session when the singleton starts, then reuses it. An @Lookup method asks the container to supply the session when rendering begins. [[spring/object-provider|ObjectProvider]] is often simpler because the dependency is explicit; use method injection when the collaborator must remain hidden behind a protected factory method."),
            ("Container creation is required", "Spring implements lookup method injection by overriding a method on a generated subclass. The host class and lookup method cannot be final. A class built by an ordinary @Bean factory method does not get this lookup override because the container did not construct the instance in the required way. Register the host as a scanned component and mark the session prototype. A lookup of a singleton target still returns the same target each time; the annotation does not change the target scope."),
            ("Test identity and cleanup", "Render two receipts and assert distinct session identities. Run parallel renders and check that temporary row buffers never cross documents. The container creates prototype instances, but it does not automatically run their destruction callbacks at the end of your method; explicitly close a session that owns a file or socket. [[spring/lifecycle-cleanup|Cleanup]] is a separate contract, and a unit test that directly calls an abstract lookup method cannot prove the runtime subclass was installed."),
        ],
        code="@Component\nabstract class ReceiptRenderCoordinator {\n    byte[] render(ReceiptDocument document) {\n        return newSession().render(document);\n    }\n\n    @Lookup\n    protected abstract ReceiptRenderSession newSession();\n}\n\n@Component\n@Scope(ConfigurableBeanFactory.SCOPE_PROTOTYPE)\nclass ReceiptRenderSession {\n    private final ByteArrayOutputStream buffer = new ByteArrayOutputStream();\n\n    byte[] render(ReceiptDocument document) {\n        document.writePdfTo(buffer);\n        return buffer.toByteArray();\n    }\n}",
        cost="Each call performs a container lookup and allocates a session. That is reasonable for document rendering, but a hot inner loop should not create a prototype per row or rely on automatic cleanup of external resources.",
        mistakes=["Do not mark the host class or lookup method final.", "Do not instantiate the host through a normal @Bean factory method and expect lookup overriding.", "Do not assume a prototype's destroy callback runs when the render method returns."],
        related=["spring/object-provider", "spring/bean-scopes", "spring/singleton-mutable-state-race", "spring/lifecycle-cleanup", "spring/component-scan-vs-bean"],
        backlink="spring/object-provider",
    ),
    dict(
        slug="application-event-listener-failure", section="spring/spring-core",
        title="Spring synchronous event listener failure: publication can fail the caller",
        summary="Default application event delivery runs listeners in the publisher's thread, so listener latency and exceptions become part of the caller's result.",
        blocks=[
            ("Publication is usually a method call", "A receipt service publishes ReceiptAccepted while saving a row. With the default multicaster, listeners run synchronously on that thread. A listener that throws can stop publication and propagate its exception to the service; if the service is still inside a transaction, that may roll back the save. An event name does not make the work asynchronous or durable. [[spring/application-events|Application events]] are local in-process communication, and [[spring/transaction-events|transaction phase listeners]] move selected work to a different commit point."),
            ("Define the failure owner", "A required invariant, such as updating a same-database receipt index, can legitimately fail the command. A best-effort notification should not decide whether the receipt is accepted. Move the latter after commit and give it a retryable durable channel if losing it matters. Configuring a multicaster ErrorHandler to swallow every listener failure can make a broken required listener invisible; assign failure handling per use case rather than globally masking exceptions."),
            ("Exercise rollback and ordering", "Register a listener that records a call, then one that throws. Publish inside a transaction and assert the command's database state matches the intended failure contract. Do not depend on an incidental listener iteration order; if order matters, declare it and test it, or call a service directly when the steps form one business operation. Measure listener duration because synchronous listeners extend request latency and hold the publisher's resources."),
        ],
        code="@Component\nfinal class ReceiptIndexListener {\n    private final ReceiptIndex receiptIndex;\n\n    ReceiptIndexListener(ReceiptIndex receiptIndex) {\n        this.receiptIndex = receiptIndex;\n    }\n\n    @EventListener\n    void on(ReceiptAccepted accepted) {\n        receiptIndex.record(accepted.receiptId());\n    }\n}",
        cost="Each synchronous listener adds its execution time to publishEvent and may hold the caller's transaction open. A slow remote call inside a listener can extend lock time and cause retries elsewhere.",
        mistakes=["Do not assume @EventListener makes delivery asynchronous or durable.", "Do not swallow every listener error when some listeners enforce required state.", "Do not call a remote service inside a transaction-scoped listener without a clear failure budget."],
        related=["spring/application-events", "spring/transaction-events", "spring/async-event-listener-failure", "spring/outbox-atomic-write", "spring/transaction-event-commit-test"],
        backlink="spring/application-events",
    ),
    dict(
        slug="async-event-listener-failure", section="spring/spring-core",
        title="Spring async event listener: handle detached failures and queue pressure",
        summary="An @Async event listener releases the publisher quickly, but its exception, executor capacity and transaction context need separate handling.",
        blocks=[
            ("The caller no longer owns completion", "An @Async @EventListener runs on an executor when async support is enabled and the listener is invoked through the Spring-managed path. A void listener's exception does not propagate to the event publisher. Configure error reporting for that executor path, and treat a rejected submission as a distinct overload condition. [[spring/application-event-listener-failure|Synchronous listeners]] have the opposite failure relationship; choose deliberately rather than adding @Async to silence a slow request."),
            ("Pass stable data", "The worker thread does not inherit the publisher's transaction. Passing a managed entity that expects an open persistence context can fail or read unexpected state. Publish IDs and immutable values, then load the required state in the worker's own transaction if needed. Even after-commit delivery remains in-memory; a crash can erase accepted work. For a receipt that must reach another system, [[spring/async-vs-durable-delivery|durable delivery]] and an outbox are the relevant boundary."),
            ("Prove error visibility", "Force the listener's target to throw and assert an observable failure record or error-handler call while the publisher's result remains as designed. Fill the executor queue and test whether the event is rejected, blocked or sent to another path. Use a fixed clock and controlled executor in tests so completion timing is deterministic. A log line from a worker is insufficient proof of delivery to a remote recipient."),
        ],
        code="@Component\nfinal class ReceiptSearchListener {\n    private final ReceiptSearchIndex searchIndex;\n\n    ReceiptSearchListener(ReceiptSearchIndex searchIndex) {\n        this.searchIndex = searchIndex;\n    }\n\n    @Async(\"receiptEventExecutor\")\n    @EventListener\n    void on(ReceiptCommitted committed) {\n        searchIndex.refresh(committed.receiptId());\n    }\n}",
        cost="The publisher saves listener latency, but each pending event consumes queue space and may become stale. A bounded executor makes overload explicit; an outbox adds storage and replay cost when completion must survive process failure.",
        mistakes=["Do not expect a void async listener exception to reach publishEvent.", "Do not pass a lazy JPA entity to a detached worker thread.", "Do not call an in-memory async listener a durable integration channel."],
        related=["spring/application-event-listener-failure", "spring/async-vs-durable-delivery", "spring/bounded-executor-rejection", "spring/transaction-thread-boundary", "spring/outbox-atomic-write"],
        backlink="spring/async-vs-durable-delivery",
    ),
    dict(
        slug="aop-final-method-boundary", section="spring/spring-core",
        title="Spring AOP final methods: advice requires an interceptable call",
        summary="Class-based proxies cannot override final or private methods, and self-calls bypass proxy advice even when the method is open.",
        blocks=[
            ("The proxy is the boundary", "A receipt reservation annotated @Transactional receives advice when another bean calls it through the Spring proxy. A direct call on this from inside the same object does not cross the proxy. With class-based proxying, a final class cannot be subclassed and a final or private method cannot be overridden for advice. Interface-based proxies have different method visibility, but they do not make private internal calls interceptable. [[spring/proxy-self-invocation|Self-invocation]] and [[spring/method-security-proxy-boundary|method security]] share this shape."),
            ("Put the boundary on a service API", "Make the advised operation a public, non-final method on a bean injected into its caller. Keep helpers private if they do not require independent advice. If the operation needs a second transaction, move it to a separate service rather than trying to manipulate proxy internals. The example gives an order service a distinct ledger collaborator; the caller crosses the proxy at reserve, so transaction advice can run. A comment on a private helper would not change execution."),
            ("Test the behavior, not the annotation", "Call the service through the application context, force a repository failure and assert the reservation rolls back. Then test a direct internal call only if the design still has one, so the test makes the difference visible. A unit test that constructs ReceiptLedger with new bypasses Spring advice and cannot prove transaction or security semantics. Proxy type may change with configuration, so prefer behavioral checks over assertions on generated class names."),
        ],
        code="@Service\nclass ReceiptLedger {\n    private final ReservationRepository reservations;\n\n    ReceiptLedger(ReservationRepository reservations) {\n        this.reservations = reservations;\n    }\n\n    @Transactional\n    public void reserve(ReceiptCommand command) {\n        reservations.insert(command.receiptId(), command.amount());\n    }\n}\n\n@Service\nclass ReceiptOrderService {\n    ReceiptOrderService(ReceiptLedger ledger) { this.ledger = ledger; }\n    private final ReceiptLedger ledger;\n    void accept(ReceiptCommand command) { ledger.reserve(command); }\n}",
        cost="A proxy adds small dispatch overhead compared with database work. The real cost of a misplaced boundary is silent loss of transaction, cache, async or authorization behavior; an integration test is cheaper than recovering corrupted state.",
        mistakes=["Do not put @Transactional on a private or final method and expect class-based advice.", "Do not call an advised method through this and expect the proxy to intercept it.", "Do not prove AOP behavior with only a new-constructed unit object."],
        related=["spring/proxy-self-invocation", "spring/method-security-proxy-boundary", "spring/transaction-events", "spring/beanpostprocessor-early-beans", "spring/context-testing"],
        backlink="spring/proxy-self-invocation",
    ),
    dict(
        slug="conditional-missing-bean-default", section="spring/spring-boot",
        title="Spring Boot ConditionalOnMissingBean: a default that yields to application code",
        summary="An auto-configuration can provide a fallback bean while letting an application supply its own implementation by type.",
        blocks=[
            ("The condition sees definitions so far", "A shared receipt starter supplies a default ReceiptGateway, but one application needs a signed gateway. @ConditionalOnMissingBean can skip the default when a compatible application bean is already registered. Put this condition in auto-configuration, which is processed after user bean definitions, rather than scattering it among ordinary application configurations whose ordering may surprise you. [[spring/auto-configuration|Auto-configuration]] selects a default; [[spring/primary-and-qualifier-selection|@Primary]] merely chooses among beans that both exist."),
            ("Publish the integration contract", "The auto-configuration class must be registered through the starter's auto-configuration imports resource. Declare a concrete return type that allows the condition to see the bean's intended API. A broad Object return type or a factory whose type cannot be predicted can produce an unexpected default. Test the starter in isolation and with a user ReceiptGateway implementation; the first case must create exactly one gateway, the second must leave the user's bean in place."),
            ("Do not hide configuration failure", "A missing required signing key is not a reason to silently instantiate an insecure fallback. Conditional creation answers whether a bean is already supplied; property validation answers whether the chosen gateway can start safely. [[spring/boot-startup-validation|Startup validation]] should fail for invalid settings. Inspect the condition outcome when a bean is unexpectedly present, and keep any override behavior explicit in release notes and context tests."),
        ],
        code="@AutoConfiguration\nclass ReceiptGatewayAutoConfiguration {\n    @Bean\n    @ConditionalOnMissingBean(ReceiptGateway.class)\n    ReceiptGateway receiptGateway(ReceiptGatewayProperties settings) {\n        return new HttpReceiptGateway(settings.endpoint());\n    }\n}",
        cost="Condition evaluation occurs at startup, with negligible request-path cost. Maintaining a starter adds a compatibility obligation: changes to the default type or condition can alter which bean applications receive during an upgrade.",
        mistakes=["Do not use a missing-bean condition in arbitrary user configuration and depend on incidental processing order.", "Do not return Object from a factory when the condition needs a predictable gateway type.", "Do not use a fallback bean to conceal invalid required credentials or endpoint settings."],
        related=["spring/auto-configuration", "spring/auto-configuration-registration", "spring/primary-and-qualifier-selection", "spring/boot-startup-validation", "spring/conditional-property-opt-in"],
        backlink="spring/auto-configuration",
    ),
    dict(
        slug="conditional-property-opt-in", section="spring/spring-boot",
        title="Spring Boot ConditionalOnProperty: make optional infrastructure opt in",
        summary="A property condition can register a feature only for an explicit value, with absence and false kept distinct from enabled.",
        blocks=[
            ("The absent value has meaning", "A receipt replay worker should not start merely because its class is on the classpath. @ConditionalOnProperty with havingValue true and matchIfMissing false requires an explicit opt-in setting. That prevents an unreviewed deployment from running a second replay loop. [[spring/scheduled-worker-multi-instance|Multi-instance scheduling]] still needs a claim or leader protocol; a property flag only controls whether a bean is registered on each instance."),
            ("Keep deployment and runtime decisions separate", "The condition is evaluated while building the context. Changing a property in an external store does not automatically add or remove the worker from an already running context. Use a controlled restart or a separately designed runtime switch with defined drain behavior. Include the flag in the same deployment review as its queue, permissions and monitoring settings. [[spring/boot-config-source-priority|Config precedence]] matters because command-line, environment and files may disagree about the final value."),
            ("Test the matrix", "Start a minimal context with the property absent, false and true. Assert that exactly the true case registers ReceiptReplayWorker. Then test a malformed value and verify the intended behavior instead of assuming arbitrary text means enabled. A context test establishes registration; a worker integration test must separately prove idempotent claims, shutdown and retry. [[spring/boot-external-config-validation|Configuration validation]] should reject a missing queue name when the feature is enabled."),
        ],
        code="@AutoConfiguration\n@ConditionalOnProperty(\n    prefix = \"receipt.replay\",\n    name = \"enabled\",\n    havingValue = \"true\",\n    matchIfMissing = false)\nclass ReceiptReplayAutoConfiguration {\n    @Bean\n    ReceiptReplayWorker receiptReplayWorker(ReceiptClaimStore claims) {\n        return new ReceiptReplayWorker(claims);\n    }\n}",
        cost="A disabled feature creates no worker or polling load. When enabled, each application instance evaluates the same setting and may start a worker, so database claim contention and polling volume still need explicit bounds.",
        mistakes=["Do not assume a conditional property is a live runtime toggle.", "Do not interpret bean registration as proof that only one cluster member will run the worker.", "Do not leave required enabled-mode settings unvalidated."],
        related=["spring/auto-configuration", "spring/conditional-missing-bean-default", "spring/boot-config-source-priority", "spring/boot-external-config-validation", "spring/scheduled-worker-multi-instance"],
        backlink="spring/boot-config-source-priority",
    ),
]

titles = {path: row["title"] for path, row in by_path.items()}
titles.update({"spring/" + item["slug"]: item["title"] for item in lessons})
subjects = {"spring/spring-core": "spring-core", "spring/spring-boot": "spring-boot"}
for number, item in enumerate(lessons):
    path = "spring/" + item["slug"]
    assert path not in by_path, path
    for target in item["related"]:
        assert target in titles, (path, target)
    body = "<p>" + prose(item["summary"]) + "</p>"
    for heading, content in item["blocks"]:
        body += "<h2>" + html.escape(heading) + "</h2><p>" + prose(content) + "</p>"
    body += ('<h2>Implementation contract</h2><pre><code class="language-java">'
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
        sort_order=6000 + number, published_at=stamp, created_at=stamp, updated_at=stamp,
    )
    row["data"] = {
        "subject_root": "spring/spring-boot", "section_path": item["section"],
        "kind": "tutorial", "content_format": "html", "seo_ready": True,
        "reading_minutes": max(4, round(len(re.sub(r"<[^>]+>", " ", body).split()) / 150)),
        "author_path": "authors/aitrove-editorial",
        "framework_version": "Spring Boot 4 / Spring Framework 7 where relevant",
        "java_version": "21 or later",
        "verification_suite": "Spring API contract review; snippets require an application-specific model",
        "related": [{"path": target, "title": titles[target]} for target in item["related"]],
    }
    rows.append(row)
    by_path[path] = row

for section, heading, summary in [
    ("spring/spring-core", "Container identity, events and proxy boundaries",
     "Concurrent singleton calls, generic injection, prototype lookup, event failures and AOP method limits."),
    ("spring/spring-boot", "Conditional auto-configuration contracts",
     "Defaults that yield to user beans and optional workers that require explicit opt-in."),
]:
    paths = ["spring/" + item["slug"] for item in lessons if item["section"] == section]
    hub = by_path[section]
    hub["data"]["modules"].append({"title": heading, "summary": summary, "lessons": paths})
    hub["body"] += "<h2>" + heading + "</h2><ul>" + "".join(
        '<li><a href="/' + path + '">' + html.escape(titles[path]) + "</a></li>"
        for path in paths
    ) + "</ul>"
    hub["updated_at"] = stamp

for item in lessons:
    source, target = item["backlink"], "spring/" + item["slug"]
    entry = by_path[source]
    entry["body"] += ('<h2>Related container contract</h2><p><a href="/' + target + '">'
                      + html.escape(titles[target]) + "</a>.</p>")
    entry["updated_at"] = stamp

for source, target in [
    ("spring/ordered-bean-list-injection", "spring/generic-type-autowire-selection"),
    ("spring/method-security-proxy-boundary", "spring/aop-final-method-boundary"),
]:
    entry = by_path[source]
    entry["body"] += ('<h2>Related container contract</h2><p><a href="/' + target + '">'
                      + html.escape(titles[target]) + "</a>.</p>")
    entry["updated_at"] = stamp

FIXTURE.write_text(json.dumps(rows, ensure_ascii=False, indent=2) + "\n")
print(f"Added {len(lessons)} Spring lessons; {len(rows)} total fixture records")
