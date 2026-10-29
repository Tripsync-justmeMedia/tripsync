# TripSync — Agent Session Briefing

## Project Identity

| Field | Value |
|---|---|
| **Product Name** | TripSync |
| **Company** | Just Me Media |
| **Type** | AI-powered travel planner (web app + PWA) |
| **Stack** | Python / Flask (backend) + HTML/CSS/JS (frontend) |
| **Live URL** | [https://tripsync.ca](https://tripsync.ca) |
| **Status** | Active — public beta |
| **AI Providers** | Groq (fast), Google Gemini (reasoning), Ollama (local/private) |

## What This App Does

TripSync generates detailed travel itineraries with pricing, booking links, and day-by-day plans. Uses a 3-tier AI strategy: Cloud (Groq), Expert Reasoning (Gemma 4), and Local (Ollama). Features currency arbitrage, flight duration estimation, and real-time booking partner links.

## Isolation Notice

> [!NOTE]
> TripSync is **completely independent** of LexSort / VERA / ProMailer / Events Arena.
> `docs/PRIVATE_HANDOFF.md` contains a "LexSort Accounts" section — this is just the founder's personal
> credential notes for his own infrastructure. It does NOT mean TripSync is part of LexSort.
> Do not import LexSort or VERA patterns into this project.

## Key Files
- `main.py` — Flask app entry point
- `server.py` — API routes
- `static/` — Frontend HTML/CSS/JS
- `docs/PRIVATE_HANDOFF.md` — Full accounts + infrastructure reference (read for credentials)
- `README.md` — Feature overview and tech stack

## Outbound / Affiliate Link Rules (learned the hard way)
- **Never hand-write partner URLs.** Use the helpers next to the `AFFILIATE` block in `index.html`
  and `planner.html`: `citySlug()`, `skyscannerUrl()`, `tiqetsUrl()`, `viatorUrl()` (and `jsStr()`
  for anything interpolated into an inline `onclick`). Every one of these was added because a
  hand-written URL 404'd, 400'd, dropped its tracking param, or broke on an apostrophe (`Xi'an`).
- Verified URL shapes (re-check after any change, see `docs/AFFILIATE_CHECKLIST.md`):
  Booking `/searchresults.html?ss=&aid=&checkin=&checkout=&group_adults=` ·
  Tiqets `/en/search?q=` (NO trailing slash) · Skyscanner
  `/transport/flights/<from-slug>/<to-slug>/<YYMMDD>/<YYMMDD>/?adults=N` · Viator
  `/searchResults/all?text=&pid=&mcid=`.
- `/api/flight-prices` needs `TRAVELPAYOUTS_TOKEN`; without it live fares silently disappear.
  See `.env.example`.
- Ekta insurance (`p=5869`, campaign 225) was removed — the marker is not subscribed, the
  redirector returns 400. Do not re-add without a subscribed campaign.
- **Multi-city deep links are built server-side** by `build_multi_city_url()` in `server.py`,
  using Cheapflights' verified pattern `/flight-search/LEG/DATE/LEG/DATE/.../LEG` (IATA codes,
  `YYYY-MM-DD`). Never assemble that path in the browser — the frontend only renders
  `data.multi_city_url`. A malformed leg/date alternation produces a broken search page.

## Dev Commands
```bash
# Install deps
pip install -r requirements.txt

# Run locally
python main.py   # or python server.py

# Deploy (Netlify for frontend, separate backend host)
# See docs/PRIVATE_HANDOFF.md for full deployment setup
```

## ⚠️ CRITICAL: Test Locally Before Deploying (learned the hard way)

**ALWAYS run the site locally and test all functionality before pushing to GitHub / deploying to Netlify.**

The site is served locally via Python HTTP server on port 8080:
```bash
cd /Users/williamcommu/Desktop/JUST_ME_MEDIA_VAULT/JustMeMedia/01_ACTIVE/TripSync
python3 -m http.server 8080
# Then open http://localhost:8080/index.html in a browser
```

**Never push to GitHub without:**
1. ✅ Running the local server (`python3 -m http.server 8080`)
2. ✅ Opening `http://localhost:8080/index.html` in a browser
3. ✅ Clicking every button (especially "Curate My Ideal Journey") to verify no JS errors
4. ✅ Verifying the hero background image loads correctly
5. ✅ Verifying all JavaScript functions work without null reference errors

**Common failures caught this way:**
- Removed DOM elements (`#welcomeState`) still referenced in JS → crashes `searchTrip()`
- Background image files missing or wrong path → gray placeholder instead of image
- CSS changes breaking layout → overlapping elements, dead space gaps

Deployments to Netlify auto-trigger from GitHub pushes, so broken code goes live immediately. Test first, push second.
```

## Accounts
| Service | Account | Notes |
|---|---|---|
| Groq API | In `.env` | Fast cloud inference |
| Google Gemini | In `.env` | Expert reasoning tier |
| Booking.com Affiliate | ID: 2884913 | Active |
| Netlify | William@lexsort.com | tripsync.ca frontend |
