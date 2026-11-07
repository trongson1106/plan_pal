import json
import os

CATEGORIES = {
    "physio", "massage", "counselling",
    "dental_cleaning", "eye_exam", "prescription", "doctor_visit"
}

_JSON_PATH = os.path.join(os.path.dirname(os.path.abspath(__file__)), "data", "ubc_student_health_deals.json")


def _load():
    try:
        with open(_JSON_PATH, encoding="utf-8") as f:
            data = json.load(f)
    except Exception:
        return {}

    result = {}
    for entry in data.get("plan_coverage", []):
        svc = entry.get("service", "")
        limits = entry.get("limits", "")
        pct = entry.get("insured_pct")

        if "Physiotherapists" in svc:
            result["physio"] = {"per_visit": 40, "per_year": 400, "details": limits}
        elif "Massage therapists" in svc:
            result["massage"] = {"per_visit": 35, "per_year": 400, "details": limits}
        elif "Psychologist" in svc or "Counsellor" in svc:
            result["counselling"] = {"per_year": 1250, "details": limits}
        elif "Preventive" in svc and "cleanings" in svc:
            result["dental_cleaning"] = {
                "insured_pct": pct,
                "visits_per_year": 2,
                "max_per_year": 750,
                "details": limits,
            }
        elif "Eye exam" in svc:
            result["eye_exam"] = {"max_per_exam": 50, "every_years": 2, "details": limits}
        elif "Eligible prescriptions" in svc:
            result["prescription"] = {"insured_pct": pct, "details": limits}

    return result


COVERAGE = _load()
