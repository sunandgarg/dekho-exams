"""Add original decision-optimization lessons to the Data Science path."""
import datetime
import html
import json
from pathlib import Path
import re
import uuid

root = Path(__file__).resolve().parents[1]
fixture = root / 'src/data/fixtures.json'
rows = json.loads(fixture.read_text())
slugs = (
    'decision-objective-and-action-unit',
    'constraint-feasibility-and-slack',
    'integer-allocation-and-relaxation-gap',
    'scenario-stress-and-decision-regret',
    'support-review-allocation-project',
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

add('decision-objective-and-action-unit',
    'Decision objectives: define the action before optimizing a score',
    'An optimization model needs a decision unit, a measurable outcome and an objective tied to the real action.', [
    ('Specify what can change', 'A support team has reviewer hours to assign across ordinary and partner cases. The decision variables are counts of cases to review in each queue, not predicted defect probabilities. Predicted risk can inform expected benefit, but it is an input to the decision rather than the decision itself. One unit of action is one completed review with a known time cost. [[machine-learning/decision-threshold-and-cost|A decision threshold]] is a different way to map scores to actions when capacity constraints are absent.'),
    ('Choose one accountable outcome', 'The team wants to prevent customer escalations, so it estimates prevented escalations per reviewed case. A high defect-detection count is not identical if some detected defects would never escalate. Record the outcome window and how the benefit estimate was obtained. If it came from a small observational sample, show uncertainty and avoid treating point estimates as certain. [[data-science/sampling-frame-and-coverage-error|The sampling frame]] limits where the estimate applies.'),
    ('Check the arithmetic and units', 'Suppose one ordinary review takes two analyst-hours and is expected to prevent 1.4 escalations; one partner review takes three hours and is expected to prevent 2.3. An allocation of four ordinary and three partner reviews uses 17 analyst-hours and has modeled benefit 12.5 prevented escalations. The arithmetic is simple; the hard part is defending the estimates and ensuring that a half-completed review is not counted as a completed action.'),
    ('Separate objectives from constraints', 'Review capacity is an upper bound. Minimum coverage for the partner queue is a requirement. Neither should be hidden as an arbitrary penalty in the objective if violating it is unacceptable. A weighted score that mixes labor cost, risk and fairness without units can select a numerically attractive but operationally invalid allocation. [[data-science/constraint-feasibility-and-slack|Constraint checks]] keep those rules visible.'),
    ('Keep a baseline', 'Compare the proposed plan to the current scheduling rule and to a simple first-come policy under the same budget and case mix. An optimizer that improves a made-up objective while reducing the real service outcome is a failed model. Report predicted benefit, actual capacity used and the operational baseline together.')],
    'def allocation_totals(ordinary_reviews, partner_reviews):\n    if min(ordinary_reviews, partner_reviews) < 0:\n        raise ValueError("review counts must be nonnegative")\n    analyst_hours = 2 * ordinary_reviews + 3 * partner_reviews\n    expected_prevented = 1.4 * ordinary_reviews + 2.3 * partner_reviews\n    return analyst_hours, expected_prevented\n\nhours, benefit = allocation_totals(4, 3)\nassert hours == 17 and round(benefit, 1) == 12.5',
    'Evaluating one two-queue allocation takes O(1) time and space. For Q queues the objective calculation is O(Q); searching all feasible plans is a separate problem whose cost depends on variable bounds and whether fractional or integer actions are allowed.',
    ['Do not optimize a model score without defining the action it controls.', 'Do not treat predicted benefit as measured benefit.', 'Do not hide mandatory coverage inside an arbitrary objective penalty.'],
    ['data-science/constraint-feasibility-and-slack','data-science/integer-allocation-and-relaxation-gap','machine-learning/decision-threshold-and-cost','data-science/support-review-allocation-project'])

add('constraint-feasibility-and-slack',
    'Constraint feasibility and slack: reject impossible plans early',
    'A feasible plan satisfies every declared operational bound before its objective value matters.', [
    ('Write inequalities in the right units', 'Let ordinary and partner reviews use two and three analyst-hours respectively. With 23 available hours, 2 × ordinary + 3 × partner must be at most 23. If the partner contract requires at least four reviews and ordinary coverage requires at least three, the minimum plan consumes 18 hours and leaves five hours of slack. Count reviews as nonnegative integers. [[data-science/decision-objective-and-action-unit|The action unit]] keeps hours and cases from being mixed.'),
    ('Test feasibility before seeking an optimum', 'A new policy might demand eight partner reviews and four ordinary reviews under the same 23-hour budget. That minimum consumes 32 hours, so no optimizer can satisfy it. Return an infeasible state with the conflicting requirements and required extra capacity. Do not accept a solver output merely because it returns numbers; inspect status and verify constraints independently.'),
    ('Keep hard and soft bounds apart', 'Some requirements are truly hard, such as legal handling limits or maximum available staff hours. Others are targets that can be traded off with an explicit cost, such as a preferred mix of work. Mark which is which. Softening a hard safety rule to make a model feasible is a policy change and needs approval outside the solver. A zero-slack plan may also be brittle when review duration varies.'),
    ('Report slack in human terms', 'For a feasible plan of five ordinary and four partner reviews, 22 of 23 hours are used, leaving one analyst-hour; partner coverage is exactly at the minimum of four. Those two facts explain different risks. An extra urgent partner case cannot fit, while one ordinary review may also exceed the budget. Sensitivity work should perturb hours and demand separately. [[data-science/scenario-stress-and-decision-regret|Scenario checks]] show whether the decision survives those changes.'),
    ('Validate the final schedule', 'After a solver or planner proposes an allocation, recompute every left-hand side from the released plan using the same unit definitions. Rounding a fractional result to integers can break a bound. Also check that each queue has enough eligible cases to fulfill its assigned count; a plan cannot review cases that do not exist.')],
    'def validate_review_plan(ordinary_reviews, partner_reviews, available_hours=23):\n    if any(not isinstance(count, int) or count < 0\n           for count in (ordinary_reviews, partner_reviews)):\n        raise ValueError("whole nonnegative review counts required")\n    used_hours = 2 * ordinary_reviews + 3 * partner_reviews\n    return {"feasible": (ordinary_reviews >= 3 and partner_reviews >= 4\n                         and used_hours <= available_hours),\n            "hour_slack": available_hours - used_hours,\n            "partner_coverage_slack": partner_reviews - 4}\n\nassert validate_review_plan(5, 4) == {\n    "feasible": True, "hour_slack": 1, "partner_coverage_slack": 0}',
    'Checking C constraints over Q decision variables is O(CQ) time in a dense representation; this fixed two-variable check is O(1). Feasibility reporting should preserve each constraint residual, not only one Boolean, so operators can diagnose an impossible plan.',
    ['Do not ask an optimizer to repair mutually inconsistent hard constraints.', 'Do not round a fractional plan without rechecking capacity and minimums.', 'Do not call a zero-slack schedule safe when work duration is uncertain.'],
    ['data-science/decision-objective-and-action-unit','data-science/integer-allocation-and-relaxation-gap','data-science/scenario-stress-and-decision-regret','data-science/support-review-allocation-project'])

add('integer-allocation-and-relaxation-gap',
    'Integer allocation and relaxation gaps for indivisible work',
    'A fractional allocation can bound an integer plan but cannot schedule part of an indivisible task.', [
    ('Show the difference with a small case', 'Queue A reviews take three hours and yield five benefit units; queue B reviews take two hours and yield three. The budget is seven hours. The continuous relaxation could assign 7/3 A reviews and claim 35/3, about 11.67 benefit units. Real reviews are indivisible. The best integer plan is one A and two B reviews: seven hours and 11 units. [[data-science/constraint-feasibility-and-slack|Feasibility]] is checked after the integer choice, not assumed from a fractional solution.'),
    ('Use the relaxation as information', 'For a maximization problem, the continuous relaxation provides an upper bound on the best integer objective when it contains every integer-feasible plan. The gap between that bound and a valid integer plan helps assess how much improvement might remain. It is not a percentage that can be interpreted without a stated denominator, and it may be weak for some formulations.'),
    ('Respect dependencies', 'If every partner review needs a specialist sign-off, the plan may have a second capacity constraint. If two reviews target the same customer escalation, their benefits may not add independently. A linear objective assumes additive marginal benefit; validate that assumption or model the interaction explicitly. Do not increase integer counts beyond the number of eligible cases in each queue.'),
    ('Choose a method for scale', 'Brute-force enumeration is transparent for two queues and a small budget. With many queues, dependencies and large capacities, the number of combinations grows quickly; use an appropriate integer-programming solver and retain its status, feasible incumbent and best bound. A time-limited solution may be good enough operationally without being proved optimal. State that distinction in the decision packet.'),
    ('Make the output auditable', 'Publish queue counts, hours consumed, expected benefit and every active constraint. Add a simple feasible baseline such as all B reviews under the budget, then show the improvement. Recompute the totals from source data, not only the solver return object. A plan with a higher objective but a hidden policy violation is not a win.')],
    'def best_small_integer_plan(hour_budget):\n    best = (0, 0, 0)  # benefit, queue_a_reviews, queue_b_reviews\n    for queue_a_reviews in range(hour_budget // 3 + 1):\n        for queue_b_reviews in range(hour_budget // 2 + 1):\n            used_hours = 3 * queue_a_reviews + 2 * queue_b_reviews\n            if used_hours <= hour_budget:\n                benefit = 5 * queue_a_reviews + 3 * queue_b_reviews\n                best = max(best, (benefit, queue_a_reviews, queue_b_reviews))\n    return best\n\nassert best_small_integer_plan(7) == (11, 1, 2)',
    'The two-loop enumeration uses O((B/3 + 1)(B/2 + 1)) time and O(1) auxiliary space for budget B. That is suitable only for small fixtures; general integer programming can be computationally hard, so larger instances need solver bounds and runtime limits.',
    ['Do not schedule a fractional review because the relaxed objective looks better.', 'Do not claim a time-limited integer solution is optimal without a proof or bound.', 'Do not assume benefits add when actions overlap on the same customer.'],
    ['data-science/decision-objective-and-action-unit','data-science/constraint-feasibility-and-slack','data-science/scenario-stress-and-decision-regret','data-science/support-review-allocation-project'])

add('scenario-stress-and-decision-regret',
    'Scenario stress tests and regret for uncertain allocation benefits',
    'An optimal plan under one benefit estimate may be a poor plan when the estimate or demand shifts.', [
    ('Keep constraints fixed while varying assumptions', 'A staffing plan is chosen before tomorrow’s case mix is known. Create a small set of defensible benefit scenarios, such as ordinary conditions and a partner escalation surge, while keeping available hours and minimum coverage rules explicit. The scenario set is a stress test, not a probability distribution unless frequencies have been estimated. [[data-science/sensitivity-analysis-and-decision-stability|Sensitivity analysis]] distinguishes uncertain inputs from sampling intervals.'),
    ('Compare plans in each scenario', 'Suppose two review types cost four and three hours. Under ordinary demand, their benefits per review are nine and six; under a partner surge, they are two and five. With a nine-hour budget, two first-type reviews yield 18 ordinarily but only four in the surge. Three second-type reviews yield 18 ordinarily and 15 in the surge. A plan chosen only by ordinary benefit misses the downside. These values are scenario assumptions, not measured outcomes.'),
    ('Define a decision rule', 'A worst-case rule selects the feasible plan with the highest minimum benefit across the declared scenarios. Regret instead compares each plan with the best feasible plan in that scenario and asks how much benefit the choice gives up. Different rules can choose different plans. State the organization’s risk preference before seeing the winner. [[data-science/decision-objective-and-action-unit|The objective]] must still reflect a real operating outcome.'),
    ('Check uncertain capacity too', 'If one review sometimes takes an extra hour, a plan using exactly all nine hours can be infeasible in practice. Model that as a capacity scenario or retain explicit buffer. Do not treat a precise solver result as more certain than its time-cost and benefit inputs. [[data-science/constraint-feasibility-and-slack|Slack]] identifies which constraint is closest to failure.'),
    ('Turn the stress result into evidence work', 'When plans trade places across plausible scenarios, identify which parameter matters most and collect better evidence there: a targeted review-time sample, a partner-case audit or a pilot allocation. Publish the scenario matrix and chosen rule with the plan. A later outcome audit can then distinguish a bad decision model from a scenario that actually changed.')],
    'def choose_maximin_plan(candidate_plans, benefit_scenarios, hour_budget):\n    feasible = [plan for plan in candidate_plans\n                if 4 * plan[0] + 3 * plan[1] <= hour_budget]\n    if not feasible:\n        raise ValueError("no feasible candidate plan")\n    return max(feasible, key=lambda plan: min(\n        plan[0] * first_value + plan[1] * second_value\n        for first_value, second_value in benefit_scenarios))\n\nplans = [(2, 0), (0, 3), (1, 1)]\nscenarios = [(9, 6), (2, 5)]\nassert choose_maximin_plan(plans, scenarios, 9) == (0, 3)',
    'Evaluating P candidate plans against S scenarios costs O(PS) time and O(P) memory for the feasible list. Generating all integer plans can dominate this evaluation; large instances need a solver or carefully bounded candidate set, plus independent feasibility checks.',
    ['Do not call scenario values probabilities without evidence.', 'Do not choose a risk rule after seeing which plan it favors.', 'Do not stress only benefits while assuming review duration and capacity are fixed.'],
    ['data-science/decision-objective-and-action-unit','data-science/constraint-feasibility-and-slack','data-science/integer-allocation-and-relaxation-gap','data-science/support-review-allocation-project'])

add('support-review-allocation-project',
    'Project: allocate support reviews under capacity and uncertainty',
    'Build a reviewable staffing plan that ties evidence to decisions, rejects infeasible schedules and reports scenario exposure.', [
    ('Freeze the decision inputs', 'Create 47 eligible ordinary cases and 23 partner cases. For each queue, record the number available, analyst-hours per completed review and estimated prevented escalations. Include an audit sample and uncertainty notes for those estimates. State the review day, staffing cutoff and which cases can actually be assigned. [[data-science/decision-objective-and-action-unit|The decision contract]] defines one complete review as the action.'),
    ('Write constraints as checks', 'Set a total analyst-hour budget, minimum coverage for each queue and an upper bound from eligible case counts. Include a fixture whose minimums exceed capacity and assert that the model reports infeasibility rather than returning a fake optimum. For a feasible allocation, report hours used and slack for every bound. [[data-science/constraint-feasibility-and-slack|Feasibility rules]] are reviewed before any benefit ranking.'),
    ('Solve the small integer case', 'Enumerate feasible whole-review allocations for a small fixture and compare with a first-come baseline. Calculate the continuous relaxation only as an upper bound if its formulation covers the integer plans. For a larger fixture, use a solver and save its status, best bound, runtime limit and chosen incumbent. [[data-science/integer-allocation-and-relaxation-gap|The integer lesson]] explains the difference between a valid plan and a proof of optimality.'),
    ('Stress the released plan', 'Evaluate each plan under ordinary and partner-surge benefit estimates, then under a longer review-duration scenario. Publish the selected risk rule, worst-case benefit and any capacity breach. A plan that ranks first on expected benefit but violates the stressed duration limit needs either a buffer or an explicit operational contingency. [[data-science/scenario-stress-and-decision-regret|Scenario analysis]] should be reproducible from a saved matrix.'),
    ('Deliver an audit packet', 'Save input snapshot, estimate provenance, units, constraints, feasible-plan table, selected plan, baseline, scenario matrix, code revision and a short decision note. Recompute the final plan’s objective and each constraint independently of the search routine. After the review day, compare actual hours and prevented escalations with the estimates; feed that error back into the next allocation.')],
    'def audit_released_plan(ordinary_reviews, partner_reviews,\n                            available_hours, ordinary_cases, partner_cases):\n    used_hours = 2 * ordinary_reviews + 3 * partner_reviews\n    feasible = (0 <= ordinary_reviews <= ordinary_cases and\n                0 <= partner_reviews <= partner_cases and\n                used_hours <= available_hours)\n    return {"feasible": feasible, "hours_used": used_hours,\n            "hour_slack": available_hours - used_hours}\n\nassert audit_released_plan(4, 3, 19, 47, 23) == {\n    "feasible": True, "hours_used": 17, "hour_slack": 2}',
    'Independent audit of one two-queue plan is O(1). Enumerating all bounded queue combinations is O(AB) for A and B candidate counts; scenario scoring multiplies by the number of scenarios. Reviewer time goes into estimating benefits and validating the constraints, not into the final arithmetic.',
    ['Do not accept a plan whose minimum coverage and capacity cannot both be met.', 'Do not report a fractional allocation as a shift schedule.', 'Do not omit actual-outcome follow-up after choosing a model-based plan.'],
    ['data-science/decision-objective-and-action-unit','data-science/constraint-feasibility-and-slack','data-science/integer-allocation-and-relaxation-gap','data-science/scenario-stress-and-decision-regret'])

assert len(lessons) == len(new_paths) == 5
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
               featured=False, sort_order=12200 + index, status='published', published_at=stamp,
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
module_paths = {path for module in hub['data']['modules'] for path in module['lessons']}
if not set(tutorial_paths).issubset(module_paths):
    hub['data']['modules'].insert(-1, {'title':'Decision optimization and allocation',
                                      'summary':'Translate estimates into feasible actions, whole-number plans and stress-tested choices.',
                                      'lessons':tutorial_paths})
apply_module = next(module for module in hub['data']['modules'] if module['title'] == 'Apply your knowledge')
if project_path not in apply_module['lessons']:
    apply_module['lessons'].append(project_path)
if '<h2>Decision optimization and allocation</h2>' not in hub['body']:
    hub['body'] += ('<h2>Decision optimization and allocation</h2>' + links(tutorial_paths)
                    + '<h2>Support allocation project</h2>' + links([project_path]))
hub['updated_at'] = stamp

project_hub = by_path[project_hub_path]
if project_path not in project_hub['data']['modules'][0]['lessons']:
    project_hub['data']['modules'][0]['lessons'].append(project_path)
if '<h2>Support allocation project</h2>' not in project_hub['body']:
    project_hub['body'] += '<h2>Support allocation project</h2>' + links([project_path])
project_hub['updated_at'] = stamp

for source, target in [
    ('data-science/precision-budget-and-effective-sample-size', tutorial_paths[0]),
    ('machine-learning/decision-threshold-and-cost', tutorial_paths[0]),
    ('data-science/sensitivity-analysis-and-decision-stability', tutorial_paths[1]),
    ('data-science/support-case-audit-sampling-project', tutorial_paths[1]),
    ('data-science/fulfillment-delay-analysis-project', tutorial_paths[2]),
    ('data-science/derived-metric-uncertainty-and-correlation', tutorial_paths[3]),
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
print(json.dumps({'new_articles':len(lessons), 'new_projects':1, 'crosslinks_from_existing':6}))
