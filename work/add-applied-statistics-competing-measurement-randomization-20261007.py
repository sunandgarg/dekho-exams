"""Add Applied Statistics lessons on competing events, label error, and blocked trials."""
from de_batch_publisher import publish

A = 'applied-statistics/'
COMPETE = 'Competing events and cumulative incidence'
LABEL = 'Outcome verification and misclassification'
BLOCK = 'Blocked assignment and interference'


def lesson(slug, title, module, summary, sections, code, cost, mistakes, related, project=False):
    return dict(path=A + slug, title=title, module=module, project=project,
                summary=summary, sections=sections, code=code, cost=cost,
                mistakes=mistakes, related=[A + path for path in related])


lessons = [
    lesson('competing-event-cumulative-incidence',
        'Competing events: calculate the probability of each first outcome', COMPETE,
        'Cumulative incidence tracks the probability of a particular first event while retaining other first events as competing outcomes.', [
            ('Define what stops the target event', 'A support queue can resolve a ticket, lose it to customer withdrawal, or remain open at extraction. If withdrawal makes resolution of that ticket impossible in the defined episode, withdrawal competes with resolution. An ordinary censored record is different: its future event is unknown after follow-up stops. Define entry, event time, event type, and administrative censoring before calculating a curve. [[applied-statistics/survival-risk-set-and-event-order|The risk-set lesson]] supplies the starting denominator and event order.'),
            ('Accumulate target events from the full risk set', 'At each event time, the increment in target cumulative incidence is the probability of having avoided all first events before that time, multiplied by target events divided by the current risk set. Then reduce event-free survival by both target and competing events. The code accepts grouped counts already ordered by event time. It assumes any withdrawals from follow-up have already been removed from later risk sets; it does not infer their timing. A later target event cannot be assigned to a ticket already withdrawn in this single-episode analysis.'),
            ('Avoid the wrong censoring shortcut', 'If competing withdrawals are treated like ordinary independent censoring and one minus a target-only Kaplan–Meier curve is called the real-world resolution probability, the result generally overstates that probability. That shortcut imagines a setting where withdrawn tickets could still later resolve. It may have a different hypothetical interpretation, but it is not the observed-world chance of resolution before withdrawal. [[applied-statistics/cause-specific-hazard-vs-incidence|The next lesson]] distinguishes a conditional event rate from an absolute event probability.'),
            ('Show every state at the horizon', 'At each decision horizon, report the chance of resolution, the chance of withdrawal, and the chance of no first event yet. They should fit the same episode definition and sum to one before any loss-to-follow-up adjustment. State uncertainty and how censoring was handled. A short study with late entry or many open tickets cannot be summarized by dividing resolved tickets by all tickets without regard to follow-up. [[applied-statistics/support-withdrawal-competing-project|The project]] makes the event ledger a release gate.')
        ], '''def grouped_cumulative_incidence(event_rows):
    survival = 1.0
    target_cumulative = 0.0
    other_cumulative = 0.0
    results = []
    for at_risk, resolved, withdrawn in event_rows:
        if at_risk <= 0 or min(resolved, withdrawn) < 0 or \
           resolved + withdrawn > at_risk:
            raise ValueError("invalid event-time counts")
        target_cumulative += survival * resolved / at_risk
        other_cumulative += survival * withdrawn / at_risk
        survival *= 1 - (resolved + withdrawn) / at_risk
        results.append((target_cumulative, other_cumulative, survival))
    return results

curve = grouped_cumulative_incidence([(50, 4, 6), (40, 5, 3)])
assert tuple(round(value, 2) for value in curve[-1]) == (0.18, 0.18, 0.64)
''', 'The grouped scan takes O(k) time and O(k) output space for k event times; a final-horizon value needs O(1) extra space. Sorting raw events costs O(n log n). The hard part is reconciling event types and risk sets when tickets re-open or follow-up ends at different times.',
        ['Treating withdrawal as independent censoring when reporting observed-world resolution probability.', 'Letting a ticket resolve after it has left the single-episode risk set.', 'Mixing administrative censoring with a real competing outcome.', 'Reporting a cumulative incidence without its time horizon or remaining event-free fraction.'],
        ['cause-specific-hazard-vs-incidence', 'support-withdrawal-competing-project', 'survival-risk-set-and-event-order', 'restricted-mean-resolution-time', 'population-estimand-and-sampling-frame']),
    lesson('cause-specific-hazard-vs-incidence',
        'Cause-specific hazard versus cumulative incidence: know which question changed', COMPETE,
        'A cause-specific hazard is an instantaneous event rate among those still event-free; cumulative incidence is a probability by a stated horizon.', [
            ('Read the denominator for a rate', 'A queue manager asks whether a process change makes resolution faster among tickets still open and not withdrawn. The cause-specific resolution hazard examines target events among tickets in that event-free risk set. Its local rate is conditioned on reaching the time without either event. It is useful for describing a transition mechanism, but a hazard ratio is not the same as a ratio of resolved-ticket probabilities. [[applied-statistics/survival-risk-set-and-event-order|The risk-set lesson]] checks whether the denominator is constructed correctly.'),
            ('Account for the competing path', 'A process could raise the resolution hazard and also sharply raise withdrawal. The final fraction resolved by day twelve depends on both paths, because withdrawals remove tickets before they can resolve. A model for only the resolution hazard cannot directly give the observed-world resolution probability without information about the competing hazard as well. The grouped code calculates one event-time transition from a supplied event-free survival value; it does not fit either hazard model or attach uncertainty.'),
            ('Select a measure for the decision', 'If the operational promise is the share of eligible tickets resolved by a deadline despite withdrawal, report cumulative incidence at that deadline. If the question is the resolution transition among tickets currently event-free, a cause-specific rate is relevant. For causal comparisons, intervention effects on withdrawal and censoring must be considered; changing the competing event can change target incidence even without a direct effect on the target transition. [[applied-statistics/competing-event-cumulative-incidence|The cumulative-incidence lesson]] provides the probability calculation.'),
            ('Document timing and assumptions', 'Show event counts by time, the event-free risk set, the separate transition rates, and horizon-specific probabilities. Define whether reopenings begin a new episode and whether customers can withdraw after resolution. A competing-event analysis of first outcomes cannot answer how often a resolved ticket reopens. If censoring depends on unrecorded ticket difficulty, even a correctly built competing-risk curve can be biased. [[applied-statistics/support-withdrawal-competing-project|The project]] audits that distinction before a queue change is called successful.')
        ], '''def event_time_transition(event_free_probability, at_risk,
                          resolved, withdrawn):
    if not 0 <= event_free_probability <= 1 or at_risk <= 0 or \
       min(resolved, withdrawn) < 0 or resolved + withdrawn > at_risk:
        raise ValueError("invalid transition inputs")
    resolution_increment = event_free_probability * resolved / at_risk
    withdrawal_increment = event_free_probability * withdrawn / at_risk
    next_event_free = event_free_probability - resolution_increment - \
                      withdrawal_increment
    return resolution_increment, withdrawal_increment, next_event_free

assert tuple(round(value, 2) for value in event_time_transition(0.8, 40, 5, 3)) \
       == (0.1, 0.06, 0.64)
''', 'One transition is O(1); a k-time curve is O(k) time and can stream with O(1) extra space. Estimating separate hazards with covariates is more costly and needs adequate events per type. No amount of model fitting compensates for a mislabeled withdrawal event.',
        ['Calling a cause-specific hazard ratio a risk ratio.', 'Reporting target-event incidence without counting competing events.', 'Using a first-event analysis to claim something about later reopenings.', 'Ignoring censoring related to unrecorded difficulty.'],
        ['competing-event-cumulative-incidence', 'support-withdrawal-competing-project', 'survival-risk-set-and-event-order', 'restricted-mean-resolution-time', 'observation-probability-weighting-and-sensitivity']),
    lesson('support-withdrawal-competing-project',
        'Project: audit support resolution when customers can withdraw', COMPETE,
        'Rebuild first-event histories and compare resolution by deadline without misclassifying withdrawal as ordinary follow-up loss.', [
            ('Write the decision target', 'A support team reports that a new triage policy resolved more tickets by day twelve. Define the eligible ticket cohort, policy assignment, clock origin, resolution event, customer withdrawal, and last reliable follow-up. A ticket with no recorded end after its export date is censored; a ticket explicitly withdrawn is a competing event. Do not count a reopening as a first resolution in the same episode. [[applied-statistics/competing-event-cumulative-incidence|The incidence lesson]] describes the required first-event frame.'),
            ('Reconcile every transition', 'Link ticket IDs to resolution, withdrawal, and export logs. Reject impossible ordering such as withdrawal before entry, and settle same-time event priority before analysis. Compare follow-up completeness under old and new policy; a system migration that drops late resolution scans can imitate lower performance. Make counts of resolved, withdrawn, still observed, and censored available by assignment group. [[applied-statistics/missing-outcome-ledger-and-target-population|The missingness ledger]] guards against silently deleting unknown endings.'),
            ('Estimate the operational probability', 'Use a competing-risk cumulative incidence for resolution by the declared day, and show withdrawal incidence and event-free remainder at the same horizon. Include uncertainty that respects the assignment unit, especially if support teams rather than tickets received the policy. A cause-specific resolution hazard can be supplementary, but it does not replace the deadline probability. [[applied-statistics/cause-specific-hazard-vs-incidence|The rate-versus-risk lesson]] explains why they can move in different directions.'),
            ('Publish a cautious release packet', 'The packet contains cohort SQL version, event map, timing convention, censoring summary, incidence curves, horizon contrasts, uncertainty, and the assignment unit. The gate below stops a headline if event order or policy capture is unresolved. Passing it permits statistical review rather than guaranteeing a causal policy effect. If withdrawal patterns changed under triage, disclose that change next to resolution so the result is not interpreted as a simple speed improvement.')
        ], '''def competing_event_gate(audit):
    if audit["unresolved_event_order"]:
        return "hold:event-order"
    if audit["unmatched_policy_assignments"]:
        return "hold:assignment-ledger"
    if not audit["censoring_reconciled"]:
        return "hold:follow-up"
    if not audit["withdrawal_reported"]:
        return "hold:competing-outcome"
    return "review:deadline-incidence"

audit = {"unresolved_event_order": 2, "unmatched_policy_assignments": 0,
         "censoring_reconciled": True, "withdrawal_reported": True}
assert competing_event_gate(audit) == "hold:event-order"
assert competing_event_gate({**audit, "unresolved_event_order": 0}) \
       == "review:deadline-incidence"
''', 'The release gate is O(1). Sorting n ticket events is O(n log n), and joining logs can dominate runtime. The largest cost is resolving ambiguous transitions; a fast curve made from the wrong event order is less useful than a delayed but auditable result.',
        ['Censoring explicit withdrawal.', 'Counting a reopened ticket as a first-event resolution.', 'Ignoring changes in follow-up after a logging migration.', 'Claiming a hazard contrast alone proves a deadline benefit.'],
        ['competing-event-cumulative-incidence', 'cause-specific-hazard-vs-incidence', 'survival-risk-set-and-event-order', 'missing-outcome-ledger-and-target-population', 'randomization-unit-and-experiment-design'], True),
    lesson('outcome-misclassification-and-prevalence-correction',
        'Outcome misclassification: correct an observed rate only under stated label-error assumptions', LABEL,
        'A verified sensitivity and specificity pair can adjust a binary observed rate when the labeling process is stable and sufficiently informative.', [
            ('Separate event from recorded label', 'An invoice audit uses an automated flag as a proxy for confirmed duplicate payment. Some true duplicates are missed, and some valid invoices are flagged. The observed flag rate is not the true duplicate rate. Sensitivity is the chance of a flag given a true duplicate; specificity is the chance of no flag given a truly valid invoice. Both need an adjudicated validation set reflecting the same cases and operating conditions as the target period. [[applied-statistics/diagnostic-performance-and-prevalence|The diagnostic lesson]] explains how prevalence changes what a positive flag means.'),
            ('Understand the algebra and its boundary', 'Under constant sensitivity and specificity, observed positive rate equals sensitivity times true prevalence plus one minus specificity times one minus prevalence. Rearranging gives corrected prevalence as observed rate plus specificity minus one, divided by sensitivity plus specificity minus one. The denominator must be positive for this orientation to contain useful information. The code raises an error when the supplied values imply an impossible corrected fraction; silently clipping it to zero would hide an inconsistent model or noisy estimates.'),
            ('Carry validation uncertainty', 'Sensitivity and specificity are estimates, not fixed facts. A rare event can make the corrected rate very sensitive to a small specificity error because false positives may outnumber true positives. Report the adjudication sample sizes and uncertainty in all inputs, then propagate it with an appropriate interval or resampling method. If the flagging process changed by branch, use branch-specific validation or a model that states its transport assumptions. [[applied-statistics/rare-proportion-wilson-interval|The rare-rate lesson]] warns against overconfident intervals near zero.'),
            ('Ask who was verified', 'If only flagged invoices are manually reviewed, specificity among unflagged invoices cannot be estimated. The algebra cannot manufacture that missing information. Sample some unflagged invoices for adjudication and record their selection probabilities. [[applied-statistics/verification-sampling-and-weighted-error|The verification lesson]] corrects the validation design; [[applied-statistics/invoice-label-audit-project|the project]] refuses a corrected headline until that sampling is documented.')
        ], '''def corrected_binary_prevalence(observed_positive_rate,
                                sensitivity, specificity):
    if any(not 0 <= value <= 1 for value in
           (observed_positive_rate, sensitivity, specificity)):
        raise ValueError("inputs must be proportions")
    information = sensitivity + specificity - 1
    if information <= 0:
        raise ValueError("label test is not informative in this orientation")
    corrected = (observed_positive_rate + specificity - 1) / information
    if not 0 <= corrected <= 1:
        raise ValueError("supplied rates are incompatible with this model")
    return corrected

assert round(corrected_binary_prevalence(0.08, 0.80, 0.96), 6) == \
       round(0.04 / 0.76, 6)
''', 'The algebra is O(1). Estimating sensitivity and specificity requires adjudication, and uncertainty propagation costs additional computation. When specificity is near one and event prevalence is tiny, a minor validation error can dominate the corrected answer.',
        ['Calling a flag a confirmed outcome.', 'Using sensitivity and specificity from another policy version without a transport check.', 'Clipping an impossible corrected rate instead of investigating model inconsistency.', 'Treating estimated error rates as exact when calculating final uncertainty.'],
        ['verification-sampling-and-weighted-error', 'invoice-label-audit-project', 'diagnostic-performance-and-prevalence', 'rare-proportion-wilson-interval', 'risk-difference-risk-ratio-and-odds']),
    lesson('verification-sampling-and-weighted-error',
        'Verification sampling: recover label error when flags get unequal review', LABEL,
        'A stratified adjudication sample needs its review probabilities in the analysis, especially when flagged and unflagged cases are sampled differently.', [
            ('Name the verification mechanism', 'An invoice team sends nearly every automated flag to a reviewer but audits only a fraction of unflagged invoices. The adjudicated set is therefore not a simple random sample of all eligible invoices. Computing sensitivity, specificity, or prevalence from that reviewed set without its sampling fractions overrepresents flagged items. Build the full flag-by-review ledger and retain the probability that each invoice entered manual verification. [[applied-statistics/stratified-survey-estimate-and-population-weights|The survey-weight lesson]] uses the same population accounting idea.'),
            ('Weight the validated cells', 'For a sampled invoice, use inverse verification probability to estimate how much of the full eligible population that record represents. Summing weights within the true-label by automated-flag cells gives estimated population cell totals. Divide the weighted true-positive total by all weighted true positives and false negatives for sensitivity; analogous weighted cells yield specificity. The code illustrates the weighted table, not its uncertainty interval. Positivity matters: if no unflagged invoice can be reviewed, missed duplicates cannot be estimated from this design.'),
            ('Avoid designing a collider', 'If review probability also depends on branch, invoice size, or other recorded risk cues, the weighting model must include those cues or the design must stratify on them. If reviewers see the original flag, their adjudication can be influenced by it; consider blinded or independently checked reviews for a sample. [[applied-statistics/reviewer-agreement-and-prevalence|The reviewer-agreement lesson]] handles disagreement, which is separate from unequal selection into review.'),
            ('Report design and uncertainty', 'Show eligible counts by flag status, verified counts, sampling fractions, effective weight concentration, adjudication procedure, and uncertainty that reflects the stratified design. A point estimate from a handful of unflagged audits can be fragile even when thousands of flagged invoices were reviewed. [[applied-statistics/outcome-misclassification-and-prevalence-correction|The correction lesson]] can then use the validation estimates under its own assumptions. [[applied-statistics/invoice-label-audit-project|The project]] gates both steps before publication.')
        ], '''def weighted_verification_cells(reviewed_invoices):
    cells = {(truth, flag): 0.0 for truth in (False, True)
             for flag in (False, True)}
    for confirmed_duplicate, auto_flagged, review_probability in reviewed_invoices:
        if not 0 < review_probability <= 1:
            raise ValueError("positive verification probability required")
        cells[(bool(confirmed_duplicate), bool(auto_flagged))] += \
            1 / review_probability
    return cells

cells = weighted_verification_cells([(True, True, 1.0),
                                     (False, True, 1.0),
                                     (True, False, 0.25)])
assert cells[(True, False)] == 4.0
assert cells[(True, True)] == 1.0
''', 'Accumulating n reviewed invoices takes O(n) time and O(1) table space for binary truth and flag states. Checking frame completeness and adjudication quality dominates. Extremely small review probabilities create unstable weights rather than free information.',
        ['Estimating specificity from a flagged-only review file.', 'Assigning zero to a cell that could never enter verification.', 'Ignoring branch-dependent verification probabilities.', 'Treating reviewer consensus as infallible ground truth.'],
        ['outcome-misclassification-and-prevalence-correction', 'invoice-label-audit-project', 'stratified-survey-estimate-and-population-weights', 'reviewer-agreement-and-prevalence', 'diagnostic-performance-and-prevalence']),
    lesson('invoice-label-audit-project',
        'Project: estimate duplicate-invoice prevalence with audited label error', LABEL,
        'Build a verification sample across flagged and unflagged invoices, then decide whether a corrected duplicate rate is defensible.', [
            ('Freeze a population and a truth rule', 'An accounts team reports a low duplicate-invoice rate from an automated flag. Define eligible invoices by approval date, one invoice as the counting unit, the rule version, and a consistent independent adjudication standard. Preserve flagged and unflagged invoices in the frame. Decide whether the target is confirmed duplicates, disputed duplicates, or automated flags; these are not the same event. [[applied-statistics/population-estimand-and-sampling-frame|The frame lesson]] gives the denominator.'),
            ('Design the verification sample', 'Sample invoices from both flag groups and record each inclusion probability. Oversample flags if review resources are tight, but retain some unflagged records so missed duplicates and specificity can be learned. Record branch and invoice-value bands if selection varies across them. Keep reviewers from simply copying the automated flag, and sample disagreements for a second adjudication. [[applied-statistics/verification-sampling-and-weighted-error|The verification lesson]] turns unequal review rates into weighted cell estimates.'),
            ('Calculate with uncertainty and sensitivity', 'Estimate flag sensitivity and specificity from the designed validation sample and compare the raw flag rate with a corrected duplicate prevalence under the stable-error assumption. Propagate uncertainty from both the observed flag rate and validation estimates. If a change in rule version alters error rates, produce version-specific results rather than applying one correction to all months. A correction that leaves the zero-to-one range signals an incompatible point model or sampling noise that deserves review. [[applied-statistics/outcome-misclassification-and-prevalence-correction|The correction lesson]] makes the assumption visible.'),
            ('Release an audit trail', 'The packet includes eligible counts, review draws and fractions, adjudication protocol, weighted confusion cells, estimated error rates, corrected rate and interval, rule version, and unresolved disagreement. The gate below blocks a headline if one flag stratum was never verified or if adjudicators were not assigned a documented truth rule. Passing it begins statistical review, not a guarantee that manual review is perfect. A recurring audit should check whether the labeling process drifts.')
        ], '''def invoice_label_gate(audit):
    if not audit["truth_rule_documented"]:
        return "hold:adjudication-rule"
    if audit["verified_flagged"] == 0 or audit["verified_unflagged"] == 0:
        return "hold:verification-support"
    if not audit["selection_probabilities_recorded"]:
        return "hold:sample-weights"
    if audit["unresolved_disagreements"]:
        return "hold:adjudication"
    return "review:corrected-prevalence"

audit = {"truth_rule_documented": True, "verified_flagged": 37,
         "verified_unflagged": 0, "selection_probabilities_recorded": True,
         "unresolved_disagreements": 0}
assert invoice_label_gate(audit) == "hold:verification-support"
assert invoice_label_gate({**audit, "verified_unflagged": 29}) == \
       "review:corrected-prevalence"
''', 'The gate is O(1), and weighted table construction is O(n) in reviewed invoices. Human verification is the limiting resource. Increasing only the flagged review count cannot identify missed duplicates when the unflagged stratum receives no review.',
        ['Using automatic flags as the truth variable.', 'Verifying only flags and reporting a corrected population rate.', 'Dropping selection probabilities after oversampling.', 'Reusing an old rule-version validation estimate without testing stability.'],
        ['outcome-misclassification-and-prevalence-correction', 'verification-sampling-and-weighted-error', 'population-estimand-and-sampling-frame', 'reviewer-agreement-and-prevalence', 'rare-proportion-wilson-interval'], True),
    lesson('blocked-randomization-permutation-test',
        'Blocked randomization inference: permute labels only inside assignment blocks', BLOCK,
        'An exact randomization test reproduces the actual assignment mechanism under a sharp no-effect null instead of shuffling labels across incomparable units.', [
            ('Match the test to assignment', 'A warehouse assigns a new scan procedure to half the shifts within each depot. Depot is an assignment block because route volume and scanner setup differ. Under the sharp null that the procedure changes no shift outcome, observed outcomes remain fixed while labels are reallocated according to the same within-depot randomization rule. A global permutation that moves assignments between depots was never possible in this experiment. [[applied-statistics/randomization-unit-and-experiment-design|The design lesson]] identifies the shift as the unit.'),
            ('Enumerate a small design exactly', 'For each block, choose the same number of treated shifts as originally assigned; take the Cartesian product of those block-specific assignments. Calculate a prespecified statistic under each possible assignment. The code uses the mean of block treatment-minus-control differences and returns the upper-tail randomization p-value including the observed assignment. It is intentionally for tiny experiments: combinations multiply quickly. Ties count as at least as extreme in this one-sided test, and the test should not be mislabeled two-sided.'),
            ('Understand what the null covers', 'A sharp null says every shift would have the same outcome under either assignment, allowing all counterfactual outcomes to be imputed from observed outcomes. Failure to reject is not proof of no useful effect; a confidence interval or effect estimate is needed for that. If outcomes are missing after assignment, permutation of only observed shifts breaks the design unless the missingness rule is justified. [[applied-statistics/multiple-comparisons-and-stopping-rule|Stopping and multiplicity]] still matter if many endpoints were searched.'),
            ('Keep interference on the table', 'A control shift sharing staff and a scanner with a treated shift may receive part of the intervention. Then the potential outcome of one shift depends on assignments around it, violating the simple no-interference reading. Record adjacency and operational overlap before interpreting a shift-level contrast. [[applied-statistics/interference-exposure-and-cluster-design|The interference lesson]] discusses exposure mapping; [[applied-statistics/depot-scan-blocked-trial-project|the project]] checks it before accepting the test.')
        ], '''from itertools import combinations, product

def blocked_upper_tail(blocks, observed_statistic):
    assignment_options = []
    for outcomes, treated_count in blocks:
        if not 0 < treated_count < len(outcomes):
            raise ValueError("each block needs treated and control shifts")
        assignment_options.append(list(combinations(range(len(outcomes)),
                                                   treated_count)))
    extreme = total = 0
    for assignment in product(*assignment_options):
        block_differences = []
        for (outcomes, _), treated_indices in zip(blocks, assignment):
            treated = set(treated_indices)
            treated_mean = sum(outcomes[i] for i in treated) / len(treated)
            control_mean = sum(value for i, value in enumerate(outcomes)
                               if i not in treated) / (len(outcomes) - len(treated))
            block_differences.append(treated_mean - control_mean)
        statistic = sum(block_differences) / len(block_differences)
        extreme += statistic >= observed_statistic - 1e-12
        total += 1
    return extreme / total

assert blocked_upper_tail([([21, 29], 1), ([33, 41], 1)], 8) == 0.25
''', 'With b blocks, the exact enumeration count is the product of combinations of block size and treated count; runtime grows at least that fast. Memory stores each block assignment list. Larger experiments need a prespecified Monte Carlo draw from the same design, with its simulation error reported.',
        ['Shuffling labels across blocks that never shared an assignment lottery.', 'Calling a one-sided upper-tail value two-sided.', 'Treating nonrejection as evidence of equivalence.', 'Ignoring shared staff or other interference between assigned shifts.'],
        ['interference-exposure-and-cluster-design', 'depot-scan-blocked-trial-project', 'randomization-unit-and-experiment-design', 'paired-randomization-check', 'multiple-comparisons-and-stopping-rule']),
    lesson('interference-exposure-and-cluster-design',
        'Interference exposure: decide whether the assigned unit can be isolated', BLOCK,
        'When one unit can change another unit’s outcome, treatment labels alone do not describe the exposure each unit received.', [
            ('Map the operational edges', 'A depot trial assigns a scan process by shift, but workers switch between adjacent shifts and share the same scanner queue. A nominal control shift may therefore use a device configured by a treated shift. List the ways exposure can travel: staff handoff, shared equipment, route reassignment, and supervisor instruction. Define an exposure mapping before outcome review, such as own-shift assignment plus the count of adjacent treated shifts. [[applied-statistics/randomization-unit-and-experiment-design|The assignment-unit lesson]] shows why individual tickets are not independent units in this design.'),
            ('Choose a design that contains the spillover', 'If sharing is frequent, randomize at depot-week or another cluster broad enough to contain most transfer, then obtain enough independent clusters for uncertainty. If clusters still interact, buffer periods or network-aware assignment may be needed. A larger cluster reduces the number of independent units and can raise the sample-size requirement. [[applied-statistics/cluster-attrition-and-power-budget|The cluster-power lesson]] covers that cost, while [[applied-statistics/cluster-bootstrap-and-standard-error|the bootstrap lesson]] guards against row-level precision.'),
            ('Do not mistake exposure for assignment', 'Assignment is randomized; actual exposure can depend on staffing decisions and workloads after assignment. Comparing high-exposure and low-exposure shifts without adjustment is not automatically causal, even when the original policy labels were randomized. A direct effect under one neighbor configuration differs from an overall rollout effect in which every neighboring shift is treated. State which effect the decision needs. The code counts neighboring treated assignments as a descriptive design audit, not a causal effect estimator.'),
            ('Document the residual risk', 'Report the network or roster snapshot, cluster boundaries, transitions across boundaries, timing, and the percentage of control units exposed indirectly. If transfer is material, an ordinary blocked permutation test of a no-spillover effect may answer the wrong question. [[applied-statistics/blocked-randomization-permutation-test|The blocked-test lesson]] remains valid only for its assignment mechanism and sharp-null interpretation. [[applied-statistics/depot-scan-blocked-trial-project|The project]] stops a simple policy claim when handoff leakage is unmeasured.')
        ], '''def neighbor_treatment_counts(assignments, adjacency):
    if set(assignments) != set(adjacency):
        raise ValueError("every shift needs a roster entry")
    counts = {}
    for shift_id, neighbors in adjacency.items():
        if not set(neighbors) <= set(assignments):
            raise ValueError("unknown neighboring shift")
        counts[shift_id] = sum(bool(assignments[neighbor]) for neighbor in neighbors)
    return counts

assignments = {"north-early": True, "north-late": False,
               "south-early": False}
adjacency = {"north-early": ["north-late"],
             "north-late": ["north-early", "south-early"],
             "south-early": ["north-late"]}
assert neighbor_treatment_counts(assignments, adjacency)["north-late"] == 1
''', 'Counting exposures is O(V + E) time for V shifts and E directed adjacency entries, with O(V) output space. The roster and equipment-sharing audit costs more than the graph scan. Moving to cluster assignment reduces independent units and should be reflected in power and variance calculations.',
        ['Equating randomized assignment with actual received exposure.', 'Treating tickets within a shared scanner queue as independent experimental units.', 'Changing an exposure mapping after seeing which group benefits.', 'Calling a shift-level contrast a full-rollout effect without a neighbor-policy assumption.'],
        ['blocked-randomization-permutation-test', 'depot-scan-blocked-trial-project', 'randomization-unit-and-experiment-design', 'cluster-attrition-and-power-budget', 'cluster-bootstrap-and-standard-error']),
    lesson('depot-scan-blocked-trial-project',
        'Project: audit a depot scan trial with blocked assignment and shared staff', BLOCK,
        'Reconstruct the shift lottery, check contamination, and decide whether a blocked randomization analysis supports deployment.', [
            ('Freeze design and target', 'A logistics team tested a new scan sequence on selected shifts inside each depot. Define eligible shifts, depot blocks, the fixed number assigned to the new process in each block, the outcome measured per shift, and the target policy effect. Preserve the assignment ledger even when a shift has no usable scan-time measure. A row-level analysis of individual parcels would create false precision because the lottery happened at shift level. [[applied-statistics/randomization-unit-and-experiment-design|The assignment lesson]] identifies the unit.'),
            ('Rebuild the actual lottery', 'Check that every recorded treatment label is possible under the block-specific allocation and that the analysis does not move labels across depots. Freeze one shift-level statistic and a one-sided or two-sided decision before examining results. Enumerate the within-block assignments for a small study or sample assignments from the same lottery for a larger one. [[applied-statistics/blocked-randomization-permutation-test|The randomization lesson]] demonstrates the sharp-null test, whose p-value is not a policy effect estimate.'),
            ('Measure operational spillover', 'Join shifts to staff handoffs, scanner queues, and route transfers. Count control shifts with treated neighbors and note when configuration persisted across the boundary. If interference is substantial, revise the estimand and study design before claiming an isolated shift effect; consider depot-week assignment for a follow-up trial. [[applied-statistics/interference-exposure-and-cluster-design|The interference lesson]] explains the tradeoff between containment and independent cluster count.'),
            ('Release the evidence packet', 'The packet holds the lottery seed or allocation log, block sizes, missing-outcome ledger, prespecified statistic, effect estimate and uncertainty, permutation result, spillover map, and an operational cost threshold. The gate below blocks claims when assignments do not match the planned lottery or shared-staff exposure has not been audited. A passing gate permits a scoped result, not an assertion that every depot will improve. Monitor the implemented rollout against the trial conditions.')
        ], '''def depot_trial_gate(audit):
    if audit["assignment_violations"]:
        return "hold:lottery-mismatch"
    if audit["missing_shift_outcomes"] and not audit["missingness_reviewed"]:
        return "hold:missing-shifts"
    if not audit["spillover_audited"]:
        return "hold:shared-staff-exposure"
    if not audit["statistic_predeclared"]:
        return "hold:analysis-selection"
    return "review:scoped-depot-effect"

audit = {"assignment_violations": 0, "missing_shift_outcomes": 1,
         "missingness_reviewed": True, "spillover_audited": False,
         "statistic_predeclared": True}
assert depot_trial_gate(audit) == "hold:shared-staff-exposure"
assert depot_trial_gate({**audit, "spillover_audited": True}) == \
       "review:scoped-depot-effect"
''', 'The gate is O(1). Exact assignment enumeration can grow combinatorially with shifts per block; the staff-sharing audit is O(V + E) after roster extraction. Treating every parcel as an independent replicate is cheap but gives the wrong uncertainty for a shift lottery.',
        ['Permuting across depots despite within-depot assignment.', 'Dropping shifts with missing outcomes after seeing their labels.', 'Ignoring scanner and staff spillover into controls.', 'Using a sharp-null p-value as the size of the rollout benefit.'],
        ['blocked-randomization-permutation-test', 'interference-exposure-and-cluster-design', 'randomization-unit-and-experiment-design', 'cluster-bootstrap-and-standard-error', 'multiple-comparisons-and-stopping-rule'], True),
]

crosslinks = [
    (A + 'survival-risk-set-and-event-order', A + 'competing-event-cumulative-incidence'),
    (A + 'restricted-mean-resolution-time', A + 'cause-specific-hazard-vs-incidence'),
    (A + 'support-queue-survival-project', A + 'support-withdrawal-competing-project'),
    (A + 'diagnostic-performance-and-prevalence', A + 'outcome-misclassification-and-prevalence-correction'),
    (A + 'reviewer-agreement-and-prevalence', A + 'verification-sampling-and-weighted-error'),
    (A + 'claims-audit-quality-project', A + 'invoice-label-audit-project'),
    (A + 'randomization-unit-and-experiment-design', A + 'blocked-randomization-permutation-test'),
    (A + 'cluster-bootstrap-and-standard-error', A + 'interference-exposure-and-cluster-design'),
    (A + 'receipt-review-experiment-project', A + 'depot-scan-blocked-trial-project'),
]

if __name__ == '__main__':
    publish(lessons, [COMPETE, LABEL, BLOCK], crosslinks,
            'aitrove-applied-statistics-competing-measurement-randomization-import-20261007.json',
            8466, subject='applied-statistics',
            hub_path=A + 'applied-statistics-tutorial')
