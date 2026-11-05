from copy import copy, deepcopy

labels = ["checked"]
batch = {"first": labels, "second": labels}
shallow = copy(batch)
owned = deepcopy(batch)
owned["first"].append("packed")
print(shallow["first"] is labels)
print(owned["first"] is owned["second"])
print(labels)
print(owned["second"])
