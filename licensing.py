# licensing.py
"""Handles license activation, validation, hardware ID generation, and device switching."""
import uuid
import platform
import hashlib
import requests
import sys
import random
from typing import Tuple, Optional
from config import LICENSING_SERVER_BASE_URL
try:
    import wmi
    WMI_AVAILABLE = True
except ImportError:
    print("[LICENSING] 'wmi' library not found. Install with 'pip install wmi' for better Windows HW ID.")
    WMI_AVAILABLE = False

# Define tier limits
TIER_LIMITS = {
    'BASIC': 3, # 3 messages for testing
    'BRONZE': 5, # 5 messages for testing
    'PREMIUM': 10 # 10 messages for testing
}

def generate_hardware_id() -> str:
    """
    Generates a relatively stable hardware identifier for the Windows machine.
    """
    hw_id_components = []
    try:
        mac = ':'.join(['{:02x}'.format((uuid.getnode() >> elements) & 0xff) for elements in range(0,2*6,2)][::-1])
        hw_id_components.append(mac)
    except Exception as e:
        print(f"[LICENSING] Error getting MAC address: {e}. Using fallback.")
        hw_id_components.append("fallback_mac")

    machine_guid = None
    if WMI_AVAILABLE:
        try:
            c = wmi.WMI()
            for item in c.Win32_ComputerSystemProduct():
                if item.UUID and item.UUID != "00000000-0000-0000-0000-000000000000":
                    machine_guid = item.UUID
                    break
            if not machine_guid:
                 for item in c.Win32_ComputerSystem():
                     if item.SerialNumber and item.SerialNumber.strip() and item.SerialNumber.strip().upper() != "SYSTEM SERIAL NUMBER":
                         machine_guid = item.SerialNumber.strip()
                         break
            if machine_guid:
                hw_id_components.append(machine_guid)
                print(f"[LICENSING] Used Windows Machine GUID/Serial for HW ID.")
            else:
                 print(f"[LICENSING] Windows Machine GUID/Serial not found or is default.")
        except Exception as e:
            print(f"[LICENSING] Error accessing Windows Machine GUID via WMI: {e}")

    try:
        node_name = platform.node()
        if node_name and node_name != "Unknown":
            hw_id_components.append(node_name)
        platform_id = f"{platform.system()}_{platform.release()}"
        if platform_id and platform_id not in ["_", "Unknown_"]:
            hw_id_components.append(platform_id)
    except Exception as e:
         print(f"[LICENSING] Error getting platform info for HW ID: {e}")

    if not hw_id_components:
        print(f"[LICENSING] No hardware components found. Using UUID node fallback.")
        fallback_id = hashlib.sha256(str(uuid.getnode()).encode('utf-8')).hexdigest()
        print(f"[LICENSING] Final fallback HW ID (prefix): {fallback_id[:16]}...")
        return fallback_id

    hw_string = "|".join(hw_id_components).encode('utf-8')
    hw_id = hashlib.sha256(hw_string).hexdigest()
    print(f"[LICENSING] Generated HW ID (prefix): {hw_id[:16]}... (Components used: {len(hw_id_components)})")
    return hw_id

def activate_license(key: str, hw_id: str) -> Tuple[bool, str]:
    """
    Attempts to activate the license key for the given hardware ID.
    Calls the FastAPI server's /api/activate endpoint.
    """
    url = f"{LICENSING_SERVER_BASE_URL}/api/activate"
    payload = {
        "key": key,
        "hw_id": hw_id
    }
    headers = {'Content-Type': 'application/json'}
    try:
        print(f"[LICENSING] Attempting to activate license key ending in ...{key[-8:]}")
        response = requests.post(url, json=payload, headers=headers, timeout=15)
        response.raise_for_status()
        data = response.json()
        status = data.get("status")
        message = data.get("message", "")
        expiry_date_str = data.get("expiry_date")
        print(f"[LICENSING] Activation response: {status} - {message}")
        if status == "activated":
            print(f"✅ License activated successfully. Expires: {expiry_date_str}")
            return True, expiry_date_str
        elif status == "already_activated":
            print(f"ℹ️ License already activated. Message: {message}. Proceeding to check...")
            return True, expiry_date_str
        elif status == "device_mismatch":
            print(f"❌ License activation failed: Device mismatch. {message}")
            return False, "device_mismatch"
        elif status == "expired":
            print(f"❌ License activation failed: Key is expired. {message}")
            return False, "expired"
        elif status == "invalid":
             print(f"❌ License activation failed: Invalid key. {message}")
             return False, "invalid"
        else:
            print(f"❌ Unexpected activation status from server: {status}. Message: {message}")
            return False, f"unexpected_status: {status}"
    except requests.exceptions.RequestException as e:
        print(f"❌ Error connecting to licensing server for activation: {e}")
        return False, "connection_error"
    except Exception as e:
        print(f"❌ Unexpected error during license activation: {e}")
        return False, "unexpected_error"

def check_license(key: str, hw_id: str) -> Tuple[bool, str, str, int, int, str, str]:
    """
    Checks the validity and device match of an already activated license key.
    Calls the FastAPI server's /api/check endpoint.
    Returns: (is_valid, expiry_date, tier, message_limit, messages_used, reset_date, message_status)
    """
    url = f"{LICENSING_SERVER_BASE_URL}/api/check"
    payload = {
        "key": key,
        "hw_id": hw_id
    }
    headers = {'Content-Type': 'application/json'}
    try:
        print(f"[LICENSING] Checking license key ending in ...{key[-8:]}")
        response = requests.post(url, json=payload, headers=headers, timeout=15)
        response.raise_for_status()
        data = response.json()
        status = data.get("status")
        message = data.get("message", "")
        expiry_date_str = data.get("expiry_date")

        # Extract new fields from the server response
        tier = data.get("tier", "BASIC") # Default to BASIC if not provided by server
        message_limit = data.get("message_limit", TIER_LIMITS.get(tier, 150))
        messages_used = data.get("messages_used", 0)
        reset_date_str = data.get("reset_date") # Can be None
        message_status = data.get("message_status", "ok")

        print(f"[LICENSING] Check response: {status} - {message}")
        print(f"[LICENSING] Tier: {tier}, Messages: {messages_used}/{message_limit}, Reset Date: {reset_date_str}, Status: {message_status}")

        if status == "ok":
            print(f"✅ License check passed. Valid and matches device. Expires: {expiry_date_str}")
            return True, expiry_date_str, tier, message_limit, messages_used, reset_date_str, message_status
        elif status == "expired":
            print(f"❌ License check failed: Key is expired. {message}")
            return False, "expired", "None", 0, 0, "None", "None"
        elif status == "device_mismatch":
            print(f"❌ License check failed: Device mismatch. {message}")
            return False, "device_mismatch", "None", 0, 0, "None", "None"
        elif status == "invalid":
             print(f"❌ License check failed: Invalid key. {message}")
             return False, "invalid", "None", 0, 0, "None", "None"
        else:
            print(f"❌ Unexpected check status from server: {status}. Message: {message}")
            return False, f"unexpected_status: {status}", "None", 0, 0, "None", "None"
    except requests.exceptions.RequestException as e:
        print(f"❌ Error connecting to licensing server for check: {e}")
        return False, "connection_error", "None", 0, 0, "None", "None"
    except Exception as e:
        print(f"❌ Unexpected error during license check: {e}")
        return False, "unexpected_error", "None", 0, 0, "None", "None"

def request_deactivation(license_key: str, user_code: str) -> bool:
    """
    Requests deactivation of the license using the code provided by the user.
    Calls the FastAPI server's /api/request_deactivate endpoint.
    """
    deactivation_url = f"{LICENSING_SERVER_BASE_URL}/api/request_deactivate"
    deactivation_payload = {
        "key": license_key,
        "code": user_code
    }
    headers = {'Content-Type': 'application/json'}
    try:
        print(f"[LICENSING] Sending deactivation request with code...")
        response = requests.post(deactivation_url, json=deactivation_payload, headers=headers, timeout=15)
        response.raise_for_status()
        deactivation_data = response.json()
        deactivation_status = deactivation_data.get("status")
        deactivation_message = deactivation_data.get("message", "")
        print(f"[LICENSING] Deactivation response: {deactivation_status} - {deactivation_message}")
        if deactivation_status == "success":
            print("✅ Deactivation successful. License is now unlinked from the previous device.")
            return True
        else:
            print(f"❌ Deactivation failed: {deactivation_message}")
            return False
    except requests.exceptions.RequestException as e:
        print(f"❌ Error connecting to licensing server for deactivation: {e}")
        return False
    except Exception as e:
        print(f"❌ Unexpected error during license deactivation request: {e}")
        return False

def handle_device_mismatch(license_key: str, hw_id: str) -> bool:
    """
    Handles the device mismatch scenario by prompting the user for a code
    and requesting deactivation from the server.
    """
    from gui import prompt_for_deactivation_code
    user_code = prompt_for_deactivation_code()
    if not user_code:
        return False
    if request_deactivation(license_key, user_code):
        print("[LICENSING] Retrying local activation after successful deactivation...")
        return True
    else:
        print("[LICENSING] Deactivation failed. Cannot proceed.")
        return False

def handle_license_validation(license_key: str, hw_id: str) -> bool:
    """
    Handles the full license validation process, including
    activation, checking, and user interaction for device switching.
    """
    print("🔍 Validating Bot License...")
    # First, try to check the license directly (this will handle device mismatch)
    print("[LICENSING] Performing initial license check...")
    check_success, check_result, tier, message_limit, messages_used, reset_date, message_status = check_license(license_key, hw_id)
    if check_success:
        # Store license info globally for access in main app
        global CURRENT_LICENSE_INFO
        CURRENT_LICENSE_INFO = {
            'valid': True,
            'tier': tier,
            'message_limit': message_limit,
            'messages_used': messages_used,
            'reset_date': reset_date,
            'message_status': message_status,
            'expiry_date': check_result
        }

        print(f"[LICENSING] License validated successfully. Tier: {tier}, Messages: {messages_used}/{message_limit}")

        # Check if message limit is reached
        if message_status == "limit_reached":
            from gui import show_license_error
            show_license_error(f"Message limit reached! Your {tier} tier allows {message_limit} messages per month. Please upgrade or wait for reset.")
            return False

        return True
    else:
        if check_result == "device_mismatch":
            # Handle device mismatch
            if handle_device_mismatch(license_key, hw_id):
                # After successful deactivation, try to activate on current device
                print("[LICENSING] Attempting to activate on current device after deactivation...")
                activation_success, activation_result = activate_license(license_key, hw_id)
                if activation_success:
                    print("[LICENSING] Successfully activated on current device!")
                    # Need to re-check to get updated info after activation
                    check_success, check_result, tier, message_limit, messages_used, reset_date, message_status = check_license(license_key, hw_id)
                    if check_success:
                        CURRENT_LICENSE_INFO = {
                            'valid': True,
                            'tier': tier,
                            'message_limit': message_limit,
                            'messages_used': messages_used,
                            'reset_date': reset_date,
                            'message_status': message_status,
                            'expiry_date': check_result
                        }
                    return True
                else:
                    print(f"[LICENSING] Failed to activate after deactivation: {activation_result}")
                    from gui import show_license_error
                    show_license_error(f"Failed to activate license after deactivation: {activation_result}")
                    return False
            else:
                return False
        elif check_result == "expired":
            from gui import show_license_error
            show_license_error("Your Bot License has EXPIRED. Please contact the vendor to purchase a new subscription.")
            return False
        elif check_result == "invalid":
            from gui import show_license_error
            show_license_error("INVALID Bot License Key provided. Please check the key and try again, or contact the vendor.")
            return False
        else:
            # If check failed for other reasons, try activation
            print("[LICENSING] Check failed, attempting activation...")
            activation_success, activation_result = activate_license(license_key, hw_id)
            if activation_success:
                print("[LICENSING] Activation successful!")
                # Need to re-check to get updated info after activation
                check_success, check_result, tier, message_limit, messages_used, reset_date, message_status = check_license(license_key, hw_id)
                if check_success:
                    CURRENT_LICENSE_INFO = {
                        'valid': True,
                        'tier': tier,
                        'message_limit': message_limit,
                        'messages_used': messages_used,
                        'reset_date': reset_date,
                        'message_status': message_status,
                        'expiry_date': check_result
                    }
                return True
            else:
                print(f"[LICENSING] Activation failed: {activation_result}")
                if activation_result == "device_mismatch":
                    return handle_device_mismatch(license_key, hw_id)
                elif activation_result == "expired":
                    from gui import show_license_error
                    show_license_error("Your Bot License has EXPIRED. Please contact the vendor to purchase a new subscription.")
                    return False
                elif activation_result == "invalid":
                    from gui import show_license_error
                    show_license_error("INVALID Bot License Key provided. Please check the key and try again, or contact the vendor.")
                    return False
                else:
                    from gui import show_license_error
                    show_license_error(f"Bot License validation failed ({activation_result}). Please contact the vendor.")
                    return False

# Function to increment message count
def increment_message_count(key: str, hw_id: str) -> bool:
    url = f"{LICENSING_SERVER_BASE_URL}/api/increment_message"
    payload = {"key": key, "hw_id": hw_id}
    headers = {'Content-Type': 'application/json'}

    try:
        print(f"[LICENSING] Incrementing message count for key ending in ...{key[-8:]}")
        response = requests.post(url, json=payload, headers=headers, timeout=10)
        response.raise_for_status()
        data = response.json()
        success = data.get("status") == "success"
        if success:
            print(f"[LICENSING] Message count incremented successfully.")
            # Update local cache so is_message_limit_reached() works immediately
            global CURRENT_LICENSE_INFO
            if CURRENT_LICENSE_INFO:
                CURRENT_LICENSE_INFO['messages_used'] = CURRENT_LICENSE_INFO.get('messages_used', 0) + 1
        else:
            print(f"[LICENSING] Failed to increment message count: {data.get('message', 'Unknown error')}")
        return success
    except Exception as e:
        print(f"[LICENSING] Error incrementing message count: {e}")
        return False
    
# Function to check if message limit is reached
def is_message_limit_reached() -> bool:
    """
    Check if the current message limit has been reached.
    Uses the globally stored license info.
    """
    global CURRENT_LICENSE_INFO
    # Check if CURRENT_LICENSE_INFO exists and is valid
    if not CURRENT_LICENSE_INFO or not CURRENT_LICENSE_INFO.get('valid', False):
        print("[LICENSING] No valid license info available to check message limit. Blocking action.")
        # Return True to block if no valid info is available
        return True

    # Access values safely, providing defaults
    tier = CURRENT_LICENSE_INFO.get('tier', 'BASIC')
    limit = CURRENT_LICENSE_INFO.get('message_limit', TIER_LIMITS.get(tier, 150)) # Use TIER_LIMITS for default
    used = CURRENT_LICENSE_INFO.get('messages_used', 0)

    reached = used >= limit
    print(f"[LICENSING] Message check: {used}/{limit} ({tier} tier) - Limit reached: {reached}")
    return reached

# Global variable to store current license info
CURRENT_LICENSE_INFO = None