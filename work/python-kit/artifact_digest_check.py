import hashlib
import hmac

def artifact_matches(payload, expected):
    if type(payload) is not bytes or len(payload) > 4096:
        raise ValueError("artifact byte cap")
    if type(expected) is not str or len(expected) != 64 or any(char not in "0123456789abcdef" for char in expected):
        raise ValueError("digest format")
    actual = hashlib.sha256(payload).hexdigest()
    return hmac.compare_digest(actual, expected)

owned_artifact = b"receipt-schema:v1\namount:integer\n"
trusted_expectation = hashlib.sha256(owned_artifact).hexdigest()
print("owned bytes:", artifact_matches(owned_artifact, trusted_expectation))
print("altered bytes:", artifact_matches(owned_artifact + b"x", trusted_expectation))
try:
    artifact_matches(owned_artifact, "not-a-digest")
except ValueError:
    print("digest schema rejected")
