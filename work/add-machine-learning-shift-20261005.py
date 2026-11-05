"""Add original Machine Learning lessons on distribution shift and release review."""
from ml_fixture_writer_20261005 import publish_batch

lessons = []


def add(slug, title, summary, sections, code, cost, mistakes, related):
    lessons.append(dict(path='machine-learning/' + slug, title=title,
                        summary=summary, sections=sections, code=code,
                        cost=cost, mistakes=mistakes, related=related))


add('covariate-shift-and-support-overlap',
    'Covariate shift and support overlap',
    'Input mix can change while the outcome mechanism remains similar, but adapting to a new mix requires training support where deployment cases occur.', [
    ('Start with the actual serving population', 'A shipment classifier was trained mostly on low-backlog intakes. A new depot contributes more high-backlog cases. Compare the feature distribution at the prediction timestamp, not a later enriched record. A changed marginal input distribution is evidence of input shift; it does not establish that the relation between input and outcome stayed fixed. [[machine-learning/prediction-time-feature-availability|Feature availability]] determines which columns can even be compared.'),
    ('Make overlap visible', 'Bucket a decision-relevant variable and count training and current cases in each bucket. The code flags a bucket that appears in current traffic but has no training support. That is a coverage failure: reweighting old rows cannot teach the model how outcomes behave in a region with no examples. Multivariate overlap can fail even when every single feature has a familiar range, so inspect important combinations and distances as well. [[machine-learning/nearest-neighbor-distance-and-local-support|Local support]] is a complementary row-level test.'),
    ('Do not confuse drift with damage', 'A large seasonal mix change can leave decisions sound; a small measurement change in one decisive feature can break them. Pair input counts with mature future error, calibration, review load and the existing baseline. If outcomes are delayed, document the gap between current input evidence and later performance evidence. [[machine-learning/feature-drift-and-delayed-label-monitoring|Delayed-label monitoring]] defines the clock.'),
    ('Define a response for missing support', 'Mark unsupported cases for a safe fallback or review, and collect labels under an explicit sampling plan. A model retrained on the same sparse region does not acquire new evidence. If a new depot uses a different target definition, that is more than covariate shift; reconcile the labels before pooling. [[machine-learning/group-error-gaps-and-policy-audit|The group audit]] checks whether one site bears most of the failures.'),
    ('Keep the window honest', 'Compare like-for-like intake windows and account for known schedule cycles. Log the reference cohort, current cohort, bucket boundaries, missing-value rules and the model version. A threshold chosen after inspecting a bad production week is a development decision and needs a fresh evaluation window. [[machine-learning/distribution-shift-response-project|The response project]] turns the diagnostic into a release decision.')],
    '''training_backlog = [1, 2, 2, 3, 4, 5, 6, 7]
current_backlog = [2, 4, 6, 9, 10, 11]

def backlog_band(queue_length):
    if queue_length < 4:
        return "low"
    if queue_length < 8:
        return "middle"
    return "high"

def band_counts(values):
    counts = {band: 0 for band in ("low", "middle", "high")}
    for queue_length in values:
        counts[backlog_band(queue_length)] += 1
    return counts

training_counts = band_counts(training_backlog)
current_counts = band_counts(current_backlog)
unsupported = [band for band, current_count in current_counts.items()
               if current_count and training_counts[band] == 0]
assert training_counts == {"low": 4, "middle": 4, "high": 0}
assert current_counts == {"low": 1, "middle": 2, "high": 3}
assert unsupported == ["high"]''',
    'For N reference and M current rows, counting fixed bands costs O(N + M) time and O(B) memory for B bands. Multivariate support checks cost more and can become unreliable in sparse high-dimensional spaces; the cost of obtaining representative labeled cases is often the true constraint.',
    ['Do not infer stable outcomes from stable or changing feature histograms alone.', 'Do not extrapolate an importance weight into a bucket with zero training support.', 'Do not compare post-outcome features with prediction-time features.'],
    ['machine-learning/importance-weighted-risk-under-shift','machine-learning/concept-change-with-mature-outcomes','machine-learning/feature-drift-and-delayed-label-monitoring','machine-learning/distribution-shift-response-project'])


add('importance-weighted-risk-under-shift',
    'Importance-weighted risk under covariate shift',
    'A target-to-training density ratio can reweight historical evaluation losses toward a new input mix when the conditional outcome mechanism is stable and support overlaps.', [
    ('Write the assumption before the weight', 'Suppose the mix of depot backlog bands changes, but the chance of a missed handoff within a band remains approximately the same. Historical evaluation losses can be weighted by target-band frequency divided by historical-band frequency. This estimates risk for the target mix only under that stability assumption and adequate overlap. [[machine-learning/covariate-shift-and-support-overlap|The overlap guide]] checks the necessary support condition first.'),
    ('Use evaluation rows, not training fit', 'The code uses already-issued predictions and mature outcomes from a held-out historical cohort. It estimates a weighted error rate using a simple band ratio supplied from separate distribution counts. It does not train a new classifier, and the tiny frequencies are illustrative. In an application, estimate ratios without leaking test outcomes, validate the conditional-stability premise and compare with newly labeled target cases when they mature. [[machine-learning/group-and-time-validation|The split guide]] protects those roles.'),
    ('Expose weight concentration', 'A few high-weight records can dominate the estimate. Report the largest weights and effective sample size, the squared sum of weights divided into the square of their sum. A small effective sample size means the nominal row count overstates evidence. Clip or regularize ratios only with a declared rule and report the bias this may introduce. [[machine-learning/paired-bootstrap-model-gain-intervals|Paired uncertainty]] is helpful only if the resampling unit and weights match the data design.'),
    ('Know what weighting cannot repair', 'If a new depot changes scanner behavior, the probability of a miss at a given backlog can change. Weighting the old mix then transports the wrong conditional relationship. If a target band has zero source support, the ratio is undefined; the code raises. Reweighting also does not correct a changed label definition, late features or selective outcome recording. [[machine-learning/concept-change-with-mature-outcomes|Concept checks]] require labels.'),
    ('Use the estimate as one decision input', 'Compare weighted and unweighted risk with the same outcome maturity rule. Report interval estimates or a sensitivity range for plausible ratio error and inspect group-level harm. A weighted metric can guide where to gather evidence, but should not silently replace a future-period holdout. [[machine-learning/distribution-shift-response-project|The response project]] requires that final test.')],
    '''# Historical validation cases: backlog band, issued alert, mature outcome.
validation_cases = [
    ("low", 0, 0), ("low", 0, 0),
    ("middle", 1, 1), ("middle", 0, 1),
    ("high", 1, 1), ("high", 1, 0),
]
source_share = {"low": 2 / 6, "middle": 2 / 6, "high": 2 / 6}
target_share = {"low": 1 / 6, "middle": 2 / 6, "high": 3 / 6}

def weighted_error(cases, historical_share, deployment_share):
    weights = []
    weighted_misses = 0.0
    for band, issued_alert, outcome in cases:
        if historical_share.get(band, 0) <= 0:
            raise ValueError("target band lacks historical support")
        weight = deployment_share[band] / historical_share[band]
        weights.append(weight)
        weighted_misses += weight * (issued_alert != outcome)
    weight_total = sum(weights)
    effective_size = weight_total ** 2 / sum(weight ** 2 for weight in weights)
    return weighted_misses / weight_total, effective_size

risk, effective_size = weighted_error(validation_cases, source_share, target_share)
assert risk == 5 / 12
assert effective_size < len(validation_cases)''',
    'With precomputed band ratios, N weighted losses cost O(N) time and O(1) running state; the teaching code retains O(N) weights for clarity. Estimating high-dimensional density ratios is harder and unstable near weak overlap. More labeled target cases can be worth more than a complicated weighting scheme.',
    ['Do not describe weighted risk as unbiased when the conditional outcome relation changed.', 'Do not hide a small effective sample size behind the original row count.', 'Do not estimate ratios using target outcomes from the final evaluation period.'],
    ['machine-learning/covariate-shift-and-support-overlap','machine-learning/concept-change-with-mature-outcomes','machine-learning/group-and-time-validation','machine-learning/distribution-shift-response-project'])


add('concept-change-with-mature-outcomes',
    'Concept change with mature outcomes',
    'To test whether a model has lost its relation to the outcome, compare errors on mature labels within comparable input slices and time windows.', [
    ('Separate a changing mix from a changing relation', 'A depot may receive more high-backlog shipments without a change in within-band miss rates. That is an input-mix problem. If the miss rate within a comparable band rises after a routing rule changes, the input-to-outcome relation may have changed. Neither pattern is proven by six rows; the example is a transparent diagnostic. [[machine-learning/covariate-shift-and-support-overlap|Support overlap]] is the first check.'),
    ('Wait for eligible labels', 'An unresolved shipment has no final handoff outcome yet. Comparing only fast-resolving cases can produce a false improvement. Define a maturity delay and a fixed cutoff before calculating error. Keep the original issued probability and threshold alongside the later outcome. [[machine-learning/feature-drift-and-delayed-label-monitoring|The label-clock lesson]] treats unresolved cases as missing evidence, not negatives.'),
    ('Compare within a declared slice', 'The code contrasts missed-handoff prevalence and alert error in the same middle-backlog band across two periods. Prevalence can change because of an unrecorded cause; observed differences justify investigation, not a causal explanation. Include case counts, uncertainty and other sites. A new outcome coding rule or a changed intervention can mimic model decay. [[machine-learning/group-error-gaps-and-policy-audit|The group audit]] asks which population carries the change.'),
    ('Check prediction and action feedback', 'If the alert causes staff to rescue a shipment, the observed miss rate among alerted cases is partly an effect of the policy. A naive comparison of alerted and unalerted outcomes cannot recover what would have happened without the alert. Preserve action logs and, if a policy experiment is justified, design it through governance rather than treating an observational chart as proof. [[causal-inference/causal-inference-tutorial|Causal inference]] supplies the separate question.'),
    ('Choose a bounded response', 'Investigate instrumentation, target definition and route operations before retraining. A fixed model can be perfectly implemented yet wrong for the new process. Test candidate changes with rolling-origin evaluation and an untouched later period; keep the former model available for rollback. [[machine-learning/rolling-origin-retraining-with-embargo|The backtest guide]] describes the clock.')],
    '''# Period, backlog band, original issued alert, mature missed-handoff outcome.
audited_cases = [
    ("earlier", "middle", 0, 0), ("earlier", "middle", 1, 1),
    ("earlier", "middle", 0, 0), ("earlier", "middle", 1, 1),
    ("later", "middle", 0, 1), ("later", "middle", 1, 1),
    ("later", "middle", 0, 1), ("later", "middle", 1, 1),
]

def period_audit(rows, band):
    grouped = {}
    for period, observed_band, alert, outcome in rows:
        if observed_band != band:
            continue
        counts = grouped.setdefault(period, {"support": 0, "outcomes": 0, "errors": 0})
        counts["support"] += 1
        counts["outcomes"] += outcome
        counts["errors"] += alert != outcome
    return {period: {**counts,
                     "event_rate": counts["outcomes"] / counts["support"],
                     "alert_error": counts["errors"] / counts["support"]}
            for period, counts in grouped.items()}

report = period_audit(audited_cases, "middle")
assert report["earlier"]["event_rate"] == 0.5
assert report["later"]["event_rate"] == 1.0
assert report["later"]["alert_error"] == 0.5''',
    'A period-by-slice audit over N mature cases takes O(N) time and O(P times S) summary memory for P periods and S slices. Outcome delay, label audits and policy feedback complicate interpretation far more than computing the rates.',
    ['Do not call unresolved outcomes negative.', 'Do not treat a within-slice change as proof of a specific cause.', 'Do not retrain directly on outcomes altered by the existing intervention without assessing feedback.'],
    ['machine-learning/covariate-shift-and-support-overlap','machine-learning/rolling-origin-retraining-with-embargo','machine-learning/feature-drift-and-delayed-label-monitoring','machine-learning/distribution-shift-response-project'])


add('rolling-origin-retraining-with-embargo',
    'Rolling-origin retraining with an outcome embargo',
    'A rolling-origin backtest trains on data available at each historical decision date and scores later cases while excluding outcomes that had not matured.', [
    ('Treat each origin like a real deployment', 'For a model used on Monday, only rows and labels available by Monday can train it. The next origin moves forward and repeats that decision. This tests the proposed retraining cadence against changing operations, unlike a random split that mixes seasons. [[machine-learning/group-and-time-validation|Group and time validation]] also keeps repeat shipments and shared incidents together.'),
    ('Embargo recent labels', 'If handoff outcomes need two days to settle, a Friday training snapshot cannot include Thursday labels even though the intake row exists. The code selects only cases whose label-ready timestamp precedes the origin and scores cases in the following window. The gap is a label-availability rule, not a cosmetic number of calendar days. Preserve source event time, arrival time and correction history. [[machine-learning/feature-drift-and-delayed-label-monitoring|Delayed labels]] describes why maturity matters.'),
    ('Refit the whole pipeline', 'Each origin must refit imputation, encoding, selection, calibration and the estimator using that origin’s eligible data. Reusing transformations fitted on the full table leaks future distribution information. A validation threshold chosen from all origins may overstate performance, so reserve a later untouched period for final comparison. [[machine-learning/leakage-safe-preprocessing-pipeline|Pipeline isolation]] covers the same boundary inside a fold.'),
    ('Compare policies, not just scores', 'Evaluate a fixed model, a scheduled retrain and a drift-triggered retrain with the same future decision windows and costs. A new model may improve average error while increasing false negatives at one depot or expanding the manual-review queue. Report the cadence, training size, outcome maturity, calibration and rollback behavior. [[machine-learning/selective-prediction-and-review-capacity|Review capacity]] is part of the policy.'),
    ('Do not let late data rewrite the past', 'Backfills are useful for today’s training but were not visible to a historical decision. Backtesting from a current corrected table requires availability timestamps or archived snapshots. If those records are missing, state that the backtest is approximate. [[machine-learning/distribution-shift-response-project|The release project]] requires a documented data clock before claiming a gain.')],
    '''# Intake day, label-ready day, alert outcome. Day numbers represent one archive.
cases = [(1, 3, 0), (2, 4, 1), (3, 6, 0), (4, 6, 1),
         (5, 8, 0), (6, 9, 1), (7, 10, 1), (8, 12, 0),
         (9, 12, 0), (10, 13, 1)]
origins = (6, 9)
forecast_horizon = 2

def rolling_windows(records, decision_days, horizon):
    windows = []
    for origin in decision_days:
        train = [row for row in records if row[0] < origin and row[1] <= origin]
        score = [row for row in records if origin <= row[0] < origin + horizon]
        if not train or not score:
            raise ValueError("origin lacks training or scoring rows")
        windows.append((origin, train, score))
    return windows

windows = rolling_windows(cases, origins, forecast_horizon)
assert [len(train) for _, train, _ in windows] == [4, 6]
assert [len(score) for _, _, score in windows] == [2, 2]''',
    'If each of R origins scans N archived rows, the simple backtest selector takes O(RN) time and O(N) memory per origin. Indexed timestamp selection can reduce repeated scans, while R complete model and preprocessing fits usually dominate compute. Archive availability timestamps if the result must support a release.',
    ['Do not admit a label that became ready after the historical origin.', 'Do not preprocess once on the full table before replaying origins.', 'Do not use today’s corrected row as if it were visible in the past.'],
    ['machine-learning/concept-change-with-mature-outcomes','machine-learning/leakage-safe-preprocessing-pipeline','machine-learning/champion-challenger-shadow-comparison','machine-learning/distribution-shift-response-project'])


add('champion-challenger-shadow-comparison',
    'Champion–challenger shadow comparison',
    'A challenger can score the same incoming cases as the live model without changing decisions, allowing paired comparison when outcomes later mature.', [
    ('Keep the live action fixed', 'A challenger predicts missed handoffs beside the current champion, but only the champion’s alert drives dispatch. Log both scores, versions, input snapshot, champion action and later mature outcome under one case ID. This avoids quietly changing a production policy during measurement. The shadow outcome still reflects the champion’s intervention, so it may not equal the outcome the challenger policy would have caused. [[machine-learning/concept-change-with-mature-outcomes|Policy feedback]] explains the limitation.'),
    ('Pair each comparison', 'Compare loss differences case by case; the code reports the mean challenger-minus-champion Brier loss on the same four cases. This removes one source of variation from comparing two unrelated cohorts. It is not a proof of better future policy value, and four cases are too few for a release. [[machine-learning/paired-bootstrap-model-gain-intervals|Paired resampling]] can quantify uncertainty with the right independent unit.'),
    ('Audit latency and missingness', 'The challenger may fail to score hard cases, score after the action deadline or require a feature unavailable to the live model. Include all attempted cases and report missing-score rate and latency, not only rows where both outputs exist. For a fair candidate comparison, preserve the same decision-time feature contract. [[machine-learning/prediction-time-feature-availability|Feature timing]] is non-negotiable.'),
    ('Translate score gain into an action policy', 'A lower proper scoring loss does not automatically improve dispatch. Compare predeclared thresholds, false-negative cost, calibration, subgroup error and review load on a held-out future period. If challenger alerts would change outcomes, an approved prospective test may be needed to estimate policy impact. [[machine-learning/decision-threshold-and-cost|Threshold costing]] and [[machine-learning/group-error-gaps-and-policy-audit|group auditing]] state the minimum checks.'),
    ('Name promotion and rollback rules', 'Record the minimum support, acceptable regression bounds, missingness ceiling, operational owner and rollback trigger before viewing the shadow result. A challenger can remain in shadow until enough outcomes mature. [[machine-learning/distribution-shift-response-project|The project]] closes with a bounded pilot decision, not an automatic promotion.')],
    '''# Same case, two issued risk estimates, then the mature outcome.
shadow_cases = [
    ("S741", 0.18, 0.12, 0), ("S742", 0.62, 0.79, 1),
    ("S743", 0.54, 0.37, 0), ("S744", 0.71, 0.84, 1),
]

def paired_brier_delta(rows):
    differences = []
    for shipment_id, champion_risk, challenger_risk, outcome in rows:
        if not (0 <= champion_risk <= 1 and 0 <= challenger_risk <= 1):
            raise ValueError("risk outside probability range")
        champion_loss = (champion_risk - outcome) ** 2
        challenger_loss = (challenger_risk - outcome) ** 2
        differences.append(challenger_loss - champion_loss)
    return sum(differences) / len(differences)

delta = paired_brier_delta(shadow_cases)
assert delta < 0
assert len({shipment_id for shipment_id, *_ in shadow_cases}) == 4''',
    'Paired scoring of N logged cases costs O(N) time and O(1) running memory; the teaching code stores O(N) differences. Shadow inference adds model serving cost and latency without reducing live-model cost. Mature outcomes and a policy-effect evaluation may take much longer than scoring.',
    ['Do not let a shadow score silently change the champion action.', 'Do not evaluate only cases with successful challenger scores.', 'Do not equate improved scoring loss under the champion policy with proven challenger policy value.'],
    ['machine-learning/rolling-origin-retraining-with-embargo','machine-learning/paired-bootstrap-model-gain-intervals','machine-learning/decision-threshold-and-cost','machine-learning/distribution-shift-response-project'])


add('distribution-shift-response-project',
    'Distribution shift response project',
    'A release review joins input support, mature outcome change, time-correct retraining, paired shadow evidence and rollback into one decision packet.', [
    ('Set the decision boundary', 'A new depot changes the mix of shipment backlogs. Define the intake feature snapshot, handoff target, label-ready rule, staffing deadline and affected sites before examining candidate performance. Preserve case IDs across training, shadow and final evaluation. [[machine-learning/covariate-shift-and-support-overlap|The support audit]] determines whether the old model even covers the new traffic.'),
    ('Separate evidence types', 'Input-shift counts arrive promptly; error and calibration require mature outcomes. Importance weighting can estimate target-mix risk only under overlap and a stable within-input outcome mechanism. A within-slice error change challenges that premise. Report these as separate findings rather than one drift score. [[machine-learning/importance-weighted-risk-under-shift|Weighted risk]] and [[machine-learning/concept-change-with-mature-outcomes|concept checks]] make the boundary explicit.'),
    ('Replay the proposed change', 'Use rolling origins with correct label availability to compare fixed and retrained policies. Hold out a later period that did not select the schedule, features, weights or thresholds. Run a challenger in shadow on the same new intakes and log missing scores. [[machine-learning/rolling-origin-retraining-with-embargo|The backtest]] and [[machine-learning/champion-challenger-shadow-comparison|shadow comparison]] answer different questions.'),
    ('Audit the operating consequences', 'Check error by site, calibration, false negatives, reviewer capacity, latency and the cost of a false alert. Include unsupported new cases in the report and route them through a declared fallback. A positive average paired loss difference does not establish a good outcome for every group or action. [[machine-learning/group-error-gaps-and-policy-audit|Group errors]] and [[machine-learning/selective-prediction-and-review-capacity|review load]] are release inputs.'),
    ('Make the disposition explicit', 'The code checks whether required artifacts are present; it does not judge whether their results meet a chosen business threshold. Attach measured values, decision owners, an approved pilot window, the old model version and a rollback trigger. If labels have not matured, keep the decision open instead of treating missing evidence as a pass.')],
    '''def shift_review_gate(packet):
    requirements = {
        "support_checked": "target support",
        "label_clock_documented": "label clock",
        "future_holdout_sealed": "future holdout",
        "shadow_missingness_reported": "shadow missingness",
        "group_errors_reported": "group errors",
        "review_capacity_checked": "review capacity",
        "rollback_version_retained": "rollback version",
    }
    missing = [label for field, label in requirements.items() if not packet.get(field)]
    return "ready for pilot review" if not missing else "hold: " + ", ".join(missing)

depot_packet = {
    "support_checked": True, "label_clock_documented": True,
    "future_holdout_sealed": True, "shadow_missingness_reported": False,
    "group_errors_reported": True, "review_capacity_checked": False,
    "rollback_version_retained": True,
}
assert shift_review_gate(depot_packet) == (
    "hold: shadow missingness, review capacity"
)''',
    'The checklist costs O(K) for K requirements. Cohort counting and paired scoring are O(N); R rolling model fits may cost roughly R times a single fit, depending on the estimator. The substantial operating costs are archived availability data, mature outcomes, shadow serving and a credible rollback path.',
    ['Do not call an input-distribution alarm a measured accuracy loss.', 'Do not promote a challenger on a shadow score alone when actions change outcomes.', 'Do not pass an incomplete decision packet by treating absent labels or capacity as zero risk.'],
    ['machine-learning/covariate-shift-and-support-overlap','machine-learning/importance-weighted-risk-under-shift','machine-learning/concept-change-with-mature-outcomes','machine-learning/rolling-origin-retraining-with-embargo','machine-learning/champion-challenger-shadow-comparison','machine-learning/feature-drift-and-delayed-label-monitoring'])


publish_batch(
    lessons,
    module_title='Distribution shift and model transition',
    module_summary='Diagnose support, estimate risk under an explicit assumption, replay time-correct changes and compare a shadow candidate.',
    project_heading='Distribution shift response',
    crosslinks=[
        ('machine-learning/feature-drift-and-delayed-label-monitoring', lessons[0]['path']),
        ('machine-learning/covariate-shift-and-support-overlap', lessons[1]['path']),
        ('machine-learning/label-prior-shift-and-odds-adjustment', lessons[2]['path']),
        ('machine-learning/group-and-time-validation', lessons[3]['path']),
        ('machine-learning/paired-bootstrap-model-gain-intervals', lessons[4]['path']),
        ('machine-learning/uncertainty-and-escalation-review-project', lessons[5]['path']),
    ],
    sort_start=5200,
)
