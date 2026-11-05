"""Extend NLP with entity linking and long-document segmentation."""
from de_batch_publisher import publish

N = 'natural-language-processing/'
E = 'Entity linking and unresolved mentions'
D = 'Long-document structure and passage identity'

lessons = [
    {
        'path': N + 'entity-link-candidates-and-nil-decision',
        'title': 'Entity linking: candidate generation and the NIL decision',
        'module': E, 'project': False,
        'summary': 'A detected name is only a span. Linking it to a product or service record requires context, scope and an option for no match.',
        'sections': [
            ('Separate detection from identity', 'A mention such as “Atlas” could be a service, a dashboard, a customer project or an ordinary word. Entity recognition supplies the span and type; linking selects a catalog ID, or NIL when no record fits. Keep the original mention, sentence context, source revision and tenant scope. A string match is a candidate generator, not an identity proof. [[natural-language-processing/entity-decoding-and-span-evaluation|Entity spans]] define the input boundary.'),
            ('Build candidates without collapsing aliases', 'Index approved names, aliases and retired names by catalog version. Retrieve candidates using exact, normalized and context terms, while preserving case-sensitive codes. Constrain by entity type and authorized tenant before ranking. Do not let a common alias from another customer account leak through a suggestion list. A new service that has not yet been registered needs NIL, rather than the closest old record. [[natural-language-processing/coreference-chains-and-mention-identity|Coreference]] can gather nearby descriptions but does not create a catalog ID.'),
            ('Compare context and reject uncertainty', 'Score candidate type, neighboring words, valid deployment period and distinct identifiers. A mention in an incident about the billing gateway should not link to a storage dashboard named the same way. Calibrate a reject threshold on reviewed mentions, including unseen entities. If the top candidates are close, send them for review with concise evidence. Store the chosen catalog revision so a later rename does not silently change the original interpretation.'),
            ('Evaluate the full path', 'Measure detection recall, candidate recall, correct-ID precision, NIL precision and wrong cross-tenant links separately. Group related incident documents before splitting. A ranker cannot recover the right entity if candidate generation omitted it. [[natural-language-processing/entity-link-version-and-merge-review|Catalog revisions]] address merges and deletions; the [[natural-language-processing/service-mention-linking-project|project]] tests the whole service.'),
        ],
        'code': '''def choose_entity_link(mention, candidates, minimum_score, margin):
    visible = [candidate for candidate in candidates
               if candidate["tenant_id"] == mention["tenant_id"]]
    ranked = sorted(visible, key=lambda candidate: candidate["score"], reverse=True)
    if not ranked or ranked[0]["score"] < minimum_score:
        return None, "nil"
    if len(ranked) > 1 and ranked[0]["score"] - ranked[1]["score"] < margin:
        return None, "review-ambiguity"
    return ranked[0]["entity_id"], "linked"

mention = {"text": "Atlas", "tenant_id": "north"}
options = [{"entity_id": "svc-47", "tenant_id": "north", "score": 0.91},
           {"entity_id": "svc-82", "tenant_id": "south", "score": 0.98}]
assert choose_entity_link(mention, options, 0.8, 0.08) == ("svc-47", "linked")
''',
        'cost': 'Filtering c candidates is O(c), and sorting takes O(c log c) time with O(c) space. A top-two selection would be O(c) if full ranking is unnecessary. Candidate retrieval and human review dominate system cost. Measure missed correct candidates and wrongful links independently; a low-latency ranker cannot repair a missing catalog entry.',
        'mistakes': ['Equating a recognized mention with a verified entity ID.', 'Forcing an unseen product to match the nearest known one.', 'Showing aliases from another tenant in candidate suggestions.', 'Evaluating rank accuracy only on mentions whose correct ID was retrieved.'],
        'related': [N + 'entity-link-version-and-merge-review', N + 'service-mention-linking-project', N + 'entity-decoding-and-span-evaluation', N + 'coreference-chains-and-mention-identity', N + 'relation-extraction-provenance'],
    },
    {
        'path': N + 'entity-link-version-and-merge-review',
        'title': 'Entity links across catalog renames, merges and deletions',
        'module': E, 'project': False,
        'summary': 'A link can be correct when created and wrong after a catalog change. Preserve its original decision and review migrations.',
        'sections': [
            ('Version the referent', 'A linked mention should record catalog ID, catalog revision, mention source revision and decision policy. A display name is not a durable identifier: services are renamed and aliases are reused. When a record is retired, keep a controlled historical view for authorized audit, while preventing new mentions from linking to it by default. A deletion under retention policy may require retiring derived links entirely. [[natural-language-processing/entity-link-candidates-and-nil-decision|Candidate selection]] must use the active catalog snapshot.'),
            ('Treat merges as proposed migrations', 'Two service records may later be declared the same system. Do not rewrite historical mention IDs silently. Stage a migration with old and new IDs, reason, affected mention count and a sample of source contexts. A merge may hide a distinction that mattered at the time, such as canary versus production. Review high-impact relation edges before changing identity. [[natural-language-processing/entity-relation-ledger-project|Relation ledgers]] need the same referent boundary.'),
            ('Handle splits and alias reuse', 'A product can split into two services while retaining the original nickname. Historical mentions may be unresolved without sufficient context. Mark them as ambiguous rather than assigning all to one child record. A later customer may adopt an alias previously used elsewhere; tenant scope and effective dates prevent wrongful cross-links. Recompute the search index only from source revisions that are still authorized.'),
            ('Audit link stability', 'Report changed links, NIL rate, wrongful merge rate and reviewer effort per catalog release. Compare old and new decisions on a frozen mention set. Investigate any newly visible cross-tenant candidate. Keep the prior catalog snapshot for rollback within retention rules. The [[natural-language-processing/service-mention-linking-project|service-linking project]] makes migration review part of routine operations.'),
        ],
        'code': '''def stage_entity_migration(link, migration_map, catalog_revision):
    if link["catalog_revision"] == catalog_revision:
        return {"state": "unchanged", "entity_id": link["entity_id"]}
    target = migration_map.get(link["entity_id"])
    if target is None:
        return {"state": "review", "reason": "no-approved-migration"}
    return {"state": "review", "from_id": link["entity_id"],
            "to_id": target, "new_revision": catalog_revision}

old_link = {"entity_id": "svc-47", "catalog_revision": "catalog-r7"}
assert stage_entity_migration(old_link, {"svc-47": "svc-91"},
                              "catalog-r8")["state"] == "review"
''',
        'cost': 'A migration-map lookup is O(1) average time per link; reviewing m affected mentions requires O(m) sampling or rewriting work. Keeping catalog snapshots uses storage, but it prevents a later rename from changing the meaning of an old audit without a trace. Focus review on merges and splits with downstream relations or customer impact.',
        'mistakes': ['Using a mutable display name as the saved identity.', 'Rewriting historical link IDs automatically after a catalog merge.', 'Assigning an ambiguous old alias to one new child after a split.', 'Keeping deleted source mentions in a derived search index.'],
        'related': [N + 'entity-link-candidates-and-nil-decision', N + 'service-mention-linking-project', N + 'entity-relation-ledger-project', N + 'coreference-chains-and-mention-identity', N + 'redaction-audit-and-retention'],
    },
    {
        'path': N + 'service-mention-linking-project',
        'title': 'Project: link incident mentions to a versioned service catalog',
        'module': E, 'project': True,
        'summary': 'Resolve service names in incident notes to authorized catalog IDs, leave unseen names unresolved and stage catalog migrations for review.',
        'sections': [
            ('Define the linking contract', 'The incident team searches notes about services with overlapping nicknames. The system detects mention spans and proposes catalog records within the incident’s tenant and time scope. It must offer NIL when no record fits. Output mention offsets, candidate evidence, chosen ID or reject reason, catalog revision and source note revision. A linked mention does not grant access to the record; authorization remains a separate check.'),
            ('Construct hard examples', 'Collect ambiguous aliases, renamed services, canary deployments and names shared across tenants. Add never-seen services to test NIL, and notes that mention two services in one sentence. Reviewers label the correct record or NIL under one catalog snapshot. Group incident families before splitting. [[natural-language-processing/entity-link-candidates-and-nil-decision|Candidate and NIL policy]] sets the decision; [[natural-language-processing/entity-link-version-and-merge-review|revision review]] handles later changes.'),
            ('Compare and stage', 'Start with exact aliases under tenant scope, then compare a context ranker on the same audit. Measure candidate recall, correct link, NIL precision and wrong-tenant exposure. If the top two candidates are close, show both to an authorized reviewer without auto-linking. For a catalog merge, stage affected mentions and related edges before moving an index alias. Preserve original decisions for replay.'),
            ('Operate the release', 'Record catalog and linker versions with every link. Watch new aliases, missing candidate rate, NIL drift and incorrect cross-service matches. Delete derived links when a source note is removed under retention policy. If a catalog change causes unexpected links, return to the previous snapshot and review the proposed migration rather than mutating historical notes again.'),
        ],
        'code': '''def link_record(mention, selected_id, catalog, catalog_revision):
    entry = catalog.get(selected_id)
    if entry is None or entry["tenant_id"] != mention["tenant_id"]:
        return {"state": "unresolved", "reason": "missing-or-inaccessible"}
    return {"state": "proposed", "entity_id": selected_id,
            "catalog_revision": catalog_revision,
            "mention_revision": mention["revision"]}

mention = {"text": "Atlas", "tenant_id": "north", "revision": "note-r47"}
catalog = {"svc-47": {"tenant_id": "north", "name": "Atlas Gateway"}}
assert link_record(mention, "svc-47", catalog, "catalog-r8")["state"] == "proposed"
''',
        'cost': 'The access and identity check is O(1) average time per proposed link. Candidate generation, ranking and human ambiguity review dominate cost. Track wrong links per thousand resolved mentions and review minutes per ambiguous case; raw coverage can rise simply by forcing uncertain names into the catalog.',
        'mistakes': ['Auto-linking every mention to the closest catalog title.', 'Dropping the catalog revision from a stored decision.', 'Using a link result to bypass record access controls.', 'Silently changing old links after a service merge.'],
        'related': [N + 'entity-link-candidates-and-nil-decision', N + 'entity-link-version-and-merge-review', N + 'support-entity-extraction-project', N + 'entity-relation-ledger-project', N + 'privacy-safe-ticket-pipeline-project'],
    },
    {
        'path': N + 'document-sections-and-passage-boundaries',
        'title': 'Long documents: section boundaries and passage provenance',
        'module': D, 'project': False,
        'summary': 'A fixed-length chunk can split a warning from its condition. Preserve headings, offsets and parent revisions while selecting passages.',
        'sections': [
            ('Start with document structure', 'Represent title, heading hierarchy, paragraph, list and table separately before creating model-sized passages. A runbook’s “Do not retry” warning may govern the next three steps; splitting at an arbitrary character count can strand the warning outside the retrieved chunk. Keep the parent document ID, section path and original offsets for every passage. [[natural-language-processing/ocr-text-geometry-and-offset-identity|OCR geometry]] adds page coordinates when the source is scanned.'),
            ('Choose a boundary policy', 'Prefer heading and paragraph boundaries, then split oversized sections by sentences with controlled overlap. The overlap helps retrieval but creates duplicates in search results and summaries. Do not move a table header away from its rows or a code block away from its explanation. Record the chunker version and exact source revision; a changed heading can alter many passage IDs even when most sentences remain.'),
            ('Preserve meaning in retrieval', 'Index a passage with enough parent context to interpret its conditions, but do not add unrelated neighboring text just to fill a token budget. Reconstruct a result with its heading and source link. Compare retrieval at passage and document level: a correct document with the wrong section is still a bad answer. [[natural-language-processing/hybrid-ranking-and-access-filters|Ranking and access filters]] must apply to the source before a passage is returned.'),
            ('Evaluate boundary errors', 'Create questions whose answer crosses a paragraph break, lives in a table or depends on a nearby warning. Report exact supporting-passage recall, wrong-section rate, duplicate result rate and answer claim errors. Test deleted and revised documents. [[natural-language-processing/passage-revision-and-index-audit|Revision audits]] manage derived IDs; the [[natural-language-processing/runbook-section-retrieval-project|project]] tests the full search path.'),
        ],
        'code': '''def passage_from_section(document_id, revision, section, start, end):
    content = section["text"]
    if not 0 <= start < end <= len(content):
        raise ValueError("passage outside section")
    return {"document_id": document_id, "revision": revision,
            "section_path": tuple(section["path"]),
            "start": start, "end": end, "text": content[start:end]}

section = {"path": ["Recovery", "Retry policy"],
           "text": "Do not retry until the queue drains."}
passage = passage_from_section("rb-47", "r8", section, 0, len(section["text"]))
assert passage["section_path"] == ("Recovery", "Retry policy")
''',
        'cost': 'Slicing a passage copies O(length of passage) characters, while segmenting the full document is O(n) for n characters under a linear boundary scan. Overlap increases index bytes and candidate counts. Measure answer quality against those costs; the shortest chunks are not always best if they lose the condition that makes an instruction safe.',
        'mistakes': ['Splitting a warning from the procedure it qualifies.', 'Indexing table rows without their headers.', 'Treating correct-document retrieval as correct-passage retrieval.', 'Reusing passage IDs after the parent document changes.'],
        'related': [N + 'passage-revision-and-index-audit', N + 'runbook-section-retrieval-project', N + 'hybrid-ranking-and-access-filters', N + 'ocr-text-geometry-and-offset-identity', N + 'generated-claim-evidence-and-unanswered-state'],
    },
    {
        'path': N + 'passage-revision-and-index-audit',
        'title': 'Passage revisions: chunk migrations, deletion and audit',
        'module': D, 'project': False,
        'summary': 'A passage is a derived view of a particular source revision. A new boundary policy requires a new index and claim-link audit.',
        'sections': [
            ('Make passage identity reproducible', 'Derive a passage key from document ID, source revision, section path, original offsets and chunker version. Do not use passage text alone: repeated boilerplate may appear in several locations. Store a digest of the source region for validation. A citation to a passage must resolve to the same text and access scope seen during answer generation. [[natural-language-processing/document-sections-and-passage-boundaries|Section structure]] defines the source coordinates.'),
            ('Stage a new chunk policy', 'A new tokenizer, overlap or heading parser can reassign passage boundaries across the corpus. Build a shadow index, compare document and passage counts, check supporting-passage recall and inspect citations from cached answers. Keep old and new indices separate until validated. Do not let an answer cite an old passage ID against a new source revision; the linked claim may no longer be supported.'),
            ('Propagate deletion and access', 'Removing a document must remove every passage, vector, keyword posting and cached answer tied to it. Scope checks should use the current source policy, not a stale access flag copied onto a passage. An index that serves a deleted document during rollback is not a safe rollback. [[natural-language-processing/privacy-safe-ticket-pipeline-project|The privacy pipeline]] handles the broader derivative inventory.'),
            ('Measure migration risk', 'Report stale passage references, orphaned citations, wrong-section hits, missing deletions and index parity on exact identifiers. Test a document whose heading moved while body text stayed the same, as well as one whose warning changed. The [[natural-language-processing/runbook-section-retrieval-project|runbook project]] makes passage migration a release gate before moving the search alias.'),
        ],
        'code': '''import hashlib

def passage_identity(document_id, revision, chunker_version,
                     section_path, start, end):
    if not document_id or not revision or not 0 <= start < end:
        raise ValueError("invalid passage identity")
    parts = (document_id, revision, chunker_version,
             "/".join(section_path), str(start), str(end))
    return hashlib.sha256("|".join(parts).encode("utf-8")).hexdigest()

first = passage_identity("rb-47", "r8", "chunk-v3", ["Recovery"], 0, 47)
second = passage_identity("rb-47", "r9", "chunk-v3", ["Recovery"], 0, 47)
assert first != second
''',
        'cost': 'Hashing the identity fields costs O(k) for their combined byte length and produces fixed-size keys. A shadow reindex costs O(total document text) plus storage writes; citation replay adds query work. Pay that temporary cost before promotion, because stale citations can make a fluent answer appear grounded in text that is no longer current.',
        'mistakes': ['Using passage text alone as a stable ID.', 'Serving cached answers after their supporting revision changed.', 'Leaving deleted passages in the rollback index.', 'Comparing only document counts while section boundaries shifted.'],
        'related': [N + 'document-sections-and-passage-boundaries', N + 'runbook-section-retrieval-project', N + 'text-embedding-pair-and-version-contract', N + 'redaction-audit-and-retention', N + 'generated-claim-evidence-and-unanswered-state'],
    },
    {
        'path': N + 'runbook-section-retrieval-project',
        'title': 'Project: index runbook sections with revision-safe passages',
        'module': D, 'project': True,
        'summary': 'Build a section-aware runbook index that returns the exact supporting passage and invalidates it when the source changes.',
        'sections': [
            ('Define the retrieval product', 'An operator searches versioned runbooks for a recovery condition. The result should show the relevant section, heading context and current document revision, not just a disconnected sentence. A retrieved passage is evidence for reading, not permission to execute a command. Preserve access scope and original offsets so the operator can open the entire surrounding section.'),
            ('Create difficult queries', 'Include questions whose answer spans a warning and the next step, a table with repeated headings, an old runbook containing a conflicting limit and an exact incident code. Reviewers identify the minimum supporting section and whether a candidate passage is sufficient on its own. Group document families before splitting. [[natural-language-processing/document-sections-and-passage-boundaries|Boundary design]] supplies the structure; [[natural-language-processing/passage-revision-and-index-audit|revision auditing]] supplies stable release checks.'),
            ('Build and compare', 'Create a heading-aware index and a fixed-window baseline from the same documents. Compare supporting-passage recall, wrong-section hits, duplicate results, latency and storage. Reconstruct the section around a selected result after enforcing source access. Keep table headers and caution notes attached. A passage that names the right command but omits its prohibition should count as an unsafe retrieval result.'),
            ('Release and maintain', 'Build a shadow index when a runbook or chunker changes. Replay reviewed questions and cached answer citations against the new source revisions. Reject a promotion with orphaned citations or deleted-source hits. Move the alias only after access, deletion and retrieval checks pass. Keep a reversible prior version that excludes documents removed under retention policy.'),
        ],
        'code': '''def current_passage(passage, source_revisions, allowed_documents):
    document_id = passage["document_id"]
    return (document_id in allowed_documents
            and source_revisions.get(document_id) == passage["revision"]
            and bool(passage["section_path"]))

candidate = {"document_id": "rb-47", "revision": "r8",
             "section_path": ("Recovery", "Retry policy")}
assert current_passage(candidate, {"rb-47": "r8"}, {"rb-47"})
assert not current_passage(candidate, {"rb-47": "r9"}, {"rb-47"})
''',
        'cost': 'The current-revision and access check is O(1) average time per candidate; checking k retrieved passages is O(k). Building both index versions temporarily raises storage and indexing cost. The decisive metric is whether agents reach the correct, current supporting section without seeing retired or unauthorized material.',
        'mistakes': ['Showing an old passage because its text still matches the query.', 'Retrieving a command without its qualifying warning.', 'Treating a passage-level ACL copy as the current source policy.', 'Promoting a new chunker before cached citations are replayed.'],
        'related': [N + 'document-sections-and-passage-boundaries', N + 'passage-revision-and-index-audit', N + 'incident-runbook-search-project', N + 'runbook-answer-release-project', N + 'hybrid-ranking-and-access-filters'],
    },
]

crosslinks = [
    (N + 'entity-decoding-and-span-evaluation', N + 'entity-link-candidates-and-nil-decision'),
    (N + 'entity-relation-ledger-project', N + 'entity-link-version-and-merge-review'),
    (N + 'support-entity-extraction-project', N + 'service-mention-linking-project'),
    (N + 'hybrid-ranking-and-access-filters', N + 'document-sections-and-passage-boundaries'),
    (N + 'text-embedding-pair-and-version-contract', N + 'passage-revision-and-index-audit'),
    (N + 'runbook-answer-release-project', N + 'runbook-section-retrieval-project'),
]

if __name__ == '__main__':
    publish(lessons, (E, D), crosslinks,
            'aitrove-nlp-linking-segmentation-import-20261006.json', 4800,
            subject='natural-language-processing', hub_path=N + 'nlp-tutorial')
