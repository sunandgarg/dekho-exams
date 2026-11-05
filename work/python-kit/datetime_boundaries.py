from datetime import datetime, timezone

def receipt_instant(text):
    if not 1 <= len(text) <= 40:
        raise ValueError("timestamp length")
    instant = datetime.fromisoformat(text)
    if instant.tzinfo is None or instant.utcoffset() is None:
        raise ValueError("offset required")
    return instant.astimezone(timezone.utc)

local = receipt_instant("2026-09-29T10:00:00+05:30")
print(local.isoformat())
print(local == receipt_instant("2026-09-29T04:30:00+00:00"))
try:
    receipt_instant("2026-09-29T10:00:00")
except ValueError:
    print("missing offset rejected")
