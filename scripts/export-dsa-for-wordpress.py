"""Build a reviewable, draft-only WordPress import for the DSA curriculum."""

import copy
import json
from pathlib import Path

root = Path(__file__).resolve().parents[1]
fixtures = json.loads((root / "src/data/fixtures.json").read_text())
selected = [
    copy.deepcopy(entry)
    for entry in fixtures
    if entry["path"].startswith("dsa/")
    or entry["path"].startswith("quizzes/dsa-")
    or entry["path"] == "authors/aitrove-editorial"
]
paths = {entry["path"] for entry in selected}
assert len(paths) == len(selected), "duplicate DSA path"
assert "dsa/dsa-tutorial-learn-data-structures-and-algorithms" in paths
assert "authors/aitrove-editorial" in paths

for entry in selected:
    entry["status"] = "draft"
    entry["data"]["seo_ready"] = False

output = root / "work/aitrove-dsa-import-drafts.json"
output.write_text(json.dumps(selected, ensure_ascii=False, indent=2) + "\n")
print(json.dumps({"records": len(selected), "status": "draft", "output": str(output)}))
