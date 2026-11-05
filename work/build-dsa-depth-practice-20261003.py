"""Add an advanced DSA design exercise and explained quiz bank."""

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
project_path = "dsa/warehouse-index-versioning-project"
quiz_path = "quizzes/dsa-advanced-structure-contracts"
stamp = datetime.datetime.now(datetime.UTC).isoformat()
lesson_paths = [
    "dsa/bloom-filter-membership-boundary",
    "dsa/sparse-set-bounded-identifiers",
    "dsa/skip-list-ordered-index",
    "dsa/bplus-leaf-split-range-index",
    "dsa/persistent-segment-tree-versioned-sums",
    "dsa/monotonic-deque-window-minimum",
]
assert project_path not in by_path and quiz_path not in by_path


def lesson_links(paths):
    return "<ul>" + "".join('<li><a href="/' + path + '">' + html.escape(by_path[path]["title"]) + "</a></li>" for path in paths) + "</ul>"


project = copy.deepcopy(by_path["dsa/depot-network-range-audit-project"])
project.update(
    id=str(uuid.uuid5(uuid.NAMESPACE_URL, "aitrove:" + project_path)),
    path=project_path,
    title="Project: design a versioned warehouse index",
    summary="Select exact, probabilistic, ordered, and versioned structures under one workload.",
    body=(
        "<p>A warehouse needs four read paths: reject shipment IDs that are definitely absent, show active device slots from a fixed ID range, scan bay keys in order, and answer daily count ranges against both current and earlier audit revisions. A fifth path reports the minimum delay in every three-reading window. Write an operation contract before choosing storage. A fast local structure does not replace the authoritative shipment index or the durable audit record.</p>"
        "<h2>Design the access paths</h2><p>Put a Bloom filter in front of the exact shipment index, but query that index whenever the filter says possible. Keep active device IDs in a sparse set only if the bounded universe fits memory; document that swap deletion changes iteration order. For mutable ordered bay keys, compare a skip list with an actual page-oriented B+ index. The one-level leaf-split lesson is an invariant exercise, not a deployable database. Choose a persistent segment tree when auditors must compare historical range totals after point corrections. Use a monotonic deque for one-pass fixed-width delay windows.</p>"
        "<h2>Acceptance trace</h2><p>Start with daily counts 47, 31, 26, and 58. The old [1, 4) total is 115. Replace index two with 29 and keep the old root; the new total is 118 while the old remains 115. Activate device slots 47, 61, and 52, then remove 61; membership for 61 is false even if its sparse cell has a stale index. Insert bay 58 between 52 and 61. A positive Bloom response still needs an exact lookup. For readings 47, 31, 26, 58, 19, and 42 with width three, report minima 26, 26, 19, and 19.</p>"
        '<pre><code class="language-text">Old range version: 115\nNew range version: 118\nActive slots after removal: 47, 52\nBay order around insertion: 52, 58, 61\nThree-reading minima: 26, 26, 19, 19</code></pre>'
        "<h2>Cost and failure review</h2><p>State memory for the filter's bit capacity, the sparse set's full ID universe, skip-list links, each retained range version, and the window deque. Distinguish expected skip-list lookup from worst-case lookup, and distinguish a B+ page visit from Python list shifting. Specify how an authoritative write and its filter update become consistent, how audit roots are retained or discarded, and how ordered-index changes survive a process failure. A design passes only when its reported snapshot and exact record source agree with the operation contract.</p>"
        "<h3>Common Mistakes</h3><ul><li>Do not accept a Bloom positive as an exact hit.</li><li>Do not call an in-memory root a durable audit record.</li><li>Do not use a static sparse-set universe without sizing its memory.</li><li>Do not call the one-level page split a complete B+ index.</li></ul>"
        "<h2>Connected lessons</h2>" + lesson_links(lesson_paths + [root])
    ),
    sort_order=40600,
    created_at=stamp,
    updated_at=stamp,
    published_at=stamp,
)
project["data"].update(
    section_path="dsa/projects",
    related=[{"path": path, "title": by_path[path]["title"]} for path in lesson_paths],
)
entries.append(project)
by_path[project_path] = project

questions = [
    ("What does a zero required bit in a Bloom filter prove?", "That the key was not inserted into this synchronized filter", "That the key is in the authoritative index", "That no hash collision occurred", "A required zero rules out a prior insertion into that filter; the system must also keep filter updates synchronized with accepted writes."),
    ("What does an all-bits-set Bloom response mean?", "Possible membership requiring an exact check", "Certain membership", "Certain absence", "Collisions can set the same bits for different keys, so a positive response is advisory."),
    ("Why is plain Bloom-filter deletion unsafe?", "Several keys may share each bit", "It changes the hash function", "It sorts the bit array", "Clearing a shared bit could make another inserted key appear absent."),
    ("What must sparse-set membership check after reading a sparse position?", "The dense entry at that position matches the queried ID", "The dense array remains insertion ordered", "The ID has a high hash value", "Swap deletion and O(1) clear can leave old candidate positions; the dense-value check rejects stale pointers."),
    ("What is the sparse set's main memory tradeoff?", "Space proportional to the bounded ID universe", "One bit per active key only", "No extra space beyond a linked node", "The sparse position array allocates for possible IDs even when only a few are active."),
    ("What is a skip list's ordinary search guarantee?", "Expected O(log n), with possible O(n) worst case", "Worst-case O(1)", "Worst-case O(log n) under any sampled levels", "Randomized promotion gives expected short paths but cannot rule out an unfavorable level assignment."),
    ("Where must every skip-list key appear?", "In the sorted bottom lane", "Only in the highest lane", "Only in a hash bucket", "Higher lanes are optional shortcuts. The bottom lane retains the complete ordered set."),
    ("What separator is added after splitting a B+ leaf in this model?", "The first key of the new right leaf", "The last key of the old left leaf plus one", "An unrelated key from the root", "The separator routes keys at or above the first right-leaf key to that page."),
    ("What does the one-level B+ demonstration omit?", "Parent split propagation and arbitrary tree height", "Sorted leaves", "A half-open range", "A deployable multi-level index must handle overflow above the leaf and durable page changes."),
    ("How does a persistent segment-tree update retain old results?", "It copies the changed root-to-leaf path and shares untouched subtrees", "It mutates the old root in place", "It duplicates every prior version in full", "New path nodes form a new root while unchanged branches remain reachable from both versions."),
    ("What does keeping a Python version root guarantee after restart?", "Nothing without durable storage", "The root is automatically persisted", "All prior transactions were committed", "In-memory structural sharing preserves versions only while the objects and process remain available."),
    ("Why is a sliding-minimum deque linear over all readings?", "Each index enters once and leaves at most once", "Every window rescans all values", "Each insertion sorts the deque", "The while loops remove candidates permanently, so total removals across all steps are bounded by n."),
]
quiz = copy.deepcopy(by_path["quizzes/dsa-tree-graph-range-decisions"])
quiz.update(
    id=str(uuid.uuid5(uuid.NAMESPACE_URL, "aitrove:" + quiz_path)),
    path=quiz_path,
    title="Advanced structure contracts",
    summary="Check exactness, ordering, versioning, and cost in six advanced structures.",
    body="<p>Choose the claim that matches each structure's actual guarantee. Distinguish expected cost from a strict worst-case bound and in-memory versions from durable records.</p><h2>Lessons</h2>" + lesson_links(lesson_paths) + "<h2>Design exercise</h2>" + lesson_links([project_path, root]),
    sort_order=40610,
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
        for rotation, (prompt, *rest) in enumerate(questions)
        for answers, explanation in [((rest[0], rest[1], rest[2]), rest[3])]
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
