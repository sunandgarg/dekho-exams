import io
import re
from flask import Flask, request

app = Flask(__name__)
app.config.update(MAX_CONTENT_LENGTH=4096, MAX_FORM_MEMORY_SIZE=4096, MAX_FORM_PARTS=2)
@app.errorhandler(413)
def too_large(failure):
    return {"error": "upload budget exceeded"}, 413

@app.post("/receipts")
def receive():
    if set(request.form) != {"receipt_id"} or set(request.files) != {"receipt"} or len(request.form.getlist("receipt_id")) != 1 or len(request.files.getlist("receipt")) != 1:
        return {"error": "exact parts required"}, 400
    if re.fullmatch(r"R-[0-9]{4}", request.form["receipt_id"]) is None:
        return {"error": "invalid receipt ID"}, 400
    payload = request.files["receipt"].stream.read(129)
    if len(payload) > 128:
        return {"error": "file byte budget exceeded"}, 413
    return {"bytes": len(payload)}, 201

with app.test_client() as client:
    accepted = client.post("/receipts", data={"receipt_id": "R-0041", "receipt": (io.BytesIO(b"amount=125"), "received.txt")})
    oversized = client.post("/receipts", data={"receipt_id": "R-0041", "receipt": (io.BytesIO(b"x" * 129), "received.txt")})
    extra = client.post("/receipts", data={"receipt_id": "R-0041", "receipt": (io.BytesIO(b"ok"), "received.txt"), "extra": "field"})
    print("accepted:", accepted.status_code, accepted.json)
    print("file limit:", oversized.status_code)
    print("part limit:", extra.status_code)
