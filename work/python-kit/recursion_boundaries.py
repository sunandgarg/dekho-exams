def total_batch(batch, depth=0):
    if depth > 4:
        raise ValueError("batch nesting too deep")
    if type(batch) is int:
        return batch
    if type(batch) is not list:
        raise ValueError("integer leaves required")
    return sum(total_batch(child, depth + 1) for child in batch)

print(total_batch([125, [250, [75]]]))
try:
    total_batch([[[[[[1]]]]]])
except ValueError:
    print("depth budget rejected")
