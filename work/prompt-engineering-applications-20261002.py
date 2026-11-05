"""Add original applied Prompt Engineering lessons and interlinked practice."""

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
root_path = "prompt-engineering/prompt-engineering"
patterns = "prompt-engineering/patterns"
applications = "prompt-engineering/applications"
production = "prompt-engineering/production"
projects = "prompt-engineering/projects"
quizzes = "prompt-engineering/quizzes"
project_path = "prompt-engineering/multimodal-incident-brief-project"
quiz_path = "quizzes/prompt-engineering-applied-decisions"


def lesson(slug, title, summary, definition, case, sample, cost, mistakes, related):
    return dict(path="prompt-engineering/" + slug, title=title, summary=summary,
                definition=definition, case=case, sample=sample, cost=cost,
                mistakes=mistakes, related=related)


specs = [
    lesson(
        "code-change-acceptance-contract",
        "Coding prompts: name the files, behavior, and proof",
        "A coding assistant needs a bounded change and an executable acceptance check.",
        "A code-change prompt should identify the repository area, trigger, expected behavior, compatibility constraint, and tests that would prove the change. Ask the assistant to inspect relevant code before editing; do not paste secrets or an entire repository when a few files suffice. Separate the desired behavior from an implementation guess so the assistant can follow existing patterns. Review the diff, run meaningful tests, and inspect errors from the actual runtime. A successful generated patch is a candidate until those checks pass.",
        "A dispatch service sometimes assigns the same shipment twice after a retry. The task is to make assignment idempotent for shipment SH-286 without changing the public response shape. The prompt points to the assignment handler and the persistence adapter, names the duplicate-retry trigger, and asks for a test that sends the same effect key twice. The reviewer checks that one database effect occurs and that the second request returns the stored result. If the assistant proposes a new queue library, the team requires evidence that the existing adapter cannot enforce the invariant.",
        "Task: duplicate assignment retry for shipment SH-286.\nScope: assignment handler and persistence adapter.\nInvariant: one effect per stable idempotency key.\nPass: repeated request returns one assignment; existing API shape unchanged.\nProof: focused test plus full relevant suite.",
        "Repository inspection, edit generation, and tests cost more than a single chat response. Test runtime depends on the project, while diff review scales with changed lines and affected behavior. Keep the prompt narrow enough to avoid unrelated edits but include the interface contract and failure trigger. Track test failures separately from tool execution failures. A model can suggest a test that only mirrors its implementation; require a behavior-level case that would fail before the fix.",
        ["Do not accept a patch because it compiles without testing the trigger.", "Do not include secrets in repository context.", "Do not broaden a small fix into an unrequested architecture rewrite."],
        ["prompt-engineering/intent-to-acceptance-check", "prompt-engineering/metamorphic-prompt-tests"],
    ),
    lesson(
        "read-only-sql-generation-gate",
        "SQL prompts: generate a query under database-enforced limits",
        "A prompt can ask for a query, but database permissions decide what can run.",
        "Text-to-SQL needs a schema slice, business meaning for columns, permitted tables, and an expected result shape. The generated statement must be parsed or inspected before execution and run through a read-only connection with narrowly scoped grants, statement timeout, and row limit. Do not rely on a model's claim that its SQL is safe. Parameterize user values and keep identifiers on an allowlist. Review joins and aggregation for business correctness; a syntactically valid query can count the wrong events or leak rows from another tenant.",
        "An analyst asks for failed settlement batches for account AC-713 during a seven-day window. The assistant receives only the settlement_batch schema and a definition of failed state. It returns a read query with a bound account ID and two date parameters. The executor rejects a query that names a customer_profile table or lacks tenant filtering. A test dataset includes a batch from a different account with the same status, so an omitted account predicate is detected. The result is capped before display and no write grant exists on the database role.",
        "Allowed tables: settlement_batch.\nRequired filters: tenant_id, state=failed, created_at window.\nParameters: account_id, start_time, end_time.\nExecutor: read-only role, timeout, row cap; reject other tables.\nPass: no cross-account rows in test result.",
        "Parsing and permission checks add overhead but are small compared with a full-table scan caused by a poor query. A row cap protects the client but does not necessarily reduce database work if filtering or indexing is weak. Inspect the query plan for large datasets and bound the time window. Count rejected statements and wrong-result cases separately. Database permissions and tenant predicates are hard boundaries; prompt wording improves candidate quality but cannot replace either one.",
        ["Do not execute generated SQL with an administrator role.", "Do not interpolate customer values into a query string.", "Do not assume valid SQL returns the correct business result."],
        ["prompt-engineering/output-sink-validation", "prompt-engineering/tool-call-authorization-contract"],
    ),
    lesson(
        "image-generation-brief-and-review",
        "Image prompts: specify the visual contract and inspect the pixels",
        "An image prompt can describe intent, but only the rendered image shows whether it was met.",
        "A production image brief names the subject, composition, intended placement, required and forbidden elements, aspect ratio, and any exact text that must be checked later. Describe constraints that matter to the asset rather than stacking style adjectives. If editing an existing image, identify which parts must remain stable and which may change. Generated pixels require visual review for text accuracy, identity, accessibility, and unintended content. Do not treat a model's textual assurance that the image is correct as proof.",
        "A logistics dashboard needs a hero image for a tablet-width layout. The brief asks for a warehouse sorter on the left, a clear quiet area on the right for interface text, neutral lighting, and no visible company marks. The team generates three candidates, then checks the actual crop at 16:9 and a narrow mobile crop. One candidate places a pallet in the supposed quiet area; another invents a badge with unreadable lettering. Both fail despite satisfying most of the written brief. The accepted image is stored with its prompt version and review notes.",
        "Asset: warehouse dashboard hero.\nComposition: sorter left, right third visually quiet.\nFormat: 16:9 source; verify mobile crop.\nExclude: logos, badges, embedded copy.\nReview: subject placement, crop, legibility, unintended marks.",
        "Generating multiple candidates increases model cost and review time roughly with candidate count. Large output dimensions add processing and storage cost; resizing a small image does not recover missing detail. A fixed acceptance checklist makes the review faster than repeated subjective revisions. Keep exact copy in the interface when possible rather than trusting image-rendered letters. Store the accepted asset and its dimensions so later page changes can be checked against the crop and loading budget.",
        ["Do not accept an image from its prompt alone.", "Do not depend on generated lettering for critical copy.", "Do not ignore the final responsive crop."],
        ["prompt-engineering/multimodal-evidence-boundary", "prompt-engineering/evaluation-slice-design"],
    ),
    lesson(
        "audio-transcription-uncertainty",
        "Audio prompts: preserve speakers, timestamps, and uncertain words",
        "A transcript is an interpretation of a recording, not a perfect copy.",
        "An audio prompt should state whether the job is verbatim transcription, cleaned transcript, translation, or summary. These outputs have different evidence needs. Ask for speaker labels and timestamps only when the audio and tool support them, and allow an uncertain span rather than forcing a plausible word. Keep the original recording and segment IDs for review. A summary must not turn a tentative spoken statement into a confirmed decision. If a name, amount, or instruction drives an external action, verify it with the speaker or another record.",
        "A field dispatcher receives a six-minute call about a damaged valve. The assistant transcribes speakers A and B and marks the serial number after minute three as uncertain because of engine noise. It then drafts a maintenance handoff stating that a pressure reading of 47 units was reported by speaker B, not measured by the system. A reviewer listens to the flagged span before attaching a device ID. The assistant does not create a work order from the uncertain serial. A second recording with overlapping speech tests whether the speaker labels remain trustworthy.",
        "Mode: verbatim transcript first; summary second.\nSegments: timestamp, speaker, words, uncertainty flag.\nCritical field: device serial -> verify from audio or asset record.\nHandoff: reported pressure, observed uncertainty, next check.",
        "Audio processing cost grows with duration and the number of reviewable segments. A full transcript may consume more storage and reading time than a targeted extraction, but it preserves context for disputed claims. Measure field-level accuracy for names, amounts, and device IDs, not only word-level agreement. Overlapping speech and noise can increase human review. Do not compress away uncertainty in the summary merely to make it shorter.",
        ["Do not invent a speaker when voices overlap.", "Do not turn an uncertain serial into a confirmed asset ID.", "Do not label a cleaned summary as a verbatim transcript."],
        ["prompt-engineering/multimodal-evidence-boundary", "prompt-engineering/human-review-escalation"],
    ),
    lesson(
        "video-timecode-evidence",
        "Video prompts: cite the moment and the observation",
        "A video summary needs time-bounded evidence, especially for brief events.",
        "Video analysis should identify the clip, time span, observed action, and confidence limits. Sampling can miss a fast event, while a single frame can hide what happened just before or after. Ask for timecodes and distinguish visible behavior from an inferred cause. If the result will affect safety, billing, or an incident record, review the original clip around the cited time and compare it with any sensor or witness evidence. A generated summary must not be treated as a continuous record of frames it did not inspect.",
        "A depot camera clip shows a loading bay from 14:00 to 14:07. The assistant notes that a gate appears open near 14:03 and that a forklift enters the frame shortly afterward. It cannot tell whether the gate sensor failed, because no sensor feed was supplied. A reviewer scrubs the source clip around 14:03 and checks the access log. A two-second movement near the frame edge is labeled uncertain rather than omitted or described as a collision. The final incident note cites clip ID, time range, and the separate access-log ID.",
        "Clip: BAY-22, 14:00–14:07.\nObserved: gate appears open near 14:03; forklift enters frame.\nUnknown: sensor state and cause.\nVerify: replay source around cited time; compare access log.\nOutput: clip ID and time range for each claim.",
        "Long clips and high-resolution frames raise processing time and cost. Lower sampling can be economical but may miss short actions, so test with known brief events before using it for incident decisions. Human review time can be reduced by cited ranges, but the reviewer needs enough lead-in and aftermath to interpret an action. Measure timecode error and missed-event rate by event duration. Do not infer a cause from visual sequence alone when the causal sensor is absent.",
        ["Do not present sampled frames as an exhaustive timeline.", "Do not omit timecodes for a disputed observation.", "Do not infer a sensor failure from an image of an open gate."],
        ["prompt-engineering/multimodal-evidence-boundary", "prompt-engineering/evidence-id-traceability"],
    ),
    lesson(
        "time-sensitive-research-contract",
        "Research prompts: bind claims to a date and evidence record",
        "A current-sounding answer needs current evidence, not confident wording.",
        "A research prompt should state the question, relevant date or time window, acceptable evidence, and the distinction between observed facts and inference. Retrieve material from authorized sources, record each item's date and identifier, and verify that the claim is supported by the item actually read. If the available evidence predates the event or two records conflict, report the gap. A model's memory cannot establish a current price, rule, or deployment status. The application should preserve a review trail without assuming that every retrieved page remains unchanged.",
        "An operations analyst asks whether a service-credit rule changed after an August release. The assistant inspects the approved policy versions and a release record, then reports the effective rule and date with internal evidence IDs. A meeting note says the change was planned, but the approved policy has no new version; the assistant does not describe the plan as active. If the policy store is unavailable, it states that current status is unverified. The reviewer can open the cited record, inspect its effective date, and see which parts of the answer are inference.",
        "Question: rule active on 2026-09-18?\nEvidence: approved policy version + effective date; release record.\nExclude: unapproved meeting plan as proof of activation.\nOutput: verified status, evidence IDs, unresolved conflict.\nIf current store unavailable: status unverified.",
        "Retrieval adds calls and review work, but it prevents stale model memory from posing as a current fact. For M candidate records, metadata filtering is O(M) before detailed reading. Limit the search by date and system of record, then broaden only when the evidence is insufficient. Measure unsupported claims and stale-record errors separately. A cached result needs an expiry tied to the source's update pattern; otherwise a fast answer can be systematically wrong after a policy change.",
        ["Do not treat a planned change as an active rule.", "Do not answer a date-sensitive question from model memory alone.", "Do not hide a conflict between records under a single confident sentence."],
        ["prompt-engineering/retrieval-freshness-and-conflict", "prompt-engineering/evidence-id-traceability"],
    ),
]

titles = {entry["path"]: entry["title"] for entry in entries}
titles.update({spec["path"]: spec["title"] for spec in specs})
titles.update({
    applications: "Prompt engineering applications",
    project_path: "Project: produce a checked multimodal incident brief",
    quiz_path: "Applied prompt engineering decisions",
})
new_paths = {applications, project_path, quiz_path} | {spec["path"] for spec in specs}
assert not new_paths.intersection(lookup), "new route already exists"


def link(path):
    assert path in titles, path
    return f'<a href="/{html.escape(path)}">{html.escape(titles[path])}</a>'


def link_list(paths):
    return "<ul>" + "".join(f"<li>{link(path)}</li>" for path in dict.fromkeys(paths)) + "</ul>"


def related(paths):
    return [{"path": path, "title": titles[path]} for path in dict.fromkeys(paths)]


def new_article(template, *, path, title, summary, body, section, subject, kind, order, connections):
    entry = copy.deepcopy(template)
    entry.update(id=str(uuid.uuid5(uuid.NAMESPACE_URL, "aitrove:" + path)),
                 path=path, title=title, summary=summary, body=body,
                 category="AI & Data", subject=subject, difficulty="Advanced",
                 tags=["prompt engineering", kind], sort_order=order,
                 status="published", published_at=stamp, created_at=stamp, updated_at=stamp)
    entry["data"].update(kind=kind, reading_minutes=10 if kind == "tutorial" else 15,
                         author_path="authors/aitrove-editorial", subject_root=root_path,
                         section_path=section, content_format="html", seo_ready=True,
                         related=related(connections))
    return entry


tabs = [
    {"title": "Prompt Engineering", "path": root_path},
    {"title": "Patterns", "path": patterns},
    {"title": "Applications", "path": applications},
    {"title": "Production", "path": production},
    {"title": "Projects", "path": projects},
    {"title": "Quizzes", "path": quizzes},
]
for path in [root_path, patterns, production, projects, quizzes]:
    lookup[path]["data"]["resource_tabs"] = tabs
    lookup[path]["updated_at"] = stamp

app_hub = copy.deepcopy(lookup[root_path])
app_hub.update(id=str(uuid.uuid5(uuid.NAMESPACE_URL, "aitrove:" + applications)),
               path=applications, title=titles[applications],
               summary="Apply prompt contracts to code, data, images, audio, video, and current research.",
               subject="prompt-engineering-applications", sort_order=31,
               published_at=stamp, created_at=stamp, updated_at=stamp)
app_hub["data"] = {
    "subject_root": root_path, "section_path": applications,
    "content_format": "html", "seo_ready": True, "resource_tabs": tabs,
    "modules": [{
        "title": "Applied prompt contracts",
        "summary": "Use the right checks for the output's destination and evidence type.",
        "lessons": [spec["path"] for spec in specs],
    }],
}
app_hub["body"] = (
    "<p>Application prompts need more than an output format. Code, database queries, generated images, recordings, video, and current research each have a different proof boundary. Select the workflow you need, then inspect its result before use.</p>"
    "<h2>Applied lessons</h2>" + link_list([spec["path"] for spec in specs])
    + "<h2>Practice and review</h2>" + link_list([
        project_path, quiz_path, root_path, patterns, production,
    ])
)

new_rows = [app_hub]
for index, spec in enumerate(specs):
    neighbors = []
    if index > 0:
        neighbors.append(specs[index - 1]["path"])
    if index + 1 < len(specs):
        neighbors.append(specs[index + 1]["path"])
    connections = list(dict.fromkeys(
        [applications, root_path] + spec["related"] + neighbors
        + [project_path, quiz_path]
    ))
    body = (
        f"<p>{html.escape(spec['definition'])}</p>"
        f"<h2>Decision in practice</h2><p>{html.escape(spec['case'])}</p>"
        f'<pre><code class="language-text">{html.escape(spec["sample"])}</code></pre>'
        f"<h2>Performance and operating cost</h2><p>{html.escape(spec['cost'])}</p>"
        "<h3>Common Mistakes</h3><ul>"
        + "".join(f"<li>{html.escape(item)}</li>" for item in spec["mistakes"])
        + "</ul><h2>Connected lessons</h2>" + link_list(connections)
    )
    new_rows.append(new_article(
        lookup["prompt-engineering/task-contract"],
        path=spec["path"], title=spec["title"], summary=spec["summary"],
        body=body, section=applications, subject="prompt-engineering-applications",
        kind="tutorial", order=26000 + index, connections=connections[:8],
    ))

project_body = (
    "<p>This project assembles a checked incident brief from a six-minute dispatcher call and a seven-minute depot camera clip. The artifacts are fictional and independently identified. The deliverable is a brief that separates what was heard, what was seen, what the access log reports, and what remains unknown. It must not turn a blurry frame or noisy word into a confirmed cause.</p>"
    "<h2>Build the evidence packet</h2>"
    "<p>Transcribe the call with segment IDs, speaker labels, and uncertainty flags. Mark the device serial near minute three as unreadable. Review the video around the cited gate event and keep a time range for every visual claim. Add the access-log record as a separate source. Ask the model to draft impact, observed sequence, unknowns, and next checks with evidence IDs. Validate the IDs against the packet and preserve a review state when audio and video appear to conflict.</p>"
    "<h2>Review the result</h2>"
    "<p>Construct 33 test cases by varying noise, speaker overlap, clip sampling, and missing access logs. Reserve 11 cases as a holdout. A reviewer listens to uncertain audio spans and scrubs cited video ranges. Check that the brief never claims the gate sensor failed without telemetry, never invents a serial, and never makes a maintenance ticket from uncertain identity. The final case packet records the prompt version, artifacts, missed-event count, and any human correction.</p>"
    '<pre><code class="language-text">Artifacts: CALL-31, VIDEO-BAY-22, ACCESS-LOG-44.\nOutput fields: observed_audio, observed_video, log_fact, unknowns, next_check.\nAudio gate: uncertain serial stays unresolved.\nVideo gate: each visual claim has clip ID and time range.\nRelease gate: no unsupported cause or unauthorized work-order effect.</code></pre>'
    "<h2>Performance and operating cost</h2>"
    "<p>Processing cost grows with recording duration, frame density, and the number of reviewable segments. Lower sampling may reduce cost but miss short events, so report missed-event rates on the holdout. Human review can focus on flagged spans rather than reading every transcript word, provided those flags are reliable. Keep media retention and access within the product policy. A compact brief saves operator time only if its evidence links allow disputed claims to be checked.</p>"
    "<h3>Common Mistakes</h3><ul>"
    "<li>Do not merge a reported pressure reading with a sensor measurement.</li>"
    "<li>Do not turn a sampled frame into a continuous timeline.</li>"
    "<li>Do not execute a work order from an uncertain asset ID.</li>"
    "</ul><h2>Connected lessons</h2>"
    + link_list([
        "prompt-engineering/audio-transcription-uncertainty",
        "prompt-engineering/video-timecode-evidence",
        "prompt-engineering/multimodal-evidence-boundary",
        "prompt-engineering/evidence-id-traceability",
        "prompt-engineering/human-review-escalation",
        quiz_path,
    ])
)
new_rows.append(new_article(
    lookup["devops/practice-project"], path=project_path,
    title=titles[project_path],
    summary="Produce an incident brief with checked audio, video, and log evidence.",
    body=project_body, section=projects, subject="prompt-engineering-project",
    kind="project", order=26050,
    connections=[
        "prompt-engineering/audio-transcription-uncertainty",
        "prompt-engineering/video-timecode-evidence",
        "prompt-engineering/evidence-id-traceability",
        quiz_path,
    ],
))
lookup[projects]["data"]["modules"][0]["lessons"].append(project_path)
lookup[projects]["body"] += (
    "<h2>Multimodal incident brief</h2>"
    "<p>Combine audio, video, and log evidence without collapsing their different uncertainty states.</p>"
    + link_list([project_path, applications])
)

question_specs = [
    ("A generated patch compiles but the retry bug is untested. What is missing?",
     "A behavior test for the duplicate-retry trigger", "A longer assistant persona", "More comments",
     "Compilation does not prove the target invariant.",
     "prompt-engineering/code-change-acceptance-contract"),
    ("A small code fix proposes an unrelated queue migration. What should the reviewer demand?",
     "Evidence that the existing adapter cannot enforce the invariant", "Immediate acceptance", "A larger prompt",
     "Scope changes need a reason tied to the requested behavior.",
     "prompt-engineering/code-change-acceptance-contract"),
    ("A generated SELECT query omits tenant filtering. Is it safe to execute?",
     "No; reject it under the executor's query policy", "Yes, because it is read-only", "Yes, if the prompt asked politely",
     "Read-only access can still expose another tenant's rows.",
     "prompt-engineering/read-only-sql-generation-gate"),
    ("Where must SQL permission be enforced?",
     "At the database role and executor boundary", "In the model's explanation alone", "In a CSS rule",
     "Prompt wording cannot grant or restrict database privileges.",
     "prompt-engineering/read-only-sql-generation-gate"),
    ("An image candidate puts a pallet in the reserved text area. What is the result?",
     "Reject or revise after inspecting the rendered asset", "Accept because the prompt named the area", "Hide it with copy",
     "The pixels determine whether the composition contract passed.",
     "prompt-engineering/image-generation-brief-and-review"),
    ("A generated badge has unreadable lettering. What is a safer design choice?",
     "Keep critical copy in the interface", "Treat the letters as exact", "Skip visual review",
     "Text needed for users should be verifiable and accessible.",
     "prompt-engineering/image-generation-brief-and-review"),
    ("Engine noise obscures an audio serial number. What should the transcript say?",
     "Mark the span uncertain and request verification", "Invent the likely serial", "Omit the device entirely",
     "A critical field must retain its uncertainty.",
     "prompt-engineering/audio-transcription-uncertainty"),
    ("A summary turns a speaker's tentative statement into a confirmed reading. Is that valid?",
     "No; preserve that it was reported, not measured", "Yes, summaries may strengthen claims", "Yes, if shorter",
     "A source statement and sensor observation have different authority.",
     "prompt-engineering/audio-transcription-uncertainty"),
    ("A clip samples frames and shows an open gate. Can it prove the gate sensor failed?",
     "No; obtain sensor or access evidence", "Yes, visual openness proves the sensor state", "Yes, if the clip is long",
     "A visual observation does not establish an unseen sensor cause.",
     "prompt-engineering/video-timecode-evidence"),
    ("What makes a disputed video claim reviewable?",
     "Clip ID, time range, and original recording", "A confident adjective", "A longer summary",
     "A reviewer needs to find the cited moment.",
     "prompt-engineering/video-timecode-evidence"),
    ("A meeting note planned a policy change, but no approved version exists. What is the current status?",
     "Unverified as active", "Definitely active", "Active because the note is recent",
     "A plan is not proof that the rule took effect.",
     "prompt-engineering/time-sensitive-research-contract"),
    ("The policy store is unavailable for a date-sensitive question. What should the assistant do?",
     "State that current status is unverified", "Answer from memory", "Assume the newest rule",
     "Current claims need current evidence.",
     "prompt-engineering/time-sensitive-research-contract"),
]
questions = []
for index, (prompt, correct, wrong_a, wrong_b, explanation, target) in enumerate(question_specs):
    options = [correct, wrong_a, wrong_b]
    offset = index % 3
    questions.append({
        "prompt": prompt, "options": options[offset:] + options[:offset],
        "answer": (-offset) % 3,
        "explanation": explanation + " Review " + titles[target] + ".",
    })

quiz_body = (
    "<p>These cases test what an application must verify when a model produces code, a query, an image, a transcript, a video summary, or a current claim. Choose the response that preserves the evidence boundary.</p>"
    "<h2>Review the applications</h2>" + link_list([spec["path"] for spec in specs])
    + "<h3>Common Mistakes</h3><ul>"
    "<li>Do not accept a generated artifact from its prompt alone.</li>"
    "<li>Do not execute a query or tool effect based only on model text.</li>"
    "<li>Do not turn uncertain media evidence into a confirmed cause.</li>"
    "</ul><h2>Practice</h2>" + link_list([project_path, applications, production])
)
quiz_row = copy.deepcopy(lookup["quizzes/prompt-engineering-design-decisions"])
quiz_row.update(id=str(uuid.uuid5(uuid.NAMESPACE_URL, "aitrove:" + quiz_path)),
                path=quiz_path, title=titles[quiz_path],
                summary="Twelve decisions across code, SQL, image, audio, video, and research prompts.",
                body=quiz_body, sort_order=26060, status="published",
                published_at=stamp, created_at=stamp, updated_at=stamp)
quiz_row["data"].update(section_path=quizzes, subject_root=root_path,
                        questions=questions, duration_minutes=14,
                        related=related([applications, project_path, patterns, production]))
new_rows.append(quiz_row)
lookup[quizzes]["data"]["modules"][0]["lessons"].append(quiz_path)
lookup[quizzes]["body"] += (
    "<h2>Applied decision quiz</h2>"
    "<p>Test whether the generated artifact is safe and sufficiently supported for its destination.</p>"
    + link_list([quiz_path, applications])
)

backlinks = {
    root_path: [applications, "prompt-engineering/code-change-acceptance-contract",
                "prompt-engineering/image-generation-brief-and-review", project_path, quiz_path],
    "prompt-engineering/task-contract": ["prompt-engineering/code-change-acceptance-contract"],
    "prompt-engineering/output-sink-validation": ["prompt-engineering/read-only-sql-generation-gate"],
    "prompt-engineering/multimodal-evidence-boundary": [
        "prompt-engineering/image-generation-brief-and-review",
        "prompt-engineering/audio-transcription-uncertainty",
        "prompt-engineering/video-timecode-evidence",
    ],
    "prompt-engineering/retrieval-freshness-and-conflict": [
        "prompt-engineering/time-sensitive-research-contract",
    ],
    "prompt-engineering/evidence-id-traceability": [
        "prompt-engineering/video-timecode-evidence",
        "prompt-engineering/time-sensitive-research-contract",
    ],
}
for path, targets in backlinks.items():
    entry = lookup[path]
    entry["body"] += (
        "<h2>Apply the boundary</h2>"
        "<p>Use the artifact's source and destination to decide what must be checked before the result is accepted.</p>"
        + link_list(targets)
    )
    if entry["type"] != "subject":
        existing = [item["path"] for item in entry["data"].get("related", [])]
        entry["data"]["related"] = related(existing + targets)
    entry["updated_at"] = stamp

entries.extend(new_rows)
assert len({entry["path"] for entry in entries}) == len(entries), "duplicate route"
fixture.write_text(json.dumps(entries, ensure_ascii=False, indent=2) + "\n")
print(json.dumps({"newHubs": 1, "newLessons": len(specs),
                  "newProjects": 1, "newQuizzes": 1, "newRecords": len(new_rows)}))
