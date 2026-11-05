"""Validate the concurrent-state lessons and exercise representative contracts."""

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
    "concurrenthashmap-computeifabsent-counter", "concurrentskiplistmap-time-window",
    "copyonwritearraylist-listener-registry", "atomicreference-immutable-map-snapshot",
    "delayqueue-retry-expiry", "exchanger-two-party-buffer-swap",
    "linkedtransferqueue-receipt-handoff", "longaccumulator-high-water-mark",
    "threadlocal-context-restoration", "locksupport-condition-loop",
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
    parsed = LessonStructure()
    parsed.feed(body)
    assert not parsed.stack, slug
quiz = lookup["quizzes/java-concurrent-state"]
assert len(quiz["data"]["questions"]) == 10
assert {question["answer"] for question in quiz["data"]["questions"]} == {0, 1, 2}
for question in quiz["data"]["questions"]:
    assert 0 <= question["answer"] < len(question["options"]) == 3
    assert len(set(question["options"])) == 3
reachable = {target for entry in entries if entry["path"].startswith("java/") and entry["type"] == "subject"
             for module in entry["data"]["modules"] for target in module["lessons"]}
assert set("java/" + slug for slug in slugs) <= reachable
assert quiz["path"] in reachable

with tempfile.TemporaryDirectory(prefix="aitrove-java-concurrent-") as folder:
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

    harness = directory / "JavaConcurrentStateSmoke.java"
    harness.write_text('''import java.time.Duration;
import java.util.List;
import java.util.Map;
import java.util.concurrent.CountDownLatch;
import java.util.concurrent.TimeUnit;
import java.util.concurrent.atomic.AtomicReference;

public class JavaConcurrentStateSmoke {
    public static void main(String[] arguments) throws Exception {
        DepotArrivalCounters counts = new DepotArrivalCounters();
        Thread first = new Thread(() -> { for (int item = 0; item < 47; item++) counts.record("depot-82"); });
        Thread second = new Thread(() -> { for (int item = 0; item < 47; item++) counts.record("depot-82"); });
        first.start(); second.start(); first.join(); second.join();
        if (counts.count("depot-82") != 94) throw new AssertionError("counter");

        DispatchSequenceWindow window = new DispatchSequenceWindow();
        window.record(240, "receipt-240");
        window.record(287, "receipt-287");
        if (!window.read(240, 287).equals(List.of("receipt-240"))) throw new AssertionError("window");

        ShipmentNoticeListeners listeners = new ShipmentNoticeListeners();
        StringBuilder noticed = new StringBuilder();
        java.util.function.Consumer<String> listener = noticed::append;
        listeners.register(listener); listeners.register(listener);
        listeners.dispatch("parcel-47");
        if (!noticed.toString().equals("parcel-47")) throw new AssertionError("listener deduplication");

        DepotFeeSnapshots fees = new DepotFeeSnapshots();
        fees.setFee("depot-47", 8200);
        Map<String, Long> old = fees.snapshot();
        fees.setFee("depot-82", 2400);
        if (old.size() != 1 || fees.snapshot().size() != 2) throw new AssertionError("immutable version");

        OrderRetryQueue retries = new OrderRetryQueue();
        retries.schedule("order-47", Duration.ofSeconds(23));
        if (retries.pollDue() != null) throw new AssertionError("early retry");
        retries.schedule("order-82", Duration.ZERO);
        if (!"order-82".equals(retries.pollDue())) throw new AssertionError("due retry");

        ParcelBufferSwap swap = new ParcelBufferSwap();
        AtomicReference<byte[]> partnerResult = new AtomicReference<>();
        byte[] left = new byte[47]; byte[] right = new byte[47];
        Thread partner = new Thread(() -> {
            try { partnerResult.set(swap.swap(right)); }
            catch (Exception failure) { throw new AssertionError(failure); }
        });
        partner.start();
        if (swap.swap(left) != right) throw new AssertionError("exchange");
        partner.join();
        if (partnerResult.get() != left) throw new AssertionError("partner exchange");

        ReceiptTransferLane lane = new ReceiptTransferLane();
        AtomicReference<String> receipt = new AtomicReference<>();
        Thread consumer = new Thread(() -> {
            try { receipt.set(lane.awaitReceipt()); }
            catch (InterruptedException failure) { Thread.currentThread().interrupt(); }
        });
        consumer.start();
        if (!lane.handoff("receipt-47")) throw new AssertionError("transfer");
        consumer.join();
        if (!"receipt-47".equals(receipt.get())) throw new AssertionError("consumer receipt");

        BacklogHighWaterMark peak = new BacklogHighWaterMark();
        peak.observe(23); peak.observe(47); peak.observe(8);
        if (peak.highestObserved() != 47) throw new AssertionError("peak");

        TenantTraceScope.run("depot-47", () -> {
            TenantTraceScope.run("depot-82", () -> {
                if (!"depot-82".equals(TenantTraceScope.current())) throw new AssertionError("inner scope");
            });
            if (!"depot-47".equals(TenantTraceScope.current())) throw new AssertionError("restore");
        });
        if (TenantTraceScope.current() != null) throw new AssertionError("cleanup");

        OneWaiterDispatchGate gate = new OneWaiterDispatchGate();
        CountDownLatch started = new CountDownLatch(1);
        AtomicReference<Boolean> passed = new AtomicReference<>();
        Thread waiter = new Thread(() -> { started.countDown(); passed.set(gate.await()); });
        waiter.start();
        if (!started.await(3, TimeUnit.SECONDS)) throw new AssertionError("waiter not started");
        gate.signal(); waiter.join();
        if (!Boolean.TRUE.equals(passed.get())) throw new AssertionError("gate signal");
        System.out.println("Concurrent state checks passed");
    }
}''')
    compiled = subprocess.run(["javac", "--release", "17", "-cp", str(directory),
                               "-d", str(directory), str(harness)], capture_output=True, text=True)
    assert compiled.returncode == 0, compiled.stderr
    ran = subprocess.run(["java", "-cp", str(directory), "JavaConcurrentStateSmoke"],
                         capture_output=True, text=True, timeout=30)
    assert ran.returncode == 0, ran.stderr
    assert ran.stdout.strip() == "Concurrent state checks passed", ran.stdout

print(json.dumps({"compiled": len(slugs), "localSmoke": True, "result": ran.stdout.strip()}))
