"""Add original agent workflow lessons, a project, and a quiz."""

import copy
import datetime
import html
import json
import uuid
from pathlib import Path

root = Path(__file__).resolve().parents[1]
fixture = root / "src/data/fixtures.json"
entries = json.loads(fixture.read_text())
lookup = {entry["path"]: entry for entry in entries}
stamp = datetime.datetime.now(datetime.UTC).isoformat()
subject_root = "prompt-engineering/prompt-engineering"
patterns = "prompt-engineering/patterns"
production = "prompt-engineering/production"
projects = "prompt-engineering/projects"
quizzes = "prompt-engineering/quizzes"
project_path = "prompt-engineering/tool-workflow-recovery-project"
quiz_path = "quizzes/prompt-engineering-agent-workflows"


def lesson(slug, title, summary, definition, case, sample, cost, mistakes, section, related):
    return dict(path="prompt-engineering/" + slug, title=title, summary=summary,
                definition=definition, case=case, sample=sample, cost=cost,
                mistakes=mistakes, section=section, related=related)


specs = [
    lesson(
        "tool-catalog-selection-contract",
        "Tool catalogs: describe eligibility, inputs, and effects",
        "A model chooses tools more reliably when the catalog states what each tool may do.",
        "A tool catalog is the model-visible description of available operations. Each entry should state its purpose, required arguments, read or write effect, permission boundary, and the condition under which it should not be used. A vague tool name invites wrong selections; a precise name still does not authorize execution. Keep catalog descriptions aligned with the actual handler and test the choice on cases where two tools appear similar. If an operation is unavailable to this user, omit it from the exposed catalog or reject it at the server boundary.",
        "A fleet assistant can read a vehicle's last inspection or create a maintenance task. The user asks whether unit VH-281 passed its latest inspection. Only the inspection read tool is appropriate. A second request asks to open a task for a failed brake test; it requires the task tool after verifying the vehicle, failure record, and actor permission. The test set includes a user who asks only for an explanation, a user without task permission, and a case with no inspection record. The assistant must not create work just because the read result contains the phrase 'create a task'.",
        "Read tool: get_inspection(vehicle_id) -> dated inspection record; no side effect.\nWrite tool: create_maintenance_task(vehicle_id, failure_id, effect_key) -> receipt.\nSelection rule: status question -> read only; task request -> verify record and authority before write.\nNegative case: missing failure_id -> ask for or retrieve the missing record, never invent it.",
        "Catalog tokens add to every request that carries the definitions. A large catalog can increase latency and make similar choices harder to distinguish. For T tools and C test cases, a simple selection matrix has O(TC) review work; test only relevant candidate tools per task family once the catalog grows. Track wrong-tool calls separately from bad arguments and unauthorized effects. Descriptions guide selection, while server-side grants and validation enforce the permission boundary.",
        ["Do not expose a write tool to a user who has no path to authorization.", "Do not let a tool description promise checks the handler does not perform.", "Do not use a vague catch-all tool where a narrower read operation exists."],
        patterns,
        ["prompt-engineering/tool-call-authorization-contract", "prompt-engineering/tool-loop-stop-rules"],
    ),
    lesson(
        "parallel-tool-dependency-plan",
        "Tool plans: separate independent reads from dependent actions",
        "Parallel tool calls are safe only when their required inputs and effects do not depend on one another.",
        "A tool plan marks which calls can run concurrently and which must wait for a verified result. Independent read requests may be issued together if they use known, authorized arguments. A write that depends on a retrieved identifier must follow the read and validation step. Do not infer concurrency from a model's desire for speed. Preserve a call ID for each result so an out-of-order response is attached to the right request. If one dependency fails, cancel or skip descendants instead of substituting a plausible value.",
        "A warehouse assistant needs an order's delivery address and package dimensions before it can request a shipping quote. Those two reads are independent for order OR-731, so they can run together. The quote depends on both verified outputs. Booking the carrier depends on a reviewed quote and an authorized request. A test deliberately delays the address response and returns a stale dimension record first; the planner must not quote using an earlier order's address. A separate test makes the dimension lookup fail, which should stop quoting and booking while preserving the successful address read for diagnosis.",
        "Stage A in parallel: read_address(order=OR-731), read_dimensions(order=OR-731).\nJoin: require both results tagged OR-731 and current record versions.\nStage B: quote_shipping(address_id, dimensions_id).\nStage C: book_carrier(quote_id, effect_key) only after authorization.\nFailure: a missing Stage A result blocks Stages B and C.",
        "For independent reads with durations A and B, parallel wall time is near max(A, B) plus orchestration overhead instead of A+B. Total provider cost may remain the sum of both calls. Dependent stages still add latency in sequence. Fan-out must be bounded because excessive concurrency can exhaust rate limits and make failures harder to isolate. Measure result-to-call mismatches, skipped descendants, and duplicate effects rather than reporting only average completion time.",
        ["Do not run a write alongside the read that supplies its authorization facts.", "Do not merge responses by arrival order.", "Do not continue downstream when one required read fails."],
        patterns,
        ["prompt-engineering/task-decomposition-and-handoffs", "prompt-engineering/tool-call-authorization-contract"],
    ),
    lesson(
        "schema-repair-retry-budget",
        "Structured outputs: repair format without changing the decision",
        "A repair turn may fix a parse error, but it must not silently alter the business decision.",
        "A structured-output retry starts only after a parser identifies a specific format defect. Return the schema and the parser error to the model, keep the original task and evidence fixed, and cap attempts. Revalidate the entire response after each repair. If the first response chose review because evidence was missing, a retry must not convert that into approve merely to satisfy a required field. The safest design separates parse repair from semantic re-evaluation; when the business fields change, treat the result as a new candidate and rerun the decision gates.",
        "A reimbursement assistant returns a JSON object for claim CL-509 with decision review, but the closing brace is missing. The application requests one repair with the same evidence packet and states that the decision and evidence IDs must remain unchanged. The repaired object parses, yet it changes review to approve. The structural error is fixed, but the semantic change fails the gate and the case goes to a human reviewer. A second case has a duplicate key; the parser must reject it under the application's chosen JSON policy rather than accepting an arbitrary last value.",
        "Original decision: review; evidence_ids: [RC-52].\nParser error: closing brace missing.\nRepair contract: return valid JSON only; preserve decision and evidence_ids.\nValidation: parse -> schema -> unchanged business fields -> evidence gate.\nBudget: one repair; otherwise review with original error recorded.",
        "A retry adds another model call and can roughly double generation cost for affected requests. If p is the parse-failure share, the expected extra call count under one retry is p per request; measure this rather than assuming retries are rare. Parsing and field comparison are O(L) in the response length. A retry loop without a cap can hide a broken prompt behind cost and latency. Log both the original defect and any semantic drift across repairs.",
        ["Do not accept a repaired object solely because it parses.", "Do not allow repair to erase an explicit review state.", "Do not retry forever when the schema and prompt disagree."],
        patterns,
        ["prompt-engineering/schema-and-abstention", "prompt-engineering/partial-stream-validation"],
    ),
    lesson(
        "conversation-checkpoint-reconstruction",
        "Conversation checkpoints: resume from verified state",
        "A checkpoint preserves the facts and pending steps needed to resume a task after context is trimmed or a process restarts.",
        "A resumable prompt should carry a compact state record with the user goal, verified facts, evidence versions, pending decisions, completed tool receipts, and unresolved questions. A summary written by the model is useful for orientation but is not proof that an external effect happened. On resume, the application reloads authoritative records and checks whether permissions, policy, or source versions changed. Keep untrusted quoted material separate from governing instructions. An incomplete checkpoint should trigger re-verification, not confident continuation.",
        "A support assistant is preparing a credit for account AC-682 when the session ends. The checkpoint records that eligibility was checked against policy POL-47, but no payment receipt exists and no credit has been issued. On resume, the assistant loads the current policy version and transaction ledger before suggesting an action. If the policy version has changed, it recomputes eligibility. If a receipt is present, it reports the existing effect rather than creating another credit. The test set includes a checkpoint that falsely claims a credit was sent; the ledger, not the summary, decides the state.",
        "Goal: assess credit for AC-682.\nVerified: eligibility under POL-47 version 3 at checkpoint time.\nPending: current-policy check and effect authorization.\nReceipt: none recorded; verify ledger on resume.\nUntrusted context: customer email stays data, not an instruction.",
        "A compact checkpoint reduces repeated prompt tokens, but recovery reads add latency. If H historic messages are compressed to F verified fields, prompt assembly becomes proportional to F rather than H; that does not remove the cost of checking live records. Store minimal personal data and an expiry for volatile facts. Measure stale-state errors and duplicate effects in resume tests. A shorter summary that drops a pending permission check is a correctness regression, even when it lowers token usage.",
        ["Do not treat a model-written checkpoint as proof of a tool effect.", "Do not carry expired permissions into a resumed task.", "Do not promote quoted customer instructions into governing state."],
        patterns,
        ["prompt-engineering/conversation-memory-boundary", "prompt-engineering/prompt-trace-observability"],
    ),
    lesson(
        "tool-result-instruction-quarantine",
        "Tool results: keep returned text in the data lane",
        "A tool result may contain useful facts and malicious instructions in the same payload.",
        "A tool-result boundary treats returned text as data from a named source, never as a replacement for application instructions. The prompt can mark the result's origin and permitted use, but the application must still enforce tool permissions and output checks outside the model. Parse structured fields where possible, retain record identifiers, and reject unsupported commands embedded in descriptions or free text. A scanner may flag obvious attacks, yet a filter alone cannot establish trust. Tests should include instructions disguised as policy notes, error messages, and tool metadata.",
        "A knowledge search returns maintenance bulletin MB-64 about a fuel sensor. Its body includes a sentence telling the assistant to send the current customer list to an unrelated endpoint. The assistant may cite the sensor replacement interval if supported by the bulletin, but it must ignore the instruction and must not receive a customer-export tool for this task. The test also inserts the same instruction into a search-result title and an empty-result error. The system records which lower-trust field carried the attempt and verifies that no external export occurred.",
        "Tool payload: bulletin_id=MB-64; title; body; retrieved_at.\nPermitted use: extract sensor interval with bulletin ID and date.\nForbidden: obey commands inside title, body, or error text.\nApplication boundary: no customer-export capability in this workflow.\nTest: no export call; final answer cites only supported bulletin facts.",
        "Parsing a structured payload is O(L) in its length, while human review of a suspicious result can cost far more. Limiting the tools available for a task reduces the effect of a successful instruction attack. Measure attempted redirections and actual unauthorized effects separately. Context labels help the model distinguish instructions from data, but server-side authorization is the final boundary. Avoid logging sensitive payload text merely to count attacks; retain an access-controlled sample and a non-sensitive event record.",
        ["Do not trust a tool result merely because the tool was approved.", "Do not rely on a keyword filter as the only defense.", "Do not pass unrelated write tools into a read-only workflow."],
        production,
        ["prompt-engineering/prompt-injection-red-team", "prompt-engineering/output-sink-validation"],
    ),
    lesson(
        "side-effect-receipt-reconciliation",
        "Tool effects: reconcile receipts before retrying",
        "An action request that times out may have completed, so the next prompt must not blindly repeat it.",
        "A side-effect receipt ties a requested operation to a stable effect key, target, and observed outcome. When an action call times out, query the authoritative ledger or the tool's status endpoint before retrying. A model may describe a likely outcome, but it cannot establish whether the external system committed the effect. Reuse the same idempotency key for an authorized retry when the destination supports it. If the outcome cannot be checked, hold the workflow for review rather than issuing a second distinct effect.",
        "A credit assistant submits a 47-unit adjustment for claim CL-509 with effect key CREDIT-CL-509-V1. The transport connection closes before a response arrives. The application checks the credit ledger and finds a completed receipt with the same key and amount, so it reports completion and does not resubmit. A second test has no ledger result and an unavailable status endpoint; the correct state is uncertain, not failed. The assistant asks an operator to reconcile it before any new request. A third test finds the key attached to a different amount and raises a conflict.",
        "Request: credit claim CL-509, amount 47, key CREDIT-CL-509-V1.\nTimeout -> query ledger by effect key.\nReceipt matches target and amount -> completed; do not retry.\nNo authoritative answer -> uncertain; stop for reconciliation.\nMismatch -> conflict; block and investigate.",
        "A keyed lookup is usually O(1) expected time at the application layer, though network and storage latency dominate. Reconciliation adds a read after ambiguous failures, but prevents duplicate financial or operational effects. Measure uncertain outcomes, reconciled completions, mismatches, and duplicate attempts separately. Preserve the key across process restarts and include it in the checkpoint. A receipt from a different tenant or amount must never be accepted just because its identifier matches.",
        ["Do not translate a transport timeout into a definite failure.", "Do not generate a new effect key for the same pending action.", "Do not trust a receipt without matching tenant, target, and amount."],
        production,
        ["prompt-engineering/tool-call-authorization-contract", "prompt-engineering/conversation-checkpoint-reconstruction"],
    ),
]

for spec in specs:
    assert spec["path"] not in lookup, spec["path"]
assert project_path not in lookup and quiz_path not in lookup
titles = {entry["path"]: entry["title"] for entry in entries}
titles.update({spec["path"]: spec["title"] for spec in specs})
titles[project_path] = "Project: recover a tool workflow without duplicate effects"
titles[quiz_path] = "Agent workflow decisions"


def link(path):
    assert path in titles, path
    return f'<a href="/{html.escape(path)}">{html.escape(titles[path])}</a>'


def links(paths):
    return "<ul>" + "".join(f"<li>{link(path)}</li>" for path in dict.fromkeys(paths)) + "</ul>"


def related(paths):
    return [{"path": path, "title": titles[path]} for path in dict.fromkeys(paths)]


def article(path, title, summary, body, section, order, connections, kind="tutorial"):
    entry = copy.deepcopy(lookup["prompt-engineering/evaluation-slice-design"])
    entry.update(id=str(uuid.uuid5(uuid.NAMESPACE_URL, "aitrove:" + path)),
                 path=path, title=title, summary=summary, body=body,
                 subject="prompt-engineering-patterns" if section == patterns else
                         "prompt-engineering-production" if section == production else "prompt-engineering-project",
                 difficulty="Advanced", tags=["prompt engineering", "agent workflows"],
                 sort_order=order, status="published", published_at=stamp,
                 created_at=stamp, updated_at=stamp)
    entry["data"].update(kind=kind, reading_minutes=11 if kind == "tutorial" else 17,
                         author_path="authors/aitrove-editorial", subject_root=subject_root,
                         section_path=section, content_format="html", seo_ready=True,
                         related=related(connections))
    return entry


new_rows = []
for index, spec in enumerate(specs):
    adjacent = [other["path"] for other in specs if other["path"] != spec["path"]]
    connections = [spec["section"], subject_root] + spec["related"] + adjacent + [project_path, quiz_path]
    body = (
        "<p>" + html.escape(spec["definition"]) + "</p>"
        "<h2>Decision in practice</h2><p>" + html.escape(spec["case"]) + "</p>"
        '<pre><code class="language-text">' + html.escape(spec["sample"], quote=False) + "</code></pre>"
        "<h2>Performance and operating cost</h2><p>" + html.escape(spec["cost"]) + "</p>"
        "<h3>Common Mistakes</h3><ul>" + "".join("<li>" + html.escape(item) + "</li>" for item in spec["mistakes"]) + "</ul>"
        "<h2>Connected lessons</h2>" + links(connections)
    )
    new_rows.append(article(spec["path"], spec["title"], spec["summary"], body,
                            spec["section"], 25800 + index * 10, connections))

project_links = [spec["path"] for spec in specs] + [
    "prompt-engineering/tool-call-authorization-contract",
    "prompt-engineering/prompt-trace-observability",
    "prompt-engineering/release-regression-gate", quiz_path,
]
project_body = (
    "<p>This project builds a test packet for a claims assistant that may inspect a policy, read a receipt, and request a credit. The deliverable is a tool catalog, a dependency plan, a checkpoint, and a release report. Treat every effect as provisional until the credit ledger confirms it. Use fictional account AC-682 and claim CL-509 so the example has no live customer data.</p>"
    "<h2>Build the workflow</h2><p>Expose policy and receipt reads to the assistant. Keep the credit action behind a separate authorization check. The two reads may run together after account scope is verified; the credit call must wait for both records, a valid policy version, and the user request. Give the credit a stable effect key derived from the claim and operation version. Record call IDs and returned record versions. A result body may contain instructions, but those words remain data and cannot change the tool plan.</p>"
    "<h2>Test failure and recovery</h2><p>Create 41 cases: missing receipt, stale policy, conflicting amount, swapped read response, malformed JSON, malicious tool text, timeout before credit receipt, and an already completed credit. Hold back 13 cases for the final check. In the timeout case, restart from a checkpoint that says the action outcome is uncertain. Query the ledger by the existing key; report completion only if the receipt matches tenant, claim, and amount. If no authoritative status is available, stop for review. A parser repair may correct punctuation but must not change the decision or evidence IDs.</p>"
    '<pre><code class="language-text">Goal: assess CL-509 for AC-682.\nReads: current policy and receipt; join by claim and account.\nAction gate: current policy + verified receipt + actor permission.\nEffect key: CREDIT-CL-509-V1; preserve across retries.\nRelease cases: 41 total, 13 held out; zero duplicate or unauthorized credits.\nUncertain effect: reconcile ledger before any retry.</code></pre>'
    "<h2>Performance and operating cost</h2><p>Parallel reads reduce wall time toward the slower read, while the credit and reconciliation stages remain sequential. Running every holdout case through both baseline and candidate increases model calls, but a missed duplicate credit costs more than the extra evaluation. Report wrong tool selection, malformed outputs, skipped dependencies, uncertain effects, duplicate effects, and operator review load separately. A short successful demo is not a release test for these failure paths.</p>"
    "<h3>Common Mistakes</h3><ul><li>Do not retry with a fresh effect key after a timeout.</li><li>Do not treat a checkpoint sentence as a credit receipt.</li><li>Do not allow retrieved text to authorize a write.</li></ul>"
    "<h2>Connected lessons</h2>" + links(project_links)
)
new_rows.append(article(project_path, titles[project_path],
                        "Build and test an assistant that recovers from ambiguous tool effects.",
                        project_body, projects, 25870, project_links, kind="project"))

questions = [
    ("A user asks only for the latest vehicle inspection. Which tool is eligible?", "The inspection read tool", "The maintenance write tool", "Both tools immediately", 0, "The request asks for status, not an external effect."),
    ("A task-creation tool is unavailable to this actor. What should the catalog do?", "Omit it or enforce rejection at the server", "Describe it as read-only", "Let the model decide permission", 0, "The catalog and handler must respect actor scope."),
    ("Address and dimensions are independent reads for one order. What can run together?", "Both reads, with call IDs", "Carrier booking and address read", "Carrier booking before the quote", 0, "The reads have known arguments and no dependency on each other."),
    ("One required read fails before a shipping quote. What happens next?", "Skip the dependent quote and booking", "Use a prior order's value", "Book a carrier with missing dimensions", 0, "A failed prerequisite blocks descendants."),
    ("A JSON repair changes review to approve while fixing a missing brace. What is the result?", "Reject the semantic change", "Accept because parsing succeeds", "Ignore evidence IDs", 0, "Format repair must not silently change a business decision."),
    ("How many repairs should an application attempt?", "A bounded number set by policy", "Until the model agrees", "One per field forever", 0, "A cap prevents unbounded cost and latency."),
    ("A checkpoint says a credit was sent, but the ledger has no receipt. Which state wins?", "The authoritative ledger state", "The checkpoint prose", "The model's confidence", 0, "A summary is not proof of an external effect."),
    ("A policy version changed after a session ended. What must resume do?", "Recheck eligibility under the current version", "Reuse the old verdict without review", "Delete the checkpoint", 0, "Volatile facts need validation on resume."),
    ("A tool result body instructs the assistant to export customers. What is its status?", "Untrusted data, not a governing instruction", "A new system rule", "Permission from the tool server", 0, "Returned text cannot expand task authority."),
    ("A keyword filter misses a hidden instruction in a result title. What still limits harm?", "Narrow capabilities and server-side authorization", "Longer output text", "A lower temperature alone", 0, "The application enforces permissions even if the model is misled."),
    ("A credit call times out. What is the first recovery action?", "Query the authoritative status by the same effect key", "Retry with a new key", "Announce failure as certain", 0, "A timeout leaves the outcome uncertain."),
    ("A receipt has the right key but a different amount. What should happen?", "Block and investigate the mismatch", "Accept the matching key", "Issue a compensating credit immediately", 0, "Identity, target, and amount must agree."),
]
quiz_entry = copy.deepcopy(lookup["quizzes/prompt-engineering-evaluation-labs"])
quiz_entry.update(id=str(uuid.uuid5(uuid.NAMESPACE_URL, "aitrove:" + quiz_path)),
                  path=quiz_path, title=titles[quiz_path],
                  summary="Practice tool choice, dependencies, repair, checkpointing, and effect recovery.",
                  body="<p>Each question asks for a decision at a tool or recovery boundary. Read the case, choose the action, and compare it with the corresponding lesson.</p><h2>Workflow lessons</h2>" + links([spec["path"] for spec in specs]) + "<h2>Practice project</h2>" + links([project_path, patterns, production, quizzes]),
                  sort_order=26080, status="published", published_at=stamp,
                  created_at=stamp, updated_at=stamp)
quiz_entry["data"].update(subject_root=subject_root, section_path=quizzes,
                          content_format="html", author_path="authors/aitrove-editorial",
                          seo_ready=True, duration_minutes=12,
                          related=related([spec["path"] for spec in specs] + [project_path]),
                          questions=[{"prompt": prompt,
                                      "options": ([a, b, c][index % 3:] + [a, b, c][:index % 3]),
                                      "answer": (answer - index) % 3, "explanation": explanation}
                                     for index, (prompt, a, b, c, answer, explanation) in enumerate(questions)])
new_rows.append(quiz_entry)

for hub_path, selected, title, summary in [
    (patterns, [spec["path"] for spec in specs if spec["section"] == patterns],
     "Agent workflow boundaries", "Select tools, schedule dependent calls, repair structure, and resume from verified state."),
    (production, [spec["path"] for spec in specs if spec["section"] == production],
     "Tool result and effect controls", "Contain instructions in tool data and reconcile ambiguous effects."),
    (projects, [project_path], "Tool workflow recovery project", "Test a claims action across ambiguous and adversarial cases."),
    (quizzes, [quiz_path], "Agent workflow quiz", "Apply the boundaries to short operational decisions."),
]:
    hub = lookup[hub_path]
    hub["data"]["modules"].append({"title": title, "summary": summary, "lessons": selected})
    hub["body"] += "<h2>" + html.escape(title) + "</h2><p>" + html.escape(summary) + "</p>" + links(selected + [quiz_path, project_path])
    hub["updated_at"] = stamp

root_hub = lookup[subject_root]
root_hub["body"] += "<h2>Agent workflow decisions</h2><p>These lessons connect tool choice with verification, recovery, and a project that tests ambiguous effects.</p>" + links([spec["path"] for spec in specs] + [project_path, quiz_path])
root_hub["updated_at"] = stamp

backlinks = {
    "prompt-engineering/tool-call-authorization-contract": specs[0]["path"],
    "prompt-engineering/task-decomposition-and-handoffs": specs[1]["path"],
    "prompt-engineering/schema-and-abstention": specs[2]["path"],
    "prompt-engineering/conversation-memory-boundary": specs[3]["path"],
    "prompt-engineering/prompt-injection-red-team": specs[4]["path"],
    "prompt-engineering/tool-loop-stop-rules": specs[5]["path"],
}
for existing_path, new_path in backlinks.items():
    entry = lookup[existing_path]
    entry["body"] += "<p><strong>Continue with:</strong> " + link(new_path) + ".</p>"
    entry["data"]["related"] = related([item["path"] for item in entry["data"]["related"]] + [new_path])
    entry["updated_at"] = stamp

entries.extend(new_rows)
fixture.write_text(json.dumps(entries, ensure_ascii=False, indent=2) + "\n")
print(json.dumps({"newLessons": len(specs), "newProjects": 1, "newQuizzes": 1,
                  "newPaths": [entry["path"] for entry in new_rows]}))
