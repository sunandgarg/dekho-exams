import numpy as np

def warehouse_costs(demand, prices):
    matrix = np.asarray(demand, dtype=np.float64)
    vector = np.asarray(prices, dtype=np.float64)
    if matrix.ndim != 2 or any(not 1 <= size <= 8 for size in matrix.shape) or vector.shape != (matrix.shape[1],):
        raise ValueError("warehouse/product shape")
    if not np.isfinite(matrix).all() or not np.isfinite(vector).all() or (matrix < 0).any() or (vector < 0).any():
        raise ValueError("finite nonnegative values")
    return (matrix * vector).sum(axis=1)

print("totals:", warehouse_costs([[2, 1], [1, 3]], [1.5, 2.0]).tolist())
try:
    warehouse_costs([[2, 1], [1, 3]], [[1.5], [2.0]])
except ValueError:
    print("broadcastable wrong shape rejected")
