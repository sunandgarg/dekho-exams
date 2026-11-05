import json

def unique_names(pairs):
    result = {}
    for name, value in pairs:
        if name in result:
            raise ValueError("duplicate name: " + name)
        result[name] = value
    return result

payload = '{"tenant":"north-47","tenant":"south-47"}'
try:
    json.loads(payload, object_pairs_hook=unique_names)
except ValueError as error:
    print(str(error))
