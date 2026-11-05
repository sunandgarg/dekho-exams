"""Add deletion, rollback, and shortest-route practice with reciprocal links."""

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
subject_root = "dsa/dsa-tutorial-learn-data-structures-and-algorithms"
project_path = "dsa/depot-rollback-and-route-project"
quiz_path = "quizzes/dsa-tree-deletion-rollback-routes"
assert project_path not in by_path and quiz_path not in by_path
stamp = datetime.datetime.now(datetime.UTC).isoformat()
related = [
    "dsa/red-black-ordered-deletion",
    "dsa/avl-interval-index-deletion",
    "dsa/disjoint-set-rollback-checkpoints",
    "dsa/stale-entry-heap-shortest-route",
]


def links(paths):
    return "<ul>" + "".join(
        '<li><a href="/' + path + '">' + html.escape(by_path[path]["title"]) + "</a></li>"
        for path in paths
    ) + "</ul>"


project = copy.deepcopy(by_path["dsa/warehouse-mutation-release-project"])
project.update(
    id=str(uuid.uuid5(uuid.NAMESPACE_URL, "aitrove:" + project_path)), path=project_path,
    title="Project: test depot rollback, routes, and ordered deletion",
    summary="Exercise temporary links, route relaxation, and two balanced deletion contracts.",
    sort_order=41150, created_at=stamp, updated_at=stamp, published_at=stamp,
)
project["data"].update(
    reading_minutes=18,
    related=[{"path": path, "title": by_path[path]["title"]} for path in related],
)
project["body"] = (
    "<p>A depot planner evaluates a temporary bridge before approving a maintenance release. It must answer whether depots are connected under the proposed bridge, calculate a route over currently active directed roads, remove expired scheduler deadlines, and remove a booked maintenance window. Treat those as four distinct data-structure contracts. Build an independent oracle for each: a small edge list, a distance relaxation model, a sorted set of deadlines, and a plain list of windows. The production question comes later: when do readers see all accepted changes together?</p>"
    "<h2>Temporary connectivity</h2>"
    "<p>Join D-19 with D-26, then record a rollback checkpoint. Temporarily join D-26 with D-47. D-19 and D-47 must be connected under the proposal, but not after rollback. D-19 and D-26 remain connected in both states. Check the parent and size history after repeated redundant joins. A rollback token belongs to the active in-memory branch; it is not a durable revision number, and it cannot remove one old edge while preserving arbitrary later unions.</p>"
    "<h2>Routes and ordered indexes</h2>"
    "<p>Use directed roads D-19 to D-26 at 7 minutes, D-19 to D-47 at 14, D-26 to D-47 at 3, D-26 to D-52 at 8, and D-47 to D-52 at 4. The shortest route from D-19 to D-52 takes 14 minutes through D-26 and D-47. The old 14-minute heap entry for D-47 must be skipped after its distance improves to 10. Remove deadlines 26, 47, and 83 from the red-black index holding 47, 52, 61, 19, 26, 58, and 83; check order and every color path. Remove exact window [19, 26) from an AVL interval index, then query [25, 30) and require no overlap. Audit height and maximum-end metadata after the deletion.</p>"
    "<h2>Acceptance trace</h2><pre><code class=\"language-text\">Temporary D-19 to D-47: connected\nAfter rollback D-19 to D-47: disconnected\nD-19 to D-52: 14 via D-26 and D-47\nRemaining deadlines: 19, 52, 58, 61\nAfter removal [25, 30): no overlap</code></pre>"
    "<h2>Cost and state boundary</h2>"
    "<p>Union by size without path compression bounds rollback-DSU find and union by O(log n); reverting u successful unions takes O(u). Balanced tree removals take O(log n) per key and O(log n) stack space in these recursive models. The lazy shortest-path heap can hold O(E) entries for E roads; stale entries are discarded on pop. These facts do not establish a transaction. If a planner approves the proposal, specify a publication version or committed record that binds the new graph, route data, and ordered indexes. If it rejects the proposal, keep the old state visible. A process crash between separate writes needs a recovery rule; no example here supplies one.</p>"
    "<h3>Common Mistakes</h3><ul>"
    "<li>Do not enable unrecorded path compression in a rollback DSU.</li>"
    "<li>Do not process a stale heap distance as a current shortest route.</li>"
    "<li>Do not trust sorted red-black output without color and black-height checks.</li>"
    "<li>Do not leave AVL maximum-end metadata stale after deleting a window.</li>"
    "<li>Do not call a temporary checkpoint a durable published revision.</li>"
    "</ul><h2>Connected lessons</h2>" + links(related + ["dsa/index-mutation-invariants-project", "dsa/projects", "dsa/quizzes", subject_root])
)
entries.append(project)
by_path[project_path] = project

questions = [
    ("A red-black delete returns sorted keys. Which separate check is still required?", ["Equal black height and valid red-link placement", "Only the Python list length", "Only the current root key"], 0, "Search order alone cannot prove the balancing representation. Audit both black height and the red-link rules after deletion."),
    ("A deleted red-black node has two children. What happens to its successor?", ["It replaces the target key and is removed from the right subtree", "It remains in both locations", "It must become an unrelated root"], 0, "Copy the smallest right-subtree key into the target position, then remove that original successor to avoid a duplicate."),
    ("After top-down red-black deletion, what color must the surviving root have?", ["Black", "Red", "Whichever color the last rotation produced"], 0, "The public deletion operation restores a black root after temporary color moves used during descent."),
    ("An AVL interval deletion changes child pointers. Which metadata must be refreshed?", ["Height and subtree maximum end", "Only a node count", "Only the removed interval's start"], 0, "Height controls rotations, and maximum end controls overlap pruning. Both depend on the resulting child arrangement."),
    ("Why can AVL deletion need a different rotation decision from insertion?", ["The remaining child's balance determines the taller grandchild", "The removed key always identifies a new tall side", "Deletion never rotates"], 0, "After a subtree shrinks, inspect child heights to select a single or double rotation; the removed key alone is insufficient."),
    ("What does rollback DSU record for a successful union?", ["The changed parent and former root size", "A copy of every path to the root", "All graph edges ever observed"], 0, "Restoring the changed child parent and the receiving root's earlier size reverses one union in constant time."),
    ("Why does the rollback example avoid path compression?", ["Its history would not include all compressed parent changes", "Path compression makes sets disconnected", "Find would otherwise be undefined"], 0, "A compressed find mutates multiple parent links. The short union history cannot undo those unrecorded writes."),
    ("What does a checkpoint token in this DSU represent?", ["A length in the current change history", "A durable database transaction ID", "The number of graph vertices"], 0, "The token marks how many successful unions remain in one active in-memory branch. It is not a persistent revision."),
    ("A shorter route is pushed while an older heap entry remains. How is the old entry handled?", ["Discard it when its distance differs from the best recorded value", "Process it as a second current path", "Delete the destination vertex"], 0, "Lazy Dijkstra keeps duplicate heap entries and skips stale ones at removal, preserving the current shortest tentative distance."),
    ("Which road weight invalidates Dijkstra's settled-node rule?", ["A negative travel time", "A zero travel time", "A positive travel time"], 0, "Negative edges can improve a route after a vertex was treated as final. This implementation rejects them before search."),
    ("Why can the lazy shortest-path heap use O(E) space?", ["Each successful relaxation can push another entry", "Every graph has E vertices", "The heap stores the entire path text for each edge"], 0, "The queue retains superseded entries until they surface, so its size is tied to successful edge relaxations rather than only vertices."),
    ("What publishes the approved bridge and index changes as one visible state?", ["A specified commit or version-publication boundary", "The DSU checkpoint integer alone", "A valid shortest route alone"], 0, "Correct in-memory structures do not coordinate cross-index visibility. A separate publication rule decides which version readers observe."),
]
balanced_questions = []
for number, (prompt, options, answer, explanation) in enumerate(questions):
    correct = options[answer]
    distractors = [option for index, option in enumerate(options) if index != answer]
    position = number % 3
    distractors.insert(position, correct)
    balanced_questions.append((prompt, distractors, position, explanation))
questions = balanced_questions

quiz = copy.deepcopy(by_path["quizzes/dsa-deletion-priority-dependency-checks"])
quiz.update(
    id=str(uuid.uuid5(uuid.NAMESPACE_URL, "aitrove:" + quiz_path)), path=quiz_path,
    title="Tree deletion, rollback, and route checks",
    summary="Test color repair, AVL metadata, connectivity checkpoints, and stale route entries.",
    sort_order=41160, created_at=stamp, updated_at=stamp, published_at=stamp,
)
quiz["data"].update(
    duration_minutes=15,
    related=[{"path": path, "title": by_path[path]["title"]} for path in related + [project_path]],
    questions=[{"prompt": prompt, "options": options, "answer": answer, "explanation": explanation} for prompt, options, answer, explanation in questions],
)
quiz["body"] = (
    "<p>Check the structure that remains after deletion, the history retained for rollback, and the heap entry that still represents the best route.</p>"
    "<h2>Lessons</h2>" + links(related) + "<h2>Design exercise</h2>" + links([project_path, subject_root])
)
entries.append(quiz)
by_path[quiz_path] = quiz

for hub_path, destination in (("dsa/projects", project_path), ("dsa/quizzes", quiz_path)):
    hub = by_path[hub_path]
    hub["data"]["modules"][0]["lessons"].append(destination)
    hub["body"] += '<p><a href="/' + destination + '">' + html.escape(by_path[destination]["title"]) + "</a></p>"
    hub["updated_at"] = stamp
    root_module = next(module for module in by_path[subject_root]["data"]["modules"] if module["title"] == hub["title"])
    root_module["lessons"].append(destination)
    by_path[subject_root]["body"] += '<p><a href="/' + destination + '">' + html.escape(by_path[destination]["title"]) + "</a></p>"
    by_path[subject_root]["updated_at"] = stamp

for old_path, new_path in (
    ("dsa/red-black-ordered-insertion", "dsa/red-black-ordered-deletion"),
    ("dsa/avl-interval-index-insertion", "dsa/avl-interval-index-deletion"),
    ("dsa/disjoint-set-union-connectivity", "dsa/disjoint-set-rollback-checkpoints"),
    ("dsa/indexed-binary-heap-decrease-key", "dsa/stale-entry-heap-shortest-route"),
):
    old = by_path[old_path]
    old["body"] += '<p><a href="/' + new_path + '">' + html.escape(by_path[new_path]["title"]) + "</a> extends this operation.</p>"
    old["updated_at"] = stamp
for path in related:
    entry = by_path[path]
    entry["body"] += '<p>Apply this operation in the <a href="/' + project_path + '">depot rollback project</a>, then check the <a href="/' + quiz_path + '">deletion and route quiz</a>.</p>'
    entry["updated_at"] = stamp

fixture.write_text(json.dumps(entries, ensure_ascii=False, indent=2) + "\n")
print(json.dumps({"added": [project_path, quiz_path], "questions": len(questions)}))
