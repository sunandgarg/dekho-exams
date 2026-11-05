"""Compile the new channel and management samples and exercise local contracts."""

import html
import json
import re
import subprocess
import tempfile
from html.parser import HTMLParser
from pathlib import Path

root = Path(__file__).resolve().parents[1]
entries = json.loads((root / "src/data/fixtures.json").read_text())
lookup = {entry["path"]: entry for entry in entries}
slugs = [
    "filechannel-write-completion", "filechannel-positioned-exact-read",
    "filechannel-transfer-progress", "filechannel-force-durability",
    "filechannel-lock-region", "filechannel-truncate-recovery",
    "asynchronousfilechannel-buffer-lifetime", "threadmxbean-deadlock-snapshot",
    "threadmxbean-cpu-time-policy", "memorymxbean-heap-snapshot",
    "classloading-mxbean-counts",
]


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
            assert attributes[0][1] == "language-java" and self.stack[-1] == "pre", attributes
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
quiz = lookup["quizzes/java-channels-mxbeans"]
assert len(quiz["data"]["questions"]) == 12
assert {question["answer"] for question in quiz["data"]["questions"]} == {0, 1, 2}
reachable = {target for entry in entries if entry["path"].startswith("java/") and entry["type"] == "subject"
             for module in entry["data"]["modules"] for target in module["lessons"]}
assert set("java/" + slug for slug in slugs) <= reachable
assert quiz["path"] in reachable

with tempfile.TemporaryDirectory(prefix="aitrove-java-channel-mxbean-") as folder:
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
                                   "-cp", str(directory), "-d", str(directory), str(source_file)],
                                  capture_output=True, text=True)
        assert compiled.returncode == 0, (slug, compiled.stderr)

    harness = directory / "JavaChannelManagementSmoke.java"
    harness.write_text('''import java.io.EOFException;
import java.nio.file.Files;
import java.nio.file.Path;
import java.util.Arrays;
import java.util.Comparator;

public class JavaChannelManagementSmoke {
    public static void main(String[] arguments) throws Exception {
        Path staging = Files.createTempDirectory("aitrove-channel-");
        try {
            byte[] payload = new byte[47_000];
            for (int index = 0; index < payload.length; index++) payload[index] = (byte) (index % 83);
            Path manifest = staging.resolve("manifest-47.bin");
            ManifestChannelWriter.create(manifest, payload);
            if (!Arrays.equals(Files.readAllBytes(manifest), payload)) throw new AssertionError("complete write");
            byte[] record = IndexedReceiptReader.read(manifest, 8_192, 64);
            if (!Arrays.equals(record, Arrays.copyOfRange(payload, 8_192, 8_256)))
                throw new AssertionError("positioned read");
            boolean shortRead = false;
            try { IndexedReceiptReader.read(manifest, 46_999, 47); }
            catch (EOFException expected) { shortRead = true; }
            if (!shortRead) throw new AssertionError("short record accepted");
            Path copied = staging.resolve("copy-47.bin");
            if (ArchiveChannelTransfer.copy(manifest, copied) != payload.length
                    || !Arrays.equals(Files.readAllBytes(copied), payload))
                throw new AssertionError("transfer");
            Path durable = staging.resolve("durable-47.bin");
            DurableManifestStage.write(durable, payload);
            if (!Arrays.equals(Files.readAllBytes(durable), payload)) throw new AssertionError("forced stage");
            Path marker = staging.resolve("marker.bin");
            HandoffMarkerLock.mark(marker, (byte) 47);
            if (Files.readAllBytes(marker)[0] != 47) throw new AssertionError("lock write");
            ReceiptLogTailRecovery.cutToValidatedBoundary(copied, 8_192);
            if (Files.size(copied) != 8_192) throw new AssertionError("truncate");
            byte[] asynchronous = ArchiveAsyncRead.readOnce(manifest, 8_192, 64);
            if (asynchronous.length == 0 || asynchronous.length > 64 || asynchronous[0] != payload[8_192])
                throw new AssertionError("asynchronous read");
        } finally {
            try (var paths = Files.walk(staging)) {
                paths.sorted(Comparator.reverseOrder()).forEach(path -> {
                    try { Files.delete(path); }
                    catch (java.io.IOException failure) { throw new RuntimeException(failure); }
                });
            }
        }
        if (!PlatformDeadlockSnapshot.threadNames().isEmpty()) throw new AssertionError("unexpected deadlock");
        CurrentThreadCpuSample.nanoseconds().ifPresent(value -> {
            if (value < 0) throw new AssertionError("negative CPU reading");
        });
        HeapUsageSample.Snapshot heap = HeapUsageSample.capture();
        if (heap.usedBytes() < 0 || heap.committedBytes() < heap.usedBytes())
            throw new AssertionError("heap snapshot");
        LoadedClassSample.Counts classes = LoadedClassSample.capture();
        if (classes.current() < 1 || classes.loadedSinceStart() < classes.current())
            throw new AssertionError("class snapshot");
        System.out.println("file channel and JVM management checks passed");
    }
}''')
    compiled = subprocess.run(["javac", "--release", "17", "-cp", str(directory),
                               "-d", str(directory), str(harness)], capture_output=True, text=True)
    assert compiled.returncode == 0, compiled.stderr
    ran = subprocess.run(["java", "-cp", str(directory), "JavaChannelManagementSmoke"],
                         capture_output=True, text=True, timeout=30)
    assert ran.returncode == 0, ran.stderr
    assert ran.stdout.strip() == "file channel and JVM management checks passed", ran.stdout

print(json.dumps({"compiled": len(slugs), "localSmoke": True, "result": ran.stdout.strip()}))
