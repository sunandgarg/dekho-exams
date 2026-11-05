import json

def unique_object(pairs):
    result = {}
    for name, value in pairs:
        if name in result:
            raise ValueError("duplicate field")
        result[name] = value
    return result

def receipt_document(payload):
    if type(payload) is not str or len(payload) > 200:
        raise ValueError("document length")
    return json.loads(payload, object_pairs_hook=unique_object)

print(receipt_document('{"receipt":{"id":"R41","minor":125}}'))
try:
    receipt_document('{"receipt":{"minor":125,"minor":0}}')
except ValueError:
    print("duplicate rejected")
