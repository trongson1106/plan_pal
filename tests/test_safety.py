"""pytest tests for data/safety.py keyword gate."""
import sys, os
sys.path.insert(0, os.path.join(os.path.dirname(__file__), ".."))

import pytest
from data.safety import check_safety


def tier(text):
    t, _ = check_safety(text)
    return t


# ---------------------------------------------------------------------------
# P0 false-positive fixes
# ---------------------------------------------------------------------------
class TestFalsePositives:
    def test_flu_shot_not_emergency(self):
        assert tier("I need a flu shot") is None

    def test_crushed_exam_not_emergency(self):
        assert tier("I crushed my exam") is None

    def test_drowning_in_homework_not_emergency(self):
        assert tier("I'm drowning in homework") is None

    def test_drowning_in_work_not_emergency(self):
        assert tier("drowning in work this semester") is None

    def test_allergy_shot_not_emergency(self):
        assert tier("I get allergy shots every month") is None

    def test_booster_shot_not_emergency(self):
        assert tier("do I need a booster shot for travel?") is None

    def test_shot_my_shot_not_emergency(self):
        assert tier("I shot my shot and asked her out") is None


# ---------------------------------------------------------------------------
# True positives that must still fire
# ---------------------------------------------------------------------------
class TestTruePositives:
    def test_got_shot(self):
        assert tier("I got shot") == "EMERGENCY_911"

    def test_cant_breathe(self):
        assert tier("I can't breathe") == "EMERGENCY_911"

    def test_asthma_attack(self):
        assert tier("I have an asthma attack") == "EMERGENCY_911"

    def test_inhaler_isnt_helping(self):
        assert tier("my inhaler isnt helping") == "EMERGENCY_911"

    def test_chest_pain(self):
        assert tier("chest pain") == "EMERGENCY_911"

    def test_drowning_no_ignore(self):
        # bare "drowning" with no ignore phrase should still fire
        assert tier("I think I'm drowning") == "EMERGENCY_911"

    def test_suicide(self):
        assert tier("I want to kill myself") == "CRISIS_988"

    def test_sexual_assault(self):
        assert tier("I was sexually assaulted") == "VIOLENCE_SAFETY"

    def test_assaulted_me(self):
        assert tier("someone assaulted me last night") == "VIOLENCE_SAFETY"

    def test_i_was_assaulted(self):
        assert tier("I was assaulted") == "VIOLENCE_SAFETY"


# ---------------------------------------------------------------------------
# Non-emergency inputs (should return None / URGENT_ER at most — no crash)
# ---------------------------------------------------------------------------
class TestNonEmergency:
    def test_inhaler_need_not_emergency(self):
        # "need my inhaler" removed from EMERGENCY_911 — goes to Gemini
        assert tier("I have asthma and need my inhaler") is None

    def test_sprained_ankle(self):
        assert tier("sprained ankle") is None

    def test_exam_stress(self):
        assert tier("Exam stress") is None

    def test_stomachache_no_crash(self):
        # May be None or URGENT_ER — just must not crash
        result = tier("I have a stomachach so bad")
        assert result in (None, "URGENT_ER", "EMERGENCY_911")

    def test_empty_string(self):
        assert tier("") is None


# ---------------------------------------------------------------------------
# Example chips — must pass through to Gemini (None)
# ---------------------------------------------------------------------------
class TestExampleChips:
    def test_ankle_chip(self):
        assert tier("I sprained my ankle playing sports") is None

    def test_stress_chip(self):
        assert tier("I've been really stressed and can't sleep") is None

    def test_asthma_chip(self):
        # "I have asthma and need my inhaler refilled" — inhaler *refill*, not emergency
        assert tier("I have asthma and need my inhaler refilled") is None


# ---------------------------------------------------------------------------
# Multilingual safety
# ---------------------------------------------------------------------------
class TestMultilingual:
    def test_mandarin_cant_breathe(self):
        assert tier("我喘不过气") == "EMERGENCY_911"

    def test_spanish_cant_breathe(self):
        assert tier("no puedo respirar") == "EMERGENCY_911"

    def test_mandarin_suicide(self):
        assert tier("我想死") == "CRISIS_988"

    def test_korean_suicide(self):
        assert tier("자살하고 싶어요") == "CRISIS_988"

    def test_hindi_cant_breathe(self):
        assert tier("मुझे सांस नहीं ले सकता") == "EMERGENCY_911"

    def test_farsi_suicide(self):
        assert tier("خودکشی می خواهم") == "CRISIS_988"

    def test_spanish_sexual_assault(self):
        assert tier("sufrí una agresión sexual") == "VIOLENCE_SAFETY"
