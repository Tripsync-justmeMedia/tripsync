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

## Dev Commands
```bash
# Install deps
pip install -r requirements.txt

# Run locally
python main.py   # or python server.py

# Deploy (Netlify for frontend, separate backend host)
# See docs/PRIVATE_HANDOFF.md for full deployment setup
```

## Accounts
| Service | Account | Notes |
|---|---|---|
| Groq API | In `.env` | Fast cloud inference |
| Google Gemini | In `.env` | Expert reasoning tier |
| Booking.com Affiliate | ID: 2884913 | Active |
| Netlify | William@lexsort.com | tripsync.ca frontend |
