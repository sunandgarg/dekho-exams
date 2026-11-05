"""Add original platform engineering operating-contract content to local fixtures."""

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
                      operation=operation, language=language, sample=sample, cost=cost,
                      mistakes=mistakes, related=related))


lesson(
    "service-catalog-operational-owner",
    "Service catalog ownership: prove that the named team can respond",
    "A catalog owner is operationally useful only when it resolves to an active team, reachable rota, and current runbook.",
    "A service catalog is an indexed description of software and its relationships. Its owner field is a claim, not a pager test. A renamed team, deleted repository, stale on-call schedule, or missing runbook can leave a polished catalog entry that fails during an incident. Treat catalog metadata as a contract whose critical fields must be checked against systems of record and against an actual escalation path. The service identifier should remain stable across repository renames so incidents and release evidence still join to the same workload.",
    "For a payment-reconciliation API, register a stable service ID, repository, production workload, owning team, escalation schedule, runbook, data classification, and retirement state. A scheduled verifier resolves the team and schedule through their current identities and records the last successful check; it does not infer ownership from the person who last committed code. Inject three faults into a disposable catalog: delete the schedule, move the repository, and disable the runbook link. Each should flag a different broken contract with an assigned repair owner. During a simulated incident, start from a runtime alert and reach the responsible human without searching chat history. When ownership transfers, the receiving team acknowledges the alert path before the old team is removed, and the record retains a transfer date. A stale entry is marked suspect even if its source file still parses.",
    "text",
    "Service: payment-reconciliation\nStable ID: payments.reconciliation\nOwner: team-ledger-operations\nEscalation: current rota ID and tested contact\nRunbook: current incident procedure\nRuntime: production workload identity\nLast verified: timestamp and result\nTransfer: receiving-team acceptance required",
    "Verifying S services against external systems takes O(S) lookups per field, before caching or batching. Aggressive full-catalog polling can overload identity and paging APIs; use incremental checks with a periodic full audit. Measure unresolved owners, failed escalation drills, stale verification age, and incidents where ownership lookup exceeded the response target. A catalog entry is not evidence of response readiness until the lookup path works.",
    ["Do not use the last code author as the production owner.", "Do not accept a team name whose paging destination no longer exists.", "Do not remove the previous owner before the new team accepts escalation."],
    ["devops/alert-design", "devops/runbook-automation-guardrails", "devops/release-evidence-record", "devops/cost-capacity-ownership"],
)

lesson(
    "service-catalog-dependency-evidence",
    "Service catalog dependencies: distinguish declared edges from observed calls",
    "A dependency graph is a maintained hypothesis about failure paths, not a complete trace of production traffic.",
    "Catalog relations answer who says a service depends on a database, queue, API, or shared platform. Runtime telemetry answers which calls were observed in a particular window. Neither is complete by itself: a rarely used disaster-recovery path may have no recent trace, while a one-off request can appear in telemetry without being an intended contract. Incident impact analysis should compare both views, label the evidence age and direction of each edge, and send disputed relationships to an owner. Retired components must not vanish from history before their consumers are known.",
    "A ledger API declares a dependency on a settlement queue and a fraud service. The incident graph also shows recent calls to a legacy rates API that is absent from the catalog. The service owner checks code and configuration, confirms the rates call is still on the invoice path, and adds a reviewed edge. Conversely, an old database edge remains declared but has no calls; the team cannot remove it until a full billing-cycle test and configuration search show the fallback is gone. Simulate loss of the fraud service and use the graph to select synthetic transactions and accountable owners. Mark each edge as declared, observed, or both, with source and last verification time; avoid treating trace sampling gaps as proof of no dependency. Before deleting a service entry, traverse inbound edges, assign each consumer a migration or explicit waiver, and retain a tombstone that points to the replacement identity. Catalog ingestion errors should trigger a freshness alarm so a cached last-good entry is not mistaken for recently reviewed truth.",
    "text",
    "Ledger dependency review\nDeclared: ledger API -> settlement queue\nObserved: ledger API -> legacy rates API\nDispute: old billing database edge\nEvidence: source, direction, window, owner\nRetirement: inbound consumers accepted migration\nFreshness: last successful catalog processing",
    "An indexed dependency traversal is O(V + E) over services and edges; joining traces adds cost proportional to selected telemetry volume. Sampling, missing propagation, and encrypted paths can undercount calls. Track unowned edges, declared-only edges past review age, unexplained observed calls, and retirement attempts with inbound consumers. A large graph is cheap to draw but expensive to keep truthful; spend review effort on edges that affect release and incident decisions.",
    ["Do not delete a dependency because it was absent from a short trace window.", "Do not assume a declared edge describes actual current traffic.", "Do not retire a catalog entry before its inbound consumers have a disposition."],
    ["devops/dependency-bulkhead-isolation", "devops/synthetic-transaction-monitoring", "devops/release-evidence-record", "devops/alert-design"],
)

lesson(
    "self-service-provisioning-contract",
    "Self-service provisioning: make the request contract explicit",
    "A platform request is a versioned API call with identity, policy, capacity, ownership, and a lifecycle decision.",
    "A self-service form that creates resources is an API even when its interface is a template. The request must validate requester authority, environment, data classification, region, cost center, quota, naming identity, and the desired retention period before side effects begin. The response must expose a durable request ID and a clear distinction between accepted, ready, rejected, and failed. Resource creation without an owner or cleanup rule moves toil from the requestor to the platform team and leaves orphaned infrastructure behind.",
    "A product team requests a review environment for the claims API. The platform validates that the team owns the service, its allowed region matches the data classification, the requested database tier fits budget and provider quota, and the lease has an expiry. It records the requested specification and policy decision under an idempotency key before creating any cloud resource. Repeat the same request after a client timeout; the platform should return the original request state instead of creating a second database. Change the requested tier while reusing the key and require a conflict rather than silently mutating the first request. A policy denial should explain which field failed and how to request an exception without leaking secret values. Publish the resource owner, support boundary, monthly cost estimate, deletion rule, and handoff condition in the response. A successful form submission is not proof that the workload can connect to its database.",
    "text",
    "Claims environment request\nRequest ID: durable identifier\nIdempotency key: caller plus operation identity\nService owner: team-claims\nClassification: internal\nRegion: approved region\nCapacity: database tier within quota and budget\nLease: expiry and renewal owner\nResult: accepted, ready, rejected, or failed",
    "Admission checks can be O(1) with indexed ownership and quota data, while provisioning latency depends on external providers and may last minutes. Keeping request records and a reconciliation worker adds storage and operational cost but prevents duplicate resources after retries. Measure requests denied for clear reasons, duplicate side effects, time to usable environment, orphan rate, and resources without a cost owner. Recheck quotas at execution because capacity can change between approval and allocation.",
    ["Do not create resources before recording an idempotent request.", "Do not call an accepted request ready before connectivity and ownership checks pass.", "Do not hide policy failures behind a generic provisioning error."],
    ["devops/provider-quota-preflight", "devops/namespace-resource-quotas", "devops/cost-capacity-ownership", "devops/ephemeral-environment-controls"],
)

lesson(
    "async-provisioning-state-machine",
    "Provisioning state machines: handle partial success and retries",
    "External resource creation is asynchronous; a durable controller must reconcile partial progress without duplicating it.",
    "A template runner can time out after creating a repository but before creating its database, or after issuing a provider request but before receiving the response. Blindly rerunning the whole script can duplicate resources or erase the only clue to an in-flight operation. Model each step with a durable operation ID, desired identity, observed provider identity, retry policy, timeout, and compensating action. Compensation is not always deletion: a database holding customer data may need retention and human review after a later step fails.",
    "For an audit-reporting service, the workflow creates a repository, workload identity, namespace, database, and deployment binding. Persist step state before and after each external call. Force the database response to time out after the provider has accepted it, then resume by looking up the stable requested database identity rather than issuing another create. Force the deployment binding to fail after the database exists. Mark the request partially ready, keep the database under a bounded retention rule, and present a repair or disposal choice to the owner. The workflow should never report Ready until a synthetic application connection succeeds and the owner can locate the created resources. A cancellation request must stop new steps while allowing in-flight calls to settle and be inventoried. Record every resource's desired identity, observed ID, creation timestamp, cost owner, and final disposition; otherwise later cleanup becomes guesswork. Reconcile the record against the provider inventory periodically to detect resources that exist but were never recorded as complete.",
    "text",
    "Audit service states\nRequested -> Validated -> Provisioning\nProvisioning -> Ready | PartialFailure | CancelPending\nPartialFailure -> Repairing | RetainedForReview\nCancelPending -> Settled -> Cleaned | RetainedForReview\nEvery transition: request ID, step ID, provider ID, timestamp\nReady gate: resource inventory plus application connection",
    "A workflow with K steps needs O(K) durable state and provider calls; retries increase requests and can amplify cost if external APIs lack stable identifiers. Reconciliation work scales with outstanding requests plus known resources, so archive terminal records without losing audit evidence. Measure stuck transitions, duplicate provider IDs per request, partial failures older than their repair window, and Ready states whose user-path probe fails. A timeout is uncertainty, not proof that a provider did nothing.",
    ["Do not rerun a timed-out create without checking the provider for the intended resource.", "Do not delete stateful resources as a blanket compensation action.", "Do not equate the final script exit code with the actual resource inventory."],
    ["devops/self-service-provisioning-contract", "devops/provider-quota-preflight", "devops/terraform-import-ownership", "devops/release-evidence-record"],
)

lesson(
    "golden-path-template-upgrade",
    "Golden path templates: design upgrades after code generation",
    "A generated repository is a copy at creation time; changing the template does not change its existing consumers.",
    "A golden path can establish build, test, deployment, telemetry, and incident defaults, but those defaults drift as tooling and policy change. A template version must describe what it generated and how an existing service moves to a newer contract. Treat generated code as team-owned, compare its current state before modifying it, and distinguish files the platform may manage from files the service has customized. Compatibility windows, codemods, and conformance checks make upgrades observable rather than relying on new templates to fix old repositories.",
    "A Java billing worker was created from template version 4.2; version 5.0 switches to a new workload identity and changes the CI workflow permissions. Record the template ID and original version in the service catalog. An upgrade tool reads the repository, proposes a patch, and checks whether affected files still match the known generated baseline. It opens a reviewable change for the service owner, runs build and deployment checks, and marks the adoption only after a real production rollout uses the new identity. If the owner customized the workflow, produce a conflict with a precise diff rather than replacing it. Test three consumers: untouched generated code, a locally modified workflow, and an old service that skipped version 4.5. Define whether the migration supports each starting version or requires intermediate steps. Keep a cutoff date for the old identity and track services still using it. A new repository created from version 5.0 is not evidence that the existing fleet has upgraded.",
    "text",
    "Template migration contract\nTemplate: java-billing-worker\nFrom: 4.2 (or supported intermediate)\nTo: 5.0\nManaged files: declared and baseline-checked\nConflict: owner review required\nConformance: CI permission and identity tests\nAdoption proof: deployed service uses new identity",
    "Scanning R repositories and M managed files is O(R × M) metadata comparisons, plus each repository's tests. Forced blanket changes are faster until they overwrite local behavior; reviewable migrations cost engineering time but reduce outage risk. Measure template version distribution, migration conflict rate, time to adopted production state, and policy violations remaining after cutoff. A catalog version field should reflect observed adoption, not merely that a patch was proposed.",
    ["Do not assume template updates modify repositories already generated.", "Do not overwrite a team-customized workflow without a reviewed diff.", "Do not mark an upgrade adopted before the service passes its deployment gate."],
    ["devops/ci-matrix-required-gate", "devops/terraform-module-contracts", "devops/release-evidence-record", "devops/policy-exception-expiry"],
)

lesson(
    "platform-template-execution-boundary",
    "Platform template execution: restrict parameters, actions, and credentials",
    "A template that runs code and publishes repositories crosses a privilege boundary, even when its form looks harmless.",
    "Template parameters may be untrusted input; template actions may create repositories, call cloud APIs, read secrets, or write into an organization. Authorization needs to cover who can see and execute the template, which parameters they can set, which actions may run, and what credentials each action receives. Restricting the web form alone is weak if an API caller can submit a different payload. Logs and generated repositories must not expose action tokens or secret values.",
    "A platform template creates an event-processing service and binds a deploy identity. Give the template a narrow repository-creation credential and a separate short-lived identity for the deployment registration step. The user supplies a repository name and target team; validate both against an allowlist and verified team membership on the server side. Reject a repository path containing parent traversal, an unapproved organization, or a requested identity outside the team's scope. Add a test action that tries to print its token and verify output redaction, log access, and token expiry. Review custom actions as privileged code, including network egress and access to runner files. A team allowed to create a development service should not inherit production secret access because both use the same underlying action. Record the effective policy decision and action versions with the request; if the template changes while a request waits in a queue, the worker must execute the reviewed version or reevaluate policy before side effects.",
    "text",
    "Event service template boundary\nCaller: verified team member\nTemplate version: immutable for queued request\nParameters: server-side validation\nRepository scope: approved organization and name\nAction credentials: separate, short-lived, least privilege\nLogs: redacted and access-controlled\nDecision: policy, action version, request ID",
    "Server-side authorization adds O(A) policy checks for A privileged actions and may call identity services; caching reduces latency but risks stale membership. Isolating credentials and retaining decision logs adds setup and storage cost. Measure denied cross-team requests, privileged action inventory, token exposure tests, and queued requests executed under changed policies. Security here depends on the executor's effective permissions, not the labels shown in the form.",
    ["Do not trust client-side form validation as authorization.", "Do not give every action one organization-wide token.", "Do not execute a queued request under an unreviewed template revision."],
    ["devops/self-service-provisioning-contract", "devops/policy-exception-expiry", "devops/secret-workload-create-access-boundary", "devops/release-evidence-record"],
)

lesson(
    "platform-composition-revision-rollout",
    "Platform API revisions: control changes to managed resources",
    "A platform API revision can change many consumers' infrastructure without changing each consumer's request.",
    "A shared composition or controller template translates a higher-level service claim into concrete cloud resources. Its revision is part of the effective infrastructure release identity. Some controllers can follow the newest revision automatically; others allow claims to stay pinned until explicitly moved. Either mode needs a target inventory, rendered or planned diff, compatibility check, health gate, and rollback rule. Reverting a definition may not reverse a provider-side migration, deletion, or data-format change.",
    "A managed database claim is used by 34 services. Revision 8 adds backup retention and changes a network rule. List every claim and the revision it currently observes, then partition consumers by environment and failure tolerance. Promote one disposable claim, inspect its resulting managed resources and external provider state, and run a backup-and-restore check. Advance a small production cohort only after both the controller's observed revision and application connectivity agree with the intended change. A consumer with a custom network policy must be reported as a conflict, not silently coerced. During a negative drill, make revision 9 invalid and confirm later claims stay pinned or the rollout controller stops further updates. If automatic update is enabled, control its blast radius through claim selection or revision policy before publishing the new composition. Record which claims remain on revision 8 and why; a global definition version alone does not prove fleet convergence.",
    "text",
    "Managed database revision rollout\nClaim inventory: 34 service IDs and observed revisions\nCandidate: revision 9 plus resource diff\nCohorts: disposable, small production, remaining\nGate: provider state, backup restore, app connectivity\nConflict: custom network policy requires owner review\nStop: failed cohort blocks later revisions\nRollback: provider-side effects evaluated separately",
    "Inventory and status checks scale O(C) for C claims; external reconciliation can be far slower and may be rate-limited by the provider. Smaller cohorts extend rollout time but bound simultaneous change. Measure claims on unsupported revisions, unexpected provider diffs, failed migrations, and time from definition publication to verified consumer adoption. A green controller condition does not substitute for a data restore or application connection check.",
    ["Do not change a shared composition without enumerating its consumers.", "Do not assume reverting a definition undoes provider-side changes.", "Do not treat desired revision as proof every claim observed it."],
    ["devops/terraform-module-contracts", "devops/provider-quota-preflight", "devops/backup-and-recovery", "devops/gitops-fleet-promotion-cohorts"],
)

lesson(
    "platform-product-slo-and-adoption",
    "Platform product signals: measure usable outcomes and support load",
    "A platform is useful when service teams can complete an operation safely, predictably, and without hidden manual rescue.",
    "Request volume is not adoption quality. A team may click a self-service button and still need a platform engineer to repair the result, or abandon the path after a timeout. Define success at the customer boundary: time to a usable environment, first successful deployment, policy denial clarity, restore success, and repeatable cleanup. Pair these with platform reliability measures such as request completion, stuck state, incident impact, and support effort. Segment by template version and team to find a broken path without turning identities into high-cardinality telemetry labels.",
    "For a service-bootstrap product, measure the fraction of accepted requests that reach a passing first deployment within a stated window. Track the median and tail elapsed time from accepted request to ready workload, manual interventions per completed service, and support tickets per active consumer. For cleanup, count expired leases that still hold billable resources. A failed request remains in the denominator even if an engineer manually fixes it; otherwise the dashboard rewards silent rescue. Run an experiment on a new template version with a small cohort, compare success and support load with an earlier version, and inspect failures by step. Publish an error budget for the platform's own provisioning API, then pause feature rollout if failures consume it. Do not set a universal target without a baseline and service-team agreement. The monthly review must decide which failure mode to remove, who owns the fix, and how the next measurement will prove it worked.",
    "text",
    "Bootstrap product scorecard\nAccepted -> ready environment -> first deploy\nCompletion: successful first deploy / accepted requests\nLatency: median and tail from acceptance to usable workload\nSupport: human interventions and tickets per consumer\nCleanup: expired leases with live billable resources\nReliability: stuck requests and provisioning incidents\nBreakdown: template version, step, bounded team cohort",
    "Computing funnel metrics from N requests is O(N) per batch pass or constant work per event with preaggregated counters. Detailed event retention and high-cardinality labels can become expensive; keep durable request IDs in logs and bounded dimensions in metrics. Measure both automated completion and the cost of human rescue, because a fast median can coexist with an unusable tail. Revisit thresholds when the workload mix changes rather than treating one number as permanent truth.",
    ["Do not count a submitted form as a successful platform outcome.", "Do not remove manually rescued failures from the denominator.", "Do not use unbounded request IDs as metrics labels."],
    ["devops/self-service-provisioning-contract", "devops/async-provisioning-state-machine", "devops/cost-capacity-ownership", "devops/alert-design"],
)


titles = {row["path"]: row["title"] for row in rows}
titles.update({item["path"]: item["title"] for item in specs})
project_path = "devops/platform-self-service-contract-project"
quiz_path = "quizzes/devops-platform-self-service-decisions"
titles[project_path] = "Project: prove a self-service platform request end to end"
titles[quiz_path] = "DevOps platform self-service decisions"
assert all(path in titles for item in specs for path in item["related"])
assert project_path not in by_path and quiz_path not in by_path


def links(paths):
    return "<ul>" + "".join(
        f'<li><a href="/{html.escape(path)}">{html.escape(titles[path])}</a></li>'
        for path in dict.fromkeys(paths)
    ) + "</ul>"


for heading, summary, slugs in [
    ("Platform ownership evidence", "Verify reachable owners and compare declared dependencies with runtime evidence.", ["service-catalog-operational-owner", "service-catalog-dependency-evidence"]),
    ("Self-service resource lifecycle", "Validate the request contract and recover from partial provisioning.", ["self-service-provisioning-contract", "async-provisioning-state-machine"]),
    ("Template change boundaries", "Upgrade generated consumers and restrict template execution privileges.", ["golden-path-template-upgrade", "platform-template-execution-boundary"]),
    ("Platform rollout and outcomes", "Control shared API revisions and measure usable consumer outcomes.", ["platform-composition-revision-rollout", "platform-product-slo-and-adoption"]),
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
               category="DevOps", difficulty="Advanced", tags=["devops", "platform-engineering"],
               sort_order=23000 + index, published_at=stamp, created_at=stamp, updated_at=stamp)
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
               summary="Build a request controller and prove ownership, privilege, partial recovery, upgrade, and cleanup behavior.",
               difficulty="Advanced", sort_order=23090,
               published_at=stamp, created_at=stamp, updated_at=stamp)
project["data"] = {"kind": "project", "reading_minutes": 10,
                   "author_path": "authors/aitrove-editorial", "subject_root": course,
                   "section_path": project_hub, "content_format": "html", "seo_ready": True,
                   "related": [{"path": target, "title": titles[target]} for target in project_related]}
project["body"] = (
    "<p>Build a disposable self-service path for a claims-review API. The input is a team-owned request for a repository, workload identity, namespace, and database. Acceptance requires a usable first deployment, verified support ownership, bounded privilege, a recoverable partial failure, and a cleanup disposition for every created resource. Use local fakes or disposable provider accounts; do not run the drill against shared production infrastructure.</p>"
    "<h2>Define the request boundary</h2><p>Give each request a durable ID, caller identity, stable service ID, data classification, region, quota, cost center, lease expiry, and idempotency key. Validate ownership and policy on the server. Submit the same request twice after a simulated client timeout and prove only one set of resources exists. Submit a different specification under the same key and require a conflict. Show the requester the accepted state separately from the ready state and preserve a reason for denial without exposing credentials.</p>"
    "<h2>Recover partial progress</h2><p>Persist step transitions and provider identifiers. After the database create is accepted, discard its response, restart the worker, and recover by looking up the intended provider identity. Fail a later deployment binding and verify the database remains inventoried under a bounded retention decision. Cancel another request while a call is in flight; do not report cleanup until the call settles and the resource is found or proved absent. A passing first deployment and an application connection test are required for Ready.</p>"
    "<pre><code class=\"language-text\">Claims platform acceptance\nRequest: one durable ID and one resource set after retries\nPolicy: caller, team, data class, region, quota checked\nExecution: step state and provider IDs recoverable\nPrivileges: action-specific short-lived credentials\nCatalog: reachable owner, rota, runbook, dependencies\nUpgrade: modified generated file yields review conflict\nShared API: failed first cohort stops later consumers\nCleanup: every expired lease has verified disposition\nOutcome: first deployment succeeds without manual rescue</code></pre>"
    "<h2>Test the consumer lifecycle</h2><p>Register the resulting service with an active team, paging rota, runbook, and declared database dependency. Disable the rota and verify the catalog check fails. Add an observed undeclared call and give its edge an owner and evidence window. Create a second repository from an older template version, customize its CI permissions, and run an upgrade proposal; require a review conflict rather than replacing that file. Attempt to invoke the provisioning action for an unauthorized team, then inspect server-side denial and log redaction.</p>"
    "<h2>Promote and measure</h2><p>Give the database API two revisions. Inventory its consumers, promote one disposable claim, then a small production-like cohort; force a failure and prove later claims remain on their previous revision. Report each claim's observed revision, provider state, and application connection result. Calculate accepted-to-first-deploy completion, tail latency, manual interventions, stuck requests, and expired leases with live billable resources. Count rescued requests as automation failures. Deliver a resource inventory and a cleanup record that another operator can audit.</p>"
    "<h3>Common Mistakes</h3><ul><li>Do not infer readiness from the template task finishing.</li><li>Do not retry uncertain provider calls without reconciling existing resources.</li><li>Do not mark a generated service upgraded before its owner reviews and deploys the change.</li></ul>"
    "<h2>Connected lessons</h2>" + links([*project_related, project_hub])
)
rows.append(project)
by_path[project_hub]["data"]["modules"][0]["lessons"].append(project_path)
by_path[project_hub]["body"] += "<h2>Platform self-service drill</h2>" + links([project_path])
by_path[project_hub]["updated_at"] = stamp

questions = [
    ("What makes a catalog owner operationally credible?", ["An active team, reachable escalation, and current runbook", "The last person to commit", "A nonempty owner field"], "The field must lead to a responding human during an incident."),
    ("How should an unobserved declared dependency be handled?", ["Review across its full use cycle before removal", "Delete it after one quiet trace window", "Assume telemetry is complete"], "Rare fallback paths may not appear in a short observation window."),
    ("What should happen when a request repeats after a client timeout?", ["Return the original operation state without duplicating resources", "Create a second database", "Treat timeout as proof nothing happened"], "Idempotency binds retry attempts to one durable operation."),
    ("What if the same idempotency key carries changed parameters?", ["Reject it as a conflicting request", "Silently alter the first request", "Ignore the new fields and report ready"], "A reused key cannot safely identify two desired specifications."),
    ("What follows a provider create call that times out?", ["Reconcile by stable requested identity and provider inventory", "Blindly issue the create again", "Delete every related resource"], "The provider may have accepted the first call."),
    ("When may a partially failed database be deleted automatically?", ["Only under its explicit retention and data disposition rule", "Whenever a later template step fails", "When the UI tab closes"], "Stateful resources can hold valuable or regulated data."),
    ("Does a template update repair existing generated repositories?", ["No; consumers need an explicit reviewed migration", "Yes; all generated files change automatically", "Only if the repository is private"], "Generation copies an initial state rather than maintaining a live link."),
    ("What if a service team changed a generated workflow?", ["Show a reviewable migration conflict", "Overwrite it with the newest template", "Exclude the service from all future checks"], "Local changes require owner review before replacement."),
    ("Where must template parameter authorization be enforced?", ["At the server-side action boundary", "Only in browser form fields", "Only in a catalog description"], "API callers can bypass client-side controls."),
    ("What proves a shared platform API revision reached a consumer?", ["Its observed revision, provider state, and application check", "The definition file changed", "The platform team announced it"], "A global definition change does not establish consumer convergence."),
    ("What should a failed first revision cohort do?", ["Block later consumers pending diagnosis", "Automatically update every remaining claim", "Delete the failed consumer"], "Cohorts exist to contain a bad shared change."),
    ("How should manually rescued provisioning requests affect success metrics?", ["Remain automation failures while recording the rescue", "Be removed from the denominator", "Count as immediate self-service success"], "Removing rescued failures hides platform support cost."),
]
quiz = copy.deepcopy(by_path["quizzes/devops-operations"])
quiz.update(id=str(uuid.uuid5(uuid.NAMESPACE_URL, "aitrove:" + quiz_path)), path=quiz_path,
            title=titles[quiz_path], summary="Twelve decisions on platform ownership, request safety, template migration, API revisions, and outcomes.",
            sort_order=23100, published_at=stamp, created_at=stamp, updated_at=stamp)
quiz["data"] = {"subject_root": course, "section_path": quiz_hub, "content_format": "html",
                "author_path": "authors/aitrove-editorial", "seo_ready": True, "duration_minutes": 12,
                "related": [{"path": target, "title": titles[target]} for target in project_related],
                "questions": [dict(prompt=prompt, options=options[index % 3:] + options[:index % 3],
                                   answer=(-index % 3) % 3, explanation=explanation)
                              for index, (prompt, options, explanation) in enumerate(questions)]}
quiz["body"] = (
    "<p>Evaluate whether a platform request yields a usable service and a resource set that can be owned, upgraded, and retired. For each decision, check the effective executor privileges and observed consumer state rather than the form's success message.</p>"
    "<h2>Review these lessons</h2>" + links(project_related)
    + "<h2>Other checks</h2>" + links([quiz_hub, "quizzes/devops-platform-reliability", "quizzes/devops-cost-capacity-decisions"])
    + "<h3>Common Mistakes</h3><ul><li>Do not count a submitted request as a ready service.</li><li>Do not erase partial failures from the platform scorecard.</li></ul>"
)
rows.append(quiz)
by_path[quiz_hub]["data"]["modules"][0]["lessons"].append(quiz_path)
by_path[quiz_hub]["body"] += "<h2>Platform self-service check</h2>" + links([quiz_path])
by_path[quiz_hub]["updated_at"] = stamp

for item in specs:
    row = next(row for row in rows if row["path"] == item["path"])
    row["body"] += "<h2>Practice and check</h2>" + links([project_path, quiz_path])
    row["data"]["related"].extend({"path": path, "title": titles[path]} for path in [project_path, quiz_path])

for source, targets in {
    "devops/cost-capacity-ownership": ["devops/self-service-provisioning-contract", "devops/platform-product-slo-and-adoption"],
    "devops/ephemeral-environment-controls": ["devops/self-service-provisioning-contract", "devops/async-provisioning-state-machine"],
    "devops/terraform-module-contracts": ["devops/golden-path-template-upgrade", "devops/platform-composition-revision-rollout"],
    "devops/namespace-resource-quotas": ["devops/self-service-provisioning-contract"],
    "devops/policy-exception-expiry": ["devops/platform-template-execution-boundary"],
    "devops/runbook-automation-guardrails": ["devops/service-catalog-operational-owner"],
    "devops/provider-quota-preflight": ["devops/async-provisioning-state-machine"],
    "devops/dependency-bulkhead-isolation": ["devops/service-catalog-dependency-evidence"],
    "devops/gitops-fleet-promotion-cohorts": ["devops/platform-composition-revision-rollout"],
    "devops/cost-capacity-recovery-project": [project_path],
}.items():
    row = by_path[source]
    row["body"] += "<h2>Platform operating-contract follow-up</h2>" + links(targets)
    row["data"].setdefault("related", []).extend({"path": target, "title": titles[target]} for target in targets)
    row["updated_at"] = stamp

assert len({row["path"] for row in rows}) == len(rows)
fixture.write_text(json.dumps(rows, ensure_ascii=False, indent=2) + "\n")
print(json.dumps({"new_lessons": len(specs), "new_projects": 1, "new_quiz_banks": 1, "total_records": len(rows)}))
