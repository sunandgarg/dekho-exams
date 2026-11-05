"""Compile the new Java API examples and exercise their local contracts."""

import html
import json
import re
import subprocess
import tempfile
from html.parser import HTMLParser
from pathlib import Path

root = Path(__file__).resolve().parents[1]
entries = json.loads((root / "src/data/fixtures.json").read_text())
slugs = [
    "file-tree-visitor-failure-policy", "watch-service-key-lifecycle",
    "watch-service-overflow-reconciliation", "directory-stream-close-and-cap",
    "symbolic-link-attribute-boundary", "jdbc-batch-update-counts",
    "jdbc-resultset-null-cursor", "jdbc-generated-key-ownership",
    "jdbc-fetch-size-bounded-read", "processbuilder-command-token-boundary",
    "process-timeout-and-cleanup",
]
lookup = {entry["path"]: entry for entry in entries}


class LessonStructure(HTMLParser):
    allowed = {"p", "h2", "h3", "ul", "li", "strong", "pre", "code", "a"}

    def __init__(self):
        super().__init__()
        self.stack = []

    def handle_starttag(self, tag, attributes):
        assert tag in self.allowed, tag
        if tag == "a":
            assert len(attributes) == 1 and attributes[0][0] == "href", attributes
            assert attributes[0][1].startswith("/") and attributes[0][1][1:] in lookup, attributes
        elif tag == "code":
            assert len(attributes) == 1 and attributes[0][0] == "class", attributes
            assert attributes[0][1].startswith("language-"), attributes
            assert self.stack and self.stack[-1] == "pre", attributes
        else:
            assert not attributes, attributes
        self.stack.append(tag)

    def handle_endtag(self, tag):
        assert self.stack and self.stack.pop() == tag, tag


for slug in slugs:
    entry = lookup["java/" + slug]
    assert entry["body"].startswith("<p>")
    assert entry["body"].count("<h3>Common Mistakes</h3>") == 1
    assert "http://" not in entry["body"] and "https://" not in entry["body"]
    parsed = LessonStructure()
    parsed.feed(entry["body"])
    assert not parsed.stack, slug
quiz = lookup["quizzes/java-files-jdbc-process"]
assert len(quiz["data"]["questions"]) == 12
assert {question["answer"] for question in quiz["data"]["questions"]} == {0, 1, 2}
reachable = {target for entry in entries if entry["path"].startswith("java/") and entry["type"] == "subject"
             for module in entry["data"]["modules"] for target in module["lessons"]}
assert set("java/" + slug for slug in slugs) <= reachable
assert quiz["path"] in reachable

with tempfile.TemporaryDirectory(prefix="aitrove-java-new-") as folder:
    directory = Path(folder)
    for slug in slugs:
        entry = lookup["java/" + slug]
        blocks = re.findall(r'<pre><code class="language-java">([\s\S]*?)</code></pre>', entry["body"])
        assert len(blocks) == 1, slug
        source = html.unescape(blocks[0])
        public_class = re.search(r"public class (\w+)", source)
        assert public_class, slug
        source_file = directory / (public_class.group(1) + ".java")
        source_file.write_text(source)
        compiled = subprocess.run(["javac", "--release", str(entry["data"]["java_release"]),
                                   "-d", str(directory), str(source_file)], capture_output=True, text=True)
        assert compiled.returncode == 0, (slug, compiled.stderr)

    harness = directory / "JavaContractSmoke.java"
    harness.write_text('''import java.io.IOException;
import java.nio.file.*;

public class JavaContractSmoke {
    public static void main(String[] arguments) throws Exception {
        Path staging = Files.createTempDirectory("aitrove-manifest-");
        try {
            Files.writeString(staging.resolve("receipt-47.manifest"), "receipt-47");
            Path depot = Files.createDirectory(staging.resolve("depot"));
            Files.writeString(depot.resolve("receipt-82.manifest"), "receipt-82");
            if (ManifestTreeInventory.scan(staging).size() != 2) throw new AssertionError("tree count");
            if (BoundedManifestListing.list(staging).size() != 1) throw new AssertionError("direct count");
            if (DirectoryReconciliation.snapshot(staging).size() != 2) throw new AssertionError("snapshot count");
            ManifestAttributeGate.requireRegularEntry(staging.resolve("receipt-47.manifest"));
            boolean rejectedDirectory = false;
            try { ManifestAttributeGate.requireRegularEntry(depot); }
            catch (IOException expected) { rejectedDirectory = true; }
            if (!rejectedDirectory) throw new AssertionError("directory accepted");
            for (int receiptNumber = 0; receiptNumber < 47; receiptNumber++) {
                Files.writeString(staging.resolve("batch-" + receiptNumber + ".manifest"), "ready");
            }
            boolean rejectedOverflow = false;
            try { BoundedManifestListing.list(staging); }
            catch (IOException expected) { rejectedOverflow = true; }
            if (!rejectedOverflow) throw new AssertionError("listing cap not enforced");
            boolean rejectedSnapshotOverflow = false;
            try { DirectoryReconciliation.snapshot(staging); }
            catch (IOException expected) { rejectedSnapshotOverflow = true; }
            if (!rejectedSnapshotOverflow) throw new AssertionError("snapshot cap not enforced");
        } finally {
            try (var paths = Files.walk(staging)) {
                paths.sorted(java.util.Comparator.reverseOrder()).forEach(path -> {
                    try { Files.delete(path); }
                    catch (IOException failure) { throw new RuntimeException(failure); }
                });
            }
        }
        Process versionCheck = JavaRuntimeProbe.start();
        if (ChildProcessDeadline.await(versionCheck) != 0) throw new AssertionError("child exit");
        System.out.println("filesystem and process checks passed");
    }
}''')
    compiled = subprocess.run(["javac", "--release", "17", "-cp", str(directory),
                               "-d", str(directory), str(harness)], capture_output=True, text=True)
    assert compiled.returncode == 0, compiled.stderr
    ran = subprocess.run(["java", "-cp", str(directory), "JavaContractSmoke"],
                         capture_output=True, text=True, timeout=20)
    assert ran.returncode == 0, ran.stderr
    assert ran.stdout.strip() == "filesystem and process checks passed", ran.stdout

print(json.dumps({"compiled": len(slugs), "localSmoke": True, "result": ran.stdout.strip()}))
