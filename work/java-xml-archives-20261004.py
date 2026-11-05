"""Add original Java XML and archive-processing lessons."""

import copy
import datetime
import html
import json
import re
import uuid
from pathlib import Path

root = Path(__file__).resolve().parents[1]
fixture = root / "src/data/fixtures.json"
entries = json.loads(fixture.read_text())
lookup = {row["path"]: row for row in entries}
stamp = datetime.datetime.now(datetime.UTC).isoformat()

lessons = [
    dict(slug="xml-dom-external-access-boundary", title="Java DOM parsing: deny external XML access at the factory", group="XML processing boundaries", release=11,
         definition="A DOM parser builds an in-memory document tree. Its factory must state whether external DTD and schema references may be opened before parsing untrusted XML.",
         details="This method accepts at most 47,000 input bytes, enables secure processing, and denies external DTD and schema access at the factory. It makes namespace processing explicit. These settings block external resource access through those JAXP properties; they are not a universal bound on every internal expansion or document shape. Set processing limits suited to the deployed JDK and validate the resulting structure before using values. A DOM tree retains nodes for the document, so use a streaming parser when input size cannot be tightly bounded. The caller owns the input bytes; this method owns its parser.",
         case="A supplier sends a manifest containing an external entity reference. The parser must not fetch a local file or remote resource as a side effect of reading that manifest. The same intake rejects a 47,001-byte payload before building a tree. A valid but deeply nested 47,000-byte document still needs a depth policy at the service boundary.",
         code='''import java.io.ByteArrayInputStream;
import javax.xml.XMLConstants;
import javax.xml.parsers.DocumentBuilderFactory;
import org.w3c.dom.Document;

public class BoundedManifestDom {
    public static Document parse(byte[] xml) throws Exception {
        if (xml.length > 47_000) throw new IllegalArgumentException("Manifest XML exceeds cap");
        DocumentBuilderFactory factory = DocumentBuilderFactory.newInstance();
        factory.setNamespaceAware(true);
        factory.setFeature(XMLConstants.FEATURE_SECURE_PROCESSING, true);
        factory.setAttribute(XMLConstants.ACCESS_EXTERNAL_DTD, "");
        factory.setAttribute(XMLConstants.ACCESS_EXTERNAL_SCHEMA, "");
        return factory.newDocumentBuilder().parse(new ByteArrayInputStream(xml));
    }
}''',
         cost="Parsing B input bytes is at least O(B) work and retains a tree whose memory can substantially exceed B. The byte cap limits source size, not the exact number of nodes or expanded text. Reject unsupported security settings rather than silently falling back to an unsafe parser.",
         mistakes=["Do not let the parser use default external-access policy for untrusted input.", "Do not treat secure processing as a complete document-size or depth limit.", "Do not build a DOM for an unbounded stream."],
         related=["java/files", "java/charsetdecoder-report-policy", "java/zip-entry-expanded-limit"]),
    dict(slug="xml-stax-pull-and-close", title="Java StAX: pull XML events under a count and entity policy", group="XML processing boundaries", release=11,
         definition="StAX lets the caller pull XML events one at a time. That limits retained tree state, but the caller still owns input size, entity policy, event count, and reader closure.",
         details="The factory disables DTD support and external entities, then the code counts receipt start elements. It rejects more than 47 receipts and closes the XMLStreamReader in finally. The source is a bounded byte array, so this method does not open an external stream. A provider may reject a requested property; fail that setup rather than ignoring it. Pull parsing is useful when the workflow needs only selected values, but an XML grammar and depth limit remain separate requirements. If an InputStream were supplied by a caller, closing the reader would not be a safe substitute for an explicit stream-ownership agreement.",
         case="A depot accepts a manifest with 47 receipt elements. A 48th makes the document invalid for this intake, even if the XML is syntactically sound. The count is a business limit, not a parser feature. The implementation does not keep the document tree merely to compute that count.",
         code='''import java.io.ByteArrayInputStream;
import javax.xml.stream.XMLInputFactory;
import javax.xml.stream.XMLStreamConstants;
import javax.xml.stream.XMLStreamReader;

public class ReceiptStaxCounter {
    public static int count(byte[] xml) throws Exception {
        if (xml.length > 47_000) throw new IllegalArgumentException("XML exceeds cap");
        XMLInputFactory factory = XMLInputFactory.newFactory();
        factory.setProperty(XMLInputFactory.SUPPORT_DTD, false);
        factory.setProperty(XMLInputFactory.IS_SUPPORTING_EXTERNAL_ENTITIES, false);
        XMLStreamReader reader = factory.createXMLStreamReader(new ByteArrayInputStream(xml));
        try {
            int receipts = 0;
            while (reader.hasNext()) {
                if (reader.next() == XMLStreamConstants.START_ELEMENT
                        && "receipt".equals(reader.getLocalName())) {
                    if (++receipts > 47) throw new IllegalArgumentException("Too many receipts");
                }
            }
            return receipts;
        } finally {
            reader.close();
        }
    }
}''',
         cost="The scan is O(E) over E XML events and retains O(1) application state beyond parser buffers. The 47,000-byte input cap bounds the source array, while parser internals and deeply nested input still merit separate limits.",
         mistakes=["Do not assume streaming removes the need for input and depth caps.", "Do not ignore a provider's refusal to disable external entities.", "Do not leave the XMLStreamReader open after a failure."],
         related=["java/xml-dom-external-access-boundary", "java/stream-resource-lifetime", "java/bounded-line-reader"]),
    dict(slug="xml-xpath-fixed-expression", title="Java XPath: compile a fixed selection, not user-supplied code", group="XML processing boundaries", release=11,
         definition="XPath selects nodes from an XML tree. A fixed expression is a known application rule; concatenating user text into an XPath expression changes that rule.",
         details="The method evaluates a static path against a Document that the caller has already parsed under an external-access and size policy. It extracts receipt IDs from attribute nodes and caps the result at 47. NodeList retains references into the DOM tree, so the document remains reachable during extraction. The expression is not a general-purpose search feature; if a user needs a filter, select the known nodes first and compare their values in Java. Namespaces require an explicit NamespaceContext or namespace-aware DOM selection rather than guessing prefixes.",
         case="An audit asks for receipt IDs in the top-level manifest collection. A fixed path returns those IDs. If a user submits a receipt ID containing brackets or quotes, that input belongs in a value comparison, not in the XPath source. A malformed or unexpected tree yields an empty result that the caller must distinguish from an approved empty manifest.",
         code='''import java.util.ArrayList;
import java.util.List;
import javax.xml.xpath.XPathConstants;
import javax.xml.xpath.XPathExpression;
import javax.xml.xpath.XPathFactory;
import org.w3c.dom.Document;
import org.w3c.dom.NodeList;

public class ManifestXPathIds {
    public static List<String> receiptIds(Document manifest) throws Exception {
        XPathExpression selection = XPathFactory.newInstance().newXPath()
            .compile("/manifest/receipt/@id");
        NodeList attributes = (NodeList) selection.evaluate(manifest, XPathConstants.NODESET);
        if (attributes.getLength() > 47) throw new IllegalArgumentException("Too many receipts");
        List<String> ids = new ArrayList<>();
        for (int index = 0; index < attributes.getLength(); index++) {
            ids.add(attributes.item(index).getNodeValue());
        }
        return ids;
    }
}''',
         cost="XPath evaluation traverses the relevant DOM nodes and can cost O(N) or more according to expression and implementation; result storage is O(R) for R selected IDs. This static expression is simple, but the DOM itself still has O(document) retention.",
         mistakes=["Do not concatenate user data into an XPath program.", "Do not assume an empty selection proves the input was valid.", "Do not treat a prefix spelling as a namespace identity."],
         related=["java/xml-dom-external-access-boundary", "java/xml-namespace-uri-selection", "java/regex-quote-user-input"]),
    dict(slug="xml-schema-local-validation", title="Java XML Schema validation: use a trusted schema without external fetches", group="XML processing boundaries", release=11,
         definition="A SchemaFactory compiles an XML Schema, and a Validator checks an XML instance against it. Both stages need an external-resource policy.",
         details="This method takes a schema path selected by trusted configuration, rejects an oversized XML instance, and sets empty external DTD and schema-access lists on both factory and validator. The supplied schema file is the intended root input; external includes and imports are not allowed by this policy. Create a Validator for each operation instead of sharing mutable validation state across threads. A successful schema check proves conformance to that schema, not authorization to act on the document. The schema itself needs review and version control.",
         case="A carrier changes its manifest format. The service chooses the approved local schema for that carrier version and validates the received bytes. If the schema tries to import an outside definition, compilation fails instead of fetching it. If XML fails validation, the request is rejected before database writes begin.",
         code='''import java.io.ByteArrayInputStream;
import java.nio.file.Path;
import javax.xml.XMLConstants;
import javax.xml.transform.stream.StreamSource;
import javax.xml.validation.Schema;
import javax.xml.validation.SchemaFactory;
import javax.xml.validation.Validator;

public class LocalManifestSchemaGate {
    public static void validate(Path approvedSchema, byte[] xml) throws Exception {
        if (xml.length > 47_000) throw new IllegalArgumentException("XML exceeds cap");
        SchemaFactory factory = SchemaFactory.newInstance(XMLConstants.W3C_XML_SCHEMA_NS_URI);
        factory.setFeature(XMLConstants.FEATURE_SECURE_PROCESSING, true);
        factory.setProperty(XMLConstants.ACCESS_EXTERNAL_DTD, "");
        factory.setProperty(XMLConstants.ACCESS_EXTERNAL_SCHEMA, "");
        Schema schema = factory.newSchema(approvedSchema.toFile());
        Validator validator = schema.newValidator();
        validator.setProperty(XMLConstants.ACCESS_EXTERNAL_DTD, "");
        validator.setProperty(XMLConstants.ACCESS_EXTERNAL_SCHEMA, "");
        validator.validate(new StreamSource(new ByteArrayInputStream(xml)));
    }
}''',
         cost="Schema compilation has a setup cost and retains schema structures; a service can reuse an immutable compiled Schema under its version policy. Each validation scans the instance and uses memory according to its grammar and provider. Keep an explicit input cap and processing limits.",
         mistakes=["Do not accept unreviewed schema paths from a request.", "Do not allow imports merely because the root schema is local.", "Do not share one mutable Validator across concurrent requests."],
         related=["java/xml-dom-external-access-boundary", "java/jdbc-transactions", "java/files"]),
    dict(slug="xml-transformer-bounded-output", title="Java XML Transformer: bound serialized output and external access", group="XML processing boundaries", release=11,
         definition="An identity Transformer serializes a DOM tree. The caller must control external stylesheet access and the number of bytes written to its output sink.",
         details="The factory denies external DTD and stylesheet access and enables secure processing. The method writes into a bounded OutputStream that rejects the byte which would exceed 47,000 output bytes. A DOM can produce more serialized bytes than its original input due to escaping and formatting; input caps alone are not output caps. This code assumes the Document came from a trusted parse boundary. It returns a complete byte array only after transformation succeeds. It does not publish the bytes to a final file or sign them.",
         case="A receipt editor changes one field in a parsed manifest and serializes it for review. If escaped text grows the output past 47,000 bytes, the transform fails and no truncated result is returned. The caller can then revise the business limit or reject the edit; it cannot silently store the prefix.",
         code='''import java.io.ByteArrayOutputStream;
import java.io.IOException;
import java.io.OutputStream;
import javax.xml.XMLConstants;
import javax.xml.transform.TransformerFactory;
import javax.xml.transform.dom.DOMSource;
import javax.xml.transform.stream.StreamResult;
import org.w3c.dom.Document;

public class BoundedManifestXmlWriter {
    public static byte[] serialize(Document manifest) throws Exception {
        TransformerFactory factory = TransformerFactory.newInstance();
        factory.setFeature(XMLConstants.FEATURE_SECURE_PROCESSING, true);
        factory.setAttribute(XMLConstants.ACCESS_EXTERNAL_DTD, "");
        factory.setAttribute(XMLConstants.ACCESS_EXTERNAL_STYLESHEET, "");
        ByteArrayOutputStream bytes = new ByteArrayOutputStream();
        OutputStream capped = new OutputStream() {
            private int written;
            @Override public void write(int value) throws IOException {
                if (written == 47_000) throw new IOException("XML output exceeds cap");
                bytes.write(value);
                written++;
            }
            @Override public void write(byte[] data, int offset, int length) throws IOException {
                if (length > 47_000 - written) throw new IOException("XML output exceeds cap");
                bytes.write(data, offset, length);
                written += length;
            }
        };
        factory.newTransformer().transform(new DOMSource(manifest), new StreamResult(capped));
        return bytes.toByteArray();
    }
}''',
         cost="Serialization is O(B) over emitted bytes and retains O(B) output memory, capped at 47,000, plus the already-held DOM. The byte array copy on return briefly uses another O(B) allocation. A streaming file sink would reduce retained output but needs staging and cleanup.",
         mistakes=["Do not treat a bounded input as proof of bounded serialized output.", "Do not expose a partial byte array after transformation failure.", "Do not leave external stylesheet access to a provider default."],
         related=["java/xml-dom-external-access-boundary", "java/xml-schema-local-validation", "java/atomic-file-publication"]),
    dict(slug="xml-namespace-uri-selection", title="Java XML namespaces: select by URI and local name", group="XML processing boundaries", release=11,
         definition="An XML namespace prefix is a document-local abbreviation. Code that identifies an element should use its namespace URI and local name, not depend on the sender's chosen prefix.",
         details="The method selects receipt elements by namespace URI and local name from a namespace-aware Document, then reads their unqualified id attributes. It rejects more than 47 matches. getElementsByTagNameNS finds descendants, so the caller must also validate the expected tree shape if only direct children are allowed. The namespace URI passed to this method is an identifier; the code does not dereference it. The parser boundary still decides whether external resources can be opened and how much input is accepted.",
         case="One carrier writes a prefix 'c' and another uses 'shipment' for the same namespace URI. Both represent the same receipt element name. A prefix-based string comparison would produce different results; this method does not. A receipt nested in an unexpected wrapper still needs structural validation rather than being accepted solely because its namespace matches.",
         code='''import java.util.ArrayList;
import java.util.List;
import org.w3c.dom.Document;
import org.w3c.dom.Element;
import org.w3c.dom.NodeList;

public class NamespacedReceiptIds {
    public static List<String> select(Document manifest, String namespaceUri) {
        NodeList receipts = manifest.getElementsByTagNameNS(namespaceUri, "receipt");
        if (receipts.getLength() > 47) throw new IllegalArgumentException("Too many receipts");
        List<String> ids = new ArrayList<>();
        for (int index = 0; index < receipts.getLength(); index++) {
            Element receipt = (Element) receipts.item(index);
            ids.add(receipt.getAttribute("id"));
        }
        return ids;
    }
}''',
         cost="The DOM search visits matching tree regions and may scan O(N) nodes; the result list is O(R) for R matches. The DOM remains the larger memory cost. Repeated whole-tree searches should be measured before replacing one pass with many queries.",
         mistakes=["Do not compare namespace prefixes as global identities.", "Do not assume descendant selection enforces direct-child placement.", "Do not infer that a namespace URI is a resource the parser should fetch."],
         related=["java/xml-dom-external-access-boundary", "java/xml-xpath-fixed-expression", "java/xml-schema-local-validation"]),
    dict(slug="gzip-inflated-byte-cap", title="Java GZIPInputStream: cap bytes after decompression", group="Archive and compression boundaries", release=11,
         definition="GZIPInputStream yields uncompressed bytes. A compressed input-size cap does not bound the number of bytes a decoder can produce.",
         details="The method caps compressed input at 47,000 bytes and refuses more than 47,000 inflated bytes while reading chunks. It closes the decompressor even when a read or size check fails. It returns only a complete, accepted byte array. The inflated-byte limit protects application memory but not all CPU work consumed before reaching it; admission, time, and nesting policies may also be needed for untrusted archives. A checksum inside GZIP detects accidental corruption, not sender identity.",
         case="A depot receives a 900-byte compressed manifest that expands to 82,000 bytes. Checking only the upload length would accept it. This decoder stops when the inflated stream crosses 47,000 bytes and does not pass a partial manifest to the parser.",
         code='''import java.io.ByteArrayInputStream;
import java.io.ByteArrayOutputStream;
import java.io.IOException;
import java.util.zip.GZIPInputStream;

public class BoundedManifestInflater {
    public static byte[] inflate(byte[] compressed) throws IOException {
        if (compressed.length > 47_000) throw new IOException("Compressed input exceeds cap");
        ByteArrayOutputStream result = new ByteArrayOutputStream();
        try (GZIPInputStream input = new GZIPInputStream(new ByteArrayInputStream(compressed))) {
            byte[] chunk = new byte[8_192];
            int count;
            while ((count = input.read(chunk)) != -1) {
                if (count > 47_000 - result.size()) throw new IOException("Inflated data exceeds cap");
                result.write(chunk, 0, count);
            }
        }
        return result.toByteArray();
    }
}''',
         cost="Decompression is O(I+O) for compressed input I and inflated output O in ordinary workloads. Retained output is O(O), capped here, with an 8,192-byte work buffer. Highly compressible input can consume disproportionate work before the cap is hit.",
         mistakes=["Do not use compressed length as an expanded-size limit.", "Do not return a prefix after the limit is crossed.", "Do not treat the GZIP checksum as authentication."],
         related=["java/zip-entry-expanded-limit", "java/xml-dom-external-access-boundary", "java/bounded-line-reader"]),
    dict(slug="gzip-output-footer-ownership", title="Java GZIPOutputStream: close before using the compressed bytes", group="Archive and compression boundaries", release=11,
         definition="GZIPOutputStream writes a compressed stream whose trailer is completed when the stream finishes or closes. Reading the destination before that point risks an incomplete artifact.",
         details="The method bounds its source payload, writes it through a GZIPOutputStream, and returns the ByteArrayOutputStream contents only after the compressor closes. The compressor owns the sink for the scoped call. For a file destination, write to a staging name and publish only after close and any durability decision. Compression is not encryption; it does not protect private manifest data. This in-memory version is suitable only for bounded payloads and does not claim a useful compression ratio for every input.",
         case="A batch contains 47,000 bytes of receipt text. Returning the output array while the compressor is still open could omit the final trailer. The try-with-resources scope ends first; the caller receives a complete GZIP member or an exception.",
         code='''import java.io.ByteArrayOutputStream;
import java.io.IOException;
import java.util.zip.GZIPOutputStream;

public class ManifestGzipWriter {
    public static byte[] compress(byte[] manifest) throws IOException {
        if (manifest.length > 47_000) throw new IllegalArgumentException("Manifest exceeds cap");
        ByteArrayOutputStream destination = new ByteArrayOutputStream();
        try (GZIPOutputStream compressed = new GZIPOutputStream(destination)) {
            compressed.write(manifest);
        }
        return destination.toByteArray();
    }
}''',
         cost="Compression scans B input bytes and retains O(B) output in this bounded design, though exact compressed size depends on data. The final toByteArray copies the compressed bytes. Repeated large batches should stream to a staged file under a byte and time budget.",
         mistakes=["Do not read compressed output before finish or close.", "Do not call compression encryption.", "Do not publish a staged file before the compressor closes successfully."],
         related=["java/gzip-inflated-byte-cap", "java/atomic-file-publication", "java/files"]),
    dict(slug="zip-duplicate-entry-names", title="Java ZipFile entries: reject duplicate names before selection", group="Archive and compression boundaries", release=11,
         definition="A ZIP archive can contain more than one entry with the same name. A reader must define whether duplicates are rejected before choosing one entry by name.",
         details="The code reads central-directory entries without inflating them, caps the entry count at 47, and rejects duplicate names. It returns only a metadata list. This does not validate entry paths for extraction or prove the archive payloads are safe to inflate; those are separate steps. If a consumer uses ZipFile.getEntry after accepting duplicates, different tools may select or present a different occurrence. Rejecting ambiguity early keeps a manifest name tied to exactly one archive member under this policy.",
         case="A supplier sends an archive with two entries both named receipt-47.xml, one approved and one altered. A UI might display one while a later reader opens the other. This scan fails the archive before either entry is parsed. It also fails a 48-entry archive rather than silently ignoring the tail.",
         code='''import java.io.IOException;
import java.nio.file.Path;
import java.util.ArrayList;
import java.util.Enumeration;
import java.util.HashSet;
import java.util.List;
import java.util.Set;
import java.util.zip.ZipEntry;
import java.util.zip.ZipFile;

public class UniqueZipEntryNames {
    public static List<String> scan(Path archive) throws IOException {
        List<String> names = new ArrayList<>();
        Set<String> observed = new HashSet<>();
        try (ZipFile zip = new ZipFile(archive.toFile())) {
            Enumeration<? extends ZipEntry> entries = zip.entries();
            while (entries.hasMoreElements()) {
                if (names.size() == 47) throw new IOException("ZIP entry count exceeds cap");
                String name = entries.nextElement().getName();
                if (!observed.add(name)) throw new IOException("Duplicate ZIP entry: " + name);
                names.add(name);
            }
        }
        return names;
    }
}''',
         cost="Scanning E metadata entries is O(E) expected time and O(E) memory for names and the set, capped at 47. It does not incur the cost of decompression. A later payload read needs its own expanded-byte bound.",
         mistakes=["Do not select by name before resolving duplicates.", "Do not mistake this metadata scan for extraction-path validation.", "Do not trust entry count or size metadata as a decompression limit."],
         related=["java/zip-path-validation", "java/zip-entry-expanded-limit", "java/zip-entry-crc-boundary"]),
    dict(slug="zip-entry-crc-boundary", title="Java ZIP CRC32: detect corruption without claiming authenticity", group="Archive and compression boundaries", release=11,
         definition="A ZIP entry's CRC32 can detect accidental byte changes when compared with the bytes actually read. It cannot prove who created the archive or prevent intentional alteration.",
         details="The method opens one named entry, requires a declared CRC, and computes CRC32 over at most 47,000 inflated bytes. It drains to end before comparing, so the result is not based on a prefix. The name is chosen by a trusted caller after duplicate-name and path checks; this method does not extract to disk. An attacker can change data and recompute CRC32, so use an authenticated signature or trusted transport when origin matters. Closing both entry stream and ZipFile is part of the read boundary.",
         case="A shipment ZIP entry is damaged during storage. The computed CRC differs from its header value, and the import stops before parsing XML. A malicious sender could deliberately supply matching data and CRC, so the same check must not be called a security signature.",
         code='''import java.io.IOException;
import java.io.InputStream;
import java.nio.file.Path;
import java.util.zip.CRC32;
import java.util.zip.ZipEntry;
import java.util.zip.ZipFile;

public class ReceiptZipCrcGate {
    public static long verifiedBytes(Path archive, String approvedName) throws IOException {
        try (ZipFile zip = new ZipFile(archive.toFile())) {
            ZipEntry entry = zip.getEntry(approvedName);
            if (entry == null || entry.getCrc() < 0) throw new IOException("Entry or CRC missing");
            CRC32 checksum = new CRC32();
            long total = 0;
            try (InputStream input = zip.getInputStream(entry)) {
                byte[] chunk = new byte[8_192];
                int count;
                while ((count = input.read(chunk)) != -1) {
                    if (count > 47_000 - total) throw new IOException("Entry exceeds cap");
                    checksum.update(chunk, 0, count);
                    total += count;
                }
            }
            if (checksum.getValue() != entry.getCrc()) throw new IOException("ZIP CRC mismatch");
            return total;
        }
    }
}''',
         cost="Decompressing and checksumming B bytes costs O(B) time and O(1) application memory beyond an 8,192-byte buffer. The cap bounds output bytes, not all decompression CPU or archive metadata work.",
         mistakes=["Do not call CRC32 an authentication mechanism.", "Do not compare a checksum before consuming the full entry.", "Do not select ambiguous duplicate names without an earlier policy."],
         related=["java/zip-entry-expanded-limit", "java/zip-duplicate-entry-names", "java/hmac-sha256-verify"]),
    dict(slug="zip-output-finalization", title="Java ZipOutputStream: close each entry and the archive before publication", group="Archive and compression boundaries", release=11,
         definition="ZipOutputStream builds entries and writes central-directory metadata when the archive is finished. A successful entry write does not by itself produce a complete ZIP file.",
         details="The method creates a new archive with one fixed, application-owned entry name, writes a bounded manifest, closes the entry, and closes the stream. Only then can its caller stage or publish the file. If a write fails, the partial archive path can remain; the owner should remove or quarantine it. Untrusted entry names require separate path and duplicate rules before adding them. ZIP compresses data but does not authenticate or encrypt it merely because an archive exists.",
         case="A review worker writes receipt-47.manifest into a ZIP for handoff. It must not notify readers after write returns while the central directory is still missing. The stream scope completes first. A failure leaves the destination untrusted and requires cleanup before another attempt reuses that name.",
         code='''import java.io.IOException;
import java.nio.file.Files;
import java.nio.file.Path;
import java.util.zip.ZipEntry;
import java.util.zip.ZipOutputStream;

public class ReceiptZipWriter {
    public static void create(Path stagingArchive, byte[] manifest) throws IOException {
        if (manifest.length > 47_000) throw new IllegalArgumentException("Manifest exceeds cap");
        try (ZipOutputStream zip = new ZipOutputStream(Files.newOutputStream(stagingArchive,
                java.nio.file.StandardOpenOption.CREATE_NEW,
                java.nio.file.StandardOpenOption.WRITE))) {
            zip.putNextEntry(new ZipEntry("receipt-47.manifest"));
            zip.write(manifest);
            zip.closeEntry();
        }
    }
}''',
         cost="Writing B bytes costs O(B) compression work with buffering inside the stream. The method retains the caller's bounded byte array rather than another full copy. Archive finalization and later atomic publication add I/O that must complete before readers are told the artifact is ready.",
         mistakes=["Do not publish an archive before its stream closes.", "Do not leave a failed partial archive under a trusted final name.", "Do not accept unvalidated user-controlled entry names."],
         related=["java/gzip-output-footer-ownership", "java/atomic-file-publication", "java/zip-path-validation"]),
]

quiz_path = "quizzes/java-xml-archives"
quiz_title = "Java XML and archive boundaries quiz"
new_paths = ["java/" + lesson["slug"] for lesson in lessons] + [quiz_path]
assert len(new_paths) == len(set(new_paths)) and not set(new_paths) & lookup.keys()
titles = {row["path"]: row["title"] for row in entries}
titles.update({"java/" + lesson["slug"]: lesson["title"] for lesson in lessons})
titles[quiz_path] = quiz_title


def link(path):
    assert path in titles, path
    return f'<a href="/{html.escape(path)}">{html.escape(titles[path])}</a>'


def links(paths):
    return "<ul>" + "".join("<li>" + link(path) + "</li>" for path in dict.fromkeys(paths)) + "</ul>"


def related(paths):
    return [{"path": path, "title": titles[path]} for path in dict.fromkeys(paths)]


new_rows = []
for index, lesson in enumerate(lessons):
    path = "java/" + lesson["slug"]
    cohort = ["java/" + item["slug"] for item in lessons if item["group"] == lesson["group"] and item["slug"] != lesson["slug"]]
    connections = lesson["related"] + cohort + [quiz_path, "java/advanced-java"]
    body = ("<p>" + html.escape(lesson["definition"]) + "</p>"
            + "<h2>Operational contract</h2><p>" + html.escape(lesson["details"]) + "</p>"
            + "<h2>Failure case</h2><p>" + html.escape(lesson["case"]) + "</p>"
            + '<h2>Java code</h2><pre><code class="language-java">' + html.escape(lesson["code"], quote=False) + "</code></pre>"
            + "<h2>Performance and ownership cost</h2><p>" + html.escape(lesson["cost"]) + "</p>"
            + "<h3>Common Mistakes</h3><ul>" + "".join("<li>" + html.escape(item) + "</li>" for item in lesson["mistakes"]) + "</ul>"
            + "<h2>Connected lessons</h2>" + links(connections))
    row = copy.deepcopy(lookup["java/casts"])
    row.update(id=str(uuid.uuid5(uuid.NAMESPACE_URL, "https://aitrove.in/" + path)), path=path,
               title=lesson["title"], summary=lesson["definition"], body=body,
               subject="java-advanced", category="Programming", tags=["java", lesson["group"].lower(), lesson["slug"]],
               difficulty="Advanced", sort_order=34600 + index * 10, status="published",
               featured=False, published_at=stamp, created_at=stamp, updated_at=stamp)
    row["data"] = {"subject_root": "java/java", "section_path": "java/advanced-java",
                   "kind": "tutorial", "content_format": "html", "reading_minutes": max(5, round(len(re.sub("<[^>]+>", " ", body).split()) / 150)),
                   "author_path": "authors/aitrove-editorial", "related": related(connections),
                   "seo_ready": True, "java_release": lesson["release"], "java_version": str(lesson["release"]) + "+"}
    new_rows.append(row)

questions = [
    ("What must a DOM factory decide before untrusted XML is parsed?", "External resource access and processing limits", "Only output indentation", "Only the filename suffix", "Parsing can otherwise fetch outside resources or retain excessive structure."),
    ("Does StAX automatically cap how many receipt elements may arrive?", "No, the caller must enforce that limit", "Yes, at 47", "Yes, when a reader is closed", "Streaming changes retention, not the business element count."),
    ("Where does a user receipt ID belong when XPath uses a fixed selection?", "In a Java value comparison after selection", "Concatenated into the XPath source", "In a namespace prefix name", "The expression is application code; data should not alter it."),
    ("What should an XML Schema validator do with an unapproved external import?", "Reject it under the external-access policy", "Fetch it silently", "Treat it as a receipt ID", "The local schema root does not authorize outside dependencies."),
    ("Why bound serialized XML output separately from input?", "Escaping can increase emitted bytes", "Transformers always emit fewer bytes", "DOM never retains memory", "A source cap is not an output cap."),
    ("What identifies an XML element across different prefixes?", "Namespace URI and local name", "The sender's prefix spelling", "Its indentation", "Prefixes are document-local abbreviations."),
    ("Which limit matters for a compressed GZIP payload?", "The inflated byte count", "Only compressed input length", "Only the filename length", "Small compressed input can expand far beyond the upload size."),
    ("When is an in-memory GZIP result complete?", "After the compressor finishes or closes", "Immediately after construction", "Before the trailer is written", "The trailer is part of the stream."),
    ("Why reject duplicate ZIP entry names?", "Later readers may select different occurrences", "They always mean encryption", "They prove a valid schema", "Name lookup is ambiguous when duplicates are accepted."),
    ("What does a matching ZIP CRC32 prove?", "Accidental corruption was not detected by that check", "The sender is authenticated", "The data is encrypted", "CRC32 is not an authentication code."),
    ("When may a new ZIP archive be announced as complete?", "After entry and archive finalization succeed", "After putNextEntry alone", "Before ZipOutputStream closes", "The central directory must be written."),
    ("What should follow a failed archive or XML transformation?", "Reject or quarantine the incomplete result", "Publish its prefix", "Assume omitted bytes were optional", "Partial output is not a complete accepted artifact."),
]
quiz = copy.deepcopy(lookup["quizzes/java-io"])
quiz.update(id=str(uuid.uuid5(uuid.NAMESPACE_URL, "https://aitrove.in/" + quiz_path)), path=quiz_path,
            title=quiz_title, summary="Check XML parser policy, archive size, integrity, and finalization contracts.",
            body="<p>Choose the decision supported by each API contract. These are local self-check questions.</p><h2>Read the lessons</h2>" + links(new_paths[:-1]) + "<h3>Common Mistakes</h3><p>Do not treat a parser default, compressed input length, or checksum as a complete trust boundary.</p>",
            sort_order=34750, status="published", published_at=stamp, created_at=stamp, updated_at=stamp)
quiz["data"].update(content_format="html", subject_root="java/java", section_path="java/java-quizzes",
                    duration_minutes=18, seo_ready=True,
                    questions=[{"prompt": prompt,
                                "options": ([correct, wrong_a, wrong_b][index % 3:] + [correct, wrong_a, wrong_b][:index % 3]),
                                "answer": (-index) % 3, "explanation": explanation}
                               for index, (prompt, correct, wrong_a, wrong_b, explanation) in enumerate(questions)])
new_rows.append(quiz)

for group in dict.fromkeys(lesson["group"] for lesson in lessons):
    selected = ["java/" + item["slug"] for item in lessons if item["group"] == group]
    hub = lookup["java/advanced-java"]
    hub["data"]["modules"].append({"title": group, "summary": "Choose input, output, external-access, and failure limits.", "lessons": selected})
    hub["body"] += "<h2>" + html.escape(group) + "</h2><p>Keep every parser and archive boundary explicit.</p>" + links(selected)
    hub["updated_at"] = stamp
lookup["java/java-quizzes"]["data"]["modules"].append({"title": "XML and archive decisions", "summary": "Test parser and compressed-input boundaries.", "lessons": [quiz_path]})
lookup["java/java-quizzes"]["body"] += "<h2>XML and archive decisions</h2><p>Test the new parser and archive boundaries.</p>" + links([quiz_path])
lookup["java/java-quizzes"]["updated_at"] = stamp
lookup["java/java"]["body"] += "<h2>Further Java XML and archive topics</h2><p>Inspect parsing, compression, and file publication limits.</p>" + links(new_paths)
lookup["java/java"]["updated_at"] = stamp

backlinks = {
    "java/files": ["java/xml-dom-external-access-boundary", "java/gzip-inflated-byte-cap"],
    "java/zip-path-validation": ["java/zip-duplicate-entry-names", "java/zip-output-finalization"],
    "java/zip-entry-expanded-limit": ["java/gzip-inflated-byte-cap", "java/zip-entry-crc-boundary"],
    "java/atomic-file-publication": ["java/xml-transformer-bounded-output", "java/zip-output-finalization"],
    "java/charsetdecoder-report-policy": ["java/xml-dom-external-access-boundary"],
    "java/hmac-sha256-verify": ["java/zip-entry-crc-boundary"],
}
for old_path, targets in backlinks.items():
    old = lookup[old_path]
    old["body"] += "<p><strong>Continue with:</strong> " + ", ".join(link(target) for target in targets) + ".</p>"
    old["data"]["related"] = related([item["path"] for item in old["data"].get("related", [])] + targets)
    old["updated_at"] = stamp

entries.extend(new_rows)
fixture.write_text(json.dumps(entries, ensure_ascii=False, indent=2) + "\n")
print(json.dumps({"newArticles": len(lessons), "newQuizzes": 1, "newPaths": new_paths}))
