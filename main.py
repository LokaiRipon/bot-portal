# main.py
import sys
import time
import os

def anti_debug():
    # Timing check (debuggers slow down execution)
    start = time.time()
    time.sleep(0.01)
    if time.time() - start > 0.05:
        print("Debugger detected!")
        sys.exit(1)

    # Check for common debuggers (Windows)
    try:
        import subprocess
        result = subprocess.run(['tasklist'], capture_output=True, text=True)
        suspicious = ['ollydbg', 'x32dbg', 'x64dbg', 'ida', 'windbg']
        if any(proc in result.stdout.lower() for proc in suspicious):
            sys.exit(1)
    except:
        pass

anti_debug()


# main.py
"""Main entry point for the bot application."""

import sys
import time
import keyboard
import random

# Import functions from your modules
from selenium_setup import connect
from chat_scraper import get_client_profile, get_my_profile, get_chat_history
from ai_interaction import load_city_database, generate_reply
from human_mimic import clear_input_box, type_like_human
import tkinter as tk
from tkinter import ttk

from gui import collect_user_credentials, show_error_dialog, show_license_error, show_info_dialog, prompt_for_deactivation_code
from licensing import generate_hardware_id, handle_license_validation, increment_message_count, is_message_limit_reached, CURRENT_LICENSE_INFO

def main():
    """Main entry point for the bot application."""
    print("🤖 Bot application starting...")
    try:
        # 1. Setup & Credentials
        license_key = collect_user_credentials()
        hw_id = generate_hardware_id()
        
        # 2. License Validation
        if not handle_license_validation(license_key, hw_id):
            return

        # --- Create GUI_gui Simulation Window ---
        setup_root = tk.Tk()
        setup_root.title("Bot Setup")
        setup_root.geometry("350x100")
        setup_root.resizable(False, False)
        setup_root.geometry("+0+0")
        # Try to set icon if available (from config.resource_path)
        try:
             from config import resource_path
             icon_path = resource_path("icon.ico")
             if os.path.exists(icon_path):
                setup_root.iconbitmap(default=icon_path)
        except Exception:
             pass # Ignore if icon fails

        setup_root.attributes('-topmost', True) # Keep window on top
        status_label = ttk.Label(setup_root, text="Initializing...", font=("Arial", 10))
        status_label.pack(padx=20, pady=30)
        setup_root.update() # Show the window immediately
        # -----------------------------------

        # 3. Bot Startup (Selenium, GOLOGIN) - Pass the label
        print("🚀 Continuing with Bot Startup...")
        # Pass the status_label to connect
        driver = connect(status_label=status_label)
        if not driver:
            # Update status on error
            status_label.config(text="Setup failed. Check logs.")
            setup_root.update()
            time.sleep(2) # Brief pause to show error
            setup_root.destroy() # Close the window

            error_msg = "❌ Failed to connect to the browser. Please check GoLogin and network."
            print(error_msg)
            from gui import show_error_dialog
            show_error_dialog("Connection Error", error_msg)
            sys.exit(1)

        # --- Show "Ready" and Close Window ---
        status_label.config(text="✅ Ready! Browser window opened.")
        setup_root.update()
        time.sleep(1.5) # Show "Ready" message for 1.5 seconds
        setup_root.destroy() # Close the setup window

        # --- Ensures Selenium is looking at the chat tab, not the login page or other tabs. ---
        # --- During startup give the bot time to load tabs completely ---
        print("🔍 Searching for the correct chat tab...")
        correct_tab_found = False
        # Allow a few attempts in case tabs are still loading
        for attempt in range(15): # Increased attempts slightly
            print(f"[DEBUG] Tab search attempt {attempt + 1}/15")
            for handle in driver.window_handles:
                driver.switch_to.window(handle)
                current_url = driver.current_url.lower()
                current_title = driver.title.lower()
                print(f"[DEBUG] Checking tab - URL: {current_url}, Title: '{current_title}'")

                # --- IMPROVED TAB IDENTIFICATION (Flexible for future sites) ---
                # --- UPDATE THIS LIST: Add new chat domains here as needed ---
                chat_domains = ["chathomebase.com", "remotely4u.com"]
                # ------------------------------------------------------------
                is_chat_domain = any(domain in current_url for domain in chat_domains)
                is_chat_path = "/chat" in current_url # Adjust if path is different, e.g., '/messages'
                # Explicitly avoid known incorrect tabs (like withinhours.com)
                is_not_wrong_site = "0.9 hours" not in current_title and "within hours" not in current_title

                if is_chat_domain and is_chat_path and is_not_wrong_site:
                     print(f"[DEBUG] ✅ Switched to likely chat tab (Improved check): {driver.title} ({driver.current_url})")
                     correct_tab_found = True
                     break # Found the correct tab based on improved criteria

            if correct_tab_found:
                break
            else:
                print("[DEBUG] Correct chat tab not found yet. Waiting 1 second before retrying...")
                time.sleep(1) # Wait a bit before checking again

        if not correct_tab_found:
            print("[DEBUG] ⚠️ No correct chat tab found after several attempts. The current active tab might be wrong.")
            # Inform the user that the correct tab wasn't automatically found
            from gui import show_error_dialog
            show_error_dialog("Warning", "The bot could not automatically switch to the chat tab. Please ensure the correct chat tab is active and reload the page if necessary.")
        else:
            print("✅ Driver is now focused on the correct chat tab.")

        print("✅ Driver object created successfully.")
        # 4. Loading AI Data (e.g., city database)
        print("🚀 Loading city database for AI...")
        CITY_COORDS = load_city_database()
        print(f"🎉 City database ready with {len(CITY_COORDS)} entries.")

        # 5. The Main Loop
        print("🤖 Bot started. Press F8 to generate reply, F9 to exit.")
        while True:
            if keyboard.is_pressed("f8"):
                print("⌨️ F8 detected...")

                # NEW: Check message limit before processing
                if is_message_limit_reached():
                    print("❌ Message limit reached!")
                    # Import here to avoid circular import issues if necessary
                    from gui import show_license_error
                    from licensing import CURRENT_LICENSE_INFO # Import to access the info

                    # Get tier and limit from the stored info
                    tier = CURRENT_LICENSE_INFO.get('tier', 'BASIC')
                    limit = CURRENT_LICENSE_INFO.get('message_limit', 150)
                    reset_date = CURRENT_LICENSE_INFO.get('reset_date', 'Unknown')

                    # NEW: Create a more specific message for daily limit
                    daily_limit_message = f"""
                    Message limit reached! Your {tier} tier allows {limit} messages per day. 
                    Please upgrade your subscription to enjoy longer messages per day!
                    """

                    print(f"[LICENSING] {daily_limit_message}")
                    show_license_error(daily_limit_message) # Show the specific message
                    time.sleep(1)  # Brief pause to let the dialog show
                    continue  # Skip this iteration

                # ... (rest of the F8 logic: scraping, AI, typing, incrementing) ...
                time.sleep(random.uniform(0.2, 0.5))
                print("[DEBUG] Waiting briefly for chat to update...")
                time.sleep(1.5) # Wait 1.5 seconds for page/DOM to update
                # ----------------------
                client_info = get_client_profile(driver)
                time.sleep(random.uniform(0.1, 0.2))
                my_info = get_my_profile(driver)
                time.sleep(random.uniform(0.1, 0.2))
                chat_history = get_chat_history(driver)
                reply = generate_reply(client_info, chat_history, my_info, CITY_COORDS)
                print(f"🧠 AI: {reply}")

                print("⌨️ Please ensure the chat input box is focused (clicked). Typing in 2 seconds...")
                time.sleep(2)

                clear_input_box()
                time.sleep(random.uniform(0.2, 0.5))
                type_like_human(reply)
                print("✅ Typing complete. Please review and send manually.")

                # NEW: Increment message count after successful reply
                if license_key and hw_id:
                    from licensing import increment_message_count # Import here to avoid circular issues if needed
                    increment_message_count(license_key, hw_id)
                    # Update local counter for display (optional)
                    if hasattr(main, 'message_counter'):
                        main.message_counter += 1
                    else:
                        main.message_counter = 1
                    print(f"📊 Messages sent: {getattr(main, 'message_counter', 1)}")

                time.sleep(0.5)

            if keyboard.is_pressed("f9"):
                print("👋 Exiting...")
                break
            time.sleep(0.1)
    except Exception as e:
        # Ensure setup window is closed on unexpected error before main loop
        if 'setup_root' in locals() and setup_root:
            try:
                setup_root.destroy()
            except:
                pass
        print(f"\nUnexpected error in main application loop: {e}")
        error_msg = "An unexpected error occurred. Please restart the bot."
        show_error_dialog("Fatal Error", error_msg)
        sys.exit(1)
    finally:
        # Ensure setup window is closed in finally block as well
        if 'setup_root' in locals() and setup_root:
            try:
                setup_root.destroy()
            except:
                pass
        if 'driver' in locals() and driver:
            try:
                driver.quit() # This will now also call stop_gologin_profile() due to our modification
                print("Browser driver closed.")
            except Exception as e:
                print(f"Error closing browser driver: {e}")
        else:
            # If driver was never created or failed early, ensure profile is stopped
            print("Main loop ended without a driver. Ensuring profile is stopped...")
            
if __name__ == "__main__":
    main()