import google.generativeai as genai
import os
from dotenv import load_dotenv

load_dotenv()
key = os.environ.get("GEMINI_API_KEY")
print(f"KEY FOUND: {bool(key)}")
genai.configure(api_key=key)

try:
    model = genai.GenerativeModel("gemma-2-27b-it")
    response = model.generate_content("Hi")
    print("RESPONSE:", response.text)
except Exception as e:
    print("ERROR:", e)
