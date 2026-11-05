"""Add morphology and keyphrase extraction modules to the NLP path."""
from de_batch_publisher import publish

N = 'natural-language-processing/'
M = 'Morphology and search-term identity'
K = 'Keyphrase extraction and document indexing'

lessons = [
    {
        'path': N + 'lemma-pos-and-domain-term-contract',
        'title': 'Lemmas, part of speech and domain terms in a search index',
        'module': M, 'project': False,
        'summary': 'Word forms help recall, but careless reduction can erase a product name or make two different actions look identical.',
        'sections': [
            ('Define the index identity', 'Store original text and offsets before making any searchable representation. A lemma is a normalized word form conditioned on a grammatical reading; a stem is a mechanical reduction and may not be a word. Neither should replace the original. In “the charge backs out” and “a chargeback arrived,” a nearby sequence of letters does not establish the same event. Keep exact identifiers, product names and quoted error text in separate fields. [[natural-language-processing/unicode-tokenization-boundary|Unicode token boundaries]] are part of this contract.'),
            ('Use context for ambiguous forms', 'A token such as “returns” may be a noun in a policy title or a verb in a customer report. Part-of-speech assignment influences a lemma and can fail on terse headings. Store the tagger version, language and confidence beside the derived form. Where uncertainty is high, index both the surface form and a small reviewed expansion set. Never rewrite the source sentence in place. A one-size suffix rule is especially brittle for mixed-language or technical vocabulary.'),
            ('Protect terms with operational meaning', 'Maintain an allowlist for domain tokens such as SKU names, incident codes and command flags. A product name that resembles an ordinary plural is still an exact entity. Review each normalization change against exact-match queries and misspellings. Use [[natural-language-processing/script-profile-and-code-switching-boundary|script profiling]] before applying language-specific morphology; a message can switch language in the middle of a sentence. Version the term list and rebuild derived postings when it changes.'),
            ('Evaluate retrieval effects', 'Compare exact search, surface-plus-lemma search and a conservative domain dictionary on held-out queries. Report recall at a fixed review depth, rank changes, false matches and exact-code preservation. A gain on broad “refunds” queries cannot excuse a lost search for order ZX-47. [[natural-language-processing/hybrid-ranking-and-access-filters|Hybrid ranking]] combines these lexical signals with semantic candidates, while [[natural-language-processing/morphology-aware-support-search-project|the project]] tests a release in context.'),
        ],
        'code': '''def searchable_forms(surface, part_of_speech, lemma_table, protected):
    exact = surface.casefold()
    if exact in protected:
        return (exact,)
    lemma = lemma_table.get((exact, part_of_speech))
    return tuple(dict.fromkeys((exact, lemma))) if lemma else (exact,)

lexicon = {("returns", "VERB"): "return", ("returns", "NOUN"): "return"}
assert searchable_forms("Returns", "VERB", lexicon, set()) == ("returns", "return")
assert searchable_forms("ZX-47", "NOUN", lexicon, {"zx-47"}) == ("zx-47",)
''',
        'cost': 'A dictionary lookup is O(1) average time per token and emits at most two postings here. Contextual tagging adds inference time and model storage. Duplicated postings increase index size and candidate counts, so measure retrieval quality and query latency together. The protected-term set must be versioned with the index rather than updated silently in a live query path.',
        'mistakes': ['Replacing stored source text with its lemma sequence.', 'Applying an English suffix rule to every language.', 'Reducing an exact order code because it resembles an ordinary token.', 'Claiming better search from token accuracy without checking retrieval outcomes.'],
        'related': [N + 'morphology-ambiguity-and-versioned-reindex', N + 'morphology-aware-support-search-project', N + 'unicode-tokenization-boundary', N + 'script-profile-and-code-switching-boundary', N + 'hybrid-ranking-and-access-filters'],
    },
    {
        'path': N + 'morphology-ambiguity-and-versioned-reindex',
        'title': 'Morphology ambiguity, index versions and rollback',
        'module': M, 'project': False,
        'summary': 'A new lemma map changes which documents a query can reach. Ship it as an index version with an audit and rollback path.',
        'sections': [
            ('Record the transform chain', 'The searchable form depends on decoding, token boundaries, language choice, part-of-speech tagging, lemma rules and protected-term policy. Record a digest for that bundle with each derived index. If one component changes, build a new index namespace or rebuild all affected postings. Mixing query forms from a new analyzer with old document postings causes silent misses. [[natural-language-processing/text-embedding-pair-and-version-contract|Embedding version pairing]] follows the same principle for vector indices.'),
            ('Inspect ambiguous readings', 'Sample short support headings, commands, proper nouns and code-switched messages. The word “left” can describe direction or a completed departure; a tagger with no context may choose incorrectly. Permit an abstain state that indexes the surface form only. Review false expansions that pull unrelated cases into top results. If a query contains an exact error code, preserve its exact-match channel even when other words are expanded.'),
            ('Reindex without breaking search', 'Build the new postings from immutable source revisions and compare them with the current index. Check document counts, tenant scope, query parity on exact identifiers and ranking metrics on reviewed queries. Move a search alias only after the audit passes. Keep the old index until rollback is no longer required. A deleted source must be excluded from both versions; retaining it in a shadow index is a privacy failure.'),
            ('Measure the release', 'Report unmatched exact queries, recall at a chosen depth, false positives caused by expansion, p95 latency and index size. Separate new-language and technical-term slices. [[natural-language-processing/lemma-pos-and-domain-term-contract|The term contract]] defines what may be expanded. The [[natural-language-processing/morphology-aware-support-search-project|support search project]] turns these checks into an operational gate.'),
        ],
        'code': '''def eligible_for_index_swap(old_manifest, new_manifest, audit):
    if old_manifest["tenant_scope"] != new_manifest["tenant_scope"]:
        return False
    if new_manifest["source_revision"] != audit["source_revision"]:
        return False
    return (audit["exact_code_misses"] == 0
            and audit["deleted_source_hits"] == 0
            and audit["recall_at_8"] >= audit["minimum_recall_at_8"])

old = {"tenant_scope": "support-eu", "source_revision": "r46"}
new = {"tenant_scope": "support-eu", "source_revision": "r47"}
audit = {"source_revision": "r47", "exact_code_misses": 0,
         "deleted_source_hits": 0, "recall_at_8": 0.84,
         "minimum_recall_at_8": 0.81}
assert eligible_for_index_swap(old, new, audit)
''',
        'cost': 'The release gate is O(1), while a full reindex is O(t) tokenization work plus postings writes for t source tokens. Running two indices temporarily increases storage and refresh cost. Treat that cost as part of a reversible release, and measure the shadow index for deletion compliance before moving the alias.',
        'mistakes': ['Deploying a query analyzer before rebuilding document postings.', 'Keeping removed records in the rollback index.', 'Scoring only average queries while exact identifiers fail.', 'Using a language-specific lemma map after uncertain language detection.'],
        'related': [N + 'lemma-pos-and-domain-term-contract', N + 'morphology-aware-support-search-project', N + 'hybrid-ranking-and-access-filters', N + 'script-profile-and-code-switching-boundary', N + 'text-embedding-pair-and-version-contract'],
    },
    {
        'path': N + 'morphology-aware-support-search-project',
        'title': 'Project: release morphology-aware support search',
        'module': M, 'project': True,
        'summary': 'Build an index that finds inflected support terms while keeping product names and ticket codes exact.',
        'sections': [
            ('Set the search task', 'Agents search a restricted support corpus by issue description, incident ID and exact order code. Keep the original ticket and its access scope as the source of truth. Index surface forms alongside a controlled lemma expansion, not in place of them. Search for “returned item” should reach a relevant “returns” case, while ZX-47 must never match ZX-74. Record the version of the text transform used by each index shard.'),
            ('Create an adversarial audit', 'Gather approved queries from agent sessions and write relevance judgments for a fixed top-eight review depth. Include plural forms, past tense, ambiguous words, code-switched notes and product terms that resemble ordinary words. Add exact-code negatives and deleted tickets. Group near-duplicate incidents before splitting so an easy copied template does not inflate the outcome. [[natural-language-processing/lemma-pos-and-domain-term-contract|The term contract]] guides expansion.'),
            ('Build and compare', 'Construct an exact baseline, then a surface-plus-lemma index from the same corpus revision. Compare recall, false expansions, precise code lookup, latency and storage. A contextual tagger can be added only where its incremental gain clears the review cost. [[natural-language-processing/morphology-ambiguity-and-versioned-reindex|Versioned reindexing]] provides the release and rollback procedure. Recheck tenant filters after candidate generation and before a result is shown.'),
            ('Ship the guarded index', 'Keep both index versions during a staged rollout. Inspect misses and unexpected matches from real queries without logging unrestricted ticket text. Exclude deleted sources from both versions. If technical identifiers miss or cross-tenant results appear, return to the old alias immediately. Record source revision, analyzer digest and audit metrics for each promotion.'),
        ],
        'code': '''def search_hit_allowed(hit, tenant_id, removed_ids):
    return (hit["tenant_id"] == tenant_id
            and hit["document_id"] not in removed_ids)

hits = [
    {"document_id": "case-47", "tenant_id": "north"},
    {"document_id": "case-82", "tenant_id": "south"},
]
visible = [hit for hit in hits if search_hit_allowed(hit, "north", set())]
assert [hit["document_id"] for hit in visible] == ["case-47"]
''',
        'cost': 'The access filter is O(1) average per candidate with a set of deleted IDs; scanning k candidates is O(k). The morphology index costs extra postings, and contextual tagging adds per-document and query inference. Compare all of those with the cost of agents missing a relevant case. Access filtering must be enforced independently of model relevance.',
        'mistakes': ['Letting a lemma posting override an exact ticket-code match.', 'Evaluating with training incidents repeated in the query audit.', 'Serving results before tenant and deletion checks.', 'Promoting a new analyzer without a matching rebuilt index.'],
        'related': [N + 'lemma-pos-and-domain-term-contract', N + 'morphology-ambiguity-and-versioned-reindex', N + 'hybrid-ranking-and-access-filters', N + 'incident-runbook-search-project', N + 'privacy-safe-ticket-pipeline-project'],
    },
    {
        'path': N + 'keyphrase-candidate-spans-and-nested-terms',
        'title': 'Keyphrase candidates: spans, nesting and document context',
        'module': K, 'project': False,
        'summary': 'Useful keyphrases are document-grounded spans, not a bag of frequent words or an invented label.',
        'sections': [
            ('Specify what a phrase represents', 'A runbook phrase may name a symptom, subsystem or repair step. Decide whether a phrase must occur verbatim in the source, whether abbreviations may be expanded and whether a named identifier belongs in the phrase list. Store the original half-open span and text revision for extractive candidates. “Queue lag” and “queue lag threshold” overlap, but may answer different search needs. [[natural-language-processing/span-offset-annotation|Span annotations]] give reviewers an exact location.'),
            ('Generate bounded candidates', 'Start with noun-like spans, domain lexicon terms and short n-grams, then discard boilerplate headers and private identifiers. Preserve sentence and section context so “retry limit” in a warning is not treated as the same instruction as a recommended retry. Candidate rules are allowed to overgenerate; the ranker and review policy decide which phrases are useful. Keep a reason code for each candidate source, and test tokenization on hyphens, punctuation and mixed scripts.'),
            ('Resolve overlap deliberately', 'Normalize whitespace and case for duplicate detection without losing source offsets. If both a nested and full phrase remain, give each a purpose: the shorter term may support broad navigation, while the longer term disambiguates a specific failure. Do not concatenate nearby high-scoring words into a phrase that never appeared. Terms generated as taxonomy labels belong in a separate field, clearly marked as derived labels.'),
            ('Evaluate against retrieval', 'Phrase precision alone can reward obvious document titles while missing details users search for. Use a reviewed list of target questions, check whether phrases improve discovery and track false links between unrelated incidents. Report phrase coverage, redundancy and stability after document revisions. [[natural-language-processing/keyphrase-ranking-and-human-utility|Ranking and utility]] covers selection; the [[natural-language-processing/runbook-keyphrase-index-project|runbook project]] tests the full index.'),
        ],
        'code': '''def collect_phrase_spans(document, candidate_spans):
    seen = set()
    phrases = []
    for start, end in candidate_spans:
        if not 0 <= start < end <= len(document):
            raise ValueError("invalid source span")
        phrase = document[start:end]
        identity = " ".join(phrase.casefold().split())
        if identity and identity not in seen:
            seen.add(identity)
            phrases.append({"start": start, "end": end, "text": phrase})
    return phrases

runbook = "Inspect queue lag before changing the retry limit."
assert collect_phrase_spans(runbook, [(8, 17), (8, 17)])[0]["text"] == "queue lag"
''',
        'cost': 'Validating c spans and normalizing their total character length L takes O(c + L) expected time and O(c + L) space. Generating every n-gram up to a fixed width is linear in document tokens times that width; unconstrained spans grow quadratically. Bound candidate length, and measure downstream reviewer and index cost rather than ranking only phrase count.',
        'mistakes': ['Presenting a generated taxonomy label as a verbatim source phrase.', 'Removing nested phrases without checking their separate search value.', 'Changing normalization after recording offsets.', 'Ranking boilerplate section titles above specific repair terms.'],
        'related': [N + 'keyphrase-ranking-and-human-utility', N + 'runbook-keyphrase-index-project', N + 'span-offset-annotation', N + 'dependency-tree-contract-and-token-alignment', N + 'incident-runbook-search-project'],
    },
    {
        'path': N + 'keyphrase-ranking-and-human-utility',
        'title': 'Keyphrase ranking: usefulness, redundancy and drift',
        'module': K, 'project': False,
        'summary': 'A phrase list should help an agent find the right document. Score that outcome rather than rewarding frequent but empty terms.',
        'sections': [
            ('Separate salience from utility', 'A phrase can be prominent in a document and useless in a search result. “Customer issue” may occur often but distinguishes nothing; “callback timeout after 47 retries” may occur once and identify the case. Combine local evidence, corpus rarity, location and domain policy, then inspect results at a fixed phrase budget. Do not fit corpus statistics on held-out documents. [[natural-language-processing/keyphrase-candidate-spans-and-nested-terms|Candidate spans]] determine what the ranker may choose.'),
            ('Control redundancy and leakage', 'Deduplicate normalized repeats and compare nested phrases under a policy that values specificity without hiding a useful broad label. Keep document family and tenant boundaries in corpus statistics. A rare customer ID is not a valuable keyphrase; redact or exclude it before ranking. If a phrase list is displayed publicly, ensure every phrase is safe to show and grounded in an accessible source. [[natural-language-processing/pii-detection-and-redaction-boundary|Redaction]] is an upstream gate.'),
            ('Measure with human tasks', 'Ask reviewers whether a phrase helps identify, distinguish or retrieve a runbook for a realistic question. Also report retrieval at a fixed depth, duplicate phrase rate, private-term leakage and how often phrases survive a document edit. Multiple reviewers may disagree about a useful phrase; keep those judgments rather than flattening them into one hidden label. Compare against document title and TF-IDF baselines on a frozen query set.'),
            ('Handle revisions', 'Phrase spans and corpus frequencies can change when the source or index grows. Attach a source revision and extractor version. Recompute affected documents after edits, and withdraw phrases from deleted content. A new ranker should be evaluated on old and newly introduced sections before an alias moves. The [[natural-language-processing/runbook-keyphrase-index-project|project]] gives the index a reversible release gate.'),
        ],
        'code': '''def rank_keyphrases(candidates, corpus_document_frequency, corpus_size):
    ranked = []
    for candidate in candidates:
        phrase = candidate["text"].casefold()
        document_frequency = corpus_document_frequency.get(phrase, 0)
        rarity = (corpus_size + 1) / (document_frequency + 1)
        score = candidate["local_count"] * rarity
        ranked.append((score, phrase))
    return sorted(ranked, reverse=True)

phrases = [{"text": "queue lag", "local_count": 2},
           {"text": "incident", "local_count": 3}]
ranked = rank_keyphrases(phrases, {"queue lag": 4, "incident": 90}, 120)
assert ranked[0][1] == "queue lag"
''',
        'cost': 'Scoring c candidates is O(c) average dictionary work, followed by O(c log c) sorting and O(c) output space. This baseline is intentionally simple; its score is not a calibrated probability. Corpus-frequency refresh can be expensive across many revisions. Measure retrieval gain, reviewer usefulness and leakage separately before paying for a more complex ranker.',
        'mistakes': ['Treating a high extraction score as proof a phrase helps a user.', 'Learning document frequency from the held-out audit set.', 'Letting a rare customer identifier become the top phrase.', 'Leaving phrases from a deleted source in a public index.'],
        'related': [N + 'keyphrase-candidate-spans-and-nested-terms', N + 'runbook-keyphrase-index-project', N + 'sparse-text-baseline', N + 'pii-detection-and-redaction-boundary', N + 'hybrid-ranking-and-access-filters'],
    },
    {
        'path': N + 'runbook-keyphrase-index-project',
        'title': 'Project: build a reviewed runbook keyphrase index',
        'module': K, 'project': True,
        'summary': 'Extract source-grounded phrases from runbooks, rank them for agent search and remove them when the source changes.',
        'sections': [
            ('Set the product boundary', 'An incident runbook contains symptoms, commands and recovery steps. The index should expose phrases that help an authorized agent find the right section, not invent a diagnosis. Store phrase text, original span, source revision, access scope and extractor version. A phrase has no independent truth once its source is edited. Keep a link to the exact runbook section so an agent can inspect the surrounding instruction.'),
            ('Create the review set', 'Write realistic search questions from agent tasks. Have reviewers mark relevant runbook sections and useful phrase candidates independently. Include nested terms, repeated titles, rare commands, renamed products and private ticket identifiers. Group documents by incident family before splitting. [[natural-language-processing/keyphrase-candidate-spans-and-nested-terms|Candidate generation]] must keep original offsets; [[natural-language-processing/keyphrase-ranking-and-human-utility|ranking]] must measure usefulness rather than frequency alone.'),
            ('Build a minimal index', 'Extract bounded candidates and reject boilerplate and sensitive spans. Rank the remaining phrases, allow a small number per section and keep the source text for verification. Compare against title-only and sparse lexical baselines at a fixed review depth. Filter by tenant and access scope before displaying phrases or linked sections. Treat a missing source revision as an invalid index record.'),
            ('Release and maintain', 'Shadow-build a new index when extraction rules or corpus revisions change. Check source counts, stale spans, retrieval gain, leakage and deletion propagation. Move the index alias only after the fixed audit passes, and retain the old safe version briefly for rollback. Monitor phrase click-through alongside false matches; clicks alone can reward misleading but attractive terms.'),
        ],
        'code': '''def verified_phrase_record(document, span, source_revision):
    start, end = span
    if not source_revision or not 0 <= start < end <= len(document):
        raise ValueError("phrase source is not verifiable")
    phrase = document[start:end]
    return {"text": phrase, "start": start, "end": end,
            "source_revision": source_revision}

record = verified_phrase_record("Inspect queue lag.", (8, 17), "rev-47")
assert record["text"] == "queue lag"
''',
        'cost': 'Span verification is O(1) plus O(length of phrase) to copy the text. Extraction across d documents costs at least the total token count and index writes; shadow builds temporarily double storage. The harder cost is reviewer time for query relevance and sensitive-term checks. Keep a fixed phrase budget per section and report retrieval gain per added index entry.',
        'mistakes': ['Publishing a phrase without a source revision or offset.', 'Indexing private ticket IDs from a copied runbook example.', 'Evaluating extraction against the same documents used to tune ranking.', 'Failing to remove phrases when a runbook section is deleted.'],
        'related': [N + 'keyphrase-candidate-spans-and-nested-terms', N + 'keyphrase-ranking-and-human-utility', N + 'incident-runbook-search-project', N + 'span-offset-annotation', N + 'pii-detection-and-redaction-boundary'],
    },
]

crosslinks = [
    (N + 'unicode-tokenization-boundary', N + 'lemma-pos-and-domain-term-contract'),
    (N + 'script-profile-and-code-switching-boundary', N + 'morphology-ambiguity-and-versioned-reindex'),
    (N + 'hybrid-ranking-and-access-filters', N + 'morphology-aware-support-search-project'),
    (N + 'span-offset-annotation', N + 'keyphrase-candidate-spans-and-nested-terms'),
    (N + 'sparse-text-baseline', N + 'keyphrase-ranking-and-human-utility'),
    (N + 'incident-runbook-search-project', N + 'runbook-keyphrase-index-project'),
]

if __name__ == '__main__':
    publish(lessons, (M, K), crosslinks,
            'aitrove-nlp-morphology-keyphrases-import-20261006.json', 4776,
            subject='natural-language-processing', hub_path=N + 'nlp-tutorial')
