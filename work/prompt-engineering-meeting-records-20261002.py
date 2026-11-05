"""Add original meeting-record prompt lessons, project, and quiz."""

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
project_path = "prompt-engineering/beacon-pilot-meeting-record-project"
quiz_path = "quizzes/prompt-engineering-meeting-records"

specs = [
    {
        "slug": "meeting-input-consent-and-evidence-boundary",
        "title": "Meeting prompts: define authorized inputs and evidence",
        "summary": "Bound transcript access, distinguish notes from speech, and retain uncertain spans.",
        "definition": "A meeting-record prompt begins with an input boundary. Name the meeting, authorized transcript and notes, access scope, intended recipients, and retention rule. Treat the transcript as evidence about what was said, not as proof that a plan was approved. Speaker labels and timestamps can be wrong; ask for a traceable span and mark uncertain attribution rather than assigning a statement to the nearest name. The system that captures or shares a meeting must apply its recording and access policy outside the prompt. A recap generator should receive the minimum permitted excerpt needed for its task and should not silently combine another meeting, chat thread, or private document.",
        "case": "In a fictional Beacon API pilot meeting, five attendees discuss a limited deployment to 20 depots. The permitted packet contains the transcript and chair's notes for that meeting only. One sentence at 12:43 is partly inaudible and the transcript labels its speaker as Dana, but the chair's notes do not confirm it. The prompt marks the speaker as uncertain; it does not turn the sentence into Dana's commitment. A separate private staffing note is excluded. The recap is prepared for the five attendees to review before it reaches the larger delivery group. The prompt's access instruction cannot itself grant or revoke transcript permissions.",
        "sample": "Meeting: Beacon API pilot; audience: five attendees.\nAllowed: this meeting's transcript and chair notes only.\nExcluded: private staffing note and other meeting threads.\nSpan 12:43: attribution uncertain; do not assign an owner.\nOutput: draft recap for attendee correction before wider share.",
        "cost": "Scanning T transcript turns and N note items is O(T+N) work before summarization. Long recordings raise token cost and increase the chance that a late decision is buried; segment by agenda item while preserving time and speaker context. Keeping evidence span IDs beside draft claims adds storage proportional to the number of claims, but saves review time when someone disputes a decision. Retention and access rules need enforcement in the meeting system; removing a transcript from a prompt does not delete its stored copy.",
        "mistakes": ["Do not infer consent to record or share from a prompt instruction.", "Do not assign an inaudible statement to a named person without confirmation.", "Do not merge private notes into a recap for a wider audience."],
        "related": ["prompt-engineering/audio-overlap-speaker-review", "prompt-engineering/privacy-and-data-minimization", "prompt-engineering/context-and-trust-boundaries"],
        "section": applications,
    },
    {
        "slug": "meeting-decision-proposal-and-dissent-ledger",
        "title": "Meeting minutes: separate decisions from proposals",
        "summary": "Classify each statement as approved, proposed, rejected, or unresolved with its evidence span.",
        "definition": "A decision ledger prevents a recap from promoting discussion into policy. For every proposed change, record the exact decision question, status, approving authority, evidence span, and any condition. Use distinct labels for approved, proposed, rejected, and unresolved; a confident speaker or silence after a suggestion is not an approval. Preserve material disagreement when it changes the next step. If the transcript and chair's notes conflict, mark the item for attendee review instead of selecting the cleaner story. Draft minutes should state what the meeting established and what remains open, using short sentences that a participant can confirm or correct.",
        "case": "Beacon's chair approves a pilot in 20 depots after rollback validation. A participant proposes rolling out to all 47 depots in the same week, but the chair says the wider rollout is outside today's decision. Another attendee asks whether the pilot can start without the rollback test; no answer is recorded. The recap lists the 20-depot pilot as a conditional decision, the 47-depot rollout as a proposal not approved, and the missing rollback-test answer as unresolved. It does not write 'Beacon rollout approved' because that headline would erase the scope and condition. The approval span is retained for attendee review.",
        "sample": "D1 approved conditionally: 20-depot pilot after rollback validation.\nP1 proposed, not approved: expansion to all 47 depots.\nO1 unresolved: may pilot start before rollback test?\nEvidence: retain transcript spans and chair-note comparison.\nHeadline: pilot decision, not full rollout approval.",
        "cost": "Classifying M material agenda statements is O(M) initial passes, followed by human review of disputed or high-impact entries. A compact ledger is cheaper to correct than a long narrative whose assumptions are woven through several paragraphs. Do not use a vote count unless the meeting actually recorded a vote and its rules. Classification quality matters more than compression ratio: an extra line that preserves a condition is less costly than a brief recap that sends a team toward an unauthorized rollout.",
        "mistakes": ["Do not label a proposal as approved because it went unchallenged for one minute.", "Do not omit a condition from the decision headline.", "Do not erase dissent when it changes who must review the next step."],
        "related": ["prompt-engineering/classification-rubric-and-unknown-label", "prompt-engineering/evidence-id-traceability", "prompt-engineering/evaluation-label-disagreement"],
        "section": applications,
    },
    {
        "slug": "meeting-action-owner-date-confirmation-gate",
        "title": "Meeting actions: verify owner, task, and due date",
        "summary": "Keep unassigned work unassigned until a named owner accepts it.",
        "definition": "An action item is an agreed task with an owner, deliverable, and due point or explicit absence of one. A prompt should extract these fields separately and require evidence for each. A person's question about a task does not assign them the task; a phrase such as 'someone should check' produces an unassigned item. Do not invent calendar dates from 'soon' or map a month/day to a year without meeting context. When owner or deadline is missing, label it missing and ask the meeting chair or participant to confirm. If the application creates tickets, the recap remains a draft until the owner and target system are authorized.",
        "case": "In the Beacon meeting, Dana accepts the rollback validation and says she will send the test result by 10 October 2026. The chair asks who will notify the 20 pilot depots, but no one accepts that task. The ledger records Dana's action with its date and leaves depot notification unassigned with no deadline. The transcript's uncertain 12:43 utterance cannot be used to fill the gap. A generated ticket for Dana's task still needs an authorized submission step and a receipt from the ticket system. The recap does not claim the task is complete merely because a ticket was drafted.",
        "sample": "A1: Dana; rollback validation result; due 10 Oct 2026; accepted.\nA2: notify 20 pilot depots; owner missing; due date missing.\nDo not use uncertain 12:43 speaker to fill A2.\nDraft ticket != submitted ticket; require receipt after authorized create.",
        "cost": "Extracting A candidate actions from T turns can be O(T+A) if candidates retain span pointers. Verification time rises with ambiguous ownership, but that is the cost of not assigning work to the wrong person. Cross-check due dates against the meeting date and time zone when deadlines matter. Ticket creation has an external side effect; validation, authorization, and receipt reconciliation add steps beyond text generation. Keep the output small enough for attendees to correct each action before it enters a work queue.",
        "mistakes": ["Do not assign a task to the person who merely asked about it.", "Do not translate 'soon' into a precise deadline without confirmation.", "Do not call an action complete because a draft ticket exists."],
        "related": ["prompt-engineering/tool-call-authorization-contract", "prompt-engineering/side-effect-receipt-reconciliation", "prompt-engineering/browser-form-preview-submit-boundary"],
        "section": applications,
    },
    {
        "slug": "meeting-recap-revision-and-cross-session-state",
        "title": "Meeting recaps: preserve corrections across sessions",
        "summary": "Track what changed, who confirmed it, and which earlier decision remains in force.",
        "definition": "A recurring-meeting recap should carry forward only confirmed decisions and open actions, with their versions and owners. The prompt must not treat a newer meeting as a blanket replacement for all prior minutes. A correction may change the wording of one action, revoke a decision, or merely add context. Record the original claim, corrected claim, confirming person, and effective meeting. If two sessions conflict, show the conflict until an authorized owner resolves it. In the next recap, distinguish completed, still open, superseded, and newly assigned actions. This keeps the record usable without pasting entire transcripts into every prompt.",
        "case": "One week after Beacon's pilot meeting, a follow-up says the rollback validation passed and Dana's action is complete. The 20-depot pilot may proceed. The 47-depot expansion is still unapproved. The chair corrects an earlier recap that had mistakenly named Dana as owner of depot notification; the action returns to unassigned until Jo accepts it in the follow-up. The revision ledger retains the old wording, the correction, and the meeting where Jo accepted. It does not silently overwrite the earlier minutes or assume the full rollout became approved because the pilot condition cleared.",
        "sample": "Prior D1: 20-depot pilot conditional on rollback test.\nFollow-up: rollback passed -> condition satisfied; pilot may proceed.\nPrior P1: 47-depot expansion remains unapproved.\nCorrection: notification owner Dana -> unassigned -> Jo accepted.\nRecord each state change with confirming meeting and reviewer.",
        "cost": "With H historical decisions and actions, a bounded carry-forward ledger needs O(H) storage; replaying all prior transcript tokens for every meeting grows much faster as the series lengthens. Diffing K changed entries is O(K) after identifiers match. A version ledger adds review work but prevents an attractive recap from erasing accountability. Archive closed actions according to the organization's retention policy instead of carrying them forever. A model summary can suggest what changed; the meeting owner confirms the operative state.",
        "mistakes": ["Do not overwrite an earlier record without an explicit correction trail.", "Do not treat fulfillment of a pilot condition as approval for full expansion.", "Do not carry a guessed owner into the next meeting as settled fact."],
        "related": ["prompt-engineering/conversation-checkpoint-reconstruction", "prompt-engineering/conversation-memory-boundary", "prompt-engineering/evaluation-case-version-ledger"],
        "section": applications,
    },
    {
        "slug": "meeting-recap-release-access-and-correction-gate",
        "title": "Meeting recap release: review scope, access, and corrections",
        "summary": "Verify every decision and action before sharing a recap beyond participants.",
        "definition": "A meeting recap is ready for release only when the permitted audience, decision ledger, action owners, due dates, unresolved items, and sensitive material have been reviewed. The prompt can produce a draft and a verification checklist; it cannot authorize recipients, change recording consent, or send the recap by itself. Ask the chair or designated reviewer to inspect high-impact decisions and participant-attributed commitments. Send a correction route with the released record so attendees can contest an error. If a correction changes a ticket or published plan, update that downstream artifact through its own authorized workflow and record the receipt.",
        "case": "Beacon's draft correctly lists a conditional 20-depot pilot, an unapproved 47-depot proposal, Dana's rollback task, and an unassigned notification task. Before wider distribution, the chair checks the evidence spans and removes a private staffing remark from the summary. Dana confirms her due date. The draft remains with attendees until the chair approves the recipient list. After release, Jo corrects the notification owner and accepts it; the correction is recorded in the next version. A ticket is created only after the work system's approval gate and its receipt is linked to the action ledger.",
        "sample": "Check: D1 condition; P1 not approved; A1 owner/date; A2 unassigned.\nRemove: private staffing remark outside the recap's audience.\nReview: chair approves claims and recipient list.\nCorrection route: attendee reports error; version and downstream ticket updated.\nSend only after authorized release; retain delivery receipt.",
        "cost": "For D decisions, A actions, and R proposed recipients, release review requires O(D+A+R) checks before downstream effects. Human approval adds delay but targets the points where a wrong attribution or unauthorized disclosure has the greatest cost. Keep the shared recap concise and store evidence spans in a restricted review packet; publishing every transcript quote to all recipients expands exposure. Sending and ticket creation are separate side effects, each needing its own success receipt and correction path if later information changes.",
        "mistakes": ["Do not interpret a generated draft as permission to email recipients.", "Do not release a private remark because it appeared in the authorized transcript.", "Do not correct the recap while leaving a contradictory downstream ticket in place."],
        "related": ["prompt-engineering/prompt-release-review-packet", "prompt-engineering/privacy-and-data-minimization", "prompt-engineering/side-effect-receipt-reconciliation"],
        "section": production,
    },
]

paths = ["prompt-engineering/" + spec["slug"] for spec in specs]
assert not set(paths + [project_path, quiz_path]).intersection(lookup)
titles = {entry["path"]: entry["title"] for entry in entries}
titles.update({path: spec["title"] for path, spec in zip(paths, specs)})
titles[project_path] = "Project: review a Beacon pilot meeting record"
titles[quiz_path] = "Meeting-record prompt decisions"


def link(path):
    assert path in titles, path
    return f'<a href="/{html.escape(path)}">{html.escape(titles[path])}</a>'


def links(selected):
    return "<ul>" + "".join(f"<li>{link(path)}</li>" for path in dict.fromkeys(selected)) + "</ul>"


def related(selected):
    return [{"path": path, "title": titles[path]} for path in dict.fromkeys(selected)]


def article(path, title, summary, body, section, order, connections, kind="tutorial"):
    entry = copy.deepcopy(lookup["prompt-engineering/evaluation-slice-design"])
    subject = "prompt-engineering-applications" if section == applications else "prompt-engineering-production" if section == production else "prompt-engineering-project"
    entry.update(id=str(uuid.uuid5(uuid.NAMESPACE_URL, "aitrove:" + path)), path=path,
                 title=title, summary=summary, body=body, subject=subject,
                 difficulty="Advanced", tags=["prompt engineering", "meeting records"],
                 sort_order=29900 + order, status="published", published_at=stamp,
                 created_at=stamp, updated_at=stamp)
    entry["data"].update(kind=kind, reading_minutes=11 if kind == "tutorial" else 19,
                         author_path="authors/aitrove-editorial", subject_root=subject_root,
                         section_path=section, content_format="html", seo_ready=True,
                         related=related(connections))
    return entry


new_rows = []
for index, (path, spec) in enumerate(zip(paths, specs)):
    connections = [spec["section"], subject_root] + spec["related"] + [peer for peer in paths if peer != path] + [project_path, quiz_path]
    body = ("<p>" + html.escape(spec["definition"]) + "</p>"
            + "<h2>Operational case</h2><p>" + html.escape(spec["case"]) + "</p>"
            + '<pre><code class="language-text">' + html.escape(spec["sample"], quote=False) + "</code></pre>"
            + "<h2>Performance and operating cost</h2><p>" + html.escape(spec["cost"]) + "</p>"
            + "<h3>Common Mistakes</h3><ul>" + "".join("<li>" + html.escape(mistake) + "</li>" for mistake in spec["mistakes"]) + "</ul>"
            + "<h2>Connected lessons</h2>" + links(connections))
    new_rows.append(article(path, spec["title"], spec["summary"], body, spec["section"], index * 10, connections))

project_connections = paths + ["prompt-engineering/audio-overlap-speaker-review", "prompt-engineering/tool-call-authorization-contract", "prompt-engineering/prompt-release-review-packet", quiz_path]
project_body = (
    "<p>Draft a reviewed record for a fictional Beacon API pilot meeting and its follow-up. Five attendees discuss a 20-depot pilot, a possible expansion to 47 depots, rollback validation, and depot notification. The permitted packet is the meeting transcript and chair's notes; a private staffing note is excluded. The deliverables are a decision ledger, action ledger, attendee-review draft, correction record, and release checklist. No real recording, email, or ticket is created by this exercise.</p>"
    "<h2>Classify the first meeting</h2><p>The chair conditionally approves the 20-depot pilot after rollback validation. Expansion to 47 depots is proposed but not approved. Whether the pilot could start without a test remains an open question in the transcript and must not silently become approval. Dana accepts the rollback test result due 10 October 2026. Depot notification has no accepted owner or due date. An utterance at 12:43 has uncertain speaker attribution, so it cannot fill those missing fields. Every material entry keeps an evidence span for participant correction.</p>"
    "<h2>Carry corrections into the follow-up</h2><p>The follow-up confirms the rollback test passed, satisfying the pilot condition. It does not approve the 47-depot expansion. Jo accepts depot notification, correcting an earlier draft that had guessed Dana as owner. The revision ledger retains the old draft, correction, confirming meeting, and current action state. Before sharing the recap beyond attendees, the chair reviews decisions, owner and date fields, recipient access, and the removal of the private staffing remark. A ticket can be submitted only through an authorized work-system step, with its receipt linked back to the action.</p>"
    '<pre><code class="language-text">D1: 20-depot pilot; conditional approval; rollback test required.\nP1: 47-depot expansion; proposed, not approved.\nA1: Dana; rollback test result; due 10 Oct 2026.\nA2: depot notification; unassigned -> Jo accepts in follow-up.\nUncertain span: 12:43 speaker unknown; no invented commitment.\nRelease: chair reviews audience, claims, corrections, and side effects.</code></pre>'
    "<h2>Performance and operating cost</h2><p>For T transcript turns and A action candidates, evidence extraction is O(T+A) with span pointers. Carrying a bounded ledger of H open decisions and actions uses O(H) state between sessions instead of resending every transcript. Review adds one check per material decision, commitment, and recipient. That work is justified by the risk of turning a proposal into a rollout or assigning a task to the wrong person. The final recap remains a draft until the chair approves it; text generation cannot grant access or prove a ticket was submitted.</p>"
    "<h3>Common Mistakes</h3><ul><li>Do not equate discussion with approval.</li><li>Do not guess an owner from an uncertain transcript segment.</li><li>Do not send or create tickets merely because the recap prompt asks for them.</li></ul>"
    "<h2>Connected lessons</h2>" + links(project_connections))
new_rows.append(article(project_path, titles[project_path], "Separate a pilot decision from a proposal and carry corrected actions into a reviewed recap.", project_body, projects, 60, project_connections, kind="project"))

questions = [
    ("What must a meeting-record prompt define before summarizing?", "Permitted inputs, audience, and evidence boundary", "Only the desired tone", "A wider recipient list", "Access and evidence are part of the work contract."),
    ("How should the uncertain 12:43 speaker be handled?", "Mark attribution unknown and seek confirmation", "Assign it to Dana", "Drop all meeting decisions", "Uncertain speech cannot establish a commitment."),
    ("What was approved in the first Beacon meeting?", "A conditional 20-depot pilot", "Expansion to 47 depots", "No decision of any kind", "The chair approved only the scoped pilot after validation."),
    ("How should the 47-depot idea appear?", "Proposed, not approved", "Approved rollout", "Completed action", "A proposal is a separate ledger state."),
    ("What happened to the question about starting without the rollback test?", "It remained unresolved", "It changed the decision condition", "It approved full rollout", "The transcript contains no answer."),
    ("Who accepted rollback validation, and when is its result due?", "Dana, 10 October 2026", "Jo, 10 October 2026", "An unnamed person, no date", "The accepted action has an owner and date."),
    ("Who owns depot notification after the first meeting?", "No confirmed owner", "Dana by default", "The uncertain 12:43 speaker", "The action stays unassigned until accepted."),
    ("What changes when the rollback test passes?", "The pilot condition is satisfied", "The 47-depot expansion is approved", "The earlier minutes disappear", "A cleared condition does not widen the decision."),
    ("What should happen to the incorrect Dana notification assignment?", "Keep a correction trail, then record Jo's acceptance", "Silently overwrite it", "Leave the wrong ticket active", "Versioned corrections preserve accountability."),
    ("Does a recap draft authorize distribution?", "No; the chair reviews claims and recipients first", "Yes, if it reads well", "Yes, if a model generated it", "Release authority sits outside the prompt."),
    ("How should a private staffing remark be handled for the wider recap?", "Exclude it from that audience's summary", "Include it because it was transcribed", "Publish the whole transcript", "Allowed input does not imply unrestricted output."),
    ("What proves a ticket was created after approval?", "A receipt from the work system", "A draft action sentence", "A model's assurance", "A side effect needs a system result."),
]
quiz_entry = copy.deepcopy(lookup["quizzes/prompt-engineering-multimodal-evidence"])
quiz_entry.update(id=str(uuid.uuid5(uuid.NAMESPACE_URL, "aitrove:" + quiz_path)),
                  path=quiz_path, title=titles[quiz_path],
                  summary="Test transcript boundaries, decision labels, action ownership, corrections, and release.",
                  body="<p>Choose the meeting-record decision supported by the permitted packet.</p><h2>Lessons</h2>" + links(paths) + "<h2>Project and sections</h2>" + links([project_path, applications, production, quizzes]),
                  sort_order=29970, status="published", published_at=stamp,
                  created_at=stamp, updated_at=stamp)
quiz_entry["data"].update(subject_root=subject_root, section_path=quizzes,
                          content_format="html", author_path="authors/aitrove-editorial",
                          seo_ready=True, duration_minutes=12,
                          related=related(paths + [project_path]),
                          questions=[{"prompt": prompt,
                                      "options": ([correct, wrong_a, wrong_b][index % 3:] + [correct, wrong_a, wrong_b][:index % 3]),
                                      "answer": (-index) % 3, "explanation": explanation}
                                     for index, (prompt, correct, wrong_a, wrong_b, explanation) in enumerate(questions)])
new_rows.append(quiz_entry)

for hub_path, selected, title, summary in [
    (applications, paths[:4], "Meeting decisions and actions", "Bind the transcript, separate approvals from proposals, and verify owners and corrections."),
    (production, paths[4:], "Meeting recap release", "Check access, sensitive material, correction routes, and side-effect receipts."),
    (projects, [project_path], "Beacon meeting record", "Review a fictional pilot decision, proposal, actions, and follow-up corrections."),
    (quizzes, [quiz_path], "Meeting-record decisions", "Test attribution, approval scope, action ownership, and release."),
]:
    hub = lookup[hub_path]
    hub["data"]["modules"].append({"title": title, "summary": summary, "lessons": selected})
    hub["body"] += "<h2>" + html.escape(title) + "</h2><p>" + html.escape(summary) + "</p>" + links(selected + [project_path, quiz_path])
    hub["updated_at"] = stamp

root_hub = lookup[subject_root]
root_hub["body"] += "<h2>Meeting records and accountable follow-up</h2><p>Keep transcript evidence, decision scope, action ownership, corrections, and release authority separate.</p>" + links(paths + [project_path, quiz_path])
root_hub["updated_at"] = stamp

backlinks = {
    "prompt-engineering/audio-overlap-speaker-review": paths[0],
    "prompt-engineering/privacy-and-data-minimization": paths[0],
    "prompt-engineering/classification-rubric-and-unknown-label": paths[1],
    "prompt-engineering/evidence-id-traceability": paths[1],
    "prompt-engineering/tool-call-authorization-contract": paths[2],
    "prompt-engineering/side-effect-receipt-reconciliation": paths[2],
    "prompt-engineering/conversation-checkpoint-reconstruction": paths[3],
    "prompt-engineering/prompt-release-review-packet": paths[4],
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
