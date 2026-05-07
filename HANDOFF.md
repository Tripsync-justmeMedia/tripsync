# TripSync — Complete Project Handoff
**Last Updated:** May 7, 2026  
**Owner:** William — Just Me Media  
**Company:** Just Me Media  
**Developer Contact:** wcommu@gmail.com  

---

## What TripSync Is
AI-powered travel destination finder. User describes their dream trip in plain English. TripSync returns 3 detailed destination cards with real prices, flight estimates, visa info, and direct booking links to Booking.com, Agoda, and Expedia. Monetizes through affiliate commissions on every hotel and flight click.

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

### On William's Mac (Local)
```
~/tripsync/
  server.py        — standalone Flask backend (TripSync only)
  index.html       — full frontend
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
| Fallback AI | Ollama local (llama3.1:8b) — local only, not on Render |
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

- ✅ Departure city field (remembers between sessions)
- ✅ Currency selector (12 currencies)
- ✅ Date pickers + guest count + budget field
- ✅ 3 destination cards with Premium Glassmorphism UI
- ✅ Dynamic Vibe Tags (#Beach, #History, etc.)
- ✅ Trip Type selector (Round Trip, One Way, Multi-city)
- ✅ Booking links: Booking.com, Agoda, Expedia
- ✅ Flight search: Google Flights (Robust deep-linking)
- ✅ PDF download (jsPDF) with Just Me Media branding
- ✅ Save card as image (html2canvas)
- ✅ Share buttons: WhatsApp, X/Twitter, Facebook, Email, Copy Link
- ✅ Native share API (mobile)
- ✅ PWA install banner (Add to Home Screen)
- ✅ Service worker registration (needs sw.js + manifest.json added)
- ✅ Left sidebar: Named trip projects + Interactive History (Local-First)
- ✅ Clickable Recent Searches history
- ✅ Auto-reset fields for new projects
- ✅ Example chips (no location hardcoding)
- ✅ Mobile responsive
- ✅ Just Me Media footer branding
- ✅ Click tracking → SQLite

---

## Affiliate Links — READY, NEED IDs

Current placeholders in index.html:
```javascript
const AFFILIATE = {
  booking_aid: 'YOUR_BOOKING_AID',
  agoda_cid: 'YOUR_AGODA_CID',
  expedia_affcid: 'YOUR_EXPEDIA_AFFCID'
};
```

**To insert IDs once approved — run this on Mac:**
```bash
cd ~/tripsync
sed -i '' 's/YOUR_BOOKING_AID/real_id_here/' index.html
sed -i '' 's/YOUR_AGODA_CID/real_id_here/' index.html
sed -i '' 's/YOUR_EXPEDIA_AFFCID/real_id_here/' index.html
git add index.html
git commit -m "Add affiliate IDs"
git push
```

**To register:**
- Booking.com → partners.booking.com
- Agoda → partners.agoda.com
- Expedia → expediagroup.com/partners

---

## Deployment

### Auto-Deploy (normal workflow)
```bash
cd ~/tripsync
# make changes to index.html or server.py
git add .
git commit -m "describe what changed"
git push
# Render auto-deploys within ~2 minutes
```

### Render Settings
- **Build Command:** `pip install -r requirements.txt`
- **Start Command:** `gunicorn server:app`
- **Instance:** Free tier
- **Region:** Virginia US East
- **Auto-deploy:** On (triggers on every GitHub push)

### If Render Goes Down
```bash
# Check logs at render.com dashboard
# Or redeploy manually: Render → Manual Deploy → Deploy latest commit
```

---

## Local Development

### Start TripSync locally
```bash
cd ~/tripsync
python3 server.py
# Visit http://127.0.0.1:5001
```

### Start Symbiotic Engine locally
```bash
cd ~/symbiotic
python3 server.py
# Or double-click SymbioticEngine.command on Desktop
# Visit http://127.0.0.1:5000
```

### If anything breaks locally
```bash
pkill -f server.py
cd ~/tripsync && python3 server.py &
curl http://127.0.0.1:5001
```

---

## PWA — Needs Completing

Two files need to be added to `~/tripsync/` for full PWA support:

### manifest.json
```json
{
  "name": "TripSync",
  "short_name": "TripSync",
  "description": "AI Travel Planner by Just Me Media",
  "start_url": "/",
  "display": "standalone",
  "background_color": "#0f0f0f",
  "theme_color": "#0f0f0f",
  "icons": [
    { "src": "/icon-192.png", "sizes": "192x192", "type": "image/png" },
    { "src": "/icon-512.png", "sizes": "512x512", "type": "image/png" }
  ]
}
```

### sw.js (service worker)
```javascript
self.addEventListener('fetch', e => {
  e.respondWith(fetch(e.request).catch(() => caches.match(e.request)));
});
```

### Flask routes to add in server.py
```python
@app.route('/manifest.json')
def manifest():
    return send_from_directory('.', 'manifest.json')

@app.route('/sw.js')
def sw():
    return send_from_directory('.', 'sw.js')
```

---

## What's Done ✅

- Standalone TripSync app separated from Symbiotic Engine
- Clean GitHub repo at Tripsync-justmeMedia/tripsync
- Deployed on Render.com with auto-deploy
- UptimeRobot keeping it alive 24/7
- Global departure city field (no Toronto hardcoding)
- Currency selector (12 currencies)
- PDF download with Just Me Media branding
- Save card as image
- Social sharing: WhatsApp, X, Facebook, Email, Copy Link
- PWA install banner (Add to Home Screen)
- Just Me Media footer
- Affiliate link slots ready

---

## What's Next 🔜

**Immediate:**
- [ ] Add manifest.json + sw.js + icons for full PWA
- [ ] Apply for Booking.com, Agoda, Expedia affiliate accounts
- [ ] Add GROQ_API_KEY to Render environment variables if not done

**Short term:**
- [ ] Buy gettripsync.com domain (~$12/yr)
- [ ] Connect domain to Render
- [ ] Post on Reddit (r/travel, r/solotravel, r/SideProject)
- [ ] First TikTok/Reel screen recording

**Medium term:**
- [ ] Add Gemini API as third brain (free at aistudio.google.com)
- [ ] Add Amadeus flight API for real prices (free tier)
- [ ] SEO landing page / blog content
- [ ] Email capture ("save your results")
- [ ] Admin dashboard for click stats

**Longer term:**
- [ ] Google Play Store (PWA wrapper via TWA)
- [ ] Apple App Store (WebView wrapper)
- [ ] Premium tier ($4.99/mo) — unlimited saves, history sync
- [ ] Embed widget for travel bloggers

---

## Security Notes

- Affiliate IDs live in frontend JS — acceptable for MVP, move to backend before scaling
- Rate limiting not yet implemented — add flask-limiter when traffic grows
- .env file is gitignored — never commit it
- SQLite db is ephemeral on Render free tier — data resets on redeploy (acceptable for now)
- For production scale: migrate to PostgreSQL (Render has free tier)

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
