"""Add eviction, expiration, versioned handles, and wider heap branches."""

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
        path="dsa/lfu-cache-frequency-and-recency-eviction", program="lfu_incident_cache.py",
        template="dsa/lru-cache-eviction-invariant", section="dsa/hash-tables",
        title="LFU caches: evict by frequency, then recency",
        summary="Track one recency queue per frequency and remove the oldest key in the least-used group.",
        definition="An LFU cache tracks how often each resident key has been accessed. When full, it evicts a key from the smallest frequency group; within that group, it chooses the least recently accessed or written key. This implementation keeps a key-to-value-and-frequency map and an ordered key set for each active frequency. Reading a present key promotes it to the next group. Updating an existing key replaces its value and counts as one access. Inserting a new key starts at frequency one. Empty frequency groups are removed, and the minimum active frequency is kept explicitly. A miss returns None and does not alter counts. Capacity zero stores nothing. The cache is single-process and has no frequency aging or expiry policy.",
        case="An incident dashboard stores pump-47 and valve-19 in a cache with capacity two. Reading pump-47 increases its frequency. Inserting sensor-61 evicts valve-19, the only key still at the minimum frequency. Pump-47 remains available and valve-19 is absent. The internal ordered sets also decide a tie: if both keys had frequency one, the earlier member of that group would leave first. An update to a resident key is explicitly treated as an access, which differs from implementations that update without promotion. The policy must be chosen before comparing observed evictions with a reference model.",
        cost="For capacity C, expected lookup, promotion, insertion, and eviction are O(1) using hash maps and ordered dictionaries. Resident entries and their frequency-group membership use O(C) space, while the number of active groups is at most C. These are expected hash-operation bounds, not real-time guarantees. Frequencies grow without decay, so an old hot entry can resist eviction after the workload changes; production caches may age or reset counts. An LRU cache needs only one recency order and can be simpler. This LFU example does not bound retained Python integer frequency width, add thread synchronization, distinguish a stored None from a miss, or combine eviction with time-to-live.",
        mistakes=["Do not evict the newest key when frequencies tie; this policy uses least recent.", "Do not leave an empty minimum-frequency group behind after promotion.", "Do not change counts on a miss.", "Do not call lifetime access counts an aging frequency policy."],
        related=["dsa/lru-cache-eviction-invariant", "dsa/hash-map-collision-and-load-contract", "dsa/doubly-linked-list-relink-and-ownership"],
    ),
    dict(
        path="dsa/ttl-heap-expiration-with-stale-records", program="ttl_incident_index.py",
        template="dsa/binary-heap-priority-scheduling", section="dsa/trees-and-heaps",
        title="Expiry heaps: invalidate stale TTL records on replacement",
        summary="Pair a live-key map with a deadline heap and ignore old deadline entries after overwrites.",
        definition="A time-to-live index keeps live key values in a dictionary and expiration records in a min-heap. A write creates a unique serial number, stores its expiry beside the live value, and pushes the same expiry and serial into the heap. Advancing the clock removes every due heap record, but deletes a dictionary entry only when its current serial and expiry still match that record. This check prevents an earlier deadline from deleting a replacement value. The API uses caller-supplied integer time, requires nondecreasing calls, and defines an entry as expired at its deadline. A zero lifetime expires immediately. It has no background timer: expiration happens when the caller advances or queries the index.",
        case="At time 23, write pump-47 with lifetime 19, so its first deadline is 42. At time 29, replace it with a rechecked value lasting 38 units, with deadline 67. A read at time 42 must return rechecked; the first heap record is stale and cannot delete the replacement. A read at time 67 returns no value because the current deadline is due. A clock step back from 67 is rejected. The trace tests the serial identity rule rather than only heap order. A negative lifetime is rejected before any write occurs.",
        cost="With W heap records since the last full rebuild, insertion takes O(log W) time and the heap can use O(W) space even if only a few keys remain live. Advancing through E due records takes O(E log W) time; a read may trigger that work, so its worst-case latency is not constant. A sequence of reads with no due records uses expected O(1) dictionary work plus a heap-head check. Lazy stale records need a compaction policy if repeated overwrites would grow memory too far. This index does not promise wall-clock scheduling, durable timers, concurrent mutation safety, or a fixed upper bound on per-request cleanup work.",
        mistakes=["Do not let an old deadline delete a newer replacement of the same key.", "Do not describe lazy heap storage as O(number of live keys).", "Do not treat expiry at the deadline as still valid.", "Do not assume a background thread removes entries without an advance call."],
        related=["dsa/binary-heap-priority-scheduling", "dsa/stale-entry-heap-shortest-route", "dsa/lfu-cache-frequency-and-recency-eviction"],
    ),
    dict(
        path="dsa/generational-slot-map-stale-handle-rejection", program="generational_incident_handles.py",
        template="dsa/sparse-set-bounded-identifiers", section="dsa/array-data-structure-guide",
        title="Generational slots: reject stale handles after reuse",
        summary="Pair each reusable array slot with a changing generation and a store identity.",
        definition="A generational slot store hands callers a handle containing an owning-store identity, a slot number, and that slot's generation. Removal marks the slot empty, increments its generation, and puts its number on a free list. A later insertion may reuse the same physical slot, but the earlier handle no longer matches its new generation. Looking up an old or foreign handle raises instead of returning another incident. The implementation uses a private empty marker so None can itself be stored as a value. Handles are immutable dataclass values, and the store identity is compared by object identity. This is a single-process model; handles are not serialized or valid after a store is reconstructed.",
        case="Insert pump-47 and retain its handle. Remove it, then insert valve-19. The second incident reuses the freed array position, yet its generation differs, so the old pump handle fails lookup and the new valve handle succeeds. A handle from another store also fails even if slot and generation happen to match. Without generations, recycling slot zero would let a stale caller silently read valve-19 as though it were pump-47. The example's unbounded Python integer generations avoid wraparound in ordinary execution, while fixed-width production implementations need an explicit overflow policy.",
        cost="Insertion, lookup, and removal take O(1) list operations in the normal model; free-list push and pop are O(1), and memory is O(S) for S slots ever allocated until an explicit compaction design is added. Removed slots are reused, but the backing arrays do not shrink. A handle stores three fields, including an owner token, so it costs more than a raw integer index. Operations on Python's growing generation integers have bit-length cost beyond a fixed-width model. This design prevents stale-slot aliasing within one live store, but does not provide thread synchronization, durable IDs, garbage collection, or a safe strategy for serialized handles crossing process lifetimes.",
        mistakes=["Do not reuse a slot without advancing its generation.", "Do not accept a handle from a different store instance.", "Do not use None as an empty marker when None is a valid stored value.", "Do not serialize this in-memory owner token as a durable identity."],
        related=["dsa/sparse-set-bounded-identifiers", "dsa/resizable-array-growth-and-insert-cost", "dsa/immutable-index-snapshot-publication"],
    ),
    dict(
        path="dsa/dary-heap-stable-priority-dispatch", program="dary_dispatch_heap.py",
        template="dsa/binary-heap-priority-scheduling", section="dsa/trees-and-heaps",
        title="D-ary heaps: trade shallower ascent for wider extraction",
        summary="Use four-way branching and a sequence counter to keep equal-priority dispatch stable.",
        definition="A d-ary min-heap stores a complete tree in one array. For zero-based position I, its parent is floor((I - 1) / D), and its children occupy D times I plus one through D times I plus D. Insertion bubbles a new entry toward the root. Extraction saves the root, moves the last entry down the cheapest-child path, and returns the root task. This program requires D at least two. Each entry carries a unique insertion sequence after the priority, so equal priorities leave in arrival order and incident identifiers are never compared. It implements push and pop only; there is no decrease-key operation or deletion of an arbitrary pending incident.",
        case="A four-way heap receives pump at priority 47, valve at 19, sensor at 19, and grid at 61. Popping four times returns valve, sensor, pump, grid. Valve wins the tie because it was inserted before sensor. Changing D would alter the array shape and number of child comparisons but should not alter that output order. A queue that stores only priority and an incident object may fail when two priorities tie and the objects cannot be ordered; the sequence field prevents that accidental comparison.",
        cost="For N pending incidents, insertion crosses at most O(log base D of N) ancestors. Extraction descends the same height but scans up to D children per level, taking O(D log base D of N) comparisons. Peek would be O(1), and storage is O(N). Larger D can shorten the path while increasing work per extraction; the best arity depends on the operation mix and machine behavior. A binary heap is often enough. This Python example uses a range and min call for each child scan, making the comparison cost visible rather than claiming a universal speedup. It does not support a stable reprioritization or indexed decrease key.",
        mistakes=["Do not use binary child formulas in a four-way heap.", "Do not compare incident objects to break equal priorities.", "Do not claim every larger arity makes extraction faster.", "Do not advertise decrease-key when the implementation exposes only push and pop."],
        related=["dsa/binary-heap-priority-scheduling", "dsa/indexed-binary-heap-decrease-key", "dsa/stale-entry-heap-shortest-route"],
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
                 sort_order=42500 + order * 10, created_at=stamp, updated_at=stamp, published_at=stamp)
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
project_path = "dsa/incident-retention-and-dispatch-audit-project"
quiz_path = "quizzes/dsa-eviction-expiry-handle-heap-contracts"
assert project_path not in by_path and quiz_path not in by_path
project = copy.deepcopy(by_path["dsa/incident-text-index-contract-audit-project"])
project.update(id=str(uuid.uuid5(uuid.NAMESPACE_URL, "aitrove:" + project_path)), path=project_path,
               title="Project: audit incident retention and dispatch", summary="Check four mutation contracts against explicit reference states.",
               sort_order=42540, created_at=stamp, updated_at=stamp, published_at=stamp)
project["data"].update(reading_minutes=30, related=[{"path": path, "title": by_path[path]["title"]} for path in new_paths])
project["body"] = (
    "<p>A dispatch console caches incident summaries, expires temporary states, recycles incident slots, and schedules work by priority. These are four separate lifecycles. Implement a plain reference alongside each index: scan resident cache entries for minimum frequency and oldest tie, scan live expiration records at an explicit clock value, keep every issued handle with its expected live or stale status, and sort queued tasks by priority followed by insertion order. Compare the result after every operation. A cached value may still exist while its TTL entry has expired; a freed slot may be reused while its previous handle remains invalid. Treat these differences as contracts, not as implementation details to smooth over.</p>"
    "<h2>Acceptance trace</h2><p>Cache pump-47 and valve-19 at capacity two, read pump-47, then add sensor-61: valve-19 leaves. Write pump-47 at time 23 for 19 units and replace it at time 29 for 38 units: the replacement survives the old deadline 42 and expires at 67. Remove the first handle for pump-47, then insert valve-19 into its slot: the first handle must fail and the new one must resolve. For four-way dispatch, insert priorities 47, 19, 19, and 61 in that order; the two priority-19 incidents leave in their arrival order.</p>"
    '<h3>Expected output</h3><pre><code class="language-text">evicted=valve-19 at-42=rechecked at-67=none\nold-handle=stale dispatch=[valve, sensor, pump, grid]</code></pre>'
    "<h2>Boundary and cost review</h2><p>Try zero cache capacity, a frequency tie, an overwritten key with several old expiry records, zero lifetime, backward time, a foreign-store handle, repeated removal, an empty dispatch heap, and equal priorities with non-comparable task objects. State the memory bound for each component. Lazy expiry records can outnumber live keys; the slot store retains its highest allocated size even after deletion; and the heap keeps only pending tasks. The examples model single-process state. Durable scheduling, synchronization, generation overflow in fixed-width languages, and cache frequency aging require separate designs.</p>"
    "<h3>Common Mistakes</h3><ul><li>Do not break LFU ties with newest-first eviction.</li><li>Do not let an old expiry record remove a replacement.</li><li>Do not resolve a handle solely by its slot number.</li><li>Do not compare task objects on equal priority.</li></ul>"
    "<h2>Connected lessons</h2>" + links(new_paths + ["dsa/projects", "dsa/quizzes", subject_root])
)
entries.append(project)
by_path[project_path] = project

questions = [
    ("Which resident leaves when LFU frequency is tied?", ["The least recently used key within the minimum-frequency group", "The most recently used key", "The key with the longest string"], "The stated policy resolves an equal-frequency tie by the oldest recency position in that frequency group's ordered keys."),
    ("What does a successful LFU get do here?", ["Return the value and increase its access frequency", "Return the value without changing state", "Evict another key immediately"], "A present key is moved to the next frequency group, while a miss returns None without touching counters."),
    ("Why remove an empty minimum-frequency group?", ["The minimum pointer must identify an active group", "Every frequency must remain allocated forever", "A miss should create a new group"], "After the last key leaves a group, retaining it as the minimum would make later eviction select an empty container."),
    ("How does the expiry heap avoid deleting a replacement?", ["Compare the popped expiry and serial with the current live record", "Delete by key whenever any deadline appears", "Keep one heap entry total for all keys"], "A stale deadline can remain in the heap after overwrite, so its serial must match the current dictionary entry before deletion."),
    ("What is true at an entry's exact expiry deadline?", ["It is expired", "It remains live for one extra unit", "Its value is promoted to the LFU cache"], "The API defines expiry as due when the stored deadline is less than or equal to the advanced clock value."),
    ("Why can expiry-heap storage exceed live-key count?", ["Overwrites leave old deadline records until they are popped or compacted", "Dictionary lookup duplicates all records", "The heap stores one node per clock tick"], "Lazy replacement writes another heap record, and stale records with future deadlines can remain after their keys are overwritten."),
    ("What invalidates a removed slot handle after slot reuse?", ["A changed generation at the same slot", "Changing the payload string only", "Sorting all slot values"], "The handle's old generation no longer matches the reused slot, preventing a stale reference from resolving to a new value."),
    ("Why include store identity in this in-memory handle?", ["Matching slot and generation from another store must still be rejected", "It makes the handle durable across processes", "It eliminates the free list"], "Two stores can allocate the same slot and generation, so the owner token separates their otherwise identical handle fields."),
    ("What is retained after every slot is removed?", ["Allocated slot and generation arrays remain available for reuse", "Only the last payload remains live", "Every old handle becomes valid again"], "The free list reuses slots but this implementation does not shrink its backing arrays or restore stale generations."),
    ("What is the parent of d-ary heap position I greater than zero?", ["Floor of (I minus one) divided by D", "Floor of I divided by two for every D", "D times I plus one"], "A complete d-ary array tree assigns each parent D consecutive child positions beginning at D times parent plus one."),
    ("Why does the dispatch entry include an insertion sequence?", ["Equal priorities leave in arrival order without comparing task objects", "It makes extraction constant time", "It removes the priority field"], "The unique sequence breaks priority ties before Python reaches an incident object that may not support ordering."),
    ("What does a larger heap arity increase during extraction?", ["The number of child candidates compared per level", "The number of values stored per task", "The cost of reading an empty queue"], "Wider branching shortens the descent but requires checking up to D children at each level to find the smallest."),
]
balanced = []
for number, (prompt, options, explanation) in enumerate(questions):
    correct = options[0]
    distractors = options[1:]
    position = number % 3
    distractors.insert(position, correct)
    balanced.append({"prompt": prompt, "options": distractors, "answer": position, "explanation": explanation})
quiz = copy.deepcopy(by_path["quizzes/dsa-postings-position-grams-lexicon-contracts"])
quiz.update(id=str(uuid.uuid5(uuid.NAMESPACE_URL, "aitrove:" + quiz_path)), path=quiz_path,
            title="Eviction, expiry, handles, and heap contracts", summary="Check frequency ties, stale deadlines, recycled slots, and wider heap paths.",
            sort_order=42550, created_at=stamp, updated_at=stamp, published_at=stamp)
quiz["data"].update(duration_minutes=20, related=[{"path": path, "title": by_path[path]["title"]} for path in new_paths + [project_path]], questions=balanced)
quiz["body"] = "<p>Check the lifecycle behind each structure: cache reads alter frequency, deadlines can go stale, slot generations reject old handles, and equal-priority tasks need a stable tie rule.</p><h2>Lessons</h2>" + links(new_paths) + "<h2>Design exercise</h2>" + links([project_path, subject_root])
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
    ("dsa/hash-map-collision-and-load-contract", new_paths[0]),
    ("dsa/binary-heap-priority-scheduling", new_paths[1]),
    ("dsa/stale-entry-heap-shortest-route", new_paths[1]),
    ("dsa/sparse-set-bounded-identifiers", new_paths[2]),
    ("dsa/resizable-array-growth-and-insert-cost", new_paths[2]),
    ("dsa/indexed-binary-heap-decrease-key", new_paths[3]),
):
    old = by_path[old_path]
    old["body"] += '<p><a href="/' + new_path + '">' + html.escape(by_path[new_path]["title"]) + "</a> adds a related lifecycle choice.</p>"
    old["updated_at"] = stamp
for path in new_paths:
    entry = by_path[path]
    peers = [other for other in new_paths if other != path]
    entry["body"] += '<p>Compare its invariant with ' + ", ".join('<a href="/' + other + '">' + html.escape(by_path[other]["title"]) + "</a>" for other in peers) + ', then run the <a href="/' + project_path + '">retention and dispatch audit</a> and <a href="/' + quiz_path + '">operation quiz</a>.</p>'
    entry["updated_at"] = stamp

fixture.write_text(json.dumps(entries, ensure_ascii=False, indent=2) + "\n")
print(json.dumps({"lessons": new_paths, "project": project_path, "quiz": quiz_path, "questions": len(questions)}))
