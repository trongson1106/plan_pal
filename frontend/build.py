"""
Builds the PlanPal page (index.html in the repo root) from:
  frontend/app.html                 the page template
  frontend/i18n/*.js                translations
  frontend/places/*                 areas, postal-code centres, campus places
  data/ubc_student_health_deals.json   the clinics and deals (Justin's file)

Run from the repo root:   python frontend/build.py
Only uses the Python standard library.
"""
import json
import os
import re
import sys

HERE = os.path.dirname(os.path.abspath(__file__))
ROOT = os.path.dirname(HERE)
DEALS = os.path.join(ROOT, "data", "ubc_student_health_deals.json")
OUT = os.path.join(ROOT, "index.html")

CATEGORY = {"Dental": "dental", "Vision": "vision", "Chiropractic": "chiropractor",
            "Physiotherapy": "physio", "Pharmacy": "prescription"}


def read(*parts):
    with open(os.path.join(HERE, *parts), encoding="utf-8") as f:
        return f.read()


def load_json(*parts):
    return json.loads(read(*parts))


def build_network():
    """Clinics with student deals, placed on the map.

    Location: the saved spot for a clinic we've placed before (coords.json),
    otherwise the centre of its postal code's first 3 characters.
    Link: "booking_url" in the deals JSON, else places/websites.json (found by
    hand, keyed "name|address"), else booking_overrides.json, else "website".
    "b": 1 marks a link we know takes online bookings.
    """
    with open(DEALS, encoding="utf-8") as f:
        deals = json.load(f)
    coords = load_json("places", "coords.json")
    overrides = load_json("places", "booking_overrides.json")
    found = load_json("places", "websites.json")
    fsa = json.loads(re.search(r"const FSA = (\{.*?\});", read("places", "static.js"), re.S).group(1))

    network, warnings = [], []
    for c in deals.get("clinics", []):
        name = (c.get("clinic_name") or "").strip()
        address = (c.get("address") or "").strip()
        cat = CATEGORY.get(c.get("category"))
        if not cat:
            warnings.append(f"Unknown category '{c.get('category')}' for {name}: skipped")
            continue
        postal = re.sub(r"\s+", "", (c.get("postal_code") or "").upper())
        if name + "|" + address in coords:
            lat, lng = coords[name + "|" + address]
        elif postal[:3] in fsa:
            lat, lng = fsa[postal[:3]]
            warnings.append(f"Placed by postal area only (about 1-2 km accuracy): {name}, {postal}")
        else:
            warnings.append(f"Bad postal code '{c.get('postal_code')}' for {name}: skipped. Fix it in the JSON.")
            continue
        entry = {"c": cat, "n": name, "a": address, "p": (c.get("phone") or "").strip(),
                 "d": (c.get("deal_summary") or "").strip(),
                 "lat": round(lat, 5), "lng": round(lng, 5),
                 "campus": c.get("on_or_near_ubc_campus") == "Yes"}
        extra = found.get(name + "|" + address, {})
        booking = (c.get("booking_url") or "").strip() or extra.get("booking_url", "") or overrides.get(name, "")
        url = booking or (c.get("website") or "").strip() or extra.get("website", "")
        if url:
            if not url.startswith("http"):
                url = "https://" + url
            if "rexall.ca" in url:
                url = "https://www.rexall.ca/flu"   # Rexall's booking page is for flu shots
            entry["w"] = url
            if booking:
                entry["b"] = 1
        network.append(entry)
    return network, warnings


def main():
    network, warnings = build_network()
    other = read("places", "other_clinics.json")
    data = (read("places", "static.js") + "\n"
            + "const NETWORK = " + json.dumps(network, ensure_ascii=False, separators=(",", ":")) + ";\n"
            + "const OTHER_CLINICS = " + other.strip() + ";\n")

    i18n = lambda name: read("i18n", name)
    merge = '''
function mergeI18n(lang, add) {
  const target = I18N[lang] || (I18N[lang] = { cat: {} });
  target.cat = target.cat || {};
  for (const [k, v] of Object.entries(add)) {
    if (k === "cat") { for (const [c, f] of Object.entries(v)) target.cat[c] = Object.assign({}, target.cat[c] || {}, f); }
    else if (k === "cond") target.cond = v;
    else target[k] = v;
  }
}
mergeI18n("en", I18N_V3_EN);
for (const [lang, add] of Object.entries(I18N_V3)) mergeI18n(lang, add);
mergeI18n("en", I18N_V4_EN);
for (const [lang, add] of Object.entries(I18N_V4)) mergeI18n(lang, add);
mergeI18n("en", I18N_V5_EN);
for (const [lang, add] of Object.entries(I18N_V5)) mergeI18n(lang, add);
'''
    extra = "\n".join(i18n(n) for n in ["i18n_v3_en.js", "i18n_v3_other.js", "i18n_v4_en.js",
                                         "i18n_v4_other.js", "i18n_v5_en.js", "i18n_v5_other.js"])
    page = (read("app.html")
            .replace("/*__I18N__*/", i18n("i18n.js"))
            .replace("/*__I18N_V2__*/", i18n("i18n_v2.js"))
            .replace("/*__I18N_V3__*/", extra + merge)
            .replace("/*__DATA__*/", data))
    if "/*__" in page.split("<script>", 1)[1][:400]:
        sys.exit("A placeholder was not filled in. Check frontend/app.html.")
    with open(OUT, "w", encoding="utf-8") as f:
        f.write(page)

    with_links = sum(1 for p in network if p.get("w"))
    print(f"Wrote {OUT}")
    print(f"{len(network)} clinics with deals, {with_links} with a website or booking link.")
    for w in warnings:
        print("  note:", w)


if __name__ == "__main__":
    main()
