"""Independent small-case and failure-boundary checks for the eighth Python pass."""
import contextlib
import html
import io
import itertools
import json
import pathlib
import random
import re
import unittest
from collections import Counter

ROOT = pathlib.Path(__file__).resolve().parents[2]
FIXTURES = ROOT / 'src/data/fixtures.json'
PROGRAMS = None
if FIXTURES.exists():
    PROGRAMS = {entry['path'].split('/')[-1]: html.unescape(re.search(
        r'<code class="language-python">([\s\S]*?)</code>', entry['body'])[1])
        for entry in json.loads(FIXTURES.read_text())
        if entry['type'] == 'article' and entry['path'].startswith('python/')}


def load(slug):
    source = PROGRAMS[slug] if PROGRAMS else pathlib.Path(__file__).with_name(slug.replace('-', '_') + '.py').read_text()
    namespace = {'__name__': '__main__'}
    with contextlib.redirect_stdout(io.StringIO()):
        exec(compile(source, slug, 'exec'), namespace)
    return namespace


ORACLES = {'starredEnvelopeCombinations': 250, 'multisetComparisons': 1200,
           'intervalPairwiseComparisons': 1200, 'clockBoundaryCases': 1001,
           'totalFrequencyComparisons': 1000, 'archiveMutationComparisons': 400, 'stableDedupeComparisons': 500,
           'assignmentReaderCases': 50}


class AssuranceChecks(unittest.TestCase):
    def test_starred_envelope_combinations(self):
        decode = load('starred-unpacking')['decode_envelope']
        rng = random.Random(20260929)
        for _ in range(ORACLES['starredEnvelopeCombinations']):
            payload = [rng.choice(('DEL', 'R41', 'BOM')) for _ in range(rng.randrange(1, 4))]
            checksum = sum(map(len, payload))
            self.assertEqual(decode(('v1', *payload, checksum)), payload)
            with self.assertRaises(ValueError):
                decode(('v1', *payload, checksum + 1))
        for bad in (['v1', 'R41', 3, 'extra', 'overflow'], ('v1',), ('v1', True, 0)):
            with self.assertRaises(ValueError):
                decode(bad)

    def test_comparison_and_import_lifetime(self):
        chain = load('comparison-chains')
        self.assertEqual(chain['reads'], ['ledger', 'ledger'])
        cache = load('import-cache-ownership')
        self.assertIs(cache['first'], cache['second'])
        self.assertIsNot(cache['first'], cache['third'])
        self.assertEqual(cache['third'].starts, 1)

    def test_context_suppression_and_key_invariant(self):
        guard = load('context-exit-suppression')['FailureGuard']
        with self.assertRaises(RuntimeError):
            with guard(suppress=True):
                raise RuntimeError('unhandled')
        with self.assertRaises(ValueError):
            with guard(suppress=False):
                raise ValueError('owned')
        receipt_key = load('hash-key-mutation-interview')['ReceiptKey']
        key = receipt_key('R41')
        original_hash = hash(key)
        key.identifier = 'R42'
        self.assertEqual(key, receipt_key('R42'))
        self.assertEqual(original_hash, hash('R41'))
        self.assertEqual(hash(key), hash('R42'))

    def test_multiset_independent_frequency_oracle(self):
        gaps = load('multiset-diff-exercise')['receipt_gaps']
        rng = random.Random(41)
        alphabet = ['R41', 'R42', 'R43', 'R44']
        for _ in range(ORACLES['multisetComparisons']):
            due = rng.choices(alphabet, k=rng.randrange(0, 15))
            scanned = rng.choices(alphabet, k=rng.randrange(0, 15))
            oracle_due = [(key, due.count(key) - scanned.count(key)) for key in alphabet if due.count(key) > scanned.count(key)]
            oracle_seen = [(key, scanned.count(key) - due.count(key)) for key in alphabet if scanned.count(key) > due.count(key)]
            self.assertEqual(gaps(due, scanned), (oracle_due, oracle_seen))
            self.assertEqual(gaps(due, scanned), gaps(due.copy(), scanned.copy()))
        for bad in ([True], ['R４１'], ['R4'], ['r41']):
            with self.assertRaises(ValueError):
                gaps(bad, [])

    def test_half_open_intervals_against_all_pairs(self):
        check = load('interval-conflict-exercise')['no_conflicts']
        rng = random.Random(90)
        for _ in range(ORACLES['intervalPairwiseComparisons']):
            spans = []
            for _ in range(rng.randrange(0, 12)):
                start = rng.randrange(0, 100)
                spans.append((start, start + rng.randrange(1, 15)))
            before = spans.copy()
            oracle = all(not (left[0] < right[1] and right[0] < left[1])
                         for left, right in itertools.combinations(spans, 2))
            self.assertEqual(check(spans), oracle)
            self.assertEqual(spans, before)
        for bad in ([(0, 0)], [(1, True)], [(0, 1441)], [(4, 2)]):
            with self.assertRaises(ValueError):
                check(bad)

    def test_fake_clock_at_every_small_boundary(self):
        active = load('fake-clock-tests')['active_lease']
        for now in range(ORACLES['clockBoundaryCases']):
            expiry = 500
            self.assertEqual(active(now, expiry), now in range(expiry))
        for args in ((True, 10), (10, False), (-1, 10), (10, 100001)):
            with self.assertRaises(ValueError):
                active(*args)

    def test_total_against_frequency_formula(self):
        total = load('metamorphic-reconciliation')['receipt_total']
        rng = random.Random(99)
        for _ in range(ORACLES['totalFrequencyComparisons']):
            batch = [rng.randrange(0, 101) for _ in range(rng.randrange(0, 21))]
            expected = sum(amount * count for amount, count in Counter(batch).items())
            self.assertEqual(total(batch), expected)
            self.assertEqual(total(list(reversed(batch))), expected)
        with self.assertRaises(ValueError):
            total([0] * 21)

    def test_patch_and_autospec_boundaries(self):
        patch = load('patch-lookup-tests')
        self.assertEqual(patch['consumer'].read(), 10)
        callable_test = load('test-double-signature')
        with self.assertRaises(TypeError):
            callable_test['submission'](41, 'DEL')
        self.assertEqual(callable_test['submit_receipt'](41, region='BOM'), 'BOM:41')

    def test_assignment_reader_and_mapping_views(self):
        reader = load('assignment-expression')['read_ids']
        for count in range(ORACLES['assignmentReaderCases']):
            identifiers = [f'R{index:02d}' for index in range(count)]
            self.assertEqual(reader(io.StringIO(''.join(value + '\n' for value in identifiers))),
                             (identifiers, count + 1))
        for content in ('R41', 'R41\nBAD\n', 'R４１\n'):
            with self.assertRaises(ValueError):
                reader(io.StringIO(content))
        view = load('dict-view-liveness')
        self.assertEqual(list(view['keys_view']), ['R42'])
        self.assertEqual(view['keys_snapshot'], ('R41',))

    def test_finally_and_stable_dedupe(self):
        interview = load('finally-return-interview')
        self.assertEqual(interview['unsafe_result'](), 'accepted')
        with self.assertRaises(ValueError):
            interview['safe_result']()
        dedupe = load('stable-dedup-exercise')['first_seen']
        rng = random.Random(141)
        alphabet = ['R41', 'R42', 'R43', 'R44']
        for _ in range(ORACLES['stableDedupeComparisons']):
            batch = rng.choices(alphabet, k=rng.randrange(0, 30))
            oracle = list(dict.fromkeys(batch))
            self.assertEqual(dedupe(batch), (oracle, len(batch) - len(oracle)))
        with self.assertRaises(ValueError):
            dedupe(['R４１'])

    def test_reference_and_temp_cleanup(self):
        reference = load('iterator-reference')
        self.assertEqual(list(reference['stream']), [])
        self.assertEqual(list(reference['receipt_ids']), [41, 42])
        temporary = load('tempdir-cleanup-tests')
        self.assertFalse(temporary['owned_path'].exists())

    def test_archive_bytes_and_module_origin(self):
        namespace = load('wheel-record-verification')
        archive = namespace['archive_for']
        matches = namespace['declared_module_matches']
        original = b"owner = 'aitrove'\n"
        self.assertTrue(matches(archive(original)))
        rng = random.Random(77)
        for _ in range(ORACLES['archiveMutationComparisons']):
            replacement = bytes(rng.randrange(0, 256) for _ in range(rng.randrange(0, 45)))
            if replacement == original:
                continue
            self.assertFalse(matches(archive(replacement)))
        module = load('module-origin-check')['module']
        self.assertEqual(module.limit(), 500)


if __name__ == '__main__':
    unittest.main(verbosity=2)
    print('ASSURANCE_ORACLES=' + str(sum(ORACLES.values())))
