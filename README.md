# [PlanPal](https://ubc-coverage-server.onrender.com/)

> **Find the right care. Know what your plan covers.**

PlanPal helps UBC students act on a health concern in under 30 seconds. Describe what is going on in plain language — any language — and PlanPal tells you which type of professional to see, exactly what your AMS/GSS plan pays, and what to say when you call to book.

Built at **Hackcamp 2026**.

---

## How it works

```
Student types (or speaks) a health concern
        │
        ▼
Safety gate  ──── keyword match? ──→  Emergency screen (911 / 988 / VictimLink / 811)
        │ no match
        ▼
Gemini AI classifier
  · Detects language (ISO 639-1)
  · Sets red flag  (none / 811 / 911 / 988)
  · Returns up to 3 care needs with one-line explanations and booking scripts
        │
        ▼
Coverage lookup  →  per-visit cap, annual limit, % paid by Pacific Blue Cross
        │
        ▼
Frontend renders results, clinic finder, and "what to say when you book"
```

The safety gate runs **before** Gemini is ever called. If a keyword from the 100+ term list matches, the AI is never invoked — the emergency screen appears immediately.

---

## Coverage supported

| Category | Per Visit | Annual Limit |
|---|---|---|
| Physiotherapy | $40 | $400 |
| Massage (RMT) | $35 | $400 |
| Chiropractor | $35 | $400 |
| Other practitioners | $35 | $400 |
| Counselling | 100% | $1,250 |
| Dental | — | $750 (70% preventive · 50% basic) |
| Vision | — | $50 eye exam (every 2 yrs) · $80 eyewear (every 24 mo) |
| Prescriptions | 80% | Rexall covers the other 20% (up to $40) |
| Vaccines | 100% | $150 |
| Doctor visit | Free | Covered by MSP |
| Medical equipment | — | Orthotics $300/yr · Orthopedic shoes $500/yr |
| Hearing aids | — | $500 every 5 yrs |

Insurer: **Pacific Blue Cross** (group 43979), administered by **Alumo**.
Coverage numbers sourced from `data/ubc_student_health_deals.json` (pulled 2026-11-07).

---

## Project structure

```
.
├── app.py                          # Flask server — /ask, /health, /plan-meta
├── api.py                          # Gemini classifier (care category, red flags)
├── data/
│   ├── safety.py                   # Pre-AI keyword safety triage (5 tiers)
│   ├── coverage.py                 # Plan dollar amounts per category
│   └── ubc_student_health_deals.json
├── index.html                      # Full SPA — HTML + CSS + vanilla JS (no build step)
├── logo/
│   ├── planpal-logo.svg
│   └── favicon.svg
├── tests/
│   ├── test_ask.py
│   ├── test_safety.py
│   ├── test_gemini.py
│   └── test_prompt.py
└── requirements.txt
```

---

## Running locally

**Prerequisites:** Python 3.11+, a [Google AI Studio](https://aistudio.google.com) API key.

```bash
# 1. Clone and create a virtual environment
python -m venv venv
source venv/bin/activate        # Windows: venv\Scripts\activate

# 2. Install dependencies
pip install -r requirements.txt

# 3. Set environment variables
echo "GEMINI_API_KEY=your_key_here" > .env

# 4. Start the server
python app.py
```

Open `http://localhost:5000`.

### Environment variables

| Variable | Default | Description |
|---|---|---|
| `GEMINI_API_KEY` | *(required)* | Google AI Studio API key |
| `GEMINI_MODEL` | `gemini-3.5-flash-lite` | Gemini model to use |
| `GEMINI_TIMEOUT` | `10` | Request timeout in seconds |
| `ALLOWED_ORIGIN` | `*` | CORS allowed origin for production deploys |

### Running tests

```bash
pytest tests/
```

---

## API

### `POST /ask`

Classify a student's health concern and return coverage information.

**Rate limit:** 20 requests per minute per IP.

**Request**
```json
{ "question": "I sprained my ankle playing soccer" }
```

**Response**
```json
{
  "language": "en",
  "red_flag": "none",
  "urgency": "this_week",
  "why": "A physiotherapist can assess and treat ankle sprains.",
  "needs": [
    {
      "category": "physio",
      "dental_type": null,
      "condition": null,
      "see_today": false,
      "practitioner": null,
      "why_one_line": "Physiotherapists usually treat ankle sprains like this.",
      "what_to_say": "I have the UBC AMS/GSS student health plan. Do you bill Pacific Blue Cross directly?",
      "coverage": { "per_visit": 40, "per_year": 400 }
    }
  ]
}
```

**Red flag values**

| Value | Meaning |
|---|---|
| `none` | No safety concern |
| `811` | Nurse line recommended — uncertain severity |
| `911` | Life-threatening emergency |
| `988` | Suicide or self-harm crisis |

### `GET /health`

Returns `{"ok": true}`. Used for uptime checks.

### `GET /plan-meta`

Returns plan metadata (administrator, last-pulled date) from the coverage JSON.

---

## Frontend

A single HTML file with inline CSS and vanilla JavaScript — no build step, no framework, no bundler.

- **Multilingual** — UI strings translate to the student's detected language; language picker in the top bar
- **Voice input** — microphone button triggers Web Speech API dictation
- **Safety screen** — full-screen overlay with large tap-to-call buttons for 911 / 988 / VictimLink / 811
- **Coverage page** — interactive breakdown of all plan benefits with a "used so far" tracker
- **Recent history** — previous questions stored in `localStorage` (nothing logged server-side)
- **Example chips** — pre-filled prompts for the three most common student scenarios
- **Dark mode** — respects `prefers-color-scheme`; WCAG 4.5:1 contrast in both themes
- **Accessible** — keyboard navigation, screen-reader labels, `prefers-reduced-motion` support
- **Mobile-first** — 2-column desktop layout kicks in at 900 px

---

## Safety design

Safety is enforced in two independent layers so an AI failure can never leave a student without emergency information.

**Layer 1 — keyword gate (`data/safety.py`)**
Runs synchronously before any network call. Matches 100+ phrases across five tiers in English, plus high-risk terms in Mandarin (Simplified and Traditional), Cantonese, Punjabi, Hindi, Korean, Spanish, Farsi, and French. If any phrase matches, Gemini is never called and the emergency screen appears immediately.

| Tier | Examples |
|---|---|
| `EMERGENCY_911` | chest pain, can't breathe, seizure, overdose |
| `CRISIS_988` | suicidal ideation, self-harm, want to die |
| `VIOLENCE_SAFETY` | assault, domestic violence, trafficking |
| `POISON_OD` | accidental ingestion, double dose, child swallowed |
| `URGENT_ER` | severe abdominal pain, high fever, broken bone |

**Layer 2 — Gemini red flag**
When no keyword matches, Gemini independently evaluates for `911`, `988`, and `811` flags. The server validates the full response shape and falls back to `red_flag: "811"` (call a nurse) if Gemini returns anything unusable or times out.

**No diagnosis:** The system prompt explicitly forbids Gemini from naming conditions, suggesting treatments, or guessing causes. It only identifies the *type* of professional the student should see.

**Prompt injection:** Student input is wrapped in `<user_message>` tags and the prompt instructs Gemini to treat that content as data, not instructions.

---

## License

For hackathon demonstration purposes. Coverage data is sourced from publicly available UBC AMS/GSS plan documentation and is provided for informational use only — verify current limits at [studentbenefits.ca](https://studentbenefits.ca).
