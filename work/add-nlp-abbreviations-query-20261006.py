"""Add abbreviation governance and query-reformulation modules to NLP."""
from de_batch_publisher import publish

N = 'natural-language-processing/'
A = 'Abbreviation scope and glossary governance'
Q = 'Search queries and reformulation safety'

lessons = [
    {
        'path': N + 'abbreviation-definition-scope-and-collisions',
        'title': 'Abbreviations: definition scope, collisions and unknown forms',
        'module': A, 'project': False,
        'summary': 'A short form can be defined in one section, mean something else in another and remain unknown in a third. Resolve each occurrence against its own evidence.',
        'sections': [
            ('Extract a definition as a local claim', 'An incident note may introduce “Return Authorization (RA)” near a shipment paragraph. Another team may use RA for “Risk Assessment.” Record the short-form span, candidate long-form span, section, document revision and author. The parenthetical pattern is a candidate, not proof; some parentheses contain versions, comments or unrelated codes. Check that the letters align with the proposed expansion, then retain the source text for review. [[natural-language-processing/span-offset-annotation|Span identity]] allows a reviewer to revisit the exact phrase.'),
            ('Limit how far a definition travels', 'A definition in one incident should not silently govern another incident or an appended policy section. Set a documented scope: paragraph, section, document or approved glossary. Prefer a nearby explicit definition over a global default when both are valid, but flag incompatible definitions in the same scope. A heading boundary may terminate local authority. [[natural-language-processing/document-sections-and-passage-boundaries|Section boundaries]] prevent a definition from leaking into the next document fragment. Save the scope rule version with the decision.'),
            ('Treat collisions and missing expansions honestly', 'The letters RA are insufficient to choose between shipping and risk workflows. Use domain, surrounding nouns and explicit local definitions as evidence. When no expansion is supported, return unresolved with candidate IDs; do not substitute the most frequent organizational meaning. An unknown form may be a new product name or a typo. The [[natural-language-processing/domain-word-sense-inventory-and-nil|sense inventory]] has a related NIL state, but abbreviation expansion also has the distinct problem of locating and validating a long-form phrase.'),
            ('Evaluate the actual reading task', 'Audit extraction accuracy, scope errors, collision decisions and unresolved rate. Test headings, repeated definitions, quoted old policies and notes containing two teams. A global accuracy number can hide a rare acronym whose wrong expansion sends an operator to the wrong procedure. Measure whether a reader or search system receives the correct expansion and whether the original short form remains visible. Never erase the source phrase merely because an expansion was proposed.'),
        ],
        'code': '''def initialism_matches(short_form, long_form):
    words = [word for word in long_form.replace("-", " ").split() if word]
    initials = "".join(word[0].upper() for word in words)
    return initials == short_form.upper()

def stage_definition(short_form, long_form, section_id, revision):
    if not section_id or not revision:
        raise ValueError("definition needs section and revision")
    if not initialism_matches(short_form, long_form):
        return {"state": "review", "reason": "letter-mismatch"}
    return {"state": "candidate", "short_form": short_form,
            "long_form": long_form, "section_id": section_id,
            "source_revision": revision}

assert stage_definition("RA", "Return Authorization", "shipment-47", "r3")["state"] == "candidate"
assert stage_definition("RA", "Risk Control", "policy-82", "r4")["state"] == "review"
''',
        'cost': 'The illustrative letter check is O(c) time and space for c characters in the candidate expansion. Searching every possible surrounding phrase would be more expensive; bound the candidate window and section. The strict initial-letter rule intentionally abstains on irregular acronyms. Measure its missed definitions rather than relaxing it until false matches silently enter the glossary.',
        'mistakes': ['Applying a definition from one document to the entire corpus.', 'Accepting every parenthesized phrase as an expansion.', 'Forcing a frequent meaning when local evidence is absent.', 'Removing the original abbreviation after attaching a proposed long form.'],
        'related': [N + 'abbreviation-registry-version-and-reindex', N + 'incident-abbreviation-glossary-project', N + 'span-offset-annotation', N + 'document-sections-and-passage-boundaries', N + 'domain-word-sense-inventory-and-nil'],
    },
    {
        'path': N + 'abbreviation-registry-version-and-reindex',
        'title': 'Abbreviation registry: ownership, versions and index migration',
        'module': A, 'project': False,
        'summary': 'A glossary is a versioned decision service. A new expansion can change search results, annotations and generated summaries.',
        'sections': [
            ('Separate local evidence from approved defaults', 'An approved registry entry can supply a fallback when a document never defines its own short form. Each entry needs an owner, expansion, domain, validity period, alias status and approval record. Local definitions are still evidence, not an automatic override across domains. Store the selected entry ID, registry version and source document revision on each expansion. [[natural-language-processing/abbreviation-definition-scope-and-collisions|Definition scope]] determines whether a local phrase outranks a registry candidate.'),
            ('Plan collisions as schema changes', 'If the operations team introduces RA for Risk Assessment while shipping already uses Return Authorization, do not overwrite the older entry. Add a second domain-scoped sense and mark unqualified uses ambiguous. A renamed team, retired term or merged product can alter prior annotations. Publish a mapping from old IDs to new IDs; leave rows unresolved if the original text cannot distinguish them. Review saved searches and summary templates before activating the mapping.'),
            ('Rebuild only what the decision affects', 'A registry update may require expanding affected search index entries, cached suggestions and quality dashboards. Record which documents used the old entry and which relied on local definitions. Reprocess the former first, then compare search results for a frozen query set. A full corpus rebuild is avoidable when dependency records are sound. [[natural-language-processing/passage-revision-and-index-audit|Index revision auditing]] supplies a way to verify that visible passages match the new glossary and document revision.'),
            ('Release with a rollback path', 'Have the owner approve the new meaning, sample affected documents and freeze an evaluation set containing both domains. Track wrong expansion rate, unresolved cases, index coverage and queries whose top result changes. A sudden drop in unresolved rate may mean the system began forcing a default. Keep the previous registry and index generation until the new version passes review. [[natural-language-processing/incident-abbreviation-glossary-project|The glossary project]] tests this end-to-end.'),
        ],
        'code': '''REGISTRY = {
    "RA": [
        {"entry_id": "shipping-ra-r2", "domain": "shipping",
         "expansion": "Return Authorization"},
        {"entry_id": "risk-ra-r1", "domain": "risk",
         "expansion": "Risk Assessment"},
    ]
}

def registry_candidates(short_form, domain):
    entries = REGISTRY.get(short_form.upper(), [])
    return [entry for entry in entries if entry["domain"] == domain]

assert registry_candidates("ra", "shipping")[0]["entry_id"] == "shipping-ra-r2"
assert registry_candidates("ra", "unknown") == []
''',
        'cost': 'Scanning k registry entries for one short form is O(k) time and O(k) output space. A keyed index can make domain lookup effectively constant for a small, curated registry. Reindexing d affected documents costs at least O(d) before token processing; keep dependency records so a single glossary edit does not trigger a needless full rebuild.',
        'mistakes': ['Replacing a colliding entry instead of adding a scoped one.', 'Forgetting which index rows were built from the previous registry.', 'Using registry approval as proof that every occurrence has that meaning.', 'Retiring the old version before the new search results are audited.'],
        'related': [N + 'abbreviation-definition-scope-and-collisions', N + 'incident-abbreviation-glossary-project', N + 'passage-revision-and-index-audit', N + 'entity-link-version-and-merge-review', N + 'hybrid-ranking-and-access-filters'],
    },
    {
        'path': N + 'incident-abbreviation-glossary-project',
        'title': 'Project: ship an incident glossary with scoped expansions',
        'module': A, 'project': True,
        'summary': 'Extract abbreviations from incident notes, review collisions and expose expansions without changing what the original note said.',
        'sections': [
            ('Set the reader-facing contract', 'The incident viewer may display a proposed long form beside a short form, with its source and confidence state. It must preserve the original characters and document revision. A reader can inspect the local definition, registry entry or unresolved candidates. The viewer never silently rewrites an incident note. Start with RA in shipping and risk documents, then add an unqualified RA occurrence that must remain unresolved. [[natural-language-processing/abbreviation-definition-scope-and-collisions|The scope rules]] decide what evidence is admissible.'),
            ('Build the review set', 'Collect notes with local parenthetical definitions, definitions several paragraphs away, conflicting sections, copied quotations and unknown forms. Group every revision of one incident in the same evaluation split. Annotate the short form, long form if present, section and correct reader action. Include notes where the acronym letters do not align with any nearby phrase. A clean, independent holdout prevents a repeated template from making extraction look more reliable than it is.'),
            ('Stage extraction and migration', 'Extract candidates, apply section scope, and fall back to the approved registry only when domain evidence is present. Keep unresolved cases visible for review. When a new registry version arrives, mark dependent expansions and index rows stale. Reprocess only affected documents, compare their previous and new display decisions, and have an owner approve changed meanings. [[natural-language-processing/abbreviation-registry-version-and-reindex|Registry versioning]] keeps the old interpretation recoverable.'),
            ('Measure the release', 'Report correct display rate, wrong expansion rate, unresolved rate, reviewer minutes and search-result changes by domain. Inspect every high-impact collision rather than averaging it into easy single-meaning forms. Shadow the new glossary on recent incidents, then release with the prior registry and index ready for rollback. Access control on the incident note must also protect its expansion and any cached search snippet.'),
        ],
        'code': '''def display_expansion(local_candidates, registry_candidates):
    local = {item["expansion"] for item in local_candidates}
    if len(local) == 1:
        return {"state": "local", "expansion": next(iter(local))}
    if len(local) > 1:
        return {"state": "review", "reason": "local-collision"}
    approved = {item["expansion"] for item in registry_candidates}
    if len(approved) == 1:
        return {"state": "registry", "expansion": next(iter(approved))}
    return {"state": "unresolved"}

assert display_expansion([{"expansion": "Return Authorization"}], []) == {
    "state": "local", "expansion": "Return Authorization"}
assert display_expansion([], [{"expansion": "Return Authorization"},
                              {"expansion": "Risk Assessment"}])["state"] == "unresolved"
''',
        'cost': 'Building the distinct expansion sets takes O(l + r) time and space for l local and r registry candidates. The function does not decide whether candidates were extracted correctly; reviewer quality and source scope remain upstream gates. A wrong expansion in a published incident can cost more than an unresolved label, so measure that error explicitly.',
        'mistakes': ['Displaying a registry default despite conflicting local definitions.', 'Removing an unknown short form from the reader view.', 'Mixing revisions of one incident across train and test.', 'Exposing an expansion from a restricted note in a public search snippet.'],
        'related': [N + 'abbreviation-definition-scope-and-collisions', N + 'abbreviation-registry-version-and-reindex', N + 'incident-handoff-summary-project', N + 'passage-revision-and-index-audit', N + 'privacy-safe-ticket-pipeline-project'],
    },
    {
        'path': N + 'query-rewrite-provenance-and-protected-tokens',
        'title': 'Query rewrites: provenance, protected tokens and user intent',
        'module': Q, 'project': False,
        'summary': 'A search rewrite may improve recall while changing the question. Keep the original query and protect terms that carry operational meaning.',
        'sections': [
            ('Distinguish correction from expansion', 'Correcting a typo in “authorizaton” differs from adding “payment” to “hold.” The first may recover an intended token; the second chooses a domain. Record the original query, proposed rewrite, rule or model version, affected spans and reason. Never replace a quoted phrase, incident ID, error code or negated term without explicit policy. [[natural-language-processing/domain-word-sense-inventory-and-nil|Domain sense decisions]] can support an expansion, but an uncertain sense should not become an invisible hard filter.'),
            ('Use a bounded candidate set', 'Generate a few alternatives from approved terminology, spelling rules or reviewed query patterns. Keep the unchanged query in retrieval, and treat additions as optional recall paths until judged cases show they help. An expansion from a broad synonym list can pull in an unrelated domain and displace the exact match. Scope candidates by language and product, and record why each term was added. [[natural-language-processing/hybrid-ranking-and-access-filters|Hybrid ranking]] can combine original and expanded matches while still enforcing document access.'),
            ('Preserve operators and exclusions', 'The query “refund not pending” should not become a search for pending refunds. Preserve negation and quoted spans in a structured representation. A minus operator, field filter or date constraint may be syntax rather than prose. Parse the application’s supported query grammar before rewriting its free-text portion. Unknown syntax should pass through unchanged or request user clarification, not be guessed. A rewrite is a proposal about the user’s intent, not a fact about the corpus.'),
            ('Measure the whole result page', 'Compare original-only and rewritten results on incident-scoped judged queries. Report correct-runbook recall, wrong-domain top results, latency and the percentage of queries changed. Slice by short queries, identifiers, quoted text and negatives. Show reviewers both query forms and the matched evidence. A rewrite that increases recall but hides the only exact answer is a regression. [[natural-language-processing/query-feedback-bias-and-drift-audit|Feedback audits]] help identify misleading post-release signals.'),
        ],
        'code': '''APPROVED_ALIASES = {"authorization": ("card authorization",),
                    "rollback": ("revert deployment",)}

def rewrite_query(query, protected_tokens):
    terms = query.split()
    optional = []
    for term in terms:
        if term in protected_tokens or term.startswith("-") or term.isdigit():
            continue
        optional.extend(APPROVED_ALIASES.get(term.lower(), ()))
    return {"original": query, "optional_phrases": tuple(optional)}

proposal = rewrite_query("authorization -pending INC47", {"INC47"})
assert proposal["original"] == "authorization -pending INC47"
assert proposal["optional_phrases"] == ("card authorization",)
''',
        'cost': 'Scanning t space-separated terms is O(t) time, excluding the size of emitted expansions. A real search grammar needs a proper parser for quotes, escapes and filters; this code deliberately emits optional phrases without altering the original. Every added branch can increase retrieval and ranking work, so cap candidate count and measure tail latency with relevance.',
        'mistakes': ['Overwriting the original query with an unreviewed guess.', 'Expanding inside an incident ID or quoted phrase.', 'Dropping negation while normalizing text.', 'Judging success from recall alone when wrong-domain top results rise.'],
        'related': [N + 'query-feedback-bias-and-drift-audit', N + 'runbook-query-reformulation-project', N + 'hybrid-ranking-and-access-filters', N + 'domain-word-sense-inventory-and-nil', N + 'incident-runbook-search-project'],
    },
    {
        'path': N + 'query-feedback-bias-and-drift-audit',
        'title': 'Search feedback: position bias, query drift and audit design',
        'module': Q, 'project': False,
        'summary': 'Clicks reflect exposure as well as relevance. Evaluate reformulations against independent judgments before turning interaction traces into policy.',
        'sections': [
            ('Separate observation from judgment', 'A user may click the first result because it is visible, not because it answers the question. A zero-click session may mean the snippet answered it or the results failed. Log query form, displayed positions, eligible document set and action timing; do not equate a click with a relevant label. Protect user and document identifiers under retention policy. [[natural-language-processing/query-rewrite-provenance-and-protected-tokens|Rewrite provenance]] identifies which query version produced the result page.'),
            ('Watch for feedback loops', 'If an expanded query promotes one runbook, that runbook receives more exposure and therefore more clicks. Training the next expansion on those clicks can reinforce its own initial error. Keep a frozen set of independently judged queries and compare it across releases. Randomized exploration can estimate exposure effects where permitted, but it still needs privacy and safety review. An operator’s explicit relevance mark is stronger evidence than a bare click, though it can still reflect task context.'),
            ('Detect movement away from intent', 'A query for “card hold release” may expand toward generic refund content because the corpus contains many refund articles. Track whether newly introduced terms dominate top results and whether exact-match evidence disappears. Compare original-only, expanded-only and combined rankings. Flag a rewrite when it moves the correct runbook below the first screen or brings in a wrong-domain answer. [[natural-language-processing/abbreviation-definition-scope-and-collisions|Abbreviation collisions]] can make this drift worse for short queries.'),
            ('Build a release audit', 'Group related incident queries, copied templates and follow-up reformulations together before splitting. Ask reviewers to judge result relevance without seeing which algorithm produced it. Measure top-result errors, correct-result recall, query-change rate and latency by language and product. After release, sample changed queries rather than only popular ones. Roll back the rewrite rule when the audited error rises, even if overall click-through increases.'),
        ],
        'code': '''def audit_changed_results(original_rank, rewritten_rank, relevant_ids):
    if not original_rank or not rewritten_rank:
        return {"review": True, "reason": "empty-result-list"}
    original_hit = original_rank[0] in relevant_ids
    rewritten_hit = rewritten_rank[0] in relevant_ids
    return {"review": original_hit and not rewritten_hit,
            "original_top_relevant": original_hit,
            "rewritten_top_relevant": rewritten_hit}

audit = audit_changed_results(["runbook-47", "note-82"],
                              ["note-82", "runbook-47"], {"runbook-47"})
assert audit["review"] and not audit["rewritten_top_relevant"]
''',
        'cost': 'The top-result check is O(1) with a set of judged relevant IDs, but collecting unbiased judgments is the expensive part. Auditing all k ranked results costs O(k) per query and exposes more regressions. Keep the judged set independent of click-derived training signals; otherwise a feedback loop can make a weak policy appear to improve itself.',
        'mistakes': ['Using raw clicks as ground-truth relevance labels.', 'Comparing rankings without preserving exposure positions.', 'Allowing rewritten terms to displace the only exact answer.', 'Splitting follow-up queries from one incident across train and test.'],
        'related': [N + 'query-rewrite-provenance-and-protected-tokens', N + 'runbook-query-reformulation-project', N + 'grouped-temporal-text-validation', N + 'hybrid-ranking-and-access-filters', N + 'text-feedback-loop-and-shadow-audit'],
    },
    {
        'path': N + 'runbook-query-reformulation-project',
        'title': 'Project: release controlled runbook query reformulation',
        'module': Q, 'project': True,
        'summary': 'Propose bounded search alternatives, preserve the operator’s exact query and reject rewrites that bury the correct runbook.',
        'sections': [
            ('Define the search contract', 'An on-call engineer enters “authorization timeout INC47.” The search service may suggest a reviewed phrase such as “card authorization,” but must preserve INC47, the original terms and any explicit filters. Access rules apply to every result, regardless of rewrite. Store the original query and all optional expansions with a policy version so a result can be explained later. [[natural-language-processing/query-rewrite-provenance-and-protected-tokens|The rewrite contract]] fixes protected tokens and the audit record.'),
            ('Create a hard evaluation set', 'Include terse error-code queries, misspellings, abbreviations with multiple meanings, quoted phrases, negated searches and incidents with several similarly named services. Group all reformulations from one incident in the same split. Reviewers judge which runbook answers each query, including cases with no eligible document. Freeze the judged set before choosing expansion rules, otherwise the team can tune to a remembered list of successes.'),
            ('Stage results safely', 'Retrieve using both the original and approved optional phrases, enforce access, then rank with explicit preference for exact evidence. If an expansion changes the top result, record the reason for audit. When all candidates are uncertain, show original-only results and a suggestion the engineer may choose. Do not use clicks from the same staged release as ground-truth training labels. [[natural-language-processing/query-feedback-bias-and-drift-audit|Feedback auditing]] detects position bias and query drift.'),
            ('Gate and roll back the release', 'Compare top-result correctness, correct-runbook recall, wrong-domain rate, access violations and tail latency against original-only search. Inspect every case where a previously correct top result is displaced. Shadow the proposed policy before enabling it, then sample changed queries after release by product and language. Retain the previous alias table and ranking version for rollback. A rise in clicks cannot overrule independently judged wrong answers.'),
        ],
        'code': '''def choose_visible_results(original_hits, expanded_hits, allowed_ids):
    seen = set()
    visible = []
    for document_id in original_hits + expanded_hits:
        if document_id in allowed_ids and document_id not in seen:
            seen.add(document_id)
            visible.append(document_id)
    return visible

result = choose_visible_results(["runbook-47", "restricted-91"],
                                ["runbook-47", "note-82"],
                                {"runbook-47", "note-82"})
assert result == ["runbook-47", "note-82"]
''',
        'cost': 'Merging n original and m expanded hits is O(n + m) expected time and space with hash sets. Retrieval and reranking add their own latency, so cap expansions and audit the slow tail, not only the median. The order in this illustration favors original hits; a production ranker still needs judged-query evaluation and the same access gate.',
        'mistakes': ['Letting expansion results bypass access filtering.', 'Replacing the original query instead of retaining it.', 'Training on clicks produced by the same ranking policy.', 'Calling the release successful while previously correct top answers disappear.'],
        'related': [N + 'query-rewrite-provenance-and-protected-tokens', N + 'query-feedback-bias-and-drift-audit', N + 'incident-runbook-search-project', N + 'runbook-section-retrieval-project', N + 'hybrid-ranking-and-access-filters'],
    },
]

crosslinks = [
    (N + 'span-offset-annotation', N + 'abbreviation-definition-scope-and-collisions'),
    (N + 'document-sections-and-passage-boundaries', N + 'abbreviation-definition-scope-and-collisions'),
    (N + 'passage-revision-and-index-audit', N + 'abbreviation-registry-version-and-reindex'),
    (N + 'incident-handoff-summary-project', N + 'incident-abbreviation-glossary-project'),
    (N + 'hybrid-ranking-and-access-filters', N + 'query-rewrite-provenance-and-protected-tokens'),
    (N + 'text-feedback-loop-and-shadow-audit', N + 'query-feedback-bias-and-drift-audit'),
    (N + 'incident-runbook-search-project', N + 'runbook-query-reformulation-project'),
]

if __name__ == '__main__':
    publish(lessons, (A, Q), crosslinks,
            'aitrove-nlp-abbreviations-query-import-20261006.json', 4824,
            subject='natural-language-processing', hub_path=N + 'nlp-tutorial')
