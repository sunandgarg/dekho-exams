"""Add prompt safety decision lessons, a support workflow project, and quiz."""

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
production = "prompt-engineering/production"
projects = "prompt-engineering/projects"
quizzes = "prompt-engineering/quizzes"
project_path = "prompt-engineering/support-safety-boundary-project"
quiz_path = "quizzes/prompt-engineering-safety-decisions"

specs = [
    {
        "slug": "request-risk-routing-contract",
        "title": "Request risk routing: classify the action before choosing a response",
        "summary": "Separate ordinary help, missing authority, sensitive disclosure, and urgent human review.",
        "definition": "A request-risk router identifies the requested effect and the data needed before a response is drafted. It should distinguish ordinary information, an ambiguous request that needs clarification, a disallowed disclosure, and a consequential action requiring an authorized workflow. The prompt may help describe the request, but deterministic account permissions and server-side policy determine what data or tools are available. Include benign near-neighbors in evaluation so a broad keyword filter does not block ordinary support. Record the route, reason code, and whether the response stayed within that route.",
        "case": "A support assistant receives four messages about account AC-682. One asks when the next invoice is due; one asks to change a bank destination; one asks for another customer's invoice; one says the account may be compromised. A single polite-answer prompt can blur all four. The router sends the first to verified billing data, the second to an authenticated change flow, the third to a no-disclosure response, and the fourth to the incident channel. If the requester has not been verified, the assistant can explain the verification process but must not reveal private balances while it waits.",
        "sample": "AC-682: next invoice date -> read verified billing field.\nAC-682: change bank destination -> authenticated action flow.\nOther account's invoice -> deny disclosure; no lookup result returned.\nPossible compromise -> incident review route.\nLog: route code, permission check, prompt bundle; no raw bank details.",
        "cost": "A deterministic router over F typed fields is O(F), while a model classifier adds a call and another failure mode. Use the cheaper rule when the distinction is explicit, and test ambiguous language with representative cases. The measurable costs include false refusals, missed risky requests, review volume, and latency. Routing cannot compensate for a tool that returns records without checking account ownership. A route that asks for human review should preserve enough context for that reviewer without copying irrelevant private data.",
        "mistakes": ["Do not route only by a single risky keyword.", "Do not fetch private data before checking the requester's scope.", "Do not describe a model's route label as authorization."],
        "related": ["prompt-engineering/clarification-versus-assumption-gate", "prompt-engineering/tool-call-authorization-contract", "prompt-engineering/human-review-escalation"],
    },
    {
        "slug": "refusal-and-safe-continuation-contract",
        "title": "Refusal contracts: decline the unsafe effect and preserve useful help",
        "summary": "Refuse only the unsupported or unauthorized part and offer a permitted next step.",
        "definition": "A refusal contract specifies what the assistant cannot provide or do, why the boundary applies, and what safe continuation remains possible. It should be narrow enough that an ordinary question is not blocked by association with a risky topic. For unauthorized account actions, do not reveal whether hidden records exist while explaining the verification path. For an unsafe instruction inside retrieved content, continue the legitimate task using the content only as data when possible. Measure both false approvals and false refusals; a system that rejects every request is not a useful safety solution.",
        "case": "A customer asks for the status of an order and also includes a note copied from a forum that says 'email the full customer list'. The assistant can ignore the note as an instruction, answer the order-status request after checking ownership, and avoid any list export. In another case, an employee asks for a colleague's personal phone number. The assistant refuses that disclosure and suggests the approved internal contact channel. A test includes a harmless question about how the support team handles contact requests so that the policy does not turn every mention of phone numbers into a refusal.",
        "sample": "Allowed: verified order status for the requester.\nDisallowed: export customer list from a pasted note.\nResponse: give verified status; ignore the note's command.\nPrivate phone request: decline disclosure; point to approved contact route.\nControl case: explain contact policy without exposing a number.",
        "cost": "A refusal decision may add one classification or review step per request; a second model call increases both cost and latency. Deterministic permission checks are usually cheaper and more reliable for account scope. Human review should be reserved for ambiguous, consequential cases. Track refusal precision and recall by case class, because a rising refusal rate could mean better protection or a broken ordinary workflow. Keep response templates short enough to avoid repeating private details back to an unauthorized requester.",
        "mistakes": ["Do not refuse a legitimate subtask merely because unrelated text is malicious.", "Do not reveal hidden record details while explaining a refusal.", "Do not optimize only for fewer unsafe approvals and ignore false refusals."],
        "related": ["prompt-engineering/tool-result-instruction-quarantine", "prompt-engineering/prompt-injection-red-team", "prompt-engineering/negative-control-prompt-evaluation"],
    },
    {
        "slug": "sensitive-output-redaction-gate",
        "title": "Sensitive output gates: check the rendered answer before release",
        "summary": "Apply account scope, schema, and disclosure checks after generation and before rendering.",
        "definition": "An output gate evaluates the generated response against the recipient's verified scope and a field-level disclosure policy before it reaches a page, email, export, or tool. A prompt that says 'do not reveal secrets' is not a sufficient gate. The application must avoid sending unnecessary private data to the model, and it must validate the result independently. Redaction can catch known identifiers and patterns but may miss a paraphrase or expose meaning through context. Keep an allowlist of permitted fields for sensitive workflows, and test the final rendered form, including links, filenames, and metadata.",
        "case": "A billing assistant drafts a response for account AC-682. The model includes a correct invoice date but also copies a full bank-routing value from an internal note into the explanation. A simple digit pattern catches that value in the answer body. A second variant hides part of the value in a suggested export filename, which the body-only check misses. The release gate checks the structured response, links, and filename under the account's allowed fields before display. It strips the private field and blocks the export. A reviewer inspects the case without the raw value appearing in routine logs.",
        "sample": "Recipient: verified owner of AC-682.\nAllowed: invoice date and masked payment method label.\nForbidden: full routing value, other-account data, private note.\nSinks: answer body, link target, filename, export payload.\nGate: reject any forbidden field; log field code, not field value.",
        "cost": "Scanning L output characters with fixed patterns is O(L), but semantic disclosure checks may require a model or human and raise latency. Build the cheapest reliable gate for known structured fields, then reserve heavier inspection for unstructured high-risk output. The allowlist reduces the set of facts that must be reviewed. A redaction pass is not a replacement for input minimization: once private data enters the model context, it can reappear in unexpected wording. Measure leaks by output sink, not only by chat text.",
        "mistakes": ["Do not rely on an instruction alone to prevent disclosure.", "Do not inspect only the visible answer body when links and exports are also outputs.", "Do not log the secret while recording that a redaction gate fired."],
        "related": ["prompt-engineering/privacy-and-data-minimization", "prompt-engineering/output-sink-validation", "prompt-engineering/prompt-telemetry-privacy-budget"],
    },
    {
        "slug": "system-prompt-as-nonsecret-contract",
        "title": "System prompts: treat instructions as guidance, not a secret vault",
        "summary": "Keep credentials and authorization rules in systems the model cannot rewrite.",
        "definition": "A system prompt can describe task boundaries, response format, and tool-use intent. It is not a confidential storage location or an access-control layer. Users may probe for its contents, and the model may quote or paraphrase parts of its instructions. Keep credentials, hidden customer data, and permission decisions outside the prompt. A tool call should be checked against the authenticated principal, action, object, and current state by the application. If prompt wording leaks, the primary security question is whether the disclosed text grants any capability or exposes a secret that should never have been there.",
        "case": "A team embeds a service token and a list of administrator accounts in a long system message for a support bot, then asks it not to reveal them. A curious user requests the bot's setup. Even if most replies refuse, one paraphrased answer could expose the token. The fix is to remove the token, rotate it, and bind tool credentials in the server runtime. The prompt can still say that account exports require verification. The export endpoint enforces that rule against the user's session, so disclosure of the wording cannot authorize an export.",
        "sample": "Prompt: task, response schema, permitted tool intent.\nServer: credentials, account ownership, export authorization.\nTool call: verify principal + action + object + current state.\nTest: prompt disclosure attempt cannot reveal a credential.\nTest: copied prompt text cannot grant export access.",
        "cost": "Moving permissions to a server check adds a lookup or policy evaluation per effect, generally O(1) with indexed account data, though remote authorization calls add latency. This cost is small compared with a private-data breach or wrong-account action. Shorter prompts also avoid paying tokens for secret material that should not be there. Evaluate prompt-disclosure attempts, but do not confuse a model's refusal rate with proof of server security. A check must fail closed when the session or object scope cannot be verified.",
        "mistakes": ["Do not put credentials or customer lists in the system prompt.", "Do not treat hidden prompt wording as an access-control mechanism.", "Do not let a tool trust the model's claim that a user is authorized."],
        "related": ["prompt-engineering/role-priority-and-conflict-resolution", "prompt-engineering/tool-call-authorization-contract", "devops/secrets-and-configuration"],
    },
    {
        "slug": "high-impact-advice-review-gate",
        "title": "High-impact advice: route uncertain decisions to qualified review",
        "summary": "Keep generated explanations separate from professional decisions and external effects.",
        "definition": "A high-impact advice gate detects when an answer could be treated as a decision affecting health, finances, legal rights, access, or safety. The prompt should state the assistant's bounded task and preserve uncertainty, but a disclaimer alone does not make an unsupported recommendation safe. Require current verified evidence, a clearly identified decision owner, and a review path when facts are missing or the effect is consequential. Evaluate false reassurance and unnecessary escalation separately. The application must prevent the model from submitting an irreversible action while a case is still awaiting review.",
        "case": "An employee asks a benefits assistant whether a dependent is eligible for a costly treatment reimbursement. The record includes two plans with different terms and a policy excerpt that expired last quarter. A confident yes or no would be unsafe. The assistant identifies the conflicting plan IDs, says which document is stale, and routes the case to the benefits specialist with a compact evidence packet. It may explain the application steps that apply to either plan, but it cannot approve payment or imply a verified medical or coverage determination. A benign question about where to find the current plan document should still receive a direct answer.",
        "sample": "Case BN-274; plans: PL-8 and PL-11; policy excerpt expired.\nAllowed: explain application steps and name missing plan choice.\nBlocked: eligibility verdict and payment approval.\nReview packet: case ID, plan IDs, stale document ID, unresolved question.\nControl: current-plan location question receives direct help.",
        "cost": "A review route adds queue time and specialist effort; sending every routine question there creates delay without reducing consequential errors. Checking F required facts is O(F), while retrieving a current policy and obtaining human approval dominate latency. Design a narrow trigger from decision impact and missing evidence, and measure the share of cases that truly needed review. A model call saved by skipping verification is not economical if it leads to an incorrect payment or denial. Keep review packets concise and access-controlled.",
        "mistakes": ["Do not rely on a disclaimer to repair an unsupported determination.", "Do not approve an external effect from stale or conflicting evidence.", "Do not escalate a simple location question as though it were a benefits verdict."],
        "related": ["prompt-engineering/human-review-escalation", "prompt-engineering/retrieval-freshness-and-conflict", "prompt-engineering/selective-prediction-thresholds"],
    },
]

paths = ["prompt-engineering/" + spec["slug"] for spec in specs]
new_paths = set(paths + [project_path, quiz_path])
assert not new_paths.intersection(lookup)
titles = {entry["path"]: entry["title"] for entry in entries}
titles.update({path: spec["title"] for path, spec in zip(paths, specs)})
titles[project_path] = "Project: build a support safety boundary"
titles[quiz_path] = "Prompt safety decisions"


def link(path):
    assert path in titles, path
    return f'<a href="/{html.escape(path)}">{html.escape(titles[path])}</a>'


def links(paths_to_link):
    return "<ul>" + "".join(f"<li>{link(path)}</li>" for path in dict.fromkeys(paths_to_link)) + "</ul>"


def related(paths_to_link):
    return [{"path": path, "title": titles[path]} for path in dict.fromkeys(paths_to_link)]


def article(path, title, summary, body, section, order, connections, kind="tutorial"):
    entry = copy.deepcopy(lookup["prompt-engineering/evaluation-slice-design"])
    entry.update(id=str(uuid.uuid5(uuid.NAMESPACE_URL, "aitrove:" + path)),
                 path=path, title=title, summary=summary, body=body,
                 subject="prompt-engineering-production" if section == production else "prompt-engineering-project",
                 difficulty="Advanced", tags=["prompt engineering", "safety decisions"],
                 sort_order=order, status="published", published_at=stamp,
                 created_at=stamp, updated_at=stamp)
    entry["data"].update(kind=kind, reading_minutes=11 if kind == "tutorial" else 18,
                         author_path="authors/aitrove-editorial", subject_root=subject_root,
                         section_path=section, content_format="html", seo_ready=True,
                         related=related(connections))
    return entry


new_rows = []
for index, (path, spec) in enumerate(zip(paths, specs)):
    peers = [other for other in paths if other != path]
    connections = [production, subject_root] + spec["related"] + peers + [project_path, quiz_path]
    body = (
        "<p>" + html.escape(spec["definition"]) + "</p>"
        "<h2>Decision in practice</h2><p>" + html.escape(spec["case"]) + "</p>"
        '<pre><code class="language-text">' + html.escape(spec["sample"], quote=False) + "</code></pre>"
        "<h2>Performance and operating cost</h2><p>" + html.escape(spec["cost"]) + "</p>"
        "<h3>Common Mistakes</h3><ul>" + "".join("<li>" + html.escape(item) + "</li>" for item in spec["mistakes"]) + "</ul>"
        "<h2>Connected lessons</h2>" + links(connections)
    )
    new_rows.append(article(path, spec["title"], spec["summary"], body,
                            production, 26500 + index * 10, connections))

project_connections = paths + ["prompt-engineering/prompt-injection-red-team",
                                "prompt-engineering/output-sink-validation", quiz_path]
project_body = (
    "<p>This project defines the boundary for a fictional support assistant that answers billing questions, drafts account-change instructions, and prepares incident referrals. The assistant may read only records belonging to an authenticated requester. It has no payment or export authority. Build a request router, refusal and continuation policy, output gate, and escalation packet, then test the combination on benign and risky cases. The final deliverable is a release decision with reasons, not a claim that prompt wording alone made the workflow safe.</p>"
    "<h2>Route four requests</h2><p>Case AC-682 asks for its next invoice date and can receive that date from a verified billing field. A second request asks to change a bank destination and must enter the authenticated account-change flow. A third asks for another customer's invoice and must be denied without revealing whether that document exists. A fourth reports possible compromise and goes to the incident owner. Add a benign question about the contact policy; it should receive an answer rather than a blanket refusal. Store route codes and permission outcomes, not the raw bank destination.</p>"
    "<h2>Test leakage and high-impact advice</h2><p>A pasted note orders the assistant to export customers while the user asks only for an order update. The legitimate status request can continue after ownership verification; the pasted command cannot gain tool access. An internal note contains a full bank-routing value. Check both answer text and export filenames so the value cannot leave through another output sink. Remove credentials from the system prompt and enforce permissions at the export endpoint. Finally, test a benefits eligibility request with two plan IDs and an expired policy excerpt. The assistant should ask for the plan choice and route the consequential decision to a specialist, while still answering a separate question about where to find the current plan document.</p>"
    '<pre><code class="language-text">Request routes: verified read | authenticated change | deny disclosure | incident.\nTool scope: read AC-682 only; no payment or customer export.\nOutput gate: body, links, filenames, export payload.\nHigh-impact case BN-274: two plans, stale policy; no eligibility verdict.\nBenign controls: contact policy and current-plan document location.\nRelease gate: no private leak, wrong-account action, or blanket refusal.</code></pre>'
    "<h2>Performance and operating cost</h2><p>For N labeled cases and V prompt variants, one offline comparison requires O(NV) model calls plus permission checks and review of ambiguous outcomes. Field-level output scanning is O(L) in response length. Human escalation adds queue time, so measure false refusals and unnecessary specialist referrals alongside leaks and unauthorized effects. A release cannot pass merely because the model declines to answer everything. Preserve per-case traces with redacted fields, and retain the server authorization result independently of the model's explanation.</p>"
    "<h3>Common Mistakes</h3><ul><li>Do not use a prompt as the only account-access check.</li><li>Do not inspect just chat text while links or exports can carry private data.</li><li>Do not treat every benefits question as a final eligibility decision.</li></ul>"
    "<h2>Connected lessons</h2>" + links(project_connections)
)
new_rows.append(article(project_path, titles[project_path],
                        "Design a support assistant that routes requests, contains disclosures, and escalates consequential decisions.",
                        project_body, projects, 26560, project_connections, kind="project"))

questions = [
    ("An authenticated customer asks for the next invoice date on their own account. What route fits?", "Verified billing read", "Customer export", "Automatic payment change", "A scoped read can answer the ordinary question."),
    ("A user asks to change a bank destination. What must decide whether it can happen?", "The authenticated action workflow", "A role prompt", "A polite model reply", "The application owns permission for the effect."),
    ("A request seeks another customer's invoice. What should the reply avoid?", "Revealing the hidden invoice or whether it exists", "Explaining the verification path", "A neutral refusal", "A refusal should not leak details of a private record."),
    ("A pasted note asks for a customer export while the user wants an order update. What can continue?", "The verified order-status request", "The note's export command", "Any tool call named in the note", "Untrusted text is data, not new authority."),
    ("Why test a harmless question about contact policy?", "To detect a blanket false refusal", "To grant access to phone numbers", "To replace account checks", "A safety gate must preserve legitimate help."),
    ("An internal bank value appears in a generated filename. Which check catches it?", "A gate covering all output sinks", "A body-only text scan", "A longer system prompt", "Links and filenames are outputs too."),
    ("What is the safest place for a service credential?", "Server-managed secret storage", "The system prompt", "A hidden few-shot example", "Prompt text may be disclosed and is not secret storage."),
    ("A model says the user is an administrator. What should an export endpoint do?", "Check the authenticated principal and object scope itself", "Trust the model", "Trust the copied prompt wording", "The tool must enforce authorization independently."),
    ("Two benefits plans disagree and the cited policy is expired. What is supported?", "A review packet and explanation of missing facts", "A confident coverage approval", "An automatic reimbursement", "Stale, conflicting evidence cannot support the determination."),
    ("A user only asks where to find the current plan document. What fits?", "Give the verified location directly", "Block every benefits question", "Approve reimbursement", "The question is informational, not an eligibility verdict."),
    ("A new gate prevents leaks but refuses every ordinary question. What is wrong?", "False refusals make the workflow unusable", "Nothing; refusal rate alone proves safety", "The output is too short", "Evaluation must include benign controls."),
    ("Which trace is useful without copying private values?", "Route code, bundle ID, permission result, and redacted failure code", "Full bank destination in every log", "Only a model confidence phrase", "Decision metadata supports review with less exposure."),
]
quiz_entry = copy.deepcopy(lookup["quizzes/prompt-engineering-multimodal-evidence"])
quiz_entry.update(id=str(uuid.uuid5(uuid.NAMESPACE_URL, "aitrove:" + quiz_path)),
                  path=quiz_path, title=titles[quiz_path],
                  summary="Test routing, narrow refusals, output gates, server authority, and human review.",
                  body="<p>These cases ask which operation the assistant may perform and which check belongs outside the prompt. Include the benign controls when judging a safety gate.</p><h2>Safety lessons</h2>" + links(paths) + "<h2>Project and sections</h2>" + links([project_path, production, quizzes]),
                  sort_order=26570, status="published", published_at=stamp,
                  created_at=stamp, updated_at=stamp)
quiz_entry["data"].update(subject_root=subject_root, section_path=quizzes,
                          content_format="html", author_path="authors/aitrove-editorial",
                          seo_ready=True, duration_minutes=12,
                          related=related(paths + [project_path]),
                          questions=[{"prompt": prompt,
                                      "options": ([correct, distractor_a, distractor_b][index % 3:] + [correct, distractor_a, distractor_b][:index % 3]),
                                      "answer": (-index) % 3, "explanation": explanation}
                                     for index, (prompt, correct, distractor_a, distractor_b, explanation) in enumerate(questions)])
new_rows.append(quiz_entry)

for hub_path, selected, title, summary in [
    (production, paths, "Safety decision boundaries", "Route requests, refuse narrowly, validate output, and reserve high-impact decisions for review."),
    (projects, [project_path], "Support safety workflow", "Test permissions, output sinks, and benign controls in one support scenario."),
    (quizzes, [quiz_path], "Safety decisions quiz", "Choose the correct boundary for common support requests."),
]:
    hub = lookup[hub_path]
    hub["data"]["modules"].append({"title": title, "summary": summary, "lessons": selected})
    hub["body"] += "<h2>" + html.escape(title) + "</h2><p>" + html.escape(summary) + "</p>" + links(selected + [project_path, quiz_path])
    hub["updated_at"] = stamp

root_hub = lookup[subject_root]
root_hub["body"] += "<h2>Safety decisions in production</h2><p>A useful assistant routes requests by permitted effect, keeps private fields out of output, and escalates decisions it cannot support.</p>" + links(paths + [project_path, quiz_path])
root_hub["updated_at"] = stamp

backlinks = {
    "prompt-engineering/tool-call-authorization-contract": paths[0],
    "prompt-engineering/tool-result-instruction-quarantine": paths[1],
    "prompt-engineering/privacy-and-data-minimization": paths[2],
    "prompt-engineering/role-priority-and-conflict-resolution": paths[3],
    "prompt-engineering/human-review-escalation": paths[4],
    "prompt-engineering/output-sink-validation": paths[2],
    "prompt-engineering/prompt-injection-red-team": paths[1],
    "prompt-engineering/prompt-telemetry-privacy-budget": paths[2],
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
