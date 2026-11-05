"""Extend the DevOps curriculum with host, cluster, security, and operations topics."""

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


lesson("linux-service-diagnostics", "Linux service diagnostics: process, socket, and journal",
       "Find whether a failed request reached the host, listener, and process.",
       "A service outage on a Linux host can be caused by a dead process, a listener bound to the wrong address, a failed dependency, or a route that never reached the host. Diagnose those layers in order. A process listed as running is weaker evidence than a successful user request; process state only says the operating system has not terminated it.",
       "For a report-renderer service managed by systemd, inspect the unit state, recent journal entries, and listening sockets before restarting anything. Compare the process start time with the first bad request. If the service listens only on loopback while the proxy expects another interface, a restart may not change the fault. If systemd has repeatedly restarted the unit, capture the exit code and the first failure before changing the restart policy. Run the commands under an account with appropriate read access, then verify a request through the same route users take. A local curl success does not test DNS, TLS, or the edge proxy. Record the exact command output and timestamps in the incident timeline; a temporary fix without the original failure evidence makes later repair harder.",
       "bash", "systemctl status report-renderer --no-pager\njournalctl -u report-renderer --since '20 minutes ago' --no-pager\nss -ltnp | grep ':8147'\ncurl --fail --silent --show-error 127.0.0.1:8147/health/ready",
       "Journal retention and host logging consume disk; size and rotate them without deleting the evidence needed for incident review. A restart is fast when a process is wedged, yet repeated restarts can amplify load or hide a dependency fault. The local health request in the sample is one layer of evidence, not a production availability test. Check the edge path and a user-facing operation before declaring recovery. Limit privileged diagnostic access and avoid placing secret values in collected logs.",
       ["Do not restart before recording the first error and exit state.", "Do not equate a listening socket with a healthy user operation.", "Do not treat a localhost check as proof that the public route works."],
       ["devops/dns-tls-edge", "devops/observability-signals", "devops/incident-response"])

lesson("dns-tls-edge", "DNS, TLS, and reverse-proxy failure boundaries",
       "Separate name resolution, certificate validation, proxy routing, and upstream health.",
       "A public HTTPS request crosses multiple boundaries: DNS identifies an address, TLS authenticates the endpoint and protects transport, a proxy accepts the request, and an upstream application handles it. A failure at one layer can look like an application outage unless each boundary is tested separately. A certificate can be valid but served for the wrong hostname, and a healthy upstream can be unreachable through a wrong proxy route.",
       "For an invoice portal, record the hostname and intended origin, resolve it from a client network, check the presented certificate name and expiry, then inspect proxy logs and upstream response. Test the exact path and Host header that users send. If a proxy read timeout appears, remember that it can refer to inactivity between upstream reads rather than the whole response duration; compare it with application latency before extending it. Automate certificate renewal and alert on the certificate actually served at the edge, not merely the file on disk. During a cutover, lower DNS caching expectations only after checking the relevant TTL and clients that may retain old answers. The commands below are diagnostic; substitute an owned hostname and avoid using insecure TLS flags as a routine workaround.",
       "bash", "dig +short invoices.internal.example\nopenssl s_client -connect invoices.internal.example:443 -servername invoices.internal.example </dev/null\ncurl --proto-default https --fail --show-error --verbose invoices.internal.example/health/ready",
       "External checks add network traffic and monitoring expense, but catch faults invisible to internal health probes. DNS changes may take time to propagate through caches; certificate renewal can fail because of access or validation errors. Keep a planned overlap between old and new endpoints during migration. The sample hostname is illustrative. Do not paste full TLS diagnostic output into public tickets without reviewing it for internal hostnames or session details.",
       ["Do not disable certificate verification to hide a mismatch.", "Do not assume a valid certificate file is the one the proxy serves.", "Do not raise a timeout before locating the slow boundary."],
       ["devops/linux-service-diagnostics", "devops/kubernetes-service-discovery", "devops/alert-design"])

lesson("self-hosted-runner-isolation", "CI runner isolation: treat repository code as untrusted",
       "Prevent one build job from inheriting another job's credentials or workspace.",
       "A CI runner executes repository-controlled code. A persistent self-hosted runner may retain files, processes, tokens, or network access between jobs. The trust boundary includes who can trigger a workflow and which repositories share a runner group. An environment approval gate does not make a compromised host clean.",
       "For a claims platform, run external pull-request tests on isolated hosted workers with read-only permissions. Put deployment jobs on a separate runner group that accepts only protected repository workflows. If self-hosting is necessary, use one-job ephemeral instances and destroy the underlying workspace after each job; deregistration alone does not erase secrets from reused hardware. Restrict access to cloud metadata endpoints and internal networks. Pin third-party actions and keep the deployer's OIDC trust policy scoped to the production environment. The YAML fragment shows a job boundary, not a complete security policy. Audit the actual branch, workflow-file, runner-group, and cloud-role permissions together; a narrow job token cannot compensate for a runner that already holds a long-lived administrator key.",
       "yaml", "jobs:\n  verify:\n    runs-on: ubuntu-latest\n    permissions: {contents: read}\n    steps:\n      - run: make test\n  promote:\n    needs: verify\n    runs-on: [self-hosted, isolated-release]\n    environment: production\n    permissions: {contents: read, id-token: write}\n    steps:\n      - run: ./release/promote-verified-digest.sh",
       "Ephemeral runners require provisioning time, image maintenance, and centralized logs. Those costs buy a cleaner boundary; a persistent runner can be cheaper per job while creating a large compromise path. The fragment omits checkout and identity exchange, so it cannot run as a complete workflow. Review which people can change runner labels and assign jobs. A label is a scheduler selector, not an access-control guarantee by itself.",
       ["Do not give untrusted pull-request jobs access to a deployer runner.", "Do not assume deregistration wipes reused hardware.", "Do not treat a runner label as the only security boundary."],
       ["devops/github-actions-security", "devops/artifact-promotion", "devops/supply-chain-verification"])

lesson("supply-chain-verification", "Software supply chain: SBOM and provenance at admission",
       "Check what was built, where it came from, and whether deployment permits it.",
       "A software bill of materials lists components associated with an artifact. Build provenance records how an artifact was produced, including the builder and source inputs. Neither file makes a release safe merely by existing. A deployment policy must verify the attestation against a trusted identity and compare the artifact digest with the object being admitted.",
       "For a reconciliation worker, generate an SBOM when the image is built, attach provenance to the exact digest, scan the component inventory against current advisories, and verify the builder identity before promotion. Decide what happens when a dependency has no known version or a scan service is unavailable; silent success is not a policy. Allow a time-limited exception only with an owner, affected digest, reason, and expiry. The YAML sketch is an internal release policy, not a standard admission-controller API. A real implementation should verify signatures or trusted attestations cryptographically and reject a digest with no matching statement. Re-scan retained images as advisory data changes; an image that passed last week can become vulnerable without being rebuilt.",
       "yaml", "service: reconciliation-worker\nartifactDigest: sha256:47b22c901a19\nrequiredBuilder: isolated-release-builder\nrequireProvenance: true\nrequireSbom: true\nunknownScanResult: hold\nexceptionExpires: null",
       "SBOM generation, signing, verification, and repeated scanning add build time and storage. An SBOM may omit runtime-installed components or misidentify a package; validate inventory quality before using it as a hard gate. Provenance ties an image to a builder but does not prove its source code is free of defects. The shortened digest is illustrative and must become a full registry digest. Keep trusted builder identifiers and policy changes under review, because weakening either defeats the check.",
       ["Do not treat an SBOM as a vulnerability-free certificate.", "Do not accept provenance without matching its artifact digest.", "Do not turn scanner outages into automatic approvals."],
       ["devops/artifact-promotion", "devops/container-image-builds", "devops/self-hosted-runner-isolation"])

lesson("configuration-management", "Configuration management: converge hosts without surprise restarts",
       "Apply the declared host state repeatedly and inspect what would change.",
       "Configuration management expresses desired packages, files, users, and service state as repeatable tasks. A well-behaved run should converge: after the host reaches the desired state, another run should make no change. This is different from a shell script that appends a line or restarts a daemon every time it runs.",
       "For a report-renderer host, manage its configuration file from a reviewed template and notify a restart handler only when that file changes. Validate the rendered configuration before a restart, and roll out to one host before the rest of the fleet. Ansible check mode can preview many module changes, but some tasks cannot predict their result or may be skipped; it is not a substitute for a disposable-host test. The play below uses a managed template and one handler. It assumes the template exists in the role and that the service name matches the host package. Store credentials in a secret system, not the template repository. Record the inventory version and deployment result so a host drift report points back to the same reviewed change.",
       "yaml", "- name: Configure report renderer\n  hosts: renderers\n  become: true\n  tasks:\n    - name: Install service configuration\n      ansible.builtin.template:\n        src: report-renderer.conf.j2\n        dest: /etc/report-renderer.conf\n        mode: '0640'\n      notify: Restart report renderer\n  handlers:\n    - name: Restart report renderer\n      ansible.builtin.service:\n        name: report-renderer\n        state: restarted",
       "A host-wide run can consume network and package-manager capacity, so use batches and a rollback plan. A handler avoids restarting an unchanged service, yet a changed file can still trigger a disruptive restart; use the application's reload or drain behavior where available. Template output can contain sensitive values even when the source file does not. Limit diff output and retention if secrets may be rendered. Track failed hosts explicitly rather than reporting fleet success from only the first completed batch.",
       ["Do not use an append-only shell command for a convergent setting.", "Do not assume check mode predicts every task.", "Do not restart all hosts at once without capacity headroom."],
       ["devops/linux-service-diagnostics", "devops/terraform-state-and-plan", "devops/incident-response"])

lesson("kubernetes-resource-budgets", "Kubernetes requests and limits: schedule for real load",
       "Set a resource budget that supports normal traffic and rollout overlap.",
       "A container resource request informs scheduling and is the denominator for CPU-utilization scaling. A limit constrains runtime use. CPU over a limit may be throttled; memory over a limit can end in an out-of-memory kill. Requests are not a promise that the application cannot use more, and a large request can prevent a Pod from being scheduled even when measured average use is low.",
       "For a document-index service, derive CPU and memory requests from representative load, then include cold starts, garbage-collection peaks, and the surge Pod needed by a rolling update. Observe throttling, memory working set, OOM events, and p95 request latency together. The fragment sets a 280 millicore CPU request and 640 MiB memory request. The CPU limit is higher to allow bursts, while the memory limit leaves headroom for a measured peak; these numbers are an exercise, not a recommendation for another service. Re-test after changing the runtime or payload size. If no node can fit the request, increasing replicas or enabling autoscaling will not solve placement until capacity changes.",
       "yaml", "resources:\n  requests:\n    cpu: 280m\n    memory: 640Mi\n  limits:\n    cpu: 900m\n    memory: 1180Mi",
       "Higher requests reserve more scheduling capacity and can increase infrastructure cost. Low CPU limits can lengthen response time even when average usage looks safe; low memory limits can create restart loops. Omitting requests can make autoscaling by CPU utilization undefined for affected Pods. Compare costs against SLO impact under real peak traffic. A container can also exhaust ephemeral storage or file descriptors, which these CPU and memory settings do not cover.",
       ["Do not copy requests from a quiet development environment.", "Do not confuse CPU throttling with memory OOM behavior.", "Do not add replicas when the scheduler has no room for them."],
       ["devops/kubernetes-deployments", "devops/horizontal-autoscaling", "devops/capacity-load-testing"])

lesson("horizontal-autoscaling", "Horizontal autoscaling: choose a signal tied to demand",
       "Scale replicas without letting a misleading metric create a feedback loop.",
       "A HorizontalPodAutoscaler adjusts a workload's desired replica count from observed metrics. CPU utilization compares usage with declared CPU requests, so missing or unrealistic requests distort that signal. Scaling adds capacity only after metrics arrive, the controller acts, and new Pods start and become ready.",
       "For a thumbnail service, CPU may correlate with work when each request has similar processing cost. Measure the CPU request, per-Pod throughput, and cold-start duration before choosing a target. Keep a minimum replica count that can handle the interval before new Pods become ready. A queue worker may need queue age or backlog per worker instead of CPU, because an idle process can still face a growing backlog. The YAML sample scales a Deployment between three and eleven replicas at a 68 percent average CPU-utilization target. Verify the metrics adapter, Pod requests, and application readiness before applying it. During a load test, inspect whether latency improves as replicas rise and whether downstream storage becomes the new bottleneck. A rising HPA desired count with pending Pods is a capacity fault, not a successful scale-out.",
       "yaml", "apiVersion: autoscaling/v2\nkind: HorizontalPodAutoscaler\nmetadata: {name: thumbnail-api}\nspec:\n  scaleTargetRef: {apiVersion: apps/v1, kind: Deployment, name: thumbnail-api}\n  minReplicas: 3\n  maxReplicas: 11\n  metrics:\n    - type: Resource\n      resource:\n        name: cpu\n        target: {type: Utilization, averageUtilization: 68}",
       "More replicas consume compute and can multiply connections to a shared database. Scaling has a delay; it cannot rescue traffic spikes shorter than the measurement and startup path. Overreactive rules can oscillate, so test scale-down behavior and stabilization on the target cluster. The sample requires a functioning resource-metrics pipeline. If the service is dominated by a single serialized dependency, additional Pods can make contention worse while the autoscaler reports progress.",
       ["Do not use CPU utilization without CPU requests.", "Do not assume desired replicas are running and ready.", "Do not scale the front end past a fixed downstream bottleneck."],
       ["devops/kubernetes-resource-budgets", "devops/kubernetes-probes", "devops/queue-consumer-reliability"])

lesson("kubernetes-service-discovery", "Kubernetes Service discovery: selectors, endpoints, and DNS",
       "Trace a request from a stable Service name to ready backend Pods.",
       "A Kubernetes Service gives clients a stable virtual address and selects backend Pods by labels. EndpointSlices represent the matching network endpoints used for routing. Cluster DNS maps the service name to its address or, for a headless Service, to backend addresses. A correct DNS answer does not prove that any ready backend exists.",
       "A receipt gateway calls the receipt-api Service in the accounting namespace. Verify the Service selector, Pod labels, EndpointSlices, target port, and readiness state in that order. A single label typo can create a Service with no endpoints while all Pods remain healthy. Cross-namespace clients should use a qualified service name rather than relying on a search path that may change. The manifest below maps port 80 to a named container port, making the port contract visible. It is a Service fragment that still needs a matching Deployment with a port named http. Test a rolling update while watching endpoint membership; the service should route only to ready replicas. If DNS succeeds but requests time out, inspect network policy and application listeners before changing DNS.",
       "yaml", "apiVersion: v1\nkind: Service\nmetadata:\n  name: receipt-api\n  namespace: accounting\nspec:\n  selector: {app: receipt-api}\n  ports:\n    - name: http\n      port: 80\n      targetPort: http",
       "DNS caching and endpoint changes can delay the view seen by clients, but repeatedly bypassing the Service to use Pod IPs makes normal replacement brittle. Large endpoint sets consume control-plane resources; EndpointSlices are the current scaling mechanism. The Service does not authenticate a caller or enforce application authorization. Keep network policy and workload identity separate. When testing from a Pod, use a disposable diagnostic Pod with narrow permissions and remove it after the incident.",
       ["Do not call a resolved Service healthy when it has no ready endpoints.", "Do not rely on Pod IPs as durable client addresses.", "Do not mistake a Service selector for an access-control policy."],
       ["devops/kubernetes-probes", "devops/network-policy-isolation", "devops/dns-tls-edge"])

lesson("network-policy-isolation", "Kubernetes NetworkPolicy: permit only required flows",
       "Constrain east-west traffic with tested ingress and egress rules.",
       "A NetworkPolicy selects Pods and states which layer-four ingress or egress connections are allowed. It works only when the cluster network implementation enforces it. A policy is additive: multiple policies selecting a Pod combine allowed traffic. It does not inspect HTTP paths or replace application authentication.",
       "For a claims API, begin with a namespace isolation plan and list the flows the service actually needs: ingress from the gateway, DNS queries, database access, and telemetry egress. Apply an ingress policy to one canary namespace and test both allowed and denied connections before broad rollout. The sample allows TCP port 8080 from Pods labelled role=gateway in the same namespace. It says nothing about egress and does not provide a global default deny; add separate rules after mapping outbound needs. A namespace selector is needed for cross-namespace sources. Before relying on any deny test, verify that the CNI implements NetworkPolicy. Record the observed denied path, because a broken DNS egress rule can look like application failure.",
       "yaml", "apiVersion: networking.k8s.io/v1\nkind: NetworkPolicy\nmetadata: {name: claims-api-ingress}\nspec:\n  podSelector: {matchLabels: {app: claims-api}}\n  policyTypes: [Ingress]\n  ingress:\n    - from:\n        - podSelector: {matchLabels: {role: gateway}}\n      ports:\n        - {protocol: TCP, port: 8080}",
       "Policies add review and testing cost. A deny-by-default rollout can cut off DNS, health checks, metrics, or control traffic if the flow inventory is incomplete. The shown peer selector matches Pods in the policy's namespace; it does not permit an identically labelled Pod elsewhere. Kubernetes NetworkPolicy handles TCP and UDP, with SCTP support depending on the implementation; other protocols have implementation-specific behavior. Test the exact cluster plugin rather than treating a manifest accepted by the API as enforced security.",
       ["Do not assume policy enforcement from API acceptance alone.", "Do not forget DNS and telemetry egress during isolation.", "Do not treat a same-namespace podSelector as a cross-namespace rule."],
       ["devops/kubernetes-service-discovery", "devops/kubernetes-rbac", "devops/secrets-and-configuration"])

lesson("kubernetes-rbac", "Kubernetes RBAC: bind one service account to one job",
       "Grant API permissions at the smallest useful scope.",
       "Role-based access control authorizes Kubernetes API actions through Roles or ClusterRoles and their bindings. A RoleBinding grants permissions within one namespace. A workload normally runs under a ServiceAccount; granting broad access to the namespace's default account can make that authority available to unrelated Pods.",
       "A release observer needs to read Deployments in the operations namespace to report rollout status. Create a dedicated ServiceAccount, grant get and list on deployments there, and bind that Role only to that identity. The YAML sample contains three documents so the identity, permissions, and binding can be reviewed together. Do not add secrets read access merely to make debugging easier; secret access can expose credentials. Test the effective permission with kubectl auth can-i using service-account impersonation before running the Pod. Also inspect what the container can reach on the network, because RBAC controls Kubernetes API requests, not all network connections. If the job never calls the Kubernetes API, disable its automatic service-account token mount instead of creating a Role.",
       "yaml", "apiVersion: v1\nkind: ServiceAccount\nmetadata: {name: rollout-observer, namespace: operations}\n---\napiVersion: rbac.authorization.k8s.io/v1\nkind: Role\nmetadata: {name: rollout-reader, namespace: operations}\nrules:\n  - apiGroups: [apps]\n    resources: [deployments]\n    verbs: [get, list]\n---\napiVersion: rbac.authorization.k8s.io/v1\nkind: RoleBinding\nmetadata: {name: rollout-observer-binding, namespace: operations}\nsubjects:\n  - {kind: ServiceAccount, name: rollout-observer, namespace: operations}\nroleRef: {kind: Role, name: rollout-reader, apiGroup: rbac.authorization.k8s.io}",
       "Fine-grained roles take maintenance as APIs and workloads change, but reduce blast radius. A cluster-wide binding is easier to write and easier to misuse. Test both intended permissions and a denied operation. A service account's token may be present in a Pod even when code does not need it; remove the mount in such workloads. Review who can edit the Role, RoleBinding, and workload template, because control of those resources can change effective authority.",
       ["Do not attach cluster-admin to a service account for convenience.", "Do not grant the namespace default account permissions meant for one workload.", "Do not confuse API authorization with network isolation."],
       ["devops/network-policy-isolation", "devops/secrets-and-configuration", "devops/github-actions-security"])

lesson("persistent-storage", "Persistent storage: PVC lifecycle and data ownership",
       "Choose a storage class and deletion path before writing durable data.",
       "A PersistentVolumeClaim requests storage with an access mode and size. The bound volume may outlive a Pod, but persistence alone is not a backup. A StorageClass and volume reclaim policy determine how the underlying storage is provisioned and what may happen when claims are removed. StatefulSet identity and storage are useful for some stateful systems, yet they do not replace the database's replication or recovery design.",
       "For an audit-journal component, first decide whether its data belongs on a managed database, object store, or a Pod-mounted volume. If a PVC is required, name the StorageClass, capacity, access mode, encryption expectations, snapshot method, and reclaim behavior. The sample requests 37 GiB with ReadWriteOnce; that mode constrains mounting according to the storage driver and is not a cross-zone replication promise. Rehearse Pod replacement, node loss, and claim deletion in a disposable namespace. Inspect the StorageClass reclaimPolicy before assuming deleted claims preserve data. Store the application's schema revision with backup metadata so restored data can be opened by a compatible image. A successful reschedule to a new node only proves attachment, not data integrity.",
       "yaml", "apiVersion: v1\nkind: PersistentVolumeClaim\nmetadata: {name: audit-journal-data, namespace: audit}\nspec:\n  accessModes: [ReadWriteOnce]\n  storageClassName: encrypted-durable\n  resources:\n    requests:\n      storage: 37Gi",
       "Durable storage costs money even when the application is idle, and snapshots consume additional capacity. ReadWriteOnce does not mean exactly one Pod in all circumstances; interpret the access mode through its Kubernetes and driver semantics. The sample StorageClass name is illustrative and must exist in the target cluster. Volume deletion can be irreversible when the class uses Delete reclaim policy. Keep restore tests independent of the volume's apparent persistence and monitor capacity before the filesystem fills.",
       ["Do not call a PVC a backup.", "Do not assume claim deletion retains the underlying disk.", "Do not select a storage class without testing zone and attachment behavior."],
       ["devops/backup-and-recovery", "devops/kubernetes-resource-budgets", "devops/database-change-safety"])

lesson("alert-design", "Alert design: page on impact and include a first action",
       "Turn an indicator into a low-noise, actionable page.",
       "An alert rule evaluates an operational signal and sends a notification when a condition persists. A page should indicate user impact or a near-term risk that requires prompt human action. A dashboard is for investigation; sending every dashboard threshold to an on-call phone creates noise and delays response to serious incidents.",
       "For a document-download service, alert when a meaningful volume of requests has a sustained server-error ratio above its baseline. Route the page to the team that can pause rollout or repair the service, and include a runbook with the first checks: current release digest, affected route, dependency health, and rollback compatibility. The Prometheus rule below uses a ratio and a 6-minute pending interval; it is only a starting point. Add a minimum traffic condition and an explicit no-data alert in the real rule set, and evaluate the effect against historical data before enabling paging. Test that the notification reaches the intended person and that a resolved condition clears it. A missing metrics pipeline should trigger its own monitoring path, because an absent error series is not a healthy series.",
       "yaml", "groups:\n  - name: document-download\n    rules:\n      - alert: DownloadServerErrors\n        expr: sum(rate(download_requests_total{result=\"server_error\"}[6m])) / sum(rate(download_requests_total[6m])) > 0.018\n        for: 6m\n        labels: {severity: page, owner: documents}\n        annotations: {summary: 'Document download errors exceed the review threshold'}",
       "A longer pending interval reduces transient pages but delays notification. A ratio without a traffic floor can be noisy at low request volume or undefined at zero; this sketch is deliberately incomplete until those cases are handled. Too many label combinations can multiply alert instances and on-call load. Keep diagnostic labels stable and bounded. Use the service's SLO and real recovery time to choose thresholds rather than copying 1.8 percent into another service.",
       ["Do not page on a condition with no operator action.", "Do not interpret absent telemetry as zero failures.", "Do not ship a ratio alert without checking low-traffic behavior."],
       ["devops/service-level-objectives", "devops/observability-signals", "devops/incident-response"])

lesson("queue-consumer-reliability", "Queue consumers: acknowledgement, idempotency, and backlog",
       "Process redelivered work without duplicating its business effect.",
       "A queue decouples producers from consumers, but many delivery systems can redeliver a message after a crash, lost acknowledgement, or expired visibility interval. The consumer therefore needs an idempotent business operation, not an assumption that every message arrives once. Acknowledgement should follow durable processing; acknowledging first can lose work if the process stops before the side effect commits.",
       "A refund-notification worker receives a refund event with a stable event identifier. In one transaction, insert an idempotency record and the intended outbox notification; if the event identifier already exists, return success without creating another notification. Commit before acknowledging the queue message. The SQL sketch shows the deduplication gate, not the entire worker protocol. Set the consumer's in-flight limit according to memory and downstream capacity. Monitor oldest-message age, retries, dead-letter volume, and completed business actions; CPU alone may stay low while backlog grows. If processing fails permanently, move the message to an inspected dead-letter path with a replay procedure. A replay must preserve the same event identifier so the deduplication contract still applies.",
       "sql", "BEGIN;\nINSERT INTO processed_refund_events (event_id, processed_at)\nVALUES (:event_id, CURRENT_TIMESTAMP)\nON CONFLICT (event_id) DO NOTHING;\n-- Only when the insert affected one row: write the notification outbox row.\nCOMMIT;\n-- Acknowledge the queue message after the transaction commits.",
       "The idempotency table and outbox consume storage; retain records for at least the period in which messages may be replayed, and align cleanup with the queue's retention policy. A small prefetch protects downstream systems but can lower throughput, while a large prefetch increases unacknowledged work after a crash. The SQL assumes a database with ON CONFLICT support and a unique event_id constraint. Duplicate deliveries are normal operational input, not proof that the broker is broken.",
       ["Do not acknowledge before durable processing.", "Do not deduplicate on a mutable payload description.", "Do not alert only on queue depth without looking at oldest-message age."],
       ["devops/horizontal-autoscaling", "devops/database-change-safety", "devops/alert-design"])

lesson("capacity-load-testing", "Capacity and load tests: identify the next bottleneck",
       "Measure service behavior at representative concurrency before changing replica counts.",
       "A load test applies a controlled workload and observes throughput, latency, errors, and resource saturation. Its value is in locating the limiting boundary, not in producing the largest requests-per-second number. A test that ignores request mix, data size, cache state, or downstream quotas can overstate production capacity.",
       "For a parcel-tracking API, replay a mix of lookup and update operations against synthetic records that resemble production sizes. Increase concurrency in steps, hold each step long enough to observe steady behavior, and record p95 latency, error ratio, CPU throttling, database connections, and queue age. Stop when an agreed safety threshold is reached; never run a destructive peak test against production without a controlled window and ownership. Use the small plan below to make assumptions visible. If a new replica improves throughput but doubles database connections, size the shared database before enabling autoscaling. Compare cold-cache and warm-cache runs, and include a rollout period when old and new Pods overlap. The observed bottleneck determines the next change: increasing replicas will not fix a serialized database lock.",
       "yaml", "service: parcel-tracking\ntrafficMix:\n  lookupPercent: 73\n  updatePercent: 27\nsteps:\n  - {clients: 35, holdMinutes: 9}\n  - {clients: 85, holdMinutes: 9}\n  - {clients: 155, holdMinutes: 9}\nstopAt:\n  p95LatencyMs: 620\n  serverErrorPercent: 1.2",
       "A realistic test needs isolated infrastructure and representative data, which cost time and compute. Short tests can miss garbage collection, cache eviction, connection leaks, and autoscaler delay. The numeric limits above are exercise values, not general service targets. Record test image digest, environment size, and data profile so two runs can be compared. Watch client-side saturation too; a load generator that cannot sustain its planned rate may make the service appear healthier than it is.",
       ["Do not compare runs with different data profiles as if they were identical.", "Do not increase replicas before checking the downstream limit.", "Do not let the load generator become the hidden bottleneck."],
       ["devops/kubernetes-resource-budgets", "devops/horizontal-autoscaling", "devops/service-level-objectives"])


titles = {row["path"]: row["title"] for row in rows}
titles.update({item["path"]: item["title"] for item in specs})
project_path = "devops/diagnose-service-project"
quiz_path = "quizzes/devops-platform-reliability"
titles[project_path] = "Project: diagnose a broken service path"
titles[quiz_path] = "DevOps platform reliability decisions"
for item in specs:
    assert all(target in titles for target in item["related"]), item["path"]


def links(paths):
    return "<ul>" + "".join(f'<li><a href="/{html.escape(path)}">{html.escape(titles[path])}</a></li>' for path in paths) + "</ul>"


groups = [
    ("Hosts and edge", "Locate the failing process, name, certificate, or proxy boundary.", ["linux-service-diagnostics", "dns-tls-edge", "configuration-management"]),
    ("Build trust", "Isolate runners and verify what a release contains and where it was built.", ["self-hosted-runner-isolation", "supply-chain-verification"]),
    ("Cluster capacity and routing", "Size Pods, scale from demand, and trace the route to a ready backend.", ["kubernetes-resource-budgets", "horizontal-autoscaling", "kubernetes-service-discovery", "persistent-storage"]),
    ("Cluster access and operations", "Limit traffic and API authority; page on impact and process queued work safely.", ["network-policy-isolation", "kubernetes-rbac", "alert-design", "queue-consumer-reliability", "capacity-load-testing"]),
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
               category="DevOps", difficulty="Intermediate", tags=["devops", "operations"],
               sort_order=17400 + order, published_at=stamp, created_at=stamp, updated_at=stamp)
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
               summary="Trace a failing HTTPS request through DNS, proxy, Service, policy, Pod, and alerting.",
               sort_order=17490, published_at=stamp, created_at=stamp, updated_at=stamp)
project["data"] = {"kind": "project", "reading_minutes": 8,
                   "author_path": "authors/aitrove-editorial", "subject_root": course,
                   "section_path": project_hub, "content_format": "html", "seo_ready": True,
                   "related": [{"path": target, "title": titles[target]} for target in ["devops/dns-tls-edge", "devops/kubernetes-service-discovery", "devops/network-policy-isolation", "devops/alert-design"]]}
project["body"] = (
    "<p>This project traces a document-download failure from a client request to a Kubernetes Pod. Work in a disposable namespace with synthetic data. The goal is a repeatable diagnosis and a safe repair, supported by captured evidence from each network and application boundary.</p>"
    "<h2>Construct the path</h2><p>Deploy three replicas of a small API behind a Service and an HTTPS edge route. Set readiness so an unready Pod is removed from normal traffic. Give the workload a resource request, a dedicated service account, and a NetworkPolicy that permits only the intended gateway flow. Record the image digest and baseline request success. Add an external request check and an alert whose owner can take a first action. If the test environment lacks NetworkPolicy enforcement, record that limitation rather than claiming isolation.</p>"
    "<pre><code class=\"language-text\">Failure exercise: document-download\n1. Break a Service selector; capture ready Pod and empty endpoint evidence.\n2. Restore the selector; block the gateway with a policy change.\n3. Restore traffic; serve an expired test certificate at the edge.\n4. For each fault, record client error, first alert, root boundary, and repair time.</code></pre>"
    "<h2>Evaluate the repair</h2><p>For each injected fault, start at the client symptom. Check DNS and TLS, proxy response, Service endpoints, network policy, Pod readiness, and application logs in order. Change one variable at a time. After repair, verify a user-facing operation from outside the cluster and confirm the alert resolves. Compare the fault's detection delay with the service objective. Write a short incident record naming the first useful signal and any missing signal. Clean up the namespace after preserving the diagnostic output.</p>"
    "<h2>Cost and verification</h2><p>The exercise consumes temporary compute, a test hostname or certificate, and monitoring capacity. An edge TLS error may never reach a Pod, so a Pod-only alert will miss it. A policy manifest accepted by the API may not be enforced by the cluster plugin. A corrected Service selector can restore endpoints without fixing an unrelated readiness failure. Keep the evidence for each layer distinct to avoid a lucky repair being misreported as a complete diagnosis.</p>"
    "<h3>Common Mistakes</h3><ul><li>Do not assume a resolved hostname means the application was reached.</li><li>Do not treat an empty endpoint set as a DNS fault.</li><li>Do not claim policy isolation until a denied connection has been tested.</li></ul>"
    "<h2>Reference lessons</h2>" + links(["devops/linux-service-diagnostics", "devops/dns-tls-edge", "devops/kubernetes-service-discovery", "devops/network-policy-isolation", "devops/kubernetes-probes", "devops/alert-design", project_hub]))
rows.append(project)
project_index = by_path[project_hub]
project_index["data"]["modules"][0]["lessons"].append(project_path)
project_index["body"] += "<h2>Service-path diagnosis</h2>" + links([project_path])
project_index["updated_at"] = stamp


questions = [
    ("What does a listening socket prove?", ["A process is listening on an address and port", "The public HTTPS route works", "Every request is valid"], 0, "A socket is only one layer of the request path."),
    ("Which check identifies the certificate users actually receive?", ["A TLS connection to the public edge name", "A local file listing", "A database health check"], 0, "The edge can serve a different certificate from the expected file."),
    ("Why isolate a deployment runner from pull-request jobs?", ["Untrusted code could reach retained credentials or networks", "Tests cannot run on Linux", "Image tags cannot be read"], 0, "Runner execution is a trust boundary."),
    ("What must provenance verification match?", ["The deployed artifact digest and trusted builder", "Only a human-readable tag", "The current time alone"], 0, "Statements must bind to the object admitted."),
    ("What should an unchanged configuration run do?", ["Make no unnecessary change", "Restart every service", "Append a second copy of each setting"], 0, "Convergent tasks settle on the declared state."),
    ("What does a CPU request affect?", ["Scheduling and utilization-based scaling", "TLS certificate renewal", "Queue message ordering"], 0, "CPU utilization is measured relative to the request."),
    ("What if HPA wants eleven replicas but new Pods remain Pending?", ["Investigate schedulable capacity", "Assume scale-out succeeded", "Raise the alert threshold"], 0, "Desired replicas are not running replicas."),
    ("What can a Service have even with no ready backends?", ["A DNS answer", "A successful business response", "An automatic backup"], 0, "Name resolution does not create endpoints."),
    ("When does a NetworkPolicy manifest enforce traffic?", ["When the cluster network implementation supports it", "Whenever the API accepts YAML", "Only when a ServiceAccount exists"], 0, "Enforcement depends on the plugin."),
    ("Why use a dedicated ServiceAccount?", ["Limit API authority to one workload", "Make every Pod a cluster admin", "Replace application authentication"], 0, "Shared default accounts broaden access."),
    ("What does a PVC provide by itself?", ["A storage claim", "A tested backup", "Cross-region data recovery"], 0, "Durability and restoration need separate design."),
    ("When should a queue consumer acknowledge work?", ["After durable processing commits", "Before any side effect", "Only when CPU falls"], 0, "Early acknowledgement can lose work."),
]
quiz = copy.deepcopy(by_path["quizzes/devops-operations"])
quiz.update(id=str(uuid.uuid5(uuid.NAMESPACE_URL, "aitrove:" + quiz_path)), path=quiz_path,
            title=titles[quiz_path], summary="Twelve checks on hosts, release trust, cluster access, and asynchronous work.",
            sort_order=17500, published_at=stamp, created_at=stamp, updated_at=stamp)
quiz["data"] = {"subject_root": course, "section_path": quiz_hub, "content_format": "html",
                "author_path": "authors/aitrove-editorial", "seo_ready": True, "duration_minutes": 12,
                "related": [{"path": target, "title": titles[target]} for target in ["devops/linux-service-diagnostics", "devops/supply-chain-verification", "devops/kubernetes-resource-budgets", "devops/network-policy-isolation", "devops/queue-consumer-reliability"]],
                "questions": [dict(prompt=prompt, options=options[index % 3:] + options[:index % 3],
                                   answer=(answer - index % 3) % 3, explanation=explanation)
                              for index, (prompt, options, answer, explanation) in enumerate(questions)]}
quiz["body"] = "<p>Choose the operational decision supported by the evidence in each situation. Review the linked lesson when an answer fails.</p><h2>Review these lessons</h2>" + links([item["path"] for item in quiz["data"]["related"]]) + "<h2>Other checks</h2>" + links([quiz_hub, "quizzes/devops-delivery", "quizzes/devops-operations"]) + "<h3>Common Mistakes</h3><ul><li>Do not treat a passing configuration check as proof of user success.</li><li>Do not infer isolation from a policy that was never tested.</li></ul>"
rows.append(quiz)
quiz_index = by_path[quiz_hub]
quiz_index["data"]["modules"][0]["lessons"].append(quiz_path)
quiz_index["body"] += "<h2>Platform reliability check</h2>" + links([quiz_path])
quiz_index["updated_at"] = stamp


for source, targets in {
    "devops/incident-response": ["devops/linux-service-diagnostics", "devops/alert-design"],
    "devops/github-actions-security": ["devops/self-hosted-runner-isolation"],
    "devops/artifact-promotion": ["devops/supply-chain-verification"],
    "devops/terraform-state-and-plan": ["devops/configuration-management"],
    "devops/kubernetes-deployments": ["devops/kubernetes-resource-budgets", "devops/horizontal-autoscaling"],
    "devops/kubernetes-probes": ["devops/kubernetes-service-discovery"],
    "devops/secrets-and-configuration": ["devops/network-policy-isolation", "devops/kubernetes-rbac"],
    "devops/backup-and-recovery": ["devops/persistent-storage"],
    "devops/service-level-objectives": ["devops/alert-design"],
    "devops/observability-signals": ["devops/capacity-load-testing"],
}.items():
    row = by_path[source]
    row["body"] += "<h2>Operational follow-up</h2>" + links(targets)
    row["data"].setdefault("related", []).extend({"path": target, "title": titles[target]} for target in targets)
    row["updated_at"] = stamp

assert len({row["path"] for row in rows}) == len(rows)
fixture.write_text(json.dumps(rows, ensure_ascii=False, indent=2) + "\n")
print(json.dumps({"new_lessons": len(specs), "new_projects": 1,
                  "new_quiz_banks": 1, "total_records": len(rows)}))
