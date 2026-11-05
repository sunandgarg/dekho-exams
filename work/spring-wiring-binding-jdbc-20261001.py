"""Publish checked Spring wiring, MVC binding and JDBC lessons."""

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
lessons = []


def add(section, slug, title, definition, sections, code, proof, cost, mistakes, links):
    lessons.append(locals().copy())


add("spring-core", "primary-and-qualifier-selection",
    "Spring @Primary and @Qualifier: default selection versus an explicit bean",
    "@Primary selects a default candidate for a single-valued dependency; @Qualifier narrows a particular injection point.",
    [
        ("Name both decisions", [
            "A dispatch planner needs the regional route for normal requests and a fallback route for an explicit recovery path. Mark one gateway as primary for the unqualified constructor parameter, then qualify the fallback parameter by bean name. The checked context resolves those two different objects without asking the planner to search the container.",
            "A qualifier is a selection constraint, not a fallback order. If the named bean is absent, context creation fails. Two primary beans of the same matching type are still ambiguous. [[spring/qualifiers|Qualifier basics]] and [[spring/constructor-injection|constructor injection]] explain the underlying candidate resolution."
        ]),
        ("Keep configuration changes observable", [
            "Renaming a bean can break a string qualifier even though the Java type still compiles. A small context test catches that failure before startup reaches traffic. Prefer a semantic custom qualifier when multiple implementations will evolve independently; a default should be an intentional application policy, not an accidental registration order."
        ]),
    ],
    '''@Bean @Primary DispatchGateway regionalGateway() { return () -> "regional"; }
@Bean DispatchGateway fallbackGateway() { return () -> "fallback"; }
@Bean DispatchPlanner dispatchPlanner(
        DispatchGateway defaultGateway,
        @Qualifier("fallbackGateway") DispatchGateway fallbackGateway) {
    return new DispatchPlanner(defaultGateway, fallbackGateway);
}''',
    "WiringAndBindingContractTest.primarySetsDefaultWhileQualifierSelectsAnExplicitGateway",
    "Bean selection happens during context assembly, not for every dispatch call. The test proves one local object graph; it does not prove a network gateway works or that a fallback endpoint is healthy. If the planner keeps singleton collaborators, they must still be safe for concurrent requests.",
    ["Do not use @Primary as a replacement for an explicit recovery dependency.", "Do not assume a qualifier will silently choose another bean when its target disappears.", "Do not infer thread safety from singleton bean selection."],
    ["spring/qualifiers", "spring/constructor-injection", "spring/auto-configuration", "spring/component-scan-vs-bean"])

add("spring-core", "configuration-proxy-bean-methods",
    "Spring @Configuration proxyBeanMethods: direct calls can create a second object",
    "An inter-bean call to a @Bean method is intercepted by a full @Configuration class, but acts like a plain Java call when proxyBeanMethods is false.",
    [
        ("Watch object identity", [
            "A delivery client calls retryPolicy() while it is being built. In the full configuration, Spring intercepts that call and supplies the managed singleton. With proxyBeanMethods=false, the call constructs another RetryPolicy, separate from the bean registered under that method. The test compares identity in both contexts.",
            "The safer configuration style is to declare RetryPolicy as a parameter of the deliveryClient bean method. Then the container resolves the dependency explicitly, and the method does not rely on proxy interception. This is especially useful when a configuration class is designed without method proxies. [[spring/component-scan-vs-bean|Bean construction]] and [[spring/application-context|context ownership]] provide the surrounding model."
        ]),
        ("Different from an AOP service proxy", [
            "This is configuration-method interception at bean creation time. [[spring/proxy-self-invocation|Transactional self-invocation]] concerns calls on a service instance at runtime. Both involve proxies, but fixing one does not fix the other."
        ]),
    ],
    '''@Configuration(proxyBeanMethods = false)
static class PlainPolicyConfig {
    @Bean RetryPolicy retryPolicy() { return new RetryPolicy(4); }
    @Bean DeliveryClient deliveryClient() {
        return new DeliveryClient(retryPolicy());
    }
}''',
    "WiringAndBindingContractTest.directBeanMethodCallChangesIdentityWithoutConfigurationProxy",
    "The extra direct call allocates a second policy object and may repeat factory side effects. The local context test measures identity only; it does not establish performance savings for disabling configuration proxies. If a factory opens a resource, a directly created copy also lacks the expected container lifecycle ownership.",
    ["Do not call a sibling @Bean method under proxyBeanMethods=false when the managed singleton is required.", "Do not assume a directly constructed object receives container lifecycle callbacks.", "Do not confuse configuration interception with service AOP interception."],
    ["spring/component-scan-vs-bean", "spring/application-context", "spring/proxy-self-invocation", "spring/constructor-injection"])

add("spring-core", "ordered-bean-list-injection",
    "Spring @Order on injected lists: execution order is not startup order",
    "@Order can sort multiple beans injected as a List of one interface, but it does not define when those singletons are created.",
    [
        ("Make pipeline order explicit", [
            "A receipt pipeline runs ownership checks before stock checks. The source fixture declares stock first in the configuration file, yet assigns ownership order 10 and stock order 20. The injected List is checked as ownership, then stock. Sorting by registration order would have produced the opposite result.",
            "A collection injection includes every matching bean unless the dependency is narrowed. Adding a new ReceiptCheck elsewhere can therefore change the pipeline. Assert the final list in a context test and keep each check's side effects visible. [[spring/primary-and-qualifier-selection|Single-bean selection]] solves a different problem."
        ]),
        ("Do not use order for initialization", [
            "An @Order annotation affects collection ordering and some extension-point ordering. It does not guarantee that one singleton starts before another. Use constructor dependencies or a documented lifecycle relationship when one component genuinely requires another to exist first. [[spring/lifecycle-cleanup|Lifecycle ownership]] covers shutdown as well."
        ]),
    ],
    '''@Bean @Order(20) ReceiptCheck stockCheck() { return () -> "stock"; }
@Bean @Order(10) ReceiptCheck ownershipCheck() { return () -> "ownership"; }
@Bean ReceiptPipeline receiptPipeline(List<ReceiptCheck> checks) {
    return new ReceiptPipeline(checks);
}''',
    "WiringAndBindingContractTest.orderedListInjectionDoesNotDependOnDeclarationOrder",
    "Sorting k matching beans costs at most O(k log k) during graph assembly in the general case; executing the pipeline costs the sum of its checks for each receipt. The test establishes local injection order, not thread safety or that checks are idempotent.",
    ["Do not assume source-code declaration order defines the injected pipeline.", "Do not treat @Order as a singleton startup dependency.", "Do not add a new matching bean without testing how it changes the list."],
    ["spring/primary-and-qualifier-selection", "spring/constructor-injection", "spring/lifecycle-cleanup", "spring/testing-boundaries"])

add("spring-web", "mvc-modelattribute-allowed-fields",
    "Spring MVC @ModelAttribute: allowlist fields before binding a form",
    "A @ModelAttribute can bind request parameters onto writable properties; an @InitBinder allowlist limits which setters receive client input.",
    [
        ("Do not bind a privilege flag", [
            "A dispatch preference form exposes region to the requester, while canApprove belongs to the authorization model. Without a binding rule, a matching request parameter could set that writable property. The controller's binder allows only region. The checked MockMvc request sends canApprove=true and receives WEST:false, proving this local form binding ignored that field.",
            "A dedicated input type with only permitted fields is preferable to exposing a domain object with administrative setters. An allowlist remains useful when a mutable form type is required. This lesson concerns @ModelAttribute parameter binding, not JSON @RequestBody deserialization; [[spring/rest-validation|request validation]] and [[spring/tenant-receipt-authorization|authorization]] are separate gates."
        ]),
        ("Keep rejected input handling deliberate", [
            "Ignoring an unexpected field can be acceptable for a browser form, but a strict API may reject it. Decide at the transport boundary and test that decision. A field allowlist does not limit raw request size, nested object depth or what an authenticated user may do after binding."
        ]),
    ],
    '''@InitBinder("dispatchPreference")
void allowedInput(WebDataBinder binder) {
    binder.setAllowedFields("region");
}

@PostMapping("/contract/dispatch-preference")
String update(@ModelAttribute DispatchPreference dispatchPreference) {
    return dispatchPreference.getRegion() + ":" + dispatchPreference.isCanApprove();
}''',
    "WiringAndBindingContractTest.formBindingIgnoresAnUnapprovedPrivilegeField",
    "Binding cost grows with submitted fields and conversion work; request-size limits belong earlier in the HTTP stack. Standalone MockMvc proves this controller and binder path only. It does not prove the production filter chain, authenticated identity or persistence constraints.",
    ["Do not expose a domain entity with writable privilege fields as an unrestricted form object.", "Do not mistake an allowlist for authorization.", "Do not assume this binder constrains JSON request-body deserialization."],
    ["spring/mvc-request-pipeline", "spring/rest-validation", "spring/tenant-receipt-authorization", "spring/mockmvc-standalone-scope"])

add("spring-data", "named-parameter-jdbc-list",
    "Spring NamedParameterJdbcTemplate: expand an ID list without dropping tenant scope",
    "NamedParameterJdbcTemplate binds a collection into an IN clause while other named parameters remain part of the SQL predicate.",
    [
        ("Keep the ownership predicate in SQL", [
            "The fixture asks for three receipt IDs, but one belongs to another tenant. The query binds both tenantId and receiptIds; the result contains only the two rows owned by TENANT-A. Filtering rows after a broader query would allow unauthorized records to leave the database boundary and can waste I/O.",
            "Collection expansion is for values, not arbitrary SQL identifiers. Never splice an untrusted comma-separated string into the SQL grammar. [[spring/tenant-jdbc-predicate|Tenant predicates]] explains why the ownership condition must appear in the database statement, and [[java/jdbc-prepared|prepared values]] covers the lower-level boundary."
        ]),
        ("Cap the list before building SQL", [
            "Each ID becomes a bound value. A huge list increases SQL size, parameter count and planning work; databases also differ in parameter limits. Define a maximum batch size and decide what an empty list means before executing, since an empty IN clause has no useful portable SQL shape."
        ]),
    ],
    '''var parameters = new MapSqlParameterSource()
        .addValue("tenantId", "TENANT-A")
        .addValue("receiptIds", List.of(47L, 82L, 91L));
var matches = named.queryForList(
        "select receipt_id from receipt_route where tenant_id = :tenantId " +
        "and receipt_id in (:receiptIds) order by receipt_id",
        parameters, Long.class);''',
    "JdbcParametersAndKeysContractTest.namedCollectionParameterKeepsTenantPredicateInTheQuery",
    "The fixture scans a tiny H2 table. Real cost depends on tenant cardinality, ID count, indexes and the database planner. The query returns O(k) IDs for k matches and holds the supplied list and result in memory; benchmark the target database before choosing a batch cap.",
    ["Do not remove tenant_id from the SQL and filter the returned rows in Java.", "Do not interpolate IDs or a tenant string directly into SQL.", "Do not pass an unbounded or empty ID collection without a defined policy."],
    ["spring/jdbc-template", "spring/tenant-jdbc-predicate", "java/jdbc-prepared", "spring/jdbc-pool-capacity"])

add("spring-data", "simple-jdbc-insert-generated-key",
    "Spring SimpleJdbcInsert: read the generated key after one insert",
    "SimpleJdbcInsert can execute an insert and return the key generated by the database for that row.",
    [
        ("Let the insert return the identity", [
            "The receipt table generates its ID. The fixture supplies tenant and amount, calls executeAndReturnKey, then queries that exact ID and checks the stored amount. Reading a separate maximum ID after insertion would race another writer and could associate the wrong receipt with the request.",
            "The key is an identity, not proof that a wider workflow committed. If a later step fails inside the same transaction, the row may roll back even though the database assigned an ID. [[spring/transactions|Transaction ownership]] and [[spring/outbox-atomic-write|the outbox boundary]] cover what must commit together."
        ]),
        ("Declare columns deliberately", [
            "The insert builder names tenant_id and amount_cents explicitly. Depending on database metadata to decide every writable column can make a schema addition change the insert unexpectedly. Generated-key retrieval also depends on driver and database support; run the integration test against the actual engine before relying on it in a release."
        ]),
    ],
    '''var insert = new SimpleJdbcInsert(source)
        .withTableName("receipt_entry")
        .usingColumns("tenant_id", "amount_cents")
        .usingGeneratedKeyColumns("id");
Number generatedId = insert.executeAndReturnKey(
        Map.of("tenant_id", "TENANT-A", "amount_cents", 4725L));''',
    "JdbcParametersAndKeysContractTest.generatedKeyIsReadFromTheDatabaseInsertResult",
    "One insert and one verification query run in the fixture. Database-generated identity allocation and metadata inspection vary by driver; this H2 test does not prove another database's generated-key behavior. Keep a configured insert object reusable rather than rebuilding metadata on every request.",
    ["Do not use SELECT MAX(id) to discover the row just inserted.", "Do not treat a generated ID as proof that a transaction committed.", "Do not assume H2 key retrieval establishes target-database behavior."],
    ["spring/jdbc-template", "spring/transactions", "spring/outbox-atomic-write", "spring/flyway-versioned-receipts"])


def paragraph(value):
    escaped = html.escape(value)
    return "<p>" + re.sub(r"\[\[([^|]+)\|([^\]]+)\]\]",
        lambda match: '<a href="/' + match[1] + '">' + match[2] + "</a>", escaped) + "</p>"


titles = {path: row["title"] for path, row in by.items()}
titles.update({"spring/" + item["slug"]: item["title"] for item in lessons})
section_paths = {"spring-core": "spring/spring-core", "spring-web": "spring/web-apis", "spring-data": "spring/data-transactions"}
grouped = {section: [] for section in section_paths}
for index, item in enumerate(lessons):
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
        tags=["spring", "spring-boot", item["slug"]], sort_order=2400 + index,
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
        "title": "Checked wiring and boundary contracts" if section == "spring-core" else
                 "Form binding boundary" if section == "spring-web" else "JDBC parameters and generated identity",
        "summary": "Run the source-kit test, then inspect the failure and ownership rule.",
        "lessons": paths,
    })
    hub["body"] += "<h2>New checked lessons</h2><ul>" + "".join(
        '<li><a href="/' + path + '">' + html.escape(titles[path]) + "</a></li>" for path in paths) + "</ul>"
    hub["updated_at"] = stamp

reverse = {
    "spring/qualifiers": ["spring/primary-and-qualifier-selection"],
    "spring/component-scan-vs-bean": ["spring/configuration-proxy-bean-methods", "spring/ordered-bean-list-injection"],
    "spring/mvc-request-pipeline": ["spring/mvc-modelattribute-allowed-fields"],
    "spring/jdbc-template": ["spring/named-parameter-jdbc-list", "spring/simple-jdbc-insert-generated-key"],
    "spring/tenant-jdbc-predicate": ["spring/named-parameter-jdbc-list"],
    "spring/transactions": ["spring/simple-jdbc-insert-generated-key"],
}
for path, targets in reverse.items():
    row = by[path]
    row["body"] += "<h2>Checked follow-up</h2>" + paragraph("Continue with " + ", ".join(
        "[[" + target + "|" + titles[target] + "]]" for target in targets) + ".")
    row["updated_at"] = stamp

FILE.write_text(json.dumps(rows, ensure_ascii=False, indent=2) + "\n")
print("Added", len(lessons), "Spring tutorials; linked from", len(reverse), "existing lessons")
