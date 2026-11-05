import pandas as pd

amounts = pd.Series([125, None, 75], dtype="Int64")
absent = pd.Series([None, None], dtype="Int64")
print(str(amounts.dtype))
print(amounts.dropna().astype(int).tolist())
print("missing:", int(amounts.isna().sum()))
print("total:", int(amounts.sum(min_count=1)))
print("all absent stays missing:", bool(pd.isna(absent.sum(min_count=1))))
