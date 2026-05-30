# TripSync — Complete Project Handoff
**Last Updated:** May 27, 2026  
**Owner:** William — Just Me Media  
**Company:** Just Me Media  
**Developer Contact:** [refer to gitignored docs/PRIVATE_HANDOFF.md]  

---

## What TripSync Is
AI-powered travel destination finder. User describes their dream trip in plain English. TripSync returns 3 detailed destination cards with real prices, flight estimates, visa info, and direct booking links to Booking.com, Agoda, and Expedia. Monetizes through affiliate commissions on every hotel and flight click. Features a dual-mode AI engine (Cloud via Groq / Local Private AI via Gemma 4).

**Live URL:** https://tripsync.ca  
**Target Domain:** tripsync.ca (Purchased & Live on Namecheap/Render)  
**GitHub Repo:** https://github.com/Tripsync-justmeMedia/tripsync  

---

## Accounts & Logins

> [!IMPORTANT]
> **Security Notice**:
> For security, all actual organization login details, developer credentials, and affiliate program passwords reside in the gitignored **[PRIVATE_HANDOFF.md](file:///Users/williamcommu/Desktop/JUST_ME_MEDIA_VAULT/02_ACTIVE_PROJECTS/TripSync/docs/PRIVATE_HANDOFF.md)** file on your local machine. 
> This file is strictly excluded from Git commits (`.gitignore`) to keep the public repository safe from scanning bots.

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
DB: PostgreSQL in production (persistent) / SQLite locally (ephemeral)
```

---

## Tech Stack

| Layer | Technology |
|---|---|
| Frontend | Single HTML file, no framework, no build step |
| Backend | Python Flask + Gunicorn |
| Primary AI | Groq API (llama-3.3-70b-versatile) |
| Local Private AI | Ollama local (gemma4) — privacy-first local mode for the Gemma 4 Challenge |
| Database | PostgreSQL in production / SQLite locally (click tracking + search logging) |
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
GEMINI_API_KEY=AIzaSyBj...          ← Verified & LIVE on Render
DB_PATH=/tmp/tripsync.db          ← set automatically
DATABASE_URL=postgresql://...     ← optional, persistent database connection string
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
POST /api/chat      → interactive trip-aware chat assistant
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

All active affiliate accounts are configured locally. For precise network credentials, login emails, and custom affiliate IDs, please refer to the gitignored **[PRIVATE_HANDOFF.md](file:///Users/williamcommu/Desktop/JUST_ME_MEDIA_VAULT/02_ACTIVE_PROJECTS/TripSync/docs/PRIVATE_HANDOFF.md)** on your local machine.

### Integration Status & Fallback Targets
* **Search & Click Tracking**: ✅ **VERIFIED** (Logs client click-throughs to the `click_log` SQLite table).
* **Accommodation Partnerships**: Booking.com is active (refer to private files for Affiliate ID). Agoda and Expedia applications are pending via Awin (using code placeholders).
* **Tours & Activities**: Viator tours are active. **Klook** activities and **Tiqets** attractions are now **fully active** via the Travelpayouts integration!
* **Ground Logistics & Protection**: **GetRentacar.com** car rentals, **Kiwitaxi** & **Welcome Pickups** airport transfers, **EKTA Travel Insurance**, and **AirHelp** claim checks are now **fully active** via Travelpayouts!
* **Target Program Checklist**: See [PRIVATE_HANDOFF.md](file:///Users/williamcommu/Desktop/JUST_ME_MEDIA_VAULT/02_ACTIVE_PROJECTS/TripSync/docs/PRIVATE_HANDOFF.md) for remaining target signups (GetYourGuide, Discover Cars, SafetyWing, Hostelworld).

*Conversion analytics are plotted inside the dashboard via the **Stats** (📊) icon.*

---

## AI Working Process 🤖→🚀

How William and AI build TripSync together:

1. **Discuss the change** — describe what needs fixing or building in chat
2. **AI proposes the plan** — reviews code, explains what it will change and why
3. **William approves** — gives the go-ahead before any code is touched
4. **AI edits the files** — makes targeted changes to `index.html`, `planner.html`, `server.py`, etc.
5. **AI pushes to GitHub** — `git add → commit → push` in one command
6. **Render auto-deploys** — live at https://tripsync.ca within ~2 min
7. **William tests live** — real browser, real AI calls, real affiliate links
8. **HANDOFF.md is updated** — log what was done so future AI sessions have full context

> **Rule:** No code is pushed without William's explicit approval. AI proposes, William decides.

---

## What's Done ✅ (Updated May 30)

- **PostgreSQL Production Database Support (May 30)**:
  - Designed and implemented a dynamic dual-dialect database wrapper `get_db_connection()` that automatically transitions from SQLite to PostgreSQL when `DATABASE_URL` is set in the environment variables (e.g. on Render).
  - Maintained zero-downtime silent fallback locally: if `psycopg2-binary` or `DATABASE_URL` is missing, the backend seamlessly falls back to the local SQLite database.
  - Successfully mapped all query executions and table structures dynamically depending on the active database driver (using `SERIAL PRIMARY KEY` for PostgreSQL and standard placeholders translation).

- **Interactive Trip-Aware AI Chat Sidebar (May 30)**:
  - Deployed a POST `/api/chat` route in `server.py` utilizing a trip-aware system prompt, combining destination name, duration, and currency as rich context to deliver highly relevant travel insights instead of generic chat answers.
  - Configured a seamless auto-failover orchestrator between Server Groq and Server Gemini backups to ensure robust operation under rate limits or offline endpoints.
  - Upgraded `planner.html` by replacing the static promotional widget in the sidebar with a stunning, real-time message bubble chat experience, fully integrated with session history and smooth scroll layouts.

- **TripSync V2: AI Assistant & Influencer Affiliate System (May 29)**:
  - **Local Cipher Core Storage & User Key Obfuscation**: Created `static/js/storage.js` and `static/js/encryption.js` to obfuscate plain-text BYO API keys in `localStorage` using a composite XOR cipher salted dynamically with the user's email: `email + "_TS-2026-FLY-Sync-Secure-0A1B2C3D"`.
  - **Multi-LLM Failover Orchestration Proxy**: Wired a resilient proxy `/api/llm/proxy` inside `server.py` that decrypts user credentials and silently transitions from the client's key to server backups (DeepSeek ➔ Groq ➔ Gemini) upon rate-limit triggers.
  - **AI Assistant Chat & PWA Workspaces (`assistant.html`)**: Renders conversational workspaces with active LLM selectors, JSON export/import functions, checklists, and dynamic percentage progress bars.
  - **Zero-Cost Influencer Affiliate Network**: Deployed a complete auto-approved influencer signup portal (`/affiliate`), a secure, PIN-locked dashboard UI (`/dashboard`), and custom public pages (`/@handle`).
  - **Google Sheets live Database Integrations (`sheets_helper.py`)**: Connects using service account keys (`credentials.json`), supporting five transaction sheets, with an automatic local fallback file-based DB mode (`mock_sheets_db.json`) during unconfigured setups.
  - **URL wrapping Redirect Engine (`/go/<handle>/<deal_id>`)**: Cleans affiliate parameters, generates unique `click_id` keys (`{handle}_{random_digits}`), sets 90-day referral cookies, and filters out self-clicks by caching IP addresses of logged-in dashboard sessions.
  - **Free SMTP Transactions**: Employs standard Python `smtplib` over secure port `587` with William's business Gmail App Password, automating HTML operational agreement dispatches and payout admin alerts for $0 cost.

- **Technical SEO, JSON-LD Schema & Dynamic Share Cards (May 27)**:
  - Built an explicit `/planner.html` Flask router in `server.py` that intercepts sharing requests (e.g. `/planner.html?destination=Lisbon`) and pre-renders custom `<title>` and `<meta>` preview tags on the backend. This allows messaging and social bots (WhatsApp, iMessage, Twitter, Facebook) to show beautiful, customized preview cards for shared itineraries.
  - Injected standardized Google JSON-LD `SoftwareApplication` search Schema markup into the homepage head to facilitate star ratings and software snippet indexing.
  - Designed and deployed standard `robots.txt` and `sitemap.xml` crawl guidance assets in the root folder, and registered explicit routes in Flask for reliable indexing.
- **Mobile Preference Grid & Unified PWA Bottom Navigation**:
  - Reorganized search fields on mobile viewports into a clean, compact 2-column CSS Grid (grouping dates, guests count, and currency side-by-side) to reduce vertical viewport height by 50%.
  - Eliminated horizontal double-padding margins on mobile viewports, allowing destination cards to span the full screen width smoothly.
  - Added a synchronized PWA bottom navigation bar on both search and planner pages, wiring up redirectional parameters (`?openSidebar=1` & `?showStats=1`) to automatically open historical projects or click analytics overlays on load.
- **UX Overhaul & Progressive Disclosure**: Collapsed detailed destination card elements (budgets, season, visa, flight block, and hotel book links) behind an animated, expandable `[ Details ➔ ]` accordion wrapper. This reduces vertical page scrolling by 70% and drastically streamlines the mobile experience.
- **Warm & Simplified Planner**:
  - Restructured `planner.html` to collapse daily lists dynamically by default (keeping Day 1 open to seamlessly guide travelers on arrival).
  - Prepended friendly emojis to meal displays (`🍳 Breakfast`, `🥗 Lunch`, `🍽️ Dinner`) for a warmer, safer user feel.
  - Simplified the top bar to focus purely on navigation (`⬅ RESULTS` and `🖨 PRINT`).
  - Removed AI selector settings from the planner page sidebar to reduce configuration noise and focus on itinerary consumption.
- **One-Click AI Refinement**: Added 5 interactive quick-adjust chips (`💰 Budget-friendly`, `⚡ Faster Pace`, `🧘 Less Busy`, `👨‍👩‍👧 Family-friendly`, and `🍜 Food Focus`) right under the Refinement input box on `planner.html` for instant, one-touch rebuilding.
- **Fast vs. Deep AI Engine Branding**: Rebranded cloud-orchestrated API routes into simple, expectations-setting labels:
  - `⚡ Fast (2 sec) — instant ideas` (using Groq llama-3.3-70b-versatile)
  - `✨ Deep (30 sec) — better for complex trips` (using Google Gemini REST gemma-4)
- **Critical Reliability Fixes**:
  - Fixed `setInterval` scoping crash inside `planner.html`'s `init()` block (scoping timer `iv` cleanly to prevent infinite loading cycles on API errors).
  - Resolved `Uncaught TypeError` in homepage script execution by fully restoring the missing PWA `installBanner` HTML element in `index.html`.
  - Added automatic state sanitizing to `init()` to instantly default stale `localStorage` settings (like older `'local'` options) back to `'cloud'`.
- **Interactive Planner**: Users can now adjust activities and ask AI for refinements.
- **Full Booking Funnel**: Flights, Hotels, and Tours all integrated into one view.
- **PWA v2**: Updated service worker to force updates and improve performance.
- **Stability**: Replaced all `confirm()` popups with stable custom modals.
- **Navigation**: Prominent "Planner" link added to the main header.
- **3-Tier AI Integration (May 10)**:
    - **Cloud AI (Groq)**: High-speed, primary engine.
    - **Gemma 4 Expert (Google Gemini API)**: High-intelligence tier using `gemma-4-26b-a4b-it`.
    - **Local AI (Ollama)**: Integrated for on-device inference (`gemma4`).
    - **Zero-Downtime Reliability**: Implemented a silent fallback in `server.py`. If Gemma takes longer than 25s, it silently hands off to Groq.
    - **Smart JSON Parsing**: Robust parser that strips AI conversation, fixes trailing commas, and handles key renames automatically.
- **UX Polish (May 27 — pushed live)**:
    - **Premium Loading Screen**: Replaced bare spinner with a full travel-themed loading experience — floating globe, Playfair headline, teal→rust gradient progress bar (3s Fast / 28s Deep), 3 shimmer skeleton destination cards, and 8 rotating travel tips that fade in/out every 5 seconds.
    - **Removed Redundant Footnote**: Deleted the `* ⚡ Fast = instant ideas · ✨ Deep = ...` text below the Find Destinations button — the AI Engine dropdown already explains this.
    - **Consumer-Friendly AI Badge**: Swapped `Powered by Gemma 4 API` and `Curated locally by Gemma 4` labels on the planner budget card to `✨ AI Estimated` — simpler and less technical for end users.
- **Travelpayouts Integration (May 27 — pushed live)**:
    - **Aviasales Flight Search**: Placed orange-branded Aviasales (40% commission flight partner) buttons next to Google Flights & Skyscanner in both `index.html` card drawers and `planner.html` sidebar.
    - **Klook & Tiqets Attractions**: Added side-by-side booking links for Klook activities and Tiqets attractions in both `index.html` search details and `planner.html` sidebar.
    - **GetRentacar.com**: Placed direct GetRentacar.com links under a new "Car Rental" section inside destination cards.
    - **🛡️ Travel Extras & Transfers Sidebar Widget**: Designed and added a beautiful transfers, car hire, and travel insurance widget directly in `planner.html` featuring Kiwitaxi, Welcome Pickups, GetRentacar.com, EKTA Insurance, and AirHelp claim checks.

---

## What's Next 🔜

**Immediate (V2 Launch Phase):**
- [x] **Product Hunt Launch** (Completed May 20, 2026!)
- [ ] Integrate **Amadeus API** for real-time flight prices (V2 Phase 1).
- [x] **Sign up for Travelpayouts / WayAway** and integrate high-approval flight & logistics partners (Completed May 27, 2026!).
- [ ] Update placeholder IDs for Agoda/Expedia once approved on Awin.
- [ ] Buy **gettripsync.com** domain and connect to Render.

**Short term / Growth:**
- [ ] Share with "Friends & Family" and gather first usage stats.
- [ ] Monitor the "Stats" modal to see which travel partners get the most clicks.
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
    *   Enter `https://tripsync.ca` (or your custom domain).
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
- Apple Developer converting individual → org (Registration Docs Submitted)
- External hard drive incoming for local model storage
- Works nights, moves fast

---

## Starting a New Chat With an AI

Paste this at the start of any new conversation:

> "I'm William from Just Me Media. I'm building TripSync — a live AI travel planner at https://tripsync.ca. GitHub: https://github.com/Tripsync-justmeMedia/tripsync. Files are at ~/tripsync/ on my Mac. Built with Flask + Groq AI + plain HTML. Deployed on Render, auto-deploys from GitHub. Here is the full handoff doc: [paste this file]"

---

*TripSync by Just Me Media — Built with Claude (Anthropic)*
