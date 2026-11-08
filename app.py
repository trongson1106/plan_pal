import os

from flask import Flask, request, jsonify, send_from_directory
from flask_cors import CORS
from flask_limiter import Limiter
from flask_limiter.util import get_remote_address

try:
    from dotenv import load_dotenv
    load_dotenv()
except ImportError:
    pass

from data.safety import check_safety
from api import classify
from data.coverage import coverage_for, get_plan_meta
from data.er_signs import er_signs_for

app = Flask(__name__)

ALLOWED_ORIGIN = os.getenv("ALLOWED_ORIGIN", "*")
CORS(app, origins=ALLOWED_ORIGIN)
app.json.ensure_ascii = False

limiter = Limiter(
    app=app,
    key_func=get_remote_address,
    default_limits=[],
    storage_uri="memory://",
)

_TIER_TO_FLAG = {
    "EMERGENCY_911":   "911",
    "CRISIS_988":      "988",
    "VIOLENCE_SAFETY": "911",
    "POISON_OD":       "911",
    "URGENT_ER":       "911",
}


@app.get("/")
def index():
    return send_from_directory(".", "index.html")


@app.get("/logo/<path:filename>")
def logo(filename):
    return send_from_directory("logo", filename)


@app.get("/health")
def health():
    return jsonify({"ok": True})


@app.get("/plan-meta")
def plan_meta():
    return jsonify(get_plan_meta())


@app.post("/ask")
@limiter.limit("20 per minute")
def ask():
    body = request.get_json(silent=True) or {}
    if not isinstance(body.get("question"), str):
        return jsonify({"error": "question is required"}), 400
    question = body["question"].strip()
    if not question:
        return jsonify({"error": "question is required"}), 400
    if len(question) > 500:
        return jsonify({"error": "question too long (max 500 characters)"}), 400

    # Safety gate: Gemini is never called on safety paths.
    tier, kw = check_safety(question)
    if tier:
        flag = _TIER_TO_FLAG.get(tier, "911")
        print(f"[safety] {tier} ({kw!r}) triggered, Gemini NOT called", flush=True)
        return jsonify({"language": None, "red_flag": flag, "urgency": "today",
                        "why": "", "needs": [], "category": None,
                        "why_one_line": "", "coverage": None, "what_to_say": None,
                        "fallback": False})

    result = classify(question)  # never raises

    red_flag = result.get("red_flag")
    if red_flag == "none":
        red_flag = None

    needs = []
    for n in result.get("needs", []):
        needs.append({
            "category": n["category"],
            "dental_type": n.get("dental_type"),
            "condition": n.get("condition"),
            "see_today": n.get("see_today", False),
            "practitioner": n.get("practitioner"),
            "why_one_line": n.get("why_one_line"),
            "what_to_say": n.get("what_to_say_when_booking"),
            "coverage": coverage_for(n["category"], n.get("dental_type")),
            "er_signs": er_signs_for(n["category"], n.get("condition")),
        })

    first = needs[0] if needs else {}
    return jsonify({
        "language": result.get("language"),
        "red_flag": red_flag,
        "urgency": result.get("urgency", "this_week"),
        "why": result.get("why", ""),
        "fallback": result.get("fallback", False),
        "needs": needs,
        # Legacy fields for older page versions.
        "category": first.get("category"),
        "why_one_line": first.get("why_one_line") or "",
        "coverage": first.get("coverage"),
        "what_to_say": first.get("what_to_say"),
    })
