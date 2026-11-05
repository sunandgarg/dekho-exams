"""Connect advanced Web Development lessons to projects and an explained quiz."""

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
    dict(path="web-tech/account-access-recovery-project", title="Project: account access and recovery boundary",
         summary="Trace login, recovery, session revocation, and record permission as separate decisions.",
         intro="Build a small account-access service for a reviewer who needs case 47. The project has four independently testable boundaries: password verification, session issue and revocation, one-use recovery, and case-level permission. A successful password or federated identity check may create a local session, but the case route must still decide whether this reviewer may see that particular record. Keep the public recovery request response neutral for present and absent accounts. The deliverable includes a request/response contract, a storage design for short-lived tokens, and a replay test; a decorative sign-in page does not satisfy it.",
         scope=["Store a salted slow password verifier through a maintained library, apply a shared attempt budget, and create a fresh session after success.", "Issue a short-lived one-use recovery token, consume it atomically with the credential change, and apply a documented session revocation rule.", "Reject an unassigned case on both its direct page route and nested media endpoint, regardless of which sign-in method established identity."],
         code="UPDATE recovery_tokens\nSET used_at = CURRENT_TIMESTAMP\nWHERE token_digest = :token_digest\n  AND used_at IS NULL\n  AND expires_at > CURRENT_TIMESTAMP\nRETURNING account_id;",
         language="sql", cost="Password checks intentionally use CPU and memory, so an unbounded login endpoint can exhaust service capacity. Recovery token and session records add bounded storage with expiry and cleanup work. A case-permission lookup should be indexed, but revocation must reach every worker before a former session can continue to read private data.",
         checks=["Try a wrong password and an absent account; the public response must not reveal which exists.", "Race two uses of one recovery link; exactly one may change the credential.", "After recovery, replay an old session and request an unassigned case and its media URL."],
         mistakes=["Treating an account recovery link as a reusable login session.", "Accepting a case ID because the signed-in UI once displayed its link.", "Implementing a password hash format in application code instead of using a maintained verifier."],
         related=["web-tech/password-verification-and-login-budgets", "web-tech/account-recovery-and-session-revocation", "web-tech/federated-login-callback-boundary", "web-tech/session-cookie-and-csrf-boundary", "web-tech/record-level-authorization"]),
    dict(path="web-tech/webhook-contract-and-browser-verification-project", title="Project: webhook contract and browser verification",
         summary="Keep an external event safe, preserve old API clients, and prove the user journey after release.",
         intro="Build a small media-processing callback for case 47. The external processor sends an event when image 61 is ready. Verify the event's raw-body signature and freshness, record its event ID before applying a side effect, then expose the resulting image state through an API shape that an older browser client can still read. A critical browser journey opens the case URL directly and checks the visible result after a refresh. The deliverable is a running boundary trace: accepted event, duplicate event, altered payload, stale event, old client, and direct-route browser load.",
         scope=["Verify the exact raw bytes and timestamp with a configured signing key; keep the key out of client bundles and logs.", "Use a uniqueness constraint on event ID and a short acknowledgement path, moving longer conversion work to a durable queue.", "Retain the old response field during a measured compatibility window, then test old and new browser clients against the intermediate shape."],
         code="INSERT INTO received_events (event_id, event_type, received_at)\nVALUES (:event_id, :event_type, CURRENT_TIMESTAMP)\nON CONFLICT (event_id) DO NOTHING;",
         language="sql", cost="Signature verification scans the body, O(B), and event-ID retention uses storage proportional to the accepted delivery window. Browser journeys cost more than unit tests because they start the built application and real page logic. Keep a short critical route test in the release gate and use field performance evidence to check whether the image change helped real devices.",
         checks=["Send the same signed event twice; the second acknowledgement must not create a second image state.", "Change one payload byte and move the event timestamp outside the allowed window in separate tests.", "Run an old client against the expanded API, then open the case route directly in the built release."],
         mistakes=["Reconstructing JSON before signature verification.", "Assuming a successful component test proves the deployed nested route works.", "Removing an old API field while cached browser clients still depend on it."],
         related=["web-tech/signed-webhook-delivery-and-replay", "web-tech/api-evolution-and-compatibility", "web-tech/browser-journey-and-fault-tests", "web-tech/field-and-lab-performance-evidence", "web-tech/background-jobs-and-outbox"]),
]

for number, project in enumerate(projects, start=1):
    assert project["path"] not in by_path
    entry = copy.deepcopy(by_path["web-tech/case-intake-end-to-end-project"])
    entry.update(id=str(uuid.uuid5(uuid.NAMESPACE_URL, "aitrove:" + project["path"])),
                 path=project["path"], title=project["title"], summary=project["summary"],
                 sort_order=970 + number, created_at=stamp, updated_at=stamp, published_at=stamp)
    entry["data"] = {"subject_root": "web-tech/web-technology", "section_path": "web-tech/web-technology/project",
                     "content_format": "html", "seo_ready": False, "kind": "project",
                     "author_path": "authors/aitrove-editorial", "reading_minutes": 8,
                     "related": project["related"]}
    body = para(project["intro"])
    body += "<h2>Build contract</h2><ul>" + "".join(f"<li>{html.escape(item)}</li>" for item in project["scope"]) + "</ul>"
    body += f'<h2>Implementation checkpoint</h2><pre><code class="language-{project["language"]}">' + html.escape(project["code"], quote=False) + '</code></pre>'
    body += "<h2>Cost and boundaries</h2>" + para(project["cost"])
    body += "<h2>Acceptance checks</h2><ul>" + "".join(f"<li>{html.escape(item)}</li>" for item in project["checks"]) + "</ul>"
    body += "<h3>Common Mistakes</h3><ul>" + "".join(f"<li>{html.escape(item)}</li>" for item in project["mistakes"]) + "</ul>"
    body += "<h2>Related lessons</h2><p>" + "; ".join(link(path) for path in project["related"]) + ".</p>"
    entry["body"] = body
    entries.append(entry)
    by_path[entry["path"]] = entry

quiz_path = "quizzes/web-development-identity-and-integration-contracts"
quiz_spec = dict(title="Web Development: identity and integration contracts quiz",
                 summary="Twelve explained questions on recovery, callbacks, outbound fetches, webhooks, API compatibility, and browser evidence.",
                 related=["web-tech/password-verification-and-login-budgets", "web-tech/account-recovery-and-session-revocation",
                          "web-tech/federated-login-callback-boundary", "web-tech/outbound-url-and-ssrf-boundary",
                          "web-tech/signed-webhook-delivery-and-replay", "web-tech/api-evolution-and-compatibility",
                          "web-tech/browser-journey-and-fault-tests", "web-tech/field-and-lab-performance-evidence"],
                 questions=[
                     ("What should be stored for password verification?", ["The plaintext password", "A unique-salt slow verifier from a maintained facility", "A fast unsalted digest"], 1, "A deliberately costly salted verifier limits offline guessing after a database leak; plaintext and fast unsalted digests expose the account far more easily."),
                     ("A successful password check proves what?", ["Identity for this sign-in step, not case-level permission", "Permission for every case", "That the browser is free of injected script"], 0, "Authentication establishes who made the request. The service must still authorize each protected case, note, and media route for that account."),
                     ("Two reset requests use one recovery link at once. What must the server ensure?", ["Both update the password", "The newest response silently wins", "Only one atomic token claim can proceed"], 2, "A one-use token needs an atomic claim with the credential update. Otherwise separate workers can both observe it unused and accept conflicting changes."),
                     ("How should the public recovery request respond for an absent account?", ["With its stored email", "With the same neutral wording as for an existing account", "With the account's case list"], 1, "Different public messages reveal whether an account exists. A neutral response can still trigger private delivery when the account is present."),
                     ("Which callback value binds federated login to the browser that began it?", ["A checked pending state value", "The display email alone", "The case path in the URL"], 0, "The application must match the returned state to its short-lived pending flow before accepting the callback; token verification remains a separate step."),
                     ("What is still required after a federated provider verifies identity?", ["Nothing; all records are public", "Only changing the page title", "A local session and record-level permission decisions"], 2, "An external identity claim does not define the application's case assignments. Local sessions and authorization remain under the service's control."),
                     ("Why is an approved URL hostname string check insufficient for server-side fetching?", ["It costs too much CPU", "Redirects and DNS answers can lead to private destinations", "It prevents image decoding"], 1, "A textual allowlist is only an initial gate. The connector must validate actual connection targets and redirected hops, with network egress limits as another boundary."),
                     ("What bytes should a webhook signature cover?", ["The exact raw received body according to the sender's contract", "A JSON object reserialized by the receiver", "Only the event title"], 0, "Parsing and reserializing can change whitespace or field order. Verify the signature over the exact bytes defined by the delivery contract."),
                     ("A signed webhook arrives twice with one event ID. What should happen?", ["Two stored side effects", "Reject all future webhooks", "A safe acknowledgement with one effective side effect"], 2, "A valid signature says who signed the message, not whether it is new. Durable event-ID deduplication makes delivery retries safe."),
                     ("Why keep an old API response field during a rollout?", ["To prevent a cached old client from breaking before it upgrades", "To make every response private", "To avoid writing any tests"], 0, "Clients may remain open or cached while the server changes. An expanded response gives old and new clients a compatibility window."),
                     ("What makes a browser journey stronger than checking one component function?", ["A fixed sleep", "A direct route, real visible outcome, and persisted result", "A CSS selector with no user task"], 1, "A journey crosses route serving, controls, requests, and response handling. It should assert that the person's task completed, not merely that a button exists."),
                     ("How should lab and field performance results be used together?", ["Use one synthetic homepage score for every route", "Ignore real device differences", "Use lab traces for diagnosis and route-specific field data for impact"], 2, "Controlled traces help explain a suspected cause, while observations from relevant routes and devices show how often real visitors experience it."),
                 ])

assert quiz_path not in by_path
quiz = copy.deepcopy(by_path["quizzes/web-development-browser-contracts"])
quiz.update(id=str(uuid.uuid5(uuid.NAMESPACE_URL, "aitrove:" + quiz_path)), path=quiz_path,
            title=quiz_spec["title"], summary=quiz_spec["summary"], sort_order=993,
            created_at=stamp, updated_at=stamp, published_at=stamp)
quiz["data"] = {"subject_root": "web-tech/web-technology", "section_path": "web-tech/quizzes",
                "content_format": "html", "seo_ready": False,
                "questions": [{"prompt": prompt, "options": options, "answer": answer, "explanation": explanation}
                              for prompt, options, answer, explanation in quiz_spec["questions"]]}
quiz["body"] = para(quiz_spec["summary"] + " Choose a response, read the explanation, and reopen the related lesson for the failed boundary.")
quiz["body"] += "<h2>Related lessons</h2><p>" + "; ".join(link(path) for path in quiz_spec["related"]) + ".</p>"
entries.append(quiz)
by_path[quiz_path] = quiz

project_hub = by_path["web-tech/web-technology/project"]
project_hub["data"]["modules"][0]["lessons"].extend(project["path"] for project in projects)
project_hub["body"] += "<h2>Identity and integration projects</h2><ul>" + "".join(
    f'<li>{link(project["path"])} — {html.escape(project["summary"])}</li>' for project in projects) + "</ul>"
project_hub["summary"] = "Build and verify nine projects across browser, API, data, identity, integration, offline, live, and release contracts."
project_hub["updated_at"] = stamp

quiz_hub = by_path["web-tech/quizzes"]
quiz_hub["data"]["modules"][0]["lessons"].append(quiz_path)
quiz_hub["body"] += "<h2>Identity and integration checks</h2><p>" + link(quiz_path) + " — " + html.escape(quiz_spec["summary"]) + "</p>"
quiz_hub["updated_at"] = stamp

for path, project_path in [
    ("web-tech/identity-and-application-security", projects[0]["path"]),
    ("web-tech/integration-and-verification", projects[1]["path"]),
]:
    hub = by_path[path]
    hub["body"] += "<h2>Practice path</h2><p>Build " + link(project_path) + " and check decisions in " + link(quiz_path) + ".</p>"
    hub["updated_at"] = stamp

for entry in entries:
    if entry["type"] != "article" or entry["data"].get("section_path") not in {
        "web-tech/identity-and-application-security", "web-tech/integration-and-verification"
    }:
        continue
    project_path = projects[0]["path"] if entry["data"]["section_path"] == "web-tech/identity-and-application-security" else projects[1]["path"]
    entry["body"] += "<h2>Apply and check</h2><p>Build " + link(project_path) + " and review " + link(quiz_path) + ".</p>"
    entry["data"]["related"].extend([project_path, quiz_path])
    entry["updated_at"] = stamp

root_entry = by_path["web-tech/web-technology"]
root_entry["body"] += "<h2>Advanced practice</h2><p>Apply account and integration contracts with " + link(projects[0]["path"]) + " and " + link(projects[1]["path"]) + ".</p>"
root_entry["updated_at"] = stamp

fixture.write_text(json.dumps(entries, ensure_ascii=False, indent=2) + "\n")
print(json.dumps({"new_projects": len(projects), "new_quizzes": 1, "new_questions": len(quiz_spec["questions"])}))
