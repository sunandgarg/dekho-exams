"""Add two-choice hashing, packed spatial search, and bitwise trie lessons."""

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
        path="dsa/cuckoo-hashing-relocation-rebuild",
        program="cuckoo_asset_ids.py",
        title="Cuckoo hashing: relocate keys and recover from cycles",
        summary="Keep each asset ID in one of two slots, with rollback and bounded rebuild attempts.",
        section="dsa/hash-tables",
        definition="A two-table cuckoo set gives each key one candidate slot in each table. Lookup inspects at most those two slots. Insertion may evict an occupant from the first table, move that occupant to its alternate slot, and continue alternating. A repeated relocation can cycle without finding an empty slot. This implementation records each replacement and reverses them if its bounded displacement attempt fails. It then builds candidate tables with new salts, growing capacity when needed, and publishes the new tables only after every key is placed. If all bounded rebuild attempts fail, the old set remains intact and insertion raises. Keys are unsigned 64-bit integers; two IDs that differ outside that domain are rejected rather than being silently treated as the same fingerprint.",
        case="Insert asset IDs 19, 47, 61, 83, and 95. Membership finds 61 and rejects 26. Removing 47 clears its one occupied candidate slot; a second lookup no longer finds it, and four IDs remain. A duplicate insertion returns false. A collision can displace several existing IDs, so checking only the new ID after insertion would miss lost occupants. The reference test compares the entire set after each mutation. Two tables of capacity C have 2C physical slots, but this model begins rebuilding before more than C live IDs are stored; growing the table is a separate cost, not a free continuation of a two-probe lookup.",
        cost="Membership and deletion inspect no more than two slots and take O(1) time, with O(1) working space. A successful insertion without rebuild follows a displacement chain of at most 2C attempts and logs that many replacements for rollback. Rebuild scans every live key and can make several placement attempts in freshly allocated tables; it is expensive and this deterministic, bounded implementation does not promise an expected constant insertion bound. Candidate table memory is O(C) per attempt, in addition to the old table until publication. A failed rebuild raises without changing the old table. The salts are deterministic and are not cryptographic defenses against chosen keys or a substitute for independent random hash functions.",
        mistakes=["Do not leave a partially relocated table when insertion reaches a cycle.", "Do not claim constant-time insertion because lookup checks two slots.", "Do not confuse per-table capacity C with total physical slots 2C.", "Do not accept integers outside the declared unsigned width."],
        related=["dsa/robin-hood-hash-backward-shift-deletion", "dsa/open-addressing-tombstones-rehash", "dsa/hash-map-collision-and-load-contract"],
    ),
    dict(
        path="dsa/packed-r-tree-rectangle-intersection",
        program="packed_depot_rtree.py",
        title="Packed R-tree: search intersecting depot rectangles",
        summary="Bulk-load bounding rectangles, prune disjoint branches, and verify leaf hits.",
        section="dsa/trees-and-heaps",
        definition="A packed R-tree groups spatial records into bounded-size nodes and stores a minimum bounding rectangle over each group. This example sorts rectangle centers into x-oriented strips, then groups each strip by y position. It repeats that packing process over child nodes until one root remains. A query descends only into nodes whose bounding rectangles intersect the query, then checks each candidate record's own rectangle. Bounding boxes can overlap; finding one matching child does not license skipping another. The index is static after bulk loading and caps node size without enforcing a minimum fill rule. It does not implement R-tree insertion, split repair, deletion, or geographic distance. Rectangle boundaries count as intersections here, and reversed input bounds are rejected.",
        case="Five depot service zones include D-19 at [4, 5] to [11, 12], D-26 at [18, 7] to [26, 14], D-47 at [9, 10] to [16, 19], D-61 far away, and D-83 at [12, 2] to [20, 8]. A query from [10, 8] to [19, 15] intersects D-19, D-26, D-47, and D-83, including a boundary touch at y=8. A distant query returns an empty list. Internal bounds can admit a false candidate because they enclose a group, so the leaf-level check is necessary. Results are sorted by ID for repeatable output; the sort is a presentation cost, not part of pruning.",
        cost="For N records and fixed fanout M at least two, repeated sorting during bulk loading takes O(N log N) time and O(N) stored nodes and records. The search visits only intersecting bounding rectangles when the groups separate well, but heavy overlap can force O(N) traversal. If K records match, sorting the returned IDs adds O(K log K) time and O(K) result space. The explicit traversal stack can grow with the number of visited nodes. No worst-case logarithmic query promise follows from the tree shape alone. A static k-d tree is suited to a different point-nearest-neighbor contract; this index answers axis-aligned rectangle intersection. Geographic coordinates require a separately defined projection and wrap policy.",
        mistakes=["Do not stop after the first intersecting child when bounding rectangles overlap.", "Do not return every record inside an intersecting parent box without a leaf check.", "Do not treat touching edges as disjoint under this inclusive rectangle contract.", "Do not call this immutable packed index a live insertion and deletion API."],
        related=["dsa/kd-tree-exact-nearest-depot", "dsa/interval-tree-max-endpoint-pruning", "dsa/bplus-multilevel-insertion"],
    ),
    dict(
        path="dsa/binary-trie-maximum-xor-multiset",
        program="bit_trie_asset_xor.py",
        title="Binary tries: choose a maximum-XOR fingerprint",
        summary="Store fixed-width integer fingerprints with duplicate counts and deletions.",
        section="dsa/trees-and-heaps",
        definition="A binary trie stores one fixed-width unsigned integer as a root-to-leaf sequence of bits, most significant first. Every node counts how many stored values pass through it, so duplicates share a path. To maximize XOR with a query, follow the opposite query bit whenever that branch exists; a higher XOR bit outweighs every combination of lower bits. The path reconstructs an actual stored partner, and the method returns that partner with its XOR score. Removal decrements counts and drops an empty suffix branch. This is a multiset of integer fingerprints, not an XOR linear basis: the answer must be one value actually stored, rather than a XOR combination of several values.",
        case="Store 19, 47, 61, 83, and a second 47 as eight-bit fingerprints. For query 26, the best stored partner is 83, giving XOR score 73. Removing one 47 leaves one copy; removing it again leaves zero. A missing removal raises. An empty index cannot supply a partner and raises instead of inventing zero. Both inserted values and queries must fit the declared unsigned width. Without the width check, Python negative integers and wider positive values would not have the fixed bit paths this trie assumes.",
        cost="With bit width B, insertion, count, removal, and best-partner search each visit exactly B levels: O(B) time. Storage is O(U B) nodes in the worst case for U distinct stored values, with shared prefixes reducing actual use. Duplicate occurrences change counts without adding new branches. Removal may free an unused suffix, but Python object dictionaries carry overhead that can exceed a flat array for small sets. Greedy maximum-XOR search gives one stored maximizing partner; if several partners tie in score, the bit path still determines the numerical partner. This implementation is single-threaded and does not provide a concurrent snapshot.",
        mistakes=["Do not accept a wider or negative integer after constructing a fixed-width trie.", "Do not erase a shared branch when removing only one duplicate.", "Do not return an XOR combination that was never stored as a partner.", "Do not query a maximum partner from an empty multiset."],
        related=["dsa/trie-prefix-index-and-terminal-flag", "dsa/bitvector-rank-select-superblocks", "dsa/implicit-treap-range-reversal"],
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
                 sort_order=42000 + order * 10, created_at=stamp, updated_at=stamp, published_at=stamp)
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
project_path = "dsa/asset-spatial-fingerprint-audit-project"
quiz_path = "quizzes/dsa-cuckoo-spatial-bit-trie-contracts"
assert project_path not in by_path and quiz_path not in by_path
project = copy.deepcopy(by_path["dsa/forest-substring-note-audit-project"])
project.update(id=str(uuid.uuid5(uuid.NAMESPACE_URL, "aitrove:" + project_path)), path=project_path,
               title="Project: audit asset IDs and depot zones",
               summary="Compare two-choice hashing, rectangle search, and fingerprint XOR to plain reference models.",
               sort_order=42040, created_at=stamp, updated_at=stamp, published_at=stamp)
project["data"].update(reading_minutes=25, related=[{"path": path, "title": by_path[path]["title"]} for path in new_paths])
project["body"] = (
    "<p>A maintenance console tracks active asset IDs, depot service rectangles, and integer fingerprints. Use a Python set as the asset oracle, a direct rectangle scan for spatial search, and a multiset plus maximum over XOR scores for fingerprints. Run the reference check after every mutation. In the cuckoo set, force collisions and a rebuild, then check that a failed candidate insertion cannot remove an old ID. In the spatial index, generate overlapping boxes so a parent intersection has false-positive candidates that need leaf checks. In the bit trie, insert duplicates and remove them one at a time. None of the three structures can answer a question outside its contract: an immutable spatial tree cannot take live edits, a two-slot lookup does not make insertion free, and a maximum-XOR partner is not an arbitrary XOR basis combination.</p>"
    "<h2>Acceptance trace</h2><p>Insert asset IDs 19, 47, 61, 83, and 95. Confirm 61 is present and 26 absent, remove 47, and require four remaining IDs. Build the five service rectangles shown in the spatial lesson; query [10, 8] through [19, 15] and require D-19, D-26, D-47, and D-83 in sorted order. The distant query returns no matches. Store fingerprints 19, 47, 61, 83, and 47 at width eight; querying 26 returns stored partner 83 and XOR score 73. After two removals of 47, its count is zero.</p>"
    '<h3>Expected output</h3><pre><code class="language-text">asset-61=true asset-26=false live=4\nzones=D-19,D-26,D-47,D-83 distant=none\npartner=83 score=73 count-47=0</code></pre>'
    "<h2>Boundary and cost review</h2><p>Reject IDs outside the unsigned 64-bit domain and fingerprints outside the configured bit width. Check an empty spatial index, a box that only touches a boundary, duplicate record IDs, an empty fingerprint multiset, and a missing removal. The cuckoo lookup makes at most two probes, but relocation and rebuilding have separate costs. R-tree overlap can visit every record, and sorted output adds its own time. A bit trie spends one step per bit and retains one count per live path. Record the chosen coordinate system; these sample rectangles use planar integer coordinates, not latitude and longitude.</p>"
    "<h3>Common Mistakes</h3><ul><li>Do not discard an evicted key when relocation fails.</li><li>Do not confuse an enclosing node box with an exact record hit.</li><li>Do not delete a trie branch still used by another fingerprint.</li><li>Do not infer a worst-case fast search from a favorable sample layout.</li></ul>"
    "<h2>Connected lessons</h2>" + links(new_paths + ["dsa/projects", "dsa/quizzes", subject_root])
)
entries.append(project)
by_path[project_path] = project

questions = [
    ("How many candidate slots does membership inspect in this cuckoo set?", ["At most two", "Every slot in both tables", "One slot per stored asset"], "Each key has one calculated position in each of the two tables, so membership checks no more than those two cells."),
    ("What happens when a relocation walk reaches its limit?", ["Recorded replacements are reversed before rebuilding", "The pending asset ID is discarded", "The last occupant is silently overwritten"], "Rollback restores the old table before candidate rebuilds, so a failed insertion cannot lose an already stored asset ID."),
    ("What does the cuckoo capacity count?", ["Slots in each table", "All slots across both tables", "The maximum allowed asset ID"], "Capacity C names one table's length; the two tables together have 2C physical slots before a possible rebuild."),
    ("What insertion guarantee does this bounded deterministic implementation make?", ["It may raise after failed rebuild attempts without changing the old set", "Every insertion finishes in constant time", "Every collision is solved by one displacement"], "A relocation cycle can force rebuilding, and the finite attempt budget leaves a defined failure path with the previous set preserved."),
    ("What does a packed R-tree parent rectangle enclose?", ["All record rectangles below that parent", "Only one exact matching record", "The geographic route between two depots"], "A parent's minimum bounding rectangle covers its descendants, which is why it can prune disjoint groups but may admit candidates."),
    ("Why check leaf records after a parent intersects the query?", ["The parent box can overlap while a particular record box does not", "Leaf nodes have no rectangles", "Search must visit all leaves even when parents are disjoint"], "Enclosing rectangles can contain empty space, so a surviving branch still needs an exact intersection test for each record."),
    ("What update operation does this packed spatial index implement?", ["None after bulk loading", "Live insertion with automatic split repair", "Deletion with reinsertion"], "The construction packs a fixed input into a static tree; live inserts or deletes would require additional update algorithms."),
    ("What is the worst-case rectangle-search traversal cost under heavy overlap?", ["O(N) visited records and nodes", "Guaranteed O(log N)", "O(1) because the root has one rectangle"], "Overlapping bounding rectangles may leave every branch eligible, making the traversal scan the entire index in the worst case."),
    ("Which bit does maximum-XOR search prefer at each level?", ["The opposite of the query bit when that branch exists", "Always zero", "The same bit as the query"], "A differing high bit contributes more to the XOR score than every lower bit together, so the opposite branch is preferred."),
    ("What does each binary-trie node count represent?", ["Stored occurrences passing through that node", "The number of zero bits in the whole set", "The number of distinct roots"], "The count records multiplicity along a prefix and lets duplicate insertions share nodes while removal preserves still-used branches."),
    ("What happens after removing one of two identical fingerprints?", ["One occurrence remains on the same path", "The entire path must disappear", "All other fingerprints are reinserted"], "One deletion decrements path counts once; only a branch whose count reaches zero can be removed safely."),
    ("What must a reported maximum-XOR partner be?", ["One fingerprint actually stored", "Any XOR combination of stored fingerprints", "The bitwise complement even if absent"], "A trie follows a live root-to-leaf path and reconstructs a stored value, unlike a linear basis that combines values."),
]
balanced = []
for number, (prompt, options, explanation) in enumerate(questions):
    correct = options[0]
    distractors = options[1:]
    position = number % 3
    distractors.insert(position, correct)
    balanced.append({"prompt": prompt, "options": distractors, "answer": position, "explanation": explanation})
quiz = copy.deepcopy(by_path["quizzes/dsa-circular-traversal-bitset-rank"])
quiz.update(id=str(uuid.uuid5(uuid.NAMESPACE_URL, "aitrove:" + quiz_path)), path=quiz_path,
            title="Cuckoo slots, spatial boxes, and bit trie paths",
            summary="Check displacement rollback, rectangle pruning, and maximum-XOR multiplicity.",
            sort_order=42050, created_at=stamp, updated_at=stamp, published_at=stamp)
quiz["data"].update(duration_minutes=20, related=[{"path": path, "title": by_path[path]["title"]} for path in new_paths + [project_path]], questions=balanced)
quiz["body"] = "<p>Check exact operation boundaries. A hash key has two candidate slots, a spatial parent box is a filter, and a trie answer must be a stored fingerprint.</p><h2>Lessons</h2>" + links(new_paths) + "<h2>Design exercise</h2>" + links([project_path, subject_root])
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
    ("dsa/robin-hood-hash-backward-shift-deletion", new_paths[0]),
    ("dsa/open-addressing-tombstones-rehash", new_paths[0]),
    ("dsa/kd-tree-exact-nearest-depot", new_paths[1]),
    ("dsa/interval-tree-max-endpoint-pruning", new_paths[1]),
    ("dsa/trie-prefix-index-and-terminal-flag", new_paths[2]),
    ("dsa/bitvector-rank-select-superblocks", new_paths[2]),
):
    old = by_path[old_path]
    old["body"] += '<p><a href="/' + new_path + '">' + html.escape(by_path[new_path]["title"]) + "</a> adds a related operation contract.</p>"
    old["updated_at"] = stamp
for path in new_paths:
    entry = by_path[path]
    entry["body"] += '<p>Apply the invariant in the <a href="/' + project_path + '">asset and depot audit project</a>, then check the <a href="/' + quiz_path + '">operations quiz</a>.</p>'
    entry["updated_at"] = stamp

fixture.write_text(json.dumps(entries, ensure_ascii=False, indent=2) + "\n")
print(json.dumps({"lessons": new_paths, "project": project_path, "quiz": quiz_path, "questions": len(questions)}))
