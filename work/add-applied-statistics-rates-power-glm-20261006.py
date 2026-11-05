"""Expand Applied Statistics with rare rates, study power and GLM contracts."""
from de_batch_publisher import publish

A = 'applied-statistics/'
RATE = 'Rare events and exposure-aware rates'
POWER = 'Power and practical effect planning'
GLM = 'Generalized linear model interpretation'
lessons = [
    {
        'path': A + 'rare-proportion-wilson-interval',
        'title': 'Rare proportions: keep interval uncertainty visible at zero and one',
        'module': RATE, 'project': False,
        'summary': 'A rare-event proportion needs a bounded interval that remains informative when the observed count is zero.',
        'sections': [
            ('Define the trial before the fraction', 'A fulfillment center records damaged packages among inspected shipments. The numerator is a confirmed damage count; the denominator is shipments inspected under a fixed policy, not every package mentioned in a complaint queue. Choose the reporting window and inspection eligibility before computing a rate. If inspection is targeted at suspicious packages, the observed fraction estimates the inspected group, not all shipments. [[applied-statistics/population-estimand-and-sampling-frame|The sampling frame]] is part of the result.'),
            ('Avoid a collapsed uncertainty band', 'A plain estimate is damaged divided by inspected. The familiar normal interval can produce a negative lower bound or a zero-width result when no damage is observed. A Wilson score interval stays within zero and one and retains positive width at the boundary. Specify the confidence level through its normal critical value, and show the count beside the interval. Zero observed damage in a small sample is not evidence that the true rate must be zero. [[applied-statistics/confidence-interval-coverage|Coverage interpretation]] still applies: the procedure has a repeated-sample target.'),
            ('Check independence and changing inspection', 'The calculation below treats inspected outcomes as independent Bernoulli trials with one rate. Packages from one supplier batch can fail together; repeated inspections of the same package are not new trials. A policy change that directs inspectors toward risky suppliers changes the sampling frame even if the underlying shipment quality stays fixed. Count supplier batches, show inspection share and consider a design-aware interval when dependence is material. [[applied-statistics/cluster-bootstrap-and-standard-error|Cluster uncertainty]] addresses grouped observations rather than pretending each scan is independent.'),
            ('Use the interval in a decision', 'Compare the interval with a predeclared operational limit rather than declaring success from a point estimate below it. If the upper bound remains above the limit, the evidence cannot yet establish the desired rate under this design. More representative inspections may narrow the interval; repeated scans of the same batch often will not. [[applied-statistics/poisson-count-rate-and-exposure|Exposure rates]] cover events per unit time rather than binary outcomes per package, and [[applied-statistics/warehouse-incident-rate-project|the project]] keeps those denominators separate.'),
        ],
        'code': '''from math import sqrt

def wilson_damage_interval(damaged, inspected, critical=1.96):
    if inspected <= 0 or not 0 <= damaged <= inspected or critical <= 0:
        raise ValueError("invalid damage counts or critical value")
    rate = damaged / inspected
    scale = 1 + critical ** 2 / inspected
    center = (rate + critical ** 2 / (2 * inspected)) / scale
    half = critical * sqrt(rate * (1 - rate) / inspected +
                           critical ** 2 / (4 * inspected ** 2)) / scale
    return center - half, center + half

lower, upper = wilson_damage_interval(0, 47)
assert lower >= 0
assert 0 < upper < 1
''',
        'cost': 'The interval takes O(1) time and space after the count is validated. Its computational cost is trivial beside representative inspection and confirmation. The formula does not repair batch dependence, selective inspection or misclassified damage; those limitations can dominate the apparent precision.',
        'mistakes': ['Reporting a zero rate as proof that no damage risk exists.', 'Using a normal interval that collapses to zero width at zero events.', 'Counting repeated scans of the same package as independent trials.', 'Applying an inspected-package interval to all shipments after targeted inspection.'],
        'related': [A + 'poisson-count-rate-and-exposure', A + 'warehouse-incident-rate-project', A + 'confidence-interval-coverage', A + 'population-estimand-and-sampling-frame', A + 'cluster-bootstrap-and-standard-error'],
    },
    {
        'path': A + 'poisson-count-rate-and-exposure',
        'title': 'Event counts and exposure: compare rates across unequal observation time',
        'module': RATE, 'project': False,
        'summary': 'A count becomes comparable only after its event definition and at-risk exposure are aligned across groups.',
        'sections': [
            ('Choose the exposure unit', 'Two warehouses report equipment stoppages, but one ran many more machine-hours. Compare confirmed stoppages per operating machine-hour, not raw counts per calendar month. Exclude hours when a machine was not at risk under the declared event definition, and record changes in telemetry coverage. A rate can be scaled to a readable number of hours without changing its meaning. [[applied-statistics/population-estimand-and-sampling-frame|The target]] identifies which machines and operating periods are represented.'),
            ('Separate counts from rates', 'For count C and positive exposure E, the observed rate is C divided by E. A warehouse with six stoppages over 1,200 machine-hours has the same observed rate as one with three over 600 hours. A rate ratio is meaningful only when the event rule, exposure clock and case mix are comparable. A zero event count has a zero point rate but remains uncertain, just as zero damaged packages do. [[applied-statistics/rare-proportion-wilson-interval|The binomial interval]] addresses a different denominator: independent yes-or-no trials.'),
            ('Inspect the Poisson working model', 'A simple Poisson count model assumes events arise with a stable rate over exposure and has variance equal to its mean under the model. Stoppages may cluster during a faulty shift, violating that variance pattern. Calculate counts by machine, shift and week; compare observed variation with fitted variation before using a narrow Poisson uncertainty statement. Missing machine-hours can make a warehouse appear worse even when its event count is accurate. [[applied-statistics/poisson-regression-offset-and-dispersion|The regression lesson]] extends the rate model with predictors and an exposure offset.'),
            ('Publish a reviewable comparison', 'Show count, exposure, unit, observation period, telemetry coverage and rate together. Do not rank warehouses from a tiny count difference without uncertainty and comparable exposure. If the decision is about an intervention, account for maintenance schedules and other changes rather than treating the raw rate ratio as causal. [[causal-inference/confounder-graph-and-covariate-timing|A confounder review]] frames that question; [[applied-statistics/warehouse-incident-rate-project|the project]] catches a broken exposure meter.'),
        ],
        'code': '''def machine_stoppage_rates(warehouses, per_hours=1000):
    report = {}
    for warehouse, record in warehouses.items():
        events = record["stoppages"]
        hours = record["machine_hours"]
        if hours <= 0 or events < 0 or int(events) != events:
            raise ValueError("invalid count or exposure")
        report[warehouse] = events / hours * per_hours
    return report

rates = machine_stoppage_rates({
    "north": {"stoppages": 6, "machine_hours": 1200},
    "south": {"stoppages": 3, "machine_hours": 600},
})
assert rates == {"north": 5.0, "south": 5.0}
''',
        'cost': 'Computing rates for g groups is O(g) time and O(g) output space. Reliable at-risk exposure collection is the expensive part. A later count model can fit quickly on aggregated data, but incorrect or missing exposure can reverse the apparent ranking no matter how sophisticated the model is.',
        'mistakes': ['Comparing stoppage counts without operating hours.', 'Using calendar time while machines were shut down and not at risk.', 'Treating a Poisson variance assumption as verified by a point rate.', 'Calling an observational warehouse rate ratio the effect of a maintenance policy.'],
        'related': [A + 'rare-proportion-wilson-interval', A + 'warehouse-incident-rate-project', A + 'poisson-regression-offset-and-dispersion', A + 'population-estimand-and-sampling-frame', 'causal-inference/confounder-graph-and-covariate-timing'],
    },
    {
        'path': A + 'warehouse-incident-rate-project',
        'title': 'Project: audit rare damage and machine stoppage reports',
        'module': RATE, 'project': True,
        'summary': 'Reconcile binary inspection denominators and machine-hour exposure before making a warehouse quality claim.',
        'sections': [
            ('Split two different estimands', 'A warehouse dashboard places package damage and machine stoppages under one incident tile. Rebuild them separately. Package damage is a binary outcome among eligible inspected packages; stoppages are event counts over operating machine-hours. Freeze inspection selection, event confirmation, deduplication and observation windows. A numerator may be correct while its denominator is wrong. [[applied-statistics/rare-proportion-wilson-interval|The damage interval]] and [[applied-statistics/poisson-count-rate-and-exposure|the exposure rate]] answer different questions.'),
            ('Trace a suspicious zero', 'The latest damage sample has no confirmed failures among 47 inspected packages. Report zero observed damage with a nonzero upper interval bound, not a guaranteed clean warehouse. Most inspected packages came from one supplier batch; document that dependence and obtain a broader sample before generalizing. One shift recorded an extra scan for each package, which should not double the trial count. [[applied-statistics/cluster-bootstrap-and-standard-error|Batch-level uncertainty]] matters if the supplier link is strong.'),
            ('Repair the operating clock', 'The south warehouse shows fewer stoppages than north, but its meter lost operating-hour events during a gateway outage. Raw counts suggest an improvement; the valid exposure periods imply the same observed rate in the training example. Separate confirmed exposure from missing intervals and do not manufacture hours from a wall-clock duration. A missingness audit should name the responsible telemetry owner. [[data-science/missingness-mechanisms-and-observation-process|Observation-process checks]] limit the comparison.'),
            ('Gate the claim', 'Publish counts, inspected and operating denominators, interval method, supplier-batch coverage and telemetry completeness. Hold a cross-warehouse improvement claim until both denominators are reconciled and uncertainty is reviewed. A later intervention study needs a design for maintenance and supplier changes. The packet should link to [[applied-statistics/confidence-interval-coverage|interval interpretation]] and [[applied-statistics/poisson-regression-offset-and-dispersion|count-model diagnostics]] rather than a single green status badge.'),
        ],
        'code': '''def warehouse_report_gate(report, limits):
    if report["duplicate_package_scans"]:
        return "hold:inspection-denominator"
    if report["machine_hour_coverage"] < limits["minimum_hour_coverage"]:
        return "hold:exposure-clock"
    if report["supplier_batches"] < limits["minimum_batches"]:
        return "review:cluster-support"
    if report["damage_upper_bound"] > limits["maximum_damage_bound"]:
        return "hold:damage-uncertainty"
    return "publish:scoped-rates"

limits = {"minimum_hour_coverage": 0.96, "minimum_batches": 5,
          "maximum_damage_bound": 0.07}
report = {"duplicate_package_scans": False, "machine_hour_coverage": 0.89,
          "supplier_batches": 7, "damage_upper_bound": 0.076}
assert warehouse_report_gate(report, limits) == "hold:exposure-clock"
assert warehouse_report_gate({**report, "machine_hour_coverage": 0.99},
                             limits) == "hold:damage-uncertainty"
''',
        'cost': 'The gate is O(1) time and space after source reconciliation. Restoring machine-hour telemetry and inspecting more supplier batches cost far more than calculating a fraction. A low-cost dashboard shortcut would leave the operational claim dependent on an unobserved denominator.',
        'mistakes': ['Combining event-per-hour and damaged-package percentages as if they share a denominator.', 'Counting duplicate scans as new inspected packages.', 'Replacing missing operating hours with elapsed calendar hours.', 'Treating zero observed damage as a zero-width uncertainty interval.'],
        'related': [A + 'rare-proportion-wilson-interval', A + 'poisson-count-rate-and-exposure', A + 'confidence-interval-coverage', A + 'cluster-bootstrap-and-standard-error', 'data-science/missingness-mechanisms-and-observation-process'],
    },
    {
        'path': A + 'minimum-detectable-effect-and-sample-plan',
        'title': 'Minimum detectable effect: plan a study around a useful change',
        'module': POWER, 'project': False,
        'summary': 'A sample-size plan joins a decision-worthy effect, error rates, baseline variability and the actual assignment unit.',
        'sections': [
            ('Start with the smallest useful change', 'A checkout team can justify shipping a new payment screen if successful payment rises from 20% to at least 25% without increasing fraud review. That five-percentage-point difference is a practical threshold chosen from business cost, not from whichever result later becomes significant. State the target population, primary binary outcome, equal or unequal allocation, two-sided false-positive rate and desired power before exposure begins. [[applied-statistics/hypothesis-test-and-effect-size|Effect size]] is part of the decision contract.'),
            ('Use an approximation transparently', 'For two independent equally sized groups, a normal approximation can estimate required users per arm from a planning baseline, target difference and critical multipliers. The code uses a pooled planning variance and rounds up. It is a starting budget, not an exact guarantee of achieved power: actual baseline rates, dropout, repeated users and a discrete test can change the needed size. Recalculate with design-specific software before committing traffic. [[applied-statistics/randomization-unit-and-experiment-design|Assignment units]] may be accounts rather than sessions.'),
            ('Plan a range, not one magic number', 'Show sample needs for several plausible baseline rates and effect thresholds. Smaller effects cost sharply more observations because the difference enters the denominator squared in this approximation. If capacity cannot reach the useful effect, change the question, extend the run, or acknowledge that the study will be imprecise. Do not quietly redefine the effect after a null result. [[applied-statistics/cluster-attrition-and-power-budget|Cluster and attrition adjustments]] translate a user-level target into a deployable plan.'),
            ('Protect the resulting decision rule', 'Freeze success criteria, launch window, inclusion rules and any interim looks. Adding many outcomes or repeated unplanned significance checks changes the false-positive behavior. Power is the chance of rejecting a specified false null under an assumed data-generating scenario; it is not the chance that the eventual hypothesis is true. [[applied-statistics/multiple-comparisons-and-stopping-rule|Stopping rules]] and [[applied-statistics/checkout-power-project|the project]] carry the plan into execution.'),
        ],
        'code': '''from math import ceil

def approximate_users_per_arm(baseline_rate, target_rate,
                              critical_alpha=1.96, critical_power=0.84):
    if not 0 < baseline_rate < 1 or not 0 < target_rate < 1:
        raise ValueError("rates must be between zero and one")
    difference = abs(target_rate - baseline_rate)
    if difference == 0:
        raise ValueError("target must differ from baseline")
    pooled_rate = (baseline_rate + target_rate) / 2
    variance = pooled_rate * (1 - pooled_rate)
    return ceil(2 * (critical_alpha + critical_power) ** 2 *
                variance / difference ** 2)

needed = approximate_users_per_arm(0.20, 0.25)
assert needed == 1094
assert approximate_users_per_arm(0.20, 0.23) > needed
''',
        'cost': 'The approximation is O(1) time and space. Actual study cost scales with independent assigned units, outcome maturity and review capacity. A power number computed from session rows instead of the randomized account unit can be far too optimistic despite correct arithmetic.',
        'mistakes': ['Choosing the minimum effect after inspecting the result.', 'Treating approximate sample size as a guarantee of achieved power.', 'Counting sessions when assignment and dependence are at account level.', 'Ignoring the other primary outcome or repeated interim tests in the design.'],
        'related': [A + 'cluster-attrition-and-power-budget', A + 'checkout-power-project', A + 'hypothesis-test-and-effect-size', A + 'randomization-unit-and-experiment-design', A + 'multiple-comparisons-and-stopping-rule'],
    },
    {
        'path': A + 'cluster-attrition-and-power-budget',
        'title': 'Cluster and attrition planning: count independent branches, not rows',
        'module': POWER, 'project': False,
        'summary': 'A clustered rollout needs enough independent assignment units after outcome loss, not merely enough observed customer rows.',
        'sections': [
            ('Identify why rows are dependent', 'A checkout interface is rolled out by branch because staff training and shared devices make per-customer randomization impractical. Customers within a branch share local procedures, so the effective information is smaller than a same-size independent-user experiment. An intracluster correlation estimate from earlier comparable branches can guide planning, but it has uncertainty. [[applied-statistics/randomization-unit-and-experiment-design|The randomization unit]] governs both analysis and sample size.'),
            ('Build a transparent first budget', 'For roughly equal cluster size m, the simple design-effect approximation is one plus (m minus one) times the intracluster correlation. Multiply the independent-user target by that factor, adjust for expected outcome retention, then round up to whole branches. This does not replace a proper cluster trial calculation: unequal sizes, few branches, covariate adjustment and contamination can change power. [[applied-statistics/minimum-detectable-effect-and-sample-plan|The base target]] must be tied to a useful change before inflation.'),
            ('Handle missing outcomes explicitly', 'If payment success is unobserved for some assigned accounts, a retention adjustment budgets more assignment but does not remove bias. Track loss by arm, branch and baseline risk. The analysis should retain the assigned population under its predeclared missing-outcome rule. If one branch is closed mid-study, dropping it can break balance and shrink the true number of independent units. [[data-science/missingness-mechanisms-and-observation-process|Missingness mechanisms]] require separate sensitivity work.'),
            ('Check feasibility and uncertainty', 'List required branches per arm, eligible accounts per branch, expected retention and the uncertainty around the correlation assumption. Run a range of correlation values; if branch capacity cannot meet the plan, state that the desired effect is not resolvable under this rollout. Avoid a false precision claim from thousands of customers in only a handful of branches. [[applied-statistics/cluster-bootstrap-and-standard-error|Cluster-aware uncertainty]] belongs in analysis; [[applied-statistics/checkout-power-project|the project]] holds a branch-limited launch.'),
        ],
        'code': '''from math import ceil

def branches_per_arm(independent_users, users_per_branch, correlation, retention):
    if independent_users < 1 or users_per_branch < 2:
        raise ValueError("positive users and branch size required")
    if not 0 <= correlation < 1 or not 0 < retention <= 1:
        raise ValueError("invalid correlation or retention")
    design_effect = 1 + (users_per_branch - 1) * correlation
    assigned_users = ceil(independent_users * design_effect / retention)
    return ceil(assigned_users / users_per_branch)

branches = branches_per_arm(1094, 20, 0.03, 0.90)
assert branches == 96
assert branches_per_arm(1094, 20, 0.06, 0.90) > branches
''',
        'cost': 'The planning calculation is O(1) time and space. Operational cost rises with the number of independent branches, not just customer observations. Larger within-branch correlation and lower retention can make a branch rollout infeasible; collecting more customers in the same few branches does not create new independent assignments.',
        'mistakes': ['Inflating user count while leaving the number of assigned branches unchanged.', 'Treating one pilot estimate of intracluster correlation as exact.', 'Calling attrition adjustment a solution to selective missing outcomes.', 'Applying an individual-level significance test to a branch-randomized release.'],
        'related': [A + 'minimum-detectable-effect-and-sample-plan', A + 'checkout-power-project', A + 'randomization-unit-and-experiment-design', A + 'cluster-bootstrap-and-standard-error', 'data-science/missingness-mechanisms-and-observation-process'],
    },
    {
        'path': A + 'checkout-power-project',
        'title': 'Project: decide whether a branch checkout experiment has enough power',
        'module': POWER, 'project': True,
        'summary': 'Translate a useful payment lift into branches per arm, then reject an underpowered launch before collecting outcomes.',
        'sections': [
            ('Freeze the practical question', 'The checkout team wants a five-percentage-point payment-success improvement from a 20% planning baseline while fraud-review load stays within capacity. Branches receive the interface assignment because staff training is shared. Write the primary outcome, guardrail, analysis population and fixed decision rule before recruiting branches. The useful effect is a cost judgment, not a number selected from a pilot p-value. [[applied-statistics/minimum-detectable-effect-and-sample-plan|The individual-unit approximation]] supplies only the first budget.'),
            ('Convert to assignment units', 'The independent-user approximation yields 1,094 observations per arm under the stated planning multipliers. With 20 users per branch, estimated within-branch correlation of 0.03 and 90% outcome retention, the simple inflation suggests 96 branches per arm. Only 58 per arm are available. Show a sensitivity range for correlation and branch size; do not fill the gap by counting multiple sessions per user. [[applied-statistics/cluster-attrition-and-power-budget|The branch adjustment]] is still approximate but exposes the feasibility problem.'),
            ('Reject a weak claim, not the investigation', 'At 58 branches per arm, a negative result would leave the decision-worthy effect unresolved under the planned design. Options include a longer recruitment window, a larger effect threshold justified by economics, or a different valid assignment scheme. Do not launch and reinterpret a nonsignificant result as proof of no benefit. Keep an explicit fraud-review guardrail and avoid adding new primary outcomes later. [[applied-statistics/multiple-comparisons-and-stopping-rule|The stopping rule]] remains fixed.'),
            ('Handoff the experiment packet', 'Record planning baseline, useful effect, allocation, alpha, target power, branch sizes, correlation range, retention, expected outcome maturity and branch availability. Name the decision owner and conditions for a revised design. If the study proceeds later, analyze by assigned branch and report effect sizes and uncertainty. [[applied-statistics/hypothesis-test-and-effect-size|Effect reporting]] and [[applied-statistics/cluster-bootstrap-and-standard-error|cluster sampling]] govern the analysis, not a session-level shortcut.'),
        ],
        'code': '''from math import ceil

def checkout_plan_gate(independent_users, users_per_branch, correlation,
                       retention, available_branches):
    if independent_users < 1 or users_per_branch < 2 or not 0 <= correlation < 1:
        raise ValueError("invalid study design")
    if not 0 < retention <= 1 or available_branches < 0:
        raise ValueError("invalid retention or branch capacity")
    required = ceil(ceil(independent_users *
                         (1 + (users_per_branch - 1) * correlation) /
                         retention) / users_per_branch)
    return {"required_per_arm": required,
            "state": "ready" if available_branches >= required else "hold:branch-capacity"}

plan = checkout_plan_gate(1094, 20, 0.03, 0.90, 58)
assert plan == {"required_per_arm": 96, "state": "hold:branch-capacity"}
''',
        'cost': 'The gate uses O(1) time and space. Recruiting branches, preserving assignment and waiting for mature payment outcomes dominate study cost. An underpowered launch can be costly twice: it consumes users and still fails to distinguish a useful effect from noise.',
        'mistakes': ['Calling 58 branches sufficient because their customer rows exceed the individual target.', 'Moving the useful-effect threshold after a null result.', 'Treating nonsignificance as proof that the screen cannot help.', 'Ignoring fraud-review capacity when planning payment success.'],
        'related': [A + 'minimum-detectable-effect-and-sample-plan', A + 'cluster-attrition-and-power-budget', A + 'randomization-unit-and-experiment-design', A + 'multiple-comparisons-and-stopping-rule', A + 'cluster-bootstrap-and-standard-error'],
    },
    {
        'path': A + 'logistic-model-odds-and-risk-interpretation',
        'title': 'Logistic regression: translate odds coefficients back to risk',
        'module': GLM, 'project': False,
        'summary': 'A logistic coefficient changes log odds; its exponent is an odds ratio, not an automatic risk ratio or causal effect.',
        'sections': [
            ('Identify the outcome and comparison', 'A claims team models whether a submitted claim needs manual verification within seven days. Define the eligible claims, prediction-time fields, label maturity and the contrast of interest. A logistic model keeps fitted probabilities between zero and one by modeling log odds as a linear function of inputs. A coefficient compares cases at fixed included covariates; it does not describe a guaranteed change from intervening on that field. [[applied-statistics/linear-regression-estimand-and-slope|Coefficient interpretation]] still begins with the design.'),
            ('Keep odds and probability distinct', 'If the baseline probability is 0.20, its odds are 0.25. Multiplying those odds by 1.8 gives 0.45, corresponding to probability about 0.31, not 0.36. The probability difference depends on baseline risk, so one odds ratio does not map to one risk difference for every claim. The code performs that conversion explicitly. [[machine-learning/logistic-regression-log-loss-and-odds|Model fitting and log loss]] are related, while this lesson focuses on interpretation and inference.'),
            ('Audit data and uncertainty', 'Inspect class counts, repeated customers, case-mix shifts and complete separation. A huge coefficient with a huge standard error can indicate sparse outcome support rather than a dramatic stable effect. An outcome collected only for reviewed claims produces selective labels; a well-fitted model on those rows need not describe all submissions. [[applied-statistics/rare-proportion-wilson-interval|Rare outcome counts]] and [[mlops/selective-label-observation-and-audit-sampling|observation bias]] deserve explicit reports.'),
            ('Report useful quantities', 'Show predicted risks for a few prespecified, supported claim profiles, with uncertainty and calibration on a future cohort. Include baseline prevalence and action threshold so the odds ratio is not left to stand alone. If the goal is an intervention effect, use a causal design. [[applied-statistics/claim-count-glm-project|The project]] compares interpretation of binary risk with a separate count-rate model; [[machine-learning/probability-calibration|calibration]] tests whether predicted probabilities match observed frequencies.'),
        ],
        'code': '''from math import exp, log

def risk_after_odds_multiplier(baseline_risk, odds_multiplier):
    if not 0 < baseline_risk < 1 or odds_multiplier <= 0:
        raise ValueError("invalid risk or odds multiplier")
    baseline_odds = baseline_risk / (1 - baseline_risk)
    changed_odds = baseline_odds * odds_multiplier
    return changed_odds / (1 + changed_odds)

candidate_risk = risk_after_odds_multiplier(0.20, 1.8)
assert round(candidate_risk, 6) == round(0.45 / 1.45, 6)
assert candidate_risk != 0.20 * 1.8
assert round(exp(log(1.8)), 6) == 1.8
''',
        'cost': 'The odds conversion is O(1) time and space. Fitting a logistic model costs repeated passes through the data and depends on sample and feature size. Collecting representative mature labels and auditing sparse groups are more important for a trustworthy estimate than the cost of this arithmetic.',
        'mistakes': ['Reading an odds ratio as a risk ratio.', 'Calling an observational coefficient the effect of changing the claim field.', 'Ignoring sparse-event separation and unstable coefficient uncertainty.', 'Validating only on reviewed claims while describing all submitted claims.'],
        'related': [A + 'poisson-regression-offset-and-dispersion', A + 'claim-count-glm-project', A + 'rare-proportion-wilson-interval', 'machine-learning/logistic-regression-log-loss-and-odds', 'machine-learning/probability-calibration'],
    },
    {
        'path': A + 'poisson-regression-offset-and-dispersion',
        'title': 'Poisson count models: use exposure offsets and test dispersion',
        'module': GLM, 'project': False,
        'summary': 'A Poisson log-link model turns a count predictor into a rate comparison only when exposure is represented correctly.',
        'sections': [
            ('Model events over time at risk', 'A claims operations team counts duplicate submissions per branch-month. Branches operate for different numbers of monitored claim-days. A count model with a log exposure offset predicts expected events as exposure times a modeled rate; the offset coefficient is fixed at one. Do not pass both exposure and its logarithm to a library that already logs the exposure argument. [[applied-statistics/poisson-count-rate-and-exposure|The raw rate lesson]] establishes the denominator before regression begins.'),
            ('Interpret a coefficient on the rate scale', 'With a log link, exponentiating a predictor coefficient gives a conditional rate ratio at fixed included covariates and comparable exposure. A rate ratio of 1.4 means the modeled rate is 40% higher for that contrast, not that every branch will have 40% more events. Expected count also scales with exposure: double at-risk claim-days and the modeled count doubles under the same rate. The small program below calculates expected counts from a prespecified model; it is not a fitting routine.'),
            ('Check variance and zeros', 'The basic Poisson model sets conditional variance equal to conditional mean. Duplicate submissions can arrive in bursts from one system outage, producing extra variation and many zero months. Compare residual patterns and count variance within comparable exposure bands; investigate event deduplication and offsets before changing distribution families. A negative-binomial or other model may better handle excess spread, but it cannot repair wrong claim-day exposure. [[applied-statistics/regression-residuals-and-influence|Residual thinking]] transfers to this count setting.'),
            ('Keep inference and causality separate', 'Branch software versions, staffing and season can confound the predictor. Standard errors may need branch clustering if repeated months share shocks. Report count, exposure, modeled rate, dispersion check, calendar support and uncertainty by branch segment. [[applied-statistics/claim-count-glm-project|The project]] holds a rate claim when the offset is missing or event bursts violate the planned uncertainty; [[causal-inference/confounder-graph-and-covariate-timing|a confounder graph]] is needed for intervention claims.'),
        ],
        'code': '''from math import exp, log

def expected_duplicate_claims(log_baseline_rate, log_rate_ratio,
                              upgraded_branch, monitored_claim_days):
    if monitored_claim_days <= 0 or upgraded_branch not in (0, 1):
        raise ValueError("invalid exposure or branch indicator")
    linear_predictor = (log_baseline_rate +
                        log_rate_ratio * upgraded_branch +
                        log(monitored_claim_days))
    return exp(linear_predictor)

base = expected_duplicate_claims(log(0.07), log(1.4), 0, 200)
upgraded = expected_duplicate_claims(log(0.07), log(1.4), 1, 200)
assert round(base, 6) == 14
assert round(upgraded, 6) == 19.6
''',
        'cost': 'A single prediction takes O(1) time and space; fitting a count model requires repeated scans of the training rows. Correct exposure collection, deduplication and dependence-aware uncertainty cost more than evaluating the link function. A tiny standard error from an underdispersed working assumption can be misleading when branch outages create event bursts.',
        'mistakes': ['Comparing count coefficients without an at-risk exposure offset.', 'Logging exposure twice when a fitting library already accepts raw exposure.', 'Assuming Poisson mean-equals-variance after clustered system outages.', 'Reading a conditional rate ratio as an intervention effect.'],
        'related': [A + 'logistic-model-odds-and-risk-interpretation', A + 'claim-count-glm-project', A + 'poisson-count-rate-and-exposure', A + 'regression-residuals-and-influence', 'causal-inference/confounder-graph-and-covariate-timing'],
    },
    {
        'path': A + 'claim-count-glm-project',
        'title': 'Project: review binary claim risk and duplicate-count rates',
        'module': GLM, 'project': True,
        'summary': 'Keep odds, rates and exposure separate while reviewing two models built from the same claims workflow.',
        'sections': [
            ('Split the outcomes', 'A claims department has two reports. One predicts whether a claim requires manual verification within seven days. The other counts duplicate submissions per branch-month. Define a mature binary label and eligible claims for the first; define an event rule and monitored claim-days for the second. These are different estimands even if both involve the same operational system. [[applied-statistics/logistic-model-odds-and-risk-interpretation|Binary risk]] and [[applied-statistics/poisson-regression-offset-and-dispersion|count rates]] require different interpretations.'),
            ('Catch two plausible errors', 'A draft memo says a logistic odds ratio of 1.8 means risk rose by 80%; at a 20% baseline, the implied comparison risk is only about 31% under the stated odds relation. The count report compares raw branch totals even though monitored claim-days differ. Rebuild the model packet with baseline risk, odds conversion, event counts and exposure. Preserve model versions, inclusion windows and prediction-time covariates. [[applied-statistics/poisson-count-rate-and-exposure|Raw exposure arithmetic]] is the first audit.'),
            ('Review model adequacy', 'Check binary calibration on future mature claims, sparse positive groups and whether unreviewed claims lack labels. For counts, inspect residuals by branch-month and whether outages create overdispersion or zero-heavy periods. Keep repeated branches together when estimating uncertainty. Do not fix a count offset issue by swapping model family, and do not call a sparse binary odds coefficient stable because its point estimate is large. [[machine-learning/probability-calibration|Calibration]] and [[applied-statistics/regression-residuals-and-influence|residual checks]] provide separate evidence.'),
            ('Publish a scoped decision', 'Gate each report separately: hold the count-rate memo if exposure coverage is incomplete, and hold the binary risk memo if label maturity or calibration fails. Include intervention caveats for both because assignment was observational. Hand off corrected quantities, uncertainty method, data-quality owner and follow-up sample plan. [[applied-statistics/population-estimand-and-sampling-frame|The sampling frame]] determines whose claims are described; [[causal-inference/confounder-graph-and-covariate-timing|causal review]] is a later study.'),
        ],
        'code': '''def claim_model_release(binary_report, count_report, limits):
    if binary_report["mature_label_share"] < limits["minimum_label_share"]:
        return "hold:binary-labels"
    if binary_report["calibration_error"] > limits["maximum_calibration_error"]:
        return "hold:binary-calibration"
    if count_report["exposure_coverage"] < limits["minimum_exposure_coverage"]:
        return "hold:count-exposure"
    if count_report["dispersion_ratio"] > limits["maximum_dispersion_ratio"]:
        return "review:count-dispersion"
    return "publish:scoped-model-reports"

limits = {"minimum_label_share": 0.92, "maximum_calibration_error": 0.06,
          "minimum_exposure_coverage": 0.96, "maximum_dispersion_ratio": 1.6}
binary = {"mature_label_share": 0.95, "calibration_error": 0.04}
counts = {"exposure_coverage": 0.83, "dispersion_ratio": 1.3}
assert claim_model_release(binary, counts, limits) == "hold:count-exposure"
assert claim_model_release(binary, {**counts, "exposure_coverage": 0.99},
                           limits) == "publish:scoped-model-reports"
''',
        'cost': 'The aggregate gate is O(1) time and space. Fitting, mature-label collection, exposure repair and dependence-aware intervals dominate effort. Combining two distinct reports into one approval can mask a faulty count denominator behind an acceptable binary classifier.',
        'mistakes': ['Describing an odds ratio as a risk ratio in the memo.', 'Comparing branch count totals without monitored claim-days.', 'Treating model-family changes as a fix for missing exposure.', 'Calling an observational coefficient a causal intervention result.'],
        'related': [A + 'logistic-model-odds-and-risk-interpretation', A + 'poisson-regression-offset-and-dispersion', A + 'poisson-count-rate-and-exposure', A + 'population-estimand-and-sampling-frame', 'machine-learning/probability-calibration'],
    },
]

crosslinks = [
    (A + 'confidence-interval-coverage', A + 'rare-proportion-wilson-interval'),
    (A + 'population-estimand-and-sampling-frame', A + 'poisson-count-rate-and-exposure'),
    (A + 'contact-center-survey-audit-project', A + 'warehouse-incident-rate-project'),
    (A + 'hypothesis-test-and-effect-size', A + 'minimum-detectable-effect-and-sample-plan'),
    (A + 'randomization-unit-and-experiment-design', A + 'cluster-attrition-and-power-budget'),
    (A + 'receipt-review-experiment-project', A + 'checkout-power-project'),
    ('machine-learning/logistic-regression-log-loss-and-odds', A + 'logistic-model-odds-and-risk-interpretation'),
    (A + 'regression-residuals-and-influence', A + 'poisson-regression-offset-and-dispersion'),
    (A + 'route-time-regression-review-project', A + 'claim-count-glm-project'),
]

if __name__ == '__main__':
    publish(lessons, [RATE, POWER, GLM], crosslinks,
            'aitrove-applied-statistics-rates-power-glm-import-20261006.json',
            8421, subject='applied-statistics', hub_path=A + 'applied-statistics-tutorial')
