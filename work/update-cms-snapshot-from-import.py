"""Overlay a successful WordPress import into the public outage fallback."""

import base64
import gzip
import json
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
SNAPSHOT = ROOT / "public/__data/cms-snapshot.txt"


def main() -> None:
    if len(sys.argv) != 2:
        raise SystemExit("Usage: update-cms-snapshot-from-import.py IMPORT.json")
    imported = json.loads(Path(sys.argv[1]).read_text())
    packed = base64.b64decode(SNAPSHOT.read_text().strip())
    rows = json.loads(gzip.decompress(packed))
    by_path = {row[2]: row for row in rows}
    assert len(by_path) == len(rows)
    added = 0
    for entry in imported:
        assert entry["status"] == "published"
        path = entry["path"]
        old = by_path.get(path)
        row = [
            old[0] if old else entry["id"], entry["type"], path,
            entry["title"], entry["summary"], entry["body"],
            entry.get("category"), entry.get("subject"), entry.get("difficulty"),
            entry.get("tags", []), entry.get("data", {}), entry.get("potd_date"),
            entry.get("featured", False), entry.get("sort_order", 0),
            old[14] if old else entry["published_at"], entry["updated_at"],
        ]
        if old:
            old[:] = row
        else:
            rows.append(row)
            added += 1
        by_path[path] = row
    assert len({row[2] for row in rows}) == len(rows)
    encoded = json.dumps(rows, ensure_ascii=False, separators=(",", ":")).encode()
    SNAPSHOT.write_text(base64.b64encode(gzip.compress(encoded, compresslevel=9, mtime=0)).decode())
    print(json.dumps({"imported": len(imported), "added": added, "snapshot_entries": len(rows)}))


if __name__ == "__main__":
    main()
