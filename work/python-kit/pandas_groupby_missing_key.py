import pandas as pd

receipts = pd.DataFrame({"region": ["north", None, "north"], "minor": [125, 75, 50]})
totals = receipts.groupby("region", dropna=False)["minor"].sum()
print("north:", int(totals.loc["north"]))
print("missing:", int(totals[totals.index.isna()].iloc[0]))
print("accounted:", int(totals.sum()) == int(receipts["minor"].sum()))
