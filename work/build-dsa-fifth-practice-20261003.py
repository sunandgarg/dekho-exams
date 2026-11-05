"""Add practice for deletion, priority changes, tombstones, and dependencies."""

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
project_path = "dsa/warehouse-mutation-release-project"
quiz_path = "quizzes/dsa-deletion-priority-dependency-checks"
assert project_path not in by_path and quiz_path not in by_path
stamp = datetime.datetime.now(datetime.UTC).isoformat()
related = [
    "dsa/bplus-deletion-borrow-merge",
    "dsa/indexed-binary-heap-decrease-key",
    "dsa/open-addressing-tombstones-rehash",
    "dsa/dependency-graph-topological-order",
]


def links(paths):
    return "<ul>" + "".join(
        '<li><a href="/' + path + '">' + html.escape(by_path[path]["title"]) + "</a></li>"
        for path in paths
    ) + "</ul>"


project = copy.deepcopy(by_path["dsa/index-mutation-invariants-project"])
project.update(
    id=str(uuid.uuid5(uuid.NAMESPACE_URL, "aitrove:" + project_path)), path=project_path,
    title="Project: release a warehouse plan after indexed mutations",
    summary="Test page deletion, changing priorities, collision chains, and task prerequisites together.",
    sort_order=41050, created_at=stamp, updated_at=stamp, published_at=stamp,
)
project["data"].update(
    reading_minutes=17,
    related=[{"path": path, "title": by_path[path]["title"]} for path in related],
)
project["body"] = (
    "<p>A warehouse release deletes retired bay IDs, changes a delayed dispatch job's priority, removes old owner records, and orders dependent work. Each structure answers a different question. The B+ index supports ordered bay scans; an indexed heap selects the next priority; an open-addressed directory resolves bay ownership; a dependency graph prevents shipment before prerequisites. Write a test plan that checks their separate invariants after each mutation. Then define the state boundary visible to readers. Correct individual operations do not make a release atomic across four indexes.</p>"
    "<h2>Mutation contract</h2>"
    "<p>Start with bay IDs 19, 26, 31, 47, 52, 58, 61, 67, 73, and 83. Retire the first six. The remaining B+ leaf chain must scan 61, 67, 73, 83, and every nonroot page must meet its minimum occupancy. Queue J-47 at priority 9, J-52 at 6, J-61 at 12, and J-83 at 7. Decrease J-61 to 3; its removal must precede J-52. In the owner directory, 47, 58, and 69 collide under eleven slots. Removing 47 must leave both later records discoverable. Insert 80 after the removal and check it separately.</p>"
    "<h2>Dependency contract</h2>"
    "<p>Stock precedes reserve; reserve precedes pick and label; pick precedes pack; pack and label precede ship. Accept any complete order respecting those edges. Reject an added edge from ship back to stock as a cycle. Record whether the release publishes all new index roots and queue state together, or whether readers may see an intermediate state. If the system persists its records, specify the log or transaction boundary and what recovery does after a process stops between two index writes. The in-memory examples here do not supply those facilities.</p>"
    "<h2>Acceptance trace</h2><pre><code class=\"language-text\">Bay scan: 61, 67, 73, 83\nFirst dispatch: J-61 at priority 3\nOwner 58: present after deleting 47\nOwner 80: present after insertion\nShip: after pack and label\nAdded ship-to-stock edge: cycle rejected</code></pre>"
    "<h2>Cost and ownership review</h2>"
    "<p>State page capacity when assessing B+ occupancy. Count an O(k) lower bound for returning k scanned bays, even if finding the first leaf is fast. Indexed-heap priority changes are expected O(log n) with a working position map. Linear probing is expected constant time only under a suitable key distribution and controlled load; a collision run can force O(n) probing. Topological ordering scans O(V + E) tasks and edges. These costs describe in-memory algorithms. They do not include disk page writes, retries, process crashes, or coordination among concurrent writers. Those require separate acceptance tests and a documented owner of the committed state.</p>"
    "<h3>Common Mistakes</h3><ul>"
    "<li>Do not verify only the final B+ scan while leaving stale internal separators.</li>"
    "<li>Do not change a job's priority without repairing the heap and its position map.</li>"
    "<li>Do not turn a tombstone into an empty slot before the collision chain is rebuilt.</li>"
    "<li>Do not return a partial task order as success when a cycle remains.</li>"
    "<li>Do not call four separate writes one atomic release without a publication rule.</li>"
    "</ul><h2>Connected lessons</h2>" + links(related + ["dsa/index-mutation-invariants-project", "dsa/projects", "dsa/quizzes", subject_root])
)
entries.append(project)
by_path[project_path] = project

questions = [
    ("A B+ leaf falls below minimum occupancy after deletion. What is the next structural action?", ["Borrow from a sibling with spare keys, or merge", "Stop because the key is absent", "Paint the root red"], 0, "A short leaf must be repaired through sibling redistribution or merging. A merge can make the parent underfull too."),
    ("After merging B+ leaves, what must happen to the ordered scan chain?", ["Relink the surviving leaf around the removed leaf", "Leave the old pointer as a historical record", "Remove every next pointer"], 0, "Range scans follow leaf links, so a removed leaf cannot remain in the active chain even if parent child pointers are correct."),
    ("Which B+ deletion check catches routing damage that a final leaf scan may miss?", ["Each separator matches its right child's smallest key", "The first leaf has a next pointer", "The root is a leaf"], 0, "A scan can follow links and appear sorted while an outdated separator routes a point lookup to the wrong child."),
    ("Why does an indexed heap keep a job-to-array-position map?", ["To find a target job for priority updates", "To make every job durable", "To sort jobs by arrival time"], 0, "The map avoids a full heap scan before decrease-key. Every swap must update the positions of both moved jobs."),
    ("After decreasing a min-heap priority, which direction repairs the heap?", ["Rise toward the root", "Always move to the last slot", "Scan every leaf and reverse the array"], 0, "A smaller priority can violate the parent relationship, so the changed entry moves upward until its parent is no larger."),
    ("What does the pair (priority, job ID) imply for equal priorities?", ["Job ID breaks the tie", "Submission time always breaks the tie", "The heap chooses randomly"], 0, "Tuple ordering compares the job ID after equal priority. A stable arrival policy needs a separate sequence number."),
    ("Why must linear probing keep a tombstone after removing a colliding key?", ["Lookup must continue to later entries in the probe run", "Tombstones lower every hash value", "A tombstone makes the array immutable"], 0, "Making a deleted slot empty would stop a later lookup before it reaches keys displaced by the earlier collision."),
    ("When inserting into a probe run with a tombstone, when can that slot be reused?", ["After checking the rest of the run for an existing key", "Immediately, without reading later slots", "Only after every entry is removed"], 0, "A matching key may appear after the tombstone. Writing first would create a duplicate and break map update semantics."),
    ("What does a rebuild of an open-addressed table preserve?", ["Live key-value pairs while discarding tombstones", "Every old array index", "Only the newest inserted key"], 0, "Rehashing reinserts each live entry into a fresh array. Exact old positions are not part of the map's contract."),
    ("What does a task's incoming-edge count represent?", ["Unresolved prerequisites", "Number of workers currently idle", "Its priority in the heap"], 0, "Each prerequisite edge contributes one incoming count. A task becomes ready only after every predecessor is emitted."),
    ("The ready queue empties after four of six tasks. What does a topological-order routine report?", ["A dependency cycle blocks a complete order", "The four-task prefix is a complete plan", "All remaining tasks can run together"], 0, "If tasks remain but none has zero incoming edges, at least one cycle prevents a complete dependency order."),
    ("What makes a multi-index warehouse release visible as one state?", ["A documented atomic commit or version-publication boundary", "A valid topological order alone", "A smaller hash table"], 0, "Correct isolated data structures do not coordinate visibility. A shared commit or publication protocol defines which version readers see."),
]
balanced_questions = []
for number, (prompt, options, answer, explanation) in enumerate(questions):
    correct = options[answer]
    distractors = [option for index, option in enumerate(options) if index != answer]
    position = number % 3
    distractors.insert(position, correct)
    balanced_questions.append((prompt, distractors, position, explanation))
questions = balanced_questions
quiz = copy.deepcopy(by_path["quizzes/dsa-mutation-and-versioning-contracts"])
quiz.update(
    id=str(uuid.uuid5(uuid.NAMESPACE_URL, "aitrove:" + quiz_path)), path=quiz_path,
    title="Deletion, priority, and dependency checks",
    summary="Check B+ underflow, indexed-heap updates, tombstones, and cycle rejection.",
    sort_order=41060, created_at=stamp, updated_at=stamp, published_at=stamp,
)
quiz["data"].update(
    duration_minutes=15,
    related=[{"path": path, "title": by_path[path]["title"]} for path in related + [project_path]],
    questions=[{"prompt": prompt, "options": options, "answer": answer, "explanation": explanation} for prompt, options, answer, explanation in questions],
)
quiz["body"] = (
    "<p>Check what survives after deletion, what moves when priority changes, and why a dependency cycle blocks a release. Each answer names an operation contract.</p>"
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
    ("dsa/bplus-multilevel-insertion", "dsa/bplus-deletion-borrow-merge"),
    ("dsa/binary-heap-priority-scheduling", "dsa/indexed-binary-heap-decrease-key"),
    ("dsa/hash-map-collision-and-load-contract", "dsa/open-addressing-tombstones-rehash"),
    ("dsa/graph-adjacency-list-and-bfs", "dsa/dependency-graph-topological-order"),
):
    old = by_path[old_path]
    old["body"] += '<p><a href="/' + new_path + '">' + html.escape(by_path[new_path]["title"]) + "</a> continues this operation with mutation checks.</p>"
    old["updated_at"] = stamp

for path in related:
    entry = by_path[path]
    entry["body"] += '<p>Apply this operation in the <a href="/' + project_path + '">warehouse release project</a>, then check the <a href="/' + quiz_path + '">deletion and dependency quiz</a>.</p>'
    entry["updated_at"] = stamp

fixture.write_text(json.dumps(entries, ensure_ascii=False, indent=2) + "\n")
print(json.dumps({"added": [project_path, quiz_path], "questions": len(questions)}))
