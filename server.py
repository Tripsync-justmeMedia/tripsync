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

load_dotenv()

app = Flask(__name__, static_url_path='', static_folder='.')

logging.basicConfig(level=logging.INFO)

DB_PATH    = os.environ.get('DB_PATH', '/tmp/tripsync.db')
GROQ_KEY   = os.environ.get('GROQ_API_KEY')
GROQ_URL   = "https://api.groq.com/openai/v1/chat/completions"
GROQ_MODEL = "llama-3.3-70b-versatile"
OLLAMA_URL = "http://localhost:11434/api/generate"

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

# --- JSON extractor (4 strategies) ---
def extract_json_safe(text):
    text = text.strip()
    try: return json.loads(text)
    except: pass
    for pattern in [r'\{[\s\S]*"destinations"[\s\S]*\}', r'```json\s*([\s\S]*?)\s*```', r'```\s*([\s\S]*?)\s*```']:
        m = re.search(pattern, text, re.DOTALL)
        if m:
            candidate = m.group(1) if m.lastindex else m.group(0)
            try: return json.loads(candidate.strip())
            except: continue
    s, e = text.find('{'), text.rfind('}')
    if s != -1 and e > s:
        try: return json.loads(text[s:e+1])
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
                json={"model": "llama3.1:8b", "prompt": prompt, "stream": False,
                      "options": {"temperature": 0.5, "num_predict": 1500}},
                timeout=90)
            if resp.status_code == 200:
                return resp.json().get("response", "")
        except Exception as e:
            logging.error(f"Ollama attempt {attempt+1}: {e}")
        time.sleep(1)
    return None

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

    return f"""You are TripSync, an expert AI travel planner. Return ONLY valid JSON, no extra text, no markdown.

User request: {query}{extra}

Return exactly 3 destination recommendations in this exact JSON format:
{{
  "destinations": [
    {{
      "city": "City Name",
      "country": "Country Name",
      "description": "2-3 sentences explaining why this matches their request",
      "match_score": "9.2/10",
      "best_season": "November to March",
      "budget_per_day": "X-Y {currency} per person",
      "flight_estimate": "X-Y {currency} return{' from ' + depart_city if depart_city else ''}",
      "flight_duration": "X-Y hours",
      "visa": "Visa requirements for most nationalities",
      "highlights": ["Activity 1", "Activity 2", "Activity 3", "Activity 4"],
      "flight_class": "{flight_class}",
      "hotel_rating": "{hotel_rating}"
    }}
  ]
}}

Rules:
- All prices in {currency}
- {('Flights from ' + depart_city) if depart_city else 'Include realistic flight estimates'}
- Be specific with real price ranges
- highlights must be an array of 4-6 short strings
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
        c.execute("INSERT INTO search_log (query,departure,currency,flight_class,hotel_rating,timestamp) VALUES (?,?,?,?,?,?)",
            (query, depart_city, currency, flight_class, hotel_rating, datetime.now().isoformat()))
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
@app.route('/api/generate-itinerary', methods=['POST'])
def generate_itinerary():
    data        = request.get_json()
    destination = data.get('destination', '')
    days        = data.get('days', 5)
    preferences = data.get('preferences', '')
    currency    = data.get('currency', 'USD')
    flight_class= data.get('flightClass', 'economy')

    prompt = f"""Create a {days}-day travel itinerary for {destination}.
Preferences: {preferences}. Currency: {currency}. Flight class: {flight_class}.

Return ONLY valid JSON:
{{
  "destination": "{destination}",
  "days": {days},
  "itinerary": [
    {{
      "day": 1,
      "title": "Arrival and Exploration",
      "activities": ["Activity 1", "Activity 2", "Activity 3"],
      "meals": ["Breakfast spot", "Lunch spot", "Dinner spot"],
      "tips": ["Local tip here"]
    }}
  ],
  "budget_estimate": "X-Y {currency} per day",
  "best_time_to_visit": "Months"
}}"""

    result_text = call_groq(prompt, max_tokens=4000)
    if not result_text:
        return jsonify({"error": "Could not generate itinerary. Try again."}), 503
    result = extract_json_safe(result_text)
    if not result:
        return jsonify({"error": "Could not parse itinerary."}), 500
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
