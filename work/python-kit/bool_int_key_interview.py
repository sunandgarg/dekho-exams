access = {True: "review"}
access[1] = "approve"
print("entries:", len(access))
print("by bool:", access[True])
print("by int:", access[1])
print("same hash:", hash(True) == hash(1))
