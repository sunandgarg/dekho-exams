"""Add Kubernetes storage lifecycle contracts to the local DevOps preview."""

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
    "readwriteoncepod-writer-fence", "ReadWriteOncePod: enforce one Kubernetes writer for one claim",
    "Distinguish a node-level mount rule from a Pod-level single-writer rule.",
    "ReadWriteOnce permits a volume to be mounted read-write by one node; it does not, by itself, prohibit two Pods on that same node from writing through the mount. ReadWriteOncePod is the access mode intended to restrict a compatible CSI volume to one Pod at a time. This is a scheduling and mount contract, not a distributed database lease or a guarantee against a process that still holds access outside the cluster.",
    "A receipt ledger keeps one writable segment on a persistent claim. Verify that the cluster version and CSI provisioner, attacher, and resizer support the Pod-level mode before changing a live claim. Create a disposable claim with the fragment below and schedule one writer. Attempt a second writer on the same node; it should wait rather than opening the same files. Then kill the first Pod during a simulated commit and inspect application recovery before permitting the replacement. Record the old writer's termination, volume unmount, and new writer's first successful transaction. A forced node loss can leave uncertainty about the prior process, so pair the mount rule with the ledger's own fencing or transaction recovery. Change an existing volume's access mode only through a supported migration procedure and a tested backup, not by assuming a claim edit will rewrite every bound resource safely.",
    "yaml", "apiVersion: v1\nkind: PersistentVolumeClaim\nmetadata:\n  name: receipt-ledger-writer\n  namespace: checkout\nspec:\n  accessModes:\n    - ReadWriteOncePod\n  storageClassName: receipt-csi-retain\n  resources:\n    requests:\n      storage: 47Gi",
    "Single-Pod enforcement can lengthen failover because the old mount must be released before the replacement starts. The extra waiting is preferable to concurrent corruption for a single-writer store, but it affects recovery objectives. Measure time from old-Pod failure to new-Pod write acceptance, mount conflict events, and incomplete transactions. The requested 47 GiB is capacity planning input, not a guarantee that the application can safely fill every byte; leave filesystem and recovery headroom.",
    ["Do not treat ReadWriteOnce as a one-Pod writer fence.", "Do not assume every CSI driver supports ReadWriteOncePod.", "Do not omit application-level recovery after the prior writer disappears."],
    ["devops/persistent-storage", "devops/failover-write-fencing", "devops/statefulset-rollout-safety", "devops/csi-volume-attach-ceiling"],
)

lesson(
    "wait-for-first-consumer-placement", "Delayed volume binding: choose storage topology with the first Pod",
    "Prevent a zonal disk from binding before the scheduler knows the workload constraints.",
    "A StorageClass using Immediate binding can provision a volume as soon as a claim appears, before a consuming Pod's node affinity, taints, or topology spread are considered. With zonal or local storage, that can leave the Pod unschedulable. WaitForFirstConsumer delays binding or provisioning until scheduling has a consumer to place, provided the driver and storage type support that mode.",
    "A receipt database must run in a zone that has both storage capacity and an available node. Inspect the current claim, StorageClass binding mode, PV node affinity, Pod placement rules, and scheduler events. Create a test class like the fragment below with an approved CSI driver and its actual parameters. Request a claim, then create the database Pod; confirm the selected PV zone agrees with the Pod's eligible nodes. Repeat with one zone intentionally out of capacity and observe whether the scheduler chooses another allowed zone. Do not set Pod nodeName directly in this test: bypassing the scheduler can leave a delayed-binding claim pending. If the workload must stay in one zone, state that constraint explicitly and plan a restore or replication route for zone loss. A binding mode change on a class does not move volumes already provisioned under it.",
    "yaml", "apiVersion: storage.k8s.io/v1\nkind: StorageClass\nmetadata:\n  name: receipt-zonal-retain\nprovisioner: ebs.csi.aws.com\nreclaimPolicy: Retain\nvolumeBindingMode: WaitForFirstConsumer\nallowVolumeExpansion: true",
    "Delayed binding adds scheduling time before the first Pod can start. It reduces stranded zonal disks but cannot create capacity that the provider lacks. A Retain policy in the sample also creates a manual reclamation and billing obligation. Measure claim Pending duration, provisioning failures, zone distribution, and volumes whose affinity no longer has eligible nodes. Test the exact CSI driver and cloud account; the sample class expresses a contract, not a complete provider installation.",
    ["Do not interpret a Pending claim as automatically broken under delayed binding.", "Do not bypass the scheduler with nodeName when the claim waits for its first consumer.", "Do not expect a new StorageClass setting to relocate an existing PV."],
    ["devops/persistent-storage", "devops/topology-spread-placement", "devops/node-autoscaling-headroom", "devops/provider-quota-preflight"],
)

lesson(
    "pvc-expansion-two-stage-check", "PVC expansion: verify both backing volume and usable filesystem",
    "Grow capacity through the claim and check what the application can actually write.",
    "A PVC size increase requests more storage from a supporting driver and StorageClass. Provisioning the larger backing volume and growing the filesystem are related but distinct stages. Some filesystems and drivers can complete growth while mounted; others require a remount or Pod restart. Kubernetes volume expansion grows a claim but does not provide a general shrink operation. A larger requested number is not evidence that the database sees more usable space.",
    "The receipt ledger has 8 GiB free and its ingestion forecast needs 31 GiB of additional headroom. Confirm the StorageClass permits expansion, the CSI driver supports it, the provider quota and billing allow the target size, and a restorable copy exists. Patch a disposable claim to the reviewed size shown below, then watch claim conditions, controller and node events, PV capacity, and filesystem free space inside the Pod. Write and read a synthetic record beyond the old capacity boundary. If the controller expands the device but the filesystem does not grow, follow that driver and filesystem's restart procedure during a maintenance window; do not repeatedly increase the request in hope of clearing a stuck condition. Record the original and target size, expansion latency, and the point at which the application can use the space. Repeat the procedure after an injected node restart.",
    "bash", "kubectl -n checkout patch pvc receipt-ledger-writer --type merge -p '{\"spec\":{\"resources\":{\"requests\":{\"storage\":\"79Gi\"}}}'\nkubectl -n checkout describe pvc receipt-ledger-writer",
    "Capacity charges normally increase with provisioned volume size, and some providers also charge for performance tiers or snapshots. Expansion may consume I/O and delay a restart, so schedule it before the filesystem is nearly full. Measure application-visible free bytes, expansion duration, failed resize events, and database write latency. The numerical target is illustrative: calculate it from growth rate, retention, filesystem reserve, and provider limits for the real workload.",
    ["Do not edit the PV capacity field directly as a substitute for a PVC resize.", "Do not assume a larger PVC request means the filesystem has grown.", "Do not plan to shrink the same claim after an overestimate."],
    ["devops/persistent-storage", "devops/inode-exhaustion-recovery", "devops/csi-volume-attach-ceiling", "devops/backup-and-recovery"],
)

lesson(
    "pv-reclaim-policy-deletion-path", "PV reclaim policy: trace the real asset before deleting a claim",
    "Make Delete and Retain behavior a reviewed data-lifecycle decision.",
    "A PersistentVolume's reclaim policy determines what happens after its claim is released. Delete can remove the PV and its backing storage asset when the provisioner supports deletion. Retain leaves the released asset for an administrator to reclaim manually. The StorageClass supplies a policy to newly provisioned PVs, but the live PV's policy is the value that matters during an actual claim deletion. A retained disk is not automatically a usable backup.",
    "A checkout namespace is being retired while receipt archives must remain available for seven more months. Identify the claim, bound PV, provider volume ID, reclaim policy, snapshots, encryption key, and documented owner. Confirm the live PV is set to Retain before deleting the claim, then rehearse in a disposable namespace. Observe the released PV and cloud asset after deletion; store its identifiers in a restricted handoff record. Test reattachment through a separate recovery claim or approved restore path rather than assuming a Released PV can be claimed without manual preparation. If Delete is intended for ephemeral review data, verify the provider asset actually disappears and no customer records were copied into it. A finalizer may delay object deletion while in use; investigate the active reference instead of removing protection blindly. Review class defaults when creating new workloads, because an omitted policy may not match the retention requirement.",
    "bash", "kubectl -n checkout get pvc receipt-archive -o wide\nkubectl get pv -o custom-columns=NAME:.metadata.name,CLAIM:.spec.claimRef.name,POLICY:.spec.persistentVolumeReclaimPolicy,STATUS:.status.phase",
    "Retain prevents automatic deletion but leaves storage billing, access-control, and erasure work to operators. Delete reduces orphan cost but can remove the only copy if the recovery plan was assumed rather than tested. Measure released volumes with no owner, assets deleted outside the retention window, and time to restore a retained claim. A snapshot or retained PV can still be unusable if its encryption key is gone or its data is inconsistent.",
    ["Do not infer the live PV policy solely from the current StorageClass definition.", "Do not call a retained disk a tested backup.", "Do not remove protection finalizers just to make a deletion command finish."],
    ["devops/persistent-storage", "devops/immutable-backup-retention", "devops/volume-snapshot-recovery", "devops/stuck-finalizer-recovery"],
)

lesson(
    "statefulset-pvc-retention-contract", "StatefulSet PVC retention: separate scale-down from deletion",
    "Keep data for removed ordinals unless a tested purge is intended.",
    "A StatefulSet can define separate claim-retention behavior when the set is deleted and when it scales down. The default Retain behavior preserves claims created from volume claim templates; choosing Delete for either transition makes those claims eligible for deletion under that event. Claim deletion then interacts with the bound PV's reclaim policy, so a Pod count change can lead to a storage-asset consequence far beyond scheduling.",
    "A three-replica receipt index is temporarily scaled to two replicas. Before changing the count, map each ordinal to its claim, volume ID, data generation, and restore point. In a test cluster with the required feature support, use the fragment below to retain claims during both scale-down and set deletion. Scale from three to two and confirm the third claim remains and is not mounted by another Pod. Scale back to three and verify that the ordinal recovers its expected data, not a newly empty volume. Then test a deliberate Delete policy in a disposable set and observe both the PVC deletion and the PV reclaim behavior. If the database rebalances or discards shards on scale-down, coordinate that application operation before touching replica count. A retained claim consumes storage and may hold a zone constraint, but it preserves a fast path back only if the data format remains compatible.",
    "yaml", "apiVersion: apps/v1\nkind: StatefulSet\nmetadata:\n  name: receipt-index\n  namespace: checkout\nspec:\n  persistentVolumeClaimRetentionPolicy:\n    whenDeleted: Retain\n    whenScaled: Retain",
    "Retaining an ordinal's claim costs storage even while its Pod is absent. Deleting it can lower cost but requires a recovery copy and may extend scale-up time. The fragment is the policy portion of a StatefulSet and needs the full selector, template, service name, and claim template before application. Measure orphaned ordinal claims, reuse success, data-generation match, and provider assets after deletion. Verify cluster version and feature availability rather than assuming every older control plane honors the field.",
    ["Do not equate scaling down a StatefulSet with safe data deletion.", "Do not ignore the PV reclaim policy beneath a deleted PVC.", "Do not assume a retained claim contains a compatible shard after application upgrades."],
    ["devops/statefulset-rollout-safety", "devops/persistent-storage", "devops/volume-snapshot-recovery", "devops/pv-reclaim-policy-deletion-path"],
)

lesson(
    "fsgroup-volume-startup-cost", "Volume ownership changes: keep fsGroup from turning recovery into a long mount",
    "Measure permission work before tuning a large-volume Pod restart.",
    "A Pod fsGroup can make mounted files accessible to a process group, but changing ownership and permissions across a large volume may delay startup. The fsGroupChangePolicy field can skip recursive work when the volume root already matches the expected ownership for supported volume types. Some CSI drivers perform group handling themselves; in that case the Kubernetes-side policy may not control the mount time. Permission tuning must preserve data access, not merely shorten a readiness graph.",
    "A receipt archive Pod spends several minutes before its application container starts after moving to a new node. Compare scheduling, attach, mount, ownership-change, and application-start timestamps. Inspect the security context, volume root ownership, CSI driver capabilities, and file count before changing policy. In a disposable copy of the volume, test OnRootMismatch as shown below, first with a matching root and then with an intentionally wrong root. Confirm the application can read and write a sample file owned by the actual workload identity after both mounts. If the driver owns the group change, inspect its mount behavior rather than assuming the field altered it. Avoid a broad root-level chmod or chown across a production volume during an incident; it can be slow and can change access beyond the target service. Record cold and warm mount time separately.",
    "yaml", "apiVersion: v1\nkind: Pod\nmetadata:\n  name: receipt-archive-check\n  namespace: checkout\nspec:\n  securityContext:\n    runAsUser: 2047\n    runAsGroup: 2047\n    fsGroup: 2047\n    fsGroupChangePolicy: OnRootMismatch\n  containers:\n    - name: archive-check\n      image: registry.internal/receipt-archive@sha256:aaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaa\n      command: [\"/app/check-volume\"]\n      volumeMounts:\n        - name: archive\n          mountPath: /data\n  volumes:\n    - name: archive\n      persistentVolumeClaim:\n        claimName: receipt-archive",
    "Skipping a recursive walk can cut mount latency for a large, correctly owned tree. It also means nested files with unexpected ownership are not repaired just because the root matches. Measure mount duration, file count, permission-denied errors, and recovery time after node loss. The image digest is a placeholder for an approved internal image and must be replaced before use. A root mismatch can still trigger the full walk, so plan for that slow path during failover.",
    ["Do not equate a faster mount with correct permissions on every nested file.", "Do not assume fsGroupChangePolicy controls a CSI driver that handles group mounts itself.", "Do not run an unbounded recursive ownership change during a production incident."],
    ["devops/persistent-storage", "devops/graceful-pod-shutdown", "devops/statefulset-rollout-safety", "devops/node-pressure-eviction"],
)

lesson(
    "raw-block-volume-mode-contract", "Raw block PVCs: make the application's formatting responsibility explicit",
    "Choose Block only when the workload owns block-device layout and recovery.",
    "A Filesystem PVC presents a mounted filesystem to the container. A Block PVC presents an unformatted block device through a volume device path. The latter can avoid a filesystem layer for software that manages its own storage layout, but it also transfers formatting, corruption detection, and recovery responsibility to that application. The PVC and PV volume modes must match during binding; changing a claim to Block is not a safe shortcut for improving a filesystem workload's throughput.",
    "A ledger engine can manage its own page layout. In an isolated cluster with a CSI driver that supports raw block, request a Block claim and map it to the container's device path as shown below. Verify the engine refuses to initialize a device with unexpected existing data, writes a recognizable generation marker, and can reopen it after a Pod restart. Test a mismatched filesystem-mode claim and confirm it does not silently bind as a raw device. Before every restore, check the backup format, device size, block alignment, and application version; copying a filesystem snapshot onto an application-formatted block device may not produce a usable ledger. Restrict device access to the intended Pod and retain a recovery copy before any initialization that could overwrite bytes. The sample is only a claim; the consuming Pod must use volumeDevices rather than volumeMounts.",
    "yaml", "apiVersion: v1\nkind: PersistentVolumeClaim\nmetadata:\n  name: receipt-ledger-block\n  namespace: checkout\nspec:\n  volumeMode: Block\n  accessModes:\n    - ReadWriteOncePod\n  storageClassName: receipt-csi-retain\n  resources:\n    requests:\n      storage: 63Gi",
    "Raw block can reduce one layer of overhead, but it increases the cost of application-specific formatting and recovery tests. It does not guarantee higher throughput; provider IOPS limits, queue depth, and write pattern may dominate. Measure sustained latency and recovery time against a filesystem baseline before choosing the mode. Capacity billing remains tied to provisioned storage, and a 63 GiB device may need internal metadata reserve that the application must account for.",
    ["Do not mount a Block claim as though it were a filesystem path.", "Do not initialize a raw device without proving which volume ID it is.", "Do not assume a filesystem snapshot restores an application-managed block layout."],
    ["devops/persistent-storage", "devops/readwriteoncepod-writer-fence", "devops/volume-snapshot-recovery", "devops/backup-and-recovery"],
)

lesson(
    "local-pv-node-loss-contract", "Local PVs: plan for node loss as a data-location failure",
    "A retained disk on a failed node is not an instantly movable replica.",
    "A local PersistentVolume represents storage tied to a specific node and carries node affinity so the scheduler can place a consuming Pod there. It can provide low-latency I/O, but another node cannot attach the same bytes when the original host fails. Pod rescheduling and storage recovery are separate operations. A healthy replica count before failure does not establish that data on a lost local volume can be served elsewhere.",
    "A receipt index stores rebuildable search segments on local SSD. Map each PV to node, zone, ordinal, and source data checkpoint. Use a StorageClass with delayed binding so the first consumer and available local PV are selected together; inspect the bound PV's node affinity before launch. Kill the test node and observe that the affected Pod cannot simply use that same local volume on a replacement node. Rebuild its segment from a verified upstream checkpoint onto a new claim, then compare document count and query results before rejoining traffic. If the local data is not rebuildable, the design needs replication or a backup and restore procedure with a measured recovery objective before deployment. During node maintenance, drain only after the replacement data path is ready; moving the Pod object alone does not move the disk. Track abandoned PVs on dead hosts for secure disposal and accounting.",
    "text", "Receipt local-volume recovery record\nPV identity: claim, node, zone, ordinal\nData source: upstream checkpoint and generation\nNode loss: old disk unavailable to replacement node\nRecovery: create new claim, rebuild, compare count and queries\nTraffic gate: rejoin only after data verification\nCleanup: retire old PV and physical media under owner approval",
    "Local SSD can improve latency and avoid network-storage charges, but it moves availability cost into replication, rebuild traffic, spare capacity, and operations. A large index may take hours to reconstruct, so calculate recovery time from actual ingest rate and throttling limits. Measure rebuild duration, source load, missing documents, and PVs stranded on failed nodes. Do not present a local PV as interchangeable with a network block volume during incident response.",
    ["Do not expect a local PV to attach to a replacement node.", "Do not route queries to a rebuilt shard before its generation is verified.", "Do not choose local storage for irreplaceable data without a tested recovery route."],
    ["devops/persistent-storage", "devops/wait-for-first-consumer-placement", "devops/node-autoscaling-headroom", "devops/backup-and-recovery"],
)

titles = {row["path"]: row["title"] for row in rows}
titles.update({item["path"]: item["title"] for item in specs})
project_path = "devops/storage-lifecycle-recovery-project"
quiz_path = "quizzes/devops-storage-lifecycle-decisions"
titles[project_path] = "Project: keep receipt data through Kubernetes storage transitions"
titles[quiz_path] = "DevOps storage lifecycle decisions"
unknown = {path for item in specs for path in item["related"] if path not in titles}
assert not unknown, unknown


def links(paths):
    return "<ul>" + "".join(
        f'<li><a href="/{html.escape(path)}">{html.escape(titles[path])}</a></li>'
        for path in paths
    ) + "</ul>"


for heading, summary, slugs in [
    ("Writer and placement rules", "Keep one writer and bind zonal storage with the consuming Pod.", ["readwriteoncepod-writer-fence", "wait-for-first-consumer-placement"]),
    ("Capacity and deletion paths", "Check usable space after growth and trace the reclaim action before claim deletion.", ["pvc-expansion-two-stage-check", "pv-reclaim-policy-deletion-path"]),
    ("Ordinal and mount lifetime", "Preserve StatefulSet claims intentionally and measure ownership work at startup.", ["statefulset-pvc-retention-contract", "fsgroup-volume-startup-cost"]),
    ("Device and node boundaries", "Give raw block devices an application owner and plan for local-node loss.", ["raw-block-volume-mode-contract", "local-pv-node-loss-contract"]),
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
               sort_order=21000 + index, published_at=stamp, created_at=stamp, updated_at=stamp)
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
               summary="Rehearse writer fencing, placement, growth, deletion, mount, and node-loss recovery.",
               difficulty="Advanced", sort_order=21090,
               published_at=stamp, created_at=stamp, updated_at=stamp)
project["data"] = {"kind": "project", "reading_minutes": 9,
                   "author_path": "authors/aitrove-editorial", "subject_root": course,
                   "section_path": project_hub, "content_format": "html", "seo_ready": True,
                   "related": [{"path": target, "title": titles[target]} for target in project_related]}
project["body"] = (
    "<p>Use a disposable Kubernetes cluster with a CSI driver that supports the selected access and expansion features, plus a separate local-volume test node. Create synthetic receipt data and an independent restorable copy before each destructive experiment. Record the claim, PV, provider asset, node or zone, application generation, reclaim policy, and owner. A bound claim is only the start of the acceptance check; finish with an application read and a verified recovery path.</p>"
    "<h2>Move a single writer</h2><p>Create a ReadWriteOncePod claim, start one ledger writer, and try to start a second on the same node. Verify the second cannot write concurrently. Fail the first Pod during a synthetic transaction, then measure the new writer's mount and transaction-recovery time. Provision a zonal claim with WaitForFirstConsumer and confirm the selected PV zone agrees with the Pod's placement rules. Repeat when one zone lacks capacity, and record Pending and scheduling events instead of labeling every delay a storage outage.</p>"
    "<pre><code class=\"language-text\">Receipt storage acceptance gates\nWriter: no concurrent Pod write to one claim\nPlacement: PV zone matches scheduled consumer\nExpansion: backing device and usable filesystem both grow\nReclaim: expected asset remains or is deleted after claim release\nStatefulSet: scaled ordinal retains its intended claim\nMount: ownership policy keeps access correct and startup bounded\nBlock: application recognizes the expected device generation\nLocal node loss: rebuilt data passes count and query checks</code></pre>"
    "<h2>Grow, remove, and restore</h2><p>Increase a test PVC request and verify both PV capacity and free bytes inside the container, then write past the prior capacity boundary. Scale a StatefulSet down and back up under Retain policies; compare ordinal and data generation. Delete a disposable claim first under Retain and then under Delete, checking the real provider asset each time. Mount a large copied volume with matching and mismatched fsGroup ownership to measure both paths. Present a raw block claim to a test application that knows its format and reject an unknown generation before writes. Finally remove a local-volume node, rebuild the affected index from a checkpoint, and keep it out of traffic until query results agree.</p>"
    "<h2>Cost and verification</h2><p>Report storage billed after Retain, expansion charge, mount delay, idle ordinal cost, and rebuild traffic after node loss. Include claim and PV identifiers in the evidence without exporting user data. If a driver or cluster version lacks one feature, mark that case unverified and use a compatible isolated environment; a YAML parse is not a storage test.</p>"
    "<h3>Common Mistakes</h3><ul><li>Do not call a larger claim a successful expansion until the application can use the space.</li><li>Do not infer asset deletion from the PVC object alone.</li><li>Do not treat local storage as a movable replica.</li></ul>"
    "<h2>Connected lessons</h2>" + links([*project_related, project_hub])
)
rows.append(project)
by_path[project_hub]["data"]["modules"][0]["lessons"].append(project_path)
by_path[project_hub]["body"] += "<h2>Storage lifecycle recovery drill</h2>" + links([project_path])
by_path[project_hub]["updated_at"] = stamp

questions = [
    ("What can ReadWriteOnce still permit on one node?", ["More than one Pod writing the same mounted volume", "A second node attaching automatically", "A tested database lease"], "It is a node-level access mode, not a one-Pod fence."),
    ("What must support ReadWriteOncePod?", ["The cluster and compatible CSI components", "Only the application label", "An HTTP readiness check"], "The access mode depends on compatible storage components."),
    ("Why delay binding a zonal volume?", ["The scheduler can consider the consuming Pod's constraints", "The disk becomes globally movable", "It removes provider quota"], "Early provisioning can choose a zone the Pod cannot use."),
    ("What can bypass scheduling and leave a delayed claim Pending?", ["Setting nodeName directly on the Pod", "Using a node selector", "Declaring a storage request"], "Delayed binding relies on scheduler participation."),
    ("What confirms a PVC expansion is useful?", ["The application sees and writes into the larger filesystem", "Only the requested size field changed", "The old volume was deleted"], "The backing device and filesystem can complete separately."),
    ("Can the same PVC be shrunk through ordinary expansion?", ["No, growth is supported but general shrink is not", "Yes, by editing the PV first", "Yes, when the Pod is unready"], "Plan capacity and migration accordingly."),
    ("Which policy leaves a released PV for manual reclamation?", ["Retain", "Delete", "Immediate"], "The provider asset still needs an owner and billing review."),
    ("Which reclaim value matters when deleting a live claim?", ["Its bound PV's current policy", "Only a newly edited StorageClass default", "The Pod's readiness result"], "The current PV policy determines the release path."),
    ("What does a StatefulSet scale-down Retain policy preserve?", ["The affected ordinal's template PVC", "The running Pod forever", "Every external backup"], "The claim remains even after the Pod is removed."),
    ("When may OnRootMismatch still be slow?", ["The volume root ownership differs and triggers a recursive change", "The Pod has no volume", "A cache hit skips the mount"], "The slow path remains when the root mismatches."),
    ("What must a Block-mode application's container expect?", ["A raw device and its own storage layout", "A preformatted directory mount", "A portable local PV"], "Block mode gives the application an unformatted device."),
    ("What restores service after a local-PV node is lost?", ["A tested rebuild or replication onto storage available to a new node", "Rescheduling the Pod with the same local bytes", "Changing only the Pod name"], "Local bytes remain tied to the failed node."),
]
quiz = copy.deepcopy(by_path["quizzes/devops-operations"])
quiz.update(id=str(uuid.uuid5(uuid.NAMESPACE_URL, "aitrove:" + quiz_path)), path=quiz_path,
            title=titles[quiz_path], summary="Twelve decisions on Kubernetes storage ownership and recovery.",
            sort_order=21100, published_at=stamp, created_at=stamp, updated_at=stamp)
quiz["data"] = {"subject_root": course, "section_path": quiz_hub, "content_format": "html",
                "author_path": "authors/aitrove-editorial", "seo_ready": True, "duration_minutes": 12,
                "related": [{"path": target, "title": titles[target]} for target in project_related],
                "questions": [dict(prompt=prompt, options=options[index % 3:] + options[:index % 3],
                                   answer=(-index % 3) % 3, explanation=explanation)
                              for index, (prompt, options, explanation) in enumerate(questions)]}
quiz["body"] = (
    "<p>Decide who may write a claim, where it can bind, when growth becomes usable, and whether a deletion reaches the backing asset. Confirm the application result and recovery path, not only the Kubernetes object phase.</p>"
    "<h2>Review these lessons</h2>" + links(project_related)
    + "<h2>Other checks</h2>" + links([quiz_hub, "quizzes/devops-ci-verification-decisions", "quizzes/devops-data-continuity-decisions"])
    + "<h3>Common Mistakes</h3><ul><li>Do not infer single-Pod safety from a node-level access mode.</li><li>Do not delete a claim before checking its bound PV policy.</li></ul>"
)
rows.append(quiz)
by_path[quiz_hub]["data"]["modules"][0]["lessons"].append(quiz_path)
by_path[quiz_hub]["body"] += "<h2>Storage lifecycle check</h2>" + links([quiz_path])
by_path[quiz_hub]["updated_at"] = stamp

for item in specs:
    row = next(row for row in rows if row["path"] == item["path"])
    row["body"] += "<h2>Practice and check</h2>" + links([project_path, quiz_path])
    row["data"]["related"].extend({"path": path, "title": titles[path]} for path in [project_path, quiz_path])

for source, targets in {
    "devops/persistent-storage": ["devops/readwriteoncepod-writer-fence", "devops/wait-for-first-consumer-placement", "devops/pvc-expansion-two-stage-check", "devops/pv-reclaim-policy-deletion-path"],
    "devops/statefulset-rollout-safety": ["devops/statefulset-pvc-retention-contract", "devops/fsgroup-volume-startup-cost"],
    "devops/volume-snapshot-recovery": ["devops/pv-reclaim-policy-deletion-path", "devops/raw-block-volume-mode-contract"],
    "devops/csi-volume-attach-ceiling": ["devops/readwriteoncepod-writer-fence"],
    "devops/topology-spread-placement": ["devops/wait-for-first-consumer-placement"],
    "devops/node-autoscaling-headroom": ["devops/local-pv-node-loss-contract"],
}.items():
    row = by_path[source]
    row["body"] += "<h2>Advanced follow-up</h2>" + links(targets)
    row["data"].setdefault("related", []).extend({"path": target, "title": titles[target]} for target in targets)
    row["updated_at"] = stamp

assert len({row["path"] for row in rows}) == len(rows)
fixture.write_text(json.dumps(rows, ensure_ascii=False, indent=2) + "\n")
print(json.dumps({"new_lessons": len(specs), "new_projects": 1, "new_quiz_banks": 1, "total_records": len(rows)}))
