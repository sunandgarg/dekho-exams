"""Add original Data Science lessons on bounded outcomes and attrition."""
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
    'partial-identification-and-the-assumption-ledger',
    'worst-case-bounds-for-missing-binary-outcomes',
    'treatment-effect-bounds-under-differential-attrition',
    'bounded-missing-outcome-risk-scenarios',
    'decision-thresholds-and-follow-up-value-under-bounds',
    'attrition-bounds-policy-decision-project',
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

add('partial-identification-and-the-assumption-ledger',
    'Partial identification and an assumption ledger',
    'Partial identification reports the range of parameter values consistent with observed data and stated assumptions when the data cannot support one point value.', [
    ('Name the estimand before the interval', 'A queue experiment assigns branches to a new routing policy. The target is the difference in deadline-breach probability between assigned groups for every eligible ticket, including tickets whose final outcome was not captured. A responder-only difference targets a different population unless missingness is justified. Write down treatment assignment, outcome window, eligible denominator and the sign of benefit before computing any range. [[causal-inference/estimand-and-counterfactual-unit|The estimand lesson]] separates the policy question from its estimator.'),
    ('Distinguish three kinds of uncertainty', 'An identification interval reflects what the observed data and assumptions permit even with arbitrarily many similar observations. A confidence interval reflects sampling variability around a parameter or bound. A scenario range reflects selected assumptions that may not exhaust all possibilities. They are not interchangeable. The code below records a lower and upper value with its assumption label; it does not supply a statistical confidence level. [[data-science/worst-case-bounds-for-missing-binary-outcomes|Worst-case outcome bounds]] give a concrete construction.'),
    ('Build the assumption ledger', 'For every tightening step, record the outcome support, missing-outcome rule, assignment mechanism, any restriction on missing-ticket risk, and the population to which it applies. A binary breach indicator has known support zero to one. That alone limits how much missing tickets can change a rate. Claiming missing tickets behave like observed tickets is much stronger and needs evidence. Keep those assumptions as separate rows rather than burying them in code.'),
    ('Let wide bounds carry information', 'A range crossing zero may be operationally unsatisfying, but it reveals that the available outcome data cannot settle the sign under the current assumptions. Filling missing tickets with a convenient value would hide this limitation. An honest wide range can motivate targeted log recovery or a validation audit. [[data-science/decision-thresholds-and-follow-up-value-under-bounds|The decision lesson]] shows when a narrower range would matter.'),
    ('Do not promote design bounds into causal identification', 'If branches chose their own policy status, worst-case missing-outcome bounds on each observed group rate still do not remove selection bias. Random assignment, a defended comparison trend, or another identification design must support the treatment contrast. The code enforces ordered numeric endpoints only; the substantive ledger explains why those endpoints are valid. [[data-science/treatment-effect-bounds-under-differential-attrition|The attrition contrast]] assumes a valid assignment design.')],
    '''def identification_record(estimand, lower, upper, assumptions):
    if not estimand or not assumptions:
        raise ValueError("estimand and assumptions are required")
    if lower > upper:
        raise ValueError("bounds are reversed")
    return {"estimand": estimand, "lower": lower, "upper": upper,
            "assumptions": tuple(assumptions),
            "sign_identified": lower > 0 or upper < 0}

record = identification_record(
    "assigned-policy minus control breach probability",
    lower=-.14, upper=.06,
    assumptions=("binary outcome", "valid branch assignment",
                 "unobserved outcomes may be zero or one"))
assert record["lower"] <= 0 <= record["upper"]
assert record["sign_identified"] is False''',
    'Recording one interval is O(A) time and space for A assumption strings. Computing credible bounds can be more involved; the main cost is recovering the population frame, outcome status and design evidence needed to justify the ledger.',
    ['Do not label an identification interval a 95% confidence interval.', 'Do not claim a causal bound from a self-selected comparison without a causal design.', 'Do not suppress a wide interval simply because it crosses the action threshold.'],
    ['data-science/worst-case-bounds-for-missing-binary-outcomes','data-science/treatment-effect-bounds-under-differential-attrition','data-science/decision-thresholds-and-follow-up-value-under-bounds','data-science/attrition-bounds-policy-decision-project'])

add('worst-case-bounds-for-missing-binary-outcomes',
    'Worst-case bounds for missing binary outcomes',
    'For a binary outcome, the full-population event rate lies between observed events divided by all eligible units and observed events plus missing outcomes divided by all eligible units.', [
    ('Keep the full eligible denominator', 'A branch has 87 eligible tickets. The deadline result is known for 72; 19 of those breached. The other 15 outcomes are unavailable because one event stream failed. If every missing ticket avoided a breach, the overall rate is 19/87. If every missing ticket breached, it is 34/87. The observed-case rate 19/72 is neither endpoint and should not be labeled the full-branch rate. [[data-science/partial-identification-and-the-assumption-ledger|The assumption ledger]] names the binary support behind the bound.'),
    ('Recognize what makes the bounds valid', 'The result needs a complete eligibility frame, correct observed labels and a binary outcome that must be zero or one for every eligible unit. If missing tickets could have been excluded under the frozen policy, eligibility itself is uncertain and the simple formula does not solve that problem. If outcome labels are wrong, add a separate measurement-error analysis. [[data-science/outcome-label-error-audit-project|The label-error project]] covers that failure route.'),
    ('Do not assume randomness of missingness', 'The bounds remain valid whether lost outcomes are mostly successes, mostly failures or selectively absent after a system outage, as long as the listed support and frame hold. They often become wide when many outcomes are missing. That width is the price of declining an unsupported missing-at-random assumption, not a flaw in the arithmetic. If all outcomes are observed, both endpoints coincide at the observed rate.'),
    ('Report loss as a count and a fraction', 'Show 15/87 missing alongside the bounds. A one-point interval in a huge trial and a one-point interval in a tiny branch have different sampling uncertainty even if their identification widths match. The code works from counts; it does not produce a confidence interval for the endpoints. [[data-science/treatment-effect-bounds-under-differential-attrition|The group contrast]] combines two such intervals when assignment supports a comparison.'),
    ('Use added information to tighten, not disguise', 'If operations recover outcomes for six of the missing tickets, update observed events and reduce the missing count. Each recovered binary outcome narrows the worst-case rate interval by 1/87, regardless of whether that ticket breached. The center may move in either direction. This points to a concrete data-collection plan instead of filling missing cells from an arbitrary average.')],
    '''def binary_rate_bounds(eligible, observed, observed_events):
    if not (isinstance(eligible, int) and isinstance(observed, int)
            and isinstance(observed_events, int)):
        raise ValueError("counts must be integers")
    if eligible <= 0 or not 0 <= observed_events <= observed <= eligible:
        raise ValueError("inconsistent outcome counts")
    missing = eligible - observed
    return observed_events / eligible, (observed_events + missing) / eligible

lower, upper = binary_rate_bounds(eligible=87, observed=72,
                                  observed_events=19)
assert abs(lower - 19 / 87) < 1e-12
assert abs(upper - 34 / 87) < 1e-12
assert abs((upper - lower) - 15 / 87) < 1e-12''',
    'The bound calculation is O(1) time and space after counts are available. Building and validating the eligibility frame is O(N) over N units; log recovery can dominate the entire analysis.',
    ['Do not divide observed events by observed tickets when reporting a bound for all eligible tickets.', 'Do not present worst-case endpoints as confidence limits.', 'Do not treat an uncertain eligibility frame as a solved missing-outcome problem.'],
    ['data-science/partial-identification-and-the-assumption-ledger','data-science/treatment-effect-bounds-under-differential-attrition','data-science/bounded-missing-outcome-risk-scenarios','data-science/attrition-bounds-policy-decision-project'])

add('treatment-effect-bounds-under-differential-attrition',
    'Treatment-effect bounds under differential attrition',
    'With a valid assignment design and binary outcomes missing in each arm, an effect interval subtracts the largest possible control rate from the smallest possible treated rate, and vice versa.', [
    ('Define the direction of the effect', 'Let the outcome be a deadline breach, where lower is better. The effect is assigned-policy breach probability minus control breach probability. A negative number favors the policy. Among 50 assigned-policy tickets, 40 outcomes are known and 15 breached. Among 50 control tickets, 45 outcomes are known and 20 breached. The missing counts differ, so comparing 15/40 with 20/45 conditions on two selected responder sets. [[data-science/worst-case-bounds-for-missing-binary-outcomes|The rate-bounds lesson]] keeps both full denominators.'),
    ('Combine group endpoints correctly', 'The treated rate lies from 0.30 to 0.50. The control rate lies from 0.40 to 0.50. Therefore the treated-minus-control effect lies from -0.20 to +0.10. The lower effect pairs the smallest treated rate with the largest control rate; the upper pairs the largest treated rate with the smallest control rate. Using lower minus lower would omit feasible outcomes and understate uncertainty. The code computes and checks this ordering.'),
    ('Keep assignment and interference assumptions visible', 'The difference of group risks can represent an assignment effect only when assignment supports exchangeability for the eligible units, treatment is defined consistently and spillovers are handled. These missing-outcome bounds do not repair confounding in a management-selected rollout. If the trial assigns branches, not tickets, sampling uncertainty belongs at the branch level even though the arithmetic uses ticket counts. [[data-science/assignment-aware-permutation-test-for-branches|Assignment-aware inference]] treats that unit distinction.'),
    ('Interpret the zero crossing', 'Because the interval contains zero, the observed outcomes and binary support alone do not determine whether the policy helped. This is not a null-hypothesis result or a p-value. A narrow conventional confidence interval fitted only to observed tickets would answer a different, stronger-assumption question. Show both the endpoint counts and the interval so reviewers can see why the sign remains unresolved.'),
    ('Choose a defensible next constraint', 'Operational evidence might bound breach risk among missing tickets instead of allowing the entire zero-to-one range. Such a restriction narrows the interval only to the extent it is credible. [[data-science/bounded-missing-outcome-risk-scenarios|The scenario lesson]] calculates that narrower range, while [[data-science/decision-thresholds-and-follow-up-value-under-bounds|the decision lesson]] translates an interval into a policy action.')],
    '''def arm_rate_bounds(assigned, observed, breaches):
    if assigned <= 0 or not 0 <= breaches <= observed <= assigned:
        raise ValueError("inconsistent arm counts")
    missing = assigned - observed
    return breaches / assigned, (breaches + missing) / assigned

def effect_bounds(treated_counts, control_counts):
    treated_low, treated_high = arm_rate_bounds(*treated_counts)
    control_low, control_high = arm_rate_bounds(*control_counts)
    return treated_low - control_high, treated_high - control_low

treated = (50, 40, 15)
control = (50, 45, 20)
lower_effect, upper_effect = effect_bounds(treated, control)
assert abs(lower_effect - (-.20)) < 1e-12
assert abs(upper_effect - .10) < 1e-12''',
    'Given arm counts, interval arithmetic is O(1) time and space. Validating unit-level assignment, missingness and outcome status requires a scan of the underlying study frame; dependence-aware sampling uncertainty is a separate analysis.',
    ['Do not subtract matching endpoints when bounding a difference.', 'Do not use ticket-level precision when branches were assigned.', 'Do not call an effect interval causal if treatment groups were self-selected.'],
    ['data-science/worst-case-bounds-for-missing-binary-outcomes','data-science/bounded-missing-outcome-risk-scenarios','data-science/assignment-aware-permutation-test-for-branches','data-science/attrition-bounds-policy-decision-project'])

add('bounded-missing-outcome-risk-scenarios',
    'Bounded missing-outcome risk scenarios',
    'A missing-outcome risk restriction narrows worst-case bounds by assigning a credible lower and upper event fraction to the missing units in each group.', [
    ('State the restriction as a rate', 'Suppose 10 assigned-policy outcomes are missing. Rather than pretend none or all breached, an audit of similar outage tickets may support a missing-ticket breach fraction between 0.20 and 0.60. For five missing control outcomes, a separate range from 0.10 to 0.40 may be plausible. These are assumptions about missing units, not observed rates and not probabilities assigned to particular records. Keep the rationale and population match in the ledger. [[data-science/partial-identification-and-the-assumption-ledger|The ledger lesson]] distinguishes observed facts from restrictions.'),
    ('Calculate arm bounds before the contrast', 'The treated group has 15 observed breaches among 50 assigned and 10 missing. Its rate lies between (15 + 10 × 0.20)/50 = 0.34 and (15 + 10 × 0.60)/50 = 0.42. The control group has 20 observed breaches, five missing, and risk range 0.10 to 0.40, yielding 0.41 to 0.44. The treated-minus-control contrast lies between -0.10 and +0.01. It still crosses zero. [[data-science/treatment-effect-bounds-under-differential-attrition|The worst-case contrast]] was wider.'),
    ('Do not confuse plausible with identified', 'The observed data do not verify that missing tickets have those risk ranges. A validation sample drawn from a different outage or branch may not transfer. If the imposed ranges exclude a realistic failure mode, the narrow interval is false reassurance. Show the unrestricted result alongside the restricted result, with the rule that made each endpoint smaller. The code rejects risk ranges outside zero to one and inconsistent arm counts.'),
    ('Preserve group-specific missingness', 'Applying one missing-risk range to both groups may be unjustified if policy launch changes logging or ticket mix. Conversely, inventing different ranges solely to obtain a preferred effect is equally weak. Use process logs, recovered ticket samples and domain constraints to motivate each arm. [[data-science/missing-not-at-random-sensitivity-analysis|Missing-not-at-random sensitivity]] examines a related problem using model-based shifts.'),
    ('Propagate further uncertainty separately', 'The scenario interval is conditional on exact counts and fixed risk restrictions. It is not a statistical confidence interval and does not account for small-sample variation in the observed breaches. If a random sample of missing outcomes is recovered, the plausible ranges can be re-estimated with uncertainty, but the selection mechanism of that recovery sample must be documented. [[data-science/decision-thresholds-and-follow-up-value-under-bounds|The decision lesson]] checks whether the remaining range matters.')],
    '''def risk_restricted_rate(assigned, observed, breaches, missing_risk):
    low_risk, high_risk = missing_risk
    if assigned <= 0 or not 0 <= breaches <= observed <= assigned:
        raise ValueError("inconsistent arm counts")
    if not 0 <= low_risk <= high_risk <= 1:
        raise ValueError("invalid missing-outcome risk range")
    missing = assigned - observed
    return ((breaches + missing * low_risk) / assigned,
            (breaches + missing * high_risk) / assigned)

treated = risk_restricted_rate(50, 40, 15, (.20, .60))
control = risk_restricted_rate(50, 45, 20, (.10, .40))
effect = (treated[0] - control[1], treated[1] - control[0])
assert all(abs(actual - expected) < 1e-12
           for actual, expected in zip(treated, (.34, .42)))
assert all(abs(actual - expected) < 1e-12
           for actual, expected in zip(control, (.41, .44)))
assert all(abs(actual - expected) < 1e-12
           for actual, expected in zip(effect, (-.10, .01)))''',
    'Two-arm bound evaluation is O(1) time and space. A grid over K plausible risk-range pairs costs O(K). Establishing credible restrictions through audits and preserving a sampling design is more expensive than the interval arithmetic.',
    ['Do not label an assumption-dependent range a confidence interval.', 'Do not choose missing-risk values after inspecting which ones favor the rollout.', 'Do not silently use the observed-case risk as the missing-case risk.'],
    ['data-science/treatment-effect-bounds-under-differential-attrition','data-science/missing-not-at-random-sensitivity-analysis','data-science/decision-thresholds-and-follow-up-value-under-bounds','data-science/attrition-bounds-policy-decision-project'])

add('decision-thresholds-and-follow-up-value-under-bounds',
    'Decision thresholds and follow-up value under bounds',
    'A bounded effect supports an action only when every effect in the defensible interval falls on the same side of the decision threshold; otherwise additional outcome recovery may change the choice.', [
    ('Put the cost threshold on the effect scale', 'A routing policy costs 3,200 units for the planned period, covers 2,000 tickets, and a prevented breach is worth 80 units. It breaks even if the breach-rate effect is at most -0.02: a two-point reduction prevents an expected 40 breaches, worth 3,200. This is a decision threshold, not a claim about the true effect. [[data-science/treatment-effect-bounds-under-differential-attrition|The effect-bound lesson]] defines the sign convention.'),
    ('Map the interval to net value', 'If the effect may lie between -0.10 and +0.01, the possible net value runs from -4,800 to +12,800 units under this simple linear value model. The lower net value uses the least favorable effect, because a positive breach effect adds harm. The result is unresolved against a zero-net-value rule. Do not report the midpoint as an expected value; no probabilities over the interval were supplied. The code returns approve, reject or unresolved from endpoint comparisons.'),
    ('Quantify what follow-up can remove', 'For an arm with N assigned and M missing binary outcomes, the unrestricted rate interval has width M/N. Recovering one missing outcome reduces that width by exactly 1/N, whatever its observed value. In a two-arm effect interval, recovering four treated outcomes when N is 50 shrinks the total width by 0.08. Its position can shift depending on those four outcomes. This is a width calculation, not a guarantee that the sign or policy choice will become clear.'),
    ('Choose records for information and feasibility', 'If both arms have equal denominators, each recovered ticket reduces worst-case width equally, but tickets may differ in audit cost or the chance their logs still exist. With unequal denominators, a recovered ticket in the smaller arm changes width more. Prioritize recoverable missing records that also help evaluate whether missingness differs by group. Do not audit only apparent successes or only the branch with a politically useful result. [[data-science/worst-case-bounds-for-missing-binary-outcomes|The single-rate lesson]] shows the width identity.'),
    ('Do not confuse a bound with a final decision mandate', 'Other constraints may matter: staffing capacity, equity, customer harm and the ability to reverse rollout. The rule below is deliberately narrow and uses a specified linear value model. If a defensible interval straddles the threshold, report the unresolved region and the feasible follow-up plan. [[data-science/attrition-bounds-policy-decision-project|The project]] gathers the data and decision assumptions in one packet.')],
    '''def decision_from_effect_bounds(effect_low, effect_high,
                                ticket_volume, value_per_prevented, policy_cost):
    if effect_low > effect_high or ticket_volume <= 0:
        raise ValueError("invalid effect range or volume")
    if value_per_prevented <= 0 or policy_cost < 0:
        raise ValueError("invalid value inputs")
    net_low = -effect_high * ticket_volume * value_per_prevented - policy_cost
    net_high = -effect_low * ticket_volume * value_per_prevented - policy_cost
    if net_low > 0:
        action = "approve under stated bounds"
    elif net_high < 0:
        action = "reject under stated bounds"
    else:
        action = "unresolved"
    return net_low, net_high, action

net_low, net_high, action = decision_from_effect_bounds(
    -.10, .01, 2000, 80, 3200)
assert abs(net_low - (-4800)) < 1e-12
assert abs(net_high - 12800) < 1e-12
assert action == "unresolved"
assert abs(4 / 50 - .08) < 1e-12''',
    'The endpoint decision rule is O(1) time and space. Recovering K missing outcomes costs O(K) data review, while recalculating arm counts is O(K). The model omits nonlinear harm and uncertainty in ticket volume and value per breach.',
    ['Do not call the midpoint of an identification interval an expected effect.', 'Do not assert follow-up guarantees a decision merely because it narrows width.', 'Do not hide the sign convention when converting breach effects into value.'],
    ['data-science/treatment-effect-bounds-under-differential-attrition','data-science/bounded-missing-outcome-risk-scenarios','data-science/sensitivity-analysis-and-decision-stability','data-science/attrition-bounds-policy-decision-project'])

add('attrition-bounds-policy-decision-project',
    'Project: decide a routing policy with missing outcomes',
    'Prepare an evidence packet for a randomized routing rollout whose missing ticket outcomes leave the sign of the breach-rate effect unresolved.', [
    ('Lock the population and assignment unit', 'The assigned units are branches, and eligible tickets are counted under a frozen deadline rule. Record the branch lottery, exposure window, ticket denominator and breach definition before outcome recovery. A ticket-level calculation does not change the branch-level assignment mechanism. If branches selected their own status, the packet must not call the contrast randomized. [[data-science/partial-identification-and-the-assumption-ledger|The assumption ledger]] keeps design claims separate from missing-outcome claims.'),
    ('Audit every outcome status', 'For each assigned arm, list eligible, observed, breached and missing ticket counts. Reconcile observed plus missing to eligible. Separate missing due to logging failure from tickets never eligible; otherwise the denominator itself is wrong. Compute unrestricted rate bounds and the treated-minus-control effect interval. Show the complete-case contrast only as a descriptive comparison with a different missingness assumption. [[data-science/worst-case-bounds-for-missing-binary-outcomes|The rate lesson]] supplies the count formula.'),
    ('Create a disclosed restriction set', 'Use recovered logs or a sampling audit to justify plausible breach-risk ranges for missing tickets in each arm. Keep the worst-case interval alongside every restricted interval. If evidence does not support a restriction, leave the interval wide. Do not describe assumed risks as measured facts. [[data-science/bounded-missing-outcome-risk-scenarios|The risk-scenario lesson]] gives the arithmetic.'),
    ('Put an action threshold next to the bounds', 'Translate ticket volume, value per prevented breach and rollout cost into a break-even effect. State whether all, none or only some effects in the defensible interval justify rollout. If unresolved, estimate how many missing ticket outcomes can be recovered and how much bound width each recovery could remove. That is a concrete next experiment, not a promise of a favorable answer. [[data-science/decision-thresholds-and-follow-up-value-under-bounds|The decision lesson]] handles the endpoint logic.'),
    ('Issue a bounded recommendation', 'The executable gate checks that arm counts and decision inputs are present and internally consistent. It does not validate randomization, produce a confidence interval or certify the risk restrictions. The review packet should include the assignment log, outcome frame, all bound sets, follow-up plan and unresolved assumptions. If the eligibility frame or assignment record is incomplete, stop before reporting a causal effect. [[data-science/treatment-effect-bounds-under-differential-attrition|The effect lesson]] explains that limit.')],
    '''def attrition_review_gate(packet):
    required = {"assignment_log", "treated_counts", "control_counts",
                "unrestricted_bounds", "restriction_ledger",
                "decision_threshold", "follow_up_plan"}
    missing = sorted(required - set(packet))
    if missing:
        raise ValueError("missing packet items: " + ", ".join(missing))
    arm_missing = {}
    for arm in ("treated", "control"):
        assigned, observed, breaches = packet[arm + "_counts"]
        if assigned <= 0 or not 0 <= breaches <= observed <= assigned:
            raise ValueError("invalid " + arm + " counts")
        arm_missing[arm] = assigned - observed
    return {"packet_complete": True,
            "missing_by_arm": arm_missing,
            "has_follow_up_plan": bool(packet["follow_up_plan"])}

packet = {"assignment_log": "branch lottery retained",
          "treated_counts": (50, 40, 15),
          "control_counts": (50, 45, 20),
          "unrestricted_bounds": (-.20, .10),
          "restriction_ledger": {"treated": (.20, .60),
                                 "control": (.10, .40)},
          "decision_threshold": -.02,
          "follow_up_plan": "recover four treated ticket outcomes"}
review = attrition_review_gate(packet)
assert review == {"packet_complete": True,
                  "missing_by_arm": {"treated": 10, "control": 5},
                  "has_follow_up_plan": True}''',
    'The gate is O(A) time and space for A packet fields, plus constant work for two arms. The substantial cost is reconstructing assignment and ticket histories, then obtaining missing outcomes under a documented follow-up process.',
    ['Do not report a causal bound without a supported assignment design.', 'Do not call a chosen risk restriction observed data.', 'Do not treat packet completeness as statistical or operational approval.'],
    ['data-science/partial-identification-and-the-assumption-ledger','data-science/worst-case-bounds-for-missing-binary-outcomes','data-science/treatment-effect-bounds-under-differential-attrition','data-science/bounded-missing-outcome-risk-scenarios','data-science/decision-thresholds-and-follow-up-value-under-bounds'])

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
               featured=False, sort_order=14000 + index, status='published', published_at=stamp,
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
module_title = 'Partial identification and outcome bounds'
if not any(module['title'] == module_title for module in hub['data']['modules']):
    hub['data']['modules'].insert(-1, {'title':module_title,
                                      'summary':'Keep missing-outcome assumptions visible and test whether the policy decision survives them.',
                                      'lessons':tutorial_paths})
apply_module = next(module for module in hub['data']['modules'] if module['title'] == 'Apply your knowledge')
if project_path not in apply_module['lessons']:
    apply_module['lessons'].append(project_path)
if '<h2>' + module_title + '</h2>' not in hub['body']:
    hub['body'] += '<h2>' + module_title + '</h2>' + links(tutorial_paths)
    hub['body'] += '<h2>Attrition-bound policy review</h2>' + links([project_path])
hub['updated_at'] = stamp

project_hub = by_path[project_hub_path]
if project_path not in project_hub['data']['modules'][0]['lessons']:
    project_hub['data']['modules'][0]['lessons'].append(project_path)
if '<h2>Attrition-bound policy review</h2>' not in project_hub['body']:
    project_hub['body'] += '<h2>Attrition-bound policy review</h2>' + links([project_path])
project_hub['updated_at'] = stamp

for source, target in [
    ('data-science/missing-not-at-random-sensitivity-analysis', tutorial_paths[0]),
    ('data-science/proxy-measurement-and-label-error', tutorial_paths[1]),
    ('data-science/assignment-aware-permutation-test-for-branches', tutorial_paths[2]),
    ('data-science/sensitivity-analysis-and-decision-stability', tutorial_paths[3]),
    ('data-science/single-branch-policy-transfer-review-project', tutorial_paths[4]),
    ('data-science/outcome-label-error-audit-project', project_path),
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
