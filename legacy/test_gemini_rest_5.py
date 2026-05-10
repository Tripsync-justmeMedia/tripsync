import requests
import os
from dotenv import load_dotenv

load_dotenv()
key = os.environ.get("GEMINI_API_KEY")
url = f"https://generativelanguage.googleapis.com/v1beta/models/gemma-2-9b-it:generateContent?key={key}"

payload = {
    "contents": [{"parts": [{"text": "Hi"}]}]
}

try:
    resp = requests.post(url, json=payload, timeout=30)
    print("STATUS:", resp.status_code)
    print("RESPONSE:", resp.json())
except Exception as e:
    print("ERROR:", e)
