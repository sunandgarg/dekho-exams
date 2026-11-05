import pandas as pd

amounts = pd.Series([125, 250, 75, 50], dtype="Int64")
trailing = amounts.rolling(window=2, min_periods=2).sum()
print([None if pd.isna(value) else int(value) for value in trailing])
with_gap = pd.Series([125, None, 75], dtype="Int64")
print(with_gap.rolling(2, min_periods=2).count().tolist())
