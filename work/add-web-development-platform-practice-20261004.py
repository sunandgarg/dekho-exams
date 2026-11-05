"""Add typed frontend and browser trust practice routes."""

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


def link(path):
    assert path in by_path, path
    return f'<a href="/{html.escape(path, quote=True)}">{html.escape(by_path[path]["title"])}</a>'


def para(value):
    return f"<p>{html.escape(value)}</p>"


projects = [
    dict(path="web-tech/typed-review-console-project", title="Project: typed review console",
         summary="Build a case route that validates raw API data, survives request races, and loads its optional editor on demand.",
         intro="Build the review console for cases 47 and 62. The route loads one case summary, shows status and review count, and offers an optional photo-annotation editor. Parse the API response from unknown data through one decoder before it reaches components. Switch between cases while responses complete in the wrong order; the screen and URL must still agree. The editor should not burden every queue visitor, so load it on the first annotation action and provide a visible wait, retry, and plain-note fallback if the module fails. A component boundary earns its place only when it makes the task easier to maintain.",
         scope=["Decode raw JSON into a narrow case model, rejecting malformed counts, missing IDs, and unsupported statuses before rendering.", "Use route data loading or an effect with cleanup; reject any stale success or error result after caseId changes.", "Move annotation code behind a task-level module split and test cold, warm, failed, and old-tab chunk requests."],
         code='function isCaseSummary(rawCase) {\n  return rawCase !== null && typeof rawCase === "object" &&\n    Number.isInteger(rawCase.caseId) && rawCase.caseId > 0 && Number.isInteger(rawCase.reviewCount) && rawCase.reviewCount >= 0 &&\n    (rawCase.status === "open" || rawCase.status === "closed");\n}',
         language="javascript", cost="Decoding an n-item list costs O(n) in record count. A route-level fetch can avoid a component waterfall; an unnecessary extra cache can add invalidation work. Deferring the editor reduces initial bytes but moves download and evaluation cost to first use. Record both queue load and editor-open timings. Keep server authorization and response status handling independent of frontend types; a valid JSON shape is not permission to read that case.",
         failure="First return a numeric string for reviewCount and verify the console shows a controlled decode error. Then make case 62 finish before case 47 and confirm the panel stays on 62. Fail the old request after the route changes; its error must not replace the current case. Finally remove the editor chunk from a simulated old deployment and check that the user can retry or leave a plain note without losing context. These failures cross separate boundaries and need separate recovery states.",
         checks=["Decode valid, malformed, and future-version raw JSON before any component receives it.", "Run both response orders and an old-request failure after route change.", "Measure cold first editor use and recover from a failed chunk request.", "Verify case-level authorization independently of successful decoding."],
         mistakes=["Casting response JSON to a type without runtime checks.", "Protecting success but not error completion from an obsolete request.", "Calling smaller initial JavaScript a win without measuring first editor use."],
         related=["web-tech/typescript-and-runtime-api-boundaries", "web-tech/react-effects-and-request-races", "web-tech/web-components-and-shadow-boundaries", "web-tech/module-splitting-and-interaction-budget", "web-tech/record-level-authorization"]),
    dict(path="web-tech/private-page-trust-review-project", title="Project: private page trust review",
         summary="Audit response policy, note rendering, dependencies, and telemetry for a private case page.",
         intro="Review a private case page before release. It displays notes, loads a chart on one report route, and emits operational events when a case fails to open. Confirm that private pages cannot be framed by unrelated origins, that cross-site navigation does not disclose full case paths, and that browser capabilities the page does not need are denied. Render notes as text. Review a chart dependency update from a clean lockfile install and inspect browser requests. Finally, make failure telemetry useful without storing notes, tokens, session values, or full URLs. The deliverable is a small evidence packet, not a claim that headers alone secure the service.",
         scope=["Capture actual browser policy headers on success, redirect, and error responses for private routes, plus the distinct public widget route.", "Save and reload HTML-looking note text through the full API path; review any raw-markup sink separately.", "Build from a clean dependency install, inspect changed packages and network traffic, and prove telemetry excludes private payloads with retention checks."],
         code='function caseFailureEvent(errorKind, requestId, releaseId) {\n  const accepted = ["route_failure", "permission_denied", "decode_failure"];\n  if (!accepted.includes(errorKind)) throw new Error("Unsupported category");\n  return { event: errorKind, routeClass: "case_detail", requestId, releaseId };\n}',
         language="javascript", cost="Policy headers are cheap on the wire; route-by-route testing and partner compatibility cost time. Text rendering is cheaper to maintain than an unnecessary rich-text sanitizer. Clean installs and dependency diffs take engineer attention, but reduce surprises from mutable packages. Narrow telemetry reduces storage and disclosure; if a rare incident needs extra context, add a time-limited diagnostic field with an owner rather than turning on whole-body logging.",
         failure="Force a 403 response and inspect whether it lost the private route's frame policy. Enter a note that looks like markup, then reload and make sure it remains literal text. Simulate a chart-library update that sends a request to an unknown host and confirm the review catches it. Trigger an account recovery error and search the resulting logs for a test token and private note. If either appears, pause rollout, restrict affected logs, and fix the logging boundary before claiming the page is ready.",
         checks=["Verify policy headers across successful and failed private responses, then test framing behavior.", "Render hostile-looking note input as text after save, reload, and live update.", "Inspect lockfile changes, built network traffic, and optional chart failure behavior.", "Search telemetry for seeded secrets and test the configured deletion period."],
         mistakes=["Assuming policy headers replace server authorization.", "Treating a database note as safe HTML.", "Calling a lockfile or advisory scan a full dependency review.", "Logging entire failed requests for convenience."],
         related=["web-tech/embedding-and-browser-capability-headers", "web-tech/dom-sinks-and-trusted-content", "web-tech/dependency-integrity-and-update-window", "web-tech/telemetry-minimization-and-retention", "web-tech/output-escaping-and-csp"]),
]

for number, project in enumerate(projects, start=1):
    assert project["path"] not in by_path
    entry = copy.deepcopy(by_path["web-tech/case-intake-end-to-end-project"])
    entry.update(id=str(uuid.uuid5(uuid.NAMESPACE_URL, "aitrove:" + project["path"])),
                 path=project["path"], title=project["title"], summary=project["summary"],
                 sort_order=990 + number, created_at=stamp, updated_at=stamp, published_at=stamp)
    entry["data"] = {"subject_root": "web-tech/web-technology", "section_path": "web-tech/web-technology/project",
                     "content_format": "html", "seo_ready": False, "kind": "project",
                     "author_path": "authors/aitrove-editorial", "reading_minutes": 8, "related": project["related"]}
    body = para(project["intro"])
    body += "<h2>Build contract</h2><ul>" + "".join(f"<li>{html.escape(item)}</li>" for item in project["scope"]) + "</ul>"
    body += f'<h2>Implementation checkpoint</h2><pre><code class="language-{project["language"]}">' + html.escape(project["code"], quote=False) + "</code></pre>"
    body += "<h2>Cost and boundaries</h2>" + para(project["cost"])
    body += "<h2>Failure drill</h2>" + para(project["failure"])
    body += "<h2>Acceptance checks</h2><ul>" + "".join(f"<li>{html.escape(item)}</li>" for item in project["checks"]) + "</ul>"
    body += "<h3>Common Mistakes</h3><ul>" + "".join(f"<li>{html.escape(item)}</li>" for item in project["mistakes"]) + "</ul>"
    body += "<h2>Related lessons</h2><p>" + "; ".join(link(path) for path in project["related"]) + ".</p>"
    entry["body"] = body
    entries.append(entry)
    by_path[entry["path"]] = entry

quiz_path = "quizzes/web-development-platform-trust-contracts"
questions = [
    ("What does a TypeScript assertion do to untrusted JSON at runtime?", ["Validate every field", "Nothing; a runtime decoder is still required", "Authorize the case"], 1, "A type assertion disappears from emitted JavaScript. Network data remains untrusted until the fields needed by the application are checked at runtime."),
    ("The API returns reviewCount as a string. What should the decoder do?", ["Silently concatenate it", "Assume the compiler will fix it", "Reject or deliberately normalize it under the written contract"], 2, "A string is not the promised count. An explicit boundary may reject it or apply a documented conversion, but components should not improvise different coercions."),
    ("Case 47 loads after the user has switched to case 62. Which result owns the panel?", ["Case 62", "Whichever response arrives last", "Both merged together"], 0, "The current route owns the visible state. Cleanup or a generation check must prevent old success and error callbacks from replacing it."),
    ("What should an effect cleanup do for a route-bound request?", ["Nothing if fetch started", "Stop or ignore work tied to the previous route", "Remove the route parameter"], 1, "An obsolete request can finish after navigation. Cleanup should abort where possible and prevent its completion paths from updating current state."),
    ("Does a shadow root make a custom element a security sandbox?", ["Yes, it blocks malicious script", "Only for CSS", "No; it encapsulates DOM and style, not trust"], 2, "Shadow DOM helps isolate component structure and styles but does not replace input handling, authorization, or browser security policy."),
    ("When is task-level module splitting useful?", ["When optional heavy code can wait until a clear task, with loading and failure recovery", "For every tiny helper", "Only when all visitors use the module"], 0, "Deferring an optional editor can save first-page work, but its first use must have a measured wait and a route to recover from download failure."),
    ("A private case page must not be framed. Which control belongs on its response?", ["A broad wildcard frame allowlist", "A restrictive frame-ancestors policy", "A client-only click handler"], 1, "The framing decision belongs in the actual response policy for the private route, including its error responses; record authorization remains separate."),
    ("What is the default way to display a plain case note containing angle brackets?", ["Assign it to innerHTML", "Decode it twice", "Render it as text"], 2, "Plain notes do not need a markup parser. Text rendering preserves characters without creating active HTML from an untrusted value."),
    ("What does a dependency lockfile prove?", ["Which versions a clean install resolves, not that their code is safe", "That no package can make network requests", "That external scripts never change"], 0, "A lockfile supports reproducibility. It does not replace provenance, transitive diff, runtime behavior, license, and rollback review."),
    ("A chart script is needed only on one route. What should review include?", ["Only the package name", "Route scope, changed dependencies, network requests, and first-use behavior", "Only its compressed size"], 1, "A route-scoped optional dependency can still create privacy and interaction costs. Review its behavior and failure path, not just its size."),
    ("Which telemetry field is least suitable for a case-load failure event?", ["A coarse route class", "A release identifier", "The complete private note and session token"], 2, "Operational events should answer triage questions without copying private content or credentials into a second storage system."),
    ("How should retention be verified?", ["Read the policy document only", "Test deletion in the actual store after the retention interval", "Assume old logs are never accessed"], 1, "A written limit is not an operational guarantee. A test event past its lifetime should disappear from the relevant storage and deletion path."),
]

assert quiz_path not in by_path
quiz = copy.deepcopy(by_path["quizzes/web-development-browser-contracts"])
quiz.update(id=str(uuid.uuid5(uuid.NAMESPACE_URL, "aitrove:" + quiz_path)), path=quiz_path,
            title="Web Development: platform and trust contracts quiz",
            summary="Twelve explained decisions about runtime types, async UI work, browser controls, dependencies, and telemetry.",
            sort_order=995, created_at=stamp, updated_at=stamp, published_at=stamp)
quiz["data"] = {"subject_root": "web-tech/web-technology", "section_path": "web-tech/quizzes",
                "content_format": "html", "seo_ready": False,
                "questions": [{"prompt": prompt, "options": options, "answer": answer, "explanation": explanation}
                              for prompt, options, answer, explanation in questions]}
quiz["body"] = para(quiz["summary"] + " Choose a response, read its explanation, and reopen a related lesson for the missed boundary.")
quiz["body"] += "<h2>Related lessons</h2><p>" + "; ".join(link(path) for project in projects for path in project["related"][:4]) + ".</p>"
entries.append(quiz)
by_path[quiz_path] = quiz

project_hub = by_path["web-tech/web-technology/project"]
project_hub["data"]["modules"][0]["lessons"].extend(project["path"] for project in projects)
project_hub["body"] += "<h2>Platform and trust projects</h2><ul>" + "".join(
    f'<li>{link(project["path"])} — {html.escape(project["summary"])}</li>' for project in projects) + "</ul>"
project_hub["summary"] = "Build and verify thirteen projects across browser, API, data, identity, accessibility, localization, platform, privacy, offline, live, and release contracts."
project_hub["updated_at"] = stamp

quiz_hub = by_path["web-tech/quizzes"]
quiz_hub["data"]["modules"][0]["lessons"].append(quiz_path)
quiz_hub["body"] += "<h2>Platform and trust checks</h2><p>" + link(quiz_path) + " — " + html.escape(quiz["summary"]) + "</p>"
quiz_hub["updated_at"] = stamp

for path, project_path in [("web-tech/typed-frontend-and-component-platform", projects[0]["path"]),
                           ("web-tech/browser-security-and-data-stewardship", projects[1]["path"])]:
    hub = by_path[path]
    hub["body"] += "<h2>Practice path</h2><p>Build " + link(project_path) + " and check choices in " + link(quiz_path) + ".</p>"
    hub["updated_at"] = stamp

for entry in entries:
    if entry["type"] != "article" or entry["data"].get("section_path") not in {
        "web-tech/typed-frontend-and-component-platform", "web-tech/browser-security-and-data-stewardship"
    }:
        continue
    project_path = projects[0]["path"] if entry["data"]["section_path"] == "web-tech/typed-frontend-and-component-platform" else projects[1]["path"]
    entry["body"] += "<h2>Apply and check</h2><p>Build " + link(project_path) + " and review " + link(quiz_path) + ".</p>"
    entry["data"]["related"].extend([project_path, quiz_path])
    entry["updated_at"] = stamp

root_entry = by_path["web-tech/web-technology"]
root_entry["body"] += "<h2>Platform and trust practice</h2><p>Apply frontend and data-stewardship boundaries with " + link(projects[0]["path"]) + " and " + link(projects[1]["path"]) + ".</p>"
root_entry["updated_at"] = stamp

fixture.write_text(json.dumps(entries, ensure_ascii=False, indent=2) + "\n")
print(json.dumps({"new_projects": len(projects), "new_quizzes": 1, "new_questions": len(questions)}))
