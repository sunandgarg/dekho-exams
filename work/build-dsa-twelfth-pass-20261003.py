"""Add bitmap, heavy-light, and sorted-run tutorials with practice material."""

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

lessons = [
    dict(
        path="dsa/bitvector-rank-select-superblocks",
        program="bitvector_rank_select.py",
        title="Bitvector rank and select: count and locate set bits",
        summary="Pack flags into words, count earlier ones, and locate an ordinal set bit.",
        section="dsa/hash-tables",
        definition="A bitvector stores Boolean flags as bits. Rank1(stop) counts set bits in the half-open prefix [0, stop); select1(ordinal) returns the position of the zero-based ordinal set bit. This index packs flags into 64-bit logical words and stores the number of ones before each word. Rank combines one prefix entry with a masked population count. Select first finds a word whose prefix bracket contains the ordinal, then removes earlier set bits within that word. The bitmap is immutable after construction. Changing a bit would also change every later prefix count, so a mutable design needs a different summary structure or a rebuild.",
        case="A timeline has active incident flags at positions 19, 47, and 61. Rank1(48) returns 2 because the prefix includes positions 19 and 47. Select1(1) returns 47, and rank at the full length returns 3. A count at stop 47 would exclude the flag at 47; the half-open boundary is part of the contract. The bitmap positions are not incident IDs. A separate mapping is required if the application wants to find an incident record after locating its position. This is a plain packed bitmap with prefix counts, not a compressed bitmap format.",
        cost="Building from N input flags scans O(N) values and allocates O(ceil(N/64)) Python integers for words and the same order of prefix counts. Rank uses O(1) indexed operations plus a population count on a bounded 64-bit word. Select binary-searches the prefix array in O(log(N/64)) comparisons and removes at most 63 bits, so the within-word phase is bounded by a constant. An empty bitmap has rank zero but no valid select ordinal. Python integers and lists add object overhead beyond the logical bit count, so this example should not be marketed as a measured succinct encoding.",
        mistakes=["Do not treat rank's stop position as inclusive.", "Do not use one-based select ordinals against this zero-based API.", "Do not mutate packed words without repairing later prefix counts.", "Do not claim this Python representation uses exactly N bits of memory."],
        related=["dsa/bitset-adjacency-matrix-dense-graph", "dsa/bloom-filter-membership-boundary", "dsa/sparse-set-bounded-identifiers"],
    ),
    dict(
        path="dsa/heavy-light-tree-path-sums",
        program="heavy_light_depot_paths.py",
        title="Heavy-light decomposition: sum weights along a tree path",
        summary="Flatten heavy chains and combine Fenwick ranges for node-weight paths.",
        section="dsa/trees-and-heaps",
        definition="Heavy-light decomposition assigns each tree node to a chain formed by repeatedly choosing a largest child subtree. Every move between chains crosses a light edge, and a root-to-leaf path crosses O(log N) such edges. Nodes receive contiguous positions within their chains. A Fenwick tree over those positions stores node weights, so a path query sums chain ranges until both endpoints share one chain. This example includes both endpoints and counts the common ancestor exactly once. The constructor requires one connected acyclic tree with distinct depot IDs; weights may change, but edges and node IDs are fixed after construction.",
        case="The depot tree connects D-19 to D-26 and D-47; D-26 connects to D-52 and D-61; D-47 connects to D-83. With weights 7, 11, 13, 17, 19, and 23 respectively, the path from D-52 to D-83 sums 17+11+7+13+23=71. Replacing D-19's weight with 29 changes that path sum to 93. The path from D-61 to D-52 stays 47 because it does not pass through D-19. A path between any two vertices is unique only because the input is a tree. For a general road network, choosing one spanning tree would discard alternative routes and would answer a different question.",
        cost="For N nodes, adjacency, parent, depth, subtree size, chain head, position, and Fenwick arrays use O(N) space. This straightforward constructor inserts each flattened weight into Fenwick separately, so preprocessing costs O(N log N) time. A node-weight update costs O(log N). A path query crosses O(log N) chains and performs an O(log N) Fenwick range sum for each, giving O(log² N) time. An ordinary parent walk is simpler and costs O(path length) per query. This implementation uses iterative topology passes to avoid recursive DFS depth limits, but it is not a fully online tree structure: linking or cutting an edge requires rebuilding.",
        mistakes=["Do not count a chain boundary node twice when climbing toward the common ancestor.", "Do not mistake node weights for edge weights without changing the flattened contract.", "Do not accept a cyclic or disconnected input as one tree.", "Do not claim fast link and cut operations from a fixed-topology decomposition."],
        related=["dsa/fenwick-tree-point-update-prefix-query", "dsa/iterative-binary-tree-traversal-orders", "dsa/graph-adjacency-list-and-bfs"],
    ),
    dict(
        path="dsa/lsm-sorted-runs-tombstone-compaction",
        program="lsm_sorted_runs_tombstones.py",
        title="Sorted runs and tombstones: model an LSM read path",
        summary="Flush a memtable, search newest runs first, and compact superseded keys.",
        section="dsa/hash-tables",
        definition="A log-structured merge design buffers writes in a mutable memtable and periodically produces immutable sorted runs. A point lookup checks the memtable first, then runs from newest to oldest; the first matching key decides visibility. A deletion is represented by a tombstone so an older value does not reappear after a later run is written. This in-memory model flushes when the memtable reaches a distinct-key threshold. It stores each run as a sorted tuple and uses binary search within that run. Full compaction visits runs oldest to newest so newer entries overwrite older ones; after all older runs are consumed, their tombstones can be dropped.",
        case="Write A-19 as west and A-47 as north; the first two-key memtable flushes. Then update A-19 to east and delete A-47; another run flushes. A lookup finds east from the newer run, while the tombstone makes A-47 absent despite its north value in the older run. There are two runs before compaction and one run containing only A-19 afterward. If compaction merged only some runs while older runs remained elsewhere, discarding a tombstone could resurrect a deleted value. This example avoids that hazard by compacting all existing runs together and keeping the current memtable as the newest layer.",
        cost="A memtable write is expected O(1) until a flush; sorting M distinct memtable entries costs O(M log M) time and O(M) new-run space. With R runs, a missing-key lookup performs up to R binary searches, costing O(sum log size(run)) and incurring read amplification. Full compaction over T stored entries and D distinct keys costs expected O(T + D log D) time in this dictionary-and-sort model and O(D) additional space. Keeping multiple versions increases space until compaction. These are in-memory algorithm costs, not disk I/O or durability guarantees. The code has no write-ahead log, fsync, manifest, snapshots, concurrent reads, or crash recovery.",
        mistakes=["Do not search older runs before the memtable or newer runs.", "Do not treat a tombstone as an absent entry while an older value still exists.", "Do not discard tombstones during partial compaction when older layers remain.", "Do not call this in-memory demonstration a durable database."],
        related=["dsa/immutable-index-snapshot-publication", "dsa/framed-journal-torn-tail-recovery", "dsa/bplus-deletion-borrow-merge"],
    ),
]


def links(paths):
    return "<ul>" + "".join('<li><a href="/' + path + '">' + html.escape(by_path[path]["title"]) + "</a></li>" for path in paths) + "</ul>"


for order, lesson in enumerate(lessons):
    path, section = lesson["path"], lesson["section"]
    assert path not in by_path
    source = root / "work/dsa-programs" / lesson["program"]
    program = source.read_text().rstrip()
    output = subprocess.run([sys.executable, str(source)], check=True, capture_output=True, text=True).stdout.strip()
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
    entry = copy.deepcopy(by_path["dsa/fenwick-tree-point-update-prefix-query"])
    entry.update(id=str(uuid.uuid5(uuid.NAMESPACE_URL, "aitrove:" + path)), path=path, title=lesson["title"], summary=lesson["summary"], body=body,
                 sort_order=41700 + order * 10, created_at=stamp, updated_at=stamp, published_at=stamp)
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
project_path = "dsa/incident-bitmap-path-index-compaction-project"
quiz_path = "quizzes/dsa-bit-rank-path-and-run-contracts"
assert project_path not in by_path and quiz_path not in by_path
project = copy.deepcopy(by_path["dsa/incident-search-and-streaming-project"])
project.update(id=str(uuid.uuid5(uuid.NAMESPACE_URL, "aitrove:" + project_path)), path=project_path,
               title="Project: audit incident flags, depot paths, and sorted runs",
               summary="Check bit ordinals, fixed-tree path sums, and tombstone visibility under compaction.",
               sort_order=41740, created_at=stamp, updated_at=stamp, published_at=stamp)
project["data"].update(reading_minutes=22, related=[{"path": path, "title": by_path[path]["title"]} for path in new_paths])
project["body"] = (
    "<p>An incident console tracks active flags in a fixed timeline, weighs depots on a fixed tree, and keeps recent asset states across sorted runs. Give each layer a precise boundary. Bitmap rank counts positions before a stop, while select locates the zero-based ordinal one. Path sums include both endpoint depots and only the nodes on their unique tree route. The sorted-run index must preserve the newest write or tombstone for each key. Use a list, parent walk, and plain dictionary as independent oracles rather than trusting the index's own summaries.</p>"
    "<h2>Acceptance trace</h2><p>Place active flags at timeline positions 19, 47, and 61. Rank at stop 48 must be 2; selecting ordinal 1 must locate position 47. Query the D-52 to D-83 path with depot weights 17, 11, 7, 13, and 23 along that route, obtaining 71. Replace D-19's weight 7 with 29, and require 93 for the same route but 47 for D-61 to D-52. Flush A-19=west and A-47=north; then flush A-19=east and a deletion marker for A-47. Verify the visible results before and after full compaction.</p>"
    '<h3>Expected output</h3><pre><code class="language-text">rank1(48)=2 select1(1)=47\npath-before=71 path-after=93 alternate=47\nA-19=east A-47=missing runs-before=2 runs-after=1</code></pre>'
    "<h2>Cost and boundary review</h2><p>Rank is O(1) over a bounded packed word, while this select implementation searches the word-prefix array. A point weight update is O(log N) and a heavy-light path sum is O(log² N). A missing-key sorted-run lookup may search every run, and full compaction rewrites all surviving keys. Reject invalid ordinals, malformed trees, and unsupported value types in the test suite. The bitmap and tree topology cannot be edited by their shown APIs. The sorted-run program is only an in-memory model; writing these tuples to disk without a journal and recovery protocol would not make it crash safe.</p>"
    "<h3>Common Mistakes</h3><ul><li>Do not include the stop position in a prefix rank.</li><li>Do not count a chain junction twice.</li><li>Do not read an older run past a newer deletion marker.</li><li>Do not discard a marker while older runs can still supply the deleted key.</li></ul>"
    "<h2>Connected lessons</h2>" + links(new_paths + ["dsa/projects", "dsa/quizzes", subject_root])
)
entries.append(project)
by_path[project_path] = project

questions = [
    ("What does rank1(48) include?", ["Set positions from 0 through 47", "The bit at position 48", "Only the 48th set bit"], "Rank uses a half-open prefix, so it counts every one before the stop and excludes the bit at the stop itself."),
    ("What is select1(1) in a zero-based API?", ["The position of the second set bit", "The number of set bits before position 1", "The position of the first set bit"], "Ordinal zero names the first one, making ordinal one the second one in position order."),
    ("Why does changing one bitmap bit invalidate later prefix entries?", ["Every later word summary counts earlier ones", "All words must be resorted", "A rank index stores incident IDs as strings"], "The prefix count before each later word includes the changed word, so those cached totals need adjustment."),
    ("What makes a heavy-light chain heavy?", ["At each node it follows a largest child subtree", "It contains the largest edge weights", "It is chosen by lexical depot ID"], "Selecting a largest child leaves light transitions that reduce remaining subtree size enough to bound their number."),
    ("How many times should the common ancestor contribute to a node-weight path sum?", ["Once", "Twice", "Never"], "The two endpoint climbs meet at one node; counting it on both sides would overstate the path total."),
    ("What happens when a depot link is added after this decomposition is built?", ["The fixed-topology index needs rebuilding", "Only one Fenwick cell changes", "All old path answers remain valid without work"], "Chain heads, parents, depths, and flattened positions describe the original tree and do not support link edits."),
    ("Which layer should a sorted-run point lookup check first?", ["The current memtable", "The oldest run", "The run with the smallest key"], "The newest write may still be in memory and must override any older value on disk or in an earlier run."),
    ("What does a tombstone prevent?", ["An older run's value from reappearing after deletion", "Binary search within a run", "A memtable from flushing"], "A deletion marker is a visible newer record that masks matching older values until compaction can safely eliminate them."),
    ("When can full compaction discard deletion markers in the shown model?", ["When every older run is consumed and no older value remains", "Before checking any older run", "Whenever the memtable reaches two entries"], "A marker can vanish only after all sources it masks are removed from the resulting run set."),
    ("What is the point-update cost for depot weights in the shown index?", ["O(log N)", "O(1) worst case", "O(N²)"], "The depot's flattened position is known, and one Fenwick update climbs a logarithmic number of summary cells."),
    ("Why might a missing asset lookup become costly with many runs?", ["It may binary-search each run before confirming absence", "It must rescan every bitmap bit", "It must rebuild the depot tree"], "Without filters or a bounded run hierarchy, an absent key forces a search through every immutable run."),
    ("What production property does the sorted-run example omit?", ["Durability after a process or power failure", "Newest-first lookup", "Deletion masking"], "Its runs and memtable live only in memory; the code has no journal, sync, manifest, or recovery protocol."),
]
balanced = []
for number, (prompt, options, explanation) in enumerate(questions):
    correct = options[0]
    distractors = options[1:]
    position = number % 3
    distractors.insert(position, correct)
    balanced.append({"prompt": prompt, "options": distractors, "answer": position, "explanation": explanation})
quiz = copy.deepcopy(by_path["quizzes/dsa-pattern-spatial-frequency-indexes"])
quiz.update(id=str(uuid.uuid5(uuid.NAMESPACE_URL, "aitrove:" + quiz_path)), path=quiz_path,
            title="Bit rank, depot paths, and sorted-run contracts",
            summary="Check prefix boundaries, chain sums, and deletion visibility.",
            sort_order=41750, created_at=stamp, updated_at=stamp, published_at=stamp)
quiz["data"].update(duration_minutes=18, related=[{"path": path, "title": by_path[path]["title"]} for path in new_paths + [project_path]], questions=balanced)
quiz["body"] = "<p>Use the exact range and freshness contract in each question. One off-by-one bit, repeated ancestor, or ignored tombstone changes the answer.</p><h2>Lessons</h2>" + links(new_paths) + "<h2>Design exercise</h2>" + links([project_path, subject_root])
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
    ("dsa/bitset-adjacency-matrix-dense-graph", new_paths[0]),
    ("dsa/fenwick-tree-point-update-prefix-query", new_paths[1]),
    ("dsa/framed-journal-torn-tail-recovery", new_paths[2]),
):
    old = by_path[old_path]
    old["body"] += '<p><a href="/' + new_path + '">' + html.escape(by_path[new_path]["title"]) + "</a> adds a related operation contract.</p>"
    old["updated_at"] = stamp
for path in new_paths:
    entry = by_path[path]
    entry["body"] += '<p>Test this invariant in the <a href="/' + project_path + '">incident flag and path audit</a>, then answer the <a href="/' + quiz_path + '">contract quiz</a>.</p>'
    entry["updated_at"] = stamp

fixture.write_text(json.dumps(entries, ensure_ascii=False, indent=2) + "\n")
print(json.dumps({"lessons": new_paths, "project": project_path, "quiz": quiz_path, "questions": len(questions)}))
