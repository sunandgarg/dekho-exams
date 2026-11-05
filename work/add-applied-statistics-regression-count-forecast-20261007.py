"""Add Applied Statistics lessons on regression uncertainty, count models, and forecasting."""
from de_batch_publisher import publish

A = 'applied-statistics/'
REGRESSION = 'Regression uncertainty under changing variance'
COUNTS = 'Zero-heavy counts and operational exposure'
FORECAST = 'Time-ordered forecast evaluation'


def lesson(slug, title, module, summary, sections, code, cost, mistakes, related, project=False):
    return dict(path=A + slug, title=title, module=module, project=project,
                summary=summary, sections=sections, code=code, cost=cost,
                mistakes=mistakes, related=[A + path for path in related])


lessons = [
    lesson('heteroskedasticity-hc3-and-leverage',
        'Regression uncertainty: inspect changing residual spread and high influence', REGRESSION,
        'Heteroskedasticity changes error variance across observations; influence determines how strongly each row can shape a fitted regression.', [
            ('Define the coefficient before its standard error', 'A carrier analyst regresses route time on distance, parcel load, depot and schedule. The slope may describe a conditional association or a policy effect only under different design assumptions. Plot residuals against fitted time, distance, and depot before trusting the usual constant-variance standard error. A widening residual cloud suggests that long routes have different noise from short ones. [[applied-statistics/linear-regression-estimand-and-slope|The estimand lesson]] defines what the coefficient can represent; [[applied-statistics/regression-residuals-and-influence|residual diagnostics]] expose misspecification beyond changing variance.'),
            ('Separate a covariance repair from a model repair', 'An HC3-style heteroskedasticity-consistent covariance uses squared residuals scaled by influence, roughly dividing each residual by one minus its hat value before building the covariance matrix. The code calculates that ingredient, not a complete coefficient covariance. A variance-aware covariance can alter the uncertainty attached to the same fitted coefficients when errors are heteroskedastic, but it does not remove confounding, missing nonlinear structure, or dependence between repeated routes from one depot. A row with influence nearly one deserves direct inspection because its adjusted residual can dominate.'),
            ('Choose the independent unit', 'If many routes share a driver, depot, or dispatch day, errors may move together. HC3 alone addresses changing row-level variance under independence assumptions; it does not create independent observations where clusters exist. A cluster-aware covariance or cluster bootstrap needs enough independent groups and the right grouping level. [[applied-statistics/cluster-bootstrap-and-standard-error|The cluster lesson]] addresses that boundary. Do not select a standard-error formula solely because it makes a desired slope significant.'),
            ('Report sensitivity on the same effect scale', 'Show the coefficient and its unit, ordinary and justified alternative standard errors, influence distribution, influential rows, and the operational consequences of excluding any records. If a few high-influence routes determine the direction, the model may be extrapolating beyond common route support. [[applied-statistics/route-time-regression-audit-project|The project]] requires a frozen target population and a depot-level dependence review before a route-time claim is released.')
        ], '''def hc3_residual_factors(residuals, leverage_values):
    if not residuals or len(residuals) != len(leverage_values):
        raise ValueError("aligned residuals and influence required")
    factors = []
    for residual, influence in zip(residuals, leverage_values):
        if not 0 <= influence < 1:
            raise ValueError("influence must be in [0, 1)")
        factors.append((residual / (1 - influence)) ** 2)
    return factors

factors = hc3_residual_factors([3.0, 3.0], [0.2, 0.8])
assert factors[1] > 10 * factors[0]
''', 'Computing n HC3 residual factors is O(n) time and output space. Full covariance construction also uses the design matrix and matrix operations. Refitting with a better functional form or clustering strategy costs more, but multiplying residuals alone cannot fix those model boundaries.',
        ['Calling HC3 a cure for confounding or a wrong mean model.', 'Using row-independent HC3 when many observations share one depot shock.', 'Deleting a high-influence route only because it weakens the preferred result.', 'Treating a slope measured in minutes per kilometer as a unitless effect.'],
        ['clustered-regression-score-and-dependence', 'route-time-regression-audit-project', 'linear-regression-estimand-and-slope', 'regression-residuals-and-influence', 'cluster-bootstrap-and-standard-error']),
    lesson('clustered-regression-score-and-dependence',
        'Clustered regression: count independent groups before trusting precision', REGRESSION,
        'Cluster-aware uncertainty allows residuals within a group to co-move, while identification and finite-group limits remain separate questions.', [
            ('Map the shared shock', 'A route-time policy changes at depot level, yet an extract has tens of thousands of parcel rows. Parcels from the same depot-day share staff, weather, loading delays, and policy assignment. Treating parcel rows as independent can give a tiny standard error without many independent policy comparisons. The correct group may be depot, depot-day, or another unit depending on assignment and shock persistence; it must be justified from the data-generating process. [[applied-statistics/randomization-unit-and-experiment-design|The randomization-unit lesson]] is the first audit for a trial.'),
            ('Aggregate score contributions within group', 'A cluster-variance-aware sandwich covariance builds group-level sums of each row’s design-vector contribution times its residual, then combines outer products of those group sums. The code below computes one scalar predictor score total per group to make the aggregation visible. It is not a complete cluster covariance or a small-cluster correction. If a shock persists across days at one depot, grouping only by depot-day may still split a dependent process. [[applied-statistics/heteroskedasticity-hc3-and-leverage|HC3]] treats changing variance but cannot substitute for that dependence map.'),
            ('Check the number and balance of groups', 'Thirty thousand rows in four depots do not give thirty thousand independent assignment units. With few clusters or one cluster dominating treatment exposure, asymptotic standard errors can be unreliable. Inspect cluster counts by arm, size distribution, treatment support, and whether a cluster ever changes treatment status. A cluster bootstrap should resample whole independent groups, not parcels; with very few groups it also has limits. [[applied-statistics/cluster-bootstrap-and-standard-error|The bootstrap lesson]] explains the resampling unit.'),
            ('Keep inference and bias separate', 'A cluster-aware interval can widen uncertainty but cannot undo an observational policy rollout confounded by depot readiness. Report the coefficient with its scale, clustering unit and rationale, independent group count, and sensitivity to plausible group definitions. [[applied-statistics/route-time-regression-audit-project|The project]] blocks a precise claim when assignment groups and inference groups do not align. A larger data extract is not a replacement for new independent depots.')
        ], '''from collections import defaultdict

def predictor_residual_scores(route_rows):
    totals = defaultdict(float)
    for depot_id, predictor_value, residual in route_rows:
        if not depot_id:
            raise ValueError("depot ID required")
        totals[depot_id] += predictor_value * residual
    return dict(totals)

scores = predictor_residual_scores([("east", 2, 3), ("east", 4, -1),
                                    ("west", 3, 2)])
assert scores == {"east": 2.0, "west": 6.0}
''', 'The group-score accumulation is O(n) time and O(g) space for n rows and g groups. A full covariance also needs matrix products and a defensible finite-group procedure. The expensive step is finding the real dependence boundary, not summing another million parcel rows.',
        ['Clustering by a smaller unit than the assignment or persistent shock.', 'Calling thousands of parcels thousands of independent policy units.', 'Assuming a cluster correction fixes confounded policy assignment.', 'Using an asymptotic interval with only a handful of uneven groups without qualification.'],
        ['heteroskedasticity-hc3-and-leverage', 'route-time-regression-audit-project', 'cluster-bootstrap-and-standard-error', 'randomization-unit-and-experiment-design', 'survey-design-variance-and-psu']),
    lesson('route-time-regression-audit-project',
        'Project: audit a route-time regression before claiming a policy gain', REGRESSION,
        'Rebuild route-level evidence, check residual spread and depot dependence, and decide whether a policy coefficient is fit for release.', [
            ('Freeze the question and population', 'A logistics group claims its revised dispatch policy saves time per route. Define eligible routes, clock boundaries, depot and calendar coverage, the policy assignment process, and whether the target is an association or a causal change. A regression of observed minutes on policy, distance, load and depot can support different claims under different assumptions. Preserve excluded and missing routes in an eligibility ledger. [[applied-statistics/linear-regression-estimand-and-slope|The regression-estimand lesson]] starts the review.'),
            ('Inspect variance and influence', 'Plot residuals against predicted route time, distance and load. Record influence and influential observations, including unusually long rural routes. Compare the coefficient and uncertainty under the planned error model and a justified heteroskedasticity-aware calculation. Do not silently remove routes because they weaken a favorable policy result. [[applied-statistics/heteroskedasticity-hc3-and-leverage|The HC3 lesson]] explains why uncertainty can change while the coefficient does not.'),
            ('Rebuild the independent-group story', 'Trace the policy rollout and shared shocks across depots and days. If the decision was made for each depot, parcel rows are not independent assignments. Count groups in each policy state and decide whether depot-level clustering or another design-aware method is supportable. A group with no comparison exposure can force extrapolation. [[applied-statistics/clustered-regression-score-and-dependence|The cluster lesson]] separates group uncertainty from observational assignment bias.'),
            ('Publish a qualified packet', 'The packet includes cohort SQL, outcome and predictor timing, coefficient units, residual and influence summaries, influence sensitivity, independent-group counts, error-structure rationale, and uncertainty under prespecified alternatives. The gate below holds the policy claim if the independent unit is undefined or an influential route is hidden. Passing it allows review of the estimate, not automatic causal attribution. A follow-up randomized rollout may still be the right decision.')
        ], '''def route_regression_gate(audit):
    if not audit["cohort_reconciled"]:
        return "hold:route-frame"
    if not audit["assignment_unit_defined"]:
        return "hold:independent-unit"
    if audit["unreviewed_influential_routes"]:
        return "hold:influence-review"
    if not audit["group_uncertainty_reviewed"]:
        return "hold:dependence"
    return "review:qualified-effect"

audit = {"cohort_reconciled": True, "assignment_unit_defined": False,
         "unreviewed_influential_routes": 0,
         "group_uncertainty_reviewed": True}
assert route_regression_gate(audit) == "hold:independent-unit"
assert route_regression_gate({**audit, "assignment_unit_defined": True}) \
       == "review:qualified-effect"
''', 'The gate is O(1); cohort and group reconciliation is O(n) expected time with indexed routes. Fitting and resampling a regression cost more, but the critical resource is independent rollout units. A fast row-level standard error cannot create depots that were not studied.',
        ['Calling an adjusted observational slope a causal policy effect.', 'Choosing the covariance method by whether the p-value crosses a threshold.', 'Dropping influential rural routes without showing the change in target population.', 'Clustering parcel rows at a unit smaller than the policy assignment.'],
        ['heteroskedasticity-hc3-and-leverage', 'clustered-regression-score-and-dependence', 'linear-regression-estimand-and-slope', 'regression-residuals-and-influence', 'cluster-bootstrap-and-standard-error'], True),
    lesson('excess-zero-counts-and-structural-opportunity',
        'Excess zeros: separate no opportunity from a stochastic zero count', COUNTS,
        'A count dataset may contain zeros from a genuine no-opportunity state and zeros generated by an ordinary low-rate count process.', [
            ('Define exposure before interpreting zero', 'A facility records device faults per machine-week. Some machines were switched off all week; others ran for many hours without a fault. Both rows have zero faults, but the first has no operating exposure and the second provides evidence about the fault rate. A positive exposure offset belongs in a count-rate model; a true zero-exposure row should not be assigned a logged offset or mistaken for an exceptionally safe machine. [[applied-statistics/poisson-regression-offset-and-dispersion|The offset lesson]] keeps counts and time at risk aligned.'),
            ('Compare observed zeros with a rate model', 'Given a supplied Poisson mean for each exposed row, the predicted zero probability is exp of negative mean. Sum those probabilities to obtain the expected number of zero rows under that model, then compare with the observed count. The code performs only that diagnostic. More observed zeros can arise from genuine structural states, unmodeled heterogeneity, clustering, or a wrong exposure record; the gap alone does not identify a mixture component. [[applied-statistics/negative-binomial-variance-and-count-heterogeneity|The dispersion lesson]] tests a competing explanation.'),
            ('Choose a mechanism before a model family', 'A zero-inflated count model treats some exposed rows as belonging to a latent always-zero state while the ordinary count component can also produce zeros. A hurdle model instead models zero versus positive separately, then a positive truncated count. Both can fit many zeros, but their parameters have different operational meanings. If inactive machines are observed directly, classify or exclude zero-exposure periods using the target population instead of inferring a latent class by default. [[applied-statistics/hurdle-count-severity-and-frequency|The hurdle lesson]] separates occurrence from positive severity.'),
            ('Evaluate what a decision needs', 'Report exposure completeness, observed and expected zero fractions, positive-count distribution, calibration by machine type, and uncertainty. A fitted model with better likelihood may still be poor for predicting the number of faults or the chance of any fault on a future machine. [[applied-statistics/device-fault-count-project|The project]] requires both zero-frequency and positive-count checks before a maintenance claim.')
        ], '''from math import exp

def zero_count_diagnostic(observed_counts, predicted_means):
    if not observed_counts or len(observed_counts) != len(predicted_means):
        raise ValueError("aligned exposed rows required")
    if any(count < 0 or int(count) != count for count in observed_counts) or \
       any(mean <= 0 for mean in predicted_means):
        raise ValueError("nonnegative counts and positive means required")
    observed_zeros = sum(count == 0 for count in observed_counts)
    expected_zeros = sum(exp(-mean) for mean in predicted_means)
    return observed_zeros, expected_zeros

observed, expected = zero_count_diagnostic([0, 0, 1, 3], [1.0] * 4)
assert observed == 2 and 1 < expected < 2
''', 'The diagnostic is O(n) time and O(1) extra space for n exposed rows. Fitting a mixture is more costly and can be unstable with weakly identified components. Cleaning machine uptime is often more valuable than adding a latent zero process.',
        ['Treating a zero-exposure machine-week as a safe exposed week.', 'Calling every extra zero proof of a structural always-zero class.', 'Comparing models on likelihood alone while ignoring future zero and positive-count calibration.', 'Logging zero exposure or silently replacing it with one operating hour.'],
        ['negative-binomial-variance-and-count-heterogeneity', 'hurdle-count-severity-and-frequency', 'device-fault-count-project', 'poisson-regression-offset-and-dispersion', 'poisson-count-rate-and-exposure']),
    lesson('negative-binomial-variance-and-count-heterogeneity',
        'Negative binomial counts: model extra variance without inventing structural zeros', COUNTS,
        'A negative binomial mean-variance relationship allows fault counts to vary more than a Poisson model with the same conditional mean.', [
            ('Look at spread at comparable exposure', 'Two machines can run for similar hours and still have very different fault counts because their age, maintenance history, or working conditions differ. A conditional Poisson model has variance equal to its mean. A negative binomial model in one common parameterization has variance equal to mean plus alpha times mean squared, with nonnegative alpha. The code below calculates this variance for supplied parameters; it does not estimate alpha. [[applied-statistics/poisson-regression-offset-and-dispersion|The Poisson regression lesson]] explains where the baseline assumption enters.'),
            ('Distinguish heterogeneity from a data defect', 'A large count spread can reflect omitted predictors, route or machine clustering, changing observation windows, coding mistakes, or real latent rate heterogeneity. Check those explanations before adding a distributional parameter. Negative binomial dispersion can produce more zeros than Poisson without a separate always-zero class. A zero-inflated model therefore needs a substantive mechanism, not just a zero histogram. [[applied-statistics/excess-zero-counts-and-structural-opportunity|The zero lesson]] separates an inactive device from a functioning device with zero observed faults.'),
            ('Preserve rate meaning', 'Use the same fault definition and operating exposure in both candidate models. With a log link, the exposure offset has coefficient one by design; if machine-hours were recorded differently by site, neither distribution repairs that measurement problem. Compare conditional mean calibration, variance, zero frequency, and tail frequency on held-out machine-weeks. A model that matches total faults but badly misses the rare high-fault machines may fail the maintenance decision.'),
            ('Report the inference limit', 'Show estimated mean, alpha and uncertainty, exposure distribution, cluster structure, and whether predictive performance improves in the groups that matter. A negative binomial fit is still an association unless assignment or causal assumptions support more. [[applied-statistics/hurdle-count-severity-and-frequency|The hurdle lesson]] offers a distinct two-part question; [[applied-statistics/device-fault-count-project|the project]] compares them only after the exposure ledger is trustworthy.')
        ], '''def negative_binomial_variance(conditional_mean, dispersion_alpha):
    if conditional_mean < 0 or dispersion_alpha < 0:
        raise ValueError("mean and dispersion must be nonnegative")
    return conditional_mean + dispersion_alpha * conditional_mean ** 2

assert negative_binomial_variance(3, 0) == 3
assert negative_binomial_variance(3, 0.4) == 6.6
''', 'One variance calculation is O(1). Estimating model coefficients and dispersion needs numerical optimization, and validating tails needs enough independent exposed units. An extra variance parameter is cheaper than repairing an incorrect uptime ledger but cannot substitute for it.',
        ['Reading extra zeros alone as proof a zero-inflated model is needed.', 'Ignoring different machine-hours when comparing raw counts.', 'Assuming a dispersion parameter fixes omitted predictors or shared site shocks.', 'Reporting a model improvement without inspecting high-fault tail predictions.'],
        ['excess-zero-counts-and-structural-opportunity', 'hurdle-count-severity-and-frequency', 'device-fault-count-project', 'poisson-regression-offset-and-dispersion', 'cluster-bootstrap-and-standard-error']),
    lesson('hurdle-count-severity-and-frequency',
        'Hurdle models: separate any event from the number of events once positive', COUNTS,
        'A hurdle model splits the probability of crossing zero from the distribution of strictly positive counts.', [
            ('Ask two operational questions', 'A maintenance team may need the probability that a machine faults at all this week and, separately, the expected number of faults among machine-weeks with at least one. A hurdle model has a binary occurrence component and a positive-count component that is truncated at zero. Its unconditional mean is occurrence probability times the mean among positive counts. The code calculates only that identity from supplied quantities. [[applied-statistics/excess-zero-counts-and-structural-opportunity|The excess-zero lesson]] explains why inactive devices should first be identified from exposure records.'),
            ('Do not call the parts independent causes', 'The two components are a statistical factorization. They do not prove there are two physical mechanisms or that preventing the first fault has no effect on later faults. A service change could shift occurrence, positive severity, or both. If the business decision is spare-parts inventory, a total mean may matter; if it is preventive inspection scheduling, the chance of any fault may be more useful. Report each component on its own scale.'),
            ('Handle exposure and truncation correctly', 'A positive-count model must assign no probability to zero and be evaluated against only positive observed counts; fitting an ordinary count likelihood to just positive rows without accounting for truncation is not the same model. Exposure hours can affect both the occurrence probability and positive count, but their relationships need not be identical. Compare predictions by machine type and hours, including zero fraction and upper tail, on a later validation period. [[applied-statistics/negative-binomial-variance-and-count-heterogeneity|The dispersion lesson]] gives an alternative for broad count variation.'),
            ('Communicate uncertainty and deployment', 'Report the occurrence model, positive-count model, combined mean, each interval or uncertainty band, and the fraction of rows with incomplete exposure. A zero-heavy model is unsafe for maintenance staffing if it matches average faults but misses burst weeks. [[applied-statistics/device-fault-count-project|The project]] rejects a model chosen solely because its overall likelihood is higher and requires both operational components to calibrate.')
        ], '''def hurdle_expected_faults(any_fault_probability,
                           mean_faults_given_positive):
    if not 0 <= any_fault_probability <= 1 or \
       mean_faults_given_positive < 1:
        raise ValueError("valid occurrence probability and positive count mean required")
    return any_fault_probability * mean_faults_given_positive

assert hurdle_expected_faults(0.25, 2.8) == 0.7
assert hurdle_expected_faults(0, 3.2) == 0
''', 'Combining supplied components is O(1), while fitting occurrence and zero-truncated count models costs separate optimization. Assessing both stages and their joint uncertainty is more work than fitting one mean, but it matches two distinct maintenance decisions.',
        ['Fitting an untruncated positive-count likelihood after deleting zeros.', 'Interpreting a statistical hurdle as proof of two physical fault causes.', 'Ignoring operating exposure in either component.', 'Selecting a model on total mean accuracy while it misses occurrence or burst counts.'],
        ['excess-zero-counts-and-structural-opportunity', 'negative-binomial-variance-and-count-heterogeneity', 'device-fault-count-project', 'poisson-regression-offset-and-dispersion', 'diagnostic-performance-and-prevalence']),
    lesson('device-fault-count-project',
        'Project: select a fault-count model from exposure, zeros and burst behavior', COUNTS,
        'Audit machine-hour exposure, compare count distributions, and publish only the predictive quantities maintenance can act on.', [
            ('Freeze the machine-week frame', 'A factory wants to forecast maintenance work from logged device faults. Define eligible machine-weeks, powered-on hours, fault deduplication, site and machine type, and the outcome maturity cutoff. Separate powered-off weeks from active weeks with no faults. If a device was down and its fault log was unavailable, mark missing observation rather than zero. [[applied-statistics/poisson-count-rate-and-exposure|The exposure lesson]] supplies the denominator; [[applied-statistics/missing-outcome-ledger-and-target-population|the missingness lesson]] handles absent logs.'),
            ('Diagnose before fitting', 'Compare observed zeros with Poisson expectations for exposed rows, inspect count variance among comparable exposure bands, and examine high-fault machine-weeks. Check whether site or device age explains spread before considering latent classes. The simple Poisson, negative binomial, zero-inflated and hurdle candidates answer different data stories; candidate selection must reflect the maintenance decision. [[applied-statistics/excess-zero-counts-and-structural-opportunity|Zero diagnostics]], [[applied-statistics/negative-binomial-variance-and-count-heterogeneity|extra variance]] and [[applied-statistics/hurdle-count-severity-and-frequency|two-part modeling]] connect to these checks.'),
            ('Validate on a later period', 'For each model, predict chance of any fault, mean count per machine-week and probability of a costly burst on a later time window. Report calibration by site and machine type with denominators. A likelihood advantage on the training set is insufficient if a simpler count model predicts the maintenance inventory better. Preserve exposure and model versions so a logging update cannot be mistaken for a risk shift.'),
            ('Gate the operational packet', 'The packet contains uptime reconciliation, zero-exposure rules, missing-log counts, candidate assumptions, later-period calibration, uncertainty and a staffing loss measure. The gate below refuses a published recommendation if inactive machines were counted as safe exposed weeks or burst validation is missing. Passing it permits operations review; it does not establish that changing maintenance will causally change the observed fault rate.')
        ], '''def device_fault_gate(audit):
    if audit["zero_exposure_as_safe"]:
        return "hold:exposure-definition"
    if audit["missing_logs_as_zero"]:
        return "hold:missing-faults"
    if not audit["later_window_validated"]:
        return "hold:forecast-validation"
    if not audit["burst_calibration_reviewed"]:
        return "hold:high-count-tail"
    return "review:maintenance-model"

audit = {"zero_exposure_as_safe": True, "missing_logs_as_zero": False,
         "later_window_validated": True, "burst_calibration_reviewed": True}
assert device_fault_gate(audit) == "hold:exposure-definition"
assert device_fault_gate({**audit, "zero_exposure_as_safe": False}) \
       == "review:maintenance-model"
''', 'The gate is O(1). Frame reconstruction and group summaries are O(n) over machine-weeks, while fitting several count models and validating rare bursts take more time. Wrong uptime exposure is a data fault that no model comparison can cheaply fix.',
        ['Treating powered-off machines as exposed zero-fault evidence.', 'Replacing unavailable fault logs with zero counts.', 'Choosing the most complex count model from training likelihood alone.', 'Reporting total fault accuracy without checking burst-week calibration.'],
        ['excess-zero-counts-and-structural-opportunity', 'negative-binomial-variance-and-count-heterogeneity', 'hurdle-count-severity-and-frequency', 'poisson-count-rate-and-exposure', 'missing-outcome-ledger-and-target-population'], True),
    lesson('rolling-origin-backtest-and-forecast-horizon',
        'Rolling-origin backtests: make every forecast from information available then', FORECAST,
        'A rolling-origin evaluation moves the forecast date forward and uses only data available before each origin to predict a declared future horizon.', [
            ('Freeze the production timing', 'A service center forecasts next week’s incoming cases every Friday. The input snapshot at a Friday origin must contain only cases, holidays and staffing plans known by that Friday; later corrections and post-week totals cannot leak backward. For a four-week horizon, the answer is the demand four weeks out, not the next observed week. Choose train length, update cadence, horizon and final audit period before model comparison. [[applied-statistics/serial-correlation-and-effective-information|The serial-dependence lesson]] explains why randomly shuffled rows give misleading certainty.'),
            ('Generate comparable origins', 'At each origin, fit or update the candidate using observations ending before a declared gap, then predict the target horizon. The gap may reflect reporting delay or operational embargo. The code returns simple index windows for an expanding history; it does not fit a model. Every forecast must be stored with its origin, target period, horizon and model version. If a target period lacks a final count, flag it as pending rather than treating it as zero.'),
            ('Compare against a plain baseline', 'A seasonal last-year value or recent-week average can be a serious baseline. Use the same origins and target periods for every candidate, then score both overall and by horizon, region and known peak periods. Aggregate errors from many adjacent origins can be correlated because their training sets and forecast targets overlap. Avoid calling the number of forecasts the number of independent policy trials. [[applied-statistics/forecast-interval-coverage-by-horizon|The interval lesson]] checks whether uncertainty grows appropriately with horizon.'),
            ('Preserve a final untouched window', 'Tune models on earlier backtest origins, reserve later origins for final comparison, and then monitor live forecasts using their original archived versions. Rebuilding a forecast after the target week using newly corrected history is useful for diagnosis but not a valid historical prediction. [[applied-statistics/staffing-demand-forecast-project|The project]] requires timestamped feature snapshots and a later-period score before staffing changes are justified.')
        ], '''def expanding_forecast_windows(total_periods, minimum_train,
                               horizon, gap=0):
    if minimum_train <= 0 or horizon <= 0 or gap < 0 or \
       total_periods < minimum_train + gap + horizon:
        raise ValueError("history cannot support the requested windows")
    return [(tuple(range(0, train_end)), train_end + gap + horizon - 1)
            for train_end in range(minimum_train,
                                   total_periods - gap - horizon + 1)]

windows = expanding_forecast_windows(12, 5, 3, gap=1)
assert windows[0] == ((0, 1, 2, 3, 4), 8)
assert windows[-1][1] == 11
''', 'The window generator creates O(k n) stored indices across k origins and up to n training periods; streaming slices avoids the list cost. Refitting every origin is more expensive but reproduces the production forecast. Random train-test shuffling is faster and answers the wrong timing question.',
        ['Using a feature corrected after the forecast origin.', 'Scoring a four-week forecast against next week.', 'Treating pending target counts as zero.', 'Tuning and reporting accuracy on the same final origins.'],
        ['forecast-interval-coverage-by-horizon', 'staffing-demand-forecast-project', 'serial-correlation-and-effective-information', 'moving-block-bootstrap-and-block-length', 'distribution-quantiles-and-outlier-policy']),
    lesson('forecast-interval-coverage-by-horizon',
        'Forecast intervals: check coverage and width at each planning horizon', FORECAST,
        'A forecast interval should cover future outcomes at its declared rate on comparable future periods without becoming uselessly wide.', [
            ('Attach uncertainty to the right target', 'A staffing forecast for next week and one for six weeks ahead have different information sets. Keep their origin and horizon labels with the point prediction and lower and upper bounds. A confidence interval for an average trend is not a prediction interval for a new weekly case count. An interval around the point forecast should account for future outcome variation as well as estimation uncertainty under the chosen model. [[applied-statistics/mean-response-vs-prediction-interval|The interval distinction]] carries over from regression.'),
            ('Measure empirical coverage', 'On archived rolling-origin forecasts with mature outcomes, count the fraction of realized weekly volumes within the stated bounds separately for each horizon. A nominal 90-percent interval should have roughly that coverage across comparable future periods if it is calibrated, but small samples are noisy. Also report average width and how often the actual count exceeds the upper staffing limit. The code audits supplied records; it does not construct or recalibrate an interval. [[applied-statistics/rolling-origin-backtest-and-forecast-horizon|The backtest lesson]] ensures the records were genuine forecasts.'),
            ('Watch sharpness and regime changes', 'A huge interval can cover nearly everything while offering little staffing value. Compare width and operational undercapacity cost with a frozen baseline. Coverage may look right overall while holiday weeks, new service lines or one region under-cover. Group reports need denominators, and adjacent rolling forecasts can share errors. If the outcome definition or case intake policy changes, the old interval calibration may no longer transport.'),
            ('Report asymmetric risk', 'Understaffing from an upper-tail miss can cost more than overstaffing. A central interval may not match that loss; a high predictive quantile can be a better staffing threshold. Show the cost choice and avoid shifting it after seeing the results. [[applied-statistics/conditional-quantile-and-pinball-loss|The quantile lesson]] gives an asymmetric score. [[applied-statistics/staffing-demand-forecast-project|The project]] requires horizon coverage, width, peak-period checks and upper-tail misses before approving staffing recommendations.')
        ], '''def interval_coverage_by_horizon(forecast_rows):
    summary = {}
    for horizon, actual, lower, upper in forecast_rows:
        if horizon <= 0 or lower > upper:
            raise ValueError("valid horizon and bounds required")
        covered, count, total_width = summary.get(horizon, (0, 0, 0.0))
        summary[horizon] = (covered + (lower <= actual <= upper),
                            count + 1, total_width + upper - lower)
    return {horizon: {"coverage": covered / count,
                      "mean_width": width / count, "rows": count}
            for horizon, (covered, count, width) in summary.items()}

report = interval_coverage_by_horizon([(1, 29, 25, 34), (1, 38, 27, 35),
                                       (3, 42, 30, 48)])
assert report[1] == {"coverage": 0.5, "mean_width": 8.5, "rows": 2}
''', 'Auditing n saved forecasts is O(n) time and O(h) space for h distinct horizons. Generating interval forecasts can be much costlier and must be repeated as the model updates. A cheap global coverage percentage can conceal expensive upper-tail misses at the horizon used for staffing.',
        ['Calling an interval for the mean a range for next week’s actual count.', 'Pooling one-week and six-week forecasts into one coverage figure.', 'Making intervals wider until coverage looks good without reporting width.', 'Checking only periods whose outcome has already arrived and dropping delayed peaks.'],
        ['rolling-origin-backtest-and-forecast-horizon', 'staffing-demand-forecast-project', 'mean-response-vs-prediction-interval', 'conditional-quantile-and-pinball-loss', 'serial-correlation-and-effective-information']),
    lesson('staffing-demand-forecast-project',
        'Project: validate a case-volume forecast before it sets staffing', FORECAST,
        'Archive true forecast origins, score multiweek errors and interval coverage, and hold staffing automation when outcomes or features leak across time.', [
            ('Define the staffing decision', 'A service center sets weekly staffing from forecasts of incoming cases. Freeze which channels count, the intake timestamp, the roster decision date, each forecast horizon, and the loss of overstaffing versus an upper-tail shortfall. A forecast made Friday for a week several periods later cannot use the eventual schedule change, later marketing campaign, or finalized case count unless those facts were known Friday. [[applied-statistics/rolling-origin-backtest-and-forecast-horizon|The rolling-origin lesson]] enforces that chronology.'),
            ('Archive and replay historical origins', 'Save the data snapshot, model version, target week, horizon, point prediction and interval generated at each origin. Evaluate candidates and a simple seasonal baseline on identical mature target weeks. Keep final origins untouched during selection. Reporting delays are real missing outcomes, not zeros. If the case taxonomy changed, map old and new definitions before claiming an improvement. [[applied-statistics/missing-outcome-ledger-and-target-population|The outcome ledger]] captures unresolved target periods.'),
            ('Score the decision quantities', 'Report absolute error or another chosen point score, interval coverage and width by horizon, peak-week misses, and staffing shortfall cost. A model can reduce mean error while still missing the weeks that require surge staff. Check regions and queues separately with denominators. [[applied-statistics/forecast-interval-coverage-by-horizon|The interval lesson]] audits whether the uncertainty band is both calibrated and usable.'),
            ('Gate rollout and monitor drift', 'The packet includes origin snapshots, feature availability times, target maturity, baseline comparison, horizon-specific scores, interval checks, and the cost threshold used to choose staffing. The gate below blocks automated recommendations when snapshots were reconstructed using future fields or interval coverage was never checked. Passing it starts monitored deployment; keep weekly residuals and route or channel mix under review as demand changes.')
        ], '''def staffing_forecast_gate(audit):
    if audit["future_feature_leaks"]:
        return "hold:forecast-origin"
    if audit["pending_targets_as_zero"]:
        return "hold:target-maturity"
    if not audit["baseline_scored_on_same_weeks"]:
        return "hold:baseline-comparison"
    if not audit["horizon_coverage_reviewed"]:
        return "hold:interval-calibration"
    return "review:monitored-staffing"

audit = {"future_feature_leaks": 1, "pending_targets_as_zero": False,
         "baseline_scored_on_same_weeks": True,
         "horizon_coverage_reviewed": True}
assert staffing_forecast_gate(audit) == "hold:forecast-origin"
assert staffing_forecast_gate({**audit, "future_feature_leaks": 0}) \
       == "review:monitored-staffing"
''', 'The gate is O(1), while replaying k origins can require k model fits and O(k n) historical rows without caching. Timestamped snapshots consume storage, but without them a backtest can unknowingly use future data and overstate staffing value.',
        ['Recomputing historical features from a database after future corrections arrived.', 'Treating pending case totals as zero demand.', 'Comparing a model and baseline on different weeks.', 'Reporting mean accuracy while hiding costly peak-week staffing misses.'],
        ['rolling-origin-backtest-and-forecast-horizon', 'forecast-interval-coverage-by-horizon', 'conditional-quantile-and-pinball-loss', 'missing-outcome-ledger-and-target-population', 'serial-correlation-and-effective-information'], True),
]

crosslinks = [
    (A + 'regression-residuals-and-influence', A + 'heteroskedasticity-hc3-and-leverage'),
    (A + 'cluster-bootstrap-and-standard-error', A + 'clustered-regression-score-and-dependence'),
    (A + 'route-time-regression-review-project', A + 'route-time-regression-audit-project'),
    (A + 'poisson-regression-offset-and-dispersion', A + 'excess-zero-counts-and-structural-opportunity'),
    (A + 'poisson-count-rate-and-exposure', A + 'negative-binomial-variance-and-count-heterogeneity'),
    (A + 'claim-count-glm-project', A + 'device-fault-count-project'),
    (A + 'serial-correlation-and-effective-information', A + 'rolling-origin-backtest-and-forecast-horizon'),
    (A + 'mean-response-vs-prediction-interval', A + 'forecast-interval-coverage-by-horizon'),
    (A + 'refund-delay-series-review-project', A + 'staffing-demand-forecast-project'),
]

if __name__ == '__main__':
    publish(lessons, [REGRESSION, COUNTS, FORECAST], crosslinks,
            'aitrove-applied-statistics-regression-count-forecast-import-20261007.json',
            8484, subject='applied-statistics',
            hub_path=A + 'applied-statistics-tutorial')
