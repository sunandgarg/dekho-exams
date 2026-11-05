"""Add a scored self-check for Spring Batch restart and Modulith boundaries."""

import copy
import datetime
import html
import json
import pathlib
import uuid

ROOT = pathlib.Path(__file__).resolve().parents[1]
FILE = ROOT / "src/data/fixtures.json"
rows = json.loads(FILE.read_text())
by = {row["path"]: row for row in rows}
stamp = datetime.datetime.now(datetime.UTC).isoformat()
path = "quizzes/spring-batch-modulith"
assert path not in by

questions = [
    ("A four-row import commits rows 1 and 2, then fails while writing row 3. What remains in the target table?", ["The first two committed rows", "No rows because the entire job rolls back", "All four rows"], 0, "A chunk step commits successful groups separately; the later failed group rolls back its own work."),
    ("The operator relaunches a failed import for the same manifest. Which parameter rule preserves the JobInstance?", ["Use the same identifying manifest ID", "Add the current timestamp as an identifying value", "Use a new random manifest ID"], 0, "A new identifying value creates a different JobInstance and may repeat committed business work."),
    ("A completed JobInstance is launched again with identical identifying parameters. What should the operator expect?", ["Spring Batch rejects the duplicate completed instance", "The old execution resumes at row 3", "The repository silently deletes prior metadata"], 0, "A completed instance is not a failed execution to restart; a new business run needs a distinct identity."),
    ("The failed execution saved a reader count of two, but restart revisits committed rows. Which sink rule matters?", ["Use a stable source key and reconcile a replay", "Trust the saved count as exactly-once delivery", "Disable all database constraints"], 0, "Reader metadata is not a substitute for an idempotent destination decision."),
    ("An H2 MERGE makes the local import test pass. What still needs review for a production ledger?", ["Changed payload under the same source ID and the target database's upsert semantics", "Only the page color", "Whether the source ID can be removed"], 0, "A blind upsert can overwrite a previously accepted value, and H2 syntax does not specify another database's behavior."),
    ("A receipt writer calls an external HTTP service inside the chunk transaction. The database chunk rolls back. What can be inferred about the HTTP call?", ["Its effect may already have happened", "It always rolls back with the database", "Spring Batch removes the remote request"], 0, "The local transaction manager does not govern a remote service's commit."),
    ("A malformed row always has the same invalid bytes. Which failure policy fits?", ["Reject or skip it under an explicit reconciliation rule", "Retry forever", "Treat it as a temporary database deadlock"], 0, "A deterministic parse failure is not repaired by repetition; skipped business rows need accounting."),
    ("A retry policy handles a brief deadlock. What must bound the extra work?", ["A retry limit and a failure outcome", "An unlimited loop", "A larger heading on the lesson"], 0, "Retries can repeat reads and writes, so they need a budget and a visible terminal result."),
    ("Dispatch imports InventoryQueries from the inventory root package. What does Modulith verification check?", ["That the package dependency follows the module API boundary", "That the caller is authorized for the tenant", "That Kafka accepted an event"], 0, "Package verification checks structure, not user permissions or external delivery."),
    ("Dispatch constructs a public inventory.internal class. Java compilation succeeds. What should the architecture check report?", ["An invalid cross-module internal dependency", "A valid API because the class is public", "A missing network route"], 0, "The root package is the default API; public visibility alone does not make an internal package part of it."),
    ("An ApplicationModules.verify test passes. What has not yet been demonstrated?", ["Bean wiring and listener behavior in a running Spring context", "That classes were available to the scanner", "That the package graph passed its declared rules"], 0, "Classpath architecture verification does not instantiate beans or deliver events."),
    ("Inventory emits ReceiptReserved before its version check succeeds. What is wrong?", ["It announced a successful domain fact before the guarded state change", "The event name is too short", "The module root cannot contain records"], 0, "A rejected reservation must not produce a success event; the publication boundary needs a committed decision."),
    ("A transactional listener publication is recorded by a configured Modulith registry. What does that prove about a Kafka send?", ["Nothing about broker acceptance yet", "The broker has committed the message", "The consumer has processed it exactly once"], 0, "A local publication record and an external broker acknowledgement are different boundaries."),
    ("Which next test closes the largest gap in the current isolated Modulith fixture?", ["Start a module context and assert state plus event behavior", "Repeat the same classpath scan ten times", "Replace the module API with a private import"], 0, "The current checks prove the dependency graph; a running module test would check wiring and behavior."),
]

review_paths = [
    "spring/batch-job-identity", "spring/batch-committed-chunk",
    "spring/batch-idempotent-writer", "spring/batch-retry-skip-policy",
    "spring/modulith-module-api", "spring/modulith-internal-violation",
    "spring/modulith-event-boundary", "spring/modulith-module-tests",
]
assert all(target in by for target in review_paths)
body = "<p>Spring Batch restarts preserve committed work, while a Modulith package check constrains which classes another module may call.</p>"
body += "<h2>Review the boundaries</h2><ul>" + "".join(
    '<li><a href="/' + target + '">' + html.escape(by[target]["title"]) + "</a></li>"
    for target in review_paths) + "</ul>"
body += "<h2>Check your reasoning</h2><p>Answer each question and inspect the explanation. This browser self-check does not run a production database or event broker.</p>"
body += "<h3>Common Mistakes</h3><p>A saved cursor does not prove exactly-once output, and a package check does not prove runtime delivery.</p>"

row = copy.deepcopy(by["quizzes/spring-core"])
row.update(id=str(uuid.uuid5(uuid.NAMESPACE_URL, "https://aitrove.in/" + path)), path=path,
    title="Spring Batch and Modulith boundary quiz",
    summary="Check chunk commits, job identity, replay safety, module APIs and event-delivery limits.",
    body=body, sort_order=750,
    tags=["spring", "spring-boot", "spring-batch", "spring-modulith", "quiz"],
    published_at=stamp, created_at=stamp, updated_at=stamp)


def positioned_question(index, prompt, options, answer, explanation):
    shift = index % len(options)
    shifted = options[shift:] + options[:shift]
    return {"prompt": prompt, "options": shifted,
            "answer": (answer - shift) % len(options), "explanation": explanation}


row["data"] = {"questions": [
    positioned_question(index, prompt, options, answer, explanation)
    for index, (prompt, options, answer, explanation) in enumerate(questions)],
    "duration_minutes": 12, "subject_root": "spring/spring-boot",
    "section_path": "spring/quizzes", "content_format": "html", "seo_ready": True}
rows.append(row)
hub = by["spring/quizzes"]
hub["data"]["modules"].append({"title": "Batch and Modulith boundaries",
    "summary": "Fourteen decisions across restart, replay, package APIs and events.",
    "lessons": [path]})
hub["body"] += '<h2>Batch and Modulith self-check</h2><p><a href="/' + path + '">' + row["title"] + "</a></p>"
hub["updated_at"] = stamp
FILE.write_text(json.dumps(rows, ensure_ascii=False, indent=2) + "\n")
print("Added", len(questions), "Spring Batch and Modulith questions")
