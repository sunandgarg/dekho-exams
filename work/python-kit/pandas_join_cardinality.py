import pandas as pd
from pandas.errors import MergeError

receipts = pd.DataFrame({"receipt_id": [41, 42], "minor": [125, 75]})
currency = pd.DataFrame({"receipt_id": [41, 42], "unit": ["INR", "INR"]})
joined = receipts.merge(currency, on="receipt_id", validate="one_to_one")
print("joined:", len(joined))
duplicates = pd.DataFrame({"receipt_id": [41, 41], "unit": ["INR", "USD"]})
try:
    receipts.merge(duplicates, on="receipt_id", validate="one_to_one")
except MergeError:
    print("duplicate key rejected")
