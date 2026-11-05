"""Publish original Spring Boot startup, config-import, and migration lessons."""
from __future__ import annotations
import datetime, html, json, pathlib, re, uuid
ROOT=pathlib.Path(__file__).resolve().parents[1]
FILE=ROOT/'src/data/fixtures.json';rows=json.loads(FILE.read_text());by={r['path']:r for r in rows}
stamp=datetime.datetime.now(datetime.UTC).isoformat();specs=[]

def add(subject,slug,title,opening,sections,code,lang,proof,limit,mistakes,links):
 specs.append(dict(subject=subject,path='spring/'+slug,title=title,opening=opening,sections=sections,code=code,lang=lang,proof=proof,limit=limit,mistakes=mistakes,links=links))

add('spring-boot','boot-profile-file-selection','Spring Boot profile files: bind only the selected environment override',
'A profile-specific properties file contributes settings when its named Spring profile is active.',[
('The checked choice',[
'BootRelaySettingsTest writes two files into a temporary directory. application.properties sets batch size 17 and timeout 750ms. application-review.properties sets batch size 29 only. The context starts with review active and the additional directory selected. The bound RelaySettings record reports 29 and 750ms. The profile file overrides one key; the base file still supplies the other.',
'The selected value matters to a background worker. A team can inspect the base file and assume 17 rows per tick while the deployed profile actually admits 29. [[spring/boot-config-precedence-file-cli|The CLI collision test]] shows a further override. [[spring/poller-batch-limit|The polling budget]] explains why a larger batch needs load measurements.' ]),
('Do not treat profile names as access control',[
'A profile selects configuration. It does not authenticate a caller, hide a secret or prevent an operator from starting the wrong profile. Print the active profile and non-secret effective settings in a protected startup diagnostic. Check a real deployment with its selected file; this fixture uses local JUnit files.',
'If two profiles define the same key, define and test their order for that deployment. This test selects one profile and does not claim every multi-profile ordering rule. A required setting should still be validated after all selected sources are loaded.'])],
'''Files.writeString(dir.resolve("application.properties"),
    "relay.batch-size=17\\nrelay.timeout=750ms\\n");
Files.writeString(dir.resolve("application-review.properties"),
    "relay.batch-size=29\\n");
try (var context = app().run("--spring.profiles.active=review",
    "--spring.config.additional-location=" + dir.toUri())) {
    assertEquals(29, context.getBean(RelaySettings.class).batchSize());
}''','java','BootRelaySettingsTest.activeProfileLoadsItsFileOverTheBaseFile',
'Only one local profile and a JUnit temporary directory are checked. No container mount, process environment variable, secret store or multi-profile collision is exercised.',
['Do not read only the base file when a profile is active.','Do not assume a profile is an authorization boundary.','Do not size production batches from one local fixture.'],
['spring/boot-additional-config-file','spring/boot-config-precedence-file-cli','spring/boot-startup-validation','spring/poller-batch-limit'])

add('spring-boot','boot-required-config-import','Spring Boot config import: fail startup when a required file is missing',
'A non-optional config import makes a missing external file a startup error rather than an unnoticed fallback.',[
('The missing-file test',[
'BootRelaySettingsTest points spring.config.import at a file URI that does not exist. The non-web Boot context fails before a RelaySettings bean can run. The test does not assert a specific outer exception class because Boot wraps the missing-location cause while constructing the application.',
'This policy fits a setting that must come from deployment state. If the application silently falls back to an old batch size or stale endpoint, it may process work with the wrong assumptions. [[spring/boot-optional-config-import|The optional case]] deliberately chooses different behavior. Document which imports are mandatory and check that the intended path is mounted before rollout.' ]),
('Do not put secrets into diagnostics',[
'A location error may reveal the path, while binding errors can reveal a rejected value. Avoid putting credentials in command-line arguments or startup logs. A missing secret import should prevent a service from accepting traffic, but the error page should not include a credential.',
'The test proves a missing local file is rejected. It does not verify a readable file that contains a wrong key, wrong permissions, a rotated secret, or the availability of a remote configuration service. [[spring/boot-external-config-validation|Typed validation]] handles the value after a source is loaded.'])],
'''String missing = configDirectory.resolve("missing.properties").toUri().toString();
assertThrows(RuntimeException.class,
    () -> app().run("--spring.config.import=" + missing));''','java','BootRelaySettingsTest.requiredImportFailsBeforeAWorkerCanStart',
'The test uses an absent file in a local temporary directory. It does not measure a deployment volume or a remote config source, and it does not inspect secret handling.',
['Do not mark a mandatory import optional merely to clear a startup failure.','Do not confuse a missing file with a present file containing an invalid value.','Do not print imported secrets in startup diagnostics.'],
['spring/boot-optional-config-import','spring/boot-external-config-validation','spring/boot-profile-file-selection','spring/dependency-readiness'])

add('spring-boot','boot-optional-config-import','Spring Boot optional config import: know which default survives',
'An optional config import lets startup proceed when its file is absent, leaving other configuration sources to supply the effective value.',[
('The checked fallback',[
'BootRelaySettingsTest prefixes an absent file URI with optional:. The context starts and RelaySettings reports the declared defaults: batch size 8 and timeout 2s. Those values are not proof that the file was loaded. The test chooses absence on purpose and asserts the fallback state.',
'For a local developer override, optional behavior can be useful. For a production-required endpoint or credential, it can hide a broken mount. [[spring/boot-required-config-import|The required import]] makes that failure visible. Decide per setting; do not apply optional: to an entire configuration path as a reflex.' ]),
('Make a fallback observable',[
'An operator should be able to tell whether the optional source was present without exposing secret values. Report a source-availability signal or a redacted effective setting. If the default is unsafe for production, reject startup with typed validation or a deployment-specific requirement.',
'This fixture has one absent file and programmatic defaults. It does not test partially written files, permission errors or simultaneous environment and CLI overrides. [[spring/boot-config-source-matrix|The source matrix]] separates those combinations.'])],
'''String missing = configDirectory.resolve("missing.properties").toUri().toString();
try (var context = app().run(
    "--spring.config.import=optional:" + missing)) {
    assertEquals(8, context.getBean(RelaySettings.class).batchSize());
}''','java','BootRelaySettingsTest.optionalMissingImportKeepsTheDeclaredDefaults',
'The fallback is checked for one local missing file. It does not establish that any other optional source is safe to omit in production.',
['Do not interpret a valid default as evidence that an import succeeded.','Do not make a required secret optional.','Do not hide the source of an effective value from operators.'],
['spring/boot-required-config-import','spring/boot-additional-config-file','spring/boot-config-source-matrix','spring/boot-startup-validation'])

add('spring-boot','boot-config-source-priority','Spring Boot config source priority: a builder default may lose to a packaged file',
'A programmatic SpringApplication default has lower priority than configuration loaded from the application file in this checked startup path.',[
('A test that first used the wrong database',[
'The source kit packages spring.datasource.url=jdbc:h2:mem:receipt_application. The first BootFlywayStartupTest supplied a unique H2 URL with SpringApplicationBuilder.properties. Boot still opened the packaged receipt_application database. Two test stages therefore touched the wrong shared database, and a supposed checksum failure did not occur. The test was corrected to pass the unique URL as a command-line argument.',
'This is a concrete reason to inspect the effective DataSource, not just a builder call. [[spring/boot-command-line-precedence|The settings fixture]] checks that CLI values reach a bound bean. [[spring/boot-flyway-startup|The migration fixture]] now checks separate database histories across two context starts.' ]),
('Protect isolation',[
'A test URL that is accidentally shadowed can contaminate another test or make a migration appear repeatable for the wrong reason. Use an isolated database name, assert the expected schema history and inspect the connection URL when setup is ambiguous. Do not rely on tests passing in one fixed order.',
'The source kit uses H2 with DB_CLOSE_DELAY=-1 so two contexts can see the same named database during one test. That is deliberate for the V2-to-V3 trace. It is not a persistence guarantee across process restarts.'])],
'''return new SpringApplicationBuilder(MigrationApplication.class)
    .web(WebApplicationType.NONE)
    .properties("spring.flyway.locations=classpath:db/relay-migration")
    .run("--spring.datasource.url=" + uniqueH2Url);''','java','BootFlywayStartupTest.start uses a command-line URL; BootRelaySettingsTest checks file/default/CLI binding',
'The verified collision is a packaged H2 URL versus a builder default. Other source combinations and a deployed database URL still require their own checks.',
['Do not assume a builder default outranks application.properties.','Do not share a fixed in-memory database name across isolation tests.','Do not treat H2 memory lifetime as a restart test.'],
['spring/boot-flyway-startup','spring/boot-config-source-matrix','spring/boot-command-line-precedence','spring/boot-profile-file-selection'])

add('spring-data','boot-flyway-startup','Spring Boot Flyway startup: apply versioned SQL before querying a receipt',
'Spring Boot can create a Flyway bean and migrate the configured DataSource while its application context starts.',[
('The checked non-web context',[
'BootFlywayStartupTest starts a minimal non-web Boot context with the test-scoped spring-boot-starter-flyway. It points spring.flyway.locations at three SQL resources under db/relay-migration and selects target version 2. When run returns, the test obtains Flyway and JdbcTemplate beans and counts two versioned history entries. The old receipt insert then succeeds while tenant_id is nullable.',
'A second context starts against the same named H2 database with target version 3. Boot applies the remaining migration before the test reads rows. The older insert shape now fails the NOT NULL constraint; the new shape succeeds. [[spring/flyway-expand-contract|The SQL phase lesson]] explains why this is a compatibility interval rather than a single schema flip.' ]),
('Name the application boundary',[
'This test proves Boot auto-configuration in a separate test application. It does not wire Flyway into the runnable ReceiptApplication. The starter is test-scoped, and the migrations are test resources. [[spring/flyway-boot-ownership|The ownership decision]] remains open for a real rollout.',
'H2 2.3.232 checks the local sequence. It does not measure DDL locks, transaction behavior or a concurrent replica deployment on the target engine. The startup path must be tested again against that engine before a production release.'])],
'''try (var context = start(uniqueH2Url, 2)) {
    assertNotNull(context.getBean(Flyway.class));
    var jdbc = context.getBean(JdbcTemplate.class);
    jdbc.update("insert into shipment_receipt(receipt_id, amount_minor) values (102, 500)");
}''','java','BootFlywayStartupTest.bootAppliesEachStageBeforeTheApplicationReadsRows',
'This is a non-web test context, test-scoped starter and H2 database. ReceiptApplication remains without runtime Flyway wiring.',
['Do not call a direct Flyway API test proof of Boot startup wiring.','Do not put the contract migration into service before old writers retire.','Do not infer target-engine lock time from H2.'],
['spring/boot-flyway-version-step','spring/boot-flyway-history-failure','spring/flyway-versioned-receipts','spring/flyway-boot-ownership'])

add('spring-data','boot-flyway-version-step','Spring Boot migration target: test an old writer before closing the schema',
'A staged migration test can stop at an intermediate version to check whether an older application write remains valid.',[
('V2 accepts the old shape',[
'The first Boot context targets migration version 2. Its receipt table has a nullable tenant_id. The test inserts receipt 102 with only receipt_id and amount_minor. Both that row and the V1 seed row have null tenant_id. A new reader that assumes ownership is already populated would be wrong during this overlap.',
'The second context targets version 3 against the same H2 URL. Flyway backfills those rows and tightens tenant_id to NOT NULL. The test counts zero null owners and rejects an old-shape insert. It then accepts receipt 104 with east as tenant. [[spring/schema-contract-gate|The contract phase]] must follow an application rollout that already writes the new field.' ]),
('This is a version step, not live coexistence',[
'The test closes the first context before opening the second. It does not run old and new processes at the same time. A real release should start both versions against a disposable target-engine database while traffic continues, then verify reads, writes and rollback options at each version.',
'V3 backfills a tiny test table in one statement. A large table may need bounded, resumable work with business-reviewed tenant assignment. A NOT NULL constraint can enforce presence, not correctness of that assignment.'])],
'''spring.flyway.target=2
# Old write omitting tenant_id succeeds here.
spring.flyway.target=3
# Only the new write shape succeeds after this stage.''','properties','BootFlywayStartupTest.bootAppliesEachStageBeforeTheApplicationReadsRows',
'Two contexts run sequentially on H2. There is no simultaneous old/new process pair, real user traffic or target-engine DDL measurement.',
['Do not deploy the NOT NULL phase while an old writer still runs.','Do not label a sequential test a mixed-version concurrency test.','Do not equate a non-null legacy value with verified tenant ownership.'],
['spring/boot-flyway-startup','spring/flyway-expand-contract','spring/schema-rollout-tests','spring/tenant-jdbc-predicate'])

add('spring-data','boot-flyway-history-failure','Spring Boot migration history failure: stop context startup on a mismatch',
'A changed recorded migration checksum can prevent a Boot context from completing startup when Flyway validates history.',[
('The isolated failure',[
'BootFlywayStartupTest first starts at version 3 in an isolated H2 database. It then changes the recorded checksum for V2 in that disposable history table and closes the context. A second Boot start against the same database throws before returning an application context. The test asserts failure; it does not suppress the mismatch or call repair.',
'[[spring/flyway-history-checksum|The direct API fixture]] isolates the validation exception. This Boot fixture checks the additional boundary: the application context itself does not finish creation. A deployment platform should keep an instance out of traffic when startup fails, but that platform behavior is not exercised here.' ]),
('Stop and inspect before repair',[
'A checksum mismatch may mean an applied file changed, an artifact was built incorrectly or the history table was altered. Inspect the release artifact and actual schema before deciding on a forward migration or a database-specific recovery procedure. Editing the history row to make startup pass can hide incompatible state.',
'The test deliberately modifies a checksum, not a SQL file. It says nothing about incomplete DDL on engines that cannot roll back a failed migration. [[spring/boot-flyway-test-scope|The test-scope boundary]] also means ReceiptApplication has no such startup gate yet.'])],
'''try (var context = start(url, 3)) {
    context.getBean(JdbcTemplate.class).update(
        "update \"flyway_schema_history\" set \"checksum\" = \"checksum\" + 1 where \"version\" = '2'");
}
assertThrows(RuntimeException.class, () -> start(url, 3));''','java','BootFlywayStartupTest.invalidHistoryPreventsTheNextBootStartup',
'The mismatch is injected into H2 history. No applied SQL file is edited and no deployment orchestrator, target engine or recovery action is tested.',
['Do not clear a checksum error by rewriting production history without investigation.','Do not serve traffic from a context that failed startup.','Do not treat a checksum check as proof that business rows are correct.'],
['spring/boot-flyway-startup','spring/flyway-history-checksum','spring/boot-flyway-test-scope','spring/dependency-readiness'])

add('spring-testing','boot-flyway-test-scope','Spring Boot migration tests: distinguish a test starter from a runtime rollout',
'A test-scoped migration starter can verify Boot auto-configuration without placing Flyway in the runnable application artifact.',[
('Two different fixtures',[
'FlywayReceiptMigrationTest calls Flyway.configure directly and checks ordered SQL plus history. BootFlywayStartupTest uses spring-boot-starter-flyway on the test classpath and lets a separate Boot context perform migration during startup. These tests establish different things. Neither changes ReceiptApplication to a production database-backed API.',
'The SQL files live under src/test/resources/db/relay-migration. The test sets spring.flyway.locations explicitly; the files are not a default runtime migration directory. The source ZIP includes test sources so readers can run them locally. [[spring/flyway-boot-ownership|The ownership lesson]] explains what would have to change for a deployed application.' ]),
('Test the artifact you ship',[
'Before claiming production startup migrations, promote the chosen dependency and reviewed SQL into the runtime artifact, or use a separate deployment migration job. Pin the target database module as needed and check its actual DDL behavior. Then verify the final packaged artifact in a disposable environment.',
'Keep test seed data out of production migrations unless it is genuinely required. Here V1 inserts one receipt for a controlled exercise. A production seed policy needs a different decision and review.'])],
'''<dependency>
  <groupId>org.springframework.boot</groupId>
  <artifactId>spring-boot-starter-flyway</artifactId>
  <scope>test</scope>
</dependency>''','xml','BootFlywayStartupTest and FlywayReceiptMigrationTest; Maven dependency has test scope',
'No production database module, runtime migration job, packaged ReceiptApplication integration or target-engine startup test exists.',
['Do not present the test starter as a runtime dependency.','Do not leave sample seed rows in a production release by accident.','Do not assume a passing H2 context validates another engine.'],
['spring/boot-flyway-startup','spring/flyway-boot-ownership','spring/flyway-versioned-receipts','spring/schema-rollout-tests'])

add('spring-exercises','boot-config-migration-trace','Spring exercise: trace selected config and staged Boot migrations',
'A startup trace asks which configuration value and schema version a context actually receives.',[
('Configuration trace',[
'The base file sets batch size 17 and timeout 750ms. The review profile file sets batch size 29 only. Predict the bound record with review active: 29 and 750ms. Next, remove a required imported file. The context fails. Prefix its location with optional: and the example context starts with declared defaults 8 and 2s. The corresponding BootRelaySettingsTest methods check these states.',
'Now place an unrelated packaged DataSource URL next to a builder default URL. Predict which database Boot opens. The source-kit startup test originally opened the packaged database; it now passes a unique URL as a CLI argument. [[spring/boot-config-source-priority|The priority lesson]] explains why.' ]),
('Migration trace',[
'Start one non-web Boot context targeting V2, insert a receipt without tenant_id and close it. Start a second context against the same H2 database targeting V3. Predict the null count and which insert shape fails. Finally change the V2 history checksum and predict whether a third context returns. The checked BootFlywayStartupTest covers these exact boundaries.',
'Write down what remains unproven: target-engine DDL, simultaneous old/new processes, large backfill and production dependency scope. The exercise has no hosted judge; run the source kit and compare persisted rows and history.'])],
'''mvn -q -Dtest=BootRelaySettingsTest,BootFlywayStartupTest test''','bash','BootRelaySettingsTest and BootFlywayStartupTest',
'The trace runs in one process with local files and H2. It is not a production deployment rehearsal or a cross-device graded exercise.',
['Do not infer the active profile from the base file alone.','Do not expect an optional import to prove the missing file was read.','Do not claim two sequential contexts are concurrent deployed versions.'],
['spring/boot-profile-file-selection','spring/boot-required-config-import','spring/boot-flyway-version-step','spring/boot-flyway-history-failure'])

add('spring-projects','boot-versioned-receipt-project','Spring Boot project: test a versioned receipt schema before choosing deployment ownership',
'A versioned receipt project should prove schema transitions before promoting a database-backed API.',[
('Assemble the local check',[
'The source kit already has three migration files and a non-web Boot startup fixture. Run V2, insert an old-shape receipt, then run V3 against the same named H2 database. Check history, backfilled rows, old-writer rejection and new-writer acceptance. Run a separate checksum-mismatch test to confirm startup fails rather than serving against uncertain schema state.',
'This is a project boundary, not a deployed receipt service. ReceiptApplication still uses an in-memory ReceiptStore and fixture Basic authentication. The test starter and SQL resources are not runtime migration wiring. [[spring/receipt-api-project|The earlier API project]] describes that runnable surface; [[spring/boot-flyway-test-scope|the test-scope lesson]] marks what remains separate.' ]),
('Choose the next release gate',[
'Decide whether an application instance or a deployment job owns migrations. Use a disposable instance of the selected production database, not H2 alone. Start actual old and new application versions across V2; measure DDL locks and verify rollback options. Backfill tenant ownership from an authoritative source before enforcing NOT NULL.',
'Only after those checks should the API use a persistent repository and make readiness depend on its required database. A passing migration test does not provide a real identity store, broker or durable outbox worker. Keep each boundary named in the deployment plan.'])],
'''mvn -q -Dtest=BootFlywayStartupTest,FlywayReceiptMigrationTest test''','bash','BootFlywayStartupTest and FlywayReceiptMigrationTest',
'The deliverable is a local checked source kit. There is no production database, migration job, runtime Flyway wiring, real issuer, broker or release orchestration.',
['Do not present the non-web test context as the runnable API.','Do not apply V3 before retiring old writers.','Do not treat a green migration test as proof of crash recovery.'],
['spring/boot-flyway-startup','spring/boot-flyway-test-scope','spring/receipt-api-project','spring/tenant-command-api-project'])

def para(value):
 escaped=html.escape(value)
 return '<p>'+re.sub(r'\[\[([^|]+)\|([^\]]+)\]\]',lambda m:'<a href="/'+m[1]+'">'+m[2]+'</a>',escaped)+'</p>'

titles={p:r['title'] for p,r in by.items()};titles.update({s['path']:s['title'] for s in specs})
for s in specs:
 p=s['path'];assert p not in by,p;assert all(x in titles for x in s['links']),p
 hub=next(r for r in rows if r['type']=='subject' and r['subject']==s['subject'])
 body=para(s['opening'])
 for heading,paragraphs in s['sections']:
  body+='<h2>'+html.escape(heading)+'</h2>'+''.join(para(x) for x in paragraphs)
 body+='<h2>Checked source</h2><pre><code class="language-'+s['lang']+'">'+html.escape(s['code'].strip(),quote=False)+'</code></pre>'
 body+='<h2>Verification boundary</h2>'+para(s['proof']+'. The excerpt is shortened; the source kit contains the checked fixture.')
 body+='<h2>Costs and limits</h2>'+para(s['limit'])
 body+='<h3>Common Mistakes</h3><ul>'+''.join('<li>'+html.escape(x)+'</li>' for x in s['mistakes'])+'</ul>'
 body+='<h2>Read next</h2>'+para(', '.join('[['+x+'|'+titles[x]+']]' for x in s['links'])+'.')
 row=by['spring/if-match-receipt-write'].copy()
 row.update(id=str(uuid.uuid5(uuid.NAMESPACE_URL,'https://aitrove.in/'+p)),type='article',path=p,title=s['title'],summary=s['opening'],body=body,subject=s['subject'],difficulty='Intermediate',status='published',tags=['spring','spring-boot','migration' if 'flyway' in p or 'migration' in p else 'configuration'],featured=False,sort_order=900+len(rows),published_at=stamp,created_at=stamp,updated_at=stamp)
 row['data']={'subject_root':'spring/spring-boot','section_path':hub['path'],'kind':'tutorial','content_format':'html','reading_minutes':max(4,round(len(re.sub(r'<[^>]+>',' ',body).split())/150)),'author_path':'authors/aitrove-editorial','seo_ready':True,'related':[{'path':x,'title':titles[x]} for x in s['links']],'framework_version':'Spring Boot 4.0.8 / Spring Framework 7','java_version':'21 source-kit baseline','verification_suite':s['proof'],'download_path':'/downloads/aitrove-spring-source-kit.zip'}
 rows.append(row);by[p]=row

groups={
 'spring-boot':('Profiles, imports and effective sources',['spring/boot-profile-file-selection','spring/boot-required-config-import','spring/boot-optional-config-import','spring/boot-config-source-priority']),
 'spring-data':('Boot migration startup',['spring/boot-flyway-startup','spring/boot-flyway-version-step','spring/boot-flyway-history-failure']),
 'spring-testing':('Migration test classpath',['spring/boot-flyway-test-scope']),
 'spring-exercises':('Configuration and migration trace',['spring/boot-config-migration-trace']),
 'spring-projects':('Versioned receipt schema',['spring/boot-versioned-receipt-project']),
}
for subject,(title,paths) in groups.items():
 hub=next(r for r in rows if r['type']=='subject' and r['subject']==subject)
 hub['data']['modules'].append({'title':title,'summary':'Check selected settings and the staged database startup path.','lessons':paths});hub['updated_at']=stamp
 if '<h2>Section lessons</h2>' in hub['body']:
  links='<ul>'+''.join('<li><a href="/'+p+'">'+html.escape(titles[p])+'</a></li>' for m in hub['data']['modules'] for p in m['lessons'])+'</ul>'
  hub['body']=re.sub(r'(<h2>Section lessons</h2>)[\s\S]*?(<h2>Continue learning</h2>)',lambda m:m[1]+links+m[2],hub['body'])

reverse={
 'spring/flyway-boot-ownership':['spring/boot-flyway-startup','spring/boot-flyway-test-scope'],
 'spring/flyway-history-checksum':['spring/boot-flyway-history-failure'],
 'spring/flyway-expand-contract':['spring/boot-flyway-version-step'],
 'spring/boot-config-source-matrix':['spring/boot-profile-file-selection','spring/boot-config-source-priority'],
 'spring/boot-additional-config-file':['spring/boot-required-config-import','spring/boot-optional-config-import'],
 'spring/schema-rollout-tests':['spring/boot-flyway-version-step'],
 'spring/testing-boundaries':['spring/boot-flyway-test-scope'],
 'spring/receipt-api-project':['spring/boot-versioned-receipt-project'],
 'java/versioned-migrations':['spring/boot-flyway-startup'],
}
for p,targets in reverse.items():
 row=by[p];marker='<h2>Continue with checked Boot startup</h2>'
 row['body']=row['body'].split(marker)[0]+marker+para('Continue with '+', '.join('[['+x+'|'+titles[x]+']]' for x in targets)+'.');row['updated_at']=stamp

old=by['spring/flyway-boot-ownership']
old['body']=old['body'].replace('The downloadable kit declares flyway-core with test scope. FlywayReceiptMigrationTest creates a Flyway instance directly and applies its three test resources. ReceiptApplication does not enable a runtime migration path.','The downloadable kit now declares spring-boot-starter-flyway with test scope. FlywayReceiptMigrationTest creates a Flyway instance directly; BootFlywayStartupTest also checks a separate non-web Boot context. ReceiptApplication still does not enable a runtime migration path.')
old['body']=old['body'].replace('No Boot Flyway auto-configuration integration, production database module, concurrent-replica deployment job, readiness gate or target-engine migration is checked.','A separate non-web Boot auto-configuration test now checks local startup on H2. No production database module, concurrent-replica deployment job, readiness gate or target-engine migration is checked.')
old['body']=old['body'].replace('&lt;groupId&gt;org.flywaydb&lt;/groupId&gt;\n  &lt;artifactId&gt;flyway-core&lt;/artifactId&gt;','&lt;groupId&gt;org.springframework.boot&lt;/groupId&gt;\n  &lt;artifactId&gt;spring-boot-starter-flyway&lt;/artifactId&gt;')
old['body']=old['body'].replace('FlywayReceiptMigrationTest uses Flyway.configure() directly; ReceiptApplication does not run Flyway at startup.','FlywayReceiptMigrationTest uses Flyway.configure() directly; BootFlywayStartupTest checks a separate non-web Boot context. ReceiptApplication does not run Flyway at startup.')
old=by['spring/migration-runner-boundary']
old['body']=old['body'].replace('Target-database DDL, concurrent deployment, Boot startup integration and rollback remain untested.','Target-database DDL, concurrent deployment, ReceiptApplication runtime integration and rollback remain untested. A separate non-web Boot startup test covers the local H2 migration path.')
old['body']=old['body'].replace('The separate FlywayReceiptMigrationTest checks test-scoped Flyway execution and history.','FlywayReceiptMigrationTest checks direct test-scoped Flyway execution and history; BootFlywayStartupTest checks a separate Boot context.')
old=by['spring/boot-config-source-matrix']
old['body']=old['body'].replace('Host environment variables and mounted deployment files remain untested.','A selected review profile and missing required/optional imports are also checked. Host environment variables and mounted deployment files remain untested.')

quiz_path='quizzes/spring-boot-startup';assert quiz_path not in by
questions=[
('Which value binds when application-review.properties sets batch size 29 over base size 17?',['29','17','8'],0,'The active review profile overrides that key; the base file still supplies timeout.'),
('The review profile omits timeout. What does the checked bean report?',['750 milliseconds from the base file','No timeout bean','29 seconds'],0,'The profile file changes batch size only.'),
('What happens when a non-optional imported file is missing?',['Boot context startup fails','The import silently uses defaults','Flyway repairs the file'],0,'The required import test expects startup failure.'),
('What happens for the same missing file with optional: added?',['Startup continues using other sources','Startup always fails','The file is created'],0,'The checked optional import leaves the declared defaults in effect.'),
('Does an optional default value prove the imported file was read?',['No','Yes','Only for Duration'],0,'The fixture intentionally succeeds while the optional file is absent.'),
('A packaged DataSource URL and builder default URL disagree. Which URL did the first migration test open?',['The packaged application.properties URL','The unique builder default','A random PostgreSQL URL'],0,'The failed first fixture showed the builder default had lower priority.'),
('How does the corrected startup fixture select its unique H2 database?',['It passes the URL as a command-line property','It renames the packaged file','It reads a browser cookie'],0,'The CLI URL wins over the packaged setting in this checked context.'),
('Which component applies SQL when the non-web test Boot context starts?',['Boot Flyway auto-configuration','The direct API call from another test','ReceiptController'],0,'BootFlywayStartupTest uses a test-scoped starter and Boot startup.'),
('At target version 2, can the old writer omit tenant_id?',['Yes; the column is nullable','No; V3 already tightened it','Only after a checksum failure'],0,'The V2 stage accepts the old insert in the test.'),
('At target version 3, what happens to an old insert omitting tenant_id?',['It is rejected','It gets a trusted tenant automatically','It rewinds migration history'],0,'V3 backfills prior rows and sets NOT NULL for new writes.'),
('What does the checksum mismatch test do to the next Boot startup?',['It prevents a context from being returned','It rewrites history automatically','It silently skips V2'],0,'The test deliberately corrupts recorded V2 checksum and asserts startup failure.'),
('Does the runnable ReceiptApplication now execute Flyway on production startup?',['No; the starter and SQL are test-scoped','Yes; the non-web test is the runnable API','Yes; all H2 tests deploy migrations'],0,'Runtime migration ownership and target-engine rollout are still open.')]
q=by['quizzes/spring-core'].copy();q.update(id=str(uuid.uuid5(uuid.NAMESPACE_URL,'https://aitrove.in/'+quiz_path)),path=quiz_path,title='Spring Boot configuration and migration startup quiz',summary='Twelve explained checks on selected files, required imports and startup migrations.',sort_order=604,published_at=stamp,created_at=stamp,updated_at=stamp)
q['body']=para('A Spring self-check on profile selection, imported configuration and staged Flyway startup.')+'<h2>Review before answering</h2><ul>'+''.join('<li><a href="/'+p+'">'+html.escape(titles[p])+'</a></li>' for p in ['spring/boot-profile-file-selection','spring/boot-required-config-import','spring/boot-optional-config-import','spring/boot-config-source-priority','spring/boot-flyway-startup','spring/boot-flyway-version-step','spring/boot-flyway-history-failure'])+'</ul><h3>Common Mistakes</h3><ul><li>Do not read only the base file when a profile is active.</li><li>Do not confuse an optional fallback with a loaded import.</li><li>Do not present a test-scoped migration starter as runtime wiring.</li></ul>'
q['data']={'questions':[{'prompt':p,'options':o,'answer':a,'explanation':e} for p,o,a,e in questions],'duration_minutes':12,'subject_root':'spring/spring-boot','section_path':'spring/quizzes','content_format':'html','seo_ready':True}
rows.append(q);by[quiz_path]=q
hub=by['spring/quizzes'];hub['data']['modules'].append({'title':'Boot startup and migration','summary':'Twelve explained questions on selected config and versioned startup.','lessons':[quiz_path]});hub['updated_at']=stamp
if '<h2>Section lessons</h2>' in hub['body']:
 links='<ul>'+''.join('<li><a href="/'+p+'">'+html.escape(by[p]['title'])+'</a></li>' for m in hub['data']['modules'] for p in m['lessons'])+'</ul>'
 hub['body']=re.sub(r'(<h2>Section lessons</h2>)[\s\S]*?(<h2>Continue learning</h2>)',lambda m:m[1]+links+m[2],hub['body'])
FILE.write_text(json.dumps(rows,ensure_ascii=False,indent=2)+'\n')
print(json.dumps({'newArticles':[s['path'] for s in specs],'quiz':quiz_path,'quizQuestions':len(questions)}))
