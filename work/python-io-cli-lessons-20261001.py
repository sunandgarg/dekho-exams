"""Add three runnable Python I/O and command-boundary lessons."""

import copy
import datetime
import html
import json
import pathlib
import re
import uuid

ROOT = pathlib.Path(__file__).resolve().parents[1]
FIXTURE = ROOT / "src/data/fixtures.json"
rows = json.loads(FIXTURE.read_text())
by_path = {row["path"]: row for row in rows}
stamp = datetime.datetime.now(datetime.UTC).isoformat()

lessons = [
    dict(slug="csv-spreadsheet-export-boundary", section="python/examples", subject="python-examples",
         title="Python CSV export: spreadsheet cells are an execution boundary",
         summary="CSV quoting preserves field structure, but a spreadsheet may interpret a leading cell value as a formula.",
         explanation="A support report includes an untrusted label beginning with =. csv.writer escapes delimiters and quotes; it does not decide whether a spreadsheet executes that cell. For a human-viewed export, this program adds a tab prefix to suspicious leading characters and quotes all fields. That changes the underlying data. Keep machine-readable interchange separate from the spreadsheet rendition. [[python/csv-duplicate-headers|Header validation]] and [[python/bounded-csv|row limits]] address other boundaries.",
         boundary="Spreadsheet programs vary, and a save/reopen cycle can change how cells are interpreted. Test the actual spreadsheet used by your audience. The prefix policy applies only at the start of a cell; if a product trims whitespace or normalizes input first, do the policy after that normalization. Never claim this format is universally safe or lossless. A typed exchange format is better when clients need exact data.",
         source='''import csv
import io

def spreadsheet_cell(value):
    return "\\t" + value if value and value[0] in "=+-@" else value

output = io.StringIO()
writer = csv.writer(output, lineterminator="\\n", quoting=csv.QUOTE_ALL)
writer.writerow([spreadsheet_cell("=47+1"), spreadsheet_cell("safe-label")])
print(repr(output.getvalue()))''',
         expected=repr('"\t=47+1","safe-label"\n'),
         cost="The cell scan is O(total field bytes). Maintaining two export contracts costs more than one file, but avoids silently corrupting a machine import.",
         mistakes=["CSV quoting alone does not settle spreadsheet formula interpretation.", "No single text prefix is safe for every spreadsheet and downstream consumer.", "Do not feed altered display cells into a lossless import without a reversal contract."],
         related=["python/csv-import", "python/csv-duplicate-headers", "python/bounded-csv"]),
    dict(slug="ipaddress-network-membership", section="python/web-applications", subject="python-web",
         title="Python ipaddress membership: parse the peer before an allowlist",
         summary="ipaddress can classify a parsed address against a CIDR network; the harder question is which peer address to trust.",
         explanation="An internal webhook accepts traffic from one documented IPv4 range. ip_address parses the address and membership checks the network. This program proves that pure predicate. It does not prove where peer_text came from. A header supplied by the requester is not a peer identity unless a trusted proxy rewrites it and the application trusts that proxy. [[python/url-target-policy|Outbound target rules]] protect a different network direction.",
         boundary="IPv4 and IPv6 are different families. Malformed text raises ValueError and must not fall through to allow. If the service sits behind several proxies, define exactly which hop supplies the canonical peer, strip untrusted forwarding headers at the edge, and test that path. A private or reserved range is not automatically authorized.",
         source='''from ipaddress import ip_address, ip_network

allowed = ip_network("192.0.2.0/24")
for peer_text in ("192.0.2.47", "203.0.113.7", "invalid"):
    try:
        accepted = ip_address(peer_text) in allowed
    except ValueError:
        accepted = False
    print(peer_text, accepted)''',
         expected="192.0.2.47 True\n203.0.113.7 False\ninvalid False",
         cost="A membership test is cheap for one network. A large policy list needs an indexed or precomputed structure, while trusted-peer extraction remains a separate boundary.",
         mistakes=["Do not trust an arbitrary forwarded header as the peer address.", "A private or reserved address is not permission by itself.", "Malformed addresses must not fall back to allow."],
         related=["python/url-target-policy", "python/flask-routing", "python/json-validation"]),
    dict(slug="argparse-command-contract", section="python/projects", subject="python-projects",
         title="Python argparse subcommands: require the operation before side effects",
         summary="An argparse subcommand separates operation-specific flags and rejects a missing command before business work starts.",
         explanation="A receipt tool has a reconcile operation with tenant and limit arguments. add_subparsers(required=True) makes the command explicit, and the reconcile parser owns its flags. The program passes a fixed argv list so the lesson executes independently of the surrounding test runner. [[python/receipt-cli|The receipt CLI]] connects parsing to file and output ownership.",
         boundary="Parsing is not authorization. A tenant string still needs access checks when the command talks to a shared service. int conversion validates numeric syntax, not an acceptable range, so reject out-of-range values before opening storage or starting network work. Never let a misspelled command silently select a destructive default.",
         source='''import argparse

parser = argparse.ArgumentParser(prog="receiptctl", add_help=False)
commands = parser.add_subparsers(dest="command", required=True)
reconcile = commands.add_parser("reconcile", add_help=False)
reconcile.add_argument("--tenant", required=True)
reconcile.add_argument("--limit", type=int, required=True)
arguments = parser.parse_args([
    "reconcile", "--tenant", "north-47", "--limit", "47"
])
if not 1 <= arguments.limit <= 500:
    raise ValueError("limit outside accepted range")
print(arguments.command, arguments.tenant, arguments.limit)''',
         expected="reconcile north-47 47",
         cost="Argument parsing is small relative to the operation. Explicit subcommands prevent ambiguous flag sets but need versioned usage documentation.",
         mistakes=["A parsed tenant string does not prove access.", "Do not default to destructive work when the command is missing.", "type=int checks syntax but not the domain range."],
         related=["python/receipt-cli", "python/configuration-precedence", "python/input-exercise"]),
]

titles = {path: row["title"] for path, row in by_path.items()}
titles.update({"python/" + item["slug"]: item["title"] for item in lessons})
for number, item in enumerate(lessons):
    path = "python/" + item["slug"]
    assert path not in by_path
    for target in item["related"]:
        assert target in titles, (path, target)
    body = "<p>" + html.escape(item["summary"]) + "</p>"
    body += "<h2>Operation contract</h2><p>" + re.sub(r"\[\[([^|]+)\|([^\]]+)\]\]", lambda m: '<a href="/' + m[1] + '">' + m[2] + "</a>", html.escape(item["explanation"])) + "</p>"
    body += "<h2>Failure and ownership boundary</h2><p>" + html.escape(item["boundary"]) + "</p>"
    body += '<h2>Working program</h2><pre><code class="language-python">' + html.escape(item["source"], quote=False) + "</code></pre>"
    body += '<h3>Output</h3><pre><code class="language-text">' + html.escape(item["expected"], quote=False) + "</code></pre>"
    body += "<h2>Costs and limits</h2><p>" + html.escape(item["cost"]) + "</p>"
    body += "<h3>Common Mistakes</h3><ul>" + "".join("<li>" + html.escape(m) + "</li>" for m in item["mistakes"]) + "</ul>"
    body += "<h2>Connected lessons</h2><p>" + ", ".join('<a href="/' + target + '">' + html.escape(titles[target]) + "</a>" for target in item["related"]) + ".</p>"
    row = copy.deepcopy(by_path["python/async-task-groups"])
    row.update(id=str(uuid.uuid5(uuid.NAMESPACE_URL, "https://aitrove.in/" + path)), path=path,
               title=item["title"], summary=item["summary"], body=body, subject=item["subject"],
               tags=["python", item["slug"]], sort_order=7100 + number,
               published_at=stamp, created_at=stamp, updated_at=stamp)
    row["data"] = {
        "subject_root": "python/python-programming-language-tutorial",
        "section_path": item["section"], "content_format": "html", "kind": "tutorial",
        "python_version": "3.11+ syntax; verified on local CPython", "python_minimum": "3.11",
        "reading_minutes": max(4, round(len(re.sub(r"<[^>]+>", " ", body).split()) / 150)),
        "author_path": "authors/aitrove-editorial",
        "download_path": "/downloads/aitrove-python-source-kit.zip",
        "related": [{"path": target, "title": titles[target]} for target in item["related"]],
        "seo_ready": True, "expected_output": item["expected"],
    }
    rows.append(row)
    by_path[path] = row

for section, heading in {
    "python/examples": "Spreadsheet export boundaries",
    "python/web-applications": "Network peer classification",
    "python/projects": "Command-line contracts",
}.items():
    paths = ["python/" + item["slug"] for item in lessons if item["section"] == section]
    hub = by_path[section]
    hub["data"]["modules"].append({"title": heading, "summary": "Runnable boundary checks.", "lessons": paths})
    hub["body"] += "<h2>" + heading + "</h2><ul>" + "".join(
        '<li><a href="/' + path + '">' + html.escape(titles[path]) + "</a></li>" for path in paths
    ) + "</ul>"
    hub["updated_at"] = stamp

parent = by_path["python/python-programming-language-tutorial"]
parent["body"] += "<h2>Export, network and command contracts</h2><ul>" + "".join(
    '<li><a href="/python/' + item["slug"] + '">' + html.escape(item["title"]) + "</a></li>"
    for item in lessons
) + "</ul>"
parent["updated_at"] = stamp
for source, target in [
    ("python/csv-import", "python/csv-spreadsheet-export-boundary"),
    ("python/url-target-policy", "python/ipaddress-network-membership"),
    ("python/receipt-cli", "python/argparse-command-contract"),
]:
    row = by_path[source]
    row["body"] += '<h2>Related boundary</h2><p><a href="/' + target + '">' + html.escape(titles[target]) + "</a></p>"
    row["updated_at"] = stamp

FIXTURE.write_text(json.dumps(rows, ensure_ascii=False, indent=2) + "\n")
print("Added", len(lessons), "Python I/O and CLI lessons")
