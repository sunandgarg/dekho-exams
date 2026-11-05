"""Add search relevance and annotation quality prompt curricula."""

import copy
import datetime
import html
import json
import uuid
from pathlib import Path

root = Path(__file__).resolve().parents[1]
fixture = root / "src/data/fixtures.json"
entries = json.loads(fixture.read_text())
lookup = {row["path"]: row for row in entries}
stamp = datetime.datetime.now(datetime.UTC).isoformat()
subject_root = "prompt-engineering/prompt-engineering"
applications = "prompt-engineering/applications"
production = "prompt-engineering/production"
projects = "prompt-engineering/projects"
quizzes = "prompt-engineering/quizzes"

clusters = [
    dict(
        label="Search relevance evaluation", tag="search relevance", order=32700,
        project="prompt-engineering/beacon-search-relevance-project",
        project_title="Project: review Beacon Supply search relevance",
        quiz="quizzes/prompt-engineering-search-relevance-evaluation",
        quiz_title="Search relevance prompt decisions",
        intro="Search relevance evaluation compares a fixed query set, a known catalog snapshot, eligible candidates, human judgments, and observed ranking. Beacon Supply has 47 fictional help and catalog queries. Five return no eligible result and 42 return at least one. A model can draft intent labels and discrepancy notes, while a reviewer validates evidence and a search engineer controls changes to retrieval or ranking.",
        case="Keep the 47-query denominator visible. The five empty queries need separate investigation: missing index data, tokenization, filters, and permissions can all cause an empty set. For one judged query, three of the first five eligible results are relevant, giving precision at five of 3/5 or 0.6. Seven query-document judgments are disputed and cannot be silently scored as irrelevant. Hold the release comparison until those judgments and the candidate pool are versioned.",
        sample="Beacon Supply | query set: 47 | catalog snapshot: C-47\n42 queries have candidates; 5 have no eligible result\nOne judged query: 3 relevant in first 5 -> P@5 = 0.6\nSeven disputed query-document judgments: review queue\nDecision: no aggregate winner from one query",
        cost="For Q queries with K inspected ranks, constructing a top-K judgment sheet is O(QK) comparisons after retrieval. Human judging dominates elapsed time and grows with uncertain pairs. Reusing the same snapshot and judgment policy makes a comparison possible; changing either one requires a new baseline. A single query-level score is evidence about that query, never a population-wide result.",
        mistakes=["Do not call an unjudged document irrelevant.", "Do not infer overall search quality from one query.", "Do not publish a ranking win while disputed labels remain in the release slice."],
        specs=[
            dict(slug="search-query-intent-and-evaluation-slice", title="Search prompts: define query intent and evaluation slices", section=applications,
                 summary="Pin the user task, query population, and catalog snapshot before judging results.",
                 definition="A search evaluation slice is a fixed set of queries grouped by the task the user meant to complete. Record normalized query text, language, device or role when relevant, intent class, catalog snapshot, filters, and expected eligible result type. A prompt may propose intent labels, but it must expose ambiguous queries and preserve the raw wording. A slice drawn only from successful searches cannot measure empty searches or uncommon terminology. The denominator belongs to the query set, not the number of results retrieved.",
                 case="Beacon Supply freezes 47 help and catalog queries at snapshot C-47. Five have no eligible result; they stay in the slice. A query for 'seal 47' may mean a part number or an installation guide, so reviewers keep both candidate intents until a session or owner clarifies the task. The model writes a proposed label and its evidence, not a made-up purchase intent. Role-specific filters are logged with the query because they change what could have been returned.",
                 sample="query_id: BS-Q47\nraw_text: seal 47\nintent_candidates: part lookup | installation help\ncatalog_snapshot: C-47\nrole_filter: contractor\nintent_status: review",
                 cost="Grouping Q queries by a small intent taxonomy is O(Q) record work plus human review for ambiguous cases. Snapshotting the eligible catalog costs storage proportional to indexed records, but prevents later catalog changes from rewriting the test. Retain rare and zero-result queries even if their count makes a headline score less flattering.",
                 mistakes=["Do not discard empty queries from the denominator.", "Do not label ambiguity as certainty because one result looks plausible.", "Do not compare slices built from different catalog snapshots."],
                 related=["prompt-engineering/evaluation-slice-design", "prompt-engineering/retrieval-evidence-selection"]),
            dict(slug="search-relevance-judgment-rubric-and-pooling", title="Search prompts: judge relevance without treating unknown as wrong", section=applications,
                 summary="Build a candidate pool and a relevance rubric with an explicit unjudged state.",
                 definition="A relevance rubric describes what counts as useful for a particular query and intent: exact answer, partial support, related but insufficient, or ineligible. Pool candidates from more than one retrieval or ranking variant so an incumbent system does not define the entire answer key. Every query-document pair needs a stable ID, snapshot, eligibility decision, grade, and judge status. Unjudged is a missing label. It is not the same as a human decision that a document fails the task.",
                 case="For Beacon's 'seal 47' query, a part page and an installation guide enter the candidate pool from different runs. The part page is useful only if the intent is product lookup; the guide is useful for installation help. A third result has not been reviewed. The prompt asks judges to cite the supported task, and the sheet keeps that third result unjudged until review. Seven disputed pairs have separate adjudication IDs rather than being flattened to a majority vote.",
                 sample="BS-Q47 / doc-P17: candidate grade, intent-dependent\nBS-Q47 / doc-G42: candidate grade, intent-dependent\nBS-Q47 / doc-U63: UNJUDGED\njudgment_version: J-47\nconflicts: adjudication queue",
                 cost="Pooling R runs over Q queries at K results requires O(RQK) candidate visits before deduplication. Labeling unique pairs costs human time and a ledger of O(U) records for U unique pairs. Pooling reduces dependence on one run but cannot prove every relevant document was found; record the pool construction rule.",
                 mistakes=["Do not score an unjudged pair as a negative.", "Do not let a single system supply all candidate documents.", "Do not merge relevance and permission eligibility into one opaque grade."],
                 related=["prompt-engineering/evaluation-label-disagreement", "prompt-engineering/retrieval-context-packet-coverage-and-claim-mapping"]),
            dict(slug="search-retrieval-coverage-and-zero-results", title="Search prompts: diagnose candidate coverage and zero results", section=applications,
                 summary="Separate an empty eligible set from ranking failure and locate the cause.",
                 definition="Candidate coverage asks whether retrieval produced a potentially useful, permitted item before ranking rearranged the list. An empty result can follow a missing document, stale index, analyzer mismatch, overstrict filter, or permission rule. A prompt should request a bounded diagnostic ledger: query ID, index snapshot, normalized tokens, filter chain, eligible count at each gate, and known answer availability. It must not recommend bypassing access control simply because a relevant private item exists.",
                 case="Beacon has five empty queries among 47. Two have catalog records not yet indexed, one uses an alternate part spelling, one is filtered by a category condition, and one would match only a document the contractor role cannot access. These are fictional diagnostic findings for the project packet, not five identical ranking defects. The permission case remains empty for that role; the proposed fix is a safe public answer or clearer no-result message, not exposure of the private record.",
                 sample="47 queries: 42 with candidates + 5 empty\nempty causes: index lag 2; spelling 1; filter 1; permission 1\npermission empty: do not relax access rule\nowner: index | analyzer | filter | content/permission",
                 cost="Tracing Q queries through G gates costs O(QG) logged gate checks when counts are available. Replaying full retrieval can be more expensive because it touches the index and filter services. Gate counts narrow the investigation, while missing diagnostics should stay unknown rather than be assigned a convenient cause.",
                 mistakes=["Do not call every zero-result query a ranking bug.", "Do not bypass a permission filter for better coverage.", "Do not guess a cause without gate-level evidence."],
                 related=["prompt-engineering/retrieval-permission-change-deletion-and-release-evaluation", "prompt-engineering/prompt-trace-observability"]),
            dict(slug="search-ranking-metrics-and-denominators", title="Search prompts: calculate ranking metrics on judged pairs", section=production,
                 summary="Keep metric arithmetic, judgment coverage, and aggregation rules separate.",
                 definition="Precision at K counts judged relevant items among the first K eligible results when the required judgments are available. A ranking report should name K, query population, relevance threshold, missing-judgment policy, and aggregation method. Graded gain measures require an explicit grade-to-gain rule and a declared ideal ordering; a prompt should never invent either. Put metric arithmetic in code, then ask the model to explain the computed numbers and exclusions. Show judgment coverage alongside the score.",
                 case="One Beacon query has three relevant items in its first five judged results, so precision at five is 0.6. That value says nothing about the other 46 queries. Seven disputed query-document judgments are held out of a release comparison until adjudicated or handled by a predeclared missing-label policy. If a new ranker places an unjudged item high, the sheet requests another judgment instead of quietly treating the item as a miss.",
                 sample="BS-Q12: relevant@5 = [1, 0, 1, 0, 1]\nP@5 = (1 + 0 + 1 + 0 + 1) / 5 = 0.6\nQuery set = 47; displayed metric covers BS-Q12 only\nDisputed pairs = 7; aggregate comparison = pending",
                 cost="Calculating top-K scores for Q fully judged queries is O(QK) time and O(Q) stored per-query summaries. Obtaining missing judgments is the expensive step. Averages can hide failures on rare intents, so keep the slice breakdown and the count of scored queries beside every reported value.",
                 mistakes=["Do not divide by retrieved count when reporting precision at five.", "Do not present one query's 0.6 as an overall score.", "Do not calculate graded metrics without a grade rule and complete required judgments."],
                 related=["prompt-engineering/aggregate-denominator-reconciliation", "prompt-engineering/report-claim-ledger-and-number-reconciliation"]),
            dict(slug="search-click-bias-and-release-guardrails", title="Search prompts: interpret clicks and gate a ranking release", section=production,
                 summary="Treat click logs as biased behavior and require offline plus online guardrails.",
                 definition="A click records exposure and user action, not a clean relevance grade. Position, presentation, prior familiarity, and the absence of a result all affect whether a user clicks. A release review combines a fixed judged set with live signals, segment breakdowns, zero-result rate, permissions checks, and latency. The prompt should draft a decision memo from named measurements and state which evidence is missing. It cannot turn an attractive click-through change into authorization to publish or ignore a safety gate.",
                 case="Beacon's proposed ranker improves clicks on popular part searches but has no adjudicated result for seven disputed pairs, while five empty queries remain under investigation. A mobile contractor segment also has a slower result response. The release memo records the observed click change as a hypothesis, lists the unresolved judgments, and requests segment and latency checks. The engineer holds the rollout until the agreed gates pass; the model neither deploys nor calls clicks proof of relevance.",
                 sample="offline: 7 disputed judgments pending\nempty queries: 5 / 47, causes tracked separately\nonline: clicks by segment, exposure, and position\nguards: permission, no-result rate, latency\nrelease decision: hold until named gates pass",
                 cost="Aggregating E exposure events is O(E) scan work, with additional storage for segment counters. Judged-set comparisons cost O(QK) as configured. Recording exposure and position adds telemetry volume but prevents a misleading interpretation of clicks. Release gates should use measured thresholds chosen before reading the outcome.",
                 mistakes=["Do not use clicks as unbiased relevance labels.", "Do not average away a failing user segment.", "Do not invent a release threshold after seeing the result."],
                 related=["prompt-engineering/online-prompt-experiment-stop-rules", "prompt-engineering/analytics-prompt-metric-and-event-contract"]),
        ],
        backlinks=[("prompt-engineering/retrieval-evidence-selection",0),("prompt-engineering/evaluation-label-disagreement",1),("prompt-engineering/retrieval-permission-change-deletion-and-release-evaluation",2),("prompt-engineering/aggregate-denominator-reconciliation",3),("prompt-engineering/online-prompt-experiment-stop-rules",4)],
        questions=[
            ("What is the search query denominator?", "All 47 frozen queries", "Only 42 queries with candidates", "Only clicked queries", "The fixed slice includes empty searches."),
            ("What is an unjudged result?", "A pair with no completed relevance label", "A confirmed irrelevant result", "A permitted document", "Missing judgment is not a negative grade."),
            ("Why pool candidates from multiple runs?", "To reduce dependence on one run's coverage", "To prove all relevant documents exist", "To remove human review", "A single run limits what judges see."),
            ("What can cause an empty eligible set?", "Index, analyzer, filter, or permission gates", "Only ranking order", "Only click position", "Retrieval gates must be inspected separately."),
            ("How is Beacon's one P@5 computed?", "Three relevant among five gives 0.6", "Three divided by 47 gives 0.6", "Five divided by three gives 0.6", "The metric uses the five inspected ranks for that query."),
            ("Can 0.6 describe all 47 queries?", "No, it is one judged query", "Yes, by extrapolation", "Yes, because K is five", "The other queries have not been scored in this example."),
            ("How should seven disputed pairs be handled?", "Adjudicate or apply a predeclared policy", "Silently call them irrelevant", "Remove all empty queries", "A changed label policy can alter the comparison."),
            ("Does a private match justify removing a permission filter?", "No, keep access control and inspect safe alternatives", "Yes, for coverage", "Yes, for offline scoring", "Relevance does not grant access."),
            ("What is a click in this evaluation?", "An exposure-dependent behavior signal", "A clean human relevance grade", "Proof of task completion", "Position and presentation change clicks."),
            ("What should accompany an aggregate score?", "Scored-query count and slice breakdown", "Only the largest segment", "A model confidence adjective", "Coverage and segments make the denominator visible."),
            ("Who authorizes ranking deployment?", "The release owner after agreed gates", "The prompt model", "Any click increase", "A generated memo is not deployment approval."),
            ("What is the current project decision?", "Hold the comparison while disputed judgments remain", "Declare the new ranker the winner", "Ignore the seven pairs", "The packet lacks completed release evidence."),
        ],
    ),
    dict(
        label="Annotation quality workflow", tag="annotation quality", order=32900,
        project="prompt-engineering/meridian-annotation-quality-project",
        project_title="Project: adjudicate Meridian support labels",
        quiz="quizzes/prompt-engineering-annotation-quality-workflow",
        quiz_title="Annotation quality prompt decisions",
        intro="Annotation quality is a workflow for defining a labelable unit, applying a versioned rubric, recording uncertainty, and resolving disagreement. Meridian has 47 fictional support-ticket excerpts for a refund-versus-replacement routing task. Two reviewers label each excerpt independently. Their first-pass agreement is 40 of 47, about 85.1 percent; that is raw agreement, not proof that the labels are correct.",
        case="Seven excerpts disagree. Three lack earlier thread context, and four contain wording that could support refund or replacement. After context review and owner adjudication, five receive final labels and two remain unknown. The final ledger has 45 labeled excerpts and two explicit unknowns. Do not train or score on the two unknowns as if they were negatives. Lock the rubric, input scope, and holdout allocation before using the examples in a prompt or evaluation set.",
        sample="47 excerpts = 40 first-pass agreements + 7 disagreements\n7 disagreements = 3 missing context + 4 ambiguous wording\n5 adjudicated to final label; 2 remain UNKNOWN\nfinal: 45 labeled + 2 UNKNOWN\nraw agreement: 40 / 47 = 85.1% (rounded)",
        cost="Two independent passes require O(2N) annotation actions for N items; adjudication adds O(D) review for D disagreements. The ledger requires O(N) storage. The extra review cost is justified where a wrong routing label changes customer treatment. Raw agreement alone can look high under an imbalanced label distribution, so inspect confusion by class and keep an unknown state.",
        mistakes=["Do not report raw agreement as correctness.", "Do not force the two unknown excerpts into a majority class.", "Do not expose private customer text in a prompt when a redacted unit is enough."],
        specs=[
            dict(slug="annotation-task-unit-and-label-taxonomy", title="Annotation prompts: define the unit and label taxonomy", section=applications,
                 summary="State exactly what is labeled and what each category means.",
                 definition="An annotation prompt needs a single unit of work, a finite label set, decision criteria, exclusions, and an unknown route. Ticket-level and message-level labels answer different questions. Define whether the label describes customer intent, authorized next action, or final case outcome; these cannot be used interchangeably. Each label should have observable evidence and a counterexample that separates it from its nearest neighbor. Version the taxonomy before annotators begin so later changes are traceable.",
                 case="Meridian labels one redacted ticket excerpt at a time for requested resolution: refund, replacement, or unknown. A customer who asks whether an item can be repaired is not automatically asking for a replacement. A later agent promise is not the customer's original intent. The prompt returns a label proposal with an evidence span and a scope note. If the excerpt lacks the relevant message, it returns unknown and requests the minimum earlier context.",
                 sample="unit: one redacted ticket excerpt\nlabels: REFUND | REPLACEMENT | UNKNOWN\ntarget: customer's requested resolution\nexclude: agent promise and final case outcome\noutput: label + evidence span + missing-context flag",
                 cost="Applying a stable taxonomy to N units is O(N) decisions, with O(N) stored labels and evidence spans. Ambiguous units increase review time rather than algorithmic complexity. A small taxonomy with a genuine unknown route reduces false precision without hiding which cases need a human.",
                 mistakes=["Do not mix customer request with final resolution.", "Do not label an entire thread when the unit is an excerpt.", "Do not define categories only by their names."],
                 related=["prompt-engineering/classification-rubric-and-unknown-label", "prompt-engineering/input-normalization-contract"]),
            dict(slug="annotation-input-privacy-and-context-window", title="Annotation prompts: minimize private input while preserving context", section=applications,
                 summary="Use redacted evidence spans and request only context needed to label a unit.",
                 definition="Annotation input should contain a stable item ID, scoped text, permitted metadata, and a record of redaction. Names, addresses, payment details, and unrelated messages rarely help classify a requested resolution. Strip those fields before model-assisted drafting or reviewer export. Context still matters: a phrase such as 'send another' may refer to a replacement only when a preceding message identifies the product and request. Mark missing context rather than letting the model fabricate it.",
                 case="Three Meridian disagreements come from excerpts missing earlier thread turns. The reviewer retrieves only the preceding relevant message through an approved view, preserving redaction. Two excerpts now have clear requested outcomes, while one stays unknown after context review. The audit ledger stores the excerpt ID and context receipt rather than copying a full private conversation into the prompt. The other four disagreements concern ambiguous wording, not missing data.",
                 sample="item: M-17\nexcerpt: 'Could you send another?'\nredaction: customer identity removed\ncontext_request: preceding product/resolution message only\nstatus: UNKNOWN until scoped context is reviewed",
                 cost="Redacting B input bytes is O(B) processing; retrieving the few needed messages adds I/O proportional to those messages, not the whole archive. Narrow context lowers exposure and annotation noise. Keep the redaction version so reviewers can distinguish a truly absent fact from one intentionally withheld.",
                 mistakes=["Do not paste full ticket histories by default.", "Do not infer missing context from phrasing alone.", "Do not erase the fact that a field was redacted."],
                 related=["prompt-engineering/privacy-and-data-minimization", "prompt-engineering/evidence-id-traceability"]),
            dict(slug="annotation-double-labeling-and-agreement", title="Annotation prompts: measure agreement before adjudication", section=applications,
                 summary="Record independent labels, class confusion, and the raw-agreement denominator.",
                 definition="Double labeling gives two independent judgments for the same item under the same rubric version. Hide the first label from the second reviewer to avoid anchoring. Compute raw agreement as matching first-pass labels divided by double-labeled items, then inspect which label pairs disagree. Agreement measures consistency, not truth. Imbalanced categories can inflate it; chance-adjusted measures need their own assumptions and a complete contingency table. The prompt can format the ledger but deterministic code should count matches.",
                 case="Meridian's two reviewers agree on 40 of 47 excerpts and disagree on seven. Raw agreement is 40/47, approximately 85.1 percent. That number does not show whether both reviewers misunderstood refund policy. The seven disagreements are listed by item ID and label pair. Three need preceding context and four need a clearer rule for language that could request either refund or replacement. No reviewer sees the other's label before the first pass closes.",
                 sample="double-labeled items: 47\nfirst-pass agreements: 40\ndisagreements: 7\nraw agreement: 40 / 47 = 0.851063...\nquality verdict: requires adjudication and class review",
                 cost="Comparing N paired labels is O(N) time and O(N) ledger storage; class-pair counts need O(C squared) counters for C labels. Independent passes roughly double annotation labor. That cost exposes a weak rubric before its labels become a hidden dependency in evaluation.",
                 mistakes=["Do not call 85.1 percent accuracy.", "Do not let the second reviewer see the first label.", "Do not hide class-specific disagreement behind one average."],
                 related=["prompt-engineering/evaluation-label-disagreement", "prompt-engineering/qualitative-label-disagreement-and-adjudication"]),
            dict(slug="annotation-adjudication-and-rubric-versioning", title="Annotation prompts: adjudicate conflicts and version the rule", section=production,
                 summary="Resolve disagreements with evidence and preserve an unknown outcome.",
                 definition="Adjudication is a recorded decision by an owner using the task definition, relevant context, and a rubric version. The record must preserve both initial labels, the evidence considered, final outcome or unknown state, rationale, and whether the rubric changed. If guidance changes, flag older items that might be affected and rerun a bounded review. A prompt can draft a conflict summary; it should not erase minority reasoning or silently convert unresolved cases to the dominant category.",
                 case="Meridian investigates seven conflicts. Three are linked to missing context and four to wording that permits two interpretations. After scoped context and owner review, five receive final labels; two stay unknown because evidence cannot distinguish outcomes. The ledger therefore has 45 labeled items, counting 40 initial agreements and five resolved conflicts. The two unknowns are excluded from label-dependent scoring under the declared policy, while their frequency remains visible.",
                 sample="first-pass: 40 agreed + 7 disputed = 47\nresolved disputes: 5\nunresolved UNKNOWN: 2\nfinal labeled: 40 + 5 = 45\nrecord: initial labels, context receipt, owner, rule version",
                 cost="Adjudicating D conflicts costs O(D) ledger visits plus human investigation. If a rule revision touches A prior items, re-review adds O(A) work. Preserving the old labels and rule versions costs storage but allows teams to explain why a metric changed after a guideline edit.",
                 mistakes=["Do not delete dissenting labels after a final decision.", "Do not treat unknown as a failure to be filled by guesswork.", "Do not compare label counts across rubric versions without a migration rule."],
                 related=["prompt-engineering/evaluation-label-disagreement", "prompt-engineering/report-claim-ledger-and-number-reconciliation"]),
            dict(slug="annotation-holdout-leakage-and-drift-review", title="Annotation prompts: protect holdouts and sample drift", section=production,
                 summary="Keep evaluation labels out of examples and monitor changed input patterns.",
                 definition="A labeled item should have provenance, rubric version, split assignment, and permitted use. If an evaluation excerpt or its near duplicate appears in a few-shot prompt, the held-out score no longer measures transfer to unseen cases. Freeze split assignment before tuning. In production, sample by time, channel, and uncommon outcomes so a new support policy or product phrase does not disappear in an overall agreement rate. Route changed patterns to human review before relabeling an old test set.",
                 case="Meridian reserves a holdout from the 45 finally labeled excerpts and keeps the two unknowns in a separate review queue. A near-duplicate of one holdout appears in a proposed few-shot prompt, so that example is replaced before evaluation. A later support channel starts using 'swap it' where older tickets said 'send another'. The prompt flags the phrase for rubric review and samples that channel explicitly; it does not retroactively rewrite frozen labels to improve a score.",
                 sample="item: M-28 | rubric: R-47 | split: HOLDOUT\nfew-shot near-duplicate: reject\nunknown queue: 2 items, not negative labels\ndrift slice: new-channel 'swap it' requests\naction: owner review before rubric update",
                 cost="Checking N items against H held-out fingerprints is O(N+H) expected work with indexed hashes, while semantic near-duplicate review has a higher human cost. Sampling E live items is O(E) scan work before quotas. Preserve lineage so a prompt revision cannot quietly use its own test answers.",
                 mistakes=["Do not place held-out excerpts in examples.", "Do not treat the two unknowns as negative cases.", "Do not overwrite historical labels to match new policy without versioning."],
                 related=["prompt-engineering/evaluation-data-leakage", "prompt-engineering/synthetic-evaluation-holdout-and-contamination"]),
        ],
        backlinks=[("prompt-engineering/classification-rubric-and-unknown-label",0),("prompt-engineering/privacy-and-data-minimization",1),("prompt-engineering/qualitative-label-disagreement-and-adjudication",2),("prompt-engineering/evaluation-label-disagreement",3),("prompt-engineering/evaluation-data-leakage",4)],
        questions=[
            ("What is Meridian's annotation unit?", "One redacted ticket excerpt", "A complete customer account", "The final agent resolution", "The unit and target are fixed before labeling."),
            ("What does UNKNOWN mean?", "Evidence cannot support a requested-resolution label", "The customer asked for refund", "The majority label", "Unknown preserves a genuine evidence gap."),
            ("Why hide the first reviewer's label?", "To keep the second first pass independent", "To remove item IDs", "To avoid versioning", "Seeing the first label can anchor the second judgment."),
            ("What is first-pass raw agreement?", "40 divided by 47, about 85.1 percent", "45 divided by 47, exactly 85.1 percent", "Seven divided by 40", "Only 40 of 47 independent pairs initially match."),
            ("Does raw agreement prove label correctness?", "No, both reviewers can share the same error", "Yes, at 85 percent", "Yes, if labels are private", "Consistency and correctness answer different questions."),
            ("How many excerpts initially disagree?", "Seven", "Two", "Forty", "The paired ledger records 47 minus 40 agreements."),
            ("How many conflicts lacked earlier context?", "Three", "Four", "Seven", "Three conflicts need a scoped earlier message."),
            ("How many conflicts concern ambiguous wording?", "Four", "Three", "Forty", "The seven conflicts split into three and four."),
            ("How many final labels exist after adjudication?", "Forty-five", "Forty", "Forty-seven", "Five conflicts resolve in addition to 40 agreements."),
            ("What happens to the two unresolved items?", "They remain explicit UNKNOWN cases", "They become refunds", "They become held-out negatives", "The evidence does not support either target label."),
            ("Why reject a holdout near-duplicate in few-shot examples?", "It would leak evaluation material into the prompt", "It costs one extra token", "It changes the customer request", "A held-out test should remain unseen during tuning."),
            ("What should a rubric revision retain?", "Old labels, owner rationale, and version", "Only the new majority counts", "No item identifiers", "Versioned provenance makes comparisons interpretable."),
        ],
    ),
]

new_paths = []
for cluster in clusters:
    new_paths.extend("prompt-engineering/" + spec["slug"] for spec in cluster["specs"])
    new_paths.extend([cluster["project"], cluster["quiz"]])
assert len(new_paths) == len(set(new_paths)) and not set(new_paths) & lookup.keys()
titles = {row["path"]: row["title"] for row in entries}
for cluster in clusters:
    titles.update({"prompt-engineering/" + spec["slug"]: spec["title"] for spec in cluster["specs"]})
    titles[cluster["project"]] = cluster["project_title"]
    titles[cluster["quiz"]] = cluster["quiz_title"]


def link(path):
    assert path in titles, path
    return f'<a href="/{html.escape(path)}">{html.escape(titles[path])}</a>'


def links(paths):
    return "<ul>" + "".join("<li>" + link(path) + "</li>" for path in dict.fromkeys(paths)) + "</ul>"


def related(paths):
    return [{"path": path, "title": titles[path]} for path in dict.fromkeys(paths)]


def article(path, title, summary, body, section, order, connections, tag, kind="tutorial"):
    row = copy.deepcopy(lookup["prompt-engineering/evaluation-slice-design"])
    subjects = {applications: "prompt-engineering-applications", production: "prompt-engineering-production", projects: "prompt-engineering-project"}
    row.update(id=str(uuid.uuid5(uuid.NAMESPACE_URL, "aitrove:" + path)), path=path, title=title,
               summary=summary, body=body, subject=subjects[section], difficulty="Advanced",
               tags=["prompt engineering", tag], sort_order=order,
               status="published", published_at=stamp, created_at=stamp, updated_at=stamp)
    row["data"].update(kind=kind, reading_minutes=11 if kind == "tutorial" else 18,
                       author_path="authors/aitrove-editorial", subject_root=subject_root,
                       section_path=section, content_format="html", seo_ready=True,
                       related=related(connections))
    return row


new_rows = []
for cluster in clusters:
    paths = ["prompt-engineering/" + spec["slug"] for spec in cluster["specs"]]
    for index, (path, spec) in enumerate(zip(paths, cluster["specs"])):
        connections = [spec["section"], subject_root] + spec["related"] + [other for other in paths if other != path] + [cluster["project"], cluster["quiz"]]
        body = ("<p>" + html.escape(spec["definition"]) + "</p>"
                + "<h2>Operational case</h2><p>" + html.escape(spec["case"]) + "</p>"
                + '<pre><code class="language-text">' + html.escape(spec["sample"], quote=False) + "</code></pre>"
                + "<h2>Performance and review cost</h2><p>" + html.escape(spec["cost"]) + "</p>"
                + "<h3>Common Mistakes</h3><ul>" + "".join("<li>" + html.escape(item) + "</li>" for item in spec["mistakes"]) + "</ul>"
                + "<h2>Connected lessons</h2>" + links(connections))
        new_rows.append(article(path, spec["title"], spec["summary"], body, spec["section"], cluster["order"] + index * 10, connections, cluster["tag"]))

    project_connections = paths + [cluster["quiz"], "prompt-engineering/evaluation-slice-design", "prompt-engineering/report-claim-ledger-and-number-reconciliation"]
    project_body = ("<p>" + html.escape(cluster["intro"]) + "</p>"
                    + "<h2>Review the packet</h2><p>" + html.escape(cluster["case"]) + "</p>"
                    + '<pre><code class="language-text">' + html.escape(cluster["sample"], quote=False) + "</code></pre>"
                    + "<h2>Performance and review cost</h2><p>" + html.escape(cluster["cost"]) + "</p>"
                    + "<h3>Common Mistakes</h3><ul>" + "".join("<li>" + html.escape(item) + "</li>" for item in cluster["mistakes"]) + "</ul>"
                    + "<h2>Related lessons</h2>" + links(project_connections))
    new_rows.append(article(cluster["project"], cluster["project_title"], "Apply the " + cluster["label"].lower() + " evidence contract to a fictional packet.", project_body, projects, cluster["order"] + 80, project_connections, cluster["tag"], "project"))

    quiz = copy.deepcopy(lookup["quizzes/prompt-engineering-security-alert-triage"])
    quiz.update(id=str(uuid.uuid5(uuid.NAMESPACE_URL, "aitrove:" + cluster["quiz"])), path=cluster["quiz"],
                title=cluster["quiz_title"], summary="Test evidence, arithmetic, boundaries, and release decisions in " + cluster["label"].lower() + ".",
                body="<p>Choose the decision supported by the recorded packet.</p><h2>Lessons</h2>" + links(paths) + "<h2>Project and sections</h2>" + links([cluster["project"], applications, production, quizzes]),
                sort_order=cluster["order"] + 90, status="published", published_at=stamp, created_at=stamp, updated_at=stamp)
    quiz["data"].update(subject_root=subject_root, section_path=quizzes, content_format="html",
                        author_path="authors/aitrove-editorial", seo_ready=True, duration_minutes=12,
                        related=related(paths + [cluster["project"]]),
                        questions=[{"prompt": prompt,
                                    "options": ([correct, wrong_a, wrong_b][index % 3:] + [correct, wrong_a, wrong_b][:index % 3]),
                                    "answer": (-index) % 3, "explanation": explanation}
                                   for index, (prompt, correct, wrong_a, wrong_b, explanation) in enumerate(cluster["questions"])])
    new_rows.append(quiz)

    for hub_path, selected, title, summary in [
        (applications, paths[:3], cluster["label"] + " inputs", "Define the evidence and task unit before findings."),
        (production, paths[3:], cluster["label"] + " review", "Verify comparisons and release boundaries."),
        (projects, [cluster["project"]], cluster["label"] + " project", "Apply the lesson sequence to a fictional packet."),
        (quizzes, [cluster["quiz"]], cluster["label"] + " decisions", "Test the packet's decision gates."),
    ]:
        hub = lookup[hub_path]
        hub["data"]["modules"].append({"title": title, "summary": summary, "lessons": selected})
        hub["body"] += "<h2>" + html.escape(title) + "</h2><p>" + html.escape(summary) + "</p>" + links(selected + [cluster["project"], cluster["quiz"]])
        hub["updated_at"] = stamp
    lookup[subject_root]["body"] += "<h2>" + html.escape(cluster["label"] + " prompts") + "</h2><p>Follow evidence from intake to a bounded decision.</p>" + links(paths + [cluster["project"], cluster["quiz"]])
    lookup[subject_root]["updated_at"] = stamp

    for old_path, new_index in cluster["backlinks"]:
        row = lookup[old_path]
        row["body"] += "<p><strong>Continue with:</strong> " + link(paths[new_index]) + ".</p>"
        row["data"]["related"] = related([item["path"] for item in row["data"].get("related", [])] + [paths[new_index]])
        row["updated_at"] = stamp

entries.extend(new_rows)
fixture.write_text(json.dumps(entries, ensure_ascii=False, indent=2) + "\n")
print(json.dumps({"newLessons": 10, "newProjects": 2, "newQuizzes": 2, "newPaths": [row["path"] for row in new_rows]}))
