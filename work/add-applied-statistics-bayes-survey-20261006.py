"""Add Bayesian model checks and design-aware survey estimation."""
from de_batch_publisher import publish

A = 'applied-statistics/'
BAYES = 'Bayesian model checks and decisions'
SURVEY = 'Survey estimates and design-aware uncertainty'
lessons = [
    {
        'path': A + 'prior-sensitivity-and-effective-information',
        'title': 'Prior sensitivity: show when limited data leave a decision exposed',
        'module': BAYES, 'project': False,
        'summary': 'A prior is part of a Bayesian model; compare defensible alternatives when its influence can change an operational decision.',
        'sections': [
            ('Name the rate and time window', 'A helpdesk tracks the fraction of support tickets escalated within one day. Define which tickets count, when the outcome is mature and whether repeat contacts from one customer are independent. A beta-binomial model treats observed escalations as conditionally exchangeable Bernoulli outcomes with one common rate. That compact assumption can fail if queues or shifts differ. [[applied-statistics/population-estimand-and-sampling-frame|The target population]] determines what the rate represents.'),
            ('Make the prior interpretable', 'Write a Beta prior with positive shape values before looking at this period. Its mean is alpha divided by alpha plus beta; that sum indicates how much prior concentration the model carries, although it is not automatically a literal sample of past tickets. After s escalations among n mature tickets, the posterior is Beta(alpha+s, beta+n-s). Compare a low-concentration prior with a prior reflecting documented past operations. [[data-science/beta-binomial-updating-and-effective-prior-size|The basic update]] supplies the arithmetic; the applied question is whether the chosen prior changes the action.'),
            ('Test sensitivity at the decision boundary', 'Translate each posterior into the same decision rule, cost assumptions and observation window. If one reasonable prior favors intervention and another does not, report the decision as prior-sensitive rather than selecting whichever result is convenient. Check prior predictive implications: would this prior regularly predict implausible escalation counts before seeing current tickets? A prior with a plausible mean can still be too concentrated. [[applied-statistics/posterior-predictive-group-check|Predictive checks]] inspect a different failure: whether the common-rate model can reproduce the observed group pattern.'),
            ('Record the uncertainty that remains', 'A posterior interval answers a probability statement conditional on the model and prior, unlike a frequentist confidence interval. Neither removes biased ticket selection, delayed escalation labels or a changed queue policy. Archive the prior choices, mature outcome counts, posterior summaries and action thresholds. [[data-science/posterior-intervals-and-decision-probabilities|Decision probabilities]] connect uncertainty to the action; [[applied-statistics/helpdesk-escalation-bayesian-project|the project]] shows two priors leading to different recommendations.'),
        ],
        'code': '''def escalation_posterior(prior_alpha, prior_beta, escalations, mature_tickets):
    if prior_alpha <= 0 or prior_beta <= 0:
        raise ValueError("prior shapes must be positive")
    if not 0 <= escalations <= mature_tickets:
        raise ValueError("invalid observed counts")
    alpha = prior_alpha + escalations
    beta = prior_beta + mature_tickets - escalations
    return {"alpha": alpha, "beta": beta, "mean": alpha / (alpha + beta)}

weak = escalation_posterior(2, 18, 9, 47)
skeptical = escalation_posterior(4, 56, 9, 47)
assert weak["mean"] > 0.14
assert skeptical["mean"] < 0.14
''',
        'cost': 'A conjugate update is O(1) time and space after valid counts exist. Repeating it across k priors costs O(k), while collecting comparable, mature tickets and checking group structure dominate operational effort. More numerical precision cannot compensate for a prior chosen after seeing the preferred action.',
        'mistakes': ['Describing alpha plus beta as observed prior tickets without evidence.', 'Picking the prior that produces the desired escalation decision.', 'Treating a narrow posterior as protection against a changed ticket frame.', 'Pooling repeat contacts as independent Bernoulli trials without checking dependence.'],
        'related': [A + 'posterior-predictive-group-check', A + 'helpdesk-escalation-bayesian-project', A + 'population-estimand-and-sampling-frame', 'data-science/beta-binomial-updating-and-effective-prior-size', 'data-science/posterior-intervals-and-decision-probabilities'],
    },
    {
        'path': A + 'posterior-predictive-group-check',
        'title': 'Posterior predictive checks: can one rate reproduce the group pattern?',
        'module': BAYES, 'project': False,
        'summary': 'A posterior predictive check simulates outcomes from a fitted model and compares a declared feature of those outcomes with observed data.',
        'sections': [
            ('Choose a discrepancy that matters', 'The helpdesk model assumes one escalation rate across two queues. Operations sees a much higher observed rate in the night queue. Before simulating, choose the absolute difference between queue rates as the discrepancy. The goal is not to certify the model with one number; it is to ask whether replicated datasets under the common-rate model commonly exhibit a gap at least as large as the real one. [[applied-statistics/prior-sensitivity-and-effective-information|Prior choice]] determines the posterior parameter draws used in this check.'),
            ('Replicate the observation process', 'Draw a rate from the posterior, then draw new escalation counts for each queue at its observed number of mature tickets. Compare replicated gaps with the observed gap. Preserve queue denominators and the same outcome window; otherwise the simulation tests a different design. A small replicated-tail fraction flags a pattern the model struggles to generate, but it is not a classical p-value and does not identify the cause. Shared agents, label delay or queue-specific rates are all candidates for investigation.'),
            ('Check multiple failure modes separately', 'A gap statistic can miss an overall count mismatch or a burst concentrated on one shift. Inspect replicated total escalations, queue gaps and temporal runs, each tied to an operational concern. Do not keep inventing checks until one produces a desired pass. Use held-out or future data when the question is predictive performance outside the fitting set. [[applied-statistics/cluster-bootstrap-and-standard-error|Cluster dependence]] matters if tickets arrive in agent or customer groups; a simple independent-binomial generator does not reproduce those correlations.'),
            ('Decide what follows', 'If a common-rate model cannot reproduce queue differences, consider a stratified or hierarchical model, or repair the event ledger if labels differ by queue. Compare model revisions using the same outcome definition and sample frame. Keep the simulated distribution and random seed in the review packet. [[applied-statistics/helpdesk-escalation-bayesian-project|The project]] holds an automatic intervention while the night queue discrepancy remains unexplained; [[data-science/calibration-drift-and-reference-checks|drift checks]] matter after deployment.'),
        ],
        'code': '''from random import Random

def queue_gap_check(group_counts, prior, draws=600, seed=47):
    if draws < 1 or any(not 0 <= hits <= total or total == 0
                        for hits, total in group_counts):
        raise ValueError("invalid group counts or draw count")
    observed = abs(group_counts[0][0] / group_counts[0][1] -
                   group_counts[1][0] / group_counts[1][1])
    successes = sum(hits for hits, _ in group_counts)
    trials = sum(total for _, total in group_counts)
    rng = Random(seed)
    extreme = 0
    for _ in range(draws):
        rate = rng.betavariate(prior[0] + successes,
                              prior[1] + trials - successes)
        simulated = [sum(rng.random() < rate for _ in range(total)) / total
                     for _, total in group_counts]
        extreme += abs(simulated[0] - simulated[1]) >= observed
    return extreme / draws

tail_fraction = queue_gap_check([(7, 45), (15, 39)], (2, 18))
assert 0 <= tail_fraction <= 1
''',
        'cost': 'The direct simulation uses O(d × n) time for d draws and n total ticket trials, with O(1) extra space. Vectorized or count-distribution sampling can reduce runtime for large n. The check is only as credible as the observation model: a shared-rate simulation cannot validate queue-dependent labels or correlated repeat contacts.',
        'mistakes': ['Calling the replicated-tail fraction a probability that the model is true.', 'Changing denominators or label windows between observed and simulated counts.', 'Choosing only the discrepancy that makes the model look adequate.', 'Using an in-sample predictive check as a substitute for future-period validation.'],
        'related': [A + 'prior-sensitivity-and-effective-information', A + 'helpdesk-escalation-bayesian-project', A + 'cluster-bootstrap-and-standard-error', 'data-science/beta-binomial-updating-and-effective-prior-size', 'data-science/calibration-drift-and-reference-checks'],
    },
    {
        'path': A + 'helpdesk-escalation-bayesian-project',
        'title': 'Project: review a prior-sensitive helpdesk escalation decision',
        'module': BAYES, 'project': True,
        'summary': 'Compare prior assumptions, check queue-level replication and delay a costly intervention when the model frame is inadequate.',
        'sections': [
            ('Write the decision before updating', 'The helpdesk considers adding a night-shift reviewer if one-day escalation risk is high enough. Define eligible tickets, mature one-day outcomes, the labor cost and the loss from unreviewed escalations. Use the same cost rule for every candidate prior. Nine escalations among 47 mature tickets are available for the first analysis; repeat contacts are grouped by customer for a later dependence review. [[applied-statistics/prior-sensitivity-and-effective-information|Prior sensitivity]] begins with an explicit operational threshold, not a retrospective prior choice.'),
            ('Compare plausible prior positions', 'A low-concentration prior and a more skeptical prior yield posterior means on opposite sides of the cost threshold. Record both and mark the decision prior-sensitive. The point estimates differ because 47 tickets do not overwhelm every defensible prior concentration. Plot or tabulate prior predictive ticket counts and reject a prior only for a documented mismatch, not because it blocks the preferred action. [[data-science/posterior-intervals-and-decision-probabilities|Posterior decision summaries]] should use the same loss assumptions.'),
            ('Check queue structure', 'Split the mature cases into day and night queues. The observed gap is large enough to warrant a posterior predictive group check under the pooled-rate model. Reproduce each queue count and outcome window in simulations; save the seed and a distribution of replicated gaps. If the model cannot represent the pattern, a pooled intervention rule may be wrong for both queues. Investigate queue-specific labels, agent staffing and customer mix. [[applied-statistics/posterior-predictive-group-check|The predictive check]] is a model criticism tool, not proof of a night-shift cause.'),
            ('Publish a bounded disposition', 'Hold automatic staffing changes while the prior-sensitive decision and queue discrepancy are reviewed. Continue collecting mature outcomes under the frozen definition, consider a stratified model if sample support permits, and set a revisit date. Include prior shapes, group denominators, posterior means, decision costs, predictive-check result and data owner. The result is still useful: it identifies exactly which assumption controls the proposed action. [[applied-statistics/population-estimand-and-sampling-frame|The target frame]] must remain fixed across the next sample.'),
        ],
        'code': '''def reviewer_decision(prior_options, escalations, tickets, no_review_cost,
                      review_fixed_cost, reviewed_case_cost):
    choices = []
    for alpha, beta in prior_options:
        risk = (alpha + escalations) / (alpha + beta + tickets)
        no_review = no_review_cost * risk
        add_reviewer = review_fixed_cost + reviewed_case_cost * risk
        choices.append("add-reviewer" if add_reviewer < no_review else "keep-current")
    return choices[0] if len(set(choices)) == 1 else "review:prior-sensitive"

decision = reviewer_decision([(2, 18), (4, 56)], 9, 47, 8, 0.7, 3)
assert decision == "review:prior-sensitive"
''',
        'cost': 'Computing decisions for k candidate priors costs O(k) time and O(k) space. The greater cost is validating ticket maturity, queue heterogeneity and staffing impact. An automatic change based on a single pooled posterior can spend labor on the wrong shift or miss the queue with the highest actual burden.',
        'mistakes': ['Tuning the prior after seeing which staffing decision it produces.', 'Using tickets without mature escalation outcomes in the denominator.', 'Assuming a pooled rate describes both queues despite a failed group check.', 'Equating a prior-sensitive decision with proof that data are useless.'],
        'related': [A + 'prior-sensitivity-and-effective-information', A + 'posterior-predictive-group-check', A + 'population-estimand-and-sampling-frame', 'data-science/beta-binomial-updating-and-effective-prior-size', 'data-science/posterior-intervals-and-decision-probabilities'],
    },
    {
        'path': A + 'stratified-survey-estimate-and-population-weights',
        'title': 'Stratified survey estimates: weight toward the named population',
        'module': SURVEY, 'project': False,
        'summary': 'A stratified estimate combines stratum rates using population shares, not the accidental share of completed responses.',
        'sections': [
            ('Specify the survey target', 'A service desk surveys customers in metropolitan and rural regions after case closure. The target is the satisfaction rate among all eligible closed cases in a fixed month, not just people who responded. Define the eligibility frame, outcome wording, contact modes and known region totals. An oversampled rural group may be sensible for precision, but its raw sample share should not replace its population share in an overall estimate. [[applied-statistics/population-estimand-and-sampling-frame|The estimand and frame]] come first.'),
            ('Construct the combined estimate', 'Estimate the satisfaction rate within each region, then multiply by that region’s share of eligible cases and sum. This simple poststratified calculation assumes respondents represent their region with respect to satisfaction; it cannot repair nonresponse differences within a region. If the sample had unequal inclusion probabilities inside regions, start from the documented design weights before any calibration. [[data-science/survey-inclusion-probabilities-and-base-weights|Base weights]] track that first selection step.'),
            ('Expose missing cells and weight stress', 'A region with no valid respondents cannot contribute a measured regional rate. Do not silently redistribute its population share. Report invited, eligible, contacted and completed counts by region, plus missing satisfaction answers. Inspect the largest resulting weights and the effective sample size; a few high-weight responses can dominate the estimate. [[data-science/weight-extremes-and-effective-sample-size|Weight diagnostics]] expose that concentration, while [[applied-statistics/survey-design-variance-and-psu|design variance]] addresses dependence that a weighted mean cannot describe.'),
            ('Publish the scope of inference', 'Archive the population totals and date, response definition, region mapping, weighting formula and completed-cell counts. A weighted point estimate is still vulnerable to nonresponse associated with satisfaction after conditioning on region. Compare early and late responders, conduct a bounded nonresponse sensitivity analysis and describe unresolved selection risk. [[applied-statistics/contact-center-survey-audit-project|The project]] holds a statewide claim when one region has no usable response support.'),
        ],
        'code': '''def population_weighted_satisfaction(responses_by_region, population_counts):
    if set(responses_by_region) != set(population_counts):
        raise ValueError("population and response regions differ")
    total_population = sum(population_counts.values())
    if total_population <= 0:
        raise ValueError("population must be positive")
    estimate = 0.0
    for region, answers in responses_by_region.items():
        if not answers or population_counts[region] < 0:
            raise ValueError("empty or invalid region")
        estimate += (population_counts[region] / total_population) * \
                    (sum(answers) / len(answers))
    return estimate

estimate = population_weighted_satisfaction(
    {"metro": [1, 0, 1, 1], "rural": [0, 1]},
    {"metro": 700, "rural": 300})
assert round(estimate, 6) == 0.675
''',
        'cost': 'The calculation is O(n + g) time and O(1) extra space beyond stored responses for n answers and g regions. Weight construction, contact attempts and nonresponse assessment dominate the real cost. The arithmetic yields a point estimate but does not supply a design-correct standard error or eliminate within-region selection bias.',
        'mistakes': ['Using the completed-sample region share as the population share.', 'Filling a no-response region with the overall respondent rate.', 'Calling poststratification a cure for all nonresponse bias.', 'Reporting the weighted estimate with an ordinary row-level standard error.'],
        'related': [A + 'survey-design-variance-and-psu', A + 'contact-center-survey-audit-project', A + 'population-estimand-and-sampling-frame', 'data-science/survey-inclusion-probabilities-and-base-weights', 'data-science/weight-extremes-and-effective-sample-size'],
    },
    {
        'path': A + 'survey-design-variance-and-psu',
        'title': 'Survey uncertainty: count sampled clusters, strata and weight concentration',
        'module': SURVEY, 'project': False,
        'summary': 'A survey’s standard error must reflect how units were selected; the respondent count alone does not reveal independent information.',
        'sections': [
            ('Map the actual selection design', 'The service desk samples contact-center branches, then cases inside each branch. Cases from one branch share staffing, customer mix and workflow, so they are not independent draws from the full population. Record each sampled branch as a primary sampling unit, each design stratum, inclusion and response-adjusted weights, and the analysis population. [[applied-statistics/cluster-bootstrap-and-standard-error|Cluster resampling]] explains why replacing individual cases can make uncertainty too small.'),
            ('Check whether variance is identifiable', 'A stratum represented by one sampled branch lacks direct within-stratum between-branch variation for a simple design-based variance calculation. A chosen lonely-cluster method or pooling rule requires a documented design decision; setting variance to zero is not acceptable. Count distinct branches per stratum before fitting a standard error. The diagnostic code below only checks support and weight concentration; it intentionally does not pretend to be a full survey-variance estimator.'),
            ('Separate two information limits', 'Kish effective sample size, the square of total weight divided by the sum of squared weights, describes weight concentration. It does not account for clustering and is not an adjusted number of independent branches. A large respondent count can coexist with few sampled branches and extreme weights. Use software and variance methods that encode the original strata, primary units and weights for reportable confidence intervals. [[data-science/precision-budget-and-effective-sample-size|Precision budgeting]] helps set collection targets, while [[applied-statistics/confidence-interval-coverage|coverage]] explains the repeated-sample claim.'),
            ('Report design sensitivity', 'Compare weighted and unweighted estimates as a diagnostic, not as competing truths. Show completion by stratum, sampled branches, weight range, effective count and interval method. If a region or stratum is poorly supported, mark it as limited rather than forcing a narrow statewide interval. [[applied-statistics/stratified-survey-estimate-and-population-weights|Population weighting]] provides the point estimate; [[applied-statistics/contact-center-survey-audit-project|the audit project]] blocks publication when a one-branch stratum cannot support the promised precision.'),
        ],
        'code': '''def survey_design_check(records):
    if not records:
        raise ValueError("survey records required")
    branches = {}
    weights = []
    for record in records:
        if record["weight"] <= 0:
            raise ValueError("weights must be positive")
        branches.setdefault(record["stratum"], set()).add(record["branch_id"])
        weights.append(record["weight"])
    effective_count = sum(weights) ** 2 / sum(weight ** 2 for weight in weights)
    return {"branches_per_stratum": {key: len(value) for key, value in branches.items()},
            "weight_effective_count": effective_count,
            "supported": all(len(value) >= 2 for value in branches.values())}

survey = [{"stratum": "metro", "branch_id": "m-47", "weight": 2},
          {"stratum": "metro", "branch_id": "m-82", "weight": 3},
          {"stratum": "rural", "branch_id": "r-31", "weight": 7}]
report = survey_design_check(survey)
assert not report["supported"]
assert report["weight_effective_count"] < len(survey)
''',
        'cost': 'The support scan is O(n) expected time and O(p) space for n responses and p distinct primary units. A design-aware variance calculation costs more and depends on the survey plan. The effective count is a warning about variable weights, not a shortcut to a confidence interval that ignores clustering.',
        'mistakes': ['Treating every case inside one sampled branch as independent.', 'Using weight effective count as if it accounted for cluster dependence.', 'Assigning zero variance to a stratum with one sampled branch.', 'Discarding strata and primary-unit IDs after calculating a weighted mean.'],
        'related': [A + 'stratified-survey-estimate-and-population-weights', A + 'contact-center-survey-audit-project', A + 'cluster-bootstrap-and-standard-error', A + 'confidence-interval-coverage', 'data-science/precision-budget-and-effective-sample-size'],
    },
    {
        'path': A + 'contact-center-survey-audit-project',
        'title': 'Project: audit a weighted contact-center satisfaction estimate',
        'module': SURVEY, 'project': True,
        'summary': 'Rebuild the population-weighted rate, expose a single-branch stratum and hold an overconfident statewide interval.',
        'sections': [
            ('State who is represented', 'A contact center wants a monthly satisfaction number across metropolitan and rural cases. Record all eligible closures, invitation mode, question wording, region population totals and the response window. The rural region was deliberately oversampled, so the raw respondent average is not the combined population rate. [[applied-statistics/stratified-survey-estimate-and-population-weights|The stratified estimate]] uses eligible-case shares while preserving each region’s observed rate.'),
            ('Audit the response trail', 'Count invited, contacted, completed and item-missing cases by region and branch. In the first export, rural cases came from one branch; a contractor also failed to transmit the question for a set of night contacts. Keep those misses visible. A region weight does not restore answers that are systematically missing inside that region. Compare response patterns and state a bounded sensitivity scenario before any statewide claim. [[data-science/missingness-mechanisms-and-observation-process|The observation process]] is part of the result.'),
            ('Reject false precision', 'Compute the weighted point estimate from the documented population totals, then inspect distinct sampled branches per stratum and weight concentration. The one-branch rural stratum cannot support the advertised ordinary row-level standard error. Hold that interval, consult the sampling plan for an approved variance method and gather more branches if the desired precision requires them. [[applied-statistics/survey-design-variance-and-psu|The design check]] distinguishes respondent count from independent branch support.'),
            ('Deliver a reviewable packet', 'Report regional rates with completed denominators, population controls and dates, sample-selection steps, contact and item nonresponse, branch counts, weight summary and interval method. Mark any unmeasured region or stratum explicitly. The point estimate may be presented with a clear scope if the data owner approves, but do not attach an unsupported confidence claim. [[applied-statistics/confidence-interval-coverage|Coverage language]] and [[data-science/support-survey-weighting-audit-project|the weighting audit]] connect to the follow-up collection plan.'),
        ],
        'code': '''def survey_publication_gate(report, limits):
    if report["unmatched_population_regions"]:
        return "hold:population-frame"
    if report["missing_item_share"] > limits["maximum_missing_share"]:
        return "review:item-nonresponse"
    if min(report["branches_per_stratum"].values()) < 2:
        return "hold:variance-support"
    if report["weight_effective_count"] < limits["minimum_effective_count"]:
        return "hold:weight-concentration"
    return "publish:design-reviewed"

limits = {"maximum_missing_share": 0.08, "minimum_effective_count": 72}
report = {"unmatched_population_regions": False, "missing_item_share": 0.04,
          "branches_per_stratum": {"metro": 4, "rural": 1},
          "weight_effective_count": 86}
assert survey_publication_gate(report, limits) == "hold:variance-support"
assert survey_publication_gate({**report, "branches_per_stratum":
       {"metro": 4, "rural": 3}}, limits) == "publish:design-reviewed"
''',
        'cost': 'The gate scans g strata in O(g) time and O(g) temporary space. A proper interval needs the sampling plan, primary-unit identifiers and design-aware software; extending collection across rural branches costs more than calculating a weighted point estimate. Publishing an ordinary row-level interval would be cheap but unjustifiably precise.',
        'mistakes': ['Calling a raw respondent average the statewide satisfaction rate after rural oversampling.', 'Treating a missing survey answer as a negative satisfaction response.', 'Computing an ordinary standard error despite a one-branch rural stratum.', 'Dropping branch and selection metadata from the publication packet.'],
        'related': [A + 'stratified-survey-estimate-and-population-weights', A + 'survey-design-variance-and-psu', A + 'confidence-interval-coverage', 'data-science/support-survey-weighting-audit-project', 'data-science/missingness-mechanisms-and-observation-process'],
    },
]

crosslinks = [
    (A + 'hypothesis-test-and-effect-size', A + 'prior-sensitivity-and-effective-information'),
    ('data-science/beta-binomial-updating-and-effective-prior-size', A + 'posterior-predictive-group-check'),
    ('data-science/support-escalation-bayesian-monitoring-project', A + 'helpdesk-escalation-bayesian-project'),
    (A + 'population-estimand-and-sampling-frame', A + 'stratified-survey-estimate-and-population-weights'),
    (A + 'cluster-bootstrap-and-standard-error', A + 'survey-design-variance-and-psu'),
    ('data-science/support-survey-weighting-audit-project', A + 'contact-center-survey-audit-project'),
]

if __name__ == '__main__':
    publish(lessons, [BAYES, SURVEY], crosslinks,
            'aitrove-applied-statistics-bayes-survey-import-20261006.json',
            8415, subject='applied-statistics', hub_path=A + 'applied-statistics-tutorial')
