"""
Handles interaction with the GoLogin using the official gologin library.
Replaces the previous custom API interaction.
"""
import os
import time
import urllib.parse # Import for parsing URLs
from gologin.gologin import GoLogin
from config import GOLOGIN_BASE_URL # e.g., "http://127.0.0.1:3001" - Used for API calls if needed, but less critical now

# --- Configuration ---
# Retrieve from environment variables set by gui.py
GOLOGIN_PROFILE_ID = "68ecbd3596dd615464f4ef92"
GOLOGIN_TOKEN_KEY = "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.eyJzdWIiOiI2OGVjYmQzNTk2ZGQ2MTU0NjRmNGVmMDMiLCJ0eXBlIjoiZGV2Iiwiand0aWQiOiI2OGVjYzg0YjFlZTM2NzY0MTc3ZmI1MWIifQ.rptTybcV0Bx2q9tnrJDVCqXf1tWyv78RxUjzT-zJ4Ec"

# Keep a reference to the GoLogin object for potential cleanup
_gologin_instance = None
_profile_path = None

def get_gologin_browser():
    """
    Starts the GoLogin profile using the official library and returns the debugger address.
    Exits if the profile cannot be started.
    """
    global _gologin_instance, _profile_path

    # 1. Validate required variables
    if not GOLOGIN_PROFILE_ID:
        print("❌ [GoLogin] Missing GOLOGIN_PROFILE_ID environment variable. Check your setup.")
        return None
    if not GOLOGIN_TOKEN_KEY:
        print("❌ [GoLogin] Missing GOLOGIN_TOKEN_KEY environment variable. Check your setup.")
        return None

    print(f"[GoLogin] Attempting to manage profile: {GOLOGIN_PROFILE_ID}")

    try:
        # 2. Initialize GoLogin object
        print("[GoLogin] Initializing GoLogin object...")
        _gologin_instance = GoLogin({
            "token": GOLOGIN_TOKEN_KEY,
            "profile_id": GOLOGIN_PROFILE_ID,
            "local": True, # Explicitly state it's a local profile (default)
            # You can add other options here if needed, like 'tmpdir' for temp profile storage
        })

        # 3. Start the profile
        print("[GoLogin] Starting GoLogin profile...")
        start_result = _gologin_instance.start() # This launches the browser process
        print(f"[GoLogin] Profile started. Start result: {start_result}")

        # 4. Get the debugger address from the start_result
        debugger_url = None
        if isinstance(start_result, str):
            # Check if it's a simple host:port string (like "127.0.0.1:XXXX")
            if ":" in start_result and start_result.count(":") == 1:
                # It's likely a host:port string
                parts = start_result.split(":")
                if len(parts) == 2 and parts[0] and parts[1].isdigit():
                    host = parts[0]
                    port = int(parts[1])
                    debugger_url = f"ws://{host}:{port}"
                else:
                    raise ValueError(f"Invalid host:port format: {start_result}")
            else:
                # Assume it's a full WebSocket URL
                debugger_url = start_result
        else:
            # If start_result is not a string, try to extract the wsUrl from it if possible.
            if hasattr(start_result, 'wsUrl'):
                debugger_url = start_result.wsUrl
            elif isinstance(start_result, dict) and 'wsUrl' in start_result:
                debugger_url = start_result['wsUrl']
            else:
                # Fallback: Try to get the debugging URL from the profile status
                print("[GoLogin] Could not determine debugger URL from start result. Trying alternative methods.")
                # You could implement a retry mechanism or use the /json/version endpoint directly
                # For now, raise an error
                raise RuntimeError("Failed to get debugger URL from start result.")

        if not debugger_url:
            raise RuntimeError("Failed to get debugger URL after trying multiple methods.")

        # 5. Parse the debugger URL to extract the port
        # Assuming the URL is in the format ws://127.0.0.1:XXXX/...
        parsed_url = urllib.parse.urlparse(debugger_url)
        debugger_port = parsed_url.port
        if debugger_port is None:
            raise ValueError(f"Could not parse port from debugger URL: {debugger_url}")

        debugger_address = f"127.0.0.1:{debugger_port}" # Use 127.0.0.1 for localhost
        print(f"[GoLogin] ✅ Calculated debugger address: {debugger_address}")

        # 6. Wait a bit for the browser to fully initialize
        print("[GoLogin] Waiting for browser to be ready...")
        time.sleep(5) # Increased wait time slightly
        print("[GoLogin] Browser should be ready.")

        return debugger_address

    except Exception as e:
        print(f"[GoLogin] FAILED to start profile or get debugger address: {e}")
        # Attempt to stop the instance if it was started but failed later
        if _gologin_instance:
            try:
                print("[GoLogin] Attempting to stop profile due to startup error...")
                _gologin_instance.stop()
                print("[GoLogin] Profile stopped after error.")
            except:
                pass # Ignore errors during cleanup if startup failed
        return None

def stop_gologin_profile():
    """
    Stops the currently running GoLogin profile instance.
    Should be called when the script is shutting down.
    """
    global _gologin_instance, _profile_path
    if _gologin_instance:
        try:
            print("[GoLogin] Stopping profile...")
            _gologin_instance.stop()
            print("[GoLogin] Profile stopped.")
        except Exception as e:
            print(f"[GoLogin] Error stopping profile: {e}")
        finally:
            _gologin_instance = None
            _profile_path = None
    else:
        print("[GoLogin] No profile instance found to stop.")

# Example usage (if run directly for testing):
if __name__ == "__main__":
    # Ensure GoLogin is running, Local API is enabled, and environment variables are set before running this
    print("[TEST] Attempting to get GoLogin browser debugger address...")
    print(f"[TEST] Using Profile ID: {GOLOGIN_PROFILE_ID}")
    print(f"[TEST] Using Base URL: {GOLOGIN_BASE_URL}")
    # Note: Token key is not printed for security reasons
    debugger_address = get_gologin_browser()
    if debugger_address:
        print(f"[TEST] SUCCESS! Got debugger address: {debugger_address}")
        print(f"[TEST] You can now connect Selenium to: {debugger_address}")
        print(f"[TEST] Remember to call stop_gologin_profile() when done.")
        # Example cleanup
        input("Press Enter to stop the profile...")
        stop_gologin_profile()
    else:
        print("[TEST] FAILED to get debugger address. Check logs above.")