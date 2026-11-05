from flask import Flask, jsonify, request
from werkzeug.exceptions import HTTPException

application = Flask(__name__)
application.config["MAX_CONTENT_LENGTH"] = 64
@application.errorhandler(HTTPException)
def http_failure(failure):
    return jsonify(status=failure.code, error="request rejected"), failure.code
@application.errorhandler(Exception)
def internal_failure(failure):
    return jsonify(status=500, error="internal failure"), 500
@application.post("/receipts")
def create_receipt():
    request.get_json()
    return jsonify(accepted=True), 201
@application.get("/owned-failure")
def owned_failure():
    raise RuntimeError("owned diagnostic not for the response")

client = application.test_client()
print("missing:", client.get("/missing").status_code)
print("method:", client.get("/receipts").status_code)
print("oversized:", client.post("/receipts", data='"' + 'x' * 100 + '"', content_type="application/json").status_code)
failure = client.get("/owned-failure")
print("internal:", failure.status_code, failure.get_json()["error"])
print("diagnostic exposed:", b"owned diagnostic" in failure.data)
