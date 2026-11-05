"""Add advanced DevOps packaging, routing, policy, and recovery lessons."""

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


def lesson(slug, title, summary, definition, practice, language, sample, cost, mistakes, related):
    path = "devops/" + slug
    assert path not in by_path
    specs.append(dict(path=path, title=title, summary=summary, definition=definition,
                      practice=practice, language=language, sample=sample,
                      cost=cost, mistakes=mistakes, related=related))


lesson("helm-release-review", "Helm release review: render before applying",
       "Inspect the exact Kubernetes objects produced by a chart and values revision.",
       "A Helm chart is a package of Kubernetes templates and default values. A release is an installed instance of that chart. Values files alter the rendered objects, so a chart version alone does not identify the manifest that reached the cluster. A release review should include the chart revision, environment values, rendered diff, and the image digest that workload templates reference.",
       "For a receipt API, pin the chart in source control, keep nonsecret environment values in a reviewed file, and render the proposed release in CI. Compare that output with the current cluster objects before promotion. Check changed resource requests, Service selectors, probes, role bindings, and deletion of objects—not only the container image. The shell sequence below validates and renders a local chart without applying it. It assumes the chart and values file exist in the repository. Store the rendered output as review evidence with controlled retention; a chart may emit secret values from inputs, so do not publish the output blindly. Helm rollback restores a release revision's manifests, but a database migration and external side effects may remain. Test rollback compatibility before relying on the command during an incident.",
       "bash", "helm lint ./charts/receipt-api -f release/production-values.yaml\nhelm template receipt-api ./charts/receipt-api \\\n  --namespace receipts \\\n  -f release/production-values.yaml \\\n  > release/rendered-receipt-api.yaml\nkubectl diff -n receipts -f release/rendered-receipt-api.yaml",
       "Rendering and diffing cost little compared with an outage, though large charts can produce review noise. A changed default in a chart dependency can alter objects without an obvious edit to the environment values file; pin dependencies and inspect the rendered result. The diff command needs cluster read access, and its exit code can report differences rather than an operational failure. Do not treat a clean lint result as proof that the new Pods will schedule or become ready.",
       ["Do not review values while ignoring the rendered objects.", "Do not commit secret values to a chart or public render log.", "Do not assume Helm rollback reverses data changes."],
       ["devops/gitops-reconciliation", "devops/kubernetes-deployments", "devops/database-change-safety"])

lesson("gateway-api-routing", "Gateway API routing: accepted route versus working request",
       "Bind a hostname and path to the intended Service, then test the edge path.",
       "An HTTPRoute declares HTTP routing rules that attach to a Gateway listener and send matching requests to backend Services. The Gateway controller reports whether it accepted the route. Acceptance is a control-plane status, not a successful client transaction: DNS, TLS, backend endpoints, policy, and application behavior still determine whether the request works.",
       "A claims portal serves its case API under a path prefix. Give the HTTPRoute an explicit hostname and parent Gateway, then inspect its status conditions after applying. Verify that the named Gateway allows the route's namespace and that the backend Service has ready endpoints. The example assumes an existing public Gateway in the same namespace and a Service called claims-api on port 8080. It routes only the /cases prefix; another route must handle unrelated paths. Test the exact hostname over TLS from outside the cluster, including a missing case, a slow request, and a request during rollout. If a route is accepted but the backend is missing, inspect ReferenceResolved and backend health rather than changing DNS at random. Keep authentication and authorization in the correct edge or application layer; a route match is not an access decision.",
       "yaml", "apiVersion: gateway.networking.k8s.io/v1\nkind: HTTPRoute\nmetadata: {name: claims-cases, namespace: claims}\nspec:\n  parentRefs:\n    - name: claims-public\n  hostnames: [claims.internal.example]\n  rules:\n    - matches:\n        - path: {type: PathPrefix, value: /cases}\n      backendRefs:\n        - {name: claims-api, port: 8080}",
       "A Gateway controller and its data plane consume capacity even when the application is idle. Path rules can overlap, so review route conflicts and host ownership before adding another team to a shared Gateway. The hostname is illustrative. Status conditions may lag reconciliation; collect both controller status and an external request result. A Service port mismatch can produce a bad backend while the route object itself parses correctly.",
       ["Do not equate Accepted with a healthy client response.", "Do not assume a route may attach across namespaces without permission.", "Do not use path routing as a substitute for authorization."],
       ["devops/kubernetes-service-discovery", "devops/dns-tls-edge", "devops/network-policy-isolation"])

lesson("ci-cache-boundaries", "CI dependency caches: speed without hidden build inputs",
       "Treat restored cache content as untrusted and keep the lockfile authoritative.",
       "A dependency cache stores files that are expensive to fetch again. It is a performance aid, not a release artifact and not a source of truth for versions. A build must be able to succeed from a clean runner using its lockfile and trusted registries when the cache is absent. Cache access and writes also form a security boundary because one workflow may restore files saved by another.",
       "For a Node-based audit portal, cache package download data keyed to the lockfile and toolchain, then run npm ci so the dependency tree is still checked against the committed lock. Do not cache node_modules across untrusted branches as though it were reviewed source. Keep tokens, generated credentials, and private configuration out of cache paths. The shell block demonstrates the clean install and test steps after a cache restore; the hosting workflow still needs an explicit cache rule and a read-only trust posture for outside pull requests. Measure cold and warm builds separately. If a cache hit saves only a few seconds but expands attack surface or invalidation work, remove it. A cache miss should slow the job, not change the package set or produce a different image digest without explanation.",
       "bash", "node --version\nnpm ci --prefer-offline\nnpm run lint\nnpm test\nnpm run build",
       "Caches consume storage and can increase debugging time when keys are too broad. A lockfile-keyed cache narrows stale reuse but still must be treated as untrusted input; package-manager integrity checks and a clean install help. npm ci removes an existing node_modules directory before installation and fails when the lockfile disagrees with package metadata. That behavior is useful for repeatability, but installation scripts can still execute, so review dependency trust and runner permissions. Do not compare a warm-cache build with a cold build as if their timing had the same conditions.",
       ["Do not cache secrets or credentials.", "Do not promote a cache as if it were a verified artifact.", "Do not let an untrusted workflow overwrite a trusted release cache."],
       ["devops/continuous-integration", "devops/self-hosted-runner-isolation", "devops/artifact-promotion"])

lesson("trace-context-propagation", "Distributed traces: preserve context without leaking data",
       "Follow one user operation across services while limiting what travels with it.",
       "A trace links spans from the same operation through a trace identifier and propagated context. Propagation lets a downstream service attach work to the caller's trace. It does not prove the caller is authorized, and trace headers from an external client can be malformed or forged. Baggage fields may travel across service boundaries, so they are unsuitable for credentials or personal data.",
       "A parcel API calls a pricing service and a document renderer. Propagate trace context through the approved library rather than manually copying an unvalidated header. Record stable operation names and service identity; put a bounded deployment version attribute on spans so an incident can compare old and new releases. Do not attach full addresses or customer names. The shell request below supplies a syntactically valid traceparent header to a local diagnostic endpoint; it tests propagation only when both services export spans to an observable backend. Inspect whether all three spans share the trace ID and whether the edge sanitizes incoming context according to the trust policy. If sampling drops the request, a missing trace is not proof no work occurred; logs and metrics must still describe the user failure.",
       "bash", "curl --fail --show-error \\\n  -H 'traceparent: 00-c4e2b6114e3047bb91ef681ca5f8a370-b84c2271f8a3d965-01' \\\n  127.0.0.1:8147/diagnostics/parcel-price",
       "Traces consume network and storage proportional to request volume, span count, and sampling policy. Head sampling is cheap but may miss rare failures; retaining every trace can be expensive. Keep span attributes low in cardinality when aggregating and set retention appropriate to incident review. Propagating internal trace identifiers to outside endpoints can reveal architecture details, so decide where context is stripped. A trace is a debugging record, not a security token or proof of business success.",
       ["Do not put secrets or personal data in baggage.", "Do not trust incoming trace headers as authorization.", "Do not conclude that an unsampled request never happened."],
       ["devops/observability-signals", "devops/alert-design", "devops/incident-response"])

lesson("feature-flag-release", "Feature flags: stop exposure without pretending code vanished",
       "Separate deployment from activation and give a risky feature a tested off path.",
       "A feature flag selects behavior at runtime. It can reduce exposure before or after a code deployment, but disabling it does not reverse database writes, queue messages, or an incompatible API response already sent. A safe flag has a default, owner, target group, expiry or removal plan, and observable result.",
       "For a settlement batch algorithm, deploy code with the new path off by default, then enable it for one internal tenant after a test that exercises the complete ledger write. Observe duplicate-write rate and reconciliation delay before expanding the audience. The policy record below is an editorial release contract, not a vendor API. The application must evaluate the flag at the correct decision point and use a stable targeting key; changing cohorts between requests can make diagnosis difficult. Test flag-provider failure and stale-cache behavior. The off path must remain compatible with the current schema until the rollback window closes. Record the flag state and cohort in operational telemetry without making tenant IDs high-cardinality metric labels. Remove the flag after the migration finishes so two permanent code paths do not accumulate.",
       "yaml", "feature: settlement_batch_v2\nowner: settlements-oncall\ndefault: false\nfirstCohort: internal-ledger\nstopWhen:\n  duplicateWrites: 1\n  reconciliationDelayMinutes: 17\nremoveAfterRelease: ledger-054",
       "Flag evaluation adds a small runtime dependency and creates a second behavior path to test. Keeping old and new paths for months multiplies test combinations and operational confusion. A remotely controlled flag can be fast to switch, but provider outages or propagation delays mean not every instance changes at once. Define the failure default and measure actual exposure. The sample stop thresholds are scenario values; choose limits from service impact and the release's risk model.",
       ["Do not call a flag switch a data rollback.", "Do not create a flag with no owner or removal plan.", "Do not assume all instances observe a flag change instantly."],
       ["devops/progressive-delivery", "devops/database-change-safety", "devops/service-level-objectives"])

lesson("terraform-module-contracts", "Terraform modules: small interfaces and explicit state owners",
       "Package repeated infrastructure only where the boundary is stable.",
       "A Terraform module groups resources behind input variables and outputs. The root module composes those units and owns a particular state. A module is useful when it captures a repeated architectural decision, such as a private service endpoint, with a clear interface. Wrapping every single resource in a custom module can hide behavior without reducing risk.",
       "A billing platform has one network module and one application endpoint module. Pass the network ID as an input rather than having the endpoint module discover or create an unreviewed network. Pin remote module versions; for a local source, review the same repository revision as the root configuration. The HCL sketch shows a root module call and a returned endpoint ID. It assumes a module directory with matching variables and output; it is not a full provider configuration. Document whether changing each input replaces a resource and who approves that replacement. Keep separate state units for infrastructure with different lifecycle owners, but do not pass secret values through broadly readable outputs. Use a plan to review the actual graph and retain locking for the root state. An attractive module interface does not make a destructive plan safe.",
       "hcl", "module \"billing_endpoint\" {\n  source        = \"./modules/private-service-endpoint\"\n  network_id    = module.billing_network.id\n  service_name  = \"billing-ledger\"\n  owner_team    = \"payments-platform\"\n}\n\noutput \"billing_endpoint_id\" {\n  value = module.billing_endpoint.id\n}",
       "Modules reduce duplication but add versioning and interface maintenance. Deep nesting makes ownership and replacement behavior hard to inspect. Outputs can expose sensitive attributes in state even when marked sensitive in command output, so access to state remains important. A local module moves with the root repository; a remote module must be pinned and upgraded deliberately. Do not run parallel applies against a shared state merely because resources live in different module folders.",
       ["Do not create an abstraction for every single resource by default.", "Do not hide resource replacement behind a harmless-looking variable name.", "Do not treat separate module folders as separate state locks."],
       ["devops/terraform-state-and-plan", "devops/configuration-management", "devops/cost-capacity-ownership"])

lesson("admission-policy-guardrails", "Kubernetes admission policy: reject an unsafe workload before scheduling",
       "Make a narrow validation rule observable before enforcing it.",
       "A ValidatingAdmissionPolicy evaluates matched Kubernetes API requests with CEL expressions. A binding decides where the policy applies and whether a failure is denied, warned, or audited. It can reject a manifest before it reaches a controller; it does not inspect the image's actual contents or prove that an allowed deployment is healthy.",
       "For a payments namespace, require every Deployment container image reference to include a digest marker. Start with a warning binding, inventory the existing violations, and only then switch to denial. The sample includes the policy and a binding scoped to namespaces carrying an explicit enforcement label. The expression checks for the marker, not a full 64-character digest or trusted registry; a production policy should validate the complete reference and pair it with signed-provenance verification. Test CREATE and UPDATE requests, sidecars, and emergency rollback manifests. A fail-closed policy protects the boundary but can block incident mitigation if no approved prior digest exists. Record an exception process with a narrow scope and expiry rather than removing admission controls for the whole cluster.",
       "yaml", "apiVersion: admissionregistration.k8s.io/v1\nkind: ValidatingAdmissionPolicy\nmetadata: {name: require-deployment-digests}\nspec:\n  failurePolicy: Fail\n  matchConstraints:\n    resourceRules:\n      - apiGroups: [apps]\n        apiVersions: [v1]\n        operations: [CREATE, UPDATE]\n        resources: [deployments]\n  validations:\n    - expression: 'object.spec.template.spec.containers.all(c, c.image.contains(\"@sha256:\"))'\n      message: Container images need a digest reference\n---\napiVersion: admissionregistration.k8s.io/v1\nkind: ValidatingAdmissionPolicyBinding\nmetadata: {name: require-deployment-digests-payments}\nspec:\n  policyName: require-deployment-digests\n  validationActions: [Warn]\n  matchResources:\n    namespaceSelector:\n      matchLabels: {policy-tier: payment-enforced}",
       "CEL evaluation costs control-plane work on matched API calls, so keep expressions focused and test admission latency. A Warn action does not block unsafe Deployments; change to Deny only after the inventory and rollback path are ready. Namespace labels are part of the policy boundary and need controlled edit rights. The example does not cover initContainers or ephemeralContainers and only checks for a substring, so it must not be presented as complete image integrity enforcement. An admission failure is a configuration result, not a runtime health signal.",
       ["Do not mistake Warn for enforcement.", "Do not claim a digest substring proves image provenance.", "Do not block rollback without a safe approved revision."],
       ["devops/supply-chain-verification", "devops/kubernetes-rbac", "devops/artifact-promotion"])

lesson("multi-region-failover", "Multi-region failover: define write ownership before moving traffic",
       "Connect the recovery objective to replication, routing, and data consistency.",
       "A regional failover sends users to an alternate location after the primary becomes unavailable. It is not just a DNS switch: the standby needs compatible application code, current enough data, credentials, capacity, and a rule for which location may accept writes. Recovery point and recovery time objectives set the acceptable data gap and interruption window.",
       "A shipping-label service targets a 13-minute recovery point and a 61-minute restoration time. Keep an alternate region provisioned with enough capacity for essential operations, then measure replication lag and test promotion under controlled conditions. The runbook outline below makes write ownership explicit. Before changing traffic, fence the old writer so two regions cannot accept conflicting label numbers. Verify that the standby can read its secrets and that its image digest is compatible with the replicated schema. Route a small synthetic request first, then representative user traffic. If the primary returns after failover, do not automatically reverse traffic; reconcile data and decide how it will become a standby. Record observed data loss and elapsed time during a drill, including operator decision delay rather than only infrastructure startup.",
       "text", "Shipping-label failover drill\nRPO target: 13 minutes\nRTO target: 61 minutes\n1. Verify primary fault and replication lag.\n2. Fence primary writes; appoint one write owner.\n3. Promote standby data and validate schema/image compatibility.\n4. Run a synthetic create-and-read transaction.\n5. Shift traffic in stages and measure user errors.\n6. Keep the former primary isolated pending reconciliation.",
       "A warm standby consumes compute, storage, and replication bandwidth before any incident occurs. A cold restore costs less day to day but may miss a short RTO. Replication can copy bad data or deletion, so independent backups remain necessary. DNS or global routing changes can be delayed by caching. Test the service's complete path, including payment, email, or label providers that may be region-bound. A drill that only promotes a database has not verified that users can complete a transaction.",
       ["Do not switch writes before fencing the old primary.", "Do not assume replication replaces point-in-time backups.", "Do not measure RTO from the moment the standby is ready while excluding detection and decision time."],
       ["devops/backup-and-recovery", "devops/incident-response", "devops/dns-tls-edge"])

lesson("cost-capacity-ownership", "Cloud cost and capacity: assign an owner to each recurring resource",
       "Connect spend to service demand without cutting the headroom needed for recovery.",
       "Infrastructure cost is an operational signal. A cluster may be cheap per idle hour and expensive under autoscaling, retained snapshots, log ingestion, or cross-region transfer. Cost allocation labels and budget alerts make a service's recurring spend visible, but they do not tell a team which resource can safely be removed. Capacity must still meet release surge, peak demand, and recovery objectives.",
       "For a media-processing service, label compute, storage, and telemetry resources with the service and owning team. Review daily cost beside queue age, throughput, request latency, and failed work. A sudden spend increase may be an expected load spike, a retry loop, or an orphaned test environment. The YAML sample is an internal budget record, not a cloud-provider API. Set a response owner and an escalation threshold. Before shrinking a worker group, load-test the new capacity and confirm that old messages can clear within the agreed window. Before reducing log retention, verify incident and audit requirements. Model standby capacity as an intentional recovery expense; deleting it to meet a monthly target can invalidate the stated RTO.",
       "yaml", "service: media-processing\nowner: media-platform\nmonthlyBudgetUnits: 7400\nreviewWhenDailyUnitsAbove: 310\ntrack:\n  - worker-compute\n  - queue-storage\n  - trace-ingest\n  - standby-capacity\nkeepRecoveryCapacity: true",
       "Frequent cost reports and fine-grained labels create monitoring work, but make waste and ownership visible. Autoscaling saves idle compute while increasing bills at peak and sometimes multiplying downstream connections. Deleting an unused test namespace can be low risk; cutting a production replica without measurement is not. The numbers in the sample are invented budget units, not currency or advice. Report savings alongside reliability signals so the team can see whether a cost cut shifted expense into incidents or user delays.",
       ["Do not cut recovery headroom without updating the recovery objective.", "Do not interpret every cost spike as waste.", "Do not leave recurring resources without a named owner."],
       ["devops/capacity-load-testing", "devops/horizontal-autoscaling", "devops/multi-region-failover"])


titles = {row["path"]: row["title"] for row in rows}
titles.update({item["path"]: item["title"] for item in specs})
project_path = "devops/harden-release-project"
quiz_path = "quizzes/devops-advanced-delivery"
titles[project_path] = "Project: harden a release boundary"
titles[quiz_path] = "DevOps advanced delivery decisions"
for item in specs:
    assert all(target in titles for target in item["related"]), item["path"]


def links(paths):
    return "<ul>" + "".join(f'<li><a href="/{html.escape(path)}">{html.escape(titles[path])}</a></li>' for path in paths) + "</ul>"


groups = [
    ("Release packaging and routes", "Review the rendered release, route attachment, and runtime exposure.", ["helm-release-review", "gateway-api-routing", "feature-flag-release"]),
    ("Trusted build inputs", "Keep caches disposable and verify admission evidence before deployment.", ["ci-cache-boundaries", "admission-policy-guardrails"]),
    ("Cross-service evidence", "Connect traces to user impact without propagating private data.", ["trace-context-propagation"]),
    ("Infrastructure ownership and recovery", "Keep module, cost, and failover contracts explicit.", ["terraform-module-contracts", "cost-capacity-ownership", "multi-region-failover"]),
]
hub = by_path[course]
for title, summary, slugs in groups:
    paths = ["devops/" + slug for slug in slugs]
    hub["data"]["modules"].append({"title": title, "summary": summary, "lessons": paths})
    hub["body"] += f"<h2>{html.escape(title)}</h2><p>{html.escape(summary)}</p>" + links(paths)
hub["updated_at"] = stamp


for order, item in enumerate(specs):
    path = item["path"]
    row = copy.deepcopy(by_path["devops/continuous-integration"])
    row.update(id=str(uuid.uuid5(uuid.NAMESPACE_URL, "aitrove:" + path)), path=path,
               title=item["title"], summary=item["summary"], subject="devops",
               category="DevOps", difficulty="Advanced", tags=["devops", "operations"],
               sort_order=17600 + order, published_at=stamp, created_at=stamp, updated_at=stamp)
    row["data"] = {"kind": "tutorial", "reading_minutes": 6,
                   "author_path": "authors/aitrove-editorial", "subject_root": course,
                   "section_path": course, "content_format": "html", "seo_ready": True,
                   "related": [{"path": target, "title": titles[target]} for target in item["related"]]}
    row["body"] = (f"<p>{html.escape(item['definition'])}</p><h2>Operational decision</h2>"
                   f"<p>{html.escape(item['practice'])}</p>"
                   f'<pre><code class="language-{item["language"]}">{html.escape(item["sample"])}</code></pre>'
                   f"<h2>Cost and verification</h2><p>{html.escape(item['cost'])}</p>"
                   + "<h3>Common Mistakes</h3><ul>"
                   + "".join(f"<li>{html.escape(mistake)}</li>" for mistake in item["mistakes"])
                   + "</ul><h2>Connected lessons</h2>" + links([course, *item["related"]]))
    rows.append(row)


project = copy.deepcopy(by_path["devops/practice-project"])
project.update(id=str(uuid.uuid5(uuid.NAMESPACE_URL, "aitrove:" + project_path)),
               path=project_path, title=titles[project_path],
               summary="Gate one release on rendered manifests, trace evidence, admission, and a tested off switch.",
               difficulty="Advanced", sort_order=17690,
               published_at=stamp, created_at=stamp, updated_at=stamp)
project["data"] = {"kind": "project", "reading_minutes": 8,
                   "author_path": "authors/aitrove-editorial", "subject_root": course,
                   "section_path": project_hub, "content_format": "html", "seo_ready": True,
                   "related": [{"path": target, "title": titles[target]} for target in ["devops/helm-release-review", "devops/admission-policy-guardrails", "devops/feature-flag-release", "devops/trace-context-propagation"]]}
project["body"] = (
    "<p>This project hardens the release boundary for a settlement API. Use a disposable cluster and synthetic ledger records. Produce a release packet that another operator can inspect before a candidate image reaches users; do not treat the output of one tool as the whole decision.</p>"
    "<h2>Prepare the release</h2><p>Build once and record the full image digest. Render a pinned chart with reviewed values, then compare the output with current objects. Include the Deployment, Service, resource requests, health probes, route, service account, and expected database schema version. Attach an SBOM and provenance to the image digest. Run the admission rule in warning mode first; after existing violations are fixed, change it to denial in the test namespace. Verify that an image reference without a digest is rejected and the approved digest is accepted.</p>"
    "<pre><code class=\"language-text\">Settlement release packet\nCommit: reviewed revision\nImage: full registry digest\nChart: reviewed revision and values checksum\nAdmission: warning inventory, then deny test\nFlag: off by default; owner and expiry recorded\nTrace: one synthetic write across API and ledger worker\nRecovery: previous digest plus compatible schema confirmed</code></pre>"
    "<h2>Expose and recover</h2><p>Deploy with the new path off. Confirm the Gateway route is accepted, then run a synthetic write through the public test hostname and inspect its trace. Enable the feature for one internal account, observe errors and ledger duplicates, and switch it off when a deliberate fault is injected. Check that the old behavior remains compatible with current data. Attempt an approved rollback in the disposable environment and record the result. Close the packet with a named operator, timestamps, and the reason to promote or stop.</p>"
    "<h2>Cost and verification</h2><p>The project consumes temporary cluster capacity, trace storage, and operator review time. A warning-only admission rule does not block a bad release; a full digest reference does not establish provenance. A flag off switch cannot undo completed writes. Preserve the negative tests as evidence, then remove disposable resources. Report any control that could not be exercised instead of marking it passed.</p>"
    "<h3>Common Mistakes</h3><ul><li>Do not deploy a rendered manifest that was not the one reviewed.</li><li>Do not enable a feature before its off path has been tested.</li><li>Do not use a trace as proof that a ledger write committed correctly.</li></ul>"
    "<h2>Reference lessons</h2>" + links(["devops/helm-release-review", "devops/gateway-api-routing", "devops/admission-policy-guardrails", "devops/feature-flag-release", "devops/trace-context-propagation", project_hub]))
rows.append(project)
project_index = by_path[project_hub]
project_index["data"]["modules"][0]["lessons"].append(project_path)
project_index["body"] += "<h2>Release boundary hardening</h2>" + links([project_path])
project_index["updated_at"] = stamp


questions = [
    ("What should a Helm review inspect after values are selected?", ["Rendered Kubernetes objects", "Only the chart name", "Only a release icon"], 0, "Values and dependencies determine the output."),
    ("What does an Accepted HTTPRoute prove?", ["The controller accepted the route configuration", "A client transaction succeeded", "The certificate renewed"], 0, "Data-path health still needs a request test."),
    ("What should happen on a CI cache miss?", ["The build regenerates inputs from the lockfile", "The job deploys the last cache", "The test gate disappears"], 0, "A cache is optional acceleration."),
    ("Where should credentials be placed in trace context?", ["Nowhere", "Baggage", "Every span name"], 0, "Propagated context may cross trust boundaries."),
    ("What can a feature off switch leave behind?", ["Completed data writes", "No code in the image", "A new source branch"], 0, "Runtime exposure control is not data recovery."),
    ("What does a Terraform module folder own automatically?", ["No separate state lock", "A dedicated state backend", "A cloud account"], 0, "State belongs to the root configuration and its backend."),
    ("What does an admission Warn action do?", ["Report a violation without denial", "Reject every request", "Verify image signatures"], 0, "Deny is needed for enforcement."),
    ("What is missing from a digest-substring policy?", ["Full digest and provenance validation", "A matching Service name", "A CPU request"], 0, "The marker alone is weak evidence."),
    ("What comes before shifting writes to a standby region?", ["Fence the old writer", "Delete every backup", "Turn off tracing"], 0, "Two active writers can conflict."),
    ("Does replication replace independent backups?", ["No", "Yes", "Only for small databases"], 0, "Bad writes and deletion can replicate too."),
    ("What should accompany a capacity cost cut?", ["Load and recovery evidence", "Only a lower invoice", "Removal of all alerts"], 0, "Savings must preserve the service objective."),
    ("What is a trace's main role in a release packet?", ["Explain cross-service execution", "Prove authorization", "Prove every data commit"], 0, "A trace is diagnostic evidence."),
]
quiz = copy.deepcopy(by_path["quizzes/devops-operations"])
quiz.update(id=str(uuid.uuid5(uuid.NAMESPACE_URL, "aitrove:" + quiz_path)), path=quiz_path,
            title=titles[quiz_path], summary="Twelve checks on rendered releases, routes, flags, policy, traces, and failover.",
            sort_order=17700, published_at=stamp, created_at=stamp, updated_at=stamp)
quiz["data"] = {"subject_root": course, "section_path": quiz_hub, "content_format": "html",
                "author_path": "authors/aitrove-editorial", "seo_ready": True, "duration_minutes": 12,
                "related": [{"path": target, "title": titles[target]} for target in ["devops/helm-release-review", "devops/gateway-api-routing", "devops/feature-flag-release", "devops/admission-policy-guardrails", "devops/multi-region-failover"]],
                "questions": [dict(prompt=prompt, options=options[index % 3:] + options[:index % 3],
                                   answer=(answer - index % 3) % 3, explanation=explanation)
                              for index, (prompt, options, answer, explanation) in enumerate(questions)]}
quiz["body"] = "<p>Choose the decision supported by the release evidence. Review the linked rule when a result is unclear.</p><h2>Review these lessons</h2>" + links([item["path"] for item in quiz["data"]["related"]]) + "<h2>Other checks</h2>" + links([quiz_hub, "quizzes/devops-delivery", "quizzes/devops-operations", "quizzes/devops-platform-reliability"]) + "<h3>Common Mistakes</h3><ul><li>Do not confuse a parsed object with a healthy request.</li><li>Do not call a flag or rollback a data restore.</li></ul>"
rows.append(quiz)
quiz_index = by_path[quiz_hub]
quiz_index["data"]["modules"][0]["lessons"].append(quiz_path)
quiz_index["body"] += "<h2>Advanced delivery check</h2>" + links([quiz_path])
quiz_index["updated_at"] = stamp


for source, targets in {
    "devops/gitops-reconciliation": ["devops/helm-release-review"],
    "devops/kubernetes-service-discovery": ["devops/gateway-api-routing"],
    "devops/continuous-integration": ["devops/ci-cache-boundaries"],
    "devops/observability-signals": ["devops/trace-context-propagation"],
    "devops/progressive-delivery": ["devops/feature-flag-release"],
    "devops/terraform-state-and-plan": ["devops/terraform-module-contracts"],
    "devops/supply-chain-verification": ["devops/admission-policy-guardrails"],
    "devops/backup-and-recovery": ["devops/multi-region-failover"],
    "devops/capacity-load-testing": ["devops/cost-capacity-ownership"],
}.items():
    row = by_path[source]
    row["body"] += "<h2>Advanced follow-up</h2>" + links(targets)
    row["data"].setdefault("related", []).extend({"path": target, "title": titles[target]} for target in targets)
    row["updated_at"] = stamp

assert len({row["path"] for row in rows}) == len(rows)
fixture.write_text(json.dumps(rows, ensure_ascii=False, indent=2) + "\n")
print(json.dumps({"new_lessons": len(specs), "new_projects": 1,
                  "new_quiz_banks": 1, "total_records": len(rows)}))
