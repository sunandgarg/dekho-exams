amounts = [125, 0, -10, True, 75]
labels = [f"minor:{amount}" for amount in amounts if type(amount) is int and amount > 0]
print(labels)
print(amounts)
