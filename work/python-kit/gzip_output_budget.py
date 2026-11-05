import gzip
import io
import zlib

def bounded_gzip(payload):
    if type(payload) is not bytes or len(payload) > 512:
        raise ValueError("compressed byte budget exceeded")
    try:
        with gzip.GzipFile(fileobj=io.BytesIO(payload), mode="rb") as decoder:
            expanded = decoder.read(129)
    except (OSError, EOFError, zlib.error) as failure:
        raise ValueError("invalid gzip stream") from failure
    if len(expanded) > 128:
        raise ValueError("expanded byte budget exceeded")
    return expanded

encoded = gzip.compress(b"receipt:125", mtime=0)
print("decoded:", bounded_gzip(encoded).decode("ascii"))
print("members:", bounded_gzip(gzip.compress(b"A", mtime=0) + gzip.compress(b"B", mtime=0)))
for invalid in (gzip.compress(b"x" * 129, mtime=0), encoded[:-1]):
    try:
        bounded_gzip(invalid)
    except ValueError:
        print("stream rejected")
