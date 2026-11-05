import json
import pickle

shared_events = ["paid"]
trusted_cache = {"R-47": shared_events, "R-73": shared_events}
restored_cache = pickle.loads(pickle.dumps(trusted_cache, protocol=4))
print("alias_preserved", restored_cache["R-47"] is restored_cache["R-73"])

def parse_received_receipt(payload):
    if len(payload) > 96:
        raise ValueError("record too large")
    record = json.loads(payload.decode("utf-8"))
    if (type(record) is not dict or set(record) != {"receipt", "amount"}
            or type(record["receipt"]) is not str
            or type(record["amount"]) is not int):
        raise ValueError("wrong record shape")
    return record["receipt"], record["amount"]

print("received", parse_received_receipt(b'{"receipt":"R-47","amount":73}'))
try:
    parse_received_receipt(pickle.dumps(trusted_cache, protocol=4))
except (UnicodeError, ValueError, json.JSONDecodeError):
    print("pickle_input_rejected", True)
