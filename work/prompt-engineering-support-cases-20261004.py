"""Add original customer-support case prompt lessons and connected practice."""

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
project_path = "prompt-engineering/aster-seat-activation-support-project"
quiz_path = "quizzes/prompt-engineering-customer-support-cases"

specs = [
    dict(slug="support-prompt-ticket-identity-and-message-chronology", title="Support prompts: reconstruct ticket identity and chronology", section=applications,
         summary="Keep the customer, tenant, ticket, and latest request distinct.",
         definition="A support prompt should receive a scoped ticket ID, verified requester identity, account or tenant ID, message sequence, attachment versions, and current status. Thread summaries are useful only if they preserve corrections and agent commitments. Treat quoted older messages as history rather than the latest instruction. A model can identify the unresolved question and list facts needing verification; it should not merge similarly named customers or accounts. The ticketing system remains the authority for who can view or update the case. Keep external customer text separate from internal notes so a draft cannot leak a private operational comment.",
         case="Aster Console ticket T-47 concerns tenant N-47. The requester initially says that an employee invite failed, then clarifies that the invite was created but activation stopped at the seat limit. An earlier agent note says 'one seat may be free,' based on a dashboard showing 46 active seats. The latest customer request asks what must happen next. The assistant preserves that chronology and treats the old agent note as unverified, not as a promise to activate the employee. Another tenant named North Aster is excluded by its different tenant ID.",
         sample="Ticket T-47 | tenant N-47 | requester verified member\nFirst report: invite failed\nCorrection: invite exists; activation at seat limit\nOld agent note: one seat may be free -> unverified\nCurrent question: what can authorized admin do next?",
         cost="Reading M messages in order is O(M), while joining the ticket to account records is O(1) average with stable IDs. Long threads can consume context and bury corrections; a compact, versioned state summary costs a little review time but avoids acting on superseded text. A model should cite message IDs for disputed statements instead of relying on its own compressed memory.",
         mistakes=["Do not promote an older agent guess into a current entitlement fact.", "Do not join accounts by similar display names.", "Do not expose internal notes in a customer-facing draft."],
         related=["prompt-engineering/email-thread-chronology-and-superseded-claims", "prompt-engineering/conversation-memory-boundary"]),
    dict(slug="support-prompt-intent-urgency-and-routing-rubric", title="Support prompts: route by issue and verified urgency", section=applications,
         summary="Classify the work without treating frustration as a service incident.",
         definition="Support triage needs a bounded taxonomy, an unknown label, severity criteria, and an escalation destination. The model may label the issue and propose a queue, but the application should check the ticket's current product, account type, and policy triggers. Negative wording can indicate frustration without proving production-wide impact. A request to reach a human should be honored through the configured handoff, not answered with repeated self-service text. Record why the case was routed and how that decision can be corrected if new evidence arrives.",
         case="T-47 is an account-access and seat-allocation question, not a confirmed Aster Console outage. The requester is frustrated and says onboarding is blocked for one employee. That impact matters, but there is no evidence that other tenants are affected. The prompt selects the account-support queue and flags the stated onboarding deadline for agent review. If later monitoring confirms a shared invite service failure, the case can be linked to an incident; the first response must not invent that incident to sound helpful.",
         sample="Primary intent: seat allocation / activation\nScope: one tenant, one employee reported\nUrgency input: onboarding deadline stated by requester\nOutage status: unconfirmed\nQueue: account support; human handoff available",
         cost="Classifying T tickets is O(T) inference calls plus deterministic routing lookups. A narrow taxonomy makes evaluation and correction cheaper than free-form labels, but unknown cases must stay open rather than forced into the nearest category. Evaluate routing separately for ordinary, urgent, and human-request cases so a high average score does not hide a missed escalation.",
         mistakes=["Do not call customer frustration proof of a broad outage.", "Do not route an unknown issue as a confident account fix.", "Do not block a requested human handoff with another scripted reply."],
         related=["prompt-engineering/classification-rubric-and-unknown-label", "prompt-engineering/human-review-escalation"]),
    dict(slug="support-prompt-knowledge-version-and-answer-evidence", title="Support prompts: answer from current product guidance", section=applications,
         summary="Match the help article to the account's product version and policy date.",
         definition="A support answer should connect each instruction to an approved knowledge record whose product version, audience, region, and effective date match the ticket. Retrieval rank is not authority: an older article may score higher while describing behavior that has changed. If the current guidance conflicts with a trusted system status, surface the conflict rather than selecting the more convenient sentence. The assistant can draft steps from the reviewed record, but a human or test environment should validate any claim about what the product will do after the user clicks a control. Keep the article revision ID in the case packet.",
         case="Aster Console v4.2 counts pending invites against a 47-seat allocation. An older v4.1 article describes only active seats and appears first in semantic search. Tenant N-47 runs v4.2, so the assistant selects the current article and compares it with the entitlement service. The dashboard shows 46 active seats, but that number alone does not establish spare capacity. The reply explains why an existing pending invite can occupy the remaining place, without linking the customer to an obsolete instruction.",
         sample="Tenant product: Aster Console v4.2\nKnowledge revision: seats-v4.2-r3, active + pending\nObsolete candidate: seats-v4.1-r1, active only\nSelected guidance: v4.2 after entitlement check\nConflict: stop and review, do not guess",
         cost="Retrieving K candidates is dominated by index search; filtering them by version and effective date is O(K). The filter can reduce recall, so record when no compatible article exists and send the gap to a specialist. A short current answer is cheaper to support than a long answer assembled from mixed versions, especially when product behavior changed between releases.",
         mistakes=["Do not use the highest-ranked article without checking its version.", "Do not treat dashboard active seats as the full allocation rule.", "Do not paper over a conflict between knowledge and current account state."],
         related=["prompt-engineering/retrieval-freshness-and-conflict", "prompt-engineering/retrieval-rerank-after-authorization-and-version-check"]),
    dict(slug="support-prompt-entitlement-and-requester-permission", title="Support prompts: verify entitlement and requester authority", section=production,
         summary="Read current account state before proposing a seat change.",
         definition="A support prompt cannot establish account entitlement from customer prose. Query an authorized service for tenant ID, seat limit, active seats, pending reservations, and record freshness, then reconcile the total. Verify the requester role separately from tenant membership. A member may ask for an explanation yet lack authority to withdraw another person's invite, buy seats, or change an account setting. Any such action needs the correct administrator or specialist path and a fresh permission check at execution time. Minimize account data in the customer draft; expose counts and next steps, not another employee's private details.",
         case="N-47 has a limit of 47 seats: 46 active and one pending invite. That totals 47 reserved, leaving zero currently available. The requester is a verified member, not an admin, so the assistant can explain the allocation but cannot withdraw the pending invite or purchase capacity on the member's behalf. An authorized admin may review the pending reservation in the product. The assistant does not name the invited employee in the public reply, and it rechecks the ledger before any later change because the state may move while the ticket is open.",
         sample="Tenant N-47: limit 47\nActive 46 + pending 1 = reserved 47\nAvailable now: 0\nRequester role: member, not admin\nAllowed draft: explain counts and admin path\nForbidden effect: withdraw invite or buy seats as member",
         cost="Checking S account records is O(S) with keyed lookups; one ticket usually needs a constant number of reads. The arithmetic is trivial but stale state can invalidate it, so attach a retrieval time or version. Permission checks must run where the side effect occurs, even if the prompt performed an earlier read. That redundancy prevents a convincing explanation from becoming unauthorized account administration.",
         mistakes=["Do not infer an available seat from active count alone.", "Do not equate membership with admin permission.", "Do not expose the pending invitee's details to an unrelated requester."],
         related=["prompt-engineering/deterministic-calculation-gates", "prompt-engineering/tool-call-authorization-contract"]),
    dict(slug="support-prompt-clarifying-question-and-troubleshooting-branch", title="Support prompts: ask only the question that changes the next step", section=production,
         summary="Choose a focused clarification instead of a generic troubleshooting list.",
         definition="A support assistant should ask a clarifying question only when the answer changes routing, diagnosis, or an allowed action. Prefer a targeted request for the observed error state, product version, or scope over a broad demand for screenshots and logs. Do not ask the customer to send credentials or private tokens. When the account ledger already explains the capacity block, say so; do not stall with unrelated browser-cache steps. If the evidence is inconsistent, state which fact is uncertain and what single safe check would resolve it. Preserve the customer's earlier answers so the same question is not asked twice.",
         case="For T-47, the current entitlement ledger accounts for the blocked activation, so the next reply need not ask the member to clear cookies. If the customer says an admin removed the pending invite five minutes ago, the prompt should request a fresh entitlement read rather than demanding screenshots of billing details. If the service remains full after that read, the specialist can inspect invite state with proper access. The assistant never asks the member for an admin password to expedite the case.",
         sample="Known: 46 active + 1 pending = 47 reserved\nNo need: cache reset or credential screenshot\nIf admin reports invite removed: refresh entitlement record\nIf record conflicts: route to account specialist\nNever request password or token",
         cost="Selecting among C diagnostic branches is O(C) rule evaluation after retrieving the relevant state. Each extra question delays resolution and may expose more private data; each skipped necessary question risks a false answer. A test set should include both cases where the ledger suffices and cases where it conflicts, so the model learns to ask when a response actually changes the next step.",
         mistakes=["Do not ask for secrets as troubleshooting evidence.", "Do not repeat questions answered earlier in the ticket.", "Do not prescribe unrelated steps when a verified capacity record explains the block."],
         related=["prompt-engineering/clarification-versus-assumption-gate", "prompt-engineering/privacy-and-data-minimization"]),
    dict(slug="support-prompt-reply-handoff-and-resolution-receipt", title="Support prompts: separate reply, handoff, and resolution", section=production,
         summary="Keep the customer-facing commitment tied to actions that actually occurred.",
         definition="A support draft should distinguish the observed account state, the proposed next step, the responsible team, and what has or has not been done. The model can prepare a concise response and a separate internal handoff with ticket IDs, verified facts, unresolved questions, and current knowledge revision. Sending the reply, moving a queue, changing an account, and closing a ticket are different effects; each needs its own authorization and receipt. An ambiguous send timeout requires checking the ticket timeline before retry. A ticket is resolved only after the action or explanation is confirmed, not because the assistant produced polished text.",
         case="Aster drafts a reply for T-47: the v4.2 allocation is full at 46 active seats plus one pending reservation, and an authorized admin can review the pending invite. The member is not told that a seat was freed because no such effect occurred. If the requester needs a deadline-specific option, an account specialist receives a private handoff with ledger version and ticket history. The customer reply waits for the assigned agent's review. A later send timeout is reconciled against the ticket timeline before any duplicate response.",
         sample="Customer draft: 47/47 reserved; admin review is next\nInternal handoff: T-47, N-47, ledger version, knowledge r3\nNot done: invite withdrawal or seat purchase\nSend: pending agent review and receipt\nClosure: pending confirmed outcome",
         cost="Building an evidence-linked handoff for M messages and K facts is O(M+K), while ticket receipt checks are O(1) average by operation ID. The review adds latency but avoids unkept promises and duplicate sends. Keep customer text free of internal notes, and preserve a concise internal packet so a specialist can continue without asking the customer to repeat the whole history.",
         mistakes=["Do not claim a seat was freed before a confirmed account change.", "Do not send the internal handoff as the customer reply.", "Do not close a case merely because a draft was generated."],
         related=["prompt-engineering/side-effect-receipt-reconciliation", "prompt-engineering/incident-internal-handoff-and-decision-ledger"]),
]

paths = ["prompt-engineering/" + spec["slug"] for spec in specs]
assert not set(paths + [project_path, quiz_path]) & lookup.keys()
titles = {entry["path"]: entry["title"] for entry in entries}
titles.update({path: spec["title"] for path, spec in zip(paths, specs)})
titles[project_path] = "Project: handle Aster seat activation ticket T-47"
titles[quiz_path] = "Customer-support case decisions"


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
               tags=["prompt engineering", "customer support"], sort_order=32000 + order,
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

project_connections = paths + ["prompt-engineering/side-effect-receipt-reconciliation", "prompt-engineering/retrieval-freshness-and-conflict", quiz_path]
project_body = (
    "<p>Prepare a reviewable support response for fictional Aster Console ticket T-47 on tenant N-47. The requester first reports a failed invite, then clarifies that an existing invite cannot activate at the seat limit. An earlier agent speculated that one seat might be free. The current question is what the member can do next. Keep customer-facing text separate from internal notes, and do not send or change the account as part of this exercise.</p>"
    "<h2>Verify the case and guidance</h2><p>Confirm tenant and requester IDs, then read the current entitlement record and compatible v4.2 knowledge revision. The limit is 47 seats: 46 active plus one pending reservation equals 47, so zero seats are currently available. The v4.1 article that counts only active seats is obsolete for this tenant. The requester is a member rather than an admin. The assistant can explain the count and suggest that an authorized admin review the pending invite, but it cannot reveal the invitee's private details, withdraw the invite, or buy seats on the member's behalf.</p>"
    "<h2>Draft the bounded response and handoff</h2><p>Route T-47 to account support. The one-person onboarding impact matters, but no shared outage has been confirmed. Do not ask for passwords or generic cache resets. If the requester says the pending invite has already been removed, request a fresh entitlement read; a stale number is not proof the block persists. Draft a plain reply describing the current 47-of-47 allocation and the admin path. Give the specialist a separate packet with ticket history, ledger version, knowledge revision, and unresolved state. Keep send, account action, and closure pending their respective reviews and receipts.</p>"
    '<pre><code class="language-text">T-47 / N-47 | requester: verified member\nAster Console v4.2 | knowledge: seats-v4.2-r3\nSeat limit 47; active 46; pending 1; available 0\nQueue: account support; outage unconfirmed\nCustomer draft: explain count and admin path\nAccount change, send, and closure: not executed</code></pre>'
    "<h2>Performance and review cost</h2><p>Reading M ticket messages is O(M); current entitlement and role checks are keyed lookups. Filtering K help articles by version and date is O(K) after retrieval. The human review costs time but catches false promises and a wrong-tenant response. The final packet needs message IDs, account snapshot time, selected article revision, draft recipient, permissions, and effect receipts before anyone calls the case resolved.</p>"
    "<h3>Common Mistakes</h3><ul><li>Do not use the old agent's guess as entitlement evidence.</li><li>Do not count only active seats while pending invites reserve capacity.</li><li>Do not ask the member for an admin password.</li><li>Do not equate a draft reply with a sent response or a resolved case.</li></ul>"
    "<h2>Related lessons</h2>" + links(project_connections))
new_rows.append(article(project_path, titles[project_path], "Reconstruct the ticket, verify a 47-seat allocation, and prepare a permission-aware reply.", project_body, projects, 70, project_connections, "project"))

questions = [
    ("Which message defines the current T-47 request?", "The latest clarification about blocked activation", "The first invite-failed report alone", "The older agent's one-seat guess", "Thread chronology preserves corrections and current intent."),
    ("What prevents tenant mix-up?", "Stable ticket and tenant IDs", "Similar account display names", "The model's memory", "Names alone are not account identity."),
    ("Does customer frustration prove an outage?", "No; route the one-tenant impact without inventing shared scope", "Yes, always", "Only if a draft says so", "Observed scope and sentiment are different inputs."),
    ("Which guidance applies to N-47?", "The compatible v4.2 seat article", "The highest-ranked obsolete v4.1 article", "Any article about accounts", "Product version and effective rule determine relevance."),
    ("How many seats are currently available?", "Zero: 46 active plus one pending equals 47 reserved", "One, because 46 are active", "Forty-seven", "Pending reservations count under the current rule."),
    ("May the verified member withdraw the pending invite?", "No; use the authorized admin path", "Yes, because they opened the ticket", "Yes, if the model recommends it", "Membership and admin authority are distinct."),
    ("Should the reply name the pending invitee?", "No, the member needs the count and admin path", "Yes, to sound precise", "Only in the subject line", "Avoid unneeded private account details."),
    ("What if an admin reports the invite was removed minutes ago?", "Refresh the entitlement state", "Keep repeating the old count", "Ask for a password", "A current read resolves the stale-state question."),
    ("Is a browser-cache reset the next step for verified full capacity?", "No, it does not address the observed allocation", "Yes, always", "Only before checking the ledger", "Troubleshooting should follow the evidence."),
    ("What belongs in the private specialist handoff?", "Ticket history, ledger version, guidance revision, and unknowns", "Only a polished customer greeting", "The member's password", "The specialist needs traceable facts without secret collection."),
    ("A reply send times out. What next?", "Check the ticket timeline or receipt before retry", "Send again immediately", "Mark the case solved", "The first send may have succeeded."),
    ("When is T-47 resolved?", "After the action or explanation is confirmed under the case process", "When the draft is generated", "When a queue is selected", "Drafting and routing are not resolution."),
]
quiz = copy.deepcopy(lookup["quizzes/prompt-engineering-survey-design-analysis"])
quiz.update(id=str(uuid.uuid5(uuid.NAMESPACE_URL, "aitrove:" + quiz_path)), path=quiz_path,
            title=titles[quiz_path], summary="Test ticket history, routing, current guidance, account authority, and receipts.",
            body="<p>Choose the support decision supported by the verified account and ticket record.</p><h2>Lessons</h2>" + links(paths) + "<h2>Project and sections</h2>" + links([project_path, applications, production, quizzes]),
            sort_order=32090, status="published", published_at=stamp, created_at=stamp, updated_at=stamp)
quiz["data"].update(subject_root=subject_root, section_path=quizzes, content_format="html",
                    author_path="authors/aitrove-editorial", seo_ready=True, duration_minutes=12,
                    related=related(paths + [project_path]),
                    questions=[{"prompt": prompt,
                                "options": ([correct, wrong_a, wrong_b][index % 3:] + [correct, wrong_a, wrong_b][:index % 3]),
                                "answer": (-index) % 3, "explanation": explanation}
                               for index, (prompt, correct, wrong_a, wrong_b, explanation) in enumerate(questions)])
new_rows.append(quiz)

for hub_path, selected, title, summary in [
    (applications, paths[:3], "Support case intake and guidance", "Reconstruct the case, route it, and select current help content."),
    (production, paths[3:], "Support decisions and handoff", "Verify permissions, ask focused questions, and separate draft from effect."),
    (projects, [project_path], "Aster seat activation support", "Apply the full review to a fictional 47-seat tenant."),
    (quizzes, [quiz_path], "Support case decisions", "Test account and communication boundaries."),
]:
    hub = lookup[hub_path]
    hub["data"]["modules"].append({"title": title, "summary": summary, "lessons": selected})
    hub["body"] += "<h2>" + html.escape(title) + "</h2><p>" + html.escape(summary) + "</p>" + links(selected + [project_path, quiz_path])
    hub["updated_at"] = stamp

lookup[subject_root]["body"] += "<h2>Customer-support case prompts</h2><p>Carry a verified ticket from intake to a bounded reply and specialist handoff.</p>" + links(paths + [project_path, quiz_path])
lookup[subject_root]["updated_at"] = stamp

backlinks = {
    "prompt-engineering/email-thread-chronology-and-superseded-claims": paths[0],
    "prompt-engineering/classification-rubric-and-unknown-label": paths[1],
    "prompt-engineering/retrieval-freshness-and-conflict": paths[2],
    "prompt-engineering/tool-call-authorization-contract": paths[3],
    "prompt-engineering/clarification-versus-assumption-gate": paths[4],
    "prompt-engineering/side-effect-receipt-reconciliation": paths[5],
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
