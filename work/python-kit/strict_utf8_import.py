def decode_receipt(raw):
    if type(raw) is not bytes or len(raw) > 80:
        raise ValueError("byte budget")
    if raw.startswith(b"\xef\xbb\xbf"):
        raise ValueError("BOM not permitted")
    return raw.decode("utf-8")

print(decode_receipt("Café R41".encode("utf-8")))
for payload in (b"\xc3(", b"\xef\xbb\xbfR41"):
    try:
        decode_receipt(payload)
    except (UnicodeDecodeError, ValueError):
        print("bytes rejected")
