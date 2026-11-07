import os
from flask import Flask, request, jsonify
from flask_cors import CORS

app = Flask(__name__)
CORS(app)  # lets the Lovable page call this server

app.json.ensure_ascii = False  # keeps Chinese readable in responses

@app.get("/health")
def health():
    return jsonify({"ok": True})

@app.post("/ask")
def ask():
    data = request.get_json(silent=True) or {}
    question = data.get("question", "")

    # STUB: hardcoded answer in the agreed format.
    # Justin's safety.py, Jordan's Gemini code and coverage.py replace this later.
    return jsonify({
        "language": "en",
        "red_flag": None,          # or "911" / "988" / "811"
        "category": "physio",
        "why_one_line": "Back pain from sitting fits a physiotherapist.",
        "coverage": {
            "per_visit": 40,
            "per_year": 400
        },
        "echo": question
    })