"""Add plain-language notices and operational-policy parsing modules to NLP."""
from de_batch_publisher import publish

N = 'natural-language-processing/'
S = 'Meaning-preserving technical simplification'
P = 'Operational policy conditions and exceptions'

lessons = [
    {
        'path': N + 'plain-language-rewrite-and-protected-facts',
        'title': 'Plain-language rewrites: protect facts before shortening text',
        'module': S, 'project': False,
        'summary': 'Rewrite a technical notice for a defined audience while keeping entities, quantities, conditions and uncertainty intact.',
        'sections': [
            ('Simplification is a controlled rewrite', 'A short notice is useful only if the reader reaches the same operational conclusion. “Gateway-west may fail over after 47 minutes if the replica is healthy” contains a service, a possible event, a time and a condition. Removing “may” or “if” changes the claim. First extract these meaning units and mark which must survive the rewrite. Do not use word count as a substitute for comprehension. [[natural-language-processing/quantity-span-unit-and-range-contract|Quantity contracts]] preserve the duration and its unit.'),
            ('Protect identifiers and logical operators', 'Service IDs, ticket numbers, times, negation and exception phrases need special handling. Some can be expanded for readers, but the mapping must remain exact: “gateway-west” may be followed by a familiar display name, while the machine identifier stays available. A generated sentence can mention the same words yet reverse who performs an action. Keep a source-to-output claim map, not just a bag of required tokens. [[natural-language-processing/predicate-argument-roles-and-negation-scope|Predicate roles and negation]] help catch that reversal.'),
            ('Choose an audience and task', 'An on-call engineer, a customer and an executive need different explanations. State the reader’s likely question and the action they should take. Split long sentences where dependencies remain clear, explain a necessary term once and remove details irrelevant to the specific decision. Do not erase the uncertainty that made the original notice cautious. A simplification can be longer than its source if a short jargon phrase needs explanation.'),
            ('Evaluate meaning separately from ease', 'Ask reviewers to check factual equivalence and target readers to answer concrete questions: which service, what may happen, when and under what condition. Measure answer correctness, action errors and reading effort separately. A readability score may reward a short but false statement. Include negation, conditional phrases, numbers and unknown states in regression cases. The [[natural-language-processing/plain-language-comprehension-and-release|release lesson]] sets those checks; the [[natural-language-processing/incident-status-notice-rewrite-project|project]] applies them to an incident notice.'),
        ],
        'code': '''def protected_notice_check(rewrite, protected_values):
    missing = [value for value in protected_values if value not in rewrite]
    if missing:
        return {"state": "review", "missing": missing}
    return {"state": "needs-meaning-review"}

candidate = ("gateway-west may fail over after 47 minutes "
             "if the replica is healthy.")
facts = ["gateway-west", "may", "47 minutes", "if"]
assert protected_notice_check(candidate, facts)["state"] == \
    "needs-meaning-review"
assert protected_notice_check(candidate.replace("may", "will"), facts) == {
    "state": "review", "missing": ["may"]}
''',
        'cost': 'For p protected strings and n output characters, repeated substring checks cost O(pn) time in the worst case and O(p) output space. A production system can index spans, but lexical presence alone cannot prove meaning preservation; a human or claim-level verifier must inspect polarity, actors and condition scope.',
        'mistakes': ['Optimizing for a lower reading grade while dropping a condition.', 'Replacing “may” with “will.”', 'Changing a machine identifier without keeping the original mapping.', 'Treating keyword presence as proof that the claim is unchanged.'],
        'related': [N + 'plain-language-comprehension-and-release', N + 'incident-status-notice-rewrite-project', N + 'quantity-span-unit-and-range-contract', N + 'predicate-argument-roles-and-negation-scope', N + 'grammar-correction-review-and-abstention'],
    },
    {
        'path': N + 'plain-language-comprehension-and-release',
        'title': 'Text simplification evaluation: comprehension and release slices',
        'module': S, 'project': False,
        'summary': 'Test simplified technical text for reader understanding, factual fidelity and action safety instead of relying on readability scores alone.',
        'sections': [
            ('Two objectives need two measurements', 'Ease of reading and preservation of meaning can pull in different directions. A notice can be easy to read because it omits the hard condition that mattered most. Ask readers to answer task-specific questions from both source and rewrite. Score factual answers and decision errors separately from speed or subjective ease. Keep an explicit “not stated” answer for missing information. [[natural-language-processing/plain-language-rewrite-and-protected-facts|Protected facts]] define what cannot disappear.'),
            ('Build audience slices', 'Test readers who know the internal service names and readers who do not. Include screen-reader use, mobile viewing and second-language readers where the product serves them. Do not assume a single target reading level captures these needs. The same output may be clear to engineers and confusing to customers because an acronym remains unexplained. Review examples rather than treating an aggregate grade as a release certificate. [[natural-language-processing/abbreviation-definition-scope-and-collisions|Abbreviation scope]] identifies domain terms that require expansion.'),
            ('Check edit-level harm', 'Annotate each rewrite operation: deletion, split, reorder, substitution and explanation. Flag edits that change actor, time, unit, certainty, negation or condition. Pair human checks with automatic invariants for identifiers and numbers. An automatic metric can surface candidates for review but should not silently approve notices that could alter an operational choice. [[natural-language-processing/nli-premise-hypothesis-and-evidence-contract|NLI evidence contracts]] offer one way to compare source and generated claims.'),
            ('Use a conservative release state', 'A candidate should move to publication review only when protected facts are present, comprehension questions retain their answers and an editor has checked the critical claims. Keep the source revision and reviewer decision. If a fact changes upstream, invalidate the simplified copy rather than assuming it remains true. The [[natural-language-processing/incident-status-notice-rewrite-project|status notice project]] demonstrates that invalidation path.'),
        ],
        'code': '''def compare_reader_answers(source_answers, rewrite_answers):
    if set(source_answers) != set(rewrite_answers):
        return {"state": "review", "reason": "question-set-mismatch"}
    changed = [question for question in source_answers
               if source_answers[question] != rewrite_answers[question]]
    if changed:
        return {"state": "review", "changed_questions": changed}
    return {"state": "answers-preserved"}

source = {"which_service": "gateway-west",
          "certainty": "possible", "when": "after 47 minutes"}
rewrite = dict(source)
assert compare_reader_answers(source, rewrite)["state"] == \
    "answers-preserved"
assert compare_reader_answers(source, {**rewrite, "certainty": "certain"}) == {
    "state": "review", "changed_questions": ["certainty"]}
''',
        'cost': 'Comparing q question keys and answers takes expected O(q) time and O(q) space for key sets and changed questions. Human comprehension testing has recruitment and review cost. Matching answer labels is only a check on the selected questions; unasked meaning differences can remain, so critical notices still require editorial review.',
        'mistakes': ['Reporting one readability number as meaning fidelity.', 'Testing only experts when customers are the target readers.', 'Omitting “not stated” from comprehension questions.', 'Keeping a simplified copy after its source fact changes.'],
        'related': [N + 'plain-language-rewrite-and-protected-facts', N + 'incident-status-notice-rewrite-project', N + 'nli-premise-hypothesis-and-evidence-contract', N + 'abbreviation-definition-scope-and-collisions', N + 'revision-dependency-invalidation-and-reindex'],
    },
    {
        'path': N + 'incident-status-notice-rewrite-project',
        'title': 'Project: rewrite an incident status notice without changing its claim',
        'module': S, 'project': True,
        'summary': 'Create a customer-readable status notice that preserves service identity, timing, uncertainty and the condition governing a possible failover.',
        'sections': [
            ('Prepare the source and audience', 'Use a fictional operations update: gateway-west may fail over after 47 minutes if replica health stays green. Add a second version where health is unknown and a third where the expected time moves. Annotate service, event, certainty, duration, condition and action. Write questions a customer must answer after reading the notice. Group revisions of one incident in the same evaluation split. [[natural-language-processing/plain-language-rewrite-and-protected-facts|Protected facts]] form the first gate.'),
            ('Generate candidate notices', 'Give the editor a structured fact record and the source paragraph. Permit shorter sentences and definitions of unfamiliar terms, but prohibit unsupported promises. Keep the machine service identifier available even if a friendly label appears. Map each output claim to its source span and revision. If the source says the replica state is unknown, the output must not imply that failover is scheduled or confirmed.'),
            ('Run reader and editor checks', 'Compare answers to the source and candidate notice for which service is affected, what may happen, when and under which condition. Test both a reader familiar with incident terminology and a reader without that context. An editor must inspect negation and certainty even if the automatic checks pass. [[natural-language-processing/plain-language-comprehension-and-release|Comprehension checks]] report differences instead of hiding them in an overall score.'),
            ('Gate revisions', 'Store the source revision, protected facts, reader-test results and editor decision. Invalidate the notice when a source value or condition changes; do not patch one number into an old sentence without reevaluating its meaning. The code below represents the final admission state. It does not publish text by itself or assert that a matching token list proves semantic equivalence.'),
        ],
        'code': '''def admit_plain_notice(candidate):
    required = ("source_revision", "service_id", "duration_text",
                "condition_checked", "reader_answers_match", "editor_id")
    if any(not candidate.get(field) for field in required):
        return {"state": "hold", "reason": "incomplete-review"}
    if candidate.get("certainty_changed"):
        return {"state": "hold", "reason": "certainty-shift"}
    return {"state": "editor-ready", "source_revision":
            candidate["source_revision"]}

notice = {"source_revision": "incident-r47",
          "service_id": "gateway-west", "duration_text": "47 minutes",
          "condition_checked": True, "reader_answers_match": True,
          "editor_id": "editor-82", "certainty_changed": False}
assert admit_plain_notice(notice)["state"] == "editor-ready"
assert admit_plain_notice({**notice, "certainty_changed": True}) == {
    "state": "hold", "reason": "certainty-shift"}
''',
        'cost': 'The fixed-field gate takes O(1) time and space. Generating candidates and conducting reader tests cost more and depend on document length and audience size. The editor-ready state allows final human review, not automatic publication or an assertion that the notice is factually complete.',
        'mistakes': ['Turning a possible failover into a promised event.', 'Removing the condition to shorten the notice.', 'Testing comprehension only against the rewrite and not the source.', 'Keeping a notice after the incident source revision changes.'],
        'related': [N + 'plain-language-rewrite-and-protected-facts', N + 'plain-language-comprehension-and-release', N + 'generated-claim-evidence-and-unanswered-state', N + 'quantity-span-unit-and-range-contract', N + 'incident-handoff-summary-project'],
    },
    {
        'path': N + 'operational-rule-actors-triggers-and-exceptions',
        'title': 'Operational rules: actors, triggers, obligations and exceptions',
        'module': P, 'project': False,
        'summary': 'Parse an operational policy into a typed rule with a responsible actor, trigger, required action, deadline and exception scope.',
        'sections': [
            ('Separate the rule components', '“When gateway-west is degraded, on-call must page the owner within 47 minutes unless maintenance is approved” contains more than an action phrase. It names a trigger, actor, action, deadline and exception. Each component needs a source span and a typed meaning. A missing exception is not the same as an exception known to be false. Keep the original clause and revision beside the proposed frame. [[natural-language-processing/predicate-argument-roles-and-negation-scope|Predicate roles]] help identify who must do what.'),
            ('Attach exceptions to the right rule', 'An exception may sit in a following sentence or a footnote. It may modify one deadline, one actor or an entire section. Do not apply an exception globally just because it occurs nearby. Link it to a specific rule ID and record the evidence supporting that link. If the scope is ambiguous, hold the policy decision for review. [[natural-language-processing/discourse-units-and-relation-scope|Discourse scope]] helps distinguish a local qualification from a broad rule.'),
            ('Distinguish obligation from observation', '“On-call pages the owner” describes what happened; “on-call must page the owner” prescribes an action. Negation and modal verbs change the policy state. Dates, units and role names may need normalization, but a model’s normalized values should never become authority without a governed rule review. The code below validates only the shape and source spans of an extracted rule; it does not decide whether a live alert is required.'),
            ('Evaluate policy interpretation', 'Test trigger detection, actor binding, action binding, exception attachment and deadline normalization independently. Include negated triggers, double exceptions, outdated policies and references to another section. Score false required actions and false exemptions separately; both can cause operational harm. The [[natural-language-processing/policy-precedence-and-unknown-condition-state|precedence lesson]] handles multiple rule versions, and the [[natural-language-processing/incident-notification-rule-audit-project|project]] tests a conservative decision ledger.'),
        ],
        'code': '''def validate_operational_rule(source, frame):
    for component in ("trigger", "actor", "action", "exception"):
        start, end = frame[component]["span"]
        if not 0 <= start < end <= len(source):
            return {"state": "review", "reason": "invalid-span"}
        if source[start:end] != frame[component]["text"]:
            return {"state": "review", "reason": "span-mismatch"}
    if frame.get("deadline_minutes") != 47:
        return {"state": "review", "reason": "deadline-policy"}
    return {"state": "frame-valid"}

source = ("When gateway-west is degraded, on-call must page the owner "
          "within 47 minutes unless maintenance is approved.")
def span_of(phrase):
    start = source.index(phrase)
    return {"text": phrase, "span": (start, start + len(phrase))}
frame = {"trigger": span_of("gateway-west is degraded"),
         "actor": span_of("on-call"),
         "action": span_of("page the owner"),
         "exception": span_of("maintenance is approved"),
         "deadline_minutes": 47}
assert validate_operational_rule(source, frame)["state"] == "frame-valid"
''',
        'cost': 'Four fixed span checks take O(e) time and space for copied evidence substrings of total length e. A larger schema costs O(f+e) across f fields. Valid spans prove only provenance, not that the exception truly modifies this rule; that semantic link requires separate review.',
        'mistakes': ['Dropping “unless” and applying the rule unconditionally.', 'Treating a descriptive sentence as an obligation.', 'Applying an exception to the wrong clause.', 'Using a model-derived rule as live operational authority.'],
        'related': [N + 'policy-precedence-and-unknown-condition-state', N + 'incident-notification-rule-audit-project', N + 'predicate-argument-roles-and-negation-scope', N + 'discourse-units-and-relation-scope', N + 'time-expression-anchor-and-zone-contract'],
    },
    {
        'path': N + 'policy-precedence-and-unknown-condition-state',
        'title': 'Operational policy decisions: precedence and unknown conditions',
        'module': P, 'project': False,
        'summary': 'Select the applicable policy revision and hold a decision when trigger, exception or rule precedence cannot be verified.',
        'sections': [
            ('A parsed clause is not the active policy', 'An organization can retain old runbooks, draft amendments and current approved policies in the same search index. A correct extraction from an obsolete document can still produce the wrong decision. Select policies by trusted effective dates, approval state, scope and revision before evaluating their language. Store the selected rule ID with the result. [[natural-language-processing/operational-rule-actors-triggers-and-exceptions|Rule frames]] describe what each candidate says, not which candidate is authoritative.'),
            ('Resolve scope and precedence explicitly', 'A service-specific rule may override a general one, but only if the policy owner says so. Do not assume that the newest retrieved paragraph wins. If two active rules disagree and no precedence record resolves them, hold the decision and show both sources. Exception scope needs the same discipline: an approved maintenance window for archive-east cannot exempt gateway-west. [[natural-language-processing/entity-link-candidates-and-nil-decision|Entity linking]] can prevent similar service names from being conflated.'),
            ('Use three-valued conditions', 'A trigger or exception can be true, false or unknown. Unknown maintenance approval cannot be treated as false merely because a log entry was absent. Likewise, an unknown degradation state cannot be treated as a definite trigger. Ask for trusted evidence with timestamp and source. The code below chooses a unique active policy revision; it stops before deciding whether a page is required. That later decision must consume verified condition states.'),
            ('Measure decision failures', 'Test conflicting active revisions, backdated corrections, service-specific overrides, missing approval evidence and ambiguous exception scope. Report wrong-rule selection, false exemptions, false obligations and held cases. Human review should focus on cases with competing rules or unknown conditions. The [[natural-language-processing/incident-notification-rule-audit-project|notification project]] keeps the final action outside extracted prose.'),
        ],
        'code': '''def select_active_rule(rules, service_id, event_time):
    eligible = [rule for rule in rules
                if rule["service_id"] == service_id
                and rule["approved"]
                and rule["effective_from"] <= event_time
                and (rule["effective_until"] is None
                     or event_time < rule["effective_until"])]
    if len(eligible) != 1:
        return {"state": "review", "candidate_ids":
                [rule["rule_id"] for rule in eligible]}
    return {"state": "selected", "rule_id": eligible[0]["rule_id"]}

rules = [{"rule_id": "policy-47", "service_id": "gateway-west",
          "approved": True, "effective_from": "2026-10-01T00:00:00Z",
          "effective_until": None}]
assert select_active_rule(rules, "gateway-west",
                          "2026-10-06T03:47:00Z")["rule_id"] == "policy-47"
assert select_active_rule(rules + rules, "gateway-west",
                          "2026-10-06T03:47:00Z")["state"] == "review"
''',
        'cost': 'Scanning r rules takes O(r) time and O(k) output space for k eligible candidates. An indexed policy store can reduce selection cost. ISO timestamp strings compare lexically only when normalized to the same fixed UTC format; production must parse timestamps and handle version conflicts before relying on this selection.',
        'mistakes': ['Choosing the newest search hit rather than an approved active rule.', 'Treating unknown exception evidence as a negative answer.', 'Applying one service’s exemption to another.', 'Silently resolving two active conflicting policies by list order.'],
        'related': [N + 'operational-rule-actors-triggers-and-exceptions', N + 'incident-notification-rule-audit-project', N + 'entity-link-candidates-and-nil-decision', N + 'revision-dependency-invalidation-and-reindex', N + 'trusted-action-gate-and-retrieval-audit'],
    },
    {
        'path': N + 'incident-notification-rule-audit-project',
        'title': 'Project: audit incident notification rules and exceptions',
        'module': P, 'project': True,
        'summary': 'Build a review ledger for service-degradation notification rules, including effective revision, deadline and maintenance exceptions.',
        'sections': [
            ('Construct the policy fixture', 'Create fictional approved and superseded policies for gateway-west, each with an effective interval. One rule requires on-call to page an owner within 47 minutes of verified degradation unless approved maintenance covers the same service and event time. Add an overlapping draft, an archive-east exception and an unknown maintenance approval. Annotate clause spans, rule IDs, actors, actions, deadlines and exception links. [[natural-language-processing/operational-rule-actors-triggers-and-exceptions|Rule extraction]] creates reviewable candidate frames.'),
            ('Resolve authority before conditions', 'Filter by service, approval and effective interval. If multiple active rules survive, stop for policy-owner review. Bind the selected rule to verified observations of degradation and maintenance approval, each with source and timestamp. Never infer that an unmentioned approval is false. [[natural-language-processing/policy-precedence-and-unknown-condition-state|Precedence and unknown states]] prevent a plausible but unsupported notification decision.'),
            ('Build a non-executing decision ledger', 'Record whether the trigger is true, false or unknown; whether the exception is true, false or unknown; and which rule revision was selected. The code below returns “page-required-for-review” only when trigger is verified true and exception verified false. It does not send a page. A separate trusted service must validate operator identity, deadline and current incident state before an external action.'),
            ('Evaluate counterexamples', 'Report wrong-rule selections, false required pages, false exemptions, unresolved cases correctly held and deadline normalization errors. Test an event just before and after a policy boundary. Review cases where the same word “maintenance” appears without an approved window. Keep all source spans so a policy owner can correct the extraction and invalidate affected decisions.'),
        ],
        'code': '''def notification_review_state(rule_id, trigger_state, exception_state):
    if not rule_id:
        return {"state": "hold", "reason": "rule-unresolved"}
    if trigger_state not in {"true", "false"}:
        return {"state": "hold", "reason": "trigger-unknown"}
    if trigger_state == "false":
        return {"state": "not-triggered", "rule_id": rule_id}
    if exception_state not in {"true", "false"}:
        return {"state": "hold", "reason": "exception-unknown"}
    if exception_state == "true":
        return {"state": "exempt-for-review", "rule_id": rule_id}
    return {"state": "page-required-for-review", "rule_id": rule_id}

assert notification_review_state("policy-47", "true", "false") == {
    "state": "page-required-for-review", "rule_id": "policy-47"}
assert notification_review_state("policy-47", "true", "unknown")["state"] == \
    "hold"
assert notification_review_state("policy-47", "false", "unknown")["state"] == \
    "not-triggered"
''',
        'cost': 'The three-state gate takes O(1) time and space. Source retrieval, rule selection and evidence verification dominate system cost. Its output is a review classification only; external paging requires a separate authenticated workflow and a fresh check of the incident and policy state.',
        'mistakes': ['Paging because a policy sentence was found in search.', 'Assuming missing maintenance evidence means no exception.', 'Applying a draft rule to a current incident.', 'Sending an external notification from a parser’s output.'],
        'related': [N + 'operational-rule-actors-triggers-and-exceptions', N + 'policy-precedence-and-unknown-condition-state', N + 'trusted-action-gate-and-retrieval-audit', N + 'time-expression-anchor-and-zone-contract', N + 'incident-claim-verification-project'],
    },
]

crosslinks = [
    (N + 'grammar-correction-review-and-abstention', N + 'plain-language-rewrite-and-protected-facts'),
    (N + 'nli-premise-hypothesis-and-evidence-contract', N + 'plain-language-comprehension-and-release'),
    (N + 'incident-handoff-summary-project', N + 'incident-status-notice-rewrite-project'),
    (N + 'discourse-units-and-relation-scope', N + 'operational-rule-actors-triggers-and-exceptions'),
    (N + 'revision-dependency-invalidation-and-reindex', N + 'policy-precedence-and-unknown-condition-state'),
    (N + 'trusted-action-gate-and-retrieval-audit', N + 'incident-notification-rule-audit-project'),
]

if __name__ == '__main__':
    publish(lessons, (S, P), crosslinks,
            'aitrove-nlp-plain-policy-import-20261006.json', 4902,
            subject='natural-language-processing', hub_path=N + 'nlp-tutorial')
