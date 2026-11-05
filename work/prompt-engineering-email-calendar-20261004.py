"""Add email and calendar prompt workflow lessons, project, and quiz."""

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
project_path = "prompt-engineering/aster-vendor-email-calendar-project"
quiz_path = "quizzes/prompt-engineering-email-calendar"

specs = [
    dict(slug="email-thread-chronology-and-superseded-claims", title="Email prompts: reconstruct the thread before drafting", section=applications,
         summary="Separate current decisions from older quoted text and proposals.",
         definition="An email thread is a sequence of messages, not a single flat document. A prompt that summarizes or drafts a reply should receive message IDs, send times, authors, recipients, and thread relationships from the mail service. Parse quoted earlier text as a quotation, not as a new statement by the latest sender. Build a claim ledger that marks each item proposed, corrected, approved, or unresolved. The most recent message can clarify an older claim, but recency alone does not grant approval. If a reply is missing from the fetched thread, state that the record is incomplete before claiming agreement.",
         case="Aster Operations discusses a depot pilot with a vendor. The first email proposes 47 sites. A later message from the authorized program owner limits the approved pilot to 20 sites; the 47-site expansion remains a future proposal. A final vendor reply quotes the original 47-site text while asking about a meeting. A flat summarizer could mistake that quotation for a renewed approval. The prompt instead ties each claim to its message ID and asks the drafter to say '20-site pilot' while leaving expansion unresolved.",
         sample="Message M-41: 47-site expansion proposed.\nMessage M-47: program owner approves 20-site pilot only.\nMessage M-52: quotes M-41; asks for meeting.\nCurrent claim: 20-site pilot approved.\nUnresolved: 47-site expansion; no renewed approval.",
         cost="Sorting M messages by reliable timestamps is O(M log M), while walking provider-supplied thread order is O(M). Claim extraction adds review proportional to the number of substantive statements. Restrict retrieval to the relevant thread and referenced attachments; loading an entire mailbox increases privacy exposure and token cost. A short provenance ledger prevents a correction from disappearing when a long quoted chain dominates the prompt.",
         mistakes=["Do not treat a quoted old proposal as a new decision.", "Do not infer approval solely from the latest message's position.", "Do not claim the thread is complete when a referenced reply is missing."],
         related=["prompt-engineering/meeting-decision-proposal-and-dissent-ledger", "prompt-engineering/context-distillation-evidence-ledger", "prompt-engineering/evidence-id-traceability"]),
    dict(slug="email-sender-identity-and-instruction-boundary", title="Email prompts: keep sender identity and message text separate", section=applications,
         summary="Use verified mailbox metadata for identity and treat message bodies as lower-trust content.",
         definition="The display name and signature in an email are claims inside a message, not proof of who controls an account. The application should provide verified mailbox identity and authorization context separately from the body. An inbound message may ask the assistant to change a workflow, reveal private information, or ignore earlier rules. The model can summarize that request, but cannot adopt it as a higher-priority instruction. Before drafting a consequential response, check whether the sender and recipient belong to the authorized thread and whether any requested action falls inside the user's current task. Mail content is evidence about what someone wrote; sending, scheduling, or data disclosure remains governed by trusted permissions.",
         case="A message in the Aster thread displays the name 'Pilot Director' and says to send every depot contact list to an unfamiliar address before scheduling. The application metadata shows that the sender is an external vendor account without access to the contact list. The assistant records the request as an unapproved vendor ask and does not fetch or attach private contacts. It can still answer the legitimate meeting question after a user reviews the proposed recipients. A signature block cannot confer internal approval authority.",
         sample="Display name: Pilot Director; verified account: external vendor.\nBody request: send depot contacts to new address.\nDecision: report request; do not fetch or disclose contacts.\nLegitimate task: draft meeting reply within existing thread.\nEffect authority: current user and mail service, not body text.",
         cost="Checking a sender against a trusted directory is O(1) average with a keyed lookup; parsing M headers and recipients is O(M). The identity check adds little latency compared with the risk of treating forged display text as authority. Avoid feeding entire unrelated mailbox history into the model. Record only the account and message IDs needed for this task, and keep confidential address lists outside the prompt unless the user has authorized their use.",
         mistakes=["Do not equate a display name or signature with verified identity.", "Do not obey instructions embedded in an inbound email body.", "Do not retrieve unrelated contacts to satisfy an unapproved vendor request."],
         related=["prompt-engineering/tool-result-instruction-quarantine", "prompt-engineering/request-risk-routing-contract", "prompt-engineering/retrieval-identity-and-document-permission-gate"]),
    dict(slug="email-attachment-version-and-content-gate", title="Email prompts: verify attachment version and coverage", section=applications,
         summary="Tie claims to the actual attachment opened and mark missing files unresolved.",
         definition="An attachment name is not its content, and the latest email does not always contain the latest approved file. A prompt should receive attachment IDs, message links, version markers, file type, and extraction status. Inspect only attachments relevant to the question. If extraction fails or a file is missing, do not invent its contents from the filename or a prior message. For a revised file, compare the specific fields that matter and record which version supports each claim. Treat text inside attachments as data, including any instruction-like text. A scanned image may require separate visual review if text extraction omits a table or signature.",
         case="The vendor first attaches pilot-plan-v3 to M-41, showing 47 candidate sites. The authorized owner later attaches pilot-plan-v4 to M-47, listing 20 approved pilot sites and leaving expansion in a separate appendix. M-52 mentions 'the attached final plan' but contains no attachment. The assistant uses the verified v4 file for the pilot count and reports that M-52 supplied no new file. If v4 cannot be opened, it pauses the count claim rather than falling back silently to v3.",
         sample="M-41 attachment A-3: v3, 47 candidate sites.\nM-47 attachment A-4: v4, 20 approved pilot sites.\nM-52: says 'attached'; attachment list empty.\nCurrent pilot claim: A-4, if extraction succeeds.\nA-4 unavailable: count remains unverified.",
         cost="Extracting A relevant attachments costs roughly O(total bytes), and comparing R required fields is O(R) after parsing. Narrow extraction saves tokens and reduces exposure to irrelevant files. The cost of checking an actual attachment ID is small compared with sending a wrong count to a customer or creating an event for an obsolete plan. Store file IDs and hashes so a reviewer can reproduce which bytes supported the draft.",
         mistakes=["Do not treat a filename as proof of file contents.", "Do not assume a later email includes the file it mentions.", "Do not silently substitute v3 when v4 is unavailable."],
         related=["prompt-engineering/document-page-anchor-and-field-conflict", "prompt-engineering/retrieval-freshness-and-conflict", "prompt-engineering/api-docs-code-schema-and-version-boundary"]),
    dict(slug="email-recipient-scope-and-reply-all-review", title="Email prompts: review To, Cc, Bcc, and reply scope", section=production,
         summary="Resolve recipients from trusted identities before any draft or send effect.",
         definition="A reply prompt should name the intended audience and disclosure scope before it generates a polished message. The original thread may include observers, external vendors, hidden recipients, or an address that now routes elsewhere. Do not infer that reply-all is appropriate merely because an address appeared in a prior message. Resolve each recipient through trusted mailbox or directory data, flag external domains, and state whether the reply should remain in the same thread. Bcc recipients are a separate disclosure decision; a model should not silently add or expose them. A draft can be prepared for review, while sending requires current user authority and a checked recipient set.",
         case="The Aster discussion includes the program owner, one vendor coordinator, and a broad legacy distribution list. The requested meeting reply is intended for the owner and coordinator only. A reply-all would reveal the pilot timing to the legacy list. The assistant proposes those two explicit recipients, keeps the thread relationship, and leaves the list out. A quoted address in the message body is not automatically a recipient. Before sending, the user sees the To and Cc fields as well as the exact body.",
         sample="To: verified program owner and vendor coordinator.\nCc: none; legacy distribution list excluded.\nBcc: none unless separately requested and reviewed.\nThread: reply to M-52, preserve conversation identity.\nSend: only after current user reviews recipients and body.",
         cost="Resolving R recipient IDs is O(R) with indexed directory lookups. The preview step adds a human decision, but prevents accidental disclosure to a large group. A long thread may contain many stale addresses, so derive recipients from the current task rather than copying every header. Record the reviewed recipient set with the draft version; a later body edit should not silently expand the audience.",
         mistakes=["Do not use reply-all by default.", "Do not copy addresses from quoted text into recipient fields.", "Do not add Bcc recipients without an explicit disclosure decision."],
         related=["prompt-engineering/sensitive-output-redaction-gate", "prompt-engineering/browser-form-preview-submit-boundary", "prompt-engineering/incident-update-audience-owner-and-release-gate"]),
    dict(slug="email-draft-commitment-and-send-receipt", title="Email prompts: separate drafted commitments from sent messages", section=production,
         summary="Check promises in the body and verify the effect through a mail-service receipt.",
         definition="Writing 'we will deliver Friday' can create a commitment even before the send button is pressed. A drafting prompt should distinguish confirmed facts, proposed actions, owners, and deadlines. It should not promise a date that the thread has not approved. Save a draft with its thread ID, recipients, body version, and attachment list, then present it for review. The send operation is a separate effect. If the send call times out, query the mail service for the draft or message receipt before trying again. A model's claim that it sent a message is not delivery evidence, and a provider's acceptance receipt may still be narrower than confirmed recipient delivery.",
         case="The Aster reply says the team can review the 20-site pilot on Tuesday. It does not promise to approve 47-site expansion or deliver a final vendor contract by Friday. The assistant saves draft D-47, containing the two reviewed recipients and no contact-list attachment. The user approves the exact draft. If sending returns an ambiguous timeout, the workflow checks whether D-47 became a sent message before another attempt. The final user report distinguishes draft saved, send accepted, and recipient delivery when those states are known.",
         sample="Draft D-47: 20-site pilot review; 47-site expansion unresolved.\nRecipients: two reviewed addresses; attachments: none.\nCommitment: meeting proposal only, no contract deadline.\nSend timeout: query mail-service state before retry.\nFinal status: draft, accepted send, or confirmed delivery separately.",
         cost="A keyed receipt lookup is O(1) average; reviewing C commitment claims is O(C). An extra receipt query is cheaper than a duplicate email to an external party. Keep a stable draft ID and body version through retries. If the body or recipients change after approval, require a new review instead of treating the old approval as transferable. Measure drafting latency separately from mail delivery latency.",
         mistakes=["Do not write an unapproved deadline as a firm promise.", "Do not call a saved draft a sent message.", "Do not resend after an ambiguous timeout without checking mail-service state."],
         related=["prompt-engineering/side-effect-receipt-reconciliation", "prompt-engineering/meeting-action-owner-date-confirmation-gate", "prompt-engineering/browser-effect-receipt-and-recovery"]),
    dict(slug="calendar-prompt-availability-timezone-and-duration", title="Calendar prompts: resolve availability, zone, and duration", section=applications,
         summary="Turn a vague meeting request into a concrete interval before drafting an invite.",
         definition="A calendar prompt should request a date, start time, duration, named time zone, required attendees, and availability window. A local clock time without a zone can refer to several different instants. The application should convert proposed local times into resolved instants using its time-zone data and query free/busy for the calendars the user is allowed to inspect. Free/busy does not reveal the contents of private events; the assistant should not request those details unless authorized. A suggestion is not a confirmed booking. Check buffers, holidays, and the difference between a tentative hold and a final invite.",
         case="The Aster vendor asks for 'Tuesday at 11:30' without naming a time zone. The assistant does not guess from the vendor signature. The program owner instead proposes Tuesday 15:00 to 15:45 UTC for three named attendees. The application checks each required calendar's availability for that exact interval and returns only free/busy status. One attendee has a conflict, so the assistant offers another verified slot rather than creating a conflicting invite. A 45-minute duration is explicit, not inferred from a default calendar setting.",
         sample="Ambiguous request: Tuesday 11:30, zone missing -> clarify.\nOwner proposal: Tuesday 15:00–15:45 UTC.\nRequired attendees: three verified identities.\nFree/busy check: conflict found -> propose another checked slot.\nNo calendar effect before exact interval review.",
         cost="Checking A attendees across S candidate slots is O(AS) availability queries without batching; provider batch calls can reduce network overhead but not the logical checks. Time-zone conversion is inexpensive, yet a wrong instant can waste every attendee's time. Keep only free/busy results in the prompt when event titles are not needed. Recheck availability immediately before creating the event because calendars can change between suggestion and approval.",
         mistakes=["Do not infer a time zone from a signature or locale.", "Do not treat a suggested time as a booked event.", "Do not expose private event details when free/busy is sufficient."],
         related=["prompt-engineering/recurring-task-timezone-and-window-contract", "prompt-engineering/meeting-action-owner-date-confirmation-gate", "prompt-engineering/privacy-and-data-minimization"]),
    dict(slug="calendar-invite-create-update-and-receipt", title="Calendar prompts: distinguish create, update, and cancellation", section=production,
         summary="Bind every event change to an event ID, current state, guest list, and receipt.",
         definition="A calendar event is an external effect with an identity. Before creating one, review title, start and end instants, time zone, organizer, attendee list, location, and notification behavior. After creation, keep the returned event ID and version. A later request to move a meeting should update that event rather than create a near-duplicate. Read current state before applying a change, especially when another organizer may have edited it. Cancellation is distinct from deleting a local hold. If the API response is ambiguous, reconcile against the calendar by event ID and expected version before retrying. Prompt wording cannot substitute for the provider's effect receipt.",
         case="After the Aster owner selects a conflict-free slot, the assistant prepares a 45-minute invite titled '20-site pilot review' for three checked attendees. The user reviews the details and authorizes creation. The calendar returns event E-47 and version V-1. The vendor later asks to move it by 30 minutes; the assistant checks E-47, recomputes the interval, reviews changed notifications, and updates the same event. If an update times out, it reads E-47 before sending another request. It does not create E-48 by assumption.",
         sample="Proposed event: 20-site pilot review, 45 minutes, three attendees.\nCreate approved -> event E-47, version V-1.\nMove request -> read E-47, check new interval, update E-47.\nTimeout -> reconcile E-47 before retry.\nCancellation -> explicit scope and guest-notice review.",
         cost="A keyed event read is O(1) average at the application level, though network latency can dominate. Rechecking A attendee calendars adds O(A) logical availability checks per proposed change. Version matching and receipts add a small amount of state but prevent duplicate events and lost updates. Review notification behavior because editing an event can message guests even when the prompt describes the edit as minor.",
         mistakes=["Do not create a second event to move an existing one.", "Do not assume a timeout means the create or update failed.", "Do not cancel an entire event when the user meant one tentative hold."],
         related=["prompt-engineering/side-effect-receipt-reconciliation", "prompt-engineering/browser-effect-receipt-and-recovery", "prompt-engineering/recurring-run-idempotency-and-retry-boundary"]),
    dict(slug="calendar-recurring-event-instance-scope", title="Calendar prompts: scope recurrence changes to the right instances", section=production,
         summary="Separate one occurrence from an entire series and verify exceptions.",
         definition="A recurring meeting represents a rule plus individual occurrences and exceptions. A prompt should ask whether the user intends to edit one occurrence, this and later occurrences, or the whole series. Those scopes can produce different effects and guest notifications. Preserve the recurrence rule, time zone, exception dates, and organizer identity in the review packet. Do not infer a series-wide change from 'move next Tuesday.' A local display may show only a few generated occurrences, so check the underlying event identity before editing. After a change, inspect both the target occurrence and unaffected neighboring occurrences.",
         case="Suppose the Aster pilot review becomes a weekly series for four weeks. The owner says 'move next Tuesday's call by 30 minutes.' The assistant targets only that dated occurrence and leaves the other three at their prior time. A separate later request to move all remaining sessions needs a new scope review. If one occurrence was cancelled, the assistant must not recreate it while updating the series. The calendar service returns exception or instance IDs that the application retains for verification.",
         sample="Series: four weekly sessions, one named time zone.\nRequest: move next Tuesday only.\nTarget: dated instance, not whole recurrence rule.\nVerify: target moved; other three unchanged.\nLater series-wide request -> separate scope and notice review.",
         cost="Checking K generated occurrences and E exceptions is O(K+E) for a bounded review window. A series-wide update can affect many more guests and dates than a single-instance edit, so the prompt should present an effect count before approval. Avoid materializing an unbounded recurrence solely for a preview; choose a finite horizon and state it. A missing exception record can cause a cancelled meeting to reappear, so include cancellation cases in release tests.",
         mistakes=["Do not turn 'next Tuesday' into a change to every future meeting.", "Do not lose a cancelled-instance exception during a series edit.", "Do not claim an unbounded series was fully reviewed from a short preview."],
         related=["prompt-engineering/recurring-task-intent-and-stop-condition", "prompt-engineering/recurring-task-timezone-and-window-contract", "prompt-engineering/meeting-recap-revision-and-cross-session-state"]),
]

paths = ["prompt-engineering/" + spec["slug"] for spec in specs]
assert not set(paths + [project_path, quiz_path]) & lookup.keys()
titles = {entry["path"]: entry["title"] for entry in entries}
titles.update({path: spec["title"] for path, spec in zip(paths, specs)})
titles[project_path] = "Project: review an Aster vendor reply and invite"
titles[quiz_path] = "Email and calendar prompt decisions"


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
               tags=["prompt engineering", "email calendar"], sort_order=31300 + order,
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
            + "<h2>Performance and operating cost</h2><p>" + html.escape(spec["cost"]) + "</p>"
            + "<h3>Common Mistakes</h3><ul>" + "".join("<li>" + html.escape(item) + "</li>" for item in spec["mistakes"]) + "</ul>"
            + "<h2>Connected lessons</h2>" + links(connections))
    new_rows.append(article(path, spec["title"], spec["summary"], body, spec["section"], index * 10, connections))

project_connections = paths + ["prompt-engineering/meeting-decision-proposal-and-dissent-ledger", "prompt-engineering/side-effect-receipt-reconciliation", quiz_path]
project_body = (
    "<p>A fictional Aster Operations vendor thread begins with a 47-site expansion proposal. An authorized owner later approves only a 20-site pilot and attaches plan v4. A subsequent vendor message quotes the 47-site proposal and asks for a meeting, saying a final plan is attached even though the message has no attachment. The user wants a reply draft and a proposed calendar invite. This project creates a review packet; it does not send email or write a calendar event.</p>"
    "<h2>Resolve the thread and draft</h2><p>Read message IDs, send times, verified account identities, recipients, and attachment lists. Use v4 to support the 20-site pilot count only if extraction succeeds. Treat the quoted 47-site text as an older proposal. The draft goes to the authorized owner and vendor coordinator, not the legacy distribution list. It proposes a pilot review and avoids promising a contract deadline. A new address requesting the depot contact list is an unapproved disclosure request, even if its display name claims seniority. Save the reviewed message as a draft with a stable ID.</p>"
    "<h2>Propose the calendar event</h2><p>The vendor's 'Tuesday 11:30' lacks a time zone, so ask for clarification or use a separately confirmed interval. The owner supplies Tuesday 15:00–15:45 UTC. Check the three required attendees' free/busy state and recheck just before creating an event. If a conflict appears, offer a verified alternative. Creation, update, and cancellation each require a precise event identity and effect review. A later request to move one occurrence of a weekly series must not shift the whole series.</p>"
    '<pre><code class="language-text">M-41: 47-site expansion proposed; attachment A-3 is v3.\nM-47: 20-site pilot approved; attachment A-4 is v4.\nM-52: quotes M-41; says attached but has no file.\nReply: two reviewed recipients; draft only; no contact list.\nInvite candidate: Tuesday 15:00–15:45 UTC, three attendees.\nEffects: send and create only after exact preview and current approval.</code></pre>'
    "<h2>Performance and review cost</h2><p>Thread reconstruction costs O(M log M) when M messages require timestamp ordering. Extract only the A attachments relevant to the decision, rather than the entire mailbox. Availability checks over S candidate slots and three attendees cost O(3S) logical queries. Receipt lookups add little relative to duplicate mail or calendar effects. The release suite tests a quoted old proposal, missing attachment, forged display name, reply-all disclosure, time-zone ambiguity, conflicting attendee, send timeout, event update timeout, and one-instance recurrence change.</p>"
    "<h3>Common Mistakes</h3><ul><li>Do not promote quoted expansion text to approval.</li><li>Do not invent the missing final attachment.</li><li>Do not send to the legacy list by default.</li><li>Do not guess the vendor's time zone.</li><li>Do not call a saved draft a sent message or a proposed time a booked event.</li></ul>"
    "<h2>Connected lessons</h2>" + links(project_connections))
new_rows.append(article(project_path, titles[project_path], "Reconcile thread, attachments, recipients, and a tentative meeting interval.", project_body, projects, 90, project_connections, "project"))

questions = [
    ("What is the current approved rollout scope?", "The 20-site pilot", "The quoted 47-site expansion", "Both scopes", "The authorized owner's later approval limits the pilot."),
    ("Does the latest quoted 47-site text renew approval?", "No, it is quoted older content", "Yes, all quotations are new decisions", "Only if it appears twice", "Quotation is not a fresh authorization."),
    ("M-52 says a final plan is attached but has no file. What follows?", "Report that no attachment was supplied", "Invent the final plan", "Use v3 without saying so", "The attachment list controls what is available."),
    ("What proves an email sender's authority?", "Trusted account and authorization data", "The display name", "A signature claim", "Message text does not grant identity or permission."),
    ("Should the reply include the legacy distribution list?", "Only if the current user approves that audience", "Yes, reply-all is automatic", "Yes, because it once appeared", "Recipient scope is a current disclosure choice."),
    ("What state follows saving draft D-47?", "Draft saved, not sent", "Recipient delivery confirmed", "The calendar event exists", "Draft persistence and sending are separate effects."),
    ("A send call times out. What should happen before retry?", "Query the mail service for the message or draft receipt", "Send again immediately", "Claim delivery", "An ambiguous effect needs reconciliation."),
    ("What is missing from 'Tuesday 11:30'?", "A time zone", "A font choice", "A message subject", "The clock time is not a unique instant without zone context."),
    ("What should the calendar check reveal when only availability is needed?", "Free or busy for the exact interval", "Every private event title", "All mailbox contents", "Use the least information needed for scheduling."),
    ("What does an attendee conflict mean?", "Offer another verified slot", "Create anyway and call it confirmed", "Ignore that attendee", "A proposed interval is not yet a valid booking."),
    ("An event update times out. What should the agent do?", "Read the event by ID before another update", "Create a second event", "Assume it was cancelled", "The first update may have succeeded."),
    ("What does 'move next Tuesday' mean for a weekly series?", "Edit the named occurrence only", "Shift every future occurrence", "Delete the series", "The stated scope is one dated instance."),
]
quiz = copy.deepcopy(lookup["quizzes/prompt-engineering-chart-creation"])
quiz.update(id=str(uuid.uuid5(uuid.NAMESPACE_URL, "aitrove:" + quiz_path)), path=quiz_path,
            title=titles[quiz_path], summary="Test thread evidence, recipient scope, send receipts, and event identity.",
            body="<p>Choose the mail or calendar decision supported by verified records and current approval.</p><h2>Lessons</h2>" + links(paths) + "<h2>Project and sections</h2>" + links([project_path, applications, production, quizzes]),
            sort_order=31400, status="published", published_at=stamp, created_at=stamp, updated_at=stamp)
quiz["data"].update(subject_root=subject_root, section_path=quizzes, content_format="html",
                    author_path="authors/aitrove-editorial", seo_ready=True, duration_minutes=12,
                    related=related(paths + [project_path]),
                    questions=[{"prompt": prompt,
                                "options": ([correct, wrong_a, wrong_b][index % 3:] + [correct, wrong_a, wrong_b][:index % 3]),
                                "answer": (-index) % 3, "explanation": explanation}
                               for index, (prompt, correct, wrong_a, wrong_b, explanation) in enumerate(questions)])
new_rows.append(quiz)

for hub_path, selected, title, summary in [
    (applications, [paths[0], paths[1], paths[2], paths[5]], "Email and calendar input checks", "Reconstruct thread claims, inspect attachments, and resolve meeting time."),
    (production, [paths[3], paths[4], paths[6], paths[7]], "Email and calendar effect gates", "Review recipients, receipts, event updates, and recurrence scope."),
    (projects, [project_path], "Aster vendor reply and invite", "Apply message, attachment, recipient, and event checks to one workflow."),
    (quizzes, [quiz_path], "Email and calendar decisions", "Test quoted claims, time zones, approval, and effect receipts."),
]:
    hub = lookup[hub_path]
    hub["data"]["modules"].append({"title": title, "summary": summary, "lessons": selected})
    hub["body"] += "<h2>" + html.escape(title) + "</h2><p>" + html.escape(summary) + "</p>" + links(selected + [project_path, quiz_path])
    hub["updated_at"] = stamp

lookup[subject_root]["body"] += "<h2>Email and calendar workflows</h2><p>Reconstruct messages, verify recipients and attachments, and distinguish proposals from external effects.</p>" + links(paths + [project_path, quiz_path])
lookup[subject_root]["updated_at"] = stamp

backlinks = {
    "prompt-engineering/meeting-decision-proposal-and-dissent-ledger": paths[0],
    "prompt-engineering/tool-result-instruction-quarantine": paths[1],
    "prompt-engineering/document-page-anchor-and-field-conflict": paths[2],
    "prompt-engineering/sensitive-output-redaction-gate": paths[3],
    "prompt-engineering/side-effect-receipt-reconciliation": paths[4],
    "prompt-engineering/recurring-task-timezone-and-window-contract": paths[5],
    "prompt-engineering/browser-effect-receipt-and-recovery": paths[6],
    "prompt-engineering/recurring-task-intent-and-stop-condition": paths[7],
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
