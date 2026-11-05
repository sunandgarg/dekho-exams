"""Add object-storage recovery contracts to the local DevOps preview."""

import copy
import datetime
import html
import json
import uuid
from pathlib import Path

root = Path(__file__).resolve().parents[1]
fixture = root / "src/data/fixtures.json"
rows = json.loads(fixture.read_text())
by_path = {row["path"]: row for row in rows}
stamp = datetime.datetime.now(datetime.UTC).isoformat()
course = "devops/devops-tutorial"
project_hub = course + "/project"
quiz_hub = "devops/quizzes"
specs = []


def lesson(slug, title, summary, definition, operation, language, sample, cost, mistakes, related):
    path = "devops/" + slug
    assert path not in by_path, path
    specs.append(dict(path=path, title=title, summary=summary, definition=definition,
                      operation=operation, language=language, sample=sample,
                      cost=cost, mistakes=mistakes, related=related))


lesson(
    "object-version-delete-marker-recovery",
    "Object version recovery: distinguish a delete marker from lost bytes",
    "A missing current object can still have a recoverable older version.",
    "In a versioned object store, a delete without a version identifier can create a delete marker that becomes the current version. A normal read of the key then appears missing, while earlier object versions remain addressable by version identifier. A delete that names a specific version is a different operation: it can permanently remove that version unless retention blocks it. Recovery starts by identifying the exact key, bucket, version history, and current marker; a blind re-upload can overwrite the business meaning of the key.",
    "A settlement service reads daily receipt manifests from a versioned archive. After an operator deletes a manifest key, freeze automation that could expire or overwrite it. List versions and markers for that exact key with a read-only role. Compare the candidate version's creation time, checksum, and manifest record count with the authoritative settlement ledger. In an isolated rehearsal, restore visibility by removing only the current delete marker or by copying the selected old version to a new current version, according to the approved recovery policy. Record both old and new version identifiers. If later writes happened after the marker, removing it alone may expose the wrong version, so check the complete ordering first. Restrict permanent version deletion to a separate role and require a retention decision before any cleanup. Test the reader path, not just the storage API: an application cache may still return a stale miss after the object is visible.",
    "bash",
    "aws s3api list-object-versions --bucket receipt-archive-drill --prefix settlements/2026-09-27/manifest.json\naws s3api head-object --bucket receipt-archive-drill --key settlements/2026-09-27/manifest.json --version-id reviewed-version-id",
    "Listing V versions for one key takes O(V) review work and may require pagination; the actual restore is a small number of metadata or copy operations, but a copy can incur storage and request charges. Measure time to identify the authoritative version, time until the application reads it, and the age of the latest verified version. Versioning consumes storage for old bytes; pair recovery requirements with reviewed noncurrent-version retention rather than assuming old versions remain forever.",
    ["Do not equate a current-key 404 with permanent loss of every version.", "Do not delete a version identifier while trying to remove only a marker.", "Do not restore solely by timestamp when the ledger or checksum contradicts it."],
    ["devops/backup-and-recovery", "devops/immutable-backup-retention", "devops/object-replication-recovery", "devops/encryption-key-rotation-recovery"],
)

lesson(
    "object-lifecycle-version-retention",
    "Object lifecycle rules: model current, noncurrent, and archive states",
    "Expiry of a current key does not necessarily remove its stored versions.",
    "Object lifecycle policy is a state machine over object age, current-version status, storage class, and sometimes tags or prefixes. In a versioned bucket, current-version expiration can make a delete marker current while a former current version becomes noncurrent. A separate rule may then expire noncurrent versions permanently. Moving an object into an archive class can change restore latency and retrieval charges. Those transitions must be judged against the actual restore-time objective, not only a retention duration on paper.",
    "A claims archive retains monthly evidence while allowing fast recovery of the last two settlement cycles. Build a state table before deploying a rule: write date, current-version expiry, noncurrent expiry, archive transition, minimum storage duration, legal hold, and the final irreversible deletion point. Include versions created by corrections; their noncurrent age begins when they stop being current, not when the key was first created. Put a narrow prefix or tag on test objects in a disposable bucket, advance or inspect eligibility where the provider permits, and verify that a current-key read, version-specific read, and archive restore each behave as expected. Record when the lifecycle engine actually acts; eligibility time is not a synchronous deletion guarantee. Price transitions, retrievals, and early deletion periods against expected access rather than labelling the coldest tier automatically cheapest. Review the policy with records and recovery owners before letting it touch protected evidence.",
    "text",
    "Claims evidence lifecycle review\nCurrent key: readable during active claims window\nNoncurrent correction: retained through rollback window\nArchive transition: restore latency fits recovery objective\nLegal hold: prevents deletion where applicable\nIrreversible point: version expiry after reviewed retention\nTest: current read, old-version read, archive restore, final listing",
    "For N object versions, inventory-based review is O(N) in records processed and storage proportional to retained bytes. More versions increase storage cost; archive retrieval adds request and data charges. Measure oldest required recovery point, sample restore duration, noncurrent bytes, and lifecycle backlog. The expensive failure is a policy that permanently expires the only correct version before anyone has tested a restore.",
    ["Do not use current-key expiry as proof all versions were deleted.", "Do not assume archived bytes satisfy a short restore objective without a timed drill.", "Do not apply a broad prefix rule to held evidence without testing its exact filters."],
    ["devops/object-version-delete-marker-recovery", "devops/immutable-backup-retention", "devops/backup-and-recovery", "devops/cost-capacity-ownership"],
)

lesson(
    "multipart-upload-abort-budget",
    "Multipart uploads: bound abandoned parts and retry cost",
    "An unfinished multipart upload is not a completed object, yet its parts can consume billable storage.",
    "A multipart upload has an initiation identifier, uploaded parts, and an explicit completion or abort. A failure after some parts arrive can leave those parts stored without creating the final readable object. Listing normal objects will not reveal that cost. An abort policy controls abandoned uploads, but it must leave enough time for legitimate slow transfers to finish and account for clients retrying parts after a network break.",
    "A media-ingest worker sends large evidence bundles from remote offices. Define a maximum upload duration from observed slow-link transfers, then choose an abort-after age beyond that duration with an explicit margin. List incomplete uploads and their ages in a disposable bucket before applying the rule. Kill a worker after several parts are accepted, let its retry lease expire, and verify the client either resumes with the correct upload identifier or starts a new upload and aborts the old one. Complete a different upload just before the deadline to ensure the cleanup policy does not interrupt legitimate work. Keep the authoritative ingest record separate from the object key; mark it complete only after the storage service confirms the completed object and its checksum. When a retry creates a second upload identifier for the same key, choose one winner and clean up the loser. Track incomplete-part bytes and oldest age, not only final object count. Avoid placing secrets in object keys or upload metadata because listings and logs can expose them.",
    "text",
    "Evidence upload control\nMaximum legitimate duration: measured on slowest supported link\nAbort threshold: duration plus retry and scheduling margin\nCompletion gate: object exists and checksum matches ingest record\nFailed worker: old upload ID recorded for cleanup\nAlert: incomplete-part bytes or oldest age breaches budget",
    "Listing U open uploads is O(U) and may need pagination; part inspection adds work proportional to the selected upload's parts. Storage cost grows with incomplete bytes and time until abort, while an aggressive threshold increases re-upload bandwidth and CPU. Measure abort count, successful completion age, duplicate upload identifiers, and bytes reclaimed. The right threshold is a service-specific tradeoff, not a copied default.",
    ["Do not infer zero abandoned storage from a normal object listing.", "Do not acknowledge ingest before completing and verifying the object.", "Do not set cleanup age shorter than supported slow-link transfers."],
    ["devops/object-lifecycle-version-retention", "devops/queue-visibility-lease", "devops/backup-and-recovery", "devops/cost-capacity-ownership"],
)

lesson(
    "object-checksum-copy-reconciliation",
    "Object integrity: verify bytes without trusting an ETag shortcut",
    "An object ETag is not a universal full-file digest.",
    "Multipart uploads and some encryption or copy paths produce ETags that cannot be treated as an MD5 digest of the entire payload. A transfer success response proves the storage API accepted an operation, not that the application selected the correct source version or can parse the resulting document. Store a digest or supported checksum with an explicit algorithm and checksum type, then compare like with like across upload, copy, and restore paths.",
    "A receipt archive copies nightly bundles into a recovery account. The producer computes a SHA-256 digest over the final uncompressed payload and writes it into a signed manifest with key, version identifier, byte length, record count, and schema generation. Upload with provider-supported integrity checks and keep the producer digest as the application-level authority. After copy, inspect destination version, size, encryption accessibility, and provider checksum type. If a multipart source becomes a single-part copy, a provider checksum or ETag can change even when bytes do not; download a controlled sample and recompute the application digest. For bulk estates, use a provider-supported at-rest checksum job where available, but keep a sampled application parse check because byte integrity does not prove semantic validity. Compare the manifest against both source and destination inventories, quarantine mismatches, and never overwrite the good source to make a failed comparison disappear.",
    "text",
    "Receipt bundle manifest\nKey: receipts/2026-09-27/batch-47.bin\nSource version: recorded at upload completion\nPayload SHA-256: computed over final uncompressed bytes\nLength and record count: recorded by producer\nDestination version: recorded after copy\nAcceptance: digest, length, decrypt, and parser result agree",
    "Hashing B bytes costs O(B) CPU and O(1) streaming memory, while a full readback also incurs B bytes of retrieval and network traffic. Inventory reconciliation over N entries costs O(N) comparisons with memory bounded by the chosen join strategy. Measure checksum mismatch rate, unverified-copy age, and time to retrieve and parse a sample. A small verification sample is cheaper but leaves residual risk; size it from the recovery objective and observed defect rate.",
    ["Do not compare an ETag with a whole-file MD5 across multipart or encryption paths.", "Do not compare checksums with different algorithms or composite/full-object types.", "Do not call a copy recoverable until a reader can decrypt and parse it."],
    ["devops/object-replication-recovery", "devops/backup-and-recovery", "devops/encryption-key-rotation-recovery", "devops/object-version-delete-marker-recovery"],
)

lesson(
    "object-event-ordering-idempotency",
    "Object events: survive duplicate delivery and stale notifications",
    "An object-created notification is a hint to inspect durable state, not the only record of a write.",
    "Object-storage notifications can be delivered more than once and may arrive out of order. A consumer that keys only on object name can process an older overwrite after a newer one, or publish duplicate downstream work for the same version. Record the object version or another immutable generation identifier and make the resulting side effect idempotent. Where a provider includes a per-key ordering token, compare it only in its documented scope; do not turn it into a global ordering guarantee.",
    "A claims-index service receives object-created events through a queue. Its database stores one row per bucket, key, version, and processing generation, with a unique constraint on that tuple. On each event it checks the exact version, obtains a lease, validates checksum and schema, then commits the index pointer and processed marker in one transaction. A duplicate event sees the committed marker and exits. An old event may still produce a historical index if policy requires it, but it cannot replace the active pointer without a compare-and-set against the recorded current generation. Test duplicate delivery, reversed event order, missing object, a worker crash after indexing but before queue acknowledgement, and a poison file. Use an inventory or periodic listing to reconcile objects that never produced a usable event. Keep replay windows and dead-letter retention long enough for incident response, while avoiding customer data in event logs.",
    "text",
    "Claims index event identity\nIdempotency key: bucket + object key + version ID + processor generation\nRead: version-specific object and checksum\nCommit: index pointer and processed marker atomically\nDuplicate: detect committed marker and acknowledge\nReordered: older version cannot replace newer active pointer\nGap repair: periodic inventory reconciliation",
    "For E delivered events, processing is O(E) plus object-read cost; a keyed unique index gives expected logarithmic lookup in a B-tree and storage proportional to distinct processed versions. Deduplication does not prevent missed notifications, so reconciliation is still necessary. Measure duplicate rate, event-to-index lag, dead-letter age, and inventory-to-index gaps. A queue can smooth bursts, but unbounded replay can overload the indexer unless concurrency is capped.",
    ["Do not use object key alone as an idempotency key when overwrites are allowed.", "Do not assume delivery order matches write order across all keys.", "Do not remove periodic reconciliation merely because notifications are enabled."],
    ["devops/queue-consumer-reliability", "devops/dead-letter-replay", "devops/transactional-outbox-delivery", "devops/object-inventory-reconciliation"],
)

lesson(
    "presigned-object-access-expiry",
    "Presigned object access: bound authority and expiry",
    "A signed URL grants the signer’s allowed object operation to anyone who holds the URL while it remains valid.",
    "A presigned object URL is a bearer capability for a specific request. Its usable lifetime is limited by the requested expiry, the signer’s underlying credential lifetime, and any policy conditions such as signature age or network path. Revoking an application session alone may not immediately revoke a URL already issued. Treat it as sensitive data, keep its scope narrow, and provide a clear response when clients retry after expiry.",
    "A support portal allows a customer to download one invoice PDF. Authorize the customer against the invoice record before generating a URL for the exact object version and read operation. Use a short expiry derived from expected transfer time and client conditions; for a large file, allow a new authorized URL rather than issuing a day-long capability. Avoid recording the full query string in analytics, reverse-proxy logs, support tickets, or referrer-bearing pages. If a credential is rotated or disabled, test how outstanding URLs behave; do not promise instant revocation from an application database flag. For sensitive exports, consider a mediated download path that rechecks access, and use provider policy to restrict signature age or network reach where the product permits. Test clock skew, expired credentials, a copied URL used by a second client, and a retry after the URL expires. Monitor issuance volume and unusual download geography without logging the capability itself.",
    "text",
    "Invoice download capability review\nAuthorization: customer owns invoice record\nScope: one read of one object version\nExpiry: shortest workable transfer window\nLogging: omit signed query string\nReissue: require a fresh authorization check\nRevocation test: signer credential and storage policy behavior",
    "Issuing a URL is cheap, but mediated access adds an application hop and possibly bandwidth charges. A shorter expiry reduces the exposure window while increasing legitimate reissue attempts on slow networks. Measure denied reissues, expired-transfer retries, issuance rate, and downloads outside expected client conditions. The security cost of logging the token is independent of how short its expiry looks on a dashboard.",
    ["Do not treat a presigned URL as bound to the first browser that opens it.", "Do not assume requested expiry outlives temporary signer credentials.", "Do not put the signed query string in telemetry or error reports."],
    ["devops/secret-rotation-rollout", "devops/telemetry-sensitive-data-boundary", "devops/encryption-key-rotation-recovery", "devops/object-version-delete-marker-recovery"],
)

lesson(
    "object-lock-hold-key-recovery",
    "Locked objects: test retention, legal hold, and decryption together",
    "Preventing deletion does not guarantee that a retained object can be read.",
    "An object-level retention rule can block permanent deletion of a protected version for a fixed period, while a legal hold can continue until an authorized actor removes it. In a versioned store, a simple delete may still add a marker that hides a protected version from normal reads. Encryption adds a separate dependency: the restore identity must be able to use the required key when the object is needed. An immutable ciphertext with an unavailable key is not an accepted backup.",
    "A regulated payout ledger keeps signed daily exports. Separate ordinary writers, retention administrators, legal-hold administrators, and restore readers. In a disposable account, protect one version, attempt a permanent version delete with the ordinary role, and record the denied result. Then issue a simple delete and verify whether a marker hides the old version while the protected bytes remain. Turn on a legal hold, let the planned retention window end in the test design, and verify that hold removal is a separate reviewed action. Restore the exact version using the recovery role and encryption key; test one older backup after a key rotation and verify its digest against the ledger manifest. Record the retention mode and authority able to change it. Check that the key’s deletion schedule, grants, and account boundaries outlive every required restore point. Never use a real legal hold merely to exercise the tutorial, and never infer compliance from a successful write alone.",
    "text",
    "Payout export recovery gate\nProtected version: identifier and retain-until time recorded\nSimple delete: marker behavior tested separately\nPermanent delete: ordinary role denied during protection\nLegal hold: distinct owner and removal workflow\nDecrypt: old and current exports readable by recovery role\nIntegrity: restored digest matches signed ledger manifest",
    "Retention increases stored-version bytes and can prevent cost-driven cleanup until expiry. Restore testing adds read and key-service requests; reviewing K versions requires O(K) metadata work and selected data reads. Measure protected-version count, key-access denial, tested restore age, and time from incident start to a verified readable export. The strongest deletion barrier is useless if the recovery role cannot decrypt or locate the chosen version.",
    ["Do not treat a delete marker as proof a locked version was erased.", "Do not assume legal hold ends when a fixed retention date passes.", "Do not retire an encryption key before the last protected object can be restored."],
    ["devops/immutable-backup-retention", "devops/encryption-key-rotation-recovery", "devops/object-version-delete-marker-recovery", "devops/backup-and-recovery"],
)

lesson(
    "object-inventory-reconciliation",
    "Object inventory: reconcile delayed snapshots with live decisions",
    "A periodic object inventory is a batch observation, not a current authorization or recovery oracle.",
    "An inventory report can enumerate object versions and selected metadata at a scheduled cadence. Its delay is useful for estate-wide reconciliation but cannot settle whether a key was deleted, held, or overwritten moments ago. Treat inventory generation time and scope as fields in every comparison. For an incident decision, confirm the selected key and version with a live metadata or read request.",
    "A claims platform expects one archived evidence object for every closed claim. Export a signed application manifest with claim identifier, object key, version, digest, and expected retention class. Join it with the storage inventory for the same account, prefix, and report generation, then classify missing objects, extra objects, mismatched versions, unprotected versions, and copies not yet reconciled. Sample each class with live version-specific reads before opening a deletion or restore action. Inventory may arrive after a write or before a replication catch-up; keep those in a pending-age bucket instead of immediately declaring data loss. Paginate live listings only for a bounded slice so the incident tool does not exhaust API quotas during a broad outage. The comparison should produce a review queue with owner and evidence, not an automatic bulk delete of unexpected objects. Store the report and manifest with access controls; object keys can reveal customer or business context. Re-run the join after repair and retain before-and-after counts.",
    "text",
    "Claims archive reconciliation\nManifest: claim ID, key, version, digest, retention class\nInventory: generation time, scope, key, version, status\nJoin: missing, extra, wrong version, pending replication\nLive sample: read exact version and verify digest\nAction: reviewed restore or correction, then rerun comparison",
    "A sort-merge join over M manifest entries and N inventory rows costs O(M log M + N log N) for sorting and O(M + N) for the merge; streaming both already sorted sources reduces working memory. Reconciliation at scale also incurs report storage and query charges. Measure report age, unmatched count by class, oldest unresolved mismatch, and false alarms caused by snapshot delay. A zero-mismatch report from last week cannot prove that today’s archive is intact.",
    ["Do not treat a daily report as a live source of truth for a fresh delete.", "Do not compare different prefixes or generation windows as if they were identical.", "Do not bulk-delete extra keys before sampling and assigning an owner."],
    ["devops/object-replication-recovery", "devops/object-checksum-copy-reconciliation", "devops/object-event-ordering-idempotency", "devops/backup-and-recovery"],
)

titles = {row["path"]: row["title"] for row in rows}
titles.update({item["path"]: item["title"] for item in specs})
project_path = "devops/object-storage-recovery-project"
quiz_path = "quizzes/devops-object-storage-decisions"
titles[project_path] = "Project: recover a versioned object archive"
titles[quiz_path] = "DevOps object-storage recovery decisions"
assert all(path in titles for item in specs for path in item["related"])


def links(paths):
    return "<ul>" + "".join(
        f'<li><a href="/{html.escape(path)}">{html.escape(titles[path])}</a></li>'
        for path in dict.fromkeys(paths)
    ) + "</ul>"


for heading, summary, slugs in [
    ("Version and lifecycle recovery", "Find the exact retained version and test when lifecycle policy makes it unreachable or deletes it.", ["object-version-delete-marker-recovery", "object-lifecycle-version-retention"]),
    ("Transfer and integrity", "Clean up incomplete parts and verify copy bytes with an explicit digest contract.", ["multipart-upload-abort-budget", "object-checksum-copy-reconciliation"]),
    ("Events and access", "Process object notifications safely and constrain signed download capabilities.", ["object-event-ordering-idempotency", "presigned-object-access-expiry"]),
    ("Protection and reconciliation", "Test held-version decryption and compare delayed inventory with live state.", ["object-lock-hold-key-recovery", "object-inventory-reconciliation"]),
]:
    paths = ["devops/" + slug for slug in slugs]
    by_path[course]["data"]["modules"].append({"title": heading, "summary": summary, "lessons": paths})
    by_path[course]["body"] += f"<h2>{html.escape(heading)}</h2><p>{html.escape(summary)}</p>" + links(paths)
by_path[course]["updated_at"] = stamp

for index, item in enumerate(specs):
    path = item["path"]
    row = copy.deepcopy(by_path["devops/continuous-integration"])
    row.update(id=str(uuid.uuid5(uuid.NAMESPACE_URL, "aitrove:" + path)), path=path,
               title=item["title"], summary=item["summary"], subject="devops",
               category="DevOps", difficulty="Advanced", tags=["devops", "object-storage"],
               sort_order=21800 + index, published_at=stamp, created_at=stamp, updated_at=stamp)
    row["data"] = {"kind": "tutorial", "reading_minutes": 6,
                   "author_path": "authors/aitrove-editorial", "subject_root": course,
                   "section_path": course, "content_format": "html", "seo_ready": True,
                   "related": [{"path": target, "title": titles[target]} for target in item["related"]]}
    row["body"] = (
        f"<p>{html.escape(item['definition'])}</p><h2>Operational decision</h2>"
        f"<p>{html.escape(item['operation'])}</p>"
        f'<pre><code class="language-{item["language"]}">{html.escape(item["sample"])}</code></pre>'
        f"<h2>Cost and verification</h2><p>{html.escape(item['cost'])}</p>"
        + "<h3>Common Mistakes</h3><ul>"
        + "".join(f"<li>{html.escape(mistake)}</li>" for mistake in item["mistakes"])
        + "</ul><h2>Connected lessons</h2>" + links([course, *item["related"]])
    )
    rows.append(row)

project_related = [item["path"] for item in specs]
project = copy.deepcopy(by_path["devops/practice-project"])
project.update(id=str(uuid.uuid5(uuid.NAMESPACE_URL, "aitrove:" + project_path)),
               path=project_path, title=titles[project_path],
               summary="Rehearse marker recovery, multipart cleanup, digest checks, replay, access expiry, and held-version restore.",
               difficulty="Advanced", sort_order=21890,
               published_at=stamp, created_at=stamp, updated_at=stamp)
project["data"] = {"kind": "project", "reading_minutes": 9,
                   "author_path": "authors/aitrove-editorial", "subject_root": course,
                   "section_path": project_hub, "content_format": "html", "seo_ready": True,
                   "related": [{"path": target, "title": titles[target]} for target in project_related]}
project["body"] = (
    "<p>Use disposable object buckets, synthetic claims records, temporary credentials, and a queue-backed indexer. Define the recovery point and recovery-time objectives before injecting faults. Create three versions of a claim manifest with different record counts, then put a delete marker above them. Retain an external digest for each version. The exercise is accepted only when the correct version is readable through the application and its digest matches the signed manifest.</p>"
    "<h2>Recover the exact version</h2><p>List versions and markers for one key. Record each version identifier, write time, digest, and claim ledger generation. Remove only the marker in one rehearsal; in another, copy a reviewed historical version forward and compare the resulting current version with the ledger. Apply a narrow lifecycle rule in a separate test prefix and show current, noncurrent, archive, and final expiry states. Record the earliest irreversible deletion point. If an archive tier delays retrieval, time the restore and compare it with the recovery objective.</p>"
    "<h2>Inject transfer and delivery faults</h2><p>Start a multipart upload, send several parts, then kill the producer. Inspect incomplete uploads and bytes; allow the reviewed abort rule to clean up the abandoned identifier while a separate slow legitimate upload completes. Copy one completed object to a recovery bucket and compare exact versions, length, application digest, decryption, and parser result. Deliver the same object-created event twice and then reverse the order of two version events. The indexer must publish one active pointer for the newest approved generation and retain an auditable processed marker for each attempted version. Reconcile a deliberately suppressed event with an inventory or bounded live listing.</p>"
    "<pre><code class=\"language-text\">Archive recovery acceptance\nSelected version matches claims ledger and digest\nCurrent read returns the reviewed manifest\nAbandoned parts are reclaimed after the retry window\nCopied version decrypts and parses in the recovery account\nDuplicate and reversed events do not regress the active index\nExpired signed URL is denied and reissue checks authorization\nProtected old version survives deletion attempt and remains decryptable\nInventory mismatch is sampled live and reviewed before action</code></pre>"
    "<h2>Test protection and access</h2><p>Issue a short-lived read URL for one object version, exercise it before and after expiry, and verify that no signed query string appears in logs. Repeat after signer credential expiry. Protect a separate version with retention and legal hold in the disposable account, test permanent deletion with an ordinary role, and observe whether a simple delete adds a marker. Restore the protected version with the recovery role and the required encryption key. Do not use a production hold or production customer document. Compare a scheduled inventory report with an application manifest, preserving the report generation time and classifying recently written objects as pending until a live check resolves them.</p>"
    "<h2>Cost and verification</h2><p>Report recovery time, oldest verified recovery point, incomplete-part bytes, copy and readback bytes, inventory lag, event duplicates, missed-event age, signed-URL expiry failures, and key-denied restores. State which results came from the disposable provider environment and which were only reasoned from configuration. Include cleanup evidence for every bucket, queue, key, temporary role, and held test version. A successful API call alone does not satisfy the drill when the application still reads the wrong claim generation.</p>"
    "<h3>Common Mistakes</h3><ul><li>Do not erase a version while trying to clear a marker.</li><li>Do not use ETag equality as the only integrity check.</li><li>Do not bulk-delete inventory outliers without a live sample.</li></ul>"
    "<h2>Connected lessons</h2>" + links([*project_related, project_hub])
)
rows.append(project)
by_path[project_hub]["data"]["modules"][0]["lessons"].append(project_path)
by_path[project_hub]["body"] += "<h2>Object archive recovery drill</h2>" + links([project_path])
by_path[project_hub]["updated_at"] = stamp

questions = [
    ("What can a simple delete create in a versioned bucket?", ["A current delete marker", "A digest of every version", "A new encryption key"], "Older versions can remain addressable by version ID."),
    ("What identifies the intended version during recovery?", ["Version ID plus ledger and digest evidence", "Only the newest timestamp", "Only the object key"], "The business record and payload integrity must agree."),
    ("What can current-version lifecycle expiry leave behind?", ["Noncurrent versions and a delete marker", "Only a database row", "A guaranteed empty bucket"], "Noncurrent cleanup is a separate decision."),
    ("What must an archive transition satisfy?", ["The timed restore objective", "Only the lowest storage price", "Only a successful upload"], "Retrieval delay can break recovery even if bytes remain."),
    ("Why inspect incomplete multipart uploads?", ["Parts can consume storage without a completed object", "They always appear in normal object listings", "They prove the final digest"], "Abort or completion releases the abandoned-part obligation."),
    ("When should ingest be marked complete?", ["After completed object and integrity verification", "After the first part", "After a queue lease starts"], "The final readable object is the acceptance boundary."),
    ("Can an ETag always stand for a full-file MD5?", ["No, multipart and encryption paths can differ", "Yes, for every copy", "Yes, if the key matches"], "Compare explicit algorithms and checksum types."),
    ("What is a safe object-event identity for overwrites?", ["Bucket, key, version, and processor generation", "Key alone", "Delivery timestamp alone"], "Version-specific identity prevents duplicate work and stale overwrite."),
    ("Why reconcile inventory when events are enabled?", ["Events can be duplicated, reordered, or missed by a consumer", "Inventory changes event order", "A queue stores every object forever"], "A periodic independent comparison finds gaps."),
    ("What limits a signed URL's usable lifetime?", ["Requested expiry, signer credentials, and policy conditions", "Only browser session expiry", "Only the object size"], "The earliest applicable boundary wins."),
    ("Does an object legal hold end when fixed retention expires?", ["No, it remains until authorized removal", "Yes, always", "Only when the key changes"], "Retention and hold are independent controls."),
    ("How should a fresh inventory mismatch be handled?", ["Check report time and sample live version state", "Delete every extra key", "Assume immediate data loss"], "Scheduled reports lag current storage state."),
]
quiz = copy.deepcopy(by_path["quizzes/devops-operations"])
quiz.update(id=str(uuid.uuid5(uuid.NAMESPACE_URL, "aitrove:" + quiz_path)), path=quiz_path,
            title=titles[quiz_path], summary="Twelve decisions on object versions, integrity, event delivery, and recovery.",
            sort_order=21900, published_at=stamp, created_at=stamp, updated_at=stamp)
quiz["data"] = {"subject_root": course, "section_path": quiz_hub, "content_format": "html",
                "author_path": "authors/aitrove-editorial", "seo_ready": True, "duration_minutes": 12,
                "related": [{"path": target, "title": titles[target]} for target in project_related],
                "questions": [dict(prompt=prompt, options=options[index % 3:] + options[:index % 3],
                                   answer=(-index % 3) % 3, explanation=explanation)
                              for index, (prompt, options, explanation) in enumerate(questions)]}
quiz["body"] = (
    "<p>Choose the action that preserves the correct object version and proves it can be read. Separate retained bytes, current-key visibility, notification delivery, and application acceptance.</p>"
    "<h2>Review these lessons</h2>" + links(project_related)
    + "<h2>Other checks</h2>" + links([quiz_hub, "quizzes/devops-storage-lifecycle-decisions", "quizzes/devops-cost-capacity-decisions"])
    + "<h3>Common Mistakes</h3><ul><li>Do not infer permanent loss from a current-key miss.</li><li>Do not treat an inventory snapshot as live state.</li></ul>"
)
rows.append(quiz)
by_path[quiz_hub]["data"]["modules"][0]["lessons"].append(quiz_path)
by_path[quiz_hub]["body"] += "<h2>Object storage recovery check</h2>" + links([quiz_path])
by_path[quiz_hub]["updated_at"] = stamp

for item in specs:
    row = next(row for row in rows if row["path"] == item["path"])
    row["body"] += "<h2>Practice and check</h2>" + links([project_path, quiz_path])
    row["data"]["related"].extend({"path": path, "title": titles[path]} for path in [project_path, quiz_path])

for source, targets in {
    "devops/backup-and-recovery": ["devops/object-version-delete-marker-recovery", "devops/object-checksum-copy-reconciliation"],
    "devops/immutable-backup-retention": ["devops/object-lifecycle-version-retention", "devops/object-lock-hold-key-recovery"],
    "devops/object-replication-recovery": ["devops/object-checksum-copy-reconciliation", "devops/object-inventory-reconciliation"],
    "devops/queue-consumer-reliability": ["devops/object-event-ordering-idempotency"],
    "devops/dead-letter-replay": ["devops/object-event-ordering-idempotency"],
    "devops/encryption-key-rotation-recovery": ["devops/object-lock-hold-key-recovery"],
    "devops/telemetry-sensitive-data-boundary": ["devops/presigned-object-access-expiry"],
    "devops/cost-capacity-ownership": ["devops/multipart-upload-abort-budget"],
}.items():
    row = by_path[source]
    row["body"] += "<h2>Object storage follow-up</h2>" + links(targets)
    row["data"].setdefault("related", []).extend({"path": target, "title": titles[target]} for target in targets)
    row["updated_at"] = stamp

assert len({row["path"] for row in rows}) == len(rows)
fixture.write_text(json.dumps(rows, ensure_ascii=False, indent=2) + "\n")
print(json.dumps({"new_lessons": len(specs), "new_projects": 1, "new_quiz_banks": 1, "total_records": len(rows)}))
