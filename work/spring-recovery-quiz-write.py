"""Extend the Spring data/production quiz with checked worker recovery cases."""
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
    ("One receipt task runs and one waits in a one-thread, one-slot executor. What should the default policy do with a third submission?",
     ["Store it durably", "Reject the third task", "Start an unlimited worker"], 1,
     "The bounded executor fixture observes TaskRejectedException. Neither running nor queued work is durable."),
    ("Worker-A holds an outbox lease until logical time 200. Can worker-B claim the row at time 150?",
     ["Yes, if it uses a different token", "No, the prior lease is still valid", "Yes, if the event is old"], 1,
     "The conditional update refuses a second claim before expiry."),
    ("After worker-B reclaims an expired row, what should worker-A's acknowledgement update?",
     ["The delivered flag", "No rows", "Every row for the same receipt"], 1,
     "A current claim token in the update predicate fences a stale owner from changing the row."),
    ("Why record an event ID and apply the stock mutation in one transaction?",
     ["To make broker delivery exactly once", "To make a failed mutation roll back its dedup record", "To avoid a database uniqueness constraint"], 1,
     "The local fixture checks both repeat suppression and rollback of an event ID after a failed stock change."),
    ("A relay sends E-41 and stops before it can persist acknowledgement. What can a retry do?",
     ["Send E-41 again", "Prove E-41 was never seen", "Undo the first send automatically"], 0,
     "The send and database acknowledgement have a failure window; the destination needs its own duplicate rule."),
    ("What does the local outbox lease test establish about two deployed replicas?",
     ["Their concurrent claims are safe under load", "Only sequential H2 lease and token outcomes", "Their clocks cannot differ"], 1,
     "The checked fixture uses deterministic times and sequential statements; deployment concurrency still needs a target-database test."),
]
assert len(quiz["data"]["questions"]) == 12
quiz["data"]["questions"].extend(dict(prompt=prompt, options=options, answer=answer, explanation=explanation)
    for prompt, options, answer, explanation in questions)
quiz["summary"] = "Eighteen explained questions on Spring data, worker recovery and production boundaries."
related = ["spring/bounded-executor-rejection", "spring/outbox-expiring-lease",
    "spring/outbox-fenced-ack", "spring/consumer-dedup-transaction",
    "spring/at-least-once-delivery-boundary"]
links = "".join('<li><a href="/' + path + '">' + html.escape(by_path[path]["title"]) + "</a></li>"
    for path in related)
quiz["body"] = quiz["body"].replace("</ul><h2>Check your reasoning</h2>",
    links + "</ul><h2>Check your reasoning</h2>")
quiz["updated_at"] = datetime.datetime.now(datetime.UTC).isoformat()
FILE.write_text(json.dumps(rows, ensure_ascii=False, indent=2) + "\n")
print(json.dumps({"quiz": quiz["path"], "questions": len(quiz["data"]["questions"])}))
