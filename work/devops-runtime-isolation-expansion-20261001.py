"""Add runtime-isolation decisions to the local DevOps preview."""

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
    "pod-security-admission-rollout",
    "Pod Security Admission: stage warnings before a namespace denies Pods",
    "Collect violation evidence and control the policy version before enforcement.",
    "Pod Security Admission evaluates Pods against built-in privileged, baseline, or restricted standards. Namespace labels select enforce, warn, and audit behavior independently. Enforce rejects new nonconforming Pods; it does not retroactively terminate an existing Pod. A policy version label can hold the standard at a reviewed Kubernetes release while the cluster upgrades, so a security rule change does not arrive as an accidental side effect of a control-plane upgrade.",
    "A receipt-processing namespace contains application Pods and one legacy diagnostic sidecar. Begin with baseline enforcement and restricted warn and audit labels in a disposable namespace. Submit every Deployment, Job, init container, and debug-container workflow through server-side dry-run. Gather warnings and audit annotations, then fix or separate workloads with a real need for exceptions. The fragment pins the example labels to a cluster version; replace that version with one supported by the target control plane. Before moving enforce to restricted, calculate the number of Pods that a rolling restart would need to recreate and prove those manifests pass admission. Test a rollout and rollback, not only a currently running Pod. Keep highly privileged agents in separately governed namespaces and restrict who can create workloads there. Record every exemption with an owner and expiry; a broadly permissive namespace can bypass the intended boundary.",
    "yaml",
    "apiVersion: v1\nkind: Namespace\nmetadata:\n  name: receipt-processing\n  labels:\n    pod-security.kubernetes.io/enforce: baseline\n    pod-security.kubernetes.io/enforce-version: v1.36\n    pod-security.kubernetes.io/warn: restricted\n    pod-security.kubernetes.io/warn-version: v1.36\n    pod-security.kubernetes.io/audit: restricted\n    pod-security.kubernetes.io/audit-version: v1.36",
    "Warning and audit stages cost review time but expose blocked workloads before an outage. An abrupt enforce change can stall rollouts even while old Pods remain healthy, leaving a service unable to replace failed replicas. Measure dry-run violations, denied Pod creations, exception age, and replacement capacity under a simulated node drain. Pinning a policy version reduces surprise but requires an explicit review when the cluster standard advances.",
    ["Do not use a running Pod as proof that its replacement will pass a new enforce policy.",
     "Do not exempt a broad namespace merely to keep one privileged agent running.",
     "Do not copy the sample version label into a cluster that does not support it."],
    ["devops/admission-policy-guardrails", "devops/container-runtime-restrictions", "devops/cluster-upgrade-drill", "devops/policy-exception-expiry"],
)

lesson(
    "seccomp-runtime-default-portability",
    "Seccomp RuntimeDefault: test syscall behavior across node runtimes",
    "An explicit default profile still depends on the runtime installed on the node.",
    "Seccomp filters the system calls a container may make. RuntimeDefault selects the default profile supplied by the container runtime, rather than a single profile whose exact syscall list Kubernetes fixes for every cluster. Two node pools can therefore run a Pod with the same manifest and still differ in allowed calls after a runtime change. A privileged container is not made safe by declaring seccomp; test the effective security context on the node that actually runs it.",
    "A document-rendering service invokes a native font engine that uses less common kernel calls. Add RuntimeDefault at the Pod level, then run the full render path on every supported node image and runtime version in a canary pool. The fragment belongs in a Pod specification and applies unless a container overrides it. Collect denied-syscall events and application failures, including cold starts and font-cache rebuilds. Compare the profile and runtime version on healthy and failing nodes before weakening the policy. If a narrower Localhost profile is genuinely needed, distribute and verify the exact profile on every eligible node and test its update path before scheduling production Pods. Do not solve one denied call by setting Unconfined across the namespace. Confirm all init and sidecar containers that inherit the Pod-level profile still start and complete their work. Record the chosen runtime build with release evidence so a node upgrade has a known regression target.",
    "yaml",
    "securityContext:\n  seccompProfile:\n    type: RuntimeDefault",
    "Default filtering reduces kernel attack surface with little application work, but a runtime upgrade can change both security and compatibility. Measure denied calls, render error rate, startup time, and failures by node image. Testing one Pod on one node is cheap and incomplete; a small node matrix costs more CI capacity but is far less expensive than discovering a syscall mismatch during a fleet rollout. The fragment is only a Pod security-context section, not a standalone workload.",
    ["Do not assume RuntimeDefault has identical syscall rules on every runtime build.",
     "Do not switch to Unconfined without isolating the required call and reviewing risk.",
     "Do not ignore init and sidecar containers that inherit the Pod profile."],
    ["devops/container-runtime-restrictions", "devops/cluster-upgrade-drill", "devops/pod-security-admission-rollout", "devops/canary-cohort-analysis"],
)

lesson(
    "apparmor-node-profile-availability",
    "AppArmor profiles: match Pod placement to actual node enforcement",
    "A declared profile needs a capable node and the expected profile bytes.",
    "AppArmor constrains operations such as file access for a container process. An explicit RuntimeDefault request has different admission behavior from leaving the field unset when a node lacks AppArmor. A Localhost profile is resolved from a profile loaded on the node, so a Pod manifest alone cannot distribute its contents. Scheduling a restricted workload to a node without the required profile can fail or leave the intended rule unenforced, depending on the configuration.",
    "A claim-export worker is allowed to read its input directory but must not write to its policy directory. Build a test profile and install it through a controlled node-image or node-agent rollout, then verify its hash and active mode on every node eligible for the worker. The fragment shows only the container security-context field; the named Localhost profile must exist before this Pod can rely on it. Use a node label whose assignment is controlled by the platform team, and schedule a canary to each eligible node pool. Attempt one allowed export and one denied policy write, then inspect the kernel audit result and the application error. Repeat after a node replacement. For RuntimeDefault, test a node with AppArmor disabled and check whether an explicit field prevents admission; do not infer enforcement from a Pod phase alone. Keep the profile distribution path and rollback path in the same release record as the workload.",
    "yaml",
    "securityContext:\n  appArmorProfile:\n    type: Localhost\n    localhostProfile: receipt-exporter-deny-policy-write",
    "Custom profiles add node management and can reduce scheduling headroom until all eligible nodes are prepared. A profile that blocks a legitimate export produces an application outage, while a missing profile can defeat the intended isolation. Measure profile hash drift, Pod start failures by node, denied operations, and time to bring a replacement node into the eligible pool. The fragment is a container security-context section, not a complete Pod manifest.",
    ["Do not assume a Localhost profile is shipped inside the container image.",
     "Do not trust a label without checking the node's loaded profile and enforcement mode.",
     "Do not interpret a running Pod as proof that an omitted AppArmor field is enforced on every node."],
    ["devops/container-runtime-restrictions", "devops/seccomp-runtime-default-portability", "devops/node-autoscaling-headroom", "devops/pod-security-admission-rollout"],
)

lesson(
    "supplemental-group-merge-boundary",
    "Supplemental groups: remove unexpected access inherited from an image",
    "Review the process group set, not only runAsUser and fsGroup.",
    "A container process can inherit supplementary groups from the image's account database in addition to groups declared in a Pod security context. Those extra groups may grant access to mounted files even when runAsUser and runAsGroup look narrow. SupplementalGroupsPolicy Strict limits the group set to explicit Pod choices on supported nodes and runtimes. Its availability varies by Kubernetes and node runtime version, so mixed-node behavior must be checked before relying on it.",
    "A receipt-index worker should read an archive volume as group 3047 and nothing else. Inspect the image's account record and the process identity in a canary Pod. Apply the fragment below in a compatible test cluster, confirm the node advertises support, then compare the first process's UID, primary GID, and supplementary groups with the intended set. Attempt reads of a permitted archive file and a decoy file owned by a group present only in the image. On older nodes or unsupported runtimes, verify whether the Pod is rejected or whether the intended rule is not enforced; do not silently keep using the same manifest. Keep the volume's fsGroup behavior separate from the process group calculation, because a mount permission change can also affect access. If the application performs its own setgroups call, test the effective identity after startup, not only the initial Pod status.",
    "yaml",
    "securityContext:\n  runAsUser: 2047\n  runAsGroup: 2047\n  fsGroup: 3047\n  supplementalGroupsPolicy: Strict",
    "Strict groups can expose image assumptions and cause permission errors that were masked by an undeclared image group. Fix the image or file ownership rather than adding broad groups until tests pass. Measure unexpected group memberships, denied file reads, and Pod start failures by node runtime. This Pod-level fragment needs a supported cluster and volume-permission review before deployment; the same group number can carry different business meaning in another workload.",
    ["Do not infer the full process group set from runAsUser alone.",
     "Do not assume every node supports Strict or has the same fallback behavior.",
     "Do not add a broad group solely to silence an access failure without checking the file owner."],
    ["devops/container-runtime-restrictions", "devops/fsgroup-volume-startup-cost", "devops/apparmor-node-profile-availability", "devops/pod-security-admission-rollout"],
)

lesson(
    "read-only-root-scratch-contract",
    "Read-only root filesystems: inventory every required write path",
    "Move temporary writes into bounded volumes before enforcing the flag.",
    "readOnlyRootFilesystem prevents a container from writing to its image root filesystem. It does not make mounted volumes read-only, and it does not eliminate the need for scratch space. Libraries may write temporary files, caches, sockets, or certificates during startup and on rare request paths. A successful readiness probe therefore does not prove the workload can run through a full transaction under this setting.",
    "An invoice renderer writes generated PDFs into a temporary directory and then uploads them to object storage. Trace writes during startup, normal render, large-document render, font-cache rebuild, and graceful shutdown. Put only the required scratch directory on a bounded emptyDir and set the container root filesystem read-only. The fragment shows the relevant Pod-template fields; the application image and other Pod fields belong to the reviewed release manifest. Run a request that fills the scratch directory up to its planned limit and confirm the renderer rejects the job without filling the node. Separate the uploaded result from scratch so a Pod restart does not become data loss. Verify that sidecars and init containers have their own write paths; changing one application container's flag does not harden all containers in the Pod. If a component writes to an unexpected path, fix its configuration or image rather than mounting a writable directory over the whole root.",
    "yaml",
    "spec:\n  containers:\n    - name: invoice-renderer\n      securityContext:\n        readOnlyRootFilesystem: true\n      volumeMounts:\n        - name: render-scratch\n          mountPath: /var/tmp/render\n  volumes:\n    - name: render-scratch\n      emptyDir:\n        sizeLimit: 740Mi",
    "A read-only image layer reduces writable surface, but emptyDir still consumes node resources and disappears with the Pod. Its limit must fit peak concurrent renders, log growth, and rollout overlap without inviting node-pressure eviction. Measure scratch high-water mark, failed writes, upload completion, and restart recovery. This fragment is a Pod-template portion; it omits image, requests, limits, and other deployment-specific fields.",
    ["Do not assume readOnlyRootFilesystem makes mounted Secrets or data volumes read-only.",
     "Do not infer write-path completeness from startup alone.",
     "Do not store the only copy of an invoice in ephemeral scratch space."],
    ["devops/container-runtime-restrictions", "devops/ephemeral-storage-limit-accounting", "devops/node-pressure-eviction", "devops/object-replication-recovery"],
)

lesson(
    "user-namespace-volume-compatibility",
    "Pod user namespaces: verify host mapping and volume compatibility",
    "A container UID is not the same identity as the mapped host UID.",
    "A Pod user namespace maps container user IDs to different host IDs when hostUsers is false. This can reduce what a process that appears to be root inside the container can do on the node. It does not make a compromised application harmless. Node kernel, runtime, and filesystem support determine whether the Pod starts, and some volume or host-namespace combinations are incompatible with this mode.",
    "A media-conversion worker needs temporary files and a restricted input volume. In an isolated Linux node pool that supports user namespaces, launch a canary with hostUsers false and record the UID shown inside the container and the mapped host identity. Verify read and write permissions on every mounted volume and exercise the entire conversion path. The fragment is only the relevant Pod-spec portion; the production manifest must supply the approved image, resources, and placement. Confirm the storage driver's idmapped-mount support before migration. Raw block volumeDevices and NFS mounts are incompatible with user-namespace Pods in current Kubernetes behavior, and hostNetwork, hostPID, and hostIPC cannot be combined with hostUsers false. If the worker needs one of those facilities, do not force the flag into its manifest; isolate it through an alternative node and access design. Repeat after node upgrades because kernel and runtime changes can alter mount behavior.",
    "yaml",
    "spec:\n  hostUsers: false\n  securityContext:\n    runAsUser: 2047\n    runAsGroup: 2047\n  containers:\n    - name: media-converter\n      volumeMounts:\n        - name: conversion-scratch\n          mountPath: /var/tmp/conversion\n  volumes:\n    - name: conversion-scratch\n      emptyDir: {}",
    "User namespaces reduce host-identity exposure but add node and storage compatibility constraints. A failed mount can leave capacity stranded if only some nodes support the workload. Measure start failures by node, permission errors, eligible-node headroom, and host-versus-container UID mapping. The example UID is an application choice, not a promise about its exact host mapping; inspect the real mapping on the target runtime.",
    ["Do not equate container root with host root after a user namespace is enabled.",
     "Do not schedule a user-namespace Pod onto storage that lacks required idmapped mounts.",
     "Do not combine hostUsers false with raw block devices or prohibited host namespaces."],
    ["devops/container-runtime-restrictions", "devops/raw-block-volume-mode-contract", "devops/node-autoscaling-headroom", "devops/read-only-root-scratch-contract"],
)

lesson(
    "runtimeclass-isolation-overhead",
    "RuntimeClass: budget the real cost of a stronger sandbox",
    "A named runtime handler needs prepared nodes and explicit Pod overhead.",
    "RuntimeClass selects a container runtime configuration for a Pod. A class can route a sensitive workload to a stronger sandbox, but the named handler must exist on the selected nodes. A class can also declare scheduling constraints and Pod overhead so the scheduler and quota account for runtime infrastructure outside the application containers. A RuntimeClass object by itself does not install or verify the handler.",
    "A document-unpacking service handles untrusted archives. Install the isolated handler on a labeled node pool through a controlled node-image rollout, then define a RuntimeClass with matching scheduling and measured overhead. The fragment is illustrative configuration; the handler name, node label, and resource numbers must match a tested node pool before use. Launch a canary Pod using the class and unpack a hostile synthetic archive under a CPU and memory load representative of peak requests. Compare startup latency, throughput, memory footprint, and failure handling with the ordinary runtime. Drain a node and confirm a replacement Pod lands only where the handler is available. If the class is missing or the handler fails, the workload should fail visibly instead of silently falling back to the ordinary runtime. Include sandbox overhead in rollout surge capacity and namespace quota; container requests alone understate this placement cost.",
    "yaml",
    "apiVersion: node.k8s.io/v1\nkind: RuntimeClass\nmetadata:\n  name: archive-isolated\nhandler: archive-isolated\nscheduling:\n  nodeSelector:\n    platform.example.internal/archive-isolated: \"true\"\noverhead:\n  podFixed:\n    cpu: 90m\n    memory: 118Mi",
    "A stronger sandbox can reduce host exposure while increasing cold-start time, per-Pod memory, and node-pool cost. It can also narrow eligible placement so a node failure affects more Pods at once. Measure runtime overhead from the actual implementation, rejected or failed Pod starts, eligible-node spare capacity, and unpack throughput. The sample overhead is a planning example, not a benchmark result or a value safe to copy into an arbitrary runtime.",
    ["Do not treat a RuntimeClass object as proof that every node has its handler.",
     "Do not ignore runtime overhead when sizing quota and rollout surge.",
     "Do not silently fall back to an ordinary runtime when the isolation requirement is mandatory."],
    ["devops/container-runtime-restrictions", "devops/kubernetes-resource-budgets", "devops/node-autoscaling-headroom", "devops/pod-security-admission-rollout"],
)

lesson(
    "ephemeral-storage-limit-accounting",
    "Local ephemeral storage: account for logs, writable layers, and emptyDir",
    "A scratch-directory limit is only one part of a Pod's node-disk footprint.",
    "Kubernetes local ephemeral-storage requests influence scheduling, while limits can trigger eviction when measured usage exceeds the allowed amount. Non-memory emptyDir contents, container writable layers, and container logs can contribute to local storage use. A tmpfs emptyDir instead consumes memory. Files deleted while still open can be missed by directory-scan accounting, so measured use and actual node pressure may diverge.",
    "A document-import Pod expands compressed files before indexing. Estimate peak expanded bytes, application logs during a failed import, writable-layer changes, and the temporary overlap of a rolling update. Set an explicit ephemeral-storage request and limit, plus a smaller emptyDir sizeLimit for import scratch. The fragment is a container-and-volume portion of a Pod template. Fill scratch in a disposable node pool, then separately generate logs and writable-layer files; observe which limit and eviction signal appears in each case. Test the same workload with memory-backed emptyDir and confirm the memory budget, not disk budget, becomes the constraint. Inspect node filesystem layout because a kubelet that cannot measure local ephemeral storage as configured may not enforce a nominal per-Pod limit even while node disk pressure still evicts Pods. Add alerting for node free space and the importer's scratch high-water mark. Avoid retrying the same oversized archive indefinitely after eviction.",
    "yaml",
    "spec:\n  containers:\n    - name: document-importer\n      resources:\n        requests:\n          ephemeral-storage: 880Mi\n        limits:\n          ephemeral-storage: 2Gi\n      volumeMounts:\n        - name: import-scratch\n          mountPath: /var/tmp/import\n  volumes:\n    - name: import-scratch\n      emptyDir:\n        sizeLimit: 1400Mi",
    "A larger request lowers the chance of disk contention but reduces how many Pods fit on a node. A lower limit contains one workload's growth but may evict useful work during a legitimate large import. Measure bytes per document, expansion ratio, log rate, evictions, and node free space at surge peak. The chosen numbers are synthetic; derive a real budget from observed high-percentile imports and recovery headroom, and reject input above the safe bound before downloading it.",
    ["Do not equate emptyDir sizeLimit with the Pod's whole local-storage limit.",
     "Do not classify a tmpfs emptyDir as disk usage; it consumes memory.",
     "Do not assume a deleted-but-open file frees node space immediately."],
    ["devops/kubernetes-resource-budgets", "devops/node-pressure-eviction", "devops/inode-exhaustion-recovery", "devops/read-only-root-scratch-contract"],
)

titles = {row["path"]: row["title"] for row in rows}
titles.update({item["path"]: item["title"] for item in specs})
project_path = "devops/runtime-isolation-recovery-project"
quiz_path = "quizzes/devops-runtime-isolation-decisions"
titles[project_path] = "Project: harden a document worker without losing its recovery path"
titles[quiz_path] = "DevOps runtime isolation decisions"
assert all(path in titles for item in specs for path in item["related"])


def links(paths):
    return "<ul>" + "".join(
        f'<li><a href="/{html.escape(path)}">{html.escape(titles[path])}</a></li>'
        for path in paths
    ) + "</ul>"


for heading, summary, slugs in [
    ("Admission and syscall boundaries", "Stage policy enforcement and verify runtime syscall filtering on each node pool.", ["pod-security-admission-rollout", "seccomp-runtime-default-portability"]),
    ("Node and process identity", "Prove AppArmor profile availability and the actual process group set.", ["apparmor-node-profile-availability", "supplemental-group-merge-boundary"]),
    ("Filesystem and user mapping", "Bound writable scratch and test user-namespace storage compatibility.", ["read-only-root-scratch-contract", "user-namespace-volume-compatibility"]),
    ("Sandbox and local capacity", "Price runtime overhead and include all local disk consumers in placement decisions.", ["runtimeclass-isolation-overhead", "ephemeral-storage-limit-accounting"]),
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
               sort_order=21400 + index, published_at=stamp, created_at=stamp, updated_at=stamp)
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
               summary="Test security enforcement, node compatibility, and recovery under bounded storage.",
               difficulty="Advanced", sort_order=21490,
               published_at=stamp, created_at=stamp, updated_at=stamp)
project["data"] = {"kind": "project", "reading_minutes": 9,
                   "author_path": "authors/aitrove-editorial", "subject_root": course,
                   "section_path": project_hub, "content_format": "html", "seo_ready": True,
                   "related": [{"path": target, "title": titles[target]} for target in project_related]}
project["body"] = (
    "<p>Use disposable namespaces and node pools with known kernel, runtime, AppArmor, and storage capabilities. Run a document-unpacking worker against synthetic archives, including one oversized file and one file intended to test a denied policy write. Record the exact manifest revision, node image, security profile hash, and active process identity before fault injection. Keep the worker out of production traffic until the full unpack, upload, restart, and rollback path is observed.</p>"
    "<h2>Prove the boundaries</h2><p>Stage baseline enforce with restricted warn and audit, then server-side dry-run every workload template. Move to restricted enforcement only after a replacement Pod survives a drain. Test RuntimeDefault seccomp across two node-runtime builds. Install a custom AppArmor profile on only part of a disposable node pool and verify unsupported placement fails visibly; then distribute it and repeat. Compare process groups under Merge and Strict on supported nodes, using a decoy file to expose unintended access. Confirm the image root is read-only and that every required write lands in a bounded scratch mount.</p>"
    "<pre><code class=\"language-text\">Document worker acceptance gates\nAdmission: replacement Pod passes reviewed policy version\nSeccomp: supported render and unpack paths work on every node build\nAppArmor: profile hash and denied write are verified\nGroups: process lacks undeclared image groups\nRoot: required writes use bounded scratch, never the image layer\nUser namespace: host mapping and every volume mount are tested\nRuntimeClass: handler exists and overhead fits surge capacity\nDisk: logs, layers, and emptyDir stay inside node headroom</code></pre>"
    "<h2>Inject failure and recover</h2><p>Launch a user-namespace canary with compatible storage, then try a separately isolated incompatible-volume test and record the mount failure. Use an isolated RuntimeClass on prepared nodes; remove one eligible node and verify replacement headroom. Fill scratch, then grow logs and the writable layer independently to exercise local-storage accounting. Observe whether the Pod is evicted and whether the queue lease releases for replay. Roll back the hardening change through the reviewed manifest, preserving the denied-path audit evidence. Do not weaken every workload's policy because one worker has an undeclared file path.</p>"
    "<h2>Cost and verification</h2><p>Report policy violations, denied syscalls and file accesses, node-specific start failures, initial process groups, eligible-node capacity, sandbox cold-start cost, and disk high-water marks. State which behavior was verified on an actual node and which was only parsed as configuration. A manifest accepted by the API server does not prove the runtime handler or security profile exists on the scheduled node.</p>"
    "<h3>Common Mistakes</h3><ul><li>Do not enforce a new policy before testing replacement Pods.</li><li>Do not assume a declared profile is present on every node.</li><li>Do not count only emptyDir when sizing local ephemeral storage.</li></ul>"
    "<h2>Connected lessons</h2>" + links([*project_related, project_hub])
)
rows.append(project)
by_path[project_hub]["data"]["modules"][0]["lessons"].append(project_path)
by_path[project_hub]["body"] += "<h2>Runtime isolation drill</h2>" + links([project_path])
by_path[project_hub]["updated_at"] = stamp

questions = [
    ("What does Pod Security enforce do to an existing nonconforming Pod?", ["It does not retroactively terminate it", "It deletes it immediately", "It rewrites its security context"], "Enforcement applies when a new Pod is admitted."),
    ("Why pin a Pod Security policy version?", ["To review rule changes separately from a control-plane upgrade", "To install a runtime handler", "To encrypt a Secret"], "A pinned standard avoids unreviewed policy drift."),
    ("Can RuntimeDefault seccomp vary across node pools?", ["Yes, runtime builds can supply different default profiles", "No, Kubernetes fixes one syscall list forever", "Only when a ConfigMap changes"], "The selected runtime supplies the profile."),
    ("What must accompany a Localhost AppArmor profile?", ["The expected profile loaded on every eligible node", "Only a name inside the image", "A PVC reclaim policy"], "The manifest does not distribute node profiles."),
    ("What can Merge add to a Pod's group set?", ["Supplementary groups from the image account database", "Cloud IAM roles", "Kubernetes node labels"], "The process can inherit groups not written in the Pod security context."),
    ("What should be checked before relying on Strict groups?", ["Cluster and node-runtime support plus the effective process identity", "Only the Pod name", "Only the filesystem size"], "Support and effective groups are runtime facts."),
    ("What remains writable with readOnlyRootFilesystem?", ["Writable mounted volumes", "The image root layer", "Every host directory"], "The flag affects the image root, not all mounts."),
    ("What is a critical user-namespace volume check?", ["Whether the node and filesystem support the required idmapped mounts", "Whether the Pod has a public IP", "Whether the ConfigMap is immutable"], "Unsupported mounts can keep the Pod from starting."),
    ("Can a user-namespace Pod use raw block volumeDevices in the documented mode?", ["No", "Yes, always", "Only when the Pod is privileged"], "That combination is incompatible in the current contract."),
    ("What does RuntimeClass overhead account for?", ["Runtime infrastructure beyond container requests", "Only application heap", "Only persistent storage"], "Scheduling and quota need the sandbox's resource cost."),
    ("What contributes to local ephemeral-storage use?", ["Logs, writable layers, and non-memory emptyDir", "Only persistent claims", "Only image download bytes"], "Several Pod-local paths can consume node disk."),
    ("Where is tmpfs emptyDir charged?", ["Memory", "Persistent volume capacity", "A remote object store"], "Memory-backed scratch changes the resource bottleneck."),
]
quiz = copy.deepcopy(by_path["quizzes/devops-operations"])
quiz.update(id=str(uuid.uuid5(uuid.NAMESPACE_URL, "aitrove:" + quiz_path)), path=quiz_path,
            title=titles[quiz_path], summary="Twelve decisions on runtime enforcement and recovery cost.",
            sort_order=21500, published_at=stamp, created_at=stamp, updated_at=stamp)
quiz["data"] = {"subject_root": course, "section_path": quiz_hub, "content_format": "html",
                "author_path": "authors/aitrove-editorial", "seo_ready": True, "duration_minutes": 12,
                "related": [{"path": target, "title": titles[target]} for target in project_related],
                "questions": [dict(prompt=prompt, options=options[index % 3:] + options[:index % 3],
                                   answer=(-index % 3) % 3, explanation=explanation)
                              for index, (prompt, options, explanation) in enumerate(questions)]}
quiz["body"] = (
    "<p>Decide which isolation rules the API server checks, which protections require prepared nodes, and which resource costs appear only when a Pod runs. Validate a replacement workload before enforcing a new policy.</p>"
    "<h2>Review these lessons</h2>" + links(project_related)
    + "<h2>Other checks</h2>" + links([quiz_hub, "quizzes/devops-configuration-delivery-decisions", "quizzes/devops-storage-lifecycle-decisions"])
    + "<h3>Common Mistakes</h3><ul><li>Do not infer node enforcement from an admitted manifest.</li><li>Do not omit runtime overhead and scratch use from capacity planning.</li></ul>"
)
rows.append(quiz)
by_path[quiz_hub]["data"]["modules"][0]["lessons"].append(quiz_path)
by_path[quiz_hub]["body"] += "<h2>Runtime isolation check</h2>" + links([quiz_path])
by_path[quiz_hub]["updated_at"] = stamp

for item in specs:
    row = next(row for row in rows if row["path"] == item["path"])
    row["body"] += "<h2>Practice and check</h2>" + links([project_path, quiz_path])
    row["data"]["related"].extend({"path": path, "title": titles[path]} for path in [project_path, quiz_path])

for source, targets in {
    "devops/container-runtime-restrictions": ["devops/pod-security-admission-rollout", "devops/seccomp-runtime-default-portability", "devops/apparmor-node-profile-availability", "devops/supplemental-group-merge-boundary", "devops/read-only-root-scratch-contract", "devops/user-namespace-volume-compatibility", "devops/runtimeclass-isolation-overhead"],
    "devops/admission-policy-guardrails": ["devops/pod-security-admission-rollout"],
    "devops/fsgroup-volume-startup-cost": ["devops/supplemental-group-merge-boundary"],
    "devops/node-pressure-eviction": ["devops/ephemeral-storage-limit-accounting"],
    "devops/kubernetes-resource-budgets": ["devops/runtimeclass-isolation-overhead", "devops/ephemeral-storage-limit-accounting"],
    "devops/raw-block-volume-mode-contract": ["devops/user-namespace-volume-compatibility"],
    "devops/cluster-upgrade-drill": ["devops/seccomp-runtime-default-portability"],
}.items():
    row = by_path[source]
    row["body"] += "<h2>Advanced follow-up</h2>" + links(targets)
    row["data"].setdefault("related", []).extend({"path": target, "title": titles[target]} for target in targets)
    row["updated_at"] = stamp

assert len({row["path"] for row in rows}) == len(rows)
fixture.write_text(json.dumps(rows, ensure_ascii=False, indent=2) + "\n")
print(json.dumps({"new_lessons": len(specs), "new_projects": 1, "new_quiz_banks": 1, "total_records": len(rows)}))
