"""Add original survey-weighting lessons to Data Science."""
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
    'survey-inclusion-probabilities-and-base-weights',
    'nonresponse-cell-adjustment-and-positivity',
    'survey-calibration-to-known-margins',
    'weight-extremes-and-effective-sample-size',
    'support-survey-weighting-audit-project',
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

add('survey-inclusion-probabilities-and-base-weights',
    'Survey inclusion probabilities and base weights',
    'A base weight is the inverse of a known selection probability, connecting sampled units to the population they represent.', [
    ('Specify the frame and unit', 'The support-handoff survey frame contains 1,200 eligible cases: 800 standard and 400 partner. The design randomly invites 80 cases from each queue without replacement. The selection probability is 80/800, or 0.10, for a standard case and 80/400, or 0.20, for a partner case. One case is the sampling unit, even if a customer opened multiple cases; customer-level claims would require a different design. [[data-science/sampling-frame-and-coverage-error|Frame coverage]] limits what the weights can represent.'),
    ('Compute inverse selection weights', 'A selected standard case represents 1/0.10, or 10, frame cases. A selected partner case represents 1/0.20, or five. Multiplying each 80-case invitation count by its base weight reconstructs 800 and 400, for a total of 1,200. This is a design check, not evidence that respondents mirror the frame. If cases were sampled with replacement or through multiple routes, their inclusion probabilities need the actual design formula.'),
    ('Distinguish invitation and respondent sets', 'The base weight belongs to an invited unit before response is known. Suppose 48 standard and 32 partner invitees answer. Applying base weights only to those 80 respondents yields represented totals of 480 and 160, which do not sum to the 1,200-case frame. [[data-science/nonresponse-cell-adjustment-and-positivity|Response adjustment]] is a separate step with its own assumptions. Never call the base weight a cure for nonresponse.'),
    ('Keep design metadata at record level', 'Store stratum, frame size, sample size, selection probability, base weight and draw identifier beside every invitation. A report should preserve the date and eligibility version of the frame. If a case became ineligible after drawing, document whether it was an out-of-scope unit or a nonrespondent; those changes alter denominators and adjustment logic. [[data-science/stratified-sampling-and-design-weights|Stratified sampling]] supplies the broader design context.'),
    ('State the estimand', 'A weighted case-level share estimates a proportion among frame cases under the probability design and valid response assumptions. It does not automatically estimate a proportion among unique customers or all support interactions. If one queue has a different outcome definition, reweighting cannot make the measures comparable. [[data-science/survey-construct-and-recall-window|The survey contract]] determines what the item actually measures.')],
    'def invitation_design(frame_counts, invitation_counts):\n    plan = {}\n    for queue, frame_size in frame_counts.items():\n        invited = invitation_counts.get(queue, 0)\n        if frame_size <= 0 or not 0 < invited <= frame_size:\n            raise ValueError("invalid frame or invitation count")\n        probability = invited / frame_size\n        plan[queue] = {"inclusion_probability": probability,\n                       "base_weight": 1 / probability,\n                       "reconstructed_frame": invited / probability}\n    if set(invitation_counts) - set(frame_counts):\n        raise ValueError("invitation queue missing from frame")\n    return plan\n\ndesign = invitation_design({"standard": 800, "partner": 400},\n                           {"standard": 80, "partner": 80})\nassert design["standard"]["base_weight"] == 10\nassert design["partner"]["base_weight"] == 5\nassert sum(item["reconstructed_frame"] for item in design.values()) == 1200',
    'For G sampling strata, computing design weights is O(G) time and output space. Joining weights to I invitation records is O(I) expected time with keyed lookup. Correct variance estimation must also retain the actual sampling design, not only final weights.',
    ['Do not infer a respondent weight directly from selection probability alone.', 'Do not use a case-level base weight for a unique-customer estimand.', 'Do not discard frame and draw metadata after calculating one weighted percentage.'],
    ['data-science/nonresponse-cell-adjustment-and-positivity','data-science/survey-calibration-to-known-margins','data-science/weight-extremes-and-effective-sample-size','data-science/support-survey-weighting-audit-project'])

add('nonresponse-cell-adjustment-and-positivity',
    'Nonresponse adjustment cells and the positivity check',
    'A response adjustment increases respondent weights within a cell to account for invited units that did not answer, conditional on the cell definition.', [
    ('Calculate each response factor', 'Of 80 standard invitees, 48 respond; of 80 partner invitees, 32 respond. Their cell response shares are 0.60 and 0.40. Multiply base weights 10 and five by inverse response shares: a standard respondent gets 10 × 80/48, about 16.67, while a partner respondent gets 5 × 80/32, or 12.5. The adjusted respondent weights sum to 800 standard and 400 partner frame cases. This arithmetic restores known queue totals, not unobserved opinions.'),
    ('State the identifying assumption', 'Within each adjustment cell, response must be sufficiently unrelated to the survey outcome after conditioning on known variables for the adjustment to remove response bias. If customers with confusing handoffs are less likely to answer even within the standard queue, a queue-only adjustment still misses them. Compare respondents and nonrespondents on pre-invitation case features, then consider a better cell definition or follow-up sample. [[data-science/nonresponse-bias-and-follow-up|Nonresponse analysis]] addresses the residual risk.'),
    ('Guard against empty cells', 'A cell with zero respondents has no observed survey outcome to upweight. Division by zero is a symptom of missing support, not a numerical nuisance to patch with an enormous weight. Combine cells only when the groups can reasonably share an outcome relationship, collect more responses, or report the cell as unresolved. Very small response counts produce unstable weights even when they are nonzero. [[data-science/weight-extremes-and-effective-sample-size|Weight diagnostics]] quantify that instability.'),
    ('Separate unit and item nonresponse', 'A completed survey may still skip the handoff-clarity item. The 48 and 32 counts address unit response; an item-level estimate may need another denominator and possibly another adjustment. Do not apply the same factor blindly to every question if eligibility and displayed branches differ. [[data-science/response-options-and-ordinal-coding|Response-state coding]] distinguishes skipped, not displayed and substantive answers.'),
    ('Keep a release table', 'Publish frame counts, invitations, respondents, response shares, base weights and adjusted totals by cell. Verify that response IDs are unique and belong to sampled invitations. Record any cell collapsing and its rationale. If the fielding method changed halfway through, separate the periods before calculating a shared response factor. A weighted estimate is only as defensible as these provenance checks.')],
    'def adjusted_queue_weights(frame_counts, invited_counts, response_counts):\n    weights = {}\n    for queue, frame_size in frame_counts.items():\n        invited = invited_counts[queue]\n        responded = response_counts[queue]\n        if not 0 < responded <= invited <= frame_size:\n            raise ValueError("empty or inconsistent response cell")\n        base_weight = frame_size / invited\n        weights[queue] = base_weight * invited / responded\n    return weights\n\nweights = adjusted_queue_weights({"standard": 800, "partner": 400},\n                                 {"standard": 80, "partner": 80},\n                                 {"standard": 48, "partner": 32})\nassert round(weights["standard"], 2) == 16.67\nassert weights["partner"] == 12.5\nassert round(48 * weights["standard"] + 32 * weights["partner"]) == 1200',
    'For G adjustment cells, factor calculation is O(G) time and output space; attaching weights to R respondents is O(R) expected time. More detailed cells may reduce bias but increase variance and empty-cell risk. Variance estimation must respect both design and adjustment.',
    ['Do not treat adjusted queue totals as proof that opinions are unbiased within queues.', 'Do not generate a weight for a cell with no respondents.', 'Do not confuse survey completion with substantive response to every item.'],
    ['data-science/survey-inclusion-probabilities-and-base-weights','data-science/survey-calibration-to-known-margins','data-science/weight-extremes-and-effective-sample-size','data-science/support-survey-weighting-audit-project'])

add('survey-calibration-to-known-margins',
    'Survey calibration to known population margins',
    'Calibration adjusts respondent weights so weighted totals match trusted frame totals for variables measured on the same population.', [
    ('Identify trustworthy controls', 'The support frame gives 800 standard and 400 partner cases, plus 720 email and 480 phone cases. After a queue-level response adjustment, the weighted respondent data may already match the queue totals but show 600 email and 600 phone. Those channel margins are known independently from the frame and refer to the same 1,200 eligible cases. They can be calibration controls. A margin from a different period or a different case definition cannot be imposed without creating a false match.'),
    ('Iterate proportional adjustments', 'Raking alternates between queue and channel margins. Within a margin, multiply each current cell weight by target total divided by current weighted total. Repeat until both sets of margins are close enough. The process does not create missing queue-channel combinations; if a population cell has no responding support, a numerical algorithm cannot supply its survey answers. [[data-science/nonresponse-cell-adjustment-and-positivity|Positivity]] remains a prerequisite.'),
    ('Monitor convergence and extreme factors', 'Four positive weighted cells start at standard-email 500, standard-phone 300, partner-email 100 and partner-phone 300. Raking them toward the two sets of target margins changes each cell, not just the overall total. Stop when residual errors fall below a declared tolerance and record the iteration count. Oscillation, a large factor or nonconvergence can signal incompatible controls, sparse support or a poor cell structure.'),
    ('State what calibration cannot repair', 'Matching known queue and channel counts helps with imbalance on those variables. It does not prove handoff clarity is independent of response within each queue-channel cell. Nor does it correct biased item wording. Compare weighted and unweighted estimates, report the variables used, and inspect whether one respondent dominates a subgroup. [[data-science/survey-construct-and-recall-window|The item definition]] remains unchanged by weight calibration.'),
    ('Preserve final totals and variance inputs', 'Save base, response-adjusted and calibrated weights separately. Recompute each control margin from released weights and document any residual. The weights alone are insufficient for a design-based interval when invitations were stratified or clustered; preserve strata, draw probabilities and any replicate weights. [[data-science/weight-extremes-and-effective-sample-size|Weight dispersion]] is an additional diagnostic, not a replacement for the survey design.')],
    'def rake_cells(cells, targets, passes=100, tolerance=1e-8):\n    adjusted = [dict(cell) for cell in cells]\n    if sum(targets["queue"].values()) != sum(targets["channel"].values()):\n        raise ValueError("control totals disagree")\n    for _ in range(passes):\n        for dimension in ("queue", "channel"):\n            for category, target in targets[dimension].items():\n                members = [cell for cell in adjusted if cell[dimension] == category]\n                current = sum(cell["weight"] for cell in members)\n                if current <= 0 or target < 0:\n                    raise ValueError("unsupported or invalid margin")\n                factor = target / current\n                for cell in members:\n                    cell["weight"] *= factor\n        errors = [abs(sum(cell["weight"] for cell in adjusted\n                          if cell[dimension] == category) - target)\n                  for dimension in targets for category, target in targets[dimension].items()]\n        if max(errors) < tolerance:\n            return adjusted\n    raise ValueError("raking did not converge")\n\ncells = [{"queue": "standard", "channel": "email", "weight": 500.0},\n         {"queue": "standard", "channel": "phone", "weight": 300.0},\n         {"queue": "partner", "channel": "email", "weight": 100.0},\n         {"queue": "partner", "channel": "phone", "weight": 300.0}]\ntargets = {"queue": {"standard": 800, "partner": 400},\n           "channel": {"email": 720, "phone": 480}}\ncalibrated = rake_cells(cells, targets)\nassert round(sum(cell["weight"] for cell in calibrated if cell["channel"] == "email")) == 720',
    'For I passes, N populated cells and K control categories, this direct implementation costs O(IKN) time and O(N) output space. Production systems use sparse matrices and design-aware calibration routines. Check residuals and weight extremes after convergence.',
    ['Do not calibrate to margins from a different eligible population.', 'Do not assume raking can fill a cell with no respondent data.', 'Do not discard the original design variables once final weights exist.'],
    ['data-science/survey-inclusion-probabilities-and-base-weights','data-science/nonresponse-cell-adjustment-and-positivity','data-science/weight-extremes-and-effective-sample-size','data-science/support-survey-weighting-audit-project'])

add('weight-extremes-and-effective-sample-size',
    'Weight extremes, effective sample size and trimming tradeoffs',
    'Unequal weights can reduce precision and make one response influential; trimming them changes the estimand unless totals are restored and assumptions are reviewed.', [
    ('Read the weight distribution', 'After queue-level nonresponse adjustment, 48 standard respondents each carry weight about 16.67 and 32 partner respondents each carry 12.5. Their total represents 1,200 cases. Show minimum, median, maximum, selected quantiles, sum and the share of total weight held by the largest respondents. A single large weight may indicate a low-response cell, a rare design stratum or a coding error. Investigate its origin before applying an arbitrary cap.'),
    ('Use a weights-only precision diagnostic', 'The Kish effective sample size for 80 respondents with these weights is (sum of weights) squared divided by sum of squared weights, about 78.5. It indicates how much unequal weights alone reduce a simple-random-sample-equivalent count. It ignores clustering, stratification, outcome association and nonresponse model error. [[data-science/precision-budget-and-effective-sample-size|Precision planning]] needs the full design when a confidence interval or target margin is required.'),
    ('Understand the trimming bargain', 'If one respondent has weight 95 while many others carry five, capping 95 at 25 reduces concentration but also removes represented population mass. Raking or another calibration after trimming may restore known totals while moving other weights. Neither step guarantees that the outcome bias improved. Compare estimates and control margins before and after, and explain why the chosen cap is defensible.'),
    ('Inspect estimates by subgroup', 'An overall effective size can hide a partner subgroup represented by only a few respondents. Report unweighted counts and effective size for each published domain. If one domain has no respondents, no amount of scaling creates evidence about its clarity answers. [[data-science/nonresponse-cell-adjustment-and-positivity|Positivity checks]] take priority over a tidy final total.'),
    ('Use design-aware uncertainty', 'A naive standard error computed as if 80 equal-probability independent cases had been sampled misses stratification, finite-population sampling, nonresponse adjustment and calibration. Preserve the sample design and use a suitable survey variance method or documented replicate weights. The effective size is a diagnostic for weight dispersion, not a complete variance estimator. [[data-science/survey-calibration-to-known-margins|Calibration]] can alter the weight distribution again.')],
    'def weight_diagnostics(final_weights):\n    if not final_weights or any(weight <= 0 for weight in final_weights):\n        raise ValueError("positive respondent weights required")\n    total = sum(final_weights)\n    square_total = sum(weight * weight for weight in final_weights)\n    return {"respondents": len(final_weights),\n            "weight_sum": total,\n            "effective_size": total * total / square_total,\n            "largest_share": max(final_weights) / total}\n\nrespondent_weights = [800 / 48] * 48 + [400 / 32] * 32\ndiagnostic = weight_diagnostics(respondent_weights)\nassert diagnostic["respondents"] == 80\nassert 78 < diagnostic["effective_size"] < 79',
    'Diagnostics over R respondents cost O(R) time and O(1) extra space. Sorting for quantiles adds O(R log R) time. A small effective size points to instability, but variance estimation still needs the original design and outcome structure.',
    ['Do not present a weights-only effective size as a complete survey standard error.', 'Do not cap an extreme weight without checking the population margins it represents.', 'Do not hide tiny subgroup respondent counts behind a healthy overall effective size.'],
    ['data-science/survey-inclusion-probabilities-and-base-weights','data-science/nonresponse-cell-adjustment-and-positivity','data-science/survey-calibration-to-known-margins','data-science/support-survey-weighting-audit-project'])

add('support-survey-weighting-audit-project',
    'Project: audit weights for a support-handoff survey',
    'Build a traceable case-level survey estimate from inclusion probabilities through response adjustment, calibration and precision checks.', [
    ('Freeze the population and draw', 'Create a 1,200-case frame with 800 standard and 400 partner handoffs. Randomly invite 80 cases from each queue, retaining draw IDs and known selection probabilities. The survey item asks whether the next step after the handoff was mostly or completely clear. [[data-science/survey-construct-and-recall-window|The measurement contract]] defines the case and the recall window; weights cannot repair a different question.'),
    ('Reconcile respondents and base weights', 'Use 48 standard and 32 partner completed surveys. Verify that every completion belongs to one invitation and that invitation IDs are unique. Base weights are 10 and five, reconstructing the frame from invitations. Response-adjusted weights are 800/48 and 400/32, reconstructing the frame from respondents. Record both stages rather than overwriting one weight column. [[data-science/survey-inclusion-probabilities-and-base-weights|The design lesson]] explains the distinction.'),
    ('Calculate an item estimate with denominators', 'Suppose 28 of 48 standard respondents and 12 of 32 partner respondents choose the top two clarity categories. The unweighted respondent share is 40/80, or 50%. With queue-adjusted weights, the weighted share is about 51.4% across frame cases under the within-queue response assumption. Keep any item skips separate; this fixture assumes all 80 completed respondents provided a substantive answer. [[data-science/nonresponse-cell-adjustment-and-positivity|Response adjustment]] does not guarantee that assumption is true.'),
    ('Test calibration and concentration', 'Add known frame channel totals of 720 email and 480 phone cases. Compare those with weighted respondent channel totals, then rake to both queue and channel controls if the respondent data support every required category. Check residuals and investigate large adjustment factors. Calculate the weights-only effective size and subgroup respondent counts before and after calibration. [[data-science/weight-extremes-and-effective-sample-size|Precision diagnostics]] reveal what a final percentage hides.'),
    ('Publish the audit packet', 'Save frame version, inclusion probabilities, invitation and response counts, item codebook, base and adjusted weights, control totals, calibration tolerance, weight distribution, weighted and unweighted estimates, and a design-aware uncertainty plan. Compare respondents and nonrespondents on known case features. If a cell lacks responses or the channel control is from another population, withhold the calibrated estimate and explain why. [[data-science/survey-calibration-to-known-margins|Calibration]] is a model-assisted adjustment, not validation by itself.')],
    'def queue_weighted_clarity(queue_outcomes, frame_counts):\n    weighted_yes = 0.0\n    represented = 0.0\n    for queue, (top_two, answered) in queue_outcomes.items():\n        if queue not in frame_counts or not 0 <= top_two <= answered or answered == 0:\n            raise ValueError("invalid queue outcomes")\n        respondent_weight = frame_counts[queue] / answered\n        weighted_yes += top_two * respondent_weight\n        represented += answered * respondent_weight\n    if set(queue_outcomes) != set(frame_counts):\n        raise ValueError("missing queue")\n    return weighted_yes / represented\n\nshare = queue_weighted_clarity({"standard": (28, 48), "partner": (12, 32)},\n                               {"standard": 800, "partner": 400})\nassert round(share, 3) == 0.514',
    'Queue aggregation costs O(G) for G groups. Record-level weighting and audit checks cost O(R + I) over R responses and I invitations. Calibration adds iterative passes. The key unresolved risk is outcome-dependent response within adjustment cells.',
    ['Do not use final weights without their frame and adjustment history.', 'Do not report the weighted share as unbiased without the response assumption.', 'Do not publish a calibrated subgroup rate with no respondent support.'],
    ['data-science/survey-inclusion-probabilities-and-base-weights','data-science/nonresponse-cell-adjustment-and-positivity','data-science/survey-calibration-to-known-margins','data-science/weight-extremes-and-effective-sample-size'])

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
               featured=False, sort_order=12700 + index, status='published', published_at=stamp,
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
    hub['data']['modules'].insert(-1, {'title':'Survey weighting and population estimates',
                                      'summary':'Track selection, adjust response, calibrate to controls and inspect precision.',
                                      'lessons':tutorial_paths})
apply_module = next(module for module in hub['data']['modules'] if module['title'] == 'Apply your knowledge')
if project_path not in apply_module['lessons']:
    apply_module['lessons'].append(project_path)
if '<h2>Survey weighting and population estimates</h2>' not in hub['body']:
    hub['body'] += ('<h2>Survey weighting and population estimates</h2>' + links(tutorial_paths)
                    + '<h2>Support survey weighting project</h2>' + links([project_path]))
hub['updated_at'] = stamp

project_hub = by_path[project_hub_path]
if project_path not in project_hub['data']['modules'][0]['lessons']:
    project_hub['data']['modules'][0]['lessons'].append(project_path)
if '<h2>Support survey weighting project</h2>' not in project_hub['body']:
    project_hub['body'] += '<h2>Support survey weighting project</h2>' + links([project_path])
project_hub['updated_at'] = stamp

for source, target in [
    ('data-science/stratified-sampling-and-design-weights', tutorial_paths[0]),
    ('data-science/nonresponse-bias-and-follow-up', tutorial_paths[1]),
    ('data-science/support-handoff-survey-measurement-project', tutorial_paths[2]),
    ('data-science/precision-budget-and-effective-sample-size', tutorial_paths[3]),
    ('data-science/support-handoff-survey-measurement-project', project_path),
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
