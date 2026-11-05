from flask import Flask, jsonify, request

application = Flask(__name__)
receipts = [(41, 125), (42, 75), (43, 200)]

@application.get("/receipts")
def list_receipts():
    raw = request.args.get("after", "0")
    if not 1 <= len(raw) <= 6 or any(char not in "0123456789" for char in raw):
        return jsonify(error="invalid cursor"), 400
    selected = [(identifier, amount) for identifier, amount in receipts if identifier > int(raw)][:2]
    return jsonify(ids=[identifier for identifier, _ in selected],
                   next=selected[-1][0] if selected else None)

with application.test_client() as client:
    first = client.get("/receipts").get_json()
    second = client.get("/receipts?after=42").get_json()
    print(first["ids"], first["next"])
    print(second["ids"], second["next"])
    print("bad cursor:", client.get("/receipts?after=+1").status_code)
