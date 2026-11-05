"""Publish original Spring lifecycle, MVC dispatch and Boot runner lessons."""

import copy
import datetime
import html
import json
import pathlib
import re
import uuid

ROOT = pathlib.Path(__file__).resolve().parents[1]
FILE = ROOT / "src/data/fixtures.json"
rows = json.loads(FILE.read_text())
by = {row["path"]: row for row in rows}
stamp = datetime.datetime.now(datetime.UTC).isoformat()
items = []


def add(section, slug, title, definition, sections, code, proof, cost, mistakes, links):
    items.append(locals().copy())


add("spring-core", "lazy-singleton-initialization",
    "Spring @Lazy singleton: failure moves from context refresh to first use",
    "A lazy singleton is created on first demand instead of during normal eager singleton initialization.",
    [
        ("Know when the constructor runs", [
            "The checked context starts with no ReportIndex instance. Its first getBean call constructs one; later requests receive that singleton. A second context adds an eager ReportService that requires ReportIndex, and the supposedly lazy index is built during refresh to satisfy that dependency. The annotation alone does not defer every dependency path.",
            "Deferring construction can shorten startup, but it can also postpone an invalid credential, missing file or broken configuration until a user request. For infrastructure needed to serve traffic, startup validation is usually more useful than hiding the failure. [[spring/boot-startup-validation|Boot configuration validation]] and [[spring/dependency-readiness|readiness]] handle different parts of that decision."
        ]),
        ("Avoid confusing identity and timing", [
            "A lazy singleton is still one container-managed instance once created; it is not a new object per call. [[spring/bean-scopes|Scopes]] explains the identity rule. If an eager consumer should hold a proxy instead of forcing the target at startup, inspect [[spring/lazy-injection-point|lazy injection at the parameter]] and test the actual call path."
        ]),
    ],
    '''@Bean @Lazy ReportIndex reportIndex() {
    constructed.incrementAndGet();
    return new ReportIndex(47);
}
@Bean EagerReportService reportService(ReportIndex index) {
    return new EagerReportService(index);
}''',
    "LifecycleAndMvcDispatchContractTest.lazySingletonWaitsOnlyUntilItIsRequestedOrNeededByEagerBean",
    "Construction work moves to first demand only when no eager bean forces the dependency. That demand can add latency to the first request. The test checks local instance counts; it does not measure real startup savings, request latency or readiness under load.",
    ["Do not assume @Lazy guarantees a dependency stays uncreated at context refresh.", "Do not hide a required infrastructure failure until live traffic arrives.", "Do not confuse a lazy singleton with prototype scope."],
    ["spring/lazy-injection-point", "spring/bean-scopes", "spring/boot-startup-validation", "spring/dependency-readiness"])

add("spring-core", "lazy-injection-point",
    "Spring @Lazy injection point: defer a dependency behind a proxy",
    "A lazy injection-point proxy can let an eager consumer start without constructing its lazy target until a method is invoked.",
    [
        ("Mark both sides of the boundary deliberately", [
            "The fixture marks PricingIndex as a lazy bean and the PricingService constructor parameter as lazy. Context refresh builds the service but not the target index. Calling rate through the injected interface then builds the index once and returns 47. The first version of this fixture marked only the injection parameter; because the target bean was otherwise eager, Spring had already constructed it during refresh. That failed check is the useful edge case.",
            "An interface keeps the proxy boundary straightforward. Avoid relying on proxying a final class or a method that cannot be intercepted. [[spring/lazy-singleton-initialization|Bean-level laziness]] establishes when a target itself is eligible for delayed creation; [[spring/proxy-self-invocation|service proxies]] are a separate mechanism."
        ]),
        ("First call can fail", [
            "A proxy does not make the remote dependency healthy. It moves construction and any associated error to the first method invocation. If availability matters before traffic, use a startup or readiness check that exercises the dependency intentionally, then bound first-use latency and failure handling."
        ]),
    ],
    '''@Bean @Lazy PricingIndex pricingIndex() {
    return new LoadedPricingIndex();
}
@Bean PricingService pricingService(@Lazy PricingIndex index) {
    return new PricingService(index);
}''',
    "LifecycleAndMvcDispatchContractTest.lazyInjectionProxyDelaysAnEagerServicesDependency",
    "The proxy adds one dispatch indirection and defers construction cost to first call. The local test checks exactly one construction after method invocation; it does not measure proxy overhead or prove safe behavior if first use occurs concurrently on a busy service.",
    ["Do not mark only the parameter lazy and assume an otherwise eager target is unbuilt.", "Do not use a lazy proxy to suppress required startup checks.", "Do not assume every final or inaccessible method can be proxied."],
    ["spring/lazy-singleton-initialization", "spring/bean-scopes", "spring/dependency-readiness", "spring/proxy-self-invocation"])

add("spring-core", "depends-on-init-destroy",
    "Spring @DependsOn: force initialization and reverse destruction order",
    "@DependsOn names a container-managed bean that must initialize before a dependent bean and, for singletons, outlive it during shutdown.",
    [
        ("Use it only for an indirect prerequisite", [
            "The intake stage needs a registry initialized before intake starts, but the small fixture does not inject the registry directly. @DependsOn names that prerequisite. The checked lifecycle trace is registry start, intake start, intake stop, registry stop. Spring closes the dependent first so its prerequisite still exists during cleanup.",
            "Where one object actually calls another, prefer constructor injection. It states the dependency in Java's type system and gives the application a usable collaborator. [[spring/constructor-injection|Constructor boundaries]] and [[spring/lifecycle-cleanup|cleanup ownership]] explain those simpler cases."
        ]),
        ("Ordering cannot repair broken side effects", [
            "If registry startup fails, intake does not become usable; the context should fail rather than serve half-initialized traffic. An ordered startup is not a transaction or a distributed readiness guarantee. [[spring/boot-runner-startup-failure|Runner failure]] covers another startup cut point."
        ]),
    ],
    '''@Bean(initMethod = "start", destroyMethod = "stop")
Stage registry() { return new Stage("registry"); }

@Bean(initMethod = "start", destroyMethod = "stop")
@DependsOn("registry")
Stage intake() { return new Stage("intake"); }''',
    "LifecycleAndMvcDispatchContractTest.dependsOnForcesStartupAndReverseShutdownOrder",
    "The fixture records four callbacks in one process. A real startup cost equals the work done by the stages; @DependsOn merely fixes ordering. It does not coordinate multiple replicas or guarantee cleanup after a forced process kill.",
    ["Do not use @Order on injected lists to express a bean creation dependency.", "Do not replace an actual constructor dependency with a bean-name string.", "Do not assume shutdown callbacks run after a hard kill."],
    ["spring/ordered-bean-list-injection", "spring/constructor-injection", "spring/lifecycle-cleanup", "spring/boot-runner-startup-failure"])

add("spring-web", "mvc-query-parameter-conditions",
    "Spring MVC mapping params: route a format choice before the handler runs",
    "A request-mapping params condition participates in handler selection, so an unmatched value is rejected before either controller method runs.",
    [
        ("Make formats explicit", [
            "Two export methods share one path but require format=csv or format=json. The checked MockMvc requests select the respective handler. format=xml matches neither; this fixture receives HTTP 400 from the MVC mapping layer. A client cannot assume that an unknown format silently chooses a default.",
            "The fixture returns fixed strings to isolate dispatch. A real export must use a serializer with declared response Content-Type and escaping rules. [[spring/receipt-media-types|Consumes and produces]] deals with HTTP media negotiation; a query-parameter condition is a different decision."
        ]),
        ("Do not turn a format flag into authorization", [
            "Changing the query string should not grant access to hidden data. Run identity and tenant checks on every matched handler. A third format needs its own tested response contract, size budget and content-escaping policy. [[spring/mvc-request-pipeline|The request pipeline]] shows where mapping fits."
        ]),
    ],
    '''@GetMapping(path = "/contract/receipt-export", params = "format=csv")
String csv() { return "receipt,amount\\nRC-47,4725"; }

@GetMapping(path = "/contract/receipt-export", params = "format=json")
String json() { return "{\\\"receipt\\\":\\\"RC-47\\\",\\\"amount\\\":4725}"; }''',
    "LifecycleAndMvcDispatchContractTest.queryParameterConditionsSelectOneHandlerAndRejectUnknownFormat",
    "Handler selection is small relative to serialization, database I/O and response transfer. Standalone MockMvc checks mapping for three local requests; it does not exercise production filters, authentication, large exports or actual JSON/CSV serialization.",
    ["Do not let an unsupported parameter value fall through to an unrelated handler.", "Do not confuse format=csv with a Content-Type or Accept contract.", "Do not mistake handler selection for tenant authorization."],
    ["spring/mvc-request-pipeline", "spring/receipt-media-types", "spring/tenant-receipt-authorization", "spring/mockmvc-standalone-scope"])

add("spring-web", "mvc-local-exception-precedence",
    "Spring MVC exception handlers: a controller-local handler wins before global advice",
    "Spring MVC considers a matching @ExceptionHandler on the controller before a matching handler in @RestControllerAdvice.",
    [
        ("Keep the response contract local when needed", [
            "Two controllers throw the same IllegalStateException in the fixture. One controller has a local handler that maps its known receipt conflict to 409. The other has no local handler, so global advice maps the failure to 500. The checked responses show that the shared advice does not overwrite the local contract.",
            "A bare IllegalStateException is intentionally small test input, not a recommended production error taxonomy. Define a specific conflict exception and a stable public response in a real API. [[spring/problem-details|ProblemDetail]] covers the public envelope, while [[spring/mvc-scoped-advice|scoped advice]] limits a global policy to selected controllers."
        ]),
        ("Test registration, not just annotation text", [
            "The standalone fixture registers its advice explicitly. A production web-context test must also check that component scanning installed the intended advice and that authentication filters run before the handler. Do not return internal exception messages to clients by default."
        ]),
    ],
    '''@GetMapping("/contract/local-conflict")
String read() { throw new IllegalStateException("conflict"); }

@ExceptionHandler(IllegalStateException.class)
ResponseEntity<String> local(IllegalStateException rejected) {
    return ResponseEntity.status(HttpStatus.CONFLICT).body("receipt conflict");
}''',
    "LifecycleAndMvcDispatchContractTest.controllerLocalExceptionHandlerWinsBeforeGlobalAdvice",
    "Exception mapping runs only on a failing request. This fixture checks two local outcomes, not every nested cause or ordered-advice interaction. Diagnostic logging, correlation IDs and response schemas need their own tested policy.",
    ["Do not assume a global handler always overrides a controller-local one.", "Do not expose raw exception messages as the public API shape.", "Do not treat standalone advice registration as proof of deployed component scanning."],
    ["spring/problem-details", "spring/mvc-validation-problem", "spring/mvc-scoped-advice", "spring/mockmvc-standalone-scope"])

add("spring-web", "mvc-scoped-advice",
    "Spring @RestControllerAdvice selector: apply an error policy to one controller family",
    "A controller-advice selector can constrain a global exception handler to specified controller types.",
    [
        ("One error policy need not cover every route", [
            "The checked fixture gives ScopedReceiptController a 422 response for invalid input, while a second controller using the same exception receives the fallback 500 response. assignableTypes selects the first controller family, and @Order places the scoped advice ahead of the fallback. This is a deliberate policy boundary, not a way to conceal inconsistent API designs.",
            "Advice matching is resolved around controller dispatch. A controller-local handler still takes priority for its own exception. [[spring/mvc-local-exception-precedence|Local precedence]] explains that first step; [[spring/problem-details|public error shape]] covers the next one."
        ]),
        ("Make new controllers prove their policy", [
            "A new controller outside the selector can unexpectedly fall through to a generic response. Test one selected and one unselected controller, then run a web-context test that checks actual component registration. The fixture is standalone MockMvc and explicitly installs both advice objects."
        ]),
    ],
    '''@RestControllerAdvice(assignableTypes = ScopedReceiptController.class)
@Order(10)
static class ScopedReceiptAdvice {
    @ExceptionHandler(IllegalArgumentException.class)
    ResponseEntity<String> rejected(IllegalArgumentException invalid) {
        return ResponseEntity.unprocessableEntity().body("invalid scoped receipt");
    }
}''',
    "LifecycleAndMvcDispatchContractTest.adviceSelectorOnlyHandlesItsAssignedController",
    "Advice selectors add matching work at request time; the fixture has two controllers and does not measure throughput. Broad selector policies can be hard to audit when many controllers are added, so keep the scope and fallback behavior in an integration test.",
    ["Do not assume an advice selector covers controllers introduced later.", "Do not mistake @Order for authorization or handler mapping order.", "Do not claim standalone MockMvc proves production advice scanning."],
    ["spring/mvc-local-exception-precedence", "spring/problem-details", "spring/mvc-request-pipeline", "spring/mockmvc-standalone-scope"])

add("spring-boot", "boot-runner-argument-boundary",
    "Spring Boot ApplicationRunner and CommandLineRunner: parse arguments at startup",
    "ApplicationRunner receives parsed application arguments; CommandLineRunner receives the raw String array passed to startup.",
    [
        ("Choose the argument shape you need", [
            "The fixture starts a non-web Boot context with --batch.size=47 and tenant-west. An ordered ApplicationRunner reads the batch.size option as 47. A later CommandLineRunner reads the raw second argument as tenant-west. The checked event list establishes both the argument shape and runner order for this configuration.",
            "An application runner is not a background worker. It executes in the startup path and blocks completion of SpringApplication.run. Bound critical startup work, validate its inputs and fail clearly if the service cannot operate. [[spring/boot-runner-startup-failure|The failure case]] checks what happens when a runner rejects startup."
        ]),
        ("Do not conflate order with readiness", [
            "@Order sorts these runners; it does not promise remote dependencies are healthy or that an orchestrator has withdrawn traffic. [[spring/readiness-health-group|Readiness groups]] and [[spring/boot-graceful-shutdown|shutdown behavior]] cover separate platform contracts."
        ]),
    ],
    '''@Bean @Order(10)
ApplicationRunner validateBatch() {
    return arguments -> runnerEvents.add(
        "typed:" + arguments.getOptionValues("batch.size").get(0));
}
@Bean @Order(20)
CommandLineRunner inspectRawArguments() {
    return arguments -> runnerEvents.add("raw:" + arguments[1]);
}''',
    "LifecycleAndMvcDispatchContractTest.bootRunnersReceiveTypedAndRawArgumentsInDeclaredOrder",
    "Every runner contributes directly to startup time. This local non-web context checks argument parsing and order; it does not check an HTTP listener, deployment readiness, secret handling or whether a remote service is reachable.",
    ["Do not index raw arguments without validating their count.", "Do not perform unbounded remote work in a startup runner.", "Do not treat runner order as a substitute for readiness checks."],
    ["spring/boot-runner-startup-failure", "spring/boot-command-line-precedence", "spring/boot-startup-validation", "spring/readiness-health-group"])

add("spring-boot", "boot-runner-startup-failure",
    "Spring Boot runner failure: reject startup instead of accepting unsafe settings",
    "An exception from an ApplicationRunner prevents SpringApplication.run from completing successfully.",
    [
        ("Make the rejected state visible", [
            "The checked runner throws for an unsafe batch setting. The test asserts that the Boot launch raises an exception with that cause instead of returning a healthy context to its caller. A production runner should include a bounded, actionable error and avoid printing sensitive configuration values.",
            "The application context may have already initialized other components before a runner executes. A failed run is therefore not proof that no socket ever opened or that no external side effect occurred. Keep irreversible work out of startup runners; validate configuration before starting work where possible. [[spring/boot-startup-validation|Configuration validation]] and [[spring/boot-runner-argument-boundary|runner argument parsing]] are the adjacent contracts."
        ]),
        ("Decide what must stop the process", [
            "A missing required schema or credential can justify failing startup. A transient downstream outage may be better represented by readiness DOWN while the process remains live. The choice belongs to the service's recovery design, not to a blanket catch-and-continue block."
        ]),
    ],
    '''@Bean ApplicationRunner rejectUnsafeSettings() {
    return arguments -> {
        throw new IllegalStateException("unsafe batch setting");
    };
}''',
    "LifecycleAndMvcDispatchContractTest.failingApplicationRunnerPreventsSuccessfulBootStartup",
    "The fixture tests one non-web context and its thrown cause. It does not establish how an ingress routes traffic during web-server startup, whether shutdown hooks finish external cleanup, or how a platform restarts the process after failure.",
    ["Do not swallow a required startup validation failure and report ready.", "Do not assume a failed runner means no external effect occurred earlier.", "Do not log secret values in startup exceptions."],
    ["spring/boot-runner-argument-boundary", "spring/boot-startup-validation", "spring/dependency-readiness", "spring/readiness-during-termination"])


def paragraph(value):
    escaped = html.escape(value)
    return "<p>" + re.sub(r"\[\[([^|]+)\|([^\]]+)\]\]",
        lambda match: '<a href="/' + match[1] + '">' + match[2] + "</a>", escaped) + "</p>"


titles = {path: row["title"] for path, row in by.items()}
titles.update({"spring/" + item["slug"]: item["title"] for item in items})
section_paths = {"spring-core": "spring/spring-core", "spring-web": "spring/web-apis", "spring-boot": "spring/spring-boot"}
grouped = {section: [] for section in section_paths}
for index, item in enumerate(items):
    path = "spring/" + item["slug"]
    assert path not in by, path
    assert all(target in titles for target in item["links"]), path
    body = paragraph(item["definition"])
    for heading, paragraphs in item["sections"]:
        body += "<h2>" + html.escape(heading) + "</h2>" + "".join(paragraph(text) for text in paragraphs)
    body += '<h2>Checked code</h2><pre><code class="language-java">' + html.escape(item["code"].strip(), quote=False) + "</code></pre>"
    body += "<h2>Verification boundary</h2>" + paragraph("The Maven source kit passes " + item["proof"] + " on its local Spring Boot 4 and Java 21 fixture.")
    body += "<h2>Cost and ownership</h2>" + paragraph(item["cost"])
    body += "<h3>Common Mistakes</h3><ul>" + "".join("<li>" + html.escape(text) + "</li>" for text in item["mistakes"]) + "</ul>"
    body += "<h2>Read next</h2>" + paragraph(", ".join("[[" + target + "|" + titles[target] + "]]" for target in item["links"]) + ".")
    row = copy.deepcopy(by["spring/component-scan-vs-bean"])
    row.update(id=str(uuid.uuid5(uuid.NAMESPACE_URL, "https://aitrove.in/" + path)), path=path,
        title=item["title"], summary=item["definition"], body=body, subject=item["section"],
        tags=["spring", "spring-boot", item["slug"]], sort_order=2450 + index,
        published_at=stamp, created_at=stamp, updated_at=stamp)
    row["data"] = {
        "subject_root": "spring/spring-boot", "section_path": section_paths[item["section"]],
        "kind": "tutorial", "content_format": "html", "seo_ready": True,
        "reading_minutes": max(4, round(len(re.sub(r"<[^>]+>", " ", body).split()) / 150)),
        "author_path": "authors/aitrove-editorial",
        "framework_version": "Spring Boot 4.0.8 / Spring Framework 7",
        "java_version": "21 source-kit baseline", "verification_suite": item["proof"],
        "download_path": "/downloads/aitrove-spring-source-kit.zip",
        "related": [{"path": target, "title": titles[target]} for target in item["links"]],
    }
    rows.append(row)
    by[path] = row
    grouped[item["section"]].append(path)

for section, paths in grouped.items():
    hub = by[section_paths[section]]
    hub["data"]["modules"].append({
        "title": "Startup and lifecycle decisions" if section == "spring-core" else
                 "Request dispatch and error scope" if section == "spring-web" else "Boot startup runners",
        "summary": "Check creation, routing and failure at the exact framework boundary.",
        "lessons": paths,
    })
    hub["body"] += "<h2>New checked lessons</h2><ul>" + "".join(
        '<li><a href="/' + path + '">' + html.escape(titles[path]) + "</a></li>" for path in paths) + "</ul>"
    hub["updated_at"] = stamp

reverse = {
    "spring/bean-scopes": ["spring/lazy-singleton-initialization", "spring/lazy-injection-point"],
    "spring/lifecycle-cleanup": ["spring/depends-on-init-destroy"],
    "spring/mvc-request-pipeline": ["spring/mvc-query-parameter-conditions"],
    "spring/problem-details": ["spring/mvc-local-exception-precedence", "spring/mvc-scoped-advice"],
    "spring/boot-startup-validation": ["spring/boot-runner-argument-boundary", "spring/boot-runner-startup-failure"],
    "spring/boot-command-line-precedence": ["spring/boot-runner-argument-boundary"],
}
for path, targets in reverse.items():
    row = by[path]
    row["body"] += "<h2>Checked follow-up</h2>" + paragraph("Continue with " + ", ".join(
        "[[" + target + "|" + titles[target] + "]]" for target in targets) + ".")
    row["updated_at"] = stamp

FILE.write_text(json.dumps(rows, ensure_ascii=False, indent=2) + "\n")
print("Added", len(items), "Spring tutorials; linked from", len(reverse), "existing lessons")
