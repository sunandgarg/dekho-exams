"""Add checked wire-input and local I/O lessons to the Python curriculum."""

import copy
import datetime
import html
import json
import uuid
from pathlib import Path


root = Path(__file__).resolve().parents[1]
fixture = root / "src/data/fixtures.json"
rows = json.loads(fixture.read_text())
by_path = {row["path"]: row for row in rows}
stamp = datetime.datetime.now(datetime.UTC).isoformat()

lessons = [
    dict(
        slug="pickle-trust-boundary",
        title="Python pickle: preserve trusted aliases without decoding received objects",
        summary="pickle restores Python object graphs, including aliases, and must stay behind a trusted-data boundary.",
        contract="An owned in-process state graph gives two receipt keys the same list. Its trusted pickle round trip retains that alias. A separate received-record function accepts a bounded UTF-8 JSON object with a declared schema. When given pickle bytes, that function rejects them without calling pickle.loads.",
        boundary="A byte length limit does not make an untrusted pickle safe. Deserialization can invoke arbitrary object reconstruction hooks before an application can validate the returned value. JSON also needs input budgets and a schema; this small fixture checks only one bounded record and does not implement a general API parser.",
        source='''import json
import pickle

shared_events = ["paid"]
trusted_cache = {"R-47": shared_events, "R-73": shared_events}
restored_cache = pickle.loads(pickle.dumps(trusted_cache, protocol=4))
print("alias_preserved", restored_cache["R-47"] is restored_cache["R-73"])

def parse_received_receipt(payload):
    if len(payload) > 96:
        raise ValueError("record too large")
    record = json.loads(payload.decode("utf-8"))
    if (type(record) is not dict or set(record) != {"receipt", "amount"}
            or type(record["receipt"]) is not str
            or type(record["amount"]) is not int):
        raise ValueError("wrong record shape")
    return record["receipt"], record["amount"]

print("received", parse_received_receipt(b'{"receipt":"R-47","amount":73}'))
try:
    parse_received_receipt(pickle.dumps(trusted_cache, protocol=4))
except (UnicodeError, ValueError, json.JSONDecodeError):
    print("pickle_input_rejected", True)''',
        expected="alias_preserved True\nreceived ('R-47', 73)\npickle_input_rejected True",
        cost="Serialization visits the reachable object graph and allocates output bytes; restoring it allocates a new graph. The alias test is an ownership fact, not a reason to accept pickle over a network.",
        mistakes=["Never call pickle.loads on received or tamperable bytes.", "A post-load type check cannot undo code already run during deserialization.", "JSON parsing still requires a byte budget and application field checks."],
        related=["python/json-validation", "python/hmac-envelope", "python/strict-utf8-import"],
    ),
    dict(
        slug="query-field-duplicates",
        title="Python query strings: retain blank fields and reject repeated keys",
        summary="Parsing a query into pairs preserves duplicate names long enough to reject them.",
        contract="An owned pair list encodes a slash in the receipt identifier before transmission. The decoder retains blank values, requires exactly one receipt and one amount, and rejects repeated fields. It also caps the field count before building an application mapping.",
        boundary="parse_qsl is a field parser, not a complete request validator. Percent escapes, Unicode normalization, numeric ranges, and authorization need separate rules. A query field limit does not cap the total request-line bytes; impose a byte limit at the receiving layer too.",
        source='''from urllib.parse import parse_qsl, urlencode

def parse_receipt_query(query):
    pairs = parse_qsl(query, keep_blank_values=True, strict_parsing=True,
                      errors="strict", max_num_fields=2)
    if len(pairs) != 2 or {name for name, _ in pairs} != {"receipt", "amount"}:
        raise ValueError("wrong or repeated fields")
    fields = dict(pairs)
    if not fields["receipt"] or not fields["amount"].isascii() or not fields["amount"].isdecimal():
        raise ValueError("invalid field")
    return fields["receipt"], int(fields["amount"])

wire_query = urlencode([("receipt", "R/47"), ("amount", "73")])
print("wire", wire_query)
print("parsed", parse_receipt_query(wire_query))
for rejected_query in ("receipt=R-47&receipt=R-73", "receipt=&amount=73",
                       "receipt=R-47&amount=73&mode=paid"):
    try:
        parse_receipt_query(rejected_query)
    except ValueError:
        print("rejected", rejected_query.split("&")[0])''',
        expected="wire receipt=R%2F47&amount=73\nparsed ('R/47', 73)\nrejected receipt=R-47\nrejected receipt=\nrejected receipt=R-47",
        cost="Parsing scans the query and allocates decoded field strings. The two-field ceiling bounds field count only; the caller must also cap query bytes before parsing.",
        mistakes=["Converting to a dict first silently discards the fact that a key repeated.", "The default parser may discard blank values unless asked to retain them.", "Field count is not a request-byte budget."],
        related=["python/url-target-policy", "python/flask-routing", "python/json-duplicate-keys"],
    ),
    dict(
        slug="email-header-assembly",
        title="Python EmailMessage: keep received newlines out of a header field",
        summary="A message header is a field value, not a place to concatenate received mail syntax.",
        contract="The fixture tries to assign a received subject containing a newline and a second header name. EmailMessage rejects that assignment. It then sets a plain owned subject and body and serializes the message locally; nothing is sent.",
        boundary="Header validation is one part of mail handling. Addresses, recipients, attachment types, message size, SMTP transport, and delivery rules need separate policies. The body of a message is not made trusted merely because its subject was accepted.",
        source='''from email import policy
from email.message import EmailMessage

message = EmailMessage(policy=policy.SMTP)
try:
    message["Subject"] = "Receipt R-47 paid\\nBcc: hidden"
except ValueError:
    print("newline_rejected", True)
message["Subject"] = "Receipt R-47 paid"
message.set_content("Receipt R-47 was recorded.")
serialized = message.as_bytes()
print("one_subject", serialized.count(b"Subject:") == 1)
print("body_present", b"Receipt R-47 was recorded." in serialized)''',
        expected="newline_rejected True\none_subject True\nbody_present True",
        cost="Serialization allocates bytes proportional to the message body. This fixture keeps one short local message and makes no mail-delivery or attachment-budget claim.",
        mistakes=["Do not concatenate a received value into raw header lines.", "A valid subject does not validate a recipient or body.", "Building bytes locally is not evidence that a message was delivered."],
        related=["python/log-redaction", "python/strings-bytes", "python/bounded-json-lines"],
    ),
    dict(
        slug="email-duplicate-headers",
        title="Python email parsing: inspect all sender headers before trusting one",
        summary="A parsed message may retain repeated sender headers; single-value access hides that multiplicity.",
        contract="A controlled byte message has two From fields. BytesParser retains both, and the application rejects it when the count differs from one. A separate single-sender message passes the same count check. Parsing is explicit about its policy.",
        boundary="The fixture does not authenticate a sender, verify a signature, or decide mail delivery. A unique From field is only one structural rule. Full mail ingestion also needs byte limits, defect handling, MIME part budgets, and an identity policy independent of header text.",
        source='''from email import policy
from email.parser import BytesParser

parser = BytesParser(policy=policy.default)
repeated = parser.parsebytes(
    b"From: receipts@aitrove.in\\r\\nFrom: audit@aitrove.in\\r\\n"
    b"Subject: R-47\\r\\n\\r\\npaid\\r\\n"
)
single = parser.parsebytes(
    b"From: receipts@aitrove.in\\r\\nSubject: R-73\\r\\n\\r\\npaid\\r\\n"
)
print("repeated_count", len(repeated.get_all("From", [])))
print("repeated_rejected", len(repeated.get_all("From", [])) != 1)
print("single_accepted", len(single.get_all("From", [])) == 1)''',
        expected="repeated_count 2\nrepeated_rejected True\nsingle_accepted True",
        cost="Parsing a complete message retains its body and header structure in memory. A production reader needs a byte budget before parsebytes and a part policy afterward.",
        mistakes=["message['From'] may conceal a repeated field; use get_all for a uniqueness rule.", "A syntactically valid address is not authenticated identity.", "Do not assume parsing alone rejects every malformed MIME tree."],
        related=["python/email-header-assembly", "python/json-duplicate-keys", "python/csv-duplicate-headers"],
    ),
    dict(
        slug="configparser-literal-percent",
        title="Python ConfigParser: read literal percent signs without hidden interpolation",
        summary="ConfigParser interpolation and case folding can change how a stored option is read.",
        contract="A controlled export configuration contains a literal percent sign. With interpolation disabled, the application reads those bytes as text. A second configuration repeats the same option with different letter case; strict parsing rejects that duplicate before it can replace the first value.",
        boundary="Disabling interpolation does not validate business values, protect secrets, or decide which configuration file is trusted. ConfigParser stores string values; parse and range-check each field before publishing settings to workers.",
        source='''import configparser

settings = configparser.ConfigParser(interpolation=None, strict=True)
settings.read_string("[export]\\npattern = paid%complete\\nretention_days = 47\\n")
print("pattern", settings["export"]["pattern"])
print("retention", settings.getint("export", "retention_days"))

duplicate = configparser.ConfigParser(interpolation=None, strict=True)
try:
    duplicate.read_string("[export]\\nRetention = 47\\nretention = 73\\n")
except configparser.DuplicateOptionError:
    print("case_duplicate_rejected", True)''',
        expected="pattern paid%complete\nretention 47\ncase_duplicate_rejected True",
        cost="Configuration parsing allocates values proportional to the source text. The input file still needs an ownership and size policy before parsing.",
        mistakes=["Default interpolation treats percent syntax as special.", "Option names are case-insensitive by default, which affects duplicate detection.", "getint converts text but does not enforce a domain range."],
        related=["python/toml-configuration", "python/configuration-precedence", "python/assert-validation"],
    ),
    dict(
        slug="socketpair-exact-recv",
        title="Python socket recv: assemble an exact frame across local socket reads",
        summary="A socket read can return fewer bytes than requested; a framed receiver must loop until complete or EOF.",
        contract="Two owned sockets exchange one complete seven-byte receipt frame, followed by a second frame whose body stops after three of seven bytes. The receiving loop collects exact lengths and rejects the truncated second frame when the sender closes its write side. No port or external host is used.",
        boundary="socketpair checks one local stream on the tested host. A live network peer may stall without closing, so a receiver needs a deadline and an overall byte budget. This fixture does not prove TLS authentication, remote ordering, or operation under every socket platform.",
        source='''import socket

def receive_exact(connection, byte_count):
    chunks = []
    remaining = byte_count
    while remaining:
        chunk = connection.recv(remaining)
        if not chunk:
            raise EOFError("receipt frame ended early")
        chunks.append(chunk)
        remaining -= len(chunk)
    return b"".join(chunks)

def receive_frame(connection, maximum_body):
    body_size = int.from_bytes(receive_exact(connection, 2), "big")
    if body_size > maximum_body:
        raise ValueError("receipt body too large")
    return receive_exact(connection, body_size)

sender, receiver = socket.socketpair()
try:
    receiver.settimeout(1)
    sender.sendall((7).to_bytes(2, "big") + b"R47paid"
                   + (7).to_bytes(2, "big") + b"R73")
    sender.shutdown(socket.SHUT_WR)
    print("first", receive_frame(receiver, 8).decode("ascii"))
    try:
        receive_frame(receiver, 8)
    except EOFError:
        print("short_second_rejected", True)
finally:
    sender.close()
    receiver.close()''',
        expected="first R47paid\nshort_second_rejected True",
        cost="The loop copies each chunk into a list and joins at completion, using memory proportional to the bounded body. For large frames, stream into an owned sink under a separate total-byte policy.",
        mistakes=["One recv call is not an exact-length contract.", "EOF before the declared body ends is a rejected frame.", "A socket timeout is not a total request deadline across many reads."],
        related=["python/async-length-prefixed-frame", "python/socket-frame-reading", "python/tls-client-context-policy"],
    ),
    dict(
        slug="textio-newline-contract",
        title="Python TextIOWrapper: choose whether input line endings are normalized",
        summary="TextIOWrapper can translate received line endings or leave them visible to the parser.",
        contract="Two independent wrappers decode the same owned UTF-8 bytes. The universal-newline reader converts CRLF and LF to LF. The second reader keeps the original endings, so a byte-sensitive parser can distinguish them. Both wrappers close their owned buffers.",
        boundary="Neither mode changes the original bytes in the source buffer. For signed or hashed wire data, authenticate bytes before text translation. A real file reader should also declare encoding, error policy, and a byte limit; the in-memory fixture omits those outer constraints.",
        source='''import io

wire_bytes = b"R-47\\r\\nR-73\\n"
with io.TextIOWrapper(io.BytesIO(wire_bytes), encoding="utf-8", newline=None) as normalized:
    print("normalized", repr(normalized.read()))
with io.TextIOWrapper(io.BytesIO(wire_bytes), encoding="utf-8", newline="") as preserved:
    print("preserved", repr(preserved.read()))''',
        expected="normalized 'R-47\\nR-73\\n'\npreserved 'R-47\\r\\nR-73\\n'",
        cost="Decoding scans the input and allocates a text representation. The two independent wrappers in this fixture each hold a short source; do not duplicate large buffers merely to compare modes in production.",
        mistakes=["Universal-newline mode changes the text returned by read.", "Text normalization must not precede verification of exact signed bytes.", "Closing a TextIOWrapper also closes its underlying buffer unless ownership is transferred deliberately."],
        related=["python/strings-bytes", "python/hashlib-streaming-integrity", "python/csv-import"],
    ),
    dict(
        slug="nofollow-owned-directory",
        title="Python POSIX dir_fd and O_NOFOLLOW: reject a final symlink on an owned open",
        summary="A directory descriptor and O_NOFOLLOW let a POSIX open reject a symlink in its final path component.",
        contract="An owned temporary directory contains one receipt file and a symlink pointing at it. The fixture opens the real file relative to an already-open directory descriptor, reads its exact bytes, and sees an error when it tries to open the symlink with O_NOFOLLOW.",
        boundary="This is a checked POSIX fixture; Windows requires another implementation. O_NOFOLLOW guards the final component only, and a directory descriptor does not by itself make every later operation race-free. Do not use string-prefix path checks as a substitute for descriptor-based ownership and a clear symlink policy.",
        source='''import errno
import os
from pathlib import Path
from tempfile import TemporaryDirectory

with TemporaryDirectory() as directory:
    receipt_path = Path(directory) / "receipt-47.txt"
    receipt_path.write_bytes(b"paid:47")
    (Path(directory) / "current.txt").symlink_to(receipt_path.name)
    directory_fd = os.open(directory, os.O_RDONLY | os.O_DIRECTORY)
    try:
        receipt_fd = os.open("receipt-47.txt", os.O_RDONLY | os.O_NOFOLLOW,
                             dir_fd=directory_fd)
        try:
            print("receipt", os.read(receipt_fd, 7))
        finally:
            os.close(receipt_fd)
        try:
            link_fd = os.open("current.txt", os.O_RDONLY | os.O_NOFOLLOW,
                              dir_fd=directory_fd)
        except OSError as failure:
            print("link_rejected", failure.errno in (errno.ELOOP, errno.EMLINK))
        else:
            os.close(link_fd)
            raise AssertionError("symlink unexpectedly opened")
    finally:
        os.close(directory_fd)''',
        expected="receipt b'paid:47'\nlink_rejected True",
        cost="Descriptor-based opens cost system calls and require explicit close ownership. They avoid trusting an earlier resolved path name, but the full threat model still determines which components and operations need protection.",
        mistakes=["O_NOFOLLOW covers the final component, not every ancestor in a path.", "A prior path check can become stale before a later open.", "Close both the opened file and directory descriptors on every path."],
        related=["python/scandir-stale-metadata", "python/pathlib-files", "python/atomic-file-replacement"],
    ),
]

new_paths = ["python/" + item["slug"] for item in lessons]
assert not any(path in by_path for path in new_paths)
titles = {row["path"]: row["title"] for row in rows}
titles.update({path: item["title"] for path, item in zip(new_paths, lessons)})
for order, (item, path) in enumerate(zip(lessons, new_paths)):
    assert all(target in titles for target in item["related"]), path
    body = "<p>" + html.escape(item["summary"]) + "</p>"
    body += "<h2>Operation contract</h2><p>" + html.escape(item["contract"]) + "</p>"
    body += "<h2>Failure boundary</h2><p>" + html.escape(item["boundary"]) + "</p>"
    body += '<h2>Working program</h2><pre><code class="language-python">' + html.escape(item["source"], quote=False) + "</code></pre>"
    body += '<h3>Output</h3><pre><code class="language-text">' + html.escape(item["expected"], quote=False) + "</code></pre>"
    body += "<h2>Costs and limits</h2><p>" + html.escape(item["cost"]) + "</p>"
    body += "<h3>Common Mistakes</h3><ul>" + "".join("<li>" + html.escape(mistake) + "</li>" for mistake in item["mistakes"]) + "</ul>"
    body += "<h2>Connected lessons</h2><ul>" + "".join(
        '<li><a href="/' + target + '">' + html.escape(titles[target]) + "</a></li>"
        for target in item["related"]) + "</ul>"
    row = copy.deepcopy(by_path["python/json-validation"])
    row.update(id=str(uuid.uuid5(uuid.NAMESPACE_URL, "https://aitrove.in/" + path)),
               path=path, title=item["title"], summary=item["summary"], body=body,
               subject="python-examples", tags=["python", item["slug"]],
               sort_order=8800 + order, published_at=stamp, created_at=stamp, updated_at=stamp)
    row["data"] = {"subject_root": "python/python-programming-language-tutorial",
                   "section_path": "python/examples", "content_format": "html", "kind": "tutorial",
                   "python_version": "3.11+ syntax; verified on local CPython",
                   "python_minimum": "3.11", "reading_minutes": 5,
                   "author_path": "authors/aitrove-editorial",
                   "download_path": "/downloads/aitrove-python-source-kit.zip",
                   "related": [{"path": target, "title": titles[target]} for target in item["related"]],
                   "seo_ready": True, "expected_output": item["expected"]}
    rows.append(row)
    by_path[path] = row

examples = by_path["python/examples"]
examples["data"]["modules"].append({"title": "Received data and owned local I/O",
                                    "summary": "Test parser shape, byte ownership and rejection paths.",
                                    "lessons": new_paths})
examples["body"] += "<h2>Received data and owned local I/O</h2><ul>" + "".join(
    '<li><a href="/' + path + '">' + html.escape(titles[path]) + "</a></li>"
    for path in new_paths) + "</ul>"
examples["updated_at"] = stamp
parent = by_path["python/python-programming-language-tutorial"]
parent["body"] += "<h2>Received data and owned local I/O</h2><ul>" + "".join(
    '<li><a href="/' + path + '">' + html.escape(titles[path]) + "</a></li>"
    for path in new_paths) + "</ul>"
parent["updated_at"] = stamp

for source, target in [
    ("python/json-validation", "python/pickle-trust-boundary"),
    ("python/url-target-policy", "python/query-field-duplicates"),
    ("python/log-redaction", "python/email-header-assembly"),
    ("python/csv-duplicate-headers", "python/email-duplicate-headers"),
    ("python/configuration-precedence", "python/configparser-literal-percent"),
    ("python/socket-frame-reading", "python/socketpair-exact-recv"),
    ("python/strict-utf8-import", "python/textio-newline-contract"),
    ("python/scandir-stale-metadata", "python/nofollow-owned-directory"),
]:
    row = by_path[source]
    row["body"] += '<p><a href="/' + target + '">Continue with ' + html.escape(titles[target]) + "</a>.</p>"
    row["updated_at"] = stamp

quiz_path = "quizzes/python-wire-input-ownership"
assert quiz_path not in by_path
quiz = copy.deepcopy(by_path["quizzes/python-boundary-contracts"])
quiz_body = "<p>Check serialization trust, repeated fields, mail headers, local streams and file descriptors.</p><h2>Review the related lessons</h2><ul>"
quiz_body += "".join('<li><a href="/' + path + '">' + html.escape(titles[path]) + "</a></li>" for path in new_paths)
quiz_body += "</ul><h3>Common Mistakes</h3><p>Passing a local parser fixture does not establish a network or filesystem security boundary.</p>"
quiz.update(id=str(uuid.uuid5(uuid.NAMESPACE_URL, "https://aitrove.in/" + quiz_path)),
            path=quiz_path, title="Python received-input and ownership quiz",
            summary="Twelve explained questions on received data, headers, stream reads and descriptor ownership.",
            body=quiz_body, sort_order=8900, published_at=stamp, created_at=stamp, updated_at=stamp)
raw_questions = [
    ("When may an application call pickle.loads?", "Only on data it already trusts", "Before validating any received bytes", "Whenever a size limit is set", "Object reconstruction may run code before a post-load check."),
    ("What can a trusted pickle round trip preserve?", "Shared aliases within an object graph", "Authentication of a remote sender", "A network byte budget", "Two keys can still point to the same restored list."),
    ("Why parse a query into pairs before making a dict?", "To detect repeated names", "To bypass percent decoding", "To disable all blank fields", "A dict replacement would hide key multiplicity."),
    ("Does max_num_fields cap the bytes in an entire request?", "No", "Yes", "Only when fields are ASCII", "The receiving layer needs a separate byte ceiling."),
    ("What happens when a newline is assigned to a protected message header?", "The assignment is rejected", "It is sent as a second header", "The body becomes encrypted", "Header assembly rejects line breaks in the field value."),
    ("Which method exposes repeated parsed From fields?", "get_all", "get_content", "as_bytes", "Single-value access may hide repeated header values."),
    ("What does interpolation=None do for a percent sign in ConfigParser?", "Preserves it as literal text", "Treats it as a secret", "Deletes the option", "The parser no longer interprets percent syntax in values."),
    ("Can one socket recv call be assumed to fill a frame?", "No", "Yes for a local pair", "Only when the sender used sendall", "A stream receiver must loop to a declared length or reject EOF."),
    ("What should a framed receiver do on EOF before the declared body ends?", "Reject the frame", "Accept the bytes as a shorter frame", "Wait forever", "The received prefix does not satisfy the declared record length."),
    ("Which newline mode preserves CRLF in decoded text?", "An empty newline argument", "newline=None", "Any mode after read", "Universal-newline translation can be enabled without translating endings by using an empty argument."),
    ("What does O_NOFOLLOW guard in the shown POSIX open?", "The final path component", "Every ancestor path component", "All future renames", "The flag rejects opening a final symlink, not an entire arbitrary path tree."),
    ("Which descriptors must be closed in the owned directory fixture?", "Both directory and receipt descriptors", "Only the receipt descriptor", "Neither when bytes are read", "Each successful os.open creates a descriptor with a close owner."),
]
quiz["data"]["questions"] = []
for index, (prompt, correct, wrong_a, wrong_b, explanation) in enumerate(raw_questions):
    options = [correct, wrong_a, wrong_b]
    options = options[index % 3:] + options[:index % 3]
    quiz["data"]["questions"].append({"prompt": prompt, "options": options,
                                      "answer": options.index(correct), "explanation": explanation})
rows.append(quiz)
by_path[quiz_path] = quiz
quiz_hub = by_path["python/quizzes"]
quiz_hub["data"]["modules"][-1]["lessons"].append(quiz_path)
needle = "</ul><h2>Continue learning</h2>"
assert needle in quiz_hub["body"]
quiz_hub["body"] = quiz_hub["body"].replace(needle,
    '<li><a href="/' + quiz_path + '">' + html.escape(quiz["title"]) + "</a></li>" + needle)
parent["body"] += '<p><a href="/' + quiz_path + '">Check the received-input quiz</a>.</p>'
for path in new_paths:
    by_path[path]["body"] += '<p><a href="/' + quiz_path + '">Test this contract</a>.</p>'

fixture.write_text(json.dumps(rows, ensure_ascii=False, indent=2) + "\n")
print("Added", len(lessons), "lessons and one quiz")
