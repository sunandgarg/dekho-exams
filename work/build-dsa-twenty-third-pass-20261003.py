"""Add mergeable, monotone, and double-ended priority queue content."""

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
    dict(path="dsa/pairing-heap-two-pass-meld", program="pairing_incident_heap.py",
         template="dsa/dary-heap-stable-priority-dispatch", section="dsa/trees-and-heaps",
         title="Pairing heaps: meld roots and pair children on removal",
         summary="Join root trees in constant time and rebuild after delete-min with a two-pass pairing.",
         definition="A pairing heap is a heap-ordered rooted tree whose children are themselves pairing heaps. Meld compares two roots and attaches the larger root beneath the smaller one. Insertion melds a singleton with the current root; merging two queues melds their roots and transfers ownership from the donor. Removing the minimum is the harder operation. The program first melds adjacent children from left to right, then folds those paired trees from right to left. A unique arrival number follows each priority, so equal-priority incidents leave in arrival order even after two queues merge. It exposes push, meld, and pop only; there are no stable node handles or decrease-key operation in this version.",
         case="Two dispatch teams maintain separate pending queues. East holds pump-47 at priority 47 and valve-19 at 19; West holds sensor-61 at 19 and grid-83 at 61. Melding West into East empties the donor and yields valve, sensor, pump, grid on repeated removal. The equal-priority order comes from arrival numbers assigned before the merge. If each queue restarted its own sequence counter, the two priority-19 entries could compare equal and fall through to a task object or an arbitrary tie. A global sequence in this single-process example avoids that ambiguity.",
         cost="Meld and push perform one root comparison and child append, O(1) under the list-operation model. A single pop can visit every child of the removed root and take O(N) worst-case time; the usual two-pass pairing-heap analysis concerns amortized behavior across operation sequences, not a fixed per-pop deadline. Space is O(N) nodes plus child references. This Python list representation and global sequence are teaching choices, not claims about optimal object overhead or thread safety. A binary heap may be simpler when queues never merge. Self-melding is rejected, and references held to donor nodes should be treated as transferred to the recipient.",
         mistakes=["Do not forget the second, right-to-left pairing pass after removing the root.", "Do not use independent tie counters if merged queues require global arrival order.", "Do not claim worst-case constant-time removal.", "Do not keep mutating a donor heap as though meld had copied its nodes."],
         related=["dsa/binary-heap-priority-scheduling", "dsa/dary-heap-stable-priority-dispatch", "dsa/indexed-binary-heap-decrease-key"]),
    dict(path="dsa/binomial-heap-degree-carry-meld", program="binomial_incident_heap.py",
         template="dsa/dary-heap-stable-priority-dispatch", section="dsa/trees-and-heaps",
         title="Binomial heaps: carry equal-degree trees during merge",
         summary="Keep at most one tree per degree while moving work between priority queues.",
         definition="A binomial heap is a forest with at most one heap-ordered tree of each degree. Linking two degree-D trees makes the larger root a child of the smaller root, producing one degree-D-plus-one tree. The forest therefore behaves like a binary count: equal degrees carry into the next degree. This implementation stores roots by degree, merges a singleton or another forest by repeated carries, and extracts the smallest root before returning its children to the forest. It compares priority followed by one process-wide arrival number to preserve stable ties across merged queues. A meld transfers the donor's roots and leaves the donor empty. There is no decrease-key or arbitrary-node deletion API.",
         case="East and West each hold two incident tasks. Their merge may have two degree-one roots, which must link into one degree-two tree; leaving both roots at degree one breaks the representation invariant. The merged queue returns valve-19 and sensor-61 before pump-47 and grid-83. Emptying the donor is part of the ownership contract, not an optimization detail. A checker can recursively count nodes in each tree and compare its size with two raised to its degree, then verify that every parent priority is no greater than its children.",
         cost="For N entries, a forest has at most O(log N) roots. Push, meld, and pop perform O(log N) tree links or root scans in the worst-case structural model; finding the minimum here scans the roots rather than storing a separate pointer. Space is O(N) nodes and child references. Python dictionary operations add expected hashing costs, and the stated structural bounds do not promise hard real-time latency. The forest representation pays more pointer overhead than an array heap, but melding it does not require inserting all donor entries one by one. This direct code assumes single-process ownership and does not synchronize concurrent producers.",
         mistakes=["Do not retain two roots with the same degree after a carry.", "Do not discard the removed root's children during extraction.", "Do not call the donor independently usable after ownership transfer.", "Do not promise constant-time minimum lookup when roots are scanned."],
         related=["dsa/pairing-heap-two-pass-meld", "dsa/binary-heap-priority-scheduling", "dsa/btree-page-split-insertion"]),
    dict(path="dsa/radix-heap-monotone-integer-priorities", program="radix_monotone_incident_queue.py",
         template="dsa/dary-heap-stable-priority-dispatch", section="dsa/trees-and-heaps",
         title="Radix heaps: queue nondecreasing integer priorities",
         summary="Bucket integer keys by their highest differing bit from the last extracted key.",
         definition="A radix heap is useful when priorities are nonnegative integers and no later insertion can fall below the last priority removed. It groups entries by the bit length of priority XOR the last removed priority. Bucket zero contains keys equal to that last value. If bucket zero is empty, the queue finds the first nonempty bucket, makes its smallest priority the new last value, and redistributes that bucket under the new difference. The monotone rule makes that redistribution safe: a future key cannot undercut an already extracted priority. This program rejects a lower inserted priority and returns the stored incident with its priority. It gives no stable order among equal priorities and cannot act as a general-purpose queue for arbitrary decreases.",
         case="A shortest-route worker extracts distances 19, 19, 47, and 61 from four initially pending incidents. A new candidate at priority 18 after the worker has removed priority 19 would violate the queue contract and raises instead of silently misplacing the entry. Nonnegative edge-weight route searches can satisfy the monotone extraction rule when they insert tentative distances after processing the current minimum. Negative edges and workloads that reprioritize old work downward do not satisfy it. The example prints priorities only because equal-priority incident order is unspecified.",
         cost="Let W be the maximum bit width reached by a key difference and N the number of accepted entries. Push computes one bucket index and appends in O(1) bucket work plus integer bit operations. A pop can scan O(W) buckets and redistribute O(N) entries in one call, so it has no logarithmic worst-case latency claim. Each entry changes buckets at most O(W) times as the last value grows, giving O(NW) total redistribution work over a finite-width batch; storage is O(N+W). Python integers are unbounded, so W is workload-dependent. The code does not handle deletion, decrease-key, or stable ties.",
         mistakes=["Do not insert a priority below the last extracted value.", "Do not sort equal priorities by incident ID unless the API promises that order.", "Do not call one redistribution pop constant time.", "Do not apply the queue to negative-weight route updates."],
         related=["dsa/stale-entry-heap-shortest-route", "dsa/binary-heap-priority-scheduling", "dsa/dary-heap-stable-priority-dispatch"]),
    dict(path="dsa/dual-heap-double-ended-priority-queue", program="dual_heap_incident_queue.py",
         template="dsa/dary-heap-stable-priority-dispatch", section="dsa/trees-and-heaps",
         title="Double-ended queues: reconcile min and max heaps",
         summary="Use two heaps and an exact live map to remove either priority extreme.",
         definition="A double-ended priority queue must remove the lowest or highest priority on demand. This design stores each incident in a min-heap and max-heap and keeps one exact live map keyed by incident ID. Removing from one heap deletes its live-map record; the matching entry in the other heap becomes stale and is skipped when encountered. Arrival numbers make equal-priority removal deterministic and prevent an old entry from matching a later reuse of the same ID. When heap entries grow too far beyond live records, both heaps are rebuilt from the live map. It is a practical twin-heap design, not a min-max heap with alternating tree levels. Duplicate live IDs are rejected.",
         case="Four incidents have priorities 47, 19, 61, and 19. Pop-min returns the first priority-19 arrival, valve-19. Pop-max then returns priority-61 sensor-61. Both removed incidents leave stale entries in the opposite heap, but the live map prevents either from being returned twice. Reusing a removed incident ID creates a new arrival number; a stale earlier heap record cannot masquerade as the new one. Without periodic rebuilding, a workload alternating additions and removals at one end can retain an arbitrarily large opposing heap even when few incidents remain live.",
         cost="Each insertion adds one entry to each heap, O(log N) time. A removal may skip many stale entries or trigger O(N) heap rebuilding, so one call has O(N log N) conservative worst-case work; across a long sequence, each stale entry is discarded once and threshold rebuilds amortize the cleanup. After a mutation, the threshold keeps stored heap entries O(L+1) for L live IDs, with a fixed small allowance. The exact live map means O(L) key storage as well, unlike an approximate membership structure. If memory or latency spikes cannot be accepted, use an indexed double-ended heap with stricter update rules. This example is single-threaded.",
         mistakes=["Do not return a stale entry from the opposite heap.", "Do not match a reused ID without checking its arrival generation.", "Do not claim every removal has logarithmic worst-case latency.", "Do not omit a compaction policy when stale entries can accumulate."],
         related=["dsa/binary-heap-priority-scheduling", "dsa/two-heap-running-median", "dsa/ttl-heap-expiration-with-stale-records"]),
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
                 sort_order=42800 + order * 10, created_at=stamp, updated_at=stamp, published_at=stamp)
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
project_path = "dsa/priority-queue-meld-monotone-extreme-audit-project"
quiz_path = "quizzes/dsa-priority-queue-meld-monotone-extreme-contracts"
assert project_path not in by_path and quiz_path not in by_path
project = copy.deepcopy(by_path["dsa/approximate-membership-mutation-audit-project"])
project.update(id=str(uuid.uuid5(uuid.NAMESPACE_URL, "aitrove:" + project_path)), path=project_path,
               title="Project: audit four priority-queue contracts", summary="Check forest merge, root pairing, monotone keys, and both removal extremes.",
               sort_order=42840, created_at=stamp, updated_at=stamp, published_at=stamp)
project["data"].update(reading_minutes=30, related=[{"path": path, "title": by_path[path]["title"]} for path in new_paths])
project["body"] = (
    "<p>A regional dispatcher has to join two task queues, process nondecreasing route distances, and occasionally remove both the cheapest and most urgent task. These are different operation contracts. Build an exact sorted reference for each queue and compare every result after each mutation. Test pairing and binomial heaps against merged reference queues, a radix heap against nonnegative integer priorities that never fall below the last extraction, and the dual heap against the smallest and largest live task keys. Keep distinct incident IDs and explicit insertion order. A queue that gives correct output on one fixed list can still fail after a donor is reused, a degree carry is missed, or a stale opposite-heap entry is returned twice.</p>"
    "<h2>Acceptance trace</h2><p>Give East priorities 47 and 19, West priorities 19 and 61, then meld them. Both meldable queues must leave West empty and return the four IDs by priority, preserving the two priority-19 arrivals in their global order. Insert integer priorities 47, 19, 61, and 19 into the radix queue and check the extracted numeric order. After the first priority-19 removal, reject a new priority 18. In the double-ended queue, remove minimum 19 and maximum 61, then verify that neither incident can reappear from the opposite heap.</p>"
    '<h3>Expected review record</h3><pre><code class="language-text">melded-order=[valve-19, sensor-61, pump-47, grid-83]\nradix-order=[19, 19, 47, 61] late-priority-18=rejected\ndual-min=valve-19 dual-max=sensor-61</code></pre>'
    "<h2>Boundary and cost review</h2><p>Test an empty pop, a self-meld, equal priorities from separate queues, a binomial forest with repeated carries, a radix bucket containing several distinct priorities, reuse of a removed ID, and a long run that leaves stale entries in one dual heap. Distinguish worst-case latency from amortized sequence cost. The pairing pop can scan many children, radix redistribution can move many entries at once, and dual-heap cleanup can rebuild both arrays. State which APIs expose meld, which accept only monotone integer priorities, and which support both minimum and maximum removal.</p>"
    "<h3>Common Mistakes</h3><ul><li>Do not call every heap meld a copy.</li><li>Do not leave duplicate binomial root degrees.</li><li>Do not insert below the radix queue's last extraction.</li><li>Do not return stale entries from the opposite heap.</li></ul>"
    "<h2>Connected lessons</h2>" + links(new_paths + ["dsa/projects", "dsa/quizzes", subject_root])
)
entries.append(project)
by_path[project_path] = project

questions = [
    ("What does pairing-heap meld compare?", ["The two roots, attaching the larger beneath the smaller", "Every node in both heaps", "The last child of each root only"], "Meld preserves heap order by comparing roots and making the larger root a child of the smaller one."),
    ("How does this pairing heap rebuild after delete-min?", ["Pair adjacent children, then fold paired trees from right to left", "Sort every node by incident ID", "Keep only the first child and discard the rest"], "The two-pass process first forms pairs and then melds those subtrees back into one valid heap."),
    ("What happens to the donor after pairing-heap meld?", ["It becomes empty because node ownership transfers", "It retains an independent copy", "Both queues share a mutable root forever"], "The implementation transfers the donor root and size into the recipient, then clears the donor fields."),
    ("What is the binomial forest invariant?", ["At most one tree of each degree", "Every root has exactly one child", "All trees have the same degree"], "Equal-degree trees are linked like a binary carry until each occupied degree has one root."),
    ("What does linking two degree-D binomial trees produce?", ["One degree-D-plus-one tree", "Two degree-D-minus-one trees", "A sorted array of all nodes"], "One root becomes a child of the other, increasing the winning root's degree by one."),
    ("Why inspect all binomial roots during this pop?", ["This implementation does not maintain a separate minimum-root pointer", "Children always contain the minimum", "There is exactly one root for every node"], "The minimum must be selected among O(log N) roots before its children are merged back into the forest."),
    ("What priority can be inserted after a radix queue last removed 47?", ["An integer at least 47", "Any negative integer", "Only an integer below 47"], "The monotone queue requires every later inserted priority to be no smaller than the last extracted priority."),
    ("What decides a radix bucket number?", ["The bit length of priority XOR the last extracted priority", "The incident ID string length", "The number of current queue members"], "The highest differing bit from the last removed key groups entries that may need redistribution together."),
    ("What can one radix pop cost when bucket zero is empty?", ["A scan and redistribution of many queued entries", "Exactly one array access in all cases", "A full sort of every original stream record"], "Advancing the last key may move every entry in the first nonempty bucket during a single extraction."),
    ("What identifies a live dual-heap entry?", ["Incident ID together with priority and arrival number", "Only its incident ID", "Only whether it is at either heap root"], "An arrival generation prevents a stale record for a reused ID from being mistaken for its later insertion."),
    ("Why can the dual-ended queue hold stale heap records?", ["Removing from one heap leaves the matching record in the other", "Every push copies all earlier tasks", "It never deletes live-map entries"], "The opposite heap is cleaned lazily, so its old record must be skipped or removed during compaction."),
    ("What cost can dual-heap compaction add to one operation?", ["A linear rebuild of both heaps from live state", "A guaranteed constant-time pointer change", "An exact distinct-count calculation"], "The threshold rebuild discards accumulated stale entries, which can make one call much slower than its amortized average."),
]
balanced = []
for number, (prompt, options, explanation) in enumerate(questions):
    distractors = options[1:]
    position = number % 3
    distractors.insert(position, options[0])
    balanced.append({"prompt": prompt, "options": distractors, "answer": position, "explanation": explanation})
quiz = copy.deepcopy(by_path["quizzes/dsa-approximate-membership-mutation-contracts"])
quiz.update(id=str(uuid.uuid5(uuid.NAMESPACE_URL, "aitrove:" + quiz_path)), path=quiz_path,
            title="Priority-queue merge, monotonicity, and extremes", summary="Check tree carries, pairing passes, radix buckets, and stale twin-heap entries.",
            sort_order=42850, created_at=stamp, updated_at=stamp, published_at=stamp)
quiz["data"].update(duration_minutes=20, related=[{"path": path, "title": by_path[path]["title"]} for path in new_paths + [project_path]], questions=balanced)
quiz["body"] = "<p>Choose the operation contract that each queue actually supports, then check what happens at a merge, redistribution, or stale entry.</p><h2>Lessons</h2>" + links(new_paths) + "<h2>Design exercise</h2>" + links([project_path, subject_root])
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
    ("dsa/binary-heap-priority-scheduling", new_paths[0]),
    ("dsa/binary-heap-priority-scheduling", new_paths[1]),
    ("dsa/stale-entry-heap-shortest-route", new_paths[2]),
    ("dsa/dary-heap-stable-priority-dispatch", new_paths[2]),
    ("dsa/two-heap-running-median", new_paths[3]),
    ("dsa/ttl-heap-expiration-with-stale-records", new_paths[3]),
):
    old = by_path[old_path]
    old["body"] += '<p><a href="/' + new_path + '">' + html.escape(by_path[new_path]["title"]) + "</a> adds another queue operation contract.</p>"
    old["updated_at"] = stamp
for path in new_paths:
    entry = by_path[path]
    peers = [other for other in new_paths if other != path]
    entry["body"] += '<p>Compare its queue operations with ' + ", ".join('<a href="/' + other + '">' + html.escape(by_path[other]["title"]) + "</a>" for other in peers) + ', then run the <a href="/' + project_path + '">priority-queue audit</a> and <a href="/' + quiz_path + '">contract quiz</a>.</p>'
    entry["updated_at"] = stamp

fixture.write_text(json.dumps(entries, ensure_ascii=False, indent=2) + "\n")
print(json.dumps({"lessons": new_paths, "project": project_path, "quiz": quiz_path, "questions": len(questions)}))
