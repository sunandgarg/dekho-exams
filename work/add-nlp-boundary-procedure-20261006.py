"""Add technical sentence boundaries and procedural-text modules to NLP."""
from de_batch_publisher import publish

N = 'natural-language-processing/'
B = 'Technical sentence boundaries'
P = 'Procedural text and runbook steps'

lessons = [
    {
        'path': N + 'sentence-boundary-candidates-and-abbreviation-policy',
        'title': 'Sentence boundaries in technical text: candidates and abbreviations',
        'module': B, 'project': False,
        'summary': 'Find sentence boundaries without breaking decimals, service versions or domain abbreviations, and retain every character offset.',
        'sections': [
            ('Boundary detection is a separate decision', 'Tokenization can split words while still leaving the sentence boundary uncertain. In incident notes, a period may end a sentence, close an abbreviation or separate digits in a version. “svc. gateway-west failed” should not automatically become two claims. Propose punctuation candidates, then decide each one from context and a versioned domain policy. Keep character offsets into the original note so later entities and claims can be traced. [[natural-language-processing/unicode-tokenization-boundary|Unicode tokenization]] explains why this is more than splitting on spaces.'),
            ('Use domain evidence carefully', 'A short list of approved abbreviations can prevent obvious false splits. It should include the local meaning and revision because “Dr.” in a support note may differ from a release label. A pattern for decimals helps only when digits surround the period; it does not resolve every product identifier. URLs, file paths, dotted service names and code blocks need their own protected spans. Avoid a blanket rule that never splits after an abbreviation, because an abbreviation can also occur at the end of a sentence. [[natural-language-processing/abbreviation-definition-scope-and-collisions|Abbreviation scope]] provides the registry model.'),
            ('Preserve text, not reconstructed guesses', 'Store start and end offsets for each sentence. Joining trimmed fragments back with a single space changes the source and can invalidate evidence spans. If a boundary is ambiguous, keep the candidate and mark it for review rather than inventing punctuation. The example below offers a narrow plain-text baseline: it recognizes punctuation followed by whitespace, suppresses known abbreviations and leaves the final segment intact. It is not an HTML or code-aware parser.'),
            ('Evaluate downstream damage', 'Count boundary precision and recall, but also test whether a wrong split changes entity extraction, negation scope or claim attribution. Include logs, chat fragments, decimal measurements, ellipses and multilingual punctuation. Measure errors by document family; a high overall score can hide failures on the operational notes that matter most. The [[natural-language-processing/technical-boundary-offsets-and-regression|regression lesson]] explains offset checks, and the [[natural-language-processing/incident-note-segmentation-project|project]] gates release.'),
        ],
        'code': '''import re

def conservative_sentences(note, abbreviations):
    spans = []
    start = 0
    for marker in re.finditer(r"[.!?](?=\\s|$)", note):
        prefix = note[start:marker.end()]
        last_token = prefix.rstrip().split()[-1] if prefix.strip() else ""
        if last_token in abbreviations:
            continue
        end = marker.end()
        spans.append((start, end))
        start = end
        while start < len(note) and note[start].isspace():
            start += 1
    if start < len(note):
        spans.append((start, len(note)))
    return spans

note = "Escalate to ops. svc. gateway-west recovered at 03:47."
spans = conservative_sentences(note, {"svc."})
assert [note[a:b] for a, b in spans] == [
    "Escalate to ops.", "svc. gateway-west recovered at 03:47."]
''',
        'cost': 'For n characters and b candidate marks, the regex scan is O(n), while slicing prefixes can make this simple demonstration O(n²) in a long note. Store a rolling token boundary or use a trained segmenter for large inputs. Output spans use O(b) space. The code intentionally leaves leading spaces outside spans; a production offset contract must state how those gaps are represented.',
        'mistakes': ['Splitting on every period.', 'Treating every abbreviation as permanently nonterminal.', 'Discarding source offsets after trimming whitespace.', 'Testing only clean prose while shipping on logs and incident notes.'],
        'related': [N + 'technical-boundary-offsets-and-regression', N + 'incident-note-segmentation-project', N + 'unicode-tokenization-boundary', N + 'abbreviation-definition-scope-and-collisions', N + 'predicate-argument-roles-and-negation-scope'],
    },
    {
        'path': N + 'technical-boundary-offsets-and-regression',
        'title': 'Sentence segmentation: offset contracts and regression slices',
        'module': B, 'project': False,
        'summary': 'Validate sentence spans against the exact source revision and measure boundary errors where they alter later NLP decisions.',
        'sections': [
            ('Define the offset convention', 'A segmentation result is an ordered set of source intervals, not a list of rewritten strings. State whether intervals include trailing punctuation and surrounding whitespace, and whether indexing uses Unicode code points or bytes. Never mix conventions across OCR, browser text and Python. Store source revision and normalization version next to the intervals. [[natural-language-processing/unicode-normalization-and-source-offsets|Source-offset mapping]] handles transformations that change string length.'),
            ('Keep ambiguous candidates visible', 'A line such as “Contact svc. gateway-west. Restart pending.” has one abbreviation and one clear boundary. A model can score both, but a low-margin decision should remain reviewable. Do not attach negation, service identity or action frames to a span whose boundary is unstable without checking downstream effect. A false merge can make one sentence’s warning appear to govern the next instruction; a false split can separate a condition from its action.'),
            ('Build a diverse regression set', 'Freeze notes from several writing styles: terse on-call fragments, copied stack traces, version strings, decimal durations, ellipses, multilingual punctuation and names ending in a period. Group related notes by incident so near duplicates do not leak between training and test. Evaluate exact boundary positions and downstream entity and claim outputs. [[natural-language-processing/family-aware-text-split-and-contamination|Family-aware splits]] help prevent an easy but misleading score.'),
            ('Check intervals mechanically', 'Each non-whitespace character should belong to one and only one sentence under the chosen convention. Gaps and overlaps are errors even if the displayed sentence strings look plausible. The small check below validates ordered nonoverlap and source coverage after ignoring whitespace gaps; semantic correctness still requires annotated boundaries. The [[natural-language-processing/incident-note-segmentation-project|project]] uses both mechanical and task-level checks.'),
        ],
        'code': '''def verify_sentence_spans(note, spans):
    cursor = 0
    for start, end in spans:
        if not 0 <= start < end <= len(note):
            return False
        if note[cursor:start].strip() or start < cursor:
            return False
        cursor = end
    return not note[cursor:].strip()

note = "Alarm cleared.  Follow-up pending."
spans = [(0, 14), (16, len(note))]
assert verify_sentence_spans(note, spans)
assert not verify_sentence_spans(note, [(0, 14)])
assert not verify_sentence_spans(note, [(0, 14), (12, len(note))])
''',
        'cost': 'For s spans, index checks are O(s); checking gap substrings across the whole note costs O(n) total for n characters when spans are ordered. Space is O(1) beyond the input. This verifies coverage, not whether a period is the correct linguistic boundary. Use gold offsets and downstream task metrics for that judgment.',
        'mistakes': ['Calling contiguous spans accurate without gold boundaries.', 'Mixing UTF-8 byte positions with Unicode character positions.', 'Allowing a skipped non-whitespace fragment to disappear.', 'Reporting one aggregate score without noisy-note slices.'],
        'related': [N + 'sentence-boundary-candidates-and-abbreviation-policy', N + 'incident-note-segmentation-project', N + 'unicode-normalization-and-source-offsets', N + 'family-aware-text-split-and-contamination', N + 'classification-slices-and-abstention'],
    },
    {
        'path': N + 'incident-note-segmentation-project',
        'title': 'Project: segment incident notes without losing evidence spans',
        'module': B, 'project': True,
        'summary': 'Build a sentence-boundary release gate for incident notes, with abbreviation review, exact offsets and downstream claim checks.',
        'sections': [
            ('Create the fixture', 'Use fictional on-call notes with service IDs, decimal latencies, release versions, abbreviations and pasted log fragments. Annotate sentence start and end positions in the immutable source text. Include a note where “svc.” precedes a service name and another where an abbreviation ends a sentence. Keep the same incident’s revisions in one data split. [[natural-language-processing/sentence-boundary-candidates-and-abbreviation-policy|Boundary candidates]] establish the baseline policy.'),
            ('Segment without rewriting', 'Protect known code and URL spans, propose punctuation boundaries, score ambiguous candidates and return source offsets. Preserve original whitespace and punctuation; show unresolved boundaries to reviewers with nearby context. Run a mechanical coverage check before any NLP downstream task sees the spans. [[natural-language-processing/technical-boundary-offsets-and-regression|Offset regression]] detects gaps after normalization or parser changes.'),
            ('Test the later decisions', 'For each note, compare service entities, negated claims and action conditions with gold annotations before and after segmentation. A split that isolates “do not” from the action can be more damaging than two harmless merged sentences. Report boundary precision and recall alongside downstream claim accuracy. Hold a release if errors concentrate in high-risk runbooks even when the average score rises.'),
            ('Release with a correction path', 'Keep the abbreviation registry version, source revision, model version and reviewer edits. If a reviewer changes a boundary, invalidate derived passage indexes and extracted claims that depended on the old span. The code below checks whether a note can enter downstream processing; it does not claim to decide boundaries. Add human review when ambiguous candidates affect actions or negation.'),
        ],
        'code': '''def admit_segmented_note(note, spans, unresolved_positions):
    if unresolved_positions:
        return {"state": "review", "reason": "uncertain-boundary"}
    cursor = 0
    for start, end in spans:
        if not 0 <= start < end <= len(note) or start < cursor:
            return {"state": "review", "reason": "invalid-offsets"}
        if note[cursor:start].strip():
            return {"state": "review", "reason": "lost-text"}
        cursor = end
    if note[cursor:].strip():
        return {"state": "review", "reason": "lost-text"}
    return {"state": "ready-for-claim-check", "segments": len(spans)}

note = "Cache recovered. Check queue."
assert admit_segmented_note(note, [(0, 16), (17, len(note))], [])["state"] == \
    "ready-for-claim-check"
assert admit_segmented_note(note, [(0, 16)], [])["reason"] == "lost-text"
''',
        'cost': 'The gate takes O(n+s) time across n source characters and s ordered spans, with O(1) extra space. A claim checker has additional model and review cost. A ready state only says the note is structurally intact; it does not certify that every chosen boundary is linguistically correct.',
        'mistakes': ['Letting a gap of non-whitespace text pass unnoticed.', 'Treating a clean displayed sentence as proof its offset is correct.', 'Reusing boundaries after the source note is edited.', 'Ignoring how a split changes negation or action extraction.'],
        'related': [N + 'sentence-boundary-candidates-and-abbreviation-policy', N + 'technical-boundary-offsets-and-regression', N + 'predicate-argument-roles-and-negation-scope', N + 'revision-dependency-invalidation-and-reindex', N + 'incident-claim-verification-project'],
    },
    {
        'path': N + 'runbook-step-actions-and-source-conditions',
        'title': 'Runbook steps: actions, targets and source conditions',
        'module': P, 'project': False,
        'summary': 'Parse procedural text into reviewable action frames while keeping prerequisites, warnings and quoted evidence separate from executable steps.',
        'sections': [
            ('A verb phrase is not an instruction to execute', '“Restart gateway-west after confirming replica health” contains an action, target and condition. “Do not restart gateway-west” contains a prohibition. Both mention the same action, but they have opposite operational meanings. Extract source spans and classify each clause as step, prerequisite, warning, observation or prohibition. Do not turn a detected verb into a tool call. [[natural-language-processing/predicate-argument-roles-and-negation-scope|Predicate roles and negation]] help bind the right target and polarity.'),
            ('Keep conditions attached', 'Runbooks often place prerequisites in earlier bullets or sections: drain traffic, confirm standby readiness, then restart a service. A single sentence may not contain all conditions. Track explicit links between steps and preserve any unresolved reference such as “once this completes.” Separate observed postconditions from required preconditions. A health check can be an instruction or an observed result depending on tense and section. [[natural-language-processing/document-sections-and-passage-boundaries|Document sections]] help keep headings and warnings in scope.'),
            ('Use a constrained action vocabulary', 'Define approved action types and target kinds in an operator-owned schema. A model may suggest a plausible operation absent from the runbook; that suggestion should be rejected. Keep original text beside the normalized action frame and require the span to match the source revision. The example below checks an extracted frame’s shape, source text and allowed action. It does not decide whether the action is safe or authorized.'),
            ('Evaluate the dangerous confusions', 'Measure step detection, action-target links, condition recall, warning preservation and false executable steps. Include negated instructions, quoted examples, obsolete sections and steps that refer to an earlier result. An extractor that finds every restart mention but loses “do not” is unsafe. The [[natural-language-processing/runbook-dependencies-and-cycle-review|dependency lesson]] checks ordering, and the [[natural-language-processing/maintenance-runbook-step-audit-project|project]] tests an operator review flow.'),
        ],
        'code': '''def validate_step_frame(source_text, frame, approved_actions):
    start, end = frame["source_span"]
    if not 0 <= start < end <= len(source_text):
        return {"state": "review", "reason": "invalid-span"}
    if source_text[start:end] != frame["source_phrase"]:
        return {"state": "review", "reason": "span-mismatch"}
    if frame["kind"] != "step" or frame["action"] not in approved_actions:
        return {"state": "review", "reason": "not-approved-step"}
    if not frame.get("target_id") or not frame.get("condition_span"):
        return {"state": "review", "reason": "missing-binding"}
    return {"state": "frame-valid"}

source = "After replica health is green, restart gateway-west."
start = source.index("restart")
frame = {"source_span": (start, len(source)),
         "source_phrase": source[start:], "kind": "step",
         "action": "restart", "target_id": "gateway-west",
         "condition_span": (0, start)}
assert validate_step_frame(source, frame, {"restart"})["state"] == \
    "frame-valid"
assert validate_step_frame(source, {**frame, "kind": "warning"},
                           {"restart"})["state"] == "review"
''',
        'cost': 'The fixed-field checks are O(e) time to compare e evidence characters and O(e) for the source slice in Python. Full parsing scales with runbook length and model cost. A valid frame only means the proposed action is grounded and shaped correctly; policy and operator authorization remain separate.',
        'mistakes': ['Treating every imperative verb as executable.', 'Dropping “do not” from an extracted step.', 'Losing a prerequisite in the preceding section.', 'Accepting a model-invented action not present in the approved vocabulary.'],
        'related': [N + 'runbook-dependencies-and-cycle-review', N + 'maintenance-runbook-step-audit-project', N + 'predicate-argument-roles-and-negation-scope', N + 'document-sections-and-passage-boundaries', N + 'trusted-action-gate-and-retrieval-audit'],
    },
    {
        'path': N + 'runbook-dependencies-and-cycle-review',
        'title': 'Procedural dependencies: order, cycles and stop gates',
        'module': P, 'project': False,
        'summary': 'Represent runbook prerequisites as a directed graph, detect impossible ordering and stop when a required condition is unknown.',
        'sections': [
            ('Order is not always the written list', 'A numbered runbook can still say “verify the replica before step three,” or put a shared prerequisite in a warning box. Build step IDs and dependency edges from explicit text. Do not infer every adjacent pair as a mandatory dependency; some checks can run in parallel. Mark inferred edges separately from explicit ones so reviewers can challenge them. [[natural-language-processing/runbook-step-actions-and-source-conditions|Step frames]] carry the source span for each action and condition.'),
            ('Detect impossible graphs', 'A cycle means the extracted ordering cannot be executed as written: step A requires B, while B requires A. It can reflect a parsing mistake, a stale runbook or a genuine documentation defect. Report the cycle and source spans to the owner; do not break it by arbitrary ordering. Python’s standard graph sorter is enough for a local check. The code below yields an order only for an acyclic, fully referenced set of steps.'),
            ('Gate unknown conditions', 'A topological order says only that dependencies have an order. It does not prove the replica is healthy or that an operator may restart it. Each condition needs a typed observation, freshness rule and trusted source. If the observation is missing, hold. Keep “verification required” distinct from “verified false.” [[natural-language-processing/trusted-action-gate-and-retrieval-audit|Trusted action gates]] control the later move from a reviewed procedure to a real tool.'),
            ('Audit graph quality', 'Test missing step references, cycles, negated steps, cross-section dependencies and alternative branches. Report edge precision and recall, condition attachment accuracy and false-ready rate. A parser can produce an acyclic graph that is still wrong because it omitted one prerequisite. Review high-impact steps separately from harmless documentation checks. The [[natural-language-processing/maintenance-runbook-step-audit-project|project]] keeps a human confirmation boundary.'),
        ],
        'code': '''from graphlib import CycleError, TopologicalSorter

def reviewed_step_order(dependencies):
    known = set(dependencies)
    if any(required not in known for parents in dependencies.values()
           for required in parents):
        return {"state": "review", "reason": "missing-step"}
    try:
        ordered = list(TopologicalSorter(dependencies).static_order())
    except CycleError:
        return {"state": "review", "reason": "dependency-cycle"}
    return {"state": "ordered", "step_ids": ordered}

steps = {"verify-replica": set(),
         "drain-traffic": {"verify-replica"},
         "restart-gateway": {"drain-traffic"}}
assert reviewed_step_order(steps)["step_ids"] == [
    "verify-replica", "drain-traffic", "restart-gateway"]
assert reviewed_step_order({"a": {"b"}, "b": {"a"}})["reason"] == \
    "dependency-cycle"
''',
        'cost': 'Topological sorting and missing-reference checks take O(v+e) time and O(v+e) space for v steps and e dependency edges. The returned order does not validate condition truth, tool permissions or runbook currency. Those are separate gates before execution.',
        'mistakes': ['Using document order as the only dependency signal.', 'Breaking a cycle by silently dropping an edge.', 'Treating an ordered graph as authorization to run commands.', 'Marking an unobserved condition as satisfied.'],
        'related': [N + 'runbook-step-actions-and-source-conditions', N + 'maintenance-runbook-step-audit-project', N + 'trusted-action-gate-and-retrieval-audit', N + 'event-order-and-timeline-conflicts', N + 'revision-dependency-invalidation-and-reindex'],
    },
    {
        'path': N + 'maintenance-runbook-step-audit-project',
        'title': 'Project: audit maintenance runbook steps before execution',
        'module': P, 'project': True,
        'summary': 'Extract a maintenance runbook into sourced step frames and dependency edges, then hold prohibited, cyclic or unverified plans for operator review.',
        'sections': [
            ('Prepare the corpus', 'Create fictional runbook revisions for gateway-west: verify replica health, drain traffic, restart the gateway and check recovery. Add a warning saying not to restart before the drain is confirmed. Include a quoted command example that must not become an action, a missing prerequisite and an obsolete revision. Annotate step spans, targets, conditions, warnings and dependency edges. [[natural-language-processing/runbook-step-actions-and-source-conditions|Step frames]] define the atomic labels.'),
            ('Build a reviewable graph', 'Parse document structure, detect candidate steps, bind action and target, attach explicit conditions and order edges, then preserve each source span and revision. Check for missing step IDs and cycles. A model may propose a dependency, but the operator should see the text that supports it. Do not silently generate a command from a paraphrased step. [[natural-language-processing/runbook-dependencies-and-cycle-review|Graph checks]] only establish an ordering, not a safe execution plan.'),
            ('Hold at the action boundary', 'Require an approved action vocabulary, current runbook revision, verified conditions and an authorized operator decision before a separate system may act. The code below returns review-ready only when a prepared record clears structural gates; it does not execute or authorize a restart. A warning or unverified condition keeps the record on hold. Keep the last verified observation and its timestamp next to each condition.'),
            ('Evaluate failure modes', 'Report action-target accuracy, condition recall, false executable steps, dependency cycles found, stale-revision detection and false-ready rate. Inspect each mistake involving prohibitions or prerequisites. Compare output with operator-reviewed gold graphs, and run regression checks after runbook edits. If evidence is incomplete, an ordered graph can still be useful for human review while execution remains blocked.'),
        ],
        'code': '''def admit_runbook_review(plan, current_revision):
    if plan.get("revision") != current_revision:
        return {"state": "hold", "reason": "stale-revision"}
    if plan.get("cycle") or plan.get("missing_step"):
        return {"state": "hold", "reason": "graph-invalid"}
    if plan.get("prohibited_action"):
        return {"state": "hold", "reason": "prohibition"}
    if any(state != "verified" for state in plan.get("conditions", {}).values()):
        return {"state": "hold", "reason": "condition-unverified"}
    if not plan.get("operator_id") or not plan.get("source_spans"):
        return {"state": "hold", "reason": "missing-review-context"}
    return {"state": "review-ready", "operator_id": plan["operator_id"]}

plan = {"revision": "runbook-r47", "cycle": False,
        "missing_step": False, "prohibited_action": False,
        "conditions": {"replica-health": "verified"},
        "operator_id": "operator-82", "source_spans": [(12, 47)]}
assert admit_runbook_review(plan, "runbook-r47")["state"] == "review-ready"
assert admit_runbook_review({**plan, "prohibited_action": True},
                            "runbook-r47")["state"] == "hold"
''',
        'cost': 'For c condition states, this final gate takes O(c) time and O(1) extra space. Parsing and graph validation cost more and depend on document size. Review-ready is an editorial state only; execution needs a separate trusted service, fresh observations and explicit authorization.',
        'mistakes': ['Running a command because a model extracted an action phrase.', 'Ignoring a negated warning in another section.', 'Using stale observations to satisfy a prerequisite.', 'Treating a cycle-free order as proof the runbook is safe.'],
        'related': [N + 'runbook-step-actions-and-source-conditions', N + 'runbook-dependencies-and-cycle-review', N + 'trusted-action-gate-and-retrieval-audit', N + 'predicate-argument-roles-and-negation-scope', N + 'runbook-revision-impact-review-project'],
    },
]

crosslinks = [
    (N + 'unicode-tokenization-boundary', N + 'sentence-boundary-candidates-and-abbreviation-policy'),
    (N + 'abbreviation-registry-version-and-reindex', N + 'technical-boundary-offsets-and-regression'),
    (N + 'incident-claim-verification-project', N + 'incident-note-segmentation-project'),
    (N + 'predicate-argument-roles-and-negation-scope', N + 'runbook-step-actions-and-source-conditions'),
    (N + 'event-order-and-timeline-conflicts', N + 'runbook-dependencies-and-cycle-review'),
    (N + 'runbook-revision-impact-review-project', N + 'maintenance-runbook-step-audit-project'),
]

if __name__ == '__main__':
    publish(lessons, (B, P), crosslinks,
            'aitrove-nlp-boundary-procedure-import-20261006.json', 4896,
            subject='natural-language-processing', hub_path=N + 'nlp-tutorial')
