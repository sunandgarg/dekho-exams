"""Export the local Web Development expansion as reviewable WordPress drafts."""

import copy
import json
from pathlib import Path

root = Path(__file__).resolve().parents[1]
entries = json.loads((root / "src/data/fixtures.json").read_text())
selected = [copy.deepcopy(entry) for entry in entries if entry["path"].startswith("web-tech/")
            or entry["path"].startswith("quizzes/web-development-")
            or entry["path"] == "authors/aitrove-editorial"]
assert len(selected) == 572, len(selected)
assert len({entry["path"] for entry in selected}) == len(selected)
for entry in selected:
    entry["status"] = "draft"
    entry["data"]["seo_ready"] = False
output = root / "work/aitrove-web-development-import-drafts.json"
output.write_text(json.dumps(selected, ensure_ascii=False, indent=2) + "\n")
print(json.dumps({"records": len(selected), "status": "draft", "output": str(output)}))
