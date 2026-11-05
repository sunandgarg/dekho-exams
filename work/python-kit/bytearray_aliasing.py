frame = bytearray(b"R41:125")
snapshot = bytes(frame)
view = memoryview(frame)
frame[0] = ord("X")
print("snapshot:", snapshot)
print("buffer:", bytes(frame))
print("view:", view[0])
try:
    frame.extend(b"!")
except BufferError:
    print("resize blocked by view")
view.release()
frame.extend(b"!")
print("resized:", bytes(frame))
