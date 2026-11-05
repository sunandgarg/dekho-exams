"""Add original configuration-delivery contracts to the local DevOps preview."""

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
    "configmap-projection-refresh-boundary",
    "ConfigMap projection: prove when a running process sees a new value",
    "Distinguish a refreshed mounted file from a refreshed application configuration.",
    "A ConfigMap volume can receive updated files after the kubelet observes a change, but that propagation is eventual and depends on its synchronization and cache behavior. A ConfigMap consumed as an environment variable is fixed for the life of the container. A ConfigMap file mounted through subPath does not receive projected updates. Even when the file changes, an application that parsed it once still runs with its earlier in-memory value until it reloads or restarts.",
    "A receipt router reads a routing weight from a mounted configuration file. Update a disposable ConfigMap while observing three timestamps: the API object's resource version, the content visible at the container path, and the router's reported active generation. Use an ordinary directory mount, then repeat with a subPath mount to expose the different behavior. For a process that supports reload, make it reopen the path and validate the complete new document before swapping its active configuration; preserve the previous generation if parsing fails. For an application that cannot reload safely, change the Pod template and perform a controlled rollout instead. Check the value on every replica, not a single Pod. The fragment mounts a directory, which allows the projected file to change; it does not make the application read it again. Keep a per-replica active-generation metric so a partially propagated update is visible during a release.",
    "yaml",
    "apiVersion: v1\nkind: Pod\nmetadata:\n  name: receipt-router-projection-check\n  namespace: checkout\nspec:\n  containers:\n    - name: router\n      image: registry.internal/receipt-router:approved-build\n      volumeMounts:\n        - name: routing\n          mountPath: /etc/receipt-routing\n          readOnly: true\n  volumes:\n    - name: routing\n      configMap:\n        name: receipt-routing-live",
    "Propagation delay can leave replicas on different routing generations for a period. A forced restart removes that delay but creates rollout and capacity cost. Measure API-to-file delay, file-to-active delay, mixed-generation duration, and failed reloads. Do not use a rapid toggle as a distributed synchronization mechanism; a configuration change that requires atomic global cutover needs a separate coordination contract.",
    ["Do not assume an environment variable changes when its ConfigMap changes.",
     "Do not use subPath for a file that must receive projected updates.",
     "Do not call projection success an application reload without checking active behavior."],
    ["devops/secrets-and-configuration", "devops/feature-flag-release", "devops/kubernetes-probes", "devops/gitops-reconciliation"],
)

lesson(
    "immutable-config-release-generation",
    "Immutable configuration: bind each release to one named generation",
    "Make a configuration change create a reviewed Pod-template change and a reversible name.",
    "An immutable ConfigMap refuses data changes after creation. A new configuration generation therefore needs a new object name, and the workload must reference that name to receive it. This makes the release's configuration identity explicit and avoids an in-place change that silently reaches already-running Pods at different times. The object is not a secret and immutability does not validate its contents.",
    "A settlement calculator needs a new rounding policy for one release. Produce a named ConfigMap from a reviewed document, set immutable to true, and record a content digest in the release evidence. Update the Deployment Pod template to point to the new name, then canary the new calculator against synthetic and shadowed production-shaped cases before increasing traffic. The fragment defines only the configuration object; the Deployment reference is a separate reviewed change. Keep the prior immutable object while rollback remains possible. After the rollback window closes, inventory live Pod references, retained ReplicaSets, and disaster-recovery manifests before deleting old generations. Reusing a deleted name is unsafe because old Pods may retain mounts and operators can no longer tell which bytes that name once represented. Prefer a generation name derived from a verified build or policy revision rather than a mutable label such as latest.",
    "yaml",
    "apiVersion: v1\nkind: ConfigMap\nmetadata:\n  name: settlement-rounding-r47\n  namespace: checkout\nimmutable: true\ndata:\n  policy.yaml: |\n    currency: INR\n    rounding: HALF_EVEN\n    minor_unit: 2",
    "Versioned objects consume API storage and need garbage collection. They also make rollback and incident reconstruction cheaper because the workload references a specific generation. Measure failed configuration validations, old-generation object count, mixed-version Pod duration, and rollback time. The cost of retaining a small ConfigMap is usually lower than the cost of losing the exact configuration that produced a financial result, but retention still needs an owner and expiry rule.",
    ["Do not mutate a released generation by deleting and recreating the same name.",
     "Do not purge a prior object while rollback or an old ReplicaSet still references it.",
     "Do not treat immutable as proof that the policy is valid or confidential."],
    ["devops/gitops-reconciliation", "devops/release-evidence-record", "devops/feature-flag-release", "devops/configmap-projection-refresh-boundary"],
)

lesson(
    "required-config-key-startup-gate",
    "Required configuration keys: fail startup before accepting traffic",
    "Make a missing or malformed value visible as a deployment failure.",
    "A Pod that references a required ConfigMap or Secret key cannot start its container when the object or key is absent. Marking the reference optional changes that failure mode into an absent value, which may be worse if the application falls back to an unsafe default. An envFrom source also deserves inspection: keys that cannot become valid environment variable names can be skipped while the Pod continues starting.",
    "A claims service needs an immutable policy generation and a signing key identifier. Use explicit key references instead of sweeping an entire object into the process environment. Create both resources before the rollout, verify their names and keys in the target namespace, and use an init or application startup check to validate syntax and compatibility. The fragment shows a required non-secret key; the signing material should be a separate Secret reference scoped to the component that needs it. Exercise three failure cases in a disposable namespace: missing object, misspelled key, and syntactically invalid policy. The first two should stop container creation; the last needs an application validation failure before readiness. Inspect Pod events and startup logs without printing secret values. Only mark a key optional after defining an explicit safe fallback and a test for that absence. Promote the new Pod only when it reports the expected configuration generation and passes a user-path check.",
    "yaml",
    "apiVersion: v1\nkind: Pod\nmetadata:\n  name: claims-policy-check\n  namespace: checkout\nspec:\n  containers:\n    - name: policy-check\n      image: registry.internal/claims-policy:approved-build\n      env:\n        - name: POLICY_GENERATION\n          valueFrom:\n            configMapKeyRef:\n              name: claims-policy-r47\n              key: generation\n              optional: false",
    "Failing startup early spends rollout time and capacity but prevents a process from serving with guessed configuration. Measure missing-reference events, startup validation failures, time to rollback, and the number of Pods that accepted traffic on an unexpected generation. Explicit references add manifest maintenance; they also make the runtime contract reviewable. A healthy readiness probe is meaningful only if it checks the validated configuration actually used by the request path.",
    ["Do not use optional true to hide an unplanned missing key.",
     "Do not assume envFrom imported every key merely because the container started.",
     "Do not print secret contents while diagnosing a configuration startup error."],
    ["devops/secrets-and-configuration", "devops/kubernetes-probes", "devops/immutable-config-release-generation", "devops/admission-policy-guardrails"],
)

lesson(
    "config-secret-generation-consistency",
    "Configuration pairs: prevent mixed policy and credential generations",
    "Promote a compatible config-and-secret pair rather than two independent live names.",
    "Kubernetes does not provide an atomic update across a ConfigMap and a Secret. A process can see a new non-secret policy with an older credential, or the reverse, if each object is changed independently and projected asynchronously. The safe unit of change is an application-defined compatible generation, with a validation step before it becomes active. A Kubernetes object resource version is not a shared transaction identifier across separate resources.",
    "A payment gateway changes its endpoint audience and client credential together. Create a versioned policy object and a separately controlled credential object, both labeled with a release generation that contains no secret bytes. Test the pair against the target service in a disposable workload before changing the production Pod template to reference both names. If overlap is supported, issue the new credential first, deploy Pods that can authenticate with it, and revoke the old credential only after old Pods and connections drain. If overlap is not supported, schedule a bounded maintenance switch and keep a tested rollback path. The text contract below is suitable for a release review; it is not a substitute for an authentication probe. During rollout, report the policy generation, credential identifier, and successful authenticated transaction from each new Pod. Reject a mismatched pair before readiness, even if both Kubernetes objects exist.",
    "text",
    "Payment gateway release contract\nGeneration: gateway-r47\nPolicy object: gateway-policy-r47\nCredential object: gateway-client-r47\nRequired audience: settlement-v2\nActivation gate: authenticated synthetic transaction succeeds\nRetirement gate: no old Pod or connection uses gateway-client-r46\nRollback: restore the previous compatible pair",
    "Keeping two credential generations valid may extend exposure and billing for a short period, but it avoids an authentication outage during rolling replacement. A hard cutover reduces overlap at the price of a narrower failure window. Measure mixed-generation Pods, failed authentication by generation, old credential use after retirement, and time until a bad pair is rejected. Never put a credential value in a label, annotation, log, or release record.",
    ["Do not assume two API-object updates land atomically in every Pod.",
     "Do not revoke the old credential before old connections are drained and a new transaction is proven.",
     "Do not expose credential bytes while recording the generation pair."],
    ["devops/secret-rotation-rollout", "devops/secrets-and-configuration", "devops/immutable-config-release-generation", "devops/release-evidence-record"],
)

lesson(
    "external-secret-sync-freshness",
    "External secret sync: treat freshness as a monitored runtime contract",
    "Separate a healthy reconciliation object from a current credential in the process.",
    "An external secret controller or CSI integration adds another reconciliation path between an issuer and an application. The issuer can rotate a credential while the cluster copy, mounted file, or process cache remains older. A controller reporting success at one moment does not prove that every Pod has loaded the latest usable value. Refresh intervals, API failures, issuer outages, mount behavior, and application reload rules all affect the age of the credential that handles requests.",
    "A receipt exporter receives a short-lived object-store credential from an external issuer. Record issuance and expiry times without recording the token itself. Set a maximum allowed age that leaves room for retry and clock skew, and alert before expiry rather than after the first failed upload. In a disposable environment, block the controller's issuer access, rotate the credential, and observe the external version, Kubernetes or CSI version, file version, process version, and successful upload. Restore access and measure catch-up time. If the application reads the file once, use a supervised reload or Pod rollout; a changed mount is not enough. If the integration does not create a Kubernetes Secret, do not use a Secret-object check as the only evidence. The policy fragment sets an acceptance rule independent of a particular controller; the implementation must map its own status fields to these checks.",
    "text",
    "Receipt exporter credential freshness contract\nIssued lifetime: 46 minutes\nMaximum active age: 29 minutes\nAlert before expiry: 14 minutes\nEvidence: issuer version, projected version, process version\nRequest proof: upload and read-back with active credential\nFailure action: stop new exports before an expired credential causes repeated retries",
    "Short refresh intervals increase issuer traffic and control-plane work; long intervals increase stale-credential risk. Alert on age and failed authenticated requests together, because a credential can be fresh but invalid for its audience. Model the retry budget against credential lifetime, issuer rate limits, and restart time. Avoid recording the credential value in telemetry; version identifiers and timestamps are enough for correlation.",
    ["Do not equate controller Ready status with the version currently held by a process.",
     "Do not set refresh timing close to credential expiry without a failure margin.",
     "Do not inspect freshness by printing token bytes into logs."],
    ["devops/secret-rotation-rollout", "devops/configmap-projection-refresh-boundary", "devops/alert-design", "devops/credential-incident-rotation"],
)

lesson(
    "secret-workload-create-access-boundary",
    "Secret access: audit workload creation as an indirect read permission",
    "A subject that can run a Pod may be able to expose namespace Secrets without Secret get.",
    "Secret RBAC is not limited to direct get, list, and watch requests. A subject that can create a Pod or a controller that creates Pods in a namespace can often mount a Secret there and arrange for a container to reveal its contents. The namespace and workload-admission boundary therefore matters as much as the Secret-reader role. List and watch permissions can also reveal all Secret data returned by those API operations.",
    "A build automation identity may deploy a claims service but must not gain access to the settlement signing key. Place the signer in a separately administered namespace and give the build identity no workload-creation privilege there. Review permission to create Pods, Deployments, Jobs, and other Pod-producing resources in each namespace, plus permission to alter the service account or Pod template of a trusted workload. In an isolated test cluster, impersonate the identity and attempt to create a Pod that mounts the protected Secret; the admission or authorization check must deny it before scheduling. The command below tests one direct workload permission, but an audit must enumerate controller resources and inherited roles as well. Use audit logs to detect unusual bulk Secret reads and workload creation near sensitive mounts. A Secret volume mounted only into a signer sidecar can narrow exposure inside a trusted Pod, but it does not repair a namespace that accepts arbitrary attacker-controlled Pods.",
    "bash",
    "kubectl auth can-i create pods -n settlement --as=system:serviceaccount:ci:claims-deployer\nkubectl auth can-i create deployments.apps -n settlement --as=system:serviceaccount:ci:claims-deployer\nkubectl auth can-i list secrets -n settlement --as=system:serviceaccount:ci:claims-deployer",
    "Separate namespaces and admission checks add deployment administration and may require a controlled promotion service. They reduce the blast radius of a compromised CI identity. Measure identities with workload-create rights in sensitive namespaces, rejected unauthorized Pod attempts, and broad Secret list or watch grants. A can-i denial is useful evidence for that specific verb and resource; it does not prove that a different controller, impersonation path, or privileged service account cannot reach the same data.",
    ["Do not call a role safe merely because it lacks direct Secret get.",
     "Do not overlook Deployments, Jobs, and other resources that create Pods.",
     "Do not mount a signing key into a container that does not need it."],
    ["devops/kubernetes-rbac", "devops/admission-policy-guardrails", "devops/self-hosted-runner-isolation", "devops/secrets-and-configuration"],
)

lesson(
    "etcd-secret-encryption-rotation",
    "Kubernetes Secret encryption: rotate keys without losing restore access",
    "Treat encryption at rest and key retirement as a data-recovery procedure.",
    "A Kubernetes Secret is not encrypted in the API server's backing store merely because its data field is base64 encoded. API data encryption at rest must be configured for the relevant resource. With an external KMS provider, availability of the key service and old decryption keys becomes part of cluster restore. Changing the first encryption provider or key affects new writes; previously stored objects need a controlled rewrite before an old key can be retired.",
    "A platform team rotates the key used to protect receipt-service Secrets. First inventory control-plane instances, the encryption configuration they actually run, the KMS provider's health, backup age, and the oldest restore point that remains in scope. Stage the new key while keeping the old decrypt path available, restart or reload the API servers according to the platform's supported procedure, and write a disposable Secret to prove new encryption. Re-encrypt existing Secret objects using a reviewed rewrite procedure and verify representative objects can be read after every control-plane instance has converged. Restore an encrypted backup into an isolated cluster with the keys needed by that backup; a successful current-cluster read alone does not prove restore. Retire the old key only when all live objects and retained backups that require it have expired or been migrated. The checklist below intentionally contains no key material.",
    "text",
    "Receipt cluster encryption rotation gates\nNew writes: verified under the intended active key\nExisting objects: rewritten and read back\nAPI servers: all use the reviewed provider order\nKMS: available during reads and failover\nBackup: isolated restore succeeds with retained decrypt keys\nOld key: retired only after live and backup dependencies end",
    "Rewriting every encrypted object creates API and etcd load; schedule and throttle it rather than creating a control-plane incident. Keeping an old key longer expands key-management cost and exposure, yet deleting it early can make backups unreadable. Measure failed decrypt requests, KMS latency and errors, object rewrite progress, and restore success. Encryption at rest protects stored API data, not a Secret copied into a Pod environment, log, image, or unencrypted backup.",
    ["Do not confuse base64 encoding with encryption.",
     "Do not remove the old decrypt key after verifying only a newly written Secret.",
     "Do not claim a backup is restorable until it has been read with its required keys."],
    ["devops/secrets-and-configuration", "devops/encryption-key-rotation-recovery", "devops/immutable-backup-retention", "devops/etcd-quorum-maintenance"],
)

lesson(
    "projected-token-file-refresh",
    "Projected identity tokens: reopen the file and verify its audience",
    "A rotating token file does not refresh a credential cached forever by the client.",
    "A projected ServiceAccount token can be bound to a Pod, limited to an audience, and rotated by the kubelet before expiry. An application that reads the token file only at startup can still present an expired token later. The receiving service must validate the audience and issuer rather than treating any signed cluster token as authorization. A static long-lived token Secret does not provide the same lifecycle.",
    "A settlement exporter uses a projected token to authenticate to an internal broker. Request only the broker audience and a bounded expiration in the Pod volume, then configure the client to reopen the token path before exchange or after a rejected request. The fragment shows the projected source; a consuming container still needs a read-only mount and the broker must verify the audience. In a disposable Pod, inspect token expiry without logging the token, keep the Pod running past the original expiry, and prove that a subsequent broker call uses a renewed token. Send the same token to a test audience that should reject it. Delete the Pod and verify its bound identity can no longer be used after the platform's revocation behavior takes effect. Record token age, refresh failures, and authentication errors by workload identity. If a library caches the file contents indefinitely, replace or wrap that behavior before shortening token lifetimes.",
    "yaml",
    "apiVersion: v1\nkind: Pod\nmetadata:\n  name: settlement-exporter-identity-check\n  namespace: settlement\nspec:\n  automountServiceAccountToken: false\n  serviceAccountName: settlement-exporter\n  containers:\n    - name: exporter\n      image: registry.internal/settlement-exporter:approved-build\n      volumeMounts:\n        - name: broker-identity\n          mountPath: /var/run/broker-identity\n          readOnly: true\n  volumes:\n    - name: broker-identity\n      projected:\n        sources:\n          - serviceAccountToken:\n              path: token\n              audience: settlement-broker\n              expirationSeconds: 2400",
    "Shorter token lives reduce exposure after theft but increase dependence on token refresh and issuer availability. Frequent reads of a local projected file are cheap; repeated remote token exchanges and broker authentication can add latency and rate-limit pressure. Measure refresh lead time, expiry margin, audience rejection, and how quickly the client recovers after a temporary issuer outage. The token belongs to the Pod identity, so preserving it beyond the Pod's lifetime is a design error.",
    ["Do not cache token bytes for the entire container lifetime.",
     "Do not assume a valid signature means the token has the intended audience.",
     "Do not substitute a permanent ServiceAccount token Secret for a rotating projection without accepting the added risk."],
    ["devops/service-account-token-boundaries", "devops/federated-workload-identity", "devops/secret-workload-create-access-boundary", "devops/credential-incident-rotation"],
)

titles = {row["path"]: row["title"] for row in rows}
titles.update({item["path"]: item["title"] for item in specs})
project_path = "devops/configuration-delivery-recovery-project"
quiz_path = "quizzes/devops-configuration-delivery-decisions"
titles[project_path] = "Project: prove configuration and identity delivery during a release"
titles[quiz_path] = "DevOps configuration delivery decisions"
assert all(path in titles for item in specs for path in item["related"])


def links(paths):
    return "<ul>" + "".join(
        f'<li><a href="/{html.escape(path)}">{html.escape(titles[path])}</a></li>'
        for path in paths
    ) + "</ul>"


for heading, summary, slugs in [
    ("Configuration propagation", "Measure projected files, application reloads, and release-bound immutable generations.", ["configmap-projection-refresh-boundary", "immutable-config-release-generation"]),
    ("Startup and generation safety", "Reject missing keys and mismatched policy-credential pairs before readiness.", ["required-config-key-startup-gate", "config-secret-generation-consistency"]),
    ("Secret freshness and access", "Observe issuer-to-process lag and workload creation as an indirect Secret permission.", ["external-secret-sync-freshness", "secret-workload-create-access-boundary"]),
    ("Encryption and rotating identity", "Keep decrypt keys available through restore and reopen projected token files.", ["etcd-secret-encryption-rotation", "projected-token-file-refresh"]),
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
               category="DevOps", difficulty="Advanced", tags=["devops", "operations"],
               sort_order=21200 + index, published_at=stamp, created_at=stamp, updated_at=stamp)
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
               summary="Rehearse configuration freshness, startup gates, Secret access, key rotation, and token expiry.",
               difficulty="Advanced", sort_order=21290,
               published_at=stamp, created_at=stamp, updated_at=stamp)
project["data"] = {"kind": "project", "reading_minutes": 9,
                   "author_path": "authors/aitrove-editorial", "subject_root": course,
                   "section_path": project_hub, "content_format": "html", "seo_ready": True,
                   "related": [{"path": target, "title": titles[target]} for target in project_related]}
project["body"] = (
    "<p>Use a disposable cluster and synthetic credentials. Separate the test namespaces for application, settlement signer, and CI deployer. Prepare an isolated encrypted backup and a restore cluster before experimenting with key retirement. Record the configuration generation and credential identifier, never their sensitive values. The acceptance result is a successful user-path request with the expected active generation, not the mere existence of Kubernetes objects.</p>"
    "<h2>Exercise propagation and startup</h2><p>Update a mounted ConfigMap and measure API-to-file and file-to-process delay on every replica. Repeat through subPath and an environment variable, then document why those paths remain stale. Create a new immutable generation and roll it to a canary while preserving the prior object. Try a missing required object, missing key, and invalid policy; confirm no failing Pod receives traffic. Deliberately publish a policy and credential with mismatched generations and verify that startup validation rejects the pair. Correct both references and prove one authenticated synthetic transaction before promotion.</p>"
    "<pre><code class=\"language-text\">Configuration delivery acceptance gates\nProjection: every replica reports file and active generation\nStartup: missing or malformed required values block readiness\nPairing: policy and credential generation agree\nExternal sync: active credential age stays inside the limit\nAccess: CI identity cannot create a Secret-reading workload\nEncryption: retained backup restores with required decrypt key\nIdentity: broker accepts a refreshed token and rejects wrong audience</code></pre>"
    "<h2>Exercise loss and recovery</h2><p>Block the external issuer, rotate its synthetic credential, and time the lag through controller, mount, process, and successful request. Impersonate the CI deployer and attempt both direct Secret reads and workload creation in the signer namespace. Rotate an isolated cluster's API-data encryption key, rewrite test Secrets, and restore an older encrypted backup while its decrypt key is still available. Keep one projected-token Pod alive beyond its first token's expiry; verify the client reopens the file and that the broker rejects a different audience. For each fault, capture events and metrics without printing Secret or token bytes.</p>"
    "<h2>Cost and verification</h2><p>Report mixed-generation duration, restart capacity, issuer request rate, KMS latency, object rewrite load, token refresh errors, and rollback time. Mark any drill unverified when the cluster or integration does not support it. Keep the old configuration object and decrypt key until the explicit rollback and backup windows close. A YAML parse and an RBAC can-i response are useful checks, but neither proves that the complete runtime path behaved correctly.</p>"
    "<h3>Common Mistakes</h3><ul><li>Do not equate a changed file with a changed process configuration.</li><li>Do not test only direct Secret get while ignoring workload creation.</li><li>Do not retire a key before testing restoration of an older backup.</li></ul>"
    "<h2>Connected lessons</h2>" + links([*project_related, project_hub])
)
rows.append(project)
by_path[project_hub]["data"]["modules"][0]["lessons"].append(project_path)
by_path[project_hub]["body"] += "<h2>Configuration delivery recovery drill</h2>" + links([project_path])
by_path[project_hub]["updated_at"] = stamp

questions = [
    ("Which ConfigMap consumption path needs a new Pod for an updated value?", ["An environment variable", "An ordinary projected directory file", "A fresh API read"], "Environment values are fixed for a running container."),
    ("What happens to a ConfigMap mounted through subPath after the object changes?", ["The mounted file does not receive projected updates", "The process always reloads it", "Every Pod restarts automatically"], "subPath does not follow the projection update."),
    ("How should an immutable ConfigMap change reach a Deployment?", ["Create a new named object and change the Pod template reference", "Edit its data in place", "Reuse a deleted name while old Pods run"], "A new name ties the rollout to a specific generation."),
    ("What should a missing required config key do before traffic?", ["Prevent container start or fail validation before readiness", "Silently choose an unreviewed default", "Mark the key optional automatically"], "Required values must not become hidden runtime guesses."),
    ("Can a ConfigMap and Secret be updated as one Kubernetes transaction?", ["No, validate an application-defined compatible pair", "Yes, if their names are identical", "Yes, when both are mounted"], "Separate objects can reach consumers at different times."),
    ("What proves an externally issued credential reached an application?", ["A successful request using the reported active version", "Only controller Ready status", "Only a changed Secret timestamp"], "The issuer-to-process path needs end-to-end evidence."),
    ("Which permission can expose namespace Secrets without direct Secret get?", ["Creating a Pod that mounts one", "Reading a public ConfigMap", "Watching a Service name"], "Workload creation can become an indirect Secret read."),
    ("What does Secret list permission return?", ["Secret objects including their data", "Only object names", "Only counts"], "List and watch require the same care as direct reads."),
    ("Why retain an old encryption key during a rotation?", ["Older stored objects or backups may still require it", "It makes base64 encoding secure", "It updates mounted Secret files"], "Restore scope determines the old decrypt dependency."),
    ("What verifies API-data encryption rotation beyond a new write?", ["Old objects rewritten and an older encrypted backup restored", "A new Pod scheduled", "A ConfigMap made immutable"], "New writes alone do not prove old data remains readable."),
    ("What must a long-running client do with a projected token?", ["Reopen the token file when refreshing credentials", "Cache the first token forever", "Copy it into the image"], "The kubelet can rotate the file while the process keeps an old value."),
    ("What should a broker check on a projected token?", ["The intended audience and issuer along with authorization", "Only that the file exists", "Only that the Pod is Ready"], "A signed token for another audience is not authorization for this broker."),
]
quiz = copy.deepcopy(by_path["quizzes/devops-operations"])
quiz.update(id=str(uuid.uuid5(uuid.NAMESPACE_URL, "aitrove:" + quiz_path)), path=quiz_path,
            title=titles[quiz_path], summary="Twelve decisions on configuration and identity delivery.",
            sort_order=21300, published_at=stamp, created_at=stamp, updated_at=stamp)
quiz["data"] = {"subject_root": course, "section_path": quiz_hub, "content_format": "html",
                "author_path": "authors/aitrove-editorial", "seo_ready": True, "duration_minutes": 12,
                "related": [{"path": target, "title": titles[target]} for target in project_related],
                "questions": [dict(prompt=prompt, options=options[index % 3:] + options[:index % 3],
                                   answer=(-index % 3) % 3, explanation=explanation)
                              for index, (prompt, options, explanation) in enumerate(questions)]}
quiz["body"] = (
    "<p>Choose the runtime evidence required before a configuration, credential, or identity update is promoted. Separate object state from the value active in a process and from a successful authenticated request.</p>"
    "<h2>Review these lessons</h2>" + links(project_related)
    + "<h2>Other checks</h2>" + links([quiz_hub, "quizzes/devops-storage-lifecycle-decisions", "quizzes/devops-artifact-trust-decisions"])
    + "<h3>Common Mistakes</h3><ul><li>Do not infer process freshness from an API object version.</li><li>Do not overlook indirect Secret access through workload creation.</li></ul>"
)
rows.append(quiz)
by_path[quiz_hub]["data"]["modules"][0]["lessons"].append(quiz_path)
by_path[quiz_hub]["body"] += "<h2>Configuration delivery check</h2>" + links([quiz_path])
by_path[quiz_hub]["updated_at"] = stamp

for item in specs:
    row = next(row for row in rows if row["path"] == item["path"])
    row["body"] += "<h2>Practice and check</h2>" + links([project_path, quiz_path])
    row["data"]["related"].extend({"path": path, "title": titles[path]} for path in [project_path, quiz_path])

for source, targets in {
    "devops/secrets-and-configuration": ["devops/configmap-projection-refresh-boundary", "devops/required-config-key-startup-gate", "devops/secret-workload-create-access-boundary", "devops/etcd-secret-encryption-rotation"],
    "devops/secret-rotation-rollout": ["devops/config-secret-generation-consistency", "devops/external-secret-sync-freshness"],
    "devops/gitops-reconciliation": ["devops/immutable-config-release-generation"],
    "devops/kubernetes-rbac": ["devops/secret-workload-create-access-boundary"],
    "devops/service-account-token-boundaries": ["devops/projected-token-file-refresh"],
    "devops/immutable-backup-retention": ["devops/etcd-secret-encryption-rotation"],
    "devops/kubernetes-probes": ["devops/required-config-key-startup-gate"],
}.items():
    row = by_path[source]
    row["body"] += "<h2>Advanced follow-up</h2>" + links(targets)
    row["data"].setdefault("related", []).extend({"path": target, "title": titles[target]} for target in targets)
    row["updated_at"] = stamp

assert len({row["path"] for row in rows}) == len(rows)
fixture.write_text(json.dumps(rows, ensure_ascii=False, indent=2) + "\n")
print(json.dumps({"new_lessons": len(specs), "new_projects": 1, "new_quiz_banks": 1, "total_records": len(rows)}))
