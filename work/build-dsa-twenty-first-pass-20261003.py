"""Add bounded streaming summaries, distinct estimation, and fixed-size sampling."""

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
    dict(path="dsa/misra-gries-frequent-item-candidates", program="misra_gries_incident_candidates.py",
         template="dsa/count-min-sketch-frequency-boundary", section="dsa/hash-tables",
         title="Misra–Gries: find frequent-item candidates in one pass",
         summary="Keep a bounded set of counters that cannot miss an item above a chosen frequency threshold.",
         definition="A stream can contain millions of incident codes, but the question may be narrower: which codes could occur more than one third of the time? Misra–Gries retains two counters for that threshold. A matching code increments its counter; an unseen code takes a free counter; if both counters are occupied, one occurrence is canceled from each resident and the incoming code. The remaining keys are candidates, not proven winners. For K counters, every key with true frequency greater than N divided by K plus one must survive. A second pass over a replayable stream, or exact counts maintained elsewhere, is required to report the qualifying keys and their true counts. The stream here is insertion-only and incident codes are hashable strings.",
         case="In an eleven-record incident feed, pump-47 occurs six times while valve-19 and sensor-61 occur twice each and grid-83 once. With two slots the threshold is eleven divided by three, so pump-47 must appear among the candidates. The summary can also retain a code below that threshold. Its stored count has suffered cancellation and must not be printed as the exact number of pump incidents. This distinction matters if an on-call dashboard drives an alert from the summary: display candidates for investigation, or verify them against durable event records before sending a frequency claim.",
         cost="A matching or free-slot update takes expected O(1) dictionary work. When all K slots are occupied, decrementing and deleting counters takes O(K) worst-case time. Space is O(K), independent of stream length; that bound excludes retention of the input for a later verification pass. Total work over N records is O(NK) with this direct Python loop as a conservative bound. The algorithm does not identify the exact top K by rank, handle negative corrections, or promise that every returned key passes the threshold. If exact counts are needed without a replay source, store them separately at the cost of unbounded distinct-key space.",
         mistakes=["Do not interpret residual counter values as exact frequencies.", "Do not discard a key above N/(K+1) from the final candidate set.", "Do not call every surviving key a verified heavy hitter.", "Do not apply insertion-only cancellation to negative updates without another model."],
         related=["dsa/count-min-sketch-frequency-boundary", "dsa/hash-map-collision-and-load-contract", "dsa/lfu-cache-frequency-and-recency-eviction"]),
    dict(path="dsa/space-saving-topk-stream-summary", program="space_saving_incident_topk.py",
         template="dsa/count-min-sketch-frequency-boundary", section="dsa/hash-tables",
         title="Space-Saving: ranked candidates with count bounds",
         summary="Replace the smallest tracked counter to keep ranked candidates and explicit estimation error.",
         definition="Space-Saving maintains a fixed number of tracked incident codes. A hit increments its estimate. An unseen code uses a free slot, or replaces a code with the minimum estimate when the summary is full. The replacement receives estimate minimum plus one and error minimum. For a tracked code, its true frequency lies between estimate minus error and estimate, inclusive. A tracked code with zero error has an exact count. The bound is more informative than printing an unlabeled approximate count, but it does not turn the candidate list into an exact ranking. This program resolves equal-minimum ties by incident-code order to make runs repeatable. It accepts insertion-only events and assumes codes are strings.",
         case="A monitoring feed repeatedly emits pump-47, with occasional valve-19, sensor-61, and grid-83 records. A two-slot summary reports candidates ordered by estimated count. Its pump entry may have an error range after earlier replacements; the tuple states that uncertainty rather than hiding it. If a responder needs the actual two most frequent codes, replay the feed and count all candidate codes or use an exact index. When two codes share a minimum estimate, removing the alphabetical one is merely this implementation's stable tie rule; another tie rule can change which borderline code survives without violating the count bounds.",
         cost="This direct implementation stores O(K) entries. Existing-key updates use expected O(1) dictionary work; insertion into a full summary scans K entries to locate a minimum, so its worst-case time is O(K). Producing the sorted display costs O(K log K). Heap-indexed implementations can reduce minimum selection work but need careful updates to avoid stale heap records. Counts and error bounds refer to the insertion-only prefix seen so far. Deletion, sliding windows, distributed merges, and adversarial key ordering need separate algorithms or contracts. A small fixed K is useful when storing exact counts for every distinct incident code would be too costly.",
         mistakes=["Do not label estimated counts as exact counts when error is positive.", "Do not omit the replaced minimum from the new key's error field.", "Do not claim O(1) replacement for this linear minimum search.", "Do not promise exact top-K membership for a bounded candidate summary."],
         related=["dsa/misra-gries-frequent-item-candidates", "dsa/count-min-sketch-frequency-boundary", "dsa/hash-map-collision-and-load-contract"]),
    dict(path="dsa/hyperloglog-register-distinct-estimate", program="hyperloglog_incident_distinct.py",
         template="dsa/count-min-sketch-frequency-boundary", section="dsa/hash-tables",
         title="HyperLogLog: estimate unique IDs with fixed registers",
         summary="Hash event IDs into registers and estimate distinct cardinality from leading-zero ranks.",
         definition="HyperLogLog answers a cardinality question: about how many distinct incident IDs have appeared? It is not a membership test and cannot list those IDs. The program hashes a UTF-8 ID to a fixed 64-bit fingerprint, chooses a register from the high precision bits, and stores the largest leading-zero rank seen in the remaining bits. An estimate combines all registers with a harmonic mean. When the raw estimate is small and empty registers remain, it uses an empty-register correction. Two summaries with the same precision and identical hash convention can merge by taking each register's maximum. A repeated ID makes no register change. The result is approximate even if the program is otherwise deterministic.",
         case="One region sees incident IDs numbered 47 through 146; another sees 97 through 196. There are 150 distinct IDs in the union, though each region observed 100. Merging the register arrays estimates that union without shipping an exact set of all IDs. The printed number can differ from 150. That is expected. If billing or access control requires an exact count, use a set or a verified database query instead. Mixing a different text encoding, hash method, or precision in one merge would make its estimate meaningless, so the interface rejects unequal precision and the documented program fixes the hash and encoding.",
         cost="With P precision bits, the sketch uses 2^P registers. Under a fixed-width hash model, register update is O(1), estimate and merge are O(2^P), and memory is O(2^P). Hashing a string also costs O(length of the encoded ID). Higher P uses more space and generally reduces sampling error; it cannot guarantee a particular error on one observed stream. This compact lesson omits large-range bias correction and does not claim a specified confidence interval. A 64-bit fingerprint also has a finite collision domain. Deletions cannot be reversed from max registers, and a merged result cannot be split back into its component streams.",
         mistakes=["Do not treat an approximate cardinality as an exact unique-ID count.", "Do not merge sketches with different precision or hash conventions.", "Do not use register maxima to infer membership or list IDs.", "Do not assume a duplicate can increase a register after the first identical hash."],
         related=["dsa/bloom-filter-membership-boundary", "dsa/count-min-sketch-frequency-boundary", "dsa/hash-map-collision-and-load-contract"]),
    dict(path="dsa/reservoir-sampling-fixed-memory", program="reservoir_incident_sampler.py",
         template="dsa/resizable-array-growth-and-insert-cost", section="dsa/array-data-structure-guide",
         title="Reservoir sampling: keep a uniform fixed-size sample",
         summary="Retain K records from an unknown-length stream without favoring early arrivals.",
         definition="Reservoir sampling keeps at most K incident IDs without knowing how long the feed will run. The first K arrivals fill the reservoir. On arrival number N greater than K, draw an integer uniformly from zero through N minus one; replace a stored slot only when the draw is below K. Each of the N observed positions then has inclusion probability K divided by N, assuming independent uniform random draws. The program uses a private seeded Python random generator so its example output is reproducible. This is a sample of event positions: if an incident ID appears repeatedly, it has multiple chances to appear. The sampler does not deduplicate IDs, weight recent events, or provide a cryptographic draw.",
         case="An incident pipeline receives twenty event records numbered 47 through 66 and keeps four for manual review. Saving the first four would exclude every later event. A reservoir can replace earlier selections as later records arrive while using four stored IDs. The printed sample is one seeded outcome, not a guarantee that those IDs are special. If events are removed later, the original uniformity proof no longer applies. If the review policy requires one sample per unique customer rather than one sample per event, deduplicate upstream or choose a different sampling contract before using the output.",
         cost="For capacity K and N processed events, memory is O(K), and each arrival performs O(1) reservoir operations plus the cost of generating a random integer. Returning a sample copy takes O(K). Zero capacity stores nothing while still counting arrivals. Python's random generator is suitable for this reproducible teaching example but must not be used for security-sensitive draws. A single sample has no promise to represent every rare class; statistical guarantees concern repeated random runs. This implementation does not merge independently sampled streams, retract old events, or sample by weight. Those variants need extra counts or priorities and distinct proofs.",
         mistakes=["Do not keep only the first K arrivals and call them a stream-wide uniform sample.", "Do not confuse uniform event positions with uniform unique IDs.", "Do not claim one seeded output proves a distributional guarantee.", "Do not use a non-cryptographic generator for security decisions."],
         related=["dsa/resizable-array-growth-and-insert-cost", "dsa/monotonic-deque-window-minimum", "dsa/count-min-sketch-frequency-boundary"]),
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
                 sort_order=42600 + order * 10, created_at=stamp, updated_at=stamp, published_at=stamp)
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
project_path = "dsa/stream-summary-distinct-sampling-audit-project"
quiz_path = "quizzes/dsa-heavy-hitter-distinct-sample-contracts"
assert project_path not in by_path and quiz_path not in by_path
project = copy.deepcopy(by_path["dsa/incident-retention-and-dispatch-audit-project"])
project.update(id=str(uuid.uuid5(uuid.NAMESPACE_URL, "aitrove:" + project_path)), path=project_path,
               title="Project: audit four bounded stream views", summary="Compare candidate, count-bound, distinct-count, and uniform-sample contracts.",
               sort_order=42640, created_at=stamp, updated_at=stamp, published_at=stamp)
project["data"].update(reading_minutes=30, related=[{"path": path, "title": by_path[path]["title"]} for path in new_paths])
project["body"] = (
    "<p>A monitoring service receives a stream too large to retain in its request process. It needs four different views: likely high-frequency incident codes, count ranges for ranked candidates, an approximate number of unique incident IDs across regions, and a small event sample for human review. Build four independent reference checks before combining the views. Keep exact counts and an exact ID set only inside the test reference. A bounded production summary cannot recover every original event. Define whether each input is an event position, an incident code, or a unique ID; mixing those units produces convincing but false conclusions. Save the four bounded states independently and never report an estimate as a verified count.</p>"
    "<h2>Acceptance trace</h2><p>Feed eleven incident codes with pump-47 appearing six times, valve-19 and sensor-61 twice each, and grid-83 once. With two slots, pump-47 must survive Misra–Gries because six exceeds eleven divided by three. For every tracked Space-Saving key, assert exact frequency is between estimate minus error and estimate. Feed one hundred region IDs beginning at 47 and another one hundred beginning at 97; after merging same-precision HyperLogLog registers, compare the estimate with the exact union size 150 but do not require equality. Sample four positions from twenty arriving events using a fixed seed, then repeat across many independent seeds to assess inclusion rates.</p>"
    '<h3>Expected review record</h3><pre><code class="language-text">verified-heavy-hitter=pump-47 exact-count=6\nregion-union-exact=150 estimate=approximate\nsample-size=4 stream-length=20</code></pre>'
    "<h2>Boundary and cost review</h2><p>Test zero and invalid capacities, a stream shorter than the reservoir, duplicate IDs, candidate false positives, estimate bounds after every Space-Saving replacement, and a HyperLogLog merge with mismatched precision. State that the two frequency summaries are insertion-only, the distinct sketch is hash-dependent and approximate, and the sample is uniform over positions under random draws. Compare their memory with exact dictionaries or sets. If replay is impossible, Misra–Gries candidates cannot be verified by a second pass; the system must either store exact counts elsewhere or clearly show an unresolved candidate list.</p>"
    "<h3>Common Mistakes</h3><ul><li>Do not report candidate keys as verified threshold winners.</li><li>Do not discard Space-Saving error bounds.</li><li>Do not interpret an HLL estimate as an exact union count.</li><li>Do not confuse event sampling with unique-entity sampling.</li></ul>"
    "<h2>Connected lessons</h2>" + links(new_paths + ["dsa/projects", "dsa/quizzes", subject_root])
)
entries.append(project)
by_path[project_path] = project

questions = [
    ("What does a two-counter Misra–Gries summary guarantee for N records?", ["Every key above N/3 remains a candidate", "Every remaining count is exact", "Exactly two true winners are returned"], "Cancellation cannot remove a key whose true frequency exceeds N divided by three, though extra candidates may survive."),
    ("How can a candidate be confirmed as a threshold winner?", ["Count candidates on a replayable stream", "Read its residual counter as exact", "Sort candidate labels alphabetically"], "A second pass can count retained candidate keys exactly; residual counters have lost increments during cancellation."),
    ("What is the direct update cost when every Misra–Gries slot is full?", ["O(K) to decrement K counters", "O(1) worst case for any K", "O(N) additional memory"], "The simple implementation visits every resident counter in a full summary and removes those reaching zero."),
    ("What range contains a tracked Space-Saving key's true count?", ["Estimate minus error through estimate", "Estimate through estimate plus error", "Always exactly the estimate"], "On replacement the old minimum becomes error, so the stored estimate is an upper bound and its adjusted value a lower bound."),
    ("What happens when an unseen key arrives in a full Space-Saving summary?", ["Replace a minimum entry with estimate minimum plus one", "Discard the key without any state change", "Clear all counters and restart"], "Replacing a minimum counter preserves a bounded candidate summary and records the inherited uncertainty as error."),
    ("What costs O(K) in this Space-Saving implementation?", ["Finding the minimum tracked entry on replacement", "Updating an existing dictionary key", "Reading the fixed capacity field"], "A direct scan selects the smallest estimate with a stable code tie rule rather than maintaining a separate indexed heap."),
    ("What does a HyperLogLog register retain?", ["The largest leading-zero rank for its hash bucket", "Every original incident ID", "An exact count of all IDs in that bucket"], "Each bucket stores a maximum rank from hash suffixes, discarding the original IDs and exact bucket membership."),
    ("When can two sketches merge by register-wise maximum?", ["Their precision and hash conventions agree", "They use different precision for better coverage", "One sketch contains only duplicate IDs"], "Corresponding registers must represent the same buckets and ranks, which requires matching precision, encoding, and hash method."),
    ("What is the result of adding the same ID again to this sketch?", ["No register changes", "Every register increments", "The estimate becomes an exact count"], "The deterministic hash selects the same bucket and rank, and taking the maximum with an identical rank leaves it unchanged."),
    ("What is one position's inclusion probability after N arrivals with reservoir size K?", ["K/N when N exceeds K", "K regardless of N", "One only for the first K arrivals"], "The replacement rule preserves equal inclusion probability for each observed position under uniform independent draws."),
    ("What does the sample treat as its population?", ["Event positions, including repeated IDs", "Unique IDs after automatic deduplication", "Only the first K events"], "Each arrival participates separately, so a repeated identifier occupies several possible event positions in the stream."),
    ("What does a zero-capacity reservoir do?", ["Count arrivals while retaining no event values", "Reject every arriving event", "Store one event because counting starts at zero"], "Zero capacity is valid in this implementation: the seen counter advances, while the stored value list stays empty."),
]
balanced = []
for number, (prompt, options, explanation) in enumerate(questions):
    correct = options[0]
    distractors = options[1:]
    position = number % 3
    distractors.insert(position, correct)
    balanced.append({"prompt": prompt, "options": distractors, "answer": position, "explanation": explanation})
quiz = copy.deepcopy(by_path["quizzes/dsa-eviction-expiry-handle-heap-contracts"])
quiz.update(id=str(uuid.uuid5(uuid.NAMESPACE_URL, "aitrove:" + quiz_path)), path=quiz_path,
            title="Frequent items, distinct counts, and stream samples", summary="Check bounded candidates, count errors, register merges, and sampling probability.",
            sort_order=42650, created_at=stamp, updated_at=stamp, published_at=stamp)
quiz["data"].update(duration_minutes=20, related=[{"path": path, "title": by_path[path]["title"]} for path in new_paths + [project_path]], questions=balanced)
quiz["body"] = "<p>Choose the statement supported by each bounded stream state. Candidate keys, count ranges, approximate cardinality, and sampled event positions answer different questions.</p><h2>Lessons</h2>" + links(new_paths) + "<h2>Design exercise</h2>" + links([project_path, subject_root])
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
    ("dsa/count-min-sketch-frequency-boundary", new_paths[0]),
    ("dsa/count-min-sketch-frequency-boundary", new_paths[1]),
    ("dsa/bloom-filter-membership-boundary", new_paths[2]),
    ("dsa/hash-map-collision-and-load-contract", new_paths[2]),
    ("dsa/resizable-array-growth-and-insert-cost", new_paths[3]),
    ("dsa/lfu-cache-frequency-and-recency-eviction", new_paths[0]),
):
    old = by_path[old_path]
    old["body"] += '<p><a href="/' + new_path + '">' + html.escape(by_path[new_path]["title"]) + "</a> adds a bounded stream contract.</p>"
    old["updated_at"] = stamp
for path in new_paths:
    entry = by_path[path]
    peers = [other for other in new_paths if other != path]
    entry["body"] += '<p>Compare its result with ' + ", ".join('<a href="/' + other + '">' + html.escape(by_path[other]["title"]) + "</a>" for other in peers) + ', then complete the <a href="/' + project_path + '">bounded-stream audit</a> and <a href="/' + quiz_path + '">contract quiz</a>.</p>'
    entry["updated_at"] = stamp

fixture.write_text(json.dumps(entries, ensure_ascii=False, indent=2) + "\n")
print(json.dumps({"lessons": new_paths, "project": project_path, "quiz": quiz_path, "questions": len(questions)}))
