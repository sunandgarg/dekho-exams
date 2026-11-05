"""Small publisher for independently written Data Visualization lessons."""
import datetime
import html
import json
import re
import uuid
from pathlib import Path


def publish(lessons, sort_start, module_groups, incoming, packet_name):
    root = Path(__file__).resolve().parents[1]
    fixture = root / "src/data/fixtures.json"
    packet = root / "work" / packet_name
    rows = json.loads(fixture.read_text())
    by_path = {row["path"]: row for row in rows}
    stamp = datetime.datetime.now(datetime.UTC).isoformat()
    prefix = "data-visualization/"
    hub = prefix + "data-visualization-tutorial"
    new_paths = [prefix + lesson["slug"] for lesson in lessons]
    assert all(path not in by_path for path in new_paths)
    titles = {path: row["title"] for path, row in by_path.items()}
    titles.update(zip(new_paths, (lesson["title"] for lesson in lessons)))
    marker = re.compile(r"\[\[([^|\]]+)\|([^\]]+)\]\]")

    def render(value):
        parts, start = [], 0
        for match in marker.finditer(value):
            parts.append(html.escape(value[start:match.start()]))
            path, label = match.groups()
            if path not in titles:
                raise ValueError(f"broken link: {path}")
            parts.append(f'<a href="/{html.escape(path, quote=True)}">{html.escape(label)}</a>')
            start = match.end()
        return "".join(parts) + html.escape(value[start:])

    def link(path):
        if path not in titles:
            raise ValueError(f"broken related link: {path}")
        return f'<a href="/{html.escape(path, quote=True)}">{html.escape(titles[path])}</a>'

    def body_for(lesson):
        body = f'<p>{render(lesson["summary"])}</p>'
        for heading, paragraph in lesson["sections"]:
            body += f'<h2>{html.escape(heading)}</h2><p>{render(paragraph)}</p>'
        body += '<h2>Worked contract</h2><pre><code class="language-python">' + html.escape(lesson["code"]) + '</code></pre>'
        body += '<h2>Performance and operating cost</h2><p>' + render(lesson["cost"]) + '</p>'
        body += '<h3>Common Mistakes</h3><ul>' + ''.join(f'<li>{render(item)}</li>' for item in lesson["mistakes"]) + '</ul>'
        body += '<h2>Validation drill</h2><p>' + render(lesson["drill"]) + '</p>'
        body += '<h2>Read next</h2><ul>' + ''.join(f'<li>{link(path)}</li>' for path in lesson["related"]) + '</ul>'
        return body

    changed = []
    for offset, lesson in enumerate(lessons):
        path = new_paths[offset]
        body = body_for(lesson)
        row = {
            "id": str(uuid.uuid5(uuid.NAMESPACE_URL, "https://aitrove.in/" + path)),
            "type": "article", "path": path, "title": lesson["title"],
            "summary": lesson["summary"], "body": body, "category": "AI & Data",
            "subject": "data-visualization", "difficulty": "Advanced",
            "tags": ["ai-data", "data-visualization", "tutorial"], "potd_date": None,
            "featured": False, "sort_order": sort_start + offset, "status": "published",
            "published_at": stamp, "created_at": stamp, "updated_at": stamp,
            "data": {"subject_root": hub, "section_path": hub,
                     "content_format": "html", "seo_ready": True, "kind": "tutorial",
                     "reading_minutes": max(6, round(len(re.sub('<[^>]+>', ' ', body).split()) / 180)),
                     "author_path": "authors/aitrove-editorial",
                     "verification_suite": "Executable standard-library example and editorial review",
                     "related": [{"path": target, "title": titles[target]}
                                 for target in lesson["related"]]},
        }
        rows.append(row)
        by_path[path] = row
        changed.append(row)

    for path in (hub, "data-visualization"):
        row = by_path[path]
        for heading, offsets in module_groups:
            targets = [new_paths[offset] for offset in offsets]
            row["data"]["modules"].append({"title": heading, "lessons": targets})
            row["body"] += f'<h2>{html.escape(heading)}</h2><ul>' + ''.join(
                f'<li>{link(target)}</li>' for target in targets) + '</ul>'
        row["updated_at"] = stamp
        changed.append(row)

    for source, offsets in incoming.items():
        row = by_path[prefix + source]
        targets = [new_paths[offset] for offset in offsets]
        row["body"] += '<h2>Continue this visualization path</h2><ul>' + ''.join(
            f'<li>{link(target)}</li>' for target in targets) + '</ul>'
        related = row["data"].setdefault("related", [])
        known = {value["path"] for value in related}
        related.extend({"path": target, "title": titles[target]}
                       for target in targets if target not in known)
        row["updated_at"] = stamp
        changed.append(row)

    heading = '<h2>Continue this visualization path</h2>'
    section_pattern = re.compile(r'(?:<h2>Continue this visualization path</h2><ul>(?:<li><a href="[^"]+">[^<]+</a></li>)+</ul>)+')
    for row in rows:
        if not row["path"].startswith(prefix) or heading not in row.get("body", ""):
            continue
        main, tail = row["body"].split(heading, 1)
        tail = heading + tail
        if not section_pattern.fullmatch(tail):
            raise ValueError(f"unexpected continuation markup: {row['path']}")
        anchors = re.findall(r'(<a href="([^"]+)">[^<]+</a>)', tail)
        distinct = list({href: anchor for anchor, href in anchors}.values())
        consolidated = main + heading + '<ul>' + ''.join(f'<li>{anchor}</li>' for anchor in distinct) + '</ul>'
        if consolidated != row["body"]:
            row["body"] = consolidated
            row["updated_at"] = stamp
            changed.append(row)

    assert len(rows) == len({row["path"] for row in rows})
    assert all(row.get("body", "").count(heading) <= 1 for row in rows
               if row["path"].startswith(prefix))
    changed = list({row["path"]: row for row in changed}.values())
    fixture.write_text(json.dumps(rows, ensure_ascii=False, indent=2) + "\n")
    packet.write_text(json.dumps(changed, ensure_ascii=False, indent=2) + "\n")
    print(f"Added {len(lessons)} lessons; publication packet has {len(changed)} entries: {packet}")
