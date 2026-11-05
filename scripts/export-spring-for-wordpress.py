"""Produce a reviewable Spring draft import from local editorial fixtures."""

import argparse
import copy
import json
from pathlib import Path

root = Path(__file__).resolve().parents[1]
parser = argparse.ArgumentParser(description=__doc__)
parser.add_argument("--output", type=Path, default=root / "work/aitrove-spring-import-drafts.json")
args = parser.parse_args()

fixtures = json.loads((root / "src/data/fixtures.json").read_text())
selected = [
    copy.deepcopy(row)
    for row in fixtures
    if row["path"].startswith(("spring/", "quizzes/spring-"))
    or row["path"] == "authors/aitrove-editorial"
]
paths = {row["path"] for row in selected}
assert len(paths) == len(selected), "duplicate path in Spring import"
assert "spring/spring-boot" in paths and "authors/aitrove-editorial" in paths

for row in selected:
    row["status"] = "draft"
    row["data"]["seo_ready"] = False

output = args.output.resolve()
output.parent.mkdir(parents=True, exist_ok=True)
output.write_text(json.dumps(selected, ensure_ascii=False, indent=2) + "\n")
print(json.dumps({"entries": len(selected), "status": "draft", "output": str(output)}))
