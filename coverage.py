
# Categories Gemini is allowed to return. Anything else falls back to "doctor_visit".
CATEGORIES = [
    "physio",
    "massage",
    "counselling",
    "dental_cleaning",
    "eye_exam",
    "prescription",
    "doctor_visit",
]

COVERAGE = {
    "physio": {
        "title": "Physiotherapy",
        "per_visit": 40,          # plan pays up to $40 per visit
        "annual_max": 400,        # about 10 visits
        "percent": 100,           # 100% of the covered amount, capped at per_visit
        "plain": "The plan pays up to $40 per visit, up to $400 a year. "
                 "You pay the rest of the bill.",
        "where_free": None,       # fill in if you find a student/teaching clinic that bills $0
        "verified": True,         # from your Pacific Blue Cross screenshots
    },
    "massage": {
        "title": "Massage therapy",
        "per_visit": 35,
        "annual_max": 400,
        "percent": 100,
        "plain": "The plan pays up to $35 per visit, up to $400 a year. "
                 "You pay the rest of the bill.",
        "where_free": None,
        "verified": True,
    },
    "counselling": {
        "title": "Counselling / psychology",
        "per_visit": 300,         # registered psychologist limit. CHECK the clinical counsellor limit
        "annual_max": 1250,
        "percent": 100,
        "plain": "Fully covered up to $300 per session and $1,250 a year "
                 "(roughly 8 or more sessions).",
        "where_free": "UBC Student Health & Counselling offers a few free sessions first.",
        "verified": False,        # confirm clinical counsellor per-visit limit
    },
    "dental_cleaning": {
        "title": "Dental cleaning",
        "per_visit": None,
        "annual_max": 750,        # overall dental maximum, shared with other dental work
        "percent": 70,            # 70% normally, 100% at an Alumo network dentist
        "percent_network": 100,
        "visits_per_year": 2,
        "plain": "The plan pays 70% of a cleaning. At a network dentist it pays "
                 "100%, so you pay $0. Up to 2 cleanings a year.",
        "where_free": "Alumo network dentists (confirm the campus dentist is in the network).",
        "verified": False,        # confirm network wording and the 2 per year limit
    },
    "eye_exam": {
        "title": "Eye exam",
        "per_visit": None,        # TODO: read from the app
        "annual_max": None,       # TODO
        "percent": None,
        "plain": "Vision care is covered by the plan. Check the exact amount in "
                 "the Pacific Blue Cross app.",
        "where_free": "The optometrist in the Nest offers a discount on contacts (confirm 10% vs 20%).",
        "verified": False,
    },
    "prescription": {
        "title": "Prescriptions",
        "per_visit": None,
        "annual_max": None,
        "percent": None,
        "plain": "The plan covers most of the cost of prescriptions. At a network "
                 "pharmacy (for example Rexall) your out-of-pocket cost is lower.",
        "where_free": "Network pharmacies such as Rexall. Confirm the dispensing-fee cap.",
        "verified": False,        # your story: ~$20 at Shoppers vs $0 at Rexall
    },
    "doctor_visit": {
        "title": "Doctor visit",
        "per_visit": None,
        "annual_max": None,
        "percent": 100,
        "plain": "A visit with a family doctor or at UBC Student Health is covered "
                 "by provincial MSP, so it costs you nothing.",
        "where_free": "UBC Student Health Service",
        "verified": True,
    },
}




