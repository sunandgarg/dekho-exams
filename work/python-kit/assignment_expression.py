from io import StringIO

def read_ids(stream):
    accepted = []
    reads = 0
    while (line := stream.readline(16)) != "":
        reads += 1
        if len(line) > 8 or not line.endswith("\n"):
            raise ValueError("bounded complete line")
        identifier = line[:-1]
        if len(identifier) != 3 or identifier[0] != "R" or any(char not in "0123456789" for char in identifier[1:]):
            raise ValueError("receipt identifier")
        accepted.append(identifier)
    return accepted, reads + 1

print(read_ids(StringIO("R41\nR42\n")))
try:
    read_ids(StringIO("R41\nBAD\n"))
except ValueError:
    print("invalid line rejected")
