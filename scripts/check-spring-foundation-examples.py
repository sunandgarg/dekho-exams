"""Compile the Java listings added in the Spring foundations pass."""

import html
import json
import pathlib
import re
import subprocess
import tempfile


ROOT = pathlib.Path(__file__).resolve().parents[1]
CLASSPATH = (ROOT / "work/spring-kit/target/classpath.txt").read_text().strip()
ENTRIES = json.loads((ROOT / "src/data/fixtures.json").read_text())
PATHS = {
    "spring/component-scan-vs-bean",
    "spring/circular-constructor-graph",
    "spring/mvc-request-pipeline",
    "spring/filters-vs-interceptors",
    "spring/security-matcher-order",
    "spring/session-csrf-boundary",
}

checked = set()
for entry in ENTRIES:
    if entry["path"] not in PATHS:
        continue
    blocks = re.findall(
        r'<pre><code class="language-java">(.*?)</code></pre>', entry["body"], re.S
    )
    assert len(blocks) == 1, entry["path"]
    source = html.unescape(blocks[0])
    declared = re.search(r"public\s+class\s+(\w+)", source)
    filename = f"{declared.group(1)}.java" if declared else "Snippet.java"
    with tempfile.TemporaryDirectory() as directory:
        source_file = pathlib.Path(directory) / filename
        source_file.write_text(source)
        result = subprocess.run(
            ["javac", "-cp", CLASSPATH, "-d", directory, str(source_file)],
            capture_output=True,
            text=True,
            timeout=30,
        )
        assert result.returncode == 0, f"{entry['path']}: {result.stderr}"
    checked.add(entry["path"])

assert checked == PATHS, f"Missing snippets: {PATHS - checked}"
print(f"Compiled {len(checked)} Spring Java examples against the source-kit dependencies.")
