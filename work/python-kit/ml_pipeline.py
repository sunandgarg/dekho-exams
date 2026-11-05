import numpy as np
from sklearn.pipeline import Pipeline
from sklearn.preprocessing import StandardScaler
from sklearn.linear_model import LogisticRegression

training = np.array([[1, 10], [2, 20], [3, 30], [4, 40]], dtype=float)
labels = np.array([0, 0, 1, 1])
evaluation = np.array([[2.5, 25], [100, 1000]], dtype=float)
model = Pipeline([("scale", StandardScaler()),
                  ("classify", LogisticRegression(random_state=41, max_iter=200))])
model.fit(training, labels)
owned_mean = model.named_steps["scale"].mean_.copy()
print("training mean:", owned_mean.tolist())
predictions = model.predict(evaluation)
print("prediction count:", len(predictions))
print("mean unchanged:", bool(np.array_equal(owned_mean, model.named_steps["scale"].mean_)))
