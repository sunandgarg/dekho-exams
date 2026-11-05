"""Compile the new Java lessons and exercise their network-free contracts."""

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
    "http-query-value-encoding", "http-redirect-origin-boundary",
    "http-connect-request-deadlines", "http-streaming-body-size-limit",
    "http-retry-after-budget", "http-cookie-jar-scope",
    "forkjoin-recursive-task-threshold", "forkjoin-owned-pool-lifecycle",
    "forkjoin-managed-blocker-queue", "forkjoin-failure-and-sibling-work",
    "parallel-stream-side-effect-boundary",
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
            assert attributes[0][1] == "language-java", attributes
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
quiz = lookup["quizzes/java-http-forkjoin"]
assert len(quiz["data"]["questions"]) == 12
assert {question["answer"] for question in quiz["data"]["questions"]} == {0, 1, 2}
reachable = {target for entry in entries if entry["path"].startswith("java/") and entry["type"] == "subject"
             for module in entry["data"]["modules"] for target in module["lessons"]}
assert set("java/" + slug for slug in slugs) <= reachable
assert quiz["path"] in reachable

with tempfile.TemporaryDirectory(prefix="aitrove-java-http-forkjoin-") as folder:
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

    harness = directory / "JavaHttpForkJoinSmoke.java"
    harness.write_text('''import java.io.ByteArrayInputStream;
import java.io.IOException;
import java.net.URI;
import java.net.http.HttpClient;
import java.net.http.HttpHeaders;
import java.net.http.HttpRequest;
import java.net.http.HttpResponse;
import java.nio.charset.StandardCharsets;
import java.util.List;
import java.util.Map;
import java.util.Optional;
import java.util.concurrent.ForkJoinPool;
import javax.net.ssl.SSLSession;

public class JavaHttpForkJoinSmoke {
    static class BodyResponse implements HttpResponse<java.io.InputStream> {
        private final byte[] bytes;
        private final int status;
        private final HttpHeaders headers;
        BodyResponse(byte[] bytes, int status, Map<String, List<String>> headers) {
            this.bytes = bytes;
            this.status = status;
            this.headers = HttpHeaders.of(headers, (name, value) -> true);
        }
        public int statusCode() { return status; }
        public HttpRequest request() { return null; }
        public Optional<HttpResponse<java.io.InputStream>> previousResponse() { return Optional.empty(); }
        public HttpHeaders headers() { return headers; }
        public java.io.InputStream body() { return new ByteArrayInputStream(bytes); }
        public Optional<SSLSession> sslSession() { return Optional.empty(); }
        public URI uri() { return URI.create("https://inventory.invalid/items"); }
        public HttpClient.Version version() { return HttpClient.Version.HTTP_1_1; }
    }
    public static void main(String[] arguments) throws Exception {
        URI base = URI.create("https://inventory.invalid/items");
        String query = CatalogQueryUri.search(base, "seal 47 & blue").toString();
        if (!query.endsWith("?q=seal+47+%26+blue")) throw new AssertionError("query");
        if (!ShipmentRedirectGate.sameOrigin(base, URI.create("/next")).toString()
                .equals("https://inventory.invalid/next")) throw new AssertionError("relative redirect");
        boolean crossed = false;
        try { ShipmentRedirectGate.sameOrigin(base, URI.create("https://elsewhere.invalid/next")); }
        catch (IllegalArgumentException expected) { crossed = true; }
        if (!crossed) throw new AssertionError("cross-origin redirect accepted");
        if (WarehouseHttpDeadlines.lookup(base).timeout().orElseThrow().toSeconds() != 7)
            throw new AssertionError("request timeout");
        if (InventoryBodyReader.read(new BodyResponse("ready".getBytes(StandardCharsets.UTF_8), 200, Map.of())).length != 5)
            throw new AssertionError("body read");
        boolean oversized = false;
        try { InventoryBodyReader.read(new BodyResponse(new byte[47_001], 200, Map.of())); }
        catch (IOException expected) { oversized = true; }
        if (!oversized) throw new AssertionError("oversized body accepted");
        if (CatalogRetryHint.delay(new BodyResponse(new byte[0], 503, Map.of("Retry-After", List.of("47"))))
                .orElseThrow().toSeconds() != 47) throw new AssertionError("retry delay");
        if (CatalogRetryHint.delay(new BodyResponse(new byte[0], 503, Map.of("Retry-After", List.of("82")))).isPresent())
            throw new AssertionError("early retry suggested");
        if (CatalogRetryHint.delay(new BodyResponse(new byte[0], 503, Map.of("Retry-After", List.of("Friday")))).isPresent())
            throw new AssertionError("unsupported retry date");
        int[] quantities = new int[47_000];
        java.util.Arrays.fill(quantities, 2);
        if (ShipmentBatchRunner.sum(quantities) != 94_000) throw new AssertionError("fork sum");
        if (ForkJoinPool.commonPool().invoke(new ValidatedShipmentSum(quantities, 0, quantities.length)) != 94_000)
            throw new AssertionError("validated sum");
        quantities[46_999] = -1;
        boolean rejectedNegative = false;
        try { ForkJoinPool.commonPool().invoke(new ValidatedShipmentSum(quantities, 0, quantities.length)); }
        catch (IllegalArgumentException expected) { rejectedNegative = true; }
        if (!rejectedNegative) throw new AssertionError("negative quantity accepted");
        long streamTotal = ShipmentStreamTotal.sum(List.of(
            new ShipmentStreamTotal.Shipment("receipt-47", 17),
            new ShipmentStreamTotal.Shipment("receipt-82", 30)));
        if (streamTotal != 47) throw new AssertionError("stream total");
        System.out.println("HTTP boundary and fork/join checks passed");
    }
}''')
    compiled = subprocess.run(["javac", "--release", "17", "-cp", str(directory),
                               "-d", str(directory), str(harness)], capture_output=True, text=True)
    assert compiled.returncode == 0, compiled.stderr
    ran = subprocess.run(["java", "-cp", str(directory), "JavaHttpForkJoinSmoke"],
                         capture_output=True, text=True, timeout=20)
    assert ran.returncode == 0, ran.stderr
    assert ran.stdout.strip() == "HTTP boundary and fork/join checks passed", ran.stdout

print(json.dumps({"compiled": len(slugs), "localSmoke": True, "result": ran.stdout.strip()}))
