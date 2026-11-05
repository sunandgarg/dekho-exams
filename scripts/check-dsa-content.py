"""Validate the DSA curriculum and execute its standalone Python examples."""

import html
import json
import re
import subprocess
import sys
from html.parser import HTMLParser
from pathlib import Path

root = Path(__file__).resolve().parents[1]
entries = json.loads((root / "src/data/fixtures.json").read_text())
by_path = {entry["path"]: entry for entry in entries}
root_path = "dsa/dsa-tutorial-learn-data-structures-and-algorithms"
curriculum = [entry for entry in entries if entry["path"].startswith("dsa/")]
articles = [entry for entry in curriculum if (entry.get("data") or {}).get("kind") in {"tutorial", "algorithm", "project"}]
quiz_banks = [entry for entry in entries if entry["path"] in {
    "quizzes/dsa-linear-hash-decisions", "quizzes/dsa-tree-graph-range-decisions",
    "quizzes/dsa-advanced-structure-contracts", "quizzes/dsa-index-and-queue-invariants",
    "quizzes/dsa-mutation-and-versioning-contracts",
    "quizzes/dsa-deletion-priority-dependency-checks",
    "quizzes/dsa-tree-deletion-rollback-routes",
    "quizzes/dsa-offline-queue-snapshot-recovery",
    "quizzes/dsa-online-persistence-journal-cas",
    "quizzes/dsa-pattern-spatial-frequency-indexes",
    "quizzes/dsa-circular-traversal-bitset-rank",
    "quizzes/dsa-sparse-quantile-parity-sequence",
    "quizzes/dsa-bit-rank-path-and-run-contracts",
    "quizzes/dsa-lazy-ancestor-grid-hash-contracts",
    "quizzes/dsa-forest-substring-piece-contracts",
    "quizzes/dsa-cuckoo-spatial-bit-trie-contracts",
    "quizzes/dsa-range-proof-median-contracts",
    "quizzes/dsa-block-threshold-disjoint-line-contracts",
    "quizzes/dsa-rank-window-grid-contracts",
    "quizzes/dsa-postings-position-grams-lexicon-contracts",
    "quizzes/dsa-eviction-expiry-handle-heap-contracts",
    "quizzes/dsa-heavy-hitter-distinct-sample-contracts",
    "quizzes/dsa-approximate-membership-mutation-contracts",
    "quizzes/dsa-priority-queue-meld-monotone-extreme-contracts",
    "quizzes/dsa-spatial-grid-tree-code-contracts",
    "quizzes/dsa-gap-rope-block-sequence-contracts",
    "quizzes/dsa-compact-integer-index-contracts",
    "quizzes/dsa-arena-free-buddy-slab-contracts",
    "quizzes/dsa-hamt-term-route-directory-contracts",
    "quizzes/dsa-clock-slru-admission-wheel-contracts",
    "quizzes/dsa-splay-and-resident-history-contracts",
    "quizzes/dsa-layout-cartesian-meld-potential-contracts",
    "quizzes/dsa-range-successor-rebuild-filter-contracts",
    "quizzes/dsa-palindrome-cap-quantile-window-contracts",
    "quizzes/dsa-split-grid-version-hierarchy-contracts",
    "quizzes/dsa-metric-centroid-perfect-membership-contracts",
    "quizzes/dsa-fm-block-max-model-euler-contracts",
    "quizzes/dsa-predecessor-vector-suffix-interval-contracts",
    "quizzes/dsa-overlay-reachability-order-meld-contracts",
    "quizzes/dsa-heap-merge-spatial-rule-contracts",
    "quizzes/dsa-phrase-stabbing-code-condensation-contracts",
    "quizzes/dsa-ordered-rank-grid-majority-contracts",
    "quizzes/dsa-weighted-candidate-bitmap-contracts",
    "quizzes/dsa-group-cut-threshold-family-contracts",
    "quizzes/dsa-signed-window-mode-contracts",
    "quizzes/dsa-prefix-neighborhood-replica-unitig-contracts",
    "quizzes/dsa-adaptive-bit-slice-simhash-dag-contracts",
    "quizzes/dsa-range-mex-xor-affine-priority-contracts",
    "quizzes/dsa-rank-burst-tariff-frequency-routing-contracts",
    "quizzes/dsa-slot-distinct-text-median-ball-contracts"
}]
allowed_tags = {"p", "h2", "h3", "ul", "li", "strong", "pre", "code", "a"}
banned = re.compile(r"\b(?:delve|leverage|harness|foster|streamline|showcase|navigate|demystify|furthermore|moreover|additionally|robust|crucial|pivotal|multifaceted|bespoke|seamless|dynamic|quintessential|nuanced|powerful|versatile)\b", re.I)
errors = []
body_links = 0
executed = 0


class BodyParser(HTMLParser):
    def __init__(self, path):
        super().__init__(convert_charrefs=True)
        self.path = path
        self.links = []

    def handle_starttag(self, tag, attrs):
        if tag not in allowed_tags:
            errors.append(f"{self.path}: invalid tag {tag}")
        attributes = dict(attrs)
        if tag == "a":
            target = attributes.get("href", "")
            if not target.startswith("/") or target[1:] not in by_path:
                errors.append(f"{self.path}: unresolved or external link {target}")
            self.links.append(target)
        if tag == "code" and not attributes.get("class", "").startswith("language-"):
            errors.append(f"{self.path}: code block lacks a language class")


for entry in curriculum + quiz_banks:
    path = entry["path"]
    body = entry.get("body", "")
    if not body.startswith("<p>"):
        errors.append(f"{path}: body does not start with a paragraph")
    if banned.search(body):
        errors.append(f"{path}: banned wording")
    parser = BodyParser(path)
    parser.feed(body)
    body_links += len(parser.links)
    if path != root_path and (entry.get("data") or {}).get("subject_root") != root_path:
        errors.append(f"{path}: wrong subject root")

for entry in articles:
    path = entry["path"]
    body = entry["body"]
    if "<h3>Common Mistakes</h3>" not in body:
        errors.append(f"{path}: no Common Mistakes section")
    prose = re.sub(r"<pre>[\s\S]*?</pre>", "", body)
    prose = re.sub(r"<[^>]+>", " ", prose)
    if len(re.findall(r"\b[\w-]+\b", html.unescape(prose))) < 140:
        errors.append(f"{path}: prose under 140 words")
    code_blocks = re.findall(r'<pre><code class="language-python">([\s\S]*?)</code></pre>', body)
    outputs = re.findall(r'<h3>Output</h3><pre><code class="language-text">([\s\S]*?)</code></pre>', body)
    if (entry.get("data") or {}).get("kind") != "project":
        if len(code_blocks) != 1 or len(outputs) != 1:
            errors.append(f"{path}: expected one Python block and one output block")
            continue
        program = html.unescape(code_blocks[0])
        expected = html.unescape(outputs[0]).strip()
        run = subprocess.run([sys.executable, "-c", program], capture_output=True, text=True, timeout=5)
        if run.returncode or run.stdout.strip() != expected:
            errors.append(f"{path}: code output mismatch: {run.stderr or run.stdout!r}")
        else:
            executed += 1

for entry in quiz_banks:
    questions = (entry.get("data") or {}).get("questions", [])
    if len(questions) != 12 or len({question["prompt"] for question in questions}) != 12:
        errors.append(f"{entry['path']}: expected 12 distinct questions")
    for question in questions:
        options = question.get("options", [])
        if len(options) != 3 or len(set(options)) != 3 or question.get("answer") not in range(3):
            errors.append(f"{entry['path']}: invalid options or answer")
        if len(question.get("explanation", "")) < 60 or question.get("explanation", "").startswith("The stated operation"):
            errors.append(f"{entry['path']}: explanation is too generic")

module_paths = set()
for entry in curriculum:
    for module in (entry.get("data") or {}).get("modules", []):
        module_paths.update(module.get("lessons", []))
for entry in articles:
    if entry["path"] not in module_paths:
        errors.append(f"{entry['path']}: missing from a module")

report = {"passed": not errors, "sections": len([entry for entry in curriculum if (entry.get("data") or {}).get("modules")]) - 1,
          "articles": len(articles), "quizzes": len(quiz_banks), "questions": sum(len(entry["data"].get("questions", [])) for entry in quiz_banks),
          "bodyLinks": body_links, "executedPythonExamples": executed, "errors": errors}
(root / "work/dsa-content-validation.json").write_text(json.dumps(report, indent=2) + "\n")
print(json.dumps(report))
if errors:
    raise SystemExit(1)
