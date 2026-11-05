import pandas as pd

readings = pd.DataFrame({"minute": [10, 20, 30], "receipt_id": [41, 42, 43]})
events = pd.DataFrame({"minute": [8, 19, 25], "state": ["opened", "checked", "closed"]})
joined = pd.merge_asof(readings, events, on="minute", direction="backward", tolerance=3)
print(["missing" if pd.isna(value) else value for value in joined["state"]])
print(joined["receipt_id"].tolist())
