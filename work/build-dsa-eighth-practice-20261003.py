"""Add an operational project, checked quiz, and reciprocal DSA paths."""

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
project_path = "dsa/live-depot-index-recovery-project"
quiz_path = "quizzes/dsa-online-persistence-journal-cas"
assert project_path not in by_path and quiz_path not in by_path
stamp = datetime.datetime.now(datetime.UTC).isoformat()
related = [
    "dsa/online-connectivity-after-edge-removal",
    "dsa/persistent-ordered-index-path-copying",
    "dsa/framed-journal-torn-tail-recovery",
    "dsa/cas-queue-link-help-and-reclamation",
]


def links(paths):
    return "<ul>" + "".join(
        '<li><a href="/' + path + '">' + html.escape(by_path[path]["title"]) + "</a></li>"
        for path in paths
    ) + "</ul>"


project = copy.deepcopy(by_path["dsa/reversible-depot-release-project"])
project.update(
    id=str(uuid.uuid5(uuid.NAMESPACE_URL, "aitrove:" + project_path)), path=project_path,
    title="Project: audit a live depot index and recovery path",
    summary="Test changing graph edges, immutable index roots, torn journal tails, and CAS schedule claims.",
    sort_order=41350, created_at=stamp, updated_at=stamp, published_at=stamp,
)
project["data"].update(
    reading_minutes=21,
    related=[{"path": path, "title": by_path[path]["title"]} for path in related],
)
project["body"] = (
    "<p>A depot inventory must answer route questions while links arrive and disappear, retain old ownership views for an audit, and restore committed page changes after an interrupted append. Keep each guarantee separate. Use live adjacency sets for the current route question, immutable ordered-index roots for past views, and complete validated journal frames for restart. The queue exercise is a schedule trace for compare-and-swap reasoning; its Python comparison methods have no concurrent atomicity. Do not combine them into an untested claim of one transaction.</p>"
    "<h2>Live graph and historical index</h2>"
    "<p>Start with D-19 linked to D-26 and D-47 isolated. Ask whether D-19 reaches D-47, add D-26 to D-47, ask again, delete that link, and ask again. Require false, true, false. Add a second route before deletion and check that an alternate path keeps the depots connected. Reject a duplicate add and an absent removal. For the ordered index, retain the root containing asset 47, add asset 61 under a fresh root, then remove 47 under a third. Query all three roots. Check that a subtree untouched by an edit is reused by identity and that old owners remain unchanged.</p>"
    "<h2>Restart and queue schedule</h2>"
    "<p>Append a complete transaction frame for P-19 and P-26, sync it, then inject a short final frame for P-52. Replay must return only the complete transaction and trim the torn tail. Replace a byte in a full frame and require a checksum error rather than quiet truncation. Run the queue schedule with a stale tail observation: the stale link must fail after another offer has linked its node. Check FIFO order, then explain why the same Python assignments cannot establish lock-free progress or safe memory reclamation under concurrent execution.</p>"
    "<h2>Acceptance trace</h2><pre><code class=\"language-text\">Live route: false, true, false\nOld ordered root: asset 47; third root: asset 61\nRecovered pages: P-19, P-26; torn P-52 absent\nStale link: false; drained jobs: J-47, J-61</code></pre>"
    "<h2>Cost and failure review</h2>"
    "<p>Adjacency updates do expected O(1) hash-set work, while a route question may visit O(V + E) graph entries. The treap expects O(log N) copied nodes per edit but has O(N) worst-case height. A framed journal append writes O(B) bytes and waits on fsync; replay reads O(L) journal bytes. The queue schedule is only sequential. Record those bounds beside their assumptions. Add a single-writer rule, version-retention policy, and restart-before-append rule to the implementation contract. A production storage engine needs checkpointing, a durable filename protocol, process coordination, and fault testing beyond this exercise.</p>"
    "<h3>Common Mistakes</h3><ul>"
    "<li>Do not keep a union-only component cache after deleting an edge.</li>"
    "<li>Do not edit a node reachable from an older index root.</li>"
    "<li>Do not silently replay past a full checksum failure.</li>"
    "<li>Do not append behind an incomplete tail without recovery.</li>"
    "<li>Do not describe a sequential CAS schedule as a concurrent lock-free implementation.</li>"
    "</ul><h2>Connected lessons</h2>" + links(related + ["dsa/reversible-depot-release-project", "dsa/projects", "dsa/quizzes", subject_root])
)
entries.append(project)
by_path[project_path] = project

questions = [
    ("What gives the live graph its answer after an edge deletion?", ["A fresh search over current adjacency sets", "An unchanged union-only parent array", "Future event intervals supplied in advance"], "A fresh search sees the present edges and can detect whether deletion split a component or left another path."),
    ("What must an undirected edge deletion update?", ["Both endpoint adjacency sets", "Only the source endpoint", "Only a disjoint-set root"], "Both endpoint sets represent the same undirected edge; leaving one direction behind corrupts later traversal."),
    ("Why does the baseline graph query cost O(V + E)?", ["A breadth-first search may visit every reachable vertex and edge", "Hashing always scans every edge during insertion", "The graph is copied for every update"], "The queue and visited set can grow with vertices, and traversal may inspect every stored adjacency entry."),
    ("What makes an older ordered-index root safe to retain?", ["Edited paths use new immutable nodes while other subtrees are shared", "The new root overwrites all old nodes", "A global mutable map rewrites old owners"], "Path copying preserves nodes reachable from earlier roots and reuses only the subtrees left unchanged."),
    ("Which treap cost is supported by independent random priorities?", ["Expected logarithmic search height", "Guaranteed logarithmic height for every priority sequence", "Constant-time ordered traversal"], "Independent random priorities give expected balance; an unlucky ordering can still make a linear-height tree."),
    ("Why can a frozen treap node still expose a changed old version?", ["A mutable object referenced by one of its fields can change", "Frozen nodes always duplicate the entire heap", "Search keys become unordered after a read"], "The node blocks field reassignment, but an object held in a field needs its own immutability rule."),
    ("What should recovery do with a short final journal payload?", ["Truncate the incomplete tail and retain earlier complete frames", "Apply the partial transaction", "Skip the bytes and continue after them"], "A short final frame has no complete validated transaction and must not be replayed or left before a new append."),
    ("What should a full frame with a failed checksum trigger in the shown policy?", ["An error requiring investigation", "Silent application of its JSON content", "Unconditional deletion of every earlier frame"], "A complete frame with mismatched bytes may be corruption in the middle, so the model refuses silent data loss."),
    ("When does the shown writer acknowledge a transaction?", ["After a complete frame write and successful fsync", "As soon as JSON is encoded in memory", "After an unsynced torn header is written"], "Acknowledgment follows the checked write and synchronization call under the stated single-writer storage assumptions."),
    ("Where does the queue offer make its node reachable?", ["At the successful link from the observed tail node", "Only after a later tail-pointer help step", "When its Python object is allocated"], "The link changes reachability; tail advancement can lag and another participant may help complete it."),
    ("What does the Python CAS schedule actually establish?", ["A sequential transition trace with stale-comparison failure", "Atomicity across hardware threads", "Safe reclamation of detached nodes"], "Its checks are ordinary Python operations, so it cannot prove concurrent atomicity or safe reuse of removed nodes."),
    ("Why is lock-free different from wait-free?", ["System-wide progress can hold while one participant keeps retrying", "Every participant has a fixed step bound in both", "Neither term describes progress"], "A lock-free progress argument does not promise a bounded number of steps for each individual participant."),
]
balanced_questions = []
for number, (prompt, options, explanation) in enumerate(questions):
    correct = options[0]
    distractors = options[1:]
    position = number % 3
    distractors.insert(position, correct)
    balanced_questions.append({"prompt": prompt, "options": distractors, "answer": position, "explanation": explanation})

quiz = copy.deepcopy(by_path["quizzes/dsa-offline-queue-snapshot-recovery"])
quiz.update(
    id=str(uuid.uuid5(uuid.NAMESPACE_URL, "aitrove:" + quiz_path)), path=quiz_path,
    title="Online routes, persistent roots, journals, and CAS checks",
    summary="Check live graph updates, structural sharing, record recovery, and queue progress limits.",
    sort_order=41360, created_at=stamp, updated_at=stamp, published_at=stamp,
)
quiz["data"].update(
    duration_minutes=17,
    related=[{"path": path, "title": by_path[path]["title"]} for path in related + [project_path]],
    questions=balanced_questions,
)
quiz["body"] = (
    "<p>Read each question as a claim about a specific implementation. Separate expected cost from worst-case cost, sequential simulation from concurrent progress, and validated records from durable acknowledgment.</p>"
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
    ("dsa/offline-connectivity-edge-lifetimes", "dsa/online-connectivity-after-edge-removal"),
    ("dsa/immutable-index-snapshot-publication", "dsa/persistent-ordered-index-path-copying"),
    ("dsa/page-redo-journal-recovery-model", "dsa/framed-journal-torn-tail-recovery"),
    ("dsa/bounded-queue-close-and-drain", "dsa/cas-queue-link-help-and-reclamation"),
):
    old = by_path[old_path]
    old["body"] += '<p><a href="/' + new_path + '">' + html.escape(by_path[new_path]["title"]) + "</a> examines the next boundary.</p>"
    old["updated_at"] = stamp
for path in related:
    entry = by_path[path]
    entry["body"] += '<p>Test this contract in the <a href="/' + project_path + '">live depot audit project</a>, then check the <a href="/' + quiz_path + '">operations quiz</a>.</p>'
    entry["updated_at"] = stamp

fixture.write_text(json.dumps(entries, ensure_ascii=False, indent=2) + "\n")
print(json.dumps({"added": [project_path, quiz_path], "questions": len(questions)}))
