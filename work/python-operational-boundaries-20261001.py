"""Add executable Python operational-boundary lessons and one quiz."""

import copy
import datetime
import html
import json
import pathlib
import uuid

root = pathlib.Path(__file__).resolve().parents[1]
fixture = root / "src/data/fixtures.json"
rows = json.loads(fixture.read_text())
by_path = {row["path"]: row for row in rows}
stamp = datetime.datetime.now(datetime.UTC).isoformat()

lessons = [
    dict(slug="subprocess-timeout-reap", section="python/advanced-python", subject="python-advanced",
         title="Python subprocess timeout: kill and reap the timed-out child",
         summary="A Popen timeout raises without stopping the child; the owner must terminate and collect it.",
         contract="A receipt import starts a separate interpreter. communicate(timeout=...) limits this one wait, and TimeoutExpired leaves the process alive. The exception path kills it, then calls communicate again to close the pipes and collect its return status. A subprocess that launches its own descendants needs a separately designed process-group policy; killing one PID does not imply a whole tree stopped.",
         boundary="The fixture uses a sleeping child so the timeout is reproducible. A launch failure occurs before Popen returns and belongs to a different error path. communicate buffers pipe output in memory: use an output budget or a file for untrusted volume. An OS process supervisor may also need to own shutdown when the parent dies.",
         source='''import subprocess
import sys

child = subprocess.Popen(
    [sys.executable, "-c", "import time; time.sleep(1)"],
    stdout=subprocess.PIPE,
    stderr=subprocess.PIPE,
)
try:
    child.communicate(timeout=0.02)
    timed_out = False
except subprocess.TimeoutExpired:
    timed_out = True
    child.kill()
    child.communicate()
print("timed_out", timed_out)
print("reaped", child.returncode is not None)''', expected="timed_out True\nreaped True",
         cost="Process creation and shutdown dominate this tiny fixture. The wait is bounded, but the second communicate can still retain output; set output limits for an untrusted child.",
         mistakes=["A timeout exception does not kill the process.", "Calling wait with unread pipes can deadlock when the child fills them.", "Killing the direct child is not a process-tree policy."],
         related=["python/subprocess-boundaries", "python/subprocess-output-spool", "python/async-deadlines"]),
    dict(slug="subprocess-output-spool", section="python/projects", subject="python-projects",
         title="Python subprocess output: spool bytes before accepting a report",
         summary="A completed child can emit more data than a report contract permits, even when its exit status is zero.",
         contract="A formatter writes to a temporary file, so the parent does not collect the entire stdout in a Python string. After the child exits, the owner measures bytes and rejects the oversized result before parsing it. The output limit is an acceptance boundary here, not a hard production disk quota. Pair a real untrusted command with an OS or streaming limit that stops growth while it runs.",
         boundary="The child is a fixed local interpreter command. Never splice a requester-supplied shell string into it. A redirect to a file avoids an in-memory pipe buffer but consumes storage; reserve a spool directory with quotas and cleanup. stderr needs its own policy. A zero exit code only reports process success, not report validity.",
         source='''import subprocess
import sys
import tempfile

with tempfile.TemporaryFile() as report_output:
    completed = subprocess.run(
        [sys.executable, "-c", "import sys; sys.stdout.write('R' * 47000)"],
        stdout=report_output,
        stderr=subprocess.DEVNULL,
        check=True,
        timeout=5,
    )
    report_output.seek(0, 2)
    byte_count = report_output.tell()
    print("exit", completed.returncode)
    print("bytes", byte_count)
    print("accepted", byte_count <= 4096)''', expected="exit 0\nbytes 47000\naccepted False",
         cost="Spooling uses O(output bytes) temporary storage and O(1) application memory for the size check. The shown check occurs after completion; a live hard limit requires bounded streaming or platform quotas.",
         mistakes=["Redirecting stdout does not enforce a disk budget.", "Do not treat returncode zero as proof that the output meets a schema.", "Discarded stderr hides diagnostics; use a bounded separate diagnostic path in a service."],
         related=["python/subprocess-boundaries", "python/subprocess-timeout-reap", "python/gzip-output-budget"]),
    dict(slug="tls-client-context-policy", section="python/web-applications", subject="python-web",
         title="Python TLS client context: require certificate and hostname checks",
         summary="A client SSLContext can require certificate validation and hostname matching before any socket is opened.",
         contract="The client builds its TLS policy once and passes the context to a connection path that supplies the intended server hostname. create_default_context loads a trust policy and enables certificate checks. This local program inspects those settings; it does not perform a handshake, prove a remote certificate valid, or decide whether an arbitrary URL is an allowed destination.",
         boundary="Never turn check_hostname off to make an internal service work. Supply the expected DNS name, maintain a deliberate trust store, and test a real endpoint with both accepted and rejected certificates. TLS identity does not replace application authorization or a target allowlist. Trust-store contents and protocol defaults can change with the runtime and system.",
         source='''import ssl

client_context = ssl.create_default_context(ssl.Purpose.SERVER_AUTH)
print("hostname_check", client_context.check_hostname)
print("certificate_required", client_context.verify_mode == ssl.CERT_REQUIRED)''',
         expected="hostname_check True\ncertificate_required True",
         cost="Context construction reads trust configuration. Reusing a context avoids repeating that setup, but the program makes no network or throughput claim.",
         mistakes=["A configured context is not a verified connection.", "A certificate chain without hostname matching does not identify the requested host.", "TLS verification does not authorize a target URL or request body."],
         related=["python/url-target-policy", "python/ipaddress-network-membership", "python/flask-routing"]),
    dict(slug="sqlite-migration-rollback", section="python/projects", subject="python-projects",
         title="Python SQLite migration: commit schema and version as one unit",
         summary="An explicit transaction can roll back both a failed DDL change and its schema-version update.",
         contract="A receipt database begins at schema version one. The attempted second migration adds a column, then hits a conflicting table definition. Explicit BEGIN and ROLLBACK leave both the column and version unchanged. The code uses execute for each statement rather than executescript, whose pending-transaction behavior can break a caller's assumption about transaction ownership.",
         boundary="This in-memory fixture tests rollback, not a deployment migration. Back up real data, serialize migration runners, validate the current version, and plan what happens when an old application instance sees the new schema. Some schema operations and external effects have different transaction behavior; test the exact SQLite version and operation before a release.",
         source='''import sqlite3

database = sqlite3.connect(":memory:", isolation_level=None)
database.execute("BEGIN IMMEDIATE")
database.execute("CREATE TABLE receipts (receipt_id TEXT PRIMARY KEY)")
database.execute("PRAGMA user_version = 1")
database.execute("COMMIT")

try:
    database.execute("BEGIN IMMEDIATE")
    database.execute("ALTER TABLE receipts ADD COLUMN batch_id TEXT")
    database.execute("CREATE TABLE receipts (duplicate_id TEXT)")
    database.execute("PRAGMA user_version = 2")
    database.execute("COMMIT")
except sqlite3.OperationalError:
    database.execute("ROLLBACK")

version = database.execute("PRAGMA user_version").fetchone()[0]
columns = [row[1] for row in database.execute("PRAGMA table_info(receipts)")]
print("version", version)
print("columns", columns)
database.close()''', expected="version 1\ncolumns ['receipt_id']",
         cost="The migration lock blocks competing writes while held. A large table rewrite can be expensive; measure it with production-like size before scheduling a release.",
         mistakes=["Do not update user_version before verifying the schema change.", "Do not assume executescript preserves a transaction opened by its caller.", "Rollback of an in-memory fixture does not prove a deployment upgrade path."],
         related=["python/sqlite-transactions", "python/sqlite-savepoints", "python/sqlite-backup-project"]),
    dict(slug="json-duplicate-name-rejection", section="python/data-types", subject="python-types",
         title="Python JSON duplicate names: reject ambiguous object fields",
         summary="A JSON object with the same name twice can silently keep one value unless the parser enforces a policy.",
         contract="A signed instruction should not let two parsers disagree about the tenant field. object_pairs_hook receives ordered pairs for each object; the hook rejects a repeated name before producing a dict. This is parser-level validation. It does not authenticate the payload, enforce its complete schema, or reject a different spelling of the same logical identifier after case normalization.",
         boundary="The default decoder accepts duplicate names and keeps a later value. Applying a strict hook to every object is simple but costs a set per object. Set a byte limit before parsing untrusted input. Keep the original bytes for signature verification when the protocol signs bytes; reserializing a parsed dict is not equivalent to those original bytes.",
         source='''import json

def unique_names(pairs):
    result = {}
    for name, value in pairs:
        if name in result:
            raise ValueError("duplicate name: " + name)
        result[name] = value
    return result

payload = '{"tenant":"north-47","tenant":"south-47"}'
try:
    json.loads(payload, object_pairs_hook=unique_names)
except ValueError as error:
    print(str(error))''', expected="duplicate name: tenant",
         cost="The hook visits each key once and retains the decoded object. A duplicate check is O(keys) expected time per object with O(keys) extra membership state.",
         mistakes=["Do not rely on a default decoder to reject duplicate names.", "A parsed object is not the byte sequence that a signature covered.", "Case folding or Unicode normalization may need a separate field-name rule."],
         related=["python/json-validation", "python/json-nonfinite-number-boundary", "python/hmac-envelope"]),
    dict(slug="tar-member-preflight", section="python/advanced-python", subject="python-advanced",
         title="Python tar preflight: reject links and path escapes before extraction",
         summary="Archive member metadata can contain parent traversal or links even when a tar stream parses successfully.",
         contract="A report archive is allowed to contain regular files under a known folder. This program inspects names, rejects parent components and absolute paths, and refuses non-file members. It never extracts. In an actual ingestion path, apply a supported extraction filter, unpack into a fresh directory, and enforce member-count and total-size budgets while writing.",
         boundary="Preflight metadata alone cannot stop a changing archive source or a race in a shared destination. Duplicate member names, case-insensitive collisions, decompression cost, and special files deserve separate checks. An extraction filter is a defense layer, not a complete quota or sandbox. This fixture makes no cross-platform extraction guarantee.",
         source='''import io
import tarfile
from pathlib import PurePosixPath

archive_bytes = io.BytesIO()
with tarfile.open(fileobj=archive_bytes, mode="w") as archive:
    safe = tarfile.TarInfo("reports/quarter-47.txt")
    safe.size = 3
    archive.addfile(safe, io.BytesIO(b"47\\n"))
    escape = tarfile.TarInfo("../outside.txt")
    escape.size = 0
    archive.addfile(escape, io.BytesIO())
    link = tarfile.TarInfo("reports/shortcut")
    link.type = tarfile.SYMTYPE
    link.linkname = "../outside.txt"
    archive.addfile(link)

archive_bytes.seek(0)
accepted = []
rejected = 0
with tarfile.open(fileobj=archive_bytes, mode="r:") as archive:
    for member in archive:
        name = PurePosixPath(member.name)
        if (not member.isfile() or not name.parts or name.is_absolute()
                or ".." in name.parts or name.parts[0] != "reports"):
            rejected += 1
        else:
            accepted.append(member.name)
print("accepted", accepted)
print("rejected", rejected)''', expected="accepted ['reports/quarter-47.txt']\nrejected 2",
         cost="Preflight walks all members and stores only accepted names here. A real extractor must budget the bytes written and clean up a partial directory on failure.",
         mistakes=["A valid tar header does not make a member path safe.", "Rejecting '..' in names does not alone solve link or destination races.", "The data extraction filter does not enforce storage, CPU, or member-count budgets."],
         related=["python/zip-member-validation", "python/gzip-output-budget", "python/pathlib-files"]),
    dict(slug="generated-invariant-cases", section="python/testing", subject="python-testing",
         title="Python generated checks: name the invariant and keep rejected cases",
         summary="A generated input loop is useful only when each case checks a precise invariant and failures remain reproducible.",
         contract="The parser accepts signed decimal integer text and must round-trip every number in a bounded range. The loop checks that invariant for 95 inputs, then tests three invalid forms separately. This is a deterministic regression fixture, not exhaustive proof for every integer string and not a replacement for a property-testing engine that shrinks failures.",
         boundary="Varying inputs without an assertion does not test anything. Random generation needs a recorded seed and a strategy that includes boundaries; a fixed range is easier to reproduce but narrower. Define whether whitespace, plus signs, leading zeroes, Unicode digits, and overflow are valid before broadening the input space.",
         source='''def parse_signed_decimal(raw):
    digits = raw[1:] if raw.startswith("-") else raw
    if not digits or not all("0" <= character <= "9" for character in digits):
        raise ValueError("not signed decimal")
    return int(raw)

checked = 0
for quantity in range(-47, 48):
    assert parse_signed_decimal(str(quantity)) == quantity
    checked += 1

rejected = 0
for raw in ("", "47x", " 47"):
    try:
        parse_signed_decimal(raw)
    except ValueError:
        rejected += 1
print("round_trips", checked)
print("rejected", rejected)''', expected="round_trips 95\nrejected 3",
         cost="The shown loop runs O(n × digits) checks with constant state. A broader generated suite needs a runtime budget and retained failing seeds or examples.",
         mistakes=["Generated values do not prove the invariant outside their domain.", "Keep rejected-input tests separate from success round trips.", "An unrecorded random seed makes an intermittent failure hard to reproduce."],
         related=["python/unittest-subtests", "python/mutation-testing", "python/refactor-contract-tests"]),
    dict(slug="atomic-file-replacement", section="python/projects", subject="python-projects",
         title="Python file replacement: write a sibling file before changing the name",
         summary="A same-directory temporary file can be flushed and replaced without exposing a partially written target through its pathname.",
         contract="A receipt index is written to a sibling temporary file. The writer flushes Python buffers, asks the OS to flush the file, closes it, then uses os.replace on the target path. A reader opening the target before or after replacement sees a whole old or new file on filesystems that honor the operation's atomic rename semantics; an already open reader may keep the old inode.",
         boundary="Atomic replacement is a visibility contract, not a universal crash-durability promise. Durable directory-entry persistence may require a directory fsync on supported POSIX filesystems; Windows and network filesystems differ. Validate the destination and permissions, clean a failed temporary file, and coordinate concurrent writers if the last writer must not silently win.",
         source='''import os
import pathlib
import tempfile

with tempfile.TemporaryDirectory() as directory:
    target = pathlib.Path(directory) / "receipt-index.txt"
    target.write_text("revision 46\\n")
    with tempfile.NamedTemporaryFile(
        mode="w", encoding="utf-8", dir=directory,
        prefix=".receipt-index-", delete=False,
    ) as draft:
        draft.write("revision 47\\n")
        draft.flush()
        os.fsync(draft.fileno())
        draft_name = draft.name
    try:
        os.replace(draft_name, target)
    finally:
        if os.path.exists(draft_name):
            os.unlink(draft_name)
    print(target.read_text().strip())
    print("target_exists", target.exists())''', expected="revision 47\ntarget_exists True",
         cost="The write is O(bytes) and uses a second file until replacement. File fsync can add storage latency; the example does not time it or prove power-loss survival.",
         mistakes=["Writing directly to the target can expose a partial file.", "File fsync and atomic rename are distinct from directory durability.", "Last-writer-wins replacement is not a concurrency control policy."],
         related=["python/pathlib-files", "python/tempdir-cleanup-tests", "python/sqlite-cli-project"]),
]

titles = {path: row["title"] for path, row in by_path.items()}
titles.update({"python/" + item["slug"]: item["title"] for item in lessons})
for order, item in enumerate(lessons):
    path = "python/" + item["slug"]
    assert path not in by_path
    for target in item["related"]:
        assert target in titles, target
    paragraphs = [item["summary"], item["contract"], item["boundary"]]
    body = "<p>" + html.escape(paragraphs[0]) + "</p>"
    body += "<h2>Operation contract</h2><p>" + html.escape(paragraphs[1]) + "</p>"
    body += "<h2>Failure and ownership boundary</h2><p>" + html.escape(paragraphs[2]) + "</p>"
    body += '<h2>Working program</h2><pre><code class="language-python">' + html.escape(item["source"], quote=False) + "</code></pre>"
    body += '<h3>Output</h3><pre><code class="language-text">' + html.escape(item["expected"], quote=False) + "</code></pre>"
    body += "<h2>Costs and limits</h2><p>" + html.escape(item["cost"]) + "</p>"
    body += "<h3>Common Mistakes</h3><ul>" + "".join("<li>" + html.escape(text) + "</li>" for text in item["mistakes"]) + "</ul>"
    body += "<h2>Connected lessons</h2><ul>" + "".join(
        '<li><a href="/' + target + '">' + html.escape(titles[target]) + "</a></li>"
        for target in item["related"]) + "</ul>"
    row = copy.deepcopy(by_path["python/async-task-groups"])
    row.update(id=str(uuid.uuid5(uuid.NAMESPACE_URL, "https://aitrove.in/" + path)),
               path=path, title=item["title"], summary=item["summary"], body=body,
               subject=item["subject"], tags=["python", item["slug"]],
               sort_order=7500 + order, published_at=stamp, created_at=stamp, updated_at=stamp)
    row["data"] = {"subject_root": "python/python-programming-language-tutorial",
                   "section_path": item["section"], "content_format": "html", "kind": "tutorial",
                   "python_version": "3.11+ syntax; verified on local CPython",
                   "python_minimum": "3.11", "reading_minutes": 5,
                   "author_path": "authors/aitrove-editorial",
                   "download_path": "/downloads/aitrove-python-source-kit.zip",
                   "related": [{"path": target, "title": titles[target]} for target in item["related"]],
                   "seo_ready": True, "expected_output": item["expected"]}
    rows.append(row)
    by_path[path] = row

for section in sorted({item["section"] for item in lessons}):
    paths = ["python/" + item["slug"] for item in lessons if item["section"] == section]
    hub = by_path[section]
    hub["data"]["modules"].append({"title": "Process and data boundaries", "summary": "Runnable operation and failure contracts.", "lessons": paths})
    hub["body"] += "<h2>Process and data boundaries</h2><ul>" + "".join(
        '<li><a href="/' + path + '">' + html.escape(titles[path]) + "</a></li>"
        for path in paths) + "</ul>"
    hub["updated_at"] = stamp

parent = by_path["python/python-programming-language-tutorial"]
parent["body"] += "<h2>Process and data contracts</h2><ul>" + "".join(
    '<li><a href="/python/' + item["slug"] + '">' + html.escape(item["title"]) + "</a></li>"
    for item in lessons) + "</ul>"
parent["updated_at"] = stamp
for source, target in [
    ("python/subprocess-boundaries", "python/subprocess-timeout-reap"),
    ("python/url-target-policy", "python/tls-client-context-policy"),
    ("python/sqlite-transactions", "python/sqlite-migration-rollback"),
    ("python/json-validation", "python/json-duplicate-name-rejection"),
    ("python/zip-member-validation", "python/tar-member-preflight"),
    ("python/unittest-subtests", "python/generated-invariant-cases"),
    ("python/pathlib-files", "python/atomic-file-replacement"),
]:
    row = by_path[source]
    row["body"] += '<p><a href="/' + target + '">Continue with ' + html.escape(titles[target]) + "</a>.</p>"
    row["updated_at"] = stamp

quiz_path = "quizzes/python-process-data-boundaries"
assert quiz_path not in by_path
quiz = copy.deepcopy(by_path["quizzes/python-boundary-contracts"])
quiz_targets = ["python/" + item["slug"] for item in lessons]
quiz_body = "<p>Test the operation and failure boundaries before adapting these fixtures.</p><h2>Review the related lessons</h2><ul>"
quiz_body += "".join('<li><a href="/' + target + '">' + html.escape(titles[target]) + "</a></li>" for target in quiz_targets)
quiz_body += "</ul><h3>Common Mistakes</h3><p>These answers do not prove a remote TLS peer, a deployment migration, or an archive extraction service.</p>"
quiz.update(id=str(uuid.uuid5(uuid.NAMESPACE_URL, "https://aitrove.in/" + quiz_path)),
            path=quiz_path, title="Python process and data boundary quiz",
            summary="Twelve explained checks on process ownership, TLS settings, migrations and input parsing.",
            body=quiz_body, sort_order=7700, published_at=stamp, created_at=stamp, updated_at=stamp)
raw_questions = [
    ("Does Popen.communicate(timeout=...) kill a child when time expires?", "No, the owner must stop and reap it", "Yes, along with all descendants", "Yes, if stdout is a pipe", "TimeoutExpired leaves the child running."),
    ("After killing a timed-out child with piped output, what collects its status?", "A second communicate call", "A new Popen object", "Closing only stdin", "Communicate drains the pipes and reaps the child."),
    ("What does a tempfile stdout redirect bound?", "Application memory used for captured stdout", "The child’s total disk writes", "The command’s CPU usage", "Spooling moves output out of a Python string but needs a storage quota."),
    ("Does a zero subprocess exit status validate a report schema?", "No, validate the output separately", "Yes, every byte is trusted", "Only when stderr is empty", "Exit status is a process result, not a data contract."),
    ("What does the local SSLContext fixture prove?", "Hostname and certificate checks are configured", "A remote server passed a handshake", "All destinations are authorized", "Inspecting a context does not open a socket."),
    ("What should accompany a client TLS connection’s certificate validation?", "The expected hostname", "An arbitrary forwarded header", "A disabled hostname check", "The peer certificate must match the intended identity."),
    ("What remains after the failed SQLite migration in this fixture?", "Version one and the original columns", "Version two and the new column", "No receipts table", "Explicit rollback undoes the attempted DDL in this transaction."),
    ("Why avoid executescript inside a caller-owned pending SQLite transaction?", "It can implicitly commit pending work", "It always creates a savepoint", "It never executes DDL", "Its transaction behavior differs from separate execute calls."),
    ("How can json.loads reject repeated object names?", "Use object_pairs_hook to inspect pairs", "Set sort_keys=True", "Encode the input twice", "The pairs hook sees duplicate names before a dict drops the distinction."),
    ("Does inspecting tar member names alone prove safe extraction?", "No, links, quotas and destination races remain", "Yes, if the archive parses", "Yes, when every name is lowercase", "Metadata preflight is one layer, not an extraction sandbox."),
    ("What does the 95-case integer loop prove?", "Its stated invariant for that bounded fixture", "Every possible input string", "Correctness of an unrelated parser", "Generated cases are evidence for the chosen domain only."),
    ("What is distinct from atomic os.replace visibility?", "Crash durability of the directory entry", "The target pathname", "Closing the temporary file", "Atomic name replacement does not itself promise power-loss persistence."),
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
quiz_hub["body"] = quiz_hub["body"].replace("</ul><h2>Continue learning</h2>",
    '<li><a href="/' + quiz_path + '">' + html.escape(quiz["title"]) + "</a></li></ul><h2>Continue learning</h2>")
parent["body"] += '<p><a href="/' + quiz_path + '">Check the process and data boundary quiz</a>.</p>'
for target in quiz_targets:
    by_path[target]["body"] += '<p><a href="/' + quiz_path + '">Test this boundary</a>.</p>'

fixture.write_text(json.dumps(rows, ensure_ascii=False, indent=2) + "\n")
print("Added", len(lessons), "lessons and one quiz")
