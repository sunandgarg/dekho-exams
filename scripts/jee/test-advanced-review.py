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
    for mutation in ('missing-declaration', 'wrong-original', 'wrong-source'):
        bad = copy.deepcopy(entry)
        if mutation == 'missing-declaration': bad.pop('supersedesKey')
        if mutation == 'wrong-original': bad['supersedesKey'] = {}
        if mutation == 'wrong-source': bad['officialKey']['url'] = 'https://example.com/key.pdf'
        try:
            check(original, bad)
        except AssertionError:
            continue
        raise AssertionError(mutation)
print('Official correction guards passed')
