"""Build reviewed Advanced timed papers and balanced practice sets without changing official marking claims."""
from pathlib import Path
from hashlib import sha256
from collections import defaultdict, Counter
import gzip, json, re, math
ROOT = Path(__file__).resolve().parents[2]
ARCHIVE = ROOT / 'public/jee-advanced-archive'
OUT = ROOT / 'src/generated/jee-advanced-mocks'
KEYS = ('choiceKey', 'choiceKeys', 'numericKey', 'numericRange')
SUBJECTS = ('physics', 'chemistry', 'mathematics')


def reviewed_key(item, entry):
    key = entry.get('key', {})
    assert not key or len(key) == 1 and set(key) <= set(KEYS)
    original = {k: item[k] for k in KEYS if k in item}
    if 'supersedesKey' in entry:
        # Official corrections name the exact archived key; raw records stay immutable.
        assert original == entry['supersedesKey'] and set(key) == set(original)
        proof = entry.get('officialKey') or entry['pdfKeyReview']
        source = proof
        if 'officialKey' not in entry:
            # A supplied final-key table also needs the matched official question paper.
            assert re.fullmatch(r'Year-wise/\d{4}/DekhoExams_JEE_Advanced_\d{4}_Paper_[12]\.pdf', proof['file'])
            assert proof['keyPages'] and all(isinstance(n, int) and n > 0 for n in proof['keyPages'])
            source = proof['questionPaper']
        assert source['url'].startswith('https://jeeadv.ac.in/past_qps/')
        assert re.fullmatch('[a-f0-9]{64}', source['pdfSha256'])
        assert re.fullmatch('[a-f0-9]{64}', proof['pdfSha256']) and proof['printedKey']
    else:
        assert not any(k in item and item[k] != v for k, v in key.items())
    return key


def build():
    approved = json.loads((ROOT / 'src/data/approved-diagrams.json').read_text())
    review = json.loads((ROOT / 'scripts/jee/advanced-pdf-review.json').read_text())
    raw = {}
    for file in sorted((ARCHIVE / 'q').glob('*.bin')):
        raw.update(json.loads(gzip.decompress(file.read_bytes())))
    records, reader, applied = {}, {}, set()
    def checked(html):
        def image(m):
            src = re.search(r'\ssrc="([^"]+)"', m[0])
            path = src[1].split('?')[0] if src else ''
            return m[0].replace(src[0], ' src="'+path+'?v='+approved[path]+'"', 1) if path in approved else '<span class="jee-figure-pending">Diagram pending review</span>'
        return re.sub(r'<img\b[^>]*>', image, html)
    for slug, q in raw.items():
        if q.get('canonical'): continue
        assert q['complete'] and q['body']
        item = {k:q[k] for k in ('body', 'subject', 'options', 'solution', 'kind', *KEYS) if k in q}
        h = sha256(json.dumps([q['body'], q['options']], ensure_ascii=False).encode()).hexdigest()
        entry = review.get(h, {})
        if entry: applied.add(h)
        patch = {}
        if entry.get('hold'):
            for k in KEYS: item.pop(k, None)
            item['review'] = 'Answer key conflict'
            patch = {'hold': True}
        else:
            key = reviewed_key(item, entry)
            item.update(key); patch.update(key)
        if entry.get('figures') and not entry.get('hold'):
            pieces = [item['body'], *item['options']]
            used = set()
            for slot, part in enumerate(pieces):
                occurrence = 0
                def replacement(m):
                    nonlocal occurrence
                    match = next((fig for fig in entry['figures'] if fig['slot']==slot and fig['occurrence']==occurrence), None)
                    occurrence += 1
                    if not match: return m[0]
                    assert (m[1] or m[2]) == match['expected'] and match['path'] in approved
                    used.add((slot,occurrence-1))
                    return '<img src="'+match['path']+'" alt="Question diagram" loading="lazy">'
                pieces[slot] = re.sub(r'<span class="jee-figure-pending" data-figure="([^"]+)"[^>]*>[^<]*</span>|<img\b[^>]*\ssrc="([^"]+)"[^>]*>', replacement, part)
            assert len(used) == len(entry['figures'])
            item['body'], item['options'] = pieces[0], pieces[1:]
            patch.update(body=pieces[0], options=pieces[1:])
        if patch: reader[h] = patch
        item.update(body=checked(item['body']), options=[checked(o) for o in item['options']], solution=checked(item['solution']))
        if 'review' not in item:
            if any('jee-figure-pending' in s for s in [item['body'], *item['options']]): item['review'] = 'Diagram pending'
            elif not any(k in item for k in KEYS): item['review'] = 'Answer key unavailable'
        if any(k in item for k in KEYS):
            assert q['kind'] in ('mcq', 'mcqm', 'integer', 't/f')
            assert all(i in range(len(q['options'])) for i in item.get('choiceKeys', [item['choiceKey']] if 'choiceKey' in item else []))
            assert all(math.isfinite(n) for n in item.get('numericRange', [item['numericKey']] if 'numericKey' in item else []))
        records[slug] = item
    assert applied == set(review), 'PDF evidence must still match the original source exactly'
    OUT.mkdir(parents=True, exist_ok=True)
    emitted = set()
    def save(id, rows):
        data = json.dumps(rows, ensure_ascii=False, separators=(',', ':'))
        assert not re.search(r'exam\s*(?:side|goal)|watermark|<(?:script|iframe)\b|(?:src|href)="(?:https?:)?//', data, re.I)
        target = OUT / f'{id}.{len(rows)}.json.gz'
        target.write_bytes(gzip.compress(data.encode(), compresslevel=6, mtime=0)); emitted.add(target)
    used = set()
    for file in sorted((ARCHIVE / 'paper').glob('*.bin')):
        ids = [raw[r['id']].get('canonical', r['id']) for r in json.loads(gzip.decompress(file.read_bytes()))]
        assert len(ids)==len(set(ids)) and not used.intersection(ids)
        used.update(ids); save(file.stem, [records[k] for k in ids])
    paper_positions = len(used)
    for subject in SUBJECTS:
        ids = sorted(k for k in records.keys()-used if records[k]['subject']==subject)
        for i in range(0, len(ids), 25): save(f'extra-{subject}-{i//25+1:02}', [records[k] for k in ids[i:i+25]])
        used.update(ids)
    assert used==records.keys()
    pools, seen = defaultdict(list), set()
    for q in records.values():
        if q.get('review') or not q['solution'] or 'jee-figure-pending' in q['solution']: continue
        h = sha256(json.dumps([q['body'],q['options']],ensure_ascii=False).encode()).digest()
        if h in seen: continue
        seen.add(h); pools[q['subject']].append(q)
    n = 0
    while all(len(pools[s])>=20 for s in SUBJECTS):
        n += 1; rows=[]
        for subject in SUBJECTS: rows.extend(pools[subject][:20]); del pools[subject][:20]
        save(f'mixed-{n:02}', rows)
    assert n > 0
    for old in OUT.glob('*.json.gz'):
        if old not in emitted: old.unlink()
    (OUT/'reader.json').write_text(json.dumps(reader,ensure_ascii=False,separators=(',',':')))
    remaining=Counter();scored=0
    for q in records.values():
        key=any(k in q for k in KEYS);diagram=any('jee-figure-pending' in s for s in [q['body'],*q['options']])
        if q.get('review')=='Answer key conflict': remaining['conflict']+=1
        elif not key and diagram: remaining['key_and_diagram']+=1
        elif not key: remaining['key']+=1
        elif diagram: remaining['diagram']+=1
        else: scored+=1
    stats=dict(questions=len(records),scored=scored,remaining=remaining,paperPositions=paper_positions,papers=len(list((ARCHIVE/'paper').glob('*.bin'))),mixedMocks=n,mixedQuestions=n*60,recoveredKeys=sum('key' in v for v in review.values()),recoveredDiagrams=sum(len(v.get('figures',[])) for v in review.values()))
    (OUT/'stats.json').write_text(json.dumps(stats,indent=2)+'\n');print(json.dumps(stats))

if __name__=='__main__': build()
