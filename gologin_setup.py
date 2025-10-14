"""
Handles interaction with the GoLogin Local API.
Replaces morelogin.py.
This version uses the modern /browser/start-profile endpoint.
"""
import requests
import time
import os
import json
import urllib.parse # Import for parsing URLs
from config import GOLOGIN_BASE_URL 

def is_profile_running(profile_id):
    """
    Check if the specified GoLogin profile is currently running via the Local API.
    Returns (is_running: bool, ws_url: str or None)
    """
    token_key = os.getenv("GOLOGIN_TOKEN_KEY")
    if not profile_id:
        print("❌ [GoLogin API] Profile ID is missing (not set in environment).")
        return False, None
    if not token_key:
        print("❌ [GoLogin API] Token Key is missing (not set in environment).")
        return False, None

    info_url = f"{GOLOGIN_BASE_URL}/profile/info?profileId={profile_id}"
    try:
        # Include token in headers for authentication if required by your GoLogin version
        headers = {
            "Authorization": f"Bearer {token_key}",
            "Content-Type": "application/json"
        }
        resp = requests.get(info_url, headers=headers, timeout=10)
        print(f"[GoLogin API] Info check: {info_url}, Status Code: {resp.status_code}")

        if resp.status_code == 200:
            response_data = resp.json()
            status = response_data.get("status") # 'running' or 'stopped'
            ws_url = response_data.get("wsUrl") # Websocket URL if running
            print(f"[GoLogin API] Status from API: {status}, wsUrl: {ws_url}")
            if status == "running" and ws_url:
                return True, ws_url
            elif status == "stopped":
                return False, None
            else:
                print(f"[GoLogin API] Unexpected status from API: {status}")
                return False, None
        else:
            print(f"[GoLogin API] Info check failed with HTTP {resp.status_code}: {resp.text}")
            # If it's a 404 or 405, it likely means the API is not running or incorrect port
            if resp.status_code in [404, 405]:
                 print(f"[GoLogin API] API endpoint might be incorrect or GoLogin desktop app is not running/listening on {GOLOGIN_BASE_URL}. Please check the GoLogin application and its settings.")
            return False, None

    except requests.exceptions.ConnectionError:
        print(f"[GoLogin API] Connection failed. Is GoLogin desktop app running and Local API enabled on {GOLOGIN_BASE_URL}?")
        return False, None
    except requests.exceptions.Timeout:
        print(f"[GoLogin API] Request timed out while checking info for {profile_id}.")
        return False, None
    except requests.exceptions.RequestException as e:
        print(f"[GoLogin API] An error occurred during info check: {e}")
        return False, None
    except json.JSONDecodeError:
        print(f"[GoLogin API] Failed to decode JSON response from info check: {resp.text}")
        return False, None

def get_gologin_browser():
    """
    Starts the GoLogin profile via Local API and returns the debugger address.
    Expects the GoLogin desktop application to be running.
    Exits if the profile cannot be started.
    """
    profile_id = os.getenv("GOLOGIN_PROFILE_ID")
    token_key = os.getenv("GOLOGIN_TOKEN_KEY")

    # 1. Validate required variables (re-checking here as a final safety)
    if not profile_id:
        print("❌ [GoLogin API] Missing GOLOGIN_PROFILE_ID environment variable. Check your setup.")
        return None
    if not token_key:
        print("❌ [GoLogin API] Missing GOLOGIN_TOKEN_KEY environment variable. Check your setup.")
        return None

    print(f"[GoLogin API] Attempting to manage profile: {profile_id}")
    print("[GoLogin API] Attempting to start profile via Local API...")

    # 3. Launch via Local API using the modern endpoint
    start_url = f"{GOLOGIN_BASE_URL}/browser/start-profile" # this was where the bug was bannaa! 😓
    print(f"[GoLogin API] Calling GoLogin Local API to START: {start_url}")

    try:
        # Prepare the JSON body
        payload = {
            "profileId": profile_id,
            "sync": True # Set to True to sync profile data
        }

        # Include token in headers for authentication
        headers = {
            "Authorization": f"Bearer {token_key}",
            "Content-Type": "application/json"
        }

        resp = requests.post(start_url, json=payload, headers=headers, timeout=60) # Increased timeout for startup
        print(f"[GoLogin API] Start request completed. Status Code: {resp.status_code}")
        print(f"[GoLogin API] Start response: {resp.text[:300]}...") # Log first 300 chars of response

        if resp.status_code == 200:
            response_data = resp.json()
            ws_url = response_data.get("wsUrl")
            if ws_url:
                print("[GoLogin API] Profile started successfully via Local API.")
                print("[GoLogin API] NOTE: The GoLogin desktop app UI might not update instantly, but the profile is running.")
            else:
                print(f"[GoLogin API] API reported success but did not return a WebSocket URL. Response: {response_data}")
                return None
        else:
            print(f"[GoLogin API] Start request failed with HTTP {resp.status_code}: {resp.text}")
            if resp.status_code == 404:
                print(f"[GoLogin API] ERROR: The API endpoint '{start_url}' was not found. Is the profile ID '{profile_id}' correct? Is the GoLogin desktop app running and Local API enabled?")
            elif resp.status_code == 401:
                print(f"[GoLogin API] ERROR: Unauthorized. Check if your GOLOGIN_TOKEN_KEY is correct for the specified profile.")
            elif resp.status_code == 403:
                print(f"[GoLogin API] ERROR: Forbidden. Check API permissions or profile access in GoLogin app.")
            else:
                print(f"[GoLogin API] ERROR: Unexpected response code {resp.status_code}.")
            return None

    except requests.exceptions.ConnectionError:
        print(f"[GoLogin API] Connection failed while trying to start profile. Is the GoLogin desktop app running and Local API enabled on {GOLOGIN_BASE_URL}?")
        return None
    except requests.exceptions.Timeout:
        print(f"[GoLogin API] Request timed out while starting profile {profile_id}. It might take longer than 60 seconds or the GoLogin app is unresponsive.")
        return None
    except requests.exceptions.RequestException as e:
        print(f"[GoLogin API] An error occurred during profile start request: {e}")
        return None
    except json.JSONDecodeError:
        print(f"[GoLogin API] Failed to decode JSON response from start request: {resp.text}")
        return None

    # 4. Parse the port from wsUrl returned by the API
    if not ws_url:
         print("[GoLogin API] Failed to get WebSocket URL after attempting start.")
         return None

    try:
        parsed = urllib.parse.urlparse(ws_url)
        port = parsed.port or 9222 # Default to 9222 if port not found in URL
        debugger_address = f"localhost:{port}"
        print(f"[GoLogin API] ✅ Calculated debugger address: {debugger_address}")
        # Allow some time for the browser process to fully initialize after API call
        print("[GoLogin API] Waiting for browser to be ready...")
        time.sleep(5) # Increased wait time slightly
        print("[GoLogin API] Browser should be ready.")
        return debugger_address
    except Exception as e:
        print(f"[GoLogin API] Failed to parse WebSocket URL '{ws_url}': {e}")
        return None

# this is just for testing, ahh but its work is done!
# Example usage (if run directly for testing):
# if __name__ == "__main__":s
    # print("[TEST] Attempting to get GoLogin browser debugger address via Local API...")
    # print(f"[TEST] Using Base URL: {GOLOGIN_BASE_URL}")
    # debugger_address = get_gologin_browser()
    # if debugger_address:
        # print(f"[TEST] SUCCESS! Got debugger address: {debugger_address}")
        # print(f"[TEST] You can now connect Selenium to: {debugger_address}")
    # else:
        # print("[TEST] FAILED to get debugger address. Check logs above.")
        # print("[TEST] Ensure GoLogin desktop app is running and Local API is enabled.")
