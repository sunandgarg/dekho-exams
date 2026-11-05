"""Expand Applied Statistics with imputation, sparse outcomes and quantile decisions."""
from de_batch_publisher import publish

A = 'applied-statistics/'
IMPUTE = 'Multiple imputation and missing-data checks'
SPARSE = 'Sparse categorical outcomes'
TAIL = 'Conditional quantiles and tail decisions'


def lesson(slug, title, module, summary, sections, code, cost, mistakes, related, project=False):
    return dict(path=A + slug, title=title, module=module, project=project,
                summary=summary, sections=sections, code=code, cost=cost,
                mistakes=mistakes, related=[A + path for path in related])


lessons = [
    lesson('multiple-imputation-and-rubin-combination',
        'Multiple imputation: combine estimates and both sources of uncertainty', IMPUTE,
        'Multiple imputation creates several plausible completed datasets, fits the same analysis to each, and combines the resulting estimates and variances.', [
            ('Begin with the missingness design', 'A repair network measures resolution time for eligible cases, but some completion timestamps are absent. Define eligibility, maturity, outcome, and observed predictors before considering filled values. The imputation model should preserve variables that matter to the analysis, including branch and priority interactions when the final model uses them. Draw several plausible values for each missing field rather than reusing one predicted mean. [[applied-statistics/missing-outcome-ledger-and-target-population|The missing-outcome ledger]] still counts every absent value; imputation does not erase it.'),
            ('Fit first, combine second', 'Run the same substantive analysis on each completed dataset and collect one coefficient or contrast with its estimated sampling variance. Average the estimates. Average their variances to obtain within-imputation uncertainty; compute the sample variance of estimates to obtain between-imputation uncertainty. With m completed datasets, total variance is within plus (1 + 1/m) times between. The small code block combines supplied outputs only. It neither generates credible imputations nor supplies a final confidence interval, whose degrees of freedom need separate care.'),
            ('Understand what changes the answer', 'If all completed datasets produce almost identical estimates, between-imputation variance is small; a large spread says missing values materially affect the result. Extra imputations reduce Monte Carlo noise but cannot repair a wrong observation model. A predictor measured after resolution may leak the outcome into the imputation process. If missingness depends on the unrecorded delay after conditioning on observed predictors, ordinary missing-at-random imputation can remain biased. [[applied-statistics/observation-probability-weighting-and-sensitivity|Observation weighting]] shares that identification limit.'),
            ('Publish the analysis boundary', 'Report eligible and missing counts, imputation model variables, number of completed datasets, diagnostics, pooled estimate, within and between components, and sensitivity to a worse missing-case scenario. Keep transformed coefficients on the analysis scale used for combining, then convert for interpretation if justified. A single imputed dataset or a pooled row-level average understates uncertainty. [[applied-statistics/imputation-diagnostics-and-mnar-shifts|The diagnostics lesson]] tests whether plausible draws and sensitivity ranges agree with the operational decision.')
        ], '''from math import sqrt

def combine_imputation_estimates(estimates, sampling_variances):
    if len(estimates) < 2 or len(estimates) != len(sampling_variances):
        raise ValueError("at least two paired analyses are required")
    if any(variance < 0 for variance in sampling_variances):
        raise ValueError("sampling variances must be nonnegative")
    count = len(estimates)
    pooled = sum(estimates) / count
    within = sum(sampling_variances) / count
    between = sum((estimate - pooled) ** 2 for estimate in estimates) / (count - 1)
    return pooled, sqrt(within + (1 + 1 / count) * between)

estimate, standard_error = combine_imputation_estimates([4.2, 5.1, 4.8],
                                                         [0.36, 0.49, 0.25])
assert round(estimate, 3) == 4.7
assert round(standard_error ** 2, 6) == round((0.36 + 0.49 + 0.25) / 3 +
                                             (4 / 3) * 0.21, 6)
''', 'Combining m scalar estimates is O(m) time and O(1) extra space after the results exist. Generating m completed datasets and refitting the substantive model is the dominant cost. More runs reduce simulation noise; they do not buy identification when missingness depends on unrecorded outcomes.',
        ['Using one filled dataset and its usual standard error as the final analysis.', 'Averaging completed rows before fitting, which discards between-imputation spread.', 'Leaving an interaction out of the imputation model when it defines the target contrast.', 'Claiming missing-at-random behavior was proved by comparing observed groups.'],
        ['imputation-diagnostics-and-mnar-shifts', 'service-recovery-imputation-project', 'missing-outcome-ledger-and-target-population', 'observation-probability-weighting-and-sensitivity', 'confidence-interval-coverage']),
    lesson('imputation-diagnostics-and-mnar-shifts',
        'Imputation diagnostics: inspect draws and stress missing-not-at-random shifts', IMPUTE,
        'Diagnostics compare plausible completed values with observed data and expose decisions that depend on assumptions about unseen outcomes.', [
            ('Inspect by the variables that matter', 'A combined estimate can look stable while the completed resolution times for urgent cases violate known service limits. Compare observed and filled distributions within branch, priority, calendar period, and other predictors used by the decision. Review trace plots across imputation iterations if the algorithm samples them, impossible values, and changes in the substantive coefficient across completed datasets. A visual match alone does not prove the missingness assumption. [[applied-statistics/multiple-imputation-and-rubin-combination|Combination rules]] describe uncertainty conditional on the model that generated those draws.'),
            ('Hold out observed cells as a diagnostic', 'Mask a declared subset of known outcomes, generate fills without access to them, and compare filled distributions and prediction errors with held-out truths. This checks whether the model can reconstruct cases resembling the observed ones. It cannot directly validate cases absent because unusually slow repairs never received a closing timestamp. Preserve the selection logic and random seed so an apparent improvement cannot be created by testing only easy cases.'),
            ('Move the unseen outcomes deliberately', 'For sensitivity analysis, shift imputed missing-case resolution times upward by a plausible extra delay and refit or recompute the decision for each shift. A positive shift represents systematically slower unseen cases on the working scale. Choose the range from operational knowledge, not from the threshold that makes the result favorable. The code computes a simple completed mean from supplied observed and filled values to show how a shift changes the conclusion; a full analysis must re-estimate its model and uncertainty across imputations. [[applied-statistics/missing-outcome-ledger-and-target-population|The ledger]] provides the count exposed to this shift.'),
            ('Report a tipping range', 'Present the smallest shift that changes the operational call, the missing fraction in every important group, and the assumption needed to exclude such a shift. If the sign changes under a modest plausible delay, mark the decision as fragile. A large number of imputations cannot make an implausible model safe. [[applied-statistics/service-recovery-imputation-project|The project]] requires a predeclared service threshold and an explicit hold when the conclusion hinges on unseen urgent cases.')
        ], '''def shifted_completed_mean(observed_minutes, filled_minutes, extra_missing_delay):
    if not observed_minutes or not filled_minutes:
        raise ValueError("observed and filled groups required")
    if extra_missing_delay < 0 or any(value < 0 for value in
                                      observed_minutes + filled_minutes):
        raise ValueError("durations and shift must be nonnegative")
    total = sum(observed_minutes) + sum(filled_minutes)
    return (total + len(filled_minutes) * extra_missing_delay) / \
           (len(observed_minutes) + len(filled_minutes))

assert shifted_completed_mean([18, 27, 33], [24], 0) == 25.5
assert shifted_completed_mean([18, 27, 33], [24], 12) == 28.5
''', 'The mean calculation is O(n) time and O(1) extra space. Repeating the full imputation and analysis over s shifts and m imputations costs roughly s times m model fits. A quick shift grid is useful for screening, but final uncertainty must reflect the analysis actually used.',
        ['Reading matching observed and filled histograms as proof of missing-at-random.', 'Using post-outcome predictors unavailable at the intended decision time.', 'Selecting the sensitivity range after seeing the desired headline.', 'Shifting the point estimate while leaving a final uncertainty interval unchanged.'],
        ['multiple-imputation-and-rubin-combination', 'service-recovery-imputation-project', 'missing-outcome-ledger-and-target-population', 'observation-probability-weighting-and-sensitivity', 'population-estimand-and-sampling-frame']),
    lesson('service-recovery-imputation-project',
        'Project: decide whether a service recovery target survives missing outcomes', IMPUTE,
        'Reconcile repair cohorts, pool imputed analyses, and test how much slower unseen closures could be before a release claim fails.', [
            ('Freeze the service question', 'A repair team claims a queue change reduced resolution time for urgent cases. Define eligible tickets, the clock start and stop, which tickets have matured, the comparison period, and the predeclared improvement threshold. Keep a ticket without a final timestamp in the eligible denominator. If the new queue also changes which cases receive a final scan, analyzing completed tickets alone conditions on the intervention. [[applied-statistics/missing-outcome-ledger-and-target-population|The cohort ledger]] must reconcile before modeling.'),
            ('Build and inspect several completed datasets', 'Use baseline branch, device type, priority, intake period, and other pre-resolution variables to draw plausible missing times. Restrict impossible durations. Review observed-versus-filled distributions by urgent status and branch; mask a prespecified set of known cases for a reconstruction check. Fit the same urgent-case contrast in each completed dataset and combine coefficient and variance outputs. A model that imputes urgent tickets as routine tickets simply because the routine group is larger is not acceptable. [[applied-statistics/multiple-imputation-and-rubin-combination|Combination rules]] carry both variance sources.'),
            ('Challenge the favorable model', 'Add extra delay to imputed urgent cases over a stated range and repeat the analysis. Show the tipping shift that would erase the target improvement. If a branch has no observed urgent outcomes, there is no direct evidence for its timing distribution; a pooled model may extrapolate, but that should be labeled and reviewed. [[applied-statistics/imputation-diagnostics-and-mnar-shifts|The sensitivity lesson]] explains why a good masked-observation score cannot settle this risk.'),
            ('Release a decision packet', 'Include cohort counts, missing reasons, branch-level observation rates, variables and constraints used in imputation, draw count, analysis model, pooled estimate, uncertainty, and the shift grid. The gate below blocks an unreviewed decision when missing urgent outcomes, diagnostics, or sensitivity work are absent. A passing gate is a documentation condition; it is not statistical proof that the unseen cases behave like observed ones. Preserve versioned extracts so the result can be reproduced.')
        ], '''def recovery_release_gate(audit):
    if audit["eligible"] != audit["observed"] + audit["missing"]:
        return "hold:cohort-reconciliation"
    if audit["missing_urgent"] and not audit["urgent_diagnostics_passed"]:
        return "hold:urgent-imputation"
    if audit["missing"] and not audit["sensitivity_grid_reviewed"]:
        return "hold:unseen-outcome-shift"
    return "review:effect-and-uncertainty"

audit = {"eligible": 47, "observed": 41, "missing": 6,
         "missing_urgent": 3, "urgent_diagnostics_passed": False,
         "sensitivity_grid_reviewed": True}
assert recovery_release_gate(audit) == "hold:urgent-imputation"
assert recovery_release_gate({**audit, "urgent_diagnostics_passed": True}) \
       == "review:effect-and-uncertainty"
''', 'The gate is O(1); the material cost is rebuilding ticket lineage and rerunning the model for each completed dataset and sensitivity scenario. Cheap complete-case reporting cannot recover tickets missing precisely because resolution was difficult.',
        ['Calling filled timestamps observed facts.', 'Imputing with fields recorded only after closure.', 'Suppressing branches with no observed urgent outcomes.', 'Publishing only the favorable missing-at-random result without its tipping shift.'],
        ['multiple-imputation-and-rubin-combination', 'imputation-diagnostics-and-mnar-shifts', 'missing-outcome-ledger-and-target-population', 'observation-probability-weighting-and-sensitivity', 'confidence-interval-coverage'], True),
    lesson('sparse-contingency-and-exact-test',
        'Sparse contingency tables: exact conditional inference for a two-by-two contrast', SPARSE,
        'A conditional exact test enumerates tables with the observed margins instead of relying on a large-cell approximation.', [
            ('Specify what the four cells count', 'An audit flags duplicate claim payments under two review policies. The table records flagged and unflagged claims in each policy group, using one independent claim as the unit. Preserve the actual denominators, assignment process, and observation window; two flags on the same claim are not two independent trials. Sparse cells can make a large-sample chi-square approximation inaccurate. [[applied-statistics/rare-proportion-wilson-interval|Rare-proportion intervals]] are also needed when a rate estimate is the main output.'),
            ('Condition on the observed margins', 'For a fixed two-by-two table under the null odds ratio of one, the upper-left count follows a hypergeometric distribution when row and column totals are conditioned on. Enumerate feasible counts, calculate each table probability, and sum probability at or above the observed count for a prespecified one-sided alternative. The code below does exactly that. Two-sided exact p-values have more than one definition, so its one-sided tail must not be relabeled as a generic two-sided result. [[applied-statistics/hypothesis-test-and-effect-size|The testing lesson]] separates a tail probability from effect magnitude.'),
            ('Look at design and scale', 'An exact conditional calculation is exact for its stated sampling model and tail rule; it cannot fix biased assignment, unequal follow-up, or dependent units. Report the four counts, absolute event rates, risk difference and a defensible uncertainty interval alongside any p-value. The odds ratio can be large while the absolute change is tiny when events are rare. [[applied-statistics/risk-difference-risk-ratio-and-odds|The effect-scale lesson]] explains why product decisions often need both.'),
            ('Do not repair zeros silently', 'A zero event cell does not license adding a hidden half-count and presenting the result as raw evidence. Some estimators use continuity corrections or penalized models, each with an interpretation cost. Choose the effect measure and interval method before inspecting the favorable direction, and disclose any correction. [[applied-statistics/claims-rule-categorical-project|The project]] holds a launch claim if counted units, exposure windows, or policy assignment cannot be reconciled.')
        ], '''from math import comb

def upper_tail_fixed_margins(policy_events, policy_total,
                             all_events, all_claims):
    if not 0 <= policy_events <= policy_total <= all_claims or \
       not 0 <= all_events <= all_claims or \
       all_events - policy_events > all_claims - policy_total:
        raise ValueError("inconsistent contingency margins")
    denominator = comb(all_claims, policy_total)
    upper = min(policy_total, all_events)
    return sum(comb(all_events, event_count) *
               comb(all_claims - all_events, policy_total - event_count)
               for event_count in range(policy_events, upper + 1)
               if 0 <= policy_total - event_count <= all_claims - all_events) / denominator

assert upper_tail_fixed_margins(2, 4, 2, 8) == 3 / 14
''', 'For N claims and a feasible upper-left-cell range of width k, direct enumeration takes O(k) combinatorial evaluations and O(1) extra space. Large counts need numerically stable probability routines. The computation is trivial next to verifying claim independence and consistent policy exposure.',
        ['Calling a one-sided tail a two-sided exact p-value.', 'Treating a small p-value as a large operational benefit.', 'Counting repeated claim flags as independent claims.', 'Assuming exact arithmetic repairs selection or follow-up bias.'],
        ['risk-difference-risk-ratio-and-odds', 'claims-rule-categorical-project', 'rare-proportion-wilson-interval', 'hypothesis-test-and-effect-size', 'randomization-unit-and-experiment-design']),
    lesson('risk-difference-risk-ratio-and-odds',
        'Binary outcomes: report absolute risk, risk ratio, and odds on their own scales', SPARSE,
        'Risk difference, risk ratio and odds ratio summarize different aspects of the same two-group table and are not interchangeable.', [
            ('Start with event counts and denominators', 'A duplicate-payment control flags 3 of 240 reviewed claims under one rule and 9 of 240 under another. Event risks are 1.25 percent and 3.75 percent. The absolute risk difference is minus 2.5 percentage points if the first rule is labeled candidate. The candidate risk ratio is one third. An odds ratio is calculated from event odds, not event probabilities, and is similar to the risk ratio here only because both event rates are low. [[applied-statistics/sparse-contingency-and-exact-test|Sparse-table testing]] addresses a null model, not which effect scale serves the decision.'),
            ('Choose the scale before seeing the sign', 'A risk difference tells an operations team how many events might change per hundred comparable claims. A risk ratio expresses proportional change. An odds ratio is natural in logistic modeling and certain sampling designs, but should not be described to readers as a direct relative probability. A baseline risk near zero makes a ratio unstable or undefined even when an absolute difference remains meaningful. [[applied-statistics/logistic-model-odds-and-risk-interpretation|The logistic lesson]] translates fitted odds carefully.'),
            ('Show uncertainty and design limitations', 'Report intervals appropriate to each effect scale and sparse counts, plus the actual table and exposure period. A naive Wald interval can behave badly near zero. If assignment was not randomized, changes in case mix or detection effort may explain the contrast. If claims are clustered by account or reviewer, standard errors based on independent claims can be too small. [[applied-statistics/cluster-bootstrap-and-standard-error|The cluster lesson]] starts from the independent unit.'),
            ('Interpret zero events honestly', 'When the candidate group has no observed events, the point risk is zero, but population risk is not proved zero. If the baseline group also has no events, a risk ratio is undefined. The code returns no ratio in that case rather than inventing infinity or adding hidden pseudo-events. A reviewer should see both event counts and an uncertainty bound before a rule is declared safe. [[applied-statistics/claims-rule-categorical-project|The project]] links effect scale to the cost per missed duplicate.')
        ], '''def binary_effects(candidate_events, candidate_total,
                   baseline_events, baseline_total):
    if min(candidate_total, baseline_total) <= 0 or \
       not 0 <= candidate_events <= candidate_total or \
       not 0 <= baseline_events <= baseline_total:
        raise ValueError("valid events and positive denominators required")
    candidate_risk = candidate_events / candidate_total
    baseline_risk = baseline_events / baseline_total
    return {"risk_difference": candidate_risk - baseline_risk,
            "risk_ratio": candidate_risk / baseline_risk if baseline_risk else None}

comparison = binary_effects(3, 240, 9, 240)
assert round(comparison["risk_difference"], 4) == -0.025
assert round(comparison["risk_ratio"], 6) == round(1 / 3, 6)
assert binary_effects(0, 47, 0, 47)["risk_ratio"] is None
''', 'The point-effect calculation is O(1) time and space. Intervals, cluster adjustment and design review cost more than arithmetic. A ratio with a tiny baseline can vary sharply as one event is reclassified, so report counts and absolute changes with it.',
        ['Calling odds ratios risk ratios when outcomes are common.', 'Suppressing denominators or using different observation windows.', 'Calling zero observed events proof of zero population risk.', 'Selecting only the scale that makes a change look largest.'],
        ['sparse-contingency-and-exact-test', 'claims-rule-categorical-project', 'rare-proportion-wilson-interval', 'logistic-model-odds-and-risk-interpretation', 'diagnostic-performance-and-prevalence']),
    lesson('claims-rule-categorical-project',
        'Project: audit a rare duplicate-payment rule before replacing it', SPARSE,
        'Compare two claim controls with reconciled denominators, a declared effect scale, and a sparse-cell uncertainty review.', [
            ('Define the policy decision', 'A claims team proposes a new duplicate-payment flag. Decide whether the target is confirmed duplicate payments per eligible claim, false flags per reviewed claim, or total review cost; these are distinct outcomes. Freeze the approval window and ensure both policies had a comparable opportunity to detect an event. Match the unit of assignment, the unit counted, and the interval used for uncertainty. [[applied-statistics/population-estimand-and-sampling-frame|The estimand lesson]] defines the target population.'),
            ('Reconcile the audit trail', 'Construct a four-cell table for each chosen binary outcome, then verify every claim ID appears once in the analysis unit and that policy labels match the actual rule running at decision time. Repeated flags on one account may demand account-level treatment. A zero or small cell is visible evidence, not an invitation to suppress the table. [[applied-statistics/sparse-contingency-and-exact-test|The exact-test lesson]] provides one prespecified one-sided calculation when its fixed-margin model fits.'),
            ('Quantify business effect and uncertainty', 'Give candidate and baseline risks, absolute difference, and ratio only if the baseline risk is positive. Convert the absolute difference to expected events for the planned volume while stating that transport requires comparable future claims and detection effort. Add a suitable sparse-event interval and a review of costs from false flags. If event adjudication is blinded differently across policies, a statistical test does not repair that measurement difference. [[applied-statistics/risk-difference-risk-ratio-and-odds|The effect-scale lesson]] prevents odds and risks from being mixed.'),
            ('Set the release gate', 'The packet includes policy version, eligible counts, detected and adjudicated events, repeated-account handling, exact or interval method, false-flag burden, and the operational threshold. The gate below halts release for irreconcilable counts or missing decisions about the independent unit. Passing it only allows review of effect and uncertainty; it does not assert that a new rule is better. Preserve disagreement cases for adjudicator recheck and monitor for drift after rollout.')
        ], '''def claims_rule_gate(audit):
    if audit["candidate_events"] > audit["candidate_total"] or \
       audit["baseline_events"] > audit["baseline_total"]:
        return "hold:count-reconciliation"
    if not audit["independent_unit_defined"]:
        return "hold:independent-unit"
    if not audit["matched_observation_window"]:
        return "hold:window"
    return "review:effect-and-cost"

audit = {"candidate_events": 3, "candidate_total": 240,
         "baseline_events": 9, "baseline_total": 240,
         "independent_unit_defined": False, "matched_observation_window": True}
assert claims_rule_gate(audit) == "hold:independent-unit"
assert claims_rule_gate({**audit, "independent_unit_defined": True}) \
       == "review:effect-and-cost"
''', 'The gate and point comparisons are O(1). Claim-level reconciliation is O(n) over records when IDs are indexed. The expensive work is outcome adjudication and correcting repeated-account dependence; no faster test substitutes for a trustworthy four-cell table.',
        ['Mixing confirmed duplicates with unadjudicated flags.', 'Treating repeated flags on one claim as independent events.', 'Comparing unequal detection windows.', 'Approving a rule from a favorable ratio while ignoring absolute benefit and false-flag cost.'],
        ['sparse-contingency-and-exact-test', 'risk-difference-risk-ratio-and-odds', 'rare-proportion-wilson-interval', 'cluster-bootstrap-and-standard-error', 'population-estimand-and-sampling-frame'], True),
    lesson('conditional-quantile-and-pinball-loss',
        'Conditional quantiles: optimize tail predictions with pinball loss', TAIL,
        'A conditional quantile predicts a percentile of outcomes at given feature values, which differs from the mean and from a pooled population percentile.', [
            ('State the quantity for the decision', 'A dispatch team needs a planned time that covers roughly nine of ten comparable shipments, conditional on route, service tier, and booking day. A global ninetieth percentile ignores those fields; a conditional mean answers another question. Fit a model for the chosen quantile level, then evaluate it on later shipments whose outcomes were not used to fit the model. [[applied-statistics/distribution-quantiles-and-outlier-policy|The distribution lesson]] addresses unconditional summaries and the treatment of extreme observations.'),
            ('Use an asymmetric loss', 'Pinball loss weights an underprediction by the quantile level and an overprediction by one minus that level. At a high quantile, missing a slow shipment is costly in the objective, so its minimizer estimates a high conditional percentile under appropriate model capacity and data. The code below scores supplied predictions; it does not train a quantile model. An intercept-only minimizer targets a marginal quantile, while a feature model targets conditional behavior. [[applied-statistics/mean-response-vs-prediction-interval|Prediction intervals]] answer a related but distinct two-bound question.'),
            ('Separate fit from calibration', 'A small average pinball loss does not prove that each route tier has the desired empirical coverage. Count how often actual dispatch time is at or below the predicted threshold overall and within meaningful groups on a time-separated holdout. Too few examples in a rare route make its coverage noisy; report numerator and denominator. Shipment cancellations and late outcome logging can distort the holdout just as they distort training data.'),
            ('Know what a percentile promise means', 'A predicted ninetieth percentile is not a guarantee for the next specific shipment. The conditional model can be misspecified, and traffic patterns can change. If the service promise has a penalty, compare alternative quantile levels against the actual loss and monitoring threshold. [[applied-statistics/quantile-crossing-and-tail-coverage|The coverage lesson]] checks ordering and group performance when several quantiles are estimated separately; [[applied-statistics/dispatch-time-quantile-project|the project]] turns those checks into a release gate.')
        ], '''def mean_pinball(actual_minutes, predicted_minutes, quantile):
    if not 0 < quantile < 1 or not actual_minutes or \
       len(actual_minutes) != len(predicted_minutes):
        raise ValueError("aligned values and a quantile in (0, 1) required")
    return sum(quantile * max(actual - predicted, 0) +
               (1 - quantile) * max(predicted - actual, 0)
               for actual, predicted in zip(actual_minutes, predicted_minutes)) / \
           len(actual_minutes)

assert round(mean_pinball([31, 52], [38, 44], 0.9), 2) == 3.95
''', 'Scoring n forecasts is O(n) time and O(1) extra space. Fitting a conditional quantile model is usually more expensive and depends on the chosen model family. A global sorted percentile is cheaper but misses route-specific variation and can under-cover slow groups.',
        ['Calling a conditional quantile a mean prediction.', 'Reporting training-set coverage as the service guarantee.', 'Dropping delayed or cancelled shipments from holdout without a defined rule.', 'Using one global coverage figure to hide a failing route tier.'],
        ['quantile-crossing-and-tail-coverage', 'dispatch-time-quantile-project', 'distribution-quantiles-and-outlier-policy', 'mean-response-vs-prediction-interval', 'serial-correlation-and-effective-information']),
    lesson('quantile-crossing-and-tail-coverage',
        'Quantile crossing and tail coverage: audit ordered forecasts by group', TAIL,
        'Separately fitted quantile models can produce incoherent ordering, and overall coverage can conceal undercoverage in an important segment.', [
            ('Check prediction ordering first', 'If a model reports both a median and a ninetieth-percentile dispatch time for the same booking, the higher quantile should not fall below the median. Independent fits can cross, especially where data are thin or features fall outside training support. Count crossings on the future holdout and inspect which route and service groups produce them. Sorting the predictions for display hides a model defect; if rearrangement is chosen, state that it changes the predictions and reevaluate its coverage. [[applied-statistics/conditional-quantile-and-pinball-loss|Pinball loss]] evaluates each level separately.'),
            ('Measure coverage with denominators', 'For each quantile level, calculate the fraction of held-out actual durations at or below the predicted threshold. At a nominal 0.9 level, approximately 90 percent is a calibration target for a well-specified future population, subject to sampling error. Also calculate by route, booking period, and service tier. A sample of twelve remote deliveries cannot support the same precision as thousands of local deliveries; show counts rather than treating both percentages equally.'),
            ('Distinguish calibration from sharpness', 'A model can achieve very high coverage by predicting implausibly long times for everyone. Report pinball loss or threshold width along with coverage, and compare against a frozen simple baseline. Use a time-separated validation window and avoid tuning on the final audit period. If traffic patterns move, rolling coverage can fail even when the historical average appears acceptable. [[applied-statistics/serial-correlation-and-effective-information|Serial dependence]] also matters when treating repeated weekly observations as independent evidence.'),
            ('Define what happens on failure', 'Crossings, severe group undercoverage, missing outcomes, or a changed route mix should trigger review before service promises are published. A group with no validation support needs a fallback or restricted scope. The code audits supplied median and high-quantile predictions and computes overall high-quantile coverage; production reporting should also partition by group and attach uncertainty. [[applied-statistics/dispatch-time-quantile-project|The project]] requires that fuller decision packet.')
        ], '''def quantile_audit(actual_minutes, median_minutes, p90_minutes):
    if not actual_minutes or not (len(actual_minutes) == len(median_minutes) ==
                                  len(p90_minutes)):
        raise ValueError("aligned validation rows required")
    crossings = sum(high < median for median, high in
                    zip(median_minutes, p90_minutes))
    coverage = sum(actual <= high for actual, high in
                   zip(actual_minutes, p90_minutes)) / len(actual_minutes)
    return {"crossings": crossings, "p90_coverage": coverage,
            "rows": len(actual_minutes)}

report = quantile_audit([24, 41, 58, 35], [27, 39, 33, 30], [40, 52, 48, 28])
assert report == {"crossings": 1, "p90_coverage": 0.5, "rows": 4}
''', 'The audit is O(n) time and O(1) extra space for n validation rows. Group reporting adds O(g) counters for g segments. Correcting and refitting a crossed model costs more; merely sorting its two outputs is cheap but requires a fresh calibration check.',
        ['Silently sorting crossed quantiles and retaining the old validation claim.', 'Treating ninety-percent nominal coverage as exact in a tiny subgroup.', 'Using very wide thresholds to meet coverage without reporting loss.', 'Evaluating on records selected by whether their dispatch scan arrived.'],
        ['conditional-quantile-and-pinball-loss', 'dispatch-time-quantile-project', 'distribution-quantiles-and-outlier-policy', 'mean-response-vs-prediction-interval', 'serial-correlation-and-effective-information']),
    lesson('dispatch-time-quantile-project',
        'Project: release a route-aware dispatch threshold with tail calibration', TAIL,
        'Build a time-separated validation packet for conditional dispatch quantiles and hold release when tail performance fails in a supported segment.', [
            ('Freeze the service claim', 'A shipping team wants a dispatch threshold for each booking. Define the clock from accepted booking to first dispatch scan, the routes and tiers covered, cancellations, delayed scan handling, and what a customer-facing threshold means. Train on an earlier window and reserve a later period for evaluation. A global historical percentile is a baseline, not proof that one threshold is adequate across all routes. [[applied-statistics/conditional-quantile-and-pinball-loss|Conditional quantiles]] connect the threshold to booking features.'),
            ('Audit the data before the fit', 'Check that route, tier, booking time and other features existed at booking. Do not use a post-dispatch status to predict dispatch time. Keep a separate ledger for missing scans and investigate whether the longest shipments are most likely to have late or absent events. Freeze route definitions before comparing performance; silently merging a poor group into a broad average hides the failure. [[applied-statistics/missing-outcome-ledger-and-target-population|Missing-outcome accounting]] protects the validation population.'),
            ('Compare model and baseline on the future slice', 'Fit at least the median and a high conditional quantile if both will be displayed. Count crossings, compute pinball loss, and report high-quantile coverage overall and by prespecified route and service groups with denominators. A coverage rate above target achieved by huge times is not useful, so compare threshold size and loss against the frozen baseline. A rare group with insufficient evidence gets a documented fallback rather than a fabricated precision claim. [[applied-statistics/quantile-crossing-and-tail-coverage|The audit lesson]] defines these checks.'),
            ('Gate and monitor the promise', 'The gate below rejects crossings, missing-outcome reconciliation gaps, or a segment below its prespecified coverage floor when it has enough validation observations. A passing gate starts monitored rollout, not a perpetual guarantee: track weekly coverage, scan completeness and route mix; review when those drift. Attach model version, validation dates, segment counts, and baseline comparison to the decision packet. Do not choose group floors after seeing which launch candidate passes.')
        ], '''def dispatch_tail_gate(audit, minimum_rows, coverage_floor):
    if audit["eligible"] != audit["observed"] + audit["missing"]:
        return "hold:outcome-ledger"
    if audit["crossings"]:
        return "hold:quantile-crossing"
    for segment in audit["segments"]:
        if segment["rows"] >= minimum_rows and \
           segment["coverage"] < coverage_floor:
            return "hold:segment-coverage"
    return "review:monitored-rollout"

audit = {"eligible": 202, "observed": 200, "missing": 2,
         "crossings": 0, "segments": [{"rows": 88, "coverage": 0.82}]}
assert dispatch_tail_gate(audit, 40, 0.85) == "hold:segment-coverage"
assert dispatch_tail_gate({**audit, "segments": [{"rows": 88, "coverage": 0.89}]},
                          40, 0.85) == "review:monitored-rollout"
''', 'The release gate is O(g) time and O(1) extra space for g segment summaries. Producing the predictions and complete outcome ledger dominates compute and operational cost. Group floors need uncertainty and sufficient support; a cheap pass based on aggregate coverage misses that boundary.',
        ['Using a post-dispatch field as a booking-time predictor.', 'Accepting aggregate coverage when a major route group undercovers.', 'Ignoring absent scans or treating cancellations inconsistently.', 'Treating a passing historical gate as a permanent service guarantee.'],
        ['conditional-quantile-and-pinball-loss', 'quantile-crossing-and-tail-coverage', 'distribution-quantiles-and-outlier-policy', 'missing-outcome-ledger-and-target-population', 'serial-correlation-and-effective-information'], True),
]

modules = [IMPUTE, SPARSE, TAIL]
crosslinks = [
    (A + 'missing-outcome-ledger-and-target-population', A + 'multiple-imputation-and-rubin-combination'),
    (A + 'observation-probability-weighting-and-sensitivity', A + 'imputation-diagnostics-and-mnar-shifts'),
    (A + 'refund-outcome-missingness-project', A + 'service-recovery-imputation-project'),
    (A + 'rare-proportion-wilson-interval', A + 'sparse-contingency-and-exact-test'),
    (A + 'diagnostic-performance-and-prevalence', A + 'risk-difference-risk-ratio-and-odds'),
    (A + 'logistic-model-odds-and-risk-interpretation', A + 'risk-difference-risk-ratio-and-odds'),
    (A + 'distribution-quantiles-and-outlier-policy', A + 'conditional-quantile-and-pinball-loss'),
    (A + 'mean-response-vs-prediction-interval', A + 'quantile-crossing-and-tail-coverage'),
    (A + 'serial-correlation-and-effective-information', A + 'dispatch-time-quantile-project'),
]

if __name__ == '__main__':
    publish(lessons, modules, crosslinks,
            'aitrove-applied-statistics-imputation-categorical-quantiles-import-20261007.json',
            8457, subject='applied-statistics',
            hub_path=A + 'applied-statistics-tutorial')
