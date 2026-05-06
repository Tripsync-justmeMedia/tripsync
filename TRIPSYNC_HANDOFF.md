# TripSync — Complete Project Handoff
**Last Updated:** May 2026  
**Owner:** William — Just Me Media  
**Company:** Just Me Media  
**Developer Contact:** wcommu@gmail.com  

## What TripSync Is
AI-powered travel destination finder + multi-stop smart router.

**Live URL:** https://tripsync-ilao.onrender.com  
**GitHub Repo:** https://github.com/Tripsync-justmeMedia/tripsync  

## Accounts
- GitHub: wcommu@gmail.com
- Render: wcommu@gmail.com
- Groq API: wcommu@gmail.com (WORKING)

## Tech Stack
- Frontend: HTML/CSS/JS (single file)
- Backend: Python Flask + Gunicorn
- AI: Groq API (llama-3.3-70b-versatile)
- Database: SQLite
- Hosting: Render.com

## Features (ALL WORKING)
- Multi-stop anywhere-anywhere routing
- 3 destination cards
- PDF export
- Save/load trips to localStorage
- Share: WhatsApp, Twitter, Facebook, Email
- 12 currencies
- Mobile responsive

## API Routes
- GET / - serves index.html
- POST /api/tripsync - destination cards
- POST /api/multi-stop - multi-stop itinerary
- POST /api/track-click - affiliate tracking
- GET /api/stats - usage stats

## Environment Variables (on Render)
GROQ_API_KEY = configured and working

## Commands
Local dev: cd ~/tripsync && python3 server.py
Deploy: git add . && git commit -m "msg" && git push

## Test Query
"toronto-anywhere-anywhere-thailand-bali-anywhere-anywhere-toronto, 1 month each, Jan-Apr 2027"

## Affiliate IDs (placeholders to replace)
YOUR_BOOKING_AID, YOUR_AGODA_CID, YOUR_EXPEDIA_AFFCID

## Files Location
~/tripsync/
  - server.py
  - index.html
  - requirements.txt
  - TRIPSYNC_HANDOFF.md

## For New AI Sessions
"TripSync is live at https://tripsync-ilao.onrender.com. Files at ~/tripsync/. Built with Flask + Groq. Multi-stop routing works."
