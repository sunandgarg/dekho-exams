from flask import Flask, abort

def create_application():
    application = Flask(__name__)
    application.config["TESTING"] = True
    @application.get("/receipts/<int:receipt_id>")
    def receipt(receipt_id):
        if receipt_id <= 0:
            abort(400)
        return {"receipt_id": receipt_id, "amount_minor": 125}
    return application

client = create_application().test_client()
response = client.get("/receipts/41")
print(response.status_code, response.get_json())
print(client.get("/receipts/0").status_code)
print(client.get("/receipts/not-an-id").status_code)
