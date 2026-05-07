#!/bin/bash

# Update flight links to auto-populate destination
sed -i '' 's|https://www.skyscanner.com/transport/flights/${document.getElementById('\''departureCity'\'').value.toLowerCase()}/${d.city.toLowerCase()}/|`https://www.skyscanner.com/transport/flights/${departure}/${d.city.toLowerCase()}/${startDate}/`|g' index.html

# Update booking.com hotel links
sed -i '' 's|https://www.booking.com/searchresults.html?dest=${d.city}&aid=${AFFILIATE.booking_aid}|`https://www.booking.com/searchresults.html?dest=${encodeURIComponent(d.city)}&aid=${AFFILIATE.booking_aid}`|g' index.html

echo "Link updates complete. Check the file to verify."
