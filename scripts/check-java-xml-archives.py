"""Compile new XML/archive samples and exercise bounded local contracts."""

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
    "xml-dom-external-access-boundary", "xml-stax-pull-and-close",
    "xml-xpath-fixed-expression", "xml-schema-local-validation",
    "xml-transformer-bounded-output", "xml-namespace-uri-selection",
    "gzip-inflated-byte-cap", "gzip-output-footer-ownership",
    "zip-duplicate-entry-names", "zip-entry-crc-boundary",
    "zip-output-finalization",
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
quiz = lookup["quizzes/java-xml-archives"]
assert len(quiz["data"]["questions"]) == 12
assert {question["answer"] for question in quiz["data"]["questions"]} == {0, 1, 2}
reachable = {target for entry in entries if entry["path"].startswith("java/") and entry["type"] == "subject"
             for module in entry["data"]["modules"] for target in module["lessons"]}
assert set("java/" + slug for slug in slugs) <= reachable
assert quiz["path"] in reachable

with tempfile.TemporaryDirectory(prefix="aitrove-java-xml-archive-") as folder:
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

    harness = directory / "JavaXmlArchiveSmoke.java"
    harness.write_text('''import java.io.ByteArrayOutputStream;
import java.io.IOException;
import java.nio.charset.StandardCharsets;
import java.nio.file.Files;
import java.nio.file.Path;
import java.util.Arrays;
import java.util.Comparator;
import java.util.List;
import java.util.zip.GZIPOutputStream;
import javax.xml.XMLConstants;
import org.w3c.dom.Document;

public class JavaXmlArchiveSmoke {
    public static void main(String[] arguments) throws Exception {
        Path staging = Files.createTempDirectory("aitrove-xml-archive-");
        try {
            byte[] manifest = "<manifest><receipt id='receipt-47'/></manifest>"
                .getBytes(StandardCharsets.UTF_8);
            Document parsed = BoundedManifestDom.parse(manifest);
            if (!ManifestXPathIds.receiptIds(parsed).equals(List.of("receipt-47")))
                throw new AssertionError("XPath selection");
            if (ReceiptStaxCounter.count(manifest) != 1) throw new AssertionError("StAX count");
            StringBuilder excessReceipts = new StringBuilder("<manifest>");
            for (int receipt = 0; receipt < 48; receipt++) excessReceipts.append("<receipt/>");
            excessReceipts.append("</manifest>");
            boolean rejectedReceiptCount = false;
            try { ReceiptStaxCounter.count(excessReceipts.toString().getBytes(StandardCharsets.UTF_8)); }
            catch (IllegalArgumentException expected) { rejectedReceiptCount = true; }
            if (!rejectedReceiptCount) throw new AssertionError("StAX receipt cap");
            Path secret = staging.resolve("private.txt");
            Files.writeString(secret, "DO-NOT-READ");
            String external = "<!DOCTYPE manifest [<!ENTITY leaked SYSTEM '" + secret.toUri()
                + "'>]><manifest>&leaked;</manifest>";
            boolean externalBlocked = false;
            try {
                Document unsafe = BoundedManifestDom.parse(external.getBytes(StandardCharsets.UTF_8));
                externalBlocked = !unsafe.getDocumentElement().getTextContent().contains("DO-NOT-READ");
            } catch (Exception expected) { externalBlocked = true; }
            if (!externalBlocked) throw new AssertionError("external entity resolved");
            byte[] serialized = BoundedManifestXmlWriter.serialize(parsed);
            if (BoundedManifestDom.parse(serialized).getDocumentElement() == null)
                throw new AssertionError("XML serialization");
            Document largeOutput = BoundedManifestDom.parse("<manifest/>".getBytes(StandardCharsets.UTF_8));
            largeOutput.getDocumentElement().setTextContent("r".repeat(47_000));
            boolean rejectedOutput = false;
            try { BoundedManifestXmlWriter.serialize(largeOutput); }
            catch (Exception expected) { rejectedOutput = true; }
            if (!rejectedOutput) throw new AssertionError("XML output cap");
            byte[] namespaced = "<c:manifest xmlns:c='urn:aitrove:shipment'><c:receipt id='receipt-82'/></c:manifest>"
                .getBytes(StandardCharsets.UTF_8);
            if (!NamespacedReceiptIds.select(BoundedManifestDom.parse(namespaced),
                    "urn:aitrove:shipment").equals(List.of("receipt-82")))
                throw new AssertionError("namespace URI");
            String schema = "<xs:schema xmlns:xs='" + XMLConstants.W3C_XML_SCHEMA_NS_URI + "'>"
                + "<xs:element name='manifest'><xs:complexType><xs:sequence>"
                + "<xs:element name='receipt' minOccurs='1' maxOccurs='47'>"
                + "<xs:complexType><xs:attribute name='id' type='xs:string' use='required'/>"
                + "</xs:complexType></xs:element></xs:sequence></xs:complexType></xs:element></xs:schema>";
            Path approvedSchema = staging.resolve("manifest-schema.xsd");
            Files.writeString(approvedSchema, schema);
            LocalManifestSchemaGate.validate(approvedSchema, manifest);
            boolean rejectedInvalidSchema = false;
            try { LocalManifestSchemaGate.validate(approvedSchema,
                "<manifest/>".getBytes(StandardCharsets.UTF_8)); }
            catch (Exception expected) { rejectedInvalidSchema = true; }
            if (!rejectedInvalidSchema) throw new AssertionError("schema rejection");
            byte[] compressed = ManifestGzipWriter.compress(manifest);
            if (!Arrays.equals(BoundedManifestInflater.inflate(compressed), manifest))
                throw new AssertionError("GZIP round trip");
            byte[] huge = new byte[47_001];
            ByteArrayOutputStream compressedHuge = new ByteArrayOutputStream();
            try (GZIPOutputStream gzip = new GZIPOutputStream(compressedHuge)) {
                gzip.write(huge);
            }
            boolean rejectedExpansion = false;
            try { BoundedManifestInflater.inflate(compressedHuge.toByteArray()); }
            catch (IOException expected) { rejectedExpansion = true; }
            if (!rejectedExpansion) throw new AssertionError("GZIP expansion cap");
            Path archive = staging.resolve("receipt-47.zip");
            ReceiptZipWriter.create(archive, manifest);
            if (!UniqueZipEntryNames.scan(archive).equals(List.of("receipt-47.manifest")))
                throw new AssertionError("ZIP names");
            if (ReceiptZipCrcGate.verifiedBytes(archive, "receipt-47.manifest") != manifest.length)
                throw new AssertionError("ZIP CRC");
        } finally {
            try (var paths = Files.walk(staging)) {
                paths.sorted(Comparator.reverseOrder()).forEach(path -> {
                    try { Files.delete(path); }
                    catch (IOException failure) { throw new RuntimeException(failure); }
                });
            }
        }
        System.out.println("XML and archive checks passed");
    }
}''')
    compiled = subprocess.run(["javac", "--release", "17", "-cp", str(directory),
                               "-d", str(directory), str(harness)], capture_output=True, text=True)
    assert compiled.returncode == 0, compiled.stderr
    ran = subprocess.run(["java", "-cp", str(directory), "JavaXmlArchiveSmoke"],
                         capture_output=True, text=True, timeout=30)
    assert ran.returncode == 0, ran.stderr
    assert ran.stdout.strip() == "XML and archive checks passed", ran.stdout

print(json.dumps({"compiled": len(slugs), "localSmoke": True, "result": ran.stdout.strip()}))
