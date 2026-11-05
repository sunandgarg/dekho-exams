"""Validate the asynchronous Java lesson packet and exercise deterministic contracts."""
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
    "completablefuture-thencompose-dependent-stage",
    "completablefuture-thencombine-independent",
    "completablefuture-applytoeither-race",
    "completablefuture-exceptionallycompose-fallback",
    "completablefuture-join-versus-get",
    "completablefuture-cancellation-is-status",
    "executor-invokeall-bounded-batch",
    "executor-invokeany-first-success",
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
            assert len(attributes) == 1 and attributes[0] == ("class", "language-java")
            assert self.stack[-1] == "pre"
        else:
            assert not attributes, attributes
        self.stack.append(tag)

    def handle_endtag(self, tag):
        assert self.stack and self.stack.pop() == tag, tag

for slug in slugs:
    entry = lookup["java/" + slug]
    body = entry["body"]
    assert body.startswith("<p>")
    assert body.count("<h3>Common Mistakes</h3>") == 1
    assert "http://" not in body and "https://" not in body
    assert entry["data"]["section_path"] == "java/advanced-java"
    parser = LessonStructure()
    parser.feed(body)
    assert not parser.stack, slug

quiz = lookup["quizzes/java-async-contracts"]
assert len(quiz["data"]["questions"]) == 8
for question in quiz["data"]["questions"]:
    assert 0 <= question["answer"] < len(question["options"]) == 3
    assert len(set(question["options"])) == 3
reachable = {target for entry in entries if entry["path"].startswith("java/") and entry["type"] == "subject"
             for module in entry["data"]["modules"] for target in module["lessons"]}
assert set("java/" + slug for slug in slugs) <= reachable
assert quiz["path"] in reachable

with tempfile.TemporaryDirectory(prefix="aitrove-java-async-") as folder:
    directory = Path(folder)
    for slug in slugs:
        entry = lookup["java/" + slug]
        blocks = re.findall(r'<pre><code class="language-java">([\s\S]*?)</code></pre>', entry["body"])
        assert len(blocks) == 1, slug
        source = html.unescape(blocks[0])
        class_name = re.search(r"public class (\w+)", source)
        assert class_name, slug
        source_file = directory / (class_name.group(1) + ".java")
        source_file.write_text(source)
        compiled = subprocess.run(["javac", "--release", str(entry["data"]["java_release"]),
                                   "-cp", str(directory), "-d", str(directory), str(source_file)],
                                  capture_output=True, text=True)
        assert compiled.returncode == 0, (slug, compiled.stderr)

    harness = directory / "JavaAsyncContractsSmoke.java"
    harness.write_text('''import java.util.List;
import java.util.concurrent.Callable;
import java.util.concurrent.CompletableFuture;
import java.util.concurrent.ExecutionException;
import java.util.concurrent.ExecutorService;
import java.util.concurrent.Executors;
import java.util.concurrent.Future;
import java.util.concurrent.TimeUnit;

public class JavaAsyncContractsSmoke {
    public static void main(String[] arguments) throws Exception {
        CompletableFuture<Long> shipment = new CompletableFuture<>();
        CompletableFuture<String> receipt = ShipmentReceiptChain.receipt(
                shipment, identifier -> CompletableFuture.completedFuture("R-" + identifier));
        shipment.complete(47L);
        if (!receipt.join().equals("R-47")) throw new AssertionError("thenCompose");

        CompletableFuture<Long> quote = InsuredShipmentQuote.totalCents(
                CompletableFuture.completedFuture(82L), CompletableFuture.completedFuture(17L));
        if (quote.join() != 99L) throw new AssertionError("thenCombine");

        CompletableFuture<String> east = new CompletableFuture<>();
        CompletableFuture<String> west = new CompletableFuture<>();
        CompletableFuture<String> raced = ReplicaReceiptRace.firstReceipt(east, west);
        west.complete("west-47");
        if (!raced.join().equals("west-47") || east.isCancelled())
            throw new AssertionError("applyToEither ownership");

        CompletableFuture<String> primary = CompletableFuture.failedFuture(
                new ReceiptReplicaFallback.DepotUnavailable("offline"));
        if (!ReceiptReplicaFallback.recover(primary,
                () -> CompletableFuture.completedFuture("backup-82")).join().equals("backup-82"))
            throw new AssertionError("exceptionallyCompose");
        CompletableFuture<String> invalid = CompletableFuture.failedFuture(
                new IllegalArgumentException("invalid"));
        if (!ReceiptReplicaFallback.recover(invalid,
                () -> CompletableFuture.completedFuture("incorrect backup")).isCompletedExceptionally())
            throw new AssertionError("fallback classification");

        CompletableFuture<String> abandoned = new CompletableFuture<>();
        if (!ReceiptCancellationBoundary.abandonResult(abandoned) || !abandoned.isCancelled())
            throw new AssertionError("cancellation state");
        if (!ReceiptWaitBoundary.interruptible(CompletableFuture.completedFuture("ready")).equals("ready"))
            throw new AssertionError("get path");

        ExecutorService executor = Executors.newFixedThreadPool(2);
        try {
            List<Callable<String>> batch = List.of(() -> "first", () -> "second");
            if (!ReceiptBatchDeadline.collect(executor, batch).equals(List.of("first", "second")))
                throw new AssertionError("invokeAll order");
            List<Callable<String>> replicas = List.of(
                    () -> { throw new IllegalStateException("east failed"); }, () -> "west receipt");
            if (!ReceiptReplicaSelection.read(executor, replicas).equals("west receipt"))
                throw new AssertionError("invokeAny success");
        } finally {
            executor.shutdownNow();
            if (!executor.awaitTermination(3, TimeUnit.SECONDS))
                throw new AssertionError("executor did not stop");
        }
        System.out.println("Async local contracts passed");
    }
}''')
    compiled = subprocess.run(["javac", "--release", "17", "-cp", str(directory),
                               "-d", str(directory), str(harness)], capture_output=True, text=True)
    assert compiled.returncode == 0, compiled.stderr
    ran = subprocess.run(["java", "-cp", str(directory), "JavaAsyncContractsSmoke"],
                         capture_output=True, text=True, timeout=30)
    assert ran.returncode == 0, ran.stderr
    assert ran.stdout.strip() == "Async local contracts passed", ran.stdout

print(json.dumps({"compiled": len(slugs), "localSmoke": True, "result": ran.stdout.strip()}))
