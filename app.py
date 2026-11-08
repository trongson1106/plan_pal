import os
import re

from flask import Flask, request, jsonify, send_from_directory
from flask_cors import CORS

try:
    from dotenv import load_dotenv
    load_dotenv()
except ImportError:
    pass

from data.safety import EMERGENCY_911, CRISIS_988
from api import classify
from coverage import coverage_for

app = Flask(__name__)
CORS(app)
app.json.ensure_ascii = False


def _phrase_regex(phrases):
    """Whole-word matching, so "backstroke" doesn't match "stroke"."""
    escaped = "|".join(re.escape(p) for p in phrases)
    return re.compile(r"(^|[^a-z0-9])(" + escaped + r")(?=$|[^a-z0-9])")


RE_911 = _phrase_regex(EMERGENCY_911)
RE_988 = _phrase_regex(CRISIS_988)


def _normalize(text):
    # Phones type curly apostrophes; make "can’t" match "can't".
    return re.sub(r"[‘’ʼ`´]", "'", text.lower())


def _safety_check(question):
    """Return '911', '988', or None. Never calls Gemini."""
    q = _normalize(question)
    if RE_911.search(q):
        return "911"
    if RE_988.search(q):
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
    question = (body.get("question") or "").strip()
    if not question:
        return jsonify({"error": "question is required"}), 400
    if len(question) > 2000:
        question = question[:2000]

    # Safety gate: Gemini is never called on 911/988 paths.
    flag = _safety_check(question)
    if flag:
        print(f"[safety] {flag} triggered, Gemini NOT called", flush=True)
        return jsonify({"language": None, "red_flag": flag, "needs": [],
                        "category": None, "why_one_line": "", "coverage": None, "what_to_say": None})

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
        })

    first = needs[0] if needs else {}
    return jsonify({
        "language": result.get("language"),
        "red_flag": red_flag,
        "needs": needs,
        # The fields below repeat the first need, for older versions of the page.
        "category": first.get("category"),
        "why_one_line": first.get("why_one_line") or "",
        "coverage": first.get("coverage"),
        "what_to_say": first.get("what_to_say"),
    })
