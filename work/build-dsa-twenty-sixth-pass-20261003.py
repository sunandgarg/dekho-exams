"""Add compact integer and trie index lessons to the DSA fixtures."""

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
    dict(path="dsa/elias-fano-monotone-alert-ids", program="elias_fano_alert_ids.py",
         template="dsa/bitvector-rank-select-superblocks", section="dsa/hash-tables",
         title="Elias–Fano: split sorted IDs into low parts and high bits",
         summary="Represent a fixed increasing integer sequence and recover values by rank.",
         definition="Elias–Fano separates each strictly increasing integer into a fixed-width low part and a high part. The high parts are monotone; placing a one at high value plus element rank creates a bit sequence from which the high value can be recovered by select-one minus rank. The low parts retain the omitted bits. This lesson fixes a nonnegative universe bound and validates sorted, unique input before building the representation. It stores the high sequence as a Python list and also stores every one position for direct rank access. Those auxiliary positions make select constant time in this program but are extra machine-word storage, so its conceptual encoded-bit count is not a measurement of Python memory use. The structure is static. There is no insertion or deletion path.",
         case="A maintenance feed has alert IDs 13, 19, 47, 61, 83, and 129 in a universe below 256. Value at rank three is 61 using zero-based rank; the first value at least 50 is also 61. The lower-bound operation binary-searches reconstructed values and returns no result above the final ID. Duplicate alert IDs are rejected because the lesson indexes a strictly increasing set rather than a multiset. A large universe with few IDs changes the chosen lower-bit width, so copying one hard-coded width into another feed would decode incorrect values. The conceptual bit count covers only low parts and the high bit sequence, not list objects or the select-position helper.",
         cost="For N values in universe U, construction writes O(N + U / 2^L) conceptual high bits plus N low parts, where L is the selected lower width. At(rank) costs O(1) here because one positions are explicitly indexed. Lower bound costs O(log N) such accesses. The encoded representation has N times L low bits and about N + U / 2^L high bits; this Python model also stores O(N) integer references for select positions and unpacked bit/list elements. If a packed rank/select implementation replaces those helpers, its cost depends on that implementation. This structure is useful for immutable ordered IDs, not for a mutable incident queue.",
         mistakes=["Do not treat a conceptual bit count as measured Python heap use.", "Do not accept unsorted or repeated values in a strict-ID index.", "Do not forget to subtract rank from the selected high-bit position.", "Do not claim insertions are supported by an immutable encoding."],
         related=["dsa/bitvector-rank-select-superblocks", "dsa/coordinate-compression-ordered-ranks", "dsa/inverted-index-sorted-postings-intersection"]),
    dict(path="dsa/chunked-array-bitmap-alert-set", program="chunked_alert_bitmap.py",
         template="dsa/bitvector-rank-select-superblocks", section="dsa/hash-tables",
         title="Chunked integer sets: switch sparse arrays to dense bitmaps",
         summary="Partition a bounded integer set and choose a local representation by occupancy.",
         definition="A chunked integer set splits each 16-bit alert ID into an eight-bit high chunk key and an eight-bit low offset. Sparse chunks store sorted low offsets; dense chunks store a 256-bit integer mask. When an array passes 32 entries it promotes to a mask, and when a mask falls to 16 entries it demotes to an array. The two thresholds create hysteresis, avoiding representation switches on every insert/delete near one cutoff. Exact membership checks either binary-search the array or test a mask bit. Intersection visits chunk keys present in both sets, combines local masks, and emits exact IDs. This is a small explanatory hybrid, not a compatible serialized bitmap format or a benchmarked production library. It omits run containers, SIMD operations, rank/select, and cardinality-wide metadata.",
         case="The active set holds alert 47, 61, 83, and forty consecutive IDs starting at 512. A reviewed set holds 47, 129, 515, 516, and 517. Their intersection is 47, 515, 516, 517; the chunk for IDs 512 through 767 has promoted to a dense mask. A duplicate insertion changes nothing, and deleting an absent ID raises an error. During a long removal sequence, the dense chunk converts back to a sorted array only after its population reaches 16. That later threshold prevents a stream alternating around 32 from repeatedly allocating two different representations.",
         cost="Let K be the number of common chunks, A the maximum sparse-array population, and R the number of intersection results. Sparse membership costs O(log A), but insertion/removal shifts O(A) list entries. Dense bit tests and updates work on one bounded 256-bit integer, treated as O(1) in this fixed-domain model. Intersection converts sparse common chunks to masks in O(KA), performs bounded-width bit operations, and emits R IDs; sorting chunk keys adds O(K log K). Stored data is O(N + D * 256) conceptual bits across N sparse entries and D dense chunks, plus Python dictionary, list, and integer overhead. No compression ratio is promised for Python objects.",
         mistakes=["Do not confuse this two-container model with a full bitmap file format.", "Do not promote and demote at the same occupancy threshold.", "Do not count duplicate insertions twice.", "Do not return a chunk match before testing the low offset."],
         related=["dsa/bitvector-rank-select-superblocks", "dsa/hash-set-membership-and-order", "dsa/inverted-index-sorted-postings-intersection"]),
    dict(path="dsa/gap-varint-postings-seek-checkpoints", program="gap_varint_posting_seeks.py",
         template="dsa/inverted-index-sorted-postings-intersection", section="dsa/hash-tables",
         title="Gap-encoded postings: add checkpoints to bytewise seeks",
         summary="Store sorted document-ID differences as variable-length integers and bound local scans.",
         definition="A posting list contains strictly increasing document IDs. Subtracting the previous ID turns them into nonnegative gaps, and a seven-payload-bit byte code writes small gaps in fewer bytes than large ones. This program sets the high byte bit when another byte follows; a byte with that bit clear ends the integer. Every few postings it records the absolute document ID and byte offset immediately after its code. Seek-at-least binary-searches checkpoint IDs, starts after the greatest checkpoint no larger than the target, and decodes subsequent gaps until it finds a qualifying ID. The previous absolute ID is necessary because gaps cannot be interpreted independently. A checkpoint equal to the target answers directly. The list is immutable and stored as one bytearray plus Python checkpoint records.",
         case="A term appears in documents 47, 61, 83, 129, and 515. Seeking at least 80 returns 83; seeking at least 200 returns 515. With a checkpoint every two postings, a seek may skip a prefix of the byte stream before decoding the short local tail. The encoded gaps occupy six bytes in this particular trace, excluding checkpoint tuples and the Python bytearray header. That number should not be generalized into a compression guarantee: widely spaced IDs take more bytes, and dense checkpoints can cost more than they save for small lists. The parser rejects a truncated integer rather than silently accepting a partial document ID.",
         cost="Encoding N document IDs costs O(T) time and T bytes for the emitted byte stream, plus O(N / S) checkpoints at stride S. Full iteration costs O(T + N). Seek-at-least costs O(log(N / S) + S * B) time in the worst local block, where B is the maximum encoded bytes in one scanned gap; for arbitrary-size Python integers B is not a fixed constant. Memory includes T bytes and checkpoint records, not just the byte count printed by the example. This implementation does not support in-place updates, phrase positions, term frequencies, or direct random access to posting rank without scanning from a checkpoint.",
         mistakes=["Do not decode a gap without the preceding absolute ID.", "Do not forget that a checkpoint offset points after its encoded posting.", "Do not count stream bytes as total index memory.", "Do not accept a truncated variable-length integer as a complete posting."],
         related=["dsa/inverted-index-sorted-postings-intersection", "dsa/positional-inverted-index-phrase-matching", "dsa/front-coded-term-lexicon-blocks"]),
    dict(path="dsa/louds-level-order-alert-trie", program="louds_alert_trie.py",
         template="dsa/trie-prefix-index-and-terminal-flag", section="dsa/trees-and-heaps",
         title="Level-order unary degree tries: encode child runs as bits",
         summary="Read a static trie through degree bits, edge labels, and terminal flags.",
         definition="A level-order unary degree sequence writes one bit for each outgoing edge of a node, followed by a zero that ends that node's child run. Nodes are visited breadth-first. Because edges are emitted in that order, the rank of a one bit identifies its child node number; the matching edge label sits at child number minus one. A previous zero marks where the current node's run begins, and the current zero marks where it ends. This lesson builds an ordinary temporary trie, emits the level-order arrays, then answers exact-word and prefix lookup using only those emitted arrays. It keeps explicit zero positions and one-rank prefixes for easy navigation. They are Python integer lists, so the model illustrates the encoding relation but is not a compact succinct implementation with packed bits and sampled rank/select directories.",
         case="A static alert dictionary contains alert, alloy, bay, and badge. Exact lookup accepts alert, prefix lookup accepts al, and exact lookup rejects al because no terminal flag marks that prefix as a full key. The encoded tree has fifteen nodes, including the empty root. Children are emitted in sorted label order, so a lookup can stop scanning a child run once it passes the requested character. An empty string may still be a valid exact key if it was included during construction; its terminal flag belongs to the root. After construction, adding a term would require rebuilding the level-order layout and its rank/zero helpers.",
         cost="Building a temporary trie takes O(M) character visits for M total input characters, plus child-label sorting at each node before encoding. The emitted degree sequence has 2V - 1 bits for V nodes, with V - 1 edge labels and V terminal flags. This Python example also stores O(V) integer references for zero positions and rank prefixes, so those counts describe a conceptual layout rather than actual packed memory. Lookup visits one child run per character and costs O(sum of visited node degrees); with a fixed bounded alphabet it is O(P) for prefix length P, but a wide branching node can add scan work. It supports static exact and prefix existence only, not updates or autocomplete ranking.",
         mistakes=["Do not omit terminal flags for keys that end at internal trie nodes.", "Do not treat the root as an edge label.", "Do not call unpacked Python arrays a measured succinct index.", "Do not mutate the temporary trie after emitting a static level-order layout."],
         related=["dsa/trie-prefix-index-and-terminal-flag", "dsa/compressed-trie-edge-splitting", "dsa/bitvector-rank-select-superblocks"]),
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
                 sort_order=43100 + order * 10, created_at=stamp, updated_at=stamp, published_at=stamp)
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
project_path = "dsa/compact-integer-index-contract-audit-project"
quiz_path = "quizzes/dsa-compact-integer-index-contracts"
assert project_path not in by_path and quiz_path not in by_path
project = copy.deepcopy(by_path["dsa/editable-sequence-tradeoff-audit-project"])
project.update(id=str(uuid.uuid5(uuid.NAMESPACE_URL, "aitrove:" + project_path)), path=project_path,
               title="Project: audit compact alert and document indexes", summary="Compare encoded integer lookups, hybrid chunks, posting seeks, and static trie terms.",
               sort_order=43140, created_at=stamp, updated_at=stamp, published_at=stamp)
project["data"].update(reading_minutes=30, related=[{"path": path, "title": by_path[path]["title"]} for path in new_paths])
project["body"] = (
    "<p>An incident search service has sorted alert IDs, active alert sets, document postings, and a fixed alert-term dictionary. Build one exact reference model for each: a sorted integer list, Python sets, a sorted document-ID list, and a set of terms. Compare every encoded answer to the reference before discussing size. Record two different measurements: conceptual bits or stream bytes, and actual Python object storage. The first cannot establish the second. Reject out-of-domain IDs, unsorted postings, and missing terms according to each API. Keep the representation immutable where the lesson says it is immutable.</p>"
    "<h2>Acceptance trace</h2><p>For Elias–Fano, use IDs 13, 19, 47, 61, 83, and 129 below 256; rank three and lower bound 50 both return 61. Intersect an active chunked set with a reviewed set and obtain 47, 515, 516, and 517, with the active 512-series chunk promoted to a bitmap. Encode postings 47, 61, 83, 129, and 515; seek at least 80 and 200 to find 83 and 515. In the term trie, alert is an exact key, al is a prefix but not an exact key, and an absent term fails both lookups.</p>"
    '<h3>Expected review record</h3><pre><code class="language-text">lower-bound-50=61\nshared=[47, 515, 516, 517]\nseek-200=515\nal-prefix=True\nal-key=False</code></pre>'
    "<h2>Boundary and cost review</h2><p>Generate sorted integer samples with large gaps, empty lists, a first ID of zero, and targets before or after the list. Toggle enough chunk entries across the promotion and demotion thresholds, then compare every membership and intersection with exact sets. Decode the full posting stream and test targets on either side of checkpoints; corrupt a final continuation byte to confirm a truncated code is rejected. Compare term and prefix lookup with direct string tests, including an empty term. State the work required to rebuild each static layout and identify every auxiliary list excluded from a printed byte or bit count.</p>"
    "<h3>Common Mistakes</h3><ul><li>Do not present a conceptual encoding length as the process heap footprint.</li><li>Do not lose an absolute document ID at a seek checkpoint.</li><li>Do not count a trie prefix as a complete term without its terminal flag.</li><li>Do not toggle sparse and dense chunk types at one shared cutoff.</li></ul>"
    "<h2>Connected lessons</h2>" + links(new_paths + ["dsa/projects", "dsa/quizzes", subject_root])
)
entries.append(project)
by_path[project_path] = project

questions = [
    ("What is stored in the low part of an Elias–Fano value?", ["Its fixed-width least significant bits", "Its position in the Python object heap", "The number of zeros before the next high bit"], "The low part retains the fixed-width remainder while the high part is represented through one positions in a monotone bit sequence."),
    ("How is the Elias–Fano high value recovered at rank i?", ["Select its one position and subtract i", "Add the universe size to i", "Count only the low-part bits"], "The one for rank i is placed at high value plus i, so subtracting i recovers that high value before recombination."),
    ("Why does the example not prove a Python memory saving?", ["It stores unpacked bit entries and an extra list of one positions", "It refuses to decode ranked values", "Every encoded integer is a decimal string"], "The printed bit count excludes Python list and integer objects, including the direct-select positions kept by the teaching program."),
    ("When does the chunked alert set promote a sparse container?", ["After its population exceeds the sparse cutoff", "After every duplicate insertion", "Only when an ID changes its high chunk key"], "Promotion occurs when one chunk's sorted low-offset array passes the configured threshold, switching that chunk to a bit mask."),
    ("Why are separate promotion and demotion cutoffs useful?", ["They prevent representation thrashing near a single boundary", "They remove the need to track membership", "They make every intersection independent of chunk keys"], "Hysteresis allows occupancy to move through an interval without repeatedly allocating array and bitmap forms."),
    ("What must be checked after two sets share a chunk key?", ["Which low-offset bits or array entries overlap", "Whether the chunk IDs have the same text label", "Only the total number of chunks"], "Equal high chunks identify candidate regions; intersection still requires exact low-offset membership within each shared region."),
    ("Why are gaps useful for sorted posting IDs?", ["Nearby IDs produce small nonnegative differences", "They make the list mutable without rewriting bytes", "They erase the requirement for sorted IDs"], "Taking differences from the previous absolute document ID often makes values smaller for dense postings, which can reduce variable-byte length."),
    ("What does a posting checkpoint store for a seek?", ["An absolute ID and the byte offset immediately after its code", "Only the term's first character", "A pointer into an unrelated bitmap"], "A decoder needs an absolute starting ID and a byte position to interpret following gaps without rescanning the entire prefix."),
    ("What must the byte decoder do if every remaining byte says more bytes follow?", ["Reject the truncated integer", "Return the partial value as a document ID", "Treat the final continuation bit as zero automatically"], "A continuation-marked tail is incomplete and cannot safely establish the next posting ID."),
    ("What does a zero bit mark in the level-order trie encoding?", ["The end of one node's child run", "A terminal word by itself", "The root's outgoing edge label"], "Each node emits one bits for outgoing edges followed by one zero delimiter, which separates its children from the next node's run."),
    ("Why is a prefix not automatically an exact trie key?", ["The reached node must also carry a terminal flag", "Every prefix has a separate hash collision", "The level-order bits contain no child runs"], "Traversal can reach a valid prefix node without that node marking the end of an inserted term."),
    ("Why is this level-order trie a static teaching model?", ["Adding a term changes breadth-first node order and auxiliary navigation arrays", "Its edge labels are stored only in source code", "It cannot answer prefix existence"], "The emitted arrays are built for one fixed dictionary; insertion would require rebuilding the layout and rank/zero helpers."),
]
balanced = []
for number, (prompt, options, explanation) in enumerate(questions):
    distractors = options[1:]
    position = number % 3
    distractors.insert(position, options[0])
    balanced.append({"prompt": prompt, "options": distractors, "answer": position, "explanation": explanation})
quiz = copy.deepcopy(by_path["quizzes/dsa-gap-rope-block-sequence-contracts"])
quiz.update(id=str(uuid.uuid5(uuid.NAMESPACE_URL, "aitrove:" + quiz_path)), path=quiz_path,
            title="Compact integer sets, postings, and tries", summary="Check encoding boundaries, exact membership, checkpoint seeks, and term flags.",
            sort_order=43150, created_at=stamp, updated_at=stamp, published_at=stamp)
quiz["data"].update(duration_minutes=20, related=[{"path": path, "title": by_path[path]["title"]} for path in new_paths + [project_path]], questions=balanced)
quiz["body"] = "<p>Match each compact index to its immutable or mutable contract. Distinguish conceptual encoding size from Python storage and verify exact results after every coarse filter.</p><h2>Lessons</h2>" + links(new_paths) + "<h2>Design exercise</h2>" + links([project_path, subject_root])
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
    ("dsa/bitvector-rank-select-superblocks", new_paths[0]),
    ("dsa/bitvector-rank-select-superblocks", new_paths[1]),
    ("dsa/inverted-index-sorted-postings-intersection", new_paths[1]),
    ("dsa/inverted-index-sorted-postings-intersection", new_paths[2]),
    ("dsa/trie-prefix-index-and-terminal-flag", new_paths[3]),
    ("dsa/compressed-trie-edge-splitting", new_paths[3]),
):
    old = by_path[old_path]
    old["body"] += '<p><a href="/' + new_path + '">' + html.escape(by_path[new_path]["title"]) + "</a> adds a compact lookup contract.</p>"
    old["updated_at"] = stamp
for path in new_paths:
    entry = by_path[path]
    peers = [other for other in new_paths if other != path]
    entry["body"] += '<p>Compare its storage and lookup contract with ' + ", ".join('<a href="/' + other + '">' + html.escape(by_path[other]["title"]) + "</a>" for other in peers) + ', then run the <a href="/' + project_path + '">index audit</a> and <a href="/' + quiz_path + '">contract quiz</a>.</p>'
    entry["updated_at"] = stamp

fixture.write_text(json.dumps(entries, ensure_ascii=False, indent=2) + "\n")
print(json.dumps({"lessons": new_paths, "project": project_path, "quiz": quiz_path, "questions": len(questions)}))
