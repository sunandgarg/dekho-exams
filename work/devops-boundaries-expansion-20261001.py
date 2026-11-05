"""Expand the local DevOps preview with ownership and recovery boundaries."""

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


lesson(
    "service-account-token-boundaries", "Service account tokens: mount only when the workload needs Kubernetes API access",
    "Remove ambient API credentials from Pods that never call the cluster control plane.",
    "A Kubernetes ServiceAccount identifies a workload to the API server. Its token is a credential, not a general-purpose application secret. A Pod may receive an automatically mounted token even when the application never calls the Kubernetes API. The existence of RBAC restrictions lowers the scope of that token but does not make needless exposure desirable.",
    "A document-rendering worker reads jobs from a queue and writes finished PDFs to object storage. It has no reason to list Pods or read Secrets. Assign it a dedicated ServiceAccount with no added RoleBinding and disable automatic token mounting in its Pod template. The manifest shows that boundary but omits queue configuration, resource requests, and probes, which must be added for the real service. Test the container after changing the mount setting; a hidden library that calls the API should fail visibly and trigger an architecture decision, not a silent return to the default account. If a controller really needs API access, grant only the verbs and resources required, use short-lived projected credentials, and check the audience and expiration. Cloud access belongs to a separately reviewed identity mapping rather than a broad Kubernetes Role.",
    "yaml", "apiVersion: v1\nkind: ServiceAccount\nmetadata: {name: document-renderer, namespace: documents}\n---\napiVersion: apps/v1\nkind: Deployment\nmetadata: {name: document-renderer, namespace: documents}\nspec:\n  replicas: 3\n  selector:\n    matchLabels: {app: document-renderer}\n  template:\n    metadata:\n      labels: {app: document-renderer}\n    spec:\n      serviceAccountName: document-renderer\n      automountServiceAccountToken: false\n      containers:\n        - name: renderer\n          image: registry.internal/document-renderer@sha256:REPLACE_WITH_FULL_DIGEST",
    "Separate accounts add a small amount of configuration and review work. They also make audit records easier to attribute and limit the reach of a compromised Pod. A token turned off at the Pod level does not remove other secrets supplied through environment variables, volumes, or node metadata. Inspect all credential paths. A short-lived token still grants its permissions until it expires or its trust is revoked, so avoid permissions that are wider than the work requires.",
    ["Do not run every workload as the namespace default account.", "Do not mount an API token just because RBAC looks narrow.", "Do not confuse a Kubernetes ServiceAccount with a cloud identity grant."],
    ["devops/kubernetes-rbac", "devops/container-runtime-restrictions", "devops/credential-incident-rotation", "devops/secrets-and-configuration"],
)

lesson(
    "federated-workload-identity", "Federated workload identity: replace standing cloud keys with scoped trust",
    "Issue short-lived cloud access to the intended workload identity and environment.",
    "Workload identity federation lets an external identity provider's signed assertion be exchanged for short-lived cloud credentials. The trust policy must bind the expected issuer, audience, subject, repository or namespace, and environment. A valid token from the wrong workflow or Pod should not be enough to assume the production role.",
    "A claims deployment pipeline needs permission to update only its production service. Separate build and deploy jobs. The build job produces a signed artifact without cloud deploy rights; the deploy job runs behind an environment gate and requests a short-lived identity assertion. The policy sketch names the checks that the cloud-side trust rule must enforce; it is not a provider-specific policy document. Test negative cases: a pull request, a branch outside the release rule, and a staging environment must all fail to assume the production role. Rotate or revoke the trust mapping when repository ownership changes. Keep the cloud role's resource permissions narrow, because federation removes stored keys but does not automatically enforce least privilege after exchange.",
    "text", "Production deploy trust contract\nIssuer: approved CI identity provider\nAudience: cloud token-exchange endpoint\nSubject: claims repository, release branch, production environment\nRole scope: update claims service and read deployment state\nNegative tests: pull request, staging job, unrelated repository\nExpiry: short-lived credentials; no stored cloud access key",
    "Federation adds an issuer and claim-mapping dependency to deployment. An outage there can delay releases, so retain a controlled, audited emergency path. Short-lived credentials reduce the time a stolen token remains useful; they do not prevent a malicious job within the permitted subject from deploying. Review job permissions, branch protection, environment approvers, and the trust rule together. Log assumption events without logging raw assertions.",
    ["Do not trust only the issuer while ignoring subject and audience.", "Do not give build jobs production deployment permission.", "Do not store the exchanged token in a long-lived artifact."],
    ["devops/github-actions-security", "devops/credential-incident-rotation", "devops/artifact-promotion", "devops/service-account-token-boundaries"],
)

lesson(
    "terraform-address-refactoring", "Terraform address refactoring: move state without recreating infrastructure",
    "Make an address change explicit and inspect the plan for replacement or destruction.",
    "A Terraform resource address identifies an object in state. Renaming a resource or moving it into a module changes that address even if the cloud object should stay the same. A moved block tells Terraform to associate the old state address with the new configuration address. It is a state mapping, not a command to rename a cloud object or to transfer ownership between separate state backends.",
    "A payments team moves an audit bucket resource into a storage module. Keep the old and new addresses in a reviewed moved block, update configuration, and run a plan under the same state lock. The HCL fragment is only the address mapping; it assumes the destination resource exists in the module and refers to the same provider object. The plan should show a move, with no create or destroy for that bucket. Retain the block while older workspaces or branches may still hold the old address. If ownership must move between separate state files, use a planned remove-and-import procedure with state backups and one writer at a time. Do not edit remote state JSON by hand because a plan looks inconvenient.",
    "hcl", "moved {\n  from = aws_s3_bucket.payment_audit\n  to   = module.audit_storage.aws_s3_bucket.records\n}",
    "A moved block is cheap at runtime but demands coordination across environments and branches. Removing it too early can turn a later plan into a destroy-and-create operation. State migration across backends is more expensive: it needs locks, backups, a checked import identifier, and a period when two configurations cannot both manage the object. For stateful resources, the cost of an accidental replacement can dwarf the review time. Reject any plan that unexpectedly replaces a bucket containing retained records.",
    ["Do not rename an address and assume Terraform recognizes the old object.", "Do not use a moved block as a cross-backend ownership transfer.", "Do not approve a stateful replacement because the source diff is small."],
    ["devops/terraform-state-and-plan", "devops/terraform-module-contracts", "devops/backup-and-recovery", "devops/cost-capacity-ownership"],
)

lesson(
    "gitops-emergency-change", "GitOps emergency changes: preserve one recorded desired state",
    "Contain an incident without leaving the cluster and repository in disagreement.",
    "A GitOps controller repeatedly compares declared configuration with live resources and may restore drift. A manual cluster edit can be overwritten if self-healing is enabled. Pausing reconciliation can keep an urgent fix in place, but it also suspends correction of unrelated drift. The incident procedure needs a bounded pause, an owner, a repository change, and a verified return to reconciliation.",
    "A payments API needs an immediate route correction after an unsafe policy reaches production. First identify the application and exact object the controller owns; record its current revision and health. If a manual correction is necessary, pause or narrowly disable synchronization under an incident record, apply the smallest safe change, and measure the user path. Create the matching repository change before resuming automated sync. The checklist below is a decision record, not a command sequence for a particular controller. Compare live and desired objects after reconciliation restarts; the incident is not closed because kubectl accepted a patch. Revert the temporary pause and verify that a later safe change still deploys. If the incident involves a compromised repository, do not treat that repository as trusted desired state until access is contained.",
    "text", "Emergency GitOps change record\nApplication: payments-api\nLive revision and affected object: captured before edit\nSync pause owner and expiry: named incident commander\nManual change: narrow object patch with user-path check\nRepository repair: reviewed matching revision\nExit gate: sync resumed, live equals desired, service healthy",
    "A pause reduces automated interference but raises drift risk for every object within its scope. Keep it short and visible. A direct patch can be faster than a repository review, yet a forgotten patch will either disappear or remain untracked. Test the recovery path under a disposable application before production, including what happens when a sync window or policy blocks the intended change. Retain the incident record with the exact revisions and operator actions.",
    ["Do not leave synchronization paused after the incident.", "Do not rely on a manual patch surviving self-healing.", "Do not merge an unreviewed repository change only to match a live mistake."],
    ["devops/gitops-reconciliation", "devops/incident-response", "devops/admission-policy-guardrails", "devops/progressive-delivery"],
)

lesson(
    "volume-snapshot-recovery", "Volume snapshots: test application-consistent restore",
    "Separate storage-level capture from a restorable database state.",
    "A Kubernetes VolumeSnapshot asks a compatible storage driver to capture a PersistentVolumeClaim's data. It does not by itself guarantee a transactionally consistent database backup, copy the application's configuration, or prove that another cluster can restore the data. The snapshot controller and CSI driver must support the operation for the chosen storage class.",
    "A ledger service stores its database on a PVC. Quiesce writes or use the database's supported backup protocol before capturing a volume snapshot; record the database position, schema version, image digest, and any encryption-key dependency. The manifest requests a snapshot in the same namespace as the source claim. Restore it to a new PVC in a disposable namespace, start the compatible database version, and run a synthetic balance check. Measure elapsed restore time and recovered transaction position against the recovery objectives. A snapshot kept in the same failure domain can vanish with the storage system; copy or export recovery data according to the failure model. Keep independent backups for bad writes that were already reflected in recent snapshots.",
    "yaml", "apiVersion: snapshot.storage.k8s.io/v1\nkind: VolumeSnapshot\nmetadata: {name: ledger-checkpoint-47, namespace: ledger}\nspec:\n  volumeSnapshotClassName: ledger-csi-snapshots\n  source:\n    persistentVolumeClaimName: ledger-data",
    "Snapshots consume storage and can incur transfer cost when copied across regions. Fast capture often shifts work to restore time, when blocks must be rehydrated before the database meets its latency target. A successful snapshot status proves a storage operation, not application integrity. Test restores with realistic data size and key access. Track retention and deletion separately from the source PVC so routine cleanup cannot erase the only usable recovery point.",
    ["Do not call a crash-consistent disk image a verified database backup.", "Do not keep every recovery point in the same failure domain.", "Do not skip the restore drill after a successful snapshot event."],
    ["devops/persistent-storage", "devops/backup-and-recovery", "devops/database-change-safety", "devops/multi-region-failover"],
)

lesson(
    "certificate-renewal-path", "Certificate renewal: verify the served certificate after issuance",
    "Test issuer, Secret update, workload reload, and the external TLS handshake as one path.",
    "Certificate renewal replaces an expiring certificate before clients reject it. In Kubernetes, a certificate controller may update a Secret successfully while an ingress or application still serves the old certificate. The operational unit is the entire path from issuance through reload to the hostname seen by clients, including private-key access and any intermediate chain.",
    "A parcel gateway terminates TLS for a customer-facing hostname. Create a Certificate resource using an existing approved issuer, set the expected DNS name, and alert with enough time to investigate failures before expiry. The fragment names a Secret for the gateway to consume; it assumes the issuer and gateway wiring already exist. In a test environment, trigger a renewal through the controller's supported mechanism, inspect the new certificate's validity, then connect to the external hostname and verify which certificate is actually served. Confirm that a reload does not cut active connections beyond the service target. If the gateway caches the old Secret, fix its reload path rather than repeatedly deleting and recreating credentials. Protect the private key with narrow namespace access and backup rules that match the issuer model.",
    "yaml", "apiVersion: cert-manager.io/v1\nkind: Certificate\nmetadata: {name: parcel-edge, namespace: parcels}\nspec:\n  secretName: parcel-edge-tls\n  dnsNames: [parcels.internal.example]\n  issuerRef:\n    name: parcel-edge-issuer\n    kind: Issuer",
    "Automatic issuance reduces routine manual work but adds controller, DNS or challenge, and gateway dependencies. A certificate can be Ready while the client still sees an expired one. Monitor expiry from outside the cluster as well as controller status. Renewal may rotate keys and trigger a rollout; test how that affects long-lived connections and pinning clients. The hostname is illustrative. Do not assume a Secret update reaches every edge replica at the same instant.",
    ["Do not equate Certificate Ready with a successful client handshake.", "Do not delete the TLS Secret as the default rotation procedure.", "Do not log or broadly copy private-key material."],
    ["devops/dns-tls-edge", "devops/gateway-api-routing", "devops/alert-design", "devops/credential-incident-rotation"],
)

lesson(
    "egress-dns-contract", "Egress policy and DNS: restrict destinations without breaking name resolution",
    "Start with observed traffic, then deny unexpected outbound paths and test DNS explicitly.",
    "A Kubernetes NetworkPolicy can restrict egress from selected Pods when the cluster networking plugin enforces it. Once egress isolation applies, a workload may lose DNS resolution unless a matching rule permits traffic to the cluster's DNS service. Standard NetworkPolicy matches Pods, namespaces, and IP ranges; it is not a portable policy language for filtering arbitrary domain names.",
    "A claims processor must reach a queue inside the cluster and one approved external document endpoint. Inventory actual destinations and ports before applying deny rules. The fragment is a default-deny egress policy for the claims processor; it intentionally has no allow rules and will break both queue access and DNS until narrow companion policies are added. Apply it first in a disposable namespace, then permit DNS to the labeled DNS Pods on the observed port and the exact internal service path. Handle the external destination with an egress gateway or policy capability supported by the chosen network stack, not an invented DNS selector. Test name lookup, the approved call, and a denied destination from inside the selected Pod. Capture the policy engine's decision signal when available.",
    "yaml", "apiVersion: networking.k8s.io/v1\nkind: NetworkPolicy\nmetadata: {name: claims-deny-egress, namespace: claims}\nspec:\n  podSelector:\n    matchLabels: {app: claims-processor}\n  policyTypes: [Egress]",
    "Egress restrictions add policy maintenance as services and DNS paths change. Excessively broad CIDR allows can create a hidden escape path; overly narrow rules can stop critical callbacks or telemetry. DNS answers may change independently of IP-based policy. Verify enforcement with the installed network plugin and run a negative connectivity test; a policy object accepted by the API server does not prove traffic is blocked. Watch blocked requests during rollout, including startup-time dependency checks.",
    ["Do not assume a default-deny egress policy leaves DNS working.", "Do not claim standard NetworkPolicy filters by hostname.", "Do not call a policy effective without testing a blocked path."],
    ["devops/network-policy-isolation", "devops/kubernetes-service-discovery", "devops/dns-tls-edge", "devops/observability-signals"],
)

lesson(
    "overload-shedding", "Overload shedding: refuse excess work before latency collapses",
    "Put a queue and concurrency limit at the service boundary, with a client retry contract.",
    "Overload shedding rejects work a service cannot finish within its deadline. It is different from a crash or silent queue growth: the caller receives an explicit response, and the service protects capacity for work already admitted. Autoscaling may add capacity, but it reacts after measurement and cannot help when a shared database, signer, or queue is the bottleneck.",
    "A document-signing API has 47 workers and a measured capacity of 82 concurrent signing requests. Admit work only while the bounded queue remains below its deadline-based limit; reject excess requests with a retryable status and a short, bounded retry hint. The text policy is an application contract, not a proxy configuration. Choose which requests retain priority: a completion callback may matter more than a new preview request. Test with a burst that exceeds capacity and verify that admitted operations still complete within the objective. Measure rejected requests separately from failures, because hiding the shed rate makes the dashboard look healthy while users are refused. Clients must use jitter and a total deadline; identical immediate retries can make the overload worse.",
    "text", "Document signing admission policy\nWorkers: 47\nMeasured safe in-flight work: 82 requests\nQueue admission: only if predicted finish fits deadline\nOver-capacity result: explicit retryable response\nClient contract: bounded attempts, jitter, stable operation key\nMeasure: admitted latency, shed rate, downstream saturation",
    "A small queue improves latency under overload but rejects more requests; a large queue increases apparent acceptance while many requests expire before service. The correct limit depends on service time distribution, not only worker count. Reserved capacity for high-priority operations can protect core workflows but needs fairness rules to prevent starvation. Test the behavior when telemetry or the admission counter fails, and decide whether to fail closed or use a conservative static limit.",
    ["Do not use an unbounded queue to disguise overload.", "Do not let clients retry shed work immediately in sync.", "Do not measure only admitted requests when reporting availability."],
    ["devops/retry-timeout-budgets", "devops/horizontal-autoscaling", "devops/capacity-load-testing", "devops/service-level-objectives"],
)

lesson(
    "release-evidence-record", "Release evidence: tie one deployed digest to one approval decision",
    "Record the artifact, configuration, tests, and actual runtime revision together.",
    "A release evidence record connects a proposed change to the artifact deployed and the health observed after exposure. A green CI run tied only to a branch name is weak evidence because the branch, dependencies, and environment can change. The record should identify immutable inputs and the decision that moved them into an environment.",
    "A shipment API release packet includes commit, image digest, chart or manifest revision, database migration compatibility, build attestations, security gate result, approving operator, deployment timestamp, and the runtime digest observed in the cluster. The text block is a review schema, not proof that those controls ran. Promote the same image digest tested in staging; change environment configuration through a reviewed revision rather than rebuilding the image. After deployment, read back the running Pods and route a synthetic shipment request through the real edge path. Record both a stop decision and a promotion decision with their thresholds. If the observed digest differs from the approved digest, halt promotion and investigate provenance before deciding that the service looks healthy.",
    "text", "Shipment release packet\nSource commit: immutable revision\nArtifact: full image digest and build attestation\nConfiguration: reviewed manifest revision and values checksum\nGate: test, migration compatibility, security result\nDecision: named approver, time, environment\nObserved runtime: Pod image IDs and edge transaction result\nRecovery: previous digest and compatible schema verified",
    "The packet consumes storage and reviewer time. Automate evidence collection where it reduces transcription error, but keep the approval judgment explicit. Retain records long enough for incident reconstruction and access review; avoid embedding tokens or private customer payloads. A runtime readback closes a common gap between intended and actual deployment. One passing synthetic transaction is a narrow check, so pair it with error and latency monitoring for the rollout window.",
    ["Do not approve a mutable tag as the only artifact identity.", "Do not rebuild separately for each environment and call it one promoted artifact.", "Do not treat an approval record as proof that the intended digest ran."],
    ["devops/artifact-promotion", "devops/supply-chain-verification", "devops/helm-release-review", "devops/progressive-delivery"],
)

lesson(
    "infrastructure-drift-triage", "Infrastructure drift: distinguish emergency repair from unauthorized change",
    "Compare desired configuration with provider state before choosing an apply direction.",
    "Infrastructure drift is a difference between declared configuration, Terraform state, and the real provider object. It may result from an emergency console edit, another controller, provider defaults, or an unreviewed change. A Terraform plan can reveal differences, but it cannot tell operators whether the declared value or the live value is the correct one after an incident.",
    "A storage team notices an encryption setting changed outside its reviewed configuration. Freeze applies to the affected state, preserve audit events, and determine who changed the setting and why. Run a refresh-backed plan in a read-only review context and inspect the exact proposed actions. The shell block records a plan for review but must not be used to apply without deciding ownership. If the live setting is a valid emergency repair, update code through review and confirm the next plan is clean. If the change is unauthorized, contain access first, then restore the approved value with a controlled apply. Check dependent services and data before declaring recovery; changing a property back may not undo data created during the drift interval.",
    "bash", "terraform init -input=false\nterraform plan -input=false -out=drift-review.tfplan\nterraform show -no-color drift-review.tfplan",
    "Plan review consumes operator time and provider API calls, but an automatic revert can worsen an incident when live state carries a needed repair. A saved plan can include sensitive values; store and delete it under the same controls as state. Refresh may be delayed by provider consistency and does not detect every external effect. Monitor drift on a cadence that matches resource risk, and avoid running multiple controllers against the same setting without an explicit owner.",
    ["Do not auto-apply a drift plan before understanding the live change.", "Do not leave a saved plan in an unrestricted CI artifact.", "Do not confuse a clean plan with proof that external data is intact."],
    ["devops/terraform-state-and-plan", "devops/terraform-address-refactoring", "devops/incident-response", "devops/cost-capacity-ownership"],
)


titles = {row["path"]: row["title"] for row in rows}
titles.update({item["path"]: item["title"] for item in specs})
project_path = "devops/reconcile-production-boundaries-project"
quiz_path = "quizzes/devops-ownership-and-recovery"
titles[project_path] = "Project: reconcile production boundaries"
titles[quiz_path] = "DevOps ownership and recovery decisions"
for item in specs:
    assert all(target in titles for target in item["related"]), item["path"]


def links(paths):
    return "<ul>" + "".join(f'<li><a href="/{html.escape(path)}">{html.escape(titles[path])}</a></li>' for path in paths) + "</ul>"


groups = [
    ("Identity and deployment ownership", "Scope workload credentials and record one approved release.", ["service-account-token-boundaries", "federated-workload-identity", "gitops-emergency-change", "release-evidence-record"]),
    ("Infrastructure state and recovery", "Refactor state deliberately and test recoverable storage.", ["terraform-address-refactoring", "volume-snapshot-recovery", "infrastructure-drift-triage"]),
    ("Edge and capacity boundaries", "Prove certificate rotation, egress control, and overload behavior.", ["certificate-renewal-path", "egress-dns-contract", "overload-shedding"]),
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
               sort_order=18000 + order, published_at=stamp, created_at=stamp, updated_at=stamp)
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
               summary="Run an identity, drift, certificate, and restore exercise with an auditable release packet.",
               difficulty="Advanced", sort_order=18090,
               published_at=stamp, created_at=stamp, updated_at=stamp)
project["data"] = {"kind": "project", "reading_minutes": 9,
                   "author_path": "authors/aitrove-editorial", "subject_root": course,
                   "section_path": project_hub, "content_format": "html", "seo_ready": True,
                   "related": [{"path": target, "title": titles[target]} for target in ["devops/federated-workload-identity", "devops/infrastructure-drift-triage", "devops/volume-snapshot-recovery", "devops/release-evidence-record"]]}
project["body"] = (
    "<p>This project tests whether one service can be deployed, observed, and recovered through declared ownership boundaries. Use a disposable cluster, a test cloud account, and synthetic financial records. State the stop conditions before exercising any fault; do not use production credentials or a real customer database.</p>"
    "<h2>Build the release packet</h2><p>Build one ledger API image and record its digest. Give the workload a dedicated ServiceAccount with no automatic API token if the application does not call Kubernetes. Permit deployment through a short-lived federated identity bound to the test repository and environment. Record the approved image, configuration revision, operator, and observed runtime digest. Issue a test certificate and verify the externally served result after renewal.</p>"
    "<pre><code class=\"language-text\">Boundary exercise evidence\nArtifact: one approved image digest\nIdentity: allowed test job and rejected unrelated job\nDrift: provider audit event and reviewed Terraform plan\nRecovery: snapshot, new PVC, compatible database check\nEdge: renewed certificate observed by external client\nExit: desired state reconciled and temporary access revoked</code></pre>"
    "<h2>Inject and recover</h2><p>Change one harmless test infrastructure setting outside Terraform, pause applies, and capture the audit event and plan. Decide whether to update code or restore the declared value; document why. Capture a database-consistent recovery point, restore it to a new PVC, and verify a synthetic balance. Deny one unapproved egress destination while confirming approved DNS still works. Exercise a controlled overload burst and record admitted latency plus rejected work. End with a clean desired-state comparison and revoke all temporary identities.</p>"
    "<h2>Cost and verification</h2><p>The test uses temporary compute, storage snapshots, certificate issuance, and operator time. A successful controller status is not enough: attach the actual client handshake, restored query, denied identity exchange, and provider plan result. Record any check that could not run as unverified. Remove disposable resources after retaining only approved evidence, and confirm that the final test account no longer has temporary access.</p>"
    "<h3>Common Mistakes</h3><ul><li>Do not treat a green deployment as proof of the intended artifact identity.</li><li>Do not call a snapshot usable until a compatible restore has been tested.</li><li>Do not leave a reconciliation pause or temporary trust rule active.</li></ul>"
    "<h2>Connected lessons</h2>" + links(["devops/service-account-token-boundaries", "devops/federated-workload-identity", "devops/infrastructure-drift-triage", "devops/volume-snapshot-recovery", "devops/certificate-renewal-path", "devops/egress-dns-contract", "devops/overload-shedding", "devops/release-evidence-record", project_hub]))
rows.append(project)
project_index = by_path[project_hub]
project_index["data"]["modules"][0]["lessons"].append(project_path)
project_index["body"] += "<h2>Production boundaries exercise</h2>" + links([project_path])
project_index["updated_at"] = stamp

questions = [
    ("When should a Pod disable automatic ServiceAccount token mounting?", ["When it does not need Kubernetes API access", "Whenever it runs in production", "Only after it receives cluster-admin"], 0, "Unneeded ambient credentials should not be exposed to the container."),
    ("What must a federated production trust rule bind?", ["Issuer, audience, and intended subject or environment", "Only the repository display name", "Only the cloud region"], 0, "The allowed workload must be distinct from unrelated jobs."),
    ("What is a moved block for?", ["Mapping an old Terraform state address to a new address", "Transferring two remote state backends automatically", "Renaming a cloud object at its provider"], 0, "It records the address change inside a configuration's state."),
    ("What should follow a manual GitOps incident patch?", ["A reviewed desired-state repair and resumed reconciliation", "A permanent sync pause", "Deletion of the repository"], 0, "The live and declared states must converge again."),
    ("What proves a volume snapshot is usable for a database?", ["A compatible restore and application-level integrity check", "Snapshot object creation alone", "The source PVC still being Bound"], 0, "Capture status does not establish transaction consistency or restore success."),
    ("What proves a renewed edge certificate reached clients?", ["An external handshake to the actual hostname", "A Secret update alone", "A green Pod phase"], 0, "The serving edge can retain an older certificate."),
    ("What commonly breaks after default-deny egress?", ["DNS unless narrowly permitted", "Only incoming HTTP requests", "Terraform state locking"], 0, "Name lookup is outbound traffic from the selected Pods."),
    ("Why use a bounded queue during overload?", ["To reject work that cannot meet its deadline", "To guarantee zero rejections", "To hide downstream saturation"], 0, "Unbounded waiting converts overload into latency and timeouts."),
    ("What closes the artifact-identity gap after deployment?", ["Read back the digest running in the environment", "Trust the branch name", "Retag the image after approval"], 0, "The runtime revision must match the approved artifact."),
    ("What should happen before applying a drift plan?", ["Determine whether the live change is valid and who owns it", "Always auto-revert", "Delete the state file"], 0, "A live emergency repair may be the correct current state."),
    ("What should a federation negative test attempt?", ["Assumption from an unrelated job or environment", "Only the approved production job", "Only a local syntax parse"], 0, "Trust boundaries require proof of denial as well as success."),
    ("What makes an overload report honest?", ["Counting rejected requests alongside admitted latency", "Reporting only completed requests", "Ignoring client retries"], 0, "A low latency among admitted requests can conceal rejected users."),
]
quiz = copy.deepcopy(by_path["quizzes/devops-operations"])
quiz.update(id=str(uuid.uuid5(uuid.NAMESPACE_URL, "aitrove:" + quiz_path)), path=quiz_path,
            title=titles[quiz_path], summary="Twelve decisions on identity, drift, restore, TLS, egress, and overload.",
            sort_order=18100, published_at=stamp, created_at=stamp, updated_at=stamp)
quiz["data"] = {"subject_root": course, "section_path": quiz_hub, "content_format": "html",
                "author_path": "authors/aitrove-editorial", "seo_ready": True, "duration_minutes": 12,
                "related": [{"path": target, "title": titles[target]} for target in ["devops/service-account-token-boundaries", "devops/terraform-address-refactoring", "devops/volume-snapshot-recovery", "devops/egress-dns-contract", "devops/overload-shedding"]],
                "questions": [dict(prompt=prompt, options=options[index % 3:] + options[:index % 3],
                                   answer=(answer - index % 3) % 3, explanation=explanation)
                              for index, (prompt, options, answer, explanation) in enumerate(questions)]}
quiz["body"] = "<p>Choose the decision that preserves a verified production boundary. Review the linked lesson for the reasoning behind each answer.</p><h2>Review these lessons</h2>" + links([item["path"] for item in quiz["data"]["related"]]) + "<h2>Other checks</h2>" + links([quiz_hub, "quizzes/devops-delivery", "quizzes/devops-operations", "quizzes/devops-platform-reliability", "quizzes/devops-advanced-delivery", "quizzes/devops-resilience-and-response"]) + "<h3>Common Mistakes</h3><ul><li>Do not confuse a configured control with a tested denial.</li><li>Do not confuse storage capture with an application restore.</li></ul>"
rows.append(quiz)
quiz_index = by_path[quiz_hub]
quiz_index["data"]["modules"][0]["lessons"].append(quiz_path)
quiz_index["body"] += "<h2>Ownership and recovery check</h2>" + links([quiz_path])
quiz_index["updated_at"] = stamp

for item in specs:
    row = next(row for row in rows if row["path"] == item["path"])
    row["body"] += "<h2>Practice and check</h2>" + links([project_path, quiz_path])
    row["data"]["related"].extend({"path": target, "title": titles[target]} for target in [project_path, quiz_path])

for source, targets in {
    "devops/kubernetes-rbac": ["devops/service-account-token-boundaries", "devops/federated-workload-identity"],
    "devops/github-actions-security": ["devops/federated-workload-identity"],
    "devops/terraform-module-contracts": ["devops/terraform-address-refactoring"],
    "devops/gitops-reconciliation": ["devops/gitops-emergency-change"],
    "devops/persistent-storage": ["devops/volume-snapshot-recovery"],
    "devops/dns-tls-edge": ["devops/certificate-renewal-path", "devops/egress-dns-contract"],
    "devops/network-policy-isolation": ["devops/egress-dns-contract"],
    "devops/capacity-load-testing": ["devops/overload-shedding"],
    "devops/artifact-promotion": ["devops/release-evidence-record"],
    "devops/terraform-state-and-plan": ["devops/infrastructure-drift-triage"],
}.items():
    row = by_path[source]
    row["body"] += "<h2>Advanced follow-up</h2>" + links(targets)
    row["data"].setdefault("related", []).extend({"path": target, "title": titles[target]} for target in targets)
    row["updated_at"] = stamp

assert len({row["path"] for row in rows}) == len(rows)
fixture.write_text(json.dumps(rows, ensure_ascii=False, indent=2) + "\n")
print(json.dumps({"new_lessons": len(specs), "new_projects": 1,
                  "new_quiz_banks": 1, "total_records": len(rows)}))
