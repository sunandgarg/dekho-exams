import numpy as np

amounts = np.array([125.0, np.nan, np.inf, -3.0], dtype=np.float64)
finite = np.isfinite(amounts)
accepted = finite & (amounts >= 0)
print("finite:", finite.tolist())
print("accepted:", accepted.tolist())
print("selected:", amounts[accepted].tolist())
