"""Add range corrections, authenticated hash proofs, and running medians."""

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
        path="dsa/fenwick-two-tree-range-add-sum",
        program="range_add_fenwick.py",
        title="Two Fenwick trees: add across ranges and query sums",
        summary="Track a difference sequence and its weighted prefix for logarithmic range work.",
        section="dsa/range-query-structures",
        definition="A point-update Fenwick tree cannot add a value to an entire range and then sum arbitrary ranges with the same formula. The two-tree variant stores a difference sequence in one Fenwick array and each difference multiplied by its zero-based position in another. For a prefix ending before position S, the element total is S times the first difference prefix minus the weighted difference prefix. A half-open update [start, stop) adds a difference at start and subtracts it at stop, when stop is inside the array. A range sum subtracts two prefixes. Empty intervals are valid and contribute zero. The public API uses zero-based positions and half-open stops throughout.",
        case="Start with five depot capacities 23, 47, 19, 61, and 38. Add seven to positions [1, 4), then subtract four from [3, 5). The final values are 23, 54, 26, 64, and 34. Sum [1, 5) and get 178; sum [3, 4) and get 64. The second update overlaps the first at position three, and subtracts from position four without changing position two. A right boundary is excluded, so a correction to [1, 4) never touches the value at index four. Bounds are checked before any mutation to avoid partially applying an invalid request.",
        cost="Let N be the fixed array length. Each range addition makes at most four Fenwick point updates and costs O(log N) time, while each prefix or range sum costs O(log N) time. Two Fenwick arrays use O(N) memory. This program builds from initial values with N one-position updates, costing O(N log N); a specialized direct build could be faster. Values can be negative because the structure stores arithmetic totals, not a monotone count. Fixed-width languages need an accumulator wide enough for S times a difference and the total. A static prefix array is simpler for query-only data, while a lazy segment tree supports other aggregate and update combinations that this pair of additive trees cannot express directly.",
        mistakes=["Do not omit the weighted difference tree when asking for range sums.", "Do not update the stop boundary when stop equals the array length.", "Do not mix inclusive and half-open range endpoints.", "Do not reuse this additive formula for assignment or minimum queries."],
        related=["dsa/fenwick-tree-point-update-prefix-query", "dsa/lazy-segment-tree-range-add-minimum", "dsa/prefix-sum-range-query-contract"],
    ),
    dict(
        path="dsa/merkle-tree-indexed-inclusion-proof",
        program="merkle_scan_proof.py",
        title="Merkle trees: verify an indexed scan record",
        summary="Hash ordered leaves and sibling paths against a separately trusted batch root.",
        section="dsa/trees-and-heaps",
        definition="A binary hash tree summarizes an ordered batch in one root digest. This implementation hashes each record with a leaf prefix and each pair of child digests with a different branch prefix. Those prefixes keep a record byte string separate from a serialized branch. For an odd node count, the last node advances unchanged to the next level. A third prefix commits the batch size together with the tree digest in the final root. A proof carries only sibling digests on the record's path and marks whether each sibling is left or right. Verification reconstructs the path using the claimed index and size, rejects a missing or extra sibling, and compares the size-bound result with a trusted root. The root must arrive through a trusted channel; a proof cannot authenticate itself.",
        case="A scan batch contains five byte records, including D-61:19 at index three. Its inclusion proof has three siblings under the chosen odd-node rule. With the batch's trusted root and size, the original record verifies true; changing it to D-61:20 verifies false. The record order, index, tree shape, byte encoding, and hash prefix rules are all part of the protocol. Two identical payloads at different positions are distinct occurrences for this proof. A caller who accepts an attacker-supplied root alongside an attacker-supplied proof learns only that they agree with each other, not that the scan belongs to an approved batch.",
        cost="For N records containing B total input bytes, building all levels hashes O(B + N) bytes at fixed digest length and stores O(N) digests. A proof has O(log N) siblings and takes O(log N) time to extract from the stored levels. Verification hashes the submitted record, O(log N) fixed-size pairs, and one size-bound root, using O(log N) proof space and O(1) extra working space. This immutable batch rebuilds after any record change; it does not provide append consistency proofs, signatures, timestamps, or collision resistance beyond the chosen digest algorithm's assumptions. The root encoding here is this lesson's protocol, and its trusted delivery matters more than the short path's speed.",
        mistakes=["Do not accept an untrusted root and call the proof authenticated.", "Do not swap sibling order when recomputing a parent digest.", "Do not omit index and batch-size checks for an odd-shaped tree.", "Do not hash leaves and branches under the same undifferentiated byte format."],
        related=["dsa/framed-journal-torn-tail-recovery", "dsa/immutable-index-snapshot-publication", "dsa/persistent-segment-tree-versioned-sums"],
    ),
    dict(
        path="dsa/two-heap-running-median",
        program="running_median_service.py",
        title="Two heaps: maintain an exact running median",
        summary="Balance a lower max-heap and upper min-heap for append-only measurements.",
        section="dsa/trees-and-heaps",
        definition="An append-only median index divides recorded integers into a lower half and an upper half. The lower half is a max-heap, represented here by negated integers in Python's min-heap; the upper half is an ordinary min-heap. Every lower value must be no greater than every upper value, and the lower heap has either the same number of entries or one extra. The top of the lower heap is the median for odd counts. For even counts, the mean of both heap tops is returned as an exact rational number, avoiding a rounded floating-point answer. A call before the first record raises. This API does not remove or revise old observations.",
        case="Record scan counts 47, 19, 61, 26, and 83. The sorted order is 19, 26, 47, 61, 83, so the current median is 47. Record 52; now the middle two are 47 and 52, and the exact median is 99/2. Both heap sizes differ by at most one after each append. A burst of high values can move an upper-heap root into the lower heap, but it cannot make the lower top exceed the upper top when insertion and rebalancing preserve their partition. A sliding-window median would need an explicit deletion strategy; simply dropping an old count from a side list does not remove its heap entry.",
        cost="Each append makes one heap insertion and at most one transfer, taking O(log N) time for N recorded values. Reading the two roots takes O(1) heap operations; constructing an exact rational has arithmetic cost tied to integer bit length. The heaps retain all N values, using O(N) space. Sorting all values after each append would cost O(N log N) per query; a sorted array would make inserts O(N) due shifting. These heaps are a good fit when the stream only grows. They are not a bounded-memory window and they do not support arbitrary removal or timestamp expiration in this example.",
        mistakes=["Do not average two roots when the count is odd.", "Do not let one heap grow two entries larger than the other.", "Do not use floating-point division when an exact even-count median is required.", "Do not describe this append-only index as a sliding-window median."],
        related=["dsa/binary-heap-priority-scheduling", "dsa/indexed-binary-heap-decrease-key", "python/running-median-heaps"],
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
                 sort_order=42100 + order * 10, created_at=stamp, updated_at=stamp, published_at=stamp)
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
project_path = "dsa/scan-batch-capacity-median-integrity-project"
quiz_path = "quizzes/dsa-range-proof-median-contracts"
assert project_path not in by_path and quiz_path not in by_path
project = copy.deepcopy(by_path["dsa/asset-spatial-fingerprint-audit-project"])
project.update(id=str(uuid.uuid5(uuid.NAMESPACE_URL, "aitrove:" + project_path)), path=project_path,
               title="Project: audit capacity, medians, and scan integrity",
               summary="Compare range corrections, stream medians, and inclusion proofs with plain reference checks.",
               sort_order=42140, created_at=stamp, updated_at=stamp, published_at=stamp)
project["data"].update(reading_minutes=25, related=[{"path": path, "title": by_path[path]["title"]} for path in new_paths])
project["body"] = (
    "<p>A depot console accepts capacity corrections across days, appends scan counts, and seals a batch of raw scan records. Use three independent checks. An ordinary list receives every range correction and supplies sums by slicing. A sorted copy of all recorded counts supplies the exact median after each append. A freshly built hash tree checks that a proof belongs to a separately retained root and batch size. These checks should run after mixed operations, including empty ranges, negative corrections, duplicate counts, and an odd batch length. The structures solve different problems: arithmetic changes to a fixed array, order statistics over an append-only stream, and evidence that a byte record occupied one position in one committed batch. Sharing a dashboard does not make their update rules interchangeable.</p>"
    "<h2>Acceptance trace</h2><p>Initialize capacities 23, 47, 19, 61, 38. Add seven over [1, 4), subtract four over [3, 5), and require 178 for [1, 5). Record scan counts 47, 19, 61, 26, 83, then 52: the two medians are 47 and 99/2. Seal five byte records with D-61:19 at index three. The original record verifies against the stored root; D-61:20 must fail against the same root. Replacing a capacity value is not the same as adding a difference. Editing a sealed record changes its leaf digest and requires a new root.</p>"
    '<h3>Expected output</h3><pre><code class="language-text">range-sum=178 median-five=47 median-six=99/2\noriginal-proof=true altered-proof=false</code></pre>'
    "<h2>Boundary and cost review</h2><p>Validate each half-open range before changing either Fenwick tree. Check the heap-size and ordering invariants after each count; an empty stream has no median. Reject a proof with missing or extra siblings, a wrong position, or a wrong batch size. The batch root and size need an authenticated source. A rebuilt hash tree is not an append-consistency protocol, and the example's median heaps do not evict expired readings. State whether reports use raw integer counts or another numeric unit before computing an exact fraction.</p>"
    "<h3>Common Mistakes</h3><ul><li>Do not mistake a range addition for assignment.</li><li>Do not average heap tops after an odd number of records.</li><li>Do not accept a proof against a root supplied by the same untrusted party.</li><li>Do not leave the batch size out of an odd-node proof check.</li></ul>"
    "<h2>Connected lessons</h2>" + links(new_paths + ["dsa/projects", "dsa/quizzes", subject_root])
)
entries.append(project)
by_path[project_path] = project

questions = [
    ("What does the first Fenwick tree store in the two-tree range-add design?", ["Differences at update boundaries", "Current values in sorted order", "Minimums of child intervals"], "Boundary differences let one range addition change only its start and stop contributions in the first Fenwick tree."),
    ("Why is the second Fenwick tree needed?", ["It stores position-weighted differences for prefix totals", "It stores hashes of updated ranges", "It records the array's maximum"], "A prefix of the underlying values weights each boundary difference by how many positions follow it, which requires a second weighted summary."),
    ("What happens when an update ends exactly at the array length?", ["No stop-boundary Fenwick update is needed", "The last element is updated twice", "The request is invalid"], "The half-open stop sits beyond all stored positions, so there is no later value whose difference must be reversed."),
    ("What is the update cost for this fixed-size two-tree index?", ["O(log N)", "O(N) because every covered value is visited", "O(1) for arbitrary assignments"], "A range addition changes a constant number of Fenwick boundary entries, and each entry update climbs logarithmically."),
    ("What makes a Merkle inclusion root meaningful?", ["The verifier already trusts that root and batch size", "The prover includes the root beside the proof", "The proof contains at least one sibling"], "An attacker can construct a matching root and path for arbitrary data; the expected root and batch size need a separate trusted origin."),
    ("Why are leaf and branch hashes prefixed differently?", ["To separate record bytes from serialized child-digest pairs", "To shorten every digest", "To sort scan records alphabetically"], "Different input domains stop a record byte sequence from being treated as the same kind of object as a branch's encoded children."),
    ("What does the verifier do when an odd node has no sibling at one level?", ["Carry its digest upward unchanged under this tree rule", "Invent a zero-valued sibling", "Reverse the digest's bytes"], "This tree promotes an unpaired final digest, and both proof creation and verification must apply exactly that same shape rule."),
    ("What must happen to a proof with an extra sibling after reaching the root?", ["Reject it", "Ignore the extra sibling", "Append it to the payload"], "The proof must match the exact path implied by position and size; accepting trailing data weakens the path-format contract."),
    ("Which heap holds the lower half of scan counts?", ["A max-heap represented by negated values", "An ordinary min-heap of the largest values", "A FIFO queue"], "The lower half needs quick access to its largest member, so negating values lets Python's min-heap supply that boundary."),
    ("How does the exact even-count median use heap roots?", ["The rational mean of the lower maximum and upper minimum", "The lower maximum alone", "The average of every stored value"], "The two middle sorted values sit at the heap roots, and an exact fraction retains a half-unit result without rounding."),
    ("How much work does one append take in the two-heap index?", ["O(log N) heap work", "O(1) worst-case work for every heap move", "O(N log N) because it sorts all observations"], "One insertion and at most one root transfer use heap operations whose cost grows logarithmically with recorded count."),
    ("Which operation is missing from this median implementation?", ["Deleting an expired observation", "Adding a negative count", "Reading an even-count median"], "The heaps retain every inserted value; a sliding window needs a separate deletion or expiration design to remove old entries."),
]
balanced = []
for number, (prompt, options, explanation) in enumerate(questions):
    correct = options[0]
    distractors = options[1:]
    position = number % 3
    distractors.insert(position, correct)
    balanced.append({"prompt": prompt, "options": distractors, "answer": position, "explanation": explanation})
quiz = copy.deepcopy(by_path["quizzes/dsa-cuckoo-spatial-bit-trie-contracts"])
quiz.update(id=str(uuid.uuid5(uuid.NAMESPACE_URL, "aitrove:" + quiz_path)), path=quiz_path,
            title="Range corrections, hash proofs, and median heaps",
            summary="Check boundary differences, trusted roots, and exact middle values.",
            sort_order=42150, created_at=stamp, updated_at=stamp, published_at=stamp)
quiz["data"].update(duration_minutes=20, related=[{"path": path, "title": by_path[path]["title"]} for path in new_paths + [project_path]], questions=balanced)
quiz["body"] = "<p>Check the operation boundary before the asymptotic claim. Range additions touch two differences, inclusion proofs need a trusted root, and append-only heaps keep every count.</p><h2>Lessons</h2>" + links(new_paths) + "<h2>Design exercise</h2>" + links([project_path, subject_root])
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
    ("dsa/fenwick-tree-point-update-prefix-query", new_paths[0]),
    ("dsa/lazy-segment-tree-range-add-minimum", new_paths[0]),
    ("dsa/framed-journal-torn-tail-recovery", new_paths[1]),
    ("dsa/immutable-index-snapshot-publication", new_paths[1]),
    ("dsa/binary-heap-priority-scheduling", new_paths[2]),
    ("python/running-median-heaps", new_paths[2]),
):
    old = by_path[old_path]
    old["body"] += '<p><a href="/' + new_path + '">' + html.escape(by_path[new_path]["title"]) + "</a> adds a related operation contract.</p>"
    old["updated_at"] = stamp
for path in new_paths:
    entry = by_path[path]
    entry["body"] += '<p>Apply the invariant in the <a href="/' + project_path + '">scan batch audit project</a>, then check the <a href="/' + quiz_path + '">operations quiz</a>.</p>'
    entry["updated_at"] = stamp

fixture.write_text(json.dumps(entries, ensure_ascii=False, indent=2) + "\n")
print(json.dumps({"lessons": new_paths, "project": project_path, "quiz": quiz_path, "questions": len(questions)}))
