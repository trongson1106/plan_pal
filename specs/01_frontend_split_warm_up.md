# Spec 01: Split Frontend and Backend, Warm Up on Load

## Problem
Render's free tier sleeps after ~15 min idle and takes 30-60 s to wake. The whole app, including the static UI, is blocked behind that wake-up.

## Goal
The UI loads instantly from a CDN. Only `/ask` depends on the backend, and the backend is woken before the student finishes typing.

## Scope
1. Host `index.html`, `logo/`, and static assets on Netlify.
2. Point the frontend at the backend through a single configurable base URL.
3. Warm-up ping on page load.
4. "Waking up" state when `/ask` is slow.
5. CORS locked to the frontend origin.

## Requirements

### Hosting
- Deploy the repo (or a `/web` folder) as a static site. No build step.
- Add the custom/default domain to the backend's `ALLOWED_ORIGIN` env var (replace `*`).
- Keep `GET /` on the backend serving `index.html` as a fallback so the old URL keeps working.

### API base URL
- Add `const API_BASE = "https://<backend-host>";` near the top of the script in `index.html`.
- All `fetch` calls use `${API_BASE}/ask`, `/health`, `/plan-meta`.

### Warm-up
- On `DOMContentLoaded`, fire `fetch(API_BASE + "/health", { cache: "no-store" })`. Ignore errors silently.
- Do not block rendering on it.

### Slow-response state
- If `/ask` has not responded after 3 s, replace the spinner text with a localized message, e.g. "Waking up the server, this can take up to a minute the first time."
- Add the string to every language in the UI translation table.
- Client timeout for `/ask`: 70 s. On timeout, show a retry button, not a blank screen.
- Never show a loading message that delays the safety screen (see Spec 04).

## Acceptance criteria
- [ ] Page is interactive in under 1.5 s on a cold backend (Lighthouse, throttled 4G).
- [ ] After backend sleep, opening the page triggers `/health` (visible in network tab).
- [ ] A cold `/ask` shows the waking message after 3 s and succeeds without a manual reload.
- [ ] Requests from any other origin are rejected by CORS.
- [ ] Old backend URL still serves the app.

## Out of scope
Changing backend hosting (Spec 02), offline support (Spec 03).