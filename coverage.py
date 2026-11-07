"""
coverage.py: every dollar figure in Covered lives here. Gemini only picks a category.

Source: Alumo plan pages (ubc-ams-gss.alumo.ca/health and /dental), pulled 2026-11-07.
Plan year: Sep 1, 2026 to Aug 31, 2027.
verified=True means the numbers match the Alumo page. Anything False shows "estimate".
"""

PLAN_YEAR_END = "Aug 31"

# Give this exact list to Jordan for the Gemini prompt (two new ones: chiropractor, vaccine).
CATEGORIES = [
    "physio",
    "massage",
    "chiropractor",
    "counselling",
    "dental_cleaning",
    "eye_exam",
    "prescription",
    "vaccine",
    "doctor_visit",
]

COVERAGE = {
    "physio": {
        "title": "Physiotherapy",
        "per_visit": 40,
        "annual_max": 400,
        "percent": 100,
        "plain": "The plan pays up to $40 per visit, up to $400 a year. You pay the rest of the bill.",
        "network_note": "Network physios cap fees at $75 for the first visit and $65 for follow-ups, "
                        "so you pay about $35 then $25. No doctor's referral needed.",
        "limit_note": "A doctor's note is needed after the 24th visit in a calendar year.",
        "verified": True,
    },
    "massage": {
        "title": "Massage therapy",
        "per_visit": 35,
        "annual_max": 400,
        "percent": 100,
        "plain": "The plan pays up to $35 per visit, up to $400 a year. You pay the rest of the bill.",
        "network_note": "There is no massage network for UBC, so any registered massage therapist works.",
        "limit_note": None,
        "verified": True,
    },
    "chiropractor": {
        "title": "Chiropractor",
        "per_visit": 35,
        "annual_max": 400,
        "percent": 100,
        "plain": "The plan pays up to $35 per visit, up to $400 a year. You pay the rest of the bill.",
        "network_note": "Network chiropractors cap fees at $75 for the first visit and $45 for follow-ups, "
                        "so you pay about $40 then $10.",
        "limit_note": None,
        "verified": True,
    },
    "counselling": {
        "title": "Counselling / psychology",
        "per_visit": None,       # the Alumo page lists only the combined yearly limit
        "annual_max": 1250,
        "percent": 100,
        "plain": "Fully covered up to $1,250 a year, combined. That covers psychologists, social workers, "
                 "registered clinical counsellors, and online CBT.",
        "network_note": "PsyVitaliti (network) offers reduced session rates on 50-minute sessions.",
        "limit_note": None,
        "verified": True,
    },
    "dental_cleaning": {
        "title": "Dental cleaning",
        "per_visit": None,
        "annual_max": 750,       # one $750 limit shared by ALL dental work
        "percent": 70,
        "percent_network": 100,
        "visits_per_year": 2,
        "plain": "The plan pays 70% of a cleaning. At a network dentist the network adds 30%, "
                 "so it can cost you $0.",
        "network_note": "Network dentists add 30% on preventive care, 20% on basic work.",
        "limit_note": "Cleaning once every 6 months, max 2 a year. The $750 dental limit is shared "
                      "with all dental work. For work expected to cost $300 or more, send a "
                      "treatment plan to Pacific Blue Cross first.",
        "verified": True,
    },
    "eye_exam": {
        "title": "Eye exam",
        "per_visit": 50,         # 1 exam, up to $50, per 2 policy years
        "annual_max": None,
        "percent": 100,
        "plain": "The plan pays one eye exam up to $50 every 2 policy years. Glasses or contacts: "
                 "up to $80 every 24 months (the receipt must show the prescription).",
        "network_note": "Network exams cost $60 to $99, so the plan covers most of it. "
                        "Many network optometrists also take $75 off glasses.",
        "limit_note": "1 exam per 2 policy years.",
        "verified": True,
    },
    "prescription": {
        "title": "Prescriptions",
        "per_visit": None,
        "annual_max": None,
        "percent": 80,
        "percent_network": 100,
        "plain": "The plan pays 80% of eligible prescriptions, with no deductible. At Rexall the "
                 "remaining 20% is covered up to $40, so many prescriptions cost $0.",
        "network_note": "Rexall covers the remaining 20% (max $40) when you show your plan card.",
        "limit_note": "BC students must register for Fair PharmaCare, or the plan stops paying "
                      "after $250 claimed.",
        "verified": True,
    },
    "vaccine": {
        "title": "Vaccines",
        "per_visit": None,
        "annual_max": 150,
        "percent": 100,
        "plain": "Vaccinations are covered up to $150 per policy year. A flu shot is covered up to $25 "
                 "(pharmacy fee capped at $15).",
        "network_note": "Rexall runs a free walk-in flu clinic at the Nest each fall (bring your MSP card).",
        "limit_note": None,
        "verified": True,
    },
    "doctor_visit": {
        "title": "Doctor visit",
        "per_visit": None,
        "annual_max": None,
        "percent": 100,
        "plain": "A visit with a family doctor or UBC Student Health is covered by provincial MSP, "
                 "so it costs you nothing.",
        "network_note": "UBC Student Health Service is on campus.",
        "limit_note": None,
        "verified": True,
    },
}


def estimate_you_pay(category, bill_total, spent_so_far=0):
    """Rough estimate of what the student pays for one visit. Returns None if numbers are missing."""
    info = COVERAGE.get(category)
    if not info or bill_total is None or info.get("percent") is None:
        return None

    plan_pays = bill_total * info["percent"] / 100
    if info.get("per_visit") is not None:
        plan_pays = min(plan_pays, info["per_visit"])
    if info.get("annual_max") is not None:
        plan_pays = min(plan_pays, max(info["annual_max"] - spent_so_far, 0))

    plan_pays = round(plan_pays, 2)
    remaining = None
    if info.get("annual_max") is not None:
        remaining = max(info["annual_max"] - spent_so_far - plan_pays, 0)
    return {"plan_pays": plan_pays, "you_pay": round(bill_total - plan_pays, 2), "est_remaining": remaining}


def get_card(category, spent_so_far=0):
    """The card the front end shows. Unknown categories fall back to doctor_visit (free via MSP)."""
    if category not in COVERAGE:
        category = "doctor_visit"
    info = COVERAGE[category]
    annual_max = info.get("annual_max")
    return {
        "category": category,
        "title": info["title"],
        "covered_text": info["plain"],
        "network_note": info.get("network_note"),
        "limit_note": info.get("limit_note"),
        "per_visit": info.get("per_visit"),
        "annual_max": annual_max,
        "est_remaining": max(annual_max - spent_so_far, 0) if annual_max is not None else None,
        "resets": PLAN_YEAR_END,
        "estimate": not info.get("verified", False),
    }


if __name__ == "__main__":
    print(get_card("physio"))
    print(estimate_you_pay("physio", 75))        # plan pays 40, you pay 35
    print(estimate_you_pay("chiropractor", 75))  # plan pays 35, you pay 40
    print(get_card("something_weird"))           # falls back to doctor_visit
