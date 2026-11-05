"""Add four allocation-structure lessons and their connected review material."""

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
    dict(path="dsa/checkpoint-bump-arena-lifetime", program="checkpoint_bump_arena.py",
         template="dsa/resizable-array-growth-and-insert-cost", section="dsa/array-data-structure-guide",
         title="Checkpoint arenas: reclaim a region by lifetime",
         summary="Allocate aligned byte spans and roll back a whole group at one checkpoint.",
         definition="A bump arena reserves one byte region and advances a cursor for each allocation. Alignment may leave padding before a span, so the next address is the aligned cursor, not necessarily the old cursor itself. A checkpoint captures both the cursor and the next handle number. Rewinding restores the cursor and invalidates handles allocated after that checkpoint. Earlier handles stay valid because their spans lie before the saved cursor. This model zeroes every newly allocated span, including space reused after a rewind, and uses monotonically increasing handle numbers so an old handle cannot accidentally name a replacement span. The region has a fixed capacity; an allocation that does not fit raises an error without changing state. There is no individual free operation. The useful lifetime is a request, parse, or batch whose objects can all be discarded together.",
         case="A pump inspection stores the seven-byte tag PUMP-47 at an aligned offset. The service begins a checkpoint, reserves twelve bytes for a temporary report, then abandons that report. Rewinding releases the whole temporary tail in one step. A new twelve-byte reservation may begin at the same byte offset, while the original tag remains readable through its earlier handle and the abandoned handle is rejected. Writing a shorter payload into a reused allocation would otherwise leave old bytes visible in the unread tail, so the model clears the full span before returning it. Alignment padding counts against capacity even though the caller did not request those bytes.",
         cost="For an arena of capacity C and alignment A, an allocation computes its aligned offset and clears S allocated bytes, taking O(S) time because this teaching model promises zeroed bytes. Without zeroing, cursor placement itself is O(1). A read or write of S bytes costs O(S). Marking is O(1). Rewind scans the active-handle dictionary to discard later handles, so it costs O(H) time for H active handles; a lower-level arena could instead use a stack of allocation records. The byte region takes O(C) space, and Python handle records take O(H) additional space. Reset invalidates all handles but retains the reserved region for reuse.",
         mistakes=["Do not treat alignment padding as usable payload bytes.", "Do not reuse handle numbers after rewind or reset while stale handles may survive.", "Do not read uninitialized tails after reusing a span; this model clears them.", "Do not promise individual object release from an arena that only rewinds a tail."],
         related=["dsa/resizable-array-growth-and-insert-cost", "dsa/immutable-index-snapshot-publication", "dsa/generational-slot-map-stale-handle-rejection"]),
    dict(path="dsa/first-fit-free-span-coalescing", program="first_fit_span_free_list.py",
         template="dsa/resizable-array-growth-and-insert-cost", section="dsa/array-data-structure-guide",
         title="Free spans: first-fit allocation and adjacent coalescing",
         summary="Track arbitrary released regions and join neighbors into reusable space.",
         definition="A free-span list stores the unallocated intervals of one fixed address range. The first-fit policy scans spans in increasing start-address order and takes the first interval long enough for a request. A partial fit advances that free span's start; an exact fit removes the span. The allocated map records the size associated with each returned start address, so release does not trust a caller-supplied length. On release, the interval returns to the free list, the list is sorted, and adjacent intervals are joined. Coalescing matters: two released neighbors can satisfy one larger request only when the allocator recognizes that their union is contiguous. This is an address-management model, not an operating-system allocator; it does not move live allocations or return memory to a host process.",
         case="A 64-unit maintenance buffer first reserves 13 units for a pump record and 19 for a valve record. Releasing both creates two adjacent intervals; coalescing turns them into one span from zero through 31. A later 24-unit service record starts at zero, leaving a free tail from 24 through 63. Total free units are 40. If the two earlier records remained separate, neither isolated interval could fit the 24-unit request despite their combined capacity. Conversely, enough total free units do not guarantee success when live allocations divide them into small nonadjacent holes. An unknown start address is rejected rather than freeing somebody else's span.",
         cost="Let F be the number of free spans. First-fit allocation scans at most F spans and may shift a Python list when one is removed, so it costs O(F) time. Release appends, sorts, and merges F plus one spans, costing O(F log F) time and O(F) temporary list space. The allocated map gives expected O(1) ownership lookup, with O(L) records for L live allocations. Capacity accounting uses O(F) time by summing lengths. A balanced interval tree or size-indexed bins could change search costs, but each also adds metadata and different fragmentation tradeoffs. First fit does not compact occupied intervals or guarantee that a suitable contiguous block exists.",
         mistakes=["Do not equate total free space with the largest available contiguous span.", "Do not merge intervals across a live allocation.", "Do not accept a release size supplied by a caller when the allocator has the ownership record.", "Do not claim constant-time release for this sorting implementation."],
         related=["dsa/checkpoint-bump-arena-lifetime", "dsa/resizable-array-growth-and-insert-cost", "dsa/sparse-set-bounded-identifiers"]),
    dict(path="dsa/buddy-power-of-two-block-coalescing", program="power_of_two_buddy_blocks.py",
         template="dsa/avl-interval-index-insertion", section="dsa/trees-and-heaps",
         title="Buddy blocks: split powers of two and reunite partners",
         summary="Round a request to a block order and merge only its exact free buddy.",
         definition="A buddy pool covers a power-of-two capacity with one free root block. A request rounds up to the smallest power-of-two block that can hold it. When no block of that order is free, the allocator takes a larger block and repeatedly splits it into equal halves, returning one half to the free set at each level. The partner of a block beginning at an aligned address is found by toggling the bit for that block size. Release can merge two halves only when both are free and are true partners at the same order; two merely adjacent blocks of unequal size cannot be combined by that rule. The allocated map records both block order and requested size. This model stores sets of integer offsets and does not reserve or copy the actual payload bytes.",
         case="A 128-unit pool serves a 13-unit pump request with a 16-unit block and a 19-unit valve request with a 32-unit block. The gap between requested and assigned capacity is internal fragmentation, not a leak. When the pump and valve blocks are released, each climbs the hierarchy only while its matching free buddy is present. Eventually the free root at offset zero covers all 128 units again. Releasing an unknown offset fails because no live allocation owns it. The example deliberately chooses the lowest free start at a found order for repeatable output; another tie rule could place the same requests differently without changing the buddy invariant.",
         cost="Let C be the capacity and F the number of free blocks at the selected order. Searching orders and splitting cost O(log C), while choosing the minimum from a Python set costs O(F); allocation here is therefore O(F + log C), not guaranteed logarithmic. Release probes at most log C buddy sets, giving expected O(log C) time with hash-set membership. The free sets and ownership map use O(C) metadata in the worst case of unit blocks, in addition to any payload store a real allocator would require. Power-of-two rounding can waste nearly half a selected block for a request just above the previous order. This model does not provide physical pages, locking, or operating-system reclamation.",
         mistakes=["Do not merge blocks merely because their addresses touch; both must be free buddies of one order.", "Do not report requested bytes as the amount of block capacity held.", "Do not assume min over a Python set is constant time.", "Do not allow a non-power-of-two root capacity without a different covering scheme."],
         related=["dsa/first-fit-free-span-coalescing", "dsa/avl-interval-index-insertion", "dsa/packed-r-tree-rectangle-intersection"]),
    dict(path="dsa/generational-slab-slot-cache", program="generational_slab_cache.py",
         template="dsa/generational-slot-map-stale-handle-rejection", section="dsa/hash-tables",
         title="Slab slots: reuse fixed-size pages with generation checks",
         summary="Serve same-shaped records from page slots while rejecting stale handles.",
         definition="A slab cache divides each page into a fixed number of equal-shaped object slots. Its free-slot stack stores page and slot coordinates. Allocation pops one coordinate, writes the incident record, marks it live, and returns a handle containing page, slot, and generation. If the stack is empty, the cache adds one page and its slots. Release clears the value, increments that slot's generation, and pushes its coordinate for reuse. A stale handle cannot read a replacement record at the same coordinate because its generation no longer matches. This is a same-shaped in-memory object model; it does not account for byte alignment, page headers, physical page allocation, or object finalizers. Pages stay allocated even when every slot becomes free.",
         case="With three slots per page, four incident records force a second page. The handle for incident 19 is released, then incident 29 takes the freed coordinate. The replacement's page and slot match the old handle, but its generation differs, so reading through the old handle raises an error. A direct page/slot pointer without a generation field would expose the new record under the old identity. The model also rejects a second release of the old handle. It does not shrink the cache when activity falls; retaining empty pages makes reuse cheap, but can keep memory committed after a brief peak.",
         cost="Popping or returning one free slot and checking a generation use expected O(1) time under Python set membership. Adding a page initializes S slots and therefore costs O(S) time and O(S) space for S slots per page. For P pages, value slots, generation cells, and free coordinates together use O(P times S) space; live ownership adds O(L) entries for L active records. Lookup is expected O(1). A page is not moved or compacted, and this example has no concurrent access protection. If a generation counter eventually wraps in a fixed-width implementation, old handles could become valid again; Python integers in this model do not wrap automatically.",
         mistakes=["Do not identify a record solely by page and slot after that slot is reused.", "Do not decrement a generation on release; monotone generations reject old handles.", "Do not claim that empty pages are returned to the system in this model.", "Do not apply fixed-size slot cost claims to arbitrary-sized objects."],
         related=["dsa/generational-slot-map-stale-handle-rejection", "dsa/sparse-set-bounded-identifiers", "dsa/checkpoint-bump-arena-lifetime"]),
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
                 sort_order=43200 + order * 10, created_at=stamp, updated_at=stamp, published_at=stamp)
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
project_path = "dsa/allocation-ownership-coalescing-audit-project"
quiz_path = "quizzes/dsa-arena-free-buddy-slab-contracts"
assert project_path not in by_path and quiz_path not in by_path
project = copy.deepcopy(by_path["dsa/editable-sequence-tradeoff-audit-project"])
project.update(id=str(uuid.uuid5(uuid.NAMESPACE_URL, "aitrove:" + project_path)), path=project_path,
               title="Project: audit four reusable storage contracts", summary="Check scope reclamation, arbitrary free spans, buddy merges, and stale slots.",
               sort_order=43240, created_at=stamp, updated_at=stamp, published_at=stamp)
project["data"].update(reading_minutes=30, related=[{"path": path, "title": by_path[path]["title"]} for path in new_paths])
project["body"] = (
    "<p>A maintenance service needs temporary parse bytes, variable-sized report buffers, power-of-two page units, and fixed-shape incident records. Assign one structure to each workload and write down who owns a live allocation. Build a small reference ledger with occupied intervals for the first three structures and live coordinate-generation pairs for the slab cache. After each operation, compare coverage, overlap, free capacity, and stale-handle behavior against that ledger. Treat a failed allocation as a state-preserving event. Account for padding and rounded blocks separately from requested payload sizes.</p>"
    "<h2>Acceptance trace</h2><p>Write PUMP-47 before an arena checkpoint, reserve a temporary twelve-byte span, rewind, and verify the earlier tag survives while the old temporary handle fails. In a 64-unit first-fit pool, allocate 13 and 19, release both, and allocate 24 at start zero with 40 units free. In a 128-unit buddy pool, allocate 13 and 19, release both, and recover one free root block. In a three-slot slab, allocate four incidents, reuse one released coordinate, and reject its old generation.</p>"
    '<h3>Expected review record</h3><pre><code class="language-text">arena-stable=PUMP-47\nfirst-fit-start=0\nbuddy-root=128\nslab-stale=True</code></pre>'
    "<h2>Boundary and cost review</h2><p>Try an arena allocation that exceeds remaining aligned capacity and ensure the cursor does not move. Exercise a free pool with enough total free units but no contiguous fit. For every buddy release, verify that only a true same-order partner merges, and that the final free and allocated blocks cover the root exactly. Fill two slab pages, release one handle twice, then allocate into its old coordinate and prove the first handle stays invalid. Explain why zeroing changes the arena allocation cost, why sorting changes free-list release cost, and why min over a set affects this buddy implementation.</p>"
    "<h3>Common Mistakes</h3><ul><li>Do not confuse a reused address with a reused object identity.</li><li>Do not count adjacent live space as a free interval.</li><li>Do not merge unequal buddy orders.</li><li>Do not infer that an empty slab page has been returned to the host.</li></ul>"
    "<h2>Connected lessons</h2>" + links(new_paths + ["dsa/projects", "dsa/quizzes", subject_root])
)
entries.append(project)
by_path[project_path] = project

questions = [
    ("What does an arena checkpoint preserve?", ["A cursor and the boundary between earlier and later handles", "Every released object in a global free list", "One buddy set for each block order"], "The checkpoint records the cursor and next handle number, allowing a rewind to retain earlier spans while invalidating later handles."),
    ("Why does the arena clear a reused span?", ["To prevent old bytes from appearing in an unwritten tail", "To make alignment padding available", "To allow individual object release"], "A shorter new write could otherwise leave stale bytes visible when the caller reads the whole allocation after a rewind."),
    ("What happens when an aligned arena request exceeds capacity?", ["It raises without changing the allocation cursor", "It wraps to address zero and overwrites live data", "It silently drops alignment"], "The fit check runs before the handle and cursor are advanced, so a rejected request preserves the existing allocation state."),
    ("Which free span does first fit choose?", ["The first address-ordered span large enough for the request", "The smallest span regardless of scan order", "The newest released span even if it is too short"], "The implementation scans its sorted free spans from low addresses and takes the first interval with enough contiguous units."),
    ("Why merge adjacent released spans?", ["Their union may satisfy a request that neither isolated span can hold", "It moves all live allocations to address zero", "It removes the need for an ownership map"], "Coalescing restores a larger contiguous interval while leaving intervening live allocations untouched and separately owned."),
    ("Can total free units alone prove that a request fits?", ["No; live intervals can split free capacity into small holes", "Yes; first fit compacts all records automatically", "Yes; every free span always begins at zero"], "A request needs one contiguous interval at least as large as its size, even when the sum of smaller holes is greater."),
    ("How large a block serves a buddy request of 19 units?", ["32 units", "19 units exactly", "16 units"], "Buddy blocks have power-of-two sizes, so the smallest order that can contain nineteen units has thirty-two units of capacity."),
    ("When may two buddy blocks merge?", ["When both are free, share one order, and are exact partners", "Whenever their requested payload sizes match", "Whenever their starts are numerically adjacent"], "The partner is computed by toggling the size bit, and only that same-order free buddy can form the next larger aligned block."),
    ("Why is buddy allocation here not guaranteed O(log C)?", ["Choosing min from a Python set can scan free blocks", "The pool copies every payload byte", "Generation validation walks every slab page"], "Order search and splitting follow logarithmic levels, but selecting the lowest free offset from a set adds a scan over that set."),
    ("What does a slab handle carry beyond a page and slot?", ["A generation value", "The size of every free interval", "The entire page contents"], "The generation changes when a slot is released, so an old handle cannot read an unrelated record later stored at the same coordinate."),
    ("What happens when the slab free-slot stack is empty?", ["A new fixed-slot page is initialized", "An active incident is overwritten", "All generations are reset to zero"], "The cache grows by one page and pushes that page's slots before serving the waiting allocation from a free coordinate."),
    ("Does releasing the last object on a slab page return the page?", ["No; this model retains its pages for later reuse", "Yes; release always shrinks the page array", "Only if the object has a larger generation"], "Release clears one slot and returns it to the stack, but no page removal or compaction operation exists in this teaching model."),
]
balanced = []
for number, (prompt, options, explanation) in enumerate(questions):
    distractors = options[1:]
    position = number % 3
    distractors.insert(position, options[0])
    balanced.append({"prompt": prompt, "options": distractors, "answer": position, "explanation": explanation})
quiz = copy.deepcopy(by_path["quizzes/dsa-gap-rope-block-sequence-contracts"])
quiz.update(id=str(uuid.uuid5(uuid.NAMESPACE_URL, "aitrove:" + quiz_path)), path=quiz_path,
            title="Arenas, free spans, buddies, and slab slots", summary="Check lifetime, contiguous fit, merge rules, and stale-handle rejection.",
            sort_order=43250, created_at=stamp, updated_at=stamp, published_at=stamp)
quiz["data"].update(duration_minutes=20, related=[{"path": path, "title": by_path[path]["title"]} for path in new_paths + [project_path]], questions=balanced)
quiz["body"] = "<p>Check each storage structure against its ownership and reuse contract. Separate requested payload, reserved capacity, and generation-based object identity.</p><h2>Lessons</h2>" + links(new_paths) + "<h2>Design exercise</h2>" + links([project_path, subject_root])
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
    ("dsa/resizable-array-growth-and-insert-cost", new_paths[0]),
    ("dsa/generational-slot-map-stale-handle-rejection", new_paths[0]),
    ("dsa/sparse-set-bounded-identifiers", new_paths[1]),
    ("dsa/avl-interval-index-insertion", new_paths[2]),
    ("dsa/generational-slot-map-stale-handle-rejection", new_paths[3]),
    ("dsa/sparse-set-bounded-identifiers", new_paths[3]),
):
    old = by_path[old_path]
    old["body"] += '<p><a href="/' + new_path + '">' + html.escape(by_path[new_path]["title"]) + "</a> extends the storage ownership comparison.</p>"
    old["updated_at"] = stamp
for path in new_paths:
    entry = by_path[path]
    peers = [other for other in new_paths if other != path]
    entry["body"] += '<p>Compare ownership and reuse with ' + ", ".join('<a href="/' + other + '">' + html.escape(by_path[other]["title"]) + "</a>" for other in peers) + ', then run the <a href="/' + project_path + '">storage audit</a> and <a href="/' + quiz_path + '">contract quiz</a>.</p>'
    entry["updated_at"] = stamp

fixture.write_text(json.dumps(entries, ensure_ascii=False, indent=2) + "\n")
print(json.dumps({"lessons": new_paths, "project": project_path, "quiz": quiz_path, "questions": len(questions)}))
