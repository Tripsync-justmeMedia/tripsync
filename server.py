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

# Setup logging
logging.basicConfig(level=logging.INFO)

DB_PATH = os.environ.get('DB_PATH', '/tmp/tripsync.db')

def init_db():
    conn = sqlite3.connect(DB_PATH)
    c = conn.cursor()
    c.execute('''CREATE TABLE IF NOT EXISTS search_log
                 (id INTEGER PRIMARY KEY AUTOINCREMENT,
                  query TEXT,
                  timestamp TEXT,
                  departure TEXT,
                  currency TEXT)''')
    c.execute('''CREATE TABLE IF NOT EXISTS clicks
                 (id INTEGER PRIMARY KEY AUTOINCREMENT,
                  destination TEXT,
                  link_type TEXT,
                  timestamp TEXT)''')
    conn.commit()
    conn.close()

init_db()

def call_groq(prompt):
    api_key = os.environ.get('GROQ_API_KEY')
    if not api_key:
        return None
    headers = {
        "Authorization": f"Bearer {api_key}",
        "Content-Type": "application/json"
    }
    data = {
        "model": "llama-3.3-70b-versatile",
        "messages": [{"role": "user", "content": prompt}],
        "temperature": 0.3
    }
    try:
        response = requests.post("https://api.groq.com/openai/v1/chat/completions", headers=headers, json=data, timeout=30)
        if response.status_code == 200:
            return response.json()['choices'][0]['message']['content']
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
    
    prompt = f"""Return ONLY valid JSON. User wants: "{query}" from {departure}. Currency: {currency}.
    Structure: {{"destinations": [{{"city": "", "country": "", "description": "", "match_score": "9.2/10", "best_season": "", "budget_per_day": "CAD X-Y", "flight_estimate": "CAD X-Y return", "flight_duration": "X hours", "visa": "", "highlights": ["a","b","c","d","e"]}}]}}
    Return 3 destinations."""
    
    result = call_groq(prompt)
    if result:
        try:
            json_match = re.search(r'\{.*\}', result, re.DOTALL)
            if json_match:
                return jsonify(json.loads(json_match.group()))
        except:
            pass
    return jsonify({"destinations": []})

@app.route('/api/multi-stop', methods=['POST'])
def multi_stop():
    data = request.json
    query = data.get('query', '')
    departure = data.get('departure', 'Toronto')
    currency = data.get('currency', 'CAD')
    
    prompt = f"""Return ONLY valid JSON. User wants: "{query}"
    Departure: {departure}
    Currency: {currency}
    
    Structure:
    {{
      "total_estimated_cost_{currency}": 2850,
      "savings_vs_direct_percent": 42,
      "legs": [
        {{"from": "Toronto", "to": "Vancouver", "flight_number_example": "AC119", "duration_hours": 5, "estimated_cost_{currency}": 250, "stopover_days_suggested": 1, "booking_link": "https://www.skyscanner.com/transport/flights/toronto/vancouver/"}},
        {{"from": "Vancouver", "to": "Tokyo", "flight_number_example": "AC23", "duration_hours": 10, "estimated_cost_{currency}": 850, "stopover_days_suggested": 2, "booking_link": "https://www.skyscanner.com/transport/flights/vancouver/tokyo/"}},
        {{"from": "Tokyo", "to": "Bangkok", "flight_number_example": "TG661", "duration_hours": 7, "estimated_cost_{currency}": 320, "stopover_days_suggested": 0, "booking_link": "https://www.skyscanner.com/transport/flights/tokyo/bangkok/"}},
        {{"from": "Bangkok", "to": "Denpasar", "flight_number_example": "FD396", "duration_hours": 4, "estimated_cost_{currency}": 110, "stopover_days_suggested": 0, "booking_link": "https://www.skyscanner.com/transport/flights/bangkok/bali/"}},
        {{"from": "Denpasar", "to": "Taipei", "flight_number_example": "BR256", "duration_hours": 5, "estimated_cost_{currency}": 280, "stopover_days_suggested": 2, "booking_link": "https://www.skyscanner.com/transport/flights/bali/taipei/"}},
        {{"from": "Taipei", "to": "Los Angeles", "flight_number_example": "BR12", "duration_hours": 11, "estimated_cost_{currency}": 750, "stopover_days_suggested": 1, "booking_link": "https://www.skyscanner.com/transport/flights/taipei/losangeles/"}},
        {{"from": "Los Angeles", "to": "Toronto", "flight_number_example": "AC788", "duration_hours": 5, "estimated_cost_{currency}": 290, "stopover_days_suggested": 0, "booking_link": "https://www.skyscanner.com/transport/flights/losangeles/toronto/"}}
      ],
      "tips": [
        "Book this as 3 separate tickets for lowest price",
        "Use Zipair for Vancouver→Tokyo to save ~$300",
        "Taipei stopover: EVA Air offers free hotel",
        "All flights operate Jan-Apr 2027"
      ]
    }}
    Return ONLY valid JSON."""
    
    result = call_groq(prompt)
    if result:
        try:
            json_match = re.search(r'\{.*\}', result, re.DOTALL)
            if json_match:
                return jsonify(json.loads(json_match.group()))
        except:
            pass
    
    # Fallback response
    return jsonify({
        "total_estimated_cost_CAD": 2850,
        "savings_vs_direct_percent": 42,
        "legs": [
            {"from": departure, "to": "Vancouver", "flight_number_example": "AC119", "duration_hours": 5, "estimated_cost_CAD": 250, "stopover_days_suggested": 1, "booking_link": "https://www.skyscanner.com/"},
            {"from": "Vancouver", "to": "Tokyo", "flight_number_example": "AC23", "duration_hours": 10, "estimated_cost_CAD": 850, "stopover_days_suggested": 2, "booking_link": "https://www.skyscanner.com/"},
            {"from": "Tokyo", "to": "Bangkok", "flight_number_example": "TG661", "duration_hours": 7, "estimated_cost_CAD": 320, "stopover_days_suggested": 0, "booking_link": "https://www.skyscanner.com/"},
            {"from": "Bangkok", "to": "Denpasar", "flight_number_example": "FD396", "duration_hours": 4, "estimated_cost_CAD": 110, "stopover_days_suggested": 0, "booking_link": "https://www.skyscanner.com/"},
            {"from": "Denpasar", "to": "Taipei", "flight_number_example": "BR256", "duration_hours": 5, "estimated_cost_CAD": 280, "stopover_days_suggested": 2, "booking_link": "https://www.skyscanner.com/"},
            {"from": "Taipei", "to": "Los Angeles", "flight_number_example": "BR12", "duration_hours": 11, "estimated_cost_CAD": 750, "stopover_days_suggested": 1, "booking_link": "https://www.skyscanner.com/"},
            {"from": "Los Angeles", "to": "Toronto", "flight_number_example": "AC788", "duration_hours": 5, "estimated_cost_CAD": 290, "stopover_days_suggested": 0, "booking_link": "https://www.skyscanner.com/"}
        ],
        "tips": ["Book as 3 separate tickets", "Use Zipair for Pacific crossing", "Check EVA Air stopover deals"]
    })

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
