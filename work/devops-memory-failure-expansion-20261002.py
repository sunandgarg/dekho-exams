"""Add original memory-failure lessons, a drill, and a decision check."""

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


def article(slug, title, summary, definition, decision, language, sample, cost, mistakes, related):
    return dict(path="devops/" + slug, title=title, summary=summary,
                definition=definition, decision=decision, language=language,
                sample=sample, cost=cost, mistakes=mistakes, related=related)


specs = [
    article(
        "container-oom-attribution",
        "Container OOM attribution: separate a limit kill from node eviction",
        "Tie a restart to its container, cgroup, and node before raising a memory limit.",
        "A container OOM kill occurs when memory charged to its cgroup cannot be reclaimed within its limit. A node-pressure eviction is a kubelet decision made from node availability and Pod priority. They can appear in the same incident, but they have different remedies. A restarted container can also have exited for an application error or a probe failure. The reason field alone is a starting point; capture the preceding trend and the node condition before the old container state disappears.",
        "A document-conversion Pod restarts every time a 73 MiB scan is decoded. Record its container ID, previous termination reason, restart count, Pod events, node MemoryPressure condition, and memory usage by container. If the container was OOMKilled while the node stayed healthy, inspect its limit and charge breakdown; if the Pod was Evicted after node pressure, inspect aggregate requests and node reservations. Repeat one controlled load in a disposable cluster and preserve the memory peak, input size, and result. Do not erase the fault by increasing the limit until you know whether the process retained data or simply needs a documented working set.",
        "bash",
        "kubectl -n claims describe pod converter-0\nkubectl -n claims get pod converter-0 -o jsonpath='{range .status.containerStatuses[*]}{.name}{\" previous=\"}{.lastState.terminated.reason}{\" restarts=\"}{.restartCount}{\"\\n\"}{end}'\nkubectl describe node worker-07",
        "The three API reads are O(1) in object count, but event retention and monitoring resolution limit historical certainty. Each retry consumes startup CPU and may replay work; correlate OOM frequency with duplicated jobs and user latency. A larger limit increases worst-case node demand and can move the failure to another Pod. Preserve a pre-change baseline and verify the same input after the fix.",
        ["Do not equate an exit code with a complete root cause.", "Do not call an eviction a container-limit OOM.", "Do not raise a limit without checking node headroom and input replay."],
        ["devops/node-pressure-eviction", "devops/kubernetes-resource-budgets", "devops/queue-visibility-lease"],
    ),
    article(
        "jvm-container-memory-headroom",
        "JVM container memory: leave room beyond the Java heap",
        "Budget heap, stacks, direct buffers, JVM internals, and native libraries inside one container limit.",
        "The Java heap is only one consumer of a JVM process's resident memory. Thread stacks, class metadata, code cache, direct buffers, garbage collector structures, and native libraries also consume memory charged to the container. A heap maximum equal to the cgroup limit leaves no allowance for these allocations. The exact mix changes with thread count, application libraries, and traffic, so a fixed percentage must be tested under the workload rather than copied between services.",
        "A payment-ledger worker has a 1536 MiB container limit and peaks at 910 MiB committed heap under an import. Start with a measured nonheap allowance, then choose a heap ceiling that still admits peak direct buffers and thread stacks. In a disposable environment, enable JVM native memory tracking at summary level, record a baseline, and compare it during a representative import. Native tracking cannot explain every allocation made outside the JVM, so compare its figures with process RSS and the container charge. If the application throws Java OutOfMemoryError, preserve its message and heap evidence; if the kernel kills the process, inspect the cgroup limit and all native consumers. Store heap dumps in a bounded, access-controlled location because they may contain customer data.",
        "bash",
        "jcmd 1 VM.native_memory baseline\njcmd 1 VM.native_memory summary.diff\ncat /sys/fs/cgroup/memory.current\ncat /sys/fs/cgroup/memory.max",
        "Native memory tracking adds CPU and memory overhead; measure the diagnostic run before enabling it broadly. A larger heap may reduce garbage collection pressure but leaves less native headroom and can increase restart cost. Track peak RSS, heap occupancy after collection, direct-buffer use, thread count, and OOM events through the same import window. On systems without cgroup v2, use the equivalent runtime and OS counters rather than assuming these paths exist.",
        ["Do not set the heap maximum equal to the container limit.", "Do not assume a kernel OOM produces a Java heap dump.", "Do not treat native tracking as a complete accounting of external library allocations."],
        ["devops/container-oom-attribution", "devops/kubernetes-resource-budgets", "devops/telemetry-sensitive-data-boundary"],
    ),
    article(
        "tmpfs-emptydir-memory-charge",
        "Memory-backed emptyDir: budget file bytes as container memory",
        "A fast scratch volume can exhaust a Pod's memory even while the application heap is stable.",
        "An emptyDir volume with medium Memory uses tmpfs. Its file pages count toward memory use, not the Pod's local ephemeral-storage budget. Data remains for the Pod lifetime, even if a writing container restarts; a restarted process cannot rely on garbage collection to remove old scratch files. Setting a size limit controls volume growth, but it does not replace a realistic container memory limit or a cleanup rule.",
        "A claims renderer writes intermediate PDFs into a shared tmpfs volume. The renderer's heap stays near 240 MiB while 420 MiB of old files accumulate after failed attempts. Give the scratch volume a 320 MiB sizeLimit, reserve memory for the process and sidecar, and delete each task's files after its result is committed. Inject a failed render, restart the renderer, and verify the volume still contains the abandoned file until cleanup runs. Measure which container receives the memory charge on the chosen runtime instead of assuming the sidecar owns it. If the files must survive Pod deletion, use durable storage rather than tmpfs.",
        "yaml",
        "apiVersion: v1\nkind: Pod\nmetadata:\n  name: claims-renderer\nspec:\n  containers:\n    - name: renderer\n      image: registry.internal/claims-renderer@sha256:1111111111111111111111111111111111111111111111111111111111111111\n      resources:\n        requests:\n          memory: 768Mi\n        limits:\n          memory: 1152Mi\n      volumeMounts:\n        - name: scratch\n          mountPath: /work\n  volumes:\n    - name: scratch\n      emptyDir:\n        medium: Memory\n        sizeLimit: 320Mi",
        "A full scan of F scratch files is O(F); recording per-task paths makes targeted cleanup proportional to the files for that task. tmpfs avoids disk I/O but buys that speed with scarce memory and possible OOM kills. Track scratch bytes, failed cleanup attempts, container charge, and node pressure at the same time. A size limit can make writes fail earlier; the application must handle that error without leaving a half-published result.",
        ["Do not charge tmpfs scratch to ephemeral-storage quota alone.", "Do not assume a container restart clears an emptyDir volume.", "Do not put irreplaceable output in a Pod-lifetime scratch volume."],
        ["devops/ephemeral-storage-limit-accounting", "devops/container-oom-attribution", "devops/persistent-storage"],
    ),
    article(
        "cgroup-memory-reclaim-signals",
        "Cgroup memory signals: read reclaim before the OOM counter",
        "Memory pressure can stall a service well before a process is killed.",
        "On a Linux cgroup v2 host, memory.current shows charged memory, memory.stat separates broad charge classes, and memory.events reports boundary events such as high, max, and OOM. Pressure stall information records time tasks could not progress because of resource pressure. A rising RSS graph without a matching latency or reclaim signal is different from a service repeatedly stalling on reclaim. These counters are scoped to a cgroup; they must be read from the workload's actual path, not an unrelated host shell.",
        "A settlement worker slows during the hourly ledger sweep, yet no OOM kill occurs. In an isolated test, collect memory.current, memory.stat, memory.events, and memory.pressure before, during, and after the sweep. Calculate deltas rather than treating cumulative counters as instantaneous rates. Correlate reclaim and full-stall changes with queue age and request latency. If the pressure is caused by file cache, compare active and inactive file charge with working-set demand; if anonymous memory grows and stays high after the sweep, investigate retained objects or allocator behavior. Preserve node-level pressure separately: one container may look quiet while its node struggles.",
        "bash",
        "cat /sys/fs/cgroup/memory.current\ncat /sys/fs/cgroup/memory.stat\ncat /sys/fs/cgroup/memory.events\ncat /sys/fs/cgroup/memory.pressure",
        "Reading four small control files is O(1), but storing per-container samples at high frequency scales with active cgroup count and retention duration. Sample at a rate that preserves short sweeps without multiplying monitoring cost. Use workload-level latency and queue age as outcome signals; a counter increase without user impact may call for capacity planning rather than paging. Check cgroup version and metric exporter semantics before comparing clusters.",
        ["Do not read host counters and label them as container counters.", "Do not interpret a cumulative event count without a time window.", "Do not treat OOM absence as proof that memory pressure is harmless."],
        ["devops/container-oom-attribution", "devops/observability-signals", "devops/metric-cardinality-budget"],
    ),
    article(
        "memory-growth-leak-or-cache",
        "Memory growth: distinguish retained data from useful cache",
        "A growing resident set is evidence to investigate, not a diagnosis of a leak.",
        "Resident memory can rise because of live application objects, allocator arenas, direct buffers, mapped files, or page cache charged to a cgroup. A leak is memory that remains reachable or otherwise unreclaimable after the work that required it has ended. A cache may grow deliberately and then stabilize or shrink under pressure. One flat traffic window cannot establish either behavior; use repeated, comparable work cycles and measure what remains after each cycle.",
        "A fraud-scoring service rises from 310 to 690 MiB after eight batch windows. Replay a fixed 47,000-record batch three times in a disposable environment. Record memory.current, process RSS, anonymous versus file charge, application cache entry count, and post-cycle latency. If the heap's live set rises after every collection, capture a controlled heap profile; if RSS rises while live heap and cgroup charge stabilize, inspect allocator retention and mappings before rewriting business logic. Disable or bound one cache at a time, then compare throughput and tail latency. A restart that resets memory only proves the memory belonged to the process, not that it was leaked.",
        "text",
        "Fraud scorer comparison\nBatch input: 47,000 records, repeated three times\nWindow: before, peak, after each cycle\nSignals: cgroup charge, RSS, anonymous/file split, live heap, cache entries\nDecision: leak, bounded cache, allocator retention, or unresolved\nAcceptance: stable post-cycle baseline with no latency regression",
        "A full heap capture is O(H) in live heap bytes and can pause or slow the service; profile a disposable replica first. A bounded cache trades hit rate for predictable memory use, so compare cache misses and downstream load after tightening it. Keep the batch input and runtime version fixed when comparing experiments. Alert on sustained growth paired with exhausted headroom or user impact, not on every healthy warm-up.",
        ["Do not call every RSS increase a memory leak.", "Do not infer that a restart identifies the allocation source.", "Do not shrink a cache without measuring its downstream cost."],
        ["devops/cgroup-memory-reclaim-signals", "devops/jvm-container-memory-headroom", "devops/capacity-load-testing"],
    ),
    article(
        "memory-safe-rollout-headroom",
        "Memory-safe rollouts: reserve space for old and new Pods",
        "A replacement Pod needs schedulable memory before the old version releases its request.",
        "A rolling update can temporarily run old and new replicas together. The scheduler admits the new Pods from requests, while the node must survive their actual peaks plus system reservations. If a large service is already close to node memory capacity, maxSurge can leave new Pods Pending or push the node into pressure. Setting maxUnavailable higher may free capacity, but it can cut serving capacity before the new version proves ready.",
        "A reporting API runs six replicas, each requesting 896 MiB, on nodes whose remaining allocatable memory is only 1.3 GiB. A rollout with two surge Pods needs 1792 MiB of additional requests before either old Pod exits, so it cannot fit on that pool even if current usage is low. Add node capacity or use a smaller surge after verifying the service can meet its availability target; do not solve the scheduling block by falsifying requests. Test cold-start memory and readiness under load, then drain an old Pod and inspect node pressure, restart counts, and p99 latency. Include sidecars and DaemonSet overhead in the headroom ledger.",
        "text",
        "Reporting API rollout\nReplicas: 6\nRequest per new Pod: 896 MiB\nmaxSurge: 2\nAdditional requested memory: 1792 MiB\nAvailable node allocatable headroom: 1331 MiB\nDecision: add capacity or revise rollout after availability test",
        "The scheduling comparison is O(P) over pending Pods for a simple capacity ledger, but real placement also depends on affinity, topology, quotas, and per-node fit. One aggregate free-memory number is insufficient if no single node can host a Pod. Extra surge capacity costs node time, while low surge increases rollout duration. Measure schedule-to-ready time, unavailable endpoints, MemoryPressure events, and user latency for the chosen strategy.",
        ["Do not use average free memory as proof a Pod fits on a node.", "Do not lower memory requests merely to force scheduling.", "Do not increase maxUnavailable without checking serving capacity."],
        ["devops/kubernetes-deployments", "devops/topology-spread-placement", "devops/node-autoscaling-headroom"],
    ),
]

project_path = "devops/memory-failure-boundary-project"
quiz_path = "quizzes/devops-memory-failure-decisions"
titles = {row["path"]: row["title"] for row in rows}
titles.update({item["path"]: item["title"] for item in specs})
titles[project_path] = "Project: diagnose a memory failure without moving it to another Pod"
titles[quiz_path] = "DevOps memory failure decisions"
assert all(item["path"] not in by_path for item in specs)
assert project_path not in by_path and quiz_path not in by_path
assert all(path in titles for item in specs for path in item["related"])


def links(paths):
    return "<ul>" + "".join(
        f'<li><a href="/{html.escape(path)}">{html.escape(titles[path])}</a></li>'
        for path in dict.fromkeys(paths)
    ) + "</ul>"


for heading, summary, paths in [
    ("Memory failure attribution", "Separate limit kills, reclaim stalls, and retained memory before changing a budget.", [item["path"] for item in specs[:2]] + [specs[3]["path"], specs[4]["path"]]),
    ("Memory placement and scratch space", "Account for tmpfs files and replacement Pods as real memory consumers.", [specs[2]["path"], specs[5]["path"]]),
]:
    by_path[course]["data"]["modules"].append({"title": heading, "summary": summary, "lessons": paths})
    by_path[course]["body"] += f"<h2>{html.escape(heading)}</h2><p>{html.escape(summary)}</p>" + links(paths)
by_path[course]["updated_at"] = stamp

for index, item in enumerate(specs):
    path = item["path"]
    row = copy.deepcopy(by_path["devops/continuous-integration"])
    row.update(id=str(uuid.uuid5(uuid.NAMESPACE_URL, "aitrove:" + path)), path=path,
               title=item["title"], summary=item["summary"], subject="devops",
               category="DevOps", difficulty="Advanced", tags=["devops", "memory-operations"],
               sort_order=24000 + index, published_at=stamp, created_at=stamp, updated_at=stamp)
    row["data"] = {"kind": "tutorial", "reading_minutes": 6,
                   "author_path": "authors/aitrove-editorial", "subject_root": course,
                   "section_path": course, "content_format": "html", "seo_ready": True,
                   "related": [{"path": target, "title": titles[target]} for target in item["related"]]}
    row["body"] = (
        f"<p>{html.escape(item['definition'])}</p><h2>Operational decision</h2>"
        f"<p>{html.escape(item['decision'])}</p>"
        f'<pre><code class="language-{item["language"]}">{html.escape(item["sample"])}</code></pre>'
        f"<h2>Cost and verification</h2><p>{html.escape(item['cost'])}</p>"
        + "<h3>Common Mistakes</h3><ul>"
        + "".join(f"<li>{html.escape(mistake)}</li>" for mistake in item["mistakes"])
        + "</ul><h2>Connected lessons</h2>" + links([course, *item["related"]])
    )
    rows.append(row)

related_paths = [item["path"] for item in specs]
project = copy.deepcopy(by_path["devops/practice-project"])
project.update(id=str(uuid.uuid5(uuid.NAMESPACE_URL, "aitrove:" + project_path)),
               path=project_path, title=titles[project_path],
               summary="Inject a memory limit kill, a tmpfs growth fault, and rollout pressure; classify each with evidence.",
               difficulty="Advanced", sort_order=24090,
               published_at=stamp, created_at=stamp, updated_at=stamp)
project["data"] = {"kind": "project", "reading_minutes": 10,
                   "author_path": "authors/aitrove-editorial", "subject_root": course,
                   "section_path": project_hub, "content_format": "html", "seo_ready": True,
                   "related": [{"path": target, "title": titles[target]} for target in related_paths]}
project["body"] = (
    "<p>Use a disposable Kubernetes cluster and a document-conversion workload with a memory-backed scratch volume. The goal is to identify three different failure boundaries without hiding one by moving it to another Pod. Save the workload manifest, input sizes, node allocatable capacity, and monitoring snapshots before changing any limit.</p>"
    "<h2>Inject and classify</h2><p>First, use a bounded input that crosses the container memory limit; capture prior termination state, cgroup counters, restart count, and node condition. Next, leave task files in tmpfs across a container restart and show that file charge remains while the heap recovers. Finally, schedule a two-Pod surge against a node pool that cannot fit both requests. Explain which fault is a cgroup kill, which is scratch growth, and which is an admission or placement failure. Keep a separate node-pressure run if the test cluster can safely support it.</p>"
    "<pre><code class=\"language-text\">Memory drill acceptance\nInput: fixed 73 MiB scan plus a smaller control input\nKill: previous container state and charge peak recorded\nScratch: abandoned file persists across container restart\nPlacement: requested surge exceeds per-node fit\nRecovery: cleanup and capacity change tied to each cause\nUser path: one accepted conversion after every repair</code></pre>"
    "<h2>Repair and recheck</h2><p>Set a scratch size limit and task cleanup, then replay the failed input and verify that a full volume produces a handled error. Budget JVM heap and native headroom from observed peaks if the renderer uses Java. For the rollout, add capacity or reduce surge only after testing the service availability target. Run the same inputs three times and report post-cycle memory, pressure stall change, OOM counts, queue age, and p99 latency. A repair passes only when it removes the targeted failure and keeps the user path working without raising another Pod's failure rate.</p>"
    "<h3>Common Mistakes</h3><ul><li>Do not claim a restart fixed a retained-memory problem.</li><li>Do not use one node-wide memory graph to attribute a container kill.</li><li>Do not reduce requests to make a rollout appear schedulable.</li></ul>"
    "<h2>Connected lessons</h2>" + links([*related_paths, project_hub])
)
rows.append(project)
by_path[project_hub]["data"]["modules"][0]["lessons"].append(project_path)
by_path[project_hub]["body"] += "<h2>Memory failure drill</h2>" + links([project_path])
by_path[project_hub]["updated_at"] = stamp

questions = [
    ("A container restarts while its node remains healthy. What evidence comes first?", ["Previous termination state and container charge around the restart", "Only the current Pod phase", "A larger limit"], "The old termination and charge trend separate a limit kill from other exits."),
    ("A Pod is Evicted during node MemoryPressure. What must be examined?", ["Node availability, requests, reservations, and Pod usage", "Only the killed container's heap", "The image tag alone"], "Node eviction is a node availability decision, not proof of a single container limit breach."),
    ("Why can a JVM be killed with heap below its configured maximum?", ["Native memory, stacks, buffers, and other charges share the cgroup limit", "The heap maximum is the whole process RSS", "The scheduler stops it at its request"], "The Java heap is only part of the process memory budget."),
    ("What does JVM native memory tracking omit?", ["Some allocations by code outside the JVM", "All JVM internal allocations", "The ability to compare baselines"], "External native code can allocate memory that JVM tracking does not attribute."),
    ("Which budget includes a memory-backed emptyDir?", ["Memory charge, with a separate volume size limit", "Only ephemeral-storage", "Only the image-layer budget"], "tmpfs pages consume memory charged to the Pod's containers."),
    ("What happens to emptyDir files after one container restarts?", ["They can remain for the Pod lifetime", "They are always cleared", "They become durable across Pod deletion"], "A container restart does not recreate the Pod volume."),
    ("How should cumulative memory.events values be analyzed?", ["Compare deltas over a known interval", "Treat the total as events per second", "Ignore them unless OOM is nonzero"], "Cumulative counts need a time window to describe current behavior."),
    ("Why collect pressure signals when OOM count is zero?", ["Reclaim stalls can harm latency before a kill", "Pressure means the application leaked", "The kernel cannot report pressure"], "A service can make slow progress under reclaim without an OOM event."),
    ("What proves repeated RSS growth is a leak?", ["A retained baseline across comparable work cycles after examining charge classes", "One rising dashboard line", "A restart returning RSS to zero"], "A controlled comparison distinguishes retained state from warm-up and cache."),
    ("What should follow a cache size reduction?", ["Measure hit rate, downstream load, and latency", "Assume memory savings have no cost", "Turn off downstream monitoring"], "Less cache memory can increase network or database work."),
    ("Six new Pods each request 896 MiB and surge is two. What extra request must fit?", ["1792 MiB", "896 MiB", "5376 MiB"], "Two surge Pods require two additional requests before old Pods leave."),
    ("What if aggregate free memory is ample but no node can fit a new Pod?", ["Treat per-node placement as the constraint", "Lower requests without measurement", "Ignore affinity and topology"], "Scheduling requires a node satisfying the Pod's full request and placement rules."),
]
quiz = copy.deepcopy(by_path["quizzes/devops-operations"])
quiz.update(id=str(uuid.uuid5(uuid.NAMESPACE_URL, "aitrove:" + quiz_path)), path=quiz_path,
            title=titles[quiz_path], summary="Twelve decisions on OOM attribution, JVM headroom, tmpfs, reclaim, and rollout placement.",
            sort_order=24100, published_at=stamp, created_at=stamp, updated_at=stamp)
quiz["data"] = {"subject_root": course, "section_path": quiz_hub, "content_format": "html",
                "author_path": "authors/aitrove-editorial", "seo_ready": True, "duration_minutes": 12,
                "related": [{"path": target, "title": titles[target]} for target in related_paths],
                "questions": [dict(prompt=prompt, options=options[index % 3:] + options[:index % 3],
                                   answer=(-index % 3) % 3, explanation=explanation)
                              for index, (prompt, options, explanation) in enumerate(questions)]}
quiz["body"] = (
    "<p>Classify the memory failure before selecting a repair. Each answer should account for the container, the node, and the user path affected by the change.</p>"
    "<h2>Review these lessons</h2>" + links(related_paths)
    + "<h2>Other checks</h2>" + links([quiz_hub, "quizzes/devops-runtime-isolation-decisions", "quizzes/devops-cost-capacity-decisions"])
    + "<h3>Common Mistakes</h3><ul><li>Do not treat every memory graph as the same signal.</li><li>Do not confuse a fix for one Pod with recovered service capacity.</li></ul>"
)
rows.append(quiz)
by_path[quiz_hub]["data"]["modules"][0]["lessons"].append(quiz_path)
by_path[quiz_hub]["body"] += "<h2>Memory failure check</h2>" + links([quiz_path])
by_path[quiz_hub]["updated_at"] = stamp

for item in specs:
    row = next(row for row in rows if row["path"] == item["path"])
    row["body"] += "<h2>Practice and check</h2>" + links([project_path, quiz_path])
    row["data"]["related"].extend({"path": path, "title": titles[path]} for path in [project_path, quiz_path])

for source, targets in {
    "devops/node-pressure-eviction": [specs[0]["path"], specs[3]["path"]],
    "devops/kubernetes-resource-budgets": [specs[1]["path"], specs[5]["path"]],
    "devops/ephemeral-storage-limit-accounting": [specs[2]["path"]],
    "devops/observability-signals": [specs[3]["path"], specs[4]["path"]],
    "devops/capacity-load-testing": [specs[4]["path"], specs[5]["path"]],
    "devops/node-autoscaling-headroom": [specs[5]["path"]],
    "devops/runtime-isolation-recovery-project": [project_path],
}.items():
    row = by_path[source]
    row["body"] += "<h2>Memory failure follow-up</h2>" + links(targets)
    row["data"].setdefault("related", []).extend({"path": target, "title": titles[target]} for target in targets)
    row["updated_at"] = stamp

assert len({row["path"] for row in rows}) == len(rows)
fixture.write_text(json.dumps(rows, ensure_ascii=False, indent=2) + "\n")
print(json.dumps({"new_lessons": len(specs), "new_projects": 1, "new_quiz_banks": 1,
                  "total_records": len(rows)}))
