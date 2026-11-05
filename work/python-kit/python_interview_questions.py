nested = [[125]]
outer_copy = nested.copy()
print(nested is outer_copy)
print(nested[0] is outer_copy[0])
outer_copy[0].append(75)
print(nested)

def new_tags(tags=None):
    return [] if tags is None else tags

print(new_tags() is new_tags())
