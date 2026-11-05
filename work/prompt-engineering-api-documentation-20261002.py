"""Add original API-documentation prompt lessons, project, and quiz."""

import copy
import datetime
import html
import json
import uuid
from pathlib import Path

root = Path(__file__).resolve().parents[1]
fixture = root / "src/data/fixtures.json"
entries = json.loads(fixture.read_text())
lookup = {entry["path"]: entry for entry in entries}
stamp = datetime.datetime.now(datetime.UTC).isoformat()
subject_root = "prompt-engineering/prompt-engineering"
applications = "prompt-engineering/applications"
production = "prompt-engineering/production"
projects = "prompt-engineering/projects"
quizzes = "prompt-engineering/quizzes"
project_path = "prompt-engineering/shipment-status-api-docs-review-project"
quiz_path = "quizzes/prompt-engineering-api-documentation"

specs = [
    {
        "slug": "api-docs-code-schema-and-version-boundary",
        "title": "API documentation prompts: bind prose to a versioned contract",
        "summary": "Read the endpoint, schema, tests, and version before drafting an API page.",
        "definition": "An API documentation prompt should receive a bounded evidence packet: the relevant operation contract, implementation behavior, integration tests, and version policy. Identify which artifact defines the public contract when code and schema disagree. The model may draft an explanation, but it must not invent a parameter, status code, response field, or permission from surrounding conventions. State the exact endpoint version and change under review. Ask for a discrepancy ledger before prose if a test and specification differ. Separate public behavior from internal class names; readers need the contract they can call, not an unreviewed dump of source code.",
        "case": "A fictional Shipment Status API adds the status held to version two of its shipment response. The endpoint is GET /v2/shipments/{shipmentId}. The approved operation contract allows queued, in_transit, held, and delivered. One old guide lists only three values, while an integration test has a held fixture. The prompt first records that drift and asks the API owner to confirm that held is released in v2. It does not infer that a new hold_reason field exists just because the implementation stores one internally. The public page will be drafted only against the confirmed contract and test fixture.",
        "sample": "Scope: GET /v2/shipments/{shipmentId}; version 2.\nPacket: approved operation contract, handler behavior, integration tests.\nChange: held joins queued, in_transit, delivered.\nConflict: old guide lacks held -> record drift and confirm release.\nUnknown: internal hold_reason is not automatically public.",
        "cost": "Reading E endpoint artifacts and T relevant tests is O(E+T) inspection work. Restricting the prompt to the changed operation reduces token cost and prevents an unrelated endpoint from contaminating the example. A discrepancy ledger takes extra review but is cheaper than publishing an invented field across several pages. A generated page must be checked against the authoritative contract after editing; a good opening paragraph does not validate every request and response detail.",
        "mistakes": ["Do not document an internal field as public without contract evidence.", "Do not copy an older guide as the only truth when its enum is stale.", "Do not mix behavior from different API versions."],
        "related": ["prompt-engineering/code-change-acceptance-contract", "prompt-engineering/schema-migration-prompt-review", "prompt-engineering/evidence-id-traceability"],
        "section": applications,
    },
    {
        "slug": "api-operation-request-response-error-matrix",
        "title": "API prompts: document the full operation matrix",
        "summary": "Specify inputs, success and failure responses, permissions, and retry behavior.",
        "definition": "An API operation page should describe how a caller forms a request and interprets every documented outcome. The prompt must enumerate method, path parameters, authentication scope, successful response shape, material error codes, and retry guidance supported by the service contract. A happy-path body alone leaves integrators to guess what happens when an ID is missing or access is denied. The prompt should label fields that are required, optional, or conditionally present and keep null distinct from absent. If the source packet does not establish an error code or retry policy, mark it for owner review instead of filling the gap with a familiar convention.",
        "case": "For GET /v2/shipments/{shipmentId}, the approved contract requires shipmentId and a reader permission. The successful response has shipment_id and status; the held fixture uses SH-4721 and status held. A not-found result is documented as 404 with a structured code. The security test proves a caller without the reader permission receives 403. The prompt leaves a timeout retry rule open until the API owner confirms it. It does not show a 200 response with status delivered for a missing ID, and it does not treat 403 as evidence that the shipment does not exist.",
        "sample": "GET /v2/shipments/{shipmentId}\nRequired path: shipmentId; permission: shipment:read.\n200: shipment_id, status; held fixture SH-4721.\n403: caller lacks read permission.\n404: shipment ID not found under approved visibility rule.\nRetry on timeout: unresolved until owner confirms policy.",
        "cost": "For R response classes and F documented fields, a complete review is O(R+F) contract checks per operation. Authentication and error tests often cost more to inspect than the success fixture, but they prevent misleading integration instructions. A generated error matrix should be checked against actual tests or approved specification, not merely against another generated page. Omitting unknown retry behavior can be safer than prescribing retries that amplify an outage or duplicate a side effect.",
        "mistakes": ["Do not infer 404 versus 403 behavior without checking visibility rules.", "Do not call an optional field required because it appears in one fixture.", "Do not invent retry advice from a status code alone."],
        "related": ["prompt-engineering/schema-and-abstention", "prompt-engineering/request-risk-routing-contract", "prompt-engineering/tool-call-authorization-contract"],
        "section": applications,
    },
    {
        "slug": "api-example-fixture-and-secret-safety-gate",
        "title": "API examples: validate payloads and strip credentials",
        "summary": "Use deterministic fixtures, run examples, and keep private values out of docs.",
        "definition": "A documentation example should be a verified contract case, not a plausible-looking JSON object. The prompt must identify the fixture or test that supplies each field, use fictional identifiers, and omit live credentials and personal data. Validate the example against the released schema, then run a request or contract test in a safe environment where practical. Check that printed output agrees with the status description and version. For a request requiring authorization, use a clear placeholder rather than a valid token. The review should catch accidental copy of production IDs, access keys, internal hostnames, and sample values that imply a field exists when it does not.",
        "case": "The held-shipment page includes SH-4721 as a fictional ID. Its 200 response shows shipment_id and status held, matching the approved fixture. An earlier draft inserted hold_reason and a long authorization token copied from a debug log; both are removed. The contract does not expose hold_reason, and the token is not safe to publish. The reviewer runs the example against a local fixture and confirms the JSON parses and the two public fields have the right types. A 403 example uses a fabricated error code already present in the permission test, not a copied customer response.",
        "sample": "Request ID: SH-4721 (fictional fixture).\n200 JSON: {\"shipment_id\":\"SH-4721\",\"status\":\"held\"}\nAuthorization: <reader-token> placeholder only.\nReject: internal hold_reason, live token, production identifier.\nCheck: JSON parse, released schema, fixture output, version.",
        "cost": "Parsing an example of B bytes is O(B) and schema validation depends on the schema depth and field count; a single local fixture run is usually cheap compared with a published integration error. Secret scanning adds a pass over the draft and generated files. The prompt should not claim that one valid example proves the whole operation correct; negative cases and permission boundaries need separate tests. Keep examples few and distinct so each teaches a meaningful branch rather than repeating the success body with new IDs.",
        "mistakes": ["Do not publish a real token as a convenient example.", "Do not add a field because it appears in an internal log.", "Do not trust syntax-only JSON validation as proof of contract alignment."],
        "related": ["prompt-engineering/sensitive-output-redaction-gate", "prompt-engineering/output-sink-validation", "prompt-engineering/regression-test-oracle-contract"],
        "section": applications,
    },
    {
        "slug": "api-change-compatibility-and-migration-note",
        "title": "API changes: explain client impact and migration",
        "summary": "Classify compatibility from client behavior, not only schema shape.",
        "definition": "An API change prompt should describe the before and after contract, supported versions, affected clients, rollout timing, and test evidence. Adding an enum value can look additive in a schema while breaking clients with exhaustive status handling. The prompt should ask how callers treat unknown values and whether a versioned migration note is required. Record the old behavior, new behavior, fallback for clients that cannot update immediately, and owner of each compatibility claim. Do not announce a deprecation or date unless the release policy approves it. A migration note is a change guide, not a substitute for the current operation page.",
        "case": "Shipment Status v2 adds held. One client maps every known status to an icon with no default branch; held causes that client to fail despite being an added enum value. Another client displays unknown statuses as 'Status unavailable' and continues. The prompt documents both outcomes and asks the API owner whether to gate held behind a version boundary or coordinate the client release. The draft migration note tells callers to handle unknown status values and adds a held fixture to contract tests. It does not claim that every client is safe because the response still uses a string.",
        "sample": "Before: queued | in_transit | delivered.\nAfter: queued | in_transit | held | delivered.\nClient A: exhaustive mapping -> fails on held.\nClient B: unknown fallback -> remains usable.\nGate: choose version/release plan; add held contract fixture.\nDo not invent deprecation date or universal compatibility.",
        "cost": "With C known client integrations and S changed status values, targeted compatibility review is O(CS) behavior checks. Unknown external clients add uncertainty; publish a conservative migration note and monitoring plan rather than claiming total coverage. A coordinated release may slow delivery, but it avoids turning an apparently harmless schema addition into a client outage. Keep version and behavior claims tied to the actual deployment state; a merged contract change is not proof that every environment serves held.",
        "mistakes": ["Do not equate additive schema shape with safe client behavior.", "Do not promise a retirement date the release plan has not approved.", "Do not report held as live in every environment from a merged test alone."],
        "related": ["prompt-engineering/model-migration-contract", "prompt-engineering/schema-migration-prompt-review", "prompt-engineering/release-regression-gate"],
        "section": applications,
    },
    {
        "slug": "api-docs-link-drift-and-release-evidence",
        "title": "API docs release: test links, examples, and live version",
        "summary": "Reconcile published pages with the deployed contract and preserve a review trail.",
        "definition": "An API documentation release prompt should name the target version and environment, affected pages, internal links, example fixtures, contract checks, owner approval, and rollback path. A docs build can succeed while pointing readers to a stale enum page or a newer endpoint that is not deployed. Validate internal links and navigation, run sample payload checks, and compare the published claim with a deployment receipt or approved release record. If docs publish before the service, label the future behavior clearly or defer the page. Keep a change ledger so a later release can tell which examples and migration notes need revision. Do not let the model itself declare production behavior from code that has not shipped.",
        "case": "The Shipment Status v2 draft links to a shared status-values page that still lists three values. Link checking reports a valid destination, but a content check detects the stale enum. The editorial owner updates the values page and reruns its link and example checks. The v2 operation page, held fixture, and migration note remain in review until the deployment record confirms held is served. A staged environment may serve held earlier; the page must label that environment instead of implying public availability. After release, a client report that held is mishandled opens a correction to the migration guidance and a tracked follow-up.",
        "sample": "Check pages: operation, status values, migration note.\nCheck links: targets resolve and describe the same version.\nCheck examples: parse, schema, fixture, secret scan.\nCheck release: deployment receipt confirms held in target environment.\nIf mismatch: hold or label staged behavior; record correction owner.",
        "cost": "For L links and X examples, basic verification is O(L+X) checks, plus contract tests and a deployment-state lookup. Automated link checks catch missing targets but not semantically stale destinations, so reviewers inspect version-sensitive pages. Publishing a correction costs less when the change ledger identifies affected examples and status lists. A rollback of docs must not erase a truthful migration warning for clients already seeing held; the owner decides whether to patch text, change routing, or coordinate a service rollback.",
        "mistakes": ["Do not treat a resolving link as proof that its target is current.", "Do not publish a future endpoint as live without a deployment receipt.", "Do not fix one operation page while leaving a shared enum page stale."],
        "related": ["prompt-engineering/prompt-release-review-packet", "prompt-engineering/evidence-reference-checker", "prompt-engineering/prompt-version-rollout"],
        "section": production,
    },
]

paths = ["prompt-engineering/" + spec["slug"] for spec in specs]
assert not set(paths + [project_path, quiz_path]).intersection(lookup)
titles = {entry["path"]: entry["title"] for entry in entries}
titles.update({path: spec["title"] for path, spec in zip(paths, specs)})
titles[project_path] = "Project: review Shipment Status API documentation"
titles[quiz_path] = "API-documentation prompt decisions"


def link(path):
    assert path in titles, path
    return f'<a href="/{html.escape(path)}">{html.escape(titles[path])}</a>'


def links(selected):
    return "<ul>" + "".join(f"<li>{link(path)}</li>" for path in dict.fromkeys(selected)) + "</ul>"


def related(selected):
    return [{"path": path, "title": titles[path]} for path in dict.fromkeys(selected)]


def article(path, title, summary, body, section, order, connections, kind="tutorial"):
    entry = copy.deepcopy(lookup["prompt-engineering/evaluation-slice-design"])
    subject = "prompt-engineering-applications" if section == applications else "prompt-engineering-production" if section == production else "prompt-engineering-project"
    entry.update(id=str(uuid.uuid5(uuid.NAMESPACE_URL, "aitrove:" + path)), path=path,
                 title=title, summary=summary, body=body, subject=subject,
                 difficulty="Advanced", tags=["prompt engineering", "api documentation"],
                 sort_order=30100 + order, status="published", published_at=stamp,
                 created_at=stamp, updated_at=stamp)
    entry["data"].update(kind=kind, reading_minutes=11 if kind == "tutorial" else 19,
                         author_path="authors/aitrove-editorial", subject_root=subject_root,
                         section_path=section, content_format="html", seo_ready=True,
                         related=related(connections))
    return entry


new_rows = []
for index, (path, spec) in enumerate(zip(paths, specs)):
    connections = [spec["section"], subject_root] + spec["related"] + [peer for peer in paths if peer != path] + [project_path, quiz_path]
    body = ("<p>" + html.escape(spec["definition"]) + "</p>"
            + "<h2>Operational case</h2><p>" + html.escape(spec["case"]) + "</p>"
            + '<pre><code class="language-text">' + html.escape(spec["sample"], quote=False) + "</code></pre>"
            + "<h2>Performance and operating cost</h2><p>" + html.escape(spec["cost"]) + "</p>"
            + "<h3>Common Mistakes</h3><ul>" + "".join("<li>" + html.escape(mistake) + "</li>" for mistake in spec["mistakes"]) + "</ul>"
            + "<h2>Connected lessons</h2>" + links(connections))
    new_rows.append(article(path, spec["title"], spec["summary"], body, spec["section"], index * 10, connections))

project_connections = paths + ["prompt-engineering/schema-migration-prompt-review", "prompt-engineering/sensitive-output-redaction-gate", "prompt-engineering/prompt-release-review-packet", quiz_path]
project_body = (
    "<p>Update the fictional Shipment Status API documentation for GET /v2/shipments/{shipmentId}. The confirmed version-two contract adds held to queued, in_transit, and delivered. The held fixture is SH-4721. The public success response includes shipment_id and status; an internal hold_reason field is not in the public contract. The deliverables are an operation page, checked example, compatibility note, shared status-values update, and release packet. The work remains a draft until the API owner confirms target-environment deployment.</p>"
    "<h2>Freeze the contract and examples</h2><p>Read the approved operation contract, implementation behavior, integration tests, and version policy. Record that the old values guide is stale. Document required shipmentId and shipment:read permission. The approved tests show 200 for an authorized found shipment, 403 without permission, and 404 for a missing ID under the visibility rule. Leave timeout retry guidance open until the owner confirms it. The held example uses a fictional ID and only public fields. Remove a copied live token and internal hold_reason. Parse the JSON, check schema alignment, and run the fixture test.</p>"
    "<h2>Review client impact and publication state</h2><p>A client with exhaustive status handling fails on held, while a client with an unknown-status fallback remains usable. The change therefore needs a migration note and coordinated release decision even though the response field remains a string. Update the shared values page and inspect links for semantic freshness, not only destination existence. Confirm that held is deployed in the target environment before the public page claims it is live. Keep the operation page, tests, migration note, deployment receipt, and editorial approval together for review.</p>"
    '<pre><code class="language-text">GET /v2/shipments/{shipmentId}; permission shipment:read.\n200 fixture: {"shipment_id":"SH-4721","status":"held"}.\n403: missing permission; 404: missing visible ID.\nNo public hold_reason; no real token in examples.\nClient check: exhaustive mapping may fail on new held value.\nRelease: update values page, test links/examples, confirm deployment.</code></pre>'
    "<h2>Performance and operating cost</h2><p>Reviewing E affected endpoints, C client integrations, L links, and X examples needs O(E+C+L+X) targeted checks before release. JSON parsing of an example is O(B) for B bytes; that syntax check does not prove authorization or compatibility. Keeping the evidence packet scoped to one operation reduces model context cost and review noise. A deployment receipt answers whether the service serves held; a merged code change and passing docs build do not. The editorial owner may hold publication when the schema, test, and running service disagree.</p>"
    "<h3>Common Mistakes</h3><ul><li>Do not publish an internal field or live credential.</li><li>Do not call an added enum value universally compatible.</li><li>Do not label staged behavior public before deployment is confirmed.</li></ul>"
    "<h2>Connected lessons</h2>" + links(project_connections))
new_rows.append(article(project_path, titles[project_path], "Align one versioned shipment endpoint, examples, migration note, and release state.", project_body, projects, 60, project_connections, kind="project"))

questions = [
    ("What should an API documentation prompt bind to a page?", "A versioned contract, implementation, and relevant tests", "Only an old guide", "An internal class name", "The public page needs a bounded evidence packet."),
    ("Which new status is confirmed for Shipment Status v2?", "held", "returned", "unknown", "The approved contract adds held."),
    ("Is internal hold_reason automatically a public response field?", "No; it needs public contract evidence", "Yes, because code stores it", "Yes, if an example looks useful", "Internal storage is not the API contract."),
    ("What does 403 indicate in the approved test?", "The caller lacks shipment:read permission", "The shipment is necessarily missing", "The JSON cannot parse", "Permission behavior differs from not found."),
    ("What should happen to unspecified timeout retry guidance?", "Hold it for API-owner confirmation", "Invent a standard retry rule", "Copy one from another endpoint", "Retry policy must be supported by the contract."),
    ("What belongs in the held success example?", "Fictional shipment ID and confirmed public fields", "A live token", "An internal hold_reason field", "Examples should align with a fixture and protect secrets."),
    ("Does valid JSON prove a response example matches the API?", "No; validate against schema and fixture", "Yes, always", "Only if it uses two fields", "Syntax is a weaker check than contract alignment."),
    ("Why might adding held break a client?", "The client may use exhaustive status handling", "All additions are harmless", "The endpoint path disappeared", "Behavioral compatibility depends on callers."),
    ("What should a migration note explain?", "Before and after behavior and client handling", "Only the new status spelling", "A guessed retirement date", "Clients need a change path and scope."),
    ("A link resolves to an old three-value guide. Is that enough?", "No; the destination is semantically stale", "Yes, resolution proves accuracy", "Yes, if the URL is short", "Link health and content freshness are separate."),
    ("What proves held is served in the target environment?", "An approved deployment record or verified runtime check", "A merged code branch", "A passing docs build", "Release state needs its own evidence."),
    ("What should publication do when contract and deployed service disagree?", "Hold or clearly label the environment until reconciled", "Publish as live anyway", "Delete the migration note", "Docs must match the service readers can call."),
]
quiz_entry = copy.deepcopy(lookup["quizzes/prompt-engineering-multimodal-evidence"])
quiz_entry.update(id=str(uuid.uuid5(uuid.NAMESPACE_URL, "aitrove:" + quiz_path)),
                  path=quiz_path, title=titles[quiz_path],
                  summary="Test versioned contracts, response matrices, examples, compatibility, and release drift.",
                  body="<p>Choose the API-documentation decision supported by the confirmed contract.</p><h2>Lessons</h2>" + links(paths) + "<h2>Project and sections</h2>" + links([project_path, applications, production, quizzes]),
                  sort_order=30170, status="published", published_at=stamp,
                  created_at=stamp, updated_at=stamp)
quiz_entry["data"].update(subject_root=subject_root, section_path=quizzes,
                          content_format="html", author_path="authors/aitrove-editorial",
                          seo_ready=True, duration_minutes=12,
                          related=related(paths + [project_path]),
                          questions=[{"prompt": prompt,
                                      "options": ([correct, wrong_a, wrong_b][index % 3:] + [correct, wrong_a, wrong_b][:index % 3]),
                                      "answer": (-index) % 3, "explanation": explanation}
                                     for index, (prompt, correct, wrong_a, wrong_b, explanation) in enumerate(questions)])
new_rows.append(quiz_entry)

for hub_path, selected, title, summary in [
    (applications, paths[:4], "API documentation contracts", "Ground operation pages, examples, and migration notes in a versioned public contract."),
    (production, paths[4:], "API docs release evidence", "Check links, examples, shared status lists, and deployed behavior."),
    (projects, [project_path], "Shipment Status docs review", "Review a fictional v2 status addition and its client impact."),
    (quizzes, [quiz_path], "API documentation decisions", "Test public fields, errors, examples, compatibility, and release state."),
]:
    hub = lookup[hub_path]
    hub["data"]["modules"].append({"title": title, "summary": summary, "lessons": selected})
    hub["body"] += "<h2>" + html.escape(title) + "</h2><p>" + html.escape(summary) + "</p>" + links(selected + [project_path, quiz_path])
    hub["updated_at"] = stamp

root_hub = lookup[subject_root]
root_hub["body"] += "<h2>API documentation and release alignment</h2><p>Bind examples and migration notes to the public contract and deployed version.</p>" + links(paths + [project_path, quiz_path])
root_hub["updated_at"] = stamp

backlinks = {
    "prompt-engineering/code-change-acceptance-contract": paths[0],
    "prompt-engineering/schema-migration-prompt-review": paths[0],
    "prompt-engineering/schema-and-abstention": paths[1],
    "prompt-engineering/sensitive-output-redaction-gate": paths[2],
    "prompt-engineering/regression-test-oracle-contract": paths[2],
    "prompt-engineering/model-migration-contract": paths[3],
    "prompt-engineering/evidence-reference-checker": paths[4],
    "prompt-engineering/prompt-release-review-packet": paths[4],
}
for old_path, new_path in backlinks.items():
    entry = lookup[old_path]
    entry["body"] += "<p><strong>Continue with:</strong> " + link(new_path) + ".</p>"
    entry["data"]["related"] = related([item["path"] for item in entry["data"].get("related", [])] + [new_path])
    entry["updated_at"] = stamp

entries.extend(new_rows)
fixture.write_text(json.dumps(entries, ensure_ascii=False, indent=2) + "\n")
print(json.dumps({"newLessons": len(specs), "newProjects": 1, "newQuizzes": 1,
                  "newPaths": [entry["path"] for entry in new_rows]}))
