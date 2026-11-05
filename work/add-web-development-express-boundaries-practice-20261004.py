"""Add an Express permit API project and assessment drafts."""
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


hub_path = "web-tech/express-request-and-process-boundaries"
lessons = [
    "web-tech/express-middleware-order-and-request-identity",
    "web-tech/express-five-async-errors-and-response-contracts",
    "web-tech/node-request-budgets-abort-and-event-loop-fairness",
    "web-tech/node-http-drain-readiness-and-graceful-shutdown",
]
project_path = "web-tech/express-permit-api-lifecycle-project"
quiz_path = "quizzes/web-development-express-request-process"
assert hub_path in by_path and all(path in by_path for path in lessons)
assert project_path not in by_path and quiz_path not in by_path

project = copy.deepcopy(by_path["web-tech/case-intake-end-to-end-project"])
project.update(id=str(uuid.uuid5(uuid.NAMESPACE_URL, "aitrove:" + project_path)), path=project_path,
               title="Project: Express permit API lifecycle",
               summary="Build a private case API with ordered trust checks, bounded reads, controlled errors, and a drain protocol.",
               sort_order=3705, created_at=stamp, updated_at=stamp, published_at=stamp)
project["data"] = {"subject_root": "web-tech/web-technology", "section_path": "web-tech/web-technology/project",
                   "content_format": "html", "seo_ready": False, "kind": "project", "author_path": "authors/aitrove-editorial",
                   "reading_minutes": 10, "related": [hub_path] + lessons}
project["body"] = paragraph(
    "Build an Express 5 permit API serving two reviewers with nonoverlapping case sets. Reviewer 47 can read case 62 but reviewer 81 cannot. The service accepts a bounded JSON approval request, verifies the caller and case permission, and commits one logical approval under a stable operation ID. A paged search returns at most 47 summaries and cancels downstream read work when the client disconnects. An unexpected async rejection must produce one controlled error response when headers are still available. During deployment, the instance reports not ready, stops admitting work, lets short requests finish, and closes repository resources under a 29-second deadline. A response lost after approval commit is recoverable by replaying the same operation ID."
)
project["body"] += "<h2>Build contract</h2><ul>" + "".join("<li>" + html.escape(item) + "</li>" for item in [
    "Register body limits, authentication, private routes, unmatched-route handling, and error middleware in dependency order.",
    "Authorize the exact case in a server service; classify validation, forbidden, missing, conflict, and unexpected failures.",
    "Reject oversized search work, bound output to 47 rows, and cancel supported reads without claiming write rollback.",
    "Track readiness and drain state, close the HTTP listener once, and release resources within the deployment budget.",
]) + "</ul>"
project["body"] += '<h2>Implementation checkpoint</h2><pre><code class="language-javascript">' + html.escape(
    'function mayApplyApproval(operationId, committedIds) {\n'
    '  return !committedIds.has(operationId);\n'
    '}\n'
    'const committedIds = new Set(["permit-62-reviewer-47-command-81"]);\n'
    'console.log(mayApplyApproval("permit-62-reviewer-47-command-81", committedIds));\n'
    '// Output: false', quote=False) + "</code></pre>"
project["body"] += "<h2>Cost and boundaries</h2>" + paragraph(
    "Authentication and case permission add database work to each private route. That cost belongs before the protected effect, even when the HTTP handler is small. A body limit caps parser memory; a 47-row page caps response memory at O(page size) instead of O(all cases). A large synchronous sort still blocks unrelated JavaScript callbacks, so indexed database order or offloaded jobs may be required. Canceling a read can save downstream work, but the database may already have finished and an approval may already be committed. Drain time keeps old capacity alive during rollout and must fit inside the platform's termination budget. Operation deduplication uses O(m) storage for m retained commands and provides the recovery path for ambiguous lost responses."
)
project["body"] += "<h2>Failure drill</h2>" + paragraph(
    "Move authentication below the private router in a negative test, observe the failed prerequisite, and restore the correct order. Submit malformed and oversized bodies, a valid session for a forbidden case, and an unknown route. Inject a rejected promise before headers and verify one safe 500. Start a slow read, disconnect the client, and inspect downstream cancellation. Commit an approval, drop its response, and replay the same operation ID: one status transition and notification must remain. Signal termination during a short read and a hanging read. Check readiness, new request admission, repository close order, and the hard deadline behind the actual proxy."
)
project["body"] += "<h2>Acceptance checks</h2><ul>" + "".join("<li>" + html.escape(item) + "</li>" for item in [
    "No private route or repository effect accepts a reviewer without exact case permission.",
    "Every request ends in one response or a documented closed-stream outcome; errors disclose no private trace.",
    "One costly request cannot starve small requests or exceed the declared memory and output bounds.",
    "Shutdown changes readiness, drains bounded work, closes resources, and permits safe replay of a lost write response.",
]) + "</ul>"
project["body"] += "<h3>Common Mistakes</h3><ul><li>Registering a prerequisite after the route it should protect.</li><li>Launching a critical promise without awaiting it.</li><li>Treating client abort as database rollback.</li><li>Exiting immediately on a termination signal.</li></ul>"
project["body"] += "<h2>Related lessons</h2><p>" + "; ".join(link(path) for path in project["data"]["related"]) + ".</p>"
entries.append(project)
by_path[project_path] = project

questions = [
    ("Where must authentication middleware be registered for a private router?", ["Before the router", "After its successful handlers", "Only in the final 404 handler"], 0, "Middleware executes in registration order, so private routes need identity before they run."),
    ("A valid reviewer session is present. What authorizes access to case 62?", ["The session alone", "A case-level permission check", "A forwarded client IP header"], 1, "Identity and resource permission are separate decisions; the service must verify this reviewer and case."),
    ("What should an unmatched route do after all intended routes?", ["Wait without responding", "Retry every router", "Return a controlled 404"], 2, "A final unmatched-route handler ends requests that no registered route accepted."),
    ("How does Express 5 handle a rejected promise returned by an async route?", ["It forwards the rejection to error handling", "It silently reports success", "It rewrites a committed database action"], 0, "A returned rejected promise enters Express 5's error path; detached work outside that promise does not."),
    ("A streamed response has sent headers before an error. What is no longer safe?", ["Logging internal context", "Sending a second JSON status and body", "Closing the connection"], 1, "HTTP headers and status are already committed, so an error handler cannot replace them with another JSON response."),
    ("Which outcome is a domain conflict rather than an internal server error?", ["A database driver crash", "An unhandled programming exception", "A case changed before approval"], 2, "A changed case is an expected state conflict and should have a controlled contract distinct from a 500."),
    ("What limits memory for a permit search response?", ["A bounded page size", "An unbounded sort", "A longer request timeout"], 0, "A fixed maximum page keeps response size proportional to that page rather than the full case set."),
    ("Why can an async route still block other Node requests?", ["Await always blocks the loop", "It can run a large synchronous sort before yielding", "It sends a JSON response"], 1, "An async declaration does not make synchronous CPU work cooperative with the event loop."),
    ("What does aborting a disconnected approval guarantee?", ["The write was rolled back", "The reviewer gets a success response", "Nothing about a write already committed"], 2, "Client cancellation can stop some work but does not reverse a committed mutation; replay identity resolves ambiguity."),
    ("What should readiness report when a process begins to drain?", ["Not ready for new routed work", "Healthy and ready for all new writes", "That the database has rolled back"], 0, "A draining instance can remain alive while telling the load balancer not to route new work to it."),
    ("When should repository pools normally close during drain?", ["Before active handlers finish", "After bounded in-flight work finishes or reaches deadline", "Only on the next startup"], 1, "Closing the repository too early breaks active requests; shutdown must coordinate their bounded completion."),
    ("A committed approval response is lost during shutdown. What makes retry safe?", ["A new ID on every attempt", "An immediate process.exit", "The same operation ID checked by the server"], 2, "Server-side deduplication of a stable logical command can return the prior committed outcome."),
]
assert len(questions) == 12 and [sum(row[2] == index for row in questions) for index in range(3)] == [4, 4, 4]
quiz = copy.deepcopy(by_path["quizzes/web-development-browser-contracts"])
quiz.update(id=str(uuid.uuid5(uuid.NAMESPACE_URL, "aitrove:" + quiz_path)), path=quiz_path,
            title="Web Development: Express request and process quiz",
            summary="Twelve explained choices about middleware, async errors, request budgets, and shutdown.",
            sort_order=3706, created_at=stamp, updated_at=stamp, published_at=stamp)
quiz["data"] = {"subject_root": "web-tech/web-technology", "section_path": "web-tech/quizzes",
                "content_format": "html", "seo_ready": False,
                "questions": [{"prompt": prompt, "options": options, "answer": answer, "explanation": explanation}
                              for prompt, options, answer, explanation in questions]}
quiz["body"] = paragraph(quiz["summary"] + " Choose an answer, inspect the reason, and return to the related failure drill.")
quiz["body"] += "<h2>Related lessons</h2><p>" + "; ".join(link(path) for path in [hub_path] + lessons + [project_path]) + ".</p>"
entries.append(quiz)
by_path[quiz_path] = quiz

for index_path, heading, target, summary in [
    ("web-tech/web-technology/project", "Express service project", project_path, project["summary"]),
    ("web-tech/quizzes", "Express lifecycle check", quiz_path, quiz["summary"]),
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
curriculum["body"] += "<h2>Express request practice</h2><p>" + link(project_path) + "; " + link(quiz_path) + ".</p>"
curriculum["updated_at"] = stamp
fixture.write_text(json.dumps(entries, ensure_ascii=False, indent=2) + "\n")
print(json.dumps({"new_projects": 1, "new_quizzes": 1, "new_questions": 12}))
