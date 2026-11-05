def receipt_stream(trace):
    for receipt_id in (41, 42):
        trace.append("read:" + str(receipt_id))
        yield receipt_id

trace = []
stream = receipt_stream(trace)
print(trace)
print(next(stream))
print(trace)
print(list(stream))
print(list(stream))
