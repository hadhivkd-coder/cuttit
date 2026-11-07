---
name: city-map-reel
description: Make a 9:16 "navigation app" style map reel of a real route through any city - a 3D Google Earth Studio flight plus an animated maps overlay (route line, turn card, landmark card, drop pin). Use when the user asks for a map reel, route reel, city flyover, or "map edit" of a place.
---

# City Map Reel

You produce a ~14 second vertical reel (1080x1920, 30 fps) that follows a real
route through a city and lands on one landmark. The user never keyframes by hand.

## Ask first (one message, then wait)
1. City, start point and the landmark to end on (e.g. "Kozhikode beach -> Mananchira Square").
2. Mode: driving or walking.
3. Their handle for the end card (optional).

## Step 1 - Real route
- Get directions from OSRM: `https://router.project-osrm.org/route/v1/{driving|foot}/{lon1},{lat1};{lon2},{lat2}?overview=full&geometries=geojson&steps=true`
- Geocode names with Nominatim (`nominatim.openstreetmap.org/search?format=json&q=...`, 1 request/second, send a User-Agent).
- Keep the route between 0.8 and 2 km. Longer routes feel rushed in 14 s.
- Pull 3-5 "pop-in" places near the route from Overpass (`tourism`, `amenity=place_of_worship`, `shop=mall`, `historic`).
- SHOW THE USER the route as a list of street names + the pop-ins, and wait for "ok".

## Step 2 - Camera (.esp for Google Earth Studio)
Write `make_camera.py` that outputs `camera.esp` (Earth Studio project JSON):
- Sample the route polyline into one keyframe every 0.5 s.
- 0-60% of time: chase cam, altitude 250-400 m, tilt 60-65 deg, heading = bearing of the road ahead, smoothed over 1 s so turns don't snap.
- At the final turn: tilt down to 35-45 deg over 1.5 s.
- Arrival: hold 0.5 s, then orbit the landmark 120 deg at 500 m, radius 300 m.
- Ease every segment (no linear jumps). Export frames at 1080x1920.
- Also write `track.json`: for every frame, the screen x/y of the blue dot and of each pop-in. The overlay uses this so it stays glued to the flight.

Tell the user: open earth.google.com/studio in Chrome, File > Import > camera.esp, Render, drop `flight.mp4` back here.

## Step 3 - Overlay (maps UI layer)
Build with Python (Pillow) frames + ffmpeg, or an HTML page captured with Playwright:
- Top: turn card (arrow + street name + distance counting down).
- Bottom: ETA bar, speed sign.
- Pop-in pins: scale 0 -> 1.1 -> 1 over 8 frames when their point enters the frame.
- Landmark card slides up from the bottom at arrival; red pin drops with 2 expanding rings.
- "Arrived" banner, then end card with the handle.
- Use your own design: rounded white cards, one accent colour, Inter/Roboto. Do NOT copy any real app's logo or icon.

Composite: `ffmpeg -i flight.mp4 -framerate 30 -i overlay/%05d.png -filter_complex overlay -c:v libx264 -pix_fmt yuv420p -crf 18 reel.mp4`

## Step 4 - Notes
Take notes one round at a time ("the card covers the route", "the pin is late") and re-render only the overlay when possible.

## Rules
- Google Earth requires visible attribution: keep the small "Google Earth" credit in the frame.
- OSM data: add "Map data (c) OpenStreetMap contributors" in the caption or end card.
- Never guess a route - always use real OSRM output.
