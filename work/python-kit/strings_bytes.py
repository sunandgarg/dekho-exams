def decode_record(payload):
    if len(payload) > 4096:
        raise ValueError("record exceeds byte limit")
    return payload.decode("utf-8", errors="strict")

record = decode_record("₹125".encode("utf-8"))
print(record)
print(len(record))
try:
    decode_record(b"\xe2\x82")
except UnicodeDecodeError:
    print("malformed UTF-8 rejected")
