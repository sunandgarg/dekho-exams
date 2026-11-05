"""Extend Applied Statistics with sequential tests, process charts and survey calibration."""
from de_batch_publisher import publish

A = 'applied-statistics/'
SEQUENTIAL = 'Planned interim decisions'
PROCESS = 'Statistical process monitoring'
SURVEY = 'Survey calibration and weight diagnostics'


def lesson(slug, title, module, summary, sections, code, cost, mistakes, related, project=False):
    return dict(path=A + slug, title=title, module=module, project=project,
                summary=summary, sections=sections, code=code, cost=cost,
                mistakes=mistakes, related=[A + path for path in related])


lessons = [
    lesson('interim-look-alpha-allocation',
        'Interim analyses: allocate false-positive risk before the first look', SEQUENTIAL,
        'A planned series of hypothesis tests needs a declared error budget across all opportunities to stop for success.', [
            ('List every decision opportunity', 'A checkout team plans to inspect an experiment after 36, 72, and 120 independent store-days. If it runs an ordinary five-percent test at each look and stops at the first favorable result, its chance of a false success exceeds the one-look target. Freeze the primary outcome, direction, assignment unit, look schedule, and total type-I-error budget before exposure begins. [[applied-statistics/multiple-comparisons-and-stopping-rule|The stopping-rule lesson]] explains why a dashboard refresh is an analysis when it can change the decision.'),
            ('Spend a simple conservative budget', 'One transparent design assigns a small local significance level to each planned look, with their sum no greater than the total budget. The union bound then controls the chance of any false rejection even though the looks reuse data, but it can sacrifice power. This is a deliberately simple allocation, not an implementation of a specialized group-sequential boundary. The code checks planned local thresholds and returns the first declared crossing; it assumes each supplied p-value is valid for its prespecified look under the null.'),
            ('Distinguish efficacy from futility', 'Stopping because evidence supports benefit and stopping because further recruitment is not useful are different decisions. A futility rule may be nonbinding for type-I-error control under a stated design, yet it still affects expected sample size and interpretation. A harm monitor also needs its own outcome and operating rule. Do not select the number or timing of looks after watching the effect estimate, then pretend those looks were prespecified. [[applied-statistics/minimum-detectable-effect-and-sample-plan|The power lesson]] links early boundaries to required information.'),
            ('Report the full path', 'For every planned and actual look, report information accrued, p-value or test statistic, local boundary, and whether enrollment continued. If the trial stops early, disclose that the point estimate may be exaggerated by selection of the first boundary crossing. A confidence interval copied from a fixed-sample analysis may have the wrong repeated-use properties. [[applied-statistics/early-stopping-estimation-and-maturity|The next lesson]] separates the decision boundary from effect-size estimation; [[applied-statistics/checkout-interim-monitor-project|the project]] records the audit trail.')
        ], '''def first_planned_crossing(p_values, local_alpha, total_alpha):
    if not p_values or len(p_values) != len(local_alpha):
        raise ValueError("one threshold required for each planned look")
    if not 0 < total_alpha < 1 or any(not 0 <= value <= 1 for value in p_values):
        raise ValueError("p-values and budget must be probabilities")
    if any(threshold < 0 for threshold in local_alpha) or \
       sum(local_alpha) > total_alpha + 1e-12:
        raise ValueError("planned thresholds exceed total alpha")
    for look, (p_value, threshold) in enumerate(zip(p_values, local_alpha), 1):
        if p_value <= threshold:
            return look
    return None

assert first_planned_crossing([0.021, 0.009, 0.035],
                              [0.005, 0.015, 0.03], 0.05) == 2
''', 'Checking k planned looks is O(k) time and O(1) extra space. Specialized boundaries can preserve more power but need calibrated design software and simulation. The cheap act of reusing a fixed-sample threshold at every look can invalidate the stated false-positive rate.',
        ['Inspecting extra unrecorded looks and claiming the original budget still applies.', 'Confusing a conservative local-alpha allocation with an optimized group-sequential boundary.', 'Changing the primary metric after seeing an interim result.', 'Reporting only the final favorable look and hiding earlier decisions.'],
        ['early-stopping-estimation-and-maturity', 'checkout-interim-monitor-project', 'multiple-comparisons-and-stopping-rule', 'minimum-detectable-effect-and-sample-plan', 'randomization-unit-and-experiment-design']),
    lesson('early-stopping-estimation-and-maturity',
        'Early stopping: separate the success decision from effect estimation', SEQUENTIAL,
        'A trial stopped on favorable interim evidence selects unusually strong early estimates, so its effect report needs the stopping history and mature outcomes.', [
            ('Recognize selection at the boundary', 'Suppose a queue experiment stops as soon as an improvement statistic crosses a high early threshold. Among trials that stop, sampling noise often helped push the observed contrast across that threshold. The observed effect can therefore overstate the underlying effect even when the stopping decision controlled its false-positive probability. A valid rejection rule is not automatically an unbiased point estimator or a compatible confidence interval. [[applied-statistics/interim-look-alpha-allocation|The interim-look lesson]] defines the decision rule.'),
            ('Freeze outcome maturity', 'At an early look, long-running cases may still be unresolved. Comparing completed cases only can select fast cases differently across arms. Set a maturity window before each look, account for missing outcomes, and record the eligible number per randomized unit. If maturity rules change midtrial, the nominal p-value may be testing a different endpoint from the planned one. [[applied-statistics/missing-outcome-ledger-and-target-population|The missing-outcome ledger]] provides the counts and reasons.'),
            ('Report an adjusted or qualified effect', 'A fully adjusted estimate or repeated confidence interval depends on the planned sequential design and should be calculated with a validated method. If that method is unavailable, report the raw estimate as descriptive, label the uncertainty limitation, and collect a prespecified follow-up sample for a separate estimate. Do not treat later nonrandom adopters as an unbiased continuation of the trial. The code below audits maturity and assignment counts before any effect calculation; it deliberately does not manufacture a sequential interval.'),
            ('Keep safety and deployment distinct', 'A trial may cross an efficacy boundary while a cost or safety guardrail remains uncertain. Record every boundary and the eventual adoption rule before reading interim results. An early stop may leave little data on rare harms and on segments enrolled later. [[applied-statistics/checkout-interim-monitor-project|The project]] requires the exact stop reason, maturity ledger, and effect-report status before making a rollout recommendation. [[applied-statistics/rare-proportion-wilson-interval|Rare-event intervals]] illustrate why a small safety sample is weak evidence of absence.')
        ], '''def interim_maturity_gate(look):
    if look["eligible"] != look["mature"] + look["not_yet_mature"]:
        return "hold:cohort-ledger"
    if look["randomized_units"] != look["assigned_units"]:
        return "hold:assignment-ledger"
    if look["not_yet_mature"] and not look["maturity_rule_applied"]:
        return "hold:outcome-maturity"
    if not look["boundary_version_frozen"]:
        return "hold:unfrozen-boundary"
    return "review:sequential-result"

look = {"eligible": 127, "mature": 119, "not_yet_mature": 8,
        "randomized_units": 44, "assigned_units": 44,
        "maturity_rule_applied": False, "boundary_version_frozen": True}
assert interim_maturity_gate(look) == "hold:outcome-maturity"
assert interim_maturity_gate({**look, "maturity_rule_applied": True}) \
       == "review:sequential-result"
''', 'The gate is O(1). Reconstructing event maturity is O(n) over cases, and estimating a stopping-adjusted effect requires specialized analysis of the full design. Reporting a fixed-sample interval is computationally cheap but can be misleading after result-dependent stopping.',
        ['Calling the first boundary-crossing effect unbiased.', 'Treating unresolved outcomes as failures or dropping them without a frozen rule.', 'Using a fixed-sample interval as if repeated looks had not occurred.', 'Claiming a rare safety event is absent after a small early-stop sample.'],
        ['interim-look-alpha-allocation', 'checkout-interim-monitor-project', 'missing-outcome-ledger-and-target-population', 'confidence-interval-coverage', 'rare-proportion-wilson-interval']),
    lesson('checkout-interim-monitor-project',
        'Project: monitor a checkout experiment with declared interim looks', SEQUENTIAL,
        'Freeze a store-day experiment, allocate its success-test budget, and document maturity and safety before a rollout call.', [
            ('Write the trial contract', 'A retailer tests a changed checkout prompt by assigning store-days within regions. The target is a predeclared change in successful checkouts per eligible visit, with a refund complaint rate as a safety outcome. Fix the assignment unit, region blocks, eligibility rules, event lag, maximum study length, and planned look dates. An analyst can refresh a dashboard whenever needed for operations, but a refreshed significance test becomes another decision opportunity if it can stop the trial. [[applied-statistics/randomization-unit-and-experiment-design|The design lesson]] defines the independent unit.'),
            ('Freeze success thresholds', 'Allocate the total false-positive budget across the scheduled looks before viewing outcomes. A simple conservative allocation is auditable; a less conservative design needs calibrated boundaries and simulation of its operating properties. Store versioned thresholds alongside each look. Check that the observed count of decision looks matches the plan. [[applied-statistics/interim-look-alpha-allocation|The alpha-allocation lesson]] explains the error accounting, and [[applied-statistics/multiple-comparisons-and-stopping-rule|multiplicity]] also applies if several primary metrics are promoted after launch.'),
            ('Audit maturity and guardrails', 'At each look, reconcile eligible, mature, pending and missing outcomes for both arms. A checkout visit whose refund window has not closed cannot yet contribute to the complaint endpoint as a known noncomplaint. Publish the exposure and assignment counts by store-day, inspect cross-store traffic where relevant, and keep the complaint guardrail separate from the success boundary. [[applied-statistics/early-stopping-estimation-and-maturity|The early-stop lesson]] warns that a selected winning effect can be exaggerated.'),
            ('Deliver a scoped decision', 'The packet includes randomization audit, all scheduled and actual looks, effect and safety estimates, boundary decisions, maturity rules, and the method used for uncertainty after stopping. The gate below blocks a rollout claim when an undocumented look occurred or immature outcomes were silently counted. Passing the gate permits a statistical and business review; it does not promise the effect will transfer to stores outside the trial. A monitored rollout should keep the same outcome definitions.')
        ], '''def checkout_interim_gate(trial):
    if trial["actual_decision_looks"] != trial["logged_decision_looks"]:
        return "hold:unlogged-look"
    if not trial["alpha_plan_frozen"]:
        return "hold:alpha-plan"
    if trial["immature_counted_as_known"]:
        return "hold:outcome-maturity"
    if not trial["safety_reported"]:
        return "hold:safety"
    return "review:rollout-evidence"

trial = {"actual_decision_looks": 3, "logged_decision_looks": 2,
         "alpha_plan_frozen": True, "immature_counted_as_known": False,
         "safety_reported": True}
assert checkout_interim_gate(trial) == "hold:unlogged-look"
assert checkout_interim_gate({**trial, "logged_decision_looks": 3}) \
       == "review:rollout-evidence"
''', 'The gate is O(1). Joining store-day assignments to visit and refund events is O(n) expected time with indexed IDs. Statistical simulation for a richer sequential design costs more, but the expensive audit is usually discovering undocumented looks and outcome delays.',
        ['Running extra success tests while retaining the planned error claim.', 'Counting pending refund windows as clean outcomes.', 'Reporting a selected early estimate as a guaranteed rollout effect.', 'Omitting the safety endpoint because the primary metric crossed a boundary.'],
        ['interim-look-alpha-allocation', 'early-stopping-estimation-and-maturity', 'randomization-unit-and-experiment-design', 'multiple-comparisons-and-stopping-rule', 'rare-proportion-wilson-interval'], True),
    lesson('varying-denominator-p-chart',
        'P charts: monitor defect fractions with subgroup-specific denominators', PROCESS,
        'A p chart compares each subgroup defect fraction with limits that reflect its own inspection count under a stable binomial baseline.', [
            ('Define a rational subgroup', 'A dispatch operation audits damaged parcels each week. The count inspected varies with volume and audit staffing, so a single fixed-width band around the weekly rate is inappropriate. Define each week, eligible parcel frame, defect rule, and inspection plan; count defective parcels, not the number of defect marks on parcels. Choose a baseline period judged stable before interpreting future points. [[applied-statistics/rare-proportion-wilson-interval|A proportion interval]] answers uncertainty for a particular rate, while a control chart asks whether the process has changed relative to a historical baseline.'),
            ('Use the actual denominator', 'With baseline defect fraction p, the usual binomial standard deviation for subgroup size n is the square root of p times one minus p divided by n. A three-standard-deviation upper limit therefore narrows in high-volume weeks and widens in low-volume weeks; the lower limit is truncated at zero. The code calculates this simple limit from a supplied baseline, not from the week being assessed. It does not account for overdispersion, autocorrelation, or a baseline estimated from very few weeks.'),
            ('Separate a signal from the cause', 'A point beyond its limit is a prompt to inspect materials, routes, scanners, or sampling changes. It does not prove a particular employee or intervention caused the spike. A point inside the limits also does not prove the operation meets a customer specification; the process may be stable at an unacceptable defect rate. [[applied-statistics/process-overdispersion-and-measurement-drift|The diagnostic lesson]] checks whether the simple binomial bands are credible.'),
            ('Keep chart rules prespecified', 'If several supplementary run rules are used, the false-alarm behavior changes. State the complete set before watching the chart, and retain each week even if it is inconvenient. A change in the damage definition or audited population requires a new baseline or a documented bridge, not silent continuation of one chart. [[applied-statistics/parcel-defect-monitor-project|The project]] gates a public quality claim on that measurement continuity.')
        ], '''from math import sqrt

def p_chart_limits(baseline_fraction, inspected_count, width=3):
    if not 0 < baseline_fraction < 1 or inspected_count <= 0 or width <= 0:
        raise ValueError("valid baseline, count and width required")
    spread = width * sqrt(baseline_fraction *
                          (1 - baseline_fraction) / inspected_count)
    return max(0.0, baseline_fraction - spread), \
           min(1.0, baseline_fraction + spread)

low_small, high_small = p_chart_limits(0.04, 50)
low_large, high_large = p_chart_limits(0.04, 500)
assert high_small > high_large
assert low_small == 0
''', 'A subgroup limit is O(1); computing w weekly points is O(w). The baseline and chart are cheap, but adjudicating a damage-rule change can be expensive. A three-sigma formula assumes a stable binomial process and can alarm too often when parcels are clustered by route.',
        ['Using the same control limits for weeks with very different inspected counts.', 'Treating a control limit as a customer specification.', 'Selecting a favorable baseline after seeing the new weeks.', 'Continuing one chart through a changed defect or sampling rule.'],
        ['process-overdispersion-and-measurement-drift', 'parcel-defect-monitor-project', 'rare-proportion-wilson-interval', 'poisson-count-rate-and-exposure', 'serial-correlation-and-effective-information']),
    lesson('process-overdispersion-and-measurement-drift',
        'Process charts: test extra variation before blaming a weekly signal', PROCESS,
        'When observed defect fractions vary more than an independent binomial model predicts, standard p-chart limits can create misleading alarms.', [
            ('Look beyond one plotted point', 'A weekly parcel audit may sample many parcels from the same truck, supplier lot, or route. Those parcels share handling conditions, so their defect outcomes can move together. A binomial chart that treats them as independent has limits that are too narrow. Different inspectors may also apply the damage definition differently; a sudden apparent improvement could be a labeling change. Compare subgroup composition, route mix, inspector assignments, and audit coverage before attributing a signal to operations. [[applied-statistics/varying-denominator-p-chart|The p-chart lesson]] states the simple reference model.'),
            ('Calculate a rough dispersion diagnostic', 'For each week, compare its defect count with n times the baseline fraction, scaled by the binomial variance n p(1-p). Summing these standardized squared residuals and dividing by a stated degrees-of-freedom value gives a rough dispersion statistic. Values well above one suggest more variation than that simple model expects. The code uses k minus one because the pooled baseline is estimated from the same k weeks; it is a screening calculation, not an automatic formal test or a license to widen limits until anomalies disappear.'),
            ('Separate stable heterogeneity from a real shift', 'Extra variation may reflect stable route differences, an unstable process, or data collection artifacts. Stratify by prespecified operational groups or use an approach that respects clustering, then rebuild a stable baseline. If the process itself drifted throughout the baseline, a larger dispersion factor hides the instability rather than correcting it. [[applied-statistics/cluster-bootstrap-and-standard-error|The clustering lesson]] connects shared units to understated uncertainty; [[applied-statistics/serial-correlation-and-effective-information|serial dependence]] matters across weeks.'),
            ('Monitor the measurement process too', 'Audit a sample of images under one damage rubric and track disagreement by inspector and week. A process chart on defect labels cannot distinguish product quality from a new interpretation of damage without such checks. Report both the operational trend and the measurement audit. [[applied-statistics/parcel-defect-monitor-project|The project]] holds a quality claim if route clustering or a rubric switch has not been reconciled, even if a simple control chart appears favorable.')
        ], '''def rough_binomial_dispersion(weekly_counts):
    if len(weekly_counts) < 2 or any(n <= 0 or not 0 <= defects <= n
                                      for defects, n in weekly_counts):
        raise ValueError("at least two valid weeks required")
    total_defects = sum(defects for defects, _ in weekly_counts)
    total_inspected = sum(n for _, n in weekly_counts)
    baseline = total_defects / total_inspected
    if not 0 < baseline < 1:
        raise ValueError("baseline needs both outcomes")
    pearson_sum = sum((defects - n * baseline) ** 2 /
                      (n * baseline * (1 - baseline))
                      for defects, n in weekly_counts)
    return pearson_sum / (len(weekly_counts) - 1)

assert rough_binomial_dispersion([(4, 100), (4, 100)]) == 0
assert rough_binomial_dispersion([(1, 100), (9, 100)]) > 1
''', 'The diagnostic is O(w) time and O(1) extra space for w weeks. Better chart design may need route-level records and a different variance model. Inflating bands after seeing an inconvenient alarm is cheap but erases the intended monitoring rule.',
        ['Treating many parcels from one truck as independent observations.', 'Calling every out-of-limit week a process failure without checking sampling.', 'Using overdispersion to justify hiding a baseline that was already drifting.', 'Ignoring inspector or rubric changes when labels define the measured outcome.'],
        ['varying-denominator-p-chart', 'parcel-defect-monitor-project', 'cluster-bootstrap-and-standard-error', 'serial-correlation-and-effective-information', 'reviewer-agreement-and-prevalence']),
    lesson('parcel-defect-monitor-project',
        'Project: monitor parcel damage without confusing mix and measurement shifts', PROCESS,
        'Build a weekly defect ledger, inspect dispersion, and decide when a quality trend can be reported from a stable baseline.', [
            ('Build one count contract', 'A distribution center wants to publish its weekly damaged-parcel fraction. Define inspected parcels, defect criteria, unique parcel IDs, route and supplier fields, week boundaries, and how audits are selected. Repeated damage marks on one parcel count as one defective parcel for a p chart. Reconcile eligible audits and finalized labels each week before plotting. [[applied-statistics/varying-denominator-p-chart|The p-chart lesson]] uses the actual inspected count for each week.'),
            ('Freeze and inspect a baseline', 'Choose a prior period that was operationally stable under the same rubric. Check route and supplier mix, inspector assignment, and whether weekly sample size changed sharply. Compute a baseline fraction, subgroup-specific limits, and a prespecified signal rule. A stable chart can still sit above the customer’s tolerated damage level, which is a separate decision threshold. Do not discard bad weeks to make the baseline appear stable.'),
            ('Investigate extra variation', 'Calculate a rough dispersion diagnostic and compare route-level fractions. If parcels from one truck move together, either group the data at an appropriate level or use limits that reflect the real dependence structure. Re-adjudicate a sample of images after any rubric change. [[applied-statistics/process-overdispersion-and-measurement-drift|The diagnostic lesson]] explains why simply widening bands is not enough. Record the date and effect of each operational intervention so a before-after claim is not assembled from incompatible periods.'),
            ('Gate the quality report', 'The packet includes the audit frame, weekly numerators and denominators, baseline version, chart rule, route composition, dispersion review, rubric history, and investigated signals. The gate below blocks a public improvement claim if the label rubric changed without a bridge or if the baseline was chosen after the results. Passing the gate begins review, not proof that any one operational change caused improvement. Continue monitoring after release and retire baselines when their measurement contract changes.')
        ], '''def parcel_quality_gate(audit):
    if audit["duplicate_parcels"]:
        return "hold:counting-unit"
    if not audit["baseline_frozen_before_review"]:
        return "hold:baseline-selection"
    if audit["rubric_changed"] and not audit["rubric_bridge_complete"]:
        return "hold:measurement-bridge"
    if not audit["dispersion_reviewed"]:
        return "hold:extra-variation"
    return "review:quality-trend"

audit = {"duplicate_parcels": 0, "baseline_frozen_before_review": True,
         "rubric_changed": True, "rubric_bridge_complete": False,
         "dispersion_reviewed": True}
assert parcel_quality_gate(audit) == "hold:measurement-bridge"
assert parcel_quality_gate({**audit, "rubric_bridge_complete": True}) \
       == "review:quality-trend"
''', 'The gate is O(1); compiling weekly counts is O(n) over audited parcels with indexed IDs. Re-adjudicating disputed images and assessing route dependence are the expensive steps. A chart built on inconsistent labels is fast to render but cannot support a stable quality claim.',
        ['Counting damage marks instead of defective parcels.', 'Removing high-defect weeks from the baseline without a declared reason.', 'Using a stable control chart as proof customer specifications are met.', 'Ignoring a damage-rubric change that makes periods incomparable.'],
        ['varying-denominator-p-chart', 'process-overdispersion-and-measurement-drift', 'rare-proportion-wilson-interval', 'cluster-bootstrap-and-standard-error', 'reviewer-agreement-and-prevalence'], True),
    lesson('survey-poststratification-and-raking-margins',
        'Survey calibration: distinguish known joint cells from separate margins', SURVEY,
        'Poststratification can match known joint population cells; raking iteratively matches separate known margins when their joint table is unavailable.', [
            ('Start with the survey design', 'A contact-center survey oversamples high-volume branches and loses more respondents from late shifts. Begin with inclusion probabilities and a response ledger for the full invited frame. Design weights account for unequal selection; adjustment for nonresponse needs assumptions tied to recorded variables. Calibration then aligns weighted sample totals with independently known population counts, such as branch-by-shift cells or separate branch and shift margins. [[applied-statistics/stratified-survey-estimate-and-population-weights|The survey-estimate lesson]] establishes what population the weights target.'),
            ('Use joint cells when known', 'If every branch-by-shift population count is reliable and represented in the sample, multiply each base weight by target cell total divided by the cell’s current weighted total. The code performs that direct poststratification for one declared cell label. A target cell with positive population count but no sample support cannot be created by multiplying weights; it needs a broader grouping or an explicit model. A zero target with sampled records also deserves a frame audit before those records are silently assigned zero weight.'),
            ('Rake when only margins are known', 'When the joint cross-tabulation is unavailable, iterative proportional fitting alternates adjustments for branch and shift totals until both sets of margins agree within tolerance. This does not ensure the joint distribution is correct, nor does it repair nonresponse driven by unmeasured dissatisfaction within cells. The margins should describe the same population and time window; inconsistent totals cannot all be matched. [[applied-statistics/survey-weight-concentration-and-effective-n|The weight-diagnostic lesson]] checks whether calibration concentrates influence.'),
            ('Carry the design into uncertainty', 'Use variance estimation that reflects sampling clusters, stratification, and the calibration procedure. A simple row-independent standard error for a weighted average is usually incomplete. Report base and final weight ranges, target margins, unsupported cells, convergence tolerance if raking, and sensitivity to trimming. [[applied-statistics/contact-center-calibration-project|The project]] gates a branch satisfaction headline when calibration support or population totals are inconsistent.')
        ], '''def poststratify_cell_weights(sample_rows, target_counts):
    current = {cell: 0.0 for cell in target_counts}
    for cell, base_weight in sample_rows:
        if cell not in target_counts or base_weight <= 0:
            raise ValueError("known cell and positive base weight required")
        current[cell] += base_weight
    if any(total > 0 and current[cell] == 0
           for cell, total in target_counts.items()):
        raise ValueError("positive target cell lacks sample support")
    return [(cell, base_weight * target_counts[cell] / current[cell])
            for cell, base_weight in sample_rows]

weights = poststratify_cell_weights([("day", 2), ("day", 2), ("late", 1)],
                                   {"day": 30, "late": 18})
assert [weight for _, weight in weights] == [15, 15, 18]
''', 'Direct poststratification is O(n + g) time and O(g) space for n sample records and g cells. Raking adds repeated passes over variables until convergence. Neither procedure manufactures observations for an unsupported group or removes bias from unmeasured nonresponse.',
        ['Calibrating to margins from a different population or date.', 'Assigning weights to an empty positive target cell as if observations existed.', 'Calling separate-margin raking equivalent to a known joint distribution.', 'Using final weights with a row-independent variance formula that ignores the design.'],
        ['survey-weight-concentration-and-effective-n', 'contact-center-calibration-project', 'stratified-survey-estimate-and-population-weights', 'survey-design-variance-and-psu', 'missing-outcome-ledger-and-target-population']),
    lesson('survey-weight-concentration-and-effective-n',
        'Survey weights: inspect concentration and the limits of effective sample size', SURVEY,
        'Unequal weights can make a nominally large survey depend heavily on a small number of respondents.', [
            ('Inspect the final weights, not only their sum', 'After design, nonresponse and calibration adjustments, a late-shift respondent may represent many invited agents. Show minimum, median, upper tail, and total final weight, plus the share held by the largest few respondents or primary sampling units. If one branch dominates, a weighted overall satisfaction score can change sharply when a handful of answers move. [[applied-statistics/survey-poststratification-and-raking-margins|The calibration lesson]] explains why these weights were created.'),
            ('Use a diagnostic, not a replacement variance', 'The Kish-style unequal-weight effective count is the square of total weight divided by the sum of squared weights. It equals the raw sample count when all weights match and shrinks when a few weights dominate. The code computes that diagnostic. It does not capture clustering, stratification, outcome correlation with weights, or the finite population correction; therefore it is not a universal substitute for a design-based standard error. [[applied-statistics/survey-design-variance-and-psu|The PSU lesson]] keeps the actual sample design in the variance calculation.'),
            ('Trim with a declared tradeoff', 'Capping extreme weights can lower variance but may reintroduce bias if the rare respondents truly represent underserved groups. Choose a cap by a documented rule, then compare estimates before and after trimming and, where appropriate, recalibrate to maintain known margins. A cap chosen only because it changes the headline in a favorable direction is not defensible. If an entire target subgroup never responded, trimming cannot solve its absent support.'),
            ('Publish domain-level support', 'An overall estimate can have a reasonable effective count while an important late-shift or small-branch domain is supported by very few independent people. Report sample and weighted denominators by domain, response rates, weight concentration, and design-aware intervals. [[applied-statistics/contact-center-calibration-project|The project]] blocks a center ranking when a domain has no respondent support, even if the overall weighted score appears precise.')
        ], '''def unequal_weight_effective_n(weights):
    if not weights or any(weight <= 0 for weight in weights):
        raise ValueError("positive weights required")
    return sum(weights) ** 2 / sum(weight ** 2 for weight in weights)

assert unequal_weight_effective_n([1, 1, 1, 1]) == 4
assert unequal_weight_effective_n([1, 1, 4]) == 2
''', 'The diagnostic is O(n) time and O(1) extra space. Sorting weights for tail summaries costs O(n log n), and design-aware variance estimation may require replicate weights or PSU aggregation. A simple effective count is cheap but cannot capture every source of survey uncertainty.',
        ['Reporting raw respondent count as the precision of a highly weighted estimate.', 'Treating unequal-weight effective n as a complete design-effect calculation.', 'Trimming weights after seeing which cap makes a desired ranking appear.', 'Hiding a domain with no responding units behind a stable overall score.'],
        ['survey-poststratification-and-raking-margins', 'contact-center-calibration-project', 'survey-design-variance-and-psu', 'stratified-survey-estimate-and-population-weights', 'cluster-bootstrap-and-standard-error']),
    lesson('contact-center-calibration-project',
        'Project: calibrate a contact-center survey without hiding sparse shifts', SURVEY,
        'Combine selection and response records with known staffing counts, then audit whether a weighted satisfaction comparison can represent every shift.', [
            ('Define the employee population', 'A service organization wants branch-level satisfaction rates from an agent survey. Freeze the active employee roster, field period, branch and shift codes, invitation method, response definition, and whether contractors are eligible. The roster supplies known branch-by-shift counts. Keep nonrespondents in the response ledger so a high response rate in one shift cannot masquerade as a population balance. [[applied-statistics/population-estimand-and-sampling-frame|The frame lesson]] states whom the estimate covers.'),
            ('Build weights in order', 'Start from selection probabilities, assess response patterns by variables known for every invited agent, and use joint branch-by-shift poststratification if each target cell has respondent support. If only separate margins are trustworthy, consider raking and document its weaker information about the joint mix. [[applied-statistics/survey-poststratification-and-raking-margins|The calibration lesson]] shows why an empty late-shift cell cannot be repaired by arithmetic alone. Stop or narrow the claim when support is absent.'),
            ('Inspect concentration and variance', 'Compare raw and weighted satisfaction, response rates, final weight tails, and effective-weight diagnostics by branch and shift. Estimate uncertainty using the actual design and calibration, rather than pretending all weighted rows were sampled independently. Test a predeclared weight-cap sensitivity, but do not publish only the cap that produces the most flattering branch rank. [[applied-statistics/survey-weight-concentration-and-effective-n|The weight lesson]] distinguishes a diagnostic count from a design-based interval.'),
            ('Release a transparent report', 'The packet contains roster version, invitation and response flow, target totals, cell support, base and final weights, calibration method, weight concentration, branch estimates and intervals, and any trimmed-weight sensitivity. The gate below blocks a claim if target totals conflict or a positive population cell has no respondents. Passing it starts statistical review; unmeasured nonresponse can still bias a calibrated result. Field a follow-up sample for unsupported shifts before making a confident branch comparison.')
        ], '''def center_survey_gate(audit):
    if not audit["roster_totals_reconcile"]:
        return "hold:population-totals"
    if audit["unsupported_positive_cells"]:
        return "hold:cell-support"
    if not audit["weight_concentration_reviewed"]:
        return "hold:weight-influence"
    if not audit["design_variance_reported"]:
        return "hold:survey-uncertainty"
    return "review:scoped-satisfaction"

audit = {"roster_totals_reconcile": True, "unsupported_positive_cells": 1,
         "weight_concentration_reviewed": True,
         "design_variance_reported": True}
assert center_survey_gate(audit) == "hold:cell-support"
assert center_survey_gate({**audit, "unsupported_positive_cells": 0}) \
       == "review:scoped-satisfaction"
''', 'The gate is O(1). Weight construction is O(n + g) for n responses and g target cells; repeated raking adds passes. The costly work is verifying roster totals and following up with a group that never responded, because no weighting formula can observe its satisfaction.',
        ['Calibrating to outdated staffing totals.', 'Treating an empty shift as if a large weight could create a response.', 'Publishing only weighted point estimates without design-aware intervals.', 'Changing a trimming rule after the preferred branch loses its rank.'],
        ['survey-poststratification-and-raking-margins', 'survey-weight-concentration-and-effective-n', 'stratified-survey-estimate-and-population-weights', 'survey-design-variance-and-psu', 'population-estimand-and-sampling-frame'], True),
]

crosslinks = [
    (A + 'multiple-comparisons-and-stopping-rule', A + 'interim-look-alpha-allocation'),
    (A + 'minimum-detectable-effect-and-sample-plan', A + 'early-stopping-estimation-and-maturity'),
    (A + 'checkout-power-project', A + 'checkout-interim-monitor-project'),
    (A + 'rare-proportion-wilson-interval', A + 'varying-denominator-p-chart'),
    (A + 'serial-correlation-and-effective-information', A + 'process-overdispersion-and-measurement-drift'),
    (A + 'warehouse-incident-rate-project', A + 'parcel-defect-monitor-project'),
    (A + 'stratified-survey-estimate-and-population-weights', A + 'survey-poststratification-and-raking-margins'),
    (A + 'survey-design-variance-and-psu', A + 'survey-weight-concentration-and-effective-n'),
    (A + 'contact-center-survey-audit-project', A + 'contact-center-calibration-project'),
]

if __name__ == '__main__':
    publish(lessons, [SEQUENTIAL, PROCESS, SURVEY], crosslinks,
            'aitrove-applied-statistics-sequential-process-survey-import-20261007.json',
            8475, subject='applied-statistics',
            hub_path=A + 'applied-statistics-tutorial')
