import base64
import binascii

def canonical_bytes(encoded):
    if type(encoded) is not str or not encoded.isascii() or len(encoded) > 64:
        raise ValueError("bounded ASCII encoding required")
    try:
        decoded = base64.b64decode(encoded, validate=True)
    except binascii.Error as failure:
        raise ValueError("invalid Base64") from failure
    if len(decoded) > 32 or base64.b64encode(decoded).decode("ascii") != encoded:
        raise ValueError("canonical bounded encoding required")
    return decoded

print("decoded:", canonical_bytes("fQ==").hex())
for received in ("fQ==\n", "fQ", "fR==", "__8="):
    try:
        canonical_bytes(received)
    except ValueError:
        print("spelling rejected")
