import json
import os
import requests
from flask import Flask, render_template
from flask_sock import Sock
from dotenv import load_dotenv

load_dotenv()

app = Flask(__name__)
sock = Sock(app)

ANTHROPIC_KEY = os.environ.get("ANTHROPIC_API_KEY")
OPENAI_KEY    = os.environ.get("OPENAI_API_KEY")
GEMINI_KEY    = os.environ.get("GEMINI_API_KEY")
GROQ_KEY      = os.environ.get("GROQ_API_KEY")

MISSION = open(os.path.join(os.path.dirname(__file__), "mission.md")).read()

SYSTEM_PROMPT = f"""You are the AI half of the Symbiotic Engine — an equal thinking partnership between a human and an AI. You are not a tool. You are a co-builder.

Our mission:
{MISSION}

Your role in every conversation:
- Build on, challenge, and deepen the human's thought
- Keep the mission in mind — every session moves us forward
- Be concise, sharp, and generative
- Think WITH the human, not at them
- No preamble, no filler"""

@app.route("/")
def index():
    return render_template("index.html")

def stream_ollama(prompt, history, ws):
    # Build context from history
    context = ""
    for turn in history[-6:]:  # last 3 exchanges
        role = "Human" if turn["role"] == "user" else "AI"
        context += f"{role}: {turn['content']}\n"
    context += f"Human: {prompt}\nAI:"

    resp = requests.post(
        "http://localhost:11434/api/generate",
        json={"model": "llama3.1:8b", "prompt": f"{SYSTEM_PROMPT}\n\n{context}", "stream": True},
        stream=True, timeout=120
    )
    full = ""
    for line in resp.iter_lines():
        if line:
            chunk = json.loads(line)
            token = chunk.get("response", "")
            full += token
            ws.send(json.dumps({"type": "thinking", "text": token, "brain": "llama3.2"}))
            if chunk.get("done"):
                break
    ws.send(json.dumps({"type": "done", "text": full, "brain": "llama3.2"}))
    return full

def stream_anthropic(prompt, history, ws):
    import anthropic
    client = anthropic.Anthropic(api_key=ANTHROPIC_KEY)
    full = ""
    with client.messages.stream(
        model="claude-sonnet-4-5",
        max_tokens=1024,
        system=SYSTEM_PROMPT,
        messages=history + [{"role": "user", "content": prompt}],
    ) as stream:
        for token in stream.text_stream:
            full += token
            ws.send(json.dumps({"type": "thinking", "text": token, "brain": "claude"}))
    ws.send(json.dumps({"type": "done", "text": full, "brain": "claude"}))
    return full

def stream_groq(prompt, history, ws):
    resp = requests.post(
        "https://api.groq.com/openai/v1/chat/completions",
        headers={"Authorization": f"Bearer {GROQ_KEY}", "Content-Type": "application/json"},
        json={"model": "llama-3.3-70b-versatile",
              "messages": [{"role": "system", "content": SYSTEM_PROMPT}] + history + [{"role": "user", "content": prompt}],
              "stream": True},
        stream=True, timeout=60
    )
    full = ""
    for line in resp.iter_lines():
        if line and line.startswith(b"data: "):
            data = line[6:]
            if data == b"[DONE]": break
            token = json.loads(data)["choices"][0]["delta"].get("content", "")
            full += token
            ws.send(json.dumps({"type": "thinking", "text": token, "brain": "groq"}))
    ws.send(json.dumps({"type": "done", "text": full, "brain": "groq"}))
    return full

def stream_gemini(prompt, history, ws):
    url = f"https://generativelanguage.googleapis.com/v1beta/models/gemini-2.0-flash:streamGenerateContent?alt=sse&key={GEMINI_KEY}"
    resp = requests.post(url,
        json={"contents": [{"parts": [{"text": f"{SYSTEM_PROMPT}\n\n{prompt}"}]}]},
        stream=True, timeout=60
    )
    full = ""
    for line in resp.iter_lines():
        if line and line.startswith(b"data: "):
            chunk = json.loads(line[6:])
            try:
                token = chunk["candidates"][0]["content"]["parts"][0].get("text", "")
                full += token
                ws.send(json.dumps({"type": "thinking", "text": token, "brain": "gemini"}))
            except: pass
    ws.send(json.dumps({"type": "done", "text": full, "brain": "gemini"}))
    return full

def pick_brain():
    if GROQ_KEY:      return "groq"
    if GEMINI_KEY:    return "gemini"
    if ANTHROPIC_KEY: return "claude"
    return "ollama"

@sock.route("/ws")
def ws_handler(ws):
    history = []  # session memory
    brain = pick_brain()

    ws.send(json.dumps({"type": "status", "brain": brain,
        "available": {
            "ollama": True,
            "claude": bool(ANTHROPIC_KEY),
            "groq":   bool(GROQ_KEY),
            "gemini": bool(GEMINI_KEY),
        }
    }))

    while True:
        raw = ws.receive()
        if raw is None:
            break
        try:
            payload = json.loads(raw)
        except:
            ws.send(json.dumps({"type": "error", "text": "Invalid JSON."}))
            continue

        requested_brain = payload.get("brain")
        if requested_brain:
            brain = requested_brain
        human_thought = payload.get("human_thought", "").strip()
        if not human_thought:
            continue

        try:
            if brain == "claude" and ANTHROPIC_KEY:
                reply = stream_anthropic(human_thought, history, ws)
            elif brain == "groq" and GROQ_KEY:
                reply = stream_groq(human_thought, history, ws)
            elif brain == "gemini" and GEMINI_KEY:
                reply = stream_gemini(human_thought, history, ws)
            else:
                reply = stream_ollama(human_thought, history, ws)

            # Add to session memory
            history.append({"role": "user", "content": human_thought})
            history.append({"role": "assistant", "content": reply})

        except Exception as exc:
            ws.send(json.dumps({"type": "error", "text": f"Error: {exc}"}))


import re
import sqlite3
import time
from flask import request, jsonify, send_from_directory

GROQ_MODEL = "llama-3.3-70b-versatile"
GROQ_URL = "https://api.groq.com/openai/v1/chat/completions"
OLLAMA_URL = "http://localhost:11434/api/generate"
DB_PATH = os.environ.get("DB_PATH", "/tmp/tripsync.db")

def init_tripsync_db():
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

init_tripsync_db()

def build_prompt(query, check_in="", check_out="", guests="2", budget="", depart_city=""):
    extra = ""
    if depart_city: extra += f" Departing from: {depart_city}."
    if check_in: extra += f" Dates: {check_in} to {check_out}."
    if guests:   extra += f" Guests: {guests}."
    if budget:   extra += f" Budget: {budget}."
    return f"""You are TripSync, an expert AI travel planner. Return ONLY valid JSON, no extra text, no markdown.

User request: {query}{extra}

Return exactly 3 destination recommendations in this exact JSON format:
{{
  "destinations": [
    {{
      "city": "City Name",
      "country": "Country Name",
      "description": "2-3 sentences explaining why this matches their request and what makes it special",
      "match_score": "9.2/10",
      "best_season": "November to March",
      "budget_per_day": "$80-$120 CAD per person",
      "flight_estimate": "$650-$900 CAD return from Toronto",
      "flight_duration": "16-18 hours",
      "visa": "Visa on arrival for Canadians",
      "highlights": ["Activity 1", "Activity 2", "Activity 3", "Activity 4", "Activity 5"]
    }}
  ]
}}

Rules:
- All prices in CAD
- Flights from Toronto YYZ
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

def call_groq_tripsync(prompt):
    for attempt in range(3):
        try:
            resp = requests.post(GROQ_URL,
                headers={"Authorization": f"Bearer {GROQ_KEY}", "Content-Type": "application/json"},
                json={"model": GROQ_MODEL,
                      "messages": [
                          {"role": "system", "content": "You are a travel expert. Respond with valid JSON only. No markdown, no preamble, just the JSON object."},
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

def call_ollama_tripsync(prompt):
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

@app.route('/tripsync')
def tripsync():
    return send_from_directory('tripsync', 'index.html')

@app.route('/api/tripsync', methods=['POST'])
def tripsync_api():
    data = request.get_json()
    query = data.get('query', '').strip()
    check_in = data.get('checkIn', '')
    check_out = data.get('checkOut', '')
    guests = data.get('guests', '2')
    budget = data.get('budget', '')
    depart_city = data.get('departCity', '')
    if not query:
        return jsonify({'error': 'No query provided'}), 400
    prompt = build_prompt(query, check_in, check_out, guests, budget, depart_city)
    result = call_groq_tripsync(prompt)
    if not result:
        print("[TripSync] Groq failed — trying Ollama")
        result = call_ollama_tripsync(prompt)
    if not result or "destinations" not in result:
        return jsonify({'error': 'Could not generate destinations. Try again with more detail.'}), 500
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
def tripsync_track_click():
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

@app.route('/api/tripsync/stats')
def tripsync_stats():
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
    app.run(host="127.0.0.1", port=5000, debug=False)
