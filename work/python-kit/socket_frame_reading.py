import socket

def read_exact(stream, count):
    chunks = bytearray()
    while len(chunks) < count:
        chunk = stream.recv(min(2, count - len(chunks)))
        if not chunk:
            raise EOFError("truncated frame")
        chunks.extend(chunk)
    return bytes(chunks)

def read_frame(stream):
    length = int.from_bytes(read_exact(stream, 2), "big")
    if length > 32:
        raise ValueError("frame cap")
    return read_exact(stream, length)

for wire in (b"\x00\x05R0041", b"\x00\x05R0", b"\x00\x21"):
    sender, receiver = socket.socketpair()
    with sender, receiver:
        receiver.settimeout(1)
        sender.sendall(wire)
        sender.shutdown(socket.SHUT_WR)
        try:
            print("payload:", read_frame(receiver))
        except (EOFError, ValueError) as failure:
            print(type(failure).__name__)
