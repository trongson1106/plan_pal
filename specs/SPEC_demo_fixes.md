# Spec: PlanPal pre-demo fixes

## Goal
Make small, safe improvements before the hackathon demo. **Keep the app's core unchanged**: the Flask `/ask` endpoint, the safety gate before Gemini, the Gemini classifier, the coverage lookup, and the single-file `index.html` frontend. Do not refactor, rename files, add frameworks, or redesign screens. Prefer the smallest change that satisfies each item.

## Before you start
1. Read `app.py`, `api.py`, `data/safety.py`, and `data/coverage.py`.
2. `index.html` is large (~376 KB, inline CSS and JS). **Do not read it whole.** Use grep to find the relevant sections (safety overlay, result rendering, privacy notice, history, coverage page, i18n strings) and edit only those parts.
3. Post a short plan (files and functions to touch) before editing. Then do the items in the priority order below, and commit after each item if git is available.
4. This spec replaces any earlier "severity tiers" spec. Item 4 below is the lightweight version.

## Priority order
P0 (must): items 1, 2, 3, 4, 5
P1 (should): items 6, 7, 8
P2 (if time): items 9, 10

---

## P0

### 1. Make the privacy copy accurate
**Problem:** The app says questions aren't stored. That is true server-side, but the text is sent to Google's Gemini API.

**Change:**
- Find the "Private by design" notice and its "How it works" content in `index.html`.
- Update the copy (and all translations of it) to the equivalent of:
  - Short line: "No account. We don't save your questions."
  - "How it works" detail: "Your question is sent to Google's AI to work out the right type of care. We don't keep it on our servers. Recent questions stay only on this device."
- Keep it plain language, one tap to read.

**Done when:** The notice mentions that text is sent to Google's AI, and the English string is present in every language the UI supports (or falls back to English).

### 2. Fix false positives in the safety keyword gate (`data/safety.py`)
**Problem:** Some keywords will fire on normal student language and send people to a false emergency screen. Example: "flu shot" matches `shot`.

**Change (edit the keyword lists; keep the same tiers and structure):**
- Replace the bare words below with specific phrases:
  - `shot` -> `got shot`, `was shot`, `been shot`, `gunshot`, `shot in the`
  - `crushed` -> `crushed by`, `crushed my hand`, `crushed my leg`, `crushed my foot`
  - `swallowed` (in POISON_OD) -> `swallowed bleach`, `swallowed poison`, `swallowed a battery`, `swallowed a magnet`, `kid swallowed`, `child swallowed`, `baby swallowed`
  - `choking` -> `choking on food`, `is choking`, `am choking`, `cant stop choking`, `baby choking`
  - `assaulted` stays, but remove it from matching figurative uses by requiring an adjacent context where practical (`i was assaulted`, `got assaulted`, `assaulted me`)
  - `drowning` -> `drowning`, `almost drowned`, `near drowning` (remove "drowning in homework" risk by also adding a small ignore list, see below)
- **Inhaler phrases:** keep `inhaler not working`, `inhaler isnt helping`, `inhaler isnt working`, `cant breathe`, `asthma attack` as `EMERGENCY_911`. **Remove `need my inhaler`, `lost my inhaler` from `EMERGENCY_911`.** Treat them as non-emergency: pass to Gemini (do not call 911). Instead, handled in item 4 below via a follow-up line on the result: "If you're struggling to breathe or your inhaler isn't helping, call 911."
- Add a small `IGNORE_PHRASES` list checked **before** matching. If the normalized text contains one of these, skip the single-word-style matches it would trigger (not the multi-word emergencies):
  - `flu shot`, `covid shot`, `vaccine shot`, `allergy shot`, `booster shot`, `drowning in homework`, `drowning in work`, `dying of laughter`, `killing it`, `crushed my exam`, `crushed it`, `i could die of`, `shot my shot`
- Keep this principle: **missing a real emergency is worse than a false alarm.** Only loosen the specific cases above. Do not remove any other keywords.

**Add a test file** `tests/test_safety.py` (pytest) with at least these cases:

| Input | Expected tier |
|---|---|
| "I need a flu shot" | None |
| "I crushed my exam" | None |
| "I'm drowning in homework" | None |
| "I got shot" | EMERGENCY_911 |
| "I can't breathe" | EMERGENCY_911 |
| "I have an asthma attack" | EMERGENCY_911 |
| "my inhaler isnt helping" | EMERGENCY_911 |
| "I have asthma and need my inhaler" | None (goes to Gemini) |
| "I want to kill myself" | CRISIS_988 |
| "I was sexually assaulted" | VIOLENCE_SAFETY |
| "chest pain" | EMERGENCY_911 |
| "I have a stomachach so bad" | None or URGENT_ER (either fine, no crash) |
| "sprained ankle" | None |
| "Exam stress" | None |

Also run each of the three example chips through the gate and assert the tier. Fix any failure by editing keywords, not by weakening the test.

### 3. Make non-English safety work
**Problem:** The keyword gate is English-only but the app accepts any language.

**Change:**
- In `api.py`/`app.py`: when Gemini returns `red_flag` of `911` or `988`, the response must trigger **the same full-screen safety overlay** in `index.html` that a keyword hit triggers. Confirm this path exists end to end; fix if not.
- Add a short multilingual keyword list in `data/safety.py` as a **second pass** (same matching and normalization approach), covering the highest-risk phrases only, for: Mandarin (simplified and traditional), Cantonese (written), Punjabi (Gurmukhi), Hindi, Korean, Spanish, Farsi, French. Cover these concepts per language, 1 to 3 common phrasings each:
  - can't breathe / chest pain -> `EMERGENCY_911`
  - suicide / want to die / kill myself -> `CRISIS_988`
  - overdose / took too many pills -> `EMERGENCY_911`
  - sexual assault / someone is hurting me -> `VIOLENCE_SAFETY`
- Do not rely on ASCII-only normalization for these: the `normalize()` step must not delete non-Latin characters when matching this list (match these on NFKC-normalized text, with simple substring matching for CJK since there are no word boundaries).
- Mark the list with a comment: "REVIEW BY NATIVE SPEAKERS BEFORE PRODUCTION."

**Done when:** A Mandarin "我喘不过气" (can't breathe) and a Spanish "no puedo respirar" show the safety overlay without a Gemini call.

### 4. Show urgency, a one-line "why", and "Go to the ER if..." on results
**Problem:** Results say "See a doctor" with no urgency level or safety net. The red flag only appears for 811/911/988.

**Change in `api.py` (Gemini prompt and parsing):**
- Add two fields to the JSON the model returns, per overall response (not per need):
  - `urgency`: one of `"today"`, `"this_week"`, `"self_care"`
  - `why`: one sentence (max ~20 words), plain language, explains the urgency, **no diagnosis**. Example: "Severe pain that lasts more than a few hours should be checked today."
- Add to the prompt: choose `today` if there is severe, sudden, worsening, or unclear-but-concerning symptoms; when unsure, choose the more urgent option; never choose `self_care` if `red_flag` is not `none`.
- Validate the JSON response strictly: `urgency` must be one of the allowed values, `red_flag` one of `none|811|911|988`, category one of the known coverage categories. Anything invalid -> use the fallback (item 5).
- Enforce in code (not just the prompt): if `red_flag` != `none` then `urgency` can't be `self_care`; if `red_flag` is `811` then urgency is at least `today`.

**Change in `index.html`:**
- On the result screen, show a small **urgency badge** with icon + text (do not rely on colour alone):
  - today: "See someone today" (amber, clock icon)
  - this_week: "This week" (blue, calendar icon)
  - self_care: "Self-care first" (green, home icon)
- Show the `why` line directly under the headline.
- Add a **"Go to the ER if..." card** below the main action, on every result (collapsed by default for `self_care`, expanded otherwise), with a "Call 911" button. Source the bullets from a static table in one place (e.g. `data/er_signs.py` served in the `/ask` response, or a JS object), keyed by category, with a `general` default:
  - general: trouble breathing; chest pain or pressure; confusion or hard to wake; fainting; symptoms getting quickly worse
  - abdominal: pain that is sudden and severe; belly hard or very tender; vomiting blood or black stool; fever with the pain; can't keep fluids down
  - breathing/asthma: can't speak full sentences; lips turning blue; inhaler not helping; chest pain
  - injury: bleeding that won't stop; bone visible or limb deformed; head hit with vomiting or confusion; numbness or can't move the area
  - mental health: thoughts of harming yourself (call or text 9-8-8)
- For asthma / inhaler results, put this line at the top of the card: "If you're struggling to breathe or your inhaler isn't helping, call 911."
- All new strings go through the existing i18n/translation mechanism. If a translation is missing, fall back to English.
- Add a one-line footer on results: "PlanPal helps you find care. It can't diagnose."

**Done when:** Every result shows a badge, a why line, and the ER card. A `red_flag: "811"` result is never shown as self-care.

### 5. Don't fail silently
**Problem:** If Gemini errors or returns unusable JSON, the app falls back to 811 with no explanation.

**Change:**
- In `api.py`, keep the fallback (`red_flag: "811"`, `urgency: "today"`) but add `fallback: true` to the response.
- In `index.html`, when `fallback` is true, show a visible line above the result: "We couldn't process that just now. If you're worried, call HealthLink BC at 811." Translated via the existing i18n.
- Add a request timeout (e.g. 10 s) to the Gemini call so the UI doesn't hang. On timeout use the same fallback.
- Log the error server-side (type only, **not the user's text**).

**Done when:** Setting an invalid `GEMINI_API_KEY` yields the fallback message in the UI with no stack trace and no hang.

---

## P1

### 6. Lock down the server (`app.py`)
- Cap `question` length at 500 characters (trim, return 400 with a friendly message if empty or longer). Reject non-string input.
- Add a simple rate limit on `/ask` (e.g. 20 requests/minute per IP; use `flask-limiter` or a small in-memory counter; if adding a library, add it to the install line).
- Restrict `flask-cors` to the app's own origin (read from an env var like `ALLOWED_ORIGIN`, default same-origin / localhost for dev) instead of `*`.
- Ensure `.env` is in `.gitignore`. Never log the API key or the user's question.

### 7. Hide and clear history
- In `index.html`, add a "Clear history" action in the recent questions section and in settings.
- Add a setting "Show recent questions on home" (default **off**). When off, don't render the list on the home screen.
- Wording on the list: "Saved only on this device."

### 8. Soften claims about plan data and MSP
- On the coverage page, add: "Plan details from Alumo, as of Nov 7, 2026. Confirm with Pacific Blue Cross before booking." Date comes from the JSON's pull date, not hardcoded.
- Replace "Free with MSP" with logic that reads a one-time setting "Do you have BC MSP?" (stored in `localStorage`, default **yes**). If **no**, show "Cost varies. Ask the clinic about fees for people without BC MSP."
- Eye exam row: remove "Due now" unless the user has entered a last-exam date. Otherwise show "Covered once every 2 years."

---

## P2 (only if time)

### 9. Show hours on clinic results
- If the clinic data already has hours, show "Open now / Closes 8 pm" or "Closed". If not, skip. Do not invent hours.
- When the user's local time is outside open hours for every listed clinic and `urgency` is `today`, show 811 and the nearest ER first.

### 10. Booking script in two languages
- Under "What to say when you call", show the script in English (to say) with the user's language below it (to read). Keep the "Read aloud" button reading the English script.

---

## Demo insurance
- Add `tests/test_ask.py` with ~15 inputs hitting `/ask` (Gemini mocked): the three example chips, a safety hit for each tier, a non-English emergency, an empty string, a 600-character string, and a Gemini failure.
- Cache the response for the three example chips (a small dict keyed by chip text, used only when Gemini fails or times out) so the demo still works if the API or the wifi fails. Mark clearly in code as `DEMO_FALLBACK`.

## Constraints and non-goals
- Do not change the coverage dollar amounts or `ubc_student_health_deals.json`.
- Do not change how the clinic finder or "Change area" work.
- Do not change the visual identity (dark green primary, layout, typography).
- Do not diagnose, name conditions, or suggest treatments anywhere.
- Do not log or store user question text server-side.
- If you are unsure whether a change is in scope, skip it and list it under "Not done" in your final summary.

## Final checklist (report back)
1. List each item (1 to 10) as done, partially done, or skipped, with the files changed.
2. Paste the pytest output.
3. Manually verify and state results for: "flu shot", "I can't breathe", "I have asthma and need my inhaler", a Mandarin emergency phrase, and an invalid API key.
4. List any assumptions you made.
