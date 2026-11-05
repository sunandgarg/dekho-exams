"""Export practical guides as WordPress review drafts."""
import copy
import json
from pathlib import Path

root = Path(__file__).resolve().parents[1]
rows = json.loads((root / 'src/data/fixtures.json').read_text())
selected = [copy.deepcopy(row) for row in rows
            if row['path'].startswith('guides/') or row['path'] == 'authors/aitrove-editorial']
assert len(selected) == 10, len(selected)
for row in selected:
    row['status'] = 'draft'
    row['data']['seo_ready'] = False
output = root / 'work/aitrove-practical-guides-import-drafts.json'
output.write_text(json.dumps(selected, ensure_ascii=False, indent=2) + '\n')
print(json.dumps({'entries':len(selected), 'status':'draft', 'output':str(output)}))
