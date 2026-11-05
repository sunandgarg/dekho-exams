from collections import ChainMap

defaults = {"timeout": 30, "region": "local"}
deployment = {"timeout": 10}
request = {}
settings = ChainMap(request, deployment, defaults)
print("initial:", settings["timeout"])
settings["timeout"] = 5
snapshot = dict(settings)
deployment["region"] = "west"
print("request:", request)
print("default timeout:", defaults["timeout"])
print("live region:", settings["region"])
print("snapshot region:", snapshot["region"])
try:
    del settings["region"]
except KeyError:
    print("later-layer deletion rejected")
