"""Add Angular permit operations practice and assessment drafts."""
import copy
import datetime
import html
import json
import uuid
from pathlib import Path

root = Path(__file__).resolve().parents[1]
fixture = root / "src/data/fixtures.json"
entries = json.loads(fixture.read_text())
by_path = {entry["path"]: entry for entry in entries}
stamp = datetime.datetime.now(datetime.UTC).isoformat()


def paragraph(value):
    return "<p>" + html.escape(value) + "</p>"


def link(path):
    assert path in by_path, path
    return '<a href="/' + path + '">' + html.escape(by_path[path]["title"]) + "</a>"


hub_path = "web-tech/angular-signals-and-delivery-boundaries"
lessons = [
    "web-tech/angular-signal-sources-computed-views-and-effect-scope",
    "web-tech/angular-component-input-output-and-row-identity",
    "web-tech/angular-httpclient-streams-and-stale-detail-requests",
    "web-tech/angular-ssr-hydration-and-private-transfer-state",
]
project_path = "web-tech/angular-permit-operations-queue-project"
quiz_path = "quizzes/web-development-angular-signals-delivery"
assert hub_path in by_path and all(path in by_path for path in lessons)
assert project_path not in by_path and quiz_path not in by_path

project = copy.deepcopy(by_path["web-tech/case-intake-end-to-end-project"])
project.update(id=str(uuid.uuid5(uuid.NAMESPACE_URL, "aitrove:" + project_path)), path=project_path,
               title="Project: Angular permit operations queue",
               summary="Build a case queue with signal-derived views, component contracts, stale-request control, and safe hydration.",
               sort_order=3667, created_at=stamp, updated_at=stamp, published_at=stamp)
project["data"] = {"subject_root": "web-tech/web-technology", "section_path": "web-tech/web-technology/project",
                   "content_format": "html", "seo_ready": False, "kind": "project", "author_path": "authors/aitrove-editorial",
                   "reading_minutes": 9, "related": [hub_path] + lessons}
project["body"] = paragraph(
    "Build an Angular permit operations queue for a city reviewer. The first page contains 47 cases and a total of 47,000 authorized summaries. Search and status are writable source signals; visible cases and counts are computed from the same source snapshot. A row receives a required case input and emits an approval intent, while the parent owns the mutation, pending state, and rollback. Stable case IDs must keep a private note attached to its case when sorting changes. Switching rapidly between cases 47 and 81 may finish requests in reverse order; only the active case may appear. The initial server HTML and browser render must agree on authorized data before a browser-only saved display preference applies."
)
project["body"] += "<h2>Build contract</h2><ul>" + "".join("<li>" + html.escape(item) + "</li>" for item in [
    "Keep one writable case snapshot and derive the visible list, count, and status summary with computed signals.",
    "Use required inputs and typed outputs for row contracts; track rows by stable case ID and keep server mutations in the owner.",
    "Bind detail requests to selected identity, cancel obsolete reads, and validate response identity before display.",
    "Isolate server requests, transfer only authorized boot data, and defer browser storage until after initial render.",
]) + "</ul>"
project["body"] += '<h2>Implementation checkpoint</h2><pre><code class="language-javascript">' + html.escape(
    'function mayShowPermitDetail(requestGeneration, activeGeneration, responseCaseId, selectedCaseId) {\n'
    '  return requestGeneration === activeGeneration && responseCaseId === selectedCaseId;\n'
    '}\n'
    'console.log(mayShowPermitDetail(47, 81, 47, 81));\n'
    '// Output: false', quote=False) + "</code></pre>"
project["body"] += "<h2>Cost and boundaries</h2>" + paragraph(
    "A changed query may scan n authorized cases and allocate up to O(n) visible references. A computed signal avoids recomputation while its dependencies stay unchanged; it does not turn a 47,000-case filter into constant-time work. Preserve an O(page size) render boundary and ask the server for paged search when filtering all cases on every keystroke becomes expensive. Stable row identity retains editor state, which also means private drafts need explicit expiry and logout cleanup. Canceling an obsolete read saves some client work, but the server may already have processed it. Generation and identity checks still guard publication. Server-side rendering spends bytes and CPU per request; transfer only data already authorized for that viewer and never share mutable reviewer state across requests."
)
project["body"] += "<h2>Failure drill</h2>" + paragraph(
    "Load the same authorized snapshot on server and client, then apply a saved page-size preference only after hydration. Reverse the completion order of detail requests for cases 47 and 81; case 47 must not overwrite case 81. Insert a new case before a row whose editor contains a private note, then sort in both directions. The note must remain with its case ID. Force an approval failure after the child emits its intent and verify that the parent restores the previous server-backed status. Render two reviewers concurrently on one server worker and compare their boot payloads: a case from one reviewer must never enter the other response."
)
project["body"] += "<h2>Acceptance checks</h2><ul>" + "".join("<li>" + html.escape(item) + "</li>" for item in [
    "Visible cases, count, and status summary always describe the same source snapshot and filters.",
    "Rapid selection changes cannot publish stale detail or leak detail from another selected case.",
    "Sort, insertion, and rejected approval preserve case-owned notes and authoritative status.",
    "Concurrent server renders keep viewer data separate, and the first browser render matches authorized HTML.",
]) + "</ul>"
project["body"] += "<h3>Common Mistakes</h3><ul><li>Copying computed output into another writable signal.</li><li>Using a row position as the tracking key.</li><li>Assuming cancellation alone prevents an obsolete response from rendering.</li><li>Serializing private detail into a shared server cache.</li></ul>"
project["body"] += "<h2>Related lessons</h2><p>" + "; ".join(link(path) for path in project["data"]["related"]) + ".</p>"
entries.append(project)
by_path[project_path] = project

questions = [
    ("Where should the visible count come from when search and status change?", ["The computed visible-case result", "A separate writable counter updated later", "The index of the last rendered row"], 0, "A computed count based on the visible-case result stays aligned with the same snapshot and filters."),
    ("What makes a computed signal update?", ["A timer outside Angular", "A signal dependency it read changes", "A direct write to the computed signal"], 1, "Computed output is read-only and recalculates when a signal read during its derivation changes."),
    ("What is an appropriate use for an effect?", ["Copying one signal into another", "Owning all business state", "Synchronizing an external API or side effect"], 2, "Effects are suited to external synchronization; derived view data belongs in computed values."),
    ("A row cannot render without a permit record. Which input contract expresses that?", ["A required, typed input", "An optional untyped global", "A query parameter read by every row"], 0, "A required typed input declares the component's data contract and lets the parent supply the record."),
    ("Who should own an approval request emitted by a case row?", ["The row by mutating its input", "The parent that owns pending and server state", "The list's array index"], 1, "The row reports intent through an output; the owning parent coordinates the mutation and rollback."),
    ("Which @for tracking choice survives a resort and insertion?", ["The current row index", "A new random value per render", "The stable permit case ID"], 2, "Stable entity identity prevents private editor state from being reassigned to a different row."),
    ("What happens when an HttpClient cold observable is subscribed to twice?", ["It can issue two backend requests", "It always reuses one cached response", "The second subscription is forbidden"], 0, "Each subscription to a cold HTTP observable can start a distinct request unless sharing is intentional."),
    ("Why use switchMap for rapid case-detail selection?", ["To retry approvals indefinitely", "To replace the prior read stream with the latest selection", "To make responses immutable"], 1, "Switching to the latest detail stream stops obsolete reads from being the active result for that selection."),
    ("A transport ignores cancellation. What additional publication check is needed?", ["Arrival time only", "Response byte length", "Active request generation and selected case identity"], 2, "A late response must still match the active generation and selected case before entering the detail panel."),
    ("How should per-reviewer state be allocated during server rendering?", ["Inside each request", "As one writable module singleton", "From the previous viewer's transfer payload"], 0, "Request-scoped state keeps one reviewer's selection and private data out of another server response."),
    ("When should a saved browser display preference alter server-rendered markup?", ["Before the first browser render differs", "After the initial matching render", "By changing server authorization"], 1, "The initial browser view should match the server's authorized HTML; local preferences can apply afterward."),
    ("What belongs in transferred boot data?", ["Every private case in the organization", "One cache shared across reviewers", "Only data authorized for that response's viewer"], 2, "A serialized boot payload is visible in the response and must be scoped to the viewer who requested it."),
]
assert len(questions) == 12 and [sum(row[2] == index for row in questions) for index in range(3)] == [4, 4, 4]
quiz = copy.deepcopy(by_path["quizzes/web-development-browser-contracts"])
quiz.update(id=str(uuid.uuid5(uuid.NAMESPACE_URL, "aitrove:" + quiz_path)), path=quiz_path,
            title="Web Development: Angular signals and delivery quiz",
            summary="Twelve explained choices about signals, component ownership, HTTP streams, and hydration.",
            sort_order=3668, created_at=stamp, updated_at=stamp, published_at=stamp)
quiz["data"] = {"subject_root": "web-tech/web-technology", "section_path": "web-tech/quizzes",
                "content_format": "html", "seo_ready": False,
                "questions": [{"prompt": prompt, "options": options, "answer": answer, "explanation": explanation}
                              for prompt, options, answer, explanation in questions]}
quiz["body"] = paragraph(quiz["summary"] + " Choose an answer, inspect its reason, and revisit the relevant lesson when a boundary fails.")
quiz["body"] += "<h2>Related lessons</h2><p>" + "; ".join(link(path) for path in [hub_path] + lessons + [project_path]) + ".</p>"
entries.append(quiz)
by_path[quiz_path] = quiz

for index_path, module_path, title, item_path, item_summary in [
    ("web-tech/web-technology/project", "web-tech/web-technology/project", "Angular operations queue project", project_path, project["summary"]),
    ("web-tech/quizzes", "web-tech/quizzes", "Angular delivery check", quiz_path, quiz["summary"]),
]:
    index = by_path[index_path]
    index["data"]["modules"][0]["lessons"].append(item_path)
    index["body"] += "<h2>" + title + "</h2><p>" + link(item_path) + " — " + html.escape(item_summary) + "</p>"
    index["updated_at"] = stamp
hub = by_path[hub_path]
hub["body"] += "<h2>Practice and check</h2><p>Build " + link(project_path) + " and review " + link(quiz_path) + ".</p>"
hub["updated_at"] = stamp
for path in lessons:
    lesson = by_path[path]
    lesson["body"] += "<h2>Apply and check</h2><p>Build " + link(project_path) + " and review " + link(quiz_path) + ".</p>"
    lesson["data"]["related"].extend([project_path, quiz_path])
    lesson["updated_at"] = stamp
root_entry = by_path["web-tech/web-technology"]
root_entry["body"] += "<h2>Angular operations practice</h2><p>" + link(project_path) + "; " + link(quiz_path) + ".</p>"
root_entry["updated_at"] = stamp
fixture.write_text(json.dumps(entries, ensure_ascii=False, indent=2) + "\n")
print(json.dumps({"new_projects": 1, "new_quizzes": 1, "new_questions": 12}))
