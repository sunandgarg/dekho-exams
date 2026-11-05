"""Add a case-mutation project and explained API contract quiz."""

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


project = dict(path="web-tech/conflict-safe-case-api-project", title="Project: conflict-safe case API",
               summary="Build a case mutation route with conditional writes, bounded retries, durable report operations, and structured errors.",
               intro="Implement a case-review API for reviewers 29 and 31. Both may open case 47 at version 62, but the second save must not erase the first. Return a strong validator with the case representation and require it for a mutation. Compare version and update the stored case atomically, then return a new validator. For a report over 62 cases, persist a durable operation and enqueue intent before returning an accepted response; let its owner inspect a status resource later. Add one downstream analysis call with an overall deadline and a bounded retry policy. The client must preserve unsaved notes after a conflict or network uncertainty. Error bodies must identify recovery paths without copying private notes, credentials, or internal exceptions.",
               scope=["Require a current If-Match validator on case writes and reject missing or stale conditions without a partial update.", "Give analysis requests one retry owner, a deadline, and a stable idempotency key when commit outcome is uncertain.", "Return a report operation path only after its record and enqueue intent are durable; authorize status reads and result links.", "Use distinct HTTP status and machine codes for conflict, validation, denial, and temporary dependency failure."],
               code='function saveDecision(ifMatch, currentVersion) {\n  if (ifMatch === null) return 428;\n  if (ifMatch !== `"case-47-v${currentVersion}"`) return 412;\n  return 200;\n}\nconsole.log(saveDecision(`"case-47-v62"`, 63));\n// Output: 412',
               cost="An atomic version comparison adds little work to a keyed record update, but the UI needs a real conflict path. Retry attempts consume dependency capacity and can multiply under layered clients, so cap them within one deadline. Durable operation records and status polling add storage and request traffic; they are justified when work survives a request or browser session. A stable error code registry costs maintenance but prevents clients from parsing changing human prose. Record each operation's owner and expiry instead of treating a hard-to-guess identifier as permission.",
               failure="Run two saves from version 62 at the same time; only one may apply. Pause the server between a separate version read and write to prove an unchecked implementation can lose data, then move the condition into the atomic write. Drop the downstream response after an accepted analysis request; a repeated call with the same key must not start a second job. Restart the API immediately after responding to a report request; its status resource must still exist. Finally return each planned error and verify that the browser neither reports success nor discards the user's draft on failure.",
               checks=["A missing or stale validator prevents a write and keeps the rejected draft available for recovery.", "A timeout after commit and a bounded retry do not duplicate the downstream effect.", "A report operation survives process restart and only its authorized owner reads status and output.", "Error status and machine code identify recovery while responses omit raw private data."],
               mistakes=["Checking a version before an unconditional update.", "Retrying an uncertain mutation without an idempotency contract.", "Returning accepted before writing the operation record.", "Sending status 200 with a free-text error for a failed save."],
               related=["web-tech/conditional-writes-and-lost-update-prevention", "web-tech/request-deadlines-retries-and-backoff", "web-tech/accepted-operations-and-status-resources", "web-tech/structured-api-errors-and-recovery", "web-tech/idempotent-write-requests"])

assert project["path"] not in by_path
entry = copy.deepcopy(by_path["web-tech/case-intake-end-to-end-project"])
entry.update(id=str(uuid.uuid5(uuid.NAMESPACE_URL, "aitrove:" + project["path"])),
             path=project["path"], title=project["title"], summary=project["summary"],
             sort_order=1050, created_at=stamp, updated_at=stamp, published_at=stamp)
entry["data"] = {"subject_root": "web-tech/web-technology", "section_path": "web-tech/web-technology/project",
                 "content_format": "html", "seo_ready": False, "kind": "project",
                 "author_path": "authors/aitrove-editorial", "reading_minutes": 8, "related": project["related"]}
body = para(project["intro"])
body += "<h2>Build contract</h2><ul>" + "".join(f"<li>{html.escape(item)}</li>" for item in project["scope"]) + "</ul>"
body += '<h2>Implementation checkpoint</h2><pre><code class="language-javascript">' + html.escape(project["code"], quote=False) + "</code></pre>"
body += "<h2>Cost and boundaries</h2>" + para(project["cost"])
body += "<h2>Failure drill</h2>" + para(project["failure"])
body += "<h2>Acceptance checks</h2><ul>" + "".join(f"<li>{html.escape(item)}</li>" for item in project["checks"]) + "</ul>"
body += "<h3>Common Mistakes</h3><ul>" + "".join(f"<li>{html.escape(item)}</li>" for item in project["mistakes"]) + "</ul>"
body += "<h2>Related lessons</h2><p>" + "; ".join(link(path) for path in project["related"]) + ".</p>"
entry["body"] = body
entries.append(entry)
by_path[entry["path"]] = entry

quiz_path = "quizzes/web-development-api-mutation-contracts"
questions = [
    ("What prevents a second reviewer from silently overwriting a newer case edit?", ["An atomic conditional write using the observed validator", "A longer browser timeout", "A smaller font"], 0, "The client sends its observed version and the server compares it in the same atomic operation that changes the record. A separate precheck leaves a race."),
    ("What should happen when a required write precondition is missing?", ["Apply the update anyway", "Return a distinct required-precondition response", "Pretend the case does not exist"], 1, "A missing validator differs from a stale validator. The client needs to know it must obtain a current representation before attempting the mutation."),
    ("A client sends an old If-Match validator. What is the safe response?", ["Overwrite the record", "Retry automatically with the newest validator", "Reject the write and provide a conflict recovery path"], 2, "A stale validator means the client made its decision from old state. Automatically retrying against the newest state can recreate the lost-update problem."),
    ("What does a caller timeout prove about a mutation?", ["Only that the caller stopped waiting", "That the server certainly rolled back", "That the browser cleared its cache"], 0, "The response may be lost after the server committed. A safe retry needs an idempotency contract or a status lookup for uncertain outcomes."),
    ("When is a retry eligible?", ["For every status forever", "When the operation is repeat-safe, the error is transient, and budget remains", "Whenever the user clicks twice"], 1, "A bounded retry uses a plausible transient failure, safe repeat behavior, and a remaining deadline. Validation and version conflicts need correction, not backoff."),
    ("Why avoid independent retry loops at every layer?", ["They make CSS slower", "They remove authorization", "They can multiply requests during an outage"], 2, "Browser, gateway, and downstream retries can compound into many attempts for one user action. Give one layer ownership of the total attempt budget."),
    ("What must exist before an API returns accepted for a long report?", ["A durable operation and enqueue intent", "Only an in-memory callback", "A completed report file"], 0, "Acceptance means the service has taken responsibility for later work. Persist the operation and enqueue intent before responding so a process restart cannot lose it."),
    ("What should a status resource distinguish?", ["Only success and everything else", "Queued, running, succeeded, failed, and cancellation outcomes", "The user's browser width"], 1, "A client needs an honest state after the first request ends. Terminal failure and cancellation must not remain indistinguishable from running forever."),
    ("What grants access to a report status resource?", ["Knowing a numeric operation ID", "Holding any case validator", "Current authorization for that operation"], 2, "An identifier locates the operation; it is not authority. The status endpoint and final result link must check the caller's current rights."),
    ("What should a failed save return at the HTTP layer?", ["An appropriate non-success status", "Always 200 with success:false", "A redirect to a font file"], 0, "A non-success HTTP status lets clients, monitoring, and intermediaries distinguish failure from a completed mutation. The body can then describe the recovery path."),
    ("Which field should a client use for stable recovery branching?", ["A localized sentence only", "A stable machine-readable code", "A raw stack trace"], 1, "Human wording can change or be localized. A documented machine code and appropriate HTTP status keep client behavior stable across message edits."),
    ("What belongs in a public error detail?", ["The full private note", "A database stack trace", "A safe explanation that helps the user recover"], 2, "The response may be visible to clients and logs. Keep detail useful but omit credentials, private record content, and internal exception data."),
]

def varied_item(number, question):
    prompt, options, answer, explanation = question
    shift = (number * 2) % len(options)
    return {"prompt": prompt, "options": options[shift:] + options[:shift],
            "answer": (answer - shift) % len(options), "explanation": explanation}


assert quiz_path not in by_path
quiz = copy.deepcopy(by_path["quizzes/web-development-browser-contracts"])
quiz.update(id=str(uuid.uuid5(uuid.NAMESPACE_URL, "aitrove:" + quiz_path)), path=quiz_path,
            title="Web Development: API mutation contracts quiz",
            summary="Twelve explained decisions about conditional writes, retry safety, durable operations, and recoverable errors.",
            sort_order=1055, created_at=stamp, updated_at=stamp, published_at=stamp)
quiz["data"] = {"subject_root": "web-tech/web-technology", "section_path": "web-tech/quizzes",
                "content_format": "html", "seo_ready": False,
                "questions": [varied_item(number, question) for number, question in enumerate(questions)]}
quiz["body"] = para(quiz["summary"] + " Choose one response, inspect its explanation, and return to the related lesson for a missed boundary.")
quiz["body"] += "<h2>Related lessons</h2><p>" + "; ".join(link(path) for path in project["related"]) + ".</p>"
entries.append(quiz)
by_path[quiz_path] = quiz

project_hub = by_path["web-tech/web-technology/project"]
project_hub["data"]["modules"][0]["lessons"].append(project["path"])
project_hub["body"] += "<h2>API mutation project</h2><p>" + link(project["path"]) + " — " + html.escape(project["summary"]) + "</p>"
project_hub["summary"] = "Build and verify eighteen projects across browser, API, data, identity, search, quality, layout, runtime, accessibility, localization, privacy, offline, live, and release contracts."
project_hub["updated_at"] = stamp

quiz_hub = by_path["web-tech/quizzes"]
quiz_hub["data"]["modules"][0]["lessons"].append(quiz_path)
quiz_hub["body"] += "<h2>API mutation checks</h2><p>" + link(quiz_path) + " — " + html.escape(quiz["summary"]) + "</p>"
quiz_hub["updated_at"] = stamp

hub = by_path["web-tech/api-mutation-and-failure-contracts"]
hub["body"] += "<h2>Practice path</h2><p>Build " + link(project["path"]) + " and check decisions in " + link(quiz_path) + ".</p>"
hub["updated_at"] = stamp

for lesson_path in ["web-tech/conditional-writes-and-lost-update-prevention", "web-tech/request-deadlines-retries-and-backoff",
                    "web-tech/accepted-operations-and-status-resources", "web-tech/structured-api-errors-and-recovery"]:
    lesson = by_path[lesson_path]
    lesson["body"] += "<h2>Apply and check</h2><p>Build " + link(project["path"]) + " and review " + link(quiz_path) + ".</p>"
    lesson["data"]["related"].extend([project["path"], quiz_path])
    lesson["updated_at"] = stamp

root_entry = by_path["web-tech/web-technology"]
root_entry["body"] += "<h2>API mutation practice</h2><p>Apply conditional writes, retry budgets, and status resources with " + link(project["path"]) + ".</p>"
root_entry["updated_at"] = stamp

fixture.write_text(json.dumps(entries, ensure_ascii=False, indent=2) + "\n")
print(json.dumps({"new_projects": 1, "new_quizzes": 1, "new_questions": len(questions)}))
