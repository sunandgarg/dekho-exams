"""Add original Data Science lessons on sampling and resilient analysis."""
import datetime
import html
import json
from pathlib import Path
import re
import uuid

root = Path(__file__).resolve().parents[1]
fixture = root / 'src/data/fixtures.json'
rows = json.loads(fixture.read_text())
new_slugs = (
    'sampling-frame-and-coverage-error', 'stratified-sampling-and-design-weights',
    'nonresponse-bias-and-follow-up', 'precision-budget-and-effective-sample-size',
    'support-case-audit-sampling-project', 'column-profile-and-domain-constraints',
    'outlier-investigation-and-quarantine', 'robust-summaries-and-mad',
    'subgroup-distribution-and-aggregation-reversal', 'fulfillment-delay-analysis-project',
)
new_paths = {'data-science/' + slug for slug in new_slugs}
rows = [row for row in rows if row['path'] not in new_paths]
by_path = {row['path']:row for row in rows}
stamp = datetime.datetime.now(datetime.UTC).isoformat()
lessons = []

def add(slug, title, summary, sections, code, cost, mistakes, related):
    lessons.append(dict(path='data-science/' + slug, title=title, summary=summary,
                        sections=sections, code=code, cost=cost,
                        mistakes=mistakes, related=related))

add('sampling-frame-and-coverage-error',
    'Sampling frames and coverage error: who could enter the analysis?',
    'A sampling frame is the operational list from which observations can be selected; it may not cover the population the decision concerns.', [
    ('Specify the population first', 'A support team wants the defect rate among all submitted cases last quarter. Its export contains only cases assigned to agents, omitting self-service closures and bounced submissions. Even a random draw from that export cannot recover the absent units. Define the case identity, eligibility window, decision time and outcome before querying. [[data-science/dataset-grain-and-join-cardinality|Dataset grain]] prevents one case with several status events from counting several times.'),
    ('Audit the frame', 'Compare eligible intake IDs with the export. Count missing IDs, duplicate IDs, unknown eligibility and records that arrived after the cutoff. Break the differences down by channel and week. Coverage error is not the same as random sampling error: a larger draw from a systematically incomplete list can make the estimate more precise around the wrong quantity. [[applied-statistics/population-estimand-and-sampling-frame|The estimand]] defines what the final number is allowed to describe.'),
    ('Record selection before outcomes', 'Freeze the frame version and selection mechanism before viewing labels. If high-severity cases have a separate queue, include that queue or limit the claim to the ordinary queue. Capture inclusion probability for each selected unit and a reason for excluded units. Later joins to reviewer decisions should use stable case IDs and an as-of cutoff, not a mutable current-status table.'),
    ('Rehearse a discrepancy', 'Suppose 1,500 intake IDs appear in the event log, but only 1,320 are in the agent export. Of the 180 missing, 145 are self-service closures and 35 failed assignment. A defect estimate from the export applies to assigned cases unless those groups are separately measured or brought into the frame. Report the 180-case gap before quoting a rate.')],
    'def coverage_gaps(eligible_case_ids, frame_case_ids):\n    eligible = set(eligible_case_ids)\n    frame = set(frame_case_ids)\n    return {"missing": eligible - frame,\n            "out_of_scope": frame - eligible,\n            "covered": eligible & frame}',
    'Building two ID sets costs O(N + M) expected time and space for N eligible IDs and M frame IDs. The result checks coverage by identity; deciding eligibility and resolving duplicate business entities require separate rules.',
    ['Do not call a random sample representative when the frame excludes a channel.', 'Do not use current mutable status to reconstruct last quarter’s eligibility.', 'Do not count status events as distinct cases.'],
    ['data-science/stratified-sampling-and-design-weights','data-science/nonresponse-bias-and-follow-up','data-science/dataset-grain-and-join-cardinality','applied-statistics/population-estimand-and-sampling-frame'])

add('stratified-sampling-and-design-weights',
    'Stratified sampling and design weights for operational estimates',
    'A stratified sample draws within named groups; a population estimate must reflect each group’s population size and selection probability.', [
    ('Choose strata before drawing', 'Divide the eligible support-case frame by intake channel and severity only when those fields are known for every case at selection time. Oversample a rare partner channel to study it well, but preserve its population count. A convenience queue is not a probability sample just because it contains several groups. [[data-science/sampling-frame-and-coverage-error|Frame coverage]] must be checked before weighting can repair unequal selection.'),
    ('Estimate at the right scale', 'Suppose the main channel has 1,200 cases, with 24 defects in a random sample of 120. The partner channel has 300 cases, with 24 defects in a random sample of 60. Their rates are 20% and 40%. The population-weighted rate is (1,200 × 0.20 + 300 × 0.40) / 1,500 = 24%. Pooling the 48 defects over 180 sampled cases gives 26.7% because the partner channel was oversampled.'),
    ('Carry weights with records', 'Within a simple random sample from a stratum, the base weight is population count divided by sample count. Save stratum, sample design, selection probability and weight beside the reviewed outcome. Do not recompute a weight from the number of respondents if nonresponse changes the denominator; response adjustment is a separate assumption. [[data-science/nonresponse-bias-and-follow-up|Nonresponse analysis]] asks whether the respondents resemble the selected nonrespondents.'),
    ('Report both group and total', 'Show each stratum’s population count, sample count, observed defect count and uncertainty, then the weighted total. A small stratum can have a noisy rate even when its overall weighted contribution is modest. If sampling occurred in clusters, such as stores or agents, a simple independent-case standard error is too optimistic. [[applied-statistics/cluster-bootstrap-and-standard-error|Cluster-aware uncertainty]] should match the actual draw.')],
    'def stratified_defect_rate(strata):\n    population = sum(group["population_count"] for group in strata)\n    if population == 0 or any(group["sample_count"] == 0 for group in strata):\n        raise ValueError("empty population or stratum sample")\n    return sum(group["population_count"] * group["defect_count"] / group["sample_count"]\n               for group in strata) / population\n\nassert stratified_defect_rate([\n    {"population_count": 1200, "sample_count": 120, "defect_count": 24},\n    {"population_count": 300, "sample_count": 60, "defect_count": 24},\n]) == 0.24',
    'The estimate scans S strata in O(S) time and O(1) auxiliary space. Drawing samples and computing design-based uncertainty cost more; large weights reduce effective information and should be reported.',
    ['Do not pool oversampled strata without weights.', 'Do not assume stratification removes frame or nonresponse bias.', 'Do not use a case-level standard error for clustered selection.'],
    ['data-science/sampling-frame-and-coverage-error','data-science/nonresponse-bias-and-follow-up','data-science/precision-budget-and-effective-sample-size','applied-statistics/cluster-bootstrap-and-standard-error'])

add('nonresponse-bias-and-follow-up',
    'Nonresponse bias: diagnose the missing outcomes before adjusting',
    'Nonresponse occurs when a selected unit lacks the outcome needed for analysis; its bias depends on how nonrespondents differ from respondents.', [
    ('Separate absence types', 'A case never selected is not a nonrespondent. A selected case whose reviewer could not retrieve its attachment is. Record selection, contact or retrieval attempt, response state and reason independently. Compare response by channel, week and severity using fields known for the full selected sample. [[data-science/missing-data-policy|Missing-data policy]] also distinguishes unknown evidence from a measured zero.'),
    ('Quantify what is known', 'For binary outcomes, a simple bound within the selected sample treats every missing case as non-defective for the lower bound and defective for the upper bound. If 31 of 47 selected cases were reviewed and 6 defects were found, the selected-sample defect fraction lies from 6/47 to 22/47 without further assumptions. These are deliberately wide bounds; they are not population confidence intervals and do not correct the sampling design.'),
    ('Use follow-up to learn', 'Choose a random subset of nonrespondents for a more expensive retrieval attempt. Record the second-stage selection probability and outcome. A successful follow-up can reveal whether ordinary respondents were unusually easy or hard cases. Adjustment weights based on observed covariates only reduce bias under assumptions about response within those groups. If the missing outcome itself drives response, weighting cannot make the problem disappear.'),
    ('Publish sensitivity, not certainty', 'Report the original response rate, response by stratum, follow-up yield and estimates under several plausible assumptions. Separate the observed rate among respondents from a weighted target-population estimate. When results change sign under modest assumptions about missing cases, the decision is not stable. [[data-science/precision-budget-and-effective-sample-size|More sampling]] may not help until the retrieval process improves.')],
    'def binary_outcome_bounds(positive_count, reviewed_count, selected_count):\n    if not 0 <= positive_count <= reviewed_count <= selected_count or selected_count == 0:\n        raise ValueError("invalid selected-sample counts")\n    missing_count = selected_count - reviewed_count\n    return positive_count / selected_count, (positive_count + missing_count) / selected_count\n\nassert binary_outcome_bounds(6, 31, 47) == (6 / 47, 22 / 47)',
    'The bound is O(1) time and space. Stratified follow-up requires storing selection and response events for each selected unit; inference cost depends on that design, not on this arithmetic.',
    ['Do not replace a missing binary outcome with zero without stating an assumption.', 'Do not call response weighting a guaranteed correction.', 'Do not present selected-sample bounds as population confidence intervals.'],
    ['data-science/sampling-frame-and-coverage-error','data-science/stratified-sampling-and-design-weights','data-science/precision-budget-and-effective-sample-size','data-science/missing-data-policy'])

add('precision-budget-and-effective-sample-size',
    'Precision budgets and effective sample size for weighted analyses',
    'A sample-size plan must account for the unit drawn, expected response, unequal weights and the smallest comparison the decision needs.', [
    ('Plan backward from the decision', 'A team may need a defect-rate estimate for all support cases and a separate estimate for partner cases. The partner comparison often sets the review budget because it has fewer eligible units. Define an acceptable interval width and consequence of a wrong decision before choosing a count. A single rule such as “review 100 cases” ignores prevalence, clustering, response loss and the number of slices reported.'),
    ('Inspect weight concentration', 'The common weight-only diagnostic (sum of weights)² / sum of squared weights measures how concentrated weights are. Four responses weighted 2, 2, 2 and 8 have a diagnostic of 196/76, about 2.58 rather than four equally weighted observations. That number is not a full design-based effective sample size when cases were drawn in clusters or have correlated outcomes. [[data-science/stratified-sampling-and-design-weights|The sampling design]] remains primary.'),
    ('Budget for response and review', 'If 47 completed reviews are needed and only about four in five selected cases are expected to yield an outcome, drawing exactly 47 is unlikely to suffice. Plan follow-up slots and record why outcomes fail. Use pilot response rates by stratum, then revise the allocation if a source proves harder to retrieve. Preserve a final audit sample separate from any active-learning queue used to improve a model.'),
    ('Report uncertainty honestly', 'Compute intervals using the actual sampling units and weight scheme; a naive binomial interval can understate uncertainty after cluster selection or heavy weighting. Examine whether the interval crosses the operational threshold. [[applied-statistics/cluster-bootstrap-and-standard-error|Cluster resampling]] is one route when the design supports it, while sparse strata may need a wider interval or an explicit insufficient-data label.')],
    'def weight_concentration_ess(weights):\n    if not weights or any(weight <= 0 for weight in weights):\n        raise ValueError("positive weights required")\n    total = sum(weights)\n    return total * total / sum(weight * weight for weight in weights)\n\nassert round(weight_concentration_ess([2, 2, 2, 8]), 2) == 2.58',
    'The diagnostic scans N weights in O(N) time and O(1) auxiliary space. Design-aware interval estimation may require cluster-level resampling, adding repeated O(N) passes and storage for group IDs.',
    ['Do not treat a weight-only diagnostic as a complete variance calculation.', 'Do not plan from completed reviews without response loss.', 'Do not let an overall precision target hide a weak decision-critical stratum.'],
    ['data-science/stratified-sampling-and-design-weights','data-science/nonresponse-bias-and-follow-up','data-science/support-case-audit-sampling-project','applied-statistics/cluster-bootstrap-and-standard-error'])

add('support-case-audit-sampling-project',
    'Project: estimate support-case defects from an auditable sample',
    'Build a sampling packet that a reviewer can use to reconstruct eligibility, selection, response and a weighted estimate.', [
    ('Freeze the frame', 'Collect one row per eligible support case for a fixed quarter. Include intake ID, channel, submission timestamp, eligibility rule and a snapshot identifier. Compare the intake event log with the agent export and list uncovered self-service or failed-assignment cases. Deduplicate case IDs before sampling. [[data-science/sampling-frame-and-coverage-error|The frame audit]] is a release gate, not an appendix to a rate.'),
    ('Draw and record', 'Split the frame into main and partner channels. Choose random cases within each stratum and save the seed, chosen IDs, population counts and inclusion probabilities. Oversample the partner channel if it is small, but do not pool outcomes without design weights. Assign each selected case to a blind reviewer and preserve a distinct missing-outcome state for inaccessible evidence.'),
    ('Analyze response and precision', 'Report response by channel, weighted defect rates, selected-sample bounds for unresolved labels and a design-aware uncertainty estimate. Compare the decision with and without a random follow-up of nonrespondents. Recompute the result from a frozen input manifest. [[data-science/nonresponse-bias-and-follow-up|Response assumptions]] and [[data-science/precision-budget-and-effective-sample-size|precision limits]] must appear beside the final number.'),
    ('Submit failure evidence', 'Add a duplicate intake event, a case omitted from the export and one reviewed case with an attachment that cannot be opened. The pipeline should detect each without silently classifying it as non-defective. Deliver the frame diff, sample manifest, reviewer ledger, weighted calculation, interval procedure and a short decision memo that states exactly which population the estimate describes.')],
    'def weighted_defect_fraction(review_rows):\n    reviewed = [row for row in review_rows if row["defective"] is not None]\n    total_weight = sum(row["design_weight"] for row in reviewed)\n    if total_weight <= 0:\n        raise ValueError("no observed weighted outcomes")\n    return sum(row["design_weight"] * int(row["defective"])\n               for row in reviewed) / total_weight',
    'The reviewed-row estimate is O(N) time and O(N) space as written; streaming accumulators reduce space to O(1). It describes reviewed units under the supplied weights, while nonresponse and coverage require separate adjustments or limits.',
    ['Do not suppress uncovered frame units in the final report.', 'Do not count missing reviews as clean cases.', 'Do not present a weighted respondent rate as assumption-free population truth.'],
    ['data-science/sampling-frame-and-coverage-error','data-science/stratified-sampling-and-design-weights','data-science/nonresponse-bias-and-follow-up','data-annotation/annotator-assignment-and-blinding'])

add('column-profile-and-domain-constraints',
    'Column profiles and domain constraints before analysis',
    'A column profile measures observed shape and violations; it does not decide what a value means without a domain contract.', [
    ('Profile the right snapshot', 'For delivery records, count rows, unique shipment IDs, missing arrival times, negative durations and records outside the analysis window. Profile by source and ingestion day so one broken feed is not hidden by a clean majority. Save the source snapshot and code revision. [[data-science/reproducible-analysis-snapshot|A reproducible snapshot]] lets a reviewer regenerate the same counts after the live tables change.'),
    ('State validity rules', 'A nonnegative duration is a range constraint, while “arrived after dispatch” compares two fields. A unique shipment ID is an identity rule, not a distribution statistic. Treat a missing arrival time as unknown or censored according to the business event, never as zero minutes. [[data-science/missing-data-policy|Missingness policy]] should be set before summary calculations.'),
    ('Separate observation from intervention', 'The profile may flag a 930-minute delivery, but it cannot by itself prove a data error. The shipment could have been held overnight. Send impossible records to quarantine, plausible extremes to investigation and routine records to analysis. Record each disposition and the rule version. [[data-science/outlier-investigation-and-quarantine|Outlier triage]] needs evidence beyond a percentile.'),
    ('Check the denominator', 'If 1,500 shipments were dispatched and 47 have no arrival time, a mean duration over 1,453 completed shipments describes completed shipments only. Report that coverage beside the mean. If the dashboard silently drops the 47, a process delay can appear as an improvement. Keep counts for eligible, observed, missing, invalid and excluded records in every output packet.')],
    'def profile_shipments(shipments):\n    shipment_ids = set()\n    report = {"rows": 0, "duplicate_ids": 0, "missing_arrival": 0, "invalid_order": 0}\n    for shipment in shipments:\n        report["rows"] += 1\n        shipment_id = shipment["shipment_id"]\n        report["duplicate_ids"] += shipment_id in shipment_ids\n        shipment_ids.add(shipment_id)\n        arrival = shipment["arrival_minute"]\n        report["missing_arrival"] += arrival is None\n        report["invalid_order"] += arrival is not None and arrival < shipment["dispatch_minute"]\n    return report',
    'A single pass over N rows takes O(N) expected time and O(U) space for U unique IDs. Exact distinct counting can be memory-heavy; partitioned or approximate counts are alternatives only when the contract permits them.',
    ['Do not replace a missing event time with zero.', 'Do not call every extreme value invalid.', 'Do not show a cleaned statistic without eligible and excluded counts.'],
    ['data-science/outlier-investigation-and-quarantine','data-science/robust-summaries-and-mad','data-science/reproducible-analysis-snapshot','data-engineering/quality-quarantine-and-reconciliation'])

add('outlier-investigation-and-quarantine',
    'Outlier investigation: impossible values, rare events and quarantines',
    'An outlier is unusual relative to a comparison group; it may be a measurement error, a valid rare case or a process change.', [
    ('Compare like with like', 'A delivery time of 930 minutes is extreme for same-day urban orders and ordinary for a remote route with overnight handoff. Define the route, service promise and clock boundary before choosing a threshold. Use distribution displays and resistant summaries to locate candidates. [[data-visualization/distribution-and-outlier-displays|A distribution view]] exposes heavy tails and subgroup mixtures better than one global cutoff.'),
    ('Distinguish invalidity from rarity', 'An arrival time earlier than dispatch violates chronology and should be quarantined pending correction. A late but chronologically valid delivery may be operationally important, especially when a customer asks why it occurred. Do not delete it merely because it shifts the mean. Record status as valid, invalid, unresolved or excluded-by-policy, with evidence and rule version for each decision.'),
    ('Measure policy effects', 'Compute a summary with all valid records and a second summary under any declared exclusion rule. Report how many records moved, which routes they belong to and how the decision changes. If a threshold is tuned after seeing the target metric, the cleaned estimate is selected to look favorable. [[data-science/robust-summaries-and-mad|Resistant statistics]] can describe the middle without erasing tail events.'),
    ('Test a disputed case', 'Create 47 shipments: 45 ordinary arrivals, one valid overnight delay and one negative duration from an event-order bug. Quarantine only the negative duration. Keep the overnight delay in the valid set and in a tail-case investigation queue. If the KPI excludes it under a service rule, publish both the rule and the count of excluded valid records.')],
    'def triage_delivery(record, review_threshold_minutes=480):\n    arrival = record["arrival_minute"]\n    dispatch = record["dispatch_minute"]\n    if arrival is None:\n        return "unresolved"\n    duration = arrival - dispatch\n    if duration < 0:\n        return "invalid"\n    if duration > review_threshold_minutes:\n        return "investigate"\n    return "valid"',
    'The rule is O(1) per record and O(N) for N records. Investigations have human cost that grows with the flagged queue; threshold choice should account for that capacity and the harm of missed cases.',
    ['Do not equate a high anomaly score with an invalid record.', 'Do not tune an exclusion threshold to improve a published KPI.', 'Do not lose a valid rare case from incident analysis.'],
    ['data-science/column-profile-and-domain-constraints','data-science/robust-summaries-and-mad','data-science/subgroup-distribution-and-aggregation-reversal','data-visualization/distribution-and-outlier-displays'])

add('robust-summaries-and-mad',
    'Resistant summaries: median, trimmed mean and median absolute deviation',
    'A resistant summary describes central behavior when a few valid extremes can dominate the ordinary mean or standard deviation.', [
    ('Choose a statistic for the question', 'The mean estimates an arithmetic average over all valid deliveries and is sensitive to long delays. The median describes a typical observed delivery, while a trimmed mean removes equal fractions from both tails after sorting. Neither makes late deliveries irrelevant. Publish the tail rate separately when the decision concerns service failures. [[data-science/outlier-investigation-and-quarantine|Triage]] decides validity before a summary is calculated.'),
    ('Use MAD carefully', 'Median absolute deviation is the median of absolute distances from the median. For delays of 21, 22, 23, 24 and 139 minutes, the mean is 45.8, the median is 23 and the raw MAD is 1. MAD can be zero when many values tie, so dividing by it to assign anomaly scores needs a stated fallback. A scale factor may be used under distribution assumptions; do not silently treat raw MAD as a standard deviation.'),
    ('Keep units and strata', 'Report minutes, not a unitless number, and calculate summaries within comparable route types before pooling. A median can stay flat even while the slowest 5% deteriorates; add tail quantiles or threshold exceedance counts. [[data-science/subgroup-distribution-and-aggregation-reversal|Subgroup analysis]] matters when channel mix changes between periods. The same route may improve even if the aggregate median moves in the other direction.'),
    ('Recompute a fixture', 'Start with the five delays above. Mark the 139-minute value as a valid overnight case and leave it in the mean and tail count. Then add a negative duration from a bad timestamp and quarantine that record. Recompute the valid mean, median and MAD; the first extreme affects the mean, while the invalid record should never enter any of the three.')],
    'from statistics import mean, median\n\ndef delivery_summaries(delays_minutes):\n    if not delays_minutes or any(delay < 0 for delay in delays_minutes):\n        raise ValueError("valid nonnegative delays required")\n    center = median(delays_minutes)\n    return {"mean": mean(delays_minutes), "median": center,\n            "raw_mad": median(abs(delay - center) for delay in delays_minutes)}\n\nassert delivery_summaries([21, 22, 23, 24, 139]) == {"mean": 45.8, "median": 23, "raw_mad": 1}',
    'Sorting for medians costs O(N log N) time and O(N) memory in the standard-library implementation. The mean is O(N); reporting route-specific medians adds grouping storage and repeated sorts.',
    ['Do not delete valid tail cases just to make a summary stable.', 'Do not divide by MAD when it is zero.', 'Do not mistake a typical-case median for a tail-service measure.'],
    ['data-science/outlier-investigation-and-quarantine','data-science/subgroup-distribution-and-aggregation-reversal','data-science/fulfillment-delay-analysis-project','data-visualization/distribution-and-outlier-displays'])

add('subgroup-distribution-and-aggregation-reversal',
    'Subgroup distributions and aggregation reversal',
    'An aggregate rate can move opposite to every subgroup rate when the mixture of groups changes.', [
    ('Hold the question steady', 'Suppose an established route and a new route have different baseline success rates. In an earlier period, the established route succeeds on 90 of 100 deliveries and the new route on 1 of 10. In a later period, they succeed on 19 of 20 and 40 of 200. Each route improves—from 90% to 95%, and from 10% to 20%—yet the pooled rate falls from 91/110, about 82.7%, to 59/220, about 26.8% because volume shifts toward the harder route.'),
    ('Report composition beside outcomes', 'Show subgroup numerator, denominator and rate for both periods, plus each group’s share of total volume. The pooled number is still a real operational measure; it answers a different question from within-route performance. To compare like-for-like performance, standardize both periods to a declared reference mix, then report the actual mix separately. [[data-science/metric-denominator-and-cohort|Denominator discipline]] prevents a change in population from being mistaken for a process regression.'),
    ('Avoid post-hoc slices', 'Choose route groups because they explain service conditions or allocation policy, not because one partition produces a preferred headline. Small cells carry large uncertainty; suppress or combine them under a documented rule. If group membership changes during the period, define whether a shipment belongs to its dispatch route, delivery route or current route. [[data-visualization/aggregation-grain-and-denominator|Aggregation grain]] must match that choice.'),
    ('Test the reversal', 'Calculate the two within-route rates and the two pooled rates from the counts above. Then use the earlier route mix for both periods and compare standardized rates. A dashboard that displays only the pooled decline would miss the within-route improvements; a dashboard that displays only standardized gains would hide the operational burden of shifting volume.')],
    'def rate(successes, attempts):\n    if attempts <= 0 or not 0 <= successes <= attempts:\n        raise ValueError("invalid counts")\n    return successes / attempts\n\nold_route_rates = (rate(90, 100), rate(1, 10))\nnew_route_rates = (rate(19, 20), rate(40, 200))\nassert all(new > old for old, new in zip(old_route_rates, new_route_rates))\nassert rate(59, 220) < rate(91, 110)',
    'Computing G subgroup counts from N records costs O(N) time and O(G) space. Standardization is O(G) once counts exist; uncertainty must still reflect the sampling or dependence structure.',
    ['Do not compare pooled rates without their group composition.', 'Do not choose subgroup boundaries after viewing the desired result.', 'Do not hide the actual operational volume mix when reporting standardized rates.'],
    ['data-science/metric-denominator-and-cohort','data-science/robust-summaries-and-mad','data-science/fulfillment-delay-analysis-project','data-visualization/aggregation-grain-and-denominator'])

add('fulfillment-delay-analysis-project',
    'Project: audit fulfillment delays without hiding the tail',
    'Build a reproducible delivery-delay analysis that separates invalid timestamps, valid rare cases and route-mix effects.', [
    ('Define the event contract', 'Create one row per shipment with stable ID, dispatch time, arrival time, route, service promise and source revision. Include 47 fixture shipments with one duplicate event, one missing arrival, one negative duration and one valid overnight delay. State whether open shipments are excluded, censored or reported separately. [[data-science/column-profile-and-domain-constraints|The profile]] must count each state before filtering.'),
    ('Triage before summarizing', 'Quarantine impossible chronology and duplicate identity conflicts with reasons. Investigate the overnight delay but keep it as valid unless evidence shows a recording error. Compute mean, median, raw MAD and a threshold-exceedance rate on the valid completed set, with numerator and denominator. Compare the summary with and without a declared valid-tail exclusion only as a sensitivity result.'),
    ('Check route mix', 'Split the analysis by established and new routes. Report counts and rates in each period, then use one fixed reference mix to compare performance. Reproduce an aggregation reversal with a controlled fixture and ensure the dashboard shows both the pooled operational result and the standardized within-route view. [[data-science/subgroup-distribution-and-aggregation-reversal|The reversal lesson]] provides a test case.'),
    ('Deliver a review packet', 'Save raw fixture, data cutoff, code revision, validation report, quarantine ledger, summary output and a short decision memo. Include exact counts for eligible, complete, missing, invalid and valid tail records. Rerun from the frozen snapshot and compare output checksums. A reader should be able to trace the 139-minute case from source event through every summary without it silently disappearing.')],
    'from statistics import median\n\ndef median_delay_by_route(shipments):\n    grouped = {}\n    for shipment in shipments:\n        arrival = shipment["arrival_minute"]\n        if arrival is None or arrival < shipment["dispatch_minute"]:\n            continue\n        grouped.setdefault(shipment["route"], []).append(arrival - shipment["dispatch_minute"])\n    return {route: median(delays) for route, delays in grouped.items()}',
    'Grouping N shipments costs O(N) time and space; sorting route samples for medians costs O(N log N) in the worst case. Production code must also preserve rejected-row counts and reasons, which this focused summary function leaves to the validation stage.',
    ['Do not silently drop invalid rows without a quarantine ledger.', 'Do not present only a median when tail failures matter.', 'Do not attribute a pooled rate change solely to process quality without checking route mix.'],
    ['data-science/column-profile-and-domain-constraints','data-science/outlier-investigation-and-quarantine','data-science/robust-summaries-and-mad','data-science/subgroup-distribution-and-aggregation-reversal'])

assert len(lessons) == len(new_paths) == 10
assert {item['path'] for item in lessons} == new_paths
titles = {path: row['title'] for path, row in by_path.items()}
titles.update({item['path']: item['title'] for item in lessons})

def prose(value):
    return re.sub(r'\[\[([^|]+)\|([^\]]+)\]\]',
                  lambda match: '<a href="/' + match[1] + '">' + match[2] + '</a>',
                  html.escape(value))

def links(paths):
    return '<ul>' + ''.join('<li><a href="/' + path + '">' + html.escape(titles[path]) + '</a></li>'
                            for path in paths) + '</ul>'

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
               difficulty='Intermediate', tags=['ai-data', 'data-science'], potd_date=None,
               featured=False, sort_order=11600 + index, status='published', published_at=stamp,
               created_at=stamp, updated_at=stamp,
               data={'subject_root':root_path,
                     'section_path':project_hub_path if is_project else root_path,
                     'content_format':'html', 'seo_ready':True,
                     'kind':'project' if is_project else 'tutorial',
                     'reading_minutes':max(5, len(re.sub(r'<[^>]+>', ' ', body).split()) // 180),
                     'author_path':'authors/aitrove-editorial',
                     'verification_suite':'Editorial and syntax review; project inputs needed for runtime checks',
                     'related':[{'path':target, 'title':titles[target]} for target in item['related']]})
    rows.append(row)
    by_path[path] = row

sampling_paths = ['data-science/' + slug for slug in new_slugs[:4]]
analysis_paths = ['data-science/' + slug for slug in new_slugs[5:9]]
project_paths = ['data-science/' + new_slugs[4], 'data-science/' + new_slugs[9]]
hub = by_path[root_path]
module_paths = {path for module in hub['data']['modules'] for path in module['lessons']}
if not set(sampling_paths).issubset(module_paths):
    hub['data']['modules'].insert(-1, {'title':'Sampling and representativeness',
                                      'summary':'Audit the frame, design and response process before claiming a population rate.',
                                      'lessons':sampling_paths})
if not set(analysis_paths).issubset(module_paths):
    hub['data']['modules'].insert(-1, {'title':'Profiling and resilient analysis',
                                      'summary':'Validate fields, investigate tails and distinguish composition from process change.',
                                      'lessons':analysis_paths})
apply_module = next(module for module in hub['data']['modules'] if module['title'] == 'Apply your knowledge')
for path in project_paths:
    if path not in apply_module['lessons']:
        apply_module['lessons'].append(path)
if '<h2>Sampling and representativeness</h2>' not in hub['body']:
    hub['body'] += ('<h2>Sampling and representativeness</h2>' + links(sampling_paths)
                    + '<h2>Profiling and resilient analysis</h2>' + links(analysis_paths)
                    + '<h2>Additional projects</h2>' + links(project_paths))
hub['updated_at'] = stamp

project_hub = by_path[project_hub_path]
for path in project_paths:
    if path not in project_hub['data']['modules'][0]['lessons']:
        project_hub['data']['modules'][0]['lessons'].append(path)
if '<h2>Additional project briefs</h2>' not in project_hub['body']:
    project_hub['body'] += '<h2>Additional project briefs</h2>' + links(project_paths)
project_hub['updated_at'] = stamp

for source, target in [
    ('data-science/getting-started', sampling_paths[0]),
    ('applied-statistics/population-estimand-and-sampling-frame', sampling_paths[0]),
    ('data-science/missing-data-policy', sampling_paths[2]),
    ('data-science/bootstrap-interval-interpretation', sampling_paths[3]),
    ('data-science/exploratory-analysis-without-peeking', analysis_paths[0]),
    ('data-engineering/quality-quarantine-and-reconciliation', analysis_paths[1]),
    ('data-visualization/distribution-and-outlier-displays', analysis_paths[2]),
    ('data-science/metric-denominator-and-cohort', analysis_paths[3]),
]:
    source_row = by_path[source]
    anchor = '<p><strong>Continue the workflow:</strong> <a href="/' + target + '">' + html.escape(titles[target]) + '</a>.</p>'
    if anchor not in source_row['body']:
        source_row['body'] += anchor
        if source_row['type'] == 'article':
            source_row['data'].setdefault('related', []).append({'path':target, 'title':titles[target]})
        source_row['updated_at'] = stamp

assert len({row['path'] for row in rows}) == len(rows)
fixture.write_text(json.dumps(rows, ensure_ascii=False, indent=2) + '\n')
print(json.dumps({'new_articles':len(lessons), 'new_projects':len(project_paths), 'crosslinks_from_existing':8}))
