"""Add original, test-bounded Spring configuration and Flyway lessons."""
from __future__ import annotations
import datetime, html, json, pathlib, re, uuid
ROOT=pathlib.Path(__file__).resolve().parents[1]
FILE=ROOT/'src/data/fixtures.json'
rows=json.loads(FILE.read_text()); by_path={r['path']:r for r in rows}
stamp=datetime.datetime.now(datetime.UTC).isoformat(); specs=[]

def add(subject,slug,title,opening,sections,code,language,proof,limits,mistakes,links):
 specs.append(dict(subject=subject,path='spring/'+slug,title=title,opening=opening,sections=sections,code=code,language=language,proof=proof,limits=limits,mistakes=mistakes,links=links))

add('spring-boot','boot-additional-config-file','Spring Boot external config file: bind the value the process actually loads',
'An additional configuration location adds a properties file to Spring Boot startup before a typed configuration bean is bound.',[
('Load a real file',[
'BootRelaySettingsTest writes application.properties into a JUnit temporary directory. It starts a non-web SpringApplication context with spring.config.additional-location set to that directory URI. The file supplies relay.batch-size=17 and relay.timeout=750ms; the bound RelaySettings record reports those values instead of the programmatic defaults of 8 and 2s. This is a real file read, not a MapPropertySource inserted after startup.',
'Boot resolves additional locations early. A directory URI needs its trailing separator so the loader can look for application.properties inside it. The test obtains that URI from Path.toUri rather than joining a platform-specific path string. [[spring/boot-config-source-matrix|The source matrix]] now has a checked file row, but a mounted volume with different permissions still needs a deployment test.' ]),
('Keep the file operationally boring',[
'Store only non-secret relay settings in the example file. A mounted secret needs access controls, rotation and an error policy that does not print its value. Treat a missing additional location as a startup or rollout decision; do not silently assume the intended file was read just because the application starts with defaults.',
'The [[spring/boot-startup-validation|startup validator]] checks value ranges after binding. It cannot tell whether a plausible value came from the intended source. An effective-settings diagnostic can report selected non-secret values and their origins to operators, while omitting credentials.'])],
'''Files.writeString(configDirectory.resolve("application.properties"),
    "relay.batch-size=17\\nrelay.timeout=750ms\\n");
try (var context = app().run(
    "--spring.config.additional-location=" + configDirectory.toUri())) {
    assertEquals(17, context.getBean(RelaySettings.class).batchSize());
}''','java',
'BootRelaySettingsTest.additionalPropertiesFileOverridesPackagedDefaults',
'The test uses one local temporary file and one process. It does not exercise containers, permissions on a production mount, a remote secret store or profile-specific file selection.',
['Do not append a filename where Boot expects a directory location.','Do not infer that a missing config file was loaded from a plausible default value.','Do not log credentials while reporting effective settings.'],
['spring/boot-config-precedence-file-cli','spring/boot-external-config-validation','spring/boot-config-source-matrix','spring/configuration-properties'])

add('spring-boot','boot-config-precedence-file-cli','Spring Boot file versus command line: assert the bound result',
'When a command-line argument and an additional properties file set the same key, the effective value reaches the bound bean from the command line in this fixture.',[
('The collision test',[
'The temporary file sets relay.batch-size=17 and relay.timeout=750ms. The application starts with --relay.batch-size=23. BootRelaySettingsTest asserts batchSize 23 and timeout 750 milliseconds on RelaySettings. Checking both fields matters: a mistaken global replacement could make the first assertion pass while discarding the file entirely.',
'This proves the ordering of the two sources in the checked Boot 4.0.8 startup path. It does not establish the ordering of every environment variable, imported location or platform secret. [[spring/boot-additional-config-file|The file-only test]] isolates loading. [[spring/boot-command-line-precedence|The default-versus-CLI test]] isolates the older, narrower collision.' ]),
('Report the effective value',[
'A runbook that lists a value in application.properties but ignores launch arguments can describe the wrong worker capacity. Read the bound settings at startup or through a protected diagnostic endpoint. Redact secrets and retain the property origin only where operators need it.',
'For a poller, changing batch size changes database query work, heap allocation and per-tick duration. That is an operational choice, not only a syntax question. [[spring/poller-batch-limit|The polling budget]] explains the load consequence.'])],
'''try (var context = app().run(
    "--spring.config.additional-location=" + configDirectory.toUri(),
    "--relay.batch-size=23")) {
    var settings = context.getBean(RelaySettings.class);
    assertEquals(23, settings.batchSize());
    assertEquals(Duration.ofMillis(750), settings.timeout());
}''','java',
'BootRelaySettingsTest.commandLineOverridesAdditionalPropertiesFile',
'The test checks a local file and CLI against programmatic defaults. It does not set a real operating-system environment variable or exercise cloud configuration injection.',
['Do not compare only raw Environment strings when callers use typed configuration beans.','Do not assume one overridden key replaces every key from the file.','Do not promote a test batch size into a production capacity recommendation.'],
['spring/boot-additional-config-file','spring/boot-command-line-precedence','spring/poller-batch-limit','spring/boot-config-source-matrix'])

add('spring-boot','boot-external-config-validation','Spring Boot config validation: separate valid syntax from a safe relay setting',
'Configuration binding converts external text into a typed setting; validation then rejects a value outside the application contract.',[
('Two separate failures',[
'The RelaySettings record binds an int batchSize and a Duration timeout. Its batch size has a 1..100 constraint. A command-line value of zero causes context startup to fail; the test asserts failure rather than allowing a worker to run with no useful batch. A file containing 750ms binds Duration.ofMillis(750), which avoids an implicit unit guess.',
'The file tests check only accepted values. They do not yet test a corrupt file, a missing required key when a programmatic default is removed, an unknown property or a secret source outage. [[spring/boot-additional-config-file|File loading]] and [[spring/boot-config-precedence-file-cli|precedence]] happen before the final bean is judged.' ]),
('Treat a restart as a configuration change',[
'A 100-row upper bound is a validity guard, not a load-test result. The service can still overload a small database with a value inside the allowed range. Roll out a changed batch size with queue-age, connection-wait and tick-duration observations. If the value is rejected, the process should remain unready rather than starting a worker with a guessed fallback.',
'Config values must not appear in failure reports when they are credentials. Keep the typed bean small and avoid using a secret as an exception message. [[spring/readiness-health-group|Readiness checks]] apply once startup succeeds; they do not repair a failed bind.'])],
'''@Validated
@ConfigurationProperties("relay")
record RelaySettings(@Min(1) @Max(100) int batchSize,
                     @NotNull Duration timeout) { }
assertThrows(RuntimeException.class,
    () -> app().run("--relay.batch-size=0"));''','java',
'BootRelaySettingsTest.invalidEffectiveBatchSizePreventsStartup and additionalPropertiesFileOverridesPackagedDefaults',
'The fixture checks one invalid integer and explicit Duration units. It does not prove every configuration key, secret source, mount failure or operational capacity limit.',
['Do not confuse a parseable value with an acceptable operating point.','Do not silently replace an invalid operator value with a default.','Do not expose secret values in binding diagnostics.'],
['spring/boot-additional-config-file','spring/boot-startup-validation','spring/readiness-health-group','spring/boot-config-source-matrix'])

add('spring-data','flyway-versioned-receipts','Flyway SQL migrations: record ordered schema changes against a real database',
'A versioned Flyway migration applies a named SQL file once and records its outcome in a schema-history table.',[
('The checked sequence',[
'The source kit ships V1__create_receipts.sql, V2__expand_tenant.sql and V3__backfill_and_contract.sql under a test-only migration location. FlywayReceiptMigrationTest applies versions 1, 2 and 3 in separate steps against one H2 database. It asserts one executed migration at each step, three successful versioned history entries after version 3 and zero new executions on a second migrate call.',
'The test configures Flyway through its Java API. The dependency is test-scoped; the downloadable application does not run migrations on production startup. [[spring/migration-runner-boundary|The older runner-boundary lesson]] now points to this checked fixture. [[spring/flyway-boot-ownership|Boot integration]] remains an explicit deployment choice.' ]),
('Own the files, not just the final schema',[
'Changing a SQL file after it has been applied changes what the version claims to mean. Commit migration files with the application change and review the old application against every intermediate schema. A migration version is not a license to skip the compatibility interval.',
'The first file creates one receipt table and a seed row. That seed is fixture data, not a recommendation to store business seed records in every production migration. Keep a separate procedure for large data backfills and target-engine DDL planning.'])],
'''Flyway.configure().dataSource(source)
    .locations("classpath:db/relay-migration").target("2").load().migrate();
// The test then runs the old insert while tenant_id is nullable.''','java',
'FlywayReceiptMigrationTest.orderedFilesPreserveTheOldWriterUntilContract',
'Flyway runs through its Java API on H2 2.3.232. This is not a Spring Boot auto-configuration test or a deployment against PostgreSQL, MySQL or another production engine.',
['Do not call direct ALTER TABLE tests migration-history tests.','Do not edit an applied versioned file as a normal repair.','Do not place an unbounded production backfill in application startup.'],
['spring/flyway-expand-contract','spring/flyway-history-checksum','spring/flyway-boot-ownership','spring/migration-runner-boundary'])

add('spring-data','flyway-expand-contract','Flyway expand and contract: show exactly when an old writer breaks',
'An expand-and-contract rollout keeps old writes valid while a new nullable column is introduced, then rejects them only after the constraint is tightened.',[
('Version 2 is the overlap window',[
'V1 creates shipment_receipt with receipt_id and amount_minor. V2 adds nullable tenant_id. After Flyway applies V2, the test inserts receipt 102 without tenant_id; both the seed and new row have null tenant_id. That is intentional. The old writer still runs, so a new reader must not assume every historical row has an owner.',
'V3 assigns legacy to the null rows and then sets tenant_id NOT NULL. The test checks that no null rows remain, the old insert fails and a new insert with tenant_id=east succeeds. [[spring/schema-expand-column|The direct SQL expansion check]] and [[spring/schema-contract-gate|the constraint lesson]] explain each phase without migration tooling.' ]),
('The fixture is smaller than a deployment',[
'The test performs a backfill and NOT NULL alteration in one tiny H2 migration. A large production table may require resumable batches, index planning and an application release between backfill and constraint. New writers should deploy before V3 and old writers should retire before V3. The fixture checks SQL behavior, not that rollout timing.',
'When two application versions coexist, tenant-scoped reads need a policy for still-null rows. Guessing the tenant from a default can make authorization consistently wrong. [[spring/tenant-jdbc-predicate|The tenant predicate]] shows why ownership must be established before scoped queries trust it.'])],
'''-- V2__expand_tenant.sql
alter table shipment_receipt add column tenant_id varchar(40);
-- V3__backfill_and_contract.sql
update shipment_receipt set tenant_id = 'legacy' where tenant_id is null;
alter table shipment_receipt alter column tenant_id set not null;''','sql',
'FlywayReceiptMigrationTest.orderedFilesPreserveTheOldWriterUntilContract',
'Two rows and one H2 process do not measure lock time, batch cost, data ownership accuracy, mixed-version processes or recovery from an interrupted migration.',
['Do not require the new column in the same step that introduces it to an old writer.','Do not assign a guessed tenant to production records.','Do not infer target-engine DDL lock behavior from H2.'],
['spring/flyway-versioned-receipts','spring/schema-backfill-batch','spring/schema-contract-gate','spring/tenant-jdbc-predicate'])

add('spring-data','flyway-history-checksum','Flyway validation: detect a changed applied migration before another write',
'Flyway validation compares discovered migration definitions with the recorded history for already applied versions.',[
('The ordinary path',[
'After applying V1 through V3, the fixture counts three successful versioned history entries, reruns migrate and sees zero executed migrations, then calls validate without failure. The check is about history consistency, not business-row correctness. The receipt assertions separately prove that the column contract changed as expected.',
'A second test deliberately corrupts the recorded checksum for version 2 and expects FlywayValidateException. That is a controlled simulation of a history mismatch. It does not edit a committed migration file or show how an operator should repair a production history table. [[spring/flyway-versioned-receipts|The versioned-file lesson]] establishes the files being compared.' ]),
('Do not auto-repair uncertainty',[
'A mismatch is a reason to stop and inspect the deployed file, prior release artifact and schema state. Rewriting history to silence validation can hide drift. A failed non-transactional DDL step needs a database-specific recovery procedure, a reviewed forward migration or a restore decision.',
'The fixture is isolated H2 and has no concurrent migrators. It does not show a process crash between SQL statements, target-database transaction semantics or deployment locks. [[spring/schema-rollout-tests|The rollout matrix]] lists the untested states.'])],
'''migrationAt("3").migrate();
jdbc.update("update \"flyway_schema_history\" "
    + "set \"checksum\" = \"checksum\" + 1 where \"version\" = '2'");
assertThrows(FlywayValidateException.class,
    () -> migrationAt("3").validate());''','java',
'FlywayReceiptMigrationTest.changedRecordedChecksumFailsValidation',
'The test corrupts a checksum in an isolated H2 history table. It does not change a deployed SQL file, perform repair or prove crash recovery for DDL on another engine.',
['Do not treat a green row-count check as migration-history validation.','Do not change recorded checksums manually in a deployed database to clear an error.','Do not assume every database rolls back DDL on migration failure.'],
['spring/flyway-versioned-receipts','spring/flyway-boot-ownership','spring/schema-rollout-tests','spring/migration-runner-boundary'])

add('spring-boot','flyway-boot-ownership','Spring Boot and Flyway: choose who runs migrations before traffic starts',
'Spring Boot can invoke Flyway migrations during application startup when the runtime dependency and database are configured.',[
('What this kit actually does',[
'The downloadable kit declares flyway-core with test scope. FlywayReceiptMigrationTest creates a Flyway instance directly and applies its three test resources. ReceiptApplication does not enable a runtime migration path. The generated SQL files sit under db/relay-migration, away from Boot’s conventional db/migration path. This separation keeps a reader from mistaking a checked teaching fixture for a production rollout.',
'If an application startup owns migrations, coordinate concurrent replicas and readiness so none serves a schema it cannot read. If a deployment job owns them, make the job idempotent and gate the rollout on its result. Choose one owner. [[spring/flyway-versioned-receipts|The API test]] proves ordered local execution, not either deployment arrangement.' ]),
('Match dependency scope to ownership',[
'Moving Flyway to runtime and placing scripts in the configured location is a deliberate application change. The target database may need an additional Flyway database module. Run the exact scripts against a disposable instance of that engine before promotion. Test old and new application versions across V2; after V3 the old writer is intentionally incompatible.',
'Never start a long, unbounded data backfill on every replica. A migration tool records versions; it does not decide business ownership for historical rows or guarantee zero lock time. [[spring/flyway-expand-contract|The staged rollout]] names those decisions.'])],
'''<!-- The source kit keeps this test-only. Runtime rollout requires an owner. -->
<dependency>
  <groupId>org.flywaydb</groupId>
  <artifactId>flyway-core</artifactId>
  <scope>test</scope>
</dependency>''','xml',
'FlywayReceiptMigrationTest uses Flyway.configure() directly; ReceiptApplication does not run Flyway at startup',
'No Boot Flyway auto-configuration integration, production database module, concurrent-replica deployment job, readiness gate or target-engine migration is checked.',
['Do not call a test-scoped dependency production migration wiring.','Do not let both a job and every replica own the same rollout without a deliberate coordination plan.','Do not assume migration history proves the application can read all legacy rows.'],
['spring/flyway-versioned-receipts','spring/flyway-expand-contract','spring/dependency-readiness','spring/schema-rollout-tests'])

add('spring-exercises','flyway-config-release-trace','Spring exercise: predict file overrides and three migration versions',
'A release trace records the bound worker settings and the receipt writes that remain legal at each migration version.',[
('Settings trace',[
'Start with programmatic defaults batchSize=8 and timeout=2s. Add a file with batchSize=17 and timeout=750ms. The bound record becomes 17 and 750ms. Add the command-line argument --relay.batch-size=23. The bound record becomes 23 and 750ms. The two BootRelaySettingsTest file cases check those exact states. Replace the command-line value with zero and startup fails validation.',
'For each state, write the effective value, its source and whether a worker may start. Do not infer that an absent mounted file was read from the presence of an acceptable default. [[spring/boot-config-precedence-file-cli|The collision lesson]] explains the checked row.' ]),
('Database trace',[
'At V1, tenant_id does not exist. At V2, the old insert omitting tenant_id succeeds and leaves null. At V3, migration backfills existing null rows and requires tenant_id on future inserts. The old insert then fails; a new insert with east succeeds. Record the count of applied versions as 1, 2 and 3. A repeated migrate at V3 executes zero files.',
'Now change the recorded checksum for V2 in a disposable test database and run validate. Expect a validation exception before another release proceeds. Explain why rewriting history is not the repair plan. Run the named Maven tests and compare your trace with their assertions; the exercise has no hosted judge.'])],
'''mvn -q -Dtest=BootRelaySettingsTest,FlywayReceiptMigrationTest test''','bash',
'BootRelaySettingsTest and FlywayReceiptMigrationTest',
'The trace uses a local file and H2 migrations. It does not prove mounted-secret behavior, target-engine DDL, mixed-version deployment timing or recovery after a process kill.',
['Do not carry the file batch size through a later command-line override.','Do not expect an old writer to work after V3 requires tenant_id.','Do not describe a checksum mismatch as a row-data error.'],
['spring/boot-additional-config-file','spring/boot-config-precedence-file-cli','spring/flyway-expand-contract','spring/flyway-history-checksum'])

def para(value):
 escaped=html.escape(value)
 return '<p>'+re.sub(r'\[\[([^|]+)\|([^\]]+)\]\]',lambda m:'<a href="/'+m[1]+'">'+m[2]+'</a>',escaped)+'</p>'

titles={p:r['title'] for p,r in by_path.items()};titles.update({s['path']:s['title'] for s in specs})
for spec in specs:
 p=spec['path'];assert p not in by_path,p;assert all(x in titles for x in spec['links']),p
 hub=next(r for r in rows if r['type']=='subject' and r['subject']==spec['subject'])
 body=para(spec['opening'])
 for heading,paragraphs in spec['sections']:
  body+='<h2>'+html.escape(heading)+'</h2>'+''.join(para(x) for x in paragraphs)
 body+='<h2>Checked source</h2><pre><code class="language-'+spec['language']+'">'+html.escape(spec['code'].strip(),quote=False)+'</code></pre>'
 body+='<h2>Verification boundary</h2>'+para(spec['proof']+'. The excerpt is shortened or a labelled design sketch; the kit contains the checked tests.')
 body+='<h2>Costs and limits</h2>'+para(spec['limits'])
 body+='<h3>Common Mistakes</h3><ul>'+''.join('<li>'+html.escape(x)+'</li>' for x in spec['mistakes'])+'</ul>'
 body+='<h2>Read next</h2>'+para(', '.join('[['+x+'|'+titles[x]+']]' for x in spec['links'])+'.')
 row=by_path['spring/if-match-receipt-write'].copy()
 row.update(id=str(uuid.uuid5(uuid.NAMESPACE_URL,'https://aitrove.in/'+p)),type='article',path=p,title=spec['title'],summary=spec['opening'],body=body,subject=spec['subject'],difficulty='Intermediate',status='published',tags=['spring','spring-boot','configuration' if spec['subject']=='spring-boot' else 'migration'],featured=False,sort_order=900+len(rows),published_at=stamp,created_at=stamp,updated_at=stamp)
 row['data']={'subject_root':'spring/spring-boot','section_path':hub['path'],'kind':'tutorial','content_format':'html','reading_minutes':max(4,round(len(re.sub(r'<[^>]+>',' ',body).split())/150)),'author_path':'authors/aitrove-editorial','seo_ready':True,'related':[{'path':x,'title':titles[x]} for x in spec['links']],'framework_version':'Spring Boot 4.0.8 / Spring Framework 7','java_version':'21 source-kit baseline','verification_suite':spec['proof'],'download_path':'/downloads/aitrove-spring-source-kit.zip'}
 rows.append(row);by_path[p]=row

groups={
 'spring-boot':('External files and migration ownership',['spring/boot-additional-config-file','spring/boot-config-precedence-file-cli','spring/boot-external-config-validation','spring/flyway-boot-ownership']),
 'spring-data':('Versioned receipt migrations',['spring/flyway-versioned-receipts','spring/flyway-expand-contract','spring/flyway-history-checksum']),
 'spring-exercises':('Settings and migration release trace',['spring/flyway-config-release-trace']),
}
for subject,(title,paths) in groups.items():
 hub=next(r for r in rows if r['type']=='subject' and r['subject']==subject)
 hub['data']['modules'].append({'title':title,'summary':'Check loaded settings and the receipt migration sequence.','lessons':paths});hub['updated_at']=stamp
 if '<h2>Section lessons</h2>' in hub['body']:
  links='<ul>'+''.join('<li><a href="/'+p+'">'+html.escape(titles[p])+'</a></li>' for module in hub['data']['modules'] for p in module['lessons'])+'</ul>'
  hub['body']=re.sub(r'(<h2>Section lessons</h2>)[\s\S]*?(<h2>Continue learning</h2>)',lambda m:m[1]+links+m[2],hub['body'])

reverse={
 'spring/boot-config-source-matrix':['spring/boot-additional-config-file','spring/boot-config-precedence-file-cli'],
 'spring/configuration-properties':['spring/boot-external-config-validation'],
 'spring/migration-runner-boundary':['spring/flyway-versioned-receipts','spring/flyway-history-checksum'],
 'spring/schema-rollout-tests':['spring/flyway-expand-contract'],
 'spring/schema-expand-column':['spring/flyway-expand-contract'],
 'spring/boot-command-line-precedence':['spring/boot-config-precedence-file-cli'],
 'spring/dependency-readiness':['spring/flyway-boot-ownership'],
 'java/versioned-migrations':['spring/flyway-versioned-receipts'],
}
for p,targets in reverse.items():
 row=by_path[p];marker='<h2>Checked file and migration continuation</h2>'
 row['body']=row['body'].split(marker)[0]+marker+para('Continue with '+', '.join('[['+x+'|'+titles[x]+']]' for x in targets)+'.');row['updated_at']=stamp

# Replace superseded claims in the older pages, preserving their original boundaries.
old=by_path['spring/boot-config-source-matrix']
old['body']=old['body'].replace('Neither sets a real process environment variable or reads a mounted config file.','The newer BootRelaySettingsTest also reads a real local temporary application.properties file. No test sets a real process environment variable or reads a deployment-mounted config file.')
old['body']=old['body'].replace('Only a manual two-source override and a Boot default/CLI override are checked today.','A manual two-source override, Boot default/CLI override, local additional file and file/CLI collision are checked. Host environment variables and mounted deployment files remain untested.')
old=by_path['spring/boot-command-line-precedence']
old['body']=old['body'].replace('It does not load an application.properties file or control the host environment.','Separate tests now load a temporary application.properties file and check its collision with the CLI. This particular assertion does not control the host environment.')
old=by_path['spring/migration-runner-boundary']
old['body']=old['body'].replace('It does not include Flyway, Liquibase, a schema history table, checksums, repair policy or migration-on-startup wiring. Do not describe it as a Flyway test.','A separate FlywayReceiptMigrationTest now executes three test-only versioned SQL files, records history and checks validation. SchemaEvolutionContractTest remains direct SQL; no runtime migration-on-startup wiring, target-engine test or repair policy is included.')
old['body']=old['body'].replace('// Not executed by this kit:','// The following names are a sketch; checked files are under db/relay-migration:')
old['body']=old['body'].replace('SchemaEvolutionContractTest checks direct H2 SQL only; no migration runner test exists.','SchemaEvolutionContractTest checks direct H2 SQL. The separate FlywayReceiptMigrationTest checks test-scoped Flyway execution and history.')
old['body']=old['body'].replace('Migration history, checksums, target-database DDL behavior, concurrent deployment and rollback are not checked. The file names above are a design sketch, not shipped scripts.','Migration history and checksum validation are now checked in a separate H2 fixture. Target-database DDL, concurrent deployment, Boot startup integration and rollback remain untested. The names above are a sketch; the actual test files have different names.')
old=by_path['spring/schema-rollout-tests']
old['body']=old['body'].replace('Do not infer Flyway checksum or migration-history behavior from these direct JdbcTemplate tests.','Do not infer Flyway history behavior from the direct JdbcTemplate tests; a separate FlywayReceiptMigrationTest now checks it on H2.')
old['body']=old['body'].replace('No migration tool, target database, mixed-version process pair, realistic table volume or crash/restart flow is checked.','A separate test-scoped Flyway fixture checks ordered files on H2. No target database, mixed-version process pair, realistic table volume or crash/restart flow is checked.')
quiz=by_path['quizzes/spring-operations']
for q in quiz['data']['questions']:
 if q['prompt'].startswith('Does the config fixture prove actual environment-variable precedence?'):
  q['options'][0]='No; it checks defaults, CLI and a local file, but no process environment variable'
  q['explanation']='The kit now checks a temporary application.properties file and a file/CLI collision, but does not set a real process environment variable.'
 if q['prompt'].startswith('Does SchemaEvolutionContractTest execute Flyway migrations?'):
  q['explanation']='That named test still uses direct H2 SQL. The separate FlywayReceiptMigrationTest executes versioned files.'
  q['options'][0]='No; that test uses direct H2 SQL, while a separate test runs Flyway'
quiz['body']=quiz['body'].replace('Do not describe direct H2 SQL as a migration-runner test.','Keep the direct SQL test separate from the newer Flyway migration test.')
quiz['updated_at']=stamp

questions=[
 ('A temporary application.properties sets batch size 17 over a programmatic default of 8. What binds in the checked context?',['17','8','Both as a list'],0,'BootRelaySettingsTest loads the file through an additional location before binding the record.'),
 ('The file sets batch size 17 and the CLI sets 23. What value does RelaySettings report?',['23','17','8'],0,'The checked CLI/file collision leaves 23 as the effective batch size.'),
 ('The file also sets timeout 750ms while the CLI changes only batch size. What timeout binds?',['750 milliseconds','2 seconds','23 milliseconds'],0,'An override for one key does not erase the other file-backed key.'),
 ('Which source is not exercised as an actual process source by these tests?',['Operating-system environment variable','Local temporary properties file','Command-line argument'],0,'The kit has no real environment-variable setup in its Boot startup fixture.'),
 ('What does a successful bind of batch size 100 establish?',['Only that it passes the declared range; capacity still needs measurement','That any database can handle 100 rows per tick','That a missing file was loaded'],0,'Range validation is distinct from a throughput or origin check.'),
 ('At Flyway V2, what does the old receipt writer do?',['It inserts a row with null tenant_id','It fails because tenant_id is required','It rewrites V1 history'],0,'V2 adds the column as nullable and the test inserts receipt 102 with the old shape.'),
 ('At Flyway V3, what happens to the old writer?',['Its insert fails the NOT NULL constraint','It silently gets tenant_id east','It drops the table'],0,'The test backfills old rows, tightens the column, then asserts old-shape rejection.'),
 ('How many migrations execute on a second migrate call after V3?',['Zero','Three','One'],0,'Flyway history records all three applied versions; the rerun executes none.'),
 ('What does the isolated checksum-corruption test expect from validate?',['FlywayValidateException','A new migration version','Automatic history repair'],0,'Changing the recorded V2 checksum creates a validation mismatch in the test database.'),
 ('Does the downloadable application run these Flyway files at production startup?',['No; Flyway is test-scoped and the test calls its API','Yes; every replica runs V3 on launch','Only when a CLI batch size is set'],0,'The kit has no runtime Flyway integration or deployment owner.'),
 ('Which release concern remains open after the H2 test?',['Target-engine DDL locks and mixed-version timing','Whether V2 has a nullable tenant column','Whether history records three successes'],0,'The local fixture proves narrow H2 behavior and has no production-engine or concurrent-release exercise.'),
 ('What should an operator do after a migration checksum mismatch?',['Stop and inspect the artifact and schema before choosing a reviewed repair','Edit the history row until validation passes','Ignore it if the newest application starts'],0,'A mismatch is evidence of drift, not a reason to suppress the validation gate.'),
]
quiz['data']['questions'] += [{'prompt':p,'options':o,'answer':a,'explanation':e} for p,o,a,e in questions]
quiz['summary']='Twenty-four explained checks on configuration files, effective settings and versioned schema changes.'
quiz['body']=quiz['body'].replace('<h3>Common Mistakes</h3>','<h2>File and migration checks</h2><ul>'+''.join('<li><a href="/'+p+'">'+html.escape(titles[p])+'</a></li>' for p in ['spring/boot-additional-config-file','spring/boot-config-precedence-file-cli','spring/flyway-versioned-receipts','spring/flyway-expand-contract','spring/flyway-history-checksum'])+'</ul><h3>Common Mistakes</h3>')
FILE.write_text(json.dumps(rows,ensure_ascii=False,indent=2)+'\n')
print(json.dumps({'articles':[s['path'] for s in specs],'quiz':quiz['path'],'quizQuestions':len(quiz['data']['questions'])}))
