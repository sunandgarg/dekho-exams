"""Add graph message-passing and unaligned sequence-recognition paths."""
from de_batch_publisher import publish

GRAPHS = 'Graph message passing and incident attribution'
CTC = 'Unaligned sequence recognition and OCR checks'
LESSONS = []


def add(slug, title, summary, sections, code, cost, mistakes, related, module, project=False):
    assert len(sections) == 5
    LESSONS.append(dict(path='deep-learning/' + slug, title=title, summary=summary,
                        sections=sections, code=code, cost=cost, mistakes=mistakes,
                        related=related, module=module, project=project))


add('graph-message-passing-edge-direction-and-self-state',
    'Graph message passing, edge direction and self state',
    'A graph layer is an aggregation rule over a declared edge snapshot; reversing an edge or omitting self state changes what a service node can know.', [
    ('Define the prediction unit', 'A service dependency graph has service nodes and directed calls: checkout calls billing, billing calls a ledger, and an incident may affect any of them. First decide whether the target is a service state, a call failure or a whole-incident label. A node model emits one result per service. A link model scores pairs. Pooling node states produces a graph-level result. Their training labels and review units differ. [[deep-learning/receipt-defect-segmentation-project|Pixel-level prediction]] has a similar requirement: match output units to annotation units before choosing a loss.'),
    ('Write the edge convention down', 'If an edge is stored as caller to callee, aggregation toward the destination carries information from callers to callees. Incident propagation may instead require the reverse direction, or two distinct relation types. A supposedly undirected graph is usually represented by both directed edges. Test a three-node example by hand. A silent edge reversal can preserve tensor shapes and training loss while changing the operational claim. Record whether duplicate calls are collapsed or weighted, and whether self loops are explicit.'),
    ('Aggregate without degree surprises', 'Summing incoming messages scales with node degree; averaging makes a node with two similar callers comparable to one with twenty. Neither is always correct. A busy shared service may need degree as a feature because traffic itself matters. Include the node’s own state through a self loop or a separate transform, then combine it with neighbor messages. An isolated node should still retain its own features rather than produce an undefined mean. The code uses self-inclusive averaging so its result can be checked without a graph library.'),
    ('Keep feature and edge clocks aligned', 'At an alert time, use metrics and calls observed by that time. A service graph assembled from the entire later incident can expose the answer through edges added after the alert. Attach valid-from and valid-to times to dependencies, and declare how long telemetry is delayed. A graph learner can also memorize service identity if train and test share the same nodes. [[deep-learning/graph-neighbor-sampling-and-time-split|The split lesson]] separates transductive and newly introduced services.'),
    ('Probe the model against simpler rules', 'Compare a graph layer with a local-feature baseline and a hand-coded upstream/downstream summary. Ablate edges, flip their directions and remove high-degree hubs; measure which incident classes change. Inspect a few message paths rather than treating attention or embedding magnitude as proof of causality. If the graph model wins only when future edges are present, the result is leakage. [[deep-learning/service-incident-graph-project|The applied project]] includes that failure test.')],
    '''service_pressure = {"checkout": 8.0, "billing": 4.0, "inventory": 2.0}
calls = [("checkout", "billing"), ("checkout", "inventory")]

def self_and_caller_mean(features, directed_calls):
    incoming = {service: [pressure] for service, pressure in features.items()}
    for caller, callee in directed_calls:
        if caller not in features or callee not in features:
            raise ValueError("edge references an unknown service")
        incoming[callee].append(features[caller])
    return {service: sum(values) / len(values)
            for service, values in incoming.items()}

updated_pressure = self_and_caller_mean(service_pressure, calls)
assert updated_pressure == {"checkout": 8.0, "billing": 6.0,
                            "inventory": 5.0}''',
    'One aggregation pass over V nodes and E directed edges costs O(V + E) time and O(V + E) temporary storage in this list-based demonstration. A dense V-by-V adjacency matrix costs O(V²) space even when the call graph is sparse. A learned layer also stores feature-width activations for backward; stacking L layers expands the information horizon to L hops and can make representations less distinct. Measure edge count, degree skew and per-layer memory before adding depth.',
    ['Do not assume a caller-to-callee edge sends information in both directions.', 'Do not divide by zero for isolated nodes or discard their self features.', 'Do not infer causality from a large message weight without a timing and ablation check.'],
    ['deep-learning/graph-neighbor-sampling-and-time-split', 'deep-learning/service-incident-graph-project', 'deep-learning/receipt-defect-segmentation-project', 'deep-learning/occlusion-attribution-and-sanity-checks', 'deep-learning/inference-schema-and-latency'], GRAPHS)

add('graph-neighbor-sampling-and-time-split',
    'Graph neighbor sampling and time-safe evaluation',
    'Sampling controls the number of edges a graph batch touches, but the sampled neighborhood must still obey the prediction timestamp and label boundary.', [
    ('Start with seed nodes', 'A node-classification batch contains seed services whose labels contribute to the loss. To compute a two-layer message-passing result, the loader needs neighbors of seeds and neighbors of those neighbors; these context nodes are not automatically extra labeled examples. Record seed IDs separately from sampled node IDs, and mask the loss to seeds. If a context node also appears in validation, that is not necessarily leakage for a transductive fixed graph; using its held-out label or post-cutoff features is leakage. State the evaluation setting.'),
    ('Bound the receptive field', 'With at most k neighbors at each of L hops, a seed can touch up to a quantity proportional to k raised to L nodes before deduplication. High-degree hubs make full-neighborhood training expensive. Sampling caps work but adds variance: two draws around the same service can differ. Fix a seed for parity tests and keep fanout, hop count and edge direction with the model artifact. If the task depends on one rare upstream service, uniform sampling may omit exactly the relation that matters. Compare recall by degree and relation type.'),
    ('Enforce edge and feature cutoff', 'For an incident scored at minute 47, exclude a dependency first observed at minute 53 and telemetry emitted after minute 47, even if the graph snapshot is built days later. A stored row timestamp is only useful if it represents when the value became observable, not when it was eventually backfilled. A feature computed over a centered window can include the future without an obvious future timestamp on the row. [[deep-learning/graph-message-passing-edge-direction-and-self-state|Edge direction]] remains a separate contract.'),
    ('Choose the split deliberately', 'A temporal split tests future incidents on known services. A service-holdout split tests transfer to services absent from training, and may need a different identity encoding. A random node split on one static graph usually answers a narrower transductive question. Split by incident identity where one incident labels many related service nodes; otherwise near-duplicate states can land in both train and test. Keep a simple local-feature baseline under the same split. [[deep-learning/augmentation-leakage-boundary|Leakage boundaries]] apply to graph context too.'),
    ('Test sampled versus full-neighborhood inference', 'For a small held-out graph, compare sampled outputs across several draws with full-neighborhood outputs. Report variance and failure cases rather than presenting one favorable sample. At serving time, pin the graph snapshot, fanout and seed policy; a changed graph can change scores without a model update. Keep a fallback if required neighbors are missing. [[deep-learning/service-incident-graph-project|The project]] makes the cutoff and evaluation populations explicit.')],
    '''from random import Random

observed_calls = [
    ("checkout", "billing", 31),
    ("billing", "ledger", 39),
    ("checkout", "inventory", 53),
]

def sample_visible_callers(seed_services, call_events, cutoff_minute, fanout, seed):
    if fanout < 1:
        raise ValueError("fanout must be positive")
    incoming = {service: [] for service in seed_services}
    for caller, callee, observed_minute in call_events:
        if observed_minute <= cutoff_minute and callee in incoming:
            incoming[callee].append(caller)
    randomizer = Random(seed)
    return {service: tuple(randomizer.sample(sorted(set(callers)),
                                             min(fanout, len(set(callers)))))
            for service, callers in incoming.items()}

sampled = sample_visible_callers(["billing", "inventory"], observed_calls,
                                 cutoff_minute=47, fanout=2, seed=29)
assert sampled == {"billing": ("checkout",), "inventory": ()}''',
    'Building a filtered adjacency list costs O(E) time and O(E) space for E call events; sampling up to k callers for B seed nodes costs roughly O(Bk) after indexing, subject to degree and deduplication. This small demonstration rescans events and is suited to an audit, not a high-throughput loader. Multiple graph layers may expand neighborhoods toward O(Bk^L) before shared nodes merge. Store or query a timestamp-indexed graph snapshot for production and measure the bias from missing sampled neighbors.',
    ['Do not apply a seed-node label to every context node in its sampled subgraph.', 'Do not use future graph edges merely because the test graph was exported later.', 'Do not compare a sampled model with a full-graph baseline under different feature cutoffs.'],
    ['deep-learning/graph-message-passing-edge-direction-and-self-state', 'deep-learning/service-incident-graph-project', 'deep-learning/augmentation-leakage-boundary', 'deep-learning/distributed-sampler-tail-and-global-loss-weighting', 'deep-learning/inference-schema-and-latency'], GRAPHS)

add('service-incident-graph-project',
    'Project: attribute service incidents with a time-safe graph',
    'Use a two-hop call graph to rank affected services while auditing edge direction, future-edge leakage, sampled-neighborhood variance and on-call review cost.', [
    ('Freeze the operational question', 'For each incident at its first alert, rank services for engineer review. The label is a reviewed affected-service set, not an automatically inferred causal root. Snapshot telemetry and directed dependencies as they were observable at alert time. Keep incident IDs, service IDs, review timestamps and a delayed-label flag. A service with no recorded calls still needs a local-feature score. [[deep-learning/graph-message-passing-edge-direction-and-self-state|The message-passing lesson]] defines the direction convention.'),
    ('Build and test a minimal graph layer', 'Represent each service with a fixed-window error-rate and latency feature; normalize using training incidents only. Propagate caller features toward callees for one experiment and reverse edges for another. The code checks a single tensor aggregation step and updates a classifier on three services. It proves that dimensions, aggregation and loss connect; it does not establish incident ranking quality. Require a hand-checked miniature graph before adding relation types or more layers.'),
    ('Separate seeds from context', 'Train on incident-service labels for seed nodes only. If the full graph is too large, sample a two-hop context with a fixed fanout and record the draw. Measure whether rare critical upstream dependencies are omitted. Keep the same held-out incidents and feature cutoff for the graph model and the local baseline. [[deep-learning/graph-neighbor-sampling-and-time-split|The sampling lesson]] explains why a random node split can overstate transfer.'),
    ('Evaluate the review workflow', 'Report recall among reviewed affected services in the first three suggestions, false leads per incident, and time from alert to first correct suggestion. Break results out by new service, isolated service, high-degree shared service and incident size. Inspect cases where reversing edges improves a subset: that may indicate direction-specific failure modes, not permission to choose direction after viewing final test. Include calibration or abstention so an engineer sees when the graph is incomplete. [[deep-learning/temperature-scaling-and-selective-risk|Selective risk]] is one way to set review coverage.'),
    ('Ship with graph-version parity', 'Package the model with graph snapshot revision, feature windows, missing-neighbor rule and fanout. Replay a fixed incident in a clean process and compare scores. Gate release on held-out incident recall, false leads and p95 graph fetch plus scoring latency. Fall back to the local-feature ranker when dependency data is stale. Monitor drift in edge count, hub degree and unavailable services; retraining alone will not repair a broken observability clock.')],
    '''import torch
from torch import nn
from torch.nn import functional as functional

torch.manual_seed(47)
service_features = torch.tensor([[0.8, 0.3], [0.4, 0.7], [0.2, 0.5]])
# checkout -> billing, checkout -> inventory; self state is retained.
caller_index = torch.tensor([0, 0, 0, 1, 2])
callee_index = torch.tensor([0, 1, 2, 1, 2])
incoming_sum = torch.zeros_like(service_features)
incoming_sum.index_add_(0, callee_index, service_features[caller_index])
incoming_count = torch.zeros(3, 1)
incoming_count.index_add_(0, callee_index, torch.ones(5, 1))
service_context = incoming_sum / incoming_count
assert service_context.shape == (3, 2)
assert torch.allclose(service_context[1],
                      (service_features[0] + service_features[1]) / 2)

incident_head = nn.Linear(2, 1)
optimizer = torch.optim.AdamW(incident_head.parameters(), lr=0.003)
reviewed_affected = torch.tensor([[0.0], [1.0], [0.0]])
optimizer.zero_grad(set_to_none=True)
loss = functional.binary_cross_entropy_with_logits(
    incident_head(service_context), reviewed_affected)
loss.backward()
optimizer.step()
assert torch.isfinite(loss)''',
    'The example materializes E edge messages and aggregates them in O(EF + VF) time for V services and F feature dimensions, with O(VF + EF) feature and message storage before optimizer state. Real incident graphs also pay for timestamped edge retrieval and often for two-hop sampling. Rank evaluation must group service labels by incident; treating every service row as an independent test example inflates certainty. The three-service code is a wiring test, not a benchmark or a claim that caller aggregation is the correct incident direction.',
    ['Do not train on an edge graph assembled after the alert cutoff.', 'Do not score only easy connected services while dropping isolated ones.', 'Do not equate an affected-service label with proven root cause.'],
    ['deep-learning/graph-message-passing-edge-direction-and-self-state', 'deep-learning/graph-neighbor-sampling-and-time-split', 'deep-learning/temperature-scaling-and-selective-risk', 'deep-learning/inference-schema-and-latency', 'deep-learning/service-event-lstm-project'], GRAPHS, True)

add('ctc-time-length-and-blank-alignment-contract',
    'CTC time lengths, blank labels and alignment feasibility',
    'Connectionist temporal classification trains a sequence recognizer without per-frame character labels, but every encoded length and repeated symbol must fit a valid alignment.', [
    ('State the alignment problem', 'A receipt line image may produce thirty visual time steps while its transcript contains eleven characters. No annotator has marked which column owns each character. CTC sums the probabilities of frame-level paths that collapse to the transcript. The output vocabulary includes a blank symbol that is not a transcript character. This is useful when monotonic left-to-right alignment is plausible; it is a poor fit for reading order that jumps between multiple columns without a separate layout policy. [[deep-learning/segmentation-mask-alignment-and-ignore-pixels|Pixel masks]] solve a different supervision problem.'),
    ('Calculate encoded length after the encoder', 'The input length passed to the loss is the number of valid encoder time steps, not raw image width, original audio samples or the length of a greedy-decoded transcript. Every stride, pooling and crop changes that length. If a batch pads images to a common width, retain the pre-padding encoded length for each item. Check all input lengths against the logits time dimension. The loss convention used here expects log probabilities arranged as time, batch, classes; silently swapping time and batch can produce plausible tensor values with the wrong semantics.'),
    ('Reserve blank and validate targets', 'Choose one blank ID, such as zero, and keep it out of the target transcript. A repeated character needs a blank or another frame-level separation to survive collapse: a transcript of two consecutive identical characters can require more time steps than its raw target length. The code tests a repeated-character target of length three against seven encoder steps. Check the alphabet map, normalized transcript and lengths before the loss. An unknown character should be rejected or mapped by a documented policy, not silently dropped.'),
    ('Treat impossible alignments as data failures', 'If an image is too narrow after the encoder, the transcript has no legal CTC path and loss may become infinite. Some implementations can zero such losses, but that can hide a systematic preprocessing error. Count and inspect rejected examples, especially long line items and repeated-character cases. Fix encoder resolution or data preparation rather than quietly training on a smaller population. Keep target-length distribution and the ratio of encoded steps to characters in the dataset report.'),
    ('Separate loss from transcription quality', 'A finite CTC loss proves only that the alignment calculation ran. Decode predictions with a fixed blank-collapse rule, then report character and field error by receipt type and capture device. Track output blank rate, deletion-heavy failures and line-order mistakes. [[deep-learning/ctc-greedy-collapse-and-error-audit|The decoder lesson]] prevents the common error of removing blanks before merging repeated IDs. [[deep-learning/receipt-line-ocr-ctc-project|The project]] joins training with field-level review.')],
    '''import torch
from torch import nn

torch.manual_seed(47)
encoder_logits = torch.randn(7, 1, 5, requires_grad=True)
line_transcript = torch.tensor([1, 2, 2], dtype=torch.long)
encoded_lengths = torch.tensor([7], dtype=torch.long)
transcript_lengths = torch.tensor([3], dtype=torch.long)
assert encoded_lengths.max().item() <= encoder_logits.size(0)
assert not (line_transcript == 0).any()
ctc = nn.CTCLoss(blank=0, reduction="mean", zero_infinity=False)
loss = ctc(encoder_logits.log_softmax(-1), line_transcript,
           encoded_lengths, transcript_lengths)
assert torch.isfinite(loss)
loss.backward()
assert torch.isfinite(encoder_logits.grad).all()''',
    'For T encoded steps, U transcript symbols and C output classes, logits alone cost O(TC) memory per example; the alignment calculation adds work that grows with both T and U, often described as O(TU) state transitions for a fixed sequence. A wider image increases encoder activations and CTC work even when its transcript remains short. The example is an alignment and gradient check, not a trained OCR system. Measure accepted versus rejected lines and actual throughput for the target widths.',
    ['Do not pass raw image width as encoder input length after strided convolutions.', 'Do not put the blank ID in a transcript or pad with an ID counted as a target.', 'Do not hide impossible alignments by zeroing infinite loss without an audit.'],
    ['deep-learning/ctc-greedy-collapse-and-error-audit', 'deep-learning/receipt-line-ocr-ctc-project', 'deep-learning/convolution-output-geometry-and-receptive-field', 'deep-learning/causal-target-shift-and-padding-loss', 'deep-learning/segmentation-mask-alignment-and-ignore-pixels'], CTC)

add('ctc-greedy-collapse-and-error-audit',
    'CTC greedy collapse and transcription error audit',
    'Greedy CTC decoding merges consecutive identical frame IDs before removing blanks; evaluation then has to measure the fields people actually read.', [
    ('Collapse in the correct order', 'Take the most likely class at each encoded time step. First merge adjacent repeated IDs, then remove blank IDs. A blank between identical character IDs separates two emitted characters. Removing blanks first would merge them and turn a legitimate double letter into one. The pure-Python decoder tests that boundary. Preserve the chosen alphabet map and text-normalization policy with the model; a character index has no meaning without its revision. [[deep-learning/ctc-time-length-and-blank-alignment-contract|The alignment lesson]] establishes blank and length constraints.'),
    ('Know what greedy decoding misses', 'The most likely path does not always collapse to the most probable output sequence, because many paths may support one transcript. Greedy decoding is cheap and deterministic, so it is a useful baseline. If errors on ambiguous line items matter, test beam search with a fixed beam width and document whether it uses a language model or field grammar. Compare accuracy, memory and p95 decoding time. A larger beam cannot repair a line crop that omitted the first digit.'),
    ('Score edits with a clear denominator', 'Character error rate counts substitutions, deletions and insertions divided by reference characters. A line with no characters needs an explicit policy rather than division by zero. Compute error per line and aggregate edit counts across lines for a micro rate; the mean of per-line rates answers a different question and can overweight tiny strings. Field accuracy for totals, dates and identifiers is often more consequential than a small global character-rate change. Keep punctuation and spacing normalization fixed before comparing models.'),
    ('Inspect systematic blank behavior', 'Track blank-frame fraction and output-length distribution, then review empty predictions and repeated-character deletions. A model can achieve a finite training loss and still output mostly blanks early in training or on out-of-domain fonts. Stratify by line width, contrast, blur and capture device. Do not lower the reported error by discarding low-confidence lines; show coverage and risk together. [[deep-learning/temperature-scaling-and-selective-risk|Abstention policy]] belongs in the final workflow.'),
    ('Audit reading order and release thresholds', 'A line recognizer assumes that the crop contains one sequence in reading order. Multi-column receipts require a line detector and ordering rule before CTC decoding. Review the highest-cost fields and manual-correction time, not only raw character error. Freeze normalization, decoder and validation thresholds before opening the final held-out receipts. [[deep-learning/receipt-line-ocr-ctc-project|The project]] gates the recognizer on field-level quality and latency.')],
    '''def greedy_ctc(frame_ids, blank_id=0):
    collapsed = []
    previous = None
    for class_id in frame_ids:
        if class_id != previous:
            collapsed.append(class_id)
        previous = class_id
    return [class_id for class_id in collapsed if class_id != blank_id]

frame_classes = [0, 1, 1, 0, 2, 0, 2, 2]
assert greedy_ctc(frame_classes) == [1, 2, 2]
assert greedy_ctc([0, 0, 0]) == []
alphabet = {1: "S", 2: "7"}
recognized_line = "".join(alphabet[class_id]
                          for class_id in greedy_ctc(frame_classes))
assert recognized_line == "S77"''',
    'Greedy decoding is O(T) time and O(T) output memory for T frame IDs, or O(U) output memory if only emitted symbols are retained. A beam search retains multiple partial prefixes and costs more time and memory as beam width grows. Character error requires an edit-distance calculation, commonly O(RP) time for reference length R and prediction length P, with row-wise O(min(R, P)) memory. Report field correction cost and decoder latency at the same width and batch policy used in serving.',
    ['Do not remove blanks before collapsing adjacent repeats.', 'Do not compare character error after changing text normalization between models.', 'Do not present a greedy path as necessarily the highest-probability transcript.'],
    ['deep-learning/ctc-time-length-and-blank-alignment-contract', 'deep-learning/receipt-line-ocr-ctc-project', 'deep-learning/decoding-stop-rules-and-beam-score', 'deep-learning/temperature-scaling-and-selective-risk', 'deep-learning/inference-schema-and-latency'], CTC)

add('receipt-line-ocr-ctc-project',
    'Project: recognize receipt line items with CTC',
    'Train a line-level recognizer on transcript-only labels, then prove that encoded widths, blank collapse, field accuracy and review latency hold on unseen receipts.', [
    ('Create line and transcript contracts', 'Extract one reading-order line per image and keep the parent physical receipt ID. Normalize orientation, grayscale range and transcript characters under a versioned rule; retain the raw image and reviewed text. Split by physical receipt before crops or synthetic distortions. Record blank ID zero and a fixed alphabet. The miniature model below takes already encoded time-step features and performs one valid loss update; it does not claim to detect lines or read photographs. [[deep-learning/ctc-time-length-and-blank-alignment-contract|The CTC contract]] defines legal lengths.'),
    ('Audit width and supervision', 'For every batch, derive encoded time lengths from the actual feature extractor output and original valid crop width, not the padded batch width. Reject empty transcripts unless the workflow explicitly models them. Flag unknown characters and target repetitions that cannot fit the available frames. Save the excluded-line report so quality metrics cannot quietly improve by dropping hard cases. The code provides seven and nine valid time steps for two transcripts and checks that labels contain no blank.'),
    ('Train and decode separately', 'Monitor finite loss, gradient norms and output blank fraction. Decode with the frozen greedy collapse rule; only add beam search if it improves held-out field accuracy enough to justify its time cost. Report character edits, exact line matches, exact total/date matches and manual correction minutes by store format and camera. [[deep-learning/ctc-greedy-collapse-and-error-audit|The decoder lesson]] defines repeated-character behavior. Compare with a non-neural OCR baseline under identical crops and normalization.'),
    ('Validate the pipeline rather than one tensor', 'Run line detection, ordering, crop normalization, encoder, decoder and field parsing on held-out full receipts. Check that a total on the neighboring line is not attributed to the wrong item. Group uncertainty by receipt ID because several line images from one receipt are correlated. Measure p95 wall time including cropping and decoding, and inspect empty or truncated outputs. If a crop omits half a line, a better CTC model cannot recover its missing content.'),
    ('Release with a fallback', 'Predeclare minimum exact-field accuracy, maximum deletion rate on repeated characters, review capacity and p95 end-to-end latency. Package alphabet, blank ID, crop policy, encoded-length calculation, model, decoder and parser versions. Re-run a fixed receipt set after upgrades; route low-confidence or malformed fields to review while retaining the previous OCR path. The deliverable is a field-level error ledger and reproducible deployment bundle, not just a declining training-loss curve.')],
    '''import torch
from torch import nn

torch.manual_seed(47)
line_features = torch.randn(9, 2, 6)
valid_time = torch.tensor([9, 7], dtype=torch.long)
transcript_ids = torch.tensor([1, 2, 2, 3, 1], dtype=torch.long)
transcript_sizes = torch.tensor([3, 2], dtype=torch.long)
assert valid_time.max().item() <= line_features.size(0)
assert transcript_sizes.sum().item() == transcript_ids.numel()
assert not (transcript_ids == 0).any()

character_head = nn.Linear(6, 5)
optimizer = torch.optim.AdamW(character_head.parameters(), lr=0.0007)
optimizer.zero_grad(set_to_none=True)
log_probs = character_head(line_features).log_softmax(-1)
loss = nn.CTCLoss(blank=0, zero_infinity=False)(
    log_probs, transcript_ids, valid_time, transcript_sizes)
assert torch.isfinite(loss)
loss.backward()
optimizer.step()''',
    'A line encoder generally dominates inference cost, while CTC scoring must process valid encoded time steps and transcript lengths. This tiny linear head has O(TBCF) multiply cost for T steps, B lines, C classes and F input features, plus O(TBC) logits memory; a real convolutional encoder adds its own activations. Padding every crop to the widest batch item wastes compute, so bucket similar widths while retaining true lengths. Evaluate end-to-end receipt latency, since detection and ordering may cost more than the character head.',
    ['Do not split line crops from one physical receipt across train and test.', 'Do not use padded width as every sample’s CTC input length.', 'Do not optimize character error while ignoring totals, dates and manual correction cost.'],
    ['deep-learning/ctc-time-length-and-blank-alignment-contract', 'deep-learning/ctc-greedy-collapse-and-error-audit', 'deep-learning/receipt-defect-segmentation-project', 'deep-learning/decoding-stop-rules-and-beam-score', 'deep-learning/inference-schema-and-latency'], CTC, True)

CROSSLINKS = [
    ('deep-learning/occlusion-attribution-and-sanity-checks', 'deep-learning/graph-message-passing-edge-direction-and-self-state'),
    ('deep-learning/augmentation-leakage-boundary', 'deep-learning/graph-neighbor-sampling-and-time-split'),
    ('deep-learning/service-event-lstm-project', 'deep-learning/service-incident-graph-project'),
    ('deep-learning/temperature-scaling-and-selective-risk', 'deep-learning/service-incident-graph-project'),
    ('deep-learning/inference-schema-and-latency', 'deep-learning/service-incident-graph-project'),
    ('deep-learning/convolution-output-geometry-and-receptive-field', 'deep-learning/ctc-time-length-and-blank-alignment-contract'),
    ('deep-learning/causal-target-shift-and-padding-loss', 'deep-learning/ctc-time-length-and-blank-alignment-contract'),
    ('deep-learning/decoding-stop-rules-and-beam-score', 'deep-learning/ctc-greedy-collapse-and-error-audit'),
    ('deep-learning/receipt-defect-segmentation-project', 'deep-learning/receipt-line-ocr-ctc-project'),
    ('deep-learning/receipt-image-quality-project', 'deep-learning/receipt-line-ocr-ctc-project'),
    ('deep-learning/deep-learning-tutorial', 'deep-learning/service-incident-graph-project'),
]

if __name__ == '__main__':
    publish(LESSONS, (GRAPHS, CTC), CROSSLINKS,
            'aitrove-deep-learning-graphs-ctc-import-20261006.json',
            7910, subject='deep-learning')
