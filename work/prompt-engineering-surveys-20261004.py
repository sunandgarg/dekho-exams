"""Add original survey-design and survey-analysis prompt lessons."""

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
project_path = "prompt-engineering/meridian-pickup-survey-review-project"
quiz_path = "quizzes/prompt-engineering-survey-design-analysis"

specs = [
    dict(slug="survey-prompt-population-frame-and-invitation-contract", title="Survey prompts: define the population and invitation frame", section=applications,
         summary="Separate the people of interest from the contacts actually invited.",
         definition="A survey prompt should name the decision, target population, eligibility rule, invitation frame, recruitment channel, field period, and unit of analysis. A contact export is not the population merely because it is convenient. The model can identify gaps in a proposed frame and draft a recruitment brief, but it cannot make an opt-in group representative by wording the invitation more carefully. Store one invitation ID per eligible person and decide how duplicates, bounced messages, and unknown eligibility will be counted before fieldwork. Do not let a later summary silently substitute respondents for everyone the product serves.",
         case="Meridian Parcel wants to understand pickup-window preferences among customers who used pickup in the last 30 days. Its contact list contains 240 unique invitation records, all from customers who enabled email notices. Customers who use pickup but lack email notices are outside that frame. The study memo names that gap. The assistant may draft a neutral invitation for those 240 contacts, yet the final report cannot claim to describe every Meridian customer or every pickup user. A duplicated address is resolved before invitation so the person is not counted twice.",
         sample="Target: recent pickup users\nFrame: 240 unique email-notice contacts\nExcluded: pickup users without email notices\nUnit: one eligible person\nClaim boundary: invited frame, not all customers",
         cost="Deduplicating N contact records by stable participant key is O(N) expected time and O(N) memory. Checking frame coverage may require a separate population count and review of excluded channels. The extra intake work protects the meaning of every later percentage. Prompt text cannot repair coverage gaps after responses arrive; keep the frame manifest and recruitment version attached to the analysis.",
         mistakes=["Do not call the email-contact frame the entire customer population.", "Do not count duplicate invitation addresses as separate people.", "Do not invent eligibility for an unverified contact."],
         related=["prompt-engineering/research-question-eligibility-prompt-contract", "prompt-engineering/qualitative-participant-denominator-and-repeat-counts"]),
    dict(slug="survey-prompt-neutral-question-and-construct-check", title="Survey prompts: check wording against the intended construct", section=applications,
         summary="Remove leading language and keep one measurable idea per question.",
         definition="A survey item must state the behavior or opinion it intends to measure, the reference period, and terms respondents can interpret consistently. Ask the model to compare candidate wording with that construct, flag leading adjectives, double questions, hidden assumptions, and ambiguous time spans. The model's preferred wording remains a draft until reviewed with people who resemble the respondents. If a historical trend requires unchanged wording, label the trade-off rather than quietly editing the item and treating the results as comparable. Keep the final question text and version in the data record.",
         case="Meridian initially drafts, 'How frustrating is our confusing pickup window?' That wording presumes both confusion and frustration. The revision asks, 'During your most recent pickup, how clear was the time window shown before confirmation?' with a specified response scale. A separate item asks whether the person could plan around that window; clarity and planning are not forced into one answer. The assistant records the wording change, but it cannot claim that the new item is unbiased without a respondent pilot.",
         sample="Construct A: perceived clarity at most recent pickup\nDraft: 'How frustrating is our confusing pickup window?'\nRevised: 'How clear was the time window shown before confirmation?'\nConstruct B: ability to plan -> separate item\nQuestion version: Q7-v2",
         cost="Reviewing Q items against a construct ledger is O(Q) for a first pass, with human testing adding respondent time. A short question can be expensive if it changes what is measured and invalidates a trend. Preserve the exact text and order at fielding, since a paraphrased label in the report cannot substitute for the instrument respondents actually saw.",
         mistakes=["Do not embed the desired answer in an adjective.", "Do not combine clarity and planning into one response.", "Do not compare two waves after changing question wording without marking the break."],
         related=["prompt-engineering/clarification-versus-assumption-gate", "prompt-engineering/multilingual-equivalence-check"]),
    dict(slug="survey-prompt-response-options-and-skip-logic", title="Survey prompts: validate answer options and skip paths", section=applications,
         summary="Make the form's branch logic and response states explicit.",
         definition="A question can be well worded and still fail because its answer options overlap, omit a plausible choice, or force an ineligible respondent to guess. Specify whether the item permits one answer or several, the ordering rule, an explicit not-applicable path, and the logic that makes each follow-up eligible. Treat unanswered, skipped by design, and declined as distinct values. The model can inspect a branch graph and generate test cases, while the form engine enforces it. Record the instrument version with every response so a later branch change does not mix incompatible records.",
         case="Meridian asks about the most recent pickup. Customers without a pickup in the last 30 days should not see Q7 on window clarity; they follow a not-applicable branch. For eligible users, the scale has one ordered choice from very unclear to very clear plus a separate cannot-recall option. A pilot tester discovers that the form sends cannot-recall users to a planning follow-up anyway. The team repairs the branch and tests both paths before invitation.",
         sample="Q6 recent pickup? yes -> Q7 clarity\nQ6 no -> Q7 skipped by design\nQ7 cannot recall -> no planning follow-up\nQ7 ordered scale -> one response\nMissing answer != branch skip != declined",
         cost="Validating a branch graph with V questions and E transitions is O(V+E); testing representative paths adds cases but catches unreachable or contradictory states. Keep the branch rules in application logic because a prompt cannot ensure runtime behavior. Distinguishing skip reasons costs a few fields and prevents invalid denominators later.",
         mistakes=["Do not force an ineligible respondent to rate an experience they did not have.", "Do not code a branch skip as an unanswered item.", "Do not let a multi-select question masquerade as a single-choice measure."],
         related=["prompt-engineering/dataset-intake-column-contract", "prompt-engineering/aggregate-denominator-reconciliation"]),
    dict(slug="survey-prompt-pilot-test-and-version-freeze", title="Survey prompts: pilot the instrument before fielding", section=production,
         summary="Test comprehension and routing, then freeze the fielded version.",
         definition="A prompt can create a review checklist, but it cannot substitute for people interpreting the survey in context. Pilot with a small group resembling the intended respondents, ask what each question meant to them, and inspect actual branch behavior. Log every issue with the item ID, observed interpretation, severity, proposed repair, owner, and retest result. Once fielding begins, freeze the question and branch version for that wave. An emergency fix may be necessary, but the analysis must mark which respondents saw each version and avoid pooling changed items without a compatibility argument.",
         case="Five Meridian pilot participants see Q7-v1. Two interpret 'pickup window' as the period for collecting a parcel from a locker, while the study means the delivery slot before pickup. The team rewrites the item as Q7-v2, tests it again, and fixes the cannot-recall branch found in the pilot. The 240-person invitation uses only the frozen v2 instrument. If a form fix is made mid-wave, its release time and affected response IDs are recorded rather than hidden in a final percentage.",
         sample="Pilot: 5 people; 2 misread Q7-v1\nRepair: clarify pre-confirmation time window in Q7-v2\nBranch repair: cannot recall skips planning item\nRetest: affected paths checked\nFielded instrument: frozen v2",
         cost="A pilot adds fixed recruitment and review time, while graph regression remains O(V+E) for V items and E branches. That cost is smaller than collecting a full wave whose key item cannot be interpreted. Store instrument checks as executable cases where possible, but preserve the participants' explanations too; a branch test cannot detect a word that readers understand differently.",
         mistakes=["Do not treat a model's wording preference as respondent validation.", "Do not silently edit a fielded item.", "Do not close a pilot issue before the changed path is retested."],
         related=["prompt-engineering/evaluation-slice-design", "prompt-engineering/prompt-evaluation-ci-gate"]),
    dict(slug="survey-prompt-disposition-and-item-denominator", title="Survey prompts: reconcile invitations, submissions, and item denominators", section=production,
         summary="Show exactly who was eligible for each reported answer.",
         definition="Survey analysis needs a disposition ledger. Count invitations, known ineligible contacts, submitted forms, partial forms, completed forms, branch-ineligible people, item nonanswers, and valid answers separately. A percentage for a specific item divides by that item's valid eligible responses, not by every invitation or every opened form. Use deterministic code to reconcile counts and have the prompt explain the result. A submission fraction is descriptive; by itself it does not prove the respondents resemble nonrespondents or justify a population estimate.",
         case="Meridian sends 240 invitations and receives 84 submitted forms. Seven are partial; 77 are complete. Twelve complete respondents had no pickup in the reference period and correctly skipped Q7. Among the remaining 65 eligible respondents, 39 choose the narrower-window option. The item result is 39 of 65, or 60%, among eligible complete respondents. The simple submission fraction is 84 of 240, or 35%. Neither figure describes all pickup users because the invitation frame excludes people without email notices and nonrespondents may differ.",
         sample="Invited 240; submitted 84; partial 7; complete 77\nQ7 branch-ineligible 12; eligible complete 65\nNarrower-window choice 39 / 65 = 60%\nSubmission fraction 84 / 240 = 35%\nPopulation preference: not inferred",
         cost="Counting R response records by disposition and branch is O(R), with O(Q) counters for Q items; checking unique invitation IDs adds O(R) expected memory. The arithmetic is simple, but the eligibility path must be correct before denominators mean anything. Keep both count and denominator next to each reported percentage, including when the number looks less persuasive after missing data is exposed.",
         mistakes=["Do not divide 39 by all 240 invitations for the Q7 item result.", "Do not count branch-ineligible respondents as missing answers.", "Do not equate a 35% submission fraction with absence of nonresponse bias."],
         related=["prompt-engineering/aggregate-denominator-reconciliation", "prompt-engineering/deterministic-calculation-gates"]),
    dict(slug="survey-prompt-open-text-and-private-response-boundary", title="Survey prompts: code open text without exposing respondents", section=production,
         summary="Keep free-text analysis tied to consent, IDs, and a reviewed codebook.",
         definition="Open-text survey answers can contain names, addresses, account details, or stories about other people. Screen and minimize that content before model analysis, then keep pseudonymous response IDs and item versions attached to each retained excerpt. Use a codebook with inclusion and exclusion rules rather than allowing the model to invent a polished theme from a handful of vivid comments. Track how many distinct respondents contributed to each code, separate blank answers from branch skips, and retain contrary comments. A public report should not reproduce a rare identifying quote just because it is memorable.",
         case="One Meridian response names a depot worker while describing a pickup delay. The analyst removes the name and keeps the operational detail under response R-47. Another answer says the broad window is useful because someone is home all day; it is a counterexample to the narrow-window proposal. The codebook marks planning difficulty and preference for flexibility separately. The final memo can summarize both without exposing the worker or pretending that one quote speaks for all 65 eligible respondents.",
         sample="R-47: worker name removed; delay detail retained\nCode PLANNING_DIFFICULTY: reviewed inclusion rule\nCode FLEXIBILITY_PREFERENCE: contrary case retained\nCount unit: distinct respondents, not repeated phrases\nPublic quote: suppress if re-identification risk remains",
         cost="Screening T free-text answers and assigning K candidate codes directly is O(TK); deduplicating by respondent is O(T) expected time. Human review is needed for uncertain redactions, code changes, and rare quotations. A smaller, traceable excerpt set often gives a better analysis than sending every raw answer into a model and hoping the output stays private.",
         mistakes=["Do not put direct identifiers into the analysis batch without need.", "Do not count repeated phrases as separate respondents.", "Do not omit comments that challenge the leading interpretation."],
         related=["prompt-engineering/privacy-and-data-minimization", "prompt-engineering/interview-prompt-codebook-operational-definitions"]),
    dict(slug="survey-prompt-claim-scope-and-release-review", title="Survey prompts: release findings with explicit scope", section=production,
         summary="Pair every finding with its exact question, denominator, and frame.",
         definition="The final survey memo should identify the population of interest, actual invitation frame, field dates, instrument version, response dispositions, item wording, denominator, and limitations. Separate descriptive sample results from population claims and product hypotheses. The model can draft prose from a locked results table, but it should not recompute figures in free text or broaden 'eligible complete respondents' into 'customers.' A reviewer must trace each quoted comment and numerical statement to its response and item record. Release should stop if branch logic, wording versions, or privacy checks remain unresolved.",
         case="Meridian's draft headline says '60% of customers want narrower windows.' The approved table only shows 39 of 65 eligible complete respondents selecting that option. The invitation frame had 240 email-notice contacts, and 84 forms were submitted. The reviewer rewrites the claim to describe the eligible respondents and includes the exact Q7 wording and frame limitation. The team treats a narrower-window control as a design hypothesis, not a proven preference across the full customer base.",
         sample="Claim: 39 of 65 eligible complete respondents selected narrower\nItem: Q7-v2, pre-confirmation window preference\nFrame: invited email-notice contacts only\nNot supported: 60% of all customers\nDecision: test optional narrow-window control",
         cost="Reconciling C claims against an indexed results ledger is O(C) lookups plus review of cited records. The review cost grows when a report hides question versions or branch exclusions, so keep those fields alongside each figure. A concise claim with a visible denominator can be verified faster than a persuasive paragraph that asks readers to guess who answered.",
         mistakes=["Do not replace 'eligible respondents' with 'customers.'", "Do not detach a percentage from its item wording and denominator.", "Do not call a proposed control a measured improvement."],
         related=["prompt-engineering/report-claim-ledger-and-number-reconciliation", "prompt-engineering/qualitative-finding-to-product-decision-gate"]),
]

paths = ["prompt-engineering/" + spec["slug"] for spec in specs]
assert not set(paths + [project_path, quiz_path]) & lookup.keys()
titles = {entry["path"]: entry["title"] for entry in entries}
titles.update({path: spec["title"] for path, spec in zip(paths, specs)})
titles[project_path] = "Project: review Meridian pickup survey findings"
titles[quiz_path] = "Survey prompt decisions"


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
               tags=["prompt engineering", "survey research"], sort_order=31900 + order,
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

project_connections = paths + ["prompt-engineering/aggregate-denominator-reconciliation", "prompt-engineering/privacy-and-data-minimization", quiz_path]
project_body = (
    "<p>Review a fictional Meridian Parcel pickup-window survey before its product memo is released. The target is recent pickup users, but the invitation frame contains only 240 unique contacts who enabled email notices. Build a survey contract, pilot the instrument, reconcile the response ledger, and draft a claim with its exact scope. The model may assist with drafts and checks; the form engine enforces branches and deterministic code calculates counts.</p>"
    "<h2>Inspect wording, branches, and pilot results</h2><p>Replace the leading draft 'How frustrating is our confusing pickup window?' with a neutral clarity item about the most recent pickup. Keep ability to plan as a separate construct. Q6 routes customers without a recent pickup away from Q7; cannot-recall answers do not enter a planning follow-up. Five pilot participants review Q7-v1, and two interpret 'pickup window' as locker collection rather than the pre-confirmation time range. The team clarifies Q7-v2, repairs the branch, retests it, and freezes the instrument before the 240 invitations are sent.</p>"
    "<h2>Reconcile the evidence</h2><p>Meridian receives 84 submitted forms, including seven partial and 77 complete. Twelve complete respondents correctly skip Q7 because they had no recent pickup. The other 65 are eligible complete respondents, and 39 select a narrower window: 39/65 is 60%. The simple submission fraction is 84/240, or 35%; it does not prove absence of nonresponse bias. One open answer contains a depot worker's name, which is removed before coding. A preference for flexible windows stays as a contrary case. The memo cannot say that 60% of customers want a narrow window.</p>"
    '<pre><code class="language-text">Frame: 240 unique email-notice contacts\nPilot: 5 participants; 2 misread Q7-v1; Q7-v2 retested\nSubmitted: 84; partial: 7; complete: 77\nQ7 branch-ineligible: 12; eligible complete: 65\nNarrower choice: 39 / 65 = 60% of eligible complete respondents\nSimple submission fraction: 84 / 240 = 35%</code></pre>'
    "<h2>Performance and review cost</h2><p>Deduplicate N invitations in O(N) expected time, validate a V-question and E-branch form in O(V+E), and reconcile R responses in O(R). The release packet should hold the invitation frame, instrument version, pilot corrections, branch dispositions, exact Q7 wording, counts, private-text review, and the approved claim. A missing denominator or unreviewed version change blocks release even if the generated summary reads well.</p>"
    "<h3>Common Mistakes</h3><ul><li>Do not treat email-notice contacts as all pickup users.</li><li>Do not field leading wording without respondent review.</li><li>Do not count branch skips as missing answers.</li><li>Do not publish an identifying free-text quote or an unsupported population claim.</li></ul>"
    "<h2>Related lessons</h2>" + links(project_connections))
new_rows.append(article(project_path, titles[project_path], "Review survey wording, branch eligibility, response counts, and a bounded product claim.", project_body, projects, 80, project_connections, "project"))

questions = [
    ("Who is covered by Meridian's 240-contact invitation frame?", "Recent pickup users with email notices in that frame", "All Meridian customers", "Every recent pickup user", "A contact frame may exclude people outside its channel."),
    ("Why reject 'our confusing pickup window' in Q7?", "It presumes the experience was confusing", "It is too short", "It contains the word window", "Leading language changes what the item asks."),
    ("Should clarity and ability to plan share one response?", "No, ask them as separate constructs", "Yes, they are identical", "Only if the model prefers it", "One answer cannot clearly identify two distinct mechanisms."),
    ("What happens when Q6 says no recent pickup?", "Q7 is skipped by design", "Q7 is a missing answer", "The respondent must guess", "The form branch controls item eligibility."),
    ("What does the five-person pilot reveal?", "Two participants misread Q7-v1, requiring repair and retest", "The full population prefers one option", "The final 60% figure", "A pilot tests comprehension, not population preference."),
    ("Can Q7-v1 and Q7-v2 be pooled silently?", "No, keep instrument versions and assess compatibility", "Yes, the title is similar", "Yes, if a summary is short", "Wording changes can alter responses."),
    ("How many complete responses were submitted?", "77", "84", "240", "Seven of 84 submissions were partial."),
    ("What is Q7's eligible complete denominator?", "65", "77", "240", "Twelve complete respondents skipped Q7 by branch."),
    ("What is 39 of 65 for the narrow-window item?", "60% of eligible complete respondents", "60% of all customers", "39% of invitees", "The item count uses its eligible answered denominator."),
    ("Does 84 of 240 prove the respondents represent the frame?", "No; 35% submission alone does not settle bias", "Yes, always", "Only if a model says so", "Response and nonresponse can differ."),
    ("How should a named depot worker in open text be handled?", "Remove unneeded identity before model coding", "Publish the quote verbatim", "Use the name as a code", "Private detail is unnecessary to analyze pickup timing."),
    ("What may the release memo claim?", "39 of 65 eligible complete respondents chose narrower", "60% of all customers prefer narrower", "A new control is proven to improve pickup", "The locked result supports a sample-bound item claim."),
]
quiz = copy.deepcopy(lookup["quizzes/prompt-engineering-security-alert-triage"])
quiz.update(id=str(uuid.uuid5(uuid.NAMESPACE_URL, "aitrove:" + quiz_path)), path=quiz_path,
            title=titles[quiz_path], summary="Test survey frames, wording, branches, pilot versions, denominators, and release claims.",
            body="<p>Choose the survey decision supported by the instrument and response ledger.</p><h2>Lessons</h2>" + links(paths) + "<h2>Project and sections</h2>" + links([project_path, applications, production, quizzes]),
            sort_order=31990, status="published", published_at=stamp, created_at=stamp, updated_at=stamp)
quiz["data"].update(subject_root=subject_root, section_path=quizzes, content_format="html",
                    author_path="authors/aitrove-editorial", seo_ready=True, duration_minutes=12,
                    related=related(paths + [project_path]),
                    questions=[{"prompt": prompt,
                                "options": ([correct, wrong_a, wrong_b][index % 3:] + [correct, wrong_a, wrong_b][:index % 3]),
                                "answer": (-index) % 3, "explanation": explanation}
                               for index, (prompt, correct, wrong_a, wrong_b, explanation) in enumerate(questions)])
new_rows.append(quiz)

for hub_path, selected, title, summary in [
    (applications, paths[:3], "Survey input and instrument", "Define the frame, write neutral questions, and validate branches."),
    (production, paths[3:], "Survey testing and release", "Pilot the form, reconcile counts, protect open text, and bound claims."),
    (projects, [project_path], "Meridian pickup survey", "Apply the instrument and response checks to a fictional survey."),
    (quizzes, [quiz_path], "Survey decisions", "Test question and denominator boundaries."),
]:
    hub = lookup[hub_path]
    hub["data"]["modules"].append({"title": title, "summary": summary, "lessons": selected})
    hub["body"] += "<h2>" + html.escape(title) + "</h2><p>" + html.escape(summary) + "</p>" + links(selected + [project_path, quiz_path])
    hub["updated_at"] = stamp

lookup[subject_root]["body"] += "<h2>Survey research prompts</h2><p>Trace an instrument from invitation frame to a bounded finding.</p>" + links(paths + [project_path, quiz_path])
lookup[subject_root]["updated_at"] = stamp

backlinks = {
    "prompt-engineering/research-question-eligibility-prompt-contract": paths[0],
    "prompt-engineering/multilingual-equivalence-check": paths[1],
    "prompt-engineering/dataset-intake-column-contract": paths[2],
    "prompt-engineering/evaluation-slice-design": paths[3],
    "prompt-engineering/aggregate-denominator-reconciliation": paths[4],
    "prompt-engineering/privacy-and-data-minimization": paths[5],
    "prompt-engineering/report-claim-ledger-and-number-reconciliation": paths[6],
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
