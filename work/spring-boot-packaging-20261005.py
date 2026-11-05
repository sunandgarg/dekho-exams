"""Add original Spring Boot startup and packaging lessons to local fixtures."""
import copy
import datetime
import html
import json
import pathlib
import re
import uuid

root = pathlib.Path(__file__).resolve().parents[1]
fixture = root / 'src/data/fixtures.json'
rows = json.loads(fixture.read_text())
by_path = {row['path']: row for row in rows}
stamp = datetime.datetime.now(datetime.UTC).isoformat()


def prose(value):
    return re.sub(r'\[\[([^|]+)\|([^\]]+)\]',
                  lambda match: '<a href="/' + match[1] + '">' + match[2] + '</a>',
                  html.escape(value))


lessons = [
    dict(slug='boot-failure-analyzer-action', title='Spring Boot FailureAnalyzer: turn one startup exception into an actionable failure',
         summary='A FailureAnalyzer recognizes a specific startup exception and supplies a focused description and repair action without swallowing the failure.',
         blocks=[
             ('Analyze one failure family', 'A receipt service refuses to start when its ledger schema version is unsupported. A custom analyzer can recognize that domain exception and name the incompatible version in the startup report. It must return null for unrelated failures so another analyzer or the original stack trace can handle them. The analyzer changes diagnosis, not the process outcome. [[spring/boot-startup-validation|Startup validation]] still prevents an unsafe service from accepting traffic.'),
             ('Register before the context exists', 'A startup failure may occur before ordinary beans are available, so registering the analyzer as an application bean is not a safe discovery strategy. Package its implementation name under the FailureAnalyzer key in META-INF/spring.factories. Keep its constructor light; avoid database queries, secrets and network calls inside error reporting. If the exception contains a password or connection string, redact that information before creating the description. [[spring/boot-condition-report-diagnosis|The condition report]] is better for missing auto-configuration than a domain-specific analyzer.'),
             ('Prove both branches', 'Start a small application with an unsupported ledger version and capture the failure report. Check that the report names the expected version and a precise repair step, then assert startup still exits unsuccessfully. Trigger an unrelated bean creation error and confirm this analyzer does not claim it. A diagnostic that turns every exception into a generic ledger message costs more time than it saves.')],
         code='final class LedgerVersionAnalyzer\n        extends AbstractFailureAnalyzer<UnsupportedLedgerVersionException> {\n    @Override protected FailureAnalysis analyze(\n            Throwable rootFailure, UnsupportedLedgerVersionException cause) {\n        return new FailureAnalysis(\n            "Receipt ledger schema " + cause.schemaVersion() + " is unsupported",\n            "Run the approved ledger migration before starting this service",\n            rootFailure);\n    }\n}',language='java',
         cost='An analyzer runs only on startup failure. Its operational cost is inaccurate advice or leaked secrets, not request latency.',
         mistakes=['Do not treat an analyzer as a recovery mechanism that permits unsafe startup.', 'Do not register it only as a normal application bean.', 'Do not echo credentials from the exception into the report.'],
         related=['spring/boot-startup-validation','spring/boot-condition-report-diagnosis','spring/boot-runner-startup-failure','spring/boot-exit-code-contract','spring/flyway-boot-ownership'],backlink='spring/boot-startup-validation'),
    dict(slug='boot-condition-report-diagnosis', title='Spring Boot condition report: locate the missing auto-configuration decision',
         summary='A condition report records why auto-configuration matched or backed off; inspect the exact condition before adding another bean or excluding a module.',
         blocks=[
             ('Read the decision chain', 'A receipt HTTP client is absent after deployment. The class might be missing, a required property might be false, or a user bean may have caused a conditional default to back off. The condition report shows positive and negative matches by configuration source. Find the failed condition for the expected auto-configuration class, then inspect the actual classpath and property value. [[spring/conditional-missing-bean-default|Missing-bean defaults]] and [[spring/conditional-property-opt-in|property opt-ins]] cover the two common decisions.'),
             ('Use a controlled diagnostic surface', 'Startup debug logging can print the report during local diagnosis. Actuator can expose a conditions endpoint when installed and enabled, but do not expose that endpoint on an unrestricted public management surface: it reveals class and configuration details. Capture only the relevant entry in an incident note. A missing bean error by itself does not prove that scanning failed; [[spring/component-scan-vs-bean|component scanning]] and auto-configuration are different paths.'),
             ('Compare before changing code', 'Run the same packaged artifact with the failing and healthy configuration, then compare the condition entry. Do not add an explicit bean solely to silence an exception until the reason for backoff is known. A targeted test should assert the intended bean is present when the opt-in property is true and absent when false. That proves the contract without depending on the entire text of a report, which can change across framework versions.')],
         code='Logger diagnosticLog = LoggerFactory.getLogger(ReceiptApplication.class);\nConditionEvaluationReport report =\n    ConditionEvaluationReport.get(context.getBeanFactory());\nreport.getConditionAndOutcomesBySource().entrySet().stream()\n    .filter(entry -> entry.getKey().contains("ReceiptClient"))\n    .forEach(entry -> diagnosticLog.info(\n        "{} -> {}", entry.getKey(), entry.getValue()));',language='java',
         cost='Report inspection is a diagnostic task, not a request path. Exposing it broadly increases information leakage; large reports can also be noisy without a named condition to inspect.',
         mistakes=['Do not infer a scan failure from every missing auto-configured bean.', 'Do not publish the conditions endpoint to anonymous clients.', 'Do not assert the full report text in a version-sensitive test.'],
         related=['spring/conditional-missing-bean-default','spring/conditional-property-opt-in','spring/component-scan-vs-bean','spring/auto-configuration','spring/boot-failure-analyzer-action'],backlink='spring/auto-configuration'),
    dict(slug='boot-properties-scan-boundary', title='Spring Boot configuration-property scanning: keep the package boundary explicit',
         summary='ConfigurationPropertiesScan discovers eligible property types in selected packages; a class outside that boundary will not become a bound bean by accident.',
         blocks=[
             ('Locate the scanned package', 'A receipt retry policy record lives in a library package while the application class sits under another root. A no-argument ConfigurationPropertiesScan scans from the annotated class package, so the library record may not be registered. Name a class in the library package through basePackageClasses or register the type explicitly with EnableConfigurationProperties. The class reference survives package renaming better than a string literal. [[spring/configuration-properties|Property binding]] then validates the values that reached the bean.'),
             ('Do not confuse two scanners', 'Component scanning finds component stereotypes. Configuration-property scanning finds eligible ConfigurationProperties classes but skips classes that are also components. Register a given configuration type through one clear path; duplicate registration can create confusing bean names and injection ambiguity. A third-party object that you cannot annotate may be bound through a ConfigurationProperties bean method. [[spring/component-scan-vs-bean|The component-scan boundary]] explains why importing a module does not automatically discover all its classes.'),
             ('Check the packaged module', 'A test in the application module may see the property record because test configuration imports it, while the final packaged service does not. Start the packaged application with a nondefault receipt retry count and assert the bound bean sees exactly that number. Then remove the required value and assert validation fails. That detects both an absent scan and an unintended fallback default.')],
         code='@SpringBootApplication\n@ConfigurationPropertiesScan(basePackageClasses = ReceiptRetryProperties.class)\nclass ReceiptApplication {}\n\n// ReceiptRetryProperties lives in the library package selected above.\n@ConfigurationProperties(prefix = "receipt.retry")\nrecord ReceiptRetryProperties(int maxAttempts, Duration backoff) {}',language='java',
         cost='Scanning a narrow package limits startup class inspection. The main risk is silent omission or duplicate registration, which a packaged-context test catches.',
         mistakes=['Do not assume the application root covers a sibling library package.', 'Do not annotate one properties type as both a scanned configuration type and a component without intent.', 'Do not rely on a test-only import to prove packaged discovery.'],
         related=['spring/configuration-properties','spring/component-scan-vs-bean','spring/boot-external-config-validation','spring/boot-startup-validation','spring/boot-condition-report-diagnosis'],backlink='spring/configuration-properties'),
    dict(slug='boot-layered-jar-image-cache', title='Spring Boot layered jar: keep dependency changes out of the application layer',
         summary='A layered executable jar separates dependencies and application bytes so image builders can reuse unchanged layers across deployments.',
         blocks=[
             ('Observe what changes', 'A receipt-service patch changes controller classes but leaves the framework libraries untouched. A layered Boot archive includes an index describing layers such as dependencies, snapshot dependencies, loader code and application code. An image build can place stable library bytes before the frequently changing application layer. This improves cache reuse for transfer and rebuilds; it does not make the running Java process faster by itself. [[spring/boot-executable-jar-classpath|The executable jar layout]] explains where the classes and nested libraries live.'),
             ('Keep the index honest', 'Inspect the packaged archive, not only the build script. A project dependency that changes on every build may land with application code, while a snapshot library can invalidate its own layer often. Custom layer rules should follow actual change frequency and must be checked after a dependency restructure. [[spring/boot-buildpack-build-run-config|A buildpack image]] can read the layer index, but its builder and run image versions also affect cache behavior.'),
             ('Measure the right cost', 'Build two images from the same dependency graph with only one receipt class changed. Compare layer digests, bytes pushed and deployment pull time. Then upgrade a dependency and confirm the appropriate library layer changes. A test that merely finds layers.idx proves the archive has metadata, not that the deployment pipeline actually reuses layers.')],
         code='jar tf target/receipt-service.jar | rg "BOOT-INF/(layers.idx|classes/|lib/)"\njava -Djarmode=tools -jar target/receipt-service.jar list-layers',language='bash',
         cost='Layer metadata is small. Image size may remain similar; the benefit is fewer changed bytes sent and stored when only application code changes.',
         mistakes=['Do not claim layering reduces runtime latency without measuring startup separately.', 'Do not infer cache reuse solely from the presence of layers.idx.', 'Do not place frequently changing generated files in a stable dependency layer.'],
         related=['spring/boot-executable-jar-classpath','spring/boot-buildpack-build-run-config','spring/application-startup-timeline','spring/boot-startup-validation','spring/boot-condition-report-diagnosis'],backlink='spring/application-startup-timeline'),
    dict(slug='boot-buildpack-build-run-config', title='Spring Boot buildpack image: separate build settings from deployed secrets',
         summary='Buildpack environment values shape the generated image; application credentials and deployment settings belong to the runtime environment.',
         blocks=[
             ('Two configuration moments', 'The receipt service image build chooses a JVM version and builder policy. The running container later receives a database address, credentials and pool limits for its deployment. Passing a secret as a build setting risks leaving it in build logs, layers or cached metadata. Treat the image as the reusable artifact and keep deployment-specific values outside it. [[spring/boot-configtree-file-binding|Config-tree binding]] can read a mounted secret at runtime.'),
             ('Pin the artifact', 'Record the builder image, run image, JDK version and resulting image digest with each release. A mutable tag may change the base image without a source change. Spring Boot’s image task delegates to buildpacks, so an application property does not set a buildpack parameter, and a buildpack JVM setting does not replace a Spring property at runtime. [[spring/boot-layered-jar-image-cache|Layered jar behavior]] affects how unchanged bytes may be reused.'),
             ('Test both environments', 'Build the image with a controlled JVM version, then run that exact digest with a disposable database and injected runtime configuration. Assert the process starts and binds a known non-secret property. Rebuild after changing only a runtime value: the image digest should remain the same because no rebuild is needed. A deployment test should also confirm missing credentials fail before accepting traffic.')],
         code='tasks.named<BootBuildImage>("bootBuildImage") {\n    environment.put("BP_JVM_VERSION", "21")\n}\n// Supply receipt database credentials when the image is run, not here.',language='kotlin',
         cost='Building images consumes CPU, network and registry storage. Keeping runtime configuration out of the image permits one digest to serve several environments and avoids needless rebuilds.',
         mistakes=['Do not place database passwords in buildpack environment settings.', 'Do not assume a mutable builder tag reproduces the same image later.', 'Do not rebuild an image just to change one runtime property.'],
         related=['spring/boot-layered-jar-image-cache','spring/boot-configtree-file-binding','spring/boot-external-config-validation','spring/boot-executable-jar-classpath','spring/boot-startup-validation'],backlink='spring/boot-configtree-file-binding'),
    dict(slug='boot-executable-jar-classpath', title='Spring Boot executable jar: load resources through the classpath, not a file path',
         summary='Boot places application classes and resources inside an executable archive; code that assumes every classpath resource is a normal file can fail after packaging.',
         blocks=[
             ('The archive is a different filesystem view', 'A receipt rules document under application resources may be a visible file in an IDE and an entry inside the packaged jar in production. Calling getFile on a classpath resource assumes an ordinary filesystem path. Use getResourceAsStream or Spring Resource input streams for read-only content, and copy to a managed temporary path only when a third-party library strictly requires a File. [[spring/boot-layered-jar-image-cache|Layering]] changes image construction, not this resource-access contract.'),
             ('Do not write back into the jar', 'An executable archive is a deployable artifact. Generated reports, uploaded receipts and caches need explicit external storage. A relative working-directory path can change between an IDE, a container and a service manager; bind a writable location through validated configuration. Check permissions, quota and cleanup. [[spring/boot-external-config-validation|External config validation]] can reject a missing output directory at startup.'),
             ('Run the packaged artifact', 'Package the app and invoke the exact executable archive used for deployment. Read a small rules resource, then run the same feature from an IDE. Assert identical parsed values. If a dependency uses system class loading or demands a real file, exercise that integration under java -jar before release rather than trusting a unit test classpath.')],
         code='try (InputStream rules = ReceiptApplication.class\n        .getResourceAsStream("/receipt-rules.json")) {\n    if (rules == null) throw new IllegalStateException("Receipt rules missing");\n    receiptRules = objectMapper.readValue(rules, ReceiptRules.class);\n}',language='java',
         cost='Stream access reads only the requested bytes. Copying large bundled assets to a temporary directory adds startup I/O and storage pressure; avoid it unless the library requires a real file.',
         mistakes=['Do not call getFile on every classpath resource.', 'Do not attempt to write generated receipts into the executable jar.', 'Do not rely only on IDE execution to validate resource loading.'],
         related=['spring/boot-layered-jar-image-cache','spring/boot-buildpack-build-run-config','spring/boot-external-config-validation','spring/boot-startup-validation','spring/application-startup-timeline'],backlink='spring/boot-startup-validation'),
    dict(slug='boot-exit-code-contract', title='Spring Boot process exit codes: make job failure visible to the scheduler',
         summary='A command-line Boot process can return a nonzero exit code for a failed business run, allowing its scheduler to distinguish failure from a clean stop.',
         blocks=[
             ('Map outcome to process status', 'A nightly receipt settlement may finish its Java main method even though the imported job failed. A zero process exit then tells the scheduler the run succeeded. Implement ExitCodeGenerator for the final business outcome and pass SpringApplication.exit’s result to System.exit in a one-shot process. A long-running HTTP service usually should not exit after a single request failure. [[spring/batch-flow-exitstatus-restart|Batch flow status]] determines which job result should be mapped.'),
             ('Avoid a false success', 'If a runner throws before normal shutdown, a domain exception can also carry an exit code. Test both a normal completed job and a failed job after the context closes. Several generators may exist; establish their ordering or consolidate the policy so a later nonzero code does not surprise operators. Keep the mapping small and documented in the scheduler configuration. [[spring/boot-runner-startup-failure|Runner failures]] are startup failures, not ordinary request errors.'),
             ('Exercise the real shell contract', 'Launch the packaged artifact as a subprocess against a disposable input manifest. Check its numeric exit status and durable result rows. A mocked ExitCodeGenerator test can prove one method returns 47, but not that main actually passes the value to the operating system. For a retryable failure, reconcile committed chunks before the scheduler launches the same job identity again.')],
         code='final class SettlementExitCode implements ExitCodeGenerator {\n    private final SettlementResult result;\n    SettlementExitCode(SettlementResult result) { this.result = result; }\n    @Override public int getExitCode() {\n        return result.failed() ? 47 : 0;\n    }\n}\n// In the one-shot main method:\nSystem.exit(SpringApplication.exit(SpringApplication.run(ReceiptBatchApp.class, args)));',language='java',
         cost='Exit-code calculation is negligible. A wrong mapping can cause an unattended scheduler to skip a failed run or retry an already completed one.',
         mistakes=['Do not return zero after a failed batch execution.', 'Do not terminate a long-running web server for one request error.', 'Do not test only the generator while leaving the main method’s process exit unverified.'],
         related=['spring/batch-flow-exitstatus-restart','spring/boot-runner-startup-failure','spring/batch-job-identity','spring/batch-running-execution-recovery','spring/boot-failure-analyzer-action'],backlink='spring/boot-runner-startup-failure'),
    dict(slug='boot-devtools-restart-boundary', title='Spring Boot DevTools restart: reproduce classloader failures without it',
         summary='DevTools restart uses development class loading and is normally absent from a packaged production archive; test suspected classloader defects under the final jar.',
         blocks=[
             ('Development has another loader', 'A receipt serializer is loaded from a project module while its dependency remains in a stable library loader. DevTools restart can replace application classes after a change without restarting the full JVM. That saves local feedback time, but static caches, custom reflection or serialization may expose classloader mismatches. A failure seen only after several IDE restarts should be reproduced once with restart disabled and once with the executable archive. [[spring/boot-executable-jar-classpath|Packaged classpath behavior]] is the deployment reference.'),
             ('Keep it out of deployment', 'Declare DevTools as a development-only dependency. Boot’s packaged archives exclude it by default, but inspect the final jar rather than assuming a build customization preserved that rule. Never force restart support on in production to fix a missing bean. That hides the real startup problem and adds a development tool to a sensitive environment. [[spring/boot-condition-report-diagnosis|The condition report]] can explain a missing bean directly.'),
             ('Diagnose the actual class', 'Log both a class name and its defining classloader for the two objects involved in a cast failure; avoid logging payloads or credentials. Recreate the issue with a controlled classpath update, then restart disabled. If only DevTools fails, adjust local module loading or static cache ownership. If the packaged jar fails too, fix the underlying integration rather than a development restart setting.')],
         code='dependencies {\n    developmentOnly("org.springframework.boot:spring-boot-devtools")\n}\n\n// For one local diagnostic run, disable restart as a JVM property:\n// -Dspring.devtools.restart.enabled=false',language='kotlin',
         cost='Restart improves local iteration but holds two classloaders and can retain stale references in badly scoped static caches. Packaged production startup remains the release check.',
         mistakes=['Do not force DevTools restart on in a production process.', 'Do not blame every packaged startup error on the development loader.', 'Do not rely on IDE restart as the only launch-mode test.'],
         related=['spring/boot-executable-jar-classpath','spring/boot-condition-report-diagnosis','spring/boot-startup-validation','spring/boot-layered-jar-image-cache','spring/auto-configuration'],backlink='spring/boot-executable-jar-classpath'),
    dict(slug='boot-context-initializer-boundary', title='Spring Boot context initializer: make pre-refresh customization narrow',
         summary='An ApplicationContextInitializer runs before bean definitions load; it is suitable for early context setup, not normal service construction.',
         blocks=[
             ('Use the early hook deliberately', 'A host application embeds the receipt module and needs to attach one context identifier before configuration classes are parsed. A SpringApplication initializer receives the ConfigurableApplicationContext before refresh and can set that early value. Ordinary services should still be declared as components or beans, so their dependencies, conditions and lifecycle remain visible to the container. [[spring/application-context|ApplicationContext ownership]] provides the baseline.'),
             ('Know what is unavailable', 'The initializer does not have a fully refreshed context. Do not call getBean for a service that has not been constructed, start a scheduler or open a database connection from the hook. Register the initializer programmatically before run for one application, or through an explicit library registration when every consuming app needs it. [[spring/beanfactorypostprocessor-definition-phase|BeanFactoryPostProcessor]] is a later mechanism for editing definitions; [[spring/beanpostprocessor-early-beans|BeanPostProcessor]] operates on bean instances.'),
             ('Prove ordering and absence', 'Start the same application with and without the initializer. Assert the context identifier is visible during configuration loading, while normal beans are created once and shut down normally. A test that registers the initializer after run cannot prove anything: the context has already passed that phase. Keep the early value non-secret if it may enter logs or diagnostic names.')],
         code='// In main(String[] args):\nString deploymentSlot = System.getenv().getOrDefault("DEPLOYMENT_SLOT", "local");\nSpringApplication receiptApplication = new SpringApplication(ReceiptApplication.class);\nreceiptApplication.addInitializers(context ->\n    context.setId("receipt-service-" + deploymentSlot));\nConfigurableApplicationContext runningContext = receiptApplication.run(args);',language='java',
         cost='The hook runs once per context start. Long or blocking work here delays readiness and makes startup failures harder to attribute.',
         mistakes=['Do not request application service beans before context refresh.', 'Do not register the initializer after the application has run.', 'Do not use an initializer for ordinary constructor-injected services.'],
         related=['spring/application-context','spring/beanfactorypostprocessor-definition-phase','spring/beanpostprocessor-early-beans','spring/boot-startup-validation','spring/boot-failure-analyzer-action'],backlink='spring/application-context'),
]

titles = {path: row['title'] for path, row in by_path.items()}
titles.update({'spring/' + lesson['slug']: lesson['title'] for lesson in lessons})
for number, lesson in enumerate(lessons):
    path = 'spring/' + lesson['slug']
    assert path not in by_path, path
    for target in lesson['related']:
        assert target in titles, (path, target)
    body = '<p>' + prose(lesson['summary']) + '</p>'
    for heading, content in lesson['blocks']:
        body += '<h2>' + html.escape(heading) + '</h2><p>' + prose(content) + '</p>'
    body += '<h2>Implementation contract</h2><pre><code class="language-' + lesson['language'] + '">' + html.escape(lesson['code'], quote=False) + '</code></pre>'
    body += '<h2>Cost and verification</h2><p>' + prose(lesson['cost']) + '</p>'
    body += '<h3>Common Mistakes</h3><ul>' + ''.join('<li>' + prose(mistake) + '</li>' for mistake in lesson['mistakes']) + '</ul>'
    body += '<h2>Read next</h2><p>' + ', '.join('<a href="/' + target + '">' + html.escape(titles[target]) + '</a>' for target in lesson['related']) + '.</p>'
    row = copy.deepcopy(by_path['spring/component-scan-vs-bean'])
    row.update(id=str(uuid.uuid5(uuid.NAMESPACE_URL, 'https://aitrove.in/' + path)), path=path, title=lesson['title'], summary=lesson['summary'], body=body, subject='spring-boot', tags=['spring', 'spring-boot', lesson['slug']], sort_order=6800 + number, published_at=stamp, created_at=stamp, updated_at=stamp)
    row['data'] = {'subject_root': 'spring/spring-boot', 'section_path': 'spring/spring-boot', 'kind': 'tutorial', 'content_format': 'html', 'seo_ready': True, 'reading_minutes': max(4, round(len(re.sub(r'<[^>]+>', ' ', body).split()) / 150)), 'author_path': 'authors/aitrove-editorial', 'framework_version': 'Spring Boot 4 / Spring Framework 7 where relevant', 'java_version': '21 or later', 'verification_suite': 'Spring Boot API contract review; snippets require an application-specific model', 'related': [{'path': target, 'title': titles[target]} for target in lesson['related']]}
    rows.append(row)
    by_path[path] = row

new_paths = ['spring/' + lesson['slug'] for lesson in lessons]
hub = by_path['spring/spring-boot']
hub['data']['modules'].append({'title': 'Startup diagnostics and packaging boundaries', 'summary': 'Failure reports, property discovery, jar layout, image settings, exit codes and pre-refresh hooks.', 'lessons': new_paths})
hub['body'] += '<h2>Startup diagnostics and packaging boundaries</h2><ul>' + ''.join('<li><a href="/' + path + '">' + html.escape(titles[path]) + '</a></li>' for path in new_paths) + '</ul>'
hub['updated_at'] = stamp
for lesson in lessons:
    target = 'spring/' + lesson['slug']
    entry = by_path[lesson['backlink']]
    entry['body'] += '<h2>Related Boot contract</h2><p><a href="/' + target + '">' + html.escape(titles[target]) + '</a>.</p>'
    entry['updated_at'] = stamp
for source, target in [
    ('spring/boot-runner-startup-failure', 'spring/boot-failure-analyzer-action'),
    ('spring/conditional-missing-bean-default', 'spring/boot-condition-report-diagnosis'),
    ('spring/component-scan-vs-bean', 'spring/boot-properties-scan-boundary'),
    ('spring/boot-executable-jar-classpath', 'spring/boot-layered-jar-image-cache'),
    ('spring/boot-external-config-validation', 'spring/boot-buildpack-build-run-config'),
    ('spring/boot-buildpack-build-run-config', 'spring/boot-executable-jar-classpath'),
    ('spring/batch-flow-exitstatus-restart', 'spring/boot-exit-code-contract'),
    ('spring/boot-layered-jar-image-cache', 'spring/boot-devtools-restart-boundary'),
    ('spring/boot-startup-validation', 'spring/boot-context-initializer-boundary'),
]:
    entry = by_path[source]
    entry['body'] += '<h2>Related Boot contract</h2><p><a href="/' + target + '">' + html.escape(titles[target]) + '</a>.</p>'
    entry['updated_at'] = stamp

fixture.write_text(json.dumps(rows, ensure_ascii=False, indent=2) + '\n')
print(f'Added {len(lessons)} Spring Boot lessons; {len(rows)} total fixture records')
