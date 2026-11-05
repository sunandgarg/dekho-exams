from datetime import datetime, timezone
from zoneinfo import ZoneInfo

zone = ZoneInfo("America/New_York")
for hour in (5, 6):
    instant = datetime(2024, 11, 3, hour, 30, tzinfo=timezone.utc)
    local = instant.astimezone(zone)
    print(local.isoformat(), "fold=" + str(local.fold))
