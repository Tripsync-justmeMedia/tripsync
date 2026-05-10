# TripSync — Technical Handoff & Quick Start
**Updated:** May 10, 2026  

This document provides a technical overview of the TripSync architecture and instructions for maintaining the production environment.

## 🚀 Quick Start
1.  **Local Dev**: `python3 server.py` (App runs on http://127.0.0.1:5000)
2.  **Environment**: Ensure `.env` contains `GROQ_API_KEY` and `GEMINI_API_KEY`.
3.  **Deployment**: Pushes to `main` branch trigger auto-deploy to Render.

## 🧠 AI Architecture
TripSync uses a unique **3-Tier AI System** for unmatched reliability:
*   **Tier 1: Cloud (Groq/Llama 3.3)** — Primary engine for high-speed results.
*   **Tier 2: Expert (Gemini/Gemma 4)** — Deep reasoning for expert queries.
*   **Tier 3: Local (Ollama/Gemma4)** — Optional on-device processing for privacy.

**Zero-Downtime Fallback**: If the Expert tier (Tier 2) experiences any API latency or rate limits, the system automatically and silently hands off the request to the Cloud tier (Tier 1) to ensure the user always receives a response.

## 📊 Infrastructure
*   **Hosting**: Render (Web Service)
*   **Database**: SQLite (`tripsync.db`). Note: Data is ephemeral on Render's free tier. For persistent stats, migrate to PostgreSQL.
*   **PWA**: Service worker (`sw.js`) and manifest (`manifest.json`) are configured for "Add to Home Screen" support.

## 💰 Monetization
Affiliate tracking is integrated via `index.html` and `planner.html`.
*   **Booking.com**: Active (AID: 2884913)
*   **Agoda/Expedia**: Placeholders ready for CID/AffID update.
*   **Viator**: Tour links integrated into the Interactive Planner.

## 🔒 Security
*   API keys are strictly managed via environment variables on the Render dashboard.
*   Frontend data is "Local-First," stored in the user's browser for maximum privacy.

---
*Just Me Media — High-Performance Travel Tech*
