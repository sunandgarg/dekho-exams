"""Validate runtime-discovery lessons, compile examples, and run local contracts."""
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
    "reflection-target-exception-boundary", "reflection-exact-overload-lookup",
    "reflection-trysetaccessible-module", "dynamic-proxy-object-method-contract",
    "service-loader-provider-failure", "classforname-no-initialization",
    "module-exports-vs-opens-check", "methodhandle-exact-callsite",
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

quiz = lookup["quizzes/java-reflection-contracts"]
assert len(quiz["data"]["questions"]) == 8
for question in quiz["data"]["questions"]:
    assert 0 <= question["answer"] < len(question["options"]) == 3
    assert len(set(question["options"])) == 3
reachable = {target for entry in entries if entry["path"].startswith("java/") and entry["type"] == "subject"
             for module in entry["data"]["modules"] for target in module["lessons"]}
assert set("java/" + slug for slug in slugs) <= reachable
assert quiz["path"] in reachable

with tempfile.TemporaryDirectory(prefix="aitrove-java-reflection-") as folder:
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

    harness = directory / "JavaReflectionContractsSmoke.java"
    harness.write_text('''import java.util.concurrent.atomic.AtomicLong;

public class JavaReflectionContractsSmoke {
    public static class ShipmentPolicy {
        public String evaluate(long shipmentId) {
            if (shipmentId < 0) throw new IllegalStateException("Invalid shipment");
            return "approved-" + shipmentId;
        }
    }
    public static class DepotRates {
        public long rate(long depotId, int parcels) { return depotId + parcels; }
        public long rate(Long depotId, int parcels) { return -1; }
    }
    public static class AuditRecord {
        private String auditCode() { return "REVIEW-82"; }
    }

    public static void main(String[] arguments) throws Throwable {
        if (!ShipmentPolicyInvocation.evaluate(new ShipmentPolicy(), 47).equals("approved-47"))
            throw new AssertionError("method invocation");
        boolean targetFailure = false;
        try { ShipmentPolicyInvocation.evaluate(new ShipmentPolicy(), -1); }
        catch (IllegalStateException expected) { targetFailure = true; }
        if (!targetFailure) throw new AssertionError("target failure unwrapping");

        if (DepotRateLookup.cents(new DepotRates(), 47, 3) != 50)
            throw new AssertionError("primitive overload selection");
        if (!AuditCodeAccess.read(new AuditRecord()).equals("REVIEW-82"))
            throw new AssertionError("deep reflection on owned class");

        AtomicLong reads = new AtomicLong();
        ReceiptReaderProxy.Reader reader = ReceiptReaderProxy.counting(id -> "R-" + id, reads);
        if (!reader.read(82).equals("R-82") || reads.get() != 1)
            throw new AssertionError("proxy delegate");
        if (!reader.equals(reader) || reader.equals(new Object()) ||
                reader.hashCode() != System.identityHashCode(reader) ||
                !reader.toString().equals("ReceiptReaderProxy"))
            throw new AssertionError("proxy Object methods");

        boolean missingProvider = false;
        try { ReceiptCodecDiscovery.requiredProvider(); }
        catch (IllegalStateException expected) { missingProvider = true; }
        if (!missingProvider) throw new AssertionError("missing service provider");
        if (ReceiptCodecTypeGate.resolve("warehouse") != ReceiptCodecTypeGate.WarehouseCodec.class)
            throw new AssertionError("allowlisted class");
        boolean unknownKey = false;
        try { ReceiptCodecTypeGate.resolve("external"); }
        catch (IllegalArgumentException expected) { unknownKey = true; }
        if (!unknownKey) throw new AssertionError("unknown class key");

        PluginModuleVisibility.Access access = PluginModuleVisibility.inspect(
                String.class, JavaReflectionContractsSmoke.class.getModule());
        if (!access.consumerReadsProvider() || !access.packageExported())
            throw new AssertionError("java.base visibility");
        if (!ReceiptCodeSlice.read("RECEIPT-47", 8, 10).equals("47"))
            throw new AssertionError("invokeExact callsite");
        System.out.println("Reflection local contracts passed");
    }
}''')
    compiled = subprocess.run(["javac", "--release", "17", "-cp", str(directory),
                               "-d", str(directory), str(harness)], capture_output=True, text=True)
    assert compiled.returncode == 0, compiled.stderr
    ran = subprocess.run(["java", "-cp", str(directory), "JavaReflectionContractsSmoke"],
                         capture_output=True, text=True, timeout=30)
    assert ran.returncode == 0, ran.stderr
    assert ran.stdout.strip() == "Reflection local contracts passed", ran.stdout

print(json.dumps({"compiled": len(slugs), "localSmoke": True, "result": ran.stdout.strip()}))
