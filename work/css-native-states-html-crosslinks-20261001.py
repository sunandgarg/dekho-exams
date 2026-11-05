"""Connect HTML controls and media lessons to native-state CSS decisions."""

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
    "html/file-upload-form": ["css/file-selector-button-native"],
    "html/readonly-vs-disabled": ["css/read-only-control-state"],
    "html/radio-checkbox": ["css/indeterminate-checkbox-state"],
    "html/button-type-default": ["css/default-submit-selector"],
    "html/required-vs-aria-required": ["css/required-optional-control-state"],
    "html/placeholder-vs-label": ["css/placeholder-text-contrast"],
    "html/lists-and-definitions": ["css/nth-child-filtered-siblings"],
    "html/video-captions": ["css/caption-cue-presentation"],
}

for source, targets in crosslinks.items():
    row = by_path[source]
    assert row["type"] == "article"
    assert all(target in by_path for target in targets)
    assert all(f'href="/{target}"' not in row["body"] for target in targets)
    row["body"] += "<h2>Related CSS decisions</h2><ul>" + "".join(
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
