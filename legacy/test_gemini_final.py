import google.generativeai as genai
import os
from dotenv import load_dotenv

load_dotenv()
key = os.environ.get("GEMINI_API_KEY")
genai.configure(api_key=key)

try:
    model = genai.GenerativeModel("gemini-1.5-flash")
    response = model.generate_content("Hi")
    print("SUCCESS:", response.text)
except Exception as e:
    print("ERROR:", e)
