"""Connect HTML interaction lessons to new CSS behavior decisions."""

import datetime
import html
import json
from pathlib import Path


root = Path(__file__).resolve().parents[1]
fixture = root / "src/data/fixtures.json"
rows = json.loads(fixture.read_text())
by_path = {row["path"]: row for row in rows}
stamp = datetime.datetime.now(datetime.UTC).isoformat()
crosslinks = {
    "html/dialog-and-details": ["css/interpolate-intrinsic-size", "css/discrete-display-transitions"],
    "html/dialog-vs-popover": ["css/anchor-positioning-overlays", "css/starting-style-entry-transitions"],
    "html/exclusive-details-groups": ["css/interpolate-intrinsic-size"],
    "html/form-help-and-errors": ["css/anchor-positioning-overlays"],
    "html/incident-evidence-project": ["css/scroll-driven-view-timelines"],
}

for source, targets in crosslinks.items():
    row = by_path[source]
    assert row["type"] == "article"
    assert all(target in by_path for target in targets)
    assert all(f'href="/{target}"' not in row["body"] for target in targets)
    row["body"] += "<h2>CSS behavior decisions</h2><ul>" + "".join(
        f'<li><a href="/{html.escape(target)}">{html.escape(by_path[target]["title"])}</a></li>'
        for target in targets
    ) + "</ul>"
    row["data"].setdefault("related", []).extend(
        {"path": target, "title": by_path[target]["title"]} for target in targets
    )
    row["updated_at"] = stamp

fixture.write_text(json.dumps(rows, ensure_ascii=False, indent=2) + "\n")
print(json.dumps({"html_articles": len(crosslinks),
                  "reciprocal_links": sum(map(len, crosslinks.values()))}))
