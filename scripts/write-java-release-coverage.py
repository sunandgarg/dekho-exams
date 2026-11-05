"""Export the current curriculum, its tested scope, and explicit remaining work."""
import ast, html, json, pathlib, re

ROOT = pathlib.Path(__file__).resolve().parents[1]
OUT = ROOT.parent.parent / 'outputs'
entries = json.loads((ROOT / 'src/data/fixtures.json').read_text())
lookup = {e['path']: e for e in entries}
batch = json.loads((OUT / 'java-release-batch.json').read_text())
enrichment = json.loads((OUT / 'java-release-link-changes.json').read_text())
programs = json.loads((OUT / 'java-program-check.json').read_text())
prior = ast.parse((ROOT / 'scripts/write-java-depth-coverage.py').read_text())
values = {n.targets[0].id: ast.literal_eval(n.value) for n in prior.body
          if isinstance(n, ast.Assign) and isinstance(n.targets[0], ast.Name)
          and n.targets[0].id in {'remaining', 'sources'}}
remaining = values['remaining']
remaining['java/advanced-java'][:2] = [
    'Native function linking, shared foreign-memory ownership and wider Java 25/library coverage. The new confined Arena fixture covers allocation, alignment, bounds and lifetime only.',
    'Full Spring/Jakarta, Swing and JavaFX tracks. The new SwingWorker and Java2D examples are bounded introductions, not complete desktop tracks.']
remaining['java/java'].append('Broader locale selection, message formatting, encoding and real configuration-source integration.')
remaining['java/java-projects'].append('Filesystem ZIP extraction with symlink-race protection and durable publication. The new example stages bounded bytes in memory; it does not write files.')
sources = values['sources'] + [
    ('Arena, Java 25', 'https://docs.oracle.com/en/java/javase/25/docs/api/java.base/java/lang/foreign/Arena.html'),
    ('VarHandle ordering', 'https://docs.oracle.com/en/java/javase/25/docs/api/java.base/java/lang/invoke/VarHandle.html'),
    ('ServiceLoader', 'https://docs.oracle.com/javase/8/docs/api/java/util/ServiceLoader.html'),
    ('ResourceBundle', 'https://docs.oracle.com/javase/8/docs/api/java/util/ResourceBundle.html'),
    ('Properties', 'https://docs.oracle.com/javase/8/docs/api/java/util/Properties.html'),
    ('SwingWorker', 'https://docs.oracle.com/javase/8/docs/api/javax/swing/SwingWorker.html'),
    ('BufferedImage', 'https://docs.oracle.com/javase/8/docs/api/java/awt/image/BufferedImage.html'),
    ('AbstractProcessor', 'https://docs.oracle.com/javase/8/docs/api/javax/annotation/processing/AbstractProcessor.html'),
    ('LongAdder', 'https://docs.oracle.com/javase/8/docs/api/java/util/concurrent/atomic/LongAdder.html'),
    ('ZIP input', 'https://docs.oracle.com/javase/8/docs/api/java/util/zip/ZipInputStream.html'),
    ('HashMap API', 'https://docs.oracle.com/javase/8/docs/api/java/util/HashMap.html'),
    ('OpenJDK 8u HashMap implementation', 'https://github.com/openjdk/jdk8u/blob/master/jdk/src/share/classes/java/util/HashMap.java'),
    ('EnumMap', 'https://docs.oracle.com/javase/8/docs/api/java/util/EnumMap.html'),
    ('EnumSet', 'https://docs.oracle.com/javase/8/docs/api/java/util/EnumSet.html'),
    ('BigDecimal', 'https://docs.oracle.com/javase/8/docs/api/java/math/BigDecimal.html')]
routes = {e['path'] for e in entries if e['path'].startswith('java/') or e['type'] == 'quiz' and e.get('subject') == 'java-quizzes'}
assert len(routes) == 219
new = set(batch['added']); expanded = set(batch['expanded'])
linked = {e['path'] for e in enrichment['plan']}
sections = []; reached = set()
for tab in lookup['java/java']['data']['resource_tabs']:
    hub = lookup[tab['path']]; modules = []
    for module in hub['data']['modules']:
        lessons = []
        for path in module['lessons']:
            assert path in routes, path
            status = 'new' if path in new else 'expanded' if path in expanded else 'linked' if path in linked else 'existing'
            lessons.append({'path': path, 'title': lookup[path]['title'], 'status': status})
            reached.add(path)
        modules.append({'title': module['title'], 'lessons': lessons})
    reached.add(hub['path'])
    sections.append({'path': hub['path'], 'title': tab['title'], 'modules': modules, 'remaining': remaining[hub['path']]})
assert reached == routes, routes - reached
kit = ROOT / 'work/java-finish/source-kit'
manifest = json.loads((kit / 'manifest.json').read_text())
report = {**batch, 'javaRoutes': len(routes), 'additionalBodyLinks': enrichment['addedLinks'],
          'sourcePrograms': len(manifest), 'sections': sections, 'sources': sources,
          'verification': {'programs': programs},
          'remaining': 'Selected curriculum populated; exhaustive Java/library coverage, real CMS import, deployment, authenticated progress and server judging remain.'}
if (OUT / 'java-release-browser-check.json').exists():
    report['verification']['browser'] = json.loads((OUT / 'java-release-browser-check.json').read_text())
(OUT / 'java-release-coverage.json').write_text(json.dumps(report, indent=2) + '\n')
(OUT / 'aitrove-java-full-content.json').write_text(json.dumps([e for e in entries if e['path'] in routes], indent=2, ensure_ascii=False) + '\n')
(OUT / 'aitrove-reviewed-publish-content.json').write_text(json.dumps([e for e in entries if e['data'].get('seo_ready') is True], indent=2, ensure_ascii=False) + '\n')
previous = (OUT / 'java-next-coverage.html').read_text()
style = previous.split('<style>')[1].split('</style>')[0]
script = previous.split('<script>')[1].split('</script>')[0].replace("state==='expanded'", "state==='expanded'||state==='linked'")
branches = []
for section in sections:
    groups = []
    for module in section['modules']:
        items = ''.join('<li data-status="'+l['status']+'"><a href="http://127.0.0.1:3001/'+l['path']+'">'+html.escape(l['title'])+'</a> <span>'+l['status']+'</span></li>' for l in module['lessons'])
        groups.append('<details open><summary>'+html.escape(module['title'])+'</summary><ul>'+items+'</ul></details>')
    groups.append('<details class="remaining" open><summary>Still remaining</summary><ul>'+''.join('<li>'+html.escape(s)+'</li>' for s in section['remaining'])+'</ul></details>')
    branches.append('<section class="branch"><h2><a href="http://127.0.0.1:3001/'+section['path']+'">'+html.escape(section['title'])+'</a></h2>'+''.join(groups)+'</section>')
intro = f'<p><strong>219 routes: 195 articles, 10 hubs, 14 quizzes and 168 questions.</strong></p><p>This pass adds ten lessons, expands four, adds {enrichment["addedLinks"]} useful body links and writes specific preparation for all fourteen quizzes. Existing means present, not exhaustive API coverage.</p><p>{programs["programsAndFragmentsCompiled"]} compiled code units, {programs["programsAndFragmentsExecuted"]} executions and {programs["declaredOutputsChecked"]} matched outputs, targeting releases 8, 11, 17, 21 and 25. The source kit contains {len(manifest)} complete standalone source units and 203 source/build/documentation files. Prior unchanged dependency/property suites are recorded separately.</p><p><a href="http://127.0.0.1:3001/java/java">Open Java</a> · <a href="http://127.0.0.1:3001/quizzes/java-25">Java 25 quiz</a> · <a href="http://127.0.0.1:3001/downloads/aitrove-java-source-kit.zip" download>Download source kit</a></p>'
doc = '<!doctype html><html lang="en"><head><meta charset="utf-8"><meta name="viewport" content="width=device-width,initial-scale=1"><meta name="robots" content="noindex,follow"><title>AI Trove Java coverage</title><style>'+style+'</style></head><body><main><h1>Java · completed and remaining</h1><div class="intro">'+intro+'</div><div class="controls"><input id="find" aria-label="Find a topic" placeholder="Find a topic"><select id="show" aria-label="Show"><option value="all">All coverage</option><option value="new">New, expanded and linked</option><option value="remaining">Remaining only</option></select></div>'+''.join(branches)+'<p>WordPress import and live deployment are separate from the GitHub review branch. Preview stays out of search indexing until launch.</p></main><script>'+script+'</script></body></html>'
(OUT / 'java-release-coverage.html').write_text(doc)
(ROOT / 'public/java-coverage.html').write_text(doc)
lines = ['# AI Trove Java publishing handoff', '', '219 Java routes: 195 articles, 10 hubs, 14 quiz banks and 168 questions. Ten new lessons, four expanded lessons, 195 added links and fourteen specific quiz preparation pages. Quiz landings share the reading shell; previous/next links use curriculum order.', '',
         '## Writing and verification', '',
         'Fresh explanations, programs and teaching examples were written for AI Trove against verified contracts. Changing values in copied examples is not this workflow. Java facts/API syntax, third-party logos and dependency code are not exclusive AI Trove property. Generated text is not claimed to be human-authored, and detector outcomes are not guaranteed.', '',
         f'{programs["programsAndFragmentsCompiled"]} code units compiled, {programs["programsAndFragmentsExecuted"]} ran, and {programs["declaredOutputsChecked"]} declared outputs matched. All ten new programs were included. The kit contains 169 standalone JDK source units and 203 total source/build/documentation files. No binaries, JDK distribution, secrets or heap dumps are bundled.', '',
         'Prior unchanged tests: 22 Maven dependency cases; 5,085,835 algorithm/boundary checks; three rejected cross-package compilations; owned-process histogram/heap capture; named modules, Gradle and JMH execution smoke checks. H2 evidence does not establish another database engine behavior. Benchmark smoke checks do not rank implementations.', '',
         'The full Java import payload has 219 records; reviewed publish payload has 220 including the editorial profile. WordPress still needs the updated plugin, import and readiness metadata backfill. No CMS connection or production deployment is claimed.', '', '## Research', '',
         'The five requested sites were inspected in order for topic coverage. Primary API/source references verified contracts. Explanations and programs were not copied from their pages. This was targeted research, not an exhaustive crawl of the internet.', '']
lines += ['- ['+label+']('+url+')' for label, url in sources]
lines += ['', '## Completed skeleton and remaining scope', '']
for section in sections:
    lines += ['### '+section['title'], '', '['+section['path']+'](http://127.0.0.1:3001/'+section['path']+')', '']
    for module in section['modules']:
        lines.append('- '+module['title']+': '+str(len(module['lessons']))+' linked lessons.')
    lines += ['', 'Remaining:'] + ['- '+s for s in section['remaining']] + ['']
lines += ['Authenticated cross-device progress, real judging, production fault/load checks, broader frameworks/native interop and actual CMS publishing remain. The current Java curriculum is populated; all of Java is not complete.']
(OUT / 'java-release-editorial-handoff.md').write_text('\n'.join(lines)+'\n')
print(json.dumps({'routes':len(routes), 'programs':len(manifest), 'additionalLinks':enrichment['addedLinks']}))
