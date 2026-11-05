"""Add original Spring Web delivery and client-boundary lessons to preview fixtures."""
import copy
import datetime
import html
import json
import pathlib
import re
import uuid

root = pathlib.Path(__file__).resolve().parents[1]
fixture = root / 'src/data/fixtures.json'
rows = json.loads(fixture.read_text())
by_path = {row['path']: row for row in rows}
stamp = datetime.datetime.now(datetime.UTC).isoformat()


def prose(value):
    return re.sub(r'\[\[([^|]+)\|([^\]]+)\]',
                  lambda match: '<a href="/' + match[1] + '">' + match[2] + '</a>',
                  html.escape(value))


lessons = [
    dict(slug='mvc-private-receipt-cache-policy', title='Spring MVC private Cache-Control: decide who may retain a receipt',
         summary='Cache-Control on a personalized response sets the storage boundary; a valid ETag alone does not make a tenant receipt safe for a shared cache.',
         blocks=[
             ('Bind the cache decision to the data', 'A receipt total is visible only to the authenticated tenant. A browser may keep a short-lived copy if product policy permits it, but an intermediary must not reuse the response for another user. Set a private directive on the response, and decide separately whether sensitive fields require no-store. [[spring/conditional-receipt-get|Conditional GET]] saves response bytes after authorization; it is not an authorization check.'),
             ('Validate before a conditional response', 'A client may send If-None-Match for a receipt it no longer owns. Resolve the tenant and authorize that receipt before computing the entity tag or returning 304. Scope the tag to the representation and tenant; changing visibility or serialization must change the validator. A private cache can still retain data on a shared device, so use no-store for a receipt that must leave no local copy.'),
             ('Test through the full path', 'Request the same receipt as its owner and as a second tenant, including a matching If-None-Match header. The owner may receive 304 after a prior 200; the second tenant must never get a revealing 304. Inspect Cache-Control on both 200 and 304. If a reverse proxy rewrites headers, test that deployed edge as well.')],
         code='@GetMapping("/receipts/{receiptId}")\nResponseEntity<ReceiptView> readReceipt(\n        @PathVariable UUID receiptId, Authentication authentication) {\n    ReceiptView receipt = receiptService.authorizedView(authentication, receiptId);\n    return ResponseEntity.ok()\n        .cacheControl(CacheControl.maxAge(Duration.ofMinutes(2)).cachePrivate())\n        .eTag("\\\"" + receipt.representationVersion() + "\\\"")\n        .body(receipt);\n}', language='java',
         cost='A short private cache can reduce repeated transfer and rendering. ETag calculation still costs enough to load the authorized version; no-store trades this saving for tighter data retention.',
         mistakes=['Do not mark tenant-specific receipts public.', 'Do not emit a 304 before checking current authorization.', 'Do not use a stable ETag when the visible representation or permissions changed.'],
         related=['spring/conditional-receipt-get','spring/receipt-media-types','spring/security-filter-chain','spring/mvc-range-receipt-download','spring/mvc-safe-download-filename'], backlink='spring/conditional-receipt-get'),
    dict(slug='mvc-range-receipt-download', title='Spring MVC byte ranges: resume an authorized receipt download',
         summary='Spring MVC can turn a Range request into a partial Resource response when the controller returns a repeatable Resource with a normal 200 response.',
         blocks=[
             ('Return a repeatable resource', 'A large archived receipt may need resume support after a dropped connection. A controller can return a FileSystemResource through ResponseEntity<Resource>; Spring MVC parses valid byte ranges and writes the selected region. The returned resource must support repeatable reads and a known length. An InputStreamResource is not suitable for this transparent range path. [[spring/mvc-streaming-response-disconnect|StreamingResponseBody]] is a different delivery contract.'),
             ('Authorize before opening storage', 'Resolve the receipt through the tenant-scoped storage service, then expose only the authorized file. Do not construct a filesystem path from a client filename or ID. Return status 200 in the controller even when Range is present; the MVC resource writer decides whether the response becomes 206. Apply the appropriate private cache and download-name policy. [[spring/mvc-private-receipt-cache-policy|Private caching]] still matters for a partial response.'),
             ('Exercise real headers', 'Test a normal GET, Range: bytes=0-46, an invalid range, and a second-tenant request. Check the actual Content-Range, status and selected byte count, rather than only asserting controller return values. Verify that the underlying resource stays readable until the response finishes; deleting a temporary file early can break the transfer.')],
         code='@GetMapping(path = "/receipts/{receiptId}/pdf", produces = "application/pdf")\nResponseEntity<Resource> download(\n        @PathVariable UUID receiptId, Authentication authentication) {\n    Resource pdf = receiptStorage.authorizedFile(authentication, receiptId);\n    return ResponseEntity.ok() // MVC changes this to 206 for a valid Range.\n        .contentType(MediaType.APPLICATION_PDF)\n        .cacheControl(CacheControl.noStore())\n        .body(pdf);\n}', language='java',
         cost='A range response reads and transfers only the selected bytes, but multiple tiny ranges increase request overhead. Storage still needs an efficient seekable resource and an authorization check on every request.',
         mistakes=['Do not return InputStreamResource for automatic range handling.', 'Do not manually set 206 on the controller ResponseEntity.', 'Do not use the request path as a storage path.'],
         related=['spring/mvc-streaming-response-disconnect','spring/mvc-private-receipt-cache-policy','spring/mvc-safe-download-filename','spring/upload-byte-budget','spring/receipt-media-types'], backlink='spring/mvc-streaming-response-disconnect'),
    dict(slug='mvc-safe-download-filename', title='Spring MVC Content-Disposition: produce a safe attachment filename',
         summary='A download filename is presentation metadata; derive it from authorized server data and let ContentDisposition encode the header.',
         blocks=[
             ('Separate identity from a label', 'A client may request receipt 47 and submit an arbitrary filename in the URL. The storage lookup must use the authorized receipt identity, while the attachment label comes from a controlled server field. Restrict the label to an expected form such as receipt-47.pdf and keep its extension consistent with the response media type. [[spring/mvc-range-receipt-download|Byte-range delivery]] uses the same rule on every partial request.'),
             ('Let the header builder encode', 'Content-Disposition has quoting and non-ASCII filename rules. Assemble it with ContentDisposition.attachment().filename(name, UTF_8) rather than concatenating raw user text into a header. Encoding protects header syntax, but it does not make an untrusted path component safe for storage or prevent misleading names. Normalize or reject separators, controls and unexpected extensions before building the value.'),
             ('Check the client-facing result', 'Test ASCII and non-ASCII controlled labels and inspect the parsed Content-Disposition value. Also test a malicious submitted name; the server label should remain unchanged. A browser may choose its own saved filename despite the header, so tests should assert the response contract rather than a particular browser dialog.')],
         code='String attachmentName = "receipt-47.pdf"; // Derived from server metadata.\nContentDisposition attachment = ContentDisposition.attachment()\n    .filename(attachmentName, StandardCharsets.UTF_8)\n    .build();\nreturn ResponseEntity.ok()\n    .header(HttpHeaders.CONTENT_DISPOSITION, attachment.toString())\n    .contentType(MediaType.APPLICATION_PDF)\n    .body(receiptStorage.authorizedFile(authentication, receiptId));', language='java',
         cost='Header construction is constant work. The expensive operation is reading the attachment; a misleading or unsafe name creates client-side confusion even when bytes are correct.',
         mistakes=['Do not paste a client-supplied filename into the header.', 'Do not confuse header encoding with filesystem path validation.', 'Do not advertise .pdf while returning another media type.'],
         related=['spring/mvc-range-receipt-download','spring/receipt-media-types','spring/multipart-receipt-import','spring/upload-byte-budget','spring/mvc-private-receipt-cache-policy'], backlink='spring/multipart-receipt-import'),
    dict(slug='mvc-versioned-static-asset-cache', title='Spring MVC versioned static assets: cache immutable bytes by content',
         summary='A content-versioned asset URL can carry a long cache lifetime because a byte change yields a different URL; HTML and private API responses need separate policies.',
         blocks=[
             ('Version the address, not the clock', 'A deployed stylesheet may keep its old bytes in a browser for months. If its URL contains a content-derived version, a changed build produces a different address and can use a long public cache lifetime. A plain /assets/site.css URL cannot safely promise that lifetime across deployments. [[spring/mvc-private-receipt-cache-policy|Tenant data]] must not inherit this static-asset policy.'),
             ('Generate URLs through the resolver', 'Configure a resource handler with a VersionResourceResolver, then generate links through ResourceUrlProvider or a view integration that applies the resource chain. Merely configuring the resolver does not rewrite hard-coded page URLs. If precompressed variants are served, resolver ordering matters: version the original bytes consistently. Keep HTML relatively fresh so it can point at the newly versioned asset.'),
             ('Test two builds', 'Build with one stylesheet, capture its generated URL and response headers, then change one byte and build again. The new URL should differ, both versions should return the expected content while deployed, and the HTML should reference the current version. A CDN that purges old assets before old HTML expires can still break users.')],
         code='@Configuration\nclass AssetDelivery implements WebMvcConfigurer {\n    @Override public void addResourceHandlers(ResourceHandlerRegistry registry) {\n        registry.addResourceHandler("/assets/**")\n            .addResourceLocations("classpath:/static/assets/")\n            .setCacheControl(CacheControl.maxAge(Duration.ofDays(365)).cachePublic())\n            .resourceChain(true)\n            .addResolver(new VersionResourceResolver()\n                .addContentVersionStrategy("/**"));\n    }\n}', language='java',
         cost='The resource chain performs version resolution and may cache lookups. Long-lived browser and CDN copies reduce repeated asset transfer, while retaining old versioned files consumes deployment storage.',
         mistakes=['Do not give unversioned files a one-year public lifetime.', 'Do not assume hard-coded asset links acquire a version automatically.', 'Do not apply the asset cache rule to HTML or personalized responses.'],
         related=['spring/mvc-private-receipt-cache-policy','spring/boot-layered-jar-image-cache','spring/boot-executable-jar-classpath','spring/receipt-media-types','spring/conditional-receipt-get'], backlink='spring/boot-executable-jar-classpath'),
    dict(slug='webclient-request-attributes-context', title='Spring WebClient attributes versus Reactor Context: choose the right request scope',
         summary='A WebClient attribute belongs to one client request; Reactor Context follows a reactive subscription into later or nested client requests.',
         blocks=[
             ('Keep local policy local', 'One receipt lookup can tag a request with a routing hint through attribute. An ExchangeFilterFunction can inspect it, but a second request created inside flatMap does not receive that attribute automatically. This is useful for a one-call option such as an audit classification. A correlation value that must reach nested requests belongs in Reactor Context at the outer subscription boundary.'),
             ('Do not turn context into authority', 'A request attribute or context value is application metadata, not proof of user permission. The receiving service must still authenticate and authorize its own request. Keep context keys typed or centrally named to avoid collision, and avoid putting passwords or full receipt bodies there. [[spring/webclient-response-ownership|Response ownership]] remains with the code that decodes each exchange.'),
             ('Test a nested call', 'Issue one client request that triggers another in flatMap. Assert a one-call attribute affects only the first request, then place a trace identifier in Reactor Context and assert both filters see it. Run the test without the context key too; the filter should have an explicit fallback or fail clearly rather than throwing an unexplained lookup error.')],
         code='WebClient receiptClient = WebClient.builder()\n    .filter((request, next) -> Mono.deferContextual(context -> {\n        String traceId = context.getOrDefault("receiptTraceId", "missing");\n        ClientRequest tagged = ClientRequest.from(request)\n            .header("X-Trace-Id", traceId).build();\n        return next.exchange(tagged);\n    }))\n    .build();\n\nMono<ReceiptView> result = receiptClient.get().uri(receiptUri)\n    .retrieve().bodyToMono(ReceiptView.class)\n    .contextWrite(context -> context.put("receiptTraceId", "trace-47"));', language='java',
         cost='Context lookup and one header are small per request. The main cost is accidental metadata loss across manually started subscriptions or a security bug if context is mistaken for authorization.',
         mistakes=['Do not expect a WebClient attribute to propagate to nested requests.', 'Do not use Reactor Context as an authentication decision by itself.', 'Do not call subscribe manually in the middle of a chain and assume the original context follows.'],
         related=['spring/webclient-response-ownership','spring/webclient-status-specific-decoding','spring/webclient-redacted-request-audit','spring/security-filter-chain','spring/trusted-forwarded-headers'], backlink='spring/webclient-response-ownership'),
    dict(slug='webclient-redacted-request-audit', title='Spring WebClient request audit: log route identity without payload leakage',
         summary='An ExchangeFilterFunction can record outbound method and approved route metadata; logging the complete URL, headers or body can leak credentials and tenant data.',
         blocks=[
             ('Record a bounded event', 'For a receipt gateway, an outbound audit event may need the operation name, method, result category and duration. The request URL can include a token or personal identifier in its query, so omit the query and use an approved route label when paths contain IDs. Do not dump Authorization or Cookie headers. [[spring/webclient-request-attributes-context|A request attribute]] can carry an internal operation label for this single exchange.'),
             ('Keep the response body owned', 'A filter that forwards next.exchange(request) can observe status without consuming the body. If it instead reads the body to print it, the caller may no longer be able to decode it and pooled buffers may remain unreleased. Capture timing around the publisher and pass the same response onward. [[spring/webclient-response-ownership|Response ownership]] explains how a filter must release a body when it terminates an exchange.'),
             ('Verify safe failure paths', 'Use a mock HTTP server to return a success, a non-2xx response, and a connection failure. Assert one bounded event per subscription and check that secrets and query parameters never enter captured logs. Also verify the caller can still decode the body. A filter runs on subscription, so constructing a Mono alone should emit no audit event.')],
         code='ExchangeFilterFunction requestAudit = (request, next) -> {\n    String operation = request.attribute("operation")\n        .map(String::valueOf).orElse("unclassified");\n    long started = System.nanoTime();\n    return next.exchange(request)\n        .doOnNext(response -> auditLog.info("outbound={} method={} status={} elapsedMs={}",\n            operation, request.method(), response.statusCode().value(),\n            Duration.ofNanos(System.nanoTime() - started).toMillis()))\n        .doOnError(failure -> auditLog.warn("outbound={} method={} failed",\n            operation, request.method()));\n};', language='java',
         cost='One event per subscribed request adds log volume and formatting work. Sampling or aggregation may be needed at high request rates; logging bodies creates far greater memory, latency and privacy cost.',
         mistakes=['Do not log full URLs with query strings, credentials or personal IDs.', 'Do not consume the response body in an audit filter and then hand the empty response to the caller.', 'Do not assume a constructed but unsubscribed Mono sent a request.'],
         related=['spring/webclient-response-ownership','spring/webclient-request-attributes-context','spring/webclient-status-specific-decoding','spring/filters-vs-interceptors','spring/trusted-forwarded-headers'], backlink='spring/webclient-status-specific-decoding'),
    dict(slug='stomp-message-subscribe-authorization', title='Spring STOMP authorization: separate SEND from SUBSCRIBE permissions',
         summary='An authenticated WebSocket handshake does not authorize every STOMP destination; inbound MESSAGE and SUBSCRIBE frames need separate destination rules.',
         blocks=[
             ('Two frame types, two capabilities', 'A receipt client may send a command to an application prefix and subscribe to updates, but it must not publish directly to the broker topic. Authorization rules should allow the intended MESSAGE destination and deny client MESSAGE frames to broker prefixes. A SUBSCRIBE rule must also constrain which tenant or user queue can be observed. [[spring/stomp-handshake-identity|Handshake identity]] establishes the principal; destination checks govern actions after connection.'),
             ('Apply ownership to identifiers', 'A pattern such as /topic/tenants/{tenantId}/receipts is not safe merely because the caller is authenticated. Compare the tenantId with a verified tenant claim or domain authorization result. Keep a final deny rule for unhandled MESSAGE and SUBSCRIBE frames. Server-originated sends through SimpMessageSendingOperations follow a different path from client inbound messages. [[spring/websocket-stomp-boundary|The STOMP boundary]] explains that distinction.'),
             ('Attack-test the matrix', 'Connect as two tenants. For each principal, attempt an allowed application SEND, a forbidden direct broker SEND, a permitted subscription, and a cross-tenant subscription. Assert denial at the inbound frame boundary and check that no forbidden message is broadcast. A successful HTTP handshake is not evidence that these four cases are covered.')],
         code='@Configuration\n@EnableWebSocketSecurity\nclass ReceiptSocketSecurity {\n    @Bean\n    AuthorizationManager<Message<?>> messageAuthorization(\n            MessageMatcherDelegatingAuthorizationManager.Builder messages) {\n        messages.simpSubscribeDestMatchers("/user/queue/receipts")\n            .authenticated();\n        messages.simpTypeMatchers(SimpMessageType.SUBSCRIBE).denyAll();\n        messages.simpDestMatchers("/topic/**", "/queue/**").denyAll();\n        messages.simpDestMatchers("/app/receipts/**").authenticated();\n        messages.simpTypeMatchers(SimpMessageType.MESSAGE).denyAll();\n        messages.anyMessage().authenticated();\n        return messages.build();\n    }\n}', language='java',
         cost='Each inbound frame incurs matcher and authorization work. Broad subscriptions can also drive high fan-out and broker memory use; authorization and [[spring/stomp-slow-client-budget|slow-client budgets]] address different costs.',
         mistakes=['Do not rely on HTTP handshake authentication as destination authorization.', 'Do not permit client MESSAGE frames to broker-owned destinations.', 'Do not use an authenticated-only rule for tenant-addressed subscriptions without checking tenant ownership.'],
         related=['spring/stomp-handshake-identity','spring/websocket-stomp-boundary','spring/stomp-slow-client-budget','spring/stomp-broker-scale-boundary','spring/security-filter-chain'], backlink='spring/websocket-stomp-boundary'),
]

titles = {path: row['title'] for path, row in by_path.items()}
titles.update({'spring/' + lesson['slug']: lesson['title'] for lesson in lessons})
for number, lesson in enumerate(lessons):
    path = 'spring/' + lesson['slug']
    assert path not in by_path, path
    for target in lesson['related']:
        assert target in titles, (path, target)
    body = '<p>' + prose(lesson['summary']) + '</p>'
    for heading, content in lesson['blocks']:
        body += '<h2>' + html.escape(heading) + '</h2><p>' + prose(content) + '</p>'
    body += '<h2>Implementation contract</h2><pre><code class="language-' + lesson['language'] + '">' + html.escape(lesson['code'], quote=False) + '</code></pre>'
    body += '<h2>Cost and verification</h2><p>' + prose(lesson['cost']) + '</p>'
    body += '<h3>Common Mistakes</h3><ul>' + ''.join('<li>' + prose(mistake) + '</li>' for mistake in lesson['mistakes']) + '</ul>'
    body += '<h2>Read next</h2><p>' + ', '.join('<a href="/' + target + '">' + html.escape(titles[target]) + '</a>' for target in lesson['related']) + '.</p>'
    row = copy.deepcopy(by_path['spring/component-scan-vs-bean'])
    row.update(id=str(uuid.uuid5(uuid.NAMESPACE_URL, 'https://aitrove.in/' + path)), path=path,
               title=lesson['title'], summary=lesson['summary'], body=body,
               subject='spring-web', tags=['spring', 'spring-web', lesson['slug']],
               sort_order=6900 + number, published_at=stamp, created_at=stamp, updated_at=stamp)
    row['data'] = {'subject_root': 'spring/spring-boot', 'section_path': 'spring/web-apis',
                   'kind': 'tutorial', 'content_format': 'html', 'seo_ready': True,
                   'reading_minutes': max(4, round(len(re.sub(r'<[^>]+>', ' ', body).split()) / 150)),
                   'author_path': 'authors/aitrove-editorial',
                   'framework_version': 'Spring Boot 4 / Spring Framework 7 where relevant',
                   'java_version': '21 or later',
                   'verification_suite': 'Spring Web API contract review; snippets require an application-specific model',
                   'related': [{'path': target, 'title': titles[target]} for target in lesson['related']]}
    rows.append(row)
    by_path[path] = row

new_paths = ['spring/' + lesson['slug'] for lesson in lessons]
hub = by_path['spring/web-apis']
hub['data']['modules'].append({'title': 'HTTP delivery and client boundaries',
                               'summary': 'Private response caches, range downloads, attachment names, static asset versions, client context and STOMP permissions.',
                               'lessons': new_paths})
hub['body'] += '<h2>HTTP delivery and client boundaries</h2><ul>' + ''.join(
    '<li><a href="/' + path + '">' + html.escape(titles[path]) + '</a></li>' for path in new_paths) + '</ul>'
hub['updated_at'] = stamp
for lesson in lessons:
    target = 'spring/' + lesson['slug']
    entry = by_path[lesson['backlink']]
    entry['body'] += '<h2>Related delivery contract</h2><p><a href="/' + target + '">' + html.escape(titles[target]) + '</a>.</p>'
    entry['updated_at'] = stamp
for source, target in [
    ('spring/receipt-media-types', 'spring/mvc-private-receipt-cache-policy'),
    ('spring/receipt-media-types', 'spring/mvc-safe-download-filename'),
    ('spring/upload-byte-budget', 'spring/mvc-range-receipt-download'),
    ('spring/conditional-receipt-get', 'spring/mvc-versioned-static-asset-cache'),
    ('spring/webclient-status-specific-decoding', 'spring/webclient-request-attributes-context'),
    ('spring/filters-vs-interceptors', 'spring/webclient-redacted-request-audit'),
    ('spring/stomp-handshake-identity', 'spring/stomp-message-subscribe-authorization'),
]:
    entry = by_path[source]
    entry['body'] += '<h2>Related delivery contract</h2><p><a href="/' + target + '">' + html.escape(titles[target]) + '</a>.</p>'
    entry['updated_at'] = stamp

fixture.write_text(json.dumps(rows, ensure_ascii=False, indent=2) + '\n')
print(f'Added {len(lessons)} Spring Web lessons; {len(rows)} total fixture records')
