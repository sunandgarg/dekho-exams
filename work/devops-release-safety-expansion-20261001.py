"""Extend the DevOps preview with recovery and release safety lessons."""

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
    "failover-write-fencing", "Failover fencing: prevent two writable database leaders",
    "Prove the former writer has lost authority before accepting traffic on a replacement.",
    "Failover fencing removes write authority from a failed or isolated leader before a replacement accepts writes. It matters when a network partition makes a healthy server appear dead to one observer while clients can still reach it. A promotion that changes only the connection string can leave two writable databases, each accepting valid-looking transactions that cannot be reconciled by replay alone.",
    "A settlement database has a primary in one zone and a standby in another. Before promotion, the operator records the last acknowledged payout ID and the candidate's replay position. Stop the former primary's write endpoint with a tested mechanism outside the application, such as a managed-service promotion protocol or host/network isolation that the old process cannot bypass. The text gate is an operational record, not an instruction to perform blind node shutdown. Confirm the old endpoint rejects a test write, then promote and route one synthetic payout through the new writer. If the former host returns, keep it isolated until its data is compared and it is rebuilt as a replica; do not reconnect it as a peer with divergent writes. In an asynchronous system, separately reconcile transactions acknowledged on the old primary but not replayed on the promoted candidate. A consensus store may reject minority writes, but that property must be verified for the actual database and topology rather than assumed from the presence of a lease.",
    "text", "Settlement failover gate\nOld writer: isolated from application and direct clients\nCandidate: replay position and missing-write window recorded\nNegative test: old endpoint rejects a controlled write\nPromotion: one named operator and one candidate\nPositive test: new writer commits a synthetic payout\nReturn: old host rebuilt as replica after divergence check",
    "Fencing can lengthen recovery because the team must establish which side has authority before traffic moves. That cost prevents much larger inconsistency from simultaneous writers. An aggressive automatic failover can improve apparent availability while losing acknowledged writes if the candidate was behind. Measure both recovery time and the gap between the last acknowledged business operation and the new writer's state. Test direct clients, scheduled jobs, and bypass routes; changing a load balancer alone may leave an old write path open.",
    ["Do not promote based only on a missed heartbeat while the old writer may accept traffic.", "Do not rejoin a divergent former primary without rebuilding or reconciling it.", "Do not call zero split-brain risk proof that no acknowledged data was lost."],
    ["devops/replica-lag-read-contract", "devops/multi-region-failover", "devops/database-change-safety", "devops/break-glass-access"],
)

lesson(
    "immutable-backup-retention", "Immutable backup retention: protect recovery copies from deletion",
    "Choose a retention lock with a restore test and a known long-term storage bill.",
    "An immutable backup retention control prevents a recovery point from being changed or deleted during a defined period, including by a compromised privileged account when the storage system enforces that rule. It protects availability of the copy; it does not prove the copy is recent, decryptable, application-consistent, or free of corrupted data. Some retention modes cannot be shortened after a lock becomes final.",
    "A ledger service retains daily recovery points for forty-seven days in a separate backup account. Set minimum and maximum retention under a reviewed policy, allow the provider's cooling period to elapse only after testing lifecycle behavior in a disposable vault, and keep write access separate from delete administration. The text block is a control record, not a provider configuration file. Attempt a denied delete with a test identity and restore a recent recovery point into isolated infrastructure. Verify the schema, decryption key, row counts, and one synthetic transaction. Keep a catalog of recovery points with their expiration and restore location. If a backup is infected or logically corrupt, immutability preserves that bad state too; retain older known-good points and test recovery from more than the newest copy. Never enable indefinite retention accidentally, because a permanent lock can create an unavoidable cost.",
    "text", "Ledger recovery-copy policy\nDaily recovery point; retention: 47 days\nStorage account: separate from application writers\nDeletion test: privileged test identity denied\nRestore test: isolated database and synthetic ledger query\nKey check: decrypt oldest retained point\nReview: expiry inventory and monthly restore result",
    "Protected copies consume storage for the entire enforced period, and long retention multiplies cost as data grows. Cross-account and cross-region copies add transfer and operational overhead. A shorter period reduces cost but may leave no clean copy after a slow-moving corruption. Set the period from the business recovery and investigation window, then verify it with an actual restore. Monitor failed backup jobs and the age of the newest verified recovery point, not only the existence of a locked vault.",
    ["Do not treat a locked vault as evidence that its contents restore correctly.", "Do not set permanent retention without a deliberate long-term cost decision.", "Do not keep all recovery copies under the same credentials as the production writer."],
    ["devops/backup-and-recovery", "devops/volume-snapshot-recovery", "devops/cost-capacity-ownership", "devops/credential-incident-rotation"],
)

lesson(
    "encryption-key-rotation-recovery", "Encryption key rotation: keep old data decryptable during recovery",
    "Separate rotating key material from replacing a key identifier or revoking access.",
    "Encryption-key rotation changes which cryptographic material protects new writes. In some managed key systems, rotating material under the same key identifier retains older versions so existing ciphertext remains decryptable. Replacing the key identifier or disabling the old key is a different operation: archived backups and old volumes may still require it. The application must be able to decrypt historical data throughout its retention window.",
    "A claims database and its snapshots use a customer-managed encryption key. Inventory every active volume, backup, export, and regional copy tied to the old key before changing access. The text gate distinguishes an in-place rotation from migration to a new key; provider behavior must be verified for the chosen service. After rotation, encrypt a new test record and decrypt both it and a record written before rotation. Restore an old snapshot into a disposable account with the intended recovery role, then check that the key policy permits the restore path. If moving to a new key identifier, re-encrypt or migrate retained assets on a controlled schedule before revoking the old key. Test a deliberately denied recovery role in the disposable environment to find hidden key dependencies. Do not disable the old key merely because today's application deployment reads and writes successfully.",
    "text", "Claims key transition gate\nOld key: active volumes, archives, snapshots inventoried\nChange type: material rotation or new key identifier\nNew write: encrypted and decrypted successfully\nHistorical read: pre-rotation record decrypted\nRecovery: oldest retained snapshot restored with recovery role\nRevocation: old key disabled only after dependent assets migrate",
    "Keeping historical key material and access paths increases the attack surface and audit burden, but deleting them early can make an immutable backup useless. Re-encryption requires I/O, temporary storage, and time; large archives can outlast a release window. Measure the oldest retained encrypted asset and the exact role required to restore it. Key-rotation success must include a historical decrypt and recovery test, not just a successful new encryption call.",
    ["Do not confuse rotation under one key identifier with migration to a new identifier.", "Do not revoke the old key while retained snapshots still require it.", "Do not test only encryption of new records."],
    ["devops/secrets-and-configuration", "devops/secret-rotation-rollout", "devops/immutable-backup-retention", "devops/backup-and-recovery"],
)

lesson(
    "gitops-crd-rollout-order", "GitOps rollout order: install API definitions before dependent objects",
    "Stage custom-resource definitions, controllers, and instances with observed readiness gates.",
    "A custom-resource definition adds an API type to a Kubernetes cluster. A custom resource cannot be admitted until that definition is established, and a controller may not be ready to reconcile it immediately afterward. GitOps synchronization order can sequence objects, but an annotation that places a definition earlier does not prove the corresponding controller is healthy or that a newly changed schema is compatible with existing instances.",
    "A billing operator upgrade introduces a new InvoiceQueue field. Put the definition in an earlier synchronization wave, wait for it to become Established, and roll the controller with a compatibility check before applying resources that use the field. The YAML fragment shows annotations on two resources; it is not a full definition or instance. In a disposable cluster, sync the old resource under the new definition, then the new resource under both old and new controller versions if the upgrade permits overlap. Observe reconciliation status and a synthetic queue operation before continuing application rollout. If the controller fails, stop the sync and retain the old working objects; removing an API definition can delete access to every instance and may destroy data depending on the environment. Record the intended reverse order for rollback, including whether the old controller understands the new field.",
    "yaml", "kind: CustomResourceDefinition\nmetadata:\n  name: invoicequeues.billing.aitrove.test\n  annotations:\n    argocd.argoproj.io/sync-wave: '-1'\n---\nkind: InvoiceQueue\nmetadata:\n  name: payout-queue\n  annotations:\n    argocd.argoproj.io/sync-wave: '1'",
    "More synchronization stages slow deployment and increase the number of intermediate states that must be observed. They also prevent a fast application rollout from outrunning its API and controller dependencies. Watch API establishment, controller availability, and reconciliation errors separately. A green GitOps sync can still leave a business queue stuck if its controller reports Ready but cannot process the new field. Keep both schema and on-disk compatibility in the rollback plan.",
    ["Do not create a new custom resource before its definition is established.", "Do not treat wave order as proof that the controller processed the instance.", "Do not delete a definition to roll back one bad instance."],
    ["devops/gitops-reconciliation", "devops/cluster-upgrade-drill", "devops/admission-policy-guardrails", "devops/release-evidence-record"],
)

lesson(
    "hpa-stabilization-boundaries", "HPA stabilization: prevent replica oscillation without masking demand",
    "Tune scale-down behavior against startup time, traffic bursts, and downstream limits.",
    "A HorizontalPodAutoscaler changes a workload's desired replica count from sampled metrics. Its control loop is periodic, and new Pods need scheduling, image pulls, startup, and readiness before they add usable capacity. A scale-down stabilization window holds recent recommendations to avoid rapid replica loss after a short dip. It does not reserve nodes or increase database sessions.",
    "A parcel API sees short traffic troughs between campaign batches. Configure a conservative scale-down window and a maximum reduction per interval, then test with a load trace that includes two bursts separated by a quiet period. The YAML fragment belongs under an autoscaler specification; it is not a complete object. Set CPU requests to measured values before using utilization as a signal, and observe unavailable endpoints and p95 latency as the controller changes desired replicas. Compare the chosen window with Pod startup and node-provisioning delays. If the autoscaler requests more Pods but they remain Pending, inspect scheduling and node pool limits rather than shortening the scale-down window. If a database pool is fixed, cap replicas or reduce per-Pod sessions so scale-out does not exhaust the backend. Validate missing-metric behavior in a disposable environment; the controller can make a different decision when some metrics are unavailable.",
    "yaml", "spec:\n  minReplicas: 4\n  maxReplicas: 19\n  behavior:\n    scaleDown:\n      stabilizationWindowSeconds: 360\n      policies:\n      - type: Pods\n        value: 2\n        periodSeconds: 60",
    "Longer stabilization keeps extra Pods running through quiet periods, raising compute cost but reducing cold scale-out and endpoint churn. A short window saves capacity and can cause repeated initialization work or latency spikes. Evaluate the full response time from load rise to Ready endpoints, not only the autoscaler's desired count. Revisit thresholds when request sizes, initialization cost, or downstream capacity changes. Record whether the chosen metric reflects actual user demand or a symptom of an overloaded dependency.",
    ["Do not assume desired replicas are immediately serving traffic.", "Do not tune HPA CPU utilization without realistic CPU requests.", "Do not scale API replicas beyond the database session budget."],
    ["devops/horizontal-autoscaling", "devops/node-autoscaling-headroom", "devops/database-pool-pressure", "devops/capacity-load-testing"],
)

lesson(
    "cache-stampede-control", "Cache stampedes: bound origin work when popular keys expire",
    "Coordinate misses and measure stale-data tolerance before adding cache locks.",
    "A cache stampede occurs when many requests miss the same popular key and all recompute or fetch it from an origin. A single expiry can multiply work at the database precisely when traffic is high. A per-process lock reduces duplicate work inside one instance but does not coordinate dozens of replicas. A distributed lease can coordinate across replicas, yet a lease failure must have a bounded fallback.",
    "A tariff lookup is requested by every parcel quote. Give its entries a base lifetime with small deterministic jitter, allow a short stale-read window only where the business rule permits it, and use a single-flight mechanism for a miss within each instance. The text block is an operational policy, not a library API. For a cross-instance hot key, let one instance refresh under a short lease while others serve an explicitly bounded stale value or return a controlled error. Do not serve stale prices after a legal cutoff. Load-test an expiry with forty-seven concurrent callers across several instances and count origin queries, lock waits, stale responses, and user latency. Simulate cache outage separately; the fallback must not direct every request to a database already near its connection limit. Keep key versioning tied to tariff revision so an invalidation does not silently return an older legal rate.",
    "text", "Tariff cache policy\nBase lifetime: 11 minutes with bounded jitter\nStale allowance: 45 seconds outside legal cutoff\nLocal miss: one loader per key and instance\nCross-instance refresh: short lease, one owner\nOrigin limit: 8 concurrent tariff queries\nProof: 47 simultaneous misses do not create 47 origin reads",
    "Jitter lowers synchronized expiry but creates slightly variable freshness. Serving stale results preserves availability while risking an outdated business decision; its maximum age must be explicit and tested. Coordination adds lease storage, timeouts, and failure cases, so use it only for genuinely hot keys. A low origin-concurrency cap protects the database but may increase request queue time. Measure hit ratio and origin load alongside correctness of the returned tariff revision.",
    ["Do not assume an in-process lock coordinates multiple replicas.", "Do not allow stale data through a business cutoff that requires a new value.", "Do not treat a cache outage as permission to flood the origin."],
    ["devops/overload-shedding", "devops/database-pool-pressure", "devops/retry-timeout-budgets", "devops/capacity-load-testing"],
)

lesson(
    "edge-rate-limit-fairness", "Edge rate limits: reject abuse without penalizing shared networks",
    "Choose an aggregation key and response contract that preserve legitimate tenants.",
    "A rate limit bounds accepted requests over a time window or token budget. At an edge, its effectiveness depends on where the client identity comes from and how requests are grouped. A simple source-IP rule can block many unrelated users behind one corporate gateway, while trusting an unverified forwarded header lets a caller change the grouping key. A rate limit is a load-shedding control, not a guarantee that the backend stays below capacity.",
    "A claims upload endpoint receives both authenticated partner traffic and anonymous login requests. Apply a broad pre-authentication protection for login attempts and a tighter per-partner budget after a verified identity is available; keep global concurrency and database limits as separate guards. The text block is a design contract, not a firewall rule. Return a clear rejection response and a retry interval that matches the policy, while avoiding a response that reveals whether a username exists. Test two partners sharing one NAT address and one partner sending bursts from many addresses. Measure accepted and rejected requests by policy ID, and confirm the protected operation remains usable for a low-volume partner. Check proxy trust configuration before using any forwarded address. During an incident, raise or lower limits through a reviewed, time-bounded change with a rollback path.",
    "text", "Claims upload admission policy\nPre-auth login: source-level abuse guard plus global cap\nAuthenticated upload: verified partner ID budget\nShared NAT test: partner A cannot consume partner B budget\nDistributed-source test: one partner cannot bypass its budget\nResponse: explicit rejection and bounded retry guidance\nGuard: backend concurrency limit remains in place",
    "Fine-grained counters use more edge state and monitoring cardinality than a single global rule, but avoid punishing unrelated clients. A strict threshold reduces overload at the cost of rejected legitimate bursts. A generous threshold may still permit concurrent requests beyond the database's safe limit. Set policies from measured traffic distributions and business priority, then test fairness and user impact. Keep response and log fields free of raw credentials or personal identifiers.",
    ["Do not equate source IP with one user or tenant.", "Do not trust a client-supplied forwarding header without a verified proxy chain.", "Do not rely on a rate limit alone when the backend also needs a concurrency cap."],
    ["devops/overload-shedding", "devops/gateway-api-routing", "devops/metric-cardinality-budget", "devops/database-pool-pressure"],
)

lesson(
    "multiarch-image-promotion", "Multi-architecture images: verify every platform behind one tag",
    "Promote a manifest index only after each target architecture passes a runtime check.",
    "A multi-platform container image index points to separate platform-specific manifests. A node selects the variant matching its operating system and architecture when pulling the image. A build that succeeds on one architecture does not prove the other variant has the same dependencies, native libraries, or runtime behavior. The top-level index digest and the child manifests are distinct identities that should be recorded together.",
    "A document parser runs on both x86 and ARM nodes. Build both variants from one reviewed source revision and inspect the index before promotion. The shell fragment is a read-only manifest inspection; use the approved registry name and digest from the build record. Run malformed-document regression tests on actual nodes of both architectures, then confirm each Pod reports the expected image ID. If a builder used emulation, account for slower compilation and test enough native behavior to catch architecture-specific faults. Keep the old index digest available for rollback and make sure it still resolves to both variants. Never promote a mutable tag alone; two clusters can pull different contents if the tag changes between deployments. When scanning or attesting the build, cover the index and each child artifact according to the chosen tool's model.",
    "bash", "docker buildx imagetools inspect registry.internal/parcel/document-parser@sha256:0123456789abcdef0123456789abcdef0123456789abcdef0123456789abcdef\nkubectl get pods -n render -l app=document-parser -o wide\nkubectl get pods -n render -l app=document-parser -o yaml",
    "Two architecture variants increase build time, registry storage, scan work, and test-matrix size. Native builders can reduce emulation overhead but add runner management. One index simplifies deployment references only when its children are complete and verified. A digest pins content, yet a runtime regression on an untested architecture remains possible. Measure startup and parsing latency on each platform before assuming identical performance.",
    ["Do not infer ARM behavior from a passing x86 test.", "Do not record only a mutable tag when promoting an image index.", "Do not confuse the index digest with the selected child manifest or runtime image ID."],
    ["devops/container-image-builds", "devops/artifact-promotion", "devops/supply-chain-verification", "devops/dependency-patch-campaign"],
)

titles = {row["path"]: row["title"] for row in rows}
titles.update({item["path"]: item["title"] for item in specs})
project_path = "devops/failover-release-safety-project"
quiz_path = "quizzes/devops-release-safety"
titles[project_path] = "Project: protect a release through failover and capacity pressure"
titles[quiz_path] = "DevOps release safety decisions"
for item in specs:
    assert all(target in titles for target in item["related"]), item["path"]


def links(paths):
    return "<ul>" + "".join(f'<li><a href="/{html.escape(path)}">{html.escape(titles[path])}</a></li>' for path in paths) + "</ul>"


groups = [
    ("Recovery authority and retained data", "Prevent competing writers and preserve decryptable recovery points.", ["failover-write-fencing", "immutable-backup-retention", "encryption-key-rotation-recovery"]),
    ("Ordered deployment and capacity", "Stage API changes, replica behavior, and cache-origin work.", ["gitops-crd-rollout-order", "hpa-stabilization-boundaries", "cache-stampede-control"]),
    ("Edge fairness and image variants", "Bound abusive traffic and verify every platform in a promoted image.", ["edge-rate-limit-fairness", "multiarch-image-promotion"]),
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
               sort_order=18800 + order, published_at=stamp, created_at=stamp, updated_at=stamp)
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
               summary="Prove write fencing, backup decryption, rollout order, cache protection, and platform-specific image behavior.",
               difficulty="Advanced", sort_order=18890,
               published_at=stamp, created_at=stamp, updated_at=stamp)
project_related = ["devops/failover-write-fencing", "devops/immutable-backup-retention", "devops/encryption-key-rotation-recovery", "devops/gitops-crd-rollout-order", "devops/hpa-stabilization-boundaries", "devops/cache-stampede-control", "devops/edge-rate-limit-fairness", "devops/multiarch-image-promotion"]
project["data"] = {"kind": "project", "reading_minutes": 9,
                   "author_path": "authors/aitrove-editorial", "subject_root": course,
                   "section_path": project_hub, "content_format": "html", "seo_ready": True,
                   "related": [{"path": target, "title": titles[target]} for target in project_related]}
project["body"] = (
    "<p>This exercise protects a synthetic settlement service while its database, controller, image, and edge policy change. Use disposable infrastructure and test-only records. Capture the writer identity, last acknowledged payout, backup key, GitOps revision, image index digest, and baseline origin load before starting.</p>"
    "<h2>Stage and verify</h2><p>Promote an isolated standby only after the former writer fails a controlled write attempt. Restore a retained recovery point with the intended recovery role, then decrypt a record written before key rotation. Apply a changed custom-resource definition and wait for establishment before introducing its dependent resource. Validate the controller processes a synthetic event. Build x86 and ARM image variants and run the same parser test on actual nodes of both types. Keep every digest and decision attached to the release record.</p>"
    "<pre><code class=\"language-text\">Settlement exercise evidence\nOld writer rejected; new writer accepted one test payout\nOld snapshot restored and historical record decrypted\nCustom API established; controller processed test object\nBoth architecture variants ran the parser regression\nBurst load: cache origin bounded and tenant budgets isolated\nRecovery owner: named, with last acknowledged payout checked</code></pre>"
    "<h2>Apply pressure</h2><p>Expire a popular tariff key while forty-seven clients request it across several API replicas. Count origin reads and verify a legal-cutoff request never receives a stale tariff. Run two authenticated partners behind the same NAT address and confirm one cannot consume the other's budget. Apply a traffic profile with two bursts separated by a quiet period; observe autoscaler desired Pods, Ready endpoints, database sessions, and latency. If failover loses an acknowledged payout, stop the release and reconcile it before serving normal traffic.</p>"
    "<h2>Cost and verification</h2><p>The drill uses extra replicas, protected backup storage, two image variants, and test traffic. Record the time until a serving endpoint appears, the number of origin reads per cache miss, rejected requests by tenant, and the oldest successful restore. Do not score the drill as passed solely because a controller reports healthy. Clean up disposable assets after retaining the evidence under the team's approved policy.</p>"
    "<h3>Common Mistakes</h3><ul><li>Do not declare failover safe while the former writer accepts direct clients.</li><li>Do not revoke the key needed to restore older copies.</li><li>Do not treat one platform's image test as proof for every node.</li></ul>"
    "<h2>Connected lessons</h2>" + links([*project_related, project_hub]))
rows.append(project)
project_index = by_path[project_hub]
project_index["data"]["modules"][0]["lessons"].append(project_path)
project_index["body"] += "<h2>Failover and release safety exercise</h2>" + links([project_path])
project_index["updated_at"] = stamp

questions = [
    ("What must be proven before a standby starts accepting writes?", ["The former writer no longer accepts writes", "The old DNS record has a short TTL", "The cache hit ratio is high"], 0, "Fencing closes the competing-writer path."),
    ("What does immutable retention fail to prove?", ["That the backup can be decrypted and restored", "That deletion is restricted during retention", "That a copy is kept for its enforced period"], 0, "A protected copy still needs recovery tests."),
    ("What differs between rotating material and replacing a key identifier?", ["Historical data may still depend on the older identifier", "Neither needs a decrypt test", "Both erase old ciphertext automatically"], 0, "Key identity and retained material determine historical access."),
    ("What is required after an earlier GitOps sync wave installs a custom API?", ["Verify establishment and controller reconciliation", "Assume all custom resources are healthy", "Delete the definition during rollback"], 0, "Wave order alone is not a processing result."),
    ("What does an HPA desired replica count omit?", ["Scheduling, startup, and readiness time", "The declared maximum replica value", "The selected workload name"], 0, "Desired Pods do not serve until ready."),
    ("Why can a local cache lock fail to prevent a stampede?", ["Other replicas run separate locks", "Every cache key uses one global process", "Jitter makes all expirations identical"], 0, "Cross-instance demand can still hit the origin."),
    ("Why is source IP a weak tenant limit key?", ["Many tenants can share one NAT address", "An IP address always names one account", "An IP limit automatically caps database sessions"], 0, "The aggregation key may combine unrelated callers."),
    ("What must be tested for a multi-platform image?", ["Each target architecture on representative nodes", "Only the builder's host architecture", "Only the top-level tag text"], 0, "Child variants can differ in native dependencies and behavior."),
    ("What can happen after a former database writer returns?", ["Divergent writes need reconciliation or rebuild", "It safely rejoins every topology without inspection", "All cached data becomes current"], 0, "An isolated writer may have accepted different transactions."),
    ("What does a locked backup with indefinite retention risk?", ["Storage cost that cannot be ended early", "Automatic deletion after one day", "No need for a restore key"], 0, "Final locks can make retention irreversible."),
    ("How should a cache behave at a legal price cutoff?", ["Reject or fetch the required revision rather than serve disallowed stale data", "Always extend staleness to keep the cache green", "Assume a local lock updates all replicas"], 0, "Correctness sets the freshness boundary."),
    ("What identifies the deployed multi-architecture artifact?", ["The reviewed index digest plus verified child and runtime identities", "A mutable tag alone", "Only the x86 test log"], 0, "Promotion evidence must cover the index and selected variants."),
]
quiz = copy.deepcopy(by_path["quizzes/devops-operations"])
quiz.update(id=str(uuid.uuid5(uuid.NAMESPACE_URL, "aitrove:" + quiz_path)), path=quiz_path,
            title=titles[quiz_path], summary="Twelve decisions on write authority, retained data, autoscaling, cache load, and image variants.",
            sort_order=18900, published_at=stamp, created_at=stamp, updated_at=stamp)
quiz["data"] = {"subject_root": course, "section_path": quiz_hub, "content_format": "html",
                "author_path": "authors/aitrove-editorial", "seo_ready": True, "duration_minutes": 12,
                "related": [{"path": target, "title": titles[target]} for target in project_related],
                "questions": [dict(prompt=prompt, options=options[index % 3:] + options[:index % 3],
                                   answer=(answer - index % 3) % 3, explanation=explanation)
                              for index, (prompt, options, answer, explanation) in enumerate(questions)]}
quiz["body"] = "<p>Choose the action supported by the observed release evidence. Each question probes a failure or ownership boundary that a green deployment status cannot resolve.</p><h2>Review these lessons</h2>" + links(project_related) + "<h2>Other checks</h2>" + links([quiz_hub, "quizzes/devops-failure-boundaries", "quizzes/devops-system-boundaries", "quizzes/devops-stateful-operations"]) + "<h3>Common Mistakes</h3><ul><li>Do not infer a usable backup from its retention setting.</li><li>Do not infer that a former writer stopped merely because the connection string changed.</li></ul>"
rows.append(quiz)
quiz_index = by_path[quiz_hub]
quiz_index["data"]["modules"][0]["lessons"].append(quiz_path)
quiz_index["body"] += "<h2>Release safety check</h2>" + links([quiz_path])
quiz_index["updated_at"] = stamp

for item in specs:
    row = next(row for row in rows if row["path"] == item["path"])
    row["body"] += "<h2>Practice and check</h2>" + links([project_path, quiz_path])
    row["data"]["related"].extend({"path": target, "title": titles[target]} for target in [project_path, quiz_path])

for source, targets in {
    "devops/multi-region-failover": ["devops/failover-write-fencing"],
    "devops/backup-and-recovery": ["devops/immutable-backup-retention"],
    "devops/secrets-and-configuration": ["devops/encryption-key-rotation-recovery"],
    "devops/gitops-reconciliation": ["devops/gitops-crd-rollout-order"],
    "devops/horizontal-autoscaling": ["devops/hpa-stabilization-boundaries"],
    "devops/overload-shedding": ["devops/cache-stampede-control", "devops/edge-rate-limit-fairness"],
    "devops/container-image-builds": ["devops/multiarch-image-promotion"],
}.items():
    row = by_path[source]
    row["body"] += "<h2>Advanced follow-up</h2>" + links(targets)
    row["data"].setdefault("related", []).extend({"path": target, "title": titles[target]} for target in targets)
    row["updated_at"] = stamp

assert len({row["path"] for row in rows}) == len(rows)
fixture.write_text(json.dumps(rows, ensure_ascii=False, indent=2) + "\n")
print(json.dumps({"new_lessons": len(specs), "new_projects": 1,
                  "new_quiz_banks": 1, "total_records": len(rows)}))
