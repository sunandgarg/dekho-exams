import numpy as np

def resampled_mean_interval(values, draws, seed):
    if not isinstance(values, list) or not 2 <= len(values) <= 64 or any(type(value) not in (int, float) or not np.isfinite(value) or not 0 <= value <= 1000000 for value in values):
        raise ValueError("observations rejected")
    if type(draws) is not int or not 1 <= draws <= 4096 or type(seed) is not int or not 0 <= seed <= 1000000:
        raise ValueError("resampling budget rejected")
    observed = np.array(values, dtype=float)
    generator = np.random.default_rng(seed)
    indexes = generator.integers(0, len(values), size=(draws, len(values)))
    means = observed[indexes].mean(axis=1)
    return np.quantile(means, [.05, .95])

values = [100, 200, 300, 400]
interval = resampled_mean_interval(values, 2000, 41)
print("percentile interval:", np.round(interval, 1).tolist())
print("seed reproduced:", bool(np.array_equal(interval, resampled_mean_interval(values, 2000, 41))))
print("input unchanged:", values == [100, 200, 300, 400])
