import hashlib
import io

payload = b"R" * 47 + b"|north-47"
digest = hashlib.sha256()
source = io.BytesIO(payload)
while chunk := source.read(7):
    digest.update(chunk)
expected = hashlib.sha256(payload).digest()
print("same", digest.digest() == expected)
print("bytes", len(payload))
