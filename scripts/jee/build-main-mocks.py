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


def build():
    pools = defaultdict(list)
    seen = set()
    for shard in sorted((ROOT / "public/jee-archive/q").glob("*.bin")):
        for q in json.loads(gzip.decompress(shard.read_bytes())).values():
            if not eligible(q):
                continue
            digest = sha256(json.dumps([q["body"], q["options"]], ensure_ascii=False).encode()).digest()
            if digest in seen:
                continue
            seen.add(digest)
            pools[q["subject"], q["kind"]].append({k: q[k] for k in ("slug", "subject", "body", "options", "solution", "kind", "choiceKey" if q["kind"] == "mcq" else "numericKey")})
    OUT.mkdir(parents=True, exist_ok=True)
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
    while all(len(pools[s, k]) >= size for s in SUBJECTS for k, size in (("mcq", 20), ("integer", 5))):
        n += 1
        rows = []
        for subject in SUBJECTS:
            for kind, size in (("mcq", 20), ("integer", 5)):
                pool = pools[subject, kind]
                rows.extend(pool[:size])
                del pool[:size]
        save(f"mock-{n:02}", rows)
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
