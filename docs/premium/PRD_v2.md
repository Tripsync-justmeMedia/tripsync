# TripSync Premium - Product Requirements Document v2
**Date:** May 2026  
**Key Change:** Real-time prices are FREE for all users

## Free Tier (Builds user base)
- ✅ AI multi-stop route generation
- ✅ **Real-time flight & hotel prices** (via Amadeus + affiliates)
- ✅ Save 3 itineraries
- ✅ Basic PDF export
- ✅ Share read-only link

## Premium Tier ($4.99/mo or $29.99/yr) - Control & Collaboration
- ❌ Edit itinerary (cities, dates, notes)
- ❌ Calendar view (month/week/day)
- ❌ Extend/shorten stays (slider auto-recalculates)
- ❌ Sync to Google/Apple Calendar
- ❌ Collaborate with travel buddies
- ❌ Export to Excel/CSV
- ❌ Remove "Just Me Media" footer
- ❌ Unlimited saved itineraries

## Why this works
Free users get the BEST prices → They keep coming back
Premium users get CONTROL → They pay

## Real-time Price APIs (Free tier for launch)

| API | Free Limit | Used for |
|-----|-----------|----------|
| Amadeus | 500/day | Flight prices |
| Agoda | Unlimited (affiliate) | Hotel prices |
| Booking.com | Unlimited (via Awin) | Hotel prices |

## Monthly Cost at 10,000 users
- Amadeus: $0 (within free tier if 500 searches/day)
- Database: $0 (Render free tier)
- Auth: $0 (Supabase free tier)
- **Total: $0** until you exceed 500 daily searches
