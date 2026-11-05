"""Archive the original SQL seed as JSON for historical comparison.

The active src/data/fixtures.json is the read-only export of published records
from the former prototype, rebranded for AITrove. Running this script does not
replace that active snapshot.
"""
import json
import re
from pathlib import Path

root = Path(__file__).resolve().parents[1]
sql = (root / "drizzle/migrations/0000_cms_entries_and_roles.sql").read_text()
fields = ["type", "path", "title", "summary", "body", "category", "subject", "difficulty", "tags", "data", "potd_date", "status", "featured", "sort_order"]


def split_row(line):
    values, current = [], []
    quoted = False
    i = 1
    while i < len(line) - 1:
        char = line[i]
        if char == "'":
            if quoted and i + 1 < len(line) and line[i + 1] == "'":
                current.append("''")
                i += 2
                continue
            quoted = not quoted
        if char == "," and not quoted:
            values.append("".join(current).strip())
            current = []
        else:
            current.append(char)
        i += 1
    values.append("".join(current).strip())
    return values


def decode(raw):
    if raw.lower() == "null":
        return None
    if raw.lower() in {"true", "false"}:
        return raw.lower() == "true"
    if re.fullmatch(r"-?\d+", raw):
        return int(raw)
    if raw.lower().startswith("current_date"):
        return None
    escaped = raw.startswith("E'")
    text = raw[2:-1] if escaped else raw[1:-1]
    text = text.replace("''", "'")
    if escaped:
        text = text.replace("\\n", "\n").replace("\\t", "\t").replace("\\\\", "\\")
    return text

rows = []
for line in sql.splitlines():
    line = line.strip()
    if not line.startswith("('"):
        continue
    values = split_row(line.rstrip(",;"))
    if len(values) != len(fields):
        raise ValueError(f"Expected {len(fields)} values, got {len(values)}: {line[:90]}")
    row = dict(zip(fields, (decode(v) for v in values)))
    row["tags"] = row["tags"].strip("{}").split(",") if row["tags"] != "{}" else []
    row["data"] = json.loads(row["data"])
    row["id"] = f"sample-{len(rows) + 1}"
    row["created_at"] = row["updated_at"] = "2026-01-01T00:00:00Z"
    row["published_at"] = "2026-01-01T00:00:00Z"
    rows.append(row)

out = root.parent / "archived-sql-fixtures.json"
out.write_text(json.dumps(rows, ensure_ascii=False, indent=2) + "\n")
print(f"Wrote {len(rows)} original sample records to {out}")
