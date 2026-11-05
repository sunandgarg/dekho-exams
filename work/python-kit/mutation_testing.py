def accepted_quantity(value):
    return type(value) is int and 0 <= value <= 1000000

def boolean_mutant(value):
    return isinstance(value, int) and 0 <= value <= 1000000

def boundary_mutant(value):
    return type(value) is int and 0 <= value < 1000000

CASES = [(0, True), (125, True), (1000000, True), (True, False), (-1, False), (1000001, False), ("125", False)]
def passes_contract(operation):
    return all(operation(value) is expected for value, expected in CASES)

print("original passes:", passes_contract(accepted_quantity))
mutants = [boolean_mutant, boundary_mutant]
print("selected mutants killed:", sum(not passes_contract(operation) for operation in mutants))
print("selected mutants:", len(mutants))
