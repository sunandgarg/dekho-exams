"""Publish original Spring upload and health-probe lessons from checked fixtures."""
from __future__ import annotations

import datetime
import html
import json
import pathlib
import re
import uuid

ROOT = pathlib.Path(__file__).resolve().parents[1]
FILE = ROOT / "src/data/fixtures.json"
rows = json.loads(FILE.read_text())
by_path = {row["path"]: row for row in rows}
stamp = datetime.datetime.now(datetime.UTC).isoformat()
specs = []


def add(subject, slug, title, opening, sections, code, proof, limits, mistakes, links):
    specs.append(dict(subject=subject, path="spring/" + slug, slug=slug,
        title=title, opening=opening, sections=sections, code=code,
        proof=proof, limits=limits, mistakes=mistakes, links=links))


add("spring-web", "multipart-receipt-import", "Spring MVC multipart receipt import: validate before storing",
"A multipart import endpoint receives a named part, checks its bytes and stores it under a server-generated path.", [
    ("The checked request boundary", ["The local controller accepts a part named file at POST /contract/imports. It rejects an empty or missing part, checks a small byte budget, decodes strict UTF-8 and requires a receipt_id,amount_minor header before writing a temporary file. A valid upload returns the generated basename. The test sends ../../outside.csv as the original filename and confirms that the stored file stays under the temporary directory with a new name.", "This is a standalone MockMvc controller, not an endpoint in ReceiptApplication. [[spring/upload-byte-budget|The byte-budget lesson]] explains the two checks. [[spring/upload-generated-filename|The path lesson]] covers why the filename is ignored. The file's declared text/csv type is not enough to accept it; the test submits HTML while claiming CSV and receives 422."]),
    ("Define an import lifecycle", ["The fixture only stages bytes. It does not parse all CSV records, insert receipts, scan for malware, choose a durable object store or clean old staged files. A real import should assign an owner, record stage state, set retention, validate each record and publish a result without holding the HTTP request open for unbounded work. [[spring/import-api-project|The project plan]] separates these steps."])
], '''@PostMapping("/contract/imports")
String receive(@RequestParam("file") MultipartFile file) throws IOException {
    if (file.isEmpty())
        throw new ResponseStatusException(HttpStatus.BAD_REQUEST);
    if (file.getSize() > MAX_BYTES)
        throw new ResponseStatusException(HttpStatus.PAYLOAD_TOO_LARGE);
    byte[] content;
    try (var input = file.getInputStream()) {
        content = input.readNBytes(MAX_BYTES + 1);
    }
    if (content.length > MAX_BYTES)
        throw new ResponseStatusException(HttpStatus.PAYLOAD_TOO_LARGE);
    // Strict UTF-8 and header checks run before this file is created.
    Path stored = Files.createTempFile(storage, "receipt-import-", ".csv");
    Files.write(stored, content);
    return stored.getFileName().toString();
}''',
"MultipartReceiptImportTest.storesValidatedBytesUnderGeneratedName and MultipartReceiptImportTest.rejectsEmptyOrMissingPart",
"The test uses MockMultipartFile and a JUnit temporary directory. It does not exercise a servlet container's multipart parser, proxy upload limits, disk exhaustion, concurrent uploads or durable retention. Holding the accepted bytes in memory is bounded to 128 bytes in this fixture; a production budget needs a different value and workload measurement.",
["Do not use the client filename as a storage path.", "Do not trust MIME text without checking bytes.", "Do not call a staged file an imported receipt batch."],
["spring/upload-byte-budget", "spring/upload-generated-filename", "spring/upload-utf8-header", "spring/import-api-project"])

add("spring-web", "upload-byte-budget", "Spring multipart size limits: enforce parser and application budgets",
"An upload byte budget limits how much request data reaches parsing and storage.", [
    ("Two different limit points", ["Spring Boot exposes multipart max-file-size and max-request-size settings for the servlet parser. Those settings are outside the standalone MockMvc fixture. The checked controller also rejects a part whose reported size exceeds 128 bytes, then reads at most 129 bytes to catch an inconsistent or changing source before storing anything. The oversized test receives 413 and leaves the directory empty.", "A parser limit can reject a request before the controller runs. The controller limit still guards the application's own allocation and keeps its contract visible in a unit-scale test. It is not a substitute for reverse-proxy and servlet limits. [[spring/multipart-receipt-import|The import entrypoint]] checks content and path boundaries after this budget. [[spring/upload-mockmvc-boundary|The test-boundary lesson]] states what MockMvc cannot prove."]),
    ("Budget the whole request", ["Multipart overhead and multiple parts can make the request larger than one file. Configure both per-file and total-request ceilings in the deployed stack, and make the proxy ceiling consistent. Limit row count and field length after CSV parsing too; small bytes can still trigger costly work if interpreted badly. Never call readAllBytes on an unbounded user upload. The fixture's 128-byte value is intentionally tiny so the test can assert the boundary."])
], '''if (file.getSize() > MAX_BYTES) throw new ResponseStatusException(HttpStatus.PAYLOAD_TOO_LARGE);
byte[] content;
try (var input = file.getInputStream()) {
    content = input.readNBytes(MAX_BYTES + 1);
}
if (content.length > MAX_BYTES) throw new ResponseStatusException(HttpStatus.PAYLOAD_TOO_LARGE);''',
"MultipartReceiptImportTest.rejectsOversizedPartBeforeStorage",
"MockMultipartFile materializes bytes before the controller sees them. The test proves controller behavior, not peak memory or container rejection. Production limits need deployment tests that include the proxy and servlet parser; 413 mapping may differ by layer.",
["Do not confuse max-file-size with max-request-size.", "Do not read an unbounded upload into a byte array.", "Do not infer proxy behavior from standalone MockMvc."],
["spring/multipart-receipt-import", "spring/upload-mockmvc-boundary", "spring/upload-utf8-header"])

add("spring-security", "upload-generated-filename", "Spring file uploads: discard the supplied filename before writing",
"A multipart original filename is caller-controlled metadata, not a safe path component.", [
    ("The test sends traversal text", ["The accepted fixture upload declares ../../outside.csv. The controller never joins that value to the storage directory. It calls Files.createTempFile within a JUnit temporary root, returns only the generated basename and verifies the bytes exist at that resolved path. The test proves one path boundary in local storage. It does not prove a mounted production volume's permissions, symlink policy or cleanup schedule.", "Ignore content type as an authority signal too. A second test labels HTML bytes text/csv; header validation rejects it before a file is created. A filename extension and a MIME declaration can both be chosen by the uploader. [[spring/upload-utf8-header|The format lesson]] describes the deliberately narrow byte check; [[spring/multipart-receipt-import|the entrypoint]] stages only accepted bytes."]),
    ("Separate public labels from storage keys", ["If users need to see their original filename, store a sanitized display label in a separate field with length and character bounds. Do not let it determine filesystem placement. Generate an opaque key for storage and keep an ownership record. On failure after creating a temporary file, delete it or mark it for cleanup; the fixture deletes its file on a write error but does not simulate disk failure."])
], '''Path stored = Files.createTempFile(storage, "receipt-import-", ".csv");
try { Files.write(stored, content); }
catch (IOException failure) {
    Files.deleteIfExists(stored);
    throw failure;
}''',
"MultipartReceiptImportTest.storesValidatedBytesUnderGeneratedName and MultipartReceiptImportTest.rejectsFakeCsvMediaTypeWhenBytesHaveWrongHeader",
"The path test runs in a temporary directory and uses a generated local file. It does not audit filesystem ACLs, symbolic links, object-store policies, malware scanning or file retention. Staging bytes costs disk space and must have a quota outside this fixture.",
["Do not join getOriginalFilename() to a storage root.", "Do not accept a file because its extension says CSV.", "Do not expose an internal absolute path as the public upload identifier."],
["spring/multipart-receipt-import", "spring/upload-utf8-header", "spring/upload-mockmvc-boundary"])

add("spring-web", "upload-utf8-header", "Spring CSV uploads: reject malformed UTF-8 and an unknown header",
"An upload format check decodes bounded bytes strictly and rejects content that does not match the import contract.", [
    ("The two rejected bodies", ["One MockMvc request claims text/csv but contains HTML. Another starts with the expected header and ends with an invalid UTF-8 byte. Both receive 422 and leave no staged file. The controller uses a decoder configured to report malformed and unmappable input, then requires the exact receipt_id,amount_minor header followed by content. This avoids accepting replacement characters silently in the local import contract.", "The header is only a first gate. It does not validate row quoting, numeric ranges, duplicates, line endings or a CSV injection policy. Those belong in an actual parser and domain validation stage. [[spring/upload-byte-budget|The byte limit]] bounds how much the decoder sees, while [[spring/upload-generated-filename|the path rule]] keeps a bad body from becoming a stored file."]),
    ("Define the text contract explicitly", ["A deployed importer needs a documented encoding and line-ending policy. If it accepts a BOM or CRLF, add deliberate branches and tests; do not rely on platform defaults. After parsing, report row numbers without logging sensitive record values. The fixture's narrow header requirement is useful evidence for early rejection, not a complete CSV specification."])
], '''String decoded = StandardCharsets.UTF_8.newDecoder()
    .onMalformedInput(CodingErrorAction.REPORT)
    .onUnmappableCharacter(CodingErrorAction.REPORT)
    .decode(ByteBuffer.wrap(content)).toString();
if (!decoded.startsWith(HEADER))
    throw new ResponseStatusException(HttpStatus.UNPROCESSABLE_CONTENT);''',
"MultipartReceiptImportTest.rejectsFakeCsvMediaTypeWhenBytesHaveWrongHeader and MultipartReceiptImportTest.rejectsMalformedUtf8BeforeStorage",
"The fixture checks two malformed inputs and one valid short body. It does not test CSV grammar, spreadsheet formula injection, record counts or localized number formats. Strict decoding is O(n) in bounded bytes and stores one decoded string in memory.",
["Do not trust a request Content-Type declaration as byte validation.", "Do not silently replace malformed UTF-8 if exact identifiers matter.", "Do not treat a matching header as proof that every row is valid."],
["spring/multipart-receipt-import", "spring/upload-byte-budget", "spring/upload-mockmvc-boundary"])

add("spring-testing", "upload-mockmvc-boundary", "Spring MockMvc multipart tests: what the fixture proves",
"A standalone MockMvc multipart test checks controller mapping and response behavior without running the servlet container parser.", [
    ("Assert state, not only status", ["The fixture sends valid, oversized, fake-format, invalid-UTF-8, empty and missing parts. For each rejection it checks that the temporary directory is empty; the accepted case checks the generated filename and exact stored bytes. Those assertions catch a controller that returns an error after leaving a staged file. The tests also show that a malicious original filename is ignored, but only inside a JUnit temporary directory.", "MockMultipartFile already contains the test bytes. Standalone MockMvc bypasses the deployed servlet multipart configuration, reverse proxy, request-size enforcement and authentication filter chain. [[spring/upload-byte-budget|The budget lesson]] separates controller checks from parser limits. [[spring/readiness-health-group|The readiness test]] uses a real local HTTP server for a different boundary."]),
    ("Add a deployed route check", ["Before exposing uploads, test a real container with max-file-size and max-request-size, accepted and rejected MIME declarations, interruption during transfer, storage failure, auth, CSRF or bearer rules, and concurrent uploads. The current controller is not registered in ReceiptApplication. A successful standalone test cannot prove that the actual application serves POST /contract/imports."])
], '''client.perform(multipart("/contract/imports").file(upload(
        "../../outside.csv", "text/csv", validCsv)))
    .andExpect(status().isOk());
assertEquals(1, storedFiles().size());''',
"MultipartReceiptImportTest runs five local tests covering accepted and rejected parts",
"These tests run without servlet-container parsing, deployment storage, authentication, request streaming or proxy limits. MockMultipartFile allocates its bytes in memory before the controller. The accepted test checks one short file; it is not a throughput benchmark.",
["Do not call standalone MockMvc an end-to-end upload test.", "Do not assert only a 413 or 422 while ignoring staged files.", "Do not infer container max-request-size behavior from controller code."],
["spring/multipart-receipt-import", "spring/upload-byte-budget", "spring/readiness-health-group", "spring/testing-boundaries"])

add("spring-production", "readiness-health-group", "Spring Boot readiness health group: withdraw traffic on a required dependency failure",
"A readiness probe tells a traffic router whether this instance can serve its required work now.", [
    ("The local HTTP result", ["The test starts ReceiptApplication on a random loopback port with probes enabled and a test-only importStore indicator included in the readiness group. When the AtomicBoolean-backed indicator is UP, /actuator/health/readiness returns 200. When it becomes DOWN, the same path returns 503. The liveness path remains 200, and the receipt API still rejects an anonymous request. This is a real local HTTP/filter-path check, unlike the earlier direct HealthIndicator unit test.", "ReceiptSecurity now permits the health endpoint and its nested group paths without credentials. It does not permit the API. [[spring/liveness-readiness-separation|The liveness lesson]] explains why a dependency failure should not necessarily ask an orchestrator to restart the process. [[spring/health-probe-security|The exposure lesson]] covers the narrow public path."]),
    ("Keep the health question narrow", ["The indicator in this test is not a real database or broker check. A production readiness component should measure the dependency required to accept new work, with a bounded timeout and no expensive query per probe. Include it in readiness only if the service cannot safely accept traffic without it. The app's default runtime configuration does not enable this test indicator or health group wiring; deployment configuration remains to be written."])
], '''management.endpoint.health.probes.enabled=true
management.endpoint.health.group.readiness.include=readinessState,importStore''',
"ReadinessHealthGroupHttpTest.failedImportStoreWithdrawsReadinessWithoutChangingLiveness",
"One temporary Boot server and an AtomicBoolean indicator prove local HTTP status mapping. There is no Kubernetes object, load balancer, real dependency timeout or deployment drain test. Frequent expensive health checks can increase load during an outage; the fixture's boolean is constant time.",
["Do not put every optional dependency into readiness.", "Do not call a test boolean a live database probe.", "Do not assume a local 503 has been wired to the orchestrator."],
["spring/liveness-readiness-separation", "spring/health-probe-security", "spring/dependency-readiness", "spring/actuator-health"])

add("spring-production", "liveness-readiness-separation", "Spring Boot liveness versus readiness: do not restart on every dependency outage",
"Liveness asks whether a process needs replacement; readiness asks whether it should receive new traffic.", [
    ("The two paths diverge", ["In the checked local server, importStore becomes DOWN. Readiness returns 503 while liveness still returns 200. That is intentional: a store outage can make new import work unsafe without proving that restarting this JVM will repair the store. The test also checks that anonymous API access remains 401, so probe exposure does not open business routes.", "Spring Boot's health groups supply distinct endpoint paths when probes are enabled. The custom importStore indicator is included only in readiness for this test. [[spring/readiness-health-group|The group lesson]] shows the property wiring. [[spring/dependency-readiness|The earlier indicator lesson]] checks UP/DOWN directly but does not establish HTTP behavior."]),
    ("Plan termination and recovery", ["When readiness fails, an orchestrator may stop sending new traffic, but in-flight work, drain time and queued jobs need their own policy. A bad liveness rule can create a restart loop across the fleet during a shared dependency failure. Set probe thresholds and timeouts from measured startup and recovery behavior. This fixture tests one instance at one point in time; no rolling deployment or restart policy is checked."])
], '''assertEquals(503, get("/actuator/health/readiness").statusCode());
assertEquals(200, get("/actuator/health/liveness").statusCode());
assertEquals(401, get("/api/receipts").statusCode());''',
"ReadinessHealthGroupHttpTest.failedImportStoreWithdrawsReadinessWithoutChangingLiveness",
"The local indicator flips immediately and has no network timeout or stale cache. These assertions say nothing about Kubernetes probe periods, restart thresholds, startup probes or graceful drain. The extra HTTP requests are low cost in the fixture; measure real indicators before choosing intervals.",
["Do not make a shared dependency outage a liveness failure by default.", "Do not assume readiness drains in-flight requests.", "Do not set probe thresholds without measuring startup and recovery."],
["spring/readiness-health-group", "spring/dependency-readiness", "spring/actuator-health", "spring/health-probe-security"])

add("spring-security", "health-probe-security", "Spring Security health probes: expose only the health path",
"A public health probe exception should match the intended Actuator health path without opening application data routes.", [
    ("The source-kit matcher", ["ReceiptSecurity permits /actuator/health and /actuator/health/**, then requires authentication for every other request. The readiness HTTP test calls the nested readiness path without credentials and receives 200 or 503 according to the indicator. It then calls /api/receipts anonymously and receives 401. The matcher change is small, but the test checks both allowed and protected outcomes.", "This does not settle whether health details should be public. The kit configures show-details=never. A deployed management port, reverse proxy or platform probe may use another exposure model. [[spring/readiness-health-group|The group lesson]] covers status mapping; [[spring/security-filter-chain|the filter-chain lesson]] covers matcher order and defaults."]),
    ("Treat the path as operational data", ["Health response bodies should avoid secrets, hostnames and raw dependency errors. Allowlisting a probe endpoint does not authorize a business endpoint, even when both share one server. Check any custom Actuator base path after deployment; hard-coded matchers can drift if the endpoint moves. This test checks only the kit's default /actuator path, one nested health group and the receipt API."])
], '''http.authorizeHttpRequests(requests -> requests
    .requestMatchers("/actuator/health", "/actuator/health/**").permitAll()
    .anyRequest().authenticated());''',
"ReadinessHealthGroupHttpTest.failedImportStoreWithdrawsReadinessWithoutChangingLiveness and HttpSecurityBoundaryTest.apiRejectsAnonymousRequest",
"The test has no external gateway, custom management port or changed Actuator base path. Public health paths still consume server resources and can reveal status; rate and detail policies belong to the deployment design. No sensitive details are enabled in the kit.",
["Do not permit every Actuator endpoint to expose health probes.", "Do not expose raw dependency errors in public health details.", "Do not skip an anonymous API denial assertion."],
["spring/readiness-health-group", "spring/liveness-readiness-separation", "spring/security-filter-chain", "spring/actuator-health"])

add("spring-exercises", "upload-and-probe-trace-exercise", "Spring exercise: trace upload rejection and readiness changes",
"An upload-and-probe trace distinguishes controller rejection, stored-file state and operational readiness.", [
    ("Predict the upload matrix", ["Send a valid short CSV with the original filename ../../outside.csv, an oversized part, an HTML body labelled text/csv, an invalid UTF-8 byte, an empty part and a missing part. Predict each status and whether the temporary directory contains a file. The accepted request stores bytes under a generated basename. The oversize request returns 413; fake-format and invalid-encoding requests return 422; empty and missing parts return 400. Rejected requests leave no file in the checked fixture.", "Now set the test dependency indicator DOWN. Predict readiness, liveness and anonymous API status: 503, 200 and 401. The two halves use different test boundaries. [[spring/upload-mockmvc-boundary|Multipart runs under standalone MockMvc]], while [[spring/readiness-health-group|health runs over a local HTTP port]]."]),
    ("Extend the proofs", ["Add a test where storage writing fails after a temporary path is created, then check cleanup. Add a deployed multipart size test against an actual servlet container, and a readiness test with a bounded dependency timeout. The source kit does not include those extensions, and this exercise has no hosted judge. State exactly which new outcome each extension would prove."])
], '''mvn -q -Dtest=MultipartReceiptImportTest,ReadinessHealthGroupHttpTest test''',
"MultipartReceiptImportTest and ReadinessHealthGroupHttpTest provide the local status and state outcomes",
"The exercise combines separate local fixtures; the upload route is not registered in ReceiptApplication and the health indicator is test-only. It does not model malware scanning, persistent import jobs, a Kubernetes probe or a real dependency outage.",
["Do not infer storage state from a response code alone.", "Do not call a malformed upload a parsed CSV row failure.", "Do not equate liveness with dependency readiness."],
["spring/multipart-receipt-import", "spring/upload-mockmvc-boundary", "spring/readiness-health-group", "spring/liveness-readiness-separation"])

add("spring-projects", "import-api-project", "Spring Boot receipt import project: stage, validate and report without hiding failure",
"A receipt import service needs bounded intake, durable staging, row validation and an observable completion record.", [
    ("What the source kit actually checks", ["The standalone upload controller accepts a short receipt CSV, rejects oversized or invalid bytes and ignores the caller filename for storage. A separate Boot HTTP test shows readiness tracking a test-only dependency state. These are useful pieces, but they are not one deployed import service. ReceiptApplication does not expose /contract/imports, and the local temporary file is not durable storage.", "The design should create an import ID bound to an authenticated tenant, stage bytes under a generated key, persist a job state and parse records with a clear row-error contract. A worker can process bounded chunks after the request returns. [[spring/multipart-receipt-import|The intake lesson]] covers the first boundary; [[spring/receipt-outbox-command|the outbox lesson]] covers a database intent record for later work."]),
    ("Release gates", ["Run the controller through the real servlet parser and proxy with configured request ceilings. Test storage failure, duplicate submissions, tenant ownership, format ambiguity, partial row errors, retry safety, retention and cleanup. Use an actual dependency indicator in readiness only when losing that dependency means the instance must stop taking new imports. Avoid putting a slow full-table query in each probe. Measure memory, disk and worker throughput with representative files before choosing the production limits."])
], '''// Target flow; not wired into ReceiptApplication yet.
ImportId importId = intake.stage(trustedTenant, boundedUpload);
jobs.enqueue(importId);
return importId;''',
"MultipartReceiptImportTest and ReadinessHealthGroupHttpTest provide separate local intake and health checks",
"This is a project design, not a runnable import service. The checked upload controller and test indicator are separate from the Boot entrypoint. There is no durable store, parser, worker, tenant identity, deployed proxy or lifecycle cleanup in the source kit.",
["Do not expose a test-only import route as if it were deployed.", "Do not call temporary local storage durable.", "Do not mark a job complete before row results are committed."],
["spring/multipart-receipt-import", "spring/readiness-health-group", "spring/receipt-outbox-command", "spring/tenant-command-api-project"])


def para(value: str) -> str:
    escaped = html.escape(value)
    return "<p>" + re.sub(r"\[\[([^|]+)\|([^\]]+)\]\]",
        lambda match: '<a href="/' + match[1] + '">' + match[2] + "</a>", escaped) + "</p>"


titles = {path: row["title"] for path, row in by_path.items()}
titles.update({spec["path"]: spec["title"] for spec in specs})
for spec in specs:
    path = spec["path"]
    assert path not in by_path, path
    assert all(target in titles for target in spec["links"]), path
    hub = next(row for row in rows if row["type"] == "subject" and row["subject"] == spec["subject"])
    body = para(spec["opening"])
    for heading, paragraphs in spec["sections"]:
        body += "<h2>" + html.escape(heading) + "</h2>" + "".join(para(value) for value in paragraphs)
    language = "bash" if spec["subject"] == "spring-exercises" else "properties" if spec["slug"] == "readiness-health-group" else "java"
    body += '<h2>Checked source</h2><pre><code class="language-' + language + '">' + html.escape(spec["code"].strip(), quote=False) + "</code></pre>"
    body += "<h2>Verification boundary</h2>" + para(spec["proof"] + " in the downloadable Spring source kit. The excerpt is shortened; the kit contains the complete test.")
    body += "<h2>Costs and limits</h2>" + para(spec["limits"])
    body += "<h3>Common Mistakes</h3><ul>" + "".join("<li>" + html.escape(item) + "</li>" for item in spec["mistakes"]) + "</ul>"
    body += "<h2>Read next</h2>" + para(", ".join("[[" + target + "|" + titles[target] + "]]" for target in spec["links"]) + ".")
    row = by_path["spring/if-match-receipt-write"].copy()
    row.update(id=str(uuid.uuid5(uuid.NAMESPACE_URL, "https://aitrove.in/" + path)), type="article",
        path=path, title=spec["title"], summary=spec["opening"], body=body,
        subject=spec["subject"], difficulty="Intermediate", status="published",
        tags=["spring", "spring-boot", spec["slug"]], featured=False,
        sort_order=900 + len(rows), published_at=stamp, created_at=stamp, updated_at=stamp)
    row["data"] = {"subject_root": "spring/spring-boot", "section_path": hub["path"],
        "kind": "tutorial", "content_format": "html",
        "reading_minutes": max(4, round(len(re.sub(r"<[^>]+>", " ", body).split()) / 150)),
        "author_path": "authors/aitrove-editorial", "seo_ready": True,
        "related": [{"path": target, "title": titles[target]} for target in spec["links"]],
        "framework_version": "Spring Boot 4.0.8 / Spring Framework 7",
        "java_version": "21 source-kit baseline", "verification_suite": spec["proof"],
        "download_path": "/downloads/aitrove-spring-source-kit.zip"}
    rows.append(row)
    by_path[path] = row

grouped = {
    "spring-web": ("Bounded receipt uploads", ["spring/multipart-receipt-import", "spring/upload-byte-budget", "spring/upload-utf8-header"]),
    "spring-security": ("Upload and health exposure", ["spring/upload-generated-filename", "spring/health-probe-security"]),
    "spring-testing": ("Multipart test scope", ["spring/upload-mockmvc-boundary"]),
    "spring-production": ("Readiness and liveness", ["spring/readiness-health-group", "spring/liveness-readiness-separation"]),
    "spring-exercises": ("Upload and probe traces", ["spring/upload-and-probe-trace-exercise"]),
    "spring-projects": ("Receipt import design", ["spring/import-api-project"]),
}
for subject, (title, paths) in grouped.items():
    hub = next(row for row in rows if row["type"] == "subject" and row["subject"] == subject)
    hub["data"]["modules"].append({"title": title,
        "summary": "Check byte, storage and operational health boundaries.", "lessons": paths})
    hub["updated_at"] = stamp
    if "<h2>Section lessons</h2>" in hub["body"]:
        links = "<ul>" + "".join('<li><a href="/' + path + '">' + html.escape(titles[path]) + "</a></li>"
            for module in hub["data"]["modules"] for path in module["lessons"]) + "</ul>"
        hub["body"] = re.sub(r"(<h2>Section lessons</h2>)[\s\S]*?(<h2>Continue learning</h2>)",
            lambda match: match[1] + links + match[2], hub["body"])

reverse = {
    "spring/rest-validation": ["spring/multipart-receipt-import"],
    "spring/receipt-media-types": ["spring/upload-utf8-header"],
    "spring/security-filter-chain": ["spring/health-probe-security"],
    "spring/testing-boundaries": ["spring/upload-mockmvc-boundary"],
    "spring/dependency-readiness": ["spring/readiness-health-group"],
    "spring/actuator-health": ["spring/liveness-readiness-separation"],
    "spring/receipt-api-project": ["spring/import-api-project"],
    "java/files": ["spring/upload-generated-filename"],
    "java/strict-utf8": ["spring/upload-utf8-header"],
}
for path, targets in reverse.items():
    assert path in by_path, path
    row = by_path[path]
    marker = "<h2>Continue with checked upload and readiness</h2>"
    row["body"] = row["body"].split(marker)[0] + marker + para("Continue with " + ", ".join(
        "[[" + target + "|" + titles[target] + "]]" for target in targets) + ".")
    row["updated_at"] = stamp

FILE.write_text(json.dumps(rows, ensure_ascii=False, indent=2) + "\n")
print(json.dumps({"added": [spec["path"] for spec in specs], "count": len(specs)}))
