"""Replace generic quiz feedback with operation-specific explanations."""

import json
from pathlib import Path

fixture = Path(__file__).resolve().parents[1] / "src/data/fixtures.json"
entries = json.loads(fixture.read_text())
explanations = {
    "quizzes/dsa-linear-hash-decisions": [
        "Most appends write into reserved capacity; a growth event copies existing references, giving constant amortized cost across a sequence.",
        "Every existing element may need a new index after a front insertion, so its movement cost grows with list length.",
        "The half-open interval excludes index zero and includes indices one, two, and three: 31 + 26 + 58 = 115.",
        "Each prefix entry summarizes an earlier snapshot. A changed source value invalidates every later total until the table is rebuilt.",
        "Changing a known node's link takes constant work. Locating that node by value still requires a walk in the general case.",
        "Removal changes both neighboring references; an external key-to-node index must also discard or update the detached node.",
        "A stack removes the item pushed most recently. Its order matches nested work and reversal of committed edits.",
        "A deque supports endpoint insertion and removal without shifting a list's remaining elements after every front pop.",
        "Head and tail can coincide in both states. Count, a reserved slot, or another explicit flag resolves the ambiguity.",
        "Hash-backed lookup is expected constant time under suitable hashing and resizing; collisions and adverse cases can cost more.",
        "A composite key includes the depot boundary. A bare shipment ID cannot distinguish the same ID in two depots.",
        "Membership is the set's contract. Reporting order needs a separate sequence or an explicit sort operation.",
    ],
    "quizzes/dsa-tree-graph-range-decisions": [
        "Search follows one branch per level. A plain tree can have height n, so the bound depends on actual height h.",
        "Ordered inserts can keep attaching nodes to one side of an unbalanced tree, creating a linear chain.",
        "A min-heap guarantees the smallest key at the root; the rest of its array is only partially ordered.",
        "An arrival counter makes tie order part of the heap key rather than relying on arbitrary payload comparison.",
        "The path for a prefix may exist because longer keys share it. A terminal marker records an exact stored key.",
        "Each reachable vertex and its stored outgoing edges are processed at most once with a visited set.",
        "Marking before enqueue prevents multiple incoming edges from placing the same vertex in the queue repeatedly.",
        "Union-find stores component membership. It does not preserve an actual route or support splitting after an edge deletion.",
        "This Fenwick add method propagates a change amount. A replacement must first be converted to a delta from the old value.",
        "This segment-tree method writes the new leaf value, then recomputes its ancestors from the two children.",
        "The corrected interval adds 31, 29, and 58: 118. Index zero remains outside the half-open range.",
        "A static prefix table pays once for construction and then answers each range sum with two array reads.",
    ],
}

for entry in entries:
    if entry["path"] in explanations:
        questions = entry["data"]["questions"]
        feedback = explanations[entry["path"]]
        assert len(questions) == len(feedback) == 12
        for question, explanation in zip(questions, feedback):
            question["explanation"] = explanation

fixture.write_text(json.dumps(entries, ensure_ascii=False, indent=2) + "\n")
print(json.dumps({"quizBanks": len(explanations), "refinedExplanations": sum(map(len, explanations.values()))}))
