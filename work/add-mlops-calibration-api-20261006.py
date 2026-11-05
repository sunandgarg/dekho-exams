"""Add probability-calibration operations and inference API exposure lessons."""
from de_batch_publisher import publish

M = 'mlops/'
CAL = 'Calibration monitoring and policy requalification'
API = 'Prediction API exposure and query-abuse controls'
lessons = [
    {
        'path': M + 'calibration-ledger-and-matured-outcome-windows',
        'title': 'Calibration monitoring: pair score bands with matured outcomes',
        'module': CAL, 'project': False,
        'summary': 'Calibration measures whether predicted probabilities match observed event rates in comparable, mature outcome cohorts.',
        'sections': [
            ('Record the probability contract', 'A claims model predicts the chance that a submitted repair claim needs manual inspection. Store raw score, calibrated probability, calibrator revision, model revision, decision threshold, event time, cohort and eventual label join key. A model can rank claims well while assigning probabilities that are too high or low. Compare observed event rates with mean predicted probabilities within score bands, and publish the band sample size. [[mlops/score-threshold-policy-and-change-control|Threshold policy]] uses those probabilities but answers a different decision question.'),
            ('Wait for labels to mature', 'A claim may be inspected days after its score was issued. Exclude recent predictions whose outcome window has not closed; otherwise a quiet-looking band may simply lack labels. Record both scored count and mature joined count by band and cohort. Late labels and corrected outcomes should update a versioned ledger, not silently replace an old report. [[mlops/prediction-outcome-join-and-maturity|Outcome joins]] define maturity and [[mlops/label-corrections-and-evaluation-ledger|label corrections]] keep changes traceable.'),
            ('Watch selection bias', 'Claims routed to manual review are more likely to receive confirmed labels than auto-cleared claims. Calibration measured only on reviewed claims does not represent all scored claims. Use an independent audit sample, or report the reviewed population honestly and avoid a site-wide calibration claim. Split by acquisition channel, repair category and score band, then show uncertainty where counts are small. [[mlops/selective-label-observation-and-audit-sampling|Audit sampling]] supplies a second observation frame.'),
            ('Trigger investigation, not automatic retuning', 'A band whose observed rate drifts away from its mean prediction may reflect prevalence change, data quality, label latency or a broken scoring pipeline. Check calibration error over comparable windows with minimum sample counts and a stable label definition. Investigate cohort composition before refitting. A new calibrator must pass its own holdout and policy review. [[mlops/calibrator-revision-and-threshold-requalification|Calibrator requalification]] governs the change rather than letting a dashboard rewrite production scores.'),
        ],
        'code': '''def band_calibration(records, lower, upper, minimum_mature):
    eligible = [record for record in records if record["mature"]
                and lower <= record["probability"] < upper]
    if len(eligible) < minimum_mature:
        return {"state": "insufficient", "count": len(eligible)}
    predicted = sum(row["probability"] for row in eligible) / len(eligible)
    observed = sum(row["outcome"] for row in eligible) / len(eligible)
    return {"state": "measured", "count": len(eligible),
            "predicted": predicted, "observed": observed}

claims = [{"probability": 0.42, "outcome": 1, "mature": True},
          {"probability": 0.48, "outcome": 0, "mature": True},
          {"probability": 0.46, "outcome": 1, "mature": False}]
report = band_calibration(claims, 0.4, 0.5, 2)
assert report["state"] == "measured" and report["count"] == 2
assert report["observed"] == 0.5
''',
        'cost': 'One band scan is O(n) time and O(n) temporary space for n records; streaming sums can reduce extra space to O(1). A full monitoring job should compute all bands in one pass. Audit labeling has an operational cost, but a reviewed-only sample may make an inexpensive report misleading.',
        'mistakes': ['Treating ranked scores as calibrated probabilities without checking outcomes.', 'Counting immature predictions as negative outcomes.', 'Reporting calibration from the review queue as if it covered all claims.', 'Refitting on the same holdout later used to approve the calibrator.'],
        'related': [M + 'calibrator-revision-and-threshold-requalification', M + 'claims-calibration-monitoring-project', M + 'prediction-outcome-join-and-maturity', M + 'selective-label-observation-and-audit-sampling', M + 'score-threshold-policy-and-change-control'],
    },
    {
        'path': M + 'calibrator-revision-and-threshold-requalification',
        'title': 'Calibrator releases: requalify thresholds after score remapping',
        'module': CAL, 'project': False,
        'summary': 'A probability remapping is a new decision component; it can change who crosses an unchanged numeric threshold.',
        'sections': [
            ('Treat the calibrator as a release artifact', 'A claims classifier is unchanged, but a newly fitted calibrator maps raw score 0.47 to probability 0.63 instead of 0.51. If manual inspection starts at 0.60, that claim changes route. Version the calibrator, training labels, fit window, base model and score transformation, then bind them to the threshold policy. Do not roll out a new calibrator as a dashboard-only change. [[mlops/run-manifest-and-artifact-lineage|Artifact lineage]] must identify the exact mapping that produced every decision.'),
            ('Fit without contaminated evidence', 'Fit calibration on predictions from observations not used to fit the base model, or use a cross-validated out-of-fold design. Reserve a later untouched evaluation set for the final check. Repeated attempts to choose a mapping on the final set make its estimate optimistic. Time and entity splits still matter: two claims from one repair center can share process artifacts. [[mlops/snapshot-split-and-environment-replay|Snapshot and split replay]] makes the fit reproducible.'),
            ('Requalify both probability and workload', 'Compare reliability bands, a proper probability score, decision precision and recall, and expected manual-review volume on the same eligible frame. Inspect channel and repair-type slices; a better global calibration curve can coexist with a harmful routing change for one segment. Put a capacity limit on new reviews before expanding traffic. [[mlops/slice-quality-gates-and-uncertainty|Slice gates]] and [[mlops/score-threshold-policy-and-change-control|threshold change control]] should approve the combined base-model, calibrator and policy tuple.'),
            ('Ship a reversible tuple', 'Shadow both tuples, then canary the new one while retaining the old mapping and threshold. Log the tuple revision with each score and route. If review volume breaches the agreed limit or mature outcomes deteriorate, restore the prior tuple rather than patching the threshold blindly. [[mlops/promotion-attestation-and-reversible-pointer|The reversible pointer]] allows a single rollback, and [[mlops/claims-calibration-monitoring-project|the project]] catches a mapping that looks better overall but overwhelms reviewers.'),
        ],
        'code': '''def calibrator_promotion(report, limits):
    if report["evaluation_overlap"]:
        return "hold:data-overlap"
    if report["max_slice_gap"] > limits["max_slice_gap"]:
        return "hold:slice-calibration"
    if report["review_volume"] > limits["review_capacity"]:
        return "hold:review-capacity"
    if report["brier_score"] > limits["brier_score"]:
        return "hold:probability-quality"
    return "canary:bound-tuple"

limits = {"max_slice_gap": 0.08, "review_capacity": 470,
          "brier_score": 0.19}
report = {"evaluation_overlap": False, "max_slice_gap": 0.04,
          "review_volume": 392, "brier_score": 0.16}
assert calibrator_promotion(report, limits) == "canary:bound-tuple"
assert calibrator_promotion({**report, "review_volume": 514}, limits) == \
       "hold:review-capacity"
''',
        'cost': 'The aggregate gate is O(1) time and space. Fitting a calibrator adds a training pass and evaluation cost; shadowing two tuples doubles scoring work for sampled requests. Review capacity is a hard operating constraint because a remapping can move many claims across a threshold without changing model rank order.',
        'mistakes': ['Changing a calibrator without versioning the decision tuple.', 'Fitting the mapping on base-model training predictions and claiming independent calibration.', 'Checking probability error but ignoring manual-review volume.', 'Adjusting the threshold after canary without a separate recorded policy revision.'],
        'related': [M + 'calibration-ledger-and-matured-outcome-windows', M + 'claims-calibration-monitoring-project', M + 'run-manifest-and-artifact-lineage', M + 'score-threshold-policy-and-change-control', M + 'promotion-attestation-and-reversible-pointer'],
    },
    {
        'path': M + 'claims-calibration-monitoring-project',
        'title': 'Project: monitor claims probabilities and release a new calibrator',
        'module': CAL, 'project': True,
        'summary': 'Build a mature-label report, spot review-selection bias and test a calibrator with a bounded review queue.',
        'sections': [
            ('Assemble the scoring ledger', 'The service scores repair claims and routes high-risk cases to inspectors. Capture model, calibrator and threshold revisions with each claim ID, event time, probability, route and acquisition channel. Join only outcomes whose inspection window has closed. Report how many scored claims were eligible, how many were labeled and how many are still pending. [[mlops/calibration-ledger-and-matured-outcome-windows|The monitoring ledger]] keeps incomplete labels out of the denominator.'),
            ('Expose the biased sample', 'Most inspected claims have outcomes, while auto-cleared claims rarely do. A naive calibration table uses only inspected claims and claims the middle-score band is underconfident. Add an independently selected audit sample of auto-cleared claims and report the two frames separately. One small channel has too few mature labels for a stable band estimate; mark it insufficient instead of drawing a confident line through it. Review corrected labels in a versioned record.'),
            ('Test a candidate mapping', 'Fit a candidate calibrator on a separate earlier period. Hold the latest evaluation frame untouched until the mapping is fixed. Compare probability error and band gaps, then rerun the routing threshold on both candidate and incumbent probabilities. The candidate improves global probability error but would send 514 claims per day to a team that can handle 470. Hold it. [[mlops/calibrator-revision-and-threshold-requalification|The release gate]] requires both probability quality and operating capacity.'),
            ('Deliver a decision record', 'Report score-band counts, maturity, audit coverage, slice gaps, review-volume forecast, fit and evaluation windows, and the exact decision tuple. If another candidate passes, shadow it and canary with a rollback pointer. Recheck mature outcomes after deployment; do not treat early review yield as the final outcome. Link the handoff to [[mlops/prediction-outcome-join-and-maturity|outcome maturity]] and [[mlops/score-threshold-policy-and-change-control|threshold policy]].'),
        ],
        'code': '''def claims_release(candidate, prior, daily_capacity):
    if candidate["fit_window"] == candidate["evaluation_window"]:
        return "hold:overlap"
    if candidate["daily_review_count"] > daily_capacity:
        return "hold:capacity"
    if candidate["mature_brier"] >= prior["mature_brier"]:
        return "hold:no-quality-gain"
    return "canary"

prior = {"mature_brier": 0.18}
candidate = {"fit_window": "weeks-47-54", "evaluation_window": "weeks-55-58",
             "daily_review_count": 514, "mature_brier": 0.16}
assert claims_release(candidate, prior, 470) == "hold:capacity"
assert claims_release({**candidate, "daily_review_count": 392},
                      prior, 470) == "canary"
''',
        'cost': 'The release check is O(1). The ledger join and band aggregation scale linearly with scored claims if indexed by claim ID; retrospective audit labeling and parallel shadow scoring add cost. Capacity is measured in reviewed claims per day, not merely CPU time, so a faster scorer can still create an unusable release.',
        'mistakes': ['Marking pending claims as clean to fill calibration bins.', 'Using only inspected claims to describe every scored claim.', 'Choosing a calibrator on the protected evaluation period.', 'Promoting a better probability score despite exceeding reviewer capacity.'],
        'related': [M + 'calibration-ledger-and-matured-outcome-windows', M + 'calibrator-revision-and-threshold-requalification', M + 'prediction-outcome-join-and-maturity', M + 'selective-label-observation-and-audit-sampling', M + 'score-threshold-policy-and-change-control'],
    },
    {
        'path': M + 'prediction-api-output-contract-and-exposure-budget',
        'title': 'Prediction API exposure: define what a client may learn from scores',
        'module': API, 'project': False,
        'summary': 'A prediction endpoint exposes information through its outputs; response detail and query access need an explicit contract.',
        'sections': [
            ('Inventory the output surface', 'A supplier-risk endpoint receives account and transaction features and returns a route. Some clients ask for the full probability vector, intermediate features and explanation weights, even though they only need approve, review or decline. Document each client’s necessary response fields, model revision visibility, error behavior and retention. Full scores can help legitimate decisions, but they also reveal more about the model’s behavior to anyone able to send many queries. [[mlops/inference-request-response-contracts|Request-response contracts]] provide the base schema.'),
            ('Set a per-client query budget', 'Authenticate the caller, cap requests over a sliding operational window and track distinct input patterns as well as raw request count. A retry of the same request ID should return the same result without consuming a fresh inference budget. Watch high-volume boundary probing and unusually broad feature sweeps. Those signals justify investigation, not a conclusive model-extraction verdict. [[mlops/idempotent-inference-retries-and-quotas|Idempotent quotas]] separate client retries from fresh queries.'),
            ('Return only needed precision', 'A workflow that consumes a three-state route should receive the route and an explanation category, not a many-decimal probability or hidden feature vector. Other clients may need calibrated probabilities; grant that through a scoped contract and log its usage. Rounding alone does not remove information risk, and output reduction can impair an approved downstream task. Review utility and exposure together. [[mlops/calibrator-revision-and-threshold-requalification|Calibrator revisions]] also change the meaning of a disclosed score.'),
            ('Keep monitoring proportionate', 'Store pseudonymous client ID, request ID, feature-family digest, response type, model revision and time, subject to retention limits. Avoid storing raw sensitive feature values merely to investigate probing. Escalate unusual behavior to a case with an owner and expiry. An endpoint can be copied or imitated without any obvious spike, so controls reduce exposure rather than guarantee secrecy. [[mlops/prediction-api-query-patterns-and-case-review|Query-pattern review]] provides a reproducible decision path.'),
        ],
        'code': '''def response_for_scope(decision, scope):
    public = {"route": decision["route"], "reason": decision["reason"]}
    if scope == "risk-probability-reader":
        return {**public, "probability": decision["probability"]}
    return public

result = {"route": "review", "reason": "unusual-volume",
          "probability": 0.4731, "hidden_features": [3, 8]}
assert "probability" not in response_for_scope(result, "route-reader")
assert response_for_scope(result, "risk-probability-reader")["probability"] \
       == 0.4731
assert "hidden_features" not in response_for_scope(result,
                                                  "risk-probability-reader")
''',
        'cost': 'Response selection is O(1) time and space for a fixed schema. Per-client window tracking requires O(a) state for active clients and periodic expiry. Reducing output detail is cheap, but added authentication, quota storage and case review have operational cost. No output policy alone prevents copying behavior from repeated queries.',
        'mistakes': ['Returning internal feature vectors because one client needs a route.', 'Treating rounding as a complete privacy or extraction defense.', 'Counting idempotent retries as new independent queries.', 'Declaring any high-volume client malicious without service context.'],
        'related': [M + 'prediction-api-query-patterns-and-case-review', M + 'supplier-risk-api-exposure-project', M + 'inference-request-response-contracts', M + 'idempotent-inference-retries-and-quotas', M + 'calibrator-revision-and-threshold-requalification'],
    },
    {
        'path': M + 'prediction-api-query-patterns-and-case-review',
        'title': 'Prediction API query review: distinguish probing from legitimate bursts',
        'module': API, 'project': False,
        'summary': 'Query-pattern alerts need context, an investigation trail and reversible controls before they affect a client.',
        'sections': [
            ('Look for structure in a bounded window', 'A supplier-risk client sends hundreds of similar requests with one feature changed at a time. Another client legitimately replays a nightly batch after an outage. Count distinct request IDs, feature-family digests, response scopes, route transitions and per-minute rate under one authenticated identity. Compare against the client’s registered workload and prior windows. Exact retries should collapse under the same idempotency key. [[mlops/prediction-api-output-contract-and-exposure-budget|The exposure contract]] defines which answers the client should receive.'),
            ('Make alerts specific and reversible', 'A sudden surge with many one-field variations can open a case. Step down to a lower request rate or route-only response when the client contract permits it; keep a clear expiry and emergency exception for critical workflows. Do not silently change numeric results for the same request, and do not block a known recovery batch solely because it is large. [[mlops/inference-evasion-monitoring-and-containment|Evasion containment]] is a neighboring workflow but asks whether inputs manipulate decisions, not whether outputs reveal model behavior.'),
            ('Investigate with limited records', 'Preserve pseudonymous caller ID, rule revision, request count, distinct-input ratio, response scope and sampled request IDs. An investigator can ask the client about a known batch replay and compare timing with deployment or outage records. Record the conclusion as confirmed misuse, explained burst or unresolved. Avoid inferring theft of weights from a pattern alone. [[mlops/incident-triage-and-evidence-timeline|Incident evidence]] keeps who decided what and when.'),
            ('Measure the controls themselves', 'Track rate-limit errors, blocked legitimate calls, investigation precision, case age and client appeal outcomes. If a rule blocks many ordinary batch jobs, reduce its scope or change the baseline, then version the rule. Keep model revisions and probability scopes in the case because a release can change query behavior without a caller changing intent. [[mlops/supplier-risk-api-exposure-project|The project]] exercises both a probing-like sequence and a planned replay.'),
        ],
        'code': '''def query_case(window, client_plan):
    if window["unique_requests"] <= client_plan["planned_requests"]:
        return "observe:within-plan"
    if window["one_field_variations"] < client_plan["variation_alert"]:
        return "review:unexpected-volume"
    if window["response_scope"] != client_plan["approved_scope"]:
        return "hold:scope-mismatch"
    return "review:structured-query-pattern"

plan = {"planned_requests": 82, "variation_alert": 47,
        "approved_scope": "route-reader"}
window = {"unique_requests": 119, "one_field_variations": 63,
          "response_scope": "route-reader"}
assert query_case(window, plan) == "review:structured-query-pattern"
assert query_case({**window, "unique_requests": 72}, plan) == \
       "observe:within-plan"
''',
        'cost': 'The aggregate rule is O(1) time and space; producing its window features is O(n) time over n requests and needs bounded per-client state. Review time and false-positive client disruption are material. Sampled evidence lowers storage but may miss a particular query sequence, so the sampling policy belongs in the case packet.',
        'mistakes': ['Equating high request volume with confirmed extraction.', 'Ignoring a client’s documented outage replay.', 'Changing response values instead of applying a visible contract or rate policy.', 'Leaving a temporary rate cap active without expiry or owner.'],
        'related': [M + 'prediction-api-output-contract-and-exposure-budget', M + 'supplier-risk-api-exposure-project', M + 'incident-triage-and-evidence-timeline', M + 'idempotent-inference-retries-and-quotas', M + 'inference-evasion-monitoring-and-containment'],
    },
    {
        'path': M + 'supplier-risk-api-exposure-project',
        'title': 'Project: audit a supplier-risk prediction API after a query surge',
        'module': API, 'project': True,
        'summary': 'Separate a planned client replay from structured probing, then apply scoped, reversible response controls.',
        'sections': [
            ('Map two client contracts', 'A purchasing system needs only approve, review or decline plus a reason category. An internal risk desk is approved for calibrated probabilities. Record both scopes, authenticated client IDs, request budgets, idempotency rules and retention period. A new endpoint accidentally exposes full probability precision and a hidden feature vector to the purchasing client. Fix the response contract before interpreting any observed traffic. [[mlops/prediction-api-output-contract-and-exposure-budget|Output scope]] is the first control.'),
            ('Classify the surge', 'Client A sends 119 distinct requests in a short window, with 63 one-field variations and repeated decision-boundary crossings. Client B sends 390 requests after a documented overnight outage, but most are exact retries with stable request IDs. Collapse retries, compare each client with its registered workload and open a review case for A. Do not call A malicious yet, and do not block B’s approved replay. [[mlops/prediction-api-query-patterns-and-case-review|Query review]] provides the structured evidence packet.'),
            ('Apply and test limited controls', 'Remove unauthorized fields from the purchasing response, cap A’s fresh requests temporarily and provide an escalation route. Preserve the same route for the same accepted request ID. Keep B on its recovery allowance. Re-run a legitimate sample from both clients and verify that the risk desk still receives the probability its workflow needs. If A’s case is explained by a sanctioned test, expire the cap and record the conclusion.'),
            ('Report outcome and limits', 'Deliver a case packet with client scope, unique-versus-retry counts, response-field exposure, variation signal, rule revision, human decision, hold expiry and service impact. State clearly that the logs show a query pattern, not proof that a model was copied. Track future misuse reports and [[mlops/incident-triage-and-evidence-timeline|incident decisions]], and connect API changes to [[mlops/inference-request-response-contracts|request-response contract tests]].'),
        ],
        'code': '''def api_client_action(client, scope, fresh_requests, planned_limit):
    if scope not in client["approved_scopes"]:
        return "reject:scope"
    if fresh_requests > planned_limit:
        return "review:temporary-rate-cap"
    return "serve:approved-response"

purchasing = {"approved_scopes": {"route-reader"}}
assert api_client_action(purchasing, "risk-probability-reader", 47, 82) \
       == "reject:scope"
assert api_client_action(purchasing, "route-reader", 119, 82) \
       == "review:temporary-rate-cap"
assert api_client_action(purchasing, "route-reader", 72, 82) \
       == "serve:approved-response"
''',
        'cost': 'The contract decision is O(1) expected time and space for a small scope set. Window aggregation scales with fresh request volume and uses per-client expiring state. An overly strict cap can delay legitimate purchasing, while overexposed probabilities reveal unnecessary model behavior; measure both service errors and exposure reductions.',
        'mistakes': ['Confusing exact retries with new boundary probes.', 'Removing an approved probability field from the internal risk desk.', 'Claiming a copied model from traffic patterns alone.', 'Keeping a temporary client cap after the investigation closes.'],
        'related': [M + 'prediction-api-output-contract-and-exposure-budget', M + 'prediction-api-query-patterns-and-case-review', M + 'inference-request-response-contracts', M + 'idempotent-inference-retries-and-quotas', M + 'incident-triage-and-evidence-timeline'],
    },
]

crosslinks = [
    (M + 'prediction-outcome-join-and-maturity', M + 'calibration-ledger-and-matured-outcome-windows'),
    (M + 'score-threshold-policy-and-change-control', M + 'calibrator-revision-and-threshold-requalification'),
    (M + 'selective-label-observation-and-audit-sampling', M + 'claims-calibration-monitoring-project'),
    (M + 'inference-request-response-contracts', M + 'prediction-api-output-contract-and-exposure-budget'),
    (M + 'idempotent-inference-retries-and-quotas', M + 'prediction-api-query-patterns-and-case-review'),
    (M + 'incident-triage-and-evidence-timeline', M + 'supplier-risk-api-exposure-project'),
]

if __name__ == '__main__':
    publish(lessons, [CAL, API], crosslinks,
            'aitrove-mlops-calibration-api-import-20261006.json', 6214,
            subject='mlops', hub_path=M + 'mlops-tutorial')
