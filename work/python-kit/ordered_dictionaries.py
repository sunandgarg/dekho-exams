from collections import OrderedDict

recent = OrderedDict([("R-0041", 125), ("R-0042", 250)])
recent.move_to_end("R-0041")
print("access order:", list(recent))
print("evicted:", recent.popitem(last=False))
first = OrderedDict([("DEL", 1), ("BOM", 2)])
second = OrderedDict([("BOM", 2), ("DEL", 1)])
print("ordered equality:", first == second)
print("mapping equality:", first == dict(second))
