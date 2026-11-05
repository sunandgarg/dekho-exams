"""Add original, checked Spring config-data lessons to the separate Spring track."""
from __future__ import annotations

import datetime
import html
import json
import pathlib
import re
import uuid

ROOT = pathlib.Path(__file__).resolve().parents[1]
FILE = ROOT / 'src/data/fixtures.json'
rows = json.loads(FILE.read_text())
by = {row['path']: row for row in rows}
stamp = datetime.datetime.now(datetime.UTC).isoformat()


def p(value):
    escaped = html.escape(value)
    return '<p>' + re.sub(r'\[\[([^|]+)\|([^\]]+)\]\]',
        lambda match: '<a href="/' + match[1] + '">' + match[2] + '</a>', escaped) + '</p>'


lessons = [
    dict(slug='boot-nested-relative-import', section='spring-boot',
         title='Spring Boot nested config imports: each file becomes the next base directory',
         opening='A relative import declared inside an imported Spring Boot file resolves beside that imported file.',
         parts=[('Follow all three files', [
             'The checked child starts from a launch directory, but its additional config location points to config/application.properties. That file imports relay/worker.properties. The worker file imports overrides/late.properties. The final file lives at config/relay/overrides/late.properties and sets relay.batch-size to 37. The child reports batch 37 and keeps the one-second timeout from the first file. [[spring/boot-relative-import-process|The one-hop test]] stops at worker.properties; this test adds the second hop.',
             'Each file owns its own relative path. Resolving overrides/late.properties from the process working directory, or even from the first application.properties, would pick the wrong location. The test checks the effective bean value, not just whether every filename exists.']),
             ('Check precedence and failure separately', [
             'In this fixture the later imported batch value replaces 17 from the worker file and 11 from application.properties. The one-second timeout remains because neither imported file defines it. [[spring/boot-nested-import-missing|The missing-hop case]] proves a required second import stops startup instead of falling back silently.',
             'This is a local temporary-file chain in one child JVM. It does not test a Kubernetes volume, filesystem permission change or a config file replaced during startup.'])],
         code='// config/application.properties\nrelay.batch-size=11\nrelay.timeout=1s\nspring.config.import=relay/worker.properties\n// config/relay/worker.properties\nrelay.batch-size=17\nspring.config.import=overrides/late.properties\n// config/relay/overrides/late.properties\nrelay.batch-size=37', lang='properties',
         proof='RelaySettingsProcessTest.secondRelativeImportUsesTheIntermediateFilesDirectory',
         mistakes=['Do not resolve every relative import from application.properties.','Do not use the launch directory as the base for an import declared in a file.','Do not call this temporary-file chain a container mount test.'],
         links=['spring/boot-relative-config-import','spring/boot-relative-import-process','spring/boot-nested-import-missing','spring/boot-config-source-matrix']),
    dict(slug='boot-nested-import-missing', section='spring-boot',
         title='Spring Boot nested import failure: a missing second hop must stop startup',
         opening='A required config import inside an imported file is still required when Boot starts a new process.',
         parts=[('Reject the incomplete chain', [
             'The test creates config/application.properties and config/relay/worker.properties. The worker imports overrides/missing.properties, but that file is absent. The child exits nonzero without printing a bound batch. The failure is observed at startup, before the probe can use RelaySettings. [[spring/boot-nested-relative-import|The successful chain]] supplies the same kind of second hop and reaches a final batch value.',
             'A required import gives a stronger release signal than an optional fallback. A service may otherwise run with the first file’s defaults even though an operator thought a later file was present. [[spring/boot-required-config-import|The first-hop missing-file test]] covers a different path.']),
             ('Keep the failure claim narrow', [
             'The assertion checks exit status and absence of the success marker. It avoids coupling to Boot’s outer exception text, which can change between releases. It does not check bad permissions, an empty but existing file, a malformed value, or a file removed after startup. [[spring/boot-configtree-invalid-value|The typed-value case]] addresses one of those separate failures.'])],
         code='// config/relay/worker.properties\nspring.config.import=overrides/missing.properties\n// No config/relay/overrides/missing.properties exists.', lang='properties',
         proof='RelaySettingsProcessTest.missingSecondRelativeImportStopsTheChildProcess',
         mistakes=['Do not mark an operator-owned file optional solely to hide a bad path.','Do not assert one exact wrapper exception across Boot versions.','Do not confuse a missing file with a file containing an invalid key.'],
         links=['spring/boot-nested-relative-import','spring/boot-required-config-import','spring/boot-missing-import-process','spring/boot-configtree-required-location']),
    dict(slug='boot-configtree-file-binding', section='spring-boot',
         title='Spring Boot configtree: bind one file per property in a child JVM',
         opening='A configtree import turns filenames under a directory into Spring Boot property names.',
         parts=[('Name the files after the properties', [
             'The fixture creates a local mounted-values/relay directory with batch-size containing 41 and timeout containing 1500ms. Its application.properties imports the absolute directory using configtree:. A child JVM then reports batch 41 and timeout 1500 milliseconds. Those two values come from real files, not from a manually inserted PropertySource. [[spring/boot-env-process-binding|The environment fixture]] takes a different input path.',
             'The path passed after configtree: is an absolute directory path ending in a slash. A file: URL after configtree: did not resolve in this pinned fixture, so the checked example uses the directory form directly. Each file contains a value. The file path supplies the key.']),
             ('Do not expose the payload to prove loading', [
             'The two checked values are non-secret settings. A configtree may also carry credentials, but the probe does not read or print one. Diagnose a sensitive import by checking presence, successful binding, and redacted source identity. [[spring/boot-configtree-test-boundary|The boundary page]] separates these local files from an actual platform secret mount.',
             'A file-tree import is not a live subscription. This test starts once and reads the values at startup; it does not prove that changing a file refreshes an already running bean.'])],
         code='spring.config.import=configtree:/absolute/path/mounted-values/\n# mounted-values/relay/batch-size contains 41\n# mounted-values/relay/timeout contains 1500ms', lang='properties',
         proof='RelaySettingsProcessTest.fileTreeImportBindsValuesWithoutPrintingASecret',
         mistakes=['Do not put a file: URL after configtree: in this checked fixture.','Do not log a credential to show that a file-tree import worked.','Do not assume a file change updates a bean without a separate refresh mechanism.'],
         links=['spring/boot-configtree-env-precedence','spring/boot-configtree-required-location','spring/boot-configtree-invalid-value','spring/boot-configtree-test-boundary']),
    dict(slug='boot-configtree-env-precedence', section='spring-boot',
         title='Spring Boot configtree versus environment: assert the effective value',
         opening='The checked process takes relay.batch-size from its environment when a configtree also provides that property.',
         parts=[('Create a real collision', [
             'A local file tree contains relay/batch-size with 41. The child process inherits RELAY_BATCHSIZE=44. It reports BOUND_BATCH=44, establishing the effective bean value under this pinned Boot configuration. This complements [[spring/boot-env-cli-precedence|the environment-versus-CLI test]] and [[spring/boot-config-precedence-file-cli|the file-versus-CLI test]]. One source list alone would not show which value the worker receives.',
             'Operationally, the operator may mount 41 while a launcher injects 44. Inspect the final process environment and non-secret bound value when diagnosing a surprise batch size. [[spring/poller-batch-limit|The polling budget]] determines the work admitted per tick.']),
             ('Avoid a blanket precedence slogan', [
             'This fixture has one tree, one environment value and one programmatic default. Profile files, Java system properties, JSON application properties and test-only sources are absent. [[spring/boot-config-source-matrix|The matrix]] keeps combinations distinct. Do not extrapolate this assertion to every source type.',
             'Credentials require a different diagnostic. It is enough to verify their source and shape without printing their values.'])],
         code='// mounted-values/relay/batch-size: 41\n// child environment: RELAY_BATCHSIZE=44\n// child result: BOUND_BATCH=44', lang='text',
         proof='RelaySettingsProcessTest.environmentValueOverridesTheImportedFileTree',
         mistakes=['Do not inspect only the mounted file when an environment override exists.','Do not print secret values while tracing source precedence.','Do not claim this pairwise test covers every Boot property source.'],
         links=['spring/boot-configtree-file-binding','spring/boot-env-cli-precedence','spring/boot-config-source-matrix','spring/poller-batch-limit']),
    dict(slug='boot-configtree-required-location', section='spring-boot',
         title='Spring Boot required configtree: reject an absent directory',
         opening='A non-optional configtree location prevents the checked Boot child from starting when its directory is absent.',
         parts=[('Fail on the location', [
             'The test writes spring.config.import=configtree: followed by an absolute path to absent-values/. It never creates that directory. The child exits nonzero and never prints a bound batch. A default batch value exists in the probe, but it cannot make a required source appear. [[spring/boot-configtree-file-binding|The successful file-tree case]] creates the directory and its two value files.',
             'If an operator promises to supply a directory, a required import turns a missing mount path into an immediate startup failure. An optional prefix is appropriate only when the application has a documented fallback for the entire directory. [[spring/boot-optional-config-import|The optional file fixture]] uses that different policy.']),
             ('Directory presence is only the first check', [
             'A directory can exist while an individual required key is missing or invalid. The probe’s defaults mean a missing batch-size file could leave batch 8 in place. Stronger deployment contracts should validate required keys explicitly and test missing-file cases. [[spring/boot-configtree-invalid-value|The invalid-value test]] proves only one bound range rejection.',
             'This is a local directory, not a container mount with platform permissions, rotation or availability guarantees.'])],
         code='spring.config.import=configtree:/absolute/path/absent-values/\n# Required directory is absent; the child exits nonzero.', lang='properties',
         proof='RelaySettingsProcessTest.missingRequiredFileTreeStopsStartup',
         mistakes=['Do not assume a default value rescues a missing required import.','Do not treat directory presence as proof that every required file exists.','Do not make every deployment source optional to avoid startup failures.'],
         links=['spring/boot-configtree-file-binding','spring/boot-configtree-invalid-value','spring/boot-required-config-import','spring/boot-configtree-test-boundary']),
    dict(slug='boot-configtree-invalid-value', section='spring-boot',
         title='Spring Boot configtree validation: reject a present but unsafe value',
         opening='An existing configtree file can still contain a value that fails typed configuration validation.',
         parts=[('Load, bind, then validate', [
             'The local file mounted-values/relay/batch-size exists and contains 0. Boot finds the tree, binds the setting and rejects it because the relay record requires a batch size from 1 through 100. The child exits nonzero without printing a successful bound result. [[spring/boot-configtree-required-location|The absent-directory case]] fails earlier, before the value is read.',
             'This distinction matters during rollout. A successful file lookup does not mean the application can safely process work. A value can be empty, malformed, out of range, or inconsistent with another setting. The fixture checks only the out-of-range integer. [[spring/boot-startup-validation|The typed validation lesson]] explains the bean constraint.']),
             ('Keep the error report safe', [
             'The checked value is non-secret. A production validation failure may include the rejected value in logs, so do not use a secret property as the demonstration. A sensitive property should have a redacted diagnostic and a separate presence or format check. The source kit has no credential-bearing configtree test.',
             'A file may also change after startup. This test does not establish runtime refresh, atomic file replacement or the behavior of a running worker during rotation.'])],
         code='// mounted-values/relay/batch-size contains 0\n@Min(1) @Max(100) int batchSize\n// Child process exits before BOUND_BATCH is printed.', lang='java',
         proof='RelaySettingsProcessTest.invalidValueInFileTreeFailsValidation',
         mistakes=['Do not call a readable file a valid configuration.','Do not include a secret value in a binding-error screenshot.','Do not infer runtime reload from a startup validation test.'],
         links=['spring/boot-configtree-file-binding','spring/boot-configtree-required-location','spring/boot-startup-validation','spring/boot-configtree-test-boundary']),
    dict(slug='boot-extensionless-config-file', section='spring-boot',
         title='Spring Boot extensionless config file: give the loader a properties hint',
         opening='An extensionless imported file needs an extension hint so Spring Boot can parse its contents as properties.',
         parts=[('Name the format in the import', [
             'The test creates a file named relay-values with no suffix. It contains relay.batch-size=47 and relay.timeout=2s. application.properties imports that file URI with [.properties] appended. The child reports batch 47 and timeout 2000 milliseconds. This verifies parsing of one actual extensionless local file rather than a hand-built property map.',
             'Some mounted files lack conventional extensions. An extension hint selects a loader without renaming the file supplied by the platform. The file remains a fixed URI; [[spring/boot-nested-relative-import|a relative import]] follows a different path rule.']),
             ('Do not overstate the mount evidence', [
             'The file is written by the test in a temporary directory. No platform injects it and no secret value is present. The case does not check YAML, alternate encodings, permission errors or rotation. [[spring/boot-configtree-file-binding|A configtree]] is another option when each file represents one key.',
             'A successful parse is only the first step. Keep typed validation for ranges, endpoint shape and cross-setting constraints.'])],
         code='spring.config.import=file:/absolute/path/relay-values[.properties]\n# relay-values has no extension and contains relay.batch-size=47', lang='properties',
         proof='RelaySettingsProcessTest.extensionlessPropertiesFileNeedsAnExtensionHint',
         mistakes=['Do not expect the loader to infer every extensionless file format.','Do not confuse a fixed file URI with a relative import.','Do not call a temporary-file test a production platform mount test.'],
         links=['spring/boot-configtree-file-binding','spring/boot-nested-relative-import','spring/boot-additional-config-file','spring/boot-configtree-test-boundary']),
    dict(slug='boot-configtree-test-boundary', section='spring-testing',
         title='Spring Boot file-tree tests: prove binding without claiming secret delivery',
         opening='A local configtree fixture proves Spring Boot reads values from files, while platform secret delivery needs a separate release test.',
         parts=[('What the child process checks', [
             'RelaySettingsProcessTest now launches a child JVM with a real file tree, an environment override, an absent required directory and an out-of-range file value. It also checks a two-hop relative import and an extensionless properties file. These tests cover concrete startup paths under the pinned source-kit version. [[spring/boot-configtree-file-binding|The file-binding page]] states the successful case; [[spring/boot-configtree-required-location|the missing-location page]] states one failure case.',
             'The fixture does not create a container, attach a secret volume, change the Unix user, or start ReceiptApplication. It does not prove that a deployment manifest points at the right mount or that the application can read it after a rollout.']),
             ('Design the deployment check', [
             'Start the packaged application with the actual entrypoint, user identity, working directory and mount. Use non-secret sentinel settings to check path resolution and source precedence. For a credential, check presence and behavior through a safe authenticated operation; do not echo its bytes or return them from an Actuator endpoint.',
             'Exercise missing mount, invalid value and restored mount as separate deployments. Confirm readiness and traffic behavior; a child exit alone does not test an ingress controller. [[spring/liveness-readiness-separation|Health groups]] and [[spring/readiness-during-termination|termination order]] describe those distinct states.'])],
         code='// Local proof: configtree directory + child JVM + non-secret bound values.\n// Deployment proof still needed: real mount + identity + packaged app + readiness.', lang='text',
         proof='RelaySettingsProcessTest (twelve child-JVM cases)',
         mistakes=['Do not describe a temporary directory as a secret mount.','Do not log credentials to prove a configtree import.','Do not substitute a process-exit check for deployment readiness and ingress tests.'],
         links=['spring/boot-configtree-file-binding','spring/boot-configtree-required-location','spring/boot-config-process-test-boundary','spring/liveness-readiness-separation']),
]

titles = {row['path']:row['title'] for row in rows}
titles.update({'spring/'+item['slug']:item['title'] for item in lessons})
for item in lessons:
    path = 'spring/'+item['slug']
    assert path not in by
    body = p(item['opening'])
    for heading, paragraphs in item['parts']:
        body += '<h2>'+html.escape(heading)+'</h2>'+''.join(p(text) for text in paragraphs)
    body += '<h2>Checked source</h2><pre><code class="language-'+item['lang']+'">'+html.escape(item['code'],quote=False)+'</code></pre>'
    body += '<h2>Verification boundary</h2>'+p(item['proof']+'. The full fixture is in the downloadable source kit.')
    body += '<h3>Common Mistakes</h3><ul>'+''.join('<li>'+html.escape(text)+'</li>' for text in item['mistakes'])+'</ul>'
    body += '<h2>Read next</h2>'+p(', '.join('[['+target+'|'+titles[target]+']]' for target in item['links'])+'.')
    section_path = 'spring/testing' if item['section']=='spring-testing' else 'spring/spring-boot'
    row=by['spring/if-match-receipt-write'].copy()
    row.update(id=str(uuid.uuid5(uuid.NAMESPACE_URL,'https://aitrove.in/'+path)),type='article',path=path,
               title=item['title'],summary=item['opening'],body=body,subject=item['section'],
               difficulty='Intermediate',status='published',tags=['spring','configuration','testing'],
               featured=False,sort_order=1400+len(rows),published_at=stamp,created_at=stamp,updated_at=stamp)
    row['data']={'subject_root':'spring/spring-boot','section_path':section_path,'kind':'tutorial',
                 'content_format':'html','reading_minutes':max(4,round(len(re.sub(r'<[^>]+>',' ',body).split())/150)),
                 'author_path':'authors/aitrove-editorial','seo_ready':True,
                 'related':[{'path':target,'title':titles[target]} for target in item['links']],
                 'framework_version':'Spring Boot 4.0.8 / Spring Framework 7','java_version':'21 source-kit baseline',
                 'verification_suite':item['proof'],'download_path':'/downloads/aitrove-spring-source-kit.zip'}
    rows.append(row)
    by[path]=row

for hub_path,heading,summary in [
    ('spring/spring-boot','Nested files and config trees','Checked second-hop imports, file-per-key trees and extensionless files.'),
    ('spring/testing','File-tree release boundary','Separate local child-process proof from platform secret delivery.')]:
    hub=by[hub_path]
    paths=['spring/'+item['slug'] for item in lessons if ('spring/testing' if item['section']=='spring-testing' else 'spring/spring-boot')==hub_path]
    hub['data']['modules'].append({'title':heading,'summary':summary,'lessons':paths})
    hub['updated_at']=stamp
    if '<h2>Section lessons</h2>' in hub['body']:
        links='<ul>'+''.join('<li><a href="/'+path+'">'+html.escape(titles[path])+'</a></li>' for module in hub['data']['modules'] for path in module['lessons'])+'</ul>'
        hub['body']=re.sub(r'(<h2>Section lessons</h2>)[\s\S]*?(<h2>Continue learning</h2>)',lambda match:match[1]+links+match[2],hub['body'])

revisions={
 'spring/boot-relative-config-import':[
  ('a second nested import remains untested','RelaySettingsProcessTest now checks a second nested import')],
 'spring/boot-config-process-test-boundary':[
  ('It does not read a Kubernetes Secret, mounted volume or external config service.','A later fixture now reads a synthetic local file tree through configtree:; it still does not read a Kubernetes Secret, production-mounted volume or external config service.')],
 'spring/boot-config-source-matrix':[
  ('A deployment-mounted file and secret source remain untested.','A synthetic local configtree is now checked in a child process. A deployment-mounted file and secret source remain untested.')],
}
for path,replacements in revisions.items():
    row=by[path]
    for before,after in replacements:
        if before in row['body']:
            row['body']=row['body'].replace(before,after)
        elif before in row['data'].get('verification_suite',''):
            row['data']['verification_suite']=row['data']['verification_suite'].replace(before,after)
        else:
            raise AssertionError((path,before))
    row['updated_at']=stamp

reverse={
 'spring/boot-relative-config-import':['spring/boot-nested-relative-import'],
 'spring/boot-relative-import-process':['spring/boot-nested-relative-import'],
 'spring/boot-missing-import-process':['spring/boot-nested-import-missing'],
 'spring/boot-config-process-test-boundary':['spring/boot-configtree-test-boundary'],
 'spring/boot-config-source-matrix':['spring/boot-configtree-env-precedence'],
 'spring/boot-startup-validation':['spring/boot-configtree-invalid-value'],
 'spring/boot-additional-config-file':['spring/boot-extensionless-config-file'],
 'spring/testing-boundaries':['spring/boot-configtree-test-boundary'],
}
for path,targets in reverse.items():
    row=by[path]
    row['body']+='<h2>Checked config-data continuation</h2>'+p('Continue with '+', '.join('[['+target+'|'+titles[target]+']]' for target in targets)+'.')
    row['updated_at']=stamp

quiz_path='quizzes/spring-config-tree'
assert quiz_path not in by
questions=[
 ('Where does the second relative import resolve?',['Beside worker.properties','Beside application.properties','From the JVM launch directory'],0,'Each declaring file supplies the base for its own relative import.'),
 ('What batch value wins in the checked three-file chain?',['37','17','11'],0,'The second imported file supplies 37.'),
 ('What timeout remains in that three-file chain?',['One second','Two seconds','Thirty-seven seconds'],0,'Only application.properties supplies the timeout.'),
 ('What happens when the required second-hop file is absent?',['The child exits nonzero','Batch 17 always wins','Boot creates the file'],0,'The chain cannot complete a required import.'),
 ('In a configtree, what supplies a property name?',['The path and filename','The Maven artifact name','The JVM PID'],0,'The file path supplies the key and the file contents supply the value.'),
 ('What path form passed the checked configtree test?',['An absolute directory path after configtree:','A file: URL after configtree:','The current working directory alone'],0,'The fixture uses an absolute directory path ending with a slash.'),
 ('What batch size wins when a tree has 41 and the environment has 44?',['44','41','8'],0,'The child reports the environment-provided 44.'),
 ('What happens if a required configtree directory is absent?',['Startup fails','An empty directory is generated','The CLI flag becomes secret'],0,'The non-optional location is missing.'),
 ('What does a tree file containing batch-size 0 prove?',['Binding can succeed at file lookup but fail typed validation','The directory does not exist','The file is refreshed automatically'],0,'The present value violates the bean range.'),
 ('What tells Boot to parse an extensionless file as properties?',['A [.properties] import hint','Renaming the JAR','A queue consumer'],0,'The checked import includes an extension hint.'),
 ('Does the local file-tree fixture prove a platform secret mount?',['No','Yes','Only for a one-second timeout'],0,'The test creates temporary local files and uses no platform mount.'),
 ('What should a production check avoid returning in diagnostics?',['Credential contents','Non-secret source identity','A process exit code'],0,'Secrets should not be echoed to prove loading.'),
]
quiz=by['quizzes/spring-boot-startup'].copy()
quiz.update(id=str(uuid.uuid5(uuid.NAMESPACE_URL,'https://aitrove.in/'+quiz_path)),path=quiz_path,
            title='Spring Boot config imports and file trees quiz',
            summary='Twelve explained questions about nested imports, file-per-key trees and their test limits.',
            sort_order=1400,published_at=stamp,created_at=stamp,updated_at=stamp)
quiz['body']=p('Check the file lookup and validation contracts before changing a deployment config path.')+'<h2>Review before answering</h2><ul>'+''.join('<li><a href="/'+path+'">'+html.escape(titles[path])+'</a></li>' for path in ['spring/boot-nested-relative-import','spring/boot-nested-import-missing','spring/boot-configtree-file-binding','spring/boot-configtree-env-precedence','spring/boot-configtree-required-location','spring/boot-configtree-invalid-value','spring/boot-extensionless-config-file'])+'</ul><h3>Common Mistakes</h3><ul><li>Do not resolve every import from the first file.</li><li>Do not confuse a loaded file with a valid value.</li><li>Do not call a synthetic tree a platform secret mount.</li></ul>'
quiz['data']={'questions':[{'prompt':q,'options':options,'answer':answer,'explanation':explanation} for q,options,answer,explanation in questions],
              'duration_minutes':12,'subject_root':'spring/spring-boot','section_path':'spring/quizzes',
              'content_format':'html','seo_ready':True}
rows.append(quiz)
hub=by['spring/quizzes']
hub['data']['modules'].append({'title':'Config data files','summary':'Twelve checks on nested imports and config trees.','lessons':[quiz_path]})
hub['updated_at']=stamp
if '<h2>Section lessons</h2>' in hub['body']:
    links='<ul>'+''.join('<li><a href="/'+path+'">'+html.escape({**titles,quiz_path:quiz['title']}[path])+'</a></li>' for module in hub['data']['modules'] for path in module['lessons'])+'</ul>'
    hub['body']=re.sub(r'(<h2>Section lessons</h2>)[\s\S]*?(<h2>Continue learning</h2>)',lambda match:match[1]+links+match[2],hub['body'])

FILE.write_text(json.dumps(rows,ensure_ascii=False,indent=2)+'\n')
print(json.dumps({'articles':len(lessons),'questions':len(questions),'paths':['spring/'+item['slug'] for item in lessons]}))
