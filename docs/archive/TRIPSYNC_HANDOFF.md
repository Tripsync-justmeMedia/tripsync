# TripSync — Technical Handoff & Maintenance Guide
**Updated:** October 12, 2026 | **Architecture Version:** v2.6 | **Budget:** $0

This document provides the complete technical architecture, active endpoints, failover mechanisms, and operational maintenance procedures for TripSync.

---

## 🚀 Quick Reference

| Service | Details | Link / Access |
|---|---|---|
| **Live Frontend** | Netlify Production | [https://tripsync.ca](https://tripsync.ca) |
| **Live Backend** | Render Web Service (`gunicorn server:app`) | `https://tripsync-nvss.onrender.com` |
| **Health Ping** | Version & AI provider diagnostics | `https://tripsync-nvss.onrender.com/api/ping` |
| **Render Account** | `promailer@justmemedia.ca` | [dashboard.render.com](https://dashboard.render.com) |
| **Netlify Account** | `wcommu@gmail.com` | Project: `tripsync-ca-studio` |
| **GitHub Remote** | `Tripsync-justmeMedia/tripsync` | Pushes to `main` auto-deploy backend to Render |
| **Uptime Monitor** | UptimeRobot (`wcommu@gmail.com`) | 5-minute HTTP ping to `/api/ping` keeps Render awake |

---

## 🧠 AI Engine Architecture ($0 Zero-Downtime)

To eliminate broken models, rate-limit 500s, and cloud deprecations, TripSync utilizes an automated 4-layer failover chain:

```
User Query (Main Search or Planner)
   ↓
[ Layer 1: Groq Cloud AI ]
   ↳ Tries active models in sequence:
     1. qwen/qwen3.8-27b (ultra-fast, ~2s)
     2. openai/gpt-oss-120b
     3. openai/gpt-oss-20b
   ↳ If 404/429/error → automatically rolls to Layer 2
   ↓
[ Layer 2: Google Gemini Cloud API ]
   ↳ Target: gemini-flash-lite-latest (fast cloud fallback)
   ↳ Fallback: gemma-4-26b-a4b-it (with thought-chain filtering)
   ↳ If unavailable → silently rolls to Layer 3
   ↓
[ Layer 3: Curated Dynamic Fallback Engine ]
   ↳ Built-in server-side engine in server.py
   ↳ Generates tailored 3-destination packages & full 5-day itineraries
   ↳ Automatically calculates return flights for the user's departure city and currency
   ↳ ZERO error pages, ZERO hangs, ZERO downtime for visitors
```

---

## 🛠️ Deployment Workflows

### 1. Backend Updates (Render)
Render automatically builds and deploys upon pushes to the `Tripsync-justmeMedia/tripsync` repository:
```bash
git add server.py requirements.txt
git commit -m "feat/fix: description"
git push origin main
```
*Note: Ensure the git remote `origin` pushes to `https://github.com/Tripsync-justmeMedia/tripsync.git`.*

### 2. Frontend Updates (Netlify)
Because Netlify is linked directly to the production site `tripsync.ca`, frontend asset updates (HTML, CSS, JS, Service Worker) should be deployed via Netlify CLI:
```bash
netlify deploy --prod --dir=.
```

---

## 🔐 Environment Variables

### Render Dashboard (`dashboard.render.com`)
* `GROQ_API_KEY`: Active Groq API key (`gsk_...`)
* `GEMINI_API_KEY`: Google AI Studio key (optional, adds secondary reasoning tier)
* `PORT`: `5001` (or Render default)
* `DB_PATH`: `/tmp/tripsync.db` (ephemeral SQLite; PostgreSQL supported via `DATABASE_URL`)

### Local Development (`.env`)
```env
GROQ_API_KEY=your_groq_key_here
GEMINI_API_KEY=your_gemini_key_here
```

---

## 📱 PWA & Browser Hygiene

* **Service Worker (`sw.js` v4)**:
  * Strict scheme filter: ignores `chrome-extension://` requests to prevent Cache API TypeError.
  * API calls (`/api/*`) strictly bypass cache to ensure real-time search results.
  * Network-first for HTML pages, cache-first for static assets.
* **Modern Standards**:
  * Uses `<meta name="mobile-web-app-capable" content="yes">` alongside iOS legacy tags.
  * Content Security Policy in `netlify.toml` explicitly whitelists `cdnjs.cloudflare.com`, `googletagmanager.com`, and `fonts.googleapis.com`.
  * Removed all legacy ad-network injection scripts (`emrld.ltd`).

---

## 🔍 Health Check & Diagnostics

Check live backend health and environment flags anytime:
```bash
curl -s https://tripsync-nvss.onrender.com/api/ping
```
**Response Format:**
```json
{
  "status": "online",
  "version": "2.6",
  "has_groq": true,
  "has_gemini": false,
  "timestamp": 1791817556.05
}
```
If `has_groq` or `has_gemini` is false, check the environment variables in the Render dashboard.

---
*Just Me Media — High-Performance Zero-Downtime Travel Architecture*
