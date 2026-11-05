import json
import re

def audit_line(record):
    event = record.get("event")
    receipt_id = record.get("receipt_id")
    if event not in {"accepted", "rejected"}:
        raise ValueError("unsupported audit event")
    if not isinstance(receipt_id, str) or re.fullmatch(r"R-[0-9]{4}", receipt_id) is None:
        raise ValueError("invalid audit identifier")
    return json.dumps({"event": event, "receipt_id": receipt_id}, sort_keys=True)

record = {"event": "accepted", "receipt_id": "R-0041", "token": "fixture-only"}
print(audit_line(record))
print("token" in record)
try:
    audit_line({"event": "accepted", "receipt_id": "R-0041\n"})
except ValueError:
    print("line injection rejected")
