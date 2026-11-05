"""Add original Java cryptographic API boundary lessons."""

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


def add(slug, title, definition, sections, source, output, cost, mistakes, related):
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
        ", ".join("[[" + target + "|" + lookup.get(target, {}).get("title", target.rsplit("/", 1)[-1].replace("-", " ")) + "]]" for target in related) + "."
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
        tags=["java", "cryptography", slug],
        difficulty="Advanced",
        sort_order=1400 + len(added),
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
        "java_release": 8,
        "java_version": "8+",
    }
    entry["_related_paths"] = related
    entries.append(entry)
    lookup[path] = entry
    added.append(path)


add(
    "sha256-explicit-utf8",
    "Java SHA-256: hash declared bytes, not an implicit string encoding",
    "MessageDigest hashes bytes; a text digest is reproducible only when the text-to-byte encoding is part of the protocol.",
    [
        ("Define the byte contract", [
            "A receipt checksum calculated with the platform default charset can change when the job moves to another runtime. Encode the exact text with UTF-8 before hashing, and decide separately whether line endings and Unicode normalization are canonicalized. The fixture uses an accented receipt marker so the byte count is visible.",
            "A plain digest detects accidental changes only when its expected value is trusted through another channel. It does not authenticate a message from an attacker who can replace both bytes and digest. Use [[java/hmac-sha256-verify|HMAC verification]] for shared-key authentication."
        ]),
        ("Keep passwords out of this workflow", [
            "SHA-256 is intentionally fast. Storing password digests directly with this method makes guessing inexpensive; password storage needs a purpose-built, tuned password hashing scheme and its own migration policy. [[java/unicode-encoding|Unicode encoding]] covers the bytes being hashed."
        ]),
    ],
    '''import java.nio.charset.StandardCharsets;
import java.security.MessageDigest;
import java.util.Arrays;

public class ReceiptDigestBytes {
    public static void main(String[] args) throws Exception {
        byte[] receiptBytes = "café".getBytes(StandardCharsets.UTF_8);
        byte[] first = MessageDigest.getInstance("SHA-256").digest(receiptBytes);
        byte[] second = MessageDigest.getInstance("SHA-256").digest(receiptBytes);
        System.out.println("bytes=" + receiptBytes.length);
        System.out.println("digestBytes=" + first.length);
        System.out.println("same=" + Arrays.equals(first, second));
    }
}''',
    "bytes=5\ndigestBytes=32\nsame=true",
    "Hashing visits the input bytes and keeps fixed-size digest state, while this program allocates the UTF-8 byte array and result. For a large file, stream chunks instead of loading it all into memory. The digest cannot reconstruct the input or substitute for a MAC.",
    ["Do not call getBytes without an explicit charset in a wire protocol.", "Do not treat a public digest as proof of origin.", "Do not store passwords as a bare SHA-256 digest."],
    ["java/unicode-encoding", "java/hmac-sha256-verify", "java/message-digest-bytebuffer", "java/byte-streams"],
)


add(
    "message-digest-bytebuffer",
    "Java MessageDigest.update(ByteBuffer): the input position moves to its limit",
    "MessageDigest.update(ByteBuffer) reads the buffer's remaining bytes and advances its position to the limit.",
    [
        ("Hash the intended slice", [
            "A packet buffer may contain a header followed by a payload. If the protocol authenticates only the payload, position the buffer at the payload boundary before updating the digest. The method consumes the remaining view; a later parser must duplicate or reposition the buffer deliberately.",
            "The fixture compares the buffer update with a fresh digest of the text payload. The matching result verifies this one slice, not any hidden metadata. [[java/bytebuffer-order|ByteBuffer layout]] covers position and limit rules used by binary protocols."
        ]),
        ("Keep reusable state local", [
            "A MessageDigest instance is mutable. Calling digest finishes and resets it, so a second computation on the same instance needs its own input updates. Do not share one instance across independent concurrent requests."
        ]),
    ],
    '''import java.nio.ByteBuffer;
import java.nio.charset.StandardCharsets;
import java.security.MessageDigest;
import java.util.Arrays;

public class PacketPayloadDigest {
    public static void main(String[] args) throws Exception {
        ByteBuffer packet = ByteBuffer.wrap("header:data-47".getBytes(StandardCharsets.UTF_8));
        packet.position(7);
        MessageDigest digest = MessageDigest.getInstance("SHA-256");
        digest.update(packet);
        byte[] payloadHash = digest.digest();
        byte[] directHash = MessageDigest.getInstance("SHA-256").digest("data-47".getBytes(StandardCharsets.UTF_8));
        System.out.println("remaining=" + packet.remaining());
        System.out.println("same=" + Arrays.equals(payloadHash, directHash));
    }
}''',
    "remaining=0\nsame=true",
    "The digest processes O(n) remaining bytes with fixed-size internal state; the fixture's packet and result arrays use space proportional to their sizes. Moving a buffer position is cheap, but silently reusing a consumed buffer changes what later code reads.",
    ["Do not assume update(ByteBuffer) leaves position unchanged.", "Do not hash an entire backing array when only the remaining slice is authorized.", "Do not share mutable MessageDigest state across requests."],
    ["java/bytebuffer-order", "java/sha256-explicit-utf8", "java/byte-streams", "java/hmac-sha256-verify"],
)


add(
    "hmac-sha256-verify",
    "Java HmacSHA256 verification: reject a changed message",
    "HMAC authenticates bytes using a secret key shared by the signer and verifier.",
    [
        ("Verify the exact serialized message", [
            "The verifier must calculate the MAC over the same byte sequence the signer used. Reformatting a timestamp or changing whitespace before verification changes the message. This fixture generates a process-local key, signs one dispatch record, then shows that a changed record does not match.",
            "The key exists only for this run. Production key creation, storage, access control, rotation, and version tags need a separate design. A digest alone cannot provide this origin check; [[java/sha256-explicit-utf8|SHA-256 byte hashing]] covers the distinction."
        ]),
        ("Frame multiple fields", [
            "Concatenating variable-length fields without boundaries can make different records produce identical MAC input bytes. [[java/hmac-field-framing|Field framing]] gives a small counterexample. Keep the algorithm identifier and key version with stored tags so verification can select the right key after rotation."
        ]),
    ],
    '''import java.nio.charset.StandardCharsets;
import java.security.MessageDigest;
import javax.crypto.KeyGenerator;
import javax.crypto.Mac;
import javax.crypto.SecretKey;

public class DispatchRecordMac {
    static byte[] tag(SecretKey key, String record) throws Exception {
        Mac signer = Mac.getInstance("HmacSHA256");
        signer.init(key);
        return signer.doFinal(record.getBytes(StandardCharsets.UTF_8));
    }

    public static void main(String[] args) throws Exception {
        KeyGenerator generator = KeyGenerator.getInstance("HmacSHA256");
        SecretKey key = generator.generateKey();
        byte[] storedTag = tag(key, "dispatch=R-47");
        System.out.println("accepted=" + MessageDigest.isEqual(storedTag, tag(key, "dispatch=R-47")));
        System.out.println("tampered=" + MessageDigest.isEqual(storedTag, tag(key, "dispatch=R-48")));
    }
}''',
    "accepted=true\ntampered=false",
    "MAC computation processes O(n) message bytes and returns a fixed-size tag; the example allocates text bytes and tag arrays. Verification cost is small compared with key lifecycle risk. Do not log the key or treat a test-generated ephemeral key as persistent configuration.",
    ["Do not compare a tag over one serialization with a different serialization.", "Do not hard-code a production HMAC key in source.", "Do not confuse HMAC with encryption; the message remains readable."],
    ["java/hmac-field-framing", "java/sha256-explicit-utf8", "java/secure-random-token-encoding", "java/tls-local-project"],
)


add(
    "hmac-field-framing",
    "Java HMAC field framing: prevent ambiguous concatenation",
    "A MAC authenticates bytes, so two distinct field tuples that serialize to the same bytes receive the same tag under one key.",
    [
        ("Encode boundaries before signing", [
            "The pairs (AB, C) and (A, BC) both become ABC under naive concatenation. That is not a cryptographic collision; the application supplied identical input. Prefix each UTF-8 field with its byte length before updating the MAC so tuple boundaries survive serialization.",
            "The fixture prints equality for both encodings. This format is only a local protocol sketch: a stored protocol also needs a version and a canonical definition for every field type. [[java/hmac-sha256-verify|HMAC verification]] explains the tag's authentication role."
        ]),
        ("Validate lengths at ingestion", [
            "A length prefix does not limit the resource cost of an untrusted field. Cap each field before allocating or MACing it; reject a negative or oversized advertised length in a decoder before reading a body."
        ]),
    ],
    '''import java.io.ByteArrayOutputStream;
import java.io.DataOutputStream;
import java.nio.charset.StandardCharsets;
import java.security.MessageDigest;
import javax.crypto.KeyGenerator;
import javax.crypto.Mac;
import javax.crypto.SecretKey;

public class OrderTupleTag {
    static byte[] framed(String first, String second) throws Exception {
        ByteArrayOutputStream bytes = new ByteArrayOutputStream();
        DataOutputStream output = new DataOutputStream(bytes);
        for (String field : new String[] { first, second }) {
            byte[] encoded = field.getBytes(StandardCharsets.UTF_8);
            output.writeInt(encoded.length);
            output.write(encoded);
        }
        return bytes.toByteArray();
    }

    static byte[] tag(SecretKey key, byte[] message) throws Exception {
        Mac signer = Mac.getInstance("HmacSHA256");
        signer.init(key);
        return signer.doFinal(message);
    }

    public static void main(String[] args) throws Exception {
        SecretKey key = KeyGenerator.getInstance("HmacSHA256").generateKey();
        byte[] leftRaw = tag(key, "ABC".getBytes(StandardCharsets.UTF_8));
        byte[] rightRaw = tag(key, ("A" + "BC").getBytes(StandardCharsets.UTF_8));
        System.out.println("raw same=" + MessageDigest.isEqual(leftRaw, rightRaw));
        System.out.println("framed same=" + MessageDigest.isEqual(tag(key, framed("AB", "C")), tag(key, framed("A", "BC"))));
    }
}''',
    "raw same=true\nframed same=false",
    "Framing and MAC calculation each process the fields' bytes, so time and temporary memory grow with total encoded length. A streaming encoder can avoid the whole-message buffer when records are large; its verifier must use exactly the same field order and lengths.",
    ["Do not concatenate variable-length fields without a boundary rule.", "Do not mistake an application serialization collision for a hash-function collision.", "Do not accept an unbounded advertised field length."],
    ["java/hmac-sha256-verify", "java/bytebuffer-order", "java/datainputstream-readfully-eof", "java/sha256-explicit-utf8"],
)


add(
    "secure-random-token-encoding",
    "Java SecureRandom token encoding: preserve unpredictable bytes in a URL-safe form",
    "A random bearer token starts as bytes from SecureRandom; Base64 URL encoding only turns those bytes into transport-safe text.",
    [
        ("Generate before encoding", [
            "The fixture draws 32 bytes and encodes them without padding. The exact token changes on every run, so it reports only the resulting length and alphabet. The encoding does not add entropy, and a readable token is still a credential that must be protected from logs and referrers.",
            "[[java/secure-random-tokens|Token lifecycle]] covers storage and expiry. [[java/base64-url-vs-basic|Base64 alphabets]] explains why a URL-safe token may not decode under a basic alphabet."
        ]),
        ("Treat collision policy separately", [
            "A large random space reduces accidental collisions, but an issuing service should still enforce uniqueness in its storage boundary. Hash stored bearer tokens when lookup design permits, and compare an incoming token under a defined authentication policy."
        ]),
    ],
    '''import java.security.SecureRandom;
import java.util.Base64;

public class RecoveryTokenText {
    public static void main(String[] args) {
        byte[] tokenBytes = new byte[32];
        new SecureRandom().nextBytes(tokenBytes);
        String token = Base64.getUrlEncoder().withoutPadding().encodeToString(tokenBytes);
        System.out.println("characters=" + token.length());
        System.out.println("urlSafe=" + token.matches("[A-Za-z0-9_-]+"));
    }
}''',
    "characters=43\nurlSafe=true",
    "Generating and encoding n bytes takes work and output storage proportional to n. Encoding expands 32 bytes to 43 unpadded URL-safe characters here; it does not make the token secret after disclosure. Avoid repeatedly constructing a generator for every token in a high-volume issuer.",
    ["Do not use java.util.Random for a bearer credential.", "Do not log the token merely because it is printable.", "Do not confuse Base64 encoding with encryption or hashing."],
    ["java/secure-random-tokens", "java/base64-url-vs-basic", "java/sha256-explicit-utf8", "java/tls-local-project"],
)


add(
    "aes-gcm-authenticated-decryption",
    "Java AES-GCM: reject a changed ciphertext before accepting plaintext",
    "AES-GCM combines encryption with an authentication tag; decryption must reject a record whose ciphertext or tag was changed.",
    [
        ("Bind key, nonce and tag", [
            "The fixture generates a process-local AES key and a fresh 12-byte nonce, encrypts a dispatch note, then changes the final transmitted byte. The valid record decrypts; the changed record fails tag verification. Do not release plaintext from a failed decryption to callers.",
            "A nonce must not be reused with the same key. A production record format must store the nonce beside the ciphertext and tag, define a key identifier, and enforce a key rotation policy. This small program tests the API boundary, not the storage design."
        ]),
        ("Authenticate context too", [
            "If a ciphertext belongs to one tenant or record ID, include that context as associated data before encryption and decryption. [[java/aes-gcm-associated-data|Associated data]] shows the mismatch failure. The encrypted payload remains subject to input-size limits."
        ]),
    ],
    '''import java.nio.charset.StandardCharsets;
import java.security.SecureRandom;
import java.util.Arrays;
import javax.crypto.AEADBadTagException;
import javax.crypto.Cipher;
import javax.crypto.KeyGenerator;
import javax.crypto.SecretKey;
import javax.crypto.spec.GCMParameterSpec;

public class DispatchNoteSeal {
    public static void main(String[] args) throws Exception {
        KeyGenerator keys = KeyGenerator.getInstance("AES");
        keys.init(128);
        SecretKey key = keys.generateKey();
        byte[] nonce = new byte[12];
        new SecureRandom().nextBytes(nonce);
        GCMParameterSpec parameters = new GCMParameterSpec(128, nonce);
        Cipher encrypt = Cipher.getInstance("AES/GCM/NoPadding");
        encrypt.init(Cipher.ENCRYPT_MODE, key, parameters);
        byte[] sealed = encrypt.doFinal("dispatch=R-47".getBytes(StandardCharsets.UTF_8));
        Cipher decrypt = Cipher.getInstance("AES/GCM/NoPadding");
        decrypt.init(Cipher.DECRYPT_MODE, key, parameters);
        System.out.println("roundtrip=" + "dispatch=R-47".equals(new String(decrypt.doFinal(sealed), StandardCharsets.UTF_8)));
        byte[] changed = Arrays.copyOf(sealed, sealed.length);
        changed[changed.length - 1] ^= 1;
        decrypt.init(Cipher.DECRYPT_MODE, key, parameters);
        try { decrypt.doFinal(changed); }
        catch (AEADBadTagException rejected) { System.out.println("tamper rejected"); }
    }
}''',
    "roundtrip=true\ntamper rejected",
    "Encryption and decryption process O(n) plaintext or ciphertext bytes and allocate result arrays, including the authentication tag. This example's fresh random nonce is local to one operation; high-volume production systems also need a durable nonce-uniqueness strategy under one key.",
    ["Do not reuse a GCM nonce with the same key.", "Do not ignore AEADBadTagException or return unauthenticated plaintext.", "Do not treat an ephemeral generated key as a recoverable stored key."],
    ["java/aes-gcm-associated-data", "java/secure-random-token-encoding", "java/hmac-sha256-verify", "java/byte-streams"],
)


add(
    "aes-gcm-associated-data",
    "Java AES-GCM associated data: bind ciphertext to its record context",
    "AES-GCM associated data is authenticated with the ciphertext but is not encrypted into it.",
    [
        ("Tie the payload to its owner", [
            "A sealed payment note should not be movable from one account context to another without detection. Feed a canonical account identifier through updateAAD before doFinal on both sides. Decryption with a different identifier fails tag verification even when the key, nonce and ciphertext are unchanged.",
            "The fixture checks one matching and one mismatched context. It does not serialize the context or key version; a production record must define and persist enough metadata to reproduce the exact AAD bytes after restart."
        ]),
        ("Order API calls correctly", [
            "Call updateAAD before processing plaintext or ciphertext for a GCM operation. Apply identical byte encoding and field framing at both ends. [[java/hmac-field-framing|HMAC field framing]] shows why ambiguous concatenation can undermine a context definition."
        ]),
    ],
    '''import java.nio.charset.StandardCharsets;
import java.security.SecureRandom;
import javax.crypto.AEADBadTagException;
import javax.crypto.Cipher;
import javax.crypto.KeyGenerator;
import javax.crypto.SecretKey;
import javax.crypto.spec.GCMParameterSpec;

public class AccountNoteContext {
    static byte[] open(SecretKey key, byte[] nonce, byte[] sealed, String account) throws Exception {
        Cipher decrypt = Cipher.getInstance("AES/GCM/NoPadding");
        decrypt.init(Cipher.DECRYPT_MODE, key, new GCMParameterSpec(128, nonce));
        decrypt.updateAAD(account.getBytes(StandardCharsets.UTF_8));
        return decrypt.doFinal(sealed);
    }

    public static void main(String[] args) throws Exception {
        KeyGenerator keys = KeyGenerator.getInstance("AES");
        keys.init(128);
        SecretKey key = keys.generateKey();
        byte[] nonce = new byte[12];
        new SecureRandom().nextBytes(nonce);
        Cipher encrypt = Cipher.getInstance("AES/GCM/NoPadding");
        encrypt.init(Cipher.ENCRYPT_MODE, key, new GCMParameterSpec(128, nonce));
        encrypt.updateAAD("account-47".getBytes(StandardCharsets.UTF_8));
        byte[] sealed = encrypt.doFinal("approved".getBytes(StandardCharsets.UTF_8));
        System.out.println("accepted=" + "approved".equals(new String(open(key, nonce, sealed, "account-47"), StandardCharsets.UTF_8)));
        try { open(key, nonce, sealed, "account-48"); }
        catch (AEADBadTagException rejected) { System.out.println("wrong context rejected"); }
    }
}''',
    "accepted=true\nwrong context rejected",
    "Authentication work grows with ciphertext and associated-data length. The AAD is not secret; it needs canonical bytes and a stable storage format. A new encryption operation needs a new nonce under the same key even when the plaintext or account changes.",
    ["Do not confuse authenticated associated data with encrypted data.", "Do not change AAD encoding between encryption and decryption.", "Do not reuse a GCM nonce under one key for a different account."],
    ["java/aes-gcm-authenticated-decryption", "java/hmac-field-framing", "java/unicode-encoding", "java/secure-random-token-encoding"],
)


add(
    "base64-url-vs-basic",
    "Java Base64 URL encoding: choose the alphabet at the transport boundary",
    "Base64's basic and URL-safe encoders carry the same bytes with different punctuation; neither format protects the bytes from readers.",
    [
        ("Match the receiving protocol", [
            "A short binary marker demonstrates the difference without printing a credential. The basic alphabet uses plus and slash, while the URL alphabet substitutes hyphen and underscore. Removing padding changes text length, not the decoded bytes.",
            "A receiver must use the matching decoder and reject malformed input rather than silently trying several formats. [[java/secure-random-token-encoding|Random token encoding]] uses the URL-safe form because bearer tokens often travel through URL-compatible fields."
        ]),
        ("Do not give encoding a security role", [
            "Anyone holding a Base64 value can decode it. Encrypt sensitive content with an authenticated scheme when confidentiality is required; [[java/aes-gcm-authenticated-decryption|AES-GCM]] covers that separate operation. Put limits on encoded length before decoding untrusted fields."
        ]),
    ],
    '''import java.util.Arrays;
import java.util.Base64;

public class BinaryMarkerAlphabets {
    public static void main(String[] args) {
        byte[] marker = { (byte) 0xfb, (byte) 0xff };
        String basic = Base64.getEncoder().encodeToString(marker);
        String url = Base64.getUrlEncoder().withoutPadding().encodeToString(marker);
        System.out.println("basic=" + basic);
        System.out.println("url=" + url);
        System.out.println("same=" + Arrays.equals(marker, Base64.getUrlDecoder().decode(url)));
    }
}''',
    "basic=+/8=\nurl=-_8\nsame=true",
    "Encoding and decoding process O(n) bytes and allocate output proportional to input length. A transport-safe alphabet is a formatting decision; it does not add secrecy, integrity or source authentication.",
    ["Do not treat Base64 as encryption.", "Do not feed URL-alphabet input to a basic decoder without a protocol rule.", "Do not decode unbounded input into memory."],
    ["java/secure-random-token-encoding", "java/aes-gcm-authenticated-decryption", "java/byte-streams", "java/sha256-explicit-utf8"],
)


for path in added:
    entry = lookup[path]
    entry["data"]["related"] = [{"path": target, "title": lookup[target]["title"]} for target in entry.pop("_related_paths")]

hub = lookup["java/java"]
title = "Cryptographic API boundaries"
hub["data"]["modules"] = [module for module in hub["data"]["modules"] if module["title"] != title]
hub["data"]["modules"].append({
    "title": title,
    "summary": "Make byte encoding, message authentication, token generation and encrypted-record context explicit.",
    "lessons": added,
})
hub["updated_at"] = stamp

reverse = {
    "java/secure-random-tokens": ["java/secure-random-token-encoding", "java/aes-gcm-authenticated-decryption"],
    "java/unicode-encoding": ["java/sha256-explicit-utf8", "java/aes-gcm-associated-data"],
    "java/byte-streams": ["java/message-digest-bytebuffer", "java/aes-gcm-authenticated-decryption"],
    "java/bytebuffer-order": ["java/message-digest-bytebuffer", "java/hmac-field-framing"],
    "java/tls-local-project": ["java/hmac-sha256-verify", "java/aes-gcm-authenticated-decryption"],
}
for path, targets in reverse.items():
    entry = lookup[path]
    marker = "<h2>Cryptographic API boundaries</h2>"
    entry["body"] = entry["body"].split(marker)[0] + marker + paragraph(
        "Continue with " + ", ".join("[[" + target + "|" + lookup[target]["title"] + "]]" for target in targets) + "."
    )
    entry["updated_at"] = stamp

FILE.write_text(json.dumps(entries, ensure_ascii=False, indent=2) + "\n")
print("Added", len(added), "Java lessons; linked from", len(reverse), "existing lessons")
