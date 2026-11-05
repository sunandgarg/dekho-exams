import numpy as np
from sklearn.model_selection import TimeSeriesSplit
from sklearn.preprocessing import StandardScaler

observations = np.arange(12, dtype=float).reshape(-1, 1)
splitter = TimeSeriesSplit(n_splits=3, test_size=2, gap=1)
for training, evaluation in splitter.split(observations):
    scaler = StandardScaler().fit(observations[training])
    print("train:", [int(training[0]), int(training[-1])],
          "test:", [int(evaluation[0]), int(evaluation[-1])],
          "mean:", float(scaler.mean_[0]))
