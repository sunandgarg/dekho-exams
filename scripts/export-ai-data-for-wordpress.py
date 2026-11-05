"""Export the local AI & Data curriculum as review drafts."""
import copy
import json
from pathlib import Path

root = Path(__file__).resolve().parents[1]
rows = json.loads((root / 'src/data/fixtures.json').read_text())
selected = [copy.deepcopy(row) for row in rows if row['path'].startswith(('data-science/', 'machine-learning/',
                                                                        'data-engineering/', 'deep-learning/',
                                                                        'natural-language-processing/', 'mlops/',
                                                                        'applied-statistics/', 'retrieval-ai/',
                                                                        'data-visualization/', 'time-series/',
                                                                        'recommendation-systems/', 'causal-inference/',
                                                                        'computer-vision/', 'streaming-analytics/',
                                                                        'graph-machine-learning/', 'anomaly-detection/',
                                                                        'online-experimentation/', 'feature-stores/',
                                                                        'multimodal-ai/', 'privacy-aware-ml/',
                                                                        'knowledge-graphs/', 'geospatial-analytics/',
                                                                        'data-annotation/', 'synthetic-data/'))
            or row['path'] == 'authors/aitrove-editorial']
assert len({row['path'] for row in selected}) == len(selected)
for row in selected:
    row['status'] = 'draft'
    row['data']['seo_ready'] = False
output = root / 'work/aitrove-ai-data-import-drafts.json'
output.write_text(json.dumps(selected, ensure_ascii=False, indent=2) + '\n')
print(json.dumps({'entries': len(selected), 'status': 'draft', 'output': str(output)}))
