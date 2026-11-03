# TripSync — Agent Session Briefing

## Project Identity

| Field | Value |
|---|---|
| **Product Name** | TripSync |
| **Company** | Just Me Media |
| **Type** | AI-powered travel planner (web app + PWA) |
| **Stack** | Python / Flask (backend) + HTML/CSS/JS (frontend) |
| **Live URL** | [https://tripsync.ca](https://tripsync.ca) |
| **Status** | Active — public beta |
| **AI Providers** | Groq (fast), Google Gemini (reasoning), Ollama (local/private) |

## What This App Does

TripSync generates detailed travel itineraries with pricing, booking links, and day-by-day plans. Uses a 3-tier AI strategy: Cloud (Groq), Expert Reasoning (Gemma 4), and Local (Ollama). Features currency arbitrage, flight duration estimation, and real-time booking partner links.

## Isolation Notice

> [!NOTE]
> TripSync is **completely independent** of LexSort / VERA / ProMailer / Events Arena.
> `docs/PRIVATE_HANDOFF.md` contains a "LexSort Accounts" section — this is just the founder's personal
> credential notes for his own infrastructure. It does NOT mean TripSync is part of LexSort.
> Do not import LexSort or VERA patterns into this project.

## Key Files
- `main.py` — Flask app entry point
- `server.py` — API routes
- `static/` — Frontend HTML/CSS/JS
- `docs/PRIVATE_HANDOFF.md` — Full accounts + infrastructure reference (read for credentials)
- `README.md` — Feature overview and tech stack

## Outbound / Affiliate Link Rules (learned the hard way)
- **Never hand-write partner URLs.** Use the helpers next to the `AFFILIATE` block in `index.html`
  and `planner.html`: `citySlug()`, `skyscannerUrl()`, `tiqetsUrl()`, `viatorUrl()` (and `jsStr()`
  for anything interpolated into an inline `onclick`). Every one of these was added because a
  hand-written URL 404'd, 400'd, dropped its tracking param, or broke on an apostrophe (`Xi'an`).
- Verified URL shapes (re-check after any change, see `docs/AFFILIATE_CHECKLIST.md`):
  Booking `/searchresults.html?ss=&aid=&checkin=&checkout=&group_adults=` ·
  Tiqets `/en/search?q=` (NO trailing slash) · Skyscanner
  `/transport/flights/<from-slug>/<to-slug>/<YYMMDD>/<YYMMDD>/?adults=N` · Viator
  `/searchResults/all?text=&pid=&mcid=`.
- `/api/flight-prices` needs `TRAVELPAYOUTS_TOKEN`; without it live fares silently disappear.
  See `.env.example`.
- Ekta insurance (`p=5869`, campaign 225) was removed — the marker is not subscribed, the
  redirector returns 400. Do not re-add without a subscribed campaign.
- **Multi-city deep links are built server-side** by `build_multi_city_url()` in `server.py`,
  using Cheapflights' verified pattern `/flight-search/LEG/DATE/LEG/DATE/.../LEG` (IATA codes,
  `YYYY-MM-DD`). Never assemble that path in the browser — the frontend only renders
  `data.multi_city_url`. A malformed leg/date alternation produces a broken search page.
- **CJ Publisher ID `7953580`** (Just Me Media) is set in `index.html` and `planner.html`.
  Booking.com links prefer the CJ wrapper and fall back to `aid=2884913`.
  `agoda_cid` / `expedia_affcid` are still `YOUR_*` placeholders — do not advertise either
  partner (including in the logo marquee) until a real CID exists.

## Homepage Hero Rules (learned the hard way)
- `hero-bg.jpg` is **992×1071 (portrait)** — plane at the top, stewardess bottom-right.
  On a 16:9 screen, showing the whole image needs a ~1554px-tall hero, so it is impossible to
  show both figures uncropped without a huge empty hero. Chosen trade-off:
  `background-size: cover; background-position: top center` — the plane is always fully
  visible and there is never dead space. The stewardess is cropped on wide desktop.
  A wide 16:9 hero image would be needed to fix that; do not "solve" it with `contain`.
- Hero height is `min-height: calc(100vh - 60px)`. It was `100vh`, which measured the whole
  viewport *on top of* the 60px header and pushed the footer below the fold.
- **Dead space is a layout bug, not a styling preference.** `.results-area` must keep
  `padding: 0`; the padding lives on `#destinationsOutput`, with
  `#destinationsOutput:empty { display: none }`. Otherwise an empty results panel leaves a
  48px cream band between the hero and the footer. Verify with a probe: footer `top` must
  equal hero `bottom`.
- Mobile keeps `min-height: 600px` (overrides the `calc`). On mobile the planner is the point —
  "less is more". iPad / landscape should feel like the full desktop page.

## Trusted Partners Marquee
- The partner strip is an **infinite marquee**, not a static row, so the partner list can grow
  without adding height or clutter. Markup: `.partner-logos > .partner-marquee > .partner-track`.
- The track holds the list **twice**; the duplicate set is wrapped in `.partner-dup` and marked
  `aria-hidden="true"`. The animation is a seamless `translateX(-50%)` over 45s, paused on
  hover, with edge mask fades and a `prefers-reduced-motion` fallback (animation off,
  duplicates hidden).
- **All logos are self-hosted in `assets/partners/`** — never hotlink a partner CDN again.
  They are rendered monochrome white via `filter: brightness(0) invert(1)` at `opacity: .7`,
  so any logo with a transparent background works; do not add a full-colour PNG (it becomes a
  white blob under that filter).
- Real marks: Booking.com, Skyscanner, Klook, AirHelp (Wikimedia), Tiqets (official CDN).
  Authored white wordmarks (no official asset available): Viator, KiwiTaxi, Welcome Pickups,
  GetRentACar, Aviasales. Swap in official brand-kit files under the same filenames when
  available — no code change needed.
- 10 partners are shown: Booking.com, Skyscanner, Viator, Tiqets, Klook, KiwiTaxi,
  Welcome Pickups, GetRentACar, AirHelp, Aviasales. **Agoda and Expedia are deliberately
  excluded** (placeholder affiliate CIDs).
- On mobile the marquee is moved to the end of the hero with `order: 10` so it never pushes
  the search form, CTA, or "Optional extras" down. Logos shrink to 16px at ≤640px.

## Dev Commands
```bash
# Install deps
pip install -r requirements.txt

# Run locally (frontend)
python3 -m http.server 8080

# Run locally (full app + API)
python main.py   # or python server.py
```

## Deploying (READ THIS — the old assumption was wrong)

**A `git push` does NOT deploy.** The Netlify site `tripsync-ca-studio`
(id `a7d0f090-eae5-41ca-b28d-674a513e697e`, team `wcommu`, custom domain `tripsync.ca`)
is **not connected to GitHub** — `repo_url` is null and every deploy in its history is a manual
CLI deploy. Pushing only updates the repo.

Deploy from a **clean staging directory**, never from the repo root:

```bash
STAGE=/tmp/ts_deploy
rm -rf $STAGE && mkdir -p $STAGE
cp index.html planner.html affiliate.html assistant.html dashboard.html handle.html \
   privacy.html terms.html manifest.json sw.js robots.txt sitemap.xml netlify.toml \
   hero-bg.jpg hero-bg-wide.jpg $STAGE/
cp -R assets static $STAGE/
cp *.png *.ico $STAGE/
netlify deploy --prod --dir=$STAGE
```

- **NEVER run `netlify deploy --dir=.`** — the repo root contains `.env`, `credentials.json`,
  `mock_sheets_db.json`, `.venv/` and `docs/PRIVATE_HANDOFF.md`. `--dir=.` uploads all of it to a
  public CDN. Only the static frontend files belong in the publish set.
- Netlify post-processing rewrites links (`planner.html` → `/planner`) and adds pretty URLs. That
  is expected; it does not touch CSS/JS.
- `netlify.toml` (headers + `/api/*` proxy to the Render backend) lives in the repo root and is
  applied by the CLI; it is also copied into the publish set.

**Known blocker (2026-11-01):** production deploys return
`403 {"error":"Account credit usage exceeded - new deploys are blocked until credits are added"}`.
Draft deploys (`netlify deploy --dir=$STAGE`, no `--prod`) still succeed and give a preview URL.
To go live again the founder must add credits / upgrade at
<https://app.netlify.com/teams/wcommu/billing>, then re-run the `--prod` command above.


## ⚠️ CRITICAL: Test Locally Before Deploying (learned the hard way)

**ALWAYS run the site locally and test all functionality before pushing to GitHub / deploying to Netlify.**

The site is served locally via Python HTTP server on port 8080:
```bash
cd /Users/williamcommu/Desktop/JUST_ME_MEDIA_VAULT/JustMeMedia/01_ACTIVE/TripSync
python3 -m http.server 8080
# Then open http://localhost:8080/index.html in a browser
```

**Never push to GitHub without:**
1. ✅ Running the local server (`python3 -m http.server 8080`)
2. ✅ Opening `http://localhost:8080/index.html` in a browser
3. ✅ Clicking every button (especially "Curate My Ideal Journey") to verify no JS errors
4. ✅ Verifying the hero background image loads correctly
5. ✅ Verifying all JavaScript functions work without null reference errors

**Common failures caught this way:**
- Removed DOM elements (`#welcomeState`) still referenced in JS → crashes `searchTrip()`
- Background image files missing or wrong path → gray placeholder instead of image
- CSS changes breaking layout → overlapping elements, dead space gaps

Deployments are **manual** (`netlify deploy --prod --dir=<staging>`) — a GitHub push does not
deploy. See `AGENTS.md` → "Deploying" before shipping, and never deploy the repo root.

---

## ⛔ HARD RULE: No Pushes Without Explicit Approval

**NEVER push to GitHub or deploy to Netlify without the founder's explicit approval.**

This is a non-negotiable rule. Before any push/deploy:
1. ✅ Test locally first (see rules above)
2. ✅ Show the founder the visual result (screenshot or live preview)
3. ✅ Wait for explicit "yes" or "approved" from the founder
4. ✅ Only then push and deploy

**Never assume approval.** If the founder says "test locally first" or "let me review," that means STOP and wait. Do not push. Do not deploy. Do not run `git push` or `netlify deploy` in the background.

This rule was added because previous sessions wasted GitHub and Netlify rate limits by pushing/deploying without approval.

## Accounts
| Service | Account | Notes |
|---|---|---|
| Groq API | In `.env` | Fast cloud inference |
| Google Gemini | In `.env` | Expert reasoning tier |
| Booking.com Affiliate | ID: 2884913 | Active |
| CJ Affiliate | Publisher ID: 7953580 | Just Me Media; Booking.com links |
| Travelpayouts | Marker 733310 / trs 533550 | Klook, Tiqets, Aviasales, AirHelp, KiwiTaxi, Welcome Pickups, GetRentACar |
| Viator (Partnerize) | pid P00327306 / mcid 42383 | Active |
| Netlify | William@lexsort.com | tripsync.ca frontend |
