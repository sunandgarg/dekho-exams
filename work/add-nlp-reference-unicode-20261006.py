"""Add incident reference identity and Unicode text-identity lessons."""
from de_batch_publisher import publish

N = 'natural-language-processing/'
R = 'Reference identity across incident documents'
U = 'Unicode identity and spoof-resistant text'

lessons = [
    {
        'path': N + 'coreference-split-antecedents-and-bridging',
        'title': 'References to groups and related entities: identity versus bridging',
        'module': R, 'project': False,
        'summary': '“They” may denote two earlier actors, while “the gateway” may be associated with a deployment without being that deployment. Model both cases explicitly.',
        'sections': [
            ('Separate identity from association', 'Coreference links mentions that denote the same entity. Bridging links a new entity to something already mentioned: “the deployment failed; the gateway retried” does not mean gateway and deployment are identical. Record a typed relation instead of merging their chains. A bad merge can make a later summary claim the deployment itself retried. [[natural-language-processing/coreference-chains-and-mention-identity|Mention-chain identity]] provides the base rule; bridging preserves a related but distinct referent.'),
            ('Allow several antecedents when the text does', '“The API and worker restarted. They recovered after 47 seconds” refers to a group formed from two earlier entities. Picking the nearest single noun loses one participant. Represent the group mention with a stable group ID and member IDs, while keeping both original entity chains intact. Do not invent group membership from adjacency alone. The plural form, sentence structure and incident context are evidence, but a reviewer should inspect high-impact recovery claims.'),
            ('Preserve unresolved references', 'A note that says “it failed again” may follow mentions of a queue, a gateway and a check. If the context does not identify which one failed, store an unresolved mention with candidate chain IDs and its source span. Do not attach it to the most recent noun just to complete the graph. [[natural-language-processing/role-frame-decoding-and-provenance|Role frames]] can help identify what action a mention performs, but they cannot recover an absent antecedent from thin air.'),
            ('Score the distinctions that matter', 'Evaluate identity-chain links, group membership, bridging edges and unresolved rate separately. An ordinary pair score can reward a system that overmerges easy names while missing group and bridging cases. Include repeated component names, revisions and quoted prior updates. Inspect whether downstream timelines and summaries attribute failures to the right service. The [[natural-language-processing/incident-reference-audit-project|reference audit project]] checks the user-visible effect rather than only mention-pair agreement.'),
        ],
        'code': '''def reference_record(mention_id, relation, targets, source_revision):
    if not mention_id or not source_revision:
        raise ValueError("mention and source revision are required")
    if relation == "group" and len(set(targets)) < 2:
        raise ValueError("a group needs distinct members")
    if relation == "identity" and len(targets) != 1:
        raise ValueError("identity needs one chain")
    if relation not in {"group", "identity", "bridging", "unresolved"}:
        raise ValueError("unknown reference relation")
    return {"mention_id": mention_id, "relation": relation,
            "targets": tuple(targets), "source_revision": source_revision}

group = reference_record("they-47", "group", ["api-12", "worker-19"], "note-r3")
assert group["targets"] == ("api-12", "worker-19")
assert reference_record("it-82", "unresolved", [], "note-r3")["relation"] == "unresolved"
''',
        'cost': 'Validating k target IDs costs O(k) time and O(k) temporary space. Candidate generation over m mentions can reach O(m²) if every mention is compared with every earlier one; section and incident boundaries reduce that work. Human review is most valuable where a group or bridging decision changes a published incident claim.',
        'mistakes': ['Merging a component with an event merely because they are related.', 'Forcing a plural pronoun onto one nearest antecedent.', 'Replacing an unresolved reference with a guess to make a graph complete.', 'Reporting only overall chain scores while group membership is wrong.'],
        'related': [N + 'cross-document-mention-chain-revision-and-access', N + 'incident-reference-audit-project', N + 'coreference-chains-and-mention-identity', N + 'role-frame-decoding-and-provenance', N + 'incident-handoff-summary-project'],
    },
    {
        'path': N + 'cross-document-mention-chain-revision-and-access',
        'title': 'Cross-document reference chains: revisions, scope and access',
        'module': R, 'project': False,
        'summary': 'The same service can appear in multiple updates, but identical strings alone do not justify merging incidents or exposing restricted evidence.',
        'sections': [
            ('Define the join scope first', 'A handoff might combine a status message, deployment note and operator transcript. Link mentions only after verifying incident ID, service registry identity and time context. Two tickets can both say “gateway” while referring to separate environments or regions. Keep document ID, revision and span on every mention, and record why two chains were joined. [[natural-language-processing/entity-link-candidates-and-nil-decision|Entity linking]] proposes registry identities; coreference still decides whether particular mentions in context denote the same thing.'),
            ('Treat revisions as new evidence', 'A corrected update may change “the gateway failed” to “the gateway check failed.” A chain derived from the old sentence cannot remain silently active. Mark its mention and dependent edges stale, then re-evaluate the corrected span under the current document revision. Preserve the old chain for audit. [[natural-language-processing/passage-revision-and-index-audit|Passage revision tracking]] helps find derived entries that need a rebuild after source edits.'),
            ('Keep access on each mention', 'A public status page and a restricted incident note may refer to the same service. Their mention chains can be connected internally, but a public answer must use only evidence the reader may see. Do not leak a restricted quotation, speaker or document title through a generated explanation. Filter source spans before assembling the visible chain, and distinguish a missing public antecedent from an unresolved private one. The access decision is per evidence item, not a property of the service name.'),
            ('Audit merges and downstream claims', 'Review a sample of accepted joins, rejected joins and NIL candidates after every registry or document revision. Measure wrong cross-incident merge rate, stale-edge rate and access violations. Pair metrics alone cannot show whether a summary assigned a rollback to the wrong region. Run a final claim check against visible, active source spans. The [[natural-language-processing/incident-reference-audit-project|applied audit]] turns these conditions into a release gate.'),
        ],
        'code': '''def can_join_mentions(left, right):
    if left["incident_id"] != right["incident_id"]:
        return False
    if left["environment"] != right["environment"]:
        return False
    return (left["registry_id"] is not None and
            left["registry_id"] == right["registry_id"] and
            bool(left["source_revision"]) and bool(right["source_revision"]))

first = {"incident_id": "inc-47", "environment": "staging",
         "registry_id": "gateway-west", "source_revision": "r2"}
second = {"incident_id": "inc-47", "environment": "staging",
          "registry_id": "gateway-west", "source_revision": "r5"}
assert can_join_mentions(first, second)
assert not can_join_mentions(first, {**second, "environment": "production"})
''',
        'cost': 'Checking one candidate pair is O(1). Building all cross-document pairs is potentially quadratic in mentions, so partition by incident and environment before matching. A registry ID is useful evidence but not a timeless guarantee: track registry migrations and source revisions, and budget reviewer time for merges that affect incident summaries.',
        'mistakes': ['Joining two “gateway” mentions across unrelated incidents.', 'Leaving a chain active after its supporting note is corrected.', 'Using a restricted antecedent to explain a public mention.', 'Assuming a shared registry ID means two different environments are the same instance.'],
        'related': [N + 'coreference-split-antecedents-and-bridging', N + 'incident-reference-audit-project', N + 'entity-link-version-and-merge-review', N + 'passage-revision-and-index-audit', N + 'generated-claim-evidence-and-unanswered-state'],
    },
    {
        'path': N + 'incident-reference-audit-project',
        'title': 'Project: audit references across incident updates',
        'module': R, 'project': True,
        'summary': 'Build reviewable mention chains across incident notes, including plural references and related entities, without crossing access or revision boundaries.',
        'sections': [
            ('Set the incident task', 'A responder reads updates saying “the API and worker restarted,” “they recovered,” and “the gateway check still failed.” The system proposes entity chains, a group reference and a related check, then drafts a handoff. Every displayed claim needs an active source span and reader access. Start from exact mention spans, document revisions and incident IDs rather than replacing source sentences with a model paraphrase. [[natural-language-processing/coreference-split-antecedents-and-bridging|Group and bridging rules]] determine which links are identity and which are association.'),
            ('Build difficult cases', 'Collect parallel incidents with repeated service names, staging and production updates, corrections, quotations and notes with several plausible antecedents. Annotate group membership, bridging relations, unresolved pronouns and registry IDs. Group every revision of one incident before splitting evaluation. Include a restricted note whose content may support an internal review but must not appear in a public handoff. A realistic holdout needs wrong-merge traps, not only easy repeated names.'),
            ('Stage chains with reasons', 'Generate candidates within incident and environment scope, then retain the source span and match reason on each proposed edge. Mark edges stale when their source revision changes. Require review for high-impact ambiguous group or bridging decisions. The draft handoff may state that a referent is unresolved. [[natural-language-processing/cross-document-mention-chain-revision-and-access|Cross-document scope]] and access filtering run before any visible claim is assembled.'),
            ('Gate the release', 'Score incorrect cross-incident merges, missing group members, identity-versus-bridging confusion, stale evidence and access leaks. Review final handoff sentences for claims about the wrong component or environment. Measure reviewer time and abstention, since forcing every pronoun into a chain can improve a pair metric while harming the handoff. Shadow the system on resolved incidents, then keep the previous chain build available for rollback.'),
        ],
        'code': '''def visible_mentions(mentions, reader_roles, current_revisions):
    visible = []
    for mention in mentions:
        if mention["source_revision"] != current_revisions.get(mention["document_id"]):
            continue
        if not set(mention["roles_allowed"]) & set(reader_roles):
            continue
        visible.append(mention["mention_id"])
    return visible

mentions = [
    {"mention_id": "api-47", "document_id": "status", "source_revision": "r3",
     "roles_allowed": ["public", "responder"]},
    {"mention_id": "trace-82", "document_id": "private", "source_revision": "r4",
     "roles_allowed": ["responder"]},
]
assert visible_mentions(mentions, {"public"}, {"status": "r3", "private": "r4"}) == ["api-47"]
''',
        'cost': 'Filtering m mentions is O(m) time and O(m) output space with small role sets. Candidate creation and reviewer checks add more work. Access should be enforced again at the final sentence-evidence boundary; a correct hidden chain can still leak if a generated handoff quotes its restricted source.',
        'mistakes': ['Showing a restricted antecedent in a public explanation.', 'Using a stale source revision for a new handoff.', 'Collapsing a group mention into one component.', 'Judging chain quality without inspecting final incident claims.'],
        'related': [N + 'coreference-split-antecedents-and-bridging', N + 'cross-document-mention-chain-revision-and-access', N + 'incident-handoff-summary-project', N + 'incident-discourse-map-project', N + 'entity-relation-ledger-project'],
    },
    {
        'path': N + 'unicode-normalization-and-source-offsets',
        'title': 'Unicode normalization: search keys without losing source offsets',
        'module': U, 'project': False,
        'summary': 'Canonical and compatibility normalization solve different comparison problems. Keep original text and map transformed spans back to it.',
        'sections': [
            ('Choose normalization by field', 'Two visually similar strings may use different code-point sequences. NFC can make canonically equivalent forms comparable; compatibility normalization may also fold distinctions that a document preserves intentionally. Use a documented comparison form for each field: a search key, identifier and quoted source passage may need different treatment. Do not turn the normalized value into the only stored copy. [[natural-language-processing/unicode-tokenization-boundary|Tokenization boundaries]] depend on the chosen text form and must be versioned with the index.'),
            ('Retain an offset map', 'A detected entity span on transformed text is not automatically an offset into the original text. Normalization can change code-point count, and case folding can do so too. Record source revision, normalization policy and a mapping from transformed ranges to original ranges, or run span extraction on the original and normalize only comparison keys. A highlight that points into the wrong customer name is a real product error, not a cosmetic discrepancy. [[natural-language-processing/span-offset-annotation|Span annotations]] must stay anchored to the original.'),
            ('Keep search and identity separate', 'Search may index alternate forms to improve recall, while an account identifier or document ID needs its own exact equality and security policy. Do not use a broad compatibility fold as an implicit authority to merge accounts, incidents or entities. Show the user the original spelling, and make the matching policy inspectable. [[natural-language-processing/confusable-identifier-triage-and-script-policy|Confusable triage]] addresses lookalike characters that ordinary normalization does not necessarily collapse.'),
            ('Audit language and revision effects', 'Test combining marks, full-width forms, ligatures, emoji sequences and text from each supported script. Measure retrieved-result changes, broken highlights and accidental key collisions. Reindex when a normalization policy changes, and retain the old policy version for comparison. A transformation that improves one language may damage another or convert two distinct operational IDs into the same key. The [[natural-language-processing/spoof-resistant-text-intake-project|intake project]] keeps those cases visible during release review.'),
        ],
        'code': '''import unicodedata

def comparison_record(source_text, policy_version):
    return {"original": source_text,
            "nfc_key": unicodedata.normalize("NFC", source_text),
            "policy_version": policy_version}

composed = comparison_record("caf\u00e9", "norm-r4")
decomposed = comparison_record("cafe\u0301", "norm-r4")
assert composed["nfc_key"] == decomposed["nfc_key"]
assert composed["original"] != decomposed["original"]
''',
        'cost': 'Normalizing n code points is O(n) time and O(n) output space. Maintaining a reliable transformed-to-source offset map also costs O(n) and needs explicit tests for expansions and contractions. The short code only builds a comparison record; it deliberately does not claim that offsets in the key can be reused on the original.',
        'mistakes': ['Overwriting source text with a normalized key.', 'Using transformed offsets to highlight the original passage.', 'Applying compatibility folding to authoritative IDs without a collision policy.', 'Changing normalization without rebuilding affected search indexes.'],
        'related': [N + 'confusable-identifier-triage-and-script-policy', N + 'spoof-resistant-text-intake-project', N + 'unicode-tokenization-boundary', N + 'span-offset-annotation', N + 'script-profile-and-code-switching-boundary'],
    },
    {
        'path': N + 'confusable-identifier-triage-and-script-policy',
        'title': 'Confusable identifiers: script policy and review queues',
        'module': U, 'project': False,
        'summary': 'A visually familiar service name can contain different characters. Triage suspicious identifiers without treating every multilingual phrase as an attack.',
        'sections': [
            ('Scope the policy to identifiers', 'An incident title may mix scripts legitimately. A machine-readable service slug, however, usually has a narrower alphabet contract. Define allowed characters and case policy for each identifier field, rather than applying one mixed-script rejection rule to all natural language. Preserve the original bytes and code points for audit. [[natural-language-processing/script-profile-and-code-switching-boundary|Script profiling]] helps describe a message; a security decision needs field-specific rules and a reviewed allowlist.'),
            ('Separate normalization from lookalikes', 'Canonical normalization does not make every visually similar character equal. A Latin letter and a similar-looking letter from another script may remain different keys. A full confusable analysis needs a versioned character mapping and a declared supported repertoire; a small script check is only a triage signal. Do not use a generated visual skeleton as the displayed identifier or as unquestioned proof of identity. [[natural-language-processing/unicode-normalization-and-source-offsets|Normalization policy]] provides a separate comparison step.'),
            ('Make collisions reviewable', 'When a new identifier resembles an existing service slug, stage both originals, code-point names, owner and registry IDs for review. Restrict creation or require approval according to the field policy. Do not silently merge two accounts or services because a visual mapping matches. Conversely, avoid flagging every multilingual customer message; the policy belongs to identifier creation and high-risk routing, not ordinary prose. Keep a decision record so a later policy revision can revisit accepted exceptions.'),
            ('Measure both safety and friction', 'Audit missed lookalikes, false alarms by language, reviewer time and accidental collisions after registry changes. Use realistic font renderings in manual review because visual similarity depends on display context. A triage rule that blocks legitimate names can harm users even while catching a few suspicious cases. The [[natural-language-processing/spoof-resistant-text-intake-project|intake project]] tests how the identifier rule interacts with search and customer text.'),
        ],
        'code': '''import unicodedata

def identifier_script_hint(identifier):
    scripts = set()
    for character in identifier:
        if character.isalpha():
            name = unicodedata.name(character, "")
            scripts.add(name.split(" ", 1)[0] if name else "UNKNOWN")
    return {"scripts": sorted(scripts), "review": len(scripts) > 1}

latin = identifier_script_hint("gateway47")
mixed = identifier_script_hint("gаteway47")  # second character is Cyrillic
assert latin["scripts"] == ["LATIN"]
assert mixed["review"]
''',
        'cost': 'This illustrative name-based scan is O(n) time and O(s) space for n characters and s observed name prefixes. It is a triage hint, not complete script detection or confusable comparison: common, inherited and complex script properties need a dedicated, versioned standard-data implementation. Apply the stronger check at identifier boundaries, where review volume is manageable.',
        'mistakes': ['Treating a simple mixed-script hint as a complete confusable detector.', 'Rejecting multilingual prose under an identifier-only policy.', 'Displaying a transformed skeleton instead of the submitted spelling.', 'Automatically merging records because two identifiers look alike.'],
        'related': [N + 'unicode-normalization-and-source-offsets', N + 'spoof-resistant-text-intake-project', N + 'script-profile-and-code-switching-boundary', N + 'entity-link-candidates-and-nil-decision', N + 'privacy-safe-ticket-pipeline-project'],
    },
    {
        'path': N + 'spoof-resistant-text-intake-project',
        'title': 'Project: preserve text identity in support intake',
        'module': U, 'project': True,
        'summary': 'Accept multilingual support text, keep source spans stable and review lookalike service identifiers before they enter routing or search.',
        'sections': [
            ('Set distinct field contracts', 'A support message is free-form multilingual text; a service slug is a controlled identifier. Store the original message and identifier separately. Build an NFC comparison key for search, but retain source offsets for highlights and audits. Apply a field-specific identifier policy only to the slug. The service should never rewrite a customer quotation merely to make search easier. [[natural-language-processing/unicode-normalization-and-source-offsets|Normalization and offsets]] define the source-to-key relationship.'),
            ('Build an adversarial review set', 'Include canonically equivalent names, combining marks, full-width text, mixed-script lookalikes, ordinary code switching and copied screenshots that passed through OCR. Annotate which field is an identifier, which is prose and what the user should see. Group near-identical tickets and document revisions in the same evaluation split. Include a suspicious service slug whose visual form resembles an approved one, plus legitimate multilingual prose that must pass without identifier alarms.'),
            ('Stage routing and review', 'Normalize comparison keys without discarding originals, then run field-specific identifier triage. Hold suspicious new slugs for owner review; do not auto-merge them with the nearest existing slug. Continue processing the free-form message under ordinary privacy and language rules. Any extracted span shown to a reviewer must map back to the original source revision. [[natural-language-processing/confusable-identifier-triage-and-script-policy|The identifier policy]] is a review gate, not a general language filter.'),
            ('Release against user-visible errors', 'Measure wrong routing, missed suspicious slugs, false alarms by script, broken highlights and search-result changes. Inspect whether a customer can still find a document using an alternate Unicode form while the displayed title retains its source spelling. Shadow the policy before release and keep old index keys until migration passes. Roll back if legitimate messages are blocked or if identifiers collapse into the same authority key without review.'),
        ],
        'code': '''import unicodedata

def stage_intake(message, service_slug, allowed_slugs):
    search_key = unicodedata.normalize("NFC", message)
    if service_slug not in allowed_slugs:
        return {"state": "review-identifier", "original_message": message,
                "search_key": search_key, "service_slug": service_slug}
    return {"state": "accepted", "original_message": message,
            "search_key": search_key, "service_slug": service_slug}

record = stage_intake("cafe\u0301 gateway alert", "gateway-west",
                      {"gateway-west", "worker-east"})
assert record["state"] == "accepted"
assert record["original_message"] != record["search_key"]
assert stage_intake("gateway alert", "gаteway-west", {"gateway-west"})["state"] == "review-identifier"
''',
        'cost': 'Creating a comparison key for n characters is O(n) time and space; membership in an in-memory allowed-slug set is expected O(1). The code uses exact allowlisting for illustration, not a full confusable algorithm. A production registration path also needs a versioned security mapping and owner review. Keep search recall and identifier authority as separate measured outcomes.',
        'mistakes': ['Normalizing away the only stored copy of the message.', 'Applying identifier rejection rules to all customer prose.', 'Auto-merging a suspicious slug with a visually similar approved one.', 'Highlighting the normalized key with offsets from the original message.'],
        'related': [N + 'unicode-normalization-and-source-offsets', N + 'confusable-identifier-triage-and-script-policy', N + 'document-intake-ocr-project', N + 'privacy-safe-ticket-pipeline-project', N + 'script-profile-and-code-switching-boundary'],
    },
]

crosslinks = [
    (N + 'coreference-chains-and-mention-identity', N + 'coreference-split-antecedents-and-bridging'),
    (N + 'entity-link-candidates-and-nil-decision', N + 'cross-document-mention-chain-revision-and-access'),
    (N + 'incident-handoff-summary-project', N + 'incident-reference-audit-project'),
    (N + 'unicode-tokenization-boundary', N + 'unicode-normalization-and-source-offsets'),
    (N + 'span-offset-annotation', N + 'unicode-normalization-and-source-offsets'),
    (N + 'script-profile-and-code-switching-boundary', N + 'confusable-identifier-triage-and-script-policy'),
    (N + 'document-intake-ocr-project', N + 'spoof-resistant-text-intake-project'),
]

if __name__ == '__main__':
    publish(lessons, (R, U), crosslinks,
            'aitrove-nlp-reference-unicode-import-20261006.json', 4830,
            subject='natural-language-processing', hub_path=N + 'nlp-tutorial')
