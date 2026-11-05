"""Publish checked JWT tenant, query and security-trace lessons under Spring."""
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


add("spring-security", "jwt-tenant-principal", "Spring Security JWT tenant principal: map only a validated claim",
"A JWT tenant principal is an identity value taken from a validated token claim, not from a request header or URL segment.", [
    ("The converter has a trust precondition", ["The source-kit web context verifies a locally signed JWT, its issuer, audience, expiry and required tenant_id claim before the JWT authentication converter uses tenant_id as the principal name. The token has subject reviewer-41, yet the tenant service sees tenant-east. That distinction is intentional: user identity and tenant ownership are different fields, even when an application chooses a tenant claim for this narrow fixture.", "The path /contract/tenant/tenant-east returns the east row. A request for tenant-west with the same token returns 403. Sending X-Tenant: tenant-west does not change the principal. [[spring/jwt-resource-server|The base JWT lesson]] checks token trust and scope without tenant mapping; [[spring/tenant-jdbc-predicate|the query lesson]] checks the database side of this boundary."]),
    ("Choose a claim contract before coding", ["A signature proves who issued the token, not that every claim was assigned by an authorized tenant registry. The issuer must define tenant membership, rotation and revocation rules. A production system may use a stable subject plus a separately checked tenant membership service instead of treating tenant_id as the principal. Do not accept a caller-selected tenant header as a replacement for that trust decision."])
], '''var converter = new JwtAuthenticationConverter();
converter.setPrincipalClaimName("tenant_id");
http.oauth2ResourceServer(resource -> resource.jwt(jwt ->
    jwt.decoder(decoder).jwtAuthenticationConverter(converter)));''',
"JwtTenantBoundaryTest.trustedTenantClaimPassesTheMatchingServiceRule and JwtTenantBoundaryTest.anotherTenantIsForbiddenAfterAuthentication",
"The test uses ephemeral RSA keys and a local web context. It does not contact an identity provider, check JWKS rotation or model users with membership in multiple tenants. Signature verification and database lookup add per-request CPU and I/O respectively; cache any derived membership only with a revocation policy.",
["Do not trust X-Tenant as an identity source.", "Do not confuse token subject with tenant ownership.", "Do not map an unvalidated optional claim into the principal."],
["spring/jwt-resource-server", "spring/tenant-claim-required", "spring/tenant-jdbc-predicate", "spring/tenant-receipt-authorization"])

add("spring-security", "scope-versus-tenant-access", "Spring Security scope versus tenant ownership: two separate decisions",
"A token scope permits a class of operation; tenant ownership decides which records that operation may touch.", [
    ("The same HTTP status can hide a different failure", ["In the checked web context, a signed token with receipt.write cannot call a receipt.read endpoint: the filter chain returns 403 before the service. A token with receipt.read but tenant-east cannot read the tenant-west path: the method rule returns 403. Both are forbidden, but the responsible layer differs. A valid scope does not grant all tenant rows.", "The filter requires SCOPE_receipt.read. The managed reader uses @PreAuthorize to compare its tenant argument with authentication.name, which came from the validated JWT tenant_id. The JDBC query also has tenant_id in its predicate. This gives [[spring/tenant-jdbc-predicate|a database backstop]] if a caller changes routes or calls another service method. [[spring/role-authority-prefix|Roles and authorities]] have different naming rules; do not substitute a role string for a scope without an explicit mapping."]),
    ("Trace decisions in order", ["First verify token trust and required claims. Then check endpoint scope, service ownership and row predicate. Record denial counts by layer without logging bearer tokens. If the user has access to several tenants, the identity system needs a membership rule for the selected tenant; this single-tenant fixture deliberately does not implement that model."])
], '''.authorizeHttpRequests(requests -> requests
    .requestMatchers("/contract/tenant/**").hasAuthority("SCOPE_receipt.read"))

@PreAuthorize("#p0 == authentication.name")
public String read(String tenant) { return scopedLookup(tenant); }''',
"JwtTenantBoundaryTest.wrongScopeIsForbiddenBeforeTheService and JwtTenantBoundaryTest.anotherTenantIsForbiddenAfterAuthentication",
"Two MockMvc requests check local filter and method outcomes. The fixture has no remote issuer, real tenant registry, token revocation, database row-level security or deployed gateway. Extra ownership checks add small local comparison cost; the database predicate must still be indexed for large tables.",
["Do not equate receipt.read with permission to read every receipt.", "Do not infer the denial layer from HTTP 403 alone.", "Do not let a URL tenant override the signed tenant identity."],
["spring/jwt-tenant-principal", "spring/tenant-jdbc-predicate", "spring/method-authorization", "spring/role-authority-prefix"])

add("spring-security", "tenant-claim-required", "Spring JWT tenant claims: reject missing or malformed ownership before conversion",
"A required tenant claim should fail token validation before a service attempts tenant authorization.", [
    ("Reject absence at the decoder", ["The local decoder checks that tenant_id is present and matches the fixture's tenant-[a-z]+ format. A signed, unexpired token with the correct scope but no tenant_id returns 401. The controller does not receive a null principal and try to guess a tenant from the path. The format rule is only syntax; it does not prove that the issuer was allowed to grant tenant-east.", "Issuer, audience, timestamps and signature are checked in the same decoder chain. A token that has a valid tenant string but the wrong audience is still not for this API. [[spring/jwt-resource-server|The trust fixture]] covers those separate rejections. The [[spring/jwt-tenant-principal|principal converter]] runs only after the decoder accepts the token in this bounded context."]),
    ("Make claim changes a migration", ["If the identity provider changes claim names or casing, clients can suddenly receive 401. Publish a claim contract with allowed values and an overlap plan. Do not silently fall back to a request header during migration; that turns a missing signed claim into caller-controlled identity. Treat an unknown tenant as denied even if its string matches the syntax rule."])
], '''jwt -> {
    String tenant = jwt.getClaimAsString("tenant_id");
    return tenant != null && tenant.matches("tenant-[a-z]+")
        ? OAuth2TokenValidatorResult.success()
        : OAuth2TokenValidatorResult.failure(new OAuth2Error("invalid_tenant"));
}''',
"JwtTenantBoundaryTest.missingTenantClaimIsRejectedByTheDecoder",
"The regex is a small local syntax check. This test does not fetch tenant membership, check revoked tokens or exercise a remote authorization server. Regex complexity here is linear in a short claim; production should also bound token size at the HTTP edge.",
["Do not replace a missing signed claim with an untrusted header.", "Do not mistake a well-formed tenant string for authorized membership.", "Do not let a null claim reach repository selection."],
["spring/jwt-tenant-principal", "spring/jwt-resource-server", "spring/scope-versus-tenant-access"])

add("spring-security", "tenant-jdbc-predicate", "Spring JdbcTemplate tenant predicates: put ownership in the SQL query",
"A tenant-scoped repository query includes the trusted tenant identifier in its database predicate for every read or write.", [
    ("The same receipt ID exists twice", ["The H2 fixture stores R-41 for tenant-east and tenant-west with different states. Querying by receipt ID and tenant ID returns accepted for east, held for west and no row for a third tenant. The authenticated web request for east reaches that query; a west route under the east token is denied by method security before query execution. The two checks cover separate boundaries.", "Do not fetch by receipt ID alone and filter afterward. That can disclose the wrong row through logging, caching, serialization or a later code path. Use the trusted identity mapped in [[spring/jwt-tenant-principal|JWT validation]], then bind it as a SQL parameter. For writes, include tenant_id and expected state or version in the update predicate, and inspect the affected row count. [[spring/tenant-receipt-write|The earlier write fixture]] is only an in-memory service rule."]),
    ("Keys and plans matter", ["The fixture uses a composite primary key (receipt_id, tenant_id). A real schema should choose an index order based on its query patterns and verify the plan on the target database. The predicate is an application safeguard; database row-level security can add another independent boundary if the platform supports it. Never form SQL identifiers from tenant text."])
], '''String state = jdbc.queryForObject(
    "select state from tenant_receipt where receipt_id = ? and tenant_id = ?",
    String.class, "R-41", trustedTenant);''',
"JwtTenantBoundaryTest.scopedQueryExcludesRowsForOtherTenantValues and JwtTenantBoundaryTest.trustedTenantClaimPassesTheMatchingServiceRule",
"The test checks three tenant values against two H2 rows and one authenticated request. It does not prove target-database plans, row-level security, large-table latency or that every application repository uses the predicate. An indexed point lookup is expected to scale with index depth plus returned rows; measure the chosen schema.",
["Do not query by receipt ID and filter in Java afterward.", "Do not pass a URL or header tenant into SQL without a membership decision.", "Do not ignore a zero-row update in a tenant-scoped write."],
["spring/jwt-tenant-principal", "spring/scope-versus-tenant-access", "spring/tenant-receipt-write", "spring/jdbc-template"])

add("spring-security", "tenant-header-spoof", "Spring tenant headers: prove they cannot override a signed identity",
"A caller-supplied tenant header is request data and must not replace the tenant identity established by authentication.", [
    ("The header changes nothing in the fixture", ["A valid tenant-east token requests the east row while sending X-Tenant: tenant-west. The result is still tenant-east:accepted. The same token requests the tenant-west route and sets the header to tenant-west; the service rule returns 403. Those cases show that this local controller ignores the header for ownership. The URL path is also only a requested resource, not authority.", "A reverse proxy may inject a trusted tenant header after authentication in some architectures. That requires a strict network trust boundary, header stripping at the edge and a documented mapping to the authenticated principal. This source kit has no such proxy. Treat its headers as untrusted. [[spring/jwt-tenant-principal|The signed claim]] supplies the fixture's principal, and [[spring/tenant-jdbc-predicate|the SQL predicate]] carries it to storage."]),
    ("Test the negative route", ["A positive request with an irrelevant spoofed header is not enough: the cross-tenant route must still fail when the attacker aligns both path and header. The test checks both. It does not prove that every ingress path strips a tenant header; deployed proxy tests are still needed before relying on header-based identity anywhere in the system."])
], '''client.perform(get("/contract/tenant/tenant-west")
    .header("Authorization", "Bearer " + token("tenant-east", "receipt.read"))
    .header("X-Tenant", "tenant-west"))
    .andExpect(status().isForbidden());''',
"JwtTenantBoundaryTest.trustedTenantClaimPassesTheMatchingServiceRule and JwtTenantBoundaryTest.anotherTenantIsForbiddenAfterAuthentication",
"The test runs one local filter chain and controller. It does not include a CDN, gateway or reverse proxy. No additional database work is performed for the denied call; a production service should verify this side-effect boundary explicitly.",
["Do not accept a tenant header from the open internet as identity.", "Do not treat path parameters as proof of ownership.", "Do not test only the positive request when spoofing is the risk."],
["spring/jwt-tenant-principal", "spring/scope-versus-tenant-access", "spring/tenant-jdbc-predicate"])

add("spring-testing", "jwt-web-context-test", "Test Spring JWT authorization through filters, service proxy and SQL",
"A security integration test must exercise every layer named in its claim: decoder, filter chain, managed service and scoped query.", [
    ("The fixture installs actual local components", ["JwtTenantBoundaryTest creates a Spring web application context, installs springSecurity() on MockMvc, registers a JWT decoder, and calls a managed @PreAuthorize reader backed by JdbcTemplate. It checks success for the matching tenant, 403 for wrong scope, 403 for wrong tenant, 401 for missing tenant claim, and distinct H2 rows under one receipt ID. A direct call to the target method would miss both filters and the proxy rule.", "This is broader than [[spring/mockmvc-standalone-scope|standalone MockMvc]], which registers a controller directly. It is still a local context, not the site's full Boot application component scan or a live server. The signing keys are generated in the test, not discovered through remote JWKS. [[spring/failure-layer-matrix|The failure-layer lesson]] explains how to state that evidence honestly."]),
    ("Keep negative cases tied to state", ["The test's denied reads return no protected value. For a write, also inspect the database afterward to prove that no mutation occurred. Add an untrusted-header case because a path-only denial can miss an identity override. Before release, repeat these checks against the deployed route, actual issuer and target database, including issuer outage and key rotation."])
], '''client = MockMvcBuilders.webAppContextSetup(context)
    .apply(springSecurity()).build();

client.perform(get("/contract/tenant/tenant-west")
    .header("Authorization", "Bearer " + eastToken))
    .andExpect(status().isForbidden());''',
"JwtTenantBoundaryTest.trustedTenantClaimPassesTheMatchingServiceRule, JwtTenantBoundaryTest.wrongScopeIsForbiddenBeforeTheService, JwtTenantBoundaryTest.anotherTenantIsForbiddenAfterAuthentication and JwtTenantBoundaryTest.missingTenantClaimIsRejectedByTheDecoder",
"The five local tests create an in-memory H2 database and web context per method. They cost more than a plain unit test but omit remote issuer discovery, application deployment, gateway behavior, real database grants and write-side effects. No performance or production trust claim follows from their speed.",
["Do not call a direct service-object test proof of a security filter.", "Do not call MockMvc proof of a deployed proxy path.", "Do not infer database safety from a 403 without checking the protected state."],
["spring/jwt-tenant-principal", "spring/scope-versus-tenant-access", "spring/tenant-jdbc-predicate", "spring/mockmvc-standalone-scope"])

add("spring-projects", "tenant-receipt-api-security-plan", "Spring Boot receipt API: move from local Basic auth to tenant-scoped tokens",
"A tenant-aware receipt API needs a trusted identity source, a declared permission rule and an owner predicate at the data boundary.", [
    ("The source kit has two separate systems", ["The runnable ReceiptApplication uses an in-memory receipt store and local Basic credentials. The JWT tenant fixture is a separate test web context with temporary signing keys and H2 rows. They have not been combined into one deployed API. A migration would replace the local user store, configure a real resource-server issuer and audience, validate tenant membership, then pass an immutable trusted owner to service and repository calls.", "Do not switch authentication and assume authorization follows. The filter can require SCOPE_receipt.read while a service checks selected tenant membership; the query must include tenant_id. [[spring/tenant-jdbc-predicate|The H2 query lesson]] covers row selection. [[spring/scope-versus-tenant-access|The scope lesson]] shows that two different 403 decisions can exist in one request."]),
    ("Define release gates", ["Store receipts durably with migrations and an index for tenant-scoped access. Test two tenants with the same receipt ID for reads and writes; test token expiry, wrong issuer, wrong audience, missing claim and old signing keys. Check startup and request behavior when the issuer is unavailable. The current local JWT fixture only checks static trusted keys. Before exposing the endpoint, replace fixture credentials and prove that web, method and SQL boundaries agree in the deployed environment."])
], '''// Target service boundary; the current application does not deploy this flow.
@PreAuthorize("#p0 == authentication.name")
public Receipt read(String trustedTenant, String receiptId) {
    return receiptRepository.findByIdAndTenant(receiptId, trustedTenant);
}''',
"JwtTenantBoundaryTest.trustedTenantClaimPassesTheMatchingServiceRule and JwtTenantBoundaryTest.scopedQueryExcludesRowsForOtherTenantValues",
"This is a migration plan backed by a separate local fixture, not a runnable production API. Real identity integration adds provider availability, key cache, revocation and membership costs. A database-backed API also needs pool sizing, migrations and deployed authorization tests.",
["Do not deploy the source kit's local Basic credentials.", "Do not assume a token signature alone grants a tenant row.", "Do not call the separate JWT fixture the current application's authentication path."],
["spring/receipt-api-project", "spring/jwt-tenant-principal", "spring/scope-versus-tenant-access", "spring/tenant-jdbc-predicate"])

add("spring-exercises", "tenant-auth-trace-exercise", "Spring security exercise: trace four JWT request outcomes",
"A JWT authorization trace follows token validation, endpoint scope, method ownership and database lookup in that order.", [
    ("Predict before running", ["For a GET /contract/tenant/tenant-east, predict the status when a signed token has tenant-east and receipt.read. Repeat with receipt.write, with tenant-west in the URL, and with tenant_id absent. Keep the token issuer, audience and signature valid in each case so only one boundary changes. Write down which layer rejects each request, not only its status code.", "The source-kit outcomes are 200 for the matching request, 403 for wrong scope, 403 for wrong tenant and 401 for missing tenant claim. The matching response is tenant-east:accepted from H2. The wrong-tenant request does not return tenant-west:held. Compare [[spring/scope-versus-tenant-access|scope and ownership]] before reading the test code. The fixture includes X-Tenant spoofing in both allowed and denied cases."]),
    ("Extend the exercise", ["Add a token with a valid tenant_id syntax but a tenant unknown to the application. Decide whether the decoder, service or membership layer should reject it and explain why. The current fixture does not consult a tenant registry, so do not claim it already solves that case. For a write variant, assert the database rows after every denial. This exercise has no hosted judge; run the downloadable JUnit test locally and compare both response and state."])
], '''mvn -q -Dtest=JwtTenantBoundaryTest test''',
"JwtTenantBoundaryTest.trustedTenantClaimPassesTheMatchingServiceRule, JwtTenantBoundaryTest.wrongScopeIsForbiddenBeforeTheService, JwtTenantBoundaryTest.anotherTenantIsForbiddenAfterAuthentication and JwtTenantBoundaryTest.missingTenantClaimIsRejectedByTheDecoder",
"The four status outcomes are local MockMvc checks. This exercise does not grade remote submissions or simulate a real issuer. The JUnit run creates a small RSA key and H2 database per local context; no workload result follows from it.",
["Do not say every 403 came from the same rule.", "Do not use a header value to repair a missing token claim.", "Do not treat a valid token as permission for every tenant."],
["spring/jwt-web-context-test", "spring/scope-versus-tenant-access", "spring/tenant-claim-required"])

add("spring-exercises", "tenant-query-exercise", "Spring data exercise: repair a receipt query missing its tenant predicate",
"A receipt lookup keyed only by receipt ID can select another tenant's row when IDs are reused across tenants.", [
    ("Repair the query and prove it", ["Start with a conceptual lookup that selects by receipt_id alone. The fixture stores R-41 twice: tenant-east has accepted and tenant-west has held. Add tenant_id to the SQL predicate and bind the trusted tenant from authentication. Then assert that east returns accepted, west returns held only for an authorized west identity, and a third tenant returns no row. Do not rely on an ORDER BY to hide the duplicate ID.", "The source-kit [[spring/tenant-jdbc-predicate|tenant predicate lesson]] contains the repaired lookup. Its web test also denies an east token requesting the west route. Those are separate checks: a correct query does not make an untrusted tenant parameter trustworthy, and a correct service rule does not excuse an unscoped repository method."]),
    ("Add a write trace", ["Change the read to update state. Include both receipt_id and tenant_id in the WHERE clause, and check that the affected row count is exactly one. If zero, distinguish not-found, stale version and unauthorized access according to the API's disclosure policy. The current fixture checks a read predicate, not a database write or row-level security. Run the named JUnit test locally; this exercise has no hosted judge."])
], '''String sql = "select state from tenant_receipt "
    + "where receipt_id = ? and tenant_id = ?";
List<String> states = jdbc.queryForList(sql, String.class, "R-41", trustedTenant);''',
"JwtTenantBoundaryTest.scopedQueryExcludesRowsForOtherTenantValues",
"The test queries two H2 rows and an absent third tenant value. It does not exercise a production data set, index plan, write transaction or a user-to-tenant membership service. For a large table, inspect a composite index plan on the target engine.",
["Do not fetch by receipt ID alone and filter after the query.", "Do not bind an unverified URL tenant into the repaired SQL.", "Do not call a zero-row update success."],
["spring/tenant-jdbc-predicate", "spring/jwt-tenant-principal", "spring/tenant-auth-trace-exercise"])


def para(value: str) -> str:
    escaped = html.escape(value)
    return "<p>" + re.sub(r"\[\[([^|]+)\|([^\]]+)\]\]",
        lambda found: '<a href="/' + found[1] + '">' + found[2] + "</a>", escaped) + "</p>"


titles = {path: row["title"] for path, row in by_path.items()}
titles.update({spec["path"]: spec["title"] for spec in specs})
for spec in specs:
    path = spec["path"]
    assert path not in by_path, path
    assert all(target in titles for target in spec["links"]), (path, spec["links"])
    hub = next(row for row in rows if row["type"] == "subject" and row["subject"] == spec["subject"])
    body = para(spec["opening"])
    for heading, paragraphs in spec["sections"]:
        body += "<h2>" + html.escape(heading) + "</h2>" + "".join(para(value) for value in paragraphs)
    language = "bash" if path == "spring/tenant-auth-trace-exercise" else "java"
    body += '<h2>Checked source</h2><pre><code class="language-' + language + '">' + html.escape(spec["code"].strip(), quote=False) + "</code></pre>"
    body += "<h2>Verification boundary</h2>" + para(spec["proof"] + " runs in the downloadable Spring source kit. The excerpt is shortened; the kit contains the complete test.")
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
    "spring-security": ("Trusted tenant identity", ["spring/jwt-tenant-principal", "spring/scope-versus-tenant-access", "spring/tenant-claim-required", "spring/tenant-jdbc-predicate", "spring/tenant-header-spoof"]),
    "spring-testing": ("JWT web-context proof", ["spring/jwt-web-context-test"]),
    "spring-projects": ("Tenant-aware API migration", ["spring/tenant-receipt-api-security-plan"]),
    "spring-exercises": ("JWT and SQL boundary traces", ["spring/tenant-auth-trace-exercise", "spring/tenant-query-exercise"]),
}
for subject, (title, paths) in grouped.items():
    hub = next(row for row in rows if row["type"] == "subject" and row["subject"] == subject)
    hub["data"]["modules"].append({"title": title,
        "summary": "Trace both accepted and rejected tenant requests.", "lessons": paths})
    hub["updated_at"] = stamp
    if "<h2>Section lessons</h2>" in hub["body"]:
        links = "<ul>" + "".join('<li><a href="/' + path + '">' + html.escape(titles[path]) + "</a></li>"
            for module in hub["data"]["modules"] for path in module["lessons"]) + "</ul>"
        hub["body"] = re.sub(r"(<h2>Section lessons</h2>)[\s\S]*?(<h2>Continue learning</h2>)",
            lambda found: found[1] + links + found[2], hub["body"])

reverse = {
    "spring/jwt-resource-server": ["spring/jwt-tenant-principal", "spring/tenant-claim-required"],
    "spring/tenant-receipt-authorization": ["spring/scope-versus-tenant-access", "spring/tenant-jdbc-predicate"],
    "spring/tenant-receipt-write": ["spring/tenant-jdbc-predicate"],
    "spring/role-authority-prefix": ["spring/scope-versus-tenant-access"],
    "spring/testing-boundaries": ["spring/jwt-web-context-test"],
    "spring/receipt-api-project": ["spring/tenant-receipt-api-security-plan"],
    "java/jdbc-prepared": ["spring/tenant-jdbc-predicate"],
    "java/junit-tests": ["spring/jwt-web-context-test"],
}
for path, targets in reverse.items():
    assert path in by_path, path
    row = by_path[path]
    marker = "<h2>Continue with checked tenant security</h2>"
    row["body"] = row["body"].split(marker)[0] + marker + para("Continue with " + ", ".join(
        "[[" + target + "|" + titles[target] + "]]" for target in targets) + ".")
    row["updated_at"] = stamp

FILE.write_text(json.dumps(rows, ensure_ascii=False, indent=2) + "\n")
print(json.dumps({"added": [spec["path"] for spec in specs], "count": len(specs)}))
