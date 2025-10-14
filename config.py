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
DECRYPTION_KEY_B64 = "aEpySVR6S3FGdm16MVJhcHpMQ1ZSSXA3cW96NUFGeG5NdXN5bHJVdDB6ST0="
ENCRYPTED_API_KEY_B64 = "Z0FBQUFBQm95OXVwWEFMVXNoWkE5TldUdFo3QVRaV1h1RElXWFc2YUtmWkFISXd6QjhWZDQtNWZFVHg0WUVkdUYyaWRqcC1CLUczd0dRalpyYnYxanJidnR2bHFCSjNrN3laTHVlSlJnZkd4Z1NoY2xTNG95MzVOQnpVSW1zNkJWN3lwV2VvbWI5eHRYU3U2dF9kbTdDaEJiMldXOW5kQnQyZEwxLTk5MnI3NGt6enk2bHI1c093NVloYXE1ODhtSU04U04wTnNCZEJxZ1dod2RTdUxnbXFLVzE4RHNQQ1lHdEF2dDhaU08tUzBDWFdSWlczcjVzQXZpWkM5RHhYYkhEUHhaR3h0dmtQXzNkS0UtM09rTVZLdndzTkNwYldDcktXZW1yUXpiWmk3NDc4X0tyM0h6STA9"

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