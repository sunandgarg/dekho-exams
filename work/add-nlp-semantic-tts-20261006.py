"""Add structured-query parsing and speech-input preparation modules to NLP."""
from de_batch_publisher import publish

N = 'natural-language-processing/'
Q = 'Natural language to governed queries'
S = 'Text preparation for speech output'

lessons = [
    {
        'path': N + 'natural-language-query-intent-and-schema-grounding',
        'title': 'Natural-language queries: intent, schema grounding and ambiguity',
        'module': Q, 'project': False,
        'summary': 'Convert a user question into a typed, reviewable query plan before any database syntax or execution is considered.',
        'sections': [
            ('Separate wording from data shape', '“Show gateway-west incidents after the rollout” expresses a dataset, service filter and time boundary. It does not name a table or prove which rollout is meant. Map each phrase to an approved semantic field, operator and typed value. Store the original question and the schema version that supplied the mapping. If “rollout” could mean two release events, ask for clarification rather than inventing a date. [[natural-language-processing/entity-link-candidates-and-nil-decision|Entity linking with a NIL decision]] offers the same discipline for an ambiguous service name.'),
            ('Ground fields in a governed catalog', 'A model may propose a plausible column that is absent, sensitive or semantically wrong. The application should accept only published field IDs from a catalog that states type, access level and allowed operations. A free-text “customer” field may mean account owner, ticket submitter or affected tenant; choosing one silently changes the answer. Keep the mapping from question span to field ID for review. [[natural-language-processing/quantity-span-unit-and-range-contract|Quantity and unit contracts]] matter when a question asks for duration or a numeric threshold.'),
            ('Treat uncertainty as a plan state', 'Validate required slots before compiling anything: dataset, allowed projection, filters, time range and row limit. Mark unsupported aggregation or missing entity identity as unresolved. Do not let an untrusted document define new schema names or permissions. A typed plan allows the execution layer to reject unsafe operations without trying to understand arbitrary generated SQL. [[natural-language-processing/retrieved-text-instruction-authority-boundary|Retrieved-text trust]] keeps runbook prose from becoming query authority.'),
            ('Evaluate semantic correctness', 'Exact string comparison between SQL queries can punish equivalent plans, while one matching result on a small fixture can reward an accidental filter. Review the intended field bindings and test execution on cases that distinguish close interpretations. Include aliases, date boundaries, null values and users with different access scopes. The [[natural-language-processing/read-only-query-compilation-and-scope|compiler lesson]] checks the plan against an allowlist; the [[natural-language-processing/incident-query-semantic-parse-project|project]] checks answer behavior end to end.'),
        ],
        'code': '''def validate_incident_plan(plan, allowed_fields):
    if plan.get("dataset") != "incidents":
        return {"state": "review", "reason": "unknown-dataset"}
    if not plan.get("service_id") or not plan.get("after_utc"):
        return {"state": "review", "reason": "missing-constraint"}
    projection = plan.get("projection", [])
    if not projection or any(field not in allowed_fields for field in projection):
        return {"state": "review", "reason": "field-scope"}
    if plan.get("limit", 0) not in range(1, 48):
        return {"state": "review", "reason": "row-limit"}
    return {"state": "validated", "plan": dict(plan)}

candidate = {"dataset": "incidents", "service_id": "gateway-west",
             "after_utc": "2026-09-27T00:00:00Z",
             "projection": ["incident_id", "opened_at"], "limit": 47}
assert validate_incident_plan(candidate,
                              {"incident_id", "opened_at"})["state"] == "validated"
assert validate_incident_plan({**candidate, "projection": ["secret_note"]},
                              {"incident_id", "opened_at"})["state"] == "review"
''',
        'cost': 'Checking p projected fields takes expected O(p) time and O(p) space for the returned plan copy. This example checks shape and field names, not timestamp validity or user authorization. A production boundary must parse typed values, bind the authenticated principal and reject unsupported operations before database access.',
        'mistakes': ['Treating a plausible generated column name as a real schema field.', 'Guessing an ambiguous rollout date.', 'Calling a plan safe because its SQL parses.', 'Letting retrieved text or model output expand the user’s field access.'],
        'related': [N + 'read-only-query-compilation-and-scope', N + 'incident-query-semantic-parse-project', N + 'entity-link-candidates-and-nil-decision', N + 'quantity-span-unit-and-range-contract', N + 'retrieved-text-instruction-authority-boundary'],
    },
    {
        'path': N + 'read-only-query-compilation-and-scope',
        'title': 'Read-only query compilation: identifiers, parameters and scope',
        'module': Q, 'project': False,
        'summary': 'Compile only validated semantic fields into a parameterized read-only query with a fixed tenant and row boundary.',
        'sections': [
            ('Compile from approved identifiers', 'Database drivers parameterize values, not table and column identifiers. Map each semantic field to an approved physical column; never paste a model-supplied identifier into SQL. Build the query shape from a small allowlisted grammar and bind service, time and tenant values as parameters. The compiled statement should be read-only and carry a hard result limit. [[natural-language-processing/natural-language-query-intent-and-schema-grounding|Typed plans]] provide the input contract that makes this compiler manageable.'),
            ('Bind access beyond the prompt', 'A user asking for all incidents does not gain access to another tenant because the model phrased the request confidently. Derive tenant and role from authenticated application state, not from the natural-language question. Filter rows at the database boundary and consider column-level policy for fields such as personal notes. A retrieved runbook cannot authorize a broader query. [[natural-language-processing/trusted-action-gate-and-retrieval-audit|Trusted action gates]] apply the same separation to effectful tools.'),
            ('Constrain cost and cardinality', 'A harmless SELECT can still scan a huge table or return too much private data. Require a bounded time window, row cap and indexed filter where the product needs them. Estimate or reject expensive plans before execution. A count question and a row-list question have different result types and should not share an improvised compiler path. Keep query timeout, logging and pagination policy outside generated prose. The example below shows a single approved row-list shape rather than claiming to handle arbitrary SQL.'),
            ('Test with adversarial wording', 'Try quoted SQL fragments, nonexistent fields, alternate service aliases, null timestamps and limit requests above policy. Verify the resulting statement and parameters, plus returned rows under two tenant identities. Compare semantic answers, not only whether the query executed. The [[natural-language-processing/incident-query-semantic-parse-project|incident query project]] includes an ambiguous question that must stop for clarification before any statement is compiled.'),
        ],
        'code': '''ALLOWED_COLUMNS = {"incident_id": "incident_id",
                   "opened_at": "opened_at", "status": "status"}

def compile_incident_rows(plan, tenant_id):
    if not tenant_id or plan["dataset"] != "incidents":
        raise ValueError("authorized tenant and dataset are required")
    fields = plan["projection"]
    if not fields or any(field not in ALLOWED_COLUMNS for field in fields):
        raise ValueError("unknown or disallowed projection")
    if not 1 <= plan["limit"] <= 47:
        raise ValueError("limit outside policy")
    columns = ", ".join(ALLOWED_COLUMNS[field] for field in fields)
    statement = (f"SELECT {columns} FROM incidents "
                 "WHERE tenant_id = ? AND service_id = ? "
                 "AND opened_at >= ? ORDER BY opened_at DESC LIMIT ?")
    parameters = (tenant_id, plan["service_id"],
                  plan["after_utc"], plan["limit"])
    return statement, parameters

plan = {"dataset": "incidents", "projection": ["incident_id"],
        "service_id": "gateway-west", "after_utc": "2026-09-27T00:00:00Z",
        "limit": 47}
sql, values = compile_incident_rows(plan, "tenant-82")
assert "tenant_id = ?" in sql and values[0] == "tenant-82"
assert "gateway-west" not in sql
''',
        'cost': 'Compiling p projected columns takes O(p) time and space for the statement. Database work depends on indexes, selectivity and returned rows; a tenant-service-time index can avoid a full scan for this shape. This code returns a statement and parameters but does not establish an authenticated connection or enforce database-level row policy by itself.',
        'mistakes': ['Interpolating model-supplied column names into SQL.', 'Trusting a tenant ID supplied by the question.', 'Assuming a SELECT cannot overload a database.', 'Using parameter placeholders for values while leaving identifiers unchecked.'],
        'related': [N + 'natural-language-query-intent-and-schema-grounding', N + 'incident-query-semantic-parse-project', N + 'trusted-action-gate-and-retrieval-audit', N + 'quantity-span-unit-and-range-contract', N + 'classification-slices-and-abstention'],
    },
    {
        'path': N + 'incident-query-semantic-parse-project',
        'title': 'Project: answer an incident question through a governed query plan',
        'module': Q, 'project': True,
        'summary': 'Parse an operational question into approved fields, compile a bounded tenant-scoped query and hold ambiguous or unauthorized requests.',
        'sections': [
            ('Define the fixture', 'An operator asks for gateway-west incidents opened after a specific rollout. The system must identify the rollout event and translate its approved timestamp into a read-only incident filter. Add a second rollout with a similar name, a restricted notes field and a request for too many rows. The ambiguous rollout should produce a clarification request, not a guessed time boundary. [[natural-language-processing/natural-language-query-intent-and-schema-grounding|Semantic grounding]] maps words to known fields and values.'),
            ('Build the contract', 'Annotators provide the intended dataset, service, time boundary, projection and expected result type for each question. Record schema version and user role. Freeze a small database fixture with cases that distinguish wrong service, wrong rollout and wrong tenant. Keep data synthetic but realistic enough to expose a missing filter. A match on a trivial one-row database would not validate the plan. Group paraphrased questions by intent family before model evaluation.'),
            ('Execute behind a boundary', 'Validate the plan shape and user scope, compile identifiers from an allowlist, bind values and enforce a limit. Use a read-only database identity with its own row policy. Log the semantic plan and compiled query shape without storing unnecessary private result data. [[natural-language-processing/read-only-query-compilation-and-scope|Safe compilation]] prevents raw model text from becoming SQL; the application must still verify the result against the user’s question.'),
            ('Gate the release', 'Report field-link errors, ambiguous questions correctly held, unauthorized-column attempts, tenant leaks, result correctness and query cost. Review both the generated plan and actual rows. A correct SQL string can still represent the wrong interpretation. The code below checks an approved plan and scope before compilation; a production release also tests the database’s independent access controls.'),
        ],
        'code': '''def admit_incident_query(plan, user_scope):
    if plan.get("state") != "validated":
        return {"state": "clarify-or-review"}
    request = plan["plan"]
    if request["service_id"] not in user_scope["service_ids"]:
        return {"state": "deny", "reason": "service-scope"}
    if set(request["projection"]) - user_scope["field_ids"]:
        return {"state": "deny", "reason": "field-scope"}
    return {"state": "eligible-for-read", "tenant_id": user_scope["tenant_id"]}

validated = {"state": "validated", "plan": {
    "service_id": "gateway-west", "projection": ["incident_id"]}}
scope = {"tenant_id": "tenant-82", "service_ids": {"gateway-west"},
         "field_ids": {"incident_id", "opened_at"}}
assert admit_incident_query(validated, scope) == {
    "state": "eligible-for-read", "tenant_id": "tenant-82"}
assert admit_incident_query({"state": "unresolved"}, scope)["state"] == \
    "clarify-or-review"
''',
        'cost': 'Checking s permitted services and p projected fields is expected O(p) time with O(p) temporary space for the set difference. Actual query cost depends on database indexes and cardinality. The eligible state is not execution; separate authentication, read-only credentials and result checks remain mandatory.',
        'mistakes': ['Executing a plan that still contains an ambiguous rollout.', 'Using a model-supplied tenant value.', 'Testing only SQL syntax instead of returned rows and user intent.', 'Treating an application field allowlist as a substitute for database access policy.'],
        'related': [N + 'natural-language-query-intent-and-schema-grounding', N + 'read-only-query-compilation-and-scope', N + 'entity-link-candidates-and-nil-decision', N + 'trusted-action-gate-and-retrieval-audit', N + 'grouped-temporal-text-validation'],
    },
    {
        'path': N + 'speech-text-normalization-and-unit-reading',
        'title': 'Speech input text: expand numbers, units and protected tokens',
        'module': S, 'project': False,
        'summary': 'Written text is not a complete speech script. Expand ambiguous numbers and units under a locale policy while protecting service identifiers.',
        'sections': [
            ('Separate display text from spoken form', 'A dashboard may display “gateway-west: 47 ms,” but a spoken alert should name the service and say “forty-seven milliseconds” under a declared language policy. Store both the original text and the reviewed spoken form; do not overwrite the written value. A bare “47” could be an incident ID, count, time or version. Its surrounding field type determines the expansion. [[natural-language-processing/quantity-span-unit-and-range-contract|Quantity contracts]] preserve value and unit before any speech rendering.'),
            ('Protect names and commands', 'Service names, acronyms, paths and commands can sound misleading when an engine guesses pronunciation. Keep protected spans with typed roles and locale-specific readings approved by owners. A command shown in a runbook may need character-by-character reading or may be omitted from speech entirely if reading it would be unsafe. [[natural-language-processing/abbreviation-definition-scope-and-collisions|Abbreviation scope]] helps distinguish a product acronym from an ordinary word.'),
            ('Treat normalization as a versioned transform', 'The same text can require different spoken forms by locale, voice or product policy. Record normalization rules, lexicon version and source text revision so generated audio can be reproduced and corrected. If a value or term is unknown, route it to a pronunciation review queue rather than silently guessing. Keep offsets from original text to speech segments for captions and incident audit. [[natural-language-processing/unicode-normalization-and-source-offsets|Source offsets]] prevent a cleaned string from losing its link to the displayed record.'),
            ('Evaluate meaning and intelligibility', 'Test numbers, decimals, units, dates, identifiers, abbreviations and mixed-language terms. Human listeners should verify the spoken value and service name, not merely rate naturalness. A pleasant voice can still read “ms” as an unrelated word or reverse a threshold. The [[natural-language-processing/pronunciation-lexicon-version-and-review|lexicon lesson]] controls domain words; the [[natural-language-processing/operational-alert-speech-project|project]] gates critical alert audio.'),
        ],
        'code': '''def spoken_metric(metric, locale):
    readings = {("en", "ms"): "milliseconds",
                ("en", "min"): "minutes"}
    if not isinstance(metric["value"], int):
        return {"state": "review", "reason": "unsupported-value"}
    unit = readings.get((locale, metric["unit"]))
    if unit is None:
        return {"state": "review", "reason": "unknown-unit"}
    return {"state": "ready", "spoken_text":
            f"{metric['value']} {unit}", "display_value":
            f"{metric['value']} {metric['unit']}"}

assert spoken_metric({"value": 47, "unit": "ms"}, "en") == {
    "state": "ready", "spoken_text": "47 milliseconds",
    "display_value": "47 ms"}
assert spoken_metric({"value": 82, "unit": "ms"}, "hi")["state"] == "review"
''',
        'cost': 'A fixed lookup and integer check are expected O(1) time and space, excluding output-string length. This example expands a unit but leaves number-to-words conversion to a locale-aware speech engine or reviewed formatter. Never assume its default pronunciation is correct for critical values or identifiers.',
        'mistakes': ['Replacing display text with spoken text and losing source fidelity.', 'Reading every number as a count without field context.', 'Guessing a service pronunciation from spelling alone.', 'Reusing audio after the underlying threshold or lexicon changed.'],
        'related': [N + 'pronunciation-lexicon-version-and-review', N + 'operational-alert-speech-project', N + 'quantity-span-unit-and-range-contract', N + 'abbreviation-definition-scope-and-collisions', N + 'unicode-normalization-and-source-offsets'],
    },
    {
        'path': N + 'pronunciation-lexicon-version-and-review',
        'title': 'Pronunciation lexicons: locale, domain terms and review',
        'module': S, 'project': False,
        'summary': 'A domain pronunciation rule needs an owner, locale, source revision and audible review before it is used for operational speech.',
        'sections': [
            ('Model a term as more than spelling', 'The string “SRE” may be read as separate letters, while a service name may have an approved spoken alias. Store token or phrase, language, pronunciation representation, context scope, owner and lexicon revision. A single global replacement may corrupt ordinary words that share the same letters. Use longest approved phrase matches under explicit boundaries, then send unmatched technical terms for review. [[natural-language-processing/speech-text-normalization-and-unit-reading|Text normalization]] decides the unit and identifier roles before this pronunciation lookup.'),
            ('Version changes against audio', 'When a team renames gateway-west, old audio may still use the former name. Keep the source text revision, lexicon revision and synthesis engine version on each audio artifact. Invalidate or re-record affected alerts when any of these change. Reviewers should hear the full phrase, because a token-level pronunciation can be correct in isolation and confusing in context. [[natural-language-processing/passage-revision-and-index-audit|Revision auditing]] uses a similar dependency idea for text search.'),
            ('Handle mixed language carefully', 'A Hindi sentence can contain an English service ID. Choose pronunciation per span, not per whole message, and keep the original identifier visible in captions. If the language switch is uncertain, ask a reviewer or use a safe explicit spelling policy. A lexicon entry is not proof that the whole sentence has correct accent, timing or meaning. [[natural-language-processing/script-profile-and-code-switching-boundary|Code-switching analysis]] informs the segment policy.'),
            ('Audit by listening', 'Measure term pronunciation accuracy, value accuracy, listener comprehension and mismatch between caption and speech. Include new services, abbreviations with collisions and low-volume locales. A word error rate computed by an automatic transcriber can help triage but cannot replace a targeted listening check for a critical threshold. The [[natural-language-processing/operational-alert-speech-project|operational alert project]] keeps an approved audio manifest and a rollback path.'),
        ],
        'code': '''def approved_pronunciation(term, locale, lexicon):
    entry = lexicon.get((locale, term))
    if entry is None or entry["review_state"] != "approved":
        return {"state": "review", "term": term, "locale": locale}
    return {"state": "ready", "term": term, "locale": locale,
            "spoken_form": entry["spoken_form"],
            "lexicon_revision": entry["revision"]}

lexicon = {("en", "SRE"): {"spoken_form": "S R E",
                             "review_state": "approved", "revision": "lex-r8"},
           ("en", "gateway-west"): {"spoken_form": "gateway west",
                                     "review_state": "pending", "revision": "lex-r8"}}
assert approved_pronunciation("SRE", "en", lexicon)["spoken_form"] == "S R E"
assert approved_pronunciation("gateway-west", "en", lexicon)["state"] == "review"
''',
        'cost': 'One dictionary lookup is expected O(1) time and space for a term. Scanning an utterance for many phrases requires tokenization and a match index; a naive scan over t terms and n tokens can cost O(t × n). A reviewed lexicon improves named terms but does not validate the speech engine’s complete output.',
        'mistakes': ['Applying a global string replacement without token boundaries.', 'Using a pending pronunciation in a critical alert.', 'Forgetting to regenerate audio after a lexicon revision.', 'Scoring naturalness while ignoring whether the service name was understood.'],
        'related': [N + 'speech-text-normalization-and-unit-reading', N + 'operational-alert-speech-project', N + 'abbreviation-definition-scope-and-collisions', N + 'script-profile-and-code-switching-boundary', N + 'asr-transcript-segments-and-entity-risk'],
    },
    {
        'path': N + 'operational-alert-speech-project',
        'title': 'Project: release a spoken operational alert with reviewed values',
        'module': S, 'project': True,
        'summary': 'Prepare a short incident alert for speech, verify units and service pronunciation, and block stale or unreviewed audio.',
        'sections': [
            ('Set the alert task', 'An operator must hear that gateway-west latency reached 47 milliseconds and that the rollback wait is 82 minutes. The displayed alert retains exact identifiers and values. The spoken script expands units, uses approved service pronunciation and preserves the two different measurements. Include an older 47-minute rollback rule to expose stale audio. [[natural-language-processing/speech-text-normalization-and-unit-reading|Speech text normalization]] determines how each typed value is read.'),
            ('Build a review fixture', 'Store source event and runbook passage IDs, source revisions, locale, typed values, protected terms, lexicon revision and generated audio version. Add cases with an unknown abbreviation, a changed threshold, a mixed-language sentence and a caption mismatch. Reviewers listen without seeing a presumed correct transcript, then compare what they heard with the source record. A synthetic audio preview is not a substitute for an actual listening check in the target environment.'),
            ('Check dependencies', 'Only approved normalization and pronunciation entries may enter critical audio. When the runbook threshold or lexicon changes, invalidate the old artifact and regenerate. Preserve the audio and script under their versions for audit, but do not serve a stale version. [[natural-language-processing/pronunciation-lexicon-version-and-review|Lexicon review]] governs domain terms; [[natural-language-processing/numeric-claim-calculation-and-evidence|numeric evidence checks]] verify the source value before it is spoken.'),
            ('Gate the release', 'Compare spoken values with source values, confirm service identity, check caption alignment and collect listener comprehension results by locale. Block release if any critical value or protected term is unreviewed. The code below verifies the artifact manifest, not the wave form; final acceptance still requires listening to the generated audio and testing it on the intended device.'),
        ],
        'code': '''def audio_release_state(artifact, active_source, active_lexicon):
    pending = []
    if artifact["source_revision"] != active_source:
        pending.append("source-revision")
    if artifact["lexicon_revision"] != active_lexicon:
        pending.append("lexicon-revision")
    if not artifact["values_reviewed"]:
        pending.append("value-review")
    if not artifact["listening_reviewed"]:
        pending.append("listening-review")
    return {"state": "hold" if pending else "ready",
            "pending": pending}

audio = {"source_revision": "runbook-r8", "lexicon_revision": "lex-r8",
         "values_reviewed": True, "listening_reviewed": False}
assert audio_release_state(audio, "runbook-r8", "lex-r8") == {
    "state": "hold", "pending": ["listening-review"]}
audio["listening_reviewed"] = True
assert audio_release_state(audio, "runbook-r8", "lex-r8")["state"] == "ready"
''',
        'cost': 'This fixed-field manifest check is O(1) time and space. Speech synthesis, audio storage and human listening cost depend on duration, locales and revisions. A ready manifest only records completed checks; it cannot prove the audio sounded correct unless the listening result was collected and tied to this exact artifact version.',
        'mistakes': ['Reading “ms” as an unreviewed abbreviation.', 'Serving audio from an old rollback threshold.', 'Accepting a correct transcript without listening to the audio.', 'Changing the service name in speech while leaving the caption unchanged.'],
        'related': [N + 'speech-text-normalization-and-unit-reading', N + 'pronunciation-lexicon-version-and-review', N + 'quantity-span-unit-and-range-contract', N + 'numeric-claim-calculation-and-evidence', N + 'support-call-transcript-review-project'],
    },
]

crosslinks = [
    (N + 'entity-link-candidates-and-nil-decision', N + 'natural-language-query-intent-and-schema-grounding'),
    (N + 'trusted-action-gate-and-retrieval-audit', N + 'read-only-query-compilation-and-scope'),
    (N + 'incident-claim-verification-project', N + 'incident-query-semantic-parse-project'),
    (N + 'quantity-span-unit-and-range-contract', N + 'speech-text-normalization-and-unit-reading'),
    (N + 'abbreviation-registry-version-and-reindex', N + 'pronunciation-lexicon-version-and-review'),
    (N + 'support-call-transcript-review-project', N + 'operational-alert-speech-project'),
]

if __name__ == '__main__':
    publish(lessons, (Q, S), crosslinks,
            'aitrove-nlp-semantic-tts-import-20261006.json', 4878,
            subject='natural-language-processing', hub_path=N + 'nlp-tutorial')
