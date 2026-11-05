graph = {
    "receive": ["validate"],
    "validate": ["dispatch"],
    "dispatch": ["receive"],
}
state = {}
path = []

def cycle_from(stage):
    state[stage] = "active"
    path.append(stage)
    for dependency in graph[stage]:
        if state.get(dependency) == "active":
            return path[path.index(dependency):] + [dependency]
        if dependency not in state:
            found = cycle_from(dependency)
            if found:
                return found
    path.pop()
    state[stage] = "done"
    return None

print(" -> ".join(cycle_from("receive")))
