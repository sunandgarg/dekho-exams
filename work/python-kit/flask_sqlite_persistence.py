from pathlib import Path
import sqlite3
import tempfile
from flask import Flask, g, jsonify, request

def receipt_app(database_path):
    application = Flask(__name__)
    application.config["MAX_CONTENT_LENGTH"] = 1024
    with sqlite3.connect(database_path) as setup:
        setup.execute("CREATE TABLE IF NOT EXISTS receipts (receipt_id TEXT PRIMARY KEY, amount INTEGER NOT NULL CHECK(amount >= 0))")
    setup.close()
    def database():
        if "receipt_database" not in g:
            g.receipt_database = sqlite3.connect(database_path)
        return g.receipt_database
    @application.teardown_appcontext
    def release_database(failure):
        owned = g.pop("receipt_database", None)
        if owned is not None:
            owned.close()
    @application.post("/receipts")
    def store_receipt():
        if not request.is_json:
            return jsonify(error="JSON required"), 415
        import re
        payload = request.get_json()
        if not isinstance(payload, dict) or set(payload) != {"receipt_id", "amount"}:
            return jsonify(error="fields rejected"), 400
        if not isinstance(payload["receipt_id"], str) or re.fullmatch(r"R-[0-9]{4}", payload["receipt_id"]) is None:
            return jsonify(error="identifier rejected"), 400
        if type(payload["amount"]) is not int or not 0 <= payload["amount"] <= 1000000:
            return jsonify(error="amount rejected"), 400
        try:
            with database():
                database().execute("INSERT INTO receipts VALUES (?, ?)", (payload["receipt_id"], payload["amount"]))
        except sqlite3.IntegrityError:
            return jsonify(error="duplicate receipt"), 409
        return jsonify(receipt_id=payload["receipt_id"]), 201
    @application.get("/receipts")
    def list_receipts():
        rows = database().execute("SELECT receipt_id,amount FROM receipts ORDER BY receipt_id LIMIT 20").fetchall()
        return jsonify([{"receipt_id": identifier, "amount": amount} for identifier, amount in rows])
    return application

with tempfile.TemporaryDirectory() as directory:
    path = Path(directory) / "receipts.sqlite3"
    client = receipt_app(path).test_client()
    print("accepted:", client.post("/receipts", json={"receipt_id": "R-0041", "amount": 125}).status_code)
    print("duplicate:", client.post("/receipts", json={"receipt_id": "R-0041", "amount": 250}).status_code)
    reopened = receipt_app(path).test_client()
    print(reopened.get("/receipts").get_json())
