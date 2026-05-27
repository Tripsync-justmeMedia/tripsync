import os
import json
import sqlite3
import logging
import re
import time
from datetime import datetime
from flask import Flask, request, jsonify, send_from_directory
from dotenv import load_dotenv
import requests
import google.generativeai as genai

load_dotenv()

app = Flask(__name__, static_url_path='', static_folder='.')

logging.basicConfig(level=logging.INFO)

DB_PATH    = os.environ.get('DB_PATH', '/tmp/tripsync.db')
GROQ_KEY   = os.environ.get('GROQ_API_KEY')
GROQ_URL   = "https://api.groq.com/openai/v1/chat/completions"
GROQ_MODEL = "llama-3.3-70b-versatile"
OLLAMA_URL = "http://localhost:11434/api/generate"
GEMINI_API_KEY = os.environ.get("GEMINI_API_KEY")
if GEMINI_API_KEY:
    genai.configure(api_key=GEMINI_API_KEY)

# --- Amadeus Configurations ---
AMADEUS_CLIENT_ID = os.environ.get("AMADEUS_CLIENT_ID")
AMADEUS_CLIENT_SECRET = os.environ.get("AMADEUS_CLIENT_SECRET")
AMADEUS_BASE_URL = "https://test.api.amadeus.com"

_amadeus_token = None
_amadeus_token_expires = 0  # timestamp

IATA_FALLBACKS = {
    "toronto": "YYZ", "tokyo": "NRT", "new york": "JFK", "london": "LHR", "paris": "CDG",
    "lisbon": "LIS", "rome": "FCO", "bangkok": "BKK", "singapore": "SIN", "barcelona": "BCN",
    "amsterdam": "AMS", "sydney": "SYD", "los angeles": "LAX", "chicago": "ORD",
    "miami": "MIA", "san francisco": "SFO", "vancouver": "YVR", "dubai": "DXB",
    "hong kong": "HKG", "munich": "MUC", "frankfurt": "FRA", "reykjavik": "KEF",
    "bali": "DPS", "denpasar": "DPS", "phuket": "HKT", "honolulu": "HNL", "cancun": "CUN"
}

AIRLINE_NAMES = {
    "AA": "American Airlines", "DL": "Delta Air Lines", "UA": "United Airlines",
    "LH": "Lufthansa", "BA": "British Airways", "AF": "Air France",
    "KL": "KLM", "EK": "Emirates", "QR": "Qatar Airways", "SQ": "Singapore Airlines",
    "CX": "Cathay Pacific", "AC": "Air Canada", "WS": "WestJet", "EI": "Aer Lingus",
    "IB": "Iberia", "AZ": "ITA Airways", "TK": "Turkish Airlines", "NH": "ANA",
    "JL": "Japan Airlines", "KE": "Korean Air", "QF": "Qantas", "NZ": "Air New Zealand",
    "B6": "JetBlue", "AS": "Alaska Airlines", "WN": "Southwest Airlines",
    "FR": "Ryanair", "U2": "EasyJet", "TP": "TAP Air Portugal", "LX": "Swiss"
}

# --- Database ---
def init_db():
    conn = sqlite3.connect(DB_PATH)
    c = conn.cursor()
    c.execute('''CREATE TABLE IF NOT EXISTS search_log (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        query TEXT, departure TEXT, currency TEXT,
        flight_class TEXT, hotel_rating TEXT,
        timestamp TEXT)''')
    c.execute('''CREATE TABLE IF NOT EXISTS click_log (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        destination TEXT, platform TEXT, project_name TEXT,
        timestamp INTEGER, created_at TEXT DEFAULT CURRENT_TIMESTAMP)''')
    c.execute('''CREATE TABLE IF NOT EXISTS flight_price_cache (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        origin TEXT,
        destination TEXT,
        departure_date TEXT,
        return_date TEXT,
        flight_class TEXT,
        currency TEXT,
        price_data TEXT,
        cached_at INTEGER)''')
    conn.commit()
    conn.close()

init_db()

# --- SQLite Cache Handlers ---
def get_cached_flight_price(origin, destination, dep_date, ret_date, flight_class, currency):
    try:
        conn = sqlite3.connect(DB_PATH)
        c = conn.cursor()
        c.execute("""
            SELECT price_data, cached_at FROM flight_price_cache 
            WHERE origin=? AND destination=? AND departure_date=? AND return_date=? AND flight_class=? AND currency=?
        """, (origin.lower(), destination.lower(), dep_date, ret_date or "", flight_class.lower(), currency.upper()))
        row = c.fetchone()
        conn.close()
        
        if row:
            price_data, cached_at = row
            # If less than 6 hours old (6 * 3600 = 21600 seconds)
            if time.time() - cached_at < 21600:
                return json.loads(price_data)
    except Exception as e:
        logging.error(f"Error checking cached flight price: {e}")
    return None

def cache_flight_price(origin, destination, dep_date, ret_date, flight_class, currency, data):
    try:
        conn = sqlite3.connect(DB_PATH)
        c = conn.cursor()
        # Delete any existing stale entry
        c.execute("""
            DELETE FROM flight_price_cache 
            WHERE origin=? AND destination=? AND departure_date=? AND return_date=? AND flight_class=? AND currency=?
        """, (origin.lower(), destination.lower(), dep_date, ret_date or "", flight_class.lower(), currency.upper()))
        
        # Insert new entry
        c.execute("""
            INSERT INTO flight_price_cache (origin, destination, departure_date, return_date, flight_class, currency, price_data, cached_at)
            VALUES (?, ?, ?, ?, ?, ?, ?, ?)
        """, (origin.lower(), destination.lower(), dep_date, ret_date or "", flight_class.lower(), currency.upper(), json.dumps(data), int(time.time())))
        conn.commit()
        conn.close()
    except Exception as e:
        logging.error(f"Error caching flight price: {e}")

# --- Amadeus OAuth ---
def get_amadeus_token():
    global _amadeus_token, _amadeus_token_expires
    if not AMADEUS_CLIENT_ID or not AMADEUS_CLIENT_SECRET:
        logging.warning("Amadeus Client ID or Secret not set")
        return None
    
    now = time.time()
    # If token exists and is not expired (with 10-second buffer)
    if _amadeus_token and now < _amadeus_token_expires - 10:
        return _amadeus_token
        
    url = f"{AMADEUS_BASE_URL}/v1/security/oauth2/token"
    headers = {"Content-Type": "application/x-www-form-urlencoded"}
    data = {
        "grant_type": "client_credentials",
        "client_id": AMADEUS_CLIENT_ID,
        "client_secret": AMADEUS_CLIENT_SECRET
    }
    
    try:
        resp = requests.post(url, headers=headers, data=data, timeout=10)
        if resp.status_code == 200:
            res_data = resp.json()
            _amadeus_token = res_data.get("access_token")
            expires_in = res_data.get("expires_in", 1799)
            _amadeus_token_expires = now + expires_in
            return _amadeus_token
        else:
            logging.error(f"Failed to get Amadeus token: {resp.status_code} {resp.text}")
    except Exception as e:
        logging.error(f"Error fetching Amadeus token: {e}")
        
    return None

# --- Amadeus IATA Resolver ---
def resolve_iata_code(keyword):
    token = get_amadeus_token()
    if not token:
        return None
        
    url = f"{AMADEUS_BASE_URL}/v1/reference-data/locations"
    headers = {"Authorization": f"Bearer {token}"}
    params = {
        "subType": "CITY",
        "keyword": keyword,
        "page[limit]": 1
    }
    
    try:
        resp = requests.get(url, headers=headers, params=params, timeout=10)
        if resp.status_code == 200:
            data = resp.json()
            if "data" in data and len(data["data"]) > 0:
                return data["data"][0].get("iataCode")
    except Exception as e:
        logging.error(f"Error resolving IATA for keyword {keyword}: {e}")
        
    return None

# --- Amadeus Flight Offers Search Client ---
def fetch_flight_price(origin_city, dest_city, departure_date, return_date=None, travel_class="ECONOMY", currency="USD"):
    # Resolve IATA codes
    origin_iata = IATA_FALLBACKS.get(origin_city.lower())
    if not origin_iata:
        origin_iata = resolve_iata_code(origin_city)
        
    dest_iata = IATA_FALLBACKS.get(dest_city.lower())
    if not dest_iata:
        dest_iata = resolve_iata_code(dest_city)
        
    if not origin_iata or not dest_iata:
        logging.warning(f"Could not resolve IATA for {origin_city} -> {dest_city}")
        return None
        
    token = get_amadeus_token()
    if not token:
        return None
        
    url = f"{AMADEUS_BASE_URL}/v2/shopping/flight-offers"
    headers = {"Authorization": f"Bearer {token}"}
    
    amadeus_class = "ECONOMY"
    if travel_class:
        tc = travel_class.upper().replace(" ", "_")
        if tc in ["ECONOMY", "PREMIUM_ECONOMY", "BUSINESS", "FIRST"]:
            amadeus_class = tc
            
    params = {
        "originLocationCode": origin_iata,
        "destinationLocationCode": dest_iata,
        "departureDate": departure_date,
        "adults": 1,
        "currencyCode": currency,
        "travelClass": amadeus_class,
        "max": 5
    }
    
    if return_date:
        params["returnDate"] = return_date
        
    try:
        resp = requests.get(url, headers=headers, params=params, timeout=12)
        if resp.status_code == 200:
            res_data = resp.json()
            if "data" in res_data and len(res_data["data"]) > 0:
                offers = res_data["data"]
                cheapest_offer = offers[0]
                price = cheapest_offer.get("price", {}).get("total")
                
                airline_code = None
                try:
                    itineraries = cheapest_offer.get("itineraries", [])
                    if itineraries:
                        segments = itineraries[0].get("segments", [])
                        if segments:
                            airline_code = segments[0].get("carrierCode")
                except:
                    pass
                    
                return {
                    "price": float(price) if price else None,
                    "airline_code": airline_code,
                    "currency": currency,
                    "origin_iata": origin_iata,
                    "dest_iata": dest_iata
                }
        else:
            logging.error(f"Amadeus Flight Offer Search failed: {resp.status_code} {resp.text}")
    except Exception as e:
        logging.error(f"Error calling Amadeus Flight Offer Search: {e}")
        
    return None


# --- JSON extractor (Enhanced) ---
def extract_json_safe(text):
    if not text: return None
    text = text.strip()
    
    # Remove markdown code blocks if present
    if "```" in text:
        for pattern in [r'```json\s*([\s\S]*?)\s*```', r'```\s*([\s\S]*?)\s*```']:
            m = re.search(pattern, text, re.DOTALL)
            if m:
                text = m.group(1).strip()
                break
    
    # Try direct load
    try: return json.loads(text)
    except: pass
    
    # Try to find first { and last }
    s, e = text.find('{'), text.rfind('}')
    if s != -1 and e > s:
        candidate = text[s:e+1]
        # Common fix: remove trailing commas before closing braces
        candidate = re.sub(r',\s*([\]}])', r'\1', candidate)
        try: return json.loads(candidate)
        except: pass
        
    return None

# --- Groq call with retry ---
def call_groq(prompt, max_tokens=2000):
    if not GROQ_KEY:
        logging.error("No GROQ_API_KEY found")
        return None
    for attempt in range(3):
        try:
            resp = requests.post(GROQ_URL,
                headers={"Authorization": f"Bearer {GROQ_KEY}", "Content-Type": "application/json"},
                json={"model": GROQ_MODEL,
                      "messages": [
                          {"role": "system", "content": "You are a travel expert. Respond with valid JSON only. No markdown, no preamble."},
                          {"role": "user", "content": prompt}],
                      "max_tokens": max_tokens, "temperature": 0.7},
                timeout=25)
            if resp.status_code == 200:
                return resp.json()['choices'][0]['message']['content']
        except Exception as e:
            logging.error(f"Groq attempt {attempt+1}: {e}")
        time.sleep(1)
    return None

# --- Ollama fallback (local only) ---
def call_ollama(prompt):
    for attempt in range(2):
        try:
            resp = requests.post(OLLAMA_URL,
                json={"model": "gemma4", "prompt": prompt, "stream": False,
                      "options": {"temperature": 0.5, "num_predict": 1500}},
                timeout=90)
            if resp.status_code == 200:
                return resp.json().get("response", "")
        except Exception as e:
            logging.error(f"Ollama attempt {attempt+1}: {e}")
        time.sleep(1)
    return None

# --- Gemma 4 API (Gemini REST) ---
def call_gemma_api(prompt):
    if not GEMINI_API_KEY:
        logging.error("No GEMINI_API_KEY found")
        return "Error: No GEMINI_API_KEY found"
    
    url = f"https://generativelanguage.googleapis.com/v1beta/models/gemma-4-26b-a4b-it:generateContent?key={GEMINI_API_KEY}"
    payload = {
        "contents": [{"parts": [{"text": prompt}]}],
        "generationConfig": {
            "temperature": 0.7,
            "maxOutputTokens": 2000
        }
    }
    
    try:
        # Reduced timeout to 15s to allow Groq fallback within Render's 30s limit
        resp = requests.post(url, json=payload, timeout=15)
        
        # INSTANT FALLBACK for Rate Limits (429) or Server Errors (502, 503)
        if resp.status_code in [429, 502, 503]:
            logging.warning(f"Gemma API returned {resp.status_code}. Triggering instant fallback to Groq.")
            return call_groq(prompt)
            
        if resp.status_code == 200:
            data = resp.json()
            if "candidates" in data and len(data["candidates"]) > 0:
                return data["candidates"][0]["content"]["parts"][0]["text"]
        
        # If we get any other non-200 code, still fallback as a safety measure
        logging.warning(f"Gemma API failed with code {resp.status_code}. Falling back to Groq.")
        return call_groq(prompt)
        
    except requests.exceptions.Timeout:
        logging.error("Gemma API timed out (25s limit). Falling back to Groq.")
        return call_groq(prompt)
    except Exception as e:
        logging.error(f"Gemma API connection error, falling back to Groq: {e}")
        return call_groq(prompt)

# --- Build destination search prompt ---
def build_prompt(query, depart_city="", currency="USD", check_in="", check_out="",
                 guests="2", budget="", flight_class="economy", hotel_rating="any",
                 amenities=None, car_type="none"):
    extra = ""
    if depart_city:    extra += f" Departing from: {depart_city}."
    if check_in:       extra += f" Dates: {check_in} to {check_out}."
    if guests:         extra += f" Travelers: {guests}."
    if budget:         extra += f" Budget: {budget}."
    if flight_class and flight_class != "economy":
        extra += f" Flight class: {flight_class}."
    if hotel_rating and hotel_rating != "any":
        extra += f" Hotel rating: {hotel_rating} stars minimum."
    if amenities:
        extra += f" Hotel amenities wanted: {', '.join(amenities)}."
    if car_type and car_type != "none":
        extra += f" Car rental needed: {car_type}."

    return f"""You are TripSync, a world-class AI travel curator. Your goal is to inspire and provide high-accuracy travel planning.
Return ONLY valid JSON, no extra text, no markdown.

User request: {query}{extra}

Return exactly 3 destination recommendations in this exact JSON format:
{{
  "destinations": [
    {{
      "city": "City Name",
      "country": "Country Name",
      "description": "A compelling 3-4 sentence narrative on why this is the perfect match. Focus on the 'vibe' and specific experiences.",
      "vibe_tags": ["#Tag1", "#Tag2", "#Tag3"],
      "match_score": "9.2/10",
      "best_season": "November to March",
      "budget_per_day": "X-Y {currency} per person",
      "flight_estimate": "X-Y {currency} return{' from ' + depart_city if depart_city else ''}",
      "flight_duration": "X-Y hours",
      "visa": "Visa requirements for most nationalities",
      "highlights": ["Iconic Activity", "Local Secret", "Food Experience", "Must-see Spot"],
      "smart_deal_insight": "One powerful sentence about timing or currency (e.g., 'Book 6 weeks out on a Tuesday for ~15% savings' or 'Switching to BRL currency may lower this fare').",
      "best_time_to_book": "6-8 weeks out",
      "flight_class": "{flight_class}",
      "hotel_rating": "{hotel_rating}"
    }}
  ]
}}

Pricing & Logistics Rules:
- All prices in {currency}.
- FLIGHT PRICING: 
  * If depart_city is '{depart_city}', calculate a realistic return flight price and duration from that specific city.
  * If the destination is on a different continent (e.g., North America to Asia), the flight_estimate MUST be {currency}1,200 - {currency}2,500+.
  * If depart_city is EMPTY or 'your city', set flight_estimate to "Set origin for price" and flight_duration to "Duration varies". DO NOT GUESS.
- Return ONLY JSON. No preamble, no markdown."""

# --- Routes ---
@app.route('/api/ping')
def ping():
    return jsonify({"status": "online", "timestamp": time.time()})

@app.route('/')
def index():
    return send_from_directory('.', 'index.html')

@app.route('/robots.txt')
def robots():
    return send_from_directory('.', 'robots.txt')

@app.route('/sitemap.xml')
def sitemap():
    return send_from_directory('.', 'sitemap.xml')

@app.route('/planner.html')
def planner():
    destination = request.args.get('destination', '').strip()
    days = request.args.get('days', '5').strip()
    
    try:
        with open('planner.html', 'r', encoding='utf-8') as f:
            content = f.read()
            
        if destination:
            title = f"{destination} {days}-Day Travel Itinerary — TripSync"
            desc = f"Explore a detailed {days}-day travel itinerary for {destination} on TripSync. View flight deals, recommended hotels, tours, transfers, and budgets."
            
            content = content.replace(
                '<title>Trip Planner — TripSync</title>',
                f'<title>{title}</title>'
            )
            content = content.replace(
                '<meta property="og:title" content="Trip Planner — TripSync">',
                f'<meta property="og:title" content="{title}">'
            )
            content = content.replace(
                '<meta property="twitter:title" content="Trip Planner — TripSync">',
                f'<meta property="twitter:title" content="{title}">'
            )
            content = content.replace(
                '<meta name="description" content="View your detailed travel itinerary, flight suggestions, hotels, and custom transfers on TripSync — the AI Travel Planner.">',
                f'<meta name="description" content="{desc}">'
            )
            content = content.replace(
                '<meta property="og:description" content="View your detailed travel itinerary, flight suggestions, hotels, and custom transfers on TripSync — the AI Travel Planner.">',
                f'<meta property="og:description" content="{desc}">'
            )
            content = content.replace(
                '<meta property="twitter:description" content="View your detailed travel itinerary, flight suggestions, hotels, and custom transfers on TripSync — the AI Travel Planner.">',
                f'<meta property="twitter:description" content="{desc}">'
            )
        return content
    except Exception as e:
        logging.error(f"Error pre-rendering dynamic planner metadata: {e}")
        
    return send_from_directory('.', 'planner.html')

@app.route('/manifest.json')
def manifest():
    return send_from_directory('.', 'manifest.json')

@app.route('/sw.js')
def sw():
    return send_from_directory('.', 'sw.js')

@app.route('/api/tripsync', methods=['POST'])
def tripsync():
    data = request.get_json()
    query       = data.get('query', '').strip()
    depart_city = data.get('departCity', data.get('departure', '')).strip()
    currency    = data.get('currency', 'USD')
    check_in    = data.get('checkIn', '')
    check_out   = data.get('checkOut', '')
    guests      = data.get('guests', '2')
    budget      = data.get('budget', '')
    flight_class= data.get('flightClass', 'economy')
    hotel_rating= data.get('hotelRating', 'any')
    amenities   = data.get('amenities', [])
    car_type    = data.get('carType', 'none')

    if not query:
        return jsonify({'error': 'No query provided'}), 400

    prompt = build_prompt(query, depart_city, currency, check_in, check_out,
                         guests, budget, flight_class, hotel_rating, amenities, car_type)

    result_text = call_groq(prompt)
    if not result_text:
        logging.info("Groq failed — trying Ollama")
        result_text = call_ollama(prompt)

    result = extract_json_safe(result_text) if result_text else None

    if not result or "destinations" not in result:
        return jsonify({'error': 'Could not generate destinations. Try again.'}), 500

    try:
        conn = sqlite3.connect(DB_PATH)
        c = conn.cursor()
        c.execute("INSERT INTO search_log (query,departure,currency,timestamp) VALUES (?,?,?,?)",
            (query, depart_city, currency, datetime.now().isoformat()))
        conn.commit()
        conn.close()
    except Exception as e:
        logging.error(f"DB log error: {e}")

    return jsonify(result)

@app.route('/api/tripsync-local', methods=['POST'])
def tripsync_local():
    data = request.get_json()
    query       = data.get('query', '').strip()
    depart_city = data.get('departCity', data.get('departure', '')).strip()
    currency    = data.get('currency', 'USD')
    check_in    = data.get('checkIn', '')
    check_out   = data.get('checkOut', '')
    guests      = data.get('guests', '2')
    budget      = data.get('budget', '')
    flight_class= data.get('flightClass', 'economy')
    hotel_rating= data.get('hotelRating', 'any')
    amenities   = data.get('amenities', [])
    car_type    = data.get('carType', 'none')

    if not query:
        return jsonify({'error': 'No query provided'}), 400

    prompt = build_prompt(query, depart_city, currency, check_in, check_out,
                         guests, budget, flight_class, hotel_rating, amenities, car_type)

    result_text = call_ollama(prompt)

    result = extract_json_safe(result_text) if result_text else None

    if not result or "destinations" not in result:
        return jsonify({'error': 'Local AI Mode requires TripSync to be run locally with Ollama (gemma4) installed. Switch to Cloud AI for immediate results, or <a href="https://github.com/Tripsync-justmeMedia/tripsync" target="_blank" style="text-decoration: underline; font-weight: bold; color: inherit;">see our GitHub for local instructions!</a>'}), 200

    try:
        conn = sqlite3.connect(DB_PATH)
        c = conn.cursor()
        c.execute("INSERT INTO search_log (query,departure,currency,timestamp) VALUES (?,?,?,?)",
            (query, depart_city, currency, datetime.now().isoformat()))
        conn.commit()
        conn.close()
    except Exception as e:
        logging.error(f"DB log error: {e}")

    return jsonify(result)

@app.route('/api/tripsync-gemma', methods=['POST'])
def tripsync_gemma():
    data = request.get_json()
    query       = data.get('query', '').strip()
    depart_city = data.get('departCity', data.get('departure', '')).strip()
    currency    = data.get('currency', 'USD')
    check_in    = data.get('checkIn', '')
    check_out   = data.get('checkOut', '')
    guests      = data.get('guests', '2')
    budget      = data.get('budget', '')
    flight_class= data.get('flightClass', 'economy')
    hotel_rating= data.get('hotelRating', 'any')
    amenities   = data.get('amenities', [])
    car_type    = data.get('carType', 'none')

    if not query:
        return jsonify({'error': 'No query provided'}), 400

    prompt = build_prompt(query, depart_city, currency, check_in, check_out,
                         guests, budget, flight_class, hotel_rating, amenities, car_type)

    result_text = call_gemma_api(prompt)
    if not result_text or result_text.startswith("Error:"):
        return jsonify({"error": f"Gemma API unavailable: {result_text}"}), 503

    result = extract_json_safe(result_text)
    if not result:
        logging.error(f"Failed to parse Gemma response: {result_text}")
        return jsonify({"error": f"Could not parse Gemma response: {result_text[:200]}..."}), 500
    
    # Ensure 'destinations' exists even if renamed
    if "destinations" not in result:
        for k in ["recommendations", "results", "trips", "data"]:
            if k in result:
                result["destinations"] = result[k]
                break
    
    if "destinations" not in result:
        return jsonify({"error": "Missing 'destinations' in response"}), 500

    try:
        conn = sqlite3.connect(DB_PATH)
        c = conn.cursor()
        c.execute("INSERT INTO search_log (query,departure,currency,timestamp) VALUES (?,?,?,?)",
            (query, depart_city, currency, datetime.now().isoformat()))
        conn.commit()
        conn.close()
    except Exception as e:
        logging.error(f"DB log error: {e}")

    resp = jsonify(result)
    resp.headers['X-AI-Mode'] = 'gemma'
    return resp

# --- Multi-stop route planner ---
@app.route('/api/multi-stop', methods=['POST'])
def multi_stop():
    data        = request.get_json()
    query       = data.get('query', '')
    depart_city = data.get('departCity', data.get('departure', '')).strip()
    currency    = data.get('currency', 'USD')

    if not depart_city:
        match = re.search(r'from\s+(\w+)', query.lower())
        depart_city = match.group(1).capitalize() if match else "your city"

    prompt = f"""Return ONLY valid JSON. No other text.
User wants this route: "{query}". Trip starts in {depart_city}. Currency: {currency}.

Create a realistic multi-stop flight itinerary with 5-8 legs.
Every city must be a REAL city name. Use REAL airline codes (AC, UA, DL, AA, BA, LH, EK, QR, SQ, TG, CX, NH, JL, KE).
The FIRST leg MUST depart from {depart_city}.

Pricing & Logistics Rules:
- All prices in {currency}.
- SMART INSIGHT: Provide one high-value "Smart Deal" tip for this specific multi-city route.

Return EXACTLY this structure:
{{
  "total_estimated_cost": 0,
  "route_savings": "0%",
  "smart_deal_insight": "...",
  "legs": [
    {{
      "origin": "city",
      "destination": "city",
      "flight_no": "AC123",
      "duration": "0h",
      "stay_duration": 0,
      "cost": 0
    }}
  ],
  "planning_tips": ["tip1", "tip2", "tip3", "tip4"]
}}"""

    result_text = call_groq(prompt, max_tokens=3000)
    result = extract_json_safe(result_text) if result_text else None
    if not result:
        return jsonify({"error": "Could not generate route. Please try again."}), 503
    return jsonify(result)

# --- Day-by-day itinerary generator ---
def build_itinerary_prompt(destination, days, currency, preferences='', flight_class='economy'):
    prompt = f"""Create a highly detailed {days}-day travel itinerary for {destination}.
Preferences: {preferences}. Currency: {currency}. Flight class: {flight_class}.

Return ONLY valid JSON:
{{
  "destination": "{destination}",
  "days": {days},
  "total_budget_estimate": "X-Y {currency}",
  "suggested_accommodation": [
    {{ "name": "Hotel Name", "type": "Luxury/Mid-range/Boutique", "reason": "Why this hotel?" }},
    {{ "name": "Hotel Name 2", "type": "Budget/Hostel", "reason": "Why this one?" }}
  ],
  "itinerary": [
    {{
      "day": 1,
      "title": "Arrival & City Vibe",
      "activities": ["Specific Activity 1", "Specific Activity 2", "Evening Experience"],
      "meals": {{ "breakfast": "Place Name", "lunch": "Place Name", "dinner": "Place Name" }},
      "daily_budget": "X-Y {currency}",
      "tips": ["Pro travel tip for this day"]
    }}
  ]
}}"""
    return prompt

@app.route('/api/generate-itinerary', methods=['POST'])
def generate_itinerary():
    data        = request.get_json()
    destination = data.get('destination', '')
    days        = data.get('days', 5)
    preferences = data.get('preferences', '')
    currency    = data.get('currency', 'USD')
    flight_class= data.get('flightClass', 'economy')

    prompt = build_itinerary_prompt(destination, days, currency, preferences, flight_class)

    result_text = call_groq(prompt, max_tokens=4000)
    if not result_text:
        return jsonify({"error": "Could not generate itinerary. Try again."}), 503
    result = extract_json_safe(result_text)
    if not result:
        return jsonify({"error": "Could not parse itinerary."}), 500
    return jsonify(result)

@app.route('/api/generate-itinerary-local', methods=['POST'])
def generate_itinerary_local():
    data = request.get_json()
    destination = data.get('destination', '')
    days = data.get('days', 5)
    currency = data.get('currency', 'USD')
    prompt = build_itinerary_prompt(destination, days, currency)
    result = call_ollama(prompt)
    if not result:
        return jsonify({"error": "Local AI Mode requires TripSync to be run locally with Ollama (gemma4) installed. Switch to Cloud AI for immediate results, or <a href=\"https://github.com/Tripsync-justmeMedia/tripsync\" target=\"_blank\" style=\"text-decoration: underline; font-weight: bold; color: inherit;\">see our GitHub for local instructions!</a>"}), 200
    parsed = extract_json_safe(result)
    if not parsed:
        return jsonify({"error": "Could not parse response"}), 500
    return jsonify(parsed)

@app.route('/api/generate-itinerary-gemma', methods=['POST'])
def generate_itinerary_gemma():
    data = request.get_json()
    destination = data.get('destination', '')
    days = data.get('days', 5)
    currency = data.get('currency', 'USD')
    prompt = build_itinerary_prompt(destination, days, currency)
    result_text = call_gemma_api(prompt)
    if not result_text or result_text.startswith("Error:"):
        return jsonify({"error": f"Gemma API unavailable: {result_text}"}), 503
    parsed = extract_json_safe(result_text)
    if not parsed:
        logging.error(f"Failed to parse Gemma itinerary: {result_text}")
        return jsonify({"error": f"Could not parse response: {result_text[:200]}..."}), 500
    
    resp = jsonify(parsed)
    resp.headers['X-AI-Mode'] = 'gemma'
    return resp

@app.route('/api/refine-itinerary', methods=['POST'])
def refine_itinerary():
    data = request.get_json()
    destination = data.get('destination', '')
    days = data.get('days', 5)
    currency = data.get('currency', 'USD')
    instruction = data.get('instruction', '')
    prompt = f"Refine the {days}-day travel itinerary for {destination} based on this instruction: '{instruction}'. Return ONLY valid JSON."
    result_text = call_groq(prompt, max_tokens=4000)
    result = extract_json_safe(result_text)
    return jsonify(result)

# --- Flight prices ---
@app.route('/api/flight-prices', methods=['POST'])
def get_flight_prices():
    data = request.get_json() or {}
    origin = data.get('origin', '').strip()
    destination = data.get('destination', '').strip()
    dep_date = data.get('departureDate', '').strip() # YYYY-MM-DD
    ret_date = data.get('returnDate', '').strip() # YYYY-MM-DD (optional)
    flight_class = data.get('flightClass', 'economy').strip()
    currency = data.get('currency', 'USD').strip()
    
    if not origin or not destination or not dep_date:
        return jsonify({"error": "Missing required fields (origin, destination, departureDate)"}), 400
        
    # Check cache first
    cached = get_cached_flight_price(origin, destination, dep_date, ret_date, flight_class, currency)
    if cached:
        logging.info(f"Returning cached flight price for {origin} -> {destination}")
        return jsonify(cached)
        
    # Fetch from Amadeus
    logging.info(f"Fetching fresh flight price for {origin} -> {destination}")
    fresh = fetch_flight_price(origin, destination, dep_date, ret_date, flight_class, currency)
    
    if fresh:
        airline_code = fresh.get("airline_code")
        airline_name = AIRLINE_NAMES.get(airline_code, airline_code or "Unknown Airline")
        fresh["airline_name"] = airline_name
        
        # Cache the result
        cache_flight_price(origin, destination, dep_date, ret_date, flight_class, currency, fresh)
        return jsonify(fresh)
        
    return jsonify({"error": "No flights found or API limits exceeded"}), 404

# --- Click tracking ---
@app.route('/api/track-click', methods=['POST'])
def track_click():
    data = request.get_json()
    try:
        conn = sqlite3.connect(DB_PATH)
        c = conn.cursor()
        c.execute("INSERT INTO click_log (destination,platform,project_name,timestamp) VALUES (?,?,?,?)",
            (data.get('destination',''), data.get('platform', data.get('link_type','')),
             data.get('project',''), data.get('timestamp', int(time.time()*1000))))
        conn.commit()
        conn.close()
        return jsonify({"ok": True})
    except Exception as e:
        return jsonify({"error": str(e)}), 500

# --- Stats ---
@app.route('/api/stats')
def stats():
    try:
        conn = sqlite3.connect(DB_PATH)
        c = conn.cursor()
        c.execute("SELECT COUNT(*) FROM search_log")
        searches = c.fetchone()[0]
        c.execute("SELECT platform, COUNT(*) as cnt FROM click_log GROUP BY platform ORDER BY cnt DESC")
        clicks = [{"platform": r[0], "count": r[1]} for r in c.fetchall()]
        c.execute("SELECT COUNT(*) FROM click_log")
        total_clicks = c.fetchone()[0]
        conn.close()
        return jsonify({"total_searches": searches, "total_clicks": total_clicks, "clicks_by_platform": clicks})
    except Exception as e:
        return jsonify({"error": str(e)}), 500

if __name__ == '__main__':
    port = int(os.environ.get("PORT", 5001))
    app.run(host='0.0.0.0', port=port, debug=False)
