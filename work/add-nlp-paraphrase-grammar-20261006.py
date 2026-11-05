"""Add paraphrase and grammar-edit learning paths."""
from de_batch_publisher import publish

N = 'natural-language-processing/'
P = 'Paraphrase and duplicate decisions'
G = 'Grammar correction with meaning preservation'

lessons = [
    {
        'path': N + 'paraphrase-equivalence-and-hard-negatives',
        'title': 'Paraphrase equivalence: make hard negatives change the decision',
        'module': P, 'project': False,
        'summary': 'Two support messages can share almost every word while disagreeing about status, amount or actor. Label equivalence for the downstream decision, not surface overlap.',
        'sections': [
            ('Write the equivalence rule', 'For duplicate incident detection, two messages are equivalent only when they describe the same operational issue at a compatible time and scope. “The gateway retried 47 times” and “The gateway allows 47 retries” are related but not duplicates: observed count and configured limit answer different questions. Store source revisions, conversation group, entity IDs and a reviewer label with an explicit reason. A semantic similarity score is a candidate signal, not a truth label. [[natural-language-processing/nli-premise-hypothesis-and-evidence-contract|Entailment]] asks whether one statement supports another; bidirectional equivalence is stricter.'),
            ('Build adversarial pairs', 'Include changed negation, numbers, product versions, speakers and dates. Add truly equivalent pairs with different wording, word order and abbreviations. A random unrelated negative set is too easy. Review mined hard negatives because an apparently different message may be a legitimate duplicate after context is read. Keep copied templates and repeated incidents in one split. [[natural-language-processing/grouped-temporal-text-validation|Grouped temporal validation]] prevents the same event from leaking into train and audit.'),
            ('Handle asymmetry and context', '“Payment failed” may summarize “payment failed after the callback timed out,” but the shorter sentence omits a cause; whether that counts as a duplicate depends on the task. Define whether paraphrase requires exact informational equivalence or merely the same resolution queue. Do not silently change between these definitions. Record surrounding context needed to resolve pronouns and ticket references, while withholding private text from users without access.'),
            ('Measure the actual decision', 'Report pair precision and recall at a chosen threshold, then evaluate cluster errors once pairs are connected. A few false pair links can merge unrelated incidents. Break out number changes, negation and cross-language pairs. Compare a lexical baseline against an embedding candidate system and a pairwise reranker. [[natural-language-processing/paraphrase-cluster-transitivity-review|Cluster review]] addresses the nontransitive edges, and the [[natural-language-processing/support-duplicate-review-project|support duplicate project]] tests the operational release.'),
        ],
        'code': '''def protected_fields_match(left, right):
    if left["incident_id"] != right["incident_id"]:
        return False
    for field in ("observed_status", "product_version", "amount_minor"):
        if left.get(field) != right.get(field):
            return False
    return True

first = {"incident_id": "inc-47", "observed_status": "failed",
         "product_version": "v7", "amount_minor": 2847}
changed = {**first, "amount_minor": 2947}
assert not protected_fields_match(first, changed)
''',
        'cost': 'A protected-field gate is O(1) for a fixed field list. Comparing every pair of n messages is O(n²), so generate candidates by time, tenant and index before applying a costly pair model. Candidate pruning reduces work but can lose true duplicates. Publish candidate recall, pair precision and wrongful cluster merges alongside p95 matching latency.',
        'mistakes': ['Treating shared keywords as equivalence.', 'Using an easy random-negative test set and missing changed-number failures.', 'Equating one-way entailment with a paraphrase.', 'Scoring pair labels without measuring the incident clusters users see.'],
        'related': [N + 'paraphrase-cluster-transitivity-review', N + 'support-duplicate-review-project', N + 'nli-premise-hypothesis-and-evidence-contract', N + 'text-embedding-pair-and-version-contract', N + 'grouped-temporal-text-validation'],
    },
    {
        'path': N + 'paraphrase-cluster-transitivity-review',
        'title': 'Duplicate clusters: review transitivity, bridges and source identity',
        'module': P, 'project': False,
        'summary': 'Pair scores do not automatically form safe duplicate groups. A single weak bridge can join two unrelated incident families.',
        'sections': [
            ('Separate pair confidence from cluster identity', 'If A matches B and B matches C, it does not follow that A and C describe the same incident. B may be a vague message that fits both. Simple connected components will still merge all three. Define a cluster rule: common verified incident key, reviewer approval for cross-group bridges or a representative-medoid check. Keep a reason and model version for every accepted edge. A cluster ID should remain stable across model updates only through an explicit migration.'),
            ('Find bridge errors early', 'Inspect edges whose removal splits a large component, clusters with mixed product versions and members with incompatible protected fields. Review the shortest explanation path between a new message and the cluster representative. A broad outage creates thousands of similar tickets, so cap reviewer workload with risk-ranked samples rather than reviewing every pair. Never let one uncertain edge silently swallow a separate privacy or billing incident.'),
            ('Evaluate at two levels', 'Use reviewed pair labels for precision and recall, then compare resulting clusters with incident-level truth. Report false merges, false splits, maximum cluster size and changes after retraining. A method can improve pair F1 while making one catastrophic merge. Reserve whole incidents and time windows for audit; copied templates across splits can hide the problem. [[natural-language-processing/paraphrase-equivalence-and-hard-negatives|Equivalence policy]] defines a valid edge.'),
            ('Manage revisions and deletions', 'When a source message is edited or removed, revalidate edges based on that revision and recompute affected clusters. Do not expose a private ticket title through a cluster shared with another tenant. Store access scope on every membership query. The [[natural-language-processing/support-duplicate-review-project|project]] stages cluster changes for review and keeps a rollback snapshot.'),
        ],
        'code': '''def safe_cluster_members(seed_id, accepted_edges, compatible):
    members = {seed_id}
    frontier = [seed_id]
    while frontier:
        current = frontier.pop()
        for left, right in accepted_edges:
            candidate = right if left == current else left if right == current else None
            if candidate is None or candidate in members:
                continue
            if all(compatible(candidate, existing) for existing in members):
                members.add(candidate)
                frontier.append(candidate)
    return members

edges = [("ticket-47", "ticket-82"), ("ticket-82", "ticket-91")]
compatible = lambda candidate, existing: {candidate, existing} != {"ticket-47", "ticket-91"}
assert safe_cluster_members("ticket-47", edges, compatible) == {"ticket-47", "ticket-82"}
''',
        'cost': 'This direct scan revisits all e edges for each accepted member and checks compatibility with current members, reaching O(m·e + m²) time for m members; it is a clear audit example, not a large-scale clustering engine. Index adjacency and cache approved constraints for production. Review cost should target high-impact bridge edges, while reporting false merges as a release-blocking metric.',
        'mistakes': ['Taking transitive closure of uncertain pair predictions without review.', 'Preserving a cluster ID after its source evidence changed.', 'Reporting pair F1 while hiding a large wrongful merge.', 'Showing private ticket details to another tenant through shared membership.'],
        'related': [N + 'paraphrase-equivalence-and-hard-negatives', N + 'support-duplicate-review-project', N + 'grouped-temporal-text-validation', N + 'hybrid-ranking-and-access-filters', N + 'privacy-safe-ticket-pipeline-project'],
    },
    {
        'path': N + 'support-duplicate-review-project',
        'title': 'Project: stage support-ticket duplicate groups for review',
        'module': P, 'project': True,
        'summary': 'Build a duplicate-review queue that proposes incident groups, blocks incompatible status or amount changes and keeps every merge reversible.',
        'sections': [
            ('Set the workflow', 'Support agents want to see potentially repeated customer reports without losing separate cases. The service proposes a candidate pair with reasons and protected-field comparisons; a reviewer accepts a merge or rejects it. No model output deletes a ticket or collapses customer histories automatically. Keep tenant scope and incident permissions attached to all candidates.'),
            ('Construct a hard corpus', 'Collect messages from the same incident plus near misses from adjacent incidents. Include number changes, negated status, repeated templates, revised ticket text and messages from different customer accounts. Label pair equivalence under one policy version. Group by incident and time before splitting. Use [[natural-language-processing/paraphrase-equivalence-and-hard-negatives|the equivalence contract]] to keep an identical phrase from overriding an incompatible observed fact.'),
            ('Stage cluster changes', 'Retrieve likely pairs, run a pair model and protected-field gate, then propose an edge. Compute the candidate cluster and flag any bridge that would unite two previously separate groups. Require a reviewer for high-impact merges. [[natural-language-processing/paraphrase-cluster-transitivity-review|Cluster review]] explains why pair accuracy alone is insufficient. Store before and after membership snapshots so a mistaken merge can be undone.'),
            ('Operate safely', 'Track reviewer acceptance, false merges, false splits, queue age and cross-tenant access checks. Sample confident automatic suggestions for audit even if they were not merged. A new embedding model needs a fresh index and replay against the fixed incident-level audit set. If a ticket is deleted under retention policy, remove derived vectors and invalidate its incident-group edges.'),
        ],
        'code': '''def stage_duplicate_edge(left, right, same_tenant, fields_compatible):
    if left == right:
        raise ValueError("a ticket cannot duplicate itself")
    if not same_tenant:
        return {"state": "rejected", "reason": "tenant-boundary"}
    if not fields_compatible:
        return {"state": "review", "reason": "protected-field-conflict"}
    return {"state": "review", "reason": "candidate-duplicate",
            "tickets": tuple(sorted((left, right)))}

proposal = stage_duplicate_edge("ticket-47", "ticket-82", True, True)
assert proposal["state"] == "review"
''',
        'cost': 'The staging gate is O(1) time and space. Candidate retrieval and pair reranking dominate compute; incident-level review dominates human cost. Model throughput is secondary to wrongful merge rate. Store only the minimum pair evidence required for review, and enforce tenant access before the candidate is displayed or cached.',
        'mistakes': ['Auto-merging tickets because their pair score exceeds a threshold.', 'Ignoring a changed amount or negated status.', 'Testing pairs while never measuring group-level false merges.', 'Leaving deleted ticket embeddings in the candidate index.'],
        'related': [N + 'paraphrase-equivalence-and-hard-negatives', N + 'paraphrase-cluster-transitivity-review', N + 'text-embedding-pair-and-version-contract', N + 'privacy-safe-ticket-pipeline-project', N + 'grouped-temporal-text-validation'],
    },
    {
        'path': N + 'grammar-edit-spans-and-protected-fields',
        'title': 'Grammar correction: edit spans without changing protected meaning',
        'module': G, 'project': False,
        'summary': 'A grammatical rewrite should not alter a customer’s amount, order ID, negation or uncertainty. Represent each edit so it can be reviewed and rejected.',
        'sections': [
            ('Set the editor’s authority', 'The editor may fix spelling and grammar in a support draft, but it must not decide whether a refund is approved. Mark identifiers, amounts, dates, product names and placeholders as protected fields. Keep the unedited original and return an ordered list of replacement spans rather than a bare new string. A reviewer can then inspect what changed. [[natural-language-processing/translation-placeholder-and-terminology-contract|Translation token protection]] covers a related boundary, but grammar editing also must preserve negation and modality.'),
            ('Validate a proposed edit', 'Each edit uses half-open original offsets, old text and replacement. Reject overlap and stale source mismatches. Apply edits from right to left so earlier offsets remain valid. Some correct grammar changes span multiple words; do not assume every edit is one token. Preserve Unicode representation and avoid normalizing the source after offsets are recorded. [[natural-language-processing/span-offset-annotation|Original span alignment]] defines the coordinate system.'),
            ('Review meaning preservation', '“The refund may arrive tomorrow” must not become “The refund will arrive tomorrow.” A grammar model can produce fluent, confident text while strengthening a promise or deleting “not.” Compare protected tokens, critical entities and explicit status words before presentation, then sample outputs for human adequacy review. Multiple valid corrections may exist, so exact match to one reference is an incomplete quality metric. [[natural-language-processing/grammar-correction-review-and-abstention|Review gates]] decide when the editor should abstain.'),
            ('Measure the edits users accept', 'Report accepted edit rate, unnecessary edit rate, protected-field failures, meaning reversals and reviewer time saved. Break out non-native writing, mixed-language messages and technical identifiers. A model that changes many words may have high fluency yet create more review work than a conservative rule baseline. The [[natural-language-processing/support-reply-grammar-project|support reply project]] puts these tradeoffs into a real draft workflow.'),
        ],
        'code': '''def apply_reviewable_edits(original_text, edits):
    ordered = sorted(edits, key=lambda edit: edit["start"])
    previous_end = 0
    for edit in ordered:
        start, end = edit["start"], edit["end"]
        if not 0 <= start < end <= len(original_text) or start < previous_end:
            raise ValueError("invalid or overlapping edit")
        if original_text[start:end] != edit["old"]:
            raise ValueError("stale edit source")
        previous_end = end
    corrected = original_text
    for edit in reversed(ordered):
        corrected = (corrected[:edit["start"]] + edit["replacement"]
                     + corrected[edit["end"]:])
    return corrected

draft = "Refund are pending for order ZX-47."
assert apply_reviewable_edits(draft, [{"start": 7, "end": 10,
    "old": "are", "replacement": "is"}]) == "Refund is pending for order ZX-47."
''',
        'cost': 'Sorting e edits takes O(e log e); repeated immutable-string replacements can copy O(n·e) characters for n source characters. For large documents, assemble output once after validation. Model generation and reviewer inspection dominate cost for short support drafts. Measure meaning-change failures separately; lower latency does not justify an editor that strengthens a customer-facing promise.',
        'mistakes': ['Returning only a rewritten string with no inspectable edit trail.', 'Applying original offsets left to right after text length changes.', 'Treating one reference correction as the only acceptable output.', 'Accepting a grammatical sentence that changes “may” to “will.”'],
        'related': [N + 'grammar-correction-review-and-abstention', N + 'support-reply-grammar-project', N + 'span-offset-annotation', N + 'translation-placeholder-and-terminology-contract', N + 'summary-claim-verification-and-review'],
    },
    {
        'path': N + 'grammar-correction-review-and-abstention',
        'title': 'Grammar correction review: minimal edits, abstention and audit',
        'module': G, 'project': False,
        'summary': 'An editor should fix clear errors, leave uncertain text alone and make risky changes easy for an agent to reject.',
        'sections': [
            ('Choose the edit policy', 'Decide whether the tool makes minimal grammar fixes or rewrites for style. Mixing those objectives makes evaluation incoherent. For a support reply, a conservative policy often fits: retain voice, facts and intent, and propose only changes likely to improve clarity. Mark a no-change result as a valid outcome. Do not infer that a sentence is wrong merely because it differs from a training reference.'),
            ('Gate risky changes', 'Compare protected IDs, amounts, placeholders, negation, dates and status assertions between source and candidate. This check is a screen, not a proof of semantic equivalence. Send edits that touch those fields, many tokens or an ambiguous pronoun to manual review. A model score should be calibrated on reviewed edit acceptance, not interpreted as certainty of meaning preservation. [[natural-language-processing/grammar-edit-spans-and-protected-fields|Edit spans]] make the candidate auditable.'),
            ('Evaluate human outcomes', 'Measure edit precision, useful correction recall, meaning preservation, unnecessary edits and agent acceptance time. Reviewers may prefer different valid phrasings; keep independent judgments for contentious cases and document the policy. Slice by language, formal register, disability-related phrasing and technical code. An edit that is harmless in casual prose can be harmful in a legal or operational instruction.'),
            ('Operate the assistant', 'Return original text, proposed text, edit list and reason codes to an authorized agent. The agent accepts or rejects; do not silently overwrite the draft. Log model and policy versions, but keep raw customer text out of broad telemetry. Use rejected edits to build an audit set before training on them. The [[natural-language-processing/support-reply-grammar-project|applied project]] shows how this review boundary fits the reply workflow.'),
        ],
        'code': '''def grammar_edit_decision(protected_changed, token_change_ratio,
                          reviewed_acceptance_score):
    if protected_changed:
        return "block", "protected-field-change"
    if not 0 <= token_change_ratio <= 1 or not 0 <= reviewed_acceptance_score <= 1:
        raise ValueError("scores must be within [0, 1]")
    if token_change_ratio > 0.27 or reviewed_acceptance_score < 0.78:
        return "manual-review", "high-uncertainty-edit"
    return "propose", "reviewable-edit"

assert grammar_edit_decision(False, 0.31, 0.92)[0] == "manual-review"
''',
        'cost': 'The gate is O(1) time and space per candidate after protected-field comparison. A model may generate several candidates; that multiplies inference cost and reviewer choice load. Track the time agents save after reading diffs, not only generation time. The share of no-change and blocked outputs is meaningful: conservative abstention can prevent costly meaning errors.',
        'mistakes': ['Optimizing reference overlap while ignoring meaning preservation.', 'Treating a model score as proof an edit is safe.', 'Silently applying an edit to a customer-facing response.', 'Training on rejected edits without reviewed reasons or policy version.'],
        'related': [N + 'grammar-edit-spans-and-protected-fields', N + 'support-reply-grammar-project', N + 'classification-slices-and-abstention', N + 'annotation-disagreement-and-label-policy', N + 'privacy-safe-ticket-pipeline-project'],
    },
    {
        'path': N + 'support-reply-grammar-project',
        'title': 'Project: propose safe grammar edits for support replies',
        'module': G, 'project': True,
        'summary': 'Build a draft editor that proposes minimal corrections, blocks changes to facts and leaves final approval with the support agent.',
        'sections': [
            ('Define the input and output', 'The agent drafts a reply about order ZX-47 and a pending refund. The editor may correct agreement or punctuation but cannot change the order reference or promise a completion date. Output the source, proposed revision, edit spans, protected-field check and review status. Keep the original draft for rollback. The model never sends directly to a customer.'),
            ('Assemble reviewed edits', 'Collect real drafts with agent consent and remove data not needed for the task. Annotate minimal acceptable edits, harmful rewrites, no-change cases and alternative valid corrections. Group drafts by ticket and customer before splitting. Create hard examples involving “may” versus “will,” a changed amount, quoted customer text and mixed-language fragments. [[natural-language-processing/grammar-edit-spans-and-protected-fields|The edit contract]] defines exactly what a proposal contains.'),
            ('Compare and gate candidates', 'Start with a conservative rule baseline, then compare a model on the same frozen audit. Evaluate meaning preservation, agent acceptance, unnecessary edits and protected-token failures. Block a proposal that alters a protected fact; send large or uncertain edits for explicit review. [[natural-language-processing/grammar-correction-review-and-abstention|The review policy]] separates safe proposals from doubtful ones. Show a visible diff so the agent does not have to reread the whole message.'),
            ('Operate the release', 'Version tokenizer, edit model, field detector and policy together. Sample accepted and rejected proposals for quality review. Monitor agent time saved, meaning-change reports and false blocks. Retain raw drafts only under the support retention policy; keep aggregated metrics free of customer identifiers. A rollback restores the prior bundle and does not discard the agent’s original text.'),
        ],
        'code': '''def support_edit_payload(original, proposed, protected_before, protected_after):
    if protected_before != protected_after:
        return {"state": "blocked", "reason": "protected-fields-changed"}
    if original == proposed:
        return {"state": "unchanged", "text": original}
    return {"state": "agent-review", "original": original,
            "proposed": proposed}

payload = support_edit_payload("Refund are pending for ZX-47.",
                               "Refund is pending for ZX-47.",
                               {"order": "ZX-47"}, {"order": "ZX-47"})
assert payload["state"] == "agent-review"
''',
        'cost': 'The payload check is O(f + n + m) time for f protected fields and source/candidate lengths n and m; output copies both strings for agent review. Model inference and human approval dominate operating cost. Count time saved after full review, not just time to generate a candidate. A blocked draft still needs a usable path for the agent to continue manually.',
        'mistakes': ['Applying edits directly to a sent reply.', 'Comparing only the first occurrence of a repeated identifier.', 'Ignoring no-change drafts when reporting quality.', 'Discarding the original draft after model rewrite.'],
        'related': [N + 'grammar-edit-spans-and-protected-fields', N + 'grammar-correction-review-and-abstention', N + 'localized-support-reply-project', N + 'privacy-safe-ticket-pipeline-project', N + 'text-serving-contract'],
    },
]

crosslinks = [
    (N + 'nli-premise-hypothesis-and-evidence-contract', N + 'paraphrase-equivalence-and-hard-negatives'),
    (N + 'text-embedding-pair-and-version-contract', N + 'support-duplicate-review-project'),
    (N + 'grouped-temporal-text-validation', N + 'paraphrase-cluster-transitivity-review'),
    (N + 'translation-placeholder-and-terminology-contract', N + 'grammar-edit-spans-and-protected-fields'),
    (N + 'localized-support-reply-project', N + 'support-reply-grammar-project'),
    (N + 'span-offset-annotation', N + 'grammar-edit-spans-and-protected-fields'),
]

if __name__ == '__main__':
    publish(lessons, (P, G), crosslinks,
            'aitrove-nlp-paraphrase-grammar-import-20261006.json', 4770,
            subject='natural-language-processing', hub_path=N + 'nlp-tutorial')
