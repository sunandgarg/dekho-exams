"""Add applied practice for the third DSA depth pass."""

import copy
import datetime
import html
import json
import uuid
from pathlib import Path

fixture = Path(__file__).resolve().parents[1] / "src/data/fixtures.json"
entries = json.loads(fixture.read_text())
by_path = {entry["path"]: entry for entry in entries}
root = "dsa/dsa-tutorial-learn-data-structures-and-algorithms"
project_path = "dsa/maintenance-index-ownership-project"
quiz_path = "quizzes/dsa-index-and-queue-invariants"
stamp = datetime.datetime.now(datetime.UTC).isoformat()
lesson_paths = [
    "dsa/red-black-tree-invariant-audit",
    "dsa/btree-page-split-insertion",
    "dsa/interval-tree-max-endpoint-pruning",
    "dsa/compressed-trie-edge-splitting",
    "dsa/bounded-thread-queue-acknowledgment",
]
assert project_path not in by_path and quiz_path not in by_path


def lesson_links(paths):
    return "<ul>" + "".join('<li><a href="/' + path + '">' + html.escape(by_path[path]["title"]) + "</a></li>" for path in paths) + "</ul>"


project = copy.deepcopy(by_path["dsa/warehouse-index-versioning-project"])
project.update(
    id=str(uuid.uuid5(uuid.NAMESPACE_URL, "aitrove:" + project_path)),
    path=project_path,
    title="Project: own a maintenance index and work queue",
    summary="Design ordered bay search, interval checks, prefix lookup, and bounded worker intake.",
    body=(
        "<p>A maintenance system accepts bay IDs, repair windows, part codes, and queued jobs. Its read path asks whether a bay exists, whether a requested time overlaps a repair window, and whether a part code is an exact match. Its write path must ingest jobs without an unbounded in-memory backlog. Assign a data structure to each operation and write down which process owns the authoritative state. A fast in-memory search tree cannot replace durable storage or a completed-job record.</p>"
        "<h2>Choose structures and invariants</h2><p>Use a B-tree page model to reason about ordered bay insertion and median promotion; choose an actual storage engine for on-disk indexes. Use a balanced interval tree with subtree maximums when frequent overlap queries and updates justify it. A plain unbalanced tree has O(n) worst-case height. Use a compressed trie for exact and prefix-oriented part-code routing when shared runs of symbols make node reduction useful. A red-black invariant audit can detect color or black-height damage after mutation, but it is not an insertion algorithm. A bounded synchronized queue protects worker memory while leaving retry and durability to separate services.</p>"
        "<h2>Acceptance trace</h2><p>Insert bay IDs 47, 52, 61, 19, 26, 58, and 83; an in-order read must produce 19, 26, 47, 52, 58, 61, 83. For half-open windows [19, 26), [31, 42), [47, 61), [52, 58), and [83, 91), query [25, 32) and require some overlap, then query [62, 80) and require none. Store dock47, dock52, and doll61 as part codes; dock is a traversable prefix, not an exact key. Fill a two-slot queue with J-47 and J-52; a nonblocking J-61 attempt must report full instead of disappearing silently.</p>"
        '<pre><code class="language-text">Bay order: 19, 26, 47, 52, 58, 61, 83\nWindow [25, 32): overlap\nWindow [62, 80): no overlap\nPart dock47: exact; dock: prefix only\nThird queued job: backpressure</code></pre>'
        "<h2>Cost and ownership review</h2><p>State the B-tree degree and distinguish CPU comparisons from page I/O. Pair interval metadata with balancing if a strict logarithmic bound matters; count O(k) output for k reported overlaps. Budget compressed edge labels and test insertion at a key that is itself another key's prefix. Specify a queue shutdown signal, failed-job record, bounded retry policy, and the point where a worker declares completion. Acknowledging a local queue item after an exception must not masquerade as a successful repair.</p>"
        "<h3>Common Mistakes</h3><ul><li>Do not treat an invariant checker as a mutation method.</li><li>Do not present a Python B-tree model as crash-safe storage.</li><li>Do not claim a plain interval BST has balanced worst-case height.</li><li>Do not equate queue removal with successful processing.</li></ul>"
        "<h2>Connected lessons</h2>" + lesson_links(lesson_paths + ["dsa/bplus-leaf-split-range-index", root])
    ),
    sort_order=40800,
    created_at=stamp,
    updated_at=stamp,
    published_at=stamp,
)
project["data"].update(section_path="dsa/projects", related=[{"path": path, "title": by_path[path]["title"]} for path in lesson_paths])
entries.append(project)
by_path[project_path] = project

questions = [
    ("What keeps a red-black search path logarithmic?", "Color and equal-black-height invariants maintained across updates", "An in-order traversal after every lookup", "A hash value stored at the root", "Red-parent and equal-black-height rules limit the longest path relative to the shortest; an ordered BST alone does not."),
    ("What does the red-black audit program implement?", "Validation of one stored tree state", "Complete insertion and deletion", "Disk persistence", "Its traversal checks ordering, color, and black height. It does not rotate or recolor during an update."),
    ("What happens before B-tree insertion descends into a full child here?", "The child is split and its median enters the parent", "The new key is discarded", "Every existing page is copied", "Splitting makes the chosen next child nonfull and preserves ordered key ranges."),
    ("What does a B-tree node contain?", "Several ordered keys and child ranges", "Exactly one key and at most two children", "Only a hash bucket", "B-tree fan-out comes from multiple keys per page; a binary-search-tree node has a different shape."),
    ("Why must every B-tree leaf share a depth?", "It is part of the balanced page-search invariant", "It makes all keys identical", "It eliminates disk writes", "Equal leaf depth prevents one search from traversing a much longer branch than another."),
    ("Which interval metadata lets a search skip a left subtree?", "The largest end endpoint reachable below that child", "The number of nodes in the subtree", "Only the root start value", "If the left subtree's largest end is at most the query low bound, no left interval can overlap."),
    ("What is the overlap rule for half-open intervals [a,b) and [c,d)?", "a < d and c < b", "a <= d and c <= b", "a == c only", "Strict comparisons make intervals that merely touch at an endpoint nonoverlapping."),
    ("Why does the plain interval BST not promise logarithmic worst-case search?", "Its height can grow to n without balancing", "The max-end field is always zero", "It has no search key", "Subtree augmentation helps pruning but does not prevent an unfavorable insertion order from creating a chain."),
    ("When must a compressed trie split an edge?", "When a new key shares only a proper prefix of that edge", "After every exact lookup", "Only after the root becomes black", "The split retains the old suffix branch and makes room for the new diverging suffix."),
    ("Why does a compressed trie still need an exact-key marker?", "A traversable prefix may not itself be a stored key", "Edges are never labeled", "Every child has the same suffix", "Path existence identifies a route through the index; the marker identifies a completed key."),
    ("What does put_nowait do on a full bounded queue?", "It raises Full for the caller to handle", "It silently overwrites the oldest job", "It marks a task complete", "A bounded queue exposes backpressure; silently losing the attempted job would change the contract."),
    ("When should a queue worker call task_done?", "After handling the dequeued item under its processing policy", "Before reading the item", "Only when the process restarts", "The unfinished count tracks outstanding local work, but task_done still does not prove durable or remote success."),
]
quiz = copy.deepcopy(by_path["quizzes/dsa-advanced-structure-contracts"])
quiz.update(
    id=str(uuid.uuid5(uuid.NAMESPACE_URL, "aitrove:" + quiz_path)),
    path=quiz_path,
    title="Index and queue invariants",
    summary="Check page splits, balance claims, interval pruning, exact keys, and worker intake.",
    body="<p>Choose the claim supported by each indexed or queued operation. Separate an in-memory teaching model from a durable service boundary.</p><h2>Lessons</h2>" + lesson_links(lesson_paths) + "<h2>Design exercise</h2>" + lesson_links([project_path, root]),
    sort_order=40810,
    created_at=stamp,
    updated_at=stamp,
    published_at=stamp,
)
quiz["data"].update(
    section_path="dsa/quizzes",
    duration_minutes=12,
    related=[{"path": path, "title": by_path[path]["title"]} for path in lesson_paths + [project_path]],
    questions=[
        {"prompt": prompt, "options": [answers[(offset + rotation) % 3] for offset in range(3)],
         "answer": (-rotation) % 3, "explanation": explanation}
        for rotation, (prompt, correct, wrong_a, wrong_b, explanation) in enumerate(questions)
        for answers in [(correct, wrong_a, wrong_b)]
    ],
)
entries.append(quiz)
by_path[quiz_path] = quiz

for path, hub_path in ((project_path, "dsa/projects"), (quiz_path, "dsa/quizzes")):
    for target in (hub_path, root):
        hub = by_path[target]
        module = hub["data"]["modules"][0] if target == hub_path else next(module for module in hub["data"]["modules"] if module["title"] == by_path[hub_path]["title"])
        module["lessons"].append(path)
        hub["body"] += '<p><a href="/' + path + '">' + html.escape(by_path[path]["title"]) + "</a></p>"
        hub["updated_at"] = stamp

for lesson_path in lesson_paths:
    lesson = by_path[lesson_path]
    lesson["body"] += "<p><strong>Apply it:</strong> " + '<a href="/' + project_path + '">' + html.escape(project["title"]) + "</a> and " + '<a href="/' + quiz_path + '">' + html.escape(quiz["title"]) + "</a>.</p>"
    lesson["data"]["related"].extend([{"path": project_path, "title": project["title"]}, {"path": quiz_path, "title": quiz["title"]}])
    lesson["updated_at"] = stamp

fixture.write_text(json.dumps(entries, ensure_ascii=False, indent=2) + "\n")
print(json.dumps({"project": project_path, "quiz": quiz_path, "questions": len(questions)}))
