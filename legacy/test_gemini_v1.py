import requests
import os
from dotenv import load_dotenv

load_dotenv()
key = os.environ.get("GEMINI_API_KEY")
# Testing v1 endpoint
url = f"https://generativelanguage.googleapis.com/v1/models/gemini-1.5-flash:generateContent?key={key}"

payload = {
    "contents": [{"parts": [{"text": "Hi"}]}]
}

try:
    resp = requests.post(url, json=payload, timeout=30)
    print("STATUS:", resp.status_code)
    if resp.status_code == 200:
        print("SUCCESS!")
    else:
        print("RESPONSE:", resp.json())
except Exception as e:
    print("ERROR:", e)
