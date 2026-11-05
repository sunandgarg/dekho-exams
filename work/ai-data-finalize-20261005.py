"""Connect the AI & Data lessons to project, Python and evaluation routes."""
import datetime
import html
import json
import pathlib

root = pathlib.Path(__file__).resolve().parents[1]
fixture = root / 'src/data/fixtures.json'
rows = json.loads(fixture.read_text())
by_path = {row['path']: row for row in rows}
stamp = datetime.datetime.now(datetime.UTC).isoformat()

project_hubs = [
    ('data-science/data-science-for-beginners/project',
     'Practice data science with a checked receipt-review report.',
     'Begin with one submission per row. The project asks for a rate that another analyst can reproduce from a pinned extract, with late outcomes and join multiplicity visible rather than discarded.',
     ['data-science/practice-project', 'data-science/dataset-grain-and-join-cardinality',
      'data-science/missing-data-policy', 'data-science/metric-denominator-and-cohort',
      'data-science/reproducible-analysis-snapshot']),
    ('machine-learning/machine-learning-tutorial/project',
     'Practice model evaluation against an operational review limit.',
     'Build a receipt-triage baseline before fitting a model. The project requires a prediction clock, grouped development folds, a future holdout and an action threshold tied to analyst capacity.',
     ['machine-learning/practice-project', 'machine-learning/prediction-time-feature-availability',
      'machine-learning/group-and-time-validation', 'machine-learning/leakage-safe-preprocessing-pipeline',
      'machine-learning/decision-threshold-and-cost', 'machine-learning/probability-calibration']),
]
for path, summary, introduction, links in project_hubs:
    row = by_path[path]
    row['summary'] = summary
    row['body'] = '<p>' + introduction + '</p><h2>Project and required concepts</h2><ul>' + ''.join(
        '<li><a href="/' + target + '">' + html.escape(by_path[target]['title']) + '</a></li>'
        for target in links) + '</ul><h2>Completion standard</h2><p>Submit the runnable analysis, its input and version manifest, the outcome counts, failure-case checks and a short decision note. Keep the final evaluation partition separate from development choices.</p>'
    row['data']['content_format'] = 'html'
    row['data']['seo_ready'] = True
    row['updated_at'] = stamp

cross_links = {
    'data-science/dataset-grain-and-join-cardinality': ['python/pandas-join-cardinality', 'python/pandas-null-joins'],
    'data-science/missing-data-policy': ['python/pandas-nullable', 'python/pandas-groupby-missing-key'],
    'data-science/exploratory-analysis-without-peeking': ['python/pandas-groupby', 'python/numpy-finite-gate'],
    'data-science/metric-denominator-and-cohort': ['python/datetime-boundaries', 'python/pandas-groupby'],
    'data-science/reproducible-analysis-snapshot': ['python/bounded-csv'],
    'machine-learning/prediction-time-feature-availability': ['python/pandas-asof-joins'],
    'machine-learning/group-and-time-validation': ['prompt-engineering/evaluation-data-leakage'],
    'machine-learning/leakage-safe-preprocessing-pipeline': ['python/pandas-categorical'],
    'machine-learning/decision-threshold-and-cost': ['prompt-engineering/fairness-slice-testing'],
}
for source, targets in cross_links.items():
    row = by_path[source]
    row['body'] += '<h2>Connected implementation</h2><ul>' + ''.join(
        '<li><a href="/' + target + '">' + html.escape(by_path[target]['title']) + '</a></li>'
        for target in targets) + '</ul>'
    row['data']['related'].extend({'path': target, 'title': by_path[target]['title']} for target in targets)
    row['updated_at'] = stamp

backlinks = [
    ('python/pandas-join-cardinality', 'data-science/dataset-grain-and-join-cardinality'),
    ('python/pandas-nullable', 'data-science/missing-data-policy'),
    ('python/pandas-groupby', 'data-science/metric-denominator-and-cohort'),
    ('python/pandas-asof-joins', 'machine-learning/prediction-time-feature-availability'),
    ('prompt-engineering/evaluation-data-leakage', 'machine-learning/group-and-time-validation'),
    ('prompt-engineering/fairness-slice-testing', 'machine-learning/decision-threshold-and-cost'),
]
for source, target in backlinks:
    row = by_path[source]
    row['body'] += '<p><strong>Apply this boundary:</strong> <a href="/' + target + '">' + html.escape(by_path[target]['title']) + '</a>.</p>'
    row['updated_at'] = stamp

fixture.write_text(json.dumps(rows, ensure_ascii=False, indent=2) + '\n')
print(json.dumps({'project_hubs': len(project_hubs), 'outbound_crosslinks': sum(map(len, cross_links.values())), 'backlinks': len(backlinks)}))
