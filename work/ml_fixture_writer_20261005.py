"""Write a reviewed batch of original Machine Learning fixture lessons."""
import datetime
import html
import json
import re
import uuid
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
FIXTURE = ROOT / 'src/data/fixtures.json'
HUB = 'machine-learning/machine-learning-tutorial'
PROJECT_HUB = HUB + '/project'


def publish_batch(lessons, module_title, module_summary, project_heading,
                  crosslinks, sort_start):
    rows = json.loads(FIXTURE.read_text())
    new_paths = {item['path'] for item in lessons}
    assert len(new_paths) == len(lessons)
    rows = [row for row in rows if row['path'] not in new_paths]
    by_path = {row['path']: row for row in rows}
    titles = {path: row['title'] for path, row in by_path.items()}
    titles.update({item['path']: item['title'] for item in lessons})
    stamp = datetime.datetime.now(datetime.UTC).isoformat()

    def prose(value):
        return re.sub(r'\[\[([^|]+)\|([^\]]+)\]\]',
                      lambda match: '<a href="/' + match[1] + '">' + match[2] + '</a>',
                      html.escape(value))

    def link_list(targets):
        return '<ul>' + ''.join('<li><a href="/' + target + '">' + html.escape(titles[target]) + '</a></li>'
                                for target in targets) + '</ul>'

    for index, item in enumerate(lessons):
        path = item['path']
        is_project = path.endswith('-project')
        body = '<p>' + html.escape(item['summary']) + '</p>'
        for heading, paragraph in item['sections']:
            body += '<h2>' + html.escape(heading) + '</h2><p>' + prose(paragraph) + '</p>'
        body += ('<h2>Implementation</h2><pre><code class="language-python">' +
                 html.escape(item['code']) + '</code></pre>' +
                 '<h2>Performance and operating cost</h2><p>' + html.escape(item['cost']) + '</p>' +
                 '<h3>Common Mistakes</h3><ul>' +
                 ''.join('<li>' + html.escape(mistake) + '</li>' for mistake in item['mistakes']) +
                 '</ul><h2>Read next</h2>' + link_list(item['related']))
        row = dict(id=str(uuid.uuid5(uuid.NAMESPACE_URL, 'https://aitrove.in/' + path)),
                   type='article', path=path, title=item['title'], summary=item['summary'], body=body,
                   category='AI & Data', subject='machine-learning-project' if is_project else 'machine-learning',
                   difficulty='Advanced', tags=['ai-data', 'machine-learning'], potd_date=None,
                   featured=False, sort_order=sort_start + index, status='published', published_at=stamp,
                   created_at=stamp, updated_at=stamp,
                   data={'subject_root':HUB, 'section_path':PROJECT_HUB if is_project else HUB,
                         'content_format':'html', 'seo_ready':True,
                         'kind':'project' if is_project else 'tutorial',
                         'reading_minutes':max(5, len(re.sub(r'<[^>]+>', ' ', body).split()) // 180),
                         'author_path':'authors/aitrove-editorial',
                         'verification_suite':'Editorial, code and internal-link checks',
                         'related':[{'path':target, 'title':titles[target]} for target in item['related']]})
        rows.append(row)
        by_path[path] = row

    tutorial_paths = [item['path'] for item in lessons if not item['path'].endswith('-project')]
    project_paths = [item['path'] for item in lessons if item['path'].endswith('-project')]
    assert len(project_paths) == 1
    project_path = project_paths[0]
    hub = by_path[HUB]
    if not any(module['title'] == module_title for module in hub['data']['modules']):
        hub['data']['modules'].insert(-1, {'title':module_title,
                                          'summary':module_summary,
                                          'lessons':tutorial_paths})
    apply_module = next(module for module in hub['data']['modules']
                        if module['title'] == 'Apply your knowledge')
    if project_path not in apply_module['lessons']:
        apply_module['lessons'].append(project_path)
    if '<h2>' + module_title + '</h2>' not in hub['body']:
        hub['body'] += '<h2>' + module_title + '</h2>' + link_list(tutorial_paths)
        hub['body'] += '<h2>' + project_heading + '</h2>' + link_list([project_path])
    hub['updated_at'] = stamp

    project_hub = by_path[PROJECT_HUB]
    if project_path not in project_hub['data']['modules'][0]['lessons']:
        project_hub['data']['modules'][0]['lessons'].append(project_path)
    if '<h2>' + project_heading + '</h2>' not in project_hub['body']:
        project_hub['body'] += '<h2>' + project_heading + '</h2>' + link_list([project_path])
    project_hub['updated_at'] = stamp

    for source, target in crosslinks:
        source_row = by_path[source]
        anchor = ('<p><strong>Continue the workflow:</strong> <a href="/' + target + '">' +
                  html.escape(titles[target]) + '</a>.</p>')
        if anchor not in source_row['body']:
            source_row['body'] += anchor
            source_row['data'].setdefault('related', []).append({'path':target, 'title':titles[target]})
            source_row['updated_at'] = stamp

    assert len({row['path'] for row in rows}) == len(rows)
    FIXTURE.write_text(json.dumps(rows, ensure_ascii=False, indent=2) + '\n')
    print(json.dumps({'new_articles':len(lessons), 'new_projects':1,
                      'crosslinks_from_existing':len(crosslinks)}))
