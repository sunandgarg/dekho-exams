"""Publish original Spring configuration and schema-rollout lessons with checked limits."""
from __future__ import annotations
import datetime,html,json,pathlib,re,uuid
ROOT=pathlib.Path(__file__).resolve().parents[1];FILE=ROOT/'src/data/fixtures.json'
rows=json.loads(FILE.read_text());by_path={r['path']:r for r in rows};stamp=datetime.datetime.now(datetime.UTC).isoformat();specs=[]

def add(subject,slug,title,opening,sections,code,proof,limits,mistakes,links):
 specs.append(dict(subject=subject,path='spring/'+slug,title=title,opening=opening,sections=sections,code=code,proof=proof,limits=limits,mistakes=mistakes,links=links))

add('spring-boot','boot-command-line-precedence','Spring Boot command-line properties: test the effective value at startup',
'Command-line properties can replace application defaults before a Spring Boot context binds its configuration objects.',[
 ('The checked value',[
 'BootRelaySettingsTest starts a non-web SpringApplication context with relay.batch-size=8 and relay.timeout=2s as defaults. It passes --relay.batch-size=12 to run. The RelaySettings bean reports 12 and keeps the two-second timeout. The assertion reads the bound object, not only the raw Environment property, so it catches an override that exists but never reaches the consumer.',
 'This check uses SpringApplicationBuilder rather than manually inserting property sources. It proves the command-line/default ordering for this small context. It does not prove a precedence matrix involving actual operating-system environment variables, imported config files, Kubernetes secrets or remote configuration. [[spring/config-override-check|The earlier override fixture]] inserts named sources directly; [[spring/boot-config-source-matrix|the matrix lesson]] separates those two forms of evidence.' ]),
 ('Treat the effective setting as a contract',[
 'An operator may believe a flag was applied when a misspelled key silently leaves a default active. During startup, log a redacted subset of effective non-secret settings or expose a protected diagnostic view. Do not print credentials or access tokens. Use one canonical property prefix and document units for time and size values.',
 'For a relay, batch size affects database load and outage recovery. Changing it without a load test can increase lock waits. [[spring/boot-duration-units|The duration lesson]] checks that a separate timeout does not borrow an unintended unit.'])],
 '''new SpringApplicationBuilder(SettingsConfig.class)
    .web(WebApplicationType.NONE)
    .properties("relay.batch-size=8", "relay.timeout=2s")
    .run("--relay.batch-size=12");''',
 'BootRelaySettingsTest.commandLineOverridesPackagedDefaults',
 'The test uses application defaults and one command-line argument. It does not load an application.properties file or control the host environment.',
 ['Do not infer a deployment value from a source file alone.','Do not log secrets while reporting effective settings.','Do not accept an unrecognized override key without an operator check.'],
 ['spring/boot-duration-units','spring/boot-startup-validation','spring/boot-config-source-matrix','spring/config-override-check'])

add('spring-boot','boot-duration-units','Spring Boot Duration binding: make timeout units explicit',
'A typed Duration property carries a time unit into application code instead of leaving a raw integer to be interpreted later.',[
 ('The checked binding',[
 'RelaySettings declares timeout as Duration. The Boot fixture starts with a 2s default, then runs with --relay.timeout=450ms. It asserts Duration.ofMillis(450), not 450 seconds or an unlabelled numeric value. The unit suffix is part of the operator contract.',
 'A typed field prevents one common conversion error, but it does not set a safe deadline by itself. A 450-millisecond value might be too short for the target service or too long for a request budget. [[spring/boot-startup-validation|Startup validation]] should reject missing or out-of-range values; the current fixture validates non-null but does not impose a numeric timeout range.' ]),
 ('Budget the whole operation',[
 'A connect timeout is only one stage. DNS, connection acquisition, request write, response read and retries consume the same wall-clock operation budget. Name each configured deadline and state whether it applies per attempt or across all attempts. If a retry loop can run indefinitely, a correct Duration parse does not save the service from exhaustion.',
 'The test does not open a network connection. It checks binding, not timeout enforcement. [[spring/relay-retry-schedule|The retry lesson]] covers stored due times; this setting could eventually control an adapter, but that wiring is still absent.'])],
 '''record RelaySettings(@Min(1) @Max(100) int batchSize,
                     @NotNull Duration timeout) { }
// --relay.timeout=450ms binds to Duration.ofMillis(450).''',
 'BootRelaySettingsTest.explicitDurationUnitBindsWithoutGuessingMilliseconds',
 'The test proves one explicit unit through Boot binding. It does not test negative durations, overflow, deployed timeouts or whole-operation deadlines.',
 ['Do not document a naked number when the unit matters.','Do not confuse a parsed timeout with enforced cancellation.','Do not set per-attempt timeouts without an overall budget.'],
 ['spring/boot-command-line-precedence','spring/boot-startup-validation','spring/relay-retry-schedule','spring/configuration-properties'])

add('spring-boot','boot-startup-validation','Spring Boot configuration validation: reject an unusable relay before work starts',
'Validated configuration prevents a Spring Boot context from starting with a batch size outside the declared operating range.',[
 ('Fail at binding',[
 'The RelaySettings record carries @Min(1), @Max(100) and @NotNull constraints. The test passes --relay.batch-size=0 over a valid default. Context creation throws a runtime startup failure; the failure analysis names the command-line property origin and the minimum constraint. No scheduler starts in this small configuration context.',
 'The test checks the invalid effective value, not a controller request. A bad setting should fail before the worker claims events. [[spring/boot-command-line-precedence|The precedence lesson]] explains how the invalid command-line value wins. Existing [[spring/configuration-properties|configuration material]] covers typed binding more generally.' ]),
 ('What one constraint misses',[
 'Min and max protect only the numeric range. They do not prove that batch size 100 fits connection-pool capacity, that timeout matches a service objective, or that a secret points to a trusted endpoint. Validate cross-field invariants where needed and exercise them in a startup test. Keep the error message useful without printing a secret value.',
 'The fixture has no external database or broker. A successfully bound configuration does not mean dependencies are ready. [[spring/dependency-readiness|Readiness]] is a separate operational signal after startup.'])],
 '''@Validated
@ConfigurationProperties("relay")
record RelaySettings(@Min(1) @Max(100) int batchSize,
                     @NotNull Duration timeout) { }''',
 'BootRelaySettingsTest.invalidEffectiveBatchSizePreventsStartup',
 'One invalid command-line batch size is checked. No full environment matrix, secret binding, cross-field rule or deployed health check is included.',
 ['Do not silently clamp an invalid operator value.','Do not treat successful binding as dependency readiness.','Do not leak secret values in startup errors.'],
 ['spring/boot-command-line-precedence','spring/boot-duration-units','spring/dependency-readiness','spring/configuration-properties'])

add('spring-boot','boot-config-source-matrix','Spring Boot configuration sources: test each deployment path, not a guessed order',
'A configuration source matrix records which value reaches a typed bean when defaults, files, environment variables and command-line arguments disagree.',[
 ('Two forms of evidence',[
 'The kit has an ApplicationContextRunner test that inserts a packaged-default source and an operator source manually, then checks the bound timeout. A newer SpringApplicationBuilder test passes defaults and a command-line override through Boot startup. Both checks are narrow. Neither sets a real process environment variable or reads a mounted config file.',
 'Build a deployment matrix with one case per actual source combination: packaged file, profile-specific file, mounted file, environment variable, command-line flag and secret store. Assert the effective bean value and the source origin for a non-secret key. [[spring/boot-command-line-precedence|The CLI check]] is the first checked row. [[spring/config-override-check|The manual source check]] is a second, different row.' ]),
 ('Reduce configuration drift',[
 'Use one prefix and document the supported keys. A property name that changes between releases needs a migration notice and a test for the old key. Fail startup when a required setting is absent. Unknown fields require a policy: Boot binding can ignore unknown names unless the application opts into stricter behavior, so a typo may leave the default running.',
 'Do not publish values for credentials. Verify that a secret is present and correctly shaped without returning it in an error page or health detail. A deployment-specific override deserves a real startup test in the deployment environment, not only a unit test with a MapPropertySource.'])],
 '''// Matrix to add outside this kit:
// packaged file × profile file × environment × CLI × mounted secret
// Assert the bound RelaySettings value for each supported combination.''',
 'ConfigurationOverrideBoundaryTest.selectsAndValidatesTheEffectiveTimeout and BootRelaySettingsTest.commandLineOverridesPackagedDefaults',
 'The full matrix is a plan. Only a manual two-source override and a Boot default/CLI override are checked today.',
 ['Do not claim a real environment-variable test from a manually inserted MapPropertySource.','Do not display secret values when explaining origin.','Do not assume a misspelled property causes startup failure by default.'],
 ['spring/boot-command-line-precedence','spring/boot-startup-validation','spring/config-override-check','spring/profiles-properties'])

add('spring-data','schema-expand-column','Spring database rollout: add a nullable column before changing every writer',
'An expand migration adds schema capacity while the old application version can still write rows.',[
 ('The checked expansion',[
 'SchemaEvolutionContractTest starts with receipt_id and amount_minor, then adds nullable tenant_id. It inserts an old-shape row that names only the original columns. H2 accepts the row, leaving tenant_id null. This proves the local expansion preserves old-writer compatibility for that one insert shape.',
 'The fixture then backfills both existing rows to legacy. [[spring/schema-backfill-batch|The backfill lesson]] explains why a production update needs batches and a tenant ownership rule. [[java/versioned-migrations|The Java migration page]] describes versioned application boundaries; this Spring page focuses on the datasource behavior in the kit.' ]),
 ('Roll forward in stages',[
 'A deployed sequence usually needs: add a nullable column, deploy code that writes it, backfill historical rows, verify absence of nulls, then add a required constraint. If old instances remain during a rolling release, contracting early breaks them. The test demonstrates exactly that rejection in [[spring/schema-contract-gate|the contract phase]].',
 'H2 DDL and production DDL differ. Large table rewrites, lock duration, replication lag and rollback rules need target-database tests. The source kit invokes SQL directly; it does not run a migration tool or store a schema history.'])],
 '''alter table shipment_receipt add column tenant_id varchar(40);
insert into shipment_receipt(receipt_id, amount_minor) values (102, 500);''',
 'SchemaEvolutionContractTest.nullableExpansionAcceptsOldWriterAndBackfillPreservesRows',
 'One H2 table and two rows are checked. No rolling deployment, target-database lock estimate or versioned migration runner is present.',
 ['Do not add NOT NULL before old writers are gone or updated.','Do not use select-star assumptions across a schema rollout.','Do not treat H2 DDL cost as a production estimate.'],
 ['spring/schema-backfill-batch','spring/schema-contract-gate','spring/migration-runner-boundary','java/versioned-migrations'])

add('spring-data','schema-backfill-batch','Spring database backfill: assign historical rows before enforcing ownership',
'A backfill assigns a valid tenant value to historical rows while a new column is still nullable.',[
 ('The checked row state',[
 'The H2 fixture inserts one row before expansion and one old-writer row afterward. Both have null tenant_id until an UPDATE assigns legacy. A count then finds two legacy rows. This is an explicit local rule chosen for the fixture; it is not a safe universal rule for assigning real customer records.',
 'For a real tenant migration, derive ownership from trusted existing data. Quarantine rows whose owner cannot be proven. Count unresolved rows before adding a NOT NULL constraint. [[spring/tenant-jdbc-predicate|Tenant predicates]] only protect reads once the stored owner is correct; a wrong backfill can make authorization consistently wrong.' ]),
 ('Bound the production job',[
 'The fixture updates the entire tiny table in one statement. On a large table, choose bounded batches with a stable key range or cursor, record progress, make reruns idempotent and monitor lock waits. A process can fail between batches; restarting should not duplicate or skip work. Verify sample rows and total counts before contraction.',
 'A migration tool can version the DDL, but a data backfill may need a separate controlled job and audit trail. [[spring/migration-runner-boundary|The runner lesson]] states what this kit does not automate. [[spring/schema-contract-gate|The contract test]] shows the failure old writers see after the final constraint.'])],
 '''update shipment_receipt
set tenant_id = 'legacy'
where tenant_id is null;''',
 'SchemaEvolutionContractTest.nullableExpansionAcceptsOldWriterAndBackfillPreservesRows',
 'The test has two rows and a single H2 UPDATE. It does not prove correct ownership of real tenant data, bounded lock time or restart-safe batch progress.',
 ['Do not invent a tenant owner for ambiguous historical data.','Do not run an unbounded update on a large table without measuring locks.','Do not enforce NOT NULL while unresolved rows remain.'],
 ['spring/schema-expand-column','spring/schema-contract-gate','spring/migration-runner-boundary','spring/tenant-jdbc-predicate'])

add('spring-data','schema-contract-gate','Spring database contract phase: reject old writers only after backfill',
'A contract migration enforces a required tenant column after data and application writers have moved to the new shape.',[
 ('The checked boundary',[
 'The test adds tenant_id as nullable, backfills the original row, then sets the column NOT NULL. An old writer that inserts only receipt_id and amount_minor now fails with a translated data-integrity exception. A new writer that supplies tenant_id=east succeeds. Two rows remain after the rejected insert.',
 'That failure is the point of the test. The expansion phase lets both writer shapes coexist; the contract phase deliberately ends old-writer compatibility. [[spring/schema-expand-column|Expansion]] and [[spring/schema-backfill-batch|backfill]] must be verified before this step reaches a rolling deployment.' ]),
 ('Gate on observed state',[
 'Before contraction, check that all running application versions write the new column, unresolved null count is zero, backfill ownership has been reviewed and rollback plans do not require the old writer. Keep the migration step in version control and test it on the target engine. H2 accepts this DDL, but its locks and failure modes are not a production model.',
 'The local test starts from a new in-memory database each run. It does not prove that applying a migration twice is safe, that a mixed-version fleet has drained, or that a failed production DDL transaction rolls back. [[spring/migration-runner-boundary|Migration tooling]] needs separate integration checks.'])],
 '''alter table shipment_receipt alter column tenant_id set not null;
-- Old insert omitting tenant_id now fails.
insert into shipment_receipt(receipt_id, amount_minor, tenant_id)
values (103, 900, 'east');''',
 'SchemaEvolutionContractTest.contractRejectsOldWriterOnlyAfterBackfill',
 'The test checks one H2 constraint transition. It does not run a mixed-version service fleet, a target database or a migration history runner.',
 ['Do not contract before old writers stop.','Do not assume failed production DDL rolls back as H2 does.','Do not skip the null-count and ownership checks.'],
 ['spring/schema-expand-column','spring/schema-backfill-batch','spring/migration-runner-boundary','spring/tenant-jdbc-predicate'])

add('spring-data','migration-runner-boundary','Spring Boot migrations: what a versioned runner must add to the SQL test',
'A versioned migration runner records which schema changes have been applied so application startup and deployment can reason about database state.',[
 ('The current kit boundary',[
 'SchemaEvolutionContractTest calls JdbcTemplate.execute with ALTER TABLE statements and uses a fresh H2 database for each test. It checks the row behavior of expand, backfill and contract. It does not include Flyway, Liquibase, a schema history table, checksums, repair policy or migration-on-startup wiring. Do not describe it as a Flyway test.',
 'Spring Boot can invoke a migration tool when the tool and its integration are present. A production rollout should pin migration scripts in version control, apply each version once, verify checksums and test the same scripts on the target database. [[spring/schema-expand-column|The expansion fixture]] supplies a small SQL contract, not that deployment workflow.' ]),
 ('Separate DDL from long data work',[
 'A backfill of millions of rows may exceed startup time and lock budgets. Keep it resumable and observable rather than hiding it in a startup hook. Gate contraction on measured completion and on old-writer retirement. Specify whether the migration runner or deployment pipeline owns execution so two rollout processes do not race ambiguously.',
 'The next integration test should start from the previous released schema, apply versioned scripts, start old and new writers at the right stages, and inspect history plus row state after a failure. [[spring/schema-rollout-tests|The test matrix]] names those cases.'])],
 '''// Not executed by this kit:
// V1__create_shipment_receipt.sql
// V2__add_nullable_tenant_id.sql
// V3__require_tenant_id.sql''',
 'SchemaEvolutionContractTest checks direct H2 SQL only; no migration runner test exists',
 'Migration history, checksums, target-database DDL behavior, concurrent deployment and rollback are not checked. The file names above are a design sketch, not shipped scripts.',
 ['Do not call direct JdbcTemplate DDL a versioned Flyway migration.','Do not place an unbounded backfill in application startup.','Do not contract before application versions and data are ready.'],
 ['spring/schema-expand-column','spring/schema-backfill-batch','spring/schema-contract-gate','spring/schema-rollout-tests'])

add('spring-testing','schema-rollout-tests','Spring schema rollout tests: check old and new writers at every phase',
'A schema rollout test matrix runs the old and new application write shapes against each migration phase.',[
 ('The local assertions',[
 'The source kit checks two points. After nullable expansion, an old insert omitting tenant_id succeeds and the backfill assigns both rows. After NOT NULL contraction, that old insert fails and a new insert with tenant_id succeeds. The tests inspect counts and stored values, not only exception types.',
 'That is a useful local contract, but a production sequence has more states: old code on old schema, old code on expanded schema, new code on expanded schema, new code after backfill and new code on contracted schema. [[spring/schema-expand-column|The first fixture]] and [[spring/schema-contract-gate|the second]] cover only a small subset in H2.' ]),
 ('Move to the target engine',[
 'Run the exact versioned SQL against the production database engine in a disposable integration environment. Include realistic indexes and row counts, concurrent traffic, migration restart after failure, read replicas if used and DDL lock monitoring. Check that rollback to the previous application version is possible at each deployment stage; after contraction it may not be.',
 'Do not infer Flyway checksum or migration-history behavior from these direct JdbcTemplate tests. [[spring/migration-runner-boundary|The runner plan]] is separate. Keep a reviewer-visible record of which versions can coexist.'])],
 '''mvn -q -Dtest=SchemaEvolutionContractTest test''',
 'SchemaEvolutionContractTest has two local H2 tests',
 'No migration tool, target database, mixed-version process pair, realistic table volume or crash/restart flow is checked.',
 ['Do not test only the final schema.','Do not claim old-version rollback works after a breaking constraint.','Do not use a tiny H2 table to estimate production DDL locks.'],
 ['spring/schema-expand-column','spring/schema-backfill-batch','spring/schema-contract-gate','spring/migration-runner-boundary'])

add('spring-exercises','config-schema-rollout-exercise','Spring exercise: predict startup and SQL states across a staged rollout',
'A rollout trace asks which configuration value binds and which write shape survives each database phase.',[
 ('Resolve startup first',[
 'The application default says relay.batch-size=8 and relay.timeout=2s. The operator passes --relay.batch-size=12 and --relay.timeout=450ms. Predict the bound record: batch size 12, timeout 450 milliseconds. Change the batch flag to 0; startup fails before a worker can claim an event. These are checked by BootRelaySettingsTest.',
 'Now add nullable tenant_id to shipment_receipt. An old writer omitting it succeeds. Backfill historical rows to legacy. Set tenant_id NOT NULL. The same old insert fails; a writer supplying east succeeds. These states are checked by SchemaEvolutionContractTest. [[spring/schema-contract-gate|The contract lesson]] explains why an old version must be drained first.' ]),
 ('Change the rollout',[
 'Suppose ten million rows have no trusted tenant owner. Do not label all of them legacy merely to satisfy a constraint. Describe how to quarantine ambiguous rows, batch provable assignments and measure completion. Then write the target-database and versioned-runner tests still missing from the kit.',
 'The exercise combines separate local fixtures. It is not a deployed migration, hosted judge or authorization audit. [[spring/boot-config-source-matrix|The configuration matrix]] and [[spring/schema-rollout-tests|the schema matrix]] are the next checks.'])],
 '''mvn -q -Dtest=BootRelaySettingsTest,SchemaEvolutionContractTest test''',
 'BootRelaySettingsTest and SchemaEvolutionContractTest provide the local answers',
 'The exercise has no real environment-variable source, migration runner, tenant registry or target database.',
 ['Do not treat a default property as the effective operator value.','Do not invent tenant ownership to satisfy NOT NULL.','Do not call a passing H2 test a deployed rollout.'],
 ['spring/boot-command-line-precedence','spring/boot-startup-validation','spring/schema-contract-gate','spring/schema-rollout-tests'])

def para(value):
 escaped=html.escape(value)
 return '<p>'+re.sub(r'\[\[([^|]+)\|([^\]]+)\]\]',lambda m:'<a href="/'+m[1]+'">'+m[2]+'</a>',escaped)+'</p>'

titles={p:r['title'] for p,r in by_path.items()};titles.update({s['path']:s['title'] for s in specs})
for spec in specs:
 p=spec['path'];assert p not in by_path,p;assert all(x in titles for x in spec['links']),p
 hub=next(r for r in rows if r['type']=='subject' and r['subject']==spec['subject'])
 body=para(spec['opening'])
 for heading,ps in spec['sections']:body+='<h2>'+html.escape(heading)+'</h2>'+''.join(para(x) for x in ps)
 lang='bash' if spec['code'].startswith('mvn ') else 'sql' if spec['code'].startswith(('alter ','update ')) else 'java'
 body+='<h2>Checked source</h2><pre><code class="language-'+lang+'">'+html.escape(spec['code'].strip(),quote=False)+'</code></pre>'
 body+='<h2>Verification boundary</h2>'+para(spec['proof']+'. The excerpt is shortened or a labelled design sketch; the kit contains the checked tests.')
 body+='<h2>Costs and limits</h2>'+para(spec['limits'])
 body+='<h3>Common Mistakes</h3><ul>'+''.join('<li>'+html.escape(x)+'</li>' for x in spec['mistakes'])+'</ul>'
 body+='<h2>Read next</h2>'+para(', '.join('[['+x+'|'+titles[x]+']]' for x in spec['links'])+'.')
 row=by_path['spring/if-match-receipt-write'].copy();row.update(id=str(uuid.uuid5(uuid.NAMESPACE_URL,'https://aitrove.in/'+p)),type='article',path=p,title=spec['title'],summary=spec['opening'],body=body,subject=spec['subject'],difficulty='Intermediate',status='published',tags=['spring','spring-boot','configuration' if spec['subject']=='spring-boot' else 'migration'],featured=False,sort_order=900+len(rows),published_at=stamp,created_at=stamp,updated_at=stamp)
 row['data']={'subject_root':'spring/spring-boot','section_path':hub['path'],'kind':'tutorial','content_format':'html','reading_minutes':max(4,round(len(re.sub(r'<[^>]+>',' ',body).split())/150)),'author_path':'authors/aitrove-editorial','seo_ready':True,'related':[{'path':x,'title':titles[x]} for x in spec['links']],'framework_version':'Spring Boot 4.0.8 / Spring Framework 7','java_version':'21 source-kit baseline','verification_suite':spec['proof'],'download_path':'/downloads/aitrove-spring-source-kit.zip'}
 rows.append(row);by_path[p]=row

groups={
 'spring-boot':('Effective relay settings',['spring/boot-command-line-precedence','spring/boot-duration-units','spring/boot-startup-validation','spring/boot-config-source-matrix']),
 'spring-data':('Staged tenant schema rollout',['spring/schema-expand-column','spring/schema-backfill-batch','spring/schema-contract-gate','spring/migration-runner-boundary']),
 'spring-testing':('Schema rollout checks',['spring/schema-rollout-tests']),
 'spring-exercises':('Settings and rollout trace',['spring/config-schema-rollout-exercise']),
}
for subject,(title,paths) in groups.items():
 hub=next(r for r in rows if r['type']=='subject' and r['subject']==subject)
 hub['data']['modules'].append({'title':title,'summary':'Check effective settings and staged database writes.','lessons':paths});hub['updated_at']=stamp
 if '<h2>Section lessons</h2>' in hub['body']:
  links='<ul>'+''.join('<li><a href="/'+p+'">'+html.escape(titles[p])+'</a></li>' for module in hub['data']['modules'] for p in module['lessons'])+'</ul>'
  hub['body']=re.sub(r'(<h2>Section lessons</h2>)[\s\S]*?(<h2>Continue learning</h2>)',lambda m:m[1]+links+m[2],hub['body'])

reverse={
 'spring/configuration-properties':['spring/boot-duration-units','spring/boot-startup-validation'],
 'spring/config-override-check':['spring/boot-command-line-precedence','spring/boot-config-source-matrix'],
 'spring/tenant-jdbc-predicate':['spring/schema-backfill-batch'],
 'spring/tenant-command-api-project':['spring/schema-contract-gate'],
 'spring/testing-boundaries':['spring/schema-rollout-tests'],
 'java/versioned-migrations':['spring/schema-expand-column'],
}
for p,targets in reverse.items():
 assert p in by_path,p
 row=by_path[p];marker='<h2>Continue with checked settings and schema rollout</h2>'
 row['body']=row['body'].split(marker)[0]+marker+para('Continue with '+', '.join('[['+x+'|'+titles[x]+']]' for x in targets)+'.');row['updated_at']=stamp

quiz_path='quizzes/spring-operations'
assert quiz_path not in by_path
questions=[
 ('A default batch size is 8 and the CLI passes --relay.batch-size=12. What binds?',['12','8','Both values as a list'],0,'Boot chooses the effective command-line value for the typed relay settings in the checked context.'),
 ('The CLI passes --relay.timeout=450ms. What is the typed value?',['Duration of 450 milliseconds','Duration of 450 seconds','A String with no time unit'],0,'The Boot fixture binds the explicit suffix to Duration.ofMillis(450).'),
 ('The effective batch size is 0 under @Min(1). What happens in the checked context?',['Startup fails','The setting silently becomes 1','The scheduler starts with zero work'],0,'Configuration validation rejects the value while the context is being created.'),
 ('Does the config fixture prove actual environment-variable precedence?',['No; it tests defaults and CLI plus a separate manual source test','Yes; every host environment is simulated','Yes; H2 selects the source'],0,'No real process environment variable or mounted config file is set in the source kit.'),
 ('After a nullable tenant_id column is added, can the old writer omit it?',['Yes in the H2 expansion check','No, because any new column is required','Only when Flyway runs'],0,'The old-shape INSERT succeeds while tenant_id remains nullable.'),
 ('Why must historical ownership be reviewed before backfill?',['A guessed tenant can turn later authorization into a consistent wrong answer','The SQL syntax requires a reviewer name','The column cannot contain text'],0,'A NOT NULL constraint cannot prove the stored tenant is the right tenant.'),
 ('What does the local backfill update select?',['Rows where tenant_id is null','Every row on each retry','Only rows already marked east'],0,'The fixture assigns a local legacy value to rows with null tenant_id.'),
 ('What changes after tenant_id becomes NOT NULL?',['An old insert omitting it fails','Existing rows disappear','Command-line settings stop binding'],0,'The contract test asserts rejection of the old writer shape and success of the new shape.'),
 ('Does SchemaEvolutionContractTest execute Flyway migrations?',['No; it calls direct H2 SQL','Yes; it checks Flyway history checksums','Yes; it starts a production database'],0,'The kit has no Flyway dependency or versioned migration runner.'),
 ('What should be checked before contracting a column?',['No unresolved rows and no old writers still running','Only that a nullable ALTER TABLE passed on H2','Only the newest application build hash'],0,'The rollout needs both data and application-version readiness.'),
 ('Why can a passing H2 schema test not estimate a production lock window?',['Engines and table volumes have different DDL behavior','JUnit disables indexes everywhere','A tiny table has more locks than a large one'],0,'The fixture has two in-memory rows and no deployment traffic.'),
 ('Which test belongs next for the rollout?',['Apply versioned scripts on the target engine with old and new writers','Repeat the same H2 insert without changes','Remove the tenant predicate from reads'],0,'A target-engine matrix is needed for DDL behavior and mixed-version compatibility.'),
]
q=by_path['quizzes/spring-core'].copy()
q.update(id=str(uuid.uuid5(uuid.NAMESPACE_URL,'https://aitrove.in/'+quiz_path)),path=quiz_path,title='Spring Boot settings and schema rollout quiz',summary='Twelve explained checks on effective settings and staged database changes.',sort_order=603,published_at=stamp,created_at=stamp,updated_at=stamp)
q['body']=para('A Spring self-check on configuration binding, validation and expand/backfill/contract database phases.')+'<h2>Review before answering</h2><ul>'+''.join('<li><a href="/'+p+'">'+html.escape(titles[p])+'</a></li>' for p in ['spring/boot-command-line-precedence','spring/boot-duration-units','spring/boot-startup-validation','spring/schema-expand-column','spring/schema-backfill-batch','spring/schema-contract-gate','spring/migration-runner-boundary'])+'</ul><h3>Common Mistakes</h3><ul><li>Do not mistake a default for the effective setting.</li><li>Do not contract a schema while old writers still run.</li><li>Do not describe direct H2 SQL as a migration-runner test.</li></ul>'
q['data']={'questions':[{'prompt':p,'options':o,'answer':a,'explanation':e} for p,o,a,e in questions],'duration_minutes':12,'subject_root':'spring/spring-boot','section_path':'spring/quizzes','content_format':'html','seo_ready':True}
rows.append(q);by_path[quiz_path]=q
quiz_hub=by_path['spring/quizzes'];quiz_hub['data']['modules'].append({'title':'Settings and schema rollout','summary':'Twelve explained questions on startup and migration phases.','lessons':[quiz_path]});quiz_hub['updated_at']=stamp
if '<h2>Section lessons</h2>' in quiz_hub['body']:
 links='<ul>'+''.join('<li><a href="/'+p+'">'+html.escape(by_path[p]['title'])+'</a></li>' for m in quiz_hub['data']['modules'] for p in m['lessons'])+'</ul>'
 quiz_hub['body']=re.sub(r'(<h2>Section lessons</h2>)[\s\S]*?(<h2>Continue learning</h2>)',lambda m:m[1]+links+m[2],quiz_hub['body'])
FILE.write_text(json.dumps(rows,ensure_ascii=False,indent=2)+'\n')
print(json.dumps({'articles':[s['path'] for s in specs],'quiz':quiz_path,'quizQuestions':len(questions)}))
