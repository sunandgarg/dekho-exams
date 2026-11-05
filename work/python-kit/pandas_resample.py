import pandas as pd

index = pd.to_datetime(["2026-09-01T00:10:00Z", "2026-09-01T00:50:00Z", "2026-09-01T02:10:00Z"])
amounts = pd.Series([125, 250, 75], index=index, dtype="Int64")
if not amounts.index.is_monotonic_increasing or amounts.index.hasnans:
    raise ValueError("ordered timestamps required")
hourly = amounts.resample("1h", closed="left", label="left").sum(min_count=1)
print([timestamp.strftime("%H:%M") for timestamp in hourly.index])
print([None if pd.isna(amount) else int(amount) for amount in hourly])
