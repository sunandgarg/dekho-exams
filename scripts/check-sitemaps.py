"""Read-only release check: all sitemap inventories, three live URLs per map and mock SEO."""
import concurrent.futures
import json
import random
import subprocess
import sys
import xml.etree.ElementTree as ET
from email.parser import BytesHeaderParser
from html.parser import HTMLParser
from pathlib import Path
from urllib.parse import urlparse

ORIGIN = "https://dekhoexams.com"
BASE = sys.argv[1] if len(sys.argv) > 1 else ORIGIN
ROOT = Path(__file__).resolve().parent.parent


def get(path):
    raw = subprocess.check_output([
        "curl", "-fsS", "--retry", "2", "--max-time", "30", "-D", "-",
        "-A", "DekhoExams-Sitemap-Check/1.0", BASE + path,
    ])
    head, body = raw.split(b"\r\n\r\n", 1)
    assert head.splitlines()[0].split()[1] == b"200", path
    return BytesHeaderParser().parsebytes(head.split(b"\r\n", 1)[1]), body.decode()


def locs(xml):
    return [node.text for node in ET.fromstring(xml).findall(".//{*}loc")]


class Head(HTMLParser):
    def __init__(self):
        super().__init__()
        self.robots, self.canonical = [], []

    def handle_starttag(self, tag, attrs):
        attrs = dict(attrs)
        if tag == "meta" and attrs.get("name") == "robots":
            self.robots.append(attrs["content"])
        if tag == "link" and attrs.get("rel") == "canonical":
            self.canonical.append(attrs["href"])


def page(path, noindex=False, canonical=None):
    headers, html = get(path)
    head = Head()
    head.feed(html)
    assert head.canonical == [canonical or ORIGIN + path], (path, head.canonical)
    robots = head.robots + [headers.get("X-Robots-Tag", "")]
    assert head.robots and any("noindex" in r for r in robots) == noindex, (path, robots)
    return path


_, robots = get("/robots.txt")
assert "Disallow: /\n" not in robots and f"Sitemap: {ORIGIN}/sitemap.xml" in robots
headers, index = get("/sitemap.xml")
assert "xml" in headers.get("Content-Type", "") and "noindex" not in headers.get("X-Robots-Tag", "")
assert ET.fromstring(index).tag.endswith("}sitemapindex")
maps, urls, samples = {}, set(), []
children = locs(index)
assert children and len(children) == len(set(children))
for child in children:
    assert child.startswith(ORIGIN + "/sitemap-")
    path = urlparse(child).path
    headers, xml = get(path)
    entries = locs(xml)
    assert ET.fromstring(xml).tag.endswith("}urlset")
    assert "xml" in headers.get("Content-Type", "") and "noindex" not in headers.get("X-Robots-Tag", "")
    assert 0 < len(entries) <= 50000 and len(xml.encode()) <= 50 * 1024 * 1024
    assert len(entries) == len(set(entries)) and not urls.intersection(entries), path
    assert all(u.startswith(ORIGIN + "/") and not urlparse(u).query and not urlparse(u).fragment for u in entries)
    urls.update(entries)
    maps[path] = len(entries)
    samples.extend(random.Random(42).sample(entries, min(3, len(entries))))
    print(path, len(entries), file=sys.stderr, flush=True)

local = {u for f in (ROOT / "public").glob("sitemap-*.xml") for u in locs(f.read_text())}
assert local <= urls, sorted(local - urls)[:10]
assert not any(u.endswith(".pdf") or "/print/" in u for u in urls)
samples.append(ORIGIN + "/")
for exam in ("jee-main", "jee-advanced"):
    hub = "/questions/" + exam + "/mock-tests"
    assert ORIGIN + hub in urls
    samples.append(ORIGIN + hub)
    paper = json.loads((ROOT / "src/data" / (exam + "-papers.json")).read_text())[0]["slug"]
    page(hub + "?paper=" + paper, noindex=True, canonical=ORIGIN + hub)

with concurrent.futures.ThreadPoolExecutor(max_workers=3) as pool:
    checked = list(pool.map(page, sorted({urlparse(u).path for u in samples})))
print(json.dumps({
    "origin": BASE, "unique_urls": len(urls), "sitemaps": maps,
    "local_generated_urls_covered": len(local), "checked_indexable_pages": checked,
    "selected_paper_views_noindex": True,
    "scope": "Full XML and generated-inventory comparison; sampled HTTP page checks, not a full-site crawl.",
}, indent=2))
