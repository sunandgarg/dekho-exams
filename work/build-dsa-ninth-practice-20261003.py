"""Add search-and-stream project, quiz, and reciprocal lesson links."""

import copy
import datetime
import html
import json
import uuid
from pathlib import Path

root = Path(__file__).resolve().parents[1]
fixture = root / "src/data/fixtures.json"
entries = json.loads(fixture.read_text())
by_path = {entry["path"]: entry for entry in entries}
subject_root = "dsa/dsa-tutorial-learn-data-structures-and-algorithms"
project_path = "dsa/incident-search-and-streaming-project"
quiz_path = "quizzes/dsa-pattern-spatial-frequency-indexes"
assert project_path not in by_path and quiz_path not in by_path
stamp = datetime.datetime.now(datetime.UTC).isoformat()
related = [
    "dsa/aho-corasick-failure-linked-alert-index",
    "dsa/suffix-array-lcp-incident-search",
    "dsa/kd-tree-exact-nearest-depot",
    "dsa/count-min-sketch-frequency-boundary",
]


def links(paths):
    return "<ul>" + "".join(
        '<li><a href="/' + path + '">' + html.escape(by_path[path]["title"]) + "</a></li>"
        for path in paths
    ) + "</ul>"


project = copy.deepcopy(by_path["dsa/live-depot-index-recovery-project"])
project.update(
    id=str(uuid.uuid5(uuid.NAMESPACE_URL, "aitrove:" + project_path)), path=project_path,
    title="Project: search incident text and count event pressure",
    summary="Choose term matching, substring lookup, nearest depot, and compact event counts by contract.",
    sort_order=41450, created_at=stamp, updated_at=stamp, published_at=stamp,
)
project["data"].update(
    reading_minutes=23,
    related=[{"path": path, "title": by_path[path]["title"]} for path in related],
)
project["body"] = (
    "<p>An incident console receives a fixed dictionary of alert terms, an immutable incident transcript, a static list of depot coordinates, and a stream of event codes. The same word search does not fit all four jobs. A failure-linked trie reports every overlapping term during one message scan; a suffix array finds arbitrary nonempty substrings in the stored transcript; a k-d tree searches planar depot coordinates; and a count-min sketch gives compact, approximate positive counts. State which index is rebuilt when its input changes. Keep output ordering and error direction explicit.</p>"
    "<h2>Text and location contract</h2>"
    "<p>Index heat, eat, and seal, then scan overheat seal heat. Require both heat/eat overlaps. Build a suffix array over valve alert valve and find valve at offsets 12 and 0 in suffix order, followed by alert at 6. Check the adjacent common-prefix length for the suffix at offset 0. Index D-19 at (4, 9), D-47 at (18, 7), and D-61 at (12, 22); request the nearest to (16, 9) and expect D-47 with squared distance 8. Add an equal-distance pair and specify the depot-ID tie rule before relying on pruning.</p>"
    "<h2>Frequency and boundary contract</h2>"
    "<p>Use four counter rows and 47 columns. Record bay-hot seven times and gate-open three times. Check that each estimate is at least its exact count, and deliberately find an unrecorded event code with a positive estimate to expose collision behavior. Reject subtraction, deletion, and zero-weight writes. State that this implementation's deterministic hashes do not supply the formal probability bounds of a separately specified universal hash family. Keep a small exact map in the test code as an oracle, not as part of the fixed-memory sketch.</p>"
    "<h2>Acceptance trace</h2><pre><code class=\"language-text\">Alert matches: heat/eat overlap, seal, heat/eat overlap\nTranscript valve offsets in suffix order: 12, 0\nNearest to (16, 9): D-47, squared distance 8\nRecorded bay-hot estimate: at least 7</code></pre>"
    "<h2>Cost and failure review</h2>"
    "<p>For total term length M, longest term H, message length N, and Z hits, the sparse failure-linked trie has a conservative O(MH + R) build bound for R inherited output references and an O(N + Z) scan. Rank-doubling suffix construction costs O(T log² T) for text length T, while its binary lookup costs O(P log T) for pattern length P. Median-sorted k-d construction costs O(D log² D) for D depots, and nearest search can still visit all D points. A sketch with rows r and width w holds O(rw) counters and hashes every update across r rows. Test empty inputs, collisions, ties, and stale immutable indexes.</p>"
    "<h3>Common Mistakes</h3><ul>"
    "<li>Do not discard suffix alert terms inherited from a failure link.</li>"
    "<li>Do not display suffix-order offsets as if they were transcript order.</li>"
    "<li>Do not equate Euclidean coordinate distance with road travel time.</li>"
    "<li>Do not present an approximate sketch estimate as an exact count.</li>"
    "<li>Do not reuse an immutable index after changing its source data.</li>"
    "</ul><h2>Connected lessons</h2>" + links(related + ["dsa/live-depot-index-recovery-project", "dsa/projects", "dsa/quizzes", subject_root])
)
entries.append(project)
by_path[project_path] = project

questions = [
    ("Why does the failure-linked trie inherit output terms?", ["A suffix of one term can finish at the same input position", "Every term starts at the root on every character", "The term dictionary is sorted by length"], "Following a fallback can land at a terminal state, so its matches must be reported alongside the current state's own terms."),
    ("What does the alert scanner's offset count?", ["Python Unicode code points", "UTF-8 bytes in a file", "Rendered screen columns"], "The program iterates Python string elements and records their zero-based positions, which are not byte offsets in encoded storage."),
    ("What happens if indexed alert terms change?", ["Rebuild failures and inherited outputs", "Change the term tuple only", "Keep old failure links forever"], "Changing trie edges alters suffix relationships, so the existing failure links and output lists no longer describe the term set."),
    ("Why can valve appear at offsets 12 then 0 in a suffix-array result?", ["Suffixes are returned in lexicographic order", "The scan reverses the message", "Offset 0 is deleted from the index"], "The shorter valve suffix sorts before the longer suffix beginning with the same characters at the start of the transcript."),
    ("What build cost belongs to the shown rank-doubling suffix array?", ["O(N log² N) with comparison sorting each round", "Guaranteed O(N) in this implementation", "O(1) after reading the text"], "Each of logarithmically many rank widths sorts N constant-size rank pairs with a comparison sort."),
    ("Does the shown substring lookup use its LCP array to speed comparisons?", ["No; it slices the text for each binary-search comparison", "Yes; every comparison is constant time", "No; it linearly scans every suffix"], "The LCP data is computed, but the two search boundaries compare up to the full pattern length at each binary-search step."),
    ("When may exact nearest search skip a k-d tree's far side?", ["The split-plane distance squared is strictly greater than the best squared point distance", "The near child contains any point", "The two coordinate values are equal"], "A farther branch cannot improve distance only when the separating plane itself is already farther than the best point."),
    ("Why must the far side be checked on equal plane distance?", ["A depot there may tie on distance and win by ID", "It always contains a closer point", "The tree has lost its axis"], "The deterministic tie rule can select an ID on the other side even when both points are equally distant."),
    ("What is the worst-case nearest-query cost of this static k-d tree?", ["O(N) visited points", "Guaranteed O(log N)", "O(1) for two coordinates"], "An exact query can fail to prune many subtrees, so the balanced shape does not guarantee logarithmic work."),
    ("For positive-only updates, how does a count-min estimate compare with its true count?", ["It is at least the true count and may overestimate", "It is always exact", "It is always smaller"], "Each hashed row includes the key's own increments plus any collision increments, and taking the minimum preserves that direction."),
    ("Does a positive estimate prove an event code was recorded?", ["No; other keys may collide in every queried row", "Yes; the sketch stores every event code", "Yes; hashes eliminate all collisions"], "The matrix stores counters rather than key identities, so a never-seen code can map to counters raised by other events."),
    ("What assumption is needed before quoting a formal count-min error probability?", ["A specified hash family and parameter analysis", "Any arbitrary deterministic hash implementation", "A rule allowing negative updates"], "The sample's deterministic hashes give repeatability but do not by themselves establish a universal-hashing probability theorem."),
]
balanced_questions = []
for number, (prompt, options, explanation) in enumerate(questions):
    correct = options[0]
    distractors = options[1:]
    position = number % 3
    distractors.insert(position, correct)
    balanced_questions.append({"prompt": prompt, "options": distractors, "answer": position, "explanation": explanation})

quiz = copy.deepcopy(by_path["quizzes/dsa-online-persistence-journal-cas"])
quiz.update(
    id=str(uuid.uuid5(uuid.NAMESPACE_URL, "aitrove:" + quiz_path)), path=quiz_path,
    title="Pattern, spatial, and frequency index checks",
    summary="Test overlapping matches, suffix order, plane pruning, and sketch error direction.",
    sort_order=41460, created_at=stamp, updated_at=stamp, published_at=stamp,
)
quiz["data"].update(
    duration_minutes=18,
    related=[{"path": path, "title": by_path[path]["title"]} for path in related + [project_path]],
    questions=balanced_questions,
)
quiz["body"] = (
    "<p>Match each index to the contract it actually supplies. Pay attention to overlap, ordering, worst-case search, and one-sided count error.</p>"
    "<h2>Lessons</h2>" + links(related) + "<h2>Design exercise</h2>" + links([project_path, subject_root])
)
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
    ("dsa/trie-prefix-index-and-terminal-flag", "dsa/aho-corasick-failure-linked-alert-index"),
    ("dsa/compressed-trie-edge-splitting", "dsa/suffix-array-lcp-incident-search"),
    ("dsa/interval-tree-max-endpoint-pruning", "dsa/kd-tree-exact-nearest-depot"),
    ("dsa/bloom-filter-membership-boundary", "dsa/count-min-sketch-frequency-boundary"),
):
    old = by_path[old_path]
    old["body"] += '<p><a href="/' + new_path + '">' + html.escape(by_path[new_path]["title"]) + "</a> handles a related query contract.</p>"
    old["updated_at"] = stamp
for path in related:
    entry = by_path[path]
    entry["body"] += '<p>Apply this structure in the <a href="/' + project_path + '">incident search project</a>, then test the <a href="/' + quiz_path + '">index decisions quiz</a>.</p>'
    entry["updated_at"] = stamp

fixture.write_text(json.dumps(entries, ensure_ascii=False, indent=2) + "\n")
print(json.dumps({"added": [project_path, quiz_path], "questions": len(questions)}))
