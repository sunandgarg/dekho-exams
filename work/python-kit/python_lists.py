receipt_batch = [[41, 125], [42, 75]]
snapshot = receipt_batch[:]
snapshot[0][1] = 200
snapshot.append([43, 50])
print(receipt_batch)
print(snapshot)
print(receipt_batch[0] is snapshot[0])
