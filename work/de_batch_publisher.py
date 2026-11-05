"""Small shared publisher for editorial Data Engineering batches."""
import datetime
import html
import json
import re
import uuid
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
FIXTURE = ROOT / 'src/data/fixtures.json'
def publish(lessons, modules, crosslinks, import_name, sort_start, subject='data-engineering', hub_path=None):
    hub_path = hub_path or f'{subject}/{subject}-tutorial'
    project_hub_path = hub_path + '/project'
    rows = json.loads(FIXTURE.read_text())
    paths = {item['path'] for item in lessons}
    assert len(paths) == len(lessons) >= 6
    rows = [row for row in rows if row['path'] not in paths]
    by_path = {row['path']: row for row in rows}
    titles = {path: row['title'] for path, row in by_path.items()}
    titles.update({item['path']: item['title'] for item in lessons})
    now = datetime.datetime.now(datetime.UTC).isoformat()

    def prose(value):
        return re.sub(r'\[\[([^|]+)\|([^\]]+)\]\]',
                      lambda match: '<a href="/' + match[1] + '">' + match[2] + '</a>',
                      html.escape(value))

    def link_list(targets):
        return '<ul>' + ''.join('<li><a href="/' + target + '">' +
                               html.escape(titles[target]) + '</a></li>' for target in targets) + '</ul>'

    changed = set(paths) | {hub_path, project_hub_path}
    for index, item in enumerate(lessons):
        for target in item['related']:
            assert target in titles, target
        body = '<p>' + html.escape(item['summary']) + '</p>'
        for heading, paragraph in item['sections']:
            body += '<h2>' + html.escape(heading) + '</h2><p>' + prose(paragraph) + '</p>'
        body += ('<h2>Implementation</h2><pre><code class="language-python">' +
                 html.escape(item['code']) + '</code></pre>' +
                 '<h2>Performance and operating cost</h2><p>' + html.escape(item['cost']) +
                 '</p><h3>Common Mistakes</h3><ul>' +
                 ''.join('<li>' + html.escape(mistake) + '</li>' for mistake in item['mistakes']) +
                 '</ul><h2>Read next</h2>' + link_list(item['related']))
        path = item['path']
        row = dict(id=str(uuid.uuid5(uuid.NAMESPACE_URL, 'https://aitrove.in/' + path)),
                   type='article', path=path, title=item['title'], summary=item['summary'], body=body,
                   category='AI & Data', subject=subject + '-project' if item['project'] else subject,
                   difficulty='Advanced', tags=['ai-data', subject], potd_date=None,
                   featured=False, sort_order=sort_start + index, status='published',
                   published_at=now, created_at=now, updated_at=now,
                   data={'subject_root': hub_path, 'section_path': project_hub_path if item['project'] else hub_path,
                         'content_format': 'html', 'seo_ready': True,
                         'kind': 'project' if item['project'] else 'tutorial',
                         'reading_minutes': max(5, len(re.sub(r'<[^>]+>', ' ', body).split()) // 180),
                         'author_path': 'authors/aitrove-editorial',
                         'verification_suite': 'Editorial, code and internal-link checks',
                         'related': [{'path': target, 'title': titles[target]} for target in item['related']]})
        rows.append(row)
        by_path[path] = row

    hub, project_hub = by_path[hub_path], by_path[project_hub_path]
    for module_title in modules:
        lesson_paths = [item['path'] for item in lessons if item['module'] == module_title and not item['project']]
        project_paths = [item['path'] for item in lessons if item['module'] == module_title and item['project']]
        assert len(lesson_paths) >= 2 and len(project_paths) == 1
        if not any(module['title'] == module_title for module in hub['data']['modules']):
            hub['data']['modules'].insert(-1, {'title': module_title,
                                               'summary': 'Inspect the failure boundary and complete the applied release.',
                                               'lessons': lesson_paths})
        practice = next(module for module in hub['data']['modules'] if module['title'] == 'Apply your knowledge')
        if project_paths[0] not in practice['lessons']:
            practice['lessons'].append(project_paths[0])
        if '<h2>' + module_title + '</h2>' not in hub['body']:
            hub['body'] += '<h2>' + module_title + '</h2>' + link_list(lesson_paths)
            hub['body'] += '<h2>' + module_title + ' project</h2>' + link_list(project_paths)
        if project_paths[0] not in project_hub['data']['modules'][0]['lessons']:
            project_hub['data']['modules'][0]['lessons'].append(project_paths[0])
        if project_paths[0] not in project_hub['body']:
            project_hub['body'] += '<h2>' + module_title + '</h2>' + link_list(project_paths)
    hub['updated_at'] = project_hub['updated_at'] = now

    for source, target in crosslinks:
        assert source in by_path and target in by_path, (source, target)
        changed.add(source)
        row = by_path[source]
        anchor = ('<p><strong>Continue the workflow:</strong> <a href="/' + target + '">' +
                  html.escape(titles[target]) + '</a>.</p>')
        if anchor not in row['body']:
            row['body'] += anchor
            row['data'].setdefault('related', []).append({'path': target, 'title': titles[target]})
            row['updated_at'] = now
    assert len({row['path'] for row in rows}) == len(rows)
    FIXTURE.write_text(json.dumps(rows, ensure_ascii=False, indent=2) + '\n')
    import_path = ROOT / 'work' / import_name
    import_path.write_text(json.dumps([by_path[path] for path in sorted(changed)], ensure_ascii=False, indent=2) + '\n')
    print(json.dumps({'new_articles': len(lessons), 'new_projects': sum(item['project'] for item in lessons),
                      'crosslinks': len(crosslinks), 'import_rows': len(changed),
                      'import_path': str(import_path)}))
