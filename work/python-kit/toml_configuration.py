import tomllib

def dispatch_config(text):
    if len(text) > 1024:
        raise ValueError("configuration budget exceeded")
    parsed = tomllib.loads(text)
    if set(parsed) != {"region", "workers"}:
        raise ValueError("unexpected configuration fields")
    if parsed["region"] not in {"DEL", "BOM"}:
        raise ValueError("unknown region")
    if type(parsed["workers"]) is not int or not 1 <= parsed["workers"] <= 8:
        raise ValueError("workers must be an integer from 1 to 8")
    return parsed

print(dispatch_config('region="DEL"\nworkers=3'))
try:
    dispatch_config('region="DEL"\nworkers=true')
except ValueError:
    print("boolean worker count rejected")
