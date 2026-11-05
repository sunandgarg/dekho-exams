"""Publish checked mutation lessons from standalone Data Structures programs."""

import copy
import datetime
import html
import json
import subprocess
import sys
import uuid
from pathlib import Path

root_dir = Path(__file__).resolve().parents[1]
fixture = root_dir / "src/data/fixtures.json"
entries = json.loads(fixture.read_text())
by_path = {entry["path"]: entry for entry in entries}
subject_root = "dsa/dsa-tutorial-learn-data-structures-and-algorithms"
stamp = datetime.datetime.now(datetime.UTC).isoformat()

lessons = [
    {
        "path": "dsa/red-black-ordered-insertion",
        "program": "red_black_insert.py",
        "title": "Red-black insertion: rotate and recolor an ordered index",
        "section": "dsa/trees-and-heaps",
        "summary": "A left-leaning red-black insertion keeps ordered keys and equal black height.",
        "definition": "A left-leaning red-black search tree represents a balanced ordered index with colored parent links. A newly inserted key starts red. During the return from recursion, a right-leaning red link rotates left, a pair of left red links rotates right, and two red children trigger a color split. The root becomes black before the update finishes. These transformations preserve binary-search order and equal black height, so insertion and search remain O(log n) in the worst case when the invariant is maintained. The program handles unique integer keys and ignores a duplicate; it does not implement deletion or concurrent access.",
        "case": "A scheduler inserts deadlines 47, 52, 61, 19, 26, 58, and 83. Sorted traversal must report every deadline once, regardless of the root chosen by rotations. The audit also rejects a right-leaning red link, adjacent red links, unequal black height, and an out-of-order descendant. Keeping a separate audit in the teaching program makes the invariant observable; application code would normally run such checks in tests rather than after every live insertion. A deadline's payload or tie policy would need its own key convention before this becomes a scheduler index.",
        "cost": "One insertion follows a logarithmic-height path and performs only bounded local rotations or color changes per visited node, giving O(log n) time and O(log n) recursive stack space. The index stores O(n) nodes. The final in-order list and full audit each take O(n) time and are demonstration checks, not part of ordinary insertion. Python assertions can be disabled, so production invariant testing should use explicit errors. The implementation does not erase deadlines; deletion requires additional move-red and fix-up cases and must be tested separately.",
        "mistakes": ["Do not mark the new root red after a completed insertion.", "Do not rotate pointers without moving the corresponding color relationship.", "Do not claim this insertion-only program handles deletion or cross-thread mutation."],
        "related": ["dsa/red-black-tree-invariant-audit", "dsa/avl-rotation-height-invariant", "dsa/binary-search-tree-order-invariant"],
    },
    {
        "path": "dsa/bplus-multilevel-insertion",
        "program": "bplus_insert.py",
        "title": "B+ trees: propagate leaf splits through multiple levels",
        "section": "dsa/trees-and-heaps",
        "summary": "Promote separators from leaf and internal splits while retaining ordered leaf links.",
        "definition": "A B+ tree routes search through internal separator keys while storing actual keys in leaves. Leaves remain at one depth and form an ordered chain for range scans. An insertion descends to a leaf, inserts the new key, splits an overfull page, and may propagate a separator split through several parents or create a new root. This in-memory program implements unique integer-key insertion with a three-key page limit; it handles more than one tree level. It omits deletion, page persistence, duplicate-record storage, and concurrent writers. The upper separators direct a key equal to the separator into the right child.",
        "case": "An inventory index accepts bay keys 47, 52, 61, 19, 26, 58, 83, 31, 67, and 73. Each leaf holds at most three keys. Inserting enough keys creates more leaves and can split an internal page. A scan follows leaf links to report all ten keys in order. Lookup for 58 succeeds; lookup for 49 fails. The linked scan matters because a range query should not have to ascend to the root for every adjacent key. The tiny capacity makes structural changes visible; a storage engine would choose page size and durability rules for its medium.",
        "cost": "With capacity c and balanced height h, lookup and insertion visit O(h) pages, where h is O(log_c n) for a properly occupied B+ tree. In this Python model, searching within a page uses logarithmic comparisons but list insertion can shift O(c) references. A split may propagate through O(h) ancestors. The program stores O(n) keys and references and uses O(h) recursion. Range scans cost O(h + k) page and item work to return k adjacent keys under a suitable page layout. This code does not model disk I/O, write-ahead logging, or crash-safe page publication; do not treat an in-memory success as a database guarantee.",
        "mistakes": ["Do not store the only copy of a data key in an internal separator.", "Do not forget to link a new right leaf into the range-scan chain.", "Do not stop after a leaf split if the parent is also overfull."],
        "related": ["dsa/bplus-leaf-split-range-index", "dsa/btree-page-split-insertion", "dsa/skip-list-ordered-index"],
    },
    {
        "path": "dsa/avl-interval-index-insertion",
        "program": "avl_interval_insert.py",
        "title": "Balanced interval indexes: rotate height and maximum metadata together",
        "section": "dsa/trees-and-heaps",
        "summary": "AVL insertion keeps both tree height and subtree maximum endpoint current.",
        "definition": "An interval search tree can be balanced with AVL rotations while storing the maximum interval end under each node. Ordering by the pair (start, end) lets distinct windows share a start. After insertion, each ancestor recomputes its height and maximum end; any required single or double rotation then refreshes both metadata fields in child-first order. An overlap lookup can skip a left subtree whose maximum end is not greater than the query's low endpoint. The implementation supports insertion and finding one overlap, using half-open intervals. Deletion and enumerating every overlap require additional methods.",
        "case": "A maintenance calendar inserts [47, 61), [19, 26), [52, 58), [83, 91), and [31, 42). It finds an overlap for [25, 32) and none for [62, 80). The stored root height remains three and its maximum end is 91 after the five inserts. Those values are derived from children, not guessed from insertion order. A plain augmented BST could become a chain under sorted starts; AVL height repair keeps this index logarithmic while endpoint metadata supports pruning. Equal complete interval pairs are ignored here rather than counted as separate bookings.",
        "cost": "Insertion and one-overlap lookup take O(log n) time because AVL height is logarithmic and each visited node performs O(1) metadata work. Insertion uses O(log n) recursion stack space, and the tree uses O(n) nodes. The search returns any overlapping interval, not necessarily the earliest or shortest one. A query that must enumerate k overlaps needs output-sensitive traversal and at least O(k) result work. Concurrent readers must not inspect partly rotated nodes without synchronization or an immutable snapshot; this Python program has no such protocol.",
        "mistakes": ["Do not update height while leaving max-end metadata stale after a rotation.", "Do not call touching half-open endpoints an overlap.", "Do not claim this insertion-only index handles removal of a booking."],
        "related": ["dsa/interval-tree-max-endpoint-pruning", "dsa/avl-rotation-height-invariant", "dsa/red-black-ordered-insertion"],
    },
    {
        "path": "dsa/compressed-trie-deletion-and-merge",
        "program": "compressed_trie_delete.py",
        "title": "Compressed tries: delete exact keys and merge unused edges",
        "section": "dsa/trees-and-heaps",
        "summary": "Unmark a terminal key without removing shared descendants, then collapse lone paths.",
        "definition": "Deletion from a compressed trie first locates a complete stored key, clears its terminal marker, and walks back toward the root. An edge whose child has no terminal marker and no children can be removed. An edge whose child has no terminal marker and exactly one child can merge with that child's edge label. A branch shared by other keys must remain. The operation depends on exact-key status: removing a traversable prefix that was never a stored key should report false and leave the index unchanged. This program keeps variable-length edge labels and a separate terminal boolean.",
        "case": "A parts index stores dock47, dock52, doll61, and the complete key dock. Removing dock makes dock an internal prefix but leaves dock47 and dock52 searchable. Removing dock52 then permits some nonbranching path labels to merge, while doll61 remains intact. Both calls return true because both keys were stored. A repeated removal of dock52 would return false. The index is case-sensitive and uses Python string comparison without Unicode normalization; an application handling user-entered identifiers should define normalization before key insertion and deletion.",
        "cost": "For a key of length L, the path walk compares edge labels against remaining input. With a bounded child alphabet and indexed edge choice, work is O(L); this simple implementation scans child labels, so a node with many children adds a branching-factor cost. The path stack uses O(number of traversed edges) extra space and the stored labels plus nodes use space proportional to inserted key material. Merging edges creates a new concatenated Python string and therefore copies those characters. Concurrent mutation would need synchronization; this example is an in-memory single-writer index.",
        "mistakes": ["Do not delete a shared branch while removing one terminal key.", "Do not report success when only a prefix path exists.", "Do not leave two consecutive single-child nonterminal nodes after cleanup."],
        "related": ["dsa/compressed-trie-edge-splitting", "dsa/trie-prefix-index-and-terminal-flag", "dsa/hash-set-membership-and-order"],
    },
]

assert all(lesson["path"] not in by_path for lesson in lessons)
for order, lesson in enumerate(lessons):
    path, section = lesson["path"], lesson["section"]
    source = root_dir / "work/dsa-programs" / lesson["program"]
    program = source.read_text().rstrip()
    result = subprocess.run([sys.executable, str(source)], check=True, capture_output=True, text=True).stdout.strip()
    related_paths = [section, subject_root, *lesson["related"], "dsa/projects", "dsa/quizzes"]
    body = (
        "<p>" + html.escape(lesson["definition"]) + "</p>"
        + "<h2>Operational case</h2><p>" + html.escape(lesson["case"]) + "</p>"
        + '<h2>Working Python program</h2><pre><code class="language-python">' + html.escape(program, quote=False) + "</code></pre>"
        + '<h3>Output</h3><pre><code class="language-text">' + html.escape(result) + "</code></pre>"
        + "<h2>Time, space, and tradeoff</h2><p>" + html.escape(lesson["cost"]) + "</p>"
        + "<h3>Common Mistakes</h3><ul>" + "".join("<li>" + html.escape(mistake) + "</li>" for mistake in lesson["mistakes"]) + "</ul>"
        + "<h2>Connected lessons</h2><ul>" + "".join('<li><a href="/' + related_path + '">' + html.escape(by_path[related_path]["title"]) + "</a></li>" for related_path in related_paths) + "</ul>"
    )
    entry = copy.deepcopy(by_path["dsa/fenwick-tree-point-update-prefix-query"])
    entry.update(id=str(uuid.uuid5(uuid.NAMESPACE_URL, "aitrove:" + path)), path=path, title=lesson["title"], summary=lesson["summary"],
                 body=body, sort_order=40900 + order * 10, created_at=stamp, updated_at=stamp, published_at=stamp)
    entry["data"].update(section_path=section, related=[{"path": related_path, "title": by_path[related_path]["title"]} for related_path in related_paths])
    entries.append(entry)
    by_path[path] = entry
    for hub_path in (section, subject_root):
        hub = by_path[hub_path]
        module = hub["data"]["modules"][0] if hub_path == section else next(module for module in hub["data"]["modules"] if module["title"] == by_path[section]["title"])
        module["lessons"].append(path)
        hub["body"] += '<p><a href="/' + path + '">' + html.escape(lesson["title"]) + "</a></p>"
        hub["updated_at"] = stamp

fixture.write_text(json.dumps(entries, ensure_ascii=False, indent=2) + "\n")
print(json.dumps({"addedLessons": len(lessons), "paths": [lesson["path"] for lesson in lessons]}))
