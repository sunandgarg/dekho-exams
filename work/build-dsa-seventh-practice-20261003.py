"""Add a release exercise and checked questions for operational structures."""

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
project_path = "dsa/reversible-depot-release-project"
quiz_path = "quizzes/dsa-offline-queue-snapshot-recovery"
assert project_path not in by_path and quiz_path not in by_path
stamp = datetime.datetime.now(datetime.UTC).isoformat()
related = [
    "dsa/offline-connectivity-edge-lifetimes",
    "dsa/bounded-queue-close-and-drain",
    "dsa/immutable-index-snapshot-publication",
    "dsa/page-redo-journal-recovery-model",
]


def links(paths):
    return "<ul>" + "".join(
        '<li><a href="/' + path + '">' + html.escape(by_path[path]["title"]) + "</a></li>"
        for path in paths
    ) + "</ul>"


project = copy.deepcopy(by_path["dsa/depot-rollback-and-route-project"])
project.update(
    id=str(uuid.uuid5(uuid.NAMESPACE_URL, "aitrove:" + project_path)), path=project_path,
    title="Project: plan a reversible depot release",
    summary="Separate a batch connectivity answer, queue shutdown, in-memory publication, and page replay.",
    sort_order=41250, created_at=stamp, updated_at=stamp, published_at=stamp,
)
project["data"].update(
    reading_minutes=19,
    related=[{"path": path, "title": by_path[path]["title"]} for path in related],
)
project["body"] = (
    "<p>A depot release retires a temporary bridge, stops new dispatch work, and publishes new bay ownership with matching repair windows. Model each operation at its actual boundary. The edge timeline is a known batch of add, remove, and ask events. The queue is an in-process FIFO with a close state. The paired indexes are immutable snapshots published under one process lock. A page redo list demonstrates which committed changes replay after a simulated interruption. These four mechanisms answer different questions; none alone supplies a durable multi-process transaction.</p>"
    "<h2>Connectivity and queue contract</h2>"
    "<p>Process six timeline events: add D-19 to D-26; ask whether D-19 reaches D-47; add D-26 to D-47; ask again; remove that second edge; ask once more. Require false, true, false. Reject adding the same active edge twice and removing an inactive edge. Next, fill a two-slot dispatch queue with J-47 and J-52. A nonblocking third offer fails. Close the queue, then drain J-47 and J-52 in order before a final take signals closure. Test a blocked producer and a blocked consumer separately: both must wake when the queue closes, with the producer's new offer rejected.</p>"
    "<h2>Publication and replay contract</h2>"
    "<p>Capture an inventory snapshot containing bays 47 and 52. Retire 47 and add 61 with [47, 58) as its repair window. A reader retaining the old snapshot still sees 47; a new reader sees version 2 with 52 and 61. An orphan window must fail before publication. For page replay, record one committed update to P-19 and P-26, then an unfinished update to P-52. Recovery from the checkpoint applies only the committed group. State the missing storage guarantees: the Python list has no durable flush order, torn-record validation, or undo for a page that was written before its transaction committed.</p>"
    "<h2>Acceptance trace</h2><pre><code class=\"language-text\">D-19 to D-47 by event: false, true, false\nThird queued job: refused; accepted jobs drain before closed\nOld bays: 47, 52; new bays: 52, 61\nRecovered pages: P-19, P-26; unfinished P-52 absent</code></pre>"
    "<h2>Cost and boundary review</h2>"
    "<p>For Q events and I active-edge intervals, time-tree assignment stores O(I log Q) interval references. Union-by-size rollback adds logarithmic find cost without path compression. Queue insertion and removal take O(1) work while holding a lock, but blocking time has no fixed bound. Full map-copy publication takes O(B + W) time and memory for B bays and W windows per retained version. Journal replay scans its records and committed updates linearly. These costs describe the shown algorithms. A production release needs explicit durable ordering, a commit record that survives power loss, and a rule for readers in other processes. Write separate tests for those requirements.</p>"
    "<h3>Common Mistakes</h3><ul>"
    "<li>Do not answer an online edge update with a batch algorithm that assumes future events are known.</li>"
    "<li>Do not leave blocked queue threads asleep when close changes the state they await.</li>"
    "<li>Do not mutate a value object inside an old shallow snapshot.</li>"
    "<li>Do not replay an unfinished page group as committed.</li>"
    "<li>Do not mistake a consistent in-process pointer swap for power-loss durability.</li>"
    "</ul><h2>Connected lessons</h2>" + links(related + ["dsa/warehouse-mutation-release-project", "dsa/projects", "dsa/quizzes", subject_root])
)
entries.append(project)
by_path[project_path] = project

questions = [
    ("When is a time-tree connectivity method suitable?", ["When the complete add, remove, and ask sequence is known before processing", "When each edge must be removed online before the next event arrives", "Only when the graph has no vertices"], 0, "The edge-lifetime intervals require future removal positions. The method answers a known batch rather than a live stream."),
    ("Where is one active edge interval stored in a time segment tree?", ["In nodes whose ranges partition the interval", "Only in the last query leaf", "In every leaf of the entire timeline"], 0, "A range decomposition places the edge in a logarithmic number of covering nodes, then rollback removes it after each branch."),
    ("What restores DSU state after visiting a time-tree branch?", ["Rolling back to the checkpoint taken before its edge unions", "Compressing every parent path", "Discarding every graph vertex"], 0, "The branch applies its active edges, answers its leaves, and pops union changes until the earlier history length returns."),
    ("What must a bounded queue do when close occurs while a producer waits on full capacity?", ["Wake the producer and reject a new offer", "Keep the producer asleep indefinitely", "Silently increase capacity"], 0, "Close changes the producer's waiting condition. A broadcast wakes it so the offer can report that intake has ended."),
    ("How does the shown queue treat accepted items after close?", ["It drains them in FIFO order before signaling closure", "It deletes them immediately", "It marks them durably complete"], 0, "The deque retains accepted work until consumers remove it. Closure stops new offers but does not acknowledge processing."),
    ("Why is a condition wait inside a while loop?", ["The state can differ after wakeup, so the predicate must be checked again", "A loop makes the deque persistent", "A loop avoids holding any lock"], 0, "A wakeup does not reserve the needed item or slot. The thread rechecks the guarded condition after reacquiring the lock."),
    ("What does the snapshot store publish in one pointer change?", ["A validated pair of bay and repair-window maps", "One bay map while the window map is still being edited", "A disk transaction shared across machines"], 0, "Both maps are copied and checked before one current-snapshot reference is replaced under the lock."),
    ("Why can an old snapshot still be read after publication?", ["The reader retains its earlier immutable snapshot reference", "Every old read is redirected to new mutable maps", "The writer overwrites old tuple values"], 0, "The writer creates new maps and leaves the old mapping views intact for readers holding the old version."),
    ("What limitation does a shallow mapping view retain?", ["Mutable objects stored as values can still change", "Keys are always lost on read", "It cannot hold integers"], 0, "The view blocks changes to the mapping itself. A list or other mutable value inside it would need its own freezing rule."),
    ("What makes a pending page group eligible for redo in this model?", ["A matching commit marker appears after its page records", "A begin marker appears without page records", "Its transaction ID has the highest number"], 0, "Replay holds page changes in a pending map and applies them only when the transaction's commit record is read."),
    ("Which failure is outside the in-memory redo-list model?", ["A torn durable record or an uncommitted data page already flushed to disk", "An unfinished group with no commit marker", "Two page records in one committed group"], 0, "The model can ignore unfinished in-memory records, but it has no physical flush, record validation, or undo protocol."),
    ("Which statement correctly separates publication and durability?", ["One in-process snapshot swap gives coherent local reads, while power-loss safety needs a storage protocol", "A pointer swap alone survives power loss", "A queue close commits disk pages"], 0, "Atomic visibility to local readers and persistence across crashes are separate guarantees with different mechanisms."),
]
balanced_questions = []
for number, (prompt, options, answer, explanation) in enumerate(questions):
    correct = options[answer]
    distractors = [option for index, option in enumerate(options) if index != answer]
    position = number % 3
    distractors.insert(position, correct)
    balanced_questions.append((prompt, distractors, position, explanation))
questions = balanced_questions

quiz = copy.deepcopy(by_path["quizzes/dsa-tree-deletion-rollback-routes"])
quiz.update(
    id=str(uuid.uuid5(uuid.NAMESPACE_URL, "aitrove:" + quiz_path)), path=quiz_path,
    title="Offline connectivity, queue, snapshot, and recovery checks",
    summary="Test edge lifetimes, closure, version visibility, and committed page replay.",
    sort_order=41260, created_at=stamp, updated_at=stamp, published_at=stamp,
)
quiz["data"].update(
    duration_minutes=16,
    related=[{"path": path, "title": by_path[path]["title"]} for path in related + [project_path]],
    questions=[{"prompt": prompt, "options": options, "answer": answer, "explanation": explanation} for prompt, options, answer, explanation in questions],
)
quiz["body"] = (
    "<p>Choose the guarantee actually supplied by each data structure. Keep batch knowledge, in-process visibility, and durable recovery separate.</p>"
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
    ("dsa/disjoint-set-rollback-checkpoints", "dsa/offline-connectivity-edge-lifetimes"),
    ("dsa/bounded-thread-queue-acknowledgment", "dsa/bounded-queue-close-and-drain"),
    ("dsa/persistent-segment-tree-versioned-sums", "dsa/immutable-index-snapshot-publication"),
    ("dsa/bplus-deletion-borrow-merge", "dsa/page-redo-journal-recovery-model"),
):
    old = by_path[old_path]
    old["body"] += '<p><a href="/' + new_path + '">' + html.escape(by_path[new_path]["title"]) + "</a> extends this operational boundary.</p>"
    old["updated_at"] = stamp
for path in related:
    entry = by_path[path]
    entry["body"] += '<p>Apply this contract in the <a href="/' + project_path + '">reversible depot release project</a>, then check the <a href="/' + quiz_path + '">operations quiz</a>.</p>'
    entry["updated_at"] = stamp

fixture.write_text(json.dumps(entries, ensure_ascii=False, indent=2) + "\n")
print(json.dumps({"added": [project_path, quiz_path], "questions": len(questions)}))
