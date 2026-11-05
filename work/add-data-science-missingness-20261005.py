"""Add a focused missing-observations sequence to Data Science."""
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
    'missingness-mechanisms-and-observation-process',
    'complete-case-selection-and-target-population',
    'train-only-imputation-and-missingness-indicators',
    'missing-not-at-random-sensitivity-analysis',
    'delivery-scan-missingness-project',
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

add('missingness-mechanisms-and-observation-process',
    'Missingness mechanisms: model why a value is absent',
    'Before filling a blank field, find out whether the observation process depends on the event or value being measured.', [
    ('Define the record and the gap', 'A parcel-delivery table expects a final scan for every dispatched parcel. For 47 parcels, nine lack that scan. The missing value may mean an offline scanner, an unintegrated carrier, a parcel still in transit, or a genuine failure to scan. These are different states. Preserve the raw event stream and define a cutoff time before marking a scan absent. A field that is not yet due is not missing in the same way as a lost event.'),
    ('Distinguish mechanisms carefully', 'Missing completely at random means scan absence is independent of observed and unobserved delivery facts. Missing at random means observed facts, such as carrier and depot, can explain the absence after conditioning on them. Missing not at random means the chance of a missing scan still depends on an unobserved outcome, such as whether the parcel was actually late. These are assumptions about a data-generating process, not labels that a null-count query can prove.'),
    ('Measure patterns at the right grain', 'Count eligible records, missing records and missing rates by carrier, depot, calendar day and device version. Keep the denominator in every group. A jump from one missing scan among five parcels to three among six is more operationally meaningful than an unqualified count increase. [[data-science/sampling-frame-and-coverage-error|Coverage errors]] can remove parcels before they reach this table, so inspect upstream counts too.'),
    ('Separate causes from correlates', 'A high missing rate at one depot is evidence for investigation, not proof that the depot caused it. The depot may route a particular carrier whose scan events arrive late. Build a timeline of expected event, ingestion time and analysis cutoff, then ask the system owner about failures and retries. Do not infer an MCAR, MAR or MNAR mechanism from a significance test alone; several mechanisms can fit the same observed data.'),
    ('Write a policy before analysis', 'Record which blank states are recoverable, which rows remain eligible for the decision, and which assumptions require sensitivity analysis. For a service report, a late scan can be treated as pending until a fixed grace window closes. Keep original missingness flags even if a later workflow fills values. [[data-science/complete-case-selection-and-target-population|Complete-case selection]] changes who is represented in the estimate.')],
    'from collections import defaultdict\n\ndef scan_gap_rates(parcel_rows):\n    counts = defaultdict(lambda: {"eligible": 0, "missing": 0})\n    for parcel in parcel_rows:\n        if not parcel["scan_due"]:\n            continue\n        group = counts[parcel["carrier"]]\n        group["eligible"] += 1\n        group["missing"] += parcel["final_scan_at"] is None\n    return {carrier: (count["missing"], count["eligible"])\n            for carrier, count in counts.items()}\n\nparcels = [\n    {"carrier": "North", "scan_due": True, "final_scan_at": None},\n    {"carrier": "North", "scan_due": True, "final_scan_at": "18:42"},\n    {"carrier": "South", "scan_due": False, "final_scan_at": None},\n]\nassert scan_gap_rates(parcels) == {"North": (1, 2)}',
    'A single pass over N parcel rows costs O(N) time and O(G) space for G carrier groups. The result reports observed patterns; it does not establish a missingness mechanism. Event-history joins may dominate runtime when the source stream is large.',
    ['Do not classify a not-yet-due scan as missing.', 'Do not infer a mechanism solely from an observed missing-rate table.', 'Do not overwrite the original absence flag when repairing data.'],
    ['data-science/complete-case-selection-and-target-population','data-science/train-only-imputation-and-missingness-indicators','data-science/missing-not-at-random-sensitivity-analysis','data-science/delivery-scan-missingness-project'])

add('complete-case-selection-and-target-population',
    'Complete-case selection: know whose outcome remains',
    'Deleting incomplete rows can change the population represented by a rate or model, even when the remaining table looks clean.', [
    ('Name the target quantity', 'Suppose the service question is the late-delivery rate for all 47 dispatched parcels. Calculating late share only among parcels with a final scan estimates a rate in the scanned subset unless additional assumptions connect that subset to all dispatched parcels. A clean denominator is not the same as the intended denominator. State the eligible population, the outcome window and the point at which a parcel enters it.'),
    ('Show selection numerically', 'Consider 20 partner parcels, of which eight have a missing final scan, and 27 ordinary parcels, of which one is missing. Dropping incomplete rows retains 12 partner and 26 ordinary parcels. The partner share falls from 20/47, about 42.6%, to 12/38, about 31.6%. Even before estimating lateness, the selected table represents a different mix. Whether the late rate is biased depends on how scan absence relates to lateness within these groups.'),
    ('Use a selection diagram in words', 'A carrier affects both scan availability and delay risk. Conditioning on scan availability by dropping absent rows can change the carrier mix; a further relationship between delay and scanning may remain inside each carrier. Compare retained and excluded rows on variables known for everyone. [[data-science/missingness-mechanisms-and-observation-process|The observation process]] tells you which variables to check. A reweighting calculation needs estimated observation probabilities and positivity, not just a wish to restore the row count.'),
    ('Preserve honest bounds', 'If the binary late status of nine parcels is truly unknown, and seven of the other 38 were late, the overall late rate is between 7/47 and 16/47 without further assumptions: about 14.9% to 34.0%. These wide bounds may still answer whether a service threshold is definitely met. If they straddle the threshold, identify what follow-up evidence would narrow them. [[data-science/missing-not-at-random-sensitivity-analysis|Sensitivity analysis]] can explore narrower, stated assumptions.'),
    ('Report what was removed', 'Publish original eligible count, excluded count, reasons for exclusion, retained group mix and the analysis denominator. Keep excluded records in an audit table. Complete-case analysis can be appropriate for some estimands under some observation processes; it is not automatically valid because the missing fraction is small, nor automatically invalid because the fraction is large.')],
    'def binary_rate_bounds(observed_late, observed_total, missing_total):\n    if min(observed_late, observed_total, missing_total) < 0:\n        raise ValueError("counts must be nonnegative")\n    if observed_late > observed_total:\n        raise ValueError("late count exceeds observed count")\n    eligible = observed_total + missing_total\n    if eligible == 0:\n        raise ValueError("no eligible parcels")\n    return observed_late / eligible, (observed_late + missing_total) / eligible\n\nlower, upper = binary_rate_bounds(7, 38, 9)\nassert round(lower, 3) == 0.149 and round(upper, 3) == 0.340',
    'The bound calculation is O(1) time and space after counts are known. Producing group-level counts from N rows is O(N). Bounds are intentionally broad because no unobserved late statuses are invented.',
    ['Do not present a complete-case rate as the full-population rate without assumptions.', 'Do not hide a changed group mix behind one overall missing percentage.', 'Do not impute a binary outcome as zero simply because its final scan is absent.'],
    ['data-science/missingness-mechanisms-and-observation-process','data-science/train-only-imputation-and-missingness-indicators','data-science/missing-not-at-random-sensitivity-analysis','data-science/delivery-scan-missingness-project'])

add('train-only-imputation-and-missingness-indicators',
    'Train-only imputation and missingness indicators',
    'For prediction, fit replacement values on training data and preserve whether a value was missing at decision time.', [
    ('Decide which time the feature belongs to', 'A parcel-delay model is scored when a parcel leaves the depot. Its features may include a promised transit time and the carrier’s last known operating load. A final-delivery scan is a future outcome and cannot become an input, filled or not. Define the prediction timestamp first. [[machine-learning/leakage-safe-preprocessing-pipeline|Leakage checks]] apply to preprocessing as well as to the model itself.'),
    ('Fit on training observations only', 'Suppose known depot queue times in training are 31, 47 and 55 minutes, while one training row is blank. Their median is 47. Store that value from the training fold, apply it to its blank row, and use the same stored value for validation and later production rows. If the validation batch changes the median, the model has learned from data reserved for evaluation. In cross-validation, each fold needs its own fitted imputer.'),
    ('Keep an absence flag', 'Replacing a blank queue time with 47 makes it numerically identical to a measured 47. A separate flag tells the model which value was substituted. That flag may help if an offline scanner predicts service delays, but it can also encode a temporary incident that disappears after repair. Inspect missing rates by time and group before deploying the feature; the flag is a measured signal, not a causal explanation.'),
    ('Use a baseline and compare', 'Median replacement is a simple baseline, not a universal distribution model. It compresses variation and can distort relationships when many values are absent. Compare a model with and without the missingness flag, and compare both against a policy that removes the affected feature. Evaluate on a time-held-out set representing future operations. [[data-science/complete-case-selection-and-target-population|Row deletion]] changes the evaluated population and may make scores look better for the wrong reason.'),
    ('Store the fitted policy', 'Version the training cutoff, eligible feature columns, imputation statistic and absent-value definition. Apply exactly that transformation at scoring time. If a carrier begins sending an explicit string such as "unknown" instead of a null, normalize it before the stored transformation and measure the rate change. A pipeline prevents accidental refitting but cannot repair a badly defined prediction timestamp.')],
    'from statistics import median\n\ndef fit_queue_time_policy(training_minutes):\n    measured = [minutes for minutes in training_minutes if minutes is not None]\n    if not measured:\n        raise ValueError("no measured training values")\n    return median(measured)\n\ndef transform_queue_time(values, replacement):\n    return [(replacement if value is None else value, value is None)\n            for value in values]\n\nreplacement = fit_queue_time_policy([31, 47, None, 55])\nassert replacement == 47\nassert transform_queue_time([None, 47, 61], replacement) == [\n    (47, True), (47, False), (61, False)]',
    'Computing a median by sorting T measured training values costs O(T log T) time and O(T) memory. Transforming N rows costs O(N) time and output space. Persist the fitted statistic; recalculating it on a test or live batch changes the model contract.',
    ['Do not calculate replacement values from validation or test data.', 'Do not use an outcome that is unavailable at prediction time as a feature.', 'Do not assume an absence flag remains predictive after collection systems change.'],
    ['data-science/missingness-mechanisms-and-observation-process','data-science/complete-case-selection-and-target-population','data-science/missing-not-at-random-sensitivity-analysis','data-science/delivery-scan-missingness-project'])

add('missing-not-at-random-sensitivity-analysis',
    'Missing-not-at-random sensitivity: test what unseen outcomes could change',
    'When missing outcomes may be systematically worse or better, vary that assumption and show when the decision reverses.', [
    ('Start with identified facts', 'For 47 eligible parcels, seven of 38 observed outcomes are late; nine outcomes are missing. The observed late share is 7/38, about 18.4%, but it is not necessarily the all-parcel late rate. The assumption-free range is 7/47 to 16/47. A sensitivity analysis narrows this range only by adding stated assumptions about the unseen parcels. [[data-science/complete-case-selection-and-target-population|The target population]] must stay fixed across scenarios.'),
    ('Define transparent scenarios', 'Consider missing-parcel late shares of 0%, 25%, 50%, 75% and 100%. The implied full-population rate is (7 + 9 × assumed share)/47. These are scenario expectations and need not be integer late-parcel counts; do not portray them as observed outcomes. A carrier investigation could motivate a narrower set. The scenario grid is useful because readers can see precisely how much unobserved lateness the result requires.'),
    ('Find the tipping point', 'Suppose the service target is a late rate below 25%. Solving (7 + 9 × q)/47 < 0.25 gives q < 19/36, about 52.8%. At or above that assumed late share among missing parcels, the target is no longer met under this model. This threshold is easier to review than a claim that the missing data are harmless. It does not estimate q.'),
    ('Stress structure, not only one percentage', 'Missingness may concentrate in the partner carrier, where delay rates differ from ordinary parcels. A single q for every missing record hides that structure. Repeat the calculation by carrier and date with the original eligible denominators, then aggregate with the actual population mix. Also check whether scans simply arrive after the analysis cutoff; an ingestion lag is a measurement issue that can be investigated directly.'),
    ('Connect the result to action', 'If plausible scenarios fall on both sides of the 25% target, report the target as unresolved. Request delayed scan recovery, a manual sample of missing parcels or carrier logs before making a stronger claim. If a decision must be made now, state which conservative rule it follows. [[data-science/missingness-mechanisms-and-observation-process|Mechanism evidence]] informs the scenario range, while the sensitivity calculation shows its consequences.')],
    'def implied_late_rate(observed_late, observed_total, missing_total,\n                      assumed_missing_late_share):\n    if not 0 <= assumed_missing_late_share <= 1:\n        raise ValueError("missing late share must be between zero and one")\n    eligible = observed_total + missing_total\n    if missing_total < 0 or eligible <= 0 or not 0 <= observed_late <= observed_total:\n        raise ValueError("invalid observed counts")\n    return (observed_late + missing_total * assumed_missing_late_share) / eligible\n\nassert round(implied_late_rate(7, 38, 9, 0.5), 3) == 0.245\nassert implied_late_rate(7, 38, 9, 0.75) > 0.25',
    'Each scenario rate costs O(1) time and space; G scenarios cost O(G) time. Stratified scenarios require count aggregation first. No computation can identify the unobserved share from observed records alone without additional assumptions or data.',
    ['Do not call a scenario assumption an estimated fact.', 'Do not report a single imputed rate without showing a range or tipping point.', 'Do not combine groups with different missingness patterns before checking them separately.'],
    ['data-science/missingness-mechanisms-and-observation-process','data-science/complete-case-selection-and-target-population','data-science/train-only-imputation-and-missingness-indicators','data-science/delivery-scan-missingness-project'])

add('delivery-scan-missingness-project',
    'Project: audit missing delivery scans before reporting service rates',
    'Build a reproducible report that separates overdue gaps, selection, prediction-time imputation and unseen-outcome uncertainty.', [
    ('Create a defensible fixture', 'Use 47 eligible dispatched parcels split into 20 partner and 27 ordinary parcels. Mark eight partner and one ordinary final scans as missing after a declared grace window. Give every parcel a carrier, dispatch time, expected scan deadline and known pre-dispatch queue time when available. Keep scan events separate from the parcel dimension so duplicate retries and late arrivals are visible. [[data-science/missingness-mechanisms-and-observation-process|The observation-process lesson]] guides the status definitions.'),
    ('Validate the cohort', 'Assert that exactly 47 parcels enter the target population and that nine are overdue without a final scan. Count missing rates within carrier and day, including both numerator and denominator. Add a not-yet-due parcel to the raw fixture and prove it is excluded from the overdue-gap count. Reconcile the parcel dimension with the event stream before calculating any late rates.'),
    ('Quantify selection', 'Show that complete-case deletion leaves 38 parcels, with partner share 12/38 rather than 20/47. Use seven observed late deliveries as a separate illustrative outcome fixture and calculate the assumption-free late-rate bounds 7/47 and 16/47. Label the observed-subset rate 7/38. [[data-science/complete-case-selection-and-target-population|The selection lesson]] explains why those three numbers answer different questions.'),
    ('Build a leakage-safe prediction baseline', 'For a separate delay-prediction exercise, fit the queue-time replacement from training dates only. Keep a missingness flag and apply the stored value to future dates. Compare validation performance with a feature-omission baseline. Do not feed final scans into a pre-dispatch model. [[data-science/train-only-imputation-and-missingness-indicators|The imputation lesson]] supplies a small executable contract.'),
    ('Publish the decision packet', 'Plot implied all-parcel late rates as the assumed unseen late share moves from zero to one, and mark the 25% service threshold. Record the tipping share, carrier-specific gap rates, event cutoff, code revision, excluded counts and unresolved data-quality questions. After late events arrive, compare their outcomes with the assumptions and update the next report. [[data-science/missing-not-at-random-sensitivity-analysis|Sensitivity analysis]] remains visible alongside the point estimate.')],
    'def report_counts(eligible_parcels, overdue_missing, observed_late):\n    observed = eligible_parcels - overdue_missing\n    if observed <= 0 or overdue_missing < 0 or not 0 <= observed_late <= observed:\n        raise ValueError("invalid parcel counts")\n    return {"observed": observed,\n            "observed_late_share": observed_late / observed,\n            "all_parcel_lower": observed_late / eligible_parcels,\n            "all_parcel_upper": (observed_late + overdue_missing) / eligible_parcels}\n\npacket = report_counts(47, 9, 7)\nassert packet["observed"] == 38\nassert round(packet["all_parcel_upper"], 3) == 0.340',
    'Count aggregation is O(N) over N parcels, or O(N + E) if E scan events need reconciliation. The final packet calculation is O(1). Review effort should focus on cohort eligibility, timestamps and missingness assumptions rather than the arithmetic.',
    ['Do not mix not-yet-due and overdue scans.', 'Do not use a post-dispatch outcome as a pre-dispatch feature.', 'Do not publish the observed-subset late share as the all-parcel service rate.'],
    ['data-science/missingness-mechanisms-and-observation-process','data-science/complete-case-selection-and-target-population','data-science/train-only-imputation-and-missingness-indicators','data-science/missing-not-at-random-sensitivity-analysis'])

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
               featured=False, sort_order=12300 + index, status='published', published_at=stamp,
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
    hub['data']['modules'].insert(-1, {'title':'Missing observations and valid inference',
                                      'summary':'Diagnose missingness, selection, safe imputation and sensitivity to unseen outcomes.',
                                      'lessons':tutorial_paths})
apply_module = next(module for module in hub['data']['modules'] if module['title'] == 'Apply your knowledge')
if project_path not in apply_module['lessons']:
    apply_module['lessons'].append(project_path)
if '<h2>Missing observations and valid inference</h2>' not in hub['body']:
    hub['body'] += ('<h2>Missing observations and valid inference</h2>' + links(tutorial_paths)
                    + '<h2>Delivery scan audit project</h2>' + links([project_path]))
hub['updated_at'] = stamp

project_hub = by_path[project_hub_path]
if project_path not in project_hub['data']['modules'][0]['lessons']:
    project_hub['data']['modules'][0]['lessons'].append(project_path)
if '<h2>Delivery scan audit project</h2>' not in project_hub['body']:
    project_hub['body'] += '<h2>Delivery scan audit project</h2>' + links([project_path])
project_hub['updated_at'] = stamp

for source, target in [
    ('data-science/missing-data-policy', tutorial_paths[0]),
    ('data-science/sampling-frame-and-coverage-error', tutorial_paths[1]),
    ('machine-learning/leakage-safe-preprocessing-pipeline', tutorial_paths[2]),
    ('data-science/sensitivity-analysis-and-decision-stability', tutorial_paths[3]),
    ('data-science/fulfillment-delay-analysis-project', project_path),
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
