"""Produce a reviewable WordPress import for the Prompt Engineering curriculum."""

import argparse
import copy
import json
from pathlib import Path

root = Path(__file__).resolve().parents[1]
parser = argparse.ArgumentParser(description=__doc__)
parser.add_argument("--publish", action="store_true", help="retain published status; default is drafts")
parser.add_argument("--output", type=Path, default=root / "work/aitrove-prompt-engineering-import-drafts.json")
args = parser.parse_args()
fixtures = json.loads((root / "src/data/fixtures.json").read_text())
selected = [copy.deepcopy(row) for row in fixtures if row["path"].startswith(("prompt-engineering/", "quizzes/prompt-engineering-")) or row["path"] == "authors/aitrove-editorial"]
paths = {row["path"] for row in selected}
assert len(paths) == len(selected), "duplicate path in Prompt Engineering import"
assert "prompt-engineering/prompt-engineering" in paths and "authors/aitrove-editorial" in paths
if not args.publish:
    for row in selected:
        row["status"] = "draft"
        row["data"]["seo_ready"] = False
output = args.output.resolve()
output.parent.mkdir(parents=True, exist_ok=True)
output.write_text(json.dumps(selected, ensure_ascii=False, indent=2) + "\n")
print(json.dumps({"entries": len(selected), "status": "published" if args.publish else "draft", "output": str(output)}))
