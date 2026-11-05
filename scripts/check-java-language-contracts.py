"""Compile the new Java language lessons and test their distinct contracts."""

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
    "generic-wildcard-copy-contract", "generic-erasure-runtime-type-check",
    "generic-bridge-method-dispatch", "interface-default-method-conflict",
    "record-compact-constructor-normalization", "instanceof-pattern-scope",
    "switch-expression-yield-contract", "sealed-hierarchy-exhaustive-switch",
    "annotation-retention-runtime-gate", "repeatable-annotations-runtime-read",
    "enum-constant-specific-fee",
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
quiz = lookup["quizzes/java-language-contracts"]
assert len(quiz["data"]["questions"]) == 11
assert {question["answer"] for question in quiz["data"]["questions"]} == {0, 1, 2}
for question in quiz["data"]["questions"]:
    assert 0 <= question["answer"] < len(question["options"]) == 3
    assert len(set(question["options"])) == 3
reachable = {target for entry in entries if entry["path"].startswith("java/") and entry["type"] == "subject"
             for module in entry["data"]["modules"] for target in module["lessons"]}
assert set("java/" + slug for slug in slugs) <= reachable
assert quiz["path"] in reachable

with tempfile.TemporaryDirectory(prefix="aitrove-java-language-") as folder:
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

    harness = directory / "JavaLanguageContractsSmoke.java"
    harness.write_text('''import java.util.ArrayList;
import java.util.List;

public class JavaLanguageContractsSmoke {
    public static void main(String[] arguments) throws Exception {
        List<ParcelEventCopy.ScannedParcel> scanned =
            List.of(new ParcelEventCopy.ScannedParcel("parcel-47"));
        List<ParcelEventCopy.ParcelEvent> events = new ArrayList<>();
        ParcelEventCopy.append(scanned, events);
        if (!events.get(0).parcelId().equals("parcel-47")) throw new AssertionError("wildcard copy");

        if (!TypedReceiptBoundary.checkedCopy(List.of("receipt-82"), String.class)
                .equals(List.of("receipt-82"))) throw new AssertionError("typed copy");
        boolean rejectedType = false;
        try { TypedReceiptBoundary.checkedCopy(List.of(47), String.class); }
        catch (ClassCastException expected) { rejectedType = true; }
        if (!rejectedType) throw new AssertionError("type mismatch");

        if (FeeBridgeInspection.rateThroughBase() != 4700L || FeeBridgeInspection.bridgeCount() != 1)
            throw new AssertionError("generic bridge");
        if (!CombinedReceiptLabel.render().equals("AUDIT-82 / RECEIPT-47"))
            throw new AssertionError("default resolution");

        var mass = ShipmentMassPolicy.accept("  parcel-82  ", 23_000);
        if (!mass.shipmentId().equals("parcel-82")) throw new AssertionError("record normalization");
        boolean rejectedMass = false;
        try { ShipmentMassPolicy.accept("parcel-82", 47_001); }
        catch (IllegalArgumentException expected) { rejectedMass = true; }
        if (!rejectedMass) throw new AssertionError("record validation");

        if (RefundPatternGate.acceptedCents(new RefundPatternGate.RefundEvent("receipt-23", 2300)) != 2300)
            throw new AssertionError("pattern match");
        boolean rejectedEvent = false;
        try { RefundPatternGate.acceptedCents("not a refund"); }
        catch (IllegalArgumentException expected) { rejectedEvent = true; }
        if (!rejectedEvent) throw new AssertionError("unsupported event");

        if (OrderChargeSwitch.charge(OrderChargeSwitch.State.HELD, 2300) != 2347)
            throw new AssertionError("switch yield");
        if (BillingRequestRouter.signedCents(new BillingRequestRouter.RefundRequest(47)) != -47)
            throw new AssertionError("sealed switch");

        if (!AuditMarkerInspection.marked(AuditMarkerInspection.InvoiceActions.class,
                "approve", long.class)) throw new AssertionError("runtime marker");
        if (!DispatchLabelReader.labels(DispatchLabelReader.class.getDeclaredMethod("dispatch"))
                .equals(List.of("depot-47", "depot-82")))
            throw new AssertionError("repeatable annotation");
        if (ParcelTierFees.Tier.STANDARD.fee(1001) != 94
                || ParcelTierFees.Tier.EXPRESS.fee(1001) != 164)
            throw new AssertionError("constant-specific fee");
        System.out.println("Language contract checks passed");
    }
}''')
    compiled = subprocess.run(["javac", "--release", "21", "-cp", str(directory),
                               "-d", str(directory), str(harness)], capture_output=True, text=True)
    assert compiled.returncode == 0, compiled.stderr
    ran = subprocess.run(["java", "-cp", str(directory), "JavaLanguageContractsSmoke"],
                         capture_output=True, text=True, timeout=30)
    assert ran.returncode == 0, ran.stderr
    assert ran.stdout.strip() == "Language contract checks passed", ran.stdout

print(json.dumps({"compiled": len(slugs), "localSmoke": True, "result": ran.stdout.strip()}))
