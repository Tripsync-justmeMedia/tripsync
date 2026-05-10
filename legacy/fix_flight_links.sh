#!/bin/bash

# Backup current file
cp index.html index_backup_flight_fix.html

# Replace the single flight link with multiple options
sed -i '' 's|<a href="https://www.google.com/travel/flights?q=Flights%20from%20${dep}%20to%20${d.city}" target="_blank" class="booking-btn">✈️ Search Flights</a>|\
<a href="https://www.google.com/travel/flights?q=Flights%20from%20${dep}%20to%20${d.city}" target="_blank" class="booking-btn">✈️ Google Flights</a>\
<a href="https://www.kayak.com/flights/${dep}-${d.city}" target="_blank" class="booking-btn">🌍 Kayak</a>\
<a href="https://www.expedia.com/Flights-Search?destination=${d.city}" target="_blank" class="booking-btn">🏨 Expedia</a>\
<a href="https://www.cheapoair.com/flights/results?destination=${d.city}" target="_blank" class="booking-btn">💰 CheapOair</a>|g' index.html

echo "Added multiple flight options. Deploying..."
git add index.html
git commit -m "Add multiple flight search options (Google, Kayak, Expedia, CheapOair)"
git push
