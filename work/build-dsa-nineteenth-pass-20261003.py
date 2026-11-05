"""Add operational text-index structures with verified queries."""

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
section = "dsa/hash-tables"
stamp = datetime.datetime.now(datetime.UTC).isoformat()

lessons = [
    dict(
        path="dsa/inverted-index-sorted-postings-intersection", program="incident_postings.py",
        title="Inverted indexes: intersect sorted incident postings",
        summary="Map each exact term to sorted document IDs and answer all-term queries by merging lists.",
        definition="A document-level inverted index maps a term to the sorted IDs of documents containing that term. It stores each document ID only once per term, even if the term repeats inside the document. For an all-term query, sorted postings can be intersected with two advancing cursors; neither cursor needs to retreat. This implementation processes the shortest list first, retains the caller's exact pre-tokenized terms, and returns IDs in ascending order. A missing term makes the intersection empty. An empty query also returns an empty list by this API's choice, rather than matching every document. It builds one immutable snapshot and does not silently update the index when the source document collection changes.",
        case="Four incident records use IDs 103, 218, 347, and 492. Record 103 says valve, pressure, pressure; record 218 says pump, pressure; record 347 says valve, pressure, pump; record 492 says valve, sensor. The query valve AND pressure returns IDs 103 and 347. Valve AND sensor returns 492, and valve AND offline returns none. Pressure appears twice in record 103, yet that document ID appears once in its posting list. A Boolean query tests document membership, not how often a word occurs. Tokenization and case normalization must be agreed with upstream producers; this example deliberately accepts exact tokens as supplied.",
        cost="Let D be the number of documents, T the total supplied tokens, and P the total unique document-term pairs. Sorting document IDs costs O(D log D), and building postings requires O(T) expected set and hash work plus O(P) storage. A two-list intersection of lengths A and B takes O(A + B) time and O(min(A, B)) result space; several intersections take time proportional to the lists examined and intermediate results. A full document scan would revisit every record per query. A dictionary of unsorted ID sets may be simpler for small corpora, but sorted lists make merge behavior explicit and support compact ordered storage. This version has no deletion, ranking, or phrase semantics.",
        mistakes=["Do not add the same document ID twice for a repeated term.", "Do not assume document-level membership proves adjacent word order.", "Do not return the shortest posting list without intersecting the rest.", "Do not change source documents without rebuilding this immutable snapshot."],
        related=["dsa/hash-map-collision-and-load-contract", "dsa/trie-prefix-index-and-terminal-flag", "dsa/lsm-sorted-runs-tombstone-compaction"],
    ),
    dict(
        path="dsa/positional-inverted-index-phrase-matching", program="positional_incident_phrases.py",
        title="Positional postings: find exact token phrases",
        summary="Retain token offsets per document so repeated terms and adjacency can be checked.",
        definition="A positional inverted index extends term-to-document postings with every token offset at which the term appears. A phrase matches only when all query tokens occur at consecutive offsets in one document and in the requested order. Candidate document IDs first come from the intersection of term document sets; each candidate then tests aligned offsets. Repeated terms remain distinct positions, so a query for pressure pressure requires two adjacent occurrences rather than one occurrence counted twice. This implementation accepts pre-tokenized sequences and zero-based positions. It returns ascending document IDs, returns no documents for an empty phrase, and treats matching as exact token equality. Punctuation rules, stemming, and case folding are external indexing decisions.",
        case="Incident 103 contains pump pressure low pressure. Incident 218 contains low pump pressure. Incident 347 contains pump pressure pressure low. The phrase pump pressure appears in all three. Pressure low appears in 103 and 347. Pressure pressure appears only in 347. A document-level AND index would consider both terms present but could not distinguish pump pressure from pressure pump or test repeated-term adjacency. This positional example makes that distinction concrete. A later edit to one incident changes token offsets beyond the edit and requires a rebuilt snapshot in this simple design.",
        cost="Let T be the number of tokens across the corpus and F the number of stored occurrences. Index construction takes O(T) expected dictionary work and O(F) position storage. For a query of K terms, candidate-set intersection costs work tied to participating posting sets; within each candidate document, creating K position sets and checking starting positions costs O(sum of relevant stored positions plus K times the first-term occurrences) expected hash work. The worst case can approach the number of indexed positions examined. Positional postings use more memory than document-level postings, but answer phrase and proximity questions that the smaller structure cannot. This example is immutable and does not implement ranking or phrase slop.",
        mistakes=["Do not accept a document merely because all phrase terms appear somewhere in it.", "Do not collapse repeated token offsets into one position.", "Do not change tokenization rules between indexing and querying.", "Do not claim phrase order can be recovered from plain document ID lists."],
        related=["dsa/inverted-index-sorted-postings-intersection", "dsa/aho-corasick-failure-linked-alert-index", "dsa/suffix-array-lcp-incident-search"],
    ),
    dict(
        path="dsa/trigram-index-verified-substring-candidates", program="trigram_incident_candidates.py",
        title="Trigram indexes: filter and verify substring candidates",
        summary="Intersect three-character postings, then check the original text to remove false matches.",
        definition="A trigram index maps each distinct three-character slice to document IDs containing that slice. For a substring of at least three characters, every exact match must contain all of its trigrams, so intersecting those postings produces candidates. The intersection is only a filter: a document may contain the trigrams in different places or a different order. The final query checks the full fragment against original text before returning an ID. For fragments shorter than three characters, this implementation scans every document because it stores no shorter grams. Empty strings follow the host language's substring rule and match every stored document. Matching is exact by code point and case; there is no normalization layer or token boundary rule.",
        case="Records 103, 218, 347, and 492 contain pressure valve warning, pump pressure warning, valve sensor alert, and pressure pressure. Searching pressure returns 103, 218, and 492. Searching valve returns 103 and 347. The short fragment ps returns none after scanning the source strings. If separate fragments in a document happen to supply every trigram of a requested string, that record is still rejected unless the complete requested string occurs contiguously. This verification step is mandatory for correctness. The static index retains source text because a posting list alone cannot make that final decision.",
        cost="For total text length C, construction takes O(C) expected hash work and up to O(C) document-gram references, in addition to retaining O(C) source text. A query creates O(L) trigrams for a length-L fragment, intersects their posting sets, and verifies candidates by substring search. Its worst case still scans substantial source text; short fragments always check every document. Python's substring-search cost depends on implementation and content, so no blanket constant-time claim is made. The index helps when grams sharply cut the candidate set. A suffix array or automaton serves different substring workloads and may be preferable when exact substring queries dominate and the text snapshot is stable.",
        mistakes=["Do not return trigram candidates without checking the full fragment.", "Do not forget that a fragment shorter than three characters has no trigram filter.", "Do not normalize only the query or only the stored text.", "Do not treat a trigram match as a token or phrase match."],
        related=["dsa/inverted-index-sorted-postings-intersection", "dsa/suffix-array-lcp-incident-search", "dsa/suffix-automaton-online-substrings"],
    ),
    dict(
        path="dsa/front-coded-term-lexicon-blocks", program="front_coded_incident_terms.py",
        title="Front-coded lexicons: store shared prefixes within sorted term blocks",
        summary="Keep one full anchor per block and encode later terms as anchor-prefix lengths plus suffixes.",
        definition="A front-coded term lexicon sorts distinct terms and divides them into small blocks. It retains the first term of each block in full, then stores each later term as the length of its common prefix with that anchor plus its remaining suffix. Searching compares the request with block anchors, reconstructs one candidate block, and checks whether the exact term occurs there. The anchor rule is explicit: every encoded term refers to its block's first term, not to the preceding term. This form is easy to inspect but does not pack lengths into bytes or guarantee a net memory saving in Python, where tuples and strings have object overhead. It is a static dictionary without postings or token-frequency data.",
        case="Seven distinct incident terms include pressure, pressurize, pressurized, pump, pumps, valve, and valves. With blocks of three sorted terms, the first block reconstructs pressure, pressurize, pressurized. The exact term pressurized is present, while pressurizer is absent even though it shares a long prefix. A lookup for a string before the first anchor also fails. This demonstrates why prefix similarity is useful for storage but does not imply term membership. A new term inserted between existing anchors may change block boundaries and encoded suffixes, so this simple snapshot rebuilds rather than editing compressed storage in place.",
        cost="For U distinct terms with total character count C and block size K, sorting costs O(U log U) string comparisons and encoding scans shared prefixes up to O(C + U times anchor length) in a conservative bound. The stored payload consists of full anchors, prefix lengths, and suffixes; actual byte savings depend on term similarity and representation overhead. Searching anchors takes O(log(U/K)) string comparisons, then reconstructing at most K terms costs time proportional to their characters. This favors compact sorted vocabularies with common beginnings. A trie offers prefix traversal without rebuilding whole blocks, while a plain hash set often wins for simple in-memory exact membership.",
        mistakes=["Do not decode a suffix against the preceding term when this format uses the block anchor.", "Do not report a shared prefix as an exact term hit.", "Do not assume Python object storage is byte-compressed by this representation.", "Do not change block size or sorted terms without rebuilding encoded blocks."],
        related=["dsa/trie-prefix-index-and-terminal-flag", "dsa/compressed-trie-edge-splitting", "dsa/inverted-index-sorted-postings-intersection"],
    ),
]


def links(paths):
    return "<ul>" + "".join('<li><a href="/' + path + '">' + html.escape(by_path[path]["title"]) + "</a></li>" for path in paths) + "</ul>"


for order, lesson in enumerate(lessons):
    path = lesson["path"]
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
    entry = copy.deepcopy(by_path["dsa/hash-map-collision-and-load-contract"])
    entry.update(id=str(uuid.uuid5(uuid.NAMESPACE_URL, "aitrove:" + path)), path=path, title=lesson["title"], summary=lesson["summary"], body=body,
                 sort_order=42400 + order * 10, created_at=stamp, updated_at=stamp, published_at=stamp)
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
project_path = "dsa/incident-text-index-contract-audit-project"
quiz_path = "quizzes/dsa-postings-position-grams-lexicon-contracts"
assert project_path not in by_path and quiz_path not in by_path
project = copy.deepcopy(by_path["dsa/query-workload-rank-window-grid-audit-project"])
project.update(id=str(uuid.uuid5(uuid.NAMESPACE_URL, "aitrove:" + project_path)), path=project_path,
               title="Project: audit incident text index contracts", summary="Compare document, phrase, substring, and vocabulary queries against direct scans.",
               sort_order=42440, created_at=stamp, updated_at=stamp, published_at=stamp)
project["data"].update(reading_minutes=30, related=[{"path": path, "title": by_path[path]["title"]} for path in new_paths])
project["body"] = (
    "<p>An incident console needs four different text lookups. One request asks for documents containing every supplied exact term. Another asks for consecutive tokens in a fixed order. A third asks whether a character fragment occurs anywhere in stored source text. The final request asks whether one vocabulary term is present in a compact sorted dictionary. Build the reference results by scanning token lists, testing adjacent slices, applying source-text substring checks, and checking membership in a plain set. Then compare those results with sorted postings, positional postings, a trigram filter, and front-coded blocks. Do not treat these as interchangeable queries: document membership loses position, character fragments ignore token boundaries, and vocabulary membership does not identify any document.</p>"
    "<h2>Acceptance trace</h2><p>Use incident IDs 103, 218, 347, and 492. The document-term query valve AND pressure returns 103 and 347; repeated pressure in one record does not duplicate its ID. For the token sequences in the phrase lesson, pump pressure returns 103, 218, and 347, while pressure pressure returns only 347. For the raw text records, pressure returns 103, 218, and 492 after full-fragment verification. A three-term first block reconstructs pressure, pressurize, and pressurized; pressurizer remains absent. Try an empty query, an absent term, repeated phrase tokens, and a two-character fragment.</p>"
    '<h3>Expected output</h3><pre><code class="language-text">and=[103, 347] phrase=[103, 218, 347] substring=[103, 218, 492]\nlexicon-hit=true lexicon-miss=false</code></pre>'
    "<h2>Boundary and cost review</h2><p>State the tokenization and case rules once, then apply them before both indexing and querying. Use unique IDs for documents and distinguish a term's occurrence frequency from its document frequency. Measure the extra stored positions for phrase queries and the retained raw text needed to verify trigram candidates. Compare front-coded payload sizes with ordinary strings in the actual runtime rather than assuming a byte saving from a conceptual encoding. All four examples build snapshots: a changed document or vocabulary entry requires rebuilding here. A production incremental index would need update, deletion, and publication rules not supplied by these lessons.</p>"
    "<h3>Common Mistakes</h3><ul><li>Do not duplicate an ID in one term's posting list.</li><li>Do not answer an exact phrase with document-level AND alone.</li><li>Do not return trigram candidates without complete substring verification.</li><li>Do not interpret a decoded shared prefix as a term hit.</li></ul>"
    "<h2>Connected lessons</h2>" + links(new_paths + ["dsa/projects", "dsa/quizzes", subject_root])
)
entries.append(project)
by_path[project_path] = project

questions = [
    ("What does one document-level posting list store?", ["Sorted unique IDs of documents containing its term", "Every token position in every document", "Only the most recent document ID"], "A repeated term in one document still contributes one ID to its document-level posting list, which is ordered for merging."),
    ("How do two sorted posting lists answer an AND query?", ["Advance cursors and emit matching IDs", "Concatenate both lists without checking IDs", "Return the shorter list without comparison"], "Two forward-only cursors compare current IDs, emit equal ones, and advance past smaller IDs until one list ends."),
    ("What can plain document-level postings not establish?", ["That two terms occur consecutively in a given order", "That a document contains both terms", "That a query term is absent"], "A posting list contains document membership but no token offsets, so term order and adjacency cannot be recovered from it."),
    ("What extra data does a positional posting retain?", ["Token offsets for each term inside each document", "Only a document's total byte count", "Only its sorted vocabulary"], "Phrase matching needs the places where each term occurs, allowing successive offsets to be checked in the same document."),
    ("What must pressure pressure match?", ["Two adjacent occurrences at different token positions", "One pressure token reused twice", "Any document containing the word pressure"], "Repeated terms in a phrase require two distinct consecutive offsets, even though both offsets belong to one term's posting map."),
    ("Why is tokenization policy part of the positional-index contract?", ["Index and query must agree on exact token boundaries and equality", "Token positions remain valid after arbitrary edits", "Every character is already a separate token"], "Changing case or punctuation handling on just one side changes the token sequence and can create false misses or hits."),
    ("What does intersecting all query trigrams produce?", ["Candidate documents that still require full-fragment verification", "Only proven exact substring matches", "Token-order phrase matches"], "A document can contain all required trigrams in separate places, so candidates must be checked against the complete fragment."),
    ("What happens for a two-character query in a trigram-only index?", ["The implementation scans the stored source strings", "It intersects nonexistent three-character grams", "It treats the query as an empty string"], "A fragment shorter than three characters has no trigram filter, so the program falls back to direct substring checks."),
    ("Why retain original text alongside trigram postings?", ["To reject candidates lacking the contiguous requested fragment", "To sort document IDs by length", "To remove every repeated trigram automatically"], "The posting intersection is a necessary filter but not a proof that all grams appear together in the correct order."),
    ("What does each front-coded block retain in full?", ["Its first term, used as the anchor for later suffixes", "Only the longest term", "Every term without any prefix encoding"], "The encoded later terms each record a prefix length relative to the first complete term in their sorted block."),
    ("Why can pressurizer be absent while pressurized is present?", ["Sharing a prefix does not make the entire term equal", "The dictionary stores only suffixes and no anchors", "Every prefix is automatically a terminal term"], "Front coding saves repeated prefix characters, while membership still compares a reconstructed complete term with the exact request."),
    ("What is a limitation of the demonstrated front-coded lexicon?", ["New terms require rebuilding its sorted encoded blocks", "It cannot check exact membership", "It requires every term to have equal length"], "Inserting a term can shift sorted block boundaries and change anchor-relative encodings, so this snapshot has no local edit method."),
]
balanced = []
for number, (prompt, options, explanation) in enumerate(questions):
    correct = options[0]
    distractors = options[1:]
    position = number % 3
    distractors.insert(position, correct)
    balanced.append({"prompt": prompt, "options": distractors, "answer": position, "explanation": explanation})
quiz = copy.deepcopy(by_path["quizzes/dsa-rank-window-grid-contracts"])
quiz.update(id=str(uuid.uuid5(uuid.NAMESPACE_URL, "aitrove:" + quiz_path)), path=quiz_path,
            title="Postings, positions, trigrams, and lexicon contracts", summary="Check four text-index structures and their exact query meanings.",
            sort_order=42450, created_at=stamp, updated_at=stamp, published_at=stamp)
quiz["data"].update(duration_minutes=20, related=[{"path": path, "title": by_path[path]["title"]} for path in new_paths + [project_path]], questions=balanced)
quiz["body"] = "<p>Decide which stored evidence proves document membership, phrase adjacency, raw substring presence, or exact vocabulary membership. The query type determines the index.</p><h2>Lessons</h2>" + links(new_paths) + "<h2>Design exercise</h2>" + links([project_path, subject_root])
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
    ("dsa/hash-map-collision-and-load-contract", new_paths[0]),
    ("dsa/trie-prefix-index-and-terminal-flag", new_paths[3]),
    ("dsa/aho-corasick-failure-linked-alert-index", new_paths[1]),
    ("dsa/suffix-array-lcp-incident-search", new_paths[2]),
    ("dsa/lsm-sorted-runs-tombstone-compaction", new_paths[0]),
    ("dsa/compressed-trie-edge-splitting", new_paths[3]),
):
    old = by_path[old_path]
    old["body"] += '<p><a href="/' + new_path + '">' + html.escape(by_path[new_path]["title"]) + "</a> adds a related indexing contract.</p>"
    old["updated_at"] = stamp
for path in new_paths:
    entry = by_path[path]
    peers = [other for other in new_paths if other != path]
    entry["body"] += '<p>Compare its query with ' + ", ".join('<a href="/' + other + '">' + html.escape(by_path[other]["title"]) + "</a>" for other in peers) + ', then run the <a href="/' + project_path + '">incident text index audit</a> and <a href="/' + quiz_path + '">index contract quiz</a>.</p>'
    entry["updated_at"] = stamp

fixture.write_text(json.dumps(entries, ensure_ascii=False, indent=2) + "\n")
print(json.dumps({"lessons": new_paths, "project": project_path, "quiz": quiz_path, "questions": len(questions)}))
