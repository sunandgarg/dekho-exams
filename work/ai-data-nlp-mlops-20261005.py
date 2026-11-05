"""Add original NLP and MLOps curricula to the local AI & Data preview."""
import datetime
import html
import json
from pathlib import Path
import re
import uuid

root = Path(__file__).resolve().parents[1]
fixture = root / 'src/data/fixtures.json'
rows = json.loads(fixture.read_text())
rows = [row for row in rows if not row['path'].startswith(('natural-language-processing/', 'mlops/'))]
by_path = {row['path']: row for row in rows}
stamp = datetime.datetime.now(datetime.UTC).isoformat()

def prose(value):
    return re.sub(r'\[\[([^|]+)\|([^\]]+)\]',
                  lambda match: '<a href="/' + match[1] + '">' + match[2] + '</a>',
                  html.escape(value))

lessons = [
 dict(path='natural-language-processing/corpus-identity-and-label-policy', title='Text corpus contracts: identity, label timing and annotation rules',
      summary='A text corpus needs stable document identity, a prediction clock and a label policy before tokenization or model fitting.',
      sections=[
       ('Define one document', 'A support ticket can contain an original message, replies and internal notes. Decide whether one record means a ticket at submission or a later conversation snapshot. Stable ticket IDs and revision numbers keep edits from becoming unrelated examples. Record created, observed and labeled times separately. If the model routes a ticket at submission, a later agent note cannot be a training feature. [[machine-learning/prediction-time-feature-availability|Feature availability]] is the same boundary in tabular models.'),
       ('Write the label rule', 'Define categories by the action they trigger, not by vague language. A billing question and a refund request may mention the same words but require different queues. Specify which label wins when multiple requests occur, or use a multi-label target. Store annotator identity, guideline version and disagreement resolution. Unknown and ambiguous cases should remain visible; forcing every case into a confident class hides policy uncertainty.'),
       ('Control sensitive text', 'Raw tickets can contain names, account numbers and attachments. Limit access, remove or mask only under a versioned policy, and retain enough governed provenance to audit errors. A blanket digit deletion can remove invoice codes that distinguish tasks. [[natural-language-processing/unicode-tokenization-boundary|Normalization]] should preserve task-critical characters and must be applied consistently at training and serving.'),
       ('Test the source contract', 'Create fixtures with one edited ticket, two tickets from one customer, a delayed label and a note added after the routing decision. Assert the intended record count and that no future text enters the model input. Review a small annotation disagreement sample before scaling data collection.')],
      code='def eligible_ticket(record, decision_time):\n    if not record.ticket_id or record.submitted_at > decision_time:\n        raise ValueError("invalid ticket identity or clock")\n    visible = [message.text for message in record.messages\n               if message.created_at <= decision_time\n               and message.visibility == "customer"]\n    if not visible:\n        raise ValueError("no customer text at decision time")\n    return "\\n".join(visible)',language='python',
      cost='Constructing one snapshot reads O(M) messages per ticket and copies O(C) characters. Retaining revisions increases storage; it also makes labels and prediction-time inputs auditable.',
      mistakes=['Do not merge later agent notes into a submission-time input.', 'Do not silently force ambiguous tickets into one category.', 'Do not discard ticket revisions before an audit policy is defined.'],
      related=['natural-language-processing/unicode-tokenization-boundary','natural-language-processing/grouped-temporal-text-validation','machine-learning/prediction-time-feature-availability','data-engineering/source-contract-and-raw-landing']),
 dict(path='natural-language-processing/unicode-tokenization-boundary', title='Unicode and tokenization: preserve meaning at the text boundary',
      summary='Text preprocessing is a versioned transform that must preserve characters relevant to labels, spans and serving behavior.',
      sections=[
       ('Start with the task', 'Lowercasing, accent removal and punctuation deletion are choices, not automatic cleaning. An invoice code containing a hyphen may differ from one without it; negation can reverse a support request. Keep raw text and a versioned transformed representation. Test emoji, mixed scripts, composed accents, line breaks and ticket IDs before applying a global rule. [[natural-language-processing/corpus-identity-and-label-policy|The corpus contract]] decides which changes preserve meaning.'),
       ('Choose a token boundary', 'A word tokenizer, character n-grams and subword tokenizer create different vocabularies and unknown-token behavior. Record the tokenizer implementation, version, vocabulary and special-token map with the model. A model trained with one token map cannot safely serve another. For extraction tasks, keep a mapping from token positions back to original character offsets; normalized text may not have identical offsets.'),
       ('Measure what is lost', 'Count empty outputs, unknown tokens and lengths before and after truncation by language or channel. A maximum length of 256 units can cut a long ticket before the actual request; inspect where the answer sits. When truncating, state whether you keep the beginning, end or selected segments. [[natural-language-processing/span-offset-annotation|Span annotations]] need the original text coordinate system.'),
       ('Exercise edge cases', 'Use fixtures with a one-character ticket, a non-Latin message, combining marks and an unusually long message. Verify that each produces a deliberate output or a named rejection. Compare training and serving token IDs on the same raw bytes. A visual text match does not prove byte or token equality.')],
      code='import unicodedata\n\ndef normalize_ticket_text(raw_text):\n    if not isinstance(raw_text, str) or not raw_text.strip():\n        raise ValueError("empty ticket text")\n    normalized = unicodedata.normalize("NFC", raw_text)\n    normalized = " ".join(normalized.split())\n    if len(normalized) > 120_000:\n        raise ValueError("ticket exceeds processing limit")\n    return normalized',language='python',
      cost='Normalization scans O(C) characters and creates O(C) output storage. Tokenization is usually linear in input length but vocabulary lookup and long-sequence model cost depend on the chosen architecture.',
      mistakes=['Do not remove punctuation without checking task meaning.', 'Do not apply a new tokenizer to an old fitted model.', 'Do not interpret normalized offsets as raw-text offsets.'],
      related=['natural-language-processing/sparse-text-baseline','natural-language-processing/span-offset-annotation','deep-learning/tensor-shape-dtype-contract','natural-language-processing/text-serving-contract']),
 dict(path='natural-language-processing/sparse-text-baseline', title='Sparse text baselines: fit vocabulary inside the training boundary',
      summary='A sparse vectorizer and linear classifier form a measurable baseline when vocabulary and document-frequency statistics are fitted only on training text.',
      sections=[
       ('Use a baseline that can fail clearly', 'Represent support tickets with word or character features, then fit a linear classifier. Character n-grams can tolerate misspellings and invoice fragments; word features can be easier to inspect. Compare both only under the same split and metric. Do not jump to a larger model before knowing whether the task is separable with a modest representation. [[natural-language-processing/grouped-temporal-text-validation|The split]] determines whether a baseline score is credible.'),
       ('Keep fitting inside the fold', 'Vocabulary selection and inverse-document-frequency weights learn from text. Fitting them on the whole corpus before splitting leaks information from evaluation messages. Put vectorization and classification in one pipeline, and fit only on training records within each fold. At serving time, transform with the saved vectorizer; do not rebuild a vocabulary from requests.'),
       ('Interpret sparse evidence cautiously', 'A strong weight on a product code may reflect a useful routing rule or a temporary data artifact. Inspect high-weight terms and error cases by product and time slice. Short messages can become all-zero vectors if the token rule discards every term; define a fallback or abstain path. [[natural-language-processing/classification-slices-and-abstention|Slice evaluation]] exposes that failure.'),
       ('Record the comparison', 'Save vectorizer parameters, label order, split IDs and metric counts with the model. Compare against a majority-class and simple rules baseline. Report per-class precision and recall with denominators; a single accuracy number can hide a rare urgent queue.')],
      code='from sklearn.feature_extraction.text import TfidfVectorizer\nfrom sklearn.linear_model import LogisticRegression\nfrom sklearn.pipeline import make_pipeline\n\nticket_router = make_pipeline(\n    TfidfVectorizer(analyzer="char_wb", ngram_range=(3, 5), min_df=2),\n    LogisticRegression(max_iter=800, class_weight="balanced"),\n)\nticket_router.fit(training_texts, training_labels)\nvalidation_labels = ticket_router.predict(validation_texts)',language='python',
      cost='With N documents and Z nonzero features, sparse fitting scales mainly with Z and classifier iterations; dense conversion can require O(NV) memory for vocabulary size V. Measure matrix sparsity before changing models.',
      mistakes=['Do not fit vocabulary or IDF weights before splitting.', 'Do not rebuild the vectorizer at inference.', 'Do not report accuracy alone for a rare urgent class.'],
      related=['natural-language-processing/grouped-temporal-text-validation','natural-language-processing/classification-slices-and-abstention','machine-learning/leakage-safe-preprocessing-pipeline','natural-language-processing/text-serving-contract']),
 dict(path='natural-language-processing/grouped-temporal-text-validation', title='Text validation: split conversations, duplicates and time together',
      summary='A text evaluation partition must separate repeated conversations and future time, or near-duplicate wording can inflate the result.',
      sections=[
       ('Identify repeat exposure', 'One customer may reopen a ticket by copying an earlier description. Templates may also create many near-identical messages. Random document splitting can place the same phrasing on both sides and make memorization look like generalization. Group by conversation or customer according to the deployment question, and audit high-similarity cross-partition pairs. [[machine-learning/group-and-time-validation|Grouped validation]] provides the broader model-selection rule.'),
       ('Respect the prediction clock', 'A future validation window asks whether the classifier handles new products and language. Keep training before the cutoff, then apply an entity rule to prevent a customer conversation spanning both sides from leaking. When these constraints conflict, document excluded records and the resulting population. An evaluation with only historical random folds answers a different question.'),
       ('Handle delayed labels', 'Some tickets receive a final category days after submission. Select evaluation examples by submission time, but calculate metrics only when labels have matured under a fixed cutoff. Otherwise recent difficult cases can disappear and the apparent quality rises. [[mlops/drift-delayed-label-monitoring|Delayed-label monitoring]] uses the same maturity rule after launch.'),
       ('Audit the split itself', 'Report counts by label, language, customer and month. Confirm disjoint group IDs and inspect a bounded near-duplicate sample. If the urgent category is absent from one fold, do not conceal it by averaging the fold metric. Revisit the split design or collect more examples.')],
      code='def assert_ticket_split(training_rows, evaluation_rows):\n    training_conversations = {row.conversation_id for row in training_rows}\n    evaluation_conversations = {row.conversation_id for row in evaluation_rows}\n    if training_conversations & evaluation_conversations:\n        raise ValueError("conversation crosses evaluation boundary")\n    latest_training = max(row.submitted_at for row in training_rows)\n    earliest_evaluation = min(row.submitted_at for row in evaluation_rows)\n    if latest_training >= earliest_evaluation:\n        raise ValueError("future overlap in text split")',language='python',
      cost='Group and time checks are O(N) over ticket records with O(G) memory for G groups. Near-duplicate search is costlier than exact matching; blocking or approximate indexing avoids all-pairs O(N²) comparison.',
      mistakes=['Do not scatter replies from one conversation across partitions.', 'Do not score labels before their maturity cutoff.', 'Do not hide missing classes in a fold average.'],
      related=['natural-language-processing/corpus-identity-and-label-policy','natural-language-processing/sparse-text-baseline','natural-language-processing/classification-slices-and-abstention','machine-learning/group-and-time-validation']),
]

lessons.extend([
 dict(path='natural-language-processing/span-offset-annotation', title='Entity spans: align annotations to the original text',
      summary='An extraction label names a half-open character span in a specific text revision, with an explicit policy for overlap and normalization.',
      sections=[
       ('Store coordinates with identity', 'A ticket might mention an invoice ID, product and date. Store start and end character offsets against the exact raw text revision that annotators saw. If a later normalization collapses spaces, old offsets may point to different characters. Save the selected substring and a text hash beside offsets to catch drift. [[natural-language-processing/corpus-identity-and-label-policy|Corpus identity]] makes that pairing stable.'),
       ('Define overlap semantics', 'A product code may appear inside a longer order reference. Decide whether overlapping spans are allowed and whether nested labels are meaningful. If a model or library supports only non-overlapping entities, do not quietly drop valid nested annotations; change the representation or define a priority policy. State whether offsets count Unicode code points, bytes or another unit at every API boundary.'),
       ('Align without guessing', 'Token-based models need character spans mapped to token spans. A strict mapping may reject an annotation cutting through a token. A permissive expansion can change the labeled text. Count rejected alignments and inspect them before training. [[natural-language-processing/unicode-tokenization-boundary|Tokenization changes]] can alter these counts even when raw documents are unchanged.'),
       ('Evaluate exact and partial errors', 'Exact span match is strict; a prediction missing one character can be wrong even when its label looks right. Report exact boundary errors, wrong labels and missed spans separately. Add fixtures for repeated identical IDs in one ticket, punctuation next to an ID and a corrected ticket revision. A raw substring check prevents stale offsets from passing silently.')],
      code='def validate_span(ticket_text, start_char, end_char, selected_text):\n    if not (0 <= start_char < end_char <= len(ticket_text)):\n        raise ValueError("span outside ticket")\n    observed = ticket_text[start_char:end_char]\n    if observed != selected_text:\n        raise ValueError("annotation offsets no longer match text")\n    return {"start": start_char, "end": end_char, "text": observed}',language='python',
      cost='One span validation is O(L) for substring length L; validating S spans costs the total selected length. Token alignment adds tokenizer work over document length and storage for offset maps.',
      mistakes=['Do not reuse offsets after changing text normalization.', 'Do not silently expand misaligned spans.', 'Do not assume repeated strings identify the intended occurrence.'],
      related=['natural-language-processing/unicode-tokenization-boundary','natural-language-processing/corpus-identity-and-label-policy','natural-language-processing/text-serving-contract','data-science/reproducible-analysis-snapshot']),
 dict(path='natural-language-processing/classification-slices-and-abstention', title='Text classification evaluation: inspect slices and allow abstention',
      summary='A routing metric needs class counts, language and channel slices, and a policy for cases the model should send to human review.',
      sections=[
       ('Tie the metric to work', 'A false urgent route consumes specialist capacity; a missed urgent ticket delays response. Set a primary metric tied to those costs, then show a confusion matrix and per-class support. An overall score can rise while the rare urgent queue becomes worse. [[machine-learning/decision-threshold-and-cost|Threshold choice]] should use a validation set and a measured review budget.'),
       ('Inspect relevant slices', 'Split results by language, product, message length and arrival channel. State numerator and denominator for every slice, and suppress or qualify unstable estimates from tiny counts. A model can perform well on long English descriptions while failing on short mixed-language messages. The slice list should be written before reading the final test set.'),
       ('Make uncertainty actionable', 'A route confidence below a declared threshold can go to manual triage. An abstention is not automatically a success; count its volume, delay and eventual correct destination. If the classifier cannot represent a new queue, an out-of-scope detector or fallback is needed. [[natural-language-processing/text-serving-contract|Serving]] must expose the fallback consistently.'),
       ('Test operational capacity', 'Simulate a week of tickets with a realistic class mix. At each threshold, count automated routes, manual reviews, urgent misses and wrong specialist assignments. Compare the chosen policy with a simple rule and with no automation. Re-evaluate after a queue taxonomy change rather than assuming old labels retain their meaning.')],
      code='def route_with_abstention(class_scores, class_names, minimum_score):\n    if len(class_scores) != len(class_names) or len(class_scores) == 0:\n        raise ValueError("invalid score contract")\n    best_index = max(range(len(class_scores)), key=class_scores.__getitem__)\n    if class_scores[best_index] < minimum_score:\n        return "manual-review"\n    return class_names[best_index]',language='python',
      cost='Threshold selection over N scored tickets costs O(N) for each candidate threshold; sorting once supports a sweep in O(N log N). Manual-review volume is an operational cost and must be budgeted.',
      mistakes=['Do not hide rare-class failures in one average.', 'Do not count abstention as a correct automated route.', 'Do not choose thresholds on the untouched final test set.'],
      related=['natural-language-processing/sparse-text-baseline','natural-language-processing/text-serving-contract','machine-learning/decision-threshold-and-cost','mlops/drift-delayed-label-monitoring']),
 dict(path='natural-language-processing/text-serving-contract', title='Text inference: package tokenizer, labels and reject paths',
      summary='A serving endpoint must use the fitted preprocessing artifact, stable class order and bounded request handling from the evaluated model.',
      sections=[
       ('Bind the artifacts', 'A model file alone does not define text behavior. Package normalization, tokenizer or vectorizer, class mapping and threshold with the weights. Verify their versions at startup. Rebuilding a vocabulary from incoming tickets changes feature positions and invalidates the classifier. [[natural-language-processing/sparse-text-baseline|Sparse baselines]] should serve through the fitted pipeline, not a second preprocessing script.'),
       ('Bound inputs', 'Reject empty, undecodable and oversized messages before allocating large intermediate arrays. Set policy for attachments and unsupported languages. Preserve original ticket ID for idempotent routing requests, but keep customer text out of routine application logs. An inference response should identify model version, predicted queue and whether it abstained.'),
       ('Measure both speed and meaning', 'Load the artifact once per worker, warm it and measure p95 latency with realistic text lengths and concurrency. Track rejection, abstention and queue distributions. A sudden shift may be a product launch, a source parser error or model behavior change; investigate before retraining. [[mlops/drift-delayed-label-monitoring|Monitoring]] separates these signals.'),
       ('Test a rollback', 'Run known-good messages through candidate and current models. Confirm class names, preprocessing hash and accepted size range. Keep the previous complete artifact available. A deployment can pass health checks while swapping two class IDs, so include expected route outputs in the smoke set.')],
      code='def route_ticket(request, loaded_pipeline, class_names, model_version):\n    if not request.ticket_id or not isinstance(request.text, str) or not request.text.strip():\n        raise ValueError("ticket ID and text required")\n    if len(request.text.encode("utf-8")) > 180_000:\n        raise ValueError("ticket text exceeds byte limit")\n    predicted_queue = loaded_pipeline.predict([request.text])[0]\n    if predicted_queue not in class_names:\n        raise RuntimeError("model returned unknown queue")\n    return {"ticket_id": request.ticket_id, "queue": predicted_queue,\n            "model_version": model_version}',language='python',
      cost='Sparse inference visits input tokens and nonzero features; latency also includes decoding, queue wait and serialization. A text-length cap bounds worst-case memory and processing time.',
      mistakes=['Do not rebuild vocabulary at serving time.', 'Do not omit class mapping from the deployed artifact.', 'Do not log raw customer text by default.'],
      related=['natural-language-processing/unicode-tokenization-boundary','natural-language-processing/classification-slices-and-abstention','mlops/model-registry-promotion-gates','mlops/inference-logging-privacy']),
 dict(path='natural-language-processing/ticket-routing-project', title='Project: route support tickets with auditable text evaluation',
      summary='Build a ticket router from frozen submission-time text, prove group and time isolation, and release it with an abstention path.',
      sections=[
       ('Build the input manifest', 'Create a governed fixture with ticket ID, conversation ID, submission time, visible text and final queue. Include edits, repeated customer text, delayed labels and at least one message in another language. State the annotation policy. The model input must include only text available at routing time. [[natural-language-processing/corpus-identity-and-label-policy|The corpus contract]] is the first deliverable.'),
       ('Fit a baseline safely', 'Split by conversation and future time, then fit a vectorizer and classifier only on the training partition. Keep one untouched final test partition. Compare majority-class, rule-based and sparse-model routes under the same cost metric. Count empty feature outputs and inspect frequent errors. [[natural-language-processing/sparse-text-baseline|The sparse baseline]] makes a useful reference.'),
       ('Choose an action policy', 'On validation data, select a threshold for manual review within a stated staffing budget. Report per-class and language-slice counts, wrong urgent routes and abstentions. Do not count an abstention as an automated success. [[natural-language-processing/classification-slices-and-abstention|Slice analysis]] shows where the router should stop making decisions.'),
       ('Exercise deployment failure', 'Save the fitted pipeline, class mapping and version. Reject an empty and oversized request. Smoke-test known ticket texts, then deliberately swap class order in a candidate manifest and ensure promotion fails. Submit code, data manifest, split IDs, evaluation counts and a rollback procedure.')],
      code='def check_ticket_project(training_conversation_ids, evaluation_conversation_ids, predictions, labels):\n    if set(training_conversation_ids) & set(evaluation_conversation_ids):\n        raise ValueError("conversation identity leaked")\n    if len(predictions) != len(labels):\n        raise ValueError("prediction count mismatch")\n    review_count = sum(route == "manual-review" for route in predictions)\n    return {"evaluated": len(labels), "manual_review": review_count}',language='python',
      cost='Vectorization and model fitting scale with nonzero text features and solver iterations. Split auditing is O(N) for exact identities; manual review capacity is a separate recurring operational cost.',
      mistakes=['Do not include agent replies written after the routing decision.', 'Do not report a model score without an operational baseline.', 'Do not deploy a vectorizer separately from its classifier.'],
      related=['natural-language-processing/corpus-identity-and-label-policy','natural-language-processing/grouped-temporal-text-validation','natural-language-processing/classification-slices-and-abstention','natural-language-processing/text-serving-contract']),
])

lessons.extend([
 dict(path='mlops/drift-delayed-label-monitoring', title='Model monitoring: separate input drift, data faults and delayed outcomes',
      summary='A monitoring panel should distinguish serving health, feature distribution change and measured quality after labels mature.',
      sections=[
       ('Separate three clocks', 'A request arrives now, its features may have older event times, and its correct outcome may be known days later. Monitor serving failures and freshness immediately. Compare feature distributions on a defined population and window. Compute quality only for examples whose labels have matured; otherwise recent hard cases may be undercounted. [[natural-language-processing/grouped-temporal-text-validation|Text evaluation]] has the same delayed-label boundary.'),
       ('Treat drift as a signal', 'A shifted input distribution does not automatically mean accuracy fell. A parser defect, seasonal demand or new product can all move histograms. First check counts, missingness, schema and source lag; then inspect labeled performance when available. A stable input distribution does not guarantee stable outcomes either, because the relationship between features and labels can change.'),
       ('Make baselines comparable', 'Compare the same feature definition, units and eligibility rules across reference and live windows. Slice by region, language or source only when counts support interpretation. Alert on sustained and actionable deviations rather than every small fluctuation. [[mlops/feature-training-serving-parity|Parity checks]] catch transform mismatches before drift analysis becomes misleading.'),
       ('Record investigation results', 'For an alert, keep window boundaries, sample counts, model version, feature version and triage outcome. Test a simulated parser break, a legitimate volume surge and a delayed outcome feed. The response should differ: repair the parser, adjust capacity, or wait for mature labels before claiming model degradation.')],
      code='from datetime import timedelta\n\ndef mature_outcomes(predictions, outcomes, evaluation_cutoff, delay_days=9):\n    outcome_by_request = {row.request_id: row for row in outcomes}\n    eligible = []\n    for prediction in predictions:\n        if prediction.created_at > evaluation_cutoff - timedelta(days=delay_days):\n            continue\n        outcome = outcome_by_request.get(prediction.request_id)\n        if outcome and outcome.observed_at <= evaluation_cutoff:\n            eligible.append((prediction, outcome))\n    return eligible',language='python',
      cost='Joining N predictions to outcomes uses O(N) expected time and O(L) lookup memory for L labels. Distribution monitoring needs retained aggregate statistics; raw request retention has separate privacy cost.',
      mistakes=['Do not equate feature drift with measured model failure.', 'Do not score immature outcomes as negatives.', 'Do not compare windows with different eligibility rules.'],
      related=['mlops/feature-training-serving-parity','mlops/retraining-trigger-and-challenger','mlops/inference-logging-privacy','natural-language-processing/classification-slices-and-abstention']),
 dict(path='mlops/retraining-trigger-and-challenger', title='Retraining decisions: require a reason and a challenger comparison',
      summary='A retraining trigger opens an investigation; a replacement model still needs independent evaluation and controlled rollout.',
      sections=[
       ('Name a trigger precisely', 'Triggers may include measured quality below a limit, a changed label taxonomy, or a feature contract revision. A drift alert alone is not proof that retraining fixes the problem. Repair source defects first. Record the observed window, sample size and label maturity rule behind the trigger. [[mlops/drift-delayed-label-monitoring|Monitoring]] should provide these facts, not just an alarm color.'),
       ('Freeze the comparison', 'Train a challenger on a versioned dataset with explicit cutoff and holdout. Score challenger and incumbent on the same future population under the same feature availability and cost metric. Avoid testing many candidates on the final holdout until one wins. A new model can improve average accuracy while making an urgent minority class worse; set guardrails before fitting.'),
       ('Keep deployment separate', 'A better offline score is necessary but not sufficient. Validate artifact completeness, schema parity, latency and safety checks, then use shadow or canary traffic. Keep the incumbent as an available rollback target. [[mlops/model-registry-promotion-gates|Promotion gates]] tie this evidence to the exact artifact.'),
       ('Test no-change outcomes', 'Simulate a drift alert caused by a source parser bug. The correct response is source repair, not retraining on corrupt data. Also simulate a challenger that misses an urgent-class guardrail. It must remain a candidate even if its overall score improves. Document when retraining was considered and rejected.')],
      code='def challenger_is_eligible(candidate, incumbent, limits):\n    if candidate["evaluated_count"] < limits["minimum_cases"]:\n        return False\n    if candidate["urgent_recall"] < limits["urgent_recall"]:\n        return False\n    if candidate["cost_per_ticket"] >= incumbent["cost_per_ticket"]:\n        return False\n    return candidate["latency_p95_ms"] <= limits["latency_p95_ms"]',language='python',
      cost='Training cost depends on model and dataset; evaluating two models doubles inference on the frozen comparison set. Retaining candidate artifacts and evidence is cheaper than recovering from an unreviewed release.',
      mistakes=['Do not retrain automatically on corrupted inputs.', 'Do not promote on one overall metric while a protected slice fails.', 'Do not use final-test feedback for repeated candidate tuning.'],
      related=['mlops/drift-delayed-label-monitoring','mlops/model-registry-promotion-gates','mlops/shadow-canary-and-rollback','machine-learning/group-and-time-validation']),
 dict(path='mlops/inference-logging-privacy', title='Inference logs: keep diagnostic joins without copying sensitive payloads',
      summary='Prediction logs need stable request and model identities, feature diagnostics and outcome joins under a retention and access policy.',
      sections=[
       ('Log the decision boundary', 'Record request ID, model version, feature or tokenizer version, decision time, route or score summary, abstention flag and latency. Store enough to join a delayed outcome, but avoid raw ticket text, receipt images and unbounded feature dumps in routine logs. A one-way identifier or governed mapping can preserve correlation without exposing a customer ID broadly. [[natural-language-processing/text-serving-contract|Text serving]] should follow the same contract.'),
       ('Separate operational and audit needs', 'Fast operational metrics need counts and histograms; an incident investigation may require a tightly controlled sample of raw inputs. These have different retention, consent and access rules. Do not make every engineer’s observability dashboard a raw-data archive. A deletion request must be traceable across logs and derived datasets according to the product policy.'),
       ('Make joins honest', 'Join predictions to outcomes using stable IDs and the correct decision-time window. Retries may produce multiple predictions for one request; choose whether the first, last or acted-on decision is evaluated. Otherwise duplicate rows inflate metric denominators. [[data-science/dataset-grain-and-join-cardinality|Dataset grain]] matters in production metrics too.'),
       ('Test a redaction failure', 'Inject a request containing a sample account number and verify that ordinary logs, error traces and alerts do not include the raw payload. Then verify that authorized outcome joins still work. Inspect both success and exception paths; exception logging often bypasses the intended redaction helper.')],
      code='def inference_log_record(request_id, manifest, result, elapsed_ms):\n    return {\n        "request_id": request_id,\n        "model_version": manifest["model_version"],\n        "feature_version": manifest["feature_version"],\n        "decision": result["decision"],\n        "abstained": result["decision"] == "manual-review",\n        "elapsed_ms": round(elapsed_ms, 2),\n    }',language='python',
      cost='Writing one bounded record per request is O(1) per event; storage grows O(N) with request volume. Sampling and aggregate rollups reduce storage but must retain denominators for valid monitoring.',
      mistakes=['Do not log raw sensitive payloads by default.', 'Do not count retries as independent decisions without a grain policy.', 'Do not assume exception traces follow normal redaction.'],
      related=['mlops/drift-delayed-label-monitoring','natural-language-processing/text-serving-contract','data-science/dataset-grain-and-join-cardinality','mlops/receipt-triage-release-project']),
 dict(path='mlops/receipt-triage-release-project', title='Project: release receipt triage with lineage, canary checks and rollback',
      summary='Package a receipt-triage candidate with reproducible inputs, parity checks, promotion gates, a staged rollout and delayed-outcome monitoring.',
      sections=[
       ('Produce a reviewable candidate', 'Train or reuse a receipt-triage model from a pinned input snapshot. Write a manifest naming code revision, feature schema, class order, evaluation population and artifact digest. Deliberately remove one field and show that promotion refuses the candidate. [[mlops/run-manifest-and-artifact-lineage|Artifact lineage]] is the first acceptance criterion.'),
       ('Prove feature and release behavior', 'Recompute sampled offline features at their original decision times and compare them with serving values. Stage the candidate as shadow traffic so its scores cannot perform actions. Then route a stable small customer slice through canary assignment. Inject one candidate timeout and verify fallback plus a recorded incident. [[mlops/shadow-canary-and-rollback|Rollout controls]] define this behavior.'),
       ('Monitor without invented outcomes', 'Track request count, errors, latency, abstention and feature freshness immediately. Calculate quality only after labels mature under a fixed cutoff, and state the evaluated denominator. Simulate a source parser defect and show why the response is repair rather than retraining. [[mlops/drift-delayed-label-monitoring|Monitoring]] should separate those causes.'),
       ('Demonstrate rollback', 'Keep the prior artifact and preprocessing manifest available. Switch the serving pointer back after a guardrail breach, then run known-good requests to verify previous outputs. Submit the manifest, gates, split IDs, parity report, canary assignment tests, latency sample and rollback transcript. A diagram without failure-case output is incomplete.')],
      code='def release_gate(candidate, parity_mismatches, smoke_passed, prior):\n    if parity_mismatches:\n        raise ValueError("feature parity failed")\n    if not smoke_passed or not candidate.get("artifact_sha256"):\n        raise ValueError("candidate evidence incomplete")\n    if candidate["urgent_recall"] < prior["urgent_recall"]:\n        raise ValueError("urgent-class guardrail failed")\n    return candidate["artifact_sha256"]',language='python',
      cost='Shadow traffic adds model execution per mirrored request; canary monitoring adds storage for bounded decision logs. The full project cost includes replay, evaluation and retained rollback artifacts.',
      mistakes=['Do not let a shadow score trigger a real receipt action.', 'Do not calculate quality before outcomes mature.', 'Do not delete the prior artifact before rollback is tested.'],
      related=['mlops/run-manifest-and-artifact-lineage','mlops/model-registry-promotion-gates','mlops/shadow-canary-and-rollback','mlops/drift-delayed-label-monitoring']),
])

lessons.extend([
 dict(path='mlops/run-manifest-and-artifact-lineage', title='Training manifests: link data, code, configuration and artifact',
      summary='A training run is reviewable only when the emitted model can be tied to immutable inputs, code and evaluation evidence.',
      sections=[
       ('Treat the run as a record', 'Record input snapshot ID, transform version, code revision, dependency set, configuration, random seed and label schema before fitting. Give the run a stable identifier and write the final artifact digest after serialization. A filename called latest cannot establish which data produced the model. [[data-science/reproducible-analysis-snapshot|Analysis snapshots]] describe the earlier data boundary.'),
       ('Distinguish replay levels', 'A manifest can enable logical reproduction without guaranteeing bitwise identical weights. Accelerator kernels, worker ordering and nondeterministic operations may vary. Record the environment and compare expected metrics within declared tolerances. If exact replay is required, constrain all stochastic inputs and test it explicitly. Do not claim reproducibility because a seed was set in one library.'),
       ('Bind evaluation to the artifact', 'Evaluation records should name the exact model digest and split manifest. Otherwise a good report can be paired with a different binary during promotion. Keep training, validation and final-test IDs distinct; update the report when any input changes. [[mlops/model-registry-promotion-gates|Promotion gates]] must inspect this immutable pairing.'),
       ('Test a missing field', 'Remove the input snapshot or class mapping from a candidate manifest and make validation fail. Create two artifacts under one run name and assert that their digests distinguish them. The manifest is not a decorative file; deployment checks should reject an incomplete one.')],
      code='from hashlib import sha256\nfrom pathlib import Path\n\ndef artifact_digest(model_file: Path):\n    digest = sha256()\n    with model_file.open("rb") as artifact_stream:\n        for block in iter(lambda: artifact_stream.read(1_048_576), b""):\n            digest.update(block)\n    return digest.hexdigest()\n\nrun_manifest["artifact_sha256"] = artifact_digest(model_path)',language='python',
      cost='Hashing a P-byte artifact is O(P) time with O(1) buffer memory. Retaining snapshots and model versions adds storage; the manifest itself is small but prevents expensive provenance guesses.',
      mistakes=['Do not point evaluation evidence at an unversioned latest file.', 'Do not promise bitwise replay from a seed alone.', 'Do not promote an artifact without its class and feature schema.'],
      related=['data-science/reproducible-analysis-snapshot','mlops/model-registry-promotion-gates','mlops/feature-training-serving-parity','deep-learning/checkpoint-resume-state']),
 dict(path='mlops/feature-training-serving-parity', title='Training-serving parity: compare feature values at one prediction clock',
      summary='A production feature must represent the same information and transformation that was available to the offline training example.',
      sections=[
       ('Define a feature view', 'Name source fields, types, null policy, event-time cutoff and transform version. A seven-day receipt count at 09:00 cannot include a transaction that posts at 09:05, even if the warehouse later backfills it. Compare offline and online values for the same entity and decision timestamp. [[machine-learning/prediction-time-feature-availability|Feature availability]] defines what the model was allowed to know.'),
       ('Test both paths', 'Build a parity fixture with late arrivals, corrected amounts and absent history. Run it through offline and online transforms, then compare numeric values within justified tolerance. A shared function is helpful but does not prove parity if the paths read different source snapshots. [[data-engineering/event-time-and-late-arrivals|Event-time policy]] must be shared too.'),
       ('Name freshness separately', 'An online feature can match the offline formula yet be stale because its cache has not refreshed. Record source event time and serving refresh time, set a maximum age and choose a fallback for missing or stale values. A fallback of zero changes meaning when zero is a valid measured count; use an explicit missing indicator when required.'),
       ('Monitor skew by cause', 'Log aggregate parity differences from sampled replayable requests without exposing sensitive records. Partition mismatches by feature version, source lag and entity type. A sudden mismatch after deployment may be a parser change, not model drift. Pause promotion or route to a safe fallback until the cause is understood.')],
      code='def compare_feature_snapshots(offline, online, tolerance=1e-6):\n    if offline.keys() != online.keys():\n        raise ValueError("feature names differ")\n    mismatches = {}\n    for feature_name in offline:\n        left, right = offline[feature_name], online[feature_name]\n        if left is None or right is None:\n            different = left != right\n        else:\n            different = abs(left - right) > tolerance\n        if different:\n            mismatches[feature_name] = (left, right)\n    return mismatches',language='python',
      cost='Comparing F scalar features costs O(F) per sampled request. The expensive work is reconstructing point-in-time offline values and retaining enough history to explain differences.',
      mistakes=['Do not compare values computed at different prediction times.', 'Do not mistake a stale cache for a changed formula.', 'Do not use zero as a universal missing fallback.'],
      related=['machine-learning/prediction-time-feature-availability','data-engineering/event-time-and-late-arrivals','mlops/drift-delayed-label-monitoring','mlops/model-registry-promotion-gates']),
 dict(path='mlops/model-registry-promotion-gates', title='Model promotion: require evidence before changing the serving pointer',
      summary='A model registry separates immutable candidate versions from the mutable pointer that traffic uses, with checks before promotion.',
      sections=[
       ('Register an immutable candidate', 'Store artifact digest, input and feature schemas, class map, training manifest, evaluation result and owner under a version. A human-readable alias can identify the active version, but the alias must resolve to one immutable artifact at deployment time. [[mlops/run-manifest-and-artifact-lineage|Run lineage]] proves the candidate’s origin.'),
       ('Make gates executable', 'Require complete metadata, schema compatibility, a known-good smoke set and measured latency within a declared budget. Compare candidate quality against the incumbent on the same evaluation population; allow explicit exceptions only with recorded rationale. Do not substitute a training score for an independent evaluation. Check whether the candidate artifact uses a loading format that can execute code, and accept only trusted artifacts under a controlled environment.'),
       ('Promote as a state change', 'After all gates pass, update a version pointer or alias. Record who promoted it, when, why and the previous pointer. A rollback should point to a still-available prior artifact and matching preprocessing. [[mlops/shadow-canary-and-rollback|Canary rollout]] can test behavior before the full pointer change.'),
       ('Drill rejection and rollback', 'Try a candidate with missing class mapping, a mismatched preprocessing hash and a failing known-good request. Each must be rejected. Then promote a valid candidate and roll back; verify request outputs return to the previous version. A registry page alone does not prove the serving process loaded the intended artifact.')],
      code='REQUIRED_FIELDS = {"artifact_sha256", "data_snapshot", "feature_schema",\n                   "class_names", "evaluation_manifest", "preprocess_version"}\n\ndef approve_candidate(manifest, smoke_passed, latency_p95_ms, budget_ms):\n    missing = REQUIRED_FIELDS - manifest.keys()\n    if missing or not smoke_passed or latency_p95_ms > budget_ms:\n        raise ValueError(f"candidate failed promotion gate: {sorted(missing)}")\n    return manifest["artifact_sha256"]',language='python',
      cost='Metadata checks are O(F) for F required fields; loading and smoke-testing the candidate dominate time and memory. Retaining one prior version costs storage but makes rollback practical.',
      mistakes=['Do not change a serving alias before validation finishes.', 'Do not lose the prior artifact when promoting a candidate.', 'Do not load untrusted serialized model files.'],
      related=['mlops/run-manifest-and-artifact-lineage','mlops/shadow-canary-and-rollback','mlops/feature-training-serving-parity','deep-learning/inference-schema-and-latency']),
 dict(path='mlops/shadow-canary-and-rollback', title='Shadow and canary rollout: compare a candidate without losing a rollback',
      summary='A release stages candidate observation, limited live traffic and rollback against explicit health and decision metrics.',
      sections=[
       ('Use shadow for observation', 'Send a copy of eligible requests to a candidate model while the incumbent still determines the action. Compare outputs, latency and failure rate without sending the candidate’s decision downstream. Shadow traffic can still incur compute and data-handling obligations, so keep access and retention controls. It does not prove how users will react to candidate actions.'),
       ('Make canary scope explicit', 'Route a small, stable slice of live traffic to the candidate. Use a deterministic assignment key so one customer is not switched between models on each request. Watch latency, error rate, abstention and downstream decision outcomes. If labels arrive late, do not pretend the first hour’s proxy metrics establish final quality. [[mlops/drift-delayed-label-monitoring|Label maturity]] changes the evaluation clock.'),
       ('Define stop and rollback before launch', 'Set quantitative guardrails and an owner for the rollout. Keep the old artifact, preprocessing and class mapping loaded or rapidly recoverable. On a guardrail breach, stop new candidate assignments and restore the prior pointer. Record in-flight requests and whether decisions already sent downstream require repair.'),
       ('Test routing and failure', 'Use a fixed key to confirm assignment stability, then inject a candidate timeout and incorrect class mapping. The timeout must trigger the documented fallback; the mapping failure should stop rollout before it reaches the canary. Compare candidate and incumbent over the same request population, noting where eligibility rules differ.')],
      code='import hashlib\n\ndef assign_canary(customer_id, rollout_percent):\n    if not 0 <= rollout_percent <= 100:\n        raise ValueError("invalid rollout percentage")\n    fingerprint = hashlib.sha256(customer_id.encode("utf-8")).digest()\n    bucket = int.from_bytes(fingerprint[:4], "big") % 10_000\n    return bucket < rollout_percent * 100',language='python',
      cost='Shadowing can nearly double model inference work for mirrored requests; a canary adds little per-request compute but requires parallel artifact storage and monitoring. Hash assignment is O(length of key).',
      mistakes=['Do not let shadow outputs perform real actions.', 'Do not randomize assignment independently for each request.', 'Do not discard the previous preprocessing artifact before rollback is safe.'],
      related=['mlops/model-registry-promotion-gates','mlops/drift-delayed-label-monitoring','mlops/inference-logging-privacy','mlops/receipt-triage-release-project']),
])

assert len(lessons) == 16
assert len({item['path'] for item in lessons}) == len(lessons)
titles = {path: row['title'] for path, row in by_path.items()}
titles.update({item['path']: item['title'] for item in lessons})

def link_list(paths):
    return '<ul>' + ''.join('<li><a href="/' + path + '">' + html.escape(titles[path]) + '</a></li>' for path in paths) + '</ul>'

def article_body(item):
    parts = ['<p>' + html.escape(item['summary']) + '</p>']
    for heading, paragraph in item['sections']:
        parts.extend(('<h2>' + html.escape(heading) + '</h2>', '<p>' + prose(paragraph) + '</p>'))
    parts.extend(('<h2>Implementation</h2>', '<pre><code class="language-' + item['language'] + '">' + html.escape(item['code']) + '</code></pre>',
                  '<h2>Performance and operating cost</h2>', '<p>' + html.escape(item['cost']) + '</p>',
                  '<h3>Common Mistakes</h3>', '<ul>' + ''.join('<li>' + html.escape(mistake) + '</li>' for mistake in item['mistakes']) + '</ul>',
                  '<h2>Read next</h2>', link_list(item['related'])))
    return ''.join(parts)

def make_row(path, title, summary, body, entry_type, subject, section_path, root_path, order, metadata):
    return dict(id=str(uuid.uuid5(uuid.NAMESPACE_URL, 'https://aitrove.in/' + path)), type=entry_type,
                path=path, title=title, summary=summary, body=body, category='AI & Data',
                subject=subject, difficulty='Intermediate', tags=['ai-data', subject], potd_date=None,
                featured=False, sort_order=order, status='published', published_at=stamp,
                created_at=stamp, updated_at=stamp,
                data={'subject_root':root_path, 'section_path':section_path,
                      'content_format':'html', 'seo_ready':True, **metadata})

subject_config = {
 'natural-language-processing': {
     'root':'natural-language-processing/nlp-tutorial', 'name':'Natural Language Processing',
     'summary':'Build text classifiers and extraction systems with explicit corpus, annotation, split, evaluation and serving contracts.',
     'groups':[('Corpus and representation', ['corpus-identity-and-label-policy','unicode-tokenization-boundary','span-offset-annotation','sparse-text-baseline']),
               ('Evaluation and serving', ['grouped-temporal-text-validation','classification-slices-and-abstention','text-serving-contract'])],
     'project':'ticket-routing-project',
     'foundation':['machine-learning/machine-learning-tutorial','deep-learning/deep-learning-tutorial']},
 'mlops': {
     'root':'mlops/mlops-tutorial', 'name':'MLOps',
     'summary':'Release models through traceable artifacts, feature parity, promotion gates, staged rollout, monitoring and rollback.',
     'groups':[('Build and promotion', ['run-manifest-and-artifact-lineage','feature-training-serving-parity','model-registry-promotion-gates']),
               ('Release and operate', ['shadow-canary-and-rollback','drift-delayed-label-monitoring','retraining-trigger-and-challenger','inference-logging-privacy'])],
     'project':'receipt-triage-release-project',
     'foundation':['data-engineering/data-engineering-tutorial','machine-learning/machine-learning-tutorial']},
}

for slug, config in subject_config.items():
    root_path = config['root']
    project_hub_path = root_path + '/project'
    titles[root_path] = config['name'] + ' Tutorial'
    titles[project_hub_path] = config['name'] + ': Projects'
    modules = [{'title':group_title, 'summary':'Read in order and run the failure checks.',
                'lessons':[slug + '/' + lesson_name for lesson_name in lesson_names]}
               for group_title, lesson_names in config['groups']]
    project_path = slug + '/' + config['project']
    modules.append({'title':'Apply your knowledge', 'lessons':[project_path]})
    all_paths = [path for module in modules for path in module['lessons']]
    tabs = [{'title':config['name'], 'path':root_path}, {'title':'Projects', 'path':project_hub_path}]
    hub_body = ('<p>' + html.escape(config['summary']) + '</p><h2>Learning path</h2>' + link_list(all_paths)
                + '<h2>Connected foundations</h2><p>Use the earlier data and model boundaries as prerequisites.</p>'
                + link_list(config['foundation']) + '<h2>Practice</h2>' + link_list([project_hub_path]))
    hub = make_row(root_path, titles[root_path], config['summary'], hub_body,
                   'subject', slug, root_path, root_path, 7900 if slug == 'natural-language-processing' else 8000,
                   {'modules':modules, 'resource_tabs':tabs})
    project_body = ('<p>Apply the ' + html.escape(config['name']) + ' curriculum to a checked project.</p>'
                    '<h2>Project brief</h2>' + link_list([project_path])
                    + '<h2>Required concepts</h2>' + link_list(all_paths[:-1])
                    + '<h2>Completion standard</h2><p>Submit runnable work, a data or run manifest, measured results and failure-case evidence.</p>')
    project_hub = make_row(project_hub_path, titles[project_hub_path],
                           'A checked project for the ' + config['name'] + ' curriculum.', project_body,
                           'subject', slug + '-project', project_hub_path, root_path,
                           7901 if slug == 'natural-language-processing' else 8001,
                           {'modules':[{'title':'Projects','lessons':[project_path]}], 'resource_tabs':tabs})
    rows.extend((hub, project_hub))
    by_path[root_path] = hub
    by_path[project_hub_path] = project_hub

for index, item in enumerate(lessons):
    slug = item['path'].split('/')[0]
    root_path = subject_config[slug]['root']
    is_project = item['path'].endswith('-project')
    section_path = root_path + '/project' if is_project else root_path
    body = article_body(item)
    article = make_row(item['path'], item['title'], item['summary'], body, 'article',
                       slug + '-project' if is_project else slug, section_path, root_path,
                       8100 + index,
                       {'kind':'project' if is_project else 'tutorial',
                        'reading_minutes':max(5, len(re.sub(r'<[^>]+>', ' ', body).split()) // 180),
                        'author_path':'authors/aitrove-editorial',
                        'verification_suite':'Editorial and syntax review; project inputs needed for runtime checks',
                        'related':[{'path':path,'title':titles[path]} for path in item['related']]})
    rows.append(article)
    by_path[item['path']] = article

for source, target in [
    ('machine-learning/group-and-time-validation','natural-language-processing/grouped-temporal-text-validation'),
    ('machine-learning/leakage-safe-preprocessing-pipeline','natural-language-processing/sparse-text-baseline'),
    ('deep-learning/tensor-shape-dtype-contract','natural-language-processing/unicode-tokenization-boundary'),
    ('data-engineering/event-time-and-late-arrivals','mlops/feature-training-serving-parity'),
    ('machine-learning/decision-threshold-and-cost','mlops/retraining-trigger-and-challenger'),
    ('deep-learning/inference-schema-and-latency','mlops/shadow-canary-and-rollback'),
]:
    row = by_path[source]
    anchor = '<p><strong>Continue the workflow:</strong> <a href="/' + target + '">' + html.escape(titles[target]) + '</a>.</p>'
    if anchor not in row['body']:
        row['body'] += anchor
        row['data']['related'].append({'path':target,'title':titles[target]})
        row['updated_at'] = stamp

assert len({row['path'] for row in rows}) == len(rows)
fixture.write_text(json.dumps(rows, ensure_ascii=False, indent=2) + '\n')
print(json.dumps({'new_articles':len(lessons), 'new_subject_hubs':4, 'crosslinks_from_existing':6}))
