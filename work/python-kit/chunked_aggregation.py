from io import StringIO
import pandas as pd

def region_totals(text):
    if not isinstance(text, str) or len(text) > 1024:
        raise ValueError("CSV budget exceeded")
    totals = {}
    rows = 0
    with pd.read_csv(StringIO(text), chunksize=2,
                     dtype={"region": "string", "amount": "Int64"}) as chunks:
        for chunk in chunks:
            rows += len(chunk)
            if list(chunk.columns) != ["region", "amount"] or rows > 100:
                raise ValueError("CSV shape rejected")
            if chunk.isna().any().any() or not chunk["region"].isin(["DEL", "BOM"]).all():
                raise ValueError("CSV fields rejected")
            if (chunk["amount"] < 0).any() or (chunk["amount"] > 1000000).any():
                raise ValueError("amount range rejected")
            for region, amount in chunk.groupby("region")["amount"].sum().items():
                totals[region] = totals.get(region, 0) + int(amount)
    return totals

print(region_totals("region,amount\nDEL,125\nBOM,75\nDEL,250\n"))
try:
    region_totals("region,amount\nDEL,125\nBOM,75\nDEL,-1\n")
except ValueError:
    print("later chunk rejected; no result returned")
