def accepted_squares(amounts):
    for amount in amounts:
        if amount > 0:
            yield amount * amount

stream = accepted_squares([3, -1, 4])
print(list(stream))
print(list(stream))
