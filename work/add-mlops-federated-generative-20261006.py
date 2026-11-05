"""Publish federated training and generative release operations lessons."""
from de_batch_publisher import publish

M = 'mlops/'
F = 'Federated training round operations'
G = 'Generative application release contracts'

lessons = [
    {
        'path': M + 'federated-round-eligibility-and-update-identity',
        'title': 'Federated rounds: eligible clients, base models and update identity',
        'module': F, 'project': False,
        'summary': 'A federated round needs a pinned base model and auditable participation rules before distributed updates can be combined.',
        'sections': [
            ('Define the round as an immutable unit', 'A fleet of field scanners trains a defect classifier on local observations while raw images stay on devices. Give each round an ID, base-model digest, feature schema, local-training configuration, eligibility policy, deadline and aggregation rule. A client update belongs to exactly one base digest and round; accepting a delayed update from an earlier round changes the meaning of the aggregate. [[mlops/run-manifest-and-artifact-lineage|Run lineage]] applies even though training data is not centralized, while [[mlops/edge-model-manifests-and-cohort-rollouts|edge manifests]] pin the software devices can execute.'),
            ('Select for availability without hiding bias', 'Eligible devices may need adequate charge, an approved network and a current app version. Record the number eligible, sampled, accepted, failed and timed out by device class and region. A fleet with poor connectivity may be underrepresented; do not call a random sample of available devices representative of every site. Use privacy-safe aggregates for coverage reporting. Define a minimum participation floor by relevant cohort before promotion, and hold the round if one region contributes too little evidence. [[mlops/slice-quality-gates-and-uncertainty|Slice gates]] help interpret that gap.'),
            ('Validate update envelopes', 'Require a signed or otherwise authenticated client identity, authorized base digest, tensor shape, finite numeric values, declared example count and update size limit. Authentication alone does not prove an update is benign. Keep abnormal-norm and repeated-payload signals for investigation without asserting that every outlier is an attack. Where the threat model requires it, use a reviewed secure aggregation or privacy mechanism; merely leaving raw data on devices is not a privacy guarantee. [[mlops/training-source-admission-and-quarantine|Source quarantine]] offers a comparable hold-and-review pattern.'),
            ('Close the round deliberately', 'At deadline, freeze accepted update IDs, rejects and dropout counts. Aggregate only accepted updates under the recorded rule, then evaluate the new global model on independent data and affected cohorts before rollout. Never merge late updates into an already evaluated artifact. [[mlops/federated-aggregation-dropout-and-privacy-boundary|Aggregation controls]] handle dropout and contribution limits; [[mlops/scanner-federated-round-project|the project]] includes devices that return after the round closes.'),
        ],
        'code': '''def admit_client_update(update, round_manifest, accepted_ids):
    if update["update_id"] in accepted_ids:
        return "reject:duplicate"
    if update["round_id"] != round_manifest["round_id"]:
        return "reject:wrong-round"
    if update["base_digest"] != round_manifest["base_digest"]:
        return "reject:stale-base"
    if update["tensor_shape"] != round_manifest["tensor_shape"]:
        return "reject:shape"
    if not update["authenticated"] or update["example_count"] <= 0:
        return "reject:identity-or-count"
    return "accept"

round_manifest = {"round_id": "scanner-round-47", "base_digest": "defect-r8",
                  "tensor_shape": (128,)}
update = {"update_id": "scanner-82-r47", "round_id": "scanner-round-47",
          "base_digest": "defect-r8", "tensor_shape": (128,),
          "authenticated": True, "example_count": 39}
assert admit_client_update(update, round_manifest, set()) == "accept"
assert admit_client_update({**update, "base_digest": "defect-r7"},
                           round_manifest, set()) == "reject:stale-base"
''',
        'cost': 'The envelope gate is O(1) time and space before payload inspection; checking each tensor value costs O(d) for d parameters. Round coordination uses network bandwidth proportional to participating clients times model-update bytes. Tight deadlines reduce waiting but can bias participation toward well-connected devices; measure the tradeoff rather than hiding it in a success count.',
        'mistakes': ['Aggregating a delayed update against a different base model.', 'Treating available-device sampling as a representative sample of all users.', 'Assuming local data storage alone guarantees update privacy.', 'Evaluating one aggregate and then quietly adding late updates to it.'],
        'related': [M + 'federated-aggregation-dropout-and-privacy-boundary', M + 'scanner-federated-round-project', M + 'run-manifest-and-artifact-lineage', M + 'edge-model-manifests-and-cohort-rollouts', M + 'training-source-admission-and-quarantine'],
    },
    {
        'path': M + 'federated-aggregation-dropout-and-privacy-boundary',
        'title': 'Federated aggregation: dropout, contribution caps and privacy limits',
        'module': F, 'project': False,
        'summary': 'An aggregate should reflect an explicit participant set and contribution rule, with dropout and privacy limitations stated plainly.',
        'sections': [
            ('Count who actually contributed', 'Invited clients are not accepted clients. A scanner may download the base model but disconnect before uploading an update, fail validation or arrive after the deadline. Report participation by stage and cohort. If aggregation uses example-count weighting, cap the reported count to prevent one client from dominating the round; the cap is an operational guard, not proof against malicious updates. Store accepted update IDs and the exact weighting rule with the aggregate. [[mlops/federated-round-eligibility-and-update-identity|Round identity]] fixes the eligible base and deadline.'),
            ('Handle partial rounds', 'Set a minimum number of accepted clients and a minimum cohort mix before aggregation. If the floor is missed, abort or extend under a new recorded deadline and reassess eligibility. Do not silently lower the floor because the model appears to improve on one central validation set. A region with more dropouts may be missing from that set. Keep a clear policy for whether stragglers enter the next round; their update must be retrained against its new base, never relabeled and reused. [[mlops/slice-quality-gates-and-uncertainty|Cohort uncertainty]] matters after dropout.'),
            ('Separate security properties', 'Secure aggregation can limit what the server learns from individual updates, but it does not establish that an aggregate is accurate, fair or free of harmful influence. Differential privacy requires a stated mechanism and accounting policy; it is not achieved by clipping alone. Keep authentication, transport security, access control and update validation as separate controls. Validate any privacy claim against the implemented protocol and threat model. [[mlops/inference-logging-privacy|Logging privacy]] also applies to per-device diagnostics and rejected-update records.'),
            ('Evaluate the released model', 'After aggregation, test the candidate against the prior global artifact on independent holdouts, device classes and rare defect types. Run a small edge cohort with a reversible package and watch real-world failures before broad installation. A good aggregate metric can conceal harm to a site that rarely participated. [[mlops/scanner-federated-round-project|The project]] aborts one low-participation round, then tests a revised round without claiming privacy properties its protocol did not implement.'),
        ],
        'code': '''def aggregate_client_rates(updates, minimum_clients, contribution_cap):
    if minimum_clients <= 0 or contribution_cap <= 0:
        raise ValueError("invalid round policy")
    if len(updates) < minimum_clients:
        return {"state": "abort:participation", "rate": None}
    total_weight = 0
    weighted_rate = 0.0
    for update in updates:
        if not 0 <= update["local_error_rate"] <= 1 or update["examples"] <= 0:
            raise ValueError("invalid client metric")
        weight = min(update["examples"], contribution_cap)
        total_weight += weight
        weighted_rate += weight * update["local_error_rate"]
    return {"state": "review:aggregate", "rate": weighted_rate / total_weight}

updates = [{"examples": 47, "local_error_rate": 0.2},
           {"examples": 820, "local_error_rate": 0.1},
           {"examples": 39, "local_error_rate": 0.3}]
assert aggregate_client_rates(updates[:2], 3, 82)["state"] == "abort:participation"
assert aggregate_client_rates(updates, 3, 82)["state"] == "review:aggregate"
''',
        'cost': 'The illustrative scalar aggregation is O(c) time and O(1) extra space for c clients. Real parameter aggregation costs O(cd) for d parameters per client and may require secure-aggregation communication overhead. The example aggregates reported error rates, not model weights; a production optimizer needs a separate reviewed algorithm and privacy accounting where claimed.',
        'mistakes': ['Counting invited devices as completed participants.', 'Letting one client claim an unlimited example count.', 'Treating secure aggregation as proof of model quality or full privacy.', 'Changing participation floors after seeing a candidate score.'],
        'related': [M + 'federated-round-eligibility-and-update-identity', M + 'scanner-federated-round-project', M + 'slice-quality-gates-and-uncertainty', M + 'inference-logging-privacy', M + 'edge-offline-telemetry-and-rollback'],
    },
    {
        'path': M + 'scanner-federated-round-project',
        'title': 'Project: coordinate a field-scanner federated training round',
        'module': F, 'project': True,
        'summary': 'Pin a scanner model, validate client updates, abort a sparse round and release only an independently evaluated aggregate.',
        'sections': [
            ('Prepare the fleet and manifest', 'Field scanners classify damaged shipping labels locally. Raw photos remain on-device under the product policy. Freeze a global model digest, local training settings, tensor shape, example-count cap and round deadline. Define eligibility by app version, approved network and power state, then record eligibility by warehouse region before sampling. The set that can participate is not automatically representative of the entire fleet. [[mlops/federated-round-eligibility-and-update-identity|The round manifest]] makes every accepted update traceable to one base.'),
            ('Inject failures', 'Invite 470 devices across four regions. Some return duplicate update IDs, some train against the prior base and a remote region loses connectivity. Reject stale and malformed envelopes; do not retry them as if they were new training results. The first round misses the minimum accepted-client and regional-coverage gates, so abort it without creating a promotable model. [[mlops/federated-aggregation-dropout-and-privacy-boundary|Participation accounting]] distinguishes invitations, completed uploads and accepted updates.'),
            ('Run a controlled second round', 'Start a new round with a fresh deadline and the same pinned base, rather than extending the completed round invisibly. Recompute eligibility and ensure the remote region has a valid opportunity to participate. Cap contribution weight per client and record the exact accepted update IDs and aggregate recipe. Compare the candidate on a held-out labeled set that does not consist only of the most connected sites. A claimed privacy guarantee requires a separately validated protocol; this exercise makes no such claim.'),
            ('Stage the artifact', 'Package the candidate with runtime and preprocessing digests, evaluate rare damage types and scan-quality slices, then stage a small device cohort. Monitor local failure, offline reporting coverage and rollback events before broad rollout. Publish the round history, rejected-update counts, participation by region and evaluation limits. [[mlops/edge-model-manifests-and-cohort-rollouts|Edge release controls]] manage installation; a training-round pass alone cannot guarantee device-side behavior.'),
        ],
        'code': '''def scanner_round_gate(accepted, minimum_clients, region_counts, minimum_region):
    if accepted < 0 or minimum_clients <= 0 or minimum_region < 0:
        raise ValueError("invalid policy or counts")
    if accepted < minimum_clients:
        return "abort:client-floor"
    if not region_counts or any(count < minimum_region
                                for count in region_counts.values()):
        return "abort:region-coverage"
    if sum(region_counts.values()) != accepted:
        return "hold:accounting-mismatch"
    return "evaluate:aggregate"

regions = {"north": 82, "south": 71, "east": 64, "west": 39}
assert scanner_round_gate(256, 220, regions, 47) == "abort:region-coverage"
assert scanner_round_gate(256, 220, {**regions, "west": 47}, 47) == \
       "hold:accounting-mismatch"
assert scanner_round_gate(256, 220, regions, 39) == "evaluate:aggregate"
''',
        'cost': 'The gate is O(r) time and O(1) extra space for r regions. Two rounds increase device battery, network and coordination cost; aborting a sparse first round prevents an unrepresentative aggregate from being treated as production evidence. A later rollout still incurs package downloads and delayed offline telemetry.',
        'mistakes': ['Reusing an old-base update in a later round.', 'Promoting a round that passed global participation but missed one region.', 'Presenting local-data storage as a complete privacy proof.', 'Skipping independent evaluation because aggregate training loss fell.'],
        'related': [M + 'federated-round-eligibility-and-update-identity', M + 'federated-aggregation-dropout-and-privacy-boundary', M + 'edge-model-manifests-and-cohort-rollouts', M + 'edge-offline-telemetry-and-rollback', M + 'slice-quality-gates-and-uncertainty'],
    },
    {
        'path': M + 'generative-release-manifest-and-prompt-model-binding',
        'title': 'Generative releases: bind prompt, model, tools and output contract',
        'module': G, 'project': False,
        'summary': 'A generative feature changes when any prompt, model, retrieval index, tool schema or decoding policy changes.',
        'sections': [
            ('Version the complete behavior', 'A maintenance-ticket summarizer uses a prompt template, hosted language model, retrieved manual passages, a ticket lookup tool and a JSON output contract. A prompt edit is a behavior change even if the model name stays fixed. Record immutable revisions for the template, model, retrieval index, tool schema, output validator, decoding settings and fallback route. A provider alias may shift without a visible name change, so record the resolved model identity when available. [[mlops/inference-chain-contracts-and-stage-identity|Chain identity]] is the operational base for this manifest.'),
            ('Keep inputs and authority separate', 'Ticket text and retrieved manuals are task data, not policy instructions. The application should constrain tool access outside the prompt, validate requested tool arguments and prevent a generated sentence from authorizing actions. The release packet names permitted data scopes and any redaction step. Test malicious or malformed retrieved passages as inputs; a successful output-format check cannot prove the content is trustworthy. [[mlops/inference-logging-privacy|Logging privacy]] limits retention of sensitive ticket text and generated responses.'),
            ('Use a stable response contract', 'Define required fields, allowed enum values, maximum lengths and what happens when generation is incomplete or invalid. Validate output after the model returns; do not assume a prompt instruction guarantees JSON or correct field semantics. Keep an explicit abstain or human-review state for unsupported claims. A retry should preserve the same release manifest and idempotency key. [[mlops/inference-request-response-contracts|Request contracts]] protect callers when the output schema changes.'),
            ('Promote and roll back as a bundle', 'Evaluate the whole manifest, then stage a cohort whose outputs are observable under privacy rules. A rollback must restore prompt, model selection, retrieval index and tool contract together, or the prior prompt may query an incompatible tool. [[mlops/generative-evaluation-and-abstention-gates|Evaluation gates]] test quality and failure behavior, while [[mlops/maintenance-summary-release-project|the project]] catches a stale retrieval index after a prompt update.'),
        ],
        'code': '''def generative_manifest_ready(release, available):
    required = {"prompt_revision", "model_revision", "index_revision",
                "tool_schema_revision", "output_schema_revision"}
    if set(release) != required or any(not release[name] for name in required):
        return "hold:incomplete-manifest"
    for name in required:
        if release[name] not in available[name]:
            return "hold:missing-" + name
    return "stage:bundle"

release = {"prompt_revision": "summary-p47", "model_revision": "text-r8",
           "index_revision": "manuals-i31", "tool_schema_revision": "ticket-t4",
           "output_schema_revision": "summary-s3"}
available = {name: {value} for name, value in release.items()}
assert generative_manifest_ready(release, available) == "stage:bundle"
assert generative_manifest_ready({**release, "index_revision": "manuals-i30"},
                                 available) == "hold:missing-index_revision"
''',
        'cost': 'Manifest validation is O(k) expected time and O(k) temporary space for k components. Evaluation and staged serving cost model tokens, retrieval queries, tool calls and human review. Treating every component as a versioned release increases bookkeeping but prevents a prompt-only rollback from leaving an incompatible index or tool contract live.',
        'mistakes': ['Pinning the model while leaving the prompt and index mutable.', 'Treating retrieved text as instructions with the same authority as application policy.', 'Assuming prompted JSON removes the need for output validation.', 'Rolling back the prompt without restoring its tool and retrieval dependencies.'],
        'related': [M + 'generative-evaluation-and-abstention-gates', M + 'maintenance-summary-release-project', M + 'inference-chain-contracts-and-stage-identity', M + 'inference-request-response-contracts', M + 'inference-logging-privacy'],
    },
    {
        'path': M + 'generative-evaluation-and-abstention-gates',
        'title': 'Generative evaluation gates: grounded claims, schemas and abstention',
        'module': G, 'project': False,
        'summary': 'A generative release needs task-specific checks and a defined failure route, not one aggregate judge score.',
        'sections': [
            ('Build cases from the real task', 'For a maintenance-ticket summarizer, include short and long tickets, conflicting technician notes, outdated manual pages, missing evidence and attempts to steer the assistant through retrieved text. Freeze the input snapshot and expected constraints. A generated summary can be fluent while inventing a part number or safety instruction. Use deterministic validators for schema and allowed fields, and independent human review for factual claims that need judgment. [[mlops/generative-release-manifest-and-prompt-model-binding|The release manifest]] makes comparisons repeatable.'),
            ('Separate gate types', 'Measure valid output rate, unsupported-claim rate, abstention when evidence is absent, tool-call correctness, privacy leakage, latency and cost. An automated grader can help prioritize review but may share blind spots with the model; keep a sampled human adjudication lane and a protected held-out set. Do not optimize a prompt repeatedly against the final gate cases. [[mlops/slice-quality-gates-and-uncertainty|Slice uncertainty]] applies when only a few cases exercise a rare failure.'),
            ('Test the no-answer path', 'When the manual index has no matching section, the system should state the gap and route the ticket to a technician. Do not make up a source citation or force a confident answer. Validate that an empty retrieval result, tool timeout or invalid JSON produces the defined fallback within the request deadline. [[mlops/stage-deadline-and-degraded-path-tests|Degraded-path tests]] cover latency and component failure; the evaluation gate checks whether the user-facing result remains safe and useful.'),
            ('Compare releases on fixed inputs', 'Run the old and candidate bundles with the same input set and record both outputs, resolved model identities and costs. Because text generation can vary, compare distributions and adjudicated failures rather than exact string equality alone. Stage a small cohort after offline gates, watch unsupported claims and human escalations, then promote or roll back the complete bundle. [[mlops/maintenance-summary-release-project|The project]] holds a candidate that improves formatting yet misstates a maintenance interval.'),
        ],
        'code': '''def summary_release_gate(metrics, limits):
    if metrics["evaluated"] < limits["minimum_evaluated"]:
        return "hold:coverage"
    if metrics["schema_failures"] > limits["schema_failures"]:
        return "hold:schema"
    if metrics["unsupported_claims"] > limits["unsupported_claims"]:
        return "hold:claims"
    if metrics["missing_evidence_abstentions"] < limits["minimum_abstentions"]:
        return "hold:abstention"
    return "stage:reviewed-bundle"

limits = {"minimum_evaluated": 470, "schema_failures": 2,
          "unsupported_claims": 0, "minimum_abstentions": 39}
metrics = {"evaluated": 500, "schema_failures": 1,
           "unsupported_claims": 0, "missing_evidence_abstentions": 41}
assert summary_release_gate(metrics, limits) == "stage:reviewed-bundle"
assert summary_release_gate({**metrics, "unsupported_claims": 1}, limits) == \
       "hold:claims"
''',
        'cost': 'The gate is O(1) time and space after evaluation. Generating paired outputs costs roughly two candidate runs per case, plus retrieval and review work. A zero-unsupported-claim target in a finite test set does not prove the true rate is zero; report sample size, adjudication quality and uncertainty beside the gate.',
        'mistakes': ['Using one subjective score to replace schema and factual checks.', 'Tuning on the held-out release set until the score passes.', 'Treating a fluent answer as evidence that its maintenance claim is supported.', 'Omitting empty-retrieval and tool-timeout cases from release tests.'],
        'related': [M + 'generative-release-manifest-and-prompt-model-binding', M + 'maintenance-summary-release-project', M + 'stage-deadline-and-degraded-path-tests', M + 'slice-quality-gates-and-uncertainty', M + 'inference-cost-ledger-and-allocation'],
    },
    {
        'path': M + 'maintenance-summary-release-project',
        'title': 'Project: release a maintenance-ticket summarizer with evidence gates',
        'module': G, 'project': True,
        'summary': 'Version a prompt, model and manual index together, reject unsupported instructions and stage a reversible summarizer release.',
        'sections': [
            ('Freeze the bundle', 'A service team wants short summaries of equipment maintenance tickets. The application retrieves approved manual excerpts and reads ticket metadata through a limited tool. Pin the prompt revision, resolved model revision, manual-index snapshot, tool schema, output schema and fallback policy. Separate instructions from untrusted ticket text and retrieved excerpts. [[mlops/generative-release-manifest-and-prompt-model-binding|The manifest]] is the release unit; a prompt edit alone is not the complete change.'),
            ('Build the evaluation packet', 'Assemble 500 cases with old and current manuals, conflicting notes, missing serial numbers, empty retrieval and a malicious sentence embedded in a ticket. Validate JSON fields and allowed enums mechanically. Have qualified reviewers check safety-relevant claims and whether the summary points to the evidence actually provided. When no manual passage supports an instruction, the system must abstain and send the ticket to a technician. [[mlops/generative-evaluation-and-abstention-gates|The gate]] separates format, groundedness and fallback behavior.'),
            ('Find the hidden regression', 'The candidate prompt produces shorter summaries and fewer formatting failures. Yet it uses a stale manual index that still contains an older maintenance interval. A global preference score rises while one unsupported instruction appears in a high-risk slice. Hold the bundle, rebuild the index from approved manuals and repeat the frozen test without editing the held-out cases. Check that the tool call remains within the ticket’s authorized scope. [[mlops/inference-logging-privacy|Privacy controls]] prohibit copying raw ticket text into unrestricted diagnostics.'),
            ('Stage the corrected release', 'Deploy a small technician cohort, log bundle identity and validation status, and sample output review under the permitted retention policy. Watch abstention, manual escalations, unsupported claims, p99 latency and cost. A rollback restores the prior prompt, model, index and tool contract together. Publish the evaluation limits: five hundred cases and a clean reviewed sample are evidence for a controlled release, not a promise of error-free generation. [[mlops/promotion-attestation-and-reversible-pointer|Reversible promotion]] should name the exact prior bundle.'),
        ],
        'code': '''def maintenance_summary_disposition(bundle, validated, review):
    required = {"prompt", "model", "manual_index", "tool_schema"}
    if any(not bundle.get(name) for name in required):
        return "hold:bundle-incomplete"
    if not validated["schema_ok"] or not validated["tool_scope_ok"]:
        return "hold:contract"
    if review["unsupported_instructions"]:
        return "hold:unsupported-claim"
    if not review["abstains_without_evidence"]:
        return "hold:missing-abstention"
    return "stage:technician-cohort"

bundle = {"prompt": "p47", "model": "text-r8",
          "manual_index": "manuals-i31", "tool_schema": "ticket-t4"}
validated = {"schema_ok": True, "tool_scope_ok": True}
review = {"unsupported_instructions": 0, "abstains_without_evidence": True}
assert maintenance_summary_disposition(bundle, validated, review) == \
       "stage:technician-cohort"
assert maintenance_summary_disposition(bundle, validated,
       {**review, "unsupported_instructions": 1}) == "hold:unsupported-claim"
''',
        'cost': 'The release decision is O(1) time and space, but evaluation requires generation, retrieval, tool calls and expert adjudication over many cases. Staged sampling adds review cost and reduces rollout speed. Those costs are preferable to a prompt change that silently pairs with stale manuals and produces an unsupported maintenance instruction.',
        'mistakes': ['Shipping the new prompt against an old manual index.', 'Using format success as a substitute for factual review.', 'Letting ticket text request unauthorized tool actions.', 'Rolling back only the prompt after discovering an index regression.'],
        'related': [M + 'generative-release-manifest-and-prompt-model-binding', M + 'generative-evaluation-and-abstention-gates', M + 'inference-logging-privacy', M + 'promotion-attestation-and-reversible-pointer', M + 'stage-deadline-and-degraded-path-tests'],
    },
]

crosslinks = [
    (M + 'edge-model-manifests-and-cohort-rollouts', M + 'federated-round-eligibility-and-update-identity'),
    (M + 'training-source-admission-and-quarantine', M + 'federated-aggregation-dropout-and-privacy-boundary'),
    (M + 'edge-offline-telemetry-and-rollback', M + 'scanner-federated-round-project'),
    (M + 'inference-chain-contracts-and-stage-identity', M + 'generative-release-manifest-and-prompt-model-binding'),
    (M + 'stage-deadline-and-degraded-path-tests', M + 'generative-evaluation-and-abstention-gates'),
    (M + 'inference-logging-privacy', M + 'maintenance-summary-release-project'),
]

if __name__ == '__main__':
    publish(lessons, (F, G), crosslinks,
            'aitrove-mlops-federated-generative-import-20261006.json', 6196,
            subject='mlops', hub_path=M + 'mlops-tutorial')
