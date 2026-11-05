"""Add original authorized-retrieval prompt lessons, project, and quiz."""

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
project_path = "prompt-engineering/meridian-maintenance-knowledge-assistant-project"
quiz_path = "quizzes/prompt-engineering-authorized-retrieval"

specs = [
    {
        "slug": "retrieval-identity-and-document-permission-gate",
        "title": "Retrieval prompts: enforce document permission first",
        "summary": "Resolve caller identity and document access before any passage enters model context.",
        "definition": "An enterprise retrieval prompt cannot enforce document permissions by asking the model to ignore forbidden passages. Authentication, tenant scope, document access, and permission changes belong to a trusted retrieval service. That service must obtain the caller's identity from the application session, filter candidate documents before context assembly, and fail closed when entitlement data is missing. The prompt receives only permitted passages and stable evidence identifiers. Treat document metadata supplied by the user as a request for a filter, not an authorization token. A citation to a restricted document is a disclosure even when the answer omits its full text.",
        "case": "Meridian Maintenance stores equipment instructions and separate restricted contract notes. A field technician asks how to reset pump P-47. A restricted contract page mentions the same pump and ranks first by text similarity, but the technician has no contract access. The retrieval service excludes that page before ranking and sends the model only two approved maintenance passages. The answer explains the reset with their evidence IDs. If the entitlement service times out, the assistant does not search unrestricted content and hope the prompt will hide it; it returns a bounded access-unavailable response. A supervisor with a different verified identity may see additional material through a separate request.",
        "sample": "Caller identity: authenticated technician T-47 from server session.\nAllowed corpus: maintenance manuals, site M-12.\nExcluded before model context: restricted contract C-91.\nRetrieved evidence: M-12/P47/A and M-12/P47/B.\nOn entitlement timeout: stop; do not fall back to global search.",
        "cost": "Permission filtering adds an entitlement lookup and candidate restriction to every retrieval request. With an indexed permission field, selection depends on the search system; a naive scan across N documents would cost O(N). Cache grants only within their validity window and invalidate them when access changes, or a stale cache can leak a revoked page. The model's token cost should fall when forbidden and irrelevant passages never enter context. Count denied candidates in protected telemetry, but do not expose their titles to an unauthorized caller.",
        "mistakes": ["Do not let the user supply their own access-group string as proof.", "Do not retrieve globally and ask the model to ignore restricted hits.", "Do not reveal a denied document's title in a fallback answer."],
        "related": ["prompt-engineering/retrieval-evidence-selection", "prompt-engineering/privacy-and-data-minimization", "prompt-engineering/output-sink-validation"],
        "section": applications,
    },
    {
        "slug": "retrieval-candidate-recall-exact-token-and-semantic-match",
        "title": "Retrieval prompts: balance exact identifiers and semantic recall",
        "summary": "Use checked identifiers and broad candidates without bypassing permission filters.",
        "definition": "The retrieval prompt should preserve exact identifiers, units, and site scope while asking for conceptual matches. Dense similarity can find related wording but miss a specific part code; keyword search can find the code but miss a paraphrased procedure. Candidate generation may combine both, then deduplicate by document and passage identity. Apply the same authorization constraint to every branch before merging results. A model-rewritten query is a search aid, not a replacement for the original request: retain the original entity and reject rewrites that change it. Retrieval recall is measured against answer-bearing authorized passages, not against a list of merely similar texts.",
        "case": "A technician asks for the P-47 seal reset on site M-12. One approved manual says 'P-47 seal reset'; another describes 'restore the gland pressure after seal service' without the code in its heading. An exact-token search and a semantic search each contribute a candidate. A third hit concerns pump P-74 and should be rejected after identifier checking. The restricted C-91 contract remains absent from both candidate streams. The prompt sees two authorized passages with document version and section ID, then asks whether they cover the same maintenance state or distinct steps. It does not merge them merely because both mention seals.",
        "sample": "Original request: site M-12, pump P-47, seal reset.\nExact branch: preserve P-47 and M-12.\nSemantic branch: gland-pressure restoration after seal service.\nFilter both branches by server-authorized corpus.\nDeduplicate passage IDs; reject P-74 identifier mismatch.",
        "cost": "If exact and semantic search return K and S candidates, deduplication with a set is O(K+S) time and memory before reranking. Two search branches cost more latency and index work than one, so use them for queries where exact codes and conceptual language both matter. A broadened candidate pool helps recall but can lower precision; measure whether the correct authorized passage survives the final context budget. Keep the original query, rewritten queries, and candidate IDs in a private trace for failure analysis without copying raw restricted text into logs.",
        "mistakes": ["Do not let a semantic near-match replace P-47 with P-74.", "Do not run one branch without the caller's permission filter.", "Do not judge recall by total hit count alone."],
        "related": ["prompt-engineering/query-rewrite-and-coreference", "prompt-engineering/retrieval-evidence-selection", "prompt-engineering/chunk-boundary-and-parent-context"],
        "section": applications,
    },
    {
        "slug": "retrieval-rerank-after-authorization-and-version-check",
        "title": "Retrieval prompts: rerank only authorized, current evidence",
        "summary": "Improve passage order while preserving access, document version, and exact identifiers.",
        "definition": "Reranking reorders a candidate set; it does not grant access, repair missing documents, or decide that an obsolete procedure is current. Feed a reranker only passages already authorized for the caller. Before answer generation, compare each candidate's site, equipment identifier, effective version, and supersession status with the request. An older passage may remain useful for explaining a historical change but should not be presented as the active procedure. The prompt should ask the model to name a version conflict or insufficient evidence rather than blend steps from different manuals. A high relevance score is a ranking signal, not proof that a passage supports a final claim.",
        "case": "Meridian's first-pass search returns three authorized P-47 passages. Manual revision R-8 is active; R-6 is archived and includes a reset torque that changed. A reranker favors R-6 because its wording mirrors the question. The version gate excludes R-6 from the active procedure while retaining its ID for the private audit trace. R-8 lacks one requested postcheck, so the assistant asks for the current postcheck source rather than borrowing it from the retired manual. The restriction on contract page C-91 remains unchanged throughout; its tempting similarity never makes it a reranker input.",
        "sample": "Candidates: M-12/P47/R8 active; M-12/P47/R6 superseded.\nReranker scores relevance only among permitted candidates.\nVersion gate removes R6 from active instructions.\nMissing postcheck in R8: mark unknown; request current evidence.\nNever treat a score as authorization or factual support.",
        "cost": "Scoring K query-passage pairs adds O(K) reranker calls or one batched pass, with cost and latency proportional to candidate text. Version checks are O(K) metadata work. Limit K, but test that the answer-bearing authorized passage survives candidate generation before trimming. An extra model pass may improve ordering while raising expense; compare against a no-rerank baseline on held-out questions. When entitlement changes between retrieval and generation, recheck access before context assembly or discard the stale packet.",
        "mistakes": ["Do not rerank restricted passages and filter only after generation.", "Do not promote a superseded manual because its wording scores highly.", "Do not call reranker relevance a claim-support check."],
        "related": ["prompt-engineering/retrieval-freshness-and-conflict", "prompt-engineering/evidence-reference-checker", "prompt-engineering/paired-prompt-evaluation-uncertainty"],
        "section": applications,
    },
    {
        "slug": "retrieval-context-packet-coverage-and-claim-mapping",
        "title": "Retrieval prompts: pack evidence and map claims",
        "summary": "Preserve the right sections within a bounded context and check claim-level support.",
        "definition": "A retrieval context packet should carry the request, authorized passage text, document and section identifiers, version, and a declared coverage limit. A small top-k list can omit a safety precondition that sits beside the selected chunk, so the packer should fetch necessary parent context or adjacent sections before generation. Reserve room for the actual answer and review instructions; filling the entire context window with search hits can truncate the tail or bury the decisive passage. Require each procedural claim to map to a passage that actually supports it. A valid evidence ID proves membership in the packet, not that the passage establishes the asserted fact.",
        "case": "Meridian's active R-8 manual contains a reset step in section 4.2 and a lockout precondition in section 4.1. The top chunk starts at 4.2, which could produce a hazardous answer if packed alone. The context assembler adds 4.1 after confirming both sections are authorized and current. The answer names the precondition before the reset, then maps each claim to the right section ID. When the technician asks for an electrical isolation value absent from R-8, the assistant says the available packet does not establish it. It does not infer a value from a different pump or a retired revision.",
        "sample": "Packet: R8/4.1 lockout prerequisite; R8/4.2 reset sequence.\nClaim A: lockout required -> R8/4.1.\nClaim B: reset sequence -> R8/4.2.\nElectrical isolation value: absent -> do not invent.\nCoverage: site M-12, pump P-47, active R-8 only.",
        "cost": "Packing P passages into a token budget is O(P) bookkeeping once token counts are known; expanding adjacent sections adds retrieval and token cost. A smaller packet lowers inference latency but raises omission risk. Test both answer correctness and precondition coverage, since an answer can cite a real passage yet omit the step that makes it safe. Claim mapping is O(C+P) with an indexed passage map for C claims. Keep references to packet IDs in a private trace so a reviewer can reproduce the exact evidence shown to the model.",
        "mistakes": ["Do not clip away a required precondition to meet a token limit.", "Do not accept a real evidence ID as proof of an unrelated claim.", "Do not fill a missing value from a different equipment model."],
        "related": ["prompt-engineering/chunk-boundary-and-parent-context", "prompt-engineering/evidence-id-traceability", "prompt-engineering/long-context-priority-and-truncation"],
        "section": applications,
    },
    {
        "slug": "retrieval-permission-change-deletion-and-release-evaluation",
        "title": "Retrieval release: test permission changes and deletion",
        "summary": "Evaluate denied access, revoked grants, stale indexes, and answer quality together.",
        "definition": "A secure retrieval release needs positive and negative tests. Verify that authorized users can find the right active passage and that unauthorized users cannot receive its text, title, summary, or citation. Test a grant change after a cached query, a document deletion, a superseded revision, and a retriever timeout. Deletion must cover the source, index, caches, and saved context packets according to the system's retention contract; removing one search hit is not enough. Evaluate retrieval recall, final claim support, latency, and denied-content leakage separately. A good answer score cannot compensate for a permission failure, and a secure refusal does not prove the authorized path works.",
        "case": "Meridian removes a contractor's access to site M-12 while a previous retrieval packet is cached. The release test repeats the same P-47 question under the contractor's verified identity and requires no M-12 text or document title in the response. A technician with continuing access must still retrieve active R-8 sections 4.1 and 4.2. The team then deletes a retired R-6 file and checks the index, result cache, and context-packet store for its ID. A timed-out entitlement lookup must fail closed. Only after these cases pass does the release owner approve the prompt-and-retriever bundle.",
        "sample": "Allowed case: technician sees active R8/4.1 and R8/4.2.\nDenied case: contractor sees no M-12 passage, title, or citation.\nRevocation case: cached packet cannot bypass new permission state.\nDeletion case: R6 absent from source, index, and defined caches.\nTimeout case: fail closed; record a private operational alert.",
        "cost": "A release suite with U user roles and Q queries can require O(UQ) retrieval checks; target high-risk role and document pairs rather than only average relevance. Deletion checks add storage-specific scans and may need an asynchronous completion window. Record the permission version and index version used by each test so a pass is tied to an actual state. A zero-leak assertion belongs beside quality metrics as a hard gate, because averaging it into a helpfulness score could hide one severe disclosure.",
        "mistakes": ["Do not treat cache invalidation as optional after access revocation.", "Do not measure only authorized-answer quality.", "Do not claim deletion is complete while old packets remain available."],
        "related": ["prompt-engineering/prompt-evaluation-ci-gate", "prompt-engineering/sensitive-output-redaction-gate", "prompt-engineering/release-regression-gate"],
        "section": production,
    },
]

paths = ["prompt-engineering/" + spec["slug"] for spec in specs]
assert not set(paths + [project_path, quiz_path]).intersection(lookup)
titles = {entry["path"]: entry["title"] for entry in entries}
titles.update({path: spec["title"] for path, spec in zip(paths, specs)})
titles[project_path] = "Project: secure the Meridian maintenance assistant"
titles[quiz_path] = "Authorized-retrieval prompt decisions"


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
                 difficulty="Advanced", tags=["prompt engineering", "authorized retrieval"],
                 sort_order=30400 + order, status="published", published_at=stamp,
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

project_connections = paths + ["prompt-engineering/retrieval-evidence-selection", "prompt-engineering/retrieval-freshness-and-conflict", "prompt-engineering/privacy-and-data-minimization", quiz_path]
project_body = (
    "<p>Build a prompt and retrieval review packet for a fictional Meridian Maintenance assistant. A field technician asks about the P-47 seal reset at site M-12. The trusted application session identifies the technician; the model never decides access from a user-supplied role string. A contract page C-91 mentions P-47 but is restricted. A current maintenance manual, R-8, contains the lockout precondition in section 4.1 and reset steps in section 4.2. Retired R-6 has a tempting but obsolete value. The project is a local design exercise; it does not connect to a knowledge base.</p>"
    "<h2>Assemble the permitted packet</h2><p>Filter by verified identity before search and apply the filter to exact-token and semantic branches. Reject a near-match for pump P-74. Deduplicate candidates by passage ID, discard the retired R-6 from active procedure text, and include both R-8 sections so the precondition is not lost at a chunk boundary. The prompt maps each answer claim to the section that supports it. If the user asks for an electrical isolation value absent from R-8, return a bounded missing-evidence statement. Neither a high reranker score nor an existing citation creates the missing fact.</p>"
    "<h2>Prove the negative path</h2><p>Revoke a contractor's site access and repeat the same question after a cached query. No M-12 text, title, or citation may reach the contractor. The technician still retrieves the active manual. Test an entitlement timeout as a fail-closed path and remove retired R-6 from the source, index, and defined caches. Keep protected trace IDs for debugging, without logging restricted text into general application logs. A release owner approves only after these security gates and the answer-quality checks pass.</p>"
    '<pre><code class="language-text">Identity: server-verified technician T-47; site M-12 grant.\nForbidden: contract C-91; never enters model context.\nActive packet: R8/4.1 lockout + R8/4.2 reset; P-74 rejected.\nUnknown: isolation value absent from active evidence.\nRevoked contractor: no text, title, citation, or cached packet.\nEntitlement timeout: fail closed.</code></pre>'
    "<h2>Performance and operating cost</h2><p>With K exact and S semantic candidates, deduplication takes O(K+S) time and memory. Reranking adds work per selected passage; authorization and version checks add request latency but stop forbidden or obsolete text before generation. The release suite scales with its tested roles and questions, and it must include a hard zero-leak gate. A compact packet saves model tokens while increasing omission risk, so verify precondition coverage and claim support on held-out questions before choosing its final size.</p>"
    "<h3>Common Mistakes</h3><ul><li>Do not ask the model to hide a restricted passage after retrieval.</li><li>Do not answer from retired R-6 because its wording ranks first.</li><li>Do not omit R-8's lockout precondition to save context tokens.</li><li>Do not let a cached packet survive a revoked grant.</li></ul>"
    "<h2>Connected lessons</h2>" + links(project_connections))
new_rows.append(article(project_path, titles[project_path], "Filter restricted manuals, preserve current preconditions, and test revoked access.", project_body, projects, 60, project_connections, kind="project"))

questions = [
    ("Where must document access be enforced?", "In a trusted service before model context assembly", "Only in the final prompt", "Only after answer generation", "The model should never receive forbidden passages."),
    ("What proves a caller's site M-12 access?", "The authenticated application session and entitlement check", "A role string typed in the question", "A relevant search score", "User text and similarity are not access grants."),
    ("May the denied C-91 title appear in a fallback answer?", "No", "Yes, if the body is hidden", "Only when the model is uncertain", "Metadata can disclose restricted material."),
    ("Why combine exact and semantic candidate retrieval?", "To preserve P-47 while finding paraphrased procedure wording", "To remove authorization checks", "To guarantee a correct answer", "The branches cover different recall failures."),
    ("What should happen to a P-74 hit for a P-47 question?", "Reject the identifier mismatch", "Use it because it mentions a pump", "Rename it in the prompt", "Exact entity checks bound the answer."),
    ("Can reranking grant access to C-91?", "No, reranking only reorders permitted candidates", "Yes, if its score is highest", "Yes, if the user asks twice", "Access is checked before reranking."),
    ("How should active R-8 and retired R-6 be used?", "Use R-8 for current procedure; keep R-6 out of active steps", "Blend both versions", "Prefer R-6 because it scores higher", "Version status is separate from relevance."),
    ("Why include R-8 section 4.1?", "It holds the lockout precondition", "It increases token count", "It grants contract access", "A chunk boundary can hide a needed prerequisite."),
    ("What does a valid evidence ID alone prove?", "That the passage is in the packet, not that it supports the claim", "That every claim is true", "That the user is authorized", "Claim support requires checking passage meaning."),
    ("What if the active packet lacks the isolation value?", "State that current evidence does not establish it", "Borrow it from P-74", "Guess from R-6", "Do not fabricate a safety value."),
    ("What follows access revocation?", "Invalidate or recheck cached packets before reuse", "Keep serving the old packet", "Let the model decide", "A stale packet must not bypass current entitlement."),
    ("How should an entitlement timeout behave?", "Fail closed and record a private operational signal", "Search globally", "Return a denied document title", "Missing permission data is not an authorization grant."),
]
quiz_entry = copy.deepcopy(lookup["quizzes/prompt-engineering-multimodal-evidence"])
quiz_entry.update(id=str(uuid.uuid5(uuid.NAMESPACE_URL, "aitrove:" + quiz_path)),
                  path=quiz_path, title=titles[quiz_path],
                  summary="Test access filtering, exact identifiers, version gates, claim support, and revocation.",
                  body="<p>Choose the retrieval decision supported by the verified identity and current document evidence.</p><h2>Lessons</h2>" + links(paths) + "<h2>Project and sections</h2>" + links([project_path, applications, production, quizzes]),
                  sort_order=30470, status="published", published_at=stamp,
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
    (applications, paths[:4], "Authorized retrieval prompts", "Enforce access before context, preserve exact identifiers, and map claims to current passages."),
    (production, paths[4:], "Retrieval release gates", "Test revocation, deletion, timeouts, quality, and denied-content leakage."),
    (projects, [project_path], "Meridian maintenance assistant", "Apply a permission filter and preserve active procedural preconditions."),
    (quizzes, [quiz_path], "Authorized retrieval decisions", "Test access, ranking, version, and claim-support boundaries."),
]:
    hub = lookup[hub_path]
    hub["data"]["modules"].append({"title": title, "summary": summary, "lessons": selected})
    hub["body"] += "<h2>" + html.escape(title) + "</h2><p>" + html.escape(summary) + "</p>" + links(selected + [project_path, quiz_path])
    hub["updated_at"] = stamp

root_hub = lookup[subject_root]
root_hub["body"] += "<h2>Authorized retrieval</h2><p>Keep access checks, evidence relevance, current versions, and final claims separate.</p>" + links(paths + [project_path, quiz_path])
root_hub["updated_at"] = stamp

backlinks = {
    "prompt-engineering/retrieval-evidence-selection": paths[0],
    "prompt-engineering/query-rewrite-and-coreference": paths[1],
    "prompt-engineering/chunk-boundary-and-parent-context": paths[3],
    "prompt-engineering/retrieval-freshness-and-conflict": paths[2],
    "prompt-engineering/evidence-reference-checker": paths[3],
    "prompt-engineering/privacy-and-data-minimization": paths[0],
    "prompt-engineering/long-context-priority-and-truncation": paths[3],
    "prompt-engineering/prompt-evaluation-ci-gate": paths[4],
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
