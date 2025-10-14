# ai_interaction.py
"""Here we handle interaction with the AI (OpenAI) and related data processing (including ORS)."""

import requests # type: ignore
import os
import random
from math import radians, cos, sin, sqrt, atan2
import pandas as pd # type: ignore
from cryptography.fernet import Fernet # type: ignore
from config import get_ors_api_key, resource_path

import pickle
import time
import hashlib
from pathlib import Path
from config import get_application_path 

# --- City Database Loading (for fallback/filtering) ---
def load_city_database():
    """
    Loads city data from cities.csv
    Uses: city_ascii, state_name, lat, lng
    Returns: {"miami, florida": (25.7617, -80.1918), ...}
    """
    db = {}
    csv_path = resource_path("cities.csv")

    print(f"🔍 Looking for cities.csv at: {csv_path}")

    try:
        df = pd.read_csv(csv_path)
        print(f"✅ CSV loaded successfully! Shape: {df.shape} (rows, cols)")

        df.columns = [col.strip().lower() for col in df.columns]
        print(f"📊 Columns found: {list(df.columns)}")

        required = ['city_ascii', 'state_name', 'lat', 'lng']
        for col in required:
            if col not in df.columns:
                print(f"❌ Missing column: {col}")
                return {}

        print("🔄 Loading cities into database...")

        for i, (_, row) in enumerate(df.iterrows()):
            try:
                city = row['city_ascii'].strip()
                state = row['state_name'].strip()
                full_location = f"{city}, {state}".lower()

                lat = float(row['lat']) # type: ignore
                lon = float(row['lng'])# type: ignore

                if full_location not in db:
                    db[full_location] = (lat, lon)
                else:
                    if i < 10:
                        print(f"🔁 Skipped duplicate: {full_location}")
            except Exception as e:
                print(f"⚠️ Skip row {i}: {e}")
                continue

        print(f"✅ Loaded {len(db)} unique cities into database.")
        return db

    except FileNotFoundError:
        print(f"❌ cities.csv not found at {csv_path}")
        return {}
    except Exception as e:
        print(f"❌ Error loading cities: {e}")
        return {}

# --- Distance Calculation (Haversine) ---
def calculate_distance(lat1, lon1, lat2, lon2):
    """
    Calculate Haversine distance between two points
    """
    R = 6371  # Earth radius in km
    dlat = radians(lat2 - lat1)
    dlon = radians(lon2 - lon1)
    a = sin(dlat / 2)**2 + cos(radians(lat1)) * cos(radians(lat2)) * sin(dlon / 2)**2
    c = 2 * atan2(sqrt(a), sqrt(1 - a))
    distance_km = R * c
    return distance_km

# --- ORS Caching Logic ---
CACHE_FILENAME = "ors_route_cache.pkl"
CACHE_TTL_SECONDS = 7 * 24 * 60 * 60 # Cache entries expire after 7 days. <-- Don't touch!

def get_cache_path():
    """Gets the path for the ORS cache file in the application directory."""
    app_path = Path(get_application_path())
    return app_path / CACHE_FILENAME

def load_ors_cache():
    """Loads the ORS route cache from a file."""
    cache_path = get_cache_path()
    if cache_path.exists():
        try:
            with open(cache_path, 'rb') as f:
                cache = pickle.load(f)
            # Basic sanity check
            if isinstance(cache, dict):
                print(f"[ORS_CACHE] Loaded cache with {len(cache)} entries.")
                return cache
            else:
                print(f"[ORS_CACHE] Corrupted cache file format. Creating new cache.")
        except (pickle.PickleError, EOFError, FileNotFoundError) as e:
            print(f"[ORS_CACHE] Error loading cache: {e}. Creating new cache.")
    else:
        print(f"[ORS_CACHE] No existing cache file found at {cache_path}.")
    return {} # Returns empty cache if loading fails or file doesn't exist

def save_ors_cache(cache):
    """Saves the ORS route cache to a file."""
    cache_path = get_cache_path()
    try:
        # Ensure the application directory exists
        cache_path.parent.mkdir(parents=True, exist_ok=True)
        with open(cache_path, 'wb') as f:
            pickle.dump(cache, f)
        print(f"[ORS_CACHE] Saved cache with {len(cache)} entries to {cache_path}.")
    except Exception as e:
        print(f"[ORS_CACHE] Error saving cache: {e}")

def get_cache_key(start_coords, end_coords):
    """
    Generates a unique, deterministic key for a route based on start/end coordinates.
    Sorting coordinates ensures (A->B) and (B->A) use the same key if symmetric.
    """
    # Create a tuple of tuples for immutability and sorting
    coord_tuple = tuple(sorted([tuple(start_coords), tuple(end_coords)]))
    # Create a hash of the sorted coordinates for a compact key
    cache_key = hashlib.md5(str(coord_tuple).encode('utf-8')).hexdigest()
    return cache_key

def is_cache_entry_valid(entry):
    """Checks if a cache entry is still valid based on TTL."""
    if not isinstance(entry, dict) or 'timestamp' not in entry:
        return False
    return (time.time() - entry['timestamp']) < CACHE_TTL_SECONDS

# --- End ORS Caching Logic ---

# --- Nearby City Logic (Hybrid ORS API with Improved Haversine Pre-filter & Caching) ---
def get_nearby_city(location, city_coords_db):
    """
    Returns a real city within a 35-50 minute driving time using ORS API,
    with improved Haversine pre-filtering (min distance + target sort) and caching for speed and efficiency.
    Falls back to Haversine if ORS fails or no suitable city found via ORS.
    """
    print(f"\n🔍 Searching for nearby city to: '{location}'")
    # Retrieve the ORS API key from config.py
    ORS_API_KEY = get_ors_api_key()

    loc = location.lower().strip()
    base_loc = loc.split(',')[0].strip()
    print(f"🧩 Parsed base location: '{base_loc}'")

    if loc not in city_coords_db:
        print(f"❌ '{location}' not found in database.")
        # Use fallback logic similar to original
        prefixes = ["North", "South", "East", "West", "Lake", "New", "Port", "Upper", "Green", "Sun"]
        
        prefix = random.choice(prefixes)
        fallback = f"{prefix} {base_loc}"
        print(f"🔧 Fallback: Using '{fallback}'")
        return fallback

    lat1, lon1 = city_coords_db[loc]
    origin_coords = (lon1, lat1) # ORS format (lon, lat)
    print(f"📍 Found {loc.title()}: ({lat1:.4f}, {lon1:.4f})")

    # --- Load Cache ---
    route_cache = load_ors_cache()
    cache_modified = False # Start with False
    
    # --- IMPROVED Pre-filter candidates using Haversine ---
    # --- Configuration Constants (defined locally for this function scope) ---
    MIN_HAVERSINE_DISTANCE_KM = 25  # Skip cities closer than this (unlikely to be 35+ mins drive)
    TARGET_HAVERSINE_DISTANCE_KM = 40  # Target midpoint Haversine distance for 35-45 min drive (~40km)
    PRE_FILTER_DISTANCE_KM = 75  # Upper bound for Haversine pre-filter
    # ---

    print(f"📏 Pre-filtering candidates using Haversine distance ({MIN_HAVERSINE_DISTANCE_KM} - {PRE_FILTER_DISTANCE_KM} km)...")
    haversine_candidates = []
    for city, (lat2, lon2) in city_coords_db.items():
        if city == loc:
            continue
        haversine_dist_km = calculate_distance(lat1, lon1, lat2, lon2)
        # Apply the MINIMUM distance filter here
        if MIN_HAVERSINE_DISTANCE_KM <= haversine_dist_km <= PRE_FILTER_DISTANCE_KM:
            haversine_candidates.append((city, lat2, lon2, haversine_dist_km))

    print(f"🎯 Found {len(haversine_candidates)} cities within {MIN_HAVERSINE_DISTANCE_KM}–{PRE_FILTER_DISTANCE_KM} km Haversine.")

    # --- SORT candidates by proximity to TARGET Haversine distance ---
    print(f"🔄 Sorting candidates by proximity to target Haversine distance ({TARGET_HAVERSINE_DISTANCE_KM} km)...")
    haversine_candidates.sort(key=lambda x: abs(x[3] - TARGET_HAVERSINE_DISTANCE_KM))
    # Optional: Print first few sorted candidates for debugging
    if haversine_candidates:
        print(f"[DEBUG] First 5 sorted candidates (by closeness to {TARGET_HAVERSINE_DISTANCE_KM}km Haversine): {[c[0] for c in haversine_candidates[:5]]}")

    SHUFFLE_TOP_N = min(10, len(haversine_candidates)) # Shuffle top 10 or fewer if list is small
    if SHUFFLE_TOP_N > 1:
        # Extract the top N candidates
        top_candidates = haversine_candidates[:SHUFFLE_TOP_N]
        # Shuffle them randomly
        random.shuffle(top_candidates)
        # Put the shuffled candidates back at the beginning of the list
        haversine_candidates[:SHUFFLE_TOP_N] = top_candidates
        print(f"[DEBUG] Shuffled the top {SHUFFLE_TOP_N} candidates for varied ORS checking order.")
    # -------------------------------------------------

    if ORS_API_KEY:
        print("🌐 Attempting to use OpenRouteService API for driving time...")
        try:
            candidates_via_ors = []
            # --- Update the message to reflect the actual range used ---
            print("🔎 Scanning pre-filtered & sorted cities for driving time (40-50 mins range)...") 
            MAX_ORS_CALLS = 5 # Limit API calls per request
            ors_calls_made = 0
            
            # --- Define Interleaved Index Iterator ---
            def interleaved_indices(length):
                """Generates indices in an interleaved pattern (start, mid, start+1, mid+1, ...)"""
                if length <= 0:
                    return
                mid_point = length // 2
                i, j = 0, mid_point
                toggle = True # True means take from start half, False from mid half
                
                while i < mid_point or j < length:
                    if toggle and i < mid_point:
                        yield i
                        i += 1
                    elif not toggle and j < length:
                        yield j
                        j += 1
                    # Switch toggle for next iteration, but handle cases where one half is exhausted
                    if (toggle and i >= mid_point) or (not toggle and j >= length):
                            # If one half is done, just continue with the other
                            toggle = not toggle
                    else:
                            # Normal toggle
                            toggle = not toggle
            # ------------------------------------------
    
            # --- Use the Interleaved Iterator ---
            num_candidates = len(haversine_candidates)
            if num_candidates == 0:
                    print("[ORS_SCAN] No candidates passed Haversine pre-filtering.")
                    # Consider: Should this trigger an immediate fallback, or proceed to check the next fallback logic?
                    # For now, let it proceed to the fallback outside the 'if ORS_API_KEY:' block.
            else:
                interleaved_index_iterator = interleaved_indices(num_candidates)
                
                # --- Iterate using the new pattern ---
                for _ in range(min(MAX_ORS_CALLS, num_candidates)): # Ensure we don't exceed bounds or call limit
                    if ors_calls_made >= MAX_ORS_CALLS:
                        print(f"[ORS_LIMIT] Reached maximum API calls ({MAX_ORS_CALLS}). Stopping ORS checks.")
                        break
                    
                    try:
                        # Get the next index according to the interleaved pattern
                        candidate_index = next(interleaved_index_iterator)
                    except StopIteration:
                        # This shouldn't happen with the range check, but good practice
                        print("[ORS_SCAN] No more candidates to check according to pattern.")
                        break
                    
                    # Get the candidate data using the calculated index
                    city, lat2, lon2, haversine_dist_km = haversine_candidates[candidate_index]
                    
                    # --- The rest of the ORS checking logic remains largely the same ---
                    destination_coords = (lon2, lat2) # ORS format (lon, lat) - NOTE: Potential Bug Fix (see below)
                    cache_key = get_cache_key(origin_coords, destination_coords)
                    # --- Check Cache ---
                    duration_minutes = None
                    distance_km = None
                    if cache_key in route_cache and is_cache_entry_valid(route_cache[cache_key]):
                        cached_data = route_cache[cache_key]
                        duration_minutes = cached_data['duration_minutes']
                        distance_km = cached_data['distance_km']
                        print(f"[CACHE_HIT] {city.title()}: {distance_km:.2f} km, {duration_minutes:.1f} mins (Driving - Cached)")
                    # --- ORS API Call (if not cached or expired) ---
                    else:
                        print(f"[ORS_CALL] Checking route to {city.title()} (Haversine: {haversine_dist_km:.1f} km)...")
                        # Add a small delay to be respectful of rate limits
                        time.sleep(0.15) # 150ms delay between calls
                        # --- CRITICAL FIX: Removed trailing spaces from the URL ---
                        url = "https://api.openrouteservice.org/v2/directions/driving-car" # Ensure NO trailing space
                        headers = {
                            'Authorization': ORS_API_KEY,
                            'Content-Type': 'application/json',
                            'Accept': 'application/json, application/geo+json, application/gpx+xml, img/png; charset=utf-8'
                        }
                        body = {
                            "coordinates": [origin_coords, destination_coords],
                            "instructions": False,
                            "geometry": False,
                            "units": "km",
                            "language": "en"
                        }
                        try: # Add specific try/except for the API call
                            response = requests.post(url, json=body, headers=headers, timeout=10) # Shorter timeout
                            response.raise_for_status() # Raise exception for bad status codes (like 404)
                            data = response.json()
                            ors_calls_made += 1
                            # Extract distance (in km) and duration (in seconds)
                            distance_km = data['routes'][0]['summary']['distance']
                            duration_seconds = data['routes'][0]['summary']['duration']
                            duration_minutes = duration_seconds / 60.0
                            # --- Update Cache ---
                            route_cache[cache_key] = {
                                'duration_minutes': duration_minutes,
                                'distance_km': distance_km,
                                'timestamp': time.time()
                            }
                            cache_modified = True
                            print(f"[ORS_RESULT] {city.title()}: {distance_km:.2f} km, {duration_minutes:.1f} mins (Driving - Fetched)")
                        except requests.exceptions.HTTPError as e:
                                # Specifically catch HTTP errors like 404
                                print(f"[ORS_ERROR] HTTP Error for {city.title()}: {e.response.status_code} - {e.response.reason}. Skipping this candidate.")
                                # Continue to the next candidate in the interleaved pattern
                                continue
                        except requests.exceptions.RequestException as e:
                            print(f"[ORS_ERROR] Request Error for {city.title()}: {e}. Skipping.")
                            continue
                        except KeyError as e:
                            print(f"[ORS_ERROR] Malformed response for {city.title()} (Missing Key: {e}). Skipping.")
                            continue
                        except Exception as e:
                            print(f"[ORS_ERROR] Unexpected error for {city.title()}: {e}. Skipping.")
                            continue
                        
                    # --- Check if within desired DRIVING time range (36-50 mins based on logs) ---
                    # TODO: Make this range configurable or consistent (was 35-45 in code comments)
                    if 36 <= duration_minutes <= 50: # gives a slightly wider range!
                        print(f"✅ [MATCH] {city.title()} is within 36-50 mins driving time!")
                        candidates_via_ors.append((city, distance_km, duration_minutes))
                        # IMPORTANT: Stop as soon as we find the FIRST valid one according to the pattern.
                        break
                # --- End of Iteration Loop ---
                
            # --- Save Cache (consider optimizing this) ---
            if ors_calls_made > 0:
                    save_ors_cache(route_cache)
            # --- Evaluate ORS Results ---
            if candidates_via_ors:
                # Select the first (and best, due to breaking early) candidate
                selected_city, distance_km, duration_mins = candidates_via_ors[0]
                print(f"🏆 Selected (ORS/Hybrid): {selected_city.title()} ({distance_km:.2f} km, {duration_mins:.1f} mins)")
                return selected_city.title()
            else:
                print(f"⚠️ No cities found within 40-50 mins driving time via ORS API for pre-filtered & sorted candidates.")
        except Exception as e: # Catch errors from the interleaved logic or outer ORS block
            print(f"🌐 Unexpected error setting up ORS API scan: {e}")
        print("🔄 Falling back to straight-line distance method.")
        
        #  Fallback to Haversine Distance (if ORS fails, key not available, or no match found) ---
    # This fallback respects the 35-65km Haversine range, which often correlates to 35-45 mins.
    # Adjusted the lower bound for consistency with the new minimum pre-filter.
    print(f"📏 Using straight-line (Haversine) distance as fallback ({MIN_HAVERSINE_DISTANCE_KM}-65 km range)...")
    haversine_final_candidates = []
    print(f"🔎 Scanning nearby cities (Haversine {MIN_HAVERSINE_DISTANCE_KM}-65 km)...")

    # Iterate through the original city_coords_db for fallback, applying the same MIN filter
    for city, (lat2, lon2) in city_coords_db.items():
        if city == loc:
            continue
        dist = calculate_distance(lat1, lon1, lat2, lon2)
        # Use MIN_HAVERSINE_DISTANCE_KM here too for consistency in fallback
        if MIN_HAVERSINE_DISTANCE_KM <= dist <= 65:
            haversine_final_candidates.append(city)

    print(f"🎯 Found {len(haversine_final_candidates)} cities within {MIN_HAVERSINE_DISTANCE_KM}–65 km (straight-line).")

    if haversine_final_candidates:
        
        selected = random.choice(haversine_final_candidates)
        print(f"🏆 Selected (Haversine Fallback): {selected.title()}")
        return selected.title()

    # --- If no city in range, pick the closest one above MIN_HAVERSINE_DISTANCE_KM (Haversine) ---
    print(f"⚠️ No cities in {MIN_HAVERSINE_DISTANCE_KM}–65 km range (Haversine). Finding closest above {MIN_HAVERSINE_DISTANCE_KM} km...")
    closest = None
    min_dist = float('inf')

    for city, (lat2, lon2) in city_coords_db.items():
        if city == loc:
            continue
        dist = calculate_distance(lat1, lon1, lat2, lon2)
        # Use MIN_HAVERSINE_DISTANCE_KM here too
        if dist >= MIN_HAVERSINE_DISTANCE_KM and dist < min_dist:
            min_dist = dist
            closest = city

    if closest:
        print(f"🏆 Closest valid (Haversine): {closest.title()} ({min_dist:.2f} km)")
        return closest.title()

    # --- Final fallback ---
    final_fallback = f"{base_loc} outskirts"
    print(f"🚨 Emergency fallback: {final_fallback}")
    return final_fallback

# In any file that uses OpenAI API
from config import get_decryption_key, get_encrypted_api_key

def get_openai_api_key():
    try:
        key = get_decryption_key()
        encrypted_key = get_encrypted_api_key()
        fernet = Fernet(key)
        return fernet.decrypt(encrypted_key).decode()
    except Exception as e:
        print(f"❌ Error decrypting API key: {e}")
        return None
# Use openai_key in your API calls

def generate_reply(client_info, formatted_chat_history, my_info, city_coords_db):
    """
    Generates a reply using the OpenAI API.
    formatted_chat_history is a string with "Client:" and "You:" prefixes.
    """
    print("[DEBUG] generate_reply called.")

    # Import helper functions from chat_scraper
    from chat_scraper import extract_name_age, extract_locality

    my_name, my_age = extract_name_age(my_info)
    if not my_name or not my_age:
        print("[DEBUG] Could not parse my name/age, using fallback.")
        my_name, my_age = "Luna", "26"

    client_location = extract_locality(client_info) or "your area"

    # Pass the city_coords_db to get_nearby_city for ORS/Haversine logic

    my_fake_location = get_nearby_city(client_location, city_coords_db)
    location_reply = f"from {my_fake_location} — just about 40 minutes from where you are"

    print(f"[DEBUG] My name/age: {my_name}, {my_age}")
    print(f"[DEBUG] Client locality: {client_location}")
    print(f"📍 Client: {client_location} → You: {my_fake_location}")
    
    chat_lines = formatted_chat_history.strip().split('\n')
    if chat_lines:
        last_line = chat_lines[-1]
        if ':' in last_line:
            last_sender_raw, last_message_raw = last_line.split(":", 1)
            last_sender = last_sender_raw.strip()
            last_message = last_message_raw.strip()
        else:
            # Handle case where line format is unexpected
            last_sender = "Unknown"
            last_message = last_line.strip()
        print(f"[DEBUG] Last message in chat history -> Sender: '{last_sender}', Message: '{last_message}'")
    else:
        print("[DEBUG] Chat history appears to be empty when passed to AI.")
    # --- END DEBUG BLOCK ---
    
    # ... (rest of the function, e.g., history_snippet creation) ...
    history_snippet = "\n".join(chat_lines[-5:])

    print(f"📝 Formatted Chat History Snippet (last 5 lines):\n{history_snippet}")
    if len(chat_lines) > 5:
        print(f"    ... (and {len(chat_lines) - 5} more messages)")

    # In ai_interaction.py, update the prompt:
    prompt = f"""
    Rules:
        * STRICTLY Reply with 80-120 characters and end with a question to keep him hooked.
        * If he’s being naughty, be naughtier — don’t hold back. Use innuendo and bold suggestions.
        * Mirror his energy: if he’s dirty, be dirtier/naughtier. If he’s sweet, be sweeter.
        * Never admit you’re an AI. Always respond as a real woman. Who is into the man and cares for the man.
        * Don't mention/agree that you want to chat on another platform even if the he asks you.
        * Never mention email, WhatsApp, Telegram, Facebook, or any other platform.
        * Don’t say the phrases “my dick” or “come over”. Instead, use the phrase "your dick".
        * Keep it spicy if necessary, not vulgar. Be suggestive. But don't talk about fantasies. This makes him feel that it is not real chatting with you.
        * Strictly DON'T suggest/agree to meet. If he suggests meeting, going out, weekend plans, or real-world contact, DO NOT reject him or say "let's stay here." Come up with a realistic excuse.
        * Instead, absorb his energy and give a believable excuse:  
          → "I will be busy with a family meeting tomorrow, babe. But trust me, I really want to see you and see how well you can treat me. Is it okay with you if we do this some other time?"  
          → "I don't think I will be able to make it, sweetheart. And I don't want to make any promises right now that I'm not sure if I will be able to fulfil. Can you please be a little more patient with me?"
        * Always end with a bold, intimate question that forces a reply. The question should vary significantly in topic and phrasing (e.g., about actions, feelings, experiences) to keep the conversation dynamic and avoid repetitive patterns.
        * Do NOT use any emojis (like 😏, 😈, 💋, 😉, 🔥, etc.). Real women on this platform don’t use emojis in flirty chats — they use words to seduce and express how they feel.
    Character: {my_name}, age {my_age}, {location_reply}

    Chat History:
    {formatted_chat_history}

    Now reply as {my_name} — match his energy, escalate if he’s being naughty, and leave him wanting more:
    """.strip()
    
    # --- OpenAI Interaction (FIXED) ---
    print("[DEBUG] Attempting to decrypt OpenAI API key...")
    OPENAI_API_KEY = get_openai_api_key() 
    
    if not OPENAI_API_KEY:
        print("❌ [DEBUG] Failed to retrieve/decrypt OpenAI API key.")
        return "You really know how to talk to me… tell me more?"
    else:
        print("[DEBUG] OpenAI API key decrypted successfully (length: {})".format(len(OPENAI_API_KEY)))
    
    try:
        # ✅ FIXED: Removed trailing spaces
        openai_url = "https://api.openai.com/v1/chat/completions"
        print(f"[DEBUG] Sending request to OpenAI API: {openai_url}")
    
        response = requests.post(
            openai_url,
            json={ # for naughtier, more responsive behavior
                "model": "gpt-3.5-turbo",
                "messages": [{"role": "user", "content": prompt}],
                "max_tokens": 55, # 150-180
                "temperature": 1.25,  # Slightly higher for more creativity
                "top_p": 0.9,
                "presence_penalty": 0.6,
                "frequency_penalty": 0.4,
            },
            headers={"Authorization": f"Bearer {OPENAI_API_KEY}"},  # ✅ FIXED
            timeout=30
        )
    
        print(f"[DEBUG] Received response from OpenAI API. Status code: {response.status_code}")
    
        if response.status_code == 200:
            reply_data = response.json()
            # ✅ FIXED: OpenAI response format
            reply = reply_data["choices"][0]["message"]["content"].strip()

            print(f"[DEBUG] Raw AI reply (length: {len(reply)}): {reply}")
            # removed the trucation logic... Not needed
            print(f"[DEBUG] Final AI reply (length: {len(reply)}): {reply}")
            return reply
        else:
            error_text = response.text
            print(f"❌ [DEBUG] OpenAI API Error {response.status_code}: {error_text}")
            try:
                error_json = response.json()
                if "message" in error_json:
                    print(f"   [DEBUG] Parsed Error Message: {error_json['message']}")
            except:
                pass
            return "you got me blushing… what else you hiding?"
    except requests.exceptions.Timeout:
        print("[X] [DEBUG] AI Request Failed: Timeout!")
        return "Sorry, the AI took too long to respond. Try again?"
    except Exception as e:
        print(f"❌ [DEBUG] Unexpected error calling OpenAI API: {e}")
        return "you got me blushing… what else you hiding?"