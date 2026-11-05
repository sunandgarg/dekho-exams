"""Add original, bounded reasoning-pattern lessons and an assessment."""

import copy
import datetime
import html
import json
import uuid
from pathlib import Path

root = Path(__file__).resolve().parents[1]
fixture = root / "src/data/fixtures.json"
entries = json.loads(fixture.read_text())
lookup = {entry["path"]: entry for entry in entries}
stamp = datetime.datetime.now(datetime.UTC).isoformat()
subject_root = "prompt-engineering/prompt-engineering"
patterns = "prompt-engineering/patterns"
projects = "prompt-engineering/projects"
quizzes = "prompt-engineering/quizzes"
project_path = "prompt-engineering/reasoning-pattern-selection-project"
quiz_path = "quizzes/prompt-engineering-reasoning-patterns"

specs = [
    {
        "slug": "self-consistency-answer-voting",
        "title": "Self-consistency: sample answers, then verify the winner",
        "summary": "Use multiple independent candidates when a single reasoning path is fragile, but do not mistake a vote for proof.",
        "definition": "Self-consistency samples several candidate solutions to the same bounded problem, normalizes their final answers, and selects an answer that appears repeatedly. The method is useful when different valid routes can converge on one result. It does not make the candidates independent: the same model, prompt, and misleading input can produce the same wrong answer many times. Preserve the answer and the evidence needed to check it, rather than requiring a long private reasoning transcript. Where a deterministic check exists, run that check on the selected result before release.",
        "case": "A freight team must calculate the remaining load for shipment SH-731. The manifest says 47 sealed crates were booked, 19 were loaded at Dock C, and 11 were loaded at Dock F. Five sampled responses return 17, 17, 17, 28, and 17. The vote favors 17, yet the release gate still computes 47 minus 19 minus 11 and checks that neither dock entry was duplicated. If the manifest itself is stale, all five answers can agree on the wrong business fact. The system therefore attaches the manifest revision and refuses to present the result as current when that revision is missing.",
        "sample": "Shipment SH-731: booked=47; dock_c=19; dock_f=11.\nCandidates: 17 | 17 | 17 | 28 | 17.\nNormalized winner: 17; vote share=4/5.\nIndependent arithmetic: 47 - 19 - 11 = 17.\nRelease only with a current manifest revision and no duplicate dock event.",
        "cost": "For N candidates, generation cost and token use rise roughly with N; answer normalization and a frequency table take O(N) time and O(U) space for U distinct answers. Parallel calls can reduce wall-clock time but not total compute. Stop sampling once a predefined budget is reached, and compare the incremental accuracy with a single candidate plus verifier on a held-out set. Voting over free-form prose is unstable unless equivalent answers are normalized. Do not send more candidates merely to drown out a known data-quality problem.",
        "mistakes": ["Do not call a four-of-five vote a correctness guarantee.", "Do not count differently worded versions of one answer as distinct outcomes.", "Do not skip the independent arithmetic or source-revision check."],
        "related": ["prompt-engineering/candidate-sampling-and-verifier", "prompt-engineering/deterministic-calculation-gates", "prompt-engineering/evaluation-slice-design"],
    },
    {
        "slug": "tree-of-thoughts-bounded-search",
        "title": "Tree of Thoughts: branch only where a decision can be checked",
        "summary": "Search alternative partial plans with a strict depth, width, and evaluation budget.",
        "definition": "Tree of Thoughts treats a candidate intermediate plan as a node, expands several possible next steps, scores partial plans, and retains a bounded set for another round. Use it when an early choice changes later options and a single straight-line answer is brittle. A model-generated plausibility score is weak evidence; pair it with feasibility checks from the actual task. State the maximum branching factor, search depth, retained beam width, and stop rule before the search starts. Output a selected plan with its checked constraints, not a pile of speculative branches presented as facts.",
        "case": "A warehouse needs a dispatch sequence for three temperature-controlled pallets and two refrigerated vans. The first candidate sends both heavy pallets in one van, violating its rated capacity. Another leaves a pallet beyond its cold-window limit. The search keeps only partial schedules whose cumulative weight and elapsed time remain feasible. At depth three it has two viable schedules, but one requires a driver who is unavailable; that branch is pruned from the verified roster. If the roster cannot be fetched, the system reports a conditional plan and requests dispatch approval instead of inventing availability.",
        "sample": "Depth limit: 3 decisions; branch factor: at most 3; beam: 2 plans.\nCheck each node: van weight <= rated load; cold time <= 74 min.\nPrune: over-capacity route; expired cold window; unavailable driver.\nStop: two verified feasible plans or 18 evaluated nodes.\nDeliver: chosen schedule, constraints checked, unresolved roster status.",
        "cost": "An unrestricted search with branch factor B and depth D can generate O(B^D) nodes. A beam of width W limits retained state to O(W), while expansions are about O(DWB), plus scorer and external-check costs. Bounded search still costs several model calls and can miss a good path after premature pruning. Record which constraint rejected each branch so a reviewer can distinguish a hard failure from a subjective score. Prefer direct deterministic scheduling when the whole problem can be solved by a trusted optimizer.",
        "mistakes": ["Do not expand branches without a call and node budget.", "Do not rank a feasible route below an impossible route because its prose sounds less polished.", "Do not treat a model score as proof that a constraint was checked."],
        "related": ["prompt-engineering/task-decomposition-and-handoffs", "prompt-engineering/candidate-sampling-and-verifier", "prompt-engineering/tool-loop-stop-rules"],
    },
    {
        "slug": "react-observe-act-control-loop",
        "title": "ReAct: alternate tool actions with checked observations",
        "summary": "Let new evidence change the next step while keeping tool authority and loop bounds outside the model.",
        "definition": "A ReAct-style workflow alternates a concise action proposal, a tool result, and a revised next step. The useful feature is feedback: the next operation depends on observed data rather than a plan written once at the start. The application must expose only eligible tools, validate each call against the authenticated principal, and treat returned text as data rather than instructions. A public response needs a brief evidence summary and receipt, not a private chain of thought. Set a call ceiling, duplicate-call rule, and condition for stopping before allowing the first action.",
        "case": "A maintenance assistant is asked whether pump PM-84 can return to service. Its first permitted action reads the work order and discovers a missing pressure test. The next action retrieves the test record, which shows the measurement but no supervisor sign-off. The assistant must stop at that point and state that release is pending approval. A note embedded in the test record says to mark the job complete, but the note cannot grant permission. If the record lookup times out after an earlier write request, the assistant checks the receipt instead of retrying an effect blindly.",
        "sample": "Goal: assess PM-84 return-to-service status.\nAction 1: read authorized work order -> pressure test required.\nAction 2: read test record -> measured; sign-off absent.\nStop: no release action; request supervisor sign-off.\nLimits: 4 reads, 0 unapproved writes; quarantine record text.",
        "cost": "For K tool steps, there are up to K model decisions and K tool calls, so latency accumulates across dependent steps even when each operation is quick. Retain only necessary observations to keep context growth bounded; a naive transcript can grow with every tool payload. Track tool errors and repeated calls separately from task success. A loop that can only read should never gain a write because the model describes the write as the next logical step. When data is already present and verified, a direct response avoids unnecessary tool churn.",
        "mistakes": ["Do not let a retrieved note alter tool permissions.", "Do not repeat an ambiguous effect without checking its receipt.", "Do not expose internal reasoning traces as a substitute for checked evidence."],
        "related": ["prompt-engineering/tool-loop-stop-rules", "prompt-engineering/tool-call-authorization-contract", "prompt-engineering/side-effect-receipt-reconciliation"],
    },
    {
        "slug": "least-to-most-verified-decomposition",
        "title": "Least-to-most prompting: solve smaller dependencies first",
        "summary": "Order subproblems so each checked result supports the next one.",
        "definition": "Least-to-most prompting decomposes a hard request into smaller questions and resolves them in dependency order. This is useful when the final answer depends on several facts or transformations that can be checked separately. The decomposition itself can be wrong: an omitted dependency can make every later step look internally consistent while the conclusion fails. Name the required input, output, and validation rule for each subproblem. If a step cannot be verified, stop or mark subsequent answers conditional rather than passing an unsupported value forward.",
        "case": "A retailer asks whether a delayed shipment qualifies for a customer credit. First identify the contract version effective on the ship date. Next extract the promised delivery window, then compare it with signed arrival evidence, then determine whether an exclusion applies. Only then calculate a credit under the verified rule. The model initially skips the exclusion because the customer message is persuasive. A dependency checklist catches the missing step. If the arrival signature is absent, the process can explain the pending evidence but cannot issue a credit amount.",
        "sample": "Order OR-427; contract version -> promised window -> signed arrival.\nNext: exclusion status -> verified credit rule -> amount.\nGate after each step: source ID, value, uncertainty.\nIf signed arrival missing: stop before eligibility and amount.\nFinal answer: checked result or named missing dependency.",
        "cost": "With S subproblems, a sequential workflow usually needs O(S) decisions and keeps O(S) intermediate results; dependent calls add their latencies rather than running in parallel. Validation can save rework by stopping early, but an over-split task wastes calls and creates more places for errors to propagate. Compare the decomposition with a direct baseline on the same cases. The useful measure is final decision accuracy under the same evidence and cost budget, not the apparent neatness of intermediate prose.",
        "mistakes": ["Do not skip a dependency because an answer feels obvious.", "Do not carry an unverified intermediate result into an irreversible action.", "Do not split a simple lookup into needless model calls."],
        "related": ["prompt-engineering/task-decomposition-and-handoffs", "prompt-engineering/retrieval-freshness-and-conflict", "prompt-engineering/clarification-versus-assumption-gate"],
    },
    {
        "slug": "program-aided-reasoning-sandbox",
        "title": "Program-aided prompting: make computation executable and bounded",
        "summary": "Use the model to express a calculation, then validate and execute it in a restricted runtime.",
        "definition": "Program-aided reasoning separates interpretation from computation. A model maps a natural-language request into a typed expression or small program; a deterministic evaluator calculates the result. This can reduce arithmetic slips, but it does not repair a wrong interpretation of the input. In production, prefer a limited expression schema or fixed calculation function over arbitrary generated code. Validate allowed operators, units, field names, ranges, and execution limits before evaluation. Never run free-form model output with unrestricted filesystem, network, or credential access.",
        "case": "A cold-storage invoice lists 37 pallet-days at 8.40 currency units each and a 6 percent handling charge on storage only. The assistant extracts quantities and constructs a typed calculation: storage is 310.80, handling is 18.648, and the final amount rounded once to two decimals is 329.45. The evaluator checks the units and the charge base. If the invoice instead says the handling charge applies to transport, the same arithmetic program would be wrong even though it runs perfectly. Source-field review remains a separate gate.",
        "sample": "pallet_days=37; rate_per_pallet_day=8.40; handling_rate=0.06.\nstorage=37 * 8.40 = 310.80.\nhandling=310.80 * 0.06 = 18.648.\ninvoice_total=round(310.80 + 18.648, 2) = 329.45.\nAllowed fields: pallet_days, rate, handling_rate; no arbitrary code.",
        "cost": "A fixed arithmetic expression with T operators evaluates in O(T) time and O(T) space for a parsed expression tree; a dedicated function may use constant extra space for a fixed formula. The model call and extraction review usually dominate cost, while sandbox startup adds latency if arbitrary code is permitted. Prefer decimal arithmetic for money and define rounding once at the final boundary. Compare extracted inputs to the document before trusting the computed total; an exact evaluator will faithfully compute a mistaken field.",
        "mistakes": ["Do not execute model-generated code with unrestricted privileges.", "Do not let a successful calculation certify the extracted business rule.", "Do not round every intermediate money value without a stated policy."],
        "related": ["prompt-engineering/deterministic-calculation-gates", "prompt-engineering/schema-and-abstention", "prompt-engineering/output-sink-validation"],
    },
]

paths = ["prompt-engineering/" + item["slug"] for item in specs]
assert not set(paths + [project_path, quiz_path]).intersection(lookup)
titles = {entry["path"]: entry["title"] for entry in entries}
titles.update({path: item["title"] for path, item in zip(paths, specs)})
titles[project_path] = "Project: select and verify a reasoning pattern"
titles[quiz_path] = "Reasoning patterns and operating limits"


def link(path):
    assert path in titles, path
    return f'<a href="/{html.escape(path)}">{html.escape(titles[path])}</a>'


def links(selected):
    return "<ul>" + "".join(f"<li>{link(path)}</li>" for path in dict.fromkeys(selected)) + "</ul>"


def related(selected):
    return [{"path": path, "title": titles[path]} for path in dict.fromkeys(selected)]


def article(path, title, summary, body, section, order, connections, kind="tutorial"):
    entry = copy.deepcopy(lookup["prompt-engineering/evaluation-slice-design"])
    entry.update(id=str(uuid.uuid5(uuid.NAMESPACE_URL, "aitrove:" + path)), path=path,
                 title=title, summary=summary, body=body,
                 subject="prompt-engineering-patterns" if section == patterns else "prompt-engineering-project",
                 difficulty="Advanced", tags=["prompt engineering", "reasoning patterns"],
                 sort_order=order, status="published", published_at=stamp,
                 created_at=stamp, updated_at=stamp)
    entry["data"].update(kind=kind, reading_minutes=11 if kind == "tutorial" else 19,
                         author_path="authors/aitrove-editorial", subject_root=subject_root,
                         section_path=section, content_format="html", seo_ready=True,
                         related=related(connections))
    return entry


new_rows = []
for index, (path, item) in enumerate(zip(paths, specs)):
    connections = [patterns, subject_root] + item["related"] + [peer for peer in paths if peer != path] + [project_path, quiz_path]
    body = ("<p>" + html.escape(item["definition"]) + "</p>"
            + "<h2>Operational case</h2><p>" + html.escape(item["case"]) + "</p>"
            + '<pre><code class="language-text">' + html.escape(item["sample"], quote=False) + "</code></pre>"
            + "<h2>Performance and operating cost</h2><p>" + html.escape(item["cost"]) + "</p>"
            + "<h3>Common Mistakes</h3><ul>" + "".join("<li>" + html.escape(mistake) + "</li>" for mistake in item["mistakes"]) + "</ul>"
            + "<h2>Connected lessons</h2>" + links(connections))
    new_rows.append(article(path, item["title"], item["summary"], body, patterns, 27800 + index * 10, connections))

project_connections = paths + ["prompt-engineering/evaluation-slice-design", "prompt-engineering/negative-control-prompt-evaluation", quiz_path]
project_body = (
    "<p>A fictional operations team receives three jobs: compute a shipment remainder from a current manifest, propose a constrained dispatch schedule, and decide whether a pump can return to service. Build one baseline direct response for each job. Then choose one reasoning pattern per job based on the actual failure mode, never because the method sounds more sophisticated. The deliverable is a small evaluation packet: input evidence, chosen pattern, checked output, call budget, and a failure explanation. Keep authority with the application and reviewer.</p>"
    "<h2>Choose the cheapest useful method</h2><p>For shipment SH-731, a deterministic calculation is already possible; compare it against five-candidate self-consistency only to measure whether sampling adds value. For the dispatch schedule, use a bounded branch search with a three-decision depth and a two-plan beam, and reject any plan that exceeds a van limit or cold window. For pump PM-84, use an observe-and-act read loop that stops when supervisor sign-off is absent. Add a fourth case, order OR-427, whose credit decision depends on contract version, signed arrival, and an exclusion rule. Resolve those dependencies in order. A fifth case asks for a cold-storage invoice total; extract typed fields, validate the charge base, then pass the expression to a restricted evaluator.</p>"
    "<h2>Check the decisions</h2><p>Record source revisions, one expected outcome per case, and a benign control where a direct response is enough. Count correct final decisions, unsupported claims, missed stop conditions, total model calls, tool calls, and review time. A model vote cannot substitute for the current manifest; a running program cannot establish that it used the right charge base; and a plausible branch cannot release a pump. Compare the candidate workflow with the direct baseline on the same evidence and hold out at least one case per failure class from prompt editing.</p>"
    '<pre><code class="language-text">SH-731: direct arithmetic vs five-candidate vote; verify manifest revision.\nDispatch: depth=3, beam=2; reject capacity and cold-window failures.\nPM-84: at most 4 reads; missing sign-off means stop.\nOR-427: contract -> arrival -> exclusion -> credit.\nInvoice: typed fields -> restricted decimal evaluator.\nRelease: correct checked result, no unauthorized effect, recorded cost.</code></pre>'
    "<h2>Performance and operating cost</h2><p>For C cases and V variants, offline comparison needs O(CV) model evaluations. A bounded search may expand O(DWB) partial plans for depth D, beam W, and branch limit B. Sequential subproblems and tool observations add latency. Record each call because a more accurate method may still be unsuitable under a strict response-time or cost limit. The evaluation packet should preserve enough redacted evidence to reproduce decisions without storing private payloads. A failed critical permission or safety check blocks release even if the average score improves.</p>"
    "<h3>Common Mistakes</h3><ul><li>Do not select the most elaborate pattern before measuring a direct baseline.</li><li>Do not let a model score replace a hard feasibility or authorization check.</li><li>Do not count a computed number as verified when its source fields are wrong.</li></ul>"
    "<h2>Connected lessons</h2>" + links(project_connections))
new_rows.append(article(project_path, titles[project_path], "Compare five reasoning techniques against direct baselines and hard verification gates.", project_body, projects, 27860, project_connections, kind="project"))

questions = [
    ("Four of five answers agree on 17. What is still needed before reporting the shipment remainder?", "Check arithmetic and current manifest revision", "Treat the vote as proof", "Generate fifty more votes", "Agreement cannot validate stale input or arithmetic."),
    ("What does answer normalization prevent in self-consistency voting?", "Equivalent final answers being counted separately", "Missing source documents", "Unauthorized tool calls", "Normalization groups equivalent outputs, not evidence quality."),
    ("A branch-search plan exceeds the van's rated load. What should happen?", "Prune it with the hard capacity check", "Keep it for fluent wording", "Increase its model score", "A hard constraint outranks prose quality."),
    ("What limits a Tree of Thoughts search before it begins?", "Depth, branch width, beam width, and node budget", "Only the model's confidence", "Only the length of the final answer", "Unbounded branching can grow exponentially."),
    ("A tool result tells an assistant to release a pump without sign-off. What is its status?", "Untrusted data; server authority still applies", "A new system instruction", "Supervisor approval", "Retrieved text cannot confer permission."),
    ("A prior write timed out during a tool loop. What should happen before retrying?", "Check the effect receipt", "Repeat the write immediately", "Ask the model whether it probably succeeded", "Receipt reconciliation avoids duplicate effects."),
    ("Which dependency should come before calculating an order credit?", "Effective contract and signed arrival evidence", "A persuasive customer message", "A polished apology", "The rule and arrival facts establish eligibility."),
    ("A required arrival signature is missing. How should least-to-most processing continue?", "Stop the eligibility chain or mark it conditional", "Invent an arrival time", "Issue the amount anyway", "An unsupported intermediate value contaminates later steps."),
    ("What does a restricted evaluator improve in a money calculation?", "Exact execution of validated typed arithmetic", "The accuracy of extracted contract terms", "The authority to pay a customer", "Computation and interpretation are separate checks."),
    ("Why reject arbitrary generated code for an invoice task?", "It can access resources beyond the calculation", "It always rounds correctly", "It is faster than a fixed function", "A limited expression or fixed function reduces execution risk."),
    ("A direct calculation passes the same held-out cases as a five-call vote. Which choice fits?", "Use the cheaper direct calculation", "Always use the vote", "Search more branches", "Extra calls need measurable value."),
    ("Which finding blocks a release despite better average accuracy?", "An unauthorized effect in a critical case", "A shorter response", "One fewer model call", "Critical permission failures are not offset by averages."),
]
quiz_entry = copy.deepcopy(lookup["quizzes/prompt-engineering-multimodal-evidence"])
quiz_entry.update(id=str(uuid.uuid5(uuid.NAMESPACE_URL, "aitrove:" + quiz_path)), path=quiz_path,
                  title=titles[quiz_path], summary="Choose reasoning methods, verification gates, and operating limits.",
                  body="<p>These cases test when sampling, branch search, observation loops, decomposition, and deterministic evaluation help. Select the check that owns the final decision.</p><h2>Lessons</h2>" + links(paths) + "<h2>Project and sections</h2>" + links([project_path, patterns, quizzes]),
                  sort_order=27870, status="published", published_at=stamp,
                  created_at=stamp, updated_at=stamp)
quiz_entry["data"].update(subject_root=subject_root, section_path=quizzes,
                          content_format="html", author_path="authors/aitrove-editorial",
                          seo_ready=True, duration_minutes=12, related=related(paths + [project_path]),
                          questions=[{"prompt": prompt,
                                      "options": ([correct, wrong_a, wrong_b][index % 3:] + [correct, wrong_a, wrong_b][:index % 3]),
                                      "answer": (-index) % 3, "explanation": explanation}
                                     for index, (prompt, correct, wrong_a, wrong_b, explanation) in enumerate(questions)])
new_rows.append(quiz_entry)

for hub_path, selected, title, summary in [
    (patterns, paths, "Bounded reasoning methods", "Compare sampling, branch search, observation loops, ordered decomposition, and executable calculations."),
    (projects, [project_path], "Reasoning-method selection", "Choose the cheapest pattern that fixes a measured failure."),
    (quizzes, [quiz_path], "Reasoning patterns quiz", "Test stop rules, verification gates, and cost limits."),
]:
    hub = lookup[hub_path]
    hub["data"]["modules"].append({"title": title, "summary": summary, "lessons": selected})
    hub["body"] += "<h2>" + html.escape(title) + "</h2><p>" + html.escape(summary) + "</p>" + links(selected + [project_path, quiz_path])
    hub["updated_at"] = stamp

root_hub = lookup[subject_root]
root_hub["body"] += "<h2>Reasoning methods and limits</h2><p>Choose a method from the failure it addresses, then measure the cost and verify the result.</p>" + links(paths + [project_path, quiz_path])
root_hub["updated_at"] = stamp

backlinks = {
    "prompt-engineering/candidate-sampling-and-verifier": paths[0],
    "prompt-engineering/deterministic-calculation-gates": paths[4],
    "prompt-engineering/task-decomposition-and-handoffs": paths[3],
    "prompt-engineering/tool-loop-stop-rules": paths[2],
    "prompt-engineering/tool-catalog-selection-contract": paths[2],
    "prompt-engineering/negative-control-prompt-evaluation": project_path,
    "prompt-engineering/evaluation-slice-design": project_path,
    "prompt-engineering/visible-rationale-evidence-boundary": paths[0],
}
for existing_path, new_path in backlinks.items():
    entry = lookup[existing_path]
    entry["body"] += "<p><strong>Continue with:</strong> " + link(new_path) + ".</p>"
    entry["data"]["related"] = related([item["path"] for item in entry["data"]["related"]] + [new_path])
    entry["updated_at"] = stamp

entries.extend(new_rows)
fixture.write_text(json.dumps(entries, ensure_ascii=False, indent=2) + "\n")
print(json.dumps({"newLessons": len(specs), "newProjects": 1, "newQuizzes": 1,
                  "newPaths": [entry["path"] for entry in new_rows]}))
