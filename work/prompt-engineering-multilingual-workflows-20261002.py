"""Add checked multilingual prompt workflows with a localization project."""

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
project_path = "prompt-engineering/multilingual-order-notice-project"
quiz_path = "quizzes/prompt-engineering-multilingual-workflows"

placeholder_code = '''from collections import Counter
import re

source_notice = "Shipment {shipment_id} is scheduled for {dispatch_date}."
localized_notice = "L'expédition {shipment_id} est prévue pour le {dispatch_date}."
placeholder_pattern = re.compile(r"\\{([a-z][a-z0-9_]*)\\}")

def placeholder_counts(message: str) -> Counter:
    return Counter(placeholder_pattern.findall(message))

if placeholder_counts(source_notice) != placeholder_counts(localized_notice):
    raise ValueError("localized placeholders differ from source")
print("placeholder check: pass")'''

specs = [
    {
        "slug": "translation-glossary-placeholder-contract",
        "title": "Translation prompts: preserve terms and machine placeholders",
        "summary": "Give the model a locale-specific brief while validating placeholders outside its prose.",
        "definition": "A translation prompt should state source and target locale, audience, approved glossary, protected product names, and the exact strings that must remain machine-readable. Translation quality and placeholder integrity are separate checks. The model may choose natural wording around a token, but it must not rename, drop, duplicate, or translate a named placeholder. Validate the token multiset in the application, then review meaning and tone with a competent speaker. This small validator handles simple brace-delimited names; a product using nested message syntax needs a parser for that syntax rather than a regular expression.",
        "case": "A parcel service localizes a dispatch notice for French-speaking customers in Canada. The English source includes shipment_id and dispatch_date variables. A draft reads naturally but replaces dispatch_date with date_depart; the renderer would leave an unresolved token. Another draft preserves both tokens but changes the approved service name. The assistant receives a glossary and a note that the product name stays unchanged. The application compares placeholder counts, while a reviewer checks that the departure meaning and level of formality survive. The date value remains structured data until the locale formatter renders it.",
        "sample": placeholder_code,
        "sample_lang": "python",
        "cost": "For S source strings and total length L, simple placeholder scanning is O(L) time and O(P) space for P distinct placeholder names. Human meaning review is the larger cost; a token match cannot detect a mistranslated warning or changed promise. Batch strings by feature with context, not as unrelated fragments, so terminology stays consistent. Record glossary version and locale tag with the generated draft. A second model pass may catch an omission, but it does not replace deterministic token validation or a qualified language review for consequential copy.",
        "mistakes": ["Do not translate a machine placeholder into a new identifier.", "Do not assume matching placeholders prove semantic accuracy.", "Do not send an ICU-style nested message through a simple brace matcher."],
        "related": ["prompt-engineering/template-variable-escaping", "prompt-engineering/multilingual-equivalence-check", "python/unicode-normalization"],
        "section": applications,
    },
    {
        "slug": "locale-formatting-structured-values",
        "title": "Locale-aware prompts: keep values typed until rendering",
        "summary": "Separate translated language from numbers, dates, currency, and plural selection.",
        "definition": "A locale-aware prompt can draft surrounding words, but the application should retain dates, amounts, counts, and units as typed values. Pass a locale identifier to a tested formatter when rendering; do not ask the model to invent punctuation conventions from memory. The same language can have regional conventions, and a translated sentence may need a different plural structure. Use a complete message pattern rather than concatenated fragments when quantity changes grammar. Test zero, one, two, and larger counts where the locale's plural behavior makes those cases distinct, and keep timezone separate from the display locale.",
        "case": "An order notice for OR-958 contains 1,234.50 units of CAD and a dispatch instant of 2026-11-04T18:30:00Z. The assistant should not rewrite the amount as a string before the application knows whether the customer requested English Canada or French Canada. Nor should it assume that a date displayed to a Montreal user has the same calendar day as the UTC instant. The prompt returns the message key and typed fields; the UI formats them after the customer's locale and time zone are resolved. A reviewer checks that the translated text does not change the amount or promise a delivery day the source did not state.",
        "sample": "Order OR-958; amount_value=1234.50; currency=CAD.\nDispatch_instant=2026-11-04T18:30:00Z.\nMessage key=dispatch_notice; locale=fr-CA; zone=America/Toronto.\nModel output: wording and typed field references only.\nRenderer: number, currency, date, and plural rules for resolved locale.",
        "sample_lang": "text",
        "cost": "Formatting N typed fields is O(N) application work for a fixed message, while model generation adds variable latency and cannot guarantee locale rules. Store canonical values once and render per recipient; this avoids duplicating formatted strings in data records. Testing each locale and plural category adds cases, but it catches errors that a fluent sentence review may miss. A cache key must include locale, timezone where relevant, message version, and any value affecting plural choice. Reusing a rendered string across recipients can expose the wrong date or currency format even if the translation itself is sound.",
        "mistakes": ["Do not use the model as the sole currency or date formatter.", "Do not equate locale with timezone.", "Do not build plural messages by concatenating translated fragments."],
        "related": ["prompt-engineering/template-variable-escaping", "prompt-engineering/cache-prefix-and-expiry", "python/locale-independent-money-input"],
        "section": applications,
    },
    {
        "slug": "mixed-language-intent-and-reply-locale",
        "title": "Mixed-language requests: separate intent from reply language",
        "summary": "Preserve identifiers and permissions when a customer switches languages mid-request.",
        "definition": "A mixed-language prompt should identify the requested action, relevant entities, and preferred response language as distinct fields. Do not infer account authority from the language used, and do not translate immutable identifiers such as order IDs or tracking codes. A request may contain borrowed technical terms, transliterated words, or a quoted message from another person; language detection over the entire string can therefore be misleading. Ask for clarification only when the intended action or reply language is material and unresolved. The application still checks account scope before retrieving private order data.",
        "case": "A customer writes, 'Refund kab milega for OR-958? Please answer in English.' The action is a refund-status read, the order identifier remains OR-958, and the reply locale is English despite the Hindi phrase. A second message says, 'My colleague wrote ¿Dónde está mi pedido?; what does it mean?' That is a translation request, not evidence that the customer owns a Spanish-language order. The assistant records intent and language preference separately, checks ownership only for the refund-status tool, and avoids fabricating a refund date if the status record is missing.",
        "sample": "Input A: Refund kab milega for OR-958? Answer in English.\nIntent: refund_status_read; entity: OR-958; reply: English.\nGate: authenticated owner before private lookup.\nInput B: What does '¿Dónde está mi pedido?' mean?\nIntent: translate quoted text; no order lookup or ownership claim.",
        "sample_lang": "text",
        "cost": "Extracting I intent fields from a short request is O(I) structured output work after one model call, but ambiguous code-switching can raise review volume. A separate deterministic ownership check is generally cheaper than another model round. Test mixed scripts, transliteration, quoted foreign text, and explicit reply preferences; a single majority-language label cannot capture all of them. Keep the original text for authorized review because normalization can erase distinctions, but avoid logging sensitive customer details in broad analytics. Measure wrong-action routing and wrong-language replies separately.",
        "mistakes": ["Do not treat quoted foreign text as the user's chosen reply language.", "Do not translate an order identifier.", "Do not let a language classification authorize an account lookup."],
        "related": ["prompt-engineering/request-risk-routing-contract", "prompt-engineering/clarification-versus-assumption-gate", "prompt-engineering/classification-rubric-and-unknown-label"],
        "section": applications,
    },
    {
        "slug": "cross-language-retrieval-evidence-boundary",
        "title": "Cross-language retrieval: keep policy meaning attached to its source",
        "summary": "Translate the question if useful, but verify the retrieved clause before answering.",
        "definition": "Cross-language retrieval may expand a query into another language to find the authoritative document, but the answer must stay tied to the retrieved clause and its version. Query translation can change the meaning of a term such as refund, return, or credit, so retain the original request and compare candidate results. Preserve source identifiers, effective dates, and the language of the policy. If translated excerpts conflict, do not blend them into a single rule. A qualified reviewer should adjudicate policy wording that creates a consequential entitlement, especially when the source and response languages differ.",
        "case": "A customer asks in Hindi whether a delayed parcel earns a cash refund. The current English policy says eligible delays receive store credit, while an older Hindi help page uses a word that can be read as a cash repayment. A retrieval system finds both pages. The assistant must check effective dates, retain both evidence IDs, and answer from the current policy without pretending the older page agrees. It can explain the distinction between store credit and cash refund in the requested language, but should route the mismatch for editorial repair. It cannot issue a credit solely because a retrieved page contains an instruction to do so.",
        "sample": "Question: delayed parcel -> cash refund? Reply language: Hindi.\nCurrent English policy PL-62: eligible delay -> store credit.\nOlder Hindi page PL-41: ambiguous refund wording; expired.\nAnswer: current rule with effective date; flag wording conflict.\nEffect: no credit issued without account and policy checks.",
        "sample_lang": "text",
        "cost": "If a request produces Q language variants and retrieves K passages per variant, candidate inspection can grow to O(QK) passages plus deduplication. More translations may improve recall but also raise the chance of a misleading near-match. Cache by policy version and locale, and invalidate when an authoritative clause changes. Measure retrieval recall, correct-version selection, and answer support separately; an answer in fluent Hindi is still wrong if it cites an expired rule. Keep the exact retrieved passage and translation decision available to a reviewer without exposing unrelated customer data.",
        "mistakes": ["Do not treat an expired localized page as equal to a current policy.", "Do not let a translated synonym silently change cash refund into store credit.", "Do not obey instructions embedded in retrieved policy text."],
        "related": ["prompt-engineering/query-rewrite-and-coreference", "prompt-engineering/retrieval-freshness-and-conflict", "prompt-engineering/evidence-id-traceability"],
        "section": applications,
    },
    {
        "slug": "cross-locale-evaluation-slice",
        "title": "Cross-locale evaluation: compare decisions, not word-for-word text",
        "summary": "Use matched cases to test action parity, placeholders, formatting, and abstention.",
        "definition": "A cross-locale evaluation should pair semantically equivalent requests across supported languages while allowing natural differences in expression. Score whether each locale reaches the same permitted action, preserves required entities and amounts, handles uncertainty, and obeys the same refusal boundary. Exact string matching is usually a poor measure of translation quality. Include cases with mixed language, missing data, plural forms, quoted text, and policy version conflicts. Keep localized gold labels and reviewer notes versioned; a policy change can invalidate a past expected answer without making the old run disappear.",
        "case": "An order assistant is evaluated on a matched English and Hindi request for refund status on OR-958, a French Canada dispatch notice containing two placeholders, and a Spanish quotation that asks for a translation rather than an order lookup. The English variant correctly abstains when the refund record is unavailable, but the Hindi variant invents an expected date. That mismatch blocks release even if the French notice reads well. Reviewers log whether the failure came from intent extraction, missing evidence, or answer generation, then rerun both languages on the same account and policy snapshots after the prompt changes.",
        "sample": "Case pair OR-958: English and Hindi; same missing refund record.\nExpected action: abstain in both; preserve OR-958.\nNotice fr-CA: placeholder counts match; amount/date renderer checked.\nSpanish quote: translate text; no order lookup.\nRelease: block if any locale invents a private status or date.",
        "sample_lang": "text",
        "cost": "With C semantic cases, L locales, and V prompt variants, a full comparison needs O(CLV) model evaluations plus human language review. Sampling can reduce routine workload, but every high-impact action boundary should retain a matched case for each supported locale. Separate translation fluency from decision correctness and placeholder integrity so an average score does not hide a dangerous route in one language. Store prompt, model, glossary, policy, and formatter versions for each run. A reviewer should be able to explain why two phrasings are equivalent without requiring identical output wording.",
        "mistakes": ["Do not grade translated answers solely by exact string equality.", "Do not allow a failure in one language to be averaged away by another.", "Do not compare locale runs made against different policy snapshots."],
        "related": ["prompt-engineering/multilingual-equivalence-check", "prompt-engineering/evaluation-slice-design", "prompt-engineering/paired-prompt-evaluation-uncertainty"],
        "section": production,
    },
]

paths = ["prompt-engineering/" + spec["slug"] for spec in specs]
assert not set(paths + [project_path, quiz_path]).intersection(lookup)
titles = {entry["path"]: entry["title"] for entry in entries}
titles.update({path: spec["title"] for path, spec in zip(paths, specs)})
titles[project_path] = "Project: release a multilingual order notice safely"
titles[quiz_path] = "Multilingual prompt workflow decisions"


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
    entry.update(id=str(uuid.uuid5(uuid.NAMESPACE_URL, "aitrove:" + path)),
                 path=path, title=title, summary=summary, body=body,
                 subject=subject, difficulty="Advanced", tags=["prompt engineering", "multilingual workflows"],
                 sort_order=order, status="published", published_at=stamp,
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
            + f'<pre><code class="language-{spec["sample_lang"]}">' + html.escape(spec["sample"], quote=False) + "</code></pre>"
            + "<h2>Performance and operating cost</h2><p>" + html.escape(spec["cost"]) + "</p>"
            + "<h3>Common Mistakes</h3><ul>" + "".join("<li>" + html.escape(mistake) + "</li>" for mistake in spec["mistakes"]) + "</ul>"
            + "<h2>Connected lessons</h2>" + links(connections))
    new_rows.append(article(path, spec["title"], spec["summary"], body, spec["section"], 28700 + index * 10, connections))

project_connections = paths + ["prompt-engineering/template-variable-escaping", "prompt-engineering/tool-call-authorization-contract", "html/multilingual-case-project", quiz_path]
project_body = (
    "<p>A fictional parcel service is releasing order notices and a support assistant in English, Hindi, and French Canada. Build a release packet that contains source strings, locale tags, glossary version, machine placeholders, typed monetary and date values, account-permission checks, current policy evidence, and matched evaluation cases. The prompt may draft language and identify ambiguous requests. It cannot rewrite order IDs, decide a customer's account scope, or format a date by guessing the user's timezone. The final artifact is a release decision with exact failures and owners.</p>"
    "<h2>Prepare three workflows</h2><p>First, localize the shipment notice for OR-958 while preserving shipment_id and dispatch_date. Run the placeholder check, then ask a French Canada reviewer to inspect meaning and terminology. Second, render the amount 1,234.50 CAD and dispatch instant 2026-11-04T18:30:00Z from typed fields after resolving locale and time zone. Third, route 'Refund kab milega for OR-958? Please answer in English' to a permission-checked refund-status read. A quoted Spanish sentence asking what it means must route to translation, not a private order lookup.</p>"
    "<h2>Resolve policy and evaluate</h2><p>Retrieve the current policy PL-62 and older localized page PL-41 for a delayed parcel question. Keep both evidence IDs and effective dates. Explain that the current rule concerns store credit, flag the ambiguous older wording, and do not issue any effect without the account and policy checks. Build matched English and Hindi cases with a missing refund record: both must abstain. Include a French notice with placeholders and plural or formatting checks, plus the quoted Spanish control. If one locale invents a refund date, block promotion even if the average fluency rating improves.</p>"
    '<pre><code class="language-text">OR-958: preserve order ID, shipment_id, dispatch_date.\nTyped amount=1234.50 CAD; instant=2026-11-04T18:30:00Z.\nMixed Hindi/English request: refund-status read, English reply.\nSpanish quoted text: translation only; no account lookup.\nCurrent PL-62 beats expired PL-41; flag wording conflict.\nGate: equal permitted actions and abstention across matched locales.</code></pre>'
    "<h2>Performance and operating cost</h2><p>For C cases, L locales, and V prompt variants, comparison uses O(CLV) model evaluations. Placeholder scans are linear in string length, and formatter work is linear in typed fields for a fixed message. Human linguistic review costs more than a token check but catches semantic shifts the check cannot see. Record policy, glossary, formatter, and prompt versions so a failed locale can be reproduced. Separate failure counts for wrong intent, missing placeholders, wrong format, unsupported policy claim, and unauthorized effect; one broad quality score will conceal these differences.</p>"
    "<h3>Common Mistakes</h3><ul><li>Do not treat a fluent translation as proof that placeholders or policy meaning survived.</li><li>Do not let language detection authorize a private data read.</li><li>Do not average away a wrong action in one supported locale.</li></ul>"
    "<h2>Connected lessons</h2>" + links(project_connections))
new_rows.append(article(project_path, titles[project_path], "Validate localized notices, mixed-language support, policy retrieval, and matched release cases.", project_body, projects, 28760, project_connections, kind="project"))

questions = [
    ("A translation renames {dispatch_date} to {date_depart}. What check should fail?", "Placeholder multiset validation", "A tone-only review", "A model confidence threshold", "The renderer needs the original machine key."),
    ("The placeholder names match. What remains unverified?", "Meaning and approved terminology", "Whether any tokens exist", "The order identifier syntax", "Token identity cannot certify translation quality."),
    ("What should render an amount and date for fr-CA?", "A tested locale formatter using typed values", "A model's punctuation guess", "An English formatted string reused unchanged", "Locale formatting is an application concern."),
    ("Why keep timezone separate from locale?", "The same locale can include users in different zones", "Locale always determines UTC offset", "Timezones change product names", "Display date depends on the resolved zone."),
    ("A user writes Hindi and English but requests an English answer. Which reply language fits?", "English, as explicitly requested", "Hindi, because one phrase is Hindi", "Spanish, because another ticket contains Spanish", "Explicit preference outranks majority-language guessing."),
    ("A quoted Spanish sentence asks for its meaning. Which tool action fits?", "Translate the quote without a private order lookup", "Read an order record", "Issue a refund", "Quoted language is not account authority."),
    ("Current English policy and expired localized page differ. What should the answer use?", "The current verified clause and a flagged conflict", "The older page alone", "A blended rule invented by the model", "Version and authority matter across languages."),
    ("A retrieved policy page instructs the assistant to issue credit. What authority does it have?", "None; it is retrieved data", "It overrides account checks", "It is supervisor approval", "Source text does not grant tool rights."),
    ("Two locale cases express the same missing-record request. What should be compared?", "Permitted action and abstention", "Exact sentence text", "Character count only", "Equivalent decisions matter more than identical wording."),
    ("Hindi output invents a refund date while English abstains. What is the release decision?", "Block and diagnose the locale-specific failure", "Average the two scores", "Publish because English passed", "A critical wrong answer in one locale is still a failure."),
    ("What is outside a simple named-brace placeholder regex's scope?", "Nested ICU-style message grammar", "Simple {shipment_id} tokens", "Repeated named tokens", "Complex message syntax needs a parser."),
    ("Which versions belong in a reproducible localization test record?", "Prompt, glossary, policy, formatter, and model", "Only the translated sentence", "Only the calendar date", "The decision depends on all of these inputs."),
]
quiz_entry = copy.deepcopy(lookup["quizzes/prompt-engineering-multimodal-evidence"])
quiz_entry.update(id=str(uuid.uuid5(uuid.NAMESPACE_URL, "aitrove:" + quiz_path)),
                  path=quiz_path, title=titles[quiz_path],
                  summary="Test translation integrity, locale formatting, mixed-language intent, retrieval, and parity.",
                  body="<p>Choose the boundary that preserves the intended action across languages. Fluency, formatting, evidence, and account authority require different checks.</p><h2>Lessons</h2>" + links(paths) + "<h2>Project and sections</h2>" + links([project_path, applications, production, quizzes]),
                  sort_order=28770, status="published", published_at=stamp,
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
    (applications, paths[:4], "Multilingual application contracts", "Preserve terms and placeholders, render typed values, route mixed-language intent, and verify policy."),
    (production, paths[4:], "Cross-locale evaluation", "Pair semantic cases across languages and compare decisions."),
    (projects, [project_path], "Multilingual order notice", "Release a localization and support workflow with checked evidence."),
    (quizzes, [quiz_path], "Multilingual workflow quiz", "Test integrity, authority, and parity boundaries."),
]:
    hub = lookup[hub_path]
    hub["data"]["modules"].append({"title": title, "summary": summary, "lessons": selected})
    hub["body"] += "<h2>" + html.escape(title) + "</h2><p>" + html.escape(summary) + "</p>" + links(selected + [project_path, quiz_path])
    hub["updated_at"] = stamp

root_hub = lookup[subject_root]
root_hub["body"] += "<h2>Multilingual prompt workflows</h2><p>Keep translation, formatting, intent, evidence, and permissions independently checkable.</p>" + links(paths + [project_path, quiz_path])
root_hub["updated_at"] = stamp

backlinks = {
    "prompt-engineering/multilingual-equivalence-check": paths[4],
    "prompt-engineering/template-variable-escaping": paths[0],
    "prompt-engineering/request-risk-routing-contract": paths[2],
    "prompt-engineering/retrieval-freshness-and-conflict": paths[3],
    "prompt-engineering/evaluation-slice-design": paths[4],
    "python/locale-independent-money-input": paths[1],
    "html/multilingual-case-project": project_path,
}
for old_path, new_path in backlinks.items():
    entry = lookup[old_path]
    entry["body"] += "<p><strong>Continue with:</strong> " + link(new_path) + ".</p>"
    entry["data"]["related"] = related([item["path"] for item in entry["data"]["related"]] + [new_path])
    entry["updated_at"] = stamp

entries.extend(new_rows)
fixture.write_text(json.dumps(entries, ensure_ascii=False, indent=2) + "\n")
print(json.dumps({"newLessons": len(specs), "newProjects": 1, "newQuizzes": 1,
                  "newPaths": [entry["path"] for entry in new_rows]}))
