"""Add original Spring configuration lessons tied to real child-JVM checks."""
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


def paragraph(value):
    escaped = html.escape(value)
    return '<p>' + re.sub(r'\[\[([^|]+)\|([^\]]+)\]\]',
        lambda match: '<a href="/' + match[1] + '">' + match[2] + '</a>', escaped) + '</p>'


lessons = [
    dict(slug='boot-env-process-binding', section='spring-boot', title='Spring Boot environment binding: prove the value in a child JVM',
         opening='Spring Boot binds RELAY_BATCHSIZE and RELAY_TIMEOUT from the environment inherited by a launched JVM.',
         parts=[('The process boundary', [
             'RelaySettingsProcessTest launches a separate non-web Boot process with RELAY_BATCHSIZE=29 and RELAY_TIMEOUT=750ms. Its output reports batch 29 and timeout 750 milliseconds. That check crosses the operating-system process boundary; injecting a MapPropertySource into the parent test would not. [[spring/boot-environment-variable-binding|The canonical naming rule]] maps relay.batch-size to RELAY_BATCHSIZE, with the dash removed.',
             'The test clears inherited relay variables before assigning its own. Otherwise a developer shell or CI setting could change the assertion. The child uses bounded defaults of batch 8 and two seconds so the test can distinguish an absent key from an applied override. A deployment should still validate that each required key is present; a plausible default can hide a misspelling.']),
             ('Where the check stops', [
             'This child is a small probe, not ReceiptApplication. It checks two plain values and bean validation under one pinned Boot baseline. It does not read a mounted secret, start the HTTP service or verify a container entrypoint. [[spring/boot-config-process-test-boundary|The process-test boundary]] separates these claims.',
             'Keep credentials out of diagnostic output. The probe prints non-secret values only. A production startup log can report whether a secret source was found without printing the secret itself.'])],
         code='RELAY_BATCHSIZE=29 RELAY_TIMEOUT=750ms java -cp "$CLASSPATH" in.aitrove.contracts.RelaySettingsProcessProbe\n# BOUND_BATCH=29\n# BOUND_TIMEOUT=750', lang='bash', proof='RelaySettingsProcessTest.actualEnvironmentBindsTheCanonicalRelayKeys',
         mistakes=['Do not use RELAY_BATCH_SIZE for relay.batch-size without checking the actual binding rule.','Do not pass the same value as a command-line flag and call that an environment test.','Do not print secret values to prove that binding worked.'],
         links=['spring/boot-environment-variable-binding','spring/boot-env-cli-precedence','spring/boot-env-validation-failure','spring/boot-config-process-test-boundary']),
    dict(slug='boot-env-cli-precedence', section='spring-boot', title='Spring Boot config precedence: command line beats a process variable',
         opening='A command-line relay.batch-size value replaces the environment value in the checked Boot process.',
         parts=[('Force the collision', [
             'The child receives RELAY_BATCHSIZE=29 and --relay.batch-size=31. RelaySettingsProcessTest asserts BOUND_BATCH=31. This is an effective-value check, not an inspection of two sources in isolation. [[spring/boot-command-line-precedence|The earlier startup test]] covered command line against a programmatic default; this one uses an actual inherited environment variable.',
             'The operator must know which source wins. A batch size of 31 instead of 29 changes a worker tick budget, while a timeout override can change the number of requests held in flight. [[spring/poller-batch-limit|The polling limit]] gives that setting an operational consequence.']),
             ('Keep the argument visible to review', [
             'A launcher may append flags after an operator sets environment variables. Review the final process command, not just its deployment manifest. Do not put credentials in command-line arguments where process listings may expose them. The test proves only one plain integer collision; it does not model a secret source or multiple profiles.'])],
         code='RELAY_BATCHSIZE=29 java -cp "$CLASSPATH" in.aitrove.contracts.RelaySettingsProcessProbe --relay.batch-size=31\n# BOUND_BATCH=31', lang='bash', proof='RelaySettingsProcessTest.commandLineWinsOverTheProcessEnvironment',
         mistakes=['Do not infer the effective value from the environment alone.','Do not put a password in a command-line flag for a convenient override.','Do not assume every property source has the same precedence as this pair.'],
         links=['spring/boot-env-process-binding','spring/boot-command-line-precedence','spring/boot-config-source-matrix','spring/poller-batch-limit']),
    dict(slug='boot-env-validation-failure', section='spring-boot', title='Spring Boot environment validation: fail before a worker starts',
         opening='An invalid environment-provided batch size stops the checked Boot process before it prints a bound value.',
         parts=[('Reject the effective value', [
             'The probe binds relay.batch-size to an integer constrained from 1 through 100. With RELAY_BATCHSIZE=0, the child exits nonzero and never emits BOUND_BATCH. This tests validation after the environment source has been selected. [[spring/boot-startup-validation|The typed startup rule]] is the reason the worker should not quietly run with zero rows per tick.',
             'A default of 8 is present, yet the explicit zero still fails. The default does not rescue an invalid higher-priority setting. This is different from a missing variable, which can legitimately leave the default in place under this fixture. A production requirement might reject absence too.']),
             ('Failure is not an operational rollout test', [
             'The process test checks an exit code and lack of successful output. It does not prove that a load balancer removed the instance, that a retrying orchestrator backed off, or that no work was already in flight. [[spring/liveness-readiness-separation|The health boundary]] and [[spring/boot-graceful-shutdown|the drain contract]] cover separate release behavior.'])],
         code='RELAY_BATCHSIZE=0 java -cp "$CLASSPATH" in.aitrove.contracts.RelaySettingsProcessProbe\n# Nonzero exit; no BOUND_BATCH line', lang='bash', proof='RelaySettingsProcessTest.invalidEnvironmentValuePreventsStartup',
         mistakes=['Do not validate only the programmatic default.','Do not treat absence and an explicitly invalid value as the same case.','Do not claim a failing probe proves deployment traffic was drained.'],
         links=['spring/boot-env-process-binding','spring/boot-startup-validation','spring/boot-config-source-matrix','spring/liveness-readiness-separation']),
    dict(slug='boot-relative-import-process', section='spring-boot', title='Spring Boot relative config import: change the working directory and inspect the value',
         opening='A relative Spring Boot config import can be verified while the process starts outside the configuration directory.',
         parts=[('Separate file location from launch location', [
             'The test writes config/application.properties with relay.batch-size=17, relay.timeout=750ms and spring.config.import=relay/worker.properties. The imported config/relay/worker.properties contains relay.batch-size=29. The child starts in a different launch directory and receives --spring.config.additional-location pointing at config. It reports batch 29 and timeout 750. [[spring/boot-relative-config-import|The path rule]] is observable in the bound bean rather than assumed from a string.',
             'The imported file wins for its batch key while the declaring file still supplies timeout. Check both values; checking only that startup succeeded could miss a fallback or an unintended source. [[spring/boot-config-source-matrix|The source matrix]] should name this as a distinct row.']),
             ('Do not turn this into a mount claim', [
             'The two directories are temporary directories on one local machine. The test does not mount a container volume, change file permissions or read a secret store. A release test must start the packaged artifact with its actual mount and working directory. [[spring/boot-config-process-test-boundary|The remaining test boundary]] lists the gaps.'])],
         code='relay.batch-size=17\nrelay.timeout=750ms\nspring.config.import=relay/worker.properties\n# config/relay/worker.properties: relay.batch-size=29', lang='properties', proof='RelaySettingsProcessTest.relativeImportUsesItsDeclaringFileOutsideTheWorkingDirectory',
         mistakes=['Do not resolve relay/worker.properties relative to the launch directory.','Do not assert only that the child started; inspect the effective bean values.','Do not call temporary directories a production volume mount.'],
         links=['spring/boot-relative-config-import','spring/boot-missing-import-process','spring/boot-config-source-matrix','spring/boot-config-process-test-boundary']),
    dict(slug='boot-missing-import-process', section='spring-boot', title='Spring Boot required import: fail when a relative file is missing',
         opening='A required relative Spring Boot configuration import prevents the checked child process from starting when the file is absent.',
         parts=[('Failure at the same boundary', [
             'The test creates config/application.properties with spring.config.import=relay/missing.properties and does not create that imported file. A child JVM receives the config directory as an additional location. It exits nonzero and never prints a successful bound value. [[spring/boot-required-config-import|The earlier context test]] checked a missing file URI inside one JVM; this check adds a launched-process boundary and a relative path.',
             'Use a required import when its absence must stop work. A different policy may allow a developer-only override to be optional. [[spring/boot-optional-config-import|The optional test]] proves a fallback for one missing local file; it should not be copied to a required credential.']),
             ('Other failures still need checks', [
             'The child does not test unreadable permissions, a partially written file, a wrong key, a malformed secret or rotation during a running process. A successful import also says nothing about the validity of the loaded values until binding and validation run. [[spring/boot-env-validation-failure|The invalid-value check]] covers one such boundary.'])],
         code='spring.config.import=relay/missing.properties\n# No config/relay/missing.properties exists; child exits nonzero.', lang='properties', proof='RelaySettingsProcessTest.missingRequiredRelativeImportStopsTheChildProcess',
         mistakes=['Do not turn a required deployment file into an optional import just to clear a startup error.','Do not interpret a nonzero exit as proof of a specific exception text across Boot versions.','Do not put a secret value in a startup diagnostic.'],
         links=['spring/boot-required-config-import','spring/boot-optional-config-import','spring/boot-relative-import-process','spring/boot-env-validation-failure']),
    dict(slug='boot-config-process-test-boundary', section='spring-testing', title='Spring Boot config tests: what a child JVM proves and what deployment still owes',
         opening='A child-JVM configuration test checks inherited process state and startup behavior without testing a production deployment.',
         parts=[('Three layers of evidence', [
             'A manually inserted property source checks binding rules in a local context. A Boot context checks framework startup with supplied arguments and files. RelaySettingsProcessTest goes one layer further by launching a new JVM with environment values and a separate working directory. [[spring/boot-env-process-binding|The environment result]] and [[spring/boot-relative-import-process|the import result]] make that difference concrete.',
             'The probe is not ReceiptApplication. It has no network listener, persistent database or work queue. It does not read a Kubernetes Secret, mounted volume or external config service. A deployment test should start the packaged application with the actual entrypoint, mount, user ID and rollout settings, then inspect a non-secret effective value and failure status.']),
             ('Test an outage without leaking data', [
             'Inject a missing required file and an invalid non-secret value in a staging deployment. Confirm the instance does not accept traffic and that the failure message does not expose a credential. Check a working config after restart as a separate case. [[spring/liveness-readiness-separation|Readiness]] and [[spring/boot-graceful-shutdown|shutdown]] are distinct contracts; a process-exit assertion cannot stand in for them.'])],
         code='Result result = run(Map.of("RELAY_BATCHSIZE", "29"), launchDirectory);\nassertEquals(0, result.exitCode());\nassertTrue(result.output().contains("BOUND_BATCH=29"));', lang='java', proof='RelaySettingsProcessTest (five child-JVM cases)',
         mistakes=['Do not describe a local child JVM as a container or production service.','Do not copy non-secret diagnostic techniques to credential values.','Do not skip deployment startup and rollout tests because local binding passed.'],
         links=['spring/boot-env-process-binding','spring/boot-relative-import-process','spring/boot-missing-import-process','spring/testing-boundaries']),
]

titles = {row['path']: row['title'] for row in rows}
titles.update({'spring/' + item['slug']: item['title'] for item in lessons})
for item in lessons:
    path = 'spring/' + item['slug']
    assert path not in by
    body = paragraph(item['opening'])
    for heading, paragraphs in item['parts']:
        body += '<h2>' + html.escape(heading) + '</h2>' + ''.join(paragraph(x) for x in paragraphs)
    body += '<h2>Checked source</h2><pre><code class="language-' + item['lang'] + '">' + html.escape(item['code'], quote=False) + '</code></pre>'
    body += '<h2>Verification boundary</h2>' + paragraph(item['proof'] + '. The source kit contains the full test and entry point.')
    body += '<h3>Common Mistakes</h3><ul>' + ''.join('<li>' + html.escape(x) + '</li>' for x in item['mistakes']) + '</ul>'
    body += '<h2>Read next</h2>' + paragraph(', '.join('[[' + target + '|' + titles[target] + ']]' for target in item['links']) + '.')
    hub_path = 'spring/testing' if item['section'] == 'spring-testing' else 'spring/spring-boot'
    row = by['spring/if-match-receipt-write'].copy()
    row.update(id=str(uuid.uuid5(uuid.NAMESPACE_URL, 'https://aitrove.in/' + path)), type='article', path=path,
        title=item['title'], summary=item['opening'], body=body, subject=item['section'], difficulty='Intermediate',
        status='published', tags=['spring','configuration','testing'], featured=False, sort_order=1300+len(rows),
        published_at=stamp, created_at=stamp, updated_at=stamp)
    row['data'] = {'subject_root':'spring/spring-boot','section_path':hub_path,'kind':'tutorial','content_format':'html',
        'reading_minutes':max(4, round(len(re.sub(r'<[^>]+>',' ',body).split())/150)),
        'author_path':'authors/aitrove-editorial','seo_ready':True,
        'related':[{'path':target,'title':titles[target]} for target in item['links']],
        'framework_version':'Spring Boot 4.0.8 / Spring Framework 7','java_version':'21 source-kit baseline',
        'verification_suite':item['proof'],'download_path':'/downloads/aitrove-spring-source-kit.zip'}
    rows.append(row)
    by[path] = row

for section, heading, summary in [('spring/spring-boot','Process configuration checks','Five child-JVM checks for environment, CLI, validation and relative imports.'),
                                  ('spring/testing','Process boundary','Distinguish child-process checks from deployment checks.')]:
    hub = by[section]
    paths = ['spring/' + item['slug'] for item in lessons if ('spring/testing' if item['section']=='spring-testing' else 'spring/spring-boot') == section]
    hub['data']['modules'].append({'title':heading,'summary':summary,'lessons':paths})
    hub['updated_at'] = stamp
    if '<h2>Section lessons</h2>' in hub['body']:
        links = '<ul>' + ''.join('<li><a href="/' + path + '">' + html.escape(titles[path]) + '</a></li>' for module in hub['data']['modules'] for path in module['lessons']) + '</ul>'
        hub['body'] = re.sub(r'(<h2>Section lessons</h2>)[\s\S]*?(<h2>Continue learning</h2>)', lambda match: match[1]+links+match[2], hub['body'])

revisions = {
 'spring/boot-environment-variable-binding': [
  ('The current source kit does not run that child-process check.', 'RelaySettingsProcessTest now runs that child-process check and asserts batch 29 and timeout 750 milliseconds.'),
  ('No process-environment test exists in the source kit. BootRelaySettingsTest checks file and CLI sources only', 'RelaySettingsProcessTest.actualEnvironmentBindsTheCanonicalRelayKeys checks inherited environment values in a child JVM')],
 'spring/boot-relative-config-import': [
  ('The kit has a temporary-file test for additional locations; it does not exercise nested relative imports or a container volume.', 'RelaySettingsProcessTest now checks a relative import beneath a declaring file while the child starts in another directory. A container volume remains untested.'),
  ('The source kit tests a missing required import and a missing optional file, not nested relative resolution', 'RelaySettingsProcessTest.relativeImportUsesItsDeclaringFileOutsideTheWorkingDirectory checks a relative child-file import; a second nested import remains untested')],
 'spring/boot-config-source-matrix': [
  ('No test sets a real process environment variable or reads a deployment-mounted config file.', 'RelaySettingsProcessTest now sets real child-process environment values and reads local relative config imports. A deployment-mounted file and secret source remain untested.')],
}
for path, replacements in revisions.items():
    row = by[path]
    for before, after in replacements:
        if before in row['body']:
            row['body'] = row['body'].replace(before, after)
        elif before in row['data'].get('verification_suite',''):
            row['data']['verification_suite'] = row['data']['verification_suite'].replace(before, after)
        else:
            raise AssertionError((path,before))
    row['updated_at'] = stamp

reverse = {'spring/boot-environment-variable-binding':['spring/boot-env-process-binding'],
           'spring/boot-relative-config-import':['spring/boot-relative-import-process'],
           'spring/boot-config-source-matrix':['spring/boot-env-cli-precedence','spring/boot-config-process-test-boundary'],
           'spring/boot-required-config-import':['spring/boot-missing-import-process'],
           'spring/testing-boundaries':['spring/boot-config-process-test-boundary']}
for path, targets in reverse.items():
    row = by[path]
    row['body'] += '<h2>Checked process continuation</h2>' + paragraph('Continue with ' + ', '.join('[[' + target + '|' + titles[target] + ']]' for target in targets) + '.')
    row['updated_at'] = stamp

quiz_path = 'quizzes/spring-config-process'
assert quiz_path not in by
questions = [
 ('Which environment name binds relay.batch-size in the checked probe?', ['RELAY_BATCHSIZE','RELAY_BATCH_SIZE','RELAY.BATCH-SIZE'],0,'The canonical environment spelling removes the dash.'),
 ('What value is bound when RELAY_BATCHSIZE is 29 and no CLI override exists?', ['29','8','31'],0,'The child inherits 29 and the fallback of 8 is replaced.'),
 ('What timeout is bound from RELAY_TIMEOUT=750ms?', ['750 milliseconds','750 seconds','Two seconds'],0,'The explicit unit is parsed as milliseconds.'),
 ('Why launch a child JVM for this check?', ['To test an actual inherited process environment','To replace bean validation','To simulate a production container'],0,'The parent test sets environment entries on the child process.'),
 ('What wins when the environment says 29 and the CLI says 31?', ['The CLI value 31','The environment value 29','The default value 8'],0,'The child test asserts the effective value 31.'),
 ('What happens when RELAY_BATCHSIZE=0?', ['Startup fails before a bound result is printed','The default of 8 silently wins','The worker runs zero rows'],0,'The bean constraint rejects the selected value.'),
 ('Which file declares the relative import in the local test?', ['config/application.properties','launch/application.properties','the Maven POM'],0,'The import is written into the config directory application file.'),
 ('Where does relay/worker.properties resolve?', ['Under config, beside the declaring file','Under the child launch directory','Under the test classpath root'],0,'The child starts elsewhere but binds the imported value.'),
 ('What batch value comes from the imported worker file?', ['29','17','8'],0,'The imported file replaces the declaring file batch value.'),
 ('What happens when a required relative import is absent?', ['The child exits nonzero','The child uses the default and exits zero','The importer creates an empty file'],0,'The required import prevents successful startup.'),
 ('Does the child-process test prove a container secret mount works?', ['No','Yes','Only when the timeout is 750ms'],0,'It uses local temporary files and plain environment values.'),
 ('What should a production diagnostic avoid printing?', ['Secret values','A non-secret batch count','The exit status'],0,'The local probe prints only non-secret values.'),
]
quiz = by['quizzes/spring-boot-startup'].copy()
quiz.update(id=str(uuid.uuid5(uuid.NAMESPACE_URL,'https://aitrove.in/'+quiz_path)),path=quiz_path,
    title='Spring Boot process configuration quiz',summary='Twelve explained checks on environment binding, precedence, validation and relative imports.',
    sort_order=1300,published_at=stamp,created_at=stamp,updated_at=stamp)
quiz['body'] = paragraph('Check the child-process configuration contract and its deployment limits.') + '<h2>Review before answering</h2><ul>' + ''.join('<li><a href="/' + path + '">' + html.escape(titles[path]) + '</a></li>' for path in ['spring/boot-env-process-binding','spring/boot-env-cli-precedence','spring/boot-env-validation-failure','spring/boot-relative-import-process','spring/boot-missing-import-process']) + '</ul><h3>Common Mistakes</h3><ul><li>Do not confuse environment spelling with property spelling.</li><li>Do not call a temporary directory a mounted volume.</li><li>Do not infer a successful import from a process that merely starts.</li></ul>'
quiz['data'] = {'questions':[{'prompt':prompt,'options':options,'answer':answer,'explanation':explanation} for prompt,options,answer,explanation in questions],
    'duration_minutes':12,'subject_root':'spring/spring-boot','section_path':'spring/quizzes','content_format':'html','seo_ready':True}
rows.append(quiz)
hub = by['spring/quizzes']
hub['data']['modules'].append({'title':'Process configuration','summary':'Twelve questions tied to five child-JVM checks.','lessons':[quiz_path]})
hub['updated_at'] = stamp
if '<h2>Section lessons</h2>' in hub['body']:
    links = '<ul>' + ''.join('<li><a href="/' + path + '">' + html.escape({**titles,quiz_path:quiz['title']}[path]) + '</a></li>' for module in hub['data']['modules'] for path in module['lessons']) + '</ul>'
    hub['body'] = re.sub(r'(<h2>Section lessons</h2>)[\s\S]*?(<h2>Continue learning</h2>)', lambda match: match[1]+links+match[2],hub['body'])

FILE.write_text(json.dumps(rows,ensure_ascii=False,indent=2)+'\n')
print(json.dumps({'articles':len(lessons),'questions':len(questions),'paths':['spring/'+x['slug'] for x in lessons]}))
