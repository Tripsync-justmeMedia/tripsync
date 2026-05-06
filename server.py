import json
import os
import re
import sqlite3
import time
import requests
from flask import Flask, jsonify, request, send_from_directory
from dotenv import load_dotenv

load_dotenv()

app = Flask(__name__)

GROQ_KEY   = os.environ.get("GROQ_API_KEY")
GROQ_URL   = "https://api.groq.com/openai/v1/chat/completions"
GROQ_MODEL = "llama-3.3-70b-versatile"
OLLAMA_URL = "http://localhost:11434/api/generate"
DB_PATH    = os.environ.get("DB_PATH", "/tmp/tripsync.db")

def init_db():
    conn = sqlite3.connect(DB_PATH)
    c = conn.cursor()
    c.execute("""CREATE TABLE IF NOT EXISTS click_log (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        platform TEXT, destination TEXT, project_name TEXT,
        timestamp INTEGER, created_at TEXT DEFAULT CURRENT_TIMESTAMP)""")
    c.execute("""CREATE TABLE IF NOT EXISTS search_log (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        query TEXT, check_in TEXT, check_out TEXT, guests TEXT,
        budget TEXT, results_json TEXT, timestamp INTEGER,
        created_at TEXT DEFAULT CURRENT_TIMESTAMP)""")
    conn.commit()
    conn.close()

init_db()

def build_prompt(query, check_in="", check_out="", guests="2", budget="", depart_city=""):
    extra = ""
    if depart_city: extra += f" Departing from: {depart_city}."
    if check_in:    extra += f" Dates: {check_in} to {check_out}."
    if guests:      extra += f" Guests: {guests}."
    if budget:      extra += f" Budget: {budget}."
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
      "budget_per_day": "$80-$120 USD per person",
      "flight_estimate": "$650-$900 return",
      "flight_duration": "16-18 hours",
      "visa": "Visa on arrival for most nationalities",
      "highlights": ["Activity 1", "Activity 2", "Activity 3", "Activity 4"]
    }}
  ]
}}

Rules:
- Use the currency of the departure city if provided, otherwise USD
- Flight estimates from the departure city if provided
- Be specific with real price ranges
- highlights must be an array of 4-6 short strings
- Return ONLY the JSON object, nothing else, no backticks"""

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

def call_groq(prompt):
    for attempt in range(3):
        try:
            resp = requests.post(GROQ_URL,
                headers={"Authorization": f"Bearer {GROQ_KEY}", "Content-Type": "application/json"},
                json={"model": GROQ_MODEL,
                      "messages": [
                          {"role": "system", "content": "You are a travel expert. Respond with valid JSON only."},
                          {"role": "user", "content": prompt}],
                      "max_tokens": 2000, "temperature": 0.7},
                timeout=30)
            if resp.status_code == 200:
                content = resp.json()["choices"][0]["message"]["content"]
                parsed = extract_json_safe(content)
                if parsed: return parsed
        except Exception as e:
            print(f"[TripSync] Groq attempt {attempt+1}: {e}")
        time.sleep(1)
    return None

def call_ollama(prompt):
    for attempt in range(2):
        try:
            resp = requests.post(OLLAMA_URL,
                json={"model": "llama3.1:8b", "prompt": prompt, "stream": False,
                      "options": {"temperature": 0.5, "num_predict": 1500}},
                timeout=90)
            if resp.status_code == 200:
                raw = resp.json().get("response", "")
                parsed = extract_json_safe(raw)
                if parsed: return parsed
        except Exception as e:
            print(f"[TripSync] Ollama attempt {attempt+1}: {e}")
        time.sleep(1)
    return None

@app.route('/')
def index():
    return send_from_directory('.', 'index.html')

@app.route('/api/tripsync', methods=['POST'])
def tripsync_api():
    data = request.get_json()
    query      = data.get('query', '').strip()
    check_in   = data.get('checkIn', '')
    check_out  = data.get('checkOut', '')
    guests     = data.get('guests', '2')
    budget     = data.get('budget', '')
    depart_city= data.get('departCity', '')
    if not query:
        return jsonify({'error': 'No query provided'}), 400
    prompt = build_prompt(query, check_in, check_out, guests, budget, depart_city)
    result = call_groq(prompt)
    if not result:
        result = call_ollama(prompt)
    if not result or "destinations" not in result:
        return jsonify({'error': 'Could not generate destinations. Try again.'}), 500
    try:
        conn = sqlite3.connect(DB_PATH)
        c = conn.cursor()
        c.execute("INSERT INTO search_log (query,check_in,check_out,guests,budget,results_json,timestamp) VALUES (?,?,?,?,?,?,?)",
            (query, check_in, check_out, guests, budget, json.dumps(result), int(time.time()*1000)))
        conn.commit()
        conn.close()
    except Exception as e:
        print(f"[TripSync] DB error: {e}")
    return jsonify(result)

@app.route('/api/track-click', methods=['POST'])
def track_click():
    data = request.get_json()
    try:
        conn = sqlite3.connect(DB_PATH)
        c = conn.cursor()
        c.execute("INSERT INTO click_log (platform,destination,project_name,timestamp) VALUES (?,?,?,?)",
            (data.get('platform',''), data.get('destination',''), data.get('project',''), data.get('timestamp', int(time.time()*1000))))
        conn.commit()
        conn.close()
        return jsonify({"ok": True})
    except Exception as e:
        return jsonify({"error": str(e)}), 500

@app.route('/api/stats')
def stats():
    try:
        conn = sqlite3.connect(DB_PATH)
        c = conn.cursor()
        c.execute("SELECT platform, COUNT(*) as cnt FROM click_log GROUP BY platform ORDER BY cnt DESC")
        clicks = [{"platform": r[0], "count": r[1]} for r in c.fetchall()]
        c.execute("SELECT COUNT(*) FROM search_log")
        total = c.fetchone()[0]
        conn.close()
        return jsonify({"clicks": clicks, "total_searches": total})
    except Exception as e:
        return jsonify({"error": str(e)}), 500

if __name__ == "__main__":
    port = int(os.environ.get("PORT", 5001))
    app.run(host="0.0.0.0", port=port, debug=False)
