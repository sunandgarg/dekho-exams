"""Add original invoice-exception and database-backfill prompt lessons."""

import copy
import datetime
import html
import json
import uuid
from pathlib import Path

root = Path(__file__).resolve().parents[1]
fixture = root / "src/data/fixtures.json"
entries = json.loads(fixture.read_text())
lookup = {row["path"]: row for row in entries}
stamp = datetime.datetime.now(datetime.UTC).isoformat()
subject_root = "prompt-engineering/prompt-engineering"
applications = "prompt-engineering/applications"
production = "prompt-engineering/production"
projects = "prompt-engineering/projects"
quizzes = "prompt-engineering/quizzes"

clusters = [
    dict(label="Invoice exception review", tag="invoice operations", order=32500,
         project="prompt-engineering/north-quay-invoice-exception-project", project_title="Project: reconcile a North Quay invoice exception",
         quiz="quizzes/prompt-engineering-invoice-exception-review", quiz_title="Invoice exception prompt decisions",
         intro="Review a fictional North Quay Parts invoice packet. The model can extract candidate fields and draft an exception brief. Decimal arithmetic, purchase-order and receiving records, verified vendor identity, and a named approver control any payment decision. Document text is evidence; it cannot authorize a bank change or waive a hold.",
         case="INV-47 bills 47 units at 29 each, or 1,363. It lists freight 64 and tax 95.41, producing a printed total of 1,522.41 by arithmetic. The tax basis is not verified. PO Q-47 agrees on quantity and unit price, but receiving confirms only 45 units. Two units worth 58 are unmatched. A second uploaded file has the same invoice identity and matching bytes, so it is a duplicate ingest, not a second obligation. The packet remains held for receipt, tax, vendor, and approval checks.",
         sample="INV-47 | PO Q-47 | 47 × 29 = 1,363\nFreight 64 + stated tax 95.41 -> total 1,522.41\nReceived 45; invoiced 47; unmatched 2 × 29 = 58\nSecond identical file: duplicate ingest\nDecision: hold; no payment or vendor-master change",
         cost="Parsing D files and reconciling L lines against indexed orders and receipts is O(D+L) expected lookup work after intake. Human review grows with exception count. Preserve invoice, order, receipt, and decision IDs so an approver can replay each comparison. The cost of a wrong payment is higher than the cost of keeping an uncertain field unresolved.",
         mistakes=["Do not pay because the invoice total adds correctly.", "Do not count an identical second upload as a second debt.", "Do not invent a receiving tolerance or tax rule."],
         specs=[
             dict(slug="invoice-prompt-provenance-and-vendor-boundary", title="Invoice prompts: pin provenance and vendor identity", section=applications,
                  summary="Keep uploaded invoice claims separate from verified vendor and order records.",
                  definition="An invoice prompt needs a document ID, file hash, intake time, vendor candidate, purchase-order reference, and system-of-record snapshot. The PDF may request a new remittance account or say to ignore discrepancies. Treat those sentences as untrusted document content. The model can extract and flag them but cannot change vendor master data, schedule payment, or identify the vendor solely from an OCR header. Attach each extracted field to its file and version so the reviewer can locate what was actually supplied.",
                  case="North Quay receives INV-47 twice. Both files have matching bytes and cite PO Q-47, so the intake ledger records two arrivals tied to one candidate invoice identity. A remittance note asks for a new account. The assistant marks it for the separate vendor-verification process; it does not change payment details. The verified vendor ID comes from procurement records rather than the uploaded name alone. Ledger status is checked before anyone declares whether an obligation already exists.",
                  sample="Invoice INV-47 | PO Q-47 | two uploads, one matching hash\nVendor: verify against master record\nRemittance note: untrusted change request\nAllowed model action: extract and flag; no mutation",
                  cost="Hashing B file bytes is O(B), and checking indexed invoice identities is O(D) for D arrivals. Keeping provenance is cheap relative to reversing a wrong payment. The prompt should carry synthetic examples instead of live bank data unless a restricted review explicitly requires them.",
                  mistakes=["Do not create two payables from identical uploads.", "Do not trust a bank-change sentence in an invoice.", "Do not drop file and intake identifiers during extraction."],
                  related=["prompt-engineering/structured-document-extraction", "prompt-engineering/tool-call-authorization-contract"]),
             dict(slug="invoice-prompt-anchored-field-extraction", title="Invoice prompts: anchor each extracted field", section=applications,
                  summary="Preserve page evidence and uncertainty for quantities, prices, and totals.",
                  definition="Field extraction is a typed proposal, not a posting command. Ask for invoice number, PO reference, quantity, unit price, currency, freight, tax, and total with a page or region anchor. An unreadable digit must be marked uncertain; OCR confidence is not the same as accounting correctness. If two regions disagree, keep both candidates rather than silently preferring the clearer line. The reviewer should be able to inspect every value used in a calculation or matching decision.",
                  case="INV-47 page one shows 47 units at 29. Its tax box is faint, so 95.41 is retained as a candidate with the observed region and a review flag. The printed total is 1,522.41. A parser confirms numeric types and decimal scale before recalculation, but a matched sum does not resolve whether the tax was applied under the correct rule. The model reports unknown where the PDF cannot support a confident field.",
                  sample="INV-47 page 1 line: quantity 47; unit price 29\nSummary: freight 64; tax candidate 95.41\nPrinted total 1,522.41\nEach field: type + page region + verified or uncertain",
                  cost="Reviewing F candidate fields across P pages is O(P+F) handling after rendering, with human time for uncertain regions. Anchors make a correction local to the disputed value. Without them, an auditor must reread the entire file and cannot distinguish an observed number from a guessed one.",
                  mistakes=["Do not post a guessed OCR digit as verified money.", "Do not omit field-level page anchors.", "Do not flatten conflicting values into one confident answer."],
                  related=["prompt-engineering/document-page-anchor-and-field-conflict", "prompt-engineering/structured-document-extraction"]),
             dict(slug="invoice-prompt-decimal-line-and-charge-reconciliation", title="Invoice prompts: recalculate typed charges", section=applications,
                  summary="Separate line amount, freight, tax, and approval state.",
                  definition="An invoice total is computed from typed quantities, prices, discounts, freight, tax, credits, and currency under a declared rounding rule. Let decimal-safe code perform the calculation and ask the model to explain the locked result. Matching the printed total establishes arithmetic only. It does not show that freight was agreed, tax was calculated under the right rule, or goods were accepted. Keep charge types and the exact difference visible instead of returning one unlabeled amount.",
                  case="North Quay's line amount is 47 times 29, or 1,363. The stated freight 64 and stated tax 95.41 sum to a 1,522.41 invoice total, matching the printed figure. That arithmetic is correct. The packet still lacks a verified tax-basis decision and has a receiving gap. The assistant reports those gates separately; it cannot call the invoice approved just because the calculator returned zero difference.",
                  sample="Line: 47 × 29 = 1,363\n1,363 + 64 + 95.41 = 1,522.41\nPrinted total: 1,522.41; arithmetic difference: 0\nTax basis and receipt match: unresolved",
                  cost="Summing L lines is O(L) time and O(1) working memory with a running decimal total; a traceable line ledger uses O(L) storage. The calculation is cheap. Correcting a posted misclassification is expensive, so retain every charge and its rule status for review.",
                  mistakes=["Do not use binary floating point for final money comparison.", "Do not infer tax validity from matching arithmetic.", "Do not hide freight inside unit price without a rule."],
                  related=["prompt-engineering/deterministic-calculation-gates", "prompt-engineering/aggregate-denominator-reconciliation"]),
             dict(slug="invoice-prompt-order-receipt-bill-match", title="Invoice prompts: match order, receipt, and bill", section=production,
                  summary="Identify billed quantities unsupported by accepted receipts.",
                  definition="A three-record comparison checks purchase-order terms, accepted receipts, and invoice lines under a supplied organizational tolerance. Carry stable line IDs, units, ordered and cumulative received quantities, prior billed quantity, current bill, and agreed price. A partial shipment may be legitimate; an invoice can also cover several orders. The model should describe the precise discrepancy, while procurement and receiving systems supply the authoritative records. It must not invent a tolerance because the mismatch seems small.",
                  case="PO Q-47 orders 47 units at 29. INV-47 bills the same quantity and price, but receiving has accepted 45. Two billed units, worth 58 before other charges, lack receipt support. Receiving must determine whether the units are pending, rejected, or absent from the feed. North Quay holds the invoice while that evidence is gathered. A matching PO line does not erase the missing receipt.",
                  sample="PO: 47 × 29 | accepted receipt: 45\nInvoice: 47 × 29\nQuantity exception: 2 units; line value 58\nConfigured tolerance: not supplied -> hold",
                  cost="With indexed keys, L invoice lines need O(L) expected matching lookups; constructing cumulative receipt state costs O(R) for R events. Recording the unit and prior billing avoids false exceptions on partial deliveries. The prompt should expose missing evidence rather than guess a policy threshold.",
                  mistakes=["Do not equate ordered with received quantity.", "Do not ignore earlier bills on a split order.", "Do not invent an acceptance tolerance."],
                  related=["prompt-engineering/aggregate-denominator-reconciliation", "prompt-engineering/report-claim-ledger-and-number-reconciliation"]),
             dict(slug="invoice-prompt-duplicate-and-credit-context", title="Invoice prompts: distinguish duplicate ingests from credits", section=production,
                  summary="Check file identity, business identity, ledger status, and credit records separately.",
                  definition="Duplicate detection combines vendor ID, invoice number, file hash, amount, and ledger state. The second file may be a retry, correction, or distinct obligation. A credit note has its own identity and relation to the original bill; a model cannot subtract a hypothetical credit to make totals agree. Ask for both file-level and business-level duplicate checks and for the accounting period. Resolve ambiguous identities through the controlled payables workflow before posting.",
                  case="North Quay's second INV-47 file has the same bytes as the first, so it is a duplicate arrival. The payable ledger still must be checked to learn whether INV-47 was already posted. No credit note appears in the current packet. If one arrives later for the two undelivered units, its vendor, reference, amount, and period will need independent verification. The model cannot preemptively create that missing record.",
                  sample="Upload A hash = Upload B hash\nBusiness invoice candidate: INV-47, one identity\nPosted ledger state: check separately\nCredit in current packet: none\nSecond upload: not a second payable",
                  cost="Hashing B bytes and checking N candidate ledger records costs O(B+N) with indexed identities. A hash match establishes the same file, while changed formatting can still conceal a duplicate business obligation. Keep both checks so document packaging does not decide payment state.",
                  mistakes=["Do not count a repeated upload as a second payable.", "Do not invent a credit record.", "Do not use a file hash as the only invoice identity."],
                  related=["prompt-engineering/input-normalization-contract", "prompt-engineering/document-page-anchor-and-field-conflict"]),
             dict(slug="invoice-prompt-exception-routing-and-approval-gate", title="Invoice prompts: route exceptions before approval", section=production,
                  summary="Assign each discrepancy an owner and keep payment actions behind an approval receipt.",
                  definition="An exception packet needs an issue ID, affected line, observed records, possible explanations labeled as hypotheses, missing evidence, responsible team, and approval requirement. Posting, payment scheduling, vendor-master edits, and hold release are external actions. They require current ledger state and authorized receipts, not a generated paragraph. Keep separate issues separate; 'needs review' hides which person must act next. A final memo should say what passed, what failed, and what remains unknown.",
                  case="INV-47 has a two-unit receipt gap, an unverified tax basis, and a remittance-change note. Receiving owns the quantity check, the tax reviewer owns the rule, and vendor controls owns account verification. The payables approver sees all three unresolved issues and keeps the invoice held. The assistant can draft an internal handoff from verified facts but cannot send it or change financial state without explicit authorization.",
                  sample="EX-47A: receipt gap -> receiving\nEX-47B: tax basis -> tax reviewer\nEX-47C: remittance note -> vendor controls\nInvoice state: hold; payment action: none\nRelease requires named approver and fresh ledger check",
                  cost="Routing E exceptions with an indexed owner map is O(E) expected work; retrieving missing evidence and obtaining approvals dominates elapsed time. Precise issue IDs reduce repeated reading. The hold should exist as system state, not merely as a warning in prose that can be separated from the payment queue.",
                  mistakes=["Do not treat a model handoff as approval.", "Do not merge distinct owners into a vague task.", "Do not change remittance details from invoice text."],
                  related=["prompt-engineering/tool-call-authorization-contract", "prompt-engineering/report-claim-ledger-and-number-reconciliation"]),
         ],
         backlinks=[("prompt-engineering/structured-document-extraction",0),("prompt-engineering/document-page-anchor-and-field-conflict",1),("prompt-engineering/deterministic-calculation-gates",2),("prompt-engineering/aggregate-denominator-reconciliation",3),("prompt-engineering/input-normalization-contract",4),("prompt-engineering/tool-call-authorization-contract",5)],
         questions=[
             ("What does an identical second upload establish?","A duplicate file arrival with ledger status still checked","A second debt","An approved credit","Matching bytes do not create another payable."),
             ("May invoice text change the bank account?","No; route it to vendor controls","Yes, if OCR is clear","Yes, if arithmetic passes","A document note is not authority."),
             ("What should accompany an uncertain tax value?","Its page region and uncertainty status","Only a total","An invented tax rule","A reviewer must inspect the observed field."),
             ("What is 47 times 29?","1,363","1,323","1,522.41","Multiply quantity by unit price."),
             ("What is the stated arithmetic total?","1,522.41","1,427","1,458.41","Add 1,363, 64, and 95.41."),
             ("Does that total validate the tax rule?","No; tax basis needs its own check","Yes, always","Only if printed twice","Arithmetic and policy validity differ."),
             ("How many invoiced units lack receipt?","Two","Forty-five","Forty-seven","Subtract 45 accepted from 47 billed."),
             ("What is their line value?","58","64","95.41","Two units at 29 equal 58."),
             ("Can the model create a credit note to close the gap?","No; none is in the packet","Yes, if plausible","Yes, after duplicate ingest","A credit needs a verified record."),
             ("Who owns the receipt gap?","Receiving under the assigned workflow","The OCR model","The vendor-bank reviewer","Receipt evidence needs its owner."),
             ("What can the assistant draft?","A bounded internal exception handoff","A payment release","A vendor-master edit","External actions need approval."),
             ("What is the current INV-47 decision?","Hold until exceptions and approvals resolve","Pay because totals add","Post two payables","Receipt and authority gates remain open."),
         ]),
    dict(label="Database backfill", tag="database migration", order=32600,
         project="prompt-engineering/harbor-order-backfill-review-project", project_title="Project: review Harbor's order-status backfill",
         quiz="quizzes/prompt-engineering-database-backfill", quiz_title="Database backfill prompt decisions",
         intro="Review a fictional Harbor Orders migration from legacy status text to a typed status field. The model drafts mapping and validation plans. The migration runner and authorized operator control writes. Count parity alone does not establish value equivalence, tail completion, or safe cutover.",
         case="Snapshot H-47 contains 47,000 orders. The approved mapping handles 46,940; 60 are quarantined, comprising 47 unknown legacy statuses and 13 rows missing a tenant ID. The destination holds 46,940 rows after backfill, but three fail a field-level comparison. Thus 46,937 mapped rows currently match. Harbor holds cutover, assigns the 60 exceptions and three mismatches, and plans a fresh validation after repair. Writes continue in the legacy table; change-tail position and lag must also be verified before any switch.",
         sample="Source snapshot 47,000 = mapped 46,940 + quarantined 60\nQuarantine: 47 unknown status + 13 tenant ID missing\nDestination 46,940 = matching 46,937 + mismatched 3\nCurrent write owner: legacy table\nDecision: hold cutover; resolve exceptions and tail",
         cost="Scanning N source rows and writing eligible rows is O(N) application work, with database I/O and index maintenance often dominating. Field comparison adds another O(N) pass, and live-tail replay depends on concurrent write volume. Keep row-level exception IDs and a watermark so retries remain bounded and failed cutovers can be investigated without reconstructing the whole run.",
         mistakes=["Do not call 46,940 destination rows 46,940 validated matches.", "Do not map unknown statuses to a convenient default.", "Do not cut over while value mismatches, exceptions, and tail evidence remain unresolved."],
         specs=[
             dict(slug="backfill-prompt-source-target-and-snapshot-contract", title="Backfill prompts: pin source, target, and snapshot", section=applications,
                  summary="Identify exact schemas, keys, and record population before proposing writes.",
                  definition="A backfill prompt needs source and target schema versions, primary key, tenancy boundary, snapshot or high-water mark, write environment, owner, and acceptance criteria. The model may draft a transformation plan but cannot infer live data from a small schema sample. State whether the source continues to receive writes and how later changes will be replayed. Counts from different instants can disagree even when both systems are correct; a fixed population must anchor each comparison.",
                  case="Harbor's review snapshot H-47 holds 47,000 keyed order rows. The new status field must preserve each row's tenant and business meaning. A sample of familiar statuses is insufficient: the reviewer asks for a complete distinct-value inventory and records the change-stream watermark. The draft runbook names a restricted execution role, but the prompt output grants no production write permission.",
                  sample="Snapshot H-47: 47,000 source orders\nKey: tenant_id + order_id\nTarget schema version: recorded\nWrites continue: yes; tail watermark needed\nPrompt output: plan, not execution approval",
                  cost="Inventorying N source rows is O(N) scanning; a key manifest costs O(N) storage. This preparation prevents moving counts from being mistaken for data loss. Scope scans to authorized tenants and preserve the snapshot ID for validation.",
                  mistakes=["Do not compare unpinned source and target counts.", "Do not infer all legacy values from a sample.", "Do not give a planning prompt a write credential."],
                  related=["prompt-engineering/schema-migration-prompt-review", "prompt-engineering/dataset-intake-column-contract"]),
             dict(slug="backfill-prompt-status-mapping-and-quarantine", title="Backfill prompts: map known states and quarantine unknowns", section=applications,
                  summary="Preserve unsupported legacy states and missing keys as reviewable exceptions.",
                  definition="A migration mapping lists source value, target value, preconditions, null handling, owner, and test case. Unknown source states should enter a reason-coded quarantine rather than a plausible default. Ask the model to identify collisions where distinct source meanings map to one target value, then have the data owner approve any intentional loss. Deterministic code applies the versioned mapping and emits a per-row outcome. Keep the original value and row key so a corrected mapping can replay only affected records.",
                  case="Of 47,000 Harbor orders, 46,940 map under the approved rules. Forty-seven have unfamiliar legacy statuses, and 13 lack required tenant IDs; the groups are disjoint, so 60 rows are quarantined. The assistant does not call the unknown status 'pending' just to make every row load. It creates an exception ledger with reason, pseudonymous key, observed value, and owner.",
                  sample="47,000 = mapped 46,940 + quarantined 60\nUNKNOWN_STATUS: 47 | TENANT_ID_MISSING: 13\nFallback to pending: prohibited without approval\nPreserve source value and row key",
                  cost="Applying an indexed mapping to N rows is O(N) expected time and O(K+E) memory for K mapping keys and E exceptions. Quarantine costs review time but avoids semantic loss. A model can cluster unknown values; only an owner can authorize new meaning.",
                  mistakes=["Do not silently default unknown statuses.", "Do not double-count overlapping exception IDs.", "Do not erase the original value after quarantine."],
                  related=["prompt-engineering/input-normalization-contract", "prompt-engineering/schema-migration-prompt-review"]),
             dict(slug="backfill-prompt-idempotent-batches-and-checkpoints", title="Backfill prompts: bound batches and make retries idempotent", section=applications,
                  summary="Use stable keys, durable checkpoints, and a rule for concurrent updates.",
                  definition="A backfill prompt should state the ordering key, batch size, idempotent write rule, checkpoint contents, retry behavior, and rate limit. A checkpoint means a range was processed under a mapping version, not that its values are correct. The migration runner executes reviewed code; a model merely drafts a runbook. Preserve row versions where concurrent writes matter. A retry must not create a second target row or overwrite a newer source change with an older snapshot value.",
                  case="Harbor processes the 46,940 mappable rows in bounded key ranges. If a worker stops after committing a range, it resumes from the last durable checkpoint, and replaying that range yields the same target identity. The 60 quarantined rows remain in a separate owner queue. A source status update during the backfill is applied by the later change tail rather than being erased by a stale retry.",
                  sample="Batch key: tenant_id + order_id\nCheckpoint: committed key + mapping version + watermark\nRetry: same target identity, no duplicate insert\nConcurrent change: compare version or replay tail",
                  cost="Processing N rows in batches of B is O(N) row work with about O(N/B) checkpoint writes, aside from index and network cost. Small batches shorten locks but increase overhead. Monitor latency and replication lag; a compact generated loop can still overload a live database.",
                  mistakes=["Do not call checkpoint completion value parity.", "Do not let retries create new target IDs.", "Do not overwrite a newer change with stale snapshot data."],
                  related=["prompt-engineering/schema-migration-prompt-review", "prompt-engineering/tool-call-authorization-contract"]),
             dict(slug="backfill-prompt-live-tail-and-write-ownership", title="Backfill prompts: account for writes during migration", section=production,
                  summary="Define one write owner and a replay watermark for the live tail.",
                  definition="A live backfill must account for changes after its snapshot through a write pause, controlled dual write, or ordered change-stream replay. The prompt should ask which system owns writes, how updates and deletes are represented, what watermark marks a complete tail, and how lag is observed. A zero-lag screenshot is not a durable completion claim if more events can arrive. The cutover plan needs an explicit stable gate and divergence monitoring after traffic changes.",
                  case="Harbor leaves the legacy table as write owner during snapshot H-47. New order updates enter an ordered tail that the target replays after backfill, including changes to quarantined IDs. The operator records the last applied watermark and measured lag at the planned cutover window. A generated paragraph cannot attest that the live stream is caught up; the running system supplies that evidence.",
                  sample="Write owner: legacy table\nSnapshot: H-47 | tail: ordered positions\nUpdate/delete: stable order key + source version\nCutover gate: measured lag and replay watermark",
                  cost="Applying T tail events is O(T) expected keyed work after O(N) snapshot processing. Stream ordering and deduplication may add cost. Controlled dual write can introduce partial-failure states, so any selected strategy needs a recovery path and observable lag receipt.",
                  mistakes=["Do not ignore post-snapshot updates.", "Do not give two systems write ownership without a conflict rule.", "Do not claim the tail is complete without a watermark."],
                  related=["prompt-engineering/analytics-prompt-identity-dedup-and-late-events", "prompt-engineering/schema-migration-prompt-review"]),
             dict(slug="backfill-prompt-count-and-field-parity", title="Backfill prompts: compare count and field-level parity", section=production,
                  summary="Expose wrong values even when destination row counts match.",
                  definition="Count parity is necessary but weak. A validation prompt should request the fixed source population, mapped and quarantined counts, destination unique-key count, duplicate-key check, field comparison, and mismatch ledger. Hashes help only when both sides use the same canonical encoding and field set. Keep row IDs for every mismatch. Reconcile all groups to the source total; a target with the right number of rows can still contain wrong statuses.",
                  case="Harbor has 47,000 source rows: 46,940 mapped and 60 quarantined. The target has 46,940 rows, so eligible count parity passes. A keyed status comparison finds three wrong values, leaving 46,937 matching. The model's report states both facts and withholds the cutover claim. An engineer checks whether mapping logic or retry ordering caused the three errors, then reruns the affected and full-population checks.",
                  sample="47,000 = 46,940 mapped + 60 quarantined\n46,940 target = 46,937 matching + 3 mismatched\nCount gate: pass | field-value gate: fail\nCutover: blocked",
                  cost="Sorting both N-row sets by key costs O(N log N); an indexed merge is O(N) after index preparation. Hash comparison is O(N) expected time and O(N) memory. The extra read pass reveals errors that a total cannot, and the three keyed IDs make the repair check specific.",
                  mistakes=["Do not equate equal counts with equal values.", "Do not compare hashes with different field encodings.", "Do not omit quarantined rows from source reconciliation."],
                  related=["prompt-engineering/aggregate-denominator-reconciliation", "prompt-engineering/report-claim-ledger-and-number-reconciliation"]),
             dict(slug="backfill-prompt-cutover-fallback-and-private-ledger", title="Backfill prompts: hold cutover until fallback is rehearsed", section=production,
                  summary="Tie release to value checks, tail lag, owner approval, and a safe return path.",
                  definition="A cutover packet needs mapping disposition, row and value parity, tail lag, read-path tests, capacity, rollback route, decision owner, and communications. The prompt drafts a checklist; it does not execute a switch. A fallback must account for writes accepted after any switch, since restoring an old backup alone may lose them. Keep private row content in the approved system and pass only counts, pseudonymous exception IDs, and synthetic examples into review text. Record a new receipt after the actual operation.",
                  case="Harbor still has 60 undispositioned source rows and three wrong target values. The decision is hold; the legacy table remains write owner. The operator rehearses a return route and a plan for post-switch writes in a representative environment. After owners resolve the 60 and three, a fresh parity and tail check can support a new approval. The assistant cannot label a plan as a completed cutover or paste tenant records into the memo.",
                  sample="Open: 47 unknown + 13 tenant missing + 3 value mismatches\nCurrent write owner: legacy\nPrivate rows: stay in controlled system\nFallback: preserve post-switch writes\nDecision: hold until fresh approval and receipt",
                  cost="Checking G measured release gates is O(G) lookups, but rehearsal and fallback capacity dominate elapsed time. A summary built from E exceptions and B batch receipts costs O(E+B) ledger work. The slower operator gate protects data that is harder to recover than a draft paragraph.",
                  mistakes=["Do not cut over from matching row counts alone.", "Do not promise rollback without handling post-switch writes.", "Do not expose full tenant rows to a planning prompt by default."],
                  related=["prompt-engineering/infrastructure-postapply-verification-and-rollback-review", "prompt-engineering/privacy-and-data-minimization"]),
         ],
         backlinks=[("prompt-engineering/schema-migration-prompt-review",0),("prompt-engineering/input-normalization-contract",1),("prompt-engineering/tool-call-authorization-contract",2),("prompt-engineering/analytics-prompt-identity-dedup-and-late-events",3),("prompt-engineering/aggregate-denominator-reconciliation",4),("prompt-engineering/infrastructure-postapply-verification-and-rollback-review",5)],
         questions=[
             ("What population is in H-47?","47,000 keyed source orders","46,940 target values","Three screenshots","The snapshot fixes the source population."),
             ("What happens to unknown legacy status?","Reason-coded quarantine","Automatic pending status","Removal from totals","Unsupported values need owner disposition."),
             ("How many rows are quarantined?","60: 47 status unknown and 13 tenant missing","47","13","The disjoint groups sum to 60."),
             ("What must an idempotent retry avoid?","Duplicate or stale target writes","Every checkpoint","All source updates","Repeating a batch must preserve identity and version rules."),
             ("What handles post-snapshot writes?","A defined tail or other write-ownership strategy","A static count","A model summary","Live changes need replay or a pause."),
             ("What does 46,940 target rows prove?","Eligible count parity, not value parity","All values match","All source rows moved","Three statuses still mismatch."),
             ("How many mapped values currently match?","46,937","46,940","47,000","Three of 46,940 target rows mismatch."),
             ("What should the three mismatches trigger?","Keyed investigation and a failed value gate","A green cutover","A guessed default","Count parity cannot erase value errors."),
             ("Who currently owns writes?","The legacy table","Both systems without a rule","The prompt model","The project keeps one owner before cutover."),
             ("What must fallback account for?","Writes accepted after a switch","Only the old backup name","Only chart colors","Reversal can lose intervening work."),
             ("What should a planning prompt normally receive?","Counts and minimal pseudonymous exceptions","Full tenant rows by default","Unrestricted write credentials","Lineage can be preserved with less exposure."),
             ("What is the current cutover decision?","Hold until exceptions, values, and tail are verified","Switch because counts match","Ignore the 60 quarantined","Required gates remain open."),
         ]),
]

new_paths = []
for cluster in clusters:
    new_paths.extend("prompt-engineering/" + spec["slug"] for spec in cluster["specs"])
    new_paths.extend([cluster["project"], cluster["quiz"]])
assert len(new_paths) == len(set(new_paths)) and not set(new_paths) & lookup.keys()
titles = {row["path"]: row["title"] for row in entries}
for cluster in clusters:
    titles.update({"prompt-engineering/" + spec["slug"]: spec["title"] for spec in cluster["specs"]})
    titles[cluster["project"]] = cluster["project_title"]
    titles[cluster["quiz"]] = cluster["quiz_title"]


def link(path):
    assert path in titles, path
    return f'<a href="/{html.escape(path)}">{html.escape(titles[path])}</a>'


def links(paths):
    return "<ul>" + "".join("<li>" + link(path) + "</li>" for path in dict.fromkeys(paths)) + "</ul>"


def related(paths):
    return [{"path": path, "title": titles[path]} for path in dict.fromkeys(paths)]


def article(path, title, summary, body, section, order, connections, tag, kind="tutorial"):
    row = copy.deepcopy(lookup["prompt-engineering/evaluation-slice-design"])
    subjects = {applications: "prompt-engineering-applications", production: "prompt-engineering-production", projects: "prompt-engineering-project"}
    row.update(id=str(uuid.uuid5(uuid.NAMESPACE_URL, "aitrove:" + path)), path=path, title=title,
               summary=summary, body=body, subject=subjects[section], difficulty="Advanced",
               tags=["prompt engineering", tag], sort_order=order,
               status="published", published_at=stamp, created_at=stamp, updated_at=stamp)
    row["data"].update(kind=kind, reading_minutes=11 if kind == "tutorial" else 18,
                       author_path="authors/aitrove-editorial", subject_root=subject_root,
                       section_path=section, content_format="html", seo_ready=True,
                       related=related(connections))
    return row


new_rows = []
for cluster in clusters:
    paths = ["prompt-engineering/" + spec["slug"] for spec in cluster["specs"]]
    for index, (path, spec) in enumerate(zip(paths, cluster["specs"])):
        connections = [spec["section"], subject_root] + spec["related"] + [other for other in paths if other != path] + [cluster["project"], cluster["quiz"]]
        body = ("<p>" + html.escape(spec["definition"]) + "</p>"
                + "<h2>Operational case</h2><p>" + html.escape(spec["case"]) + "</p>"
                + '<pre><code class="language-text">' + html.escape(spec["sample"], quote=False) + "</code></pre>"
                + "<h2>Performance and review cost</h2><p>" + html.escape(spec["cost"]) + "</p>"
                + "<h3>Common Mistakes</h3><ul>" + "".join("<li>" + html.escape(item) + "</li>" for item in spec["mistakes"]) + "</ul>"
                + "<h2>Connected lessons</h2>" + links(connections))
        new_rows.append(article(path, spec["title"], spec["summary"], body, spec["section"], cluster["order"] + index * 10, connections, cluster["tag"]))

    project_connections = paths + [cluster["quiz"], "prompt-engineering/evaluation-slice-design", "prompt-engineering/report-claim-ledger-and-number-reconciliation"]
    project_body = ("<p>" + html.escape(cluster["intro"]) + "</p>"
                    + "<h2>Review the packet</h2><p>" + html.escape(cluster["case"]) + "</p>"
                    + '<pre><code class="language-text">' + html.escape(cluster["sample"], quote=False) + "</code></pre>"
                    + "<h2>Performance and review cost</h2><p>" + html.escape(cluster["cost"]) + "</p>"
                    + "<h3>Common Mistakes</h3><ul>" + "".join("<li>" + html.escape(item) + "</li>" for item in cluster["mistakes"]) + "</ul>"
                    + "<h2>Related lessons</h2>" + links(project_connections))
    new_rows.append(article(cluster["project"], cluster["project_title"], "Apply the " + cluster["label"].lower() + " evidence contract to a fictional packet.", project_body, projects, cluster["order"] + 80, project_connections, cluster["tag"], "project"))

    quiz = copy.deepcopy(lookup["quizzes/prompt-engineering-security-alert-triage"])
    quiz.update(id=str(uuid.uuid5(uuid.NAMESPACE_URL, "aitrove:" + cluster["quiz"])), path=cluster["quiz"],
                title=cluster["quiz_title"], summary="Test evidence, arithmetic, boundaries, and release decisions in " + cluster["label"].lower() + ".",
                body="<p>Choose the decision supported by the recorded packet.</p><h2>Lessons</h2>" + links(paths) + "<h2>Project and sections</h2>" + links([cluster["project"], applications, production, quizzes]),
                sort_order=cluster["order"] + 90, status="published", published_at=stamp, created_at=stamp, updated_at=stamp)
    quiz["data"].update(subject_root=subject_root, section_path=quizzes, content_format="html",
                        author_path="authors/aitrove-editorial", seo_ready=True, duration_minutes=12,
                        related=related(paths + [cluster["project"]]),
                        questions=[{"prompt": prompt,
                                    "options": ([correct, wrong_a, wrong_b][index % 3:] + [correct, wrong_a, wrong_b][:index % 3]),
                                    "answer": (-index) % 3, "explanation": explanation}
                                   for index, (prompt, correct, wrong_a, wrong_b, explanation) in enumerate(cluster["questions"])])
    new_rows.append(quiz)

    for hub_path, selected, title, summary in [
        (applications, paths[:3], cluster["label"] + " inputs", "Define the evidence and task unit before findings."),
        (production, paths[3:], cluster["label"] + " review", "Verify comparisons and release boundaries."),
        (projects, [cluster["project"]], cluster["label"] + " project", "Apply the lesson sequence to a fictional packet."),
        (quizzes, [cluster["quiz"]], cluster["label"] + " decisions", "Test the packet's decision gates."),
    ]:
        hub = lookup[hub_path]
        hub["data"]["modules"].append({"title": title, "summary": summary, "lessons": selected})
        hub["body"] += "<h2>" + html.escape(title) + "</h2><p>" + html.escape(summary) + "</p>" + links(selected + [cluster["project"], cluster["quiz"]])
        hub["updated_at"] = stamp
    lookup[subject_root]["body"] += "<h2>" + html.escape(cluster["label"] + " prompts") + "</h2><p>Follow evidence from intake to a bounded decision.</p>" + links(paths + [cluster["project"], cluster["quiz"]])
    lookup[subject_root]["updated_at"] = stamp

    for old_path, new_index in cluster["backlinks"]:
        row = lookup[old_path]
        row["body"] += "<p><strong>Continue with:</strong> " + link(paths[new_index]) + ".</p>"
        row["data"]["related"] = related([item["path"] for item in row["data"].get("related", [])] + [paths[new_index]])
        row["updated_at"] = stamp

entries.extend(new_rows)
fixture.write_text(json.dumps(entries, ensure_ascii=False, indent=2) + "\n")
print(json.dumps({"newLessons": 12, "newProjects": 2, "newQuizzes": 2, "newPaths": [row["path"] for row in new_rows]}))
