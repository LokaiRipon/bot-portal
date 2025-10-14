# config.py
"""Configuration settings and constants for the bot."""
import os
import sys
from pathlib import Path
import base64


# --- Application Paths ---
def get_application_path():
    """Get the base path where the script or bundled executable resides."""
    if getattr(sys, 'frozen', False):
        application_path = os.path.dirname(sys.executable)
    else:
        application_path = os.path.dirname(os.path.abspath(__file__))
    return application_path

def resource_path(relative_path):
    """Get absolute path to resource, works for dev and for PyInstaller exe."""
    if hasattr(sys, '_MEIPASS'):
        base_path = Path(getattr(sys, '_MEIPASS', Path(__file__).parent))
    else:
        base_path = Path(__file__).parent
    return base_path / relative_path

# --- I make Licensing Configurations here ---
LICENSING_SERVER_BASE_URL = "https://license-server-iul9.onrender.com" # TODO: Update for production that is for MK's server

# ORS API Key (Base64 encoded)
ORS_API_KEY_B64 = "ZXlKdmNtY2lPaUkxWWpOalpUTTFPVGM0TlRFeE1UQXdNREZqWmpZeU5EZ2lMQ0pwWkNJNklqbGpOR0k0WXpkbE1XWXlNVFJsWVdSaVkyWXhOek5oWmpnMk56Wm1aRFZtSWl3aWFDSTZJbTExY20xMWNqWTBJbjA9"

# OpenAI API Key (Fernet encrypted, then Base64 encoded)
DECRYPTION_KEY_B64 = "U1JEU01kbWtMcWI2aTVzMkxxcmFzNl9IdGlnZ3hDU24wOHB6VlhjV21Udz0="
ENCRYPTED_API_KEY_B64 = "Z0FBQUFBQm83aVJkclk5X3VMYm9PLUtuZVJnLUc2MHlDc3kzUTdUQ1BRSWFubDJUWjNqSG8yN1JhMTRHZHBOWjduS2FiN3otSGFFaUhISjlWbURyTTV1T0I3TWEtYmdPdVZTZTBKNWk5YzhqcHBhaGxubG5rZTFjdGRieThTNjVocTNsSDVjdXJZS1lyaWV6NGpNTHN1ZDRTNUJKSy11R2hxandNbDFPTGUwNWlCUUYyRmthRWlWWi1YekdSb3BVRFBpRm9xMXl1TE5CeWJOMjJtVi1UQUozRVpWU0ZSdUhSMzBIaUhfMEtRN2FSQnlNTVViWVpLaXhsYjFrOC1vRTVqVVFzWHNiRUt4dzdGRWtLOXVjVDdRd2VQQ3FWZWNtcGVaWDAxNGs0Ny1IYk5raHNRZlIxLUU9"

# --- Functions to decode keys ---
def get_ors_api_key():
    return base64.b64decode(ORS_API_KEY_B64).decode()

def get_decryption_key():
    return base64.b64decode(DECRYPTION_KEY_B64)

def get_encrypted_api_key():
    return base64.b64decode(ENCRYPTED_API_KEY_B64)

# --- Web Element Selectors. Don't touch this! ---
PROFILE_LEFT_SELECTOR = '.customer'
PROFILE_RIGHT_SELECTOR = '.profile'
CHAT_HISTORY_SELECTOR = '.w-full'
INPUT_BOX_SELECTOR = '#textarea-id'

GOLOGIN_BASE_URL = "http://127.0.0.1:36912" # TODO: Never Touch this!!