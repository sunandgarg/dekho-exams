import numpy as np

measurements = np.array([0.1 + 0.2, 0.0], dtype=np.float64)
references = np.array([0.3, 1e-12], dtype=np.float64)
if not np.isfinite(measurements).all() or not np.isfinite(references).all():
    raise ValueError("finite measurements required")
print((measurements == references).tolist())
print(np.isclose(measurements, references, rtol=1e-10, atol=1e-11).tolist())
print(bool(np.isfinite(np.array([1.0, np.nan])).all()))
