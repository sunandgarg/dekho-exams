"""Add equivalence and multilevel-estimation curricula."""
from de_batch_publisher import publish

A = 'applied-statistics/'
E = 'Equivalence and noninferiority decisions'
G = 'Multilevel estimates and partial pooling'
T = 'Serial dependence and time-aware uncertainty'

lessons = [
    {
        'path': A + 'equivalence-margins-and-two-one-sided-decisions',
        'title': 'Equivalence margins: require the whole interval to fit',
        'module': E, 'project': False,
        'summary': 'Equivalence testing asks whether a difference is small enough in both directions under limits chosen before analysis.',
        'sections': [
            ('Define the quantity and both limits', 'A revised invoice-review screen should keep average review duration close enough to the incumbent that either direction of change is operationally acceptable. Define candidate minus incumbent in seconds, specify the eligible invoice population and commit to lower and upper acceptable differences before reading the pilot. A symmetric margin is convenient, but asymmetric limits can express different costs for a faster and a slower screen. [[applied-statistics/population-estimand-and-sampling-frame|The estimand and sampling frame]] fix what the difference represents.'),
            ('Reverse the usual burden of proof', 'A conventional difference test begins with zero difference as the null. Failing to reject it says only that the data are inconclusive for that test. An equivalence claim instead needs evidence that the true difference exceeds the lower limit and stays below the upper limit. At a five-percent level, a compatible two-one-sided procedure can be read from a valid two-sided ninety-percent confidence interval: the entire interval must fit strictly between both predeclared limits. The function below checks containment; it does not calculate the interval. [[applied-statistics/confidence-interval-coverage|Coverage assumptions]] still matter.'),
            ('Match uncertainty to assignment', 'If the same reviewer handles both interfaces on matched invoice batches, the interval must use within-reviewer differences rather than independent-row variance. If the pilot assigns whole branches, branch-level dependence belongs in the design and interval. Attrition, crossovers and a changed review clock can pull groups toward apparent similarity. Report both the assigned-group analysis and an adherence-sensitive analysis when those disruptions occur, with reasons for exclusions. [[applied-statistics/paired-estimand-and-unit-matching|Pairing]] and [[applied-statistics/cluster-bootstrap-and-standard-error|cluster resampling]] offer distinct routes, depending on assignment.'),
            ('Deliver a bounded claim', 'Successful containment supports equivalence only for the named endpoint, margin, population and observation window. It does not establish identical workflows, equal worst-case times or equivalence for error rates. Show the estimated difference, interval, limits, sample counts and missingness together. A wide interval crossing a limit is inconclusive even when its midpoint is near zero. [[applied-statistics/noninferiority-direction-and-analysis-sets|A one-sided harm limit]] answers another release question; [[applied-statistics/invoice-review-equivalence-project|the project]] joins the checks.'),
        ],
        'code': '''def equivalence_from_interval(lower_ci, upper_ci, lower_margin, upper_margin):
    if lower_ci > upper_ci or lower_margin >= upper_margin:
        raise ValueError("ordered interval and margins required")
    return lower_margin < lower_ci and upper_ci < upper_margin

assert equivalence_from_interval(-1.4, 1.8, -2.5, 2.5)
assert not equivalence_from_interval(-2.7, 1.2, -2.5, 2.5)
''',
        'cost': 'Interval containment is O(1) time and space. Constructing a valid interval can require O(n) data passes or repeated cluster resampling, while reviewer-level matching and incomplete cases must be audited first. The four comparisons cannot repair a biased pilot or a margin chosen after seeing results.',
        'mistakes': ['Calling a nonsignificant difference test proof of equivalence.', 'Changing the margin after seeing the estimate.', 'Using an invalid independent-row interval for a branch-assigned pilot.', 'Claiming every workflow outcome is equivalent from one average-duration endpoint.'],
        'related': [A + 'noninferiority-direction-and-analysis-sets', A + 'invoice-review-equivalence-project', A + 'confidence-interval-coverage', A + 'paired-estimand-and-unit-matching', A + 'minimum-detectable-effect-and-sample-plan'],
    },
    {
        'path': A + 'noninferiority-direction-and-analysis-sets',
        'title': 'Noninferiority: orient the harm margin before examining an interval',
        'module': E, 'project': False,
        'summary': 'A one-sided tolerance can rule out an unacceptable loss if the endpoint direction and analyzed population remain fixed.',
        'sections': [
            ('Put harm on the positive side', 'A new review interface may save staffing cost while allowing at most a small increase in missed duplicate invoices. Define the endpoint as candidate miss rate minus incumbent miss rate, so positive differences are harmful. A margin of 0.004 means four additional misses per thousand eligible invoices are the largest acceptable loss; that number must come from the operating decision, not the observed result. The unit and adjudication window must be identical across arms. [[applied-statistics/diagnostic-performance-and-prevalence|Miss-rate definitions]] require audited unflagged invoices.'),
            ('Test the boundary at issue', 'For this orientation, noninferiority requires a valid upper confidence bound for the difference below the positive harm margin. A point estimate below the margin is insufficient when its uncertainty crosses the boundary. If higher values are beneficial, reverse the contrast and use the corresponding lower bound instead. State whether the bound is one-sided and what error level it represents; do not silently substitute a two-sided interval with a different confidence level. [[applied-statistics/equivalence-margins-and-two-one-sided-decisions|Equivalence]] controls both directions, not only harm.'),
            ('Audit who remained in the comparison', 'An assigned-group analysis answers the effect of offering the new interface under pilot assignment, while a protocol-adherent analysis describes use among people who followed the workflow. Crossovers and exclusions can make groups look similar, which is dangerous when similarity is the desired finding. Keep an assignment ledger, predefine material deviations, show both analyses and explain disagreements instead of selecting the easier result. If review outcomes are still pending, delay the decision. [[applied-statistics/randomization-unit-and-experiment-design|The assignment unit]] determines the uncertainty structure.'),
            ('Separate tradeoffs from guardrails', 'A smaller staff cost does not compensate automatically for a miss-rate interval that still permits unacceptable harm. Report the cost saving and its uncertainty separately from the safety boundary. Add a high-severity error check and missing-adjudication table, because a single average miss rate may hide concentrated damage. The outcome is scoped to the pilot frame and period. [[applied-statistics/invoice-review-equivalence-project|The invoice project]] checks duration equivalence and error noninferiority together; [[applied-statistics/multiple-comparisons-and-stopping-rule|the decision-rule lesson]] handles added endpoints.'),
        ],
        'code': '''def noninferior_on_harm_scale(upper_difference_bound, harm_margin):
    if harm_margin <= 0:
        raise ValueError("harm margin must be positive")
    return upper_difference_bound < harm_margin

# Difference is candidate minus incumbent missed-duplicate rate.
assert noninferior_on_harm_scale(0.0026, 0.004)
assert not noninferior_on_harm_scale(0.0051, 0.004)
''',
        'cost': 'The boundary check is O(1). Obtaining a defensible bound costs at least O(n) data work and may require branch-level variance estimation. Counting only promptly adjudicated cases is cheaper but can bias the contrast toward noninferiority when difficult cases mature later.',
        'mistakes': ['Changing the sign of a difference without changing the decision rule.', 'Comparing only the point estimate with the margin.', 'Dropping crossovers or pending cases without a declared analysis plan.', 'Claiming no harm when the bound allows a loss beyond the agreed tolerance.'],
        'related': [A + 'equivalence-margins-and-two-one-sided-decisions', A + 'invoice-review-equivalence-project', A + 'randomization-unit-and-experiment-design', A + 'multiple-comparisons-and-stopping-rule', A + 'diagnostic-performance-and-prevalence'],
    },
    {
        'path': A + 'invoice-review-equivalence-project',
        'title': 'Project: decide whether an invoice workflow preserves speed and safety',
        'module': E, 'project': True,
        'summary': 'Run a two-endpoint release review with duration limits, a missed-duplicate harm margin and assignment-aware uncertainty.',
        'sections': [
            ('Lock the pilot before comparison', 'A finance team tests a revised invoice-review screen across branches. The proposed screen reduces routine handling cost, but the release rule requires review duration to remain inside a predeclared two-sided tolerance and missed-duplicate rate to stay below a one-sided harm allowance. Record eligible invoices, branch assignment, reviewer IDs, start and stop timestamps, duplicate adjudication window and planned sample sizes. The endpoints use different units and cannot be collapsed into one favorable score. [[applied-statistics/equivalence-margins-and-two-one-sided-decisions|Duration equivalence]] and [[applied-statistics/noninferiority-direction-and-analysis-sets|error noninferiority]] impose separate evidence requirements.'),
            ('Find the apparent-equivalence trap', 'The first export includes only completed reviews. The new interface has more unresolved complex invoices, so observed duration looks close to the incumbent while those hard cases are absent. Rebuild the eligible frame, account for incomplete reviews and report outcome maturity by arm. Branch-level assignment also means individual invoice rows are not independent randomized units. The first narrow interval counted every invoice as a fresh assignment; it must be replaced with branch-aware uncertainty. [[applied-statistics/cluster-attrition-and-power-budget|Cluster planning]] explains why the number of branches matters.'),
            ('Apply both boundaries without moving them', 'Compute a valid interval for candidate-minus-incumbent duration and require full containment inside the duration limits. Independently compute a bound on the missed-duplicate difference and require its upper edge below the permitted loss. Show assigned-group and adherence-sensitive estimates when staff switch screens. If those analyses disagree, identify the crossing pattern before claiming safety. Cost savings remain an additional result, not a way to offset a failed safety gate. [[applied-statistics/confidence-interval-coverage|Interval coverage]] depends on the extraction and grouping.'),
            ('Release a reviewable decision packet', 'The packet includes signed contrast definitions, margins and their operating rationale, branch and invoice counts, completion flow, both intervals, tail duration, severe misses and the source-query version. The gate below refuses release when either endpoint fails or cases remain unevaluated. It accepts precomputed interval decisions; it does not generate evidence. A failed gate calls for additional follow-up or redesign, not a narrower margin selected from the same results. [[applied-statistics/multiple-comparisons-and-stopping-rule|Additional outcomes and interim looks]] require their own plan.'),
        ],
        'code': '''def invoice_release_gate(packet):
    if packet["unresolved_outcomes"] or packet["missing_branch_ids"]:
        return "hold:data-contract"
    if not packet["duration_interval_inside_margins"]:
        return "hold:duration-equivalence"
    if not packet["miss_rate_upper_bound_below_margin"]:
        return "hold:duplicate-safety"
    if not packet["assignment_and_adherence_agree"]:
        return "review:analysis-set-disagreement"
    return "review:eligible-for-release"

packet = {"unresolved_outcomes": 0, "missing_branch_ids": 0,
          "duration_interval_inside_margins": True,
          "miss_rate_upper_bound_below_margin": False,
          "assignment_and_adherence_agree": True}
assert invoice_release_gate(packet) == "hold:duplicate-safety"
assert invoice_release_gate({**packet,
       "miss_rate_upper_bound_below_margin": True}) == "review:eligible-for-release"
''',
        'cost': 'The gate is O(1) time and space once interval results are audited. Building the packet is O(n) or more across invoices and branch clusters, and duplicate adjudication can dominate elapsed time. Reusing the completed-case export saves work only by silently changing the population being compared.',
        'mistakes': ['Publishing duration equivalence from completed cases alone.', 'Treating invoices as independently assigned when branches received the intervention.', 'Using cost savings to excuse a failed miss-rate safety bound.', 'Selecting the easier of two analyses after seeing results.'],
        'related': [A + 'equivalence-margins-and-two-one-sided-decisions', A + 'noninferiority-direction-and-analysis-sets', A + 'cluster-attrition-and-power-budget', A + 'confidence-interval-coverage', A + 'multiple-comparisons-and-stopping-rule'],
    },
    {
        'path': A + 'partial-pooling-and-small-group-estimates',
        'title': 'Partial pooling: stabilize small-group estimates without hiding variation',
        'module': G, 'project': False,
        'summary': 'A hierarchical estimate blends a noisy group mean with a shared mean according to their relative information.',
        'sections': [
            ('Name the population of groups', 'A service network reports average handling time for each depot. One depot has three observed shifts while another has forty-eight; treating the two raw averages as equally reliable invites a ranking dominated by noise. Under a simple normal model, depot means vary around a common center with between-depot variance, and observed shift times vary around each depot mean with within-depot variance. Partial pooling uses both sources of information. [[applied-statistics/population-estimand-and-sampling-frame|The sampling frame]] determines whether these depots represent the operating network.'),
            ('Make the shrinkage weight visible', 'For a group with n independent observations and known variances, the group mean receives weight n times between-group variance divided by that quantity plus within-group variance. The remainder weights the common center. A three-shift group is pulled more toward the center than a forty-eight-shift group under the same model. The code computes this conditional blend only; fitting variance components and uncertainty intervals is additional work. [[data-science/shared-priors-and-partial-pooling-limits|The shared-prior lesson]] shows why a common center can harm groups that do not exchange information plausibly.'),
            ('Do not mistake shrinkage for truth', 'Pooling helps against noisy extremes when the exchangeability model is credible. It can also erase a real depot problem if staffing, shipment class or equipment differs systematically. Inspect residuals and group-specific observed counts, then fit important predictors or separate incompatible groups before ranking. A group with zero observations receives the common mean as a model prediction, not a measured result. [[applied-statistics/multilevel-variance-and-new-group-prediction|Variance and new-group behavior]] need a separate report from fitted averages.'),
            ('Report what was borrowed', 'For each depot show raw average, pooled estimate, count, estimated between- and within-depot variation and uncertainty. Explain that an estimate pulled toward the center is conditional on the model and covariates, not an instruction to ignore a local complaint. Validate pooling by predicting held-out periods and checking whether small and large depots have credible errors. [[applied-statistics/depot-operations-pooling-project|The depot project]] catches a shifted operation that should not be smoothed into a healthy benchmark.'),
        ],
        'code': '''def pooled_depot_mean(depot_mean, shift_count, network_mean,
                      between_depot_variance, within_depot_variance):
    if shift_count < 0 or between_depot_variance <= 0 or within_depot_variance <= 0:
        raise ValueError("valid count and positive variances required")
    information = shift_count * between_depot_variance
    depot_weight = information / (information + within_depot_variance)
    return depot_weight * depot_mean + (1 - depot_weight) * network_mean

assert pooled_depot_mean(22, 3, 16, 4, 36) == 17.5
assert pooled_depot_mean(22, 48, 16, 4, 36) > 21
''',
        'cost': 'The conditional blend is O(1) per depot; all g depots cost O(g) time and output space. Fitting variance components and checking group predictors are the substantial modeling steps. A cheap average of all shifts can overrepresent large depots, while an unweighted average of depot means can overrepresent tiny ones.',
        'mistakes': ['Presenting a pooled estimate as the raw depot average.', 'Treating a zero-observation prediction as measured performance.', 'Assuming all depots are exchangeable despite equipment differences.', 'Ranking small depots without counts and interval uncertainty.'],
        'related': [A + 'multilevel-variance-and-new-group-prediction', A + 'depot-operations-pooling-project', A + 'cluster-bootstrap-and-standard-error', A + 'regression-residuals-and-influence', 'data-science/shared-priors-and-partial-pooling-limits'],
    },
    {
        'path': A + 'multilevel-variance-and-new-group-prediction',
        'title': 'Multilevel variance: separate within-group noise from new-group risk',
        'module': G, 'project': False,
        'summary': 'Random-intercept variation affects two observations from the same group and uncertainty for an unseen group.',
        'sections': [
            ('Distinguish two variance components', 'Suppose depot handling time has a shared network mean, a depot-specific deviation and shift-level noise. The between-depot variance describes how far depot baselines spread; the within-depot variance describes differences among shifts inside a depot after modeled predictors. Two shifts in one depot share the depot deviation and are correlated even if their shift noise is independent. The intraclass correlation is the between component divided by the sum of both components. [[applied-statistics/cluster-bootstrap-and-standard-error|The cluster lesson]] shows why dependence changes uncertainty.'),
            ('Predict known and new depots differently', 'For an observed depot, its shift history informs its deviation from the network mean and a partially pooled prediction can use that history. A newly opened depot has no measured deviation, so a prediction must include uncertainty from the between-depot distribution as well as future shift noise. Reusing an existing-depot interval for the new depot understates risk. The small program below calculates only a variance decomposition, not a predictive interval. [[applied-statistics/partial-pooling-and-small-group-estimates|The pooling lesson]] computes the conditional mean under a simple model.'),
            ('Respect the grouping map', 'A driver may work across depots, while a depot may serve multiple routes. Those factors are crossed, not a neat chain of drivers nested in one depot. One random-intercept term cannot automatically absorb every source of correlation; specify actual assignment and repeated-measure structure. Check that groups are distinct and variance estimates are identifiable with the observed number of depots. A near-zero estimated between-depot component may reflect sparse data or a misspecified mean. [[applied-statistics/regression-residuals-and-influence|Residual checks]] help find unmodeled patterns.'),
            ('Tie prediction to the decision', 'Report whether the target is network mean, a known depot or a future depot. Show both variance components, depot and shift counts, and uncertainty for the chosen target. A fixed list of observed depot effects may describe current sites without supporting predictions for new sites; a random-effect model adds distributional assumptions. Hold the operational ranking if group composition changed during collection. [[applied-statistics/depot-operations-pooling-project|The worked review]] adds a new depot and a mid-pilot equipment change.'),
        ],
        'code': '''def depot_intraclass_correlation(between_depot_variance,
                                 within_depot_variance):
    if between_depot_variance < 0 or within_depot_variance <= 0:
        raise ValueError("nonnegative group and positive shift variance required")
    return between_depot_variance / (
        between_depot_variance + within_depot_variance)

assert depot_intraclass_correlation(9, 16) == 0.36
assert depot_intraclass_correlation(0, 16) == 0
''',
        'cost': 'The ratio is O(1) time and space. Estimating components needs repeated work across shifts and groups; prediction for new groups needs an interval method. Ignoring group covariance makes a report cheap but can make its confidence intervals far too narrow.',
        'mistakes': ['Using a known-depot prediction interval for an unseen depot.', 'Treating many shifts as many independent depot assignments.', 'Forcing crossed driver and depot structure into one nested group.', 'Calling a small group variance proof that depots are identical.'],
        'related': [A + 'partial-pooling-and-small-group-estimates', A + 'depot-operations-pooling-project', A + 'cluster-bootstrap-and-standard-error', A + 'regression-residuals-and-influence', A + 'population-estimand-and-sampling-frame'],
    },
    {
        'path': A + 'depot-operations-pooling-project',
        'title': 'Project: rank depot handling time with group-aware uncertainty',
        'module': G, 'project': True,
        'summary': 'Review small depots, a new-site prediction and a mid-pilot equipment change before publishing performance ranks.',
        'sections': [
            ('Freeze the group and time ledger', 'A logistics team ranks depots by dispatch handling time. Define each eligible shift, depot, route mix, equipment state and measurement clock, then record which depots existed during the training period. Some depots contribute many shifts while newer ones contribute very few. Separate the target for comparing currently operating depots from the target for forecasting a future site. [[applied-statistics/partial-pooling-and-small-group-estimates|Partial pooling]] can stabilize small-group means, but its network center must refer to comparable sites.'),
            ('Find the broken pooling assumption', 'One depot replaced its scanner midway through the pilot. Its older shifts are much slower and belong to a different operating regime, yet the first model pools them as one stationary depot. Inspect timestamps, scanner versions, staffing and route mix; either model that change explicitly or limit comparison to a common regime. Keep raw and pooled estimates together. A smooth-looking ranking can conceal a real equipment problem. [[applied-statistics/regression-residuals-and-influence|Residual patterns]] are the warning, not a nuisance to average away.'),
            ('Evaluate two uncertainty targets', 'Estimate within- and between-depot variation, then report uncertainty for each existing depot and for a hypothetical newly opened depot. Predict on held-out later shifts by depot size; if pooled estimates fail on the changed-scanner depot, the exchangeability claim is weak. Compare ranking changes when that site is modeled separately. Do not call a new-site center a guaranteed operational baseline, because it has no local observations. [[applied-statistics/multilevel-variance-and-new-group-prediction|The variance lesson]] distinguishes known and unseen group risk.'),
            ('Publish a decision with limits attached', 'Deliver group counts, raw and pooled means, variance components, held-out error, equipment-change ledger and uncertainty intervals. The gate below blocks ranks if the group map or change record is incomplete. A high-rank depot with few shifts should be flagged for more observation rather than declared certainly best. A changed operating regime may require a second model and an explicit scope statement. [[data-science/shared-priors-and-partial-pooling-limits|Shared-prior limits]] and [[applied-statistics/cluster-bootstrap-and-standard-error|correct resampling units]] inform follow-up.'),
        ],
        'code': '''def depot_ranking_gate(audit, limits):
    if audit["missing_depot_ids"] or audit["unlogged_equipment_changes"]:
        return "hold:group-contract"
    if audit["depots_with_too_few_shifts"] > limits["maximum_sparse_depots"]:
        return "hold:small-group-support"
    if audit["late_holdout_error"] > limits["maximum_holdout_error"]:
        return "hold:future-fit"
    return "review:scoped-ranking"

limits = {"maximum_sparse_depots": 2, "maximum_holdout_error": 4.5}
audit = {"missing_depot_ids": 0, "unlogged_equipment_changes": 1,
         "depots_with_too_few_shifts": 1, "late_holdout_error": 3.2}
assert depot_ranking_gate(audit, limits) == "hold:group-contract"
assert depot_ranking_gate({**audit, "unlogged_equipment_changes": 0},
                          limits) == "review:scoped-ranking"
''',
        'cost': 'The gate is O(1), while the group ledger and held-out evaluation require at least O(n) work across shifts. Fitting hierarchical components is more expensive than raw averages, but the cheap rank can make a small depot look exceptional from a handful of noisy shifts.',
        'mistakes': ['Pooling old and new scanner regimes as one stable depot.', 'Publishing a rank without shift counts behind each estimate.', 'Using the same interval for observed and unseen depots.', 'Treating one low held-out error as proof that every depot is comparable.'],
        'related': [A + 'partial-pooling-and-small-group-estimates', A + 'multilevel-variance-and-new-group-prediction', A + 'cluster-bootstrap-and-standard-error', A + 'regression-residuals-and-influence', 'data-science/shared-priors-and-partial-pooling-limits'],
    },
]

lessons.extend([
    {
        'path': A + 'serial-correlation-and-effective-information',
        'title': 'Serial correlation: daily rows are not daily independent evidence',
        'module': T, 'project': False,
        'summary': 'Positive correlation across adjacent observations reduces information in a time series relative to independent rows.',
        'sections': [
            ('Define the regular observation clock', 'A returns team records a daily fraction of late refunds. Yesterday’s backlog affects today’s processing, so adjacent rates may move together. The day is an observation, but it is not automatically an independent replicate. Record reporting lag, missing days, weekday schedule, policy changes and denominator before estimating uncertainty. A series with trend or seasonality can show large apparent lag correlation even when its remaining errors follow a different pattern. [[data-science/interrupted-series-seasonality-and-residual-dependence|The interrupted-series lesson]] separates calendar structure from residual dependence.'),
            ('Use an approximation with a narrow scope', 'For a stationary AR(1)-like process with positive lag-one correlation rho, the rough effective sample size of a mean is n times one minus rho divided by one plus rho. Sixty daily values with rho 0.6 carry information resembling about fifteen independent values under that approximation. It is a diagnostic, not a replacement for an interval method. Negative or long-memory dependence, a moving mean, missing calendar days and changing variance defeat the simple formula. [[applied-statistics/confidence-interval-coverage|Interval coverage]] needs assumptions matching the actual series.'),
            ('Inspect the residual sequence', 'Fit planned mean and calendar effects first, then inspect residuals by date and lag. A random-looking marginal histogram can coexist with long positive runs. If an intervention started midway, check pre-period fit and transition lag rather than estimating one correlation across the level change. A conventional standard error that divides by the square root of every daily row can be much too small. [[applied-statistics/moving-block-bootstrap-and-block-length|A block bootstrap]] retains short runs of dependence when its stationarity conditions are defensible.'),
            ('State what can be inferred', 'Report the outcome definition, window, number of observed days, estimated lag structure and sensitivity to plausible dependence lengths. A change in daily average is an association unless assignment or a credible control supports causality. Do not turn a rough effective count into an exact p-value. [[applied-statistics/refund-delay-series-review-project|The project]] catches a policy launch where delayed refunds and a changed reporting feed both affect the apparent level.'),
        ],
        'code': '''def ar1_effective_days(observed_days, lag_one_correlation):
    if observed_days < 2 or not 0 <= lag_one_correlation < 1:
        raise ValueError("at least two days and nonnegative AR(1) correlation required")
    return observed_days * (1 - lag_one_correlation) / (
        1 + lag_one_correlation)

assert ar1_effective_days(60, 0.6) == 15
assert ar1_effective_days(60, 0) == 60
''',
        'cost': 'The approximation is O(1). Estimating correlation, testing residual structure and fitting a time-aware interval need O(n) or more work. Treating sixty correlated days as sixty independent assignments costs less computation but can make a weak change appear precise.',
        'mistakes': ['Using daily row count as independent sample size without checking dependence.', 'Applying the AR(1) approximation to trend or seasonal data as if exact.', 'Estimating correlation across an intervention step and calling it residual correlation.', 'Claiming causality from a before/after series without a credible design.'],
        'related': [A + 'moving-block-bootstrap-and-block-length', A + 'refund-delay-series-review-project', A + 'confidence-interval-coverage', A + 'cluster-bootstrap-and-standard-error', 'data-science/interrupted-series-seasonality-and-residual-dependence'],
    },
    {
        'path': A + 'moving-block-bootstrap-and-block-length',
        'title': 'Moving-block bootstrap: preserve local dependence in resampled series',
        'module': T, 'project': False,
        'summary': 'Resampling adjacent blocks instead of isolated days retains short-range order when estimating uncertainty from a stable series.',
        'sections': [
            ('Decide what may be exchanged', 'A daily operational series has short runs created by queue backlog. Ordinary row resampling breaks these runs and can understate uncertainty for a mean or stable-model residual statistic. A moving-block bootstrap samples contiguous windows and joins them to form a series of the original length. It assumes blocks from the prepared series are comparable after trend, weekday effects and known policy changes are addressed. [[applied-statistics/serial-correlation-and-effective-information|Serial dependence]] explains why the independent-row bootstrap is suspect.'),
            ('Choose a block length deliberately', 'A short block can miss dependence beyond its edge; a very long block leaves few distinct windows and unstable resamples. Declare a range of block lengths spanning the observed correlation scale, then show how the interval changes. The example samples circular blocks so every start date has a full window, wrapping from the last day to the first. That wrap is a computational convention, not evidence that final and first calendar days were adjacent in reality. [[applied-statistics/refund-delay-series-review-project|The project]] records this sensitivity before accepting a change claim.'),
            ('Resample the right object', 'If the target is a difference around a known intervention, resampling the entire raw series can shuffle observations across regimes and erase the design. Fit planned mean structure first and resample suitable residual blocks within stable segments or use another dependence-aware inference method. If a branch panel is involved, preserve both branch and time relationships rather than applying one-series blocks across all branches. The function demonstrates only a block draw; it does not produce a valid intervention interval by itself. [[data-science/controlled-interrupted-series-comparison|Controlled-series design]] remains separate.'),
            ('Keep failure modes visible', 'For each interval report the statistic, segment used for resampling, number of resamples, block-length range, seed and observed calendar gaps. Large seasonal cycles, rare regime changes and long-memory behavior may require a different model or longer follow-up. A narrow interval at one convenient block length is weak evidence if nearby lengths change the decision. [[applied-statistics/confidence-interval-coverage|Coverage claims]] apply only to the design and assumptions actually checked.'),
        ],
        'code': '''from random import Random

def circular_block_sample(daily_residuals, block_length, seed):
    size = len(daily_residuals)
    if size < 2 or not 1 <= block_length <= size:
        raise ValueError("block length must fit observed series")
    generator = Random(seed)
    resampled = []
    while len(resampled) < size:
        start = generator.randrange(size)
        resampled.extend(daily_residuals[(start + offset) % size]
                         for offset in range(block_length))
    return resampled[:size]

residuals = [1, 2, 3, 4, 5, 6, 7]
assert circular_block_sample(residuals, 3, 47) == \\
       circular_block_sample(residuals, 3, 47)
assert len(circular_block_sample(residuals, 3, 47)) == len(residuals)
''',
        'cost': 'One length-n draw takes O(n) time and O(n) space. B bootstrap draws cost O(Bn) time before recalculating the statistic. The expensive analytical step is deciding which residual segment is stable enough to resample and whether block lengths retain relevant dependence.',
        'mistakes': ['Resampling isolated daily rows from a dependent series.', 'Shuffling raw pre- and post-intervention observations together.', 'Choosing one block length only because it gives the desired interval.', 'Treating circular wraparound as literal adjacency in the operational calendar.'],
        'related': [A + 'serial-correlation-and-effective-information', A + 'refund-delay-series-review-project', A + 'cluster-bootstrap-and-standard-error', A + 'confidence-interval-coverage', 'data-science/controlled-interrupted-series-comparison'],
    },
    {
        'path': A + 'refund-delay-series-review-project',
        'title': 'Project: review a refund-delay change with correlated daily outcomes',
        'module': T, 'project': True,
        'summary': 'Audit a policy launch, reporting delay and calendar dependence before claiming a sustained reduction in late refunds.',
        'sections': [
            ('Freeze the daily measure', 'A returns team changed its triage policy on a recorded launch date. The proposed outcome is the fraction of eligible refunds completed late each day, based on the date each refund entered the queue. Capture daily eligible counts, completion maturity, weekdays, holidays, branch coverage and reporting-feed version. A calendar day with only a few mature cases is not comparable to a fully observed day with hundreds. [[applied-statistics/population-estimand-and-sampling-frame|The frame]] and [[applied-statistics/poisson-count-rate-and-exposure|exposure logic]] prevent denominator drift.'),
            ('Find two false improvements', 'The first chart shows fewer late refunds immediately after launch, but the new feed reports completed refunds two days later and the post period contains more weekends. Rebuild the outcome from matured cohorts, align calendar dates and model planned weekday effects. Inspect residual runs: backlog produces positive serial correlation even after calendar adjustment. A row-independent standard error is too small for the series. [[applied-statistics/serial-correlation-and-effective-information|The dependence lesson]] gives an information diagnostic, not a final test.'),
            ('Compare defensible uncertainty methods', 'If a stable residual segment remains after the predeclared mean model, evaluate a dependence-aware interval and compare it with a range of moving-block lengths. If the level change or seasonality remains in the resampled object, the bootstrap assumption fails and a model-based time-series approach or longer collection is needed. Show pre-period fit, transition lag, post-period duration and a placebo date check. A control series can help separate a system-wide refund shift from the policy. [[data-science/controlled-interrupted-series-comparison|The controlled-series lesson]] develops that contrast.'),
            ('Issue only the supported claim', 'Deliver the extraction version, daily counts, maturity lag, calendar model, residual diagnostics, effect estimate and intervals by method. The gate holds a result while reporting lag or post-launch coverage is unresolved. Even a stable time-aware interval does not prove the policy caused the change when other launches coincide. State the association and remaining competing explanations. [[applied-statistics/moving-block-bootstrap-and-block-length|Block-length sensitivity]] and [[data-science/interrupted-series-transition-and-lag-sensitivity|transition analysis]] remain in the review packet.'),
        ],
        'code': '''def refund_series_gate(audit, limits):
    if audit["unmatured_daily_cohorts"]:
        return "hold:outcome-maturity"
    if audit["feed_change_unreconciled"]:
        return "hold:reporting-contract"
    if audit["post_days"] < limits["minimum_post_days"]:
        return "hold:post-period-support"
    if not audit["calendar_and_dependence_checked"]:
        return "hold:serial-uncertainty"
    return "review:scoped-time-series-result"

limits = {"minimum_post_days": 47}
audit = {"unmatured_daily_cohorts": 0,
         "feed_change_unreconciled": True, "post_days": 63,
         "calendar_and_dependence_checked": True}
assert refund_series_gate(audit, limits) == "hold:reporting-contract"
assert refund_series_gate({**audit, "feed_change_unreconciled": False},
                          limits) == "review:scoped-time-series-result"
''',
        'cost': 'The gate is O(1); daily cohort reconstruction is at least O(n) over refund events, and B block-bootstrap draws require O(Bn) work on the prepared series. The audit is needed because a reporting-feed delay can impersonate a policy effect.',
        'mistakes': ['Dividing late completions by a denominator from a different cohort.', 'Treating weekends and weekdays as exchangeable raw observations.', 'Claiming policy causality from one uncontrolled before/after step.', 'Running a block bootstrap before resolving the reporting-feed break.'],
        'related': [A + 'serial-correlation-and-effective-information', A + 'moving-block-bootstrap-and-block-length', A + 'population-estimand-and-sampling-frame', 'data-science/controlled-interrupted-series-comparison', 'data-science/interrupted-series-transition-and-lag-sensitivity'],
    },
])

crosslinks = [
    (A + 'hypothesis-test-and-effect-size', A + 'equivalence-margins-and-two-one-sided-decisions'),
    (A + 'minimum-detectable-effect-and-sample-plan', A + 'noninferiority-direction-and-analysis-sets'),
    (A + 'receipt-review-experiment-project', A + 'invoice-review-equivalence-project'),
    ('data-science/shared-priors-and-partial-pooling-limits', A + 'partial-pooling-and-small-group-estimates'),
    (A + 'cluster-bootstrap-and-standard-error', A + 'multilevel-variance-and-new-group-prediction'),
    (A + 'route-time-regression-review-project', A + 'depot-operations-pooling-project'),
    ('data-science/interrupted-series-seasonality-and-residual-dependence', A + 'serial-correlation-and-effective-information'),
    ('data-science/controlled-interrupted-series-comparison', A + 'moving-block-bootstrap-and-block-length'),
    ('data-science/interrupted-series-policy-review-project', A + 'refund-delay-series-review-project'),
]

if __name__ == '__main__':
    publish(lessons, [E, G, T], crosslinks,
            'aitrove-applied-statistics-equivalence-pooling-series-import-20261007.json',
            8439, subject='applied-statistics', hub_path=A + 'applied-statistics-tutorial')
