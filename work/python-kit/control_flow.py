amounts = [None, 0, 125, -10, 75]
accepted = []
for amount in amounts:
    if amount is None or amount <= 0:
        continue
    accepted.append(amount)
print(sum(accepted))
for amount in accepted:
    if amount > 500:
        print("manual review")
        break
else:
    print("no review threshold reached")
