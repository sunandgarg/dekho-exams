dispatch_batch = ["receipt-41"]
shared_batch = dispatch_batch
shared_batch.append("receipt-42")
copied_batch = dispatch_batch.copy()
copied_batch.append("receipt-43")
print(dispatch_batch)
print(copied_batch)
print(shared_batch is dispatch_batch)
