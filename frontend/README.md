# PlanPal front end

`index.html` in the repo root is built from this folder. Don't edit `index.html` by hand; edit the files here and rebuild.

## Rebuild the page

From the repo root:

```
python frontend/build.py
```

It reads `data/ubc_student_health_deals.json`, writes `index.html`, and prints any clinics it couldn't place.

## Add or fix clinic data (Justin)

All in `data/ubc_student_health_deals.json`, then rebuild:

- **Booking links:** add `"booking_url": "https://..."` to a clinic. Use the page where a student can book (for example a Jane app link), not the home page. If there's no booking page, put the normal site in `"website"`. The page shows "Book online" for booking links it knows take bookings (Jane app, Specsavers) and "Website" for the rest.
- **New clinics:** the build places a new clinic at the centre of its postal code area (first 3 characters, about 1 to 2 km accuracy) and prints a note. That's fine for a demo.
- **Bad postal codes** are skipped and printed. Right now: Redtree Dental has `B6H 0B1`, which isn't a BC postal code.

## What's where

- `app.html`: the page, styles and logic. Plan numbers are near the top (`COVERAGE`).
- `i18n/`: translations. Every English key must exist in Chinese (simplified and traditional), Punjabi, Hindi and Korean.
- `places/static.js`: area shortcuts, BC postal-code centres, free campus services (UBC Student Health, UBC Counselling).
- `places/other_clinics.json`: walk-ins, massage and counselling clinics with no student deal.
- `places/coords.json`: saved map spots for clinics already placed.
- `places/booking_overrides.json`: booking links found by hand, used when the JSON has none.

## Handy links for testing

- `?api=mock` runs with made-up answers, no server needed (demo backup).
- `?today=2027-03-05` pretends it's another day, to show how the check-up plan changes over the year.
- Served from your own computer (any port), the page asks that same server. Anywhere else it asks the Render server.
