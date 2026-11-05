import numpy as np

amounts = np.array([125, 75, 90], dtype=np.int64)
view = amounts[1:]
selected = amounts[[1, 2]]
view[0] = 80
selected[0] = 999
print(amounts.tolist())
print(selected.tolist())
print(bool(np.shares_memory(amounts, view)))
print(bool(np.shares_memory(amounts, selected)))
