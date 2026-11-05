"""Check the AI & Data preview curriculum and its newly written lesson bodies."""
import ast
import collections
import html
from html.parser import HTMLParser
import json
from pathlib import Path
import re

root = Path(__file__).resolve().parents[1]
rows = json.loads((root / 'src/data/fixtures.json').read_text())
by_path = {row['path']: row for row in rows}
assert len(by_path) == len(rows), 'duplicate fixture path'
prefixes = ('data-science/', 'machine-learning/', 'data-engineering/', 'deep-learning/',
            'natural-language-processing/', 'mlops/', 'applied-statistics/', 'retrieval-ai/',
            'data-visualization/', 'time-series/', 'recommendation-systems/', 'causal-inference/',
            'computer-vision/', 'streaming-analytics/', 'graph-machine-learning/', 'anomaly-detection/',
            'online-experimentation/', 'feature-stores/', 'multimodal-ai/', 'privacy-aware-ml/',
            'knowledge-graphs/', 'geospatial-analytics/', 'data-annotation/', 'synthetic-data/')
course_rows = [row for row in rows if row['path'].startswith(prefixes)]
articles = [row for row in course_rows if row['type'] == 'article']
allowed = {'p', 'h2', 'h3', 'ul', 'li', 'strong', 'pre', 'code', 'a'}
banned = re.compile(r'\b(?:delve|leverage|harness|foster|streamline|showcase|navigate|demystify|furthermore|moreover|additionally|robust|crucial|pivotal|multifaceted|bespoke|seamless|dynamic|quintessential|nuanced|powerful|versatile)\b', re.I)

class ReadBody(HTMLParser):
    def __init__(self):
        super().__init__()
        self.tags = []
        self.links = []
        self.codes = []
        self.code_languages = []
        self.in_code = False

    def handle_starttag(self, tag, attrs):
        self.tags.append(tag)
        attributes = dict(attrs)
        if tag == 'a':
            self.links.append(attributes.get('href'))
        if tag == 'code':
            assert attributes.get('class') in ('language-python', 'language-sql'), attributes
            self.code_languages.append(attributes['class'])
            self.in_code = True
            self.codes.append('')

    def handle_endtag(self, tag):
        if tag == 'code':
            self.in_code = False

    def handle_data(self, data):
        if self.in_code:
            self.codes[-1] += data

counts = collections.Counter()
inbound = collections.Counter()
for row in course_rows:
    assert row['data'].get('content_format') == 'html', row['path']
    body = row['body']
    assert not re.search(r'https?://|sample content|Replace this preview lesson', body, re.I), row['path']
    parser = ReadBody()
    parser.feed(body)
    assert set(parser.tags) <= allowed, (row['path'], set(parser.tags) - allowed)
    for href in parser.links:
        assert href and href.startswith('/') and href[1:] in by_path, (row['path'], href)
        inbound[href[1:]] += 1
    if row['type'] == 'article':
        counts[row['subject']] += 1
        words = len(re.sub(r'<[^>]+>', ' ', body).split())
        assert words >= 340, (row['path'], words)
        assert len(parser.links) >= 4, (row['path'], len(parser.links))
        assert '<h3>Common Mistakes</h3>' in body, row['path']
        assert '<h2>Performance and operating cost</h2>' in body, row['path']
        assert len(parser.codes) == 1, row['path']
        if parser.code_languages[0] == 'language-python':
            ast.parse(html.unescape(parser.codes[0]))
        assert not banned.search(re.sub(r'<[^>]+>', ' ', body)), row['path']

for hub_path in ('data-science/data-science-for-beginners', 'machine-learning/machine-learning-tutorial',
                 'data-engineering/data-engineering-tutorial', 'deep-learning/deep-learning-tutorial',
                 'natural-language-processing/nlp-tutorial', 'mlops/mlops-tutorial',
                 'applied-statistics/applied-statistics-tutorial', 'retrieval-ai/retrieval-ai-tutorial',
                 'data-visualization/data-visualization-tutorial', 'time-series/time-series-tutorial',
                 'recommendation-systems/recommendation-systems-tutorial', 'causal-inference/causal-inference-tutorial',
                 'computer-vision/computer-vision-tutorial', 'streaming-analytics/streaming-analytics-tutorial',
                 'graph-machine-learning/graph-machine-learning-tutorial', 'anomaly-detection/anomaly-detection-tutorial',
                 'online-experimentation/online-experimentation-tutorial', 'feature-stores/feature-stores-tutorial',
                 'multimodal-ai/multimodal-ai-tutorial', 'privacy-aware-ml/privacy-aware-ml-tutorial',
                 'knowledge-graphs/knowledge-graphs-tutorial', 'geospatial-analytics/geospatial-analytics-tutorial',
                 'data-annotation/data-annotation-tutorial', 'synthetic-data/synthetic-data-tutorial'):
    hub = by_path[hub_path]
    module_paths = [path for module in hub['data']['modules'] for path in module['lessons']]
    assert len(module_paths) == len(set(module_paths)), hub_path
    assert all(path in by_path for path in module_paths), hub_path
    section = hub_path.split('/')[0] + '/'
    assert {row['path'] for row in articles if row['path'].startswith(section)} == set(module_paths), hub_path

assert all(inbound[row['path']] >= 2 for row in articles), 'article without two incoming links'
print(json.dumps({'passed': True, 'articles': len(articles), 'hubs': len(course_rows) - len(articles),
                  'data_science_articles': counts['data-science'] + counts['data-science-project'],
                  'machine_learning_articles': counts['machine-learning'] + counts['machine-learning-project'],
                  'data_engineering_articles': counts['data-engineering'] + counts['data-engineering-project'],
                  'deep_learning_articles': counts['deep-learning'] + counts['deep-learning-project'],
                  'nlp_articles': counts['natural-language-processing'] + counts['natural-language-processing-project'],
                  'mlops_articles': counts['mlops'] + counts['mlops-project'],
                  'applied_statistics_articles': counts['applied-statistics'] + counts['applied-statistics-project'],
                  'retrieval_ai_articles': counts['retrieval-ai'] + counts['retrieval-ai-project'],
                  'data_visualization_articles': counts['data-visualization'] + counts['data-visualization-project'],
                  'time_series_articles': counts['time-series'] + counts['time-series-project'],
                  'recommendation_systems_articles': counts['recommendation-systems'] + counts['recommendation-systems-project'],
                  'causal_inference_articles': counts['causal-inference'] + counts['causal-inference-project'],
                  'computer_vision_articles': counts['computer-vision'] + counts['computer-vision-project'],
                  'streaming_analytics_articles': counts['streaming-analytics'] + counts['streaming-analytics-project'],
                  'graph_machine_learning_articles': counts['graph-machine-learning'] + counts['graph-machine-learning-project'],
                  'anomaly_detection_articles': counts['anomaly-detection'] + counts['anomaly-detection-project'],
                  'online_experimentation_articles': counts['online-experimentation'] + counts['online-experimentation-project'],
                  'feature_stores_articles': counts['feature-stores'] + counts['feature-stores-project'],
                  'multimodal_ai_articles': counts['multimodal-ai'] + counts['multimodal-ai-project'],
                  'privacy_aware_ml_articles': counts['privacy-aware-ml'] + counts['privacy-aware-ml-project'],
                  'knowledge_graphs_articles': counts['knowledge-graphs'] + counts['knowledge-graphs-project'],
                  'geospatial_analytics_articles': counts['geospatial-analytics'] + counts['geospatial-analytics-project'],
                  'data_annotation_articles': counts['data-annotation'] + counts['data-annotation-project'],
                  'synthetic_data_articles': counts['synthetic-data'] + counts['synthetic-data-project'],
                  'internal_links_to_ai_data': sum(inbound[row['path']] for row in course_rows)}))
