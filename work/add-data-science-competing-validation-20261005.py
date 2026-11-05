"""Add original competing-risk prediction and uncertainty lessons."""
import datetime
import html
import json
import re
import uuid
from pathlib import Path

root = Path(__file__).resolve().parents[1]
fixture = root / 'src/data/fixtures.json'
rows = json.loads(fixture.read_text())
slugs = (
    'competing-outcome-contract-at-a-fixed-horizon',
    'aalen-johansen-cumulative-incidence-from-case-events',
    'cause-specific-hazards-to-absolute-event-risk',
    'competing-risk-prediction-calibration-and-brier-score',
    'paired-bootstrap-uncertainty-for-prediction-scores',
    'competing-exit-prediction-review-project',
)
new_paths = {'data-science/' + slug for slug in slugs}
rows = [row for row in rows if row['path'] not in new_paths]
by_path = {row['path']: row for row in rows}
stamp = datetime.datetime.now(datetime.UTC).isoformat()
lessons = []

def add(slug, title, summary, sections, code, cost, mistakes, related):
    lessons.append(dict(path='data-science/' + slug, title=title,
                        summary=summary, sections=sections, code=code,
                        cost=cost, mistakes=mistakes, related=related))

add('competing-outcome-contract-at-a-fixed-horizon',
    'Competing-outcome contracts at a fixed horizon',
    'A competing outcome permanently prevents the event of interest in its original form; it is an observed outcome, while loss of follow-up leaves the outcome unknown.', [
    ('Name the event and its blockers', 'For a support case, the question may be whether it is resolved by day nine. Cancellation first makes later resolution of that same case impossible. Cancellation is a competing event, not a missing status. A case still open and observed through day nine is also a known negative for the nine-day resolution indicator. A case whose status feed ended on day five is unknown at day nine. Treating all three as one zero discards why the outcome was not seen. [[data-science/competing-risks-and-resolution-incidence|Competing-risk basics]] establish the target.'),
    ('Pin the first terminal transition', 'A case can have a resolution record and a later cancellation correction. The analysis needs a deterministic policy for which terminal transition counts and whether the later row is a correction or a genuinely new case. Retain event ID, effective timestamp, recorded timestamp and policy version. Exclude a record with an impossible negative age or duplicate case ID before calculating rates. An unresolved case may have many activity events, but it still contributes one case-level terminal status.'),
    ('Build a horizon state without future leakage', 'The code accepts one final outcome and the age at which that outcome or last observation occurred. A resolution by day nine is a positive; a cancellation by day nine is a known negative. An event after nine implies the case was still under observation at nine, so the nine-day target is negative. Early loss is unknown. This single-indicator contract is appropriate for a fixed-horizon score; it does not estimate an event-time incidence curve.'),
    ('Do not rename a counterfactual', 'If cancellation had been prevented, some cancelled cases might later have resolved. That hypothetical probability is not observed nine-day resolution incidence under the actual workflow. Censoring cancellation and running ordinary Kaplan–Meier analysis answers a different hypothetical question under strong assumptions. For capacity planning, the observed chance of resolution before cancellation is often the useful quantity. [[data-science/aalen-johansen-cumulative-incidence-from-case-events|Cumulative incidence]] retains the competing outcome.'),
    ('Reconcile event shares', 'At a common mature horizon, resolution, cancellation and still-open shares must add to one among cases with known state. Report cases lost before the horizon separately. Changes in cancellation policy can change the resolution share even if the team’s conditional resolution pace did not change. The event taxonomy belongs in every saved model version and validation report.')],
    '''def resolution_by_horizon(case_id, observed_day, outcome, horizon_days):
    if not case_id or observed_day < 0 or horizon_days <= 0:
        raise ValueError("invalid case or horizon")
    if outcome not in {"resolved", "cancelled", "open", "lost"}:
        raise ValueError("unknown outcome")
    if outcome == "open" and observed_day < horizon_days:
        return None
    if outcome == "lost" and observed_day < horizon_days:
        return None
    return int(outcome == "resolved" and observed_day <= horizon_days)

cases = [("E241", 4, "resolved"), ("E242", 6, "cancelled"),
         ("E243", 12, "open"), ("E244", 5, "lost")]
states = [resolution_by_horizon(case_id, day, outcome, 9)
          for case_id, day, outcome in cases]
assert states == [1, 0, 0, None]''',
    'Classifying N already deduplicated case records takes O(N) time and O(N) output space; a streaming count needs O(1) extra space. The real cost is resolving event-log conflicts and reconstructing observation status at the historical cutoff.',
    ['Do not censor a cancellation while claiming to estimate observed resolution incidence.', 'Do not call early loss a known nine-day non-resolution.', 'Do not use a later correction as a predictor available at case creation.'],
    ['data-science/aalen-johansen-cumulative-incidence-from-case-events','data-science/cause-specific-hazards-to-absolute-event-risk','data-science/competing-risk-prediction-calibration-and-brier-score','data-science/competing-exit-prediction-review-project'])

add('aalen-johansen-cumulative-incidence-from-case-events',
    'Aalen–Johansen cumulative incidence from case events',
    'A cumulative-incidence curve accumulates one event type using the probability of remaining free from every terminal event just before each event time.', [
    ('Start with the event-free pool', 'Suppose five support cases are followed from creation. At each distinct terminal time, the risk set contains cases still free of resolution and cancellation immediately beforehand. An observed resolution adds the current event-free share divided by the risk-set size to resolution incidence; a cancellation adds the same type of increment to cancellation incidence. Both terminal types reduce the future event-free share. Right censoring only removes a case from later risk sets. [[data-science/event-time-risk-sets-and-tied-outcomes|Risk sets]] determine the denominator.'),
    ('Inspect the ledger calculation', 'The fixture below has resolution at days two and seven, cancellation at day three, and status loss at days five and nine. Its final resolution incidence is 0.50, cancellation incidence 0.20 and event-free share 0.30. These are small-fixture arithmetic checks, not reliable population estimates. In a real cohort, show uncertainty and the number still under observation near each plotted time. A flat late curve can mean no events or no cases left.'),
    ('Keep the probability identity', 'At each time, estimated resolution incidence plus cancellation incidence plus event-free probability should be one, allowing tiny floating-point error. If two categories overlap, the identity may fail or a case may leave twice. An event after the extraction cutoff must not enter an earlier curve. A case observed open at the cutoff is censored there; it is not a third terminal event.'),
    ('Use a supported tie method', 'The teaching routine rejects shared event ages so the update order is unambiguous. Actual systems often record statuses only to the day, creating ties. A maintained estimator groups events by time and handles all event types in the group together. Do not jitter dates merely to force a preferred ordering. The observation interval may be the meaningful unit, in which case interval-censored methods and sensitivity analysis are needed. [[data-science/interval-censored-resolution-times|Interval censoring]] is a different information pattern.'),
    ('Interpret incidence as observed-world risk', 'The curve estimates the probability of experiencing a particular first event by a horizon in a population with the observed competing exits, subject to censoring assumptions. It does not give the hazard among cases still open, nor the probability of resolution if all cancellations vanished. Compare workflows on a prespecified arrival cohort and horizon, then check how their competing-event policies differ.')],
    '''def competing_incidence(case_records):
    if len({case_id for case_id, _, _ in case_records}) != len(case_records):
        raise ValueError("duplicate case ID")
    if any(day <= 0 or outcome not in {"resolved", "cancelled", "censored"}
           for _, day, outcome in case_records):
        raise ValueError("invalid case observation")
    if len({day for _, day, _ in case_records}) != len(case_records):
        raise ValueError("teaching calculation requires distinct times")
    at_risk = len(case_records)
    event_free = 1.0
    incidence = {"resolved": 0.0, "cancelled": 0.0}
    steps = []
    for _, day, outcome in sorted(case_records, key=lambda record: record[1]):
        if outcome != "censored":
            increment = event_free / at_risk
            incidence[outcome] += increment
            event_free *= 1 - 1 / at_risk
        steps.append((day, incidence["resolved"], incidence["cancelled"],
                      event_free, at_risk))
        at_risk -= 1
    return steps

case_events = [("E311", 2, "resolved"), ("E312", 3, "cancelled"),
               ("E313", 5, "censored"), ("E314", 7, "resolved"),
               ("E315", 9, "censored")]
curve = competing_incidence(case_events)
assert all(abs(actual - expected) < 1e-12
           for actual, expected in zip(curve[-1][1:4], (0.5, 0.2, 0.3)))
assert all(abs(resolved + cancelled + open_share - 1) < 1e-12
           for _, resolved, cancelled, open_share, _ in curve)''',
    'Sorting N case records is O(N log N) time and the step curve uses O(N) space. The per-time update is O(1) for two terminal causes. Production estimators add grouped ties, variance calculation and checks for censoring support.',
    ['Do not remove a competing event as if it were ordinary loss of follow-up.', 'Do not infer a stable late probability from a tiny risk set.', 'Do not create artificial within-day ordering to evade tied times.'],
    ['data-science/competing-outcome-contract-at-a-fixed-horizon','data-science/cause-specific-hazards-to-absolute-event-risk','data-science/competing-risk-prediction-calibration-and-brier-score','data-science/competing-exit-prediction-review-project'])

add('cause-specific-hazards-to-absolute-event-risk',
    'From cause-specific event rates to absolute risk',
    'The chance of a first resolution by a horizon depends on both the resolution rate and every competing-exit rate along the preceding time path.', [
    ('Distinguish conditional pace from cumulative chance', 'A cause-specific resolution hazard concerns cases that remain event-free at that moment. A cumulative-incidence probability concerns everyone in the starting cohort, including cases that already cancelled and can never resolve in that episode. Faster cancellation can reduce resolution incidence even if the resolution hazard among cases still open does not change. This is why a cause-specific hazard ratio cannot simply be read as a ratio of nine-day resolution probabilities. [[data-science/cox-partial-likelihood-and-hazard-ratios|Hazard-ratio interpretation]] applies to the conditional rate.'),
    ('Calculate a discrete path', 'The example uses two time bands. In each band, a case still event-free has mutually exclusive conditional probabilities of resolving, cancelling or staying open. First-band resolution and cancellation probabilities are 0.30 and 0.15, leaving 0.55 event-free. In the second band, 0.20 and 0.10 apply only to that remaining 0.55. Final resolution incidence is 0.41, not 0.30 plus 0.20. Cancellation incidence is 0.205 and the still-event-free share is 0.385.'),
    ('Keep probabilities coherent', 'For every band, the cause-specific conditional probabilities must be nonnegative and sum to at most one. Across bands, each cumulative incidence must be nondecreasing, and the causes plus event-free share must add to one. A model that predicts 0.73 resolution and 0.48 cancellation by the same horizon violates the first-event probability budget. Reject or repair such output before showing it to operators. [[data-science/aalen-johansen-cumulative-incidence-from-case-events|Observed cumulative incidence]] provides a cohort benchmark.'),
    ('Know where the statistical model enters', 'These band probabilities are supplied inputs, not parameters estimated by the teaching code. One production route fits cause-specific models and combines their predicted hazards into cumulative incidence, with careful time discretization and baseline estimation. Another directly models the incidence target. A subdistribution-hazard coefficient is not the same as a cause-specific hazard coefficient; do not interchange them when explaining a result.'),
    ('Connect risk to decisions', 'Staffing needs may depend on the expected number resolved, the cancelled share and the still-open backlog at day nine. Report all three on the same denominator. A policy that changes cancellation rules alters the target distribution, so a model trained before that change needs later-period validation. [[data-science/temporal-validation-of-resolution-models|Temporal validation]] tests the transfer rather than assuming it.')],
    '''def first_event_probabilities(time_band_rates):
    event_free = 1.0
    resolved = cancelled = 0.0
    path = []
    for resolution_rate, cancellation_rate in time_band_rates:
        if (resolution_rate < 0 or cancellation_rate < 0 or
                resolution_rate + cancellation_rate > 1):
            raise ValueError("invalid conditional event probabilities")
        resolved += event_free * resolution_rate
        cancelled += event_free * cancellation_rate
        event_free *= 1 - resolution_rate - cancellation_rate
        path.append((resolved, cancelled, event_free))
    return path

two_band_forecast = first_event_probabilities([(.30, .15), (.20, .10)])
resolution_risk, cancellation_risk, open_risk = two_band_forecast[-1]
assert abs(resolution_risk - .41) < 1e-12
assert abs(cancellation_risk - .205) < 1e-12
assert abs(open_risk - .385) < 1e-12
assert abs(sum(two_band_forecast[-1]) - 1) < 1e-12''',
    'For B time bands and two causes, the path costs O(B) time and O(B) space; retaining only final probabilities reduces extra space to O(1). Fitting the conditional rates and carrying their uncertainty are separate statistical tasks.',
    ['Do not add conditional probabilities from different bands without multiplying by the remaining event-free share.', 'Do not call a cause-specific hazard ratio an absolute-risk ratio.', 'Do not publish cause probabilities whose sum exceeds one.'],
    ['data-science/competing-outcome-contract-at-a-fixed-horizon','data-science/aalen-johansen-cumulative-incidence-from-case-events','data-science/competing-risk-prediction-calibration-and-brier-score','data-science/competing-exit-prediction-review-project'])

add('competing-risk-prediction-calibration-and-brier-score',
    'Calibrate competing-risk predictions at a fixed horizon',
    'Competing-risk calibration compares predicted first-event incidence with the observed share of that event by a fixed horizon on the same starting cohort.', [
    ('Score the event of interest', 'For nine-day resolution prediction, a case resolved by day nine has target one. A case cancelled first by day nine has target zero: its resolution status is known, not missing. A case still observed open through day nine is also zero. A cancellation after day nine means the case had not resolved by the horizon, so the target remains zero. Early loss of observation is unknown and needs a censor-aware estimator rather than a forced label. [[data-science/competing-outcome-contract-at-a-fixed-horizon|The outcome contract]] sets this rule.'),
    ('Keep the full probability vector', 'A model may issue resolution and cancellation probabilities for the same horizon. Check that both are in [0,1] and their sum is no more than one; the remainder is predicted still-event-free probability. The example groups cases by predicted resolution risk and compares mean prediction with observed resolution share. It also computes the mean squared error of resolution risk against the binary outcome, a fixed-horizon Brier score on this fully observed fixture.'),
    ('Do not confuse calibration with causation', 'If a high-risk group predicts 0.68 resolution and 0.50 actually resolve, the absolute predictions overstate this event on that group. The result does not say an intervention caused the gap. Check group size, case mix, censoring, outcome coding and time period first. A small group can show a large apparent gap by chance. Use prespecified bins or a supported smooth estimator with uncertainty; do not tune bins until the chart looks attractive.'),
    ('Handle incomplete follow-up correctly', 'The code rejects a case lost before the horizon. In a real validation cohort, estimate incidence in risk groups with a competing-risk method and use a censor-aware score with an appropriate observation model. A complete-case-only average may change the population if disappearing cases differ by severity. [[data-science/censoring-survival-weights-and-horizon-support|Censoring support]] sets a limit on the longest useful horizon.'),
    ('Compare a frozen reference', 'A forecast is useful only relative to the decision it supports and a stable alternative. Compare its Brier score with a prespecified training-cohort incidence forecast on the same held-out cases; show calibration for resolution and cancellation separately. If one event policy changed, a good score in the old period may not transfer. [[data-science/paired-bootstrap-uncertainty-for-prediction-scores|Paired uncertainty]] prevents a tiny score difference from being overstated.')],
    '''def resolution_calibration(predictions, horizon_days):
    if horizon_days <= 0 or not predictions:
        raise ValueError("invalid horizon or empty cohort")
    if len({case_id for case_id, _, _, _, _ in predictions}) != len(predictions):
        raise ValueError("duplicate case ID")
    groups = {"lower": [], "higher": []}
    squared_errors = []
    for case_id, resolution_risk, cancellation_risk, observed_day, outcome in predictions:
        if (not 0 <= resolution_risk <= 1 or
                not 0 <= cancellation_risk <= 1 or
                resolution_risk + cancellation_risk > 1 or observed_day < 0):
            raise ValueError("invalid probability or observation")
        if outcome not in {"resolved", "cancelled", "open", "lost"}:
            raise ValueError("unknown outcome")
        if outcome in {"open", "lost"} and observed_day < horizon_days:
            raise ValueError("outcome unknown at horizon")
        target = int(outcome == "resolved" and observed_day <= horizon_days)
        group = "higher" if resolution_risk >= .5 else "lower"
        groups[group].append((resolution_risk, target))
        squared_errors.append((resolution_risk - target) ** 2)
    summary = {name: (len(values),
                      sum(risk for risk, _ in values) / len(values),
                      sum(target for _, target in values) / len(values))
               for name, values in groups.items() if values}
    return summary, sum(squared_errors) / len(squared_errors)

cases = [("E441", .72, .12, 3, "resolved"),
         ("E442", .61, .25, 5, "cancelled"),
         ("E443", .28, .37, 11, "open"),
         ("E444", .31, .15, 7, "resolved")]
groups, score = resolution_calibration(cases, 9)
assert groups["higher"][0] == 2
assert groups["higher"][2] == .5
assert 0 < score < 1''',
    'For N fully observed cases and a fixed number of groups, calculation is O(N) time and O(N) space because individual errors and bin members are retained. Running totals can make extra space O(1). Censor-aware scoring requires an additional observation model and support checks.',
    ['Do not label cancellation as missing for observed-world resolution incidence.', 'Do not score early-loss cases as known negatives.', 'Do not claim calibration from a ranking metric alone.'],
    ['data-science/competing-outcome-contract-at-a-fixed-horizon','data-science/aalen-johansen-cumulative-incidence-from-case-events','data-science/paired-bootstrap-uncertainty-for-prediction-scores','data-science/competing-exit-prediction-review-project'])

add('paired-bootstrap-uncertainty-for-prediction-scores',
    'Paired bootstrap uncertainty for prediction-score differences',
    'A case-level paired bootstrap resamples whole cases to assess how much a score difference between two frozen prediction methods varies with the validation cohort.', [
    ('Compare on identical cases', 'Suppose a baseline and a revised model each predict nine-day resolution for the same mature cases. Compute each case’s squared-error difference, baseline minus revised; a positive mean favors the revision under Brier loss. Resample case IDs with replacement and carry both predictions and the outcome together. Resampling separate model tables would break the pairing and exaggerate or distort uncertainty. [[data-science/competing-risk-prediction-calibration-and-brier-score|Fixed-horizon scoring]] defines the outcome.'),
    ('Match the sampling unit', 'If cases are independently sampled, case-level resampling is a useful first approximation. If one customer can open many related cases or a policy rollout occurs by branch, independent case resampling understates uncertainty. Use customer or rollout cluster as the resampling unit and retain every member of a selected cluster. A month-level process shift is not represented by repeatedly drawing cases from only one month; a later cohort tests transfer. [[data-science/temporal-validation-of-resolution-models|Temporal validation]] addresses that distinct question.'),
    ('Read the interval as a teaching diagnostic', 'The code uses a fixed random seed, 600 resamples and empirical percentile endpoints. It returns the observed average improvement and an interval computed from case resampling. With a tiny fixture or a skewed score difference, percentile endpoints can be unreliable. A production report should increase resamples, inspect the distribution, choose a suitable interval method, and explain the validation sampling design. A narrow interval around zero is different from evidence of a useful change.'),
    ('Do not bootstrap away missing follow-up', 'The fixture contains only known nine-day outcomes. If a competing-risk Brier score uses censoring weights, a resample should repeat the relevant censoring estimation and scoring procedure at the correct sampling unit. Holding estimated weights fixed can understate uncertainty. If the goal is uncertainty of a complete fitted pipeline, model training and tuning must also be repeated inside the resample; the simple code instead conditions on frozen predictions.'),
    ('Connect precision to action', 'A score difference is one part of release review. Report sample size, competing-event share, subgroup support, horizon and the absolute score of each model. An apparent improvement in overall Brier score may hide worse calibration in the queue where decisions are made. Use the interval to express sampling variability, not a guarantee of future deployment performance. [[data-science/competing-exit-prediction-review-project|The project]] records both claims separately.')],
    '''import random

def paired_brier_improvement(case_scores, repetitions=600, seed=47):
    if not case_scores or repetitions < 100:
        raise ValueError("insufficient cohort or resamples")
    if len({case_id for case_id, _, _, _ in case_scores}) != len(case_scores):
        raise ValueError("duplicate case ID")
    differences = []
    for _, target, baseline_risk, revised_risk in case_scores:
        if target not in (0, 1) or not 0 <= baseline_risk <= 1 or not 0 <= revised_risk <= 1:
            raise ValueError("invalid frozen prediction")
        differences.append((baseline_risk - target) ** 2 -
                           (revised_risk - target) ** 2)
    observed = sum(differences) / len(differences)
    generator = random.Random(seed)
    replicates = sorted(sum(generator.choices(differences, k=len(differences))) /
                        len(differences) for _ in range(repetitions))
    lower = replicates[int(.025 * repetitions)]
    upper = replicates[int(.975 * repetitions)]
    return observed, (lower, upper)

review_cases = [("E501", 1, .55, .72), ("E502", 0, .48, .31),
                ("E503", 0, .39, .27), ("E504", 1, .62, .68),
                ("E505", 0, .44, .29), ("E506", 1, .59, .66)]
improvement, interval = paired_brier_improvement(review_cases)
assert improvement > 0
assert interval[0] <= improvement <= interval[1]''',
    'With N cases and B resamples, direct case resampling is O(B × N + B log B) time and O(N + B) space. For clustered data, sampling and rebuilding all members of a chosen cluster adds bookkeeping. The calculation does not cover model-refit or censor-model uncertainty.',
    ['Do not bootstrap the two models independently when predictions are paired by case.', 'Do not call an interval from frozen predictions uncertainty for a retrained pipeline.', 'Do not treat a bootstrap interval as protection against calendar drift.'],
    ['data-science/competing-risk-prediction-calibration-and-brier-score','data-science/temporal-validation-of-resolution-models','data-science/censoring-survival-weights-and-horizon-support','data-science/competing-exit-prediction-review-project'])

add('competing-exit-prediction-review-project',
    'Project: review resolution predictions with competing exits',
    'Build a release packet that counts resolution, cancellation, open cases and early observation loss separately before judging a fixed-horizon forecast.', [
    ('Fix a first-event ledger', 'Set case creation as time zero and choose day nine as the business horizon. For each case, keep one first terminal event: resolved or cancelled. Record last observed age for still-open cases and a distinct loss status for records whose feed stopped early. Reconcile this case ledger to the raw event log and document timestamp corrections. [[data-science/competing-outcome-contract-at-a-fixed-horizon|The outcome contract]] prevents cancellations from disappearing into a generic censor field.'),
    ('Estimate cohort incidence', 'Build resolution and cancellation cumulative-incidence curves from the same arrival cohort. Show event counts and risk-set counts beside the curves, including how many cases were lost before day nine. Check that resolution incidence, cancellation incidence and event-free share sum to one at each event time. Do not use one minus a resolution-only Kaplan–Meier curve as observed resolution probability when cancellations block resolution. [[data-science/aalen-johansen-cumulative-incidence-from-case-events|The incidence lesson]] provides the arithmetic fixture.'),
    ('Review the prediction vector', 'For each case, freeze nine-day resolution and cancellation probabilities at creation. Reject negative probabilities and any pair summing above one. Inspect predicted versus observed first-event shares, and score resolution with the same known-horizon cohort used for calibration. If early loss exists, use a documented censor-aware method and inspect support. [[data-science/cause-specific-hazards-to-absolute-event-risk|Cause-specific rates]] can be combined into coherent incidence probabilities.'),
    ('Compare a later-period holdout', 'Evaluate on later arrivals with a mature nine-day horizon. Keep both baseline and revised predictions for the same cases, then calculate their paired score difference and uncertainty at the correct resampling unit. If one organization contributes repeated cases, resample that organization rather than pretending cases are independent. Document cancellation-policy changes across periods. [[data-science/paired-bootstrap-uncertainty-for-prediction-scores|The paired bootstrap]] conditions on frozen predictions.'),
    ('Withhold unsupported claims', 'The compact gate below rejects probability-budget failures and reports unknown horizon states; it does not fit incidence curves or approve a model. The release packet should state the target, cohort dates, first-event counts, early-loss count, curve support, calibration, score comparison, interval method and subgroup coverage. Publish no nine-day accuracy figure from the simple path while unknown states remain.')],
    '''def competing_exit_review_gate(case_forecasts, horizon_days):
    if horizon_days <= 0 or not case_forecasts:
        raise ValueError("invalid review cohort")
    if len({case_id for case_id, *_ in case_forecasts}) != len(case_forecasts):
        raise ValueError("duplicate case ID")
    counts = {"resolved": 0, "cancelled": 0,
              "open_at_horizon": 0, "unknown_at_horizon": 0}
    for case_id, resolution_risk, cancellation_risk, day, status in case_forecasts:
        if (not 0 <= resolution_risk <= 1 or
                not 0 <= cancellation_risk <= 1 or
                resolution_risk + cancellation_risk > 1 or day < 0):
            raise ValueError("invalid forecast or age")
        if status not in {"resolved", "cancelled", "open", "lost"}:
            raise ValueError("invalid case status")
        if status in {"open", "lost"} and day < horizon_days:
            counts["unknown_at_horizon"] += 1
        elif status == "resolved" and day <= horizon_days:
            counts["resolved"] += 1
        elif status == "cancelled" and day <= horizon_days:
            counts["cancelled"] += 1
        else:
            counts["open_at_horizon"] += 1
    counts["simple_score_ready"] = counts["unknown_at_horizon"] == 0
    return counts

forecast_ledger = [("E601", .63, .21, 4, "resolved"),
                   ("E602", .35, .42, 6, "cancelled"),
                   ("E603", .51, .16, 12, "open"),
                   ("E604", .41, .31, 5, "lost")]
review = competing_exit_review_gate(forecast_ledger, 9)
assert review["resolved"] == 1 and review["cancelled"] == 1
assert review["open_at_horizon"] == 1
assert review["unknown_at_horizon"] == 1
assert not review["simple_score_ready"]''',
    'For N cases, the gate costs O(N) expected time and O(N) space for uniqueness checking. Incidence estimation, censor-aware evaluation and bootstrap intervals have additional costs. The gate is a data-contract check, not statistical validation.',
    ['Do not report a nine-day Brier score from a cohort containing unknown nine-day states without an explicit censor-aware method.', 'Do not compare models on different case sets.', 'Do not hide a cancellation-policy change inside an apparent model-quality trend.'],
    ['data-science/competing-outcome-contract-at-a-fixed-horizon','data-science/aalen-johansen-cumulative-incidence-from-case-events','data-science/cause-specific-hazards-to-absolute-event-risk','data-science/competing-risk-prediction-calibration-and-brier-score','data-science/paired-bootstrap-uncertainty-for-prediction-scores'])

assert len(lessons) == len(new_paths) == 6
titles = {path: row['title'] for path, row in by_path.items()}
titles.update({item['path']: item['title'] for item in lessons})

def prose(value):
    return re.sub(r'\[\[([^|]+)\|([^\]]+)\]\]',
                  lambda match: '<a href="/' + match[1] + '">' + match[2] + '</a>',
                  html.escape(value))

def links(targets):
    return '<ul>' + ''.join('<li><a href="/' + target + '">' + html.escape(titles[target]) + '</a></li>'
                            for target in targets) + '</ul>'

def article_body(item):
    parts = ['<p>' + html.escape(item['summary']) + '</p>']
    for heading, paragraph in item['sections']:
        parts.extend(('<h2>' + html.escape(heading) + '</h2>', '<p>' + prose(paragraph) + '</p>'))
    parts.extend(('<h2>Implementation</h2>',
                  '<pre><code class="language-python">' + html.escape(item['code']) + '</code></pre>',
                  '<h2>Performance and operating cost</h2>', '<p>' + html.escape(item['cost']) + '</p>',
                  '<h3>Common Mistakes</h3>',
                  '<ul>' + ''.join('<li>' + html.escape(mistake) + '</li>' for mistake in item['mistakes']) + '</ul>',
                  '<h2>Read next</h2>', links(item['related'])))
    return ''.join(parts)

root_path = 'data-science/data-science-for-beginners'
project_hub_path = root_path + '/project'
for index, item in enumerate(lessons):
    is_project = item['path'].endswith('-project')
    body = article_body(item)
    path = item['path']
    row = dict(id=str(uuid.uuid5(uuid.NAMESPACE_URL, 'https://aitrove.in/' + path)),
               type='article', path=path, title=item['title'], summary=item['summary'], body=body,
               category='AI & Data', subject='data-science-project' if is_project else 'data-science',
               difficulty='Advanced', tags=['ai-data', 'data-science'], potd_date=None,
               featured=False, sort_order=13400 + index, status='published', published_at=stamp,
               created_at=stamp, updated_at=stamp,
               data={'subject_root':root_path,
                     'section_path':project_hub_path if is_project else root_path,
                     'content_format':'html', 'seo_ready':True,
                     'kind':'project' if is_project else 'tutorial',
                     'reading_minutes':max(5, len(re.sub(r'<[^>]+>', ' ', body).split()) // 180),
                     'author_path':'authors/aitrove-editorial',
                     'verification_suite':'Editorial, code and internal-link checks',
                     'related':[{'path':target, 'title':titles[target]} for target in item['related']]})
    rows.append(row)
    by_path[path] = row

tutorial_paths = ['data-science/' + slug for slug in slugs[:5]]
project_path = 'data-science/' + slugs[-1]
hub = by_path[root_path]
module_title = 'Competing exits and prediction uncertainty'
if not any(module['title'] == module_title for module in hub['data']['modules']):
    hub['data']['modules'].insert(-1, {'title':module_title,
                                      'summary':'Define competing exits, estimate incidence, validate event probabilities and quantify score variation.',
                                      'lessons':tutorial_paths})
apply_module = next(module for module in hub['data']['modules'] if module['title'] == 'Apply your knowledge')
if project_path not in apply_module['lessons']:
    apply_module['lessons'].append(project_path)
if '<h2>' + module_title + '</h2>' not in hub['body']:
    hub['body'] += '<h2>' + module_title + '</h2>' + links(tutorial_paths)
    hub['body'] += '<h2>Competing exit prediction review</h2>' + links([project_path])
hub['updated_at'] = stamp

project_hub = by_path[project_hub_path]
if project_path not in project_hub['data']['modules'][0]['lessons']:
    project_hub['data']['modules'][0]['lessons'].append(project_path)
if '<h2>Competing exit prediction review</h2>' not in project_hub['body']:
    project_hub['body'] += '<h2>Competing exit prediction review</h2>' + links([project_path])
project_hub['updated_at'] = stamp

for source, target in [
    ('data-science/competing-risks-and-resolution-incidence', tutorial_paths[0]),
    ('data-science/kaplan-meier-resolution-curve', tutorial_paths[1]),
    ('data-science/cox-partial-likelihood-and-hazard-ratios', tutorial_paths[2]),
    ('data-science/fixed-horizon-survival-prediction-calibration', tutorial_paths[3]),
    ('data-science/ipcw-brier-score-for-survival-predictions', tutorial_paths[4]),
    ('data-science/longitudinal-resolution-validation-project', project_path),
]:
    source_row = by_path[source]
    anchor = '<p><strong>Continue the workflow:</strong> <a href="/' + target + '">' + html.escape(titles[target]) + '</a>.</p>'
    if anchor not in source_row['body']:
        source_row['body'] += anchor
        source_row['data'].setdefault('related', []).append({'path':target, 'title':titles[target]})
        source_row['updated_at'] = stamp

assert len({row['path'] for row in rows}) == len(rows)
fixture.write_text(json.dumps(rows, ensure_ascii=False, indent=2) + '\n')
print(json.dumps({'new_articles':len(lessons), 'new_projects':1, 'crosslinks_from_existing':6}))
