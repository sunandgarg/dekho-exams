def decode_envelope(fields):
    if type(fields) not in (list, tuple) or not 3 <= len(fields) <= 5:
        raise ValueError("bounded envelope")
    version, *payload, checksum = fields
    if version != "v1" or type(checksum) is not int or checksum != sum(len(part) for part in payload if type(part) is str):
        raise ValueError("envelope fields")
    if any(type(part) is not str or not part for part in payload):
        raise ValueError("nonempty text payload")
    return payload

print(decode_envelope(("v1", "DEL", "R41", 6)))
try:
    decode_envelope(("v1", 0))
except ValueError:
    print("short envelope rejected")
try:
    decode_envelope(("v1", "DEL", 2))
except ValueError:
    print("checksum rejected")
