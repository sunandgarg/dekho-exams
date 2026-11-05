"""Add regression-inference and paired-design modules to Applied Statistics."""
from de_batch_publisher import publish

A = 'applied-statistics/'
REG = 'Regression inference and prediction limits'
PAIR = 'Paired designs and randomization checks'
lessons = [
    {
        'path': A + 'linear-regression-estimand-and-slope',
        'title': 'Linear regression slopes: define the comparison a coefficient makes',
        'module': REG, 'project': False,
        'summary': 'An ordinary least-squares slope summarizes a conditional linear association, with an interpretation tied to its units and design.',
        'sections': [
            ('Start with the target', 'A courier team records route distance and delivery minutes. Before fitting a line, define whether the target is average minutes for the sampled routes, a prediction for a future route, or the change that would result from altering distance. The first two can be studied from observed pairs; the last needs a causal design. State the route population, measurement window and units. [[applied-statistics/population-estimand-and-sampling-frame|The estimand lesson]] prevents a tidy coefficient from answering the wrong operational question.'),
            ('Read the fitted slope narrowly', 'In a one-predictor line, the slope is the change in fitted mean minutes per additional distance unit within the observed range. The intercept is the fitted value at distance zero, which can be outside the data and physically meaningless. With multiple predictors, a coefficient compares observations at fixed values of the included predictors; that condition may be implausible if the fields move together. Do not convert association into an intervention claim. [[causal-inference/confounder-graph-and-covariate-timing|A confounder graph]] gives a better starting point for that question.'),
            ('Inspect support before inference', 'Plot or tabulate distances, route types and observed times. A single distant route can set the apparent slope. A narrow distance range can produce unstable extrapolation. Fit on a declared training period; assess residuals and out-of-period error before trusting a release. [[applied-statistics/regression-residuals-and-influence|Residual checks]] separate a good-looking line from a usable error model. [[machine-learning/regression-baselines-and-holdout-metrics|A holdout baseline]] addresses prediction, while a coefficient interval addresses sampling uncertainty under model assumptions.'),
            ('Keep the arithmetic reproducible', 'For a single predictor with nonzero variation, divide the centered cross-product by the centered distance sum of squares; subtract slope times mean distance from mean time to get the intercept. Save the exact rows and filtering rule. The tiny calculation below is for inspection, not a substitute for a design-aware standard error. If several routes belong to the same depot, route-level independence is suspect; [[applied-statistics/cluster-bootstrap-and-standard-error|clustered uncertainty]] uses the depot as the sampling unit.'),
        ],
        'code': '''def fit_route_line(distances, minutes):
    if len(distances) != len(minutes) or len(distances) < 2:
        raise ValueError("paired route observations required")
    distance_mean = sum(distances) / len(distances)
    minute_mean = sum(minutes) / len(minutes)
    denominator = sum((distance - distance_mean) ** 2 for distance in distances)
    if denominator == 0:
        raise ValueError("distance has no variation")
    slope = sum((distance - distance_mean) * (minute - minute_mean)
                for distance, minute in zip(distances, minutes)) / denominator
    return minute_mean - slope * distance_mean, slope

intercept, slope = fit_route_line([2, 4, 6, 8, 10], [5, 9, 10, 15, 17])
assert round(intercept, 6) == 2.2
assert round(slope, 6) == 1.5
''',
        'cost': 'The one-predictor calculation is O(n) time and O(1) extra space for n routes. General regression solvers use matrix methods whose cost depends on row count and feature count. Computing a coefficient is cheap; obtaining credible uncertainty requires a sampling design, dependence check and enough support in the distances of interest.',
        'mistakes': ['Calling the observational slope the effect of sending a driver farther.', 'Interpreting an intercept far outside observed route distances.', 'Reporting a precise slope after filtering influential routes without a declared rule.', 'Treating repeated routes from one depot as independent samples.'],
        'related': [A + 'regression-residuals-and-influence', A + 'mean-response-vs-prediction-interval', A + 'population-estimand-and-sampling-frame', A + 'cluster-bootstrap-and-standard-error', 'machine-learning/regression-baselines-and-holdout-metrics'],
    },
    {
        'path': A + 'regression-residuals-and-influence',
        'title': 'Regression diagnostics: residual pattern, scale and influential routes',
        'module': REG, 'project': False,
        'summary': 'Residual checks ask whether a fitted mean, error spread and individual observations support the intended inference.',
        'sections': [
            ('Check the shape of error', 'A residual is observed delivery time minus the fitted time. Plot it against fitted time, distance, depot and calendar order. Curvature suggests that one straight slope misses structure; widening spread means a constant-error-scale model is questionable. Time ordering can reveal a shared disruption. A normal-looking histogram cannot repair an omitted depot effect or route dependence. [[applied-statistics/linear-regression-estimand-and-slope|The slope interpretation]] is limited by these design and model conditions.'),
            ('Separate unusual outcomes from influence', 'A route can have a large residual but ordinary distance, or extreme distance with enough influence to move the line substantially. Refit after removing an identified route as a sensitivity check, then report both fits and investigate the record; do not delete it because it is inconvenient. Compare input provenance, sensor failure and legitimate long-distance service. [[applied-statistics/distribution-quantiles-and-outlier-policy|The outlier policy]] should exist before inspecting its effect on a favorable coefficient.'),
            ('Choose the response to a failure', 'If residual spread increases with distance, a transformation, weighted model or heteroskedasticity-aware uncertainty may be appropriate, depending on the question. If depots share shocks, use a depot-aware design or clustered uncertainty. If the relationship bends, fit an approved richer mean model and compare out-of-period error. These changes solve different problems; one fix does not automatically solve the others. [[applied-statistics/cluster-bootstrap-and-standard-error|Cluster resampling]] addresses dependence, and [[applied-statistics/mean-response-vs-prediction-interval|interval design]] depends on the error question.'),
            ('Publish the diagnostic boundary', 'Save residual summaries by distance band and depot, a sensitivity refit for influential routes, the sample size and every exclusion rule. A small residual average is expected after fitting an intercept and is not a quality certificate. Report an error measure that cannot cancel positive and negative mistakes. [[applied-statistics/route-time-regression-review-project|The route review project]] rejects a candidate whose pooled fit hides rising errors on long trips.'),
        ],
        'code': '''def route_error_bands(observed, fitted, distance, cut_off):
    if not (len(observed) == len(fitted) == len(distance)):
        raise ValueError("route columns differ in length")
    bands = {"near": [], "far": []}
    for actual, predicted, km in zip(observed, fitted, distance):
        bands["near" if km <= cut_off else "far"].append(abs(actual - predicted))
    return {name: (sum(errors) / len(errors) if errors else None)
            for name, errors in bands.items()}

report = route_error_bands([5, 9, 10, 15, 17],
                           [5.2, 8.2, 11.2, 14.2, 17.2],
                           [2, 4, 6, 8, 10], 6)
assert round(report["near"], 6) == round(2.2 / 3, 6)
assert round(report["far"], 6) == 0.5
''',
        'cost': 'The band summary is O(n) time and O(n) stored absolute errors; streaming totals would reduce extra storage to O(1) for two bands. Refit-based influence checks cost at least one additional model fit per tested deletion. Diagnostic work is justified when a seemingly small aggregate error might conceal an expensive route segment.',
        'mistakes': ['Using mean signed residual as evidence of accurate predictions.', 'Deleting the point that changes the slope without investigating its provenance.', 'Treating a normal residual histogram as proof of independence.', 'Applying a variance fix to a curved mean relationship and claiming both issues are solved.'],
        'related': [A + 'linear-regression-estimand-and-slope', A + 'mean-response-vs-prediction-interval', A + 'route-time-regression-review-project', A + 'distribution-quantiles-and-outlier-policy', 'machine-learning/regression-error-slices-and-tail-cost'],
    },
    {
        'path': A + 'mean-response-vs-prediction-interval',
        'title': 'Mean-response and prediction intervals: identify whose uncertainty is covered',
        'module': REG, 'project': False,
        'summary': 'An interval for a fitted average route time is narrower than an interval for one future route under the same error model.',
        'sections': [
            ('Name the interval target', 'The dispatcher asks for the mean time of routes at seven distance units; a driver asks what one future route might take. The first is a confidence interval for a conditional mean. The second is a prediction interval and includes both uncertainty in the estimated mean and variability of individual routes. Report the target, distance, data range and probability procedure in the same sentence. [[applied-statistics/confidence-interval-coverage|Coverage]] concerns repeated use of a method, not a probability that a fixed observed interval contains its fixed parameter.'),
            ('Inspect the width terms', 'In a simple-line model, uncertainty about the fitted mean grows away from the sample mean distance. For a new route, add an individual-error term under the square root, so the prediction interval is wider at the same distance. The formula below accepts a critical multiplier chosen for the degrees of freedom and desired coverage; it does not estimate that multiplier. It assumes a straight conditional mean and an appropriate error model. [[applied-statistics/regression-residuals-and-influence|Residual diagnostics]] decide whether the assumptions deserve use.'),
            ('Guard the deployment boundary', 'Do not use a mean interval as a customer-facing arrival window. In sparse long-distance bands, uncertainty can be wider than the pooled result suggests, and extrapolating beyond observed distances is a different risk. Compare realized prediction coverage on held-out routes, including distance bands and depots. If empirical coverage fails, investigate conditional error spread, dependence and shift before widening a number mechanically. [[machine-learning/interval-coverage-by-operating-slice|Slice coverage checks]] complement the statistical formula.'),
            ('Record the decision cost', 'A prediction interval may be operationally too wide to promise a delivery time. That is a finding, not a reason to relabel it as a confidence interval. Route more uncertain cases to a broad ETA message or collect more representative routes. [[applied-statistics/route-time-regression-review-project|The project]] distinguishes a precise average estimate from a safe individual commitment; [[applied-statistics/population-estimand-and-sampling-frame|the population frame]] decides which future routes the check may represent.'),
        ],
        'code': '''from math import sqrt

def route_interval_halfwidths(distances, residual_sd, target_distance, critical):
    if len(distances) < 3 or residual_sd < 0 or critical <= 0:
        raise ValueError("invalid line interval inputs")
    center = sum(distances) / len(distances)
    spread = sum((distance - center) ** 2 for distance in distances)
    if spread == 0:
        raise ValueError("no distance variation")
    mean_factor = 1 / len(distances) + (target_distance - center) ** 2 / spread
    return (critical * residual_sd * sqrt(mean_factor),
            critical * residual_sd * sqrt(1 + mean_factor))

mean_width, route_width = route_interval_halfwidths(
    [2, 4, 6, 8, 10], 1.2, 7, 2.78)
assert route_width > mean_width > 0
''',
        'cost': 'Computing centered spread takes O(n) time and O(1) extra space; a fitted model can reuse this statistic. A model-based interval is cheap to calculate but can be misleading when residual spread changes with distance or route observations are dependent. Out-of-period coverage checks require enough fresh, labeled routes in each operating slice.',
        'mistakes': ['Presenting a mean-response interval as a range for one new route.', 'Interpreting an interval’s confidence level as a posterior probability about a fixed parameter.', 'Using the line formula well outside the sampled distance range.', 'Reporting nominal coverage without checking held-out route slices.'],
        'related': [A + 'linear-regression-estimand-and-slope', A + 'regression-residuals-and-influence', A + 'route-time-regression-review-project', A + 'confidence-interval-coverage', 'machine-learning/interval-coverage-by-operating-slice'],
    },
    {
        'path': A + 'route-time-regression-review-project',
        'title': 'Project: audit a route-time regression before promising arrivals',
        'module': REG, 'project': True,
        'summary': 'Fit a route-time association, inspect long-trip errors and separate a mean estimate from an individual ETA.',
        'sections': [
            ('Define the release question', 'A delivery team wants one number for arrival estimates. State two targets: average route minutes at a chosen distance and an interval for a future route. Extract routes from a declared period, preserve depot IDs, and record the observed distance range. Keep future weeks out of fitting. A coefficient is not the effect of forcing a courier to travel farther; route selection and traffic differ. [[applied-statistics/linear-regression-estimand-and-slope|The coefficient lesson]] fixes the estimand.'),
            ('Inspect the candidate', 'Fit a single-distance line and compare it with a constant-time baseline. Inspect residuals by distance band, depot and week. One unusually long route has both high influence and a possible scan error. Verify the original record before comparing fits with and without it; retain both results in the review packet. A widening far-route error makes pooled mean absolute error an unsafe sole gate. [[applied-statistics/regression-residuals-and-influence|Diagnostics]] determine whether the line is adequate.'),
            ('Set the interval contract', 'Use a mean-response interval when planning average depot capacity and a prediction interval for an individual driver commitment. Calculate both at a distance supported by the sample. Check prediction coverage in held-out weeks and long-trip slices; a narrow formula interval with poor realized coverage is not ready for customers. If the long-trip data are thin, collect more routes or publish a broader message. [[applied-statistics/mean-response-vs-prediction-interval|Interval targets]] must not be swapped to meet a display requirement.'),
            ('Deliver a decision packet', 'Report rows by depot, distance support, baseline and candidate error, influential-record investigation, interval assumptions and held-out coverage. A failing long-distance gate holds customer ETA use even if the average line is useful for planning. Name the owner of the missing-data and route-quality follow-up. Link this review to [[machine-learning/regression-error-slices-and-tail-cost|tail cost]] and [[applied-statistics/cluster-bootstrap-and-standard-error|depot clustering]] before a later rollout.'),
        ],
        'code': '''def route_eta_release(report, limits):
    if report["future_week_used_in_fit"]:
        return "hold:time-leakage"
    if report["far_route_mae"] > limits["far_route_mae"]:
        return "hold:far-route-error"
    if report["heldout_coverage"] < limits["minimum_coverage"]:
        return "hold:interval-coverage"
    if not report["influential_route_checked"]:
        return "hold:route-provenance"
    return "release:individual-eta"

limits = {"far_route_mae": 7.5, "minimum_coverage": 0.87}
report = {"future_week_used_in_fit": False, "far_route_mae": 8.3,
          "heldout_coverage": 0.91, "influential_route_checked": True}
assert route_eta_release(report, limits) == "hold:far-route-error"
assert route_eta_release({**report, "far_route_mae": 6.8}, limits) == "release:individual-eta"
''',
        'cost': 'The gate is O(1) time and space after report preparation. Fitting and stratified evaluation cost O(n) or more depending on the model and diagnostic refits. Investigating an influential scan, collecting held-out weeks and labeling depot-specific failures are the main operational costs; a fast gate cannot replace that evidence.',
        'mistakes': ['Shipping a customer ETA from an interval for the mean route.', 'Using future weeks in fitting and then calling them a holdout.', 'Ignoring far-route error because pooled error improved.', 'Removing an influential route before checking whether its source record is valid.'],
        'related': [A + 'linear-regression-estimand-and-slope', A + 'regression-residuals-and-influence', A + 'mean-response-vs-prediction-interval', A + 'cluster-bootstrap-and-standard-error', 'machine-learning/regression-error-slices-and-tail-cost'],
    },
    {
        'path': A + 'paired-estimand-and-unit-matching',
        'title': 'Paired comparisons: analyze within-unit changes and preserve the match',
        'module': PAIR, 'project': False,
        'summary': 'A paired design compares two observations from each independent unit, so the differences—not the raw rows—form the analysis sample.',
        'sections': [
            ('Define the pair', 'A support team measures ticket resolution minutes under two interface variants for the same agent on matched shifts. The estimand is the mean within-agent change over the eligible agents and shift types. Join on a stable agent and shift key, then reject duplicate or incomplete pairs under a declared policy. Pairing removes stable agent differences from the comparison, but it does not erase a calendar shock that affects only one variant. [[applied-statistics/randomization-unit-and-experiment-design|Assignment design]] determines what the contrast can claim.'),
            ('Analyze differences, not pooled records', 'Compute candidate minus incumbent time for each complete pair. Then summarize the distribution of those differences, its average and its standard error over independent pairs. A negative difference favors the candidate when shorter resolution is desired. If one agent contributes many shifts, the shifts are not automatically independent; aggregate by agent or use a dependence-aware method. [[applied-statistics/cluster-bootstrap-and-standard-error|Cluster resampling]] handles repeated agents better than treating every shift as a new person.'),
            ('Understand what matching cannot fix', 'If agent behavior adapts after trying one interface, the second period can carry over the first. Counterbalance order when possible and record which variant came first. A matched before/after design without random assignment remains vulnerable to learning and workload changes. Inspect unmatched agents and why their pairs failed; excluding only difficult shifts changes the target population. [[applied-statistics/population-estimand-and-sampling-frame|The sampling frame]] should state who is represented.'),
            ('Use a design-compatible test', 'A paired sign-flip randomization check is appropriate only when the assignment mechanism or sharp-null symmetry supports exchangeability of signs. A paired t procedure asks a different distributional question about mean differences. Choose before inspecting favorable results. [[applied-statistics/paired-randomization-check|The randomization lesson]] gives the exact small-sample calculation, and [[applied-statistics/support-shift-paired-review-project|the project]] catches a duplicated agent key.'),
        ],
        'code': '''from math import sqrt

def paired_shift_summary(incumbent_minutes, candidate_minutes):
    if len(incumbent_minutes) != len(candidate_minutes) or len(incumbent_minutes) < 2:
        raise ValueError("at least two complete pairs required")
    changes = [candidate - incumbent for incumbent, candidate in
               zip(incumbent_minutes, candidate_minutes)]
    average = sum(changes) / len(changes)
    variance = sum((change - average) ** 2 for change in changes) / (len(changes) - 1)
    return {"pairs": len(changes), "mean_change": average,
            "standard_error": sqrt(variance / len(changes))}

summary = paired_shift_summary([31, 29, 35, 33], [27, 28, 30, 31])
assert summary["pairs"] == 4
assert summary["mean_change"] == -3
assert summary["standard_error"] > 0
''',
        'cost': 'Creating n pair differences is O(n) time and O(n) space; streaming mean and variance can use O(1) extra space. Matching and validating unique keys often cost more than the arithmetic. A false match can move the effect estimate and make its uncertainty appear much smaller than the design supports.',
        'mistakes': ['Running an unpaired test on rows that were deliberately matched.', 'Treating repeated shifts from one agent as independent agents.', 'Dropping incomplete pairs without reporting who was lost.', 'Calling a before/after difference causal without addressing period and order effects.'],
        'related': [A + 'paired-randomization-check', A + 'support-shift-paired-review-project', A + 'randomization-unit-and-experiment-design', A + 'cluster-bootstrap-and-standard-error', A + 'population-estimand-and-sampling-frame'],
    },
    {
        'path': A + 'paired-randomization-check',
        'title': 'Paired randomization checks: enumerate sign assignments under a sharp null',
        'module': PAIR, 'project': False,
        'summary': 'An exact sign-flip check compares a predeclared paired statistic with assignments permitted by the study design.',
        'sections': [
            ('State the null and assignment', 'Suppose each depot alternates two ticket interfaces across matched shifts and the interface order is randomized within each pair. Under a sharp null of no effect on any paired shift, the observed magnitude of each difference is fixed while its sign follows the randomized assignment. Enumerating those sign patterns gives a finite reference distribution. Without randomized sign assignment, treating the same enumeration as a design-based causal p-value needs an additional symmetry assumption. [[applied-statistics/paired-estimand-and-unit-matching|Pair construction]] is a prerequisite.'),
            ('Choose a statistic in advance', 'Use the absolute mean paired difference when a two-sided change matters. Count all assignments whose absolute statistic is at least as large as the observed one, including the observed assignment. Divide by the number of permitted assignments. With four nonzero pairs, the smallest two-sided p-value from this simple sign-flip scheme is two out of sixteen, so a conventional five-percent decision is impossible even if every difference points the same way. That resolution is a design limit, not weak code.'),
            ('Respect dependence and interference', 'If several shift pairs come from one depot and depot conditions move together, independently flipping every shift is not the assignment the experiment used. Flip or permute at the randomized unit. Spillover between interfaces can also break the sharp-null comparison. Inspect order, eligibility, exclusions and outcome timing before generating permutations. [[applied-statistics/randomization-unit-and-experiment-design|The unit lesson]] and [[applied-statistics/multiple-comparisons-and-stopping-rule|the stopping rule]] prevent an exact computation from being attached to a changed design.'),
            ('Report size as well as evidence', 'A p-value does not say how many minutes were saved. Report the paired mean or median difference, pair count, the complete distribution of differences and the predeclared statistic. A small design may yield an inconclusive test while still showing a range of practically important effects. [[applied-statistics/hypothesis-test-and-effect-size|Effect-size reporting]] keeps that uncertainty visible; [[applied-statistics/support-shift-paired-review-project|the project]] uses the check only after duplicate pairs are fixed.'),
        ],
        'code': '''from itertools import product

def paired_sign_flip_pvalue(differences):
    if not differences:
        raise ValueError("at least one pair required")
    observed = abs(sum(differences) / len(differences))
    extreme = 0
    total = 0
    for signs in product((-1, 1), repeat=len(differences)):
        total += 1
        permuted = abs(sum(sign * change for sign, change in
                           zip(signs, differences)) / len(differences))
        extreme += permuted >= observed - 1e-12
    return extreme / total

assert paired_sign_flip_pvalue([4, 3, 5, 2]) == 0.125
assert paired_sign_flip_pvalue([4, -3, 5, -2]) >= 0.125
''',
        'cost': 'Exact enumeration takes O(n × 2^n) time and O(n) space for n pairs. It is sensible for a small design but not hundreds of pairs; a prespecified Monte Carlo approximation can then estimate the tail probability. The computation does not repair wrong pairing, nonrandom assignment or hidden dependence.',
        'mistakes': ['Calling sign flips an exact randomized test when order was never randomized.', 'Flipping shifts independently when depots were the assigned units.', 'Choosing a one-sided direction after inspecting the differences.', 'Interpreting a p-value as the probability that the null is true.'],
        'related': [A + 'paired-estimand-and-unit-matching', A + 'support-shift-paired-review-project', A + 'hypothesis-test-and-effect-size', A + 'randomization-unit-and-experiment-design', A + 'multiple-comparisons-and-stopping-rule'],
    },
    {
        'path': A + 'support-shift-paired-review-project',
        'title': 'Project: compare support interfaces with complete agent-shift pairs',
        'module': PAIR, 'project': True,
        'summary': 'Validate matched shifts, calculate within-agent changes and reject an invalid independent-row significance claim.',
        'sections': [
            ('Freeze the paired design', 'A support desk tests two ticket interfaces on matched agent shifts. Assign interface order within each eligible pair, keep the ticket mix and timing rules, and predeclare resolution minutes as the outcome. The analysis unit is the matched agent-shift pair; if an agent contributes repeated shifts, dependence must be handled at the agent level. Save pair IDs and assignment order before outcomes arrive. [[applied-statistics/paired-estimand-and-unit-matching|The pairing contract]] defines which records belong together.'),
            ('Audit the join', 'The first export contains the same agent-shift key twice for the candidate interface and lacks an incumbent record for a night shift. A naïve row join multiplies one observation and makes the sample size look larger. Quarantine duplicate keys, report missing pairs and inspect whether missingness tracks night work. Do not silently keep whichever duplicate appears first. The complete-case estimate represents only retained pairs unless a defensible missing-data plan expands the target. [[data-science/missing-data-policy|Missing-data policy]] should be set before comparing outcomes.'),
            ('Compute a design-compatible comparison', 'Take candidate minus incumbent time for each validated pair; retain the full distribution, mean, standard error and pair count. If assignment was randomized within pairs and the sharp null is relevant, use the exact sign-flip check on independent assigned pairs. If the desk assigned one interface only after a training week, do not call that same calculation a design-based randomized test. [[applied-statistics/paired-randomization-check|The permutation calculation]] cannot supply randomization that never happened.'),
            ('Decide and hand off', 'Report order balance, duplicate and missing-key counts, mean minutes saved, uncertainty, ticket-type slices and a practical capacity threshold. A negative average can still hide long resolution times for complex tickets. Hold rollout if the night-shift loss is material or if the pair join remains ambiguous. Deliver the frozen export, matching rule and decision log; link follow-up to [[applied-statistics/hypothesis-test-and-effect-size|effect-size interpretation]] and [[applied-statistics/multiple-comparisons-and-stopping-rule|the stopping rule]].'),
        ],
        'code': '''def validate_shift_pairs(records):
    by_pair = {}
    for record in records:
        key = (record["agent_id"], record["shift_id"])
        slot = by_pair.setdefault(key, {})
        variant = record["variant"]
        if variant in slot:
            return "hold:duplicate-variant"
        slot[variant] = record["minutes"]
    if any(set(slot) != {"incumbent", "candidate"} for slot in by_pair.values()):
        return "hold:incomplete-pair"
    changes = [slot["candidate"] - slot["incumbent"]
               for slot in by_pair.values()]
    return sum(changes) / len(changes)

shifts = [
    {"agent_id": "agent-47", "shift_id": "am", "variant": "incumbent", "minutes": 31},
    {"agent_id": "agent-47", "shift_id": "am", "variant": "candidate", "minutes": 27},
    {"agent_id": "agent-82", "shift_id": "pm", "variant": "incumbent", "minutes": 29},
    {"agent_id": "agent-82", "shift_id": "pm", "variant": "candidate", "minutes": 28},
]
assert validate_shift_pairs(shifts) == -2.5
assert validate_shift_pairs(shifts + [shifts[-1]]) == "hold:duplicate-variant"
''',
        'cost': 'The dictionary join is O(n) expected time and O(n) space for n shift records. A production review must also check repeated-agent dependence and the reason pairs are missing. Cleaning the join and obtaining comparable shifts cost more than computing a mean; skipping them can turn a duplicate into false precision.',
        'mistakes': ['Joining on agent alone and creating many-to-many matches.', 'Keeping a duplicate variant because its value looks plausible.', 'Treating repeated agent shifts as independent people.', 'Using a randomized-test label for a nonrandom before/after rollout.'],
        'related': [A + 'paired-estimand-and-unit-matching', A + 'paired-randomization-check', A + 'randomization-unit-and-experiment-design', A + 'hypothesis-test-and-effect-size', 'data-science/missing-data-policy'],
    },
]

crosslinks = [
    (A + 'population-estimand-and-sampling-frame', A + 'linear-regression-estimand-and-slope'),
    (A + 'distribution-quantiles-and-outlier-policy', A + 'regression-residuals-and-influence'),
    (A + 'confidence-interval-coverage', A + 'mean-response-vs-prediction-interval'),
    (A + 'randomization-unit-and-experiment-design', A + 'paired-estimand-and-unit-matching'),
    (A + 'hypothesis-test-and-effect-size', A + 'paired-randomization-check'),
    (A + 'receipt-review-experiment-project', A + 'support-shift-paired-review-project'),
]

if __name__ == '__main__':
    publish(lessons, [REG, PAIR], crosslinks,
            'aitrove-applied-statistics-regression-pairs-import-20261006.json',
            8408, subject='applied-statistics', hub_path=A + 'applied-statistics-tutorial')
