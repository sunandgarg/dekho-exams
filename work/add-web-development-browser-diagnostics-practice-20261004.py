"""Add a browser diagnosis project and balanced assessment."""
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


def p(value):
    return "<p>" + html.escape(value) + "</p>"


def link(path):
    assert path in by_path, path
    return '<a href="/' + path + '">' + html.escape(by_path[path]["title"]) + "</a>"


hub_path = "web-tech/browser-performance-diagnosis-and-measurement"
lessons = [
    "web-tech/field-performance-observation-and-sample-contracts",
    "web-tech/interaction-latency-traces-and-main-thread-contention",
    "web-tech/retained-dom-memory-and-lifecycle-investigation",
    "web-tech/layout-paint-regressions-and-containment-decisions",
]
project_path = "web-tech/permit-browser-regression-investigation-project"
quiz_path = "quizzes/web-development-browser-performance-diagnosis"
assert project_path not in by_path and quiz_path not in by_path

project = copy.deepcopy(by_path["web-tech/case-intake-end-to-end-project"])
project.update(id=str(uuid.uuid5(uuid.NAMESPACE_URL, "aitrove:" + project_path)), path=project_path,
               title="Project: permit browser regression investigation",
               summary="Trace a slow approval, growing photo-panel memory, and repeated table layout across a measured release.",
               sort_order=3645, created_at=stamp, updated_at=stamp, published_at=stamp)
project["data"] = {"subject_root": "web-tech/web-technology", "section_path": "web-tech/web-technology/project",
                   "content_format": "html", "seo_ready": False, "kind": "project", "author_path": "authors/aitrove-editorial",
                   "reading_minutes": 9, "related": [hub_path] + lessons}
project["body"] = p(
    "Investigate a permit portal release that looks acceptable in an aggregate dashboard but feels slow on field tablets. A reviewer opens a 620-row case table, approves a record while a filter runs, and opens and closes a photo panel 47 times. The approval feedback appears late; repeated panel use makes the tab less responsive. Build one measured investigation with a field event contract, an interaction trace, a retained-object comparison, and a rendering trace. Keep route class and release in telemetry while excluding case identifiers and complete asset paths. State the sampling fraction and sample count next to every percentile so a sparse tablet cohort is not mistaken for a fleet-wide result."
)
project["body"] += "<h2>Build contract</h2><ul>" + "".join("<li>" + html.escape(item) + "</li>" for item in [
    "Collect supported browser timing entries, record missing types, cap resource events, and treat telemetry transport failure as nonblocking.",
    "Mark one approval interaction and divide latency into input delay, handler work, and presentation delay under both idle and competing work.",
    "Run comparable photo-panel lifecycle cycles and inspect a retained path for listeners, observers, object URLs, or callback registries.",
    "Compare alternating DOM write-read updates against a batched version, then check overlays, font loading, zoom, and keyboard focus.",
]) + "</ul>"
project["body"] += '<h2>Implementation checkpoint</h2><pre><code class="language-javascript">' + html.escape(
    'function chooseInvestigation(inputDelayMs, handlerMs, presentationMs) {\n'
    '  const phases = [["input-delay", inputDelayMs], ["handler", handlerMs], ["presentation", presentationMs]];\n'
    '  phases.sort((left, right) => right[1] - left[1]);\n'
    '  return phases[0][0];\n'
    '}\n'
    'console.log(chooseInvestigation(190, 14, 106));\n'
    '// Output: input-delay', quote=False) + "</code></pre>"
project["body"] += "<h2>Cost and boundaries</h2>" + p(
    "Limit performance events by a documented per-view cap and sampling rate; collection itself consumes main-thread and network budget. A worker or chunked filter can reduce input delay but has scheduling and data-transfer cost, while immediate approval feedback needs a rollback state if the server rejects it. Memory snapshots pause or perturb the page, so use equivalent cycles and inspect retaining paths rather than comparing arbitrary heap totals. Batching row geometry avoids repeated layout, but stale widths after a font or viewport change can produce wrong placement. Paint containment may clip the photo-panel menu. Evaluate total user-visible response, not only a shorter JavaScript function."
)
project["body"] += "<h2>Failure drill</h2>" + p(
    "Disable a timing entry type and verify its absence is recorded rather than logged as zero. Block telemetry upload without preventing an approval. Start the 47,000-record filter just before the approval click, then show whether queueing or handler time dominates. Reject the approval from the server and check that optimistic feedback returns to an accurate state. Open and close the photo panel 47 times, compare retained panel objects after similar collection points, and inspect one retaining root. Finally, trigger 47 badge updates on 620 rows, test a batched measurement, and open the anchored menu at a zoomed viewport to catch accidental clipping."
)
project["body"] += "<h2>Acceptance checks</h2><ul>" + "".join("<li>" + html.escape(item) + "</li>" for item in [
    "Each field percentile includes its route cohort, release, sample count, and missing-measurement count.",
    "The slow interaction is attributed to a measured phase and retested under competing work.",
    "Panel resources release on close and late callbacks cannot revive the removed view.",
    "The table update reduces repeated layout without clipping controls or losing keyboard access.",
]) + "</ul>"
project["body"] += "<h3>Common Mistakes</h3><ul><li>Calling a metric zero when its browser entry type was unavailable.</li><li>Optimizing only the approval handler when another task delays its start.</li><li>Comparing unrelated heap snapshots or clipping a menu with containment.</li></ul>"
project["body"] += "<h2>Related lessons</h2><p>" + "; ".join(link(path) for path in project["data"]["related"]) + ".</p>"
entries.append(project)
by_path[project_path] = project

questions = [
    ("A browser does not support a requested timing entry type. What should the event say?", ["The type is missing or unsupported", "The duration was zero", "The route was instant"], 0, "An unavailable browser entry is missing evidence; treating it as zero would bias every aggregate toward a false speed improvement."),
    ("An observer starts after first paint. What should collection consider?", ["Only the latest CSS color", "Buffered delivery where supported", "A second page load for every visitor"], 1, "Buffered observation can include entries created before registration, but support and availability must still be checked."),
    ("Which field report is most interpretable?", ["One average for all devices", "A percentile with no sample count", "Percentiles by comparable route and device cohorts"], 2, "A route and device split prevents traffic-mix changes from concealing a slower experience in the field-tablet cohort."),
    ("An approval waits 190 ms before a 14 ms handler. Where is the first investigation?", ["Main-thread work ahead of the input", "The handler variable names", "The database migration log"], 0, "The largest measured interval is input delay, so shorten or schedule competing work before micro-optimizing the handler."),
    ("Why may chained promise callbacks fail to create a visible frame?", ["They delete the DOM", "Microtasks can run before rendering", "They always move work to a worker"], 1, "A run of microtasks can keep the main thread occupied before the browser gets a chance to present the next frame."),
    ("What must immediate approval feedback include when the server can reject?", ["A private image URL", "An extra CSS font", "A correction or rollback state"], 2, "Optimistic feedback can be useful, but rejection must restore truthful status and explain the failed operation."),
    ("A removed panel still appears as a retained detached node. What matters next?", ["Its path to a retaining root", "Its former background color", "The size of another tab"], 0, "The retaining path identifies the listener, closure, registry, or other owner keeping the removed view reachable."),
    ("Which comparison helps establish a panel memory leak?", ["Unrelated heap totals on two users", "Equivalent repeated cycles after warmup and collection", "One allocation spike during an image load"], 1, "Comparable lifecycle cycles and retained-object counts distinguish a steady leak from cache warmup or collection timing."),
    ("When should a panel's temporary object URL be revoked?", ["Before the image consumes it", "Only when the whole browser quits", "After the consumer is done with it"], 2, "Release belongs to the resource owner at the end of actual use; revoking too early can break the image."),
    ("A loop writes style then reads geometry for every row. What is likely to help?", ["Batch required reads before writes", "Repeat the read twice", "Add a larger image"], 0, "Separating reads from writes can avoid many forced layout calculations when the measurements do not depend on each preceding write."),
    ("What risk follows paint containment on a card with an overflowing menu?", ["The menu gains server permission", "The menu may be clipped", "The card loses every event listener"], 1, "Paint containment can clip overflowing descendants, so visible overlays need an appropriate layer and regression checks."),
    ("Layout time falls but paint time rises after a change. What follows?", ["Declare the work complete", "Ignore visual frames", "Inspect paint and user-visible frame outcome"], 2, "A faster layout phase alone does not establish a faster frame; the trace must cover the full render path."),
]
assert len(questions) == 12 and [sum(item[2] == index for item in questions) for index in range(3)] == [4, 4, 4]
quiz = copy.deepcopy(by_path["quizzes/web-development-browser-contracts"])
quiz.update(id=str(uuid.uuid5(uuid.NAMESPACE_URL, "aitrove:" + quiz_path)), path=quiz_path,
            title="Web Development: browser performance diagnosis quiz",
            summary="Twelve explained choices about browser timing, interaction phases, memory retention, and rendering cost.",
            sort_order=3646, created_at=stamp, updated_at=stamp, published_at=stamp)
quiz["data"] = {"subject_root": "web-tech/web-technology", "section_path": "web-tech/quizzes",
                "content_format": "html", "seo_ready": False,
                "questions": [{"prompt": prompt, "options": options, "answer": answer, "explanation": explanation}
                              for prompt, options, answer, explanation in questions]}
quiz["body"] = p(quiz["summary"] + " Choose an answer, inspect the explanation, and return to the lesson behind a missed decision.")
quiz["body"] += "<h2>Related lessons</h2><p>" + "; ".join(link(path) for path in [hub_path] + lessons + [project_path]) + ".</p>"
entries.append(quiz)
by_path[quiz_path] = quiz

project_hub = by_path["web-tech/web-technology/project"]
project_hub["data"]["modules"][0]["lessons"].append(project_path)
project_hub["body"] += "<h2>Browser diagnosis project</h2><p>" + link(project_path) + " — " + html.escape(project["summary"]) + "</p>"
project_hub["updated_at"] = stamp
quiz_hub = by_path["web-tech/quizzes"]
quiz_hub["data"]["modules"][0]["lessons"].append(quiz_path)
quiz_hub["body"] += "<h2>Browser diagnosis check</h2><p>" + link(quiz_path) + " — " + html.escape(quiz["summary"]) + "</p>"
quiz_hub["updated_at"] = stamp
hub = by_path[hub_path]
hub["body"] += "<h2>Practice and check</h2><p>Build " + link(project_path) + " and review " + link(quiz_path) + ".</p>"
hub["updated_at"] = stamp
for path in lessons:
    entry = by_path[path]
    entry["body"] += "<h2>Apply and check</h2><p>Build " + link(project_path) + " and review " + link(quiz_path) + ".</p>"
    entry["data"]["related"].extend([project_path, quiz_path])
    entry["updated_at"] = stamp
curriculum = by_path["web-tech/web-technology"]
curriculum["body"] += "<h2>Browser diagnosis practice</h2><p>" + link(project_path) + "; " + link(quiz_path) + ".</p>"
curriculum["updated_at"] = stamp
fixture.write_text(json.dumps(entries, ensure_ascii=False, indent=2) + "\n")
print(json.dumps({"new_projects": 1, "new_quizzes": 1, "new_questions": 12}))
