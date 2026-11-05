from datetime import datetime, timezone
from zoneinfo import ZoneInfo

def local_candidates(local, zone):
    if type(local) is not datetime or local.tzinfo is not None or not isinstance(zone, ZoneInfo):
        raise ValueError("naive datetime and named zone required")
    candidates = set()
    for fold in (0, 1):
        instant = local.replace(tzinfo=zone, fold=fold).astimezone(timezone.utc)
        restored = instant.astimezone(zone).replace(tzinfo=None)
        if restored == local:
            candidates.add(instant)
    return sorted(candidates)

zone = ZoneInfo("America/New_York")
for local in (datetime(2024, 2, 1, 12), datetime(2024, 11, 3, 1, 30),
              datetime(2024, 3, 10, 2, 30)):
    print("candidates:", len(local_candidates(local, zone)))
print("repeated UTC:", [value.strftime("%H:%M") for value in
      local_candidates(datetime(2024, 11, 3, 1, 30), zone)])
