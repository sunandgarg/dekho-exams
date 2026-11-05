from flask import Flask, Response, request

application = Flask(__name__)

@application.get("/receipts/41")
def receipt_summary():
    response = Response(b"receipt=41;amount=125\n", mimetype="text/plain")
    response.cache_control.private = True
    response.cache_control.max_age = 30
    response.add_etag()
    return response.make_conditional(request)

with application.test_client() as client:
    initial = client.get("/receipts/41")
    validator = initial.headers["ETag"]
    unchanged = client.get("/receipts/41", headers={"If-None-Match": validator})
    changed = client.get("/receipts/41", headers={"If-None-Match": '"different"'})
    print("statuses:", initial.status_code, unchanged.status_code, changed.status_code)
    print("304 body:", unchanged.data)
    print("validator retained:", unchanged.headers["ETag"] == validator)
    print("cache policy:", initial.headers["Cache-Control"])
