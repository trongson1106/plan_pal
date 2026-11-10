"""
ER sign bullet points served in the /ask response (item 4).

Keyed by care category; `_GENERAL` is the default for any category not listed.
Add a category entry when the generic bullets don't fit well.
"""

_GENERAL = [
    "Trouble breathing",
    "Chest pain or pressure",
    "Confusion or hard to wake",
    "Fainting",
    "Symptoms getting quickly worse",
]

_INJURY = [
    "Bleeding that won't stop",
    "Bone visible or limb deformed",
    "Head hit with vomiting or confusion",
    "Numbness or can't move the area",
]

_ASTHMA = [
    "Can't speak full sentences",
    "Lips turning blue",
    "Inhaler not helping",
    "Chest pain",
]

_COUNSELLING = [
    "Thoughts of harming yourself — call or text 9-8-8",
]

_BY_CATEGORY = {
    "physio":           _INJURY,
    "medical_equipment": _INJURY,
    "counselling":      _COUNSELLING,
}


def er_signs_for(category, condition=None):
    """Return a list of ER sign bullet strings for a care category."""
    if condition == "asthma":
        return _ASTHMA
    return _BY_CATEGORY.get(category, _GENERAL)
