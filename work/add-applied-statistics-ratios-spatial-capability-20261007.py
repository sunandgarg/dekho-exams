"""Add Applied Statistics lessons on ratio metrics, spatial dependence and capability."""
from de_batch_publisher import publish

A = 'applied-statistics/'
RATIOS = 'Ratio metrics and denominator uncertainty'
SPATIAL = 'Spatial dependence and geographic validation'
CAPABILITY = 'Process capability and population coverage'


def lesson(slug, title, module, summary, sections, code, cost, mistakes, related, project=False):
    return dict(path=A + slug, title=title, module=module, project=project,
                summary=summary, sections=sections, code=code, cost=cost,
                mistakes=mistakes, related=[A + path for path in related])


lessons = [
    lesson('ratio-of-totals-vs-average-ratios',
        'Ratio metrics: choose ratio of totals or average of unit ratios', RATIOS,
        'A ratio of aggregate numerators to aggregate denominators answers a different question from the average of unit-level ratios.', [
            ('Define the unit and target', 'A courier team asks for damaged parcels per thousand shipped parcels across depots. If the target is the risk for a randomly selected parcel, sum damaged parcels across eligible depots and divide by all shipped parcels. If the target is the experience of a randomly selected depot, average depot-specific rates under a stated depot weighting scheme. These targets need not agree. A small depot with four damaged parcels in forty shipments counts as much as a huge depot under an unweighted depot average, but contributes only forty shipments to the parcel-weighted rate.'),
            ('Keep numerator and denominator aligned', 'The code calculates both summaries for an original three-depot ledger and refuses impossible records. It excludes zero-shipment depots from the average of defined rates, while still requiring zero damage for such a depot. For a parcel-level risk, numerator and denominator must cover the same dates, eligible services and deduplication rules. A late damage claim counted against last month’s shipments can distort the rate even if every arithmetic operation is correct. [[applied-statistics/poisson-count-rate-and-exposure|Count-rate exposure]] explains another denominator tied to time at risk.'),
            ('Do not collapse the design', 'If depots were sampled with unequal probabilities, summing sampled shipments is not automatically a population parcel rate. A design-based estimator needs the sampling and response weights on both totals. Repeated days within depot can share shocks, so thousands of parcel rows may not yield thousands of independent uncertainty units. [[applied-statistics/survey-design-variance-and-psu|Survey design]] and [[applied-statistics/cluster-bootstrap-and-standard-error|cluster resampling]] address those boundaries. The next lesson derives a paired-denominator approximation for independent units, then warns when it fails.'),
            ('Publish both when decisions differ', 'A policy that improves the overall parcel-weighted rate could still leave small depots worse off. Report total damaged parcels, total eligible shipments, each depot’s rate, zero-denominator handling and the intended unit of fairness. A single headline rate cannot show whether the change is broad or driven by one high-volume depot. [[applied-statistics/ratio-delta-uncertainty|Ratio uncertainty]] covers the covariance between counts and exposure; [[applied-statistics/depot-damage-ratio-project|the project]] ties denominator identity to a release gate.')
        ], '''def depot_damage_rates(depot_rows):
    if not depot_rows:
        raise ValueError("at least one depot required")
    total_damage = total_shipments = 0
    defined_rates = []
    for depot_id, damaged, shipped in depot_rows:
        if not depot_id or shipped < 0 or not 0 <= damaged <= shipped:
            raise ValueError("valid aligned depot counts required")
        total_damage += damaged
        total_shipments += shipped
        if shipped:
            defined_rates.append(damaged / shipped)
    if not total_shipments:
        raise ValueError("no eligible shipments")
    return total_damage / total_shipments, sum(defined_rates) / len(defined_rates)

parcel_rate, depot_mean_rate = depot_damage_rates([
    ("Harbor", 2, 40), ("Ridge", 8, 400), ("Central", 14, 700)])
assert round(parcel_rate, 4) == 0.0211
assert round(depot_mean_rate, 4) == 0.03
''', 'Scanning d depot rows costs O(d) time and O(d) space for the stored defined rates; a running sum gives O(1) extra space. Rebuilding deduplicated parcel counts can cost far more than the division. The calculation cannot repair an incompatible date window or an unrecorded zero-exposure depot.',
        ['Calling the unweighted average depot rate a parcel-level risk.', 'Including damage claims and shipments from different eligible windows.', 'Replacing zero shipments with one to avoid division by zero.', 'Treating all parcel rows as independent when depot shocks dominate.'],
        ['ratio-delta-uncertainty', 'depot-damage-ratio-project', 'poisson-count-rate-and-exposure', 'survey-design-variance-and-psu', 'cluster-bootstrap-and-standard-error']),
    lesson('ratio-delta-uncertainty',
        'Ratio uncertainty: retain numerator-denominator covariance', RATIOS,
        'A first-order ratio standard error depends on how each unit’s numerator moves with its denominator, not on numerator variability alone.', [
            ('Linearize the paired unit', 'For independent depots with eligible damaged counts Y and shipment counts X, the aggregate rate is sum Y divided by sum X. An approximate large-sample standard error uses residual contributions Y minus estimated rate times X, their sample standard deviation, and the mean X. This keeps the covariance induced by a high-volume depot having more possible damage. The code implements that one-step approximation for positive aggregate exposure. It is not a small-sample exact interval and it does not turn unequal depots into equally informative parcels.'),
            ('Know when the approximation breaks', 'With only a few depots, one depot carrying most shipments, or a denominator total near zero, a symmetric interval from the approximate standard error can be unstable or even extend below zero. Inspect the contribution of each depot and consider a design-matched resampling or an interval built for the actual count process. Never bootstrap individual parcels when entire depots share operational conditions. [[applied-statistics/cluster-bootstrap-and-standard-error|The cluster bootstrap]] states the resampling unit; [[applied-statistics/rare-proportion-wilson-interval|the rare-proportion lesson]] covers a different independent-Bernoulli design.'),
            ('Match the sampling design', 'The code assumes independent, similarly sampled unit pairs. Stratified depots, unequal inclusion chances and repeated depot-days change the variance calculation. The target ratio also matters: if leadership wants a typical depot rather than a typical parcel, an interval for a mean of depot rates follows a different estimator. [[applied-statistics/ratio-of-totals-vs-average-ratios|The target lesson]] fixes that choice before any uncertainty calculation. If damage reporting is incomplete, a tight standard error describes only the observed ledger, not hidden damage.'),
            ('Report the denominator risk', 'Show unit count, total exposure, largest unit share, zero-exposure units, the estimated rate and the method for uncertainty. Plot residual contributions against shipment volume to see whether one site controls the estimate. A normal approximation can be useful for a large, well-spread collection of independent depots; it should be accompanied by a separate sensitivity analysis when the denominators are highly uneven. [[applied-statistics/depot-damage-ratio-project|The project]] requires that sensitivity before a performance claim.')
        ], '''from math import sqrt
from statistics import mean, stdev

def paired_ratio_se(damaged_counts, shipment_counts):
    if len(damaged_counts) != len(shipment_counts) or len(shipment_counts) < 2:
        raise ValueError("at least two aligned depots required")
    if any(shipped < 0 or not 0 <= damaged <= shipped
           for damaged, shipped in zip(damaged_counts, shipment_counts)):
        raise ValueError("valid aligned counts required")
    mean_exposure = mean(shipment_counts)
    if mean_exposure <= 0:
        raise ValueError("positive average exposure required")
    rate = sum(damaged_counts) / sum(shipment_counts)
    contributions = [damaged - rate * shipped
                     for damaged, shipped in zip(damaged_counts, shipment_counts)]
    return rate, stdev(contributions) / (sqrt(len(contributions)) * mean_exposure)

rate, standard_error = paired_ratio_se([3, 7, 12], [60, 300, 600])
assert round(rate, 4) == 0.0229 and standard_error > 0
''', 'The linearized calculation is O(d) time and O(d) space for d independent units; a two-pass variance can use O(1) extra space. Wider statistical machinery is justified when the design has strata or clusters. A precise formula applied to the wrong independence unit remains misleading.',
        ['Computing numerator and denominator standard errors separately while ignoring covariance.', 'Using a symmetric ratio interval with a tiny or unstable denominator.', 'Resampling parcels while the independent units are depots.', 'Calling a selected-depot ratio a population rate without accounting for selection.'],
        ['ratio-of-totals-vs-average-ratios', 'depot-damage-ratio-project', 'cluster-bootstrap-and-standard-error', 'survey-design-variance-and-psu', 'rare-proportion-wilson-interval']),
    lesson('depot-damage-ratio-project',
        'Project: audit a parcel-damage rate across uneven depots', RATIOS,
        'Reconstruct a paired numerator-denominator ledger, choose the business target and validate uncertainty at the depot level.', [
            ('Freeze the cohort and event clock', 'A transport network wants to compare a new packing rule with its prior damage rate. Define an eligible shipment, one unique parcel identifier, damage-report maturity, date attribution and depot ownership before counting. Keep zero-shipment depots in the coverage ledger even though their rates are undefined. Separate claims that arrive late from parcels whose observation window has not matured. [[applied-statistics/poisson-count-rate-and-exposure|Exposure definitions]] and [[applied-statistics/missing-outcome-ledger-and-target-population|missing outcomes]] help prevent a silent denominator change.'),
            ('Choose the rate whose unit matches the decision', 'If the claim is about an average parcel, use damaged parcels over eligible parcels; if it is about a typical depot, use an explicitly weighted depot-rate estimand. Calculate both as a diagnostic when depot sizes differ. A fall in the network rate can hide worsening small depots if a large depot improves. [[applied-statistics/ratio-of-totals-vs-average-ratios|The ratio lesson]] shows the arithmetic and the distinction. Preserve shipment and damage totals by depot and time period so every dashboard rate can be rebuilt.'),
            ('Estimate uncertainty from independent units', 'Review whether treatment was assigned by depot, parcel or calendar period. Use the same unit for resampling or design variance that generated independent treatment and operational shocks. Check the largest depot’s share, positive-denominator count and the sensitivity of the result when one depot is removed for diagnosis. [[applied-statistics/ratio-delta-uncertainty|The delta approximation]] gives a transparent first pass under independent depots; it cannot rescue a four-depot network from weak independent information.'),
            ('Release with explicit limits', 'The packet contains the data contract, maturation rule, target estimand, paired unit ledger, denominator distribution, missing-claim sensitivity and uncertainty method. The gate below holds a recommendation if the numerator and denominator windows differ or the target was never chosen. A passing packet is ready for statistical review; it does not prove the packing rule caused the observed change when the rollout was not randomized.')
        ], '''def damage_rate_gate(review):
    if not review["same_eligibility_window"]:
        return "hold:denominator-identity"
    if not review["target_unit_defined"]:
        return "hold:estimand"
    if not review["late_claims_accounted_for"]:
        return "hold:outcome-maturity"
    if not review["depot_dependence_reviewed"]:
        return "hold:independent-unit"
    return "review:damage-rate"

review = {"same_eligibility_window": True, "target_unit_defined": True,
          "late_claims_accounted_for": False, "depot_dependence_reviewed": True}
assert damage_rate_gate(review) == "hold:outcome-maturity"
assert damage_rate_gate({**review, "late_claims_accounted_for": True}) == "review:damage-rate"
''', 'The gate is O(1). Rebuilding the parcel ledger is O(n) expected time with unique IDs and O(n) storage for n parcels. Unit-level uncertainty then costs O(d) for d depots. The hard cost is outcome maturation, not a more elaborate division function.',
        ['Changing the rate denominator between compared periods.', 'Using a network rate to claim every depot improved.', 'Treating a late claim as no damage.', 'Estimating uncertainty at parcel level when the intervention and shocks operate by depot.'],
        ['ratio-of-totals-vs-average-ratios', 'ratio-delta-uncertainty', 'cluster-bootstrap-and-standard-error', 'missing-outcome-ledger-and-target-population', 'poisson-count-rate-and-exposure'], True),
    lesson('spatial-neighbor-dependence-and-moran-statistic',
        'Spatial dependence: inspect neighbor similarity before inference', SPATIAL,
        'Spatial autocorrelation means nearby locations can have related values, reducing the information gained from treating every location as an independent replicate.', [
            ('Define neighbors before seeing outcomes', 'A chain of retail branches shares catchment areas, weather and local promotions. A demand spike at one branch may coincide with a spike nearby. Represent spatial proximity with a documented neighbor graph or distance rule before looking for a favorable pattern. The code calculates a simple global Moran statistic from a symmetric neighbor graph; it uses each listed directed edge in the weight sum. It is a descriptive diagnostic. Its value depends on the graph, geographic extent and outcome distribution, so a positive number alone is not a calibrated significance test.'),
            ('Read the statistic with its weight map', 'The statistic compares cross-products of centered values on neighboring branches with total centered variation. Positive values suggest neighboring branches tend to be similar under the chosen graph; negative values suggest opposite-valued neighbors. An isolated branch has no neighbor contribution but still affects the global mean and denominator. Changing from road travel time to straight-line distance can change the result. Report the weights, islands and number of edges. [[applied-statistics/serial-correlation-and-effective-information|Serial dependence]] is the time analogue, but spatial effects need geographic design.'),
            ('Separate dependence from explanation', 'Nearby high-demand branches may reflect shared population density, a regional campaign, a data-entry convention or a real spillover. A spatial pattern does not identify which mechanism operates. Assess residual spatial structure after a justified model, and calibrate a reference distribution only under a null and permutation scheme that respects the sampling and spatial support. If branch locations were selected by business opportunity, permuting values as though they were exchangeable can overstate certainty.'),
            ('Change the validation question', 'A random row split often puts neighboring branches in training and test sets, making prediction at nearby sites look easier than prediction in a new region. Use a holdout design that matches the intended deployment geography. [[applied-statistics/buffered-spatial-holdout|The buffered holdout lesson]] addresses near-neighbor leakage; [[applied-statistics/branch-demand-spatial-project|the project]] checks the operational claim. Spatial dependence is not a request to put latitude and longitude into every regression regardless of purpose.')
        ], '''def moran_neighbor_statistic(values_by_branch, neighbors):
    branch_ids = set(values_by_branch)
    if len(branch_ids) < 3 or set(neighbors) != branch_ids:
        raise ValueError("at least three aligned branches required")
    center = sum(values_by_branch.values()) / len(branch_ids)
    deviations = {branch: value - center for branch, value in values_by_branch.items()}
    denominator = sum(value * value for value in deviations.values())
    edge_total = weighted_sum = 0
    for branch, adjacent in neighbors.items():
        if any(other not in branch_ids or other == branch or
               branch not in neighbors[other] for other in adjacent):
            raise ValueError("symmetric, non-self neighbor graph required")
        for other in adjacent:
            weighted_sum += deviations[branch] * deviations[other]
            edge_total += 1
    if not denominator or not edge_total:
        raise ValueError("variation and at least one edge required")
    return len(branch_ids) * weighted_sum / (edge_total * denominator)

branch_values = {"A": 1, "B": 1, "C": 9, "D": 9}
branch_neighbors = {"A": {"B"}, "B": {"A", "C"},
                    "C": {"B", "D"}, "D": {"C"}}
assert round(moran_neighbor_statistic(branch_values, branch_neighbors), 3) == 0.333
''', 'With n branches and e directed neighbor entries, this diagnostic takes O(n+e) time and O(n) extra space. Permutation calibration repeats the calculation many times and depends on a valid null. A larger neighbor matrix is not a substitute for specifying the deployment geography.',
        ['Reading the sign of one statistic as proof of a regional cause.', 'Changing the neighbor definition until a desired result appears.', 'Assuming a random branch split tests new-region performance.', 'Treating adjacent branches as independent even after a residual spatial pattern remains.'],
        ['buffered-spatial-holdout', 'branch-demand-spatial-project', 'serial-correlation-and-effective-information', 'clustered-regression-score-and-dependence', 'population-estimand-and-sampling-frame']),
    lesson('buffered-spatial-holdout',
        'Buffered spatial holdout: test prediction away from nearby training sites', SPATIAL,
        'A geographic test region plus a gap between it and training data can reveal performance hidden by nearby training neighbors.', [
            ('Match the intended prediction', 'A retailer forecasts demand for branches in a new district. Randomly holding out rows from existing districts mostly tests interpolation between familiar neighbors. Instead, mark a geographic test region and exclude a surrounding buffer from training so near-border sites do not leak local conditions into the test. Coordinates must be projected into suitable distance units; raw longitude and latitude are not kilometers. The code uses planar kilometer coordinates and returns separate train, buffer and test sets. [[applied-statistics/spatial-neighbor-dependence-and-moran-statistic|The neighbor lesson]] explains why this separation matters.'),
            ('Keep preprocessing inside each split', 'If a regional average, target encoding, imputer or scaling parameter uses all branches before the split, the held-out geography has already influenced training. Fit each transformation on training only, then apply it to the held-out region. Repeat across several regions and report performance by region, branch size and demand range. A single easy district can make a model appear portable when remote districts fail. [[applied-statistics/rolling-origin-backtest-and-forecast-horizon|Time-ordered validation]] may be needed too when deployment is both in a new place and a later month.'),
            ('Choose buffer size deliberately', 'The gap should reflect the range over which local conditions or shared records make sites similar, as well as the distance at which the business will deploy. Too narrow a gap leaves leakage; too wide a gap can remove most training examples and test an unrealistic extrapolation problem. Compare a few prespecified distances, record how many sites fall in each band, and show the same geography on a map. Do not tune the gap to obtain a desired error score.'),
            ('Do not overstate the holdout', 'Spatial separation helps estimate performance for unsampled regions resembling the selected test regions. It does not make biased branch placement representative of every possible region, and it does not establish a causal effect of location. Report coordinate quality, site duplicates, overlapping catchments, fold assignment, buffer removals and deployment similarity. [[applied-statistics/branch-demand-spatial-project|The project]] holds a release if the headline score came from random rows or leaked preprocessing.')
        ], '''from math import hypot

def buffered_region_split(branch_rows, center_km, test_radius_km, buffer_km):
    if test_radius_km <= 0 or buffer_km < 0:
        raise ValueError("valid test radius and buffer required")
    train, gap, test = [], [], []
    for branch_id, x_km, y_km in branch_rows:
        if not branch_id:
            raise ValueError("branch ID required")
        distance = hypot(x_km - center_km[0], y_km - center_km[1])
        if distance <= test_radius_km:
            test.append(branch_id)
        elif distance <= test_radius_km + buffer_km:
            gap.append(branch_id)
        else:
            train.append(branch_id)
    if not train or not test:
        raise ValueError("split needs both training and test branches")
    return train, gap, test

train, gap, test = buffered_region_split([
    ("Hill", 0, 0), ("Market", 6, 0), ("Coast", 19, 0)], (0, 0), 4, 5)
assert (train, gap, test) == (["Coast"], ["Market"], ["Hill"])
''', 'Partitioning n projected branch coordinates costs O(n) time and O(n) output space. Repeated model fits across geographic folds dominate compute. The buffer deliberately discards some training rows; that cost buys a test closer to deployment beyond a familiar neighborhood.',
        ['Computing kilometer buffers directly from unprojected degree coordinates.', 'Fitting preprocessing on all branches before geographic splitting.', 'Reporting random-row accuracy as new-region accuracy.', 'Selecting the buffer width after seeing which value looks best.'],
        ['spatial-neighbor-dependence-and-moran-statistic', 'branch-demand-spatial-project', 'rolling-origin-backtest-and-forecast-horizon', 'clustered-regression-score-and-dependence', 'serial-correlation-and-effective-information']),
    lesson('branch-demand-spatial-project',
        'Project: audit branch-demand predictions for new districts', SPATIAL,
        'Compare random-row and geographically separated validation, then qualify the forecast for the districts where it will be used.', [
            ('Define the deployment map', 'A retailer has demand histories for existing branches and plans inventory for districts with no operating branch. Freeze the target period, eligible sites, coordinate system, district boundaries and whether the claim is for new districts or another month in the same district. Check duplicate branch IDs, locations at district borders and any data source whose feature was computed after the forecast date. A random train-test split answers a much easier question than this new-district decision.'),
            ('Inspect local similarity', 'Build a defensible neighbor graph from travel distance or another business distance measure and inspect demand or residual similarity. The graph need not be complex, but its rule must be recorded before the statistic is interpreted. [[applied-statistics/spatial-neighbor-dependence-and-moran-statistic|The spatial diagnostic]] makes shared local structure visible. Demand can also move with season, so do not mistake later outcomes from nearby branches for features known at prediction time.'),
            ('Hold out districts with a gap', 'Set multiple test regions, place a buffer around each and fit the entire preprocessing and model pipeline using training regions only. Compare error, calibration and high-demand miss rate by held-out district against a random-row baseline, with sample counts for both. [[applied-statistics/buffered-spatial-holdout|The split lesson]] provides the minimum geography guard; [[applied-statistics/rolling-origin-backtest-and-forecast-horizon|the time lesson]] provides the date guard. The geographic estimate may have larger error, which is useful evidence rather than a reason to hide it.'),
            ('Publish a bounded recommendation', 'The packet includes a map of train, gap and test sites, coordinate quality, fold assignment, regional sample sizes, feature availability, model version and separate metrics for familiar versus new districts. The gate below blocks a launch score if geographic separation or train-only preprocessing was skipped. Passing it allows planning review, not a claim that every unsampled district behaves like the held-out districts.')
        ], '''def spatial_forecast_gate(audit):
    if not audit["deployment_geography_defined"]:
        return "hold:target-geography"
    if not audit["buffered_regions_tested"]:
        return "hold:spatial-validation"
    if not audit["preprocessing_fit_on_train_only"]:
        return "hold:feature-leakage"
    if not audit["regional_errors_reported"]:
        return "hold:regional-error"
    return "review:new-district-forecast"

audit = {"deployment_geography_defined": True, "buffered_regions_tested": True,
         "preprocessing_fit_on_train_only": False, "regional_errors_reported": True}
assert spatial_forecast_gate(audit) == "hold:feature-leakage"
assert spatial_forecast_gate({**audit, "preprocessing_fit_on_train_only": True}) == "review:new-district-forecast"
''', 'The gate is O(1). Geographic partitioning takes O(n) per held-out region; repeated fitting can be much more expensive. Training on fewer sites is an intentional cost of asking whether a model can work away from nearby observations.',
        ['Hiding geographic test error behind a random-row score.', 'Allowing held-out district outcomes into target encodings or preprocessing.', 'Using unprojected coordinates as kilometers.', 'Claiming the held-out districts represent every future market.'],
        ['spatial-neighbor-dependence-and-moran-statistic', 'buffered-spatial-holdout', 'rolling-origin-backtest-and-forecast-horizon', 'clustered-regression-score-and-dependence', 'population-estimand-and-sampling-frame'], True),
    lesson('capability-index-after-stability',
        'Process capability: check stability before interpreting Cpk', CAPABILITY,
        'A process capability index compares the center and spread of a stable process with fixed engineering limits.', [
            ('Separate specifications from data', 'A filling line must place each pouch between 247 and 253 grams. Those limits come from the product contract, not from the observed sample. For an approximately normal and stable process, Cpk uses the smaller distance from the process mean to either limit divided by three standard deviations. It differs from a two-sided spread-only index because off-center filling wastes room near one limit. The code calculates an illustrative sample Cpk but cannot itself establish that the process is stable or normal.'),
            ('Inspect the time order first', 'A combined pouch sample can have an acceptable mean and spread while night shifts drift upward and morning shifts drift down. Plot measurements in production order, separate shifts and batches, and investigate any changes in calibration, ingredient density or scale. A capability index on a changing mixture does not describe one persistent process. [[applied-statistics/cusum-reference-and-alarm|CUSUM monitoring]] can flag a shift prospectively; [[applied-statistics/process-shift-vs-scheduled-change|the shift lesson]] distinguishes a planned equipment change from a searched break.'),
            ('Check tails and measurement error', 'A normal assumption can be poor for clipped, skewed or mixed fill weights. Compare actual below- and above-limit counts and the distribution shape with the model’s implication. A small sample standard deviation can also be misleading if a scale rounds values heavily or loses accuracy near the limit. [[applied-statistics/repeatability-pooled-within-item|Repeatability]] isolates instrument noise; [[applied-statistics/one-sided-tolerance-bound|a tolerance bound]] asks a separate population-coverage question.'),
            ('Make the number subordinate to the decision', 'Report limits, target, units, sample period, line and shift count, stability evidence, distribution checks, estimated Cpk and uncertainty. A point value above a company threshold is not a guarantee that future production meets specification, especially when the estimate is based on few independent batches. [[applied-statistics/fill-weight-capability-project|The project]] requires a release packet that keeps engineering limits separate from statistical control limits.')
        ], '''from statistics import mean, stdev

def fill_weight_cpk(weights_g, lower_g, upper_g):
    if len(weights_g) < 2 or not lower_g < upper_g:
        raise ValueError("measurements and ordered limits required")
    process_sd = stdev(weights_g)
    if process_sd <= 0:
        raise ValueError("positive measured spread required")
    process_mean = mean(weights_g)
    return min(upper_g - process_mean, process_mean - lower_g) / (3 * process_sd)

capability = fill_weight_cpk([249.8, 250.0, 250.2], 247, 253)
assert round(capability, 3) == 5.0
''', 'Computing mean, standard deviation and Cpk is O(n) time and O(1) extra space over n weights. Keeping time order and batch metadata adds O(n) storage but is necessary for stability checks. A fast index from unstable data is not a shortcut to process qualification.',
        ['Computing capability before checking that the process is stable.', 'Calling statistical control limits engineering specifications.', 'Assuming a normal tail when observed weights are skewed or mixed.', 'Reading one estimated Cpk as a guaranteed future defect fraction.'],
        ['one-sided-tolerance-bound', 'fill-weight-capability-project', 'cusum-reference-and-alarm', 'repeatability-pooled-within-item', 'distribution-quantiles-and-outlier-policy']),
    lesson('one-sided-tolerance-bound',
        'One-sided tolerance bounds: cover individual outcomes, not only the mean', CAPABILITY,
        'A statistical tolerance bound supports a claim about a specified fraction of individual outcomes with a specified confidence level.', [
            ('Ask the population question', 'A line manager wants evidence that at least ninety percent of future pouches are below an upper weight threshold. A confidence interval for average weight cannot answer that: a tight mean can coexist with a wide upper tail. A one-sided upper tolerance bound targets the fraction of the individual-outcome distribution below a chosen bound. The required population fraction and confidence must be declared separately. [[applied-statistics/confidence-interval-coverage|Confidence intervals]] concern a parameter; [[applied-statistics/distribution-quantiles-and-outlier-policy|quantiles]] describe where individual observations fall.'),
            ('Use a simple distribution-free construction carefully', 'For independent draws from one stable continuous distribution, the sample maximum is an upper bound that covers at least fraction p of that distribution with confidence one minus p raised to sample size n. Solving for n shows why strong tail claims require many independent observations. The code returns the minimum n for this particular maximum-based plan. It does not compute a two-sided interval, correct for dependence or certify a changing process. With discrete tied values the continuous derivation may be conservative, but the sampling unit must still be defensible.'),
            ('Distinguish the sample from a stable process', 'Taking thirty pouch weights consecutively from one short run may deliver far less independent information than thirty batches across ordinary conditions. A tolerance statement for future output needs a stable, representative sampling regime. Inspect shift, ingredient batch and device state; if the line drifts, one stationary population is a doubtful model. [[applied-statistics/capability-index-after-stability|The capability lesson]] starts with stability. A maximum contaminated by a recording error should trigger an audit, not an automatic deletion.'),
            ('Compare the bound with the fixed limit', 'After sampling under the declared plan, compare the observed sample maximum with the engineering upper limit; if the maximum exceeds that limit, this simple upper-bound demonstration cannot support the desired claim. If it does not, state the exact coverage and confidence attached to the design, sample size, time window and independence assumptions. More sophisticated tolerance methods can be shorter under justified distributional assumptions, but the assumption itself must be examined. [[applied-statistics/fill-weight-capability-project|The project]] combines the bound with process diagnostics.')
        ], '''from math import ceil, log

def required_maximum_sample_size(population_fraction, confidence):
    if not 0 < population_fraction < 1 or not 0 < confidence < 1:
        raise ValueError("fraction and confidence must lie strictly between zero and one")
    return ceil(log(1 - confidence) / log(population_fraction))

required = required_maximum_sample_size(0.90, 0.95)
assert required == 29
assert 1 - 0.90 ** required >= 0.95
assert 1 - 0.90 ** (required - 1) < 0.95
''', 'Planning n from the closed-form expression is O(1). Measuring n independent items is O(n) work; storing their values and batch metadata costs O(n). The method is conservative for some aims, yet it makes the cost of a population-tail claim explicit.',
        ['Using a narrow confidence interval for mean weight as proof most pouches comply.', 'Calling consecutive measurements from one batch independent future-production draws.', 'Choosing population fraction or confidence after seeing the maximum.', 'Treating an upper bound for one tail as a two-sided guarantee.'],
        ['capability-index-after-stability', 'fill-weight-capability-project', 'confidence-interval-coverage', 'distribution-quantiles-and-outlier-policy', 'repeatability-pooled-within-item']),
    lesson('fill-weight-capability-project',
        'Project: qualify a pouch-filling line against fixed weight limits', CAPABILITY,
        'Audit process stability, measurement repeatability and population-tail evidence before recommending a line release.', [
            ('Freeze specifications and collection', 'A food-packaging plant requires sealed pouches within 247 to 253 grams and considers a line upgrade. Record the product specification, target fill, line identity, scale calibration, production shifts and ingredient batches before collecting measurements. Sample across ordinary operating conditions and retain chronological order. A calibration change during the study defines a new measurement regime, not just another value in the same distribution. [[applied-statistics/repeatability-pooled-within-item|The repeatability lesson]] helps quantify scale noise.'),
            ('Check the process before the index', 'Plot fill weight by time, shift and batch; investigate drifts, steps and outlying periods. Only after a defensible stable window is identified should a normal-model Cpk be interpreted for that window. Compare observed lower- and upper-limit failures with the model’s tail expectation. [[applied-statistics/capability-index-after-stability|The capability lesson]] shows what the index means; [[applied-statistics/cusum-reference-and-alarm|the monitoring lesson]] supports an ongoing alarm rule after release. Do not choose a stable-looking window solely because it produces a favorable index.'),
            ('Ask for individual-outcome evidence', 'If the decision requires a stated share of future pouches below the upper engineering limit, use a tolerance-bound design or another justified population-tail method. The maximum-based construction requires independent samples from one stable process and has its own required sample size. [[applied-statistics/one-sided-tolerance-bound|The tolerance lesson]] gives that tradeoff. Neither a small standard error for the mean nor an attractive point Cpk removes uncertainty about rare underfill or overfill.'),
            ('Ship a reviewable qualification', 'The packet contains fixed limits, target, full time trace, line and batch coverage, missing readings, calibration ledger, distribution diagnostics, capability estimate and its basis, and the tail claim with confidence. The gate below refuses qualification if stability or independent sampling has not been established. Passing sends the packet for operations review; it does not replace line monitoring after production restarts.')
        ], '''def fill_line_gate(packet):
    if not packet["specifications_frozen"]:
        return "hold:engineering-limits"
    if not packet["measurement_system_checked"]:
        return "hold:scale"
    if not packet["stable_window_justified"]:
        return "hold:process-stability"
    if packet["tail_claim"] and not packet["independent_tail_sample"]:
        return "hold:tail-sample"
    return "review:fill-line"

packet = {"specifications_frozen": True, "measurement_system_checked": True,
          "stable_window_justified": True, "tail_claim": True,
          "independent_tail_sample": False}
assert fill_line_gate(packet) == "hold:tail-sample"
assert fill_line_gate({**packet, "independent_tail_sample": True}) == "review:fill-line"
''', 'The gate is O(1); checking n measurements in time and by batch is O(n) expected time, while storage of the trace is O(n). Additional independent batches cost production time. Reducing code cannot replace observing the conditions the line will actually face.',
        ['Replacing engineering limits with limits estimated from the same sample.', 'Selecting only the most stable-looking hours for the capability report.', 'Using average-weight precision to claim individual pouches meet limits.', 'Stopping monitoring because an initial qualification passed.'],
        ['capability-index-after-stability', 'one-sided-tolerance-bound', 'repeatability-pooled-within-item', 'cusum-reference-and-alarm', 'distribution-quantiles-and-outlier-policy'], True)
]

modules = [RATIOS, SPATIAL, CAPABILITY]
crosslinks = [
    (A + 'poisson-count-rate-and-exposure', A + 'ratio-of-totals-vs-average-ratios'),
    (A + 'survey-design-variance-and-psu', A + 'ratio-delta-uncertainty'),
    (A + 'cluster-bootstrap-and-standard-error', A + 'ratio-delta-uncertainty'),
    (A + 'branch-compliance-sampling-project', A + 'depot-damage-ratio-project'),
    (A + 'serial-correlation-and-effective-information', A + 'spatial-neighbor-dependence-and-moran-statistic'),
    (A + 'clustered-regression-score-and-dependence', A + 'spatial-neighbor-dependence-and-moran-statistic'),
    (A + 'rolling-origin-backtest-and-forecast-horizon', A + 'buffered-spatial-holdout'),
    (A + 'staffing-demand-forecast-project', A + 'branch-demand-spatial-project'),
    (A + 'process-shift-vs-scheduled-change', A + 'capability-index-after-stability'),
    (A + 'repeatability-pooled-within-item', A + 'capability-index-after-stability'),
    (A + 'confidence-interval-coverage', A + 'one-sided-tolerance-bound'),
    (A + 'parcel-scale-agreement-project', A + 'fill-weight-capability-project'),
]

if __name__ == '__main__':
    publish(lessons, modules, crosslinks,
            'aitrove-applied-statistics-ratios-spatial-capability-20261007.json',
            8503, subject='applied-statistics',
            hub_path=A + 'applied-statistics-tutorial')
