"""Publish model-risk evidence and inference API compatibility lessons."""
from de_batch_publisher import publish

M = 'mlops/'
G = 'Model risk evidence and release scope'
A = 'Inference API compatibility and caller migration'

lessons = [
    {
        'path': M + 'model-card-scope-and-limitation-register',
        'title': 'Model cards as operating contracts: scope, evidence and limits',
        'module': G, 'project': False,
        'summary': 'A model card should tell a release reviewer where a model may run, what was measured and which uses remain unsupported.',
        'sections': [
            ('Name the decision, not just the algorithm', 'A receipt triage model assigns a review priority to eligible digital receipts. The card must state the decision owner, affected workflow, intended user, permitted geography and fallback when evidence is missing. A statement such as “detects fraud” is too broad: it hides who acts on the score and may invite use as an automatic denial. Keep the threshold and its owner alongside the decision description. [[mlops/run-manifest-and-artifact-lineage|Run lineage]] identifies the trained bytes; the card explains their supported use.'),
            ('Connect every claim to a frozen cohort', 'Record the data snapshot, labeling rule, time window, exclusion criteria, threshold and mature-outcome coverage behind each metric. Report overall quality alongside named slices that matter to operations, such as new merchants, uncommon currencies or low-quality scans. A slice with few labeled outcomes is unknown, not proof of parity. Link the exact evaluation run and model digest through [[mlops/model-registry-promotion-gates|promotion evidence]]. Avoid a screenshot of a dashboard that cannot be reproduced after labels are corrected.'),
            ('Write limitations as actions', 'A useful limitation names a trigger and response. If a receipt currency was absent from evaluation, route that case to manual review until evidence exists. If a feature goes stale, follow [[mlops/online-feature-freshness-budget-and-ttl|the freshness policy]] rather than silently score an old value. Separate unsupported use from known error patterns and unresolved risks. The card belongs to a versioned release: changing the model, threshold, eligible population or response policy may require a new review, even if the artifact digest is unchanged.'),
            ('Keep the record alive after release', 'Assign a review date and owner. Add field failures, overridden decisions and corrected labels as dated entries without rewriting the original approval. Compare deployed population with the approved scope; sustained movement into an untested slice should open a fresh evaluation, not quietly broaden the card. [[mlops/model-consumer-inventory-and-retirement-gates|Consumer inventory]] shows where the model is used, while [[mlops/receipt-model-card-review-project|the review project]] turns a vague claim into an enforceable release boundary.'),
        ],
        'code': '''def check_model_scope(card, request):
    if card["digest"] != request["model_digest"]:
        return "hold:digest"
    if request["country"] not in card["approved_countries"]:
        return "manual-review:geography"
    if request["currency"] not in card["evaluated_currencies"]:
        return "manual-review:currency"
    return "score"

card = {"digest": "receipt-r47", "approved_countries": {"IN", "SG"},
        "evaluated_currencies": {"INR", "SGD"}}
receipt = {"model_digest": "receipt-r47", "country": "IN", "currency": "INR"}
assert check_model_scope(card, receipt) == "score"
assert check_model_scope(card, {**receipt, "currency": "EUR"}) == "manual-review:currency"
''',
        'cost': 'Membership checks are O(1) expected time and O(c) memory for c allowed scope values. Maintaining the card costs review time and evidence storage, but the operational cost of a missing scope boundary is unmeasured use. The code checks a small gate; it does not measure whether the listed slices were evaluated well.',
        'mistakes': ['Treating a single aggregate score as evidence for every population.', 'Writing a limitation without a routing or escalation action.', 'Approving a threshold change under the old card without review.', 'Overwriting the original approval after a production incident.'],
        'related': [M + 'slice-quality-gates-and-uncertainty', M + 'receipt-model-card-review-project', M + 'run-manifest-and-artifact-lineage', M + 'model-registry-promotion-gates', M + 'model-consumer-inventory-and-retirement-gates'],
    },
    {
        'path': M + 'slice-quality-gates-and-uncertainty',
        'title': 'Slice quality gates when labels are sparse or delayed',
        'module': G, 'project': False,
        'summary': 'A release gate should expose weak evidence in important populations rather than averaging it away.',
        'sections': [
            ('Define slices before the candidate result', 'Choose operationally meaningful cohorts from the intended-use boundary: merchant age, receipt channel, currency or human-review route. Freeze definitions and minimum counts before reading candidate metrics. Many ad hoc cuts can uncover real problems, but selecting only the most favorable cuts after evaluation makes the release story unreliable. Each record should include cohort size, labeled count and the fraction whose outcome has matured. [[mlops/prediction-outcome-join-and-maturity|Outcome maturity]] is especially important when suspicious receipts are resolved weeks later.'),
            ('Distinguish failure from uncertainty', 'A slice with twelve mature labels and two errors should not be treated like one with twelve thousand labels, even when both show the same observed rate. Set a minimum evidence floor and compare error rates with uncertainty intervals or a documented small-sample rule. If the floor is missed, mark the slice insufficient and either hold the rollout or constrain that population to a safer route. An unknown slice is not automatically a model defect. [[mlops/model-card-scope-and-limitation-register|The model card]] records the decision and its remaining limits.'),
            ('Check the right denominator', 'Receipts routed to manual review often receive labels faster than auto-approved receipts. A naïve measured error rate among reviewed receipts describes a selected subset, not the full decision population. Preserve the original eligible count, exposure count and mature-label count per slice. Compare candidate and baseline on the same eligibility and outcome window, and annotate label corrections. [[mlops/label-corrections-and-evaluation-ledger|The evaluation ledger]] prevents a later correction from changing a release claim without a trace.'),
            ('Gate a release with an explicit state', 'Return pass, fail or insufficient rather than hiding missing evidence inside a numeric score. A severe error in a high-impact slice may block release even if the total metric improves. Record the gate revision, slice definition, measured counts and reviewer override. Overrides need an owner, expiration and compensating control, such as manual review for the affected slice. [[mlops/receipt-model-card-review-project|The applied review]] exercises a candidate that improves the average but has too little evidence for a new merchant cohort.'),
        ],
        'code': '''def slice_gate(mature_count, error_count, max_error_rate=0.06,
               minimum_mature=47):
    if mature_count < 0 or error_count < 0 or error_count > mature_count:
        raise ValueError("invalid evaluation counts")
    if mature_count < minimum_mature:
        return {"state": "insufficient", "observed_rate": None}
    rate = error_count / mature_count
    return {"state": "fail" if rate > max_error_rate else "pass",
            "observed_rate": rate}

assert slice_gate(28, 2)["state"] == "insufficient"
assert slice_gate(50, 4)["state"] == "fail"
assert slice_gate(100, 4)["state"] == "pass"
''',
        'cost': 'A single slice gate is O(1) time and space after counting. Evaluating s slices over n decisions costs O(n + s) when cohorts are assigned during one pass; overlapping cohorts may add membership work. The illustrated threshold is a policy example, not a statistical confidence bound. Real release rules need uncertainty and harm thresholds chosen for their use case.',
        'mistakes': ['Calling an unlabeled cohort a quality pass.', 'Choosing slice definitions after seeing candidate errors.', 'Comparing candidate and baseline on different maturity windows.', 'Treating an observed small-sample rate as a precise estimate.'],
        'related': [M + 'model-card-scope-and-limitation-register', M + 'receipt-model-card-review-project', M + 'prediction-outcome-join-and-maturity', M + 'label-corrections-and-evaluation-ledger', M + 'experiment-guardrails-and-interference'],
    },
    {
        'path': M + 'receipt-model-card-review-project',
        'title': 'Project: approve a receipt model with a scoped evidence dossier',
        'module': G, 'project': True,
        'summary': 'Review a candidate digest against intended use, slice evidence and production routing before any traffic is promoted.',
        'sections': [
            ('Assemble one immutable dossier', 'Use the candidate receipt model digest, training run manifest, feature contract, evaluation snapshot and proposed response policy. State that the score prioritizes human review; it must not become an automatic payment denial. Name supported countries and currencies, the decision threshold owner and the safe route for unsupported inputs. [[mlops/model-card-scope-and-limitation-register|The operating card]] supplies the human decision, while [[mlops/model-artifact-digest-and-safe-loading|the artifact digest]] pins the executable bytes.'),
            ('Probe three uncomfortable cohorts', 'Evaluate established merchants, new merchants and low-quality scans on the same mature outcome window. The candidate improves overall recall, but the new merchant cohort has only 28 mature outcomes against a 47-outcome minimum. Mark that slice insufficient. Do not turn the missing evidence into a favorable score. For low-quality scans, inspect the error count and feature availability together; a bad result may call for admission control rather than another threshold. Record eligible, scored, reviewed and labeled counts for each cohort.'),
            ('Choose an enforceable release state', 'The sample dossier should hold broad promotion. It may propose a restricted pilot that routes new merchants to manual review, but only after an owner approves that compensating control and verifies the API enforces it. Store the control expiry and the evidence that will end the restriction. [[mlops/slice-quality-gates-and-uncertainty|Slice gates]] produce pass, fail or insufficient; [[mlops/promotion-attestation-and-reversible-pointer|promotion attestation]] must not treat “insufficient” as a pass. Re-evaluate whenever scope or threshold changes.'),
            ('Deliver reviewable artifacts', 'Publish the card revision, model digest, cohort query ID, metrics, maturity rule, gate results, limitations, compensating control and reviewer decision. Include an operator test that sends an unsupported currency through the endpoint and observes manual review. A dashboard link alone is weak evidence: it can change after label corrections or data retention. Preserve a dated decision record and tell [[mlops/model-consumer-inventory-and-retirement-gates|registered consumers]] which fields and routes they may expect.'),
        ],
        'code': '''def approve_receipt_release(slices, scope_route_verified):
    if not scope_route_verified:
        return {"state": "hold", "reason": "scope-route-unverified"}
    failed = [name for name, state in slices.items() if state == "fail"]
    unknown = [name for name, state in slices.items()
               if state == "insufficient"]
    if failed:
        return {"state": "hold", "reason": "slice-failure", "slices": failed}
    if unknown:
        return {"state": "restricted-review", "slices": unknown}
    return {"state": "candidate"}

review = {"established": "pass", "new-merchant": "insufficient",
          "low-quality-scan": "pass"}
assert approve_receipt_release(review, True)["state"] == "restricted-review"
assert approve_receipt_release(review, False)["state"] == "hold"
''',
        'cost': 'The decision scan is O(s) time and O(s) output space for s slices. Gathering evidence dominates: mature outcomes can take weeks and route verification needs integration testing. A restricted decision is not production approval by itself; the proposed compensating route must actually work, have an owner and expire or be re-reviewed.',
        'mistakes': ['Promoting because the total metric improved while a material slice is unknown.', 'Stating manual review as a limitation without exercising the route.', 'Saving metrics without the evaluation snapshot or model digest.', 'Leaving a restricted approval open indefinitely.'],
        'related': [M + 'model-card-scope-and-limitation-register', M + 'slice-quality-gates-and-uncertainty', M + 'promotion-attestation-and-reversible-pointer', M + 'receipt-feature-admission-project', M + 'trusted-model-promotion-project'],
    },
    {
        'path': M + 'inference-request-response-contracts',
        'title': 'Inference API contracts: version the decision, not only the payload',
        'module': A, 'project': False,
        'summary': 'A serving API must specify request validation, response meaning, model identity and stable failure behavior for every caller.',
        'sections': [
            ('Separate public and internal contracts', 'The HTTP request belongs to the caller; the feature vector belongs to the serving pipeline. A public receipt request may contain a receipt ID and capture time while the internal model consumes normalized merchant age and currency signals. Changing the feature contract does not require every caller to change. Conversely, renaming a public field is breaking even if the model bytes are identical. [[mlops/feature-schema-evolution-and-consumers|Feature schema evolution]] covers internal consumers; this page covers the endpoint boundary and its visible decision semantics.'),
            ('Specify acceptance and rejection', 'Write the accepted media type, required fields, units, length limits, idempotency key and timestamp rules. Define a stable error code for invalid input, unsupported currency and temporary feature unavailability. Do not reply with a successful score when admission fails. A response should include a decision ID, route, model digest or approved alias, policy revision and a machine-readable reason for fallback. [[mlops/feature-contract-and-admission-gates|Admission gates]] decide whether the feature state is fit to score; the API translates that state into a safe caller response.'),
            ('Protect old clients during change', 'Additive optional fields can often remain within one API version if old clients ignore unknown response fields and new required fields are not introduced. A changed score meaning, route enum or error code requires deliberate migration even when the JSON shape stays the same. Keep the old contract available until every registered consumer has moved, or provide an explicit version adapter with contract tests. [[mlops/inference-client-migration-and-contract-tests|Client migration]] sets the evidence needed to retire that adapter.'),
            ('Test against real caller expectations', 'Use captured redacted requests and caller-owned assertions to test valid input, absent fields, extra fields, repeated idempotency keys and unavailable features. Exercise the actual deployed endpoint; a schema test alone cannot catch a model digest unexpectedly promoted behind an alias. [[mlops/receipt-inference-api-migration-project|The project]] migrates two receipt consumers while preserving their response behavior. Keep response identity in [[mlops/inference-logging-privacy|restricted decision logs]] so an incident can join an API response to the served model.'),
        ],
        'code': '''def validate_receipt_request(payload):
    required = {"receipt_id", "currency", "captured_at"}
    if not isinstance(payload, dict) or not required <= payload.keys():
        return {"ok": False, "code": "INVALID_REQUEST"}
    if not all(isinstance(payload[key], str) and payload[key]
               for key in required):
        return {"ok": False, "code": "INVALID_REQUEST"}
    if payload["currency"] not in {"INR", "SGD"}:
        return {"ok": False, "code": "UNSUPPORTED_CURRENCY"}
    return {"ok": True, "code": "ACCEPTED"}

valid = {"receipt_id": "r-47", "currency": "INR",
         "captured_at": "2026-10-06T09:00:00Z"}
assert validate_receipt_request(valid)["ok"]
assert validate_receipt_request({**valid, "currency": "EUR"})["code"] == "UNSUPPORTED_CURRENCY"
''',
        'cost': 'Validation is O(f) expected time for f required fields and O(1) extra space here. A full endpoint also pays for parsing, authentication, feature reads and model inference. The example intentionally omits timestamp parsing and size limits; a real ingress should validate those at its trust boundary before feature lookup.',
        'mistakes': ['Treating a model artifact revision as an API version.', 'Returning HTTP success with an unmarked fallback score.', 'Changing a response enum without testing old callers.', 'Logging raw receipts to diagnose contract failures.'],
        'related': [M + 'inference-client-migration-and-contract-tests', M + 'receipt-inference-api-migration-project', M + 'feature-schema-evolution-and-consumers', M + 'feature-contract-and-admission-gates', M + 'inference-logging-privacy'],
    },
    {
        'path': M + 'inference-client-migration-and-contract-tests',
        'title': 'Migrate inference clients with compatibility tests and usage evidence',
        'module': A, 'project': False,
        'summary': 'A model endpoint is safe to change only when its registered callers have proved the new contract and stopped relying on the old one.',
        'sections': [
            ('Inventory who actually calls the endpoint', 'List each client, owner, environment, API version, request shape, response fields read and retry policy. Add traffic evidence from the gateway because a repository search misses scheduled jobs and old mobile builds. A consumer can depend on a route enum even if it ignores the score. [[mlops/model-consumer-inventory-and-retirement-gates|Consumer inventory]] supplies the owner and retirement process; this migration adds concrete protocol assertions and a per-client cutover state.'),
            ('Build a compatibility matrix', 'Replay redacted request fixtures from each caller against the old and candidate endpoint. Assert stable interpretation, not byte-for-byte equality when scores legitimately change. Test missing optional fields, unknown response fields, 4xx validation, 5xx retry, timeout, idempotency and fallback. If a caller assumes a route enum is exhaustive, a new value can crash it despite a valid schema. [[mlops/inference-request-response-contracts|The API contract]] names these visible behaviors, while [[mlops/ml-test-pyramid-and-data-fixtures|test fixtures]] make them repeatable in CI.'),
            ('Move callers in measured stages', 'Deploy a compatible adapter or explicit v2 route, send a small registered client cohort to it and record version in request traces. Watch rejected requests, fallback, latency and caller retries by client ID. Distinguish “no old traffic observed” from “all old clients migrated”; intermittent batch jobs need a window spanning their schedule. Do not retire v1 while an unowned client still sends production traffic. A staged gateway switch should have a reversible route pointer and a response sample that proves which contract served.'),
            ('Retire with an evidence trail', 'Record client sign-offs, last observed v1 call, scheduled-job coverage, rollback route and expiry for the adapter. Retest old and new versions after a model promotion, because a changed model can alter a response policy without changing an API schema. [[mlops/receipt-inference-api-migration-project|The applied migration]] runs a mobile reviewer and a nightly reconciliation job through different upgrade clocks. A safe deprecation is a measured state transition, not a date written in a ticket.'),
        ],
        'code': '''def retire_contract(registered, observed, required_window_days=35):
    blockers = []
    for client_id, record in registered.items():
        traffic = observed.get(client_id, {})
        if not record["signed_off"]:
            blockers.append((client_id, "unsigned"))
        elif traffic.get("v1_calls", 0) > 0:
            blockers.append((client_id, "old-traffic"))
        elif traffic.get("observed_days", 0) < required_window_days:
            blockers.append((client_id, "short-window"))
    return {"state": "hold" if blockers else "retire", "blockers": blockers}

clients = {"review-ui": {"signed_off": True},
           "nightly-ledger": {"signed_off": True}}
usage = {"review-ui": {"v1_calls": 0, "observed_days": 47},
         "nightly-ledger": {"v1_calls": 1, "observed_days": 47}}
assert retire_contract(clients, usage)["state"] == "hold"
assert retire_contract(clients, {**usage, "nightly-ledger":
       {"v1_calls": 0, "observed_days": 47}})["state"] == "retire"
''',
        'cost': 'The retirement check is O(c) time and O(c) output space for c clients. Contract replay costs more: fixture maintenance, deployed-environment access and at least one full cycle of rare callers. The example counts observed days; production evidence also needs traffic completeness, known caller IDs and a schedule long enough to cover infrequent jobs.',
        'mistakes': ['Retiring after a short quiet interval that misses monthly jobs.', 'Assuming schema validation proves semantic response compatibility.', 'Migrating a client without watching retry and fallback rates.', 'Ignoring an unknown caller because it has no owner entry.'],
        'related': [M + 'inference-request-response-contracts', M + 'receipt-inference-api-migration-project', M + 'model-consumer-inventory-and-retirement-gates', M + 'ml-test-pyramid-and-data-fixtures', M + 'promotion-attestation-and-reversible-pointer'],
    },
    {
        'path': M + 'receipt-inference-api-migration-project',
        'title': 'Project: migrate receipt inference callers without breaking decisions',
        'module': A, 'project': True,
        'summary': 'Ship a new receipt inference contract through caller tests, staged traffic and a documented v1 retirement gate.',
        'sections': [
            ('Freeze current caller behavior', 'The review UI reads route, decision ID and score; a nightly ledger reads route and model digest. Capture redacted v1 requests, expected error codes and client retry behavior. The proposed v2 adds an explicit fallback reason and revises the route names. Treat that rename as breaking, even though both versions still return JSON. Register both owners and schedules in [[mlops/model-consumer-inventory-and-retirement-gates|the consumer inventory]]. Keep the feature vector hidden behind [[mlops/inference-request-response-contracts|the public API boundary]].'),
            ('Implement and test the adapter', 'Provide a v1 response adapter that maps v2 decision states to old route names without discarding the decision ID. Reject unmappable states instead of fabricating a score. Replay client fixtures through both routes and force invalid currency, stale feature, timeout and duplicate request key. Assert that the ledger never interprets a fallback as an ordinary score. [[mlops/inference-client-migration-and-contract-tests|Compatibility tests]] should be owned by callers and run before moving real traffic.'),
            ('Cut over on separate clocks', 'Move the review UI first and inspect rejected requests, fallback, tail latency and retry counts by client ID. Keep the nightly ledger on v1 until its scheduled run and reconciliation check pass on v2. Log API version, decision ID and served model digest with redacted identifiers. If a bad route mapping appears, return the UI to v1 while preserving already issued decision records. [[mlops/promotion-attestation-and-reversible-pointer|A reversible pointer]] handles routing; it does not undo a decision already consumed.'),
            ('Prove retirement or hold', 'Watch v1 traffic for a window longer than the least frequent caller schedule. Require owner sign-off and a gateway inventory showing no unknown v1 clients. If the ledger makes one old call, retain v1 and investigate it; a planned deprecation date does not override observed traffic. Deliver a matrix of caller, fixture result, rollout state, last old call and rollback path. [[mlops/receipt-model-incident-drill-project|The incident drill]] is a useful follow-up for a contract failure discovered after cutover.'),
        ],
        'code': '''def adapt_route_for_v1(decision):
    routes = {"HUMAN_REVIEW": "review", "AUTO_CLEAR": "clear"}
    if decision["route"] not in routes:
        raise ValueError("v1 cannot represent this decision state")
    return {"decision_id": decision["decision_id"],
            "route": routes[decision["route"]],
            "score": decision["score"]}

new_decision = {"decision_id": "decision-47", "route": "HUMAN_REVIEW",
                "score": 0.82}
assert adapt_route_for_v1(new_decision)["route"] == "review"
try:
    adapt_route_for_v1({**new_decision, "route": "FEATURE_UNAVAILABLE"})
except ValueError:
    pass
else:
    raise AssertionError("unmappable fallback must fail closed")
''',
        'cost': 'The adapter is O(1) time and space per response. Running two contracts costs test maintenance, gateway routing and monitoring until the old caller population is gone. The adapter deliberately rejects an unrepresentable state; preserving an old schema by concealing a new failure could cause a downstream decision error.',
        'mistakes': ['Mapping feature failure to a valid score just to satisfy v1.', 'Cutting over a scheduled ledger before its first full v2 run.', 'Deleting v1 after owner sign-off while gateway still sees old calls.', 'Rolling back traffic without preserving decisions already issued.'],
        'related': [M + 'inference-request-response-contracts', M + 'inference-client-migration-and-contract-tests', M + 'model-consumer-inventory-and-retirement-gates', M + 'receipt-serving-slo-project', M + 'receipt-model-incident-drill-project'],
    },
]

crosslinks = [
    (M + 'run-manifest-and-artifact-lineage', M + 'model-card-scope-and-limitation-register'),
    (M + 'prediction-outcome-join-and-maturity', M + 'slice-quality-gates-and-uncertainty'),
    (M + 'trusted-model-promotion-project', M + 'receipt-model-card-review-project'),
    (M + 'feature-schema-evolution-and-consumers', M + 'inference-request-response-contracts'),
    (M + 'ml-test-pyramid-and-data-fixtures', M + 'inference-client-migration-and-contract-tests'),
    (M + 'receipt-serving-slo-project', M + 'receipt-inference-api-migration-project'),
]

if __name__ == '__main__':
    publish(lessons, (G, A), crosslinks,
            'aitrove-mlops-governance-api-import-20261006.json', 6136,
            subject='mlops', hub_path=M + 'mlops-tutorial')
