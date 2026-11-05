"""Add four approximate-membership structure lessons and linked practice."""

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
    dict(path="dsa/counting-bloom-filter-balanced-deletion", program="counting_bloom_incident_filter.py",
         template="dsa/bloom-filter-membership-boundary", section="dsa/hash-tables",
         title="Counting Bloom filters: delete only a known insertion",
         summary="Replace membership bits with counters and make the deletion precondition explicit.",
         definition="A counting Bloom filter substitutes counters for the bits of an ordinary Bloom filter. Each insertion increments several hash-selected positions; a query reports possible membership only when every selected counter is positive. A balanced removal decrements the same positions. It can therefore remove a known prior insertion without clearing a bit still needed by another item. This implementation accepts repeated insertions as separate multiplicities. The caller must know that an insertion exists and has not already been removed. A positive filter lookup is not evidence of that fact: an absent key can test positive through collisions, and deleting it can create a false negative for a real key. The filter deliberately stores no exact key ledger, so it cannot enforce the precondition by itself.",
         case="An incident cache records pump-47 twice and valve-19 once. Removing one known pump insertion leaves pump-47 and valve-19 as possible members. The operation is safe because the caller has an exact insertion record elsewhere. A counter-underflow check catches some invalid removals, but it cannot detect every deletion of an absent false-positive key: the selected counters may all be positive due to other incidents. For a cache eviction pipeline, pair the filter with the authoritative cache-key state and update them as one logical mutation. Calling remove after a merely positive might-contain result breaks the no-false-negative contract.",
         cost="For H hash positions and M counters, insertion, lookup, and known-insert removal take O(H) hash and counter operations plus O(length of the encoded ID) hashing work per position. Storage is O(M) counters, larger than an M-bit filter; this Python list uses full integers and makes no compact-memory claim. Unbounded Python counters avoid arithmetic overflow, whereas fixed-width counters need an overflow strategy. Equal positions within one key are counted with multiplicity during removal. Hash collisions still permit false positives. The structure does not report exact multiplicity, retain item identities, or support untrusted deletion requests.",
         mistakes=["Do not delete a key merely because the filter says it might exist.", "Do not ignore repeated hash positions when checking for counter underflow.", "Do not claim the counter array stores exact key counts.", "Do not let fixed-width counters silently wrap on overflow."],
         related=["dsa/bloom-filter-membership-boundary", "dsa/count-min-sketch-frequency-boundary", "dsa/lfu-cache-frequency-and-recency-eviction"]),
    dict(path="dsa/scalable-bloom-filter-layer-growth", program="scalable_bloom_incident_filter.py",
         template="dsa/bloom-filter-membership-boundary", section="dsa/hash-tables",
         title="Scalable Bloom filters: grow without discarding old members",
         summary="Add larger filter generations as insertion counts cross planned capacity.",
         definition="A fixed Bloom filter becomes less selective when insertions exceed its design load. A scalable filter keeps the old generation and creates a new, larger generation once the current one reaches its planned insertion count. Queries check every generation. An inserted key therefore remains queryable after later growth, and a negative answer still means absent under the fixed hash convention. This program doubles each generation's planned capacity and assigns generation I a shrinking error target equal to the total error budget divided by two to the I plus one. The targets form a geometric budget; the usual probability interpretation assumes suitable hash behavior and does not certify a particular deterministic stream. Repeated keys still consume insertion capacity because the filter cannot distinguish a duplicate from a false positive without an exact set.",
         case="A monitoring service plans initially for four new incident records, then receives fifteen. Rejecting later records would create false negatives. Rebuilding from absent source data would be impossible. The scalable index instead allocates generations sized for four, eight, and sixteen insertions, preserving the first record in its original generation and adding the last to the third. Every query examines all three. An approximate-positive answer can come from any generation and must be verified against authoritative storage before it triggers a user-facing claim. This lesson counts add calls, not distinct IDs; a stream of duplicates can force growth even when its true set remains small.",
         cost="If L generations exist and generation I uses H-I hash probes, an insertion touches one current generation in O(H-I) time while lookup costs O(sum of H-I across all L). Memory is the sum of all allocated generation bit counts. This Python program uses one byte per conceptual bit, so its actual memory is larger than a packed bit array. A generation is allocated at a capacity boundary, causing a one-time allocation cost. Layer targets add to the specified overall error budget under a probabilistic hash model; independence, truncation, and real key distributions affect observed rates. There is no deletion or space reclamation of earlier generations.",
         mistakes=["Do not query only the newest generation after growth.", "Do not treat duplicate insertions as free without an exact duplicate source.", "Do not mistake a target probability for a measured guarantee on one stream.", "Do not describe a bytearray of bits as a packed-bit implementation."],
         related=["dsa/bloom-filter-membership-boundary", "dsa/counting-bloom-filter-balanced-deletion", "dsa/lsm-sorted-runs-tombstone-compaction"]),
    dict(path="dsa/blocked-bloom-filter-locality-tradeoff", program="blocked_bloom_incident_filter.py",
         template="dsa/bloom-filter-membership-boundary", section="dsa/hash-tables",
         title="Blocked Bloom filters: localize probes and watch skew",
         summary="Choose one block per key and place all its membership bits inside that block.",
         definition="A blocked Bloom filter first maps an incident ID to one block, then sets several positions within that block. Lookup reads the same block and checks the positions. This arrangement keeps a key's probes together rather than scattering them across the whole filter. It is a layout tradeoff, not a proof that every implementation wins on a real CPU. The Python program stores each block as an integer bit mask. Blocks receiving more keys fill sooner and can produce more false positives than quieter blocks, even when overall occupancy looks moderate. The hash convention must stay fixed across writes and queries. As in a standard Bloom filter, positives need verification, and clearing a selected bit to delete one key would risk hiding another.",
         case="A dispatcher has sixteen independent bit blocks, each with sixty-four positions. Pump-47, valve-19, and sensor-61 are inserted. A pump query hashes to one block and tests four local bit positions. If many incident IDs land in that same block, its bit mask can saturate while another block stays sparse. A global percentage of set bits would conceal that hot block. Record per-block occupancy before trusting a chosen block count. The output prints membership for a known insertion and the number of blocks; it does not claim a measured cache miss rate or a universal false-positive probability.",
         cost="With H in-block hash probes, insertion and lookup use O(H) bit operations and hash work proportional to the encoded key length. The conceptual bit storage is O(BW) for B blocks of W bits; Python integer and list overhead make process memory larger. All probes concern one block, but this code uses separate hash calls and does not simulate hardware cache lines. Choosing a small W or concentrating keys in one block can raise false positives. There is no deletion, count estimate, or strict capacity; after enough insertions a saturated block always answers positive for its mapped keys.",
         mistakes=["Do not infer uniform per-block load from total filter occupancy.", "Do not claim Python integer blocks are physical cache-line measurements.", "Do not clear a shared bit to remove one incident.", "Do not treat a positive answer as proof of an existing incident."],
         related=["dsa/bloom-filter-membership-boundary", "dsa/scalable-bloom-filter-layer-growth", "dsa/hash-map-collision-and-load-contract"]),
    dict(path="dsa/cuckoo-filter-fingerprint-relocation", program="cuckoo_fingerprint_incident_filter.py",
         template="dsa/cuckoo-hashing-relocation-rebuild", section="dsa/hash-tables",
         title="Cuckoo filters: relocate compact fingerprints safely",
         summary="Store fingerprints in two candidate buckets and roll back a failed bounded insertion.",
         definition="A cuckoo filter stores a short fingerprint rather than a full incident ID. A key selects a first bucket, and its fingerprint determines an alternate bucket through an XOR offset. A fingerprint may occupy either bucket. When both are full, bounded relocations move an existing fingerprint to its alternate bucket until space opens. The alternate calculation is symmetric: applying the same XOR offset twice returns the original bucket. This program records displaced slots and restores them in reverse if its kick limit is reached, so a rejected insertion cannot lose a previously accepted fingerprint. Queries can return false positives when fingerprints collide. The filter does not deduplicate keys, and every successful add consumes a slot; duplicate submissions should be controlled by an authoritative layer.",
         case="A service inserts twenty-five incident IDs into two-slot buckets. Every accepted ID must remain a possible member even if later insertions kick fingerprints across buckets. If the table reaches a relocation cycle, add returns false and the old state is restored. The accepted list in the example is maintained only to demonstrate that invariant; the filter itself keeps no exact identities. Fingerprint-only deletion is intentionally absent from this API. Removing a matched fingerprint without an authoritative identity rule can erase a different key's representation when collisions and candidate-bucket overlap occur. A membership-positive result alone is never permission to delete.",
         cost="Lookup checks at most two buckets, each holding at most S fingerprints, so it takes O(S) comparisons plus hash work; S is often a small fixed bucket size. Direct insertion is O(S), while a displaced insertion can take O(KS) for a configured K-kick limit and O(K) undo records. Storage is O(BS) fingerprint slots for B buckets, excluding Python container overhead. The fixed table has no automatic growth or rebuild, and an insertion can fail before every slot is occupied. Finite fingerprints admit false positives; no quantified rate is promised for this deterministic example. The seeded relocation choice makes tests repeatable but is not a security mechanism.",
         mistakes=["Do not leave displaced entries changed after a failed insertion.", "Do not treat fingerprint equality as exact key equality.", "Do not assume an add call cannot fail below full occupancy.", "Do not delete a positive match without an identity-safe policy."],
         related=["dsa/cuckoo-hashing-relocation-rebuild", "dsa/bloom-filter-membership-boundary", "dsa/scalable-bloom-filter-layer-growth"]),
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
                 sort_order=42700 + order * 10, created_at=stamp, updated_at=stamp, published_at=stamp)
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
project_path = "dsa/approximate-membership-mutation-audit-project"
quiz_path = "quizzes/dsa-approximate-membership-mutation-contracts"
assert project_path not in by_path and quiz_path not in by_path
project = copy.deepcopy(by_path["dsa/stream-summary-distinct-sampling-audit-project"])
project.update(id=str(uuid.uuid5(uuid.NAMESPACE_URL, "aitrove:" + project_path)), path=project_path,
               title="Project: audit approximate-membership mutations", summary="Check delete preconditions, layer growth, block skew, and relocation rollback.",
               sort_order=42740, created_at=stamp, updated_at=stamp, published_at=stamp)
project["data"].update(reading_minutes=30, related=[{"path": path, "title": by_path[path]["title"]} for path in new_paths])
project["body"] = (
    "<p>A dispatch service uses approximate membership to avoid unnecessary index reads. Build four filters against one authoritative exact set or multiset in the test process. The exact structure is the oracle, not part of the bounded filter. Add and remove known insertions from a counting filter, grow a layered filter past its first capacity, send uneven key batches through a blocked filter, and fill a fingerprint table until its bounded insertion rejects a key. After every accepted mutation, every live exact key must still receive a possible-member answer. A false positive is allowed; a false negative for an accepted live key is not. Keep the identity of rejected cuckoo additions separate so a failed insertion does not become a supposed member.</p>"
    "<h2>Acceptance trace</h2><p>Insert pump-47 twice and valve-19 once into the counting filter, remove one known pump insertion, and check both keys. Insert fifteen unique IDs into a layered filter starting at capacity four; it should have three generations and retain the first and last IDs. Insert several codes into a sixteen-block filter, then inspect occupancy per block rather than a global average alone. Use a small cuckoo table to force relocation and eventual rejection; copy its buckets before a rejected add and assert the buckets match afterward. Finally, verify every previously accepted ID still receives a positive filter answer.</p>"
    '<h3>Expected review record</h3><pre><code class="language-text">known-removal=balanced layered-generations=3\nrejected-insert=rolled-back accepted-keys=possibly-present</code></pre>'
    "<h2>Boundary and cost review</h2><p>Try repeated hashes within one counting key, absent-key deletion attempts, duplicate additions that consume layer capacity, a saturated hot block, fingerprint collisions, and a relocation loop that reaches the kick limit. Make the exact oracle responsible for authorizing deletions. State separately the memory bound of each filter and the extra test-only exact state. Measured false-positive rates depend on size, hash distribution, and load; the demonstration's fixed examples do not certify a rate. If the application cannot tolerate a false positive, it must query the authoritative record before acting.</p>"
    "<h3>Common Mistakes</h3><ul><li>Do not infer deletion authority from a positive approximate lookup.</li><li>Do not discard old layers when capacity grows.</li><li>Do not hide a saturated block behind average occupancy.</li><li>Do not leave a failed relocation chain partly applied.</li></ul>"
    "<h2>Connected lessons</h2>" + links(new_paths + ["dsa/projects", "dsa/quizzes", subject_root])
)
entries.append(project)
by_path[project_path] = project

questions = [
    ("When is counting-filter removal safe?", ["When an authoritative record confirms an unmatched prior insertion", "Whenever might-contain returns true", "Whenever any one counter is positive"], "A positive approximate lookup can be a collision; deletion needs independently known insertion multiplicity to avoid false negatives."),
    ("Why count repeated hash positions during removal?", ["One key can increment the same counter more than once", "Each key always maps to different counters", "The filter stores the original key in every counter"], "If two probes choose one position, that position receives two increments for the key and must lose two on balanced removal."),
    ("What does a counting filter reveal about one key's exact multiplicity?", ["No exact multiplicity, because counters are shared", "Its smallest counter is always exact", "The full counter sum equals that key's count"], "Other keys contribute to the same counters, so even a positive result cannot identify a key or its precise count."),
    ("Where is a key inserted after a scalable filter creates a new generation?", ["The newest generation", "Every prior generation", "Only the first generation"], "The new generation receives later additions, while earlier generations remain available to answer queries for old members."),
    ("Why must scalable lookup inspect all generations?", ["An early key may exist only in an older generation", "Only the newest generation has hash bits", "The query must clear old bits first"], "Growth preserves old filters rather than rebuilding them, so a key inserted before growth may be absent from all later layers."),
    ("What can repeated IDs do to this scalable implementation?", ["Consume insertion capacity and trigger another generation", "Reduce the number of generations", "Make all positive answers exact"], "Without an exact duplicate index, every add call increments the current generation's insertion count even for a repeated ID."),
    ("How many blocks does one key probe in the blocked filter?", ["One selected block", "Every allocated block", "A separate block for every bit"], "The first hash selects a block, and all remaining hash-derived bit positions are local to that same block."),
    ("Why inspect occupancy per block?", ["A hot block may saturate while the global average stays low", "Every block must have identical occupancy", "A full block proves every queried key exists"], "Uneven key distribution can make one block return many positive answers despite sparse neighbors elsewhere in the filter."),
    ("What does the Python blocked-filter example demonstrate about CPU caches?", ["Its layout groups probes but makes no measured hardware claim", "It proves one cache miss per query", "It guarantees faster queries than all Bloom layouts"], "A Python integer mask models local bit placement; hardware cache behavior requires a separate implementation and measurement."),
    ("Why is the alternate cuckoo bucket reversible?", ["XOR with the same fingerprint offset returns the original bucket", "Every relocation computes a new random bucket", "The fingerprint contains the entire original key"], "The alternate index is the current index XOR a stable fingerprint-derived offset, and applying that offset twice restores the first index."),
    ("What happens when bounded cuckoo relocation fails?", ["Recorded slot changes are restored and add returns false", "The last displaced fingerprint is silently lost", "All buckets are cleared"], "Rolling back the changed slots preserves every previously accepted fingerprint when no free bucket is found within the kick limit."),
    ("Why is fingerprint-only deletion absent here?", ["A matched fingerprint may represent another key", "Fingerprints cannot be moved between buckets", "The table can never contain a collision"], "Compact fingerprints lose full key identity, so deleting a merely matched position can invalidate a different inserted key under collisions."),
]
balanced = []
for number, (prompt, options, explanation) in enumerate(questions):
    distractors = options[1:]
    position = number % 3
    distractors.insert(position, options[0])
    balanced.append({"prompt": prompt, "options": distractors, "answer": position, "explanation": explanation})
quiz = copy.deepcopy(by_path["quizzes/dsa-heavy-hitter-distinct-sample-contracts"])
quiz.update(id=str(uuid.uuid5(uuid.NAMESPACE_URL, "aitrove:" + quiz_path)), path=quiz_path,
            title="Approximate membership under mutation", summary="Test balanced deletion, generation growth, blocked probes, and fingerprint rollback.",
            sort_order=42750, created_at=stamp, updated_at=stamp, published_at=stamp)
quiz["data"].update(duration_minutes=20, related=[{"path": path, "title": by_path[path]["title"]} for path in new_paths + [project_path]], questions=balanced)
quiz["body"] = "<p>Check the state each approximate-membership design retains, the answer it can support, and the mutation that can break its contract.</p><h2>Lessons</h2>" + links(new_paths) + "<h2>Design exercise</h2>" + links([project_path, subject_root])
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
    ("dsa/bloom-filter-membership-boundary", new_paths[0]),
    ("dsa/bloom-filter-membership-boundary", new_paths[1]),
    ("dsa/bloom-filter-membership-boundary", new_paths[2]),
    ("dsa/cuckoo-hashing-relocation-rebuild", new_paths[3]),
    ("dsa/lsm-sorted-runs-tombstone-compaction", new_paths[1]),
    ("dsa/hash-map-collision-and-load-contract", new_paths[2]),
):
    old = by_path[old_path]
    old["body"] += '<p><a href="/' + new_path + '">' + html.escape(by_path[new_path]["title"]) + "</a> extends the membership design choices.</p>"
    old["updated_at"] = stamp
for path in new_paths:
    entry = by_path[path]
    peers = [other for other in new_paths if other != path]
    entry["body"] += '<p>Compare its mutation contract with ' + ", ".join('<a href="/' + other + '">' + html.escape(by_path[other]["title"]) + "</a>" for other in peers) + ', then run the <a href="/' + project_path + '">membership audit</a> and <a href="/' + quiz_path + '">contract quiz</a>.</p>'
    entry["updated_at"] = stamp

fixture.write_text(json.dumps(entries, ensure_ascii=False, indent=2) + "\n")
print(json.dumps({"lessons": new_paths, "project": project_path, "quiz": quiz_path, "questions": len(questions)}))
