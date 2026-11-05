ledger = {"R41": "queued"}
keys_view = ledger.keys()
keys_snapshot = tuple(keys_view)
ledger["R42"] = "sent"
print("live:", list(keys_view))
print("snapshot:", keys_snapshot)
for identifier in tuple(keys_view):
    if ledger[identifier] == "queued":
        del ledger[identifier]
print("remaining:", sorted(ledger))
