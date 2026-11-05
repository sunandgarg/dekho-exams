"""Extend the Spring data quiz with checked tenant command outcomes."""
from __future__ import annotations

import datetime
import html
import json
import pathlib

ROOT = pathlib.Path(__file__).resolve().parents[1]
FILE = ROOT / "src/data/fixtures.json"
rows = json.loads(FILE.read_text())
quiz = next(row for row in rows if row["path"] == "quizzes/spring-data-production")
by_path = {row["path"]: row for row in rows}
questions = [
    ("A tenant-east write commits a receipt, an outbox row and a replay row. What makes those three writes atomic in the local fixture?",
     ["A single H2 transaction using one DataSource", "The JWT signature", "A broker acknowledgement"], 0,
     "TransactionTemplate encloses all three JDBC writes on one DataSource. The token controls identity, not database commit."),
    ("A POST retry uses the same tenant, key, receipt, state and expected version. What should happen?",
     ["Return the stored version without a second event", "Increment the version again", "Reject it as a stale write"], 0,
     "The replay row is checked before the versioned update, so the accepted response can be returned again."),
    ("The same tenant and key are reused for another receipt ID. How does the fixture respond?",
     ["It changes the second receipt", "It returns 409", "It publishes another event"], 1,
     "The command fingerprint includes the receipt ID, so the reused key cannot identify a different command."),
    ("A write expects version 3 while the stored row is version 1. What remains after the request?",
     ["The state changes and no event is stored", "No state change, event or replay row", "An event is stored for later repair"], 1,
     "The parameterized update affects zero rows, raises a conflict and exits the transaction before inserts."),
    ("The service throws after inserting the outbox row but before inserting its replay row. Which result is checked?",
     ["All database changes roll back", "Only the outbox row commits", "The receipt commits while the replay row disappears"], 0,
     "The test inspects the receipt, outbox and replay tables after the injected failure."),
    ("Does a committed outbox row mean an external consumer received the event?",
     ["Yes, the transaction spans the broker", "No, delivery and acknowledgement are separate work", "Only when the JWT has receipt.write"], 1,
     "The local command fixture records intent in H2; it does not run a relay, broker or consumer."),
    ("Why is an accepted east write with X-Tenant: tenant-west still an east write?",
     ["The trusted JWT claim and service rule supply tenant ownership", "The header is signed by the database", "The URL path always overrides the token"], 0,
     "The header is request data. The method rule compares the requested tenant with the validated token principal."),
]
assert len(quiz["data"]["questions"]) == 18
quiz["data"]["questions"].extend(dict(prompt=prompt, options=options, answer=answer, explanation=explanation)
    for prompt, options, answer, explanation in questions)
quiz["summary"] = "Twenty-five explained questions on Spring data, delivery and tenant command boundaries."
related = ["spring/tenant-command-transaction", "spring/tenant-idempotency-key-scope",
    "spring/tenant-versioned-write", "spring/receipt-outbox-command",
    "spring/command-rollback-proof", "spring/tenant-command-trace-exercise"]
links = "".join('<li><a href="/' + path + '">' + html.escape(by_path[path]["title"]) + "</a></li>"
    for path in related)
quiz["body"] = quiz["body"].replace("</ul><h2>Check your reasoning</h2>",
    links + "</ul><h2>Check your reasoning</h2>")
quiz["updated_at"] = datetime.datetime.now(datetime.UTC).isoformat()
FILE.write_text(json.dumps(rows, ensure_ascii=False, indent=2) + "\n")
print(json.dumps({"quiz": quiz["path"], "questions": len(quiz["data"]["questions"])}))
