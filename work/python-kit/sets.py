received_ids = {41, 42, 43}
processed_ids = {41, 44}
print(sorted(received_ids & processed_ids))
print(sorted(received_ids - processed_ids))
print(len({41, 41, 42}))
