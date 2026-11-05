import pandas as pd

def attach_regions(receipts, regions):
    if regions["region"].isna().any():
        raise ValueError("lookup region cannot be missing")
    return receipts.merge(regions, on="region", how="left", validate="many_to_one", indicator=True)

receipts = pd.DataFrame({"region": pd.Series(["DEL", None], dtype="string"), "amount": [125, 75]})
unchecked = pd.DataFrame({"region": pd.Series(["DEL", None], dtype="string"), "label": ["Delhi", "unchecked-missing"]})
print("raw null matched:", receipts.merge(unchecked, on="region", how="left")["label"].iloc[1] == "unchecked-missing")
try:
    attach_regions(receipts, unchecked)
except ValueError:
    print("missing lookup key rejected")
accepted = unchecked[unchecked["region"].notna()].copy()
joined = attach_regions(receipts, accepted)
print(joined["_merge"].astype(str).tolist())
