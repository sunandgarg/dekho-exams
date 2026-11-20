"""Official corrections must fail closed when their archived key changes."""
import copy
import json
import runpy
from pathlib import Path

root = Path(__file__).resolve().parents[2]
check = runpy.run_path(str(Path(__file__).with_name('build-advanced-mocks.py')))['reviewed_key']
ledger = json.loads((root / 'scripts/jee/advanced-pdf-review.json').read_text())
corrections = [e for e in ledger.values() if 'supersedesKey' in e]
assert len(corrections) >= 2
for entry in corrections:
    original = entry['supersedesKey']
    assert check(original, entry) == entry['key']
    mutations = ['missing-declaration', 'wrong-original', 'wrong-source', 'wrong-evidence']
    if 'officialKey' not in entry: mutations += ['wrong-file', 'missing-key-page']
    for mutation in mutations:
        bad = copy.deepcopy(entry)
        if mutation == 'missing-declaration': bad.pop('supersedesKey')
        if mutation == 'wrong-original': bad['supersedesKey'] = {}
        proof = bad.get('officialKey') or bad['pdfKeyReview']
        if mutation == 'wrong-source':
            (proof if 'officialKey' in bad else proof['questionPaper'])['url'] = 'https://example.com/key.pdf'
        if mutation == 'wrong-evidence': proof['pdfSha256'] = ''
        if mutation == 'wrong-file': proof['file'] = 'unverified.pdf'
        if mutation == 'missing-key-page': proof['keyPages'] = []
        try:
            check(original, bad)
        except AssertionError:
            continue
        raise AssertionError(mutation)
print('Official correction guards passed')

# Supplied-PDF transcription patches must be tied to the exact archived question.
content = runpy.run_path(str(Path(__file__).with_name('build-advanced-mocks.py')))['reviewed_content']
patches = [e for e in ledger.values() if 'contentCorrection' in e and 'officialKey' not in e]
assert patches
for entry in patches:
    correction = entry['contentCorrection']
    original = {'body': correction['originalBody'], 'options': correction['originalOptions']}
    assert content(original, entry) == correction['replacement']
    for mutation in ['wrong-original', 'wrong-file', 'missing-key-page', 'wrong-hash', 'wrong-order', 'key-override', 'missing-body', 'missing-option', 'unreviewed-solution']:
        bad = copy.deepcopy(entry)
        proof = bad['pdfKeyReview']
        if mutation == 'wrong-original': bad['contentCorrection']['originalBody'] += ' changed'
        if mutation == 'wrong-file': proof['file'] = 'unverified.pdf'
        if mutation == 'missing-key-page': proof['keyPages'] = []
        if mutation == 'wrong-hash': proof['pdfSha256'] = 'invalid'
        if mutation == 'wrong-order': proof['localToPdfOptionOrder'] = []
        if mutation == 'key-override': bad['supersedesKey'] = {'choiceKey': 0}
        if mutation == 'missing-body': bad['contentCorrection']['replacement']['body'] = ''
        if mutation == 'missing-option': bad['contentCorrection']['replacement']['options'].pop()
        if mutation == 'unreviewed-solution': bad['contentCorrection']['replacement']['solution'] = 'Old explanation'
        try:
            content(original, bad)
        except AssertionError:
            continue
        raise AssertionError(mutation)
print('Supplied-PDF transcription guards passed')
