"""Add missing-outcome, study-synthesis, and standardization lessons."""
from de_batch_publisher import publish

A = 'applied-statistics/'
MISSING = 'Missing outcomes and sensitivity'
META = 'Combining independent studies'
STANDARD = 'Standardized rates and composition'

lessons = [
    {
        'path': A + 'missing-outcome-ledger-and-target-population',
        'title': 'Missing outcomes: count absence before choosing an estimator',
        'module': MISSING, 'project': False,
        'summary': 'An outcome analysis starts with the eligible frame, observed outcomes, and reasons that observations are absent.',
        'sections': [
            ('Separate eligibility from observation', 'A returns team tracks whether each approved refund was completed within its service window. The denominator is every eligible refund entering a mature cohort, including cases whose final status cannot be reconstructed. An export of only completed cases changes the population and can make processing look faster. Define entry date, eligibility, outcome window, extraction date, and missing-status reason before computing a percentage. [[applied-statistics/population-estimand-and-sampling-frame|The estimand and frame]] determine what the result can describe.'),
            ('Audit patterns in recorded variables', 'Count observed and missing outcomes by branch, intake week, priority, and handling channel. A difference in observation rates across these recorded fields warns that a complete-case average may be selected. It cannot prove that absence is unrelated to the unobserved outcome; that assumption cannot be read directly from the missing cells. The example counts a small segment ledger rather than filling gaps. [[data-science/missingness-mechanisms-and-observation-process|The observation-process lesson]] distinguishes reasons for absence from statistical labels.'),
            ('Choose the method for the claim', 'If observation can be explained by recorded covariates and every relevant group has a nonzero chance of observation, a weighted or model-based estimate may recover the target under those assumptions. If difficult refunds disappear because they are difficult, this assumption can fail even after conditioning. Record a plausible range for the unobserved outcome and carry it into the decision. [[applied-statistics/observation-probability-weighting-and-sensitivity|The weighting lesson]] makes the observed-data assumption visible; [[data-science/worst-case-bounds-for-missing-binary-outcomes|bounds]] require less belief but may be wide.'),
            ('Report the missingness itself', 'Deliver the eligible count, observed count, missing count, reasons, segment rates, and comparison of observed cases with all eligible cases. Then report the estimate and uncertainty under each stated assumption. A single filled value for each missing outcome hides model uncertainty and should not be presented as measured truth. The audit should also flag whether source-system changes altered which outcomes are visible. [[applied-statistics/refund-outcome-missingness-project|The project]] treats an apparent service improvement as provisional until those counts reconcile.'),
        ],
        'code': '''from collections import defaultdict

def observation_by_branch(refund_rows):
    counts = defaultdict(lambda: [0, 0])
    for branch_id, outcome_observed in refund_rows:
        if not branch_id:
            raise ValueError("branch ID required")
        counts[branch_id][0] += 1
        counts[branch_id][1] += bool(outcome_observed)
    return {branch: {"eligible": total, "observed": observed}
            for branch, (total, observed) in counts.items()}

ledger = observation_by_branch([("north", True), ("north", False),
                                ("south", True), ("south", True)])
assert ledger["north"] == {"eligible": 2, "observed": 1}
''',
        'cost': 'The ledger scan is O(n) time and O(g) space for n refunds and g branches. Reconstructing outcome history can cost much more than counting rows, but dropping absent outcomes cheaply changes the population. A more elaborate estimator does not rescue an incomplete eligibility ledger.',
        'mistakes': ['Dividing by observed outcomes instead of the eligible frame without saying so.', 'Calling missingness random because observed segments look similar.', 'Filling absent outcomes with one value and treating them as measured.', 'Comparing branches when their reporting systems have different capture rules.'],
        'related': [A + 'observation-probability-weighting-and-sensitivity', A + 'refund-outcome-missingness-project', A + 'population-estimand-and-sampling-frame', A + 'stratified-survey-estimate-and-population-weights', 'data-science/missingness-mechanisms-and-observation-process'],
    },
    {
        'path': A + 'observation-probability-weighting-and-sensitivity',
        'title': 'Observation weighting: state positivity and test missing-outcome shifts',
        'module': MISSING, 'project': False,
        'summary': 'Inverse observation weights can target an eligible population under measured-data assumptions, while a sensitivity shift tests departures.',
        'sections': [
            ('Estimate a chance of being seen', 'Suppose completed refund status is recovered for some but not all mature cases. Fit or specify an observation probability using variables recorded for every eligible refund, such as branch, intake week, and priority. Each observed case contributes inverse-probability weight, so under-observed groups receive more influence. The normalized weighted mean below uses observed outcomes and supplied probabilities; it does not estimate those probabilities. [[applied-statistics/missing-outcome-ledger-and-target-population|The eligible ledger]] is required first.'),
            ('Check positivity and unstable weights', 'If a branch and priority combination has no observed outcomes, weighting cannot identify its mean from that stratum. Very small observation probabilities create huge weights and unstable estimates. Report their distribution, effective weight concentration, and comparisons before and after any predeclared cap. A cap trades variance for possible bias and cannot be chosen solely because it produces a preferred result. [[applied-statistics/stratified-survey-estimate-and-population-weights|The survey-weight lesson]] describes related population weighting but a distinct sampling mechanism.'),
            ('Ask what measured variables miss', 'The estimate needs an assumption that, conditional on included recorded variables, observation does not depend on the unobserved outcome. That can fail if difficult refunds are less likely to have a final status even within every recorded group. For a binary on-time outcome, examine a range in which missing cases are less successful than comparable observed cases; a sensitivity shift or bound shows how much the decision depends on that belief. [[data-science/missing-not-at-random-sensitivity-analysis|The missing-not-at-random lesson]] makes such scenarios explicit.'),
            ('Present assumption and consequence together', 'Show the complete-case value, weighted value, missing fraction, probability-model variables, smallest probabilities, and sensitivity range on one decision page. Uncertainty must account for estimating observation probabilities, not just for averaging known weights. A precise point estimate with a fragile observation assumption is not a precise operating conclusion. [[applied-statistics/refund-outcome-missingness-project|The project]] refuses a branch comparison when an entire high-priority stratum is unseen.'),
        ],
        'code': '''def normalized_observation_mean(observed_outcomes, observation_probs):
    if not observed_outcomes or len(observed_outcomes) != len(observation_probs):
        raise ValueError("aligned observed outcomes required")
    if any(not 0 < probability <= 1 for probability in observation_probs):
        raise ValueError("each observation probability must be positive")
    weights = [1 / probability for probability in observation_probs]
    return sum(weight * outcome for weight, outcome in
               zip(weights, observed_outcomes)) / sum(weights)

assert normalized_observation_mean([6, 12], [0.5, 0.25]) == 10
''',
        'cost': 'The weighted mean is O(n) time and O(n) space as written; a streaming accumulator can use O(1) extra space. Fitting the observation model and its uncertainty costs more. A zero-probability stratum is an identification failure, not a performance issue solved by faster code.',
        'mistakes': ['Estimating observation probabilities only among observed cases.', 'Allowing zero or near-zero probabilities without a support audit.', 'Calling weighted results immune to outcome-dependent missingness.', 'Ignoring uncertainty in fitted weights or choosing a cap after seeing the result.'],
        'related': [A + 'missing-outcome-ledger-and-target-population', A + 'refund-outcome-missingness-project', A + 'stratified-survey-estimate-and-population-weights', A + 'survey-design-variance-and-psu', 'data-science/missing-not-at-random-sensitivity-analysis'],
    },
    {
        'path': A + 'refund-outcome-missingness-project',
        'title': 'Project: audit a refund service result with missing final outcomes',
        'module': MISSING, 'project': True,
        'summary': 'Rebuild eligible refund cohorts, audit observation probabilities, and show what unobserved outcomes could change.',
        'sections': [
            ('Freeze the cohort', 'A service report claims the on-time refund rate rose after a queue change. Define approved refunds entering before the reporting cutoff, the service-time clock, outcome maturity, and every final-status source. Keep records that lack a final outcome in the eligible frame. The first dashboard selected only completed refunds, a condition affected by the process under review. [[applied-statistics/missing-outcome-ledger-and-target-population|The missing-outcome ledger]] separates eligibility, maturity, and observation.'),
            ('Trace an uneven feed', 'A branch migrated its status feed midway through the study. High-priority refunds are more likely to be missing after the migration, so complete cases look faster even if service did not improve. Reconcile IDs across systems and compare observation rates by branch, week, priority, and queue. A segment with no observed final outcomes cannot be recovered by inverse weighting alone. Hold the estimate until support and source errors are addressed. [[applied-statistics/observation-probability-weighting-and-sensitivity|The weighting lesson]] makes this limit visible.'),
            ('Calculate several honest views', 'Produce the observed-case rate, a weighted rate under a stated measured-data observation model, and a range under worse outcomes among missing cases. Include uncertainty from branch grouping and fitted observation probabilities. The figures answer different questions and should not be averaged into a single release number. If the weighted estimate and plausible missing-outcome scenarios disagree about the target, the dashboard cannot claim a settled improvement. [[data-science/worst-case-bounds-for-missing-binary-outcomes|Bounds]] show the broadest assumption-light range.'),
            ('Deliver a gated decision', 'The packet includes the eligible frame, outcome maturity, source reconciliation, missingness reasons, observation model, probability support, sensitivity assumptions, and branch-aware uncertainty. The gate below blocks a public claim if any structural absence or unmatched feed remains. It does not certify the weighted estimate; statistical review must still judge the observation assumption. [[applied-statistics/cluster-bootstrap-and-standard-error|The clustering lesson]] identifies the independent branch unit for uncertainty.'),
        ],
        'code': '''def refund_missingness_gate(audit, limits):
    if audit["unmatched_status_ids"]:
        return "hold:source-reconciliation"
    if audit["unobserved_priority_strata"]:
        return "hold:positivity"
    if audit["minimum_observation_probability"] < limits["minimum_probability"]:
        return "review:unstable-weights"
    if not audit["missing_outcome_sensitivity_done"]:
        return "hold:sensitivity"
    return "review:scoped-service-result"

limits = {"minimum_probability": 0.12}
audit = {"unmatched_status_ids": 2, "unobserved_priority_strata": 0,
         "minimum_observation_probability": 0.28,
         "missing_outcome_sensitivity_done": True}
assert refund_missingness_gate(audit, limits) == "hold:source-reconciliation"
assert refund_missingness_gate({**audit, "unmatched_status_ids": 0},
                               limits) == "review:scoped-service-result"
''',
        'cost': 'The gate is O(1). Reconstructing statuses is O(n) expected time with keyed lookups, while model fitting and resampling add cost. A dashboard built only from completed cases is faster because it discards the very outcomes most capable of changing the claim.',
        'mistakes': ['Treating unresolved statuses as successful refunds.', 'Fitting weights for a stratum with no observed outcomes.', 'Publishing one weighted rate without its missing-data assumption.', 'Ignoring branch-level correlation when reporting uncertainty.'],
        'related': [A + 'missing-outcome-ledger-and-target-population', A + 'observation-probability-weighting-and-sensitivity', A + 'cluster-bootstrap-and-standard-error', A + 'population-estimand-and-sampling-frame', 'data-science/worst-case-bounds-for-missing-binary-outcomes'],
    },
    {
        'path': A + 'study-effect-scale-and-precision',
        'title': 'Combining studies: align effects, units, and independent evidence',
        'module': META, 'project': False,
        'summary': 'A weighted study summary is meaningful only when each input estimates a compatible effect on the same scale.',
        'sections': [
            ('Define the study-level question', 'Several warehouses test a revised picking route, and each reports the difference in mean scan time between assigned policies. Before combining estimates, fix candidate minus incumbent, the time unit, eligible shipment type, follow-up window, and assignment unit. A study of median delivery delay or a ratio of failure risks is not interchangeable with a mean-time difference. Multiple reports from the same warehouse pilot may reuse participants and are not independent studies. [[applied-statistics/population-estimand-and-sampling-frame|The estimand lesson]] prevents an attractive numerical average of unlike quantities.'),
            ('Use precision without erasing design', 'Under a common-effect model with independent, compatible estimates and known variances, each study contributes inverse-variance weight. More precise studies exert more influence. The code below computes only that weighted point estimate; it does not test whether the common-effect assumption is credible or calculate a confidence interval. A warehouse with thousands of correlated shipments can report a falsely tiny standard error if it ignores route-level assignment. [[applied-statistics/cluster-bootstrap-and-standard-error|Cluster-aware uncertainty]] must be fixed inside each study before synthesis.'),
            ('Audit overlap and reporting selection', 'Build a registry of sites, dates, intervention versions, shipment eligibility, effect definitions, and raw data overlap. Count the same pilot once even if it appears in two reports. Look for completed but missing studies and unpublished unfavorable outcomes. A mathematically exact weighted mean cannot repair selective availability of results. Separate randomized from observational contrasts and explain why their estimands can or cannot be combined. [[applied-statistics/study-heterogeneity-and-new-site-risk|The heterogeneity lesson]] addresses differences among underlying effects.'),
            ('Report what the average can say', 'Show each study estimate and uncertainty, the harmonization decisions, and the weighted result under a named model. If effects vary materially by site, a common estimate may be too narrow a summary for a new warehouse. Report a new-site range or state that the available studies do not support transport. [[applied-statistics/warehouse-evidence-synthesis-project|The project]] catches a duplicate pilot and a scale mismatch before either enters the release packet.'),
        ],
        'code': '''def common_effect_mean(study_effects, study_variances):
    if not study_effects or len(study_effects) != len(study_variances):
        raise ValueError("aligned study estimates required")
    if any(variance <= 0 for variance in study_variances):
        raise ValueError("positive study variances required")
    weights = [1 / variance for variance in study_variances]
    return sum(effect * weight for effect, weight in
               zip(study_effects, weights)) / sum(weights)

combined = common_effect_mean([-1.2, -0.6], [0.16, 0.25])
assert round(combined, 6) == round(-9.9 / 10.25, 6)
''',
        'cost': 'The weighted mean is O(k) time and O(k) space for k studies as written. Harmonizing outcomes, verifying non-overlap, and auditing each variance usually dominate effort. Adding more reports cheaply can add no independent information when they reuse the same pilot.',
        'mistakes': ['Pooling seconds with percentage changes without conversion and a shared estimand.', 'Counting two reports of one pilot as two independent studies.', 'Using row-independent standard errors from cluster-assigned warehouses.', 'Treating a common-effect average as a prediction for a new site.'],
        'related': [A + 'study-heterogeneity-and-new-site-risk', A + 'warehouse-evidence-synthesis-project', A + 'cluster-bootstrap-and-standard-error', A + 'confidence-interval-coverage', A + 'population-estimand-and-sampling-frame'],
    },
    {
        'path': A + 'study-heterogeneity-and-new-site-risk',
        'title': 'Study heterogeneity: separate a mean effect from a new-site effect',
        'module': META, 'project': False,
        'summary': 'Between-study variation widens uncertainty for a future setting even when the average effect is estimated precisely.',
        'sections': [
            ('Distinguish two sources of spread', 'Warehouse pilots differ because of finite samples and because site operations may produce genuinely different route effects. Within-study variance quantifies uncertainty in each estimate; between-study variance describes dispersion of underlying site effects under a random-effects model. A precise average across several sites can coexist with a wide range of plausible effects at the next site. The code adds mean-estimation variance and between-site variance to show that difference; it does not calculate a calibrated prediction interval. [[applied-statistics/study-effect-scale-and-precision|Effect alignment]] comes first.'),
            ('Do not let one number replace inspection', 'A heterogeneity percentage or a fitted between-site variance is sensitive to the number and precision of available studies. With few sites, its estimate is unstable and an apparently zero value does not establish identical effects. Inspect each site result, route mix, equipment version, assignment method, and plausible effect modifiers. If the intervention was implemented differently, an average may not represent a coherent policy. [[applied-statistics/multilevel-variance-and-new-group-prediction|The multilevel lesson]] explains the analogous distinction between known and unseen groups.'),
            ('Keep the target of inference explicit', 'A confidence interval for the average underlying effect addresses the mean over the modeled set of sites. A prediction interval for a new comparable site must also allow between-site variation and uncertainty in its estimate, with careful treatment when the study count is small. A narrow average interval does not promise that every future deployment saves time. If the next warehouse has a different shipment mix, even the random-effects prediction may not transport. [[applied-statistics/standardized-rate-and-target-mix|Standardization]] can address measured mix changes, not unknown implementation differences.'),
            ('Tell the reviewer what changed', 'Report common-effect and heterogeneity-aware summaries as sensitivity analyses, not as a contest where the more favorable answer wins. Show site estimates, study count, between-site variance, mean interval, new-site interval when defensible, and reasons for any excluded report. The operational decision may require a limited local trial if the new-site range includes harm. [[applied-statistics/warehouse-evidence-synthesis-project|The synthesis project]] makes that release gate concrete.'),
        ],
        'code': '''from math import sqrt

def new_site_standard_deviation(mean_estimate_variance,
                                between_site_variance):
    if mean_estimate_variance < 0 or between_site_variance < 0:
        raise ValueError("variances cannot be negative")
    return sqrt(mean_estimate_variance + between_site_variance)

assert new_site_standard_deviation(0.25, 4.0) > 2
assert new_site_standard_deviation(0.25, 0.0) == 0.5
''',
        'cost': 'Combining two supplied variance components is O(1). Estimating between-site variance, checking compatibility, and calibrating a small-study prediction interval are the expensive steps. A simple average interval is cheaper but answers a narrower question than deployment risk.',
        'mistakes': ['Calling the confidence interval for the mean a range for every future site.', 'Declaring effects identical because fitted heterogeneity is zero in a tiny set.', 'Selecting a synthesis model after seeing which answer supports rollout.', 'Transporting a site range to a warehouse with a different implementation.'],
        'related': [A + 'study-effect-scale-and-precision', A + 'warehouse-evidence-synthesis-project', A + 'multilevel-variance-and-new-group-prediction', A + 'standardized-rate-and-target-mix', A + 'confidence-interval-coverage'],
    },
    {
        'path': A + 'warehouse-evidence-synthesis-project',
        'title': 'Project: combine warehouse pilots without double-counting evidence',
        'module': META, 'project': True,
        'summary': 'Harmonize route-time effects, remove overlapping reports, and judge uncertainty for a proposed new warehouse.',
        'sections': [
            ('Build a study inventory', 'A company has route-policy results from several warehouses. Record each site, dates, assignment, intervention version, eligible shipment class, effect scale, standard error, and report lineage. The release question is the effect of the current policy on mean scan time for a comparable new warehouse. One report uses minutes, another seconds, and a third is a revised analysis of the first pilot. Convert units only when the estimand matches, and keep one independent estimate per pilot. [[applied-statistics/study-effect-scale-and-precision|The alignment lesson]] supplies the first audit.'),
            ('Inspect rather than average immediately', 'Plot or list site effects with their uncertainty and note which warehouse had a scanner upgrade during the pilot. Recalculate variances for cluster assignment where needed. If an observational site used policy A only on difficult routes, its contrast targets a different question from randomized sites unless adjustment assumptions are defended. Do not let a precise but incompatible result dominate the weight. [[applied-statistics/cluster-bootstrap-and-standard-error|Correct independent units]] and [[applied-statistics/population-estimand-and-sampling-frame|compatible estimands]] are prerequisites.'),
            ('Report both mean and deployment risk', 'Compute a named average-effect analysis only for compatible studies, then examine between-site variation and a future-site range when the number of sites supports it. A favorable mean can coexist with a plausible slowdown at the next warehouse. Show how results change when the scanner-upgrade site is separated, and whether the proposed site resembles those studied. If few independent sites remain, frame the result as evidence for a monitored pilot rather than a guaranteed network-wide gain. [[applied-statistics/study-heterogeneity-and-new-site-risk|Heterogeneity]] is decision information.'),
            ('Publish an auditable packet', 'The packet includes the report-overlap map, unit conversions, effect definitions, variance corrections, included and excluded sites, chosen synthesis model, site-level results, and new-site caution. The gate below stops the synthesis before calculation if duplicate pilots or incompatible effects remain. A passing gate begins statistical review; it is not proof that transport or causal assumptions hold. [[applied-statistics/standardized-rate-and-target-mix|Target-mix work]] may be needed for a site with different routes.'),
        ],
        'code': '''def synthesis_gate(inventory, limits):
    if inventory["duplicate_pilots"]:
        return "hold:overlap"
    if inventory["unconverted_effect_scales"]:
        return "hold:effect-scale"
    if inventory["uncorrected_cluster_variances"]:
        return "hold:variance"
    if inventory["independent_sites"] < limits["minimum_sites"]:
        return "review:local-pilot-only"
    return "review:transport-assumptions"

limits = {"minimum_sites": 5}
inventory = {"duplicate_pilots": 1, "unconverted_effect_scales": 0,
             "uncorrected_cluster_variances": 0, "independent_sites": 6}
assert synthesis_gate(inventory, limits) == "hold:overlap"
assert synthesis_gate({**inventory, "duplicate_pilots": 0}, limits) \
       == "review:transport-assumptions"
''',
        'cost': 'The gate is O(1). The study inventory is O(k) over reports, but overlap detection and correction of site variances can require source-data review. Pooling the already reported point estimates is cheap precisely because it ignores those failure boundaries.',
        'mistakes': ['Double-counting a revised report as another pilot.', 'Converting units while leaving effect definitions incompatible.', 'Using a precise average as a guarantee for a new warehouse.', 'Including biased observational contrasts without a stated transport argument.'],
        'related': [A + 'study-effect-scale-and-precision', A + 'study-heterogeneity-and-new-site-risk', A + 'cluster-bootstrap-and-standard-error', A + 'population-estimand-and-sampling-frame', A + 'standardized-rate-and-target-mix'],
    },
]

lessons.extend([
    {
        'path': A + 'standardized-rate-and-target-mix',
        'title': 'Standardized rates: compare groups under one declared population mix',
        'module': STANDARD, 'project': False,
        'summary': 'Direct standardization applies stratum-specific rates to one shared target mix so composition does not decide the comparison.',
        'sections': [
            ('Define the common population', 'Two service centers handle different shares of routine and complex claims. Their crude escalation rates mix process performance with case composition, so a fair descriptive comparison needs a declared target distribution. Choose strata based on recorded severity before outcome review, define eligibility and outcome timing, and use the same target weights for both centers. The standardized rate is a weighted mean of each center’s stratum-specific rates. It is a comparison under the chosen mix, not the observed rate that either center actually experienced. [[applied-statistics/population-estimand-and-sampling-frame|The population lesson]] identifies who the weights represent.'),
            ('Check support before multiplying', 'Every target stratum with positive weight needs an estimable rate in each center. A missing complex-claim group cannot be filled with zero or quietly dropped while retaining the original weights. Sparse cells have large uncertainty even when the final weighted average looks smooth. Show counts and intervals for each rate, and choose a coarser grouping or an explicit model if support is inadequate. The program below only calculates a weighted point estimate from supplied rates. [[applied-statistics/rare-proportion-wilson-interval|Rare-proportion intervals]] help expose fragile cells.'),
            ('State what standardization does not solve', 'Holding observed severity mix constant removes one compositional difference in the descriptive calculation. It does not remove unmeasured complexity, different coding rules, or selection into each center. If severity is affected by the intervention, standardizing on it may change the causal question or introduce bias. Show crude, stratum-specific, and standardized rates side by side rather than presenting only the adjusted figure. [[applied-statistics/composition-reversal-and-stratum-audit|The reversal lesson]] demonstrates how crude ordering can contradict every within-stratum ordering.'),
            ('Carry uncertainty and choice of weights', 'Specify whether the target mix comes from an agreed reference period, a pooled current population, or a planned future workload. A different target mix can change the summary, so freeze it before ranking centers and disclose sensitivity to plausible alternatives. Use a variance method respecting how stratum rates and target weights were estimated. [[applied-statistics/claims-center-standardization-project|The project]] catches an absent complex stratum and a changed severity coding rule before releasing a benchmark.'),
        ],
        'code': '''def direct_standardized_rate(stratum_rates, target_weights):
    if set(stratum_rates) != set(target_weights):
        raise ValueError("rates required for every target stratum")
    if any(not 0 <= rate <= 1 for rate in stratum_rates.values()):
        raise ValueError("rates must lie between zero and one")
    if any(weight < 0 for weight in target_weights.values()) or \
       abs(sum(target_weights.values()) - 1) > 1e-9:
        raise ValueError("target weights must be nonnegative and sum to one")
    return sum(stratum_rates[group] * target_weights[group]
               for group in target_weights)

rate = direct_standardized_rate({"routine": 0.04, "complex": 0.12},
                                {"routine": 0.70, "complex": 0.30})
assert round(rate, 6) == 0.064
''',
        'cost': 'The weighted sum is O(s) time and O(1) extra space for s strata. Estimating each stratum rate and its uncertainty costs more, especially with sparse cells. A crude comparison is cheaper but can answer a different question when case mix differs.',
        'mistakes': ['Changing target weights after seeing which center wins.', 'Setting an absent stratum rate to zero.', 'Calling a standardized rate the observed workload rate.', 'Treating severity adjustment as proof of a causal service-center effect.'],
        'related': [A + 'composition-reversal-and-stratum-audit', A + 'claims-center-standardization-project', A + 'stratified-survey-estimate-and-population-weights', A + 'rare-proportion-wilson-interval', A + 'population-estimand-and-sampling-frame'],
    },
    {
        'path': A + 'composition-reversal-and-stratum-audit',
        'title': 'Composition reversal: reconcile crude and within-stratum comparisons',
        'module': STANDARD, 'project': False,
        'summary': 'An aggregate rate can reverse the ordering seen inside every recorded stratum when groups have different compositions.',
        'sections': [
            ('Read the cells before the headline', 'A candidate claims workflow can have lower escalation rates than an incumbent workflow for both routine and complex cases, yet a higher overall escalation rate if it receives many more complex cases. The crude summary is not an arithmetic error; it averages different stratum rates with different mixes. Ask whether the target is each workflow’s actual workload or a comparison under the same workload before choosing a headline. [[applied-statistics/standardized-rate-and-target-mix|Direct standardization]] expresses the second target.'),
            ('Calculate a concrete reversal', 'In the illustrative code, the candidate rates are two percent for routine and twelve percent for complex cases; the incumbent rates are three percent and fourteen percent. Candidate work is sixty percent complex, while incumbent work is twenty percent complex. Its crude rate is therefore higher despite being lower in each stratum. Under one shared half-routine, half-complex reference mix, the ordering follows the stratum-specific pattern. The numbers are invented for this lesson and do not identify a causal workflow effect. [[applied-statistics/population-estimand-and-sampling-frame|The estimand]] decides which comparison is relevant.'),
            ('Investigate why composition differs', 'Severity may have been measured before assignment, routed by staff, or recorded differently after the workflow change. Those histories have different implications. A pre-assignment severity variable can help describe like-with-like groups, but a variable changed by the workflow should not be adjusted away casually. Inspect missing severity labels and whether the same classification rules operated in both groups. Small or empty cells can make within-stratum rates unstable. [[applied-statistics/missing-outcome-ledger-and-target-population|Missingness audit]] extends to the variables that define strata.'),
            ('Publish both views with their denominators', 'Show counts, rates and uncertainty for every stratum, each group’s crude mix, the chosen reference mix, and the standardized result. Explain why the crude and standardized summaries differ rather than hiding one. If policy makers want to know expected volume for each center’s actual queue, crude rates may remain operationally important even while standardized rates support a fairer process comparison. [[applied-statistics/claims-center-standardization-project|The project]] tests whether all target strata are observed before accepting either rank.'),
        ],
        'code': '''def weighted_rate(routine_rate, complex_rate, complex_share):
    if not all(0 <= value <= 1 for value in
               (routine_rate, complex_rate, complex_share)):
        raise ValueError("rates and mix must lie between zero and one")
    return routine_rate * (1 - complex_share) + complex_rate * complex_share

candidate_crude = weighted_rate(0.02, 0.12, 0.60)
incumbent_crude = weighted_rate(0.03, 0.14, 0.20)
assert round(candidate_crude, 6) == 0.08
assert round(incumbent_crude, 6) == 0.052
assert weighted_rate(0.02, 0.12, 0.50) < \
       weighted_rate(0.03, 0.14, 0.50)
''',
        'cost': 'Each two-stratum rate is O(1) time and space; s strata take O(s). Data quality dominates computation: inconsistent severity coding or unsupported cells can invalidate a polished aggregate. The cheap crude rate remains useful for actual workload, but not as a like-for-like process comparison.',
        'mistakes': ['Calling a reversal a calculation bug without checking group composition.', 'Presenting only the standardized result while hiding actual workload rates.', 'Adjusting for a stratum created after the workflow change without a causal plan.', 'Ignoring small-cell uncertainty inside an apparently stable weighted average.'],
        'related': [A + 'standardized-rate-and-target-mix', A + 'claims-center-standardization-project', A + 'population-estimand-and-sampling-frame', A + 'rare-proportion-wilson-interval', A + 'missing-outcome-ledger-and-target-population'],
    },
    {
        'path': A + 'claims-center-standardization-project',
        'title': 'Project: compare claims centers under a shared severity mix',
        'module': STANDARD, 'project': True,
        'summary': 'Reconcile severity coding, absent cells and changing workload mix before ranking claims centers by escalation rate.',
        'sections': [
            ('Set the benchmark population', 'An operations lead wants to rank two claims centers by avoidable escalation rate. One center receives more complex claims. Freeze the eligible claim frame, escalation definition, observation window and pre-assignment severity classes, then choose a common reference distribution reflecting the future portfolio. Preserve each center’s actual workload mix for capacity planning. A standardized rate answers how rates compare under the reference mix, not how many escalations each center will handle tomorrow. [[applied-statistics/standardized-rate-and-target-mix|The standardization lesson]] defines the calculation.'),
            ('Catch a classification change', 'Midway through the quarter, one center changed its severity rule; claims previously marked complex became routine. The first export mixes old and new labels, so the stratum rates are not comparable. Reconstruct severity under one stable pre-outcome rule where possible and report the share that cannot be harmonized. One center has no observed claims in a small high-severity class. Do not insert a zero rate; combine classes only with a predeclared rationale or hold the comparison. [[applied-statistics/missing-outcome-ledger-and-target-population|The missingness ledger]] records classification gaps.'),
            ('Compare crude and common-mix estimates', 'Show actual counts and crude rates, then compute stratum rates and a direct standardized rate using the same weights for both centers. If ordering reverses, explain the composition arithmetic with denominators. Carry uncertainty from sparse rates and from any estimated target weights. Explore whether routing or staffing created additional unmeasured differences before suggesting a process change. [[applied-statistics/composition-reversal-and-stratum-audit|The reversal lesson]] explains why two valid summaries can answer different questions.'),
            ('Make the release decision auditable', 'The packet contains source-query version, case definitions, severity-rule history, observed support by center and stratum, reference weights, rate intervals and both crude and standardized results. The gate below blocks a ranking when an eligible reference stratum lacks support or the classification change remains unreconciled. A passing gate starts review; it cannot turn an observational center comparison into a randomized effect. [[applied-statistics/population-estimand-and-sampling-frame|The target frame]] and [[applied-statistics/rare-proportion-wilson-interval|small-cell uncertainty]] remain visible.'),
        ],
        'code': '''def claims_center_gate(audit, limits):
    if audit["severity_rule_unreconciled"]:
        return "hold:severity-contract"
    if audit["unsupported_target_strata"]:
        return "hold:target-support"
    if audit["smallest_stratum_count"] < limits["minimum_cell_count"]:
        return "review:sparse-cells"
    if not audit["reference_mix_predeclared"]:
        return "hold:reference-mix"
    return "review:scoped-center-comparison"

limits = {"minimum_cell_count": 23}
audit = {"severity_rule_unreconciled": 1,
         "unsupported_target_strata": 0, "smallest_stratum_count": 31,
         "reference_mix_predeclared": True}
assert claims_center_gate(audit, limits) == "hold:severity-contract"
assert claims_center_gate({**audit, "severity_rule_unreconciled": 0},
                          limits) == "review:scoped-center-comparison"
''',
        'cost': 'The gate is O(1), while assembling a stable case and severity ledger is O(n) expected time across claims. Standardization across s strata is O(s). A fast crude rank can be actively misleading when centers serve different case mixes.',
        'mistakes': ['Assigning zero to a severity class with no observations.', 'Mixing old and new severity definitions in the same stratum.', 'Publishing only adjusted rates while hiding actual queue burden.', 'Describing an observational adjusted contrast as a causal center effect.'],
        'related': [A + 'standardized-rate-and-target-mix', A + 'composition-reversal-and-stratum-audit', A + 'population-estimand-and-sampling-frame', A + 'rare-proportion-wilson-interval', A + 'missing-outcome-ledger-and-target-population'],
    },
])

crosslinks = [
    ('data-science/missingness-mechanisms-and-observation-process', A + 'missing-outcome-ledger-and-target-population'),
    ('data-science/missing-not-at-random-sensitivity-analysis', A + 'observation-probability-weighting-and-sensitivity'),
    ('data-science/delivery-scan-missingness-project', A + 'refund-outcome-missingness-project'),
    (A + 'confidence-interval-coverage', A + 'study-effect-scale-and-precision'),
    (A + 'multilevel-variance-and-new-group-prediction', A + 'study-heterogeneity-and-new-site-risk'),
    (A + 'warehouse-routing-rank-project', A + 'warehouse-evidence-synthesis-project'),
    (A + 'stratified-survey-estimate-and-population-weights', A + 'standardized-rate-and-target-mix'),
    (A + 'diagnostic-performance-and-prevalence', A + 'composition-reversal-and-stratum-audit'),
    (A + 'claims-audit-quality-project', A + 'claims-center-standardization-project'),
]

if __name__ == '__main__':
    publish(lessons, [MISSING, META, STANDARD], crosslinks,
            'aitrove-applied-statistics-missing-meta-standardization-import-20261007.json',
            8448, subject='applied-statistics', hub_path=A + 'applied-statistics-tutorial')
