import requests
import json

try:
    resp = requests.post("http://127.0.0.1:5001/api/tripsync-local", 
        json={"query":"test trip","departCity":"London","currency":"USD","checkIn":"","checkOut":"","guests":"2","budget":"","flightClass":"economy","hotelRating":"any","amenities":[],"carType":"none"})
    print("Status:", resp.status_code)
    print("Response:", resp.text)
except Exception as e:
    print("Error:", e)
