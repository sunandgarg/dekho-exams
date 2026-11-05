import numpy as np

quantities = np.array([2, 3, 1], dtype=np.int64)
unit_prices = np.array([125, 150], dtype=np.int64)
line_costs = quantities[:, None] * unit_prices[None, :]
print(line_costs.shape)
print(line_costs.tolist())
print(line_costs.sum(axis=0, dtype=np.int64).tolist())
