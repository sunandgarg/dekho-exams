"""Publish runtime dependency and inference economics modules."""
from de_batch_publisher import publish

M = 'mlops/'
R = 'Model runtime dependencies and patch response'
C = 'Inference cost attribution and budget gates'

lessons = [
    {
        'path': M + 'model-runtime-dependency-inventory',
        'title': 'Model runtime inventory: packages, loaders and execution providers',
        'module': R, 'project': False,
        'summary': 'The model file is only one part of a serving release; inventory the code and native components that load and execute it.',
        'sections': [
            ('Inventory what the model actually loads', 'Record the serving image digest, language runtime, model loader, framework, native libraries, execution provider, custom operators, preprocessing package and model format for each deployment. An automatically inferred package list can miss imports used only on uncommon routes or native libraries loaded by a provider. Capture the resolved installed versions from a clean build and exercise the real prediction entry point. [[mlops/run-manifest-and-artifact-lineage|Run lineage]] explains where the model came from; this inventory explains what executes its bytes.'),
            ('Bind inventory to deployed identity', 'A package manifest detached from its image or model digest quickly becomes stale. Attach the inventory to the image digest, model digest and route revision, then compare those identities with what each environment serves. Record provenance for third-party binaries and the owner who can approve an update. Model artifacts that deserialize executable objects deserve a stronger loading boundary than a plain data format. [[mlops/model-artifact-digest-and-safe-loading|Safe loading]] checks the artifact itself, while this module covers its transitive runtime.'),
            ('Map affected deployments precisely', 'When a library issue is found, search the inventory for exact component and version, then trace to serving cohorts, offline devices and retained rollback images. Do not assume every model trained with a package is serving through that package; training and inference environments differ. Equally, a shared base image may put many otherwise unrelated models at risk. Keep environment and runtime identity in [[mlops/inference-chain-contracts-and-stage-identity|the inference chain]] so the impact query is an evidence-backed join.'),
            ('Make missing evidence a release failure', 'A candidate without an inventory, owner or clean-load smoke test should not promote. Store the manifest with the release packet and regenerate it on every image rebuild. A version string is not enough when different bytes can be published under the same tag; prefer immutable digests for images and binaries where available. [[mlops/runtime-patch-canary-and-rollback|The patch canary]] tests behavior after a component update, and [[mlops/receipt-runtime-patch-project|the project]] uses an urgent loader fix that changes numeric output on one host class.'),
        ],
        'code': '''def affected_releases(releases, component, affected_versions):
    if not component or not affected_versions:
        raise ValueError("component and versions required")
    return [release["release_id"] for release in releases
            if release["dependencies"].get(component) in affected_versions]

releases = [
    {"release_id": "receipt-r47", "dependencies": {"model-loader": "2.8"}},
    {"release_id": "invoice-r31", "dependencies": {"model-loader": "3.1"}},
    {"release_id": "receipt-r48", "dependencies": {"model-loader": "2.8"}},
]
assert affected_releases(releases, "model-loader", {"2.8"}) == \
       ["receipt-r47", "receipt-r48"]
''',
        'cost': 'Scanning r releases is O(r) time and O(a) result space for a affected releases; an indexed inventory can reduce repeated lookup work. Manifest generation and smoke tests add build time and artifact storage. The cost buys a faster, narrower patch response: a component name without deployment linkage leaves teams guessing which models are exposed.',
        'mistakes': ['Inventorying only Python packages while ignoring native providers.', 'Assuming training dependencies match serving dependencies.', 'Treating a mutable image tag as immutable evidence.', 'Approving a model whose uncommon prediction route was never loaded.'],
        'related': [M + 'runtime-patch-canary-and-rollback', M + 'receipt-runtime-patch-project', M + 'model-artifact-digest-and-safe-loading', M + 'run-manifest-and-artifact-lineage', M + 'inference-chain-contracts-and-stage-identity'],
    },
    {
        'path': M + 'runtime-patch-canary-and-rollback',
        'title': 'Runtime patch canaries: security fix without model drift',
        'module': R, 'project': False,
        'summary': 'Patch a serving dependency with an explicit replay and host-class canary, then keep a safe rollback decision ready.',
        'sections': [
            ('Classify the patch boundary', 'A loader, framework or execution-provider update can alter deserialization, graph optimization and numeric kernels even when the model digest is identical. Record the issue, affected version range, fixed build, exposure path and urgency. If the vulnerable code is unreachable in the configured serving route, document that evidence rather than assuming exposure from a package name alone. If it is reachable, contain the route while the patch is tested. [[mlops/model-runtime-dependency-inventory|The inventory]] identifies each deployment and owner.'),
            ('Replay the old and new stacks', 'Hold model bytes, preprocessing and inputs constant while comparing the old and patched runtime. Test load failures, output schema, score distances, threshold crossings, p99 latency, memory and fallback behavior by hardware class. A security patch may fix one exploit while breaking a custom operator. Do not waive functional checks because the change is “only infrastructure.” [[mlops/optimized-model-calibration-and-parity|Score parity]] and [[mlops/optimized-model-hardware-matrix-and-fallback|hardware qualification]] provide reusable gates.'),
            ('Stage by exposure and host class', 'Deploy the patched image to a small compatible cohort, verify selected provider and actual model digest, then watch crashes, route rates and tail latency. A single global canary can miss the only host class that uses a vulnerable native library. Keep the rollout window short enough for the issue’s urgency, but long enough to collect exposed decisions. [[mlops/trace-sampling-and-coverage-ledger|Coverage evidence]] prevents a quiet dashboard from being read as a pass.'),
            ('Choose a safe recovery route', 'Rolling back to a vulnerable image may be unacceptable. Prepare an alternate known-safe image, disable the affected model route or move a cohort to a supported provider if parity and capacity allow. Record a decision tree before rollout. A rollback plan that merely says “restore previous version” is incomplete when the previous version contains the issue. [[mlops/receipt-runtime-patch-project|The project]] exercises exactly that choice and keeps the corrected host class on a safe fallback until its patched provider passes replay.'),
        ],
        'code': '''def patch_disposition(patch, canary):
    if not patch["fixed_build_verified"]:
        return "hold:unverified-fix"
    if canary["route_flips"] or not canary["provider_verified"]:
        return "fallback:safe-provider"
    if canary["p99_ms"] > canary["p99_budget_ms"]:
        return "fallback:safe-provider"
    return "expand:patched-image"

patch = {"fixed_build_verified": True}
canary = {"route_flips": 0, "provider_verified": True,
          "p99_ms": 71, "p99_budget_ms": 89}
assert patch_disposition(patch, canary) == "expand:patched-image"
assert patch_disposition(patch, {**canary, "route_flips": 2}) == \
       "fallback:safe-provider"
assert patch_disposition({"fixed_build_verified": False}, canary) == \
       "hold:unverified-fix"
''',
        'cost': 'The disposition gate is O(1) time and space. Full patch qualification costs replay, hardware-cell benchmarks, a staged cohort and temporary duplicate images. Urgent fixes compress the observation window, increasing uncertainty; risk can be reduced by narrowing affected routes and using a tested safe provider rather than skipping correctness checks.',
        'mistakes': ['Assuming unchanged model bytes imply unchanged predictions.', 'Canarying only the dominant host class.', 'Calling a patched version safe without verifying the fixed build.', 'Planning rollback to the known vulnerable image as the only escape.'],
        'related': [M + 'model-runtime-dependency-inventory', M + 'receipt-runtime-patch-project', M + 'optimized-model-calibration-and-parity', M + 'optimized-model-hardware-matrix-and-fallback', M + 'trace-sampling-and-coverage-ledger'],
    },
    {
        'path': M + 'receipt-runtime-patch-project',
        'title': 'Project: patch a receipt-model loader across mixed hosts',
        'module': R, 'project': True,
        'summary': 'Map an affected loader to deployed models, replay the fix on each host class and stage a safe fallback where parity fails.',
        'sections': [
            ('Find the affected route', 'A loader issue is reported for the version used by two receipt models. Query the deployment inventory for image digests, loader version, model format, custom operators and serving cohorts. Confirm whether the affected loading path is reachable for each model; training-only packages are outside the immediate serving exposure. Preserve the original image and fixed image digests. [[mlops/model-runtime-dependency-inventory|The inventory]] becomes the impact register, not a hand-written list assembled during an incident.'),
            ('Hold the model constant', 'Replay 2,600 paired receipt inputs through the old and fixed runtime with identical model bytes and preprocessing. One ARM class changes provider and produces three threshold crossings despite passing the output-schema smoke test. A newer CPU class keeps parity and improves its loader behavior. Investigate the provider partition before shipping to ARM. [[mlops/runtime-patch-canary-and-rollback|The patch gate]] rejects route drift even when the security fix itself is required.'),
            ('Stage a safe alternative', 'The old image cannot be the only rollback target. Route the ARM cohort through a previously qualified safe CPU provider with the fixed loader, then test its p99 and memory at expected traffic. Keep the newer CPU cohort on the patched accelerated provider. Verify the model digest, provider and image digest at the serving endpoint. If neither fixed path meets the contract, temporarily hold the affected feature and send receipts to manual review under an approved policy. [[mlops/region-failover-model-and-feature-identity|Failover identity]] helps prevent an alternate route from silently changing model inputs.'),
            ('Close with evidence', 'Publish affected and unaffected deployment lists, replay deltas, host-class canary results, fixed-build verification, route policy and owner sign-off. Monitor load failures, threshold crossings, tail latency and fallback share until the patch is fully deployed. Keep a record of the temporary provider choice so it is removed deliberately after a corrected accelerator path passes. [[mlops/promotion-attestation-and-reversible-pointer|Promotion evidence]] should point to the exact image and model pair.'),
        ],
        'code': '''def host_patch_route(host, fixed_loader, parity_ok, safe_provider_ok):
    if not fixed_loader:
        return "block:unfixed-loader"
    if parity_ok:
        return "serve:patched-provider"
    if safe_provider_ok:
        return "serve:safe-provider"
    return "manual-review"

assert host_patch_route("arm-r5", True, False, True) == "serve:safe-provider"
assert host_patch_route("cpu-r8", True, True, True) == "serve:patched-provider"
assert host_patch_route("arm-r3", True, False, False) == "manual-review"
assert host_patch_route("arm-r5", False, True, True) == "block:unfixed-loader"
''',
        'cost': 'Routing is O(1) time and space per host after qualification. Running both provider paths, replaying 2,600 requests and keeping a manual-review capacity reserve have real cost. The fallback path can increase latency and human workload; measure both and retire it only after the accelerated path passes the same route and host-class gates.',
        'mistakes': ['Patching only one of several serving images with the affected loader.', 'Shipping an ARM graph that passes schema checks but flips review routes.', 'Using an unfixed image as the sole rollback option.', 'Forgetting to remove a costly fallback after a corrected path is qualified.'],
        'related': [M + 'model-runtime-dependency-inventory', M + 'runtime-patch-canary-and-rollback', M + 'region-failover-model-and-feature-identity', M + 'promotion-attestation-and-reversible-pointer', M + 'optimized-model-hardware-matrix-and-fallback'],
    },
    {
        'path': M + 'inference-cost-ledger-and-allocation',
        'title': 'Inference cost ledger: allocate shared capacity without false precision',
        'module': C, 'project': False,
        'summary': 'Attribute model-serving spend to traffic and capacity while keeping idle time, shared hosts and sampling limits visible.',
        'sections': [
            ('Choose the billable boundary', 'A receipt-risk service pays for instances, accelerators, memory, storage, network and supporting queues. A request counter alone does not identify the cost of idle replicas or shared hosts. Collect provider billing by resource and time window, then attach immutable deployment, model and route identities to usage measurements. Keep a separate unallocated bucket for idle or unknown capacity. [[mlops/multi-model-admission-and-noisy-neighbors|Shared serving capacity]] explains why one tenant’s usage can affect another’s latency and bill.'),
            ('Allocate with a stated rule', 'For an exclusive endpoint, attribute its resource cost to its model for the window. For a shared pool, allocate a measured share by GPU time, CPU time or another defensible usage signal, and report the residual as shared overhead. If only request counts exist, label the result an estimate and keep the method visible. Never force allocations to sum to a false level of precision by hiding idle capacity. [[mlops/trace-sampling-and-coverage-ledger|Telemetry coverage]] tells readers how much usage was actually observed.'),
            ('Normalize carefully', 'Cost per completed prediction can be useful, but count retries, rejected inputs, asynchronous completions and manual fallback separately. A cheap route that drops hard cases can look efficient while shifting cost to reviewers. Compare cost by model digest, hardware class, traffic cohort and quality outcome, then pair cost with p99 latency and error rate. [[mlops/async-result-ledger-and-replay|Async result ledgers]] prevent submitted jobs from being mistaken for completed predictions.'),
            ('Turn the ledger into a decision', 'Set a per-route budget with a lookback window and an owner. If cost rises, split the change into traffic volume, unit price, utilization and request work. A new model that raises per-request compute may still lower total business cost if it reduces review workload; state both measures. [[mlops/inference-budget-gates-and-capacity-tradeoffs|Budget gates]] choose an action, and [[mlops/receipt-inference-cost-project|the project]] traces a retry loop that makes the unit-cost graph misleading.'),
        ],
        'code': '''def allocate_shared_cost(attributable_cost, idle_cost, measured_usage):
    if min(attributable_cost, idle_cost) < 0 or any(
            value < 0 for value in measured_usage.values()):
        raise ValueError("negative cost or usage")
    used = sum(measured_usage.values())
    if used <= 0:
        return {"unallocated": attributable_cost + idle_cost}
    allocated = {model: attributable_cost * value / used
                 for model, value in measured_usage.items()}
    allocated["unallocated"] = idle_cost
    return allocated

share = allocate_shared_cost(470.0, 47.0,
                             {"receipt-risk": 3.0, "invoice-risk": 2.0})
assert share["receipt-risk"] == 282.0
assert share["invoice-risk"] == 188.0
assert share["unallocated"] == 47.0
assert allocate_shared_cost(47.0, 5.0, {}) == {"unallocated": 52.0}
''',
        'cost': 'Allocation is O(m) time and O(m) output space for m models. The sample divides a known attributable charge by measured usage and preserves idle cost as unallocated; production ledgers must first separate those charges, or the rule will misattribute idle spend. High-cardinality model and route labels increase telemetry storage, so aggregate at the finest level needed for a decision.',
        'mistakes': ['Dividing the entire instance bill by successful requests without accounting for idle time.', 'Calling a request-count split exact when request compute varies.', 'Counting submissions as completions in an asynchronous route.', 'Optimizing serving spend while ignoring manual-review cost and quality.'],
        'related': [M + 'inference-budget-gates-and-capacity-tradeoffs', M + 'receipt-inference-cost-project', M + 'multi-model-admission-and-noisy-neighbors', M + 'trace-sampling-and-coverage-ledger', M + 'async-result-ledger-and-replay'],
    },
    {
        'path': M + 'inference-budget-gates-and-capacity-tradeoffs',
        'title': 'Inference budget gates: cost, latency and quality together',
        'module': C, 'project': False,
        'summary': 'A model rollout should satisfy an operating budget without hiding latency regressions or moving expensive cases to people.',
        'sections': [
            ('Establish a comparable baseline', 'Freeze a traffic mix, observation window, completed-decision definition and resource price basis before comparing variants. Separate fixed replica cost from marginal request work. A short benchmark can understate idle expense and cold starts; a long window can conceal a sudden new route. Record baseline model digest and rollout cohort so the old and new costs describe equivalent work. [[mlops/inference-cost-ledger-and-allocation|The cost ledger]] supplies attribution and its uncertainty.'),
            ('Gate on several dimensions', 'A candidate can save compute by sending borderline receipts to manual review, delaying them in a queue or dropping optional checks. Define minimum quality, maximum p99 latency, completion rate and cost per approved decision. Keep manual-review minutes and retry volume as companion measures. Do not collapse these into one opaque weighted score; a hard safety limit should remain a hard limit. [[mlops/score-threshold-policy-and-change-control|Threshold policy]] and [[mlops/slice-quality-gates-and-uncertainty|slice gates]] protect decision quality.'),
            ('Diagnose budget breaches', 'Decompose spend into replica-hours, utilization, provider fallback, batch size, retries and traffic mix. If volume doubles while unit cost stays flat, capacity planning is the issue. If cost per completed decision rises only on older hosts, inspect provider selection or memory pressure before changing the model. [[mlops/optimized-model-hardware-matrix-and-fallback|The hardware matrix]] helps explain when an apparent optimization costs more in one cell.'),
            ('Choose a reversible response', 'A budget breach can hold rollout, adjust a safe autoscaling policy, restore an approved model, shift compatible traffic or request a temporary budget exception with an expiry. Do not silently lower quality or disable required review routes to make a graph green. Publish the forecast, observed coverage, owner and next check time. [[mlops/receipt-inference-cost-project|The project]] shows why deduplicating retries and counting completed decisions can change a “cost spike” diagnosis.'),
        ],
        'code': '''def inference_release_gate(metrics, limits):
    if metrics["completed"] <= 0 or metrics["cost"] < 0:
        return "hold:invalid-window"
    if metrics["quality"] < limits["minimum_quality"]:
        return "hold:quality"
    if metrics["p99_ms"] > limits["maximum_p99_ms"]:
        return "hold:latency"
    if metrics["cost"] / metrics["completed"] > limits["maximum_cost_each"]:
        return "hold:cost"
    return "stage"

limits = {"minimum_quality": 0.91, "maximum_p99_ms": 94,
          "maximum_cost_each": 0.08}
metrics = {"completed": 4700, "cost": 329.0,
           "quality": 0.94, "p99_ms": 83}
assert inference_release_gate(metrics, limits) == "stage"
assert inference_release_gate({**metrics, "quality": 0.89}, limits) == "hold:quality"
''',
        'cost': 'The decision is O(1) time and space after metrics exist. Computing those metrics costs billing ingestion, completion joins, quality adjudication and a representative observation window. A hard budget reduces runaway spend but may hold a legitimate traffic surge; make exceptions explicit and time-bounded rather than weakening the quality and latency gates.',
        'mistakes': ['Using submitted request count as the cost denominator.', 'Treating a lower bill as success when review work increases.', 'Averaging p99 latency across unlike cohorts.', 'Changing production thresholds to meet a cost target without a quality review.'],
        'related': [M + 'inference-cost-ledger-and-allocation', M + 'receipt-inference-cost-project', M + 'score-threshold-policy-and-change-control', M + 'slice-quality-gates-and-uncertainty', M + 'optimized-model-hardware-matrix-and-fallback'],
    },
    {
        'path': M + 'receipt-inference-cost-project',
        'title': 'Project: explain a receipt-model serving cost spike',
        'module': C, 'project': True,
        'summary': 'Reconcile billing and completed decisions, identify retry amplification and choose a budget response that preserves quality.',
        'sections': [
            ('Reconstruct the window', 'A receipt-risk endpoint appears to cost 38 percent more after a release. Freeze the before and after windows, model and image digests, completed-decision counts, instance prices, retry policy and traffic mix. Billing shows more replica-hours; traces show a higher request count but not a matching increase in completed receipts. Build the ledger from resource cost and completion identity before saying the model became more expensive. [[mlops/inference-cost-ledger-and-allocation|Allocation rules]] must leave idle and unknown capacity visible.'),
            ('Find the amplification', 'Group attempts by idempotency key and record retries, timeouts and successful completions. One client cohort retries after 47 milliseconds, earlier than the service’s normal tail, so many receipts are scored twice. Separate retry work from model compute and compare p99 by host class. The new model also falls back on an older CPU class; that is a second, narrower cost driver. [[mlops/async-result-ledger-and-replay|The result ledger]] prevents duplicate attempts from being counted as new business decisions.'),
            ('Test safe responses', 'Correct the client retry deadline and verify idempotent completion. Keep the old host class on its qualified artifact until the optimized path passes its hardware matrix. Recalculate forecast cost per completed decision under the expected mix, then check quality and p99 against the baseline. Do not lower the review threshold or drop blurry scans just to meet the budget. [[mlops/inference-budget-gates-and-capacity-tradeoffs|The budget gate]] requires all dimensions to pass.'),
            ('Close the accounting loop', 'Publish observed resource cost, completed decisions, duplicate attempts, provider fallback, unallocated spend, quality and p99. Assign separate owners to retry logic and runtime qualification. Stage each correction so the cost effect can be measured without confusing it with traffic changes. Keep an expiry on any budget exception and a rollback pointer for the serving artifact. [[mlops/promotion-attestation-and-reversible-pointer|Promotion identity]] makes the next comparison auditable.'),
        ],
        'code': '''def completed_unit_cost(resource_cost, attempts):
    if resource_cost < 0:
        raise ValueError("negative cost")
    completed = {attempt["decision_id"] for attempt in attempts
                 if attempt["state"] == "completed"}
    if not completed:
        return {"cost_each": None, "completed": 0}
    return {"cost_each": resource_cost / len(completed),
            "completed": len(completed)}

attempts = [{"decision_id": "receipt-47", "state": "timeout"},
            {"decision_id": "receipt-47", "state": "completed"},
            {"decision_id": "receipt-82", "state": "completed"}]
assert completed_unit_cost(0.14, attempts)["completed"] == 2
assert completed_unit_cost(0.14, attempts)["cost_each"] == 0.07
assert completed_unit_cost(0.14, attempts[:1])["cost_each"] is None
''',
        'cost': 'Deduplicating a attempts uses O(a) expected time and O(d) memory for d distinct completed decisions. At production scale, do this in a bounded window or keyed store rather than loading every event into process memory. A corrected retry policy saves wasted compute but must preserve completion reliability; test timeout and replay semantics before rollout.',
        'mistakes': ['Dividing the bill by all attempts instead of unique completions.', 'Blaming the model before isolating client retries and provider fallback.', 'Ignoring idle replica-hours in the cost change.', 'Meeting the budget by dropping difficult cases or changing safety routes.'],
        'related': [M + 'inference-cost-ledger-and-allocation', M + 'inference-budget-gates-and-capacity-tradeoffs', M + 'async-result-ledger-and-replay', M + 'optimized-model-hardware-matrix-and-fallback', M + 'promotion-attestation-and-reversible-pointer'],
    },
]

crosslinks = [
    (M + 'model-artifact-digest-and-safe-loading', M + 'model-runtime-dependency-inventory'),
    (M + 'trace-sampling-and-coverage-ledger', M + 'runtime-patch-canary-and-rollback'),
    (M + 'optimized-model-hardware-matrix-and-fallback', M + 'receipt-runtime-patch-project'),
    (M + 'multi-model-admission-and-noisy-neighbors', M + 'inference-cost-ledger-and-allocation'),
    (M + 'score-threshold-policy-and-change-control', M + 'inference-budget-gates-and-capacity-tradeoffs'),
    (M + 'async-result-ledger-and-replay', M + 'receipt-inference-cost-project'),
]

if __name__ == '__main__':
    publish(lessons, (R, C), crosslinks,
            'aitrove-mlops-runtime-cost-import-20261006.json', 6178,
            subject='mlops', hub_path=M + 'mlops-tutorial')
