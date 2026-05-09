# TripSync — Complete Project Handoff
**Last Updated:** May 9, 2026  
**Owner:** William — Just Me Media  
**Status:** FULLY UPGRADED - Premium UI & Local History Active

## Live URL
https://tripsync-ilao.onrender.com

## Working Features
- **NEW: Private AI Mode (Gemma 4)** — Dual-mode toggle allowing strict local processing via Ollama `gemma4` for complete privacy.
- **NEW: Full PWA Support (Store Ready)**
- **NEW: App Icon & Manifest (`manifest.json`)**
- **NEW: Offline Caching (`sw.js`)**
- Google Flights links (Robust deep-linking)
- Booking.com hotel links
- Agoda hotel links
- Expedia hotel links
- **NEW: Viator Tour Booking links**
- PDF export (Branded)
- Save trips & Interactive History (localStorage - Local First)
- Privacy Policy & Terms of Service (Compliant)
- **NEW: Interactive Planner** — Manual edit (add/remove) + AI Refinement tool.
- **NEW: Dual Flight Booking** — Google Flights & Skyscanner side-by-side.
- **NEW: Viral Sharing** — WhatsApp, X, and Facebook sharing for all itineraries.
- **NEW: Master Reset (Danger Zone)** — Complete device wipe option.
- **NEW: Legacy Data Repair** — Auto-fixes old trip data on load.
- Mobile responsive & High-End Glassmorphism UI.
- Just Me Media footer branding.

## Affiliate Programs
| Partner | Status | ID Location |
| :--- | :--- | :--- |
| **Booking.com** | ✅ Active | `index.html` (JS) & `planner.html` |
| **Agoda** | ⏳ Applied | `index.html` (JS) |
| **Expedia** | ⏳ Applied | `index.html` (JS) |
| **Viator** | ⏳ Applied | `planner.html` (JS) |
| **Skyscanner** | ❌ Re-apply | `index.html` & `planner.html` |

*See [AFFILIATE_TRACKER.md](file:///Users/williamcommu/.gemini/antigravity/brain/e714ab51-99f0-4e2e-b39c-63e574765a43/AFFILIATE_TRACKER.md) for detailed ID swap instructions.*

## Production Roadmap & Goals
1.  **Friends & Family Beta**: Send out for feedback and track clicks in the Stats modal.
2.  **Monetization Swap**: As affiliate approvals arrive, update placeholders in the code.
3.  **Domain Migration**: Purchase `gettripsync.com` and connect to Render.
4.  **Store Submission**: Use **PWABuilder.com** to generate native wrappers for Apple and Google Play.
5.  **Scaling**: Move from ephemeral SQLite to **Render PostgreSQL** once traffic exceeds 100+ daily users.

## Commands
Local dev: `python3 server.py`
Deploy: `git add . && git commit -m "msg" && git push`

