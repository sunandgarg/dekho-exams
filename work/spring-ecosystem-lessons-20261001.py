"""Add original Spring Integration, Cloud Stream, Config and AOT lessons."""

import copy
import datetime
import html
import json
import pathlib
import re
import uuid


ROOT = pathlib.Path(__file__).resolve().parents[1]
FIXTURE = ROOT / "src/data/fixtures.json"
rows = json.loads(FIXTURE.read_text())
by_path = {row["path"]: row for row in rows}
stamp = datetime.datetime.now(datetime.UTC).isoformat()


def prose(value):
    escaped = html.escape(value)
    return re.sub(
        r"\[\[([^|]+)\|([^\]]+)\]\]",
        lambda match: '<a href="/' + match[1] + '">' + match[2] + "</a>",
        escaped,
    )


lessons = [
    dict(
        slug="integration-direct-executor-channel", section="spring/production",
        title="Spring Integration DirectChannel versus ExecutorChannel: where the transaction stops",
        summary="A DirectChannel invokes its handler on the sender's thread; an ExecutorChannel can dispatch on another thread and lose that transaction context.",
        blocks=[
            ("Locate the handoff", "A parcel intake service writes a row and sends a message to an allocation handler. With DirectChannel, the handler runs in the sender's call path, so a failure can propagate to the caller and its transaction. With ExecutorChannel, the send can return before the handler runs; the handler may use a different thread and a separate transaction. A saturated executor may even use the caller thread under a caller-runs policy, so that accidental behavior cannot be the transaction plan."),
            ("Give asynchronous work its own contract", "If allocation must survive a process exit, [[spring/integration-persistent-queue|use durable storage]] or [[spring/relay-transaction-boundaries|an outbox]] rather than relying on a successful send to an in-memory executor. If the work is disposable, specify the queue limit, rejection behavior and completion observation. [[spring/transaction-thread-boundary|Imperative transaction state]] does not cross a thread handoff simply because a Message carries the same business ID."),
            ("Test both outcomes", "In one integration test, make the handler throw and assert that DirectChannel send fails before the caller commits. In another, block an ExecutorChannel handler, let send return, and verify that a later handler failure does not roll back the already completed caller. This code is an implementation sketch; wire it to the actual executor and transaction manager before claiming those outcomes."),
        ],
        code='@Bean\nDirectChannel inlineAllocation() {\n    return new DirectChannel();\n}\n\n@Bean\nExecutorChannel deferredAllocation(TaskExecutor allocationExecutor) {\n    return new ExecutorChannel(allocationExecutor);\n}',
        cost="Direct dispatch consumes the caller thread until the handler finishes. Executor dispatch adds scheduling and queue pressure; it does not supply durability or a shared transaction.",
        mistakes=["Do not equate a returned ExecutorChannel send with completed business work.", "Do not rely on caller-runs behavior to preserve transaction context.", "Do not insert an asynchronous channel between two writes that must commit atomically."],
        related=["spring/integration-persistent-queue", "spring/transaction-thread-boundary", "spring/async-admission-and-completion", "spring/relay-transaction-boundaries"],
    ),
    dict(
        slug="integration-persistent-queue", section="spring/production",
        title="Spring Integration queue: bound memory and choose a real message store",
        summary="A no-argument QueueChannel is effectively unbounded in memory; a bounded queue still disappears when the process stops.",
        blocks=[
            ("Capacity is not durability", "An intake bridge that creates QueueChannel(64) limits local backlog, but message 65 can block its sender until a receiver frees space. A no-argument QueueChannel permits an Integer.MAX_VALUE capacity and can drive the heap into failure long before that numerical limit. Neither form survives a JVM exit. [[spring/integration-direct-executor-channel|An asynchronous handoff]] is only a thread decision until a durable store is introduced."),
            ("Use the store built for channels", "For persistent channel traffic, JdbcChannelMessageStore is designed for the channel queue use case. Provision its database tables, choose a unique region or group identifier, and configure a transactional poller if removal must roll back when the handler fails. A broker-backed channel is another option, with different acknowledgment behavior. [[spring/integration-poller-transaction|The poller boundary]] is where a stored message becomes processing work."),
            ("Kill the process in a test", "Publish 37 unique parcel IDs, stop the worker after a known number of commits, restart from the same store, and reconcile accepted, processed and pending IDs. A memory-only test cannot prove that work survives a crash. The sample below is only the bounded in-memory choice; a durable deployment needs explicit JDBC or broker wiring and an integration test."),
        ],
        code='@Bean\nQueueChannel localParcelBuffer() {\n    return new QueueChannel(64);\n}',
        cost="A bounded memory queue caps heap use but can backpressure callers. A JDBC store adds database writes, indexes and retention work; measure poll latency and disk growth under the expected backlog.",
        mistakes=["Do not call a bounded in-memory QueueChannel durable.", "Do not leave QueueChannel at its no-argument capacity on an untrusted input path.", "Do not assume a persistent queue removes messages transactionally without checking the poller and handler boundary."],
        related=["spring/integration-poller-transaction", "spring/integration-direct-executor-channel", "spring/worker-drain-on-shutdown", "spring/outbox-claim-lease"],
    ),
    dict(
        slug="integration-idempotent-receiver", section="spring/production",
        title="Spring Integration idempotent receiver: the metadata key is not the business commit",
        summary="The idempotent receiver interceptor detects repeated messages, but its default metadata store is process-local and its decision is separate from business state.",
        blocks=[
            ("Choose the duplicate identity", "A parcel scan from a handheld device needs a stable event ID, tenant ID and source revision. A timestamp header is not a safe business key: redelivery often has a new timestamp. MetadataStoreSelector can use an explicit key and a shared ConcurrentMetadataStore. By default, the selector's in-memory state disappears on restart, and a rejected message can still reach the handler marked as duplicate unless discard or rejection behavior is configured."),
            ("Close the atomicity gap", "If the metadata store marks an ID seen and the business database transaction then rolls back, a retry can be incorrectly dropped. Put the dedup key and business write in one database transaction when that guarantee matters, using [[spring/consumer-dedup-transaction|the unique-key consumer pattern]]. The interceptor remains useful as an early filter, but it is not proof of exactly-once effects across two stores."),
            ("Verify replay", "Deliver event parcel-47 twice, restart the process, deliver it again, and compare rows and side effects. Then fail after metadata acceptance but before the business commit. This tests the gap that a duplicate-only unit test misses. The interceptor configuration below is an implementation sketch; connect it to a durable metadata store before using it for restart behavior."),
        ],
        code='@Bean\nIdempotentReceiverInterceptor parcelDedup(ConcurrentMetadataStore store) {\n    MetadataStoreSelector selector = new MetadataStoreSelector(\n        message -> message.getHeaders().get("tenantId") + ":"\n                + message.getHeaders().get("parcelEventId"), store);\n    return new IdempotentReceiverInterceptor(selector);\n}',
        cost="Each acceptance check adds metadata I/O if the store is shared. Keys need retention and a deletion policy; deleting them too early permits old redeliveries to run again.",
        mistakes=["Do not use a changing timestamp as the duplicate identity.", "Do not assume rejected messages are discarded unless that behavior is configured.", "Do not treat a metadata-store write as atomic with a separate business database commit."],
        related=["spring/consumer-dedup-transaction", "spring/integration-persistent-queue", "spring/kafka-idempotent-consumer", "spring/integration-poller-transaction"],
    ),
    dict(
        slug="integration-poller-transaction", section="spring/production",
        title="Spring Integration poller: include receive and handler in the failure boundary",
        summary="A poller can remove a message before a handler commits unless its receive, handler and store use the intended transaction boundary.",
        blocks=[
            ("Identify who owns receive", "A PollingConsumer reads from a PollableChannel on a schedule. Adding a transaction advice to the poller can make receive and downstream JDBC work share the same transaction when they use the same transaction manager and database. With a persistent channel store, a handler exception can roll back removal. An in-memory QueueChannel cannot regain a lost process's state. [[spring/integration-persistent-queue|Store choice]] comes first."),
            ("Limit each poll", "Set a bounded number of messages per poll and a fixed delay that does not flood the database when no work exists. A handler that blocks on an external API holds the poller thread and possibly a database connection. Move remote delivery to an outbox or use a claim-and-ack protocol with [[spring/outbox-fenced-ack|fencing]] when the write cannot share the message-store transaction."),
            ("Test the rollback path", "Insert a message, fail the handler after the receive, and assert the message is still available or redelivered according to the configured store. Then restart the JVM. The outcome is store- and binder-dependent; do not infer it from the scheduling annotation alone. This page is an implementation sketch rather than a checked poller fixture."),
        ],
        code='@ServiceActivator(inputChannel = "persistedParcelQueue",\n    poller = @Poller(fixedDelay = "7000", maxMessagesPerPoll = "23"))\npublic void handleParcel(Message<ParcelAccepted> message) {\n    parcelHandler.accept(message.getPayload());\n}',
        cost="Polling adds periodic database or broker reads, even at low traffic. Larger batches improve throughput but enlarge retry scope and the time a transaction holds resources.",
        mistakes=["Do not assume @Scheduled by itself wraps message receive and handler in one transaction.", "Do not let a poller transaction span an unbounded remote call.", "Do not infer crash recovery from an in-memory queue test."],
        related=["spring/integration-persistent-queue", "spring/outbox-claim-lease", "spring/scheduled-outbox-worker", "spring/integration-idempotent-receiver"],
    ),
    dict(
        slug="cloud-stream-consumer-group", section="spring/production",
        title="Spring Cloud Stream consumer group: scale one logical reader without copying every event",
        summary="A named consumer group makes application replicas compete for messages; an anonymous group can give each instance its own subscription.",
        blocks=[
            ("Name the logical subscriber", "Three settlement replicas should form one group if each parcel event is meant to be handled once by that service. Another service, such as analytics, uses another group and gets its own copy. Leaving group unset makes the binding anonymous, which can yield a separate subscription for each instance. That may be useful for broadcast, but it is wrong for a work queue. [[spring/kafka-partition-key|Partition keys]] affect ordering within a broker, not the decision to give each group a copy."),
            ("Expect retries and rebalances", "A group does not mean exactly-once business effects. A worker can write to the database and die before acknowledgment, so the next member sees the event again. Use [[spring/consumer-dedup-transaction|a transactional dedup key]] and make every side effect replay-safe. Set concurrency with partition count and downstream connection capacity in mind."),
            ("Check the deployment topology", "Start two replicas in one group and one audit replica in a different group. Send 47 distinct event IDs. Confirm each logical group receives all 47 IDs and settlement has one committed effect per ID despite a forced consumer restart. The YAML is a binding sketch; the exact broker and binder need their own integration test."),
        ],
        code='spring:\n  cloud:\n    function:\n      definition: settleParcel\n    stream:\n      bindings:\n        settleParcel-in-0:\n          destination: parcel-events\n          group: settlement-workers\n          consumer:\n            concurrency: 3',
        language="yaml",
        cost="More consumers can raise throughput only up to broker partitions and downstream capacity. Each additional group receives a separate logical copy and adds storage and processing demand.",
        mistakes=["Do not leave a work-queue subscriber anonymous by accident.", "Do not equate consumer-group membership with exactly-once database effects.", "Do not set concurrency above the bottleneck without measuring broker and database behavior."],
        related=["spring/cloud-stream-kafka-dlq", "spring/kafka-partition-key", "spring/consumer-dedup-transaction", "spring/kafka-listener-manual-ack"],
    ),
    dict(
        slug="cloud-stream-kafka-dlq", section="spring/production",
        title="Spring Cloud Stream Kafka DLQ: stop poison messages without losing the trail",
        summary="A Kafka binder dead-letter topic is an explicit failure route after configured attempts; it is not a fix for the failed record.",
        blocks=[
            ("Bind failures to a named group", "The Kafka binder's DLQ path needs a consumer group and explicit enablement. After the configured attempts are exhausted, a failing parcel message can be published to a dead-letter topic. The application must decide who inspects, repairs and replays that record. [[spring/kafka-retry-and-poison|The listener failure lesson]] distinguishes transient errors from bad data."),
            ("Keep replay bounded", "Attach the original event ID, failure class and attempt count to an operational record. A replay worker must not blindly put a permanently invalid message back on the main topic: that creates a loop. Send repaired records under a new correction ID or preserve the original ID with a documented dedup policy. [[spring/integration-idempotent-receiver|Idempotency state]] and [[spring/consumer-dedup-transaction|business uniqueness]] need to agree on that choice."),
            ("Verify the binder's actual behavior", "Force one valid record to fail twice and then succeed; force another to fail beyond the limit. Assert the first reaches business state once and the second appears in the configured DLQ with enough context to repair it. This cannot be proven by a unit test of the Consumer function alone."),
        ],
        code='spring:\n  cloud:\n    stream:\n      bindings:\n        settleParcel-in-0:\n          destination: parcel-events\n          group: settlement-workers\n          consumer:\n            max-attempts: 3\n      kafka:\n        bindings:\n          settleParcel-in-0:\n            consumer:\n              enable-dlq: true',
        language="yaml",
        cost="Each retry consumes processing capacity and can block later records on the same partition. DLQ storage grows until records are triaged and retained or removed under policy.",
        mistakes=["Do not expect DLQ routing without the binder-specific setting and named group.", "Do not replay every DLQ record automatically.", "Do not discard the original event ID or error reason during repair."],
        related=["spring/cloud-stream-consumer-group", "spring/kafka-retry-and-poison", "spring/integration-idempotent-receiver", "spring/relay-dead-letter"],
    ),
    dict(
        slug="cloud-stream-producer-failure", section="spring/production",
        title="Spring Cloud Stream producer failure: a sent message is not an accepted business command",
        summary="A producer call can return before broker acknowledgment; an asynchronous send failure needs its own observation and retry decision.",
        blocks=[
            ("Separate local acceptance from broker acknowledgment", "A parcel API that updates a database and then emits an event has two resources. A successful local function call does not prove the broker stored the event. Some binder paths report asynchronous producer failures through an error channel rather than the caller's stack. A producer failure handler can record the failed message, but it cannot retroactively roll back a committed database transaction."),
            ("Use a replayable handoff", "Write the event to [[spring/outbox-atomic-write|an outbox]] in the same database transaction as the parcel change, then relay with a stable event ID. [[spring/kafka-producer-completion|Producer completion]] decides when the relay may acknowledge the outbox row. If acknowledgment is lost after broker acceptance, the relay may resend; consumers still need [[spring/consumer-dedup-transaction|deduplication]]."),
            ("Test the ambiguous window", "Make the broker accept an event and drop the producer acknowledgment, then restart the relay. Verify one business effect after the duplicate event arrives. Also force a definite producer failure and confirm the outbox row remains retryable. A function-level test without a broker cannot cover this window."),
        ],
        code='@Transactional\npublic void recordParcel(ParcelAccepted command) {\n    parcels.insert(command.parcelId(), command.units());\n    outbox.insert(command.eventId(), command.parcelId(), "PARCEL_ACCEPTED");\n}',
        cost="The outbox adds a database write and relay latency. It replaces an unobservable dual-write gap with retained work, retry cost and explicit reconciliation.",
        mistakes=["Do not treat a successful producer method return as durable broker acceptance.", "Do not acknowledge an outbox row before the broker result is known.", "Do not claim exactly-once delivery from a producer callback alone."],
        related=["spring/kafka-producer-completion", "spring/outbox-atomic-write", "spring/relay-transaction-boundaries", "spring/cloud-stream-consumer-group"],
    ),
    dict(
        slug="cloud-config-pinned-label", section="spring/spring-boot",
        title="Spring Cloud Config label: pin a release to the configuration it was tested with",
        summary="A Config Server label selects a Git branch, tag or commit; a moving branch can change a service's startup configuration without changing its binary.",
        blocks=[
            ("Treat configuration as a release input", "A settlement service built against a 37-second retry window can start tomorrow with a changed main-branch value if it follows a moving label. Pinning a release tag or commit lets the deployment state exactly which configuration revision it used. Keep the application name and profile explicit; Config Server resolves the application, profile and label together. [[spring/cloud-config-import|Config import]] controls where it is loaded; [[spring/boot-config-source-matrix|property precedence]] still decides which value wins."),
            ("Reject an absent revision", "For required configuration, omit the optional prefix on configserver import so startup fails when the server cannot supply it. Validate required fields after binding. A successful HTTP response can still contain an unexpected value or stale checkout, so record the effective label and non-secret config fingerprint with the release. [[spring/cloud-config-backend-staleness|The backend lesson]] covers that failure."),
            ("Replay a release", "Run the same artifact with a pinned label, record the resulting bound settings, then move the default branch and restart. The pinned deployment should preserve its contract. This is a release test plan; the sample properties are an implementation sketch and need a configured Config Server."),
        ],
        code='spring.application.name=parcel-settlement\nspring.profiles.active=production\nspring.cloud.config.label=release-47\nspring.config.import=configserver:',
        language="properties",
        cost="Pinned labels add release bookkeeping but make rollback reproducible. A Config Server request adds startup latency and a dependency whose outage policy must be deliberate.",
        mistakes=["Do not call a mutable branch name an immutable release pin.", "Do not use optional import for configuration without which the service must not start.", "Do not log secret values while recording the effective configuration revision."],
        related=["spring/cloud-config-import", "spring/cloud-config-backend-staleness", "spring/boot-config-source-matrix", "spring/boot-config-migration-trace"],
    ),
    dict(
        slug="cloud-config-backend-staleness", section="spring/spring-boot",
        title="Spring Cloud Config Git cache: a healthy server can still return stale properties",
        summary="After a successful clone, Config Server can serve its local checkout while the remote Git backend is unavailable.",
        blocks=[
            ("Distinguish HTTP health from freshness", "A Config Server can answer requests from a local working copy even when it cannot reach Git. A client may start successfully yet receive an older retry limit or feature gate. A healthy endpoint therefore proves only that the server answered, not that its answer matches the intended release. [[spring/cloud-config-pinned-label|Pin a label]] and record the resolved revision as deployment evidence."),
            ("Fail where the contract requires it", "Configure clone-on-start when the server itself must fail early on an unreachable repository. That does not remove the post-start cache behavior. Set fetch cadence to match the operational model and alert when the resolved revision lags the expected label or commit. A moving branch can make a release drift silently; a fixed commit can still be unavailable if it was never fetched."),
            ("Exercise the outage", "Fetch a known revision, disconnect the Git backend, and request configuration again. Record whether the server returns its cached checkout or an error. Restart the server with no local cache while Git is down and check the different outcome. This scenario needs a real Config Server and repository fixture; no live backend test is claimed here."),
        ],
        code='spring.cloud.config.server.git.clone-on-start=true\nspring.cloud.config.server.git.refresh-rate=37',
        language="properties",
        cost="Frequent Git refreshes add remote requests and server load; longer intervals increase possible staleness. Local cache helps availability but weakens freshness unless revision drift is observed.",
        mistakes=["Do not equate Config Server HTTP 200 with latest Git content.", "Do not assume clone-on-start prevents stale replies after startup.", "Do not roll a service on an unpinned branch without recording the resolved revision."],
        related=["spring/cloud-config-pinned-label", "spring/cloud-config-import", "spring/dependency-readiness", "spring/actuator-health"],
    ),
    dict(
        slug="cloud-config-refresh-boundary", section="spring/spring-boot",
        title="Spring Cloud refresh: changed properties do not rebuild every dependency",
        summary="A configuration refresh can rebind selected properties and refresh scoped beans; it is not an atomic replacement of the entire application context.",
        blocks=[
            ("Inspect the object graph", "A service may refresh a retry interval while an HTTP client created at startup retains its previous timeout. A @RefreshScope proxy can rebuild a target on its next use, but putting the annotation on a configuration class does not automatically make every bean returned by that class refresh scoped. Constructor-bound records have additional limits. A concurrent reader can observe a partially rebound mutable properties object unless the refresh boundary protects it."),
            ("Restrict the control plane", "The refresh actuator endpoint changes live behavior and should be exposed only to an authenticated operator path. A deployment rollout is often simpler for connection pools and other stateful clients. Spring AOT/native processing does not support context refresh, so [[spring/aot-build-time-bean-decisions|native deployments]] should treat such changes as new image releases."),
            ("Test old and new work", "Start one request before refresh and another afterward. Verify which timeout each sees, what happens to open connections, and whether a removed property actually disappears. Do not call refresh complete just because Environment returns a new string. This is a design sketch; the specific bean graph requires an application test."),
        ],
        code='@Bean\n@RefreshScope\nParcelGateway parcelGateway(ParcelGatewaySettings settings) {\n    return new ParcelGateway(settings.readTimeout());\n}',
        cost="Refresh can allocate a new client while old requests still use the former one. Track connection ownership and cleanup; an application restart is often easier to reason about for stateful dependencies.",
        mistakes=["Do not assume every singleton is rebuilt after /actuator/refresh.", "Do not expose refresh as an unauthenticated public endpoint.", "Do not promise live refresh in an AOT/native image deployment."],
        related=["spring/cloud-config-pinned-label", "spring/aot-build-time-bean-decisions", "spring/boot-config-migration-trace", "spring/restclient-timeout-budget"],
    ),
    dict(
        slug="aot-build-time-bean-decisions", section="spring/spring-boot",
        title="Spring AOT: profile and conditional beans become build-time decisions",
        summary="AOT processes the application context before runtime, so a native executable cannot freely add beans by changing a profile or conditional property later.",
        blocks=[
            ("Build the intended context", "A parcel worker built with a profile selecting a local archive client cannot become a cloud archive worker just by changing a runtime environment variable if that variable changes which beans exist. AOT fixes the classpath and bean graph at build time. Values read by an existing bean may still be runtime configuration, but conditions that decide whether a bean exists are different. [[spring/boot-profile-file-selection|Profile selection]] and [[spring/auto-configuration|auto-configuration]] need a native-specific release test."),
            ("Separate properties from topology", "Keep endpoints and timeouts as runtime values where the bean graph can remain fixed. Build separate native artifacts when two deployments genuinely need different conditional beans, or choose a design that selects behavior inside an existing bean without changing its type graph. [[spring/cloud-config-refresh-boundary|Context refresh]] is not a substitute in a native image."),
            ("Check the exact image", "Build with the production profile and run the resulting executable with production secrets and a staging dependency set. Check that the expected beans exist and rejected paths stay rejected. A JVM test alone does not establish the native image's build-time decisions."),
        ],
        code='@Configuration\n@Profile("warehouse")\nclass WarehouseArchiveConfiguration {\n    @Bean\n    ArchiveClient warehouseArchiveClient() {\n        return new WarehouseArchiveClient();\n    }\n}',
        cost="AOT and native compilation add build time and artifact-specific validation. They can improve startup and memory behavior, but each build-time profile variant increases release and test work.",
        mistakes=["Do not switch build-time conditional beans with a runtime property and expect a new graph.", "Do not infer native behavior solely from a JVM integration test.", "Do not combine a required native release path with live context refresh assumptions."],
        related=["spring/aot-runtime-hints-resource", "spring/boot-profile-file-selection", "spring/auto-configuration", "spring/cloud-config-refresh-boundary"],
    ),
    dict(
        slug="aot-runtime-hints-resource", section="spring/spring-boot",
        title="Spring native RuntimeHints: register resources reached only by name",
        summary="A native image can omit a resource or reflective type that static analysis cannot see; RuntimeHints make that reachability explicit.",
        blocks=[
            ("Trace the missing access", "A parcel printer loads a layout by a name assembled from a tenant configuration key. The JVM can find the resource on the classpath, while a native executable may omit it if no hint includes that path. Register the finite set of layouts through RuntimeHints. Treat arbitrary tenant-provided paths as untrusted input rather than adding a broad resource glob that packs secrets into the image."),
            ("Keep hints narrow", "Spring AOT already discovers many framework serialization and configuration-property cases. Add custom hints for only the name-based access your code owns. For reflection, identify the exact type and members required instead of registering an entire package. A broad hint can enlarge the image and hide an architectural dependency that should be explicit. [[spring/aot-build-time-bean-decisions|Build-time context decisions]] remain separate from reachability."),
            ("Test the real executable", "A RuntimeHints unit test can assert that the declared path is registered, but only a native smoke test proves that the resource loads and the service performs its task. Delete or rename one resource in a negative test so a missing layout fails visibly rather than silently using a default."),
        ],
        code='class ParcelLayoutHints implements RuntimeHintsRegistrar {\n    @Override\n    public void registerHints(RuntimeHints hints, ClassLoader loader) {\n        hints.resources().registerPattern("parcel-layouts/standard.json");\n        hints.resources().registerPattern("parcel-layouts/oversize.json");\n    }\n}',
        cost="Each retained resource adds image size. Native smoke tests take longer than JVM tests, but they catch missing reachability metadata before production startup.",
        mistakes=["Do not register every classpath resource to fix one missing layout.", "Do not use untrusted tenant text as a resource path.", "Do not call a RuntimeHints unit assertion a substitute for running the native executable."],
        related=["spring/aot-build-time-bean-decisions", "spring/context-testing", "spring/boot-startup-validation", "spring/boot-configtree-file-binding"],
    ),
    dict(
        slug="scheduled-worker-multi-instance", section="spring/production",
        title="Spring @Scheduled on three replicas: the callback runs three times",
        summary="@Scheduled arranges callbacks in each application context; it does not elect a cluster-wide worker.",
        blocks=[
            ("Count application instances", "When three parcel-service replicas all contain the same scheduled relay bean, each replica wakes on its own timer. A single-node test sees one call and can hide three-way production execution. Make the database claim the arbiter: atomically select due rows for one owner, retain a lease, and [[spring/outbox-fenced-ack|fence stale acknowledgments]]. The schedule merely asks each process to look for work."),
            ("Avoid overlapping local runs", "A fixed-rate trigger can fire again while a slow previous run is still active if the scheduler has capacity. Use bounded claims and a local concurrency guard where needed, but keep the database lease because local guards cannot coordinate other replicas. [[spring/scheduled-outbox-worker|The outbox worker]] supplies the state machine; [[spring/poller-shutdown|shutdown handling]] explains why a lease may outlive a worker."),
            ("Prove handoff", "Run three app instances against one database, pause the current owner after claim, and let its lease expire. Confirm a second owner takes over and the old owner cannot commit an acknowledgment. A test of only the @Scheduled method invocation cannot establish cluster safety."),
        ],
        code='@Scheduled(fixedDelayString = "${parcel.relay.delay.ms:7000}")\npublic void dispatchDueParcels() {\n    for (ClaimedParcel parcel : claims.claimDue(23)) {\n        relay.sendAndAcknowledge(parcel);\n    }\n}',
        cost="Every replica polls, adding database reads when idle. Small bounded claims and a suitable interval trade latency for load; leases require a clock and expiration policy.",
        mistakes=["Do not treat @Scheduled as a cluster leader election mechanism.", "Do not hold a local mutex and assume other replicas cannot run.", "Do not acknowledge work after losing the lease or fencing token."],
        related=["spring/scheduled-outbox-worker", "spring/outbox-claim-lease", "spring/outbox-fenced-ack", "spring/poller-shutdown"],
    ),
]

titles = {path: row["title"] for path, row in by_path.items()}
titles.update({"spring/" + item["slug"]: item["title"] for item in lessons})
subjects = {"spring/production": "spring-production", "spring/spring-boot": "spring-boot"}

for index, item in enumerate(lessons):
    path = "spring/" + item["slug"]
    assert path not in by_path, path
    assert all(target in titles for target in item["related"]), path
    body = "<p>" + prose(item["summary"]) + "</p>"
    for heading, content in item["blocks"]:
        body += "<h2>" + html.escape(heading) + "</h2><p>" + prose(content) + "</p>"
    language = item.get("language", "java")
    body += ('<h2>Implementation sketch</h2><pre><code class="language-' + language + '">'
             + html.escape(item["code"], quote=False) + "</code></pre>")
    body += "<h2>Cost and verification</h2><p>" + prose(item["cost"]) + "</p>"
    body += "<h3>Common Mistakes</h3><ul>" + "".join(
        "<li>" + prose(mistake) + "</li>" for mistake in item["mistakes"]
    ) + "</ul>"
    body += "<h2>Read next</h2><p>" + ", ".join(
        '<a href="/' + target + '">' + html.escape(titles[target]) + "</a>"
        for target in item["related"]
    ) + ".</p>"
    row = copy.deepcopy(by_path["spring/component-scan-vs-bean"])
    row.update(
        id=str(uuid.uuid5(uuid.NAMESPACE_URL, "https://aitrove.in/" + path)),
        path=path,
        title=item["title"],
        summary=item["summary"],
        body=body,
        subject=subjects[item["section"]],
        tags=["spring", "spring-boot", item["slug"].split("-")[0], item["slug"]],
        sort_order=4600 + index,
        published_at=stamp,
        created_at=stamp,
        updated_at=stamp,
    )
    row["data"] = {
        "subject_root": "spring/spring-boot",
        "section_path": item["section"],
        "kind": "tutorial",
        "content_format": "html",
        "seo_ready": True,
        "reading_minutes": max(4, round(len(re.sub(r"<[^>]+>", " ", body).split()) / 150)),
        "author_path": "authors/aitrove-editorial",
        "framework_version": "Spring Boot 4 / Spring Framework 7; Spring Cloud 5 or Spring Integration 7 where relevant",
        "java_version": "21 or later",
        "verification_suite": "Editorial API contract review; implementation sketch not compiled",
        "related": [{"path": target, "title": titles[target]} for target in item["related"]],
    }
    rows.append(row)
    by_path[path] = row

for section in subjects:
    paths = ["spring/" + item["slug"] for item in lessons if item["section"] == section]
    hub = by_path[section]
    heading = ("Integration, streaming and scheduling boundaries" if section == "spring/production"
               else "Config Server and native release boundaries")
    hub["data"]["modules"].append({
        "title": heading,
        "summary": "Trace a failure through the complete handoff or release path.",
        "lessons": paths,
    })
    hub["body"] += "<h2>" + heading + "</h2><ul>" + "".join(
        '<li><a href="/' + path + '">' + html.escape(titles[path]) + "</a></li>"
        for path in paths
    ) + "</ul>"
    hub["updated_at"] = stamp

parent = by_path["spring/spring-boot"]
parent["body"] += '<h2>Distributed Spring systems</h2><ul>' + "".join(
    '<li><a href="/spring/' + item["slug"] + '">' + html.escape(item["title"]) + "</a></li>"
    for item in lessons
) + "</ul>"
parent["updated_at"] = stamp
for source, target in [
    ("spring/transaction-thread-boundary", "spring/integration-direct-executor-channel"),
    ("spring/consumer-dedup-transaction", "spring/integration-idempotent-receiver"),
    ("spring/kafka-listener-manual-ack", "spring/cloud-stream-consumer-group"),
    ("spring/kafka-retry-and-poison", "spring/cloud-stream-kafka-dlq"),
    ("spring/cloud-config-import", "spring/cloud-config-pinned-label"),
    ("spring/boot-profile-file-selection", "spring/aot-build-time-bean-decisions"),
    ("spring/scheduled-outbox-worker", "spring/scheduled-worker-multi-instance"),
]:
    row = by_path[source]
    row["body"] += ('<h2>Related boundary</h2><p><a href="/' + target + '">'
                    + html.escape(titles[target]) + "</a></p>")
    row["updated_at"] = stamp

FIXTURE.write_text(json.dumps(rows, ensure_ascii=False, indent=2) + "\n")
print("Added", len(lessons), "Spring articles; new total", sum(
    row["path"].startswith("spring/") and row["type"] == "article" for row in rows
))
