import socket

reader, writer = socket.socketpair()
with reader, writer:
    reader.settimeout(0.02)
    try:
        reader.recv(1)
    except socket.timeout:
        print("idle_timeout", True)
    writer.sendall(b"R")
    print("received", reader.recv(1).decode("ascii"))
