"""Validate the practical guide section and the vector/raster ML lesson."""
import ast
from html.parser import HTMLParser
import html
import json
from pathlib import Path
import re

root = Path(__file__).resolve().parents[1]
rows = json.loads((root / 'src/data/fixtures.json').read_text())
by_path = {row['path']: row for row in rows}
assert len(by_path) == len(rows), 'duplicate path'

class Body(HTMLParser):
    def __init__(self):
        super().__init__()
        self.tags = []
        self.links = []
        self.code = ''
        self.in_code = False

    def handle_starttag(self, tag, attrs):
        self.tags.append(tag)
        if tag == 'a':
            self.links.append(dict(attrs).get('href'))
        if tag == 'code':
            self.in_code = True

    def handle_endtag(self, tag):
        if tag == 'code':
            self.in_code = False

    def handle_data(self, data):
        if self.in_code:
            self.code += data

guide_root = 'guides/how-to-and-shortcuts'
guides = [row for row in rows if row['path'].startswith('guides/')]
articles = [row for row in guides if row['type'] == 'article']
assert len(guides) == 9 and len(articles) == 8
hub = by_path[guide_root]
module_paths = [path for module in hub['data']['modules'] for path in module['lessons']]
assert set(module_paths) == {row['path'] for row in articles}
assert len(module_paths) == len(set(module_paths))
allowed = {'p','h2','h3','ul','li','strong','a','pre','code'}
for row in guides + [by_path['machine-learning/vector-vs-raster-in-machine-learning']]:
    assert row['data']['content_format'] == 'html', row['path']
    assert 'http://' not in row['body'] and 'https://' not in row['body'], row['path']
    parser = Body()
    parser.feed(row['body'])
    assert set(parser.tags) <= allowed, (row['path'], set(parser.tags)-allowed)
    assert all(link and link.startswith('/') and link[1:] in by_path for link in parser.links), row['path']
    if row['type'] == 'article':
        words = len(re.sub(r'<[^>]+>', ' ', row['body']).split())
        assert words >= (340 if row['path'].startswith('machine-learning/') else 300), (row['path'], words)
        assert len(parser.links) >= 4, row['path']
        assert '<h3>Common Mistakes</h3>' in row['body'], row['path']

vector = Body()
vector.feed(by_path['machine-learning/vector-vs-raster-in-machine-learning']['body'])
scope = {}
ast.parse(html.unescape(vector.code))
exec(html.unescape(vector.code), scope)
mask = scope['box_to_mask'](8, 6, 31, 19, 47, 29)
assert len(mask) == 29 and all(len(row) == 47 for row in mask)
assert sum(map(sum, mask)) == 299
assert sum(map(sum, scope['box_to_mask'](-5, 1, -1, 3, 4, 4))) == 0
assert sum(map(sum, scope['box_to_mask'](99, 1, 100, 3, 4, 4))) == 0

assert 'machine-learning/vector-vs-raster-in-machine-learning' in [
    path for module in by_path['machine-learning/machine-learning-tutorial']['data']['modules']
    for path in module['lessons']]
assert guide_root in [path for module in by_path['websites-apps/software-and-tools-a-to-z-list']['data']['modules']
                      for path in module['lessons']]
for source in [root / 'src/lib/navigation.ts', root / 'src/components/cms/home.tsx']:
    assert guide_root in source.read_text(), str(source)

print(json.dumps({'passed':True, 'guide_articles':len(articles), 'guide_hubs':1,
                  'vector_article':1, 'linked_routes':len(module_paths)}))
