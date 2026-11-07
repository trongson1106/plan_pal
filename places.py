"""
places.py: loads the Alumo network JSON and answers "where is it cheaper?".
Save the JSON next to this file as alumo_data.json.
"""
import json
import os
import re

DATA_PATH = os.path.join(os.path.dirname(os.path.abspath(__file__)), "alumo_data.json")

# our category -> category name used in the JSON
CLINIC_CATEGORY = {
    "physio": "Physiotherapy",
    "chiropractor": "Chiropractic",
    "dental_cleaning": "Dental",
    "eye_exam": "Vision",
    "prescription": "Pharmacy",
}
OFFER_CATEGORY = {
    "physio": "Physiotherapy",
    "chiropractor": "Chiropractic",
    "dental_cleaning": "Dental",
    "eye_exam": "Vision",
    "prescription": "Pharmacy",
    "counselling": "Mental health",
    "vaccine": "Vaccines",
}

# Rough closeness to UBC by postal prefix (lower = closer). Approximate, not a real distance.
POSTAL_RANK = {
    "V6T": 1, "V6S": 1,
    "V6R": 2, "V6K": 2,
    "V6M": 3, "V6N": 3, "V6J": 3, "V6H": 3,
    "V6P": 4, "V5Z": 4,
    "V6Z": 5, "V6B": 5, "V6E": 5, "V6G": 5, "V6C": 5, "V5Y": 5,
}


def _norm(text):
    return re.sub(r"[^a-z0-9]", "", (text or "").lower())


def _fix_postal(postal):
    postal = (postal or "").upper().strip()
    # data typo: Redtree Dental is listed as B6H 0B1
    return "V" + postal[1:] if postal.startswith("B6H") else postal


def _load():
    with open(DATA_PATH, encoding="utf-8") as f:
        raw = json.load(f)

    seen, clinics = set(), []
    for c in raw.get("clinics", []):
        key = (c["category"], _norm(c["address"]))   # drops repeat rows for the same location
        if key in seen:
            continue
        seen.add(key)

        postal = _fix_postal(c.get("postal_code"))
        near_ubc = (c.get("on_or_near_ubc_campus") or "").strip().lower() == "yes"
        clinics.append({
            "category": c["category"],
            "name": c["clinic_name"],
            "address": c["address"],
            "city": c.get("city"),
            "postal_code": postal,
            "phone": c.get("phone"),
            "website": c.get("website") or None,
            "deal": c.get("deal_summary"),
            "you_pay_note": c.get("with_plan_coverage"),
            "near_ubc": near_ubc,
            "rank": 0 if near_ubc else POSTAL_RANK.get(postal[:3], 9),
        })
    return clinics, raw.get("offers", [])


_CLINICS, _OFFERS = _load()


def find_places(category, limit=3):
    """Closest network places for one of our categories. Returns [] if there is no network."""
    wanted = CLINIC_CATEGORY.get(category)
    if not wanted:
        return []
    matches = [c for c in _CLINICS if c["category"] == wanted]
    matches.sort(key=lambda c: (c["rank"], c["name"]))
    return [{k: v for k, v in c.items() if k != "rank"} for c in matches[:limit]]


def get_offers(category):
    """Offers (discounts, top-ups) for a category. Check 'availability' before showing."""
    wanted = OFFER_CATEGORY.get(category)
    return [o for o in _OFFERS if o["category"] == wanted] if wanted else []


if __name__ == "__main__":
    print(len(_CLINICS), "unique clinics loaded")
    for p in find_places("physio"):
        print(p["name"], "|", p["deal"], "|", p["you_pay_note"])
    print(find_places("massage"))   # [] because there is no massage network



