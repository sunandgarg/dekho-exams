"""Connect HTML document patterns to newly added CSS behavior lessons."""

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
    "html/language-and-direction": ["css/hyphenation-and-language", "css/writing-mode-layout"],
    "html/anchors-and-paths": ["css/scroll-target-offsets"],
    "html/data-tables": ["css/cursor-affordances"],
    "html/incident-evidence-project": ["css/fragmentation-break-inside"],
    "html/form-help-and-errors": ["css/pointer-events-targeting"],
}

for source, targets in crosslinks.items():
    row = by_path[source]
    assert row["type"] == "article"
    assert "<h2>Further CSS decisions</h2>" not in row["body"]
    assert all(target in by_path for target in targets)
    row["body"] += "<h2>Further CSS decisions</h2><ul>" + "".join(
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
