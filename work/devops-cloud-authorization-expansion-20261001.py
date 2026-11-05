"""Add cloud authorization and audit-evidence contracts to the local preview."""

import copy
import datetime
import html
import json
import uuid
from pathlib import Path

root = Path(__file__).resolve().parents[1]
fixture = root / "src/data/fixtures.json"
rows = json.loads(fixture.read_text())
by_path = {row["path"]: row for row in rows}
stamp = datetime.datetime.now(datetime.UTC).isoformat()
course = "devops/devops-tutorial"
project_hub = course + "/project"
quiz_hub = "devops/quizzes"
specs = []


def lesson(slug, title, summary, definition, operation, language, sample, cost, mistakes, related):
    path = "devops/" + slug
    assert path not in by_path, path
    specs.append(dict(path=path, title=title, summary=summary, definition=definition,
                      operation=operation, language=language, sample=sample,
                      cost=cost, mistakes=mistakes, related=related))


lesson(
    "cloud-policy-decision-trace",
    "Cloud policy decisions: trace every authorization layer",
    "A role policy is one input to an API authorization result, not the complete answer.",
    "A cloud API request is evaluated against the caller identity, action, resource, request context, and several policy layers. An identity allow can be narrowed by a permissions boundary, session policy, or organization guardrail; an applicable explicit deny wins. Resource policies and cross-account requests add further rules, including cases where a grant to a role session behaves differently from a grant to the role ARN. A policy simulator is useful, but a controlled real request remains the acceptance test for a service integration.",
    "A deployment role can upload a receipt bundle but cannot update the key policy protecting that bundle. When a deployment receives AccessDenied, first capture the exact API action, resource ARN, account, region, caller ARN, assumed-role session ARN, and condition values. Read the identity policy, boundary, session policy, organization controls, resource policy, and encryption-key policy as a single decision record. Check the service's authorization reference for resource scoping and condition support; an action that does not support the intended resource type can make a precise-looking allow ineffective. Test one approved operation and one deliberately denied operation in a disposable account. If the request is cross-account, verify permissions on both sides and the relevant service-specific resource rules. Record the matched statement and the policy version used at the time of the test. Do not fix an obscure denial by attaching administrator access to the role: that obscures the actual failed condition and expands unrelated permissions. An error message may identify one denial reason without proving every other layer would allow the request after that reason is removed.",
    "text",
    "Receipt deploy authorization worksheet\nCaller: account, role ARN, session ARN, source identity\nRequest: API action, resource ARN, region, condition context\nCeilings: boundary, session policy, organization controls\nResource side: bucket and key policies where applicable\nProof: approved request succeeds; prohibited request is denied\nEvidence: policy versions and request identifiers retained",
    "Evaluating P policy statements conceptually requires checking the statements relevant to one action and resource; diagnostic effort grows with P and with the number of policy layers. Wildcards may reduce policy size but increase the blast radius of a mistake. Measure authorization failures by action and role, time to identify the denying layer, and unexpected successes found by negative tests. Keep audit identifiers, not credentials or signed requests, in the incident record.",
    ["Do not treat an identity allow as final authorization.", "Do not assume a simulator reproduces every service-side condition.", "Do not widen the role before checking the exact resource and request context."],
    ["devops/federated-workload-identity", "devops/kubernetes-rbac", "devops/break-glass-access", "devops/encryption-key-rotation-recovery"],
)

lesson(
    "delegated-role-passrole-boundary",
    "Delegated role creation: constrain both the new role and its use",
    "A creator who can attach policy and pass a role can turn a narrow deployment permission into broader service authority.",
    "Permission to create a role is not the same as permission to run a workload with it. A role's trust policy determines who can assume it, its identity policy determines what it can do, a permissions boundary caps grants from identity policies, and a PassRole permission controls which role a caller may hand to a service. Safe delegation needs constraints at each step. A boundary does not itself grant the new role an action, and the delegating principal must be prevented from removing or replacing that boundary.",
    "A platform pipeline creates one worker role for each archive processor. Require a reviewed boundary at role creation and prevent the pipeline from editing or deleting that boundary policy. Limit role names and paths to the pipeline's namespace, restrict attachment to approved policies, restrict PassRole to those roles, and tie PassRole to the intended compute service. Require a trust policy that names that service rather than an arbitrary account principal. In a disposable account, attempt to create a role without the boundary, attach a broader policy, pass an unrelated administrator role, and change the role trust to an external account; each attempt should fail. Then deploy the intended worker and verify it can read its queue and write only its output prefix. Review the role after deployment, because a controller may mutate or replace resources after the initial plan. Where a service creates its own service-linked role, treat that as a separate path rather than assuming the worker-role rule covers it. Record who can update the boundary and who can pass the resulting role; separating these authorities matters more than a reassuring role name.",
    "text",
    "Archive worker delegation gate\nCreateRole: approved path and mandatory boundary\nBoundary changes: denied to workload pipeline\nAttachPolicy: reviewed policy set only\nPassRole: approved worker role and intended compute service\nTrust: exact service principal, tested by assume attempt\nNegative tests: no-boundary, admin-role pass, external trust",
    "With R delegated roles, inventory and drift review are O(R) in role records, while permission testing adds service-specific API calls. A boundary reduces possible authority but adds policy maintenance: changing it can break many roles at once. Measure unbounded-role count, PassRole grants outside approved paths, deployment denials, and drift from reviewed trust policies. A successful role create call is not proof the resulting workload is confined.",
    ["Do not grant PassRole over every role to simplify a deployment.", "Do not let the creator remove the boundary that constrains its own creations.", "Do not treat a role's trust policy as a substitute for its permissions policy."],
    ["devops/cloud-policy-decision-trace", "devops/ci-oidc-claim-boundary", "devops/terraform-module-contracts", "devops/policy-exception-expiry"],
)

lesson(
    "abac-tag-mutation-boundary",
    "Tag-based access: defend the attribute write path",
    "An authorization tag is part of the permission boundary, not decorative metadata.",
    "Attribute-based access compares principal, request, and resource attributes to decide whether an operation is allowed. If a caller can change a resource's authorization tag or supply an untrusted session tag, it may grant itself access without editing an obvious identity policy. Tag conditions also vary by API operation and resource type; a condition that works on reads may not cover creation, tagging, or deletion. The system must control how trusted attributes enter and change.",
    "A ledger team uses a project tag to isolate payout reports. The session's project value comes from a trusted identity source, while only a separate platform role can change the protected project tag on a report store. At resource creation, require the project tag to match the caller's trusted project and reject absent or extra authorization tags. At update, deny changes to the protected key even when ordinary descriptive tags may be edited. Test a caller who tries to retag another team's resource, remove the tag, create a resource without a tag, and pass a forged session value. Check every API action in the intended workflow for tag-condition support and for operations that authorize against parent resources rather than the new object. Keep cost-center and display-name tags separate from access-control tags so routine accounting edits cannot change access. If a federated identity maps a human attribute to a session tag, review both the mapping and who can alter the upstream attribute. A successful same-team read is only half the test; cross-team denial and mutation denial are the more valuable evidence.",
    "text",
    "Payout report ABAC test matrix\nTrusted session project: ledger-west\nOwn report: read allowed\nOther-project report: read denied\nCreate without project tag: denied\nRetag other report to ledger-west: denied\nRemove protected project tag: denied\nChange descriptive owner note: permitted by separate rule",
    "Testing A protected actions against T attribute states takes O(A × T) cases if every combination is exercised. The policy can be small, but the attribute supply chain and service-specific condition support increase review cost. Measure authorization-tag mutations, resources missing trusted tags, cross-project negative-test results, and denied legitimate creates. A tag-based model that cannot explain who sets the tag is incomplete.",
    ["Do not trust a session tag merely because it appears in the request.", "Do not allow routine tag editors to alter authorization attributes.", "Do not assume a tag condition applies to every service operation."],
    ["devops/cloud-policy-decision-trace", "devops/federated-workload-identity", "devops/shared-node-cost-allocation", "devops/policy-exception-expiry"],
)

lesson(
    "service-principal-source-boundary",
    "Service-principal trust: bind the caller to the intended source",
    "A resource policy that trusts a cloud service principal may also trust requests the service makes for someone else.",
    "A managed service often writes to a bucket, publishes to a topic, or uses an encryption key on behalf of a configured customer resource. Granting the service principal alone can leave a confused-deputy path: another party might configure that service to target your resource. Where supported, constrain the service call by the source resource identifier and source account, and confirm that the service actually sends those context keys for the operation.",
    "A central audit bucket accepts log delivery from a named trail in a member account. Its resource policy allows the exact delivery action and destination prefix for the logging service, with a source-account condition and a source-resource condition tied to the approved trail. Build the policy in a disposable account and verify that the approved trail can deliver a test event. Then configure a second trail outside the approved source and confirm its delivery is denied. Check the service's documented ARN shape and policy requirements; some services call auxiliary actions before writing, and a condition copied from another service can break legitimate delivery. Review organization-wide policies separately, because a guardrail may deny a call that the bucket policy permits. If the source identifier cannot be specified at creation time, use a narrow transitional condition with a short review deadline, then replace it once the identifier is known. Capture denied request IDs and delivery health. A policy that blocks attackers but silently stops the audit trail defeats the reason it was installed.",
    "text",
    "Audit delivery resource-policy review\nPrincipal: logging service only\nAction: required bucket check and object write only\nDestination: dedicated trail prefix\nSource account: approved member account\nSource resource: named trail identifier\nPositive test: approved delivery visible\nNegative test: unapproved trail cannot deliver",
    "Evaluating N configured source resources requires an inventory of N identifiers and at least a sample of positive and negative delivery tests. A broad principal-only allow is easier to deploy but widens the destination's exposure. Measure denied foreign-source attempts, time since last valid delivery, and policy exceptions awaiting removal. A new source trail needs an intentional policy change; that review cost is part of the security control.",
    ["Do not assume a service principal identifies your account's configuration.", "Do not add source conditions without testing the service's actual call path.", "Do not accept stopped audit delivery as a successful security rollout."],
    ["devops/cloud-policy-decision-trace", "devops/log-pipeline-retention", "devops/immutable-backup-retention", "devops/policy-exception-expiry"],
)

lesson(
    "sts-session-lineage-expiry",
    "Temporary sessions: preserve caller lineage through role chains",
    "A temporary credential's effective lifetime and attributes depend on how the session was issued.",
    "A role session carries an assumed-role identity, expiry, and optional source identity or session tags. A second AssumeRole call forms a role chain with its own duration limit; only tags marked transitive continue into later sessions. Session names supplied by callers are useful labels but are not necessarily a trusted person identifier. Authorization and audit should depend on controlled issuer attributes and recorded source identity where the integration supports them.",
    "A release controller enters a tools account, then assumes a production deploy role. Require the first issuer to provide a reviewed change identifier and source identity, and permit only the intended second role. Keep the second session shorter than the expected deployment plus rollback window, or arrange safe credential refresh before expiry; a long-running migration cannot rely on one credential indefinitely. Verify that the project session tag survives the chain only when it is intentionally marked transitive, and deny callers that try to set a different project value. Record both role assumption events, source identity, session ARN, change identifier, and deployment artifact digest. Run a negative test with a missing tag and one with a forged value. Expire a disposable session mid-operation to verify the controller stops safely and can resume without double-applying a change. Do not place personal data, access tokens, or secrets in session names or tags; these fields can appear in audit records. If a workload federation path bypasses the first role, test that path separately instead of assuming the same lineage contract applies.",
    "text",
    "Release session chain\nIssuer: trusted automation identity\nFirst role: tools account, source identity retained\nSecond role: production deploy, explicit trust and short lifetime\nTransitive tag: approved project only\nEvidence: assumption events, change ID, artifact digest\nExpiry test: migration resumes without duplicate effect",
    "A two-hop chain adds credential-exchange latency and more failure points, while short sessions require renewal for long tasks. Auditing S sessions costs O(S) event records plus joins across assumption events; a stable source identity lowers investigation time. Measure sessions lacking trusted lineage, failed refreshes, expired-operation count, and role assumptions outside the expected path. Credential expiry is a recovery case, not merely a security setting.",
    ["Do not use a caller-chosen session name as verified human identity.", "Do not assume ordinary role tags propagate through a chain.", "Do not give a migration a longer time budget than its credentials without renewal or resume logic."],
    ["devops/federated-workload-identity", "devops/ci-oidc-claim-boundary", "devops/credential-incident-rotation", "devops/release-evidence-record"],
)

lesson(
    "kms-grant-lifecycle-recovery",
    "Encryption-key grants: inventory and retire temporary authority",
    "A key grant can authorize cryptographic use without changing the key policy text.",
    "Managed services commonly create grants to use a customer-managed encryption key for a resource. A grant names a grantee and allowed operations, and may constrain cryptographic requests by encryption context or source resource. A key policy review that ignores active grants misses part of the authority picture. Revoking a grant during incident response can also break a healthy volume, archive, or replication process, so removal requires a resource-to-grant map.",
    "A billing archive copies encrypted documents to a recovery account. Inventory the source and destination key policies, active grants, grantees, operations, constraints, and the storage resources that depend on them. In a disposable environment, create a constrained grant for a copy worker, complete one copy, and verify that a decrypt with the expected context succeeds while a mismatched context fails. If grant creation is retried after an ambiguous response, list grants before creating another so duplicate authority is visible. Retire the temporary grant only after the service has finished using it, then repeat the read with the permanent recovery role to prove the backup remains accessible. During key rotation, test an older encrypted object before retiring old grants or scheduling key deletion. Record grant identifiers outside public logs; encryption context is often logged in plaintext and must not contain customer secrets. For an incident, identify the exact malicious grantee and affected resources before revoking broad service grants that could take production storage offline.",
    "text",
    "Archive key-grant review\nKey: source and recovery key identifiers\nGrant: ID, grantee, operations, creation time\nConstraint: approved context or source resource\nDependency: archive or copy job using grant\nNegative test: wrong context denied\nRetirement: job complete and older restore still works",
    "For G grants across K keys, inventory is O(G + K) records; matching grants to dependent resources adds a join against resource inventory. Stale grants increase review and exposure cost, while premature retirement adds outage risk. Measure grant count by key and grantee, duplicate grants, age after job completion, and failed decrypts after cleanup. A digest-valid object is not recoverable if no approved principal can decrypt it.",
    ["Do not infer complete key authority from the key policy alone.", "Do not use customer secrets as encryption-context values.", "Do not revoke a service grant before mapping the resource that uses it."],
    ["devops/encryption-key-rotation-recovery", "devops/object-lock-hold-key-recovery", "devops/object-checksum-copy-reconciliation", "devops/cloud-policy-decision-trace"],
)

lesson(
    "audit-data-event-coverage",
    "Audit trails: prove which data-plane actions are recorded",
    "Management-event logging does not imply every object read or write is recorded.",
    "Cloud audit systems distinguish control-plane actions from data-plane activity. A trail may record role and bucket configuration changes while omitting high-volume object reads, writes, or function invocations unless selectors include those resource types and actions. Selectors are part of the evidence contract: an investigator needs to know which action, resource prefix, account, and period were covered, and when the configuration changed.",
    "A payments archive must investigate who retrieved payout exports. Before claiming read visibility, inspect the active event selectors and confirm that the archive's object resource type, bucket prefix, and read operations are included. Compare the selector with one successful read and one denied read from disposable test identities; locate the resulting records by request time and resource. Then test a write and a delete separately, because a selector restricted to reads cannot answer who altered an object. Keep management events in the proposed selector when changing from basic to advanced mode; replacing selectors without carrying forward existing coverage creates a blind interval. Scope high-volume data events by approved prefixes and actions to control charges, but document exclusions as investigative limits. Record delivery delay and the clock skew of the test client so an apparent missing event is not simply a search-window error. Do not use an audit trail as synchronous access control: the request is authorized before the event is delivered. For incident review, correlate cloud request IDs with application records while protecting customer object keys in the query output.",
    "text",
    "Payout archive event-coverage matrix\nRole and policy change: management event\nObject read: archive prefix data event\nObject write: archive prefix data event\nObject delete: archive prefix data event\nApproved and denied probes: request IDs retained\nSelector change: prior coverage compared before and after",
    "Logging cost often scales with selected event volume; broad object-read capture can be much larger than management-event volume. A review of E events is O(E) to scan without a suitable index, so retain queryable partitions and bounded time windows. Measure probe-to-delivery delay, missing probe events, excluded prefixes, and event volume by operation. If an audit record is absent, check selector scope and delivery health before concluding the operation never happened.",
    ["Do not infer object-read coverage from role-change events.", "Do not replace selectors without comparing old and new coverage.", "Do not equate missing search results with proof an operation did not occur."],
    ["devops/log-pipeline-retention", "devops/object-event-ordering-idempotency", "devops/release-evidence-record", "devops/telemetry-sensitive-data-boundary"],
)

lesson(
    "audit-log-integrity-chain",
    "Audit log integrity: verify delivery and digest continuity",
    "Storing audit files is different from proving that delivered files were not altered or removed.",
    "A log-integrity feature can deliver signed digest records that name and hash audit files. Enabling delivery of those digests is only the first step; a verifier must check signatures, file hashes, and continuity for the requested time range. An intact digest chain speaks to delivered log files, while selector coverage and delivery health determine whether the events of interest were captured at all. These are separate questions in an investigation.",
    "A finance account writes audit records into a restricted central bucket. Enable digest delivery before the test window, record the trail configuration and event selectors, and run a controlled role-assumption and object-read probe. After delivery, validate the digest chain over that bounded window with an independent read role. Verify the probe events are present and their request identifiers match the test record. In a disposable copy, alter one audit file and remove another; the validation process should report the tampering or gap rather than silently accepting the directory. Simulate a bucket-policy denial and show how delivery health and missing digest periods appear. Keep the digest bucket access path separate from the roles whose actions it records, and retain key material needed to verify signatures for the full investigation period. Do not make an incident claim from one successful file hash: record the covered accounts, regions, dates, selected event classes, and any interval when validation or delivery was disabled. A negative validation result should trigger preservation of evidence before repair automation overwrites the test artifacts.",
    "text",
    "Finance audit-evidence acceptance\nWindow: UTC start and end recorded\nCoverage: accounts, regions, event selectors\nDigest: signature and chain verified\nFiles: recorded hashes match delivered objects\nProbe: role assumption and object read located\nGap: missing delivery or disabled validation reported\nCustody: independent read role and retained results",
    "Validating F log files requires at least O(F) hash checks and reads over their bytes; digest signatures add smaller fixed cryptographic work per digest. This has retrieval and compute cost, but a sampling-only check cannot establish continuity across the whole interval. Measure unverified hours, delivery lag, validation failures, and time to explain a missing probe. A valid chain does not compensate for a selector that never recorded the object operation.",
    ["Do not call digest delivery the same as digest validation.", "Do not treat an intact file chain as proof every API action was selected.", "Do not ignore a disabled or undelivered interval in an incident timeline."],
    ["devops/audit-data-event-coverage", "devops/immutable-backup-retention", "devops/log-pipeline-retention", "devops/incident-review-actions"],
)

titles = {row["path"]: row["title"] for row in rows}
titles.update({item["path"]: item["title"] for item in specs})
project_path = "devops/cloud-authorization-audit-project"
quiz_path = "quizzes/devops-cloud-authorization-decisions"
titles[project_path] = "Project: prove a cloud deployment's authority and audit trail"
titles[quiz_path] = "DevOps cloud authorization and audit decisions"
assert all(path in titles for item in specs for path in item["related"])


def links(paths):
    return "<ul>" + "".join(
        f'<li><a href="/{html.escape(path)}">{html.escape(titles[path])}</a></li>'
        for path in dict.fromkeys(paths)
    ) + "</ul>"


for heading, summary, slugs in [
    ("Policy and role delegation", "Trace authorization through policy layers and test constrained role creation.", ["cloud-policy-decision-trace", "delegated-role-passrole-boundary"]),
    ("Attributes and service trust", "Protect access-control tags and bind service principals to intended sources.", ["abac-tag-mutation-boundary", "service-principal-source-boundary"]),
    ("Session and key authority", "Preserve temporary-session lineage and retire key grants safely.", ["sts-session-lineage-expiry", "kms-grant-lifecycle-recovery"]),
    ("Audit coverage and integrity", "Prove which operations are logged and validate the delivered evidence chain.", ["audit-data-event-coverage", "audit-log-integrity-chain"]),
]:
    paths = ["devops/" + slug for slug in slugs]
    by_path[course]["data"]["modules"].append({"title": heading, "summary": summary, "lessons": paths})
    by_path[course]["body"] += f"<h2>{html.escape(heading)}</h2><p>{html.escape(summary)}</p>" + links(paths)
by_path[course]["updated_at"] = stamp

for index, item in enumerate(specs):
    path = item["path"]
    row = copy.deepcopy(by_path["devops/continuous-integration"])
    row.update(id=str(uuid.uuid5(uuid.NAMESPACE_URL, "aitrove:" + path)), path=path,
               title=item["title"], summary=item["summary"], subject="devops",
               category="DevOps", difficulty="Advanced", tags=["devops", "cloud-security"],
               sort_order=22000 + index, published_at=stamp, created_at=stamp, updated_at=stamp)
    row["data"] = {"kind": "tutorial", "reading_minutes": 6,
                   "author_path": "authors/aitrove-editorial", "subject_root": course,
                   "section_path": course, "content_format": "html", "seo_ready": True,
                   "related": [{"path": target, "title": titles[target]} for target in item["related"]]}
    row["body"] = (
        f"<p>{html.escape(item['definition'])}</p><h2>Operational decision</h2>"
        f"<p>{html.escape(item['operation'])}</p>"
        f'<pre><code class="language-{item["language"]}">{html.escape(item["sample"])}</code></pre>'
        f"<h2>Cost and verification</h2><p>{html.escape(item['cost'])}</p>"
        + "<h3>Common Mistakes</h3><ul>"
        + "".join(f"<li>{html.escape(mistake)}</li>" for mistake in item["mistakes"])
        + "</ul><h2>Connected lessons</h2>" + links([course, *item["related"]])
    )
    rows.append(row)

project_related = [item["path"] for item in specs]
project = copy.deepcopy(by_path["devops/practice-project"])
project.update(id=str(uuid.uuid5(uuid.NAMESPACE_URL, "aitrove:" + project_path)),
               path=project_path, title=titles[project_path],
               summary="Test policy ceilings, tag mutation, service trust, session lineage, key grants, and audit evidence.",
               difficulty="Advanced", sort_order=22090,
               published_at=stamp, created_at=stamp, updated_at=stamp)
project["data"] = {"kind": "project", "reading_minutes": 9,
                   "author_path": "authors/aitrove-editorial", "subject_root": course,
                   "section_path": project_hub, "content_format": "html", "seo_ready": True,
                   "related": [{"path": target, "title": titles[target]} for target in project_related]}
project["body"] = (
    "<p>Use disposable member accounts, a temporary audit bucket, a test compute service, synthetic payout objects, and an encryption key created solely for this drill. Define expected allowed and denied API calls before writing policies. Keep the test identities separate from the role that can inspect audit evidence. Record account identifiers, policy versions, resource identifiers, and start and end times in a local test ledger; do not put credentials or signed requests into that ledger.</p>"
    "<h2>Prove delegation boundaries</h2><p>Create a deploy role whose identity policy permits writing a narrow object prefix, with a boundary that denies unrelated security changes. Exercise one permitted write and one key-policy change that must fail, then trace both outcomes across the identity, boundary, session, organization, resource, and key-policy layers. Delegate creation of an archive worker role while requiring its boundary and restricting PassRole to the reviewed compute service. Attempt to create an unbounded role, pass an administrator role, and change trust to an outside account. Each negative test needs a request identifier and a confirmed denial. A successful role creation alone is not acceptance; launch the worker and inspect the final trust and permissions.</p>"
    "<h2>Probe attributes and service callers</h2><p>Use a protected project tag to limit access to synthetic payout records. Verify an own-project read, another-project denial, and denials for missing, removed, or forged tags. Then configure a named audit trail to write into the test bucket. Limit its resource policy to the intended service source and account, prove the approved trail delivers, and confirm an unapproved trail cannot write. If a condition blocks the approved service's auxiliary call, correct the exact action without broadening every destination prefix.</p>"
    "<pre><code class=\"language-text\">Authorization and audit acceptance\nPermitted deploy write succeeds; prohibited key change fails\nNew worker role has required boundary and restricted PassRole\nForged project tag and cross-project read fail\nUnapproved service source cannot write audit objects\nRole chain retains reviewed source identity and project attribute\nTemporary key grant permits only intended context\nObject-read audit event is present for selected prefix\nDigest validation detects a changed or missing log file</code></pre>"
    "<h2>Trace sessions and grants</h2><p>Assume a tools role, then a production-like deploy role with a reviewed source identity and transitive project tag. Test a missing or forged tag, and expire one disposable session during a resumable job. Inventory the key's grants, create a constrained temporary copy grant, verify expected and mismatched encryption contexts, then retire the grant after the copy completes. Confirm that an older encrypted payout object remains readable by the recovery role. Do not retire a real service grant merely to pass this exercise.</p>"
    "<h2>Validate audit evidence</h2><p>Inspect event selectors before claiming data-plane coverage. Perform one approved object read, one denied read, and one policy change; locate all selected probe records after delivery. Carry forward prior management-event coverage when editing selectors. Enable integrity digests for the test window, validate the chain, then alter and remove files only in a disposable copy to prove the verifier reports tampering and gaps. Record selector scope, delivery delay, disabled intervals, and unverified hours. Report which claims were proven by live API calls and which remain policy review only. Clean up test roles, grants, resources, and audit files after preserving the results needed for review.</p>"
    "<h3>Common Mistakes</h3><ul><li>Do not grant administrator access to bypass one unexplained denial.</li><li>Do not let a role creator change its own boundary or trusted attributes.</li><li>Do not claim audit completeness from an intact digest when selectors excluded the target action.</li></ul>"
    "<h2>Connected lessons</h2>" + links([*project_related, project_hub])
)
rows.append(project)
by_path[project_hub]["data"]["modules"][0]["lessons"].append(project_path)
by_path[project_hub]["body"] += "<h2>Cloud authorization and audit drill</h2>" + links([project_path])
by_path[project_hub]["updated_at"] = stamp

questions = [
    ("What must an access-denied investigation capture first?", ["Exact caller, action, resource, and request context", "Only the role name", "Only the application log level"], "Authorization depends on all request dimensions and applicable policies."),
    ("Does a permissions boundary grant an action by itself?", ["No, it caps identity-policy grants", "Yes, for every resource", "Yes, after role creation"], "The boundary is a ceiling, not an allow by itself."),
    ("Why restrict PassRole separately from CreateRole?", ["A caller can hand a powerful role to a service", "It changes object checksums", "It rotates audit files"], "Delegation must constrain both role creation and use."),
    ("What is the main ABAC tag risk?", ["An untrusted tag writer can change authorization", "Tags always expire", "Tags cannot be logged"], "The attribute write path needs its own controls."),
    ("What narrows a service-principal resource policy?", ["Supported source resource and source account conditions", "Only a shorter bucket name", "Only a session display name"], "Bind the service call to the intended customer resource."),
    ("What is required after adding source conditions?", ["Test both approved delivery and unapproved denial", "Assume delivery still works", "Disable audit alerts"], "A security rule must not silently stop the service."),
    ("Which session tag survives a role chain?", ["A tag explicitly marked transitive", "Every tag on the first role", "Only a tag written to a log"], "Transitivity is an explicit session property."),
    ("Why is a caller-provided session name weak proof of person identity?", ["The caller can choose its value", "It is always encrypted", "It cannot appear in events"], "Use controlled issuer attributes or source identity."),
    ("What can authorize key use beyond key-policy text?", ["An active key grant", "Only an object ETag", "Only a DNS record"], "Grant inventory is part of effective authority."),
    ("When should a temporary key grant be retired?", ["After mapping dependencies and confirming the task is complete", "Immediately after creation", "Only when the bucket is empty"], "Premature retirement can break a service or restore."),
    ("Do management events prove object reads were logged?", ["No, data-event selector scope must be checked", "Yes, for every prefix", "Yes, if a digest exists"], "Control-plane and data-plane coverage differ."),
    ("What does a valid audit digest chain establish?", ["Integrity of covered delivered files, not selector completeness", "Every API call was logged", "Every role was least-privileged"], "Coverage, delivery, and integrity are separate questions."),
]
quiz = copy.deepcopy(by_path["quizzes/devops-operations"])
quiz.update(id=str(uuid.uuid5(uuid.NAMESPACE_URL, "aitrove:" + quiz_path)), path=quiz_path,
            title=titles[quiz_path], summary="Twelve decisions on policy layers, delegation, session authority, and audit evidence.",
            sort_order=22100, published_at=stamp, created_at=stamp, updated_at=stamp)
quiz["data"] = {"subject_root": course, "section_path": quiz_hub, "content_format": "html",
                "author_path": "authors/aitrove-editorial", "seo_ready": True, "duration_minutes": 12,
                "related": [{"path": target, "title": titles[target]} for target in project_related],
                "questions": [dict(prompt=prompt, options=options[index % 3:] + options[:index % 3],
                                   answer=(-index % 3) % 3, explanation=explanation)
                              for index, (prompt, options, explanation) in enumerate(questions)]}
quiz["body"] = (
    "<p>Decide what each policy layer permits, which attribute source can be trusted, and whether audit evidence covers the operation in question. A denied call and a missing event require different investigations.</p>"
    "<h2>Review these lessons</h2>" + links(project_related)
    + "<h2>Other checks</h2>" + links([quiz_hub, "quizzes/devops-object-storage-decisions", "quizzes/devops-runtime-isolation-decisions"])
    + "<h3>Common Mistakes</h3><ul><li>Do not mistake a permissions ceiling for an allow.</li><li>Do not infer complete event coverage from a valid log digest.</li></ul>"
)
rows.append(quiz)
by_path[quiz_hub]["data"]["modules"][0]["lessons"].append(quiz_path)
by_path[quiz_hub]["body"] += "<h2>Cloud authorization check</h2>" + links([quiz_path])
by_path[quiz_hub]["updated_at"] = stamp

for item in specs:
    row = next(row for row in rows if row["path"] == item["path"])
    row["body"] += "<h2>Practice and check</h2>" + links([project_path, quiz_path])
    row["data"]["related"].extend({"path": path, "title": titles[path]} for path in [project_path, quiz_path])

for source, targets in {
    "devops/federated-workload-identity": ["devops/cloud-policy-decision-trace", "devops/sts-session-lineage-expiry"],
    "devops/ci-oidc-claim-boundary": ["devops/delegated-role-passrole-boundary", "devops/sts-session-lineage-expiry"],
    "devops/break-glass-access": ["devops/cloud-policy-decision-trace", "devops/audit-log-integrity-chain"],
    "devops/policy-exception-expiry": ["devops/abac-tag-mutation-boundary", "devops/service-principal-source-boundary"],
    "devops/encryption-key-rotation-recovery": ["devops/kms-grant-lifecycle-recovery"],
    "devops/log-pipeline-retention": ["devops/audit-data-event-coverage", "devops/audit-log-integrity-chain"],
    "devops/release-evidence-record": ["devops/sts-session-lineage-expiry", "devops/audit-data-event-coverage"],
    "devops/object-lock-hold-key-recovery": ["devops/kms-grant-lifecycle-recovery"],
}.items():
    row = by_path[source]
    row["body"] += "<h2>Cloud authority follow-up</h2>" + links(targets)
    row["data"].setdefault("related", []).extend({"path": target, "title": titles[target]} for target in targets)
    row["updated_at"] = stamp

assert len({row["path"] for row in rows}) == len(rows)
fixture.write_text(json.dumps(rows, ensure_ascii=False, indent=2) + "\n")
print(json.dumps({"new_lessons": len(specs), "new_projects": 1, "new_quiz_banks": 1, "total_records": len(rows)}))
