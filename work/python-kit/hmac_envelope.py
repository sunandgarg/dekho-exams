import hashlib
import hmac
import re

FIXTURE_KEY = b"owned-test-key-not-a-production-secret"
def authenticated(payload, tag):
    if type(payload) is not bytes or len(payload) > 128 or type(tag) is not str or re.fullmatch(r"[0-9a-f]{64}", tag) is None:
        return False
    expected = hmac.new(FIXTURE_KEY, payload, hashlib.sha256).digest()
    return hmac.compare_digest(expected, bytes.fromhex(tag))

payload = b'{"receipt_id":"R-0041","amount":125}'
tag = hmac.new(FIXTURE_KEY, payload, hashlib.sha256).hexdigest()
print("original:", authenticated(payload, tag))
print("changed:", authenticated(payload.replace(b"125", b"250"), tag))
print("replay:", authenticated(payload, tag))
print("malformed:", authenticated(payload, "not-a-tag"))
