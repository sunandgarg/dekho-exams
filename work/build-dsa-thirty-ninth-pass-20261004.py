"""Add four standalone DSA structures and linked draft assessments."""

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
    dict(path="dsa/adaptive-radix-node-fanout-incident-codes", program="adaptive_radix_incident_codes.py",
         template="dsa/compressed-trie-edge-splitting", section="dsa/trees-and-heaps",
         title="Adaptive radix trees: grow byte-edge nodes as incident codes branch",
         summary="Compress shared byte prefixes and promote child storage through four fanout tiers.",
         definition="An adaptive radix tree indexes byte-string keys by common prefixes and grows a node's child representation as its fanout rises. This model stores a compressed prefix in each node, then uses Node4 or Node16 parallel label and child arrays, a Node48 label-to-child-position array, or a direct Node256 child array. A new key can split an existing compressed prefix at the first mismatching byte, creating a parent for the common run and two separate branches. A value may live at an internal node when one complete code prefixes longer codes. Promotion changes only the local child representation; it must preserve every outgoing byte and child. The program supports insertion with replacement and exact lookup of byte strings. It does not delete keys, shrink tiers, or persist nodes to disk. Python objects make this an operation model, not a measured compact-memory implementation.",
         case="Nineteen codes start with rack and end in distinct byte values from zero through eighteen. Their shared rack prefix lives across the root edge r and a compressed ack run. The ack node has nineteen children, so it has promoted past Node4 and Node16 into the Node48 representation. A value of 83 is then stored on the shorter key rack, while rack followed by byte eighteen returns 4718; byte nineteen is absent. Splitting rack from a longer code must preserve the existing children. An empty byte string is also a valid key in this implementation, and zero is a valid stored value; a missing lookup is represented by None, so callers should avoid using None as a meaningful value.",
         cost="For a key of L bytes, traversal compares at most L prefix bytes and performs one child lookup per branch, giving O(L) time with a fixed 256-byte alphabet. Node4 and Node16 linearly scan at most their tier capacities; Node48 and Node256 use indexed access. A promotion copies the node's current children and allocates its new representation, bounded by 256 slots but visible as a single-operation cost. Storage is O(S + N) for S retained key-prefix bytes and N nodes in this Python model, with substantial list and object overhead. Prefix splitting copies byte substrings. Unlike the prior static double-array trie, this one accepts new keys without rebuilding the whole dictionary, but lookup order and node identity are not stable after edits.",
         mistakes=["Do not discard the old child when splitting a compressed prefix.", "Do not confuse a prefix node's stored value with all descendant values.", "Do not call Python list tiers a verified compact native layout.", "Do not promise deletion or tier shrinkage that the model does not implement."],
         related=["dsa/double-array-trie-static-incident-codes", "dsa/compressed-trie-edge-splitting", "dsa/louds-level-order-alert-trie", "dsa/ternary-search-tree-incident-completion", "dsa/binary-radix-longest-prefix-routes", "dsa/trie-prefix-index-and-terminal-flag"]),
    dict(path="dsa/bit-sliced-index-sensor-range-filters", program="bit_sliced_sensor_readings.py",
         template="dsa/bitvector-rank-select-superblocks", section="dsa/array-data-structure-guide",
         title="Bit-sliced indexes: filter and sum fixed-width sensor readings",
         summary="Store one row bitmap per value bit and combine slices for exact numeric predicates.",
         definition="A bit-sliced index transposes a fixed-width unsigned numeric column into one bitmap per bit position. Bit j is set at row r when the value in row r has bit j set. A less-than query scans slices from most significant to least significant, retaining rows still equal to the threshold prefix and adding rows whose first differing bit is lower. Two such masks make a closed-range filter. A sum over selected rows counts set bits in each slice and weights them by that slice's numeric bit value. The model also supports replacing one existing row by setting or clearing its bit in every slice. Its row domain and bit width are fixed at construction. It retains the source values for audit and does not expose insertion, deletion, null semantics, signed encoding, or compressed bitmaps.",
         case="Readings 47, 19, 83, 29, 61, and 47 occupy six row positions. The closed range from 29 through 61 selects rows 0, 3, 4, and 5 and sums to 184. Replacing the 83 at row 2 with 37 adds that row to the same filter and raises the sum to 221. The range uses both endpoints; its mask is a set of row IDs rather than a sorted list of values. A query below zero returns no rows, while a threshold beyond the unsigned width includes every row. Editing row 2 must change every affected slice; updating only one bitmap would make a range predicate disagree with the stored value.",
         cost="For B value bits and N rows, the logical bitmap payload is B times N bits, plus the retained N values and Python big-integer overhead. Construction and a point replacement touch B bit positions. A less-than predicate uses O(B) big-integer bitmap operations; its machine cost also depends on N divided by the word size, so it is not truly constant per slice. A closed range performs two comparisons and bitwise combination. A selected sum performs B intersections and bit counts. Dense row masks can be effective for repeated analytic predicates, but sparse posting lists may store a low-cardinality selection more economically. An ordinary rank/select bitvector answers positions in one bitmap; this index represents the bits of numeric values across many row bitmaps.",
         mistakes=["Do not read a row mask as a value-ordered result list.", "Do not drop the upper endpoint from a closed-range predicate.", "Do not leave stale bit slices after a point replacement.", "Do not describe Python big-integer bitmap work as O(1) independent of row count."],
         related=["dsa/bitvector-rank-select-superblocks", "dsa/chunked-array-bitmap-alert-set", "dsa/run-length-bitmap-set-algebra", "dsa/wavelet-matrix-static-rank-quantile", "dsa/square-root-range-mode-readings", "dsa/two-dimensional-prefix-grid-sums"]),
    dict(path="dsa/simhash-banded-incident-near-duplicates", program="simhash_incident_near_duplicates.py",
         template="dsa/minhash-banded-incident-candidates", section="dsa/hash-tables",
         title="SimHash bands: find near-duplicate incident fingerprints",
         summary="Hash weighted tokens into 64 bits, use exact matching bands for candidates, then verify Hamming distance.",
         definition="A SimHash fingerprint maps weighted tokens into a fixed-width bit vector. Each token's digest adds or subtracts its positive weight at every bit; the sign of each accumulated position chooses the output bit. Similar feature bags often produce nearby fingerprints, though similarity of source incidents is not guaranteed by a particular Hamming threshold. This index cuts each 64-bit fingerprint into equal contiguous bands and posts incident IDs under their band values. A query unions all IDs sharing at least one band, then computes the full XOR bit count to verify Hamming distance. With eight bands, accepting a distance of at most seven guarantees candidate recall for indexed fingerprints inside that distance: fewer than eight differing bits cannot disturb all eight bands. Larger thresholds are rejected because one-band matching would then have false negatives. The model indexes distinct IDs and has no update or delete method.",
         case="Incident 47 contains weighted dock, scanner, and timeout tokens; incident 83 contains weather and road tokens. Each queried feature bag finds its matching ID at Hamming distance zero. A modified token bag can yield a small or large distance depending on hashed bit interactions; this is a fingerprint index rather than exact text equality. The returned pair includes the incident ID and verified distance. Bands are only a candidate generator. A candidate with a shared band but excessive full distance is removed, and an incident within seven differing bits cannot be missed by the eight-band index. An empty feature bag and nonpositive weights are rejected instead of producing an arbitrary all-zero fingerprint.",
         cost="For F tokens and W fixed at 64 bits, fingerprinting performs O(FW) bit-weight updates and keeps O(W) temporary scores. An insertion posts one ID to each of eight band buckets. A query reads eight buckets, deduplicates C candidate IDs, and verifies each by one 64-bit XOR and bit count, costing O(FW + C) under fixed-width word operations and O(C) temporary memory. In the worst case every indexed ID shares a band, so C equals N and the query scans the corpus; the bucket index makes no sublinear worst-case promise. Stored fingerprints and postings use O(N times eight) ID references before Python container overhead. MinHash addresses a different set-similarity signal, while this page verifies Hamming distance of weighted-token fingerprints.",
         mistakes=["Do not report a shared band as a verified near duplicate.", "Do not use a threshold of eight or more with an eight-band recall claim.", "Do not equate small fingerprint distance with semantic equivalence.", "Do not insert the same incident ID twice without a removal or replacement policy."],
         related=["dsa/minhash-banded-incident-candidates", "dsa/bk-tree-edit-distance-label-search", "dsa/vantage-point-metric-nearest-depot", "dsa/trigram-index-verified-substring-candidates", "dsa/count-sketch-signed-incident-frequencies", "dsa/static-xor-filter-membership"]),
    dict(path="dsa/minimal-acyclic-incident-word-dictionary", program="minimal_dag_incident_dictionary.py",
         template="dsa/trie-prefix-index-and-terminal-flag", section="dsa/trees-and-heaps",
         title="Minimal acyclic dictionaries: merge equivalent word suffix states",
         summary="Build a trie, intern equal terminal-and-transition signatures, then query a shared DAG.",
         definition="A minimal acyclic deterministic word dictionary recognizes a fixed finite set of strings while sharing states with identical future accepted suffixes. Build a normal trie first. In postorder, assign each node a signature containing its terminal flag and sorted character-to-canonical-child transitions; intern nodes with equal signatures as one state. Terminal status is part of the signature because a complete word and a nonterminal prefix cannot be merged merely because their child edges match. The resulting directed acyclic graph may have several incoming paths to one state, and each distinct state represents one right-language of suffix continuations. Lookup follows one labeled transition per character and accepts only when the final state is terminal. The builder deduplicates input words and supports the empty string through a terminal root. It is static; adding a word would require rebuilding or a more involved incremental minimization algorithm.",
         case="The dictionary contains dock47, rack47, dock83, and rack83. Both prefixes share the same two suffix choices, so equivalent suffix states merge even though the visible word prefixes differ. The sample has nine canonical states. Looking up rack47 succeeds, but rack alone fails because it reaches a nonterminal prefix state. A normal trie for these four strings retains separate suffix paths; the shared graph can reduce state count without changing accepted words. State numbers depend on postorder interning and are not durable IDs. Attaching a mutable payload directly to a shared state could mix values from different full words, so this model stores terminal membership only.",
         cost="Let S be the total input character count and A the maximum outgoing alphabet size. Building the temporary trie uses O(S) nodes and expected O(S) dictionary updates. Sorting each node's outgoing labels and hashing its signature yields approximately O(S log A) work under ordinary Python dictionary assumptions, plus O(S) temporary and retained state storage in the worst case. Recursion depth follows the longest word and may exceed Python's recursion limit. Lookup costs O(L) expected dictionary transitions for a length-L word and O(1) auxiliary space. Sharing is workload-dependent: a dictionary with few repeated future suffix languages may save little. A compressed trie merges unary paths; this automaton merges equivalent future languages, which is a different reduction.",
         mistakes=["Do not omit terminal status from a state's canonical signature.", "Do not attach per-word mutable payloads to a state reached by several words.", "Do not treat a prefix path as an accepted word without its terminal flag.", "Do not mutate the original word set while keeping this frozen automaton."],
         related=["dsa/trie-prefix-index-and-terminal-flag", "dsa/double-array-trie-static-incident-codes", "dsa/compressed-trie-edge-splitting", "dsa/front-coded-term-lexicon-blocks", "dsa/suffix-automaton-online-substrings", "dsa/fm-index-backward-substring-search"]),
]

for number, lesson in enumerate(lessons):
    path = lesson["path"]
    assert path not in by_path
    program = (root / "work/dsa-programs" / lesson["program"]).read_text().rstrip()
    output = subprocess.run([sys.executable, "-c", program], capture_output=True, text=True, check=True).stdout.strip()
    related = [lesson["section"], subject, *lesson["related"], "dsa/projects", "dsa/quizzes"]
    body = "<p>" + html.escape(lesson["definition"]) + "</p>"
    body += "<h2>Operational case</h2><p>" + html.escape(lesson["case"]) + "</p>"
    body += '<h2>Working Python program</h2><pre><code class="language-python">' + html.escape(program, quote=False) + "</code></pre>"
    body += '<h3>Output</h3><pre><code class="language-text">' + html.escape(output) + "</code></pre>"
    body += "<h2>Time, space, and tradeoff</h2><p>" + html.escape(lesson["cost"]) + "</p>"
    body += "<h3>Common Mistakes</h3><ul>" + "".join("<li>" + html.escape(item) + "</li>" for item in lesson["mistakes"]) + "</ul>"
    body += "<h2>Connected lessons</h2>" + links(related)
    entry = copy.deepcopy(by_path[lesson["template"]])
    entry.update(id=str(uuid.uuid5(uuid.NAMESPACE_URL, "aitrove:" + path)), path=path, title=lesson["title"],
                 summary=lesson["summary"], body=body, sort_order=46800 + 10 * number,
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
project_path = "dsa/adaptive-bit-slice-simhash-dag-audit-project"
quiz_path = "quizzes/dsa-adaptive-bit-slice-simhash-dag-contracts"
project = copy.deepcopy(by_path["dsa/allocation-ownership-coalescing-audit-project"])
project.update(id=str(uuid.uuid5(uuid.NAMESPACE_URL, "aitrove:" + project_path)), path=project_path,
               title="Project: audit adaptive nodes, bit slices, fingerprint bands, and shared word states",
               summary="Check four indexes against exact models and their declared update or approximation boundaries.",
               sort_order=46850, created_at=stamp, updated_at=stamp, published_at=stamp)
project["data"].update(reading_minutes=35,
                       related=[{"path": path, "title": by_path[path]["title"]} for path in paths])
project["body"] = "<p>An incident service keeps byte codes, numeric sensor readings, weighted text fingerprints, and a fixed command dictionary. These are four separate indexes. The adaptive radix tree changes representation as byte-edge fanout grows; the bit-sliced index answers exact numeric predicates over fixed rows; SimHash bands generate candidates that must pass a full Hamming check; the minimal acyclic dictionary shares equivalent future word states after the vocabulary freezes. Keep one direct model for each input and compare answers after every supported edit. A shared product screen must still label approximate similarity separately from exact code, numeric, and dictionary membership.</p>"
project["body"] += "<h2>Acceptance trace</h2><p>Insert nineteen rack byte codes to force Node48 promotion, then insert the shorter rack code and verify its own value. Filter six readings between 29 and 61, sum the selected rows, replace the outlier 83 with 37, and require the new mask and sum. Index two weighted incident bags and check the two exact self-queries at Hamming distance zero. Build four words ending in either 47 or 83 under dock and rack prefixes; verify accepted full words, rejected shorter prefixes, and shared canonical states. Record source snapshots so a later change cannot silently reuse a frozen dictionary or stale fingerprint bucket.</p>"
project["body"] += "<h2>Failure and cost review</h2><p>Generate byte strings that split a compressed prefix at the first, middle, and last byte, and verify every old value survives promotion. Compare bit-sliced range masks and sums with a direct array after random replacements, including empty columns and thresholds outside the domain. For each fingerprint query with distance at most seven, compare banded results with a full scan of stored fingerprints; reject larger thresholds that lack the one-band recall guarantee. Compare every short string against a plain set for the acyclic dictionary, including the empty word. Measure Python object overhead separately from conceptual bitmap or node counts. None of these teaching models has a durable storage or concurrent-update contract.</p>"
project["body"] += "<h3>Common Mistakes</h3><ul><li>Do not lose an old radix child during a prefix split.</li><li>Do not update a reading without repairing every affected slice.</li><li>Do not confuse one matching band with verified Hamming distance.</li><li>Do not attach per-word mutable data to a shared dictionary state.</li></ul>"
project["body"] += "<h2>Connected lessons</h2>" + links(paths + ["dsa/projects", "dsa/quizzes", subject])
entries.append(project)
by_path[project_path] = project

raw = [
    ("When does an adaptive radix node move from Node16 to Node48?", "When a seventeenth distinct child byte is added", "When a code reaches sixteen bytes", "Whenever its value becomes zero", "Fanout determines the node tier, so a seventeenth distinct outgoing byte exceeds Node16 capacity and triggers promotion."),
    ("What must a compressed-prefix split retain?", "The old suffix branch and its values", "Only the new key's suffix", "The former node's numeric address", "The split introduces a common parent, then keeps both the former node under its remaining byte and the new branch."),
    ("What does lookup return for an absent byte code?", "None in this model", "A descendant's stored value", "The number of children in the nearest node", "Traversal stops when a prefix mismatches or a child edge is missing; the model uses None as its missing-value marker."),
    ("What does one bit-sliced bitmap represent?", "Rows whose numeric values have one particular bit set", "All rows containing one exact whole value", "Values sorted by their magnitude", "A slice is keyed by value-bit position and contains row positions with that bit set in their stored reading."),
    ("How is a closed numeric range obtained?", "Combine two less-than masks with an inclusive upper threshold", "Read only the highest value bit", "Sort the selected rows after every update", "Rows below upper plus one are included, then rows below the lower boundary are excluded from the mask."),
    ("What must point replacement repair?", "Every bit slice whose row bit changes", "Only the source value list", "Only the most significant slice", "A replacement can change several value bits, so stale slices would corrupt future filters and weighted sums."),
    ("Why verify Hamming distance after a shared SimHash band?", "Band equality only generates candidates", "A shared band proves equal feature bags", "Every band is a complete fingerprint", "Two fingerprints can agree in one contiguous band while differing in many of their other bits, so full XOR distance decides acceptance."),
    ("What threshold keeps eight-band candidate recall complete?", "At most seven differing bits", "Any threshold through sixty-four", "Only zero differing bits", "With fewer than eight differing bit positions, at least one of eight disjoint bands has no differing bit and matches exactly."),
    ("Does a small SimHash distance prove two incidents mean the same thing?", "No, it is only a fingerprint-distance signal", "Yes, semantic identity follows from one band", "Only if incident IDs are adjacent", "The hash maps weighted token signs to bits; a short Hamming distance alone does not establish semantic equivalence."),
    ("What belongs in a canonical acyclic-dictionary state signature?", "Terminal status and sorted labeled canonical-child transitions", "Only the incoming prefix text", "Only the number of outgoing edges", "States can be shared only when they accept the same future suffix language, including whether the empty continuation is accepted."),
    ("Why can two different word prefixes reach one state?", "Their remaining accepted suffix languages are identical", "Their full words have identical spellings", "All trie nodes at one depth are merged", "Bottom-up interning joins equivalent future behavior even when the paths leading to those states have different prefixes."),
    ("What happens after the static word set changes?", "Rebuild or apply an explicit incremental minimization algorithm", "Change the root state number alone", "Every old state automatically updates", "The frozen shared graph is derived from the complete vocabulary, so changing accepted words requires reconstructing valid state signatures."),
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
            title="Check adaptive nodes, bit slices, SimHash, and acyclic word states",
            summary="Twelve explained decisions about fanout, exact numeric masks, candidate verification, and suffix sharing.",
            sort_order=46860, created_at=stamp, updated_at=stamp)
quiz["data"].update(duration_minutes=20,
                    related=[{"path": path, "title": by_path[path]["title"]} for path in paths + [project_path]],
                    questions=questions)
quiz["body"] = "<p>Choose the operation or failure rule supported by each index. Test a byte-edge promotion, an exact row mask, a verified fingerprint distance, and a shared word-state transition against the runnable examples.</p><h2>Lessons</h2>" + links(paths) + "<h2>Design exercise</h2>" + links([project_path, subject])
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
    peers = [other for other in paths if other != path]
    entry = by_path[path]
    entry["body"] += "<p>Compare this operation boundary with " + ", ".join(
        '<a href="/' + other + '">' + html.escape(by_path[other]["title"]) + "</a>" for other in peers)
    entry["body"] += ', then complete the <a href="/' + project_path + '">audit project</a> and <a href="/' + quiz_path + '">decision quiz</a>.</p>'
    entry["updated_at"] = stamp

for lesson in lessons:
    for old_path in lesson["related"][:2]:
        old = by_path[old_path]
        old["body"] += '<p><a href="/' + lesson["path"] + '">' + html.escape(lesson["title"]) + "</a> examines a related structure with a different operation boundary.</p>"
        old["updated_at"] = stamp

fixture.write_text(json.dumps(entries, ensure_ascii=False, indent=2) + "\n")
print(json.dumps({"lessons": 4, "projects": 1, "quizzes": 1, "new_routes": 6}))
