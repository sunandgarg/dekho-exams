"""Compile and run this batch's published Java fixtures, then validate links."""

import html
from html.parser import HTMLParser
import json
import pathlib
import re
import subprocess
import tempfile

ROOT = pathlib.Path(__file__).resolve().parents[1]
entries = json.loads((ROOT / "src/data/fixtures.json").read_text())
lookup = {entry["path"]: entry for entry in entries}
paths = [
    "java/math-abs-min-value", "java/floor-div-mod-negative",
    "java/bigdecimal-divide-rounding", "java/bigdecimal-setscale-unnecessary",
    "java/biginteger-exact-conversion", "java/double-nan-collection-contracts",
    "java/double-finite-validation", "java/floating-sum-order",
    "java/unsigned-integer-parsing", "java/long-to-double-precision",
]
home = json.loads((ROOT / "work/java-depth/toolchain/metadata.json").read_text())["home"]
java = str(pathlib.Path(home) / "bin/java")
javac = str(pathlib.Path(home) / "bin/javac")


class TutorialParser(HTMLParser):
    allowed = {"p", "h2", "h3", "ul", "li", "strong", "pre", "code", "a"}
    def __init__(self):
        super().__init__()
        self.links = []
    def handle_starttag(self, tag, attrs):
        assert tag in self.allowed, tag
        if tag == "a":
            href = dict(attrs).get("href", "")
            assert href.startswith("/"), href
            self.links.append(href.lstrip("/"))


for path in paths:
    entry = lookup[path]
    body = entry["body"]
    parser = TutorialParser()
    parser.feed(body)
    assert '<h3>Common Mistakes</h3>' in body, path
    assert all(target in lookup for target in parser.links), (path, parser.links)
    assert len(parser.links) >= 3, path
    assert all(item["path"] in lookup for item in entry["data"]["related"]), path
    code = re.search(r'<pre><code class="language-java">(.*?)</code></pre>', body, re.S)
    output = re.search(r'<h3>Output</h3><pre><code class="language-text">(.*?)</code></pre>', body, re.S)
    assert code and output, path
    source = html.unescape(code.group(1))
    expected = html.unescape(output.group(1)).strip()
    class_name = re.search(r'public class (\w+)', source).group(1)
    with tempfile.TemporaryDirectory() as tmp:
        source_file = pathlib.Path(tmp) / (class_name + ".java")
        source_file.write_text(source)
        subprocess.run([javac, "--release", str(entry["data"]["java_release"]), "-d", tmp, str(source_file)], check=True, capture_output=True, text=True)
        run = subprocess.run([java, "-cp", tmp, class_name], check=True, capture_output=True, text=True, timeout=15)
        assert run.stdout.strip() == expected, (path, run.stdout, expected)
    print("PASS", path, "links", len(parser.links))

modules = [item for item in lookup["java/java"]["data"]["modules"] if item["title"] == "Numeric representation boundaries"]
assert len(modules) == 1 and modules[0]["lessons"] == paths
print("Validated", len(paths), "runnable articles and the Java navigation module")
