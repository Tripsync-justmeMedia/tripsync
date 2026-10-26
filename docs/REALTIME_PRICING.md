# Real-Time Pricing — What's Actually Possible (Oct 2026)

Researched against each partner's own developer documentation. This is the honest map of
"can we show a live price on our page, or do we have to send the user to the partner's page?"

Short version:

- **Flights** — live prices on our page need either 50k MAU (Travelpayouts) or a real flight
  API (Duffel). We ship cached fares (~48h) with honest labels.
- **Hotels** — we *can* show live prices today, but only through Booking.com's official
  widget (iframe). Their Demand API needs Managed Affiliate status.
- **Activities** — Tiqets gives affiliates a self-serve API token that includes
  availability & pricing. Viator's real-time `/availability/check` needs Full Access.
- **Cars** — no API product available to us. Partner page only.

---

## What ships today

`/api/flight-prices` → `fetch_flight_price()` in `server.py`:

| Order | Source | Freshness | Label shown |
|---|---|---|---|
| 1 | `aviasales/v3/prices_for_dates` with the user's exact dates | cached, per-date | "Live fare for your dates" |
| 2 | `v1/prices/cheap` for the user's departure **month** | cached (~48h) | "Cheapest fare found for Nov 16 on Air Canada — your dates may differ" |
| 3 | `prices_for_dates` with no date filter | cached | same as above |

Requires `TRAVELPAYOUTS_TOKEN` in `.env`. Without it, the whole block silently disappears.

**Why not truly live?** The Aviasales **Flight Search API** (real-time, returns a `search_id`
then results) is gated: *"We only provide access to Projects with MAU starting from 50000."*
*(source: Travelpayouts help centre, article 30565016140434)*

---

## Partner-by-partner reality

### Travelpayouts / Aviasales — flights
| | |
|---|---|
| What we have | Data API token (marker `733310`) |
| Real-time product | Flight Search API (v2, since 1 Nov 2025) |
| Gate | **50,000 MAU**, no exceptions; also 100 req/hour per IP |
| Verdict | Not available to a beta. Data API + honest labels is the correct play. |

### Duffel — flights (the real-time option)
| | |
|---|---|
| What | REST API, `POST /air/offer_requests` → live offers from 500+ airlines |
| Signup | **Instant, self-serve** — `https://app.duffel.com/join`, test token in ~1 min |
| Cost | No upfront cost; per-order fee (published around $3/order + a % of fare — confirm at signup) |
| Gate | Test mode is instant. **Live selling requires Duffel to activate your account** (business details, how you sell) |
| Fit | Best available route to real-time flight prices on our own page |

**Action:** create the account, send me the test token. I'll wire `fetch_flight_price` to try
Duffel first and fall back to Travelpayouts, keeping the same `exact`/`basis` contract so the
UI labels stay honest.

### Booking.com — hotels
| | |
|---|---|
| What we have | Affiliate ID `2884913` (standard affiliate) |
| Demand API | Real-time availability + prices, but **Managed Affiliate Partner** status required, plus an API key token + affiliate ID header |
| Available today | **Partner Centre → Marketplace → Map Widget / Search Box** — iframe that renders *live* prices, attributed to our `aid` |
| Verdict | We cannot print hotel prices ourselves, but we *can* embed genuinely live prices. Replaces hand-written hotel cards with a real, bookable, live surface. |

**Action:** Partner Centre → Marketplace → create **Map Widget** for a destination (and a
Search Box for the results page) → paste the generated snippet to me.

### Tiqets — attractions (best self-serve win)
| | |
|---|---|
| Docs | `developers.tiqets.dev` (Distributor API) |
| Auth | `Authorization: Token <partner-api-key>` against `api.tiqets.com` |
| Access | **Keys created in the affiliate portal start with catalogue + availability/pricing access.** More advanced endpoints need review by `affiliates@tiqets.com` |
| Verdict | Real availability and pricing for attractions, available to us right now, self-serve. |

**Action:** `tiqets.com/affiliate` → **Tools → API tokens** → create token with
*Availability & Pricing* → send it to me.

### Viator — attractions
| | |
|---|---|
| What we have | Affiliate account (Basic Access) |
| Basic Access | Catalogue + `/availability/schedules/{product-code}` (schedules & pricing in bulk) |
| Real-time price check | `/availability/check` — **Full Access only**, requires approval + certification |
| Auth | `exp-api-key` header, `Accept: application/json;version=2.0`, `https://api.viator.com/partner` |
| Verdict | Basic gives real *schedules* (better than nothing, no live price calc). Apply for Full Access for real-time pricing. |

**Action:** request Full Access in the Viator partner portal; meanwhile send the API key and
I'll use `/availability/schedules` for "next available dates" on product cards.

### GetYourGuide — attractions
| | |
|---|---|
| API | Good API (`X-ACCESS-TOKEN`), public OpenAPI spec |
| Gate | **Basic access requires 100,000 monthly visits** (websites) |
| Verdict | Not eligible. Revisit when traffic grows. |

### Kiwi.com / Tequila — flights
| | |
|---|---|
| Status | Public B2B access withdrawn May 2024; **invitation-only** since |
| Verdict | Dead end for us. |

### Amadeus — flights/hotels
| | |
|---|---|
| Status | **Self-Service portal decommissioned 17 July 2026**; keys disabled. Enterprise contract only |
| Note | `server.py` still contains an Amadeus code path — it is dead code, not a fallback |

### Hotellook (Travelpayouts hotels)
| | |
|---|---|
| Status | **API fully disabled 20 October 2025.** No hotel API remains at Travelpayouts |
| Verdict | Removed from consideration. |

### GetRentacar / car rental
No public API. Partner page only. Booking.com widgets can cover cars if enabled on the account.

---

## Recommended sequence

1. **Duffel** (flights) — biggest honesty win; replaces "cached fare from a different day" with
   a real price for the user's dates.
2. **Booking Map Widget + Search Box** (hotels) — live prices with zero API gate.
3. **Tiqets token** (activities) — real availability/pricing, self-serve.
4. **Viator Full Access** (activities) — only if we want in-page price checks rather than
   schedules; slowest approval.
5. Only then consider Booking Demand API / Travelpayouts Search API, both of which need scale
   we don't have.

## What I need from you

| # | Item | Where |
|---|---|---|
| 1 | Duffel test access token | `app.duffel.com` → Dashboard → Access tokens |
| 2 | Booking Map Widget snippet (+ Search Box) | Partner Centre → Marketplace → Map Widget |
| 3 | Tiqets API token (availability & pricing) | `tiqets.com/affiliate` → Tools → API tokens |
| 4 | Viator API key | Viator partner portal → API |
| 5 | Apply for Viator **Full Access** | Viator partner support / portal |

Everything goes into `.env` (gitignored) or the page markup — never committed.

## Sources

- Travelpayouts Flight Search API access (50k MAU): `support.travelpayouts.com/hc/en-us/articles/30565016140434`
- Travelpayouts Data API: `support.travelpayouts.com/hc/en-us/articles/203956163`
- Booking.com Demand API auth / managed partners: `developers.booking.com/demand/docs/development-guide/authentication`
- Booking.com Map Widget (live prices, iframe): `affiliates.support.booking.com/kb/s/article/Map-Widget`
- Tiqets Distributor API + keys: `developers.tiqets.dev/basics/api-keys`
- Viator access levels: `partnerresources.viator.com/travel-commerce/levels-of-access`
- Viator technical guide (real-time check): `partnerresources.viator.com/travel-commerce/technical-guide`
- GetYourGuide access requirements: `partner.getyourguide.support/hc/en-us/articles/13981133907613`
- Kiwi.com partnership change: `media.kiwi.com/articles-and-interviews/better-for-business-kiwi-com-takes-a-new-approach-to-partnerships`
- Amadeus Self-Service shutdown: `developers.amadeus.com` (portal notice, 17 Jul 2026)
- Hotellook API closure: `support.travelpayouts.com/hc/en-us/articles/29534131568530`
- Duffel quick start: `duffel.com/docs/guides/getting-started-with-flights`
