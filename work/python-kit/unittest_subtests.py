import io
import unittest

def parse_minor(text):
    if type(text) is not str or not 1 <= len(text) <= 4 or any(char not in "0123456789" for char in text):
        raise ValueError("ASCII amount")
    return int(text)

visited = []
class AmountCases(unittest.TestCase):
    def test_accepted_amounts(self):
        for raw, expected in (("0", 0), ("125", 125), ("0012", 12)):
            with self.subTest(raw=raw):
                visited.append(raw)
                self.assertEqual(parse_minor(raw), expected)

result = unittest.TextTestRunner(stream=io.StringIO()).run(
    unittest.defaultTestLoader.loadTestsFromTestCase(AmountCases))
print("method:", result.testsRun, "failures:", len(result.failures))
print("cases:", visited)
try:
    parse_minor("１２")
except ValueError:
    print("non-ASCII amount rejected")
