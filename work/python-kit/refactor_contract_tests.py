import io
import unittest

def old_charge(quantity):
    if type(quantity) is not int or not 0 <= quantity <= 2:
        raise ValueError("quantity rejected")
    if quantity == 0: return 0
    if quantity == 1: return 25
    return 40

def new_charge(quantity):
    if type(quantity) is not int or not 0 <= quantity <= 2:
        raise ValueError("quantity rejected")
    return (0, 25, 40)[quantity]

class ChargeContract(unittest.TestCase):
    def test_accepted(self):
        for quantity, expected in ((0, 0), (1, 25), (2, 40)):
            self.assertEqual(old_charge(quantity), expected)
            self.assertEqual(new_charge(quantity), expected)
    def test_rejected(self):
        for operation in (old_charge, new_charge):
            for quantity in (True, -1, 3, "1"):
                with self.assertRaises(ValueError): operation(quantity)

result = unittest.TextTestRunner(stream=io.StringIO()).run(unittest.defaultTestLoader.loadTestsFromTestCase(ChargeContract))
print("contract suites:", result.testsRun)
print("preserved:", result.wasSuccessful())
