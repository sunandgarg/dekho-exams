closed = []
def running_total():
    total = 0
    try:
        while True:
            amount = yield total
            if type(amount) is not int or not 0 <= amount <= 1000:
                raise ValueError("bounded exact amount required")
            total += amount
    finally:
        closed.append("released")

producer = running_total()
print("initial:", next(producer))
print("accepted:", producer.send(125))
try:
    producer.send(True)
except ValueError:
    print("invalid send rejected")
print("closed:", closed)
second = running_total()
next(second)
second.close()
print("explicit closes:", len(closed))
