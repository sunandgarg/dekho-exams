import io
import unittest

def receipt_total(quantity, unit_minor):
    if type(quantity) is not int or type(unit_minor) is not int:
        raise TypeError("integer fields required")
    if quantity < 0 or unit_minor < 0:
        raise ValueError("negative field")
    return quantity * unit_minor

class ReceiptTotalChecks(unittest.TestCase):
    def test_total(self):
        self.assertEqual(receipt_total(3, 125), 375)
    def test_zero_quantity(self):
        self.assertEqual(receipt_total(0, 125), 0)
    def test_boolean_rejected(self):
        with self.assertRaises(TypeError):
            receipt_total(True, 125)

suite = unittest.defaultTestLoader.loadTestsFromTestCase(ReceiptTotalChecks)
result = unittest.TextTestRunner(stream=io.StringIO()).run(suite)
print("passed:", result.wasSuccessful())
print("tests:", result.testsRun)
