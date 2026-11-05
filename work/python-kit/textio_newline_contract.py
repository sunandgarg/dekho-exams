import io

wire_bytes = b"R-47\r\nR-73\n"
with io.TextIOWrapper(io.BytesIO(wire_bytes), encoding="utf-8", newline=None) as normalized:
    print("normalized", repr(normalized.read()))
with io.TextIOWrapper(io.BytesIO(wire_bytes), encoding="utf-8", newline="") as preserved:
    print("preserved", repr(preserved.read()))
