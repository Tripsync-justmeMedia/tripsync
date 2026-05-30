import os
import json
import sqlite3
import logging
import re
import time
import hashlib
import random
import smtplib
from email.mime.multipart import MIMEMultipart
from email.mime.text import MIMEText
from datetime import datetime
from flask import Flask, request, jsonify, send_from_directory, make_response
from dotenv import load_dotenv
import requests
import google.generativeai as genai
from sheets import sheets_helper

load_dotenv()

BASE_URL = os.environ.get("BASE_URL", "https://tripsync.ca")

from flask_limiter import Limiter
from flask_limiter.util import get_remote_address

app = Flask(__name__, static_url_path='', static_folder='.')

limiter = Limiter(
    get_remote_address,
    app=app,
    default_limits=[],
    storage_uri="memory://"
)

@app.errorhandler(429)
def ratelimit_handler(e):
    return jsonify({"error": "Too many requests. Please wait a moment and try again."}), 429

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

INFLUENCER_IPS = {}

def send_smtp_email(to_email, subject, html_content):
    smtp_user = os.environ.get('SMTP_USER', 'william@justmemedia.ca')
    smtp_password = (os.environ.get('SMTP_APP_PASSWORD') or os.environ.get('GMAIL_APP_PASSWORD') or '').replace(" ", "")
    
    if not smtp_password:
        logging.warning("SMTP App Password is not configured. Email notification skipped.")
        return False
        
    try:
        msg = MIMEMultipart('alternative')
        msg['Subject'] = subject
        msg['From'] = f"TripSync <{smtp_user}>"
        msg['To'] = to_email
        
        part = MIMEText(html_content, 'html')
        msg.attach(part)
        
        server = smtplib.SMTP('smtp.gmail.com', 587)
        server.starttls()
        server.login(smtp_user, smtp_password)
        server.sendmail(smtp_user, to_email, msg.as_string())
        server.quit()
        logging.info(f"Successfully sent email to {to_email} with subject: {subject}")
        return True
    except Exception as e:
        logging.error(f"Failed to send SMTP email: {e}")
        return False

def send_registration_emails(influencer_email, display_name, handle, pin):
    # Email to Influencer
    subject_influencer = "Welcome to the TripSync Influencer Family! 🎉"
    html_influencer = f"""
    <html>
      <body style="font-family: 'DM Sans', Arial, sans-serif; background-color: #faf9f6; color: #1a1a1a; padding: 20px; line-height: 1.6;">
        <div style="max-width: 600px; margin: 0 auto; background: white; border: 1px solid #f4f1ea; border-radius: 12px; padding: 30px; box-shadow: 0 4px 20px rgba(0,0,0,0.03);">
          <h2 style="font-family: 'Playfair Display', serif; color: #1a6b6b; font-size: 24px; margin-bottom: 10px;">Welcome to TripSync, {display_name}!</h2>
          <p>We are thrilled to welcome you to our zero-friction, auto-approved influencer partner program. Your profile is <strong>live instantly</strong> and ready to generate revenue.</p>
          
          <hr style="border: none; border-top: 1px solid #f4f1ea; margin: 20px 0;">
          
          <div style="background-color: #eaf4f4; border-radius: 8px; padding: 15px; margin-bottom: 20px;">
            <p style="margin: 0; font-size: 14px; font-weight: bold; color: #1a6b6b; text-transform: uppercase; letter-spacing: 1px;">Your Referral Public Page</p>
            <p style="margin: 5px 0 0; font-size: 18px; font-family: monospace; font-weight: bold;"><a href="{BASE_URL}/@{handle}" style="color: #1a6b6b; text-decoration: none;">{BASE_URL}/@{handle}</a></p>
          </div>
          
          <div style="background-color: #faf9f6; border-radius: 8px; padding: 15px; margin-bottom: 20px; border: 1px solid #f4f1ea;">
            <p style="margin: 0; font-size: 14px; font-weight: bold; color: #666; text-transform: uppercase; letter-spacing: 1px;">Access Your Private Dashboard</p>
            <p style="margin: 5px 0 0; font-size: 15px;">Dashboard URL: <a href="{BASE_URL}/dashboard.html?handle={handle}" style="color: #1a6b6b; font-weight: bold;">dashboard.html?handle={handle}</a></p>
            <p style="margin: 5px 0 0; font-size: 15px;">Your 4-Digit Login PIN: <strong style="font-size: 16px; letter-spacing: 2px;">{pin}</strong></p>
          </div>
          
          <hr style="border: none; border-top: 1px solid #f4f1ea; margin: 20px 0;">
          
          <h3 style="color: #1a6b6b; font-size: 16px; margin-bottom: 10px;">Signed Electronic Agreement Summary:</h3>
          <div style="font-size: 12px; color: #666; background: #faf9f6; padding: 15px; border-radius: 8px; border: 1px solid #f4f1ea; max-height: 180px; overflow-y: auto;">
            <strong>1. Responsibility of Offers:</strong> The influencer is completely responsible for the validity, accuracy, and expiration timelines of all custom deals, promo codes, and text descriptions they post.<br><br>
            <strong>2. TripSync Indemnity:</strong> TripSync is a free travel planner and is not liable for false, expired, or invalid hotel, flight, or tour offers posted by partners.<br><br>
            <strong>3. Commission Split:</strong> TripSync splits all net commissions earned from referenced bookings 50/50 with the referring influencer.<br><br>
            <strong>4. Payment Timeline:</strong> Commissions are manual payouts generated 30-90 days following a completed booking (when TripSync receives commissions from partners). TripSync only pays commissions actually received.<br><br>
            <strong>5. Minimum Payout:</strong> Payout requests require a minimum balance of $50 USD.
          </div>
          
          <p style="font-size: 13px; color: #888; margin-top: 25px; text-align: center;">
            &copy; 2026 TripSync by Just Me Media &middot; william@justmemedi.ca
          </p>
        </div>
      </body>
    </html>
    """
    
    send_smtp_email(influencer_email, subject_influencer, html_influencer)
    
    # Email to William (Admin Alert)
    subject_admin = f"🚨 New Influencer Registered: @{handle}"
    html_admin = f"""
    <html>
      <body style="font-family: Arial, sans-serif; background-color: #faf9f6; color: #1a1a1a; padding: 20px; line-height: 1.6;">
        <div style="max-width: 600px; margin: 0 auto; background: white; border: 1px solid #f4f1ea; border-radius: 12px; padding: 30px;">
          <h2 style="color: #c25e4d; font-size: 22px; margin-bottom: 10px;">New Influencer Registration Alert</h2>
          <p>A new influencer partner has joined TripSync. The profile has been auto-approved and recorded in Google Sheets.</p>
          
          <hr style="border: none; border-top: 1px solid #f4f1ea; margin: 20px 0;">
          
          <table style="width: 100%; border-collapse: collapse; font-size: 14px;">
            <tr>
              <td style="padding: 8px 0; font-weight: bold; color: #1a6b6b; width: 150px;">Display Name:</td>
              <td style="padding: 8px 0;">{display_name}</td>
            </tr>
            <tr>
              <td style="padding: 8px 0; font-weight: bold; color: #1a6b6b;">Handle:</td>
              <td style="padding: 8px 0;"><a href="{BASE_URL}/@{handle}" style="color: #1a6b6b; font-weight: bold;">@{handle}</a></td>
            </tr>
            <tr>
              <td style="padding: 8px 0; font-weight: bold; color: #1a6b6b;">Email:</td>
              <td style="padding: 8px 0;"><a href="mailto:{influencer_email}" style="color: #1a6b6b;">{influencer_email}</a></td>
            </tr>
          </table>
          
          <hr style="border: none; border-top: 1px solid #f4f1ea; margin: 20px 0;">
          <p style="font-size: 13px; color: #666;">This is an automated operational alert from your TripSync backend system.</p>
        </div>
      </body>
    </html>
    """
    
    send_smtp_email("william@justmemedi.ca", subject_admin, html_admin)

# --- Database ---
def get_db_connection():
    db_url = os.environ.get('DATABASE_URL')
    if db_url:
        try:
            import psycopg2
            if db_url.startswith("postgres://"):
                db_url = db_url.replace("postgres://", "postgresql://", 1)
            return psycopg2.connect(db_url), True
        except ImportError:
            logging.error("DATABASE_URL is set but psycopg2 is not installed. Falling back to SQLite.")
        except Exception as e:
            logging.error(f"PostgreSQL connection failed: {e}. Falling back to SQLite.")
    return sqlite3.connect(DB_PATH), False

def init_db():
    try:
        conn, is_pg = get_db_connection()
        c = conn.cursor()
        if is_pg:
            c.execute('''CREATE TABLE IF NOT EXISTS search_log (
                id SERIAL PRIMARY KEY,
                query TEXT, departure TEXT, currency TEXT,
                flight_class TEXT, hotel_rating TEXT,
                timestamp TEXT)''')
            c.execute('''CREATE TABLE IF NOT EXISTS click_log (
                id SERIAL PRIMARY KEY,
                destination TEXT, platform TEXT, project_name TEXT,
                timestamp BIGINT, created_at TIMESTAMPTZ DEFAULT CURRENT_TIMESTAMP)''')
            c.execute('''CREATE TABLE IF NOT EXISTS flight_price_cache (
                id SERIAL PRIMARY KEY,
                origin TEXT,
                destination TEXT,
                departure_date TEXT,
                return_date TEXT,
                flight_class TEXT,
                currency TEXT,
                price_data TEXT,
                cached_at BIGINT)''')
        else:
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
    except Exception as e:
        logging.error(f"Error initializing DB: {e}")

init_db()

# --- SQLite Cache Handlers ---
def get_cached_flight_price(origin, destination, dep_date, ret_date, flight_class, currency):
    try:
        conn, is_pg = get_db_connection()
        c = conn.cursor()
        query = """
            SELECT price_data, cached_at FROM flight_price_cache 
            WHERE origin=? AND destination=? AND departure_date=? AND return_date=? AND flight_class=? AND currency=?
        """
        if is_pg:
            query = query.replace('?', '%s')
        c.execute(query, (origin.lower(), destination.lower(), dep_date, ret_date or "", flight_class.lower(), currency.upper()))
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
        conn, is_pg = get_db_connection()
        c = conn.cursor()
        # Delete any existing stale entry
        query_delete = """
            DELETE FROM flight_price_cache 
            WHERE origin=? AND destination=? AND departure_date=? AND return_date=? AND flight_class=? AND currency=?
        """
        if is_pg:
            query_delete = query_delete.replace('?', '%s')
        c.execute(query_delete, (origin.lower(), destination.lower(), dep_date, ret_date or "", flight_class.lower(), currency.upper()))
        
        # Insert new entry
        query_insert = """
            INSERT INTO flight_price_cache (origin, destination, departure_date, return_date, flight_class, currency, price_data, cached_at)
            VALUES (?, ?, ?, ?, ?, ?, ?, ?)
        """
        if is_pg:
            query_insert = query_insert.replace('?', '%s')
        c.execute(query_insert, (origin.lower(), destination.lower(), dep_date, ret_date or "", flight_class.lower(), currency.upper(), json.dumps(data), int(time.time())))
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
UNSPLASH_ACCESS_KEY = os.environ.get('UNSPLASH_ACCESS_KEY')

def get_fallback_image(query):
    query_lower = query.lower()
    
    # Category mappings with beautiful, high-res Unsplash stock photos
    if any(k in query_lower for k in ['beach', 'tropical', 'cancun', 'caribbean', 'hawaii', 'maldives', 'island', 'coast', 'sea', 'ocean', 'bahamas', 'phuket', 'bali']):
        return 'https://images.unsplash.com/photo-1507525428034-b723cf961d3e?auto=format&fit=crop&w=1600&q=80'
    elif any(k in query_lower for k in ['tokyo', 'new york', 'london', 'paris', 'city', 'urban', 'skyline', 'chicago', 'seattle', 'metropolis', 'singapore', 'hong kong', 'toronto']):
        return 'https://images.unsplash.com/photo-1477959858617-67f85cf4f1df?auto=format&fit=crop&w=1600&q=80'
    elif any(k in query_lower for k in ['mountain', 'hiking', 'nature', 'swiss', 'alps', 'park', 'forest', 'national park', 'lake', 'rocky', 'canada', 'banff', 'greenery']):
        return 'https://images.unsplash.com/photo-1464822759023-fed622ff2c3b?auto=format&fit=crop&w=1600&q=80'
    elif any(k in query_lower for k in ['snow', 'ski', 'winter', 'ice', 'glacier', 'lapland', 'finland', 'cabin', 'iceland', 'aurora', 'norway']):
        return 'https://images.unsplash.com/photo-1482862549707-f63cb32c5fd9?auto=format&fit=crop&w=1600&q=80'
    elif any(k in query_lower for k in ['europe', 'historic', 'culture', 'rome', 'temple', 'ancient', 'museum', 'castle', 'ruins', 'greece', 'athens', 'egypt', 'kyoto', 'heritage']):
        return 'https://images.unsplash.com/photo-1485088412644-d07c37c2299b?auto=format&fit=crop&w=1600&q=80'
        
    # Default travel boat on lake
    return 'https://images.unsplash.com/photo-1476514525535-07fb3b4ae5f1?auto=format&fit=crop&w=1600&q=80'

@app.route('/api/destination-image')
def destination_image():
    query = request.args.get('query', '').strip()
    if not query:
        return jsonify({"url": 'https://images.unsplash.com/photo-1476514525535-07fb3b4ae5f1?auto=format&fit=crop&w=1600&q=80'})
        
    if not UNSPLASH_ACCESS_KEY:
        # Fallback to local curated categorizer
        return jsonify({"url": get_fallback_image(query)})
        
    # Unsplash search API URL
    url = "https://api.unsplash.com/search/photos"
    params = {
        "query": query,
        "client_id": UNSPLASH_ACCESS_KEY,
        "orientation": "landscape",
        "per_page": 1
    }
    
    try:
        resp = requests.get(url, params=params, timeout=5)
        if resp.status_code == 200:
            data = resp.json()
            if data.get('results') and len(data['results']) > 0:
                raw_url = data['results'][0]['urls']['raw']
                formatted_url = f"{raw_url}&auto=format&fit=crop&w=1600&q=80"
                return jsonify({"url": formatted_url})
        logging.warning(f"Unsplash API call failed with code {resp.status_code}. Using fallback.")
    except Exception as e:
        logging.error(f"Error calling Unsplash API: {e}")
        
    return jsonify({"url": get_fallback_image(query)})

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
            import urllib.parse
            quoted_dest = urllib.parse.quote(destination)
            full_url = f"{BASE_URL}/planner.html?destination={quoted_dest}&days={days}"
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
            content = content.replace(
                f'<meta property="og:url" content="{BASE_URL}/planner.html">',
                f'<meta property="og:url" content="{full_url}">'
            )
        return content
    except Exception as e:
        logging.error(f"Error pre-rendering dynamic planner metadata: {e}")
        
    return send_from_directory('.', 'planner.html')

@app.route('/affiliate')
def serve_affiliate():
    return send_from_directory('.', 'affiliate.html')

@app.route('/dashboard')
def serve_dashboard_clean():
    return send_from_directory('.', 'dashboard.html')

@app.route('/@<handle>')
def serve_influencer_profile(handle):
    return send_from_directory('.', 'handle.html')

@app.route('/api/affiliate/register', methods=['POST'])
def affiliate_register():
    data = request.get_json() or {}
    handle = data.get('handle', '').strip().lower()
    email = data.get('email', '').strip()
    display_name = data.get('display_name', '').strip()
    payment_method = data.get('payment_method', '').strip()
    payment_account = data.get('payment_account', '').strip()
    pin = data.get('pin', '').strip()
    social_instagram = data.get('social_instagram', '').strip()
    social_tiktok = data.get('social_tiktok', '').strip()

    if not handle or not email or not display_name or not payment_method or not payment_account or not pin:
        return jsonify({'error': 'Missing required registration fields'}), 400

    if not re.match(r'^[a-zA-Z0-9_]+$', handle):
        return jsonify({'error': 'Handle must contain only letters, numbers, and underscores'}), 400

    if len(pin) != 4 or not pin.isdigit():
        return jsonify({'error': 'PIN must be exactly 4 digits'}), 400

    pin_hash = hashlib.sha256(pin.encode('utf-8')).hexdigest()

    success, msg = sheets_helper.register_influencer(
        handle=handle,
        email=email,
        display_name=display_name,
        payment_method=payment_method,
        payment_account=payment_account,
        pin_hash=pin_hash,
        social_instagram=social_instagram,
        social_tiktok=social_tiktok
    )

    if not success:
        return jsonify({'error': msg}), 400

    # Trigger transactional SMTP emails safely
    send_registration_emails(email, display_name, handle, pin)

    return jsonify({'success': True, 'message': 'Registration successful and auto-approved!'})

@app.route('/api/affiliate/dashboard/<handle>', methods=['GET'])
def affiliate_dashboard(handle):
    handle = handle.strip().lower()
    pin = request.args.get('pin', '').strip()

    if not pin:
        return jsonify({'error': 'PIN is required to unlock the dashboard'}), 401

    influencer = sheets_helper.get_influencer(handle)
    if not influencer:
        return jsonify({'error': 'Influencer profile not found'}), 404

    pin_hash = hashlib.sha256(pin.encode('utf-8')).hexdigest()
    stored_hash = str(influencer.get('pin_hash', ''))
    if pin_hash != stored_hash:
        return jsonify({'error': 'Incorrect 4-digit PIN code'}), 401

    # Record/cache influencer IP to exclude self-clicks
    ip = request.headers.get('X-Forwarded-For', request.remote_addr)
    if ip:
        client_ip = ip.split(',')[0].strip()
        INFLUENCER_IPS[handle] = client_ip
        logging.info(f"Registered session IP for influencer @{handle}: {client_ip}")

    deals = sheets_helper.get_influencer_deals(handle)

    return jsonify({
        'affiliate': {
            'handle': influencer.get('handle'),
            'display_name': influencer.get('display_name'),
            'bio': influencer.get('bio'),
            'profile_image': influencer.get('profile_image'),
            'total_clicks': influencer.get('total_clicks', 0),
            'total_bookings': influencer.get('total_bookings', 0),
            'total_earned': influencer.get('total_earned', 0.0),
            'paid_earned': influencer.get('paid_earned', 0.0),
            'pending_earned': influencer.get('pending_earned', 0.0)
        },
        'deals': deals
    })

@app.route('/api/affiliate/update-deal', methods=['POST'])
def affiliate_update_deal():
    data = request.get_json() or {}
    handle = data.get('handle', '').strip().lower()
    pin = data.get('pin', '').strip()
    action = data.get('action', '').strip()

    if not handle or not pin:
        return jsonify({'error': 'Authentication required'}), 401

    influencer = sheets_helper.get_influencer(handle)
    if not influencer:
        return jsonify({'error': 'Influencer profile not found'}), 404

    pin_hash = hashlib.sha256(pin.encode('utf-8')).hexdigest()
    if pin_hash != str(influencer.get('pin_hash', '')):
        return jsonify({'error': 'Incorrect PIN code'}), 401

    if action == 'add':
        title = data.get('title', '').strip()
        original_url = data.get('original_url', '').strip()
        code = data.get('code', '').strip()
        category = data.get('category', 'hotel').strip()

        if not title or not original_url:
            return jsonify({'error': 'Title and original link are required'}), 400

        deal_id = "DEAL_" + str(int(time.time() * 1000))
        wrapped_url = f"/go/{handle}/{deal_id}"

        res_id = sheets_helper.add_deal(
            handle=handle,
            title=title,
            original_url=original_url,
            wrapped_url=wrapped_url,
            code=code,
            category=category
        )

        if not res_id:
            return jsonify({'error': 'Failed to save deal in Sheets database'}), 500

        return jsonify({'success': True, 'deal_id': res_id, 'wrapped_url': wrapped_url})

    elif action == 'delete':
        deal_id = data.get('deal_id', '').strip()
        if not deal_id:
            return jsonify({'error': 'Deal ID is required to delete'}), 400

        success = sheets_helper.delete_deal(handle, deal_id)
        if not success:
            return jsonify({'error': 'Failed to delete deal'}), 500

        return jsonify({'success': True})

    elif action == 'request_payout':
        total_earned = float(influencer.get('total_earned', 0.0))
        paid_earned = float(influencer.get('paid_earned', 0.0))
        unpaid_balance = total_earned - paid_earned

        if unpaid_balance < 50.0:
            return jsonify({'error': f'Minimum payout balance is $50.00 USD. Your unpaid balance is ${unpaid_balance:.2f} USD'}), 400

        payment_method = influencer.get('payment_method', 'PayPal')
        payment_account = influencer.get('payment_account', '')

        success = sheets_helper.request_payout(
            handle=handle,
            amount=unpaid_balance,
            payment_method=payment_method,
            payment_account=payment_account
        )

        if not success:
            return jsonify({'error': 'Failed to submit payout request in Sheets database'}), 500

        # Send SMTP alert to William (Admin)
        payout_subject = f"💸 Payout Requested: @{handle} - ${unpaid_balance:.2f} USD"
        payout_html = f"""
        <html>
          <body style="font-family: Arial, sans-serif; padding: 20px; line-height: 1.6; color: #1a1a1a;">
            <h2>Payout Request Pending Review</h2>
            <p>An influencer partner has requested a manual payout. Please verify their click stats and issue payment.</p>
            <hr style="border: none; border-top: 1px solid #f4f1ea;">
            <p><strong>Handle:</strong> @{handle}</p>
            <p><strong>Display Name:</strong> {influencer.get('display_name')}</p>
            <p><strong>Payout Amount:</strong> ${unpaid_balance:.2f} USD</p>
            <p><strong>Method:</strong> {payment_method}</p>
            <p><strong>Account:</strong> {payment_account}</p>
            <hr style="border: none; border-top: 1px solid #f4f1ea;">
            <p style="font-size: 12px; color: #888;">TripSync Affiliate Operations</p>
          </body>
        </html>
        """
        send_smtp_email("william@justmemedi.ca", payout_subject, payout_html)

        return jsonify({'success': True, 'amount_requested': unpaid_balance})

    return jsonify({'error': 'Invalid action'}), 400

@app.route('/api/affiliate/stats/<handle>', methods=['GET'])
def affiliate_stats(handle):
    handle = handle.strip().lower()
    influencer = sheets_helper.get_influencer(handle)
    if not influencer:
        return jsonify({'error': 'Influencer profile not found'}), 404

    deals = sheets_helper.get_influencer_deals(handle)

    return jsonify({
        'affiliate': {
            'handle': influencer.get('handle'),
            'display_name': influencer.get('display_name'),
            'bio': influencer.get('bio'),
            'profile_image': influencer.get('profile_image')
        },
        'deals': deals
    })

@app.route('/go/<handle>/<deal_id>')
def redirect_deal(handle, deal_id):
    handle = handle.strip().lower()
    deal = sheets_helper.get_deal(handle, deal_id)
    if not deal:
        logging.warning(f"Wrapped deal {deal_id} for handle @{handle} not found. Redirecting to homepage.")
        return make_response(send_from_directory('.', 'index.html'))

    original_url = deal.get('original_url', '').strip()
    deal_title = deal.get('title', 'Curated Deal')

    # Get client IP securely
    ip_header = request.headers.get('X-Forwarded-For', request.remote_addr)
    client_ip = ip_header.split(',')[0].strip() if ip_header else ""

    # Generate unique click_id (e.g. jess_1782392)
    rand_id = random.randint(1000000, 9999999)
    click_id = f"{handle}_{rand_id}"

    # Self-click exclusion filter
    is_self_click = False
    saved_ip = INFLUENCER_IPS.get(handle)
    if saved_ip and client_ip == saved_ip:
        is_self_click = True
        logging.info(f"Self-click detected for influencer @{handle} from IP {client_ip}. Click logging skipped.")

    if not is_self_click:
        sheets_helper.log_affiliate_click(
            click_id=click_id,
            handle=handle,
            deal_title=deal_title,
            ip=client_ip
        )

    # Dynamic Partner Tracking Loop & URL Cleaning
    target_url = original_url
    
    # 1. Booking.com
    if "booking.com" in target_url.lower():
        cleaned_url = re.sub(r'[\?&]aid=[^&]*', '', target_url)
        cleaned_url = re.sub(r'[\?&]label=[^&]*', '', cleaned_url)
        sep = "&" if "?" in cleaned_url else "?"
        target_url = f"{cleaned_url}{sep}aid=2884913&label={click_id}"

    # 2. Travelpayouts Campaigns (Klook, Tiqets, Viator, Klook etc.)
    elif any(tp_domain in target_url.lower() for tp_domain in ["klook.com", "tiqets.com", "viator.com", "getrentacar.com", "aviasales.com", "kiwitaxi.com", "welcomepickups.com", "ektatraveling.com"]):
        cleaned_url = re.sub(r'[\?&]marker=[^&]*', '', target_url)
        cleaned_url = re.sub(r'[\?&]trs=[^&]*', '', cleaned_url)
        cleaned_url = re.sub(r'[\?&]subid=[^&]*', '', cleaned_url)
        sep = "&" if "?" in cleaned_url else "?"
        target_url = f"{cleaned_url}{sep}marker=733310&subid={click_id}&trs=533550"

    # Make the redirection response and set a 90-day cookie
    resp = make_response(f"""
    <html>
      <head>
        <meta http-equiv="refresh" content="0; url={target_url}">
        <title>Redirecting to Partner...</title>
        <style>
          body {{ font-family: -apple-system, BlinkMacSystemFont, "Segoe UI", Roboto, sans-serif; display: flex; align-items: center; justify-content: center; height: 100vh; background-color: #faf9f6; color: #1a1a1a; }}
          .spinner {{ border: 4px solid rgba(26, 107, 107, 0.1); width: 36px; height: 36px; border-radius: 50%; border-left-color: #1a6b6b; animation: spin 1s linear infinite; margin-bottom: 20px; }}
          @keyframes spin {{ 0% {{ transform: rotate(0deg); }} 100% {{ transform: rotate(360deg); }} }}
          .card {{ text-align: center; }}
        </style>
      </head>
      <body>
        <div class="card">
          <div class="spinner" style="margin: 0 auto 15px;"></div>
          <p>Redirecting you securely to our partner page...</p>
        </div>
      </body>
    </html>
    """)

    resp.set_cookie('tripsync_referral', handle, max_age=90*24*60*60)
    return resp

@app.route('/assistant.html')
def assistant():
    return send_from_directory('.', 'assistant.html')

@app.route('/manifest.json')
def manifest():
    return send_from_directory('.', 'manifest.json')

@app.route('/sw.js')
def sw():
    return send_from_directory('.', 'sw.js')

@app.route('/api/verify-key', methods=['POST'])
def verify_key():
    data = request.get_json()
    key = data.get('key', '').strip()
    provider = data.get('provider', 'deepseek').strip()
    
    if not key:
        return jsonify({'valid': False, 'error': 'No key provided'}), 400
        
    try:
        if provider == 'deepseek':
            url = "https://api.deepseek.com/v1/chat/completions"
            headers = {"Authorization": f"Bearer {key}", "Content-Type": "application/json"}
            payload = {
                "model": "deepseek-chat",
                "messages": [{"role": "user", "content": "ping"}],
                "max_tokens": 5
            }
            resp = requests.post(url, headers=headers, json=payload, timeout=8)
            if resp.status_code == 200:
                return jsonify({'valid': True})
            else:
                try: err_msg = resp.json().get('error', {}).get('message', 'Invalid key')
                except: err_msg = f"Status code {resp.status_code}"
                return jsonify({'valid': False, 'error': err_msg}), 400
                
        elif provider == 'groq':
            url = "https://api.groq.com/openai/v1/chat/completions"
            headers = {"Authorization": f"Bearer {key}", "Content-Type": "application/json"}
            payload = {
                "model": "llama-3.3-70b-versatile",
                "messages": [{"role": "user", "content": "ping"}],
                "max_tokens": 5
            }
            resp = requests.post(url, headers=headers, json=payload, timeout=8)
            if resp.status_code == 200:
                return jsonify({'valid': True})
            else:
                try: err_msg = resp.json().get('error', {}).get('message', 'Invalid key')
                except: err_msg = f"Status code {resp.status_code}"
                return jsonify({'valid': False, 'error': err_msg}), 400
                
        elif provider == 'gemini':
            url = f"https://generativelanguage.googleapis.com/v1beta/models/gemini-1.5-flash:generateContent?key={key}"
            payload = {"contents": [{"parts": [{"text": "ping"}]}]}
            resp = requests.post(url, json=payload, timeout=8)
            if resp.status_code == 200:
                return jsonify({'valid': True})
            else:
                try: err_msg = resp.json().get('error', {}).get('message', 'Invalid key')
                except: err_msg = f"Status code {resp.status_code}"
                return jsonify({'valid': False, 'error': err_msg}), 400
                
        return jsonify({'valid': False, 'error': 'Unknown provider'}), 400
    except Exception as e:
        return jsonify({'valid': False, 'error': str(e)}), 500

import base64

def decrypt_key(encrypted_key, email=""):
    try:
        # Base64 decode
        obfuscated = base64.b64decode(encrypted_key).decode('utf-8')
        # Get composite secret
        salt = "TS-2026-FLY-Sync-Secure-0A1B2C3D"
        secret = f"{email.strip().lower()}_{salt}" if email else salt
        
        # XOR decryption
        plain_chars = []
        for i in range(len(obfuscated)):
            char_code = ord(obfuscated[i])
            salt_code = ord(secret[i % len(secret)])
            plain_chars.append(chr(char_code ^ salt_code))
            
        return "".join(plain_chars)
    except Exception as e:
        logging.error(f"Failed key decryption: {e}")
        return None

def call_deepseek_history(decrypted_key, system_prompt, history_messages):
    url = "https://api.deepseek.com/v1/chat/completions"
    headers = {"Authorization": f"Bearer {decrypted_key}", "Content-Type": "application/json"}
    
    # Format messages
    messages = [{"role": "system", "content": system_prompt}]
    for msg in history_messages:
        messages.append({"role": msg.get("role"), "content": msg.get("content")})
        
    payload = {
        "model": "deepseek-chat",
        "messages": messages,
        "max_tokens": 1500,
        "temperature": 0.7
    }
    
    try:
        resp = requests.post(url, headers=headers, json=payload, timeout=12)
        if resp.status_code == 200:
            return resp.json()['choices'][0]['message']['content'], False
        else:
            logging.warning(f"DeepSeek failed with status code {resp.status_code}: {resp.text}")
            return None, True
    except Exception as e:
        logging.error(f"DeepSeek connection error: {e}")
        return None, True

def call_groq_history(system_prompt, history_messages):
    if not GROQ_KEY:
        logging.error("No server-side GROQ_API_KEY for failover")
        return None
    url = "https://api.groq.com/openai/v1/chat/completions"
    headers = {"Authorization": f"Bearer {GROQ_KEY}", "Content-Type": "application/json"}
    
    messages = [{"role": "system", "content": system_prompt}]
    for msg in history_messages:
        messages.append({"role": msg.get("role"), "content": msg.get("content")})
        
    payload = {
        "model": GROQ_MODEL,
        "messages": messages,
        "max_tokens": 1500,
        "temperature": 0.7
    }
    try:
        resp = requests.post(url, headers=headers, json=payload, timeout=12)
        if resp.status_code == 200:
            return resp.json()['choices'][0]['message']['content']
        else:
            logging.error(f"Groq history endpoint failed: {resp.status_code} {resp.text}")
    except Exception as e:
        logging.error(f"Groq history error: {e}")
    return None

def call_gemini_history(system_prompt, history_messages):
    if not GEMINI_API_KEY:
        logging.error("No server-side GEMINI_API_KEY for failover")
        return None
    url = f"https://generativelanguage.googleapis.com/v1beta/models/gemini-1.5-flash:generateContent?key={GEMINI_API_KEY}"
    
    # Format messages for Gemini API (Gemini uses 'user' and 'model' roles)
    contents = []
    for msg in history_messages:
        role = "user" if msg.get("role") == "user" else "model"
        contents.append({
            "role": role,
            "parts": [{"text": msg.get("content")}]
        })
        
    payload = {
        "contents": contents,
        "systemInstruction": {"parts": [{"text": system_prompt}]},
        "generationConfig": {
            "temperature": 0.7,
            "maxOutputTokens": 1500
        }
    }
    try:
        resp = requests.post(url, json=payload, timeout=12)
        if resp.status_code == 200:
            data = resp.json()
            if "candidates" in data and len(data["candidates"]) > 0:
                return data["candidates"][0]["content"]["parts"][0]["text"]
        else:
            logging.error(f"Gemini history endpoint failed: {resp.status_code} {resp.text}")
    except Exception as e:
        logging.error(f"Gemini history error: {e}")
    return None

@app.route('/api/llm/proxy', methods=['POST'])
def llm_proxy():
    data = request.get_json()
    prompt = data.get('prompt', '').strip()
    encrypted_key = data.get('encrypted_key', '').strip()
    email = data.get('email', '').strip()
    provider = data.get('provider', 'deepseek').strip()
    destination = data.get('destination', '').strip()
    history = data.get('history', [])

    if not prompt:
        return jsonify({'error': 'No prompt message provided'}), 400

    decrypted_key = decrypt_key(encrypted_key, email)
    if not decrypted_key:
        return jsonify({'error': 'Invalid key decrypt challenge'}), 400

    system_prompt = f"You are TripSync, a premium AI travel curate assistant. Let's refine the trip to {destination} step-by-step. Keep responses structured, concise, friendly, and under 3-4 paragraphs. Incorporate helpful advice and bullet points where applicable."

    # Priority Order list for Auto Failover:
    # 1. Active User Key (either DeepSeek, Groq, or Gemini)
    # 2. Server Groq
    # 3. Server Gemini
    
    failover_triggered = False
    failover_provider = None
    response_text = None

    if provider == 'deepseek':
        response_text, failed = call_deepseek_history(decrypted_key, system_prompt, history)
        if failed:
            logging.warning("DeepSeek API failed. Triggering auto-failover to Groq (Tier 2)")
            failover_triggered = True
            failover_provider = 'groq'
            response_text = call_groq_history(system_prompt, history)
            if not response_text:
                logging.warning("Groq backup failed. Triggering auto-failover to Gemini (Tier 3)")
                failover_provider = 'gemini'
                response_text = call_gemini_history(system_prompt, history)
    
    elif provider == 'groq':
        url = "https://api.groq.com/openai/v1/chat/completions"
        headers = {"Authorization": f"Bearer {decrypted_key}", "Content-Type": "application/json"}
        messages = [{"role": "system", "content": system_prompt}]
        for msg in history:
            messages.append({"role": msg.get("role"), "content": msg.get("content")})
        payload = {"model": GROQ_MODEL, "messages": messages, "max_tokens": 1500, "temperature": 0.7}
        try:
            resp = requests.post(url, headers=headers, json=payload, timeout=12)
            if resp.status_code == 200:
                response_text = resp.json()['choices'][0]['message']['content']
        except Exception as e:
            logging.error(f"User Groq call failed: {e}")
        
        if not response_text:
            logging.warning("User Groq failed. Triggering auto-failover to Server Groq")
            response_text = call_groq_history(system_prompt, history)
            if not response_text:
                logging.warning("Server Groq failed. Triggering auto-failover to Server Gemini")
                failover_triggered = True
                failover_provider = 'gemini'
                response_text = call_gemini_history(system_prompt, history)

    elif provider == 'gemini':
        url = f"https://generativelanguage.googleapis.com/v1beta/models/gemini-1.5-flash:generateContent?key={decrypted_key}"
        contents = []
        for msg in history:
            role = "user" if msg.get("role") == "user" else "model"
            contents.append({"role": role, "parts": [{"text": msg.get("content")}]})
        payload = {"contents": contents, "systemInstruction": {"parts": [{"text": system_prompt}]}, "generationConfig": {"temperature": 0.7, "maxOutputTokens": 1500}}
        try:
            resp = requests.post(url, json=payload, timeout=12)
            if resp.status_code == 200:
                data = resp.json()
                if "candidates" in data and len(data["candidates"]) > 0:
                    response_text = data["candidates"][0]["content"]["parts"][0]["text"]
        except Exception as e:
            logging.error(f"User Gemini call failed: {e}")
            
        if not response_text:
            logging.warning("User Gemini failed. Triggering auto-failover to Server Gemini")
            response_text = call_gemini_history(system_prompt, history)
            if not response_text:
                logging.warning("Server Gemini failed. Triggering auto-failover to Server Groq")
                failover_triggered = True
                failover_provider = 'groq'
                response_text = call_groq_history(system_prompt, history)

    if not response_text:
        return jsonify({'error': 'All LLM failovers exhausted. API keys may be blocked or offline.'}), 502

    return jsonify({
        'response': response_text,
        'failover_triggered': failover_triggered,
        'failover_provider': failover_provider
    })

@app.route('/api/chat', methods=['POST'])
@limiter.limit("5 per minute")
def api_chat():
    data = request.get_json() or {}
    destination = data.get('destination', '').strip()
    days = data.get('days', '5').strip()
    currency = data.get('currency', 'USD').strip()
    history = data.get('history', [])

    if not history:
        return jsonify({'error': 'No chat history provided'}), 400

    system_prompt = (
        f"You are TripSync, a premium AI travel assistant helping plan a {days}-day trip to {destination} in {currency} currency. "
        f"Provide highly relevant, customized travel advice for this specific trip. Keep responses concise, structured, friendly, and under 3-4 paragraphs. "
        f"Use bullet points for lists and readability."
    )

    # Priority Order failover:
    # 1. Server Groq
    # 2. Server Gemini
    response_text = call_groq_history(system_prompt, history)
    if not response_text:
        logging.warning("Server Groq failed. Triggering failover to Server Gemini")
        response_text = call_gemini_history(system_prompt, history)

    if not response_text:
        return jsonify({'error': 'All LLM failovers exhausted. API keys may be blocked or offline.'}), 502

    return jsonify({'response': response_text})

@app.route('/api/tripsync', methods=['POST'])
@limiter.limit("5 per minute")
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
        conn, is_pg = get_db_connection()
        c = conn.cursor()
        query_sql = "INSERT INTO search_log (query,departure,currency,timestamp) VALUES (?,?,?,?)"
        if is_pg:
            query_sql = query_sql.replace('?', '%s')
        c.execute(query_sql, (query, depart_city, currency, datetime.now().isoformat()))
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
        conn, is_pg = get_db_connection()
        c = conn.cursor()
        query_sql = "INSERT INTO search_log (query,departure,currency,timestamp) VALUES (?,?,?,?)"
        if is_pg:
            query_sql = query_sql.replace('?', '%s')
        c.execute(query_sql, (query, depart_city, currency, datetime.now().isoformat()))
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
        conn, is_pg = get_db_connection()
        c = conn.cursor()
        query_sql = "INSERT INTO search_log (query,departure,currency,timestamp) VALUES (?,?,?,?)"
        if is_pg:
            query_sql = query_sql.replace('?', '%s')
        c.execute(query_sql, (query, depart_city, currency, datetime.now().isoformat()))
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
@limiter.limit("5 per minute")
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
@limiter.limit("10 per minute")
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
@limiter.limit("5 per minute")
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
@limiter.limit("5 per minute")
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
        conn, is_pg = get_db_connection()
        c = conn.cursor()
        query_sql = "INSERT INTO click_log (destination,platform,project_name,timestamp) VALUES (?,?,?,?)"
        if is_pg:
            query_sql = query_sql.replace('?', '%s')
        c.execute(query_sql,
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
        conn, is_pg = get_db_connection()
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
