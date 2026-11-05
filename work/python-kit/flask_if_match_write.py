from flask import Flask, jsonify, request

application = Flask(__name__)
receipt = {"minor": 125, "revision": 1}

@application.get("/receipt")
def read_receipt():
    response = jsonify(minor=receipt["minor"])
    response.headers["ETag"] = f'"{receipt["revision"]}"'
    return response

@application.put("/receipt")
def update_receipt():
    if request.headers.get("If-Match") != f'"{receipt["revision"]}"':
        return jsonify(error="stale revision"), 412
    payload = request.get_json(silent=True)
    if type(payload) is not dict or type(payload.get("minor")) is not int or not 0 <= payload["minor"] <= 1000:
        return jsonify(error="invalid amount"), 400
    receipt["minor"] = payload["minor"]
    receipt["revision"] += 1
    return jsonify(minor=receipt["minor"])

with application.test_client() as client:
    tag = client.get("/receipt").headers["ETag"]
    print("accepted:", client.put("/receipt", json={"minor": 150}, headers={"If-Match": tag}).status_code)
    print("stale:", client.put("/receipt", json={"minor": 175}, headers={"If-Match": tag}).status_code)
    print("stored:", client.get("/receipt").get_json()["minor"])
