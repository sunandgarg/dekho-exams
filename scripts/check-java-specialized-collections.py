"""Validate and execute specialized-collection lesson contracts."""
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
    "bitset-length-versus-cardinality", "bitset-next-set-bit-range",
    "enumset-complement-deny-policy", "enumset-typed-empty-source",
    "treeset-backed-range-view", "priorityblockingqueue-explicit-capacity",
    "copyonwritearrayset-listener-snapshot", "linkedblockingdeque-urgent-admission",
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
    assert body.startswith("<p>") and body.count("<h3>Common Mistakes</h3>") == 1
    assert "http://" not in body and "https://" not in body
    assert entry["data"]["section_path"] == "java/advanced-java"
    parser = LessonStructure()
    parser.feed(body)
    assert not parser.stack, slug

quiz = lookup["quizzes/java-specialized-collections"]
assert len(quiz["data"]["questions"]) == 8
for question in quiz["data"]["questions"]:
    assert 0 <= question["answer"] < len(question["options"]) == 3
    assert len(set(question["options"])) == 3
reachable = {target for entry in entries if entry["path"].startswith("java/") and entry["type"] == "subject"
             for module in entry["data"]["modules"] for target in module["lessons"]}
assert set("java/" + slug for slug in slugs) <= reachable
assert quiz["path"] in reachable

with tempfile.TemporaryDirectory(prefix="aitrove-java-collections-") as folder:
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

    harness = directory / "JavaSpecializedCollectionsSmoke.java"
    harness.write_text('''import java.util.ArrayList;
import java.util.BitSet;
import java.util.EnumSet;
import java.util.List;
import java.util.NavigableSet;
import java.util.TreeSet;
import java.util.concurrent.atomic.AtomicInteger;

public class JavaSpecializedCollectionsSmoke {
    public static void main(String[] arguments) throws Exception {
        BitSet slots = new BitSet();
        slots.set(3);
        slots.set(47);
        slots.set(82);
        ActiveReceiptSlots.Summary summary = ActiveReceiptSlots.summarize(slots);
        if (summary.highestSlot() != 82 || summary.activeCount() != 3)
            throw new AssertionError("BitSet statistics");
        if (!ReceiptSlotWindow.active(slots, 40, 82).equals(List.of(47)))
            throw new AssertionError("BitSet half-open scan");
        slots.clear();
        if (ActiveReceiptSlots.summarize(slots).highestSlot() != -1)
            throw new AssertionError("empty BitSet");

        EnumSet<ReceiptCapabilityPolicy.Capability> allowed = EnumSet.of(
                ReceiptCapabilityPolicy.Capability.READ,
                ReceiptCapabilityPolicy.Capability.EXPORT);
        EnumSet<ReceiptCapabilityPolicy.Capability> denied =
                ReceiptCapabilityPolicy.denied(allowed);
        if (!denied.contains(ReceiptCapabilityPolicy.Capability.ARCHIVE) ||
                denied.contains(ReceiptCapabilityPolicy.Capability.READ))
            throw new AssertionError("default-deny complement");
        if (!ReceiptReviewStates.copy(List.of()).isEmpty())
            throw new AssertionError("typed empty EnumSet");

        NavigableSet<Long> receiptIds = new TreeSet<>(List.of(3L, 82L));
        NavigableSet<Long> range = ReceiptIdRangeView.between(receiptIds, 40, 82);
        receiptIds.add(47L);
        if (!range.contains(47L) || range.contains(82L))
            throw new AssertionError("backed range view");
        boolean rejected = false;
        try { range.add(82L); } catch (IllegalArgumentException expected) { rejected = true; }
        if (!rejected) throw new AssertionError("out-of-range insert");

        BoundedPriorityReceiptInbox inbox = new BoundedPriorityReceiptInbox();
        for (int index = 0; index < 47; index++) {
            if (!inbox.submit(new BoundedPriorityReceiptInbox.Job(index, index)))
                throw new AssertionError("priority admission");
        }
        if (inbox.submit(new BoundedPriorityReceiptInbox.Job(99, 99)))
            throw new AssertionError("priority capacity");
        if (inbox.take().priority() != 46 ||
                !inbox.submit(new BoundedPriorityReceiptInbox.Job(99, 99)))
            throw new AssertionError("priority dequeue releases slot");

        ReceiptListenerRegistry registry = new ReceiptListenerRegistry();
        AtomicInteger first = new AtomicInteger();
        AtomicInteger second = new AtomicInteger();
        ReceiptListenerRegistry.Listener later = receiptId -> second.incrementAndGet();
        registry.add(receiptId -> { first.incrementAndGet(); registry.add(later); });
        registry.publish(47);
        if (first.get() != 1 || second.get() != 0)
            throw new AssertionError("copy-on-write snapshot");
        registry.publish(82);
        if (second.get() != 1) throw new AssertionError("later publication");

        ReceiptWorkDeque deque = new ReceiptWorkDeque();
        for (int index = 0; index < 46; index++) {
            if (!deque.submitNormal("normal-" + index)) throw new AssertionError("deque admission");
        }
        if (!deque.submitUrgent("urgent-47") || deque.submitNormal("overflow"))
            throw new AssertionError("deque shared capacity");
        if (!deque.take().equals("urgent-47") || !deque.submitNormal("new-slot"))
            throw new AssertionError("deque urgent order");

        System.out.println("Specialized collection contracts passed");
    }
}''')
    compiled = subprocess.run(["javac", "--release", "17", "-cp", str(directory),
                               "-d", str(directory), str(harness)], capture_output=True, text=True)
    assert compiled.returncode == 0, compiled.stderr
    ran = subprocess.run(["java", "-cp", str(directory), "JavaSpecializedCollectionsSmoke"],
                         capture_output=True, text=True, timeout=30)
    assert ran.returncode == 0, ran.stderr
    assert ran.stdout.strip() == "Specialized collection contracts passed", ran.stdout

print(json.dumps({"compiled": len(slugs), "localSmoke": True, "result": ran.stdout.strip()}))
