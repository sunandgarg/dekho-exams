"""Add original qualitative user-research prompt lessons and connected practice."""

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
applications = "prompt-engineering/applications"
production = "prompt-engineering/production"
projects = "prompt-engineering/projects"
quizzes = "prompt-engineering/quizzes"
project_path = "prompt-engineering/parcel-pickup-interview-analysis-project"
quiz_path = "quizzes/prompt-engineering-qualitative-user-research"

specs = [
    dict(slug="interview-prompt-consent-and-purpose-bound-input", title="Interview prompts: limit transcript use to the study purpose", section=applications,
         summary="Check permission and minimize participant detail before analysis.",
         definition="A research transcript is not a general-purpose prompt asset. Record the study question, permitted uses, retention boundary, participant identity key, and any excluded material before sending an excerpt to a model. Remove names, contact details, and incidental third-party stories unless they are needed for the analysis and permitted by the study. A prompt should refuse a request to repurpose interview text for outreach or a different study without a fresh authorization check. The application, not the prose instruction alone, decides which records the analyst may access. Use stable pseudonymous participant IDs so later coding can be traced without spreading direct identifiers.",
         case="A fictional Parcel Window study has 12 volunteers discussing pickup-window selection. Interview P-07 mentions a neighbor's phone number while describing a delivery problem. The analyst keeps the pickup timing excerpt but removes that unrelated number before model review. The study permits aggregate product analysis; a marketing request to create a contact list from the transcripts falls outside that purpose. The prompt returns a purpose mismatch and records that no participant text was exported for the new request.",
         sample="Study: Parcel Window pickup experience\nAllowed: coded product findings from 12 interviews\nP-07 excerpt: pickup window confusing; third-party number removed\nMarketing contact extraction: purpose mismatch -> stop",
         cost="Reviewing N excerpts for scope and identifying data takes O(N) passes, with a second human check for uncertain redactions. Keeping only needed segments lowers prompt size and exposure. The review is worth doing before analysis because a later summary cannot undo disclosure of an unnecessary phone number. Store the permission decision with the study record; never infer permission from the mere presence of a transcript file.",
         mistakes=["Do not treat access to a transcript as permission for every downstream use.", "Do not leave incidental third-party identifiers in an analysis batch.", "Do not let a prompt replace application-level access checks."],
         related=["prompt-engineering/privacy-and-data-minimization", "prompt-engineering/research-question-eligibility-prompt-contract"]),
    dict(slug="interview-prompt-segment-and-speaker-boundaries", title="Interview prompts: preserve speaker and segment boundaries", section=applications,
         summary="Keep each excerpt tied to a participant, question, and time span.",
         definition="Coding requires a stable unit of evidence. Split transcripts into segments that retain participant ID, speaker, interview question, time span, and a segment identifier. Keep enough surrounding turns to resolve pronouns and corrections, but do not join different participants into one fabricated quote. An automatic transcript may misassign a speaker or omit a negation; mark such spans uncertain and compare them with the recording when available. The model can propose segment boundaries, while the researcher resolves uncertain attribution. Each downstream code and finding should point back to the approved segment version.",
         case="At 12:14, P-03 says a pickup window was 'fine' and immediately corrects that statement after describing a missed collection. A one-sentence clip would reverse the meaning. The analyst keeps the correction in segment P03-S18, records the time range, and marks a noisy word for audio review. P-08's later complaint about the same screen stays in its own segment; merging those two voices would falsely suggest one person described both events.",
         sample="P03-S18 | speaker P-03 | 12:14-12:42\nInitial: window was fine\nCorrection: collection missed after the window changed\nAudio uncertainty: one word pending review\nP08-S09: separate participant, separate segment",
         cost="Segmenting T transcript turns is O(T) before any comparison between segments. Wider context improves interpretation but increases token cost, so attach nearby turns only where they change meaning. Versioning a corrected transcript adds storage but prevents a code from pointing at text that no longer exists. A model output without participant and segment keys is cheap to produce and expensive to audit.",
         mistakes=["Do not code the first sentence while dropping its immediate correction.", "Do not merge similar remarks from different participants into one quote.", "Do not silently repair uncertain speech without checking the recording."],
         related=["prompt-engineering/audio-transcription-uncertainty", "prompt-engineering/caption-transcript-evidence-contract"]),
    dict(slug="interview-prompt-codebook-operational-definitions", title="Interview prompts: write a codebook with inclusion rules", section=applications,
         summary="Define what qualifies for each code, including near misses.",
         definition="A code label is too vague to support consistent analysis. Give each code an operational definition, an inclusion test, an exclusion test, a representative excerpt, and a near miss. Let a segment hold more than one code when independent claims support them. Keep a version number for the codebook and distinguish new inductive candidates from approved codes. Ask the model for the segment ID, candidate code, evidence span, and reason; a researcher approves additions and ambiguous assignments. Do not interpret a broad word such as 'late' as a missed pickup if the speaker only describes a slow page.",
         case="The Parcel Window team defines WINDOW_CLARITY for uncertainty about the pickup interval shown to the customer. P-07 says the app displayed 'morning' without an end time, so the segment qualifies. P-02 says the confirmation page loaded slowly but understood the interval; that is a near miss. An early model draft tags both as WINDOW_CLARITY. The researcher rejects the second assignment and adds a separate PAGE_LATENCY candidate only after checking the rest of the interviews.",
         sample="Code WINDOW_CLARITY v2\nInclude: uncertain displayed pickup interval\nExclude: page delay with understood interval\nP07-S11 -> include, missing end time\nP02-S06 -> exclude; PAGE_LATENCY candidate",
         cost="Applying K candidate codes to N segments can require O(NK) comparisons in a direct pass. A compact codebook reduces repeated interpretation but may miss a genuinely new pattern, so reserve a candidate-code lane and review it periodically. Version changes require recoding affected segments; the cost is explicit and preferable to mixing incompatible definitions in a single count.",
         mistakes=["Do not use a label without an inclusion and exclusion test.", "Do not force every new observation into an existing code.", "Do not compare counts from different codebook versions without recoding."],
         related=["prompt-engineering/dataset-intake-column-contract", "prompt-engineering/qualitative-label-disagreement-and-adjudication"]),
    dict(slug="qualitative-label-disagreement-and-adjudication", title="Interview prompts: keep coder disagreement visible", section=production,
         summary="Record competing readings and resolve them against the segment.",
         definition="Two coders may read an interview segment differently for sound reasons. Capture each independent label, its supporting words, the codebook version, and the reason for disagreement before discussion. A model suggestion is another proposal, not an authoritative tie breaker. Adjudicate by checking the full segment and the code definition; if the evidence cannot settle the question, mark it unresolved and avoid a confident thematic claim. Report agreement only for an explicitly defined unit and label set. Do not turn a high agreement number into proof that the codes are meaningful or that the sample represents a wider population.",
         case="Coder A marks P03-S18 as WINDOW_CLARITY because the revised time surprised the participant. Coder B marks it as NOTIFICATION_TIMING because the participant describes learning of the change too late. The full segment supports both mechanisms, so the review assigns two codes with separate evidence spans. Another unclear segment remains unresolved pending audio. The review log keeps the original assignments, the final decision, and who made it; a model does not erase the disagreement.",
         sample="P03-S18 | codebook v2\nCoder A: WINDOW_CLARITY | span 12:14-12:23\nCoder B: NOTIFICATION_TIMING | span 12:25-12:42\nReview: both codes, separate spans\nP09-S04: unresolved until audio check",
         cost="A second independent pass roughly doubles coding time for the reviewed subset, and adjudication grows with disputed segments D rather than every segment N. Sample a meaningful range of cases, including near misses, instead of only easy examples. The audit trail adds a small amount of storage and prevents silent consensus. It also reveals whether a codebook revision, rather than a different model prompt, is the right fix.",
         mistakes=["Do not let one model output overwrite independent coder decisions.", "Do not force a single label when distinct supported mechanisms coexist.", "Do not present unresolved segments as agreed evidence."],
         related=["prompt-engineering/interview-prompt-codebook-operational-definitions", "prompt-engineering/evaluation-label-disagreement"]),
    dict(slug="qualitative-theme-evidence-and-counterexample-ledger", title="Interview prompts: build a theme evidence ledger", section=production,
         summary="Tie each proposed theme to segments, exclusions, and contrary cases.",
         definition="A theme is an interpretation across coded material, not a list of memorable quotes. For each candidate theme, maintain a claim, supporting participant-segment IDs, codebook version, the researcher’s interpretation, and counterexamples or boundaries. Ask the model to retrieve evidence for and against the candidate before drafting prose. If one statement is vivid but isolated, keep it as a case rather than saying the pattern recurred. A theme may include tension: some participants can value a wide pickup window while others need a narrow one. The finding must explain that variation instead of flattening it.",
         case="The Parcel Window team proposes 'vague windows block planning.' Five of 12 participants describe an unclear interval, and two of those also explain why it affected a handoff. P-11 says the broad interval was useful because someone was always home; this contrary case belongs in the ledger. A first draft says 'everyone wanted exact times.' The evidence ledger rejects that wording and narrows the claim to planning problems among the five participants who raised it, with P-11 as a boundary case.",
         sample="Theme: vague windows can impede pickup planning\nSupport: 5 participant IDs with verified segment links\nMechanism: 2 describe missed handoff planning\nCounterexample: P-11 prefers a broad interval\nRejected claim: everyone wanted exact times",
         cost="Building an index over N coded segments is O(N); checking a candidate theme against all relevant records is another O(N) scan unless indexed by code and participant. The scan is valuable because selective quote retrieval can hide a counterexample. Keep the ledger compact enough for a reviewer to open every cited span. An attractive paragraph without traceable supporting and contrary cases should not pass release.",
         mistakes=["Do not call a vivid isolated quote a recurring theme.", "Do not hide participants whose accounts conflict with the proposed claim.", "Do not treat a code name as the theme interpretation."],
         related=["prompt-engineering/research-synthesis-release-and-reproduction-gate", "prompt-engineering/qualitative-label-disagreement-and-adjudication"]),
    dict(slug="qualitative-participant-denominator-and-repeat-counts", title="Interview prompts: count people, not repeated excerpts", section=production,
         summary="Keep the participant denominator separate from segment frequency.",
         definition="A single participant can mention the same problem several times. If the claim is about participants, deduplicate coded segments by participant ID before counting; if it is about mentions, say so and keep that separate measure. Preserve the eligible interview denominator, missing records, and recruitment scope. Qualitative interviews can show mechanisms and variation, but a small purposeful sample does not produce a population prevalence estimate. The prompt may compute descriptive counts from an explicit ledger, while a deterministic check reconciles those counts to distinct participant IDs.",
         case="The Parcel Window ledger has 47 coded excerpts from 12 participants. Nine excerpts about window clarity come from five distinct participants; four of those excerpts are P-07 revisiting one event. Reporting '9 of 12 customers' would count text spans as people and overstate the finding. The study can say five of the 12 interviewed participants raised unclear windows, with the recruitment context nearby. Two participants mention a language barrier, but their remarks remain a separate finding rather than being folded into window clarity.",
         sample="Eligible interviews: 12\nCoded excerpts: 47\nWINDOW_CLARITY excerpts: 9\nDistinct WINDOW_CLARITY participants: 5\nLANGUAGE_BARRIER participants: 2\nPopulation prevalence: not estimated",
         cost="Deduplicating M coded excerpts with a participant-ID set is O(M) expected time and O(P) memory for P distinct participants. Manual verification remains necessary for misassigned speakers and duplicated interview records. Descriptive counts are cheap; false precision is costly because it can make a narrow exploratory study look like a survey. Preserve both segment and participant counts so a reviewer can reproduce the statement.",
         mistakes=["Do not divide quote counts by participant counts.", "Do not call 5 of 12 a population rate.", "Do not combine separate codes merely to make a larger number."],
         related=["prompt-engineering/aggregate-denominator-reconciliation", "prompt-engineering/deterministic-calculation-gates"]),
    dict(slug="qualitative-finding-to-product-decision-gate", title="Interview prompts: turn bounded findings into testable decisions", section=production,
         summary="State what the interviews support and what needs further testing.",
         definition="A research summary should separate observation, interpretation, design hypothesis, proposed action, and measurement plan. The model can draft a decision memo from an approved evidence ledger, but it should not present a product change as proven effective merely because participants described a problem. Attach every factual claim to participant-segment keys and every count to a reconciled denominator. Note whose experience is missing from the sample. A product owner can choose a reversible prototype, a usability test, or further recruitment, but the prompt must leave that decision and its trade-offs visible.",
         case="Five interviewed participants describe ambiguous pickup windows; two describe a language barrier; P-11 prefers a flexible interval. The team proposes displaying both a plain-language range and an optional narrower alert, then testing comprehension and successful pickup planning with participants who have varied schedules and languages. The memo does not say that the design will reduce missed pickups. It says the interview evidence motivates the prototype and identifies what an experiment must measure before rollout.",
         sample="Observed: 5 of 12 interviewees raised window clarity\nBoundary: P-11 preferred flexibility\nHypothesis: explicit range plus optional alert aids planning\nNext check: comprehension and pickup planning test\nRollout claim: withheld until measured",
         cost="Drafting from indexed findings is O(F + E) for F findings and E cited evidence spans, but reviewer effort grows with the number of claims and contested excerpts. A short memo with open evidence links is cheaper to verify than a long narrative with hidden assumptions. Product testing adds time, yet it distinguishes a plausible remedy from a demonstrated one. Preserve a release record so later results do not silently rewrite what the interviews originally showed.",
         mistakes=["Do not describe a proposed feature as an observed improvement.", "Do not remove the participant who challenges the preferred interpretation.", "Do not make the model the final owner of the product decision."],
         related=["prompt-engineering/research-synthesis-release-and-reproduction-gate", "prompt-engineering/qualitative-theme-evidence-and-counterexample-ledger"]),
]

paths = ["prompt-engineering/" + spec["slug"] for spec in specs]
assert not set(paths + [project_path, quiz_path]) & lookup.keys()
titles = {entry["path"]: entry["title"] for entry in entries}
titles.update({path: spec["title"] for path, spec in zip(paths, specs)})
titles[project_path] = "Project: analyze Parcel Window pickup interviews"
titles[quiz_path] = "Qualitative interview prompt decisions"


def link(path):
    return f'<a href="/{html.escape(path)}">{html.escape(titles[path])}</a>'


def links(selected):
    return "<ul>" + "".join(f"<li>{link(path)}</li>" for path in dict.fromkeys(selected)) + "</ul>"


def related(selected):
    return [{"path": path, "title": titles[path]} for path in dict.fromkeys(selected)]


def article(path, title, summary, body, section, order, connections, kind="tutorial"):
    row = copy.deepcopy(lookup["prompt-engineering/evaluation-slice-design"])
    subjects = {applications: "prompt-engineering-applications", production: "prompt-engineering-production", projects: "prompt-engineering-project"}
    row.update(id=str(uuid.uuid5(uuid.NAMESPACE_URL, "aitrove:" + path)), path=path, title=title,
               summary=summary, body=body, subject=subjects[section], difficulty="Advanced",
               tags=["prompt engineering", "qualitative research"], sort_order=31600 + order,
               status="published", published_at=stamp, created_at=stamp, updated_at=stamp)
    row["data"].update(kind=kind, reading_minutes=11 if kind == "tutorial" else 18,
                       author_path="authors/aitrove-editorial", subject_root=subject_root,
                       section_path=section, content_format="html", seo_ready=True,
                       related=related(connections))
    return row


new_rows = []
for index, (path, spec) in enumerate(zip(paths, specs)):
    connections = [spec["section"], subject_root] + spec["related"] + [other for other in paths if other != path] + [project_path, quiz_path]
    body = ("<p>" + html.escape(spec["definition"]) + "</p>"
            + "<h2>Operational case</h2><p>" + html.escape(spec["case"]) + "</p>"
            + '<pre><code class="language-text">' + html.escape(spec["sample"], quote=False) + "</code></pre>"
            + "<h2>Performance and review cost</h2><p>" + html.escape(spec["cost"]) + "</p>"
            + "<h3>Common Mistakes</h3><ul>" + "".join("<li>" + html.escape(item) + "</li>" for item in spec["mistakes"]) + "</ul>"
            + "<h2>Connected lessons</h2>" + links(connections))
    new_rows.append(article(path, spec["title"], spec["summary"], body, spec["section"], index * 10, connections))

project_connections = paths + ["prompt-engineering/research-question-eligibility-prompt-contract", "prompt-engineering/aggregate-denominator-reconciliation", quiz_path]
project_body = (
    "<p>Analyze a fictional Parcel Window study about choosing parcel pickup times. There are 12 consented interviews and 47 coded excerpts. The allowed use is aggregate product research. Build a reproducible, human-reviewed analysis from bounded transcript segments, not a contact list or a marketing audience. The deliverable is a decision memo with evidence links, disagreement records, counterexamples, and a testable next step.</p>"
    "<h2>Prepare and code the records</h2><p>Remove an unrelated third-party phone number from P-07's transcript before model analysis. Keep P03-S18 as one contextual segment because P-03 corrects an initial claim; mark its noisy word for audio review. Use codebook v2: WINDOW_CLARITY includes uncertain displayed intervals and excludes a slow page when the interval was understood. Coder A and coder B assign different codes to P03-S18; the review keeps both WINDOW_CLARITY and NOTIFICATION_TIMING, each tied to its own span. P09-S04 stays unresolved until the recording is checked.</p>"
    "<h2>Reconcile themes and propose a check</h2><p>Nine window-clarity excerpts come from five distinct participants, including four repeated mentions by P-07. Two participants report a language barrier. P-11 prefers a broad pickup interval; the counterexample stays beside the proposed theme. State 'five of the 12 interviewed participants' only as a sample description, not a population rate. Propose a plain-language range with an optional narrower alert. Test comprehension and pickup planning before claiming the feature improves outcomes.</p>"
    '<pre><code class="language-text">Study: 12 interviews; 47 coded excerpts\nWINDOW_CLARITY: 9 excerpts, 5 distinct participants\nLANGUAGE_BARRIER: 2 distinct participants\nCounterexample: P-11 prefers flexibility\nP09-S04: unresolved audio\nDecision: prototype range plus optional alert; measure before rollout</code></pre>'
    "<h2>Performance and review cost</h2><p>Scope screening and segmenting are O(N) in the transcript records; direct coding against K codes can be O(NK). Participant deduplication across M coded excerpts is O(M) expected time with a set. Human reviewers should inspect every disputed span and a sample of accepted labels. The project passes only when each theme has segment references, its contrary cases, a stable codebook version, reconciled counts, and an explicit boundary between interview evidence and product hypothesis.</p>"
    "<h3>Common Mistakes</h3><ul><li>Do not export incidental identifiers for an unrelated use.</li><li>Do not discard P-03's correction or P-11's counterexample.</li><li>Do not count nine excerpts as nine people.</li><li>Do not claim a prototype has already reduced missed pickups.</li></ul>"
    "<h2>Related lessons</h2>" + links(project_connections))
new_rows.append(article(project_path, titles[project_path], "Code a fictional pickup study, reconcile conflicting interpretations, and draft a bounded decision memo.", project_body, projects, 80, project_connections, "project"))

questions = [
    ("May the pickup interviews be reused to build a marketing contact list?", "No; check the study's permitted purpose", "Yes, if a model can extract names", "Yes, because the file exists", "Access to a transcript does not grant every downstream use."),
    ("What should happen to an incidental neighbor phone number?", "Remove it from the analysis input", "Keep it to make the story vivid", "Put it in the theme title", "Unneeded third-party data should not enter the prompt."),
    ("Why keep P-03's correction in the same segment?", "It changes the meaning of the initial statement", "It increases quote count", "It removes a speaker ID", "The nearby correction supplies necessary context."),
    ("What is required for a usable codebook entry?", "Inclusion and exclusion tests with examples", "A short label alone", "Only the model's preferred wording", "Operational boundaries make coding decisions reviewable."),
    ("A slow page with an understood interval is what for WINDOW_CLARITY?", "A near miss to exclude", "A definite inclusion", "Proof of a missed pickup", "The code concerns interval understanding, not loading speed."),
    ("How should two supported codes on P03-S18 be handled?", "Keep both with distinct evidence spans", "Force one label at random", "Delete coder disagreement", "Different mechanisms can coexist within one segment."),
    ("What does an unresolved noisy segment contribute to a confident theme?", "Nothing until the uncertainty is reviewed", "A guaranteed supporting quote", "A population estimate", "Uncertain attribution should remain visible."),
    ("How should P-11's preference for a broad interval be used?", "Record it as a counterexample and boundary", "Omit it from the memo", "Rewrite it as agreement", "Contrary cases limit the scope of a theme."),
    ("Nine clarity excerpts from five participants support which count?", "Five interviewed participants raised clarity", "Nine of 12 people raised clarity", "Nine population percentage points", "Segment frequency differs from participant frequency."),
    ("Can five of 12 interviews be reported as customer prevalence?", "No, it describes this recruited sample", "Yes, as a population rate", "Yes, if the quote is vivid", "A qualitative sample does not establish population prevalence."),
    ("What is the status of a range-plus-alert design?", "A hypothesis for prototype testing", "A proven improvement", "A direct participant quote", "Interviews motivate a candidate design but do not prove its effect."),
    ("What should a decision memo link to?", "Segment IDs, codebook version, counts, and counterexamples", "Only a polished executive claim", "Only model confidence", "Traceability makes the interpretation and its limits reviewable."),
]
quiz = copy.deepcopy(lookup["quizzes/prompt-engineering-location-dispatch"])
quiz.update(id=str(uuid.uuid5(uuid.NAMESPACE_URL, "aitrove:" + quiz_path)), path=quiz_path,
            title=titles[quiz_path], summary="Test transcript scope, coding, disagreement, evidence, counts, and product claims.",
            body="<p>Choose the interview-analysis decision supported by the study record and its evidence ledger.</p><h2>Lessons</h2>" + links(paths) + "<h2>Project and sections</h2>" + links([project_path, applications, production, quizzes]),
            sort_order=31690, status="published", published_at=stamp, created_at=stamp, updated_at=stamp)
quiz["data"].update(subject_root=subject_root, section_path=quizzes, content_format="html",
                    author_path="authors/aitrove-editorial", seo_ready=True, duration_minutes=12,
                    related=related(paths + [project_path]),
                    questions=[{"prompt": prompt,
                                "options": ([correct, wrong_a, wrong_b][index % 3:] + [correct, wrong_a, wrong_b][:index % 3]),
                                "answer": (-index) % 3, "explanation": explanation}
                               for index, (prompt, correct, wrong_a, wrong_b, explanation) in enumerate(questions)])
new_rows.append(quiz)

for hub_path, selected, title, summary in [
    (applications, paths[:3], "Interview input and coding", "Bound transcript use, preserve speaker context, and define codes."),
    (production, paths[3:], "Qualitative analysis and decisions", "Adjudicate labels, retain counterexamples, reconcile people, and gate claims."),
    (projects, [project_path], "Parcel Window interview study", "Apply the full analysis to a fictional pickup study."),
    (quizzes, [quiz_path], "Interview analysis decisions", "Test evidence and interpretation boundaries."),
]:
    hub = lookup[hub_path]
    hub["data"]["modules"].append({"title": title, "summary": summary, "lessons": selected})
    hub["body"] += "<h2>" + html.escape(title) + "</h2><p>" + html.escape(summary) + "</p>" + links(selected + [project_path, quiz_path])
    hub["updated_at"] = stamp

lookup[subject_root]["body"] += "<h2>Qualitative interview prompts</h2><p>Trace participant evidence from transcript intake to a bounded product decision.</p>" + links(paths + [project_path, quiz_path])
lookup[subject_root]["updated_at"] = stamp

backlinks = {
    "prompt-engineering/privacy-and-data-minimization": paths[0],
    "prompt-engineering/research-question-eligibility-prompt-contract": paths[0],
    "prompt-engineering/audio-transcription-uncertainty": paths[1],
    "prompt-engineering/dataset-intake-column-contract": paths[2],
    "prompt-engineering/retrieval-freshness-and-conflict": paths[4],
    "prompt-engineering/aggregate-denominator-reconciliation": paths[5],
    "prompt-engineering/research-synthesis-release-and-reproduction-gate": paths[6],
}
for old_path, new_path in backlinks.items():
    entry = lookup[old_path]
    entry["body"] += "<p><strong>Continue with:</strong> " + link(new_path) + ".</p>"
    entry["data"]["related"] = related([item["path"] for item in entry["data"].get("related", [])] + [new_path])
    entry["updated_at"] = stamp

entries.extend(new_rows)
fixture.write_text(json.dumps(entries, ensure_ascii=False, indent=2) + "\n")
print(json.dumps({"newLessons": len(specs), "newProjects": 1, "newQuizzes": 1,
                  "newPaths": [entry["path"] for entry in new_rows]}))
