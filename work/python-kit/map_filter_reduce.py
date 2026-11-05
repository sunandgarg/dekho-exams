from functools import reduce

adjustments = [125, -25, 75]
selected = filter(lambda amount: amount > 0, adjustments)
labeled = map(lambda amount: f"accepted:{amount}", selected)
adjustments.append(50)
print(list(labeled))
print(list(labeled))
print("empty total:", reduce(lambda total, amount: total + amount, [], 0))
