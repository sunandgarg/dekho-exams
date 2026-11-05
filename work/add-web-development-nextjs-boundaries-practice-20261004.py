"""Add a Next.js permit delivery project and assessment drafts."""
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


hub_path = "web-tech/nextjs-app-router-delivery-boundaries"
lessons = [
    "web-tech/nextjs-server-client-component-and-data-boundary",
    "web-tech/nextjs-cache-scope-and-private-read-invalidation",
    "web-tech/nextjs-server-functions-validation-and-operation-identity",
    "web-tech/nextjs-streaming-suspense-and-error-recovery",
]
project_path = "web-tech/nextjs-permit-delivery-and-cache-project"
quiz_path = "quizzes/web-development-nextjs-app-router-boundaries"
assert hub_path in by_path and all(path in by_path for path in lessons)
assert project_path not in by_path and quiz_path not in by_path

project = copy.deepcopy(by_path["web-tech/case-intake-end-to-end-project"])
project.update(id=str(uuid.uuid5(uuid.NAMESPACE_URL, "aitrove:" + project_path)), path=project_path,
               title="Project: Next.js permit delivery and cache boundary",
               summary="Build a private queue with a small client island, explicit freshness, deduplicated approvals, and a streamed panel.",
               sort_order=3695, created_at=stamp, updated_at=stamp, published_at=stamp)
project["data"] = {"subject_root": "web-tech/web-technology", "section_path": "web-tech/web-technology/project",
                   "content_format": "html", "seo_ready": False, "kind": "project", "author_path": "authors/aitrove-editorial",
                   "reading_minutes": 10, "related": [hub_path] + lessons}
project["body"] = paragraph(
    "Build a private permit dashboard for reviewers 47 and 81. The server page reads the current reviewer and sends a first page of 47 authorized summaries to a small client filter. A public permit-category list may be reused, while the private queue must stay inside the viewer's permission boundary. The reviewer approves case 62 through a server function using one operation ID for that logical intent. A dropped response followed by a retry must not create another approval or notification. After commit, the queue must show the authoritative status within the declared freshness window. A slow metrics panel streams after the useful queue shell; it must fail independently and never display another reviewer's values."
)
project["body"] += "<h2>Build contract</h2><ul>" + "".join("<li>" + html.escape(item) + "</li>" for item in [
    "Keep identity and repository access server-side; transfer only bounded, permitted, serializable case fields.",
    "Document cache audience and stale window for public categories and private queue reads separately.",
    "Validate action fields and permission, deduplicate operation IDs atomically, then refresh the affected view after commit.",
    "Place only slow authorized metrics behind a nested fallback, with a recoverable failure path and stable layout.",
]) + "</ul>"
project["body"] += '<h2>Implementation checkpoint</h2><pre><code class="language-javascript">' + html.escape(
    'function mayApplyPermitApproval(operationId, committedOperationIds) {\n'
    '  return !committedOperationIds.has(operationId);\n'
    '}\n'
    'const committedOperationIds = new Set(["permit-62-reviewer-81-attempt-47"]);\n'
    'console.log(mayApplyPermitApproval("permit-62-reviewer-81-attempt-47", committedOperationIds));\n'
    '// Output: false', quote=False) + "</code></pre>"
project["body"] += "<h2>Cost and boundaries</h2>" + paragraph(
    "A server read costs permission and repository work per reviewer. A public cache reduces repeated category reads, but a private URL-only cache can disclose case data across accounts. A bounded transfer of 47 summaries avoids shipping all 47,000 cases; client filtering costs O(n) over only those transferred cases. The deduplication ledger uses O(m) storage for m retained operation IDs and must be transactional with the mutation. Revalidating a broad path can increase database load during an approval burst, so measure fanout. Streaming can make the queue useful before slow metrics complete, but it does not shorten the metrics query itself. Keep the fallback bounded and accessible, and measure the time to the queue and the time to the completed panel separately."
)
project["body"] += "<h2>Failure drill</h2>" + paragraph(
    "Warm reviewer 47's queue, then open the same route as reviewer 81 and scan both HTML and client payloads for forbidden case IDs. Approve case 62, drop the response after commit, replay the same operation ID, and inspect one database transition and one notification. Return to the queue through a client transition and hard reload; both must converge on approved within the freshness window. Delay metrics 1.8 seconds and confirm the queue arrives first. Fail the metrics request after the shell streams and verify that the panel offers a recoverable state rather than showing zero or a permanent spinner. Disable browser scripts and repeat the first-page read."
)
project["body"] += "<h2>Acceptance checks</h2><ul>" + "".join("<li>" + html.escape(item) + "</li>" for item in [
    "No forbidden fields cross the server/client boundary or appear in another reviewer response.",
    "Private queue reads cannot reuse a response across permission boundaries.",
    "One operation ID produces one logical approval, followed by a fresh visible status.",
    "The useful shell streams before slow metrics and survives a recoverable metrics failure.",
]) + "</ul>"
project["body"] += "<h3>Common Mistakes</h3><ul><li>Moving the whole server page into a client component for one filter.</li><li>Reusing a private response by route path alone.</li><li>Refreshing cache state before the database commits.</li><li>Treating a loading fallback as error recovery.</li></ul>"
project["body"] += "<h2>Related lessons</h2><p>" + "; ".join(link(path) for path in project["data"]["related"]) + ".</p>"
entries.append(project)
by_path[project_path] = project

questions = [
    ("A page needs one interactive search field. Which boundary should move to the browser?", ["The smallest search component", "The entire private repository layer", "All layout and page modules"], 0, "A small client component can own the input while server code keeps identity and private repository access."),
    ("What kind of prop may cross a Server-to-Client Component boundary?", ["A database connection", "A small serializable permitted summary", "A server secret and raw error"], 1, "Transferred props must be serializable and contain only fields the current viewer is allowed to receive."),
    ("Who authorizes a private case detail after the client received a queue summary?", ["The search input", "The case title", "The server detail request again"], 2, "Authorization is checked at every server entry point; a permitted summary does not grant all detail access."),
    ("Which cache may safely be shared across reviewers under one public key?", ["A genuinely public permit-category list", "A private queue response", "A selected case with reviewer notes"], 0, "Public categories may have one audience, while reviewer-specific records need their own visibility boundary."),
    ("When should a successful approval invalidate its stale queue representation?", ["Before the transaction begins", "After the database commit", "Only when a browser tab closes"], 1, "The affected representation should be refreshed after the authoritative write commits, then verified in the current view."),
    ("Why is a route path alone unsafe as a key for private queue data?", ["Paths are too long", "It changes on every request", "Different reviewers can visit the same path"], 2, "A shared path does not encode reviewer identity or permission and can return another viewer's case list."),
    ("What is a server function's input trust level?", ["Untrusted, even when called by a form", "Trusted because it runs on the server", "Trusted when its button is disabled"], 0, "FormData can be changed by callers, so parsing, session checks, and case authorization remain required."),
    ("A committed approval response is lost. What should a retry reuse?", ["A new operation ID", "The original operation ID", "A client-only success badge"], 1, "Replaying one stable token lets the server return the prior logical result without committing a second effect."),
    ("Who must guarantee that one operation ID creates one logical write?", ["A client Set alone", "The button component", "The server mutation transaction"], 2, "Client state is not authoritative across retries, tabs, or failures; the server must deduplicate atomically."),
    ("Where should a slow metrics query sit when the case queue is already ready?", ["Inside a nested Suspense boundary", "Above the whole route as one blocking query", "In a shared previous-reviewer panel"], 0, "A nested boundary can send the useful queue while the slow authorized metrics panel remains pending."),
    ("Metrics fail after the shell streams. What should the panel do?", ["Display a fake zero", "Show a recoverable error state", "Leave the loading fallback forever"], 1, "Failure is distinct from pending and from a real zero; an error boundary should let the task recover."),
    ("What must be checked in a stream for two concurrent reviewers?", ["Only the first HTML chunk", "Only final paint timing", "Every chunk's viewer authorization"], 2, "A streamed response can release data in several chunks, and every emitted private value must belong to its viewer."),
]
assert len(questions) == 12 and [sum(row[2] == index for row in questions) for index in range(3)] == [4, 4, 4]
quiz = copy.deepcopy(by_path["quizzes/web-development-browser-contracts"])
quiz.update(id=str(uuid.uuid5(uuid.NAMESPACE_URL, "aitrove:" + quiz_path)), path=quiz_path,
            title="Web Development: Next.js App Router boundaries quiz",
            summary="Twelve explained choices about server/client transfer, cache scope, mutations, and streaming.",
            sort_order=3696, created_at=stamp, updated_at=stamp, published_at=stamp)
quiz["data"] = {"subject_root": "web-tech/web-technology", "section_path": "web-tech/quizzes",
                "content_format": "html", "seo_ready": False,
                "questions": [{"prompt": prompt, "options": options, "answer": answer, "explanation": explanation}
                              for prompt, options, answer, explanation in questions]}
quiz["body"] = paragraph(quiz["summary"] + " Choose an answer, check its reason, and revisit the matching boundary when the result is wrong.")
quiz["body"] += "<h2>Related lessons</h2><p>" + "; ".join(link(path) for path in [hub_path] + lessons + [project_path]) + ".</p>"
entries.append(quiz)
by_path[quiz_path] = quiz

for index_path, heading, target, summary in [
    ("web-tech/web-technology/project", "Next.js delivery project", project_path, project["summary"]),
    ("web-tech/quizzes", "Next.js boundary check", quiz_path, quiz["summary"]),
]:
    index = by_path[index_path]
    index["data"]["modules"][0]["lessons"].append(target)
    index["body"] += "<h2>" + heading + "</h2><p>" + link(target) + " — " + html.escape(summary) + "</p>"
    index["updated_at"] = stamp
hub = by_path[hub_path]
hub["body"] += "<h2>Practice and check</h2><p>Build " + link(project_path) + " and review " + link(quiz_path) + ".</p>"
hub["updated_at"] = stamp
for path in lessons:
    lesson = by_path[path]
    lesson["body"] += "<h2>Apply and check</h2><p>Build " + link(project_path) + " and review " + link(quiz_path) + ".</p>"
    lesson["data"]["related"].extend([project_path, quiz_path])
    lesson["updated_at"] = stamp
curriculum = by_path["web-tech/web-technology"]
curriculum["body"] += "<h2>Next.js delivery practice</h2><p>" + link(project_path) + "; " + link(quiz_path) + ".</p>"
curriculum["updated_at"] = stamp
fixture.write_text(json.dumps(entries, ensure_ascii=False, indent=2) + "\n")
print(json.dumps({"new_projects": 1, "new_quizzes": 1, "new_questions": 12}))
