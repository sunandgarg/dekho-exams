"""Add React review queue project and assessment drafts."""
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


hub_path = "web-tech/react-state-and-rendering-boundaries"
lessons = [
    "web-tech/react-component-identity-and-keyed-draft-lifetime",
    "web-tech/react-derived-state-and-event-ownership",
    "web-tech/react-urgent-input-and-transition-work",
    "web-tech/react-hydration-and-stable-first-render",
]
project_path = "web-tech/react-permit-review-queue-state-project"
quiz_path = "quizzes/web-development-react-state-rendering"
assert project_path not in by_path and quiz_path not in by_path

project = copy.deepcopy(by_path["web-tech/case-intake-end-to-end-project"])
project.update(id=str(uuid.uuid5(uuid.NAMESPACE_URL, "aitrove:" + project_path)), path=project_path,
               title="Project: React permit review queue state",
               summary="Keep case drafts attached to the right record while search, approval, and hydration cross distinct boundaries.",
               sort_order=3655, created_at=stamp, updated_at=stamp, published_at=stamp)
project["data"] = {"subject_root": "web-tech/web-technology", "section_path": "web-tech/web-technology/project",
                   "content_format": "html", "seo_ready": False, "kind": "project", "author_path": "authors/aitrove-editorial",
                   "reading_minutes": 9, "related": [hub_path] + lessons}
project["body"] = p(
    "Build a React permit queue for cases 29, 47, 62, and 81. A reviewer can search 47,000 summaries, open a case, write a private note, and approve it. The first page view comes from server-rendered markup. The queue must keep a note attached to its case when new records are inserted or sorting changes. Switching cases must not copy the previous note into a new case; if drafts should survive, persist them by case ID before the editor resets. The search box should follow typing promptly while its result list catches up. A saved browser filter can apply after hydration, but the first client render must agree with the server snapshot. Approval is a user command and must never fire merely because restored state says approved."
)
project["body"] += "<h2>Build contract</h2><ul>" + "".join("<li>" + html.escape(item) + "</li>" for item in [
    "Key queue rows by immutable case ID and key only the editor subtree whose case ownership changes.",
    "Derive visible cases and count from source cases plus the search phrase; send approval only from an explicit command path.",
    "Keep input text urgent, allow result rendering to lag, and reject responses from an older search generation.",
    "Pass a versioned server snapshot into the first client render; apply browser-only preferences after hydration.",
]) + "</ul>"
project["body"] += '<h2>Implementation checkpoint</h2><pre><code class="language-javascript">' + html.escape(
    'function selectCurrentSearch(responseGeneration, activeGeneration, responseCases) {\n'
    '  return responseGeneration === activeGeneration ? responseCases : null;\n'
    '}\n'
    'console.log(selectCurrentSearch(62, 81, [{ id: 47 }]));\n'
    '// Output: null', quote=False) + "</code></pre>"
project["body"] += "<h2>Cost and boundaries</h2>" + p(
    "Keying the editor by case ID can remount an expensive subtree and remove focus; it should be the smallest boundary that matches draft ownership. A draft store consumes memory and must clear records after submission, logout, or expiry. Calculating a filtered list during render is simpler than synchronizing another copy through an effect, but 47,000 records may justify a measured memo, index, worker, or windowed view. A transition can prioritize keystrokes over result rendering; it cannot interrupt one long synchronous calculation or fix a stale network response. A server snapshot adds response bytes and requires safe serialization. Applying browser preferences after hydration may add a second visible render, so design that change plainly."
)
project["body"] += "<h2>Failure drill</h2>" + p(
    "Type a note for case 47, insert case 29 ahead of it, reverse the sort, and confirm the note's owner remains 47. Switch to case 81 and back; verify the declared discard or preservation rule. Change only a toolbar label and check that note focus remains. Restore an approved record from a saved snapshot without sending an approval request. Type search phrases that issue generations 62 and 81, return generation 81 first, then return 62; the older list must be ignored. Delay the bundle, hydrate under a different time zone and saved filter, and compare server HTML with the first client render. Finally, reject an approval and check that the visible state becomes truthful again."
)
project["body"] += "<h2>Acceptance checks</h2><ul>" + "".join("<li>" + html.escape(item) + "</li>" for item in [
    "A reorder never moves a draft or pending result to a different case ID.",
    "Visible count and rows agree during typing, refresh, and server rejection.",
    "Input response and settled-result time are measured separately on a modest device.",
    "The first client render matches server markup before local preferences apply.",
]) + "</ul>"
project["body"] += "<h3>Common Mistakes</h3><ul><li>Using row index keys in a sortable queue.</li><li>Posting mutations from an effect that watches a restored flag.</li><li>Assuming a transition orders network replies or repairs hydration mismatch.</li></ul>"
project["body"] += "<h2>Related lessons</h2><p>" + "; ".join(link(path) for path in project["data"]["related"]) + ".</p>"
entries.append(project)
by_path[project_path] = project

questions = [
    ("A new case enters a sorted queue. Which row key keeps drafts with their records?", ["Immutable case ID", "Current array index", "A fresh random value"], 0, "The case ID represents the entity across insertions and sorting, so React can keep each row's state with its owner."),
    ("When should a keyed editor intentionally remount?", ["Whenever the parent label changes", "When the selected case identity changes", "At every keyboard event"], 1, "A case ID key can make a new editor instance when ownership changes, while unrelated parent updates preserve input."),
    ("Will changing an editor key preserve an unsent note for later?", ["Yes, automatically in React", "Only if the row index stays stable", "No; save the draft under its case ID first"], 2, "A changed key resets local state; any required recovery needs a separate owned draft store or persistence path."),
    ("Where should a filtered case count be computed from current cases and phrase?", ["During render from those inputs", "In a second effect-synchronized state", "In a random key"], 0, "Deriving the count with the visible rows avoids an intermediate render where the count and list disagree."),
    ("An approved flag arrives in a restored snapshot. Should an effect send approval?", ["Yes, every time it renders", "No; approval belongs to a user command", "Only when the list is sorted"], 1, "A restored value is data, not proof that the user has just issued a command to create a server side effect."),
    ("When is memoizing a filtered list justified?", ["For every three-row list", "Whenever an effect was removed", "When measured render cost warrants a cache"], 2, "Memoization adds dependency and storage work; correctness comes from deriving current inputs, while measurement supports caching."),
    ("Which update should stay urgent while result rendering is transitioned?", ["The controlled input text", "A large result grid only", "An old response generation"], 0, "The typed text should follow the user's keystroke immediately even when rendering a large result view can lag."),
    ("Does a transition move a costly synchronous filter off the main thread?", ["Always", "No; the computation needs its own solution", "Only when keys are random"], 1, "Render priority does not make a blocking JavaScript calculation run on another thread or become preemptible."),
    ("An older network search returns after the newer one. Which result may publish?", ["Both, in arrival order", "The older one because it started first", "Only the currently relevant generation"], 2, "Scheduling priority does not order network responses; the request layer must reject stale generations."),
    ("What must the first client render use when hydrating server HTML?", ["The same initial snapshot and stable formatting", "A new random timestamp", "A local filter read during render"], 0, "Hydration expects the first browser output to agree with the server HTML before browser-only preferences change it."),
    ("When can a saved browser preference safely change the server-rendered queue?", ["Before the first client render differs", "After hydration as an intentional update", "Only during a server database write"], 1, "Applying a browser-only preference after the matching first render preserves the server and client agreement boundary."),
    ("What should happen to a hydration mismatch warning?", ["Always silence it", "Treat it as a formatting feature", "Find and correct the unstable first-render value"], 2, "A warning can signal different initial content or associations; fixing its source is safer than suppressing it broadly."),
]
assert len(questions) == 12 and [sum(item[2] == index for item in questions) for index in range(3)] == [4, 4, 4]
quiz = copy.deepcopy(by_path["quizzes/web-development-browser-contracts"])
quiz.update(id=str(uuid.uuid5(uuid.NAMESPACE_URL, "aitrove:" + quiz_path)), path=quiz_path,
            title="Web Development: React state and rendering quiz",
            summary="Twelve explained choices about keyed identity, derived values, transitions, and hydration.",
            sort_order=3656, created_at=stamp, updated_at=stamp, published_at=stamp)
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
project_hub["body"] += "<h2>React review queue project</h2><p>" + link(project_path) + " — " + html.escape(project["summary"]) + "</p>"
project_hub["updated_at"] = stamp
quiz_hub = by_path["web-tech/quizzes"]
quiz_hub["data"]["modules"][0]["lessons"].append(quiz_path)
quiz_hub["body"] += "<h2>React rendering check</h2><p>" + link(quiz_path) + " — " + html.escape(quiz["summary"]) + "</p>"
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
curriculum["body"] += "<h2>React rendering practice</h2><p>" + link(project_path) + "; " + link(quiz_path) + ".</p>"
curriculum["updated_at"] = stamp
fixture.write_text(json.dumps(entries, ensure_ascii=False, indent=2) + "\n")
print(json.dumps({"new_projects": 1, "new_quizzes": 1, "new_questions": 12}))
