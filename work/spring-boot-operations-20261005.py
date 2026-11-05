"""Add original Spring Boot operations lessons to local preview fixtures."""

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
        slug="boot-virtual-thread-admission", section="spring/spring-boot",
        title="Spring Boot virtual threads: cheaper waiting still needs admission control",
        summary="Virtual threads can reduce the cost of blocking waits, but database pools, downstream capacity and JVM lifetime remain bounded resources.",
        blocks=[
            ("The switch changes thread allocation", "With Java 21 or later, Spring Boot can use virtual threads for supported task execution when spring.threads.virtual.enabled is true. That can make a receipt API with many blocked I/O calls use fewer platform threads. It does not make JDBC connections, memory, rate limits or the payment provider infinite. Keep the admission limits that protect those resources. [[spring/bounded-executor-rejection|Bounded execution]] may need to move from a platform-thread pool to a semaphore or another explicit concurrency gate once pool-size settings no longer govern the virtual-thread executor."),
            ("Inspect the blocking path", "A virtual thread can be pinned to a carrier in some blocking situations, reducing throughput instead of improving it. Measure with representative traffic and inspect JVM pinning events rather than assuming the switch helps every workload. CPU-heavy PDF rendering gains little from cheap blocking, and a database pool with 47 connections still runs at most 47 concurrent queries on that pool. [[spring/singleton-mutable-state-race|Shared singleton state]] remains shared across virtual threads; thread count is not an isolation rule."),
            ("Keep the process alive intentionally", "Virtual threads are daemon threads. A scheduler-heavy process with no other non-daemon work can exit unless the application keeps the JVM alive; spring.main.keep-alive is the Boot setting for that case. Test a worker-only deployment after startup, after an idle period and during shutdown. Compare throughput, p95 latency, database wait time and carrier pinning with the old setup. [[spring/worker-drain-on-shutdown|Worker drain]] still needs a durable retry story when the process stops."),
        ],
        code="spring.threads.virtual.enabled=true\nspring.main.keep-alive=true",
        language="properties",
        cost="Virtual threads reduce per-wait thread overhead, but each task still retains stack state and application objects. A surge of 4,700 waiting requests can exhaust a connection pool or downstream quota even when thread creation stays cheap.",
        mistakes=["Do not remove database or remote-call concurrency limits after enabling virtual threads.", "Do not assume a virtual-thread switch speeds CPU-bound receipt rendering.", "Do not ignore pinning measurements or daemon-thread process lifetime for worker-only deployments."],
        related=["spring/bounded-executor-rejection", "spring/async-boundaries", "spring/singleton-mutable-state-race", "spring/worker-drain-on-shutdown", "spring/boot-graceful-shutdown"],
        backlink="spring/bounded-executor-rejection",
    ),
    dict(
        slug="structured-log-field-policy", section="spring/production",
        title="Spring Boot structured logs: stable fields without customer data",
        summary="A JSON log format makes events machine-readable, but field naming, correlation and data limits remain application contracts.",
        blocks=[
            ("Format is only the first decision", "Spring Boot can emit structured JSON on the console by selecting a supported format such as ecs. The result is easier for a collector to parse than a changing text pattern, but it does not decide which business fields belong in logs. Record event names, bounded outcomes and trace identifiers. Keep raw receipt contents, access tokens and customer contact details out of both message text and structured key-value pairs. [[spring/tracing-log-correlation|Trace correlation]] joins a request across services; it does not authorize payload logging."),
            ("Preserve a small schema", "Choose one service name, one environment name and stable keys for receipt action and outcome. A high-cardinality receipt ID may be acceptable in a controlled audit record, but shipping it on every debug line changes retention and access requirements. Keep the log schema versioned in the collector contract so dashboards do not break when a field is renamed. If the application supplies custom Logback or Log4j configuration, verify that it respects Boot's structured-format setting rather than assuming the property overrides a custom appender."),
            ("Test one event end to end", "Generate a successful receipt issue, a rejected request and a downstream timeout. Parse the emitted lines as JSON, assert required fields and inspect every value for secret or personal-data leakage. Check collector ingestion and search by trace ID. A logger-level change can multiply line volume without changing code; [[spring/actuator-runtime-logger-control|runtime logger control]] therefore needs a bounded incident window. [[spring/metric-cardinality|Metric labels]] should stay much narrower than searchable log fields."),
        ],
        code="spring.application.name=receipt-api\nlogging.structured.format.console=ecs\nlogging.structured.ecs.service.environment=${APP_ENV:development}",
        language="properties",
        cost="JSON encoding adds bytes and formatting work per event. Collector storage cost scales with event volume and retained fields; debug logging across thousands of requests can dominate the expense far more than the formatter itself.",
        mistakes=["Do not treat JSON formatting as permission to emit tokens or customer payloads.", "Do not rename fields without checking collector queries and dashboards.", "Do not assume custom logging configuration automatically honors the Boot format property."],
        related=["spring/tracing-log-correlation", "spring/actuator-runtime-logger-control", "spring/metric-cardinality", "spring/actuator-prometheus-scrape-contract", "spring/boot-config-source-priority"],
        backlink="spring/tracing-log-correlation",
    ),
    dict(
        slug="ssl-bundle-certificate-rotation", section="spring/production",
        title="Spring Boot SSL bundle rotation: replace certificate files with a verified handoff",
        summary="A named SSL bundle separates key material from server configuration; reload support still depends on the consumer and deployment sequence.",
        blocks=[
            ("Name the trust boundary", "A receipt API serves TLS using a named PEM bundle and points server.ssl.bundle to that name. The certificate and private key live in mounted files controlled by deployment tooling, not in a repository or tutorial example. A bundle can also describe client trust material, but server identity and outbound trust have different owners. [[spring/boot-config-source-priority|Configuration precedence]] determines which file locations reach the process, and [[spring/security-filter-chain|HTTP authorization]] remains necessary after a successful TLS handshake."),
            ("Rotate both halves safely", "For a compatible embedded server, reload-on-update can notice changed PEM files and refresh its TLS connector. The deployment must publish a matching certificate and key without leaving a partial pair visible to the watcher. Do not assume every client or third-party component that consumes an SslBundle reloads itself; confirm the particular consumer. Retain an overlap window when clients cache trust material, and keep a rollback pair available if the new certificate fails validation."),
            ("Verify the handshake, not just startup", "Start with one test certificate, connect as a client that validates the expected issuer and name, rotate the mounted pair, then make a new connection and inspect the served certificate. Existing connections may continue under the old handshake until they close; test the new connection explicitly. A file timestamp change or successful application log entry is not proof the connector accepted the new identity. Record expiry monitoring and a failed-rotation alarm before relying on unattended renewal."),
        ],
        code="spring.ssl.bundle.pem.receipt-server.keystore.certificate=file:/run/receipt-tls/tls.crt\nspring.ssl.bundle.pem.receipt-server.keystore.private-key=file:/run/receipt-tls/tls.key\nspring.ssl.bundle.pem.receipt-server.reload-on-update=true\nserver.ssl.bundle=receipt-server",
        language="properties",
        cost="A reload avoids a full process restart for compatible consumers, but file watching, controlled writes and handshake tests add deployment work. A failed pair can interrupt new TLS connections until rollback or correction.",
        mistakes=["Do not store the private key in source control or print it during troubleshooting.", "Do not assume every SSL bundle consumer supports live reload.", "Do not declare rotation successful from a changed file without testing a fresh TLS handshake."],
        related=["spring/security-filter-chain", "spring/boot-config-source-priority", "spring/actuator-management-port-boundary", "spring/readiness-health-group", "spring/boot-graceful-shutdown"],
        backlink="spring/actuator-management-port-boundary",
    ),
    dict(
        slug="application-startup-timeline", section="spring/production",
        title="Spring Boot startup timeline: measure context work before extending probes",
        summary="Buffer startup steps to find slow initialization, then fix the owning bean or external dependency before widening readiness delays.",
        blocks=[
            ("Measure the phase that is slow", "A receipt service starts slowly after a new cache client and a schema check are added. A large readiness delay hides the symptom but also delays healthy replacements. Boot's BufferingApplicationStartup records startup steps for inspection; with Actuator configured, an operations-only startup endpoint can expose the timeline. This is diagnostic data about the application internals, so place it behind the same controlled management access as other operational endpoints. [[spring/boot-startup-validation|Startup validation]] should still fail promptly for a required invalid setting."),
            ("Keep the buffer bounded", "The startup recorder retains a finite number of steps. Allocate enough capacity for one representative startup without making an unlimited in-memory log. Compare cold and warm starts and record the external systems contacted by slow bean constructors. A slow step may include network wait, class loading or a dependency chain; the timing alone does not prove the root cause. [[spring/beanpostprocessor-early-beans|Early bean creation]] and [[spring/lazy-singleton-initialization|lazy initialization]] change when work occurs, not necessarily how much work exists."),
            ("Test deployment readiness separately", "Measure from process start to listener bind and from listener bind to readiness acceptance. A context may start while a required data migration or worker lease is still unavailable. Tune the platform startup probe from observed worst-case starts with margin, and keep liveness from killing a merely slow process. [[spring/dependency-readiness|Readiness]] decides traffic admission; it cannot make a slow dependency fast. Re-run the timeline after each fix so an apparent gain is not just deferred work moved onto the first customer request."),
        ],
        code="SpringApplication receiptApp = new SpringApplication(ReceiptApi.class);\nreceiptApp.setApplicationStartup(new BufferingApplicationStartup(1536));\nreceiptApp.run(args);",
        language="java",
        cost="Buffering retains step records during startup and adds small instrumentation work. Exposing the timeline adds an operational endpoint and access-control duty; deferring initialization may lower startup time while increasing first-request latency.",
        mistakes=["Do not respond to every slow startup by extending the liveness deadline.", "Do not expose startup internals on a public management route.", "Do not call deferred initialization a performance gain without measuring the first request."],
        related=["spring/boot-startup-validation", "spring/beanpostprocessor-early-beans", "spring/lazy-singleton-initialization", "spring/dependency-readiness", "spring/actuator-management-port-boundary"],
        backlink="spring/boot-startup-validation",
    ),
]

titles = {path: row["title"] for path, row in by_path.items()}
titles.update({"spring/" + item["slug"]: item["title"] for item in lessons})
subjects = {"spring/spring-boot": "spring-boot", "spring/production": "spring-production"}
for number, item in enumerate(lessons):
    path = "spring/" + item["slug"]
    assert path not in by_path, path
    for target in item["related"]:
        assert target in titles, (path, target)
    body = "<p>" + prose(item["summary"]) + "</p>"
    for heading, content in item["blocks"]:
        body += "<h2>" + html.escape(heading) + "</h2><p>" + prose(content) + "</p>"
    body += ('<h2>Implementation contract</h2><pre><code class="language-' + item["language"] + '">'
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
        sort_order=6100 + number, published_at=stamp, created_at=stamp, updated_at=stamp,
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
    ("spring/spring-boot", "Virtual-thread admission", "Java 21+ virtual-thread execution with explicit downstream limits and process lifetime."),
    ("spring/production", "Logs, TLS rotation and startup evidence", "Structured log fields, certificate handoff and measured context startup."),
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
    entry["body"] += ('<h2>Related operations contract</h2><p><a href="/' + target + '">'
                      + html.escape(titles[target]) + "</a>.</p>")
    entry["updated_at"] = stamp

for source, target in [
    ("spring/async-boundaries", "spring/boot-virtual-thread-admission"),
    ("spring/metric-cardinality", "spring/structured-log-field-policy"),
    ("spring/readiness-health-group", "spring/ssl-bundle-certificate-rotation"),
    ("spring/lazy-singleton-initialization", "spring/application-startup-timeline"),
]:
    entry = by_path[source]
    entry["body"] += ('<h2>Related operations contract</h2><p><a href="/' + target + '">'
                      + html.escape(titles[target]) + "</a>.</p>")
    entry["updated_at"] = stamp

FIXTURE.write_text(json.dumps(rows, ensure_ascii=False, indent=2) + "\n")
print(f"Added {len(lessons)} Spring operations lessons; {len(rows)} total fixture records")
