from io import StringIO
import re

def read_quantity(source, output):
    line = source.readline(5)
    if line == "":
        raise EOFError("quantity input ended")
    if re.fullmatch(r"[0-9]{1,2}\n", line) is None:
        raise ValueError("quantity line rejected")
    quantity = int(line[:-1])
    if not 1 <= quantity <= 20:
        raise ValueError("quantity range rejected")
    print(f"accepted quantity: {quantity}", file=output)
    return quantity

source, output = StringIO("3\n"), StringIO()
print(read_quantity(source, output))
print(output.getvalue().strip())
for text in ("", "\n", "123456\n"):
    try:
        read_quantity(StringIO(text), StringIO())
    except (EOFError, ValueError) as failure:
        print(type(failure).__name__)
