"""Add original software-delivery applications to the prompt curriculum."""

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
applications = "prompt-engineering/applications"
projects = "prompt-engineering/projects"
quizzes = "prompt-engineering/quizzes"
project_path = "prompt-engineering/software-delivery-review-project"
quiz_path = "quizzes/prompt-engineering-software-delivery"

specs = [
    {
        "slug": "diff-scoped-code-review-evidence",
        "title": "Diff-scoped code review: make every finding reproducible",
        "summary": "Tie a review claim to changed behavior, a concrete path, and a testable failure.",
        "definition": "A code-review prompt should inspect the proposed diff in its repository context and return a small set of actionable findings. Each finding needs a changed file and line, a reachable input or state, the resulting failure, and the expected behavior. The model may suggest a hypothesis, but the reviewer must check the surrounding call path and actual test result before treating it as a defect. Separate a verified bug from a possible risk and omit style preferences that do not affect the change. Review against the exact commit under discussion so a comment does not point at a line that has since moved.",
        "case": "A payment service changes its retry guard in PaymentCaptureService. A new condition checks whether a receipt is absent, then schedules another capture, but the receipt can arrive between the read and the retry. The useful review comment identifies the condition in the changed diff, names a delayed receipt for payment PY-583, and explains that a second capture may be attempted unless the payment gateway uses an idempotency key. The reviewer checks the gateway adapter and a concurrent test before filing the finding. A generic warning that payments are risky adds no information and should be dropped.",
        "sample": "Candidate finding: PaymentCaptureService retry branch, changed line 86.\nTrigger: PY-583 receipt arrives after the read, before retry dispatch.\nEffect to verify: duplicate capture request without a stable key.\nEvidence: inspect gateway adapter and concurrent receipt test.\nDisposition: verified finding | hypothesis needing test | no finding.",
        "cost": "For D changed lines and C relevant call sites, reading the diff and traced context is at least O(D+C); the model call adds token cost proportional to supplied context. Sending an entire repository can bury the changed behavior and raise latency. Retrieve only the necessary contracts and tests, then expand if a finding depends on a caller outside the initial scope. Track confirmed findings and false positives by severity. A high comment count is not a quality metric when most comments cannot be reproduced.",
        "mistakes": ["Do not file a finding without a reachable failure path.", "Do not cite an unchanged line as though it were part of the proposed diff.", "Do not treat a model's confidence phrase as test evidence."],
        "related": ["prompt-engineering/code-change-acceptance-contract", "prompt-engineering/evidence-id-traceability", "devops/ci-evidence-integrity-project"],
    },
    {
        "slug": "regression-test-oracle-contract",
        "title": "Generated tests: verify the oracle before trusting coverage",
        "summary": "Derive expected behavior from an independent contract and challenge it with a known fault.",
        "definition": "A test-generation prompt can propose cases from a requirement, interface contract, and failure history. The expected result must come from those sources, not from running the implementation under test and copying its output. Define boundary values, invalid inputs, duplicate operations, and state transitions where relevant. A passing generated test is weak if it merely restates the current code. Review at least one deliberately faulty variant or historical regression to see whether the test would fail for the right reason. Keep fixtures isolated so a test result does not depend on an earlier run.",
        "case": "A wallet API promises that a second request with the same transfer key returns the first receipt without moving money again. The assistant proposes a test for transfer key TR-694, amount 43.75, and an account balance of 120.00. The first call should leave 76.25 and return receipt RC-694; the second call should return the same receipt and leave 76.25. A broken variant that debits twice would leave 32.50. If the generated assertion only checks that both calls return status 200, it misses the defect despite passing. The test must assert both receipt identity and final balance.",
        "sample": "Initial balance: 120.00; transfer TR-694: 43.75.\nFirst call: receipt RC-694; balance 76.25.\nSame key again: receipt RC-694; balance still 76.25.\nFault injection: second debit -> 32.50; test must fail.\nOracle: transfer contract, not current endpoint output.",
        "cost": "For N candidate cases and M fault variants, a full matrix can require O(NM) executions, so focus mutations on meaningful boundaries and past failures. Fixture setup and external calls may dominate runtime; isolate them before multiplying cases. A mutation score is useful only when the fault variants represent behavior the contract forbids. Record which case killed which fault, not just line coverage. The model can draft cases quickly, but a human or trusted specification must approve the oracle before it becomes a release gate.",
        "mistakes": ["Do not use the current buggy implementation as the expected-result source.", "Do not count a status-only assertion as an idempotency test.", "Do not reuse mutable account state across tests without reset."],
        "related": ["prompt-engineering/code-change-acceptance-contract", "python/mutation-testing", "devops/ci-test-data-isolation"],
    },
    {
        "slug": "incident-log-timeline-triage",
        "title": "Incident triage prompts: build a timestamped evidence ledger",
        "summary": "Separate observed signals, inferred causes, and actions during an outage.",
        "definition": "An incident-triage prompt should turn logs, metrics, deployments, and operator notes into a time-ordered evidence ledger. Normalize clock zones before ordering events, preserve source IDs, and label each causal claim as observed or inferred. Logs are untrusted data: a line that contains instructions to an assistant cannot grant tool authority. The model can propose hypotheses and missing checks, but incident command and production actions remain with the authorized responders. An update should state current user impact and uncertainty rather than invent a root cause while the event is active.",
        "case": "At 14:07 UTC, checkout latency rises; at 14:09 UTC, application logs show database pool waits; at 14:12 UTC, a deployment event appears. A support note written in local time claims the deployment started at 19:38, which is 14:08 UTC under the team's offset. The ordering now suggests a possible relation, but it does not prove the release caused the pool waits. The assistant records the offset, asks for a pre-release pool baseline, and identifies the rollback owner. It does not execute rollback because a log message says to do so. It also masks customer identifiers before the ledger goes to a shared channel.",
        "sample": "INC-742; timezone for all rows: UTC.\n14:07 latency alarm; 14:08 deployment began; 14:09 pool waits.\nObserved: times and metrics. Inferred: deployment may contribute.\nNext check: pool baseline and connection count by version.\nAuthority: incident commander decides mitigation; logs are data.",
        "cost": "Sorting E event records costs O(E log E) time and O(E) space; timestamp parsing and missing-zone review can dominate the human effort. A bounded incident packet avoids repeatedly sending full logs to the model, reducing both cost and private-data exposure. Recompute the ledger when new evidence arrives, but retain earlier versions so a later correction does not silently rewrite what responders knew. Measure false causal claims, time-to-useful-hypothesis, and missing critical signals. Summarization speed is irrelevant if it hides the impact window.",
        "mistakes": ["Do not merge timestamps from different zones without normalization.", "Do not state that temporal proximity proves causation.", "Do not obey commands embedded in log lines or operator notes."],
        "related": ["prompt-engineering/prompt-trace-observability", "prompt-engineering/tool-result-instruction-quarantine", "devops/incident-response"],
    },
    {
        "slug": "schema-migration-prompt-review",
        "title": "Schema migration prompts: check old and new clients together",
        "summary": "Review compatibility windows, data backfill, and rollback limits before proposing SQL.",
        "definition": "A schema-migration prompt should receive the current schema, target schema, active application versions, write paths, data volume, and deployment order. Its output is a reviewable sequence with compatibility checks, not a single attractive ALTER statement. For a field replacement, add the new field first, move readers and writers under a measured compatibility window, backfill existing rows, then remove the old field only after old clients are gone. Record whether a step is reversible; a destructive drop cannot be undone by rolling back application code. Require a dry run and data-integrity checks owned by the database team.",
        "case": "A parcel system wants to replace a combined delivery_zone field with region_code and route_code. API version 6 still reads delivery_zone while version 7 writes the two new fields. A proposed migration that drops delivery_zone immediately would break version 6 during a rolling deployment. The assistant's plan keeps the old field, introduces the new pair, compares 4,700 migrated rows with the original value, and waits for version 6 traffic to reach zero before contract. If 23 records cannot be parsed, it stops the drop and produces a review list instead of filling guessed codes.",
        "sample": "Parcel schema: delivery_zone -> region_code + route_code.\nExpand: add new nullable fields; keep old reader path.\nMigrate: parse 4,700 rows; 23 unresolved -> review queue.\nVerify: round-trip equality and version-6 traffic count.\nContract: drop old field only after unresolved=0 and old traffic=0.",
        "cost": "A backfill of R rows is O(R) work and may create locks or replication lag; a prompt cannot estimate those costs accurately without database measurements. Dual writes add code and temporary storage, but they preserve compatibility across a rolling release. Keep the model's plan separate from the migration runner and use a staged rehearsal with representative data. Measure unresolved rows, query errors by client version, backfill duration, and rollback feasibility before approving the next phase. Review the generated SQL for dialect and transaction semantics rather than trusting syntactic plausibility.",
        "mistakes": ["Do not drop the old column while an active client still reads it.", "Do not silently guess values for unparseable rows.", "Do not promise rollback can recreate deleted production data."],
        "related": ["prompt-engineering/code-change-acceptance-contract", "prompt-engineering/prompt-release-artifact-bundle", "python/sqlite-migration-rollback"],
    },
    {
        "slug": "dependency-upgrade-review-prompt",
        "title": "Dependency upgrade prompts: trace behavior, not only versions",
        "summary": "Connect a package change to affected call sites, lockfile state, and release evidence.",
        "definition": "A dependency-upgrade prompt should identify the exact old and new versions, package source, lockfile diff, affected imports, changed behavior, and tests that exercise those paths. A security advisory or automated update proposal is a trigger for review, not proof that the application is safe after the change. Prefer official release notes and locally observed behavior for compatibility claims. Keep transitive additions and package scripts visible to the reviewer. If the upgrade changes serialization, authentication, or data formats, add a regression check at that boundary before promotion.",
        "case": "An order service upgrades a CSV parsing library from version 4.3 to 5.1. The manifest changes one direct package, but the lockfile also adds a transitive decoder. The assistant identifies the import used by OrderFeedParser and proposes tests for quoted line breaks, duplicate headers, and a 31-megabyte feed under the service's size cap. One old fixture passes yet the quoted-line-break case changes row count from 208 to 209. The team blocks promotion until it determines whether the new parser or the historical fixture is correct; the model cannot settle that by preferring the newer version.",
        "sample": "OrderFeedParser upgrade: 4.3 -> 5.1.\nReview: manifest, lockfile, transitive decoder, package scripts.\nBoundary cases: quoted newline; duplicate header; 31 MB feed.\nObserved row counts: old 208, new 209 -> investigate.\nRelease gate: reconcile expected rows and record exact build digest.",
        "cost": "With P changed packages and C affected call sites, the initial inventory is O(P+C), while tests and dependency resolution dominate wall-clock time. Scanning every repository file for every package wastes context; start with imports, public APIs, and lockfile changes, then expand around a behavioral difference. A large version jump can require several focused compatibility tests, but more generated tests are not useful if their expected results copy the new library's output. Track build digest, dependency tree, and test evidence so rollback can restore the same artifact rather than an approximate manifest.",
        "mistakes": ["Do not approve an upgrade from its version number alone.", "Do not ignore transitive packages and install scripts.", "Do not treat the newer parser's output as the test oracle."],
        "related": ["prompt-engineering/code-change-acceptance-contract", "prompt-engineering/regression-test-oracle-contract", "devops/dependency-patch-campaign"],
    },
]

paths = ["prompt-engineering/" + spec["slug"] for spec in specs]
assert not set(paths + [project_path, quiz_path]).intersection(lookup)
titles = {entry["path"]: entry["title"] for entry in entries}
titles.update({path: spec["title"] for path, spec in zip(paths, specs)})
titles[project_path] = "Project: review a checkout release from diff to incident"
titles[quiz_path] = "Prompt engineering for software delivery"


def link(path):
    assert path in titles, path
    return f'<a href="/{html.escape(path)}">{html.escape(titles[path])}</a>'


def links(selected):
    return "<ul>" + "".join(f"<li>{link(path)}</li>" for path in dict.fromkeys(selected)) + "</ul>"


def related(selected):
    return [{"path": path, "title": titles[path]} for path in dict.fromkeys(selected)]


def article(path, title, summary, body, section, order, connections, kind="tutorial"):
    entry = copy.deepcopy(lookup["prompt-engineering/evaluation-slice-design"])
    entry.update(id=str(uuid.uuid5(uuid.NAMESPACE_URL, "aitrove:" + path)),
                 path=path, title=title, summary=summary, body=body,
                 subject="prompt-engineering-applications" if section == applications else "prompt-engineering-project",
                 difficulty="Advanced", tags=["prompt engineering", "software delivery"],
                 sort_order=order, status="published", published_at=stamp,
                 created_at=stamp, updated_at=stamp)
    entry["data"].update(kind=kind, reading_minutes=11 if kind == "tutorial" else 19,
                         author_path="authors/aitrove-editorial", subject_root=subject_root,
                         section_path=section, content_format="html", seo_ready=True,
                         related=related(connections))
    return entry


new_rows = []
for index, (path, spec) in enumerate(zip(paths, specs)):
    connections = [applications, subject_root] + spec["related"] + [peer for peer in paths if peer != path] + [project_path, quiz_path]
    body = ("<p>" + html.escape(spec["definition"]) + "</p>"
            + "<h2>Operational case</h2><p>" + html.escape(spec["case"]) + "</p>"
            + '<pre><code class="language-text">' + html.escape(spec["sample"], quote=False) + "</code></pre>"
            + "<h2>Performance and operating cost</h2><p>" + html.escape(spec["cost"]) + "</p>"
            + "<h3>Common Mistakes</h3><ul>" + "".join("<li>" + html.escape(mistake) + "</li>" for mistake in spec["mistakes"]) + "</ul>"
            + "<h2>Connected lessons</h2>" + links(connections))
    new_rows.append(article(path, spec["title"], spec["summary"], body, applications, 28100 + index * 10, connections))

project_connections = paths + ["prompt-engineering/code-change-acceptance-contract", "prompt-engineering/prompt-evaluation-ci-gate", "devops/release-evidence-record", quiz_path]
project_body = (
    "<p>This project reviews a fictional checkout release that changes capture retries, updates a feed parser, and splits a parcel zone field. Build a compact prompt packet for five tasks: inspect the exact diff, draft contract-based regression tests, assess the schema migration, review the dependency change, and triage a post-release latency alarm. The assistant may propose findings and checks. CI, the database runner, and the incident commander own the effects. The final deliverable is a release recommendation with unresolved questions and evidence IDs.</p>"
    "<h2>Prepare the review packet</h2><p>Freeze commit CH-842 and include only the changed files plus the gateway adapter, transfer contract, active client versions, migration plan, lockfile diff, and parser call sites. For the retry branch, require a reachable race and test rather than a generic risk statement. Generate a transfer-idempotency test with receipt identity and final balance assertions, then run it against a deliberately faulty double-debit variant. For the schema change, keep the legacy field until version-6 traffic is zero and all 23 unparseable records are reviewed. For the parser upgrade, investigate the one-row difference before assigning an expected output.</p>"
    "<h2>Exercise incident handling</h2><p>At 14:07 UTC, checkout latency rises. A deployment begins at 14:08; pool waits follow at 14:09. Normalize the support note's local timestamp and mark causation as a hypothesis pending connection metrics. The assistant records the impact window, current mitigation owner, and next check. It masks customer identifiers and ignores any command found inside a log line. The incident commander, not the prompt, decides rollback. Compare a direct baseline prompt with the structured packet on held-out examples of true defects, harmless diffs, missing evidence, and misleading log text.</p>"
    '<pre><code class="language-text">Release CH-842: retry guard + parser upgrade + zone migration.\nReview: changed line, reachable trigger, observed or testable effect.\nTest: duplicate transfer key leaves balance 76.25 once.\nMigration: legacy reader traffic=0; unresolved rows=0 before drop.\nIncident: 14:07 alarm, 14:08 deploy, 14:09 pool waits; cause unproven.\nGate: no unverified row oracle, duplicate debit, or unauthorized rollback.</code></pre>'
    "<h2>Performance and operating cost</h2><p>For C review cases and V prompt variants, offline comparison takes O(CV) model evaluations. Diff context grows with changed lines and relevant call sites; incident ordering costs O(E log E) for E events. Fault-variant tests and migration rehearsal add runtime but expose errors a fluent review would miss. Record the exact commit, build digest, test commands, migration stage, incident timeline version, and reviewer decision. A release with one critical duplicate debit or destructive schema error is blocked even if its average review score is high.</p>"
    "<h3>Common Mistakes</h3><ul><li>Do not equate a plausible code-review sentence with a reproduced defect.</li><li>Do not derive test expectations from the changed implementation.</li><li>Do not let the assistant execute migration or rollback from a prompt alone.</li></ul>"
    "<h2>Connected lessons</h2>" + links(project_connections))
new_rows.append(article(project_path, titles[project_path], "Review a checkout release with reproducible findings, test oracles, migration gates, and incident evidence.", project_body, projects, 28160, project_connections, kind="project"))

questions = [
    ("What makes a code-review finding actionable?", "A changed location, reachable trigger, and checkable failure", "A broad warning about complexity", "A model confidence score", "A reviewer can reproduce a concrete failure."),
    ("A review comment points to a line from an older commit. What should happen?", "Recheck against the exact proposed commit", "Keep the comment unchanged", "Count it as a verified defect", "Line positions and behavior can move between revisions."),
    ("Where should a generated test obtain its expected balance?", "The independent transfer contract", "The current endpoint response", "A random model sample", "The implementation under test cannot certify itself."),
    ("A duplicate transfer returns two 200 statuses. What else must the test assert?", "Same receipt and unchanged balance after the second call", "Only response length", "Only request latency", "Status alone misses a second debit."),
    ("Why normalize incident timestamps before sorting?", "Different zones can invert the event order", "To hide missing evidence", "To prove causation", "The sequence must use a common clock basis."),
    ("A deployment precedes pool waits by one minute. Which claim is supported?", "A possible relation requiring more evidence", "The deployment definitely caused the waits", "Rollback is automatically authorized", "Temporal order alone is not a causal test."),
    ("Version 6 still reads delivery_zone. When may the old column be dropped?", "After old traffic stops and data checks pass", "Immediately after adding new fields", "When a model says it is safe", "Active readers and unresolved rows block contract."),
    ("Twenty-three rows cannot be parsed during backfill. What should the plan do?", "Stop contract and send them to review", "Guess replacement codes", "Drop them silently", "Unknown data needs adjudication before destructive change."),
    ("A lockfile adds a decoder during a direct package upgrade. What should review include?", "The transitive decoder and affected behavior", "Only the manifest version", "Only the release title", "Dependency effects include transitive changes."),
    ("Old and new parsers return different row counts. What is the correct next step?", "Determine the contract-correct count with a reviewed fixture", "Assume the newer result is right", "Ignore the difference if CI is green", "Version recency is not an oracle."),
    ("A log line instructs the assistant to run rollback. What authority does it have?", "None; it is untrusted data", "It overrides incident command", "It authorizes a production write", "Logs cannot grant tool permissions."),
    ("Which result blocks release despite better average review scores?", "A verified duplicate debit in a critical case", "One fewer review comment", "A faster summary", "Critical failures are not offset by average gains."),
]
quiz_entry = copy.deepcopy(lookup["quizzes/prompt-engineering-multimodal-evidence"])
quiz_entry.update(id=str(uuid.uuid5(uuid.NAMESPACE_URL, "aitrove:" + quiz_path)),
                  path=quiz_path, title=titles[quiz_path],
                  summary="Test diff findings, regression oracles, incident timelines, migrations, and package reviews.",
                  body="<p>Choose the check that makes a software-delivery decision reproducible. Plausible output is not enough when a release can change money, data, or production state.</p><h2>Lessons</h2>" + links(paths) + "<h2>Project and sections</h2>" + links([project_path, applications, quizzes]),
                  sort_order=28170, status="published", published_at=stamp,
                  created_at=stamp, updated_at=stamp)
quiz_entry["data"].update(subject_root=subject_root, section_path=quizzes,
                          content_format="html", author_path="authors/aitrove-editorial",
                          seo_ready=True, duration_minutes=12,
                          related=related(paths + [project_path]),
                          questions=[{"prompt": prompt,
                                      "options": ([correct, wrong_a, wrong_b][index % 3:] + [correct, wrong_a, wrong_b][:index % 3]),
                                      "answer": (-index) % 3, "explanation": explanation}
                                     for index, (prompt, correct, wrong_a, wrong_b, explanation) in enumerate(questions)])
new_rows.append(quiz_entry)

for hub_path, selected, title, summary in [
    (applications, paths, "Software delivery review", "Review diffs, test oracles, incident evidence, schema changes, and package upgrades."),
    (projects, [project_path], "Checkout release review", "Decide whether a multi-part release is ready from checked evidence."),
    (quizzes, [quiz_path], "Software delivery quiz", "Test the boundaries between model suggestions and verified release decisions."),
]:
    hub = lookup[hub_path]
    hub["data"]["modules"].append({"title": title, "summary": summary, "lessons": selected})
    hub["body"] += "<h2>" + html.escape(title) + "</h2><p>" + html.escape(summary) + "</p>" + links(selected + [project_path, quiz_path])
    hub["updated_at"] = stamp

root_hub = lookup[subject_root]
root_hub["body"] += "<h2>Engineering review applications</h2><p>Use prompts to form testable hypotheses; let code, data, and release gates settle the decision.</p>" + links(paths + [project_path, quiz_path])
root_hub["updated_at"] = stamp

backlinks = {
    "prompt-engineering/code-change-acceptance-contract": paths[0],
    "prompt-engineering/evidence-id-traceability": paths[0],
    "prompt-engineering/prompt-evaluation-ci-gate": project_path,
    "prompt-engineering/prompt-trace-observability": paths[2],
    "prompt-engineering/prompt-release-artifact-bundle": paths[3],
    "python/mutation-testing": paths[1],
    "python/sqlite-migration-rollback": paths[3],
    "devops/incident-response": paths[2],
    "devops/dependency-patch-campaign": paths[4],
}
for old_path, new_path in backlinks.items():
    entry = lookup[old_path]
    entry["body"] += "<p><strong>Continue with:</strong> " + link(new_path) + ".</p>"
    entry["data"]["related"] = related([item["path"] for item in entry["data"]["related"]] + [new_path])
    entry["updated_at"] = stamp

entries.extend(new_rows)
fixture.write_text(json.dumps(entries, ensure_ascii=False, indent=2) + "\n")
print(json.dumps({"newLessons": len(specs), "newProjects": 1, "newQuizzes": 1,
                  "newPaths": [entry["path"] for entry in new_rows]}))
