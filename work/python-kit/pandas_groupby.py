import pandas as pd

receipts = pd.DataFrame({"region": pd.Series(["DEL", "DEL", None, "BOM"], dtype="string"),
                         "amount": pd.Series([125, 250, 75, None], dtype="Int64")})
totals = receipts.groupby("region", dropna=False, sort=True)["amount"].sum(min_count=1)
for region, amount in totals.items():
    label = "missing-region" if pd.isna(region) else region
    value = None if pd.isna(amount) else int(amount)
    print(label, value)
print("rows retained:", int(receipts.groupby("region", dropna=False).size().sum()))
