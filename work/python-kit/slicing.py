receipts = [41, 42, 43, 44]
print(receipts[1:3])
print(receipts[::-1])
print(receipts[20:30])
try:
    receipts[::0]
except ValueError:
    print("zero step rejected")
