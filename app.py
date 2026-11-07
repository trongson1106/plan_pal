import os
from flask import Flask, request, jsonify, send_from_directory
from flask_cors import CORS

try:
    from dotenv import load_dotenv
    load_dotenv()
except ImportError:
    pass

from data.safety import EMERGENCY_911, CRISIS_988
from api.api import classify
from coverage import COVERAGE

app = Flask(__name__)
CORS(app)
app.json.ensure_ascii = False


def _safety_check(question):
    """Return '911', '988', or None — never calls Gemini."""
    q = question.lower()
    for phrase in EMERGENCY_911:
        if phrase in q:
            return "911"
    for phrase in CRISIS_988:
        if phrase in q:
            return "988"
    return None


@app.get("/")
def index():
    return send_from_directory(".", "index.html")


@app.get("/health")
def health():
    return jsonify({"ok": True})


@app.post("/ask")
def ask():
    body = request.get_json(silent=True) or {}
    question = body.get("question", "")

    if not question or not question.strip():
        return jsonify({"error": "question is required"}), 400

    # Safety gate — Gemini is never called on 911/988 paths
    flag = _safety_check(question)
    if flag in ("911", "988"):
        print(f"[safety] {flag} triggered — Gemini NOT called", flush=True)
        return jsonify({
            "language": None,
            "red_flag": flag,
            "category": None,
            "why_one_line": "",
            "coverage": None,
        })

    # Classify with Gemini (never raises — returns 811 fallback on any error)
    result = classify(question)

    red_flag = result.get("red_flag")
    if red_flag == "none":
        red_flag = None

    category = result.get("category")
    coverage = COVERAGE.get(category) if category else None

    why_one_line = result.get("why_one_line") or "Please consult a healthcare provider."

    return jsonify({
        "language": result.get("language"),
        "red_flag": red_flag,
        "category": category,
        "why_one_line": why_one_line,
        "coverage": coverage,
    })
