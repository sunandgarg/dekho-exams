from sklearn.metrics import confusion_matrix, precision_score, recall_score

actual = [0, 0, 0, 1, 1]
predicted = [0, 1, 0, 0, 1]
print(confusion_matrix(actual, predicted, labels=[0, 1]).tolist())
print("precision:", precision_score(actual, predicted, zero_division=0))
print("recall:", recall_score(actual, predicted, zero_division=0))
print("empty-positive precision:", precision_score([0, 0], [0, 0], zero_division=0))
