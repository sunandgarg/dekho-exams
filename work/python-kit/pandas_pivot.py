import pandas as pd

receipts = pd.DataFrame({"region": ["DEL", "DEL", "BOM"], "period": ["P1", "P1", "P2"], "amount": [125, 75, 250]})
try:
    receipts.pivot(index="region", columns="period", values="amount")
except ValueError:
    print("duplicate pair rejected")
grouped = receipts.groupby(["region", "period"], as_index=False)["amount"].sum()
wide = grouped.pivot(index="region", columns="period", values="amount").reindex(columns=["P1", "P2"])
print("accepted total:", int(wide.loc["DEL", "P1"]))
print("missing retained:", bool(pd.isna(wide.loc["DEL", "P2"])))
print("source rows:", len(receipts))
