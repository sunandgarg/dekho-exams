from contextlib import ExitStack
from io import StringIO

closed = []
def release(stream, label):
    stream.close()
    closed.append(label)

streams = []
try:
    with ExitStack() as stack:
        for label in ("receipts", "prices"):
            stream = StringIO(label)
            streams.append(stream)
            stack.callback(release, stream, label)
        raise OSError("third input unavailable")
except OSError:
    print("acquisition failed")
print(closed)
print(all(stream.closed for stream in streams))
