"""Add editable text and block-based sequence data structure lessons."""

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
    dict(path="dsa/gap-buffer-cursor-local-edits", program="gap_buffer_incident_note.py",
         template="dsa/piece-table-text-editing", section="dsa/array-data-structure-guide",
         title="Gap buffers: pay when the edit cursor crosses text",
         summary="Keep one spare interval at the cursor; distinguish local edits from long cursor moves.",
         definition="A gap buffer is one character array with an unused interval between the text before and after the cursor. Its two gap boundaries encode the cursor position; no sentinel character is part of the note. Moving the cursor copies characters across the gap, while insertion consumes spare slots and deletion expands the gap. This implementation always leaves at least one spare slot when an insertion exactly fills the current interval, so a later cursor move still has room to shift a character. When the gap needs more room, it adds spare slots in one allocation. The array contains Python characters, so offsets count Unicode code points rather than user-perceived grapheme clusters. The model has no undo, markers, line index, or concurrent editor state.",
         case="An incident operator starts with the note Valve offline, inserts the equipment number after Valve, appends a bay location, and finally prepends Alert:. Those edits require a short cursor move, an append, then a move back across nearly the whole note. The output is Alert: Valve-19 offline at bay 6. Typing several characters at one cursor is cheap until the gap grows. Jumping from the end of a large note to its start moves existing characters, so measuring only insertion after the move hides the expensive part of this workload. The text() call materializes a contiguous string for display and also copies the full logical note.",
         cost="Moving the cursor by D character positions costs O(D) time and O(1) extra space when the gap has room. Inserting M characters at the current cursor costs O(M) plus an occasional O(N) growth copy; geometric spare growth gives amortized linear cost across local insertions, but does not make distant cursor moves cheap. Forward deletion and backspace cost O(K) here because the code clears K slots; logical deletion could change a boundary without clearing them. Materializing N characters costs O(N) time and space. The allocated array is O(N + G) for note length N and spare gap G. A one-character insertion after a full-buffer cursor jump can still take O(N).",
         mistakes=["Do not display the unused gap as note content.", "Do not move a zero-width gap without first making spare space.", "Do not claim a distant cursor jump is constant time.", "Do not use code-point offsets as grapheme-aware cursor positions."],
         related=["dsa/piece-table-text-editing", "dsa/resizable-array-growth-and-insert-cost", "dsa/doubly-linked-list-relink-and-ownership"]),
    dict(path="dsa/immutable-rope-text-snapshots", program="immutable_rope_note.py",
         template="dsa/piece-table-text-editing", section="dsa/trees-and-heaps",
         title="Ropes: share text chunks across immutable revisions",
         summary="Store character counts in a binary chunk tree and retain older note roots after edits.",
         definition="A rope stores text in leaf chunks and stores the length of the left subtree at each internal node. An indexed lookup compares its offset with that left weight and descends to one leaf. Split divides a tree at an offset; joining the resulting parts with new nodes makes an edited root while unchanged subtrees remain shared with earlier roots. The example constructs a roughly balanced initial tree from short chunks, then implements insert and delete by split and join. It deliberately does not rebalance after edits. That omission matters: a run of joins can make the height proportional to the number of edits, and recursive split can eventually exhaust Python's call stack. The structure stores code-point lengths, not byte lengths or display columns.",
         case="A saved maintenance note says Pump offline at bay 6. A revised root inserts the equipment number after Pump and removes offline, producing Pump-47 at bay 6. The saved root still renders the earlier wording because no leaf or internal node is changed in place. For a review tool that compares prior and current notes, retained roots are useful. They also retain memory: an old version remains reachable until its root is released. This small example shows the ownership contract, not a balanced production text engine with bounded height under arbitrary edits.",
         cost="A join allocates one internal node in O(1) time. Indexed character lookup follows tree height H and costs O(H). Split and edits visit O(H) nodes and may copy up to L characters when splitting a leaf of length L; inserting M new characters also creates O(M) character data. A fresh build of N characters costs O(N) time and space for chunking and tree nodes. Flattening any root costs O(N) time and output space. With no post-edit balancing, H can become O(E) after E repeated edits, so no logarithmic edit guarantee is claimed. Shared subtrees lower new allocation but retained snapshots keep their referenced chunks alive.",
         mistakes=["Do not mutate shared leaves after publishing a revision.", "Do not claim constant-time arbitrary insertion from constant-time join.", "Do not assume a balanced initial tree stays balanced after edits.", "Do not confuse code-point offsets with byte offsets or grapheme boundaries."],
         related=["dsa/piece-table-text-editing", "dsa/persistent-ordered-index-path-copying", "dsa/implicit-treap-range-reversal"]),
    dict(path="dsa/unrolled-linked-list-block-edits", program="unrolled_incident_list.py",
         template="dsa/circular-linked-list-tail-invariant", section="dsa/linked-lists",
         title="Unrolled lists: link small blocks instead of single items",
         summary="Split full list nodes and merge neighboring blocks after removals.",
         definition="An unrolled linked list stores several logical items in each linked node. The link count falls because one pointer can serve a block, while insertion within a located block still shifts a bounded number of items in its local array. This implementation has a head, tail, total length, and a configurable maximum block size. Inserting into an overflowing block splits its items into two consecutive nodes; deletion unlinks an empty block and merges adjacent blocks when their combined items fit. It allows underfilled blocks, so it does not promise a minimum occupancy or a particular memory-density bound. Every item belongs to exactly one reachable block, no reachable block is empty, and the tail must be the last reachable node after a split, merge, or unlink.",
         case="An incident queue contains alert-47, alert-19, alert-61, and alert-83. The operator inserts alert-29 at logical position two, then removes the former alert-19 entry. Both changes can split or merge short blocks without shifting the whole logical sequence. The resulting order is alert-47, alert-29, alert-61, alert-83. A caller who already holds a direct block reference can edit locally, but this API receives numeric positions; it must follow block links from the head to locate them. That distinction is why the lesson does not label indexed insertion as constant time.",
         cost="Let B be the number of blocks and C the configured block capacity. Locating an arbitrary index scans up to B links; a local insertion, deletion, split, or merge can move O(C) items, so indexed edits cost O(B + C) time. Indexed reads cost O(B). Tail append is O(1) amortized with an O(C) allocation or Python-list growth at a block boundary. Traversal costs O(N) for N items, and storage is O(N + B) for item references and block links. Python's object allocation can outweigh theoretical cache benefits; this is a logical block model, not a measured low-level memory-layout claim.",
         mistakes=["Do not forget to update tail when splitting or deleting the last block.", "Do not leave an empty block reachable after deletion.", "Do not call indexed access constant time merely because each block is small.", "Do not promise minimum occupancy when the implementation only merges blocks that fit."],
         related=["dsa/singly-linked-list-head-tail-invariants", "dsa/doubly-linked-list-relink-and-ownership", "dsa/resizable-array-growth-and-insert-cost"]),
    dict(path="dsa/segmented-array-prefix-block-locate", program="segmented_incident_array.py",
         template="dsa/resizable-array-growth-and-insert-cost", section="dsa/array-data-structure-guide",
         title="Segmented arrays: locate blocks through cumulative lengths",
         summary="Use prefix counts for indexed reads and pay to repair them after middle edits.",
         definition="A segmented array stores an ordered sequence in small array blocks and keeps an aligned list of cumulative end offsets. Binary search over those offsets finds the block containing a numeric index; subtracting the preceding end gives the offset inside it. This version appends to the last block, splits an overflowing block, removes empty blocks, and merges adjacent blocks when they fit. Every cumulative end must equal the number of items through its block, and ends must strictly increase because no stored block is empty. Unlike an unrolled linked list, the outer block array permits binary search for an indexed read. Middle edits change later cumulative counts and can shift entries in the outer Python lists. That maintenance cost is explicit rather than hidden under a claimed logarithmic update.",
         case="The incident IDs alert-47, alert-19, alert-61, and alert-83 are split into blocks of at most three. Inserting alert-29 at position two and removing alert-19 changes the same logical sequence as the unrolled-list example. The cumulative ends identify which block owns the third item, alert-61, without following links from the head. If an edit alters a block near the front, all later end offsets must be repaired before the next binary search. Failing to update just one count can return a plausible but wrong incident from a neighboring block.",
         cost="For B blocks of maximum capacity C, at(index) costs O(log B) to binary-search cumulative ends and O(1) to access a block item. A middle insert or deletion costs O(B + C): local shifts and splits cost O(C), and later prefix counts or outer block-list positions can cost O(B). Appending at the tail is amortized O(1) in this Python-list model, including occasional new-block allocation; worst-case list growth can copy outer storage. Traversal and values() cost O(N). Space is O(N + B). The faster indexed read does not imply faster middle edits than an unrolled list or a plain array for small N.",
         mistakes=["Do not binary-search stale cumulative ends after an edit.", "Do not retain an empty block with a duplicate end offset.", "Do not describe middle edits as logarithmic because lookup uses binary search.", "Do not confuse a block reference count with packed memory bytes."],
         related=["dsa/resizable-array-growth-and-insert-cost", "dsa/bitvector-rank-select-superblocks", "dsa/unrolled-linked-list-block-edits"]),
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
                 sort_order=43000 + order * 10, created_at=stamp, updated_at=stamp, published_at=stamp)
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
project_path = "dsa/editable-sequence-tradeoff-audit-project"
quiz_path = "quizzes/dsa-gap-rope-block-sequence-contracts"
assert project_path not in by_path and quiz_path not in by_path
project = copy.deepcopy(by_path["dsa/spatial-update-window-overlap-audit-project"])
project.update(id=str(uuid.uuid5(uuid.NAMESPACE_URL, "aitrove:" + project_path)), path=project_path,
               title="Project: audit text edits and blocked sequence lookups", summary="Compare cursor movement, immutable text revisions, block edits, and indexed reads.",
               sort_order=43040, created_at=stamp, updated_at=stamp, published_at=stamp)
project["data"].update(reading_minutes=30, related=[{"path": path, "title": by_path[path]["title"]} for path in new_paths])
project["body"] = (
    "<p>An incident workstation keeps one editable note and a list of alert IDs. Implement four reference models: a plain Python string for note content, a list for alert order, an array of saved note versions, and explicit block boundaries. Compare every operation from the four lessons against those models. The goal is to expose when an index structure pays for a move, a path copy, a link traversal, or a prefix repair. State whether each offset is a code-point position or a logical record index; neither model silently handles grapheme clusters or distributed concurrent edits.</p>"
    "<h2>Acceptance trace</h2><p>Start with Valve offline. Insert -19 after Valve, append at bay 6, and prepend Alert:; the gap-buffer text must read Alert: Valve-19 offline at bay 6. Save Pump offline at bay 6 as one rope root, then create a later root reading Pump-47 at bay 6 while the saved root still renders its earlier content. Build both blocked alert sequences from alert-47, alert-19, alert-61, and alert-83. Insert alert-29 at index two, remove index one, and confirm the third value is alert-61. Test empty structures and edits at both ends as well as a middle position.</p>"
    '<h3>Expected review record</h3><pre><code class="language-text">note=Alert: Valve-19 offline at bay 6\nsaved=Pump offline at bay 6\nrevised=Pump-47 at bay 6\nalerts=[alert-47, alert-29, alert-61, alert-83]</code></pre>'
    "<h2>Boundary and cost review</h2><p>Run random cursor moves, insertions, forward deletions, and backspaces against the plain string. Check that the gap contains only unused slots and that its left boundary equals the logical cursor. After every rope edit, verify both the new root and a retained old root; count tree height after repeated one-sided joins. For each blocked sequence, compare every inserted or deleted ID to a plain list, check total length, and verify all block sizes. Check that cumulative ends in the segmented array equal running block lengths. Explain why a gap-buffer jump, an unbalanced rope, an unrolled numeric lookup, and segmented prefix repair may each scan or copy a large fraction of the structure.</p>"
    "<h3>Common Mistakes</h3><ul><li>Do not include the gap in displayed note text.</li><li>Do not mutate shared rope chunks.</li><li>Do not leave empty linked blocks after deletion.</li><li>Do not trust stale cumulative block ends.</li></ul>"
    "<h2>Connected lessons</h2>" + links(new_paths + ["dsa/projects", "dsa/quizzes", subject_root])
)
entries.append(project)
by_path[project_path] = project

questions = [
    ("What does the gap represent in an editable note?", ["Unused array slots at the logical cursor", "Visible underscore characters in the note", "A separate linked-list node for every character"], "Only the text before and after the unused interval is part of the logical note; the gap's left boundary gives the cursor."),
    ("What can make a one-character gap-buffer edit expensive?", ["Moving the gap across a distant part of the note first", "Using a gap that already sits at the cursor", "Leaving spare capacity for another insertion"], "A distant cursor relocation copies intervening characters even if the following insertion consumes only one gap slot."),
    ("What is the cost of displaying the complete gap-buffer note?", ["Linear in the note length", "Constant because the cursor is already known", "Logarithmic in the gap size"], "The logical text lies in two array slices, so materializing one display string visits all note characters."),
    ("Why can an old rope root still render an earlier revision?", ["Edits allocate new path nodes and share unchanged subtrees", "Every leaf is overwritten in place", "The old root stores only a timestamp"], "Structural sharing preserves the unchanged nodes reachable from earlier roots while edited paths receive new nodes."),
    ("What does an internal rope weight measure?", ["Character count in its left subtree", "The number of edit operations", "The maximum number of children"], "The left-subtree length decides whether an indexed character lies left or right and how far to subtract on a right descent."),
    ("What weakens this rope's indexed-access bound after many joins?", ["Tree height can grow because joins do not rebalance", "Leaf strings can no longer be read", "The root loses its total length"], "The initial tree is roughly balanced, but repeated one-sided joins can create a long path without a height-repair step."),
    ("When does an unrolled list split a block?", ["After an insertion pushes its item count past capacity", "Whenever a read crosses a block boundary", "Only when the whole list becomes empty"], "The split redistributes one overfull node into two ordered nodes, keeping each within the configured block limit."),
    ("Why is numeric access in an unrolled linked list not constant time?", ["It may need to follow many block links from the head", "Every block holds only one item", "Blocks are sorted by incident ID"], "Small local arrays reduce links per item, but locating a numeric index still traverses preceding blocks in this design."),
    ("What must deletion repair when the final unrolled block becomes empty?", ["The predecessor link and the tail reference", "Every incident ID in earlier blocks", "Only the displayed text string"], "An empty terminal node must be unlinked and tail moved to its predecessor so future appends use a reachable node."),
    ("How does the segmented array locate a numeric index?", ["Binary-search cumulative block ends, then subtract the previous end", "Follow a next pointer through every block", "Hash the incident ID into a bucket"], "Cumulative ends let the array choose a block by binary search and compute the local offset from its preceding boundary."),
    ("Why can a segmented-array middle insertion cost linear work in block count?", ["Later cumulative ends and outer block positions may need repair", "Binary search always visits every block", "Each block stores all incidents"], "Finding one block is logarithmic, but a structural change near the front can update or shift many later metadata entries."),
    ("What invariant prevents ambiguous segmented-array offsets?", ["Every stored block is nonempty and cumulative ends strictly increase", "Every block contains exactly one incident", "All incident IDs sort lexicographically"], "A zero-length block would duplicate a cumulative end, breaking the direct mapping from index to one owning block."),
]
balanced = []
for number, (prompt, options, explanation) in enumerate(questions):
    distractors = options[1:]
    position = number % 3
    distractors.insert(position, options[0])
    balanced.append({"prompt": prompt, "options": distractors, "answer": position, "explanation": explanation})
quiz = copy.deepcopy(by_path["quizzes/dsa-spatial-grid-tree-code-contracts"])
quiz.update(id=str(uuid.uuid5(uuid.NAMESPACE_URL, "aitrove:" + quiz_path)), path=quiz_path,
            title="Gap buffers, ropes, and blocked sequences", summary="Check cursor movement, path sharing, block ownership, and cumulative offsets.",
            sort_order=43050, created_at=stamp, updated_at=stamp, published_at=stamp)
quiz["data"].update(duration_minutes=20, related=[{"path": path, "title": by_path[path]["title"]} for path in new_paths + [project_path]], questions=balanced)
quiz["body"] = "<p>Choose a sequence representation by the operation that must be cheap. Each representation still has a boundary condition and a cost that a happy-path lookup can hide.</p><h2>Lessons</h2>" + links(new_paths) + "<h2>Design exercise</h2>" + links([project_path, subject_root])
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
    ("dsa/piece-table-text-editing", new_paths[0]),
    ("dsa/piece-table-text-editing", new_paths[1]),
    ("dsa/resizable-array-growth-and-insert-cost", new_paths[0]),
    ("dsa/resizable-array-growth-and-insert-cost", new_paths[3]),
    ("dsa/singly-linked-list-head-tail-invariants", new_paths[2]),
    ("dsa/bitvector-rank-select-superblocks", new_paths[3]),
):
    old = by_path[old_path]
    old["body"] += '<p><a href="/' + new_path + '">' + html.escape(by_path[new_path]["title"]) + "</a> adds a related sequence operation contract.</p>"
    old["updated_at"] = stamp
for path in new_paths:
    entry = by_path[path]
    peers = [other for other in new_paths if other != path]
    entry["body"] += '<p>Compare its edit and lookup costs with ' + ", ".join('<a href="/' + other + '">' + html.escape(by_path[other]["title"]) + "</a>" for other in peers) + ', then run the <a href="/' + project_path + '">sequence audit</a> and <a href="/' + quiz_path + '">contract quiz</a>.</p>'
    entry["updated_at"] = stamp

fixture.write_text(json.dumps(entries, ensure_ascii=False, indent=2) + "\n")
print(json.dumps({"lessons": new_paths, "project": project_path, "quiz": quiz_path, "questions": len(questions)}))
