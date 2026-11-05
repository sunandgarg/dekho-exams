"""Add cache-policy and timer-wheel lessons with linked review material."""

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
    dict(path="dsa/clock-second-chance-page-cache", program="clock_second_chance_cache.py",
         template="dsa/lru-cache-eviction-invariant", section="dsa/hash-tables",
         title="CLOCK caches: revisit pages through reference bits",
         summary="Use a circular hand and one access bit per resident page before eviction.",
         definition="A CLOCK cache stores page frames in a circular array, a reference bit beside each frame, and a map from page ID to frame position. A hit sets that page's bit. On a full-cache insertion, the hand inspects one frame at a time: a set bit is cleared and skipped, while the first clear bit identifies the victim. The hand then advances beyond the replacement. Newly inserted pages begin with a clear bit in this explicit policy; they have entered the cache but have not received a later hit. This approximates recency without moving a linked-list node on every hit. It does not preserve exact least-recently-used order. A page with a set bit can still be evicted after the hand clears it and completes another cycle.",
         case="Three page frames hold incident pages 47, 19, and 61. A read of 47 sets its reference bit. When page 83 arrives, the hand gives 47 a second chance, then replaces 19 because that page's bit is clear. Residents are 47, 61, and 83. An insertion into a free frame does not evict another page. Updating an existing page replaces its payload in place and marks it referenced. Missing reads raise an error rather than inserting placeholder data. The return value of put names the evicted page, if any, so a caller can distinguish a replacement from an update or unused-frame fill.",
         cost="A hit uses expected O(1) dictionary lookup and one bit update. A full insertion can inspect at most two complete passes over C frames: the first clears set bits and the second finds a clear bit, so its worst-case time is O(C). Frame storage, bits, and the position map each use O(C) space. Across many replacements the hand spreads scans, but this Python example makes no measured amortized or hardware-cache claim. There is no removal API, dirty-page handling, concurrent access control, or write-back callback. The reference bit is only a one-bit history sample, not a timestamp.",
         mistakes=["Do not claim that CLOCK implements exact LRU order.", "Do not forget to remove an evicted page from the position map.", "Do not leave the hand on the replaced frame after insertion.", "Do not treat a set reference bit as permanent immunity from eviction."],
         related=["dsa/lru-cache-eviction-invariant", "dsa/ring-buffer-capacity-and-wrap", "dsa/lfu-cache-frequency-and-recency-eviction"]),
    dict(path="dsa/segmented-lru-probation-protected", program="segmented_lru_incidents.py",
         template="dsa/lru-cache-eviction-invariant", section="dsa/hash-tables",
         title="Segmented LRU: separate probation from protected reuse",
         summary="Promote hits into a protected recency list and demote its oldest entry.",
         definition="Segmented LRU maintains two access-ordered groups. New incident records enter probation. A read hit in probation moves its record to the protected group, where repeated hits refresh its recency. When protected exceeds its own capacity, its oldest record returns to probation. If that demotion overfills probation, probation's oldest record is evicted. This gives a record that has been read twice a chance to survive a stream of one-time insertions. The implementation uses Python OrderedDict instances, whose map lookups and end moves are expected constant time. It fixes both segment capacities; their sum is the maximum number of residents, but a quiet protected segment does not lend its unused slots to probation in this model.",
         case="With two probation slots and two protected slots, incidents 47 and 19 enter probation. Reading 47 promotes it. Incident 61 enters probation, and a read promotes it. Reading 19 then fills the protected segment beyond capacity, so its oldest member, 47, falls back into probation. The final protected order is 61 then 19, and probation contains 47. A write to an existing protected record refreshes its protected position. A write to an existing probation record refreshes that group's order but does not count as a promotion; only the read path promotes in this policy. That rule is deliberate and must be stated when comparing traces.",
         cost="A successful lookup, insertion, promotion, demotion, and eviction each perform expected O(1) ordered-map operations. Each operation can trigger at most one protected demotion and one probation eviction, so the total expected time is O(1) per call under ordinary hash behavior. Resident storage is O(P + R) for probation capacity P and protected capacity R, plus map metadata. The two fixed partitions can waste available capacity when protected is empty and probation is full. This is not an adaptive policy, does not age access counts, and does not handle weighted objects or expiry.",
         mistakes=["Do not put one incident ID in both segments.", "Do not evict the protected oldest member without first demoting it to probation.", "Do not promise unused protected slots are borrowed by probation in this model.", "Do not count a probation write as a promotion when the implementation promotes only reads."],
         related=["dsa/lru-cache-eviction-invariant", "dsa/lfu-cache-frequency-and-recency-eviction", "dsa/clock-second-chance-page-cache"]),
    dict(path="dsa/aging-frequency-sketch-cache-admission", program="aging_frequency_admission.py",
         template="dsa/count-min-sketch-frequency-boundary", section="dsa/hash-tables",
         title="Frequency admission: compare an arrival with an eviction victim",
         summary="Age bounded count estimates and reject a low-frequency candidate at capacity.",
         definition="Admission decides whether an arriving item deserves cache space; eviction chooses the resident it would replace. This model keeps an LRU-ordered resident map and a separate four-row frequency sketch. Every lookup attempt and put records the key in the sketch, including a lookup that misses the resident map. A full-cache put compares the candidate's minimum row count with the LRU victim's estimate and admits only when the candidate estimate is strictly greater. Sketch counters saturate at fifteen and are halved after a fixed number of samples, limiting how long old traffic dominates. The digest is deterministic for the teaching trace. This is a simplified frequency-admission cache, not a complete windowed cache policy with adaptive regions or a measured hit-rate claim.",
         case="Residents 47 and 19 fill a two-entry cache. Four repeated reads of 47 make it a hot resident. Incident 83 arrives once and is rejected because its estimate does not exceed that of the least-recently-used victim. Five observations of incident 61 precede its put; the sketch now rates 61 above victim 19, so 61 is admitted and 19 is removed. The remaining residents are 47 and 61. Recording a request is distinct from admitting its payload, and a rejected candidate can still gain frequency evidence through later requests. Digest collisions may inflate an estimate, so this comparison is a heuristic rather than proof of future demand.",
         cost="With R rows, W counters per row, and key encoding length K, recording or estimating a key costs O(R + K) for bounded digest work; in this fixed model R is four. Every sample_size records the sketch halves all RW counters in O(RW) time, so an individual operation can have that spike. The cache map and recency update are expected O(1). Storage is O(RW + C) for C residents, excluding Python object overhead. Counter saturation and aging discard precise historical frequencies. A different hash policy, sample interval, or tie rule can change decisions, and a workload trace is needed to evaluate actual hit rates.",
         mistakes=["Do not call the sketch estimate an exact request count.", "Do not admit every miss automatically when the cache is full.", "Do not compare a candidate with an arbitrary resident when the policy names the LRU victim.", "Do not omit the O(RW) counter-halving spike from worst-case cost."],
         related=["dsa/count-min-sketch-frequency-boundary", "dsa/lfu-cache-frequency-and-recency-eviction", "dsa/lru-cache-eviction-invariant"]),
    dict(path="dsa/hashed-wheel-incident-expiry", program="hashed_expiry_wheel.py",
         template="dsa/ttl-heap-expiration-with-stale-records", section="dsa/stacks-and-queues",
         title="Hashed timing wheels: bucket incident expiries by tick",
         summary="Schedule, replace, cancel, and fire timers across a fixed circular slot array.",
         definition="A hashed timing wheel assigns each due tick to a circular slot by remainder. The active map stores the exact due tick, payload, and slot for every incident ID. The slot set holds IDs whose due ticks land there, including timers several complete revolutions away. Advancing time visits each intervening tick and examines the current slot; only entries whose exact due tick has arrived are removed and returned. Rescheduling an ID removes it from its old slot before inserting the new record, so an old expiry cannot fire after replacement. Cancellation removes both the map entry and slot membership. Time is an integer tick supplied by the caller and may move forward only. This model is single-process memory state, not a wall-clock scheduler or a durable job queue.",
         case="Incident 47 first has a review due at tick three, while incident 19 is due at tick eleven. Replacing 47's review sets its due tick to five. Advancing to tick three returns nothing; at tick five the replacement fires once with its new payload. The slot for tick eleven matches an earlier slot after one wheel revolution, but the exact due value keeps incident 19 pending until tick eleven. A missing cancellation raises an error, and a zero-delay schedule is rejected. The wheel's fixed slot count determines bucket collisions, not the maximum timer horizon; distant timers can remain in a slot across many turns.",
         cost="Scheduling or canceling uses expected O(1) set and map operations. Advancing by T ticks costs O(T + V), where V counts all entries inspected in visited slots; a far-future timer may be inspected again on every revolution. Returning E expired entries also costs O(E) output space. The wheel uses O(S + N) storage for S slots and N active timers. Unlike a min-heap, it does not jump directly to the next due event when many empty ticks pass. A hierarchy or round counters could reduce repeated distant-timer inspections, but that is outside this one-level model. The trace makes no real-time latency or concurrency guarantee.",
         mistakes=["Do not fire every item in a visited slot without checking its exact due tick.", "Do not leave an old slot membership after rescheduling the same ID.", "Do not move time backward after scheduling relative delays.", "Do not claim this wheel skips empty ticks or never revisits distant timers."],
         related=["dsa/ttl-heap-expiration-with-stale-records", "dsa/ring-buffer-capacity-and-wrap", "dsa/clock-second-chance-page-cache"]),
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
                 sort_order=43400 + order * 10, created_at=stamp, updated_at=stamp, published_at=stamp)
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
project_path = "dsa/cache-admission-expiry-policy-audit-project"
quiz_path = "quizzes/dsa-clock-slru-admission-wheel-contracts"
assert project_path not in by_path and quiz_path not in by_path
project = copy.deepcopy(by_path["dsa/allocation-ownership-coalescing-audit-project"])
project.update(id=str(uuid.uuid5(uuid.NAMESPACE_URL, "aitrove:" + project_path)), path=project_path,
               title="Project: audit eviction, admission, and expiry", summary="Trace four cache policies against explicit resident and deadline contracts.",
               sort_order=43440, created_at=stamp, updated_at=stamp, published_at=stamp)
project["data"].update(reading_minutes=30, related=[{"path": path, "title": by_path[path]["title"]} for path in new_paths])
project["body"] = (
    "<p>An incident service caches pages and records while scheduling review deadlines. Build four traces with separate state ledgers: CLOCK frame positions and reference bits, segmented LRU probation and protected order, resident LRU order plus sketch counters, and wheel slots plus exact due ticks. After each operation, verify every resident appears once, each index points to its current payload, and every active timer has exactly one slot membership. Compare decisions to a small direct simulator for each policy. Do not use a single plain LRU oracle for all four; their contracts differ intentionally.</p>"
    "<h2>Acceptance trace</h2><p>In a three-frame CLOCK cache, read 47 after filling 47, 19, and 61; inserting 83 evicts 19. In a two-plus-two segmented cache, the read sequence promotes 47, 61, and 19, leaving 61 and 19 protected and 47 on probation. In a two-entry frequency-admission cache, a cold 83 is rejected but a repeatedly observed 61 replaces 19. In an eight-slot wheel, replacing 47's tick-three review with a tick-five review prevents the old event and leaves incident 19 until tick eleven.</p>"
    '<h3>Expected review record</h3><pre><code class="language-text">clock-victim=19\nprotected=[61, 19]\ncold-admitted=False\nwheel-tick-3=[]\nwheel-tick-5=[47]</code></pre>'
    "<h2>Boundary and cost review</h2><p>Force a CLOCK sweep in which every reference bit is set, and count all inspected frames. Overfill both segmented groups and test that a demoted record does not exist in protected and probation at once. Cause a sketch counter to age and verify no estimate increases solely from aging; record a rejected candidate's later requests before retrying. Schedule timers farther than one wheel revolution, replace and cancel keys, then advance across empty ticks. State the difference between an average map operation and a worst-case sweep, sketch reset, or large timer advance.</p>"
    "<h3>Common Mistakes</h3><ul><li>Do not present a second-chance bit as an exact last-access timestamp.</li><li>Do not promote a probation write when this policy promotes only reads.</li><li>Do not call sketch estimates exact counts.</li><li>Do not fire a timer based only on its wheel slot.</li></ul>"
    "<h2>Connected lessons</h2>" + links(new_paths + ["dsa/projects", "dsa/quizzes", subject_root])
)
entries.append(project)
by_path[project_path] = project

questions = [
    ("What does a CLOCK hit change?", ["The resident frame's reference bit", "Every frame's page ID", "The capacity of the circular array"], "A hit records recent use by setting one bit at the page's known frame position without moving the page itself."),
    ("When does the CLOCK hand evict a frame?", ["When it reaches a frame whose reference bit is clear", "Whenever it reaches the most recently read page", "Only after resizing the frame array"], "The hand clears and skips set bits, then selects the first clear bit it encounters for replacement."),
    ("Why is a full CLOCK insertion not worst-case constant time?", ["It may scan across the frame array and clear many bits", "It sorts all resident IDs lexically", "It always copies every page payload"], "When all bits are set, the hand must clear them before it can find a clear victim, so one insertion scans proportional to capacity."),
    ("Where does a new segmented-LRU record enter?", ["The probation segment", "The protected segment", "Both segments at once"], "The model places new records on probation and reserves protected space for records promoted by a read hit."),
    ("What happens when protected exceeds its capacity?", ["Its oldest record is demoted to probation", "Its newest record is always deleted immediately", "All probation records move to protected"], "The oldest protected member returns to probation, which may then evict its own oldest member if over capacity."),
    ("Does an existing probation write promote the record here?", ["No; this policy promotes on a read hit", "Yes; all writes jump directly to protected", "Only if the wheel slot is empty"], "A probation write updates value and local recency while the explicit get path performs the promotion."),
    ("What is compared when the frequency cache is full?", ["Candidate estimate and LRU victim estimate", "Only the candidate's text length", "The due ticks of all cached entries"], "The admission decision keeps the incoming value only if its sketch estimate exceeds that of the resident it would evict."),
    ("Why can the sketch estimate differ from an exact count?", ["Hash collisions and counter aging change the bounded counters", "OrderedDict hides all resident keys", "Every lookup bypasses the sketch"], "Several keys can share counters, while saturation and periodic halving also discard precise historical counts."),
    ("What operation causes a sketch-wide latency spike?", ["Halving every counter after the sample threshold", "Moving one resident to the LRU end", "Looking up one key in a dictionary"], "Aging walks all rows and columns at once, which costs work proportional to the sketch dimensions for that call."),
    ("Why does a timing wheel retain exact due ticks?", ["Different revolutions can map to the same slot", "Every timer must expire after one tick", "The slot index is a unique identifier"], "Slot remainder alone cannot distinguish a near timer from a distant timer that lands in the same bucket on a later revolution."),
    ("What must rescheduling one timer ID remove?", ["Its old slot membership", "Every other timer in that slot", "All past expiry outputs"], "Removing the old membership before inserting a new due record prevents an obsolete schedule from firing or appearing twice."),
    ("What drives the cost of advancing this one-level wheel?", ["Ticks traversed plus entries inspected in visited slots", "Only the number of timers that expire", "A binary heap height for every tick"], "The implementation walks each intervening tick and may inspect a distant timer again when its slot recurs before its due tick."),
]
balanced = []
for number, (prompt, options, explanation) in enumerate(questions):
    distractors = options[1:]
    position = number % 3
    distractors.insert(position, options[0])
    balanced.append({"prompt": prompt, "options": distractors, "answer": position, "explanation": explanation})
quiz = copy.deepcopy(by_path["quizzes/dsa-arena-free-buddy-slab-contracts"])
quiz.update(id=str(uuid.uuid5(uuid.NAMESPACE_URL, "aitrove:" + quiz_path)), path=quiz_path,
            title="CLOCK, segmented LRU, admission, and timer wheels", summary="Check replacement, promotion, admission estimates, and exact expiry ticks.",
            sort_order=43450, created_at=stamp, updated_at=stamp, published_at=stamp)
quiz["data"].update(duration_minutes=20, related=[{"path": path, "title": by_path[path]["title"]} for path in new_paths + [project_path]], questions=balanced)
quiz["body"] = "<p>Separate eviction, admission, and expiry decisions before comparing cache traces. Check residency and time invariants after every operation.</p><h2>Lessons</h2>" + links(new_paths) + "<h2>Design exercise</h2>" + links([project_path, subject_root])
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
    ("dsa/lru-cache-eviction-invariant", new_paths[0]),
    ("dsa/ring-buffer-capacity-and-wrap", new_paths[0]),
    ("dsa/lru-cache-eviction-invariant", new_paths[1]),
    ("dsa/lfu-cache-frequency-and-recency-eviction", new_paths[1]),
    ("dsa/count-min-sketch-frequency-boundary", new_paths[2]),
    ("dsa/lfu-cache-frequency-and-recency-eviction", new_paths[2]),
    ("dsa/ttl-heap-expiration-with-stale-records", new_paths[3]),
    ("dsa/ring-buffer-capacity-and-wrap", new_paths[3]),
):
    old = by_path[old_path]
    old["body"] += '<p><a href="/' + new_path + '">' + html.escape(by_path[new_path]["title"]) + "</a> extends the retention comparison.</p>"
    old["updated_at"] = stamp
for path in new_paths:
    entry = by_path[path]
    peers = [other for other in new_paths if other != path]
    entry["body"] += '<p>Compare retention and timing contracts with ' + ", ".join('<a href="/' + other + '">' + html.escape(by_path[other]["title"]) + "</a>" for other in peers) + ', then run the <a href="/' + project_path + '">policy audit</a> and <a href="/' + quiz_path + '">contract quiz</a>.</p>'
    entry["updated_at"] = stamp

fixture.write_text(json.dumps(entries, ensure_ascii=False, indent=2) + "\n")
print(json.dumps({"lessons": new_paths, "project": project_path, "quiz": quiz_path, "questions": len(questions)}))
