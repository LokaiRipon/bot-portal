# gui.py
"""Graphical User Interface functions for dialogs and error messages."""

import tkinter as tk
from tkinter import simpledialog, messagebox
import os
import sys
from config import resource_path

def show_error_dialog(title: str, message: str):
    """Shows a generic error message box."""
    root = tk.Tk()
    root.withdraw()
    root.title(title)
    try:
        icon_path = resource_path("icon.ico")
        if os.path.exists(icon_path):
            root.iconbitmap(default=icon_path)
    except Exception:
        pass # Ignore icon errors
    root.attributes('-topmost', True)
    messagebox.showerror(title, message, parent=root)
    root.destroy()

def show_info_dialog(title: str, message: str):
    """Shows a generic info message box."""
    root = tk.Tk()
    root.withdraw()
    root.title(title)
    try:
        icon_path = resource_path("icon.ico")
        if os.path.exists(icon_path):
            root.iconbitmap(default=icon_path)
    except Exception as e:
        print(f"[LICENSING] Could not set icon for dialog: {e}")
    root.attributes('-topmost', True)
    messagebox.showinfo(title, message, parent=root)
    root.destroy()

def collect_user_credentials():
    """
    Collect necessary GoLogin credentials and License Key.
    Tries to load from a local config file first, otherwise asks the user via a GUI dialog.
    Saves credentials and license info to a file for future use.
    Works in both console and windowed (--windowed) PyInstaller modes.
    """
    print("\n🔐 Setup (GoLogin & License)")
    print("=" * 35)

    from config import get_application_path # Import locally to avoid circular import issues if config imports this
    # Define the path for the config file in the application directory
    config_file_path = os.path.join(get_application_path(), "bot_config.txt")
    
    token_key = None
    profile_id = None
    license_key = None

    # 1. Try loading from config file
    if os.path.exists(config_file_path):
        print(f"[DEBUG] Attempting to load credentials/license from {config_file_path}")
        try:
            with open(config_file_path, 'r') as f:
                lines = f.readlines()
                for line in lines:
                    if line.startswith("GOLOGIN_TOKEN_KEY="):
                        token_key = line.strip().split("=", 1)[1]
                    elif line.startswith("GOLOGIN_PROFILE_ID="):
                        profile_id = line.strip().split("=", 1)[1]
                    elif line.startswith("LICENSE_KEY="):
                        license_key = line.strip().split("=", 1)[1]
            
            # Basic validation for GoLogin (License checked later)
            if token_key and profile_id:
                 print("[DEBUG] GoLogin credentials loaded successfully from file.")
                 os.environ["GOLOGIN_TOKEN_KEY"] = token_key
                 os.environ["GOLOGIN_PROFILE_ID"] = profile_id
                 # License key is handled later in the flow
            else:
                 print("[DEBUG] Config file found but missing GoLogin keys or values.")
        except Exception as e:
            print(f"[DEBUG] Error reading config file: {e}")

    # --- Create a temporary root window for dialogs ---
    root = tk.Tk()
    root.withdraw() # Hide the main Tk window, only dialogs will appear
    root.title("Bot Setup")
    root.attributes('-topmost', True)
    
    # --- Set Custom Icon (if available) ---
    try:
        icon_path = resource_path("icon.ico")
        if os.path.exists(icon_path):
            root.iconbitmap(default=icon_path)
    except Exception as e:
        print(f"[DEBUG] Could not set custom icon for setup dialog: {e}")

    error_count = 0
    max_errors = 3

    # --- 2a. GoLogin Token Key ---
    if not os.getenv("GOLOGIN_TOKEN_KEY"):
        print("\n[SETUP] GoLogin Token Key not found or invalid.")
        while not token_key and error_count < max_errors:
            token_key = simpledialog.askstring(
                "GoLogin Token Key",
                "1. Open GoLogin.\n2. Go to Settings -> API.\n3. Copy your 'Token Key'.\n\nEnter your GoLogin Token Key:",
                parent=root
            )
            if token_key is None:
                error_count += 1
                print("[DEBUG] User cancelled Token Key input dialog.")
            elif not token_key.strip():
                error_count += 1
                messagebox.showwarning("Input Required", "Token Key cannot be empty. Please try again.", parent=root)
                token_key = None
            else:
                os.environ["GOLOGIN_TOKEN_KEY"] = token_key.strip()

        if not token_key:
            messagebox.showerror("Setup Failed", "GoLogin Token Key is required. Setup aborted.", parent=root)
            print("❌ GoLogin Token Key is required. Exiting.")
            root.destroy()
            sys.exit(1)

    # --- 2b. GoLogin Profile ID ---
    if not os.getenv("GOLOGIN_PROFILE_ID"):
        print("\n[SETUP] GoLogin Profile ID not found or invalid.")
        while not profile_id and error_count < max_errors:
            profile_id = simpledialog.askstring(
                "GoLogin Profile",
                "Find your bot's profile in GoLogin (e.g., P-1, P-2).\n\nEnter the full profile ID (e.g., '670b9c1a5d8f3e4c9f2d8a1b'):\n\n(Do NOT enter the order number like '1' or '2')",
                parent=root
            )
            if profile_id is None:
                error_count += 1
                print("[DEBUG] User cancelled Profile ID input dialog.")
            elif not profile_id.strip():
                error_count += 1
                messagebox.showwarning("Input Required", "Profile ID cannot be empty. Please try again.", parent=root)
                profile_id = None
            else:
                os.environ["GOLOGIN_PROFILE_ID"] = profile_id.strip()

        if not profile_id:
            messagebox.showerror("Setup Failed", "Profile ID is required. Setup aborted.", parent=root)
            print("❌ Profile ID is required. Exiting.")
            root.destroy()
            sys.exit(1)

    # --- 2c. License Key ---
    # Check if loaded license key is present, if not, ask for it.
    # The actual validation/activation happens later.
    if not license_key:
        print("\n[SETUP] License Key not found in config.")
        license_key = simpledialog.askstring(
            "Bot License Key",
            "Enter your purchased Bot License Key.\n(This was provided by the vendor after purchase)\n\nEnter License Key:",
            parent=root
        )
        if not license_key:
            messagebox.showerror("Setup Failed", "License Key is required to run the bot. Setup aborted.", parent=root)
            print("❌ License Key is required. Exiting.")
            root.destroy()
            sys.exit(1)
        license_key = license_key.strip()

    root.destroy() # Clean up the temporary Tk root window

    # --- 3. Save all to config file for next time ---
    try:
        with open(config_file_path, 'w') as f:
            f.write(f"GOLOGIN_TOKEN_KEY={os.environ['GOLOGIN_TOKEN_KEY']}\n")
            f.write(f"GOLOGIN_PROFILE_ID={os.environ['GOLOGIN_PROFILE_ID']}\n")
            # Only save license key if provided/entered
            if license_key: 
                f.write(f"LICENSE_KEY={license_key}\n") 
        print(f"\n✅ Credentials and License saved to {config_file_path} for future use.")
    except Exception as e:
        print(f"\n⚠️ Warning: Could not save config to file: {e}")
        print("   You might need to re-enter them next time.")

    print(f"\n✅ Using Profile ID: {os.environ['GOLOGIN_PROFILE_ID']}")
    print(f"✅ License Key provided (length: {len(license_key) if license_key else 0}). Will validate shortly.")
    print("🚀 Proceeding to license validation...\n")
    # Return the license key for further processing
    return license_key 

def show_license_error(error_message: str):
    """Displays a license-related error message to the user and exits the application."""
    print(f"\n🔒 LICENSE VALIDATION FAILED: {error_message}")
    show_error_dialog("Bot License Error", error_message)
    print("🛑 Bot shutting down due to license issue.")
    sys.exit(1)

def prompt_for_deactivation_code():
    """
    Prompts the user for the 4-digit deactivation code sent via email.
    Returns the code (str) or None if cancelled/invalid.
    """
    # 1. Inform user that a code was sent
    show_info_dialog(
        "Device Switch Requested",
        "This license key is registered to a different device.\n"
        "An email has been sent with a 4-digit deactivation code.\n"
        "Please check your email and enter the code in the next prompt."
    )

    # 2. Prompt user to input the 4-digit code
    temp_root = tk.Tk()
    temp_root.withdraw()
    temp_root.title("Device Switch")
    try:
        icon_path = resource_path("icon.ico")
        if os.path.exists(icon_path):
            temp_root.iconbitmap(default=icon_path)
    except Exception as e:
        print(f"[LICENSING] Could not set icon for dialog: {e}")
    temp_root.attributes('-topmost', True)
    
    user_code = simpledialog.askstring(
        "Enter Deactivation Code",
        "Enter the 4-digit code sent to your email:",
        parent=temp_root,
        show='*' # Optional: mask the input
    )
    temp_root.destroy() # Clean up temporary root

    if user_code:
        user_code = user_code.strip()
        print(f"[LICENSING] User entered code: {user_code}")
        # 3. Validate code format (basic check)
        if not user_code.isdigit() or len(user_code) != 4:
            print("[LICENSING] Invalid code format entered.")
            show_error_dialog("Invalid Code", "Please enter a valid 4-digit code.")
            return None # Fail
        return user_code
    return None # User cancelled