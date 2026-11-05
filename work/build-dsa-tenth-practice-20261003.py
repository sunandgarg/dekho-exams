"""Add foundation operations project, quiz, and reciprocal lesson links."""

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
project_path = "dsa/dispatch-ring-tree-graph-audit-project"
quiz_path = "quizzes/dsa-circular-traversal-bitset-rank"
assert project_path not in by_path and quiz_path not in by_path
stamp = datetime.datetime.now(datetime.UTC).isoformat()
related = [
    "dsa/circular-linked-list-tail-invariant",
    "dsa/iterative-binary-tree-traversal-orders",
    "dsa/bitset-adjacency-matrix-dense-graph",
    "dsa/avl-subtree-size-rank-select",
]


def links(paths):
    return "<ul>" + "".join(
        '<li><a href="/' + path + '">' + html.escape(by_path[path]["title"]) + "</a></li>"
        for path in paths
    ) + "</ul>"


project = copy.deepcopy(by_path["dsa/incident-search-and-streaming-project"])
project.update(
    id=str(uuid.uuid5(uuid.NAMESPACE_URL, "aitrove:" + project_path)), path=project_path,
    title="Project: audit dispatch order and dense depot links",
    summary="Trace a circular scheduler, four task-tree orders, bitset intersections, and AVL positions.",
    sort_order=41550, created_at=stamp, updated_at=stamp, published_at=stamp,
)
project["data"].update(
    reading_minutes=22,
    related=[{"path": path, "title": by_path[path]["title"]} for path in related],
)
project["body"] = (
    "<p>A local dispatch board must rotate through depots, show four views of a task tree, compare shared neighbors in a small dense depot graph, and answer asset rank questions. Keep the operation contracts distinct. The circular ring changes who is first by moving one tail reference. Tree orders use stacks or a queue but do not modify the task nodes. Bitset rows represent a fixed vertex mapping. The AVL node stores both height and subtree count, and each rotation has to repair both. Validate every mutation against a simpler independent representation.</p>"
    "<h2>Ring and task views</h2>"
    "<p>Append D-19, D-47, and D-61 to a ring. Rotate once, remove the front, and require D-47 as the removed depot with D-61 then D-19 remaining. Continue until empty and verify the singleton transition on the way. Build a task tree rooted at T-47, with T-19 and T-61 as its children and T-07 and T-26 beneath T-19. Record pre-, in-, post-, and level-order sequences. State whether any of those sequences is guaranteed to be sorted when the tree is not a search tree.</p>"
    "<h2>Dense links and ordered assets</h2>"
    "<p>Connect D-19 to D-26 and D-47, then connect D-61 to those same two depots. The first and last depots share two neighbors. Delete one link and assert both corresponding row bits clear; the shared count becomes one. Insert assets 47, 19, 61, 52, and 83 into a size-augmented AVL tree. Select zero-based ordinal 2 and rank key 58, then delete 47 and select every remaining ordinal. Audit height, subtree size, search ordering, and balance after each edit.</p>"
    "<h2>Acceptance trace</h2><pre><code class=\"language-text\">Ring removal after one rotation: D-47\nTree in-order: T-07, T-19, T-26, T-47, T-61\nShared neighbors before deletion: 2; after deletion: 1\nSelect ordinal 2: 52; rank 58: 3</code></pre>"
    "<h2>Cost and boundary review</h2>"
    "<p>Ring append, one-step rotation, and head removal take O(1) work, while a complete snapshot walks N members. Each tree traversal visits N task nodes and retains O(N) output. A bitset graph spends O(V²) bits for V depots before object overhead; Python row operations may touch O(V/W) machine words. An AVL tree keeps O(log N) height, so rank, select, insertion, and deletion follow logarithmic paths. Explain why repeated select is O(N log N) for all keys and why a static bitset vertex mapping is unsuitable for frequent vertex additions. Keep thread safety outside this project's contract.</p>"
    "<h3>Common Mistakes</h3><ul>"
    "<li>Do not break the ring's singleton self-link or traverse until None.</li>"
    "<li>Do not confuse post-order with level-order when clearing tasks.</li>"
    "<li>Do not update only one endpoint in an undirected bitset graph.</li>"
    "<li>Do not refresh AVL height while leaving subtree size stale.</li>"
    "<li>Do not claim a traversal result is sorted without a search-tree invariant.</li>"
    "</ul><h2>Connected lessons</h2>" + links(related + ["dsa/incident-search-and-streaming-project", "dsa/projects", "dsa/quizzes", subject_root])
)
entries.append(project)
by_path[project_path] = project

questions = [
    ("In a nonempty tail-only circular list, where is the head?", ["At tail.next", "At tail.next.next for every length", "At a null successor"], "The tail's next link closes the cycle at the first node, including the singleton case where it points back to tail."),
    ("What changes during one-step ring rotation in the shown design?", ["Only the stored tail reference", "Every node's next link", "The length and all node values"], "Moving tail to its successor changes the logical head without relinking any node or changing the ring size."),
    ("Why does ring snapshot use the stored length?", ["It gives a finite number of links to follow around a cycle", "The ring ends at None", "It sorts depot IDs"], "A circular list has no null terminator, so a bounded count prevents an unending walk and checks the length invariant."),
    ("Which traversal emits a parent after both child subtrees?", ["Post-order", "Pre-order", "Level-order"], "The ready flag postpones a post-order parent's output until its left and right descendants have completed."),
    ("When does in-order traversal guarantee sorted keys?", ["When the tree has a valid binary-search ordering invariant", "For every arbitrary binary tree", "Only when the tree has one node per level"], "In-order specifies visit positions; sorted output also requires each left key below its parent and each right key above it."),
    ("What is the working-memory bound for level-order traversal?", ["O(W) queue entries for maximum level width W", "Always O(1)", "O(H) with no output list"], "Breadth-first processing can hold a whole level in the deque, separate from the O(N) list returned to the caller."),
    ("Why does an undirected bitset update touch two rows?", ["Both directions represent the same edge", "The graph stores every edge three times", "The vertex mapping changes after each update"], "The bit in row i at column j must match the bit in row j at column i to preserve the undirected contract."),
    ("What operation counts common neighbors in the shown bitset graph?", ["Bitwise row intersection followed by population count", "Union of the two rows", "A shortest-path search"], "A set bit survives the AND exactly when both vertices have that same candidate as a neighbor."),
    ("When is dense bitset storage a poor fit?", ["The graph has many vertices and very few edges", "Many adjacency intersections are required", "Vertex IDs are fixed"], "The matrix reserves vertex-pair positions whether edges exist or not, so a sparse list can use much less memory."),
    ("What must an AVL rotation refresh for order statistics?", ["Both height and subtree size", "Only the root key", "Only the global node count"], "Balance uses heights while rank and select use subtree sizes; both summaries can change when child links rotate."),
    ("What does rank of key 58 mean in this tree?", ["The count of stored keys strictly below 58", "The one-based location of 58 even if absent", "The height of node 58"], "Rank is a lower-bound count, so it remains defined even when the requested key itself is absent."),
    ("What is the cost of enumerating N AVL keys with N separate select calls?", ["O(N log N)", "O(N) by a single visit to each node", "O(log N) total"], "Each select descends a logarithmic path; a single in-order traversal would be the linear-time enumeration method."),
]
balanced_questions = []
for number, (prompt, options, explanation) in enumerate(questions):
    correct = options[0]
    distractors = options[1:]
    position = number % 3
    distractors.insert(position, correct)
    balanced_questions.append({"prompt": prompt, "options": distractors, "answer": position, "explanation": explanation})

quiz = copy.deepcopy(by_path["quizzes/dsa-pattern-spatial-frequency-indexes"])
quiz.update(
    id=str(uuid.uuid5(uuid.NAMESPACE_URL, "aitrove:" + quiz_path)), path=quiz_path,
    title="Circular lists, traversal, bitsets, and rank checks",
    summary="Check ring links, visit order, dense graph rows, and AVL subtree counts.",
    sort_order=41560, created_at=stamp, updated_at=stamp, published_at=stamp,
)
quiz["data"].update(
    duration_minutes=18,
    related=[{"path": path, "title": by_path[path]["title"]} for path in related + [project_path]],
    questions=balanced_questions,
)
quiz["body"] = (
    "<p>Identify the invariant behind each result. Account for singleton rings, traversal output order, mirrored graph bits, and subtree sizes after rotation.</p>"
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
    ("dsa/singly-linked-list-head-tail-invariants", "dsa/circular-linked-list-tail-invariant"),
    ("dsa/binary-search-tree-order-invariant", "dsa/iterative-binary-tree-traversal-orders"),
    ("dsa/csr-sparse-graph-storage", "dsa/bitset-adjacency-matrix-dense-graph"),
    ("dsa/avl-rotation-height-invariant", "dsa/avl-subtree-size-rank-select"),
):
    old = by_path[old_path]
    old["body"] += '<p><a href="/' + new_path + '">' + html.escape(by_path[new_path]["title"]) + "</a> adds a related operation contract.</p>"
    old["updated_at"] = stamp
for path in related:
    entry = by_path[path]
    entry["body"] += '<p>Use this invariant in the <a href="/' + project_path + '">dispatch audit project</a>, then check the <a href="/' + quiz_path + '">operations quiz</a>.</p>'
    entry["updated_at"] = stamp

fixture.write_text(json.dumps(entries, ensure_ascii=False, indent=2) + "\n")
print(json.dumps({"added": [project_path, quiz_path], "questions": len(questions)}))
