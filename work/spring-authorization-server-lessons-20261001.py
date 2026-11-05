"""Add original Spring Authorization Server lessons to the Spring library."""

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
        r"\[\[([^|]+)\|([^\]]+)\]\]",
        lambda match: '<a href="/' + match[1] + '">' + match[2] + "</a>",
        escaped,
    )


lessons = [
    dict(
        slug="authorization-server-three-roles",
        title="Spring Authorization Server, OAuth2 client and resource server: three trust roles",
        summary="An authorization server issues tokens, a client obtains them, and a resource server validates them before authorizing an API request.",
        blocks=[
            ("Separate the trust roles", "A parcel dashboard signs in an operator through an authorization server. The dashboard is an OAuth2 client; the parcel API is a resource server. The issuer authenticates the operator, records the client and grant, and signs or otherwise issues a token. The API verifies issuer, signature, expiry and intended audience before it evaluates scopes. [[spring/jwt-resource-server|Resource-server validation]] does not issue tokens, and [[spring/oauth2-client-token-lifecycle|client token acquisition]] does not make the client an issuer."),
            ("Keep issuer identity stable", "The API must trust the configured issuer rather than any token with a parseable JWT shape. Keep one externally stable issuer identifier across replicas. Rotate signing keys without replacing every active key at once, and expose verification keys through the issuer's configured metadata. A fresh key generated only in process memory on every restart can invalidate tokens that were already issued. [[spring/jwt-issuer-audience-boundary|Audience checks]] stop a valid token for another API from being accepted here."),
            ("Test the wrong recipient", "Issue a token for parcel-read, then send it to the billing API. It must fail if that API expects a different audience even when the signature and issuer are valid. Also test an expired token and a token signed by an untrusted issuer. The security-filter configuration below is a starting sketch; it does not supply registered clients, durable authorization state or stable signing keys."),
        ],
        code='@Bean\nSecurityFilterChain issuerChain(HttpSecurity http) throws Exception {\n    http.oauth2AuthorizationServer(server -> {\n        http.securityMatcher(server.getEndpointsMatcher());\n        server.oidc(Customizer.withDefaults());\n    }).authorizeHttpRequests(auth -> auth.anyRequest().authenticated());\n    return http.build();\n}',
        cost="Token validation can be local when verification keys are cached, but key lookup and rotation still need controlled refresh. Issuing tokens adds persistent client and authorization records when revocation or refresh is required.",
        mistakes=["Do not treat a resource server as an authorization server because both use Spring Security.", "Do not accept a token merely because it has a valid signature; check issuer and audience.", "Do not generate a new production signing key at every startup and expect old tokens to remain valid."],
        related=["spring/jwt-resource-server", "spring/oauth2-client-token-lifecycle", "spring/jwt-issuer-audience-boundary", "spring/authorization-server-durable-state"],
    ),
    dict(
        slug="authorization-server-durable-state",
        title="Spring Authorization Server JDBC state: clients, grants and consent across restarts",
        summary="Registered clients, authorizations and consent need explicit storage decisions; tutorial in-memory services cannot carry production state across restarts.",
        blocks=[
            ("Persist each state category", "A registered client defines permitted redirect locations, authentication methods, grants and token settings. An authorization record holds issued grant state. Consent records the user's approval when that step is required. Spring Authorization Server can use JDBC repositories and services for these categories, but each needs its schema and migration. If only clients are persistent, a restart can still lose authorizations and consent. [[spring/authorization-server-three-roles|The issuer role]] therefore includes storage, not just a filter chain."),
            ("Make grant changes atomic", "Do not write client metadata by hand into the authorization tables while a token request is running. Use the repository contract and a database migration that matches the selected Spring Security release. Protect credentials, encrypt sensitive database backups, and set retention for expired authorizations. When several issuer replicas share one database, verify their issuer, signing-key and client configuration agree. [[spring/transactions|Transaction scope]] matters for any surrounding business write."),
            ("Restart while a grant is live", "Register a confidential parcel-audit client, complete one grant, restart every issuer instance, then use the permitted follow-up flow. Also revoke or expire the grant and verify it is rejected. This code is a wiring sketch: it assumes the JDBC tables, compatible dependencies and shared database are already present. A database-backed service is not, by itself, proof that a particular grant survives or is revoked correctly."),
        ],
        code='@Bean\nRegisteredClientRepository registeredClients(JdbcOperations jdbc) {\n    return new JdbcRegisteredClientRepository(jdbc);\n}\n\n@Bean\nOAuth2AuthorizationService authorizations(\n        JdbcOperations jdbc, RegisteredClientRepository clients) {\n    return new JdbcOAuth2AuthorizationService(jdbc, clients);\n}\n\n@Bean\nOAuth2AuthorizationConsentService consents(\n        JdbcOperations jdbc, RegisteredClientRepository clients) {\n    return new JdbcOAuth2AuthorizationConsentService(jdbc, clients);\n}',
        cost="JDBC-backed grants add writes, indexes, cleanup and recovery operations. Keep expiration queries and retention bounded; a token service under load can make the authorization tables a hot path.",
        mistakes=["Do not persist RegisteredClientRepository while leaving authorization state in a process-local default unintentionally.", "Do not rely on a schema copied from another Spring Security version without migration review.", "Do not call a restart test complete until existing grants and revocation behavior are checked."],
        related=["spring/authorization-server-three-roles", "spring/authorization-server-grant-boundaries", "spring/oauth2-login-session", "spring/transactions"],
    ),
    dict(
        slug="authorization-server-grant-boundaries",
        title="Spring Authorization Server grants: PKCE for public clients, credentials for services",
        summary="A browser client cannot keep a secret; PKCE protects its authorization-code exchange, while client credentials represent a service rather than a signed-in user.",
        blocks=[
            ("Start with client capability", "The parcel dashboard runs in a browser, so a bundled client secret would be visible to its users. Register it as a public client with an exact redirect location, authorization-code grant and required PKCE proof. A backend relay with a protected secret can be a confidential client and request client-credentials tokens for service-to-service work. Those tokens do not carry an operator session. [[spring/oauth2-login-session|Browser login]] and [[spring/oauth2-client-token-lifecycle|service-token caching]] solve different problems."),
            ("Check the grant against the API", "A resource server should authorize a client-credentials token as a service identity, not manufacture a user from its subject. Keep scopes narrow, validate audience, and decide whether a human action needs a delegated user token instead. An exact redirect allowlist is part of the authorization-code boundary; a loose wildcard can hand a code to an unintended page. PKCE binds the code exchange to the client that started it, but does not replace redirect validation or API authorization."),
            ("Try the attack-shaped cases", "Reject a code exchange with the wrong verifier, a redirect location absent from registration, and a browser request using a service token for an operator-only endpoint. The registration sketch below illustrates a public client; supply the redirect location from reviewed configuration, and run protocol tests against the selected Spring Security version before publishing the client."),
        ],
        code='RegisteredClient browserClient(String reviewedRedirect) {\n    return RegisteredClient.withId(UUID.randomUUID().toString())\n        .clientId("parcel-dashboard")\n        .clientAuthenticationMethod(ClientAuthenticationMethod.NONE)\n        .authorizationGrantType(AuthorizationGrantType.AUTHORIZATION_CODE)\n        .redirectUri(reviewedRedirect)\n        .scope("parcel.read")\n        .clientSettings(ClientSettings.builder().requireProofKey(true).build())\n        .build();\n}',
        cost="PKCE adds a verifier and challenge per authorization attempt, with negligible compute cost. Server-side clients must store and rotate credentials; public clients cannot solve secret storage by hiding a value in JavaScript.",
        mistakes=["Do not ship a confidential-client secret in browser code.", "Do not treat a client-credentials token as proof of a human user's identity.", "Do not use redirect wildcards or skip the verifier failure test."],
        related=["spring/authorization-server-durable-state", "spring/oauth2-login-session", "spring/oauth2-client-token-lifecycle", "spring/jwt-issuer-audience-boundary"],
    ),
]

titles = {path: row["title"] for path, row in by_path.items()}
titles.update({"spring/" + item["slug"]: item["title"] for item in lessons})
for index, item in enumerate(lessons):
    path = "spring/" + item["slug"]
    assert path not in by_path, path
    assert all(target in titles for target in item["related"]), path
    body = "<p>" + prose(item["summary"]) + "</p>"
    for heading, content in item["blocks"]:
        body += "<h2>" + html.escape(heading) + "</h2><p>" + prose(content) + "</p>"
    body += '<h2>Implementation sketch</h2><pre><code class="language-java">' + html.escape(item["code"], quote=False) + "</code></pre>"
    body += "<h2>Cost and verification</h2><p>" + prose(item["cost"]) + "</p>"
    body += "<h3>Common Mistakes</h3><ul>" + "".join("<li>" + prose(mistake) + "</li>" for mistake in item["mistakes"]) + "</ul>"
    body += "<h2>Read next</h2><p>" + ", ".join('<a href="/' + target + '">' + html.escape(titles[target]) + "</a>" for target in item["related"]) + ".</p>"
    row = copy.deepcopy(by_path["spring/component-scan-vs-bean"])
    row.update(
        id=str(uuid.uuid5(uuid.NAMESPACE_URL, "https://aitrove.in/" + path)),
        path=path,
        title=item["title"],
        summary=item["summary"],
        body=body,
        subject="spring-security",
        tags=["spring", "spring-security", "oauth2", item["slug"]],
        sort_order=4700 + index,
        published_at=stamp,
        created_at=stamp,
        updated_at=stamp,
    )
    row["data"] = {
        "subject_root": "spring/spring-boot",
        "section_path": "spring/security",
        "kind": "tutorial",
        "content_format": "html",
        "seo_ready": True,
        "reading_minutes": max(4, round(len(re.sub(r"<[^>]+>", " ", body).split()) / 150)),
        "author_path": "authors/aitrove-editorial",
        "framework_version": "Spring Boot 4 / Spring Security 7",
        "java_version": "21 or later",
        "verification_suite": "Editorial API contract review; implementation sketch not compiled",
        "related": [{"path": target, "title": titles[target]} for target in item["related"]],
    }
    rows.append(row)
    by_path[path] = row

paths = ["spring/" + item["slug"] for item in lessons]
security = by_path["spring/security"]
security["data"]["modules"].append({
    "title": "Run an OAuth2 authorization server",
    "summary": "Separate issuer trust, persistent grant state and client grant choices.",
    "lessons": paths,
})
security["body"] += "<h2>Run an OAuth2 authorization server</h2><ul>" + "".join(
    '<li><a href="/' + path + '">' + html.escape(titles[path]) + "</a></li>" for path in paths
) + "</ul>"
security["updated_at"] = stamp
parent = by_path["spring/spring-boot"]
parent["body"] += "<h2>OAuth2 authorization server</h2><ul>" + "".join(
    '<li><a href="/' + path + '">' + html.escape(titles[path]) + "</a></li>" for path in paths
) + "</ul>"
parent["updated_at"] = stamp
for source, target in [
    ("spring/jwt-resource-server", paths[0]),
    ("spring/oauth2-client-token-lifecycle", paths[2]),
    ("spring/oauth2-login-session", paths[2]),
]:
    row = by_path[source]
    row["body"] += '<h2>Related boundary</h2><p><a href="/' + target + '">' + html.escape(titles[target]) + "</a></p>"
    row["updated_at"] = stamp

FIXTURE.write_text(json.dumps(rows, ensure_ascii=False, indent=2) + "\n")
print("Added", len(lessons), "authorization-server articles")
