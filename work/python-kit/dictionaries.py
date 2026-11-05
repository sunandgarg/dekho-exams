ledger = {41: 125, 42: 75}
ledger[41] = 200
print(list(ledger))
print(ledger[41])
print(ledger.get(99, "missing"))
print(99 in ledger)
