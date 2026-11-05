"""Add a Spring Boot workflow project and explained quiz to local Web Development drafts."""

import copy
import datetime
import html
import json
import subprocess
import tempfile
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


hub_path = "web-tech/spring-boot-web-service-boundaries"
lessons = [
    "web-tech/spring-boot-security-chain-and-object-permission",
    "web-tech/spring-boot-mvc-validation-and-problem-contracts",
    "web-tech/spring-boot-jpa-scope-fetch-and-page-cost",
    "web-tech/spring-boot-transaction-replay-and-outbox-handoff",
]
project_path = "web-tech/spring-boot-permit-service-boundaries-project"
quiz_path = "quizzes/web-development-spring-boot-service-contracts"
assert hub_path in by_path and all(path in by_path for path in lessons)
assert project_path not in by_path and quiz_path not in by_path

project = copy.deepcopy(by_path["web-tech/case-intake-end-to-end-project"])
project.update(id=str(uuid.uuid5(uuid.NAMESPACE_URL, "aitrove:" + project_path)), path=project_path,
               title="Project: Spring Boot Permit Service Boundaries",
               summary="Build a scoped Spring MVC permit API with bounded JPA reads and recoverable approval delivery.",
               sort_order=3775, created_at=stamp, updated_at=stamp, published_at=stamp)
project["data"] = {"subject_root": "web-tech/web-technology", "section_path": "web-tech/web-technology/project",
                   "content_format": "html", "seo_ready": False, "kind": "project", "author_path": "authors/aitrove-editorial",
                   "reading_minutes": 10, "related": [hub_path] + lessons + ["spring/spring-boot"]}
project["body"] = paragraph(
    "Build a Spring Boot permit service for reviewer 47, reviewer 81, and private permit 62. The filter chain admits authenticated reviewers to private routes, while a service checks assignment for the exact permit. An approval request carries only operation ID, expected revision, and bounded reason. A reviewer-scoped repository query returns at most 47 permit cards with district labels and attachment counts; it must not load every attachment. The approval transaction checks current assignment and revision, commits one case result, one operation outcome, and one pending outbox event. A dropped response can be retried under the same operation ID, and a crashed queue hint cannot erase the pending event."
)
project["body"] += "<h2>Build contract</h2><ul>" + "".join("<li>" + html.escape(item) + "</li>" for item in [
    "Enable method security if an annotated service method is part of the permission boundary; test the proxy path.",
    "Bind a narrow validated command DTO, then map malformed, forbidden, missing, and stale requests separately.",
    "Apply assignment scope in SQL before paging, fetch only displayed district data, and make cursor order stable.",
    "Protect the case transition with a database concurrency rule and a unique logical operation identity.",
    "Commit outbox intent with the case, then run a relay that can recover a lost after-commit wake-up.",
]) + "</ul>"
checkpoint = '''public class SpringPermitCheckpoint {
  static boolean shouldApply(long expectedRevision, long currentRevision) {
    return expectedRevision == currentRevision;
  }

  public static void main(String[] args) {
    System.out.println(shouldApply(5, 6));
    System.out.println(shouldApply(6, 6));
  }
}'''
with tempfile.TemporaryDirectory() as directory:
    source = Path(directory) / "SpringPermitCheckpoint.java"
    source.write_text(checkpoint)
    subprocess.run(["javac", str(source)], check=True, capture_output=True, text=True)
    result = subprocess.run(["java", "-cp", directory, "SpringPermitCheckpoint"], check=True, capture_output=True, text=True)
    assert result.stdout.strip() == "false\ntrue"
project["body"] += '<h2>Implementation checkpoint</h2><pre><code class="language-java">' + html.escape(checkpoint, quote=False) + "</code></pre>"
project["body"] += "<h2>Cost and boundaries</h2>" + paragraph(
    "A reviewer-scoped detail read adds an indexed assignment check but prevents a valid account from reading every case. A bounded JPA page limits parent materialization to its chosen width; district prefetch removes per-row lazy reads, while attachment aggregation avoids loading a large child collection. A Page count query may add database work when the UI needs only next-page continuation. The approval transaction holds a lock or resolves an optimistic conflict for one case, so keep provider calls outside it. Unique operation and outbox rows add storage and writes but make ambiguous retries and lost notifications inspectable. Measure SQL count, rows read, lock wait, pending-event age, and p95 latency against a representative database."
)
project["body"] += "<h2>Failure drill</h2>" + paragraph(
    "Request permit 62 as reviewer 81 despite the broad reviewer role; no private field may appear. Invoke a guarded method through a Spring bean and then by same-bean self-call to expose the proxy boundary. Submit a blank reason, extra status field, stale revision, and an unassigned reviewer; each must have the expected distinct outcome. Give one permit 620 attachments and inspect response allocations while paging through timestamp ties. Race two exact approval retries, drop a successful HTTP response, and reuse the ID with a changed reason. Raise before commit and verify both case and outbox rollback. Then commit and kill the web process before queue wake-up; the independent relay must find the pending event."
)
project["body"] += "<h2>Acceptance checks</h2><ul>" + "".join("<li>" + html.escape(item) + "</li>" for item in [
    "Reviewer role alone never grants permit 62 to reviewer 81.",
    "Invalid shape, forbidden access, missing case, and stale revision have deliberate distinct handling.",
    "The queue stays bounded without district N+1 reads or attachment hydration.",
    "One logical approval yields one committed result and one durable notification intent.",
]) + "</ul>"
project["body"] += "<h3>Common Mistakes</h3><ul><li>Assuming every annotated self-call is intercepted.</li><li>Binding a request directly to a persistence entity.</li><li>Filtering the reviewer queue only after pagination.</li><li>Equating after-commit notification with a durable outbox.</li></ul>"
project["body"] += "<h2>Related lessons</h2><p>" + "; ".join(link(path) for path in project["data"]["related"]) + ".</p>"
entries.append(project)
by_path[project_path] = project

questions = [
    ("What does an authenticated reviewer route establish?", ["Caller and broad route admission, not access to every permit", "Ownership of every permit ID", "A committed approval operation"], "The filter chain can admit a reviewer to the API, while current object assignment must be checked for the exact permit."),
    ("What is needed before relying on @PreAuthorize?", ["Method security must be enabled and reached through the Spring bean boundary", "Only a visible navigation link", "A client-supplied reviewer ID"], "Method advice depends on method security configuration and proxy interception of the invoked Spring-managed bean."),
    ("Why can a same-bean self-call miss method advice?", ["It bypasses the Spring proxy that intercepts external calls", "It always opens a new transaction", "It automatically changes the authentication"], "A direct call on this does not travel through the proxy, so the annotation alone is not proof the guard executed."),
    ("What should an approval request DTO omit?", ["Server-owned status and reviewer identity", "A bounded reason", "An expected revision"], "A narrow command accepts client-owned fields and derives identity and state transition from the server-side service."),
    ("Is a valid request shape enough to approve a permit?", ["No; current permission and revision still need service checks", "Yes; Bean Validation locks the row", "Yes; the JSON body authorizes itself"], "Field validation catches malformed input but cannot prove the caller's current assignment or case transition legality."),
    ("How should a stale expected revision be reported?", ["As a deliberate conflict distinct from malformed input", "As an automatic silent overwrite", "As a successful validation outcome"], "A stale command needs a refresh or conflict path rather than the same treatment as a blank or malformed request field."),
    ("Where should reviewer scope be applied for a paginated queue?", ["In the SQL query before the page limit", "After loading all cases into Java", "Only in the frontend card filter"], "Filtering after pagination can leak counts, waste work, and produce short pages even when later authorized cases exist."),
    ("Why not fetch every attachment for a count?", ["A large to-many collection can dominate memory and defeat bounded paging", "JPA cannot count rows", "Attachments are always public"], "A separate aggregate or maintained counter can provide the number without hydrating hundreds of child entities."),
    ("Why add permit ID after created time in page order?", ["It gives tied timestamps a stable unique position", "It turns off authorization", "It guarantees an exact total count"], "A unique tie breaker makes cursor continuation deterministic when several cases share the same creation timestamp."),
    ("What allows an exact retry after a lost HTTP response?", ["A unique operation ID, digest, and stored public result", "A disabled browser button only", "A new unrelated operation ID"], "The persisted logical operation lets the client recover the committed outcome without repeating the transition."),
    ("What must share the approval transaction?", ["Case update, operation outcome, and pending outbox row", "External email and browser rendering", "Only the request validation annotations"], "The database must commit state and delivery intent together so rollback removes both and a post-commit crash retains both."),
    ("What recovers a lost after-commit queue hint?", ["An independent relay scanning pending outbox rows", "A larger controller timeout", "Trusting the callback will rerun after restart"], "The callback can fail after commit; a durable pending row gives a later relay something to discover and deliver."),
]
balanced = []
for number, (prompt, options, explanation) in enumerate(questions):
    answer = number % 3
    reordered = [options[1], options[2]]
    reordered.insert(answer, options[0])
    balanced.append({"prompt": prompt, "options": reordered, "answer": answer, "explanation": explanation})
quiz = copy.deepcopy(by_path["quizzes/web-development-browser-contracts"])
quiz.update(id=str(uuid.uuid5(uuid.NAMESPACE_URL, "aitrove:" + quiz_path)), path=quiz_path,
            title="Web Development: Spring Boot service contracts",
            summary="Twelve explained decisions about Spring permission, validation, JPA cost, and approval recovery.",
            sort_order=3776, created_at=stamp, updated_at=stamp, published_at=stamp)
quiz["data"] = {"subject_root": "web-tech/web-technology", "section_path": "web-tech/quizzes", "content_format": "html",
                "seo_ready": False, "questions": balanced}
quiz["body"] = paragraph(quiz["summary"] + " Choose an answer, inspect the reason, and return to the related failure drill.")
quiz["body"] += "<h2>Related lessons</h2><p>" + "; ".join(link(path) for path in [hub_path] + lessons + [project_path]) + ".</p>"
entries.append(quiz)
by_path[quiz_path] = quiz

for index_path, heading, target in [
    ("web-tech/web-technology/project", "Spring Boot permit service project", project_path),
    ("web-tech/quizzes", "Spring Boot service check", quiz_path),
]:
    index = by_path[index_path]
    index["data"]["modules"][0]["lessons"].append(target)
    index["body"] += "<h2>" + heading + "</h2><p>" + link(target) + " — " + html.escape(by_path[target]["summary"]) + "</p>"
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
curriculum["body"] += "<h2>Spring Boot service practice</h2><p>" + link(project_path) + "; " + link(quiz_path) + ".</p>"
curriculum["updated_at"] = stamp
by_path["spring/spring-boot"]["body"] += "<h2>Web Development connection</h2><p>" + link(hub_path) + "; " + link(project_path) + "; " + link(quiz_path) + ".</p>"
by_path["spring/spring-boot"]["updated_at"] = stamp
fixture.write_text(json.dumps(entries, ensure_ascii=False, indent=2) + "\n")
print(json.dumps({"new_projects": 1, "new_quizzes": 1, "new_questions": len(questions)}))
