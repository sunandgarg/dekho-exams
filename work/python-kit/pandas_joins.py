import pandas as pd

receipts = pd.DataFrame({"receipt_id": [41, 42, 43], "region": ["DEL", "DEL", "BOM"]})
directory = pd.DataFrame({"region": ["DEL"], "owner": ["north"]})
joined = receipts.merge(directory, on="region", how="left", validate="many_to_one", indicator=True)
print(joined.loc[joined["_merge"] == "left_only", "receipt_id"].tolist())
print(joined.loc[joined["_merge"] == "both", "receipt_id"].tolist())
try:
    receipts.merge(pd.DataFrame({"region": ["DEL", "DEL"]}), on="region", validate="many_to_one")
except pd.errors.MergeError:
    print("duplicate directory key rejected")
