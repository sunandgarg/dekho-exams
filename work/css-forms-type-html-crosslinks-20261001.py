"""Connect HTML form and text patterns to CSS state and readability lessons."""

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
    "html/textarea-wrap-submission": ["css/field-sizing-controls"],
    "html/form-help-and-errors": ["css/placeholder-shown-state"],
    "html/aria-invalid-errors": ["css/user-invalid-feedback"],
    "html/autocomplete-and-inputmode": ["css/autofill-state-styling"],
    "html/preformatted-code-and-output": ["css/tab-size-code-blocks"],
    "html/color-scheme-metadata": ["css/forced-color-adjust-exceptions", "css/prefers-contrast-boundaries"],
    "html/select-and-textarea": ["css/field-sizing-controls"],
    "html/headings-and-paragraphs": ["css/balanced-heading-wrap"],
}

for source, targets in crosslinks.items():
    row = by_path[source]
    assert row["type"] == "article"
    assert "<h2>Form and type styling</h2>" not in row["body"]
    assert all(target in by_path for target in targets)
    assert all(f'href="/{target}"' not in row["body"] for target in targets)
    row["body"] += "<h2>Form and type styling</h2><ul>" + "".join(
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
