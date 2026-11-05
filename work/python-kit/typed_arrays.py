from array import array

quantities = array("B", [3, 5, 8])
view = memoryview(quantities)
view[1] = 7
print("shared values:", quantities.tolist())
try:
    quantities.append(256)
except OverflowError:
    print("out of range rejected")
try:
    quantities.append(9)
except BufferError:
    print("resize while exported rejected")
view.release()
quantities.append(9)
print("released values:", quantities.tolist())
