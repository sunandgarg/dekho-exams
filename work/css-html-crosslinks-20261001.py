"""Add reciprocal CSS paths to HTML lessons with matching document contracts."""

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
    "html/document-skeleton": ["css/authoring-and-loading"],
    "html/form-help-and-errors": ["css/form-control-states", "css/form-appearance-accent"],
    "html/data-tables": ["css/data-table-layout", "css/audit-table-project"],
    "html/link-vs-button": ["css/link-decoration-states", "css/focus-visible"],
    "html/lists-and-definitions": ["css/list-markers-and-counters"],
    "html/incident-evidence-project": ["css/printable-incident-project", "css/multicolumn-reading"],
    "html/receipt-dashboard-project": ["css/receipt-dashboard-project", "css/grid-template-areas"],
    "html/responsive-images": ["css/image-fit-and-aspect", "css/aspect-ratio-boxes"],
    "html/dialog-and-details": ["css/display-visibility-hidden", "css/overscroll-boundaries"],
}

for source, targets in crosslinks.items():
    row = by_path[source]
    assert row["type"] == "article"
    assert all(target in by_path for target in targets)
    assert "<h2>Style this pattern</h2>" not in row["body"]
    row["body"] += "<h2>Style this pattern</h2><ul>" + "".join(
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
