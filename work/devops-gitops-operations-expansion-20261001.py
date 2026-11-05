"""Add GitOps operating-boundary lessons to the local DevOps curriculum."""

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
    "gitops-rendered-input-lock",
    "GitOps render locks: identify every input behind an applied manifest",
    "A Git commit identifies deployment intent only when the renderer and every external input are fixed.",
    "A GitOps controller can render a chart, apply values from another repository, expand a Kustomize base, and substitute an image reference. The final Kubernetes objects depend on all of those inputs. Recording only the application repository commit misses a chart that advanced independently, a values branch that moved, or an image tag that was replaced. A release record should bind the source revision, chart or base revision, renderer version, values revision, image digest, and digest of the rendered object set that the controller actually applied.",
    "A billing-ledger Deployment is assembled from a chart repository, a platform values repository, and an image built by the service team. The release job resolves each reference to an immutable revision, renders the manifests in a clean workspace, validates policy against the rendered output, and records a digest over a canonical resource inventory. It then asks the controller to reconcile those same revisions. Compare the controller's observed source and manifest digest with the candidate, and inspect the running image ID after rollout. During the drill, move a chart tag and a values branch without changing the application commit; the release must detect that the render changed rather than reporting the old release as identical. If the controller supports multiple sources, detect duplicate group-kind-namespace-name tuples before syncing because a later source may replace an earlier resource while still leaving a warning. Do not include live status or server-generated metadata in the canonical digest. Store the renderer version and relevant plugin configuration so a future investigator can reproduce the build even after local tooling is upgraded.",
    "text",
    "Billing render record\nApp revision: immutable commit\nChart or base: immutable revision and package digest\nValues: immutable revision and chosen file\nRenderer: version and plugin set\nImage: tested manifest digest\nOutput: canonical resource-set digest\nCluster: observed source and applied revision",
    "Rendering N objects costs work proportional to their total source and output bytes plus template evaluation; retaining each rendered snapshot adds storage per release. That cost is usually smaller than triaging an unrepeatable deployment. Measure releases with floating inputs, local-versus-controller render mismatches, duplicate resource identities, and running image digests that differ from the accepted candidate. Pinning inputs does not prove the program behaves correctly; it makes the deployed state explainable.",
    ["Do not treat one Git commit as the complete release identity when charts or values come from elsewhere.", "Do not hash server-generated status fields as release intent.", "Do not ignore duplicate rendered resource identities."],
    ["devops/gitops-reconciliation", "devops/helm-release-review", "devops/tested-artifact-digest-binding", "devops/sbom-artifact-digest-binding"],
)

lesson(
    "kustomize-overlay-diff-gate",
    "Kustomize overlays: review the complete environment diff",
    "An overlay is a transformation of a base, so the reviewed artifact is its rendered output rather than the patch file alone.",
    "A one-line patch can change a selector, image, namespace, replica count, security context, or generated ConfigMap name after composition. Base updates may reach several environments even when their overlay directories do not change. A gate should render each affected overlay with a pinned toolchain, compare the full resource identities and important fields, and identify additions, deletions, and replacements before GitOps reconciliation begins.",
    "A claims-processing service has development and production overlays. The base adds a new container port, while production changes the image digest and resource requests. The CI job renders both overlays, validates every output object against the cluster API version, and computes a structured diff from the last accepted production render. It flags a selector change because that can orphan the current Pods, a new ServiceAccount because it changes identity, and a generated ConfigMap name because a rollout may follow even if the original literal did not change. Run a negative test in which a patch target no longer matches after a base rename; the pipeline must fail or clearly report the missing intended modification, not silently deploy the unpatched base. Avoid patching a shared base with production-only secrets. For each change, reviewers see the affected clusters, resource identities, image digests, and relevant fields, then verify that the controller renders the same output. A successful YAML parse is insufficient if the overlay points at the wrong namespace or strips an admission label.",
    "yaml",
    "resources:\n  - ../../base\nnamespace: claims-production\nimages:\n  - name: registry.internal/claims-processor\n    digest: sha256:7e3a448df91e0c641fd37435a7c78890db03b9fd625126995dc975fb4d88727a\npatches:\n  - path: resources-production.yaml\n    target:\n      kind: Deployment\n      name: claims-processor",
    "If E environments each render N resources, full rendering and policy validation costs roughly O(E × N) objects plus template and diff work. Selective execution can be safe only when the dependency graph from bases to overlays is complete; otherwise a shared-base edit may skip production. Track unreviewed rendered changes, missing patch targets, unexpected deletions, and differences between CI output and controller output. Cache by immutable input digest, never by a movable branch name alone.",
    ["Do not review only the overlay patch while ignoring the rendered base.", "Do not let a nonmatching patch silently remove a production constraint.", "Do not skip production checks after a shared-base change."],
    ["devops/gitops-reconciliation", "devops/helm-release-review", "devops/immutable-config-release-generation", "devops/ci-matrix-required-gate"],
)

lesson(
    "gitops-resource-ownership-transfer",
    "GitOps ownership transfer: keep one reconciler authoritative per resource",
    "A Kubernetes object should have an explicit controller of record for the fields that determine its behavior.",
    "Two GitOps Applications, a Helm release, and a manual operator can all target the same resource identity. They may alternate writes, produce a persistent out-of-sync state, or delete the object when one owner prunes it. A transfer must identify the object, current tracking metadata, field managers, deletion behavior, and intended new owner. Server-side apply can share nonoverlapping fields, but it does not make two controllers safe owners of the same immutable or atomic field.",
    "A platform team moves the shared ingress controller Service from a bootstrap Helm release to a cluster GitOps Application. First enumerate every release and Application that tracks the Service, its live field managers, and the exact desired manifest each renders. Freeze the old release's ability to update or delete that object, then make the new Application observe or adopt it under an agreed ownership policy. Run a sync with collision detection enabled and verify the Service keeps its stable address and selectors. Remove the old template only after checking that its uninstall or prune path will not delete the adopted object. Test the sequence in an isolated cluster with the same tracking mode and chart version. A resource that must remain owned by the bootstrap system should be excluded from the new Application rather than suppressed from the conflict view. Record the handoff commit and live object identity; a green sync from the new owner is not enough if the old release still has a deletion claim over it.",
    "text",
    "Ingress Service handoff\nIdentity: core/v1 Service platform/ingress-gateway\nOld owner: bootstrap release and deletion behavior\nNew owner: cluster Application and field scope\nFreeze: old owner cannot update or prune during transfer\nVerify: address, selectors, tracking, field managers\nExit: old uninstall cannot remove adopted Service",
    "Inventorying R resources and O owners is O(R + O) when tracking information is indexed, but ownership conflicts can create repeated API writes and a controller hot loop. Measure shared-resource warnings, sync retries, field-manager conflicts, and resources whose deletion outcome is unknown. A temporary freeze adds operational overhead; use a bounded window with a named owner and a clear abort point rather than leaving both reconcilers half-enabled.",
    ["Do not add a second Application to a shared object and rely on sync order.", "Do not remove the old owner before checking its deletion behavior.", "Do not mistake a field-level merge for complete resource ownership."],
    ["devops/gitops-reconciliation", "devops/terraform-state-removal-handoff", "devops/helm-release-review", "devops/gitops-emergency-change"],
)

lesson(
    "gitops-prune-deletion-preview",
    "GitOps pruning: preview deletions as a separate release action",
    "Pruning removes previously managed resources absent from the new desired inventory; that absence can be accidental.",
    "A bad source path, failed render, renamed resource, or empty target set can make a controller propose a large deletion. The safe review unit is a before-and-after inventory of tracked objects with explicit disposition for persistent data, namespaces, controllers, and shared dependencies. Application deletion and resource pruning may follow different policies, so test both. A protection annotation or disabled-prune setting is a temporary control, not a substitute for understanding who now owns the object.",
    "A warehouse service retires an old worker Deployment but retains its PVC and audit ConfigMap. The release job compares the controller's current resource inventory with the rendered target and lists the three potential removals. The Deployment is approved for deletion after consumers reach zero and queued work is transferred. The PVC remains protected until a restore drill verifies the data export, and the audit ConfigMap moves to a separate owner. In a disposable cluster, change the source path to an empty directory and verify the controller blocks or flags mass pruning; do not enable an allow-empty exception merely to silence the alert. Test whether deleting the parent Application or Kustomization would remove or orphan its resources, and verify what happens to dependents after Kubernetes garbage collection. A resource stuck behind a finalizer requires a separate investigation, not manual finalizer removal as a first response. Record deletion authorization by resource identity, expected owner after change, and a post-sync inventory; a green application status does not prove retained data survived.",
    "text",
    "Warehouse prune review\nCurrent inventory: Deployment, PVC, audit ConfigMap\nTarget inventory: PVC, audit ConfigMap under new owner\nDelete: Deployment after queue drain\nRetain: PVC until restore acceptance\nTransfer: audit ConfigMap before old owner deletion\nAbort: empty render or unexpected deletion set\nPost-check: retained object UIDs and data accessible",
    "A diff over C current and T target identities is O(C + T) with hashed keys; the expensive part is validating data retention and dependency impact. Keeping obsolete objects indefinitely consumes storage and increases confusion, while automatic deletion without review can make recovery impossible. Measure unexpected prune candidates, protected-resource age, orphaned objects, and post-sync data checks. Require stricter approval for irreversible state than for a stateless Deployment.",
    ["Do not assume an empty render means the service was intentionally removed.", "Do not rely on a prune exception without a future owner or expiry.", "Do not remove a finalizer before identifying what cleanup it protects."],
    ["devops/gitops-reconciliation", "devops/stuck-finalizer-recovery", "devops/pv-reclaim-policy-deletion-path", "devops/terraform-state-removal-handoff"],
)

lesson(
    "gitops-sync-health-user-path",
    "GitOps verification: separate source sync, resource health, and user success",
    "A controller can report that desired objects match live objects while the service still fails its customer journey.",
    "Source freshness says which revision the controller fetched. Sync compares rendered desired state with tracked live fields. Resource health interprets rollout conditions. None alone proves authentication, database access, queue processing, or edge routing. A release gate should join those observations to a synthetic transaction and to the immutable artifact actually running, while understanding that ignored differences may hide fields the application still uses.",
    "A claims-upload release reaches the cluster and its Deployment becomes available. The application is still failing uploads because an external secret refresher has not delivered the new signing key. The release record captures source revision, rendered digest, controller sync result, Deployment observed generation and available replicas, secret generation, running image ID, and a synthetic upload that reads the uploaded claim back. The gate fails despite a green controller status. In another drill, a custom resource appears unknown or healthy because its health check is too permissive; add a check for the controller's observed generation and a workload-level probe. If an autoscaler intentionally changes replica count, narrow the ignored-difference rule to that field and confirm that image, ServiceAccount, and security fields remain compared. Test a missing Secret and a failing edge route; the release should give a specific failure state instead of an undifferentiated 'sync failed.' A user-path probe must use disposable data and should report its own error separately from controller health so incident responders know whether the problem is rendering, rollout, dependency delivery, or routing.",
    "text",
    "Claims release acceptance\nSource: approved revision fetched\nRender: accepted digest observed\nSync: no unexpected field differences\nHealth: observed generation and replicas ready\nRuntime: image ID matches tested digest\nDependency: expected secret generation delivered\nUser path: upload accepted and queryable",
    "Collecting M status signals per release is O(M); a synthetic transaction adds external calls and cleanup work. Probes that are too frequent or high-cardinality can create load and telemetry cost, so use a bounded cadence and stable labels. Measure false-green releases, time from sync to user success, stale source age, ignored field scope, and failure classification. A green sync is useful evidence, but it is a configuration statement rather than a service-level acceptance test.",
    ["Do not declare a release successful at the first Synced status.", "Do not ignore an entire resource to suppress one expected field difference.", "Do not use a local readiness response as the only customer-path test."],
    ["devops/gitops-reconciliation", "devops/synthetic-transaction-monitoring", "devops/external-secret-sync-freshness", "devops/release-evidence-record"],
)

lesson(
    "gitops-source-staleness-boundary",
    "GitOps source outages: distinguish last-good operation from fresh deployment",
    "A cluster can keep serving an old reconciled revision when its Git, chart, or artifact source is unavailable.",
    "Availability of the running service and freshness of desired-state input are different properties. A controller may retain its last successful source artifact and continue to compare or serve status while it cannot fetch the new revision. The incident response must record the last fetched revision, artifact age, source error, and whether any newer approved change is waiting. Do not interpret a stable cluster as proof that a security patch or rollback committed during the outage has been applied.",
    "An order-routing platform loses access to its chart registry during an incident. The current Pods remain healthy, so on-call staff avoid restarting them merely to clear a source error. They compare the controller's last successful artifact digest and source revision with the approved release queue and discover that a certificate fix is pending. The team checks whether the fix can be delivered through a preapproved alternate source path, including its identity and authorization, or whether the service can remain on the last-good version until the registry returns. In a disposable drill, revoke source credentials after one successful sync, submit a new desired revision, and prove the freshness alert fires even though workload health remains green. Then restore access and verify that the controller fetches and applies the intended revision once, without deploying an intermediate unreviewed head. If local cached chart bytes are used, record their digest; a cache hit is a deployable artifact only if its integrity and scope match the approved candidate. Define a maximum source staleness appropriate to the service's patch and recovery commitments, not one global threshold for every Application.",
    "text",
    "Order-routing source state\nLast successful revision: recorded commit and artifact digest\nLast fetch: timestamp and source identity\nPending approved revision: recorded separately\nRunning workload: health and image digest\nOutage decision: hold last-good or use approved alternate\nRecovery check: intended revision fetched and applied once",
    "Source checks are cheap, but retaining local artifacts costs controller storage; aggressive eviction can remove the only reproducible last-good input during an upstream outage. Measure source artifact age, fetch failure duration, pending revision count, and time from restored connectivity to applied state. Alerts should distinguish 'serving last-good' from 'unable to deploy new intent' so operators do not create a second outage while fixing the first.",
    ["Do not call a running workload current when its source has stopped updating.", "Do not restart healthy Pods solely because the source fetch failed.", "Do not deploy an unverified cache entry as a substitute for a pinned release."],
    ["devops/gitops-reconciliation", "devops/registry-replica-promotion", "devops/certificate-renewal-path", "devops/alert-design"],
)

lesson(
    "gitops-rollback-reconcile-authority",
    "GitOps rollback: return desired state and controller authority together",
    "A manual rollback is temporary if the active controller still desires the broken revision.",
    "GitOps compares live resources with declared intent. Restoring an old Deployment directly in the cluster may be overwritten by self-healing or the next sync; restoring a historical Application state can also conflict with automated sync. A rollback plan names the known-good rendered release, the immutable image digest, how intent is changed, which controller is paused if needed, and the condition for restoring ordinary reconciliation. Database schema and external side effects may not be reversible with the manifest.",
    "A reconciliation API deploys a bad config generation. The on-call operator records the currently applied source and artifact digests, then selects an earlier accepted render whose image remains pullable and whose data contract still matches the migrated database. If automation would immediately reapply the bad commit, the operator pauses or narrows sync with a time-limited incident record, updates desired state to the known-good revision, reviews the rendered deletion set, and resumes reconciliation. A synthetic reconciliation request must succeed before the incident is closed. Run a negative drill: patch the live Deployment to a previous image while leaving Git unchanged, then observe how the controller handles it. A direct patch is acceptable only as a bounded emergency action with the intended Git change queued and a known reversion path. Verify secret and ConfigMap generations, not just the container image; the earlier image may fail against the newer configuration. Preserve the failed release's evidence for investigation, and check that rollback artifacts and any admission statements still exist in the destination registry.",
    "text",
    "Reconciliation API rollback\nFailed release: source, render, image, config generation\nCandidate: accepted prior render and data compatibility\nControl: sync pause owner and expiry if needed\nIntent: revert or explicit prior revision in Git\nPre-sync: deletion and retained-resource review\nProof: controller observes target and user path passes\nExit: ordinary reconciliation restored",
    "A rollback is at least one render, review, sync, rollout, and user probe; its elapsed time depends on image availability, scheduling, and data compatibility. Keeping prior images and evidence consumes registry storage, but deleting them can turn rollback into a rebuild under incident pressure. Measure emergency patches that lack a matching intent change, pause duration, rollback user-path time, and controller reapplication of the failed revision.",
    ["Do not rely on a live kubectl patch while self-healing still targets the bad revision.", "Do not assume an earlier image is compatible with the current database schema.", "Do not forget to restore ordinary reconciliation after the incident."],
    ["devops/gitops-emergency-change", "devops/rollback-image-retention", "devops/database-change-safety", "devops/release-evidence-record"],
)

lesson(
    "gitops-fleet-promotion-cohorts",
    "Fleet promotion: bound the number of clusters changed at once",
    "A shared desired-state change can affect many clusters before operators see the first customer failure.",
    "Fleet promotion groups targets into explicit cohorts with maximum concurrency, stable selection rules, health and user-path gates, and a stop action. A controller's creation order or a branch update is not a safety policy. Review the exact target set for each wave; label changes, missing selectors, or an unselected cluster can alter coverage. Distinguish application health from business acceptance, and define how to hold later cohorts without rolling back already healthy ones.",
    "A fulfillment platform ships a new sidecar to 27 clusters. The first cohort contains one low-traffic cluster, the second has three diverse environments, and the remainder is split by region and capacity. Before release, generate the target matrix from current cluster inventory and compare it with the intended set. A promotion record pins the same rendered input and image digest for every cohort; any cluster-specific overlay difference is listed separately. Advance only after the previous group reports observed revision, healthy workloads, and successful synthetic fulfillment. If one cluster fails, stop new syncs, preserve its logs and render, and inspect whether the failure follows architecture, policy, or local dependency. A later cohort must not start simply because the first group's controller status changed to Healthy for a moment. Test the stop path in an isolated fleet and include a cluster with an intentionally stale source artifact. Record clusters that were not selected so the rollout does not end with a silent old-version island. When recovery begins, use the same cohort limits to avoid multiplying rollback load across every cluster at once.",
    "text",
    "Fulfillment fleet contract\nTarget inventory: 27 named clusters at release start\nCohorts: 1, then 3, then bounded regional groups\nPer-cluster: source, render, image, observed revision\nAdvance: workload health plus synthetic fulfillment\nStop: failed group blocks unsynced targets\nException: unselected or stale cluster requires disposition\nRollback: bounded groups with user-path proof",
    "For K clusters and G cohorts, status collection is O(K) per polling pass; too-frequent probes multiply API and application load. Smaller cohorts reduce blast radius but increase total release time, especially when each gate waits for a long observation window. Measure maximum concurrent changes, time to first failure, unselected targets, source age, and customer errors by cohort. A fleet-wide rollback should be capacity tested, because it can stress registries and schedulers more than the original rollout.",
    ["Do not use alphabetical cluster order as a substitute for risk-based cohorts.", "Do not let a missing selector silently exclude a target.", "Do not advance a group on a momentary health status without user-path evidence."],
    ["devops/progressive-delivery", "devops/canary-cohort-analysis", "devops/cluster-upgrade-drill", "devops/registry-replica-promotion"],
)


titles = {row["path"]: row["title"] for row in rows}
titles.update({item["path"]: item["title"] for item in specs})
project_path = "devops/gitops-reconciliation-boundaries-project"
quiz_path = "quizzes/devops-gitops-operations-decisions"
titles[project_path] = "Project: test GitOps render, ownership, prune, and rollback boundaries"
titles[quiz_path] = "DevOps GitOps operating-boundary decisions"
assert all(path in titles for item in specs for path in item["related"])
assert project_path not in by_path and quiz_path not in by_path


def links(paths):
    return "<ul>" + "".join(
        f'<li><a href="/{html.escape(path)}">{html.escape(titles[path])}</a></li>'
        for path in dict.fromkeys(paths)
    ) + "</ul>"


for heading, summary, slugs in [
    ("GitOps render identity", "Pin all render inputs and review complete environment output.", ["gitops-rendered-input-lock", "kustomize-overlay-diff-gate"]),
    ("Ownership and deletion", "Give each resource a controller of record and preview pruning.", ["gitops-resource-ownership-transfer", "gitops-prune-deletion-preview"]),
    ("Truth of release status", "Separate source, sync, health, and customer success signals.", ["gitops-sync-health-user-path", "gitops-source-staleness-boundary"]),
    ("Rollback and fleet control", "Return intent and controller authority together, then limit target cohorts.", ["gitops-rollback-reconcile-authority", "gitops-fleet-promotion-cohorts"]),
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
               category="DevOps", difficulty="Advanced", tags=["devops", "gitops"],
               sort_order=22600 + index, published_at=stamp, created_at=stamp, updated_at=stamp)
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
               summary="Prove that rendered intent, tracked ownership, deletion, and rollback produce the expected workload.",
               difficulty="Advanced", sort_order=22690,
               published_at=stamp, created_at=stamp, updated_at=stamp)
project["data"] = {"kind": "project", "reading_minutes": 10,
                   "author_path": "authors/aitrove-editorial", "subject_root": course,
                   "section_path": project_hub, "content_format": "html", "seo_ready": True,
                   "related": [{"path": target, "title": titles[target]} for target in project_related]}
project["body"] = (
    "<p>Use disposable clusters and repositories with a small invoice API. Put its workload in a Kustomize base, create two environment overlays, and reconcile each through a GitOps controller. The exercise is accepted only when source revisions and rendered objects match the approved candidate, one controller owns each resource, unexpected deletion is blocked, a customer-path probe passes, and a rollback returns both desired state and controller authority to a known-good release.</p>"
    "<h2>Prove the rendered candidate</h2><p>Pin the image by digest and every external chart, base, or values input by immutable revision. Render each overlay with a recorded tool version, compute a resource inventory, and compare it with the last accepted release. Change a shared base without editing production's overlay and verify production is still checked. Move an upstream values reference while holding the application commit fixed; the candidate must be detected as a different render. Add a patch whose target no longer matches and require a visible failure or review warning. Compare the controller's observed artifact with the approved input and inspect the running image after reconciliation.</p>"
    "<h2>Test ownership and pruning</h2><p>Create a shared ConfigMap that both Applications try to manage. Confirm collision detection or a deliberate ownership inventory catches it before two controllers alternately write the object. Transfer the ConfigMap to one owner with the old owner's deletion path disabled and verify its data and object identity after the old Application is removed. Remove a Deployment from the new render and inspect the proposed prune set. Then point the source at an empty directory and show the release guard blocks mass deletion. Keep one PVC and a namespace under a reviewed retention rule; verify the actual objects remain after the test, not just the controller status.</p>"
    "<pre><code class=\"language-text\">Invoice GitOps acceptance\nAll source, renderer, values, and image inputs pinned\nRendered resource identities match approved inventory\nNo two Applications claim the same managed resource\nUnexpected empty or large prune set blocked\nSync, health, runtime image, and invoice transaction pass\nSource outage reports stale artifact without restarting service\nRollback changes declared intent and restores normal sync\nFleet test holds later clusters after one failed cohort</code></pre>"
    "<h2>Separate health from customer success</h2><p>Delay delivery of the invoice-signing Secret while leaving the Deployment healthy. Require the synthetic invoice issue-and-read journey to fail the release gate. Then make the Git source unavailable after a successful revision and submit a new intent change; observe whether the service can continue on last-good while the pending change is clearly marked unapplied. Restore source access and confirm that the intended revision, not an unreviewed intermediate head, is applied. Keep timestamps for source fetch, sync, resource health, and user success so a false-green interval is visible.</p>"
    "<h2>Rollback and bound fleet impact</h2><p>Deploy a bad configuration and attempt a direct live patch without changing Git. Observe whether reconciliation replaces it. Perform the reviewed rollback through desired-state change, verify image and data compatibility, and resume ordinary sync. Repeat across several disposable clusters in two or more cohorts; force the first cohort to fail and prove later targets do not advance. Record unselected clusters, source age, resource diffs, prune candidates, rollback time, and customer-path failures. Mark provider- or controller-version-specific behavior unverified if the disposable environment does not reproduce it.</p>"
    "<h3>Common Mistakes</h3><ul><li>Do not approve a patch without seeing its full rendered output.</li><li>Do not delete an Application before inspecting its resource-retention behavior.</li><li>Do not count Synced as proof an invoice can be issued.</li></ul>"
    "<h2>Connected lessons</h2>" + links([*project_related, project_hub])
)
rows.append(project)
by_path[project_hub]["data"]["modules"][0]["lessons"].append(project_path)
by_path[project_hub]["body"] += "<h2>GitOps operating-boundary drill</h2>" + links([project_path])
by_path[project_hub]["updated_at"] = stamp

questions = [
    ("What identifies a rendered GitOps release with multiple sources?", ["Every immutable input, renderer, image digest, and resulting resource set", "Only the application repository branch", "Only the controller version"], "External charts and values can change output without changing the application commit."),
    ("What should be reviewed after a shared Kustomize base changes?", ["Every affected overlay's complete rendered output", "Only the changed base lines", "Only the development overlay"], "A shared base can alter production with no overlay file edit."),
    ("Why reject duplicate resource identities from multiple sources?", ["One source may override another while sync still proceeds", "Kubernetes forbids every duplicate filename", "The chart package cannot be fetched"], "The final object may not match the reviewer's expected source."),
    ("What is required before transferring a Service to a new Application?", ["Old owner's update and deletion behavior must be controlled", "Both owners should sync at once", "The Service should be deleted first"], "The old owner can still overwrite or prune the adopted object."),
    ("What makes an empty desired inventory dangerous?", ["It may trigger deletion of previously tracked objects", "It always disables the controller", "It forces image signing"], "A missing source path can look like intentional removal."),
    ("What should a prune review list?", ["Current and target identities plus delete, retain, and transfer decisions", "Only resources that remain", "Only container images"], "Deletion is a separate release action."),
    ("What does Synced fail to establish by itself?", ["That the customer journey works", "That tracked fields match the render", "That an Application exists"], "Configuration comparison is not an end-to-end service test."),
    ("What state should be recorded during a Git source outage?", ["Last fetched revision, artifact age, source error, and pending intent", "Only healthy Pod count", "Only the latest local branch name"], "A healthy old workload may coexist with unapplied changes."),
    ("Why can a live rollback patch be short-lived?", ["The controller may restore the still-declared bad revision", "Kubernetes deletes all old images", "DNS ignores Git"], "Desired state and reconciliation authority must return together."),
    ("What else must be checked before reverting an image?", ["Current schema and configuration compatibility", "Only the image tag spelling", "Only the previous replica count"], "Earlier code can fail against newer data and secrets."),
    ("When should a fleet cohort advance?", ["After observed revision, workload health, and user-path success", "At the first momentary green status", "As soon as the branch advances"], "A staged rollout needs a stable acceptance gate."),
    ("What must a fleet report say about an unselected cluster?", ["Name it and give it an explicit disposition", "Treat it as silently complete", "Delete it from inventory"], "Missing selector coverage can leave old-version islands."),
]
quiz = copy.deepcopy(by_path["quizzes/devops-operations"])
quiz.update(id=str(uuid.uuid5(uuid.NAMESPACE_URL, "aitrove:" + quiz_path)), path=quiz_path,
            title=titles[quiz_path], summary="Twelve decisions on render identity, ownership, pruning, source freshness, and fleet rollout.",
            sort_order=22700, published_at=stamp, created_at=stamp, updated_at=stamp)
quiz["data"] = {"subject_root": course, "section_path": quiz_hub, "content_format": "html",
                "author_path": "authors/aitrove-editorial", "seo_ready": True, "duration_minutes": 12,
                "related": [{"path": target, "title": titles[target]} for target in project_related],
                "questions": [dict(prompt=prompt, options=options[index % 3:] + options[:index % 3],
                                   answer=(-index % 3) % 3, explanation=explanation)
                              for index, (prompt, options, explanation) in enumerate(questions)]}
quiz["body"] = (
    "<p>Decide whether the proposed GitOps action preserves a reproducible render, a single owner per resource, a bounded deletion set, and customer-path acceptance. Distinguish a healthy last-good workload from a fresh approved deployment.</p>"
    "<h2>Review these lessons</h2>" + links(project_related)
    + "<h2>Other checks</h2>" + links([quiz_hub, "quizzes/devops-recovery-execution-decisions", "quizzes/devops-artifact-trust-decisions"])
    + "<h3>Common Mistakes</h3><ul><li>Do not equate a source commit with the final rendered release.</li><li>Do not let auto-sync erase an emergency rollback without an intent change.</li></ul>"
)
rows.append(quiz)
by_path[quiz_hub]["data"]["modules"][0]["lessons"].append(quiz_path)
by_path[quiz_hub]["body"] += "<h2>GitOps operating-boundary check</h2>" + links([quiz_path])
by_path[quiz_hub]["updated_at"] = stamp

for item in specs:
    row = next(row for row in rows if row["path"] == item["path"])
    row["body"] += "<h2>Practice and check</h2>" + links([project_path, quiz_path])
    row["data"]["related"].extend({"path": path, "title": titles[path]} for path in [project_path, quiz_path])

for source, targets in {
    "devops/gitops-reconciliation": ["devops/gitops-rendered-input-lock", "devops/gitops-sync-health-user-path", "devops/gitops-source-staleness-boundary"],
    "devops/helm-release-review": ["devops/gitops-rendered-input-lock", "devops/gitops-resource-ownership-transfer"],
    "devops/gitops-crd-rollout-order": ["devops/kustomize-overlay-diff-gate", "devops/gitops-prune-deletion-preview"],
    "devops/gitops-emergency-change": ["devops/gitops-rollback-reconcile-authority"],
    "devops/stuck-finalizer-recovery": ["devops/gitops-prune-deletion-preview"],
    "devops/progressive-delivery": ["devops/gitops-fleet-promotion-cohorts"],
    "devops/release-evidence-record": ["devops/gitops-rendered-input-lock", "devops/gitops-sync-health-user-path"],
    "devops/reconcile-production-boundaries-project": [project_path],
}.items():
    row = by_path[source]
    row["body"] += "<h2>GitOps operating-boundary follow-up</h2>" + links(targets)
    row["data"].setdefault("related", []).extend({"path": target, "title": titles[target]} for target in targets)
    row["updated_at"] = stamp

assert len({row["path"] for row in rows}) == len(rows)
fixture.write_text(json.dumps(rows, ensure_ascii=False, indent=2) + "\n")
print(json.dumps({"new_lessons": len(specs), "new_projects": 1, "new_quiz_banks": 1, "total_records": len(rows)}))
