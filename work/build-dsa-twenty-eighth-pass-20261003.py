"""Add advanced keyed-lookup lessons and a contract review."""

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
    dict(path="dsa/persistent-bitmap-hamt-alert-map", program="persistent_bitmap_hamt.py",
         template="dsa/persistent-ordered-index-path-copying", section="dsa/hash-tables",
         title="Bitmap hash tries: copy paths for immutable alert maps",
         summary="Index hash chunks through bitmaps while retaining prior map revisions.",
         definition="A hash-array mapped trie selects a child from successive chunks of a key's hash. This bounded model uses two four-bit chunks from an eight-bit integer digest. Each branch stores a bitmap of present slots and a dense tuple of children. Counting the set bits below a slot yields its tuple index. A leaf holds the original key and value, so lookup checks key equality rather than trusting a hash alone. Equal digests from distinct IDs end in a collision tuple. Updating a key allocates new tuples only along its route; unchanged subtrees remain shared by earlier roots. The map is immutable at its public boundary: set returns a new map instead of changing the old one. Its tiny deterministic digest makes collisions easy to demonstrate, not suitable for hostile inputs or a general-purpose hash table.",
         case="Alert IDs 47 and 303 have the same low eight bits. They occupy a collision node, yet each retrieves its own state because the terminal scan compares full IDs. Revision one stores 47 as open and 303 as review. Revision two changes only 47 to closed. Looking through revision one still returns open, while revision two returns closed and preserves the 303 value. A stored value of None is still a legitimate value because absence raises a KeyError; the lookup does not use None as a missing sentinel. Branch tuples hold only occupied slots, but Python tuple and integer overhead are not a measured compact-memory result.",
         cost="There are at most two branch levels in this eight-bit model. A branch insertion copies at most sixteen child references per level, and a collision node may copy and sort K key-value pairs, costing O(K log K). Lookup costs O(D + K) in the worst collision path for D hash chunks; here D is two. A new revision shares unaffected branches and adds O(D times 16 + K) references in the worst update. Keeping V revisions can retain old nodes and values until those roots are released. A larger fixed-width digest increases depth but does not remove adversarial collision risk without a suitable hash policy.",
         mistakes=["Do not equate equal digests with equal keys.", "Do not mutate a shared child tuple after issuing an old revision.", "Do not claim constant-time lookup when an entire collision bucket must be scanned.", "Do not call this eight-bit teaching digest resistant to chosen-key attacks."],
         related=["dsa/persistent-ordered-index-path-copying", "dsa/hash-map-collision-and-load-contract", "dsa/immutable-index-snapshot-publication"]),
    dict(path="dsa/ternary-search-tree-incident-completion", program="ternary_incident_terms.py",
         template="dsa/trie-prefix-index-and-terminal-flag", section="dsa/trees-and-heaps",
         title="Ternary search trees: branch by character and continue prefixes",
         summary="Use low, equal, and high character links for exact terms and completions.",
         definition="A ternary search tree stores one character in each node. A smaller character follows the left link without consuming the query position; a larger character follows the right link. An equal character consumes one position and follows the equal link. A terminal flag distinguishes a complete term from a prefix that merely leads to longer terms. This implementation also tracks the empty term explicitly because it has no character node. Its completion walk visits left, current, equal, then right branches, yielding lexicographic order under Python string comparison. Unlike a flat hash set, the structure exposes shared prefixes for enumeration. It is not balanced, so insertion order can create long left or right chains and a poor worst-case lookup.",
         case="The incident vocabulary contains alarm, alert, alpine, valve, and al. Requesting completions for al returns the shorter complete term first, followed by alarm, alert, and alpine. Asking whether alp is an exact term returns false even though it reaches a valid prefix path. Inserting an existing term again leaves a single terminal flag; it does not add a duplicate answer. A completion for an absent prefix returns an empty list. A full enumeration visits all stored character nodes, while a narrow prefix enumeration avoids branches before the matching prefix but still walks the entire matching subtree.",
         cost="Let P be prefix length, H the number of comparison nodes examined while finding it, and M the number of character nodes below it. Exact lookup costs O(H), which can approach O(N) for N stored characters in an unbalanced tree. Completion costs O(H + M + output characters) because results are materialized as new strings. Storage is O(N) nodes and pointers. Recursive insertion and enumeration also use O(tree height) call-stack space and can hit Python recursion limits on a deliberately skewed vocabulary. A balanced sibling-search scheme could improve comparisons, but this program keeps the node invariant visible.",
         mistakes=["Do not follow an equal link after a smaller or larger comparison.", "Do not accept a prefix as a complete term without its terminal flag.", "Do not promise logarithmic lookup from an unbalanced sibling search tree.", "Do not omit the empty term when the API allows it."],
         related=["dsa/trie-prefix-index-and-terminal-flag", "dsa/compressed-trie-edge-splitting", "dsa/louds-level-order-alert-trie"]),
    dict(path="dsa/binary-radix-longest-prefix-routes", program="longest_prefix_service_routes.py",
         template="dsa/binary-trie-maximum-xor-multiset", section="dsa/trees-and-heaps",
         title="Binary radix routing: choose the longest matching prefix",
         summary="Traverse fixed-width service IDs while retaining the deepest route seen.",
         definition="A binary radix routing trie reads a fixed-width key from its most significant bit. Each node has zero and one child links and may hold a gateway for the prefix ending at that depth. A default route is the root's gateway. Lookup walks the key bits and remembers the most recently seen gateway; when a child is absent, that remembered value is the longest matching prefix. The example rejects prefixes with nonzero host bits, preventing two numeric encodings of the same route from being treated as separate entries. It is an uncompressed binary trie, so a route can allocate one node per prefix bit. This route-selection contract differs from exact key membership or maximum-XOR queries over stored integers.",
         case="The service table has a fallback route, a four-bit north route, an eight-bit depot route, and a twelve-bit pump route. Service ID A947 in hexadecimal follows the pump prefix and returns pump. A983 follows the depot prefix but diverges before the pump-specific branch, so it returns depot. A key outside the north range returns fallback. Replacing a route at the same prefix changes that node's gateway without removing descendants; more-specific routes still win. A missing default route would return None when no stored prefix matches. The model uses sixteen-bit synthetic service identifiers, not address parsing or network-interface configuration.",
         cost="For width W, insertion visits L bits for prefix length L and costs O(L) time, allocating at most L nodes. Lookup visits at most W nodes and costs O(W) time with O(1) extra space. Across R routes, a naive upper bound is O(RW) nodes, although shared prefixes reduce the actual count. Neither operation scans all routes. This program does not delete routes, compress one-child paths, or support concurrent updates. Fixed width is part of its contract: accepting out-of-range keys without validation could silently alias distinct integers after truncation.",
         mistakes=["Do not return the first matching route when a deeper prefix may override it.", "Do not accept a prefix with nonzero bits outside its declared length.", "Do not confuse a longest-prefix route with exact membership in a bitwise trie.", "Do not silently truncate an identifier wider than the configured key width."],
         related=["dsa/binary-trie-maximum-xor-multiset", "dsa/trie-prefix-index-and-terminal-flag", "dsa/compressed-trie-edge-splitting"]),
    dict(path="dsa/extendible-hash-directory-bucket-splits", program="extendible_alert_directory.py",
         template="dsa/hash-map-collision-and-load-contract", section="dsa/hash-tables",
         title="Extendible hashing: split buckets through a shared directory",
         summary="Grow low-bit directory depth only when a full bucket needs another hash bit.",
         definition="An extendible hash directory indexes a bucket by the low global-depth bits of a digest. Multiple directory entries can refer to one bucket when that bucket's local depth is smaller. A full bucket splits using its next local-depth bit. If local depth already equals global depth, the directory doubles first, so the new bit becomes addressable. Records are then redistributed between the original and new bucket, and directory references are redirected by that bit. This model uses a deliberately bounded eight-bit digest of nonnegative alert IDs and a Python dictionary inside each bucket. Once two or more distinct IDs share all eight digest bits, they remain together as a collision overflow rather than triggering an impossible ninth-bit split. Deletion removes a record but does not merge buckets or shrink the directory.",
         case="Insert alert IDs 47, 51, 55, and 303 with bucket capacity two. Several low-bit prefixes must be distinguished, so the global directory reaches depth four; its sixteen entries refer to only five bucket objects. IDs 47 and 303 share the same eight-bit digest but still remain separate dictionary keys. Reading 303 returns its own incident record. Copying a directory entry during doubling does not clone its bucket: both entries initially point to the same object until a later split redirects some references. A consumer that assumes one unique bucket per directory position would double-count records during a scan.",
         cost="A lookup computes a directory slot and then uses expected O(1) Python dictionary access; a hostile set of equal digests is handled in one overflow bucket and inherits that dictionary's behavior. A split may scan and redistribute B records in its old bucket, while doubling copies 2^G directory references at global depth G. One insertion can therefore cost O(B + 2^G), and repeated splits may raise that cost further. The directory uses O(2^G) references plus stored records and bucket metadata, with G capped at eight here. This is an in-memory teaching model, not a paged database index with write-ahead logging, durability, bucket merge, or concurrency control.",
         mistakes=["Do not double the directory whenever any bucket splits; double only at equal local and global depth.", "Do not treat every directory entry as a distinct bucket object.", "Do not keep splitting after all configured hash bits are consumed.", "Do not claim deletion contracts the directory in this implementation."],
         related=["dsa/hash-map-collision-and-load-contract", "dsa/open-addressing-tombstones-rehash", "dsa/persistent-bitmap-hamt-alert-map"]),
]


def links(paths):
    return "<ul>" + "".join('<li><a href="/' + path + '">' + html.escape(by_path[path]["title"]) + "</a></li>" for path in paths) + "</ul>"


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
                 sort_order=43300 + order * 10, created_at=stamp, updated_at=stamp, published_at=stamp)
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
project_path = "dsa/keyed-lookup-trie-directory-audit-project"
quiz_path = "quizzes/dsa-hamt-term-route-directory-contracts"
assert project_path not in by_path and quiz_path not in by_path
project = copy.deepcopy(by_path["dsa/allocation-ownership-coalescing-audit-project"])
project.update(id=str(uuid.uuid5(uuid.NAMESPACE_URL, "aitrove:" + project_path)), path=project_path,
               title="Project: audit four keyed-lookup structures", summary="Compare immutable hash revisions, term completions, prefix routes, and bucket splits.",
               sort_order=43340, created_at=stamp, updated_at=stamp, published_at=stamp)
project["data"].update(reading_minutes=30, related=[{"path": path, "title": by_path[path]["title"]} for path in new_paths])
project["body"] = (
    "<p>An incident platform needs revisioned alert states, ordered term completion, service-route selection, and a growing alert-ID directory. Build an exact reference for each: one dictionary snapshot per revision, a sorted term set, a list of matching prefixes, and a current dictionary of alert records. Compare every answer after inserts and replacements. Use IDs 47 and 303 to force an eight-bit hash collision; never infer key equality from digest equality. Record how many directory references point to the same bucket before counting stored records. Keep the route width and hash width fixed so the exercise has an explicit failure boundary.</p>"
    "<h2>Acceptance trace</h2><p>Keep revision one of alert 47 open while revision two records closed; alert 303 remains review in both. Complete al to obtain al, alarm, alert, and alpine, while alp remains an incomplete term. Route A947 to pump, A983 to depot, and 3901 to fallback. Insert 47, 51, 55, and 303 into a two-record extendible directory and verify all four full IDs remain retrievable even though 47 and 303 share a digest. Test replacements as well as first insertions.</p>"
    '<h3>Expected review record</h3><pre><code class="language-text">old-47=open\nnew-47=closed\nalp-exact=False\nroute-A947=pump\nalert-303=incident-303</code></pre>'
    "<h2>Boundary and cost review</h2><p>Generate keys that collide on only their low four bits and keys that collide on all eight. Check historical roots after each replacement, compare every term prefix with direct string filtering, and select the deepest matching route by an independent mask scan. After each directory split, verify that every bucket's references agree with its local-depth low-bit pattern and that no record exists in two distinct buckets. Explain collision-bucket scans, skewed ternary trees, fixed route width, and directory-doubling cost without presenting these Python models as measured production memory layouts.</p>"
    "<h3>Common Mistakes</h3><ul><li>Do not overwrite a node shared by an older map revision.</li><li>Do not mark every reached term prefix as complete.</li><li>Do not stop at a short matching route when a deeper one exists.</li><li>Do not count directory aliases as separate stored buckets.</li></ul>"
    "<h2>Connected lessons</h2>" + links(new_paths + ["dsa/projects", "dsa/quizzes", subject_root])
)
entries.append(project)
by_path[project_path] = project

questions = [
    ("How does a bitmap branch locate a child in its dense tuple?", ["Count set bits below the selected slot", "Use the full alert ID as a tuple offset", "Scan every older map revision"], "A bit signals that the slot exists, and population count over lower bits gives its position among occupied tuple entries."),
    ("Why does the hash trie compare full IDs at a leaf?", ["Distinct IDs may share the same bounded digest", "Every branch stores complete route prefixes", "Tuple positions never reflect the hash"], "The digest selects a path but does not establish equality; the original key disambiguates colliding identifiers."),
    ("What preserves an older map revision after set?", ["New nodes are allocated along the changed path", "Every old root is modified in place", "All values are copied into an unrelated flat list"], "Path copying gives the updated map its own changed nodes while untouched subtrees remain safely shared with the earlier root."),
    ("Which ternary link consumes a query character?", ["The equal link", "The left link", "The right link"], "Only a character equal to the current node advances the query offset; smaller and larger comparisons stay at that offset."),
    ("Why can alp have completions without exact membership?", ["Its reached node lacks a terminal flag", "The tree cannot represent short terms", "Completion ignores all prefix characters"], "A path can lead toward longer stored words even when no inserted term ends at the current character node."),
    ("What drives a ternary tree toward linear comparison cost?", ["Long unbalanced left or right sibling chains", "Every term being stored in a single bitmap", "A fixed two-level hash digest"], "Without sibling balancing, insertion order can build a skewed comparison chain that lookup must inspect node by node."),
    ("What does longest-prefix lookup retain while walking bits?", ["The deepest gateway encountered so far", "Only the first gateway from the root", "A list of all hash-collision IDs"], "The most recently encountered route belongs to the longest matching stored prefix on the traversed path."),
    ("Why reject nonzero host bits when inserting a prefix?", ["They make multiple integers describe the same declared prefix", "They are needed to select a sibling hash bucket", "They force every route to be a default route"], "Bits outside the declared prefix are not part of its identity, so requiring zero prevents ambiguous numeric route representations."),
    ("What is the lookup bound for a fixed-width binary route trie?", ["At most one node per key bit", "Every route in the table must be scanned", "Only one node regardless of key width"], "Traversal follows one child for each inspected bit and stops on a missing child or after the configured width."),
    ("When does an extendible hash directory double?", ["When the overflowing bucket's local depth equals global depth", "On every record replacement", "Whenever two entries alias one bucket"], "A bucket split needs a new address bit only when its local depth has already reached the number of directory bits."),
    ("Why can several directory entries name one bucket?", ["The bucket may use fewer low hash bits than the directory", "Each entry always stores a separate full record copy", "The bucket has no local depth"], "A shallow bucket represents multiple directory prefixes until a split consumes another bit and redirects some aliases."),
    ("What happens when distinct IDs share all configured digest bits?", ["They remain distinguishable in a collision bucket", "The directory splits forever", "One ID silently replaces the other"], "The bounded model stops splitting after eight bits and retains full keys together in its bucket dictionary."),
]
balanced = []
for number, (prompt, options, explanation) in enumerate(questions):
    distractors = options[1:]
    position = number % 3
    distractors.insert(position, options[0])
    balanced.append({"prompt": prompt, "options": distractors, "answer": position, "explanation": explanation})
quiz = copy.deepcopy(by_path["quizzes/dsa-arena-free-buddy-slab-contracts"])
quiz.update(id=str(uuid.uuid5(uuid.NAMESPACE_URL, "aitrove:" + quiz_path)), path=quiz_path,
            title="Hash tries, term trees, routes, and directories", summary="Check collision identity, terminal terms, longest prefixes, and split rules.",
            sort_order=43350, created_at=stamp, updated_at=stamp, published_at=stamp)
quiz["data"].update(duration_minutes=20, related=[{"path": path, "title": by_path[path]["title"]} for path in new_paths + [project_path]], questions=balanced)
quiz["body"] = "<p>Match each keyed lookup to its equality, ordering, prefix, or directory contract. Inspect the collision and update boundaries before choosing a structure.</p><h2>Lessons</h2>" + links(new_paths) + "<h2>Design exercise</h2>" + links([project_path, subject_root])
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
    ("dsa/persistent-ordered-index-path-copying", new_paths[0]),
    ("dsa/hash-map-collision-and-load-contract", new_paths[0]),
    ("dsa/trie-prefix-index-and-terminal-flag", new_paths[1]),
    ("dsa/louds-level-order-alert-trie", new_paths[1]),
    ("dsa/binary-trie-maximum-xor-multiset", new_paths[2]),
    ("dsa/compressed-trie-edge-splitting", new_paths[2]),
    ("dsa/hash-map-collision-and-load-contract", new_paths[3]),
    ("dsa/open-addressing-tombstones-rehash", new_paths[3]),
):
    old = by_path[old_path]
    old["body"] += '<p><a href="/' + new_path + '">' + html.escape(by_path[new_path]["title"]) + "</a> adds a keyed lookup comparison.</p>"
    old["updated_at"] = stamp
for path in new_paths:
    entry = by_path[path]
    peers = [other for other in new_paths if other != path]
    entry["body"] += '<p>Compare lookup and update behavior with ' + ", ".join('<a href="/' + other + '">' + html.escape(by_path[other]["title"]) + "</a>" for other in peers) + ', then run the <a href="/' + project_path + '">index audit</a> and <a href="/' + quiz_path + '">contract quiz</a>.</p>'
    entry["updated_at"] = stamp

fixture.write_text(json.dumps(entries, ensure_ascii=False, indent=2) + "\n")
print(json.dumps({"lessons": new_paths, "project": project_path, "quiz": quiz_path, "questions": len(questions)}))
