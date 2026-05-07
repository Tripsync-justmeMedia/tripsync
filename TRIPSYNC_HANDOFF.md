# TripSync — Complete Project Handoff
**Last Updated:** May 7, 2026  
**Owner:** William — Just Me Media  
**Status:** FULLY UPGRADED - Premium UI & Local History Active

## Live URL
https://tripsync-ilao.onrender.com

## Working Features
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
- Example search buttons
- Mobile responsive

## Affiliate Programs (In Progress)
- Agoda: Manual review (this week)
- Booking.com: Applied via Awin (3-7 days)
- Expedia: Payment setup (this week)
- Skyscanner: Form submitted (1-2 weeks)

## Production Advice
- **Domain**: While `onrender.com` works, a custom domain (e.g., `.com`, `.io`) is recommended for App Store approval and affiliate trust.
- **Hosting**: Ensure Render is on the **Starter ($7/mo)** plan to avoid "cold starts" which can frustrate app users.

## Commands
Local dev: cd ~/tripsync && python3 server.py
Deploy: git add . && git commit -m "msg" && git push

## When Affiliate IDs Arrive
Run these commands (replace with real IDs):
sed -i '' 's|https://www.agoda.com/search?city=|https://www.agoda.com/search?city=&cid=YOUR_ID|g' index.html
sed -i '' 's|https://www.booking.com/searchresults.html?dest=|https://www.booking.com/searchresults.html?dest=&aid=YOUR_ID|g' index.html
sed -i '' 's|https://www.expedia.com/Hotel-Search?destination=|https://www.expedia.com/Hotel-Search?destination=&affcid=YOUR_ID|g' index.html
git add index.html && git commit -m "Add affiliate IDs" && git push

