import json

def reject_nonfinite(token):
    raise ValueError("nonfinite number: " + token)

try:
    json.loads('{"risk": NaN}', parse_constant=reject_nonfinite)
except ValueError as error:
    print(error)

print("accepted:", json.loads('{"risk": 47}')["risk"])
try:
    json.dumps({"risk": float("nan")}, allow_nan=False)
except ValueError:
    print("nonfinite output rejected")
