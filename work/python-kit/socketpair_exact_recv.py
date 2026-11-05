import socket

def receive_exact(connection, byte_count):
    chunks = []
    remaining = byte_count
    while remaining:
        chunk = connection.recv(remaining)
        if not chunk:
            raise EOFError("receipt frame ended early")
        chunks.append(chunk)
        remaining -= len(chunk)
    return b"".join(chunks)

def receive_frame(connection, maximum_body):
    body_size = int.from_bytes(receive_exact(connection, 2), "big")
    if body_size > maximum_body:
        raise ValueError("receipt body too large")
    return receive_exact(connection, body_size)

sender, receiver = socket.socketpair()
try:
    receiver.settimeout(1)
    sender.sendall((7).to_bytes(2, "big") + b"R47paid"
                   + (7).to_bytes(2, "big") + b"R73")
    sender.shutdown(socket.SHUT_WR)
    print("first", receive_frame(receiver, 8).decode("ascii"))
    try:
        receive_frame(receiver, 8)
    except EOFError:
        print("short_second_rejected", True)
finally:
    sender.close()
    receiver.close()
