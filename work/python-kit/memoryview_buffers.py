header = bytearray(b"ABCD")
view = memoryview(header)
selected = view[1:3]
selected[0] = ord("Z")
print(bytes(header))
try:
    header.append(0)
except BufferError:
    print("resize blocked while exported")
selected.release()
view.release()
header.append(0)
print(len(header))
