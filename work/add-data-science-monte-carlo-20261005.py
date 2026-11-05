"""Add original Monte Carlo decision-analysis lessons to Data Science."""
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
    'monte-carlo-estimands-and-reproducible-draws',
    'simulation-error-and-replication-budget',
    'joint-inputs-and-correlated-operational-shocks',
    'paired-policy-simulation-and-common-random-numbers',
    'warehouse-capacity-monte-carlo-project',
)
new_paths = {'data-science/' + slug for slug in slugs}
rows = [row for row in rows if row['path'] not in new_paths]
by_path = {row['path']: row for row in rows}
stamp = datetime.datetime.now(datetime.UTC).isoformat()
lessons = []

def add(slug, title, summary, sections, code, cost, mistakes, related):
    lessons.append(dict(path='data-science/' + slug, title=title, summary=summary,
                        sections=sections, code=code, cost=cost,
                        mistakes=mistakes, related=related))

add('monte-carlo-estimands-and-reproducible-draws',
    'Monte Carlo estimands and reproducible draws',
    'A Monte Carlo estimate averages outcomes from a specified stochastic model; the target quantity must be defined before generating random draws.', [
    ('Name the operational quantity', 'A support lead has capacity for 14 urgent reviews on a shift with 61 eligible cases. Suppose each case independently requires urgent review with modeled probability 0.19. The immediate question is the model-based chance that urgent demand exceeds 14, not the average number of urgent cases and not an observed historical breach rate. One simulated shift draws 61 urgent flags and records a breach indicator. Averaging that indicator over independent simulated shifts estimates the modeled breach probability. [[data-science/decision-objective-and-action-unit|The decision unit]] is one shift.'),
    ('Separate inputs from outcomes', 'The case count, urgent-share model, capacity and breach rule are inputs. The number of urgent cases and whether demand exceeds capacity are outputs. A change from more than 14 to at least 14 changes the event; document the boundary in the metric contract. The independence assumption is also an input, not a fact created by running code. Shared campaign days or weather shocks can make urgent cases arrive together. [[data-science/joint-inputs-and-correlated-operational-shocks|Joint-input modeling]] handles that case.'),
    ('Keep a reproducible random stream', 'Use a local random generator initialized with a recorded seed. Identical code, configuration and runtime behavior then replay the same pseudo-random sequence in this environment. A seed helps investigate a calculation; it does not make an uncertain assumption true, nor does one seed create independent evidence. Store the code version, input snapshot, run count and seed together. [[data-science/reproducible-analysis-snapshot|An analysis snapshot]] should let a reviewer recover the exact model release.'),
    ('Distinguish model risk from numerical noise', 'If the urgent probability is actually 0.27, adding simulations around 0.19 only estimates the wrong model more precisely. Examine historical case counts and stratify by shift type before fitting an input distribution. Hold back recent shifts for validation and compare predicted breach frequencies with observed ones. A simulator should fail visibly when a parameter falls outside its domain rather than silently clipping it to a comfortable value.'),
    ('Use the output for a decision', 'A modeled breach probability has value only beside an action threshold and consequence. One manager may buy flex coverage if breach chance exceeds 0.12; another may require expected backlog cost to exceed a staffing price. Preserve the probability estimate, input assumptions and candidate policy separately. [[data-science/simulation-error-and-replication-budget|Simulation error]] tells how much numerical precision the chosen run count bought, while [[data-science/warehouse-capacity-monte-carlo-project|the project]] carries the result into a policy comparison.')],
    '''from random import Random

def urgent_review_breach_probability(cases_per_shift, urgent_probability,
                                     review_capacity, replications, seed):
    if cases_per_shift < 0 or not 0 <= urgent_probability <= 1:
        raise ValueError("invalid demand model")
    if review_capacity < 0 or replications <= 0:
        raise ValueError("invalid capacity or run count")
    draw_stream = Random(seed)
    breaches = 0
    for _ in range(replications):
        urgent_cases = sum(draw_stream.random() < urgent_probability
                           for _ in range(cases_per_shift))
        breaches += urgent_cases > review_capacity
    return breaches / replications

first_run = urgent_review_breach_probability(61, 0.19, 14, 24000, 4817)
replayed = urgent_review_breach_probability(61, 0.19, 14, 24000, 4817)
assert first_run == replayed
assert 0 < first_run < 1''',
    'The direct model draws C case flags for each of R shifts: O(R × C) time and O(1) additional space. This is suitable for a transparent baseline; a binomial sampler can reduce work at scale. Faster sampling does not compensate for a wrong input distribution.',
    ['Do not call a modeled breach probability an observed historical rate.', 'Do not change a strict greater-than rule to greater-than-or-equal during reporting.', 'Do not treat a fixed seed as evidence that the input model is valid.'],
    ['data-science/simulation-error-and-replication-budget','data-science/joint-inputs-and-correlated-operational-shocks','data-science/paired-policy-simulation-and-common-random-numbers','data-science/warehouse-capacity-monte-carlo-project'])

add('simulation-error-and-replication-budget',
    'Simulation error and replication budgets',
    'Monte Carlo standard error measures variation from a finite number of simulated replications while holding the input model fixed.', [
    ('Identify two uncertainty layers', 'The support-shift simulator returns a breach flag on each modeled shift. If R independent replications yield estimated breach share p, its approximate Monte Carlo standard error is the square root of p times (1 minus p) divided by R. This quantifies numerical noise from finite simulation. It says nothing about uncertainty in the urgent probability, arrival distribution or capacity estimate. [[data-science/monte-carlo-estimands-and-reproducible-draws|The estimand lesson]] separates model inputs from outputs.'),
    ('Budget precision before running', 'For an approximate 95% half-width no larger than 0.01 under the most variable possible Bernoulli result, use p times (1 minus p) at its maximum 0.25. The planning calculation rounds up 0.25 times (1.96 divided by 0.01) squared, which is 9,604 replications. This is a fixed-run planning bound for the normal approximation, not a guarantee of exact interval coverage at rare probabilities. A rare breach may need many more runs to observe enough events for a useful estimate.'),
    ('Report the denominator and interval', 'An output such as 0.143 without a run count hides precision. Report the event count, R, estimate and a stated interval method. The simple p ± 1.96 standard-error calculation below is a diagnostic only; it can be poor near zero or one and may cross probability bounds. For publication, use a binomial interval appropriate to the event count or increase replications. A zero observed breach count does not prove a zero breach probability.'),
    ('Keep the stopping rule honest', 'Repeatedly running batches until the estimate passes a desired threshold or the interval looks favorable changes the analysis. Fix the replication budget before inspecting the result, or use a sequential method designed for optional stopping. Increasing R after finding a large standard error can be an engineering refinement if the policy and reporting rule were specified in advance; document that decision and rerun all candidate policies under the same release protocol.'),
    ('Spend compute where it changes the decision', 'If the probability threshold for buying flex coverage is 0.12 and the estimate is 0.47, a tiny Monte Carlo standard error is unlikely to alter the decision. If the estimate is 0.121, more simulation may matter. Compare numerical error with input-model sensitivity: rerun plausible urgent-share or demand assumptions. [[data-science/scenario-stress-and-decision-regret|Scenario stress]] addresses model uncertainty that a large R cannot erase.')],
    '''from math import ceil, sqrt
from random import Random

def planned_binary_replications(target_half_width, z_score=1.96):
    if not 0 < target_half_width < 1 or z_score <= 0:
        raise ValueError("invalid precision target")
    return ceil(0.25 * (z_score / target_half_width) ** 2)

def simulated_breach_precision(replications, seed):
    if replications < 2:
        raise ValueError("at least two replications required")
    draw_stream = Random(seed)
    breaches = sum(draw_stream.random() < 0.31 for _ in range(replications))
    estimate = breaches / replications
    standard_error = sqrt(estimate * (1 - estimate) / replications)
    return breaches, estimate, standard_error

budget = planned_binary_replications(0.01)
assert budget == 9604
events, probability, mc_error = simulated_breach_precision(24000, 287)
assert 0 < events < 24000
assert 1.96 * mc_error < 0.01''',
    'Planning the run count is O(1). Generating R independent breach flags is O(R) time and O(1) additional space when outcomes are streamed. Halving Monte Carlo standard error requires about four times as many independent replications, which can be expensive for detailed shift models.',
    ['Do not call Monte Carlo error the total uncertainty of a decision.', 'Do not interpret zero simulated breaches as proof of zero risk.', 'Do not keep changing the stopping rule after reading interim outcomes.'],
    ['data-science/monte-carlo-estimands-and-reproducible-draws','data-science/joint-inputs-and-correlated-operational-shocks','data-science/paired-policy-simulation-and-common-random-numbers','data-science/warehouse-capacity-monte-carlo-project'])

add('joint-inputs-and-correlated-operational-shocks',
    'Joint inputs and correlated operational shocks',
    'A simulation must preserve relationships among inputs when the same real-world event changes demand and available capacity together.', [
    ('Define the shared driver', 'On a disruption day, the warehouse receives 63 orders and only six staff are available. Otherwise it receives 41 orders and has nine staff. Each worker can complete seven orders. In this deliberately discrete teaching model, a disruption occurs with probability 0.23. When it occurs, demand 63 exceeds capacity 42; otherwise demand 41 fits within capacity 63. The modeled overflow probability is therefore 0.23. The driver creates both high load and low staffing.'),
    ('See the independence mistake', 'If demand and staffing are drawn independently with the same separate marginal probabilities, overflow occurs only when high demand and low staffing happen together. That probability is 0.23 times 0.23, or 0.0529. Both simulators can display the correct demand marginal and correct staffing marginal while disagreeing sharply on the decision event. Matching univariate histograms is not enough. [[data-science/derived-metric-uncertainty-and-correlation|Correlation and derived metrics]] explain why the joint process matters.'),
    ('Model a mechanism, not just a coefficient', 'The shared disruption state is a plausible causal driver of both arrival volume and absences. A single measured correlation coefficient would not explain which combinations of extremes are possible or when the relationship changes. In production, estimate disruption frequency and conditional arrival and staffing distributions from versioned periods; compare joint cells across seasons. If observations are sparse, use a small set of explicit scenarios and show sensitivity rather than manufacture precision.'),
    ('Keep scenario timing coherent', 'Draw the disruption state once per shift, then draw that shift’s demand and staffing conditional on the state. Drawing a new shock for every case would imply that one shift simultaneously had many unrelated weather states. Treat a shift as the replication unit and preserve any within-shift dependence. If a customer or site spans multiple shifts, temporal persistence may need a higher-level model. [[data-science/metric-denominator-and-cohort|The denominator]] for a shift-level breach is shifts, not orders.'),
    ('Validate the joint output', 'Check simulated disruption share, demand-staffing combinations, overflow frequency and source data coverage. A policy may appear safe under the independent model because the tail combination is artificially rare. Keep the independent version as a stress-test contrast, not the default if the shared mechanism is supported. [[data-science/paired-policy-simulation-and-common-random-numbers|Paired policy evaluation]] must reuse the same sampled joint shift for both policies.')],
    '''from random import Random

def overflow_rate(replications, seed, shared_disruption):
    if replications <= 0:
        raise ValueError("replications must be positive")
    draw_stream = Random(seed)
    overflows = 0
    for _ in range(replications):
        demand_disruption = draw_stream.random() < 0.23
        staffing_disruption = (demand_disruption if shared_disruption
                                else draw_stream.random() < 0.23)
        orders = 63 if demand_disruption else 41
        staff = 6 if staffing_disruption else 9
        overflows += orders > staff * 7
    return overflows / replications

coupled_risk = overflow_rate(30000, 73, True)
independent_risk = overflow_rate(30000, 73, False)
assert abs(coupled_risk - 0.23) < 0.02
assert abs(independent_risk - 0.0529) < 0.02
assert coupled_risk > independent_risk''',
    'Generating R shifts costs O(R) time and O(1) additional space. More realistic conditional distributions add sampling work but usually less cost than the decision error caused by breaking dependence. Marginal validation alone cannot detect a wrong joint tail.',
    ['Do not draw one disruption state for demand and an unrelated state for staffing when one event affects both.', 'Do not validate only the separate input marginals.', 'Do not treat the teaching probability as a measured disruption rate.'],
    ['data-science/monte-carlo-estimands-and-reproducible-draws','data-science/simulation-error-and-replication-budget','data-science/paired-policy-simulation-and-common-random-numbers','data-science/warehouse-capacity-monte-carlo-project'])

add('paired-policy-simulation-and-common-random-numbers',
    'Paired policy simulations with common random numbers',
    'To compare two policies, evaluate both on the same simulated operating conditions and average their within-replication outcome differences.', [
    ('Define the contrast before sampling', 'A warehouse manager wants the expected reduction in unfinished orders from adding three flex workers to each shift. On a sampled shift, draw disruption, order count and base staffing once. Run the baseline capacity and flex capacity against that same shift. The difference in unfinished orders is the contribution from one replication. It does not require pretending the two policies were observed on different random days. [[data-science/decision-objective-and-action-unit|The action unit]] is the shift.'),
    ('Why pairing helps', 'A high-demand day makes both baseline and flex outcomes worse. Comparing them under identical demand cancels much of that irrelevant day-to-day variation from the policy difference. With positive covariance between policy outcomes, the variance of the within-shift difference can be lower than the variance of a difference of independently estimated means. This is a potential gain, not a universal promise; a policy with a very different mechanism can change the covariance pattern.'),
    ('Keep the random draws aligned', 'Sample all exogenous inputs before applying either policy. A policy may change processing speed, but it should not silently cause the weather draw or incoming-order draw to move to another place in the random stream. Passing an immutable shift scenario into both policy functions makes the pairing visible. Record the seed and scenario generator version. [[data-science/monte-carlo-estimands-and-reproducible-draws|Reproducible draws]] are necessary for debugging, not proof that the model represents reality.'),
    ('Estimate the difference and its error', 'Average the per-shift shortfall reductions. The sample standard deviation of those reductions divided by the square root of the replication count is the Monte Carlo standard error of the paired mean, assuming independent simulated shifts. Do not compute this standard error from the two policy outcomes as though they were unrelated samples. A business decision should compare the reduction with incremental staffing cost and a range of plausible demand inputs.'),
    ('Inspect edge cases', 'Flex capacity cannot increase unfinished orders if it only adds productive staff under the same shift scenario. The code asserts this monotonicity. If the output violates it after a code change, inspect the policy logic or state mutation before reporting results. Other policies may trade one loss for another, so a nonnegative difference is not always a valid invariant. [[data-science/warehouse-capacity-monte-carlo-project|The project]] adds cost units and a release decision.')],
    '''from math import sqrt
from random import Random
from statistics import stdev

def paired_shortfall_reduction(replications, seed):
    if replications < 2:
        raise ValueError("at least two shifts required")
    draw_stream = Random(seed)
    reductions = []
    for _ in range(replications):
        disruption = draw_stream.random() < 0.27
        routine_orders = draw_stream.randint(34, 47)
        shock_orders = draw_stream.randint(18, 26) if disruption else 0
        orders = routine_orders + shock_orders
        base_staff = 8 - (2 if disruption else 0)
        base_shortfall = max(0, orders - 7 * base_staff)
        flex_shortfall = max(0, orders - 7 * (base_staff + 3))
        reductions.append(base_shortfall - flex_shortfall)
    if any(reduction < 0 for reduction in reductions):
        raise AssertionError("flex staff increased shortfall")
    return sum(reductions) / replications, stdev(reductions) / sqrt(replications)

saved_orders, mc_error = paired_shortfall_reduction(24000, 907)
assert saved_orders > 0
assert mc_error > 0''',
    'For R shifts, the direct implementation is O(R) time and O(R) space because it retains differences for a sample standard deviation. A streaming variance algorithm can reduce space to O(1). Pairing can reduce the replication budget when policy outcomes are positively correlated.',
    ['Do not simulate independent demand for policies meant to face the same shift.', 'Do not calculate the difference error as if paired outcomes were independent.', 'Do not assume common random numbers always reduce variance.'],
    ['data-science/monte-carlo-estimands-and-reproducible-draws','data-science/simulation-error-and-replication-budget','data-science/joint-inputs-and-correlated-operational-shocks','data-science/warehouse-capacity-monte-carlo-project'])

add('warehouse-capacity-monte-carlo-project',
    'Project: simulate warehouse capacity under shared shocks',
    'Build a versioned shift simulator, compare baseline and flex staffing on paired scenarios, and publish a decision packet with numerical and model uncertainty kept separate.', [
    ('Set the release contract', 'The decision is whether to reserve three flex workers per shift. One shift is one replication. Model routine orders from 34 through 47. A disruption occurs with probability 0.27, adds 18 through 26 orders and removes two of eight scheduled workers. Each available worker clears seven orders; unresolved orders cost 210 units each, and each flex worker costs 85 units per shift. These are illustrative fixture inputs, not calibrated operating estimates. [[data-science/monte-carlo-estimands-and-reproducible-draws|The estimand]] is expected net cost difference and overflow risk under this model.'),
    ('Verify a hand-calculated shift', 'A disrupted shift with 41 routine orders and 21 shock orders has 62 total orders and six base workers. Baseline capacity is 42, leaving 20 unfinished. Three flex workers increase capacity to 63, leaving none unfinished. Baseline penalty is 4,200 cost units; flex pays 255 units for the workers. That paired shift favors flex by 3,945 cost units. Check this calculation before any large random run.'),
    ('Preserve the joint operating state', 'Draw disruption once, then use it for both the demand increment and staff loss. Applying independent disruption draws to those inputs would make the dangerous high-demand, low-staff combination artificially rare. Pass the same realized shift to both policies. [[data-science/joint-inputs-and-correlated-operational-shocks|The joint-input lesson]] shows how even correct marginal distributions can yield a wrong overflow estimate.'),
    ('Quantify simulation and model uncertainty', 'Run a fixed replication budget and retain paired per-shift net savings. Report mean cost for each policy, overflow shares, mean net saving and the Monte Carlo standard error of that saving. Then rerun with plausible disruption frequencies, labor costs and per-order penalties; a larger replication count only reduces numerical error under the selected inputs. [[data-science/simulation-error-and-replication-budget|Replication planning]] and [[data-science/scenario-stress-and-decision-regret|scenario stress]] address different uncertainty layers.'),
    ('Package the decision for review', 'Archive input distributions with their historical date ranges, a shift-level data-quality check, seed, code revision, run count, one worked shift and output summaries. State whether the cost model includes customer impact of delayed orders and whether flex staff are available during disruptions. If the historical disruption rate is based on a tiny sample or the cost ranking flips under credible inputs, present both policies as unresolved and name the data needed next. The code below supplies only a transparent teaching baseline.')],
    '''from math import sqrt
from random import Random
from statistics import mean, stdev

def evaluate_capacity_policy(replications, seed):
    if replications < 2:
        raise ValueError("at least two shifts required")
    draw_stream = Random(seed)
    baseline_costs, flex_costs, savings = [], [], []
    baseline_overflows = flex_overflows = 0
    for _ in range(replications):
        disrupted = draw_stream.random() < 0.27
        routine_orders = draw_stream.randint(34, 47)
        extra_orders = draw_stream.randint(18, 26) if disrupted else 0
        orders = routine_orders + extra_orders
        available_staff = 8 - (2 if disrupted else 0)
        baseline_backlog = max(0, orders - 7 * available_staff)
        flex_backlog = max(0, orders - 7 * (available_staff + 3))
        baseline_cost = 210 * baseline_backlog
        flex_cost = 3 * 85 + 210 * flex_backlog
        baseline_costs.append(baseline_cost)
        flex_costs.append(flex_cost)
        savings.append(baseline_cost - flex_cost)
        baseline_overflows += baseline_backlog > 0
        flex_overflows += flex_backlog > 0
    return {"baseline_mean_cost": mean(baseline_costs),
            "flex_mean_cost": mean(flex_costs),
            "mean_net_saving": mean(savings),
            "saving_mc_error": stdev(savings) / sqrt(replications),
            "baseline_overflow_share": baseline_overflows / replications,
            "flex_overflow_share": flex_overflows / replications}

report = evaluate_capacity_policy(24000, 499)
assert report["baseline_overflow_share"] >= report["flex_overflow_share"]
assert abs(report["mean_net_saving"] -
           (report["baseline_mean_cost"] - report["flex_mean_cost"])) < 1e-9''',
    'Generating R shifts and evaluating two fixed policies costs O(R) time and O(R) space in this auditable implementation. Streaming means and variance reduce memory to O(1). Input estimation, validation, and stress scenarios are separate work and cannot be replaced by more replications.',
    ['Do not treat fixture costs and disruption rates as observed business facts.', 'Do not draw a new shift for the second policy in a paired comparison.', 'Do not confuse a small Monte Carlo error with a reliable operational forecast.'],
    ['data-science/monte-carlo-estimands-and-reproducible-draws','data-science/simulation-error-and-replication-budget','data-science/joint-inputs-and-correlated-operational-shocks','data-science/paired-policy-simulation-and-common-random-numbers'])

assert len(lessons) == len(new_paths) == 5
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
               difficulty='Intermediate', tags=['ai-data', 'data-science'], potd_date=None,
               featured=False, sort_order=13000 + index, status='published', published_at=stamp,
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

tutorial_paths = ['data-science/' + slug for slug in slugs[:4]]
project_path = 'data-science/' + slugs[-1]
hub = by_path[root_path]
if not any(module['title'] == 'Monte Carlo decisions and simulation quality' for module in hub['data']['modules']):
    hub['data']['modules'].insert(-1, {'title':'Monte Carlo decisions and simulation quality',
                                      'summary':'Specify a modeled decision, control simulation error, preserve shared shocks and compare policies on paired shifts.',
                                      'lessons':tutorial_paths})
apply_module = next(module for module in hub['data']['modules'] if module['title'] == 'Apply your knowledge')
if project_path not in apply_module['lessons']:
    apply_module['lessons'].append(project_path)
if '<h2>Monte Carlo decisions and simulation quality</h2>' not in hub['body']:
    hub['body'] += '<h2>Monte Carlo decisions and simulation quality</h2>' + links(tutorial_paths)
    hub['body'] += '<h2>Warehouse capacity simulation project</h2>' + links([project_path])
hub['updated_at'] = stamp

project_hub = by_path[project_hub_path]
if project_path not in project_hub['data']['modules'][0]['lessons']:
    project_hub['data']['modules'][0]['lessons'].append(project_path)
if '<h2>Warehouse capacity simulation project</h2>' not in project_hub['body']:
    project_hub['body'] += '<h2>Warehouse capacity simulation project</h2>' + links([project_path])
project_hub['updated_at'] = stamp

for source, target in [
    ('data-science/decision-objective-and-action-unit', tutorial_paths[0]),
    ('data-science/precision-budget-and-effective-sample-size', tutorial_paths[1]),
    ('data-science/derived-metric-uncertainty-and-correlation', tutorial_paths[2]),
    ('data-science/scenario-stress-and-decision-regret', tutorial_paths[3]),
    ('data-science/support-review-allocation-project', project_path),
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
print(json.dumps({'new_articles':len(lessons), 'new_projects':1, 'crosslinks_from_existing':5}))
