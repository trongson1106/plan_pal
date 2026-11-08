"""Integration tests for /ask. Gemini is mocked; safety gate runs for real."""
import sys, os
sys.path.insert(0, os.path.join(os.path.dirname(__file__), ".."))

import json
import pytest
from unittest.mock import patch

import app as app_module
from app import app as flask_app

# ---------------------------------------------------------------------------
# Shared Gemini mock — returns a minimal valid classify() result.
# ---------------------------------------------------------------------------
MOCK_OK = {"language": "en", "red_flag": "none", "urgency": "this_week",
           "why": "Physiotherapists usually treat this.", "needs": [
               {"category": "physio", "dental_type": None, "condition": None,
                "see_today": False, "practitioner": None,
                "why_one_line": "A physio can help.", "what_to_say_when_booking": "I have the AMS/GSS plan."}]}

MOCK_FALLBACK = {"language": "en", "red_flag": "811", "urgency": "today",
                 "why": "", "needs": [], "fallback": True, "error": True}


@pytest.fixture()
def client():
    flask_app.config["TESTING"] = True
    with flask_app.test_client() as c:
        yield c


def ask(client, question, mock_result=MOCK_OK):
    with patch("app.classify", return_value=mock_result):
        return client.post("/ask", json={"question": question},
                           content_type="application/json")


# ---------------------------------------------------------------------------
# Basic contract
# ---------------------------------------------------------------------------
class TestAsk:
    def test_health_endpoint(self, client):
        r = client.get("/health")
        assert r.status_code == 200
        assert r.get_json()["ok"] is True

    def test_empty_question_400(self, client):
        r = client.post("/ask", json={"question": ""})
        assert r.status_code == 400

    def test_too_long_question_400(self, client):
        r = client.post("/ask", json={"question": "x" * 501})
        assert r.status_code == 400

    def test_exactly_500_chars_ok(self, client):
        r = ask(client, "a" * 500)
        assert r.status_code == 200

    def test_missing_question_400(self, client):
        r = client.post("/ask", json={})
        assert r.status_code == 400

    def test_non_string_question_400(self, client):
        r = client.post("/ask", json={"question": 42})
        assert r.status_code == 400


# ---------------------------------------------------------------------------
# Example chip inputs go through Gemini (safety gate passes)
# ---------------------------------------------------------------------------
class TestChips:
    def test_ankle_chip(self, client):
        r = ask(client, "I sprained my ankle playing sports")
        assert r.status_code == 200
        d = r.get_json()
        assert d.get("red_flag") is None
        assert len(d["needs"]) > 0

    def test_stress_chip(self, client):
        r = ask(client, "I've been really stressed and can't sleep")
        assert r.status_code == 200

    def test_asthma_chip(self, client):
        r = ask(client, "I have asthma and need my inhaler refilled")
        assert r.status_code == 200


# ---------------------------------------------------------------------------
# Safety gate tiers — Gemini is NOT called (mock would catch it if it were)
# ---------------------------------------------------------------------------
class TestSafetyGate:
    def test_emergency_911_tier(self, client):
        with patch("app.classify", side_effect=AssertionError("Gemini should not be called")):
            r = client.post("/ask", json={"question": "I can't breathe"})
        assert r.status_code == 200
        assert r.get_json()["red_flag"] == "911"

    def test_crisis_988_tier(self, client):
        with patch("app.classify", side_effect=AssertionError("Gemini should not be called")):
            r = client.post("/ask", json={"question": "I want to kill myself"})
        assert r.status_code == 200
        assert r.get_json()["red_flag"] == "988"

    def test_violence_safety_tier(self, client):
        with patch("app.classify", side_effect=AssertionError("Gemini should not be called")):
            r = client.post("/ask", json={"question": "I was sexually assaulted"})
        assert r.status_code == 200
        assert r.get_json()["red_flag"] == "911"

    def test_poison_od_tier(self, client):
        with patch("app.classify", side_effect=AssertionError("Gemini should not be called")):
            r = client.post("/ask", json={"question": "I ate something toxic"})
        assert r.status_code == 200
        assert r.get_json()["red_flag"] == "911"

    def test_urgent_er_tier(self, client):
        with patch("app.classify", side_effect=AssertionError("Gemini should not be called")):
            r = client.post("/ask", json={"question": "I have a high fever that won't go down"})
        assert r.status_code == 200
        assert r.get_json()["red_flag"] == "911"


# ---------------------------------------------------------------------------
# Non-English emergency — safety gate fires without Gemini call
# ---------------------------------------------------------------------------
class TestNonEnglishSafety:
    def test_mandarin_cant_breathe(self, client):
        with patch("app.classify", side_effect=AssertionError("Gemini should not be called")):
            r = client.post("/ask", json={"question": "我喘不过气"})
        assert r.status_code == 200
        assert r.get_json()["red_flag"] == "911"

    def test_spanish_cant_breathe(self, client):
        with patch("app.classify", side_effect=AssertionError("Gemini should not be called")):
            r = client.post("/ask", json={"question": "no puedo respirar"})
        assert r.status_code == 200
        assert r.get_json()["red_flag"] == "911"


# ---------------------------------------------------------------------------
# Gemini failure → fallback response (no stack trace, fallback: true)
# ---------------------------------------------------------------------------
class TestFallback:
    def test_gemini_failure_returns_fallback(self, client):
        r = ask(client, "my ankle hurts", mock_result=MOCK_FALLBACK)
        assert r.status_code == 200
        d = r.get_json()
        assert d.get("fallback") is True
        assert d.get("red_flag") == "811"

    def test_no_stack_trace_on_failure(self, client):
        # The response body must be JSON, not an HTML traceback.
        r = ask(client, "my back hurts", mock_result=MOCK_FALLBACK)
        assert r.content_type.startswith("application/json")


# ---------------------------------------------------------------------------
# Response shape — urgency and why pass through
# ---------------------------------------------------------------------------
class TestResponseShape:
    def test_urgency_field_present(self, client):
        r = ask(client, "my ankle hurts")
        d = r.get_json()
        assert d.get("urgency") in ("today", "this_week", "self_care")

    def test_why_field_present(self, client):
        r = ask(client, "my ankle hurts")
        d = r.get_json()
        assert "why" in d
