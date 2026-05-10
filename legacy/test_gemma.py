import requests

prompt = """You are TripSync, a world-class AI travel curator. Your goal is to inspire and provide high-accuracy travel planning.
Return ONLY valid JSON, no extra text, no markdown.

User request: 5 days in Tokyo, budget traveller, flying from London.

Return exactly 3 destination recommendations in this exact JSON format:
{
  "destinations": [
    {
      "city": "City Name",
      "country": "Country Name",
      "description": "A compelling 3-4 sentence narrative on why this is the perfect match. Focus on the 'vibe' and specific experiences.",
      "vibe_tags": ["#Tag1", "#Tag2", "#Tag3"],
      "match_score": "9.2/10",
      "best_season": "November to March",
      "budget_per_day": "X-Y USD per person",
      "flight_estimate": "X-Y USD return from London",
      "flight_duration": "X-Y hours",
      "visa": "Visa requirements for most nationalities",
      "highlights": ["Iconic Activity", "Local Secret", "Food Experience", "Must-see Spot"],
      "flight_class": "economy",
      "hotel_rating": "any"
    }
  ]
}

Rules:
- All prices in USD
- Flights from London
- Be specific with real price ranges
- highlights must be an array of exactly 4 short, evocative strings
- vibe_tags must be an array of 3 hashtags starting with #
- Return ONLY the JSON object, nothing else"""

try:
    resp = requests.post("http://localhost:11434/api/generate",
        json={"model": "gemma4", "prompt": prompt, "stream": False,
              "options": {"temperature": 0.5, "num_predict": 1500}},
        timeout=120)
    print("STATUS:", resp.status_code)
    print("RESPONSE:", resp.json().get("response", ""))
except Exception as e:
    print("ERROR:", e)
