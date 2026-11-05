from flask import Flask, abort, request

def create_application():
    application = Flask(__name__)
    application.config.update(TESTING=True, MAX_CONTENT_LENGTH=256)
    @application.post("/receipt-estimates")
    def estimate():
        payload = request.get_json()
        if type(payload) is not dict or set(payload) != {"quantity", "unit_minor"}:
            abort(400)
        quantity, unit_minor = payload["quantity"], payload["unit_minor"]
        if type(quantity) is not int or type(unit_minor) is not int or not 0 <= quantity <= 100 or not 0 <= unit_minor <= 100000:
            abort(400)
        return {"total_minor": quantity * unit_minor}
    return application

client = create_application().test_client()
print(client.post("/receipt-estimates", json={"quantity": 3, "unit_minor": 125}).get_json())
print(client.post("/receipt-estimates", json={"quantity": True, "unit_minor": 125}).status_code)
print(client.post("/receipt-estimates", json={"quantity": 1, "unit_minor": 1, "extra": 2}).status_code)
print(client.post("/receipt-estimates", data="x" * 300, content_type="application/json").status_code)
