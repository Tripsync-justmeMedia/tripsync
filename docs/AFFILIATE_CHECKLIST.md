# 📋 TripSync Affiliate Monetization Checklist

Use this interactive checklist to track and complete your partner integrations. Once approved or when you obtain an ID, drop it into the indicated lines in `planner.html` (or let me know and I'll wire it in for you!).

---

## ⚠️ Phase 1: High Priority (Replace Existing Placeholders)

These programs already have UI buttons and code paths in the TripSync planner, but currently use placeholder IDs:

- [x] **Viator (Tours & Activities)** ✅
  - **Portal / Signup:** [Viator Partner Program](https://www.viator.com/partner)
  - **Your Partner ID (PID):** `P00327306`
  - **Where Integrated:** `planner.html` (Checklist `chkActionTours`, sidebar `viatorLink`, sticky `bbActivities`) & `index.html` (card `btn-viator`)
  - **Current Value:** `P00327306` *(Active & Verified)*

- [ ] **CJ Affiliate (Expedia, Hotels.com, Vrbo)**
  - **Portal / Signup:** [CJ.com (Commission Junction)](https://www.cj.com)
  - **What You Need:** Your 7–9 digit **CJ Publisher ID (PID)**
  - **Where It Goes:** [`planner.html:974`](file:///Users/williamcommu/Desktop/JUST_ME_MEDIA_VAULT/JustMeMedia/01_ACTIVE/TripSync/planner.html#L974)
  - **Current Value:** `101234567` *(Placeholder)*

- [ ] **Skyscanner (Flight Searches)**
  - **Portal / Signup:** [Skyscanner Affiliate via Impact](https://app.impact.com/advertiser-advertiser-info/Skyscanner.brand) or [CJ Skyscanner](https://www.cj.com)
  - **What You Need:** Your affiliate tracking campaign link / tracking parameter
  - **Where It Goes:** [`planner.html:1372`](file:///Users/williamcommu/Desktop/JUST_ME_MEDIA_VAULT/JustMeMedia/01_ACTIVE/TripSync/planner.html#L1372)
  - **Current Value:** Generic unmonetized link to Skyscanner

- [ ] **Agoda (Alternative Accommodation)**
  - **Portal / Signup:** [Agoda Partners Program](https://partners.agoda.com) or join via [Awin Agoda](https://www.awin.com)
  - **What You Need:** Your Agoda CID (Client ID)
  - **Where It Goes:** Secondary hotel links in `planner.html` and `index.html`

- [ ] **Tiqets (Attractions & Museum Passes)**
  - **Portal / Signup:** Check active campaign under [Travelpayouts Programs](https://www.travelpayouts.com)
  - **What You Need:** Updated search deep-link format for Travelpayouts Campaign 89
  - **Where It Goes:** [`planner.html:1354`](file:///Users/williamcommu/Desktop/JUST_ME_MEDIA_VAULT/JustMeMedia/01_ACTIVE/TripSync/planner.html#L1354)

---

## 🚀 Phase 2: High-Converting New Revenue Additions

These convert with high conversion rates for international travelers:

- [ ] **eSIM Mobile Data (Airalo / Saily / Nomad)**
  - **Why:** Every international tourist needs data; 10%–20% recurring commission per package.
  - **Portal / Signup:**
    - [Airalo Affiliate Program (Impact)](https://app.impact.com/advertiser-advertiser-info/Airalo.brand)
    - [Saily Affiliate via Impact / Nord Security](https://saily.com/affiliates/)
  - **Placement:** Can be featured as a default checklist item in `planner.html` + Extras sidebar.

- [ ] **GetYourGuide (Experiences & Day Trips)**
  - **Why:** Largest tour inventory across Europe and North America; pays 8%–10% per booking.
  - **Portal / Signup:** [GetYourGuide Partner Portal](https://partner.getyourguide.com)
  - **Placement:** Alternative activity provider alongside Klook in `planner.html`.

- [ ] **DiscoverCars (Car Rental Comparison)**
  - **Why:** High volume in Europe, Americas, and islands ($15–$30 commission per booking).
  - **Portal / Signup:** [DiscoverCars Affiliate Program](https://www.discovercars.com/affiliates) or via Travelpayouts.
  - **Placement:** Complement or alternative to GetRentACar in the booking checklist.

- [ ] **Travel Banking & Currency Exchange (Wise / Revolut)**
  - **Why:** High-ticket payouts ($30–$75 per approved user) for zero foreign transaction fees.
  - **Portal / Signup:**
    - [Wise Affiliate Program](https://wise.com/us/affiliate-program)
    - [Revolut Affiliate Partner](https://www.revolut.com/affiliates/)
  - **Placement:** Recommended under "Budget & Currency" sidebar in `planner.html`.

---

## ✅ Phase 3: Already Verified & Active (No Action Needed)

These are live on [tripsync.ca](https://tripsync.ca) and actively accumulating tracked clicks:

| Service / Partner | Network | Tracking Identifier | Status |
|---|---|---|---|
| **Booking.com (Hotels)** | Direct Affiliate | `aid=2884913` | ✅ Live & Tracking |
| **Aviasales (Flights)** | Travelpayouts | `marker=733310`, `trs=533550`, `campaign=100` | ✅ Live & Tracking |
| **GetRentACar (Car Rentals)** | Travelpayouts | `marker=733310`, `campaign=222` | ✅ Live & Tracking |
| **Klook (Activities & Tours)** | Travelpayouts | `marker=733310`, `campaign=137` | ✅ Live & Tracking |
| **KiwiTaxi (Airport Transfers)** | Travelpayouts | `marker=733310`, `campaign=1` | ✅ Live & Tracking |
| **Welcome Pickups (Transfers)** | Travelpayouts | `marker=733310`, `campaign=627` | ✅ Live & Tracking |
| **Ekta (Travel Insurance)** | Travelpayouts | `marker=733310`, `campaign=225` | ✅ Live & Tracking |
| **AirHelp (Flight Claims)** | Travelpayouts | `marker=733310`, `campaign=120` | ✅ Live & Tracking |

---

## 🛠️ How to Update in Code

Whenever you get an ID, open [`planner.html`](file:///Users/williamcommu/Desktop/JUST_ME_MEDIA_VAULT/JustMeMedia/01_ACTIVE/TripSync/planner.html) line 973:

```javascript
const AFFILIATE = {
  cj_pid: 'YOUR_CJ_PID_HERE',
  booking_aid: '2884913',
  tp_marker: '733310',
  tp_trs: '533550'
};
```
And for Viator, line 1351:
```javascript
document.getElementById('viatorLink').href = `https://www.viator.com/search/${encodedDest}?pid=YOUR_VIATOR_PID`;
```
Once updated, deploy to production with:
```bash
cd JustMeMedia/01_ACTIVE/TripSync
netlify deploy --prod --dir=.
```
