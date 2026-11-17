"""Build downloadable timed sets from the existing, sanitised JEE Main chapter records."""
from collections import defaultdict
from hashlib import sha256
from html import unescape
from html.parser import HTMLParser
from pathlib import Path
import gzip
import json
import math
import re

ROOT = Path(__file__).resolve().parents[2]
OUT = ROOT / "src/generated/jee-main-mocks"
SUBJECTS = ("physics", "chemistry", "mathematics")
BRANDING = re.compile(r"exam\s*[-.]?\s*(goal|side)|watermark|jee-figure-pending", re.I)
TEXT_TAGS = set("p div span b strong em i u sub sup br ol ul li table thead tbody tr td th h2 h3 h4".split())


class MathOnly(HTMLParser):
    """Allow text and local MathJax glyphs. Drop a whole question if any element is uncertain."""
    def __init__(self):
        super().__init__()
        self.safe = True
        self.math = False
        self.glyphs = 0

    def handle_starttag(self, tag, attrs):
        attrs = dict(attrs)
        if tag == "svg":
            self.safe &= not self.math and attrs.get("role") == "img"
            self.math = True
            self.glyphs = 0
        elif self.math:
            self.safe &= tag in {"use", "g", "rect"}
            if tag == "use":
                self.safe &= bool(re.fullmatch(r"/jee-archive/math\.svg#MJX-[\w-]+", attrs.get("href", "")))
                self.glyphs += 1
        else:
            self.safe &= tag in TEXT_TAGS
        self.safe &= not any(k.startswith("on") or k in {"style", "src", "xlink:href"} or (k == "href" and tag != "use") for k in attrs)

    def handle_endtag(self, tag):
        if tag == "svg":
            self.safe &= self.math and self.glyphs > 0
            self.math = False


def eligible(q):
    if not (q.get("chapter") and q.get("complete") and q.get("body") and q.get("solution")):
        return False
    if q["kind"] == "mcq":
        if len(q["options"]) != 4 or q.get("choiceKey") not in range(4):
            return False
    elif q["kind"] != "integer" or not isinstance(q.get("numericKey"), (float, int)) or not math.isfinite(q["numericKey"]) or not float(q["numericKey"]).is_integer():
        return False
    markup = " ".join([q["body"], *q["options"], q["solution"]])
    if BRANDING.search(unescape(markup)) or re.search(r"\b(?:figure|diagram|graph)\s+(?:shown|below|above)|as shown in", re.sub("<[^>]*>", " ", markup), re.I):
        return False
    parser = MathOnly()
    parser.feed(markup)
    parser.close()
    return parser.safe and not parser.math


def write_archive_sets(records, paper_ids, old_mock_hashes, old_mock_count):
    """Each canonical question belongs to one paper position or one chapter-only set."""
    dest = OUT / "archive"
    dest.mkdir(exist_ok=True)
    emitted = set()
    used = set()

    def save(name, ids):
        rows = [records[k] for k in ids]
        assert not used.intersection(ids) and len(set(ids)) == len(rows)
        used.update(ids)
        data = json.dumps(rows, ensure_ascii=False, separators=(",", ":"))
        assert not re.search(r'exam\s*(?:side|goal)|watermark|<(?:script|iframe)\b|(?:src|href)="(?:https?:)?//', data, re.I)
        path = dest / f"{name}.{len(rows)}.json.gz"
        path.write_bytes(gzip.compress(data.encode(), compresslevel=6, mtime=0))
        emitted.add(path)

    archive = ROOT / "public/jee-archive"
    for f in sorted((archive / "paper").glob("*.bin")):
        rows = json.loads(gzip.decompress(f.read_bytes()))
        save(f.stem, [paper_ids[f.stem, r["id"]] for r in rows])
    for subject in SUBJECTS:
        extra = sorted(k for k in records.keys() - used if records[k]["subject"] == subject)
        for i in range(0, len(extra), 25):
            save(f"extra-{subject}-{i//25+1:02}", extra[i:i+25])
    assert used == records.keys()
    # Mix scored PYQs into further non-overlapping mocks; individual paper attempts stay intact.
    unique = set(old_mock_hashes)
    pools = defaultdict(list)
    for k, item in records.items():
        if item.get("review") or "jee-figure-pending" in item["solution"]:
            continue
        kind = item["kind"]
        if not (kind == "mcq" and "choiceKey" in item or kind == "integer" and "numericKey" in item and float(item["numericKey"]).is_integer()):
            continue
        digest = fingerprint(item)
        if digest not in unique:
            unique.add(digest)
            pools[item["subject"],kind].append(item)
    n = old_mock_count
    while all(len(pools[s,k]) >= size for s in SUBJECTS for k,size in BLUEPRINT):
        n += 1
        rows = take_mock(pools)
        path = dest / f"combined-{n:02}.75.json.gz"
        path.write_bytes(gzip.compress(json.dumps(rows, ensure_ascii=False, separators=(",",":")).encode(),compresslevel=6,mtime=0))
        emitted.add(path)
    print(f"{n-old_mock_count} additional mixed mocks; {n} in total.")
    for f in dest.glob("*.json.gz"):
        if f not in emitted:
            f.unlink()
    print(f"Archive mocks: {len(paper_ids)} paper positions, {len(records)-len(paper_ids)} additional chapter questions; {len(used)} unique.")

BLUEPRINT = (("mcq", 20), ("integer", 5))

def fingerprint(q):
    return sha256(json.dumps([q["body"], q["options"]], ensure_ascii=False).encode()).digest()

def take_mock(pools):
    rows = []
    for subject in SUBJECTS:
        for kind, size in BLUEPRINT:
            pool = pools[subject, kind]
            rows.extend(pool[:size])
            del pool[:size]
    return rows

def build():
    pools = defaultdict(list)
    seen = set()
    records = {}
    paper_ids = {}
    pdf_keys = json.loads((ROOT / "scripts/jee/main-mock-pdf-keys.json").read_text())
    review = json.loads((ROOT / "scripts/jee/main-pdf-review.json").read_text())
    approved = json.loads((ROOT / "src/data/approved-diagrams.json").read_text())
    def checked(part):
        def img(m):
            src = re.search(r'\bsrc="([^"]+)"', m[0])
            return m[0] if src and src[1] in approved else '<span class="jee-figure-pending">Diagram pending review</span>'
        return re.sub(r"<img\b[^>]*>", img, part, flags=re.I)
    reader = {}
    applied = set()
    for shard in sorted((ROOT / "public/jee-archive/q").glob("*.bin")):
        for q in json.loads(gzip.decompress(shard.read_bytes())).values():
            if not q["chapter"]:
                paper_ids[q["paper"], q["slug"]] = q["canonical"]
                continue
            assert q["complete"] and q["solution"] and q["slug"] not in records
            item = {k: q[k] for k in ("body", "subject", "options", "solution", "kind", "choiceKey", "choiceKeys", "numericKey", "numericRange") if k in q}
            h = fingerprint(q).hex()
            if q["kind"] == "mcq" and "choiceKey" not in item:
                pdf_key = pdf_keys.get(h)
                if pdf_key is not None:
                    assert pdf_key in range(len(q["options"]))
                    item["choiceKey"] = pdf_key
            entry = review.get(h, {})
            key_fields = ("choiceKey", "choiceKeys", "numericKey", "numericRange")
            if entry:
                applied.add(h)
            if entry.get("hold"):
                for field in key_fields:
                    item.pop(field, None)
                item["review"] = "Answer key conflict"
            else:
                key = entry.get("key", {})
                if key:
                    assert len(key) == 1 and set(key) <= set(key_fields)
                    assert not any(k in item and item[k] != v for k,v in key.items())
                    assert all(i in range(len(q["options"])) for i in key.get("choiceKeys", [key["choiceKey"]] if "choiceKey" in key else []))
                    item.update(key)
                if "figures" in entry:
                    pieces = [item["body"], *item["options"]]
                    for slot, part in enumerate(pieces):
                        assert re.findall(r'data-figure="([a-f0-9]{24})"', part) == [
                            fid for fid, _, at in entry["figures"] if at == slot
                        ], "Reviewed diagrams must cover every occurrence in printed order"
                    for fid, image, slot in entry["figures"]:
                        assert re.fullmatch("[a-f0-9]{24}", fid) and re.fullmatch("[a-f0-9]{64}", image)
                        path = "/images/jee-main-reviewed/" + image + ".png"
                        assert (ROOT / "public" / path[1:]).is_file()
                        pattern = r'<span class="jee-figure-pending" data-figure="' + fid + r'">[^<]*</span>'
                        pieces[slot], count = re.subn(pattern, '<img src="' + path + '" alt="Question diagram" loading="lazy">', pieces[slot], count=1)
                        assert count == 1
                    item["body"], item["options"] = pieces[0], pieces[1:]
                restored = {k:v for k,v in item.items() if q.get(k) != v}
                item.update(body=checked(item["body"]), options=[checked(o) for o in item["options"]], solution=checked(item["solution"]))
                # A solution-only figure cannot change the mark.
                if any("jee-figure-pending" in part for part in [item["body"], *item["options"]]):
                    item["review"] = "Diagram pending"
                elif not any(k in item for k in key_fields):
                    item["review"] = "Answer key unavailable"
            changes = {} if entry.get("hold") else restored
            if changes or entry.get("hold"):
                reader[h] = {"hold": True} if entry.get("hold") else changes
            if entry.get("hold"):
                item.update(body=checked(item["body"]), options=[checked(o) for o in item["options"]], solution=checked(item["solution"]))
            records[q["slug"]] = item
            if entry.get("hold") or not eligible(q):
                continue
            digest = fingerprint(q)
            if digest in seen:
                continue
            seen.add(digest)
            pools[q["subject"], q["kind"]].append({k: q[k] for k in ("slug", "subject", "body", "options", "solution", "kind", "choiceKey" if q["kind"] == "mcq" else "numericKey")})
    OUT.mkdir(parents=True, exist_ok=True)
    assert applied == set(review)
    (OUT / "reader.json").write_text(json.dumps(reader, ensure_ascii=False, separators=(",",":")))
    emitted = set()
    count = 0

    def save(name, rows):
        nonlocal count
        data = json.dumps(rows, separators=(",", ":"), ensure_ascii=False).encode()
        assert not BRANDING.search(data.decode()) and not re.search(rb"<(?:img|image|foreignObject|path|script)\b", data, re.I)
        filename = OUT / f"{name}-{len(rows)}.json.gz"
        filename.write_bytes(gzip.compress(data, compresslevel=7, mtime=0))
        emitted.add(filename)
        count += len(rows)

    n = 0
    old_mock_hashes = set()
    while all(len(pools[s,k]) >= size for s in SUBJECTS for k,size in BLUEPRINT):
        n += 1
        rows = take_mock(pools)
        old_mock_hashes.update(fingerprint(q) for q in rows)
        save(f"mock-{n:02}", rows)
    write_archive_sets(records, paper_ids, old_mock_hashes, n)
    for subject in SUBJECTS:
        rows = pools[subject, "mcq"] + pools[subject, "integer"]
        for start in range(0, len(rows), 25):
            save(f"{subject}-{start//25+1:02}", rows[start:start+25])
    assert n > 0 and count == len(seen)
    for old in OUT.glob("*.json.gz"):
        if old not in emitted:
            old.unlink()
    print(f"JEE Main: {count} eligible questions, {n} full mocks, {len(emitted)-n} subject sets.")


if __name__ == "__main__":
    build()
