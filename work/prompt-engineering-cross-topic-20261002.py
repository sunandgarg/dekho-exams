"""Connect Prompt Engineering releases to the site's DevOps, Python, and AI tools content."""

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

specs = [
    {
        "path": "prompt-engineering/prompt-evaluation-ci-gate",
        "title": "Prompt changes in CI: test the merge candidate",
        "summary": "Run deterministic checks on every change and reserve model replay for meaningful prompt differences.",
        "definition": "A prompt evaluation gate is a repeatable check applied to the exact prompt, model settings, tool schema, and evidence contract proposed for release. Put fast deterministic checks first: parse templates, verify required variables, validate output schemas, and execute local validators. Then replay a frozen labeled set for changes that can alter model behavior. CI should record the candidate revision and case-set version; a green run for an earlier branch is not proof about the current merge candidate. Stochastic outputs require raw case results and stable thresholds, not a claim that every run will produce identical text.",
        "case": "A claims team edits a prompt to make approval explanations shorter. The template renders, but a high-impact held-out case changes from review to approve when the receipt is absent. The CI job blocks that merge despite an improved average length score. A second change only corrects a typo in a non-executed comment; the team can run static checks and a small smoke set before a scheduled full replay, according to its documented policy. A reviewer inspects the failing case, prompt diff, model setting, and evidence snapshot. The job does not silently replace the failed case with a more favorable one.",
        "sample": "Merge candidate: prompt revision PE-118, schema V4, model setting MS-7.\nStatic gates: variables present; schema parses; tool names match catalog.\nReplay: frozen set EV-47, including missing receipt and wrong-account cases.\nBlock: any critical false approval or unauthorized effect.\nReport: per-case baseline and candidate output, slice counts, latency, cost.\nOn failure: preserve artifact and case IDs for review.",
        "cost": "Static validation is typically linear in template and schema size. A replay over N cases and V prompt variants requires roughly O(NV) model calls; large sets may run in a separate job when the release policy permits, but high-impact regression cases belong on the merge gate. Cache only when input, model, and settings match exactly. Flaky model judgments should be adjudicated rather than automatically rerun until green. Count dollars, elapsed time, and human review together with error rates; a cheap gate that misses a critical false approval is not economical.",
        "mistakes": ["Do not test a different commit from the one being merged.", "Do not allow aggregate improvement to hide a critical case failure.", "Do not rerun a flaky grader until it produces a passing result."],
        "related": ["prompt-engineering/release-regression-gate", "prompt-engineering/evaluation-data-leakage", "devops/continuous-integration", "devops/git-change-control"],
    },
    {
        "path": "prompt-engineering/prompt-release-artifact-bundle",
        "title": "Prompt release artifacts: version the whole decision path",
        "summary": "Package prompt text with the model, schemas, retrieval rules, and evaluation result used to approve it.",
        "definition": "A prompt release artifact is a versioned bundle of everything that can change the observed decision: template text, variable schema, model identifier and settings, tool catalog, retrieval filters, output parser, policy references, and evaluation report. A prompt string by itself cannot reproduce a result when its evidence source or tool handler has changed. Give the bundle a stable identifier and checksum, promote the same bundle through environments, and record which version handled each request. Keep secrets out of the artifact and bind environment-specific credentials at runtime.",
        "case": "A renewal assistant passes evaluation with prompt PE-118 against policy index PI-29 and parser V4. Staging later uses parser V5, which accepts an empty evidence list, while production still runs V4. Saying that both environments use PE-118 hides the real difference. The team packages the parser contract and index version with the prompt, reruns the affected cases, and promotes one checked bundle. During a canary, an unsupported approval appears in the high-impact slice. The operator rolls back the bundle pointer and verifies that new requests use the previous version; already completed effects are reconciled separately.",
        "sample": "Bundle ID: PEB-118.\nTemplate: PE-118; variables: VS-4; parser: V4.\nModel and settings: MS-7; tools: TC-12; retrieval index: PI-29.\nEvaluation: EV-47 results and critical gate status.\nPromotion: same bundle digest in staging and canary.\nRollback: restore prior digest; reconcile in-flight effects by receipt.",
        "cost": "A manifest has small storage cost, but pinning a retrieval index or policy version may require snapshot retention. Building a digest over L bytes is O(L); evaluating N cases against V bundle variants costs O(NV) model calls. The benefit is causal diagnosis: when behavior changes, the team can identify the altered component rather than rewriting prompt prose at random. Preserve only the artifacts and payload access needed for investigation. Rollback changes future behavior, but it cannot undo a payment, ticket, or other external effect already committed.",
        "mistakes": ["Do not call a prompt string alone a reproducible release.", "Do not promote different parser or retrieval versions under one bundle ID.", "Do not assume rollback reverses completed external actions."],
        "related": ["prompt-engineering/prompt-version-rollout", "prompt-engineering/model-migration-contract", "devops/artifact-promotion", "devops/progressive-delivery"],
    },
    {
        "path": "prompt-engineering/prompt-telemetry-privacy-budget",
        "title": "Prompt telemetry: measure failures without copying private payloads",
        "summary": "Log versioned decision events and restricted evidence pointers instead of every raw prompt and response.",
        "definition": "Prompt telemetry connects a request to the versioned decision path and its checks while limiting exposure of user data. Record a trace ID, prompt bundle ID, case class, model-call status, validator outcomes, tool-call names, latency, token counts, and effect receipts. Retain raw text only under a defined access and retention policy when it is necessary for investigation. Hashing or redacting a value does not automatically make it harmless; identifiers can still link to people or accounts. Design the event schema before turning on verbose model logging.",
        "case": "A support assistant processes ticket TK-714 with a customer's payment details in the body. The operational dashboard needs to know that prompt bundle PEB-118 produced a schema failure and one bounded retry. It does not need the card digits or the full ticket text. The event stores the ticket's internal reference, bundle ID, validator failure code, retry count, and latency. A separate protected review store holds a short, redacted sample for an authorized investigator. A test injects a secret-looking value into a tool result and checks that neither ordinary logs nor error traces copy it.",
        "sample": "Trace: TR-714; bundle: PEB-118; case_class: billing.\nModel calls: 2; validator: schema_missing_field; final_state: review.\nLatency: 1840 ms; input/output tokens: 936/127.\nTool effect: none; receipt: none.\nOrdinary log excludes ticket body, payment details, and raw tool payload.\nProtected sample: redacted, access-controlled, time-limited.",
        "cost": "An event with fixed fields has O(1) storage per request apart from identifiers and labels; retaining full prompts and responses grows with payload length and can multiply storage and exposure. Aggregating M events is O(M) in the simple case. Redaction, access control, and retention jobs add operational work, so log only fields that support a named diagnostic or audit need. Sample high-volume success traffic while retaining complete counts of failures and external effects. A trace without bundle and case IDs is hard to reproduce; a trace that copies every private field is unnecessarily risky.",
        "mistakes": ["Do not enable raw prompt logging by default in a private workflow.", "Do not assume a hash removes all reidentification risk.", "Do not omit effect receipts and validation failures from the trace."],
        "related": ["prompt-engineering/prompt-trace-observability", "prompt-engineering/privacy-and-data-minimization", "devops/observability-signals", "devops/secrets-and-configuration"],
    },
]

new_paths = {spec["path"] for spec in specs}
assert not new_paths.intersection(lookup)
titles = {entry["path"]: entry["title"] for entry in entries}
titles.update({spec["path"]: spec["title"] for spec in specs})


def link(path):
    assert path in titles, path
    return f'<a href="/{html.escape(path)}">{html.escape(titles[path])}</a>'


def links(paths):
    return "<ul>" + "".join(f"<li>{link(path)}</li>" for path in dict.fromkeys(paths)) + "</ul>"


def related(paths):
    return [{"path": path, "title": titles[path]} for path in dict.fromkeys(paths)]


new_rows = []
for index, spec in enumerate(specs):
    peers = [other["path"] for other in specs if other["path"] != spec["path"]]
    connections = [production, subject_root] + spec["related"] + peers + ["prompt-engineering/retrieval-quality-gate-project"]
    body = (
        "<p>" + html.escape(spec["definition"]) + "</p>"
        "<h2>Decision in practice</h2><p>" + html.escape(spec["case"]) + "</p>"
        '<pre><code class="language-text">' + html.escape(spec["sample"], quote=False) + "</code></pre>"
        "<h2>Performance and operating cost</h2><p>" + html.escape(spec["cost"]) + "</p>"
        "<h3>Common Mistakes</h3><ul>" + "".join("<li>" + html.escape(item) + "</li>" for item in spec["mistakes"]) + "</ul>"
        "<h2>Connected lessons</h2>" + links(connections)
    )
    entry = copy.deepcopy(lookup["prompt-engineering/evaluation-slice-design"])
    entry.update(id=str(uuid.uuid5(uuid.NAMESPACE_URL, "aitrove:" + spec["path"])),
                 path=spec["path"], title=spec["title"], summary=spec["summary"],
                 body=body, subject="prompt-engineering-production", difficulty="Advanced",
                 tags=["prompt engineering", "release engineering"], sort_order=26200 + index * 10,
                 status="published", published_at=stamp, created_at=stamp, updated_at=stamp)
    entry["data"].update(kind="tutorial", reading_minutes=10,
                         author_path="authors/aitrove-editorial", subject_root=subject_root,
                         section_path=production, content_format="html", seo_ready=True,
                         related=related(connections))
    new_rows.append(entry)

production_hub = lookup[production]
production_hub["data"]["modules"].append({
    "title": "Delivery and telemetry",
    "summary": "Carry prompt evaluation into CI, promotion, and privacy-aware operations.",
    "lessons": [spec["path"] for spec in specs],
})
production_hub["body"] += "<h2>Delivery and telemetry</h2><p>Connect the tested prompt to a merge gate, a complete release bundle, and a trace that preserves decisions without copying private payloads.</p>" + links([spec["path"] for spec in specs] + ["devops/continuous-integration", "devops/artifact-promotion", "devops/observability-signals"])
production_hub["updated_at"] = stamp

root_hub = lookup[subject_root]
root_hub["body"] += "<h2>From prompt to release</h2><p>The production path continues through merge checks, versioned bundles, and privacy-aware telemetry.</p>" + links([spec["path"] for spec in specs])
root_hub["updated_at"] = stamp

prompt_crosslinks = {
    "prompt-engineering/schema-repair-retry-budget": ["python/json-validation", "python/json-duplicate-keys"],
    "prompt-engineering/read-only-sql-generation-gate": ["sql/guide-to-databases"],
    "prompt-engineering/code-change-acceptance-contract": ["ai-tools/chatgpt-codex/coding-review-checklist"],
    "prompt-engineering/candidate-sampling-and-verifier": ["python/testing"],
    "prompt-engineering/evaluation-slice-design": ["data-science/data-science-for-beginners"],
    "prompt-engineering/model-migration-contract": ["devops/artifact-promotion"],
    "prompt-engineering/prompt-version-rollout": ["devops/progressive-delivery"],
    "prompt-engineering/prompt-trace-observability": ["devops/observability-signals"],
    "prompt-engineering/privacy-and-data-minimization": ["devops/secrets-and-configuration"],
    "prompt-engineering/human-review-escalation": ["devops/incident-response"],
    "prompt-engineering/release-regression-gate": ["prompt-engineering/prompt-evaluation-ci-gate"],
    "prompt-engineering/retrieval-quality-gate-project": ["prompt-engineering/prompt-release-artifact-bundle"],
}
for page_path, targets in prompt_crosslinks.items():
    entry = lookup[page_path]
    assert entry["body"].startswith("<p>") and all(target in titles for target in targets)
    entry["body"] += "<h2>Related implementation</h2>" + links(targets)
    entry["data"]["related"] = related([item["path"] for item in entry["data"].get("related", [])] + targets)
    entry["updated_at"] = stamp

external_backlinks = {
    "devops/continuous-integration": "prompt-engineering/prompt-evaluation-ci-gate",
    "devops/artifact-promotion": "prompt-engineering/prompt-release-artifact-bundle",
    "devops/observability-signals": "prompt-engineering/prompt-telemetry-privacy-budget",
    "devops/progressive-delivery": "prompt-engineering/prompt-version-rollout",
    "devops/secrets-and-configuration": "prompt-engineering/privacy-and-data-minimization",
    "devops/incident-response": "prompt-engineering/incident-handoff-evaluation-project",
    "python/json-validation": "prompt-engineering/schema-repair-retry-budget",
    "python/testing": "prompt-engineering/candidate-sampling-and-verifier",
}
for page_path, target in external_backlinks.items():
    entry = lookup[page_path]
    assert entry["status"] == "published" and entry["data"].get("content_format") == "html", page_path
    entry["body"] += "<p><strong>Related Prompt Engineering lesson:</strong> " + link(target) + ".</p>"
    entry["updated_at"] = stamp

entries.extend(new_rows)
fixture.write_text(json.dumps(entries, ensure_ascii=False, indent=2) + "\n")
print(json.dumps({"newLessons": len(new_rows), "promptCrosslinkPages": len(prompt_crosslinks),
                  "externalBacklinkPages": len(external_backlinks),
                  "newPaths": [entry["path"] for entry in new_rows]}))
