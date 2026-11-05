from tempfile import SpooledTemporaryFile

def stage_payload(payload):
    if type(payload) is not bytes or len(payload) > 32:
        raise ValueError("byte payload cap")
    with SpooledTemporaryFile(max_size=8, mode="w+b") as staging:
        staging.write(payload)
        staging.rollover()
        staging.seek(0)
        restored = staging.read(33)
        return restored

print("round trip:", stage_payload(b"receipt:41") == b"receipt:41")
print("empty:", stage_payload(b""))
try:
    stage_payload(b"x" * 33)
except ValueError:
    print("application cap rejected")
