# TripSync — Complete Project Handoff
**Last Updated:** May 9, 2026  
**Owner:** William — Just Me Media  
**Company:** Just Me Media  
**Developer Contact:** wcommu@gmail.com  

---

## What TripSync Is
AI-powered travel destination finder. User describes their dream trip in plain English. TripSync returns 3 detailed destination cards with real prices, flight estimates, visa info, and direct booking links to Booking.com, Agoda, and Expedia. Monetizes through affiliate commissions on every hotel and flight click. Features a dual-mode AI engine (Cloud via Groq / Local Private AI via Gemma 4).

**Live URL:** https://tripsync-ilao.onrender.com  
**Target Domain:** gettripsync.com (not yet purchased)  
**GitHub Repo:** https://github.com/Tripsync-justmeMedia/tripsync  

---

## Accounts & Logins

| Service | Login | Notes |
|---|---|---|
| GitHub | wcommu@gmail.com (Google SSO) | @Tripsync-justmeMedia org |
| Render.com | wcommu@gmail.com | Free tier, auto-deploys from GitHub |
| UptimeRobot | wcommu@gmail.com | Pings every 5 min to keep Render alive |
| Groq API | wcommu@gmail.com | Free tier, llama-3.3-70b-versatile |
| Google Play | wcommu@gmail.com | Org account active |
| Apple Developer | wcommu@gmail.com | Converting individual → org |

**Affiliate accounts (PENDING — not yet applied):**
- Booking.com → partners.booking.com
- Agoda → partners.agoda.com  
- Expedia → expediagroup.com/partners

---

## File Locations

### Project Structure
```
~/tripsync/
├── index.html        # Main Search/Inspiration UI
├── planner.html      # Detailed Day-by-Day Planner UI
├── docs/             # Technical Documentation & Handoffs
├── legacy/           # Backup & Test files
├── server.py         # Flask API
├── requirements.txt  # Python dependencies
└── .env              # API keys (NEVER commit this)
```
 ├── index.html        # Main Search/Inspiration UI
├── planner.html      # NEW: Detailed Day-by-Day Planner UI
├── privacy.html      # Legal: Privacy Policy
├── terms.html        # Legal: Terms of Service
├── manifest.json     # PWA: App metadata for Store readiness
├── sw.js             # PWA: Service worker for offline caching
├── icon.png          # PWA: App icon
├── server.py          # Flask API (Groq + SQLite)
  requirements.txt — clean Python dependencies
  .gitignore       — protects .env and .db files
  .env             — API keys (NEVER commit this)

~/symbiotic/       — Symbiotic Engine (separate app, separate repo)
  server.py        — SE + old combined TripSync code
  tripsync/        — old frontend (now superseded by ~/tripsync/)
```

### On Render (Production)
```
/opt/render/project/src/
  server.py
  index.html
  requirements.txt
DB: /tmp/tripsync.db  (ephemeral — resets on redeploy)
```

---

## Tech Stack

| Layer | Technology |
|---|---|
| Frontend | Single HTML file, no framework, no build step |
| Backend | Python Flask + Gunicorn |
| Primary AI | Groq API (llama-3.3-70b-versatile) |
| Local Private AI | Ollama local (gemma4) — privacy-first local mode for the Gemma 4 Challenge |
| Database | SQLite (click tracking + search logging) |
| Hosting | Render.com free tier |
| Uptime | UptimeRobot (5-min ping) |
| Version Control | GitHub — Tripsync-justmeMedia org |
| Fonts | Google Fonts: Playfair Display + DM Sans |
| PDF | jsPDF (CDN) |
| Image Save | html2canvas (CDN) |

---

## Environment Variables

Set in Render dashboard (never in code):

```
GROQ_API_KEY=your_groq_key        ← required, working
ANTHROPIC_API_KEY=                ← installed, needs credits
OPENAI_API_KEY=                   ← optional
GEMINI_API_KEY=                   ← get free at aistudio.google.com
DB_PATH=/tmp/tripsync.db          ← set automatically
```

Local `.env` file at `~/tripsync/.env`:
```
GROQ_API_KEY=your_key_here
```

---

## How The Stack Works

### API Flow
```
User types query
→ POST /api/tripsync
→ build_prompt() — constructs JSON-forcing prompt with departure city + currency
→ call_groq() — tries Groq 3x with retry
→ if fails → call_ollama() — tries local Ollama 2x (local only)
→ extract_json_safe() — 4-strategy JSON extraction
→ logs to SQLite search_log
→ returns { destinations: [...] } to frontend
→ frontend renders 3 cards
```

### Routes
```
GET  /              → serves index.html
POST /api/tripsync  → main search endpoint
POST /api/track-click → logs affiliate clicks
GET  /api/stats     → click + search totals
GET  /manifest.json → PWA manifest (needs adding)
GET  /sw.js         → service worker (needs adding)
```

---

## Destination Card Data Structure

```json
{
  "city": "Lisbon",
  "country": "Portugal",
  "description": "2-3 sentences why it matches",
  "match_score": "9.5/10",
  "best_season": "May to October",
  "budget_per_day": "$80-$130 per person",
  "flight_estimate": "$600-$900 return",
  "flight_duration": "7-9 hours",
  "visa": "Not required for most nationalities",
  "highlights": ["Historic Trams", "Pastéis de Nata", "Alfama District", "Sintra Day Trip"]
}
```

---

## Frontend Features (Current)

- ✅ **New: Interactive Planner (`planner.html`)**
- ✅ Day-by-day itineraries with budgets & meals
- ✅ Hotel suggestions with direct booking
- ✅ **New: Viator integration for activities/tours**
- ✅ **New: Manual Activity Editing (Add/Remove items)**
- ✅ **New: AI Refinement Tool (Rebuild plan with instructions)**
- ✅ **New: Dual Flight Booking (Google Flights + Skyscanner)**
- ✅ **New: Viral Sharing (WhatsApp, X, FB) for all itineraries**
- ✅ PDF download (jsPDF) with Just Me Media branding
- ✅ Save card as image (html2canvas)
- ✅ PWA install banner (Add to Home Screen)
- ✅ Left sidebar: Named trip projects + Interactive History (Local-First)
- ✅ **New: Legacy Data Sanitizer (Auto-repairs old history)**
- ✅ Just Me Media footer branding
- ✅ Click tracking → SQLite
- ✅ **NEW: 3-Tier AI Architecture (Cloud, Gemma, Local)**
- ✅ **NEW: Zero-Downtime Silent Fallback (Gemma → Groq)**
- ✅ **NEW: Smart AI Parser (Auto-repairing malformed JSON)**

---

## Affiliate Tracking & IDs
We have a dedicated tracker for all monetization partners:
*Internal Affiliate Tracking Document*

**Current Status:**
- Booking.com: ✅ **LIVE** (aid: 2884913)
- Agoda/Expedia: ⏳ Applied (Awin)
- Viator: ⏳ Applied (Partnerize)
- Skyscanner: ❌ Re-apply after traffic grows (use WayAway as alternative)

---

## What's Done ✅ (Updated May 7)

- **Interactive Planner**: Users can now adjust activities and ask AI for refinements.
- **Full Booking Funnel**: Flights, Hotels, and Tours all integrated into one view.
- **PWA v2**: Updated service worker to force updates and improve performance.
- **Stability**: Replaced all `confirm()` popups with stable custom modals.
- **Navigation**: Prominent "Planner" link added to the main header.
- **3-Tier AI Integration (May 10)**:
    - **Cloud AI (Groq)**: High-speed, primary engine.
    - **Gemma 4 Expert (Google Gemini API)**: High-intelligence tier using `gemma-4-26b-a4b-it`. (Avg. load time: ~30 seconds)
    - **Local AI (Ollama)**: Integrated for on-device inference (`gemma4`).
    - **Zero-Downtime Reliability**: Implemented a silent fallback in `server.py`. If Gemma takes longer than 25s (nearing Render's 30s limit), it instantly and silently hands off to Groq to ensure a seamless experience. This guarantees a response in ~30s even in the worst-case scenario.
    - **Smart JSON Parsing**: Robust parser that strips AI conversation, fixes trailing commas, and handles key renames automatically.

---

## What's Next 🔜

**Immediate (Public Beta Phase):**
- [ ] **June 4, 2026: Product Hunt Launch** (Tracked in [ROADMAP.md](file:///Users/williamcommu/tripsync/docs/ROADMAP.md))
- [ ] Share with "Friends & Family" and gather first usage stats.
- [ ] Monitor the "Stats" modal to see which travel partners get the most clicks.
- [ ] Sign up for **WayAway** (Travelpayouts) as a high-approval flight alternative.

**Short term:**
- [ ] Buy **gettripsync.com** domain and connect to Render.
- [ ] Update placeholder IDs for Agoda/Expedia once approved.
- [ ] First TikTok/Reel screen recording showing the "Interactive Planner" magic.
- [ ] **SEO Landing Page**: Create city-specific landing pages for organic traffic.
- [ ] **Email Capture**: "Save this plan to email" to build a mailing list.

---

## Security Notes

- Affiliate IDs live in frontend JS — acceptable for MVP, move to backend before scaling
- Rate limiting not yet implemented — add flask-limiter when traffic grows
- .env file is gitignored — never commit it
- SQLite db is ephemeral on Render free tier — data resets on redeploy (acceptable for now)
- For production scale: migrate to PostgreSQL (Render has free tier)

---

## App Store Submission (Apple & Google)

TripSync is now a fully qualified **PWA (Progressive Web App)**. To submit it to the stores:

1.  **Preparation**: Ensure you have an icon (done) and manifest (done).
2.  **Tooling**: Use [PWABuilder.com](https://www.pwabuilder.com/).
3.  **Process**:
    *   Enter `https://tripsync-ilao.onrender.com` (or your custom domain).
    *   Download the "Android Wrapper" (`.apk` / `.aab`).
    *   Download the "iOS Wrapper" (requires a Mac and Xcode).
4.  **Hosting**: **CRITICAL** — Upgrade Render to the **Starter Plan ($7/mo)**. On the free plan, the app will "sleep," and Apple will likely reject it for taking too long to load.

---

## William's Setup

- MacBook Pro M1
- Muskoka Ontario cottage + home office
- Fiber internet
- Vibe coder — builds with AI + terminal, not manual coding
- Google Play org account active
- Apple Developer converting individual → org
- External hard drive incoming for local model storage
- Works nights, moves fast

---

## Starting a New Chat With an AI

Paste this at the start of any new conversation:

> "I'm William from Just Me Media. I'm building TripSync — a live AI travel planner at https://tripsync-ilao.onrender.com. GitHub: https://github.com/Tripsync-justmeMedia/tripsync. Files are at ~/tripsync/ on my Mac. Built with Flask + Groq AI + plain HTML. Deployed on Render, auto-deploys from GitHub. Here is the full handoff doc: [paste this file]"

---

*TripSync by Just Me Media — Built with Claude (Anthropic)*
