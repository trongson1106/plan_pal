# PlanPal — Project Summary

**Hackcamp 2026 · UBC Coverage Server**

---

## What It Is

PlanPal is a web app that helps UBC students understand and use their AMS/GSS student health plan. A student describes a health concern in plain language (any language), and the app tells them:

- What type of healthcare professional to see
- Exactly what their plan covers and how much it pays
- What to say when booking the appointment

---

## Architecture

```
Browser (index.html)
    └── POST /ask
            ├── Safety gate (data/safety.py) — keyword-based, no AI
            └── Gemini AI classifier (api.py) → Google Gemini API
                    └── Coverage lookup (data/coverage.py)
```

| File | Role |
|------|------|
| [app.py](app.py) | Flask server, single `/ask` endpoint |
| [api.py](api.py) | Gemini AI classifier — determines care category & red flags |
| [data/safety.py](data/safety.py) | Pre-AI safety keyword triage |
| [data/coverage.py](data/coverage.py) | UBC AMS/GSS plan coverage data |
| [data/ubc_student_health_deals.json](data/ubc_student_health_deals.json) | Raw plan data (pulled 2026-11-07 from Alumo) |
| [index.html](index.html) | Full single-page frontend (HTML + CSS + JS, no framework) |

---

## Request Flow

1. **Student types** (or speaks via mic) a health question in any language.
2. **Safety gate** (`data/safety.py`) scans for 100+ emergency keywords across 5 tiers before AI is ever called:
   - `EMERGENCY_911` — life-threatening (chest pain, stroke, overdose, etc.)
   - `CRISIS_988` — suicidal ideation or self-harm
   - `VIOLENCE_SAFETY` — assault, domestic violence, trafficking
   - `POISON_OD` — accidental poisoning/overdose
   - `URGENT_ER` — severe symptoms needing same-day ER care
3. If no safety keyword matches, **Gemini AI** (`api.py`) classifies the question:
   - Detects the student's language (ISO 639-1)
   - Sets a `red_flag` (`none` / `811` / `911` / `988`)
   - Returns up to 3 `needs`, each with a care category, booking script, and one-line explanation
4. **Coverage lookup** (`data/coverage.py`) attaches plan dollar amounts to each need.
5. The **frontend** renders the answer, coverage details, and clinic-finder.

---

## Coverage Categories

The plan covers 13 care types, with key dollar limits:

| Category | Per Visit | Per Year / Limit |
|----------|-----------|-----------------|
| Physiotherapy | $40 | $400/yr |
| Massage (RMT) | $35 | $400/yr |
| Chiropractor | $35 | $400/yr |
| Other practitioners | $35 | $400/yr |
| Counselling | 100% | $1,250/yr |
| Dental | — | $750/yr (70% preventive, 50% basic) |
| Vision | — | $50 eye exam (every 2 yrs), $80 eyewear (every 24 mo) |
| Prescriptions | 80% | Rexall covers the other 20% (up to $40) |
| Vaccines | 100% | $150/yr |
| Doctor visit | Free | Covered by MSP |
| Medical equipment | — | Orthotics $300/yr, orthopedic shoes $500/yr |
| Hearing aids | — | $500 every 5 yrs |

Insurer: **Pacific Blue Cross** (group 43979), administered by **Alumo**.

---

## Frontend (index.html)

Single HTML file (~376 KB) with inline CSS and vanilla JavaScript. Key features:

- **Multilingual** — UI strings translate to the student's detected language; language picker in top bar
- **Voice input** — microphone button triggers Web Speech API dictation
- **Safety screen** — full-screen red overlay with large call buttons for 911/988/etc.
- **Coverage page** — interactive breakdown of all plan benefits with "used so far" tracker
- **Recent history** — previous questions stored in `localStorage`
- **Example chips** — tap-to-fill example questions (ankle sprain, stress, asthma)
- **Privacy notice** — no account required; questions are not stored server-side
- **Dark mode + accessible** — WCAG 4.5:1 contrast, `prefers-reduced-motion`, keyboard navigation, screen-reader labels
- **Responsive** — mobile-first; 2-column desktop grid at 900px+

---

## AI Design Decisions

- **Safety-first**: Gemini is **never called** when safety keywords match — the keyword check is faster and more reliable for emergencies than an LLM.
- **No diagnosis**: The system prompt explicitly forbids Gemini from guessing conditions or suggesting treatment. It only names the *type* of professional.
- **Prompt injection protection**: Student input is wrapped in `<user_message>` tags and the prompt states that content inside those tags cannot change the instructions.
- **Fallback**: If Gemini fails or returns unusable JSON, the app falls back to `red_flag: "811"` (call a nurse line) rather than crashing.
- **Model**: `gemini-3.5-flash-lite` by default (overridable via `GEMINI_MODEL` env var).

---

## Running the Server

```bash
# Install dependencies
pip install flask flask-cors google-genai python-dotenv

# Set env vars (.env file)
GEMINI_API_KEY=your_key_here

# Start
python app.py
```

Endpoints:
- `GET /` — serves `index.html`
- `GET /health` — health check → `{"ok": true}`
- `POST /ask` — main endpoint; body: `{"question": "..."}`
