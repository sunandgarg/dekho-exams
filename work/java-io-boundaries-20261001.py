"""Add original Java I/O boundary lessons with executable examples."""

import copy
import datetime
import html
import json
import pathlib
import re
import uuid

ROOT = pathlib.Path(__file__).resolve().parents[1]
FILE = ROOT / "src/data/fixtures.json"
entries = json.loads(FILE.read_text())
lookup = {entry["path"]: entry for entry in entries}
stamp = datetime.datetime.now(datetime.UTC).isoformat()
added = []


def paragraph(value):
    escaped = html.escape(value)
    return "<p>" + re.sub(
        r"\[\[([^|]+)\|([^\]]+)\]\]",
        lambda match: '<a href="/' + match[1] + '">' + match[2] + "</a>",
        escaped,
    ) + "</p>"


def block(value, language="java"):
    return '<pre><code class="language-' + language + '">' + html.escape(value.strip(), quote=False) + "</code></pre>"


def add(slug, title, definition, sections, source, output, cost, mistakes, related, release=8):
    path = "java/" + slug
    if path in lookup:
        raise ValueError("Existing path: " + path)
    body = paragraph(definition)
    for heading, paragraphs in sections:
        body += "<h2>" + heading + "</h2>" + "".join(paragraph(item) for item in paragraphs)
    body += "<h2>Working program</h2>" + block(source)
    body += "<h3>Output</h3>" + block(output, "text")
    body += "<h2>Cost and ownership</h2>" + paragraph(cost)
    body += "<h3>Common Mistakes</h3><ul>" + "".join("<li>" + html.escape(item) + "</li>" for item in mistakes) + "</ul>"
    body += "<h2>Read next</h2>" + paragraph(
        ", ".join("[[" + item + "|" + lookup.get(item, {}).get("title", item.rsplit("/", 1)[-1].replace("-", " ")) + "]]" for item in related) + "."
    )
    entry = copy.deepcopy(lookup["java/casts"])
    entry.update(
        id=str(uuid.uuid5(uuid.NAMESPACE_URL, "https://aitrove.in/" + path)),
        path=path,
        title=title,
        summary=definition,
        body=body,
        subject="java-advanced",
        category="Programming",
        tags=["java", "io", slug],
        difficulty="Intermediate",
        sort_order=1040 + len(added),
        status="published",
        featured=False,
        published_at=stamp,
        created_at=stamp,
        updated_at=stamp,
    )
    entry["data"] = {
        "subject_root": "java/java",
        "section_path": "java/advanced-java",
        "kind": "tutorial",
        "content_format": "html",
        "reading_minutes": max(4, round(len(re.sub("<[^>]+>", " ", body).split()) / 150)),
        "author_path": "authors/aitrove-editorial",
        "related": [],
        "seo_ready": True,
        "java_release": release,
        "java_version": str(release) + "+",
    }
    entry["_related_paths"] = related
    entries.append(entry)
    lookup[path] = entry
    added.append(path)


add(
    "inputstream-short-read-loop",
    "Java InputStream short reads: assemble a complete record header",
    "InputStream.read(byte[]) may return fewer bytes than requested even when the stream has not ended.",
    [
        ("Treat the return count as the contract", [
            "A read call reports how many bytes it placed into the destination, or -1 at end of stream. A network stream, decompressor, or wrapper can deliver only part of a header. Parse only after the declared header width is present. A short positive read is progress, not proof of truncation.",
            "The loop below reads a four-byte message length from a stream that deliberately releases one byte per call. It rejects EOF before four bytes arrive. Follow the length with a separate [[java/readnbytes-truncated-frame|payload boundary]]; a valid header never proves that the body is complete."
        ]),
        ("Keep parser state local", [
            "Do not publish a partially filled header to downstream code. The caller receives a length only after all four bytes are assembled. A real framing protocol should also reject negative lengths and cap allocations before reading its payload; [[java/byte-streams|byte-stream copying]] covers the general read loop."
        ]),
    ],
    '''import java.io.ByteArrayInputStream;
import java.io.EOFException;
import java.io.IOException;
import java.io.InputStream;

public class InventoryFrameHeader {
    static int readLength(InputStream source) throws IOException {
        byte[] header = new byte[4];
        int received = 0;
        while (received < header.length) {
            int count = source.read(header, received, header.length - received);
            if (count == -1) throw new EOFException("short header");
            if (count == 0) continue;
            received += count;
        }
        return ((header[0] & 255) << 24) | ((header[1] & 255) << 16)
                | ((header[2] & 255) << 8) | (header[3] & 255);
    }

    public static void main(String[] args) throws IOException {
        byte[] wire = {0, 0, 0, 47};
        InputStream throttled = new ByteArrayInputStream(wire) {
            @Override public synchronized int read(byte[] target, int offset, int length) {
                return super.read(target, offset, Math.min(length, 1));
            }
        };
        System.out.println(readLength(throttled));
        try { readLength(new ByteArrayInputStream(new byte[] {0, 0, 0})); }
        catch (EOFException truncated) { System.out.println(truncated.getMessage()); }
    }
}''',
    "47\nshort header",
    "The header uses four bytes of fixed storage and O(4) read work, although a slow source can require four separate calls. A production loop also needs a deadline or cancellation policy for sources that can stall; the byte count alone does not impose one.",
    ["Do not assume one read fills the requested array.", "Do not parse a header after a positive but short read.", "Do not allocate a body directly from an unchecked length field."],
    ["java/readnbytes-truncated-frame", "java/datainputstream-readfully-eof", "java/byte-streams", "java/inputstream-available-not-length"],
)


add(
    "readnbytes-truncated-frame",
    "Java readNBytes: reject a truncated payload after the header",
    "InputStream.readNBytes(n) returns at most n bytes; an early end of stream can make the returned array shorter.",
    [
        ("Validate the declared length", [
            "A wire header is untrusted input. Check its sign and a protocol maximum before asking readNBytes to allocate. Then compare the returned array length with the declared size. End of stream after the header is a truncated frame, not an empty field or a successful partial message.",
            "This example uses a one-byte length prefix to isolate the rule. Larger frames should use a bounded [[java/inputstream-short-read-loop|header reader]] and a fixed-size chunk loop when allocation pressure matters."
        ]),
        ("Decide who owns the bytes", [
            "The returned array belongs to the caller. Do not expose it as mutable shared application state without a copy or a clear ownership transfer. A [[java/datainputstream-readfully-eof|readFully]] call provides a different API contract but still requires a maximum before buffer allocation."
        ]),
    ],
    '''import java.io.ByteArrayInputStream;
import java.io.EOFException;
import java.io.IOException;
import java.io.InputStream;
import java.nio.charset.StandardCharsets;

public class ShipmentFrameReader {
    static String readShipment(InputStream wire) throws IOException {
        int declared = wire.read();
        if (declared < 0) throw new EOFException("missing length");
        if (declared > 64) throw new IOException("frame too large");
        byte[] payload = wire.readNBytes(declared);
        if (payload.length != declared) throw new EOFException("truncated payload");
        return new String(payload, StandardCharsets.US_ASCII);
    }

    public static void main(String[] args) throws IOException {
        System.out.println(readShipment(new ByteArrayInputStream(new byte[] {4, 'A', 'B', '4', '7'})));
        try { readShipment(new ByteArrayInputStream(new byte[] {5, 'A', 'B'})); }
        catch (EOFException truncated) { System.out.println(truncated.getMessage()); }
    }
}''',
    "AB47\ntruncated payload",
    "readNBytes allocates up to the requested payload size, so the cap is a memory policy, not an optional validation. Time is O(n) for n bytes received. This example targets Java 11 or later; a streaming decoder can avoid retaining the whole frame.",
    ["Do not infer that readNBytes always returns the requested count.", "Do not let a header dictate an unbounded allocation.", "Do not treat an incomplete payload as a valid message."],
    ["java/inputstream-short-read-loop", "java/datainputstream-readfully-eof", "java/byte-streams", "java/strict-utf8"],
    11,
)


add(
    "datainputstream-readfully-eof",
    "Java DataInputStream.readFully: EOF can leave partial bytes in the buffer",
    "DataInputStream.readFully fills the requested region or throws EOFException, and an EOF failure may occur after some destination bytes were changed.",
    [
        ("Keep tentative data private", [
            "A caller should not reuse a partially filled buffer as though it were a complete record. Allocate the record buffer inside the operation, invoke readFully, then return it only on success. The exception is part of the framing contract; it is not permission to process the bytes already copied.",
            "The first read succeeds. The second throws after two bytes, and the program prints the private buffer so the partial mutation is visible. [[java/readnbytes-truncated-frame|readNBytes]] expresses a similar boundary through a short returned array instead."
        ]),
        ("Bound the destination before reading", [
            "readFully does not decide whether a declared record size is safe. Validate the protocol length before allocating. For a long-running stream, also consider cancellation and deadlines; a blocking read can wait for remaining bytes."
        ]),
    ],
    '''import java.io.ByteArrayInputStream;
import java.io.DataInputStream;
import java.io.EOFException;
import java.io.IOException;
import java.util.Arrays;

public class InvoiceRecordBoundary {
    static byte[] record(byte[] wire) throws IOException {
        byte[] destination = new byte[4];
        try (DataInputStream input = new DataInputStream(new ByteArrayInputStream(wire))) {
            input.readFully(destination);
        }
        return destination;
    }

    public static void main(String[] args) throws IOException {
        System.out.println(Arrays.toString(record(new byte[] {7, 8, 9, 10})));
        byte[] tentative = new byte[4];
        try (DataInputStream input = new DataInputStream(new ByteArrayInputStream(new byte[] {7, 8}))) {
            try { input.readFully(tentative); }
            catch (EOFException truncated) { System.out.println(Arrays.toString(tentative)); }
        }
    }
}''',
    "[7, 8, 9, 10]\n[7, 8, 0, 0]",
    "The fixed four-byte buffer costs O(1) space here; a general record of length n costs O(n) storage and read work. A failed read retains only tentative local data, so callers cannot accidentally publish an incomplete record.",
    ["Do not assume an exception leaves the destination unchanged.", "Do not expose a record buffer before readFully returns.", "Do not allocate an unbounded buffer from an external length."],
    ["java/inputstream-short-read-loop", "java/readnbytes-truncated-frame", "java/byte-streams", "java/try-with-resources"],
)


add(
    "charsetdecoder-report-policy",
    "Java CharsetDecoder: reject malformed UTF-8 instead of replacing bytes",
    "CharsetDecoder can report malformed and unmappable input as errors rather than silently substituting replacement characters.",
    [
        ("Make the data-loss policy explicit", [
            "A replacement character can hide a damaged identifier or signature. Set both error actions to REPORT when the text is a protocol field that must round-trip exactly. If replacement is acceptable for display-only content, make that a separate path and label it accordingly.",
            "The fixture decodes one valid identifier and rejects a malformed two-byte sequence. A [[java/strict-utf8|strict UTF-8 reader]] covers file input; this lesson shows the decoder policy directly for in-memory bytes."
        ]),
        ("Keep character and byte lengths separate", [
            "A byte cap does not imply the same character cap. UTF-8 characters can occupy multiple bytes, and a Java String uses UTF-16 code units. Enforce each limit at the layer where it matters, before allocating or persisting."
        ]),
    ],
    '''import java.nio.ByteBuffer;
import java.nio.charset.CharacterCodingException;
import java.nio.charset.CodingErrorAction;
import java.nio.charset.StandardCharsets;

public class SupplierIdentifierDecoder {
    static String decode(byte[] bytes) throws CharacterCodingException {
        return StandardCharsets.UTF_8.newDecoder()
                .onMalformedInput(CodingErrorAction.REPORT)
                .onUnmappableCharacter(CodingErrorAction.REPORT)
                .decode(ByteBuffer.wrap(bytes)).toString();
    }

    public static void main(String[] args) throws CharacterCodingException {
        System.out.println(decode(new byte[] {'S', 'U', 'P', '-', '4', '7'}));
        try { decode(new byte[] {(byte) 0xC3, (byte) 0x28}); }
        catch (CharacterCodingException invalid) { System.out.println("invalid UTF-8 rejected"); }
    }
}''',
    "SUP-47\ninvalid UTF-8 rejected",
    "Decoding is O(n) in input bytes and materializes characters in memory. A per-call decoder keeps mutable decoding state local; for a streaming pipeline, reuse one decoder within a single stream and handle underflow and overflow explicitly.",
    ["Do not accept replacement characters silently in identifiers.", "Do not count UTF-8 bytes as Java characters.", "Do not share one mutable decoder across unrelated concurrent operations."],
    ["java/strict-utf8", "java/bytebuffer-flip-compact-state", "java/files", "java/decimal-parse-boundary"],
)


add(
    "bytebuffer-flip-compact-state",
    "Java ByteBuffer flip and compact: preserve an incomplete frame",
    "ByteBuffer.flip changes a buffer from writing to reading, while compact moves unread bytes to the front for the next write cycle.",
    [
        ("Carry unfinished input across reads", [
            "A stream chunk may end halfway through a record. After flip, consume only complete records; compact retains the unread suffix and sets the position after it. The next chunk appends there. Clearing the buffer would discard the partial record, while flipping twice without a write would distort the limit.",
            "This three-byte record arrives in two chunks. The parser waits until all three bytes are present. [[java/inputstream-short-read-loop|Short reads]] explain why chunk boundaries cannot be treated as message boundaries."
        ]),
        ("Cap the record format", [
            "A fixed buffer works only if the largest accepted record fits. For variable-length frames, reject oversize declarations or move to a bounded spill strategy before compact can leave the buffer permanently full. [[java/bytebuffer-order|Byte order]] matters when a frame contains multibyte numeric fields."
        ]),
    ],
    '''import java.nio.ByteBuffer;

public class DispatchFrameAccumulator {
    static void accept(ByteBuffer pending, byte[] chunk) {
        pending.put(chunk);
        pending.flip();
        while (pending.remaining() >= 3) {
            int site = pending.get() & 255;
            int quantity = pending.get() & 255;
            int checksum = pending.get() & 255;
            System.out.println(site + ":" + quantity + ":" + checksum);
        }
        pending.compact();
    }

    public static void main(String[] args) {
        ByteBuffer pending = ByteBuffer.allocate(6);
        accept(pending, new byte[] {47, 2});
        System.out.println("pending=" + pending.position());
        accept(pending, new byte[] {49, 82, 3, 85});
        System.out.println("pending=" + pending.position());
    }
}''',
    "pending=2\n47:2:49\n82:3:85\npending=0",
    "Each complete three-byte frame is parsed once. compact copies the unread suffix, so repeated compaction of a large partial record can add copy cost; a size cap and chunk plan keep that cost predictable. The buffer owns six bytes here.",
    ["Do not call clear when unread bytes must survive.", "Do not parse a record merely because a transport read ended.", "Do not call put when the buffer lacks space for the next chunk."],
    ["java/inputstream-short-read-loop", "java/bytebuffer-order", "java/bytebuffer-slice-ownership", "java/file-channels"],
)


add(
    "writable-channel-short-write",
    "Java WritableByteChannel short writes: drain the ByteBuffer",
    "WritableByteChannel.write may consume only part of a ByteBuffer, so a complete write requires checking remaining bytes.",
    [
        ("Loop on the buffer state", [
            "The buffer position advances by the count actually written. Continue until hasRemaining is false. The fixture uses a channel that accepts at most two bytes per call, making the short-write path deterministic instead of relying on a particular filesystem or socket.",
            "[[java/file-channels|FileChannel writing]] follows the same position rule. For a nonblocking channel, write can return zero because it is not ready; register for writability or apply a deadline instead of spinning forever."
        ]),
        ("Define completion before publication", [
            "Only publish or acknowledge a record once its entire buffer has been accepted by the channel. Acceptance by a channel is not always durable storage: a file may also require a force policy, while a socket needs an application-level acknowledgment if remote processing matters. [[java/atomic-file-publication|Atomic file publication]] handles a separate visibility boundary."
        ]),
    ],
    '''import java.io.ByteArrayOutputStream;
import java.io.IOException;
import java.nio.ByteBuffer;
import java.nio.channels.WritableByteChannel;
import java.nio.charset.StandardCharsets;

public class ManifestChannelWriter {
    static class TwoByteChannel implements WritableByteChannel {
        private final ByteArrayOutputStream sink = new ByteArrayOutputStream();
        private boolean open = true;
        public int write(ByteBuffer source) {
            int count = Math.min(2, source.remaining());
            for (int index = 0; index < count; index++) sink.write(source.get());
            return count;
        }
        public boolean isOpen() { return open; }
        public void close() { open = false; }
        String contents() { return new String(sink.toByteArray(), StandardCharsets.US_ASCII); }
    }

    public static void main(String[] args) throws IOException {
        TwoByteChannel channel = new TwoByteChannel();
        ByteBuffer record = ByteBuffer.wrap("LOT-47".getBytes(StandardCharsets.US_ASCII));
        int calls = 0;
        while (record.hasRemaining()) { channel.write(record); calls++; }
        System.out.println(channel.contents());
        System.out.println("calls=" + calls);
        channel.close();
    }
}''',
    "LOT-47\ncalls=3",
    "The loop processes n bytes in O(n) total transfer work and keeps only the input buffer plus the sink. A production nonblocking channel must wait for readiness on zero-byte writes; this blocking-style demonstration always advances and therefore cannot spin.",
    ["Do not assume one write drains the buffer.", "Do not reset position between partial writes.", "Do not busy-loop on a nonblocking channel that returns zero."],
    ["java/file-channels", "java/bytebuffer-flip-compact-state", "java/atomic-file-publication", "java/byte-streams"],
)


add(
    "zip-entry-expanded-limit",
    "Java ZIP entry extraction: cap expanded bytes while reading",
    "A ZIP entry can expand far beyond its compressed size, so enforce a decompressed-byte limit during extraction.",
    [
        ("Count actual output", [
            "Metadata such as an entry's compressed size is not a safe allocation or acceptance limit. Count bytes returned by ZipInputStream.read and stop as soon as a configured expanded limit is exceeded. The fixture creates its own in-memory ZIP; its extraction path rejects a 47-byte entry under a 32-byte cap.",
            "Path traversal is a different boundary. If extracting to disk, validate destination paths as described in [[java/zip-path-validation|ZIP path validation]] and decide how to clean up a partial file after rejection."
        ]),
        ("Budget the whole archive", [
            "A per-entry cap alone permits many entries to consume unlimited total output. Add entry count, aggregate expanded bytes, compression ratio or CPU budget where appropriate. Read incrementally; [[java/byte-streams|a bounded copy loop]] avoids materializing the entire expanded entry in memory."
        ]),
    ],
    '''import java.io.ByteArrayInputStream;
import java.io.ByteArrayOutputStream;
import java.io.IOException;
import java.util.zip.ZipEntry;
import java.util.zip.ZipInputStream;
import java.util.zip.ZipOutputStream;

public class ArchiveExpansionGate {
    static byte[] archive(int payloadLength) throws IOException {
        ByteArrayOutputStream bytes = new ByteArrayOutputStream();
        try (ZipOutputStream zip = new ZipOutputStream(bytes)) {
            zip.putNextEntry(new ZipEntry("inventory.txt"));
            for (int index = 0; index < payloadLength; index++) zip.write('X');
            zip.closeEntry();
        }
        return bytes.toByteArray();
    }

    static int expandedSize(byte[] archive, int maximum) throws IOException {
        try (ZipInputStream zip = new ZipInputStream(new ByteArrayInputStream(archive))) {
            if (zip.getNextEntry() == null) throw new IOException("missing entry");
            byte[] chunk = new byte[16];
            int total = 0;
            int count;
            while ((count = zip.read(chunk)) != -1) {
                if (count > maximum - total) throw new IOException("expanded limit exceeded");
                total += count;
            }
            return total;
        }
    }

    public static void main(String[] args) throws IOException {
        System.out.println(expandedSize(archive(12), 32));
        try { expandedSize(archive(47), 32); }
        catch (IOException rejected) { System.out.println(rejected.getMessage()); }
    }
}''',
    "12\nexpanded limit exceeded",
    "The extractor uses a 16-byte chunk and constant working memory per entry. Counting is O(n) in expanded bytes read until rejection. The in-memory test archive itself uses O(n) storage only to keep this standalone program runnable.",
    ["Do not trust ZIP size metadata as the only limit.", "Do not omit an aggregate archive budget.", "Do not treat a byte cap as protection against unsafe destination paths."],
    ["java/zip-path-validation", "java/byte-streams", "java/inputstream-short-read-loop", "java/atomic-file-publication"],
)


add(
    "bounded-line-reader",
    "Java bounded line reader: reject oversized records without buffering the file",
    "A line-oriented parser should cap each record before accumulating an unbounded String or list of lines.",
    [
        ("Apply the limit while reading", [
            "The reader accepts a fixed maximum of content characters per line. A newline ends the record; a preceding carriage return is removed for CRLF input. Count characters as they arrive and reject the first one beyond the limit. Reading every line first and checking lengths afterward loses the memory bound.",
            "The implementation returns null only when EOF arrives before any record character. A final line without a newline is still valid. See [[java/files|file I/O ownership]] for closing an actual file reader and [[java/strict-utf8|strict decoding]] if malformed bytes must be rejected before characters reach this parser."
        ]),
        ("Define what a character limit means", [
            "This limit counts UTF-16 code units because Reader.read returns char values. A protocol limit expressed in UTF-8 bytes or Unicode code points needs a different counter. Keep the unit explicit in the API contract, especially when supplementary characters are permitted."
        ]),
    ],
    '''import java.io.IOException;
import java.io.Reader;
import java.io.StringReader;

public class BoundedManifestLine {
    static String readLine(Reader source, int maximumChars) throws IOException {
        if (maximumChars < 0) throw new IllegalArgumentException("negative limit");
        StringBuilder line = new StringBuilder();
        int next;
        while ((next = source.read()) != -1) {
            if (next == '\\n') break;
            if (line.length() >= maximumChars + 1L) throw new IOException("line too long");
            line.append((char) next);
        }
        if (next == -1 && line.length() == 0) return null;
        if (line.length() > 0 && line.charAt(line.length() - 1) == '\\r') line.setLength(line.length() - 1);
        if (line.length() > maximumChars) throw new IOException("line too long");
        return line.toString();
    }

    public static void main(String[] args) throws IOException {
        System.out.println(readLine(new StringReader("lot-47\\r\\n"), 6));
        try { readLine(new StringReader("shipment-82"), 6); }
        catch (IOException rejected) { System.out.println(rejected.getMessage()); }
    }
}''',
    "lot-47\nline too long",
    "The parser is O(n) in characters read and O(limit) in retained line storage. It allows one extra code unit temporarily so a terminal CR can be distinguished from content, then enforces the final content cap. A Reader still needs a byte-level input cap if decoding expansion or source volume matters.",
    ["Do not call readAllLines on an untrusted large file before validation.", "Do not confuse UTF-16 code units with UTF-8 bytes.", "Do not discard a valid last line merely because it lacks a newline."],
    ["java/files", "java/strict-utf8", "java/inputstream-short-read-loop", "java/stream-resource-lifetime"],
)


add(
    "inputstream-available-not-length",
    "Java InputStream.available is not the remaining stream length",
    "InputStream.available estimates bytes readable without blocking; it is not an end-of-stream test or total-size query.",
    [
        ("Read until the stream contract ends", [
            "A stream may have data even when available returns zero. The fixture overrides available to report zero while three bytes remain, then reads those bytes normally. Code that allocates available bytes and calls the job complete would silently drop the record.",
            "Use a [[java/inputstream-short-read-loop|read loop]] or a bounded [[java/readnbytes-truncated-frame|framed read]] instead. If the input format has a length prefix, validate that prefix independently of available."
        ]),
        ("Avoid false size assumptions", [
            "Some in-memory streams return a convenient remaining count, but code that works only on those streams can fail on sockets and wrappers. available is a scheduling hint for a narrow purpose. It does not replace protocol framing, EOF handling, or an input budget."
        ]),
    ],
    '''import java.io.ByteArrayInputStream;
import java.io.IOException;
import java.io.InputStream;

public class InventoryInputAvailability {
    public static void main(String[] args) throws IOException {
        InputStream source = new ByteArrayInputStream(new byte[] {47, 82, 15}) {
            @Override public synchronized int available() { return 0; }
        };
        System.out.println("available=" + source.available());
        int total = 0;
        int next;
        while ((next = source.read()) != -1) total += next;
        System.out.println("sum=" + total);
    }
}''',
    "available=0\nsum=144",
    "This single-byte loop is O(n) calls and constant storage; a buffered block read reduces call overhead for larger inputs. The important boundary is semantic: only read returning -1 identifies EOF for this stream.",
    ["Do not treat available equal to zero as EOF.", "Do not allocate the entire input from available.", "Do not generalize an in-memory stream's available behavior to network streams."],
    ["java/inputstream-short-read-loop", "java/readnbytes-truncated-frame", "java/byte-streams", "java/files"],
)


add(
    "bytebuffer-slice-ownership",
    "Java ByteBuffer.slice: shared storage and independent cursors",
    "ByteBuffer.slice creates a new view over the selected remaining bytes, with independent position and limit but shared content.",
    [
        ("Separate cursor independence from data independence", [
            "Moving the slice position does not move the parent's position. Writing through the slice does change the parent's bytes. A slice is useful for parsing a framed region without copying it, but it is unsafe as a long-lived snapshot when the parent buffer is reused for more input.",
            "The fixture selects bytes at parent indexes one through three, writes into the slice, and observes the parent changed while its cursor stays at one. [[java/bytebuffer-flip-compact-state|flip and compact]] manage buffer reuse; those operations can make a retained slice point at different logical data."
        ]),
        ("Copy at ownership boundaries", [
            "If an asynchronous task needs stable bytes after the read loop continues, copy the selected range or transfer exclusive ownership of the backing buffer. [[java/array-copy-ownership|Array copying]] addresses the same distinction for arrays; a read-only view prevents writes through that view but still reflects writes through other aliases."
        ]),
    ],
    '''import java.nio.ByteBuffer;
import java.util.Arrays;

public class ManifestFieldSlice {
    public static void main(String[] args) {
        ByteBuffer parent = ByteBuffer.wrap(new byte[] {10, 20, 30, 40, 50});
        parent.position(1);
        parent.limit(4);
        ByteBuffer field = parent.slice();
        field.put(0, (byte) 82);
        field.position(2);
        System.out.println(Arrays.toString(parent.array()));
        System.out.println("parent=" + parent.position() + ", field=" + field.position());
    }
}''',
    "[10, 82, 30, 40, 50]\nparent=1, field=2",
    "Creating a slice is O(1) and does not copy bytes. The memory retained by the view can include the parent's entire backing storage; a small long-lived slice can therefore keep a large parent allocation reachable.",
    ["Do not call a slice a snapshot.", "Do not assume parent and slice share cursor positions.", "Do not retain a slice after the backing buffer is repurposed without an ownership rule."],
    ["java/bytebuffer-flip-compact-state", "java/bytebuffer-order", "java/array-copy-ownership", "java/file-channels"],
)


for path in added:
    entry = lookup[path]
    entry["data"]["related"] = [
        {"path": target, "title": lookup[target]["title"]}
        for target in entry.pop("_related_paths")
    ]

hub = lookup["java/advanced-java"]
title = "I/O framing and memory boundaries"
hub["data"]["modules"] = [item for item in hub["data"]["modules"] if item["title"] != title]
hub["data"]["modules"].append({
    "title": title,
    "summary": "Reject short records, malformed text, unbounded expansion, and shared-buffer surprises.",
    "lessons": added,
})
hub["updated_at"] = stamp

reverse = {
    "java/byte-streams": ["java/inputstream-short-read-loop", "java/readnbytes-truncated-frame", "java/inputstream-available-not-length"],
    "java/file-channels": ["java/writable-channel-short-write", "java/bytebuffer-flip-compact-state", "java/bytebuffer-slice-ownership"],
    "java/strict-utf8": ["java/charsetdecoder-report-policy", "java/bounded-line-reader"],
    "java/zip-path-validation": ["java/zip-entry-expanded-limit"],
    "java/files": ["java/bounded-line-reader", "java/inputstream-available-not-length"],
    "java/bytebuffer-order": ["java/bytebuffer-flip-compact-state", "java/bytebuffer-slice-ownership"],
}
for path, targets in reverse.items():
    entry = lookup[path]
    marker = "<h2>More I/O boundary cases</h2>"
    entry["body"] = entry["body"].split(marker)[0] + marker + paragraph(
        "Continue with " + ", ".join("[[" + target + "|" + lookup[target]["title"] + "]]" for target in targets) + "."
    )
    entry["updated_at"] = stamp

FILE.write_text(json.dumps(entries, ensure_ascii=False, indent=2) + "\n")
print("Added", len(added), "Java lessons; linked from", len(reverse), "existing lessons")
