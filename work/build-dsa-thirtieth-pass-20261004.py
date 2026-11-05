"""Add splay-tree and resident-history cache lessons to the DSA draft fixture."""

import copy
import datetime
import html
import json
import subprocess
import sys
import uuid
from pathlib import Path


root = Path(__file__).resolve().parents[1]
fixture = root / "src/data/fixtures.json"
entries = json.loads(fixture.read_text())
by_path = {entry["path"]: entry for entry in entries}
subject_root = "dsa/dsa-tutorial-learn-data-structures-and-algorithms"
stamp = datetime.datetime.now(datetime.UTC).isoformat()


def links(paths):
    return "<ul>" + "".join(
        '<li><a href="/' + path + '">' + html.escape(by_path[path]["title"]) + "</a></li>"
        for path in paths
    ) + "</ul>"


lessons = [
    dict(
        path="dsa/splay-tree-access-and-join-invariants",
        program="splay_case_index.py",
        template="dsa/binary-search-tree-order-invariant",
        section="dsa/trees-and-heaps",
        title="Splay Trees: Access Rotations and Join Invariants",
        summary="Move an accessed key to the root while retaining binary-search order and parent ownership.",
        definition=(
            "A splay tree is a binary search tree that rotates the last accessed node to its root. "
            "It stores no height or color balance metadata. A search follows ordinary key comparisons; on a hit it splays "
            "the found node, and on a miss this implementation splays the last node visited. The three rotation cases are "
            "a single step when the parent is the root, two aligned steps when node and parent sit on the same side, and "
            "two crossed steps otherwise. Each rotation keeps the in-order key sequence unchanged and repairs the moved "
            "subtree's parent pointer. The root can change even when a search returns false. That is a useful locality rule, "
            "but callers must not assume read-only lookups leave the tree shape unchanged."
        ),
        case=(
            "A case index receives IDs 47, 19, 83, and 61. Its sorted output is 19, 47, 61, 83 regardless of the current "
            "root. Looking up 19 moves that case to the root. Searching for absent ID 55 visits the comparison path and "
            "then moves the last visited ID, 61, to the root; the operation still reports false. Removing 47 first splays "
            "it, detaches its two subtrees, splays the maximum of the left subtree, and attaches the right subtree there. "
            "The maximum-left node has no right child, so the join cannot violate key order. Both detached roots lose their "
            "former parent link before the join. A duplicate insertion is rejected, and its search may still reshape the tree."
        ),
        cost=(
            "A single lookup, insertion, or removal can traverse a chain of n nodes and cost O(n). Over a sequence of "
            "standard operations, the splay-tree access bound is O(log n) amortized per operation. The word amortized "
            "matters: it gives no per-request tail-latency cap. Node storage is O(n); the iterative search, rotations, "
            "and in-order walk avoid recursion, while the output list and traversal stack use O(n) extra space in the "
            "worst case. A stable-height AVL or red-black tree is preferable when the application needs a bound for every "
            "individual lookup. This model uses integer IDs, one process, and no concurrent readers; a concurrent search "
            "would mutate shared links and need synchronization. It also makes no claim about CPU-cache speed."
        ),
        mistakes=[
            "Do not call the current tree height logarithmic after every operation.",
            "Do not forget the moved middle subtree's parent pointer during a rotation.",
            "Do not treat an unsuccessful lookup as shape-preserving in this implementation.",
            "Do not attach the right subtree before exposing the maximum of the left subtree during removal.",
        ],
        related=["dsa/binary-search-tree-order-invariant", "dsa/avl-rotation-height-invariant", "dsa/skip-list-ordered-index"],
    ),
    dict(
        path="dsa/resident-lru-k-history-eviction",
        program="resident_lru_k.py",
        template="dsa/lru-cache-eviction-invariant",
        section="dsa/hash-tables",
        title="Resident LRU-K: Evict by the Kth Recent Reference",
        summary="Track bounded resident histories and compare backward reference distance at capacity.",
        definition=(
            "A resident LRU-K cache keeps the last K reference times for each currently cached key. At capacity it evicts "
            "the resident whose Kth most recent reference is oldest. A resident with fewer than K references has an "
            "undefined Kth time and loses against a fully observed resident; among such cold residents, this explicit "
            "policy evicts the one with the oldest latest reference. The code uses a logical counter instead of wall-clock "
            "time, so equal timestamps cannot occur. An update is counted as a reference. A missing read raises KeyError "
            "and records nothing. On eviction, the resident's history is discarded. This is a bounded, resident-only "
            "variant of the idea, rather than a full buffer manager with ghost histories or correlated-reference control."
        ),
        case=(
            "A three-slot incident cache stores 47, 19, and 61. The service then reads 47 and 61, giving each two "
            "observations while 19 has only its insertion. When 83 arrives, 19 is the eviction victim even though 83 "
            "also starts with one observation. The new resident remains until a later capacity decision. If the service "
            "updates 47, that update refreshes its history under this policy; a system that wants reads-only reference "
            "counts must choose a different rule. Returning the evicted ID makes the decision observable. Comparing with "
            "exact LRU is instructive: the last access alone cannot distinguish a briefly touched page from a page with "
            "repeated demand, whereas the second reference can. It still cannot forecast future demand."
        ),
        cost=(
            "A resident hit or update performs expected O(1) map work and appends to a deque of at most K timestamps. "
            "A full insertion scans all C residents to choose a victim, so that operation takes O(C) time. Storage is "
            "O(CK) timestamps plus O(C) keys and payload references. The histories here never survive eviction; this "
            "can make a recurring item look cold after it returns. An ordered candidate index could reduce victim scans "
            "at the cost of more update work and additional state, but that is outside this example. A tie falls through "
            "to the integer case ID after Kth and most-recent times, making repeated traces deterministic. Long-running "
            "services should also decide how to handle logical counter rollover and synchronized writes."
        ),
        mistakes=[
            "Do not rank a one-reference resident as though it has a Kth reference.",
            "Do not call this resident-only implementation a complete database buffer policy.",
            "Do not claim full-cache insertion is constant time while it scans every resident.",
            "Do not silently change whether writes count as references.",
        ],
        related=["dsa/lru-cache-eviction-invariant", "dsa/segmented-lru-probation-protected", "dsa/lfu-cache-frequency-and-recency-eviction"],
    ),
]


for order, lesson in enumerate(lessons):
    path = lesson["path"]
    assert path not in by_path
    source = root / "work/dsa-programs" / lesson["program"]
    program = source.read_text().rstrip()
    output = subprocess.run([sys.executable, str(source)], check=True, capture_output=True, text=True).stdout.strip()
    section = lesson["section"]
    related = [section, subject_root, *lesson["related"], "dsa/projects", "dsa/quizzes"]
    body = (
        "<p>" + html.escape(lesson["definition"]) + "</p>"
        + "<h2>Operational case</h2><p>" + html.escape(lesson["case"]) + "</p>"
        + '<h2>Working Python program</h2><pre><code class="language-python">' + html.escape(program, quote=False) + "</code></pre>"
        + '<h3>Output</h3><pre><code class="language-text">' + html.escape(output) + "</code></pre>"
        + "<h2>Time, space, and tradeoff</h2><p>" + html.escape(lesson["cost"]) + "</p>"
        + "<h3>Common Mistakes</h3><ul>" + "".join("<li>" + html.escape(item) + "</li>" for item in lesson["mistakes"]) + "</ul>"
        + "<h2>Connected lessons</h2>" + links(related)
    )
    entry = copy.deepcopy(by_path[lesson["template"]])
    entry.update(id=str(uuid.uuid5(uuid.NAMESPACE_URL, "aitrove:" + path)), path=path, title=lesson["title"], summary=lesson["summary"], body=body,
                 sort_order=43500 + order * 10, created_at=stamp, updated_at=stamp, published_at=stamp)
    entry["data"].update(section_path=section, related=[{"path": target, "title": by_path[target]["title"]} for target in related])
    entries.append(entry)
    by_path[path] = entry
    for hub_path in (section, subject_root):
        hub = by_path[hub_path]
        module = hub["data"]["modules"][0] if hub_path == section else next(module for module in hub["data"]["modules"] if module["title"] == by_path[section]["title"])
        module["lessons"].append(path)
        hub["body"] += '<p><a href="/' + path + '">' + html.escape(lesson["title"]) + "</a></p>"
        hub["updated_at"] = stamp


new_paths = [lesson["path"] for lesson in lessons]
project_path = "dsa/splay-and-history-policy-audit-project"
quiz_path = "quizzes/dsa-splay-and-resident-history-contracts"
assert project_path not in by_path and quiz_path not in by_path
project = copy.deepcopy(by_path["dsa/allocation-ownership-coalescing-audit-project"])
project.update(id=str(uuid.uuid5(uuid.NAMESPACE_URL, "aitrove:" + project_path)), path=project_path,
               title="Project: Audit Adaptive Search and Cache History", summary="Compare splay mutation and K-reference eviction against direct state ledgers.",
               sort_order=43520, created_at=stamp, updated_at=stamp, published_at=stamp)
project["data"].update(reading_minutes=25, related=[{"path": path, "title": by_path[path]["title"]} for path in new_paths])
project["body"] = (
    "<p>Build an incident lookup service with two independent components: an ordered in-memory index for case IDs and a small payload cache. The ordered index must return membership while allowing even a failed lookup to reshape its tree. The cache must document whether a write counts as a reference and evict by the Kth most recent resident access. Keep the structures separate: a splay rotation changes pointer topology but not membership, while a cache eviction changes membership but does not alter sorted case IDs. Use an integer logical clock for reproducible cache traces.</p>"
    "<h2>Acceptance trace</h2><p>Insert case IDs 47, 19, 83, and 61. Their in-order list must remain 19, 47, 61, 83 after each splay. A hit on 19 makes 19 root; a miss on 55 returns false while bringing the last comparison node, 61, to root. Remove 47 and verify the remaining ordered list and every child-to-parent link. For a three-slot K=2 cache, insert 47, 19, 61, then read 47 and 61. Inserting 83 evicts 19. A missing read raises KeyError without advancing the clock. A duplicate case insertion returns false but may reshape the tree.</p>"
    '<h3>Expected review record</h3><pre><code class="language-text">ordered-before=[19, 47, 61, 83]\nmiss-55=False; root=61\nordered-after-remove=[19, 61, 83]\ncache-victim=19\nresident-ids=[47, 61, 83]</code></pre>'
    "<h2>Failure and cost review</h2><p>Generate randomized insert, find, and remove operations against a Python set, checking sorted membership and parent links after every step. Repeat the cache trace against a small explicit history ledger, including capacity one, repeated writes, cold ties, and a read of a missing key. Record the maximum search depth and the number of cache candidates examined on each full insertion. Explain why a long splay path does not disprove its amortized bound and why the resident-history scan is still linear in capacity. Decide whether strict per-request latency or ghost history is needed before adopting either model in a production service.</p>"
    "<h3>Common Mistakes</h3><ul><li>Do not compare only the splay return value; also check its in-order and parent invariants.</li><li>Do not count a failed cache read as a reference under this policy.</li><li>Do not infer a per-operation latency bound from amortized tree cost.</li><li>Do not retain an evicted resident's history in the resident-only model.</li></ul>"
    "<h2>Connected lessons</h2>" + links(new_paths + ["dsa/projects", "dsa/quizzes", subject_root])
)
entries.append(project)
by_path[project_path] = project

questions = [
    ("What stays ordered during a splay rotation?", ["The in-order sequence of case IDs", "The exact root ID", "The depth of every descendant"], "A rotation changes local parent-child links but preserves the binary-search ordering of all keys in the affected subtree."),
    ("What does this splay implementation do after an unsuccessful lookup?", ["Splays the last visited node", "Inserts the missing ID", "Restores the old root"], "A miss returns false while moving the last node on the search path to the root, so lookup is still a structural mutation."),
    ("When is a splay operation allowed to cost linear time?", ["On an individual long path", "Never, because height is fixed", "Only when the tree is empty"], "The logarithmic guarantee is amortized across an operation sequence; one access may traverse and rotate a chain of n nodes."),
    ("Which two-step case rotates the parent before the accessed node?", ["Aligned child and parent directions", "Crossed child and parent directions", "A node with no parent"], "In a zig-zig configuration the parent rotates first, then the accessed node rotates above it."),
    ("Why splay the maximum of the left subtree before joining after deletion?", ["It has no right child for the detached right subtree to displace", "It is always the minimum key in the whole tree", "It preserves the deleted node as a ghost"], "The maximum-left node can become root and accept the detached right subtree without violating key order."),
    ("Which pointer must a rotation repair when a middle subtree changes parent?", ["The middle subtree root's parent pointer", "Only the overall root's title", "Every unrelated leaf's parent pointer"], "A moved middle subtree must point back to its new parent or later rotations and invariant checks will follow stale links."),
    ("What does resident LRU-K compare at capacity?", ["Each resident's Kth most recent reference time", "Only each resident's insertion payload size", "The order of case IDs in a search tree"], "The victim is chosen by the oldest qualifying Kth reference, with an explicit cold-resident rule when fewer than K observations exist."),
    ("How are residents with fewer than K references ranked here?", ["They lose to fully observed residents", "They are permanently protected", "They are removed before capacity is reached"], "An undefined Kth timestamp ranks below a real one, so a cold resident is the first eviction candidate under this stated policy."),
    ("Does a missing cache read advance the logical clock?", ["No; it raises KeyError without recording", "Yes; every miss is stored as a ghost", "Yes; it silently creates a resident"], "This resident-only implementation records references only for keys already in the cache or for explicit puts."),
    ("What happens to reference history after eviction?", ["It is discarded with the resident", "It is retained forever for every ID", "It is copied into the splay tree"], "The code bounds history storage by current residents; a returning key starts a fresh history rather than inheriting ghost observations."),
    ("Why is full-cache insertion O(C) in this example?", ["It scans C residents to compare history ranks", "A deque append copies all K timestamps", "A splay rotation visits every cache entry"], "The victim is selected with a linear scan over the resident map despite constant-time history append and expected map lookup."),
    ("What must a cache policy specify about updates?", ["Whether a write counts as a reference", "Whether integer keys are sorted lexicographically", "Whether splay misses create nodes"], "This model records updates as accesses; changing that rule changes Kth-history ranks and therefore later eviction choices."),
]
balanced = []
for number, (prompt, options, explanation) in enumerate(questions):
    distractors = options[1:]
    position = number % 3
    distractors.insert(position, options[0])
    balanced.append({"prompt": prompt, "options": distractors, "answer": position, "explanation": explanation})
quiz = copy.deepcopy(by_path["quizzes/dsa-arena-free-buddy-slab-contracts"])
quiz.update(id=str(uuid.uuid5(uuid.NAMESPACE_URL, "aitrove:" + quiz_path)), path=quiz_path,
            title="Splay trees and resident history eviction", summary="Check search mutation, parent links, K-reference ranking, and cold-resident rules.",
            sort_order=43530, created_at=stamp, updated_at=stamp, published_at=stamp)
quiz["data"].update(duration_minutes=20, related=[{"path": path, "title": by_path[path]["title"]} for path in new_paths + [project_path]], questions=balanced)
quiz["body"] = "<p>Review the precise mutation and eviction contracts before comparing traces. A lookup can reshape a splay tree; a cache miss leaves this resident history unchanged.</p><h2>Lessons</h2>" + links(new_paths) + "<h2>Design exercise</h2>" + links([project_path, subject_root])
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
    ("dsa/binary-search-tree-order-invariant", new_paths[0]),
    ("dsa/avl-rotation-height-invariant", new_paths[0]),
    ("dsa/lru-cache-eviction-invariant", new_paths[1]),
    ("dsa/segmented-lru-probation-protected", new_paths[1]),
):
    old = by_path[old_path]
    old["body"] += '<p><a href="/' + new_path + '">' + html.escape(by_path[new_path]["title"]) + "</a> extends this operation comparison.</p>"
    old["updated_at"] = stamp
for path in new_paths:
    other = next(other for other in new_paths if other != path)
    entry = by_path[path]
    entry["body"] += '<p>Compare the operation contract with <a href="/' + other + '">' + html.escape(by_path[other]["title"]) + '</a>, then work through the <a href="/' + project_path + '">audit project</a> and <a href="/' + quiz_path + '">contract quiz</a>.</p>'
    entry["updated_at"] = stamp

fixture.write_text(json.dumps(entries, ensure_ascii=False, indent=2) + "\n")
print(json.dumps({"lessons": new_paths, "project": project_path, "quiz": quiz_path, "questions": len(questions)}))
