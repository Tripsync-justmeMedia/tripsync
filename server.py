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
    conn.commit()
    conn.close()

init_db()

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
                timeout=30)
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
                timeout=300)
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
        resp = requests.post(url, json=payload, timeout=25) # Short timeout for faster fallback
        if resp.status_code == 200:
            data = resp.json()
            if "candidates" in data and len(data["candidates"]) > 0:
                return data["candidates"][0]["content"]["parts"][0]["text"]
        
        # If we get here, it failed. Silent fallback to Groq!
        logging.warning("Gemma API failed, falling back to Groq for competition reliability.")
        return call_groq(prompt)
        
    except Exception as e:
        logging.error(f"Gemma API error, falling back to Groq: {e}")
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
      "flight_class": "{flight_class}",
      "hotel_rating": "{hotel_rating}"
    }}
  ]
}}

Rules:
- All prices in {currency}
- {('Flights from ' + depart_city) if depart_city else 'Include realistic flight estimates'}
- Be specific with real price ranges
- highlights must be an array of exactly 4 short, evocative strings
- vibe_tags must be an array of 3 hashtags starting with #
- Return ONLY the JSON object, nothing else"""

# --- Routes ---
@app.route('/')
def index():
    return send_from_directory('.', 'index.html')

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

    return jsonify(result)

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

Return EXACTLY this structure:
{{
  "total_estimated_cost_{currency}": 0,
  "savings_vs_direct_percent": 0,
  "legs": [
    {{
      "from": "city",
      "to": "city",
      "flight_number_example": "AC123",
      "duration_hours": 0,
      "estimated_cost_{currency}": 0,
      "stopover_days_suggested": 0,
      "booking_link": "https://www.google.com/travel/flights?q=Flights+from+city1+to+city2"
    }}
  ],
  "tips": ["tip1", "tip2", "tip3", "tip4"]
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
    return jsonify(parsed)

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
