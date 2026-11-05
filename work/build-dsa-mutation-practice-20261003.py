"""Add a mutation-focused project and twelve-question practice bank."""

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
project_path = "dsa/index-mutation-invariants-project"
quiz_path = "quizzes/dsa-mutation-and-versioning-contracts"
assert project_path not in by_path and quiz_path not in by_path
stamp = datetime.datetime.now(datetime.UTC).isoformat()

related = [
    "dsa/red-black-ordered-insertion",
    "dsa/bplus-multilevel-insertion",
    "dsa/avl-interval-index-insertion",
    "dsa/compressed-trie-deletion-and-merge",
    "dsa/persistent-segment-tree-versioned-sums",
]


def links(paths):
    return "<ul>" + "".join(
        '<li><a href="/' + path + '">' + html.escape(by_path[path]["title"]) + "</a></li>"
        for path in paths
    ) + "</ul>"


project = copy.deepcopy(by_path["dsa/maintenance-index-ownership-project"])
project.update(
    id=str(uuid.uuid5(uuid.NAMESPACE_URL, "aitrove:" + project_path)),
    path=project_path,
    title="Project: test mutation invariants across four indexes",
    summary="Specify inserts, splits, overlaps, exact-key removal, and snapshot boundaries in one inventory service.",
    sort_order=40950,
    created_at=stamp,
    updated_at=stamp,
    published_at=stamp,
)
project["data"].update(
    reading_minutes=18,
    related=[{"path": path, "title": by_path[path]["title"]} for path in related],
)
project["body"] = (
    "<p>A parts service has four read contracts: find a bay ID, list bay IDs in order, reject overlapping maintenance windows, and resolve a complete part code. Its writes arrive in batches that can split index pages or rotate trees. Write a small acceptance test around the linked lessons. The test is the deliverable: each assertion should name the invariant it protects and should compare against an independent simple model. Keep the model small enough to inspect. A sorted set, a list of windows, and a plain set of part codes are enough for this exercise.</p>"
    "<h2>Operation contract</h2>"
    "<p>Insert bay IDs 47, 19, 83, 26, 61, 52, 58, 31, 67, and 73 into a B+ index capped at three keys per page. Require an ordered leaf scan and point lookup after every insertion, then check that all leaves have the same depth and every internal separator equals the smallest key in its right child. Insert the same IDs into the red-black index. Check sorted order, a black root, no right-leaning red links, and equal black height after each mutation. Duplicate inserts must leave both indexes unchanged.</p>"
    "<h2>Interval and key lifecycle</h2>"
    "<p>Insert half-open windows [47, 61), [19, 26), [52, 58), [83, 91), and [31, 42) into the AVL interval index. Query [25, 32): some stored window must overlap. Query [62, 80): none may overlap. Recompute height and subtree maximum from children after every rotation; a correct returned overlap is insufficient if the metadata is stale. Insert dock47, dock52, doll61, and dock into a compressed trie. Delete dock and confirm dock47 survives; delete dock52 and confirm doll61 survives. Removing dock52 again must report false. A prefix path alone does not prove exact membership.</p>"
    "<h2>Acceptance trace</h2>"
    "<pre><code class=\"language-text\">Bay scan: 19, 26, 31, 47, 52, 58, 61, 67, 73, 83\nBay 58: found; bay 49: missing\nWindow [25, 32): overlap; [62, 80): none\nDelete dock: true; dock47: present\nDelete dock52 again: false; doll61: present</code></pre>"
    "<h2>Cost and boundary review</h2>"
    "<p>For n keys, balanced ordered operations take O(log n) in memory, subject to page width and list shifts in the B+ model. An ordered scan returning k keys costs at least O(k), even when reaching its first leaf is logarithmic. The AVL overlap query finds one result in O(log n); reporting all matches needs output work. Trie mutation depends on key length and branch search. A persistent segment tree can preserve older aggregate versions, but it does not make a B+ page write durable. State where a transaction commits, how readers see a consistent version, and what recovery does if a process stops after changing one index but before changing the others. In-memory property tests do not answer those storage questions.</p>"
    "<h3>Common Mistakes</h3><ul>"
    "<li>Do not compare two implementations that share the same faulty helper; use a smaller independent oracle.</li>"
    "<li>Do not accept a correct leaf scan while internal separators route point lookups to the wrong page.</li>"
    "<li>Do not ignore metadata after AVL rotations because one overlap query happened to pass.</li>"
    "<li>Do not clear a compressed-trie branch used by another stored key.</li>"
    "<li>Do not treat separate successful in-memory mutations as an atomic durable update.</li>"
    "</ul><h2>Connected lessons</h2>" + links(related + ["dsa/projects", "dsa/quizzes", subject_root])
)
entries.append(project)
by_path[project_path] = project

questions = [
    ("After a B+ leaf split, which key must the parent use to route equality right?", ["The largest key in the old left leaf", "The smallest key in the new right leaf", "The median position before insertion"], 1, "The new right leaf's first key is its routing boundary. Equality must descend right because B+ data keys remain in leaves."),
    ("A child split makes a B+ internal page exceed capacity. What happens next?", ["Split that page and propagate a separator upward", "Discard the highest separator", "Keep the overflow until the next range scan"], 0, "An overfull parent must split too. Propagation may create a new root, while every leaf must stay at the same depth."),
    ("Which check detects an invalid red-black insertion even if sorted traversal is correct?", ["Equal black height on both child paths", "The first key is the minimum", "Every node has a payload"], 0, "Sorted traversal proves search order only. Unequal black heights can leave an ordered tree with broken balance guarantees."),
    ("What must an insertion operation do to the red-black root before returning?", ["Paint it black", "Paint it red", "Remove both children"], 0, "The root is required to be black in this index. A color flip during repair may change it, so the public insertion step resets it."),
    ("An AVL interval rotation changes a node's children. Which fields need repair?", ["Only the interval start", "Height and subtree maximum end", "Only the root's color"], 1, "Both height and maximum end depend on descendants. Refresh the demoted node first, then the promoted node, after pointer changes."),
    ("For half-open windows [19, 26) and [26, 31), what is their overlap?", ["One unit", "The endpoint 26", "None"], 2, "The end of the first window is excluded and the start of the second is included, so touching at 26 is not an overlap."),
    ("Why can a compressed trie remove dock while preserving dock47?", ["The terminal marker is separate from the shared path", "All descendants are duplicated at the root", "Removing a key never changes nodes"], 0, "Unmarking dock as a complete key does not remove the path or descendant used by dock47. Cleanup can merge only unused edges."),
    ("What should deleting a traversable prefix that was never stored return?", ["Success because the path exists", "Failure without changing descendants", "Success and erase every descendant"], 1, "A compressed path can be present without an exact terminal key. Exact-key deletion should report false and preserve descendants."),
    ("Which oracle is suitable for checking a small B+ insertion program?", ["Its own leaf traversal only", "A separately maintained sorted set plus structural checks", "The same split helper called twice"], 1, "An independent sorted set catches missing or duplicate keys; structural checks also catch separator and leaf-depth defects."),
    ("A versioned range-sum tree retains yesterday's root. What does that guarantee?", ["Old queries can use the old root in memory", "B+ pages are crash-safe", "All indexes commit atomically"], 0, "Path copying retains older aggregate roots for readers. It says nothing about durability or atomic publication across other indexes."),
    ("A B+ leaf scan reports k adjacent results. Which lower bound remains?", ["O(1) regardless of k", "At least O(k) to emit k results", "Exactly O(n squared)"], 1, "Even if the first leaf is located quickly, returning k distinct keys requires at least k output steps."),
    ("What protects a reader from seeing one index updated and another stale?", ["A documented transaction or version-publication boundary", "An in-order traversal of each index", "A smaller page capacity"], 0, "Individual correct mutations do not form one atomic service update. A shared commit or publication protocol defines the visible state."),
]
quiz = copy.deepcopy(by_path["quizzes/dsa-index-and-queue-invariants"])
quiz.update(
    id=str(uuid.uuid5(uuid.NAMESPACE_URL, "aitrove:" + quiz_path)),
    path=quiz_path,
    title="Mutation and versioning contracts",
    summary="Test split propagation, color repair, interval metadata, exact-key removal, and reader boundaries.",
    sort_order=40960,
    created_at=stamp,
    updated_at=stamp,
    published_at=stamp,
)
quiz["data"].update(
    duration_minutes=15,
    related=[{"path": path, "title": by_path[path]["title"]} for path in related + [project_path]],
    questions=[{"prompt": prompt, "options": options, "answer": answer, "explanation": explanation} for prompt, options, answer, explanation in questions],
)
quiz["body"] = (
    "<p>Check what each mutation actually preserves. Separate sorted output from structural correctness, and in-memory versioning from an atomic service update.</p>"
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

for path in related[:4]:
    entry = by_path[path]
    entry["body"] += '<p>Apply this mutation in the <a href="/' + project_path + '">index mutation project</a>, then check the <a href="/' + quiz_path + '">mutation quiz</a>.</p>'
    entry["updated_at"] = stamp

fixture.write_text(json.dumps(entries, ensure_ascii=False, indent=2) + "\n")
print(json.dumps({"added": [project_path, quiz_path], "questions": len(questions)}))
