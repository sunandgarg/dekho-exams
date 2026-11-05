"""Add original measurement-quality lessons to the Data Science path."""
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
    'quantity-units-and-conversion-contract',
    'resolution-rounding-and-precision',
    'calibration-drift-and-reference-checks',
    'derived-metric-uncertainty-and-correlation',
    'cold-chain-sensor-audit-project',
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

add('quantity-units-and-conversion-contract',
    'Quantity units and conversion contracts for mixed datasets',
    'A numeric column is not interpretable until its physical quantity, unit and conversion rule are known.', [
    ('Name the quantity before the column', 'A cold-chain export has values labeled temperature, but one device sends Celsius and another Fahrenheit. A value of 46.4 is dangerous if treated as Celsius and ordinary if it means Fahrenheit. Store raw value, raw unit, canonical value, canonical unit, device ID and conversion version. The schema must reject unknown units instead of guessing from magnitude. [[data-science/column-profile-and-domain-constraints|Column profiling]] can reveal suspicious ranges, but it cannot establish the missing meaning by itself.'),
    ('Separate scale conversion from unit conversion', 'Temperature conversion has an offset as well as a scale; multiplying Fahrenheit by five ninths alone is wrong. Length conversion between metres and kilometres uses a factor without an offset. A machine-learning standard score is a statistical transformation, not a physical unit conversion. Do not call both operations normalization in a pipeline log. Preserve the original measurement so a changed unit rule can be replayed and audited.'),
    ('Avoid hidden aggregation across units', 'Summing 47 kilometres and 320 metres as if both values had the same unit produces a plausible-looking but invalid route length. Canonicalize first, then aggregate. For a rate such as kilometres per hour, ensure the numerator and denominator units match the reporting contract. A percent is also unitless but its underlying population and time window still matter. [[data-science/metric-denominator-and-cohort|The metric contract]] supplies those dimensions.'),
    ('Control conversion precision', 'Use a declared decimal representation for externally reported measurements when binary floating-point artifacts would complicate reconciliation. Keep enough intermediate digits for downstream calculations and round once at the published boundary. The converted display should not imply better sensor resolution than the raw reading. [[data-science/resolution-rounding-and-precision|Resolution handling]] is a separate rule from arithmetic correctness.'),
    ('Test reversible fixtures', 'Convert 46.4 degrees Fahrenheit to exactly 8 degrees Celsius under the stated formula, then convert that result back. Test both negative and positive values, since an offset error can hide on one fixture. Reject a bare 46.4 with no unit instead of assigning a default. Record the quantity type too, so pressure values cannot enter the temperature converter.')],
    'from decimal import Decimal\n\ndef to_celsius(raw_value, raw_unit):\n    measured = Decimal(str(raw_value))\n    if raw_unit == "C":\n        return measured\n    if raw_unit == "F":\n        return (measured - Decimal("32")) * Decimal("5") / Decimal("9")\n    raise ValueError(f"unsupported temperature unit: {raw_unit}")\n\nassert to_celsius("46.4", "F") == Decimal("8.0")\nassert to_celsius("-40", "F") == Decimal("-40")',
    'Converting N rows costs O(N) time and O(1) extra memory if processed as a stream; retaining raw and canonical forms costs O(N) storage. Decimal arithmetic has a higher constant cost than binary float, so apply it where the reporting and reconciliation contract warrants it.',
    ['Do not guess a unit from the numeric range.', 'Do not treat a statistical z-score as a physical unit conversion.', 'Do not round each intermediate conversion before calculating a derived metric.'],
    ['data-science/resolution-rounding-and-precision','data-science/calibration-drift-and-reference-checks','data-science/column-profile-and-domain-constraints','data-science/cold-chain-sensor-audit-project'])

add('resolution-rounding-and-precision',
    'Measurement resolution and rounding: avoid invented precision',
    'The number of printed digits is a display choice; the instrument resolution and collection process limit what those digits mean.', [
    ('Read the instrument contract', 'A logger records temperature to the nearest 0.1 degree Celsius. A stored 8.2 does not mean the underlying quantity is known exactly to one decimal place. If nearest rounding is the only error source, a raw reading of 8.2 is consistent with a value near 8.15 through 8.25 under the tie rule. Calibration bias and sensor noise can widen that range. Keep resolution, unit, sensor model and time of measurement beside the value.'),
    ('Round only at the final boundary', 'Converting Fahrenheit to Celsius, applying calibration and averaging six readings each introduce arithmetic steps. Rounding after every step creates extra error and may push a borderline shipment across a temperature limit. Preserve enough working precision, then round the final displayed value under one declared rule. [[data-science/quantity-units-and-conversion-contract|Canonical units]] come before display formatting.'),
    ('Distinguish representation from uncertainty', 'Binary floating point can display a decimal sum with unexpected trailing digits. Decimal arithmetic can make a monetary or recorded-decimal calculation reproducible, but it does not remove measurement uncertainty. A sensor that reports 8.2 with a 0.1-degree display resolution cannot become a 0.001-degree instrument merely because the database stores three decimal places. [[data-science/derived-metric-uncertainty-and-correlation|Derived uncertainty]] needs an explicit model of the inputs.'),
    ('Apply threshold rules to raw and rounded values', 'Suppose an alert fires above 8.25 degrees Celsius. Rounding 8.249 to one decimal gives 8.2 and rounding 8.251 gives 8.3, but the classification should use the unrounded canonical reading if the sensor supports that precision. If the original device reported only one decimal, those three-digit values may be unjustified. Record whether the limit is strict or inclusive and what uncertainty band warrants review.'),
    ('Make a boundary fixture', 'Test values exactly at, just below and just above the operating limit. Include positive and negative numbers because rounding ties can behave differently across languages and libraries. Save the rounding mode with the report version. When an upstream logger changes its resolution, treat that as a measurement-system revision and compare old and new readings before splicing the series.')],
    'from decimal import Decimal, ROUND_HALF_EVEN\n\ndef display_temperature(canonical_celsius, places="0.1"):\n    return Decimal(str(canonical_celsius)).quantize(\n        Decimal(places), rounding=ROUND_HALF_EVEN\n    )\n\nassert display_temperature("8.249") == Decimal("8.2")\nassert display_temperature("8.251") == Decimal("8.3")\nassert display_temperature("8.25") == Decimal("8.2")',
    'Final display rounding is O(1) per fixed-precision reading. Keeping unrounded canonical values and metadata requires O(N) storage for N readings. Decimal operations cost more than float operations, but repeated premature rounding usually poses the larger analytical risk.',
    ['Do not equate extra stored decimals with better sensor accuracy.', 'Do not apply a threshold to a rounded display value unless the decision contract explicitly says to.', 'Do not omit the tie-breaking rounding mode from a reproducible report.'],
    ['data-science/quantity-units-and-conversion-contract','data-science/calibration-drift-and-reference-checks','data-science/derived-metric-uncertainty-and-correlation','data-science/cold-chain-sensor-audit-project'])

add('calibration-drift-and-reference-checks',
    'Calibration drift: compare sensor readings with a reference',
    'A sensor can be precise from reading to reading while remaining systematically wrong against a trusted comparison.', [
    ('Pair readings at the same condition', 'A warehouse temperature logger is checked against a reference probe. Each pair needs the same place, time and stable condition; comparing readings taken 20 minutes apart during a door opening confounds device error with real temperature change. Store sensor ID, reference ID, calibration dates, operating range and the paired values. The signed error is sensor minus reference. [[data-science/reproducible-analysis-snapshot|A frozen snapshot]] keeps the reference and sensor versions together.'),
    ('Separate bias and scatter', 'For each sensor, report mean signed error, spread of paired differences and the maximum absolute deviation across the checked range. A mean near zero can hide positive error at warm temperatures and negative error at cold temperatures, so inspect error by reference range. Repeat checks after repair, relocation or a firmware change. A single offset correction is unjustified if the response curve bends or if error depends on humidity.'),
    ('Look for drift over time', 'A device can pass a check in January and wander by July. Plot paired error against check date for that device, with maintenance events marked. Do not infer a smooth drift line from two points without acknowledging its uncertainty. If data between checks need correction, retain raw readings and create a versioned corrected series with an explicit validity period. [[data-engineering/warehouse-history-asof-join|Historical joins]] help select the correction version valid at the measurement time.'),
    ('Treat a failed check as a data decision', 'If reference comparisons breach the agreed tolerance, identify affected shipments and time ranges. Quarantine uncertain measurements or flag them for sensitivity analysis; do not silently delete them. Confirm whether the reference device was itself in date and appropriate for the range. [[data-science/outlier-investigation-and-quarantine|Outlier triage]] separates a bad device value from a genuine temperature excursion.'),
    ('Use a concrete audit', 'Suppose a sensor reports 7.4, 8.1 and 8.8 degrees while paired reference readings are 7.1, 7.8 and 8.5. Each signed error is +0.3 degree, so an additive offset is plausible over those three points. That is evidence only over the tested range and conditions; a corrective rule still needs review and future checks.')],
    'from statistics import mean\n\ndef paired_sensor_bias(paired_readings):\n    if not paired_readings:\n        raise ValueError("reference pairs required")\n    differences = [sensor_c - reference_c\n                   for sensor_c, reference_c in paired_readings]\n    return {"mean_signed_error": mean(differences),\n            "maximum_absolute_error": max(abs(error) for error in differences)}\n\nresult = paired_sensor_bias([(7.4, 7.1), (8.1, 7.8), (8.8, 8.5)])\nassert round(result["mean_signed_error"], 2) == 0.3',
    'For N paired checks, mean and maximum-error calculation cost O(N) time; this implementation stores O(N) differences for clarity, but a streaming accumulator can use O(1) memory. Range-specific or time-varying calibration needs more observations and a versioned model.',
    ['Do not interpret repeatable readings as accurate without a reference check.', 'Do not fit one offset from a narrow range and apply it everywhere.', 'Do not overwrite raw measurements when applying a later correction.'],
    ['data-science/quantity-units-and-conversion-contract','data-science/resolution-rounding-and-precision','data-science/derived-metric-uncertainty-and-correlation','data-science/cold-chain-sensor-audit-project'])

add('derived-metric-uncertainty-and-correlation',
    'Derived metrics: carry input bounds and shared error into the result',
    'A ratio or difference inherits uncertainty from its inputs; arithmetic precision is not evidence that the result is measured precisely.', [
    ('Start with a named derived quantity', 'A delivery team reports average route speed as distance divided by elapsed time. The estimated route distance is 47.2 kilometres with a conservative input range from 46.9 to 47.5 kilometres; elapsed time is 1.5 hours with a range from 1.4 to 1.6 hours. The point calculation is about 31.47 kilometres per hour. A single printed value hides both input ranges and the assumptions that produced them. [[data-science/quantity-units-and-conversion-contract|Units]] must cancel correctly.'),
    ('Propagate defensible bounds', 'For positive distance and positive time, the smallest possible ratio under separate input bounds uses the smallest distance and largest time; the largest uses the largest distance and smallest time. That gives 46.9/1.6 = 29.3125 and 47.5/1.4 about 33.93 kilometres per hour. This is a conservative arithmetic envelope, not a probability interval. If some combinations cannot occur together, the envelope may be wider than the feasible range.'),
    ('Identify shared error', 'Two distances measured with the same miscalibrated odometer share a systematic component. Averaging them reduces independent noise but not that shared bias. Likewise, subtracting two readings from one sensor may cancel an offset but not a changing slope. Record which inputs share a device, calibration, clock or source table before applying a formula that assumes independent errors. [[data-science/calibration-drift-and-reference-checks|Reference checks]] reveal some shared components.'),
    ('Keep statistical and engineering ranges distinct', 'A confidence interval for a population mean addresses sampling variability under a design. A measurement bound addresses uncertainty in the observed quantities. A derived metric may need both. Do not add their endpoints casually or label the arithmetic envelope a 95% interval. [[data-science/bootstrap-interval-interpretation|Bootstrap interpretation]] is useful only after the independent sampling unit and measurement inputs are specified.'),
    ('Tie uncertainty to the decision', 'If a route policy changes above 32 kilometres per hour, the point value is below the threshold but the arithmetic envelope crosses it. The packet should say the decision is unresolved under current input bounds and identify which measurement would reduce the range most. Rounding to one decimal place cannot make that ambiguity disappear.')],
    'from math import isclose\n\ndef positive_ratio_bounds(numerator_low, numerator_high, denominator_low, denominator_high):\n    if not 0 <= numerator_low <= numerator_high:\n        raise ValueError("numerator bounds must be nonnegative")\n    if not 0 < denominator_low <= denominator_high:\n        raise ValueError("denominator bounds must be positive")\n    return numerator_low / denominator_high, numerator_high / denominator_low\n\nlow_speed, high_speed = positive_ratio_bounds(46.9, 47.5, 1.4, 1.6)\nassert isclose(low_speed, 29.3125)\nassert round(high_speed, 2) == 33.93',
    'Computing one monotone ratio envelope is O(1) time and space. For many correlated inputs or nonlinear formulas, scenario enumeration or simulation costs more and requires an explicit dependence model; a simple endpoint calculation is not enough.',
    ['Do not call an arithmetic input-bound envelope a confidence interval.', 'Do not assume repeated measurements from one device have independent errors.', 'Do not let rounded display digits decide a threshold crossed by plausible input values.'],
    ['data-science/quantity-units-and-conversion-contract','data-science/calibration-drift-and-reference-checks','data-science/sensitivity-analysis-and-decision-stability','data-science/cold-chain-sensor-audit-project'])

add('cold-chain-sensor-audit-project',
    'Project: audit cold-chain sensor measurements before classifying excursions',
    'Build a reproducible shipment-temperature report that preserves raw units, sensor corrections and uncertainty near the operating limit.', [
    ('Create the raw fixture', 'Create 47 shipments and at least two sensor models. Mix Celsius and Fahrenheit payloads, include three duplicate event IDs, one unknown unit, two missing readings and a device whose reference-check error changes after maintenance. Include shipment IDs, sensor IDs, occurrence and known-at times, raw value, raw unit, schema version and calibration version. Preserve all raw rows. [[data-science/quantity-units-and-conversion-contract|The unit contract]] governs canonical conversion.'),
    ('Reconcile and correct', 'Deduplicate by stable event ID, quarantine unknown units and impossible timestamps, and link each sensor reading to the calibration record valid at measurement time. Keep uncorrected and corrected Celsius values separately. Do not apply a July correction to a March reading simply because it is the latest record. [[data-science/calibration-drift-and-reference-checks|Reference checks]] define the valid range and correction review.'),
    ('Classify with an uncertainty band', 'Use an 8.5-degree Celsius operating limit. If a corrected reading plus its bound is at or below the limit, mark it clear; if the reading minus its bound is above the limit, mark it confirmed high; otherwise mark it uncertain. Do not force the uncertain class into either pass or fail. [[data-science/derived-metric-uncertainty-and-correlation|Shared sensor error]] may affect several readings on one shipment.'),
    ('Publish an audit table', 'For each shipment, show accepted reading count, quarantined count, maximum corrected temperature, its uncertainty bound and classification. Include the raw-unit distribution and missing-reading count. A shipment with no valid readings is unknown, not clear. Record whether the metric is any excursion, duration above limit or maximum temperature; those are different decision quantities.'),
    ('Deliver the review packet', 'Save fixture, canonicalization rules, calibration history, corrected-readings table, quarantine ledger, code revision, analysis cutoff and assertions. A peer should reproduce 46.4 degrees Fahrenheit as 8 degrees Celsius, see one borderline reading remain uncertain, and trace any confirmed high classification back to a raw event without a private dashboard.')],
    'def excursion_state(measured_celsius, bound_celsius, limit_celsius=8.5):\n    if bound_celsius < 0:\n        raise ValueError("uncertainty bound must be nonnegative")\n    if measured_celsius + bound_celsius <= limit_celsius:\n        return "clear"\n    if measured_celsius - bound_celsius > limit_celsius:\n        return "confirmed_high"\n    return "uncertain"\n\nassert excursion_state(8.6, 0.3) == "uncertain"\nassert excursion_state(7.9, 0.2) == "clear"\nassert excursion_state(9.1, 0.3) == "confirmed_high"',
    'Classifying N accepted readings costs O(N) time and O(1) state per reading. Shipment aggregation needs O(S) state for S shipments; event deduplication and historical calibration lookup add keyed storage and lookup cost. Manual investigation of uncertain or quarantined records is the dominant operating cost.',
    ['Do not treat an absent sensor reading as evidence that temperature stayed below the limit.', 'Do not apply a calibration correction outside its documented time or measurement range.', 'Do not collapse a boundary-crossing uncertainty band into a certain pass or fail.'],
    ['data-science/quantity-units-and-conversion-contract','data-science/resolution-rounding-and-precision','data-science/calibration-drift-and-reference-checks','data-science/derived-metric-uncertainty-and-correlation'])

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
               featured=False, sort_order=12000 + index, status='published', published_at=stamp,
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
    hub['data']['modules'].insert(-1, {'title':'Measurement quality and uncertainty',
                                      'summary':'Preserve units and resolution, check device bias and carry uncertainty into decisions.',
                                      'lessons':tutorial_paths})
apply_module = next(module for module in hub['data']['modules'] if module['title'] == 'Apply your knowledge')
if project_path not in apply_module['lessons']:
    apply_module['lessons'].append(project_path)
if '<h2>Measurement quality and uncertainty</h2>' not in hub['body']:
    hub['body'] += ('<h2>Measurement quality and uncertainty</h2>' + links(tutorial_paths)
                    + '<h2>Cold-chain audit project</h2>' + links([project_path]))
hub['updated_at'] = stamp

project_hub = by_path[project_hub_path]
if project_path not in project_hub['data']['modules'][0]['lessons']:
    project_hub['data']['modules'][0]['lessons'].append(project_path)
if '<h2>Cold-chain audit project</h2>' not in project_hub['body']:
    project_hub['body'] += '<h2>Cold-chain audit project</h2>' + links([project_path])
project_hub['updated_at'] = stamp

for source, target in [
    ('data-science/column-profile-and-domain-constraints', tutorial_paths[0]),
    ('data-science/reproducible-analysis-snapshot', tutorial_paths[1]),
    ('data-science/outlier-investigation-and-quarantine', tutorial_paths[2]),
    ('data-engineering/warehouse-history-asof-join', tutorial_paths[2]),
    ('data-science/bootstrap-interval-interpretation', tutorial_paths[3]),
    ('data-science/sensitivity-analysis-and-decision-stability', tutorial_paths[3]),
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
