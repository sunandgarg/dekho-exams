"""Add original product-analysis lessons to the Data Science path."""
import datetime
import html
import json
from pathlib import Path
import re
import uuid

root = Path(__file__).resolve().parents[1]
fixture = root / 'src/data/fixtures.json'
rows = json.loads(fixture.read_text())
slugs = (
    'product-event-contract-and-identity',
    'ordered-funnel-and-conversion-window',
    'retention-cohort-and-maturity',
    'instrumentation-change-and-metric-guardrails',
    'checkout-funnel-retention-project',
)
new_paths = {'data-science/' + slug for slug in slugs}
rows = [row for row in rows if row['path'] not in new_paths]
by_path = {row['path']: row for row in rows}
stamp = datetime.datetime.now(datetime.UTC).isoformat()
lessons = []

def add(slug, title, summary, sections, code, cost, mistakes, related):
    lessons.append(dict(path='data-science/' + slug, title=title, summary=summary,
                        sections=sections, code=code, cost=cost,
                        mistakes=mistakes, related=related))

add('product-event-contract-and-identity',
    'Product event contracts: identity, deduplication and eligibility',
    'Behavior analysis needs a stable event identity and a declared user or session unit before any funnel is counted.', [
    ('Specify one event precisely', 'A checkout-start event should have a stable event ID, actor ID, session ID, cart ID, occurrence time, recorded time, platform and schema version. A page view is not a checkout start merely because the checkout route loaded: retries, prefetches and refreshes can create extra views. Define the business event and its emission point. [[streaming-analytics/event-contract-and-partition-key|An event contract]] keeps production instrumentation and analysis aligned.'),
    ('Choose the counting unit', 'A buyer can use two devices and three carts. Counting anonymous device IDs estimates device journeys; counting signed-in users estimates people only when identity is available and permitted. Session funnels answer a different question from user funnels. Document when anonymous and authenticated IDs are joined, and whether a late identity merge restates old reports. [[data-science/dataset-grain-and-join-cardinality|Dataset grain]] prevents an event-to-cart join from multiplying users.'),
    ('Deduplicate before sequencing', 'At-least-once delivery can replay one event. Keep the first valid instance for each event ID under a declared revision rule, and record conflicting payloads rather than silently choosing one. If the same business action receives two distinct IDs, event-ID deduplication alone is insufficient; a cart transition key or source transaction ID may be needed. The analysis should publish raw, duplicate and accepted counts by day and platform.'),
    ('Freeze eligibility', 'Decide whether employees, test accounts, bots and users without measurement consent are eligible before looking at conversion rates. Keep exclusion reasons and counts. A new consent banner can alter measured population composition even when customer behavior is unchanged. [[data-science/sampling-frame-and-coverage-error|Coverage analysis]] asks who never entered the event frame.'),
    ('Audit a concrete fixture', 'Create 53 raw checkout-start records with three replayed IDs, two conflicting payloads and one missing actor ID. The accepted event count depends on the collision policy, but every discarded record must be accounted for. Compare unique users and unique sessions separately. Never quote a conversion denominator from an event stream that has not passed this reconciliation.')],
    'def dedupe_checkout_events(raw_events):\n    accepted = {}\n    conflicts = []\n    for event in raw_events:\n        event_id = event["event_id"]\n        prior = accepted.get(event_id)\n        if prior is None:\n            accepted[event_id] = event\n        elif prior != event:\n            conflicts.append(event_id)\n    return list(accepted.values()), conflicts\n\naccepted_events, conflicting_ids = dedupe_checkout_events([\n    {"event_id": "evt-47", "actor_id": "buyer-19"},\n    {"event_id": "evt-47", "actor_id": "buyer-19"},\n    {"event_id": "evt-47", "actor_id": "buyer-24"},\n])\nassert len(accepted_events) == 1 and conflicting_ids == ["evt-47"]',
    'Deduplication over N records takes O(N) expected time and O(U) memory for U unique event IDs. Identity resolution and conflict review have separate costs; a streaming implementation needs bounded state or a persistent event-key index.',
    ['Do not equate a page view with a business event without an emission contract.', 'Do not mix device, session and user denominators in one funnel.', 'Do not drop conflicting event IDs without preserving an audit record.'],
    ['data-science/ordered-funnel-and-conversion-window','data-science/retention-cohort-and-maturity','data-science/sampling-frame-and-coverage-error','data-science/checkout-funnel-retention-project'])

add('ordered-funnel-and-conversion-window',
    'Ordered funnels: step order, entry rules and conversion windows',
    'A funnel counts units that complete declared steps in order within a stated observation window.', [
    ('Decide who may enter', 'A closed checkout funnel begins only with an eligible checkout-start event. An open funnel can begin at a later step, which answers a different question. Choose one before computing stage rates. If users may restart checkout, decide whether to analyze first attempt, every attempt or one attempt per session. [[data-science/product-event-contract-and-identity|Event identity]] sets the unit; the funnel rule sets the sequence.'),
    ('Enforce order and time', 'Suppose the steps are checkout start, payment attempt and order confirmation. A payment attempt before the selected checkout start does not qualify, even if it belongs to the same user. A confirmation 73 hours later should not count for a 48-hour funnel. Process each actor’s accepted events in occurrence-time order, with event ID as a stable tie-break. Use a half-open window if the boundary matters, and write down whether exactly 48 hours qualifies.'),
    ('Protect the observation cutoff', 'A checkout that began an hour before today’s data cutoff has not had 48 hours to convert. Either exclude immature entries from the fully observed 48-hour rate or report them as still pending. Treating pending entries as failures biases recent cohorts downward. [[data-science/right-censoring-and-time-to-event|Censored outcomes]] provide another analysis route when the full conversion-time distribution matters.'),
    ('Report both conditional and entry rates', 'If 83 users entered, 57 attempted payment and 41 confirmed an order, payment-to-confirmation is 41/57 while entry-to-confirmation is 41/83. These are not interchangeable. Publish counts, conditional stage rates and the total entry rate. A stage can improve while the full funnel worsens if the incoming mix changes. [[data-science/subgroup-distribution-and-aggregation-reversal|Composition checks]] belong beside the chart.'),
    ('Inspect missing paths', 'A user may complete a purchase without a recorded payment-attempt event because of an alternate wallet flow or instrumentation gap. Do not force that path into a failed step. Count and inspect skipped-step sequences. A changed payment provider can alter event emission without changing orders, so reconcile confirmations against the transaction ledger before assigning blame to customer behavior.')],
    'def completed_checkout(accepted_events, actor_id, window_minutes=2880):\n    actor_events = sorted(\n        (event for event in accepted_events if event["actor_id"] == actor_id),\n        key=lambda event: (event["minute"], event["event_id"]),\n    )\n    entry_minute = None\n    payment_seen = False\n    for event in actor_events:\n        if entry_minute is None:\n            if event["kind"] == "checkout_start":\n                entry_minute = event["minute"]\n            continue\n        if event["minute"] - entry_minute > window_minutes:\n            return False\n        if event["kind"] == "checkout_start":\n            return False  # This report measures the first attempt only.\n        if event["kind"] == "payment_attempt":\n            payment_seen = True\n        elif payment_seen and event["kind"] == "order_confirmed":\n            return True\n    return False\n\nassert completed_checkout([\n    {"actor_id": "buyer-23", "event_id": "e1", "minute": 5, "kind": "checkout_start"},\n    {"actor_id": "buyer-23", "event_id": "e2", "minute": 8, "kind": "payment_attempt"},\n    {"actor_id": "buyer-23", "event_id": "e3", "minute": 11, "kind": "order_confirmed"},\n], "buyer-23")',
    'Sorting E events for one actor costs O(E log E) time and O(E) memory; the state-machine scan is O(E). The report deliberately measures the first attempt and ends it at a restart. A session-based or every-attempt funnel needs a different attribution rule, stated before counting.',
    ['Do not count later-step events that occurred before funnel entry.', 'Do not mark recent entries as failures before their conversion window closes.', 'Do not report a stage-to-stage rate as if it were the rate from initial entry.'],
    ['data-science/product-event-contract-and-identity','data-science/retention-cohort-and-maturity','data-science/instrumentation-change-and-metric-guardrails','data-science/checkout-funnel-retention-project'])

add('retention-cohort-and-maturity',
    'Retention cohorts: return behavior only after a full observation window',
    'A retention rate compares members who entered together and had the same opportunity to return.', [
    ('Anchor membership once', 'For an acquisition cohort, assign each eligible user to the week of first verified purchase. Do not move the user to a new cohort after a later purchase or identity merge without versioning the report. Retention needs a declared return event: another paid order, any app visit or an active subscription are different outcomes. [[data-science/product-event-contract-and-identity|The event contract]] must distinguish them.'),
    ('Specify the return interval', 'Week-one retention can mean activity in days 7 through 13 after entry, activity by day 14, or activity during the next calendar week. Choose one. For the first definition, a user with a return on day 4 does not qualify unless they return again in days 7 through 13. Use the same timezone and day-boundary convention for all users. A calendar-week chart can otherwise mix seven-day and one-day opportunities.'),
    ('Exclude immature cohorts from the comparable rate', 'A user acquired nine days before cutoff has not completed the full days-7-through-13 window. Include that user in the cohort count but mark their retention outcome pending. Calculate the observed week-one rate only over users with enough follow-up, and show pending count. Dropping the pending row from the cohort entirely hides acquisition volume. [[data-science/cohort-entry-and-survivorship-bias|Cohort entry]] and [[data-science/right-censoring-and-time-to-event|censoring]] explain why this distinction matters.'),
    ('Keep composition beside retention', 'Compare acquisition channel, first-order value band and region across cohorts. A recent campaign may bring more one-time buyers and lower the pooled return rate while every channel’s within-channel rate remains stable. Standardize only when the target question calls for a fixed mix; retain the actual cohort rate for operational planning. Do not claim a product change caused the shift from a before-and-after table.'),
    ('Make a hand-checkable example', 'In a cohort of 47 acquired users, 38 have completed the full week-one window. Eleven of those 38 made a qualifying return; nine remain pending. The observed mature-user return fraction is 11/38. Counting pending users as nonreturning gives 11/47 and answers a different, premature question. Publish both the mature denominator and pending count.')],
    'def week_one_retention(purchases, acquisition_day, analysis_day):\n    matured = acquisition_day + 14 <= analysis_day\n    if not matured:\n        return None\n    return any(7 <= purchase_day - acquisition_day < 14\n               for purchase_day in purchases)\n\nassert week_one_retention([3, 9], 0, 20) is True\nassert week_one_retention([3], 0, 20) is False\nassert week_one_retention([9], 0, 10) is None',
    'Checking P purchase days for one user costs O(P) time and O(1) auxiliary space. A warehouse implementation groups purchases by stable user ID and cohort date; sorting or indexing makes interval lookups faster, but identity merges and late events can still restate historical cohorts.',
    ['Do not compare immature recent cohorts with fully observed older cohorts.', 'Do not call any return within 14 days week-one retention without defining the interval.', 'Do not assign a repeat buyer to a new acquisition cohort.'],
    ['data-science/ordered-funnel-and-conversion-window','data-science/instrumentation-change-and-metric-guardrails','data-science/cohort-entry-and-survivorship-bias','data-science/checkout-funnel-retention-project'])

add('instrumentation-change-and-metric-guardrails',
    'Instrumentation changes and metric guardrails for product analysis',
    'An event-count shift can be a collection change; reconcile product signals before treating it as behavior.', [
    ('Detect breaks in collection', 'After an app release, checkout-start events fall 28% while confirmed orders remain flat. That pattern does not prove the start experience improved. Check event volume by app version, platform, consent state and route. A renamed event, a client-side failure or a shorter session timeout can all change the numerator. [[data-science/product-event-contract-and-identity|Event-contract versions]] should be recorded with every emitted event.'),
    ('Compare to an independent ledger', 'Reconcile order confirmations to server-side paid orders using transaction IDs and a known timing window. Compare event totals, distinct transactions, unmatched client events and unmatched ledger rows. If the ledger is delayed, label the report provisional rather than forcing equality at the current minute. An independent ledger helps locate instrumentation faults but has its own exclusions, cancellations and reversals.'),
    ('Choose guardrails before changing the funnel', 'A checkout experiment may increase completed orders while also increasing refunds, failed payments or support contacts. Predeclare those guardrails and their eligible denominators. The success metric and the guardrails should use compatible exposure populations and observation windows. [[online-experimentation/metric-denominators-and-guardrails|Experiment metric contracts]] make trade-offs explicit.'),
    ('Version every published comparison', 'Record analysis code, event schema version, identity rule, eligibility rule, conversion window, cutoff and report revision. If an instrumentation fix backfills missing starts, publish a restatement of both the count and rate. Do not splice a pre-fix series to a post-fix series without marking the break. [[data-science/reproducible-analysis-snapshot|A frozen snapshot]] gives reviewers one stable target.'),
    ('Build a discrepancy threshold with context', 'Suppose 1,217 paid transactions exist in the ledger and 1,204 distinct confirmation events match them within one day. The unmatched 13 need investigation; they are not automatically data loss because the ledger may include manually entered orders. Define an acceptable discrepancy by source and delay, inspect a sample, and stop publication when a critical mismatch exceeds its stated limit.')],
    'def reconcile_transactions(ledger_ids, confirmation_ids):\n    ledger = set(ledger_ids)\n    confirmations = set(confirmation_ids)\n    return {"matched": len(ledger & confirmations),\n            "ledger_only": ledger - confirmations,\n            "event_only": confirmations - ledger}\n\nresult = reconcile_transactions({"order-41", "order-42"},\n                                {"order-41", "order-47"})\nassert result["matched"] == 1\nassert result["ledger_only"] == {"order-42"}',
    'Set reconciliation costs O(L + E) expected time and space for L ledger IDs and E event IDs. At production scale, keyed joins can run incrementally, but delayed arrivals require a retained matching window and explicit revision policy.',
    ['Do not interpret an event-count break as customer behavior without checking collection changes.', 'Do not reconcile transaction counts while ignoring distinct transaction IDs.', 'Do not change a metric definition mid-series without a versioned restatement.'],
    ['data-science/product-event-contract-and-identity','data-science/ordered-funnel-and-conversion-window','data-science/retention-cohort-and-maturity','data-science/checkout-funnel-retention-project'])

add('checkout-funnel-retention-project',
    'Project: audit checkout conversion and repeat purchase',
    'Build a product-analysis packet that reconciles event identity, ordered conversion, mature retention and transaction-ledger guardrails.', [
    ('Create a controlled event stream', 'Prepare 83 eligible checkout entrants across web and mobile. Include duplicate event IDs, two payload conflicts, one payment attempt preceding the chosen start, a wallet order without a payment-attempt event, and entries too recent for a 48-hour outcome. Add a separate paid-order ledger with transaction IDs. Store occurrence time, known-at time, app version and schema version. [[data-science/product-event-contract-and-identity|The identity lesson]] defines the accepted stream.'),
    ('Compute the ordered funnel', 'Count entrants, payment attempts after entry and confirmed orders within 48 hours. Show both payment-to-order and entry-to-order rates, and distinguish fully observed entries from pending entries. Inspect skipped-step paths instead of assigning them to failure. Keep user-level and session-level views separate. [[data-science/ordered-funnel-and-conversion-window|The sequence lesson]] supplies the state rules.'),
    ('Build retention cohorts', 'Assign first-time buyers to acquisition weeks, then measure paid return in days 7 through 13. Show cohort size, mature users, returns and pending users. Compare web and mobile composition without attributing differences to platform quality. Include a deliberately recent cohort whose week-one window has not closed. [[data-science/retention-cohort-and-maturity|The maturity rule]] prevents premature decline claims.'),
    ('Reconcile and decide', 'Join confirmation events to the paid-order ledger by transaction ID. Report ledger-only and event-only orders, refunds, payment failures and support contacts as guardrails. Simulate a mobile release that drops client checkout-start events while paid orders stay stable; the analysis should flag collection drift before it reports a conversion improvement. [[data-science/instrumentation-change-and-metric-guardrails|Instrumentation checks]] must be visible in the decision note.'),
    ('Deliver reproducible evidence', 'Save raw fixtures, ID-map policy, accepted-event ledger, cohort table, analysis cutoff, query or code revision, reconciliation report and assertions. A reviewer should be able to trace one buyer from checkout start through confirmed order and week-one return, then reproduce every numerator and denominator without a vendor dashboard.')],
    'def funnel_rates(entry_count, payment_count, order_count):\n    if not 0 <= order_count <= payment_count <= entry_count:\n        raise ValueError("invalid closed-funnel counts")\n    if entry_count == 0 or payment_count == 0:\n        raise ValueError("rate denominator is empty")\n    return {"payment_given_entry": payment_count / entry_count,\n            "order_given_payment": order_count / payment_count,\n            "order_given_entry": order_count / entry_count}\n\nmetrics = funnel_rates(83, 57, 41)\nassert round(metrics["order_given_entry"], 4) == 0.4940',
    'The final rate arithmetic is O(1), but event deduplication and ledger reconciliation scan O(N) records with O(N) ID state; per-actor sequencing adds sorting at O(N log N) worst-case time. Reviewer effort concentrates on conflicting identity and missing-path cases.',
    ['Do not infer conversion from a funnel whose recent entries have incomplete windows.', 'Do not merge user-level and session-level denominators.', 'Do not declare a product win when the independent transaction ledger contradicts client events.'],
    ['data-science/product-event-contract-and-identity','data-science/ordered-funnel-and-conversion-window','data-science/retention-cohort-and-maturity','data-science/instrumentation-change-and-metric-guardrails'])

assert len(lessons) == len(new_paths) == 5
assert {item['path'] for item in lessons} == new_paths
titles = {path: row['title'] for path, row in by_path.items()}
titles.update({item['path']: item['title'] for item in lessons})

def prose(value):
    return re.sub(r'\[\[([^|]+)\|([^\]]+)\]\]',
                  lambda match: '<a href="/' + match[1] + '">' + match[2] + '</a>',
                  html.escape(value))

def links(paths):
    return '<ul>' + ''.join('<li><a href="/' + path + '">' + html.escape(titles[path]) + '</a></li>'
                            for path in paths) + '</ul>'

def article_body(item):
    parts = ['<p>' + html.escape(item['summary']) + '</p>']
    for heading, paragraph in item['sections']:
        parts.extend(('<h2>' + html.escape(heading) + '</h2>', '<p>' + prose(paragraph) + '</p>'))
    parts.extend(('<h2>Implementation</h2>',
                  '<pre><code class="language-python">' + html.escape(item['code']) + '</code></pre>',
                  '<h2>Performance and operating cost</h2>', '<p>' + html.escape(item['cost']) + '</p>',
                  '<h3>Common Mistakes</h3>',
                  '<ul>' + ''.join('<li>' + html.escape(mistake) + '</li>' for mistake in item['mistakes']) + '</ul>',
                  '<h2>Read next</h2>', links(item['related'])))
    return ''.join(parts)

root_path = 'data-science/data-science-for-beginners'
project_hub_path = root_path + '/project'
for index, item in enumerate(lessons):
    is_project = item['path'].endswith('-project')
    body = article_body(item)
    path = item['path']
    row = dict(id=str(uuid.uuid5(uuid.NAMESPACE_URL, 'https://aitrove.in/' + path)),
               type='article', path=path, title=item['title'], summary=item['summary'], body=body,
               category='AI & Data', subject='data-science-project' if is_project else 'data-science',
               difficulty='Intermediate', tags=['ai-data', 'data-science'], potd_date=None,
               featured=False, sort_order=11900 + index, status='published', published_at=stamp,
               created_at=stamp, updated_at=stamp,
               data={'subject_root':root_path,
                     'section_path':project_hub_path if is_project else root_path,
                     'content_format':'html', 'seo_ready':True,
                     'kind':'project' if is_project else 'tutorial',
                     'reading_minutes':max(5, len(re.sub(r'<[^>]+>', ' ', body).split()) // 180),
                     'author_path':'authors/aitrove-editorial',
                     'verification_suite':'Editorial and syntax review; project inputs needed for runtime checks',
                     'related':[{'path':target, 'title':titles[target]} for target in item['related']]})
    rows.append(row)
    by_path[path] = row

tutorial_paths = ['data-science/' + slug for slug in slugs[:4]]
project_path = 'data-science/' + slugs[-1]
hub = by_path[root_path]
module_paths = {path for module in hub['data']['modules'] for path in module['lessons']}
if not set(tutorial_paths).issubset(module_paths):
    hub['data']['modules'].insert(-1, {'title':'Product behavior and retention analysis',
                                      'summary':'Fix event identity, sequence paths, mature cohorts and reconcile independent outcomes.',
                                      'lessons':tutorial_paths})
apply_module = next(module for module in hub['data']['modules'] if module['title'] == 'Apply your knowledge')
if project_path not in apply_module['lessons']:
    apply_module['lessons'].append(project_path)
if '<h2>Product behavior and retention analysis</h2>' not in hub['body']:
    hub['body'] += ('<h2>Product behavior and retention analysis</h2>' + links(tutorial_paths)
                    + '<h2>Checkout audit project</h2>' + links([project_path]))
hub['updated_at'] = stamp

project_hub = by_path[project_hub_path]
if project_path not in project_hub['data']['modules'][0]['lessons']:
    project_hub['data']['modules'][0]['lessons'].append(project_path)
if '<h2>Checkout audit project</h2>' not in project_hub['body']:
    project_hub['body'] += '<h2>Checkout audit project</h2>' + links([project_path])
project_hub['updated_at'] = stamp

for source, target in [
    ('data-science/dataset-grain-and-join-cardinality', tutorial_paths[0]),
    ('streaming-analytics/event-contract-and-partition-key', tutorial_paths[0]),
    ('data-science/cohort-entry-and-survivorship-bias', tutorial_paths[1]),
    ('data-science/metric-denominator-and-cohort', tutorial_paths[2]),
    ('data-science/right-censoring-and-time-to-event', tutorial_paths[2]),
    ('data-science/reproducible-analysis-snapshot', tutorial_paths[3]),
    ('online-experimentation/metric-denominators-and-guardrails', tutorial_paths[3]),
]:
    source_row = by_path[source]
    anchor = '<p><strong>Continue the workflow:</strong> <a href="/' + target + '">' + html.escape(titles[target]) + '</a>.</p>'
    if anchor not in source_row['body']:
        source_row['body'] += anchor
        if source_row['type'] == 'article':
            source_row['data'].setdefault('related', []).append({'path':target, 'title':titles[target]})
        source_row['updated_at'] = stamp

assert len({row['path'] for row in rows}) == len(rows)
fixture.write_text(json.dumps(rows, ensure_ascii=False, indent=2) + '\n')
print(json.dumps({'new_articles':len(lessons), 'new_projects':1, 'crosslinks_from_existing':7}))
