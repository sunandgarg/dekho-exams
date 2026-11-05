"""Add decision-boundary lessons, retrieval practice, and a quiz."""

import copy
import datetime
import html
import json
import uuid
from pathlib import Path

root = Path(__file__).resolve().parents[1]
fixture = root / "src/data/fixtures.json"
rows = json.loads(fixture.read_text())
by_path = {row["path"]: row for row in rows}
stamp = datetime.datetime.now(datetime.UTC).isoformat()
root_path = "prompt-engineering/prompt-engineering"
patterns = "prompt-engineering/patterns"
production = "prompt-engineering/production"
projects = "prompt-engineering/projects"
quizzes = "prompt-engineering/quizzes"
project_path = "prompt-engineering/retrieval-quality-gate-project"
quiz_path = "quizzes/prompt-engineering-evidence-decisions"


def lesson(slug, title, summary, section, definition, case, sample, cost, mistakes, related, language="text"):
    return dict(path="prompt-engineering/" + slug, title=title, summary=summary,
                section=section, definition=definition, case=case, sample=sample,
                cost=cost, mistakes=mistakes, related=related, language=language)


specs = [
    lesson(
        "prompting-vs-retrieval-vs-training",
        "Prompting, retrieval, or training: choose the failing layer",
        "Fix the task contract, missing knowledge, or repeated model behavior at its source.", root_path,
        "Prompting changes the instructions and context sent with a request. Retrieval supplies current or private evidence at request time. Training changes model behavior through an additional learning process. They solve different failures. If the model receives the right facts but ignores an output constraint, inspect the prompt and validation. If the facts never arrive, repair ingestion or retrieval. If a stable, frequent behavior remains poor after clean instructions and evidence, training may be worth evaluating against a fixed baseline. No option removes the need for held-out tests.",
        "A parts-support assistant repeatedly gives an old replacement rule. The team first finds that the current rule is absent from the retrieved set; rewriting the prompt cannot supply a document that was never fetched. After the index is repaired, most cases pass. A small formatting defect remains and is fixed with a schema. The team does not train a model on copies of the policy, because that would put time-bound facts in weights and make a later policy change harder to trace. The release packet records which layer changed and the cases it affected.",
        "Failure A: correct evidence present, wrong field shape -> schema and prompt.\nFailure B: current policy absent -> ingestion and retrieval.\nFailure C: repeated behavior defect after clean inputs -> compare training with baseline.\nFor each: freeze cases, cost, and acceptance checks.",
        "Prompt edits are usually quick to test; retrieval requires an index and freshness controls; training adds data preparation, evaluation, and lifecycle cost. Comparing them requires cost per accepted case, not a claim that one technique is always cheaper. If N policy updates occur, embedding current facts in model weights can add repeated retraining work. Keep private and time-sensitive facts in governed data stores when a request-time lookup can supply them. Diagnose the input path before paying to change model behavior.",
        ["Do not ask a prompt to invent missing source facts.", "Do not use training as a substitute for current policy retrieval.", "Do not call a formatting problem a knowledge problem."],
        ["prompt-engineering/task-contract", "prompt-engineering/retrieval-evidence-selection"],
    ),
    lesson(
        "query-rewrite-and-coreference",
        "Retrieval queries: resolve references without adding facts",
        "A conversational search query must preserve what the user actually asked.", patterns,
        "A user may say 'what about that one?' after several topics. A retrieval rewrite can turn the turn into a self-contained query, but it must resolve references from verified conversation state and keep unresolved references explicit. The rewrite is a search aid, not the final answer. Store the original request and the rewritten query together. Compare retrieved evidence with a query made from the original words, because an invented product name or date can retrieve a plausible but unrelated passage.",
        "A service agent is discussing two warranty plans, WP-41 for appliances and WP-62 for laptops. The user asks, 'Does the second one cover battery swelling?' The rewrite resolves 'second one' to WP-62 because the active comparison order is recorded. It does not add a purchase date or claim that swelling is covered. Search results must include the coverage rule and its effective period before the assistant answers. If the conversation order was lost during summarization, the assistant asks which plan the user means instead of guessing.",
        "Original: Does the second one cover battery swelling?\nVerified state: second plan = WP-62, laptop warranty.\nSearch query: WP-62 battery swelling coverage and exclusions.\nUnknown: purchase date; do not insert one.",
        "A rewrite adds at least one processing step and may create a second query, so compare the retrieval gain with latency. For Q rewrites and K retrieved candidates, the cost includes query generation and ranking across Q candidate lists. Measure whether the governing passage enters the top K, not merely whether search returns topical text. Store rewrite errors separately from answer errors; otherwise a good answer prompt may be blamed for a bad query. Ambiguous references should trigger clarification when the decision has consequence.",
        ["Do not turn a probable reference into a certain one.", "Do not add an unstated date to improve search results.", "Do not grade only answer fluency after a query rewrite."],
        ["prompt-engineering/conversation-memory-boundary", "prompt-engineering/retrieval-evidence-selection"],
    ),
    lesson(
        "chunk-boundary-and-parent-context",
        "Document chunks: preserve the clause and its governing exception",
        "A retrieved chunk can be accurate text yet incomplete evidence.", patterns,
        "Chunking splits long documents for indexing, but a boundary can separate a general rule from the exception that limits it. Keep a stable chunk ID, document version, section heading, and parent-document link. Retrieval may find a short passage for ranking, then expand to neighboring or parent context before a consequential answer. The expansion must stay within the authorized document scope. Test boundary cases where the clause and exception sit on opposite sides of a chunk, and compare evidence sufficiency, not only search relevance.",
        "A refund policy has a 44-day window in section 3 and an exception for opened equipment in section 4. Search returns section 3 for a request about an opened device. A prompt using only that chunk approves the refund incorrectly. The application expands to the parent policy segment, sees both sections, and sends the complete rule with IDs to the decision step. If section 4 is access-restricted, the workflow does not quote it from another tenant's index; it returns review because authorized evidence is incomplete.",
        "Retrieved hit: policy-P17/section-3, 44-day window.\nParent expansion: section-4, opened-equipment exception.\nDecision input: both sections and effective version.\nIf expansion denied or missing: review, not approve.",
        "Smaller chunks improve search specificity but can raise index size and require expansion calls. Larger chunks carry more context but increase model tokens and may bury the key exception. Evaluate chunk sizes on a fixed set of question-document pairs and measure whether the complete governing rule reaches the model. For M passages retrieved, expansion is O(M) lookups before deduplication. Preserve source locations so the final evidence IDs can be checked against the original document.",
        ["Do not accept a relevant fragment as the complete rule.", "Do not let parent expansion bypass access controls.", "Do not strip the section ID when merging neighboring chunks."],
        ["prompt-engineering/retrieval-evidence-selection", "prompt-engineering/retrieval-freshness-and-conflict"],
    ),
    lesson(
        "deterministic-calculation-gates",
        "Numeric prompts: let code calculate and the model explain",
        "A fluent calculation is not a validated arithmetic result.", patterns,
        "A prompt can interpret which fields matter and explain a computed result, but application code should perform exact arithmetic when the operation is known. Parse units, currency, and missing values before calculation. The model receives the computed total and the source rows; it may explain the rule but cannot silently override the number. For money, use decimal arithmetic with an explicit rounding rule. A mismatch between model prose and the computed value is a validation failure, not an invitation to average both answers.",
        "An invoice contains two valve assemblies at 47.25 each and three seals at 19.40 each. Code computes 152.70. The assistant explains that the total excludes tax because the input has no tax jurisdiction. A second invoice has an unknown quantity and is routed to review rather than inventing a number. The test checks the amount, row IDs, and uncertainty state. If the assistant writes 152.70 but cites only one row, the explanation fails the evidence check even though the arithmetic is correct.",
        "from decimal import Decimal\n\nline_items = [\n    {\"sku\": \"VALVE-47\", \"quantity\": 2, \"unit_price\": \"47.25\"},\n    {\"sku\": \"SEAL-19\", \"quantity\": 3, \"unit_price\": \"19.40\"},\n]\ninvoice_total = sum(\n    (Decimal(item[\"unit_price\"]) * item[\"quantity\"] for item in line_items),\n    Decimal(\"0\"),\n)\nprint(invoice_total)  # 152.70",
        "A single pass over N line items costs O(N) time and O(1) extra space beyond the input list. Decimal arithmetic avoids binary floating-point surprises for this fixed-price example, though tax and rounding rules still need their own contract. A tool call has overhead, but a deterministic subtotal is cheaper to verify than repeated model reasoning. Test empty lists, negative adjustments, unknown quantities, and unit mismatches. Do not present an untaxed subtotal as a final payable amount.",
        ["Do not ask a model to guess a missing quantity.", "Do not use binary floating point for a money contract without a rounding policy.", "Do not let prose overwrite the computed total."],
        ["prompt-engineering/input-normalization-contract", "prompt-engineering/task-decomposition-and-handoffs"], "python",
    ),
    lesson(
        "selective-prediction-thresholds",
        "Selective answers: measure when to abstain",
        "A workflow needs a decision rule for using or withholding uncertain output.", production,
        "An abstention policy defines the evidence and validation conditions under which the system may answer, and when it must return review or ask for missing data. Do not treat a model's self-reported confidence number as a calibrated probability without testing it. Build a labeled set that includes clean, conflicting, and insufficient cases. Measure the error rate among answered cases together with the share withheld. Raising the bar may reduce wrong decisions but increase human queue load; choose the tradeoff for the consequence of the task.",
        "A claims assistant can approve, deny, or request review. The release rule requires a current policy clause, matching account, and valid receipt date before either final decision. On 68 held-out cases, it withholds 11 with missing or conflicting facts. Reviewers find one unsupported approval among the 57 answered cases. The team keeps that raw count and investigates it; it does not say the system is safe because most outputs looked cautious. A stricter rule may send more cases to review, so staffing and response time are part of the release decision.",
        "Answer only if: current clause + account match + valid receipt date.\nOtherwise: review with missing-field reason.\nReport: answered_count, wrong_answer_count, withheld_count.\nGate: critical unsupported approvals must be zero on the release set.",
        "Computing rule gates is cheap relative to generation, but withheld cases shift cost to people. Track both coverage and risk: a system that abstains on every case has no wrong answers but does not perform the job. Use separate thresholds for low- and high-consequence actions. Recalibrate after policy or model changes, because a threshold tuned on old cases may no longer select the right set. Do not infer uncertainty from response length or politeness.",
        ["Do not call model self-confidence a calibrated probability without testing.", "Do not report error rate without the withheld share.", "Do not force a final label when required evidence is absent."],
        ["prompt-engineering/schema-and-abstention", "prompt-engineering/human-review-escalation"],
    ),
    lesson(
        "evaluation-data-leakage",
        "Evaluation leakage: keep the release test independent",
        "A prompt can appear to improve because the test cases leaked into its examples.", production,
        "A release evaluation needs cases independent of the material used to write the prompt, choose examples, and tune settings. Deduplicate near-identical records across development and holdout sets, including paraphrases and versions of the same incident. Freeze expected labels before running the candidate. If a failure becomes a prompt example, move that specific case out of the final holdout and add a fresh case of the same failure class. Preserve a hidden or later-collected set for the final check.",
        "A support team has 92 labeled tickets. An author copies six troublesome holdout tickets into the few-shot prompt, then reports a large gain on the same 92. The gain cannot establish generalization. The evaluator marks those six and their paraphrases as contaminated, creates a new holdout from later tickets, and compares the revised prompt with the previous version there. It also verifies that the expected answers were not embedded in a retrieved knowledge page. The team retains the contaminated cases for debugging, but stops calling them independent release evidence.",
        "Development set: prompt editing and example selection.\nFrozen holdout: unseen cases and labels.\nLeak check: duplicate IDs, near-duplicate content, retrieved answer keys.\nIf contaminated: replace release cases; keep old ones for diagnosis only.",
        "Deduplication takes additional data work and may require semantic review when cases are paraphrased. A simple hash finds exact duplicates in O(N) expected time with an index, but near-duplicates need comparison or retrieval. The cost matters because a misleading evaluation can ship a broken workflow. Log the lineage of every test case and sample example. Repeat the final check on fresh data after a policy change rather than recycling a set that authors have memorized.",
        ["Do not grade on the examples inside the prompt.", "Do not treat paraphrased duplicates as independent cases.", "Do not hide contaminated cases; label and retain them for debugging."],
        ["prompt-engineering/few-shot-example-selection", "prompt-engineering/evaluation-slice-design"],
    ),
    lesson(
        "output-sink-validation",
        "Generated output: validate again at the destination boundary",
        "A schema-valid model response can still be unsafe for an HTML page, query, or tool.", production,
        "Output validation depends on the destination. A JSON parser checks structure, but a rendered web page also needs HTML-safe handling, a database query needs parameterization, and a tool action needs authorization. Treat generated text as untrusted data even after the model follows its prompt. Keep the model's proposed value separate from the command that uses it. Escape for the specific output context, enforce allowlists where appropriate, and reject unexpected fields before passing the result to another component.",
        "A support assistant drafts a case title that includes markup from a customer note. The output schema accepts the title as a string. The UI renders it as text, not raw HTML, so the markup cannot become a script element. A second field proposes a refund amount; the executor ignores that field until it checks the actor, invoice, balance, and effect key. The team tests both sinks with hostile strings and malformed numbers. One successful JSON parse does not cover either downstream boundary.",
        "Model result: {title: customer_text, proposed_refund: 47.00}.\nUI sink: render title as text with context-appropriate encoding.\nEffect sink: validate actor, invoice, amount, idempotency key.\nReject: unexpected fields or a failed business rule.",
        "Sink-specific checks add parsing and policy work, usually small compared with a model call. For output of size B, escaping and schema validation are generally O(B), while authorization may need a database read. The checks prevent one model error from becoming code execution, a malformed query, or an unauthorized effect. Measure rejected values by sink and review whether the prompt is producing avoidable garbage, but never remove the sink check merely because recent prompts behaved well.",
        ["Do not render generated markup as trusted HTML.", "Do not build a database command by concatenating model text.", "Do not confuse schema validity with permission to act."],
        ["prompt-engineering/schema-and-abstention", "prompt-engineering/tool-call-authorization-contract"],
    ),
]

titles = {entry["path"]: entry["title"] for entry in rows}
titles.update({spec["path"]: spec["title"] for spec in specs})
titles.update({
    project_path: "Project: measure a retrieval-backed answer gate",
    quiz_path: "Prompt evidence and output decisions",
})
new_paths = {spec["path"] for spec in specs} | {project_path, quiz_path}
assert not new_paths.intersection(by_path), "new route already exists"


def link(path):
    assert path in titles, path
    return f'<a href="/{html.escape(path)}">{html.escape(titles[path])}</a>'


def link_list(paths):
    return "<ul>" + "".join(f"<li>{link(path)}</li>" for path in dict.fromkeys(paths)) + "</ul>"


def related(paths):
    return [{"path": path, "title": titles[path]} for path in dict.fromkeys(paths)]


def article(template, *, path, title, summary, body, section, subject, kind, order, connections):
    entry = copy.deepcopy(template)
    entry.update(id=str(uuid.uuid5(uuid.NAMESPACE_URL, "aitrove:" + path)),
                 path=path, title=title, summary=summary, body=body,
                 category="AI & Data", subject=subject, difficulty="Advanced",
                 tags=["prompt engineering", kind], sort_order=order,
                 status="published", published_at=stamp, created_at=stamp,
                 updated_at=stamp)
    entry["data"].update(kind=kind, reading_minutes=10 if kind == "tutorial" else 15,
                         author_path="authors/aitrove-editorial", subject_root=root_path,
                         section_path=section, content_format="html", seo_ready=True,
                         related=related(connections))
    return entry


new_rows = []
for index, spec in enumerate(specs):
    same_section = [item["path"] for item in specs if item["section"] == spec["section"]]
    location = same_section.index(spec["path"])
    neighbors = same_section[max(location - 1, 0):location] + same_section[location + 1:location + 2]
    connections = list(dict.fromkeys(
        [root_path, spec["section"]] + spec["related"] + neighbors
        + [project_path, quiz_path]
    ))
    connections = [path for path in connections if path != spec["path"]]
    body = (
        f"<p>{html.escape(spec['definition'])}</p>"
        f"<h2>Decision in practice</h2><p>{html.escape(spec['case'])}</p>"
        f'<pre><code class="language-{spec["language"]}">{html.escape(spec["sample"])}</code></pre>'
        f"<h2>Performance and operating cost</h2><p>{html.escape(spec['cost'])}</p>"
        "<h3>Common Mistakes</h3><ul>"
        + "".join(f"<li>{html.escape(item)}</li>" for item in spec["mistakes"])
        + "</ul><h2>Connected lessons</h2>" + link_list(connections)
    )
    new_rows.append(article(
        by_path["prompt-engineering/task-contract"],
        path=spec["path"], title=spec["title"], summary=spec["summary"],
        body=body, section=spec["section"],
        subject="prompt-engineering" if spec["section"] == root_path
                else "prompt-engineering-" + spec["section"].rsplit("/", 1)[1],
        kind="tutorial", order=25900 + index, connections=connections[:8],
    ))

for section, title in (
    (root_path, "Choose the right intervention"),
    (patterns, "Queries, complete evidence, and exact computation"),
    (production, "Decision gates and downstream validation"),
):
    members = [spec["path"] for spec in specs if spec["section"] == section]
    hub = by_path[section]
    hub["data"]["modules"].append({
        "title": title,
        "summary": "Locate the failing layer, then test the repaired decision boundary.",
        "lessons": members,
    })
    hub["body"] += (
        "<h2>" + html.escape(title) + "</h2>"
        "<p>A reliable answer needs the right information, a valid calculation or decision, and a destination that treats generated content as data.</p>"
        + link_list(members)
    )
    hub["updated_at"] = stamp

project_body = (
    "<p>This project measures a retrieval-backed warranty assistant before it can make a customer recommendation. Assemble 61 fictional questions against versioned plan documents. Include short direct questions, multi-turn references, outdated clauses, and cases where a rule and its exception fall in different chunks. The deliverable is a retrieval and answer-quality packet, not a single polished answer.</p>"
    "<h2>Prepare the evidence set</h2>"
    "<p>For each question, record the governing plan ID, effective version, required passages, and an expected answer or review state. Reserve 19 questions as a holdout. Run the original query and a self-contained rewrite, recording both. For each retrieval strategy, measure whether all required passages appear in the top five results. A passage that mentions the product but omits the exception does not count as sufficient. Expand parent context only inside the authorized document scope.</p>"
    "<h2>Gate the decision</h2>"
    "<p>Ask the model for decision, evidence IDs, and uncertainty reason. Validate that cited IDs are in the supplied set and that the policy version covers the case date. A deterministic code path checks arithmetic for any price adjustment. The answer gate withholds a final decision when evidence is missing, conflicting, or expired. Then validate the response again for its destination: render customer text as text and run any proposed account effect through the executor's permission checks.</p>"
    '<pre><code class="language-text">Question set: 61 cases; 19 untouched holdout cases.\nRetrieval gate: all required passages in top 5 and current version.\nAnswer gate: decision supported by supplied IDs; otherwise review.\nCompare: original query vs verified rewrite, same cases.\nReport: complete-evidence rate, unsupported-answer count, withheld share.</code></pre>'
    "<h2>Performance and operating cost</h2>"
    "<p>For N questions and Q query variants, retrieval runs are O(NQ) before any model repeats. Parent expansion increases context tokens, so measure cost per accepted case as well as evidence completeness. Keep retrieval errors separate from answer errors and publish raw counts for critical failures. A candidate that answers fewer cases may still be preferable for a consequential action if it avoids unsupported decisions, but the added human-review load must be explicit.</p>"
    "<h3>Common Mistakes</h3><ul>"
    "<li>Do not count a topical hit as the full governing rule.</li>"
    "<li>Do not tune query rewriting on the untouched holdout.</li>"
    "<li>Do not let a model-generated decision bypass the output sink or executor.</li>"
    "</ul><h2>Connected lessons</h2>"
    + link_list([
        "prompt-engineering/query-rewrite-and-coreference",
        "prompt-engineering/chunk-boundary-and-parent-context",
        "prompt-engineering/selective-prediction-thresholds",
        "prompt-engineering/evaluation-data-leakage",
        "prompt-engineering/output-sink-validation",
        quiz_path,
    ])
)
new_rows.append(article(
    by_path["devops/practice-project"], path=project_path,
    title=titles[project_path],
    summary="Measure query, evidence, abstention, and answer gates on held-out cases.",
    body=project_body, section=projects, subject="prompt-engineering-project",
    kind="project", order=25950,
    connections=[
        "prompt-engineering/query-rewrite-and-coreference",
        "prompt-engineering/chunk-boundary-and-parent-context",
        "prompt-engineering/selective-prediction-thresholds",
        "prompt-engineering/output-sink-validation",
        quiz_path,
    ],
))
by_path[projects]["data"]["modules"][0]["lessons"].append(project_path)
by_path[projects]["body"] += (
    "<h2>Retrieval quality gate project</h2>"
    "<p>Test whether the complete governing passage reaches the decision step before an answer is accepted.</p>"
    + link_list([project_path, quiz_path])
)
by_path[projects]["updated_at"] = stamp

question_specs = [
    ("The current rule never reaches the model. What should be repaired first?",
     "Ingestion or retrieval", "Response tone", "Sampling temperature",
     "A prompt cannot apply evidence absent from its input.",
     "prompt-engineering/prompting-vs-retrieval-vs-training"),
    ("A model has correct facts but returns an invalid field. Which layer is the first candidate?",
     "The output contract and parser", "The search index", "Additional training",
     "The evidence arrived; the response shape failed.",
     "prompt-engineering/prompting-vs-retrieval-vs-training"),
    ("The user says 'the second plan' after comparing two plans. What may a search rewrite do?",
     "Resolve the reference from verified conversation state", "Invent a purchase date", "Change the requested product",
     "A rewrite should make the query self-contained without adding facts.",
     "prompt-engineering/query-rewrite-and-coreference"),
    ("The conversation order was lost. What is the sound next step?",
     "Ask which plan the user means", "Guess the popular plan", "Search both and select the top hit",
     "An unresolved reference should stay unresolved when a wrong decision matters.",
     "prompt-engineering/query-rewrite-and-coreference"),
    ("A retrieved chunk states a refund window but omits an adjacent exception. Is it sufficient?",
     "No; expand authorized parent context", "Yes; the text is relevant", "Yes; a model can infer the exception",
     "A governing rule includes its applicable exceptions.",
     "prompt-engineering/chunk-boundary-and-parent-context"),
    ("Parent context is access-restricted. What should the workflow do?",
     "Return review for insufficient authorized evidence", "Read another tenant's document", "Approve from the fragment",
     "Expansion cannot bypass document access control.",
     "prompt-engineering/chunk-boundary-and-parent-context"),
    ("What is the exact subtotal of two items at 47.25 and three at 19.40?",
     "152.70", "133.30", "155.70",
     "Two times 47.25 is 94.50; three times 19.40 is 58.20.",
     "prompt-engineering/deterministic-calculation-gates"),
    ("The model explains a subtotal but the quantity is missing. What output is valid?",
     "Review with the missing quantity named", "A plausible estimate", "A forced zero",
     "Exact arithmetic needs complete normalized inputs.",
     "prompt-engineering/deterministic-calculation-gates"),
    ("A system withholds every case and reports zero wrong answers. What is missing?",
     "The answered share and useful coverage", "More confident language", "A longer prompt",
     "Risk must be evaluated with the fraction of cases handled.",
     "prompt-engineering/selective-prediction-thresholds"),
    ("Six holdout cases were copied into few-shot examples. How should they be scored?",
     "As contaminated, not independent release evidence", "As stronger proof", "As new hidden cases",
     "The prompt has seen those cases or their answers.",
     "prompt-engineering/evaluation-data-leakage"),
    ("A schema-valid title contains customer-supplied markup. How should a web UI render it?",
     "As encoded text for that UI context", "As trusted raw HTML", "As a database command",
     "Schema validity does not make the string safe at the destination.",
     "prompt-engineering/output-sink-validation"),
    ("A generated refund proposal passes JSON validation. What still blocks execution?",
     "Executor authorization and business-rule checks", "Nothing", "The model's confidence number",
     "An effect needs independent permission and state checks.",
     "prompt-engineering/output-sink-validation"),
]
questions = []
for index, (prompt, correct, wrong_a, wrong_b, explanation, target) in enumerate(question_specs):
    options = [correct, wrong_a, wrong_b]
    offset = index % 3
    questions.append({
        "prompt": prompt, "options": options[offset:] + options[:offset],
        "answer": (-offset) % 3,
        "explanation": explanation + " Review " + titles[target] + ".",
    })

quiz_body = (
    "<p>These cases ask which layer failed and what evidence is required before a result can be used. Select the answer that keeps uncertainty and downstream effects explicit.</p>"
    "<h2>Review the decisions</h2>"
    + link_list([spec["path"] for spec in specs])
    + "<h3>Common Mistakes</h3><ul>"
    "<li>Do not blame prompt wording when the governing document was never retrieved.</li>"
    "<li>Do not count a fragment as a complete rule.</li>"
    "<li>Do not treat schema-valid text as safe at every destination.</li>"
    "</ul><h2>Practice</h2>"
    + link_list([project_path, patterns, production])
)
quiz_row = copy.deepcopy(by_path["quizzes/prompt-engineering-design-decisions"])
quiz_row.update(id=str(uuid.uuid5(uuid.NAMESPACE_URL, "aitrove:" + quiz_path)),
                path=quiz_path, title=titles[quiz_path],
                summary="Twelve decisions on retrieval, arithmetic, abstention, and output sinks.",
                body=quiz_body, sort_order=25960,
                status="published", published_at=stamp, created_at=stamp,
                updated_at=stamp)
quiz_row["data"].update(section_path=quizzes, subject_root=root_path,
                        questions=questions, duration_minutes=14,
                        related=related([project_path, root_path, patterns, production]))
new_rows.append(quiz_row)
by_path[quizzes]["data"]["modules"][0]["lessons"].append(quiz_path)
by_path[quizzes]["body"] += (
    "<h2>Evidence decision quiz</h2>"
    "<p>Find the failing layer before accepting a generated answer or effect.</p>"
    + link_list([quiz_path, project_path])
)
by_path[quizzes]["updated_at"] = stamp

backlinks = {
    "prompt-engineering/task-contract": [
        "prompt-engineering/prompting-vs-retrieval-vs-training",
        "prompt-engineering/deterministic-calculation-gates",
    ],
    "prompt-engineering/conversation-memory-boundary": [
        "prompt-engineering/query-rewrite-and-coreference",
    ],
    "prompt-engineering/retrieval-evidence-selection": [
        "prompt-engineering/query-rewrite-and-coreference",
        "prompt-engineering/chunk-boundary-and-parent-context",
        project_path,
    ],
    "prompt-engineering/schema-and-abstention": [
        "prompt-engineering/selective-prediction-thresholds",
        "prompt-engineering/output-sink-validation",
    ],
    "prompt-engineering/evaluation-slice-design": [
        "prompt-engineering/evaluation-data-leakage",
        project_path,
    ],
    "prompt-engineering/structured-document-extraction": [
        "prompt-engineering/deterministic-calculation-gates",
    ],
    "prompt-engineering/tool-call-authorization-contract": [
        "prompt-engineering/output-sink-validation",
    ],
}
for path, targets in backlinks.items():
    entry = by_path[path]
    entry["body"] += (
        "<h2>Next decision</h2>"
        "<p>Check whether the right facts reached the workflow and whether the result is safe at its destination.</p>"
        + link_list(targets)
    )
    existing = [item["path"] for item in entry["data"].get("related", [])]
    entry["data"]["related"] = related(existing + targets)
    entry["updated_at"] = stamp

rows.extend(new_rows)
assert len({row["path"] for row in rows}) == len(rows), "duplicate route"
fixture.write_text(json.dumps(rows, ensure_ascii=False, indent=2) + "\n")
print(json.dumps({"addedLessons": len(specs), "addedProjects": 1,
                  "addedQuizzes": 1, "newRecords": len(new_rows)}))
