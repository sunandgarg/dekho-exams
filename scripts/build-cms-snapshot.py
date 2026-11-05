"""Build the public runtime fallback from a fresh WordPress Learning Content export.

Usage: python3 scripts/build-cms-snapshot.py /path/to/wordpress-export.xml
Only published learning entries and fields exposed by the public API are retained.
Run again and redeploy after large editorial updates; WordPress stays authoritative.
"""

import base64
import gzip
import json
import sys
import xml.etree.ElementTree as ET
from pathlib import Path


WP = "{http://wordpress.org/export/1.2/}"
OUTPUT = Path(__file__).resolve().parents[1] / "src/data/cms-snapshot.txt"


def stamp(value: str | None) -> str:
    if not value or value.startswith("0000-"):
        raise ValueError("Published entry has no valid WordPress timestamp")
    return value.replace(" ", "T") + "+00:00"


def main() -> None:
    if len(sys.argv) != 2:
        raise SystemExit("Usage: build-cms-snapshot.py WORDPRESS_EXPORT.xml")
    root = ET.parse(sys.argv[1]).getroot()
    rows = []
    paths = set()
    for item in root.findall("./channel/item"):
        if item.findtext(WP + "post_type") != "aitrove_entry":
            continue
        if item.findtext(WP + "status") != "publish":
            continue
        meta = {
            node.findtext(WP + "meta_key"): node.findtext(WP + "meta_value") or ""
            for node in item.findall(WP + "postmeta")
        }
        path = meta.get("_aitrove_path", "").strip("/").lower()
        if not path or path in paths:
            raise ValueError(f"Missing or duplicate public path: {path!r}")
        paths.add(path)
        try:
            data = json.loads(meta.get("_aitrove_data", "") or "{}")
        except json.JSONDecodeError as error:
            raise ValueError(f"Invalid data at {path}: {error}") from error
        if not isinstance(data, dict):
            data = {}
        optional = lambda name: meta.get("_aitrove_" + name) or None
        rows.append([
            item.findtext(WP + "post_id"),
            meta.get("_aitrove_type") or "article",
            path,
            item.findtext("title") or "",
            meta.get("_aitrove_summary", ""),
            meta.get("_aitrove_body", ""),
            optional("category"),
            optional("subject"),
            optional("difficulty"),
            [tag.strip() for tag in meta.get("_aitrove_tags", "").split(",") if tag.strip()],
            data,
            optional("potd_date"),
            meta.get("_aitrove_featured") == "1",
            int(meta.get("_aitrove_sort_order") or 0),
            stamp(item.findtext(WP + "post_date_gmt")),
            stamp(item.findtext(WP + "post_modified_gmt")),
        ])
    if not rows:
        raise ValueError("WordPress export has no published learning entries")
    encoded = json.dumps(rows, ensure_ascii=False, separators=(",", ":")).encode("utf-8")
    OUTPUT.write_text(base64.b64encode(gzip.compress(encoded, compresslevel=9, mtime=0)).decode("ascii"))
    print(f"Wrote {len(rows)} published WordPress entries to {OUTPUT}")


if __name__ == "__main__":
    main()
