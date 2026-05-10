import os
import json
import sqlite3
import logging
from datetime import datetime
from flask import Flask, request, jsonify, send_from_directory
from flask_cors import CORS
import requests
import re

app = Flask(__name__, static_url_path='', static_folder='.')
CORS(app)

logging.basicConfig(level=logging.INFO)
DB_PATH = os.environ.get('DB_PATH', '/tmp/tripsync.db')

def init_db():
    conn = sqlite3.connect(DB_PATH)
    c = conn.cursor()
    c.execute('''CREATE TABLE IF NOT EXISTS search_log
                 (id INTEGER PRIMARY KEY AUTOINCREMENT,
                  query TEXT, timestamp TEXT, departure TEXT, currency TEXT)''')
    c.execute('''CREATE TABLE IF NOT EXISTS clicks
                 (id INTEGER PRIMARY KEY AUTOINCREMENT,
                  destination TEXT, link_type TEXT, timestamp TEXT)''')
    conn.commit()
    conn.close()

init_db()

def call_groq(prompt):
    api_key = os.environ.get('GROQ_API_KEY')
    if not api_key:
        logging.error("No GROQ_API_KEY found")
        return None
    headers = {"Authorization": f"Bearer {api_key}", "Content-Type": "application/json"}
    data = {
        "model": "llama-3.3-70b-versatile",
        "messages": [{"role": "user", "content": prompt}],
        "temperature": 0.3
    }
    try:
        response = requests.post("https://api.groq.com/openai/v1/chat/completions", headers=headers, json=data, timeout=30)
        if response.status_code == 200:
            return response.json()['choices'][0]['message']['content']
        else:
            logging.error(f"Groq API error: {response.status_code}")
    except Exception as e:
        logging.error(f"Groq error: {e}")
    return None

@app.route('/')
def index():
    return send_from_directory('.', 'index.html')

@app.route('/api/tripsync', methods=['POST'])
def tripsync():
    data = request.json
    query = data.get('query', '')
    departure = data.get('departure', 'Toronto')
    currency = data.get('currency', 'CAD')
    
    prompt = f"""Return ONLY valid JSON. No other text. User wants: "{query}" from {departure}. Currency: {currency}.
    Structure: {{"destinations": [{{"city": "", "country": "", "description": "", "match_score": "9.2/10", "best_season": "", "budget_per_day": "CAD X-Y", "flight_estimate": "CAD X-Y return", "flight_duration": "X hours", "visa": "", "highlights": ["a","b","c","d","e"]}}]}}
    Return 3 destinations."""
    
    result = call_groq(prompt)
    if result:
        try:
            json_match = re.search(r'\{.*\}', result, re.DOTALL)
            if json_match:
                return jsonify(json.loads(json_match.group()))
        except Exception as e:
            logging.error(f"JSON parse error: {e}")
    
    return jsonify({"destinations": [], "error": "AI temporarily unavailable"})

@app.route('/api/multi-stop', methods=['POST'])
def multi_stop():
    data = request.json
    query = data.get('query', '')
    departure = data.get('departure', '')
    currency = data.get('currency', 'CAD')
    
    # Extract the starting city from the query if departure is empty
    if not departure or departure == '':
        import re
        match = re.search(r'from\s+(\w+)', query.lower())
        if match:
            departure = match.group(1).capitalize()
        else:
            departure = "your departure city"
    
    prompt = f"""Return ONLY valid JSON. No other text. User wants this exact route: "{query}"
    
    IMPORTANT: The trip starts in {departure}. The FIRST leg MUST depart from {departure}.
    Do NOT add Toronto or any other city unless the user specified it.
    
    Create a realistic multi-stop flight itinerary with 5-8 legs.
    Use REAL airline codes (AC, UA, DL, AA, BA, LH, AF, KL, EK, QR, SQ, TG, CX, NH, JL, KE).
    
    Return EXACTLY this structure:
    {{
      "total_estimated_cost_{currency}": number,
      "savings_vs_direct_percent": number,
      "legs": [
        {{
          "from": "city name",
          "to": "city name", 
          "flight_number_example": "XX123",
          "duration_hours": number,
          "estimated_cost_{currency}": number,
          "stopover_days_suggested": number,
          "booking_link": "https://www.skyscanner.com/transport/flights/city1/city2/"
        }}
      ],
      "tips": ["tip1", "tip2", "tip3", "tip4"]
    }}
    
    Make sure the route makes geographic sense. The last leg should end where the user wants to finish."""
    
    result = call_groq(prompt)
    if result:
        try:
            json_match = re.search(r'\{.*\}', result, re.DOTALL)
            if json_match:
                return jsonify(json.loads(json_match.group()))
        except Exception as e:
            logging.error(f"JSON parse error: {e}")
            return jsonify({"error": f"AI response invalid: {str(e)}", "raw": result[:500]}), 500
    
    return jsonify({"error": "AI could not generate route. Please try again."}), 503

@app.route('/api/track-click', methods=['POST'])
def track_click():
    data = request.json
    conn = sqlite3.connect(DB_PATH)
    c = conn.cursor()
    c.execute("INSERT INTO clicks (destination, link_type, timestamp) VALUES (?, ?, ?)",
              (data.get('destination'), data.get('link_type'), datetime.now().isoformat()))
    conn.commit()
    conn.close()
    return jsonify({"status": "ok"})

@app.route('/api/stats', methods=['GET'])
def stats():
    conn = sqlite3.connect(DB_PATH)
    c = conn.cursor()
    c.execute("SELECT COUNT(*) FROM search_log")
    searches = c.fetchone()[0]
    c.execute("SELECT COUNT(*) FROM clicks")
    clicks = c.fetchone()[0]
    conn.close()
    return jsonify({"searches": searches, "clicks": clicks})

if __name__ == '__main__':
    app.run(host='0.0.0.0', port=5001, debug=True)
