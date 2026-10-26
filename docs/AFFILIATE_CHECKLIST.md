# 📋 TripSync Affiliate Monetization Checklist

Last verified end-to-end: **2026-10-25** (local build, live HTTP checks + real browser).

How each link was verified: render the page → pull every generated `href` → follow it with a
browser user-agent **and** open it in a real browser (bot-protected partners only show the truth
in a browser). A link only counts as working if it lands on the right city/results page *and*
keeps its tracking parameter.

---

## ✅ Phase 3: Verified working (no action needed)

| Partner | Network | Tracking | Landing page check | Status |
|---|---|---|---|---|
| **Booking.com (hotels)** | Direct | `aid=2884913` (+ `label=` per placement) | `searchresults.html?ss=<city>&checkin=&checkout=&group_adults=` lands on city results with dates + guests kept | ✅ Live & tracking |
| **Viator (tours)** | Direct | `pid=P00327306`, `mcid=42383` | `/searchResults/all?text=<city>` lands on city tours | ✅ Live & tracking |
| **Aviasales (flights)** | Travelpayouts | `marker=733310`, `trs=533550`, `campaign=100` | `marker` re-appended by redirector | ✅ Live & tracking |
| **Klook (activities)** | Travelpayouts | `campaign=137` | `affiliate.klook.com/redirect` → city search | ✅ Live & tracking |
| **Tiqets (museums)** | Travelpayouts | `campaign=89` | `/en/search?q=<city>` → city landing page | ✅ Live & tracking |
| **GetRentacar (cars)** | Travelpayouts | `campaign=222` | `track_id` + `utm_source=travelpayouts`; Cloudflare "Just a moment" is normal for bots | ✅ Live & tracking |
| **KiwiTaxi (transfers)** | Travelpayouts | `campaign=1` | `tpo=<id>-733310` | ✅ Live & tracking |
| **Welcome Pickups** | Travelpayouts | `campaign=627` | `aff_track_id` | ✅ Live & tracking |
| **AirHelp (claims)** | Travelpayouts | `campaign=120` | `a_aid=Travelpayouts` + `data1` | ✅ Live & tracking |

---

## ⛔ Removed 2026-10-25 — dead links

| Partner | Why it was removed |
|---|---|
| **EKTA Travel Insurance** (`p=5869`, `campaign_id=225`) | `tp.media` returns **HTTP 400 "marker is not subscribed to campaign"** — the marker `733310` is not enrolled in that program, so every insurance button was an error page. The checklist row "🛡️ Insurance (opt)" was kept (it is a useful traveller to-do) but its `Get ↗` action link was removed. **Re-add only after subscribing to an insurance campaign under marker 733310.** |

---

## 🛠️ Bugs fixed in the same pass (do not regress)

1. **Booking.com `/search.html`** — does not exist; the planner's "Book This Hotel →" buttons
   returned **"Page Not Found"**. Always use `/searchresults.html`. Both the search-results cards
   *and* the planner hotel cards now share the correct path.
2. **Tiqets `/en/search/?q=`** (trailing slash) — hard **404**. Correct form is `/en/search?q=`,
   which 302s to the real city page.
3. **Skyscanner `/transport/flights-from/<from>/to/<to>/`** — does not exist (404). Correct form:
   `/transport/flights/<origin-slug>/<dest-slug>/<YYMMDD>/<YYMMDD>/?adults=N`.
4. **Viator `/search/<city>`** — 302s and can drop `pid`. Now uses
   `/searchResults/all?text=<city>&pid=…&mcid=…`, which keeps attribution and always renders results.
5. **City names were injected raw into inline `onclick`** — a city like `Xi'an` produced invalid
   JS and killed the whole booking row. All inline handlers now go through `jsStr()`
   (`index.html`), and all URL builders go through `citySlug()` / `skyscannerUrl()` /
   `tiqetsUrl()` / `viatorUrl()`.

Rule: **never hand-write a partner URL again** — use the helpers at the top of `index.html`
(`AFFILIATE` block) and `planner.html`. Re-run the verification after touching them.

---

## ⚠️ Open items (revenue, not broken links)

- **Fares are cached, not live.** `TRAVELPAYOUTS_TOKEN` is now set and `/api/flight-prices`
  returns real fares, but the Data API is a ~48h cache and has nothing for most exact dates,
  so the UI degrades to "Cheapest fare found for Nov 16 — your dates may differ". True
  real-time prices need a different provider; see **[REALTIME_PRICING.md](REALTIME_PRICING.md)**
  for the per-partner gates and what to request (Duffel for flights, Booking widget for
  hotels, Tiqets token for attractions).
- **Unverified discount claims removed** — "Aviasales (40% Off Flights)" and
  "GetRentacar.com (Save 10%)" were not backed by any partner data. Now plain labels.
- **Unused placeholder IDs**: `cj_pid`, `agoda_cid`, `expedia_affcid` are still `YOUR_*`
  placeholders but are **not referenced by any link**. Either wire a real program or delete the
  keys to avoid a future false-positive.

## 🚀 High-converting additions (unchanged)

- **eSIM (Airalo / Saily / Nomad)** — every international traveller needs data; recurring commission.
- **GetYourGuide** — alternative to Klook, 8–10% per booking.
- **DiscoverCars** — complement to GetRentacar.
- **Wise / Revolut** — travel banking, $30–$75 per approved user.
- **Insurance** — highest-value slot currently empty; pick a program you are actually subscribed to.
