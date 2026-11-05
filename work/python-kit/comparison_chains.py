reads = []
def read_amount():
    reads.append("ledger")
    return 125

print(0 < read_amount() <= 500)
print("reads:", len(reads))
amount = read_amount()
print(0 < amount and amount <= 100)
print("reads:", len(reads))
