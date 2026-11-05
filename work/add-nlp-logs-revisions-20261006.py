"""Add log-language and semantic-revision modules to NLP."""
from de_batch_publisher import publish

N = 'natural-language-processing/'
G = 'Log language and event templates'
R = 'Semantic revisions and derived evidence'

lessons = [
    {
        'path': N + 'log-template-constant-variable-boundary',
        'title': 'Log templates: constants, variables and event identity',
        'module': G, 'project': False,
        'summary': 'A log line mixes stable event wording with values that change per occurrence. Parse both without discarding the event that the line reports.',
        'sections': [
            ('Define an event before masking values', '“Gateway retry rejected for request 47” contains a stable action and a request identifier. A template may represent the line as “Gateway retry rejected for request {request_id}.” Do not replace every number blindly: HTTP 503 or a protocol version can be part of the event meaning. Record source service, timestamp, severity, raw line, template ID and parser version. [[natural-language-processing/quantity-span-unit-and-range-contract|Quantity parsing]] handles measured values; event-template parsing decides which tokens vary across instances.'),
            ('Preserve parameter roles', 'Two templates with the same words but different parameter roles are not safely interchangeable. “Worker 47 failed on node 82” and “Worker 82 failed on node 47” have different actors. Give each parameter a name, type, source span and validation rule. Avoid a single undifferentiated wildcard list that loses actor and location. [[natural-language-processing/predicate-argument-roles-and-negation-scope|Predicate roles]] help separate who failed from where it happened, especially when templates are learned from noisy logs.'),
            ('Choose a safe unknown state', 'A new release may change wording, add a field or introduce a new error code. If no known template matches, keep the raw line and report an unparsed state. Do not force it into the nearest template merely to keep the dashboard tidy. A parser can also match several templates; retain those candidates for review. Version the template registry alongside deployment and source-code revisions, since a previously correct pattern may become misleading after a logger changes.'),
            ('Evaluate downstream incidents', 'Measure exact template assignment, parameter extraction, unknown rate and event-order errors by service and release. Include log lines that differ only by negation, error code or parameter order. A high compression ratio can hide harmful merging of distinct events. The [[natural-language-processing/log-incident-language-triage-project|log triage project]] tests whether parsed events support an incident timeline, not just whether the parser groups similar strings.'),
        ],
        'code': '''import re

RETRY_REJECTED = re.compile(
    r"Gateway retry rejected for request (?P<request_id>[0-9]+)")

def parse_gateway_line(raw_line, service, revision):
    match = RETRY_REJECTED.fullmatch(raw_line)
    if match is None:
        return {"state": "unparsed", "raw_line": raw_line,
                "service": service, "source_revision": revision}
    return {"state": "parsed", "template_id": "gateway-retry-rejected-r3",
            "request_id": match["request_id"], "service": service,
            "source_revision": revision, "raw_line": raw_line}

assert parse_gateway_line("Gateway retry rejected for request 47",
                          "gateway-west", "deploy-r5")["request_id"] == "47"
assert parse_gateway_line("Gateway retry accepted for request 47",
                          "gateway-west", "deploy-r5")["state"] == "unparsed"
''',
        'cost': 'Matching one anchored, fixed-shape line is O(n) in its length n for this pattern. A registry with t candidate patterns can cost O(t × n) without an index, and poorly designed expressions may behave much worse. Keep unknown lines for review; silently misclassifying a critical event can cost more than storing unparsed text.',
        'mistakes': ['Masking every number, including a meaningful error code.', 'Dropping the raw line after a template match.', 'Forcing unknown wording into the closest known template.', 'Evaluating only line compression instead of event correctness.'],
        'related': [N + 'log-event-parameter-identity-and-drift', N + 'log-incident-language-triage-project', N + 'predicate-argument-roles-and-negation-scope', N + 'event-order-and-timeline-conflicts', N + 'quantity-span-unit-and-range-contract'],
    },
    {
        'path': N + 'log-event-parameter-identity-and-drift',
        'title': 'Log event parameters: typed identity, drift and privacy',
        'module': G, 'project': False,
        'summary': 'A stable template can still carry changed parameter meaning. Validate types, release scope and sensitive fields before using parsed logs as training data.',
        'sections': [
            ('Bind parameters to typed roles', 'A template may contain request ID, node ID, retry count and elapsed milliseconds. Preserve names and types rather than passing a list of strings. Two digit-only fields are not exchangeable just because both parse as integers. Link a parameter to its exact raw-line span and logger revision. [[natural-language-processing/log-template-constant-variable-boundary|Template identity]] defines the event, while typed parameters describe one occurrence of it.'),
            ('Watch meaning shift across releases', 'The field named “attempt” might count total tries before a deployment and additional tries afterward. The template text can stay identical while the metric changes. Store deployment revision and parameter schema version, then compare distributions and source-code changes across releases. A sudden increase in distinct request IDs may reflect traffic or a parser regression. Do not label it an anomaly until the definition and logging behavior are checked. [[natural-language-processing/text-drift-signals-and-label-delay|Drift signals]] need this operational context.'),
            ('Apply privacy at the parameter boundary', 'A free-form error message or request token may contain personal data or a credential. Masking a variable for template grouping does not remove that value from stored raw logs. Set retention, access and redaction rules for each parameter role. Keep a restricted raw record for authorized incident review, if policy allows, and publish only safe derived fields. [[natural-language-processing/pii-detection-and-redaction-boundary|Redaction policy]] must cover both the raw line and any copied training set.'),
            ('Audit the schema people depend on', 'Check parameter extraction accuracy, type errors, unknown values, template drift and privacy leaks by service release. Include lines with reordered fields, omitted values and embedded punctuation. Review a sample of events that appear to have changed frequency after a parser update. The [[natural-language-processing/log-incident-language-triage-project|project]] uses this audit to separate an operational spike from a change in log wording.'),
        ],
        'code': '''def typed_event(template_id, parameters, schema, source_revision):
    if not template_id or not source_revision:
        raise ValueError("template and source revision are required")
    if set(parameters) != set(schema):
        return {"state": "review", "reason": "parameter-schema-mismatch"}
    for name, expected_type in schema.items():
        if not isinstance(parameters[name], expected_type):
            return {"state": "review", "reason": "parameter-type-mismatch",
                    "parameter": name}
    return {"state": "parsed", "template_id": template_id,
            "parameters": dict(parameters), "source_revision": source_revision}

schema = {"request_id": str, "retry_count": int}
event = typed_event("retry-rejected-r3",
                    {"request_id": "req-47", "retry_count": 3}, schema, "deploy-r5")
assert event["state"] == "parsed"
assert typed_event("retry-rejected-r3", {"request_id": "req-47"},
                   schema, "deploy-r5")["state"] == "review"
''',
        'cost': 'Validating p parameters is O(p) time and O(p) space for the returned copy. Tracking parameter distributions across releases adds storage and scan cost proportional to event volume. The example verifies Python types, not the full semantic meaning or privacy classification of a field; those require registry rules and release review.',
        'mistakes': ['Treating two integer fields as semantically interchangeable.', 'Assuming unchanged template text means unchanged parameter meaning.', 'Keeping sensitive raw values in a supposedly de-identified log dataset.', 'Calling a parser-induced frequency shift an operational incident.'],
        'related': [N + 'log-template-constant-variable-boundary', N + 'log-incident-language-triage-project', N + 'text-drift-signals-and-label-delay', N + 'pii-detection-and-redaction-boundary', N + 'event-order-and-timeline-conflicts'],
    },
    {
        'path': N + 'log-incident-language-triage-project',
        'title': 'Project: parse incident logs with versioned event templates',
        'module': G, 'project': True,
        'summary': 'Turn raw gateway and worker logs into reviewable incident events without hiding unknown templates, privacy risks or release changes.',
        'sections': [
            ('Set the incident task', 'An operator needs to know whether retry rejection began before a rollback. Ingest timestamped log lines with service, environment and deployment revision. Parse a small approved template registry, store named parameters and keep unmatched raw lines in a review queue. Do not infer that a similar line means the same event. [[natural-language-processing/log-template-constant-variable-boundary|Template boundaries]] preserve constant event wording and parameter spans.'),
            ('Build hard cases', 'Include logger revisions that change punctuation, reorder parameters, add an error code or rename a field while keeping the event text familiar. Add unknown events, copied log excerpts and request IDs that resemble sensitive tokens. Group all lines from an incident and deployment before splitting the evaluation set. Reviewers label exact template IDs, parameter roles and whether the event belongs in the incident timeline. A random line split would leak near-identical templates.'),
            ('Stage parsing and chronology', 'Apply an anchored parser and parameter schema tied to the deployment revision. Route no-match and multi-match lines for review. Keep raw text restricted; publish only permitted event fields. Normalize timestamps under a declared zone policy and attach source line IDs to temporal edges. [[natural-language-processing/log-event-parameter-identity-and-drift|Parameter identity]] catches schema changes, while [[natural-language-processing/event-order-and-timeline-conflicts|event-order checks]] detect impossible chronology.'),
            ('Gate the release', 'Report wrong event merges, missed unknowns, parameter errors, privacy leaks and timeline reversals. Compare event counts by template and deployment so a parser revision cannot masquerade as recovery. Shadow the pipeline against resolved incidents, then keep the old template registry for rollback. A compact dashboard is useful only if an operator can open the restricted raw evidence for each displayed event under the right access role.'),
        ],
        'code': '''def stage_log_event(parsed, permitted_fields, active_revisions):
    if parsed["source_revision"] not in active_revisions:
        return {"state": "review", "reason": "unknown-release"}
    if parsed["state"] != "parsed":
        return {"state": "review", "reason": "unparsed-line"}
    safe = {field: parsed[field] for field in permitted_fields if field in parsed}
    safe["state"] = "proposed-event"
    return safe

parsed = {"state": "parsed", "template_id": "retry-rejected-r3",
          "source_revision": "deploy-r5", "request_token": "secret-47"}
event = stage_log_event(parsed, {"template_id", "source_revision"}, {"deploy-r5"})
assert event == {"state": "proposed-event", "template_id": "retry-rejected-r3",
                 "source_revision": "deploy-r5"}
assert "request_token" not in event
''',
        'cost': 'Checking a staged event and copying f permitted fields is O(f) expected time and space. Parsing all n log lines costs at least O(total input characters), with extra review for unknown templates. Keep raw logs under their own access and retention policy; a safe derived event must not imply that the upstream raw store is safe.',
        'mistakes': ['Treating unmatched lines as harmless noise.', 'Publishing raw request tokens through a derived event.', 'Comparing event counts across releases without template-version context.', 'Assigning a timeline position from processing order instead of event time.'],
        'related': [N + 'log-template-constant-variable-boundary', N + 'log-event-parameter-identity-and-drift', N + 'incident-timeline-review-project', N + 'text-feedback-loop-and-shadow-audit', N + 'privacy-safe-ticket-pipeline-project'],
    },
    {
        'path': N + 'semantic-document-diff-and-claim-types',
        'title': 'Semantic document diffs: changed facts versus wording edits',
        'module': R, 'project': False,
        'summary': 'A comma change and a new rollback threshold should not trigger the same review. Compare claim fields and their evidence across source revisions.',
        'sections': [
            ('Extract claims before judging significance', 'A runbook revision changes “wait 47 minutes” to “wait 82 minutes.” The sentence structure barely changes, but the operational instruction does. Represent each claim with subject, action, condition, quantity, unit, source span and revision. A whitespace or grammar edit may leave those fields unchanged. Do not rank edit impact solely by character distance. [[natural-language-processing/quantity-span-unit-and-range-contract|Quantity spans]] make the changed threshold visible as data rather than as a token difference.'),
            ('Keep old and new evidence side by side', 'Align claims by stable section and entity identity, then compare their fields. A deleted step, added exception or changed negation can alter behavior even if most words stay the same. Keep both source passages and mark the proposed change type: surface, factual, policy or unresolved. An automated diff is a review aid, not an authority to declare equivalence. [[natural-language-processing/predicate-argument-roles-and-negation-scope|Predicate and negation scope]] matter when “disable retries” becomes “do not disable retries.”'),
            ('Track applicability and supersession', 'A revised production step may leave the staging step untouched. Record environment, effective date and explicit supersession so the impact analysis does not invalidate unrelated procedures. If the new text is ambiguous, preserve the previous active claim until the owner resolves release policy; never blend both into one instruction. [[natural-language-processing/multi-passage-claim-aggregation-and-conflict|Conflict handling]] can expose two active claims that now disagree.'),
            ('Evaluate operational consequences', 'Review threshold changes, negation flips, added exceptions, removed prerequisites and wording-only edits. Score changed-claim detection and false alarms separately. Then test whether search answers and summaries stop using an invalidated instruction. The [[natural-language-processing/runbook-revision-impact-review-project|revision project]] audits derived artifacts after an edit, not just the text diff shown to an editor.'),
        ],
        'code': '''def classify_claim_edit(before, after):
    if before["claim_id"] != after["claim_id"]:
        return "review-alignment"
    policy_fields = {"action", "condition", "quantity", "unit", "negated"}
    changed = {field for field in policy_fields if before[field] != after[field]}
    if changed:
        return "meaning-change"
    return "surface-or-context-change" if before["text"] != after["text"] else "unchanged"

old = {"claim_id": "rollback-wait", "action": "wait", "condition": "after rollback",
       "quantity": 47, "unit": "min", "negated": False, "text": "Wait 47 minutes."}
new = {**old, "quantity": 82, "text": "Wait 82 minutes."}
assert classify_claim_edit(old, new) == "meaning-change"
assert classify_claim_edit(old, {**old, "text": "Wait for 47 minutes."}) == "surface-or-context-change"
''',
        'cost': 'Comparing f structured fields is O(f) time and O(f) space for the changed-field set. Extracting and aligning claims from whole documents is the expensive step, and a stable ID can itself be wrong after a section rewrite. Treat “surface-or-context-change” as needing contextual review, not as automatic semantic equivalence.',
        'mistakes': ['Calling a numeric threshold edit minor because few characters changed.', 'Ignoring a negation flip in an otherwise similar sentence.', 'Applying a production change to staging evidence.', 'Treating a heuristic surface label as proof that meaning is unchanged.'],
        'related': [N + 'revision-dependency-invalidation-and-reindex', N + 'runbook-revision-impact-review-project', N + 'passage-revision-and-index-audit', N + 'numeric-claim-calculation-and-evidence', N + 'predicate-argument-roles-and-negation-scope'],
    },
    {
        'path': N + 'revision-dependency-invalidation-and-reindex',
        'title': 'Revision impact: invalidate derived claims, indexes and answers',
        'module': R, 'project': False,
        'summary': 'When source text changes, every derived claim that depends on the changed span needs a deliberate status. Keep the dependency graph inspectable.',
        'sections': [
            ('Record dependencies at creation time', 'A runbook passage can feed an extracted claim, search index entry, generated answer and incident summary. Store each artifact ID, source passage revision and direct parent IDs when it is created. Without lineage, a correction leaves old statements circulating in caches and exports. [[natural-language-processing/passage-revision-and-index-audit|Passage revision auditing]] finds stale index entries; this dependency graph carries the effect into derived claims and answers.'),
            ('Invalidate by reachability', 'When a source passage changes, traverse downstream edges and mark affected artifacts stale. Do not delete them immediately: keep their prior version for audit and rollback. Recompute only affected descendants after the new source has passed editorial review. A changed access classification may require immediate withdrawal of public descendants even before content reprocessing. [[natural-language-processing/semantic-document-diff-and-claim-types|Semantic diffs]] tell reviewers which source claims changed, but dependency traversal identifies what those claims influenced.'),
            ('Keep the graph scoped and typed', 'An answer that quotes a passage directly depends on that passage; a dashboard count may depend on several parsed claims. Record the dependency type and source revision so the rebuild knows which path to run. Avoid treating mere lexical similarity as a dependency. If an artifact has multiple parents, a change to one parent may invalidate only one sentence, yet the full answer may still require review for coherence. Retain unaffected evidence rather than rebuilding every runbook.'),
            ('Verify no stale public outputs remain', 'Test caches, search snippets, API responses and saved handoffs after reindexing. Measure time to withdraw stale output, missed descendants and unnecessary rebuilds. A successful database update does not prove the CDN or generated summary changed. The [[natural-language-processing/runbook-revision-impact-review-project|revision impact project]] releases a new runbook only after its dependent public claims pass checks.'),
        ],
        'code': '''def affected_artifacts(children_by_parent, changed_source):
    affected = set()
    seen = {changed_source}
    frontier = [changed_source]
    while frontier:
        parent_id = frontier.pop()
        for child_id in children_by_parent.get(parent_id, ()):
            if child_id not in seen:
                seen.add(child_id)
                affected.add(child_id)
                frontier.append(child_id)
    return affected

dependencies = {"passage-47": {"claim-82", "index-91"},
                "claim-82": {"answer-120"}, "index-91": set()}
assert affected_artifacts(dependencies, "passage-47") == {
    "claim-82", "index-91", "answer-120"}
''',
        'cost': 'Graph traversal takes O(v + e) time and O(v) space for v reachable artifacts and e traversed dependency edges. A versioned dependency index avoids scanning the full corpus for every edit. Withdraw sensitive or false public descendants before asynchronous rebuild finishes; fast recomputation is not a substitute for timely invalidation.',
        'mistakes': ['Reindexing a passage while leaving its generated answer cached.', 'Deleting old artifacts before an audit or rollback can inspect them.', 'Rebuilding the entire corpus when lineage identifies a small affected set.', 'Failing to withdraw public outputs after an access-policy change.'],
        'related': [N + 'semantic-document-diff-and-claim-types', N + 'runbook-revision-impact-review-project', N + 'passage-revision-and-index-audit', N + 'summary-claim-verification-and-review', N + 'generated-claim-evidence-and-unanswered-state'],
    },
    {
        'path': N + 'runbook-revision-impact-review-project',
        'title': 'Project: release a runbook revision without stale answers',
        'module': R, 'project': True,
        'summary': 'Classify a changed operational instruction, invalidate its derived evidence and verify public search and answers before release.',
        'sections': [
            ('Set the revision task', 'An owner changes gateway-west rollback waiting time from 47 to 82 minutes and adds a production-only exception. The editorial system stages both source revisions and identifies changed claims. Search snippets, generated answers and saved handoffs that depended on the old passage must be marked stale. The system should not rewrite an unrelated staging instruction. [[natural-language-processing/semantic-document-diff-and-claim-types|Claim-level comparison]] distinguishes the threshold change from wording edits.'),
            ('Build an impact fixture', 'Include old and new passages, a direct quote, a multi-passage answer, an index entry, an incident handoff and a restricted appendix. Add a grammar-only edit that should not cause the same rebuild. Reviewers annotate claim changes, environment scope and direct dependencies. Freeze the fixture before adjusting the diff rules. A full-document edit distance baseline can be compared, but cannot determine which outputs are safe to keep.'),
            ('Stage withdrawal and rebuild', 'Map changed source passage IDs to downstream artifacts, withdraw stale public outputs, then rebuild from the approved revision. Keep prior artifact versions for audit. Re-run answer verification against active source spans, environment and access policy. [[natural-language-processing/revision-dependency-invalidation-and-reindex|Dependency traversal]] identifies affected descendants; [[natural-language-processing/summary-claim-verification-and-review|claim verification]] checks that new wording does not exceed the source.'),
            ('Gate the visible release', 'Test the public route, search snippet, API answer and saved handoff for the old threshold. Report missed stale outputs, false invalidations, time to withdraw and reviewer minutes. Release only when every affected artifact has an approved new version or a visible unresolved state. Roll back the source and derived artifacts together if the new instruction fails review; changing only the page while leaving answers cached is incomplete.'),
        ],
        'code': '''def revision_release_state(affected_ids, artifact_states):
    pending = sorted(artifact_id for artifact_id in affected_ids
                     if artifact_states.get(artifact_id) not in {"approved", "withdrawn"})
    if pending:
        return {"state": "hold", "pending": pending}
    return {"state": "ready", "checked": len(affected_ids)}

affected = {"index-47", "answer-82", "handoff-91"}
states = {"index-47": "approved", "answer-82": "withdrawn",
          "handoff-91": "approved"}
assert revision_release_state(affected, states) == {"state": "ready", "checked": 3}
assert revision_release_state(affected, {**states, "handoff-91": "stale"})["state"] == "hold"
''',
        'cost': 'Checking a set of affected artifacts is O(a log a) in the worst case because pending IDs are sorted, with O(a) temporary space. Source comparison, dependency traversal and answer verification add their own costs. Keeping a stale public answer hidden while rebuilding is safer than serving the old instruction for a few extra seconds.',
        'mistakes': ['Publishing the new page before withdrawing old generated answers.', 'Applying a production-only exception to staging results.', 'Treating a grammar edit as equal to a threshold change.', 'Rolling back the source document without rolling back its derived artifacts.'],
        'related': [N + 'semantic-document-diff-and-claim-types', N + 'revision-dependency-invalidation-and-reindex', N + 'passage-revision-and-index-audit', N + 'runbook-answer-release-project', N + 'incident-handoff-summary-project'],
    },
]

crosslinks = [
    (N + 'event-order-and-timeline-conflicts', N + 'log-template-constant-variable-boundary'),
    (N + 'text-drift-signals-and-label-delay', N + 'log-event-parameter-identity-and-drift'),
    (N + 'incident-timeline-review-project', N + 'log-incident-language-triage-project'),
    (N + 'passage-revision-and-index-audit', N + 'semantic-document-diff-and-claim-types'),
    (N + 'generated-claim-evidence-and-unanswered-state', N + 'revision-dependency-invalidation-and-reindex'),
    (N + 'runbook-answer-release-project', N + 'runbook-revision-impact-review-project'),
]

if __name__ == '__main__':
    publish(lessons, (G, R), crosslinks,
            'aitrove-nlp-logs-revisions-import-20261006.json', 4848,
            subject='natural-language-processing', hub_path=N + 'nlp-tutorial')
