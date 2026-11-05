"""Add original Data Science lessons on binary outcome measurement error."""
import datetime
import html
import json
import re
import uuid
from pathlib import Path

root = Path(__file__).resolve().parents[1]
fixture = root / 'src/data/fixtures.json'
rows = json.loads(fixture.read_text())
slugs = (
    'outcome-label-validation-subsample-design',
    'outcome-label-sensitivity-and-specificity-by-group',
    'binary-outcome-rate-misclassification-correction',
    'differential-outcome-error-in-group-contrasts',
    'misclassification-assumption-grid-and-decision-range',
    'outcome-label-error-audit-project',
)
new_paths = {'data-science/' + slug for slug in slugs}
rows = [row for row in rows if row['path'] not in new_paths]
by_path = {row['path']: row for row in rows}
stamp = datetime.datetime.now(datetime.UTC).isoformat()
lessons = []

def add(slug, title, summary, sections, code, cost, mistakes, related):
    lessons.append(dict(path='data-science/' + slug, title=title,
                        summary=summary, sections=sections, code=code,
                        cost=cost, mistakes=mistakes, related=related))

add('outcome-label-validation-subsample-design',
    'Design a validation subsample for outcome labels',
    'An outcome-label validation subsample pairs the production label with a more reliable adjudicated label on selected records so classification error can be estimated.', [
    ('Define what the two labels mean', 'A support system flags a ticket as a deadline breach from event logs. An audit team checks the ticket history and policy clock to assign an adjudicated breach label. The latter must follow a written rubric and should be reviewed without knowledge of the desired policy effect. It is a reference process, not a magical error-free truth. Record disagreement reasons, ambiguous cases and adjudicator agreement. [[data-science/proxy-measurement-and-label-error|The proxy-label lesson]] explains how operational labels drift from the intended outcome.'),
    ('Sample across the cells that matter', 'A random sample of tickets may contain too few production-positive cases to estimate false positives or enough tickets from only the largest branch. Stratify by production label and by the policy group or period whose rates will be compared. Fix an inclusion probability for each cell and retain it with every sampled ticket. Oversampling rare flagged tickets is useful for estimating error rates, but raw validation-sample prevalence then does not represent the full population.'),
    ('Keep review independent of downstream effects', 'Do not choose cases because their adjudicated label would make the policy result favorable. Sample IDs before reviewers inspect the ticket. Blind reviewers to treatment or month when practical, while retaining enough information to adjudicate the deadline accurately. A reference process that uses the production flag as its main evidence can reproduce the same mistake. [[data-science/outcome-label-sensitivity-and-specificity-by-group|The error-rate lesson]] needs paired labels from this step.'),
    ('Track selection and missing review', 'A sampled case may be impossible to adjudicate because the audit log is gone. Count such failures by stratum. If unresolved records are concentrated among flagged tickets after the policy launch, complete-case error rates may be biased. The code selects a reproducible number of IDs per production-label and branch cell; it does not solve nonresponse or calculate uncertainty. [[data-science/missing-not-at-random-sensitivity-analysis|Missingness sensitivity]] provides a separate tool.'),
    ('Preserve the sampling ledger', 'Store the frame count, selected count, selection rule, random seed and review status for every cell. To estimate a population quantity from an unequal-probability audit, use the design weights or a suitable likelihood. Do not discard the cell counts after adjudication. [[data-science/stratified-sampling-and-design-weights|Design weighting]] covers the general principle; the later correction lesson uses conditional error rates rather than a naive audit prevalence.')],
    '''from random import Random

def draw_validation_ids(ticket_records, per_cell, seed):
    cells = {}
    for ticket_id, branch_group, production_label in ticket_records:
        if production_label not in (0, 1):
            raise ValueError("production label must be binary")
        cells.setdefault((branch_group, production_label), []).append(ticket_id)
    randomizer = Random(seed)
    selection = []
    for cell, ticket_ids in sorted(cells.items()):
        if len(ticket_ids) < per_cell:
            raise ValueError("cell too small: " + str(cell))
        chosen = randomizer.sample(sorted(ticket_ids), per_cell)
        inclusion_probability = per_cell / len(ticket_ids)
        selection.extend((ticket_id, cell, inclusion_probability)
                         for ticket_id in chosen)
    return selection

records = [(f"N-{label}-{index}", "North", label)
           for label in (0, 1) for index in range(7)]
records += [(f"S-{label}-{index}", "South", label)
            for label in (0, 1) for index in range(9)]
sample = draw_validation_ids(records, per_cell=3, seed=47)
assert len(sample) == 12
assert {probability for _, cell, probability in sample
        if cell[0] == "North"} == {3 / 7}''',
    'For N frame records, cell construction costs O(N) expected time and O(N) space; sorting IDs for reproducible draws costs O(N log N) total in the worst case. Human adjudication and missing audit trails dominate operating cost.',
    ['Do not treat an oversampled validation set as if it were a simple random sample.', 'Do not reveal the desired policy result to adjudicators when it can be withheld.', 'Do not silently remove sampled records that cannot be reviewed.'],
    ['data-science/outcome-label-sensitivity-and-specificity-by-group','data-science/stratified-sampling-and-design-weights','data-science/proxy-measurement-and-label-error','data-science/outcome-label-error-audit-project'])

add('outcome-label-sensitivity-and-specificity-by-group',
    'Estimate outcome-label sensitivity and specificity by group',
    'Outcome-label sensitivity is the share of reference-positive records flagged by production; specificity is the share of reference-negative records left unflagged.', [
    ('Keep the reference label on the correct axis', 'For a deadline-breach flag, a false negative is an adjudicated breach that production missed. A false positive is a production breach flag on an adjudicated nonbreach. Sensitivity divides true production positives by all adjudicated positives. Specificity divides true production negatives by all adjudicated negatives. Precision uses a different denominator and cannot replace either quantity in a rate-correction formula. [[data-science/outcome-label-validation-subsample-design|The validation design]] supplies paired labels.'),
    ('Estimate within meaningful groups', 'If a new routing rule changes logging behavior, the flag may become easier to trigger after launch. Estimate error rates separately for the periods or groups whose breach rates will be contrasted, provided each cell has enough reviewed positives and negatives. Pooling all periods can mask differential error. A group with no adjudicated positive cases has undefined sensitivity, not zero sensitivity. Record the denominator beside every reported proportion.'),
    ('Respect the validation sampling design', 'The fixture computes conditional rates from paired records when sampling is uniform within each adjudicated class. A real audit may stratify on the production label instead. Then an unweighted confusion table can distort sensitivity and specificity; use known inclusion probabilities or a sampling-aware model. The code supports inverse-inclusion weighting for each reviewed record. Those weights do not correct adjudication failures or a biased reference rubric.'),
    ('Do not infer a stable error process from one month', 'A software deployment may change event timestamps and flag behavior. Compare error rates over time, branch and ticket type before applying a pooled estimate. If validation positives are scarce, uncertainty can be large even when the full production dataset has millions of tickets. Extra unreviewed production records do not identify false negatives. [[data-science/differential-outcome-error-in-group-contrasts|Group-specific correction]] makes the consequence visible.'),
    ('Use the rates only for the population they describe', 'Sensitivity and specificity estimated in a high-volume urban queue may not transfer to low-volume queues with manual overrides. A validation sample must cover the target mix or support a transparent model of error differences. A correction based on unsupported cells is extrapolation. [[data-science/binary-outcome-rate-misclassification-correction|The correction lesson]] states the algebra and its assumptions.')],
    '''def weighted_label_accuracy(reviewed_records):
    cells = {"true_positive": 0.0, "false_negative": 0.0,
             "true_negative": 0.0, "false_positive": 0.0}
    for production_label, reference_label, inclusion_probability in reviewed_records:
        if production_label not in (0, 1) or reference_label not in (0, 1):
            raise ValueError("labels must be binary")
        if not 0 < inclusion_probability <= 1:
            raise ValueError("invalid inclusion probability")
        weight = 1 / inclusion_probability
        if reference_label == 1:
            key = "true_positive" if production_label == 1 else "false_negative"
        else:
            key = "true_negative" if production_label == 0 else "false_positive"
        cells[key] += weight
    positives = cells["true_positive"] + cells["false_negative"]
    negatives = cells["true_negative"] + cells["false_positive"]
    if positives == 0 or negatives == 0:
        raise ValueError("both reference classes are needed")
    return (cells["true_positive"] / positives,
            cells["true_negative"] / negatives)

reviewed = ([(1, 1, .5)] * 18 + [(0, 1, .5)] * 2 +
            [(0, 0, .5)] * 37 + [(1, 0, .5)] * 3)
sensitivity, specificity = weighted_label_accuracy(reviewed)
assert abs(sensitivity - .9) < 1e-12
assert abs(specificity - .925) < 1e-12''',
    'For V reviewed records, weighted cell accumulation is O(V) time and O(1) auxiliary space. Precision of the rates depends on reviewed reference-positive and reference-negative counts, not the size of the unreviewed production table.',
    ['Do not substitute precision for sensitivity or specificity.', 'Do not assign a numeric sensitivity when a group has no reviewed positive records.', 'Do not ignore unequal selection probabilities in a stratified audit.'],
    ['data-science/outcome-label-validation-subsample-design','data-science/binary-outcome-rate-misclassification-correction','data-science/differential-outcome-error-in-group-contrasts','data-science/outcome-label-error-audit-project'])

add('binary-outcome-rate-misclassification-correction',
    'Correct a binary outcome rate for label error',
    'When sensitivity and specificity are known for the target population, an observed binary-label rate can be inverted to estimate the underlying outcome rate if their sum exceeds one.', [
    ('Write the observation process first', 'Let q be the fraction of tickets production flags as breaches and p the adjudicated breach fraction in the same population. If production sensitivity is Se and specificity is Sp, then q equals Se times p plus (1 minus Sp) times (1 minus p). Solving gives p = (q + Sp - 1) / (Se + Sp - 1). The identity depends on the error rates applying to this exact ticket population and period. [[data-science/outcome-label-sensitivity-and-specificity-by-group|Validation estimates]] supply Se and Sp.'),
    ('Check whether inversion is possible', 'When Se plus Sp is one, the production flag carries no prevalence information under this model. When their sum is below one, the classifier is worse than its flipped version; the simple positive-orientation correction is not appropriate without reconsidering the label definition. Even with a positive denominator, a proposed pair of error rates can imply p below zero or above one for the observed q. That is an incompatible assumption set, not a value to silently clip.'),
    ('Use the same population for every quantity', 'A production rate for September cannot safely be corrected with error rates measured only in February after a logging rewrite. Match ticket eligibility, branch, time and reference-label rubric. A validation sample selected on production label needs design-aware error rates. The correction yields an estimated descriptive rate, not a causal policy effect and not a confidence interval. [[data-science/differential-outcome-error-in-group-contrasts|Group contrasts]] need separate care.'),
    ('Understand why the change can be large', 'When breaches are rare, a small false-positive rate can form a substantial share of observed positives. In the fixture, q is 0.18, Se is 0.90 and Sp is 0.95; the corrected p is about 0.153. A one-point change in assumed specificity may move p more than a one-point change in sensitivity. Inspect a plausible range rather than fixating on one estimate. [[data-science/misclassification-assumption-grid-and-decision-range|The assumption grid]] does that.'),
    ('Carry uncertainty separately', 'The equation treats Se and Sp as fixed inputs, but validation estimates have sampling uncertainty, and q does too. A formal interval would propagate all three quantities and any dependence from an internal validation sample. The code intentionally only checks the algebra and feasibility. A corrected point rate with many decimal places can mislead when the audit sample contains few reference positives.')],
    '''def corrected_binary_rate(observed_rate, sensitivity, specificity):
    if not all(0 <= value <= 1 for value in
               (observed_rate, sensitivity, specificity)):
        raise ValueError("rates must lie between zero and one")
    information = sensitivity + specificity - 1
    if information <= 0:
        raise ValueError("uninformative or reversed label process")
    corrected = (observed_rate + specificity - 1) / information
    if not 0 <= corrected <= 1:
        raise ValueError("observed rate incompatible with assumptions")
    return corrected

production_breach_rate = .18
estimated_true_rate = corrected_binary_rate(production_breach_rate, .90, .95)
assert abs(estimated_true_rate - (.13 / .85)) < 1e-12
assert estimated_true_rate < production_breach_rate''',
    'One inversion is O(1) time and space. Estimating group-specific accuracy and propagating validation uncertainty dominate the workflow. The correction is numerically unstable when sensitivity plus specificity approaches one.',
    ['Do not clip an infeasible corrected rate into the valid range.', 'Do not reuse error rates from a different population without a transport argument.', 'Do not call a point correction an uncertainty interval or a causal effect.'],
    ['data-science/outcome-label-sensitivity-and-specificity-by-group','data-science/differential-outcome-error-in-group-contrasts','data-science/misclassification-assumption-grid-and-decision-range','data-science/outcome-label-error-audit-project'])

add('differential-outcome-error-in-group-contrasts',
    'Differential outcome-label error in group contrasts',
    'When outcome-label accuracy differs between groups or periods, correct each group’s observed rate under its own supported error model before comparing rates.', [
    ('Identify the route by which error differs', 'A routing policy may add a timestamp event that improves breach detection only in treated branches. Alternatively, a logging outage may miss late tickets in one branch. Either mechanism can change sensitivity or specificity at the same time as treatment. A raw difference in production flags then mixes the outcome difference with measurement differences. [[data-science/outcome-label-validation-subsample-design|The validation sample]] must cover the comparison groups and relevant dates.'),
    ('Correct cells before subtracting', 'Apply the binary-rate inversion separately to treated and comparison groups, using accuracy estimates for each group. The example has observed rates 0.12 and 0.18. Under the stated group-specific sensitivity and specificity, the corrected gap is much smaller than the raw -0.06 rate-point gap. This does not prove which gap is causal; it illustrates how a measured contrast changes under explicit error assumptions. [[data-science/binary-outcome-rate-misclassification-correction|The rate correction]] gives the formula.'),
    ('Do not assume error always biases toward zero', 'The direction depends on outcome prevalence and the pattern of false positives and false negatives across groups. Better recording in the treated group can make a true improvement look smaller or even reverse its apparent sign. A single pooled sensitivity and specificity pair may hide that mechanism. An audit must compare accuracy estimates with denominators and uncertainty, not just inspect the overall classification score.'),
    ('Keep causal design separate', 'Correcting labels does not solve confounding, spillovers, selection into treatment or different untreated trends. A before/after or treated/control contrast still needs its own identification argument. If the policy itself changes the meaning of eligible ticket, even group-specific sensitivity and specificity may not restore a common estimand. [[data-science/cohort-time-difference-in-differences|The rollout design]] addresses time and group comparison assumptions.'),
    ('Report unsupported cells honestly', 'If the reference audit contains no comparison-group breaches, sensitivity for that group cannot be estimated. Do not borrow the treated-group rate silently. One can show scenario values with explicit assumptions, collect more adjudications or decline to correct the contrast. [[data-science/misclassification-assumption-grid-and-decision-range|The assumption grid]] makes scenario dependence visible.')],
    '''def corrected_rate(observed, sensitivity, specificity):
    denominator = sensitivity + specificity - 1
    if not 0 <= observed <= 1 or not 0 <= sensitivity <= 1 or not 0 <= specificity <= 1:
        raise ValueError("invalid probability")
    if denominator <= 0:
        raise ValueError("error process cannot be inverted")
    answer = (observed + specificity - 1) / denominator
    if not 0 <= answer <= 1:
        raise ValueError("incompatible error assumptions")
    return answer

treated_observed = .12
comparison_observed = .18
treated_corrected = corrected_rate(treated_observed, .84, .98)
comparison_corrected = corrected_rate(comparison_observed, .94, .95)
raw_gap = treated_observed - comparison_observed
adjusted_gap = treated_corrected - comparison_corrected
assert abs(raw_gap - (-.06)) < 1e-12
assert adjusted_gap < 0 and abs(adjusted_gap) < abs(raw_gap)''',
    'For G groups, independent point corrections cost O(G) time and O(G) output space. Group-by-period validation and uncertainty propagation may need many adjudicated records; more production rows do not replace missing reference labels.',
    ['Do not assume nondifferential error merely because the same flag name appears in both groups.', 'Do not claim the corrected contrast is causal without a valid comparison design.', 'Do not borrow accuracy estimates across unsupported groups without stating the assumption.'],
    ['data-science/binary-outcome-rate-misclassification-correction','data-science/outcome-label-sensitivity-and-specificity-by-group','data-science/misclassification-assumption-grid-and-decision-range','data-science/outcome-label-error-audit-project'])

add('misclassification-assumption-grid-and-decision-range',
    'Misclassification assumption grids and decision ranges',
    'An assumption grid recalculates an outcome contrast across a prespecified set of plausible sensitivity and specificity values and reports where the decision changes.', [
    ('Make uncertainty in error rates visible', 'A small validation audit rarely pins down sensitivity and specificity to one exact value. Build plausible ranges from the audit and operational knowledge, separately for groups whose logging differs. Freeze the grid before examining which cell best supports a favored policy. Each cell is a scenario, not a posterior draw or a confidence bound. [[data-science/outcome-label-sensitivity-and-specificity-by-group|The validation lesson]] explains where the central rates come from.'),
    ('Reject impossible cells explicitly', 'For every sensitivity-specificity pair, invert the observed rate. If the sum is at most one or the implied true rate lies outside zero to one, mark the cell invalid; do not clip it and include it in the range. The code loops over declared assumptions for two groups and retains only compatible combinations. The resulting minimum and maximum adjusted gaps describe the evaluated assumption set only. They are not an identified interval unless that set is defensibly exhaustive.'),
    ('Connect the range to an action threshold', 'Suppose a queue rollout requires at least a three-point reduction in true breach rate to justify cost. Count scenarios where the adjusted treated-minus-comparison gap is at most -0.03. If the action changes across plausible assumptions, prioritize a better validation audit or a narrower rollout. Do not average scenario outputs without explicit weights for the assumptions. [[data-science/sensitivity-analysis-and-decision-stability|Decision stability]] covers the broader principle.'),
    ('Do not omit sampling uncertainty', 'This grid varies assumed accuracy but holds observed rates fixed. In a formal probabilistic bias analysis, validation and production sampling uncertainty would be propagated too, with care for dependence from an internal validation sample. A coarse grid can miss a decision boundary between selected values. Increase resolution around the boundary, but disclose the revised grid and reason. [[data-science/differential-outcome-error-in-group-contrasts|Group-specific correction]] is the calculation inside each cell.'),
    ('Keep the failure stories separate', 'A result stable to label error can still fail because of confounding or a contaminated comparison group. Conversely, weak label validation can dominate even an otherwise careful study. Show the raw contrast, central corrected contrast, scenario range, invalid-cell count and action threshold together. [[data-science/outcome-label-error-audit-project|The audit project]] turns these into a review packet.')],
    '''from itertools import product

def corrected_rate(observed, sensitivity, specificity):
    if not all(0 <= value <= 1 for value in
               (observed, sensitivity, specificity)):
        return None
    information = sensitivity + specificity - 1
    if information <= 0:
        return None
    rate = (observed + specificity - 1) / information
    return rate if 0 <= rate <= 1 else None

def contrast_assumption_grid(treated_observed, comparison_observed,
                             treated_options, comparison_options, action_gap):
    gaps = []
    invalid = 0
    for treated_error, comparison_error in product(treated_options, comparison_options):
        treated_rate = corrected_rate(treated_observed, *treated_error)
        comparison_rate = corrected_rate(comparison_observed, *comparison_error)
        if treated_rate is None or comparison_rate is None:
            invalid += 1
            continue
        gaps.append(treated_rate - comparison_rate)
    if not gaps:
        raise ValueError("no compatible assumptions")
    return {"range": (min(gaps), max(gaps)),
            "action_scenarios": sum(gap <= action_gap for gap in gaps),
            "valid_scenarios": len(gaps), "invalid_scenarios": invalid}

treated_errors = [(.82, .97), (.88, .99)]
comparison_errors = [(.91, .94), (.96, .97)]
audit = contrast_assumption_grid(.12, .18, treated_errors,
                                 comparison_errors, action_gap=-.03)
assert audit["valid_scenarios"] == 4
assert audit["invalid_scenarios"] == 0
assert audit["range"][0] <= audit["range"][1]''',
    'With T treated and C comparison assumption pairs, direct evaluation costs O(T × C) time and O(T × C) space for retained gaps. A formal uncertainty model has additional sampling and simulation cost; grid size alone does not establish validity.',
    ['Do not label a handpicked scenario range a confidence interval.', 'Do not include clipped or otherwise infeasible corrected rates.', 'Do not average scenarios without declared weights or probabilities.'],
    ['data-science/binary-outcome-rate-misclassification-correction','data-science/differential-outcome-error-in-group-contrasts','data-science/sensitivity-analysis-and-decision-stability','data-science/outcome-label-error-audit-project'])

add('outcome-label-error-audit-project',
    'Project: audit a deadline-breach outcome label',
    'Build a review packet that tests whether a production breach flag changes meaning across a policy comparison and how that uncertainty changes the decision.', [
    ('Specify the measurement target', 'The target is whether a ticket truly breached its contracted deadline under a frozen eligibility rule. Production derives a flag from event timestamps; adjudicators reconstruct a reference label from the contract and ticket history. Record known ambiguity, clock changes and missing logs. A code value alone is not the outcome definition. [[data-science/proxy-measurement-and-label-error|The label-design lesson]] provides the starting point.'),
    ('Draw a reviewable validation sample', 'Build a ticket frame by branch, period and production label. Sample within those cells using a recorded seed and inclusion probability. Review positive and negative production flags; otherwise false positives or false negatives will be unobservable. Preserve nonadjudicated cases as a separate status rather than dropping them. [[data-science/outcome-label-validation-subsample-design|The sampling lesson]] gives a reproducible draw.'),
    ('Estimate and compare error rates', 'Calculate sensitivity and specificity with the sampling design accounted for, and show reviewed reference-positive and reference-negative denominators. Split groups or periods if routing changes logging. If any required cell lacks reference positives or negatives, mark its rate unsupported. Report raw production rates, corrected descriptive rates and the corrected contrast without claiming the measurement correction solves treatment selection. [[data-science/differential-outcome-error-in-group-contrasts|The group-contrast lesson]] explains that boundary.'),
    ('Stress the decision with declared assumptions', 'Set plausible sensitivity and specificity ranges from validation uncertainty and operational changes. Reject incompatible combinations. Compare the adjusted gap range with a policy threshold, and retain the invalid-cell count. If the sign or action changes, recommend more adjudication in the cells that most affect the result. [[data-science/misclassification-assumption-grid-and-decision-range|The grid lesson]] shows the scenario calculation.'),
    ('Deliver an evidence packet, not a green stamp', 'The code below checks for the artifacts needed for review; it does not compute a valid causal interval. Include the adjudication rubric, sample ledger, unresolved cases, group-specific error tables, raw and corrected rates, decision scenarios, and a separate causal-design note. If the reference process changed mid-study or a group has no validation support, stop at a scenario statement. [[data-science/outcome-label-sensitivity-and-specificity-by-group|Error-rate support]] is essential.')],
    '''def label_error_packet_gate(packet):
    required = {"rubric", "sampling_ledger", "review_status",
                "group_error_tables", "raw_rates", "corrected_rates",
                "assumption_grid", "causal_design_note"}
    missing = sorted(required - set(packet))
    if missing:
        raise ValueError("missing review artifacts: " + ", ".join(missing))
    if not packet["sampling_ledger"] or not packet["group_error_tables"]:
        raise ValueError("validation support is absent")
    reviewed = sum(cells["reference_positive"] + cells["reference_negative"]
                   for cells in packet["group_error_tables"].values())
    if reviewed != packet["review_status"]["complete"]:
        raise ValueError("review counts disagree")
    unsupported = sorted(group for group, cells in
                         packet["group_error_tables"].items()
                         if cells["reference_positive"] == 0 or
                         cells["reference_negative"] == 0)
    return {"packet_complete": True,
            "all_groups_supported": not unsupported,
            "unsupported_groups": unsupported}

packet = {"rubric": "contract clock v3",
          "sampling_ledger": [f"T-{ticket_number}" for ticket_number in range(73)],
          "review_status": {"complete": 73, "unresolved": 0},
          "group_error_tables": {"North": {"reference_positive": 13,
                                            "reference_negative": 32},
                                 "South": {"reference_positive": 0,
                                           "reference_negative": 28}},
          "raw_rates": {"North": .12, "South": .18},
          "corrected_rates": {"North": .13},
          "assumption_grid": {"valid_scenarios": 4},
          "causal_design_note": "comparison trends require separate review"}
review = label_error_packet_gate(packet)
assert review == {"packet_complete": True,
                  "all_groups_supported": False,
                  "unsupported_groups": ["South"]}''',
    'The gate scans A artifact keys and G groups in O(A + G) expected time and O(G) output space. Adjudication, especially of rare reference-positive cases, is the substantial resource cost. A complete packet makes limitations visible; it does not certify the effect.',
    ['Do not declare an unsupported group corrected because another group has validation data.', 'Do not drop unresolved adjudications without reporting their pattern.', 'Do not treat label correction as a replacement for causal-design review.'],
    ['data-science/outcome-label-validation-subsample-design','data-science/outcome-label-sensitivity-and-specificity-by-group','data-science/binary-outcome-rate-misclassification-correction','data-science/differential-outcome-error-in-group-contrasts','data-science/misclassification-assumption-grid-and-decision-range'])

assert len(lessons) == len(new_paths) == 6
titles = {path: row['title'] for path, row in by_path.items()}
titles.update({item['path']: item['title'] for item in lessons})

def prose(value):
    return re.sub(r'\[\[([^|]+)\|([^\]]+)\]\]',
                  lambda match: '<a href="/' + match[1] + '">' + match[2] + '</a>',
                  html.escape(value))

def links(targets):
    return '<ul>' + ''.join('<li><a href="/' + target + '">' + html.escape(titles[target]) + '</a></li>'
                            for target in targets) + '</ul>'

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
               difficulty='Advanced', tags=['ai-data', 'data-science'], potd_date=None,
               featured=False, sort_order=13900 + index, status='published', published_at=stamp,
               created_at=stamp, updated_at=stamp,
               data={'subject_root':root_path,
                     'section_path':project_hub_path if is_project else root_path,
                     'content_format':'html', 'seo_ready':True,
                     'kind':'project' if is_project else 'tutorial',
                     'reading_minutes':max(5, len(re.sub(r'<[^>]+>', ' ', body).split()) // 180),
                     'author_path':'authors/aitrove-editorial',
                     'verification_suite':'Editorial, code and internal-link checks',
                     'related':[{'path':target, 'title':titles[target]} for target in item['related']]})
    rows.append(row)
    by_path[path] = row

tutorial_paths = ['data-science/' + slug for slug in slugs[:5]]
project_path = 'data-science/' + slugs[-1]
hub = by_path[root_path]
module_title = 'Outcome-label error and validation'
if not any(module['title'] == module_title for module in hub['data']['modules']):
    hub['data']['modules'].insert(-1, {'title':module_title,
                                      'summary':'Design a reference audit, estimate group-specific label error and stress-test the decision.',
                                      'lessons':tutorial_paths})
apply_module = next(module for module in hub['data']['modules'] if module['title'] == 'Apply your knowledge')
if project_path not in apply_module['lessons']:
    apply_module['lessons'].append(project_path)
if '<h2>' + module_title + '</h2>' not in hub['body']:
    hub['body'] += '<h2>' + module_title + '</h2>' + links(tutorial_paths)
    hub['body'] += '<h2>Outcome-label error audit</h2>' + links([project_path])
hub['updated_at'] = stamp

project_hub = by_path[project_hub_path]
if project_path not in project_hub['data']['modules'][0]['lessons']:
    project_hub['data']['modules'][0]['lessons'].append(project_path)
if '<h2>Outcome-label error audit</h2>' not in project_hub['body']:
    project_hub['body'] += '<h2>Outcome-label error audit</h2>' + links([project_path])
project_hub['updated_at'] = stamp

for source, target in [
    ('data-science/proxy-measurement-and-label-error', tutorial_paths[0]),
    ('data-science/stratified-sampling-and-design-weights', tutorial_paths[1]),
    ('data-science/support-handoff-survey-measurement-project', tutorial_paths[2]),
    ('data-science/cohort-time-difference-in-differences', tutorial_paths[3]),
    ('data-science/sensitivity-analysis-and-decision-stability', tutorial_paths[4]),
    ('data-science/interrupted-series-policy-review-project', project_path),
]:
    source_row = by_path[source]
    anchor = '<p><strong>Continue the workflow:</strong> <a href="/' + target + '">' + html.escape(titles[target]) + '</a>.</p>'
    if anchor not in source_row['body']:
        source_row['body'] += anchor
        source_row['data'].setdefault('related', []).append({'path':target, 'title':titles[target]})
        source_row['updated_at'] = stamp

assert len({row['path'] for row in rows}) == len(rows)
fixture.write_text(json.dumps(rows, ensure_ascii=False, indent=2) + '\n')
print(json.dumps({'new_articles':len(lessons), 'new_projects':1, 'crosslinks_from_existing':6}))
