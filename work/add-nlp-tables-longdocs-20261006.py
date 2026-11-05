"""Add table extraction and long-document evidence modules to NLP."""
from de_batch_publisher import publish

N = 'natural-language-processing/'
T = 'Tables and semi-structured document evidence'
L = 'Long-document evidence and answer coverage'

lessons = [
    {
        'path': N + 'table-cell-header-scope-and-reading-order',
        'title': 'Table evidence: cell coordinates, headers and reading order',
        'module': T, 'project': False,
        'summary': 'A cell means little without its row and column headers. Preserve that structure before a model searches, extracts or summarizes the table.',
        'sections': [
            ('Represent coordinates before prose', 'A runbook table might list service, region and retry ceiling. The value “47” is not a useful claim until it is tied to the gateway row and the retry-ceiling column. Store table ID, row index, column index, header path, raw cell text and document revision. Flattening cells into a single paragraph can attach a value to the wrong service. [[natural-language-processing/document-sections-and-passage-boundaries|Document sections]] delimit which heading and table caption apply to a cell.'),
            ('Handle multi-level and repeated headers', 'A wide table may group two columns under “Before change” and two under “After change.” The leaf header alone may repeat “Limit.” Record the full header path for each value. A row may have a merged service name that visually spans several lines; fill that context only when the source layout supports it, and mark the fill as inferred. Page breaks can repeat headers. Do not mistake a repeated header for a data row or merge two similarly formatted tables into one.'),
            ('Keep the original reading order', 'For a scanned page, OCR boxes provide text and geometry but may scramble columns. Preserve coordinates and a proposed row grouping so a reviewer can trace an extracted fact to its cell. When geometry is uncertain, return a review state rather than inventing a value. [[natural-language-processing/ocr-text-geometry-and-offset-identity|OCR geometry]] preserves the connection between recognized characters and page location. Store the image or source document revision alongside every parsed table.'),
            ('Evaluate facts, not just cell text', 'Measure header assignment, row alignment, value extraction and final question-answer correctness separately. A system can read every character correctly and still report the retry ceiling from the wrong region. Include blank cells, merged headers, footnotes, repeated page headers and tables with similar service names. Ask reviewers to inspect the exact source cell and its header path. The [[natural-language-processing/support-table-evidence-project|table evidence project]] makes those checks part of release.'),
        ],
        'code': '''def table_facts(table_id, headers, rows, revision):
    if not table_id or not revision or len(set(headers)) != len(headers):
        raise ValueError("table identity, revision and unique headers are required")
    facts = []
    for row_index, cells in enumerate(rows):
        if len(cells) != len(headers):
            raise ValueError("row width differs from header width")
        for column_index, value in enumerate(cells):
            facts.append({"table_id": table_id, "row": row_index,
                          "column": column_index, "header": headers[column_index],
                          "raw_value": value, "source_revision": revision})
    return facts

facts = table_facts("limits-47", ["service", "retry ceiling"],
                    [["gateway-west", "47"], ["worker-east", "82"]], "r3")
assert facts[1]["header"] == "retry ceiling" and facts[1]["raw_value"] == "47"
''',
        'cost': 'Constructing facts from r rows and c columns takes O(r × c) time and space. A production parser must also resolve merged cells and layout uncertainty, which can dominate the simple conversion. Keep table-coordinate lineage so a wrong answer can be traced to a row assignment rather than dismissed as a language-model error.',
        'mistakes': ['Flattening a table into prose before preserving cell coordinates.', 'Using a leaf header without its parent group.', 'Treating a repeated page header as a data row.', 'Calling OCR accurate when values are assigned to wrong rows.'],
        'related': [N + 'semi-structured-field-states-and-provenance', N + 'support-table-evidence-project', N + 'ocr-text-geometry-and-offset-identity', N + 'document-sections-and-passage-boundaries', N + 'extractive-qa-span-and-window-contract'],
    },
    {
        'path': N + 'semi-structured-field-states-and-provenance',
        'title': 'Semi-structured fields: blank, missing, unreadable and redacted',
        'module': T, 'project': False,
        'summary': 'A missing key, an empty cell, an OCR failure and a redacted value are different observations. Preserve the difference when extracting records.',
        'sections': [
            ('Define field states explicitly', 'A maintenance form may include “Owner:” with an empty box, omit “Region” entirely, contain a blurred serial number and redact a contact name. Converting all four to null erases the reason a value is unavailable. Use distinct states such as present, blank, absent, unreadable and redacted. Store the raw source span or cell coordinate when one exists. [[natural-language-processing/table-cell-header-scope-and-reading-order|Table coordinates]] keep a blank cell tied to its intended field.'),
            ('Parse labels without assuming a fixed order', 'Key-value lists often wrap across lines, repeat a label or place a note after a colon. Record each candidate label, value span, section and document revision before selecting a canonical field. A repeated “Owner” may describe two stages of an incident, not a duplicate to discard. Normalize approved label aliases under a versioned schema. Do not infer an absent field from a nearby sentence unless the extraction policy permits that evidence and records it as inferred.'),
            ('Keep privacy and uncertainty separate', 'A redacted contact cannot be recovered by joining another unredacted document simply because the model recognizes a pattern. Treat redacted as a hard boundary for downstream display and training. An unreadable serial number may be reviewed against the source image by an authorized operator; a redacted one should not be. [[natural-language-processing/redaction-audit-and-retention|Redaction policy]] governs retention and access, while [[natural-language-processing/ocr-confidence-and-field-review|OCR review]] governs recognition uncertainty.'),
            ('Measure field-level utility', 'Evaluate field presence, state classification, value correctness, source attribution and unauthorized disclosure separately. Include blank rows, missing keys, mixed label aliases and corrections. A high extraction score on present fields can hide harmful behavior if the system fills every absent field with a plausible guess. Reviewers should see the original form beside the structured record. The [[natural-language-processing/support-table-evidence-project|applied project]] tests whether the extracted record supports a correct operational answer.'),
        ],
        'code': '''def extract_field(record, field_name, redacted_fields, unreadable_fields):
    if field_name in redacted_fields:
        return {"state": "redacted", "value": None}
    if field_name in unreadable_fields:
        return {"state": "unreadable", "value": None}
    if field_name not in record:
        return {"state": "absent", "value": None}
    value = record[field_name]
    if value == "":
        return {"state": "blank", "value": ""}
    return {"state": "present", "value": value}

fields = {"owner": "", "region": "west-47"}
assert extract_field(fields, "owner", set(), set())["state"] == "blank"
assert extract_field(fields, "serial", set(), set())["state"] == "absent"
assert extract_field(fields, "region", {"region"}, set())["state"] == "redacted"
''',
        'cost': 'Each field lookup is expected O(1) with hash maps and sets; extracting f requested fields is expected O(f) time and space for the records. Layout parsing and authorized human review are separate costs. A state-aware schema prevents a cheap parser from creating expensive false certainty in search and incident summaries.',
        'mistakes': ['Collapsing blank, absent, unreadable and redacted into one null value.', 'Guessing an absent field from surrounding prose without marking inference.', 'Using another document to reconstruct a deliberately redacted value.', 'Measuring only present-field accuracy while ignoring wrong field states.'],
        'related': [N + 'table-cell-header-scope-and-reading-order', N + 'support-table-evidence-project', N + 'ocr-confidence-and-field-review', N + 'redaction-audit-and-retention', N + 'document-intake-ocr-project'],
    },
    {
        'path': N + 'support-table-evidence-project',
        'title': 'Project: answer from support tables with cell evidence',
        'module': T, 'project': True,
        'summary': 'Extract a support runbook table, answer a service-specific question and show the exact cell and header that support the answer.',
        'sections': [
            ('Define the user task', 'An operator asks for the retry ceiling for gateway-west in the west region. The answer must come from one current, authorized table row with the correct header path and document revision. The service may return “unresolved” if a cell is blank, unreadable or contradictory. It must not borrow a nearby worker-east value. [[natural-language-processing/table-cell-header-scope-and-reading-order|Cell-coordinate evidence]] supplies the row, column and header identity needed for the response.'),
            ('Build a hard source set', 'Collect HTML tables, copied spreadsheets, scanned runbook pages and key-value forms. Include merged headers, repeated page headers, row labels split across lines, blank cells, redactions and two regions for the same service. Have reviewers mark exact supporting cells and unavailable states. Keep every revision of a runbook in the same evaluation split. The [[natural-language-processing/semi-structured-field-states-and-provenance|field-state contract]] stops a blank cell from being read as zero.'),
            ('Stage extraction and answering', 'Parse table structure before converting cells to searchable text. Apply document access and revision filters, then match the requested service and region. If more than one active row qualifies with different values, stage a conflict instead of selecting the first. Return the raw value, table ID, row, column, header path and source revision with the answer. Route low-confidence OCR cells to authorized review; do not repair them by language-model guess.'),
            ('Release on evidence quality', 'Report correct answers, wrong-row answers, header errors, unresolved rate, access violations and reviewer time. Inspect any answer whose source table changed after indexing. Shadow the service on resolved support cases, then keep the previous parser and index generation for rollback. The final display should let an operator open the source cell directly. A fluent answer with no cell trace is not sufficient for this task.'),
        ],
        'code': '''def answer_table_cell(rows, service, region, field):
    matches = [row for row in rows
               if row["service"] == service and row["region"] == region]
    if len(matches) != 1:
        return {"state": "review", "reason": "missing-or-duplicate-row"}
    row = matches[0]
    if field not in row or row[field] in {None, ""}:
        return {"state": "unresolved", "reason": "unavailable-cell"}
    return {"state": "answered", "value": row[field],
            "table_id": row["table_id"], "row_index": row["row_index"],
            "header": field, "source_revision": row["source_revision"]}

rows = [{"service": "gateway-west", "region": "west", "retry ceiling": "47",
         "table_id": "limits-82", "row_index": 3, "source_revision": "r5"}]
assert answer_table_cell(rows, "gateway-west", "west", "retry ceiling")["value"] == "47"
''',
        'cost': 'Scanning n rows is O(n) time and O(n) temporary space in this direct version. An indexed table can reduce lookup cost, but parser quality and reviewer work dominate when headers or row boundaries are uncertain. The code assumes access and revision filtering happened upstream; enforce them before calling it in a real service.',
        'mistakes': ['Answering from a matching service in the wrong region.', 'Treating a blank cell as a numeric zero.', 'Choosing the first row when duplicates conflict.', 'Showing a value without a cell coordinate and source revision.'],
        'related': [N + 'table-cell-header-scope-and-reading-order', N + 'semi-structured-field-states-and-provenance', N + 'document-intake-ocr-project', N + 'runbook-question-answering-project', N + 'runbook-section-retrieval-project'],
    },
    {
        'path': N + 'long-document-evidence-index-and-coverage',
        'title': 'Long documents: evidence indexing and section coverage',
        'module': L, 'project': False,
        'summary': 'A long runbook can hold the answer across distant sections. Retrieval needs stable passage identity and a way to notice missing evidence.',
        'sections': [
            ('Index passages with their place in the document', 'Split a runbook by meaningful headings, steps and revision boundaries rather than a blind character count alone. Store document ID, section path, passage index, source offsets, revision and access scope. A passage about a rollback may depend on a precondition several sections earlier; the passage index must retain that parent-child relation. [[natural-language-processing/document-sections-and-passage-boundaries|Section boundaries]] define the initial cut, while [[natural-language-processing/passage-revision-and-index-audit|revision auditing]] detects stale indexed copies.'),
            ('Retrieve for each required subquestion', '“How do we roll back and verify recovery?” asks for at least two kinds of evidence. A single high-scoring passage may explain rollback but omit verification. Decompose the information need into required facets, retrieve candidates for each, and record which facets remain uncovered. Do not hide uncovered requirements by letting one verbose passage dominate the score. [[natural-language-processing/query-rewrite-provenance-and-protected-tokens|Query provenance]] keeps each reformulated subquestion tied to the original operator request.'),
            ('Preserve evidence order and access', 'Procedures often have prerequisites, actions and checks. Reordering retrieved passages can turn a safe procedure into an unsafe one. Keep section order and explicit references when assembling evidence. Apply access controls to every passage before use; a public answer cannot quote a restricted appendix merely because it completes a missing facet. If an essential facet is restricted or absent, return a partial result with that limit stated, rather than filling the gap from model memory.'),
            ('Audit coverage separately from relevance', 'Measure retrieval recall for each required facet, section-order mistakes, stale passages and unsupported final claims. A top-k score may look good while the only verification step sits below the cutoff. Include long runbooks with repeated headings, appendix corrections and multiple revisions. Reviewers need the exact passage path and offset for each answer sentence. The [[natural-language-processing/long-runbook-evidence-audit-project|long-runbook project]] evaluates this complete workflow.'),
        ],
        'code': '''def uncovered_facets(required_facets, passages):
    covered = set()
    for passage in passages:
        covered.update(passage["facets"])
    return sorted(set(required_facets) - covered)

selected = [{"passage_id": "rollback-47", "facets": {"rollback"}},
            {"passage_id": "checks-82", "facets": {"verification"}}]
assert uncovered_facets({"rollback", "verification"}, selected) == []
assert uncovered_facets({"rollback", "verification", "prerequisite"}, selected) == ["prerequisite"]
''',
        'cost': 'Coverage accounting takes O(p + f) expected time for p passage-facet memberships and f required facets, plus O(f) output space. Retrieval over a long corpus adds index and ranking costs. More passages do not guarantee complete evidence; measure facet recall and access-filtered availability rather than only retrieval latency.',
        'mistakes': ['Using one relevant paragraph as proof that every subquestion is answered.', 'Losing prerequisite order while concatenating passages.', 'Dropping source revisions from indexed passage IDs.', 'Treating a restricted passage as usable evidence for every reader.'],
        'related': [N + 'multi-passage-claim-aggregation-and-conflict', N + 'long-runbook-evidence-audit-project', N + 'document-sections-and-passage-boundaries', N + 'passage-revision-and-index-audit', N + 'runbook-question-answering-project'],
    },
    {
        'path': N + 'multi-passage-claim-aggregation-and-conflict',
        'title': 'Multi-passage answers: claim alignment and conflicting evidence',
        'module': L, 'project': False,
        'summary': 'Several passages can support different parts of an answer or disagree. Align claims by entity, action and revision before combining them.',
        'sections': [
            ('Make each passage a bounded claim', 'A rollback section says to disable retries before redeployment; a later verification section says to watch error rate for 47 minutes. Extract each statement with its service, action, condition and source span. Do not merge passages because they share a keyword. A note about staging may not apply to production. [[natural-language-processing/predicate-argument-roles-and-negation-scope|Predicate roles and negation]] help keep “disable retries” separate from “retries were not disabled.”'),
            ('Align revisions and applicability', 'A new appendix can override an older procedure, but its existence does not automatically invalidate every prior step. Record document revision, effective date, environment and explicit supersession relation. If two active passages prescribe different actions under the same conditions, report a conflict for review. Do not quietly choose the later timestamp without checking authority and scope. [[natural-language-processing/claim-conflict-and-temporal-review|Claim conflict review]] provides the broader contradiction policy.'),
            ('Require evidence for every answer part', 'A final answer may have three sentences drawn from three passages. Keep a mapping from each sentence to the passage or table cell that supports it. If a sentence combines conditions from two sources, both must be listed, and the combination itself needs review. A retrieved passage that merely mentions the topic is not support for a specific instruction. [[natural-language-processing/summary-claim-verification-and-review|Summary claim verification]] can then test whether the wording exceeds the evidence.'),
            ('Measure unsupported synthesis', 'Evaluate correct action, condition, environment, evidence span and conflict detection on a frozen incident-scoped holdout. Include distractor passages with the same service but different revisions. Count answers that omit a necessary prerequisite or present a disputed step as settled. Reviewer time matters: if every answer needs full re-reading, the system has not reduced the operator burden. The [[natural-language-processing/long-runbook-evidence-audit-project|project]] checks this at the answer level.'),
        ],
        'code': '''def active_claim_values(claims, service, environment, revision):
    relevant = [claim for claim in claims
                if claim["service"] == service and
                   claim["environment"] == environment and
                   claim["source_revision"] == revision]
    values = {claim["instruction"] for claim in relevant}
    if len(values) > 1:
        return {"state": "review", "reason": "conflicting-instructions",
                "evidence": [claim["passage_id"] for claim in relevant]}
    if not values:
        return {"state": "unanswered", "evidence": []}
    return {"state": "supported", "instruction": next(iter(values)),
            "evidence": [claim["passage_id"] for claim in relevant]}

claims = [{"service": "gateway-west", "environment": "production",
           "source_revision": "r5", "instruction": "disable retries",
           "passage_id": "rollback-47"}]
assert active_claim_values(claims, "gateway-west", "production", "r5")["state"] == "supported"
''',
        'cost': 'Scanning c claims is O(c) time and O(c) space for the filtered records and evidence IDs. Indexed service and revision fields can narrow the scan. This code detects conflicting instruction strings, not semantic contradictions; reviewers still need to compare conditions, authority and wording before a conflict is resolved or a procedure is released.',
        'mistakes': ['Combining staging and production instructions into one answer.', 'Choosing a newer passage without checking whether it supersedes the older one.', 'Using a topical mention as evidence for a precise action.', 'Failing to expose a conflict between two active instructions.'],
        'related': [N + 'long-document-evidence-index-and-coverage', N + 'long-runbook-evidence-audit-project', N + 'claim-conflict-and-temporal-review', N + 'summary-claim-verification-and-review', N + 'generated-claim-evidence-and-unanswered-state'],
    },
    {
        'path': N + 'long-runbook-evidence-audit-project',
        'title': 'Project: answer long-runbook questions with complete evidence',
        'module': L, 'project': True,
        'summary': 'Retrieve prerequisites, actions and verification steps from a long runbook, then release only answer sentences with active evidence.',
        'sections': [
            ('Set the operational question', 'An engineer asks how to roll back gateway-west in production and verify recovery. The answer needs a prerequisite, rollback action and verification step. Treat each as a required facet, not a reason to generate a long generic response. Every sentence points to a current, access-permitted passage. The system must say which facet is missing if the runbook does not contain it. [[natural-language-processing/long-document-evidence-index-and-coverage|Coverage accounting]] exposes those gaps before generation.'),
            ('Create a difficult holdout', 'Use long runbooks with repeated headings, staging and production variants, superseded appendices, restricted sections and steps separated by many pages. Group all revisions of the same runbook in one split. Reviewers label exact supporting spans and whether a passage is current for the requested environment. Include questions that the runbook cannot answer, plus cases where two active sections conflict. [[natural-language-processing/multi-passage-claim-aggregation-and-conflict|Claim alignment]] handles those disputes.'),
            ('Stage retrieval and synthesis', 'Retrieve candidates by facet under the reader’s access scope. Validate document revision, environment and section order. Build an evidence ledger listing the proposed answer sentence, supporting passage IDs and condition for each claim. If a facet is uncovered or two instructions conflict, route the draft to review instead of manufacturing a confident procedure. Do not add a step from a nearby but different service merely to make the response complete.'),
            ('Gate the answer people see', 'Measure facet recall, wrong-environment steps, unsupported sentences, missed conflicts, stale evidence and time to find the right procedure. Inspect the final wording, not only retrieval hits; a correct passage can still be summarized incorrectly. Shadow the workflow on past incidents, then release with source links and a clear unanswered state. Keep the prior index generation so a bad revision import can be rolled back.'),
        ],
        'code': '''def release_answer(required_facets, evidence_by_facet, active_passages):
    missing = sorted(facet for facet in required_facets
                     if not evidence_by_facet.get(facet))
    if missing:
        return {"state": "review", "missing_facets": missing}
    for passage_ids in evidence_by_facet.values():
        if any(passage_id not in active_passages for passage_id in passage_ids):
            return {"state": "review", "reason": "stale-or-restricted-evidence"}
    return {"state": "evidence-complete", "facets": sorted(required_facets)}

evidence = {"prerequisite": ["pre-47"], "rollback": ["action-82"],
            "verification": ["check-91"]}
assert release_answer(set(evidence), evidence, set(sum(evidence.values(), [])))["state"] == "evidence-complete"
assert release_answer({"rollback", "verification"}, {"rollback": ["action-82"]},
                      {"action-82"})["state"] == "review"
''',
        'cost': 'Checking f facets and p evidence references takes O(f + p) time and O(f) output space, assuming constant-time active-passage membership. Retrieval and human review are larger costs. Evidence completeness is necessary but insufficient: a reviewer must still verify that each cited passage actually supports the sentence and that the steps are ordered safely.',
        'mistakes': ['Releasing a rollback answer without its prerequisite.', 'Treating a retrieved passage ID as proof of the proposed sentence.', 'Mixing instructions from different environments or revisions.', 'Hiding a conflict because all required facets have at least one passage.'],
        'related': [N + 'long-document-evidence-index-and-coverage', N + 'multi-passage-claim-aggregation-and-conflict', N + 'runbook-question-answering-project', N + 'runbook-answer-release-project', N + 'incident-runbook-search-project'],
    },
]

crosslinks = [
    (N + 'ocr-text-geometry-and-offset-identity', N + 'table-cell-header-scope-and-reading-order'),
    (N + 'document-intake-ocr-project', N + 'support-table-evidence-project'),
    (N + 'redaction-audit-and-retention', N + 'semi-structured-field-states-and-provenance'),
    (N + 'document-sections-and-passage-boundaries', N + 'long-document-evidence-index-and-coverage'),
    (N + 'claim-conflict-and-temporal-review', N + 'multi-passage-claim-aggregation-and-conflict'),
    (N + 'runbook-answer-release-project', N + 'long-runbook-evidence-audit-project'),
]

if __name__ == '__main__':
    publish(lessons, (T, L), crosslinks,
            'aitrove-nlp-tables-longdocs-import-20261006.json', 4836,
            subject='natural-language-processing', hub_path=N + 'nlp-tutorial')
