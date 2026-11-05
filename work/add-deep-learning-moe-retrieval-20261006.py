"""Add sparse-expert and neural-retrieval Deep Learning paths."""
from de_batch_publisher import publish

EXPERTS = 'Sparse experts, routing and capacity'
RETRIEVAL = 'Neural retrieval and candidate index parity'
LESSONS = []


def add(slug, title, summary, sections, code, cost, mistakes, related, module, project=False):
    assert len(sections) == 5
    LESSONS.append(dict(path='deep-learning/' + slug, title=title, summary=summary,
                        sections=sections, code=code, cost=cost, mistakes=mistakes,
                        related=related, module=module, project=project))


add('sparse-expert-router-and-capacity-accounting',
    'Sparse expert routers and per-batch capacity accounting',
    'An expert router saves per-token computation only if routing, overflow handling and expert utilization are measured as part of the model contract.', [
    ('Route tokens, not whole deployments', 'A mixture-of-experts layer contains several parameter sets called experts. The router scores each token and sends it to a selected subset, often one or two experts, while the surrounding attention and other layers may remain shared. Sparse activation lowers arithmetic per token relative to executing every expert, but all expert weights still have to live somewhere and token exchange across devices can dominate latency. Record the expert count, selected experts per token and router score normalization with the checkpoint. [[deep-learning/scaled-dot-product-attention-mask-contract|Attention masks]] remain a separate sequence contract.'),
    ('Calculate capacity from the actual batch', 'Suppose 47 tokens route to four experts, one expert per token and capacity factor 1.25. A typical per-expert limit is the ceiling of 47 times 1.25 divided by four, or 15 tokens. If the router chooses the first expert for 21 tokens, six exceed its limit despite empty slots elsewhere. The code computes these counts with a deterministic router. Define whether overflow is dropped, sent to a backup expert or processed by a shared path; each choice changes output quality and cost.'),
    ('Avoid an invisible order effect', 'A naive capacity loop admits tokens in their input order. Reordering the same batch can then alter which tokens get expert computation. Some systems prioritize stronger router scores or use a specified token-dispatch rule. Record the rule and test both original and reordered batches. A full sentence might be split across batches at inference, so a batch-dependent overflow policy can create inconsistent answers. Capacity is a serving behavior, not merely a training-memory switch.'),
    ('Watch concentration before tuning loss', 'Count routed and accepted tokens per expert, overflow rate, entropy of router choices and accuracy by input slice. A router that sends nearly everything to one expert defeats the intended parallelism and can starve the others of gradients. Auxiliary balancing objectives may reduce concentration, yet an excessive coefficient can force artificial uniformity when tasks are genuinely uneven. [[deep-learning/expert-load-balance-and-dispatch-consistency|The balance lesson]] compares utilization with task loss and device cost.'),
    ('Choose a dense baseline', 'A dense feed-forward block with comparable active computation gives a meaningful reference. Compare quality, total parameter memory, accelerator communication, p95 latency and training stability under the same token budget. If a sparse layer wins only at a batch size unavailable in production, it has not met the serving requirement. [[deep-learning/service-event-sparse-experts-project|The project]] tests service-event classification with bounded overflow and a rollback to its dense baseline.')],
    '''from math import ceil

def dispatch_experts(router_choices, expert_count, capacity_factor):
    if expert_count < 1 or capacity_factor <= 0:
        raise ValueError("expert count and capacity factor must be positive")
    if not router_choices:
        return [], [0] * expert_count, 0
    capacity = ceil(len(router_choices) * capacity_factor / expert_count)
    accepted = [0] * expert_count
    assignments = []
    for expert_id in router_choices:
        if not 0 <= expert_id < expert_count:
            raise ValueError("router selected an unknown expert")
        if accepted[expert_id] < capacity:
            assignments.append(expert_id)
            accepted[expert_id] += 1
        else:
            assignments.append(None)
    return assignments, accepted, capacity

choices = [0] * 21 + [1] * 9 + [2] * 9 + [3] * 8
assignments, utilization, per_expert_limit = dispatch_experts(choices, 4, 1.25)
assert per_expert_limit == 15
assert utilization == [15, 9, 9, 8]
assert assignments.count(None) == 6''',
    'Computing a selected expert for each of T tokens is O(T) routing decisions after router scores exist; scoring E experts per token adds O(TE) work and score storage unless selection is fused. Expert forward work depends on accepted tokens and active width, while parameters scale with all E experts. On multiple devices, all-to-all token exchange and imbalance can dominate. The example counts top-one capacity only and intentionally leaves overflow unprocessed so the loss is visible.',
    ['Do not assume sparse activation means low total parameter memory.', 'Do not drop overflow tokens without measuring which tasks they contain.', 'Do not compare expert throughput to a dense model at a different token budget.'],
    ['deep-learning/expert-load-balance-and-dispatch-consistency', 'deep-learning/service-event-sparse-experts-project', 'deep-learning/scaled-dot-product-attention-mask-contract', 'deep-learning/distributed-sampler-tail-and-global-loss-weighting', 'deep-learning/inference-schema-and-latency'], EXPERTS)

add('expert-load-balance-and-dispatch-consistency',
    'Expert load balance, overflow slices and dispatch consistency',
    'A routed model needs both predictive checks and systems checks: expert collapse, token overflow, device skew and inference-time batching can each undo the expected gain.', [
    ('Measure offered and accepted load', 'Offered load counts the router’s first-choice tokens. Accepted load counts tokens an expert actually processes after capacity is enforced. Reporting only the latter can hide an expert receiving many requests and silently dropping the excess. Keep per-expert histograms by batch, input category and sequence position, then inspect whether rare service-event types are overrepresented in overflow. [[deep-learning/sparse-expert-router-and-capacity-accounting|The router lesson]] provides the capacity arithmetic.'),
    ('Balance without forcing sameness', 'A balance term can encourage traffic across experts, but uniform use is a proxy for healthy training, not the objective itself. Compare task loss and expert utilization as the coefficient changes. Expert collapse can leave some weights nearly untrained; too much balancing can send a token to an unhelpful expert. Freeze a few reviewed examples and trace router choices through training. An auxiliary loss needs its own unit, weighting and checkpoint metadata.'),
    ('Make dispatch deterministic where required', 'For a fixed checkpoint and token batch, router scores, tie handling and overflow priority should yield a repeatable output within numeric tolerance. Random token shuffling during training can reduce order bias but must not be an unexplained inference dependency. Test a single input alone, in a crowded batch and after changing batch order. When output changes because capacity was exceeded, document it as a model limitation rather than calling it harmless batching variation.'),
    ('Account for communication', 'With experts spread over devices, tokens must travel to the device holding each expert and their outputs must return. A model may reduce multiply-adds while increasing transfer volume and synchronization. Profile dispatch bytes, all-to-all time, expert idle time, peak memory and p95 request latency at the actual serving mix. Compare with a dense model at the same accuracy target. [[deep-learning/distributed-checkpoint-manifest-and-resume|Distributed checkpoints]] must also preserve the expert-to-device mapping or a portable remap.'),
    ('Gate using both quality and operation', 'Report accuracy by event class, overflow by event class, accepted load skew and full-path latency. A rollout gate can require no class with rising overflow, bounded expert skew, and a meaningful gain over a dense baseline at the same cost envelope. [[deep-learning/service-event-sparse-experts-project|The applied project]] uses these conditions before a shadow release. If a gate fails, use the dense model; adding experts blindly can amplify the failure.')],
    '''from collections import Counter

def audit_dispatch(offered, accepted, expert_count):
    if len(offered) != len(accepted):
        raise ValueError("offered and accepted streams must align")
    if any(expert not in range(expert_count) for expert in offered):
        raise ValueError("unknown offered expert")
    if any(expert is not None and expert not in range(expert_count)
           for expert in accepted):
        raise ValueError("unknown accepted expert")
    offered_counts = Counter(offered)
    accepted_counts = Counter(expert for expert in accepted if expert is not None)
    return [(offered_counts[index], accepted_counts[index])
            for index in range(expert_count)]

offered = [0, 0, 0, 0, 1, 1, 2, 3]
accepted = [0, 0, 0, None, 1, 1, 2, 3]
counts = audit_dispatch(offered, accepted, expert_count=4)
assert counts == [(4, 3), (2, 2), (1, 1), (1, 1)]
assert sum(requested - processed for requested, processed in counts) == 1''',
    'The audit traverses T routing records in O(T + E) time and O(E) counter space for E experts. A production trace may add token IDs, sequence positions and device IDs, increasing storage linearly with T. Dense baselines avoid expert all-to-all exchange but execute more active weights per token; sparse performance therefore depends on expert placement, batch composition and overflow rules rather than parameter count alone.',
    ['Do not report accepted load without offered load and overflow.', 'Do not interpret uniform routing as proof of useful expert specialization.', 'Do not omit batch composition from latency and output-parity tests.'],
    ['deep-learning/sparse-expert-router-and-capacity-accounting', 'deep-learning/service-event-sparse-experts-project', 'deep-learning/distributed-checkpoint-manifest-and-resume', 'deep-learning/inference-schema-and-latency', 'deep-learning/temperature-scaling-and-selective-risk'], EXPERTS)

add('service-event-sparse-experts-project',
    'Project: test sparse experts for service-event classification',
    'Compare a small expert layer with a dense classifier on the same time-split event data, then gate on class quality, overflow, device cost and batch parity.', [
    ('Prepare the event ledger', 'Collect service-event text and structured attributes with event time, source system, class label and incident group. Split by incident and time before constructing token batches. Remove identifiers that encode the answer or appear after the classification decision. Include rare incident classes and quiet periods; a sparse model might appear strong on frequent routine events while discarding the very class that matters to operators. [[deep-learning/causal-target-shift-and-padding-loss|The target boundary]] applies to event sequences as well as language generation.'),
    ('Set a dense reference', 'Train a compact shared encoder and dense classifier with the same input tokens, optimizer budget and held-out incidents. Its class recall, calibration, memory and p95 latency form the baseline. The snippet routes four synthetic token features through two experts without a capacity limit; it verifies the tensor path and finite loss only. The full project must add capacity accounting and overflow handling before making a performance claim. [[deep-learning/sparse-expert-router-and-capacity-accounting|The router lesson]] gives the operational contract.'),
    ('Inspect expert behavior', 'Track first-choice and accepted tokens per expert, overflow by event class and how often experts receive gradients. Compare alone-versus-batched predictions for reviewed incidents at serving batch sizes. A load-balancing term can move traffic while worsening rare-class recall, so publish both curves. [[deep-learning/expert-load-balance-and-dispatch-consistency|The balance lesson]] ties the histograms to the release gate.'),
    ('Profile the real path', 'Include tokenization, routing, expert dispatch, output gathering and final thresholding. If experts occupy separate accelerators, measure communication bytes and idle time; if they share one device, measure total resident weights. Repeat with the intended concurrency and sequence-length distribution. Compare accuracy at a fixed compute and latency envelope, not only parameter totals. A model that misses the deadline for long events is not an operational improvement.'),
    ('Release only a bounded shadow', 'Score incoming events without changing routing decisions, then review disagreements and overflow. Require no deterioration in severe-incident recall, a published overflow ceiling for every class, stable batching parity and an agreed p95 latency. Package the router, experts, tokenization, capacity and fallback as one versioned artifact. Retain the dense model for immediate rollback; record why any event took a fallback path.')],
    '''import torch
from torch import nn
from torch.nn import functional as functional

torch.manual_seed(47)
event_features = torch.rand(4, 6)
reviewed_classes = torch.tensor([0, 1, 2, 1])
router = nn.Linear(6, 2)
experts = nn.ModuleList([nn.Linear(6, 8), nn.Linear(6, 8)])
classifier = nn.Linear(8, 3)
route_logits = router(event_features)
expert_choice = route_logits.argmax(dim=1)
expert_outputs = torch.stack([expert(event_features) for expert in experts], dim=1)
selected = expert_outputs[torch.arange(len(event_features)), expert_choice]
class_logits = classifier(torch.relu(selected))
loss = functional.cross_entropy(class_logits, reviewed_classes)
loss.backward()
assert class_logits.shape == (4, 3) and torch.isfinite(loss)''',
    'This tiny demonstration evaluates every expert and then selects one, so its compute is O(TEF) rather than truly sparse; it is a safe tensor-path check, not a throughput demonstration. A production dispatcher computes only selected expert outputs but adds grouping, exchange and overflow costs. Resident weights still grow with expert count, while active expert arithmetic grows with selected experts per token. Measure the full path against the dense reference before claiming any gain.',
    ['Do not cite this all-experts toy forward as proof of sparse serving speed.', 'Do not hide severe-event overflow inside an aggregate average.', 'Do not release the expert layer without the exact router and capacity version.'],
    ['deep-learning/sparse-expert-router-and-capacity-accounting', 'deep-learning/expert-load-balance-and-dispatch-consistency', 'deep-learning/distributed-checkpoint-manifest-and-resume', 'deep-learning/inference-schema-and-latency', 'deep-learning/temperature-scaling-and-selective-risk'], EXPERTS, True)

add('two-tower-embedding-and-inbatch-negative-contract',
    'Two-tower embeddings and in-batch negative contracts',
    'Separate a query encoder from an item encoder so candidate vectors can be indexed, while keeping positives, accidental duplicates and exposure bias visible during training.', [
    ('Give each tower one job', 'A learning feed can encode a reader’s recent topics in a query tower and encode an article’s topic, level and text in an item tower. Both emit vectors with the same dimension; their dot product supplies a retrieval score. Item vectors can be prepared ahead of time, leaving only the query tower and nearest-neighbor search on the request path. Keep the feature schema, normalization and index version together. [[recommendation-systems/candidate-retrieval-and-eligibility|Candidate eligibility]] still filters items a user cannot or should not see.'),
    ('Construct positives from eligible exposure', 'A completed lesson is a useful positive signal, but an unseen lesson is not automatically a disliked negative. Record what was actually shown, when, where and under which ranking policy. For held-out evaluation, split by time and reader before building training pairs. A query representation that includes clicks after the target event leaks the answer. [[recommendation-systems/implicit-feedback-and-exposure-bias|Exposure bias]] explains why observed interactions are not a complete preference map.'),
    ('Handle false negatives within the batch', 'A common training matrix pairs each query with its own positive item and treats other items in that mini-batch as negatives. If two readers completed the same article, that article appears twice and the off-diagonal copy is a false negative. Build a mask by item ID or use a multi-positive objective. The code validates unique item IDs for a deliberately simple diagonal loss; a real batch builder must enforce that invariant or change the objective. Hard negatives need the same eligibility and time checks.'),
    ('Choose score scale and embedding norm', 'Dot-product logits depend on vector magnitude; normalized vectors yield cosine-like scores, while a temperature controls softmax sharpness during training. Neither choice alone fixes biased negatives. Monitor embedding norms, score distribution and query groups. A model can learn popularity alone if item frequency overwhelms the query signal. Compare against a topical or popularity baseline, especially for new readers and new articles.'),
    ('Evaluate full-corpus retrieval', 'A batch classification loss tests only the current mini-batch. Report recall at a chosen candidate count against the entire eligible article corpus or a stable evaluation snapshot, then inspect recall by topic, reader history and publication age. The nearest-neighbor index can lose some exact neighbors; measure that gap separately from model quality. [[deep-learning/retrieval-index-version-and-candidate-parity|The index lesson]] makes that parity check explicit.')],
    '''import torch
from torch import nn
from torch.nn import functional as functional

torch.manual_seed(47)
reader_features = torch.rand(4, 5)
article_features = torch.rand(4, 7)
positive_article_ids = [47, 58, 69, 81]
assert len(set(positive_article_ids)) == len(positive_article_ids)
reader_tower = nn.Linear(5, 8)
article_tower = nn.Linear(7, 8)
reader_vectors = functional.normalize(reader_tower(reader_features), dim=1)
article_vectors = functional.normalize(article_tower(article_features), dim=1)
pair_scores = reader_vectors @ article_vectors.T / 0.17
matched_positions = torch.arange(len(reader_features))
loss = functional.cross_entropy(pair_scores, matched_positions)
loss.backward()
assert pair_scores.shape == (4, 4) and torch.isfinite(loss)''',
    'For a batch of B queries and B candidate items with embedding width D, the score matrix costs O(B squared D) arithmetic and O(B squared) memory, which can dominate large-batch training. Precomputing M item vectors costs O(MD) index storage. Query encoding plus approximate search is cheaper than scanning all M items at serve time, but index build, filtering and freshness add separate costs. This synthetic update checks tensor geometry only and assumes unique positives.',
    ['Do not treat unexposed articles as confirmed dislikes.', 'Do not allow duplicate positive item IDs to become false in-batch negatives.', 'Do not use mini-batch accuracy as full-corpus retrieval recall.'],
    ['deep-learning/retrieval-index-version-and-candidate-parity', 'deep-learning/learning-feed-two-tower-project', 'recommendation-systems/implicit-feedback-and-exposure-bias', 'recommendation-systems/candidate-retrieval-and-eligibility', 'deep-learning/contrastive-temperature-and-negative-mask'], RETRIEVAL)

add('retrieval-index-version-and-candidate-parity',
    'Retrieval index versions, eligibility filters and candidate parity',
    'A good embedding model can serve the wrong recommendations when the item index is stale, the vector schema changes or eligibility is applied too late.', [
    ('Treat the index as a model artifact', 'An item vector is valid only for the item encoder, tokenizer, feature schema and normalization rule that produced it. Save those fingerprints with the index. Deploying a new query tower against an old article index can change scores without any code error. Publish the index build time, source article revision, item count and tombstone count. [[deep-learning/two-tower-embedding-and-inbatch-negative-contract|The two-tower lesson]] defines the matching vector space.'),
    ('Filter before promising a candidate', 'Remove unpublished, restricted, duplicate and already-completed articles using the eligibility state available at request time. Some approximate search systems retrieve a wide set and filter afterward; if most results fail eligibility, the final list may be short or skewed. Measure eligible yield and over-fetch needs by reader group. A score is not permission to display an item. [[recommendation-systems/candidate-retrieval-and-eligibility|The recommendation contract]] handles business eligibility beyond embedding similarity.'),
    ('Compare exact and indexed neighbors', 'For sampled queries, compute exact dot products against the same frozen eligible corpus and compare their top candidates with the approximate index. Report index recall at K, latency and memory under several parameter settings. If the exact model misses the relevant lesson, rebuilding the index will not fix it; if the exact result is good but the index drops it, retraining the towers is premature. The code performs a tiny exact ranking and an eligibility filter as a deterministic oracle.'),
    ('Handle publication and deletion explicitly', 'New articles should not wait indefinitely for a full nightly rebuild. Define incremental addition, replacement and deletion behavior, then verify that unpublished or withdrawn items disappear from every shard. A tombstoned item can survive in a cached candidate list after the index is updated. Record freshness delay from publish or withdraw event to served result, and add a last-mile eligibility check at response construction.'),
    ('Gate on real request shapes', 'Measure p95 query encoding, index search, eligibility filtering and ranking separately, then measure the end-to-end request. Test sparse reader histories, new content, long-tail topics and a sudden catalog update. [[deep-learning/learning-feed-two-tower-project|The project]] compares indexed retrieval with a topic baseline and checks the same versioned result in a live-like replay.')],
    '''def eligible_top_k(query_vector, indexed_articles, allowed_ids, limit):
    if len(query_vector) == 0 or limit < 1:
        raise ValueError("query width and limit must be positive")
    ranked = []
    for article_id, article_vector in indexed_articles.items():
        if len(article_vector) != len(query_vector):
            raise ValueError("embedding width changed")
        if article_id in allowed_ids:
            score = sum(query * item for query, item in zip(query_vector, article_vector))
            ranked.append((score, article_id))
    ranked.sort(key=lambda result: (-result[0], result[1]))
    return [article_id for _, article_id in ranked[:limit]]

article_index = {47: (0.8, 0.2), 58: (0.1, 0.9), 69: (0.6, 0.4)}
visible_articles = {47, 69}
assert eligible_top_k((0.7, 0.3), article_index, visible_articles, 2) == [47, 69]''',
    'Exact scoring of M indexed items at width D uses O(MD) arithmetic, and sorting all eligible candidates uses O(M log M) time and O(M) temporary storage. A heap can reduce top-K selection cost when K is small, while an approximate index trades some neighbor recall for faster search. Eligibility filtering and index freshness still require explicit work. The tiny oracle is for parity tests, not a large-catalog serving implementation.',
    ['Do not pair a new query encoder with stale item vectors without a version check.', 'Do not let restricted or withdrawn items survive in a cached result.', 'Do not report index recall against a corpus with different eligibility rules.'],
    ['deep-learning/two-tower-embedding-and-inbatch-negative-contract', 'deep-learning/learning-feed-two-tower-project', 'recommendation-systems/candidate-retrieval-and-eligibility', 'recommendation-systems/offline-evaluation-and-temporal-split', 'deep-learning/inference-schema-and-latency'], RETRIEVAL)

add('learning-feed-two-tower-project',
    'Project: retrieve learning articles with two neural towers',
    'Build a versioned candidate index for a learning feed, then test full-corpus recall, eligibility, new-content freshness and request latency.', [
    ('Define the reader event ledger', 'Store article impressions, clicks and completed lessons with reader ID, event time, surface and policy version. Build a reader state from events strictly before the candidate decision, then pair it with a completed article that was eligible and exposed. Split by reader and time for a final evaluation. Keep new readers and new articles as named slices. [[recommendation-systems/objective-and-interaction-contract|The interaction contract]] explains why a click and a completed lesson should not have identical weight.'),
    ('Train with deliberate negatives', 'The snippet runs one synthetic matched-pair update and asserts that each positive article appears once in the batch. Real training must deduplicate item IDs or support multiple positives, and may add reviewed hard negatives only from eligible exposed items. Compare against a topic-match baseline and a popularity baseline with identical catalog and time boundaries. [[deep-learning/two-tower-embedding-and-inbatch-negative-contract|The embedding lesson]] gives the loss and false-negative caveat.'),
    ('Build a coupled index', 'Export item vectors alongside encoder and feature-schema fingerprints. Build a candidate index from published articles, maintain tombstones and check incremental additions. At serving, encode the reader with the matching query tower, retrieve more than the final count, filter eligibility and return a bounded list. Compare exact top-K and indexed top-K on fixed queries to isolate index error. [[deep-learning/retrieval-index-version-and-candidate-parity|The index lesson]] defines the replay oracle.'),
    ('Evaluate the feed, not the training batch', 'Report full-corpus recall at candidate count, eligible yield, catalog coverage and recall by new reader, new article and topic. Separately audit withdrawn-item leaks and the delay before a new article appears. Measure p95 query encoding, index search, filtering and total request time on the target catalog size. A candidate system that retrieves only popular old pages can look strong on interaction-weighted recall while failing discovery.'),
    ('Release with a clear fallback', 'Package both towers, article vectors, index version, eligibility snapshot rule and rollback pointer. Run a shadow replay first, compare candidate sets and investigate blocked items. Gate on full-corpus recall, freshness, zero restricted-item exposure and request latency. Keep a simple eligible-topic baseline ready if the index is stale or unavailable; never relax eligibility to fill the feed.')],
    '''import torch
from torch import nn
from torch.nn import functional as functional

torch.manual_seed(47)
reader_context = torch.rand(4, 5)
article_metadata = torch.rand(4, 7)
positive_article_ids = [47, 58, 69, 81]
assert len(positive_article_ids) == len(set(positive_article_ids))
query_tower = nn.Linear(5, 8)
item_tower = nn.Linear(7, 8)
optimizer = torch.optim.AdamW(list(query_tower.parameters()) +
                              list(item_tower.parameters()), lr=0.0007)
query_vectors = functional.normalize(query_tower(reader_context), dim=1)
item_vectors = functional.normalize(item_tower(article_metadata), dim=1)
candidate_logits = query_vectors @ item_vectors.T / 0.17
loss = functional.cross_entropy(candidate_logits, torch.arange(4))
optimizer.zero_grad(set_to_none=True)
loss.backward()
optimizer.step()
assert candidate_logits.shape == (4, 4) and torch.isfinite(loss)''',
    'The in-batch B-by-B score matrix costs O(B squared D) operations for embedding width D and O(B squared) memory, on top of tower computation. An index for M published items stores O(MD) vector values plus search metadata. Exact full-catalog evaluation is more expensive than a small training-batch check; sample queries but keep the corpus complete and frozen. The code proves one synthetic update, not recommendation quality or index readiness.',
    ['Do not treat a single batch loss as a feed-quality metric.', 'Do not publish an item-vector index without encoder and schema fingerprints.', 'Do not bypass eligibility when the index returns too few candidates.'],
    ['deep-learning/two-tower-embedding-and-inbatch-negative-contract', 'deep-learning/retrieval-index-version-and-candidate-parity', 'recommendation-systems/offline-evaluation-and-temporal-split', 'recommendation-systems/lesson-feed-project', 'deep-learning/inference-schema-and-latency'], RETRIEVAL, True)

CROSSLINKS = [
    ('deep-learning/scaled-dot-product-attention-mask-contract', 'deep-learning/sparse-expert-router-and-capacity-accounting'),
    ('deep-learning/distributed-sampler-tail-and-global-loss-weighting', 'deep-learning/expert-load-balance-and-dispatch-consistency'),
    ('deep-learning/inference-schema-and-latency', 'deep-learning/service-event-sparse-experts-project'),
    ('deep-learning/contrastive-temperature-and-negative-mask', 'deep-learning/two-tower-embedding-and-inbatch-negative-contract'),
    ('recommendation-systems/candidate-retrieval-and-eligibility', 'deep-learning/retrieval-index-version-and-candidate-parity'),
    ('recommendation-systems/implicit-feedback-and-exposure-bias', 'deep-learning/two-tower-embedding-and-inbatch-negative-contract'),
    ('recommendation-systems/lesson-feed-project', 'deep-learning/learning-feed-two-tower-project'),
    ('deep-learning/inference-schema-and-latency', 'deep-learning/learning-feed-two-tower-project'),
    ('deep-learning/deep-learning-tutorial', 'deep-learning/learning-feed-two-tower-project'),
]

if __name__ == '__main__':
    publish(LESSONS, (EXPERTS, RETRIEVAL), CROSSLINKS,
            'aitrove-deep-learning-moe-retrieval-import-20261006.json',
            7960, subject='deep-learning')
