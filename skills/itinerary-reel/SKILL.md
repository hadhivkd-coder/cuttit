---
name: itinerary-reel
description: Turn a trip plan into a "3 days in <city>" reel - day cards, a map with pins hopping stop to stop, travel times, and the user's own clips. Use for travel itinerary reels, "things to do in X", or food trails.
---

# Itinerary Reel

## Ask first
1. City and number of days. 2. Their own clips/photos per stop (optional). 3. Budget level / interests.

## Steps
1. Draft the itinerary: 3-4 stops per day, geographically sensible order. Geocode each stop with Nominatim, compute walking/driving time between stops with OSRM. Show the plan as a table and wait for approval.
2. Map: draw a stylised base map from OpenStreetMap data (Overpass roads + water + parks) with Pillow or matplotlib - do NOT download map tiles in bulk. Animate a dashed line drawing between pins, pin pops on arrival.
3. Per stop: 1.5 s of the user's clip (or a styled title card if none) with name + "12 min walk" chip.
4. Day cards between days ("DAY 2"), 0.8 s each. End card: "Save this for your trip".
5. Export 1080x1920. Put the full written itinerary in the caption text file `caption.txt`.

## Rules
- Credit "(c) OpenStreetMap contributors".
- Opening hours and prices: tell the user to verify; don't state them as fact.
