def classify_expiry(records, now):
    if type(now) is not int or not 0 <= now <= 1000000 or type(records) is not list or len(records) > 64:
        raise ValueError("bounded records and clock required")
    seen, states = set(), {"pending": [], "active": [], "expired": []}
    for record in records:
        if type(record) is not dict or set(record) != {"receipt_id", "created", "ttl"}:
            raise ValueError("exact fields required")
        identifier, created, ttl = record["receipt_id"], record["created"], record["ttl"]
        if type(identifier) is not str or not identifier.isascii() or not identifier.isalnum() or not 1 <= len(identifier) <= 16 or identifier in seen or type(created) is not int or not 0 <= created <= 1000000 or type(ttl) is not int or not 1 <= ttl <= 100:
            raise ValueError("unique ID and bounded times required")
        seen.add(identifier)
        state = "pending" if now < created else "active" if now < created + ttl else "expired"
        states[state].append(identifier)
    return {state: sorted(identifiers) for state, identifiers in states.items()}

records = [{"receipt_id": "R41", "created": 100, "ttl": 10},
           {"receipt_id": "R42", "created": 110, "ttl": 5},
           {"receipt_id": "R43", "created": 120, "ttl": 5}]
print(classify_expiry(records, 110))
try:
    classify_expiry(records + [dict(records[0])], 110)
except ValueError:
    print("duplicate batch rejected")
