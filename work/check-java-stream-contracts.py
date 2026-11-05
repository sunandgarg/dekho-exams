"""Check Java 8 stream examples, HTML, links and deterministic output."""

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
    "java/stream-single-use", "java/stream-peek-side-effects",
    "java/collectors-tomap-duplicate-key", "java/collectors-groupingby-null-key",
    "java/collectors-tomap-order", "java/stream-parallel-encounter-order",
    "java/stream-reduce-identity", "java/stream-short-circuit",
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


banned = re.compile(r"\b(?:delve|leverage|harness|foster|streamline|showcase|navigate|demystify|robust|crucial|pivotal|multifaceted|bespoke|seamless|dynamic|quintessential|nuanced)\b", re.I)
for path in paths:
    entry = lookup[path]
    body = entry["body"]
    parser = TutorialParser()
    parser.feed(body)
    assert '<h3>Common Mistakes</h3>' in body, path
    assert len(parser.links) >= 4, path
    assert all(target in lookup for target in parser.links), (path, parser.links)
    assert all(item["path"] in lookup for item in entry["data"]["related"]), path
    assert not re.search(r"https?://", body), path
    assert not banned.search(html.unescape(re.sub(r"<[^>]+>", " ", body))), path
    code = re.search(r'<pre><code class="language-java">(.*?)</code></pre>', body, re.S)
    output = re.search(r'<h3>Output</h3><pre><code class="language-text">(.*?)</code></pre>', body, re.S)
    assert code and output, path
    source = html.unescape(code.group(1))
    expected = html.unescape(output.group(1)).strip()
    class_name = re.search(r'public class (\w+)', source).group(1)
    with tempfile.TemporaryDirectory() as tmp:
        source_file = pathlib.Path(tmp) / (class_name + ".java")
        source_file.write_text(source)
        subprocess.run([javac, "--release", "8", "-d", tmp, str(source_file)], check=True, capture_output=True, text=True)
        for runtime in (java, "java"):
            for run_number in range(5):
                run = subprocess.run([runtime, "-cp", tmp, class_name], check=True, capture_output=True, text=True, timeout=15)
                assert run.stdout.strip() == expected, (path, runtime, run_number, run.stdout, expected)
    print("PASS", path, "links", len(parser.links), "runs 10 across JDK 25 and system JDK")

modules = [item for item in lookup["java/java"]["data"]["modules"] if item["title"] == "Stream and collector contracts"]
assert len(modules) == 1 and modules[0]["lessons"] == paths
print("Validated", len(paths), "runnable articles and the Java navigation module")
