"""Add four distinct DSA lessons, an audit project, and a decision quiz."""

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
subject = "dsa/dsa-tutorial-learn-data-structures-and-algorithms"
stamp = datetime.datetime.now(datetime.UTC).isoformat()


def links(paths):
    return "<ul>" + "".join('<li><a href="/' + path + '">' + html.escape(by_path[path]["title"]) + "</a></li>" for path in paths) + "</ul>"


lessons = [
    dict(path="dsa/double-array-trie-static-incident-codes", program="double_array_incident_trie.py",
         template="dsa/trie-prefix-index-and-terminal-flag", section="dsa/trees-and-heaps",
         title="Double-array tries: static incident-code transitions with BASE and CHECK",
         summary="Freeze a code dictionary into indexed transitions and keep terminal membership separate from prefix reachability.",
         definition="A double-array trie stores each transition at BASE[parent] plus the label number. CHECK at the resulting slot records the parent that owns it. A lookup must compare CHECK, because an occupied numerical slot can belong to an unrelated prefix. Terminal flags answer exact membership; reaching a prefix node alone does not prove that the prefix is a stored code. The builder first groups lowercase alphanumeric codes into a temporary trie, then searches for a free offset for each node's outgoing labels. It rejects an empty code and characters outside its declared alphabet. The temporary trie is only a build aid: queries use the three arrays. The output length counts allocated slots, including holes, rather than only live nodes. This is a frozen dictionary, so adding a new code requires rebuilding the arrays.",
         case="The dictionary stores dock47, dock83, door29, and hub61. An exact query for dock47 succeeds, while dock is only a reachable prefix. A query for dome fails even though its first two letters share a path with stored codes. The sample array allocates 38 positions but owns only 17 nodes, including the root; that difference illustrates why a two-array representation is not automatically compact in a high-level runtime. If a label calculation lands on a slot whose CHECK names another parent, traversal stops immediately. The chosen offset is an implementation detail and must not be used as a stable code identifier.",
         cost="A lookup or prefix test visits O(L) transitions for a length-L code and uses O(1) auxiliary query space. Building first takes O(S) nodes for S total input characters before prefix sharing; the naive first-fit offset search can scan many occupied slots per node, so it has no claimed linear construction bound. Array length depends on placement and alphabet gaps, and Python integer lists add object overhead. The temporary trie and queued prefixes also consume build memory proportional to the input, with repeated prefix strings adding copying cost. A pointer trie handles online insertion more naturally; this layout suits a static dictionary where fast indexed traversal is worth a separate build.",
         mistakes=["Do not accept a transition without checking its recorded parent.", "Do not treat a reachable prefix as a terminal code.", "Do not assume two arrays imply packed memory when placement leaves holes.", "Do not edit the source code set without rebuilding the frozen index."],
         related=["dsa/trie-prefix-index-and-terminal-flag", "dsa/compressed-trie-edge-splitting", "dsa/louds-level-order-alert-trie", "dsa/ternary-search-tree-incident-completion", "dsa/binary-radix-longest-prefix-routes", "dsa/front-coded-term-lexicon-blocks"]),
    dict(path="dsa/hopscotch-hash-shipment-neighborhoods", program="hopscotch_shipment_ids.py",
         template="dsa/robin-hood-hash-backward-shift-deletion", section="dsa/hash-tables",
         title="Hopscotch hashing: keep each shipment near its home bucket",
         summary="Relocate occupants into legal neighborhoods before placing a new integer key.",
         definition="Hopscotch hashing is an open-addressed set with a fixed neighborhood width. Every resident key stays within H circular slots after its hash home. Lookup can inspect just those H slots; insertion first locates an empty slot and, when it lies too far away, repeatedly moves a nearby occupant into that hole if the occupant still remains inside its own home neighborhood. The hole then moves backward toward the incoming key's home. If no legal relocation exists, insertion reports failure even if other table slots remain empty. This teaching set uses direct neighborhood scans rather than a bitmap of hop information, and it has no automatic resize. Deletion clears the matching slot because lookup scans the whole allowed neighborhood; no linear-probe tombstone chain is needed. Integer IDs are its declared key domain.",
         case="At capacity 31 and neighborhood width five, shipment IDs 47, 78, 109, 140, and 171 fit in the displayed trace. ID 202 is rejected because no legal series of local moves places it within its own five-slot home window. That rejection does not discard the earlier shipments. Removing 109 makes its lookup false and leaves four residents. The failed insertion may have relocated existing keys, so callers should rely on set membership and the neighborhood invariant rather than byte-for-byte slot stability. The hash multiplier here is deterministic for reproducibility, not a defense against adversarial keys.",
         cost="Lookup and deletion inspect at most H slots, giving O(H) time and O(1) auxiliary space. Finding a hole can scan C slots in a capacity-C table. Each relocation checks at most H minus one candidates, and up to C relocations may occur, so this direct implementation has O(CH) worst-case insertion time and O(C) storage. A failed insertion can still pay that work. At high occupancy, legal placement can fail before the array is full; resizing and rehashing would be a separate operation. Robin Hood hashing instead controls probe-distance balance, while this structure enforces a hard locality window.",
         mistakes=["Do not move a resident outside its own home neighborhood.", "Do not promise insertion succeeds merely because a distant empty slot exists.", "Do not assume slot positions remain stable after a failed placement attempt.", "Do not call this direct-scan model a concurrent hopscotch table."],
         related=["dsa/robin-hood-hash-backward-shift-deletion", "dsa/cuckoo-hashing-relocation-rebuild", "dsa/open-addressing-tombstones-rehash", "dsa/hash-map-collision-and-load-contract", "dsa/linear-hashing-incremental-bucket-splits", "dsa/extendible-hash-directory-bucket-splits"]),
    dict(path="dsa/invertible-bloom-replica-set-reconciliation", program="iblt_replica_reconciliation.py",
         template="dsa/counting-bloom-filter-balanced-deletion", section="dsa/hash-tables",
         title="Invertible Bloom tables: peel differences between replica ID sets",
         summary="Subtract signed cell summaries and recover low-difference unsigned ID sets when peeling succeeds.",
         definition="An invertible Bloom lookup table is a compact set-difference sketch, not an ordinary membership filter. Each ID touches several deterministic cells; a cell stores a signed count, the XOR of IDs, and the XOR of their checksums. Insert IDs from the left replica with plus one and IDs from the right with minus one. Shared IDs cancel in every cell. A cell with count plus or minus one and a matching checksum can reveal one candidate ID. Peeling removes that candidate's contribution from every cell, exposing more pure cells. The decoder returns two exact difference sets only when all residual cells become zero; otherwise it returns failure. This model accepts distinct unsigned 64-bit integer IDs and requires both replicas to use identical cell counts, probe counts, and hash rules. A checksum match is a probabilistic guard, not a cryptographic proof.",
         case="The left replica has incident IDs 19, 29, 47, and 61; the right has 19, 47, and 83. Peeling returns left-only IDs 29 and 61 and right-only ID 83. Shared IDs 19 and 47 cancel without being listed. If the number of differing IDs overwhelms the chosen cells, a nonzero residual can remain and the decoder returns no answer, rather than a partial list presented as complete. An empty set difference decodes to two empty sets. Repeating an ID within a replica violates the set model, because a count of two would no longer mean a single distinct record.",
         cost="With K probes and M cells, each adjustment computes K positions and checks for duplicates among at most K chosen slots; this direct version costs O(K squared) hashing and O(M) table space. Peeling rescans all M cells to find each pure candidate and can remove at most D recovered IDs, so worst-case decoding is O(DM plus DK squared); a queue of newly pure cells would be faster. It copies all cell arrays before decoding, retaining the source sketch. Success depends on load and hash placement, with no guaranteed decode threshold here. A Merkle tree gives a different comparison protocol; an ordinary Bloom filter can test possible membership but cannot list both sides' missing IDs.",
         mistakes=["Do not return a partial peel as a complete replica diff.", "Do not insert duplicate IDs when the contract is set reconciliation.", "Do not use different hash parameters for the two replicas.", "Do not treat a checksum as a proof against deliberate collisions."],
         related=["dsa/counting-bloom-filter-balanced-deletion", "dsa/merkle-tree-indexed-inclusion-proof", "dsa/cuckoo-filter-fingerprint-relocation", "dsa/run-length-bitmap-set-algebra", "dsa/bloom-filter-membership-boundary", "dsa/scalable-bloom-filter-layer-growth"]),
    dict(path="dsa/de-bruijn-graph-unitig-kmer-index", program="debruijn_unitig_routes.py",
         template="dsa/csr-sparse-graph-storage", section="dsa/graphs-and-disjoint-sets",
         title="De Bruijn graphs: compact non-branching k-mer routes into unitigs",
         summary="Make each distinct k-mer an edge and stop compaction at branch vertices.",
         definition="A de Bruijn graph built from fixed-length k-mers uses each length-(k−1) prefix as an edge source and its length-(k−1) suffix as the destination. The k-mer itself is the directed edge. A unitig follows a maximal path whose internal vertices have exactly one incoming and one outgoing edge. Branches stop extension, preserving alternative routes instead of silently choosing one. This builder deduplicates input k-mers, rejects mixed lengths and k less than two, and retains explicit incoming and outgoing edge lists. After starting paths at branch or endpoint vertices, it processes any unused edges, which covers isolated one-in/one-out cycles. Each returned sequence spells its represented edges by taking the first k-mer and appending the last character of each successor. It does not estimate coverage, resolve repeats, or assemble an original genome.",
         case="The k-mers ATG, TGA, GAC, ACT, CTG, TGC, and GCA form three displayed unitigs: ATG, TGACTG, and TGCA. Vertex TG branches toward GA and GC, so the compacted paths do not claim one unique continuation across it. The first k-mer of every path supplies the initial two characters; appending a successor's final character spells each later edge once. Duplicate input k-mers are collapsed to one edge. If the task needs multiplicity or read depth, a count field must be added instead of assuming the deduplicated graph retains it. An isolated directed cycle may be represented with an arbitrary sorted starting edge; its rotation is not a canonical biological result.",
         cost="Let E be the number of distinct k-mers and V the number of observed prefix/suffix vertices. Building edge lists takes O(Ek) time due to slicing k-character strings and O(Ek + V) Python storage. Sorting k-mers and vertices for stable output adds O(E log E + V log V) comparisons with string costs. The graph walk marks each edge once, but repeated Python string concatenation can make one long output path quadratic in its length; collecting characters and joining once would remove that avoidable copying. A CSR graph is a better frozen general-purpose adjacency layout, while this structure uses overlap semantics specific to equal-length strings.",
         mistakes=["Do not extend a unitig through a vertex with two outgoing choices.", "Do not forget isolated one-in/one-out cycles after endpoint walks.", "Do not interpret deduplicated edges as read coverage counts.", "Do not claim that unitig compaction reconstructs one unique source sequence."],
         related=["dsa/csr-sparse-graph-storage", "dsa/static-compressed-suffix-tree-pattern-locations", "dsa/suffix-array-lcp-incident-search", "dsa/fm-index-backward-substring-search", "dsa/scc-condensation-reachability-index", "dsa/bitset-transitive-reachability-snapshot"]),
]

for number, lesson in enumerate(lessons):
    path = lesson["path"]
    assert path not in by_path
    program = (root / "work/dsa-programs" / lesson["program"]).read_text().rstrip()
    run = subprocess.run([sys.executable, "-c", program], check=True, capture_output=True, text=True)
    related = [lesson["section"], subject, *lesson["related"], "dsa/projects", "dsa/quizzes"]
    body = "<p>" + html.escape(lesson["definition"]) + "</p>"
    body += "<h2>Operational case</h2><p>" + html.escape(lesson["case"]) + "</p>"
    body += '<h2>Working Python program</h2><pre><code class="language-python">' + html.escape(program, quote=False) + "</code></pre>"
    body += '<h3>Output</h3><pre><code class="language-text">' + html.escape(run.stdout.strip()) + "</code></pre>"
    body += "<h2>Time, space, and tradeoff</h2><p>" + html.escape(lesson["cost"]) + "</p>"
    body += "<h3>Common Mistakes</h3><ul>" + "".join("<li>" + html.escape(item) + "</li>" for item in lesson["mistakes"]) + "</ul>"
    body += "<h2>Connected lessons</h2>" + links(related)
    entry = copy.deepcopy(by_path[lesson["template"]])
    entry.update(id=str(uuid.uuid5(uuid.NAMESPACE_URL, "aitrove:" + path)), path=path, title=lesson["title"],
                 summary=lesson["summary"], body=body, sort_order=46600 + 10 * number,
                 created_at=stamp, updated_at=stamp, published_at=stamp)
    entry["data"].update(section_path=lesson["section"],
                         related=[{"path": target, "title": by_path[target]["title"]} for target in related])
    entries.append(entry)
    by_path[path] = entry
    for hub_path in (lesson["section"], subject):
        hub = by_path[hub_path]
        module = hub["data"]["modules"][0] if hub_path == lesson["section"] else next(
            module for module in hub["data"]["modules"] if module["title"] == by_path[lesson["section"]]["title"])
        module["lessons"].append(path)
        hub["body"] += '<p><a href="/' + path + '">' + html.escape(lesson["title"]) + "</a></p>"
        hub["updated_at"] = stamp

paths = [lesson["path"] for lesson in lessons]
project_path = "dsa/static-prefix-neighborhood-replica-unitig-audit-project"
quiz_path = "quizzes/dsa-prefix-neighborhood-replica-unitig-contracts"
project = copy.deepcopy(by_path["dsa/allocation-ownership-coalescing-audit-project"])
project.update(id=str(uuid.uuid5(uuid.NAMESPACE_URL, "aitrove:" + project_path)), path=project_path,
               title="Project: audit static prefixes, neighborhood placement, replica differences, and unitigs",
               summary="Test exact lookup, legal placement, all-or-failure decoding, and branch-preserving graph paths.",
               sort_order=46650, created_at=stamp, updated_at=stamp, published_at=stamp)
project["data"].update(reading_minutes=35,
                       related=[{"path": path, "title": by_path[path]["title"]} for path in paths])
project["body"] = "<p>Build four independent representations for one incident platform. Freeze the incident-code dictionary before BASE/CHECK placement. Keep shipment IDs inside a fixed hash neighborhood, reporting a failed add without losing existing IDs. Compare two unsigned-ID replica sets with a signed invertible table and publish a diff only after complete peeling. Build a k-mer overlap graph from route fragments and stop each unitig at a branch. The acceptance contract differs across these structures: exact static lookup, bounded-locality set mutation, probabilistic recovery with explicit failure, and graph compaction that preserves alternatives.</p>"
project["body"] += "<h2>Acceptance trace</h2><p>Store dock47 and dock83, then verify dock is a prefix but not a member. Insert colliding shipment IDs into a 31-slot table with width five; rejected placement must leave membership unchanged. Reconcile {19,29,47,61} against {19,47,83} and require left-only {29,61} plus right-only {83}. Feed seven three-character route fragments into the graph and compare the multiset of k-mers extracted from returned unitigs with the deduplicated input edges. Keep the original sets and code dictionary as independent oracles, rather than trusting a structure's own reported count.</p>"
project["body"] += "<h2>Failure and cost review</h2><p>Generate absent code prefixes and confirm CHECK rejects cross-parent slots. After every hash insertion or deletion, verify that each resident is within its own circular neighborhood; exercise a full table and an empty slot too distant to use. Force an overloaded reconciliation table and demand an explicit undecodable result. Include isolated directed cycles, branch vertices, and duplicate k-mers in graph cases. Record lookup length, relocation work, peel scans, and long unitig string copying separately. None of these models provides concurrent mutation or durable storage; rebuilding the frozen indexes and checking replica parameters belong to the surrounding service.</p>"
project["body"] += "<h3>Common Mistakes</h3><ul><li>Do not equate a reachable trie prefix with a stored terminal code.</li><li>Do not place a hash resident outside its home window to force success.</li><li>Do not publish a partial replica peel as an exact difference.</li><li>Do not compact a k-mer path across a graph branch.</li></ul>"
project["body"] += "<h2>Connected lessons</h2>" + links(paths + ["dsa/projects", "dsa/quizzes", subject])
entries.append(project)
by_path[project_path] = project

raw = [
    ("Which double-array field proves that a transition belongs to the current parent?", "CHECK at the computed slot", "The slot number alone", "The terminal flag at the root", "BASE computes a candidate slot, while CHECK confirms that this occupied slot is owned by the parent being traversed."),
    ("Does reaching the node for dock prove dock is a stored code?", "No, its terminal flag must be true", "Yes, every prefix is a stored code", "Only when the arrays have no holes", "Prefix reachability and exact membership are separate because a code may end after several additional transitions."),
    ("What happens after a new code is added to the source dictionary?", "Rebuild the frozen double-array layout", "Only change one terminal flag", "Reuse any empty array slot without checking", "The builder chooses offsets against the full set of child labels, so a source edit requires a new valid placement."),
    ("How far from its hash home may a resident sit?", "Fewer than H circular positions away", "Anywhere before the next empty slot", "Only at the exact home slot", "The fixed neighborhood invariant bounds every resident's circular displacement to offsets zero through H minus one."),
    ("Can a hopscotch insertion fail while a distant table slot is empty?", "Yes, if no legal relocation brings a hole into its window", "No, any empty slot guarantees success", "Only if the key is already present", "The set rejects placement when moving a hole toward home would push a resident beyond its own permitted neighborhood."),
    ("What remains true after a failed insertion that moved old keys?", "Old membership and every resident's neighborhood invariant", "Every slot retains its old occupant", "The capacity automatically doubles", "Relocations may change physical slots, but they preserve existing keys and each key's legal home distance."),
    ("What do shared IDs do when two replica tables are subtracted?", "Their signed cell changes cancel", "They appear on both output sides", "They always make decoding fail", "Each common ID touches the same positions and checksum, so equal positive and negative contributions cancel cell by cell."),
    ("When may the decoder report complete left-only and right-only sets?", "Only after every residual cell becomes zero", "After finding its first pure cell", "When any count is negative", "A nonzero residual means unrecovered differences may remain, so the decoder must return failure instead of partial success."),
    ("What is the supported ID domain of the sample reconciliation table?", "Distinct unsigned 64-bit integer IDs", "Arbitrary repeated strings", "Signed floating-point measurements", "The sample encodes each ID into eight bytes and models sets, so duplicate entries and other value types violate its contract."),
    ("What does one graph edge represent in the k-mer index?", "One distinct length-k string joining its prefix and suffix", "A complete original read", "A vertex with no overlap", "The edge uses the first k minus one characters as its source and the last k minus one as its destination."),
    ("Where must a maximal non-branching path stop?", "At a vertex without exactly one incoming and one outgoing edge", "At every second edge", "Only when a cycle closes", "A vertex with multiple choices or no continuation is a boundary; extending through it would hide alternatives."),
    ("Why process unused edges after starting at branch vertices?", "To cover isolated one-in/one-out cycles", "To count duplicate reads twice", "To make every path a unique source genome", "A cycle with only one-in/one-out vertices has no endpoint or branch start, so its edges need a separate pass."),
]
questions = []
for number, (prompt, correct, wrong_one, wrong_two, explanation) in enumerate(raw):
    assert len(explanation) >= 60
    answer = number % 3
    options = [wrong_one, wrong_two]
    options.insert(answer, correct)
    questions.append({"prompt": prompt, "options": options, "answer": answer, "explanation": explanation})
quiz = copy.deepcopy(by_path["quizzes/dsa-splay-and-resident-history-contracts"])
quiz.update(id=str(uuid.uuid5(uuid.NAMESPACE_URL, "aitrove:" + quiz_path)), path=quiz_path,
            title="Check prefix, neighborhood, replica, and unitig contracts",
            summary="Twelve explained decisions about static lookup, local placement, peel completion, and k-mer paths.",
            sort_order=46660, created_at=stamp, updated_at=stamp)
quiz["data"].update(duration_minutes=20,
                    related=[{"path": path, "title": by_path[path]["title"]} for path in paths + [project_path]],
                    questions=questions)
quiz["body"] = "<p>Choose the exact operation contract or failure result for each structure. Use the runnable traces to separate a stored item from a candidate, a legal placement from a merely empty slot, a complete diff from a partial peel, and a unitig from an arbitrary route.</p><h2>Lessons</h2>" + links(paths) + "<h2>Design exercise</h2>" + links([project_path, subject])
entries.append(quiz)
by_path[quiz_path] = quiz

for hub_path, destination in (("dsa/projects", project_path), ("dsa/quizzes", quiz_path)):
    hub = by_path[hub_path]
    hub["data"]["modules"][0]["lessons"].append(destination)
    hub["body"] += '<p><a href="/' + destination + '">' + html.escape(by_path[destination]["title"]) + "</a></p>"
    hub["updated_at"] = stamp
    root_module = next(module for module in by_path[subject]["data"]["modules"] if module["title"] == hub["title"])
    root_module["lessons"].append(destination)
    by_path[subject]["body"] += '<p><a href="/' + destination + '">' + html.escape(by_path[destination]["title"]) + "</a></p>"
    by_path[subject]["updated_at"] = stamp

for path in paths:
    entry = by_path[path]
    peers = [other for other in paths if other != path]
    entry["body"] += "<p>Compare the operation boundary with " + ", ".join(
        '<a href="/' + other + '">' + html.escape(by_path[other]["title"]) + "</a>" for other in peers)
    entry["body"] += ', then complete the <a href="/' + project_path + '">audit project</a> and <a href="/' + quiz_path + '">decision quiz</a>.</p>'
    entry["updated_at"] = stamp

for lesson in lessons:
    for old_path in lesson["related"][:2]:
        old = by_path[old_path]
        old["body"] += '<p><a href="/' + lesson["path"] + '">' + html.escape(lesson["title"]) + "</a> examines a related structure with a different operation boundary.</p>"
        old["updated_at"] = stamp

fixture.write_text(json.dumps(entries, ensure_ascii=False, indent=2) + "\n")
print(json.dumps({"lessons": len(lessons), "projects": 1, "quizzes": 1, "new_routes": 6}))
