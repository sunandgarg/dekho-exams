"""Add rank comparisons, survival inference and diagnostic agreement lessons."""
from de_batch_publisher import publish

A = 'applied-statistics/'
RANK = 'Rank comparisons and matched outcomes'
SURVIVAL = 'Time-to-event comparisons with censoring'
AGREEMENT = 'Diagnostic quality and reviewer agreement'
lessons = [
    {
        'path': A + 'independent-rank-comparison-and-pair-probability',
        'title': 'Independent rank comparisons: report the pair probability, not a median claim',
        'module': RANK, 'project': False,
        'summary': 'A rank comparison can measure how often an observation from one group is below one from another, including ties.',
        'sections': [
            ('Start with independent units', 'Two warehouse routing policies produce different dispatch-to-scan times. Compare one shipment from policy A with one independently sampled shipment from policy B. If many shipments share a route or driver, their rows are not independent units; group-aware assignment and uncertainty are needed. Freeze the eligible shipment frame and clock before calculating a rank statistic. [[applied-statistics/population-estimand-and-sampling-frame|The population definition]] decides which future shipments the result describes.'),
            ('Use a quantity people can read', 'Count each cross-group pair where A is faster than B, give a tie half credit, and divide by the number of pairs. A value above one half favors A on this probabilistic ordering. It is related to a Mann–Whitney statistic, but a distributional test does not automatically test equality of medians: groups can differ in spread or shape. Report medians and tail quantiles separately. [[applied-statistics/distribution-quantiles-and-outlier-policy|The distribution lesson]] prevents a single rank summary from hiding a long late-delivery tail.'),
            ('Choose a valid reference distribution', 'Under randomized policy assignment, a permutation of policy labels at the assigned unit can test a sharp no-effect null. With observational groups, label permutation needs an exchangeability assumption that may fail when route mix differs. Ties and small samples affect exact test calculations; the pair-probability code below is an effect summary, not a p-value. If the same driver tried both policies on matched shifts, use [[applied-statistics/paired-estimand-and-unit-matching|a paired analysis]] instead of an independent-rank test.'),
            ('State the operating consequence', 'A policy can win most random pairs while making the worst few shipments much slower. Review median, high quantile, missing scans and service-limit failures before a rollout. Keep the statistic, sample counts, assignment rule and uncertainty together in the decision packet. [[applied-statistics/paired-sign-check-and-zero-differences|The paired sign lesson]] covers a different design; [[applied-statistics/warehouse-routing-rank-project|the project]] catches a mixed design whose first analysis treats matched shifts as independent.'),
        ],
        'code': '''def faster_pair_probability(policy_a_minutes, policy_b_minutes):
    if not policy_a_minutes or not policy_b_minutes:
        raise ValueError("both routing groups need observations")
    favorable = sum(a_time < b_time for a_time in policy_a_minutes
                    for b_time in policy_b_minutes)
    ties = sum(a_time == b_time for a_time in policy_a_minutes
               for b_time in policy_b_minutes)
    comparisons = len(policy_a_minutes) * len(policy_b_minutes)
    return (favorable + 0.5 * ties) / comparisons

probability = faster_pair_probability([4, 6, 8], [5, 7, 9])
assert round(probability, 6) == round(2 / 3, 6)
''',
        'cost': 'The direct cross-pair calculation takes O(a × b) time and O(1) extra space for group sizes a and b. Sorting and rank aggregation can reduce cost on larger samples. Calculation speed is rarely the main risk: dependence, route imbalance and unobserved scan times can dominate inference.',
        'mistakes': ['Calling a rank-test result a test of median equality without equal-shape assumptions.', 'Treating shipments from the same route as independent units.', 'Using an independent test for matched driver shifts.', 'Reporting a favorable pair probability while hiding the late-delivery tail.'],
        'related': [A + 'paired-sign-check-and-zero-differences', A + 'warehouse-routing-rank-project', A + 'distribution-quantiles-and-outlier-policy', A + 'paired-estimand-and-unit-matching', A + 'randomization-unit-and-experiment-design'],
    },
    {
        'path': A + 'paired-sign-check-and-zero-differences',
        'title': 'Paired sign checks: treat zeros and direction as design decisions',
        'module': RANK, 'project': False,
        'summary': 'A sign check uses the direction of nonzero paired changes and makes its handling of exact ties explicit.',
        'sections': [
            ('Keep the match intact', 'The same support agent handles matched shifts under two ticket views. Define one candidate-minus-incumbent duration per complete agent-shift pair, with negative values favoring the candidate. A zero difference contributes no direction to a conventional sign test, so report how many zero pairs were removed and why they occurred. Rounded time stamps can create artificial ties. [[applied-statistics/paired-estimand-and-unit-matching|Pair construction]] precedes any test statistic.'),
            ('Distinguish sign from signed rank', 'A sign check discards change magnitude and tests whether positive and negative directions are balanced under its null assumptions. A signed-rank procedure orders absolute nonzero differences and uses more magnitude information, but its familiar location interpretation needs a suitable symmetry condition on paired differences. Neither procedure turns a before/after observation into a randomized intervention. Show the differences, not just one test result. [[applied-statistics/paired-randomization-check|Assignment-based sign flips]] depend on the actual randomization scheme.'),
            ('Calculate small-sample evidence exactly', 'For n nonzero pairs under a fair independent-sign null, the number of positive signs has a binomial distribution with probability one half. A two-sided tail can be enumerated with integer combinations. The code reports a two-sided p-value using the smaller directional count; it is deliberately separate from an effect estimate. With very few pairs, attainable p-values are coarse. If repeated shifts share an agent, independent signs can fail even when the pairs themselves are complete. [[applied-statistics/cluster-bootstrap-and-standard-error|Dependence review]] remains necessary.'),
            ('Make the release question practical', 'Report counts of improvements, deteriorations and ties, plus a meaningful time difference and high-percentile delay. Predeclare whether a zero should count as a neutral outcome or a service success for the operational decision. A small p-value cannot replace a minimum useful effect, and an inconclusive p-value cannot prove equivalence. [[applied-statistics/hypothesis-test-and-effect-size|Effect-size language]] keeps those claims apart. [[applied-statistics/warehouse-routing-rank-project|The routing project]] shows how a changed pair key can reverse the analysis.'),
        ],
        'code': '''from math import comb

def paired_sign_summary(changes):
    positive = sum(change > 0 for change in changes)
    negative = sum(change < 0 for change in changes)
    ties = len(changes) - positive - negative
    nonzero = positive + negative
    if nonzero == 0:
        return {"positive": 0, "negative": 0, "ties": ties, "p_two_sided": None}
    smaller = min(positive, negative)
    tail = sum(comb(nonzero, count) for count in range(smaller + 1))
    return {"positive": positive, "negative": negative, "ties": ties,
            "p_two_sided": min(1.0, 2 * tail / (2 ** nonzero))}

report = paired_sign_summary([-4, -2, 0, 1, -3])
assert report == {"positive": 1, "negative": 3, "ties": 1,
                  "p_two_sided": 0.625}
''',
        'cost': 'Counting directions is O(n) time and O(1) extra space for n paired changes; computing the displayed binomial tail adds O(n) arithmetic. Exact arithmetic is cheap for normal study sizes. Verifying keys, timing precision and independence consumes more effort than the test itself.',
        'mistakes': ['Dropping zero pairs without reporting their count or measurement precision.', 'Using signed-rank location language when difference symmetry is unsupported.', 'Treating repeated shifts from one agent as independent sign trials.', 'Calling a nonsignificant result evidence that the two workflows are equivalent.'],
        'related': [A + 'independent-rank-comparison-and-pair-probability', A + 'warehouse-routing-rank-project', A + 'paired-estimand-and-unit-matching', A + 'paired-randomization-check', A + 'hypothesis-test-and-effect-size'],
    },
    {
        'path': A + 'warehouse-routing-rank-project',
        'title': 'Project: review routing-time differences without losing the unit',
        'module': RANK, 'project': True,
        'summary': 'Audit independent shipments and matched driver shifts before choosing a rank or paired comparison.',
        'sections': [
            ('Separate two study designs', 'A warehouse pilot contains independent shipment samples from two routing policies and a smaller set of drivers who tried both policies on matched shifts. These are not interchangeable rows. Define the dispatch-to-scan clock, eligible routes, driver and shift keys, assignment rules and missing scans for each design. [[applied-statistics/independent-rank-comparison-and-pair-probability|The cross-group pair statistic]] applies to the independent cohort; [[applied-statistics/paired-estimand-and-unit-matching|within-driver changes]] apply to matched shifts.'),
            ('Find the false sample expansion', 'The first export joins on driver ID alone. Drivers with several shifts appear repeatedly, creating a many-to-many table and a deceptively precise comparison. Rebuild one record per declared unit, quarantine duplicate shifts and report incomplete pairs. For independent shipments, keep driver clusters visible rather than pretending every parcel is unrelated. A single combined rank-test p-value from the malformed export has no defensible interpretation. [[applied-statistics/cluster-bootstrap-and-standard-error|Cluster-aware uncertainty]] may be needed after the join is repaired.'),
            ('Compare effects and tails', 'For independent shipments, report the probability that a random policy-A shipment scans faster than a random policy-B shipment, including ties. For matched shifts, report positive, negative and zero change counts, plus a mean or median time difference. Inspect late-scan quantiles in both designs. The candidate may win many pairs yet make a small set of long routes unacceptable. [[applied-statistics/distribution-quantiles-and-outlier-policy|Tail reporting]] is a release requirement rather than an optional plot.'),
            ('Deliver a limited conclusion', 'Freeze the corrected extraction, unit inventory, effect summaries and uncertainty method. If matched order was randomized, retain the assignment record for a design-based check; if it was not, describe the contrast as observational. Hold a rollout if missing scans or late-route failures exceed the agreed limit. [[applied-statistics/paired-sign-check-and-zero-differences|The sign lesson]] requires an explicit zero policy; [[applied-statistics/randomization-unit-and-experiment-design|the design lesson]] controls causal language.'),
        ],
        'code': '''def routing_review_gate(report, limits):
    if report["duplicate_unit_keys"]:
        return "hold:unit-join"
    if report["unmatched_shift_share"] > limits["maximum_unmatched_share"]:
        return "hold:pair-coverage"
    if report["late_scan_rate"] > limits["maximum_late_rate"]:
        return "hold:tail-service"
    if report["assignment_record_missing"]:
        return "publish:observational-contrast"
    return "review:design-based-contrast"

limits = {"maximum_unmatched_share": 0.07, "maximum_late_rate": 0.04}
report = {"duplicate_unit_keys": 3, "unmatched_shift_share": 0.03,
          "late_scan_rate": 0.02, "assignment_record_missing": False}
assert routing_review_gate(report, limits) == "hold:unit-join"
assert routing_review_gate({**report, "duplicate_unit_keys": 0}, limits) \
       == "review:design-based-contrast"
''',
        'cost': 'The gate is O(1) time and space after the data audit. Rebuilding a unique-unit extraction is O(n) expected time with a keyed index, while credible uncertainty needs route or driver grouping. A fast rank calculation on a many-to-many join is cheaper only because it skips the actual study design.',
        'mistakes': ['Joining matched shifts by driver alone.', 'Pooling independent shipments with repeated driver shifts.', 'Interpreting a rank statistic as a median difference.', 'Ignoring a worse late-scan tail because most cross-group pairs favor the candidate.'],
        'related': [A + 'independent-rank-comparison-and-pair-probability', A + 'paired-sign-check-and-zero-differences', A + 'paired-estimand-and-unit-matching', A + 'cluster-bootstrap-and-standard-error', A + 'distribution-quantiles-and-outlier-policy'],
    },
    {
        'path': A + 'survival-risk-set-and-event-order',
        'title': 'Survival risk sets: keep censored cases until they leave observation',
        'module': SURVIVAL, 'project': False,
        'summary': 'A product-limit survival curve updates at events using the number still at risk immediately before each event time.',
        'sections': [
            ('Define the clock and event', 'A specialist queue measures time from ticket assignment to first completed resolution. Some tickets remain open when the reporting window ends; those observations are right-censored rather than resolved at the censoring time. Specify start time, resolution rule, administrative end, timezone and whether reopened tickets count as a new episode. [[data-science/right-censoring-and-time-to-event|The censoring contract]] prevents unresolved tickets from being discarded as inconvenient missing outcomes.'),
            ('Build each risk set', 'At a distinct event time, divide the number of resolutions by the number of tickets still observed and unresolved immediately beforehand, then multiply survival by one minus that fraction. Censored tickets leave the risk set after contributing observed follow-up. When an event and censoring share a recorded time, state the tie convention; the small program processes events before removals at that time. The curve estimates the probability of remaining unresolved beyond time t under its censoring assumptions. [[data-science/kaplan-meier-resolution-curve|The foundational curve lesson]] describes the same estimator at a broader level.'),
            ('Expose tail support', 'A late curve step can be based on only two tickets. Report the number at risk at decision horizons and avoid extrapolating after follow-up ends. Censoring must be reasonably independent of the event time conditional on the design; tickets transferred to another team because they are difficult violate a casual administrative-censoring story. Compare transfer reasons and censoring frequency by queue. [[data-science/survival-curve-uncertainty-and-tail-support|Tail uncertainty]] needs this support table.'),
            ('Compare a decision horizon', 'For a service commitment such as 12 hours, report the unresolved probability at 12 hours with interval and at-risk count, if follow-up supports that horizon. If curves cross, one global test can obscure early and late differences; [[applied-statistics/restricted-mean-resolution-time|restricted mean time]] gives a horizon-based quantity. [[applied-statistics/support-queue-survival-project|The project]] catches an export that records transferred tickets as if they resolved immediately.'),
        ],
        'code': '''from collections import defaultdict

def unresolved_survival_curve(cases):
    if not cases or any(hours < 0 or event not in (0, 1)
                        for hours, event in cases):
        raise ValueError("valid observed durations required")
    by_time = defaultdict(lambda: [0, 0])
    for hours, event in cases:
        by_time[hours][0 if event else 1] += 1
    at_risk = len(cases)
    survival = 1.0
    steps = []
    for hours in sorted(by_time):
        events, censored = by_time[hours]
        if events:
            survival *= 1 - events / at_risk
            steps.append((hours, survival, at_risk))
        at_risk -= events + censored
    return steps

curve = unresolved_survival_curve([(4, 1), (6, 0), (8, 1), (8, 0)])
assert curve == [(4, 0.75, 4), (8, 0.375, 2)]
''',
        'cost': 'Grouping n cases by time is O(n) expected time and O(k) space for k distinct times; sorting times costs O(k log k). The bigger cost is correct episode and censoring records. A mathematically exact curve from misclassified transfers can systematically understate unresolved work.',
        'mistakes': ['Dropping open tickets instead of retaining their observed follow-up.', 'Counting censored tickets as resolved at their last contact.', 'Ignoring how event and censor ties are ordered.', 'Reporting a late survival estimate without the number still at risk.'],
        'related': [A + 'restricted-mean-resolution-time', A + 'support-queue-survival-project', 'data-science/right-censoring-and-time-to-event', 'data-science/kaplan-meier-resolution-curve', 'data-science/survival-curve-uncertainty-and-tail-support'],
    },
    {
        'path': A + 'restricted-mean-resolution-time',
        'title': 'Restricted mean time: compare curves at a supported horizon',
        'module': SURVIVAL, 'project': False,
        'summary': 'The area under an unresolved-survival curve up to a declared horizon summarizes time unresolved without assuming one constant hazard ratio.',
        'sections': [
            ('Choose the horizon first', 'Two ticket queues may resolve cases at different speeds early but reverse later. The restricted mean unresolved time up to 12 hours is the area under each queue’s unresolved-survival curve from zero to 12. It is measured in hours and can be compared directly: a lower value means less time unresolved within that horizon. Choose 12 hours from the service decision and observed follow-up, not because the curves happen to favor one team there. [[applied-statistics/survival-risk-set-and-event-order|Risk-set construction]] supplies the curve.'),
            ('Integrate the step function', 'A product-limit curve remains constant between event times. Sum each interval width times the survival value that applies during that interval, and stop exactly at the declared horizon. If the last observation ends before the horizon, do not carry a tail forward as if its support were known; report the horizon as unsupported or use an approved estimator with clearly stated assumptions. The code computes area from supplied event steps and assumes follow-up supports the requested endpoint. [[data-science/survival-curve-uncertainty-and-tail-support|At-risk counts]] should accompany the result.'),
            ('Interpret a difference carefully', 'A two-hour difference in restricted mean unresolved time is an average over the selected window, not a guarantee that every ticket saves two hours. When groups were not randomized, queue mix, priority and staffing can confound the contrast. Censoring patterns may differ by group. Compute uncertainty with a method that respects independent units such as account or branch, and examine support at the horizon. [[applied-statistics/cluster-bootstrap-and-standard-error|Cluster resampling]] must resample the correct unit.'),
            ('Keep both shapes visible', 'Report the two curves, at-risk tables, horizon, area estimates, difference and censoring reasons. A single area number can hide a period when one queue performs worse; those crossings matter to a service-level decision. A log-rank test has different emphasis and may have weak sensitivity to crossing alternatives. [[applied-statistics/support-queue-survival-project|The project]] holds a claim when the chosen horizon has too little observed support.'),
        ],
        'code': '''def restricted_unresolved_hours(event_steps, horizon_hours):
    if horizon_hours <= 0:
        raise ValueError("positive horizon required")
    area = 0.0
    previous_time = 0.0
    survival = 1.0
    for event_time, after_event_survival in event_steps:
        if event_time < previous_time or not 0 <= after_event_survival <= survival:
            raise ValueError("invalid survival steps")
        if event_time >= horizon_hours:
            break
        area += (event_time - previous_time) * survival
        previous_time = event_time
        survival = after_event_survival
    return area + (horizon_hours - previous_time) * survival

hours = restricted_unresolved_hours([(4, 0.75), (8, 0.375)], 10)
assert hours == 7.75
''',
        'cost': 'Integrating k sorted event steps is O(k) time and O(1) extra space. Constructing uncertainty and verifying follow-up at the horizon take more work. The function does not check whether censoring support reaches the horizon; that condition must be audited in the calling analysis.',
        'mistakes': ['Choosing a horizon after seeing which queue wins.', 'Extending a curve past available follow-up without declaring an assumption.', 'Treating a restricted-mean difference as an individual guaranteed saving.', 'Reporting one area estimate without curves, at-risk counts and censoring reasons.'],
        'related': [A + 'survival-risk-set-and-event-order', A + 'support-queue-survival-project', A + 'cluster-bootstrap-and-standard-error', 'data-science/survival-curve-uncertainty-and-tail-support', 'data-science/specialist-queue-survival-comparison-project'],
    },
    {
        'path': A + 'support-queue-survival-project',
        'title': 'Project: compare specialist queues with censored resolution times',
        'module': SURVIVAL, 'project': True,
        'summary': 'Repair event flags, choose a supported service horizon and compare unresolved time without hiding curve crossings.',
        'sections': [
            ('Lock the episode contract', 'A support organization compares two specialist queues on first completed ticket resolution after assignment. Define each ticket’s start, event, censoring time and group at assignment. A ticket still open at export is right-censored. Transfers to a different team need their own disposition because transfer may be related to difficulty; they cannot silently become resolutions. [[applied-statistics/survival-risk-set-and-event-order|Risk-set rules]] depend on this event ledger.'),
            ('Find the export error', 'The first feed marks transferred tickets as completed when a transfer message was sent. That creates an artificial early resolution advantage for the queue with more transfers. Reconcile transfer and close events using immutable ticket IDs, then rebuild curves and at-risk counts. One queue now resolves more quickly early, while the other catches up later. A single median hides the crossing pattern, and a global test is not a substitute for the service question. [[data-science/right-censoring-and-time-to-event|Censoring definitions]] keep unresolved follow-up in the dataset.'),
            ('Compare a fixed horizon', 'The service commitment is 12 hours. Check that both queues have enough observed follow-up and at-risk tickets at 12 hours, then calculate restricted mean unresolved time through that horizon. Report the difference with uncertainty based on independent assigned units. If a group has almost no support near 12 hours, hold the comparison rather than extrapolating. [[applied-statistics/restricted-mean-resolution-time|The area measure]] summarizes time within the fixed window, not every part of the curve.'),
            ('Publish limits and action', 'Deliver group sizes, event and censor counts, transfer audit, curves, at-risk table, horizon support, area difference and sensitivity to transfer handling. The queues were not randomized, so describe the contrast as observational and examine priority mix. A rollout decision should also check late unresolved tail and staffing cost. [[data-science/survival-curve-uncertainty-and-tail-support|Tail support]] and [[applied-statistics/population-estimand-and-sampling-frame|the target frame]] close the packet.'),
        ],
        'code': '''def queue_comparison_gate(report, limits):
    if report["transfers_mislabeled_as_resolved"]:
        return "hold:event-ledger"
    if min(report["at_risk_at_horizon"].values()) < limits["minimum_at_risk"]:
        return "hold:horizon-support"
    if report["censoring_difference"] > limits["maximum_censor_gap"]:
        return "review:censoring-pattern"
    if not report["assignment_randomized"]:
        return "publish:observational-contrast"
    return "review:randomized-contrast"

limits = {"minimum_at_risk": 17, "maximum_censor_gap": 0.12}
report = {"transfers_mislabeled_as_resolved": 4,
          "at_risk_at_horizon": {"queue-a": 24, "queue-b": 19},
          "censoring_difference": 0.06, "assignment_randomized": False}
assert queue_comparison_gate(report, limits) == "hold:event-ledger"
assert queue_comparison_gate({**report, "transfers_mislabeled_as_resolved": 0},
                             limits) == "publish:observational-contrast"
''',
        'cost': 'The gate is O(g) time for g groups and O(g) temporary space for group counts. Rebuilding reliable event histories and checking censoring mechanisms are the costly steps. A quick curve from the flawed transfer flag would answer a different question with false precision.',
        'mistakes': ['Treating transfer as completed resolution.', 'Discarding tickets still open at extraction.', 'Choosing the comparison horizon after inspecting crossing curves.', 'Describing nonrandom queue assignment as a causal treatment effect.'],
        'related': [A + 'survival-risk-set-and-event-order', A + 'restricted-mean-resolution-time', A + 'population-estimand-and-sampling-frame', 'data-science/right-censoring-and-time-to-event', 'data-science/survival-curve-uncertainty-and-tail-support'],
    },
    {
        'path': A + 'diagnostic-performance-and-prevalence',
        'title': 'Diagnostic performance: separate sensitivity, specificity and predictive value',
        'module': AGREEMENT, 'project': False,
        'summary': 'A flagger’s sensitivity and specificity describe conditional error rates; the meaning of a positive flag also depends on prevalence.',
        'sections': [
            ('Define truth and the target frame', 'A claims audit rule flags duplicate reimbursements for human review. True status comes from a completed independent audit, not from whether the rule raised a flag. Define eligible claims, adjudication window and unit of analysis. If only flagged claims receive verification, false negatives and prevalence are not observed for the full frame. [[mlops/selective-label-observation-and-audit-sampling|Audit sampling]] must include some unflagged cases before deployment-wide performance can be estimated.'),
            ('Keep conditional rates distinct', 'Sensitivity is the share of true duplicates flagged; specificity is the share of true nonduplicates left unflagged. Positive predictive value is the share of flagged claims that truly duplicate. Holding sensitivity and specificity fixed, positive predictive value falls when duplicates are rarer. The small calculation below shows that a flagger with seemingly strong conditional rates can still send mostly false alerts to reviewers at low prevalence. [[applied-statistics/rare-proportion-wilson-interval|Rare-event uncertainty]] matters for every count behind those percentages.'),
            ('Report the confusion counts', 'Publish true positives, false positives, false negatives and true negatives with denominators, sampling design and interval method. When audit sampling oversamples flagged claims, raw sample precision is not the live positive predictive value; reweight to the target frame under an approved design. Check groups and time windows, because changes in duplicate prevalence can alter reviewer yield without changing the conditional error rates. [[applied-statistics/stratified-survey-estimate-and-population-weights|Stratified estimation]] connects the sample to the operational population.'),
            ('Set an action threshold', 'A review team cares about missed duplicates and the capacity spent on false alarms. Predeclare acceptable miss and alert rates, then evaluate on mature independent audits. Do not claim a diagnostic rule is accurate from one headline accuracy number when most claims are legitimate. [[applied-statistics/reviewer-agreement-and-prevalence|Reviewer agreement]] checks the quality of the adjudication labels; [[applied-statistics/claims-audit-quality-project|the project]] separates label disagreement from model error.'),
        ],
        'code': '''def positive_flag_value(sensitivity, specificity, prevalence):
    if not all(0 <= value <= 1 for value in
               (sensitivity, specificity, prevalence)):
        raise ValueError("rates must lie between zero and one")
    true_positive_share = sensitivity * prevalence
    false_positive_share = (1 - specificity) * (1 - prevalence)
    flagged_share = true_positive_share + false_positive_share
    return None if flagged_share == 0 else true_positive_share / flagged_share

value = positive_flag_value(0.90, 0.95, 0.02)
assert round(value, 6) == round(0.018 / 0.067, 6)
assert value < 0.30
''',
        'cost': 'The probability conversion is O(1) time and space. Reliable estimation requires audited true labels across flagged and unflagged claims and can be expensive. A high reported sensitivity from selectively reviewed claims may be cheaper to obtain but cannot support deployment-wide performance claims.',
        'mistakes': ['Calling sensitivity the probability that a positive flag is correct.', 'Ignoring prevalence when forecasting reviewer workload.', 'Treating unreviewed claims as known true negatives.', 'Reporting only accuracy for a rare duplicate outcome.'],
        'related': [A + 'reviewer-agreement-and-prevalence', A + 'claims-audit-quality-project', A + 'rare-proportion-wilson-interval', A + 'stratified-survey-estimate-and-population-weights', 'mlops/selective-label-observation-and-audit-sampling'],
    },
    {
        'path': A + 'reviewer-agreement-and-prevalence',
        'title': 'Reviewer agreement: inspect confusion cells before one kappa number',
        'module': AGREEMENT, 'project': False,
        'summary': 'Agreement between two reviewers depends on observed matches, their label marginals and the prevalence of each label.',
        'sections': [
            ('Audit the labeling setup', 'Two claims reviewers independently classify the same sampled cases as duplicate or legitimate. Independence means neither sees the other’s answer before submitting; it does not mean their judgments are statistically independent. Define the label policy, ambiguous-case route, random audit sample and allowed evidence. An agreement rate from handpicked easy claims does not represent the queue. [[applied-statistics/diagnostic-performance-and-prevalence|Diagnostic estimates]] inherit any error in the reference labels.'),
            ('Read the complete two-by-two table', 'Record cases both call duplicate, both call legitimate, and the two disagreement directions. Observed agreement is the share on the matching diagonal. Cohen’s kappa subtracts an expected agreement derived from each reviewer’s label proportions and rescales the remainder. When true duplicates are rare, both reviewers can agree on many legitimate cases yet kappa can be modest. The code demonstrates this pattern; it does not identify which reviewer is right. [[applied-statistics/rare-proportion-wilson-interval|Rare-label counts]] should accompany the statistic.'),
            ('Interpret disagreement as work', 'Inspect the actual disagreement cases, especially missed suspected duplicates and policy edge cases. A prevalence shift or different review threshold changes the label marginals and therefore kappa, even when observed agreement remains high. Neither kappa nor percent agreement proves validity against an independent truth. Use a third adjudicator or evidence-based resolution process for disputed cases and preserve the original pair of judgments. [[data-annotation/data-annotation-tutorial|Annotation workflows]] can connect policy revision to a stable label ledger.'),
            ('Guard downstream evaluation', 'If only flagged claims are double-reviewed, the agreement sample is selected and cannot describe all claims without an audit design. Report sample construction, each confusion cell, observed agreement, kappa, positive-label prevalence and adjudication outcome. [[applied-statistics/claims-audit-quality-project|The project]] holds a model-quality claim until unflagged cases and reviewer disagreements are examined; [[applied-statistics/population-estimand-and-sampling-frame|the frame]] states which labels the result covers.'),
        ],
        'code': '''def binary_reviewer_agreement(both_duplicate, both_legitimate,
                              first_only, second_only):
    cells = (both_duplicate, both_legitimate, first_only, second_only)
    if any(cell < 0 or int(cell) != cell for cell in cells) or sum(cells) == 0:
        raise ValueError("nonnegative agreement counts required")
    total = sum(cells)
    observed = (both_duplicate + both_legitimate) / total
    first_positive = (both_duplicate + first_only) / total
    second_positive = (both_duplicate + second_only) / total
    expected = (first_positive * second_positive +
                (1 - first_positive) * (1 - second_positive))
    kappa = None if expected == 1 else (observed - expected) / (1 - expected)
    return {"observed_agreement": observed, "kappa": kappa}

report = binary_reviewer_agreement(2, 88, 5, 5)
assert report["observed_agreement"] == 0.90
assert 0 < report["kappa"] < 0.30
''',
        'cost': 'The four-cell calculation is O(1) time and space. Double review and adjudication cost far more than the statistic, but those cases reveal policy ambiguity that a single agreement number hides. A selected easy-case sample can make both cheap agreement and kappa irrelevant to the production queue.',
        'mistakes': ['Calling a high agreement rate proof that labels are correct.', 'Treating a modest kappa under rare positives as a diagnosis by itself.', 'Dropping disagreement cases after adjudication instead of preserving both original labels.', 'Generalizing flagged-only double review to all claims.'],
        'related': [A + 'diagnostic-performance-and-prevalence', A + 'claims-audit-quality-project', A + 'rare-proportion-wilson-interval', A + 'population-estimand-and-sampling-frame', 'data-annotation/data-annotation-tutorial'],
    },
    {
        'path': A + 'claims-audit-quality-project',
        'title': 'Project: separate claims-flagger errors from reviewer disagreement',
        'module': AGREEMENT, 'project': True,
        'summary': 'Build an audit frame that observes unflagged cases, adjudicates reviewer disagreement and estimates reviewer workload at live prevalence.',
        'sections': [
            ('Construct an observable truth frame', 'A duplicate-claim flagger is evaluated on cases auditors already reviewed. That selected set contains many flagged claims and almost no unflagged cases, so it cannot estimate false negatives in the full submission stream. Predeclare a random audit sample from both flag statuses, retain selection probabilities and mature outcomes, and isolate reviewers from the model score where feasible. [[applied-statistics/diagnostic-performance-and-prevalence|Diagnostic quantities]] require all four confusion cells.'),
            ('Audit the labels themselves', 'Two reviewers independently classify the sampled claims. Their overall agreement is high because most cases are legitimate, but the positive-label cells have more disputes. Preserve both original labels and send disagreement cases through documented adjudication. A kappa value alone does not say which reviewer is correct. [[applied-statistics/reviewer-agreement-and-prevalence|The agreement lesson]] ties each statistic to the full cross-tabulation and prevalence.'),
            ('Estimate operational yield', 'Use audited confusion counts with the sampling design to estimate sensitivity, specificity and live positive predictive value. At rare duplicate prevalence, even a high-sensitivity flagger can produce many false alerts. Show alert volume and missed-duplicate counts under the proposed threshold; report uncertainty on sparse positive cells. Do not use the oversampled audit fraction as the live prevalence. [[applied-statistics/stratified-survey-estimate-and-population-weights|Weighting logic]] links sampled cases to the eligible claim frame.'),
            ('Publish a gated packet', 'Require adequate unflagged audit coverage, a resolved label policy, mature outcomes and enough positive cases before a broad performance claim. Record the reviewer disagreement matrix, adjudication rule, confusion counts, selection probabilities, estimated workload and error-cost owner. If any component fails, describe the audit as incomplete. [[mlops/selective-label-observation-and-audit-sampling|Observation bias]] and [[applied-statistics/rare-proportion-wilson-interval|rare-event intervals]] define the next collection step.'),
        ],
        'code': '''def claims_audit_gate(report, limits):
    if report["unflagged_audited"] < limits["minimum_unflagged"]:
        return "hold:unflagged-coverage"
    if report["unresolved_disagreements"]:
        return "hold:label-adjudication"
    if report["mature_positive_cases"] < limits["minimum_positives"]:
        return "hold:rare-positive-support"
    if not report["selection_probabilities_recorded"]:
        return "hold:sample-design"
    return "publish:scoped-diagnostic-review"

limits = {"minimum_unflagged": 52, "minimum_positives": 17}
report = {"unflagged_audited": 34, "unresolved_disagreements": 0,
          "mature_positive_cases": 21,
          "selection_probabilities_recorded": True}
assert claims_audit_gate(report, limits) == "hold:unflagged-coverage"
assert claims_audit_gate({**report, "unflagged_audited": 63},
                         limits) == "publish:scoped-diagnostic-review"
''',
        'cost': 'The gate is O(1) time and space once counts are available. Randomly auditing unflagged cases and resolving reviewer disagreements consume staff time but are needed to estimate false negatives and live alert yield. Reusing only previously reviewed claims would be cheaper and would leave the main error rate unidentified.',
        'mistakes': ['Treating unreviewed claims as true negatives.', 'Using an oversampled audit prevalence as the live base rate.', 'Discarding reviewer disagreements from the confusion matrix.', 'Publishing one accuracy figure without denominators and workload estimates.'],
        'related': [A + 'diagnostic-performance-and-prevalence', A + 'reviewer-agreement-and-prevalence', A + 'rare-proportion-wilson-interval', A + 'stratified-survey-estimate-and-population-weights', 'mlops/selective-label-observation-and-audit-sampling'],
    },
]

crosslinks = [
    (A + 'distribution-quantiles-and-outlier-policy', A + 'independent-rank-comparison-and-pair-probability'),
    (A + 'paired-estimand-and-unit-matching', A + 'paired-sign-check-and-zero-differences'),
    (A + 'support-shift-paired-review-project', A + 'warehouse-routing-rank-project'),
    ('data-science/right-censoring-and-time-to-event', A + 'survival-risk-set-and-event-order'),
    ('data-science/survival-curve-uncertainty-and-tail-support', A + 'restricted-mean-resolution-time'),
    ('data-science/specialist-queue-survival-comparison-project', A + 'support-queue-survival-project'),
    (A + 'rare-proportion-wilson-interval', A + 'diagnostic-performance-and-prevalence'),
    ('data-annotation/data-annotation-tutorial', A + 'reviewer-agreement-and-prevalence'),
    (A + 'claim-count-glm-project', A + 'claims-audit-quality-project'),
]

if __name__ == '__main__':
    publish(lessons, [RANK, SURVIVAL, AGREEMENT], crosslinks,
            'aitrove-applied-statistics-ranks-survival-agreement-import-20261006.json',
            8430, subject='applied-statistics', hub_path=A + 'applied-statistics-tutorial')
