"""Add application-data cache operations lessons to the Web Development drafts."""
import copy
import datetime
import html
import json
import re
import subprocess
import uuid
from pathlib import Path

root = Path(__file__).resolve().parents[1]
fixture = root / "src/data/fixtures.json"
entries = json.loads(fixture.read_text())
by_path = {entry["path"]: entry for entry in entries}
stamp = datetime.datetime.now(datetime.UTC).isoformat()


def paragraph(value):
    return "<p>" + html.escape(value) + "</p>"


def link(path):
    assert path in by_path, path
    return '<a href="/' + html.escape(path, quote=True) + '">' + html.escape(by_path[path]["title"]) + "</a>"


hub_path = "web-tech/application-cache-consistency-and-capacity"
hub_title = "Application Cache Consistency and Capacity"
topics = [
    dict(
        slug="cache-aside-fill-races-and-version-guards",
        title="Cache-Aside Fill Races and Version Guards",
        summary="Prevent an old cache fill from replacing a newer database result after a concurrent write.",
        concept="An application cache is a disposable copy of data held by an authoritative store. In cache-aside reads, the application checks the cache, loads the source on a miss, and saves the result for later requests. Writes usually commit to the source and then invalidate or replace the copy. That sequence is not automatically consistent. A read can miss, fetch an older version, pause, and write it into the cache after a newer transaction commits and invalidates the key. Time-to-live eventually removes the stale copy but does not protect the intervening requests. A version guard, a carefully ordered invalidation scheme, or a decision to bypass the cache for critical reads must define the actual freshness contract.",
        case="Reviewer 47 opens permit case 62 while its summary key is absent. The read obtains version 29 from the database, then pauses before filling the cache. Reviewer 91 approves the case, committing version 30 and deleting the cached summary. The paused read finally writes version 29 into the now-empty slot. Every later reader sees an obsolete open state until expiry. The fix advances a separate version floor to 30 after commit and rejects any fill below that floor, even if no value is cached. The approval response reads version 30 from the source; the broader list may tolerate a bounded lag. The cache remains a performance copy, not an approval authority.",
        implementation="Name the source of truth and the freshness limit for each read path before selecting a cache policy. Give mutable records monotonic versions or another token that can be compared under the source's concurrency model. After a committed write, advance a version floor that remains visible even when the cached value is absent; retain it longer than any in-flight fill. An atomic fill compares the loaded version with that floor and with any cached value before storing. A separate get followed by set is not enough. There is still a stale-read window between source commit and floor publication; do not claim immediate consistency across independent stores. If the floor update fails, bypass the cache for critical reads and rely on bounded expiry or reconciliation for tolerant views. For approval or permission, read the authoritative state. Scope keys by tenant, representation, and authorization dimensions, then measure stale returns through sampled source comparisons.",
        cost="A cache hit can avoid a database query, but every miss still pays source latency and cache network work. Version floors add storage per mutable key and an atomic fill step; their retention must cover delayed fills. Broad invalidation may discard useful entries, causing a refill burst; narrow invalidation requires a complete dependency map. A short TTL bounds stale lifetime but raises miss rate. An indefinitely long TTL saves reads while making a missed invalidation expensive. Track hit rate, fill duration, rejected stale fills, source-versus-cache version gap, floor publication failure, and extra source reads for critical routes. A hit-rate percentage alone cannot show whether the cache returned correct data.",
        failure="Pause a read after loading version 29, commit version 30, publish the version floor, invalidate, then resume the old fill into an empty value slot. The old version must be rejected. Drop the floor update after a committed write and verify the system reports a degraded freshness guarantee rather than claiming strict consistency. Restart one app instance with an empty local cache while another retains a copy; both should obey the same authorization rule. Reassign the permit to another tenant and ensure the prior tenant cannot access a cached summary through an old key. Disable the cache entirely and prove the source-backed path remains correct within its capacity budget.",
        drill="Model case 62 with versions 29 and 30. Interleave one read fill and one approval commit so the fill completes last. Record what every reader can see before, during, and after the version-floor update. Implement an atomic compare-by-version fill rule and test equal-version replacement, older fill rejection into an empty value slot, missing floor, and cache outage. Set a freshness limit for a public count and a stricter source check for approval permission. Report hit rate together with observed stale-version gap rather than presenting one number as proof of correctness.",
        decision="A cache copy needs an explicit freshness contract and a race-safe rule for filling after writes.",
        code='function shouldFillCase(versionFloor, cachedVersion, loadedVersion) {\n'
             '  return loadedVersion >= versionFloor && (cachedVersion === null || loadedVersion >= cachedVersion);\n'
             '}\n'
             'console.log(shouldFillCase(30, null, 29));\n'
             '// Output: false',
        checks=["A late old fill cannot enter an empty slot after a newer version floor is published.", "Critical permission and approval paths use authoritative state.", "Version-floor publication failure has a bounded freshness or reconciliation path."],
        mistakes=["Assuming delete-after-write or comparison with a missing value blocks old fills.", "Treating TTL as proof that no stale response is served.", "Using cached ownership as the final authorization decision."],
        related=["web-tech/transactions-and-concurrent-writes", "web-tech/tenant-scope-in-cache-and-background-work"],
    ),
    dict(
        slug="cache-stampede-singleflight-and-hot-key-budgets",
        title="Cache Stampede, Singleflight, and Hot-Key Budgets",
        summary="Bound source load when a popular cache entry expires or vanishes across many application instances.",
        concept="A cache stampede occurs when many callers miss the same key and independently request the same expensive source value. It is especially damaging when a popular entry expires across replicas at the same instant or when the cache restarts empty. A per-process singleflight group can collapse concurrent loads inside one process, but six application replicas may still make six source calls. A shared refresh lease, controlled stale serving, staggered expiry, or admission limit can bound the cross-process work. Each option has a failure case. A lease holder may crash; stale data may be forbidden for a private decision; randomizing expiry only spreads scheduled misses and cannot repair a sudden eviction.",
        case="The permit dashboard asks for a daily district 47 count. At 09:00, 900 browsers refresh while six API replicas see the same expired key. The aggregate query takes 430 milliseconds and scans several joined tables. Without coordination, hundreds of copies run and delay case writes. A process-local singleflight reduces each replica to one query, but six still hit the database. The service adds a short shared refresh lease with an expiry, serves a recent count for at most 47 seconds when permitted, and limits source refresh concurrency. Case approval and access checks continue to use the source because those decisions cannot use that stale count.",
        implementation="First identify the key and its actual source cost, request rate, acceptable age, and tenant scope. Collapse simultaneous loads within each instance using one promise per key, then decide whether cross-instance coordination is justified by measured source pressure. A refresh lease needs an expiry so a crashed holder does not freeze the value forever; writes from an old holder must be rejected if a later holder has a newer generation. Give waiting callers a deadline and a fallback: bounded stale count, source request under an admission budget, or an explicit temporary error. Jitter expiration for independent keys so scheduled refreshes do not synchronize. Warm only a measured hot set after restart; preloading every possible tenant key can be more expensive than normal misses. Keep a hard cap on concurrent source work.",
        cost="Singleflight uses O(K) in-flight coordination for K active keys in one process and retains a promise only until the load settles. A shared lease adds network operations and failure handling. Stale serving lowers source pressure but trades freshness for availability within a declared age. Jitter reduces synchronized expiry but does not prevent a cache flush stampede. A too-long lease leaves callers waiting behind a dead worker; a too-short lease permits duplicate refreshes before a slow query finishes. Measure misses per hot key, source calls per miss burst, lease wait, stale age, rejected refreshes, source p95, and user task completion. Do not hide all failures behind a stale response forever.",
        failure="Expire a district count on all six replicas and send 900 simultaneous reads. Count source queries, not just cache hit rate after the burst. Crash the lease owner before it fills the value and verify another worker can take over after the lease expiry. Slow the source query beyond the lease duration; an old worker must not overwrite a newer generation. Flush the whole cache while a rollout doubles app replicas and observe that source concurrency stays under its budget. Ask for a private approval in the same test; it must not inherit the count's stale-data permission.",
        drill="Set a 430-millisecond count query, 900 concurrent readers, and six application replicas. Compare uncoordinated loading, process-local singleflight, and a shared refresh lease. Define a 47-second maximum stale age for the count, a shorter lease lifetime with safe renewal, and a 63-query aggregate source budget. Then kill the refresher, delay its old result, and let a replacement finish first. Record which result may be cached, how many source calls ran, and what response late readers receive.",
        decision="Collapse work at the scope where the stampede occurs, with a deadline and a source-load ceiling.",
        code='function sourceLoadsWithoutSharedLease(replicaCount, processSingleflightEnabled) {\n'
             '  return processSingleflightEnabled ? replicaCount : 900;\n'
             '}\n'
             'console.log(sourceLoadsWithoutSharedLease(6, true));\n'
             '// Output: 6',
        checks=["Burst tests measure source calls per key, not only steady-state hits.", "A crashed or slow lease owner cannot pin or overwrite the result indefinitely.", "Stale serving is limited to routes with an explicit age budget."],
        mistakes=["Assuming process-local singleflight coordinates every replica.", "Using a refresh lock with no expiry or fencing rule.", "Serving stale permission or payment state because stale counts are allowed."],
        related=["web-tech/load-tests-and-capacity-budgets", "web-tech/connection-pool-budgets-and-queue-admission"],
    ),
    dict(
        slug="cache-memory-eviction-and-degraded-read-paths",
        title="Cache Memory, Eviction, and Degraded Read Paths",
        summary="Treat cache capacity and eviction policy as load-control decisions with a tested source fallback.",
        concept="A finite application cache must decide what happens when values occupy its memory budget. Eviction may remove old, rare, or soon-expiring keys, depending on policy; some configurations reject new entries instead. These are not merely storage choices. Evictions create misses, and misses shift work back to the database or upstream service. A cache that fails or becomes empty can turn normal traffic into a source overload if the application has no admission path. Cache entries also consume more than payload bytes through keys, metadata, allocator overhead, replication, and network buffers. A memory limit stated only as the sum of JSON body sizes will underestimate the operating footprint.",
        case="A case-feed cache holds small list summaries and large inspection previews together. During an import, large previews displace the hot summaries. Hit rate drops from 88 percent to 29 percent while the database handles the misses. An operator raises the memory limit without checking replica buffers or host headroom; eviction slows but memory pressure moves to the process. The revised design separates preview and summary budgets, caps entry size, chooses an eviction policy for disposable summaries, and gives the source a miss-admission ceiling. When the cache is unavailable, essential case reads use a bounded source path and optional aggregate panels degrade deliberately.",
        implementation="Estimate entry count, key and value size, metadata overhead, and peak refresh behavior from production-shaped data. Set a memory ceiling with headroom for the cache process and its replication or persistence needs. Select eviction behavior according to the data contract: a disposable performance cache can evict and refill; an authoritative session or queue store must not silently evict business state. Cap single-entry size so one result does not crowd out many useful keys. Separate tenants or content classes if one workload can evict another's hot set. Set a source-read concurrency budget and timeout for misses; decide which optional views can fail closed or show a marked stale value. Run a cold-cache and cache-unreachable drill before relying on the layer for peak traffic.",
        cost="More cache memory can improve hit rate until the active working set fits, then returns diminish. A policy change can help one key distribution and harm another, so compare hit rate by key class and source work, not only a global percentage. Eviction itself is work, and repeated misses for a hot key may create a stampede. Partitioning pools increases isolation but duplicates infrastructure and monitoring. Degraded read paths add product behavior to test and communicate. Track used and resident memory, evictions, rejected writes, entry sizes, misses by class, source load, and p95 task latency under cache outage. Keep cache cost tied to measured saved source work.",
        failure="Fill the cache with 63 large preview entries and observe whether small hot case summaries survive under the chosen policy. Force memory pressure and confirm the cache either evicts disposable copies or rejects new entries as configured; neither outcome may silently remove durable session or job state. Restart the cache before a morning peak, then direct a burst of reads at an empty working set. Limit database misses so the fallback does not exceed connection and query budgets. Disconnect the cache from one API replica and verify essential case reads remain correct while optional panels report their degraded state.",
        drill="Budget 480 megabytes for a disposable cache and measure real memory use for 29 representative summary keys and 47 preview keys before extrapolating. Define a maximum preview entry size and a separate source-admission limit. Simulate one hot-tenant burst, a cold restart, and a rejected cache write at the memory ceiling. Decide which data can be recomputed, which must bypass the cache, and which must never be stored in an evicting pool. Report both steady-state performance and the peak source load during failure.",
        decision="The cache is allowed to disappear; the source path must have a measured capacity and admission rule.",
        code='function allowSourceFallback(activeSourceReads, sourceReadLimit, essentialRead) {\n'
             '  return essentialRead && activeSourceReads < sourceReadLimit;\n'
             '}\n'
             'console.log(allowSourceFallback(63, 47, true));\n'
             '// Output: false',
        checks=["Memory estimates include overhead and a tested hot working set.", "Eviction affects only disposable copies, not authoritative state.", "Cold-cache and unavailable-cache tests keep source work within budget."],
        mistakes=["Counting only serialized payload bytes as cache memory.", "Mixing durable state with an evicting performance cache.", "Assuming a high hit rate guarantees safe behavior after restart."],
        related=["web-tech/data-persistence", "web-tech/connection-pool-budgets-and-queue-admission"],
    ),
    dict(
        slug="negative-cache-entries-and-stale-read-contracts",
        title="Negative Cache Entries and Stale-Read Contracts",
        summary="Cache absence and old values only when their user-visible meaning and maximum age are explicit.",
        concept="A negative cache entry records an absent result so repeated misses do not hammer the source. Absence can change quickly: a case may be created, permission may be granted, or an external integration may recover. An absent value is also different from an error. Caching a timeout as if the case did not exist can mislead users and hide an outage. Stale serving has a separate contract: a copy older than its fresh lifetime may be returned for a limited period while refresh runs or the source is impaired. That may be fine for a district total but unsafe for access, approval, payment, or a newly published private record. Every cached negative or stale result needs a scope, age limit, and invalidation story.",
        case="Reviewer 29 queries permit case 47 before it is imported, and an absence result is cached for 63 seconds. Thirty seconds later a worker creates the case. The reviewer still sees a false not-found response unless the write invalidates the negative entry or the client has another route to fresh data. A second incident occurs when a database timeout is caught and cached as not-found for 63 seconds, concealing an outage. The service separates confirmed absence from source failure, uses a shorter negative lifetime for import-sensitive lookups, invalidates on creation, and bypasses stale cache on permission checks. A public district count may use an aged value with a visible timestamp.",
        implementation="Represent cache states explicitly: present, confirmed absent, stale present, and source error. Give negative entries their own short lifetime based on the rate of creation and the cost of repeated misses; invalidate them when a matching record is created if the write path can identify the key. Never use a single falsy value for absent, empty list, denied, and timeout. Bind keys to tenant and representation identity. For stale reads, store the source version or fetched time and enforce a maximum age on every return, including during prolonged source failure. Refresh with bounded concurrency so stale permission does not become an accidental cache stampede. A mutation or authorization decision must consult current source state or a proven stronger mechanism; showing a stale list must not grant an action.",
        cost="Negative caching saves source queries for repeated absent keys but may delay visibility of new records. A shorter lifetime reduces that delay while raising miss traffic. Stale serving can preserve an informational page during a source problem, but the product must expose age when the value could affect a user's decision. Extra state and per-route policy make cache code more complex than a plain get/set. Track negative-hit rate, newly created records hidden by negative entries, stale age p95 and maximum, error-versus-absence counts, refresh failures, and source read load. If a cache entry survives far longer than the product's acceptable age, a low average age does not excuse it.",
        failure="Query an absent case and cache that result, then create the case before negative expiry; check whether invalidation makes it visible. Turn a source timeout into an error and prove no absent entry is written. Deny one reviewer access to an existing case and ensure the denial does not contaminate another reviewer's cache key. Keep the source down longer than the stale-age limit; the informational view must stop serving the old value or clearly fail according to its contract. Return a stale case list that still shows an Approve button, then confirm the server rechecks current permission and version before applying any action.",
        drill="Define a confirmed-absence TTL of 29 seconds for a permit import workflow and a maximum stale age of 47 seconds for a district count. Query case 62 as two reviewers in different organizations, create it during the negative window, and simulate a database timeout. Record the exact cache state and response for each caller. Hold the count source down for 63 seconds and verify the stale limit. Submit an approval from an old list and assert the write path uses current source state, not the display copy.",
        decision="Cache absence and age as explicit states; never turn failure or old data into a new authority.",
        code='function cachedReadDisposition(state, ageSeconds, maximumStaleSeconds) {\n'
             '  if (state === "source-error") return "fail";\n'
             '  if (state === "confirmed-absent") return "not-found";\n'
             '  return ageSeconds <= maximumStaleSeconds ? "serve" : "refresh-or-fail";\n'
             '}\n'
             'console.log(cachedReadDisposition("present", 63, 47));\n'
             '// Output: refresh-or-fail',
        checks=["Confirmed absence and source failure have distinct cache states.", "New record creation invalidates or bounds negative results.", "Stale age is enforced per route, and actions recheck source authority."],
        mistakes=["Caching a timeout as a legitimate not-found result.", "Sharing a negative permission result across users or tenants.", "Allowing a stale display value to authorize a mutation."],
        related=["web-tech/stale-revalidation-and-versioned-purges", "web-tech/tenant-scope-in-cache-and-background-work"],
    ),
]

assert hub_path not in by_path and len(topics) == 4
hub = copy.deepcopy(by_path["web-tech/production-signals-and-incident-decisions"])
hub.update(
    id=str(uuid.uuid5(uuid.NAMESPACE_URL, "aitrove:" + hub_path)),
    path=hub_path,
    title=hub_title,
    summary="Keep application-data caches useful without stale overwrites, miss storms, memory collapse, or false absence.",
    sort_order=3620,
    created_at=stamp,
    updated_at=stamp,
    published_at=stamp,
)
hub["data"] = {
    "subject_root": "web-tech/web-technology",
    "section_path": hub_path,
    "content_format": "html",
    "seo_ready": False,
    "modules": [],
    "resource_tabs": [
        {"title": "Web Development", "path": "web-tech/web-technology"},
        {"title": "Projects", "path": "web-tech/web-technology/project"},
        {"title": "Quizzes", "path": "web-tech/quizzes"},
    ],
}
entries.append(hub)
by_path[hub_path] = hub

for number, topic in enumerate(topics):
    path = "web-tech/" + topic["slug"]
    assert path not in by_path
    subprocess.run(["node", "--check", "--input-type=module"], input=topic["code"], text=True, capture_output=True, check=True)
    entry = copy.deepcopy(by_path["web-tech/trace-context-across-request-and-job"])
    entry.update(
        id=str(uuid.uuid5(uuid.NAMESPACE_URL, "aitrove:" + path)),
        path=path,
        title=topic["title"],
        summary=topic["summary"],
        sort_order=3621 + number,
        created_at=stamp,
        updated_at=stamp,
        published_at=stamp,
    )
    related = [hub_path] + ["web-tech/" + other["slug"] for other in topics if other is not topic] + topic["related"]
    body = paragraph(topic["concept"]) + "<h2>Working case</h2>" + paragraph(topic["case"])
    body += '<h2>Implementation boundary</h2><pre><code class="language-javascript">' + html.escape(topic["code"], quote=False) + "</code></pre>" + paragraph(topic["implementation"])
    body += "<h2>Cost and boundaries</h2>" + paragraph(topic["cost"]) + "<h2>Failure trace</h2>" + paragraph(topic["failure"])
    body += "<h2>Verification</h2><ul>" + "".join("<li>" + html.escape(item) + "</li>" for item in topic["checks"]) + "</ul>"
    body += "<h2>Practice drill</h2>" + paragraph(topic["drill"]) + "<h2>Decision note</h2>" + paragraph(topic["decision"])
    body += "<h3>Common Mistakes</h3><ul>" + "".join("<li>" + html.escape(item) + "</li>" for item in topic["mistakes"]) + "</ul>"
    entry["body"] = body
    entry["data"] = {
        "subject_root": "web-tech/web-technology",
        "section_path": hub_path,
        "content_format": "html",
        "seo_ready": False,
        "kind": "tutorial",
        "author_path": "authors/aitrove-editorial",
        "reading_minutes": 8,
        "related": related,
    }
    entries.append(entry)
    by_path[path] = entry

for topic in topics:
    entry = by_path["web-tech/" + topic["slug"]]
    entry["body"] += "<h2>Related lessons</h2><p>" + "; ".join(link(path) for path in entry["data"]["related"]) + ".</p>"

hub["data"]["modules"] = [{"title": hub_title, "summary": hub["summary"], "lessons": ["web-tech/" + topic["slug"] for topic in topics]}]
hub["body"] = paragraph("An application cache stores disposable copies of source data. This track tests four failure boundaries: an old fill after a write, a popular key expiring across replicas, memory pressure shifting work to the source, and cached absence or stale values outliving their meaning.")
hub["body"] += "<h2>Topics in this track</h2><ul>" + "".join("<li>" + link("web-tech/" + topic["slug"]) + " — " + html.escape(topic["summary"]) + "</li>" for topic in topics) + "</ul>"
hub["body"] += "<h2>Prerequisite paths</h2><p>" + "; ".join(link(path) for path in ["web-tech/data-persistence", "web-tech/http-delivery-and-cache-ownership", "web-tech/tenant-scope-in-cache-and-background-work"]) + ".</p>"
root_entry = by_path["web-tech/web-technology"]
root_entry["data"]["modules"].append({"title": hub_title, "summary": hub["summary"], "lessons": [hub_path] + ["web-tech/" + topic["slug"] for topic in topics]})
root_entry["body"] += "<h2>" + link(hub_path) + "</h2>" + paragraph(hub["summary"]) + "<ul>" + "".join("<li>" + link("web-tech/" + topic["slug"]) + " — " + html.escape(topic["summary"]) + "</li>" for topic in topics) + "</ul>"
root_entry["updated_at"] = stamp
crosslinks = {
    "web-tech/data-persistence": [hub_path],
    "web-tech/tenant-scope-in-cache-and-background-work": ["web-tech/cache-aside-fill-races-and-version-guards", "web-tech/negative-cache-entries-and-stale-read-contracts"],
    "web-tech/load-tests-and-capacity-budgets": ["web-tech/cache-stampede-singleflight-and-hot-key-budgets"],
    "web-tech/connection-pool-budgets-and-queue-admission": ["web-tech/cache-memory-eviction-and-degraded-read-paths"],
    "web-tech/stale-revalidation-and-versioned-purges": ["web-tech/negative-cache-entries-and-stale-read-contracts"],
}
for path, targets in crosslinks.items():
    assert path in by_path, path
    by_path[path]["body"] += "<h2>Further connections</h2><p>" + "; ".join(link(target) for target in targets) + ".</p>"
    by_path[path]["updated_at"] = stamp

fixture.write_text(json.dumps(entries, ensure_ascii=False, indent=2) + "\n")
print(json.dumps({"new_hubs": 1, "new_lessons": 4, "prose_words": {topic["slug"]: len(re.findall(r"\b[\w'-]+\b", " ".join(str(topic[key]) for key in ("concept", "case", "implementation", "cost", "failure", "drill", "decision", "summary")))) for topic in topics}}))
