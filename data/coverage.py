"""
What the UBC AMS/GSS plan pays, per category.

Numbers come from data/ubc_student_health_deals.json ("plan_coverage", pulled
2026-11-07 from ubc-ams-gss.alumo.ca) and Alumo's health page. They're written
out here so the server still answers if the JSON file is missing.

The front end keeps the same numbers (with translations). If you change a
number here, tell Jaipaul so the page is updated too.
"""

# Every category the Gemini prompt is allowed to return.
CATEGORIES = {
    "physio",              # physiotherapist
    "massage",             # registered massage therapist
    "chiropractor",
    "other_practitioner",  # naturopath, osteopath, podiatrist, dietitian, speech therapist, athletic therapist
    "counselling",         # psychologist, counsellor, social worker
    "dental",              # anything teeth or gums (see DENTAL_TYPES)
    "vision",              # eye exam, glasses, contacts
    "prescription",        # medication, refills, pharmacy, birth control pills
    "vaccine",             # flu shot, travel or other vaccines
    "doctor_visit",        # family doctor or walk-in (covered by MSP, not this plan)
    "medical_equipment",   # crutches, braces, orthotics, wheelchair rental
    "hearing",             # hearing aids
    "other",               # nothing above fits; the page says "see a doctor"
}

DENTAL_TYPES = {"preventive", "basic", "extraction", "major", "accidental"}

CONDITIONS = {
    "diabetes", "asthma", "hearing_loss", "severe_allergy",
    "injury_support", "foot", "birth_control", "other_ongoing",
}

# per_visit / per_year are dollars. percent is what the plan pays.
# network_percent is the extra discount at an Alumo network clinic.
COVERAGE = {
    "physio":             {"per_visit": 40, "per_year": 400},
    "massage":            {"per_visit": 35, "per_year": 400},
    "chiropractor":       {"per_visit": 35, "per_year": 400},
    "other_practitioner": {"per_visit": 35, "per_year": 400},
    "counselling":        {"per_visit": None, "per_year": 1250, "percent": 100},
    "dental":             {"per_visit": None, "per_year": 750},
    "vision":             {"per_visit": None, "per_year": None,
                           "eye_exam": 50, "eye_exam_every_years": 2,
                           "eyewear": 80, "eyewear_every_months": 24},
    "prescription":       {"per_visit": None, "per_year": None, "percent": 80,
                           "network_topup": "Rexall covers the other 20%, up to $40"},
    "vaccine":            {"per_visit": None, "per_year": 150, "percent": 100},
    "doctor_visit":       {"per_visit": None, "per_year": None, "free_with_msp": True},
    "medical_equipment":  {"per_visit": None, "per_year": None,
                           "orthotics_per_year": 300, "orthopedic_shoes_per_year": 500},
    "hearing":            {"per_visit": None, "per_year": None,
                           "hearing_aids": 500, "hearing_aids_every_years": 5},
    "other":              None,
}

DENTAL_COVERAGE = {
    "preventive": {"percent": 70, "network_percent": 30},   # cleanings, checkups: 100% at a network dentist
    "extraction": {"percent": 70, "network_percent": 20},
    "basic":      {"percent": 50, "network_percent": 20},   # fillings, gum treatment, root canals
    "major":      {"percent": 0,  "network_percent": 20},   # crowns, bridges
    "accidental": {"percent": None, "network_percent": None,
                   "note": "Accidental dental: tooth damaged by a blow to the mouth, treatment within 12 months"},
}


def coverage_for(category, dental_type=None):
    """Return the coverage dict for a category (with dental type merged in)."""
    base = COVERAGE.get(category)
    if base is None:
        return None
    result = dict(base)
    if category == "dental" and dental_type in DENTAL_COVERAGE:
        result.update(DENTAL_COVERAGE[dental_type])
        result["dental_type"] = dental_type
    return result
