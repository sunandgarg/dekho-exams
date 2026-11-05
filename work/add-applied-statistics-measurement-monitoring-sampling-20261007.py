"""Add Applied Statistics lessons on measurement agreement, process shifts and finite-frame sampling."""
from de_batch_publisher import publish

A = 'applied-statistics/'
MEASUREMENT = 'Continuous measurement agreement and repeatability'
MONITORING = 'Process shifts and sequential monitoring'
SAMPLING = 'Finite-frame sampling and nonresponse'


def lesson(slug, title, module, summary, sections, code, cost, mistakes, related, project=False):
    return dict(path=A + slug, title=title, module=module, project=project,
                summary=summary, sections=sections, code=code, cost=cost,
                mistakes=mistakes, related=[A + path for path in related])


lessons = [
    lesson('paired-device-agreement-and-limits',
        'Paired device agreement: bias, limits and decision tolerance', MEASUREMENT,
        'Agreement asks whether two instruments give close enough readings on the same units for the intended decision; correlation asks a different question.', [
            ('Pair before calculating', 'A depot weighs each sealed parcel once with a dock scale and once with a handheld scale. The comparison unit is the parcel, not the individual reading. Define the difference as handheld minus dock and keep the two readings close enough in time that a change in the parcel cannot explain the gap. A strong correlation can coexist with a constant two-kilogram bias because parcels differ widely in true mass. [[applied-statistics/paired-estimand-and-unit-matching|Paired estimands]] explain why unpaired averages discard the central comparison.'),
            ('Separate bias from spread', 'The mean paired difference estimates average directional bias in the sampled operating range. A useful descriptive interval for individual future differences, when independent differences are reasonably stable and approximately normal, is mean difference plus or minus 1.96 times their sample standard deviation. This is a limit of agreement, not a confidence interval for the mean and not a pass threshold chosen after seeing the data. The code calculates descriptive limits; it does not quantify uncertainty in those limits. [[applied-statistics/confidence-interval-coverage|Interval coverage]] addresses the separate question of repeated-sample uncertainty.'),
            ('Look for proportional error', 'Plot each pair’s difference against its paired average. If heavier parcels have larger differences, one common bias and one common spread may mislead; report agreement by mass band or choose a justified scale before fitting a calibration. Also inspect duplicate parcel IDs, unit conversions, missing pairs and repeated readings from the same parcel. Repeated pairs are dependent unless the analysis accounts for the parcel. [[applied-statistics/repeatability-pooled-within-item|The repeatability lesson]] tests whether either instrument is noisy even when the parcel is unchanged.'),
            ('Set tolerance from the operation', 'If a weight discrepancy can trigger a shipping charge, specify the acceptable individual difference in kilograms before evaluating devices. A narrow average-bias interval cannot certify that nearly every parcel meets that tolerance. Report pair count, range of masses, mean bias, limits, their uncertainty, outlying pairs and the fraction beyond tolerance. Agreement only covers the conditions sampled: an indoor calibration run does not establish performance on vibrating loading bays. [[applied-statistics/parcel-scale-agreement-project|The project]] turns these findings into a replacement decision.')
        ], '''from statistics import mean, stdev

def agreement_limits(handheld_kg, dock_kg):
    if len(handheld_kg) != len(dock_kg) or len(dock_kg) < 2:
        raise ValueError("at least two aligned parcel pairs required")
    differences = [handheld - dock for handheld, dock in zip(handheld_kg, dock_kg)]
    bias = mean(differences)
    spread = stdev(differences)
    return bias, (bias - 1.96 * spread, bias + 1.96 * spread)

bias, limits = agreement_limits([12.4, 21.8, 33.1], [12.0, 22.0, 32.5])
assert round(bias, 3) == 0.267 and limits[0] < 0 < limits[1]
''', 'Pair matching and descriptive limits take O(n) time and O(n) space for n parcels. Streaming mean and variance can reduce storage to O(1), but storing pairs supports the necessary difference-versus-average plot and record audit. More pairs do not correct a changed weighing procedure.',
        ['Substituting correlation or regression fit for agreement.', 'Calling the limits a confidence interval for average bias.', 'Choosing a tolerance after seeing the device differences.', 'Treating repeated readings of one parcel as independent parcels.'],
        ['repeatability-pooled-within-item', 'parcel-scale-agreement-project', 'paired-estimand-and-unit-matching', 'confidence-interval-coverage', 'equivalence-margins-and-two-one-sided-decisions']),
    lesson('repeatability-pooled-within-item',
        'Repeatability: pool within-item variation without hiding drift', MEASUREMENT,
        'Repeatability measures variation when the same item is measured again under specified near-identical conditions.', [
            ('Define the conditions', 'A handheld scale reads the same sealed parcel three times without changing the load, operator or setting. Differences among those readings represent short-term measurement variation under that protocol. Change operator, location, temperature or day and the question becomes broader reproducibility or stability, not short-term repeatability. Preserve those fields in the measurement table so the source of spread is visible. [[applied-statistics/paired-device-agreement-and-limits|Agreement between devices]] includes their biases as well as their noise.'),
            ('Pool within each item', 'When several parcels are repeated, compute each parcel’s mean and sum its squared deviations from that mean. Divide the combined sum by the total within-parcel degrees of freedom, then take a square root. This estimates a pooled within-item standard deviation when a common short-term variance is plausible. The implementation accepts unequal repeat counts and rejects single-reading groups; it does not estimate a between-item component. Pooling all raw readings around one grand mean would mix actual parcel mass differences into measurement noise.'),
            ('Check whether one spread fits', 'Inspect within-parcel spread against true or paired-average mass, operator and measurement order. If the scale becomes noisier above thirty kilograms, a single pooled standard deviation can understate high-mass uncertainty. Order also matters: a slow zeroing drift may yield systematic first-to-third differences that a pooled variance hides. Randomize or alternate order where practical and retain the sequence. [[applied-statistics/process-shift-vs-scheduled-change|Process-shift analysis]] addresses later drift, but it cannot repair missing order metadata.'),
            ('Translate spread into a decision', 'For two independent repeated readings from one stable instrument, their difference has standard deviation about square root of two times the within-item standard deviation under the simple constant-variance model. That statement depends on independence and the same conditions; shared calibration error does not vanish. Compare the likely repeat gap with a predeclared tolerance, and report item count, repeats per item, pooled estimate, per-item spread and order diagnostics. [[applied-statistics/parcel-scale-agreement-project|The project]] refuses a device swap if precision fails despite small average bias.')
        ], '''from math import sqrt
from statistics import mean

def pooled_repeatability(parcel_repeats):
    if not parcel_repeats or any(len(readings) < 2 for readings in parcel_repeats.values()):
        raise ValueError("each parcel needs at least two readings")
    squared_error = 0.0
    degrees_of_freedom = 0
    for readings in parcel_repeats.values():
        parcel_mean = mean(readings)
        squared_error += sum((reading - parcel_mean) ** 2 for reading in readings)
        degrees_of_freedom += len(readings) - 1
    return sqrt(squared_error / degrees_of_freedom)

repeat_sd = pooled_repeatability({"P47": [14.1, 14.3], "P82": [29.6, 29.4]})
assert round(repeat_sd, 3) == 0.141
''', 'The pooled calculation is O(n) time for n readings and O(1) extra space beyond the grouped input. Storing order, operator and instrument identifiers costs O(n) but is necessary to diagnose changing precision. An extra decimal place in the output cannot compensate for a flawed repeat protocol.',
        ['Pooling around one grand mean and calling parcel-to-parcel variation instrument noise.', 'Claiming short-term repeats cover different operators or weather conditions.', 'Ignoring a trend by measurement order because pooled spread is small.', 'Using a pooled value when precision changes sharply by mass.'],
        ['paired-device-agreement-and-limits', 'parcel-scale-agreement-project', 'process-shift-vs-scheduled-change', 'paired-estimand-and-unit-matching', 'process-overdispersion-and-measurement-drift']),
    lesson('parcel-scale-agreement-project',
        'Project: decide whether a handheld parcel scale can replace the dock scale', MEASUREMENT,
        'Run paired and repeated measurements across the operating mass range, then make a tolerance-based device decision.', [
            ('Freeze the measurement plan', 'A shipping team wants handheld readings to set chargeable parcel mass. Define the dock reference procedure, handheld device model, the permitted individual discrepancy and the mass bands that matter for billing. Sample parcels from ordinary operations, including heavy and awkward loads, and measure each on both devices near the same time. Log device IDs, operator, site, timestamp and order. The parcel is the unit for agreement; repeated readings of the same parcel are nested observations, not more parcels.'),
            ('Audit paired error and noise', 'Plot handheld-minus-dock differences against paired average mass. Compute mean bias and descriptive limits in the planned operating range; inspect whether the spread or bias grows with mass. Repeat selected parcels under one controlled setup to estimate within-item variation. [[applied-statistics/paired-device-agreement-and-limits|The agreement lesson]] defines individual-difference limits, while [[applied-statistics/repeatability-pooled-within-item|the repeatability lesson]] isolates short-term noise. If a device is precise but biased, calibration may be possible; if it is unstable, a constant correction cannot solve the problem.'),
            ('Evaluate the decision boundary', 'A parcel within a few grams of a billing threshold is more sensitive to error than one far from it. Count parcels whose device disagreement could change the fee, with mass bands and device identity shown. The acceptable discrepancy must be agreed before the results are inspected. A small average bias cannot override a wide individual-difference range. [[applied-statistics/equivalence-margins-and-two-one-sided-decisions|The equivalence lesson]] explains a different inference question about average effects and margins; it does not certify every reading.'),
            ('Ship an auditable packet', 'Keep raw pairs, repeat sequences, missing and rejected records, calibration logs, mass-band plots, tolerance failures and a decision owner. The gate below checks that sampling covers the required range and that both pairwise agreement and repeatability have been reviewed. Passing it means the evidence is ready for a human replacement decision, not that an instrument is automatically certified for every depot or future calibration state.')
        ], '''def scale_replacement_gate(audit):
    if not audit["required_mass_bands_covered"]:
        return "hold:operating-range"
    if not audit["paired_difference_reviewed"]:
        return "hold:agreement"
    if not audit["repeatability_reviewed"]:
        return "hold:repeatability"
    if audit["undocumented_calibration_changes"]:
        return "hold:calibration-history"
    return "review:device-replacement"

audit = {"required_mass_bands_covered": True, "paired_difference_reviewed": True,
         "repeatability_reviewed": False, "undocumented_calibration_changes": False}
assert scale_replacement_gate(audit) == "hold:repeatability"
assert scale_replacement_gate({**audit, "repeatability_reviewed": True}) == "review:device-replacement"
''', 'The gate is O(1); reconciling and plotting n paired records is O(n) time and space. Multiple devices and operators increase the number of conditions to sample. Skipping those conditions saves collection time by narrowing the claim, not by proving broad agreement.',
        ['Approving replacement because correlation is high.', 'Reporting only mean bias when individual billing decisions depend on tails.', 'Counting repeats from one parcel as independent parcel coverage.', 'Changing the acceptable error after seeing the differences.'],
        ['paired-device-agreement-and-limits', 'repeatability-pooled-within-item', 'equivalence-margins-and-two-one-sided-decisions', 'paired-estimand-and-unit-matching', 'process-overdispersion-and-measurement-drift'], True),
    lesson('process-shift-vs-scheduled-change',
        'Process shifts: separate a scheduled intervention from a searched break', MONITORING,
        'A known intervention date defines one before-and-after comparison; searching many possible dates creates a selection problem.', [
            ('Start with the event timeline', 'A warehouse changes its scanning procedure on a recorded Monday. If the date was fixed before examining scan latency, compare prespecified pre and post windows, while checking staffing, parcel mix and seasonality. If an analyst chose the date because the chart looked different, the ordinary two-window uncertainty understates the search. The code calculates only a descriptive mean gap after a declared split. It does not estimate a causal effect or an adjusted interval. [[applied-statistics/serial-correlation-and-effective-information|Serial dependence]] further reduces independent information in daily readings.'),
            ('Watch for calendar structure', 'Weekly peaks can resemble a break if the before window contains mostly weekends and the after window mostly weekdays. Use like-for-like days or a model that includes calendar effects, and retain the full time axis. A process can drift gradually rather than jump; forcing one step change may produce an attractive but misleading date. Inspect missing days and logging changes before interpreting a shift as an operational event. [[applied-statistics/rolling-origin-backtest-and-forecast-horizon|Rolling evaluation]] offers a way to test whether a time model generalizes beyond one split.'),
            ('Treat searched dates as exploration', 'If no intervention date was planned, a scan over candidate breaks can be useful to locate investigation periods. But the best-looking split is selected from many trials. A confirmatory claim needs a separate later window, a search-aware uncertainty method or a preregistered next intervention. Report every eligible candidate date and the selection rule, not only the maximum contrast. [[applied-statistics/multiple-comparisons-and-stopping-rule|Multiplicity]] explains why unadjusted repeated looks make false alarms more likely.'),
            ('Keep detection and attribution apart', 'An apparent rise may coincide with a software update, new parcel mix or a delayed data feed. A shift detector can say the stream changed under its assumptions; it cannot identify the cause from the same series alone. Pair operational logs with time-ordered checks and state which units were independently observed. [[applied-statistics/cusum-reference-and-alarm|The CUSUM lesson]] covers prospective alarms; [[applied-statistics/scan-latency-shift-project|the project]] joins them to a release packet.')
        ], '''from statistics import mean

def scheduled_gap(daily_latency_ms, intervention_index):
    if not 2 <= intervention_index <= len(daily_latency_ms) - 2:
        raise ValueError("at least two days on each side required")
    before = daily_latency_ms[:intervention_index]
    after = daily_latency_ms[intervention_index:]
    return mean(after) - mean(before)

assert scheduled_gap([81, 83, 82, 95, 97, 96], 3) == 14
''', 'One known split takes O(n) time and O(1) extra space over an existing list. Scanning every possible split naively costs O(n squared); prefix sums reduce the arithmetic to O(n), but they do not remove the statistical selection cost. More efficient search is not stronger causal evidence.',
        ['Treating a visually chosen break date as if it had been prespecified.', 'Calling any mean gap an effect of the warehouse procedure.', 'Comparing different weekday mixes without a calendar check.', 'Using daily row count as the number of independent shifts when serial correlation is present.'],
        ['cusum-reference-and-alarm', 'scan-latency-shift-project', 'serial-correlation-and-effective-information', 'multiple-comparisons-and-stopping-rule', 'rolling-origin-backtest-and-forecast-horizon']),
    lesson('cusum-reference-and-alarm',
        'CUSUM alarms: set reference and threshold before reading the stream', MONITORING,
        'A cumulative-sum monitor adds small standardized departures from an in-control target and signals when evidence crosses a fixed decision limit.', [
            ('Freeze a stable baseline', 'A depot monitors mean scan latency per shift. Estimate its target and baseline standard deviation from a documented stable period with the same measurement procedure. For a one-sided upward chart, standardize each new shift result, subtract a reference allowance and accumulate positive excess, resetting the sum to zero when evidence runs against the shift. Choose the allowance and decision limit before the monitored series arrives. The code shows the recurrence; it does not select thresholds or calculate false-alarm rates. [[applied-statistics/process-shift-vs-scheduled-change|The break lesson]] separates prospective detection from an after-the-fact search.'),
            ('Interpret the reference allowance', 'A smaller allowance can retain weaker positive deviations, while a larger one filters more noise. The decision limit controls how much accumulated evidence is needed. Both affect false alarms and detection delay, so calibrate them against an acceptable in-control alarm frequency and the shift size that matters to operations. Do not copy a threshold from a different variable with different units or serial dependence. [[applied-statistics/varying-denominator-p-chart|Varying denominator charts]] handle a distinct fraction outcome.'),
            ('Account for dependence and mix', 'If successive shift averages share the same outages or workload, the standardized inputs are not independent. An alarm rate calibrated under independence can be wrong. Changes in parcel mix may also raise latency without a scanner defect. Rebaseline only through a documented rule after investigation; resetting whenever the chart alarms conceals a persistent shift. Preserve the full running path, missing shifts and any replacement of baseline estimates. [[applied-statistics/serial-correlation-and-effective-information|The serial-correlation lesson]] explains the information loss.'),
            ('Connect alarm to an action', 'An alarm starts diagnosis, not a declaration that a particular software release caused delay. Record the first crossing, threshold version, affected sites, raw shift measurements and competing operational events. A later quiet period does not erase a prior alarm from the audit trail. [[applied-statistics/scan-latency-shift-project|The project]] gates a claim on baseline integrity, calendar checks and a response owner.')
        ], '''def upward_cusum(shift_latency_ms, target_ms, baseline_sd, allowance, limit):
    if baseline_sd <= 0 or allowance < 0 or limit <= 0:
        raise ValueError("valid baseline and chart settings required")
    running = 0.0
    first_alarm = None
    path = []
    for shift_index, latency in enumerate(shift_latency_ms):
        standardized = (latency - target_ms) / baseline_sd
        running = max(0.0, running + standardized - allowance)
        path.append(running)
        if running >= limit and first_alarm is None:
            first_alarm = shift_index
    return first_alarm, path

alarm, chart = upward_cusum([80, 81, 86, 87, 88], 80, 4, 0.25, 2.0)
assert alarm == 3 and chart[-1] >= 2
''', 'The monitor takes O(n) time and O(n) space when retaining n chart values; alerting with only the latest state is O(1) space. Calibration by historical simulation costs more and depends on a credible stable baseline. One fast alarm rule cannot make correlated shifts independent.',
        ['Tuning the decision limit after looking at the alerts.', 'Resetting the baseline after an alarm without recording the investigation.', 'Calling the first alarm the cause or exact onset of a change.', 'Applying independent-input false-alarm claims to serially correlated shift data.'],
        ['process-shift-vs-scheduled-change', 'scan-latency-shift-project', 'serial-correlation-and-effective-information', 'varying-denominator-p-chart', 'process-overdispersion-and-measurement-drift']),
    lesson('scan-latency-shift-project',
        'Project: investigate a warehouse scan-latency alarm', MONITORING,
        'Build a time-ordered latency monitor and release a shift claim only after baseline, calendar and logging checks.', [
            ('Reconcile the series', 'A network of warehouses reports a sudden increase in time from barcode scan to inventory acknowledgement. Define that clock precisely, pin the event schema version and count missing or retried scans separately. Aggregate at the shift or another justified unit, retaining workload, site, software version and timestamp. An application change that moves the clock start can imitate slower processing even if customers see no difference. [[applied-statistics/process-overdispersion-and-measurement-drift|Measurement drift]] is therefore part of the incident review.'),
            ('Choose the analysis path', 'If the rollout date was recorded before the series was inspected, run the planned before-and-after diagnostic with matched weekdays and workload checks. If the date was found from the plot, label the result exploratory and validate on later shifts. For continuing monitoring, freeze a stable baseline and prospective CUSUM settings. [[applied-statistics/process-shift-vs-scheduled-change|The break lesson]] prevents a searched split from masquerading as a planned comparison; [[applied-statistics/cusum-reference-and-alarm|the chart lesson]] sets the alarm mechanism.'),
            ('Investigate competing explanations', 'Trace release logs, staffing, parcel size, scanner model, backlog and data-feed delay. Compare the direction and timing of changes across sites that adopted the release on different dates, but do not claim random assignment where rollout was chosen by site readiness. Keep the entire alarm path and report how serial dependence affects the uncertainty around a change. A significant before-after contrast cannot by itself distinguish software from concurrent operations changes.'),
            ('Deliver the incident packet', 'The packet includes the frozen metric and baseline, threshold configuration, complete time series, alarm time, planned or searched status, calendar comparison, missingness and competing-event log. The gate below stops a causal-looking claim when a logging definition changed or the alert was tuned on the same series. Once the packet passes, an incident owner can decide whether to roll back, run a targeted experiment or monitor further.')
        ], '''def scan_shift_gate(review):
    if not review["clock_definition_stable"]:
        return "hold:metric-definition"
    if not review["baseline_frozen_before_monitoring"]:
        return "hold:baseline"
    if not review["calendar_and_load_checked"]:
        return "hold:calendar-load"
    if review["searched_date_reported_as_planned"]:
        return "hold:search-disclosure"
    return "review:shift-incident"

review = {"clock_definition_stable": True, "baseline_frozen_before_monitoring": True,
          "calendar_and_load_checked": False, "searched_date_reported_as_planned": False}
assert scan_shift_gate(review) == "hold:calendar-load"
assert scan_shift_gate({**review, "calendar_and_load_checked": True}) == "review:shift-incident"
''', 'The gate is O(1). Aggregating n scan events by shift is O(n) expected time, and preserving the event trail uses O(n) space. Chart computation is cheap; validating the metric and comparing operational histories dominate the work. A smaller algorithm does not replace a stable clock.',
        ['Treating a software rollout date found after looking at latency as prespecified.', 'Claiming a CUSUM alarm proves a particular release caused the shift.', 'Dropping missing or retried scans from the denominator without disclosure.', 'Rebaselining silently to make the alarm disappear.'],
        ['process-shift-vs-scheduled-change', 'cusum-reference-and-alarm', 'serial-correlation-and-effective-information', 'process-overdispersion-and-measurement-drift', 'blocked-randomization-permutation-test'], True),
    lesson('finite-frame-sampling-and-correction',
        'Finite-frame sampling: adjust uncertainty for sampling without replacement', SAMPLING,
        'A simple random sample drawn without replacement from a known finite frame has less sampling variance than an equal-sized independent-draw model.', [
            ('Specify the finite target', 'An auditor has a complete register of 347 active retail branches and selects 91 distinct branches by simple random sampling without replacement. The target is the mean outcome among those 347 branches at the defined date, not a hypothetical unlimited supply of branches. When the sample is a material fraction of the frame, selecting one branch removes it from possible future selections. That dependence reduces sampling uncertainty. The frame must be complete and each listed branch must have a known equal selection chance. [[applied-statistics/population-estimand-and-sampling-frame|The frame lesson]] defines that boundary.'),
            ('Apply the correction at the right stage', 'For a simple random sample without replacement, estimate variance of the sample mean as sample variance divided by sample size, multiplied by one minus the sampling fraction n over N. This common finite-population correction is for design-based uncertainty about the fixed finite mean. It reaches zero at a census with complete measurement; measurement error and nonresponse do not vanish. The code implements this specific equal-probability design. Stratified, clustered or unequal-probability samples require their own design variance. [[applied-statistics/survey-design-variance-and-psu|The survey-design lesson]] handles those cases.'),
            ('Do not repair a defective frame with arithmetic', 'A low variance estimate from a large sampling fraction can still be biased if closed branches remain listed, new branches are missing, or branch outcomes are recorded differently. The correction describes variability from random selection under the stated design, not coverage error. The initial sample size and actual respondent count also differ: treating a small respondent set as if it were a census of the frame is invalid. [[applied-statistics/nonresponse-bounds-for-binary-outcomes|Response bounds]] make the missing-outcome risk visible.'),
            ('Report the basis and scope', 'Show N, selected n, measured n, the selection procedure, sample variance, corrected standard error and any frame changes. A smaller standard error is justified only where the draw really was without replacement from the fixed frame. If the decision concerns future branch openings, the finite-frame estimate may have the wrong target; a future-process model asks a different question. [[applied-statistics/branch-compliance-sampling-project|The project]] uses the correction only after reconciling the register and response ledger.')
        ], '''from math import sqrt
from statistics import variance

def finite_frame_mean_se(measured_values, frame_size):
    selected_count = len(measured_values)
    if selected_count < 2 or frame_size < selected_count:
        raise ValueError("at least two selected units and a valid frame required")
    estimated_variance = variance(measured_values) / selected_count
    return sqrt(estimated_variance * (1 - selected_count / frame_size))

assert finite_frame_mean_se([4.0, 8.0, 6.0], 3) == 0
assert finite_frame_mean_se([4.0, 8.0, 6.0], 15) > 0
''', 'Computing a sample variance and corrected standard error takes O(n) time and O(1) extra space over the existing measurements. Frame reconciliation is an O(N) audit and may be harder than the calculation. This simple formula must not be reused for a clustered design.',
        ['Applying simple-random-sample correction to a clustered or unequal-probability sample.', 'Claiming a census has no measurement or coverage error because sampling SE is zero.', 'Using respondent count as selected count without addressing nonresponse.', 'Using the finite-frame estimate to make claims about unknown future branches.'],
        ['nonresponse-bounds-for-binary-outcomes', 'branch-compliance-sampling-project', 'population-estimand-and-sampling-frame', 'survey-design-variance-and-psu', 'stratified-survey-estimate-and-population-weights']),
    lesson('nonresponse-bounds-for-binary-outcomes',
        'Nonresponse bounds: show what missing binary outcomes could change', SAMPLING,
        'When selected units have missing binary outcomes, the full selected-sample rate lies between treating all missing as zero and all missing as one.', [
            ('Keep selected and answered units separate', 'A compliance team draws 91 branches from its register; 73 return a yes-or-no audit result and 18 do not. The observed respondent rate is successes divided by 73, but the selected-sample rate uses 91 branches. If missing outcomes may differ from observed outcomes, a response-weighted estimate needs assumptions or useful auxiliary information. The crude bounds require no such outcome assumption: divide known successes by selected count for the low end, and add missing count for the high end. [[applied-statistics/missing-outcome-ledger-and-target-population|The missing-outcome ledger]] records why each branch is absent.'),
            ('Read bounds as a sensitivity range', 'Suppose 52 of 73 responding branches pass. Among the 91 selected, the pass rate is at least 52 divided by 91 and at most 70 divided by 91. These are logical bounds for the selected set, not a confidence interval for all 347 branches; sampling uncertainty around the population target is another layer. The code enforces the arithmetic and reports response fraction. A narrow range arises when few selected outcomes are missing, not when respondents happen to look similar on an unrelated field.'),
            ('Investigate selection before weighting', 'Compare response by region, branch size, visit type and prior compliance if those fields exist for every selected branch. A high response fraction alone does not rule out bias when the few missing branches are systematically different; a low fraction does not prove a large bias. Weighting on observed fields can reduce some imbalance if response is explainable by those fields, but it cannot identify missing outcomes without assumptions. [[applied-statistics/observation-probability-weighting-and-sensitivity|Response weighting]] and [[applied-statistics/survey-poststratification-and-raking-margins|calibration]] need those assumptions made explicit.'),
            ('Use a decision threshold honestly', 'If even the lower bound exceeds a required pass threshold, missing outcomes cannot reverse the selected-sample decision. If the interval straddles the threshold, follow-up measurement has direct value. Do not apply a finite-population correction to erase nonresponse; it addresses random selection variance only. Report selected count, answered count, reasons, outcome bounds, response-by-group checks and the target population. [[applied-statistics/branch-compliance-sampling-project|The project]] combines these checks without confusing logical bounds with uncertainty intervals.')
        ], '''def selected_binary_bounds(selected_count, answered_count, known_successes):
    if not 0 < selected_count or not 0 <= known_successes <= answered_count <= selected_count:
        raise ValueError("counts must describe one selected sample")
    missing_count = selected_count - answered_count
    return (known_successes / selected_count,
            (known_successes + missing_count) / selected_count,
            answered_count / selected_count)

low, high, response_fraction = selected_binary_bounds(91, 73, 52)
assert round(low, 3) == 0.571 and round(high, 3) == 0.769
assert round(response_fraction, 3) == 0.802
''', 'The bounds use O(1) time and space from reconciled counts. Building a per-branch response ledger costs O(n) storage and enables group audits. Extra modeling may narrow a decision range, but only by adding assumptions and independent information that the simple bounds intentionally avoid.',
        ['Calling the logical bounds a confidence interval for the population rate.', 'Using the respondent denominator for the selected-sample bound.', 'Assuming a high response rate guarantees no nonresponse bias.', 'Claiming the finite-population correction fixes unobserved outcomes.'],
        ['finite-frame-sampling-and-correction', 'branch-compliance-sampling-project', 'missing-outcome-ledger-and-target-population', 'observation-probability-weighting-and-sensitivity', 'survey-poststratification-and-raking-margins']),
    lesson('branch-compliance-sampling-project',
        'Project: audit branch compliance with a finite sample and missing replies', SAMPLING,
        'Reconcile a branch sampling frame, quantify simple-random-sample uncertainty and show how nonresponse affects a pass-rate decision.', [
            ('Freeze the frame and draw', 'A national operations team must estimate the share of active branches meeting a document-retention rule. Pin the register date, exclude closed locations using a written rule and draw distinct branch IDs with a recorded random seed. A branch is the selection unit. If the draw is stratified or regional teams choose branches by judgment, do not label it a simple random sample. Preserve the frame, selection file and visit protocol. [[applied-statistics/population-estimand-and-sampling-frame|The sampling-frame lesson]] ties the denominator to the claim.'),
            ('Reconcile measurement and response', 'Mark each selected branch as answered, refused, unreachable or ineligible; track why the classification changed. Among answered branches, record the binary compliance outcome and inspection date. A repeated inspection does not create a newly selected branch. Compute respondent summaries, but keep missing branch outcomes unresolved. [[applied-statistics/nonresponse-bounds-for-binary-outcomes|The bounds lesson]] supplies a no-assumption selected-sample range and points to useful follow-up interviews.'),
            ('Calculate design uncertainty conditionally', 'For a complete simple random sample without replacement, use the finite-frame variance for an estimated mean, with frame size N and selected size n. If outcomes are missing, that complete-data formula cannot simply be applied to respondents as though response were another equal-probability draw. Document any response model, weighting and sensitivity interval separately. [[applied-statistics/finite-frame-sampling-and-correction|The finite-frame lesson]] states the formula and its limit; [[applied-statistics/survey-design-variance-and-psu|design variance]] covers more complex draws.'),
            ('Release a qualified decision', 'Report the fixed frame, selected and answered counts, response pattern by known branch traits, observed rate, logical selected-sample bounds, sampling uncertainty under a stated design and the operational pass threshold. The gate below holds release when branch identities, response status or the design are unresolved. Passing it sends the packet to review; it does not authorize a precise population interval when missingness assumptions are unsupported.')
        ], '''def branch_audit_gate(packet):
    if not packet["frame_reconciled"]:
        return "hold:frame"
    if not packet["selection_design_recorded"]:
        return "hold:draw"
    if not packet["response_status_complete"]:
        return "hold:response-ledger"
    if packet["missing_outcomes"] and not packet["bounds_reported"]:
        return "hold:missingness-range"
    return "review:branch-compliance"

packet = {"frame_reconciled": True, "selection_design_recorded": True,
          "response_status_complete": True, "missing_outcomes": 18,
          "bounds_reported": False}
assert branch_audit_gate(packet) == "hold:missingness-range"
assert branch_audit_gate({**packet, "bounds_reported": True}) == "review:branch-compliance"
''', 'The release gate is O(1); checking a frame of N branches and n selected responses is O(N+n) expected time with indexed IDs. A simple formula takes almost no compute, while tracing branch eligibility and missing outcomes determines whether the formula means anything.',
        ['Calling a judgment sample a simple random draw.', 'Calculating a finite-frame standard error on respondents without a response assumption.', 'Collapsing refused, unreachable and ineligible branches into one silent exclusion.', 'Declaring the population pass rate certain because most branches were sampled.'],
        ['finite-frame-sampling-and-correction', 'nonresponse-bounds-for-binary-outcomes', 'population-estimand-and-sampling-frame', 'survey-design-variance-and-psu', 'contact-center-calibration-project'], True)
]

modules = [MEASUREMENT, MONITORING, SAMPLING]
crosslinks = [
    (A + 'paired-estimand-and-unit-matching', A + 'paired-device-agreement-and-limits'),
    (A + 'confidence-interval-coverage', A + 'paired-device-agreement-and-limits'),
    (A + 'equivalence-margins-and-two-one-sided-decisions', A + 'parcel-scale-agreement-project'),
    (A + 'process-overdispersion-and-measurement-drift', A + 'repeatability-pooled-within-item'),
    (A + 'serial-correlation-and-effective-information', A + 'process-shift-vs-scheduled-change'),
    (A + 'multiple-comparisons-and-stopping-rule', A + 'process-shift-vs-scheduled-change'),
    (A + 'varying-denominator-p-chart', A + 'cusum-reference-and-alarm'),
    (A + 'staffing-demand-forecast-project', A + 'scan-latency-shift-project'),
    (A + 'population-estimand-and-sampling-frame', A + 'finite-frame-sampling-and-correction'),
    (A + 'survey-design-variance-and-psu', A + 'finite-frame-sampling-and-correction'),
    (A + 'missing-outcome-ledger-and-target-population', A + 'nonresponse-bounds-for-binary-outcomes'),
    (A + 'observation-probability-weighting-and-sensitivity', A + 'nonresponse-bounds-for-binary-outcomes'),
    (A + 'contact-center-survey-audit-project', A + 'branch-compliance-sampling-project'),
]

if __name__ == '__main__':
    publish(lessons, modules, crosslinks,
            'aitrove-applied-statistics-measurement-monitoring-sampling-20261007.json',
            8494, subject='applied-statistics',
            hub_path=A + 'applied-statistics-tutorial')
