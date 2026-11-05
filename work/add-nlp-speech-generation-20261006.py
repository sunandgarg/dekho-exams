"""Extend NLP with speech transcripts and grounded generation."""
from de_batch_publisher import publish

N = 'natural-language-processing/'
S = 'Speech transcripts and speaker identity'
G = 'Grounded text generation and evaluation'

lessons = [
    {
        'path': N + 'asr-transcript-segments-and-entity-risk',
        'title': 'Speech transcripts: segments, recognition errors and entity risk',
        'module': S, 'project': False,
        'summary': 'A transcript is a derived reading of audio. Keep timing and uncertainty so an incorrect order ID cannot become a trusted fact.',
        'sections': [
            ('Represent the transcript as aligned segments', 'Store recording revision, segment start and end time, recognized words, language hypothesis and recognizer version. A final display paragraph is a derived view. Do not assume punctuation or sentence boundaries existed in the speech. Keep the audio span addressable for an authorized reviewer, and avoid publishing restricted recordings through a transcript link. [[natural-language-processing/span-offset-annotation|Text offsets]] still matter, but word-to-audio timing is a separate coordinate system.'),
            ('Treat entities as a separate failure class', 'Word error rate can improve while the model still confuses ZX-47 with ZX-74 or turns “not approved” into “approved.” Measure exact recognition of identifiers, amounts, names and negation in addition to overall word errors. Verify critical values through an authorized system or an explicit human replay of the audio. A language model may produce a plausible product name that was never spoken. [[natural-language-processing/support-entity-extraction-project|Entity extraction]] should therefore consume a transcript with provenance and uncertainty.'),
            ('Keep corrections traceable', 'A reviewer may correct a misheard word, but the original recognition result must remain available with the audio interval and correction record. Downstream offsets and extracted entities must be recomputed from the corrected transcript revision. Mark an unresolved segment rather than filling it from neighboring context. If consent or retention policy removes audio, revoke derived transcript and index records according to that policy.'),
            ('Evaluate the intended workflow', 'Audit clean and noisy calls, accents, code-switching, cross-talk, long silences and rare product names. Report word errors, entity errors, time alignment errors, review time and false actions. Compare models on the same held-out recordings, grouped by conversation. [[natural-language-processing/speaker-turn-attribution-and-overlap|Speaker attribution]] adds another uncertainty source; the [[natural-language-processing/support-call-transcript-review-project|project]] places both in a review queue.'),
        ],
        'code': '''def validate_transcript_segment(segment, recording_duration_ms):
    start = segment["start_ms"]
    end = segment["end_ms"]
    if not 0 <= start < end <= recording_duration_ms:
        raise ValueError("segment lies outside recording")
    if not segment["recording_revision"]:
        raise ValueError("recording revision is required")
    return {"start_ms": start, "end_ms": end,
            "text": segment["text"],
            "recording_revision": segment["recording_revision"]}

spoken = {"start_ms": 4700, "end_ms": 8200,
          "text": "order ZX-47", "recording_revision": "call-r7"}
assert validate_transcript_segment(spoken, 19000)["text"] == "order ZX-47"
''',
        'cost': 'Segment validation is O(1) time and space apart from copying its text. Recognition cost grows with audio duration, while storing word timing adds metadata. Human replay is expensive, so prioritize critical entities and low-confidence segments. A faster recognizer is not an improvement if it produces more wrong identifiers in the workflow.',
        'mistakes': ['Treating punctuation emitted by the recognizer as spoken evidence.', 'Using overall word error rate as a substitute for identifier accuracy.', 'Applying corrected-text offsets to the original transcript.', 'Keeping searchable transcript derivatives after audio deletion requires removal.'],
        'related': [N + 'speaker-turn-attribution-and-overlap', N + 'support-call-transcript-review-project', N + 'span-offset-annotation', N + 'entity-decoding-and-span-evaluation', N + 'script-profile-and-code-switching-boundary'],
    },
    {
        'path': N + 'speaker-turn-attribution-and-overlap',
        'title': 'Speaker turns: attribution, overlap and unresolved voices',
        'module': S, 'project': False,
        'summary': 'A correct sentence assigned to the wrong speaker can reverse a support decision. Keep diarization separate from identity verification.',
        'sections': [
            ('Separate voice clusters from people', 'Diarization groups audio by apparent speaker. Speaker A is not automatically the account owner, support agent or caller named in a CRM record. Store segment times, cluster ID, diarization version and whether a human verified a role. Avoid inferring legal or account identity from voice similarity. In a support call, a second person may speak on the same channel, and one person can be split into multiple clusters after a microphone change.'),
            ('Model overlapping speech', 'Two people can speak at once. A single-owner timeline that forces each millisecond to one speaker loses that fact. Store overlapping intervals and permit UNKNOWN attribution when separation fails. Do not attach a commitment such as “I approve the refund” to an account holder unless the audio and role verification support it. [[natural-language-processing/dialogue-handoff-and-action-gates|Action gates]] remain separate from transcript interpretation.'),
            ('Audit turn boundaries and roles', 'Measure boundary error, speaker confusion, overlap recall and role attribution on reviewed calls. A good diarization score can still hide one serious agent/customer swap in a critical span. Group recordings by call and device for evaluation; clips from one call must not appear in both train and audit. Replay disputed segments with surrounding context. [[natural-language-processing/asr-transcript-segments-and-entity-risk|Transcript segments]] supply the aligned words, not verified identities.'),
            ('Handle revisions and access', 'If a reviewer splits a turn or relabels a role, regenerate downstream summaries and action items using the revised transcript. Keep role corrections with reviewer and source interval. Limit audio and transcript access to authorized staff; a public summary should not expose a private caller name. The [[natural-language-processing/support-call-transcript-review-project|applied project]] stages uncertain turns for review before a handoff note is released.'),
        ],
        'code': '''def attributed_statement(segment, verified_roles):
    speaker = segment.get("speaker_cluster")
    role = verified_roles.get(speaker)
    if role is None:
        return {"state": "review", "speaker": speaker,
                "text": segment["text"]}
    return {"state": "attributed", "role": role,
            "text": segment["text"]}

turn = {"speaker_cluster": "voice-b", "text": "I will check ZX-47."}
assert attributed_statement(turn, {"voice-a": "agent"})["state"] == "review"
''',
        'cost': 'Role lookup is O(1) average time. Diarization cost grows with audio duration and speaker count; overlapping speech usually increases review load. A cautious UNKNOWN state may reduce automatic action extraction, but it is cheaper than publishing a promise under the wrong person’s name.',
        'mistakes': ['Treating an anonymous voice cluster as a verified customer.', 'Forcing overlapping audio into a single speaker turn.', 'Evaluating only average diarization error while critical role swaps remain.', 'Leaving a released summary unchanged after a speaker correction.'],
        'related': [N + 'asr-transcript-segments-and-entity-risk', N + 'support-call-transcript-review-project', N + 'dialogue-state-slots-and-corrections', N + 'dialogue-handoff-and-action-gates', N + 'privacy-safe-ticket-pipeline-project'],
    },
    {
        'path': N + 'support-call-transcript-review-project',
        'title': 'Project: review support-call transcripts before handoff',
        'module': S, 'project': True,
        'summary': 'Turn a recorded call into a reviewable transcript with timed evidence, uncertain speakers and protected customer identifiers.',
        'sections': [
            ('Define the intake boundary', 'The support team receives an authorized call recording. Recognition creates timed segments, then diarization proposes anonymous voice clusters. The service may draft a handoff note, but it cannot verify account ownership or execute a refund from speech alone. Store recording revision, consent and retention scope. Every extracted order ID and action item must link to the audio interval an agent can replay.'),
            ('Create the hard audit', 'Include noisy calls, overlapping speech, code-switching, corrected product names, negated approvals and similar order IDs. Reviewers transcribe critical intervals and assign speaker roles only where evidence supports them. Group all clips from one call and customer before splitting. [[natural-language-processing/asr-transcript-segments-and-entity-risk|Transcript evidence]] checks words; [[natural-language-processing/speaker-turn-attribution-and-overlap|speaker attribution]] checks who said them.'),
            ('Stage the handoff', 'Extract candidate identifiers and commitments from the transcript, but show uncertain words and speakers as unresolved. Require an agent to confirm critical fields against the authorized account system. Keep the original ASR output, the reviewer correction and the final note as separate revisions. A speaker correction invalidates any statement that depended on that turn. Redact private content from broad search indices.'),
            ('Monitor release behavior', 'Track exact identifier accuracy, speaker role errors, false commitments, review time and deletion propagation. Review sampled confident segments, not only low-score ones. A new recognizer or diarization model needs a replay on the frozen call audit before use. If a recording is removed, retire its transcript, embeddings, cached snippets and handoff draft according to policy.'),
        ],
        'code': '''def handoff_claim_status(claim):
    if not claim["audio_revision"] or not claim["start_ms"] < claim["end_ms"]:
        return "blocked"
    if claim["critical"] and (not claim["speaker_verified"]
                               or not claim["value_verified"]):
        return "agent-review"
    return "draft-only"

claim = {"audio_revision": "call-r7", "start_ms": 4700,
         "end_ms": 8200, "critical": True, "speaker_verified": False,
         "value_verified": True}
assert handoff_claim_status(claim) == "agent-review"
''',
        'cost': 'The gate is O(1) time and space per claim. Audio storage, recognition and replay dominate operating cost. Queue critical claims for review first; there is little benefit in perfecting filler words while an order ID or speaker role is wrong. Measure agent time saved after verification, not just draft-generation latency.',
        'mistakes': ['Using speech-derived intent as account authorization.', 'Publishing a commitment whose speaker is unresolved.', 'Retaining transcript vectors after the recording is removed.', 'Splitting clips from one call across train and audit.'],
        'related': [N + 'asr-transcript-segments-and-entity-risk', N + 'speaker-turn-attribution-and-overlap', N + 'incident-handoff-summary-project', N + 'pii-detection-and-redaction-boundary', N + 'dialogue-handoff-and-action-gates'],
    },
    {
        'path': N + 'generated-claim-evidence-and-unanswered-state',
        'title': 'Generated answers: claim evidence and unanswered state',
        'module': G, 'project': False,
        'summary': 'A readable answer can still assert a fact absent from the retrieved material. Keep support and refusal as explicit outcomes.',
        'sections': [
            ('Decompose the output into claims', 'For a runbook answer, identify each operational claim: current status, cause, action and condition. A claim may be supported, contradicted or not addressed by accessible passages. Store passage IDs and revisions for the supporting span. Do not treat mere word overlap as evidence. If the retrieved material does not answer a question, return an unanswered state and a useful next step. [[natural-language-processing/nli-premise-hypothesis-and-evidence-contract|Entailment]] gives a related premise-hypothesis test.'),
            ('Constrain generation before review', 'Pass only passages the requester can access. Keep exact commands, identifiers and version requirements separate from prose so they can be checked mechanically. Ask the model to produce a concise answer with claim-to-passage links, but validate those links after generation. A cited passage might exist yet not support the sentence attached to it. [[natural-language-processing/hybrid-ranking-and-access-filters|Retrieval filters]] must run before model context is assembled.'),
            ('Gate risky assertions', 'Block unsupported instructions that alter production state, financial outcomes or customer commitments. For lower-risk content, show a draft with marked unsupported sentences and let an authorized reviewer decide. A low-confidence answer is not repaired by adding a generic warning while preserving the false claim. Prefer no answer when the evidence is absent or stale. [[natural-language-processing/generation-evaluation-and-regression-slices|Regression evaluation]] measures these cases.'),
            ('Separate fluency from utility', 'Compare claim support, answerability, task completion and review time. A fluent paragraph may be worse than a brief “not documented” response when the runbook is missing. Include conflicting source revisions and retrieved distractors in the audit. The [[natural-language-processing/runbook-answer-release-project|runbook release project]] stages answers with explicit supported and unresolved states.'),
        ],
        'code': '''def claim_release_state(claims, accessible_passage_ids):
    if not claims:
        return "unanswered"
    for claim in claims:
        if claim["risk"] == "action" and claim["support"] != "supported":
            return "blocked"
        if claim["support"] != "supported":
            return "review"
        if claim["passage_id"] not in accessible_passage_ids:
            return "blocked"
    return "draft-review"

claims = [{"risk": "info", "support": "supported", "passage_id": "rb-47"}]
assert claim_release_state(claims, {"rb-47"}) == "draft-review"
assert claim_release_state([], {"rb-47"}) == "unanswered"
''',
        'cost': 'The gate scans c claims in O(c) time and uses O(1) extra space with a set of accessible passage IDs. Claim extraction, retrieval and human verification cost more. More generated sentences create more claims to inspect, so concise output can lower both inference and review expense without sacrificing the answer.',
        'mistakes': ['Treating a linked passage as proof it supports a claim.', 'Answering from inaccessible or retired runbook material.', 'Appending a warning to an unsupported production command instead of blocking it.', 'Reporting fluency while ignoring unanswered and false-action cases.'],
        'related': [N + 'generation-evaluation-and-regression-slices', N + 'runbook-answer-release-project', N + 'nli-premise-hypothesis-and-evidence-contract', N + 'hybrid-ranking-and-access-filters', N + 'summary-claim-verification-and-review'],
    },
    {
        'path': N + 'generation-evaluation-and-regression-slices',
        'title': 'Generation evaluation: claim support, disagreement and regressions',
        'module': G, 'project': False,
        'summary': 'One reference answer does not define every valid response. Evaluate factual claims, abstention and the work a reader can safely perform.',
        'sections': [
            ('Write a task-specific rubric', 'Separate correctness, evidence support, completeness, unsafe instruction, clarity and appropriate abstention. A model may produce different valid wording from a reference; exact text similarity cannot establish whether an operational claim is supported. Review each claim against its cited passage and record unsupported, contradicted and unverified states. [[natural-language-processing/generated-claim-evidence-and-unanswered-state|The claim contract]] makes the unit of evaluation explicit.'),
            ('Build hard cases', 'Include stale runbook versions, near-identical error codes, missing documents, conflicting notes and permission-filtered passages. Hold entire incidents and document revisions out of prompt or model tuning. Evaluate short unanswered replies as legitimate outputs when evidence is absent. Sample production failures by risk and by ordinary traffic; only reviewing spectacular errors hides common low-grade omissions.'),
            ('Calibrate reviewers and tools', 'Ask at least two reviewers to judge a subset without seeing each other’s decision. Adjudicate disagreement under a written policy. Automated checks can catch missing passage IDs or changed amounts, but they are screens rather than an oracle for support. Track judge version if a model assists review and compare its disagreements with human decisions. A rising acceptance rate may reflect reviewers becoming less strict rather than a better generator.'),
            ('Compare releases on the same workload', 'Report unsupported claims per answer, dangerous action rate, useful-answer rate, unanswered rate and reviewer minutes. Slice by document age, language, question type and access scope. A release passes only if severe errors stay below the agreed ceiling and task utility improves. Keep an old approved bundle available for rollback. [[natural-language-processing/runbook-answer-release-project|The project]] turns the rubric into a release test.'),
        ],
        'code': '''def summarize_generation_audit(cases):
    if not cases:
        raise ValueError("audit needs reviewed cases")
    unsupported = sum(case["unsupported_claims"] for case in cases)
    dangerous = sum(bool(case["dangerous_action"]) for case in cases)
    useful = sum(bool(case["useful"]) for case in cases)
    return {"unsupported_per_answer": unsupported / len(cases),
            "dangerous_action_rate": dangerous / len(cases),
            "useful_answer_rate": useful / len(cases)}

audit = [{"unsupported_claims": 0, "dangerous_action": False, "useful": True},
         {"unsupported_claims": 1, "dangerous_action": False, "useful": False}]
assert summarize_generation_audit(audit)["unsupported_per_answer"] == 0.5
''',
        'cost': 'Summarizing n reviewed cases is O(n) time and O(1) extra space. The expensive part is claim-level human review and maintaining a representative frozen audit. Fewer, higher-quality cases with difficult retrieval and action boundaries can reveal more than a large pile of near-duplicate easy questions.',
        'mistakes': ['Using one reference wording as the sole measure of correctness.', 'Letting a judge model grade its own family without human calibration.', 'Hiding severe action errors inside a high mean usefulness score.', 'Counting an appropriate unanswered response as an automatic failure.'],
        'related': [N + 'generated-claim-evidence-and-unanswered-state', N + 'runbook-answer-release-project', N + 'summary-claim-verification-and-review', N + 'qa-answerability-and-calibration', N + 'annotation-disagreement-and-label-policy'],
    },
    {
        'path': N + 'runbook-answer-release-project',
        'title': 'Project: release evidence-checked runbook answers',
        'module': G, 'project': True,
        'summary': 'Build a reviewed answer path that retrieves authorized passages, marks unsupported claims and abstains when the runbook has no answer.',
        'sections': [
            ('Set the answer boundary', 'An operator asks whether to retry a failed callback. The service retrieves versioned runbook passages under the operator’s permissions and drafts an answer. It must not execute the retry. Every instruction or status claim needs a passage that supports it; if no accessible document answers the question, return an unanswered state. Keep the question, retrieved revision set, generated draft and reviewer decision as separate records.'),
            ('Create adversarial questions', 'Include a current runbook, a retired version with a conflicting threshold, a similar service with a different retry limit and an inaccessible incident note. Add questions whose answer is genuinely absent. Reviewers identify supported claims and dangerous commands without seeing the model’s preferred answer first. [[natural-language-processing/generated-claim-evidence-and-unanswered-state|Claim evidence]] defines the output; [[natural-language-processing/generation-evaluation-and-regression-slices|the evaluation rubric]] defines the release test.'),
            ('Build the staged pipeline', 'Retrieve with access filters, assemble passages with IDs and revisions, then generate a short answer. Split it into claims, validate citations and exact operational tokens, and route unsupported or contradictory statements to review. A citation that points to a stale passage should fail even when its text looks plausible. Show the reviewer the passage beside the claim, not merely a confidence number.'),
            ('Operate and roll back', 'Shadow-test on recent questions before surfacing drafts to operators. Track wrong-action claims, unsupported facts, unanswered rate, review minutes and retrieval misses. Version index, access policy, prompt and model together. When a runbook changes, invalidate cached answers tied to its old revision. A rollback restores the prior approved bundle while retaining the audit of rejected drafts.'),
        ],
        'code': '''def stage_runbook_answer(retrieved, claims, allowed_revisions):
    current = {passage["id"] for passage in retrieved
               if passage["revision"] in allowed_revisions
               and passage["accessible"]}
    if not current:
        return {"state": "unanswered", "reason": "no-current-evidence"}
    for claim in claims:
        if claim["passage_id"] not in current or not claim["supported"]:
            return {"state": "review", "reason": "unsupported-claim"}
    return {"state": "draft-review", "claims": len(claims)}

passages = [{"id": "rb-47", "revision": "r8", "accessible": True}]
claims = [{"passage_id": "rb-47", "supported": True}]
assert stage_runbook_answer(passages, claims, {"r8"})["state"] == "draft-review"
''',
        'cost': 'Building the accessible passage set is O(p) time and space for p retrieved passages; checking c claims is O(c) average time. Retrieval and generation dominate machine cost, while review dominates safety cost. Keep the answer short and stop early on missing evidence, because extra prose adds unsupported-claim surface and reviewer work.',
        'mistakes': ['Treating an inaccessible passage as acceptable model context.', 'Letting an old runbook revision support a current command.', 'Skipping review because every sentence has some citation.', 'Caching an answer after its supporting runbook is retired.'],
        'related': [N + 'generated-claim-evidence-and-unanswered-state', N + 'generation-evaluation-and-regression-slices', N + 'runbook-question-answering-project', N + 'hybrid-ranking-and-access-filters', N + 'qa-answerability-and-calibration'],
    },
]

crosslinks = [
    (N + 'span-offset-annotation', N + 'asr-transcript-segments-and-entity-risk'),
    (N + 'dialogue-handoff-and-action-gates', N + 'speaker-turn-attribution-and-overlap'),
    (N + 'incident-handoff-summary-project', N + 'support-call-transcript-review-project'),
    (N + 'nli-premise-hypothesis-and-evidence-contract', N + 'generated-claim-evidence-and-unanswered-state'),
    (N + 'summary-claim-verification-and-review', N + 'generation-evaluation-and-regression-slices'),
    (N + 'runbook-question-answering-project', N + 'runbook-answer-release-project'),
]

if __name__ == '__main__':
    publish(lessons, (S, G), crosslinks,
            'aitrove-nlp-speech-generation-import-20261006.json', 4794,
            subject='natural-language-processing', hub_path=N + 'nlp-tutorial')
