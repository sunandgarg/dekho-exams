import numpy as np

feature = np.array([0, 1, 2, 3], dtype=float)
design = np.column_stack([np.ones_like(feature), feature])
observed = np.array([3, 5, 7, 9], dtype=float)
coefficients, residuals, rank, singular = np.linalg.lstsq(design, observed, rcond=None)
print("full rank:", int(rank) == design.shape[1])
print("coefficients:", np.round(coefficients, 6).tolist())
print("fit accepted:", bool(np.allclose(design @ coefficients, observed, rtol=1e-10, atol=1e-10)))
duplicate_columns = np.column_stack([feature, feature])
_, _, deficient_rank, _ = np.linalg.lstsq(duplicate_columns, observed, rcond=None)
print("deficient rank:", int(deficient_rank) < duplicate_columns.shape[1])
