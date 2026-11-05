"""Add dependency parsing and translation release lessons."""
from de_batch_publisher import publish

N = 'natural-language-processing/'
Y = 'Syntax and dependency structure'
L = 'Translation quality and localization'
lessons = [
    {
        'path': N + 'dependency-tree-contract-and-token-alignment',
        'title': 'Dependency trees: token identity, heads and structural checks',
        'module': Y, 'project': False,
        'summary': 'A dependency parser predicts head links between tokens. Validate the graph and token offsets before using its labels for extraction or search.',
        'sections': [
            ('Define the unit of syntax', 'A dependency record names a token, its head token and a relation label. One token is the root; every other token has exactly one head in a basic tree. Token IDs belong to a specific sentence and tokenizer version, not a document-wide namespace. Store original character offsets beside them. If sentence segmentation changes, the same integer ID may refer to another word. [[natural-language-processing/unicode-tokenization-boundary|Unicode tokenization]] and [[natural-language-processing/span-offset-annotation|span offsets]] are prerequisites for reproducible parses.'),
            ('Check the graph, not just a label list', 'Reject out-of-range heads, self-links, multiple roots and cycles. Check that every token reaches the root. A parser may still produce a well-formed but linguistically wrong tree, so structural validation is only an intake gate. Keep punctuation and multiword expressions under the chosen annotation convention. An apostrophe, hyphenated product name or code-switched phrase can change token boundaries and every downstream arc.'),
            ('Evaluate useful relations', 'Unlabeled attachment measures the selected head; labeled attachment also requires the relation. Calculate them on an agreed tokenization, excluding or including punctuation according to a documented policy. Break out long sentences, nonstandard spelling, mixed scripts and passive constructions. An aggregate attachment score does not prove that the subject-object relation needed by an extractor is correct. Evaluate the end task too, such as identifying the affected service in an incident note.'),
            ('Control version changes', 'Bundle sentence segmenter, tokenizer, parser weights, relation map and normalization policy. Compare token boundary differences before comparing arcs across versions; otherwise an apparent parsing regression may be a changed segmenter. Keep a reviewed audit set with messages from the target domain. [[natural-language-processing/dependency-paths-for-relation-candidates|Dependency paths]] uses validated trees to generate relation candidates, and the [[natural-language-processing/incident-syntax-extraction-project|project]] exercises the full contract.'),
        ],
        'code': '''def validate_dependency_tree(heads):
    token_count = len(heads)
    roots = [index for index, head in enumerate(heads) if head == -1]
    if len(roots) != 1:
        raise ValueError("basic tree requires one root")
    for token_index, head_index in enumerate(heads):
        if head_index == -1:
            continue
        if not 0 <= head_index < token_count or head_index == token_index:
            raise ValueError("invalid head index")
        visited = {token_index}
        cursor = head_index
        while cursor != -1:
            if cursor in visited:
                raise ValueError("dependency cycle")
            visited.add(cursor)
            cursor = heads[cursor]
    return roots[0]

assert validate_dependency_tree([1, -1, 1, 2]) == 1
''',
        'cost': 'This simple validator follows parent pointers from every token and can take O(t²) time with O(t) temporary space for t tokens. A memoized graph walk reduces validation to O(t), useful for long documents; sentence-length inputs rarely make the simple version expensive. Parser inference, annotation and tokenization changes dominate operating cost. Record structural rejection rate separately from linguistic accuracy.',
        'mistakes': ['Treating integer token IDs as stable across tokenizer versions.', 'Using a tree with a cycle because every token has a head.', 'Comparing attachment scores after changing punctuation or segmentation rules.', 'Assuming a well-formed graph proves the dependency labels are correct.'],
        'related': [N + 'dependency-paths-for-relation-candidates', N + 'incident-syntax-extraction-project', N + 'unicode-tokenization-boundary', N + 'relation-extraction-provenance', N + 'span-offset-annotation'],
    },
    {
        'path': N + 'dependency-paths-for-relation-candidates',
        'title': 'Use dependency paths to propose, not assert, entity relations',
        'module': Y, 'project': False,
        'summary': 'A short syntactic path can focus relation extraction, but negation, quotation and cross-sentence references still require evidence review.',
        'sections': [
            ('Generate bounded candidates', 'For two reviewed entity spans in a sentence, identify their syntactic heads and the path connecting them through the dependency tree. Path length and relation sequence can help a classifier decide which pairs deserve scoring. Limit by sentence, entity type and a measured path budget; aggressive pruning can lose long-distance dependencies. The parse must pass [[natural-language-processing/dependency-tree-contract-and-token-alignment|tree validation]] first, and the entity spans must still round-trip to source text.'),
            ('Keep syntax as a feature', '“Service K did not restart Queue M” contains a path between two entities, but the negator changes the assertion. “The note says Service K restarts Queue M” reports a claim rather than an observed event. Passive voice can reverse apparent word order. Store the source clause, negation cue and speaker or quotation status with each candidate. A dependency path is a candidate generator, not a proof of relation. [[natural-language-processing/relation-extraction-provenance|Relation provenance]] remains the release boundary.'),
            ('Audit pruning loss', 'Measure candidate-pair recall before classifying relation labels. Include long sentences, parenthetical clauses, code-switched verbs and cross-sentence pronouns. If a required relation is often cross-sentence, add a separate discourse route rather than silently widening every path window. Keep candidate IDs tied to parser version and source revision. A new parser may change path length without any change in the underlying fact.'),
            ('Select the simplest useful feature', 'Compare an entity-type plus local-word baseline, a dependency-path model and a contextual model against one incident-level split. A syntactic feature earns its cost only if it recovers reviewed relations or cuts false positives. Report end-to-end edge precision and recall, not path-classifier accuracy on gold pairs alone. The [[natural-language-processing/incident-syntax-extraction-project|incident project]] turns this comparison into a release decision.'),
        ],
        'code': '''def ancestor_chain(token_index, heads):
    chain = []
    while token_index != -1:
        chain.append(token_index)
        token_index = heads[token_index]
    return chain

def dependency_distance(left_token, right_token, heads):
    left_chain = ancestor_chain(left_token, heads)
    right_chain = ancestor_chain(right_token, heads)
    right_positions = {token: offset for offset, token in enumerate(right_chain)}
    return min((left_offset + right_positions[token]
                for left_offset, token in enumerate(left_chain) if token in right_positions),
               default=None)

parse_heads = [1, -1, 1, 2]
assert dependency_distance(0, 3, parse_heads) == 3
''',
        'cost': 'Walking both ancestor chains is O(h) time and O(h) space for tree height h; comparing every entity pair still costs O(e²·h) for e entities without candidate restrictions. Cache chains per sentence if throughput matters. The measured cost should include parsing and relation inference, not only this distance function. Pruning saves compute but can lower recall, so publish candidate recall alongside latency.',
        'mistakes': ['Publishing a relation because two entities have a short path.', 'Dropping the negator or quoted context from evidence.', 'Evaluating only candidates that survived pruning.', 'Reusing paths after a parser or tokenizer update.'],
        'related': [N + 'dependency-tree-contract-and-token-alignment', N + 'incident-syntax-extraction-project', N + 'relation-extraction-provenance', N + 'coreference-chains-and-mention-identity', N + 'grouped-temporal-text-validation'],
    },
    {
        'path': N + 'incident-syntax-extraction-project',
        'title': 'Project: extract incident actions from validated syntax',
        'module': Y, 'project': True,
        'summary': 'Build an action extractor that checks parse structure, keeps negation and source evidence, and stages disputed service relations for review.',
        'sections': [
            ('Set the output contract', 'The incident team needs subject, action, object and observed status from notes such as a service restarting a queue. Define the difference between planned, attempted, completed and negated actions. Store character spans and source revision for all arguments. The output is a proposed action record, not an authoritative change log. Ambiguous pronouns and unknown service IDs go to review.'),
            ('Prepare domain examples', 'Capture original incident notes with timestamps and speaker identity. Annotate entity spans, action cues, negation scope and reviewed service IDs. Include passive sentences, quoted commands, failed attempts, duplicated updates and later corrections. Group by incident and reserve recent incidents for audit. Validate parse heads and original offsets using [[natural-language-processing/dependency-tree-contract-and-token-alignment|the tree contract]] before feature extraction.'),
            ('Compare paths with a baseline', 'Use local lexical and entity-type rules as a first candidate generator. Add syntactic paths only if [[natural-language-processing/dependency-paths-for-relation-candidates|the dependency route]] improves candidate recall or reduces false staged edges. Measure candidate recall, end-to-end exact action F1, false completed-action rate and review workload. Do not evaluate a relation classifier solely on gold entity pairs. Review examples where parsing fails but the lexical baseline succeeds.'),
            ('Stage and revoke', 'Keep each proposed action with parser, tokenizer, entity model and rule versions. A reviewer approves, rejects or marks it superseded after a later note. Restrict evidence access to users who can read the incident. When the source changes, revalidate offsets and retire affected actions; never quietly update a previous approved record. [[natural-language-processing/entity-relation-ledger-project|The ledger project]] provides the state model for that handoff.'),
        ],
        'code': '''def stage_incident_action(subject, verb, object_id, source_revision, status):
    allowed_statuses = {"planned", "attempted", "completed", "negated"}
    if status not in allowed_statuses or not all((subject, verb, object_id, source_revision)):
        raise ValueError("invalid incident action")
    return {"subject": subject, "verb": verb, "object": object_id,
            "source_revision": source_revision, "observed_status": status,
            "review_state": "staged"}

action = stage_incident_action("service-k", "restart", "queue-m", "note-47-v3", "attempted")
assert action["observed_status"] != "completed"
''',
        'cost': 'The record gate is O(1) time and output space. Parsing every incident sentence and evaluating candidate pairs dominate compute; adjudication dominates human cost. Monitor p95 per-document latency, malformed parse rate, candidate recall and false completed actions together. A faster parser is not an improvement if it converts attempted or negated actions into approved completions.',
        'mistakes': ['Equating “attempted to restart” with a completed restart.', 'Omitting source revision from a staged action.', 'Assuming all dependency parse outputs are structurally valid.', 'Letting an approved action remain current after its source was corrected.'],
        'related': [N + 'dependency-tree-contract-and-token-alignment', N + 'dependency-paths-for-relation-candidates', N + 'entity-relation-ledger-project', N + 'coreference-chains-and-mention-identity', N + 'relation-extraction-provenance'],
    },
    {
        'path': N + 'translation-placeholder-and-terminology-contract',
        'title': 'Translation contracts for placeholders, numbers and terminology',
        'module': L, 'project': False,
        'summary': 'A translation can read naturally while changing an order identifier, amount, safety instruction or variable placeholder. Protect nonlinguistic tokens before evaluating style.',
        'sections': [
            ('Classify what may change', 'A customer message may contain a currency amount, date, order ID, product name and a template marker such as {ticket_id}. Some values require exact preservation; others need locale-aware formatting. Write a per-field policy. A placeholder should be protected by a typed sentinel whose mapping is stored securely, then restored and validated after translation. Do not assume the model will copy braces or digits faithfully. Keep the source revision, target locale and glossary version in the request manifest.'),
            ('Separate language quality from field integrity', 'A fluent sentence with the wrong amount is a failed translation. Run deterministic checks for protected tokens, expected identifiers, markup and numeric policy before human quality review. A repeated identifier may occur twice; compare multiplicity, not just set membership. Allow grammatical inflection of approved terms where the locale requires it, and review terminology in context. [[natural-language-processing/unicode-tokenization-boundary|Unicode handling]] matters when normalization changes visible punctuation or digits.'),
            ('Make ambiguity visible', 'A short source may not specify who acted, whether a refund is completed or what “it” refers to. Translators and models should not invent that context. Retain an uncertainty marker and request clarification for customer-facing high-impact copy. Preserve negation and modality. Review source and target side by side, including protected fields and back-linked evidence. The [[natural-language-processing/translation-evaluation-and-locale-slices|evaluation path]] covers adequacy and locale slices beyond exact-token checks.'),
            ('Package the serving rule', 'Version model, tokenizer, glossary, locale normalization, sentinel encoding and restore validator as one bundle. A failure to restore all placeholders must stop publication. Include inputs with adjacent placeholders, mixed scripts, repeated order IDs and right-to-left text in the audit set. The [[natural-language-processing/localized-support-reply-project|localized-reply project]] uses this contract before a message reaches a customer.'),
        ],
        'code': '''from collections import Counter
import re

PLACEHOLDER = re.compile(r"\\{[a-z][a-z0-9_]*\\}")

def validate_placeholders(source_text, translated_text):
    source = Counter(PLACEHOLDER.findall(source_text))
    translated = Counter(PLACEHOLDER.findall(translated_text))
    if source != translated:
        raise ValueError("placeholder names or counts changed")
    return translated

source = "Case {ticket_id} is assigned to {agent_name}."
target = "{agent_name} is assigned case {ticket_id}."
assert validate_placeholders(source, target)["{ticket_id}"] == 1
''',
        'cost': 'Scanning source and target is O(n + m) time and O(p) space for p distinct placeholders. Translation inference and bilingual review dominate operating cost. Deterministic validation is cheap and should run on every result, but it cannot prove meaning preservation. A protected token may survive while the sentence reverses negation, so combine field checks with reviewed adequacy samples.',
        'mistakes': ['Checking placeholder sets but missing a duplicated or deleted occurrence.', 'Assuming all numbers should be copied unchanged across locale formats.', 'Accepting fluent text that reverses negation or completion status.', 'Changing glossary or sentinel rules without versioning the translation bundle.'],
        'related': [N + 'translation-evaluation-and-locale-slices', N + 'localized-support-reply-project', N + 'unicode-tokenization-boundary', N + 'multilingual-calibration-and-fallback', N + 'text-serving-contract'],
    },
    {
        'path': N + 'translation-evaluation-and-locale-slices',
        'title': 'Evaluate translation by adequacy, terminology and locale slices',
        'module': L, 'project': False,
        'summary': 'Reference overlap can screen translation changes, but a release needs human checks for meaning, protected fields and harm in each supported locale.',
        'sections': [
            ('Freeze comparable inputs', 'Construct a reviewed audit set from actual supported workflows, not only clean benchmark sentences. Keep near-duplicate conversations in one split. Record source, reference translation, locale, domain, protected tokens and reviewer notes. A single source may have several valid translations, so an overlap score can penalize acceptable wording. Use corpus-level automated metrics as a regression signal and retain their tokenization settings with the report. [[natural-language-processing/grouped-temporal-text-validation|The split contract]] avoids copied ticket leakage.'),
            ('Review meaning and obligation', 'Ask bilingual reviewers whether the target preserves actor, action, tense, negation, amount and uncertainty. Score terminology separately from fluency. A translation that sounds native yet says a refund has arrived when the source says it is pending is operationally wrong. Review source-to-target and target-to-source where helpful, but back-translation alone is not proof because two errors can cancel. [[natural-language-processing/translation-placeholder-and-terminology-contract|Protected-field validation]] catches deterministic failures first.'),
            ('Report slices honestly', 'Break out short requests, long instructions, mixed scripts, formal and informal registers, product-specific vocabulary and each locale. Small slices should show support counts and uncertainty, not a confident green badge. Track the rate of untranslatable or ambiguous source messages and the number sent for clarification. If a locale lacks reviewed evidence, keep human approval as the default. The [[natural-language-processing/script-profile-and-code-switching-boundary|script profile]] may describe input, but it is not a locale truth label.'),
            ('Set a release gate', 'Require zero protected-token failures on the audit set, a minimum reviewed adequacy level by supported locale, an acceptable harmful-error count and a documented human fallback. Compare the same inputs across old and new bundles. A model update can improve average overlap while regressing a rare safety instruction. Monitor production correction reasons and human edit time after release. The [[natural-language-processing/localized-support-reply-project|reply project]] applies the gate.'),
        ],
        'code': '''def translation_release_gate(locale_audits):
    if not locale_audits:
        raise ValueError("at least one reviewed locale is required")
    for locale, audit in locale_audits.items():
        if audit["reviewed_cases"] < 47:
            return False, f"insufficient-review:{locale}"
        if audit["protected_token_failures"] or audit["harmful_meaning_errors"]:
            return False, f"critical-error:{locale}"
        if audit["adequacy_pass_rate"] < 0.91:
            return False, f"adequacy:{locale}"
    return True, "reviewed-locales-pass"

audits = {"hi-IN": {"reviewed_cases": 53, "protected_token_failures": 0,
                     "harmful_meaning_errors": 0, "adequacy_pass_rate": 0.94}}
assert translation_release_gate(audits)[0]
''',
        'cost': 'The gate is O(l) time and O(1) extra space for l locale audits. Human bilingual evaluation is the main cost; sample by risk and traffic, but keep a fixed minimum for every locale you claim to support. Automated metrics are cheap once references exist, yet they can miss semantic reversals. Report reviewer time, rejection reasons and post-release edits with model latency.',
        'mistakes': ['Using one aggregate overlap score as proof of translation quality.', 'Calling a locale supported with only a handful of reviewed cases.', 'Treating protected-token success as evidence that meaning is preserved.', 'Changing metric tokenization between model versions.'],
        'related': [N + 'translation-placeholder-and-terminology-contract', N + 'localized-support-reply-project', N + 'grouped-temporal-text-validation', N + 'script-profile-and-code-switching-boundary', N + 'classification-slices-and-abstention'],
    },
    {
        'path': N + 'localized-support-reply-project',
        'title': 'Project: release reviewed localized support replies',
        'module': L, 'project': True,
        'summary': 'Translate a support reply only after placeholders, amounts, terminology, meaning and locale-specific review have passed explicit gates.',
        'sections': [
            ('Define the customer-visible contract', 'The support agent drafts a reply about a pending refund. The translation must preserve pending status, amount, date, order reference and template placeholders. The agent remains accountable for sending it. Store source revision, target locale, translation bundle and reviewer decision. Unsupported locales return a manual translation request, not a nearest-language guess.'),
            ('Build the test set', 'Collect reviewed source replies with repeated placeholders, mixed scripts, product names, negative statements and ambiguous pronouns. Preserve grouping by case and split by time. For each locale, ask bilingual reviewers to mark adequacy, terminology, harmful meaning changes and whether a customer could act incorrectly. Include messages where the source itself needs clarification. [[natural-language-processing/translation-placeholder-and-terminology-contract|The field contract]] defines deterministic checks.'),
            ('Choose the release path', 'Compare the current and candidate translation bundles on the same audit set. Run protected-field checks on every output and bilingual review on sampled high-risk messages. Block release for missing placeholders, reversed refund status or unsupported locale claims. Use [[natural-language-processing/translation-evaluation-and-locale-slices|locale-slice evaluation]] to keep a strong majority language from hiding a weak minority locale. Keep the old bundle available for rollback.'),
            ('Operate human signoff', 'Return a draft and validation report to the agent. A reviewer can edit or reject it; store corrections under access control and include their reason in the next evaluation cycle. Never send the raw machine output automatically merely because it passed a token check. Monitor correction rate, customer misunderstandings, p95 latency and protected-field failures. Retain only the text and review data needed under the support retention policy.'),
        ],
        'code': '''def prepare_localized_reply(source, translated, locale, supported_locales, approved):
    if locale not in supported_locales:
        return {"state": "manual-translation", "reason": "unsupported-locale"}
    import re
    from collections import Counter
    marker = re.compile(r"\\{[a-z][a-z0-9_]*\\}")
    if Counter(marker.findall(source)) != Counter(marker.findall(translated)):
        return {"state": "blocked", "reason": "placeholder-mismatch"}
    if not approved:
        return {"state": "needs-agent-signoff", "text": translated}
    return {"state": "approved-draft", "text": translated}

reply = prepare_localized_reply("Refund {amount} is pending.",
                                "Refund {amount} is pending.", "hi-IN", {"hi-IN"}, False)
assert reply["state"] == "needs-agent-signoff"
''',
        'cost': 'The local marker comparison is O(n + m) time for source and target lengths and O(p) space for distinct placeholders. Translation inference, bilingual review and agent editing dominate total cost. Batch drafts only where privacy and latency allow it; never batch away signoff for high-impact replies. Track both automatic validation failures and meaning corrections so a low marker-error rate cannot mask poor translations.',
        'mistakes': ['Sending an approved draft without the agent’s final action.', 'Falling back to a related locale without reviewed evidence.', 'Ignoring a changed amount because placeholders still match.', 'Training on agent corrections before checking their source revision and consent policy.'],
        'related': [N + 'translation-placeholder-and-terminology-contract', N + 'translation-evaluation-and-locale-slices', N + 'multilingual-ticket-routing-project', N + 'privacy-safe-ticket-pipeline-project', N + 'text-serving-contract'],
    },
]
crosslinks = [
    (N + 'unicode-tokenization-boundary', N + 'dependency-tree-contract-and-token-alignment'),
    (N + 'relation-extraction-provenance', N + 'dependency-paths-for-relation-candidates'),
    (N + 'entity-relation-ledger-project', N + 'incident-syntax-extraction-project'),
    (N + 'multilingual-calibration-and-fallback', N + 'translation-evaluation-and-locale-slices'),
    (N + 'text-serving-contract', N + 'localized-support-reply-project'),
    (N + 'translation-placeholder-and-terminology-contract', N + 'translation-evaluation-and-locale-slices'),
    (N + 'dependency-tree-contract-and-token-alignment', N + 'dependency-paths-for-relation-candidates'),
]

if __name__ == '__main__':
    publish(lessons, (Y, L), crosslinks,
            'aitrove-nlp-syntax-translation-import-20261006.json', 4740,
            subject='natural-language-processing', hub_path=N + 'nlp-tutorial')
