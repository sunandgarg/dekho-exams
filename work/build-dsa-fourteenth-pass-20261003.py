"""Add forest, substring, and text-editing operation contracts to DSA."""

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
        path="dsa/link-cut-forest-path-sums",
        program="link_cut_forest_path_sum.py",
        title="Link-cut forests: change tree edges and sum a path",
        summary="Maintain node-weight paths while linking and cutting edges in an acyclic forest.",
        section="dsa/graphs-and-disjoint-sets",
        definition="A link-cut tree represents a forest through preferred paths held in auxiliary splay trees. Access changes which root-to-node path is preferred; make-root reverses a represented path so either endpoint can become its root. Each auxiliary node stores its own weight and a subtree total. After making the first endpoint root and accessing the second, the second auxiliary root summarizes the complete path, including both endpoints. This implementation also tracks the exact edges so a cut cannot silently remove a different connection. Links between already connected depots are rejected: cycles violate the forest contract. A disconnected path has no sum under this API.",
        case="Depots D-19, D-26, and D-47 have weights 7, 11, and 13. Linking D-19 to D-26 and D-26 to D-47 makes their path total 31. Cut the second edge; connectivity from D-19 to D-47 becomes false. Add D-61 with weight 17, connect D-47 to D-61 and D-26 to D-61, and the new four-depot path totals 48. These are node weights. An edge-weight model needs a separate representation, often an extra node per edge. Trying to link D-19 and D-47 now must fail because they are already connected.",
        cost="For N depots, node and direct-edge storage are O(N) in a forest. Standard splay-based link-cut operations have amortized O(log N) time; one particular operation can take longer, so this is not a worst-case latency guarantee. A path sum makes a constant number of those operations and has the same amortized bound. The splay implementation builds a temporary ancestor list during an access, which may use O(N) transient space in the worst case. A static tree with many path queries can use a precomputed path index instead. This example is single-threaded and does not maintain connectivity for arbitrary cyclic graphs.",
        mistakes=["Do not link nodes that already share a represented tree.", "Do not cut an arbitrary path when the API requires an existing direct edge.", "Do not report amortized logarithmic work as a per-request worst-case bound.", "Do not treat node-weight sums as edge-weight sums without changing the model."],
        related=["dsa/online-connectivity-after-edge-removal", "dsa/heavy-light-tree-path-sums", "dsa/disjoint-set-rollback-checkpoints"],
    ),
    dict(
        path="dsa/suffix-automaton-online-substrings",
        program="suffix_automaton_incident_text.py",
        title="Suffix automata: index substrings as text arrives",
        summary="Append characters, test substring membership, and count distinct substrings.",
        section="dsa/trees-and-heaps",
        definition="A suffix automaton compresses the substrings of an append-only text into states distinguished by their possible continuations. Each state records its longest accepted string, a suffix link, and transitions by character. An append extends the current last state; when an existing transition would skip a length boundary, a clone copies that transition map and redirects the affected suffix chain. Following transitions from the initial state answers whether a pattern occurs anywhere. The empty pattern is present. Distinct substrings are counted by summing each noninitial state's longest length minus its suffix-link state's longest length. This is a character index, not a store of match positions or occurrence counts.",
        case="Append the characters of dispatch-dispatch as incident text. The index finds patch and patch-dis, rejects warehouse, and counts 117 distinct nonempty substrings. Each append keeps earlier substring membership valid. A pattern may cross the hyphen because the hyphen is an ordinary character here; if entries should be isolated, use a separator that cannot appear in an entry and define whether cross-entry patterns are allowed. A new incident character extends the index without rebuilding the previous states. Deleting or replacing text is outside this implementation's contract.",
        cost="For N appended characters, a suffix automaton has O(N) states and transitions when alphabet size is bounded; each nonempty text has at most 2N minus 1 states. The classic construction is O(N) total time with constant-time transition access, giving amortized O(1) per append. Python dictionaries offer expected constant-time access for ordinary keys, not an adversarial worst-case promise. A contains query follows M characters in expected O(M) time. The shown distinct-substring method scans all states on every call, so it costs O(N) time and O(1) extra working space; cache and update the total if repeated constant-time counts matter. Clone dictionary copies also depend on outgoing degree. Stored states use O(N) space for a fixed alphabet.",
        mistakes=["Do not read a failed transition as a partial substring match.", "Do not omit the clone when an existing transition crosses the required length boundary.", "Do not claim this membership API reports positions or frequency.", "Do not apply append-only state to text deletions without rebuilding or choosing another index."],
        related=["dsa/suffix-array-lcp-incident-search", "dsa/aho-corasick-failure-linked-alert-index", "dsa/compressed-trie-edge-splitting"],
    ),
    dict(
        path="dsa/piece-table-text-editing",
        program="piece_table_editor.py",
        title="Piece tables: edit text through source spans",
        summary="Keep original text and appended text as sources while editing a piece sequence.",
        section="dsa/array-data-structure-guide",
        definition="A piece table stores text in two logical sources: the original document and an append-only addition buffer. The visible document is an ordered sequence of pieces, each naming a source, start offset, and length. Insertion finds a visible position, splits a piece if needed, appends the new fragment to the addition source, and inserts one descriptor. Deletion splits both boundaries and removes descriptors between them. Neither operation rewrites the original source. This Python model uses a list of pieces and a string for the addition source; those concrete choices matter for cost. An empty insertion changes nothing, and deleting an empty interval preserves the text.",
        case="Start with Depot D-19 cleared. Insert north followed by a space after Depot, then delete the D-19 segment. Rendering the resulting pieces prints Depot north cleared, length 19, across three pieces. The original source still contains its old words; visibility comes only from descriptors. A delete can leave text in either source that no live piece references. Keeping history can help an undo design, but this example does not implement undo, snapshots, compaction, or file persistence. Its positions count Python string code points, not grapheme clusters seen by a user interface.",
        cost="Let P be the number of pieces, A the current addition-buffer length, F the inserted fragment length, and N the visible length. Finding each split point scans O(P) pieces; Python list insertion and deletion may shift O(P) descriptors. Python string concatenation copies the addition buffer and fragment, costing O(A + F) time and fresh temporary string space for an insertion here. Rendering slices and joins the visible pieces in O(N + P) time and O(N) output space. Retained source text and descriptors consume O(original length + A + P) space. A production editor can use chunked append storage and a balanced piece tree for better edit scaling, but this runnable model deliberately does not claim those bounds.",
        mistakes=["Do not mutate the original source when inserting or deleting visible text.", "Do not treat a descriptor index as a character offset.", "Do not promise logarithmic edits from a Python list of pieces.", "Do not confuse code-point positions with user-perceived grapheme boundaries."],
        related=["dsa/implicit-treap-range-reversal", "dsa/resizable-array-growth-and-insert-cost", "dsa/persistent-ordered-index-path-copying"],
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
                 sort_order=41900 + order * 10, created_at=stamp, updated_at=stamp, published_at=stamp)
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
project_path = "dsa/forest-substring-note-audit-project"
quiz_path = "quizzes/dsa-forest-substring-piece-contracts"
assert project_path not in by_path and quiz_path not in by_path
project = copy.deepcopy(by_path["dsa/incident-search-and-streaming-project"])
project.update(id=str(uuid.uuid5(uuid.NAMESPACE_URL, "aitrove:" + project_path)), path=project_path,
               title="Project: audit a depot forest and incident notes",
               summary="Check live forest paths, arriving substring queries, and text edits against plain models.",
               sort_order=41940, created_at=stamp, updated_at=stamp, published_at=stamp)
project["data"].update(reading_minutes=25, related=[{"path": path, "title": by_path[path]["title"]} for path in new_paths])
project["body"] = (
    "<p>A depot console keeps an acyclic maintenance network, indexes an arriving incident log, and edits a dispatcher note. Give each operation a reference model before optimizing it. A plain adjacency map answers connected and path-sum requests by breadth-first search. A Python string answers substring membership and gives a brute-force set of distinct substrings for small cases. A second Python string tracks the note after insertion and deletion. The production-oriented structures must agree with these models after every mutation, not only at the end of a prepared trace.</p>"
    "<h2>Acceptance trace</h2><p>Give D-19, D-26, D-47, and D-61 weights 7, 11, 13, and 17. Link D-19 to D-26 and D-26 to D-47: the path sums to 31. Cut the latter edge; the endpoints are disconnected. Link D-47 to D-61, then D-26 to D-61; the path from D-19 to D-47 sums to 48. Append dispatch-dispatch one character at a time. Membership accepts patch and patch-dis, rejects warehouse, and the final distinct-substring count is 117. Insert north and a space into Depot D-19 cleared at position 6, then delete positions [12, 17). The visible note becomes Depot north cleared.</p>"
    '<h3>Expected output</h3><pre><code class="language-text">path-before=31 disconnected=true path-after=48\npatch=true warehouse=false distinct=117\nnote=Depot north cleared length=19</code></pre>'
    "<h2>Boundary and cost review</h2><p>Reject a forest link that creates a cycle and a cut that does not name a direct edge. Try a one-node path and a disconnected path. Check empty and one-character substrings after every append; no operation here deletes indexed log text. For the editor, test insertion at both ends, deletion across several pieces, and empty edits. Link-cut work is amortized logarithmic, not a deadline bound for an individual call. The suffix automaton consumes growing memory and does not return match positions. The shown piece list and Python string addition buffer may both require linear copying during an edit. Keep these limits visible in any interface built over the examples.</p>"
    "<h3>Common Mistakes</h3><ul><li>Do not turn the represented forest into a graph with cycles.</li><li>Do not count a substring once per occurrence when asked for distinct strings.</li><li>Do not rewrite source text instead of editing the live piece sequence.</li><li>Do not claim a worst-case bound from an amortized argument.</li></ul>"
    "<h2>Connected lessons</h2>" + links(new_paths + ["dsa/projects", "dsa/quizzes", subject_root])
)
entries.append(project)
by_path[project_path] = project

questions = [
    ("Which link request must a forest reject?", ["An edge between nodes already connected", "An edge between separate trees", "An edge incident to a leaf"], "Adding an edge inside one existing tree creates a cycle, breaking the forest invariant required by this link-cut implementation."),
    ("What does the shown path sum include?", ["Both endpoint node weights", "Only edge weights", "Only the internal node weights"], "The auxiliary aggregate stores a weight at each depot node, so the exposed path includes the first and last depot."),
    ("Which cut is accepted?", ["A currently present direct edge", "Any two nodes in the same tree", "Any two nodes with equal weights"], "The API records exact forest edges and rejects a pair that is merely connected through an intervening path."),
    ("What time claim applies to standard splay-based link-cut operations?", ["Amortized O(log N)", "Worst-case O(1) for every call", "Worst-case O(N log N) for every call"], "The logarithmic bound is amortized over a sequence; a single splay operation may take more than logarithmic work."),
    ("How does a suffix automaton check a pattern?", ["Follow its character transitions from the initial state", "Compare every pair of text positions", "Search only the most recent suffix"], "A complete transition walk exists exactly when the pattern is a substring of the indexed text under this contract."),
    ("Why does append sometimes create a clone state?", ["An existing transition crosses a required length boundary", "Every repeated character needs a copy", "The text buffer exceeded a fixed capacity"], "A clone separates different substring-length classes while preserving earlier transitions and suffix-link relationships."),
    ("What does this automaton's contains method return?", ["Substring membership only", "Every match position", "An occurrence count"], "The method reports whether a transition path exists; it does not retain end-position lists or count occurrences."),
    ("How much work does this distinct-substring method do per call?", ["O(number of states)", "Guaranteed O(1)", "O(pattern length)"], "The displayed method sums a contribution for each noninitial state on every request instead of maintaining a cached total."),
    ("What changes when the piece table inserts text?", ["The addition source and piece descriptors", "The immutable original source", "Every character of the original document"], "Insertion appends a fragment to the addition source and adjusts visible descriptors; original source characters remain intact."),
    ("What does a piece descriptor identify?", ["A source, start offset, and length", "A character and its color", "Only a visible document offset"], "Each piece points to a span in one backing source; its position in the piece sequence determines visible order."),
    ("Why is insertion in this Python piece-table model potentially linear?", ["String concatenation copies the addition buffer and list insertion shifts descriptors", "The model uses a balanced piece tree", "A suffix link must be rebuilt"], "The logical piece-table idea does not erase the costs of Python's immutable string concatenation or array-backed list shifts."),
    ("Which position convention does the shown editor use?", ["Python string code points", "User-perceived grapheme clusters", "UTF-8 byte offsets"], "Python string indexing counts code points, so a visual character made from multiple code points needs a separate UI mapping."),
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
            title="Forest paths, online substrings, and text pieces",
            summary="Check link-cut edges, automaton states, and piece-table mutation costs.",
            sort_order=41950, created_at=stamp, updated_at=stamp, published_at=stamp)
quiz["data"].update(duration_minutes=20, related=[{"path": path, "title": by_path[path]["title"]} for path in new_paths + [project_path]], questions=balanced)
quiz["body"] = "<p>Check each operation's exact scope. Forest links cannot form cycles, suffix membership does not give match positions, and this piece table uses Python lists and strings with their real copying costs.</p><h2>Lessons</h2>" + links(new_paths) + "<h2>Design exercise</h2>" + links([project_path, subject_root])
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
    ("dsa/online-connectivity-after-edge-removal", new_paths[0]),
    ("dsa/heavy-light-tree-path-sums", new_paths[0]),
    ("dsa/suffix-array-lcp-incident-search", new_paths[1]),
    ("dsa/aho-corasick-failure-linked-alert-index", new_paths[1]),
    ("dsa/implicit-treap-range-reversal", new_paths[2]),
    ("dsa/resizable-array-growth-and-insert-cost", new_paths[2]),
):
    old = by_path[old_path]
    old["body"] += '<p><a href="/' + new_path + '">' + html.escape(by_path[new_path]["title"]) + "</a> adds a related operation contract.</p>"
    old["updated_at"] = stamp
for path in new_paths:
    entry = by_path[path]
    entry["body"] += '<p>Apply the invariant in the <a href="/' + project_path + '">depot forest and notes project</a>, then check the <a href="/' + quiz_path + '">operations quiz</a>.</p>'
    entry["updated_at"] = stamp

fixture.write_text(json.dumps(entries, ensure_ascii=False, indent=2) + "\n")
print(json.dumps({"lessons": new_paths, "project": project_path, "quiz": quiz_path, "questions": len(questions)}))
